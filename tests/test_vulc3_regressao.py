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


def _itub4_live_like() -> CompanyData:
    """ITUB4 com MAGNITUDES live (CAL-01): VPA~19, ROE~19,3%, payout~46,7%, beta 1,0. Roda o
    caminho de DISPATCH real (analisar_acao → _intrinseco_por_motor motor='rim'), provando que
    os novos knobs de config CHEGAM ao motor. Se o dispatch ler uma key errada, degrada
    silenciosamente para ~R$23 e este gate (>30) pega — o capstone com VPA=5 só checa > 0."""
    c = CompanyData(ticker="ITUB4", nome="Itaú (live-like)", setor="Bancos", anos=_anos())
    for a in _anos():
        c.lucro_liquido[a] = 3667.0        # ROE = 3667/19000 ≈ 0,193
        c.patrimonio_liquido[a] = 19000.0  # VPA = 19000/1000 = 19,0
        c.dividendos[a] = 1712.0           # payout ≈ 0,467 → retenção ≈ 0,533
        c.num_acoes[a] = 1000.0
        c.vendas_liquidas[a] = 14000.0
        c.fco[a] = 4400.0
    c.preco_atual = 44.30
    c.beta = 1.0
    return c


def test_rim_itub4_dispatch_banda():
    """GATE DE INTEGRAÇÃO (CAL-01, fecha o key_link report→motores.rim): com insumos ITUB4 de
    magnitude live, o intrínseco do motor RIM cai MATERIALMENTE acima do teto D-02 antigo
    (>R$30, não só >0). Prova que excesso_sustentavel/g_terminal/ke_teto chegam ao funil."""
    cfg = _cfg()
    a = report.analisar_acao(_itub4_live_like(), cfg)
    assert a.arquetipo == "financeira"
    assert a.motor == "rim"
    assert a.intrinseco_motor is not None
    # Acima do teto D-02 antigo (~R$23): prova que o valor terminal chegou pelo dispatch.
    assert a.intrinseco_motor > 30.0


def _taee11_regulada() -> CompanyData:
    """TAEE11-âncora: utility regulada (Energia Elétrica, eh_concessionaria) → pagadora
    regulada → motor DDM. É o baseline que NÃO pode mexer: veredito DDM, sem suspensão,
    sem reetiqueta, sem fronteiriço — determinístico e idêntico entre execuções."""
    c = CompanyData(ticker="TAEE11", nome="Taesa (sintética)", setor="Energia Elétrica",
                    anos=_anos(), eh_concessionaria=True)
    for a in _anos():
        c.lucro_liquido[a] = 1000 + (a - 2015) * 50
        c.patrimonio_liquido[a] = 4000 + (a - 2015) * 100
        c.dividendos[a] = 600 + (a - 2015) * 30
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 1800
        c.fco[a] = 1200
    c.preco_atual = 30.0
    c.beta = 0.8
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


def test_capstone_itub4_sem_evitar_motor_rim_ddm_como_lente():
    """ITUB4 (SC#1): financeira → motor RIM alimenta o veredito, DDM é lente conservadora,
    e o selo NUNCA estampa 'Evitar' (o erro de arquitetura domado)."""
    cfg = _cfg()
    a = report.analisar_acao(_itub4_financeira(), cfg)
    assert a.arquetipo == "financeira"
    assert a.motor == "rim"
    assert a.banda_do_motor is True
    # O motor RIM referenciado (intrínseco do motor populado e positivo).
    assert a.intrinseco_motor is not None and a.intrinseco_motor > 0
    # DDM rebaixado a lente conservadora (contraponto capturado ANTES da banda do ensemble).
    assert a.contraponto_valor is not None
    assert any("lente conservadora" in al.lower() for al in a.alertas)
    # NUNCA 'Evitar': nem o texto do veredito nem o selo (bsd alto → qualidade Alta).
    assert "Evitar" not in a.veredito
    assert selo_mod.montar_selo(70.0, a.veredito, cfg).rotulo != "Evitar"


def test_capstone_taee11_baseline_ddm_identico():
    """TAEE11 (baseline intocado): motor DDM, sem suspensão/reetiqueta/fronteiriço, e o
    veredito/banda determinísticos (idênticos entre duas execuções)."""
    cfg = _cfg()
    a1 = report.analisar_acao(_taee11_regulada(), cfg)
    assert a1.arquetipo == "pagadora_regulada"
    assert a1.motor == "ddm"
    assert a1.banda_do_motor is False
    assert a1.san01_reetiquetado is False
    assert a1.arquetipo_fronteirico is False
    assert a1.arquetipo_incerto is False
    assert not a1.veredito.startswith("VERIFICAR")
    # Idêntica ao baseline: reexecutar a MESMA fixture dá o MESMO veredito/banda (sem deriva).
    a2 = report.analisar_acao(_taee11_regulada(), cfg)
    assert a2.veredito == a1.veredito
    assert (a2.vmin, a2.vmax) == (a1.vmin, a1.vmax)


def test_capstone_vale3_motor_normalizado():
    """VALE3 (SC#2): cíclica → motor 'normalizado' (não DDM), banda do motor, sem fronteiriço."""
    cfg = _cfg()
    a = report.analisar_acao(_vale3_ciclica(), cfg)
    assert a.arquetipo == "ciclica"
    assert a.motor == "normalizado"
    assert a.banda_do_motor is True
    assert a.intrinseco_motor is not None and a.intrinseco_motor > 0
    assert selo_mod.montar_selo(70.0, a.veredito, cfg).rotulo != "Evitar"


def test_capstone_wege3_motor_dcf_sem_faixa_lixo():
    """WEGE3 (SC#2): crescimento → motor 'dcf', intrínseco positivo e FINITO, banda do motor
    saudável (0 < vmin ≤ vmax, sem faixa-lixo)."""
    cfg = _cfg()
    a = report.analisar_acao(_wege3_crescimento(), cfg)
    assert a.arquetipo == "crescimento"
    assert a.motor == "dcf"
    assert a.banda_do_motor is True
    assert a.intrinseco_motor is not None
    assert a.intrinseco_motor > 0 and math.isfinite(a.intrinseco_motor)
    # Banda do motor saudável: sem faixa negativa/degenerada/infinita.
    assert a.vmin is not None and a.vmax is not None
    assert 0 < a.vmin <= a.vmax
    assert math.isfinite(a.vmax)


def test_capstone_vulc3_verifica_por_risco_real():
    """VULC3 (invariante): payout > 100% (risco REAL) → veredito começa com 'VERIFICAR'
    mesmo após toda a Fase 3 — o veredito honesto não maquia armadilha de dividendos."""
    cfg = _cfg()
    a = report.analisar_acao(_vulc3_sintetica(), cfg)
    assert a.veredito.startswith("VERIFICAR")
    assert not a.veredito.startswith("SUBAVALIADA")
