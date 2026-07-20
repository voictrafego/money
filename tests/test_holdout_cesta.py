"""VAL-02/03 — composição da cesta estratificada do hold-out (o Commit 1 do D-09).

Testa o SUBSTRATO, não a engine: o `holdout_v24.yaml` é uma cesta HONESTA — estratificada por
arquétipo (≥6 por estrato quando o universo permite), com 10 "difíceis" deliberados disjuntos
da cota, e ZERO `excecao_nota` (a lavanderia do v2.3, morta na Fase 14 / VAL-06 — o fixture novo
não nasce com ela). A ordem load-bearing (fair_value cravado ANTES de `v_modelo`, D-09) é provada
por `git blame` em `test_holdout_ordem_git`, não por este teste de composição.

Sem literal de ticker (BLIND-04a): as verdades são ESTRUTURAIS (contagens, presença/ausência de
chave), nunca `ticker == valor em reais`.
"""

from __future__ import annotations

import collections

import pytest
import yaml

import helpers_blindagem as h

# Estratos com universo < 6 no snapshot dos 104 (CRESCIMENTO tem 4 nomes): usam todos e MARCAM
# a cota não atingida (D-07). A cota mínima é a mesma do montador.
COTA_MINIMA = 6
MIN_DIFICEIS = 10


def _carregar_cesta() -> dict:
    dados = yaml.safe_load(h.HOLDOUT_V24.read_text(encoding="utf-8")) or {}
    return {k: v for k, v in dados.items() if isinstance(v, dict)}


@pytest.mark.contrato
def test_holdout_estratificado_composicao():
    """A cesta é estratificada, tem 10 difíceis disjuntos, e é livre de lavanderia (VAL-06).

    Cinco verdades estruturais:

      1. SEM LAVANDERIA — nenhuma entrada tem `excecao_nota` (a lavanderia VAL-06 não pode
         renascer pelo novo substrato). A ORDEM fair_value-antes-de-v_modelo (D-09) é provada
         por HISTÓRIA em test_holdout_ordem_git (git blame), não por ausência de conteúdo:
         depois do Commit 2 o v_modelo legitimamente existe.

      2. COTA POR ESTRATO — cada estrato ou tem ≥6 membros de cota (dificil=false) OU está
         inteiramente MARCADO `cota_incompleta` (universo < 6, D-07: usa todos, não inventa).

      3. CRESCIMENTO é o estrato raso conhecido: existe, < 6, e vem MARCADO (honesto).

      4. DIFÍCEIS — ≥10 entradas `dificil=true`, disjuntas da cota por CONSTRUÇÃO (cada ticker
         aparece uma vez, com um único `dificil` bool: cota e difícil são estados exclusivos).

      5. DEGRADAÇÃO D-03 — toda entrada SEM `fair_value` tem `lentes: []` (nenhuma lente valeu):
         a degradação é representada, nunca uma exclusão silenciosa.
    """
    cesta = _carregar_cesta()
    assert cesta, "holdout_v24.yaml vazio ou ausente"

    entradas = list(cesta.values())

    # 1. Sem lavanderia (VAL-06) --------------------------------------------------- #
    # A ORDEM fair_value-antes-de-v_modelo (D-09) é provada por HISTÓRIA em
    # test_holdout_ordem_git (git blame por linha), não por ausência de conteúdo — depois do
    # Commit 2 (Plano 04) o v_modelo LEGITIMAMENTE existe. O que permanece invariante aqui é a
    # pureza VAL-06: nenhuma entrada pode renascer com `excecao_nota` (a lavanderia do v2.3).
    assert all("excecao_nota" not in e for e in entradas), (
        "o fixture do hold-out não nasce com excecao_nota (VAL-06): nenhuma exceção pode salvar "
        "um ticker pelo novo substrato."
    )

    # 4. Difíceis (calculado antes para separar cota de difícil) ------------------- #
    dificeis = [e for e in entradas if e.get("dificil")]
    cota = [e for e in entradas if not e.get("dificil")]
    assert len(dificeis) >= MIN_DIFICEIS, (
        f"a cesta precisa de ≥{MIN_DIFICEIS} difíceis deliberados (D-06); tem {len(dificeis)}"
    )

    # 2. Cota por estrato: ≥6 OU inteiramente marcado cota_incompleta -------------- #
    cota_por_estrato = collections.Counter(e["arquetipo"] for e in cota)
    marcados = collections.defaultdict(list)
    for e in entradas:
        marcados[e["arquetipo"]].append(bool(e.get("cota_incompleta")))
    for estrato, n in cota_por_estrato.items():
        if all(marcados[estrato]):
            # estrato raso (universo < 6): usa todos, MARCA a cota — honesto (D-07).
            assert n < COTA_MINIMA, (
                f"estrato {estrato} marcado cota_incompleta mas tem {n} de cota (≥{COTA_MINIMA})"
            )
        else:
            assert n >= COTA_MINIMA, (
                f"estrato {estrato} com universo suficiente deve ter ≥{COTA_MINIMA} na cota; tem {n}"
            )

    # 3. CRESCIMENTO é o estrato raso conhecido, marcado ------------------------------ #
    assert "crescimento" in cota_por_estrato, "CRESCIMENTO ausente da cesta"
    assert all(marcados["crescimento"]), "CRESCIMENTO deveria vir MARCADO cota_incompleta (D-07)"
    assert cota_por_estrato["crescimento"] < COTA_MINIMA, (
        "CRESCIMENTO deveria ter < 6 (universo raso) e estar marcado, não inventar nomes"
    )

    # 5. Degradação D-03: sem fair_value ⇒ sem lente ------------------------------- #
    for e in entradas:
        if "fair_value" not in e:
            assert e.get("lentes") == [], (
                "entrada sem fair_value deveria ter lentes: [] (D-03, degradação reportada)"
            )
