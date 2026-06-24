---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Indicadores de tendência (timing) na aba Analisar
status: planning
last_updated: "2026-06-24T11:36:09.387Z"
last_activity: 2026-06-24
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-23)

**Core value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.
**Current focus:** Phase 03 — gr-fico-de-pre-o-na-aba-analisar

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-06-24 — Milestone v1.2 started

## Performance Metrics

**Velocity:**

- Total plans completed: 7 (v1.0)
- Average duration: — min
- Total execution time: — hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | - | - |
| 02 | 2 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01 P01 | 18 | 3 tasks | 7 files |
| Phase 01 P02 | 4 | 1 tasks | 2 files |
| Phase 01 P03 | 5 | 3 tasks | 3 files |
| Phase 01 P04 | 6 | 2 tasks | 1 files |
| Phase 01 P05 | 15 | 3 tasks | 1 files |
| Phase 02 P01 | 11 | 3 tasks | 2 files |
| Phase 02 P02 | 12 | 2 tasks | 1 files |
| Phase 03 P01 | 2 | 3 tasks | 4 files |
| Phase 03 P02 | 6 | 3 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.1 / Phase 3]: a série diária de 5a já é baixada por `ingest/prices.py` (`coletar_mercado` → `tk.history(period="5y")`) e hoje é descartada após beta/liquidez — o trabalho é PRESERVAR esse DataFrame, não fazer nova chamada de rede.
- [v1.1 / Phase 3]: a série flui `DadosMercado.hist` → `build.montar_empresa` (CompanyData) → `report.analisar_acao` (AnaliseAcao) → `app.py` (aba Analisar); o cache de 1h em `montar_empresa` já cobre o gráfico.
- [v1.1 / Phase 3]: o valor intrínseco a sobrepor é o vmin/vmax já exposto em `AnaliseAcao` (Phase 1, VAL-01) — NÃO recalcular nem alterar nenhuma fórmula de valuation.
- [v1.1 / Phase 3]: render com Plotly via `st.plotly_chart`; `plotly` adicionado ao `requirements.txt`.
- app.py é read-only: só lê campos da engine, nunca recalcula método (decisão herdada da Phase 2).
- [v1.1 / Phase 3 / Plano 01 ✓]: `serie_precos` (close 5a) preservado de `hist["Close"].dropna()` no fetch existente (zero rede nova) e conduzido `DadosMercado → CompanyData` via `build.montar_empresa`; forward-ref `Optional["pd.Series"]` mantém a engine leve (sem `import pandas` no topo). plotly>=6.0 pinado e instalado (6.8.0). pytest 62 passed, nenhuma fórmula alterada.
- [Phase ?]: [v1.1 / Phase 3 / Plano 02 ✓]: gráfico Plotly (linha preço 5a + banda DDM via add_hrect) na aba Analisar entre alertas e st.tabs (D-03); width=stretch; fallbacks série indisponível (D-05) e DDM None sem banda (D-06); 62 testes verdes; checkpoint human-verify aprovado.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- Restrição dura: os testes golden existentes em `tests/` (test_ddm, test_multiples, test_comparables, test_screening) devem continuar passando após cada mudança — nenhuma fórmula de valuation pode mudar no v1.1.
- A degradação graciosa (GRAF-03) deve seguir o padrão do aviso "preço atual indisponível (Yahoo)" já existente na Tela 1, evitando quebrar a aba quando `hist` vier vazio/None.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260620-oa9 | Avisos de confiabilidade na Tela 2 (Ranking): amostra pequena, ROE com sinal invertido, mesmo segmento | 2026-06-20 | 0e573da | [260620-oa9-ajustar-tela-2-ranking-por-multiplos-com](./quick/260620-oa9-ajustar-tela-2-ranking-por-multiplos-com/) |
| fast | fix: mapear BMGB4 → CD_CVM 24600 (Banco BMG) — resolução determinística contra hiccup do Yahoo | 2026-06-20 | bc9de8c | (gsd-fast) |
| 260622-cg9 | Robustez da resolução de tickers: retry no Yahoo + _norm cirúrgico + casamento por token-set + map +10 (incl. ELET3/ELET6→Axia) | 2026-06-22 | c06a6d1 | [260622-cg9-robustez-da-resolucao-de-tickers-retry-y](./quick/260622-cg9-robustez-da-resolucao-de-tickers-retry-y/) |
| fast | feat: aviso "preço atual indisponível (Yahoo)" na Tela 1 quando preco_atual=None | 2026-06-22 | d3e0d1b | (gsd-fast) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Docs engine | DDM-DOC-01 (alinhar docstring/teste de t em ddm.py, IN-06) | v2 | 2026-06-04 |

## Session Continuity

Last session: 2026-06-23T13:47:48.996Z
Stopped at: Phase 3 context gathered
Resume file: None

## Operator Next Steps

- Start the next milestone with /gsd-new-milestone
