"""Análise e valuation por múltiplos — Cap. 11 e 12 do livro.

- Ranking por múltiplos padronizados em [0,100] (Cap. 11, Tabela 27).
- Regressão P/L = f(Dividend Payout, ROE) por setor para estimar o P/L "justo" e o
  preço-alvo, identificando empresas subavaliadas por reversão à média (Cap. 12).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np

Number = Optional[float]


# --------------------------------------------------------------------------- #
# Cap. 11 — ranking por múltiplos padronizados [0,100]
# --------------------------------------------------------------------------- #
# "maior melhor": valor/máx*100 ; "menor melhor": mín/valor*100
MAIOR_MELHOR = {"ML", "ROE", "EY", "DY"}
MENOR_MELHOR = {"PL", "PEG"}


def padronizar_multiplo(valores: List[Number], maior_melhor: bool) -> List[Number]:
    finitos = [v for v in valores if v is not None and v > 0]
    if not finitos:
        return [None for _ in valores]
    if maior_melhor:
        vmax = max(finitos)
        return [None if v is None else (v / vmax * 100.0) for v in valores]
    vmin = min(finitos)
    return [None if v is None or v <= 0 else (vmin / v * 100.0) for v in valores]


def ranking_por_multiplos(
    empresas: List[str],
    multiplos: Dict[str, List[Number]],
    pesos: Optional[Dict[str, float]] = None,
) -> List[Dict[str, object]]:
    """Ranqueia empresas pela média (ponderada) das notas padronizadas dos múltiplos.

    `multiplos`: {"ML": [...], "ROE": [...], "PL": [...], ...} alinhado a `empresas`.
    """
    nomes = list(multiplos.keys())
    notas: Dict[str, List[Number]] = {}
    for nome in nomes:
        notas[nome] = padronizar_multiplo(multiplos[nome], nome in MAIOR_MELHOR)

    pesos = pesos or {n: 1.0 for n in nomes}
    soma_pesos = sum(pesos.get(n, 1.0) for n in nomes)

    resultado = []
    for i, emp in enumerate(empresas):
        comp = [(notas[n][i], pesos.get(n, 1.0)) for n in nomes if notas[n][i] is not None]
        if comp:
            nota = sum(v * p for v, p in comp) / sum(p for _, p in comp)
        else:
            nota = None
        resultado.append({"empresa": emp, "nota": nota,
                           "notas": {n: notas[n][i] for n in nomes}})
    resultado.sort(key=lambda r: (r["nota"] is not None, r["nota"] or 0), reverse=True)
    return resultado


# --------------------------------------------------------------------------- #
# Cap. 12 — regressão P/L = f(DP, ROE) e preço-alvo
# --------------------------------------------------------------------------- #
# Abaixo deste n, ajustar 3 parâmetros sobre poucas observações deixa a regressão
# instável (overfitting/multicolinearidade) e o veredito de preço-alvo pouco confiável.
LIMIAR_AMOSTRA = 10
# Abaixo deste R², a regressão explica pouco da variação de P/L do setor — o preço-alvo
# derivado é frágil e o veredito Subavaliada/Cara não deve ser lido com confiança (AUD-CMP-02).
LIMIAR_R2 = 0.5
# Freio de sanidade do preço-alvo de regressão (Achado 3 — freio do Ranking): um alvo com
# upside abaixo deste piso (ex.: ROMI3 alvo R$0,10 / −98%) é degenerado — a regressão extrapolou
# fora do suporte, não é uma tese de −98%. O Ranking marca esse alvo como não-confiável em vez de
# estampá-lo como preço-alvo cravado. Constante de módulo (sem config.yaml novo, padrão LIMIAR_*).
LIMIAR_UPSIDE_ABSURDO = -0.90
# Limiar de DIVERGÊNCIA entre as duas lentes da MESMA ação (Achado 4 — SINALIZAÇÃO, NÃO
# reconciliação): sinaliza quando a lente maior > 2× a menor (WEGE3 ~3×, ITUB4 ~2,2×). Coerente
# com o limiar de divergência da Fase 3 do roadmap. Const de módulo (padrão LIMIAR_*, sem config).
LIMIAR_DIVERGENCIA = 2.0


def divergencia_entre_lentes(
    v_a: Number, v_b: Number, limiar: float = LIMIAR_DIVERGENCIA
) -> tuple:
    """Sinaliza (Achado 4) divergência entre duas estimativas da MESMA ação (helper PURO).

    As duas lentes medem coisas diferentes — intrínseco ABSOLUTO por dividendos (DDM) vs. P/L
    justo RELATIVO a pares (regressão) — e podem divergir legitimamente. Este helper apenas
    AVISA quando divergem além de `limiar`: devolve `(divergiu: bool, razao = maior/menor)`.

    IMPORTANTE — isto é SINALIZAÇÃO, não RECONCILIAÇÃO. O ensemble/reconciliação real (DDM ×
    motor do arquétipo) depende dos motores da Fase 2 e é escopo da Fase 3; aqui não se inventa
    nenhum número reconciliado, só se sinaliza a discordância honestamente.

    Dado ausente/inválido em QUALQUER lente (None, zero ou negativo) → `(False, 1.0)`: não se
    inventa divergência sobre dado que não existe (evita ZeroDivision/comparação espúria).
    """
    if v_a is None or v_b is None or v_a <= 0 or v_b <= 0:
        return (False, 1.0)
    maior, menor = max(v_a, v_b), min(v_a, v_b)
    razao = maior / menor
    return (razao >= limiar, razao)


@dataclass
class RegressaoPL:
    coeficientes: np.ndarray   # [intercepto, b_DP, b_ROE]
    r2: float
    n: int

    def prever(self, dp: float, roe: float) -> float:
        b0, b1, b2 = self.coeficientes
        return float(b0 + b1 * dp + b2 * roe)

    @property
    def amostra_pequena(self) -> bool:
        """Poucas empresas para 3 parâmetros → regressão instável."""
        return self.n < LIMIAR_AMOSTRA

    @property
    def r2_baixo(self) -> bool:
        """R² < 0,5 → a regressão explica pouco do P/L do setor; preço-alvo pouco confiável."""
        return self.r2 < LIMIAR_R2

    @property
    def roe_sinal_invertido(self) -> bool:
        """b_ROE < 0 contraria Gordon (P/L justo cresce com o ROE) → overfitting."""
        return float(self.coeficientes[2]) < 0


def ajustar_regressao_pl(
    pl: Sequence[float], dp: Sequence[float], roe: Sequence[float]
) -> Optional[RegressaoPL]:
    """Ajusta P/L = b0 + b1*DP + b2*ROE por mínimos quadrados (OLS).

    Descarta observações com valores ausentes/negativos de P/L. Requer pelo menos
    4 empresas para 3 parâmetros.

    De-poison do fit (D-06, ver 09-CROSS-EFFECT-FASE10.md): o payout `d` é clampado em
    [0,1] ANTES de montar a matriz de design. A regressão foi calibrada para payout no
    domínio [0,1]; desde a Fase 9 `payout_valuation()` deixou de clampar (D-03), então um
    payout legitimamente >100% (TAEE11 ≈ 2.16) entrava cru no fit e envenenava o coeficiente
    b1. Clampar aqui é fonte única: cobre cli e app (FIX-04) sem duplicar o clamp já existente
    da PREVISÃO em `preco_alvo_por_regressao`. O canônico `payout_valuation()`/`mediana_payout`
    permanece SEM clamp (D-03 Fase 9).
    """
    linhas = [
        (p, min(max(d, 0.0), 1.0), r)
        for p, d, r in zip(pl, dp, roe)
        if None not in (p, d, r) and p > 0
    ]
    if len(linhas) < 4:
        return None
    y = np.array([l[0] for l in linhas], dtype=float)
    X = np.array([[1.0, l[1], l[2]] for l in linhas], dtype=float)
    coef, _resid, _rank, _sv = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ coef
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return RegressaoPL(coeficientes=coef, r2=r2, n=len(linhas))


@dataclass
class PrecoAlvo:
    pl_corrente: float
    pl_esperado: float
    lpa: float
    preco_corrente: float
    preco_alvo: float
    upside: float
    subavaliada: bool
    payout_fora_faixa: bool = False


def preco_alvo_por_regressao(
    reg: RegressaoPL,
    dp: float,
    roe: float,
    lpa: float,
    preco_corrente: float,
) -> Optional[PrecoAlvo]:
    """Preço-alvo = P/L_esperado * LPA (Cap. 12.2). Upside vs preço corrente.

    Conferência (CTEEP, Cap. 12): P/L esperado ≈ 14,18; LPA 2,6256 → alvo ≈ R$ 37,22.
    """
    if reg is None or None in (dp, roe, lpa, preco_corrente) or lpa <= 0:
        return None
    # Mesmo clamp do Analisar antes do DDM (report.py: payout_proj = min(media_3a, 1.0)):
    # payout fora de [0,1] (>100% ou negativo de LPA<0) não pode puxar b1*DP para valores sem sentido.
    dp_clamp = min(max(dp, 0.0), 1.0)
    payout_fora_faixa = dp_clamp != dp
    pl_esperado = reg.prever(dp_clamp, roe)
    # AUD-CMP-03: P/L esperado ≤ 0 é economicamente absurdo (regressão extrapolada fora do
    # suporte — ex.: ROE alto com b_ROE<0, caso roe_sinal_invertido). Gera preço-alvo e upside
    # negativos e um veredito "Cara" espúrio. Trata como indisponível (preço-alvo "—"), não Cara.
    if pl_esperado <= 0:
        return None
    pl_corrente = preco_corrente / lpa
    preco_alvo = pl_esperado * lpa
    upside = preco_alvo / preco_corrente - 1.0 if preco_corrente else None
    return PrecoAlvo(
        pl_corrente=pl_corrente,
        pl_esperado=pl_esperado,
        lpa=lpa,
        preco_corrente=preco_corrente,
        preco_alvo=preco_alvo,
        upside=upside,
        subavaliada=preco_alvo > preco_corrente,
        payout_fora_faixa=payout_fora_faixa,
    )
