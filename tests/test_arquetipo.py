"""Golden do classificador de arquétipo (core/arquetipo.py) — Fase 1 v2.2, ARQ-01/ARQ-02.

Trava a árvore de decisão híbrida (D-01/D-02):
- HARD-ROUTE por setor: banco/seguradora → financeira; concessionária (não-petróleo) → pagadora_regulada;
- REFINO quantitativo para o resto: CV do lucro → cíclica; ROE alto + retenção alta → crescimento;
- guarda anti-Petróleo (Pitfall 1) e degradação graciosa sob sinais None (Pitfall 2);
- conflito real de sinais → fronteiriço honesto (ARQ-02).

Tudo offline: fixtures sintéticas de 10 anos, nenhuma chamada de rede.
"""

import os

import yaml

from analista.core.arquetipo import (
    ARQUETIPO_MOTOR,
    CICLICA,
    CRESCIMENTO,
    FINANCEIRA,
    PAGADORA_REGULADA,
    classificar,
)
from analista.core.fundamentals import CompanyData

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _empresa(ticker, setor, lucros, *, payout=0.30, pl=5000.0,
             eh_concessionaria=False, anos_ini=2015):
    """Constrói CompanyData de N anos a partir de uma lista de lucros.

    dividendos = payout * lucro (payout-alvo constante); PL fixo (ROE ~ lucro/PL)."""
    anos = list(range(anos_ini, anos_ini + len(lucros)))
    c = CompanyData(ticker=ticker, nome=ticker, setor=setor, anos=anos,
                    eh_concessionaria=eh_concessionaria)
    for a, lucro in zip(anos, lucros):
        c.lucro_liquido[a] = float(lucro)
        c.patrimonio_liquido[a] = float(pl)
        c.dividendos[a] = float(payout) * float(lucro)
        c.num_acoes[a] = 1000.0
        c.vendas_liquidas[a] = float(lucro) * 4
    return c


# --- HARD-ROUTE por setor (financeira soberana) ------------------------------- #

def test_banco_vira_financeira():
    c = _empresa("BANK3", "Bancos", [1000] * 10)
    r = classificar(c, _cfg())
    assert r.chave == FINANCEIRA
    assert r.confianca == "alta"
    assert r.fronteirico is False


def test_seguradora_vira_financeira():
    c = _empresa("SEG3", "Previdência e Seguros / Seguradoras", [800] * 10)
    r = classificar(c, _cfg())
    assert r.chave == FINANCEIRA


def test_financeira_hard_route_soberana_ignora_quantitativo():
    # Mesmo com lucro oscilante violento (sinal de cíclica), setor financeiro crava.
    c = _empresa("BANK4", "Intermediação Financeira", [1000, 100, 1500, 90, 1400, 80, 1300, 120, 1500, 90])
    r = classificar(c, _cfg())
    assert r.chave == FINANCEIRA
    assert r.fronteirico is False


# --- HARD-ROUTE regulada + guarda anti-Petróleo ------------------------------- #

def test_concessionaria_vira_pagadora_regulada():
    c = _empresa("TAEE11", "Energia Elétrica", [1000] * 10, eh_concessionaria=True)
    r = classificar(c, _cfg())
    assert r.chave == PAGADORA_REGULADA
    assert r.confianca == "alta"
    assert ARQUETIPO_MOTOR[r.chave] == "ddm"


def test_petroleo_concessionaria_nao_vira_pagadora_regulada():
    # Guarda anti-Petróleo (Pitfall 1): 'Gás' ⊂ 'Petróleo e Gás' dispara eh_concessionaria falso-positivo.
    c = _empresa("PETR4", "Petróleo e Gás", [1000] * 10, eh_concessionaria=True)
    r = classificar(c, _cfg())
    assert r.chave != PAGADORA_REGULADA


# --- REFINO quantitativo ------------------------------------------------------ #

def test_lucro_oscilante_vira_ciclica():
    # CV do lucro cru >= 0.40; payout alto (retenção baixa) impede candidato crescimento.
    lucros = [1000, 100, 1200, 150, 1400, 80, 1300, 120, 1500, 90]
    c = _empresa("CICL3", "Siderurgia e Metalurgia", lucros, payout=0.80, pl=8000.0)
    r = classificar(c, _cfg())
    assert CICLICA in r.candidatos
    assert r.chave == CICLICA


def test_roe_alto_retencao_alta_vira_crescimento():
    # Série estável (CV baixo), ROE de valuation alto e payout baixo → compounder.
    lucros = [round(1000 * (1.03 ** i)) for i in range(10)]
    c = _empresa("GROW3", "Software", lucros, payout=0.20, pl=5000.0)
    r = classificar(c, _cfg())
    assert r.chave == CRESCIMENTO
    assert r.fronteirico is False


def test_compounder_realista_wege_vira_crescimento():
    # Réplica de compounder REAL (WEGE3-shape): crescimento composto forte e MONOTÔNICO
    # (>=15%/ano por 10 anos), payout baixo (retenção alta) e ROE de valuation ~0.25
    # (WEGE3 real ≈0.258). A tendência de alta domina o CV do lucro CRU (~0.46 > 0.40),
    # que hoje faz o compounder cair falsamente em 'ciclica' com fronteiriço (Gap 1 / CR-01
    # da 01-VERIFICATION.md). Um sinal de ciclicidade correto mede a OSCILAÇÃO detrended, não
    # o nível bruto: retornos ano-a-ano quase constantes → NÃO cíclica → crescimento limpo.
    lucros = [round(1000 * (1.18 ** i)) for i in range(10)]
    c = _empresa("WEGE3", "Máquinas e Equipamentos", lucros, payout=0.20, pl=15000.0)
    r = classificar(c, _cfg())
    assert r.chave == CRESCIMENTO
    assert r.fronteirico is False
    assert CICLICA not in r.candidatos


# --- Fronteiriço honesto (ARQ-02) --------------------------------------------- #

def test_conflito_de_sinais_marca_fronteirico():
    # Oscilação violenta (CV alto → cíclica) + últimos anos altos com payout baixo
    # (ROE alto + retenção alta → crescimento): dois candidatos distintos.
    lucros = [200, 1500, 100, 1800, 150, 2000, 1600, 1700, 1800, 1900]
    c = _empresa("FRON3", "Química", lucros, payout=0.15, pl=5000.0)
    r = classificar(c, _cfg())
    assert r.fronteirico is True
    assert len(r.candidatos) >= 2
    assert len(set(r.candidatos)) >= 2
    assert r.confianca == "baixa"


# --- Degradação graciosa (Pitfall 2 / T-01-01) -------------------------------- #

def test_sinais_none_degrada_sem_typeerror():
    c = CompanyData(ticker="VAZIA3", anos=[2024])
    r = classificar(c, _cfg())  # não deve levantar
    assert isinstance(r.chave, str)
    assert r.chave in ARQUETIPO_MOTOR


def test_bloco_config_ausente_nao_quebra():
    # T-01-02: sem bloco arquetipo: o classificador degrada por defaults, nunca KeyError.
    c = _empresa("BANK5", "Bancos", [1000] * 10)
    r = classificar(c, {})  # não deve levantar
    assert r.chave in ARQUETIPO_MOTOR
