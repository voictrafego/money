"""Ingestão intraday multi-timeframe (offline, zero rede).

Cobre `intraday.coletar_intraday` / `FrameOHLC` / `_PERIODO_POR_TF` (Fase 12,
v1.4): matriz period×interval, normalização de timezone, barra viva clock-free,
`atraso_min` determinístico (agora injetável) e degradação graciosa (frame curto,
vazio, exceção, timeframe inválido) — nunca exceção. Nenhum teste bate na rede:
tudo via fixtures locais e monkeypatch de `_yf`/`time.sleep` (padrão de
test_ingest_ohlc.py).
"""

import numpy as np  # noqa: F401  (paridade com test_ingest_ohlc.py)
import pandas as pd
import pytest

from analista.ingest import intraday


# ---------------------------------------------------------------------------
# Fixtures de hist intraday (OHLCV + Stock Splits), última barra viva (Volume=0)
# ---------------------------------------------------------------------------

def _frame_5min(periods=6, tz="America/Sao_Paulo", inicio="2026-06-29 10:00"):
    """Frame OHLCV 5m com `periods` barras; última barra com Volume=0 (viva)."""
    idx = pd.date_range(inicio, periods=periods, freq="5min", tz=tz)
    close = pd.Series([10.0 + i for i in range(periods)], index=idx, dtype=float)
    volume = [100.0] * (periods - 1) + [0.0]  # última barra em formação (vol 0)
    return pd.DataFrame({
        "Open": close - 0.1, "High": close + 0.2, "Low": close - 0.2,
        "Close": close, "Adj Close": close * 0.9,
        "Volume": pd.Series(volume, index=idx),
        "Stock Splits": pd.Series([0.0] * periods, index=idx),
        "Dividends": pd.Series([0.0] * periods, index=idx),
    }, index=idx)


class _TkIntraday:
    def history(self, *a, **k):
        return _frame_5min()


class _TkVazio:
    def history(self, *a, **k):
        return pd.DataFrame()


class _TkExcecao:
    def history(self, *a, **k):
        raise RuntimeError("rate-limit do Yahoo")


class _TkUmaBarra:
    def history(self, *a, **k):
        return _frame_5min(periods=1)


class _TkNaiveUTC:
    def history(self, *a, **k):
        # índice tz-naive (edge: download multi-símbolo); valores ~UTC
        f = _frame_5min(inicio="2026-06-29 13:00")
        f.index = f.index.tz_localize(None)
        return f


class _TkComSplit:
    """Frame intraday com 1 split de fator 2.0 numa barra intermediária."""
    def history(self, *a, **k):
        f = _frame_5min(periods=6)
        # base "cara" pré-split, "barata" pós-split (split na barra 3)
        f["Close"] = [200.0, 202.0, 204.0, 103.0, 104.0, 105.0]
        f["Open"] = f["Close"] - 0.1
        f["High"] = f["Close"] + 0.2
        f["Low"] = f["Close"] - 0.2
        f["Stock Splits"] = [0.0, 0.0, 0.0, 2.0, 0.0, 0.0]
        return f


def _monkeypatch_yf(monkeypatch, tk_cls):
    class _YF:
        @staticmethod
        def Ticker(sym):
            return tk_cls()

    monkeypatch.setattr(intraday.prices, "_yf", lambda: _YF())
    monkeypatch.setattr(intraday.time, "sleep", lambda *_: None)


# ---------------------------------------------------------------------------
# Matriz period×interval (DATA-01)
# ---------------------------------------------------------------------------

def test_mapa_tf_period_interval():
    """A tabela é cravada nos tetos da Yahoo [VERIFIED] — exatamente os 4 TFs."""
    assert intraday._PERIODO_POR_TF == {
        "diario": ("5y", "1d"),
        "1h": ("730d", "1h"),
        "30m": ("60d", "30m"),
        "5m": ("60d", "5m"),
    }


def test_tf_invalido():
    """timeframe fora do conjunto fechado -> disponivel=False, sem exceção (T-12-01)."""
    f = intraday.coletar_intraday("PETR4", "15m_xyz")
    assert f.disponivel is False
    assert f.motivo == "timeframe_invalido"
    assert f.ohlc is None


# ---------------------------------------------------------------------------
# Reuso do split-adjust (DATA-01 / D-02)
# ---------------------------------------------------------------------------

def test_ohlc_ajustado_reusa_split(monkeypatch):
    """ohlc_ajustado == prices._ajustar_por_split(hist): ponta recente coincide
    com o nominal (após o último split o fator cumulativo é 1)."""
    _monkeypatch_yf(monkeypatch, _TkComSplit)
    f = intraday.coletar_intraday("PETR4", "5m",
                                  agora=pd.Timestamp("2026-06-29 10:40", tz="America/Sao_Paulo"))
    assert f.ohlc_ajustado is not None
    # ponta recente coincide com o nominal (espelha test_ponta_recente_coincide_com_nominal)
    assert f.ohlc_ajustado["Close"].iloc[-1] == f.ohlc["Close"].iloc[-1]
    # pré-split foi escalado para baixo (÷2)
    assert f.ohlc_ajustado["Close"].iloc[0] == pytest.approx(f.ohlc["Close"].iloc[0] / 2.0)


# ---------------------------------------------------------------------------
# Normalização de timezone (DATA-01 / Pitfall 5)
# ---------------------------------------------------------------------------

def test_tz_normaliza_naive(monkeypatch):
    """Índice naive (assumido UTC) -> índice final em America/Sao_Paulo (-03:00)."""
    _monkeypatch_yf(monkeypatch, _TkNaiveUTC)
    f = intraday.coletar_intraday("PETR4", "5m",
                                  agora=pd.Timestamp("2026-06-29 12:00", tz="America/Sao_Paulo"))
    assert f.disponivel is True
    assert "Sao_Paulo" in str(f.ohlc.index.tz)


def test_tz_idempotente_sao_paulo(monkeypatch):
    """Índice já em America/Sao_Paulo permanece America/Sao_Paulo (idempotente)."""
    _monkeypatch_yf(monkeypatch, _TkIntraday)
    f = intraday.coletar_intraday("PETR4", "5m",
                                  agora=pd.Timestamp("2026-06-29 10:40", tz="America/Sao_Paulo"))
    assert "Sao_Paulo" in str(f.ohlc.index.tz)


# ---------------------------------------------------------------------------
# Barra viva clock-free + atraso injetável (DATA-02 / D-04 / Pitfalls 2-3)
# ---------------------------------------------------------------------------

def test_idx_ultima_fechada_clock_free(monkeypatch):
    """Fixture 6 barras, última Volume=0 -> idx_ultima_fechada == len-2, barra_viva True."""
    _monkeypatch_yf(monkeypatch, _TkIntraday)
    f = intraday.coletar_intraday("PETR4", "5m",
                                  agora=pd.Timestamp("2026-06-29 10:40", tz="America/Sao_Paulo"))
    assert f.disponivel is True
    assert f.idx_ultima_fechada == len(f.ohlc) - 2
    assert f.barra_viva is True
    assert f.ohlc["Volume"].iloc[-1] == 0  # confirma a barra viva da fixture


def test_atraso_min_injetavel(monkeypatch):
    """agora=Timestamp fixo -> atraso_min == (agora - ultima_barra_ts) em minutos."""
    _monkeypatch_yf(monkeypatch, _TkIntraday)
    # última barra da fixture (6x 5min a partir de 10:00) = 10:25; agora 10:40 => 15min
    f = intraday.coletar_intraday("PETR4", "5m",
                                  agora=pd.Timestamp("2026-06-29 10:40", tz="America/Sao_Paulo"))
    assert f.atraso_min == pytest.approx(15.0)
    assert f.ultima_barra_ts == pd.Timestamp("2026-06-29 10:25", tz="America/Sao_Paulo")


# ---------------------------------------------------------------------------
# Frame curto (DATA-02 / Pitfall 4 / A3)
# ---------------------------------------------------------------------------

def test_frame_curto_historico_insuficiente(monkeypatch):
    """Fixture com 1 barra -> idx_ultima_fechada is None, motivo=historico_insuficiente."""
    _monkeypatch_yf(monkeypatch, _TkUmaBarra)
    f = intraday.coletar_intraday("PETR4", "5m",
                                  agora=pd.Timestamp("2026-06-29 10:40", tz="America/Sao_Paulo"))
    assert f.idx_ultima_fechada is None
    assert f.motivo == "historico_insuficiente"


def test_disponivel_true_frame_curto(monkeypatch):
    """Fixture com 1 barra -> disponivel=True (há barra p/ o gráfico, A3)."""
    _monkeypatch_yf(monkeypatch, _TkUmaBarra)
    f = intraday.coletar_intraday("PETR4", "5m",
                                  agora=pd.Timestamp("2026-06-29 10:40", tz="America/Sao_Paulo"))
    assert f.disponivel is True
    assert f.barra_viva is True


# ---------------------------------------------------------------------------
# Vazio / exceção (DATA-02 / D-06) — nunca exceção
# ---------------------------------------------------------------------------

def test_vazio_sem_dados(monkeypatch):
    """history() vazio -> disponivel=False, motivo=sem_dados, sem exceção."""
    _monkeypatch_yf(monkeypatch, _TkVazio)
    f = intraday.coletar_intraday("PETR4", "5m")
    assert f.disponivel is False
    assert f.motivo == "sem_dados"
    assert f.ohlc is None


def test_excecao_fetch_falhou(monkeypatch):
    """history() levanta em todas as tentativas -> disponivel=False, motivo=fetch_falhou."""
    _monkeypatch_yf(monkeypatch, _TkExcecao)
    f = intraday.coletar_intraday("PETR4", "5m")
    assert f.disponivel is False
    assert f.motivo == "fetch_falhou"
    assert f.ohlc is None
