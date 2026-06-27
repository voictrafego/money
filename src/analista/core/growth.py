"""Taxa de crescimento (g) — Cap. 14 do livro.

O livro apresenta várias formas de estimar g. As mais usadas no MVP:
- histórico (CAGR geométrico, e aritmético como alternativa);
- por fundamentos (crescimento sustentável): g = ROE * (1 - payout);
- estável (perpetuidade): g <= crescimento esperado do PIB.
"""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np

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


def crescimento_log_linear(serie: Sequence[float]) -> Number:
    """Tendência de crescimento por regressão log-linear (Cap. 14).

    Estimador robusto que SUBSTITUI o CAGR endpoint-a-endpoint do `g_historico`: em vez de
    olhar só o primeiro e o último ponto (sensível a um único ano de fundo/topo), ajusta a
    TENDÊNCIA usando TODOS os pontos da série. OLS de ln(série) contra o tempo
    (x = 0..n-1, passo de 1 ano); o coeficiente angular (slope) é o crescimento log médio
    anual e g anualizado = exp(slope) − 1 (anualizado por construção, passo de x = 1 ano).

    Explicabilidade ("tendência de crescimento") e simplicidade (numpy.polyfit) são o motivo
    da escolha (D-01); Theil-Sen e média aparada de YoY foram rejeitados como over-engineering
    para ≤8-10 pontos já winsorizados (D-02). Esta é a fonte única reusada também pelo
    screening — consistência Analisar↔Screening por construção (D-04).

    Fronteira de None IDÊNTICA ao CAGR (D-03): série None, len < 2, ou QUALQUER ponto
    None/≤ 0 (prejuízo, onde ln é indefinido) ⇒ None. Não há fallback aritmético (mudaria a
    fronteira de None). A série é recebida CRUA — a winsorização é feita a montante.
    """
    if serie is None or len(serie) < 2:
        return None
    if any(v is None or v <= 0 for v in serie):
        return None
    x = np.arange(len(serie))
    slope = np.polyfit(x, np.log(serie), 1)[0]
    return float(np.exp(slope) - 1.0)


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
