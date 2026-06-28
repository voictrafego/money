---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: — Saneamento residual do valuation
status: planning
stopped_at: Phase 11 UI-SPEC approved
last_updated: "2026-06-28T00:30:05.930Z"
last_activity: 2026-06-27
progress:
  total_phases: 8
  completed_phases: 2
  total_plans: 6
  completed_plans: 6
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-24)

**Core value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.
**Current focus:** Phase 10 — crescimento-robusto-de-poison-do-screening

## Current Position

Phase: 11
Plan: Not started
Status: Ready to plan
Last activity: 2026-06-27

**v1.3 — execução 9 → 10 → 11 (metodologia antes das telas que a consomem):**

- Phase 9 (DYR-01, PAY-01): payout sustentável geral + DY recorrente = lucro normalizado × payout sustentável
- Phase 10 (GROW-01, GROW-02): g histórico robusto + Garimpo/Ranking sobre série normalizada (gateia as telas)
- Phase 11 (DYR-02, PAY-02, HIER-01, TEST-08): % na tabela, payout cru do último ano, header com DY rec. em destaque, trava multi-ticker + rebaseline deliberado

## Performance Metrics

**Velocity:**

- Total plans completed: 28 (v1.0 + v1.1 + v1.2)
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
| 10 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: 08-04, 07-01, 07-02, 07-03, 07-04, 07-05 (v1.2 fechado, 150 testes verdes)
- Trend: —

*Updated after each plan completion*
| Phase 09 P01 | 2min | 2 tasks | 2 files |
| Phase 09 P02 | 5min | 3 tasks | 3 files |
| Phase 9 P03 | 25min | 2 tasks | 2 files |
| Phase 10 P01 | 12min | 2 tasks | 3 files |
| Phase 10 P02 | 9min | 2 tasks | 2 files |
| Phase 10 P03 | 22min | 3 tasks | 1 file |

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
- [Phase ?]: Phase 9 Plan 01: primitiva pura mediana_payout (mediana sobre série completa, sem janela 3a, sem clamp 1.0) como irmã de base_normalizada; raiz metodológica do PAY-01 travada por golden antes dos consumidores (Plan 02)
- [Phase ?]: Phase 9 Plan 02: payout_valuation delega à mediana sobre série completa (sem janela 3a, sem clamp 1.0); DY recorrente vira earnings-based (payout_valuation × lpa_valuation ÷ preço); 4 goldens rebaselinados deliberadamente
- [Phase 9]: Phase 9 Plan 03: trava de validação multi-ticker em 2 camadas (golden offline de propriedade + checkpoint live dos 5 tickers reais aprovado: VULC3 43.1%/DY6.3%, TAEE11 217.9%/DY8.4%, EGIE3 49.9%, ITUB4 31.2%, BBAS3 18.8%); cross-effect payout-sem-clamp → regressão P/L registrado para a Fase 10 (screening.py intocado, D-06)
- [Phase 10]: Phase 10 Plan 01 (GROW-01): g_historico passa a vir de regressão log-linear (OLS de ln, g=exp(slope)-1) sobre a série de lucro normalizada inteira via novo estimador puro growth.crescimento_log_linear; fronteira de None idêntica ao CAGR (None/len<2/ponto<=0 → None, D-03); fonte única reusada pelo screening no Plan 02 (D-04); 166 testes verdes sem rebaseline (golden de valor exato reservados ao 10-03/T2)
- [Phase 10]: Phase 10 Plan 02 (GROW-02): BSD calcula crescimento_lucro/_dividendos/_fc_3a via growth.crescimento_log_linear sobre normalizacao.serie_winsorizada (série completa, D-04/D-05) — crescimento_lucro_3a == report.g_historico por construção; ajustar_regressao_pl clampa payout em [0,1] na entrada do fit (de-poison de b1, TAEE11~2.16, D-06) sem reintroduzir clamp no canônico payout_valuation (D-03); per-ano CRU e bandas REFERENCIA_BSD intactos (D-07); 166 testes verdes
- [Phase 10]: Phase 10 Plan 03 (trava de aceite): golden offline de propriedade multi-ticker (test_growth_robusto_multiticker.py, 5 testes) trava critérios a/b/c + consistência D-04; suíte completa 171 testes verde SEM rebaseline (nenhum assert de valor exato sobre g_historico/crescimento_*_3a); checkpoint live dos 5 tickers reais APROVADO — VULC3 g 31,5% < endpoint-CAGR 47,2% (spike não infla), normais não regridem, TAEE11 P/L alvo 40,06 sensato após clamp, buckets BSD sem colapso, REFERENCIA_BSD intacta (D-07). Phase 10 fechada (GROW-01/GROW-02)

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

Last session: 2026-06-28T00:30:05.927Z
Stopped at: Phase 11 UI-SPEC approved
Resume file: .planning/phases/11-apresenta-o-hierarquia-e-trava-multi-ticker/11-UI-SPEC.md

## Operator Next Steps

- Planejar a primeira fase do v1.3 com `/gsd-plan-phase 9`
