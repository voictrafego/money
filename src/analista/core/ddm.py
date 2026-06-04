"""Modelo de Desconto de Dividendos (MDD) — Cap. 13, 15 e 17 do livro.

Valor intrínseco = VP do somatório dos dividendos do período explícito + VP do valor residual.

    V_0 = Σ_{t=1..n} DIV_t / (1+Ke)^t  +  VR_n / (1+Ke)^n
    VR_n = DIV_{n+1} / (Ke - g_estável) = DIV_n * (1+g_estável) / (Ke - g_estável)

Conferência (Itaú, Cap. 17, Tabela 41): DPA_2020 = 2,362; g = 10,24%; n = 10;
    g_estável = 2,5%; Ke = 12,48% → VP dividendos ≈ 19,23, VP residual ≈ 17,99,
    valor intrínseco ≈ R$ 37,22.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

Number = Optional[float]


@dataclass
class ResultadoDDM:
    valor_intrinseco: float
    vp_dividendos: float
    vp_residual: float
    valor_residual_futuro: float
    dividendos_projetados: List[float]
    vp_por_ano: List[float]
    peso_residual: float = field(init=False)

    def __post_init__(self) -> None:
        self.peso_residual = (
            self.vp_residual / self.valor_intrinseco if self.valor_intrinseco else 0.0
        )


def valor_gordon(dpa1: float, ke: float, g: float) -> Number:
    """Modelo de Gordon (crescimento perpétuo): V = DPA_1 / (Ke - g).

    Exige Ke > g (o livro alerta para a instabilidade quando Ke ~ g).
    """
    if dpa1 is None or ke is None or g is None:
        return None
    if ke - g <= 0:
        return None
    return dpa1 / (ke - g)


def projetar_dividendos(
    dpa_inicial: float,
    n: int,
    g_alto: float,
    g_estavel: Optional[float] = None,
    decrescente: bool = False,
) -> List[float]:
    """Projeta DPA do ano 1 (dpa_inicial) ao ano n.

    - constante (decrescente=False): DIV_t = dpa_inicial * (1+g_alto)^(t-1)
    - decrescente (modelo H): g cai linearmente de g_alto (ano 1) até g_estável (ano n).
    """
    if n <= 0:
        return []
    divs = [dpa_inicial]
    if decrescente:
        if g_estavel is None:
            g_estavel = g_alto
        # taxa de crescimento aplicada do ano t-1 para o ano t, decaindo linearmente.
        for t in range(2, n + 1):
            frac = (t - 2) / (n - 2) if n > 2 else 1.0
            g_t = g_alto + (g_estavel - g_alto) * frac
            divs.append(divs[-1] * (1 + g_t))
    else:
        for _ in range(2, n + 1):
            divs.append(divs[-1] * (1 + g_alto))
    return divs


def ddm_dois_estagios(
    dpa_inicial: float,
    g_alto: float,
    n: int,
    g_estavel: float,
    ke: float,
    decrescente: bool = False,
    tributacao: float = 0.0,
) -> Optional[ResultadoDDM]:
    """DDM de dois estágios (Cap. 15/17).

    `dpa_inicial` é o dividendo por ação projetado para o PRIMEIRO ano (t=1).
    `tributacao` aplica imposto sobre dividendos: DIV_após = DIV * (1 - t).
    """
    if ke is None or g_estavel is None or ke - g_estavel <= 0:
        return None
    if dpa_inicial is None or n <= 0:
        return None

    divs = projetar_dividendos(dpa_inicial, n, g_alto, g_estavel, decrescente)
    if tributacao:
        divs = [d * (1 - tributacao) for d in divs]

    vp_por_ano = [d / (1 + ke) ** (t + 1) for t, d in enumerate(divs)]
    vp_dividendos = sum(vp_por_ano)

    div_n = divs[-1]
    vr_futuro = div_n * (1 + g_estavel) / (ke - g_estavel)
    vp_residual = vr_futuro / (1 + ke) ** n

    return ResultadoDDM(
        valor_intrinseco=vp_dividendos + vp_residual,
        vp_dividendos=vp_dividendos,
        vp_residual=vp_residual,
        valor_residual_futuro=vr_futuro,
        dividendos_projetados=divs,
        vp_por_ano=vp_por_ano,
    )


def matriz_sensibilidade(
    dpa_inicial: float,
    g_alto: float,
    n: int,
    g_estavel: float,
    ke: float,
    deltas_ke: Sequence[float],
    deltas_g: Sequence[float],
    decrescente: bool = False,
    tributacao: float = 0.0,
) -> List[List[Number]]:
    """Matriz de valor intrínseco variando Ke (linhas) e g_alto (colunas) — Cap. 12/17."""
    linhas: List[List[Number]] = []
    for dke in deltas_ke:
        linha: List[Number] = []
        for dg in deltas_g:
            res = ddm_dois_estagios(
                dpa_inicial, g_alto + dg, n, g_estavel, ke + dke, decrescente, tributacao
            )
            linha.append(res.valor_intrinseco if res else None)
        linhas.append(linha)
    return linhas
