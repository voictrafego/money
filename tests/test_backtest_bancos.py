"""Gate determinístico do BACKTEST-01 (VAL-01/VAL-02) — a metade 'teste' da entrega D-09.

Trava, OFFLINE e sobre o snapshot congelado (`tests/fixtures/snapshot_bancos_2026-07-12.yaml`),
o gate **quórum-3/4-±15%** (D-06/D-07/D-08) do RIM calibrado na Fase 4 contra as faixas de
consenso aprovadas (`tests/fixtures/fair_values_bancos.yaml`). Reusa a MESMA `rodar_cesta` do
script (`scripts/backtest_bancos.py`) → prova o mesmo número; a fórmula RIM não é reimplementada.

D-12 (loop de falha) — estado ATUAL do snapshot congelado:

    ITUB4  32.88  ∈ 30.50–50.00 ±15%  → PASS
    BBAS3  45.60  > 39×1.15            → FAIL (acima do teto de consenso)
    BBSE3  25.38  < 33×0.85            → FAIL (abaixo do piso de consenso)
    BBDC4  10.47  < 15×0.85            → FAIL (abaixo do book)

Apenas 1/4 na banda — ABAIXO do quórum 3/4. Isto NÃO é a "4ª exceção documentável" (D-08): são
3 falhas, não 1. O gate `test_backtest_gate_quorum_e_anotacao` REPROVA de propósito e está marcado
`xfail(strict=True)` — o gate NÃO é afrouxado, a banda ±15% e o quórum 3/4 permanecem intactos; a
reprovação é o achado que dispara o loop D-12 (recalibrar a Fase 4). Ver `05-04-SUMMARY.md`.
`strict=True` é o tripwire: quando a Fase 4 recalibrar e a cesta cruzar o quórum, este teste vira
XPASS→FAIL, forçando a REMOÇÃO do marcador e o FECHAMENTO explícito do loop (nunca silencioso).
"""

from __future__ import annotations

import os

import pytest
import yaml

from analista.backtest import (
    BANDA_PASS,  # D-07: reusa a MESMA banda do harness (fonte única, zero número solto)
    carregar_fair_values,
    carregar_snapshot,
    rodar_cesta,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# D-08: quórum de bancos dentro da banda ±15% para a calibração "generalizar" na cesta.
QUORUM_MIN = 3

_SNAPSHOT = os.path.join(ROOT, "tests", "fixtures", "snapshot_bancos_2026-07-12.yaml")
_FAIR_VALUES = os.path.join(ROOT, "tests", "fixtures", "fair_values_bancos.yaml")

# Piso/teto absolutos do RIM calibrado do ITUB4 (Fase 4: live R$32,87, gate duro 30–40).
# Convenção de tolerância do repo = bounds absolutos, NÃO pytest.approx.
_ITUB4_RIM_MIN = 30.0
_ITUB4_RIM_MAX = 40.0


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _rodar() -> list[dict]:
    """Roda a cesta congelada via o MESMO harness do script (offline, determinístico)."""
    empresas, rf_local = carregar_snapshot(_SNAPSHOT)
    fair_values = carregar_fair_values(_FAIR_VALUES)
    return rodar_cesta(empresas, fair_values, _cfg(), rf_local)


def test_backtest_cesta_rota_por_ticker():
    """Roteamento por ticker: ITUB4 → arquétipo financeira, motor RIM na faixa 30–40.

    NÃO assume RIM cegamente para os demais: se algum ticker rotear ≠ rim, tolera SÓ se a FV
    daquele ticker tiver `excecao_nota` (D-08). Hoje os 4 roteiam para RIM (snapshot).
    """
    res = _rodar()
    por_ticker = {r["ticker"]: r for r in res}

    itub = por_ticker["ITUB4"]
    assert itub["arquetipo"] == "financeira"
    assert itub["motor"] == "rim"
    assert itub["rim"] is not None
    assert _ITUB4_RIM_MIN <= itub["rim"] <= _ITUB4_RIM_MAX

    # Nenhum roteamento ≠ rim pode ser silencioso: exige nota de exceção documentada (D-08).
    for r in res:
        if r["motor"] != "rim":
            assert r["excecao_nota"], (
                f"{r['ticker']} roteado para '{r['motor']}' (≠ rim) sem nota de exceção → rota silenciosa"
            )


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "D-12: cesta 1/4 na banda ±15% (só ITUB4) < quórum 3/4 — a calibração RIM da Fase 4 NÃO "
        "generaliza para BBAS3/BBSE3/BBDC4. Gate NÃO afrouxado (banda/quórum intactos); reprovação "
        "é o achado que reabre a Fase 4 (loop). Ver 05-04-SUMMARY.md. Quando a Fase 4 recalibrar e a "
        "cesta cruzar o quórum, este teste vira XPASS→FAIL — remover o marcador e fechar o loop."
    ),
)
def test_backtest_gate_quorum_e_anotacao():
    """Gate D-06/D-07/D-08: quórum 3/4 dentro da banda ±15% + regra de anotação da 4ª exceção.

    Trava as 4 situações: 4/4 PASS → verde trivial; 3 PASS + 1 anotada → verde (exceção documentada);
    3 PASS + 1 silenciosa → FAIL do assert da nota (FAIL silencioso barrado, D-08); ≤2 PASS → FAIL do
    quórum (calibração não generaliza → loop D-12). O teste NÃO julga o texto da nota, só exige presença.
    """
    res = _rodar()

    passes = [r for r in res if r["passa"]]
    falhas = [r for r in res if not r["passa"]]

    # Quórum numérico: a maioria da cesta precisa cair na banda ±15% da faixa de consenso (D-08).
    assert len(passes) >= QUORUM_MIN, (
        f"quórum não atingido: {len(passes)}/{len(res)} na banda ±{BANDA_PASS:.0%} "
        f"(reprovam: {sorted(r['ticker'] for r in falhas)}) → loop D-12"
    )

    # Cada falha DEVE estar anotada — desvio sem nota = FAIL silencioso (D-08).
    for r in falhas:
        assert r["excecao_nota"], (
            f"{r['ticker']} fora da banda sem nota de exceção → FAIL silencioso"
        )


def test_backtest_determinismo():
    """O snapshot congelado não deriva: duas execuções do harness dão o MESMO RIM por ticker.

    Espelha o determinismo de reexecução de test_vulc3_regressao.py; bounds absolutos (igualdade
    exata do float reconstruído), não pytest.approx. Prova que o gate é reprodutível (offline).
    """
    rim_1 = {r["ticker"]: r["rim"] for r in _rodar()}
    rim_2 = {r["ticker"]: r["rim"] for r in _rodar()}
    assert rim_1 == rim_2
