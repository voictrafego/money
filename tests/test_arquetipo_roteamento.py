"""Golden e2e do roteamento por arquétipo PLUGADO no funil (Fase 1 v2.2, ARQ-01/ENG-01/D-04).

Ao contrário de test_arquetipo.py (que trava o classificador PURO), aqui o contrato é
ponta-a-ponta via `report.analisar_acao`: o roteamento vira comportamento observável no
veredito e no render.

- REGULADA (motor ddm): TAEE11-like idêntica — veredito DDM, NÃO suspenso (ENG-06).
- FINANCEIRA (motor pendente): ITUB4-like — veredito suspenso via "VERIFICAR" e o selo
  NÃO estampa 'evitar' (D-04), sem tocar selo.py.
- ANTI-PETRÓLEO: PETR4-like (eh_concessionaria=True + setor petróleo) NÃO vira regulada.
- DEGRADAÇÃO: CompanyData de 1 ano não levanta e popula o arquétipo.
- FRONTEIRIÇO PELO FUNIL (ARQ-02): sinais em conflito expõem fronteirico via analisar_acao.

Tudo offline: fixtures sintéticas, nenhuma chamada de rede.
"""

import os

import yaml

from analista.core import arquetipo as arq_mod
from analista.core import lentes
from analista.core.fundamentals import CompanyData
from analista.report import report
from analista.report import selo as selo_mod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _regulada_solida(ticker="REG3") -> CompanyData:
    """Utility regulada sólida (espelha _empresa_solida) — DDM roda e dá veredito direcional."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Regulada Sólida", setor="Energia Elétrica",
                    anos=anos, eh_concessionaria=True)
    for a in anos:
        c.lucro_liquido[a] = 1000 + (a - 2015) * 50
        c.patrimonio_liquido[a] = 4000 + (a - 2015) * 100
        c.dividendos[a] = 600 + (a - 2015) * 30
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 1800
        c.fco[a] = 1200
    c.preco_atual = 30.0
    c.beta = 0.8
    return c


def _financeira(ticker="BANK3") -> CompanyData:
    """Banco (setor financeiro) — hard-route financeira, motor RIM só na Fase 2 (pendente)."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Banco", setor="Bancos", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = 1000
        c.patrimonio_liquido[a] = 5000
        c.dividendos[a] = 300
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 4000
        c.fco[a] = 1200
    c.preco_atual = 70.0
    c.beta = 0.9
    return c


def _petroleo_compounder(ticker="PETR4") -> CompanyData:
    """Petróleo marcado eh_concessionaria=True: a guarda anti-Petróleo impede regulada; os
    fundamentos (ROE alto + retenção alta) roteiam crescimento — motor pendente na Fase 1."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Petróleo", setor="Petróleo e Gás",
                    anos=anos, eh_concessionaria=True)
    for i, a in enumerate(anos):
        lucro = round(1000 * (1.03 ** i))
        c.lucro_liquido[a] = lucro
        c.patrimonio_liquido[a] = 5000
        c.dividendos[a] = round(0.20 * lucro)   # payout 20% → retenção 80%
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = lucro * 4
        c.fco[a] = lucro * 1.2
    c.preco_atual = 20.0
    c.beta = 1.1
    return c


def _fronteirico(ticker="FRON3") -> CompanyData:
    """Setor não-financeiro e não-regulado, com sinais em CONFLITO: lucro oscilando violento
    (CV alto → cíclica) E últimos anos altos com payout baixo (ROE alto + retenção alta →
    crescimento) → dois candidatos distintos, fronteiriço honesto (ARQ-02)."""
    lucros = [200, 1500, 100, 1800, 150, 2000, 1600, 1700, 1800, 1900]
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Fronteiriça", setor="Extração Mineral", anos=anos)
    for a, lucro in zip(anos, lucros):
        c.lucro_liquido[a] = float(lucro)
        c.patrimonio_liquido[a] = 5000.0
        c.dividendos[a] = 0.15 * float(lucro)   # payout 15% → retenção 85%
        c.num_acoes[a] = 1000.0
        c.vendas_liquidas[a] = float(lucro) * 4
    c.preco_atual = 15.0
    c.beta = 1.0
    return c


def _ciclica(ticker="CICL3") -> CompanyData:
    """Cíclica limpa: lucro oscilando com anos de prejuízo (cv → cíclica) E ROE baixo (payout
    alto → retenção baixa), de modo que crescimento NÃO dispara — candidato único cíclica →
    motor 'normalizado' (lucro médio 7–10a), sem fronteiriço."""
    lucros = [800, -200, 900, 300, 1000, -100, 850, 400, 950, 500]
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Cíclica", setor="Extração Mineral", anos=anos)
    for a, lucro in zip(anos, lucros):
        c.lucro_liquido[a] = float(lucro)
        c.patrimonio_liquido[a] = 5000.0
        c.dividendos[a] = 0.30 * abs(float(lucro))   # payout alto → retenção baixa
        c.num_acoes[a] = 1000.0
        c.vendas_liquidas[a] = abs(float(lucro)) * 4
    c.preco_atual = 15.0
    c.beta = 1.0
    return c


def _holding(ticker="HOLD3") -> CompanyData:
    """Holding sintética (participações). O classificador da Fase 1 ainda não emite a chave
    'holding' (é escopo ARQ futuro); o roteamento é forçado via monkeypatch no anchor para
    validar o DISPATCH do motor NAV ponta-a-ponta (ENG-05)."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Holding", setor="Holdings", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = 500.0
        c.patrimonio_liquido[a] = 8000.0
        c.dividendos[a] = 200.0
        c.num_acoes[a] = 1000.0
        c.vendas_liquidas[a] = 1000.0
        c.fco[a] = 600.0
    c.preco_atual = 10.0
    c.beta = 0.7
    return c


# --- (a) REGULADA — motor ddm, veredito NÃO suspenso (ENG-06) ------------------ #
def test_regulada_mantem_motor_ddm_e_veredito_ddm():
    a = report.analisar_acao(_regulada_solida(), _cfg())
    assert a.arquetipo == "pagadora_regulada"
    assert a.motor == "ddm"
    assert a.motor_pendente is False
    assert a.arquetipo_fronteirico is False
    # O veredito NÃO é suspenso por roteamento (mantém o prefixo DDM — TAEE11 idêntica).
    assert not a.veredito.startswith("VERIFICAR")
    assert a.veredito  # DDM rodou e produziu veredito direcional


# --- (b) FINANCEIRA — motor RIM plugado → veredito suspenso, selo sem 'evitar' (D-06) --- #
def test_financeira_suspende_veredito_e_nao_estampa_evitar():
    cfg = _cfg()
    a = report.analisar_acao(_financeira(), cfg)
    assert a.arquetipo == "financeira"
    # Fase 2: o motor RIM está PLUGADO (não mais None); a suspensão migrou de motor_pendente
    # para motor != "ddm" (D-06) — o veredito segue "VERIFICAR", NÃO regride para "evitar".
    assert a.motor == "rim"
    assert a.veredito.startswith("VERIFICAR")
    # O selo sobre o veredito suspenso marca verificar=True e NÃO estampa faixa/rótulo
    # (não vira 'evitar'), via prefixo "VERIFICAR" reusado — sem tocar selo.py.
    s = selo_mod.montar_selo(70.0, a.veredito, cfg)
    assert s.verificar is True
    assert s.rotulo is None
    # A suspensão adiciona um alerta explicando o porquê (D-06).
    assert any("suspenso" in al.lower() for al in a.alertas)


# --- (c) ANTI-PETRÓLEO — não vira regulada mesmo com eh_concessionaria=True ------ #
def test_petroleo_nao_vira_pagadora_regulada():
    a = report.analisar_acao(_petroleo_compounder(), _cfg())
    assert a.arquetipo != "pagadora_regulada"
    # Fase 2: petróleo-compounder roteia para crescimento (dcf) ou cíclica (normalizado) —
    # em ambos o motor != "ddm", então o veredito segue suspenso (D-06).
    assert a.motor in {"dcf", "normalizado"}


# --- (d) DEGRADAÇÃO — 1 ano, não levanta, popula o arquétipo -------------------- #
def test_degradacao_um_ano_nao_levanta():
    c = CompanyData(ticker="VAZIA3", anos=[2024])
    c.preco_atual = 10.0
    a = report.analisar_acao(c, _cfg())   # não deve levantar
    assert a.arquetipo  # populado (default degradado pagadora_regulada)
    assert a.motor_pendente is False       # default regulada tem motor ddm


# --- (e) FRONTEIRIÇO PELO FUNIL (ARQ-02) --------------------------------------- #
def test_fronteirico_via_funil_expoe_conflito():
    a = report.analisar_acao(_fronteirico(), _cfg())
    assert a.arquetipo_fronteirico is True
    assert len(a.arquetipo_candidatos) >= 2


# --- Render mínimo (D-04): cabeçalho exibe "Arquétipo → motor" ----------------- #
def test_render_exibe_arquetipo_e_motor():
    c = _regulada_solida()
    cfg = _cfg()
    a = report.analisar_acao(c, cfg)
    md = report.relatorio_markdown(c, a, cfg)
    assert "Arquétipo:" in md
    assert "→ motor" in md


# =========================================================================== #
# Fase 2 v2.2 — anchors e2e por motor (roteamento + intrínseco do motor, D-06)
# =========================================================================== #

# --- Financeira (RIM): motor plugado, RIM destrava vs DDM, veredito segue VERIFICAR --- #
def test_financeira_rim_destrava_vs_ddm_e_segue_verificar():
    cfg = _cfg()
    c = _financeira()
    a = report.analisar_acao(c, cfg)
    ult = c.ultimo_ano()
    assert a.motor == "rim"
    assert a.intrinseco_motor is not None and a.intrinseco_motor > 0
    # (a) RIM excede o VPA (ROE > Ke → excesso positivo, estrutural).
    vpa = lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))
    assert a.intrinseco_motor > vpa
    # (b) RIM materialmente acima da referência DDM ao vivo da PRÓPRIA fixture (comparação
    # RELATIVA, robusta ao ke_rim real — não hardcoda piso absoluto R$25/28, checker Warning 1).
    ddm_ref = (a.vmin + a.vmax) / 2 if (a.vmin is not None and a.vmax is not None) \
        else (a.ddm_h.valor_intrinseco if a.ddm_h else None)
    assert ddm_ref is not None
    assert a.intrinseco_motor > 1.3 * ddm_ref
    # (c) D-06: suspenso mesmo com o motor plugado (selo não consome RIM até a Fase 3).
    assert a.veredito.startswith("VERIFICAR")
    assert selo_mod.montar_selo(70.0, a.veredito, cfg).rotulo is None


# --- Cíclica (lucro normalizado): motor 'normalizado', intrínseco populado ------ #
def test_ciclica_roteia_lucro_normalizado():
    cfg = _cfg()
    a = report.analisar_acao(_ciclica(), cfg)
    assert a.motor == "normalizado"
    assert a.intrinseco_motor is not None and a.intrinseco_motor > 0
    assert a.veredito.startswith("VERIFICAR")


# --- Crescimento (DCF): motor 'dcf', intrínseco positivo e finito (não zero/lixo) --- #
def test_crescimento_roteia_dcf_positivo_finito():
    import math
    cfg = _cfg()
    a = report.analisar_acao(_petroleo_compounder(), cfg)
    assert a.motor == "dcf"
    assert a.intrinseco_motor is not None
    assert a.intrinseco_motor > 0 and math.isfinite(a.intrinseco_motor)
    assert a.veredito.startswith("VERIFICAR")


# --- Holding (NAV): motor 'nav', intrínseco == VPA do ano-base (dispatch forçado) --- #
def test_holding_roteia_nav_igual_vpa(monkeypatch):
    cfg = _cfg()
    c = _holding()
    # O classificador ainda não emite 'holding'; força a rota para validar o dispatch NAV e2e.
    monkeypatch.setattr(
        arq_mod, "classificar",
        lambda c, cfg: arq_mod.ResultadoArquetipo(arq_mod.HOLDING),
    )
    a = report.analisar_acao(c, cfg)
    ult = c.ultimo_ano()
    assert a.motor == "nav"
    assert a.intrinseco_motor == lentes.vpa(
        c.patrimonio_liquido.get(ult), c.num_acoes.get(ult)
    )
    assert a.veredito.startswith("VERIFICAR")


# --- Regulada (DDM, NÃO suspenso): reafirma ENG-06 preservado ------------------- #
def test_regulada_ddm_nao_suspenso_eng06():
    a = report.analisar_acao(_regulada_solida(), _cfg())
    assert a.motor == "ddm"
    assert not a.veredito.startswith("VERIFICAR")


# --- Render (D-06): intrínseco do motor como referência primária + DDM rebaixado - #
def test_render_financeira_exibe_motor_e_ddm_como_lente():
    cfg = _cfg()
    c = _financeira()
    a = report.analisar_acao(c, cfg)
    md = report.relatorio_markdown(c, a, cfg)
    assert "motor do arquétipo" in md          # linha do intrínseco do motor (referência primária)
    assert "lente conservadora" in md          # DDM rebaixado onde motor != "ddm"
