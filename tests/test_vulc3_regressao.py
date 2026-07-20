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

import math
import os

import pytest
import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report
from analista.report import selo as selo_mod

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


@pytest.mark.invariante
def test_vulc3_cascata_estrutural_sobrevive():
    """WR-04 (split-before-delete): os invariantes ESTRUTURAIS da cascata domada da VULC3.

    Substitui o golden de NÍVEL `test_vulc3_cascata_domada_regressao` (classificado
    `golden_nivel`), DELETADO na Fase 11 (GROW). Aquele golden travava DUAS bandas de nível que
    a cura tornou obsoletas — NÃO atualizadas, DELETADAS (regra dura do CLAUDE.md):
      (i) FIX-06: `vmax < 3× preço` — calibrada ao `g_estavel = 2,5%` REAL. O `g_cap` derivado da
          Fase 11 (~7,28%) encolhe o spread `Ke − g` da perpetuidade e o peso do valor terminal
          quase dobra (Armadilha 5, prevista no D-07): o teto da matriz Ke×g subiu de ~2,3× para
          ~3,6× o preço. É o mesmo reflexo do `g` antigo que esta fase remove do repo.
      (ii) FIX-03: `ke >= 0,15` (banda absoluta de Ke small-cap BR) — NÍVEL de Ke, território da
          Fase 12 (KE). Deletado aqui em vez de arrastar um nível de Ke para a suíte default.
    O que SOBREVIVE (extraído ANTES da deleção, no MESMO diff) é a estrutura, não o nível:
    normalização robusta, g sustentável ≤ 0 sob payout > 100%, Ke materialmente acima do 2019,
    a banda como região da margem de segurança sobre o RIM único (Fase 13/ENG-01), a armadilha de
    payout > 100% surfaçada nos alertas, e a consistência cross-menu (Core Value). Nenhum nível em
    reais/percentual do método antigo permanece travado — BLIND-04a-safe (asserts estruturais).
    """
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
    # não tem piso); o piso max(0, …) do report pina g_alto = 0 (segue valendo com o g adotado).
    assert a.g_fundamentos <= 0.0
    assert a.g_alto == 0.0

    # ---- FIX-03 (CAPM local com Selic) — RELACIONAL (o nível de Ke é Fase 12) ----
    # Ke = rf_local (fallback) + beta × ERP: MATERIALMENTE acima dos 9,43% dos literais de 2019
    # que combustionavam o valuation. Assert relacional (> 2019), não a banda absoluta.
    assert a.ke is not None
    assert a.ke > 0.094          # acima do Ke antigo (literais EUA 2019)

    # ---- Banda = região da margem de segurança sobre o RIM único (ENG-01, Fase 13) ----
    # REWRITE: a banda deixou de ser o min/max da matriz DDM (o ensemble/matriz-como-fonte morreu
    # no Plano 03). Sob o RIM único é a região SIMÉTRICA V×(1∓ms) sobre o intrínseco do RIM (o
    # Plano 04 formaliza a região da MS primária). Invariante estrutural (sem nível em reais).
    assert a.intrinseco_motor is not None and a.intrinseco_motor > 0
    ms = cfg.get("veredito", {}).get("margem_seguranca", 0.15)
    assert a.vmin is not None and a.vmax is not None
    assert abs(a.vmin - a.intrinseco_motor * (1.0 - ms)) < 1e-9
    assert abs(a.vmax - a.intrinseco_motor * (1.0 + ms)) < 1e-9

    # ---- FIX-05 (veredito não vende armadilha como barganha) — INVARIANTE que SOBREVIVE ----
    # payout > 100% (armadilha Cap. 6) ⇒ o veredito NÃO pode ser "SUBAVALIADA" verde (barganha).
    # O veto de risco continua vivo no ramo SUBAVALIADA; e a armadilha é SEMPRE surfaçada nos
    # alertas (mesmo quando a banda estreita da MS põe o preço "NO INTERVALO"). O prefixo VERIFICAR
    # do método antigo dependia da banda DDM larga (preço abaixo de vmin) — DELETADO com ela.
    assert not a.veredito.startswith("SUBAVALIADA")
    assert any("Payout > 100%" in al for al in a.alertas)

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


# =========================================================================== #
# CAPSTONE e2e da FASE 3 (v2.2) — tickers-âncora sobre o VEREDITO FINAL da fase
# (VER-01/ENS-01/SAN-01/VER-02). Cada âncora prova que o selo consome o motor do
# ARQUÉTIPO, não o DDM fixo. Fixtures sintéticas OFFLINE (nenhuma chamada de rede),
# espelhando os padrões já provados em test_arquetipo_roteamento.py.
# =========================================================================== #

def _anos():
    return list(range(2015, 2025))


def _itub4_financeira() -> CompanyData:
    """ITUB4-âncora: banco (setor 'Bancos') → hard-route financeira → motor RIM. O RIM
    alimenta o veredito (banda do ensemble) e o DDM é rebaixado a lente conservadora; o
    compounder de qualidade NUNCA mais é carimbado 'Evitar' pelo DDM de estágio único."""
    c = CompanyData(ticker="ITUB4", nome="Itaú (sintética)", setor="Bancos", anos=_anos())
    for a in _anos():
        c.lucro_liquido[a] = 1000
        c.patrimonio_liquido[a] = 5000
        c.dividendos[a] = 300
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 4000
        c.fco[a] = 1200
    c.preco_atual = 70.0
    c.beta = 0.9
    return c


def _vale3_ciclica() -> CompanyData:
    """VALE3-âncora: cíclica (lucro oscilando com anos de prejuízo → cíclica, ROE baixo →
    retenção baixa, sem crescimento) → motor 'normalizado' (lucro médio), não DDM."""
    lucros = [800, -200, 900, 300, 1000, -100, 850, 400, 950, 500]
    c = CompanyData(ticker="VALE3", nome="Vale (sintética)", setor="Extração Mineral", anos=_anos())
    for a, lucro in zip(_anos(), lucros):
        c.lucro_liquido[a] = float(lucro)
        c.patrimonio_liquido[a] = 5000.0
        c.dividendos[a] = 0.30 * abs(float(lucro))
        c.num_acoes[a] = 1000.0
        c.vendas_liquidas[a] = abs(float(lucro)) * 4
    c.preco_atual = 15.0
    c.beta = 1.0
    return c


def _wege3_crescimento() -> CompanyData:
    """WEGE3-âncora: compounder de qualidade (lucro cresce suave sem prejuízo → crescimento,
    ROE alto + retenção alta) → motor 'dcf'. A banda vem do motor, sem faixa-lixo."""
    c = CompanyData(ticker="WEGE3", nome="WEG (sintética)", setor="Máquinas e Equipamentos",
                    anos=_anos())
    for i, a in enumerate(_anos()):
        lucro = round(1000 * (1.12 ** i))   # ~12%/ano, suave (não cíclica)
        c.lucro_liquido[a] = float(lucro)
        c.patrimonio_liquido[a] = 4000.0
        c.dividendos[a] = round(0.25 * lucro)   # payout 25% → retenção 75%
        c.num_acoes[a] = 1000.0
        c.vendas_liquidas[a] = lucro * 4
        c.fco[a] = lucro * 1.2
    c.preco_atual = 40.0
    c.beta = 0.9
    return c


def test_capstone_vulc3_nao_vende_armadilha_como_barganha():
    """VULC3 (invariante): payout > 100% (risco REAL) NÃO é vendido como 'SUBAVALIADA' (barganha),
    e a armadilha é surfaçada nos alertas — o veredito honesto não maquia armadilha de dividendos.

    REWRITE (Fase 13/ENG-01): o prefixo 'VERIFICAR' do método antigo dependia da banda DDM LARGA
    que punha o preço abaixo de vmin; sob o RIM único a banda é a região estreita da MS e o preço
    pode cair 'NO INTERVALO'. O invariante que SOBREVIVE é: não-SUBAVALIADA + armadilha nos alertas.
    """
    cfg = _cfg()
    a = report.analisar_acao(_vulc3_sintetica(), cfg)
    assert not a.veredito.startswith("SUBAVALIADA")
    assert any("Payout > 100%" in al for al in a.alertas)
