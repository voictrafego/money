"""Encanamento OHLCV + ajuste por split (offline, zero rede).

Cobre a função pura `_ajustar_por_split` (D-03/D-05) e o fluxo de `coletar_mercado`
preservando `ohlc`/`ohlc_ajustado` (D-01/D-02/D-06). Nenhum teste bate na rede:
tudo via fixtures locais e monkeypatch do yfinance (padrão de test_ingest_resolucao.py).
"""

import numpy as np
import pandas as pd
import pytest

from analista.ingest import prices


# ---------------------------------------------------------------------------
# Fixtures de hist com colunas OHLCV + Stock Splits (D-05)
# ---------------------------------------------------------------------------

def _hist_com_split():
    """Frame OHLCV com 1 split de fator 2.0 numa data intermediária.

    10 pregões. O split ocorre no índice 5 (Stock Splits = 2.0 nessa data).
    Convenção do Yahoo (auto_adjust=False): o Close NOMINAL já reflete o split
    na própria data — ou seja, há um "salto" de preço pela metade no dia do
    split. Aqui modelamos um nominal onde os 5 primeiros pregões estão na base
    "cara" (pré-split, ~200) e os 5 últimos na base "barata" (~100), de modo que
    o ajuste por split deve escalar os pré-split para baixo (÷2) e deixar a ponta
    recente intacta (fator cumulativo = 1 após o último split).
    """
    idx = pd.date_range("2021-01-01", periods=10, freq="D")
    close = pd.Series(
        [200, 202, 204, 206, 208, 104, 105, 106, 107, 108],
        index=idx, dtype=float,
    )
    open_ = close - 1.0
    high = close + 2.0
    low = close - 2.0
    volume = pd.Series([1000.0] * 10, index=idx)
    adj = close * 0.5  # retroajustado (NUNCA usado como base de ajuste por split)
    splits = pd.Series([0.0] * 10, index=idx)
    splits.iloc[5] = 2.0  # split de 2:1 no 6º pregão
    return pd.DataFrame({
        "Open": open_, "High": high, "Low": low, "Close": close,
        "Adj Close": adj, "Volume": volume, "Stock Splits": splits,
        "Dividends": pd.Series([0.0] * 10, index=idx),
    })


def _hist_sem_split():
    """Frame OHLCV sem nenhum evento de split (Stock Splits toda zero)."""
    idx = pd.date_range("2021-01-01", periods=8, freq="D")
    close = pd.Series([10, 11, 12, 13, 14, 15, 16, 17], index=idx, dtype=float)
    return pd.DataFrame({
        "Open": close - 0.5, "High": close + 1, "Low": close - 1,
        "Close": close, "Adj Close": close * 0.9,
        "Volume": pd.Series([500.0] * 8, index=idx),
        "Stock Splits": pd.Series([0.0] * 8, index=idx),
    })


# ---------------------------------------------------------------------------
# _ajustar_por_split — função pura (D-03/D-05)
# ---------------------------------------------------------------------------

def test_ponta_recente_coincide_com_nominal():
    """Após o último split, fator cumulativo = 1: cauda do ajustado == nominal."""
    hist = _hist_com_split()
    aj = prices._ajustar_por_split(hist)
    # pregões >= índice do split (5) estão na base recente -> inalterados
    for i in range(5, 10):
        assert aj["Close"].iloc[i] == hist["Close"].iloc[i]
        assert aj["Open"].iloc[i] == hist["Open"].iloc[i]
        assert aj["High"].iloc[i] == hist["High"].iloc[i]
        assert aj["Low"].iloc[i] == hist["Low"].iloc[i]
        assert aj["Volume"].iloc[i] == hist["Volume"].iloc[i]


def test_pre_split_escalado_pelo_fator_cumulativo():
    """Datas ANTERIORES ao split ficam ÷2 (preço) e ×2 (volume), sem salto."""
    hist = _hist_com_split()
    aj = prices._ajustar_por_split(hist)
    for i in range(0, 5):
        assert aj["Close"].iloc[i] == pytest.approx(hist["Close"].iloc[i] / 2.0)
        assert aj["Open"].iloc[i] == pytest.approx(hist["Open"].iloc[i] / 2.0)
        assert aj["High"].iloc[i] == pytest.approx(hist["High"].iloc[i] / 2.0)
        assert aj["Low"].iloc[i] == pytest.approx(hist["Low"].iloc[i] / 2.0)
        assert aj["Volume"].iloc[i] == pytest.approx(hist["Volume"].iloc[i] * 2.0)


def test_sem_salto_na_data_do_split():
    """A descontinuidade nominal some no ajustado (transição suave no split)."""
    hist = _hist_com_split()
    aj = prices._ajustar_por_split(hist)
    # nominal salta de 208 (i=4) p/ 104 (i=5): variação ~ -50%
    salto_nominal = hist["Close"].iloc[5] / hist["Close"].iloc[4] - 1
    assert salto_nominal < -0.4  # confirma que o salto existe no nominal
    # no ajustado, i=4 vira 104 (208/2) e i=5 segue 104 -> variação pequena
    var_aj = aj["Close"].iloc[5] / aj["Close"].iloc[4] - 1
    assert abs(var_aj) < 0.05


def test_sem_split_ajustado_igual_nominal():
    """0 eventos de split -> ajustado idêntico ao nominal (todos OHLCV iguais)."""
    hist = _hist_sem_split()
    aj = prices._ajustar_por_split(hist)
    for col in ("Open", "High", "Low", "Close", "Volume"):
        assert list(aj[col]) == list(hist[col])


def test_sem_coluna_stock_splits_nao_estoura():
    """Frame sem a coluna 'Stock Splits' -> retorna nominal inalterado, sem erro."""
    hist = _hist_sem_split().drop(columns=["Stock Splits"])
    aj = prices._ajustar_por_split(hist)
    assert aj is not None
    for col in ("Open", "High", "Low", "Close", "Volume"):
        assert list(aj[col]) == list(hist[col])


def test_funcao_e_pura_nao_muta_entrada():
    """O frame de entrada permanece inalterado após a chamada (sem side effects)."""
    hist = _hist_com_split()
    antes = hist.copy(deep=True)
    _ = prices._ajustar_por_split(hist)
    pd.testing.assert_frame_equal(hist, antes)


def test_frame_vazio_retorna_none():
    """Frame vazio -> None, sem estourar."""
    assert prices._ajustar_por_split(pd.DataFrame()) is None


# ---------------------------------------------------------------------------
# Fluxo de coletar_mercado (D-01/D-02/D-06) — preenchido na Task 2
# ---------------------------------------------------------------------------

class _TkComOHLC:
    def history(self, *a, **k):
        return _hist_com_split()

    @property
    def dividends(self):
        return pd.Series(dtype=float)


class _TkVazio:
    def history(self, *a, **k):
        return pd.DataFrame()

    @property
    def dividends(self):
        return pd.Series(dtype=float)


def _monkeypatch_yf(monkeypatch, tk_cls):
    class _YF:
        @staticmethod
        def Ticker(sym):
            return tk_cls()

    monkeypatch.setattr(prices, "_yf", lambda: _YF())
    monkeypatch.setattr(prices.time, "sleep", lambda *_: None)
    monkeypatch.setattr(prices, "_fetch_info", lambda tk: {})


def test_dm_ohlc_preserva_frame_cru(monkeypatch):
    """Com hist, dm.ohlc é o frame cru completo (mesmas colunas) e ohlc_ajustado != None."""
    _monkeypatch_yf(monkeypatch, _TkComOHLC)
    dm = prices.coletar_mercado("OHL3")
    assert dm.ohlc is not None
    assert list(dm.ohlc.columns) == list(_hist_com_split().columns)
    assert dm.ohlc_ajustado is not None
    # ponta recente do ajustado coincide com o nominal (D-05)
    assert dm.ohlc_ajustado["Close"].iloc[-1] == dm.ohlc["Close"].iloc[-1]


def test_dm_ohlc_none_quando_hist_vazio(monkeypatch):
    """hist vazio -> ohlc e ohlc_ajustado None, sem quebrar coletar_mercado (D-06)."""
    _monkeypatch_yf(monkeypatch, _TkVazio)
    monkeypatch.setattr(prices, "_fetch_info",
                        lambda tk: {"shortName": "Z", "regularMarketPrice": 5.0})
    dm = prices.coletar_mercado("ZZZ3")
    assert dm.ohlc is None
    assert dm.ohlc_ajustado is None


def test_serie_precos_nao_regrediu(monkeypatch):
    """serie_precos continua sendo o Close nominal (não regrediu com os campos novos)."""
    _monkeypatch_yf(monkeypatch, _TkComOHLC)
    dm = prices.coletar_mercado("OHL3")
    assert dm.serie_precos is not None
    assert dm.serie_precos.iloc[-1] == _hist_com_split()["Close"].iloc[-1]


# ---------------------------------------------------------------------------
# Validação multi-split estilo ITSA4 (D-08, critério de aceite #2) — offline
# ---------------------------------------------------------------------------
#
# ITSA4 tem 5 eventos de split/bonificação em ~5 anos (dez/2021, nov/2022,
# nov/2023, dez/2024, dez/2025 — verificados em runtime, CONTEXT 04 <specifics>),
# o que estressa o fator de split CUMULATIVO. Esta fixture é 100% offline: a
# validação contra o Yahoo real do ITSA4 é o checkpoint humano da Task 2.

# fatores plausíveis de bonificação por evento (produto cumulativo > 1)
_ITSA4_EVENTOS = [
    (pd.Timestamp("2021-12-15"), 1.10),
    (pd.Timestamp("2022-11-15"), 1.05),
    (pd.Timestamp("2023-11-15"), 1.10),
    (pd.Timestamp("2024-12-15"), 1.20),
    (pd.Timestamp("2025-12-15"), 1.10),
]
_ITSA4_PROD_TOTAL = 1.10 * 1.05 * 1.10 * 1.20 * 1.10  # produto dos 5 fatores


def _hist_itsa4_multisplit():
    """Fixture estilo ITSA4 (D-08): 5 eventos de split em ~5 anos de pregões diários.

    Constrói-se a partir de um caminho econômico CONTÍNUO `A` (a série já split-
    adjusted "verdadeira", suave e crescente) multiplicado pelo fator de split
    CUMULATIVO (produto dos splits que ocorrem ESTRITAMENTE DEPOIS de cada data)
    para obter o Close NOMINAL — exatamente a relação que os dados crus do Yahoo
    (auto_adjust=False) têm com a série split-adjusted. Cada evento cria um degrau
    para baixo no nominal; `_ajustar_por_split` deve RECUPERAR `A` (contínuo, sem
    saltos) a partir desse nominal cheio de degraus.

    Retorna (hist, A) para o teste asseverar contra a construção.
    """
    idx = pd.date_range("2021-01-01", "2025-12-31", freq="D")
    n = len(idx)
    # série split-adjusted "verdadeira" — suave/contínua, sem degraus (R$5 -> R$12)
    A = pd.Series(np.linspace(5.0, 12.0, n), index=idx)
    # fator cumulativo: produto dos splits ESTRITAMENTE DEPOIS de cada data
    fator = pd.Series(1.0, index=idx)
    for data, f in _ITSA4_EVENTOS:
        fator[idx < data] *= f
    close = A * fator  # Close NOMINAL com degraus nas 5 datas de split
    splits = pd.Series(0.0, index=idx)
    for data, f in _ITSA4_EVENTOS:
        splits[data] = f
    hist = pd.DataFrame({
        "Open": close * 0.99,
        "High": close * 1.02,
        "Low": close * 0.98,
        "Close": close,
        "Adj Close": close * 0.6,   # dividend-adjusted: NUNCA usado como base
        "Volume": 1_000.0 / fator,  # volume nominal (inverso); adj recupera ~1000
        "Stock Splits": splits,
        "Dividends": pd.Series(0.0, index=idx),
    })
    return hist, A


def test_itsa4_5_splits_ponta_recente_coincide_com_nominal():
    """D-08: após o último split (dez/2025), fator = 1 -> ponta recente do ajustado
    coincide com o nominal (e com a série split-adjusted verdadeira A)."""
    hist, A = _hist_itsa4_multisplit()
    aj = prices._ajustar_por_split(hist)
    ultimo_split = _ITSA4_EVENTOS[-1][0]
    cauda = hist.index >= ultimo_split
    assert cauda.sum() > 0
    # cauda do ajustado == nominal == A (sem reescala após o último evento)
    np.testing.assert_allclose(aj.loc[cauda, "Close"], hist.loc[cauda, "Close"])
    np.testing.assert_allclose(aj.loc[cauda, "Close"], A[cauda].values)


def test_itsa4_5_splits_serie_ajustada_continua_sem_saltos():
    """D-08: a série ajustada recupera o caminho contínuo A — sem degraus/cruzamentos
    espúrios nas 5 datas de split, embora o nominal salte em cada evento."""
    hist, A = _hist_itsa4_multisplit()
    aj = prices._ajustar_por_split(hist)
    # (1) o ajustado reconstrói o caminho contínuo verdadeiro em toda a janela
    np.testing.assert_allclose(aj["Close"].values, A.values, rtol=1e-9)
    # (2) em CADA data de split: nominal cai (degrau ~ 1/fator), ajustado é contínuo
    for data, f in _ITSA4_EVENTOS:
        loc = hist.index.get_loc(data)
        assert loc > 0
        razao_nominal = hist["Close"].iloc[loc] / hist["Close"].iloc[loc - 1]
        razao_aj = aj["Close"].iloc[loc] / aj["Close"].iloc[loc - 1]
        # nominal tem o degrau do split (~1/f, claramente < 1)
        assert razao_nominal < 0.97, (data, razao_nominal)
        # ajustado atravessa o evento sem salto (continuidade dentro de tolerância)
        assert abs(razao_aj - 1.0) < 0.01, (data, razao_aj)


def test_itsa4_fator_cumulativo_pre_primeiro_split():
    """D-08: datas anteriores ao 1º split (dez/2021) são escaladas pelo produto dos
    5 fatores -> ajustado MENOR que o nominal (sem salto abrupto)."""
    hist, A = _hist_itsa4_multisplit()
    aj = prices._ajustar_por_split(hist)
    primeiro_split = _ITSA4_EVENTOS[0][0]
    pre = hist.index < primeiro_split
    assert pre.sum() > 0
    # ajustado = nominal / (produto dos 5 fatores) antes do primeiro evento
    np.testing.assert_allclose(
        aj.loc[pre, "Close"].values,
        hist.loc[pre, "Close"].values / _ITSA4_PROD_TOTAL,
    )
    # o Close ajustado mais antigo é estritamente MENOR que o nominal correspondente
    assert aj["Close"].iloc[0] < hist["Close"].iloc[0]
    # volume antigo ajustado é MAIOR (sentido inverso do preço)
    assert aj["Volume"].iloc[0] > hist["Volume"].iloc[0]
