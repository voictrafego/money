"""Golden puro por motor de valuation por arquétipo (v2.2, Fase 2 — ENG-02..05).

Offline/síncrono (padrão do repo): inputs fixos de livro + tolerância absoluta. Um golden por
motor. O crítico é o RIM (ENG-02): com inputs tipo-ITUB4 devolve ~R$28 (modelo honesto/
conservador, faixa R$26–34, SEM prêmio terminal — D-02) e materialmente acima do DDM ao vivo
(~R$16), destravando o ITUB4 do "evitar". `ke_rim` (D-01) é a alavanca: Ke estrutural MENOR que
o CAPM ao vivo de banco.
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
# RIM (ENG-02) — o crítico: destrava o ITUB4
# --------------------------------------------------------------------------- #
def test_rim_itub4_honesto_maior_que_ddm():
    # Inputs tipo-ITUB4: VPA~22, ROE~19,3%, Ke estrutural~12,5%, retenção~0,53, n=10.
    # A fórmula especificada (fade linear do excesso a zero, clean surplus, SEM prêmio
    # terminal) rende ~R$28,20 — verificado aritmeticamente.
    res = motores.rim(vpa0=22.0, roe0=0.193, ke=0.125, retencao=0.53, n=10)
    assert res is not None
    # Faixa honesta do modelo conservador (teto R$34 = caso no-fade).
    assert 26.0 <= res.valor_intrinseco <= 34.0
    # Materialmente > DDM ao vivo (~R$16). NÃO 2×16: o modelo honesto não chega a R$32 sem
    # prêmio terminal (o que violaria D-02).
    assert res.valor_intrinseco >= 25.0
    # Fade completo: o Residual Income do último ano ≈ 0 (valor ancorado no VPA, D-02).
    assert abs(res.ri_por_ano[-1]) < 0.05
    assert res.vpa_base == 22.0


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
