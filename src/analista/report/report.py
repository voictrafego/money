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

from ..core import arquetipo, capm, ddm, growth, indicators, lifecycle, screening
from ..core import multiples as mult
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
    motor_pendente: bool = False                           # True quando o motor do arquétipo chega só na Fase 2 (D-04)
    # --- Fase 3 v2.2 (Achado 2 / SAN-01): guarda-corpo do DDM ---
    ddm_inaplicavel: bool = False                          # True quando a faixa DDM saiu negativa/degenerada (suprimida na borda)


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
    a.motor_pendente = motor is None

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
    if a.motor_pendente:
        # Suspensão D-04: o arquétipo deste negócio NÃO tem motor primário na Fase 1
        # (financeira→RIM, crescimento→DCF, cíclica→lucro normalizado, holding→SOTP chegam
        # na Fase 2). NÃO estampar um veredito de preço por um modelo (DDM de estágio único)
        # que não serve a este perfil — é o erro de arquitetura do ITUB4. Reusa o PREFIXO
        # existente "VERIFICAR" (Pitfall 3): selo.montar_selo (selo.py:119) já suprime
        # faixa/rótulo nesse prefixo → não estampa 'evitar', sem tocar selo.py. Guard
        # GENÉRICO por motor_pendente (não condicionado a arquetipo == financeira).
        a.veredito = (
            f"VERIFICAR — arquétipo {a.arquetipo} usa o motor '{a.motor}', que chega na "
            f"Fase 2; o DDM abaixo é lente conservadora, não o motor deste perfil. "
            f"Referências: Graham/Bazin."
        )
        a.alertas.append(
            f"Roteamento: {a.arquetipo} → motor pendente (Fase 2). Veredito de preço suspenso "
            f"para não estampar selo por um modelo que não serve a este perfil (D-04)."
        )
    elif a.vmin is not None and a.vmax is not None and a.preco_atual:
        if a.preco_atual < a.vmin:
            # DDM-FIX-05 (caso VULC3): não rotular "SUBAVALIADA" quando flags de risco
            # contradizem a tese de desconto. Preço abaixo do intrínseco + payout>100% ou
            # DY>15% costuma ser divergência de modelo / armadilha, não barganha.
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

    # DDM
    L.append("## Valuation por Desconto de Dividendos (Cap. 13-17)")
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
