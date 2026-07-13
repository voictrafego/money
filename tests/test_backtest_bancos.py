"""Gate determinístico do BACKTEST-01 (VAL-01/VAL-02) — a metade 'teste' da entrega D-09.

Trava, OFFLINE e sobre o snapshot congelado (`tests/fixtures/snapshot_bancos_2026-07-12.yaml`),
o gate **quórum-3/4-±15%** (D-06/D-07/D-08) do RIM calibrado na Fase 4 contra as faixas de
consenso aprovadas (`tests/fixtures/fair_values_bancos.yaml`). Reusa a MESMA `rodar_cesta` do
script (`scripts/backtest_bancos.py`) → prova o mesmo número; a fórmula RIM não é reimplementada.

D-12 (loop FECHADO pela Alavanca 2 + rota de seguradora / Fase 4 it.2) — estado ATUAL do snapshot:

    ITUB4  32.88  ∈ 30.50–50.00 ±15%  → PASS (inalterado — o cap satura, não regride)
    BBAS3  43.89  ∈ 20.00–39.00 ±15%  → PASS (ROE terminal normalizado ao ciclo)
    BBDC4  13.37  ∈ 15.00–24.00 ±15%  → PASS (ROE terminal normalizado ao ciclo)
    BBSE3  39.87  ∈ 33.00–46.00 ±15%  → PASS (rota de seguradora — Gordon-franquia, motor≠rim)

4/4 na banda ±15% → o quórum 3/4 é atingido com folga e o loop D-12 fecha. A recalibração da Fase 4
(normalização through-cycle do ROE terminal, Alavanca 2) generalizou na cesta de bancos SEM afrouxar
o gate — a banda ±15% e o quórum 3/4 permanecem intactos. A BBSE3 (única não-banco) roteia por uma
rota própria de seguradora capital-light (Gordon-franquia sobre o dividendo sustentável, 04-03), com
`excecao_nota` documentando a rota (motor≠rim exige nota, D-08). O `xfail(strict=True)` que travava a
reprovação de propósito foi REMOVIDO ao cruzar o quórum (fechamento explícito do loop, D-07). Ver
`04-02-SUMMARY.md`, `04-03-SUMMARY.md` e `05-04-SUMMARY.md`.
"""

from __future__ import annotations

import os

import yaml

from analista.report import report
from analista.backtest import (
    BANDA_PASS,  # D-07: reusa a MESMA banda do harness (fonte única, zero número solto)
    carregar_fair_values,
    carregar_snapshot,
    rodar_cesta,
)
from analista.core import motores

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


def test_backtest_alvos_recalibrados():
    """Alavanca 2 (CAL-01/D-01): a normalização through-cycle do ROE terminal crava os alvos.

    Sobre o snapshot congelado, via o MESMO harness `rodar_cesta`, o RIM recalibrado aterrissa em
    ITUB4 ≈ 32,88 (INALTERADO — o cap satura, não regride), BBAS3 ≈ 43,89 (dentro de 17,00–44,85) e
    BBDC4 ≈ 13,37 (dentro de 12,75–27,60). Bounds absolutos ±R$0,20 (convenção do repo, NÃO approx).
    """
    por_ticker = {r["ticker"]: r for r in _rodar()}
    alvos = {"ITUB4": 32.88, "BBAS3": 43.89, "BBDC4": 13.37}
    for tk, alvo in alvos.items():
        rim = por_ticker[tk]["rim"]
        assert rim is not None, f"{tk}: RIM None"
        assert abs(rim - alvo) <= 0.20, f"{tk}: RIM {rim:.2f} != alvo {alvo:.2f} (±0,20)"


def test_backtest_determinismo():
    """O snapshot congelado não deriva: duas execuções do harness dão o MESMO RIM por ticker.

    Espelha o determinismo de reexecução de test_vulc3_regressao.py; bounds absolutos (igualdade
    exata do float reconstruído), não pytest.approx. Prova que o gate é reprodutível (offline).
    """
    rim_1 = {r["ticker"]: r["rim"] for r in _rodar()}
    rim_2 = {r["ticker"]: r["rim"] for r in _rodar()}
    assert rim_1 == rim_2


def _analises_por_ticker() -> dict:
    """ResultadoAnalise completo por ticker — expõe `motor_rotulo`, que `rodar_cesta` não retorna."""
    empresas, rf_local = carregar_snapshot(_SNAPSHOT)
    cfg = _cfg()
    cfg = {**cfg, "capm": {**cfg.get("capm", {}), "rf_local": rf_local}}  # espelha rodar_cesta
    return {c.ticker: report.analisar_acao(c, cfg) for c in empresas}


def test_backtest_rotulo_do_motor_consistente():
    """CR-01 (fidelidade de método = Core Value): o rótulo exibido do motor casa com o motor real.

    A BBSE3 roteia para o ramo de seguradora (Gordon-franquia), que MUTA `a.motor` DENTRO do
    dispatch. O `motor_rotulo` precisa refletir esse motor — não pode exibir o número da seguradora
    sob o rótulo do RIM (book-anchored). Trava a ordem correta (rótulo computado APÓS o dispatch) e
    a presença da chave `seguradora` em MOTOR_ROTULO.
    """
    analises = _analises_por_ticker()

    bbse = analises["BBSE3"]
    assert bbse.motor == "seguradora"
    assert bbse.motor_rotulo == motores.MOTOR_ROTULO["seguradora"]
    assert "RIM" not in bbse.motor_rotulo  # não atribuir o número Gordon-franquia ao RIM

    # Os bancos seguem RIM: o rótulo do motor casa com o motor primário do arquétipo.
    for tk in ("ITUB4", "BBAS3", "BBDC4"):
        a = analises[tk]
        assert a.motor == "rim"
        assert a.motor_rotulo == motores.MOTOR_ROTULO["rim"]
