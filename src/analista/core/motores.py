"""Motores de valuation por arquétipo (v2.2, Fase 2) — funções puras config-driven.

Cada motor recebe números já-síntese (ROE/LPA/payout de valuation, VPA do ano-base) e
devolve um resultado ou `None` (never-raise), espelhando o padrão de `core/ddm.py`. Nenhum
motor recalcula método: todos COMPÕEM primitivas já testadas do `core/` (`lentes.vpa`,
`ddm.ddm_dois_estagios`, `ddm.valor_gordon`, `normalizacao.base_normalizada`) — consistência
cross-modo (FIX-04). `core/ddm.py`/`lentes.py`/`capm.py`/`normalizacao.py` ficam INTOCADOS.

Motores (arquétipo → motor primário):
- RIM (ENG-02, banco/seguradora): VPA + VP do excesso de ROE sobre Ke (Cap. 16/17). O Ke
  estrutural do RIM (`ke_rim`) é MENOR que o CAPM ao vivo de banco (~16,8%) — sem prêmio
  small-cap, que é impróprio para banco large-cap/líquido (D-01). Sem prêmio terminal: o
  excesso faz fade até o Ke e o valor ancora no VPA (D-02).
- Lucro normalizado (ENG-03, cíclica): P/L justo (Gordon) sobre o lucro médio 7–10a.
- DCF de crescimento (ENG-04, compounder): reuso PURO de `ddm.ddm_dois_estagios` com LUCRO
  no lugar de dividendo, modelo-H (conservador). "DCF sobre lucro, aproximação capital-light".
- NAV contábil (ENG-05, holding): VPA como piso patrimonial (não SOTP por segmento, D-03).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from . import ddm, lentes

Number = Optional[float]


# Rótulos humanos de cada motor — exibidos no render (o Plan 02 consome no funil).
MOTOR_ROTULO = {
    "rim": "RIM — VPA + VP do excesso de ROE sobre Ke (banco/seguradora)",
    "normalizado": "P/L justo sobre lucro normalizado (média 7–10a)",
    "dcf": "DCF sobre lucro, aproximação capital-light",
    "nav": "NAV contábil (piso patrimonial), não SOTP por segmento",
    "ddm": "DDM — lente conservadora (não é o motor deste arquétipo)",
}


@dataclass
class ResultadoRIM:
    """Resultado do Residual Income Model (espelha `ddm.ResultadoDDM`).

    `valor_intrinseco` = `vpa_base` + `vp_residual_income`. `ri_por_ano` guarda o Residual
    Income (não-descontado) de cada ano do horizonte; com fade completo, `ri_por_ano[-1] ≈ 0`.
    """

    valor_intrinseco: float
    vpa_base: float
    vp_residual_income: float
    ri_por_ano: List[float]
    peso_residual: float = field(init=False)

    def __post_init__(self) -> None:
        self.peso_residual = (
            self.vp_residual_income / self.valor_intrinseco if self.valor_intrinseco else 0.0
        )


def rim(
    vpa0: float,
    roe0: float,
    ke: float,
    retencao: float,
    n: int,
    fade_para: Optional[float] = None,
) -> Optional[ResultadoRIM]:
    """RIM com clean surplus e fade linear do excesso de ROE até Ke (D-02).

        V0 = VPA0 + Σ_{t=1..n} (ROE_t − Ke)·B_{t-1} / (1+Ke)^t

    `ROE_t` decai linearmente de `roe0` até `fade_para` (default = `ke`); o book compõe por
    clean surplus `B_t = B_{t-1}·(1 + ROE_t·retencao)`. Como o excesso vai a zero em `n`, o
    Residual Income terminal é ≈ 0 e o valor fica ancorado no VPA (SEM perpetuidade de
    excesso, SEM prêmio terminal — D-02).

    Never-raise: input None, `n <= 0`, `ke <= 0` ou `vpa0 <= 0` → None.
    """
    if None in (vpa0, roe0, ke, retencao) or n <= 0 or ke <= 0 or vpa0 <= 0:
        return None
    fade_para = ke if fade_para is None else fade_para
    b_prev, vp, ris = vpa0, 0.0, []
    for t in range(1, n + 1):
        frac = (t - 1) / (n - 1) if n > 1 else 1.0
        roe_t = roe0 + (fade_para - roe0) * frac
        ri = (roe_t - ke) * b_prev
        vp += ri / (1 + ke) ** t
        ris.append(ri)
        b_prev = b_prev * (1 + roe_t * retencao)
    return ResultadoRIM(
        valor_intrinseco=vpa0 + vp,
        vpa_base=vpa0,
        vp_residual_income=vp,
        ri_por_ano=ris,
    )


def ke_rim(beta: float, cfg: dict) -> Number:
    """Ke estrutural do RIM: rf through-the-cycle + ERP de banco (sem prêmio small-cap).

    Espelha `capm.ke_local` (rf + beta×ERP), mas com um ERP MENOR (`motores.rim.erp_banco`):
    o prêmio small-cap/iliquidez embutido em `capm.erp_local` (~1,5%) é impróprio para banco
    large-cap/líquido, e comprimir o Ke destrava o ITUB4 (D-01). O resultado é clampado a
    `[ke_piso, ke_teto]` e nunca excede o Ke ao vivo (`ke_live`) — o RIM jamais herda o Ke
    ~16,8% que comprime o DDM de banco.

    Never-raise: beta None → None.
    """
    if beta is None:
        return None
    cap = cfg["capm"]
    rim_cfg = cfg["motores"]["rim"]
    rf = cap["rf_local"]
    ke_live = rf + beta * cap["erp_local"]
    ke = rf + beta * rim_cfg["erp_banco"]
    # Clampa a [ke_piso, ke_teto] e SÓ ENTÃO aplica o teto ke_live — a trava do Ke ao vivo tem
    # de vencer mesmo o piso (D-01: o RIM nunca excede o ke_live). Se o piso viesse por fora
    # (max externo), um ke_live abaixo do ke_piso quebraria o invariante (WR-02).
    ke_clamp = max(rim_cfg["ke_piso"], min(ke, rim_cfg["ke_teto"]))
    return min(ke_clamp, ke_live)


def lucro_normalizado(lpa_normalizado: float, ke: float, g_estavel: float) -> Number:
    """P/L justo (Gordon) sobre o LPA já normalizado (média 7–10a) — cíclica (ENG-03, D-04).

    Retorna `lpa_normalizado × fair_PE`, com `fair_PE = (1+g)/(Ke−g)` implícito no Gordon
    (`ddm.valor_gordon`). O lucro médio 7–10a é resolvido pelo CHAMADOR via
    `norm.base_normalizada(serie, anos_media=cfg["motores"]["ciclica"]["anos_media"])` — aqui
    a função já recebe o LPA normalizado (fronteira FIX-04). None se `ke−g_estavel<=0` ou input None.
    """
    return ddm.valor_gordon(dpa1=lpa_normalizado, ke=ke, g=g_estavel)


def dcf_crescimento(
    lpa_valuation: float,
    g_alto: float,
    g_estavel: float,
    ke: float,
    n: int,
    decrescente: bool = True,
) -> Number:
    """DCF de crescimento por reuso PURO de `ddm.ddm_dois_estagios` (D-05, ddm.py INTOCADO).

    Alimenta o LUCRO no lugar do dividendo: `dpa_inicial = lpa_valuation × (1 + g_alto)` (lucro
    do ano 1, NÃO × payout). Modelo-H por default (`decrescente=True`) — conservador (Pitfall 4).
    Rótulo honesto: "DCF sobre lucro, aproximação capital-light". Devolve o valor intrínseco
    (positivo e finito) ou None se `ke−g_estavel<=0`, input None ou `n<=0`.
    """
    if lpa_valuation is None or g_alto is None or n is None or n <= 0:
        return None
    dpa_inicial = lpa_valuation * (1 + g_alto)
    res = ddm.ddm_dois_estagios(
        dpa_inicial=dpa_inicial,
        g_alto=g_alto,
        n=n,
        g_estavel=g_estavel,
        ke=ke,
        decrescente=decrescente,
    )
    return res.valor_intrinseco if res else None


def nav_contabil(patrimonio_liquido: float, num_acoes: float) -> Number:
    """NAV contábil = VPA do ano-base (piso patrimonial), NÃO SOTP por segmento (D-03).

    Reuso direto de `lentes.vpa` (PL/ações via `_safe_div`, None/zero-safe). None se PL ou
    número de ações forem None/zero.
    """
    return lentes.vpa(patrimonio_liquido, num_acoes)
