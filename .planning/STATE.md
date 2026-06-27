---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Saneamento residual do valuation
status: Roadmap v1.3 criado (3 fases, 8 requisitos mapeados 8/8)
stopped_at: Phase 9 context gathered
last_updated: "2026-06-27T19:19:52.224Z"
last_activity: 2026-06-27 — Roadmap v1.3 criado (Phases 9-11)
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-24)

**Core value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.
**Current focus:** Phase 9 — Payout sustentável + DY recorrente (núcleo de metodologia)

## Current Position

Phase: 9 — Payout sustentável + DY recorrente (núcleo de metodologia)
Plan: — (roadmap criado; aguardando planejamento da fase)
Status: Roadmap v1.3 criado (3 fases, 8 requisitos mapeados 8/8)
Last activity: 2026-06-27 — Roadmap v1.3 criado (Phases 9-11)

**v1.3 — execução 9 → 10 → 11 (metodologia antes das telas que a consomem):**

- Phase 9 (DYR-01, PAY-01): payout sustentável geral + DY recorrente = lucro normalizado × payout sustentável
- Phase 10 (GROW-01, GROW-02): g histórico robusto + Garimpo/Ranking sobre série normalizada (gateia as telas)
- Phase 11 (DYR-02, PAY-02, HIER-01, TEST-08): % na tabela, payout cru do último ano, header com DY rec. em destaque, trava multi-ticker + rebaseline deliberado

## Performance Metrics

**Velocity:**

- Total plans completed: 25 (v1.0 + v1.1 + v1.2)
- Average duration: — min
- Total execution time: — hours

**By Phase (concluídas):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | - | - |
| 02 | 2 | - | - |
| 03 | 2 | - | - |
| 04 | 2 | - | - |
| 05 | 3 | - | - |
| 06 | 2 | - | - |
| 08 | 4 | - | - |
| 07 | 5 | - | - |

**Recent Trend:**

- Last 5 plans: 08-04, 07-01, 07-02, 07-03, 07-04, 07-05 (v1.2 fechado, 150 testes verdes)
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work (v1.3 — saneamento residual):

- A camada `normalizacao.py` (base_normalizada = mediana p/ 2≤N<5, média winsorizada p/ N≥5; serie_winsorizada) já é o número-síntese canônico do valuation (FIX-04). O v1.3 **estende/generaliza** essa primitiva para payout, provento recorrente e crescimento — não reescreve o DDM.
- Raiz compartilhada DYR-01 + PAY-01: definir um **payout sustentável geral** que expurga anos não-recorrentes (>100%) por regra data-driven; o DY recorrente deriva de **lucro normalizado × payout sustentável** (não a mediana crua de 3 anos de dividendos). Acoplados → mesma fase (Phase 9, núcleo de metodologia).
- Hoje `payout_valuation()` é a média crua de 3 anos clampada em 1.0 → satura em 100% num ano extraordinário e zera `g_fundamentos`. PAY-01 substitui pelo expurgo de não-recorrentes.
- Hoje `dy_recorrente`/`dpa_recorrente` derivam de `base_normalizada(serie("dividendos"))` (mediana de dividendos CRUS) — cai inteira numa era de payout >100%. DYR-01 re-deriva de lucro normalizado × payout sustentável.
- GROW-02 (de-poison do Garimpo/Ranking) **gateia** as telas → metodologia (Phase 9) aterrissa antes; crescimento robusto + screening normalizado na Phase 10.
- TEST-08 é a **trava de fechamento** (Phase 11): valida contra ITUB4/EGIE3/TAEE11/BBAS3 + VULC3; rebaseline de golden só **deliberado e justificado** (extensão de TEST-07). NÃO tunar a um ticker — fixes generalizam.
- app.py é read-only (locked, Phase 2): DYR-02/PAY-02/HIER-01 são apresentação sobre campos já expostos pela engine, sem recálculo de método.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- **Invariante TEST-07 → TEST-08:** os golden de valuation devem seguir verdes ao final de cada fase OU mudar apenas por rebaseline deliberado e justificado. Nenhuma fórmula do livro (DDM Cap. 13-17) pode ser reescrita.
- **Não tunar a um ticker:** o expurgo de não-recorrentes deve valer para qualquer ticker. Validar VULC3 (caso-limite) E tickers normais de payout alto legítimo (TAEE11/EGIE3) para não rebaixar payout sustentável de quem distribui muito de forma recorrente.
- **Fronteira per-ano preservada:** `payout(ano)`/`roe(ano)`/lucro CRU seguem alimentando a tabela "Fundamentos (por ano)", o detector de armadilha (payout>100%) e a elegibilidade do screening (Cap. 8) — só os agregados de valuation/crescimento mudam de base.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Docs engine | DDM-DOC-01 (alinhar docstring/teste de t em ddm.py, IN-06) | v2 | 2026-06-04 |
| Refino | Payout-alvo por setor configurável | v2+ | 2026-06-27 |
| UI | Sinalização explícita de "ano extraordinário" na tabela de Fundamentos por ano | v2+ | 2026-06-27 |

## Session Continuity

Last session: 2026-06-27T19:19:52.219Z
Stopped at: Phase 9 context gathered
Resume file: .planning/phases/09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia/09-CONTEXT.md

## Operator Next Steps

- Planejar a primeira fase do v1.3 com `/gsd-plan-phase 9`
