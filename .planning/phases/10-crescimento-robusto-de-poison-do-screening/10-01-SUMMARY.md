---
phase: 10-crescimento-robusto-de-poison-do-screening
plan: 01
subsystem: core
tags: [growth, numpy, log-linear, valuation, regression]

# Dependency graph
requires:
  - phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia
    provides: serie_lucro_normalizada / camada de normalização winsorizada reusada como entrada do g
provides:
  - "Estimador puro growth.crescimento_log_linear(serie) -> Number (OLS de ln, g=exp(slope)-1)"
  - "g_historico em report.py agora vem da tendência log-linear sobre a série de lucro normalizada (não mais CAGR endpoint-a-endpoint)"
  - "Fonte única de g pronta para reuso pelo screening (Plan 02, GROW-02)"
affects: [10-02 (screening reusa o estimador), 10-03 (rebaseline deliberado de golden)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Estimador robusto de série como função pura irmã de cagr/crescimento_aritmetico (recebe a série inteira, devolve Number, só numpy/statistics, sem ciclo de import)"

key-files:
  created:
    - tests/test_growth.py
  modified:
    - src/analista/core/growth.py
    - src/analista/report/report.py

key-decisions:
  - "g_historico = exp(slope)-1 de OLS de ln(série) sobre a série NORMALIZADA, usando todos os pontos (D-01)"
  - "Fronteira de None idêntica ao CAGR: série None/len<2/qualquer ponto None ou <=0 -> None; sem fallback aritmético (D-03)"
  - "Theil-Sen e média aparada de YoY rejeitados como over-engineering para <=8-10 pontos já winsorizados (D-02)"
  - "Estimador é a fonte única Analisar<->Screening por construção (D-04)"

patterns-established:
  - "Estimador de crescimento de série como primitiva pura em growth.py, espelhando cagr/crescimento_aritmetico"

requirements-completed: [GROW-01]

# Metrics
duration: 12min
completed: 2026-06-27
---

# Phase 10 Plan 01: Crescimento robusto do g histórico (log-linear) Summary

**g_historico passa a vir de regressão log-linear (OLS de ln, g=exp(slope)-1) sobre a série de lucro normalizada inteira — um único ano de fundo/topo deixa de mandar no g exibido — preservando a fronteira de None do CAGR e g_alto/g_fundamentos/per-ano CRU intactos.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-27T23:13Z
- **Completed:** 2026-06-27
- **Tasks:** 2
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments
- Função pura `crescimento_log_linear(serie) -> Number` em `growth.py`: OLS de `ln(série)` contra o tempo via `numpy.polyfit`, g anualizado = `exp(slope) - 1`, sem ciclo de import (só numpy).
- Golden unitário `tests/test_growth.py` cobrindo PG +10%/-10% exata, série constante (g=0.0, não None), ano <=0 / ponto None -> None e len<2 -> None.
- Swap in-place do `g_historico` em `report.py`: de `growth.cagr(lucros[0], lucros[-1], …)` para `growth.crescimento_log_linear(lucros)` sobre a mesma série `serie_lucro_normalizada()`; downstream (g_alto, g_fundamentos, lucro CRU per-ano) preservado.
- Suíte completa verde: 166 testes (incl. test_growth_reconciliacao desigualdades e test_report golden de valor) sem regressão.

## Task Commits

Cada tarefa committada atomicamente:

1. **Task 1 (RED): golden falho do estimador** - `fa51bb7` (test)
2. **Task 1 (GREEN): crescimento_log_linear puro** - `aba533d` (feat)
3. **Task 2: swap g_historico CAGR -> log-linear** - `e751537` (feat)

_Task 1 seguiu TDD (test -> feat). Refactor não foi necessário._

## Files Created/Modified
- `tests/test_growth.py` - Golden unitário do estimador (slope conhecido + fronteira de None).
- `src/analista/core/growth.py` - `import numpy as np` + função pura `crescimento_log_linear`.
- `src/analista/report/report.py` - `g_historico` calculado pelo estimador log-linear sobre a série normalizada; comentário do bloco Crescimento atualizado.

## Decisions Made
None - seguiu o plano (D-01..D-04, D-07) como especificado.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `python`/`python3` do sistema não têm pandas; os testes rodam com o interpretador do venv do projeto (`.venv/bin/python`). Sem impacto no código.

## TDD Gate Compliance
- RED gate: `fa51bb7` (test) com falha confirmada (AttributeError: sem `crescimento_log_linear`).
- GREEN gate: `aba533d` (feat) com `tests/test_growth.py` verde (6 passed).

## Next Phase Readiness
- Estimador `crescimento_log_linear` pronto para reuso pelo screening (Plan 02, GROW-02 — `cagr_serie` em `screening.py` a substituir sobre séries normalizadas de lucro/dividendos/FCO).
- Golden de VALOR EXATO afetados pela troca de estimador continuam verdes nesta fase; o rebaseline deliberado (caso necessário) está reservado para 10-03/T2 — sem gate contraditório aqui.

## Self-Check: PASSED
- FOUND: src/analista/core/growth.py (`def crescimento_log_linear`)
- FOUND: tests/test_growth.py
- FOUND: src/analista/report/report.py (`growth.crescimento_log_linear(lucros)`)
- FOUND: commit fa51bb7, aba533d, e751537

---
*Phase: 10-crescimento-robusto-de-poison-do-screening*
*Completed: 2026-06-27*
