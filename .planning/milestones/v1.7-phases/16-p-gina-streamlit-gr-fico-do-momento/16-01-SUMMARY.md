---
phase: 16-p-gina-streamlit-gr-fico-do-momento
plan: 01
subsystem: ui
tags: [streamlit, plotly, candlestick, make_subplots, swing, read-only]

# Dependency graph
requires:
  - phase: 12-ingestao-intraday
    provides: frame_intraday (FrameOHLC, cache TTL 300s + nonce)
  - phase: 13-pivos-niveis
    provides: indicators.calcular (SinaisTecnicos — overlays, níveis, pivôs)
  - phase: 14-padroes-checklist
    provides: SinaisTecnicos.padroes / checklist
  - phase: 15-montagem-do-setup
    provides: setup.montar_setup (SetupSwing — score/grade/decomposição/níveis)
provides:
  - "4º menu monta SinaisTecnicos + SetupSwing read-only a partir do FrameOHLC (ohlc_nominal)"
  - "Dict de estado isolado tec_estado_swing (defaults D-02) + expander ⚙️ Overlays"
  - "Figura candlestick multi-painel (make_subplots): candle nominal + overlays MM + subpainéis RSI/MACD/ADX + barra viva"
  - "Selo de atraso sempre visível (D-08)"
affects: [16-02-veredito-niveis-padroes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reuso direto das funções puras de grafico.py (overlays_preco/subpaineis_ativos/layout_subplots) com estado isolado da página swing"
    - "Estado de toggles ISOLADO por página (tec_estado_swing) — espelha tec_estado da Analisar sem compartilhar"

key-files:
  created: []
  modified: [app.py]

key-decisions:
  - "Estado isolado tec_estado_swing com defaults próprios (D-02), nunca grafico.estado_padrao() nem tec_estado da Analisar (D-03/SWING-01)"
  - "calcular() sempre com ohlc_nominal=f.ohlc (Pitfall 6) — pivôs/S-R/Fib em escala nominal coerente com o candle"
  - "make_subplots multi-painel (não go.Figure single-panel) para subpainéis RSI/MACD/ADX em rows próprias; rangeslider OFF via update_xaxes (Pitfall 4)"
  - "Selo de atraso renderizado sempre que f.disponivel, não gateado por f.barra_viva (D-08)"

patterns-established:
  - "Página swing read-only: thin renderer que só LÊ campos de FrameOHLC/SinaisTecnicos/SetupSwing"
  - "Reuso golden-pinned de grafico.py trocando só o trace de preço (LINHA→CANDLESTICK)"

requirements-completed: [SWING-01, CHART-01]

# Metrics
duration: ~10min
completed: 2026-06-30
---

# Phase 16 Plan 01: Cadeia de engine swing + candlestick multi-painel Summary

**O 4º menu deixou de ser candlestick nu: agora monta read-only `SinaisTecnicos`+`SetupSwing` (com `ohlc_nominal`) e renderiza um candlestick `make_subplots` com overlays de médias móveis ligados por padrão e subpainéis RSI/MACD/ADX, controlados por um estado de toggles isolado da página.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-06-30
- **Tasks:** 2
- **Files modified:** 1 (app.py)

## Accomplishments
- Imports `indicators` + `setup` adicionados; cadeia `calcular(ohlc_nominal) → montar_setup` wirada read-only no bloco swing.
- Dict `tec_estado_swing` isolado (defaults D-02: MMs/ADX/RSI/MACD/S-R/Fib/níveis ON; Donchian/Bollinger/padrões OFF) + expander "⚙️ Overlays" espelhando os toggles da aba Analisar.
- Figura `make_subplots`: candlestick nominal em row 1 (rangeslider OFF), overlays MM via `grafico.overlays_preco`, subpainéis RSI/MACD/ADX via `grafico.subpaineis_ativos` (MACD-Histograma como `go.Bar` colorido), barra viva via `add_vline`.
- Selo de atraso "~15min (best-effort)" sempre visível (D-08).
- 283 testes golden verdes; `app.py` é a única edição.

## Task Commits

1. **Task 1: Wire da cadeia de engine + estado isolado + expander de overlays** — `ca4d2bf` (feat)
2. **Task 2: Figura make_subplots — candlestick + overlays MM + subpainéis RSI/MACD/ADX + barra viva** — `f8393b5` (feat)

## Files Created/Modified
- `app.py` — imports `indicators`/`setup`; bloco swing: cadeia read-only, dict `tec_estado_swing`, expander "⚙️ Overlays", figura `make_subplots` multi-painel substituindo o single-panel MVP, selo de atraso incondicional.

## Decisions Made
None - followed plan as specified (decisões D-02/D-03/D-08 e Pitfalls 4/6 aplicadas conforme o plano).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `python` não está no PATH do ambiente; usei `./.venv/bin/python` para AST-check e pytest. Sem impacto.

## Known Stubs
Os toggles extras `sr_on`/`fib_on`/`niveis_setup_on`/`padroes_on` já existem no estado e no expander mas ainda NÃO desenham nada nesta figura — as zonas S/R (`add_hrect`), Fibonacci/níveis do setup (`add_hline`) e anotação de padrões são entregues no plano **16-02** (deferimento explícito no `<objective>` do plano). O card de veredito (score/grade/decomposição/checklist) também é 16-02. Stubs intencionais e rastreados.

## Next Phase Readiness
- Cadeia `calcular → montar_setup` e estado isolado prontos para 16-02 consumir (`sw` e `sinais` já em escopo no bloco).
- 16-02 wira os overlays extras (S/R/Fib/setup/padrões) na figura e adiciona o card de veredito abaixo do gráfico.

## Self-Check: PASSED

- app.py — FOUND
- 16-01-SUMMARY.md — FOUND
- commit ca4d2bf (Task 1) — FOUND
- commit f8393b5 (Task 2) — FOUND

---
*Phase: 16-p-gina-streamlit-gr-fico-do-momento*
*Completed: 2026-06-30*
