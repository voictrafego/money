---
phase: 15-montagem-do-setup-setupswing-score
reviewed: 2026-06-30T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/analista/report/setup.py
  - tests/test_setup_report.py
  - config.yaml
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-06-30
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Adversarial review of the SetupSwing scoring engine (SCORE-01). The five domain invariants
were all spot-checked and mostly hold:

- **FIREWALL (OK):** `setup.py` imports only `from ..core import indicators` plus `numpy` and
  `dataclasses`. No import of `report.py` / the fundamentalist engine. Confirmed via grep.
- **R:R gate recomputed (OK):** `_rr_valor` rebuilds the ratio from raw `entrada_zona/stop/alvo`
  under `np.errstate`; it never parses the `risco_retorno` string. The test deliberately sets
  `risco_retorno="indisponivel"` yet still gets a valid ratio, proving recomputation.
- **Copy neutrality (OK):** All `grade`/`familia`/`detalhe` strings are stable study labels
  ("Forte", "duplo_fundo:confirmado", "rr=3,0"); none are imperative. The acceptance gate test
  covers long/short/degraded scenarios.
- **Graceful degradation (PARTIAL):** The `None`-guards for `sinais/niveis/contexto` work, but
  several un-guarded paths can still raise — see WR-02.
- **Config-driven (PARTIAL):** Family weights, R:R gate, penalty and grade cuts come from
  `cfg["score"]` (proven by `test_score_config_driven`). However the *intra-family* sub-score
  constants are hardcoded — see WR-01.

The scoring math is internally consistent and the arithmetic in every test comment checks out
(62.5 → Moderado, 46.25 → Fraco, 1.33 → Sem setup, rr=1.1 → gate fail). No correctness blocker
was found. Two robustness/principle warnings and two quality notes follow.

## Warnings

### WR-01: Intra-family sub-score constants are hardcoded, contradicting the "zero hardcode / ajuste sem deploy" principle

**File:** `src/analista/report/setup.py:92-98, 137-144, 122, 152-154`
**Issue:** The phase principle (docstring L12, and `config.yaml` L142-144: *"zero hardcode de
pesos/cortes (D-01)"*, *"ajuste sem deploy"*) states everything driving the score lives in
`cfg["score"]`. That holds for the **family weights** (`pesos`), `rr_minimo/rr_alvo`,
`penalidade_conflito_mtf` and `cortes_grade`. But the constants that compute each family's
`[0,1]` sub-score are baked into code and absent from config:
- `_sub_tendencia`: `base = 0.6`, ADX bonus `0.25`, MM200 bonus `0.15` (L92, L94, L97).
- `_sub_momentum`: each confirmation `0.5` (L136, L139, L142, L144).
- `_sub_padroes`: confirmed `1.0` / em_formacao `0.5` (L122).
- `_sub_volume`: rompimento `1.0` / acima_mm `0.5` (L152, L154).

These are exactly the "ASSUMED/calibráveis" values the docstring (L86-87) admits to, yet they
cannot be tuned without a code deploy — which conflicts with the config comment's promise. The
config-driven test only mutates `pesos`, so it does not catch this. This is a maintainability /
principle-conformance gap, not a runtime bug.
**Fix:** Either (a) move these constants into a `cfg["score"]["sub_pesos"]` block and read them
in each `_sub_*` helper, or (b) if intentionally fixed geometry, soften the docstring/config
comments so they don't claim "zero hardcode / ajuste sem deploy" for the whole setup montage.

### WR-02: `montar_setup` has un-guarded paths that can raise, violating the "NUNCA levanta exceção para a UI" contract

**File:** `src/analista/report/setup.py:73, 166-169, 181, 183-185`
**Issue:** The function guarantees graceful degradation (docstring L11, L162), but only guards
`sinais/niveis/contexto` being `None`. Other inputs still propagate exceptions to the UI:
- `low, high = niveis.entrada_zona` (L73) assumes a 2-element tuple. A tuple of any other
  arity raises `ValueError`/`TypeError` instead of degrading to "Sem setup".
- `sc = cfg["score"]`, `pesos = sc["pesos"]`, `sc["rr_minimo"]`, `sc["rr_alvo"]`,
  `sc["penalidade_conflito_mtf"]`, `sc["cortes_grade"]` (L166-167, L173, L200, L203) raise
  `KeyError`/`TypeError` if config is malformed or `None`.
- Direct attribute access `sinais.forca / sinais.tendencia / sinais.padroes / sinais.momentum /
  sinais.volume` (L181, L183-185) raises `AttributeError` if a contract field is absent (the
  inner reads use `getattr`, but these top-level reads do not).

The `niveis.entrada_zona` unpack is the most reachable: a lateral/partial `Niveis` with a
malformed zone would crash the whole report rather than show "Sem setup".
**Fix:** Either wrap the body in a `try/except Exception: return SetupSwing(score=0.0,
grade="Sem setup")` at the boundary (matching the stated invariant), or guard the specific
risks — e.g. validate `isinstance(niveis.entrada_zona, tuple) and len(niveis.entrada_zona) == 2`
inside `_rr_valor`, and use `getattr(sinais, "forca", None)` etc. for the family sub-objects.

## Info

### IN-01: `indicators` import is unused (dead import)

**File:** `src/analista/report/setup.py:23`
**Issue:** `from ..core import indicators` is documented as "só p/ tipos", but the symbol is
never referenced in code — `montar_setup(sinais, cfg)` is fully duck-typed with no
`indicators.SinaisTecnicos` annotation or `isinstance` check, and `indicators.` appears only
inside a comment (L67). A linter (ruff/flake8 F401) flags it. It still documents the firewall
intent, but provides no functional type coupling.
**Fix:** Either add a real type annotation that uses it (e.g. `def montar_setup(sinais:
"indicators.SinaisTecnicos | None", cfg) -> SetupSwing:`), or drop the import and keep the
firewall note as a comment only.

### IN-02: `_sub_momentum` detalhe omits the RSI contribution

**File:** `src/analista/report/setup.py:145`
**Issue:** Momentum can score from two independent signals (MACD cross + non-extreme RSI), each
0.5, but the returned `detalhe` is only `f"macd:{macd}"`. The peso-a-peso decomposition (D-02
transparency goal) is therefore incomplete for this family: a 0.5 sub-score from RSI alone shows
`macd:nenhum`, which reads as if nothing contributed.
**Fix:** Include the RSI signal in the label, e.g. `f"macd:{macd}|rsi:{rsi}"`, so the
decomposition fully explains the momentum sub-score.

---

_Reviewed: 2026-06-30_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
