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
    ohlc: Optional["pd.DataFrame"] = None           # frame OHLCV nominal 5a (Yahoo cru, auto_adjust=False)
    ohlc_ajustado: Optional["pd.DataFrame"] = None  # OHLCV split-only-adjusted p/ indicadores (Phase 5)
    serie_precos_ajustada: Optional["pd.Series"] = None  # Adj Close diário 5a — retorno total c/ dividendos reinvestidos; p/ RET-01, mesma origem do beta, sem rede nova


def _retornos_mensais(precos) -> list:
    """Retornos mensais a partir de uma série de preços (ajustada p/ beta)."""
    mensal = precos.resample("ME").last()
    ret = mensal.pct_change().dropna()
    return list(ret.values)


def _ajustar_por_split(hist) -> Optional["pd.DataFrame"]:
    """Série/frame OHLCV ajustada SÓ por splits (D-03/D-05) — função pura.

    Deriva o ajuste da coluna "Stock Splits" que já vem dentro do `hist` (auto_adjust=
    False), sem nenhuma chamada de rede (D-04). NÃO usa "Adj Close" (que mistura
    proventos — anti-pattern explícito): os indicadores técnicos precisam de preço
    split-adjusted, não dividend-adjusted.

    Regra (D-05): calcula o fator de split CUMULATIVO de trás para frente — para cada
    data, o produto dos splits que ocorrem ESTRITAMENTE DEPOIS dela. Assim, após o
    último split o fator é 1.0 e a ponta recente da ajustada coincide com a nominal.
    Open/High/Low/Close são divididos pelo fator (preços antigos escalados para a base
    recente) e Volume é multiplicado pelo fator (sentido inverso). Colunas não-OHLCV
    (Adj Close/Dividends/Stock Splits) são copiadas inalteradas.

    Tolera frame sem a coluna "Stock Splits" (retorna cópia inalterada) e frame vazio
    (retorna None), sem estourar. Não muta o frame de entrada.
    """
    if hist is None or hist.empty:
        return None

    aj = hist.copy(deep=True)
    if "Stock Splits" not in aj.columns:
        return aj

    splits = aj["Stock Splits"].fillna(0.0)
    # fator de split em cada dia: o próprio valor quando > 0, senão 1.0 (sem evento)
    fator_dia = splits.where(splits > 0, 1.0)
    # fator cumulativo "para frente": produto dos splits que ocorrem APÓS cada data.
    # cumprod reverso de fator_dia inclui o split do próprio dia; dividimos por ele
    # para que a data DO split já fique na base recente (sem salto na data do split).
    cum_rev = fator_dia[::-1].cumprod()[::-1]
    fator_cumulativo = cum_rev / fator_dia

    for col in ("Open", "High", "Low", "Close"):
        if col in aj.columns:
            aj[col] = aj[col] / fator_cumulativo
    if "Volume" in aj.columns:
        aj["Volume"] = aj["Volume"] * fator_cumulativo

    return aj


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

    # histórico de preços (para liquidez, beta e desempenho relativo).
    # auto_adjust=False traz Close NOMINAL (R$ correntes) + Adj Close (retroajustado):
    #   - serie_precos e preço-fallback usam Close nominal, p/ ficar na MESMA base que a
    #     banda DDM (vmin/vmax nominais) — senão o gráfico mostraria preços históricos
    #     retroajustados abaixo do nominal, distorcendo a leitura da margem de segurança;
    #   - beta e desempenho relativo usam Adj Close (retorno total, com proventos).
    try:
        hist = tk.history(period="5y", auto_adjust=False)
    except Exception:
        hist = None

    if hist is not None and not hist.empty:
        nominal = hist["Close"].dropna()
        # beta/desempenho relativo (abaixo) toleram fallback p/ Close nominal — é só um
        # proxy de retorno; RET-01 (serie_precos_ajustada) NÃO tolera (ver abaixo).
        ajustado = hist["Adj Close"] if "Adj Close" in hist else hist["Close"]
        dm.serie_precos = nominal
        # RET-01: SÓ persiste Adj Close real (retorno total, com proventos). Sem "Adj Close"
        # deixa None p/ a lente degradar — NUNCA usar Close nominal como se fosse retorno
        # total reinvestido (WR-02: a UI rotula RET-01 como "com dividendos reinvestidos").
        if "Adj Close" in hist:
            dm.serie_precos_ajustada = hist["Adj Close"].dropna()  # Adj Close 5a (mesma origem do beta, sem rede nova)
        else:
            dm.serie_precos_ajustada = None
        dm.ohlc = hist                               # frame OHLCV nominal completo (D-01: nada descartado)
        dm.ohlc_ajustado = _ajustar_por_split(hist)  # split-only-adjusted derivado de "Stock Splits" (D-03/D-05)
        if dm.preco_atual is None and len(nominal):
            dm.preco_atual = float(nominal.iloc[-1])
        ult_ano = hist.tail(252)
        dm.volume_financeiro_diario = float((ult_ano["Close"] * ult_ano["Volume"]).mean())

        # beta e desempenho relativo precisam do índice
        try:
            idx = yf.Ticker(INDICE_MERCADO).history(period="5y", auto_adjust=False)
        except Exception:
            idx = None
        if idx is not None and not idx.empty:
            idx_aj = idx["Adj Close"] if "Adj Close" in idx else idx["Close"]
            ra = _retornos_mensais(ajustado)[-meses_beta:]
            rm = _retornos_mensais(idx_aj)[-meses_beta:]
            n = min(len(ra), len(rm))
            if n >= 2:
                dm.beta = capm.beta(ra[-n:], rm[-n:])
            # desempenho relativo dos últimos 6 meses (~126 pregões)
            ret_acao = ajustado.iloc[-1] / ajustado.iloc[-126] - 1 if len(ajustado) > 126 else None
            ret_idx = idx_aj.iloc[-1] / idx_aj.iloc[-126] - 1 if len(idx_aj) > 126 else None
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
