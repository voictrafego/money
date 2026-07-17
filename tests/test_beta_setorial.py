"""KE-03 (Fase 12 / plano 12-01) — infra do beta setorial+Blume, PURAMENTE ADITIVA.

Cobre o gerador offline do mapa `setor -> mediana(beta cru)` (D-01/D-02/D-05), a
normalizacao de setor (holding vs operadora, D-01), o carregamento do artefato versionado
e — no bloco Blume/carimbo — o helper `capm.beta_blume` (D-03/D-04) e o stamp de fonte unica.
NADA aqui consome `beta_blume` para mudar `a.ke` (isso e' o Plano 02): a suite fica identica
em NIVEL. Betas sinteticos; nenhum nivel de reais asserido — BLIND-04a-safe.
"""

import statistics
from types import SimpleNamespace

import pytest

from analista.core import capm
from analista.ingest import macro


def _emp(setor, beta):
    """Objeto minimo com os dois campos que o gerador le: `.setor` e `.beta`."""
    return SimpleNamespace(setor=setor, beta=beta)


# ---------------------------------------------------------------------------
# Gerador do mapa (D-01/D-02): mediana do beta CRU por setor normalizado, n>=limiar
# ---------------------------------------------------------------------------

def test_mapa_vazio_never_raise():
    assert macro.mapa_beta_setorial([], limiar=3) == {}


def test_setor_com_3_betas_usa_a_mediana_do_beta_cru():
    empresas = [_emp("Bancos", 1.0), _emp("Bancos", 1.2), _emp("Bancos", 1.4)]
    mapa = macro.mapa_beta_setorial(empresas, limiar=3)
    assert "Bancos" in mapa
    # mediana do beta CRU (nao Blume: 0,33+0,67*1,2 = 1,134 != 1,2)
    assert mapa["Bancos"] == pytest.approx(statistics.median([1.0, 1.2, 1.4]))


def test_setor_abaixo_do_limiar_fica_ausente():
    empresas = [_emp("Nicho", 0.8), _emp("Nicho", 0.9)]  # so 2 betas
    assert "Nicho" not in macro.mapa_beta_setorial(empresas, limiar=3)


def test_beta_none_nao_conta_para_o_limiar_nem_para_a_mediana():
    # 3 tickers no setor, mas so 2 betas disponiveis -> abaixo do limiar
    empresas = [_emp("Setor", 0.5), _emp("Setor", 0.7), _emp("Setor", None)]
    assert "Setor" not in macro.mapa_beta_setorial(empresas, limiar=3)
    # com um 4o ticker (3 betas nao-None) a mediana ignora o None
    mapa = macro.mapa_beta_setorial(empresas + [_emp("Setor", 0.9)], limiar=3)
    assert mapa["Setor"] == pytest.approx(statistics.median([0.5, 0.7, 0.9]))


def test_normalizar_setor_agrupa_holding_e_operadora():
    assert macro._normalizar_setor(
        "Emp. Adm. Part. - Energia Elétrica"
    ) == macro._normalizar_setor("Energia Elétrica")


def test_normalizar_setor_none_never_raise():
    assert macro._normalizar_setor(None) == ""


def test_holding_e_operadora_agrupam_no_mesmo_setor():
    empresas = [
        _emp("Energia Elétrica", 0.60),
        _emp("Energia Elétrica", 0.62),
        _emp("Emp. Adm. Part. - Energia Elétrica", 0.64),
    ]
    mapa = macro.mapa_beta_setorial(empresas, limiar=3)
    assert "Energia Elétrica" in mapa
    assert mapa["Energia Elétrica"] == pytest.approx(statistics.median([0.60, 0.62, 0.64]))


# ---------------------------------------------------------------------------
# Artefato versionado (D-05): carregar + degradacao graciosa + derivacao
# ---------------------------------------------------------------------------

def test_carregar_beta_setorial_devolve_dict_de_floats():
    mapa = macro.carregar_beta_setorial()
    assert isinstance(mapa, dict)
    assert mapa, "o artefato data/beta_setorial.yaml nao pode estar vazio"
    assert all(isinstance(v, float) for v in mapa.values())


def test_carregar_beta_setorial_arquivo_ausente_degrada_para_vazio():
    assert macro.carregar_beta_setorial("/caminho/que/nao/existe/beta_setorial.yaml") == {}


def test_artefato_e_derivado_do_snapshot_e_respeita_o_limiar():
    """'derivado, nao digitado': o artefato == recomputacao do mapa sobre o universo real.

    Como `mapa_beta_setorial` so' emite setores com n_betas>=limiar, a igualdade prova de
    quebra que nenhum setor com <3 betas aparece no artefato.
    """
    import helpers_sanidade as hs

    empresas = list(hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO).values())
    esperado = macro.mapa_beta_setorial(empresas, limiar=3)
    artefato = macro.carregar_beta_setorial()
    assert artefato == pytest.approx(esperado)


# ---------------------------------------------------------------------------
# capm.beta_blume (D-03/D-04): Blume 0,33+0,67*base UMA vez; setorial > individual; never-raise
# ---------------------------------------------------------------------------

def test_beta_blume_usa_o_setorial_quando_disponivel():
    mapa = {"Energia Elétrica": 0.615}
    assert capm.beta_blume(0.615, "Energia Elétrica", mapa) == pytest.approx(0.33 + 0.67 * 0.615)


def test_beta_blume_setorial_ignora_o_individual():
    """O proposito do KE-03: a base e' a MEDIANA do setor, nao o beta cru do ticker."""
    mapa = {"Bancos": 1.216}
    # beta cru individual 1.7, mas a base Blume vem do setor (1.216), nao de 1.7
    assert capm.beta_blume(1.7, "Bancos", mapa) == pytest.approx(0.33 + 0.67 * 1.216)


def test_beta_blume_cai_no_individual_quando_setor_ausente_do_mapa():
    assert capm.beta_blume(0.88, "Calçados", {}) == pytest.approx(0.33 + 0.67 * 0.88)


def test_beta_blume_setor_none_cai_no_individual():
    mapa = {"Bancos": 1.216}
    assert capm.beta_blume(0.88, None, mapa) == pytest.approx(0.33 + 0.67 * 0.88)


def test_beta_blume_beta_none_devolve_none():
    # Contrato "beta None -> None" da engine (mesmo do ke_rim): sem dado de mercado, sem Ke.
    assert capm.beta_blume(None, "Bancos", {"Bancos": 1.216}) is None


def test_beta_blume_holding_casa_o_setor_normalizado():
    mapa = {"Energia Elétrica": 0.62}
    assert capm.beta_blume(
        1.0, "Emp. Adm. Part. - Energia Elétrica", mapa
    ) == pytest.approx(0.33 + 0.67 * 0.62)


# ---------------------------------------------------------------------------
# Carimbo de fonte unica (D-06): carimbar_beta_setorial grava a chave em cfg["capm"]
# ---------------------------------------------------------------------------

def test_carimbar_beta_setorial_grava_o_mapa_carregado():
    cfg = {"capm": {}}
    macro.carimbar_beta_setorial(cfg)
    assert cfg["capm"]["beta_setorial"] == macro.carregar_beta_setorial()


def test_carimbar_beta_setorial_cria_o_bloco_capm_ausente():
    cfg = {}
    macro.carimbar_beta_setorial(cfg)
    assert "beta_setorial" in cfg["capm"]
