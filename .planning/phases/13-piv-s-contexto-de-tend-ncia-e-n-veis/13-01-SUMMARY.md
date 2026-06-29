---
phase: 13-piv-s-contexto-de-tend-ncia-e-n-veis
plan: 01
subsystem: engine
tags: [pivots, fractal-williams, atr, wilder, no-repaint, indicators, swing]

# Dependency graph
requires:
  - phase: 12-ingest-o-intraday-timeframe
    provides: FrameOHLC (ohlc nominal + ohlc_ajustado) consumido por indicators.calcular
provides:
  - "Pivos dataclass + _pivos (fractal de Williams, no-repaint causal) populando SinaisTecnicos.pivos"
  - "Helper publico atr_wilder(ohlc, length) reusando o TR ja calculado na cadeia do ADX"
  - "Forca.atr exposto aditivamente; config indicadores.pivo_n=2 e stop_atr_m=1.5"
affects: [13-02-dow-tendencia, 13-03-sr-fibonacci-niveis, 13-04-stop-rr, 14-padroes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fractal de Williams como deteccao de pivos no-repaint (janela simetrica, lag de N barras)"
    - "Exposicao de ATR via helper publico reusando o TR do ADX (zero recalculo, D-08)"

key-files:
  created: []
  modified:
    - src/analista/core/indicators.py
    - config.yaml
    - tests/test_indicators.py

key-decisions:
  - "Pivo confirmado so quando t+N fecha -> no-repaint trivial e determinístico (D-01/D-03)"
  - "Strict via unico maximo/minimo na janela [i-N..i+N] (sum(jan==v)==1)"
  - "atr_wilder e a fonte unica do ATR; adx_wilder refatorado p/ chamar o helper, assinatura (adx,pdi,ndi) intacta"

patterns-established:
  - "Campo aditivo opcional (default None) em dataclass travado -> 191 goldens intactos"
  - "Gate no-repaint por truncacao como teste obrigatorio de toda serie causal nova"

requirements-completed: [PIVOT-01]

# Metrics
duration: ~12min
completed: 2026-06-29
---

# Phase 13 Plan 01: Pivôs (fractal de Williams) + ATR exposto Summary

**Dois primitivos no-repaint destravam a Fase 13: detecção determinística de pivôs (swing highs/lows) pelo fractal de Williams e o ATR exposto a partir do TR já calculado na cadeia do ADX — tudo 100% aditivo ao contrato SinaisTecnicos.**

## Performance

- **Duration:** ~12 min
- **Tasks:** 2/2
- **Files modified:** 3 (indicators.py, config.yaml, tests/test_indicators.py)
- **Tests:** 202 baseline → 212 (10 novos goldens), 100% verde

## Accomplishments
- `Pivos` dataclass + `_pivos`: fractal de Williams causal, com GATE de no-repaint por truncação (D-03) provado em golden; as últimas N barras nunca são pivô confirmado; degradação graciosa (frame < 2N+1 → NaN/None).
- `atr_wilder(ohlc, length)` exposto reusando exatamente o TR/suavização internos do ADX (D-08); `adx_wilder` refatorado para chamar o helper preservando a assinatura `(adx, pdi, ndi)` — goldens de ADX inalterados.
- `Forca.atr` preenchido aditivamente; novos params em `config.yaml`: `pivo_n: 2`, `stop_atr_m: 1.5`.

## Task Commits

1. **Task 1: Pivôs fractal de Williams (RED)** - `123e91c` (test)
2. **Task 1: Pivôs fractal de Williams (GREEN)** - `d2f2212` (feat)
3. **Task 2: ATR exposto via atr_wilder (RED)** - `194abfb` (test)
4. **Task 2: ATR exposto via atr_wilder (GREEN)** - `39b6128` (feat)

_TDD: cada task seguiu RED (test) → GREEN (feat); nenhum refactor necessário._

## Files Created/Modified
- `src/analista/core/indicators.py` - dataclass `Pivos` + `_pivos`; helper `atr_wilder`; `adx_wilder` refatorado para reusar o helper; campos aditivos `SinaisTecnicos.pivos` e `Forca.atr`; montagem em `calcular`.
- `config.yaml` - bloco `indicadores`: `pivo_n: 2` e `stop_atr_m: 1.5` (com comentário do "porquê").
- `tests/test_indicators.py` - 10 novos goldens: gate no-repaint de pivôs, lag de confirmação, teeth (monotônica/V), degradação; consistência do ATR com o TR do ADX, 1º válido no índice `length`, degradação, assinatura do ADX intacta, params do config.

## Decisions Made
- **Strict via único extremo na janela:** topo = `High[i]` é o único máximo de `[i-N..i+N]` (`sum(jan==v)==1`); fundo análogo com mínimo. Equivale a "estritamente maior/menor que os N vizinhos de cada lado" e é robusto a empates.
- **`atr_wilder` como fonte única:** em vez de duplicar a fórmula, `adx_wilder` passou a chamar o helper — garante consistência por construção (1e-9) e cumpre D-08 (expor, não recalcular).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixture `_frame_pivos` sem coluna `Open`**
- **Found during:** Task 1 (fase GREEN)
- **Issue:** A fixture só tinha High/Low/Close; o guard de borda de `calcular` exige as 4 colunas OHLC (`_COLUNAS_OHLC` inclui `Open`), então `test_calcular_pivos` caía no frame vazio e os pivôs vinham vazios.
- **Fix:** Adicionada coluna `Open` (=Close) à fixture.
- **Files modified:** tests/test_indicators.py
- **Committed in:** `d2f2212` (parte do commit GREEN da Task 1)

**2. [Rule 3 - Blocking] Docstring continha o literal `find_peaks`**
- **Found during:** Task 1 (fase GREEN)
- **Issue:** O critério de aceite exige `grep -n "find_peaks" indicators.py` vazio (D-01); a docstring justificava a proibição usando o literal `scipy.signal.find_peaks`, o que faria o grep retornar match.
- **Fix:** Reescrita a justificativa como "detectores por prominência do scipy" sem o token literal — proibição preservada, grep vazio.
- **Files modified:** src/analista/core/indicators.py
- **Committed in:** `d2f2212`

---

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 3)
**Impact on plan:** Ambas necessárias para os critérios de aceite (cobertura do `calcular` + grep limpo). Sem scope creep.

## Issues Encountered
None — fora dos dois auto-fixes acima.

## TDD Gate Compliance
- Task 1: RED `123e91c` (test) → GREEN `d2f2212` (feat). OK.
- Task 2: RED `194abfb` (test) → GREEN `39b6128` (feat). OK.
- Nenhum teste passou inesperadamente na fase RED (ambas falharam por `KeyError`/`AttributeError` antes da implementação).

## Verification
- `.venv/bin/python -m pytest tests/ -q` → **212 passed** (baseline 202 + 10 novos; nenhum golden existente alterado).
- GATE no-repaint de pivôs por truncação verde (D-03).
- `grep -n "find_peaks" src/analista/core/indicators.py` → vazio (D-01).
- `grep -c "def atr_wilder"` → 1.

## Known Stubs
None — `Pivos` e `Forca.atr` estão totalmente populados via `calcular`. Os params `stop_atr_m` e os consumidores a jusante (Dow, S/R, stop, R:R) são planos subsequentes da Fase 13 (escopo declarado, não stubs).

## Self-Check: PASSED
- `src/analista/core/indicators.py` modificado e contém `def atr_wilder` e `def _pivos` (FOUND).
- `config.yaml` contém `pivo_n` e `stop_atr_m` (FOUND).
- Commits `123e91c`, `d2f2212`, `194abfb`, `39b6128` presentes no log (FOUND).
- Suíte 212 verde (FOUND).
