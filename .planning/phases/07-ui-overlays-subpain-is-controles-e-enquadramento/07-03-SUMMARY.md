---
phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
plan: 03
subsystem: ui
tags: [grafico, overlays, subpaineis, marcadores, plotly-contract, pure-functions, golden-tests]

# Dependency graph
requires:
  - phase: 05-c-lculo-dos-indicadores-t-cnicos
    provides: "SinaisTecnicos (séries pd.Series por família) via indicators.calcular"
  - phase: 07-ui-overlays-subpain-is-controles-e-enquadramento (07-01)
    provides: "SinaisTecnicos.close (split-adjusted) exposta read-only p/ marcadores"
provides:
  - "grafico.py: contrato puro de montagem do gráfico técnico (overlays/subpainéis/marcadores/layout)"
  - "estado_padrao() técnico OFF; overlays_preco()->[OverlaySpec]; subpaineis_ativos()->[SubpainelSpec]"
  - "marcadores_eventos()->[Marcador] nas datas exatas; leitura_tecnica_disponivel()"
  - "dataclasses OverlaySpec/SubpainelSpec/Marcador como contrato consumido pelo app.py (Plans 04/05)"
affects: [07-04, 07-05, app.py-render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Separação decisão↔render: a lógica de QUAIS overlays/subpainéis/marcadores vive em funções puras testáveis (golden), app.py vira fina camada de render"
    - "SPEC completo (série + níveis de referência) no módulo puro — app.py não mapeia nome→série nem hardcoda 20/25, 30/70, 0"
    - "_merge(estado) sobre estado_padrao() tolera estado parcial/inesperado da sessão (T-07-04)"

key-files:
  created:
    - src/analista/grafico.py
    - tests/test_grafico_ui.py
  modified: []

key-decisions:
  - "overlays_preco E subpaineis_ativos devolvem SPECS completos (série(s)+estilo/níveis) — simetria de testabilidade exigida pelo checker"
  - "Subpainel só entra quando toggle ON E série principal tem ≥1 ponto não-NaN (degradação DATA-03)"
  - "Ordem fixa dos subpainéis [adx, rsi, macd]; row_heights com preço dominante (0.55) somando 1.0"
  - "Marcadores varrem a série inteira (não só a última barra), espelhando as regras discretas de _tendencia/_canais"

patterns-established:
  - "Módulo puro sem streamlit/plotly: devolve dados/specs, não objetos de figura (grep import==0)"
  - "TDD RED→GREEN por task: test() falhando commitado antes de feat()"

requirements-completed: [UI-01, UI-02, UI-03, UI-04]

# Metrics
duration: 14min
completed: 2026-06-27
---

# Phase 7 Plan 03: Overlays, subpainéis, marcadores e enquadramento (contrato puro) Summary

**Toda a lógica de montagem do gráfico técnico (overlays no preço, subpainéis dinâmicos com série+níveis, marcadores de evento nas datas exatas, layout) extraída para funções puras e golden-cobertas em `grafico.py` — o app.py (Plans 04/05) vira fina camada de render.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-06-27T12:19Z
- **Completed:** 2026-06-27
- **Tasks:** 2/2
- **Files modified:** 2 (ambos criados)

## Accomplishments
- `grafico.py` (236 linhas) com 6 funções puras + 3 dataclasses de spec, sem dependência de streamlit/plotly.
- `estado_padrao()` com técnico OFF por padrão (UI-06): nenhum overlay/subpainel desenhado sem o usuário ligar.
- `overlays_preco`/`subpaineis_ativos` devolvem SPECS completos (série + estilo + níveis de referência) — o app.py não mapeia nome→série nem hardcoda 20/25, 30/70, 0.
- `marcadores_eventos` lê a.sinais + close e devolve golden/death cross e rompimentos Donchian nas datas exatas, com rótulo PT para hover.
- Degradação graciosa coberta por golden: série toda-NaN não cria subpainel; série curta/achatada ⇒ marcadores `[]` e `leitura_tecnica_disponivel` False.
- Suíte: 148 testes verdes (10 novos); invariante TEST-07 (valuation) preservada.

## Task Commits

1. **Task 1 (RED): golden de overlays/subpainéis/layout** - `7f409dc` (test)
2. **Task 1 (GREEN): funções puras de montagem** - `6ada4dd` (feat)
3. **Task 2 (RED): golden de marcadores + degradação** - `980d8fc` (test)
4. **Task 2 (GREEN): marcadores nas datas exatas + degradação** - `fd25e3b` (feat)

_TDD: cada task com par test→feat._

## Files Created/Modified
- `src/analista/grafico.py` - Contrato puro: `estado_padrao`, `overlays_preco`, `subpaineis_ativos`, `layout_subplots`, `marcadores_eventos`, `leitura_tecnica_disponivel`; dataclasses `OverlaySpec`, `SubpainelSpec`, `Marcador`.
- `tests/test_grafico_ui.py` - Golden das funções de montagem (overlays SMA/EMA+janelas, donchian 55+bollinger, subpainéis com série+níveis+degradação, layout, marcadores nas datas exatas, degradação para vazio).

## Verification
- `./.venv/bin/python -m pytest tests/test_grafico_ui.py -q` → 10 passed; suíte completa 148 passed.
- `grep -n "import streamlit\|import plotly" src/analista/grafico.py` → 0 (módulo puro).

## must_haves — atendidas
- A lógica de QUAIS overlays deriva puramente do estado dos toggles + a.sinais (UI-01/UI-03). ✓
- subpaineis_ativos devolve SPEC COMPLETO (série(s) + níveis); subpainel só quando toggle ON e série não-toda-NaN (UI-02). ✓
- Marcadores nas datas exatas lendo a.sinais + close, nomeando o evento (UI-04). ✓
- Estado padrão com técnico OFF (UI-06). ✓

## Deviations from Plan
None - plano executado exatamente como escrito.

## TDD Gate Compliance
RED (`test(...)`) e GREEN (`feat(...)`) presentes em ambas as tasks. Nenhum teste passou inesperadamente na fase RED (módulo/símbolos ausentes ⇒ ImportError de coleta). Refactor não necessário (implementação mínima já limpa).

## Known Stubs
Nenhum. Todas as funções têm comportamento real coberto por golden; nenhum valor placeholder flui para a UI.

## Self-Check: PASSED
- Arquivos: src/analista/grafico.py, tests/test_grafico_ui.py, 07-03-SUMMARY.md — todos presentes.
- Commits: 7f409dc, 6ada4dd, 980d8fc, fd25e3b — todos no histórico.
