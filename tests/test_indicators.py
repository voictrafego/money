"""Trava a matemática dos indicadores (Wilder vs TradingView, no-repaint, tendência sobre SMA)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from analista.core import indicators


def _cfg_ind() -> dict:
    """Carrega o config.yaml shipado para pinar os parâmetros canônicos nos testes."""
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _serie_golden_cross() -> pd.Series:
    """Tendência de baixa longa seguida de alta sustentada → MM50 cruza acima da MM200."""
    down = np.linspace(100.0, 50.0, 200)
    up = np.linspace(50.0, 160.0, 140)
    closes = np.concatenate([down, up])
    idx = pd.date_range("2019-01-01", periods=len(closes), freq="B")
    return pd.Series(closes, index=idx)


# --- Tendencia (TREND-01..04) ---
def test_sinais_tendencia_sma():
    # Golden cross MM50×MM200 derivado SEMPRE de SMA (D-03). Recorta a série no 1º bar
    # de cruzamento para fixar o sinal "golden_cross" na última barra.
    cfg = _cfg_ind()
    close = _serie_golden_cross()
    sma50 = close.rolling(50, min_periods=50).mean()
    sma200 = close.rolling(200, min_periods=200).mean()
    diff = sma50 - sma200
    sign = np.sign(diff)
    cross_pos = None
    for i in range(1, len(diff)):
        if sign.iloc[i] > 0 and sign.iloc[i - 1] <= 0 and not np.isnan(diff.iloc[i - 1]):
            cross_pos = i
            break
    assert cross_pos is not None

    t = indicators._tendencia(close.iloc[: cross_pos + 1], cfg)
    assert t.cruzamento == "golden_cross"
    assert t.posicao_mm200 == "acima"

    # D-03: se o sinal fosse derivado da EMA, já teria cruzado antes → daria "nenhum".
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    ediff = ema50 - ema200
    assert ediff.iloc[cross_pos] > 0 and ediff.iloc[cross_pos - 1] > 0


def test_historico_curto_tendencia():
    # <200 bars: sma200 toda-NaN; sinais discretos degradam para "indisponivel" sem exceção.
    cfg = _cfg_ind()
    idx = pd.date_range("2021-01-01", periods=120, freq="B")
    close = pd.Series(np.linspace(10.0, 20.0, 120), index=idx)
    t = indicators._tendencia(close, cfg)
    assert t.sma200.isna().all()
    assert t.posicao_mm200 == "indisponivel"
    assert t.cruzamento == "indisponivel"


# --- Momentum (MOM-01..02) ---
# Dataset canônico de Wilder ("New Concepts in Technical Trading Systems"), replicado por
# StockCharts/Wikipedia/TradingView: primeiro RSI(14) = 70,5328 (SMA-seeded).
_WILDER_CLOSES = [
    44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245, 45.8433,
    46.0826, 45.8931, 46.0328, 45.6140, 46.2820, 46.2820, 46.0028, 46.0328, 46.4116,
    46.2222, 45.6439, 46.2122, 46.2521, 45.7137, 46.4515, 45.7835, 45.3548, 44.0288,
    44.1783, 44.2181, 44.5672, 43.4205, 42.6628, 43.1314,
]


def _serie_ruidosa(n: int = 320, seed: int = 42) -> pd.Series:
    """Série determinística (tendência + ciclo + ruído seedado) para no-repaint/MACD."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    base = 50.0 + 10.0 * np.sin(t / 15.0) + 0.05 * t + rng.normal(0, 1.0, n)
    idx = pd.date_range("2019-01-01", periods=n, freq="B")
    return pd.Series(base, index=idx)


def test_rsi_wilder_canonico():
    # Âncora pública: 1º RSI(14) = 70,5328; cinco seguintes batem o TradingView.
    close = pd.Series(_WILDER_CLOSES)
    rsi = indicators.rsi_wilder(close, length=14)
    validos = rsi.dropna()
    assert validos.iloc[0] == pytest.approx(70.5328, abs=1e-3)
    np.testing.assert_allclose(
        validos.iloc[:6].to_numpy(float),
        [70.5328, 66.3186, 66.5498, 69.4063, 66.3552, 57.9749],
        atol=1e-3,
    )


def test_macd_cross():
    # MACD usa EMA padrão (não Wilder). Recorta no 1º bar de cruzamento da linha×sinal.
    cfg = _cfg_ind()
    close = _serie_ruidosa()
    fast, slow, signal = cfg["indicadores"]["macd"]
    macd = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    macd_sinal = macd.ewm(span=signal, adjust=False).mean()
    d = macd - macd_sinal
    sign = np.sign(d)
    cross_pos = None
    for i in range(1, len(d)):
        if sign.iloc[i] > 0 and sign.iloc[i - 1] <= 0:
            cross_pos = i
            break
    assert cross_pos is not None
    m = indicators._momentum(close.iloc[: cross_pos + 1], cfg)
    assert m.cruzamento_macd == "cruz_alta"


def test_no_repaint_momentum():
    # ind(s[:k])[-1] == ind(s)[k-1] para RSI e linha MACD (TEST-04).
    cfg = _cfg_ind()
    s = _serie_ruidosa()
    rsi_full = indicators.rsi_wilder(s, length=cfg["indicadores"]["rsi_janela"])
    macd_full = indicators._momentum(s, cfg).macd
    for k in (60, 120, 200, 300):
        rsi_k = indicators.rsi_wilder(s.iloc[:k], length=cfg["indicadores"]["rsi_janela"])
        assert rsi_k.iloc[-1] == pytest.approx(rsi_full.iloc[k - 1], abs=1e-9)
        macd_k = indicators._momentum(s.iloc[:k], cfg).macd
        assert macd_k.iloc[-1] == pytest.approx(macd_full.iloc[k - 1], abs=1e-9)


# --- Canais (CHAN-01..03) ---
def _frame_ohlc(close, high=None, low=None, start: str = "2021-01-01") -> pd.DataFrame:
    """Frame OHLC determinístico (colunas capitalizadas, DatetimeIndex) para os Canais."""
    close = np.asarray(close, dtype=float)
    high = close + 0.5 if high is None else np.asarray(high, dtype=float)
    low = close - 0.5 if low is None else np.asarray(low, dtype=float)
    idx = pd.date_range(start, periods=len(close), freq="B")
    return pd.DataFrame({"High": high, "Low": low, "Close": close}, index=idx)


def test_donchian_breakout_causal():
    # Canal Donchian-20 dos 20 bars ANTERIORES (.shift(1)); último close rompe acima → nova_maxima.
    cfg = _cfg_ind()
    close = np.full(60, 100.0)
    close[-1] = 120.0
    df = _frame_ohlc(close)
    c = indicators._canais(df, cfg)
    assert c.rompimento_donchian == "nova_maxima"

    # No-repaint: o canal nunca inclui a barra atual → _canais(s[:k]).iloc[-1] == _canais(s)[k-1].
    for k in (40, 50):
        ck = indicators._canais(df.iloc[:k], cfg)
        assert ck.donchian_sup.iloc[-1] == pytest.approx(c.donchian_sup.iloc[k - 1], abs=1e-9)
        assert ck.donchian_inf.iloc[-1] == pytest.approx(c.donchian_inf.iloc[k - 1], abs=1e-9)

    # Sem o .shift(1) o max dos últimos 20 incluiria a própria barra (high=120.5) → nunca romperia.
    hi20_sem_shift = df["High"].rolling(20, min_periods=20).max()
    assert df["Close"].iloc[-1] <= hi20_sem_shift.iloc[-1]


def test_bollinger_touch():
    # Último close encosta na banda superior; bb usa desvio POPULACIONAL (ddof=0, TradingView).
    cfg = _cfg_ind()
    close = np.full(40, 50.0)
    close[-1] = 60.0
    df = _frame_ohlc(close, high=np.full(40, 60.5), low=np.full(40, 49.5))
    c = indicators._canais(df, cfg)
    assert c.toque_bollinger == "banda_superior"

    # Cross-check ddof=0 num slice fixo: bb_sup == SMA20 + 2*std_populacional dos últimos 20.
    sl = pd.Series(close[-20:])
    sigma = cfg["indicadores"]["bollinger"]["sigma"]
    esperado = sl.mean() + sigma * sl.std(ddof=0)
    np.testing.assert_allclose(c.bb_sup.iloc[-1], esperado, rtol=1e-12)
    # Discriminação anti-ddof=1: a amostral deslocaria a banda e NÃO bateria.
    esperado_ddof1 = sl.mean() + sigma * sl.std(ddof=1)
    assert not np.isclose(c.bb_sup.iloc[-1], esperado_ddof1, rtol=1e-9)
