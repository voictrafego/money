"""Golden das funções puras de montagem do gráfico técnico (Phase 7 — UI-01..04).

Trava a LÓGICA de quais overlays/subpainéis/marcadores desenhar, em que ordem, com quais
séries e quais níveis de referência — tudo no módulo puro `grafico.py`, sem streamlit/plotly.
A camada de render (app.py, Plans 04/05) só consome estes specs. Verificação visual de
Streamlit é difícil de automatizar; por isso a decisão vive aqui, coberta por golden.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from analista.core import indicators
from analista.grafico import (
    OverlaySpec,
    SubpainelSpec,
    estado_padrao,
    layout_subplots,
    overlays_preco,
    subpaineis_ativos,
)


def _cfg() -> dict:
    """Parâmetros canônicos shipados (mesma fonte dos golden da engine)."""
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _close_valido(n: int = 300) -> pd.Series:
    """Série crescente longa o suficiente para todas as famílias terem ponto válido."""
    idx = pd.date_range("2019-01-01", periods=n, freq="B")
    return pd.Series(np.linspace(50.0, 150.0, n), index=idx)


def _sinais(close: pd.Series) -> indicators.SinaisTecnicos:
    """SinaisTecnicos sintético via a engine (High=Low=Close p/ um plot determinístico)."""
    ohlc = pd.DataFrame({"Open": close, "High": close, "Low": close, "Close": close})
    return indicators.calcular(ohlc, _cfg())


# --------------------------------------------------------------------------- #
# estado_padrao — técnico OFF por padrão (UI-06)
# --------------------------------------------------------------------------- #
def test_estado_padrao_tudo_off():
    sinais = _sinais(_close_valido())
    est = estado_padrao()
    assert est["tendencia"]["on"] is False
    assert est["canais"]["donchian_on"] is False
    assert est["canais"]["bollinger_on"] is False
    assert est["forca"]["on"] is False
    assert est["momentum"]["rsi_on"] is False
    assert est["momentum"]["macd_on"] is False
    # Estado OFF ⇒ nenhum overlay/subpainel desenhado.
    assert overlays_preco(est, sinais) == []
    assert subpaineis_ativos(est, sinais) == []


# --------------------------------------------------------------------------- #
# overlays_preco — SMA vs EMA + janelas selecionadas (UI-01/UI-03)
# --------------------------------------------------------------------------- #
def test_overlays_sma_vs_ema_e_janelas():
    sinais = _sinais(_close_valido())
    est = estado_padrao()
    est["tendencia"] = {"on": True, "tipo": "sma", "janelas": [50, 200]}
    ov = overlays_preco(est, sinais)
    assert all(isinstance(o, OverlaySpec) for o in ov)
    assert [o.nome for o in ov] == ["SMA50", "SMA200"]
    assert ov[0].serie.equals(sinais.tendencia.sma50)
    assert ov[1].serie.equals(sinais.tendencia.sma200)

    est["tendencia"]["tipo"] = "ema"
    ov = overlays_preco(est, sinais)
    assert [o.nome for o in ov] == ["EMA50", "EMA200"]
    assert ov[0].serie.equals(sinais.tendencia.ema50)
    assert ov[1].serie.equals(sinais.tendencia.ema200)


def test_overlays_donchian_55_e_bollinger():
    sinais = _sinais(_close_valido())
    est = estado_padrao()
    est["canais"] = {"donchian_on": True, "donchian_janela": 55, "bollinger_on": True}
    ov = overlays_preco(est, sinais)
    by_nome = {o.nome: o for o in ov}
    # Donchian 55 ⇒ usa as séries longas.
    sup55 = next(o for n, o in by_nome.items() if "55" in n and "Sup" in n)
    assert sup55.serie.equals(sinais.canais.donchian_sup_55)
    # Bollinger ⇒ as três séries (sup/méd/inf).
    nomes_bb = [n for n in by_nome if "Bollinger" in n]
    assert len(nomes_bb) == 3
    sup_bb = next(o for n, o in by_nome.items() if "Bollinger" in n and "Sup" in n)
    assert sup_bb.serie.equals(sinais.canais.bb_sup)


# --------------------------------------------------------------------------- #
# subpaineis_ativos — ordem fixa + série(s) + níveis de referência (UI-02)
# --------------------------------------------------------------------------- #
def test_subpaineis_ordem_series_e_referencias():
    sinais = _sinais(_close_valido())
    est = estado_padrao()
    est["forca"] = {"on": True}
    est["momentum"] = {"rsi_on": True, "macd_on": True}
    sp = subpaineis_ativos(est, sinais)
    assert all(isinstance(s, SubpainelSpec) for s in sp)
    assert [s.nome for s in sp] == ["adx", "rsi", "macd"]
    adx, rsi, macd = sp

    assert [rotulo for rotulo, _ in adx.series] == ["ADX"]
    assert adx.referencias == [20.0, 25.0]
    assert adx.series[0][1].equals(sinais.forca.adx)

    assert [rotulo for rotulo, _ in rsi.series] == ["RSI"]
    assert rsi.referencias == [30.0, 70.0]
    assert rsi.series[0][1].equals(sinais.momentum.rsi)

    assert [rotulo for rotulo, _ in macd.series] == ["MACD", "Sinal", "Histograma"]
    assert macd.referencias == [0.0]
    assert macd.series[0][1].equals(sinais.momentum.macd)


def test_subpainel_degrada_serie_toda_nan():
    # 25 barras: ADX (precisa de 27) fica toda-NaN ⇒ não cria subpainel; RSI (14) tem ponto válido.
    sinais = _sinais(_close_valido(25))
    est = estado_padrao()
    est["forca"] = {"on": True}
    est["momentum"] = {"rsi_on": True, "macd_on": True}
    nomes = [s.nome for s in subpaineis_ativos(est, sinais)]
    assert "adx" not in nomes
    assert "rsi" in nomes


# --------------------------------------------------------------------------- #
# layout_subplots — 1+n linhas, row_heights somando 1.0, preço dominante (UI-03)
# --------------------------------------------------------------------------- #
def test_layout_subplots():
    l0 = layout_subplots(0)
    assert l0["rows"] == 1
    assert l0["row_heights"] == [1.0]

    l2 = layout_subplots(2)
    assert l2["rows"] == 3
    assert sum(l2["row_heights"]) == pytest.approx(1.0)
    assert l2["row_heights"][0] == max(l2["row_heights"])
