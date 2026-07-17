---
phase: 11-crescimento-g-grow
verified: 2026-07-17T00:00:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 11: Crescimento / `g` (GROW) Verification Report

**Phase Goal:** Curar a metade `g` da Doença 1. Derivar `g_cap = (1+π_ciclo)(1+PIB_real)−1 ≈ 7,28%`
na engine e torná-lo a FONTE ÚNICA do crescimento terminal (substituindo as duas constantes gêmeas
de 2,5% `ddm.g_estavel` e `motores.rim.g_terminal`); fechar `g_T = min(roe_terminal×retenção,
g_cap)` por empresa no RIM; a fase explícita ADOTA `g_fundamentos`; manter o orçamento em 3 graus de
liberdade. BLIND-02 (invariância à inflação na engine) permanece xfail — a metade Ke é a Fase 12.

**Verified:** 2026-07-17
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `g_cap` is DERIVED in report.py (2 sites), never a literal 0.0728 | ✓ VERIFIED | `report.py:222` and `:433` both compute `g_cap = (1.0 + cfg.get("macro",{}).get("pi_ciclo",0.0518)) * (1.0 + cfg["ddm"].get("pib_real",0.02)) - 1.0`. `grep -rn "0.0728" src/ config.yaml calibracao.lock.yaml` → empty. |
| 2 | `g_cap` replaced `ddm.g_estavel` AND `motores.rim.g_terminal` at ALL call sites | ✓ VERIFIED | `grep -n 'cfg\["ddm"\]\["g_estavel"\]\|g_terminal=rim_cfg.get' src/analista/report/report.py` → empty. All 6 call sites (seguradora Gordon :241, RIM terminal :262, cíclica Gordon :307, dcf :310, DDM lens ×3 :528-538, convergência guard :715) use `g_cap`. |
| 3 | `g_T = min(roe_terminal × retenção, g_cap)` closed identity per company in RIM | ✓ VERIFIED | `report.py:252-254`: `_retencao = 1.0 - (c.payout_valuation() or 0.0)`; `_roe_term = _roe_through_cycle(c, rim_cfg)`; `_g_T = min(_roe_term*_retencao, g_cap) if _roe_term is not None else g_cap`; passed as `g_terminal=_g_T` at `:262`. |
| 4 | `π_ciclo` measured on the SAME window as `rf` (rf_ciclo_anos) — window symmetry | ✓ VERIFIED | `cli.py::_carimbar_macro` and `app.py` analyze block both call `ipca_ciclo_para_g`/`pi_ciclo_capm` with `cfg["capm"].get("rf_ciclo_anos", 10)` — same arg as `selic_ciclo_para_capm`/`ipca_deflatores_anuais`. |
| 5 | config.yaml has NO `ddm.g_estavel` and NO `motores.rim.g_terminal`; HAS `ddm.pib_real: 0.02` | ✓ VERIFIED | grep confirms absence of both leaves; `ddm.pib_real: 0.02` present at `config.yaml:104`. `macro.pi_ciclo: 0.0518` present at `:69`. |
| 6 | `calibracao.lock.yaml`: `PIB_real` path == `ddm.pib_real`; `motores.rim.g_terminal` NOT in `congelados`; budget still 3 degrees | ✓ VERIFIED | `PIB_real: {caminho: ddm.pib_real, valor: 0.02}` at lock:86-88; `g_terminal` absent from `congelados` (only a removal-comment remains at :147); `graus_de_liberdade` still exactly `ERP`/`n_fade`/`PIB_real`. `pytest -k "orcamento_de_knobs or knobs_batem_com_o_lock"` → 22 passed (partition-based test, not just count). |
| 7 | The explicit phase ADOPTS `g_fundamentos` (D-01); `g_historico` becomes fallback/sanity | ✓ VERIFIED | `report.py:426`: `g_alto = a.g_fundamentos if a.g_fundamentos is not None else a.g_historico`. Live check on ITUB4 (snapshot): `g_fundamentos=0.09588`, `g_alto == g_fundamentos` (Ke does not bind here: `ke=0.1822`). See note below on the 9.59% vs 10.29% figure. |
| 8 | Old-`g` LEVEL goldens DELETED (not updated), structural invariants extracted BEFORE deletion (split-before-delete), no orphan in classificacao.yaml | ✓ VERIFIED | `test_g_fund_menor_que_cagr_vira_teto_do_g_alto`, `test_teto_absoluto_025_quando_g_fund_e_cagr_explodem`, `test_trava_ke_quando_g_fund_supera_ke`, `test_rota_seguradora_bbse3_gordon_franquia`, `test_vulc3_cascata_domada_regressao` — all absent from `tests/*.py` (function bodies gone; only comments reference them as "deleted golden"). Replacement invariants present and registered in `classificacao.yaml` (verified by name). `pytest -m golden_nivel` → 22 passed, 0 CLASSIFICACAO ORFA. Collection: 501/523 collected, 22 deselected — no collection errors. |
| 9 | BLIND-02 (`invariancia_inflacao_engine_itub4`) is `1 xfailed`, never XPASS | ✓ VERIFIED | Ran directly: `.venv/bin/python -m pytest -k invariancia_inflacao_engine_itub4 -rX -q` → `522 deselected, 1 xfailed`. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/ingest/macro.py::ipca_ciclo_para_g` | helper mirroring `selic_ciclo_para_capm`, arithmetic mean, graceful fallback | ✓ VERIFIED | `macro.py:160-179`: `sum(por_ano.values())/len(por_ano)` if series non-empty, else `fallback`. Docstring states entry-point-only purity. |
| `config.yaml` | `macro.pi_ciclo` default, `ddm.pib_real`, no `ddm.g_estavel`/`motores.rim.g_terminal` | ✓ VERIFIED | Confirmed via grep above. |
| `calibracao.lock.yaml` | `PIB_real` migrated caminho, `g_terminal` out of congelados, 29-leaf partition | ✓ VERIFIED | Confirmed; partition enforced by `test_orcamento_de_knobs_e_exatamente_3` (structural set-equality, not a hardcoded count). |
| `src/analista/report/report.py` | `g_cap` derivation (2 sites) + g_fundamentos adoption + per-company g_T | ✓ VERIFIED | All 3 sub-claims confirmed by direct code read and live execution. |
| `tests/test_nao_regressao_grow.py` | non-regression against REAL 104-ticker snapshot (TAEE11/BBSE3/VULC3) | ✓ VERIFIED | File exists, loads `hs.CAMINHO_SNAPSHOT_LIMPO` (not synthetic fixtures), 2 tests, both pass. |
| `tests/test_invariantes_v24.py` | D-07 coverage test (terminal load-bearing + fade-only degradation) | ✓ VERIFIED | `test_terminal_load_bearing_nao_explode_e_degrada_para_fade_only` reads `excesso_sustentavel`/`ke_g_spread_min` from config (not hardcoded), exercises both release and fade-only branches. |
| `.githooks/commit-msg` (BLIND-05) | pre-commit-msg hook blocking config+golden co-change without justification | ✓ VERIFIED | `git config core.hooksPath` → `.githooks`; hook file present and executable; trailer present on commit `a461147` with no ticker mentioned. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `report.py` (g_cap derivation, 2 sites) | `cfg['macro']['pi_ciclo']` + `cfg['ddm']['pib_real']` | `g_cap = (1+pi_ciclo)(1+pib_real)-1` | ✓ WIRED | Confirmed at lines 222 and 433. |
| `report.py` (RIM terminal call, :255-265) | `motores.rim(g_terminal=...)` | `g_terminal = min(roe_terminal*retencao, g_cap)` | ✓ WIRED | Confirmed at line 254/262; `motores.rim` signature unchanged. |
| `cli.py::_carimbar_macro` | `macro.ipca_ciclo_para_g` | stamp `cfg['macro']['pi_ciclo']` in `rf_ciclo_anos` window | ✓ WIRED | Confirmed. |
| `app.py` analyze block | `macro.ipca_ciclo_para_g` (via cached `pi_ciclo_capm`) | stamp `CFG['macro']['pi_ciclo']` | ✓ WIRED | Confirmed at app.py:258, 892-895. |
| `tests/helpers_blindagem.py::choque_nominal` | `cfg2['macro']['pi_ciclo']` | shock leg migrated from `ddm.g_estavel`/`motores.rim.g_terminal` | ✓ WIRED | `grep -n "pi_ciclo" tests/helpers_blindagem.py` shows the shock leg in `choque_nominal`; no residual `g_estavel`/`g_terminal` references. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| BLIND-02 xfail, never XPASS | `.venv/bin/python -m pytest -k invariancia_inflacao_engine_itub4 -rX -q` | `522 deselected, 1 xfailed` | ✓ PASS |
| Default suite green | `.venv/bin/python -m pytest -q` | `499 passed, 1 skipped, 22 deselected, 1 xfailed` (0 failed) | ✓ PASS |
| Golden-nivel quarantine green, 0 orphan | `.venv/bin/python -m pytest -m golden_nivel -q` | `22 passed, 501 deselected` | ✓ PASS |
| Budget partition (3 degrees) | `.venv/bin/python -m pytest -k "orcamento_de_knobs or knobs_batem_com_o_lock or justificativa_de_knob" -m "" -q` | `3 passed` | ✓ PASS |
| Non-regression on real 104-ticker snapshot | `.venv/bin/python -m pytest -k nao_regressao_grow -m "" -q` | `2 passed` | ✓ PASS |
| No debt markers (TBD/FIXME/XXX) in phase-touched files | `grep -n -E "TBD|FIXME|XXX"` across report.py, macro.py, cli.py, app.py, config.yaml, calibracao.lock.yaml, phase test files | no matches (one false-positive `\uXXXX` unicode-escape doc string, not a marker) | ✓ PASS |
| Live ITUB4 execution | direct python: `report.analisar_acao(ITUB4, cfg)` | `g_cap=0.07284`, `g_fundamentos=0.09588`, `g_alto=g_fundamentos`, `intrinseco_motor=36.65` (finite, positive) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| GROW-01 | 11-01, 11-02 | `g_cap` derived, not typed (7,28%) | ✓ SATISFIED | Derivation confirmed in report.py; no literal 0.0728. |
| GROW-02 | 11-01, 11-02 | IPCA window same as `rf` | ✓ SATISFIED | `rf_ciclo_anos` symmetry confirmed in cli.py/app.py stamps. |
| GROW-03 | 11-02 | `g_T = min(ROE_T×retenção, g_cap)` closed identity per company | ✓ SATISFIED | Confirmed at report.py:254/262. **Note:** REQUIREMENTS.md traceability table still shows GROW-03 as `Pending` with `- [ ]` — this is a documentation gap only (GROW-01/02/04/05 were flipped to `[x]`/Complete in the same phase-close commit `18ab14c`, but GROW-03 was missed). The code and tests satisfy the requirement; only the tracking doc is stale. |
| GROW-04 | 11-02, 11-03 | Explicit phase adopts `g_fundamentos` over `g_historico` | ✓ SATISFIED | Adoption logic confirmed; ITUB4 measured `g_fundamentos ≈ 9,59%` (not the ~10,29%/10,24% cited in the original 2026-07-13 forensic audit/ROADMAP). This is a measured-value drift versus the initial diagnosis text, not a code defect — see note below. |
| GROW-05 | 11-03 | `excesso_sustentavel`/`ke_g_spread_min` load-bearing by test coverage (not recalibration) | ✓ SATISFIED | D-07 coverage test reads both knobs from config, exercises release + fade-only branches; `git diff config.yaml calibracao.lock.yaml` empty for plan 03 (confirmed via `git diff dcfd1a2^..20bb97d`). |

**Orphan check:** `.planning/REQUIREMENTS.md` maps exactly GROW-01..05 to Phase 11 (no additional GROW IDs). All 5 accounted for in plan frontmatter (`requirements:` fields across 11-01/02/03 cover GROW-01, GROW-02, GROW-03, GROW-04, GROW-05 — no orphans).

### Anti-Patterns Found

None blocking. No TBD/FIXME/XXX debt markers in any file modified by this phase. No stub returns, no empty handlers, no hardcoded empty data flowing to output.

**Info-level (non-blocking) observations:**
1. `tests/test_blindagem_orcamento.py::test_knobs_batem_com_o_lock` docstring (line ~127) still says "AS 30 FOLHAS" — stale from before the Phase 11 partition recount (now 29). Cosmetic only; the actual assertion is a dynamic set-equality against the lock file, not a hardcoded "30", so it is not a functional bug — confirmed by the test passing.
2. `.planning/REQUIREMENTS.md` GROW-03 checkbox/table entry left as `Pending` while GROW-01/02/04/05 were updated to `Complete` in the same phase-closing commit (`18ab14c`). Documentation-only gap; the functional requirement is verified in code.
3. ITUB4 `g_fundamentos` measured at ≈9,59% in the current snapshot vs. the ~10,29%/10,24% figures cited in `.planning/REQUIREMENTS.md`/`ROADMAP.md`/`11-CONTEXT.md` D-01 (from the 2026-07-13 forensic audit). The ADOPTION mechanism (using `g_fundamentos` instead of `min(g_historico, g_fundamentos)`) is correctly implemented and is what GROW-04 actually requires; the specific percentage cited in planning docs reflects the diagnosis snapshot at audit time, and primitives (`roe_valuation`, `payout_valuation`) may have shifted slightly since then through Phase 8-10 data/primitive fixes. This does not block Phase 11 — the sovereign numeric criterion (ITUB4 = R$37,22) is explicitly deferred to Phase 14 (VAL) per ROADMAP/REQUIREMENTS. Flagged for awareness heading into Phase 14, not as a Phase 11 gap.

### Human Verification Required

None. All must-haves are algorithmically verifiable (derivation formulas, config/lock state, test suite results) and were verified by direct execution, not by trusting SUMMARY.md narrative.

### Gaps Summary

No gaps. All 9 observable truths derived from ROADMAP Success Criteria + PLAN frontmatter must_haves
were independently verified against the actual codebase (not SUMMARY claims):

- `g_cap` is genuinely derived (2 sites, no literal), replaces both twin 2,5% constants at all 6
  call sites.
- `g_T = min(roe_terminal×retenção, g_cap)` closed identity is wired per-company into the RIM call.
- π_ciclo window symmetry with `rf_ciclo_anos` confirmed in both cli.py and app.py entry points.
- config.yaml/calibracao.lock.yaml migration is atomic and complete; budget remains exactly 3
  degrees of freedom, enforced by a structural partition test (not just a comment).
- Old-g level goldens (5 functions across 3 files) are genuinely deleted — not updated — with
  their structural invariants split out beforehand into named replacement tests, all registered in
  classificacao.yaml with zero orphans (verified via full collection: 501/523, 22 deselected, no
  collection errors).
- BLIND-02 independently re-run and confirmed `1 xfailed`, never XPASS.
- Default suite (`pytest -q`) independently re-run: 499 passed, 0 failed.
- `golden_nivel` marker independently re-run: 22 passed, 0 failed.
- Non-regression against the REAL 104-ticker frozen snapshot (not synthetic fixtures) exists and
  passes for TAEE11/BBSE3/VULC3.
- GROW-05 (D-07) coverage reads knobs from config, exercises both the release and fade-only
  branches of the RIM terminal.
- Commit `a461147` (the atomic knob-migration commit) carries the required
  `Knob-Change-Justification:` trailer with no ticker mentioned, satisfying BLIND-05/BLIND-06.

Three informational (non-blocking) documentation-staleness items are noted above for awareness
(stale "30 folhas" docstring comment, REQUIREMENTS.md GROW-03 checkbox not flipped, and the
g_fundamentos numeric drift vs. the original forensic-audit figure) — none affect Phase 11 goal
achievement or block progression to Phase 12.

---

*Verified: 2026-07-17*
*Verifier: Claude (gsd-verifier)*
