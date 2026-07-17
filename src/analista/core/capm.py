"""Custo de capital do acionista (Ke) via CAPM — Cap. 16 do livro.

Fórmula: Ke = Rf + Beta * ERP.

Abordagem "eua_ajustada" (caso Itaú, 16.1-16.4), reconstruída para reproduzir
exatamente o Ke = 12,48% do livro:
    ERP_br (US$) = ERP_eua + EMBI+_brasil
    Ke (US$)     = Rf_eua + Beta * ERP_br
    Ke (R$)      = Ke (US$) * (1 + infl_br) / (1 + infl_eua)

Conferência (Itaú): 0,0192 + 1,24 * (0,0620 + 0,0214) = 0,122616 (US$);
    0,122616 * 1,0440 / 1,0252 = 0,12486 ~= 12,48%.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from ..ingest import macro

Number = Optional[float]


def beta(retornos_acao: Sequence[float], retornos_mercado: Sequence[float]) -> Number:
    """Beta = Cov(R_acao, R_mercado) / Var(R_mercado) (16.2).

    Espera retornos pareados (mesma frequência/datas), idealmente 60 meses.
    """
    if retornos_acao is None or retornos_mercado is None:
        return None
    pares = [
        (a, m)
        for a, m in zip(retornos_acao, retornos_mercado)
        if a is not None and m is not None
    ]
    n = len(pares)
    if n < 2:
        return None
    ra = [p[0] for p in pares]
    rm = [p[1] for p in pares]
    media_a = sum(ra) / n
    media_m = sum(rm) / n
    cov = sum((a - media_a) * (m - media_m) for a, m in pares) / n
    var_m = sum((m - media_m) ** 2 for m in rm) / n
    if var_m == 0:
        return None
    return cov / var_m


@dataclass
class CapmParams:
    rf_us: float = 0.0192
    embi_brasil: float = 0.0214
    erp_us: float = 0.0620
    inflacao_br: float = 0.0440
    inflacao_us: float = 0.0252

    def erp_brasil_usd(self) -> float:
        """Prêmio de risco para o Brasil em dólares: ERP_eua + risco-país (16.3)."""
        return self.erp_us + self.embi_brasil


def ke_eua_ajustada(beta_acao: float, params: CapmParams) -> float:
    """Ke em reais pela abordagem com dados de mercado desenvolvido + ajuste (16.4)."""
    ke_usd = params.rf_us + beta_acao * params.erp_brasil_usd()
    ke_brl = ke_usd * (1 + params.inflacao_br) / (1 + params.inflacao_us)
    return ke_brl


def ke_local(beta_acao: float, rf_local: float, erp_local: float) -> float:
    """Ke pela abordagem com dados locais (caso Engie, 17.2): Ke = Rf + Beta * ERP."""
    return rf_local + beta_acao * erp_local


def beta_blume(
    beta_cru: Number, setor: Optional[str], mapa_setorial: Optional[dict]
) -> Number:
    """Beta ajustado por Blume (`0,33 + 0,67 x base`) sobre o beta SETORIAL (KE-03, D-03/D-04).

    A base e' a mediana do setor (`mapa_setorial[_normalizar_setor(setor)]`) quando disponivel
    — a "industry beta" de Damodaran, que faz BB e Bradesco (mesmo risco de negocio) receberem
    o MESMO beta, apagando o ruido do beta individual. Fallback D-04: setor ausente do mapa (ou
    mapa vazio) -> usa o proprio `beta_cru` (beta individual Blume-ajustado). Blume aplicado UMA
    vez (D-03: agregar-beta-cru->Blume == Blume->agregar para a mediana, linear e monotonico).

    Never-raise (contrato de borda da engine, como `motores.ke_rim`): `beta_cru is None` -> None
    (sem dado de mercado, sem Ke). A normalizacao de setor e' a fonte unica de `ingest.macro`
    (nao acopla a engine a rede: `_normalizar_setor` e' pura, sem I/O).
    """
    if beta_cru is None:
        return None
    base = None
    if mapa_setorial:
        base = mapa_setorial.get(macro._normalizar_setor(setor))
    if base is None:
        base = beta_cru
    return 0.33 + 0.67 * base
