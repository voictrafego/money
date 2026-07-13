---
phase: 05-backtest-01-valida-o-na-cesta-de-bancos
reviewed: 2026-07-13T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - scripts/capturar_snapshot_bancos.py
  - scripts/backtest_bancos.py
  - src/analista/backtest.py
  - tests/test_backtest_bancos.py
  - tests/fixtures/snapshot_bancos_2026-07-12.yaml
  - tests/fixtures/fair_values_bancos.yaml
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: resolved
---

# Phase 05: Code Review Report

**Reviewed:** 2026-07-13
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed the BACKTEST-01 harness (`src/analista/backtest.py`), its deterministic gate
(`tests/test_backtest_bancos.py`), the two standalone scripts, and the two frozen YAML
fixtures. Verified, by reading and by execution, the three claims the phase makes about
itself:

- **Reuse, not reimplementation:** `rodar_cesta` genuinely sources the RIM value from
  `report.analisar_acao(...).intrinseco_motor`; `grep -c 'motores.rim('` on the module is
  0, confirmed. `report.analisar_acao` and `core/motores.py::rim` do not mutate `cfg`, and
  neither does anything in the call path make a network call — offline guarantee holds.
- **Determinism:** ran `pytest tests/test_backtest_bancos.py -v` — reproduces exactly the
  documented `2 passed, 1 xfailed`. `statistics.median` inputs come from a fixed-order list
  built once per call from a YAML file dumped with `sort_keys=True`, so there is no
  dict/set-iteration nondeterminism in this phase's code.
- **Gate logic:** `_passa`'s ±15% band widening (`fv_min*(1-0.15) .. fv_max*(1+0.15)`) and
  the `QUORUM_MIN = 3` check match the documented D-06/D-07/D-08 rules exactly, and the
  numbers reproduce the table in `05-04-SUMMARY.md` (ITUB4 PASS, the other three FAIL).

No blockers found. The two warnings below are about the **robustness of the gate itself**
as a long-lived regression tripwire (not about the frozen numbers, which this review was
explicitly told not to second-guess) — worth fixing so the `xfail(strict=True)` tripwire
can't be accidentally defeated by an unrelated future breakage, and so the harness's
"PURA" claim in its own docstring is actually true.

## Warnings

### WR-01: `xfail` has no `raises=`, so an unrelated exception is indistinguishable from the documented gate failure

**File:** `tests/test_backtest_bancos.py:86-94`
**Issue:** `test_backtest_gate_quorum_e_anotacao` is marked
`@pytest.mark.xfail(strict=True, reason="D-12: cesta 1/4 na banda...")` with no `raises=`
argument. `pytest.mark.xfail` without `raises=` swallows **any** exception raised inside
the test body as "expected failure" — not just the two `assert` statements the reason
text describes. Reproduced empirically with a minimal repro (any exception, not just
`AssertionError`, satisfies a bare `xfail(strict=True)`):

```
@pytest.mark.xfail(strict=True, reason="demo")
def test_demo():
    raise FileNotFoundError("caminho quebrado, nada a ver com o assert esperado")
# → XFAIL (not ERROR)
```

Concretely, if `tests/fixtures/snapshot_bancos_2026-07-12.yaml` is ever moved/renamed, if
`carregar_snapshot`/`carregar_fair_values` raise on a schema change, or if a future edit
to `rodar_cesta`/`report.analisar_acao` introduces an unrelated `KeyError`/`TypeError`,
the test still shows green `XFAIL` — silently masking an infrastructure break that has
nothing to do with the documented D-12 finding. This directly undermines the "tripwire"
property the docstring advertises ("quando a Fase 4 recalibrar ... vira XPASS→FAIL,
forçando a remoção do marcador") — the tripwire is supposed to catch the *specific*
condition being tracked, not accidentally suppress everything else too.

**Fix:**
```python
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "D-12: cesta 1/4 na banda ±15% (só ITUB4) < quórum 3/4 — ..."
    ),
)
def test_backtest_gate_quorum_e_anotacao():
    ...
```
This restricts the "expected failure" to the actual quorum/annotation `assert`s. Any
other exception (broken fixture path, YAML error, regression elsewhere in the call chain)
will now surface as a real `ERROR`, not a silent `XFAIL`.

### WR-02: `rodar_cesta` mutates the caller's `cfg` dict despite being documented and named as "PURA"

**File:** `src/analista/backtest.py:104-117`
**Issue:** The module docstring (lines 1-16) and the function docstring both call
`rodar_cesta` "PURA (sem I/O, sem rede)", but it mutates the `cfg` argument in place:

```python
cfg.setdefault("capm", {})
cfg["capm"]["rf_local"] = rf_local
```

This is safe *today* only because every current caller (`scripts/backtest_bancos.py`'s
`main()`, and `tests/test_backtest_bancos.py::_cfg()`) loads a brand-new `cfg` dict from
`config.yaml` immediately before calling `rodar_cesta`, so there's no aliasing across
calls. But nothing in the function signature or type hints prevents a future caller from
reusing/sharing one `cfg` object across multiple `rodar_cesta` invocations (e.g. a future
extension that loops over several frozen snapshots with different `rf_local` values in
the same process) — that caller would silently get the wrong `rf_local` in a shared
dict, and the function's own "pura" claim would actively mislead them into not
suspecting the mutation.

**Fix:** Either make it genuinely pure (don't rely on the caller never reusing `cfg`):
```python
import copy
...
def rodar_cesta(empresas, fair_values, cfg, rf_local) -> List[dict]:
    cfg = copy.deepcopy(cfg)
    cfg.setdefault("capm", {})
    cfg["capm"]["rf_local"] = rf_local
    ...
```
or, if the in-place mutation is intentional for performance reasons, drop the "PURA"
claim from the docstrings and explicitly document the side effect on `cfg` as part of the
function's contract.

## Info

### IN-01: Capture script's guard-corpo doesn't validate `dpa_trailing_12m`

**File:** `scripts/capturar_snapshot_bancos.py:96-112`
**Issue:** The guard-corpo explicitly fails the capture if `preco_atual`, `beta`, or any
of `SERIES_OBRIGATORIAS` come back empty/`None`, but says nothing about
`dpa_trailing_12m`, which is also written unconditionally into the fixture
(`entrada["dpa_trailing_12m"] = _f(c.dpa_trailing_12m)`, line 84) and is consumed by
`report.analisar_acao`'s `dy_atual()` (display multiple). If a future re-run of this
script hits a ticker where Yahoo doesn't expose trailing dividends, the snapshot would
silently freeze `dpa_trailing_12m: null` instead of failing loud like the other
guard-railed fields — a small inconsistency with the script's own stated philosophy
("guarda-corpo ... nunca fabricar valores", per `05-01-SUMMARY.md`).
**Fix:** Add `dpa_trailing_12m` to the guard-corpo loop (or explicitly document that it's
allowed to degrade to `None` because it's display-only and not RIM-critical).

### IN-02: `int(ano)`/`float(valor)` re-casts in `carregar_snapshot` are redundant but harmless

**File:** `src/analista/backtest.py:64, 73`
**Issue:** `anos=[int(a) for a in dados.get("anos", [])]` and
`destino[int(ano)] = float(valor)` re-cast values that `yaml.safe_load` already parses as
native `int`/`float` (the fixture was dumped with native Python ints/floats via
`capturar_snapshot_bancos.py`'s own `_f`/`_serie` helpers). Not a bug, just dead
defensiveness that adds noise; harmless if the fixture is ever hand-edited with quoted
numeric strings, so not worth removing, but not worth flagging as a real risk either.
**Fix:** None required — leave as defensive coding if intentional, otherwise a
no-op cleanup.

### IN-03: Gate docstring overstates the auto-tripwire condition

**File:** `tests/test_backtest_bancos.py:19-20, 89-93`
**Issue:** The module and decorator docstrings say "quando a Fase 4 recalibrar e a cesta
cruzar o quórum, este teste vira XPASS→FAIL". That's only true if recalibration
*simultaneously* results in the ≤1 remaining failing ticker having an `excecao_nota` set
in `fair_values_bancos.yaml` — reaching `QUORUM_MIN=3` alone still leaves the second
`assert` (`for r in falhas: assert r["excecao_nota"]`) able to fail, keeping the test in
a "still failing" (still `XFAIL`) state even though the headline quorum condition the
docstring describes was met. This is arguably the *correct* behavior per D-08 (an
undocumented deviation must not silently pass), but the docstring's phrasing implies
quorum alone flips the tripwire, which could cause a future engineer recalibrating Phase
4 to be confused when the suite stays green (`XFAIL`) instead of turning red (`XPASS`)
as expected.
**Fix:** Tighten the docstring wording, e.g.: "...vira XPASS→FAIL quando a cesta cruzar o
quórum **e** a falha remanescente (se houver) estiver anotada via `excecao_nota` — ambas
condições precisam ser satisfeitas simultaneamente."

---

_Reviewed: 2026-07-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
