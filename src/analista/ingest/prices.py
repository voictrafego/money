"""Preços, dividendos e mercado via yfinance (Yahoo Finance) — grátis.

Fornece: preço atual, histórico de dividendos por ano, nº de ações, liquidez (volume
financeiro médio diário), beta (vs ^BVSP) e desempenho relativo de 6 meses.

Limitação conhecida: o Yahoo agrega proventos e NÃO separa JCP de dividendo. Para
proventos auditáveis use a CVM como backstop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from ..core import capm

INDICE_MERCADO = "^BVSP"


def _yf():
    import yfinance as yf  # import tardio: dependência pesada
    return yf


def yahoo_symbol(ticker: str) -> str:
    t = ticker.upper().strip()
    return t if t.endswith(".SA") else f"{t}.SA"


@dataclass
class DadosMercado:
    ticker: str
    preco_atual: Optional[float] = None
    num_acoes: Optional[float] = None
    setor: str = ""
    nome: str = ""
    volume_financeiro_diario: Optional[float] = None
    beta: Optional[float] = None
    desempenho_relativo_6m: Optional[float] = None
    dividendos_por_ano: Dict[int, float] = field(default_factory=dict)


def _retornos_mensais(hist) -> list:
    mensal = hist["Close"].resample("ME").last()
    ret = mensal.pct_change().dropna()
    return list(ret.values)


def coletar_mercado(ticker: str, meses_beta: int = 60) -> DadosMercado:
    yf = _yf()
    sym = yahoo_symbol(ticker)
    tk = yf.Ticker(sym)
    dm = DadosMercado(ticker=ticker.upper())

    info = {}
    try:
        info = tk.info or {}
    except Exception:
        info = {}
    dm.preco_atual = info.get("currentPrice") or info.get("regularMarketPrice")
    dm.num_acoes = info.get("sharesOutstanding")
    dm.setor = info.get("sector", "") or info.get("industry", "")
    dm.nome = info.get("longName", "") or info.get("shortName", "")

    # histórico de preços (para liquidez, beta e desempenho relativo)
    try:
        hist = tk.history(period="5y", auto_adjust=True)
    except Exception:
        hist = None

    if hist is not None and not hist.empty:
        if dm.preco_atual is None:
            dm.preco_atual = float(hist["Close"].iloc[-1])
        ult_ano = hist.tail(252)
        dm.volume_financeiro_diario = float((ult_ano["Close"] * ult_ano["Volume"]).mean())

        # beta e desempenho relativo precisam do índice
        try:
            idx = yf.Ticker(INDICE_MERCADO).history(period="5y", auto_adjust=True)
        except Exception:
            idx = None
        if idx is not None and not idx.empty:
            ra = _retornos_mensais(hist)[-meses_beta:]
            rm = _retornos_mensais(idx)[-meses_beta:]
            n = min(len(ra), len(rm))
            if n >= 2:
                dm.beta = capm.beta(ra[-n:], rm[-n:])
            # desempenho relativo dos últimos 6 meses (~126 pregões)
            ret_acao = hist["Close"].iloc[-1] / hist["Close"].iloc[-126] - 1 if len(hist) > 126 else None
            ret_idx = idx["Close"].iloc[-1] / idx["Close"].iloc[-126] - 1 if len(idx) > 126 else None
            if ret_acao is not None and ret_idx is not None:
                dm.desempenho_relativo_6m = float(ret_acao - ret_idx)

    # dividendos por ano
    try:
        divs = tk.dividends
        if divs is not None and not divs.empty:
            por_ano: Dict[int, float] = {}
            for data, valor in divs.items():
                por_ano[data.year] = por_ano.get(data.year, 0.0) + float(valor)
            dm.dividendos_por_ano = por_ano  # dividendo POR AÇÃO por ano
    except Exception:
        pass

    return dm
