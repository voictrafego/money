"""Golden do classificador de arquétipo (core/arquetipo.py) — Fase 1 v2.2, ARQ-01/ARQ-02.

Trava a árvore de decisão híbrida (D-01/D-02):
- HARD-ROUTE por setor: banco/seguradora → financeira; concessionária (não-petróleo) → pagadora_regulada;
- REFINO quantitativo para o resto: CV do lucro → cíclica; ROE alto + retenção alta → crescimento;
- guarda anti-Petróleo (Pitfall 1) e degradação graciosa sob sinais None (Pitfall 2);
- conflito real de sinais → fronteiriço honesto (ARQ-02).

Tudo offline: fixtures sintéticas de 10 anos, nenhuma chamada de rede.
"""

import os

import pytest
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


# --- Séries REAIS de lucro líquido (CVM DFP, cache offline em data/cvm/) --------- #
# Congeladas como literais (determinístico, sem rede/cache no teste). Derivadas via
# `ingest.cvm.fundamentos_do_ano(cd_cvm, ano)` para os anos 2015-2023 durante o
# desenvolvimento do 01-05. Fonte empírica: 01-AUDIT-COERENCIA.md (2/setor) e
# 01-VERIFICATION.md. Substituem as progressões geométricas sintéticas (crescimento
# perfeitamente suave), que não replicam a variância de TAXA de crescimento real
# (Gap 1 / CR-01: o golden suave mascarava o misroute de WEGE3 real → ciclica).
#
# Compounders / defensivos (resid log-linear baixo — não cíclicos):
LL_WEGE3 = [1165810000, 1127832000, 1140942000, 1344148000, 1632455000,   # cd_cvm 5410
            2395957000, 3657480000, 4272872000, 5867615000]               # 2015-2023
LL_RADL3 = [339785000, 451252000, 512653000, 509313000, 788735000,        # cd_cvm 5258
            495533000, 764133000, 1014968000, 1087143000]                 # 2015-2023
LL_ABEV3 = [12879141000, 13083397000, 7850504000, 11377427000, 12188332000,  # cd_cvm 23264
            11731909000, 13122582000, 14891291000, 14960459000]              # 2015-2023
LL_LREN3 = [578838000, 625058000, 732679000, 1020136000, 1099093000,      # cd_cvm 8133
            1096269000, 633112000, 1291704000, 976259000]                 # 2015-2023
# Cíclicas genuínas (ano(s) de prejuízo na janela → evidência cíclica forte):
LL_VALE3 = [-45996622000, 13296496000, 17669992000, 25773768000, -8696040000,  # cd_cvm 4170
            24902341000, 121343000000, 96337000000, 40554000000]               # 2015-2023
LL_GGBR4 = [-4595986000, -2885929000, -338667000, 2326382000, 1216887000,  # cd_cvm 3980
            2388054000, 15558938000, 11479552000, 7536983000]              # 2015-2023
LL_SUZB3 = [-925354000, 1691998000, 1807433000, 318460000, -2814742000,    # cd_cvm 13986
            -10714935000, 8635532000, 23394887000, 14106381000]            # 2015-2023
LL_PETR4 = [-35171000000, -13045000000, 377000000, 26698000000, 40970000000,  # cd_cvm 9512
            6246000000, 107264000000, 189005000000, 125166000000]             # 2015-2023


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


def test_compounder_real_wege_vira_crescimento():
    # WEGE3 REAL (cd_cvm 5410, 2015-2023): compounder de crescimento DESIGUAL (retornos
    # ano-a-ano de -3,3% a +52,6%), não uma progressão geométrica suave. O sinal antigo
    # (CV dos retornos, ≈0.80) misrouteava para 'ciclica'/fronteiriço (Gap 1 / CR-01 /
    # 01-VERIFICATION.md), porque penalizava a variância da TAXA de crescimento. O sinal
    # correto (dispersão dos resíduos de ajuste log-linear, ≈0.174) só mede desvio da
    # TENDÊNCIA: monotônico gruda na reta → NÃO cíclica → crescimento limpo.
    c = _empresa("WEGE3", "Máquinas e Equipamentos", LL_WEGE3, payout=0.446, pl=17854776000.0)
    r = classificar(c, _cfg())
    assert r.chave == CRESCIMENTO
    assert r.fronteirico is False
    assert CICLICA not in r.candidatos


def test_compounder_real_radl_vira_crescimento():
    # RADL3 REAL (cd_cvm 5258, 2015-2023): compounder de saúde/varejo farma. Crescimento
    # desigual (queda em 2020), mas ancorado na tendência (resid log-linear ≈0.156).
    c = _empresa("RADL3", "Comércio e Distribuição", LL_RADL3, payout=0.30, pl=6028301000.0)
    r = classificar(c, _cfg())
    assert r.chave == CRESCIMENTO
    assert CICLICA not in r.candidatos


def test_ciclica_real_vale_permanece_ciclica():
    # VALE3 REAL (cd_cvm 4170): commodity com anos de prejuízo (2015, 2019) → cíclica genuína.
    c = _empresa("VALE3", "Mineração", LL_VALE3, payout=0.80, pl=198325000000.0)
    r = classificar(c, _cfg())
    assert r.chave == CICLICA


def test_ciclica_real_ggbr_com_prejuizo_permanece_ciclica():
    # GGBR4 REAL (cd_cvm 3980): siderurgia com 3 anos de prejuízo (2015-2017). Prejuízo = log
    # indefinido → tratado como evidência cíclica (override precede o guard de <3 pontos).
    c = _empresa("GGBR4", "Siderurgia e Metalurgia", LL_GGBR4, payout=0.80, pl=49238863000.0)
    r = classificar(c, _cfg())
    assert r.chave == CICLICA


# --- Golden multi-ticker: calibração travada contra AMBOS os regimes reais ----- #
# Fonte: audit empírico 2/setor (01-AUDIT-COERENCIA.md). A calibração do corte é
# validada em >=3 compounders reais e >=4 cíclicas reais (não num único ponto —
# exigência da 01-VERIFICATION.md), para que uma regressão futura do sinal ou do
# corte seja pega por golden de série REAL, não sintética.

# (ticker, setor, série real, payout, pl) — compounders/defensivos: chave != 'ciclica'.
_COMPOUNDERS_REAIS = [
    ("WEGE3", "Máquinas e Equipamentos", LL_WEGE3, 0.446, 17854776000.0),
    ("RADL3", "Comércio e Distribuição", LL_RADL3, 0.30, 6028301000.0),
    ("ABEV3", "Bebidas", LL_ABEV3, 0.90, 80143802000.0),  # defensivo (resid 0.158) — âncora limpa (NÃO TOTS3)
]

# Cíclicas reais (todas com ano(s) de prejuízo na janela): chave == 'ciclica'.
_CICLICAS_REAIS = [
    ("VALE3", "Mineração", LL_VALE3, 0.80, 198325000000.0),
    ("GGBR4", "Siderurgia e Metalurgia", LL_GGBR4, 0.80, 49238863000.0),
    ("SUZB3", "Papel e Celulose", LL_SUZB3, 0.30, 44810300000.0),
    ("PETR4", "Petróleo", LL_PETR4, 0.60, 382340000000.0),
]


@pytest.mark.parametrize("ticker,setor,lucros,payout,pl", _COMPOUNDERS_REAIS)
def test_compounder_defensivo_real_nao_vira_ciclica(ticker, setor, lucros, payout, pl):
    c = _empresa(ticker, setor, lucros, payout=payout, pl=pl)
    r = classificar(c, _cfg())
    assert r.chave != CICLICA
    assert CICLICA not in r.candidatos


@pytest.mark.parametrize("ticker,setor,lucros,payout,pl", _CICLICAS_REAIS)
def test_ciclica_real_permanece_ciclica(ticker, setor, lucros, payout, pl):
    c = _empresa(ticker, setor, lucros, payout=payout, pl=pl)
    r = classificar(c, _cfg())
    assert r.chave == CICLICA


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
