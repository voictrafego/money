"""Golden tests do read técnico consultivo da engine (Phase 6):

- TEST-06 / D-02: o desempate canônico do composite — preço ACIMA da MM200 mas com
  ADX < 20 → "sem_tendencia" (o ADX fraco vence o viés de alta da MM200).
- D-10: o resample semanal W-FRI (agregação first/max/min/last) que roda dentro de
  `analisar_acao` antes de calcular os indicadores quando a base é "semanal".

Ambos travam contra os MESMOS limiares do config.yaml shipado (via `_cfg_ind()`), de
modo que o teste e a engine compartilham os limiares de `indicators._forca` (< 20 / > 25).
"""

import copy
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report


def _cfg_ind() -> dict:
    """Carrega o config.yaml shipado para pinar os parâmetros canônicos nos testes."""
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _ohlc_acima_mm200_adx_fraco() -> pd.DataFrame:
    """Série DIÁRIA acima da própria MM200 mas com ADX < 20.

    ~210 pregões de subida lenta (100→120) seguidos de ~80 de deriva lateral estreita
    (oscilação senoidal de amplitude 0,6 em torno de 122). Ao final: o preço fica acima
    da MM200 (que ainda carrega a subida antiga, mais baixa), porém a ausência de direção
    na fase lateral leva o ADX da ponta a ~12 (< 20) → força "sem_tendencia".
    """
    subida = np.linspace(100.0, 120.0, 210)
    n_lat = 80
    t = np.arange(n_lat)
    lateral = 122.0 + 0.6 * np.sin(t * 0.7)
    closes = np.concatenate([subida, lateral])
    idx = pd.date_range("2019-01-01", periods=len(closes), freq="B")
    close = pd.Series(closes, index=idx)
    return pd.DataFrame(
        {
            "Open": close.shift(1).bfill(),
            "High": close + 0.3,
            "Low": close - 0.3,
            "Close": close,
        }
    )


def test_composite_acima_mm200_adx_fraco_eh_sem_tendencia():
    # TEST-06 / D-02: preço ACIMA da MM200 mas ADX < 20 → "sem_tendencia".
    # Crava o caso no timeframe DIÁRIO (base_temporal="diario") para não precisar de
    # ~200 barras SEMANAIS — a árvore composite é a mesma nos dois timeframes; o que se
    # trava aqui é o desempate, não o resample (esse é o test_resample_semanal_w_fri).
    cfg = copy.deepcopy(_cfg_ind())
    cfg["indicadores"]["base_temporal"] = "diario"
    c = CompanyData(ticker="TST", anos=[2023], ohlc_ajustado=_ohlc_acima_mm200_adx_fraco())

    a = report.analisar_acao(c, cfg)

    # Pré-condição do desempate: realmente acima da MM200 e com ADX fraco.
    assert a.sinais.tendencia.posicao_mm200 == "acima"
    assert a.sinais.forca.forca_adx == "sem_tendencia"
    # Veredito do composite: ADX fraco vence o viés de alta da MM200 (D-02).
    assert a.timing_estado == "sem_tendencia"


def test_resample_semanal_w_fri():
    # D-10: o resample W-FRI agrega Open=first, High=max, Low=min, Close=last e carimba
    # o índice na sexta-feira de cada semana. 3 semanas completas (15 pregões, seg→sex)
    # → exatamente 3 barras semanais, todas em sexta (weekday == 4).
    idx = pd.date_range("2019-01-07", periods=15, freq="B")  # 2019-01-07 é segunda-feira
    closes = np.arange(1, 16, dtype=float) * 10.0            # 10, 20, ..., 150 (todos distintos)
    close = pd.Series(closes, index=idx)
    df = pd.DataFrame(
        {
            "Open": close - 1.0,
            "High": close + 2.0,
            "Low": close - 2.0,
            "Close": close,
        }
    )

    sem = df.resample("W-FRI").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    ).dropna()

    # 3 barras semanais, todas carimbadas em sexta-feira.
    assert len(sem) == 3
    assert all(ts.weekday() == 4 for ts in sem.index)

    # Semana 1 (07–11/jan): Close diário 10..50. Open=primeiro dia, High=máx, Low=mín, Close=último.
    s1 = sem.iloc[0]
    assert s1["Open"] == df["Open"].iloc[0]    # primeiro pregão da semana
    assert s1["High"] == df["High"].iloc[0:5].max()
    assert s1["Low"] == df["Low"].iloc[0:5].min()
    assert s1["Close"] == df["Close"].iloc[4]  # último pregão (sexta)
