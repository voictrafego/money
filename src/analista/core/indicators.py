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
    # ATR (1ª suavização de Wilder do TR da cadeia do ADX) — insumo do stop ATR×m (LEVEL-03)
    # e das zonas S/R (LEVEL-01). Aditiva (default None) p/ não quebrar o contrato travado.
    atr: pd.Series = None


@dataclass
class Momentum:
    rsi: pd.Series
    macd: pd.Series
    macd_sinal: pd.Series
    macd_hist: pd.Series
    nivel_rsi: str              # "sobrecomprado" | "sobrevendido" | "neutro" | "indisponivel"
    cruzamento_macd: str        # "cruz_alta" | "cruz_baixa" | "nenhum" | "indisponivel"


@dataclass
class Pivos:
    pivot_high: pd.Series       # preço do High nas barras de topo CONFIRMADO, NaN nas demais
    pivot_low: pd.Series        # preço do Low nas barras de fundo CONFIRMADO, NaN nas demais
    ultimo_topo: Number         # preço do topo confirmado mais recente (ou None)
    ultimo_fundo: Number        # preço do fundo confirmado mais recente (ou None)
    n: int                      # N do fractal de Williams efetivamente usado


@dataclass
class Niveis:
    # Zonas de Suporte/Resistência (LEVEL-01, D-10): FAIXAS (low, high), NUNCA pontos.
    # Clustering de pivôs por proximidade < cluster_k×ATR (largura adapta à volatilidade do
    # papel). Donchian 20/55 entra como faixa EXTERNA de referência (ponta de donchian_*_55).
    # Aditiva (default vazio/None) p/ manter o contrato travado 100% retrocompatível.
    suportes: list = field(default_factory=list)        # [(low, high), ...] abaixo do close
    resistencias: list = field(default_factory=list)    # [(low, high), ...] acima do close
    donchian_externo_inf: Number = None                 # ponta de donchian_inf_55
    donchian_externo_sup: Number = None                 # ponta de donchian_sup_55
    # Níveis geométricos de Fibonacci ANCORADOS no último impulso CONFIRMADO (LEVEL-02/04, D-07).
    # Aditivos (default None): faixa de entrada (retração 61,8↔38,2%), os 3 níveis nomeados, o
    # alvo (extensão 161,8%) e os DOIS pivôs âncora (timestamps+preços) p/ auditabilidade.
    entrada_zona: tuple = None                          # (low, high) = (nível 61,8%, nível 38,2%)
    fib_retracoes: dict = None                          # {"382","500","618"} → preço
    alvo: Number = None                                 # extensão de Fibonacci 161,8%
    pivos_ancora: dict = None                           # {fundo_ts,fundo_preco,topo_ts,topo_preco}
    # Stop técnico (mais conservador entre swing e ATR×m, D-08) e Risco:Retorno (RR-01, D-09).
    # Aditivos: `stop` None e `risco_retorno` "indisponivel" quando não há níveis direcionais.
    stop: Number = None                                 # stop técnico (mais distante da entrada)
    risco_retorno: str = "indisponivel"                 # "1 : 2,5" (vírgula BR) ou "indisponivel"


@dataclass
class Volume:
    # Família Volume (VOL-01, D-11): MM de volume + flag booleana de rompimento confirmado.
    # Aditiva (default None/False) — nenhum campo existente de SinaisTecnicos muda.
    volume_mm: pd.Series = None                         # MM de volume (None se sem coluna Volume)
    rompimento_com_volume: bool = False                 # rompimento Donchian sup + volume > MM
    # Flag bidirecional (Fase 14, Open Q2): volume da barra fechada > MM, AGNÓSTICO de direção.
    # Confirma rompimentos de BAIXA (duplo topo/OCO) — o detector decide a direção pela neckline.
    volume_acima_mm: bool = False                       # volume[iloc-2] > volume_mm[iloc-2]


@dataclass
class ContextoTendencia:
    # Rótulo de Dow no diário e alinhamento multi-timeframe (semanal→diário).
    # Strings estáveis/neutras (NUNCA copy natural — D-01): a renderização é da Fase 16.
    dow_diario: str             # "alta" | "baixa" | "lateral" | "indisponivel"
    alinhamento_mtf: str        # "alinhado_alta" | "alinhado_baixa" | "conflito" | "indisponivel"


@dataclass
class PadraoGrafico:
    # Padrão gráfico de Murphy detectado sobre pivôs no-repaint (PAT-01, Fase 14 plano 02/03).
    # Strings estáveis/neutras (D-01): a renderização/copy é da Fase 16, NUNCA "compre/venda".
    tipo: str                   # "duplo_topo" | "duplo_fundo" | "oco" | "oco_invertido" (chave estável)
    estado: str                 # "em_formacao" | "confirmado"
    neckline: float             # linha de pescoço (vale/pico intermediário; reta na posição de rompimento p/ OCO)
    alvo: float                 # measured-move (altura projetada além da neckline)
    altura: float               # altura do padrão (base da projeção do alvo)
    pivos_envolvidos: dict      # {ts: preco} dos pivôs âncora — auditabilidade (espelha Niveis.pivos_ancora)


@dataclass
class Padroes:
    # Lista de padrões detectados na janela (Open Q3: lista, ranqueamento é da Fase 15).
    # Aditiva (default vazio) — [] = nenhum padrão (degradação graciosa, sem exceção).
    lista: list = field(default_factory=list)           # [PadraoGrafico, ...]


@dataclass
class Sinal:
    # Sinal técnico liga/desliga do checklist (SIG-01). Apenas LÊ rótulos já computados.
    # Chaves estáveis/neutras (D-01): "ativo" = sinal disparado/relevante, NUNCA "compre/venda".
    nome: str                   # "rompimento" | "cruzamento_mm" | "rsi" | "macd" | "padrao" | "volume"
    ativo: bool                 # liga/desliga
    detalhe: str                # rótulo neutro já existente (ex.: "nova_maxima", "duplo_topo:confirmado")


@dataclass
class Checklist:
    # Agregação read-only de sinais que torna explícito *por que* o setup existe (SIG-01).
    # Aditiva (default vazio) — degradação graciosa quando nada disparou.
    sinais: list = field(default_factory=list)          # [Sinal, ...]


@dataclass
class SinaisTecnicos:
    tendencia: Tendencia
    canais: Canais
    forca: Forca
    momentum: Momentum
    # Close split-adjusted usada pelos indicadores, exposta read-only para os marcadores
    # de evento da UI (UI-04). Aditiva (default None) p/ não quebrar o contrato do plan 05-01.
    close: pd.Series = None
    # Pivôs (swing highs/lows) — primitivo da Fase 13 (S/R, Fibonacci, Dow, padrões).
    # Aditiva (default None) para manter o contrato travado 100% retrocompatível.
    pivos: "Pivos" = None
    # Contexto de tendência: Dow no diário + alinhamento semanal→diário (Fase 13 plano 02).
    # Aditiva (default None) p/ manter o contrato travado 100% retrocompatível.
    contexto: "ContextoTendencia" = None
    # Níveis geométricos: zonas de S/R por cluster de pivôs + Donchian externo (Fase 13 plano 03).
    # Aditiva (default None) p/ manter o contrato travado 100% retrocompatível.
    niveis: "Niveis" = None
    # Família Volume: MM de volume + flag de rompimento com volume (Fase 13 plano 03).
    # Aditiva (default None) p/ manter o contrato travado 100% retrocompatível.
    volume: "Volume" = None
    # Padrões gráficos (duplo topo/fundo, OCO) sobre pivôs no-repaint (Fase 14, PAT-01).
    # Aditiva (default None) p/ manter o contrato travado 100% retrocompatível.
    padroes: "Padroes" = None
    # Checklist de sinais liga/desliga — por que o setup existe (Fase 14, SIG-01).
    # Aditiva (default None) p/ manter o contrato travado 100% retrocompatível.
    checklist: "Checklist" = None


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
def atr_wilder(ohlc: pd.DataFrame, length: int = 14) -> pd.Series:
    """ATR de Wilder: 1ª suavização do True Range (start=1), 1º válido no índice `length`.

    É EXATAMENTE o `atr` interno de `adx_wilder` (D-08 manda EXPOR, não recalcular): o TR
    por barra é max(high-low, |high-prev_close|, |low-prev_close|) e a suavização é a RMA de
    Wilder SMA-seeded em `arr[1:1+length]` — `start=1` porque a barra 0 (prev_close=NaN) é o
    diff indefinido. Frame com < length+1 barras → série todo-NaN (degradação graciosa, sem
    exceção). Insumo do stop ATR×m (LEVEL-03) e das zonas S/R por proximidade<k×ATR (LEVEL-01).
    """
    high, low, close = ohlc["High"], ohlc["Low"], ohlc["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = _wilder_rma_from(tr.to_numpy(float), length, start=1)
    return pd.Series(atr, index=ohlc.index)


def adx_wilder(ohlc: pd.DataFrame, length: int = 14):
    """ADX(14) pela cadeia completa de Wilder com DUPLA suavização → (adx, pdi, ndi).

    Cadeia: +DM/-DM/TR por barra → suaviza cada um com `_wilder_rma_from` (1º válido no
    índice `length`) → +DI = 100·sm(+DM)/ATR, -DI = 100·sm(-DM)/ATR → DX = 100·|+DI−−DI|/
    (+DI+−DI) → ADX = 2ª suavização de Wilder do DX SEEDADA no primeiro DX válido
    (`start=length`). Seedar a 2ª suavização em 0 faria a SMA-seed mediar `length` NaNs →
    ADX todo-NaN (RESEARCH Pitfall 2); por isso `start=length` e o 1º ADX válido cai no
    índice 2·length−1 (= 27 para length 14). Divisões protegidas com `np.errstate`
    (ATR==0 ou +DI+−DI==0 → NaN, nunca inf; mitiga T-05-06). O ATR vem de `atr_wilder`
    (mesmo TR/suavização) — exposto aditivamente sem alterar esta assinatura (D-08).
    """
    high, low = ohlc["High"], ohlc["Low"]

    up = high.diff()
    dn = -low.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)

    # 1ª suavização de Wilder — start=1 porque a barra 0 é o diff indefinido (up/dn = NaN);
    # seedar a SMA em arr[1:1+length] coloca o 1º +DI/-DI/ATR válido no índice `length`.
    # O ATR reusa exatamente o helper público (mesma cadeia de TR) — D-08.
    atr = atr_wilder(ohlc, length).to_numpy(float)
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


def regressao_trailing(close: pd.Series, win: int = 90, periodos_ano: float = 252.0):
    """Regressão linear trailing (causal) → (slope_ann %/ano, r2) como Series (D-04).

    Para cada barra i ≥ win−1, ajusta uma reta OLS sobre a janela TRAILING de `win` barras
    via `scipy.stats.linregress`. slope_ann = slope·`periodos_ano`/média(seg)·100 (inclinação
    anualizada em %/ano, normalizada pelo nível de preço — robusta a escala, comparável entre
    tickers); r2 = rvalue². Janela só do passado → no-repaint por construção.

    `periodos_ano` é o nº de barras por ano da SÉRIE: ~252 no diário (default, mantém o golden
    diário intacto) e ~52 no semanal. Sem isso o slope semanal sairia ~4,85× inflado (WR-01).
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
            slope_ann[i] = res.slope * periodos_ano / media * 100.0 if media != 0 else np.nan
        r2[i] = res.rvalue ** 2
    return pd.Series(slope_ann, index=close.index), pd.Series(r2, index=close.index)


def _forca(ohlc: pd.DataFrame, cfg: dict) -> Forca:
    """Família Força: ADX(14) dupla-Wilder + regressão linear trailing %/ano (FORCE-01..02).

    forca_adx lê a ponta do ADX: < 20 → "sem_tendencia"; > 25 → "forte"; entre → "neutro";
    NaN (histórico curto) → "indisponivel" (degradação graciosa, DATA-03).
    """
    ind = cfg["indicadores"]
    adx, pdi, ndi = adx_wilder(ohlc, ind["adx_janela"])
    atr = atr_wilder(ohlc, ind["adx_janela"])
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
        forca_adx=forca_adx, atr=atr,
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


# --------------------------------------------------------------------------- #
# Pivôs (PIVOT-01) — fractal de Williams, CAUSAL e no-repaint (D-01/D-03)
# --------------------------------------------------------------------------- #
def _pivos(ohlc: pd.DataFrame, cfg: dict) -> Pivos:
    """Pivôs (swing highs/lows) pelo fractal de Williams — CAUSAL e no-repaint (D-01/D-03).

    Um TOPO em t é a barra cujo High é ESTRITAMENTE maior que os N Highs de cada lado
    (t-N..t-1 e t+1..t+N); o FUNDO é análogo com Low e min. A confirmação só acontece
    quando t+N FECHA e essa barra t+N NÃO é a barra viva — por isso as N+1 barras mais
    recentes ficam SEMPRE NaN (a barra viva mais as N que ainda não têm N vizinhos
    FECHADOS à direita), coerente com a invariante `iloc[-2]` da fase (D-04): o pivô mais
    recente nunca depende da última barra (não-fechada), eliminando o repaint na borda.
    Um pivô já confirmado NUNCA muda quando chegam novas barras: o
    no-repaint é trivial e determinístico (D-03). É o motivo de NÃO usar detectores por
    prominência do scipy (a prominência depende da janela e pode repaint na borda — proibido
    por D-01). Espelha a causalidade do Donchian (`.shift(1)`), mas aqui a janela é simétrica
    e o lag de N barras é o preço explícito do no-repaint.

    Degradação graciosa: frame com < 2N+2 barras → séries todo-NaN e
    `ultimo_topo`/`ultimo_fundo` None, sem levantar exceção.
    """
    ind = cfg["indicadores"]
    N = ind["pivo_n"]
    high, low = ohlc["High"], ohlc["Low"]
    n_bar = len(high)

    pivot_high = pd.Series(np.nan, index=ohlc.index)
    pivot_low = pd.Series(np.nan, index=ohlc.index)

    if n_bar >= 2 * N + 2:
        h = high.to_numpy(float)
        l = low.to_numpy(float)
        # Precisa de N vizinhos à esquerda E N FECHADOS à direita (i+N <= n_bar-2, barra
        # viva excluída). As N+1 barras finais ficam SEMPRE não-confirmadas (NaN) — o pivô
        # mais recente nunca depende da última barra (não-fechada), eliminando o repaint.
        for i in range(N, n_bar - N - 1):
            jan_h = h[i - N:i + N + 1]
            if h[i] == jan_h.max() and (jan_h == h[i]).sum() == 1:   # único máximo → estrito
                pivot_high.iloc[i] = h[i]
            jan_l = l[i - N:i + N + 1]
            if l[i] == jan_l.min() and (jan_l == l[i]).sum() == 1:   # único mínimo → estrito
                pivot_low.iloc[i] = l[i]

    topos = pivot_high.dropna()
    fundos = pivot_low.dropna()
    ultimo_topo = float(topos.iloc[-1]) if len(topos) else None
    ultimo_fundo = float(fundos.iloc[-1]) if len(fundos) else None

    return Pivos(
        pivot_high=pivot_high, pivot_low=pivot_low,
        ultimo_topo=ultimo_topo, ultimo_fundo=ultimo_fundo, n=N,
    )


# --------------------------------------------------------------------------- #
# Contexto de tendência: sequência de Dow + alinhamento multi-TF (TREND-01/02)
# --------------------------------------------------------------------------- #
# Limiares do DESEMPATE de Dow (D-05): reusam a semântica de força já existente.
_DOW_ADX_MIN = 20.0      # ADX < 20 = sem tendência mensurável (mesmo corte de _forca).
_DOW_SLOPE_BAND = 5.0    # %/ano: zona morta p/ o slope ser "claramente" direcional; dentro
                         # dela a inclinação é flat e o desempate cai para "lateral".


def _dow(pivos: "Pivos", ohlc: pd.DataFrame, cfg: dict, periodos_ano: float = 252.0) -> str:
    """Rótulo de Dow no diário a partir dos pivôs CONFIRMADOS (TREND-01, D-05).

    Regra de Dow: comparando os DOIS últimos topos e os DOIS últimos fundos confirmados —
    topos crescentes E fundos crescentes (HH+HL) → "alta"; topos decrescentes E fundos
    decrescentes (LH+LL) → "baixa". Quando a sequência é AMBÍGUA (ex.: HH+LL, ou < 2 topos /
    < 2 fundos confirmados), o DESEMPATE reusa os indicadores já existentes (NÃO reimplementa
    ADX/MM — D-05): há tendência mensurável se `adx_wilder >= 20`; a direção vem do sinal da
    inclinação anualizada de `regressao_trailing`, com uma zona morta (`_DOW_SLOPE_BAND`) para
    exigir slope "claramente" positivo/negativo — caso contrário → "lateral". ADX NaN / slope
    NaN (frame curto, sem como desempatar) → "indisponivel". Determinístico por construção.
    """
    ind = cfg["indicadores"]
    if pivos is not None:
        topos = pivos.pivot_high.dropna()
        fundos = pivos.pivot_low.dropna()
    else:
        topos = fundos = pd.Series([], dtype=float)

    if len(topos) >= 2 and len(fundos) >= 2:
        hh = topos.iloc[-1] > topos.iloc[-2]
        hl = fundos.iloc[-1] > fundos.iloc[-2]
        lh = topos.iloc[-1] < topos.iloc[-2]
        ll = fundos.iloc[-1] < fundos.iloc[-2]
        if hh and hl:
            return "alta"
        if lh and ll:
            return "baixa"

    # Sequência ambígua → desempate por inclinação/ADX já existentes (D-05).
    adx, _pdi, _ndi = adx_wilder(ohlc, ind["adx_janela"])
    slope, _r2 = regressao_trailing(
        ohlc["Close"], ind["regressao_janela"], periodos_ano=periodos_ano
    )
    # WR-03: ler a barra FECHADA (penúltimo válido, iloc[-2]) — a última barra é VIVA pela
    # invariante da fase (D-04), coerente com _volume/_niveis_sr. Guarda de comprimento ≥ 2.
    adx_v = adx.dropna()
    slope_v = slope.dropna()
    if len(adx_v) < 2 or len(slope_v) < 2:
        return "indisponivel"

    tem_tendencia = adx_v.iloc[-2] >= _DOW_ADX_MIN
    sl = slope_v.iloc[-2]
    if tem_tendencia and sl > _DOW_SLOPE_BAND:
        return "alta"
    if tem_tendencia and sl < -_DOW_SLOPE_BAND:
        return "baixa"
    return "lateral"


# --------------------------------------------------------------------------- #
# Zonas de Suporte/Resistência por cluster de pivôs (LEVEL-01, D-10)
# --------------------------------------------------------------------------- #
# Largura MÍNIMA de uma zona como fração do limiar de cluster (k×ATR). Garante que TODA zona
# seja uma FAIXA, nunca um ponto (D-10) — mesmo um cluster de um único pivô vira banda.
_SR_BANDA_MIN_FRAC = 0.5


def _clusterizar_pivos(precos_ord: list, limiar: float) -> list:
    """Funde preços ORDENADOS em zonas (low, high) por single-linkage: gap < limiar agrupa.

    Cada grupo vira uma faixa (min, max). Se o grupo for estreito demais (ou um único pivô),
    a faixa é alargada simetricamente para a largura mínima `_SR_BANDA_MIN_FRAC×limiar` —
    assim a zona é SEMPRE uma banda (low<high), nunca um ponto (D-10).
    """
    if not precos_ord or limiar <= 0:
        return []
    min_w = _SR_BANDA_MIN_FRAC * limiar
    zonas = []
    grupo = [precos_ord[0]]
    for p in precos_ord[1:]:
        if p - grupo[-1] < limiar:
            grupo.append(p)
        else:
            zonas.append(_zona_banda(grupo, min_w))
            grupo = [p]
    zonas.append(_zona_banda(grupo, min_w))
    return zonas


def _zona_banda(grupo: list, min_w: float) -> tuple:
    """Faixa (low, high) do grupo, alargada para a largura mínima quando degenerada."""
    low, high = min(grupo), max(grupo)
    if high - low < min_w:
        centro = (low + high) / 2.0
        low, high = centro - min_w / 2.0, centro + min_w / 2.0
    return (low, high)


def _niveis_sr(
    pivos: "Pivos",
    ohlc: pd.DataFrame,
    atr: pd.Series,
    donchian_inf_55: pd.Series,
    donchian_sup_55: pd.Series,
    cfg: dict,
) -> Niveis:
    """Zonas de S/R por cluster de pivôs (proximidade < cluster_k×ATR) + Donchian externo.

    S/R são FAIXAS, nunca pontos (D-10): os preços de pivôs CONFIRMADOS (pivot_high+pivot_low)
    são fundidos em zonas (low,high) cuja largura adapta à volatilidade do papel (k×ATR — mais
    robusto entre tickers B3 que um % fixo). A classificação é vs o close da barra FECHADA
    (`iloc[-2]`, D-04 herdado): zonas abaixo → suportes (mais próximo primeiro); acima →
    resistências. O Donchian 20/55 (ponta de donchian_*_55, já causal `.shift(1)`) entra como
    faixa EXTERNA de referência. Os PREÇOS vêm do frame recebido (nominal quando `ohlc_nominal`
    é dado a `calcular` — D-02); o ATR é o insumo de volatilidade da cadeia do ADX.

    Degradação graciosa: sem pivôs / ATR todo-NaN / frame < 2 barras → zonas vazias e
    referências None, sem levantar exceção (mitiga T-13-06; sem div-zero — só agrupa com ATR>0).
    """
    ind = cfg["indicadores"]
    k = ind["cluster_k"]

    di = donchian_inf_55.dropna() if donchian_inf_55 is not None else pd.Series([], dtype=float)
    ds = donchian_sup_55.dropna() if donchian_sup_55 is not None else pd.Series([], dtype=float)
    don_inf = float(di.iloc[-1]) if len(di) else None
    don_sup = float(ds.iloc[-1]) if len(ds) else None

    suportes: list = []
    resistencias: list = []

    close = ohlc["Close"] if "Close" in ohlc.columns else pd.Series([], dtype=float)
    atr_validos = atr.dropna() if atr is not None else pd.Series([], dtype=float)

    if pivos is not None and len(atr_validos) and len(close) >= 2:
        precos = pd.concat([pivos.pivot_high.dropna(), pivos.pivot_low.dropna()])
        atr_val = float(atr_validos.iloc[-1])
        if len(precos) and atr_val > 0:
            ref = float(close.iloc[-2])                      # barra FECHADA (D-04)
            limiar = k * atr_val
            zonas = _clusterizar_pivos(sorted(precos.to_numpy(float)), limiar)
            for low, high in zonas:
                if (low + high) / 2.0 <= ref:
                    suportes.append((low, high))
                else:
                    resistencias.append((low, high))
            # ordena por proximidade ao close (mais próximo primeiro)
            suportes.sort(key=lambda z: ref - (z[0] + z[1]) / 2.0)
            resistencias.sort(key=lambda z: (z[0] + z[1]) / 2.0 - ref)

    return Niveis(
        suportes=suportes, resistencias=resistencias,
        donchian_externo_inf=don_inf, donchian_externo_sup=don_sup,
    )


# --------------------------------------------------------------------------- #
# Níveis de Fibonacci ancorados no último impulso confirmado (LEVEL-02/04, D-07)
# --------------------------------------------------------------------------- #
# Retração de ENTRADA (clássica) e extensão de ALVO.
_FIB_RETRACOES = (("382", 0.382), ("500", 0.5), ("618", 0.618))
_FIB_EXTENSAO = 1.618


def _niveis_fib(
    niveis: Niveis, pivos: "Pivos", contexto: "ContextoTendencia",
    ohlc_nominal: pd.DataFrame, cfg: dict,
) -> None:
    """Níveis de Fibonacci ANCORADOS no último impulso CONFIRMADO (LEVEL-02/04, D-07).

    A âncora é o par de pivôs mais recente COERENTE com a tendência diária (`contexto.dow_diario`):
    em "alta" o impulso é fundo→topo (o último TOPO confirmado e o último FUNDO confirmado ANTES
    dele); em "baixa" é topo→fundo (o último FUNDO e o último TOPO antes dele). Como os dois pivôs
    são CONFIRMADOS (fractal de Williams — imutáveis, gate do plano 01), os níveis NUNCA repaint
    (mitiga T-13-10); os dois pivôs âncora ficam documentados em `pivos_ancora` (timestamps+preços)
    para auditabilidade (D-07).

    Sobre o range (topo−fundo): retração de ENTRADA em 38,2/50/61,8% (`fib_retracoes` + a faixa
    `entrada_zona` 61,8↔38,2%) e extensão de ALVO em 161,8%. Em "alta" a retração desce do topo e
    o alvo projeta ACIMA do topo; em "baixa" espelha (retração medida do fundo para cima, alvo
    projetado ABAIXO do fundo). Os PREÇOS são os dos pivôs — que `calcular` já computa sobre o
    frame NOMINAL (D-02), logo são preços nominais.

    Degradação graciosa (mitiga T-13-11): tendência "lateral"/"indisponivel" ou sem par de pivôs
    confirmado coerente → `entrada_zona`/`alvo`/`pivos_ancora`/`fib_retracoes` permanecem None
    (níveis direcionais não fazem sentido sem tendência), sem levantar exceção. Muta `niveis`.
    """
    dow = contexto.dow_diario if contexto is not None else "indisponivel"
    if dow not in ("alta", "baixa") or pivos is None:
        return

    topos = pivos.pivot_high.dropna()
    fundos = pivos.pivot_low.dropna()

    if dow == "alta":
        if not len(topos):
            return
        topo_ts, topo_preco = topos.index[-1], float(topos.iloc[-1])
        fundos_antes = fundos[fundos.index < topo_ts]
        if not len(fundos_antes):
            return
        fundo_ts, fundo_preco = fundos_antes.index[-1], float(fundos_antes.iloc[-1])
    else:  # baixa
        if not len(fundos):
            return
        fundo_ts, fundo_preco = fundos.index[-1], float(fundos.iloc[-1])
        topos_antes = topos[topos.index < fundo_ts]
        if not len(topos_antes):
            return
        topo_ts, topo_preco = topos_antes.index[-1], float(topos_antes.iloc[-1])

    rng = topo_preco - fundo_preco
    if rng <= 0:                                  # par incoerente (topo ≤ fundo) → não ancora
        return

    if dow == "alta":
        fib = {nome: topo_preco - rng * f for nome, f in _FIB_RETRACOES}
        entrada_zona = (topo_preco - rng * 0.618, topo_preco - rng * 0.382)
        alvo = fundo_preco + rng * _FIB_EXTENSAO
    else:
        fib = {nome: fundo_preco + rng * f for nome, f in _FIB_RETRACOES}
        entrada_zona = (fundo_preco + rng * 0.382, fundo_preco + rng * 0.618)
        alvo = topo_preco - rng * _FIB_EXTENSAO

    niveis.entrada_zona = entrada_zona
    niveis.fib_retracoes = fib
    niveis.alvo = alvo
    niveis.pivos_ancora = {
        "fundo_ts": fundo_ts, "fundo_preco": fundo_preco,
        "topo_ts": topo_ts, "topo_preco": topo_preco,
    }


def _niveis_stop_rr(
    niveis: Niveis, contexto: "ContextoTendencia", atr: pd.Series,
    ohlc_nominal: pd.DataFrame, cfg: dict,
) -> None:
    """Stop técnico (mais conservador entre swing e ATR×m) + Risco:Retorno (LEVEL-03, RR-01).

    Stop (D-08): o mais CONSERVADOR (mais DISTANTE da entrada) entre o swing estrutural (preço do
    pivô âncora — fundo em "alta", topo em "baixa") e ATR×m — respeita a estrutura sem ficar
    apertado demais. Em "alta" `stop = min(swing, entrada_ref − m·ATR)` (o mais baixo); em "baixa"
    `stop = max(swing, entrada_ref + m·ATR)` (o mais alto). `entrada_ref` = ponto médio da
    `entrada_zona`. `m = cfg["indicadores"]["stop_atr_m"]`; o ATR é REUSADO (`atr_wilder`, último
    valor válido), NUNCA recalculado (D-08).

    R:R (D-09): `risco = |entrada_ref − stop|`, `retorno = |alvo − entrada_ref|`, formatado como
    `"1 : {retorno/risco}"` com vírgula decimal BR (1 casa). A razão usa `np.divide` sob
    `np.errstate` (divisão por zero → inf, não exceção); `risco ≤ 0`, NaN/inf, ou `entrada_zona`/
    `alvo`/`pivos_ancora` ausentes → `risco_retorno = "indisponivel"`, NUNCA infinito (mitiga
    T-13-09).

    Degradação graciosa: sem `entrada_zona`/`alvo` (lateral/indisponivel), sem âncora, ou sem ATR
    válido → `stop` permanece None e `risco_retorno` "indisponivel", sem exceção. Muta `niveis`.
    """
    if niveis.entrada_zona is None or niveis.alvo is None or niveis.pivos_ancora is None:
        return
    dow = contexto.dow_diario if contexto is not None else "indisponivel"
    if dow not in ("alta", "baixa"):
        return

    atr_validos = atr.dropna() if atr is not None else pd.Series([], dtype=float)
    if not len(atr_validos):
        return
    atr_val = float(atr_validos.iloc[-1])
    m = cfg["indicadores"]["stop_atr_m"]

    low, high = niveis.entrada_zona
    entrada_ref = (low + high) / 2.0

    if dow == "alta":
        swing = niveis.pivos_ancora["fundo_preco"]
        atr_stop = entrada_ref - m * atr_val
        stop = min(swing, atr_stop)               # mais distante para BAIXO (mais conservador)
    else:
        swing = niveis.pivos_ancora["topo_preco"]
        atr_stop = entrada_ref + m * atr_val
        stop = max(swing, atr_stop)               # mais distante para CIMA (mais conservador)
    niveis.stop = stop

    risco = abs(entrada_ref - stop)
    retorno = abs(niveis.alvo - entrada_ref)
    # Razão protegida: risco==0 → np.divide dá inf (não exceção, sob errstate) → "indisponivel".
    with np.errstate(divide="ignore", invalid="ignore"):
        razao = np.divide(retorno, risco)
    if risco <= 0 or not np.isfinite(razao):
        niveis.risco_retorno = "indisponivel"
    else:
        niveis.risco_retorno = "1 : " + f"{float(razao):.1f}".replace(".", ",")


# --------------------------------------------------------------------------- #
# Família Volume — MM de volume + flag rompimento com volume (VOL-01, D-11)
# --------------------------------------------------------------------------- #
def _volume(ohlc: pd.DataFrame, cfg: dict) -> Volume:
    """MM de volume + flag booleana "rompimento da Donchian superior COM volume" (VOL-01).

    `volume_mm` = média móvel do volume com `min_periods == volume_janela` (NaN com histórico
    curto, NUNCA valor parcial — alimenta a degradação). A flag é avaliada na barra FECHADA
    (`iloc[-2]`, D-04 herdado, sem repaint da barra viva): True só quando o close fechado rompe
    a banda Donchian superior CAUSAL (`.shift(1)`, mesmo idioma de `_canais`) E o volume da barra
    fechada está acima da `volume_mm` da barra fechada.

    Degradação graciosa (mitiga T-13-07/08): frame SEM coluna `Volume` → `Volume()` default
    (volume_mm None, flag False) antes de qualquer cálculo; frame curto → volume_mm todo-NaN e
    flag False (protegida contra NaN). 100% aditiva — nenhum campo existente de SinaisTecnicos muda.
    """
    ind = cfg["indicadores"]
    if "Volume" not in ohlc.columns or len(ohlc) == 0:
        return Volume()

    vol = ohlc["Volume"]
    janela = ind["volume_janela"]
    volume_mm = vol.rolling(janela, min_periods=janela).mean()

    flag = False
    flag_vol = False
    if len(ohlc) >= 2:
        j_curto = ind["donchian"][0]
        donchian_sup = ohlc["High"].rolling(j_curto, min_periods=j_curto).max().shift(1)
        dsup_f = donchian_sup.iloc[-2]        # canal causal na barra fechada
        vmm_f = volume_mm.iloc[-2]
        vol_f = vol.iloc[-2]
        close_f = ohlc["Close"].iloc[-2]
        # Parte AGNÓSTICA de direção (Open Q2): só compara volume fechado vs MM fechada.
        # Mesmo guard pd.isna; NÃO cria segunda MM (reusa vmm_f/vol_f já computados).
        if not (pd.isna(vmm_f) or pd.isna(vol_f)):
            flag_vol = bool(vol_f > vmm_f)
        if not (pd.isna(dsup_f) or pd.isna(vmm_f) or pd.isna(vol_f)):
            flag = bool(close_f > dsup_f and vol_f > vmm_f)

    return Volume(volume_mm=volume_mm, rompimento_com_volume=flag, volume_acima_mm=flag_vol)


# --------------------------------------------------------------------------- #
# Entry-point — agrega as 4 famílias sobre o OHLC split-adjusted (CR-01)
# --------------------------------------------------------------------------- #
_COLUNAS_OHLC = ("Open", "High", "Low", "Close")


def _contexto(ohlc: pd.DataFrame, cfg: dict) -> ContextoTendencia:
    """Contexto de tendência: Dow no diário + alinhamento semanal→diário (TREND-01/02).

    `dow_diario` = `_dow` sobre o frame recebido. O SEMANAL é derivado por resample W-FRI do
    PRÓPRIO frame (D-04: sem nova chamada de rede, sem buscar o timeframe semanal do Yahoo) — idioma idêntico
    ao de `report.py`, guardado por `DatetimeIndex` + colunas OHLC; sem isso o alinhamento
    degrada para "indisponivel" sem exceção (mitiga T-13-04). Sobre o semanal recomputa
    `_pivos`+`_dow` e rotula o alinhamento: ambos "alta" → "alinhado_alta"; ambos "baixa" →
    "alinhado_baixa"; qualquer divergência (inclusive um lado "lateral") → "conflito"; lado
    sem dado → "indisponivel".

    D-06: o conflito é APENAS um rótulo aditivo — NUNCA zera, NUNCA levanta, NUNCA altera os
    demais campos de SinaisTecnicos. Ele MODULA (penaliza) o score na Fase 15, jamais bloqueia
    o setup aqui (mitiga T-13-05).
    """
    dow_diario = _dow(_pivos(ohlc, cfg), ohlc, cfg)

    pode_semanal = (
        ohlc is not None
        and len(ohlc) > 0
        and isinstance(ohlc.index, pd.DatetimeIndex)
        and set(_COLUNAS_OHLC).issubset(ohlc.columns)
    )
    if pode_semanal:
        semanal = ohlc.resample("W-FRI").agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
        ).dropna()
        # WR-02: a SEMANA corrente (ainda aberta) repinta intra-semana — seu candle muda a
        # cada novo dia. Se o period_end (sexta) da última barra semanal for FUTURO em
        # relação ao último dia diário, a semana não fechou → descarta-a (não-confirmada),
        # coerente com a invariante iloc[-2] da fase.
        if len(semanal) and semanal.index[-1].normalize() > ohlc.index[-1].normalize():
            semanal = semanal.iloc[:-1]
        # WR-01: o slope é anualizado por ~52 barras/ano no semanal (não 252 do diário),
        # senão sairia ~4,85× inflado e quase toda inclinação viraria "direcional".
        dow_semanal = _dow(_pivos(semanal, cfg), semanal, cfg, periodos_ano=52.0)
    else:
        dow_semanal = "indisponivel"

    if dow_diario == "indisponivel" or dow_semanal == "indisponivel":
        alinhamento = "indisponivel"
    elif dow_diario == "alta" and dow_semanal == "alta":
        alinhamento = "alinhado_alta"
    elif dow_diario == "baixa" and dow_semanal == "baixa":
        alinhamento = "alinhado_baixa"
    else:
        alinhamento = "conflito"

    return ContextoTendencia(dow_diario=dow_diario, alinhamento_mtf=alinhamento)


def calcular(
    ohlc: "pd.DataFrame", cfg: dict, ohlc_nominal: "pd.DataFrame | None" = None
) -> SinaisTecnicos:
    """Ponto de entrada único: devolve um `SinaisTecnicos` completo (4 famílias).

    Guard na borda (espelha `ddm.ddm_dois_estagios`, mitiga T-05-05): se `ohlc` é None,
    vazio ou não tem as colunas OHLC, substitui por um frame vazio e ROTEIA pelas funções
    de família — a degradação para "indisponivel" fica em um lugar só. Nunca levanta exceção
    na aba do Streamlit. Consome SEMPRE o frame split-adjusted (CR-01) e é agnóstico de
    timeframe (recebe o frame que lhe derem; o resample semanal é da Phase 6).

    D-02 (herdado da Fase 12): níveis de PREÇO (pivôs + zonas S/R) usam o frame NOMINAL quando
    `ohlc_nominal` é fornecido; os indicadores/contexto continuam sobre o split-adjusted (`ohlc`).
    O parâmetro é OPCIONAL e ADITIVO — chamadas existentes (sem `ohlc_nominal`) usam o próprio
    `ohlc` e ficam idênticas (os 191 goldens fundamentalistas e os técnicos seguem inalterados).
    """
    if ohlc is None or len(ohlc) == 0 or not set(_COLUNAS_OHLC).issubset(ohlc.columns):
        ohlc = pd.DataFrame({c: pd.Series(dtype=float) for c in _COLUNAS_OHLC})

    # Frame das famílias de PREÇO (D-02): nominal quando fornecido e válido; senão o próprio ohlc.
    if (
        ohlc_nominal is not None
        and len(ohlc_nominal) > 0
        and set(_COLUNAS_OHLC).issubset(ohlc_nominal.columns)
    ):
        nominal = ohlc_nominal
    else:
        nominal = ohlc

    close = ohlc["Close"]
    canais = _canais(ohlc, cfg)
    forca = _forca(ohlc, cfg)
    pivos = _pivos(nominal, cfg)   # família de PREÇO → frame nominal (D-02)
    contexto = _contexto(ohlc, cfg)
    niveis = _niveis_sr(
        pivos, nominal, forca.atr, canais.donchian_inf_55, canais.donchian_sup_55, cfg
    )
    # Fibonacci ancorado no último impulso confirmado (LEVEL-02/04, D-07) — mescla no Niveis.
    _niveis_fib(niveis, pivos, contexto, nominal, cfg)
    # Stop técnico (mais conservador, D-08) + R:R formatado/degradável (RR-01, D-09).
    _niveis_stop_rr(niveis, contexto, forca.atr, nominal, cfg)
    return SinaisTecnicos(
        tendencia=_tendencia(close, cfg),
        canais=canais,
        forca=forca,
        momentum=_momentum(close, cfg),
        close=close,   # read-only: a MESMA close split-adjusted já usada (não recalcula)
        pivos=pivos,
        contexto=contexto,
        niveis=niveis,
        volume=_volume(ohlc, cfg),
    )
