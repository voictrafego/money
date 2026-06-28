"""BUG-UNIT: tickers de UNIT (XXXX11) têm preço/proventos POR UNIT, mas o LPA da CVM é
POR AÇÃO. `montar_empresa` deve converter num_acoes para a base de UNITS, alinhando
LPA/P/L/payout/DDM ao preço. Não-units ficam intactos. Nenhum teste toca a rede."""

import pytest

from analista.ingest import build, prices


def _mercado(ticker, preco, sharesout, divs_por_ano):
    dm = prices.DadosMercado(ticker=ticker)
    dm.preco_atual = preco
    dm.num_acoes = sharesout           # Yahoo sharesOutstanding (= nº de UNITS p/ unit)
    dm.nome = ticker
    dm.dividendos_por_ano = divs_por_ano  # DPA POR UNIT por ano (Yahoo)
    return dm


@pytest.fixture
def stub_fontes(monkeypatch):
    """Permite injetar mercado (Yahoo) e fundamentos (CVM) por ticker, sem rede."""
    estado = {"dm": None, "fund": {}}

    monkeypatch.setattr(build.prices, "coletar_mercado", lambda t: estado["dm"])
    monkeypatch.setattr(build.universe, "resolver", lambda t, nome: (999, "Setor X"))
    monkeypatch.setattr(build.cvm, "fundamentos_do_ano",
                        lambda cd, ano: estado["fund"].get(ano, _vazio()))
    return estado


def _vazio():
    return {k: None for k in (
        "lucro_liquido", "vendas_liquidas", "patrimonio_liquido", "ativo_circulante",
        "passivo_circulante", "divida_lp", "ativo_intangivel", "fco", "lpa")}


def _ano(lucro_mi, lpa_cvm, pl_mi=None):
    f = _vazio()
    f["lucro_liquido"] = lucro_mi * 1e6
    f["lpa"] = lpa_cvm            # CVM "Lucro por Ação" — POR AÇÃO (ON+PN)
    if pl_mi is not None:
        f["patrimonio_liquido"] = pl_mi * 1e6
    return f


def test_unit_taee_converte_para_base_de_unit(stub_fontes):
    # TAEE11: 3 ações por unit. CVM: LL R$1.580mi, LPA R$1,5287/ação → 1.034bi ações.
    # Yahoo: 344,5mi UNITS, preço R$39,72/unit, dividendo R$3,2293/unit.
    stub_fontes["dm"] = _mercado("TAEE11", 39.72, 344_498_907, {2025: 3.2293})
    stub_fontes["fund"] = {2025: _ano(1580, 1.52866)}

    c = build.montar_empresa("TAEE11", ano_base=2025, n_anos=1)

    # num_acoes deve ficar na base de UNITS (~344,5mi), não no total de ações (~1.034bi)
    assert c.num_acoes[2025] == pytest.approx(344.5e6, rel=0.02)
    # LPA por unit ~R$4,59 → P/L ~8,6 (e NÃO ~26, o valor inflado pelo bug)
    assert c.lpa(2025) == pytest.approx(4.59, rel=0.03)
    pl = 39.72 / c.lpa(2025)
    assert pl == pytest.approx(8.65, rel=0.03)
    # dividendos totais = R$3,2293/unit * 344,5mi units ≈ R$1,11bi → payout ~70% (não 211%)
    assert c.payout(2025) == pytest.approx(0.70, rel=0.05)


def test_unit_klbn_fator_derivado_da_razao(stub_fontes):
    # KLBN11: LL R$1.678mi, LPA R$0,2286/ação → ~7,34bi ações; Yahoo ~1,215bi UNITS.
    # razão 7,34/1,215 ≈ 6 → num_acoes ≈ 1,22bi (a contagem de units), P/L ~12 (não 60).
    stub_fontes["dm"] = _mercado("KLBN11", 16.96, 1_214_936_096, {2025: 1.6801})
    stub_fontes["fund"] = {2025: _ano(1678, 0.2286)}

    c = build.montar_empresa("KLBN11", ano_base=2025, n_anos=1)

    assert c.num_acoes[2025] == pytest.approx(1.22e9, rel=0.05)
    pl = 16.96 / c.lpa(2025)
    assert pl == pytest.approx(12.4, rel=0.05)


def test_nao_unit_fica_intacto(stub_fontes):
    # BBAS3 (ação ON, não-unit): num_acoes = contagem CVM crua, sem qualquer conversão.
    stub_fontes["dm"] = _mercado("BBAS3", 20.34, 5_708_689_674, {2025: 1.18})
    stub_fontes["fund"] = {2025: _ano(29172, 4.62)}  # 2024 numbers as a clean example

    c = build.montar_empresa("BBAS3", ano_base=2025, n_anos=1)

    esperado = 29172e6 / 4.62
    assert c.num_acoes[2025] == pytest.approx(esperado, rel=1e-6)  # idêntico ao comportamento antigo


def test_unit_sem_lpa_cvm_usa_units_do_yahoo(stub_fontes):
    # Sem LPA na CVM: cai no fallback Yahoo (sharesOutstanding), que já é base de UNIT.
    stub_fontes["dm"] = _mercado("TAEE11", 39.72, 344_498_907, {2025: 3.2293})
    stub_fontes["fund"] = {2025: _ano(1580, None)}  # lpa ausente

    c = build.montar_empresa("TAEE11", ano_base=2025, n_anos=1)
    assert c.num_acoes[2025] == pytest.approx(344.5e6, rel=0.01)
