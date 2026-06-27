"""Golden de REGRESSÃO end-to-end do caso âncora VULC3 (Vulcabras) — capstone da Fase 8.

Trava a cascata FIX-04 → FIX-02 → FIX-03 → FIX-06 DOMADA num único teste: se qualquer
um dos fixes regredir, este golden falha. Reproduz OFFLINE (sem rede) a patologia que o
relatório de 26/06/2026 expôs:

  - preço R$ 14,40; intrínseco pré-fix R$ 167–334 (11–23× o preço); veredito "SUBAVALIADA"
    verde; payout último 124,7%; DY 37% trailing; ROE cru 51%; Ke 9,4% (literais 2019).

A patologia sintética que a alimenta:
  - UM ano de LUCRO extraordinário (3×) dentro da janela — puxa ROE/CAGR CRUS p/ cima;
  - dividendos ≥ lucro em todos os anos da janela de valuation ⇒ payout cru > 100%;
  - beta 0,88; preço 14,40; PL/nº de ações consistentes p/ o DDM rodar.

Cada limiar abaixo traz 1 linha de justificativa PELO MÉTODO (não número mágico). Usa o
config.yaml shipado (capm.abordagem=local + rf_local=0,105 de fallback ⇒ Ke determinístico
offline, sem chamar o BCB).
"""

import os

import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANO_EXTRAORDINARIO = 2023
ULT = 2024


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _vulc3_sintetica() -> CompanyData:
    """CompanyData OFFLINE que reproduz a patologia VULC3 (cascata pré-fix)."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker="VULC3", nome="Vulcabras (sintética)",
                    setor="Têxtil e Vestuário", anos=anos)
    # Lucro recorrente ~4000 com UM ano extraordinário 12000 (3×) DENTRO da janela de 3 anos:
    # a normalização (mediana) tem de IGNORÁ-LO; o ROE/CAGR CRUS seriam inflados por ele.
    lucro = {a: 4000 for a in anos}
    lucro[ANO_EXTRAORDINARIO] = 12000
    # Dividendos ≥ lucro recorrente em todos os anos ⇒ payout cru > 100% (armadilha Cap. 6).
    div = {a: 5000 for a in anos}
    div[ANO_EXTRAORDINARIO] = 13000
    for a in anos:
        c.lucro_liquido[a] = lucro[a]
        c.patrimonio_liquido[a] = 8000
        c.dividendos[a] = div[a]
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = lucro[a] * 4
        c.fco[a] = lucro[a] * 1.2
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = 14.40
    c.dpa_trailing_12m = 5.0   # proventos 12m / nº ações ⇒ DY trailing ~34,7% (> 15%)
    c.beta = 0.88
    return c


def test_vulc3_cascata_domada_regressao():
    """Os 6 invariantes da cascata domada (um por FIX) + a trava cross-menu do caso âncora."""
    c = _vulc3_sintetica()
    cfg = _cfg()
    a = report.analisar_acao(c, cfg)

    # ---- FIX-04 (normalização de lucro — raiz) ----
    # A base de lucro de VALUATION é a MEDIANA da janela (4000), robusta ao ano extraordinário:
    # tem de ser MENOR que o lucro cru de 12000 que contaminava ROE/CAGR/payout/DY.
    base = c.base_lucro_normalizada()
    assert base is not None
    assert base < c.lucro_liquido[ANO_EXTRAORDINARIO]

    # ---- FIX-02 (reconciliação g × payout) ----
    # PAY-01/D-03: a VULC3 sintética tem div ≥ lucro em todo ano ⇒ a MEDIANA do payout cai
    # na era de payout >100% (≈1.25, sem clamp; o expurgo é intrínseco à mediana).
    assert c.payout_valuation() > 1.0
    # payout sustentável >100% ⇒ g_fund = ROE × (1 − payout) ≤ 0 (crescimento_por_fundamentos
    # não tem piso); o piso max(0, …) do report pina g_alto = 0 (L85 segue valendo).
    assert a.g_fundamentos <= 0.0
    assert a.g_alto == 0.0

    # ---- FIX-03 (CAPM local com Selic) ----
    # Ke = rf_local (0,105 fallback) + beta 0,88 × ERP 0,06 = 0,1578: faixa de small cap BR,
    # MATERIALMENTE acima dos 9,43% dos literais de 2019 que combustionavam o valuation.
    assert a.ke is not None
    assert a.ke > 0.094          # acima do Ke antigo (literais EUA 2019)
    assert a.ke >= 0.15          # dentro da faixa small cap BR

    # ---- FIX-06 (banda = sensibilidade real) + o resultado-âncora da cascata ----
    # O teto da banda intrínseca deixa de ser 11–23× o preço. Limiar = 3× (folga ampla sobre
    # o ~2,3× observado pós-cascata; qualquer regressão de FIX-01/02/03 estouraria os 3×).
    assert a.vmax is not None
    assert a.vmax < 3.0 * c.preco_atual
    # A banda vem da matriz Ke×g (sensibilidade real), não do toggle binário de 2 cenários.
    celulas = [v for linha in (a.sensibilidade or []) for v in linha if v is not None]
    assert celulas and a.vmin == min(celulas) and a.vmax == max(celulas)

    # ---- FIX-05 (veredito consome flags) ----
    # Preço abaixo do intrínseco MAS payout > 100% / DY > 15% ⇒ NÃO é "SUBAVALIADA" verde:
    # é "VERIFICAR — possível divergência de modelo".
    assert not a.veredito.startswith("SUBAVALIADA")
    assert a.veredito.startswith("VERIFICAR")

    # ---- Consistência entre menus (Core Value), travada no caso âncora ----
    # O ROE/payout que o Analisar EXIBE é a MESMA base canônica que o Ranking consome.
    assert a.multiplos["ROE"] == c.roe_valuation()
    assert a.multiplos["DP (payout)"] == c.payout_valuation()


def test_vulc3_normalizacao_doma_roe_e_dy():
    """Tells de apresentação domados: o ROE de valuation < ROE cru do ano extraordinário,
    e o DY recorrente nunca supera o trailing (FIX-04 + FIX-06 item J)."""
    c = _vulc3_sintetica()
    # ROE de valuation (base normalizada) abaixo do ROE cru do ano extraordinário.
    roe_val = c.roe_valuation()
    roe_cru_extraord = c.roe(ANO_EXTRAORDINARIO)
    assert roe_val is not None and roe_cru_extraord is not None
    assert roe_val < roe_cru_extraord
    # DY recorrente (sobre provento normalizado) ≤ DY trailing — leitura sustentável.
    assert c.dy_recorrente() <= c.dy_atual()
