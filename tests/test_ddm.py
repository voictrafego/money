"""Valida o DDM e o CAPM contra o caso Itaú do livro (Cap. 16 e 17)."""

import pytest

from analista.core import capm
from analista.core import ddm
from analista.core import growth


def test_ke_itau_capm():
    # Cap. 16: Ke do Itaú = 12,48%.
    p = capm.CapmParams(
        rf_us=0.0192, embi_brasil=0.0214, erp_us=0.0620,
        inflacao_br=0.0440, inflacao_us=0.0252,
    )
    ke = capm.ke_eua_ajustada(beta_acao=1.24, params=p)
    assert abs(ke - 0.1248) < 0.0005


def test_beta_calculo():
    # Beta de uma série perfeitamente alavancada 1,5x deve dar 1,5.
    mkt = [0.01, -0.02, 0.03, -0.01, 0.02]
    acao = [1.5 * x for x in mkt]
    b = capm.beta(acao, mkt)
    assert abs(b - 1.5) < 1e-9


def test_gordon():
    # V = DPA_1 / (Ke - g)
    v = ddm.valor_gordon(dpa1=2.0, ke=0.1248, g=0.025)
    assert abs(v - 2.0 / (0.1248 - 0.025)) < 1e-9


def test_ddm_itau_crescimento_constante():
    # Cap. 17, Tabela 41 (cenário de alto crescimento constante):
    # DPA_2020 = 2,362; g = 10,24%; n = 10; g_estável = 2,5%; Ke = 12,48%.
    # Esperado: VP dividendos ≈ 19,23, VP residual ≈ 17,99, valor intrínseco ≈ 37,22.
    res = ddm.ddm_dois_estagios(
        dpa_inicial=2.362, g_alto=0.1024, n=10, g_estavel=0.025, ke=0.1248,
    )
    assert res is not None
    # DPA do último ano (2029) ≈ R$ 5,68
    assert abs(res.dividendos_projetados[-1] - 5.68) < 0.05
    assert abs(res.vp_dividendos - 19.23) < 0.15
    assert abs(res.vp_residual - 17.99) < 0.15
    assert abs(res.valor_intrinseco - 37.22) < 0.20
    # Cerca de 48,3% do valor vem do residual.
    assert abs(res.peso_residual - 0.483) < 0.02


def test_ddm_modelo_h_conservador_menor():
    # O cenário decrescente (modelo H) deve dar valor MENOR que o constante.
    constante = ddm.ddm_dois_estagios(2.362, 0.1024, 10, 0.025, 0.1248, decrescente=False)
    decrescente = ddm.ddm_dois_estagios(2.362, 0.1024, 10, 0.025, 0.1248, decrescente=True)
    assert decrescente.valor_intrinseco < constante.valor_intrinseco


def test_ddm_ke_menor_que_g_invalido():
    assert ddm.ddm_dois_estagios(2.0, 0.10, 10, 0.15, 0.12) is None


def test_g_por_fundamentos():
    # g = ROE * (1 - payout). Itaú 2009-2015: ROE 20,4%, payout 31,5% → g ≈ 13,97%.
    g = growth.crescimento_por_fundamentos(roe=0.204, payout=0.315)
    assert abs(g - 0.1397) < 0.001


def test_cagr():
    # CAGR de 100 a 200 em 10 anos.
    g = growth.cagr(100, 200, 10)
    assert abs(g - (2 ** 0.1 - 1)) < 1e-9
