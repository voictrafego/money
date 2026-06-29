"""Ingestão de OHLCV multi-timeframe (intraday) via yfinance — grátis.

Camada de borda PARALELA e ISOLADA de `prices.coletar_mercado` (firewall com o
pipeline fundamentalista / aba Analisar): só muda `period`/`interval` e o
empacotamento no dataclass rico `FrameOHLC`. Reusa as funções puras de `prices`
(resolução `.SA`, retry calibrado, split-adjust) — não reimplementa nada.

Contrato (v1.4, Fase 12):
- `coletar_intraday(ticker, timeframe)` NUNCA levanta exceção nem devolve None:
  qualquer falha/vazio retorna `FrameOHLC(disponivel=False)` com `motivo` categorizado.
- Índice normalizado para America/Sao_Paulo, imune ao TZ do processo (VPS=UTC).
- A última barra é SEMPRE tratada como potencialmente viva (`barra_viva`); cálculos
  da Fase 13 usam a barra fechada via `iloc[-2]` (`idx_ultima_fechada = len-2`),
  detecção clock-free (sem relógio/calendário B3).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from . import prices  # reuso: yahoo_symbol, _ajustar_por_split, _yf, _MAX_TENTATIVAS, _BACKOFF_SEG

_TZ_B3 = "America/Sao_Paulo"

# Tabela period×interval CRAVADA nos tetos da Yahoo (confirmados empiricamente,
# RESEARCH §"Tabela period×interval" [VERIFIED]). Exceder o teto NÃO clampa:
# a Yahoo devolve frame VAZIO. NUNCA derivar `period` do input do usuário.
_PERIODO_POR_TF = {
    "diario": ("5y", "1d"),
    "1h": ("730d", "1h"),    # teto HARD ≤ 730 dias corridos
    "30m": ("60d", "30m"),   # teto HARD ≤ 60 dias corridos
    "5m": ("60d", "5m"),     # teto HARD ≤ 60 dias corridos
}

# Categorias de `motivo` (D-07) — a UI (Fase 16) mapeia para copy amigável; a
# copy NÃO vive nesta camada de dados.
MOTIVO_OK = ""
MOTIVO_TF_INVALIDO = "timeframe_invalido"
MOTIVO_FETCH_FALHOU = "fetch_falhou"
MOTIVO_SEM_DADOS = "sem_dados"
MOTIVO_HIST_INSUF = "historico_insuficiente"


@dataclass
class FrameOHLC:
    timeframe: str
    ohlc: Optional["pd.DataFrame"] = None           # frame OHLCV nominal (gráfico + níveis entrada/stop/alvo)
    ohlc_ajustado: Optional["pd.DataFrame"] = None  # split-only-adjusted p/ indicators.calcular (Fase 13)
    ultima_barra_ts: Optional["pd.Timestamp"] = None
    barra_viva: bool = False                         # True = última barra suspeita (em formação)
    idx_ultima_fechada: Optional[int] = None         # índice da última barra FECHADA (len-2); None se len<2
    atraso_min: Optional[float] = None               # (agora - ultima_barra_ts) em minutos; informacional
    disponivel: bool = False
    motivo: str = MOTIVO_SEM_DADOS


def _normaliza_tz(df: "pd.DataFrame") -> "pd.DataFrame":
    """Índice -> America/Sao_Paulo, determinístico e imune ao TZ do processo (VPS=UTC).

    yfinance .SA já entrega o índice tz-aware America/Sao_Paulo; `tz_convert` é
    idempotente nesse caso. Edge (download multi-símbolo / versão futura): índice
    naive é assumido UTC antes de converter (Pitfall 5 — evita TypeError).
    """
    idx = df.index
    if getattr(idx, "tz", None) is None:
        df.index = idx.tz_localize("UTC").tz_convert(_TZ_B3)
    else:
        df.index = idx.tz_convert(_TZ_B3)
    return df


def coletar_intraday(ticker: str, timeframe: str,
                     agora: Optional["pd.Timestamp"] = None) -> FrameOHLC:
    """Fetch OHLCV de um ticker no timeframe pedido — nunca exceção (D-06/D-07)."""
    # V5 input validation: timeframe contra o conjunto fechado (T-12-01 tampering)
    if timeframe not in _PERIODO_POR_TF:
        return FrameOHLC(timeframe=timeframe, disponivel=False, motivo=MOTIVO_TF_INVALIDO)

    period, interval = _PERIODO_POR_TF[timeframe]
    sym = prices.yahoo_symbol(ticker)
    yf = prices._yf()

    # retry com backoff LIMITADO (T-12-03 DoS): sucesso = frame não-vazio
    hist = None
    for tentativa in range(prices._MAX_TENTATIVAS):
        try:
            hist = yf.Ticker(sym).history(period=period, interval=interval, auto_adjust=False)
        except Exception:
            hist = None
        if hist is not None and not hist.empty:
            break
        if tentativa < prices._MAX_TENTATIVAS - 1:
            time.sleep(prices._BACKOFF_SEG[min(tentativa, len(prices._BACKOFF_SEG) - 1)])

    # guard de borda: degradação graciosa, nunca exceção
    if hist is None:
        return FrameOHLC(timeframe=timeframe, disponivel=False, motivo=MOTIVO_FETCH_FALHOU)
    if hist.empty:
        return FrameOHLC(timeframe=timeframe, disponivel=False, motivo=MOTIVO_SEM_DADOS)

    hist = _normaliza_tz(hist)
    ohlc_aj = prices._ajustar_por_split(hist)  # reuso direto da função pura (sem rede)

    # metadados clock-free de barra viva (D-04)
    n = len(hist)
    ultima_ts = hist.index[-1]
    idx_fechada = n - 2 if n >= 2 else None
    if agora is None:
        agora = pd.Timestamp.now(tz=_TZ_B3)
    atraso = float((agora - ultima_ts).total_seconds() / 60.0)

    return FrameOHLC(
        timeframe=timeframe,
        ohlc=hist,
        ohlc_ajustado=ohlc_aj,
        ultima_barra_ts=ultima_ts,
        barra_viva=(n >= 1),  # última barra SEMPRE suspeita (conservador)
        idx_ultima_fechada=idx_fechada,
        atraso_min=atraso,
        disponivel=True,  # há barra(s) p/ o gráfico mesmo com histórico curto (A3)
        motivo=(MOTIVO_HIST_INSUF if idx_fechada is None else MOTIVO_OK),
    )
