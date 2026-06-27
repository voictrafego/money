"""Golden OFFLINE de PROPRIEDADE multi-ticker do payout sustentável (PAY-01) + DY
recorrente earnings-based (DYR-01) — trava de aceite do marco: o fix vale para QUALQUER
ticker, não tuna a um (Fase 9, success criterion 4).

Estes goldens NÃO usam dados reais (que exigiriam rede): cada perfil é um `CompanyData`
sintético CALIBRADO ao espírito de um dos 5 tickers da metodologia, e cada assert trava
uma PROPRIEDADE do método (não um número de mercado). A confirmação contra os números-alvo
REAIS (VULC3 43% / TAEE11 216% / EGIE3 49% / ITUB4 31% / BBAS3 20%; DY rec. VULC3 6,2% /
TAEE11 8,3%) é o checkpoint human-verify da Task 2 deste plano.

Propriedades travadas (cada uma com 1 comentário "pelo método"):
- TAEE11 (payout >100% em TODO ano): a MEDIANA é legítima >1.0 — NÃO clampada nem zerada.
  É o contraexemplo que zeraria sob o critério (rejeitado) "expurgar payout >100%" (D-02/D-03).
- VULC3 (recorrente ~0.43 + 1 ano extraordinário): a MEDIANA cai no regime recorrente (<1.0),
  descartando o spike sem marcar/excluir o ano (D-01).
- NORMAL ESTÁVEL (EGIE3/ITUB4/BBAS3 spirit): a MEDIANA fica no payout do regime (não rebaixada)
  e o DY recorrente é earnings-based, finito e <= DY trailing sob trailing inflado.
- "PAYOUT >100% NUM ÚNICO ANO" (manchete da fase, success criterion 3): a MEDIANA sobre a série
  completa cai no regime recorrente (<1.0) ⇒ g_fund = ROE_norm × (1 − payout) VOLTA a ser > 0
  (antes era zerado pela saturação do clamp 3a). Contraste explícito com TAEE11/VULC3 (>100%
  em todos/era inteira de anos ⇒ g_fund ≤ 0).

Usa o config.yaml shipado (determinístico, offline) para `report.analisar_acao`.
"""

import os

import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _mk(
    ticker: str,
    lucros: list,
    divs: list,
    *,
    preco: float = 10.0,
    num_acoes: float = 1000.0,
    pl: float = 8000.0,
    dpa_trailing: float | None = None,
    beta: float = 0.90,
) -> CompanyData:
    """Construtor sintético OFFLINE (mesma forma de _vulc3_sintetica): séries por ano
    consistentes (PL/nº de ações) para o report rodar. `payout(ano) = div/lucro`."""
    anos = list(range(2015, 2015 + len(lucros)))
    c = CompanyData(ticker=ticker, nome=f"{ticker} (sintética)", setor="Teste", anos=anos)
    for i, a in enumerate(anos):
        c.lucro_liquido[a] = lucros[i]
        c.patrimonio_liquido[a] = pl
        c.dividendos[a] = divs[i]
        c.num_acoes[a] = num_acoes
        c.vendas_liquidas[a] = lucros[i] * 4
        c.fco[a] = lucros[i] * 1.2
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = preco
    if dpa_trailing is not None:
        c.dpa_trailing_12m = dpa_trailing
    c.beta = beta
    return c


# --------------------------------------------------------------------------- #
# PERFIL TAEE11 — payout >100% em TODO ano (transmissora; distribui de caixa
# regulatório acima do lucro contábil). A mediana é legítima >1.0.
# --------------------------------------------------------------------------- #
def test_perfil_taee11_payout_acima_de_100pct_nao_clampado():
    # div/lucro = 2.1 em TODOS os 10 anos ⇒ mediana = 2.1.
    c = _mk("TAEE11", lucros=[1000] * 10, divs=[2100] * 10)
    p = c.payout_valuation()
    assert p is not None
    # pelo método (D-02/D-03): a mediana >100% é PRESERVADA — o limiar absoluto "expurgar
    # >100%" é rejeitado (zeraria quem paga >100% de forma recorrente e sustentável).
    assert p > 1.0
    assert abs(p - 2.1) < 1e-9


# --------------------------------------------------------------------------- #
# PERFIL VULC3 — recorrente ~0.43 + UM ano extraordinário >1.0.
# --------------------------------------------------------------------------- #
def test_perfil_vulc3_mediana_descarta_spike_extraordinario():
    # payout recorrente 0.43 em 9 anos + 1 ano extraordinário 1.20.
    c = _mk("VULC3", lucros=[1000] * 10, divs=[430] * 9 + [1200])
    p = c.payout_valuation()
    assert p is not None
    # pelo método (D-01): a mediana cai no regime recorrente e descarta o spike sem
    # marcar/excluir o ano — fica < 1.0 e junto do payout dos anos normais (0.43).
    assert p < 1.0
    assert abs(p - 0.43) < 1e-9


# --------------------------------------------------------------------------- #
# PERFIL NORMAL ESTÁVEL — EGIE3/ITUB4/BBAS3 spirit (payout estável ~0.30-0.50).
# --------------------------------------------------------------------------- #
def test_perfil_normal_estavel_mediana_no_regime_e_dy_rec_earnings_based():
    # payout estável 0.49 em toda a série; trailing inflado (dpa_trailing alto).
    c = _mk("EGIE3", lucros=[1000] * 10, divs=[490] * 10, preco=10.0, dpa_trailing=1.0)
    p = c.payout_valuation()
    assert p is not None
    # pelo método: empresa estável ⇒ a mediana NÃO rebaixa o payout do regime (≈0.49).
    assert abs(p - 0.49) < 1e-9
    # DY recorrente é earnings-based (payout × LPA_norm / preço), finito e determinístico:
    # 0.49 × (1000/1000) / 10 = 0.049.
    dy_rec = c.dy_recorrente()
    assert dy_rec is not None
    assert abs(dy_rec - 0.049) < 1e-9
    # pelo método (FIX-06 item J): sob trailing inflado, a leitura recorrente é a
    # sustentável ⇒ dy_recorrente() <= dy_atual() (trailing = 1.0/10 = 0.10).
    assert c.dy_recorrente() <= c.dy_atual()


# --------------------------------------------------------------------------- #
# PERFIL "PAYOUT >100% NUM ÚNICO ANO" — guarda direta do success criterion 3.
# --------------------------------------------------------------------------- #
def test_perfil_payout_acima_100_em_um_ano_g_fund_volta_a_existir():
    # recorrente 0.50 em 9 anos + 1 ano anômalo 1.30 (div = lucro × 1.3).
    c = _mk("XPTO3", lucros=[1000] * 10, divs=[500] * 9 + [1300])
    p = c.payout_valuation()
    assert p is not None
    # pelo método (D-01): a mediana sobre a série completa cai no regime recorrente (<1.0),
    # ao contrário do caso payout>100% em TODOS os anos.
    assert p < 1.0
    a = report.analisar_acao(c, _cfg())
    # pelo método (success criterion 3): com payout sustentável <1.0, g_fund = ROE_norm ×
    # (1 − payout) VOLTA a ser > 0 — antes era zerado pela saturação do clamp 3a quando UM
    # ano passava de 100%.
    assert a.g_fundamentos is not None
    assert a.g_fundamentos > 0


def test_contraste_payout_acima_100_todos_os_anos_g_fund_nao_positivo():
    # payout >100% em TODOS os anos (era VULC3 / espírito TAEE11): a mediana fica >1.0.
    c = _mk("ALLHI3", lucros=[1000] * 10, divs=[2100] * 10)
    a = report.analisar_acao(c, _cfg())
    # pelo método (D-03): payout sustentável >100% ⇒ g_fund = ROE × (1 − payout) ≤ 0; o piso
    # max(0,…) do report pina g_alto = 0. CONTRASTA com o perfil de UM único ano (g_fund > 0).
    assert a.g_fundamentos is not None
    assert a.g_fundamentos <= 0
