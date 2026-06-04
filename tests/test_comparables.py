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


def test_ranking_por_multiplos_maior_e_menor_melhor():
    # ML maior melhor; P/L menor melhor.
    empresas = ["A", "B"]
    mult = {"ML": [0.20, 0.10], "PL": [10.0, 20.0]}
    r = cmp.ranking_por_multiplos(empresas, mult)
    # A tem ML maior (100) e P/L menor (100) → nota 100; B tem 50 e 50 → 50.
    assert r[0]["empresa"] == "A"
    assert abs(r[0]["nota"] - 100.0) < 1e-6
