---
phase: 13-motores-contrato-de-sa-da-eng
verified: 2026-07-20T01:48:04Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 13: Motores → Contrato de Saída (ENG) Verification Report

**Phase Goal:** Colapsar os 4 motores num RIM único (sob clean surplus RIM ≡ DDM ≡ DCF-equity). O
classificador de arquétipo sobrevive e passa a escolher uma âncora de ROE (erro limitado) em vez de
um modelo. O contrato de saída é o do livro (Cap. 17) — não deve trocar.

**Verified:** 2026-07-20T01:48:04Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `motores:` block in config.yaml went from ~20 keys to ≤5 (verifiable count); `dcf_crescimento`, `lucro_normalizado`, `nav_contabil` became RIM input policies, not motors | ✓ VERIFIED | `config.yaml` `motores:` block has exactly 5 leaves (`rim.{n_fade, excesso_sustentavel, ke_g_spread_min, roe_terminal_stat, anos_ciclica}`), confirmed by parsing the YAML directly. `motores.ciclica`/`motores.crescimento` sub-blocks no longer exist. `def dcf_crescimento` and `def lucro_normalizado` are absent from `src/analista/core/motores.py` (grep count 0); `def nav_contabil` survives (count 1) as a pure derivator, not invoked from the dispatch table. |
| 2 | The ensemble (ENS-01) died, along with `_guarda_san01` and `_guarda_faixa_ddm` — REMOVED, not ported | ✓ VERIFIED | `grep -cE 'def _guarda_san01\|def _guarda_faixa_ddm\|def _veredito_fronteirico\|def _hipotese_divergencia' src/analista/report/report.py` == 0. All ensemble fields (`banda_do_motor`, `divergencia_ativa`, `contraponto_valor`, `candidatos_intrinsecos`, `veredito_range`, `arquetipo_incerto`, `arquetipo_fronteirico`, `san01_reetiquetado`, `motor_pendente`) are absent from `report.py` (grep count 0). |
| 3 | The auditable bridge is displayed AND is a correctness test: P/B justo = 1 + (ROE_T − Ke)/(Ke − g), V = P/B justo × VPA, payout_T = 1 − g/ROE_T. Negative or >100% terminal payout fails the test. Guard is on the ratio (0 < P/B justo < 6) | ✓ VERIFIED | `src/analista/core/valuation.py` implements `pb_justo`/`payout_terminal` as pure, never-raise functions with the exact algebra. `report.py` computes `a.pb_justo`, `a.v_ponte`, `a.payout_terminal` on every analysis and flags `a.razao_patologica` when `pb_justo ∉ (0,6)` or `payout_terminal ∉ (0,1]`. `tests/test_eng_ponte_pb.py::test_guarda_pega_payout_terminal_negativo` and `::test_guarda_pega_pb_justo_explosivo` are genuine RED-able correctness tests (constructed fixtures with g>ROE_T and degenerate spread respectively, both assert the guard REPROVES). `app.py:1082-1090` exhibits P/B justo, V=P/B×VPA and payout terminal via `st.metric`. All pass (`pytest -k 'ponte_pb or invariantes_v24'` → 12 passed). |
| 4 | Output contract is the book's: intrinsic value + value region + SUBAVALIADA/NO INTERVALO/SOBREAVALIADA triad; MS is user control, symmetric, default 5-10%; Ke×g matrix lives. "Evitar" and "Qualidade Baixa" are gone | ✓ VERIFIED | `report.py:420-478`: `a.vmin/a.vmax` derive as the sole (primary, not fallback) path `intrinseco_motor × (1∓margem_seguranca)`; the SUB/NO INTERVALO/SOBRE tree compares `preco_atual` against this band. `config.yaml:118` `margem_seguranca: 0.05` (within 5-10%); `calibracao.lock.yaml` `user_control` documents the co-change. `app.py:1066-1071` exposes an `st.slider` (0-20%) defaulting to `cfg["veredito"]["margem_seguranca"]`, reprojecting the displayed region without recalibrating the default. Ke×g matrix (`a.sensibilidade`) is displayed at `app.py:1464-1470`, reused from Fase 12/`ddm.matriz_sensibilidade`. `grep -c '"Evitar"' src/analista/report/selo.py` == 0; `grep -c '"Baixa"' selo.py` == 0 (re-labeled "Atenção"), while "VALUE TRAP" and "Fraca" remain. `tests/test_eng_contrato.py::test_triade_vem_da_posicao_do_preco_vs_regiao_da_ms` and `::test_regiao_e_simetrica_e_escala_com_a_margem_de_seguranca` prove format/symmetry by construction. |
| 5 | `PAGADORA_REGULADA` split into `PAGADORA_MADURA` + `CONCESSAO_FINITA` (default by elimination); Ranking downgraded to a raw-multiples screener (target-price/upside/veredito columns out) — NOT deleted | ✓ VERIFIED | `src/analista/core/arquetipo.py`: `PAGADORA_REGULADA` constant is gone; `PAGADORA_MADURA`/`CONCESSAO_FINITA` exist, with `CONCESSAO_FINITA` returned by the `eh_concessionaria` hard-route (anti-Petróleo guard `_setor_casa_token` intact at line 164) and `PAGADORA_MADURA` appended as the default-by-elimination candidate (line 184). `ARQUETIPO_ANCORA_ROE` registry maps all 6 archetypes to input-derivation policies (never a model/motor id). `src/analista/cli.py::cmd_rank` (lines 160-200) prints only Nota/P/L/DY — no preço-alvo/upside/veredito, and the code comment explicitly documents ENG-11's rationale. `app.py`'s Ranking table equivalently drops those columns (grep confirms no `preco_alvo`/`upside` inside the Ranking block; the only hits are the untouched informational Graham/Bazin lenses). `comparables.ranking_por_multiplos` and `comparables.preco_alvo_por_regressao` (CTEEP conference, Cap. 12) both still exist — the Ranking apparatus was downgraded, not deleted. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `config.yaml` `motores:` block | ≤5 leaves, knob-cut | ✓ VERIFIED | Parsed count = 5 |
| `calibracao.lock.yaml` | 3 degrees of freedom (ERP, n_fade, PIB_real), scope 24 leaves (motores 5) | ✓ VERIFIED | `graus_de_liberdade` keys = `['ERP', 'n_fade', 'PIB_real']`; header states "24 folhas (motores 5 + capm 12 + ddm 5 + normalizacao 2)" |
| `src/analista/core/motores.py` | `rim` sole formula; `dcf_crescimento`/`lucro_normalizado` deleted; `"seguradora"` key removed from `MOTOR_ROTULO` | ✓ VERIFIED | `MOTOR_ROTULO = {"rim": ...}` only; no `def dcf_crescimento`/`def lucro_normalizado` |
| `src/analista/core/valuation.py` | Pure `pb_justo`/`payout_terminal` helpers (BLIND-02a identity) | ✓ VERIFIED | File exists, exports both functions, never-raise edge guards |
| `src/analista/report/report.py` | Single RIM dispatch (`_valor_rim`/`_derivar_insumo`) + ensemble removed + ponte P/B + symmetric MS region as primary path | ✓ VERIFIED | `_valor_rim` calls `motores.rim` exclusively; `a.motor = "rim"` unconditionally; ensemble symbols absent |
| `src/analista/core/arquetipo.py` | `ARQUETIPO_ANCORA_ROE` registry + `PAGADORA_MADURA`/`CONCESSAO_FINITA` split; legacy `ARQUETIPO_MOTOR` fully removed | ✓ VERIFIED | Registry present with 6 policy strings; `ARQUETIPO_MOTOR` absent (0 hits in src/app.py/tests) |
| `src/analista/report/selo.py` | `_MATRIZ` without "Evitar"; quality axis without "Baixa" | ✓ VERIFIED | grep count 0 for both strings; VALUE TRAP/Fraca survive |
| `src/analista/core/freio.py` | Deleted (last consumer of legacy machinery) | ✓ VERIFIED | File does not exist |
| `tests/test_ranking_freio.py` | Deleted whole | ✓ VERIFIED | File does not exist |
| `tests/test_eng_validacao.py` | Live regression over the real 104-ticker snapshot | ✓ VERIFIED | Runs `report.analisar_acao` over `hs.CAMINHO_SNAPSHOT_LIMPO`; asserts never-raise, no explosion, sound P/B ratio, single path; passes |
| `tests/test_eng_contrato.py`, `tests/test_eng_ponte_pb.py` | Contract/correctness tests for triad, symmetric region, P/B bridge guard | ✓ VERIFIED | All pass; guard is proven RED-able (constructed pathological fixtures fail the guard as designed) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `report._valor_rim` | `motores.rim` | Single call, insumo derived by `ARQUETIPO_ANCORA_ROE[a.arquetipo]` | ✓ WIRED | `report.py:188` calls `motores.rim(...)`; verified by grep and by the fact `a.motor` is unconditionally `"rim"` |
| `arquetipo.classificar` | `CONCESSAO_FINITA` / `PAGADORA_MADURA` | hard-route split (line 164) / default (line 184) | ✓ WIRED | Confirmed in source |
| `report.py` veredito | region `[V×(1−MS), V×(1+MS)]` | `vmin/vmax` primary path | ✓ WIRED | Confirmed no ensemble fallback remains; `test_eng_contrato.py` proves it by execution |
| `report.py` ponte P/B | `core.valuation.pb_justo`/`payout_terminal` | `ROE_T=_roe_through_cycle`, `Ke=a.ke`, `g=g_T` | ✓ WIRED | `report.py:352-353` |
| `cli.py`/`app.py` Ranking | `comparables.ranking_por_multiplos` | raw multiples columns | ✓ WIRED | Confirmed in `cli.cmd_rank`; `app.py` Ranking block |
| `app.py` MS slider | `veredito.margem_seguranca` / displayed region | `st.slider` reprojects vmin/vmax | ✓ WIRED | `app.py:1064-1078` |

### Behavioral Spot-Checks / Probe Execution

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite green per project convention | `.venv/bin/python -m pytest -q` | `470 passed, 1 skipped, 18 deselected` | ✓ PASS (matches CLAUDE.md's exact stated expectation) |
| ENG-specific tests green | `pytest -k 'eng_validacao or eng_contrato or ponte_pb or cli_rank_consistencia' -q` | `12 passed, 477 deselected` | ✓ PASS |
| Knob budget intact (3 degrees) | `pytest -k 'orcamento or knobs_batem_com_o_lock or justificativa' -q` | `4 passed, 485 deselected` | ✓ PASS |
| Collection has no CLASSIFICACAO ORFA | `pytest --collect-only -q` | `471/489 tests collected (18 deselected)` — no orphan error | ✓ PASS |
| Fase-14 hold-out respected | `grep -rniE '37[.,]22' tests/ src/ app.py` | 3 hits, all in pre-existing `test_ddm.py`/`ddm.py`/`comparables.py` (in-repo since the initial commit, not touched by Phase 13's ENG plans; testing the book's Cap. 15 DDM textbook example, not the RIM engine) | ✓ PASS — no Phase-13-introduced target-number assert |

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|------------|--------|----------|
| ENG-01 | 13-01, 13-03, 13-07 | ✓ SATISFIED | Single RIM path proven both statically and by execution over the 104 |
| ENG-02 | 13-03 | ✓ SATISFIED | Ensemble/guardas deleted, not ported |
| ENG-03 | 13-02, 13-03 | ✓ SATISFIED | Classifier survives; body untouched except split lines; `ARQUETIPO_ANCORA_ROE` added |
| ENG-04 | 13-01, 13-02, 13-03 | ✓ SATISFIED | `PAGADORA_REGULADA` split into `PAGADORA_MADURA`+`CONCESSAO_FINITA`; carve-out `g_terminal=None` measured and decided in the spike |
| ENG-05 | 13-04, 13-06 | ✓ SATISFIED | Triad from V vs region; region is primary |
| ENG-06 | 13-04, 13-05, 13-06 | ✓ SATISFIED | MS is `cfg` parameter, default 0.05, exposed via slider, never calibrated |
| ENG-07 | 13-04, 13-06 | ✓ SATISFIED | Ke×g matrix reused from Fase 12, displayed over `a.ke` |
| ENG-08 | 13-04 | ✓ SATISFIED | P/B bridge implemented, displayed, and is a correctness test |
| ENG-09 | 13-04, 13-07 | ✓ SATISFIED | Two-level guard: test-fails on pathological ratio; runtime degrades never-raise |
| ENG-10 | 13-05 | ✓ SATISFIED | `motores:` 7→5 leaves counted; lock co-changed in same commit |
| ENG-11 | 13-06 | ✓ SATISFIED | Ranking downgraded, not deleted; ensemble lens removed from `cli.cmd_rank` |

No orphaned requirements found — all ENG-01..ENG-11 IDs declared across the 7 plans' frontmatter, matching `.planning/REQUIREMENTS.md`'s traceability table (all marked Complete).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `scripts/spike_eng_rim_104.py` | 90 | `AttributeError` on `arquetipo.PAGADORA_REGULADA` (removed in a later commit of the same phase) — confirmed by running the script directly, it crashes on the first ticker | ℹ️ INFO | Does not affect the phase goal: this is a throwaway, non-production spike script (`13-01-PLAN.md` explicitly labels it "throwaway", "NÃO importado por produção") whose measurement output was already captured in `.planning/spikes/eng-rim-104.md` *before* the `arquetipo.py` split happened in 13-02. The `.md` spike doc records the `g_terminal=None` decision and the coorte-level measurement that the phase depends on — the decision itself is not affected by the script's later drift. Flagged in `13-REVIEW.md` as CR-01; recommend deleting or fixing the script in a follow-up (not a phase-13 gap). |
| `app.py` | 936-986, 1013-1054 | Dead ensemble/divergence UI blocks reference fields removed from `AnaliseAcao` (`san01_reetiquetado`, `divergencia_*`, `contraponto_valor`, `arquetipo_incerto`, `candidatos_intrinsecos`, `veredito_range`, `banda_do_motor`) | ⚠️ WARNING | Guarded by `getattr(a, "...", False)` defaults / short-circuit `and` — confirmed `app.py` still parses (`ast.parse` OK) and no code path can raise. Explicitly logged in `.planning/phases/13-motores-contrato-de-sa-da-eng/deferred-items.md` as out-of-scope for Plano 03/13 (never in any plan's `files_modified` for this concern) and in `13-REVIEW.md` as WR-02. Deferred, not a phase-13 gap. |
| `src/analista/core/comparables.py` | 81-187 | Cap. 12 P/L-regression apparatus (`RegressaoPL`, `preco_alvo_por_regressao`, etc.) has no live caller in `src/`/`app.py` after the Ranking rebaix, but is intentionally kept (not deleted) per `13-06-PLAN.md`'s explicit anti-goal "NÃO deletar `preco_alvo_por_regressao`" (CTEEP conference invariant) | ℹ️ INFO | Matches plan intent exactly — reported by `13-REVIEW.md` as WR-03, not a defect. |

None of these anti-patterns are TBD/FIXME/XXX debt markers on production code paths, and none block the phase goal.

### Human Verification Required

None. All must-haves are verifiable via code inspection, static grep, and automated test execution (unit/invariant/contrato tests directly assert the UI-adjacent contract fields: `a.vmin`/`a.vmax`/`a.pb_justo`/`a.v_ponte`/`a.payout_terminal`/`a.veredito`). The Streamlit widgets (`st.slider`, `st.metric`) are confirmed present, correctly wired to `cfg`/`AnaliseAcao` fields, and `app.py` parses cleanly (`ast.parse`); the phase's own acceptance criteria (PLAN frontmatter) are all grep/pytest-based, not visual-appearance-based, so no live-rendering check is required to close this phase.

### Gaps Summary

No gaps found. All 5 roadmap success criteria and all 11 ENG requirements are verified against the actual codebase (not SUMMARY claims): the `motores:` config block is counted at 5 leaves, the ensemble/guard machinery is fully deleted (not ported), the P/B bridge is both exhibited and provably RED-able as a correctness test, the book's output contract (triad + symmetric user-controlled MS + Ke×g matrix, "Evitar"/"Baixa" removed) is wired as the primary path, and the archetype split (`PAGADORA_MADURA`/`CONCESSAO_FINITA`) plus the Ranking downgrade (not deletion) are both confirmed in the live code paths of `cli.py`/`app.py`. The full test suite is green exactly as CLAUDE.md's project rule specifies (470 passed, 1 skipped, 18 deselected, 0 failed), and the phase's own hold-out discipline holds — no ITUB4=R$37,22 assertion was introduced by any of the 7 plans (the 3 pre-existing hits predate Phase 13 and test an unrelated DDM textbook example). The one crashing artifact (`scripts/spike_eng_rim_104.py`) is throwaway debris outside production/test code whose measurement was already consumed before it broke; it does not affect goal achievement.

---

_Verified: 2026-07-20T01:48:04Z_
_Verifier: Claude (gsd-verifier)_
