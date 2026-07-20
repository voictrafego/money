"""Classificador de arquétipo de negócio — coração do roteamento por motor (v2.2, ARQ-01/ARQ-02).

O erro do ITUB4 é de ARQUITETURA, não de fórmula: aplicar um único motor primário
(DDM de estágio único) a todo negócio carimba compounders de qualidade como "evitar".
Antes de valuar é preciso saber QUE tipo de negócio é a empresa e rotear ao motor certo.

Esta camada é PURA (espelha `lifecycle.py`): uma função `classificar(c, cfg)` que lê apenas
sinais que `CompanyData` já expõe (setor, eh_concessionaria, roe_valuation, payout_valuation,
série de lucro) — NUNCA recalcula método — e decide entre 5 chaves de arquétipo. Isolá-la em
`core/` mantém a engine testável por golden e a consistência cross-modo (mesma fonte de sinais
que Analisar/Ranking).

Roteamento HÍBRIDO (D-01/D-02): setores fortes (banco/seguradora/regulada) fazem hard-route
soberano por setor; todo o resto passa pelo refino quantitativo (ROE/retenção/oscilação do
lucro). Quando há conflito real de sinais (>= 2 candidatos distintos) o resultado é honesto:
marca `fronteirico=True` com 2-3 candidatos em vez de fingir certeza (fallback honesto).

Thresholds são config-driven (`cfg["arquetipo"]`); calibração empírica é BACKTEST-01 (deferida).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from math import log
from statistics import pstdev
from typing import List, Optional

# Ano de prejuízo (lucro <= 0) torna o ajuste log-linear indefinido (log de ≤0). Um ano de
# prejuízo é, por si só, evidência CÍCLICA forte (o método não trata quem dá prejuízo como
# compounder de dividendos). Em vez de descartar em silêncio, `_cv_lucro` devolve este
# sinal-sentinela, garantido ACIMA de qualquer `ciclica_cv_min` razoável (cíclicas reais
# medem 0.49-1.24 na escala de resíduos; o corte fica ~0.35). Precede o guard de <3 pontos.
_SINAL_PREJUIZO_CICLICO = 10.0

# Chaves de arquétipo, 1:1 com a política de derivação de ROE-âncora (D-01/D-03/ENG-03) - #
# O antigo rótulo regulada foi CINDIDO em dois herdeiros (D-05): PAGADORA_MADURA (o novo
# default-por-eliminação — empresa sem sinal roda RIM normal, não mais o balde da transmissora)
# e CONCESSAO_FINITA (o hard-route de `eh_concessionaria`, carve-out declarado ANTES do hold-out
# — a mecânica do g é o Plano 03). A string do rótulo antigo deixa de ser devolvida.
FINANCEIRA = "financeira"            # banco/seguradora → RIM
PAGADORA_MADURA = "pagadora_madura"  # madura sem sinal (default por eliminação) → RIM normal
CONCESSAO_FINITA = "concessao_finita"  # concessão de vida finita (transmissora/saneamento) → RIM carve-out
CICLICA = "ciclica"                  # lucro oscilante → lucro normalizado
CRESCIMENTO = "crescimento"          # ROE alto + retenção → DCF multi-estágio (compounder)
HOLDING = "holding"                  # participações → NAV/SOTP (stretch)

# Registry arquétipo → POLÍTICA de derivação de ROE-âncora (ENG-03, §"Mapa de âncoras"). É o
# mapa que o RIM único (Plano 03) consome para derivar o roe0-âncora com erro limitado. Os
# valores são strings de POLÍTICA (não ids de motor): CONCESSAO_FINITA usa "through_cycle_sem_g"
# (o carve-out; a mecânica do g_terminal=None fica no Plano 03).
ARQUETIPO_ANCORA_ROE = {
    FINANCEIRA: "through_cycle",
    PAGADORA_MADURA: "through_cycle",
    CONCESSAO_FINITA: "through_cycle_sem_g",
    CICLICA: "normalizado",
    CRESCIMENTO: "atual_fade",
    HOLDING: "nav_piso",
}

@dataclass
class ResultadoArquetipo:
    """Veredito do classificador. `chave` é a rota primária; `fronteirico`/`candidatos`
    carregam a dúvida honesta em conflito de sinais; `sinais` guarda os números crus
    (roe/retencao/cv_lucro) para debug e para a Fase 3 exibir o porquê da rota."""

    chave: str
    fronteirico: bool = False
    candidatos: List[str] = field(default_factory=list)
    confianca: str = "alta"
    sinais: dict = field(default_factory=dict)


def _cv_lucro(serie: list) -> Optional[float]:
    """Sinal de ciclicidade: dispersão dos RESÍDUOS de um ajuste log-linear do lucro (CR-01).

    O desvio da TENDÊNCIA — não a variância da TAXA de crescimento — é o sinal de cíclica.
    O sinal antigo (CV dos retornos ano-a-ano) penalizava compounders reais de crescimento
    DESIGUAL (WEGE3 real: retornos de -3% a +53% → CV≈0.80) da mesma forma que uma cíclica
    genuína, misrouteando-os para 'ciclica' (Gap 1 / 01-VERIFICATION.md). Ajustamos ln(lucro)
    ~ tempo por OLS sobre os anos de lucro POSITIVO e medimos o `pstdev` dos resíduos:
    - compounder que cresce ao longo de uma reta em log (ainda que desigual) → resíduos
      pequenos, gruda na tendência → dispersão BAIXA (~0.15-0.22);
    - cíclico que oscila em torno da tendência → resíduos grandes → dispersão ALTA (~0.50+).

    ANO DE PREJUÍZO (lucro <= 0): log indefinido. Precedência EXPLÍCITA — o override de
    prejuízo (evidência cíclica forte → devolve `_SINAL_PREJUIZO_CICLICO`, acima do corte)
    PRECEDE o guard de degradação de <3 pontos: uma empresa que dá prejuízo em algum ano é
    cíclica por este método, mesmo com poucos anos positivos. Sem prejuízo e com < 3 pontos
    válidos → None (degrada gracioso para o default, Pitfall 2). Função pura, O(n), sem I/O."""
    vals = [float(v) for v in serie if v is not None]
    # Override de prejuízo (precede o guard de <3 pontos) --------------------- #
    if any(v <= 0 for v in vals):
        return _SINAL_PREJUIZO_CICLICO
    if len(vals) < 3:
        return None
    # Ajuste OLS de ln(lucro) sobre o índice de tempo; dispersão dos resíduos -- #
    pts = [(i, log(v)) for i, v in enumerate(vals)]
    n = len(pts)
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    if sxx == 0:
        return None
    b = sum((x - mx) * (y - my) for x, y in pts) / sxx
    a = my - b * mx
    residuos = [y - (a + b * x) for x, y in pts]
    return pstdev(residuos)


def _setor_casa_token(setor: str, tokens: list) -> bool:
    """Casa um token financeiro no setor por LIMITE DE PALAVRA, não substring solta (T-0106-01).

    O casamento ingênuo `tok in setor` sofre over-match: um token financeiro curto casa DENTRO
    de uma palavra não-financeira (ex.: 'banco' ⊂ 'Bancoreal'). Ancoramos em fronteira de palavra
    (`\\b`) e toleramos sufixo de plural (Bancos/Seguradoras) para NÃO afrouxar os hard-routes
    financeiros genuínos; tokens multi-palavra ('intermediação financeira') casam como frase.
    Função pura, sem I/O. `setor` já vem em minúsculas."""
    for tok in tokens:
        t = str(tok).lower().strip()
        if not t:
            continue
        if re.search(r"\b" + re.escape(t) + r"(?:s|es)?\b", setor):
            return True
    return False


def classificar(c: "CompanyData", cfg: dict) -> ResultadoArquetipo:
    """Roteia uma empresa ao seu arquétipo lendo só sinais canônicos de `CompanyData`.

    Árvore híbrida (D-01/D-02), config-driven (`cfg["arquetipo"]`, com defaults):

    1. HARD-ROUTE financeira — setor contém token financeiro → FINANCEIRA (soberano, sem
       quantitativo). O SETOR_ATIV da CVM é confiável para financeiras.
    2. HARD-ROUTE concessão — `eh_concessionaria` E setor NÃO contém token de exclusão
       (guarda anti-Petróleo OBRIGATÓRIA) → CONCESSAO_FINITA (carve-out).
    3. REFINO quantitativo p/ todo o resto — dispersão dos resíduos do ajuste log-linear do
       lucro (ou prejuízo na janela) >= corte → cíclica; ROE alto E retenção alta →
       crescimento; nenhum → PAGADORA_MADURA (default maduro por eliminação).
    4. CONFLITO — >= 2 candidatos distintos → fronteiriço honesto (confiança baixa).

    Cada sinal é guardado com `is not None` ANTES de qualquer comparação (Pitfall 2): sob
    dados faltantes degrada para o default sem TypeError.
    """
    arq = (cfg or {}).get("arquetipo", {})
    financeiro_tokens = arq.get("financeiro_tokens", [])
    regulada_excluir = arq.get("regulada_excluir_tokens", [])
    roe_alto_min = arq.get("roe_alto_min", 0.15)
    retencao_alta_min = arq.get("retencao_alta_min", 0.50)
    ciclica_cv_min = arq.get("ciclica_cv_min", 0.35)

    setor = (c.setor or "").lower()

    # 1. HARD-ROUTE financeira (soberano) ------------------------------------- #
    # Casamento por LIMITE DE PALAVRA (não substring solta) — impede que um token financeiro
    # curto case dentro de uma palavra não-financeira (over-match; Achado 1b / T-0106-01).
    if _setor_casa_token(setor, financeiro_tokens):
        return ResultadoArquetipo(FINANCEIRA, confianca="alta")

    # 2. HARD-ROUTE regulada + guarda anti-Petróleo --------------------------- #
    # Exclusão anti-Petróleo pelo MESMO casamento por limite de palavra do hard-route financeiro
    # (IN-01): uma única estratégia consistente evita que um substring solto mis-roteie a regulada.
    if c.eh_concessionaria and not _setor_casa_token(setor, regulada_excluir):
        return ResultadoArquetipo(CONCESSAO_FINITA, confianca="alta")

    # 3. REFINO quantitativo -------------------------------------------------- #
    # ROE de QUALIDADE ATUAL (endpoint), NÃO a mediana through-cycle de roe_valuation (PRIM-02):
    # o roteamento quer saber se o ticker é HOJE um alto-ROE. A mediana subestima um compounder
    # de ROE crescente (fica no meio da subida) e o desrotearia de CRESCIMENTO — split de sinal
    # espelhando o split de estimador do PRIM-01 (Option A da Fase 10).
    roe = c.roe_qualidade_atual()
    payout = c.payout_valuation()
    retencao = (1.0 - payout) if payout is not None else None
    cv = _cv_lucro(c.serie("lucro_liquido"))
    sinais = {"roe": roe, "retencao": retencao, "cv_lucro": cv}

    candidatos: List[str] = []
    if cv is not None and cv >= ciclica_cv_min:
        candidatos.append(CICLICA)
    if (roe is not None and roe >= roe_alto_min
            and retencao is not None and retencao >= retencao_alta_min):
        candidatos.append(CRESCIMENTO)
    if not candidatos:
        candidatos.append(PAGADORA_MADURA)  # pagadora madura por eliminação (RIM normal, não o balde da transmissora)

    # 4. CONFLITO real de sinais → fronteiriço honesto (D-01) ----------------- #
    # `candidatos` sempre populado (debug/Fase 3 e must_have "inclui X nos candidatos");
    # o flag `fronteirico` é o que distingue conflito real (>= 2 distintos) de rota crava.
    distintos = list(dict.fromkeys(candidatos))
    if len(distintos) >= 2:
        return ResultadoArquetipo(distintos[0], fronteirico=True,
                                  candidatos=distintos, confianca="baixa", sinais=sinais)
    return ResultadoArquetipo(distintos[0], candidatos=distintos,
                              confianca="alta", sinais=sinais)
