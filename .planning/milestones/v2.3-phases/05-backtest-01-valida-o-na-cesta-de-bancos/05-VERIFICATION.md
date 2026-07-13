---
phase: 05-backtest-01-valida-o-na-cesta-de-bancos
verified: 2026-07-13T05:30:00Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
---

# Phase 5: BACKTEST-01 — Validação na cesta de bancos Verification Report

**Phase Goal:** Deliver a reproducible validation harness (VAL-01) that runs the calibrated RIM
over the bank basket (ITUB4/BBAS3/BBSE3/BBDC4) and triangulates 4 reality anchors (VAL-02),
locked by a deterministic pytest gate.

**Verified:** 2026-07-13
**Status:** passed
**Re-verification:** No — initial verification

## Critical Framing Applied

This verification distinguishes the phase's deliverable (a validation TOOL) from the tool's
output (the calibration's actual fit to the basket). Per the D-12 design captured in
`05-CONTEXT.md` and executed faithfully in `05-04-SUMMARY.md`, the harness legitimately found
that the Fase 4 calibration does NOT generalize (1/4 tickers — only ITUB4 — falls inside the
±15% quorum band). This is the harness working correctly, not a Phase 5 defect. The gate encodes
the finding as `xfail(strict=True, raises=AssertionError)` — a tripwire, not a loosened
assertion — so the suite stays green while the failure remains visible and auditable. Fase 4
reopening and Fase 6 (deploy) blocking are the correct downstream consequences (D-12 loop), not
gaps in Phase 5's own scope.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A reproducible harness (script + test) exists, runs the cesta and prints, per ticker, the RIM intrinsic alongside the 4 anchors (Roadmap SC#1) | VERIFIED | `src/analista/backtest.py::rodar_cesta` is a pure function (no I/O/network) consumed identically by `scripts/backtest_bancos.py` (produces `out/backtest_bancos.md`, verified by running it — 4 rows × 12 columns) and by `tests/test_backtest_bancos.py` (imports `rodar_cesta`, `carregar_snapshot`, `carregar_fair_values`, `BANDA_PASS` from `analista.backtest`) |
| 2 | Harness reuses the production RIM path — never reimplements the formula | VERIFIED | `grep -c "motores.rim(" src/analista/backtest.py` = 0; RIM value sourced only via `report.analisar_acao(c, cfg).intrinseco_motor` (backtest.py:128-129) |
| 3 | Harness runs offline over a frozen snapshot fixture and is deterministic | VERIFIED | `carregar_snapshot()` reads `tests/fixtures/snapshot_bancos_2026-07-12.yaml` (raw fundamentals, no live calls); `test_backtest_determinismo` asserts two independent `rodar_cesta()` runs produce bit-identical RIM values per ticker — ran green |
| 4 | The 4 reality anchors are triangulated per ticker: (a) Graham+Bazin, (b) price, (c) fair-value table, (d) peer medians | VERIFIED | `rodar_cesta()` returns, per ticker, `graham` (`lentes.preco_justo_graham`), `bazin` (`lentes.preco_teto_bazin`), `preco` (`c.preco_atual`), `fv_min`/`fv_max` (from `tests/fixtures/fair_values_bancos.yaml`), `pvp_med`/`pl_med` (`statistics.median` over `lentes.metricas_par` across the basket, D-11) — all 4 columns populated with real (non-null, non-placeholder) numbers in the executed `out/backtest_bancos.md` |
| 5 | Fair-value table exists, versioned, sourced from consensus (not Graham/Bazin/RIM), approved by user before versioning (D-01/D-02/D-03) | VERIFIED | `tests/fixtures/fair_values_bancos.yaml` has min/max/data/fonte for all 4 tickers; `05-02-SUMMARY.md` documents the explicit approval checkpoint (Task 2, "usuário respondeu 'APPROVED' com as faixas exatas") before the versioning commit `b95a4e0` (Task 3) |
| 6 | A deterministic pytest gate locks quorum-3/4-±15% with the D-08 annotation rule (4th failure must be documented or it's a silent FAIL) | VERIFIED | `test_backtest_gate_quorum_e_anotacao` encodes `assert len(passes) >= QUORUM_MIN` + `for r in falhas: assert r["excecao_nota"]` verbatim (not loosened); marked `xfail(strict=True, raises=AssertionError)` scoped to `AssertionError` only (code-review WR-01 fix applied) so any unrelated infra break would surface as ERROR, not a silently swallowed XFAIL |
| 7 | Full existing suite stays green, no regression | VERIFIED | Ran `python -m pytest tests/ -q` myself: **442 passed, 1 xfailed** (baseline was 440 passed per `04-01-SUMMARY.md`/`05-04-SUMMARY.md` — net +2 passing +1 documented xfail, zero regressions) |
| 8 | Deviations remaining are documented, not hidden (D-12); if calibration fails beyond the permitted exception, it's registered and routed back to Fase 4 | VERIFIED | `05-04-SUMMARY.md` "Finding D-12" section documents ticker/RIM/FV/desvio/hypothesis for all 3 failing tickers (BBAS3 +54.6%, BBSE3 −35.7%, BBDC4 −46.3%) and explicitly states Fase 4 must reopen and Fase 6 is blocked; no spurious `excecao_nota` was added to the fixture (verified: `fair_values_bancos.yaml` has zero `excecao_nota` keys — correct, since 3 failures ≠ 1 documentable exception per D-08) |

**Score:** 8/8 truths verified

### Note on Roadmap SC#2 ("majority falls in a reasonable band")

Roadmap Success Criterion #2 for Phase 5 states the RIM intrinsic should not remain "cronicamente
~40-50% abaixo das âncoras" and that "a maioria cai na banda razoável." As currently measured by
the harness itself, this is **not yet true in reality** (only 1/4 tickers pass; deviations run in
both directions, not uniformly below). Per the critical framing given for this verification, this
is treated as a correctly-surfaced calibration finding owned by the D-12 loop (Fase 4 reopening),
not a defect in Phase 5's deliverable — the harness's job was to honestly determine and report
this, which it did (tripwire `xfail`, finding documented, no gate loosened, no exception fabricated).
This is not counted as a Phase 5 gap; it is the mechanism working as designed.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/capturar_snapshot_bancos.py` | One-time live capture script (D-05) via `build.montar_empresa` | VERIFIED | Exists, reads config, captures 4 tickers, has guard-corpo that fails loud on missing required fields (never fabricates), writes frozen snapshot; does not call `macro.selic_ciclo_para_capm` |
| `tests/fixtures/snapshot_bancos_2026-07-12.yaml` | Frozen raw fundamentals + rf_local + observed route, per ticker | VERIFIED | Tracked in git; contains ITUB4 and the other 3 tickers with `motor_observado`/`arquetipo_observado`/`intrinseco_motor_observado` |
| `tests/fixtures/fair_values_bancos.yaml` | Per-ticker min/max/data/fonte, user-approved | VERIFIED | Tracked in git; 4 tickers, all keys present, no premature `excecao_nota` |
| `src/analista/backtest.py` | Pure `rodar_cesta()` + loaders, consumes `analisar_acao`, never reimplements RIM | VERIFIED | Exports `rodar_cesta`, `carregar_snapshot`, `carregar_fair_values`; `BANDA_PASS = 0.15` named constant; zero `motores.rim(` calls; `cfg` copied (not mutated) — WR-02 fix confirmed present in code |
| `scripts/backtest_bancos.py` | Standalone wrapper → `out/backtest_bancos.md` (D-10) | VERIFIED | Ran it: produces 4-row, 12-column github-flavored markdown table via `tabulate`, reusing the same `rodar_cesta` |
| `tests/test_backtest_bancos.py` | Deterministic gate: route test, quorum/annotation gate (xfail), determinism test | VERIFIED | 3 tests: `test_backtest_cesta_rota_por_ticker` (PASS), `test_backtest_gate_quorum_e_anotacao` (XFAIL, strict, scoped to AssertionError), `test_backtest_determinismo` (PASS) — ran directly, matches documented output |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `scripts/capturar_snapshot_bancos.py` | `ingest.build.montar_empresa` | live capture per ticker | VERIFIED | `from analista.ingest import build` + `build.montar_empresa(tk, ano_base, n)` present |
| `tests/fixtures/snapshot_bancos_2026-07-12.yaml` | `report.analisar_acao` | offline reconstruction reproduces `a.intrinseco_motor` | VERIFIED | `carregar_snapshot()` reconstructs `CompanyData`; `05-01-SUMMARY.md` documents reproduction with <0.01 error vs. captured value |
| `src/analista/backtest.py::rodar_cesta` | `report.analisar_acao` | extracts `a.intrinseco_motor`/`a.motor`, never reimplements | VERIFIED | `backtest.py:128-129`; zero `motores.rim(` calls in module |
| `src/analista/backtest.py::rodar_cesta` | `lentes.metricas_par` + `statistics.median` | peer-multiple anchor (D-11), zero external source | VERIFIED | `backtest.py:120-124` |
| `scripts/backtest_bancos.py` | `out/backtest_bancos.md` | tabulate github + write, mirrors `cli.cmd_analyze` pattern | VERIFIED | Ran the script; file written, `os.makedirs(OUT_DIR, exist_ok=True)` pattern present |
| `tests/test_backtest_bancos.py` | `src/analista/backtest.py::rodar_cesta` | imports and reuses the SAME harness as the script | VERIFIED | `from analista.backtest import (BANDA_PASS, carregar_fair_values, carregar_snapshot, rodar_cesta)` |
| `tests/test_backtest_bancos.py` | `tests/fixtures/fair_values_bancos.yaml` | ±15% gate + 4th-exception annotation rule (D-08) | VERIFIED | `_passa()` uses `fv_min`/`fv_max`; gate loop checks `r["excecao_nota"]` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `rodar_cesta()` result | `rim` per ticker | `report.analisar_acao(c, cfg).intrinseco_motor`, `c` reconstructed from frozen YAML (not empty/hardcoded) | Yes — 4 distinct, non-null floats (32.88, 45.60, 25.38, 10.47), traced to real CVM/Yahoo capture | FLOWING |
| `out/backtest_bancos.md` | full table | `rodar_cesta()` output, formatted, written to disk | Yes — actual file generated on this run with real numbers matching `05-04-SUMMARY.md` | FLOWING |
| `test_backtest_bancos.py` gate | `passes`/`falhas` | same `rodar_cesta()` call | Yes — computed from real RIM/FV comparison, not stubbed | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Harness runs offline and produces 4 rows with 4 anchors | `python scripts/backtest_bancos.py` | Wrote `out/backtest_bancos.md`, printed table with real Graham/Bazin/preço/FV/P-VP/P-L values per ticker | PASS |
| Gate test suite for this phase is green (accounting for the documented xfail) | `python -m pytest tests/test_backtest_bancos.py -v` | `test_backtest_cesta_rota_por_ticker PASSED`, `test_backtest_gate_quorum_e_anotacao XFAIL`, `test_backtest_determinismo PASSED` — "2 passed, 1 xfailed" | PASS |
| Full suite has zero regressions | `python -m pytest tests/ -q` | `442 passed, 1 xfailed` (baseline 440 passed) | PASS |
| Harness is not reimplementing the RIM formula | `grep -c "motores.rim(" src/analista/backtest.py` | `0` | PASS |
| Named constants used, not magic numbers | `grep -c BANDA_PASS src/analista/backtest.py` / `grep -c QUORUM_MIN tests/test_backtest_bancos.py` | 2 / 2 | PASS |
| No motor/config files touched by this phase | `git diff --name-only 986e98a HEAD -- 'src/analista/core/*' 'src/analista/report/selo.py' config.yaml` | empty output | PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` convention used by this project; this phase's own runnable
verification IS the pytest suite + the standalone script, both executed directly above.
Step 7c: SKIPPED (no probe-* scripts declared or discovered; phase's own test suite serves this role and was run directly).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|------------|--------------|--------|----------|
| VAL-01 | 05-01, 05-03, 05-04 | Reproducible validation harness (script + test) over the bank basket | SATISFIED | `rodar_cesta` pure function reused identically by script and test; offline, deterministic (proven by `test_backtest_determinismo`); full suite green |
| VAL-02 | 05-02, 05-03, 05-04 | Triangulates 4 anchors per ticker; deviations explained, not hidden | SATISFIED | All 4 anchors computed and present in every result row; the 1/4-quorum finding is documented (not hidden) via `xfail(strict=True)` + explicit finding write-up in `05-04-SUMMARY.md`, correctly routing to the Fase 4 D-12 loop rather than being silenced or gate-loosened |

No orphaned requirements found — `.planning/REQUIREMENTS.md` maps only VAL-01/VAL-02 to Phase 5,
both claimed across the 4 plans.

### Anti-Patterns Found

None. Scanned `src/analista/backtest.py`, `scripts/backtest_bancos.py`,
`scripts/capturar_snapshot_bancos.py`, `tests/test_backtest_bancos.py` for
TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER/"not yet implemented"/empty-return patterns — zero matches.
The prior code review (`05-REVIEW.md`) found 0 critical, 2 warnings (WR-01 xfail scoping,
WR-02 cfg mutation) — both confirmed fixed in the current code (commit `84db478`), and 3 info-level
notes (no action required, none blocking).

### Human Verification Required

None. All must-haves are verifiable programmatically (code inspection + test execution), and the
one item that inherently required a human (fair-value consensus approval, D-01) already occurred
as an in-workflow checkpoint gate during plan 05-02 execution (documented in `05-02-SUMMARY.md`,
committed at `b95a4e0`) — this is not a post-hoc human-verification item, it is a completed
workflow gate.

### Gaps Summary

No gaps found. All 8 derived observable truths for VAL-01/VAL-02 are verified in the codebase by
direct inspection and by running the code myself (`pytest tests/ -q` → 442 passed, 1 xfailed;
`python scripts/backtest_bancos.py` → real 4-anchor table). The harness is reproducible, offline,
deterministic, reuses the production RIM path without reimplementing it, and triangulates all 4
required anchors. The calibration itself does not yet generalize to the basket (1/4 tickers pass
the ±15% band) — this is a real, correctly-surfaced finding that legitimately reopens Fase 4 and
blocks Fase 6 per the phase's own D-12 design, not a defect in what Phase 5 was asked to deliver.

---

*Verified: 2026-07-13*
*Verifier: Claude (gsd-verifier)*
