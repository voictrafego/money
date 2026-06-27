"""Golden unitário do estimador robusto de crescimento (Cap. 14, GROW-01).

`crescimento_log_linear` substitui o CAGR endpoint-a-endpoint do `g_historico`: estima a
TENDÊNCIA do lucro por regressão log-linear (OLS de ln(série) contra o tempo), g = exp(slope) − 1.

Fronteira de None IDÊNTICA ao CAGR (D-03): série None, len < 2, ou QUALQUER ponto None/≤ 0
(prejuízo — ln indefinido) ⇒ None. Usa TODOS os pontos da série (mata a sensibilidade a um
único ano de fundo/topo). Série passada CRUA ao estimador (winsorização é feita a montante).
"""

import pytest

from analista.core import growth


def test_pg_crescente_recupera_a_taxa():
    """PG exata +10%/ano: slope de ln é exato ⇒ g = exp(slope) − 1 = 0.10."""
    g = growth.crescimento_log_linear([100, 110, 121, 133.1])
    assert g == pytest.approx(0.10, abs=1e-6)


def test_serie_constante_da_g_zero_nao_none():
    """Série constante: slope 0 ⇒ g == 0.0 (e NÃO None)."""
    g = growth.crescimento_log_linear([500, 500, 500, 500])
    assert g == pytest.approx(0.0, abs=1e-9)


def test_pg_decrescente_recupera_taxa_negativa():
    """PG decrescente −10%/ano: g ≈ −0.10 (negativo permitido — todos os pontos > 0)."""
    g = growth.crescimento_log_linear([1000, 900, 810, 729])
    assert g == pytest.approx(-0.10, abs=1e-6)


def test_qualquer_ano_nao_positivo_retorna_none():
    """Qualquer ponto ≤ 0 (prejuízo) ⇒ None (ln indefinido) — fronteira do CAGR (D-03)."""
    assert growth.crescimento_log_linear([100, -5, 120]) is None
    assert growth.crescimento_log_linear([100, 0, 120]) is None


def test_ponto_none_retorna_none():
    """Qualquer ponto None ⇒ None (mesma fronteira de não-positivo)."""
    assert growth.crescimento_log_linear([100, None, 120]) is None


def test_len_menor_que_2_retorna_none():
    """1 ponto, série vazia ou None ⇒ None (sem 2 pontos não há tendência)."""
    assert growth.crescimento_log_linear([100]) is None
    assert growth.crescimento_log_linear([]) is None
    assert growth.crescimento_log_linear(None) is None
