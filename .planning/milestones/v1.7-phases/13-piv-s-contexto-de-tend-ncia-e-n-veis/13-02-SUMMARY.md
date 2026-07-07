---
phase: 13-piv-s-contexto-de-tend-ncia-e-n-veis
plan: 02
subsystem: engine
tags: [dow, trend, multi-timeframe, resample, w-fri, indicators, no-network]

# Dependency graph
requires:
  - phase: 13-piv-s-contexto-de-tend-ncia-e-n-veis
    provides: "Pivos + _pivos (pivot_high/pivot_low confirmados) consumidos pelo Dow"
provides:
  - "ContextoTendencia dataclass (dow_diario + alinhamento_mtf) + campo aditivo SinaisTecnicos.contexto"
  - "_dow(pivos, ohlc, cfg): rótulo de Dow no diário (alta/baixa/lateral/indisponivel) via sequência HH/HL + desempate MM/ADX (D-05)"
  - "_contexto(ohlc, cfg): alinhamento semanal→diário por resample W-FRI do próprio frame (D-04, sem rede)"
affects: [13-03-sr-fibonacci-niveis, 13-04-stop-rr, 14-padroes, 15-score]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Rótulo de Dow por sequência de pivôs confirmados (HH+HL→alta, LH+LL→baixa) com desempate por inclinação/ADX já existentes (D-05, sem reimplementar)"
    - "Semanal derivado por resample W-FRI do próprio frame (D-04, zero nova chamada de rede), guardado por DatetimeIndex+OHLC espelhando report.py"
    - "Conflito multi-TF como rótulo aditivo e auditável — modula, nunca bloqueia (D-06)"

key-files:
  created: []
  modified:
    - src/analista/core/indicators.py
    - tests/test_indicators.py

key-decisions:
  - "Desempate de Dow reusa adx_wilder (corte 20) + regressao_trailing (zona morta de 5%/ano) — não reimplementa ADX/SMA (D-05)"
  - "Alinhamento: lado 'indisponivel' propaga 'indisponivel'; qualquer divergência (inclusive um lado 'lateral') → 'conflito'"
  - "_contexto é 100% aditivo: conflito jamais zera/levanta/altera as demais famílias de SinaisTecnicos (D-06)"

patterns-established:
  - "Constantes de heurística documentadas no módulo (_DOW_ADX_MIN, _DOW_SLOPE_BAND) quando não há param de config dedicado"

requirements-completed: [TREND-01, TREND-02]

# Metrics
duration: ~10min
completed: 2026-06-29
---

# Phase 13 Plan 02: Contexto de Tendência (Dow + Alinhamento Semanal→Diário) Summary

**A engine agora rotula a tendência do diário pela sequência de Dow sobre os pivôs do plano 01 (HH/HL com desempate por MM/ADX) e o alinhamento semanal→diário derivado por resample W-FRI do próprio frame — tudo aditivo a `SinaisTecnicos`, com o conflito multi-TF como rótulo que modula e nunca bloqueia (D-06).**

## Performance

- **Duration:** ~10 min
- **Tasks:** 2/2
- **Files modified:** 2 (indicators.py, tests/test_indicators.py)
- **Tests:** 212 baseline → 225 (13 novos goldens), 100% verde

## Accomplishments
- `ContextoTendencia` dataclass (`dow_diario`, `alinhamento_mtf`) + campo aditivo `SinaisTecnicos.contexto` (default None) — contrato travado 100% retrocompatível.
- `_dow(pivos, ohlc, cfg)` (TREND-01): topos+fundos confirmados crescentes (HH+HL) → `"alta"`; decrescentes (LH+LL) → `"baixa"`; sequência ambígua → desempate reusando `adx_wilder` (≥20 = há tendência) + sinal da `regressao_trailing` com zona morta de 5%/ano → `"lateral"`; ADX/slope NaN → `"indisponivel"`. Determinístico.
- `_contexto(ohlc, cfg)` (TREND-02): semanal por resample W-FRI do próprio frame (D-04, sem nova chamada de rede), recomputa `_pivos`+`_dow` no semanal e rotula `alinhamento_mtf` em `{alinhado_alta, alinhado_baixa, conflito, indisponivel}`. Guard `DatetimeIndex` + colunas OHLC espelha `report.py` (degrada para `"indisponivel"` sem exceção).
- D-06 provado em golden: em conflito as demais famílias (`tendencia`/`forca`/`canais`) seguem normalmente preenchidas — o setup NÃO é bloqueado.

## Task Commits

1. **Task 1: Dow no diário (RED)** - `8ed5af9` (test)
2. **Task 1: Dow no diário (GREEN)** - `453d0c8` (feat)
3. **Task 2: Alinhamento semanal→diário (RED)** - `868aa52` (test)
4. **Task 2: Alinhamento semanal→diário (GREEN)** - `4fd069a` (feat)

_TDD: cada task seguiu RED (test) → GREEN (feat); nenhum refactor necessário._

## Files Created/Modified
- `src/analista/core/indicators.py` - `ContextoTendencia` dataclass; campo aditivo `SinaisTecnicos.contexto`; constantes `_DOW_ADX_MIN`/`_DOW_SLOPE_BAND`; funções `_dow` e `_contexto`; montagem de `contexto` em `calcular`.
- `tests/test_indicators.py` - 13 novos goldens: Dow (alta HH/HL, baixa LH/LL, lateral por ADX fraco, desempate por rampa, frame curto indisponivel, determinismo); alinhamento (alinhado_alta, alinhado_baixa, conflito-não-bloqueia, frame não-datetime indisponivel, calcular popula contexto, degradação None, grep guard D-04 W-FRI/sem-1wk).

## Decisions Made
- **Desempate de Dow por slope+ADX com zona morta:** o corte de ADX (20) reusa a semântica de `_forca`; a zona morta de 5%/ano na inclinação anualizada (`_DOW_SLOPE_BAND`) é o que torna "claramente positivo/negativo" robusto — uma oscilação de lado (slope ~0) cai para `"lateral"` mesmo com ADX numericamente alto.
- **Propagação de `indisponivel`:** se diário OU semanal é `"indisponivel"` (frame curto, semanal com < ~90 barras para o desempate), o alinhamento é `"indisponivel"` — não é divergência, é ausência de dado.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Docstring de `_contexto` continha o literal `1wk`**
- **Found during:** Task 2 (fase GREEN)
- **Issue:** O critério de aceite exige `grep -n "1wk" indicators.py` vazio (D-04); a docstring justificava a proibição usando o literal `1wk`, fazendo o grep retornar match e o golden `test_sem_fetch_semanal_1wk` falhar.
- **Fix:** Reescrita a justificativa como "sem buscar o timeframe semanal do Yahoo" (mesmo padrão do `find_peaks` no plano 01) — proibição preservada, grep vazio.
- **Files modified:** src/analista/core/indicators.py
- **Committed in:** `4fd069a` (parte do commit GREEN da Task 2)

---

**Total deviations:** 1 auto-fixed (1 Rule 3)
**Impact on plan:** Necessária para o critério de aceite (grep limpo). Sem scope creep.

## Issues Encountered
None — fora do auto-fix acima.

## TDD Gate Compliance
- Task 1: RED `8ed5af9` (test) → GREEN `453d0c8` (feat). OK.
- Task 2: RED `868aa52` (test) → GREEN `4fd069a` (feat). OK.
- Nenhum teste passou inesperadamente na fase RED (falharam por `AttributeError`/contexto None/grep antes da implementação).

## Verification
- `.venv/bin/python -m pytest tests/ -q` → **225 passed** (baseline 212 + 13 novos; nenhum golden existente alterado, 191 fundamentalistas intactos).
- `grep -n "1wk" src/analista/core/indicators.py` → vazio (D-04).
- `indicators.py` contém `W-FRI` e `_dow`/`_contexto`; `SinaisTecnicos.contexto` populado por `calcular`.
- D-06 verde: em conflito as demais famílias seguem preenchidas (não bloqueia).

## Known Stubs
None — `ContextoTendencia` é totalmente populado via `calcular`. O consumo do contexto pelo score (modulação por conflito) é a Fase 15 (escopo declarado, não stub).

## Self-Check: PASSED
- `src/analista/core/indicators.py` modificado e contém `def _dow` e `def _contexto` (FOUND).
- `tests/test_indicators.py` contém goldens de `dow` e `alinhamento` (FOUND).
- Commits `8ed5af9`, `453d0c8`, `868aa52`, `4fd069a` presentes no log (FOUND).
- Suíte 225 verde (FOUND).
