---
phase: 12-custo-de-capital-ke-ke
verified: 2026-07-17T00:00:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 12: Custo de capital (Ke) Verification Report

**Phase Goal:** Curar a outra metade da Doença 1 (o Ke) — colapsar os dois Ke simultâneos (17,3% no
DDM, 13,0% no RIM) num único Ke exibido == calculado, remover o clamp `ke_piso`/`ke_teto` por
aritmética (piso do Blume), aplicar ERP 4,5% sem prêmio small-cap, e beta setorial+Blume.
**Verified:** 2026-07-17
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Existe um único Ke no sistema; o Ke exibido é o mesmo que produziu o número; a matriz é construída em torno dele | ✓ VERIFIED | `motores.ke_rim` deleted (`grep -c "def ke_rim" src/analista/core/motores.py` = 0). `report.py:261` reads `ke=a.ke` for RIM; safety-route Gordon (L241), sensitivity matrix (L540-552), and display (`L993: Ke (CAPM): {_pct(a.ke)}`) all read `a.ke`. No second Ke variable exists anywhere in `report.py`. |
| 2 | `ke_piso`/`ke_teto` removed from code+config; Ke_min (11,07% Blume floor) > g_cap (7,28%) so nothing can diverge by arithmetic, not clamp | ✓ VERIFIED | `grep -Ec "erp_banco\|ke_piso\|ke_teto" config.yaml calibracao.lock.yaml` = 0 (no lines, no stale comments). Computed by execution: `g_cap = 0.07284`; `Ke_min` (rf offline default 0.105) = `0.11985`; `Ke_min` (rf ao vivo ~9,58%) = `0.11065` — both > g_cap. `tests/test_ke_validacao.py::test_ke_min_estrutural_acima_do_g_cap` asserts the inequality dynamically (not hardcoded); `test_regressao_104_sem_explosao` runs the real 104-ticker snapshot end-to-end (93 tickers with Ke, 0 offenders) — both pass live (`pytest -k "ke_min_estrutural or regressao_104"` → 2 passed). |
| 3 | ERP = 4,5% (Damodaran mature market), sem prêmio small-cap de 1,5% | ✓ VERIFIED | `config.yaml`: `erp_local: 0.045` (comment: "mercado maduro puro... Damodaran"); `calibracao.lock.yaml` grau ERP `valor: 0.045`. `grep -n "small.cap" config.yaml src/analista/core/capm.py` → no matches. Both changed together in commit `615843f` (verified via `git show --stat`). |
| 4 | Beta setorial+Blume (0,33+0,67×β); BB e Bradesco (mesmo risco) deixam de ter Ke com 1,7pp de diferença | ✓ VERIFIED | Executed live: `BBAS3` (β cru 0,891) and `BBDC4` (β cru 1,465), both sector "Bancos" (mediana β 1,2157). With `beta_blume` via the sectoral map, both get **identical** `beta_blume = 1.14455` → **identical Ke = 15.65%**. Recomputing with individual-beta-Blume only (no sector) reproduces the claimed 1,7pp gap: Ke_BBAS3=14.67% vs Ke_BBDC4=16.40% (Δ=1.73pp) — exactly matching the REQUIREMENTS.md description of the bug this fixes. |

**Score:** 4/4 roadmap truths verified (all VERIFIED)

### PLAN-level must-haves (12-01..04)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 5 | `data/beta_setorial.yaml` versioned artifact, setor→mediana(β), n≥3 only | ✓ VERIFIED | File exists, 14 sectors, includes "Bancos: 1.2157...". Derivation matches RESEARCH numbers exactly. |
| 6 | Three entry points (cli/app/backtest) stamp `cfg["capm"]["beta_setorial"]` — engine never recomputes | ✓ VERIFIED | `grep -n beta_setorial app.py src/analista/backtest.py src/analista/cli.py` shows stamping calls in all three; `report/setup.py` = 0 matches (Correção #2 respected). |
| 7 | D-06: analyze and rank see the SAME beta_setorial map and the SAME `a.ke` for the same ticker | ✓ VERIFIED | `tests/test_cli_rank_consistencia.py::test_rank_e_analyze_carimbam_o_mesmo_macro_e_produzem_o_mesmo_intrinseco` asserts `v_analyze["beta_setorial"] == v_rank["beta_setorial"]` and `v_analyze["ke"] == v_rank["ke"]`. Ran live: 1 passed. |
| 8 | `xfail_estritos()` == 0; BLIND-02b (`test_invariancia_inflacao_engine_itub4`) runs as a normal test and passes | ✓ VERIFIED | Ran `python3 -c "...h.xfail_estritos()..."` → printed `0`. Full suite shows `0 xfailed`. |
| 9 | Lock budget stays at exactly 3 degrees of freedom (ERP, n_fade, PIB_real); no 4th knob | ✓ VERIFIED | `calibracao.lock.yaml` `graus_de_liberdade` block lists exactly ERP (0.045), n_fade (10), PIB_real (0.02) — nothing else. `pytest -k "orcamento or knobs_batem or justificativa"` → 4 passed. |

**Combined score:** 9/9 must-haves verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `data/beta_setorial.yaml` | 14-sector median-β map, n≥3 | ✓ VERIFIED | Exists, matches RESEARCH figures exactly (e.g. Bancos 1.2157, Energia Elétrica 0.6154) |
| `src/analista/core/capm.py::beta_blume` | `0.33+0.67×base`, sector>individual fallback, never-raise | ✓ VERIFIED | Code matches spec exactly; `beta_cru is None → None`; sector fallback to raw beta when map absent |
| `src/analista/core/motores.py` | `ke_rim` deleted | ✓ VERIFIED | `grep -c "def ke_rim"` = 0; docstring rewritten to describe unified Ke |
| `src/analista/report/report.py` | `a.ke` via `beta_blume` (L470ish); RIM reads `a.ke` (L261) | ✓ VERIFIED | Confirmed at both call sites by direct read |
| `config.yaml` | `erp_local: 0.045`; no `erp_banco`/`ke_piso`/`ke_teto` | ✓ VERIFIED | Confirmed by grep, 0 matches for dead knobs (incl. comments) |
| `calibracao.lock.yaml` | ERP grau = 0.045; 3 congelados removed; scope 29→26 | ✓ VERIFIED | Confirmed; comment counts consistent (26/23), no stale "29 folhas" references |
| `tests/test_ke_validacao.py` | Structural inequality + 104-ticker regression, no hardcoded golden | ✓ VERIFIED | Both tests pass live; grep confirms `11,07`/`0.1107` only appear in comments, never in an assert line |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `report.py:261` | `a.ke` | RIM receives the single Ke, doesn't recompute | ✓ WIRED | `ke=a.ke,  # KE-01/D-09` confirmed live |
| `report.py:470-482` | `capm.beta_blume` | `a.ke` computed via sectoral+Blume beta | ✓ WIRED | `capm.beta_blume(c.beta, c.setor, cap.get("beta_setorial"))` feeds `capm.ke_local` |
| `cli.py` / `app.py` / `backtest.py` | `cfg["capm"]["beta_setorial"]` | Stamped at all 3 entry points | ✓ WIRED | grep confirms all 3; `report/setup.py` correctly untouched |
| `config.yaml` | `calibracao.lock.yaml` | Same-commit sanctioned knob diff | ✓ WIRED | `git show --stat 615843f` shows exactly these 2 files + `Knob-Change-Justification:` trailer with no ticker mention |

### Data-Flow Trace (Level 4)

`a.ke` traced end-to-end by direct execution (not just reading code): loaded `config.yaml`, called
`macro.carimbar_beta_setorial(cfg)`, ran `capm.beta_blume` + `capm.ke_local` for real tickers
(BBAS3/BBDC4) from the actual 104-ticker snapshot fixture. Output matched the expected unification
(identical Ke for same-sector tickers) and reproduced the pre-fix 1.7pp divergence when computed
without the sectoral map — confirming the data flows correctly from artifact → stamp → engine →
display, not just that the code compiles.

**Status:** ✓ FLOWING

### Behavioral Spot-Checks / Probe Execution

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full default suite | `python3 -m pytest -q` | `519 passed, 1 skipped, 20 deselected, 0 failed, 0 xfailed, 0 xpassed` | ✓ PASS |
| Quarantined golden_nivel | `python3 -m pytest -m golden_nivel -q` | `20 passed` | ✓ PASS |
| `xfail_estritos()` | `python3 -c "...h.xfail_estritos()"` | `0` | ✓ PASS |
| Knob budget partition | `pytest -k "orcamento or knobs_batem or justificativa"` | `4 passed` | ✓ PASS |
| D-06 cross-menu | `pytest -k "cli_rank_consistencia"` | `1 passed` | ✓ PASS |
| KE-04 validation (structural + 104-regression) | `pytest -k "ke_min_estrutural or regressao_104"` | `2 passed` | ✓ PASS |
| BLIND-04a / hook sanity | `pytest -k "blindagem_meta or hook_do_blind05"` | `4 passed, 1 skipped` | ✓ PASS |
| BB/Bradesco Ke unification (live computation) | ad-hoc Python script against real snapshot fixture | Identical Ke 15.65% (was 1.73pp apart w/o sector map) | ✓ PASS |

**Note on invocation:** a bare `pytest -q` (without `python3 -m`) fails at COLLECTION with `ModuleNotFoundError: No module named 'tests'` on two unrelated pre-existing swing-trade test files (`test_indicators.py`, `test_setup_report.py`, both from Phase 5, unrelated to Ke/KE-01..05). Confirmed via a scratch worktree checked out at the pre-phase-12 commit (`311bd34`) that this collection failure is **pre-existing and unrelated to Phase 12's changes** — it is a local sys.path/import-mode quirk of invoking `pytest` directly vs `python3 -m pytest` (which adds cwd to `sys.path`) and is not something Phase 12 introduced or is responsible for fixing. All suite numbers above were captured with `python3 -m pytest`, which is consistent with the project having a `[tool.pytest.ini_options]` config that assumes rootdir-relative imports of `tests.*`.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|------------|-------------|--------|----------|
| KE-01 | 12-02 | Único Ke; o que produz o número é o exibido | ✓ SATISFIED | `ke_rim` deleted; `a.ke` sole variable, used at RIM/route/matrix/display |
| KE-02 | 12-03 | ERP 4,5% sem prêmio small-cap | ✓ SATISFIED | `erp_local: 0.045`, no small-cap mention, config+lock coupled in one commit |
| KE-03 | 12-01 (infra) + 12-02 (consumo) | Beta setorial+Blume; BB/Bradesco same Ke | ✓ SATISFIED | Verified by live execution — BBAS3/BBDC4 identical Ke post-fix |
| KE-04 | 12-02 (code) + 12-03 (config) + 12-04 (validated by execution) | `ke_piso`/`ke_teto` removed; Ke_min > g_cap by arithmetic | ✓ SATISFIED | grep confirms removal; both structural inequality test and 104-ticker regression pass live |
| KE-05 | 12-02 | Ke exibido == Ke calculado; matriz em torno dele | ✓ SATISFIED | Single `a.ke` feeds display (L993) and matrix (L540-552, L1046) |

**Note on KE-03 tracking across plans:** `.planning/phases/12-custo-de-capital-ke-ke/12-01-SUMMARY.md`
frontmatter lists `requirements-completed: [KE-03]`, even though 12-01 is explicitly declared
"additive-only" and `a.ke` did not yet consume `beta_blume` (confirmed by the plan's own text:
"Este plano NÃO altera `a.ke`"). The REQUIREMENTS.md text of KE-03 describes the *observable*
outcome (BB and Bradesco converging on the same Ke) — which was only actually true after 12-02.
`12-02-SUMMARY.md`'s `requirements-completed` list is `[KE-01, KE-04, KE-05]` (KE-03 omitted,
presumably because it considered KE-03 already claimed by 12-01). This is a **minor bookkeeping
inconsistency** between per-plan frontmatter tracking and the phase-level REQUIREMENTS.md status
(which correctly marks KE-03 complete at the phase level, `[x]`, `Complete`, `Phase 12` — accurate,
since the codebase does satisfy KE-03 by the end of the phase, verified above by live execution).
This does not block the phase goal — the underlying capability exists and works — but the per-plan
requirement attribution in 12-01 was premature relative to when the visible behavior actually landed.
Flagged as **informational**, not a blocker.

No orphaned requirements found — REQUIREMENTS.md's traceability table (`KE-01..05 | Phase 12 |
Complete`) accounts for all 5 IDs, and all 5 appear in at least one plan's `requirements:` frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No genuine TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers found | — | Grep hits were false positives (`\uXXXX` JS-escape docstring in `app.py`; "TODOS" Portuguese word matches "TODO" substring) |
| — | — | No clamp reintroduced under another name | — | `grep -Ei "ke_teto\|ke_piso\|min\(ke\|max\(.*ke\|clamp"` in `report.py`/`motores.py` only returns explanatory comments confirming clamp removal, plus an unrelated pre-existing `payout_valuation` clamp (not a Ke clamp) |

### Human Verification Required

None. All must-haves were verifiable programmatically (grep, direct code read, live pytest execution,
and ad-hoc Python computation against the real 104-ticker snapshot fixture). This phase touches no
UI/UX, no visual rendering, and no external/real-time service — the Streamlit app.py wiring was
verified statically (grep for stamping calls) since it mirrors the already-verified cli.py pattern
1:1, and no runtime Streamlit behavior beyond stamping is in scope for KE-01..05.

### Gaps Summary

None. All roadmap success criteria and plan-level must-haves verified against actual codebase state,
by execution where the project's CLAUDE.md rules demand it (pytest suite counts, `xfail_estritos()`,
knob-budget partition, structural Ke_min > g_cap inequality, 104-ticker anti-explosion regression, and
a fresh ad-hoc computation reproducing/eliminating the BB/Bradesco 1.7pp Ke divergence). One minor,
non-blocking documentation inconsistency noted above (KE-03 attributed to 12-01 completion in that
plan's frontmatter, though its visible behavior landed in 12-02) — informational only, phase-level
REQUIREMENTS.md tracking is accurate.

---

*Verified: 2026-07-17*
*Verifier: Claude (gsd-verifier)*
