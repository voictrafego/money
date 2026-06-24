"""Encanamento OHLCV + ajuste por split (offline, zero rede).

Cobre a função pura `_ajustar_por_split` (D-03/D-05) e o fluxo de `coletar_mercado`
preservando `ohlc`/`ohlc_ajustado` (D-01/D-02/D-06). Nenhum teste bate na rede:
tudo via fixtures locais e monkeypatch do yfinance (padrão de test_ingest_resolucao.py).
"""

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
