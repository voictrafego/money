"""Estágio do ciclo de vida da empresa — Cap. 8 (Damodaran, 2017).

Classificação simplificada em 6 estágios a partir do crescimento dos lucros e do payout.
O livro associa cada estágio à relação entre lucro, receita e dividendo: empresas maduras
(estágios 5-6) distribuem mais dividendos; empresas em crescimento (2-4) reinvestem mais.
"""

from __future__ import annotations

from typing import Optional

ESTAGIOS = {
    1: "Startup",
    2: "Crescimento jovem",
    3: "Crescimento alto",
    4: "Crescimento maduro",
    5: "Maturidade (crescimento estável)",
    6: "Declínio",
}


def classificar_estagio(
    g_lucro: Optional[float],
    payout: Optional[float],
    lucro_positivo: bool,
    lucro_decrescente: bool = False,
) -> str:
    """Heurística de classificação do estágio de ciclo de vida.

    - prejuízo persistente → Startup/Declínio;
    - alto crescimento + baixo payout → crescimento;
    - baixo crescimento + alto payout → maturidade;
    - lucro caindo + payout alto sustentado com reservas → declínio.
    """
    if not lucro_positivo:
        return ESTAGIOS[1] if not lucro_decrescente else ESTAGIOS[6]

    g = g_lucro if g_lucro is not None else 0.0
    p = payout if payout is not None else 0.0

    if lucro_decrescente and p > 0.9:
        return ESTAGIOS[6]
    if g >= 0.20 and p < 0.30:
        return ESTAGIOS[2]
    if g >= 0.10 and p < 0.50:
        return ESTAGIOS[3]
    if g >= 0.05:
        return ESTAGIOS[4]
    return ESTAGIOS[5]
