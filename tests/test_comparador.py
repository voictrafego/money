"""Golden tests do comparador lado a lado (Fase 21 / COMP-02, COMP-03).

Trava o contrato da engine do 5º menu "Comparar ações":
- `comparador.montar_comparativo` devolve um DataFrame TRANSPOSTO (tickers em COLUNAS,
  métricas em LINHAS na ordem fixa "Selo","P/L","P/VP","ROE","DY","Valor de Mercado");
- a linha "Selo" é o Selo COMPLETO (quadrante) via `report.analisar_acao(...).selo` +
  `presentation.selo_badge` — não só a cor; ausência → "—";
- regra de suficiência ≥2 (`.suficiente`), sem alvo/ranking/sort;
- never-raise: um contexto que quebre `analisar_acao` degrada só a sua coluna;
- `presentation.fmt_rs` formata reais em ptBR (None → "—").

Usa CompanyData sintéticos OFFLINE (mesmo espírito de test_presentation_multiticker) +
o config.yaml shipado (determinístico) para `report.analisar_acao`. Nunca importa `app`.
"""

import os

import pandas as pd
import yaml

from analista.core.fundamentals import CompanyData
from analista.report import comparador, presentation, report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


CFG = _cfg()

ORDEM_FIXA = ["Selo", "P/L", "P/VP", "ROE", "DY", "Valor de Mercado"]


def _mk(
    ticker: str,
    *,
    lucros=None,
    divs=None,
    preco: float = 10.0,
    num_acoes: float = 1_000_000_000.0,
    pl: float = 8000.0,
) -> CompanyData:
    """Construtor sintético OFFLINE com séries consistentes p/ o report rodar e produzir selo."""
    lucros = lucros or [1000] * 10
    divs = divs or [490] * 10
    anos = list(range(2015, 2015 + len(lucros)))
    c = CompanyData(ticker=ticker, nome=f"{ticker} (sintética)", setor="Teste", anos=anos)
    for i, a in enumerate(anos):
        c.lucro_liquido[a] = lucros[i]
        c.patrimonio_liquido[a] = pl
        c.dividendos[a] = divs[i]
        c.num_acoes[a] = num_acoes
        c.vendas_liquidas[a] = (lucros[i] or 0) * 4 or 100
        c.fco[a] = (lucros[i] or 0) * 1.2
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = preco
    c.beta = 0.90
    return c


# --------------------------------------------------------------------------- #
# fmt_rs (fonte única de formatação de reais na engine)
# --------------------------------------------------------------------------- #
def test_fmt_rs_none_vira_em_dash():
    assert presentation.fmt_rs(None) == "—"


def test_fmt_rs_ptbr_virgula_decimal_e_ponto_milhar():
    s = presentation.fmt_rs(1234.5, 1)
    assert s.startswith("R$")
    assert "1.234,5" in s  # milhar com ponto, decimal com vírgula (ptBR)


# --------------------------------------------------------------------------- #
# COMP-02/03 — DataFrame transposto (tickers em colunas, selo por coluna)
# --------------------------------------------------------------------------- #
def test_transposto_colunas_sao_tickers_e_linhas_ordem_fixa():
    c1, c2 = _mk("AAAA3"), _mk("BBBB3", preco=20.0)
    tab = comparador.montar_comparativo([c1, c2], CFG)

    assert tab.suficiente is True
    assert isinstance(tab.df, pd.DataFrame)
    # colunas = tickers na ordem de entrada
    assert list(tab.df.columns) == ["AAAA3", "BBBB3"]
    # linhas = ordem fixa, "Selo" primeiro
    assert list(tab.df.index) == ORDEM_FIXA


def test_linha_selo_e_o_badge_completo_nao_so_a_cor():
    c1 = _mk("AAAA3")
    c2 = _mk("BBBB3", preco=20.0)
    tab = comparador.montar_comparativo([c1, c2], CFG)

    a1 = report.analisar_acao(c1, CFG)
    esperado = presentation.selo_badge(
        a1.selo.cor, a1.selo.rotulo, a1.selo.qualidade, a1.selo.verificar
    )
    # a célula "Selo" é a string COMPLETA do quadrante (não o emoji só-cor)
    assert tab.df.loc["Selo", "AAAA3"] == esperado
    # e é um badge de verdade (tem cor → começa com emoji), não "—"
    assert a1.selo is not None and a1.selo.cor is not None
    assert tab.df.loc["Selo", "AAAA3"] != "—"


def test_metrica_ausente_vira_em_dash_e_valor_mercado_em_bilhoes():
    c1 = _mk("AAAA3")
    c_vazio = CompanyData(ticker="NONE3", anos=[2023])  # sem preço/num_acoes
    tab = comparador.montar_comparativo([c1, c_vazio], CFG)

    # coluna sem preço/nº de ações: os múltiplos derivados degradam para "—"
    assert tab.df.loc["P/L", "NONE3"] == "—"
    assert tab.df.loc["P/VP", "NONE3"] == "—"
    assert tab.df.loc["Valor de Mercado", "NONE3"] == "—"
    # coluna cheia: Valor de Mercado formatado em bilhões ptBR + " B"
    vm = tab.df.loc["Valor de Mercado", "AAAA3"]
    assert vm.endswith(" B") and vm.startswith("R$")


def test_ordem_das_colunas_preserva_entrada_sem_sort_nem_alvo():
    cs = [_mk("CCCC3"), _mk("AAAA3"), _mk("BBBB3")]
    tab = comparador.montar_comparativo(cs, CFG)
    # ordem de entrada preservada (sem sort, sem coluna-alvo, sem "➤")
    assert list(tab.df.columns) == ["CCCC3", "AAAA3", "BBBB3"]
    for col in tab.df.columns:
        assert "➤" not in col


# --------------------------------------------------------------------------- #
# Regra de suficiência ≥2 (substitui pares_suficientes, sem alvo)
# --------------------------------------------------------------------------- #
def test_suficiente_falso_com_menos_de_dois():
    assert comparador.montar_comparativo([_mk("AAAA3")], CFG).suficiente is False
    assert comparador.montar_comparativo([], CFG).suficiente is False


# --------------------------------------------------------------------------- #
# never-raise: contexto quebrado degrada só a sua coluna
# --------------------------------------------------------------------------- #
class _Quebrado:
    """Stub que não implementa a interface de CompanyData → derruba analisar_acao/metricas_par."""

    ticker = "BAD3"


def test_never_raise_contexto_quebrado_degrada_so_a_coluna():
    c1 = _mk("AAAA3")
    tab = comparador.montar_comparativo([c1, _Quebrado()], CFG)
    # não levantou; coluna quebrada existe e degrada por completo
    assert "BAD3" in tab.df.columns
    assert tab.df.loc["Selo", "BAD3"] == "—"
    assert tab.df.loc["P/L", "BAD3"] == "—"
    # a coluna boa continua aparecendo normalmente
    assert tab.df.loc["Selo", "AAAA3"] != "—"
