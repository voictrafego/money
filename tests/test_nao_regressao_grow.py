"""Não-regressão da cura do `g` (Fase 11) contra o MAPA REAL dos 104 tickers.

A memória `ddm-nao-consertar-e-lente-nao-motor` registra que mexer no `g` da perpetuidade
QUEBROU historicamente TAEE11/BBSE3/VULC3 (intrínseco None/absurdo/explosão). A validação tem
de ser contra o SNAPSHOT REAL congelado dos 104 (produto do código consertado,
`hs.CAMINHO_SNAPSHOT_LIMPO`), NÃO contra as fixtures sintéticas — essas exercitam patologias já
corrigidas em fases anteriores, não o dado de verdade.

O `g_cap` (~7,28%) da Fase 11 encolhe o spread `Ke − g` (Armadilha 5): estes testes provam que,
sobre o mapa real, ele NÃO regride — TAEE11/BBSE3/VULC3 produzem valuation finito, positivo e
sensato, e nenhum dos 104 (menos as falhas de mercado) vira NaN/inf ou levanta exceção. Um
`None` é aceitável (motor pendente / dado degenerado); um NaN/inf ou exceção NÃO é.

Tudo OFFLINE/determinístico: os macro-inputs são carimbados com os defaults de config (sem
rede), espelhando `backtest.rodar_cesta`. BLIND-04a-safe: os tickers sensíveis são asseridos só
por finitude/positividade (sem nível em reais); o limite superior de sanidade vive na varredura
do universo, que não nomeia ticker nenhum.
"""

from __future__ import annotations

import math

import helpers_blindagem as hb
import helpers_sanidade as hs
from analista.report import report

# Tickers historicamente sensíveis à mudança de `g` (memória ddm-nao-consertar): a régua que a
# cura do `g` NÃO pode regredir. Cada um roteia para um motor diferente (regulada/DDM,
# seguradora/Gordon-franquia, cíclica/normalizado) — cobrem três caminhos do dispatch.
SENSIVEIS = ("TAEE11", "BBSE3", "VULC3")

# Limite superior GENEROSO de sanidade (não um nível calibrado): pega explosão de perpetuidade
# (Gordon perto da singularidade Ke≈g) sem constranger o nível. Usado SÓ na varredura do
# universo (que não nomeia ticker) para ficar BLIND-04a-safe.
FATOR_SANIDADE = 50.0


def _cfg_offline() -> dict:
    """Config de produção com os macro-inputs carimbados OFFLINE (determinístico, sem rede).

    Espelha `backtest.rodar_cesta`: o `rf` vem do fallback (Selic), e o `pi_ciclo` do default do
    config — a engine deriva um `g_cap` determinístico e permanece pura.
    """
    cfg = hb.carregar_config_producao()
    cfg["capm"]["rf_local"] = cfg["capm"]["selic_fallback"]
    cfg.setdefault("macro", {})["pi_ciclo"] = cfg["macro"].get("pi_ciclo")
    return cfg


def _valor_efetivo(a) -> float | None:
    """A valuation EFETIVA de um arquétipo, sem assert (helper que CONSTRÓI, não confere).

    O motor primário grava `intrinseco_motor` (banco/seguradora/cíclica/compounder). A REGULADA
    (TAEE11) usa o DDM como MOTOR-lente: seu `intrinseco_motor` é None por arquitetura e a
    valuation vive na banda `vmin/vmax` (Ke×g). Devolve o motor quando presente, senão o meio da
    banda do DDM, senão None (motor pendente / dado degenerado — aceitável na varredura).
    """
    if a.intrinseco_motor is not None:
        return a.intrinseco_motor
    if a.vmin is not None and a.vmax is not None:
        return (a.vmin + a.vmax) / 2.0
    return None


def test_tickers_sensiveis_nao_regridem_sob_o_g_novo():
    """TAEE11/BBSE3/VULC3 do mapa REAL: valuation FINITA e POSITIVA sob o `g_cap` da Fase 11.

    O `g` novo não pode produzir None/absurdo/exceção nesses 3 casos historicamente sensíveis
    (Armadilha 5 / memória ddm-nao-consertar). Assert só de finitude/positividade — sem cravar
    nenhum nível em reais (BLIND-04a-safe). O limite superior de sanidade é a varredura abaixo.
    """
    empresas = hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO)
    falhas = hs.falhas_do_snapshot(hs.CAMINHO_SNAPSHOT_LIMPO)
    cfg = _cfg_offline()

    for tk in SENSIVEIS:
        assert tk in empresas and tk not in falhas, (
            f"{tk} ausente/degradado no mapa real — a régua sensível precisa dele presente"
        )
        a = report.analisar_acao(empresas[tk], cfg)
        valor = _valor_efetivo(a)
        assert valor is not None, (
            f"{tk} (motor '{a.motor}') NÃO produziu valuation sob o g novo: "
            f"intrinseco_motor={a.intrinseco_motor}, banda=({a.vmin}, {a.vmax}) — regressão"
        )
        assert math.isfinite(valor) and valor > 0, (
            f"{tk} (motor '{a.motor}') produziu valuation não-finita/não-positiva: {valor}"
        )


def test_varredura_dos_104_sem_nan_inf_ou_excecao():
    """Varredura barata do universo REAL: nenhum dos 104 (menos as falhas de mercado) pode virar
    NaN/inf ou levantar exceção sob o `g_cap`. Um None é aceitável (motor pendente/dado
    degenerado); um NaN/inf/exceção NÃO é. Sem ticker literal ⇒ o limite de sanidade (FATOR)
    fica BLIND-04a-safe. Reporta a lista de ofensores na mensagem do assert.
    """
    empresas = hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO)
    falhas = hs.falhas_do_snapshot(hs.CAMINHO_SNAPSHOT_LIMPO)
    cfg = _cfg_offline()

    ofensores: list[str] = []
    for tk, c in empresas.items():
        if tk in falhas:
            continue
        try:
            a = report.analisar_acao(c, cfg)
        except Exception as e:  # noqa: BLE001 — a engine é never-raise; qualquer exceção é ofensor
            ofensores.append(f"{tk}: EXCECAO {e!r}")
            continue
        valor = _valor_efetivo(a)
        if valor is None:
            continue  # None é aceitável (motor pendente / dado degenerado)
        if not math.isfinite(valor) or valor <= 0:
            ofensores.append(f"{tk}: valor não-finito/não-positivo {valor}")
        elif c.preco_atual and valor >= FATOR_SANIDADE * c.preco_atual:
            ofensores.append(f"{tk}: valor absurdo {valor} (>= {FATOR_SANIDADE}x preco)")

    assert not ofensores, (
        "a cura do `g` produziu valuation não-finita/absurda/exceção no mapa real dos 104:\n  "
        + "\n  ".join(sorted(ofensores))
    )
