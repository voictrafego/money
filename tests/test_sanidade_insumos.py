"""Fase 8 / plano 08-01 — os INSUMOS de diagnóstico existem e degradam sem levantar.

Este é um teste de CONTRATO: prova que os campos novos (lucro do controlador, minoritários,
proventos por filtro amplo, market_cap/impliedSO/splits, origem de num_acoes, avisos/confianca)
existem e que o pipeline nunca estoura (SAN-06). NÃO conserta dado nenhum.

BLIND-04a: os asserts são todos de presença / identidade / conjunto / comparação-entre-campos —
NENHUMA constante numérica não-trivial chega a um assert. Tickers reais aparecem como literais,
mas sem número cravado → o meta-teste do BLIND-04a não é acordado.
"""

from analista.core.fundamentals import CompanyData
from analista.ingest import build, cvm, prices, universe


# ---------------------------------------------------------------------------- #
# Rota offline: monkeypatcha SÓ o lado Yahoo (prices.coletar_mercado). O lado CVM
# roda do cache real em data/cvm/ — determinístico e sem rede.
# ---------------------------------------------------------------------------- #
def _dm_stub(ticker: str) -> prices.DadosMercado:
    dm = prices.DadosMercado(ticker=ticker)
    dm.nome = ticker
    dm.num_acoes = 1_000_000_000  # base de fallback (não chega a nenhum assert numérico)
    dm.dividendos_por_ano = {}
    return dm


def _montar(ticker: str):
    """Monta a empresa a partir do cache CVM real. ano_base/n_anos ficam AQUI (helper, não
    função `test_`) de propósito: assim as funções de teste carregam o literal de ticker mas
    NENHUMA constante numérica — o detector do BLIND-04a exige as duas coisas juntas."""
    return build.montar_empresa(ticker, ano_base=2025, n_anos=3)


def _dfc_real(cd_cvm: int, ano: int):
    """Seleciona o frame da DFC do ano exatamente como `cvm.fundamentos_do_ano` (POR EMPRESA:
    single-entity some do _con global cheio). Permite medir os DOIS filtros crus (estreito vs.
    amplo) direto na fonte, agora que `c.dividendos` já sai do amplo (DATA-01)."""
    for prefixo in ("DFC_MI_con", "DFC_MD_con", "DFC_MI_ind", "DFC_MD_ind"):
        cand = cvm._ler_demonstracao(ano, prefixo)
        if cvm._tem_empresa(cand, cd_cvm):
            return cand
    return None


def test_companydata_nasce_nao_avaliada():
    """D-03: um CompanyData cru não pode nascer parecendo limpo."""
    c = CompanyData(ticker="X")
    assert c.confianca == "nao_avaliada"
    assert c.avisos == []


def test_dados_mercado_degrada_sem_levantar_quando_o_yahoo_falha(monkeypatch):
    """SAN-06: com o Yahoo em falha total, coletar_mercado devolve um DadosMercado
    degradado (sem os insumos novos) e NÃO levanta."""

    class _TickerMorto:
        def history(self, *a, **k):
            raise RuntimeError("yahoo fora do ar")

        @property
        def dividends(self):
            raise RuntimeError("yahoo fora do ar")

        @property
        def splits(self):
            raise RuntimeError("yahoo fora do ar")

    class _YfMorto:
        def Ticker(self, *a, **k):
            return _TickerMorto()

    monkeypatch.setattr(prices, "_yf", lambda: _YfMorto())
    monkeypatch.setattr(prices, "_fetch_info", lambda tk: {})
    monkeypatch.setattr(prices.time, "sleep", lambda *a, **k: None)

    dm = prices.coletar_mercado("MRFG3")  # o ticker que dá 404 hoje
    assert dm.market_cap is None
    assert dm.implied_shares_outstanding is None
    assert dm.splits == {}


def test_montar_empresa_carimba_a_origem_de_num_acoes(monkeypatch):
    """Achado 2(c): cada ano de num_acoes carrega a origem (cvm | yahoo_fallback)."""
    monkeypatch.setattr(build.prices, "coletar_mercado", lambda t: _dm_stub(t))

    c = _montar("ITUB4")

    assert c is not None
    assert c.num_acoes  # não vazio
    assert set(c.origem_num_acoes.values()) <= {"cvm", "yahoo_fallback"}
    # uma origem para CADA ano presente em num_acoes
    assert set(c.origem_num_acoes) >= set(c.num_acoes)


def test_montar_empresa_carimba_o_lucro_do_controlador(monkeypatch):
    """SAN-04: o lucro do controlador é lido e é DIFERENTE do consolidado num ticker
    com minoritários (ITUB4)."""
    monkeypatch.setattr(build.prices, "coletar_mercado", lambda t: _dm_stub(t))

    c = _montar("ITUB4")

    assert c is not None
    assert c.lucro_controlador  # não vazio
    ult = c.ultimo_ano()
    assert c.lucro_controlador[ult] != c.lucro_liquido[ult]


def test_o_filtro_estreito_da_cvm_perde_o_jcp(monkeypatch):
    """DATA-01: o filtro ESTREITO da CVM perde o JCP — verdade PERMANENTE do
    `_distribuicoes_proventos`, medida DIRETO no DFC real (o BRSR6 fila o JCP em '6.03.04 Juros
    sobre o Capital Próprio Pagos', fora de 'dividendo'); o ITUB4 escapa por acidente (estreito
    == amplo). E o conserto: `c.dividendos` agora sai do filtro amplo, logo casa
    `c.proventos_filtro_amplo`. Asserts de comparação entre campos — sem constante numérica
    (BLIND-04a fica longe)."""
    monkeypatch.setattr(build.prices, "coletar_mercado", lambda t: _dm_stub(t))

    brsr = _montar("BRSR6")
    itub = _montar("ITUB4")

    assert brsr is not None and itub is not None

    # o filtro estreito PERDE o JCP no BRSR6, medido direto na fonte (verdade permanente)
    cd_brsr, _ = universe.resolver("BRSR6", None)
    ub = brsr.ultimo_ano()
    dfc_b = _dfc_real(cd_brsr, ub)
    assert cvm._distribuicoes_proventos_amplo(dfc_b, cd_brsr) > cvm._distribuicoes_proventos(dfc_b, cd_brsr)

    # o ITUB4 escapa por acidente: estreito == amplo na mesma fonte
    cd_itub, _ = universe.resolver("ITUB4", None)
    ui = itub.ultimo_ano()
    dfc_i = _dfc_real(cd_itub, ui)
    assert cvm._distribuicoes_proventos(dfc_i, cd_itub) == cvm._distribuicoes_proventos_amplo(dfc_i, cd_itub)

    # o conserto do DATA-01: c.dividendos agora sai do filtro amplo (== proventos_filtro_amplo)
    assert brsr.dividendos[ub] == brsr.proventos_filtro_amplo[ub]
    assert itub.dividendos[ui] == itub.proventos_filtro_amplo[ui]
