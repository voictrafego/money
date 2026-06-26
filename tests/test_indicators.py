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
