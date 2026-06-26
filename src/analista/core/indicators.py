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
    # Donchian-55 (mesma família, janela longa) — séries para o overlay da Phase 7.
    # Aditivas (default None) para não quebrar o contrato travado no plan 05-01.
    donchian_sup_55: pd.Series = None
    donchian_inf_55: pd.Series = None


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


# --------------------------------------------------------------------------- #
# Tendencia (TREND-01..04) — SMA/EMA 20/50/200; sinais discretos SEMPRE sobre SMA (D-03)
# --------------------------------------------------------------------------- #
def _tendencia(close: pd.Series, cfg: dict) -> Tendencia:
    """SMA e EMA 20/50/200 (ambas sempre — D-03) + posição×MM200 e golden/death cross.

    Os sinais discretos derivam SEMPRE da SMA (D-03); a EMA é vista alternativa para o plot.
    `min_periods=janela` garante NaN (não valor parcial) com histórico curto (DATA-03);
    os sinais degradam para "indisponivel" sem levantar exceção.
    """
    j20, j50, j200 = cfg["indicadores"]["sma_emas"]
    sma20 = close.rolling(j20, min_periods=j20).mean()
    sma50 = close.rolling(j50, min_periods=j50).mean()
    sma200 = close.rolling(j200, min_periods=j200).mean()
    ema20 = close.ewm(span=j20, adjust=False).mean()
    ema50 = close.ewm(span=j50, adjust=False).mean()
    ema200 = close.ewm(span=j200, adjust=False).mean()

    if len(close) == 0 or pd.isna(sma200.iloc[-1]):
        posicao = "indisponivel"
    else:
        posicao = "acima" if close.iloc[-1] > sma200.iloc[-1] else "abaixo"

    diff = (sma50 - sma200).dropna()
    if len(diff) < 2:
        cruzamento = "indisponivel"
    else:
        ultimo, penultimo = diff.iloc[-1], diff.iloc[-2]
        cruzou = np.sign(ultimo) != np.sign(penultimo)
        if cruzou and ultimo > 0:
            cruzamento = "golden_cross"
        elif cruzou and ultimo < 0:
            cruzamento = "death_cross"
        else:
            cruzamento = "nenhum"

    return Tendencia(
        sma20=sma20, sma50=sma50, sma200=sma200,
        ema20=ema20, ema50=ema50, ema200=ema200,
        posicao_mm200=posicao, cruzamento=cruzamento,
    )


# --------------------------------------------------------------------------- #
# Momentum (MOM-01..02) — RSI(14) Wilder + MACD 12/26/9 (EMA padrão, NÃO Wilder)
# --------------------------------------------------------------------------- #
def rsi_wilder(close: pd.Series, length: int = 14) -> pd.Series:
    """RSI de Wilder SMA-seeded (bate o TradingView: 1º RSI(14)=70,5328 no dataset canônico).

    A EMA ingênua (sem seed por SMA) daria 50,75 — por isso o ganho/perda médios usam
    `_wilder_rma_from`. RS = avg_gain/avg_loss é protegida contra divisão por zero:
    janela só de ganhos → RSI 100; só de perdas → RSI 0; nunca propaga inf à UI.
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = _wilder_rma_from(gain.iloc[1:].to_numpy(float), length)
    avg_loss = _wilder_rma_from(loss.iloc[1:].to_numpy(float), length)
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = avg_gain / avg_loss
        rsi = 100.0 - 100.0 / (1.0 + rs)
    # avg_loss == 0 (só ganhos) → rs=inf → RSI 100; avg_gain==avg_loss==0 → RSI neutro 50.
    rsi = np.where((avg_loss == 0) & (avg_gain > 0), 100.0, rsi)
    rsi = np.where((avg_loss == 0) & (avg_gain == 0), 50.0, rsi)
    serie = pd.Series(rsi, index=close.index[1:])
    return serie.reindex(close.index)


# --------------------------------------------------------------------------- #
# Canais (CHAN-01..03) — Donchian 20/55 causal (.shift(1)) + Bollinger 20/2σ (ddof=0)
# --------------------------------------------------------------------------- #
def _canais(ohlc: pd.DataFrame, cfg: dict) -> Canais:
    """Donchian 20/55 (canal causal) e Bollinger 20/2σ (desvio populacional).

    Todo o canal é CAUSAL: o Donchian usa `.shift(1)` — o canal é definido só pelas barras
    PASSADAS. Sem o shift, o max/min dos últimos n inclui o próprio close e o rompimento nunca
    dispara (close ≤ max que contém o próprio close). O Bollinger usa desvio POPULACIONAL
    (ddof=0, convenção TradingView/StockCharts); ddof=1 deslocaria as bandas. Histórico curto
    degrada para "indisponivel" (min_periods=janela → NaN; mitiga T-05-04). O squeeze percentil
    (largura_bb/squeeze_pct/squeeze) é preenchido no plan 05-02 Task 2.
    """
    ind = cfg["indicadores"]
    high, low, close = ohlc["High"], ohlc["Low"], ohlc["Close"]

    j_curto, j_longo = ind["donchian"]                 # [20, 55] — 20 é o canal primário
    donchian_sup = high.rolling(j_curto, min_periods=j_curto).max().shift(1)
    donchian_inf = low.rolling(j_curto, min_periods=j_curto).min().shift(1)
    donchian_sup_55 = high.rolling(j_longo, min_periods=j_longo).max().shift(1)
    donchian_inf_55 = low.rolling(j_longo, min_periods=j_longo).min().shift(1)

    if len(close) == 0 or pd.isna(donchian_sup.iloc[-1]) or pd.isna(donchian_inf.iloc[-1]):
        rompimento = "indisponivel"
    elif close.iloc[-1] > donchian_sup.iloc[-1]:
        rompimento = "nova_maxima"
    elif close.iloc[-1] < donchian_inf.iloc[-1]:
        rompimento = "perda_minima"
    else:
        rompimento = "nenhum"

    jbb = ind["bollinger"]["janela"]
    sigma = ind["bollinger"]["sigma"]
    bb_med = close.rolling(jbb, min_periods=jbb).mean()
    sd = close.rolling(jbb, min_periods=jbb).std(ddof=0)   # ddof=0 = população
    bb_sup = bb_med + sigma * sd
    bb_inf = bb_med - sigma * sd

    if len(close) == 0 or pd.isna(bb_sup.iloc[-1]) or pd.isna(bb_inf.iloc[-1]):
        toque = "indisponivel"
    elif close.iloc[-1] >= bb_sup.iloc[-1]:
        toque = "banda_superior"
    elif close.iloc[-1] <= bb_inf.iloc[-1]:
        toque = "banda_inferior"
    else:
        toque = "nenhum"

    # Squeeze percentil (CHAN-03, D-02): largura normalizada vs sua própria janela trailing.
    # bb_med==0 (preço achatado) → largura NaN, não inf (np.errstate; mitiga T-05-03).
    with np.errstate(divide="ignore", invalid="ignore"):
        largura_bb = (bb_sup - bb_inf) / bb_med.replace(0.0, np.nan)
    squeeze_janela = ind["squeeze_janela"]
    # raw=True → x é ndarray e x[-1] é a barra atual; o percentil só olha a janela até agora (causal).
    squeeze_pct = largura_bb.rolling(squeeze_janela, min_periods=squeeze_janela).apply(
        lambda x: (x <= x[-1]).mean() * 100.0, raw=True
    )
    squeeze_percentil = ind["squeeze_percentil"]
    if len(close) == 0 or pd.isna(squeeze_pct.iloc[-1]):
        squeeze = "indisponivel"
    elif squeeze_pct.iloc[-1] <= squeeze_percentil:
        squeeze = "squeeze_on"
    else:
        squeeze = "squeeze_off"

    return Canais(
        donchian_sup=donchian_sup, donchian_inf=donchian_inf,
        bb_sup=bb_sup, bb_med=bb_med, bb_inf=bb_inf,
        largura_bb=largura_bb, squeeze_pct=squeeze_pct,
        rompimento_donchian=rompimento, toque_bollinger=toque, squeeze=squeeze,
        donchian_sup_55=donchian_sup_55, donchian_inf_55=donchian_inf_55,
    )


# --------------------------------------------------------------------------- #
# Forca (FORCE-01..02) — ADX(14) dupla-Wilder + regressão linear trailing (%/ano, R²)
# --------------------------------------------------------------------------- #
def adx_wilder(ohlc: pd.DataFrame, length: int = 14):
    """ADX(14) pela cadeia completa de Wilder com DUPLA suavização → (adx, pdi, ndi).

    Cadeia: +DM/-DM/TR por barra → suaviza cada um com `_wilder_rma_from` (1º válido no
    índice `length`) → +DI = 100·sm(+DM)/ATR, -DI = 100·sm(-DM)/ATR → DX = 100·|+DI−−DI|/
    (+DI+−DI) → ADX = 2ª suavização de Wilder do DX SEEDADA no primeiro DX válido
    (`start=length`). Seedar a 2ª suavização em 0 faria a SMA-seed mediar `length` NaNs →
    ADX todo-NaN (RESEARCH Pitfall 2); por isso `start=length` e o 1º ADX válido cai no
    índice 2·length−1 (= 27 para length 14). Divisões protegidas com `np.errstate`
    (ATR==0 ou +DI+−DI==0 → NaN, nunca inf; mitiga T-05-06).
    """
    high, low, close = ohlc["High"], ohlc["Low"], ohlc["Close"]

    up = high.diff()
    dn = -low.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)

    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    # 1ª suavização de Wilder — start=1 porque a barra 0 é o diff indefinido (up/dn = NaN);
    # seedar a SMA em arr[1:1+length] coloca o 1º +DI/-DI/ATR válido no índice `length`.
    atr = _wilder_rma_from(tr.to_numpy(float), length, start=1)
    sm_pdm = _wilder_rma_from(np.asarray(plus_dm, dtype=float), length, start=1)
    sm_ndm = _wilder_rma_from(np.asarray(minus_dm, dtype=float), length, start=1)

    with np.errstate(divide="ignore", invalid="ignore"):
        pdi = 100.0 * sm_pdm / atr
        ndi = 100.0 * sm_ndm / atr
        denom = pdi + ndi
        dx = 100.0 * np.abs(pdi - ndi) / denom
    dx = np.where(denom == 0.0, np.nan, dx)

    # 2ª suavização de Wilder do DX — SEED no primeiro DX válido (start=length)
    adx_arr = _wilder_rma_from(dx, length, start=length)

    idx = ohlc.index
    return (
        pd.Series(adx_arr, index=idx),
        pd.Series(pdi, index=idx),
        pd.Series(ndi, index=idx),
    )


def regressao_trailing(close: pd.Series, win: int = 90):
    """Regressão linear trailing (causal) → (slope_ann %/ano, r2) como Series (D-04).

    Para cada barra i ≥ win−1, ajusta uma reta OLS sobre a janela TRAILING de `win` barras
    via `scipy.stats.linregress`. slope_ann = slope·252/média(seg)·100 (inclinação anualizada
    em %/ano, normalizada pelo nível de preço — robusta a escala, comparável entre tickers);
    r2 = rvalue². Janela só do passado → no-repaint por construção.
    """
    y = close.to_numpy(float)
    n = len(y)
    slope_ann = np.full(n, np.nan)
    r2 = np.full(n, np.nan)
    x = np.arange(win)
    for i in range(win - 1, n):
        seg = y[i - win + 1: i + 1]
        media = seg.mean()
        res = stats.linregress(x, seg)
        with np.errstate(divide="ignore", invalid="ignore"):
            slope_ann[i] = res.slope * 252.0 / media * 100.0 if media != 0 else np.nan
        r2[i] = res.rvalue ** 2
    return pd.Series(slope_ann, index=close.index), pd.Series(r2, index=close.index)


def _forca(ohlc: pd.DataFrame, cfg: dict) -> Forca:
    """Família Força: ADX(14) dupla-Wilder + regressão linear trailing %/ano (FORCE-01..02).

    forca_adx lê a ponta do ADX: < 20 → "sem_tendencia"; > 25 → "forte"; entre → "neutro";
    NaN (histórico curto) → "indisponivel" (degradação graciosa, DATA-03).
    """
    ind = cfg["indicadores"]
    adx, pdi, ndi = adx_wilder(ohlc, ind["adx_janela"])
    slope, r2 = regressao_trailing(ohlc["Close"], ind["regressao_janela"])

    if len(adx.dropna()) == 0 or pd.isna(adx.iloc[-1]):
        forca_adx = "indisponivel"
    elif adx.iloc[-1] < 20.0:
        forca_adx = "sem_tendencia"
    elif adx.iloc[-1] > 25.0:
        forca_adx = "forte"
    else:
        forca_adx = "neutro"

    return Forca(
        adx=adx, pdi=pdi, ndi=ndi,
        regressao_slope_ann=slope, regressao_r2=r2,
        forca_adx=forca_adx,
    )


def _momentum(close: pd.Series, cfg: dict) -> Momentum:
    """RSI(14) Wilder + MACD 12/26/9 (EMA padrão) com cruzamento de sinal rotulado.

    MACD usa `ewm(span=, adjust=False)` (EMA clássica), NUNCA Wilder — só RSI/ADX são Wilder.
    Sinais discretos degradam para "indisponivel" quando a ponta da série é NaN (DATA-03).
    """
    ind = cfg["indicadores"]
    rsi = rsi_wilder(close, ind["rsi_janela"])

    fast, slow, signal = ind["macd"]
    macd = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    macd_sinal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_sinal

    baixo, alto = ind["rsi_faixas"]
    if len(rsi.dropna()) == 0 or pd.isna(rsi.iloc[-1]):
        nivel_rsi = "indisponivel"
    elif rsi.iloc[-1] >= alto:
        nivel_rsi = "sobrecomprado"
    elif rsi.iloc[-1] <= baixo:
        nivel_rsi = "sobrevendido"
    else:
        nivel_rsi = "neutro"

    d = (macd - macd_sinal).dropna()
    if len(d) < 2:
        cruzamento_macd = "indisponivel"
    else:
        ultimo, penultimo = d.iloc[-1], d.iloc[-2]
        cruzou = np.sign(ultimo) != np.sign(penultimo)
        if cruzou and ultimo > 0:
            cruzamento_macd = "cruz_alta"
        elif cruzou and ultimo < 0:
            cruzamento_macd = "cruz_baixa"
        else:
            cruzamento_macd = "nenhum"

    return Momentum(
        rsi=rsi,
        macd=macd, macd_sinal=macd_sinal, macd_hist=macd_hist,
        nivel_rsi=nivel_rsi, cruzamento_macd=cruzamento_macd,
    )
