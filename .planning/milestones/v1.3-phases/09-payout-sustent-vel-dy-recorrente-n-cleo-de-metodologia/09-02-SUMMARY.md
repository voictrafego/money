---
phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia
plan: 02
subsystem: engine-fundamentals
tags: [payout, mediana, dy-recorrente, earnings-based, valuation, golden-rebaseline]

# Dependency graph
requires:
  - phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia
    provides: "primitiva pura mediana_payout (Plan 01) — mediana sobre série completa, sem clamp, fronteira None"
  - phase: 08-normalizacao-do-lucro
    provides: "lpa_valuation / base_lucro_normalizada (base de lucro normalizada por ação)"
provides:
  - "payout_valuation() = mediana do payout sobre a série COMPLETA, sem janela 3a e sem clamp 1.0 (PAY-01)"
  - "dpa_recorrente()/dy_recorrente() earnings-based = payout_valuation × lpa_valuation ÷ preço (DYR-01)"
  - "goldens rebaselinados p/ a semântica mediana-sem-clamp (4 asserts + docstring de módulo)"
affects: [report.analisar_acao, screening (Fase 10 — cross-effect registrado), Fase 11 (apresentação)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "payout_valuation espelha base_lucro_normalizada: monta a série per-ano completa e delega à primitiva pura (sem reimplementar a estatística)"
    - "DY recorrente earnings-based: payout sustentável aplicado ao lucro normalizado por ação (consistente com g_fund), não mais mediana de dividendos crus"

key-files:
  created: []
  modified:
    - src/analista/core/fundamentals.py
    - tests/test_fundamentals_consistencia.py
    - tests/test_vulc3_regressao.py

key-decisions:
  - "payout_valuation no-arg (FIX-04): removido o parâmetro janela; todos os call sites já chamavam sem args"
  - "Sem clamp em 1.0 (D-03): mediana pode ser >100% (VULC3 sintética 1.25, TAEE11 ≈216%); o piso g_alto = max(0,…) do report absorve payout>100% sem piso novo"
  - "DY recorrente earnings-based (D-05): payout_valuation × lpa_valuation, não a mediana crua de 3a de dividendos (que cai na era de payout >100%)"
  - "4 goldens rebaselinados deliberadamente com justificativa pelo método (clamp removido + janela→série completa); fronteira CRU payout(ano) intacta (D-06)"

requirements-completed: [PAY-01, DYR-01]

# Metrics
duration: ~5min
completed: 2026-06-27
---

# Phase 9 Plan 02: Payout sustentável + DY recorrente earnings-based (núcleo de metodologia) Summary

**`payout_valuation()` agora é a mediana do payout sobre a série histórica completa (sem janela 3a, sem clamp 1.0) delegando à primitiva do Plan 01, e `dy_recorrente()` passa a ser earnings-based (payout sustentável × LPA normalizado ÷ preço) — núcleo metodológico de PAY-01/DYR-01 com a fronteira CRU intacta e a suíte completa verde (155 testes) após rebaseline deliberado de 4 goldens.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-27T21:37:31Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- `payout_valuation()` reescrito (PAY-01): constrói a série COMPLETA `[payout(a) for a in anos_ordenados()]` e delega a `norm.mediana_payout` — sem o slice `[-janela:]` e sem o `min(…, 1.0)`. Assinatura canônica no-arg (removido o parâmetro `janela`; FIX-04 preservado).
- `dpa_recorrente()/dy_recorrente()` reescritos (DYR-01, D-05): renda sustentável = `payout_valuation() × lpa_valuation()` ÷ preço (earnings-based), consistente com o `g_fund`. Removida a derivação por `base_normalizada(serie("dividendos"))` (mediana de dividendos crus, que cai inteira na era de payout >100% no VULC3). Fronteira None preservada (payout/LPA/preço None → None).
- Rebaseline deliberado de 4 asserts (D-01/D-03/D-04) + docstring de módulo, cada um com justificativa pelo método; suíte completa 155 verdes.

## Task Commits

Cada task commitada atomicamente:

1. **Task 1: payout_valuation = mediana sobre série completa, sem clamp** - `5bee5d8` (feat)
2. **Task 2: DY recorrente earnings-based** - `2c6bf47` (feat)
3. **Task 3: Rebaseline deliberado dos 4 goldens + docstring** - `25d8b7d` (test)

## Files Created/Modified
- `src/analista/core/fundamentals.py` - `payout_valuation` delega a `norm.mediana_payout` (série completa, sem clamp, no-arg); `dpa_recorrente/dy_recorrente` earnings-based via `payout_valuation × lpa_valuation`.
- `tests/test_fundamentals_consistencia.py` - 2 goldens de payout rebaselinados (1.5 sem clamp; 0.65 mediana da série completa) + docstring de módulo atualizado p/ "mediana sobre série completa, sem clamp (PAY-01)".
- `tests/test_vulc3_regressao.py` - capstone rebaselinado: `payout_valuation() > 1.0` (≈1.25, era de payout >100%) e `g_fundamentos <= 0.0`; `g_alto == 0.0` (via piso) e `dy_recorrente() <= dy_atual()` mantidos intactos.

## Decisions Made
- payout_valuation no-arg (removido `janela`) — consistência cross-menu por construção (FIX-04).
- Sem clamp em 1.0 (D-03): a mediana >100% é legítima; o piso existente `g_alto = max(0,…)` do report cobre payout>100% (g_fund ≤ 0 ⇒ g_alto 0), sem piso novo.
- DY recorrente earnings-based (D-05) reusando a base de lucro normalizada da Fase 8.
- Os 4 goldens que quebram por design foram rebaselinados deliberadamente, com 1 comentário de justificativa cada (invariante TEST-07/TEST-08: golden muda só por rebaseline justificado).

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
- O interpretador `python` não está no PATH; usado `.venv/bin/python` (venv do projeto) para pytest e snippets de verificação. Sem impacto no código.

## Threat Surface
- T-09-03 (Tampering numérico: payout sem clamp distorcer DDM/g_alto) mitigado — `test_vulc3_regressao` verde (DDM finito, `g_alto == 0.0` via piso, `vmax < 3×preço`) e `test_growth_reconciliacao` intacto.
- T-09-04 (DY recorrente earnings-based superestimar renda vs trailing) mitigado — `test_guardrails_fix06` (dy_recorrente < trailing) + `test_vulc3` L125 (`dy_recorrente() <= dy_atual()`) verdes.
- Sem nova superfície de rede/auth/IO/PII — reescrita de métodos puros de analytics offline.

## Cross-effect registrado (Fase 10 — NÃO resolvido aqui)
- `payout_valuation` SEM clamp (TAEE11 ≈ 2.16) passa a fluir para a regressão P/L de `screening.py` (`preco_alvo_por_regressao(reg, c.payout_valuation(), …)` em cli.py L159 / app.py L472), calibrada com payout ∈ [0,1]. A decisão de clampar SÓ na entrada da regressão é da Fase 10 (de-poison do screening). Este plano NÃO tocou `screening.py`.

## Next Phase Readiness
- Núcleo de metodologia (payout sustentável + DY recorrente) pronto e consistente entre menus. Fase 10 (g histórico robusto + de-poison do screening) e Fase 11 (apresentação) podem consumir os novos agregados.

## Self-Check: PASSED
- FOUND: src/analista/core/fundamentals.py
- FOUND: tests/test_fundamentals_consistencia.py
- FOUND: tests/test_vulc3_regressao.py
- FOUND commit: 5bee5d8 (Task 1 feat)
- FOUND commit: 2c6bf47 (Task 2 feat)
- FOUND commit: 25d8b7d (Task 3 test)

---
*Phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia*
*Completed: 2026-06-27*
