"""Identidade P/B fechada (BLIND-02a) — a ponte auditável do ENG-08, módulo puro (zero I/O).

Representação steady-state (Gordon-RIM) do valuation, usada como LENTE auditável e como TESTE de
correção da razão implícita — NUNCA como o motor de valor (o motor é o RIM multiestágio de
`motores.rim`). Duas funções, ambas álgebra pura, knob-proof:

    pb_justo(roe, ke, g)      = 1 + (roe − ke) / (ke − g)
    payout_terminal(roe_t, g) = 1 − g / roe_t

Both são never-raise: insumo None, `ke − g ≤ 0` (spread não-positivo) ou `roe_t == 0` devolvem
None em vez de levantar — a fronteira `ke − g > 0` já é garantida pelo piso do Blume (Fase 12,
`Ke_min > g_cap`), mas a guarda de borda mantém a pureza (SAN-06, never-raise).
"""

from __future__ import annotations

from typing import Optional


def pb_justo(
    roe: Optional[float], ke: Optional[float], g: Optional[float]
) -> Optional[float]:
    """P/B justo steady-state = 1 + (ROE − Ke) / (Ke − g). None-guard de borda (never-raise).

    Devolve None quando qualquer insumo é None ou o spread `ke − g ≤ 0` (perpetuidade não
    converge) — nunca levanta. A identidade é EXATA (é a mesma álgebra do BLIND-02a): um choque
    de inflação que sobe ROE, Ke e g nas mesmas proporções preserva `(ROE − Ke)` e `(Ke − g)`,
    logo o P/B não se move (invariância à inflação, testada em test_invariantes_v24)."""
    if roe is None or ke is None or g is None:
        return None
    spread = ke - g
    if spread <= 0.0:
        return None
    return 1.0 + (roe - ke) / spread


def payout_terminal(roe_t: Optional[float], g: Optional[float]) -> Optional[float]:
    """Payout terminal implícito = 1 − g / ROE_T. None-guard de borda (never-raise).

    Devolve None quando `roe_t` é None/zero ou `g` é None — nunca levanta. Sob crescimento
    terminal zero (concessão finita, carve-out do spike 13-01) o payout_T crava em 1,0: é a
    identidade definicional de um terminal sem retenção (ICPC 01), não patologia — por isso a
    guarda de razão do consumidor é meio-aberta (0,1] quando g_terminal is None."""
    if roe_t is None or g is None or roe_t == 0.0:
        return None
    return 1.0 - g / roe_t
