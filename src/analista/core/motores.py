"""Motores de valuation por arquétipo (v2.2, Fase 2) — funções puras config-driven.

Cada motor recebe números já-síntese (ROE/LPA/payout de valuation, VPA do ano-base) e
devolve um resultado ou `None` (never-raise), espelhando o padrão de `core/ddm.py`. Nenhum
motor recalcula método: todos COMPÕEM primitivas já testadas do `core/` (`lentes.vpa`,
`ddm.ddm_dois_estagios`, `ddm.valor_gordon`, `normalizacao.base_normalizada`) — consistência
cross-modo (FIX-04). `core/ddm.py`/`lentes.py`/`capm.py`/`normalizacao.py` ficam INTOCADOS.

Motores (arquétipo → motor primário):
- RIM (ENG-02 / CAL-01, banco/seguradora): RIM híbrido multiestágio — VPA + janela explícita do
  excesso de ROE sobre Ke + VALOR TERMINAL (perpetuidade de Gordon sobre o RI terminal, via
  `ddm.valor_gordon`). A janela converge a um excesso sustentável limitado; o terminal cresce a
  `g_terminal` ≤ PIB. O Ke é o ÚNICO do sistema (KE-01/Fase 12): o RIM recebe `a.ke` PRONTO do
  chamador (CAPM local sobre o β setorial+Blume), NÃO recomputa um Ke estrutural nem clampa — a
  perpetuidade converge pelo piso do Blume, por aritmética.
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
    "seguradora": "DDM-franquia — Gordon sobre o dividendo sustentável (seguradora capital-light)",
    "normalizado": "P/L justo sobre lucro normalizado (média 7–10a)",
    "dcf": "DCF sobre lucro, aproximação capital-light",
    "nav": "NAV contábil (piso patrimonial), não SOTP por segmento",
    "ddm": "DDM — lente conservadora (não é o motor deste arquétipo)",
}


@dataclass
class ResultadoRIM:
    """Resultado do Residual Income Model (espelha `ddm.ResultadoDDM`).

    `valor_intrinseco` = `vpa_base` + `vp_residual_income` + `vp_terminal`. `ri_por_ano` guarda o
    Residual Income (não-descontado) de cada ano da janela explícita; `vp_terminal` é o valor
    presente do continuing value (perpetuidade de Gordon sobre o RI terminal). `vp_terminal == 0`
    quando o terminal não é liberado (comportamento D-02 legado, ou RI terminal degenerado).
    """

    valor_intrinseco: float
    vpa_base: float
    vp_residual_income: float
    ri_por_ano: List[float]
    vp_terminal: float = 0.0
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
    excesso_sustentavel: float = 0.0,
    g_terminal: Optional[float] = None,
    ke_g_spread_min: float = 0.03,
    fade_para: Optional[float] = None,
    roe_terminal: Optional[float] = None,
) -> Optional[ResultadoRIM]:
    """RIM híbrido multiestágio (CFA L2 / Ohlson): janela explícita de residual income + valor
    terminal (continuing value) via perpetuidade de Gordon sobre o RI terminal (CAL-01).

        V0 = VPA0 + Σ_{t=1..n} RI_t/(1+Ke)^t + VP_terminal
        RI_t = (ROE_t − Ke)·B_{t-1};   B_t = B_{t-1}·(1 + ROE_t·retencao)   # clean surplus
        VP_terminal = valor_gordon(RI_{n+1}, Ke, g_terminal) / (1+Ke)^n,   RI_{n+1} = RI_n·(1+g)

    JANELA: `ROE_t` decai linearmente de `roe0` até `fade_para`. Quando `fade_para` não é passado,
    `fade_para = Ke + min(roe0 − Ke, excesso_sustentavel)` — a janela é a TRANSIÇÃO do excesso
    corrente até um excesso sustentável limitado (moat durável), não a zero nem ao excesso cheio
    eterno (evita double-count janela×terminal). O `min(roe0 − Ke, cap)` é a guarda ANTI-BAD-BANK:
    se `roe0 < Ke` (banco que destrói valor), `roe0 − Ke < 0` → `fade_para < Ke` → RI terminal
    negativo → valor ABAIXO do book (P/B < 1) — correto, sem clampar a ≥ Ke.

    TERMINAL: só é liberado se `g_terminal is not None` E `Ke − g_terminal ≥ ke_g_spread_min`
    (protege configs futuros de perpetuidade explosiva). O RI terminal cresce a `g_terminal`
    (≤ PIB), NÃO à taxa de crescimento do book na janela — usar a taxa do book seria assumir
    reinvestimento a excesso-de-ROE eterno, a fonte clássica de RIM explosivo. Reusa a primitiva
    testada `ddm.valor_gordon` (que já devolve None em `Ke − g ≤ 0`), sem reimplementar.

    TERMINAL NORMALIZADO (CAL-01/Alavanca 2/D-01): `roe_terminal` (opcional) ancora o excesso do RI
    da perpetuidade no ROE through-cycle do próprio ticker (mediana histórica, computada pelo
    `report`), aplicado SÓ na base do RI terminal — a janela explícita (`roe0`/`fade_para`) fica
    INTOCADA (Pitfall 1). O excesso terminal continua CAPADO pelo `excesso_sustentavel`:
    `excesso_t = min(roe_terminal − Ke, excesso_sustentavel)`, sobre a MESMA base de book do último
    RI da janela (`B_{n-1}`). Quando `roe_terminal − Ke ≥ excesso_sustentavel` o `min(...)` satura no
    cap — IDÊNTICO ao RI terminal legado (que também satura) → o valor não regride (protege o ITUB4
    por construção). `roe_terminal=None` ⇒ comportamento legado (`RI_n`). Pode ser negativo (ROE de
    ciclo < Ke) → RI terminal negativo (anti-bad-bank preservado no terminal).

    Backward-safe: chamada legada `rim(vpa0, roe0, ke, retencao, n)` reproduz o comportamento D-02
    (excesso_sustentavel=0.0 → fade a Ke; g_terminal=None → sem terminal; vp_terminal == 0;
    roe_terminal=None → RI terminal = RI_n, bit-idêntico à it.1).

    Never-raise: input None, `n <= 0`, `ke <= 0` ou `vpa0 <= 0` → None.
    """
    if None in (vpa0, roe0, ke, retencao) or n <= 0 or ke <= 0 or vpa0 <= 0:
        return None
    if fade_para is None:
        fade_para = ke + min(roe0 - ke, excesso_sustentavel)
    b_prev, vp, ris = vpa0, 0.0, []
    b_base_ri_final = vpa0  # base de book do ÚLTIMO RI da janela (B_{n-1}) p/ o terminal normalizado
    for t in range(1, n + 1):
        frac = (t - 1) / (n - 1) if n > 1 else 1.0
        roe_t = roe0 + (fade_para - roe0) * frac
        ri = (roe_t - ke) * b_prev
        vp += ri / (1 + ke) ** t
        ris.append(ri)
        b_base_ri_final = b_prev
        b_prev = b_prev * (1 + roe_t * retencao)
    vp_terminal = 0.0
    if g_terminal is not None and ke - g_terminal >= ke_g_spread_min:
        if roe_terminal is not None:
            # Normalização through-cycle no terminal: excesso capado sobre a MESMA base de book do
            # RI legado (B_{n-1}). Satura no cap ⇒ idêntico ao legado (não regride o ITUB4).
            excesso_t = min(roe_terminal - ke, excesso_sustentavel)
            ri_terminal_base = excesso_t * b_base_ri_final
        else:
            ri_terminal_base = ris[-1]
        ri_terminal = ri_terminal_base * (1 + g_terminal)
        tv = ddm.valor_gordon(dpa1=ri_terminal, ke=ke, g=g_terminal)
        vp_terminal = tv / (1 + ke) ** n if tv is not None else 0.0
    return ResultadoRIM(
        valor_intrinseco=vpa0 + vp + vp_terminal,
        vpa_base=vpa0,
        vp_residual_income=vp,
        ri_por_ano=ris,
        vp_terminal=vp_terminal,
    )


def lucro_normalizado(lpa_normalizado: float, ke: float, g_estavel: float) -> Number:
    """P/L justo (Gordon) sobre o LPA já normalizado (média 7–10a) — cíclica (ENG-03, D-04).

    Retorna `lpa_normalizado × fair_PE`, com `fair_PE = (1+g)/(Ke−g)` implícito no Gordon
    (`ddm.valor_gordon`). O lucro médio 7–10a é resolvido pelo CHAMADOR via
    `norm.media_ciclo(serie, anos_media=cfg["motores"]["ciclica"]["anos_media"])` — a média
    through-cycle, NÃO o endpoint Theil-Sen de base_normalizada (PRIM-01, split do estimador);
    aqui a função já recebe o LPA normalizado (fronteira FIX-04). None se `ke−g_estavel<=0` ou input None.
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
    # Trava defensiva g_alto <= ke (IN-02, espelha ddm.matriz_sensibilidade): com decrescente=False
    # e g_alto>ke o estágio explícito infla em vez de convergir. O chamador do report já pré-trava,
    # mas o motor é primitiva pura e independente — protege o chamador direto.
    if ke is not None:
        g_alto = min(g_alto, ke)
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
