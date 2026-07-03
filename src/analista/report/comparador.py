"""Comparador lado a lado de N tickers (Fase 21 / COMP-02, COMP-03).

Toda a DERIVAÇÃO do 5º menu "Comparar ações" vive AQUI, na engine (gate do projeto:
`app.py` read-only para lógica). Monta uma tabela TRANSPOSTA — tickers nas COLUNAS,
métricas nas LINHAS na ordem fixa "Selo","P/L","P/VP","ROE","DY","Valor de Mercado" —
reusando 100% da engine já testada por golden:

- os 5 múltiplos vêm de `lentes.metricas_par` (fonte canônica, COMP-02);
- o Selo COMPLETO (quadrante qualidade×preço) vem de `report.analisar_acao(...).selo` +
  `presentation.selo_badge` — não o atalho só-cor (COMP-03);
- regra de suficiência ≥2 (`.suficiente`), sem alvo/ranking/sort (D2/D4).

Never-raise: um contexto que quebre `analisar_acao`/`metricas_par` degrada SÓ a sua coluna
(célula "—"); as demais aparecem. NÃO importa `app` nem faz fetch de rede — a rede fica na
UI (cacheada). Zero dependência 3rd-party nova (só `analista.*` + pandas já instalado).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

import pandas as pd

from ..core import lentes
from . import presentation, report

if TYPE_CHECKING:
    from ..core.fundamentals import CompanyData

# Ordem fixa das linhas (métricas) — "Selo" no topo de cada coluna (COMP-03).
_ORDEM_LINHAS = ["Selo", "P/L", "P/VP", "ROE", "DY", "Valor de Mercado"]


@dataclass
class ComparativoTabela:
    """Resultado do comparador: DataFrame transposto + flag de suficiência (≥2)."""

    df: pd.DataFrame
    suficiente: bool


def _selo_completo(c: "CompanyData", cfg: dict) -> str:
    """Selo COMPLETO (quadrante) de um ticker via a porta canônica. Falha/ausência → "—"."""
    try:
        a = report.analisar_acao(c, cfg)
        if a.selo is not None and a.selo.cor is not None:
            return presentation.selo_badge(
                a.selo.cor, a.selo.rotulo, a.selo.qualidade, a.selo.verificar
            )
    except Exception:
        return "—"
    return "—"


def _coluna(c: "CompanyData", cfg: dict) -> dict:
    """Dict-de-métricas (linhas) de um ticker, na ordem fixa. Never-raise por coluna."""
    selo_txt = _selo_completo(c, cfg)
    try:
        p = lentes.metricas_par(c)
        valor_mercado = (
            presentation.fmt_rs(p.valor_mercado / 1e9, 1) + " B"
            if p.valor_mercado is not None
            else "—"
        )
        return {
            "Selo": selo_txt,
            "P/L": presentation.fmt_num(p.pl),
            "P/VP": presentation.fmt_num(p.pvp),
            "ROE": presentation.fmt_pct(p.roe),
            "DY": presentation.fmt_pct(p.dy),
            "Valor de Mercado": valor_mercado,
        }
    except Exception:
        # Contexto quebrado: degrada as métricas, preservando o selo já resolvido acima.
        col = {k: "—" for k in _ORDEM_LINHAS}
        col["Selo"] = selo_txt
        return col


def montar_comparativo(
    contextos: Sequence["CompanyData"], cfg: dict
) -> ComparativoTabela:
    """Monta a tabela comparativa transposta (tickers em colunas) + flag de suficiência ≥2.

    Preserva a ordem de entrada dos contextos (sem sort, sem alvo, sem destaque). Never-raise:
    cada coluna degrada isoladamente. `.suficiente` é `len(contextos) >= 2` (regra nova que
    SUBSTITUI `pares_suficientes` — sem ticker-alvo).
    """
    dados: dict = {}
    for c in contextos:
        ticker = getattr(c, "ticker", None) or "—"
        dados[ticker] = _coluna(c, cfg)
    # dict-de-dicts já vem transposto (métricas=índice, tickers=colunas); reindexa p/ ordem fixa.
    df = pd.DataFrame(dados).reindex(_ORDEM_LINHAS)
    return ComparativoTabela(df=df, suficiente=len(contextos) >= 2)
