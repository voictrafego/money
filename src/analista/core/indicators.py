"""Indicadores técnicos consultivos (v1.2) — módulo puro sobre o OHLC split-adjusted.

A engine separa CÁLCULO de APRESENTAÇÃO (D-01): devolve um dataclass agrupado por
quatro famílias — Tendência, Canais, Força e Momentum. Cada família carrega as séries
(para o plot da Phase 7) E os sinais discretos em chaves estáveis/neutras
("acima"/"abaixo", "golden_cross"/"death_cross", "sobrecomprado"/"sobrevendido", ...).
Frases consultivas em linguagem natural NÃO entram aqui — são da Phase 6.

Suavização de Wilder (RSI/ADX): o único pedaço genuinamente hand-rolled. A RMA de Wilder
seeda com a SMA dos primeiros `length` períodos (NÃO o primeiro valor), depois é recursiva
com alpha = 1/length. O `ewm` cru não tem essa semente e diverge do TradingView.

Conferência (dataset canônico de Wilder, "New Concepts in Technical Trading Systems";
replicado por StockCharts/Wikipedia/TradingView): primeiro RSI(14) = 70,5328 (SMA-seeded;
a EMA ingênua daria 50,75). Os cinco seguintes = [66.3186, 66.5498, 69.4063, 66.3552, 57.9749].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy import stats

Number = Optional[float]


# --------------------------------------------------------------------------- #
# Contrato SinaisTecnicos (agrupado por família — D-01)
# --------------------------------------------------------------------------- #
@dataclass
class Tendencia:
    sma20: pd.Series
    sma50: pd.Series
    sma200: pd.Series
    ema20: pd.Series
    ema50: pd.Series
    ema200: pd.Series
    posicao_mm200: str          # "acima" | "abaixo" | "indisponivel"
    cruzamento: str             # "golden_cross" | "death_cross" | "nenhum" | "indisponivel"


@dataclass
class Canais:
    donchian_sup: pd.Series
    donchian_inf: pd.Series
    bb_sup: pd.Series
    bb_med: pd.Series
    bb_inf: pd.Series
    largura_bb: pd.Series
    squeeze_pct: pd.Series
    rompimento_donchian: str    # "nova_maxima" | "perda_minima" | "nenhum" | "indisponivel"
    toque_bollinger: str        # "banda_superior" | "banda_inferior" | "nenhum" | "indisponivel"
    squeeze: str                # "squeeze_on" | "squeeze_off" | "indisponivel"


@dataclass
class Forca:
    adx: pd.Series
    pdi: pd.Series
    ndi: pd.Series
    regressao_slope_ann: pd.Series
    regressao_r2: pd.Series
    forca_adx: str              # "sem_tendencia" | "forte" | "neutro" | "indisponivel"


@dataclass
class Momentum:
    rsi: pd.Series
    macd: pd.Series
    macd_sinal: pd.Series
    macd_hist: pd.Series
    nivel_rsi: str              # "sobrecomprado" | "sobrevendido" | "neutro" | "indisponivel"
    cruzamento_macd: str        # "cruz_alta" | "cruz_baixa" | "nenhum" | "indisponivel"


@dataclass
class SinaisTecnicos:
    tendencia: Tendencia
    canais: Canais
    forca: Forca
    momentum: Momentum


# --------------------------------------------------------------------------- #
# Suavização de Wilder (RSI/ADX) — único hand-roll; seed por SMA
# --------------------------------------------------------------------------- #
def _wilder_rma_from(arr: np.ndarray, length: int, start: int = 0) -> np.ndarray:
    """RMA de Wilder seedada pela SMA dos primeiros `length` valores a partir de `start`.

    O seed em `start` (em vez de 0) é o que permite reaproveitar o helper na 2ª suavização
    do ADX, onde o DX só fica válido a partir do índice `length`. Sem seed por SMA, a RMA
    diverge do TradingView (ver docstring do módulo).
    """
    out = np.full(len(arr), np.nan)
    if start + length > len(arr):
        return out
    out[start + length - 1] = arr[start:start + length].mean()
    a = 1.0 / length
    for i in range(start + length, len(arr)):
        out[i] = a * arr[i] + (1 - a) * out[i - 1]
    return out
