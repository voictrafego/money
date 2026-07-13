---
phase: 04-rim-com-valor-terminal-ke-revisado
plan: 01
subsystem: core/motores (RIM) + config + report dispatch
tags: [rim, valor-terminal, valuation, banco, CAL-01, CAL-02, tdd]
requires:
  - "core/ddm.py::valor_gordon (primitiva de perpetuidade, reuso)"
  - "core/motores.py::rim (D-02 baseline substituído)"
provides:
  - "motores.rim() híbrido com valor terminal (perpetuidade de Gordon sobre RI terminal)"
  - "ResultadoRIM.vp_terminal"
  - "config.yaml::motores.rim.{excesso_sustentavel,g_terminal,ke_g_spread_min} + ke_teto 0.13"
  - "gate duro de teste ITUB4 R$32-40 (unit + integração via report.py)"
affects:
  - "report._intrinseco_por_motor (ramo motor=='rim')"
  - "veredito do ITUB4/financeiras (intrínseco RIM ~R$23 → ~R$32,9)"
tech-stack:
  added: []
  patterns:
    - "RIM multiestágio (CFA L2 / Ohlson): janela explícita de RI + continuing value"
    - "guarda anti-bad-bank: fade_para = ke + min(roe0−ke, cap) sem clampar a ≥ ke"
    - "reuso de primitiva testada (ddm.valor_gordon) em vez de reimplementar perpetuidade"
    - "knobs config-driven, zero magic constant no corpo do motor"
key-files:
  created: []
  modified:
    - "src/analista/core/motores.py"
    - "config.yaml"
    - "src/analista/report/report.py"
    - "tests/test_motores.py"
    - "tests/test_vulc3_regressao.py"
decisions:
  - "ke_teto revisado 0.14→0.13 (CAL-02): Selic-ciclo já embute risco-país → erp_banco=0.045 sem double-count; move ITUB4 ~R$2"
  - "valor terminal é a alavanca principal (CAL-01); Ke é ajuste fino secundário — confirma a tese do research"
  - "g_terminal=0.025 declarado localmente (espelha ddm.g_estavel) por independência do motor, sem acoplar blocos"
metrics:
  duration: 0h04m
  completed: "2026-07-12"
---

# Phase 4 Plan 01: RIM com Valor Terminal + Ke Revisado Summary

RIM ganhou um valor terminal (perpetuidade de Gordon sobre o Residual Income terminal, via reuso de `ddm.valor_gordon`), substituindo a estrutura fade-para-Ke-sem-terminal (D-02) que ancorava bancos de qualidade no VPA — o ITUB4 sai de ~R$23 para ~R$32,9, dentro do gate duro R$32–40, com o Ke revisado (ke_teto 0.14→0.13) como ajuste fino secundário.

## What Was Built

- **`motores.rim()` híbrido multiestágio** (CAL-01): nova assinatura backward-safe com `excesso_sustentavel`, `g_terminal`, `ke_g_spread_min`. A janela explícita converge para um excesso sustentável limitado (`fade_para = ke + min(roe0−ke, cap)`) e o RI terminal é capitalizado como perpetuidade de Gordon descontada. `ResultadoRIM` ganhou `vp_terminal`.
- **Guarda anti-bad-bank**: `min(roe0−ke, cap)` sem clampar a ≥ ke — banco com ROE < Ke valua abaixo do book (P/B < 1), RI terminal negativo, `vp_terminal ≤ 0`.
- **`config.yaml`**: `ke_teto` 0.14→0.13 (CAL-02) + três knobs novos (`excesso_sustentavel=0.045`, `g_terminal=0.025`, `ke_g_spread_min=0.03`), cada um com o WHY documentado; comentário estagnado do `n_fade` (que dizia "~R$28 … NÃO ~R$40") reescrito para refletir a realidade pós-fase (~R$39,2 golden / ~R$32,9 live).
- **`report._intrinseco_por_motor`**: o ramo `motor=="rim"` passa os novos knobs lidos de `cfg` (leitura defensiva, defaults reproduzem D-02).
- **Gates de teste** (a falha do v2.2 era não cobrar o número): `test_rim_itub4_live_alvo_32_40` (gate duro unit, lê knobs de config + `ke_rim==0.13`), `test_rim_itub4_dispatch_banda` (gate de integração via `report.py`, prova que os knobs chegam ao funil), `test_rim_bad_bank_abaixo_do_book` (guarda anti-bad-bank).

## TDD Cycle

- **RED** (commit `9b96ed1`, `test(04-01)`): golden reescrito + 3 testes novos. Falha confirmada — `TypeError` (args novos ausentes), `ke_rim(1.29)==0.14≠0.13`, e o dispatch medindo exatamente **R$23,006** (o baseline D-02 que o research previu).
- **GREEN** (commit `53d2154`, `feat(04-01)`): terminal implementado, knobs em config, dispatch estendido. Suíte RIM verde; ITUB4 live R$32,87, golden R$39,23, bad-bank R$15,54.
- **REFACTOR**: nenhum necessário.

## Verified Numbers (batem com o research)

| Caso | Inputs | Intrínseco | vp_terminal |
|------|--------|-----------|-------------|
| ITUB4 live | vpa0=19, roe0=0.193, ke=0.13, ret=0.533, n=10 | R$32,87 | 5,73 (~17%) |
| Golden fixo | vpa0=22, roe0=0.193, ke=0.125, ret=0.53, n=10 | R$39,23 | 7,18 |
| Bad bank | vpa0=22, roe0=0.10 < ke=0.125 | R$15,54 (P/B≈0,71) | −2,76 |
| ROE==Ke | vpa0=22, roe0=ke=0.125 | R$22,00 (invariante) | 0,0 |
| Dispatch (report.py) | ITUB4 live-like via analisar_acao | R$32,87 | — |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Doc] Docstring de módulo de `motores.py` atualizado**
- **Found during:** Task 2
- **Issue:** A linha de resumo do RIM no docstring de módulo (linhas 9-13) ainda descrevia "sem prêmio terminal … fade até o Ke e o valor ancora no VPA (D-02)", factualmente errado após esta fase.
- **Fix:** Reescrito para RIM híbrido multiestágio com valor terminal + nota do ke_teto 0.13 (CAL-02). Não estava no `<action>` da Task 2, mas o plano exigia docstrings honestos; alinhado à mesma intenção do reescrever-comentário-do-n_fade.
- **Files modified:** `src/analista/core/motores.py`
- **Commit:** `53d2154`

## Task 3 (invariantes) — verificação sem delta de arquivo

Task 3 é uma tarefa de confirmação (rodar a suíte completa e checar os invariantes HARD do SC#4). Não gerou mudança de código, portanto não há commit próprio — a confirmação é o resultado da execução:
- **Suíte completa:** 440 passed, 0 failed.
- **Invariantes-chave** (`test_ddm.py` + `test_vulc3_regressao.py` + firewall selo↛report + `test_motores.py`): 30 passed.
- **Arquivos proibidos** (`ddm.py`/`selo.py`/`lentes.py`): intocados — confirmado por `git diff --name-only`.
- **TAEE11** (rota DDM): baseline idêntico (capstone verde).

## Authentication Gates

Nenhum.

## Known Stubs

Nenhum. Os três knobs novos são valores calibráveis (ponto de partida honesto), não stubs — a recalibração contra a cesta é a Fase 5 (BACKTEST-01), documentada em config e no research.

## Self-Check: PASSED

- `src/analista/core/motores.py` — FOUND (rim com vp_terminal + terminal via ddm.valor_gordon)
- `config.yaml` — FOUND (excesso_sustentavel + ke_teto 0.13)
- `src/analista/report/report.py` — FOUND (dispatch com novos knobs)
- Commit `9b96ed1` (RED) — FOUND
- Commit `53d2154` (GREEN) — FOUND
- Suíte completa: 440 passed, 0 failed
