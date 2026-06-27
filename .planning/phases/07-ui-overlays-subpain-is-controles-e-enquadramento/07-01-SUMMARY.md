---
phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
plan: 01
subsystem: api
tags: [report, indicators, degradation, pandas, pytest, technical-analysis]

# Dependency graph
requires:
  - phase: 06-integra-o-na-engine-composite-alerta-cli
    provides: "analisar_acao popula a.sinais/timing/matriz_leitura; SinaisTecnicos por família; markdown da CLI"
provides:
  - "Degradação holística em report.analisar_acao: not a.timing_resumo ⇒ matriz_leitura='' (sem leitura técnica fabricada, CR-01)"
  - "Guarda do markdown por 'not a.timing_resumo' (IN-01) cobrindo o caso só-de-força; sem linha de matriz vazia (IN-02)"
  - "Guarda do resample W-FRI por DatetimeIndex + colunas OHLC (WR-01)"
  - "Campo aditivo SinaisTecnicos.close (split-adjusted), read-only, para os marcadores de evento da UI (UI-04)"
affects: [ui-overlays, subpaineis-controles, enquadramento, marcadores-de-evento]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Degradação holística: nenhum campo derivado afirma estado quando o read técnico degrada"
    - "Campo aditivo (default None) em dataclass de contrato travado, espelhando Canais.donchian_sup_55"

key-files:
  created: []
  modified:
    - src/analista/report/report.py
    - src/analista/core/indicators.py
    - tests/test_report.py
    - tests/test_indicators.py

key-decisions:
  - "A guarda real do caso só-de-força é o markdown ('not a.timing_resumo'); o campo matriz_leitura já era '' com veredito vazio, então o golden trava a degradação pelo render."
  - "WR-01 reusa indicators._COLUNAS_OHLC para o set de colunas (DRY), em vez de literal duplicado."
  - "close exposta como a MESMA pd.Series já usada nos indicadores (sem cópia/recálculo) — read-only por construção."

patterns-established:
  - "Degradação holística: quando timing_resumo=='' todos os derivados (matriz/markdown) colapsam coerentemente."
  - "Campos aditivos em SinaisTecnicos entram com default None para preservar o contrato travado no plan 05-01."

requirements-completed: [UI-04, UI-06]

# Metrics
duration: ~12min
completed: 2026-06-27
---

# Phase 7 Plan 01: Saneamento da degradação + exposição da close Summary

**Degradação holística em report.analisar_acao (matriz_leitura colapsa com o timing; guarda de markdown/resample) e SinaisTecnicos.close split-adjusted exposta read-only — os dois habilitadores de engine da UI da Fase 7.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-06-27
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- CR-01 resolvido: o caso só-de-força (ADX indisponível com MM200 disponível, série achatada) deixa de fabricar uma leitura técnica — `matriz_leitura` colapsa junto com `timing_resumo` e o markdown mostra "Histórico de preços insuficiente para o read técnico." em vez de um timing vazio.
- IN-01/IN-02 resolvidos: guarda do markdown por `not a.timing_resumo` (remove a condição morta `timing_estado==""`) e supressão da linha de matriz vazia.
- WR-01 resolvido: o resample W-FRI só roda com `DatetimeIndex` + colunas OHLC presentes; caso contrário cai no frame original e a degradação de `indicators.calcular` (ponto único) cuida do resto.
- UI-04 habilitado: `SinaisTecnicos.close` (campo aditivo, default None) carrega a close split-adjusted já usada pelos indicadores, read-only, para os marcadores de evento da UI.
- Suíte completa 136 verde (133 baseline + 3 golden novos); nenhum golden de valuation rebaselineado (TEST-07 preservado).

## Task Commits

Each task was committed atomically:

1. **Task 1: Degradação holística em report.py (CR-01/IN-02/WR-01)** — `d14f983` (test, RED) → `a5e7156` (feat, GREEN)
2. **Task 2: Expor a close (split-adjusted) em SinaisTecnicos** — `25710a2` (test, RED) → `e17e66b` (feat, GREEN)
3. **Task 3: Golden de borda da close vazia + gate da suíte inteira** — `4994064` (test)

_TDD tasks 1 e 2 têm dois commits cada (test → feat)._

## Files Created/Modified
- `src/analista/report/report.py` — degradação holística (`not a.timing_resumo ⇒ matriz_leitura=''`), guarda de markdown por `not a.timing_resumo`, supressão de matriz vazia, guarda do resample W-FRI por `DatetimeIndex` + colunas OHLC; `import pandas as pd` adicionado.
- `src/analista/core/indicators.py` — campo aditivo `close: pd.Series = None` em `SinaisTecnicos`; `calcular` preenche `close=close`.
- `tests/test_report.py` — `_ohlc_achatado` + `test_degradacao_so_de_forca` (campos + markdown da degradação só-de-força).
- `tests/test_indicators.py` — `test_sinais_close_paridade` (close == ohlc["Close"]) e `test_sinais_close_frame_vazio` (frame vazio/None → close Series vazia).

## Decisions Made
- A asserção de campo `matriz_leitura==''` no golden só-de-força passa trivialmente com veredito vazio; o que efetivamente trava o fix (e era RED antes do fix) são as asserções de markdown — por isso o golden combina ambos os níveis.
- WR-01 reusa `indicators._COLUNAS_OHLC` para checar as colunas (evita literal duplicado).
- `close` exposta como a própria série já usada (sem cópia/recálculo): read-only por construção, alinhado ao princípio "app.py read-only não recalcula método".

## Deviations from Plan

None - plan executed exactly as written.

A estrutura do plano lista `test_degradacao_so_de_forca` e a paridade da close tanto nas tarefas TDD (1 e 2) quanto na Task 3. Para evitar commits redundantes e honrar o TDD, os goldens centrais entraram como fase RED das tarefas 1 e 2; a Task 3 adicionou o golden de borda (close de frame vazio — segundo bullet de comportamento da Task 2) e serviu de gate da suíte completa. Nenhuma mudança de escopo.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Engine pronta para a UI da Fase 7: estado degradado COERENTE (UI-06) e `a.sinais.close` read-only para os marcadores de evento (UI-04).
- Nenhuma fórmula de valuation/indicador alterada; contrato `SinaisTecnicos` preservado (campo aditivo).

## Self-Check: PASSED

- Arquivos verificados: 07-01-SUMMARY.md, src/analista/report/report.py, src/analista/core/indicators.py — todos presentes.
- Commits verificados: d14f983, a5e7156, 25710a2, e17e66b, 4994064 — todos presentes.
- Suíte: 136 passed.

---
*Phase: 07-ui-overlays-subpain-is-controles-e-enquadramento*
*Completed: 2026-06-27*
