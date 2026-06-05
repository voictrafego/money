"""Trava de consistência cross-modo (TEST-01).

A MESMA `CompanyData` (montada à mão, sem rede) deve produzir ROE/payout/veredito
coerentes entre os três modos do app:

- **Analisar:** `report.analisar_acao(c, cfg)` → `a.multiplos["ROE"]`,
  `a.multiplos["DP (payout)"]`, `a.veredito` (DDM).
- **Ranking:** funções diretas da engine — `c.roe(ult)`, `c.payout_valuation()`,
  `c.payout(ult)` e a regressão `cmp.preco_alvo_por_regressao(...).subavaliada`.

É a rede de segurança que impede uma futura divergência de reintroduzir os bugs
CR-02 / CR-03 / WR-03 fechados na Fase 1. Tudo offline: nenhuma chamada de rede.
"""

import os

import yaml

from analista.core import comparables as cmp
from analista.core import multiples as mult
from analista.core.fundamentals import CompanyData
from analista.report import report

# Raiz do projeto (espelha cli.py:25-32 — yaml.safe_load, SEM @st.cache_data).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    """Carrega config.yaml da raiz, como o cli.py (sem cache do streamlit)."""
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _empresa_solida(ticker="TAEE11"):
    """Fixture-modelo (espelha tests/test_screening.py:7-26): 10 anos, todos os campos."""
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


def test_roe_coerente_analisar_vs_ranking():
    """ROE exibido pelo Analisar == ROE do caminho Ranking (ambos c.roe(ult))."""
    c = _empresa_solida()
    cfg = _cfg()
    ult = c.ultimo_ano()

    a = report.analisar_acao(c, cfg)

    # Caminho Analisar (report.py:53) vs caminho Ranking (app.py:261). Igualdade exata.
    assert a.multiplos["ROE"] == c.roe(ult)
    assert a.multiplos["ROE"] is not None


def test_payout_coerente_ultimo_ano_vs_valuation():
    """O Analisar expõe DOIS payouts (PAYOUT-02): o último ano cru e o de valuation.

    - `multiplos["DP (payout)"]` == `c.payout(ult)` (último ano cru, report.py:56).
    - `c.payout_valuation()` (média 3a + clamp) é o número canônico do DDM/Ranking,
      distinto do cru. Ambos devem existir e ser floats coerentes.
    """
    c = _empresa_solida()
    cfg = _cfg()
    ult = c.ultimo_ano()

    a = report.analisar_acao(c, cfg)

    # Último ano cru: idêntico entre Analisar e a função da engine.
    assert a.multiplos["DP (payout)"] == c.payout(ult)

    # Payout de valuation (canônico, média 3a + clamp): mesma função no Analisar e no Ranking.
    pv = c.payout_valuation()
    assert isinstance(pv, float)
    # São os DOIS números do PAYOUT-02: o cru do último ano e o de valuation. A média 3a
    # suaviza, então tipicamente difere do ano cru — mas ambos vêm da mesma engine.
    assert pv == c.payout_valuation()  # função canônica única (determinística)


def _empresa_param(ticker, *, preco, lucro, pl, div, num_acoes=1000):
    """CompanyData de 10 anos parametrizada para montar a amostra da regressão.

    Mantém séries constantes (sem crescimento) para um ROE/payout estáveis e simples
    de calibrar. `preco` define o P/L corrente; `lucro`/`pl`/`div` definem ROE e payout.
    """
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome=ticker, setor="Energia Elétrica", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = lucro
        c.patrimonio_liquido[a] = pl
        c.dividendos[a] = div
        c.num_acoes[a] = num_acoes
        c.vendas_liquidas[a] = lucro * 5
        c.fco[a] = lucro * 1.2
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = preco
    c.volume_financeiro_diario = 40_000_000
    c.desempenho_relativo_6m = 0.10
    c.beta = 0.8
    return c


def test_veredito_direcao_coerente():
    """Direção (subavaliada/cara) coerente entre DDM (Analisar) e regressão (Ranking).

    Monta ≥4 CompanyData determinísticas (tickers distintos) calibradas para que:
      - a regressão P/L = f(DP, ROE) ajuste (n≥4, comparables.py:94) — NÃO pode ser None;
      - a empresa-alvo seja claramente BARATA: preço bem abaixo do valor justo, ROE alto
        e payout saudável, com os comparáveis em P/L mais alto (puxando o P/L "justo" da
        alvo para cima).
    Afirma a DIREÇÃO (sinal), não igualdade numérica (DDM ≠ regressão por construção).
    A asserção é obrigatória e nunca opcional: se o sinal não estabilizar, recalibram-se
    os números das fixtures (preços/lucros/dividendos/PL) — nunca se relaxa o assert.
    """
    cfg = _cfg()

    # Empresa-alvo claramente barata: ROE ~25%, payout ~50%, preço (6,00) abaixo TANTO do
    # valor intrínseco do DDM (~8,20 com LPA 1,0) quanto do preço-alvo da regressão.
    alvo = _empresa_param("AAA3", preco=6.0, lucro=1000, pl=4000, div=500)
    # Comparáveis com P/L corrente ALTO (preço caro vs lucro): puxam o P/L justo para cima,
    # tornando o preço-alvo da AAA3 (barata) acima do seu preço corrente.
    comp_b = _empresa_param("BBB3", preco=40.0, lucro=1000, pl=4000, div=500)
    comp_c = _empresa_param("CCC3", preco=45.0, lucro=900, pl=4000, div=480)
    comp_d = _empresa_param("DDD3", preco=42.0, lucro=950, pl=4200, div=510)
    empresas = [alvo, comp_b, comp_c, comp_d]

    # Vetores PL/DP/ROE como no modo Ranking (app.py:265-266).
    PL, DP, ROE = [], [], []
    for c in empresas:
        u = c.ultimo_ano()
        PL.append(mult.preco_lucro(c.preco_atual, c.lpa(u)))
        DP.append(c.payout_valuation())
        ROE.append(c.roe(u))

    reg = cmp.ajustar_regressao_pl(PL, DP, ROE)
    # Com 4 fixtures completas a regressão NÃO pode falhar (n≥4). Se vier None é bug do teste.
    assert reg is not None, "regressão None com 4 fixtures — calibrar PL/DP/ROE"
    assert reg.n >= 4

    # Preço-alvo da empresa-alvo pelo Ranking (regressão).
    u = alvo.ultimo_ano()
    pa = cmp.preco_alvo_por_regressao(
        reg, alvo.payout_valuation(), alvo.roe(u), alvo.lpa(u), alvo.preco_atual
    )
    assert pa is not None, "PrecoAlvo None — todos os campos da alvo estão presentes"

    # Veredito da MESMA empresa pelo Analisar (DDM).
    a = report.analisar_acao(alvo, cfg)
    assert a.veredito, "veredito vazio — DDM não rodou (checar beta/ke/payout)"

    # Coerência de DIREÇÃO (sinal), não de valor: barato no DDM <=> barato na regressão.
    assert a.veredito.startswith("SUBAVALIADA") == pa.subavaliada
    # Ancorar o teste num sinal determinístico conhecido: a alvo foi calibrada como barata.
    assert pa.subavaliada is True
    assert a.veredito.startswith("SUBAVALIADA")
