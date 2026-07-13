---
phase: 04-rim-com-valor-terminal-ke-revisado
plan: 02
subsystem: core/motores (RIM) + report dispatch + config + gate BACKTEST-01
tags: [rim, valor-terminal, roe-through-cycle, banco, CAL-01, CAL-02, loop-d12, tdd]
requires:
  - "core/motores.py::rim (it.1 — valor terminal via ddm.valor_gordon)"
  - "core/fundamentals.py::CompanyData.roe(ano)/anos_ordenados (série histórica)"
  - "backtest.rodar_cesta (harness offline sobre o snapshot congelado)"
provides:
  - "motores.rim(roe_terminal=None) — normalização through-cycle do ROE SÓ no RI terminal (backward-safe)"
  - "report._roe_through_cycle (mediana|média dos c.roe(ano), never-raise <3 pts → None)"
  - "config.yaml::motores.rim.roe_terminal_stat (único knob novo da Alavanca 2)"
  - "tests/fixtures/fair_values_bancos.yaml::BBSE3.excecao_nota (exceção de arquétipo D-05)"
  - "gate test_backtest_gate_quorum_e_anotacao verde (xfail(strict) removido — loop D-12 fechado)"
affects:
  - "report._intrinseco_por_motor (ramo motor=='rim' injeta roe_terminal=roe_ciclo)"
  - "veredito de BBAS3 (45,60→43,89) e BBDC4 (10,47→13,37); ITUB4 inalterado (32,88)"
tech-stack:
  added: []
  patterns:
    - "normalização through-cycle do ROE terminal (Damodaran normalized ROE) capada por excesso_sustentavel"
    - "anchor sai da SÉRIE histórica via report (fronteira FIX-04), zero constante mágica no motor (D-08)"
    - "proteção por saturação do cap: roe_ciclo−ke ≥ cap ⇒ RI terminal idêntico ao legado (não regride)"
    - "gate que cobra o NÚMERO-ALVO com bounds absolutos ±R$0,20 (não pytest.approx)"
key-files:
  created: []
  modified:
    - "src/analista/core/motores.py"
    - "src/analista/report/report.py"
    - "config.yaml"
    - "tests/test_motores.py"
    - "tests/test_backtest_bancos.py"
    - "tests/fixtures/fair_values_bancos.yaml"
decisions:
  - "roe_terminal é o ÚLTIMO param de motores.rim (default None = legado bit-idêntico); goldens intactos"
  - "reversão terminal CHEIA ao ciclo (peso 1,0); mediana como estatística (robusta ao ROE-colapso de 1 ano)"
  - "BBSE3 fica como exceção documentada (3/4+1, D-05); rota própria de seguradora deferida ao 04-03"
metrics:
  duration: 0h18m
  completed: "2026-07-13"
---

# Phase 4 Plan 02: Recalibração RIM — Normalização through-cycle do ROE terminal Summary

A cesta de bancos agora cruza o quórum: o RIM ganhou uma **normalização through-cycle do ROE aplicada SÓ no valor terminal** (Alavanca 2, D-01) — o excesso do RI da perpetuidade de Gordon é ancorado na **mediana histórica do próprio ticker** e ainda capado por `excesso_sustentavel`. BBAS3 cai de 45,60 para 43,89, BBDC4 sobe de 10,47 para 13,37, e o **ITUB4 fica bit-idêntico (32,88)** porque seu excesso through-cycle satura o cap. Resultado: **3/4 na banda ±15% + BBSE3 como exceção de arquétipo documentada**, fechando o loop D-12 e removendo o `xfail(strict)` do gate.

## What Was Built

- **`motores.rim(..., roe_terminal=None)`** (Task 1): novo parâmetro opcional no FIM da assinatura (backward-safe). Quando `roe_terminal is not None`, a base do RI terminal é recomputada como `excesso_t = min(roe_terminal − ke, excesso_sustentavel)` sobre `B_{n-1}` (a mesma base de book do último RI da janela, capturada em `b_base_ri_final`). A janela explícita (`roe0`/`fade_para`) fica **INTOCADA** (Pitfall 1) — a normalização entra só na perpetuidade. `roe_terminal=None` reproduz o legado bit-a-bit.
- **`report._roe_through_cycle(c, rim_cfg)`** (Task 2): computa o ROE through-cycle = `mediana`|`media` dos `c.roe(ano)` sobre a série (filtrando os None). Never-raise: série com <3 pontos válidos → `None` (degrada para o legado). O ramo `motor=="rim"` de `_intrinseco_por_motor` passa `roe_terminal=roe_ciclo` — só neste ramo; os demais (normalizado/dcf/nav/ddm) e o ramo fronteiriço ficam intocados.
- **`config.yaml::motores.rim.roe_terminal_stat = "mediana"`** (Task 2): único knob novo da Alavanca 2, com o WHY documentado (o anchor sai da série, não é constante — D-08). Nenhum knob existente (`excesso_sustentavel`, `g_terminal`, `ke_teto`) foi tocado.
- **`test_backtest_alvos_recalibrados`** (Task 2): asserção AUTOMATIZADA (não inspeção manual) que roda `rodar_cesta` sobre o snapshot congelado e crava ITUB4 ≈ 32,88 / BBAS3 ≈ 43,89 / BBDC4 ≈ 13,37 com bounds absolutos ±R$0,20 — reusa o mesmo harness do gate.
- **`fair_values_bancos.yaml::BBSE3.excecao_nota`** (Task 3): a exceção de arquétipo D-05 (seguradora capital-light cujo valor está na franquia/fluxo, não no book minúsculo — o RIM ancorado em book a subvaloriza).
- **Fechamento do loop D-12** (Task 3): `@pytest.mark.xfail(strict=True)` removido de `test_backtest_gate_quorum_e_anotacao` (o gate cruzou 3/4 → XPASS→FAIL exigia a remoção, D-07/Pitfall 6); docstring do módulo do gate reescrito para o novo estado; `import pytest` (não mais usado) removido.

## TDD Cycle (Task 1)

- **RED** (commit `811f509`, `test(04-02)`): `test_rim_terminal_normalizado` escrito primeiro. Falha confirmada — `TypeError: rim() got an unexpected keyword argument 'roe_terminal'`.
- **GREEN** (commit `9f874ad`, `feat(04-02)`): parâmetro + bloco terminal normalizado implementados. Suíte `test_motores.py` verde (14 passed), incluindo o golden `test_rim_itub4_live_alvo_32_40` (não-regressão).
- **REFACTOR**: nenhum necessário.

## Verified Numbers (batem com o research §Alavanca 2)

| Ticker | RIM antes | RIM depois | Banda ±15% | Alavanca | Veredito |
|--------|-----------|-----------|------------|----------|----------|
| ITUB4 | 32,88 | **32,88** (inalterado) | 25,93–57,50 | — (cap satura) | ✅ PASS |
| BBAS3 | 45,60 | **43,89** | 17,00–44,85 | 2 (ROE terminal ciclo) | ✅ PASS (alto na banda) |
| BBDC4 | 10,47 | **13,37** | 12,75–27,60 | 2 (ROE terminal ciclo) | ✅ PASS |
| BBSE3 | 25,38 | 25,38 | 28,05–52,90 | — (exceção documentada) | ⚠️ FAIL anotado (D-05) |

→ **3/4 na banda + 1 exceção documentada** — cruza o quórum, fecha o loop D-12.

Prova de não-regressão do ITUB4 (por construção): o excesso through-cycle do ITUB4 (≈4,98pp) ≥ `excesso_sustentavel` (4,5pp) → `min(...)` satura no cap → RI terminal idêntico ao legado → RIM bit-idêntico. Coberto pelo caso (b) do `test_rim_terminal_normalizado` (igualdade < 1e-9).

## Deviations from Plan

None — plan executado exatamente como escrito. Os três alvos pré-computados (ITUB4 32,88 / BBAS3 43,89 / BBDC4 13,37) foram atingidos dentro de ±R$0,20 sem afrouxar knobs nem bounds.

### Correção auto-aplicada (housekeeping, não desvio de escopo)

**[Rule 3 - Blocking] `import pytest` removido de `test_backtest_bancos.py`**
- **Found during:** Task 3
- **Issue:** Após remover o `@pytest.mark.xfail`, `import pytest` ficou sem uso — potencial falha de lint em pre-commit hook.
- **Fix:** Removido o import junto com o decorator (mesma edição semântica do fechamento do loop).
- **Commit:** `ccb5a5b`

## Threat Surface Scan

Nenhuma nova superfície: mudança em funções numéricas puras, sem rede, sem I/O, sem input não-confiável novo (T-04-01 accept). Never-raise preservado (T-04-02 mitigate): `roe_ciclo=None` ou <3 pontos → `roe_terminal=None` (degrada para o legado); `rim` já retorna None sob input degenerado.

## Authentication Gates

Nenhum.

## Known Stubs

Nenhum. A rota própria de seguradora (BBSE3 → 4/4) é escopo explícito e deferido do plano **04-03** — documentada na `excecao_nota` do fixture, não é stub silencioso.

## Test Results

- `pytest tests/test_motores.py -q`: 14 passed (inclui `test_rim_terminal_normalizado` + golden ITUB4).
- `pytest tests/test_backtest_bancos.py -q`: 4 passed (gate verde, sem xfail; `grep -c pytest.mark.xfail` = 0).
- `pytest -q` (suíte completa): **445 passed, 0 failed, 0 xfailed** (baseline era 442 passed + 1 xfailed; +2 testes novos, xfail→pass).
- `ddm.py`/`selo.py`/`lentes.py`: intocados (confirmado por `git log --name-only`).

## Self-Check: PASSED

- `src/analista/core/motores.py` — FOUND (rim com roe_terminal)
- `src/analista/report/report.py` — FOUND (_roe_through_cycle + injeção no ramo rim)
- `config.yaml` — FOUND (roe_terminal_stat: "mediana")
- `tests/fixtures/fair_values_bancos.yaml` — FOUND (BBSE3.excecao_nota)
- Commit `811f509` (RED) — FOUND
- Commit `9f874ad` (GREEN motores) — FOUND
- Commit `5cd3b61` (report+config+backtest test) — FOUND
- Commit `ccb5a5b` (fecha loop D-12) — FOUND
- Suíte completa: 445 passed, 0 failed
