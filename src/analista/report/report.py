"""Relatório do analista: amarra múltiplos (Cap. 10), crescimento (Cap. 14),
CAPM (Cap. 16) e DDM (Cap. 13-17) em um parecer por ação, com veredito.

A regressão de comparáveis (Cap. 11/12) entra no fluxo por setor (comando `rank`),
pois exige um conjunto de pares; aqui o foco é o valuation por desconto de dividendos.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd
from tabulate import tabulate

from ..core import arquetipo, capm, ddm, growth, indicators, lentes, lifecycle, motores, screening
from ..core import multiples as mult
from ..core import normalizacao as norm
from ..core import valuation
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
    # --- Fase 1 v2.2 / ENG-01 (Fase 13): roteamento por arquétipo → RIM único (aditivo, read-only) ---
    arquetipo: str = ""                                    # chave do classificador (core/arquetipo)
    motor: str = ""                                        # caminho ÚNICO de valor (ENG-01): sempre "rim"
    arquetipo_candidatos: List[str] = field(default_factory=list)  # candidatos do funil (debug do classificador)
    # --- Fase 2 v2.2: intrínseco pelo RIM único do arquétipo (motor CALCULA e EXIBE, D-06) ---
    intrinseco_motor: Optional[float] = None               # valor intrínseco pelo RIM único (None se degradou, never-raise)
    motor_rotulo: str = ""                                  # rótulo humano do motor (motores.MOTOR_ROTULO)
    # --- Fase 13 / plano 13-04: ponte P/B auditável (ENG-08, decomposição steady-state exibível) ---
    pb_justo: Optional[float] = None                       # P/B justo implícito = 1+(ROE_T−Ke)/(Ke−g_T) (lente, não motor)
    v_ponte: Optional[float] = None                        # V da ponte = pb_justo × VPA0 (sanidade da razão, não substitui o RIM)
    payout_terminal: Optional[float] = None                # payout terminal implícito = 1 − g_T/ROE_T
    razao_patologica: bool = False                         # True quando a razão implícita é patológica (ENG-09/D-10b): guard degrada o veredito
    # --- Fase 3 v2.2 (Achado 2 / SAN-01): guarda-corpo do DDM (secundário, não alimenta o veredito) ---
    ddm_inaplicavel: bool = False                          # True quando a faixa DDM saiu negativa/degenerada (suprimida na borda)


def _roe_through_cycle(c: CompanyData, rim_cfg: dict) -> Optional[float]:
    """ROE normalizado through-cycle (Alavanca 2/D-01) — anchor do RI TERMINAL do RIM.

    Ancora o excesso da perpetuidade no poder de lucro através do ciclo do PRÓPRIO ticker
    (mediana|média dos `c.roe(ano)` da série), fiel ao método do livro (lucro sustentável, não
    pontual). O anchor sai da SÉRIE (fronteira FIX-04), não é constante mágica — o motor só recebe
    o número. Never-raise: série com <3 pontos válidos → None (degrada para o legado; o 1º ano é
    None por falta de PL−1). Estatística lida do knob `roe_terminal_stat` (mediana é robusta ao
    ROE-colapso de 1 ano — agro 2025 do BBAS3)."""
    serie = [c.roe(a) for a in c.anos_ordenados()]
    validos = [r for r in serie if r is not None]
    if len(validos) < 3:
        return None
    stat = (rim_cfg or {}).get("roe_terminal_stat", "mediana")
    return statistics.mean(validos) if stat == "media" else statistics.median(validos)


def _roe0_ciclico(c: CompanyData, cfg: dict, vpa0: Optional[float]) -> Optional[float]:
    """roe0-âncora da CÍCLICA (política 'normalizado'): LPA normalizado deflacionado / VPA0 (PRIM-04).

    A série de lucro é trazida a REAIS DO ÚLTIMO ANO (deflacionada por IPCA) ANTES da MÉDIA
    through-cycle (`norm.media_ciclo`, NÃO o endpoint Theil-Sen): uma cíclica com prejuízo recente
    vale pela força de lucro do meio do ciclo, não pelo ano atual. Os deflatores são LIDOS de cfg
    (carimbados nos entry points, como o rf_local) — a engine permanece offline/determinística.
    Fallback never-raise: deflatores ausentes/vazios/sem casar ano → série nominal. None se o LPA
    normalizado ou o VPA0 degeneram."""
    if vpa0 is None or vpa0 <= 0:
        return None
    # ENG-10 (Fase 13): a janela da média through-cycle da cíclica migrou de `motores.ciclica.anos_media`
    # para `motores.rim.anos_ciclica` (política de input do RIM único). `winsor` foi deletada (inerte
    # desde PRIM-02): usa o default 0.10 hardcoded, espelho do bloco `normalizacao`.
    cic = (cfg or {}).get("motores", {}).get("rim", {})
    # WR-02: coage as chaves do carimbo para int (round-trip YAML pode entregá-las como string);
    # sem isso `an in defl` casa ZERO anos e a série sai vazia, matando o motor cíclico em silêncio.
    _defl_raw = (cfg or {}).get("macro", {}).get("ipca_deflatores") or {}
    defl = {}
    for _ano, _fator in _defl_raw.items():
        try:
            defl[int(_ano)] = float(_fator)
        except (TypeError, ValueError):
            continue
    ult = c.ultimo_ano()
    serie_lucro = [
        c.lucro_liquido[an] * defl[an]
        for an in c.anos_ordenados()
        if an in c.lucro_liquido and an in defl
    ]
    if not serie_lucro:
        serie_lucro = c.serie("lucro_liquido")
    lpa_norm = mult.lpa(
        norm.media_ciclo(
            serie_lucro,
            anos_media=cic.get("anos_ciclica", 10), winsor=0.10,
        ),
        c.num_acoes.get(ult),
    )
    if lpa_norm is None:
        return None
    return lpa_norm / vpa0


def _derivar_insumo(
    politica: str, c: CompanyData, ke: Optional[float], g_cap: float, rim_cfg: dict, cfg: dict
) -> tuple:
    """Deriva o insumo do RIM único pela política do arquétipo (ENG-01/ENG-03, §Mapa de âncoras).

    Devolve `(roe0, roe_terminal, g_terminal, base_book)`. O RIM é SEMPRE a fórmula; a política só
    escolhe o ROE-âncora da janela e o g terminal:
    - `through_cycle` (financeira/madura): roe0 = mediana through-cycle (`roe_valuation`);
    - `through_cycle_sem_g` (CONCESSAO_FINITA): idem, mas `g_terminal = None` — o carve-out do spike
      13-01 (fade-only, sem g de inflação: sob ICPC 01 o book já capitaliza a receita regulatória, e
      o g_cap embute IPCA → double-count);
    - `normalizado` (cíclica): roe0 = LPA normalizado deflacionado / VPA0;
    - `atual_fade` (crescimento): roe0 = ROE de qualidade ATUAL (endpoint), fade sobre n_fade;
    - `nav_piso` (holding): roe0 = roe_terminal = Ke ⇒ excesso ≡ 0 ⇒ V = book (NAV/piso patrimonial).
    `g_terminal` (exceto o carve-out) = identidade fechada por empresa g_T = max(0, min(ROE_T×ret,
    g_cap)) (GROW-03); usa g_cap quando o ROE through-cycle degrada (None). Never-raise: insumo
    degenerado propaga None (o RIM já é never-raise)."""
    ult = c.ultimo_ano()
    base_book = lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))
    roe_terminal = _roe_through_cycle(c, rim_cfg)
    # Piso 0 (WR-01): payout_valuation NÃO é capado em 1.0 (TAEE11 ≈ 216%), então a retenção pode ser
    # negativa; g_T ∈ [0, g_cap] evita que um g_T < 0 encolha (ou < −1 inverta) o RI terminal.
    retencao = 1.0 - (c.payout_valuation() or 0.0)
    g_T = (max(0.0, min(roe_terminal * retencao, g_cap))
           if roe_terminal is not None else g_cap)

    if politica == "normalizado":
        return _roe0_ciclico(c, cfg, base_book), roe_terminal, g_T, base_book
    if politica == "atual_fade":
        return c.roe_qualidade_atual(), roe_terminal, g_T, base_book
    if politica == "through_cycle_sem_g":
        # Carve-out CONCESSAO_FINITA (spike 13-01): terminal fade-only (g_terminal=None), sem
        # reintroduzir o g de inflação (g_cap embute IPCA → double-count sob ICPC 01).
        return c.roe_valuation(), roe_terminal, None, base_book
    if politica == "nav_piso":
        # HOLDING: piso patrimonial = NAV (VPA). roe0 = roe_terminal = Ke ⇒ excesso ≡ 0 ⇒ V = book.
        return ke, ke, None, base_book
    # "through_cycle" (financeira/madura, default por eliminação).
    return c.roe_valuation(), roe_terminal, g_T, base_book


def _valor_rim(c: CompanyData, a: AnaliseAcao, cfg: dict) -> Optional[float]:
    """Caminho ÚNICO de valor (ENG-01): deriva o insumo pela política do arquétipo e chama SEMPRE
    `motores.rim` com o Ke ÚNICO (`a.ke`, Fase 12) e o g_T fechado (Fase 11) prontos — NÃO recomputa
    Ke/g_cap. Colapsa os antigos 6 ramos (rim/normalizado/dcf/nav/ddm + rota seguradora) num só.
    Never-raise: qualquer insumo degenerado/erro → None (`motores.rim` já é never-raise)."""
    # GROW-01/D-03: g da perpetuidade DERIVADO na engine (nunca digitado) — g_cap =
    # (1+π_ciclo)(1+PIB_real)−1 ≈ 7,28%, a FONTE ÚNICA (D-04). Leitura defensiva (fallback == default).
    g_cap = (1.0 + cfg.get("macro", {}).get("pi_ciclo", 0.0518)) * (
        1.0 + cfg["ddm"].get("pib_real", 0.02)
    ) - 1.0
    rim_cfg = (cfg or {}).get("motores", {}).get("rim", {})
    politica = arquetipo.ARQUETIPO_ANCORA_ROE.get(a.arquetipo, "through_cycle")
    try:
        roe0, roe_terminal, g_terminal, base_book = _derivar_insumo(
            politica, c, a.ke, g_cap, rim_cfg, cfg
        )
        res = motores.rim(
            vpa0=base_book,
            roe0=roe0,
            ke=a.ke,  # KE-01/D-09: Ke ÚNICO já pronto (β setorial+Blume), não recomputa
            retencao=1.0 - (c.payout_valuation() or 0.0),
            n=rim_cfg.get("n_fade", 10),
            excesso_sustentavel=rim_cfg.get("excesso_sustentavel", 0.0),
            g_terminal=g_terminal,
            ke_g_spread_min=rim_cfg.get("ke_g_spread_min", 0.03),
            roe_terminal=roe_terminal,
        )
        return res.valor_intrinseco if res else None
    except Exception:
        return None


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
    # Tendência log-linear (regressão de ln(lucro) sobre o tempo) na série de lucro de
    # valuation (`serie_lucro_normalizada`): usa TODOS os pontos, então o g não é mais
    # endpoint-a-endpoint. PRIM-03/D-04: essa série passou a ser CRUA na Fase 10 (a
    # winsorização temporal saiu; o desenho do g robusto é a Fase 11). O screening consome a
    # MESMA série (crescimento_lucro_3a == g_historico por construção — Core Value).
    lucros_raw = c.serie("lucro_liquido")
    lucros = c.serie_lucro_normalizada()
    if len(lucros) >= 2:
        a.g_historico = growth.crescimento_log_linear(lucros)
    # g_fundamentos usa o MESMO payout do valuation (payout_valuation) ⇒ é o g SUSTENTÁVEL,
    # quanto a empresa consegue reinvestir: g_fund = ROE_normalizado × (1 − payout_valuation).
    a.g_fundamentos = growth.crescimento_por_fundamentos(c.roe_valuation(), c.payout_valuation())
    # GROW-01/D-03: g da perpetuidade DERIVADO (nunca digitado) — g_cap = (1+π_ciclo)(1+PIB_real)−1
    # ≈ 7,28%. Carrega em a.g_estavel o valor derivado (para os rótulos); é a FONTE ÚNICA (D-04)
    # do crescimento terminal. Leitura defensiva: o fallback == default do config (idêntico).
    g_cap = (1.0 + cfg.get("macro", {}).get("pi_ciclo", 0.0518)) * (
        1.0 + cfg["ddm"].get("pib_real", 0.02)
    ) - 1.0
    a.g_estavel = g_cap
    # GROW-04/D-01: a fase explícita ADOTA o g por fundamentos (método do livro, Cap. 14.3;
    # ITUB4 ~10,29% ≈ 10,24% do livro), em vez de subordiná-lo ao histórico. O g_historico deixa
    # de ser teto e vira número de SANIDADE exibido + FALLBACK (quando g_fundamentos é None).
    # Precedência: g_fund (sustentável) → teto absoluto 0.25 → trava ≤ Ke (FIX-01, abaixo). O
    # g_cap (~7,28%) trava SÓ o terminal, NUNCA a fase explícita (D-02): a estrutura de dois
    # estágios do livro — g alto → fade → g terminal ≤ g_cap — não pode ser colapsada num teto só.
    # Payout ≥ 100% (ou ROE não positivo) ⇒ g_fund ≤ 0 ⇒ g_alto cai para 0.
    g_alto = a.g_fundamentos if a.g_fundamentos is not None else a.g_historico
    if g_alto is not None:
        g_alto = max(0.0, min(g_alto, 0.25))  # teto absoluto 25% a.a. (inalterado); nunca < 0
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
            # KE-01/KE-03 (Fase 12): Ke ÚNICO — o β de entrada é o setorial+Blume
            # (capm.beta_blume, carimbado em cfg["capm"]["beta_setorial"] pelos entry
            # points), não o β cru. Este a.ke é O Ke exibido, o que alimenta o RIM (L261,
            # não recomputa) e o centro da matriz de sensibilidade — colapsando o antigo Ke
            # estrutural do RIM (função deletada): a perpetuidade converge pelo piso do Blume, por
            # aritmética, NÃO por clamp (KE-04). ERP segue 0,06 aqui (o corte p/ 0,045 e a
            # remoção das folhas erp_banco/ke_piso/ke_teto é o Plano 03, com o lock).
            a.ke = capm.ke_local(
                capm.beta_blume(c.beta, c.setor, cap.get("beta_setorial")),
                cap["rf_local"],
                cap["erp_local"],
            )
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
    a.arquetipo_candidatos = arq.candidatos
    # ENG-01 (Fase 13): caminho ÚNICO de valor — TODO arquétipo roda o RIM (a política do arquétipo
    # só varia o insumo). O registry legado arquétipo→motor foi deletado (Plano 06); a.motor é sempre
    # "rim" (a rota própria de seguradora e os rótulos ddm/normalizado/dcf/nav morreram, junto com o
    # ensemble motor×contraponto e as guardas-cicatriz).
    a.motor = "rim"

    # --- Dispatch do motor do arquétipo (Fase 2 v2.2, ENG-02..05) ---
    # O motor primário resolvido CALCULA e GRAVA o intrínseco do arquétipo (D-06: motor
    # calcula e EXIBE; o selo NÃO consome ainda — VER-01/Fase 3). Consome SEMPRE os números
    # já-síntese (*_valuation / base_normalizada / lentes.vpa), NUNCA o cru (Pitfall 2/FIX-04).
    # Motores são never-raise (devolvem None sob dado degenerado). O bloco DDM abaixo continua
    # rodando SEMPRE (agora como lente conservadora onde motor != "ddm") — cálculo intocado.
    # Leitura defensiva dos knobs do motor (paridade com classificar): config antigo sem
    # o bloco `motores:` degrada para os defaults do config.yaml sem quebrar o never-raise (WR-03).
    # Caminho ÚNICO (ENG-01): `_valor_rim` deriva o insumo pela política do arquétipo
    # (ARQUETIPO_ANCORA_ROE) e chama SEMPRE motores.rim com o Ke/g_T prontos (never-raise → None).
    a.intrinseco_motor = _valor_rim(c, a, cfg)
    a.motor_rotulo = motores.MOTOR_ROTULO["rim"]

    # Guarda-corpo do intrínseco do RIM: um valor NÃO-POSITIVO (book/lucro normalizado negativo:
    # holding sem patrimônio, cíclica em fundo de ciclo) NÃO é preço-alvo — é ruído que o usuário
    # leria como intrínseco negativo. Suprime na borda (None + alerta honesto) para o veredito cair
    # no ramo "sem preço-alvo" e o render não estampar um intrínseco ≈ R$ negativo.
    if a.intrinseco_motor is not None and a.intrinseco_motor <= 0:
        a.alertas.append(
            "O RIM único devolveu valor não-positivo (book/lucro normalizado negativo): "
            "não é preço-alvo — não exibido como intrínseco."
        )
        a.intrinseco_motor = None

    # --- Ponte P/B auditável (ENG-08) + guard runtime never-raise (ENG-09/D-10b) ---
    # A ponte é a decomposição STEADY-STATE (Gordon-RIM) da mesma tese do RIM multiestágio: uma
    # LENTE exibível para auditar a RAZÃO implícita, NÃO um segundo motor de valor (não substitui
    # `intrinseco_motor`). Insumos = os TERMINAIS que o RIM único consome: ROE_T=_roe_through_cycle,
    # Ke=a.ke, g=g_T (o g_terminal efetivo; None no carve-out fade-only ⇒ terminal g=0). Reusa o
    # MESMO `_derivar_insumo` do `_valor_rim` (mesma política do arquétipo), então a ponte não
    # diverge do que o motor usou. Never-raise: qualquer degeneração → campos None, nunca levanta.
    try:
        rim_cfg = (cfg or {}).get("motores", {}).get("rim", {})
        politica = arquetipo.ARQUETIPO_ANCORA_ROE.get(a.arquetipo, "through_cycle")
        _roe0, roe_T, g_term, vpa0 = _derivar_insumo(politica, c, a.ke, g_cap, rim_cfg, cfg)
        # carve-out/holding: g_terminal=None ⇒ terminal fade-only, crescimento terminal = 0.
        g_ponte = g_term if g_term is not None else 0.0
        a.pb_justo = valuation.pb_justo(roe_T, a.ke, g_ponte)
        a.payout_terminal = valuation.payout_terminal(roe_T, g_ponte)
        if a.pb_justo is not None and vpa0 is not None:
            a.v_ponte = a.pb_justo * vpa0
        # Guard de razão (D-10b): P/B justo ∈ (0,6) E payout_T ∈ (0,1] (meio-aberto — spike 13-01:
        # terminal zerado crava payout_T=1,0 por IDENTIDADE, não patologia). Fora disso = patologia
        # de MODELO (spread degenerado / payout impossível). Este guard NÃO conserta VPA inflado
        # (CGRA4 a 921×: P/B implícito ~1,4 é SÃO — bug de DADO, sinalizado por SAN-01, ORTOGONAL).
        pb_patologico = a.pb_justo is not None and not (0.0 < a.pb_justo < 6.0)
        payout_patologico = (
            a.payout_terminal is not None and not (0.0 < a.payout_terminal <= 1.0)
        )
        a.razao_patologica = pb_patologico or payout_patologico
        if a.razao_patologica:
            motivos_razao = []
            if pb_patologico:
                motivos_razao.append(f"P/B justo implícito {a.pb_justo:.1f} fora de (0,6)")
            if payout_patologico:
                motivos_razao.append(f"payout terminal {a.payout_terminal:.0%} fora de (0,100%]")
            a.alertas.append(
                "Razão implícita patológica (" + ", ".join(motivos_razao) + "): a decomposição "
                "steady-state do valor não fecha — veredito de preço degradado para verificação."
            )
    except Exception:
        # never-raise (SAN-06): a ponte é lente auditável; jamais derruba a análise nem levanta.
        a.pb_justo = a.v_ponte = a.payout_terminal = None
        a.razao_patologica = False

    # --- DDM de dois estágios (Cap. 15/17) ---
    payout_proj = c.payout_valuation()  # média 3a + clamp 1.0 (função canônica única)
    n = cfg["ddm"]["n_anos_explicito"]
    trib = cfg["ddm"].get("tributacao_dividendos", 0.0)
    if None not in (lpa, payout_proj, a.g_alto, a.ke) and a.ke > g_cap:
        dpa_inicial = lpa * (1 + a.g_alto) * payout_proj
        a.ddm_constante = ddm.ddm_dois_estagios(
            dpa_inicial, a.g_alto, n, g_cap, a.ke, decrescente=False, tributacao=trib
        )
        a.ddm_h = ddm.ddm_dois_estagios(
            dpa_inicial, a.g_alto, n, g_cap, a.ke, decrescente=True, tributacao=trib
        )
        sens = cfg["ddm"]["sensibilidade"]
        a.sensibilidade = ddm.matriz_sensibilidade(
            dpa_inicial, a.g_alto, n, g_cap, a.ke,
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

    # --- Banda do veredito = região da margem de segurança sobre o RIM único (ENG-01/ENG-02) ---
    # Plano 03: o ensemble motor×contraponto e a matriz DDM como FONTE da banda foram removidos. A
    # banda do veredito é a região SIMÉTRICA V×(1∓ms) sobre o intrínseco do RIM único (o Plano 04
    # formaliza como região da MS primária). O DDM segue rodando como display secundário (tabela/
    # sensibilidade), mas NÃO alimenta mais vmin/vmax. RIM degradou (None) → banda None (o ramo de
    # degradação do veredito suprime a faixa sem estampar preço-alvo falso).
    if a.intrinseco_motor is not None:
        margem = (cfg or {}).get("veredito", {}).get("margem_seguranca", 0.15)
        a.vmin = a.intrinseco_motor * (1.0 - margem)
        a.vmax = a.intrinseco_motor * (1.0 + margem)

    # --- Veredito de preço (ENG-01): árvore SUB/NO INTERVALO/SOBRE sobre a banda do RIM único ---
    # A banda vmin/vmax é a região da MS sobre o intrínseco do RIM único. As flags de risco (VULC3)
    # continuam vetando "SUBAVALIADA" e emitindo "possível divergência de modelo". Sem banda (RIM
    # degradou → intrínseco None, ou sem preço) → prefixo VERIFICAR (selo suprime faixa, selo.py:119),
    # nunca faixa falsa.
    if a.vmin is not None and a.vmax is not None and a.preco_atual:
        if a.razao_patologica:
            # ENG-09/D-10b: razão implícita patológica ⇒ patologia de MODELO (não bug de dado). O
            # guard runtime DEGRADA o veredito para VERIFICAR (never-raise: não levanta, não estampa
            # a faixa como barganha/preço-alvo confiável). O motivo já está detalhado nos alertas.
            a.veredito = (
                f"VERIFICAR — razão implícita do modelo patológica: o intervalo intrínseco "
                f"R$ {_br(a.vmin)}–{_br(a.vmax)} pode não ser confiável (ver alertas)."
            )
        elif a.preco_atual < a.vmin:
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
    else:
        # Degradação honesta: sem banda de preço (RIM degradou → intrínseco None, ou sem preço
        # atual). Reusa o prefixo VERIFICAR — selo.montar_selo (selo.py:119) suprime faixa/rótulo
        # → nunca estampa faixa falsa, sem tocar selo.py.
        if a.intrinseco_motor is not None:
            a.veredito = (
                f"VERIFICAR — arquétipo {a.arquetipo}: referência primária pelo intrínseco ≈ "
                f"R$ {_br(a.intrinseco_motor)} ({a.motor_rotulo or a.motor}); sem preço-alvo comparável."
            )
        else:
            a.veredito = (
                f"VERIFICAR — o RIM único não pôde estimar preço-alvo para o arquétipo {a.arquetipo}."
            )
        a.alertas.append(
            f"Roteamento: {a.arquetipo} → RIM único. Banda de preço indisponível "
            f"(intrínseco degradou); veredito de preço suspenso sem estampar faixa falsa."
        )

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
        if a.ke is not None and a.ke <= g_cap:
            faltou.append("Ke ≤ g_cap (perpetuidade não converge)")
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
    L.append(f"- g histórico (tendência log-linear, sanidade/fallback): **{_pct(a.g_historico)}**")
    L.append(f"- g por fundamentos (ROE × retenção, adotado): **{_pct(a.g_fundamentos)}**")
    L.append(f"- g alto adotado: **{_pct(a.g_alto)}**  |  g_cap (perpetuidade, derivado): **{_pct(a.g_estavel)}**")
    L.append(f"- Beta: **{_num(a.beta)}**  |  Ke (CAPM): **{_pct(a.ke)}**")
    L.append("")

    # Intrínseco pelo RIM único (ENG-01): a referência PRIMÁRIA de valor. O DDM abaixo é display
    # SECUNDÁRIO (não é o motor deste arquétipo). Só EXIBIÇÃO (render mínimo, o Plano 04 formaliza).
    motor_exibe = a.intrinseco_motor is not None
    if motor_exibe:
        L.append(f"## Valuation pelo motor do arquétipo ({a.arquetipo})")
        L.append(f"- **{a.motor_rotulo or a.motor}: R$ {_num(a.intrinseco_motor)}** (motor do arquétipo)")
        # A faixa do veredito é a região da margem de segurança sobre o intrínseco do RIM.
        if a.vmin is not None and a.vmax is not None:
            L.append(
                f"- Faixa do veredito (margem de segurança): R$ {_num(a.vmin)}–{_num(a.vmax)}"
            )
        L.append("")

    # DDM (referência secundária — não é o motor deste arquétipo)
    L.append("## Valuation por Desconto de Dividendos (Cap. 13-17)")
    if motor_exibe:
        L.append("_(referência secundária — o motor deste arquétipo é o RIM acima)_")
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
