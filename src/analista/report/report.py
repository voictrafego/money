"""Relatório do analista: amarra múltiplos (Cap. 10), crescimento (Cap. 14),
CAPM (Cap. 16) e DDM (Cap. 13-17) em um parecer por ação, com veredito.

A regressão de comparáveis (Cap. 11/12) entra no fluxo por setor (comando `rank`),
pois exige um conjunto de pares; aqui o foco é o valuation por desconto de dividendos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd
from tabulate import tabulate

from ..core import arquetipo, capm, comparables, ddm, growth, indicators, lentes, lifecycle, motores, screening
from ..core import multiples as mult
from ..core import normalizacao as norm
from ..core.fundamentals import CompanyData
from . import selo as selo_mod


@dataclass
class AnaliseAcao:
    ticker: str
    nome: str
    setor: str
    preco_atual: Optional[float]
    multiplos: Dict[str, Optional[float]] = field(default_factory=dict)
    g_historico: Optional[float] = None
    g_fundamentos: Optional[float] = None
    g_alto: Optional[float] = None
    g_estavel: Optional[float] = None
    ke: Optional[float] = None
    beta: Optional[float] = None
    estagio: str = ""
    ddm_constante: Optional[ddm.ResultadoDDM] = None
    ddm_h: Optional[ddm.ResultadoDDM] = None
    sensibilidade: Optional[List[List[Optional[float]]]] = None
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    veredito: str = ""
    alertas: List[str] = field(default_factory=list)
    # --- Phase 6: read técnico consultivo (aditivo, read-only sobre o fundamento) ---
    sinais: Optional["indicators.SinaisTecnicos"] = None   # populado por indicators.calcular
    timing_estado: str = ""                                # "tendencia_de_alta"|"sem_tendencia"|"atencao"
    timing_resumo: str = ""                                # frase PT consultiva (TIMING-01)
    matriz_leitura: str = ""                               # frase curada fundamento×técnico (Plan 02)
    alerta_reverificacao: Optional[str] = None             # None se nada rompeu (Plan 02)
    # --- Fase 20: Selo de Sustentabilidade × veredito de preço (aditivo, read-only) ---
    selo: Optional["selo_mod.Selo"] = None                 # cor do BSD × faixa do DDM → quadrante
    # --- Fase 1 v2.2: roteamento por arquétipo (aditivo, read-only) ---
    arquetipo: str = ""                                    # chave do classificador (core/arquetipo)
    motor: str = ""                                        # motor primário resolvido ("ddm" ou "pendente_fase_2")
    arquetipo_fronteirico: bool = False                    # conflito real de sinais (ARQ-02)
    arquetipo_candidatos: List[str] = field(default_factory=list)  # candidatos do funil (fallback honesto)
    motor_pendente: bool = False                           # D-06: paridade com o predicado de suspensão (motor != "ddm"); veredito de preço pelo selo suspenso onde o motor não é o DDM
    # --- Fase 2 v2.2: intrínseco pelo motor do arquétipo (aditivo; motor CALCULA e EXIBE, D-06) ---
    intrinseco_motor: Optional[float] = None               # valor intrínseco pelo motor primário do arquétipo (None se degradou)
    motor_rotulo: str = ""                                  # rótulo humano do motor (motores.MOTOR_ROTULO)
    # --- Fase 3 v2.2 (Achado 2 / SAN-01): guarda-corpo do DDM ---
    ddm_inaplicavel: bool = False                          # True quando a faixa DDM saiu negativa/degenerada (suprimida na borda)
    san01_reetiquetado: bool = False                       # SAN-01 (03-02): veredito "evitar" reetiquetado como aberração anti-DDM (número mantido visível)
    # --- Fase 3 v2.2 (VER-01/ENS-01): banda do ensemble motor×contraponto + divergência ---
    contraponto_valor: Optional[float] = None              # mid do DDM (contraponto universal, D-02); None se o DDM degradou
    banda_do_motor: bool = False                           # True quando vmin/vmax vêm do motor do arquétipo (ensemble), não do DDM
    divergencia_ativa: bool = False                        # motor × contraponto divergem > limiar (comparables.LIMIAR_DIVERGENCIA = 2×)
    divergencia_razao: Optional[float] = None              # razão maior/menor entre as duas lentes (1.0 quando não há divergência)
    divergencia_hipotese: str = ""                          # frase curada por (arquétipo, sinal) — preenchida só quando divergencia_ativa
    # --- Fase 3 v2.2 (VER-02): caso-fronteira → assume a dúvida (range dos candidatos + bandeira) ---
    arquetipo_incerto: bool = False                        # ramo fronteiriço rodou (a.arquetipo_fronteirico): classificação incerta assumida
    candidatos_intrinsecos: List[tuple] = field(default_factory=list)  # [(arquetipo, intrínseco)] dos candidatos que resolveram (não-None, positivos)
    veredito_range: Optional[tuple] = None                 # (menor, maior) dos intrínsecos quando >=2 candidatos resolveram; None se 0/1


def _guarda_faixa_ddm(a: AnaliseAcao) -> None:
    """Guarda-corpo de emissão do DDM (Achado 2 / SAN-01) — puro e read-only sobre o veredito.

    Onde o DDM roda mas a faixa intrínseca (vmin/vmax = min/max da matriz de sensibilidade)
    sai economicamente INVÁLIDA — NEGATIVA (`vmax <= 0`: HAPV3 −2,20/−1,66; PCAR3 −7,67/−5,95)
    ou DEGENERADA (`vmin == 0 and vmax == 0`: PRIO3 0–0) — essa faixa NÃO é preço-alvo, é
    ruído que o usuário lê como intrínseco. Payout baixo / alto capex / lucro negativo tornam
    o DDM por dividendos estruturalmente inaplicável àquele perfil.

    Ação: marca `a.ddm_inaplicavel` e ZERA vmin/vmax → None, de modo que a métrica
    "Intrínseco (DDM)" e a tabela do relatório caiam no caminho de "não disponível" (o ramo
    condicional existente já suprime o veredito SUB/SOBRE a partir de faixa None). Acrescenta
    um alerta honesto do porquê. NÃO toca core/ddm.py nem o firewall selo↛report — só a borda.

    O caso vmin<0 mas vmax>0 (faixa cruza zero com teto positivo) NÃO é degenerado aqui: o
    teto ainda carrega informação, então a faixa é preservada (só `vmax<=0` ou 0–0 disparam)."""
    if a.vmax is None:
        return
    faixa_negativa = a.vmax <= 0
    faixa_degenerada = a.vmin == 0 and a.vmax == 0
    if faixa_negativa or faixa_degenerada:
        a.ddm_inaplicavel = True
        a.vmin = None
        a.vmax = None
        a.alertas.append(
            "DDM estruturalmente inaplicável a este perfil (payout baixo / alto capex ou "
            "lucro negativo): a faixa por dividendos resultou negativa ou zero e NÃO é "
            "preço-alvo — por isso não é exibida como intrínseco."
        )


def _guarda_san01(
    a: AnaliseAcao, c: CompanyData, cfg: dict, valor_pares: Optional[float] = None
) -> None:
    """Guarda-corpo anti-aberração SAN-01 (Plan 03-02) — puro e read-only sobre o veredito.

    Modelado em `_guarda_faixa_ddm`: marca uma flag + mexe SÓ no veredito + alerta honesto,
    na borda de emissão, sem tocar `core/`, `ddm.py` nem `selo.py` (firewall).

    Regra literal do brief (D-05): quando o veredito montado resultaria em "evitar"
    (quadrante Baixa×Caro, i.e. prefixo SOBREAVALIADA) E os sinais canônicos configuram uma
    ABERRAÇÃO — `intrínseco < fator_pares × valor-dos-pares` (só quando `valor_pares` está
    disponível) **E** `ROE_valuation > roe_min` **E** `corte de payout > corte_payout_min` —
    troca o veredito por **"DDM conservador demais para este perfil — ver motor primário do
    arquétipo"**, MANTENDO o número intrínseco visível (reetiqueta honesta, não supressão).

    Degradação D-04 (custo-zero): no funil single-stock não há regressão de pares ajustada,
    então `valor_pares=None` — a condição de pares NÃO é avaliada (tratada como neutra) e o
    gate cai para as 2 restantes. NUNCA puxa rede.

    Never-raise: qualquer insumo obrigatório None (ROE, payout cru/normalizado) → não dispara
    (não inventa aberração sobre dado ausente). O prefixo do texto reetiquetado NÃO casa nenhum
    dos prefixos que `selo.faixa_do_veredito` reconhece → `faixa=None` → o selo não estampa
    "Evitar" (o número segue no texto). `selo.py` intocado."""
    # Gatilho: só o quadrante Baixa×Caro ("Evitar") — que o selo cruzaria a partir de SOBREAVALIADA.
    if not a.veredito.startswith("SOBREAVALIADA"):
        return

    san = (cfg or {}).get("veredito", {}).get("san01", {})
    fator_pares = san.get("fator_pares", 0.5)
    roe_min = san.get("roe_min", 0.15)
    corte_payout_min = san.get("corte_payout_min", 0.40)

    # Sinais canônicos (FIX-04): o MESMO número dos 3 modos. None → não dispara (never-raise).
    roe = c.roe_valuation()
    payout_norm = c.payout_valuation()
    ult = c.ultimo_ano()
    payout_cru = c.payout(ult) if ult is not None else None
    if roe is None or payout_norm is None or payout_cru is None or payout_cru <= 0:
        return

    corte_payout = 1.0 - (payout_norm / payout_cru)

    cond_roe = roe > roe_min
    cond_corte = corte_payout > corte_payout_min
    # Condição de pares (D-04): avaliada SÓ quando um valor-de-pares foi fornecido E há
    # intrínseco do motor para comparar; ausente → neutra (não bloqueia o gate).
    if valor_pares is not None and a.intrinseco_motor is not None:
        cond_pares = a.intrinseco_motor < fator_pares * valor_pares
    else:
        cond_pares = True

    if not (cond_roe and cond_corte and cond_pares):
        return

    # Número mantido visível: o intrínseco do motor primário quando existe; senão o mid da banda.
    ref = a.intrinseco_motor
    if ref is None and a.vmin is not None and a.vmax is not None:
        ref = (a.vmin + a.vmax) / 2.0

    a.san01_reetiquetado = True
    sufixo = f" (intrínseco ≈ R$ {_br(ref)})" if ref is not None else ""
    a.veredito = (
        "DDM conservador demais para este perfil — ver motor primário do arquétipo" + sufixo
    )
    motivos = [f"ROE {_br(roe * 100, 1)}% > {_br(roe_min * 100, 0)}%",
               f"corte de payout {_br(corte_payout * 100, 0)}% > {_br(corte_payout_min * 100, 0)}%"]
    if valor_pares is not None and a.intrinseco_motor is not None:
        motivos.append(f"intrínseco < {_br(fator_pares, 1)}× valor-dos-pares")
    a.alertas.append(
        "Guarda-corpo anti-aberração (SAN-01): veredito reetiquetado — "
        + "; ".join(motivos)
        + ". O DDM de estágio único é conservador demais para este perfil; "
        "a referência primária é o motor do arquétipo (número acima mantido visível)."
    )


def _intrinseco_por_motor(
    motor: str, c: CompanyData, a: AnaliseAcao, cfg: dict
) -> Optional[float]:
    """Dispatch PURO motor→intrínseco (extraído do funil, VER-02 03-03) — reutilizável.

    Devolve o valor intrínseco pelo motor dado consumindo SEMPRE os números-síntese
    (`*_valuation`, `norm.base_normalizada`, `lentes.vpa`), NUNCA o cru (FIX-04/Pitfall 2),
    com a MESMA lógica do dispatch do funil (rim / normalizado / dcf / nav). Caso `"ddm"`:
    o motor primário deste perfil é o próprio bloco DDM, então devolve o mid da banda
    (`vmin/vmax` já calculada) quando disponível, senão None. Never-raise: qualquer insumo
    degenerado/erro → None. É consumido pelo dispatch principal (comportamento idêntico ao
    baseline) E pelo ramo fronteiriço (um motor por candidato).

    Nota: a guarda de não-positivo (`valor <= 0` não é preço-alvo) fica no chamador — o funil
    a aplica com alerta honesto; o ramo fronteiriço a aplica ao coletar os candidatos."""
    ult = c.ultimo_ano()
    g_estavel = cfg["ddm"]["g_estavel"]
    mot_cfg = (cfg or {}).get("motores", {})
    try:
        if motor == "rim":
            res_rim = motores.rim(
                vpa0=lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult)),
                roe0=c.roe_valuation(),
                ke=motores.ke_rim(c.beta, cfg),
                retencao=(1.0 - (c.payout_valuation() or 0.0)),
                n=mot_cfg.get("rim", {}).get("n_fade", 10),
            )
            return res_rim.valor_intrinseco if res_rim else None
        if motor == "normalizado":
            cic = mot_cfg.get("ciclica", {})
            lpa_mid = mult.lpa(
                norm.base_normalizada(
                    c.serie("lucro_liquido"),
                    anos_media=cic.get("anos_media", 10), winsor=cic.get("winsor", 0.10),
                ),
                c.num_acoes.get(ult),
            )
            return motores.lucro_normalizado(lpa_mid, a.ke, g_estavel)
        if motor == "dcf":
            return motores.dcf_crescimento(
                c.lpa_valuation(), a.g_alto, g_estavel, a.ke,
                mot_cfg.get("crescimento", {}).get("n_anos_explicito", 10),
            )
        if motor == "nav":
            return motores.nav_contabil(
                c.patrimonio_liquido.get(ult), c.num_acoes.get(ult)
            )
        if motor == "ddm":
            if a.vmin is not None and a.vmax is not None:
                return (a.vmin + a.vmax) / 2.0
            return None
    except Exception:
        return None
    return None


def _veredito_fronteirico(a: AnaliseAcao, c: CompanyData, cfg: dict) -> None:
    """VER-02 (03-03): caso-fronteira → a ferramenta assume a dúvida em voz alta.

    Quando `a.arquetipo_fronteirico` (conflito real de sinais da Fase 1), roda o motor de CADA
    arquétipo candidato (`a.arquetipo_candidatos`) via `_intrinseco_por_motor` (o MESMO dispatch
    do funil, um motor por candidato), coleta os intrínsecos que resolveram (não-None, > 0) e
    monta o range [menor..maior] + a bandeira "classificação incerta entre X e Y" (D-06). O
    veredito recebe o prefixo `VERIFICAR`: `selo.montar_selo` (selo.py:119) já suprime faixa/
    rótulo, então o selo NÃO estampa faixa cravada no fronteiriço (reusa a supressão do
    VERIFICAR); o range/candidatos aparecem como CONTEÚDO exibido, não como selo.

    Degradação honesta: candidato cujo motor devolve None/≤0 é filtrado; com exatamente 1
    resolvido exibe só esse valor (sem forçar um range de 1 ponto); com 0 resolvido informa que
    os motores candidatos não estimaram preço-alvo. Sobrescreve o veredito do VER-01 (precedência
    no fronteiriço). NÃO toca `selo.py`."""
    pares: List[tuple] = []
    vistos = set()
    for cand in a.arquetipo_candidatos:
        if cand in vistos:
            continue
        vistos.add(cand)
        motor = arquetipo.ARQUETIPO_MOTOR.get(cand)
        if motor is None:
            continue
        val = _intrinseco_por_motor(motor, c, a, cfg)
        if val is not None and val > 0:
            pares.append((cand, val))

    a.arquetipo_incerto = True
    a.candidatos_intrinsecos = pares

    if len(pares) >= 2:
        valores = [v for _, v in pares]
        menor, maior = min(valores), max(valores)
        a.veredito_range = (menor, maior)
        primeiro, ultimo = pares[0][0], pares[-1][0]
        a.veredito = (
            f"VERIFICAR — caso-fronteira: classificação incerta entre {primeiro} e {ultimo}. "
            f"Intrínseco no range R$ {_br(menor)}–{_br(maior)} conforme o arquétipo assumido."
        )
        a.alertas.append(
            "Caso-fronteira (VER-02): os sinais da Fase 1 conflitam — a ferramenta assume a "
            f"dúvida. Rodou o motor de cada arquétipo candidato ({primeiro}, {ultimo}); o range "
            f"R$ {_br(menor)}–{_br(maior)} é o span honesto da classificação incerta, não um "
            "preço-alvo cravado."
        )
    elif len(pares) == 1:
        cand, val = pares[0]
        a.veredito_range = None
        a.veredito = (
            f"VERIFICAR — caso-fronteira: classificação incerta, mas só o motor do arquétipo "
            f"{cand} estimou preço-alvo (R$ {_br(val)}); os demais candidatos degradaram."
        )
        a.alertas.append(
            "Caso-fronteira (VER-02): os sinais conflitam, porém apenas um motor candidato "
            f"resolveu preço-alvo ({cand}: R$ {_br(val)}) — exibido sem forçar um range de 1 ponto."
        )
    else:
        a.veredito_range = None
        a.veredito = (
            "VERIFICAR — caso-fronteira: os sinais de arquétipo conflitam e nenhum motor "
            "candidato estimou preço-alvo confiável."
        )
        a.alertas.append(
            "Caso-fronteira (VER-02): classificação incerta e os motores candidatos não "
            "estimaram preço-alvo — veredito de preço suspenso sem estampar faixa falsa."
        )


def analisar_acao(c: CompanyData, cfg: dict) -> AnaliseAcao:
    anos = c.anos_ordenados()
    ult = c.ultimo_ano()
    a = AnaliseAcao(ticker=c.ticker, nome=c.nome, setor=c.setor, preco_atual=c.preco_atual)

    # --- Múltiplos (Cap. 10) ---
    # FIX-04: os múltiplos de VALUATION (ROE, LPA→P/L/EY, payout, DY) saem dos métodos
    # canônicos normalizados — o MESMO número que o Ranking (app/cli) consome (Core Value).
    # ML segue cru (margem do último ano, métrica de exibição, não síntese de valuation).
    lpa = c.lpa_valuation()        # base de lucro normalizada / nº ações (não o cru de 1 ano)
    dpa = c.dpa(ult)               # dividendos crus (não dependem de lucro → fora do FIX-04)
    a.multiplos = {
        "ML": mult.margem_liquida(c.lucro_liquido.get(ult), c.vendas_liquidas.get(ult)),
        "ROE": c.roe_valuation(),
        "P/L": mult.preco_lucro(c.preco_atual, lpa),
        "EY": mult.earnings_yield(lpa, c.preco_atual),
        "DP (payout)": c.payout_valuation(),
        "CDC": mult.cobertura_dividendos_caixa(c.fco.get(ult), c.num_acoes.get(ult), dpa),
        "DY": c.dy_atual(),        # trailing-12m c/ fallback (contexto: inclui extraordinários)
        "DY rec.": c.dy_recorrente(),  # FIX-06 item J: DY sobre provento NORMALIZADO (sustentável)
    }

    # --- Crescimento (Cap. 14) ---
    # Tendência log-linear (regressão de ln(lucro) sobre o tempo) na série de lucro
    # NORMALIZADA (winsorizada): usa TODOS os pontos, então um exercício atípico no
    # início/fim deixa de mandar no g histórico (não mais endpoint-a-endpoint). A série
    # CRUA segue valendo p/ os fatos per-ano do ciclo de vida (lucrou/decresceu em cada ano).
    lucros_raw = c.serie("lucro_liquido")
    lucros = c.serie_lucro_normalizada()
    if len(lucros) >= 2:
        a.g_historico = growth.crescimento_log_linear(lucros)
    # g_fundamentos usa o MESMO payout do valuation (payout_valuation) ⇒ é o g SUSTENTÁVEL,
    # quanto a empresa consegue reinvestir: g_fund = ROE_normalizado × (1 − payout_valuation).
    a.g_fundamentos = growth.crescimento_por_fundamentos(c.roe_valuation(), c.payout_valuation())
    g_estavel = cfg["ddm"]["g_estavel"]
    a.g_estavel = g_estavel
    # DDM-FIX-02 (reconciliação g × fundamentos, caso VULC3): o g_alto adotado parte do
    # crescimento histórico observado (CAGR sobre a série normalizada), mas é SUBORDINADO ao
    # g sustentável — o TETO do g_alto passa a ser g_fundamentos (CONTEXT FIX-02). O g deixa
    # de ser um haircut arbitrário do CAGR e reflete o reinvestimento real.
    # Precedência: g_fund (sustentável) → teto absoluto 0.25 → trava ≤ Ke (FIX-01, abaixo).
    # Payout ≥ 100% (ou ROE não positivo) ⇒ g_fund ≤ 0 ⇒ g_alto cai para 0 — SEM o piso
    # artificial g_estavel na fase explícita (g_estavel segue valendo só como taxa da
    # perpetuidade no DDM, não como piso do crescimento alto).
    g_alto = a.g_historico if a.g_historico is not None else a.g_fundamentos
    if a.g_fundamentos is not None:
        g_alto = a.g_fundamentos if g_alto is None else min(g_alto, a.g_fundamentos)
    if g_alto is not None:
        g_alto = max(0.0, min(g_alto, 0.25))  # teto absoluto 25% a.a.; sem piso g_estavel (nunca < 0)
    a.g_alto = g_alto

    # --- Estágio do ciclo de vida (Cap. 8) ---
    # Fatos per-ano: "lucrou em todos os anos?" / "decresceu?" leem a série CRUA — são
    # observações históricas de elegibilidade, não o número-síntese de valuation.
    lucro_positivo = all(v > 0 for v in lucros_raw) if lucros_raw else False
    lucro_decrescente = len(lucros_raw) >= 2 and lucros_raw[-1] < lucros_raw[0]
    a.estagio = lifecycle.classificar_estagio(
        a.g_historico, c.payout(ult), lucro_positivo, lucro_decrescente
    )

    # --- CAPM (Cap. 16) ---
    cap = cfg["capm"]
    a.beta = c.beta
    if c.beta is not None:
        if cap.get("abordagem") == "local":
            # FIX-03 (CAPM ao vivo, caso VULC3): Ke local = rf + beta × ERP Brasil. O rf
            # (cap["rf_local"]) é a Selic ao vivo do BCB, JÁ injetada pelos entry points
            # (cli/app); offline (testes) ele vale o selic_fallback do config. A engine NÃO
            # toca a rede aqui — lê apenas o rf resolvido em cfg, mantendo-se pura/determinística.
            a.ke = capm.ke_local(c.beta, cap["rf_local"], cap["erp_local"])
        else:
            params = capm.CapmParams(
                rf_us=cap["rf_us"], embi_brasil=cap["embi_brasil"], erp_us=cap["erp_us"],
                inflacao_br=cap["inflacao_br"], inflacao_us=cap["inflacao_us"],
            )
            a.ke = capm.ke_eua_ajustada(c.beta, params)

    # DDM-FIX-01 (caso VULC3): o crescimento da fase explícita não pode exceder Ke.
    # Acima disso o fator (1+g_alto)/(1+Ke) > 1 e a soma dos 10 anos infla a cada ano
    # em vez de convergir — artefato matemático, não tese de valor. Teto econômico = Ke.
    if a.g_alto is not None and a.ke is not None:
        a.g_alto = min(a.g_alto, a.ke)

    # --- Roteamento por arquétipo (Fase 1 v2.2, ARQ-01/ENG-01) ---
    # Classifica o negócio ANTES do valuation e resolve o motor primário do registry.
    # Aditivo/read-only: NÃO altera o bloco DDM abaixo (que roda sempre como lente); a
    # suspensão D-04 do veredito primário quando o motor está pendente é aplicada no
    # bloco de veredito. pagadora_regulada → "ddm" (TAEE11 idêntica, ENG-06).
    arq = arquetipo.classificar(c, cfg)
    a.arquetipo = arq.chave
    a.arquetipo_fronteirico = arq.fronteirico
    a.arquetipo_candidatos = arq.candidatos
    motor = arquetipo.ARQUETIPO_MOTOR.get(arq.chave)
    a.motor = motor or "pendente_fase_2"
    a.motor_pendente = a.motor != "ddm"   # D-06: paridade com o predicado de suspensão (não drift)

    # --- Dispatch do motor do arquétipo (Fase 2 v2.2, ENG-02..05) ---
    # O motor primário resolvido CALCULA e GRAVA o intrínseco do arquétipo (D-06: motor
    # calcula e EXIBE; o selo NÃO consome ainda — VER-01/Fase 3). Consome SEMPRE os números
    # já-síntese (*_valuation / base_normalizada / lentes.vpa), NUNCA o cru (Pitfall 2/FIX-04).
    # Motores são never-raise (devolvem None sob dado degenerado). O bloco DDM abaixo continua
    # rodando SEMPRE (agora como lente conservadora onde motor != "ddm") — cálculo intocado.
    # Leitura defensiva dos knobs do motor (paridade com classificar/ke_rim): config antigo sem
    # o bloco `motores:` degrada para os defaults do config.yaml sem quebrar o never-raise (WR-03).
    a.motor_rotulo = motores.MOTOR_ROTULO.get(a.motor, "")
    # Dispatch extraído em `_intrinseco_por_motor` (VER-02 03-03): mesma lógica de antes, agora
    # reutilizada também pelo ramo fronteiriço (um motor por candidato). motor == "ddm": o helper
    # devolve None aqui (a banda ainda não foi calculada) — o bloco DDM abaixo é o motor primário.
    a.intrinseco_motor = _intrinseco_por_motor(a.motor, c, a, cfg)

    # Guarda-corpo do intrínseco do motor (paridade com _guarda_faixa_ddm / SAN-01): um valor
    # NÃO-POSITIVO (PL/lucro normalizado negativo: holding sem patrimônio, cíclica em fundo de
    # ciclo) NÃO é preço-alvo — é ruído que o usuário leria como intrínseco negativo. Suprime na
    # borda (None + alerta honesto) para o veredito cair no ramo "motor sem preço-alvo" e o render
    # não estampar um intrínseco ≈ R$ negativo. A anti-aberração por mediana de pares é Fase 3.
    if a.intrinseco_motor is not None and a.intrinseco_motor <= 0:
        a.alertas.append(
            f"Motor '{a.motor}' devolveu valor não-positivo (PL/lucro normalizado negativo): "
            "não é preço-alvo — não exibido como intrínseco."
        )
        a.intrinseco_motor = None

    # --- DDM de dois estágios (Cap. 15/17) ---
    payout_proj = c.payout_valuation()  # média 3a + clamp 1.0 (função canônica única)
    n = cfg["ddm"]["n_anos_explicito"]
    trib = cfg["ddm"].get("tributacao_dividendos", 0.0)
    if None not in (lpa, payout_proj, a.g_alto, a.ke) and a.ke > g_estavel:
        dpa_inicial = lpa * (1 + a.g_alto) * payout_proj
        a.ddm_constante = ddm.ddm_dois_estagios(
            dpa_inicial, a.g_alto, n, g_estavel, a.ke, decrescente=False, tributacao=trib
        )
        a.ddm_h = ddm.ddm_dois_estagios(
            dpa_inicial, a.g_alto, n, g_estavel, a.ke, decrescente=True, tributacao=trib
        )
        sens = cfg["ddm"]["sensibilidade"]
        a.sensibilidade = ddm.matriz_sensibilidade(
            dpa_inicial, a.g_alto, n, g_estavel, a.ke,
            sens["delta_ke"], sens["delta_g"],
        )

    # --- Flags de risco (armadilhas de dividendos, Cap. 6) — usadas no veredito E nos alertas ---
    # FIX-04: os flags leem dado CRU de propósito. O payout_valuation é clampado em 1.0,
    # então NUNCA dispararia o alerta ">100%" (desligaria silenciosamente o DDM-FIX-05);
    # o detector de armadilha tem de ver o payout reportado do último ano (VULC3: 124,7%).
    dy = a.multiplos.get("DY")
    payout_ult = c.payout(ult)   # CRU (não payout_valuation) — detector de armadilha
    flag_dy = dy is not None and dy > 0.15
    flag_payout = payout_ult is not None and payout_ult > 1.0
    # AUD-VAL-02: dividendo pago em ano de prejuízo (LPA ≤ 0, DPA > 0). Com o payout agora None
    # nesse caso (multiples.dividend_payout), o teste payout>100% não pega — é armadilha explícita
    # (distribuição de reservas/caixa sem lucro), tratada à parte e somada às salvaguardas do veredito.
    lpa_ult, dpa_ult = c.lpa(ult), c.dpa(ult)
    flag_div_prejuizo = (
        dpa_ult is not None and dpa_ult > 0 and lpa_ult is not None and lpa_ult <= 0
    )

    # --- Veredito ---
    # FIX-06 (item H): a banda intrínseca vmin/vmax = min/max da matriz de SENSIBILIDADE
    # real (Ke×g, já calculada acima), não o toggle binário de 2 cenários (ddm_constante ×
    # ddm_h). A matriz cobre o grid `delta_ke × delta_g` do config — é a sensibilidade
    # econômica de fato (um Ke um pouco menor / g um pouco maior abre o teto da banda).
    celulas_sens = [v for linha in (a.sensibilidade or []) for v in linha if v is not None]
    if celulas_sens:
        a.vmin, a.vmax = min(celulas_sens), max(celulas_sens)
    else:
        # Fallback (T-08-07): matriz só-None / DDM não rodou → degrada para os 2 cenários
        # centrais (ou nada), como antes, sem deixar célula inválida virar banda espúria.
        valores = [r.valor_intrinseco for r in (a.ddm_h, a.ddm_constante) if r]
        if valores:
            a.vmin, a.vmax = min(valores), max(valores)
    # Guarda-corpo de emissão (Achado 2 / SAN-01): antes de qualquer veredito, uma faixa DDM
    # NEGATIVA (vmax<=0) ou DEGENERADA (0–0) é ruído — não preço-alvo. Suprime aqui, read-only
    # sobre o veredito e sem tocar core/ddm.py (borda de emissão apenas).
    _guarda_faixa_ddm(a)

    # --- Ensemble motor × contraponto DDM (Fase 3 v2.2, ENS-01/VER-01, D-01/D-02) ---
    # O DDM que já rodou (banda vmin/vmax = matriz de sensibilidade) é o CONTRAPONTO universal
    # (D-02): captura-se o seu mid ANTES de a banda ser sobrescrita. Então, SOMENTE quando o
    # motor do arquétipo NÃO é o DDM e calculou um intrínseco, a banda do veredito passa a vir
    # do ENSEMBLE — min/max entre o motor primário e o contraponto (D-01). Fallback D-01: se o
    # contraponto degradou (DDM suprimido/None), a banda = intrínseco ± margem de segurança
    # config-driven (leitura defensiva do knob, paridade WR-03 com o dispatch do motor). O
    # helper puro `divergencia_entre_lentes` (comparables, never-raise, limiar 2×) sinaliza a
    # divergência sem inventar número reconciliado. motor == "ddm" (TAEE11): NADA é acionado.
    if a.vmin is not None and a.vmax is not None:
        a.contraponto_valor = (a.vmin + a.vmax) / 2.0
    contraponto = a.contraponto_valor
    if a.motor != "ddm" and a.intrinseco_motor is not None:
        if contraponto is not None:
            a.vmin = min(a.intrinseco_motor, contraponto)
            a.vmax = max(a.intrinseco_motor, contraponto)
        else:
            margem = (cfg or {}).get("veredito", {}).get("margem_seguranca", 0.15)
            a.vmin = a.intrinseco_motor * (1.0 - margem)
            a.vmax = a.intrinseco_motor * (1.0 + margem)
        a.banda_do_motor = True
        a.divergencia_ativa, a.divergencia_razao = comparables.divergencia_entre_lentes(
            a.intrinseco_motor, contraponto
        )
        if a.divergencia_ativa:
            a.divergencia_hipotese = _hipotese_divergencia(
                a.arquetipo, a.intrinseco_motor, contraponto, a.divergencia_razao
            )

    # --- Veredito de preço (VER-01): árvore SUB/NO INTERVALO/SOBRE ÚNICA p/ ddm e não-ddm ---
    # A suspensão D-06 (`if a.motor != "ddm": → VERIFICAR`) foi SUBSTITUÍDA: a banda do motor
    # (ensemble, acima) já alimenta vmin/vmax, então a MESMA comparação preço×banda que o DDM
    # usava passa a servir também os arquétipos não-DDM — o selo consome o motor CERTO, não o
    # DDM fixo (VER-01). As flags de risco (VULC3) continuam vetando "SUBAVALIADA" e emitindo
    # "possível divergência de modelo" TAMBÉM no caminho do motor. Ramo terminal de degradação:
    # motor != "ddm" SEM banda (intrínseco None E DDM suprimido) → prefixo VERIFICAR (selo
    # suprime faixa, selo.py:119), nunca faixa falsa. motor == "ddm": comportamento inalterado.
    if a.vmin is not None and a.vmax is not None and a.preco_atual:
        if a.preco_atual < a.vmin:
            # DDM-FIX-05 (caso VULC3): não rotular "SUBAVALIADA" quando flags de risco
            # contradizem a tese de desconto. Preço abaixo do intrínseco + payout>100% ou
            # DY>15% costuma ser divergência de modelo / armadilha, não barganha. Preservado
            # também no caminho do motor (test_vulc3_regressao).
            if flag_payout or flag_dy or flag_div_prejuizo:
                motivos = []
                if flag_payout:
                    motivos.append("payout > 100%")
                if flag_div_prejuizo:
                    motivos.append("dividendo pago em ano de prejuízo")
                if flag_dy:
                    motivos.append("DY > 15%")
                a.veredito = (
                    f"VERIFICAR — preço R$ {_br(a.preco_atual)} abaixo do intervalo intrínseco "
                    f"R$ {_br(a.vmin)}–{_br(a.vmax)}, mas sinais de risco ({', '.join(motivos)}) "
                    f"contradizem a tese de desconto: possível divergência de modelo."
                )
            else:
                a.veredito = f"SUBAVALIADA — preço R$ {_br(a.preco_atual)} abaixo do intervalo intrínseco R$ {_br(a.vmin)}–{_br(a.vmax)}"
        elif a.preco_atual > a.vmax:
            a.veredito = f"SOBREAVALIADA — preço R$ {_br(a.preco_atual)} acima do intervalo intrínseco R$ {_br(a.vmin)}–{_br(a.vmax)}"
        else:
            a.veredito = f"NO INTERVALO — preço R$ {_br(a.preco_atual)} dentro de R$ {_br(a.vmin)}–{_br(a.vmax)}"
        # Alerta honesto: onde o MOTOR do arquétipo alimenta o veredito, o DDM é a lente
        # conservadora (contraponto), não o motor deste perfil (VER-01). motor == "ddm" não
        # emite este alerta (banda_do_motor False) — TAEE11 idêntica.
        if a.banda_do_motor:
            a.alertas.append(
                f"Motor primário do arquétipo = {a.motor_rotulo or a.motor}; o DDM é exibido "
                f"como lente conservadora (contraponto), não como o motor deste perfil (VER-01)."
            )
    elif a.motor != "ddm":
        # Degradação honesta: motor não-DDM sem banda de preço (intrínseco None E DDM suprimido,
        # ou sem preço atual). Reusa o prefixo VERIFICAR — selo.montar_selo (selo.py:119) suprime
        # faixa/rótulo → nunca estampa faixa falsa, sem tocar selo.py.
        if a.intrinseco_motor is not None:
            a.veredito = (
                f"VERIFICAR — arquétipo {a.arquetipo}: referência primária pelo intrínseco ≈ "
                f"R$ {_br(a.intrinseco_motor)} ({a.motor_rotulo or a.motor}); sem preço-alvo comparável."
            )
        else:
            a.veredito = (
                f"VERIFICAR — motor '{a.motor}' ({a.motor_rotulo or a.motor}) não pôde estimar "
                f"preço-alvo para o arquétipo {a.arquetipo}."
            )
        a.alertas.append(
            f"Roteamento: {a.arquetipo} → motor '{a.motor}'. Banda de preço indisponível "
            f"(motor e DDM degradaram); veredito de preço suspenso sem estampar faixa falsa."
        )

    # --- VER-02: caso-fronteira → assume a dúvida (range dos candidatos + bandeira) ---
    # Precedência sobre o VER-01: quando a Fase 1 marcou conflito real de sinais
    # (`arquetipo_fronteirico`), a classificação em si é incerta, então NÃO se crava um selo
    # único — roda o motor de cada candidato e sobrescreve o veredito com o range [menor..maior]
    # + a bandeira "classificação incerta entre X e Y" (prefixo VERIFICAR suprime a faixa do selo,
    # selo.py:119). Não-fronteiriço: nada roda; o veredito do VER-01 segue mandando.
    if a.arquetipo_fronteirico:
        _veredito_fronteirico(a, c, cfg)

    # --- Guarda-corpo anti-aberração SAN-01 (Plan 03-02) ---
    # Roda DEPOIS de a cadeia de veredito estar montada e ANTES de `montar_selo` (abaixo), de
    # modo que o selo consuma o veredito JÁ reetiquetado. No funil single-stock não há regressão
    # de pares ajustada → `valor_pares=None` (degradação D-04): o gate cai para as 2 condições
    # (ROE E corte de payout) e NUNCA puxa rede (custo-zero). Se disparar, o prefixo do veredito
    # reetiquetado não casa `selo.faixa_do_veredito` → o selo não estampa "Evitar".
    _guarda_san01(a, c, cfg, valor_pares=None)

    # --- Alertas / armadilhas de dividendos (Cap. 6) ---
    if flag_dy:
        a.alertas.append("DY > 15%: possível armadilha de dividendos (Cap. 6) — verificar sustentabilidade.")
    if flag_payout:
        a.alertas.append("Payout > 100%: distribui mais que o lucro (reservas) — insustentável no longo prazo.")
    if flag_div_prejuizo:
        a.alertas.append("Dividendo pago em ano de prejuízo (LPA ≤ 0): distribuição de reservas/caixa sem lucro — armadilha de dividendos (Cap. 6).")
    if not lucro_positivo:
        a.alertas.append("Prejuízo em algum ano da janela: fundamentos inconsistentes para dividendos.")
    if a.ke is None:
        a.alertas.append("Beta indisponível: não foi possível calcular Ke nem o DDM.")
    elif a.ddm_constante is None:
        # AUD-VAL-03: Ke existe mas o DDM não rodou — algum outro insumo está None. Não some
        # em silêncio (Core Value): nomeia o que faltou em vez de exibir a tela sem veredito.
        faltou = []
        if lpa is None:
            faltou.append("LPA normalizado")
        if payout_proj is None:
            faltou.append("payout sustentável")
        if a.g_alto is None:
            faltou.append("crescimento (g)")
        if a.ke is not None and a.ke <= g_estavel:
            faltou.append("Ke ≤ g estável (perpetuidade não converge)")
        motivo = ", ".join(faltou) if faltou else "insumo de valuation indisponível"
        a.alertas.append(f"DDM não calculado ({motivo}): sem valor intrínseco nem veredito.")
    ano_base = cfg.get("universo", {}).get("ano_base")
    if ano_base is not None and ult is not None and ult < ano_base:
        a.alertas.append(
            f"Ainda sem DFP de {ano_base} na CVM para esta empresa; análise usa fundamentos até {ult}."
        )

    # --- Read técnico consultivo (timing de entrada) — TIMING-01/04, ponto único CLI/UI ---
    # Passo 1: base temporal (D-10/D-12). Resample W-FRI quando "semanal" (default),
    # sobre o frame split-adjusted (CR-01, NUNCA c.ohlc). Sem segundo guard de None/curto —
    # indicators.calcular já degrada frame vazio para "indisponivel" (ponto único, DATA-03).
    base = cfg.get("indicadores", {}).get("base_temporal", "semanal")
    ohlc = c.ohlc_ajustado
    # WR-01: o resample só roda quando o frame é realmente datetime-indexado e tem as
    # colunas OHLC; caso contrário cai no frame original e a degradação de
    # indicators.calcular (ponto único) cuida do resto, sem TypeError/KeyError aqui.
    if (
        base == "semanal"
        and ohlc is not None
        and len(ohlc) > 0
        and isinstance(ohlc.index, pd.DatetimeIndex)
        and set(indicators._COLUNAS_OHLC).issubset(ohlc.columns)
    ):
        ohlc = ohlc.resample("W-FRI").agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
        ).dropna()
    # Passo 2: popular os sinais (calcular sempre devolve um SinaisTecnicos).
    a.sinais = indicators.calcular(ohlc, cfg)

    # Passo 3: árvore de decisão composite (D-01/D-02/D-03) — MM200 dá a direção,
    # ADX confirma a força. Lê os rótulos JÁ classificados (não relê o float do ADX).
    pos = a.sinais.tendencia.posicao_mm200
    forca = a.sinais.forca.forca_adx
    if pos == "indisponivel" or forca == "indisponivel":
        a.timing_estado = "sem_tendencia"      # degradação graciosa (DATA-03), sem exceção
        a.timing_resumo = ""
    elif pos == "acima" and forca == "forte":
        a.timing_estado = "tendencia_de_alta"
        resumo = "Tendência de alta confirmada (preço acima da MM200, ADX forte)"
        # Passo 4: matiz fino (D-03) — RSI/MACD refinam a frase, NUNCA mudam o estado.
        if a.sinais.momentum.nivel_rsi == "sobrecomprado":
            resumo += " — porém sobrecomprado; pode valer esperar um pullback."
        else:
            resumo += "."
        a.timing_resumo = resumo
    elif pos == "abaixo":
        a.timing_estado = "atencao"
        resumo = "Atenção: preço abaixo da MM200 (viés de baixa)"
        if a.sinais.momentum.cruzamento_macd == "cruz_baixa":
            resumo += " — cruzamento de baixa do MACD reforça o sinal."
        else:
            resumo += "."
        a.timing_resumo = resumo
    else:  # acima da MM200 mas ADX fraco/neutro — caso-limite canônico D-02/TEST-06
        a.timing_estado = "sem_tendencia"
        a.timing_resumo = (
            "Sem tendência definida (lateral / força fraca) — não é timing de entrada confirmado."
        )

    # --- Matriz fundamento×técnico (TIMING-02) e alerta de reverificação (TIMING-03) ---
    # Ambos read-only sobre o fundamento: LÊEM a.veredito/a.sinais já calculados, sem
    # recalcular nem tocar veredito/vmin/vmax. Helpers puros p/ travar por golden direto.
    a.matriz_leitura = _matriz_leitura(a.veredito, a.timing_estado)
    # CR-01: degradação HOLÍSTICA — quando o read técnico degrada (timing_resumo vazio),
    # nenhum derivado pode afirmar um estado fabricado. A matriz colapsa junto com o timing,
    # mesmo que o estado tenha caído para "sem_tendencia" e o veredito DDM esteja preenchido.
    if not a.timing_resumo:
        a.matriz_leitura = ""
    a.alerta_reverificacao = _alerta_reverificacao(a.sinais)

    # --- Selo de Sustentabilidade × veredito de preço (Fase 20, SELO-01/02) ---
    # Derivação read-only: cruza o BSD desta empresa (bsd_empresa, puro sobre o CompanyData
    # já carregado — NÃO toca a rede) com o veredito de preço JÁ montado. Never-raise: se
    # qualquer parte falhar, a.selo fica None e o veredito fundamentalista segue intacto (T-20-02).
    try:
        bsd = screening.bsd_empresa(c, cfg)
        a.selo = selo_mod.montar_selo(bsd, a.veredito, cfg)
    except Exception:
        a.selo = None

    return a


# --------------------------------------------------------------------------- #
# Matriz fundamento×técnico e alerta de reverificação (Phase 6 Plan 02)
# --------------------------------------------------------------------------- #
# Frase CURADA por célula (token do veredito × estado técnico), NÃO um template
# composicional (D-04). O fundamento sempre lidera a frase (garante UI-06). As duas
# células-âncora têm texto VERBATIM (CONTEXT D-05 / D-06).
_MATRIZ_LEITURA: Dict[tuple, str] = {
    # Célula-âncora D-05 (verbatim) — liga direto ao alerta de reverificação.
    ("SUBAVALIADA", "atencao"):
        "Fundamentalmente descontada, porém o preço perdeu a tendência — "
        "confirme que os fundamentos seguem intactos antes de entrar.",
    ("SUBAVALIADA", "tendencia_de_alta"):
        "Fundamentalmente descontada e tecnicamente em alta — os dois lados "
        "conversam; ainda assim confirme os fundamentos antes de entrar.",
    ("SUBAVALIADA", "sem_tendencia"):
        "Fundamentalmente descontada, porém sem tendência técnica definida — "
        "o desconto é do método; a entrada pode esperar confirmação de força.",
    ("NO INTERVALO", "tendencia_de_alta"):
        "Dentro do intervalo justo; tecnicamente em alta — acompanhe, "
        "sem prêmio de desconto.",
    ("NO INTERVALO", "sem_tendencia"):
        "Dentro do intervalo justo e sem tendência técnica definida — "
        "preço próximo do valor; nada a fazer pelo método agora.",
    ("NO INTERVALO", "atencao"):
        "Dentro do intervalo justo, mas o preço perdeu a tendência — "
        "reveja os fundamentos antes de qualquer decisão.",
    # Célula-âncora D-06 (verbatim) — o fundamento veta a euforia técnica.
    ("SOBREAVALIADA", "tendencia_de_alta"):
        "Tecnicamente em alta, porém acima do valor intrínseco — "
        "o método não compra caro; aguarde um preço melhor.",
    ("SOBREAVALIADA", "sem_tendencia"):
        "Acima do valor intrínseco e sem tendência técnica de suporte — "
        "o método não paga caro; aguarde um preço melhor.",
    ("SOBREAVALIADA", "atencao"):
        "Acima do valor intrínseco e com o preço perdendo tendência — "
        "o método já não compraria caro; sem pressa.",
}


# --------------------------------------------------------------------------- #
# Hipótese de divergência motor × contraponto DDM (Fase 3 v2.2, ENS-01/D-03)
# --------------------------------------------------------------------------- #
# Copy CURADA por (arquétipo, sinal da divergência) — mesmo padrão do _MATRIZ_LEITURA acima e
# do _MATRIZ do selo.py: dicionário-curado por tupla-chave, estável e testável por golden. O
# "porquê" da bandeira (brief ENS-01) é exibido, nunca escondido cravando o pior número. Sinal:
# "motor_acima" quando o intrínseco do motor > contraponto DDM; "motor_abaixo" caso contrário.
_HIPOTESE_DIVERGENCIA: Dict[tuple, str] = {
    ("financeira", "motor_acima"):
        "compounder subvalorizado pelo DDM (o Ke alto comprime o DDM de estágio único; o RIM "
        "captura o excesso de ROE sobre o Ke que o DDM não enxerga).",
    ("ciclica", "motor_abaixo"):
        "possível topo de ciclo (o lucro do ano corrente está acima do lucro mid-cycle "
        "normalizado, inflando o DDM acima do valor do motor).",
    ("crescimento", "motor_acima"):
        "crescimento subestimado pelo DDM de estágio único (o DCF multi-estágio precifica o "
        "reinvestimento de alto ROE que o DDM não captura).",
}


def _hipotese_divergencia(
    arquetipo: str,
    intrinseco_motor: Optional[float],
    contraponto: Optional[float],
    razao: Optional[float],
) -> str:
    """Frase curada por (arquétipo, sinal da divergência); fallback genérico quando a tupla não
    resolve (D-03). Puro/read-only — não toca a rede nem recalcula método."""
    if intrinseco_motor is None or contraponto is None:
        sinal = ""
    else:
        sinal = "motor_acima" if intrinseco_motor > contraponto else "motor_abaixo"
    frase = _HIPOTESE_DIVERGENCIA.get((arquetipo, sinal))
    if frase:
        return frase
    r = razao if razao is not None else 0.0
    return f"modelos divergem ~{r:.1f}× — ver as duas referências (motor × DDM)."


def _veredito_token(veredito: str) -> str:
    """Token líder do veredito DDM (read-only). '' se o DDM não calculou."""
    for t in ("SUBAVALIADA", "SOBREAVALIADA", "NO INTERVALO"):
        if veredito.startswith(t):
            return t
    return ""


def _matriz_leitura(veredito: str, timing_estado: str) -> str:
    """Frase curada fundamento-primeiro (D-04). '' se veredito vazio (degradação)."""
    token = _veredito_token(veredito)
    if not token:
        return ""
    return _MATRIZ_LEITURA.get((token, timing_estado), "")


def _alerta_reverificacao(sinais: Optional["indicators.SinaisTecnicos"]) -> Optional[str]:
    """OR dos três gatilhos de baixa (D-07), consolidado numa única mensagem (D-09),
    voz "reverifique os fundamentos" — NUNCA "venda". Dispara independente do veredito
    (D-08). None quando nenhum gatilho aciona (inclui sinais "indisponivel")."""
    if sinais is None:
        return None
    gatilhos: List[str] = []
    if sinais.tendencia.posicao_mm200 == "abaixo":
        gatilhos.append("preço abaixo da MM200")
    if sinais.tendencia.cruzamento == "death_cross":
        gatilhos.append("cruzamento de baixa MM50×MM200")
    if sinais.canais.rompimento_donchian == "perda_minima":
        gatilhos.append("rompimento da mínima do canal")
    if not gatilhos:
        return None
    return (
        "Reverifique os fundamentos: " + "; ".join(gatilhos)
        + ". Não é sinal de venda — confirme se os números seguem intactos."
    )


# --------------------------------------------------------------------------- #
# Renderização Markdown
# --------------------------------------------------------------------------- #
def _pct(x: Optional[float]) -> str:
    return "-" if x is None else f"{x*100:.1f}%"


def _num(x: Optional[float], casas: int = 2) -> str:
    return "-" if x is None else f"{x:.{casas}f}"


def _br(x: float, casas: int = 2) -> str:
    """Número no padrão ptBR (milhar '.', decimal ',') para o veredito exibido no app
    (banner), consistente com fmt_rs de app.py/presentation.py. Só FORMATA — nenhum valor
    muda. Distinto de _num (superfície CLI, ponto decimal)."""
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def relatorio_markdown(c: CompanyData, a: AnaliseAcao, cfg: dict) -> str:
    L: List[str] = []
    L.append(f"# Análise de Dividendos — {a.ticker} ({a.nome})")
    L.append("")
    L.append(f"*Setor:* {a.setor or '-'}  |  *Preço atual:* R$ {_num(a.preco_atual)}  "
             f"|  *Estágio (ciclo de vida):* {a.estagio}  "
             f"|  *Arquétipo:* {a.arquetipo or '-'} → motor {a.motor or '-'}")
    L.append("")
    L.append("> Metodologia: Orleans Martins & Felipe Pontes, *O Investidor em Ações de Dividendos*. "
             "Dados gratuitos: CVM (fundamentos), Yahoo/yfinance (preços e dividendos), BCB (Selic/IPCA).")
    L.append("")

    # Fundamentos
    L.append("## Fundamentos (por ano)")
    anos = c.anos_ordenados()
    linhas = []
    for ano in anos:
        linhas.append([
            ano,
            _num(c.lucro_liquido.get(ano) and c.lucro_liquido[ano] / 1e6, 0),
            _num(c.patrimonio_liquido.get(ano) and c.patrimonio_liquido[ano] / 1e6, 0),
            _num(c.fco.get(ano) and c.fco[ano] / 1e6, 0),
            _pct(c.roe(ano)),
            _pct(c.payout(ano)),
        ])
    L.append(tabulate(linhas, headers=["Ano", "LL (R$ mi)", "PL (R$ mi)", "FCO (R$ mi)",
                                       "ROE", "Payout"], tablefmt="github"))
    L.append("")

    # Múltiplos
    L.append("## Múltiplos (Cap. 10)")
    mlin = []
    for k, v in a.multiplos.items():
        if k in ("ML", "ROE", "DP (payout)", "DY", "DY rec.", "EY"):
            mlin.append([k, _pct(v)])
        else:
            mlin.append([k, _num(v)])
    L.append(tabulate(mlin, headers=["Múltiplo", "Valor"], tablefmt="github"))
    L.append("")

    # Crescimento e custo de capital
    L.append("## Crescimento e custo de capital (Cap. 14 e 16)")
    L.append(f"- g histórico (tendência log-linear): **{_pct(a.g_historico)}**")
    L.append(f"- g por fundamentos (ROE × retenção): **{_pct(a.g_fundamentos)}**")
    L.append(f"- g alto adotado: **{_pct(a.g_alto)}**  |  g estável (perpetuidade): **{_pct(a.g_estavel)}**")
    L.append(f"- Beta: **{_num(a.beta)}**  |  Ke (CAPM): **{_pct(a.ke)}**")
    L.append("")

    # Intrínseco pelo MOTOR do arquétipo (Fase 2 v2.2, D-06): onde o motor não é o DDM, o
    # intrínseco do motor certo é a referência PRIMÁRIA e o DDM abaixo vira lente conservadora.
    # Só EXIBIÇÃO (render mínimo, Open Question 2): não toca cálculo nem bandeira de divergência.
    ddm_e_lente = a.motor != "ddm"
    if ddm_e_lente and a.intrinseco_motor is not None:
        L.append(f"## Valuation pelo motor do arquétipo ({a.arquetipo})")
        L.append(f"- **{a.motor_rotulo or a.motor}: R$ {_num(a.intrinseco_motor)}** (motor do arquétipo)")
        L.append("")

    # DDM
    L.append("## Valuation por Desconto de Dividendos (Cap. 13-17)")
    if ddm_e_lente:
        L.append("_(lente conservadora — não é o motor deste arquétipo)_")
        L.append("")
    if a.ddm_inaplicavel:
        # Achado 2 / SAN-01: o DDM rodou mas devolveu faixa negativa/zero — inaplicável a este
        # perfil. Nota honesta em vez da tabela (distinta de "_DDM não calculado_" = faltou
        # insumo). Não estampa R$ negativo nem 0,00 como intrínseco.
        L.append("_DDM estruturalmente inaplicável a este perfil (payout baixo / alto capex ou "
                 "lucro negativo): a faixa por dividendos resultou negativa ou zero e NÃO é "
                 "preço-alvo — por isso não é exibida._")
        L.append("")
    elif a.ddm_constante and a.ddm_h:
        L.append(tabulate([
            ["Otimista (g constante)", f"R$ {_num(a.ddm_constante.valor_intrinseco)}",
             f"R$ {_num(a.ddm_constante.vp_dividendos)}", f"R$ {_num(a.ddm_constante.vp_residual)}",
             _pct(a.ddm_constante.peso_residual)],
            ["Conservador (modelo H)", f"R$ {_num(a.ddm_h.valor_intrinseco)}",
             f"R$ {_num(a.ddm_h.vp_dividendos)}", f"R$ {_num(a.ddm_h.vp_residual)}",
             _pct(a.ddm_h.peso_residual)],
        ], headers=["Cenário", "Valor intrínseco", "VP dividendos", "VP residual",
                    "% residual"], tablefmt="github"))
        L.append("")
        # Sensibilidade
        if a.sensibilidade:
            sens = cfg["ddm"]["sensibilidade"]
            header = ["Ke \\ g"] + [_pct(a.g_alto + dg) for dg in sens["delta_g"]]
            slin = []
            for i, dke in enumerate(sens["delta_ke"]):
                row = [_pct((a.ke or 0) + dke)] + [
                    f"R$ {_num(v)}" for v in a.sensibilidade[i]
                ]
                slin.append(row)
            L.append("**Matriz de sensibilidade do valor intrínseco (Ke × g):**")
            L.append("")
            L.append(tabulate(slin, headers=header, tablefmt="github"))
            L.append("")
    else:
        L.append("_DDM não calculado (faltam Beta/Ke, payout ou crescimento)._")
        L.append("")

    # Veredito
    L.append("## Veredito")
    L.append(f"**{a.veredito or 'Indeterminado'}**")
    # Guarda-corpo anti-aberração SAN-01 (Plan 03-02): nota honesta quando o veredito "evitar"
    # foi reetiquetado — o número acima é do motor primário do arquétipo; o DDM de estágio único
    # é conservador demais para este perfil (reetiqueta, não supressão).
    if a.san01_reetiquetado:
        L.append("")
        L.append(
            "_Guarda-corpo anti-aberração (SAN-01): veredito reetiquetado — a referência "
            "primária é o motor do arquétipo (número acima); o DDM de estágio único é "
            "conservador demais para este perfil._"
        )
    # Classificação incerta (VER-02, caso-fronteira): quando a Fase 1 marcou conflito real de
    # sinais, o veredito assume a dúvida — LISTA cada candidato e seu intrínseco + a bandeira
    # "classificação incerta entre X e Y" + o range [menor..maior]. Conteúdo EXIBIDO, não selo
    # cravado (o prefixo VERIFICAR já suprime a faixa). Sem fronteiriço, nenhum bloco é emitido.
    if a.arquetipo_incerto:
        L.append("")
        L.append("### Classificação incerta (caso-fronteira)")
        if a.candidatos_intrinsecos:
            for cand, val in a.candidatos_intrinsecos:
                L.append(f"- {cand}: R$ {_num(val)} (motor do arquétipo {cand})")
            primeiro = a.candidatos_intrinsecos[0][0]
            ultimo = a.candidatos_intrinsecos[-1][0]
            L.append("")
            L.append(f"Classificação incerta entre {primeiro} e {ultimo} — a ferramenta assume a dúvida em vez de cravar um selo.")
            if a.veredito_range is not None:
                menor, maior = a.veredito_range
                L.append(f"Range do intrínseco conforme o arquétipo assumido: R$ {_num(menor)}–{_num(maior)}.")
        else:
            L.append("Os motores dos arquétipos candidatos não estimaram preço-alvo confiável.")

    # Bandeira de divergência (ENS-01): quando o motor e o contraponto DDM discordam além do
    # limiar (2×), EXIBIR os dois números + o "porquê" — divergência é informação mostrada,
    # nunca escondida cravando o pior. Sem divergência ativa, nenhum bloco é emitido (render limpo).
    if a.divergencia_ativa:
        L.append("")
        L.append("### Bandeira de divergência")
        L.append(
            f"As lentes divergem ~{_num(a.divergencia_razao, 1)}×: "
            f"**{a.motor_rotulo or a.motor} R$ {_num(a.intrinseco_motor)}** "
            f"× DDM (lente conservadora) R$ {_num(a.contraponto_valor)}."
        )
        if a.divergencia_hipotese:
            L.append(f"Hipótese: {a.divergencia_hipotese}")
    if a.alertas:
        L.append("")
        L.append("### Alertas")
        for al in a.alertas:
            L.append(f"- ⚠️ {al}")
    L.append("")

    # Sinais técnicos (consultivos) — espelha o read da engine (CLI-01 / D-13).
    # Paridade CLI↔UI gratuita (ambos consomem a.sinais/analisar_acao, ponto único).
    L.append("## Sinais técnicos (consultivos)")
    if a.sinais is None or not a.timing_resumo:
        # Degradação graciosa (DATA-03), espelha o fallback do DDM. A guarda por
        # `not a.timing_resumo` (IN-01: remove a condição morta timing_estado=="") cobre
        # também o caso só-de-força (ADX indisponível com MM200 disponível, CR-01).
        L.append("_Histórico de preços insuficiente para o read técnico._")
        L.append("")
    else:
        L.append(f"**Timing de entrada:** {a.timing_resumo}")
        L.append("")
        if a.matriz_leitura:                    # IN-02: sem linha em branco espúria
            L.append(a.matriz_leitura)          # fundamento-primeiro (D-04)
        if a.alerta_reverificacao:
            L.append("")
            L.append(f"- ⚠️ {a.alerta_reverificacao}")
        L.append("")

    return "\n".join(L)
