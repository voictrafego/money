"""ENG-08 — a ponte auditável P/B como TESTE de correção da razão implícita (invariante).

Fixtures sintéticas, SEM nomear ticker, SEM asserir número-alvo do livro (Fase 14 é sagrada).
Cobre: (a) equivalência exata com a álgebra fechada do BLIND-02a; (b) a razão-guarda `payout_T ∈
(0,1]` e `pb_justo ∈ (0,6)` sobre insumos sãos; (c) RED-able — insumos de MODELO patológicos
(g terminal > ROE_T ⇒ payout_T negativo; spread degenerado ⇒ P/B > 6) violam a guarda, provando
que ela pega patologia de MODELO (não bug de dado).
"""

from __future__ import annotations

import pytest

from analista.core import valuation as val


def _pb_algebra(roe: float, ke: float, g: float) -> float:
    """A álgebra fechada do BLIND-02a, escrita à mão — a referência independente da implementação."""
    return 1.0 + (roe - ke) / (ke - g)


@pytest.mark.invariante
def test_pb_justo_equivale_a_algebra_fechada_do_blind02a():
    """ENG-08(a): `pb_justo` == `1 + (ROE−Ke)/(Ke−g)` EXATO (< 1e-9) — identidade preservada,
    knob-proof. Varre um grid de insumos sãos; a ponte é a MESMA álgebra do BLIND-02a."""
    for roe in (0.08, 0.12, 0.18, 0.25):
        for ke in (0.10, 0.1248, 0.15):
            for g in (0.0, 0.03, 0.0728):
                if ke - g <= 0:
                    continue
                esperado = _pb_algebra(roe, ke, g)
                obtido = val.pb_justo(roe, ke, g)
                assert obtido is not None
                assert abs(obtido - esperado) < 1e-9, (
                    f"pb_justo({roe},{ke},{g}) = {obtido} != {esperado} (álgebra fechada)"
                )


@pytest.mark.invariante
def test_payout_terminal_e_identidade_fechada():
    """ENG-08(a): `payout_terminal` == `1 − g/ROE_T` EXATO. g=0 ⇒ payout_T=1,0 (terminal zerado)."""
    assert abs(val.payout_terminal(0.18, 0.0728) - (1.0 - 0.0728 / 0.18)) < 1e-9
    assert val.payout_terminal(0.15, 0.0) == 1.0  # crescimento terminal zero: paga tudo (identidade)


# --- Guarda de borda (never-raise): None em vez de levantar ------------------------------------ #


@pytest.mark.invariante
def test_pb_justo_never_raise_em_spread_nao_positivo():
    """T-13-08: `ke − g ≤ 0` (perpetuidade não converge) ⇒ None, nunca ZeroDivision/exceção."""
    assert val.pb_justo(0.18, 0.10, 0.10) is None   # spread == 0
    assert val.pb_justo(0.18, 0.07, 0.12) is None   # spread < 0
    assert val.pb_justo(None, 0.12, 0.05) is None    # insumo None


@pytest.mark.invariante
def test_payout_terminal_never_raise_em_roe_zero():
    """T-13-08: ROE_T == 0 (ou None) ⇒ None, nunca ZeroDivision/exceção."""
    assert val.payout_terminal(0.0, 0.05) is None
    assert val.payout_terminal(None, 0.05) is None
    assert val.payout_terminal(0.18, None) is None


# --- Razão-guarda: pega patologia de MODELO (RED-able) ----------------------------------------- #


def _razao_sa(pb, payout_t) -> bool:
    """A MESMA razão-guarda do runtime (report._razao_patologica): P/B ∈ (0,6) E payout_T ∈ (0,1].
    Meio-aberto no payout (spike 13-01: terminal zerado crava payout_T=1,0 por identidade, não bug)."""
    pb_sa = pb is not None and 0.0 < pb < 6.0
    payout_sa = payout_t is not None and 0.0 < payout_t <= 1.0
    return pb_sa and payout_sa


@pytest.mark.invariante
def test_razao_sadia_sobre_insumos_saos():
    """ENG-08(b): sobre insumos sãos (ROE > Ke > g, spread confortável) a razão implícita é SÃ —
    `payout_T ∈ (0,1]` e `pb_justo ∈ (0,6)`."""
    roe_t, ke, g = 0.18, 0.1248, 0.0728   # spread ~5,2pp, ROE moderado (banco maduro sintético)
    pb = val.pb_justo(roe_t, ke, g)
    payout_t = val.payout_terminal(roe_t, g)
    assert _razao_sa(pb, payout_t), f"razão deveria ser sã: pb={pb}, payout_T={payout_t}"


@pytest.mark.invariante
def test_guarda_pega_payout_terminal_negativo():
    """ENG-08(c) RED-able: g terminal > ROE_T ⇒ payout_T < 0 (a empresa 'cresce' mais rápido do que
    reinveste, impossível em steady-state) ⇒ a razão-guarda REPROVA. Patologia de MODELO, não dado."""
    roe_t, ke, g = 0.06, 0.12, 0.10   # g (0,10) > ROE_T (0,06): payout_T = 1 − 0,10/0,06 < 0
    payout_t = val.payout_terminal(roe_t, g)
    assert payout_t is not None and payout_t < 0.0
    assert not _razao_sa(val.pb_justo(roe_t, ke, g), payout_t)


@pytest.mark.invariante
def test_guarda_pega_pb_justo_explosivo():
    """ENG-08(c) RED-able: spread `Ke − g` degenerado (quase zero) com ROE alto ⇒ P/B justo ≫ 6
    (multiplicador explosivo) ⇒ a razão-guarda REPROVA. Patologia de MODELO (spread), não bug de dado
    (o CGRA4 a 921× tem P/B implícito ~1,4 SÃO: é bug de VPA, ortogonal a esta guarda)."""
    roe_t, ke, g = 0.40, 0.10, 0.09   # spread 1pp, excesso ROE−Ke = 30pp ⇒ P/B = 1 + 0,30/0,01 = 31
    pb = val.pb_justo(roe_t, ke, g)
    assert pb is not None and pb > 6.0
    assert not _razao_sa(pb, val.payout_terminal(roe_t, g))

