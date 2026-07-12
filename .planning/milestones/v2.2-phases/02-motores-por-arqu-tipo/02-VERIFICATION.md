---
phase: 02-motores-por-arqu-tipo
verified: 2026-07-11T23:17:09Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "ITUB4, roteado para RIM, produz um valor intrínseco coerente com mercado, materialmente acima do ~R$16 do DDM comprimido (redação original citava ~R$40)"
    reason: "Desvio documentado e aprovado no PLAN/CONTEXT (D-02): o modelo RIM honesto/conservador (fade completo do excesso de ROE até o Ke, SEM prêmio terminal) rende ~R$28 (faixa R$26-34) para inputs tipo-ITUB4, e ~R$26,63 com o ke_rim() real (~0,14) — não ~R$40. O ~R$40 era um alvo aproximado da fase de discussão; adicionar prêmio terminal para forçar R$40 violaria D-02 (conservadorismo). A intenção real do critério (destravar o ITUB4 do 'evitar' com intrínseco materialmente > DDM ao vivo) é cumprida e verificada aritmeticamente no código."
    accepted_by: "gsd-verifier (per explicit instruction in verification task — desvio documentado em 02-CONTEXT.md D-02 e nos SUMMARYs 02-01/02-02)"
    accepted_at: "2026-07-11T23:17:09Z"
deferred:
  - truth: "Um arquétipo holding é classificado organicamente (via core/arquetipo.classificar) e roteado para NAV em produção"
    addressed_in: "Phase 3 (backlog ARQ) / documented as known gap in 02-02-SUMMARY.md"
    evidence: "02-02-SUMMARY.md Known Gaps: 'Classificador não emite a chave holding ... Fazer o classificador EMITIR holding (sinal de participações/SOTP) é escopo ARQ futuro, não deste plano de motores.' The NAV motor itself (ENG-05) IS implemented, plugged into ARQUETIPO_MOTOR (HOLDING: 'nav'), wired in the report.py dispatch, and validated e2e via monkeypatch-forced routing in test_holding_roteia_nav_igual_vpa — only the classifier's emission of the 'holding' key is out of scope for this phase."
---

# Phase 2: Motores por Arquétipo Verification Report

**Phase Goal:** Plugar no registry os motores primários que faltam (RIM, lucro normalizado, DCF multi-estágio, NAV/SOTP) roteados pelo classificador da Fase 1, para que cada arquétipo calcule o intrínseco pelo modelo certo, com o DDM rebaixado a "lente conservadora" onde não é o primário.
**Verified:** 2026-07-11T23:17:09Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ITUB4/RIM produz intrínseco coerente com mercado, materialmente acima do DDM ao vivo (~R$16); DDM aparece rebaixado a "lente conservadora" | PASSED (override) | `motores.rim(vpa0=22.0, roe0=0.193, ke=0.125, retencao=0.53, n=10).valor_intrinseco` = **R$28,20** (arithmetically re-verified live, matches golden `test_rim_itub4_honesto_maior_que_ddm`). With the REAL `ke_rim()` (0.14, not the golden unit 0.125) the value is **R$26,63** — still in the documented R$26-34 band and materially above ~R$16. e2e anchor `test_financeira_rim_destrava_vs_ddm_e_segue_verificar` asserts `intrinseco_motor > 1.3 × ddm_ref` (relative to the SAME fixture's live DDM) and `> vpa` — both pass. Render confirmed to label DDM as "lente conservadora" (`report.py:591`, `test_render_financeira_exibe_motor_e_ddm_como_lente` passes). Override applied per explicit task instruction: the "~R$40" wording in the original acceptance criterion is a documented, approved deviation (D-02, honest/conservative model without terminal premium) — verified NOT to be a stub/failure, but an intentional, aritmetically-checked reconciliation. |
| 2 | VALE3/cíclica valua sobre lucro normalizado (média 7–10a) | VERIFIED | `arquetipo.ARQUETIPO_MOTOR["ciclica"] == "normalizado"`; `report.py:208-217` dispatch calls `norm.base_normalizada(c.serie("lucro_liquido"), anos_media=10, winsor=0.10)` then `motores.lucro_normalizado(lpa_mid, a.ke, g_estavel)` = LPA normalizado × Gordon fair-PE. e2e anchor `test_ciclica_roteia_lucro_normalizado` passes (`a.motor == "normalizado"`, `intrinseco_motor > 0`). Golden `test_lucro_normalizado_usa_media_e_ignora_pico_vale` proves the oscillating-series case ignores the last-year spike. |
| 3 | WEGE3/crescimento usa DCF multi-estágio, sem zero/lixo | VERIFIED | `arquetipo.ARQUETIPO_MOTOR["crescimento"] == "dcf"`; `report.py:218-222` dispatch calls `motores.dcf_crescimento(c.lpa_valuation(), a.g_alto, g_estavel, a.ke, n=10)`, which reuses `ddm.ddm_dois_estagios` with profit substituted for dividend (grep confirms `ddm.ddm_dois_estagios` call inside `dcf_crescimento`). e2e anchor `test_crescimento_roteia_dcf_positivo_finito` asserts `intrinseco_motor > 0 and math.isfinite(...)`. Passes. |
| 4 | Um arquétipo holding usa NAV como motor primário | VERIFIED (with accepted, documented gap — see Deferred) | `arquetipo.ARQUETIPO_MOTOR["holding"] == "nav"`; `report.py:223-226` dispatch calls `motores.nav_contabil(...)` = `lentes.vpa(...)`. The motor is implemented, registered, and wired end-to-end (`test_holding_roteia_nav_igual_vpa` proves `a.motor == "nav"` and `intrinseco_motor == vpa` when routed). **Known gap (explicitly accepted per verification task instructions):** `core/arquetipo.classificar` never organically emits the `"holding"` key yet (Phase 1 classifier scope), so the e2e test forces the route via `monkeypatch`. This is documented as an accepted, non-blocking gap in `02-02-SUMMARY.md` ("Known Gaps") and deferred to Phase 3 / ARQ backlog — not a stub of the motor itself. |
| 5 | O golden test_ddm continua verde (ddm.py intocado) | VERIFIED | `python -m pytest tests/test_ddm.py -x` → all pass. `git diff --name-only 2531656 HEAD -- src/` lists only `cli.py`, `core/arquetipo.py`, `core/motores.py`, `report/report.py` — `core/ddm.py`, `core/lentes.py`, `core/capm.py`, `core/normalizacao.py`, `report/selo.py` are absent from the diff (confirmed untouched). |

**Score:** 5/5 truths verified (4 direct + 1 via documented override)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Classifier organically emitting the `holding` arquétipo key | Phase 3 / ARQ backlog | `02-02-SUMMARY.md` "Known Gaps" section — explicitly scoped out of Phase 2 (motor engine), scoped into future classifier (ARQ) work. Per verification task instructions, treated as an accepted, non-blocking known gap, not a phase-goal failure — the NAV motor exists, is registered, and is wired/disparável. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/motores.py` | `rim()`, `ke_rim()`, `lucro_normalizado()`, `dcf_crescimento()`, `nav_contabil()`, `ResultadoRIM`, `MOTOR_ROTULO` | VERIFIED | All 5 functions + dataclass + rótulo dict present, never-raise guards confirmed by reading source, all golden-tested (`tests/test_motores.py`, 11 tests pass) |
| `config.yaml` bloco `motores:` | rim/ciclica/crescimento sub-blocks, additive | VERIFIED | `git diff 2531656 HEAD -- config.yaml` shows pure addition (26 new lines appended); zero deletions in existing `capm:`/`ddm:`/`arquetipo:` blocks |
| `tests/test_motores.py` | golden puro por motor | VERIFIED | 11 tests, all pass (RIM ~R$28,20 & fade→0, ke_rim<ke_live, normalizado ignores spike, dcf>0 finite, nav==vpa, never-raise cases) |
| `src/analista/core/arquetipo.py::ARQUETIPO_MOTOR` | 5/5 filled, no `None` | VERIFIED | `{financeira: "rim", pagadora_regulada: "ddm", ciclica: "normalizado", crescimento: "dcf", holding: "nav"}` — confirmed by direct read, no `None` present |
| `src/analista/report/report.py` | `intrinseco_motor`/`motor_rotulo` fields + dispatch + suspension migration + render | VERIFIED | Fields present in `AnaliseAcao` (:59-60); dispatch block :198-227 calls the right motor per `a.motor`; suspension migrated to `if a.motor != "ddm":` (:281); render shows motor intrinsic value + "lente conservadora" label (:582-591) |
| `src/analista/cli.py` | `_motor_pendente` migrated to `!= "ddm"` | VERIFIED | Line 56: `return arquetipo.ARQUETIPO_MOTOR.get(arq.chave) != "ddm"` |
| `tests/test_arquetipo_roteamento.py` | e2e anchors per motor + updated asserts | VERIFIED | 6 new e2e anchors present (financeira/RIM, cíclica/normalizado, crescimento/DCF, holding/NAV via monkeypatch, regulada/DDM, render) — all pass |
| `tests/test_ranking_freio.py` | suspension assert updated to `!= "ddm"` | VERIFIED | `test_motor_pendente_financeira_suspende` and `test_motor_pendente_regulada_tem_motor` reflect the migrated predicate, both pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `motores.py::rim`/`ke_rim` | `config.yaml motores.rim` | `cfg["motores"]["rim"][...]` | WIRED | `ke_rim()` reads `erp_banco`/`ke_piso`/`ke_teto`; `rim()` receives `n=cfg["motores"]["rim"]["n_fade"]` from `report.py:205` |
| `motores.py::dcf_crescimento` | `core/ddm.py::ddm_dois_estagios` | import + call | WIRED | `motores.py:148` calls `ddm.ddm_dois_estagios(...)`; `ddm.py` confirmed absent from git diff (untouched) |
| `motores.py::nav_contabil` | `core/lentes.py::vpa` | import + call | WIRED | `motores.py:165` returns `lentes.vpa(...)` directly |
| `motores.py::lucro_normalizado` | `ddm.valor_gordon` + `normalizacao.base_normalizada` | import + call | WIRED | `motores.py:127` calls `ddm.valor_gordon(...)`; `report.py:211` calls `norm.base_normalizada(...)` before dispatch (fronteira FIX-04 respected — motor receives already-normalized LPA) |
| `arquetipo.py::ARQUETIPO_MOTOR` | `report.py` dispatch | `a.motor == "rim"/"normalizado"/"dcf"/"nav"` | WIRED | `report.py:188-227` resolves `a.motor` from registry then dispatches by exact string match |
| `report.py:281` (suspensão) | `cli.py:45-56` (`_motor_pendente`) | same predicate `motor != "ddm"` | WIRED | Both surfaces use the identical migrated predicate; confirmed by direct read and passing `test_ranking_freio.py` |
| `report.py` dispatch | `motores.(rim\|dcf_crescimento\|lucro_normalizado\|nav_contabil)` | import + call, consuming `*_valuation()` | WIRED | Confirmed inputs are `roe_valuation()`/`lpa_valuation()`/`payout_valuation()`/`base_normalizada()`/`lentes.vpa()` — no raw `c.lucro_liquido.get(ult)` inside the dispatch block |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `report.py` dispatch → `a.intrinseco_motor` | RIM branch | `motores.rim(vpa0=lentes.vpa(real PL/ações), roe0=c.roe_valuation(), ke=motores.ke_rim(c.beta, cfg), retencao=1-payout_valuation())` | Live computation from `CompanyData`, not hardcoded/static | FLOWING |
| `report.py` dispatch → `a.intrinseco_motor` | cíclica branch | `norm.base_normalizada(c.serie("lucro_liquido"), ...)` → `motores.lucro_normalizado(...)` | Live computation from full lucro series | FLOWING |
| `report.py` dispatch → `a.intrinseco_motor` | crescimento branch | `motores.dcf_crescimento(c.lpa_valuation(), a.g_alto, ...)` | Live computation | FLOWING |
| `report.py` dispatch → `a.intrinseco_motor` | holding branch | `motores.nav_contabil(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))` | Live computation; reachable route not organically produced by classifier yet (documented, accepted gap) | FLOWING (reachability limited by Phase-1 classifier scope, not this phase) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| RIM real (ke_rim live) ITUB4-like inputs | `motores.rim(vpa0=22.0, roe0=0.193, ke=motores.ke_rim(1.0,cfg), retencao=0.53, n=10)` | `ke_rim=0.14`, `valor_intrinseco=R$26.63`, `ke_live=0.165` | PASS — within documented R$26-34 band, ke_rim < ke_live |
| Full test suite | `python -m pytest -q` | `406 passed` | PASS |
| Phase-scoped tests | `python -m pytest tests/test_motores.py tests/test_ddm.py tests/test_arquetipo_roteamento.py tests/test_ranking_freio.py tests/test_selo.py -q` | `58 passed` | PASS |
| Untouched-files guard | `git diff --name-only 2531656 HEAD -- src/` | `cli.py, core/arquetipo.py, core/motores.py, report/report.py` only | PASS — `core/ddm.py`/`lentes.py`/`capm.py`/`normalizacao.py`/`report/selo.py` absent |
| Config additive-only guard | `git diff 2531656 HEAD -- config.yaml` | Pure addition, 0 deletions | PASS |

### Probe Execution

No dedicated `scripts/*/tests/probe-*.sh` files found in this repository; no probes declared in PLAN/SUMMARY. Step 7c: SKIPPED (no probe files; pytest suite serves as the runnable verification surface and was executed directly above).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ENG-02 | 02-01-PLAN, 02-02-PLAN | RIM disponível como motor primário para banco/seguradora | SATISFIED | `motores.rim`/`ke_rim` implemented, golden-tested, plugged (`FINANCEIRA: "rim"`), wired in dispatch, e2e anchor passes |
| ENG-03 | 02-01-PLAN, 02-02-PLAN | Lucro normalizado como motor primário para cíclica | SATISFIED | `motores.lucro_normalizado` implemented, plugged (`CICLICA: "normalizado"`), wired, e2e anchor passes |
| ENG-04 | 02-01-PLAN, 02-02-PLAN | DCF multi-estágio como motor primário para crescimento | SATISFIED | `motores.dcf_crescimento` implemented (reuses `ddm.ddm_dois_estagios`), plugged (`CRESCIMENTO: "dcf"`), wired, e2e anchor passes (positive/finite, no zero/lixo) |
| ENG-05 | 02-01-PLAN, 02-02-PLAN | NAV/SOTP como motor primário para holding | SATISFIED (motor); classifier routing deferred (see Deferred section) | `motores.nav_contabil` implemented, plugged (`HOLDING: "nav"`), wired; NAV route validated e2e via forced routing since Phase-1 classifier doesn't yet emit `holding` organically — documented, accepted, out of this phase's scope |

No orphaned requirements — `REQUIREMENTS.md` traceability table maps exactly ENG-02/ENG-03/ENG-04/ENG-05 to Phase 2, matching both PLAN frontmatter `requirements:` fields.

### Anti-Patterns Found

None found in files modified by this phase (`motores.py`, `arquetipo.py`, `report.py`, `cli.py`, `config.yaml`). Grep for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` produced one false-positive match (substring "TODOS" inside a Portuguese comment in `report.py:120`, unrelated to a TODO marker). No stub returns, no hardcoded empty data flowing to `intrinseco_motor`, no console.log-only implementations.

### Human Verification Required

None. All must-haves are verifiable programmatically via source inspection, direct function execution, and the automated test suite. No visual/UX, real-time, or external-service behavior is introduced by this phase (render is markdown text, verified by substring assertions already covered by the automated suite).

### Gaps Summary

No blocking gaps. One documented, accepted deviation (RIM ~R$28 honest vs the original "~R$40" wording — formally overridden per explicit task instruction and D-02 in `02-CONTEXT.md`) and one documented, accepted deferred item (holding classifier routing, explicitly out of Phase 2 scope per `02-02-SUMMARY.md` "Known Gaps" and the verification task's own framing). Both are called out transparently in the SUMMARYs and PLAN frontmatter rather than hidden — they reflect intentional, reasoned engineering decisions, not incomplete work. The core deliverable — 4 new valuation engines that are pure, never-raise, config-driven, golden-tested, registered in `ARQUETIPO_MOTOR`, dispatched in the funnel, and rendered with the DDM correctly demoted to "lente conservadora" — is fully implemented and verified against the live codebase (not just SUMMARY claims).

---

_Verified: 2026-07-11T23:17:09Z_
_Verifier: Claude (gsd-verifier)_
