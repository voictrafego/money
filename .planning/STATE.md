---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: — Indicadores de tendência
status: executing
stopped_at: Phase 6 context gathered
last_updated: "2026-06-27T00:13:16.352Z"
last_activity: 2026-06-27 -- Phase 06 planning complete
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 7
  completed_plans: 5
  percent: 71
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-24)

**Core value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.
**Current focus:** Phase 05 — motor-de-indicadores-puro

## Current Position

Phase: 6
Plan: Not started
Status: Ready to execute
Last activity: 2026-06-27 -- Phase 06 planning complete

Progress: [████████░░] 80%

## Performance Metrics

**Velocity:**

- Total plans completed: 12 (v1.0 + v1.1)
- Average duration: — min
- Total execution time: — hours

**By Phase (concluídas):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | - | - |
| 02 | 2 | - | - |
| 03 | 2 | - | - |
| 05 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 04 P02 | 10 | 2 tasks | 1 files |
| Phase 05 P01 | 18 | 3 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- app.py é read-only: só lê campos da engine, nunca recalcula método (locked, Phase 2).
- Série do gráfico = Close nominal (`auto_adjust=False`); indicadores usam série split-adjusted (não dividend-adjusted) — eixo nominal preserva alinhamento com a banda DDM (CR-01).
- Análise técnica (v1.2) é **consultiva**, nunca altera o veredito fundamentalista; rompimento técnico dispara **reverificação** dos fundamentos, não venda.
- [v1.2 research]: OHLC já está em memória em `coletar_mercado` (`tk.history(period="5y", auto_adjust=False)`) — preservar `dm.ohlc`, não fazer nova chamada de rede (espelha o padrão `serie_precos`).
- [v1.2 research]: hand-roll total dos indicadores em numpy/pandas/scipy — **sem nova dependência de TA** (`ta`/`pandas-ta`/`TA-Lib` incompatíveis com numpy 2.4.6 / pandas 3.0.3).
- [v1.2 research]: RSI/ADX exigem suavização de **Wilder** (`ewm(alpha=1/length, adjust=False)`, seed SMA), não EMA padrão — travar com golden test cruzado com TradingView.
- [v1.2 research]: `a.sinais` (`SinaisTecnicos`) calculado em `report.analisar_acao` — ponto único compartilhado por CLI e UI; paridade gratuita.
- [Phase ?]: [05-01] SinaisTecnicos nested por família; cross/posição×MM200 SEMPRE sobre SMA (D-03); RSI Wilder SMA-seeded = 70.5328; MACD usa EMA padrão, não Wilder.
- [05-03] ADX dupla-Wilder: 1ª suavização do DMI com start=1 (barra 0 = diff indefinido) → 1º DI no índice 14; 2ª suavização do DX com start=length → 1º ADX no índice 27. calcular() agrega as 4 famílias com guard de borda → fully-indisponivel. Checkpoint TEST-03 (ADX × TradingView) APROVADO e literais congelados em test_adx_wilder_referencia.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- Invariante TEST-07: os 64 golden tests de valuation existentes devem continuar verdes ao final de cada fase do marco — nenhuma fórmula do livro pode mudar.
- Pontos de validação (não pesquisa): Phase 4 — testar série split-adjusted com ticker de split conhecido antes de fechar; Phase 5 — cruzar fixture RSI/ADX com TradingView antes de travar o golden; Phase 7 — fresh-reader test ("cara + timing bullish") como critério de aceite explícito de UI-06.
- Degradação graciosa (DATA-03) deve seguir o padrão do aviso GRAF-03 já existente, sem quebrar a aba quando `hist`/OHLC vier vazio.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Docs engine | DDM-DOC-01 (alinhar docstring/teste de t em ddm.py, IN-06) | v2 | 2026-06-04 |

## Session Continuity

Last session: 2026-06-26T19:15:15.482Z
Stopped at: Phase 6 context gathered
Resume file: .planning/phases/06-integra-o-na-engine-composite-alerta-cli/06-CONTEXT.md

## Operator Next Steps

- Planejar a primeira fase com `/gsd-plan-phase 4`
