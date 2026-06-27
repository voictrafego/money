"""Normalização de lucro para o valuation (FIX-04 — raiz da cascata VULC3).

O lucro CVM cru de UM exercício atípico (recuperação de créditos fiscais, distribuição
extraordinária) contamina ROE, CAGR, LPA, payout e DY do valuation. Esta camada entrega
a base de lucro *robusta* — o número-síntese que o valuation deve consumir no lugar do
`lucro_liquido.get(ult)` cru.

Espírito do livro (BSD, Cap. 8.4): o Big, Safe Dividend já usa médias trienais +
winsorização a 10%. Reaproveitamos esse espírito como base de qualidade do valuation.

**Primitiva pura:** recebe sequências de números (podendo conter None) + a janela/winsor
de config e devolve número(s). NÃO importa nada da engine de fundamentos/relatório
(sem ciclo de import) — só numpy/statistics.

Método escolhido (e por quê):
  - N >= 5 válidos    -> **média winsorizada** aos percentis `winsor`/`1-winsor`. Com pontos
    suficientes a winsorização clampa só os extremos e preserva o centro — espelha o BSD.
  - 2 <= N < 5        -> **mediana**. Com poucos pontos a winsorização percentil mal desloca
    os extremos (o outlier ainda pesaria na média); a mediana é o estimador robusto correto.
  - N == 1            -> o próprio valor (nada a suavizar).
  - N == 0            -> None (degradação graciosa; série vazia/só-None — T-08-01).
"""

from __future__ import annotations

from statistics import median
from typing import List, Optional, Sequence

import numpy as np

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
    """Base de lucro normalizada sobre os últimos `anos_media` valores válidos.

    Número-síntese ÚNICO de qualidade que alimenta `roe_valuation`/`lpa_valuation`.
    Mediana p/ 2<=N<5, média winsorizada p/ N>=5, valor único p/ N=1, None p/ vazio.
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
