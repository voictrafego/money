---
phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo
fixed_at: 2026-07-12T00:00:00Z
review_path: .planning/phases/03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo/03-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 3
skipped: 1
status: partial
---

# Phase 3: Code Review Fix Report

**Fixed at:** 2026-07-12
**Source review:** .planning/phases/03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4 (CR-01, WR-01, WR-02, WR-03)
- Fixed: 3 (CR-01, WR-01, WR-03)
- Skipped: 1 (WR-02 — design tradeoff, breaks deliberate golden)

Full test suite stayed green throughout: 434 → 435 passing (one new covering test added
for CR-01). The firewall was respected — no new import of `report.py` into `selo.py` was
introduced.

## Fixed Issues

### CR-01: Motor degrades but DDM band survives → verdict/metric were DDM-derived yet labeled as the motor

**Files modified:** `src/analista/report/report.py`, `app.py`, `tests/test_report.py`
**Commit:** 5ea45ce
**Status:** fixed: requires human verification (touches verdict/label logic on a previously
untested degradation path)

**Applied fix:**
- Added an explicit `elif a.motor != "ddm" and a.vmin is not None and a.vmax is not None:`
  branch right after the ensemble block in `analisar_acao`. When the archetype motor degrades
  (`intrinseco_motor is None`) but the DDM band survives, `banda_do_motor` now stays `False`
  and an honest alert is appended: *"Motor '<motor>' (<rotulo>) degradou; a faixa exibida vem
  do DDM (contraponto), não do motor do arquétipo."*
- `app.py` metric label now falls back to `"Intrínseco (DDM)"` whenever
  `banda_do_motor is False` (not just when `motor == "ddm"`), so a DDM-derived band is never
  displayed under the motor's name.
- CLI markdown `ddm_e_lente` is now `a.motor != "ddm" and a.banda_do_motor`, so the DDM is no
  longer captioned as *"lente conservadora"* when it is the only/primary valuation shown.
- Added covering test `test_cr01_motor_degrada_mas_ddm_sobrevive_rotula_ddm` (monkeypatches
  `motores.rim` to `None` while leaving the DDM live) — the motor-None/DDM-survives path that
  the review flagged as untested. Asserts `banda_do_motor is False`, the honest degradation
  alert, and that the markdown neither says "lente conservadora" nor emits the motor section.

**Why human verification:** the fix changes which band feeds the price verdict/label on a path
that had no golden. The engine numbers are unchanged; only attribution/labeling changed. A
developer should confirm the honest-attribution wording matches product intent.

### WR-01: VER-02 borderline case — the "Intrínseco (<motor>)" metric contradicted the uncertainty banner

**Files modified:** `app.py`
**Commit:** eb2906a
**Status:** fixed

**Applied fix:** In the render, after computing `intervalo` from `vmin/vmax`, the m2 band is
now suppressed (`intervalo = "—"`) when `getattr(a, "arquetipo_incerto", False)` is set. On a
fronteiriço the classification is uncertain and `_veredito_fronteirico` never touches
`vmin/vmax`, so the primary-archetype band would contradict the candidatos range shown in the
"Classificação incerta" banner (worst case: the 0-candidate branch suspends the verdict while
the metric still showed a healthy band). The honest range now lives only in the candidatos
banner. Mirrors the existing selo suppression on VERIFICAR.

### WR-03: "Intrínseco (<motor>)" band silently blended motor + DDM contraponto; representation differed from the CLI

**Files modified:** `app.py`, `src/analista/report/report.py`
**Commit:** 69dd243
**Status:** fixed

**Applied fix:**
- `app.py`: when the band is the ensemble band (`banda_do_motor` True) and there is **no**
  divergence banner (< 2×), a one-line `st.caption` now states that the faixa combines the
  archetype motor and the DDM contraponto, showing both numbers — so the user is not misled
  into reading a "RIM" bound that is actually the DDM. On divergent cases the existing
  divergence banner already shows both numbers, so the caption is intentionally skipped.
- `src/analista/report/report.py`: the CLI markdown "Valuation pelo motor do arquétipo" section
  now also prints the ensemble band (`Faixa do veredito (motor × DDM contraponto): R$ x–y`)
  when `banda_do_motor` is set, aligning the CLI representation with the app metric (both now
  show the motor point **and** the band, instead of app-band vs CLI-point).

## Skipped Issues

### WR-02: SAN-01 reetiqueta premise is broken by the VER-01 ensemble — can mislabel a genuine overvaluation

**File:** `src/analista/report/report.py:107-180` (`_guarda_san01`), interaction with `495-503`
**Reason:** skipped — design tradeoff that would break a deliberate golden, not a clear defect.

The proposed fix adds a directional guard requiring `a.intrinseco_motor >= a.preco_atual` (or
`>= contraponto * k`) before SAN-01 reetiquets. However, the e2e golden
`test_san01_e2e_itub4_nao_estampa_evitar` (`tests/test_guardrails_ddm.py:260`) deliberately
locks in the current behavior: ITUB4-like fixture with preço 70, VPA 5.18 → RIM ≈ single digits
(i.e. `intrinseco_motor` **well below** `preco_atual`), and asserts `san01_reetiquetado is True`
and `"Evitar" not in verdict`. Adding the directional guard would block the reetiqueta on
exactly that fixture and fail the golden.

Per the task's explicit guidance ("if a finding is genuinely a design tradeoff rather than a
defect — e.g. WR-02's directional check for SAN-01 — you may skip it, recording an explicit
rationale rather than forcing a change that breaks a deliberate golden"), this finding is left
for a human product decision. The SAN-01 backstop is intentionally designed to reframe
high-ROE names where the single-stage DDM is structurally too conservative, regardless of
whether the motor also reads "expensive"; whether to additionally require directional motor
agreement is a product-design question, not a mechanical bug fix. Changing it here would break
the encoded intended behavior.

**Original issue:** SAN-01 fires on `SOBREAVALIADA` (price above `max(motor, DDM)`) without
checking that the motor directionally disagrees with the DDM, so a genuinely overvalued
high-ROE name can get its "Evitar" quadrant suppressed and be re-framed as "the DDM is too
harsh" even when the motor agrees the stock is expensive.

## Info findings (not in scope: critical_warning)

IN-01 (fronteiriço "entre X e Y" named pair) and IN-02 (redundant local `import json`) were
outside the fix scope (critical_warning) and were not addressed.

---

_Fixed: 2026-07-12_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
