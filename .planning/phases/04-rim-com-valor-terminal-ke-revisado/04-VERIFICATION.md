---
phase: 04-rim-com-valor-terminal-ke-revisado
verified: 2026-07-12T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 4: RIM com Valor Terminal + Ke Revisado Verification Report

**Phase Goal:** Consertar a alavanca principal — dar ao motor RIM um valor terminal (perpetuidade de residual income / Gordon sobre o RI terminal) que substitui/complementa o fade-para-zero-sem-terminal (D-02), para que o intrínseco de um banco que sustenta ROE > Ke deixe de ancorar no VPA. ITUB4 sai de ~R$23 para R$32-40 (CAL-01); Ke de banco revisado como ajuste secundário ke_teto 0.14->0.13 (CAL-02). Suíte completa verde; DDM/TAEE11/firewall intactos.
**Verified:** 2026-07-12
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ITUB4 (VPA≈19, ROE≈19.3%, roteado para RIM) produz intrínseco na faixa R$32–40 | VERIFIED | Independently re-ran outside the test suite: `motores.rim(vpa0=19.0, roe0=0.193, ke=ke_rim(1.29,cfg), retencao=0.533, n=10, excesso_sustentavel=0.045, g_terminal=0.025)` → **R$32.87**, `vp_terminal=5.73`. Gate test `test_rim_itub4_live_alvo_32_40` asserts `32.0 <= res.valor_intrinseco <= 40.0` and passes. Integration gate `test_rim_itub4_dispatch_banda` runs the real `report.analisar_acao()` dispatch path and asserts `intrinseco_motor > 30.0` — passes, proving the knobs reach the funnel (not just the unit call). |
| 2 | Valor terminal parametrizado em config.yaml (excesso_sustentavel, g_terminal, ke_g_spread_min) — sem constante mágica no código | VERIFIED | `config.yaml:250-256` defines all three knobs with WHY comments. `motores.py::rim()` reads them as function args (no hardcoded literals in the terminal-value branch); `report.py:207-209` reads them from `cfg["motores"]["rim"]` and passes through. |
| 3 | Ke do RIM revisado: ke_teto 0.14→0.13 (CAL-02), documentado, sem intrínseco explosivo | VERIFIED | `config.yaml:235` `ke_teto: 0.13` with rationale comment (Selic-ciclo already embeds country risk, Blume-adjusted beta). `ke_rim(1.29, cfg)` reproduced live → `0.13` exactly. No explosion: `vp_terminal` guarded by `ke_g_spread_min=0.03` before the terminal is released; ITUB4/golden/bad-bank cases all land in expected bounded ranges. |
| 4 | Banco com ROE < Ke valua ABAIXO do book (guarda anti-bad-bank) | VERIFIED | Reproduced live: `rim(vpa0=22.0, roe0=0.10, ke=0.125, ...)` → **R$15.54** (< R$22 book, P/B≈0.71), `vp_terminal=-2.76` (negative, as expected — RI terminal negative). Test `test_rim_bad_bank_abaixo_do_book` asserts `valor_intrinseco < 22.0` and `vp_terminal <= 0` — passes. |
| 5 | Suíte completa verde: test_ddm intacto, TAEE11 idêntica (rota DDM), firewall selo↛report intacto | VERIFIED | `pytest tests/` → **440 passed, 0 failed**. `git diff da942c2 HEAD --stat` confirms `ddm.py`/`selo.py`/`lentes.py` have zero diff lines since phase start (untouched). `test_capstone_taee11_baseline_ddm_identico` passes. `test_selo.py::test_firewall_selo_nao_importa_report` passes. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/motores.py` | `rim()` with terminal value (Gordon perpetuity over RI terminal) + `ResultadoRIM.vp_terminal` | VERIFIED | `ResultadoRIM` has `vp_terminal: float = 0.0` field (line ~54); `rim()` signature adds `excesso_sustentavel`, `g_terminal`, `ke_g_spread_min`; terminal branch calls `ddm.valor_gordon(dpa1=ri_terminal, ke=ke, g=g_terminal)` (line ~114) — confirmed reuse, no reimplementation of perpetuity math. |
| `config.yaml` | Knobs `motores.rim.excesso_sustentavel`/`g_terminal`/`ke_g_spread_min` + `ke_teto` revised | VERIFIED | All present at `config.yaml:235-256` with WHY comments each. `ke_teto: 0.13` confirmed. |
| `src/analista/report/report.py` | Dispatch `_intrinseco_motor` passes new knobs to `motores.rim` | VERIFIED | Lines 202-212: `res_rim = motores.rim(..., excesso_sustentavel=rim_cfg.get("excesso_sustentavel", 0.0), g_terminal=rim_cfg.get("g_terminal"), ke_g_spread_min=rim_cfg.get("ke_g_spread_min", 0.03))`. Wired and defensively defaulted. |
| `tests/test_motores.py` | Golden updated + hard gate ITUB4 R$32-40 + anti-bad-bank test | VERIFIED | `test_rim_itub4_live_alvo_32_40` contains the literal `32.0 <= res.valor_intrinseco <= 40.0` assertion (line 61); reads knobs from `_cfg()` (proves config-driven, not hardcoded); asserts `ke_rim(1.29,cfg)==0.13`. All RIM tests pass (7/7 in `-k rim`). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `motores.py::rim` | `ddm.py::valor_gordon` | perpetuidade do RI terminal | WIRED | `tv = ddm.valor_gordon(dpa1=ri_terminal, ke=ke, g=g_terminal)` — direct call, confirmed by grep and by reading the function body. |
| `report.py::_intrinseco_motor` | `motores.rim` | passa excesso_sustentavel/g_terminal lidos de cfg | WIRED | Confirmed by reading `report.py:200-212`; also proven end-to-end by `test_rim_itub4_dispatch_banda`, which runs `report.analisar_acao()` (not a direct `motores.rim()` call) and asserts the result reflects the terminal value (`> 30.0`, vs the old D-02 ceiling of ~R$23). |

### Data-Flow Trace (Level 4)

Not applicable in the standard UI sense (no React/Vue component rendering state) — this is a pure numeric engine. The equivalent trace was performed at the dispatch level: `report.analisar_acao()` → `_intrinseco_motor(motor="rim")` → `motores.rim(...)` → real computed float (not a static/empty stub). Confirmed by both the integration test and an independent live re-run outside the suite (see Truth #1).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| ITUB4 live intrinsic lands in R$32-40 | Reproduced `motores.rim(...)` + `ke_rim(...)` outside pytest via inline Python | R$32.87, ke=0.13, vp_terminal=5.73 | PASS |
| Bad-bank guard produces P/B < 1 | Reproduced `motores.rim(vpa0=22, roe0=0.10, ke=0.125,...)` outside pytest | R$15.54, vp_terminal=-2.76 | PASS |
| Full suite green | `pytest tests/` | 440 passed, 0 failed | PASS |
| Forbidden files untouched | `git diff da942c2 HEAD --stat -- ddm.py selo.py lentes.py` | empty diff | PASS |

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` convention found in this repo and none declared in the PLAN/SUMMARY. Skipped.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CAL-01 | 04-01-PLAN.md | RIM ganha valor terminal, parametrizado, ITUB4 R$32-40 | SATISFIED | Truths #1, #2 above; live reproduction R$32.87 |
| CAL-02 | 04-01-PLAN.md | Ke do RIM revisado ke_teto 0.14→0.13, sem explosão | SATISFIED | Truth #3 above; `ke_rim(1.29,cfg)==0.13` reproduced |

REQUIREMENTS.md marks both CAL-01 and CAL-02 as `[x]` and traces both to Phase 4 — consistent with this phase's scope. No orphaned requirement IDs for Phase 4 (VAL-01/VAL-02 → Phase 5, OPS-01 → Phase 6, correctly out of this phase's scope).

### Anti-Patterns Found

No blocker-level anti-patterns. No `TBD`/`FIXME`/`XXX` debt markers in any file modified by this phase (`motores.py`, `config.yaml`, `report.py`, `test_motores.py`, `test_vulc3_regressao.py`). No `TODO`/`HACK`/`PLACEHOLDER`/stub-return patterns found in the modified code paths.

Pre-existing code review (`04-REVIEW.md`, 0 blockers, 3 warnings) flags latent robustness concerns, assessed here for goal impact:

| File | Finding | Severity | Goal Impact |
|------|---------|----------|-------------|
| `motores.py:104-116` | WR-01: explicit window RI diverges unboundedly as `n` grows when `fade_para × retencao ≥ ke` (high-retention banks, payout ≤ ~25%) | Warning | **Does not undermine current goal.** Shipped default `n_fade=10` with the calibration basket's retention (~0.53, ITUB4-like) stays well inside the bounded regime — verified numerically (R$32.87, R$39.23 golden, both in target bands). Latent risk only surfaces for future high-retention tickers or if `n_fade` is raised without a corresponding guard — a Fase 5 (BACKTEST-01) calibration concern, not a Phase 4 regression. |
| `motores.py:95-96,102-103` | WR-02: "backward-safe" docstring claim is false for legacy 5-arg call when `roe0 < ke` | Warning | **Does not undermine current goal.** No caller in the repo invokes the legacy 5-arg form with `roe0 < ke` — dispatch always passes `excesso_sustentavel` explicitly, and the only bare legacy test call uses `roe0 == ke`. Documentation-accuracy issue, not a behavioral gap in the shipped phase. |
| `motores.py:149` | WR-03: `ke_rim`'s defensive fallback still defaults `ke_teto` to the rejected `0.14` if `motores.rim` config block is missing (confirmed present: `rim_cfg.get("ke_teto", 0.14)`) | Warning | **Does not undermine current goal.** Current `config.yaml` always has the `motores.rim` block with `ke_teto: 0.13`, so the fallback path is never exercised in production config. Only a latent risk if config is malformed in the future. |

These three warnings are real and should be tracked (ideally closed in a follow-up), but per review disposition (0 blockers) and the numerical re-verification performed here, none causes the phase's observable truths to fail with the shipped configuration. Recommend addressing WR-01 (the most material — unbounded divergence for high-retention banks) before or during Phase 5 (BACKTEST-01), since the validation basket will include other banks (BBAS3, BBSE3, BBDC4) whose retention profiles are not yet confirmed to stay inside the safe regime.

### Human Verification Required

None. This phase is a pure numeric engine change (no UI, no external service, no visual/async behavior) — all claims are verifiable programmatically and were independently reproduced above.

### Gaps Summary

No gaps found. All 5 observable truths verified with independent reproduction (not just trusting SUMMARY.md or pytest pass/fail alone — actual numeric outputs were recomputed live in this verification and matched exactly: R$32.87 ITUB4 live, ke=0.13, R$15.54 bad-bank, 440/440 suite green, zero diff on `ddm.py`/`selo.py`/`lentes.py`). Both requirement IDs (CAL-01, CAL-02) satisfied and traced correctly in REQUIREMENTS.md. Code review warnings (WR-01/02/03) are legitimate latent-risk findings but do not block the shipped phase goal under the current default configuration.

---

_Verified: 2026-07-12_
_Verifier: Claude (gsd-verifier)_
