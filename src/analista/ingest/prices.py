"""Preços, dividendos e mercado via yfinance (Yahoo Finance) — grátis.

Fornece: preço atual, histórico de dividendos por ano, nº de ações, liquidez (volume
financeiro médio diário), beta (vs ^BVSP) e desempenho relativo de 6 meses.

Limitação conhecida: o Yahoo agrega proventos e NÃO separa JCP de dividendo. Para
proventos auditáveis use a CVM como backstop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from ..core import capm

INDICE_MERCADO = "^BVSP"

# O rate-limit por IP de datacenter do Yahoo é intermitente: um fetch pode falhar
# ou voltar vazio e o seguinte (segundos depois) ter sucesso. Re-tentamos algumas
# vezes com backoff curto antes de desistir.
_MAX_TENTATIVAS = 3
_BACKOFF_SEG = (0.5, 1.0)


def _yf():
    import yfinance as yf  # import tardio: dependência pesada
    return yf


def _fetch_info(tk) -> dict:
    """Obtém o `info` do Ticker do Yahoo; {} em qualquer falha (mockável nos testes)."""
    try:
        return tk.info or {}
    except Exception:
        return {}


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
    dpa_trailing_12m: Optional[float] = None  # soma dos proventos/ação dos últimos 12 meses reais
    ano_dpa: Optional[int] = None             # ano da última data de provento (ano-base do DPA)
    serie_precos: Optional["pd.Series"] = None  # close diário 5a (índice = datas) p/ o gráfico


def _retornos_mensais(hist) -> list:
    mensal = hist["Close"].resample("ME").last()
    ret = mensal.pct_change().dropna()
    return list(ret.values)


def coletar_mercado(ticker: str, meses_beta: int = 60) -> DadosMercado:
    yf = _yf()
    sym = yahoo_symbol(ticker)
    tk = yf.Ticker(sym)
    dm = DadosMercado(ticker=ticker.upper())

    # retry do fetch do info: tentativa "falha" = sem nome E sem preço (ou exceção)
    info: dict = {}
    for tentativa in range(_MAX_TENTATIVAS):
        try:
            info = _fetch_info(tk)
        except Exception:
            info = {}
        tem_nome = bool(info.get("longName") or info.get("shortName"))
        tem_preco = info.get("currentPrice") is not None or info.get("regularMarketPrice") is not None
        if tem_nome or tem_preco:
            break
        if tentativa < _MAX_TENTATIVAS - 1:
            time.sleep(_BACKOFF_SEG[min(tentativa, len(_BACKOFF_SEG) - 1)])
    # ao esgotar as tentativas seguimos com info possivelmente {} (desistência, sem exceção)

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
        dm.serie_precos = hist["Close"].dropna()
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

    # dividendos por ano + soma trailing-12m pelas datas reais (para o DY corrente)
    try:
        divs = tk.dividends
        if divs is not None and not divs.empty:
            import pandas as pd

            por_ano: Dict[int, float] = {}
            for data, valor in divs.items():
                por_ano[data.year] = por_ano.get(data.year, 0.0) + float(valor)
            dm.dividendos_por_ano = por_ano  # dividendo POR AÇÃO por ano

            ult_data = divs.index.max()
            dm.ano_dpa = int(ult_data.year)
            # janela de 12 meses ancorada na última data de provento (tz-aware compatível)
            corte = ult_data - pd.Timedelta(days=365)
            trailing = float(divs[divs.index > corte].sum())
            dm.dpa_trailing_12m = trailing if trailing > 0 else None
    except Exception:
        pass

    return dm
