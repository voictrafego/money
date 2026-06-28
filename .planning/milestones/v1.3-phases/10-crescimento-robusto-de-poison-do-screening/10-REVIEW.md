---
phase: 10-crescimento-robusto-de-poison-do-screening
reviewed: 2026-06-27T23:45:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/analista/core/comparables.py
  - src/analista/core/growth.py
  - src/analista/core/screening.py
  - src/analista/report/report.py
  - tests/test_growth.py
  - tests/test_growth_robusto_multiticker.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-06-27T23:45:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Phase 10 swaps the endpoint-to-endpoint CAGR in `g_historico` for a log-linear OLS
estimator (`growth.crescimento_log_linear`), routes the BSD screening growth factors
through the same estimator over the winsorized series, and adds a `[0,1]` payout clamp
to the price-target regression fit (`ajustar_regressao_pl`).

The clamp logic is correct and symmetric (fit and prediction both clamp to `[0,1]`,
confirmed by the multiticker tests), the `r2`/`ss_tot` division is guarded, the
`None`/`<=0` guard in the estimator prevents `log` of non-positive values, and the
Screening↔Analisar equality (D-04) holds because both paths consume the identical
`serie_winsorizada(serie("lucro_liquido"))`. No crashes, security issues, or
division-by-zero paths were found.

However, the review surfaced four correctness/fidelity defects centered on (1) the
estimator's implicit assumption of uniform 1-year spacing, which the data layer
violates by silently dropping missing years; (2) a real, undocumented change to the
`g_historico` None-frontier; (3) stale rationale comments asserting a clamp parity with
the DDM that no longer exists; and (4) a user-facing label still calling the metric
"CAGR". None rise to BLOCKER (no crash/security/data-loss), but all degrade numerical
correctness or the project's stated Core Value ("números fiéis ao método e consistentes
entre si").

## Warnings

### WR-01: Log-linear estimator assumes uniform 1-year spacing, but the series drops missing years

**File:** `src/analista/core/growth.py:73-75` (with `fundamentals.serie` and `normalizacao._limpar`)
**Issue:** `crescimento_log_linear` builds the time axis as `x = np.arange(len(serie))`
and the docstring states "passo de x = 1 ano … anualizado por construção". This holds
only if the series has one point per consecutive calendar year. But the series fed in
production comes from `c.serie("lucro_liquido")` → `[d[a] for a in anos if a in d]`
(drops any year missing from the dict) and then `serie_winsorizada` →
`_limpar` (drops `None`). A company missing a year (e.g. lucro for 2015,2016,2018,2019;
2017 absent) yields a 4-element series with `x=[0,1,2,3]`, so a 5-calendar-year span is
regressed as 4 consecutive steps and `g = exp(slope)-1` is **mis-annualized**
(growth overstated). This feeds `g_alto`/DDM and the BSD factors. It does NOT break the
Analisar↔Screening equality (both use the same collapsed axis), but it is an absolute
numerical-correctness defect. (The old endpoint CAGR with `n = len-1` had the same flaw,
so this is inherited, not introduced — but the new docstring now explicitly claims
annual spacing that the pipeline cannot guarantee.)
**Fix:** Anchor `x` to the real calendar years instead of a positional index, e.g. pass
the year list alongside the values and use `x = np.array(anos) - anos[0]`; or document
loudly that the estimator requires gap-free annual series and have the data layer
forward-fill / reject series with calendar gaps before calling it.

### WR-02: `g_historico` None-frontier silently changed; docstring claim "IDÊNTICA ao CAGR" is false

**File:** `src/analista/core/growth.py:65-72`, `src/analista/report/report.py:79-80`
**Issue:** The previous `g_historico` was `growth.cagr(lucros[0], lucros[-1], len-1)`
(confirmed via `git show` of the parent commit) — it returned `None` only when an
**endpoint** was `<=0`. The new `crescimento_log_linear` returns `None` when **any**
point is `<=0` (line 71). So a company with a single interior loss year but positive
first/last lucro now flips from a finite `g_historico` to `None`, which cascades to
`g_alto` falling back to `g_fundamentos` and can change the DDM verdict. The docstring
asserts "Fronteira de None IDÊNTICA ao CAGR (D-03)" while simultaneously defining the
broader "QUALQUER ponto None/≤ 0 ⇒ None" rule — the two statements contradict each
other, and the frontier is in fact stricter than the CAGR it replaced. Interior loss
years are common for cyclical dividend names, so this is a material, undocumented
behavior change.
**Fix:** Drop the false "IDÊNTICA ao CAGR" wording and document the real (stricter)
frontier: "returns None if ANY point ≤ 0 — stricter than the old endpoint CAGR." If the
prior endpoint-only behavior is desired for tolerance to a single loss year, gate the
non-positive check to the endpoints or add an explicit fallback, but do not claim parity
that the code does not provide.

### WR-03: Stale rationale — regression clamp claims to mirror a DDM payout clamp that no longer exists

**File:** `src/analista/core/comparables.py:154-156`, `src/analista/report/report.py:134`
**Issue:** `preco_alvo_por_regressao` comments "Mesmo clamp do Analisar antes do DDM
(report.py: payout_proj = min(media_3a, 1.0))", and `report.py:134` comments
`payout_proj = c.payout_valuation()  # média 3a + clamp 1.0`. Neither is true:
`payout_valuation()` → `mediana_payout()` returns the **median over the full series with
NO clamp and NO 3-year window** (Phase 9 D-03). So the DDM in Analisar feeds a raw
payout (TAEE11 ≈ 2.16) into `dpa_inicial = lpa*(1+g_alto)*payout_proj`, while the
regression clamps payout to `[0,1]`. The clamp in the regression is itself justified
(the fit was calibrated on `[0,1]`), but the comments assert a Screening↔Analisar parity
that is factually false and will mislead the next maintainer into thinking the DDM also
clamps. The triple-wrong report comment ("média 3a + clamp 1.0" for a no-clamp full-series
median) compounds the confusion.
**Fix:** Correct both comments. In `report.py:134` describe the actual behavior:
`# mediana do payout sobre a série completa, SEM clamp (pode ser >1.0, ex. TAEE11)`. In
`comparables.py:154` state that the clamp is local to the regression domain and that the
DDM intentionally does NOT clamp — they are deliberately different, not "the same clamp".

### WR-04: User-facing label still calls the metric "CAGR" after switching to log-linear regression

**File:** `src/analista/report/report.py:406` (and the DDM-FIX-02 comment at lines 86-89)
**Issue:** The estimator is now a log-linear OLS trend, but the rendered report still
prints `- g histórico (CAGR do lucro): ...` and the inline comment at lines 86-89 still
describes it as "CAGR sobre a série normalizada". Given the project Core Value ("os
números precisam ser fiéis ao método … e consistentes"), showing "CAGR" to the user when
the number is a regression slope is a fidelity defect — the displayed methodology label
no longer matches the computation.
**Fix:** Change the label to reflect the method, e.g.
`- g histórico (tendência log-linear do lucro): ...`, and update the lines 86-89 comment
from "CAGR sobre a série normalizada" to "tendência log-linear sobre a série normalizada".

## Info

### IN-01: Redundant length guard before `crescimento_log_linear`

**File:** `src/analista/report/report.py:79`
**Issue:** `if len(lucros) >= 2: a.g_historico = growth.crescimento_log_linear(lucros)`
duplicates the function's own `len(serie) < 2 ⇒ None` guard (growth.py:69). Harmless but
dead defensiveness; if `len < 2` the function already returns `None` and `a.g_historico`
defaults to `None`.
**Fix:** Drop the `if` and call unconditionally: `a.g_historico = growth.crescimento_log_linear(lucros)`.

### IN-02: `preco_alvo` upside/pl_corrente degrade silently when `preco_corrente == 0`

**File:** `src/analista/core/comparables.py:159-161`
**Issue:** The guard only rejects `None` for `preco_corrente`, not `0.0`. With
`preco_corrente == 0`, `pl_corrente = preco_corrente / lpa` is `0`, `upside` becomes
`None` (typed `float` on `PrecoAlvo`), and `subavaliada` is `True` for any positive
`preco_alvo`. Unrealistic for a traded stock but an untested boundary that produces a
half-populated `PrecoAlvo`.
**Fix:** Treat non-positive `preco_corrente` as invalid: add `or preco_corrente <= 0` to
the guard at line 152, mirroring the `lpa <= 0` check.

### IN-03: A single zero/negative dividend (or FCO) year nullifies the whole BSD growth factor to neutral

**File:** `src/analista/core/screening.py:267-268` (with `_padronizar_absoluto` None→50)
**Issue:** `crescimento_serie` winsorizes (which keeps zeros/negatives — `_limpar` only
drops `None`) and then `crescimento_log_linear` returns `None` for any point `<= 0`. A
company with one zero-dividend or one negative-FCO year therefore gets `None` for that
factor, which `_padronizar_absoluto` maps to the **neutral 50**, not a penalty. So a year
of skipped dividends produces a better-than-zero score on the dividend-growth factor
rather than dragging the BSD down. This is consistent with the documented "ausente =
neutro" design, but for `crescimento_*` the value isn't truly absent — it was suppressed
by a real bad year, and neutral-50 understates the risk.
**Fix:** If desired, distinguish "estimator suppressed by a non-positive point" from
"data absent" and route the former to a low (penalizing) score rather than neutral 50;
otherwise document explicitly that a single non-positive year neutralizes the factor.

---

_Reviewed: 2026-06-27T23:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
