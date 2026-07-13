"""Golden puro por motor de valuation por arquétipo (v2.2 Fase 2; v2.3 Fase 4 — ENG-02..05).

Offline/síncrono (padrão do repo): inputs fixos de livro + tolerância absoluta. Um golden por
motor. O crítico é o RIM (ENG-02 / CAL-01): RIM híbrido com valor terminal (perpetuidade de
Gordon sobre o RI terminal). Com inputs tipo-ITUB4 devolve ~R$32,9 (live VPA~19, ke~13%) /
~R$39,2 (golden VPA~22, ke~12,5%), terminal ≈17% do valor — materialmente acima do DDM ao vivo
(~R$16), destravando o ITUB4 do "evitar". `ke_rim` (CAL-02, ke_teto revisado 0.14→0.13) é o
ajuste fino secundário; a alavanca principal é o valor terminal.
"""

import math
import os

import yaml

from analista.core import capm, motores
from analista.core import normalizacao as norm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------------------------------------------------------- #
# RIM (ENG-02 / CAL-01) — o crítico: destrava o ITUB4 com valor terminal
# --------------------------------------------------------------------------- #
def test_rim_itub4_honesto_maior_que_ddm():
    # Golden fixo tipo-ITUB4: VPA~22, ROE~19,3%, Ke estrutural~12,5%, retenção~0,53, n=10.
    # RIM híbrido com valor terminal (perpetuidade de Gordon sobre o RI terminal): fade parcial
    # a um excesso sustentável limitado + continuing value. Rende ~R$39,2 — verificado.
    res = motores.rim(
        vpa0=22.0, roe0=0.193, ke=0.125, retencao=0.53, n=10,
        excesso_sustentavel=0.045, g_terminal=0.025,
    )
    assert res is not None
    # Faixa-alvo do golden fixo (VPA=22, ke=12,5%): R$36–42.
    assert 36.0 <= res.valor_intrinseco <= 42.0
    # Agora HÁ prêmio terminal: o valor terminal descontado é positivo.
    assert res.vp_terminal > 0
    # O Residual Income terminal deixou de ser ≈0 — alimenta a perpetuidade (é POSITIVO).
    assert res.ri_por_ano[-1] > 0
    assert res.vpa_base == 22.0


def test_rim_itub4_live_alvo_32_40():
    # GATE DURO (CAL-01/CAL-02, nível UNIT): lê os knobs de config (prova parametrização, zero
    # constante mágica) e o ke via ke_rim (prova ke_teto revisado 0.14→0.13). ITUB4 live ≈ R$32,9.
    cfg = _cfg()
    ke = motores.ke_rim(1.29, cfg)
    # CAL-02: o teto revisado 0.13 é o clamp ativo (ke_live > 0.13).
    assert abs(ke - 0.13) < 1e-9
    rc = cfg["motores"]["rim"]
    res = motores.rim(
        vpa0=19.0, roe0=0.193, ke=ke, retencao=0.533, n=rc["n_fade"],
        excesso_sustentavel=rc["excesso_sustentavel"], g_terminal=rc["g_terminal"],
    )
    assert res is not None
    assert 32.0 <= res.valor_intrinseco <= 40.0
    assert res.vp_terminal > 0


def test_rim_terminal_normalizado():
    # Alavanca 2 (CAL-01/D-01): normalização through-cycle do ROE ENTRA SÓ no RI terminal.
    # Prova as duas metades da tese: (a) roe_terminal abaixo do cap MOVE o valor; (b) roe_terminal
    # acima do cap SATURA no excesso_sustentavel → bit-idêntico ao legado (protege o ITUB4).
    base = dict(
        vpa0=19.0, roe0=0.193, ke=0.13, retencao=0.533, n=10,
        excesso_sustentavel=0.045, g_terminal=0.025,
    )
    legado = motores.rim(**base)  # roe_terminal ausente → comportamento D-02/it.1
    assert legado is not None
    assert legado.vp_terminal > 0

    # (a) excesso terminal (roe_ciclo − ke = 0,02) MENOR que o cap (0,045) → o terminal encolhe,
    #     logo o valor_intrinseco DIFERE (e é menor) do legado — a alavanca move o número.
    abaixo = motores.rim(**base, roe_terminal=0.15)
    assert abaixo is not None
    assert abaixo.valor_intrinseco != legado.valor_intrinseco
    assert abaixo.valor_intrinseco < legado.valor_intrinseco
    assert abaixo.vp_terminal < legado.vp_terminal
    # A janela explícita fica INTOCADA (Pitfall 1): só o terminal muda.
    assert abs(abaixo.vp_residual_income - legado.vp_residual_income) < 1e-12

    # (b) excesso terminal (0,07) MAIOR que o cap (0,045) → min(...) satura no cap → o RI terminal
    #     é idêntico ao legado (que também satura) → valor_intrinseco bit-idêntico (não regride).
    acima = motores.rim(**base, roe_terminal=0.20)
    assert acima is not None
    assert abs(acima.valor_intrinseco - legado.valor_intrinseco) < 1e-9
    assert abs(acima.vp_terminal - legado.vp_terminal) < 1e-9


def test_rim_bad_bank_abaixo_do_book():
    # Guarda anti-bad-bank: banco que destrói valor (ROE < Ke) valua ABAIXO do book (P/B < 1).
    # fade_para = ke + min(roe0−ke, cap) SEM clampar a ≥ ke → RI terminal negativo → V < VPA.
    res = motores.rim(
        vpa0=22.0, roe0=0.10, ke=0.125, retencao=0.53, n=10,
        excesso_sustentavel=0.045, g_terminal=0.025,
    )
    assert res is not None
    assert res.valor_intrinseco < 22.0
    assert res.vp_terminal <= 0


def test_rim_roe_igual_ke_ancora_no_vpa():
    # Sem excesso de ROE em nenhum ano → valor ancorado no VPA.
    res = motores.rim(vpa0=22.0, roe0=0.125, ke=0.125, retencao=0.53, n=10)
    assert res is not None
    assert abs(res.valor_intrinseco - 22.0) < 1e-9


def test_rim_never_raise():
    assert motores.rim(vpa0=None, roe0=0.19, ke=0.125, retencao=0.53, n=10) is None
    assert motores.rim(vpa0=22.0, roe0=0.19, ke=0.0, retencao=0.53, n=10) is None
    assert motores.rim(vpa0=-5.0, roe0=0.19, ke=0.125, retencao=0.53, n=10) is None
    assert motores.rim(vpa0=22.0, roe0=0.19, ke=0.125, retencao=0.53, n=0) is None


# --------------------------------------------------------------------------- #
# ke_rim (D-01) — a alavanca do critério #1
# --------------------------------------------------------------------------- #
def test_ke_rim_menor_que_ke_live_de_banco():
    cfg = _cfg()
    kr = motores.ke_rim(1.0, cfg)
    # Ke estrutural na faixa [0,11; 0,14].
    assert 0.11 <= kr <= 0.14
    # E estritamente MENOR que o Ke do CAPM ao vivo de banco (o coração do critério #1).
    ke_live = capm.ke_local(1.0, cfg["capm"]["rf_local"], cfg["capm"]["erp_local"])
    assert kr < ke_live


def test_ke_rim_never_raise():
    assert motores.ke_rim(None, _cfg()) is None


# --------------------------------------------------------------------------- #
# Lucro normalizado (ENG-03) — usa média 7–10a, não 1 ano
# --------------------------------------------------------------------------- #
def test_lucro_normalizado_usa_media_e_ignora_pico_vale():
    # Série de LPA oscilante: picos e vales não podem mandar no intrínseco.
    serie = [2.0, 6.0, 1.0, 7.0, 1.5, 8.0, 1.2, 6.5, 1.8, 7.5]
    lpa_mid = norm.base_normalizada(serie, anos_media=10, winsor=0.10)
    # A base normalizada difere materialmente do último ano (7,5).
    assert abs(lpa_mid - serie[-1]) > 0.5
    intr = motores.lucro_normalizado(lpa_mid, ke=0.12, g_estavel=0.025)
    assert intr is not None and intr > 0 and math.isfinite(intr)
    # Gordon puro: intrínseco = lpa_mid / (ke - g).
    assert abs(intr - lpa_mid / (0.12 - 0.025)) < 1e-9


def test_lucro_normalizado_never_raise():
    assert motores.lucro_normalizado(5.0, ke=0.02, g_estavel=0.025) is None  # ke-g<=0
    assert motores.lucro_normalizado(None, ke=0.12, g_estavel=0.025) is None


# --------------------------------------------------------------------------- #
# DCF crescimento (ENG-04) — positivo e finito, modelo-H conservador
# --------------------------------------------------------------------------- #
def test_dcf_crescimento_positivo_finito_e_modelo_h_conservador():
    h = motores.dcf_crescimento(
        lpa_valuation=2.0, g_alto=0.15, g_estavel=0.025, ke=0.14, n=10
    )
    assert h is not None and h > 0 and math.isfinite(h)  # critério #3: não zero/lixo
    const = motores.dcf_crescimento(
        lpa_valuation=2.0, g_alto=0.15, g_estavel=0.025, ke=0.14, n=10, decrescente=False
    )
    # Modelo-H (decrescente) é conservador: <= cenário de crescimento constante.
    assert h < const


def test_dcf_crescimento_never_raise():
    # ke - g_estavel <= 0 → None.
    assert motores.dcf_crescimento(2.0, 0.15, 0.15, 0.10, 10) is None
    assert motores.dcf_crescimento(None, 0.15, 0.025, 0.14, 10) is None


# --------------------------------------------------------------------------- #
# NAV contábil (ENG-05) — piso patrimonial = VPA
# --------------------------------------------------------------------------- #
def test_nav_contabil_igual_vpa():
    assert motores.nav_contabil(5000.0, 1000.0) == 5.0


def test_nav_contabil_never_raise():
    assert motores.nav_contabil(None, 1000.0) is None
    assert motores.nav_contabil(5000.0, 0.0) is None
