---
phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia
plan: 01
subsystem: engine-normalizacao
tags: [payout, mediana, valuation, primitiva-pura, statistics, tdd]

# Dependency graph
requires:
  - phase: 08-normalizacao-do-lucro
    provides: "primitiva pura base_normalizada + _limpar + invariante de pureza (sem ciclo de import)"
provides:
  - "normalizacao.mediana_payout — primitiva pura do payout sustentável (mediana sobre série completa, sem janela 3a, sem clamp 1.0)"
  - "goldens unitários travando D-01/D-03/D-04 (no-clamp >1.0, descarte de spike, fronteira None)"
affects: [09-02, payout_valuation, dy_recorrente, fundamentals]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Irmã de base_normalizada: mesma escada de fallback (vazio->None, 1 ponto->valor) mas regra de mediana pura sobre TODOS os pontos válidos"

key-files:
  created: []
  modified:
    - src/analista/core/normalizacao.py
    - tests/test_normalizacao.py

key-decisions:
  - "Nome da primitiva fixado como mediana_payout (D-discretion do CONTEXT)"
  - "Sem parâmetro de janela e sem clamp: série completa + mediana pura (D-03/D-04)"

patterns-established:
  - "Primitiva de payout pura: _limpar -> vazio?None -> 1?valor -> float(median(limpos)); sem winsor, sem janela"

requirements-completed: [PAY-01]

# Metrics
duration: 2min
completed: 2026-06-27
---

# Phase 9 Plan 01: Primitiva mediana_payout (núcleo do payout sustentável) Summary

**Primitiva pura `mediana_payout` em normalizacao.py — mediana do payout sobre a série histórica completa, sem janela de 3a e sem clamp em 1.0, travada por goldens (TAEE11 >100% preservado, spike descartado pela mediana).**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-27T21:33:16Z
- **Completed:** 2026-06-27T21:34:46Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Goldens unitários RED para `mediana_payout` cobrindo D-01/D-03/D-04 (no-clamp >1.0, descarte de spike via mediana, série completa vs. 3a, ignora None, fronteira vazio/só-None/valor único).
- Primitiva pura `mediana_payout(valores)` implementada como irmã de `base_normalizada`: reusa `_limpar`, mesma escada de fallback, mediana pura sobre todos os pontos válidos — sem janela, sem `min(..., 1.0)`.
- Invariante de pureza (`test_primitiva_e_pura_sem_import_de_fundamentals`) segue verde; suite completa 155 testes verdes (sem regressões).

## Task Commits

Cada task commitada atomicamente:

1. **Task 1: Goldens unitários da mediana de payout (RED)** - `42d5cff` (test)
2. **Task 2: Implementar a primitiva pura mediana_payout (GREEN)** - `f737f74` (feat)

_Ciclo TDD: test (RED) -> feat (GREEN). Refactor não necessário._

## Files Created/Modified
- `tests/test_normalizacao.py` - 5 goldens novos para `mediana_payout` (no-clamp >1.0, descarte de spike, série completa, ignora None, fronteira None/valor único).
- `src/analista/core/normalizacao.py` - nova função pura `mediana_payout(valores)` (mediana sobre série completa, sem clamp, reusando `_limpar`).

## Decisions Made
- Nome `mediana_payout` (discricionário do planner, fixado em D-discretion).
- Sem clamp e sem parâmetro de janela: a primitiva recebe a série completa e devolve a mediana pura — D-03 (mediana legítima >1.0, ex. TAEE11 ≈ 2.16) e D-04 (série completa, não 3a).

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
- O interpretador `python` não está no PATH; usado `.venv/bin/python` (env do projeto) para rodar pytest. Sem impacto no código.

## Threat Surface
- T-09-01 (Tampering numérico: clamp acidental que distorce o valuation) mitigado pelos goldens de no-clamp >1.0, descarte de spike e fronteira None (Task 1/2). Sem nova superfície de rede/auth/IO — função pura offline.

## Next Phase Readiness
- `mediana_payout` pronta e travada por golden para ser consumida por `payout_valuation` e `dy_recorrente` no Plan 02 (sem ciclo de import).
- Pureza preservada; nenhum import da engine adicionado.

## Self-Check: PASSED
- FOUND: src/analista/core/normalizacao.py
- FOUND: tests/test_normalizacao.py
- FOUND commit: 42d5cff (RED)
- FOUND commit: f737f74 (GREEN)

---
*Phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia*
*Completed: 2026-06-27*
