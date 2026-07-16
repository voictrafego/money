---
phase: 10-primitivas-sem-vi-s-prim
verified: 2026-07-16T13:19:00Z
status: passed
score: 5/5 must-haves verified (2 with documented anchor-number override)
overrides_applied: 2
overrides:
  - must_have: "roe_valuation ITUB4 sai de 16,1% para 18,0%"
    reason: "Anchor numérico medido em dado sujo pré-Fase-9; não reproduz no snapshot limpo (medido: ~19,8%→18,5%, snapshot exato de bancos 18,0%). O critério é satisfeito pela mudança de MÉTODO (roe_valuation == median(roe(a)), consistente com _roe_through_cycle), provada por teste (tests/test_fundamentals_valuation.py). Documentado em 10-02-SUMMARY.md e 10-04-SUMMARY.md; instrução explícita da tarefa de verificação para aceitar a mudança de método sobre o número literal."
    accepted_by: "giovanelazri (via instrução da tarefa de verificação, herdando decisão registrada pelo executor)"
    accepted_at: "2026-07-16T13:19:00Z"
  - must_have: "g fabricado de 36% (VULC3) e 47% (CYRE3) somem após remover a winsorização"
    reason: "Anchor numérico medido em dado sujo pré-Fase-9; não reproduz no snapshot limpo. Medido: g bruto do VULC3 SOBE para ≈36,1% (não some) e CYRE3 é None nos dois modos. O critério é satisfeito pela mudança de MÉTODO (serie_lucro_normalizada devolve a série CRUA; raw != winsorizada, provado por teste) — a winsorização temporal deixou de ser aplicada, que é a causa raiz descrita no criterion. Documentado em 10-02-SUMMARY.md e 10-04-SUMMARY.md."
    accepted_by: "giovanelazri (via instrução da tarefa de verificação, herdando decisão registrada pelo executor)"
    accepted_at: "2026-07-16T13:19:00Z"
re_verification: null
gaps: []
deferred:
  - truth: "test_growth_reconciliacao.py::test_teto_absoluto_025_quando_g_fund_e_cagr_explodem / test_trava_ke_quando_g_fund_supera_ke (golden_nivel vermelhos)"
    addressed_in: "Phase 11 (GROW)"
    evidence: "10-02-SUMMARY.md: '2 golden_nivel de g (test_growth_reconciliacao) quebram como consequência do g_fund novo — tagged \"→ Fase 11 (GROW)\" na classificacao e ficam quarentenados.' ROADMAP Phase 11 goal is exactly 'a metade g da Doença 1' / g_cap derivado."
  - truth: "test_motores.py::test_rota_seguradora_bbse3_gordon_franquia (golden_nivel vermelho, banda R$39,87 da BBSE3)"
    addressed_in: "Phase 11/12 (GROW/KE)"
    evidence: "Causa raiz confirmada por leitura de código nesta verificação: dpa_recorrente() = payout_valuation() × lpa_valuation(), e lpa_valuation() consome base_lucro_normalizada (o endpoint Theil-Sen do PRIM-01) — a mesma mudança de primitiva que moveu o golden ITUB4. 10-03-SUMMARY.md confirma por execução (commit abeab5a) que a quebra é PRÉ-EXISTENTE ao Plano 03 (não é regressão da deflação IPCA); é golden_nivel, quarentenado, fora do contrato de suíte verde default."
---

# Phase 10: Primitivas sem viés (PRIM) Verification Report

**Phase Goal:** "Maior alavancagem por linha do repositório" — as primitivas de valuation
(normalização, roe_valuation, série de lucro, base do motor cíclico) deixam de ter viés.
Critério de saída soberano: o golden ITUB4 32,88 QUEBRA e é DELETADO.

**Verified:** 2026-07-16T13:19:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Golden `ITUB4 32,88 ± 0,20` (`test_backtest_alvos_recalibrados`) DELETADO — critério de saída | ✓ VERIFIED | `grep -rn "test_backtest_alvos_recalibrados" tests/ src/` → vazio. Only remaining `32.88`/`32,88` occurrences are: `helpers_blindagem.py:157,215,251,255,282` (BLIND-04a detector honeypot fixtures — explicitly NOT-TO-TOUCH per plan), `test_backtest_bancos.py:10` (prose comment), `classificacao.yaml:12` (comment), `test_invariantes_v24.py:61,119,176` (BLIND-02b docstring/prose, Fase-12 scope), `snapshot_bancos_2026-07-12.yaml:296` (observed fixture value, not a live assert). No live `assert ... 32.88` / `abs(v - 32.88) <= tol` survives. |
| 2 | BLIND-03 (normalização não pune crescimento) verde como invariante normal, xfail removido | ✓ VERIFIED | `tests/test_invariantes_v24.py::test_normalizacao_nao_pune_crescimento` runs and PASSES with `@pytest.mark.invariante` (no `xfail`). Verified by direct execution: `pytest -k nao_pune_crescimento -o addopts=""` → 1 passed. Test reads `anos_media`/`winsor` from production `config.yaml` (not hardcoded), closing the Pitfall-5 escape hatch. |
| 3 | `roe_valuation` = mediana da série de ROEs anuais (não cruza bases temporais) | ✓ VERIFIED (method); literal anchor overridden | Source read: `fundamentals.py::roe_valuation` body is exactly `serie=[self.roe(a) for a in self.anos_ordenados()]; validos=[...]; return float(median(validos)) if validos else None` — matches `_roe_through_cycle`'s statistic exactly (`roe0`/`roe_terminal` no longer diverge). `tests/test_fundamentals_valuation.py` (5 tests) proves the method identity. The ROADMAP's literal anchor ("16,1%→18,0%") does not reproduce on the clean snapshot (documented, pre-authorized override above) — the method change is what's verified. |
| 4 | Winsorização removida da série temporal; `g` fabricados de VULC3/CYRE3 somem | ✓ VERIFIED (method); literal anchor overridden | Source read: `fundamentals.py::serie_lucro_normalizada` returns `self.serie("lucro_liquido")` raw — the `norm.serie_winsorizada` wrapper is gone from `fundamentals.py` (`grep -c serie_winsorizada src/analista/core/fundamentals.py` = 0) while still alive in `screening.py` (`grep -c` ≥ 1, Cap. 8 elegibility, correctly out of PRIM scope). The ROADMAP's literal "g somem" anchor does not reproduce (VULC3 g rises to ≈36,1% raw, CYRE3 is None both ways) — documented override above; the structural fix (raw ≠ winsorized, proven by test) is what's verified. |
| 5 | Base do motor cíclico deflacionada por IPCA (`macro.ipca_deflatores_anuais`, stamping offline) | ✓ VERIFIED | `macro.py` has `ipca_deflatores_anuais`/`_compor_deflatores`/`_ipca_anual_dezembro`. `report.py` ramo `"normalizado"` reads `cfg["macro"]["ipca_deflatores"]`, multiplies the profit series before `norm.media_ciclo`, never calls `requests`/`macro` inside the engine, and has a never-raise nominal fallback. Stamping confirmed wired at both entry points (`cli.py::_carimbar_macro` used by both `cmd_analyze` and `cmd_rank`; `app.py:881`) and in `backtest.py` (`_CHAVES_GLOBAIS` includes `ipca_deflatores`; `carregar_snapshot` normalizes keys to `int`). |

**Score:** 5/5 truths verified (3 direct, 2 verified-by-method with a pre-authorized, documented override on the ROADMAP's literal numeric anchors — see `overrides:` in frontmatter).

### Deferred Items

Golden_nivel tests broken as a side effect of the primitive fixes (PRIM-01/02), correctly quarantined (not part of default suite), whose fix belongs to later phases.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | `test_growth_reconciliacao.py::test_teto_absoluto_025_quando_g_fund_e_cagr_explodem` / `test_trava_ke_quando_g_fund_supera_ke` | Phase 11 (GROW) | Tagged `"→ Fase 11 (GROW)"` in `tests/classificacao.yaml`; confirmed still red via `pytest -m golden_nivel` executed by this verifier. |
| 2 | `test_motores.py::test_rota_seguradora_bbse3_gordon_franquia` | Phase 11/12 (GROW/KE) | Root cause traced by this verifier: `dpa_recorrente()` → `lpa_valuation()` → `base_lucro_normalizada()` → the PRIM-01 Theil-Sen endpoint. `10-03-SUMMARY.md` confirms by execution (commit `abeab5a`, end of Plan 02) that this break predates Plan 03/04 — it is a downstream consequence of the sanctioned primitive change, not a Phase-10 regression against the phase's own contract (golden_nivel is quarantined by design; `NÃO fazer` explicitly permits primitives to move exaggerated numbers, to be resolved once g/Ke are fixed). |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/normalizacao.py` | `base_normalizada` = Theil-Sen endpoint + guard; `media_ciclo` = old through-cycle estimator | ✓ VERIFIED | Read in full. `theilslopes` imported and used (`slope, intercept, *_ = theilslopes(janela, np.arange(n))`); guard `endpoint<=0 → median(janela)`; ladder N=0/1/2 present; `media_ciclo` is byte-for-byte the pre-PRIM-01 ladder. Docstring contract corrected by WR-01 gap-closure (guard is not a non-negativity clamp by design). |
| `src/analista/core/fundamentals.py` | `roe_valuation`=median(roe(a)); `serie_lucro_normalizada`=raw | ✓ VERIFIED | Confirmed above (truths 3/4). Also confirms new `roe_qualidade_atual` helper (signal split, Option A) consumed only by `arquetipo.py` routing, not by RIM/display. |
| `src/analista/report/report.py` | `"normalizado"` branch consumes `media_ciclo`, deflates before averaging | ✓ VERIFIED | `media_ciclo` called at report.py; `ipca_deflatores` read offline, keys coerced to int (WR-02 fix), nominal fallback on empty/no-overlap. |
| `src/analista/ingest/macro.py` | `ipca_deflatores_anuais(anos)` — BCB SGS fetch + retry + graceful degradation | ✓ VERIFIED | `_ipca_anual_dezembro` (network) / `_compor_deflatores` (pure) split confirmed; SGS 13522-December locked code reused from `IPCA_12M` constant. |
| `tests/classificacao.yaml` | Golden lines removed, no orphans | ✓ VERIFIED | `pytest --collect-only -q` produced zero `CLASSIFICACAO ORFA` errors across the entire suite (519 items collected cleanly). |
| `config.yaml` / `calibracao.lock.yaml` | Only `normalizacao.anos_media: 3→5` co-change + additive `macro.ipca_deflatores: {}` block (out of knob scope) | ✓ VERIFIED | `git diff 930ec27 HEAD -- config.yaml calibracao.lock.yaml` shows exactly this — no other knob touched. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `report.py` ramo "normalizado" | `norm.media_ciclo` | direct call | ✓ WIRED | `grep -c media_ciclo src/analista/report/report.py` = 1 (call site confirmed by read). |
| `fundamentals.py::base_lucro_normalizada` | `norm.base_normalizada` (endpoint) | existing call, unchanged | ✓ WIRED | Confirmed by read — valuation consumers (`lpa_valuation`, `margem_valuation`, `roe_qualidade_atual`) automatically inherit the endpoint. |
| `cli.py` / `app.py` (entry points) | `cfg["macro"]["ipca_deflatores"] = macro.ipca_deflatores_anuais(...)` | offline stamping mirroring `rf_local` | ✓ WIRED | `cli.py::_carimbar_macro` used by BOTH `cmd_analyze` and `cmd_rank` (WR-03 gap-closure fix, `553f2fd`) — eliminates the cross-mode divergence the code review flagged. `app.py:881` confirmed. |
| `backtest.py::carregar_snapshot` | `ipca_deflatores` carimbado no snapshot | offline read, int-key normalized | ✓ WIRED | `_CHAVES_GLOBAIS` includes `ipca_deflatores`; keys coerced `{int(ano): float(fator) ...}` (WR-02 gap-closure fix, `d68cb52`/`657b2a9`). |
| `test_backtest_bancos.py::test_backtest_alvos_recalibrados` | (absent from repo) | função + linha classificacao.yaml deletadas | ✓ VERIFIED ABSENT | Confirmed by grep across `tests/` and `src/` — zero hits for the function/nodeid. |

### Data-Flow Trace (Level 4)

Not applicable in the traditional UI sense (this phase touches a pure computation engine, not a rendering surface). The equivalent trace — "does the deflator/median actually reach the number shown to the user" — was performed via the key-link checks above (entry point → cfg → engine → report) and confirmed offline/deterministic (`test_backtest_determinismo` green in default suite).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| BLIND-03 invariant executes and passes standalone | `pytest -k nao_pune_crescimento -o addopts=""` | `1 passed` | ✓ PASS |
| Knob budget stays at exactly 3 degrees | `pytest -k "orcamento_de_knobs or knobs_batem or justificativa" -o addopts=""` | `3 passed` | ✓ PASS |
| BLIND-04a meta-test (no live ticker+R$ assertion in calibration tests) | `pytest -k nenhum_teste_de_calibracao_crava_ticker -o addopts=""` | `1 passed` | ✓ PASS |
| WR-04 extracted invariants survive default run | `pytest -k "nenhuma_rota_diferente_de_rim_e_silenciosa or nenhuma_reprovacao_de_banda_e_silenciosa or setor_de_banco_nao_casa_o_token_seguradora"` | `3 passed`, classified `invariante` (not `golden_nivel`) in `classificacao.yaml` | ✓ PASS |
| Golden_nivel quarantine — confirm 3 pre-existing red (not phase-10 regressions) | `pytest -m golden_nivel` | `3 failed, 24 passed` — BBSE3 + 2 growth tests, matching documented expectation | ✓ PASS (matches expected/documented state) |
| Full default suite | `pytest -q` | `490 passed, 1 skipped, 27 deselected, 1 xfailed, 0 failed` | ✓ PASS |
| Commit-msg hook installed locally (repo convention) | `git config core.hooksPath` + `pytest -k hook_do_blind05_esta_instalado` | `.githooks`; `1 passed` | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` conventions apply to this repo/phase (Python/pytest project, not a migration/CLI-tooling phase with shell probes). Skipped — no runnable probe entry points declared in PLAN/SUMMARY.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| PRIM-01 | 10-01-PLAN.md | Base de lucro do valuation deixa de descartar o ano mais recente (endpoint Theil-Sen) | ✓ SATISFIED | `normalizacao.py::base_normalizada`; BLIND-03 green |
| PRIM-02 | 10-02-PLAN.md | `roe_valuation` deixa de cruzar bases temporais; vira mediana da série de ROEs | ✓ SATISFIED | `fundamentals.py::roe_valuation`; `test_fundamentals_valuation.py` |
| PRIM-03 | 10-02-PLAN.md | Winsorização não é mais aplicada à série temporal | ✓ SATISFIED | `fundamentals.py::serie_lucro_normalizada` raw |
| PRIM-04 | 10-03-PLAN.md | Base do motor cíclico deflacionada por IPCA | ✓ SATISFIED | `macro.py::ipca_deflatores_anuais`; report.py ramo "normalizado" |
| PRIM-05 | 10-04-PLAN.md | Golden ITUB4=32,88 DELETADO (critério de saída) | ✓ SATISFIED | `grep` confirms absence; suite green |

No orphaned requirements: REQUIREMENTS.md lists exactly PRIM-01..05 for Phase 10, and all 5 IDs appear in plan frontmatter (`10-01`: PRIM-01; `10-02`: PRIM-02, PRIM-03; `10-03`: PRIM-04; `10-04`: PRIM-05) — full coverage, no gaps.

### Anti-Patterns Found

None. Scanned all phase-touched production files (`normalizacao.py`, `fundamentals.py`, `arquetipo.py`, `report.py`, `macro.py`, `cli.py`, `backtest.py`, `screening.py`, `app.py`) for `TBD|FIXME|XXX`, `TODO|HACK|PLACEHOLDER`, `placeholder|coming soon|not yet implemented`, empty implementations, and hardcoded-empty patterns. Zero blocker/warning-level matches (one false-positive grep hit on `\uXXXX` in an app.py docstring about JSON escaping, unrelated to code debt).

Code review (`10-REVIEW.md`): 0 critical, 3 warnings (WR-01/02/03) — all 3 confirmed RESOLVED with dedicated commits (`9427980`, `d68cb52`, `657b2a9`, `553f2fd`) verified present in `git log`, and the fixes independently confirmed present in source during this verification (int-key coercion in `backtest.py`/`report.py`; `_carimbar_macro` shared by `cmd_analyze`/`cmd_rank`; corrected guard docstring in `normalizacao.py`). 2 info items (IN-01/IN-02) left as documented, non-blocking, matching the review's own risk assessment.

### Human Verification Required

None. This phase is a pure computation-engine change (no new UI surface, no new external dependency, no user-facing flow change) — all must-haves are mechanically verifiable via source reads, greps, and test execution, which were performed directly.

### Gaps Summary

No blocking gaps. All 5 ROADMAP success criteria are met:

1. The sovereign exit criterion — golden `ITUB4=32,88` deleted, not updated — is directly confirmed: no live assert pinning that value survives anywhere in `tests/` or `src/`; only prose/comments/honeypot fixtures remain, exactly as the plan mandated ("NÃO tocar").
2. BLIND-03 is green as a normal invariant with the `xfail` removed.
3 & 4. `roe_valuation`/`serie_lucro_normalizada` are structurally fixed exactly as specified; the ROADMAP's literal numeric anchors for these two criteria were measured on pre-Phase-9 dirty data and don't reproduce on the clean snapshot — this was documented by the executor in two separate SUMMARYs and pre-authorized as an accepted deviation by the verification task itself. Two formal overrides are recorded in this VERIFICATION.md's frontmatter for traceability, with method-level evidence (passing tests proving the structural claim) substituted for the stale literal number.
5. The cyclical motor now deflates by IPCA via the same offline-stamping pattern as `rf_local`, confirmed wired end-to-end (entry points → cfg → engine → backtest snapshot).

Knob budget remains exactly 3 degrees of freedom (ERP, n_fade, PIB_real); the only config/lock change is the sanctioned `normalizacao.anos_media: 3→5` co-change, with a ticker-free justification, confirmed by the passing `test_nenhuma_justificativa_de_knob_menciona_ticker`. Default suite is green: 490 passed, 1 skipped (jackknife → Fase 14), 1 xfailed (BLIND-02b → Fase 12), 27 deselected (`golden_nivel` quarantine), 0 failed — independently re-run and confirmed by this verifier, not merely trusted from the SUMMARY. Of the 27 quarantined `golden_nivel` tests, 3 are currently red (BBSE3 + 2 growth-reconciliation tests); these were traced to be direct, expected, documented downstream consequences of the sanctioned PRIM-01/02 primitive changes (not defects introduced carelessly), correctly excluded from the default-suite-green contract by the project's own `golden_nivel` quarantine mechanism, and explicitly deferred to Phases 11/12 per `tests/classificacao.yaml` tags and the SUMMARYs. They are recorded as `deferred` items above, not gaps.

The Phase 10 code review (`10-REVIEW.md`) findings (WR-01/02/03) were all resolved with dedicated, verifiable commits — confirmed present both in `git log` and in the current source.

---

_Verified: 2026-07-16T13:19:00Z_
_Verifier: Claude (gsd-verifier)_
