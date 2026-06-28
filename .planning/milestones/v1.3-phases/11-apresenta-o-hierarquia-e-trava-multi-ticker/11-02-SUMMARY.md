---
phase: 11-apresenta-o-hierarquia-e-trava-multi-ticker
plan: 02
subsystem: ui
tags: [streamlit, app, presentation, dividend-yield, payout, glossario, copywriting]

# Dependency graph
requires:
  - phase: 11-01
    provides: "src/analista/report/presentation.py — helpers puros header_dy/linhas_multiplos/fmt_pct/fmt_num"
  - phase: 09-payout-sustentavel-dy-recorrente
    provides: "c.payout_valuation() / c.dy_recorrente() (campos sustentáveis na engine)"
provides:
  - "app.py religado: chamador fino de presentation.header_dy / linhas_multiplos (read-only, sem recálculo de método)"
  - "Header m3 do Analisar: DY recorrente como principal + trailing como delta cinza (delta_color='off'), com fallback gracioso"
  - "Tabela de Múltiplos: 'DY rec.' formatado como % + payout cru do último ano distinto do sustentável p/ valuation"
  - "Glossário fiel às Fases 9-10: payout sustentável = mediana sem clamp; g histórico = tendência log-linear"
affects: [checkpoint-live, app.py, glossario.py]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "app.py como chamador fino da camada de apresentação (read-only): só lê campos da engine e delega montagem/formatação aos helpers"

key-files:
  created: []
  modified:
    - app.py
    - src/analista/glossario.py

key-decisions:
  - "fmt_pct/fmt_num locais do app.py mantidos (byte-idênticos aos de presentation) — sem divergência de separador; presentation só importado para header_dy/linhas_multiplos"
  - "delta_color='off' passado literal no st.metric (não via dict) p/ travar firme o cinza neutro e satisfazer o gate; delta=hdr['delta'] (None vira ausência de delta no Streamlit)"
  - "payout cru lê c.payout(c.ultimo_ano()) — paridade exata com report.py L156, não mais a.multiplos['DP (payout)']"

patterns-established:
  - "Camada de apresentação consumida pelo app: o Streamlit vira só wiring de st.metric/st.dataframe sobre dicts/listas dos helpers"

requirements-completed: [DYR-02, PAY-02, HIER-01]

# Metrics
duration: 3 min
completed: 2026-06-28
---

# Phase 11 Plan 02: Religar o app.py aos Helpers de Apresentação Summary

**app.py virou chamador fino de `presentation.header_dy`/`linhas_multiplos` — header do Analisar destaca o DY recorrente com trailing como delta cinza, a tabela de Múltiplos mostra payout cru do último ano distinto do sustentável, e o glossário ficou fiel às Fases 9-10 (mediana sem clamp + tendência log-linear), tudo read-only e sem rebaselinar golden de valuation.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-28T01:04:59Z
- **Completed:** 2026-06-28T01:07:04Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Header m3 (HIER-01): `presentation.header_dy(a.multiplos.get("DY rec."), a.multiplos.get("DY"))` alimenta `st.metric` com label/value/delta + `delta_color="off"` (trailing como contexto cinza) e fallback gracioso quando o recorrente é None.
- Tabela de Múltiplos (DYR-02 + PAY-02): loop buggado substituído por `presentation.linhas_multiplos(a.multiplos, payout_ult, payout_proj)`, com `payout_ult = c.payout(c.ultimo_ano())` CRU (paridade report.py L156) e `payout_proj = c.payout_valuation()` sustentável.
- Sweep D-07 no app.py: "g histórico (CAGR lucro)" → "g histórico (tendência log-linear)"; caption do payout reescrita; comentário obsoleto "média 3a + clamp" do modo Ranking atualizado p/ "sustentável (mediana)".
- Glossário (D-07): `payout_dual` reescrito p/ mediana da série completa sem teto (sustentável p/ DDM); `tab_crescimento` descreve regressão log-linear sobre série de lucro normalizada. Sem "média 3a"/"CAGR"/"teto de 100".
- Suíte completa verde (175 passed) via invocação canônica, zero rebaseline de golden de valuation.

## Task Commits

Each task was committed atomically:

1. **Task 1: app.py — religar header m3 + tabela de Múltiplos + relabel de Crescimento** - `2e72450` (feat)
2. **Task 2: glossário — varrer copy obsoleta de payout_dual e tab_crescimento** - `c0b6c0b` (docs)

**Plan metadata:** ver commit `docs(11-02)` abaixo.

## Files Created/Modified
- `app.py` - Import de `presentation`; header m3 via `header_dy`; tabela de Múltiplos via `linhas_multiplos` com payout cru x sustentável; rótulos/comentários obsoletos varridos. Segue read-only.
- `src/analista/glossario.py` - `payout_dual` e `tab_crescimento` reescritos fiéis às Fases 9-10.

## Decisions Made
- `fmt_pct`/`fmt_num` locais do app.py mantidos (byte-idênticos aos de `presentation`, em-dash "—") — sem divergência de separador; `presentation` importado só para `header_dy`/`linhas_multiplos`.
- `delta_color="off"` passado literal no `st.metric` (em vez de via `hdr["delta_color"]`) para travar firme o gate de grep e o cinza neutro; `delta=hdr["delta"]` (None → Streamlit omite o delta).
- Comentário obsoleto "média 3a + clamp" no modo Ranking (app.py L460) tratado como parte do sweep D-07, já que o gate de aceite exige `grep -c "média 3a" app.py == 0`.

## Deviations from Plan

None - plan executed exactly as written. O comentário "média 3a + clamp" do modo Ranking (não citado explicitamente nos `read_first` da Task 1, mas dentro do escopo do gate "média 3a == 0" e do mandato D-07 de varrer rótulos/comentários obsoletos) foi atualizado para "sustentável (mediana)" — necessário para satisfazer o critério de aceite, sem mudança de lógica (read-only).

## Issues Encountered

**Invocação da suíte completa (pré-existente, fora de escopo):** o gate de suíte usa `.venv/bin/python -m pytest -q` (175 passed), não o console-script `.venv/bin/pytest` que falha na coleta por causa de `tests/test_indicators.py` importar `from tests.test_ingest_ohlc import ...` (sys.path). Documentado no 11-01-SUMMARY; nenhum arquivo de teste foi tocado por este plano.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- app.py agora consome integralmente a camada de apresentação do Plan 01 — pronto para o checkpoint live (verificação visual da hierarquia DY recorrente/trailing e das duas linhas de payout).
- Engine de valuation intocada; nenhum golden de valuation rebaselinado.

## Self-Check: PASSED
- `app.py` modificado e parseia (`ast.parse` ok) ✓
- `src/analista/glossario.py` modificado ✓
- Commit `2e72450` (Task 1) presente no log ✓
- Commit `c0b6c0b` (Task 2) presente no log ✓
- `grep -c "presentation.header_dy" app.py` == 1, `delta_color="off"` == 1, `c.payout(c.ultimo_ano())` == 1, `presentation.linhas_multiplos` == 1 ✓
- `grep -c "CAGR lucro" app.py` == 0, `grep -c "média 3a" app.py` == 0, `grep -c 'a.multiplos.get("DP (payout)")' app.py` == 0 ✓
- `grep -c "média 3a\|CAGR\|teto de 100" src/analista/glossario.py` == 0; `payout_dual` contém "sustentável" ✓
- `.venv/bin/python -m pytest -q` → 175 passed (sem rebaseline de valuation) ✓

---
*Phase: 11-apresenta-o-hierarquia-e-trava-multi-ticker*
*Completed: 2026-06-28*
