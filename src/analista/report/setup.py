"""Montagem do SetupSwing (SCORE-01) — agregador read-only sobre SinaisTecnicos.

Lê o contrato `SinaisTecnicos` já computado (Fases 12-14, golden-testado) e o destila num
score ponderado EXPLICÁVEL (decomposição peso-a-peso), com R:R como GATE DURO, grade
qualitativa PT-BR e conflito multi-TF como penalização modulante.

Princípios (CONTEXT/RESEARCH da Fase 15):
- READ-ONLY: só LÊ rótulos discretos já validados; zero recálculo de série temporal.
- FIREWALL: importa só os tipos do contrato em core/indicators; a engine fundamentalista
  (report do módulo irmão) NUNCA é importada aqui (Critério 1).
- DEGRADAÇÃO GRACIOSA: nunca levanta exceção para a UI — degrada para SetupSwing "Sem setup".
- CONFIG-DRIVEN: pesos/rr_minimo/rr_alvo/penalidade/cortes vêm de cfg["score"] (zero hardcode).
- COPY NEUTRA: grade/detalhe são chaves estáveis de ESTUDO ("Forte", "duplo_fundo:confirmado"),
  NUNCA imperativo ("compre/venda/entre/recomend...") — fronteira "exibe, nunca recomenda" (D-06).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..core import indicators  # só p/ tipos; consome SinaisTecnicos JÁ calculado pelo caller
# O módulo da engine fundamentalista (irmão) NUNCA é importado aqui (firewall, Critério 1).


# --------------------------------------------------------------------------- #
# Contrato do setup (read-only, defaults aditivos p/ degradação graciosa)
# --------------------------------------------------------------------------- #
@dataclass
class ContribFamilia:
    # Contribuição de UMA família ao score — torna a decomposição visível peso a peso (D-02).
    # Strings (`familia`/`detalhe`) são chaves estáveis NEUTRAS, NUNCA copy imperativa (D-06).
    familia: str          # "tendencia" | "risco_retorno" | "padroes" | "momentum" | "volume"
    sub_score: float      # ∈ [0,1] — a leitura crua da família
    peso: int             # do config (35/20/20/15/10)
    contribuicao: float   # sub_score * peso → pontos no total (decomposição peso-a-peso, D-02)
    detalhe: str          # rótulo neutro de origem ("alta+forte", "duplo_fundo:confirmado", ...)


@dataclass
class SetupSwing:
    # Veredito de setup de swing — score + grade + decomposição. Tudo de ESTUDO, nunca ordem.
    score: float                                       # 0-100, já com penalização multi-TF
    grade: str                                         # "Forte"|"Moderado"|"Fraco"|"Sem setup"
    decomposicao: list = field(default_factory=list)   # [ContribFamilia, ...]
    gate_rr_ok: bool = False                           # passou no gate de R:R? (distinto do floor)
    rr_valor: float | None = None                      # razão retorno/risco recomputada (ou None)
    conflito_mtf: bool = False                         # penalização multi-TF aplicada (D-07)
    # Níveis de ESTUDO (referência, jamais ordem) — só repassa o que Niveis já tem.
    entrada_zona: tuple | None = None
    stop: float | None = None
    alvo: float | None = None


# Mapa fixo de direção de cada padrão (geometria do detector da Fase 14, A9): de alta vs de baixa.
_PADROES_ALTA = ("duplo_fundo", "oco_invertido")
_PADROES_BAIXA = ("duplo_topo", "oco")


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


# --------------------------------------------------------------------------- #
# Gate de R:R — recomputado dos campos BRUTOS de Niveis sob np.errstate
# (idioma de indicators._niveis_stop_rr L846-867; NÃO parsear o string risco_retorno)
# --------------------------------------------------------------------------- #
def _rr_valor(niveis) -> float | None:
    """Razão retorno/risco protegida; None se indisponível (lateral/risco<=0/não-finito)."""
    if niveis.entrada_zona is None or niveis.stop is None or niveis.alvo is None:
        return None
    low, high = niveis.entrada_zona
    entrada_ref = (low + high) / 2.0
    risco = abs(entrada_ref - niveis.stop)
    retorno = abs(niveis.alvo - entrada_ref)
    with np.errstate(divide="ignore", invalid="ignore"):
        razao = np.divide(retorno, risco)        # risco==0 → inf (não exceção, sob errstate)
    if risco <= 0 or not np.isfinite(razao):
        return None
    return float(razao)


# --------------------------------------------------------------------------- #
# Sub-scores por família ∈ [0,1] — lê SÓ rótulos discretos (idioma _checklist)
# Direção do setup = contexto.dow_diario ("alta"/"baixa"). Valores ASSUMED/calibráveis.
# --------------------------------------------------------------------------- #
def _sub_tendencia(contexto, forca, tendencia, direcao: str) -> tuple[float, str]:
    # base direcional (dow alinhado à direção) + bônus de força (ADX) + bônus de posição vs MM200.
    if direcao not in ("alta", "baixa"):
        return 0.0, "lateral"
    base = 0.6  # dow direcional já vale a maior parte (tendência é a família dominante)
    if getattr(forca, "forca_adx", None) == "forte":
        base += 0.25
    mm = getattr(tendencia, "posicao_mm200", None)
    if (direcao == "alta" and mm == "acima") or (direcao == "baixa" and mm == "abaixo"):
        base += 0.15
    sub = _clamp01(base)
    detalhe = f"{direcao}+{getattr(forca, 'forca_adx', 'na')}"
    return sub, detalhe


def _sub_risco_retorno(rr_valor: float, sc: dict) -> tuple[float, str]:
    # normaliza a razão acima do mínimo até o alvo (clamp [0,1]); já passou o gate aqui.
    lo = sc["rr_minimo"]
    hi = sc["rr_alvo"]
    span = hi - lo
    sub = _clamp01((rr_valor - lo) / span) if span > 0 else 1.0
    return sub, f"rr={rr_valor:.1f}".replace(".", ",")


def _sub_padroes(padroes, direcao: str) -> tuple[float, str]:
    # padrão COERENTE com a direção do dow pontua (confirmado 1.0 / em_formacao 0.5);
    # incoerente pontua 0 (não negativo, Open Q3); lista vazia → 0. Usa o máximo.
    lista = padroes.lista if padroes is not None else []
    coerentes = _PADROES_ALTA if direcao == "alta" else _PADROES_BAIXA if direcao == "baixa" else ()
    melhor = 0.0
    detalhe = "nenhum"
    for p in lista:
        if p.tipo not in coerentes:
            continue
        valor = 1.0 if p.estado == "confirmado" else 0.5
        if valor > melhor:
            melhor = valor
            detalhe = f"{p.tipo}:{p.estado}"
    return melhor, detalhe


def _sub_momentum(momentum, direcao: str) -> tuple[float, str]:
    # direção-aware (Pitfall 5): em alta, MACD cruz_alta confirma e RSI não-sobrecomprado confirma;
    # em baixa, espelhado (MACD cruz_baixa + RSI não-sobrevendido). Cada confirmação vale 0.5.
    rsi = getattr(momentum, "nivel_rsi", None)
    macd = getattr(momentum, "cruzamento_macd", None)
    sub = 0.0
    if direcao == "alta":
        if macd == "cruz_alta":
            sub += 0.5
        if rsi not in ("sobrecomprado", "indisponivel", None):
            sub += 0.5
    elif direcao == "baixa":
        if macd == "cruz_baixa":
            sub += 0.5
        if rsi not in ("sobrevendido", "indisponivel", None):
            sub += 0.5
    return _clamp01(sub), f"macd:{macd}"


def _sub_volume(volume) -> tuple[float, str]:
    if volume is None:
        return 0.0, "nenhum"
    if getattr(volume, "rompimento_com_volume", False):
        return 1.0, "rompimento_com_volume"
    if getattr(volume, "volume_acima_mm", False):
        return 0.5, "volume_acima_mm"
    return 0.0, "nenhum"


# --------------------------------------------------------------------------- #
# Montagem do SetupSwing (gate ANTES da grade — Pitfall 3)
# --------------------------------------------------------------------------- #
def montar_setup(sinais, cfg) -> SetupSwing:
    """Read-only: lê SinaisTecnicos, devolve SetupSwing. Degrada para "Sem setup", nunca levanta."""
    # 1. guard de borda → "Sem setup" neutro (todos os sub-objetos têm default None, aditivos)
    if sinais is None or sinais.niveis is None or sinais.contexto is None:
        return SetupSwing(score=0.0, grade="Sem setup")
    sc = cfg["score"]
    pesos = sc["pesos"]
    niveis = sinais.niveis
    contexto = sinais.contexto

    # 2. R:R recomputado dos campos brutos + GATE DURO (D-03/D-04)
    rr = _rr_valor(niveis)
    if rr is None or rr < sc["rr_minimo"]:
        return SetupSwing(
            score=0.0, grade="Sem setup", gate_rr_ok=False, rr_valor=rr,
            entrada_zona=niveis.entrada_zona, stop=niveis.stop, alvo=niveis.alvo,
        )

    # 3. sub-scores por família ∈ [0,1] (direção do setup = dow_diario)
    direcao = getattr(contexto, "dow_diario", "indisponivel")
    sub_t, det_t = _sub_tendencia(contexto, sinais.forca, sinais.tendencia, direcao)
    sub_r, det_r = _sub_risco_retorno(rr, sc)
    sub_p, det_p = _sub_padroes(sinais.padroes, direcao)
    sub_m, det_m = _sub_momentum(sinais.momentum, direcao)
    sub_v, det_v = _sub_volume(sinais.volume)

    decomposicao = [
        ContribFamilia("tendencia", sub_t, pesos["tendencia"], sub_t * pesos["tendencia"], det_t),
        ContribFamilia("risco_retorno", sub_r, pesos["risco_retorno"], sub_r * pesos["risco_retorno"], det_r),
        ContribFamilia("padroes", sub_p, pesos["padroes"], sub_p * pesos["padroes"], det_p),
        ContribFamilia("momentum", sub_m, pesos["momentum"], sub_m * pesos["momentum"], det_m),
        ContribFamilia("volume", sub_v, pesos["volume"], sub_v * pesos["volume"], det_v),
    ]

    # 4. soma ponderada (0-100, pois pesos somam 100 e sub ∈ [0,1])
    score_base = sum(c.contribuicao for c in decomposicao)

    # 5. penalização multi-TF (penaliza, NUNCA é causa única de "Sem setup" — D-07)
    conflito = getattr(contexto, "alinhamento_mtf", None) == "conflito"
    score = score_base * (1 - sc["penalidade_conflito_mtf"]) if conflito else score_base

    # 6. grade por cortes do config (floor < fraco → "Sem setup", Open Q1)
    cg = sc["cortes_grade"]
    if score >= cg["forte"]:
        grade = "Forte"
    elif score >= cg["moderado"]:
        grade = "Moderado"
    elif score >= cg["fraco"]:
        grade = "Fraco"
    else:
        grade = "Sem setup"

    return SetupSwing(
        score=score, grade=grade, decomposicao=decomposicao,
        gate_rr_ok=True, rr_valor=rr, conflito_mtf=conflito,
        entrada_zona=niveis.entrada_zona, stop=niveis.stop, alvo=niveis.alvo,
    )
