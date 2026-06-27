"""Golden da reconciliação g × fundamentos (DDM-FIX-02 — caso VULC3).

O `g_alto` adotado na fase explícita deixa de ser um haircut do CAGR cru e passa a ser
SUBORDINADO ao crescimento sustentável por fundamentos, calculado com o MESMO payout do
valuation: `g_fund = ROE_normalizado × (1 − payout_valuation)` (CONTEXT FIX-02).

Precedência travada por estes goldens:
  1. g_fund (sustentável) é o teto do g_alto — payout ≥ 100% ⇒ g_fund ≤ 0 ⇒ g_alto = 0
     (SEM o piso artificial `g_estavel` na fase explícita);
  2. teto absoluto 0.25;
  3. trava `g_alto ≤ Ke` (FIX-01, preservada).

Tudo offline: CompanyData montada à mão, nenhuma chamada de rede.
"""

import os

import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _mk(ticker, lucros, pls, divs, *, num_acoes=1000, preco=10.0, beta=0.8):
    """CompanyData de N anos parametrizada (séries explícitas p/ controlar g_fund/CAGR/Ke).

    payout(ano) = div/lucro (num_acoes cancela); roe_valuation = mediana(últimos 3 lucros)
    / PL médio; g_fund = roe_valuation × (1 − payout_valuation).
    """
    anos = list(range(2025 - len(lucros), 2025))
    c = CompanyData(ticker=ticker, nome=ticker, setor="Energia Elétrica", anos=anos)
    for i, ano in enumerate(anos):
        c.lucro_liquido[ano] = lucros[i]
        c.patrimonio_liquido[ano] = pls[i]
        c.dividendos[ano] = divs[i]
        c.num_acoes[ano] = num_acoes
        c.vendas_liquidas[ano] = lucros[i] * 5
        c.fco[ano] = lucros[i] * 1.2
    c.preco_atual = preco
    c.beta = beta
    return c


def test_payout_acima_de_100_zera_g_alto_sem_piso():
    """Payout ≥ 100% ⇒ g_fund = ROE × 0 = 0 ⇒ g_alto adotado = 0, mesmo com CAGR > 0.

    O piso artificial `g_estavel` da fase explícita foi REMOVIDO: o g não pode ser
    sustentado se a empresa distribui todo o lucro (caso VULC3, payout_valuation=100%).
    """
    cfg = _cfg()
    # Lucro crescente (CAGR > 0), mas dividendos = lucro todo ano ⇒ payout 100%.
    lucros = [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050]
    c = _mk("PAY100", lucros, [5000] * 10, divs=list(lucros))

    a = report.analisar_acao(c, cfg)

    assert a.g_fundamentos == 0.0           # ROE_norm × (1 − 1.0) = 0
    assert a.g_historico is not None and a.g_historico > 0  # CAGR cru seria > 0
    assert a.g_alto == 0.0                  # teto sustentável (0) vence o CAGR; sem piso g_estavel
    # Degradação sem exceção: o DDM ainda calcula um intrínseco finito com g_alto = 0.
    assert a.ddm_constante is not None and a.ddm_constante.valor_intrinseco is not None


def test_g_fund_menor_que_cagr_vira_teto_do_g_alto():
    """0 < g_fund < CAGR ⇒ g_alto adotado == g_fund (teto pelo sustentável, não pelo CAGR cru)."""
    cfg = _cfg()
    # ROE_val ≈ 1000/10000 = 0,10; payout 0,8 ⇒ g_fund = 0,10 × 0,2 = 0,02 (< Ke, < CAGR, < 0,25).
    lucros = [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050]
    divs = [round(0.8 * x) for x in lucros]
    c = _mk("GFUND", lucros, [10000] * 10, divs=divs)

    a = report.analisar_acao(c, cfg)

    assert a.g_fundamentos is not None and a.g_fundamentos > 0
    assert a.g_historico is not None and a.g_historico > a.g_fundamentos   # CAGR cru maior
    assert a.ke is not None and a.g_fundamentos < a.ke                     # Ke não morde aqui
    assert a.g_fundamentos < 0.25                                          # teto absoluto não morde
    assert a.g_alto == a.g_fundamentos     # o g adotado é o sustentável, não o CAGR


def test_teto_absoluto_025_quando_g_fund_e_cagr_explodem():
    """g_fund > 0,25 e CAGR > 0,25 (e Ke > 0,25) ⇒ g_alto == 0,25 (teto absoluto preservado)."""
    cfg = _cfg()
    # Crescimento ~40% a.a. (CAGR > 0,25); ROE_val alto + payout baixo ⇒ g_fund > 0,25.
    lucros = [100, 140, 196, 274, 384, 538, 753, 1054, 1476, 2066]
    divs = [round(0.2 * x) for x in lucros]
    # PL p/ ROE_val = mediana(últimos 3 = 1054,1476,2066 → 1476) / 3690 ≈ 0,40.
    c = _mk("TETO", lucros, [3690] * 10, divs=divs, beta=3.0)  # beta alto ⇒ Ke > 0,25

    a = report.analisar_acao(c, cfg)

    assert a.g_fundamentos is not None and a.g_fundamentos > 0.25
    assert a.g_historico is not None and a.g_historico > 0.25
    assert a.ke is not None and a.ke > 0.25     # Ke não morde: o teto que vence é o absoluto
    assert a.g_alto == 0.25


def test_trava_ke_quando_g_fund_supera_ke():
    """g_fund > Ke (e ≤ 0,25), CAGR ≥ g_fund ⇒ após a trava FIX-01, g_alto == Ke."""
    cfg = _cfg()
    # ROE_val ≈ 0,30; payout 0,5 ⇒ g_fund ≈ 0,15 (> Ke≈0,0875, < 0,25); CAGR ≈ 0,20 ≥ g_fund.
    lucros = [100, 125, 156, 195, 244, 305, 381, 477, 596, 745]
    divs = [round(0.5 * x) for x in lucros]
    c = _mk("TRKE", lucros, [1987] * 10, divs=divs, beta=0.8)

    a = report.analisar_acao(c, cfg)

    assert a.ke is not None
    assert a.g_fundamentos is not None and a.g_fundamentos > a.ke   # sustentável acima do Ke
    assert a.g_fundamentos < 0.25                                   # teto absoluto não morde
    assert a.g_historico is not None and a.g_historico >= a.g_fundamentos
    assert a.g_alto == a.ke      # a trava ≤ Ke (FIX-01) é o teto efetivo
