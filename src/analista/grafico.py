"""Montagem do gráfico técnico — funções PURAS + dataclasses de spec (Phase 7).

Este módulo é o CONTRATO de interface que os planos de `app.py` (04/05) consomem: a decisão de
QUAIS overlays/subpainéis/marcadores desenhar, em que ordem, com quais séries e quais níveis de
referência, vive aqui — coberta por golden — porque a verificação visual de Streamlit é difícil de
automatizar (deep_work_rules do CONTEXT). O `app.py` vira fina camada de render: NÃO mapeia
nome→série nem hardcoda níveis (20/25, 30/70, 0); tudo já vem nos specs.

Read-only sobre `a.sinais` (`SinaisTecnicos`): nenhuma fórmula de indicador é recalculada aqui.
SEM dependência de streamlit/plotly — as funções devolvem dados/specs, não objetos de figura.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# Dataclasses de spec — o que o app.py converte em traces
# --------------------------------------------------------------------------- #
@dataclass
class OverlaySpec:
    """Uma linha desenhada SOBRE o eixo de preço (MM / Donchian / Bollinger)."""
    nome: str
    serie: pd.Series
    estilo: dict = field(default_factory=dict)   # dica leve: {color, width, dash}


@dataclass
class SubpainelSpec:
    """Um subpainel de oscilador: carrega as séries E os níveis de referência (no módulo puro)."""
    nome: str
    series: List[Tuple[str, pd.Series]]          # [(rótulo, série), ...]
    referencias: List[float]                     # linhas horizontais de referência


@dataclass
class Marcador:
    """Marcador de evento numa data EXATA (golden/death cross, rompimento Donchian)."""
    data: pd.Timestamp
    y: float
    tipo: str                                    # golden_cross | death_cross | nova_maxima | perda_minima
    rotulo: str                                  # nome do evento em PT (hover)


# Paleta herdada do gráfico atual (preço #1f77b4); cores como dica leve de discrição.
_COR_MM = {20: "#ff7f0e", 50: "#2ca02c", 200: "#d62728"}
_COR_DONCHIAN = "#9467bd"
_COR_BOLLINGER = "#7f7f7f"


# --------------------------------------------------------------------------- #
# Estado dos toggles — técnico OFF por padrão (UI-06)
# --------------------------------------------------------------------------- #
def estado_padrao() -> dict:
    """Estado inicial dos controles: TODAS as famílias OFF (nada desenhado por padrão)."""
    return {
        "tendencia": {"on": False, "tipo": "sma", "janelas": [20, 50, 200]},
        "canais": {"donchian_on": False, "donchian_janela": 20, "bollinger_on": False},
        "forca": {"on": False},
        "momentum": {"rsi_on": False, "macd_on": False},
    }


def _merge(estado: Optional[dict]) -> dict:
    """Funde o estado (possivelmente parcial/inesperado) sobre os defaults (mitiga T-07-04)."""
    base = estado_padrao()
    if not estado:
        return base
    for familia, defaults in base.items():
        user = estado.get(familia) or {}
        base[familia] = {**defaults, **user}
    return base


def _tem_ponto_valido(serie: Optional[pd.Series]) -> bool:
    """True se a série existe e tem ≥1 ponto não-NaN (degradação DATA-03 / T-07-05)."""
    return serie is not None and bool(serie.notna().any())


# --------------------------------------------------------------------------- #
# Overlays no eixo de preço (UI-01/UI-03) — devolve SPEC completo (série + estilo)
# --------------------------------------------------------------------------- #
def overlays_preco(estado: Optional[dict], sinais) -> List[OverlaySpec]:
    """Lista de OverlaySpec a desenhar sobre o preço, derivada SÓ do estado + a.sinais.

    Estado OFF ⇒ lista vazia. Tendência: tipo "ema" usa ema*, "sma" usa sma*; `janelas`
    controla quais MMs. Canais: donchian_janela 55 ⇒ séries longas; bollinger_on ⇒ bb_*.
    """
    if sinais is None:
        return []
    est = _merge(estado)
    out: List[OverlaySpec] = []

    t = est["tendencia"]
    if t.get("on"):
        tipo = (t.get("tipo") or "sma").lower()
        tend = sinais.tendencia
        if tipo == "ema":
            mapa = {20: tend.ema20, 50: tend.ema50, 200: tend.ema200}
        else:
            mapa = {20: tend.sma20, 50: tend.sma50, 200: tend.sma200}
        for j in t.get("janelas") or [20, 50, 200]:
            serie = mapa.get(j)
            if serie is None:
                continue
            out.append(OverlaySpec(
                nome=f"{tipo.upper()}{j}",
                serie=serie,
                estilo={"color": _COR_MM.get(j, "#888888"), "width": 1.5},
            ))

    c = est["canais"]
    if c.get("donchian_on"):
        canais = sinais.canais
        if c.get("donchian_janela") == 55:
            sup, inf, sufixo = canais.donchian_sup_55, canais.donchian_inf_55, "55"
        else:
            sup, inf, sufixo = canais.donchian_sup, canais.donchian_inf, "20"
        estilo_d = {"color": _COR_DONCHIAN, "width": 1.0, "dash": "dot"}
        if sup is not None:
            out.append(OverlaySpec(f"Donchian Sup ({sufixo})", sup, dict(estilo_d)))
        if inf is not None:
            out.append(OverlaySpec(f"Donchian Inf ({sufixo})", inf, dict(estilo_d)))

    if c.get("bollinger_on"):
        canais = sinais.canais
        out.append(OverlaySpec("Bollinger Sup", canais.bb_sup,
                               {"color": _COR_BOLLINGER, "width": 1.0, "dash": "dash"}))
        out.append(OverlaySpec("Bollinger Méd", canais.bb_med,
                               {"color": _COR_BOLLINGER, "width": 1.0}))
        out.append(OverlaySpec("Bollinger Inf", canais.bb_inf,
                               {"color": _COR_BOLLINGER, "width": 1.0, "dash": "dash"}))

    return out


# --------------------------------------------------------------------------- #
# Subpainéis de osciladores (UI-02) — ordem fixa, série(s) + níveis de referência
# --------------------------------------------------------------------------- #
def subpaineis_ativos(estado: Optional[dict], sinais) -> List[SubpainelSpec]:
    """SubpainelSpec na ordem ["adx","rsi","macd"]: só toggles ON com série principal válida.

    O SPEC carrega o mapeamento nome→série(s) E os níveis de referência (no módulo puro,
    não no app.py): adx→[20,25], rsi→[30,70], macd→[0]. Série principal toda-NaN (histórico
    curto) NÃO cria subpainel (degradação DATA-03).
    """
    if sinais is None:
        return []
    est = _merge(estado)
    out: List[SubpainelSpec] = []

    forca = sinais.forca
    momentum = sinais.momentum

    if est["forca"].get("on") and _tem_ponto_valido(forca.adx):
        out.append(SubpainelSpec("adx", [("ADX", forca.adx)], [20.0, 25.0]))

    if est["momentum"].get("rsi_on") and _tem_ponto_valido(momentum.rsi):
        out.append(SubpainelSpec("rsi", [("RSI", momentum.rsi)], [30.0, 70.0]))

    if est["momentum"].get("macd_on") and _tem_ponto_valido(momentum.macd):
        out.append(SubpainelSpec(
            "macd",
            [("MACD", momentum.macd), ("Sinal", momentum.macd_sinal), ("Histograma", momentum.macd_hist)],
            [0.0],
        ))

    return out


# --------------------------------------------------------------------------- #
# Enquadramento dos subplots (UI-03) — preço dominante + osciladores proporcionais
# --------------------------------------------------------------------------- #
def layout_subplots(n_subpaineis: int) -> dict:
    """rows=1+n e row_heights (somam 1.0) com o preço como maior fração."""
    if n_subpaineis <= 0:
        return {"rows": 1, "row_heights": [1.0]}
    preco = 0.55
    resto = (1.0 - preco) / n_subpaineis
    return {"rows": 1 + n_subpaineis, "row_heights": [preco] + [resto] * n_subpaineis}
