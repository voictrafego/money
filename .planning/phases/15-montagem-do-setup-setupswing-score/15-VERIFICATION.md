---
phase: 15-montagem-do-setup-setupswing-score
verified: 2026-06-30T00:00:00Z
status: passed
score: 9/9
overrides_applied: 0
re_verification: false
---

# Phase 15: Montagem do Setup (SetupSwing) + Score — Verification Report

**Phase Goal:** Um dataclass read-only `SetupSwing` integra contexto + níveis + sinais + padrões num score ponderado explicável, com R:R como gate, em linguagem de estudo que exibe e nunca recomenda.
**Verified:** 2026-06-30
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `montar_setup(sinais, cfg)` nunca levanta exceção para a UI — degrada para "Sem setup" | VERIFIED | `montar_setup(None, cfg)` returns `SetupSwing(score=0.0, grade="Sem setup")` confirmed by smoke + `test_setup_degrada_sem_excecao` (PASSED) |
| 2 | Score decomposto peso a peso; tendência domina com peso 35 | VERIFIED | `ContribFamilia` struct in setup.py L31-38; `test_decomposicao_soma_score` asserts `Σ contribuicao == score` and each peso matches config — PASSED |
| 3 | R:R abaixo do mínimo OU indisponível → grade "Sem setup" com `gate_rr_ok=False` | VERIFIED | `test_gate_rr_zera_setup` (rr=1.1 < 1.5 → FAIL gate) and `test_rr_indisponivel_sem_setup` (entrada_zona=None → rr_valor=None) — both PASSED |
| 4 | Conflito multi-TF penaliza o score sem sozinho derrubar para "Sem setup" | VERIFIED | `test_conflito_mtf_penaliza_sem_bloquear` asserts `score == base*(1−pen)`, `grade != "Sem setup"` — PASSED |
| 5 | Grade final pertence a {Forte, Moderado, Fraco, Sem setup} | VERIFIED | `test_setup_forte`, `test_setup_moderado`, `test_setup_fraco`, `test_setup_sem_setup_por_score_baixo` — all PASSED; `test_e2e_calcular_integra` asserts `grade in {"Forte","Moderado","Fraco","Sem setup"}` |
| 6 | Pesos, rr_minimo, rr_alvo, penalidade e cortes vêm de `cfg["score"]` — zero hardcode | VERIFIED | `test_score_config_driven` zeroes `pesos["volume"]` in-memory and proves score shifts by exactly 10 — PASSED; code reads `sc = cfg["score"]` at L166 |
| 7 | Copy de grade/detalhe é neutra/de estudo (sem termos imperativos) | VERIFIED | `test_setup_sem_copy_imperativa` (line 160) scans 5 scenarios against 8 forbidden terms — PASSED |
| 8 | `setup.py` importa apenas `from ..core import indicators` — NUNCA `report.py` (firewall) | VERIFIED | `grep -E "from .*report\|import report" src/analista/report/setup.py` returns empty |
| 9 | 271 goldens existentes seguem verdes (engine fundamentalista e aba Analisar intactas) | VERIFIED | Full suite: **283 passed** (271 existing + 12 new) in 2.53s — zero regressions |

**Score:** 9/9 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/report/setup.py` | `SetupSwing` + `ContribFamilia` + `montar_setup` read-only | VERIFIED | 217 lines (> 90 min); contains `def montar_setup`, `@dataclass class SetupSwing`, `@dataclass class ContribFamilia` |
| `config.yaml` | Bloco `score:` com pesos 35/20/20/15/10, rr_minimo, rr_alvo, penalidade_conflito_mtf, cortes_grade | VERIFIED | Block at L145; pesos sum=100; forte=70 > moderado=50 > fraco=25; `indicadores:` and `padroes:` untouched |
| `tests/test_setup_report.py` | 12 goldens: grades, gate R:R, decomposição, multi-TF, degradação, anti-copy, config-driven, e2e | VERIFIED | 12 tests collected and all PASSED; contains `def _sinais_stub`, `def test_setup_sem_copy_imperativa`, `def test_gate_rr_zera_setup`, `def test_decomposicao_soma_score` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/analista/report/setup.py` | `cfg["score"]` | `sc = cfg["score"]`; reads `pesos`, `rr_minimo`, `rr_alvo`, `penalidade_conflito_mtf`, `cortes_grade` | WIRED | L166-167 in setup.py; test_score_config_driven proves end-to-end |
| `src/analista/report/setup.py` | `sinais.niveis.entrada_zona/stop/alvo` | `_rr_valor(niveis)` under `np.errstate(divide="ignore", invalid="ignore")` | WIRED | L69-81 in setup.py; `grep -c "np.errstate"` = 2; NaN/inf protected |
| `src/analista/report/setup.py` | `src/analista/core/indicators` | `from ..core import indicators` (L23) | WIRED | Verified via grep; sole external import; `PadraoGrafico`/`Padroes` used via `indicators.*` in tests |

---

### Invariant Checks

| Invariant | Command | Result | Status |
|-----------|---------|--------|--------|
| FIREWALL: no `from.*report` or `import report` in setup.py | `grep -E "from .*report\|import report" setup.py` | empty | PASS |
| Graceful degradation: `montar_setup(None, cfg)` returns `SetupSwing(score=0.0, grade="Sem setup")` | Python smoke | `score=0.0, grade="Sem setup"` | PASS |
| No series recalculation: zero `rolling`/`.ewm(`/`.diff(` in setup.py | `grep -c` | 0 | PASS |
| `np.errstate` gate present | `grep -c "np.errstate"` | 2 | PASS |
| `test_setup_sem_copy_imperativa` exists and is green | grep + pytest | L160; PASSED | PASS |
| Full suite: 283 passed | `.venv/bin/python -m pytest -q` | 283 passed in 2.53s | PASS |
| `config.yaml` only gained `score:` block; `indicadores:` and `padroes:` intact | Python config load | all 3 blocks present; pesos sum=100 | PASS |

---

### Data-Flow Trace (Level 4)

`setup.py` is a pure computation module (no rendering). Data flows from `cfg["score"]` (config) and `SinaisTecnicos` (in-memory contract from Phases 12-14) into `SetupSwing` output. No database, no fetch, no async. The data source is the caller-supplied `sinais` object; `test_e2e_calcular_integra` runs `indicators.calcular(frame, cfg)` → `montar_setup(s, cfg)` end-to-end and asserts a valid `SetupSwing` is returned. Data flow: FLOWING.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `montar_setup(None, cfg)` returns grade="Sem setup", no exception | Python smoke | `score=0.0, grade="Sem setup"` | PASS |
| 12 new test goldens green | `pytest tests/test_setup_report.py -v` | 12 passed in 0.60s | PASS |
| Full suite 283 green | `pytest -q` | 283 passed in 2.53s | PASS |
| Config smoke: pesos sum=100, grade ordering | Python config validation | all assertions pass | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SCORE-01 | 15-01-PLAN.md | Score ponderado explicável com decomposição peso a peso, R:R como gate, grade qualitativa, pesos em config.yaml | SATISFIED | All 9 truths verified; `SetupSwing` + `montar_setup` implemented and tested with 12 passing goldens |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No debt markers (TBD/FIXME/XXX), no stubs, no hardcoded empty returns | — | None |

---

### Human Verification Required

None. All observable behaviors were verifiable programmatically (pure computation, no UI rendering, no external services).

---

## Gaps Summary

No gaps. All 9 must-have truths are VERIFIED, all 3 artifacts exist and are substantive and wired, all key links are confirmed, zero regressions in the 271 existing goldens, and the 12 new tests are all green.

---

_Verified: 2026-06-30_
_Verifier: Claude (gsd-verifier)_
