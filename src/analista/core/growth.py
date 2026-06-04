"""Taxa de crescimento (g) — Cap. 14 do livro.

O livro apresenta várias formas de estimar g. As mais usadas no MVP:
- histórico (CAGR geométrico, e aritmético como alternativa);
- por fundamentos (crescimento sustentável): g = ROE * (1 - payout);
- estável (perpetuidade): g <= crescimento esperado do PIB.
"""

from __future__ import annotations

from typing import Optional, Sequence

Number = Optional[float]


def cagr(valor_inicial: float, valor_final: float, n_periodos: int) -> Number:
    """Crescimento geométrico (CAGR) = (V_n / V_0)^(1/n) - 1.

    Exige base e ponta positivas (não faz sentido com valores <= 0).
    """
    if (
        valor_inicial is None
        or valor_final is None
        or n_periodos <= 0
        or valor_inicial <= 0
        or valor_final <= 0
    ):
        return None
    return (valor_final / valor_inicial) ** (1.0 / n_periodos) - 1.0


def crescimento_aritmetico(serie: Sequence[float]) -> Number:
    """Média aritmética das variações período a período.

    g = média( (V_t - V_{t-1}) / V_{t-1} ).
    """
    if serie is None or len(serie) < 2:
        return None
    variacoes = []
    for anterior, atual in zip(serie[:-1], serie[1:]):
        if anterior in (None, 0) or atual is None:
            continue
        variacoes.append((atual - anterior) / anterior)
    if not variacoes:
        return None
    return sum(variacoes) / len(variacoes)


def crescimento_por_fundamentos(roe: float, payout: float) -> Number:
    """Crescimento sustentável (por fundamentos): g = ROE * (1 - payout).

    (1 - payout) é a taxa de reinvestimento (retenção). Cap. 14.3.
    """
    if roe is None or payout is None:
        return None
    return roe * (1.0 - payout)


def crescimento_estavel(g_calculado: float, teto_pib: float) -> float:
    """Crescimento na perpetuidade limitado ao crescimento esperado do PIB (14.4).

    O livro frisa: crescer mais que o PIB indefinidamente é economicamente insensato.
    """
    if g_calculado is None:
        return teto_pib
    return min(g_calculado, teto_pib)
