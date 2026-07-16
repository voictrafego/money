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


def test_nenhuma_rota_diferente_de_rim_e_silenciosa():
    """INVARIANTE (WR-04 / D-08): nenhum roteamento ≠ 'rim' na cesta pode ser SILENCIOSO — todo
    motor diferente de RIM exige uma nota de exceção documentada. Estrutural: não depende de NÍVEL
    de R$ nenhum.

    Extraído do golden de nível `test_backtest_cesta_rota_por_ticker` (banda R$30–40,
    `_ITUB4_RIM_MIN/MAX`), DELETADO na Fase 10 (PRIM-05): a banda de nível morreu, a guarda de
    roteamento-não-silencioso SOBREVIVE (WR-04). Sem ticker literal, sem constante em reais.
    """
    for r in _rodar():
        if r["motor"] != "rim":
            assert r["excecao_nota"], (
                f"{r['ticker']} roteado para '{r['motor']}' (≠ rim) sem nota de exceção → rota silenciosa"
            )


def test_nenhuma_reprovacao_de_banda_e_silenciosa():
    """INVARIANTE (WR-04 / D-08): uma REPROVAÇÃO de banda nunca pode ser silenciosa — todo ticker
    fora da sua faixa de consenso exige `excecao_nota`.

    É a metade ESTRUTURAL do antigo gate de quórum (`test_backtest_gate_quorum_e_anotacao`,
    DELETADO na Fase 10 PRIM-05). O CONTADOR de quórum (`len(passes) >= QUORUM_MIN`) era um golden
    de NÍVEL — dependia dos alvos de consenso do `fair_values_bancos`, exatamente o que as
    primitivas consertadas movem — e morre. A disciplina de anotação (nenhum FAIL passa
    despercebido, D-08) não depende de nível e SOBREVIVE. Sem ticker literal, sem constante em reais.
    """
    for r in _rodar():
        if not r["passa"]:
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
