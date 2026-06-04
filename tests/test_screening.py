"""Valida o screening (Cap. 8): filtros customizados, Graham e ranking BSD."""

from analista.core import screening as sc
from analista.core.fundamentals import CompanyData


def _empresa_solida(ticker="TAEE11"):
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Empresa Sólida", setor="Energia Elétrica", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = 1000 + (a - 2015) * 50
        c.patrimonio_liquido[a] = 4000 + (a - 2015) * 100
        c.dividendos[a] = 600 + (a - 2015) * 30
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 1800
        c.fco[a] = 1200
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = 30.0
    c.volume_financeiro_diario = 40_000_000
    c.desempenho_relativo_6m = 0.10
    c.beta = 0.8
    return c


def test_filtros_customizados_aprova_solida():
    c = _empresa_solida()
    # DPA atual = 870/1000 = 0,87; DY = 0,87/30 = 2,9%. Selic 1% → passa.
    res = sc.filtros_customizados(c, selic=0.01, n_anos=10)
    assert res.passou is True
    assert all(res.criterios.values())


def test_filtros_customizados_reprova_pl_negativo():
    c = _empresa_solida()
    c.patrimonio_liquido[2018] = -100  # um ano com PL negativo exclui
    res = sc.filtros_customizados(c, selic=0.01)
    assert res.passou is False
    assert res.criterios["pl_positivo"] is False


def test_filtros_customizados_dy_abaixo_da_selic():
    c = _empresa_solida()
    res = sc.filtros_customizados(c, selic=0.10)  # DY 2,9% < Selic 10%
    assert res.criterios["dy_acima_corte"] is False
    assert res.passou is False


def test_graham_flexivel_aprova():
    c = _empresa_solida()
    res = sc.filtros_graham(
        c, faturamento_usd=300_000_000, pl_atual=12.0, pvpa_atual=2.0, variante="flexivel_br"
    )
    assert res.passou is True


def test_graham_original_reprova_pvpa_alto():
    c = _empresa_solida()
    res = sc.filtros_graham(
        c, faturamento_usd=300_000_000, pl_atual=12.0, pvpa_atual=2.5, variante="original"
    )
    # P/VPA 2,5 > 1,5 reprova na versão original.
    assert res.criterios["pvpa"] is False
    assert res.passou is False


def test_bsd_ranking_ordena_e_marca_acima_80():
    boa = _empresa_solida("BOA3")
    # empresa fraca: payout baixo, sem crescimento, DY baixo
    fraca = _empresa_solida("FRACA3")
    for a in fraca.anos:
        fraca.dividendos[a] = 50          # payout baixo
        fraca.lucro_liquido[a] = 1000      # sem crescimento
        fraca.fco[a] = 200
    fraca.desempenho_relativo_6m = -0.20
    ranking = sc.bsd_ranking([boa, fraca])
    assert ranking[0]["ticker"] == "BOA3"
    assert ranking[0]["bsd"] == 100.0      # melhor empresa recebe 100 após padronização
    assert ranking[-1]["bsd"] == 0.0
