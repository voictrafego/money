"""Valida as fórmulas de múltiplos contra os exemplos numéricos do livro (Cap. 10)."""

import math

import pytest

from analista.core import multiples as m


def aprox(a, b, tol=0.01):
    return a is not None and abs(a - b) <= tol


def test_margem_liquida_cielo():
    # Cielo 2019: ML = 15,8%
    assert aprox(m.margem_liquida(0.158, 1.0), 0.158)


def test_roe_petrobras():
    # Petrobras 2019: ROE = 14,4%
    assert aprox(m.roe(0.144, 1.0), 0.144)


def test_roe_pl_negativo_invalido():
    assert m.roe(100, -50) is None


def test_preco_lucro_hypera():
    # Hypera 2019: P/L = 17,3 (preço 31,94 / LPA 1,84 ~ 17,36)
    assert aprox(m.preco_lucro(31.94, 1.84), 17.36, tol=0.05)


def test_earnings_yield_hypera():
    # EY = 1,84 / 31,94 = 5,76%
    assert aprox(m.earnings_yield(1.84, 31.94), 0.0576, tol=0.0005)


def test_dividend_payout_odontoprev():
    # Odontoprev 2019: DPA 0,36 / LPA 0,54 = 66,7%
    assert aprox(m.dividend_payout(0.36, 0.54), 0.667, tol=0.005)


def test_cobertura_dividendos_engie():
    # Engie 2019: FCO 4,768bi / 815,9mi ações = 5,84/ação; DPA 1,62 → CDC 3,6
    cdc = m.cobertura_dividendos_caixa(4_768_000_000, 815_900_000, 1.62)
    assert aprox(cdc, 3.6, tol=0.05)


def test_dividend_yield_mrv():
    # MRV 2019: DPA 1,11 / preço 21,55 = 5,15%
    assert aprox(m.dividend_yield(1.11, 21.55), 0.0515, tol=0.0005)


def test_yoc_mrv():
    # YOC = 1,11 / 9,74 = 11,40%
    assert aprox(m.dividend_yield_on_cost(1.11, 9.74), 0.1140, tol=0.0005)


def test_rta_mrv():
    # RTA = (21,55 - 11,61 + 1,11) / 11,61 = 95,18%
    assert aprox(m.retorno_total_acionista(11.61, 21.55, 1.11), 0.9518, tol=0.0005)


def test_peg_exclui_negativo_via_uso():
    # PEG = P/L / g(em %). Hypera: 19,4 / 5,9 ~ 3,29
    assert aprox(m.peg(19.4, 5.9), 3.288, tol=0.01)
