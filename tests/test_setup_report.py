"""Goldens do SetupSwing (SCORE-01): grades, gate de R:R, decomposição peso-a-peso,
penalização multi-TF, degradação graciosa, copy neutra (gate de aceite) e config-driven.

Stubs duck-typed no idioma de `_familias_stub` (test_indicators.py L1463) — constroem só os
rótulos que `montar_setup` lê, sem rodar `calcular()`, para não flutuar os 271 goldens existentes.
"""

import re
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from analista.core import indicators
from analista.report import setup
from tests.test_indicators import _frame_ohlc_longo


def _cfg_ind() -> dict:
    """Carrega o config.yaml shipado para pinar pesos/cortes (copiado de test_indicators)."""
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _padrao(tipo="duplo_fundo", estado="confirmado"):
    return indicators.Padroes(lista=[indicators.PadraoGrafico(
        tipo=tipo, estado=estado, neckline=100.0, alvo=120.0, altura=20.0, pivos_envolvidos={},
    )])


def _sinais_stub(
    dow="alta", forca_adx="forte", posicao_mm200="acima",
    alinhamento_mtf="alinhado_alta", entrada_zona=(95.0, 100.0), stop=90.0, alvo=120.0,
    nivel_rsi="neutro", cruzamento_macd="cruz_alta", rompimento_com_volume=True,
    volume_acima_mm=False, padroes="__forte__",
):
    """SinaisTecnicos duck-typed. Defaults produzem um setup FORTE de alta (score 100)."""
    contexto = SimpleNamespace(dow_diario=dow, alinhamento_mtf=alinhamento_mtf)
    forca = SimpleNamespace(forca_adx=forca_adx, adx=None)
    tendencia = SimpleNamespace(posicao_mm200=posicao_mm200, cruzamento="nenhum")
    niveis = SimpleNamespace(entrada_zona=entrada_zona, stop=stop, alvo=alvo,
                             risco_retorno="indisponivel")
    momentum = SimpleNamespace(nivel_rsi=nivel_rsi, cruzamento_macd=cruzamento_macd)
    volume = SimpleNamespace(rompimento_com_volume=rompimento_com_volume,
                             volume_acima_mm=volume_acima_mm)
    if padroes == "__forte__":
        padroes = _padrao()
    elif padroes is None:
        padroes = indicators.Padroes(lista=[])
    return SimpleNamespace(contexto=contexto, forca=forca, tendencia=tendencia,
                           niveis=niveis, momentum=momentum, volume=volume, padroes=padroes)


# --- Grades ---------------------------------------------------------------- #
def test_setup_forte():
    cfg = _cfg_ind()
    r = setup.montar_setup(_sinais_stub(), cfg)
    assert r.grade == "Forte"
    assert r.score >= cfg["score"]["cortes_grade"]["forte"]
    assert r.gate_rr_ok is True


def test_setup_moderado():
    # tend 35 + rr 20 + sem padrão (0) + momentum parcial (macd nenhum → rsi neutro 0.5*15=7.5)
    # + sem volume (0) = 62.5 → Moderado.
    cfg = _cfg_ind()
    r = setup.montar_setup(_sinais_stub(
        padroes=None, cruzamento_macd="nenhum", rompimento_com_volume=False,
    ), cfg)
    assert r.grade == "Moderado"
    cg = cfg["score"]["cortes_grade"]
    assert cg["moderado"] <= r.score < cg["forte"]


def test_setup_fraco():
    # tend 26.25 (forca neutro: 0.6+0.15) + rr 20 + sem padrão + momentum 0 (rsi sobrecomprado em
    # alta) + sem volume = 46.25 → Fraco.
    cfg = _cfg_ind()
    r = setup.montar_setup(_sinais_stub(
        forca_adx="neutro", padroes=None, cruzamento_macd="nenhum",
        nivel_rsi="sobrecomprado", rompimento_com_volume=False,
    ), cfg)
    assert r.grade == "Fraco"
    cg = cfg["score"]["cortes_grade"]
    assert cg["fraco"] <= r.score < cg["moderado"]


def test_setup_sem_setup_por_score_baixo():
    # Confluência mínima MAS R:R válido (rr=1.6 > 1.5): dow lateral zera tend/padrões/momentum,
    # só o sub-score de R:R pontua (~1.3) → score < fraco → "Sem setup" com gate_rr_ok True (floor).
    cfg = _cfg_ind()
    r = setup.montar_setup(_sinais_stub(
        dow="lateral", alinhamento_mtf="indisponivel", alvo=109.5,
        padroes=None, rompimento_com_volume=False,
    ), cfg)
    assert r.grade == "Sem setup"
    assert r.gate_rr_ok is True
    assert r.score < cfg["score"]["cortes_grade"]["fraco"]


# --- Gate de R:R ----------------------------------------------------------- #
def test_gate_rr_zera_setup():
    # Famílias todas excelentes MAS rr ~1.1 (< rr_minimo) → "Sem setup", gate_rr_ok False.
    cfg = _cfg_ind()
    r = setup.montar_setup(_sinais_stub(alvo=105.75), cfg)  # rr = 8.25/7.5 = 1.1
    assert r.grade == "Sem setup"
    assert r.gate_rr_ok is False
    assert r.rr_valor is not None and r.rr_valor < cfg["score"]["rr_minimo"]


def test_rr_indisponivel_sem_setup():
    # Lateral/indisponível: entrada_zona/stop None → rr None → "Sem setup" sem exceção.
    cfg = _cfg_ind()
    r = setup.montar_setup(_sinais_stub(entrada_zona=None, stop=None), cfg)
    assert r.grade == "Sem setup"
    assert r.rr_valor is None
    assert r.gate_rr_ok is False


# --- Decomposição peso-a-peso ---------------------------------------------- #
def test_decomposicao_soma_score():
    # SEM conflito: Σ contribuicao == score; cada ContribFamilia.peso bate o config (D-02).
    cfg = _cfg_ind()
    r = setup.montar_setup(_sinais_stub(), cfg)
    assert sum(c.contribuicao for c in r.decomposicao) == pytest.approx(r.score)
    pesos = cfg["score"]["pesos"]
    for c in r.decomposicao:
        assert c.peso == pesos[c.familia]
        assert c.contribuicao == pytest.approx(c.sub_score * c.peso)


# --- Penalização multi-TF -------------------------------------------------- #
def test_conflito_mtf_penaliza_sem_bloquear():
    # Mesmo stub forte com conflito → score == base*(1-penalidade), conflito_mtf True,
    # grade NÃO vira "Sem setup" só por isso (D-07).
    cfg = _cfg_ind()
    base = setup.montar_setup(_sinais_stub(), cfg).score
    r = setup.montar_setup(_sinais_stub(alinhamento_mtf="conflito"), cfg)
    pen = cfg["score"]["penalidade_conflito_mtf"]
    assert r.conflito_mtf is True
    assert r.score == pytest.approx(base * (1 - pen))
    assert r.grade != "Sem setup"


# --- Degradação graciosa --------------------------------------------------- #
def test_setup_degrada_sem_excecao():
    cfg = _cfg_ind()
    assert setup.montar_setup(None, cfg).grade == "Sem setup"
    s_sem_niveis = _sinais_stub()
    s_sem_niveis.niveis = None
    assert setup.montar_setup(s_sem_niveis, cfg).grade == "Sem setup"
    s_sem_ctx = _sinais_stub()
    s_sem_ctx.contexto = None
    assert setup.montar_setup(s_sem_ctx, cfg).grade == "Sem setup"


# --- Copy neutra (GATE DE ACEITE, D-06) ------------------------------------ #
def test_setup_sem_copy_imperativa():
    # Varre grade + decomposicao[].familia/detalhe em vários cenários contra termos imperativos.
    cfg = _cfg_ind()
    cenarios = [
        setup.montar_setup(_sinais_stub(), cfg),
        setup.montar_setup(_sinais_stub(dow="baixa", posicao_mm200="abaixo",
                                        cruzamento_macd="cruz_baixa", nivel_rsi="neutro",
                                        padroes=_padrao("duplo_topo", "confirmado")), cfg),
        setup.montar_setup(_sinais_stub(alvo=105.75), cfg),
        setup.montar_setup(_sinais_stub(volume_acima_mm=True, rompimento_com_volume=False), cfg),
        setup.montar_setup(None, cfg),
    ]
    proibidos = ("compre", "venda", "comprar", "vender", "entre", "recomend", "sugiro", "indico")
    for r in cenarios:
        textos = [r.grade] + [f"{c.familia} {c.detalhe}" for c in r.decomposicao]
        for texto in textos:
            for termo in proibidos:
                assert re.search(rf"\b{termo}", texto.lower()) is None, (
                    f"copy imperativo '{termo}' em '{texto}'"
                )


# --- Config-driven (zero hardcode) ----------------------------------------- #
def test_score_config_driven():
    # Zerar o peso de volume em memória muda o score do MESMO stub → prova zero hardcode.
    cfg = _cfg_ind()
    base = setup.montar_setup(_sinais_stub(), cfg).score
    cfg["score"]["pesos"]["volume"] = 0
    alterado = setup.montar_setup(_sinais_stub(), cfg).score
    assert alterado != base
    assert alterado == pytest.approx(base - 10)  # volume contribuía 1.0*10 no stub forte


# --- End-to-end (integração real do contrato) ------------------------------ #
def test_e2e_calcular_integra():
    cfg = _cfg_ind()
    s = indicators.calcular(_frame_ohlc_longo(), cfg)
    r = setup.montar_setup(s, cfg)
    assert isinstance(r, setup.SetupSwing)
    assert r.grade in {"Forte", "Moderado", "Fraco", "Sem setup"}
