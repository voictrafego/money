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
nota de rota do v2.3 [REMOVIDA na Fase 14 / VAL-06: nenhuma nota pode salvar um ticker] (motor≠rim exige nota, D-08). O `xfail(strict=True)` que travava a
reprovação de propósito foi REMOVIDO ao cruzar o quórum (fechamento explícito do loop, D-07). Ver
`04-02-SUMMARY.md`, `04-03-SUMMARY.md` e `05-04-SUMMARY.md`.
"""

from __future__ import annotations

import os

import yaml

from analista.report import report
from analista.backtest import (
    carregar_fair_values,
    carregar_snapshot,
    rodar_cesta,
)
from analista.core import motores

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_SNAPSHOT = os.path.join(ROOT, "tests", "fixtures", "snapshot_bancos_2026-07-12.yaml")
_FAIR_VALUES = os.path.join(ROOT, "tests", "fixtures", "fair_values_bancos.yaml")


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _rodar() -> list[dict]:
    """Roda a cesta congelada via o MESMO harness do script (offline, determinístico)."""
    empresas, rf_local, ipca_defl = carregar_snapshot(_SNAPSHOT)
    fair_values = carregar_fair_values(_FAIR_VALUES)
    return rodar_cesta(empresas, fair_values, _cfg(), rf_local, ipca_defl)


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
    empresas, rf_local, ipca_defl = carregar_snapshot(_SNAPSHOT)
    cfg = _cfg()
    cfg = {  # espelha rodar_cesta (rf_local + ipca_deflatores carimbados)
        **cfg,
        "capm": {**cfg.get("capm", {}), "rf_local": rf_local},
        "macro": {**cfg.get("macro", {}), "ipca_deflatores": ipca_defl or {}},
    }
    return {c.ticker: report.analisar_acao(c, cfg) for c in empresas}


def test_backtest_rotulo_do_motor_consistente():
    """CR-01 (fidelidade de método = Core Value): o rótulo exibido do motor casa com o motor real.

    REWRITE (Fase 13/ENG-01): sob o RIM ÚNICO a rota própria de seguradora MORREU — TODO ticker
    da cesta (bancos E a seguradora capital-light) roteia para o MESMO `motores.rim`, então
    `a.motor == "rim"` e `a.motor_rotulo == MOTOR_ROTULO["rim"]` para todos. A chave `seguradora`
    saiu de `MOTOR_ROTULO`.
    """
    analises = _analises_por_ticker()

    for tk in ("ITUB4", "BBAS3", "BBDC4", "BBSE3"):
        a = analises[tk]
        assert a.motor == "rim"
        assert a.motor_rotulo == motores.MOTOR_ROTULO["rim"]
