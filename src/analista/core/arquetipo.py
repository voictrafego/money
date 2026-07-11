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

from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import List, Optional

# 5 chaves de arquétipo, 1:1 com os motores primários (D-03/ENG-01) --------------- #
FINANCEIRA = "financeira"            # banco/seguradora → RIM
PAGADORA_REGULADA = "pagadora_regulada"  # transmissora/saneamento madura → DDM (já existe)
CICLICA = "ciclica"                  # lucro oscilante → lucro normalizado
CRESCIMENTO = "crescimento"          # ROE alto + retenção → DCF multi-estágio (compounder)
HOLDING = "holding"                  # participações → NAV/SOTP (stretch)

# Registry arquétipo → motor primário (ENG-01). Só pagadora_regulada tem motor nesta
# fase (DDM); os outros 4 ficam None até a Fase 2 plugar seus motores no registry.
ARQUETIPO_MOTOR = {
    FINANCEIRA: None,
    PAGADORA_REGULADA: "ddm",
    CICLICA: None,
    CRESCIMENTO: None,
    HOLDING: None,
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
    """Coeficiente de variação da OSCILAÇÃO detrended do lucro (o sinal de ciclicidade).

    A oscilação — não o nível — é o sinal de cíclica (CR-01). O CV do lucro CRU é dominado
    pela TENDÊNCIA: qualquer compounder monotônico (WEGE3-shape) tem dispersão alta só por
    subir, e seria carimbado cíclico por engano. Medimos então a dispersão dos RETORNOS
    ano-a-ano `(lucro[t] - lucro[t-1]) / |lucro[t-1]|`, que é invariante à tendência:
    - compounder monotônico → retornos ~constantes e do mesmo sinal → CV BAIXO;
    - cíclico que alterna sinal (lucro sobe e cai) → retornos oscilam de sinal, média perto
      de zero → CV ALTO.

    Filtra None; pula pontos com `lucro[t-1] == 0` (retorno indefinido). None se < 3 pontos
    válidos ou < 2 retornos calculáveis (poucos dados p/ afirmar oscilação) ou média dos
    retornos == 0 (CV indefinido). Função pura, sem I/O — O(n) sobre <=10 pontos."""
    vals = [float(v) for v in serie if v is not None]
    if len(vals) < 3:
        return None
    ret = [(b - a) / abs(a) for a, b in zip(vals, vals[1:]) if a != 0]
    if len(ret) < 2:
        return None
    m = mean(ret)
    if m == 0:
        return None
    return pstdev(ret) / abs(m)


def classificar(c: "CompanyData", cfg: dict) -> ResultadoArquetipo:
    """Roteia uma empresa ao seu arquétipo lendo só sinais canônicos de `CompanyData`.

    Árvore híbrida (D-01/D-02), config-driven (`cfg["arquetipo"]`, com defaults):

    1. HARD-ROUTE financeira — setor contém token financeiro → FINANCEIRA (soberano, sem
       quantitativo). O SETOR_ATIV da CVM é confiável para financeiras.
    2. HARD-ROUTE regulada — `eh_concessionaria` E setor NÃO contém token de exclusão
       (guarda anti-Petróleo OBRIGATÓRIA) → PAGADORA_REGULADA.
    3. REFINO quantitativo p/ todo o resto — CV da oscilação detrended do lucro (retornos
       ano-a-ano) >= corte → cíclica; ROE alto E retenção alta → crescimento; nenhum →
       pagadora_regulada (default maduro).
    4. CONFLITO — >= 2 candidatos distintos → fronteiriço honesto (confiança baixa).

    Cada sinal é guardado com `is not None` ANTES de qualquer comparação (Pitfall 2): sob
    dados faltantes degrada para o default sem TypeError.
    """
    arq = (cfg or {}).get("arquetipo", {})
    financeiro_tokens = arq.get("financeiro_tokens", [])
    regulada_excluir = arq.get("regulada_excluir_tokens", [])
    roe_alto_min = arq.get("roe_alto_min", 0.15)
    retencao_alta_min = arq.get("retencao_alta_min", 0.50)
    ciclica_cv_min = arq.get("ciclica_cv_min", 0.40)

    setor = (c.setor or "").lower()

    # 1. HARD-ROUTE financeira (soberano) ------------------------------------- #
    if any(tok.lower() in setor for tok in financeiro_tokens):
        return ResultadoArquetipo(FINANCEIRA, confianca="alta")

    # 2. HARD-ROUTE regulada + guarda anti-Petróleo --------------------------- #
    if c.eh_concessionaria and not any(tok.lower() in setor for tok in regulada_excluir):
        return ResultadoArquetipo(PAGADORA_REGULADA, confianca="alta")

    # 3. REFINO quantitativo -------------------------------------------------- #
    roe = c.roe_valuation()
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
        candidatos.append(PAGADORA_REGULADA)  # pagadora madura por eliminação

    # 4. CONFLITO real de sinais → fronteiriço honesto (D-01) ----------------- #
    # `candidatos` sempre populado (debug/Fase 3 e must_have "inclui X nos candidatos");
    # o flag `fronteirico` é o que distingue conflito real (>= 2 distintos) de rota crava.
    distintos = list(dict.fromkeys(candidatos))
    if len(distintos) >= 2:
        return ResultadoArquetipo(distintos[0], fronteirico=True,
                                  candidatos=distintos, confianca="baixa", sinais=sinais)
    return ResultadoArquetipo(distintos[0], candidatos=distintos,
                              confianca="alta", sinais=sinais)
