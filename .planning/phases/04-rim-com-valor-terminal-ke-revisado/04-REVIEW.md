---
phase: 04-rim-com-valor-terminal-ke-revisado
reviewed: 2026-07-12T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - config.yaml
  - src/analista/core/motores.py
  - src/analista/report/report.py
  - tests/test_motores.py
  - tests/test_vulc3_regressao.py
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-07-12
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Phase 04 adds a terminal (continuing) value to the RIM motor (Gordon perpetuity over the
last-window residual income), introduces three config knobs (`excesso_sustentavel`,
`g_terminal`, `ke_g_spread_min`), revises `ke_teto` 0.14→0.13 (CAL-02), and wires the new knobs
through the `report._intrinseco_por_motor` dispatch. The math is sound in the discounting
mechanics (no off-by-one in the terminal exponent; `RI_{n+1}=RI_n·(1+g)`; discount by
`(1+ke)^n` is correct), the never-raise contract holds, and the full suite (440 tests) passes.

No BLOCKER-level defects (no crash, injection, or data-loss path). However, three robustness/
correctness concerns stand out. The most material: the module documents a guard against "RIM
explosivo", but that guard only protects the **terminal** perpetuity growth — it does **not**
protect the **explicit window**, which diverges without bound as `n` grows whenever
`fade_para × retenção ≥ ke`. This condition is reached at realistic bank retention (~0.75+,
i.e. payout ≤ ~25%), so raising `n_fade` silently inflates the intrinsic. Secondary: the
"backward-safe" docstring claim is objectively false for the value-destroying-bank
(`roe0 < ke`) legacy path, and the `ke_rim` fallback default still hardcodes the rejected
0.14 `ke_teto`.

## Warnings

### WR-01: Window residual income diverges with `n` — the advertised anti-explosion guard misses the real explosion source

**File:** `src/analista/core/motores.py:104-116` (loop + terminal); config `config.yaml:239` (`n_fade`)
**Issue:** The docstring (`motores.py:89-93`) and `config.yaml:250-252` claim `ke_g_spread_min`
protects against "perpetuidade explosiva". That guard only bounds the **terminal** growth
(`ke − g_terminal ≥ 0.03`). It does nothing for the **explicit window**: the book compounds via
`b_t = b_{t-1}·(1 + roe_t·retencao)`, and each discounted residual income term is
`(roe_t − ke)·b_{t-1}/(1+ke)^t`. When `fade_para·retenção ≥ ke`, the book grows faster than the
discount rate, so the term sequence grows geometrically and the sum increases without bound as
`n` rises. For the shipped config (`ke_teto=0.13`, `roe0≈0.19` → `fade_para≈0.175`), this is
crossed at retention ≥ ~0.75 (payout ≤ ~25%), a realistic bank profile. Measured (VPA=19,
roe0=0.19, ke=0.13, excesso=0.045, g=0.025):

```
retencao=0.75:  n=10 → R$36.0 ,  n=20 → R$46.3   (fade_para·ret = 0.131 > ke = 0.13)
retencao=0.85:  n=10 → R$37.9 ,  n=20 → R$52.4
retencao=1.00,roe0=0.20: n=10 → 51.6, n=20 → 86.7, n=30 → 145.7  (monotonic, unbounded)
```

`n_fade` is presented as a freely-tunable "ajuste sem deploy" knob, but for high-retention names
it is a value amplifier with no convergence bound — a direct threat to the project Core Value
("números fiéis ao método e consistentes"). Config default `n=10` keeps the calibration basket
(retention ~0.53) bounded, so this is latent rather than active, hence WARNING not BLOCKER.
**Fix:** Either (a) add an explicit convergence guard — clamp/warn when
`fade_para·retenção ≥ ke − ε` before running the window, or (b) correct the docstring/config
comments to state that the guard covers only the terminal and that `n_fade` must stay small for
high-retention inputs, and pin a max `n_fade` in review. Minimum acceptable fix is (b);
(a) is the durable fix:
```python
# after computing fade_para, before the loop:
if fade_para * retencao >= ke:
    # window residual income does not converge in n — cap growth to keep RI bounded
    ...  # e.g. cap effective book-growth at ke, or degrade to a shorter n
```

### WR-02: "Backward-safe" claim is false for the value-destroying-bank (`roe0 < ke`) legacy path

**File:** `src/analista/core/motores.py:95-96, 102-103`
**Issue:** The docstring asserts the legacy 5-arg call `rim(vpa0, roe0, ke, retencao, n)`
"reproduz o comportamento D-02 (excesso_sustentavel=0.0 → fade a Ke)". That holds only when
`roe0 ≥ ke`. The old code was `fade_para = ke` unconditionally; the new default is
`fade_para = ke + min(roe0 − ke, excesso_sustentavel)`. With `excesso_sustentavel=0.0` and
`roe0 < ke`, `min(roe0−ke, 0.0) = roe0−ke < 0`, so `fade_para = roe0` (ROE stays flat, RI stays
negative) instead of the old fade-up to `ke` (RI → 0). Measured divergence for
`rim(22, 0.10, 0.125, 0.53, 10)`: new = **18.30**, old-behaviour = **19.92** (Δ R$1.61). No repo
caller hits this (the dispatch always passes `excesso_sustentavel`; the only legacy test call
uses `roe0 = ke`), so impact is contained to the documented API contract — but the claim is
objectively wrong and would mislead any future 5-arg caller.
**Fix:** Correct the docstring to scope the backward-safe claim to `roe0 ≥ ke`, or make the
legacy default truly equivalent:
```python
if fade_para is None:
    # legacy (excesso_sustentavel==0.0) must fade to ke even when roe0 < ke
    fade_para = ke + max(0.0, min(roe0 - ke, excesso_sustentavel)) if excesso_sustentavel else ke
```
(Only if preserving the exact D-02 legacy result is intended; otherwise just fix the docstring.)

### WR-03: `ke_rim` fallback `ke_teto` default is still the rejected 0.14 (contradicts CAL-02)

**File:** `src/analista/core/motores.py:149`
**Issue:** CAL-02 revised `ke_teto` 0.14→0.13 (`config.yaml:235`), with the phase rationale that
0.14 double-counts country risk and is wrong for a large-cap bank. But the defensive fallback in
`ke_rim` still reads `rim_cfg.get("ke_teto", 0.14)`. A config missing the `motores.rim` block
(the exact scenario this defensive `.get(...)` exists to survive, per the line-140 comment)
would silently clamp to the **rejected** 0.14 rather than the intended 0.13 — producing a higher
Ke and a materially lower intrinsic than the calibrated method, with no signal. `ke_piso` (0.11),
`ke_g_spread_min` (0.03), and `erp_banco` (0.045) fallbacks all match config; only `ke_teto`
drifted.
**Fix:**
```python
ke_clamp = max(rim_cfg.get("ke_piso", 0.11), min(ke, rim_cfg.get("ke_teto", 0.13)))
```

## Info

### IN-01: Unit test upper bound not tightened after CAL-02 (0.14→0.13)

**File:** `tests/test_motores.py:98`
**Issue:** `test_ke_rim_menor_que_ke_live_de_banco` still asserts `0.11 <= kr <= 0.14`. With the
revised `ke_teto=0.13`, this bound no longer catches a regression that re-introduced 0.14 — the
test would stay green even if CAL-02 were reverted. The sibling test
`test_rim_itub4_live_alvo_32_40` does pin `abs(ke - 0.13) < 1e-9` for beta=1.29, so the value is
covered elsewhere, but the generic ke_rim test is now loose.
**Fix:** Tighten the upper bound to `0.13` (the active clamp) so the test guards the CAL-02
revision directly: `assert 0.11 <= kr <= 0.13`.

### IN-02: Effectively-unreachable defensive branch in terminal value

**File:** `src/analista/core/motores.py:113-116`
**Issue:** `vp_terminal = tv / (1 + ke) ** n if tv is not None else 0.0`. The `else 0.0` is
unreachable in practice: the terminal branch only runs when `ke − g_terminal ≥ ke_g_spread_min`
(> 0), and `ddm.valor_gordon` returns `None` only when `ke − g ≤ 0` or an input is `None` — but
`ri_terminal` is always a float here. So `tv` is never `None` on this path. Harmless, but the
guard reads as if the terminal can silently zero out when it cannot, which slightly obscures the
real "terminal not released" path (the outer `if g_terminal is not None and ...`).
**Fix:** Either drop the dead `else 0.0` (rely on the outer guard) or add a comment noting the
branch is defensive-only. No functional change required.

---

_Reviewed: 2026-07-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
