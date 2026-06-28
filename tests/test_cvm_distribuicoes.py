"""BUG-JCP: o histórico de proventos do Yahoo perde o JCP (metade da distribuição dos bancos
nos anos antigos), subestimando o payout-mediana e o DDM. A DFC da CVM traz div + JCP
completos. Testa o extrator (casado por NOME, pois os códigos 6.03.NN não são padronizados) e
a preferência CVM > Yahoo em `montar_empresa`. Sem rede."""

import pandas as pd
import pytest

from analista.ingest import build, cvm, prices


def _dfc(linhas):
    """Monta um frame DFC sintético (CD_CVM=1, escala MIL) a partir de (codigo, nome, valor)."""
    return pd.DataFrame(
        [{"CD_CVM": 1, "CD_CONTA": cod, "DS_CONTA": nome, "VL_CONTA": val,
          "ESCALA_MOEDA": "MIL"} for cod, nome, val in linhas]
    ).astype({"CD_CONTA": "string"})


def test_extrai_dividendos_e_jcp_por_nome_nao_por_codigo():
    # Em TAEE o provento está em 6.03.09 e 6.03.04 é "Debêntures - Juros": casar por NOME.
    df = _dfc([
        ("6.03.04", "Pagamento de Debêntures - Juros", -648796.0),
        ("6.03.09", "Pagamento de dividendos e JCP", -1004020.0),
    ])
    v = cvm._distribuicoes_proventos(df, 1)
    assert v == pytest.approx(1004020.0 * 1000)  # só o provento, em R$ cheios (escala MIL)


def test_exclui_minoritarios_e_recebidos():
    df = _dfc([
        ("6.03.04", "Dividendos ou JCP pagos aos acionistas controladores", -12956523.0),
        ("6.03.05", "Dividendos ou JCP pagos aos acionistas não controladores", -2401800.0),
        ("6.02.11", "Dividendos e JCP recebidos", 5251011.0),  # 6.02 (operacional) — fora do 6.03
    ])
    v = cvm._distribuicoes_proventos(df, 1)
    assert v == pytest.approx(12956523.0 * 1000)  # apenas controladores


def test_soma_linhas_separadas_de_div_e_jcp():
    df = _dfc([
        ("6.03.03", "Dividendos pagos", -1000.0),
        ("6.03.04", "Juros sobre o capital próprio (dividendo) pagos", -500.0),
    ])
    # ambas contêm "dividendo" → somadas
    assert cvm._distribuicoes_proventos(df, 1) == pytest.approx(1500.0 * 1000)


def test_sem_linha_de_provento_retorna_none():
    df = _dfc([("6.03.01", "Pagamento de Empréstimos", -5500.0)])
    assert cvm._distribuicoes_proventos(df, 1) is None
    assert cvm._distribuicoes_proventos(None, 1) is None


# --------------------------------------------------------------------------- #
# Preferência CVM > Yahoo no montar_empresa
# --------------------------------------------------------------------------- #
@pytest.fixture
def stub_fontes(monkeypatch):
    estado = {"dm": None, "fund": {}}
    monkeypatch.setattr(build.prices, "coletar_mercado", lambda t: estado["dm"])
    monkeypatch.setattr(build.universe, "resolver", lambda t, nome: (999, "Bancos"))
    monkeypatch.setattr(build.cvm, "fundamentos_do_ano",
                        lambda cd, ano: estado["fund"].get(ano, {k: None for k in _CAMPOS}))
    return estado


_CAMPOS = ("lucro_liquido", "vendas_liquidas", "patrimonio_liquido", "ativo_circulante",
           "passivo_circulante", "divida_lp", "ativo_intangivel", "fco", "lpa",
           "dividendos_distribuidos")


def test_build_prefere_distribuicao_cvm_sobre_yahoo(stub_fontes):
    # Yahoo diria DPA 1.18/ação (sem JCP) → payout ~24%; a CVM tem o provento completo (div+JCP).
    dm = prices.DadosMercado(ticker="BBAS3")
    dm.preco_atual = 20.34
    dm.num_acoes = 5_708_689_674
    dm.nome = "Banco do Brasil"
    dm.dividendos_por_ano = {2024: 1.18}
    stub_fontes["dm"] = dm
    f = {k: None for k in _CAMPOS}
    f["lucro_liquido"] = 29172e6
    f["lpa"] = 4.62
    f["dividendos_distribuidos"] = 14824e6  # CVM: div + JCP completos
    stub_fontes["fund"] = {2024: f}

    c = build.montar_empresa("BBAS3", ano_base=2024, n_anos=1)
    assert c.dividendos[2024] == pytest.approx(14824e6)            # CVM, não Yahoo
    assert c.payout(2024) == pytest.approx(14824 / 29172, rel=0.01)  # ~50,8%, não ~24%


def test_build_cai_para_yahoo_quando_cvm_sem_provento(stub_fontes):
    dm = prices.DadosMercado(ticker="FOO3")
    dm.preco_atual = 10.0
    dm.num_acoes = 1_000_000_000
    dm.nome = "Foo"
    dm.dividendos_por_ano = {2024: 0.50}
    stub_fontes["dm"] = dm
    f = {k: None for k in _CAMPOS}
    f["lucro_liquido"] = 1000e6
    f["lpa"] = 1.0
    f["dividendos_distribuidos"] = None  # CVM sem a linha → fallback Yahoo
    stub_fontes["fund"] = {2024: f}

    c = build.montar_empresa("FOO3", ano_base=2024, n_anos=1)
    # Yahoo: 0.50/ação × 1bi ações = 500mi
    assert c.dividendos[2024] == pytest.approx(0.50 * 1_000_000_000)
