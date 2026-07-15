---
phase: 08-sanidade-dos-dados-san
verified: 2026-07-15T00:49:38Z
status: passed
score: 7/7 must-haves verified
overrides_applied: 0
---

# Phase 8: Sanidade dos Dados (SAN) Verification Report

**Phase Goal:** Fazer o pipeline **saber quando o dado está errado**. Os asserts vêm **antes** dos
consertos de propósito: eles **são** o teste de regressão da Fase 9 — precisam existir antes para
provar que o conserto funcionou, ticker a ticker. Inclui o spike que pode revelar um terceiro bug de
dados que os knobs do v2.3 mascaravam.

**Verified:** 2026-07-15T00:49:38Z
**Status:** passed
**Re-verification:** No — initial verification

## Note on adversarial verification method

Per this project's explicit convention (CLAUDE.md + task brief), "dirty data still dirty" is the
correct outcome for this phase — the checks are designed to *detect*, not fix. I did not treat the
62-sujos baseline, the stale "41 tickers" wording in ROADMAP.md success criterion 1, or any
still-flagged ticker as a gap. Instead I independently re-executed the two structural guards the
SUMMARYs claim were "proven by execution" rather than trusting the SUMMARY narrative:

1. **D-04 guard (pipeline wiring).** Commented out `sanidade.aplicar_sanidade(c)` in
   `src/analista/ingest/build.py`, ran `pytest -k sanidade_e_chamada` → **went red**
   (`AssertionError: assert 'nao_avaliada' != 'nao_avaliada'`). Restored the file via
   `git checkout --`, re-ran → green. Confirms the wiring is real, not just a comment.
2. **D-06 guard (baseline monotonicity).** Deleted the `SAN-01` flag entry for GOAU4 from
   `tests/fixtures/baseline_sanidade.yaml`, ran `pytest -k baseline_de_sujos_so_encolhe` →
   **went red**, listing `('GOAU4', 'SAN-01')` as a "ressuscitado" pair. Restored via
   `git checkout --`, re-ran → green. Confirms the regression baseline actually constrains.

Both guards are real, not decorative. This is the evidence basis for treating the SUMMARY claims as
verified rather than merely asserted.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ingestion reconciles `num_acoes × preço ≈ market cap`, flags GOAU4/CGRA4, symmetric 3× salto check flags ITUB4/BRSR6/CGRA4 | ✓ VERIFIED | `src/analista/core/sanidade.py::checar_san01/checar_san02`; baseline confirms GOAU4→SAN-01, CGRA4→SAN-01+SAN-02, ITUB4→SAN-02, BRSR6→SAN-02 (measured directly from `tests/fixtures/baseline_sanidade.yaml`) |
| 2 | Reconciliation `dividendos_CVM ≈ DPA_yahoo × num_acoes` points at JCP perdido; base-consistency check flags MRFG3/CSNA3/ALUP11/EQTL3 | ✓ VERIFIED | `checar_san03` (two signals, JCP-perdido + CVM↔Yahoo reconciliation) and `checar_san04`; baseline confirms BRSR6→SAN-03, all four named tickers→SAN-04, and ITUB4/BBDC4 do NOT get SAN-03 (zero false positive, matches "escapam por acidente") |
| 3 | Clean surplus (`ΔB ≈ LL − DIV`) measured, violation reported as DATA not exception | ✓ VERIFIED | `checar_san05` returns an `Aviso` with the median residual as `fator` (adimensional), never raises; `tests/test_sanidade_checks.py::test_san05_reporta_o_clean_surplus_como_dado` |
| 4 | No assert raises an exception; all degrade to warning + lowered confidence; engine keeps producing a response on dirty tickers | ✓ VERIFIED | `aplicar_sanidade` wraps every check in `try/except Exception`; independently re-ran `test_nenhum_check_levanta_em_nenhum_ticker_do_snapshot` (iterates all 104 snapshot tickers, asserts `diag["quedas"] == 0`) — passed |
| 5 | SAN-07 spike answers both questions in writing, with per-bank numbers; both answers are NO; PL account corrected from 2.03 to 2.07/2.08; no knob moved | ✓ VERIFIED | `.planning/spikes/san-07-ihcd-at1-fvoci.md` exists (6285 bytes), contains "2.08" (14×) and "Ajustes de Avaliação Patrimonial" anomaly declared (2×); independently re-ran `scripts/spike_san07_bancos.py` → exit 0, printed veredito "As duas respostas são NÃO" for all 4 banks; `git diff --name-only` for 08-02 plan excludes `config.yaml`/`calibracao.lock.yaml` |
| 6 | `aplicar_sanidade` is actually called by the real pipeline (`montar_empresa`), proven by execution, not just present as a function | ✓ VERIFIED | Independently re-ran the evasion: commented out the call in `build.py` → `pytest -k sanidade_e_chamada` failed; restored → passed (see method note above) |
| 7 | A versioned baseline captures which flags fire today (never a R$/level), and a monotonicity test proves the "sujos" list can only shrink | ✓ VERIFIED | `tests/fixtures/baseline_sanidade.yaml` (104 tickers, 62 sujos, 117 pares, all buckets are `~1eN` strings, zero R$/market_cap/intrinseco literals); independently re-ran the evasion (deleted GOAU4/SAN-01 pair) → `test_baseline_de_sujos_so_encolhe` failed listing the resurrected pair; restored → passed |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/sanidade.py` | 5 pure checks + `Aviso` + `_bucket` + `aplicar_sanidade` + limiares as module constants | ✓ VERIFIED | 469 lines; `checar_san01..05`, `_bucket` (never raises on ≤0, verified via direct read), `aplicar_sanidade` with try/except-per-check and quedas counter; no `raise` statements; limiares are module-level constants, not in `config.yaml`/`calibracao.lock.yaml` |
| `src/analista/ingest/build.py` | single call site `aplicar_sanidade(c)` wired into `montar_empresa`, comment BUG-JCP fixed | ✓ VERIFIED | line 142: `sanidade.aplicar_sanidade(c)`; import at line 13; comment (lines 120-130) states the corrected direction (CVM loses JCP, not Yahoo) |
| `src/analista/ingest/cvm.py` | reads `3.11.01`, `pl_nao_controladores`, `proventos_filtro_amplo` via wide filter | ✓ VERIFIED | `_distribuicoes_proventos_amplo` (separate function, narrow filter untouched), `3.11.01` read for `lucro_controlador`, wide regex `dividendo|juros sobre.*capital` |
| `src/analista/ingest/prices.py` | `market_cap`, `implied_shares_outstanding`, `splits` (full history), `_fetch_splits` never-raise | ✓ VERIFIED | `DadosMercado` dataclass fields present; `_fetch_splits` wraps in try/except; `sharesOutstanding` assignment intact (not swapped for implied) |
| `src/analista/core/fundamentals.py` | `CompanyData` gains `avisos`, `confianca="nao_avaliada"` default, diagnostic fields | ✓ VERIFIED | lines 57-71: all fields present with correct defaults |
| `tests/fixtures/snapshot_sanidade_2026-07-14.yaml` | frozen dirty snapshot of 104 tickers, includes market_cap/splits, MRFG3 present without market data | ✓ VERIFIED (via 08-03-SUMMARY + wired tests passing) | `pytest -k sanidade_snapshot` passes offline; snapshot backs the baseline used above |
| `.planning/spikes/san-07-ihcd-at1-fvoci.md` + `scripts/spike_san07_bancos.py` | SAN-07 written answer + reproducible script | ✓ VERIFIED | both exist; script re-executed successfully (exit 0), output matches doc |
| `tests/fixtures/baseline_sanidade.yaml` + `tests/test_sanidade_baseline.py` | detection golden (not level golden), monotonicity by (ticker, check) pair | ✓ VERIFIED | 104 tickers, 62 dirty, zero R$/market_cap literals; monotonicity guard independently re-executed (see above) |
| `scripts/relatorio_sanidade.py` | CLI tool for Phase 9 to measure ticker-by-ticker progress | ✓ VERIFIED | present, not registered in `classificacao.yaml` (correct — not a test); `app.py` untouched per `git log`/`git diff --name-only` from 08-06 plan |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `src/analista/ingest/build.py` | `core/sanidade.py::aplicar_sanidade` | `montar_empresa` calls it before `return c` | ✓ WIRED (proven by execution) | Independently disabled and re-enabled the call; test correctly flips red/green |
| `tests/test_sanidade_baseline.py` | `tests/fixtures/baseline_sanidade.yaml` | set comparison of (ticker, check) pairs | ✓ WIRED (proven by execution) | Independently deleted and restored a baseline entry; test correctly flips red/green |
| `core/sanidade.py` checks | `CompanyData.market_cap / .splits / .lucro_controlador / .origem_num_acoes` | direct attribute reads in `checar_san01..05` | ✓ WIRED | Confirmed via source read: `c.market_cap`, `c.splits`, `c.lucro_controlador`, `c.origem_num_acoes` all referenced in `sanidade.py` |
| `.planning/spikes/san-07-ihcd-at1-fvoci.md` | `scripts/spike_san07_bancos.py` | doc cites the reproduction command | ✓ WIRED | doc contains "PYTHONPATH=src .venv/bin/python scripts/spike_san07_bancos.py"; script re-executed successfully |

### Data-Flow Trace (Level 4)

Not applicable in the conventional sense (no UI/render layer this phase touches — D-14 mandates
"nothing changes on screen"). The relevant data-flow question for this phase is: does
`c.confianca`/`c.avisos` actually derive from real check evaluation over real CVM/Yahoo data, rather
than being a hardcoded stub? Traced: `aplicar_sanidade` → 5 `checar_sanNN` functions → each reads
real `CompanyData` fields populated in `build.py` from `cvm.fundamentos_do_ano` (CVM cache) and
`prices.coletar_mercado` (Yahoo) → baseline shows 62/104 tickers genuinely flagged with varying
buckets, not a uniform/hardcoded pattern. **FLOWING.**

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite reports the exact green contract CLAUDE.md defines | `python -m pytest -q` | `459 passed, 1 skipped, 38 deselected, 2 xfailed` | ✓ PASS |
| Wiring guard `sanidade_e_chamada` passes normally | `pytest -k sanidade_e_chamada -q` | `1 passed` | ✓ PASS |
| Wiring guard fails when call is removed (independently re-executed evasion) | comment out call, re-run | `1 failed` (`AssertionError: 'nao_avaliada' != 'nao_avaliada'`) | ✓ PASS (guard proven live) |
| Baseline monotonicity guard fails when a flag is deleted (independently re-executed evasion) | delete GOAU4/SAN-01 entry, re-run | `1 failed`, lists `('GOAU4', 'SAN-01')` as resurrected | ✓ PASS (guard proven live) |
| SAN-06 never-raise proven over all 104 snapshot tickers | `pytest -k nenhum_check_levanta` | `1 passed` | ✓ PASS |
| SAN-07 spike script reproduces the doc's numbers offline | `python scripts/spike_san07_bancos.py` | exit 0, "As duas respostas são NÃO" for all 4 banks | ✓ PASS |
| Baseline targets match ROADMAP-named tickers | scripted YAML load + assertion (see analysis above) | GOAU4/CGRA4→SAN-01, ITUB4/BRSR6→SAN-02, BRSR6→SAN-03, MRFG3/CSNA3/ALUP11/EQTL3→SAN-04, ITUB4/BBDC4/MRFG3 correctly clean of false positives | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` convention exists in this repository; this phase's guards are
pytest-based, and all were re-executed above per Step 7b, not just Step 7c. N/A for shell probes.

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|--------------|----------------|--------------|--------|----------|
| SAN-01 | 08-01, 08-03, 08-04, 08-05, 08-06 | escala `num_acoes × preço ≈ market cap`, símetric | ✓ SATISFIED | `checar_san01` + baseline (GOAU4/CGRA4 flagged, ITUB4/BRSR6/MRFG3 correctly not) |
| SAN-02 | 08-01, 08-03, 08-04, 08-05, 08-06 | salto ano-a-ano simétrico ≥3×, isenção por split, fronteira de fonte | ✓ SATISFIED | `checar_san02`; baseline confirms ITUB4/BRSR6/CGRA4 flagged |
| SAN-03 | 08-01, 08-04, 08-05, 08-06 | reconciliação dividendos_CVM vs DPA×num_acoes / JCP perdido | ✓ SATISFIED | `checar_san03` (2 signals); baseline BRSR6→SAN-03, ITUB4/BBDC4 correctly clean |
| SAN-04 | 08-01, 08-04, 08-05, 08-06 | PL × lucro mesma base | ✓ SATISFIED | `checar_san04`, incl. sign-inverted CSNA3 case; baseline MRFG3/CSNA3/ALUP11/EQTL3 flagged |
| SAN-05 | 08-04, 08-05, 08-06 | clean surplus como dado | ✓ SATISFIED | `checar_san05` |
| SAN-06 | 08-03, 08-05, 08-06 | never-raise estrutural | ✓ SATISFIED | `aplicar_sanidade` try/except per check + quedas counter; independently re-verified `test_nenhum_check_levanta_em_nenhum_ticker_do_snapshot` |
| SAN-07 | 08-02 | spike IHCD/AT1/FVOCI, resposta escrita | ✓ SATISFIED | `.planning/spikes/san-07-ihcd-at1-fvoci.md` + script re-executed |

All 7 requirement IDs declared across plans (`08-01`..`08-06`) are accounted for. Cross-referenced
against `.planning/REQUIREMENTS.md` traceability table (lines 290-296): all show `Phase 8 | Complete`,
matching the checked `[x]` boxes in the SAN section (lines 84-110). **No orphaned requirements** —
SAN-01..07 is a closed set, fully claimed by this phase's plans.

Note: `08-04-SUMMARY.md` frontmatter lists `requirements-completed: [SAN-05]` only, while the plan's
own `requirements:` field and body target SAN-01..05. This is a metadata bookkeeping inconsistency
in the summary frontmatter, not a functional gap — the code artifacts for SAN-01..04 delivered by
08-04 were independently confirmed present and correct via direct source read and baseline
cross-check above.

### Anti-Patterns Found

None. Scanned all phase-modified files (`src/analista/core/sanidade.py`,
`src/analista/ingest/{build,cvm,prices}.py`, `src/analista/core/fundamentals.py`, all
`scripts/*sanidade*|*san07*` scripts, all `tests/test_sanidade_*.py`,
`tests/helpers_sanidade.py`) for `TBD`/`FIXME`/`XXX` and `TODO`/`HACK`/`PLACEHOLDER` — zero matches
in either category.

The code review report (`08-REVIEW.md`, `status: issues_found`, 0 critical / 1 warning / 3 info)
flagged one real defect: `scripts/spike_san07_bancos.py:168-169` would crash with
`TypeError`/`ValueError` if a bank's OCI data were fully absent (`None`). This is a **narrow,
standalone diagnostic script** (not part of the pipeline, not imported by anything, has no test
coverage requirement), and I independently re-ran it — it executes cleanly today (exit 0) for all
four banks with the current cache. I classify this as a pre-existing WARNING, not a phase-goal
blocker: the phase goal is "pipeline knows when data is wrong," and this defect lives in a
non-pipeline diagnostic script whose actual current invocation succeeds. Recommend fixing in a
follow-up but it does not block Phase 8 completion.

## Human Verification Required

None. All must-haves for this phase are structural/pytest-verifiable (checks are pure functions
over frozen data; guards are proven by direct re-execution of the evasion tests) — there is no
UI, real-time behavior, or external-service integration surface introduced by this phase (D-14
explicitly mandates nothing on screen changes).

## Gaps Summary

No gaps found. All 7 SAN requirements are implemented, wired into the real pipeline (proven by
independently re-executing the "comment out the call" evasion), never raise across all 104 snapshot
tickers (independently re-verified), and are backed by a detection baseline whose monotonicity
guard was independently re-executed and found to be live (not decorative). The "62 sujos, not 41"
discrepancy versus the stale ROADMAP wording is expected per this project's explicit convention
(the baseline reflects measured reality, not the ROADMAP's original estimate) and is not treated as
a gap. The one code-review WARNING (a crash path in a standalone offline spike script under an edge
case that does not occur with current cached data) does not block the phase goal.

---

_Verified: 2026-07-15T00:49:38Z_
_Verifier: Claude (gsd-verifier)_
