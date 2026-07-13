---
phase: 04-rim-com-valor-terminal-ke-revisado
reviewed: 2026-07-13T13:33:34Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/analista/core/motores.py
  - src/analista/report/report.py
  - config.yaml
  - tests/test_motores.py
  - tests/test_backtest_bancos.py
  - tests/fixtures/fair_values_bancos.yaml
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-07-13T13:33:34Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed the iteration-2 (loop D-12) recalibration: the `roe_terminal` lever in
`motores.rim` (through-cycle normalization of the Gordon-perpetuity terminal, capped by
`excesso_sustentavel`) and the new "seguradora" routing branch in
`report._intrinseco_por_motor`.

**The numeric engine is sound.** I traced the terminal-normalization branch line by line:
`b_base_ri_final` correctly tracks `B_{n-1}` (the book base of the last window RI), the
`excesso_t = min(roe_terminal − ke, excesso_sustentavel)` cap saturates identically to the
legacy `RI_n` when `roe0 − ke ≥ cap` (so ITUB4 stays bit-identical, as claimed), and the
anti-bad-bank sign is preserved (`roe_terminal < ke` → negative terminal). Never-raise and
degradation paths hold: `roe_terminal=None` reproduces the legacy `RI_n`; `<3` valid ROE
points → `None` → legacy; `ke − g ≤ 0` degrades via `ddm.valor_gordon` returning `None`; the
seguradora route falls back to RIM on any `None` insumo. Backward-safety verified — the
function-default `roe_terminal=None` and all existing `motores.rim(...)` callers in tests
retain legacy behavior. The fronteiriço/candidate dispatch does **not** leak in practice (a
"seguradora"-token setor hard-routes to `financeira` with `fronteirico=False`, so the
candidate loop never re-enters the seguradora branch).

**However**, the seguradora lever introduces a user-facing methodology-label inconsistency
that directly violates the project's Core Value (numbers/labels must be faithful to the
method and self-consistent). One BLOCKER, two WARNINGs, two INFO.

## Critical Issues

### CR-01: Seguradora route mislabels its number as "RIM" — self-contradicting report

**File:** `src/analista/report/report.py:454` (in tandem with `:236` and `:458`)
**Issue:**
`a.motor_rotulo` is computed **before** the dispatch mutates `a.motor`:

```python
a.motor_rotulo = motores.MOTOR_ROTULO.get(a.motor, "")   # line 454: a.motor == "rim" here
a.intrinseco_motor = _intrinseco_por_motor(a.motor, c, a, cfg)  # line 458: sets a.motor = "seguradora" inside
```

For BBSE3 the seguradora branch (`report.py:236`) sets `a.motor = "seguradora"` and returns
the Gordon-franquia value (≈R$39,87). But `a.motor_rotulo` is never recomputed, so it keeps
the **RIM** label `"RIM — VPA + VP do excesso de ROE sobre Ke (banco/seguradora)"`.
Compounding this, `motores.MOTOR_ROTULO` (`motores.py:32`) has **no `"seguradora"` key**, so
even a recompute would need a new entry.

Result — the same report contradicts itself:
- header line (`report.py:888`): `... → motor seguradora`
- valuation section (`report.py:939` / `:1033` / alert `:603`): renders
  `a.motor_rotulo or a.motor` → **"RIM — VPA + VP do excesso de ROE sobre Ke …: R$ 39,87"**

The number 39,87 is correct, but it is attributed to a residual-income model when it was
produced by a single-stage dividend Gordon. For a tool whose entire value proposition is
method fidelity ("os números precisam ser fiéis ao método e consistentes entre si"),
labeling a DDM-franquia figure as "RIM — VPA + VP do excesso de ROE sobre Ke" is materially
misleading methodology. No test covers `motor_rotulo`, so the golden suite passes while the
render lies.

**Fix:** add the missing rótulo and recompute the label after the dispatch resolves the real
motor.

```python
# motores.py — MOTOR_ROTULO
"seguradora": "DDM-franquia — Gordon sobre o dividendo sustentável (seguradora capital-light)",

# report.py — after line 458, once _intrinseco_por_motor has resolved a.motor
a.intrinseco_motor = _intrinseco_por_motor(a.motor, c, a, cfg)
a.motor_rotulo = motores.MOTOR_ROTULO.get(a.motor, "")   # re-derive: dispatch may have re-routed to "seguradora"
```

This is safe for every other path: only the seguradora branch mutates `a.motor`, so for
rim/normalizado/dcf/nav/ddm the recomputed label is identical.

## Warnings

### WR-01: `_intrinseco_por_motor` documented "PURO" but mutates shared `a.motor`

**File:** `src/analista/report/report.py:236` (docstring at `:204`)
**Issue:** The helper's docstring says *"Dispatch PURO motor→intrínseco … reutilizável … é
consumido pelo dispatch principal … E pelo ramo fronteiriço (um motor por candidato)."* The
seguradora branch breaks that contract by writing `a.motor = "seguradora"` on the shared
`AnaliseAcao`. Today the fronteiriço reuse (`_veredito_fronteirico`, `:305`) is safe only by
accident: a setor containing "seguradora" hard-routes to `financeira` with
`fronteirico=False`, so the candidate loop never triggers the branch. That invariant lives in
a different module (`arquetipo.classificar`); any future change that lets a seguradora-token
ticker be fronteiriço, or that emits a "financeira" candidate for such a ticker, would
silently overwrite `a.motor` for every candidate iterated after it. A dispatch advertised as
pure and reused per-candidate should not mutate caller state.

**Fix:** stop mutating shared state inside the dispatch. Either return the resolved motor
alongside the value, or in `_veredito_fronteirico` probe candidates against a throwaway
`AnaliseAcao` (or snapshot/restore `a.motor` around the loop) so per-candidate dispatch
cannot leak into the committed `a`.

### WR-02: seguradora branch treats a zero Gordon value as success (no RIM fallback)

**File:** `src/analista/report/report.py:233-238`
**Issue:** The never-raise guard degrades to the legacy RIM only when `valor_gordon` returns
`None` (i.e. `ke − g ≤ 0`). But `dpa_recorrente()` can legitimately return `0.0` for a
seguradora with no sustainable dividend, and `ddm.valor_gordon(0*(1+g), ke, g)` returns
`0.0` (not `None`). The check `if v_seg is not None` is `True` for `0.0`, so the route
commits `a.motor = "seguradora"` and returns `0.0` instead of falling through to the RIM.
Downstream (`report.py:465`) then suppresses the non-positive value to `None` with an alert —
so the ticker ends up as "seguradora, sem preço-alvo" even though the book-anchored RIM could
have produced a real number. The comment on `:238` ("dado degenerado → cai para o RIM
legado") does not actually cover the `dpa=0`/`v_seg=0` case.

**Fix:** require a positive value before committing the route:

```python
if v_seg is not None and v_seg > 0:
    a.motor = "seguradora"
    return v_seg
# else fall through to the RIM (never-raise, não força a rota)
```

## Info

### IN-01: cross-module access to a private helper

**File:** `src/analista/report/report.py:229`
**Issue:** The branch reaches into `arquetipo._setor_casa_token` (leading underscore →
module-private). It is intentional and mirrored in tests, but it couples `report` to an
internal of `arquetipo`; a rename there breaks `report` silently.
**Fix:** promote `_setor_casa_token` to a public helper (e.g. `arquetipo.setor_casa_token`)
if it is meant to be a shared detection primitive.

### IN-02: seguradora label absent from `MOTOR_ROTULO` map

**File:** `src/analista/core/motores.py:32-38`
**Issue:** `MOTOR_ROTULO` enumerates rim/normalizado/dcf/nav/ddm but the new
`a.motor="seguradora"` value has no entry, so `MOTOR_ROTULO.get("seguradora", "")` yields
`""`. This is the second half of CR-01's root cause and should be fixed together with it (add
the "seguradora" key). Flagged separately because the missing map entry is a standalone
completeness gap in `motores.py`.
**Fix:** add the `"seguradora"` key (see CR-01 snippet).

---

_Reviewed: 2026-07-13T13:33:34Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
