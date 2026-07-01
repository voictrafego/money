"""Contrato never-raise do agregador da Home (Fase 18): home_feed.cotacoes() em lote.

Tudo via monkeypatch de `prices._yf` (mesmo padrão de test_ingest_intraday.py) — sem
rede. Trava: uma chamada `yf.download` em lote, variação do dia (close[-1]/close[-2]-1),
degradação por item (ok=False sem derrubar a lista) e ordem de saída == ordem de entrada.
"""
from __future__ import annotations

import pandas as pd
import pytest

from analista.core import home_feed
from analista.ingest import prices


# ---------------------------------------------------------------------------
# Fixtures: DataFrame no formato de yf.download(group_by="ticker")
# ---------------------------------------------------------------------------

def _df_lote(precos_por_sym: dict) -> pd.DataFrame:
    """DataFrame estilo yf.download(group_by='ticker'): colunas MultiIndex (sym, campo)."""
    idx = pd.date_range("2026-06-25", periods=5, freq="B")
    blocos = {}
    for sym, closes in precos_por_sym.items():
        for campo in ("Open", "High", "Low", "Close", "Adj Close", "Volume"):
            valores = closes if campo == "Close" else [c + 0.1 for c in closes]
            blocos[(sym, campo)] = pd.Series(valores, index=idx, dtype=float)
    df = pd.DataFrame(blocos)
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    return df


def _patch_download(monkeypatch, df, contador=None):
    class _YF:
        @staticmethod
        def download(*a, **k):
            if contador is not None:
                contador.append(k)
            if df is None:
                raise RuntimeError("rate-limit do Yahoo")
            return df

    monkeypatch.setattr(prices, "_yf", lambda: _YF())


# ---------------------------------------------------------------------------
# Contrato + variação do dia
# ---------------------------------------------------------------------------

def test_cotacoes_contrato_e_variacao_do_dia(monkeypatch):
    """ok=True, preço = última Close, pct = close[-1]/close[-2]-1 sobre barras diárias."""
    df = _df_lote({
        "BBSE3.SA": [30.0, 31.0, 32.0, 33.0, 40.0],
        "TAEE11.SA": [11.0, 11.0, 11.0, 12.0, 12.0],
    })
    _patch_download(monkeypatch, df)

    r = home_feed.cotacoes(("BBSE3", "TAEE11"))

    assert isinstance(r, list) and len(r) == 2
    for item in r:
        assert set(item.keys()) == {"ticker", "preco", "pct", "ok"}

    bbse, taee = r
    assert bbse["ticker"] == "BBSE3" and bbse["ok"] is True
    assert bbse["preco"] == pytest.approx(40.0)
    assert bbse["pct"] == pytest.approx(40.0 / 33.0 - 1.0)
    assert taee["ticker"] == "TAEE11" and taee["ok"] is True
    assert taee["preco"] == pytest.approx(12.0)
    assert taee["pct"] == pytest.approx(0.0)


def test_cotacoes_uma_unica_chamada_em_lote(monkeypatch):
    """Anti-pattern proibido: 1 download por ticker num loop. Deve ser UMA chamada."""
    contador = []
    df = _df_lote({"BBSE3.SA": [30.0, 31.0, 32.0, 33.0, 40.0],
                   "TAEE11.SA": [11.0, 11.0, 11.0, 12.0, 12.0],
                   "EGIE3.SA": [40.0, 41.0, 42.0, 43.0, 44.0]})
    _patch_download(monkeypatch, df, contador)

    home_feed.cotacoes(("BBSE3", "TAEE11", "EGIE3"))

    assert len(contador) == 1, "cotacoes deve fazer UMA chamada yf.download em lote"
    # period fixo "5d" (nunca derivado do input)
    assert contador[0].get("period") == "5d"


def test_cotacoes_degrada_por_item(monkeypatch):
    """Ticker sem dado no frame degrada (ok=False) sem contaminar os demais; ordem preservada."""
    df = _df_lote({"BBSE3.SA": [30.0, 31.0, 32.0, 33.0, 40.0]})  # TAEE11 ausente
    _patch_download(monkeypatch, df)

    r = home_feed.cotacoes(("BBSE3", "TAEE11"))

    assert [x["ticker"] for x in r] == ["BBSE3", "TAEE11"]
    assert r[0]["ok"] is True and r[0]["preco"] == pytest.approx(40.0)
    assert r[1]["ok"] is False and r[1]["preco"] is None and r[1]["pct"] is None


def test_cotacoes_download_falha_never_raise(monkeypatch):
    """Yahoo em falha total (download levanta) → todos ok=False, sem exceção."""
    _patch_download(monkeypatch, None)

    r = home_feed.cotacoes(("BBSE3", "TAEE11"))

    assert len(r) == 2
    assert all(x["ok"] is False and x["preco"] is None and x["pct"] is None for x in r)


def test_cotacoes_offline_contrato(monkeypatch):
    """Sem rede (import real do yfinance falharia ou retornaria vazio) — nunca levanta."""
    class _YFVazio:
        @staticmethod
        def download(*a, **k):
            return pd.DataFrame()

    monkeypatch.setattr(prices, "_yf", lambda: _YFVazio())

    r = home_feed.cotacoes(("BBSE3", "BADXX"))
    assert isinstance(r, list) and len(r) == 2
    assert all(set(x.keys()) == {"ticker", "preco", "pct", "ok"} for x in r)
    assert all(x["ok"] is False for x in r)


def test_cotacoes_vazio(monkeypatch):
    """Watchlist vazia → lista vazia, sem tocar a rede."""
    contador = []
    _patch_download(monkeypatch, pd.DataFrame(), contador)
    assert home_feed.cotacoes(()) == []
    assert contador == [], "watchlist vazia não deve chamar o Yahoo"
