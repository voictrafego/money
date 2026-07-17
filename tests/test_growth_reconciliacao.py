"""Invariantes estruturais da seleção do `g_alto` (GROW-04 / D-01/D-02).

A DOUTRINA MUDOU (Fase 11, GROW-04, D-01): a fase explícita deixou de SUBORDINAR o `g` ao
histórico (`min(g_historico, g_fundamentos)`) e passou a ADOTAR o `g` por fundamentos — o `g`
do livro (`g_fund = ROE_valuation × (1 − payout_valuation)`, Cap. 14.3). O `g_historico` (CAGR
log-linear) NÃO é mais teto: virou número de SANIDADE exibido + FALLBACK (usado só quando
`g_fundamentos` é None).

Os goldens de NÍVEL que codificavam a doutrina antiga (`test_g_fund_menor_que_cagr_vira_teto_do
_g_alto`, `test_teto_absoluto_025_quando_g_fund_e_cagr_explodem`, `test_trava_ke_quando_g_fund
_supera_ke`) foram DELETADOS na Fase 11 (não atualizados — regra dura do CLAUDE.md). Os
invariantes ESTRUTURAIS que estavam presos neles foram EXTRAÍDOS ANTES da deleção, no MESMO
diff (padrão split-before-delete / WR-04):

  1. ADOÇÃO (GROW-04/D-01): com `g_fund` em (0, 0.25) e < Ke, `g_alto == g_fundamentos`
     (o histórico não é mais teto);
  2. TETO ABSOLUTO 0.25: `g_alto` nunca excede 25% a.a., mesmo com `g_fund`/CAGR/Ke explodindo;
  3. TRAVA Ke (FIX-01, D-02): `g_alto ≤ Ke` — o teto econômico da fase explícita sobrevive;
  4. PAYOUT ≥ 100% ⇒ `g_alto = 0` sem piso artificial (contrato de borda, preservado).

Não há mais nenhum NÍVEL em reais/percentual do método antigo travado aqui: as fixtures são
sintéticas (CompanyData montada à mão, sem ticker, offline) e os asserts são ESTRUTURAIS
(`== g_fundamentos`, `== 0.25`, `== ke`, `== 0`) — BLIND-04a-safe. Tudo offline, nenhuma rede.
"""

import os

import pytest
import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _mk(ticker, lucros, pls, divs, *, num_acoes=1000, preco=10.0, beta=0.8):
    """CompanyData de N anos parametrizada (séries explícitas p/ controlar g_fund/CAGR/Ke).

    payout(ano) = div/lucro (num_acoes cancela); roe_valuation = mediana dos ROEs anuais
    (lucro_t / PL médio(t-1,t)); g_fund = roe_valuation × (1 − payout_valuation).
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

    O piso artificial `g_estavel` da fase explícita não existe: o g não pode ser sustentado se
    a empresa distribui todo o lucro (caso VULC3, payout_valuation = 100%). Contrato de borda:
    a degradação é sem exceção (o DDM ainda calcula um intrínseco finito com g_alto = 0).
    """
    cfg = _cfg()
    # Lucro crescente (CAGR > 0), mas dividendos = lucro todo ano ⇒ payout 100%.
    lucros = [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050]
    c = _mk("PAY100", lucros, [5000] * 10, divs=list(lucros))

    a = report.analisar_acao(c, cfg)

    assert a.g_fundamentos == 0.0           # ROE_norm × (1 − 1.0) = 0
    assert a.g_historico is not None and a.g_historico > 0  # CAGR cru seria > 0
    assert a.g_alto == 0.0                  # o g sustentável (0) vence o CAGR; sem piso g_estavel
    # Degradação sem exceção: o DDM ainda calcula um intrínseco finito com g_alto = 0.
    assert a.ddm_constante is not None and a.ddm_constante.valor_intrinseco is not None


@pytest.mark.invariante
def test_g_alto_adota_g_fundamentos_nao_subordina_ao_historico():
    """GROW-04/D-01: com g_fund em (0, 0.25) e < Ke, `g_alto == g_fundamentos` — o g adotado é o
    SUSTENTÁVEL por fundamentos (o do livro), NÃO o mínimo com o CAGR histórico.

    A doutrina antiga (`min(g_historico, g_fundamentos)`) foi REVERTIDA: mesmo quando o CAGR cru
    (g_historico) é MAIOR que o g por fundamentos, o histórico não morde — deixou de ser teto e
    virou apenas número de sanidade/fallback. Invariante estrutural (`g_alto == g_fundamentos`),
    não um nível: extraído do golden deletado `test_g_fund_menor_que_cagr_vira_teto_do_g_alto`.
    """
    cfg = _cfg()
    # ROE_val ≈ 0,17 (mediana); payout 0,8 ⇒ g_fund ≈ 0,017 (< Ke 0,153, < CAGR, < 0,25).
    lucros = [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050]
    divs = [round(0.8 * x) for x in lucros]
    c = _mk("GFUND", lucros, [10000] * 10, divs=divs)

    a = report.analisar_acao(c, cfg)

    assert a.g_fundamentos is not None and a.g_fundamentos > 0
    assert a.g_historico is not None and a.g_historico > a.g_fundamentos   # CAGR cru maior
    assert a.ke is not None and a.g_fundamentos < a.ke                     # Ke não morde aqui
    assert a.g_fundamentos < 0.25                                          # teto absoluto não morde
    assert a.g_alto == a.g_fundamentos     # ADOÇÃO: o g adotado é o sustentável, não o CAGR


@pytest.mark.invariante
def test_g_alto_respeita_o_teto_absoluto_de_025():
    """TETO ABSOLUTO: g_fund > 0,25 e CAGR > 0,25 (e Ke > 0,25) ⇒ g_alto == 0,25.

    Invariante estrutural preservado da doutrina antiga (extraído do golden deletado
    `test_teto_absoluto_025_quando_g_fund_e_cagr_explodem`): nenhum g explícito adotado pode
    exceder 25% a.a., independentemente do g por fundamentos, do CAGR ou do Ke.
    """
    cfg = _cfg()
    # Crescimento ~40% a.a. (CAGR > 0,25); ROE_val alto + payout baixo ⇒ g_fund > 0,25.
    lucros = [100, 140, 196, 274, 384, 538, 753, 1054, 1476, 2066]
    divs = [round(0.2 * x) for x in lucros]
    # PL baixo ⇒ mediana(ROE) alta ⇒ g_fund ≈ 0,36 (> 0,25); beta 3,0 ⇒ Ke ≈ 0,285 (> 0,25).
    c = _mk("TETO", lucros, [1200] * 10, divs=divs, beta=3.0)

    a = report.analisar_acao(c, cfg)

    assert a.g_fundamentos is not None and a.g_fundamentos > 0.25
    assert a.g_historico is not None and a.g_historico > 0.25
    assert a.ke is not None and a.ke > 0.25     # Ke não morde: o teto que vence é o absoluto
    assert a.g_alto == 0.25


@pytest.mark.invariante
def test_g_alto_trava_no_ke_quando_fundamentos_supera_ke():
    """TRAVA Ke (FIX-01, D-02): g_fund > Ke (e ≤ 0,25), CAGR ≥ g_fund ⇒ g_alto == Ke.

    Invariante estrutural preservado (extraído do golden deletado `test_trava_ke_quando_g_fund
    _supera_ke`): a trava econômica `g_alto ≤ Ke` da fase explícita sobrevive à adoção do g por
    fundamentos. Sem ela o fator (1+g)/(1+Ke) > 1 faria a fase explícita inflar em vez de
    convergir. O teto do g explícito é o Ke — o g_cap (perpetuidade) trava SÓ o terminal (D-02).
    """
    cfg = _cfg()
    # PL ⇒ mediana(ROE) ≈ 0,36 e g_fund ≈ 0,18 (> Ke 0,153, < 0,25); CAGR ≈ 0,25 ≥ g_fund.
    lucros = [100, 125, 156, 195, 244, 305, 381, 477, 596, 745]
    divs = [round(0.5 * x) for x in lucros]
    c = _mk("TRKE", lucros, [850] * 10, divs=divs, beta=0.8)

    a = report.analisar_acao(c, cfg)

    assert a.ke is not None
    assert a.g_fundamentos is not None and a.g_fundamentos > a.ke   # sustentável acima do Ke
    assert a.g_fundamentos < 0.25                                   # teto absoluto não morde
    assert a.g_historico is not None and a.g_historico >= a.g_fundamentos
    assert a.g_alto == a.ke      # a trava ≤ Ke (FIX-01) é o teto efetivo
