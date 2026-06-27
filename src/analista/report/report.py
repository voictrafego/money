"""Relatório do analista: amarra múltiplos (Cap. 10), crescimento (Cap. 14),
CAPM (Cap. 16) e DDM (Cap. 13-17) em um parecer por ação, com veredito.

A regressão de comparáveis (Cap. 11/12) entra no fluxo por setor (comando `rank`),
pois exige um conjunto de pares; aqui o foco é o valuation por desconto de dividendos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from tabulate import tabulate

from ..core import capm, ddm, growth, indicators, lifecycle
from ..core import multiples as mult
from ..core.fundamentals import CompanyData


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


def analisar_acao(c: CompanyData, cfg: dict) -> AnaliseAcao:
    anos = c.anos_ordenados()
    ult = c.ultimo_ano()
    a = AnaliseAcao(ticker=c.ticker, nome=c.nome, setor=c.setor, preco_atual=c.preco_atual)

    # --- Múltiplos (Cap. 10), no último ano ---
    lpa = c.lpa(ult)
    dpa = c.dpa(ult)
    a.multiplos = {
        "ML": mult.margem_liquida(c.lucro_liquido.get(ult), c.vendas_liquidas.get(ult)),
        "ROE": c.roe(ult),
        "P/L": mult.preco_lucro(c.preco_atual, lpa),
        "EY": mult.earnings_yield(lpa, c.preco_atual),
        "DP (payout)": c.payout(ult),
        "CDC": mult.cobertura_dividendos_caixa(c.fco.get(ult), c.num_acoes.get(ult), dpa),
        "DY": mult.dividend_yield(dpa, c.preco_atual),
    }

    # --- Crescimento (Cap. 14) ---
    lucros = c.serie("lucro_liquido")
    if len(lucros) >= 2:
        a.g_historico = growth.cagr(lucros[0], lucros[-1], len(lucros) - 1)
    a.g_fundamentos = growth.crescimento_por_fundamentos(c.roe(ult), c.payout(ult))
    g_estavel = cfg["ddm"]["g_estavel"]
    a.g_estavel = g_estavel
    # o livro prioriza o crescimento histórico do lucro quando o payout variou;
    # usamos o histórico se disponível, senão o por fundamentos. Limitado a um teto razoável.
    g_alto = a.g_historico if a.g_historico is not None else a.g_fundamentos
    if g_alto is not None:
        g_alto = max(g_estavel, min(g_alto, 0.25))  # piso = g estável; teto 25% a.a.
    a.g_alto = g_alto

    # --- Estágio do ciclo de vida (Cap. 8) ---
    lucro_positivo = all(v > 0 for v in lucros) if lucros else False
    lucro_decrescente = len(lucros) >= 2 and lucros[-1] < lucros[0]
    a.estagio = lifecycle.classificar_estagio(
        a.g_historico, c.payout(ult), lucro_positivo, lucro_decrescente
    )

    # --- CAPM (Cap. 16) ---
    cap = cfg["capm"]
    a.beta = c.beta
    if c.beta is not None:
        if cap.get("abordagem") == "local":
            a.ke = capm.ke_local(c.beta, cap["rf_us"] + cap["embi_brasil"],
                                 cap["erp_us"] + cap["embi_brasil"])
        else:
            params = capm.CapmParams(
                rf_us=cap["rf_us"], embi_brasil=cap["embi_brasil"], erp_us=cap["erp_us"],
                inflacao_br=cap["inflacao_br"], inflacao_us=cap["inflacao_us"],
            )
            a.ke = capm.ke_eua_ajustada(c.beta, params)

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

    # --- Veredito ---
    valores = [r.valor_intrinseco for r in (a.ddm_h, a.ddm_constante) if r]
    if valores:
        a.vmin, a.vmax = min(valores), max(valores)
    if valores and a.preco_atual:
        if a.preco_atual < a.vmin:
            a.veredito = f"SUBAVALIADA — preço R$ {a.preco_atual:.2f} abaixo do intervalo intrínseco R$ {a.vmin:.2f}–{a.vmax:.2f}"
        elif a.preco_atual > a.vmax:
            a.veredito = f"SOBREAVALIADA — preço R$ {a.preco_atual:.2f} acima do intervalo intrínseco R$ {a.vmin:.2f}–{a.vmax:.2f}"
        else:
            a.veredito = f"NO INTERVALO — preço R$ {a.preco_atual:.2f} dentro de R$ {a.vmin:.2f}–{a.vmax:.2f}"

    # --- Alertas / armadilhas de dividendos (Cap. 6) ---
    dy = a.multiplos.get("DY")
    if dy is not None and dy > 0.15:
        a.alertas.append("DY > 15%: possível armadilha de dividendos (Cap. 6) — verificar sustentabilidade.")
    if c.payout(ult) is not None and c.payout(ult) > 1.0:
        a.alertas.append("Payout > 100%: distribui mais que o lucro (reservas) — insustentável no longo prazo.")
    if not lucro_positivo:
        a.alertas.append("Prejuízo em algum ano da janela: fundamentos inconsistentes para dividendos.")
    if a.ke is None:
        a.alertas.append("Beta indisponível: não foi possível calcular Ke nem o DDM.")
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
    if base == "semanal" and ohlc is not None and len(ohlc) > 0:
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
    a.alerta_reverificacao = _alerta_reverificacao(a.sinais)

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


def relatorio_markdown(c: CompanyData, a: AnaliseAcao, cfg: dict) -> str:
    L: List[str] = []
    L.append(f"# Análise de Dividendos — {a.ticker} ({a.nome})")
    L.append("")
    L.append(f"*Setor:* {a.setor or '-'}  |  *Preço atual:* R$ {_num(a.preco_atual)}  "
             f"|  *Estágio (ciclo de vida):* {a.estagio}")
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
        if k in ("ML", "ROE", "DP (payout)", "DY", "EY"):
            mlin.append([k, _pct(v)])
        else:
            mlin.append([k, _num(v)])
    L.append(tabulate(mlin, headers=["Múltiplo", "Valor"], tablefmt="github"))
    L.append("")

    # Crescimento e custo de capital
    L.append("## Crescimento e custo de capital (Cap. 14 e 16)")
    L.append(f"- g histórico (CAGR do lucro): **{_pct(a.g_historico)}**")
    L.append(f"- g por fundamentos (ROE × retenção): **{_pct(a.g_fundamentos)}**")
    L.append(f"- g alto adotado: **{_pct(a.g_alto)}**  |  g estável (perpetuidade): **{_pct(a.g_estavel)}**")
    L.append(f"- Beta: **{_num(a.beta)}**  |  Ke (CAPM): **{_pct(a.ke)}**")
    L.append("")

    # DDM
    L.append("## Valuation por Desconto de Dividendos (Cap. 13-17)")
    if a.ddm_constante and a.ddm_h:
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
    if (a.sinais is None or a.timing_estado == ""
            or a.sinais.tendencia.posicao_mm200 == "indisponivel"):
        # Degradação graciosa (DATA-03), espelha o fallback do DDM.
        L.append("_Histórico de preços insuficiente para o read técnico._")
        L.append("")
    else:
        L.append(f"**Timing de entrada:** {a.timing_resumo}")
        L.append("")
        L.append(a.matriz_leitura)              # fundamento-primeiro (D-04)
        if a.alerta_reverificacao:
            L.append("")
            L.append(f"- ⚠️ {a.alerta_reverificacao}")
        L.append("")

    return "\n".join(L)
