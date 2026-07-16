"""Normalização de lucro para o valuation (FIX-04 — raiz da cascata VULC3).

O lucro CVM cru de UM exercício atípico (recuperação de créditos fiscais, distribuição
extraordinária) contamina ROE, CAGR, LPA, payout e DY do valuation. Esta camada entrega
a base de lucro *robusta* — o número-síntese que o valuation deve consumir no lugar do
`lucro_liquido.get(ult)` cru.

Espírito do livro (BSD, Cap. 8.4): o Big, Safe Dividend já usa médias trienais +
winsorização a 10%. Reaproveitamos esse espírito como base de qualidade do valuation.

**Primitiva pura:** recebe sequências de números (podendo conter None) + a janela/winsor
de config e devolve número(s). NÃO importa nada da engine de fundamentos/relatório
(sem ciclo de import) — só numpy/statistics/scipy.

Dois estimadores DIVIDIDOS de propósito (PRIM-01 / RESEARCH §Estimator split) — os dois
consumidores da base querem estimadores OPOSTOS:

  - `base_normalizada` (base de VALUATION, janela curta) = **ENDPOINT de tendência robusta
    (Theil-Sen)** avaliado no ano atual. Reflete o crescimento recente e é robusto a UM
    exercício atípico — sem o haircut -g/(1+g) que a mediana-do-meio impunha (BLIND-03).
    Ladder curta (D-01b): vazio -> None; N==1 -> valor; N==2 -> média dos dois. GUARD de
    degeneração: endpoint <= 0 (prejuízo recente) -> median(janela). O guard só remove o
    ARTEFATO de extrapolação negativa do endpoint (a reta Theil-Sen projetada para baixo do
    zero num ano ruim); NÃO é um clamp de não-negatividade — uma janela majoritariamente
    deficitária tem median(janela) < 0 e a base sai negativa POR DESIGN (empresa em prejuízo
    estrutural). Os consumidores a jusante toleram (Gordon/DCF degradam, a camada de
    relatório guarda `intrinseco <= 0`); quem exige base > 0 clampa no seu lado.
  - `media_ciclo` (motor CÍCLICO, janela longa) = a **média/mediana through-cycle** ANTIGA.
    Uma cíclica com prejuízo recente vale pela força de lucro do MEIO do ciclo, não pelo
    endpoint (que seria negativo). N >= 5 -> média winsorizada; 2<=N<5 -> mediana; N==1 ->
    valor; N==0 -> None.
"""

from __future__ import annotations

from statistics import median
from typing import List, Optional, Sequence

import numpy as np
from scipy.stats import theilslopes

Number = Optional[float]


def _limpar(valores: Sequence[Number]) -> List[float]:
    """Descarta os None (não contam como 0) e converte para float."""
    return [float(v) for v in valores if v is not None]


def media_winsorizada(valores: Sequence[Number], winsor: float = 0.10) -> Number:
    """Média winsorizada a `winsor` nos extremos (valores fora dos percentis são clampados).

    < 5 pontos válidos: degrada para mediana (winsor não morde poucos pontos);
    1 ponto: o próprio valor; vazio: None.
    """
    limpos = _limpar(valores)
    if not limpos:
        return None
    if len(limpos) == 1:
        return limpos[0]
    if len(limpos) < 5:
        return float(median(limpos))
    lo = float(np.percentile(limpos, winsor * 100))
    hi = float(np.percentile(limpos, (1.0 - winsor) * 100))
    clamp = [min(max(v, lo), hi) for v in limpos]
    return float(sum(clamp) / len(clamp))


def base_normalizada(
    valores: Sequence[Number], anos_media: int = 3, winsor: float = 0.10
) -> Number:
    """Base de lucro de VALUATION = ENDPOINT de tendência robusta (Theil-Sen) no ano atual.

    Número-síntese ÚNICO de qualidade que alimenta `roe_valuation`/`lpa_valuation` (PRIM-01).
    Substitui o `median()`-de-N (o ano-do-meio, que PUNIA crescimento pelo haircut fechado
    -g/(1+g)) pelo valor da tendência robusta AVALIADA NO ANO ATUAL — reflete o crescimento
    recente e é robusto a UM exercício atípico (Theil-Sen ignora o outlier na janela).

    Ladder de série curta (D-01b): vazio -> None; N==1 -> o próprio valor; N==2 -> média dos
    dois (Theil-Sen degenera com 2 pontos). GUARD de degeneração: se o endpoint <= 0 (série
    de prejuízo recente) degrada para median(janela). CONTRATO REAL do guard: ele elimina o
    ARTEFATO específico da extrapolação — a reta robusta projetada ABAIXO de zero no ano atual
    por causa de um exercício ruim — devolvendo a mediana da janela no lugar. NÃO é um clamp de
    não-negatividade: numa janela majoritariamente deficitária a própria median(janela) é
    negativa, e a base sai negativa POR DESIGN (a empresa realmente teve prejuízo no ciclo).
    RIM/DCF a jusante degradam sem levantar (Gordon/DCF caem, a camada de relatório guarda
    `intrinseco <= 0`); consumidores que exigem base estritamente positiva devem clampar no
    próprio lado.

    `winsor` permanece na assinatura por integridade do orçamento de knobs (inerte aqui —
    é consumido por `media_ciclo`). `anos_media` é a janela do Theil-Sen.
    """
    limpos = _limpar(valores)
    if not limpos:
        return None
    janela = limpos[-anos_media:] if anos_media else limpos
    n = len(janela)
    if n == 1:
        return janela[0]
    if n == 2:
        return float(sum(janela) / 2.0)
    slope, intercept, *_ = theilslopes(janela, np.arange(n))
    endpoint = intercept + slope * (n - 1)
    if endpoint <= 0:
        return float(median(janela))
    return float(endpoint)


def media_ciclo(
    valores: Sequence[Number], anos_media: int = 10, winsor: float = 0.10
) -> Number:
    """Força de lucro do MEIO do ciclo (motor cíclico) = média/mediana through-cycle.

    É o estimador que o motor `lucro_normalizado` (`anos_media=10`) precisa — a média
    through-cycle, robusta a UM ano de prejuízo recente. NÃO usa o endpoint de tendência
    (esse é `base_normalizada`, para a base de valuation de janela curta): numa cíclica com
    prejuízo recente o endpoint seria negativo, mas a força de lucro do ciclo é positiva.

    É EXATAMENTE a ladder que `base_normalizada` tinha antes do PRIM-01 (a divisão do
    estimador): vazio -> None; N==1 -> valor; 2<=N<5 -> mediana; N>=5 -> média winsorizada.
    """
    limpos = _limpar(valores)
    if not limpos:
        return None
    janela = limpos[-anos_media:] if anos_media else limpos
    n = len(janela)
    if n == 1:
        return janela[0]
    if n < 5:
        return float(median(janela))
    return media_winsorizada(janela, winsor)


def mediana_payout(valores: Sequence[Number]) -> Number:
    """Payout sustentável: mediana do payout sobre a série histórica COMPLETA (PAY-01).

    "Extraordinário" = desvio do PRÓPRIO histórico, capturado pela mediana sobre TODOS
    os anos válidos (sem janela de 3a, D-04). SEM clamp em 1.0 (D-03): a mediana pode
    ser legitimamente >100% — transmissora que distribui de caixa regulatório acima do
    lucro contábil (TAEE11 ≈ 2.16). Vazio/só-None -> None; 1 ano -> o próprio valor.
    """
    limpos = _limpar(valores)
    if not limpos:
        return None
    if len(limpos) == 1:
        return limpos[0]
    return float(median(limpos))


def serie_winsorizada(valores: Sequence[Number], winsor: float = 0.10) -> List[float]:
    """Série (mesmo comprimento dos pontos válidos) com os extremos winsorizados.

    Usada pelo CAGR de valuation: um único ano atípico no início/fim deixa de distorcer
    o `g_historico`. Com < 5 pontos válidos a winsorização não morde — devolve os limpos.
    """
    limpos = _limpar(valores)
    if len(limpos) < 5:
        return limpos
    lo = float(np.percentile(limpos, winsor * 100))
    hi = float(np.percentile(limpos, (1.0 - winsor) * 100))
    return [min(max(v, lo), hi) for v in limpos]
