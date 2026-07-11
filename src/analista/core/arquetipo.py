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
    """Coeficiente de variação da série de lucro CRU (a oscilação É o sinal de ciclicidade).

    Filtra None; None se < 3 pontos válidos (poucos dados p/ afirmar oscilação) ou média == 0
    (CV indefinido). Senão `pstdev(vals) / abs(mean(vals))` — dispersão relativa ao nível médio."""
    vals = [float(v) for v in serie if v is not None]
    if len(vals) < 3:
        return None
    m = mean(vals)
    if m == 0:
        return None
    return pstdev(vals) / abs(m)
