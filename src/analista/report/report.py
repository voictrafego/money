"""Relatório do analista: amarra múltiplos (Cap. 10), crescimento (Cap. 14),
CAPM (Cap. 16) e DDM (Cap. 13-17) em um parecer por ação, com veredito.

A regressão de comparáveis (Cap. 11/12) entra no fluxo por setor (comando `rank`),
pois exige um conjunto de pares; aqui o foco é o valuation por desconto de dividendos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from tabulate import tabulate

from ..core import capm, ddm, growth, lifecycle
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
    veredito: str = ""
    alertas: List[str] = field(default_factory=list)


def _media_payout_3a(c: CompanyData) -> Optional[float]:
    anos = c.anos_ordenados()[-3:]
    vals = [c.payout(a) for a in anos]
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


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
    payout_proj = _media_payout_3a(c)
    if payout_proj is not None:
        payout_proj = min(payout_proj, 1.0)
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
    if valores and a.preco_atual:
        vmin, vmax = min(valores), max(valores)
        if a.preco_atual < vmin:
            a.veredito = f"SUBAVALIADA — preço R$ {a.preco_atual:.2f} abaixo do intervalo intrínseco R$ {vmin:.2f}–{vmax:.2f}"
        elif a.preco_atual > vmax:
            a.veredito = f"SOBREAVALIADA — preço R$ {a.preco_atual:.2f} acima do intervalo intrínseco R$ {vmin:.2f}–{vmax:.2f}"
        else:
            a.veredito = f"NO INTERVALO — preço R$ {a.preco_atual:.2f} dentro de R$ {vmin:.2f}–{vmax:.2f}"

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
    return a


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
    return "\n".join(L)
