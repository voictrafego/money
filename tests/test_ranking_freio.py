"""Freio do modo Ranking (Achado 3) + sinalização de divergência entre lentes (Achado 4).

Fecha o Achado 3 e a SINALIZAÇÃO do Achado 4 da 01-AUDIT-COERENCIA.md (Fase 3 PUXADA, indepen-
dem da Fase 2):

- **Achado 3 (freio):** o Ranking NÃO estampa alvos de regressão frágeis (R²≈0 — ITUB4/BBAS3;
  n insuficiente), degenerados (ROMI3 R$0,10, −98%) nem alvos de tickers suspensos por arquétipo
  (motor_pendente) — paridade com a suspensão D-04 do modo Analisar. A NOTA do ranque é intacta.
- **Achado 4 (SINALIZAÇÃO):** quando as duas lentes da MESMA ação (DDM absoluto × regressão
  relativa) divergem além do limiar (WEGE3 ~3×, ITUB4 ~2,2×), o Ranking AVISA em vez de apresen-
  tar as duas como "o preço-alvo". É SINALIZAÇÃO, não reconciliação: o ensemble real (DDM × motor
  do arquétipo) depende da Fase 2 e é escopo da Fase 3.
"""

import os

import numpy as np
import pytest
import yaml

from analista import cli
from analista.cli import _motor_pendente, alvo_regressao_confiavel
from analista.core import comparables as cmp
from analista.core import freio
from analista.core.comparables import PrecoAlvo, RegressaoPL
from analista.core.fundamentals import CompanyData

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _reg(r2: float, n: int) -> RegressaoPL:
    return RegressaoPL(coeficientes=np.array([10.0, 0.0, 5.0]), r2=r2, n=n)


def _pa(preco_alvo: float, preco_corrente: float, upside: float) -> PrecoAlvo:
    return PrecoAlvo(
        pl_corrente=preco_corrente, pl_esperado=10.0, lpa=1.0,
        preco_corrente=preco_corrente, preco_alvo=preco_alvo,
        upside=upside, subavaliada=preco_alvo > preco_corrente,
    )


def _empresa(ticker: str, setor: str, *, eh_concessionaria: bool = False) -> CompanyData:
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome=ticker, setor=setor, anos=anos)
    c.eh_concessionaria = eh_concessionaria
    for a in anos:
        c.lucro_liquido[a] = 1000
        c.patrimonio_liquido[a] = 4000
        c.dividendos[a] = 600
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 1800
        c.fco[a] = 1200
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = 30.0
    c.beta = 0.8
    return c


# --------------------------------------------------------------------------- #
# Task 1 — freio de fragilidade (R²/n) + suspensão por arquétipo
# --------------------------------------------------------------------------- #
def test_freio_r2_baixo_nao_estampa_alvo():
    """ITUB4/BBAS3: R²=0 → o alvo é ruído; freio suprime (não estampa como preço-alvo)."""
    reg = _reg(r2=0.0, n=4)
    pa = _pa(preco_alvo=33.44, preco_corrente=44.30, upside=-0.25)
    confiavel, motivo = alvo_regressao_confiavel(reg, pa, motor_pendente=False)
    assert confiavel is False
    assert motivo is not None


def test_freio_alvo_degenerado_romi3():
    """ROMI3 real (alvo 0,10 / −98%, r2=0,60, n=4): freado pelo mesmo freio (n insuficiente)."""
    reg = _reg(r2=0.60, n=4)
    pa = _pa(preco_alvo=0.10, preco_corrente=6.21, upside=-0.98)
    confiavel, _ = alvo_regressao_confiavel(reg, pa, motor_pendente=False)
    assert confiavel is False


def test_freio_upside_absurdo_com_regressao_sadia():
    """Isola o freio de sanidade: regressão robusta (n≥10, R² alto) MAS upside degenerado."""
    reg = _reg(r2=0.70, n=12)
    pa = _pa(preco_alvo=0.10, preco_corrente=6.21, upside=-0.98)
    confiavel, motivo = alvo_regressao_confiavel(reg, pa, motor_pendente=False)
    assert confiavel is False
    assert motivo == "alvo degenerado"


def test_freio_suspensao_por_arquetipo():
    """Ticker motor_pendente → alvo NÃO estampado como verdade (paridade D-04)."""
    reg = _reg(r2=0.70, n=12)
    pa = _pa(preco_alvo=50.0, preco_corrente=40.0, upside=0.25)
    confiavel, motivo = alvo_regressao_confiavel(reg, pa, motor_pendente=True)
    assert confiavel is False
    assert motivo == "motor pendente"


def test_freio_guard_inverso_regressao_sadia_com_motor():
    """Guard inverso: regressão robusta + arquétipo com motor → alvo segue exibido."""
    reg = _reg(r2=0.70, n=12)
    pa = _pa(preco_alvo=50.0, preco_corrente=40.0, upside=0.25)
    confiavel, motivo = alvo_regressao_confiavel(reg, pa, motor_pendente=False)
    assert confiavel is True
    assert motivo is None


def test_freio_alvo_ausente():
    """Sem PrecoAlvo (regressão não gerou alvo) → não-confiável, sem inventar motivo."""
    reg = _reg(r2=0.70, n=12)
    confiavel, motivo = alvo_regressao_confiavel(reg, None, motor_pendente=False)
    assert confiavel is False
    assert motivo is None


def test_motor_pendente_financeira_suspende():
    """Suspensão por arquétipo (key_link, D-06): financeira → motor 'rim' (!= 'ddm') → suspensa.

    Fase 2: o motor RIM está plugado, mas o selo ainda consome só o DDM — o predicado migrou
    de 'registry devolveu None' para `motor != "ddm"`, então o Ranking segue suspenso (True).
    """
    banco = _empresa("ITUB4", "Bancos")
    assert _motor_pendente(banco, _cfg()) is True


def test_motor_pendente_regulada_tem_motor():
    """Pagadora regulada → motor 'ddm' → NÃO suspensa (motor == 'ddm', paridade D-06)."""
    util = _empresa("TAEE11", "Energia Elétrica", eh_concessionaria=True)
    assert _motor_pendente(util, _cfg()) is False


# --------------------------------------------------------------------------- #
# Task 2 — sinalização de divergência entre lentes (DDM × regressão)
# --------------------------------------------------------------------------- #
def test_divergencia_wege3_sinalizada():
    """WEGE3: DDM mid ~R$11,5 vs regressão R$35 (~3×) → divergência sinalizada."""
    divergiu, razao = cmp.divergencia_entre_lentes(11.535, 34.97)
    assert divergiu is True
    assert razao == pytest.approx(3.03, abs=0.05)


def test_divergencia_itub4_sinalizada():
    """ITUB4: DDM mid ~R$15 vs regressão R$33 (~2,2×) → divergência sinalizada."""
    divergiu, razao = cmp.divergencia_entre_lentes(15.03, 33.44)
    assert divergiu is True
    assert razao == pytest.approx(2.22, abs=0.05)


def test_divergencia_estimativas_proximas_guard_inverso():
    """Estimativas próximas (< limiar) → SEM aviso (guard inverso)."""
    divergiu, razao = cmp.divergencia_entre_lentes(30.0, 33.0)
    assert divergiu is False
    assert razao == pytest.approx(1.1, abs=0.01)


def test_divergencia_no_limiar_exato():
    """No limiar exato (2×) → divergência (>=). Trava o corte."""
    divergiu, razao = cmp.divergencia_entre_lentes(10.0, 20.0)
    assert divergiu is True
    assert razao == pytest.approx(2.0)


def test_divergencia_lente_ausente_nao_inventa():
    """Dado ausente/inválido em uma lente → (False, ...): não inventa divergência."""
    assert cmp.divergencia_entre_lentes(None, 33.0) == (False, 1.0)
    assert cmp.divergencia_entre_lentes(33.0, None) == (False, 1.0)
    assert cmp.divergencia_entre_lentes(0.0, 33.0) == (False, 1.0)
    assert cmp.divergencia_entre_lentes(-5.0, 33.0) == (False, 1.0)


def test_limiar_divergencia_padrao():
    """LIMIAR_DIVERGENCIA é const de módulo (padrão 2×), coerente com a Fase 3 do roadmap."""
    assert cmp.LIMIAR_DIVERGENCIA == 2.0
    # o default do helper usa a constante de módulo (sem config.yaml novo)
    assert cmp.divergencia_entre_lentes(10.0, 25.0)[0] is True


# --------------------------------------------------------------------------- #
# quick-260712-p6r — paridade de superfície: cli.py e app.py compartilham o MESMO freio
# --------------------------------------------------------------------------- #
def test_freio_fonte_unica_cli_e_core_sao_o_mesmo_objeto():
    """O freio vive em core/freio.py; cli.py apenas re-exporta (fonte única).

    Trava a paridade por construção: se uma futura edição redefinir o freio em cli.py em vez de
    reusar core/freio.py, o `is` quebra — o mesmo freio que o CLI cmd_rank e a aba Ranking do
    Streamlit (app.py) consomem não pode divergir sem falhar aqui.
    """
    assert freio.alvo_regressao_confiavel is cli.alvo_regressao_confiavel
    assert freio.motor_pendente is cli._motor_pendente


def test_freio_aba_ranking_suprime_motor_pendente():
    """Documenta o caso que a aba Ranking do Streamlit reetiqueta: motor_pendente + reg sadia +
    pa válido → freio devolve (False, "motor pendente") em vez de deixar estampar "Cara"/"Subavaliada".
    """
    reg = _reg(r2=0.70, n=12)
    pa = _pa(preco_alvo=50.0, preco_corrente=40.0, upside=0.25)
    confiavel, motivo = freio.alvo_regressao_confiavel(reg, pa, motor_pendente=True)
    assert confiavel is False
    assert motivo == "motor pendente"
