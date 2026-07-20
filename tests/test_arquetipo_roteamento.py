"""Golden e2e do roteamento por arquétipo PLUGADO no funil (Fase 1 v2.2, ARQ-01/ENG-01/D-04).

Ao contrário de test_arquetipo.py (que trava o classificador PURO), aqui o contrato é
ponta-a-ponta via `report.analisar_acao`: o roteamento vira comportamento observável no
veredito e no render.

- REGULADA (motor ddm): TAEE11-like idêntica — veredito DDM, NÃO suspenso (ENG-06).
- FINANCEIRA (motor RIM): ITUB4-like — a partir da Fase 3 (VER-01) o selo CONSOME o motor,
  o veredito é REAL (banda do ensemble motor×contraponto), NÃO mais suspenso via "VERIFICAR",
  e o selo estampa faixa/rótulo honesto (Alta×faixa), nunca 'evitar' pelo DDM.
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


# --- (b) FINANCEIRA — motor RIM alimenta o veredito (VER-01), selo consome o motor, nunca 'evitar' --- #
def test_financeira_veredito_real_do_motor_nunca_evitar():
    cfg = _cfg()
    a = report.analisar_acao(_financeira(), cfg)
    assert a.arquetipo == "financeira"
    # ENG-01 (Fase 13): financeira roda o RIM ÚNICO (a.motor == "rim"). O veredito de preço é
    # REAL (SUB/NO INTERVALO/SOBRE sobre a região da MS), não mais suspenso via "VERIFICAR".
    assert a.motor == "rim"
    assert a.intrinseco_motor is not None and a.intrinseco_motor > 0
    assert a.veredito.startswith(("SUBAVALIADA", "NO INTERVALO", "SOBREAVALIADA"))
    # O selo CONSOME o motor: faixa/rótulo derivados do veredito, NUNCA o 'Evitar' que o DDM
    # sozinho produziria (o erro de arquitetura do ITUB4 domado pelo RIM).
    s = selo_mod.montar_selo(70.0, a.veredito, cfg)   # bsd 70 → verde → qualidade Alta
    assert s.rotulo != "Evitar"
    assert s.faixa_preco == selo_mod.faixa_do_veredito(a.veredito)


# --- (c) ANTI-PETRÓLEO — não vira regulada mesmo com eh_concessionaria=True ------ #
def test_petroleo_nao_vira_concessao_finita():
    a = report.analisar_acao(_petroleo_compounder(), _cfg())
    # A guarda anti-Petróleo impede a rota de concessão mesmo com eh_concessionaria=True.
    assert a.arquetipo != "concessao_finita"
    # ENG-01 (Fase 13): qualquer que seja o arquétipo do refino, roda o RIM único.
    assert a.motor == "rim"


# --- (d) DEGRADAÇÃO — 1 ano, não levanta, popula o arquétipo -------------------- #
def test_degradacao_um_ano_nao_levanta():
    c = CompanyData(ticker="VAZIA3", anos=[2024])
    c.preco_atual = 10.0
    a = report.analisar_acao(c, _cfg())   # não deve levantar (never-raise, SAN-06)
    assert a.arquetipo          # populado (default degradado por eliminação)
    assert a.motor == "rim"     # ENG-01: caminho único de valor


# --- Render mínimo (D-04): cabeçalho exibe "Arquétipo → motor" ----------------- #
def test_render_exibe_arquetipo_e_motor():
    c = _regulada_solida()
    cfg = _cfg()
    a = report.analisar_acao(c, cfg)
    md = report.relatorio_markdown(c, a, cfg)
    assert "Arquétipo:" in md
    assert "→ motor" in md


# --- Render limpo fora do fronteiriço: nenhum bloco de classificação incerta --- #
def test_render_nao_fronteirico_sem_bloco_incerto():
    cfg = _cfg()
    c = _regulada_solida()
    a = report.analisar_acao(c, cfg)
    md = report.relatorio_markdown(c, a, cfg)
    assert "Classificação incerta (caso-fronteira)" not in md
