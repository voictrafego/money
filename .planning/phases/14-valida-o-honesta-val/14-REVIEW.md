---
phase: 14-valida-o-honesta-val
reviewed: 2026-07-20T16:48:26Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - scripts/backtest_bancos.py
  - scripts/montar_cesta_holdout.py
  - src/analista/backtest.py
  - tests/classificacao.yaml
  - tests/fixtures/holdout_v24.yaml
  - tests/helpers_blindagem.py
  - tests/test_backtest_bancos.py
  - tests/test_blindagem_meta.py
  - tests/test_holdout_cesta.py
  - tests/test_holdout_ordem_git.py
  - tests/test_soberano_itub4.py
findings:
  critical: 0
  warning: 5
  info: 2
  total: 7
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-07-20T16:48:26Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Phase 14 (VAL) is the honest-validation phase of v2.4. I reviewed the basket montador, the
BACKTEST-01 harness, the jackknife statistics, and the four gate tests, with special attention to
the three load-bearing mechanisms flagged by the orchestrator: judge determinism, the Monte-Carlo
null derivation of `LIMIAR_JACKKNIFE_PP`, the git-order proof, and basket-rebuild determinism.

The core statistical machinery is sound. `LIMIAR_JACKKNIFE_PP(n)` derives the threshold purely from
`n` plus four pre-registered literals (seed `20260720`, `sigma=0.35`, `M=10_000`, `pct=95`) and never
touches real data — the anti-overfit invariant holds. The MAD-normalized jackknife statistic is
scale-invariant as claimed. I ran the phase-14 tests: all 16 pass, and the two verdicts that were
designed to *skip* until the substrate existed (`test_nenhum_ticker_e_load_bearing`,
`test_holdout_ordem_por_git`) now genuinely **run** against the committed fixture (observed margin:
`desvio_norm=0.0579` vs `limiar=0.1640`).

No BLOCKER-class correctness/security/data-loss defect is provable. However, several real weaknesses
let the validation lose enforcement or reproducibility silently — the exact failure mode this phase
exists to prevent. The most important are the git-order proof failing *open* (skip) in a default
shallow CI checkout (WR-01), non-determinism from `date.today()` baked into the fixture (WR-02), and
duplicate share classes blunting the jackknife's leave-one-out power (WR-03).

## Warnings

### WR-01: git-order proof (the "coração da fase") fails open on shallow clone / no-git

**File:** `tests/test_holdout_ordem_git.py:47-55, 82-94`
**Issue:** The D-09 ordering proof (`fair_value` committed strictly before `v_modelo`) is the
load-bearing anti-circularity guarantee of the phase. But the test `skip`s whenever the repo is
shallow, and `_is_shallow()` returns `True` on **any** exception (no git, git error). The standard CI
checkout (`actions/checkout` with default `fetch-depth: 1`) is shallow, so in default automation this
proof never executes — it silently reports green. A squashed/tampered fixture (all lines one
timestamp) would sail through CI. The guarantee is effectively local-only unless every CI job
remembers to set `fetch-depth: 0`. Per the project's own lesson ("guarda só vale se for provada por
execução"), a proof that skips in the environment that gates merges is a phantom guard.
**Fix:** Make the enforcement environment explicit. Either (a) require `fetch-depth: 0` in CI and add
a test that *fails* (not skips) when running under CI with a shallow clone (detect e.g. `CI=true`
env), or (b) unshallow on demand before blaming:
```python
if _is_shallow():
    if os.environ.get("CI"):
        pytest.fail("D-09 order proof cannot run on a shallow CI clone — set fetch-depth: 0")
    pytest.skip("shallow local clone; run with full history to enforce D-09")
```

### WR-02: `date.today()` baked into the fixture breaks byte-reproducibility (contradicts the docstring)

**File:** `scripts/montar_cesta_holdout.py:241, 257, 272, 308`
**Issue:** `montar()` stamps `datetime.date.today().isoformat()` into every ticker's `data:` field and
`_emitir_yaml()` stamps it again into the header, yet the module docstring calls the montador
"determinístico" and "reproduzível". Re-running `--fair-value-only` on any other calendar day produces
a byte-different fixture even though the `fair_value` numbers are unchanged. Worse for D-09: because
`montar()` rewrites the **entire** file (not surgically), a re-run after `v_modelo` was filled would
reassign the git-blame author-time of every `fair_value` line to the new commit — silently
evaporating the very order proof of WR-01. The two independent `today()` calls (line 241 vs 272) can
also disagree across a midnight boundary within one run.
**Fix:** Freeze the date from the snapshot capture date (already available as the snapshot filename /
its `data_base`) instead of wall-clock `today()`, so the montador is a pure function of the frozen
snapshot:
```python
data_base = _data_base_do_snapshot()  # derived from the frozen snapshot, not today()
```
and document that `montar()` overwrites the whole file — so it must never be re-run after Commit 2.

### WR-03: duplicate share classes blunt the jackknife's leave-one-out power

**File:** `scripts/montar_cesta_holdout.py:140-259`; `tests/fixtures/holdout_v24.yaml` (PETR3/PETR4,
ITUB3/ITUB4, BBDC3/BBDC4)
**Issue:** The basket contains both ON and PN classes of the same issuer, each with **identical**
`fair_value` and `v_modelo` (ratios coincide exactly). The jackknife (`mediana_jackknife`) is a
leave-**one**-out: if an issuer were load-bearing, removing one of its two tickers leaves the twin in
place and the median barely moves, so the gate cannot see it. This directly undercuts the phase's
stated purpose (detecting a ticker/issuer the calibration is propped on). I verified it does not flip
the current verdict (deduped by issuer the test still passes with a *larger* margin), so this is a
power/robustness gap, not a wrong verdict today — but it is a way the gate could silently pass a
future load-bearing issuer.
**Fix:** Either collapse duplicate share classes to one row per issuer before the jackknife, or
document explicitly that co-listed classes are intentionally kept and add a leave-issuer-out variant:
```python
# dedupe by issuer root (first 4 letters) before feeding the jackknife
por_issuer = {}
for tk, r in razoes.items():
    por_issuer.setdefault(tk[:4], []).append(r)
razoes_dedup = [statistics.mean(v) for v in por_issuer.values()]
```

### WR-04: file handles leaked — `open()` without a context manager

**File:** `scripts/montar_cesta_holdout.py:313, 409`
**Issue:** `dados = open(hs.CAMINHO_SNAPSHOT_LIMPO, "rb").read()` and
`texto_atual = open(CAMINHO_FIXTURE, "r", encoding="utf-8").read()` leave the file objects open (CG
closes them eventually, but the pattern is exactly the "missing `with` for file operations" the
Python guidance flags; the rest of the file and `backtest.py` correctly use `with`).
**Fix:**
```python
with open(hs.CAMINHO_SNAPSHOT_LIMPO, "rb") as fh:
    dados = fh.read()
```

### WR-05: `--fair-value-only` default=True inside a mutually-exclusive group is a permanently-stuck flag

**File:** `scripts/montar_cesta_holdout.py:392-395`
**Issue:** `add_argument("--fair-value-only", action="store_true", default=True)` means
`args.fair_value_only` is **always** `True` and can never be turned off — even when `--fill-v-modelo`
is passed. Harmless today because `main()` only branches on `args.fill_v_modelo`, but it is a latent
trap: any future `if args.fair_value_only:` branch would misfire during a Commit-2 run.
**Fix:** Drop `default=True` and derive the default behaviour from the absence of `--fill-v-modelo`:
```python
modo.add_argument("--fair-value-only", action="store_true",
                  help="COMMIT 1: emite só fair_value (default se --fill-v-modelo ausente).")
...
if not args.fill_v_modelo:  # fair-value-only is the default path
```

## Info

### IN-01: truthiness filter silently drops a ticker whose `v_modelo`/`fair_value` rounds to 0.00

**File:** `tests/test_blindagem_meta.py:203-207`
**Issue:** `if d.get("v_modelo") and d.get("fair_value")` uses truthiness. A legitimately tiny but
positive value serialized as `"0.00"` (fixture formats with `%.2f`) parses to `0.0`, which is falsy
and is dropped from the jackknife with no signal. Not triggered by the current fixture (smallest
`fair_value` is `0.72`), but it is a silent-exclusion path in the substrate that this phase exists to
keep honest.
**Fix:** Filter on presence/positivity explicitly: `if "v_modelo" in d and "fair_value" in d and
float(d["fair_value"]) > 0`.

### IN-02: `_pb_ratio == 0.0` is swallowed by the `or 9e9` guard

**File:** `scripts/montar_cesta_holdout.py:188-191`
**Issue:** `(_pb_ratio(...) or 9e9) < 1.0` treats a genuine `P/B == 0.0` (price 0) the same as
`None`, excluding it from the P/B bucket. An edge case (needs `preco_atual == 0`), but the `or`
conflates "undefined" with "zero". Prefer an explicit `is not None` test to keep the bucket rule
literal.
**Fix:** `pb = _pb_ratio(universo[tk][0]); if pb is not None and pb < 1.0`.

---

_Reviewed: 2026-07-20T16:48:26Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
