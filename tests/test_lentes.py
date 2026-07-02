"""Golden tests das 4 lentes de valuation/contexto da Fase 19.

Valores conhecidos travam Graham (√22,5×LPA×VPA), Bazin (DPA médio ÷ 6%),
"quanto teria rendido" (Adj Close) e o comparador de pares (5 métricas + alvo).
Toda função degrada para None (never-raise) em entradas degeneradas.
"""

import math

import pandas as pd

from analista.core import lentes
from analista.core.fundamentals import CompanyData


# --------------------------------------------------------------------------- #
# VAL-01 — Preço-Justo de Graham
# --------------------------------------------------------------------------- #
def test_graham():
    # √(22,5 × 3 × 10) = √675 ≈ 25,98
    v = lentes.preco_justo_graham(3.0, 10.0)
    assert v is not None
    assert abs(v - math.sqrt(675.0)) < 1e-9
    assert abs(v - 25.98) < 0.01


def test_graham_degrada():
    assert lentes.preco_justo_graham(0.0, 10.0) is None
    assert lentes.preco_justo_graham(3.0, 0.0) is None
    assert lentes.preco_justo_graham(-1.0, 10.0) is None
    assert lentes.preco_justo_graham(3.0, -5.0) is None
    assert lentes.preco_justo_graham(None, 10.0) is None
    assert lentes.preco_justo_graham(3.0, None) is None


def test_vpa():
    assert lentes.vpa(1000.0, 100.0) == 10.0
    assert lentes.vpa(1000.0, 0.0) is None
    assert lentes.vpa(1000.0, None) is None
    assert lentes.vpa(None, 100.0) is None


# --------------------------------------------------------------------------- #
# VAL-02 — Preço-Teto de Bazin
# --------------------------------------------------------------------------- #
def test_dpa_medio():
    assert lentes.dpa_medio([1.0, 2.0, 3.0]) == 2.0
    # pula None
    assert lentes.dpa_medio([1.0, None, 3.0]) == 2.0
    # janela: só os últimos n não-None
    assert lentes.dpa_medio([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], n=3) == 5.0
    # vazio / só None -> None
    assert lentes.dpa_medio([]) is None
    assert lentes.dpa_medio([None, None]) is None


def test_bazin():
    # DPA médio 1,2 ÷ DY-mínimo 6% = 20,0
    assert lentes.preco_teto_bazin(1.2) == 20.0
    assert abs(lentes.preco_teto_bazin(1.2) - 1.2 / 0.06) < 1e-9
    assert lentes.preco_teto_bazin(0.0) is None
    assert lentes.preco_teto_bazin(-1.0) is None
    assert lentes.preco_teto_bazin(None) is None


def test_upside():
    assert lentes.upside(30.0, 20.0) == 0.5
    assert lentes.upside(30.0, 0.0) is None
    assert lentes.upside(30.0, None) is None
    assert lentes.upside(None, 20.0) is None


# --------------------------------------------------------------------------- #
# RET-01 — "Quanto teria rendido"
# --------------------------------------------------------------------------- #
def test_retorno_periodo():
    # ~2 anos de pregões diários; preço dobra linearmente de 10 a 20.
    idx = pd.date_range("2022-01-01", "2023-12-31", freq="D")
    n = len(idx)
    valores = [10.0 + 10.0 * i / (n - 1) for i in range(n)]
    serie = pd.Series(valores, index=idx)

    # janela de 1 ano: primeiro preço em/ou-após (último - 1 ano) e último preço
    corte = serie.index[-1] - pd.DateOffset(years=1)
    primeiro = serie[serie.index >= corte].iloc[0]
    ultimo = serie.iloc[-1]
    esperado = 1000.0 * ultimo / primeiro

    r = lentes.retorno_periodo(serie, anos=1, valor_inicial=1000.0)
    assert r is not None
    assert abs(r - esperado) < 1e-6

    # histórico insuficiente: série curta (30 dias) com janela de 5 anos -> None
    curta = pd.Series(
        [10.0] * 30, index=pd.date_range("2023-01-01", periods=30, freq="D")
    )
    assert lentes.retorno_periodo(curta, anos=5) is None

    # série vazia / None -> None (never-raise)
    assert lentes.retorno_periodo(pd.Series(dtype=float), anos=1) is None
    assert lentes.retorno_periodo(None, anos=1) is None


# --------------------------------------------------------------------------- #
# PEER-01 — Comparador de pares
# --------------------------------------------------------------------------- #
def _empresa(ticker, preco, lucro, pl_ano, num_acoes, dividendos, ano=2023):
    return CompanyData(
        ticker=ticker,
        anos=[ano - 1, ano],
        lucro_liquido={ano - 1: lucro, ano: lucro},
        patrimonio_liquido={ano - 1: pl_ano, ano: pl_ano},
        num_acoes={ano - 1: num_acoes, ano: num_acoes},
        dividendos={ano - 1: dividendos, ano: dividendos},
        preco_atual=preco,
    )


def test_metricas_par():
    c = _empresa("ABCD3", preco=20.0, lucro=200.0, pl_ano=1000.0,
                 num_acoes=100.0, dividendos=120.0)
    par = lentes.metricas_par(c)
    assert par.ticker == "ABCD3"
    # P/L com LPA canônico (lpa_valuation); todos os anos têm o mesmo lucro -> LPA = 2.0
    assert par.pl is not None and abs(par.pl - 20.0 / 2.0) < 1e-6
    # P/VP = preço / VPA(ano-base) = 20 / (1000/100) = 2.0
    assert par.pvp is not None and abs(par.pvp - 2.0) < 1e-6
    # valor de mercado = preço * num_acoes = 20 * 100 = 2000
    assert par.valor_mercado is not None and abs(par.valor_mercado - 2000.0) < 1e-6
    assert par.alvo is False


def test_metricas_par_degrada():
    c = CompanyData(ticker="XYZ3", anos=[2023])  # sem preço/num_acoes
    par = lentes.metricas_par(c)
    assert par.ticker == "XYZ3"
    assert par.pl is None
    assert par.pvp is None
    assert par.valor_mercado is None


def test_tabela_pares():
    empresas = [
        _empresa("ALVO3", 20.0, 200.0, 1000.0, 100.0, 120.0),
        _empresa("PAR13", 15.0, 150.0, 900.0, 100.0, 100.0),
        _empresa("PAR23", 30.0, 300.0, 1200.0, 100.0, 90.0),
    ]
    tabela = lentes.tabela_pares(empresas, "alvo3")  # case-insensitive
    assert len(tabela) == 3
    # ordem preservada
    assert [p.ticker for p in tabela] == ["ALVO3", "PAR13", "PAR23"]
    # exatamente uma linha alvo
    assert sum(1 for p in tabela if p.alvo) == 1
    assert tabela[0].alvo is True
    # 2 pares (não-alvo) -> suficiente
    assert lentes.pares_suficientes(tabela) is True


def test_pares_insuficientes():
    empresas = [_empresa("ALVO3", 20.0, 200.0, 1000.0, 100.0, 120.0)]
    tabela = lentes.tabela_pares(empresas, "ALVO3")
    assert lentes.pares_suficientes(tabela) is False
