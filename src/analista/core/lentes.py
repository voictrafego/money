"""Lentes de valuation e contexto da aba Analisar (Fase 19).

Fórmulas de referência CLÁSSICAS, complementares ao método do livro (o DDM/múltiplos
continua sendo a análise principal). Todas puras e testáveis por golden, espelhando o
padrão de `ddm.py`/`multiples.py`: recebem números, devolvem `Number`; `None` (never-raise)
quando a métrica é indefinida. A UI só LÊ o resultado.

Lentes:
- Graham (VAL-01): preço-justo = √(22,5 × LPA × VPA).
- Bazin (VAL-02): preço-teto = DPA médio (até 5 anos) ÷ DY-mínimo (6%).
- "Quanto teria rendido" (RET-01): R$ 1.000 via Adj Close (já embute reinvestimento).
- Comparador de pares (PEER-01): P/L, P/VP, ROE, DY, Valor de Mercado dos pares do setor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence

from . import multiples as mult

Number = Optional[float]

# VAL-01: constante clássica de Graham (√(22,5 × LPA × VPA)).
GRAHAM_K = 22.5
# VAL-02: DY-mínimo exigido por Bazin para boas pagadoras (6%).
BAZIN_DY_MIN = 0.06


# --------------------------------------------------------------------------- #
# VAL-01 — Preço-Justo de Graham
# --------------------------------------------------------------------------- #
def preco_justo_graham(lpa: float, vpa: float) -> Number:
    """Preço-justo de Graham = √(22,5 × LPA × VPA).

    Conferência: LPA 3,0 e VPA 10,0 → √(22,5×3×10) = √675 ≈ 25,98.

    Degradação (VAL-01): LPA ≤ 0 ou VPA ≤ 0 (ou None) → None. A fórmula não vale para
    empresa sem lucro/PL positivo (não serve p/ tech/prejuízo); a raiz de produto negativo
    seria imaginária.
    """
    if lpa is None or vpa is None or lpa <= 0 or vpa <= 0:
        return None
    return math.sqrt(GRAHAM_K * lpa * vpa)


def vpa(patrimonio_liquido: float, num_acoes: float) -> Number:
    """Valor patrimonial por ação = PL / nº de ações (do ano-base)."""
    return mult._safe_div(patrimonio_liquido, num_acoes)


# --------------------------------------------------------------------------- #
# VAL-02 — Preço-Teto de Bazin
# --------------------------------------------------------------------------- #
def dpa_medio(dpas: Sequence[Optional[float]], n: int = 5) -> Number:
    """Média aritmética dos ÚLTIMOS `n` valores não-None de `dpas`.

    Se houver menos de `n` anos, usa o período disponível (espelha a nota do concorrente).
    None se não houver nenhum DPA.
    """
    validos = [d for d in dpas if d is not None]
    if not validos:
        return None
    janela = validos[-n:]
    return sum(janela) / len(janela)


def preco_teto_bazin(dpa_med: float, dy_minimo: float = BAZIN_DY_MIN) -> Number:
    """Preço-teto de Bazin = DPA médio ÷ DY-mínimo.

    Conferência: DPA médio 1,2 e DY-mínimo 6% → 1,2 / 0,06 = 20,0.

    Degradação (VAL-02): DPA médio None ou ≤ 0 → None (só vale p/ boas pagadoras).
    """
    if dpa_med is None or dpa_med <= 0:
        return None
    return mult._safe_div(dpa_med, dy_minimo)


def upside(referencia: float, preco_atual: float) -> Number:
    """Upside de uma referência vs. o preço atual = referência/preço − 1.

    preço atual None/0 → None. Usado por Graham e Bazin.
    """
    if referencia is None or preco_atual is None or preco_atual == 0:
        return None
    return referencia / preco_atual - 1.0


# --------------------------------------------------------------------------- #
# RET-01 — "Quanto teria rendido"
# --------------------------------------------------------------------------- #
def retorno_periodo(
    serie_adj, anos: int, valor_inicial: float = 1000.0
) -> Number:
    """Quanto R$ `valor_inicial` investidos há `anos` anos valeriam hoje.

    `serie_adj` é uma pd.Series de Adj Close indexada por data (o Adj Close já embute o
    reinvestimento de dividendos, RET-01). Determina a data-corte = último índice − `anos`
    anos, pega o primeiro preço em/ou-após a corte e o último preço, e devolve
    `valor_inicial × último/primeiro`.

    Never-raise: série None/vazia OU histórico insuficiente (dado mais antigo é posterior à
    janela pedida) → None.
    """
    try:
        if serie_adj is None or len(serie_adj) == 0:
            return None
        import pandas as pd

        serie = serie_adj.dropna()
        if len(serie) == 0:
            return None
        corte = serie.index[-1] - pd.DateOffset(years=anos)
        # histórico insuficiente: não há dado tão antigo quanto a janela pedida.
        if serie.index[0] > corte:
            return None
        janela = serie[serie.index >= corte]
        if len(janela) == 0:
            return None
        primeiro = float(janela.iloc[0])
        ultimo = float(serie.iloc[-1])
        if primeiro == 0:
            return None
        return valor_inicial * ultimo / primeiro
    except Exception:
        return None
