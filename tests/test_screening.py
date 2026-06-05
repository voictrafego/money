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


def _brutos_na_fracao(frac):
    """Indicadores BSD brutos posicionados na fração `frac` de cada banda de REFERENCIA_BSD."""
    return {
        nome: lo + frac * (hi - lo) for nome, (lo, hi) in sc.REFERENCIA_BSD.items()
    }


def test_bsd_ranking_ordena_e_marca_acima_80(monkeypatch):
    # Perfis sintéticos posicionados nas bandas absolutas (não dependem do lote).
    forte = _empresa_solida("FORTE3")   # frac 0.9 → terço superior
    fraca = _empresa_solida("FRACA3")   # frac 0.1 → terço inferior
    brutos = {"FORTE3": _brutos_na_fracao(0.90), "FRACA3": _brutos_na_fracao(0.10)}

    def fake_indicadores(c, anos_media=3):
        return brutos[c.ticker]

    monkeypatch.setattr(sc, "indicadores_bsd", fake_indicadores)

    ranking = sc.bsd_ranking([fraca, forte])
    # ordenação: forte antes da fraca
    assert ranking[0]["ticker"] == "FORTE3"
    assert ranking[-1]["ticker"] == "FRACA3"
    # corte 80 ABSOLUTO: forte passa, fraca não
    assert ranking[0]["bsd"] > 80 and ranking[0]["acima_de_80"] is True
    assert ranking[-1]["bsd"] < 80 and ranking[-1]["acima_de_80"] is False
    # chaves de faltantes presentes (nenhum faltante neste perfil completo)
    for r in ranking:
        assert "fatores_faltantes" in r and "n_fatores_faltantes" in r
        assert r["n_fatores_faltantes"] == 0


def test_bsd_corte_80_absoluto_via_padronizar():
    # Smoke direto sobre _padronizar_absoluto: terço superior pontua acima do inferior.
    lo, hi = sc.REFERENCIA_BSD["payout"]
    sup = lo + (2 / 3) * (hi - lo)
    inf = lo + (1 / 3) * (hi - lo)
    notas = sc._padronizar_absoluto([sup, inf, None], lo, hi)
    assert notas[0] > notas[1]               # terço superior > terço inferior
    assert notas[2] == 50.0                  # ausente é neutro, não 0
    # clamp: acima de hi não passa de 100, abaixo de lo não fica negativo
    assert sc._padronizar_absoluto([hi * 2, lo - hi], lo, hi) == [100.0, 0.0]


def test_bsd_reprodutivel_entre_lotes():
    boa = _empresa_solida("BOA3")
    bsd_sozinha = sc.bsd_ranking([boa])[0]["bsd"]
    fraca1 = _empresa_solida("F1")
    fraca2 = _empresa_solida("F2")
    for f in (fraca1, fraca2):
        for a in f.anos:
            f.dividendos[a] = 50
            f.lucro_liquido[a] = 1000
            f.fco[a] = 200
        f.desempenho_relativo_6m = -0.20
    bsd_no_lote = [
        r for r in sc.bsd_ranking([boa, fraca1, fraca2]) if r["ticker"] == "BOA3"
    ][0]["bsd"]
    assert abs(bsd_sozinha - bsd_no_lote) < 1e-6


def test_bsd_fatores_faltantes_neutros():
    anos = list(range(2015, 2025))
    c = CompanyData(ticker="X", nome="X", setor="Energia", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = 1000
        c.patrimonio_liquido[a] = 4000
        c.dividendos[a] = 600
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 1800
        c.fco[a] = 1200
    c.preco_atual = 30.0  # sem despesa_juros e sem desempenho_relativo_6m
    r = sc.bsd_ranking([c])[0]
    assert r["n_fatores_faltantes"] >= 1
    assert "cobertura_juros" in r["fatores_faltantes"]
    assert r["bsd"] is not None
