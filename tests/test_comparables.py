"""Valida comparáveis e valuation por múltiplos contra o caso CTEEP (Cap. 12)."""

import numpy as np

from analista.core import comparables as cmp


def test_preco_alvo_cteep():
    # Cap. 12: P/L esperado ≈ 14,18; LPA 2019 = 2,6256; preço 22,16.
    # Preço-alvo ≈ 14,18 * 2,6256 ≈ R$ 37,23; upside ≈ 68%.
    # Construímos uma regressão sintética cujo P/L previsto para o perfil da CTEEP seja 14,18.
    reg = cmp.RegressaoPL(coeficientes=np.array([14.18, 0.0, 0.0]), r2=1.0, n=10)
    alvo = cmp.preco_alvo_por_regressao(reg, dp=0.5646, roe=0.142, lpa=2.6256, preco_corrente=22.16)
    assert abs(alvo.preco_alvo - 37.23) < 0.1
    assert alvo.subavaliada is True
    assert abs(alvo.upside - 0.68) < 0.02


def test_preco_alvo_clampa_payout_acima_de_1():
    # Payout 1.5 deve produzir o mesmo preço-alvo que 1.0 (clamp do Analisar) e sinalizar.
    reg = cmp.RegressaoPL(coeficientes=np.array([5.0, 3.0, 2.0]), r2=0.9, n=5)
    alto = cmp.preco_alvo_por_regressao(reg, dp=1.5, roe=0.2, lpa=2.0, preco_corrente=20.0)
    clamp = cmp.preco_alvo_por_regressao(reg, dp=1.0, roe=0.2, lpa=2.0, preco_corrente=20.0)
    assert abs(alto.preco_alvo - clamp.preco_alvo) < 1e-9
    assert alto.payout_fora_faixa is True
    assert clamp.payout_fora_faixa is False


def test_preco_alvo_clampa_payout_negativo():
    # Payout negativo (LPA<0) deve ser clampado para 0.0 sem exceção e sinalizado.
    reg = cmp.RegressaoPL(coeficientes=np.array([5.0, 3.0, 2.0]), r2=0.9, n=5)
    neg = cmp.preco_alvo_por_regressao(reg, dp=-0.3, roe=0.2, lpa=2.0, preco_corrente=20.0)
    piso = cmp.preco_alvo_por_regressao(reg, dp=0.0, roe=0.2, lpa=2.0, preco_corrente=20.0)
    assert abs(neg.preco_alvo - piso.preco_alvo) < 1e-9
    assert neg.payout_fora_faixa is True


def test_preco_alvo_payout_dentro_da_faixa_nao_sinaliza():
    reg = cmp.RegressaoPL(coeficientes=np.array([5.0, 3.0, 2.0]), r2=0.9, n=5)
    ok = cmp.preco_alvo_por_regressao(reg, dp=0.6, roe=0.2, lpa=2.0, preco_corrente=20.0)
    assert ok.payout_fora_faixa is False


def test_regressao_recupera_coeficientes():
    # P/L = 5 + 10*DP + 20*ROE exatamente.
    dp = [0.3, 0.5, 0.7, 0.4, 0.6, 0.8]
    roe = [0.10, 0.15, 0.20, 0.12, 0.18, 0.22]
    pl = [5 + 10 * d + 20 * r for d, r in zip(dp, roe)]
    reg = cmp.ajustar_regressao_pl(pl, dp, roe)
    assert reg is not None
    assert abs(reg.prever(0.5, 0.15) - (5 + 10 * 0.5 + 20 * 0.15)) < 1e-6
    assert reg.r2 > 0.999


def test_regressao_amostra_insuficiente():
    assert cmp.ajustar_regressao_pl([10, 12], [0.3, 0.5], [0.1, 0.15]) is None


def test_regressao_amostra_pequena():
    # n < LIMIAR_AMOSTRA (10) sinaliza amostra pequena; n >= 10 não.
    pequena = cmp.RegressaoPL(coeficientes=np.array([5.0, 3.0, 2.0]), r2=0.9, n=6)
    suficiente = cmp.RegressaoPL(coeficientes=np.array([5.0, 3.0, 2.0]), r2=0.9, n=10)
    assert pequena.amostra_pequena is True
    assert suficiente.amostra_pequena is False


def test_regressao_roe_sinal_invertido():
    # b_ROE (coeficientes[2]) < 0 contraria Gordon → invertido; >=0 não.
    invertido = cmp.RegressaoPL(coeficientes=np.array([5.0, 10.0, -66.72]), r2=0.9, n=6)
    normal = cmp.RegressaoPL(coeficientes=np.array([5.0, 10.0, 20.0]), r2=0.9, n=6)
    zero = cmp.RegressaoPL(coeficientes=np.array([5.0, 10.0, 0.0]), r2=0.9, n=6)
    assert invertido.roe_sinal_invertido is True
    assert normal.roe_sinal_invertido is False
    assert zero.roe_sinal_invertido is False


def test_ranking_por_multiplos_maior_e_menor_melhor():
    # ML maior melhor; P/L menor melhor.
    empresas = ["A", "B"]
    mult = {"ML": [0.20, 0.10], "PL": [10.0, 20.0]}
    r = cmp.ranking_por_multiplos(empresas, mult)
    # A tem ML maior (100) e P/L menor (100) → nota 100; B tem 50 e 50 → 50.
    assert r[0]["empresa"] == "A"
    assert abs(r[0]["nota"] - 100.0) < 1e-6
