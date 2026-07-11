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


# --- (b) FINANCEIRA — motor pendente → veredito suspenso, selo sem 'evitar' (D-04) --- #
def test_financeira_suspende_veredito_e_nao_estampa_evitar():
    cfg = _cfg()
    a = report.analisar_acao(_financeira(), cfg)
    assert a.arquetipo == "financeira"
    assert a.motor_pendente is True
    assert a.veredito.startswith("VERIFICAR")
    # O selo sobre o veredito suspenso marca verificar=True e NÃO estampa faixa/rótulo
    # (não vira 'evitar'), via prefixo "VERIFICAR" reusado — sem tocar selo.py.
    s = selo_mod.montar_selo(70.0, a.veredito, cfg)
    assert s.verificar is True
    assert s.rotulo is None
    # A suspensão adiciona um alerta explicando o porquê (D-04).
    assert any("motor pendente" in al.lower() for al in a.alertas)


# --- (c) ANTI-PETRÓLEO — não vira regulada mesmo com eh_concessionaria=True ------ #
def test_petroleo_nao_vira_pagadora_regulada():
    a = report.analisar_acao(_petroleo_compounder(), _cfg())
    assert a.arquetipo != "pagadora_regulada"
    assert a.motor_pendente is True


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
