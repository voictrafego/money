---
phase: 02-apresenta-o-e-travas-de-consist-ncia
reviewed: 2026-06-05T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - app.py
  - src/analista/glossario.py
  - tests/test_consistencia_modos.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-06-05T00:00:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed the Phase 02 changes: UI presentation additions in `app.py` (Ano-base
column in the Garimpar/Ranking tables, dual-payout rows in the Múltiplos tab,
"indisponível" labels for empresas dropped from the regression), three new glossary
tooltips in `glossario.py` (`ano_base`, `payout_dual`, `indisponivel`), and the new
cross-mode consistency test in `tests/test_consistencia_modos.py`.

No correctness or security defects were found. The presentation code respects the
read-only constraint: `app.py` reads canonical engine fields/functions (`c.ultimo_ano()`,
`c.payout_valuation()`, `a.multiplos["DP (payout)"]`) and never reimplements method
logic — `payout_valuation()` is the single canonical function shared by Analisar, Ranking,
and DDM, so showing it in the view does not fork the method. The new test passes (3 passed).

Two WARNING-level issues degrade the value of the new safety net and the glossary: one
glossary tooltip was added but never wired into the UI (dead code that defeats the purpose
of the addition), and one assertion in the new consistency test is tautological and proves
nothing. Three INFO items cover duplication and minor robustness.

## Warnings

### WR-01: New glossary tooltip `indisponivel` is dead code — never wired into the UI

**File:** `src/analista/glossario.py:111-115`
**Issue:** Phase 02 added the `"indisponivel"` glossary entry to explain the new
"indisponível" labels that appear in the Ranking table (Preço-alvo / Upside / Veredito
cells, `app.py:289-291`). However, no `help=h("indisponivel")` call exists anywhere in
the codebase — verified via grep across `app.py`, `src/`, and `tests/`. The other two
Phase-02 keys (`ano_base`, `payout_dual`) are correctly wired (`app.py:126`, `:235`, `:308`).
The user therefore sees "indisponível" cells with no explanatory tooltip, defeating the
stated intent of the addition (distinguishing the neutral "missing data" state from a
generic "—" or "cara"). The definition adds maintenance surface with zero runtime effect.
**Fix:** Wire the tooltip onto the affected columns via `column_config`, mirroring the
`Ano-base` pattern. For example, in the Ranking `st.dataframe` call (`app.py:307-308`):
```python
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
             column_config={
                 "Ano-base": st.column_config.Column("Ano-base", help=h("ano_base")),
                 "Veredito": st.column_config.Column("Veredito", help=h("indisponivel")),
             })
```
Alternatively, surface it in the existing `st.caption`/`st.info` text under the table. If
the tooltip is genuinely not wanted, remove the dead `indisponivel` entry from `G`.

### WR-02: Tautological assertion in the new consistency test proves nothing

**File:** `tests/test_consistencia_modos.py:91`
**Issue:** `assert pv == c.payout_valuation()` compares the result of
`c.payout_valuation()` (captured into `pv` on line 87) against a second call to the same
deterministic function. This is always true by construction and can never fail — it does
not verify cross-mode consistency, the determinism it claims to assert, or any relationship
between the two payout numbers (último-ano cru vs valuation). The test's docstring promises
this is "a rede de segurança que impede uma futura divergência de reintroduzir os bugs
CR-02 / CR-03 / WR-03", but this particular line contributes nothing to that guarantee. A
real regression where Ranking and Analisar diverge on the valuation payout would still pass.
**Fix:** Replace the tautology with an assertion that ties the two modes together, e.g.
verify the valuation payout is in the valid clamped range and that the same function is the
one used by both the Analisar DDM input and the Ranking `DP` vector:
```python
# Valuation payout is clamped to [0, 1] and is the SAME canonical function both
# modes feed into the regression / DDM (app.py:273 Ranking, report DDM input).
assert 0.0 <= pv <= 1.0
# Cross-mode: the value Ranking would push into the regression equals what the
# engine produces for Analisar's DDM — same canonical source, no fork.
assert c.payout_valuation() == pv  # only meaningful alongside the range/clamp check
```
At minimum, assert the clamp/range so the line exercises real behavior rather than identity.

## Info

### IN-01: Repeated O(n) linear scans of `empresas` inside the Ranking row loop

**File:** `app.py:301-302`
**Issue:** Each Ranking row does
`next(c.ultimo_ano() for c in empresas if c.ticker == r["empresa"])` and
`next(c.preco_atual for c in empresas if c.ticker == r["empresa"])` — two linear scans of
`empresas` per row, plus a separate scan elsewhere. It is correct (every `r["empresa"]`
originates from `nomes`/`empresas`, so `StopIteration` cannot occur today), but it couples
the view to that invariant and duplicates lookups. A future refactor that filters `ranking`
independently of `empresas` would turn the bare `next(...)` into an uncaught `StopIteration`.
**Fix:** Build a lookup dict once before the loop and read from it:
```python
emp_by_ticker = {c.ticker: c for c in empresas}
...
ce = emp_by_ticker[r["empresa"]]
"Ano-base": ce.ultimo_ano(),
"Preço atual": fmt_rs(ce.preco_atual),
```

### IN-02: Duplicated `column_config` Ano-base wiring across two modes

**File:** `app.py:235` and `app.py:308`
**Issue:** The `st.column_config.Column("Ano-base", help=h("ano_base"))` snippet is repeated
verbatim in the Garimpar and Ranking tables. Harmless duplication; if the Ano-base label or
help text changes, both sites must be updated in lockstep.
**Fix:** Optionally hoist to a module-level constant, e.g.
`ANO_BASE_COL = {"Ano-base": st.column_config.Column("Ano-base", help=h("ano_base"))}`
and spread it into both `column_config` dicts.

### IN-03: `payout_valuation()` can return `None`, rendering an extra dual-payout row as "—"

**File:** `app.py:128, 133`
**Issue:** `payout_proj = c.payout_valuation()` returns `None` when no payout is available
in the last 3 years (`fundamentals.py:84-85`). The view handles this gracefully —
`fmt_pct(None)` yields "—" — so there is no crash. The note is only that the new
"Payout p/ valuation (média 3a)" row will display "—" in that case while the "Payout
(último ano)" row may also be "—"; the user sees two "—" payout rows with no hint they
mean "no data". Acceptable for an edge company, but worth confirming this is the intended
presentation rather than collapsing to a single row when both are absent.
**Fix:** No change required if intended. If clearer UX is desired, skip the second row when
`payout_proj is None`, or label it explicitly (e.g. reuse the `indisponivel` tooltip from WR-01).

---

_Reviewed: 2026-06-05T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
