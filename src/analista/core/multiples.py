"""Múltiplos de lucros e de dividendos — Cap. 10 do livro.

Todas as fórmulas seguem exatamente as definições de Orleans Martins & Felipe Pontes.
Funções puras: recebem números, devolvem números. `None` quando indefinido (ex.: divisão
por zero ou denominador negativo que invalida a métrica, como o livro alerta).
"""

from __future__ import annotations

import math
from typing import Optional

Number = Optional[float]


def _safe_div(num: float, den: float) -> Number:
    if den is None or num is None:
        return None
    if den == 0:
        return None
    return num / den


# --------------------------------------------------------------------------- #
# 10.1 Múltiplos de lucros
# --------------------------------------------------------------------------- #
def margem_liquida(lucro_liquido: float, vendas_liquidas: float) -> Number:
    """ML = Lucro Líquido (recorrente) / Vendas Líquidas (10.1.1)."""
    return _safe_div(lucro_liquido, vendas_liquidas)


def roe(lucro_liquido: float, patrimonio_liquido_inicial: float) -> Number:
    """ROE = Lucro Líquido (recorrente) / PL inicial (10.1.2).

    PL negativo invalida a métrica (o livro alerta para isso).
    """
    if patrimonio_liquido_inicial is None or patrimonio_liquido_inicial <= 0:
        return None
    return _safe_div(lucro_liquido, patrimonio_liquido_inicial)


def roe_medio(lucro_liquido: float, pl_inicial: float, pl_final: float) -> Number:
    """ROE com PL médio = (PL_ini + PL_fim) / 2 — variação mais robusta (10.1.2)."""
    if pl_inicial is None or pl_final is None:
        return None
    pl_medio = (pl_inicial + pl_final) / 2
    if pl_medio <= 0:
        return None
    return _safe_div(lucro_liquido, pl_medio)


def preco_lucro(preco: float, lpa: float) -> Number:
    """P/L = Preço da ação / Lucro por ação (10.1.3)."""
    return _safe_div(preco, lpa)


def peg(pl: float, g_percent: float) -> Number:
    """PEG = P/L / g (10.1.4).

    g em PONTOS PERCENTUAIS, sem o sinal de % (ex.: 5,9 para 5,9%).
    O livro recomenda excluir PEG negativo da análise comparativa.
    """
    if pl is None or g_percent is None or g_percent == 0:
        return None
    valor = pl / g_percent
    return valor


def earnings_yield(lpa: float, preco: float) -> Number:
    """EY = LPA / Preço (10.1.5). Inverso do P/L; comparável a juros."""
    return _safe_div(lpa, preco)


# --------------------------------------------------------------------------- #
# 10.2 Múltiplos de dividendos
# --------------------------------------------------------------------------- #
def dividend_payout(dpa: float, lpa: float) -> Number:
    """DP = DPA / LPA (10.2.1). >100% = distribui mais que o lucro (reservas)."""
    return _safe_div(dpa, lpa)


def cobertura_dividendos_caixa(fco: float, num_acoes: float, dpa: float) -> Number:
    """CDC = (FCO / nº ações) / DPA (10.2.2). CDC > 1 é adequado."""
    fco_por_acao = _safe_div(fco, num_acoes)
    if fco_por_acao is None:
        return None
    return _safe_div(fco_por_acao, dpa)


def dividend_yield(dpa: float, preco: float) -> Number:
    """DY = DPA / Preço (10.2.3)."""
    return _safe_div(dpa, preco)


def dividend_yield_on_cost(dpa: float, preco_medio_aquisicao: float) -> Number:
    """YOC = DPA / Preço médio de aquisição (10.2.4)."""
    return _safe_div(dpa, preco_medio_aquisicao)


def retorno_total_acionista(preco_inicial: float, preco_final: float, dpa: float) -> Number:
    """RTA = (Preço_final - Preço_inicial + DPA) / Preço_inicial (10.2.5)."""
    if preco_inicial is None or preco_inicial == 0:
        return None
    return (preco_final - preco_inicial + dpa) / preco_inicial


# --------------------------------------------------------------------------- #
# Auxiliares
# --------------------------------------------------------------------------- #
def lpa(lucro_liquido: float, num_acoes: float) -> Number:
    """Lucro por ação."""
    return _safe_div(lucro_liquido, num_acoes)


def dpa(dividendos_totais: float, num_acoes: float) -> Number:
    """Dividendo por ação."""
    return _safe_div(dividendos_totais, num_acoes)
