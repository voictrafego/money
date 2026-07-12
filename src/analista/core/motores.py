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
  `g_terminal` ≤ PIB. O Ke estrutural (`ke_rim`) é MENOR que o CAPM ao vivo de banco — sem prêmio
  small-cap, impróprio para banco large-cap/líquido (D-01); ke_teto revisado 0.14→0.13 (CAL-02).
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

    Backward-safe: chamada legada `rim(vpa0, roe0, ke, retencao, n)` reproduz o comportamento D-02
    (excesso_sustentavel=0.0 → fade a Ke; g_terminal=None → sem terminal; vp_terminal == 0).

    Never-raise: input None, `n <= 0`, `ke <= 0` ou `vpa0 <= 0` → None.
    """
    if None in (vpa0, roe0, ke, retencao) or n <= 0 or ke <= 0 or vpa0 <= 0:
        return None
    if fade_para is None:
        fade_para = ke + min(roe0 - ke, excesso_sustentavel)
    b_prev, vp, ris = vpa0, 0.0, []
    for t in range(1, n + 1):
        frac = (t - 1) / (n - 1) if n > 1 else 1.0
        roe_t = roe0 + (fade_para - roe0) * frac
        ri = (roe_t - ke) * b_prev
        vp += ri / (1 + ke) ** t
        ris.append(ri)
        b_prev = b_prev * (1 + roe_t * retencao)
    vp_terminal = 0.0
    if g_terminal is not None and ke - g_terminal >= ke_g_spread_min:
        ri_terminal = ris[-1] * (1 + g_terminal)
        tv = ddm.valor_gordon(dpa1=ri_terminal, ke=ke, g=g_terminal)
        vp_terminal = tv / (1 + ke) ** n if tv is not None else 0.0
    return ResultadoRIM(
        valor_intrinseco=vpa0 + vp + vp_terminal,
        vpa_base=vpa0,
        vp_residual_income=vp,
        ri_por_ano=ris,
        vp_terminal=vp_terminal,
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
    # Leitura defensiva do config (paridade com classificar): um config antigo sem o bloco
    # `motores:` não pode quebrar o never-raise na borda (WR-03). Defaults == config.yaml.
    cap = (cfg or {}).get("capm", {})
    rim_cfg = (cfg or {}).get("motores", {}).get("rim", {})
    rf = cap.get("rf_local", 0.105)
    ke_live = rf + beta * cap.get("erp_local", 0.06)
    ke = rf + beta * rim_cfg.get("erp_banco", 0.045)
    # Clampa a [ke_piso, ke_teto] e SÓ ENTÃO aplica o teto ke_live — a trava do Ke ao vivo tem
    # de vencer mesmo o piso (D-01: o RIM nunca excede o ke_live). Se o piso viesse por fora
    # (max externo), um ke_live abaixo do ke_piso quebraria o invariante (WR-02).
    ke_clamp = max(rim_cfg.get("ke_piso", 0.11), min(ke, rim_cfg.get("ke_teto", 0.14)))
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
