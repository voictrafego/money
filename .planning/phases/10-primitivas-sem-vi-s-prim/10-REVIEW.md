---
phase: 10-primitivas-sem-vi-s-prim
reviewed: 2026-07-16T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - src/analista/core/normalizacao.py
  - src/analista/core/fundamentals.py
  - src/analista/core/arquetipo.py
  - src/analista/core/screening.py
  - src/analista/core/motores.py
  - src/analista/report/report.py
  - src/analista/ingest/macro.py
  - src/analista/backtest.py
  - src/analista/cli.py
  - app.py
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-07-16
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Reviewed the phase-10 numeric-primitive changes: the Theil-Sen endpoint estimator
split (`base_normalizada` vs `media_ciclo`), the `roe_valuation`=median /
`roe_qualidade_atual`=endpoint signal split, the now-raw `serie_lucro_normalizada`,
and the IPCA deflation of the cyclical motor (`macro._compor_deflatores` +
report `_intrinseco_por_motor` "normalizado" branch + entry-point stamping in
cli/app/backtest).

The core math is sound. The Theil-Sen window (`x = arange(n)`, endpoint at `n-1`)
is correct, the N=0/1/2 ladders are complete, and the deflator composition
(`prod(1+ipca[y])` for `y in ano+1..T`, `defl[T]=1.0`) brings each year to reais
of the last year in the right direction. Negative endpoints, missing IPCA keys, and
empty series are handled without raising. The deflation is confined to the cyclical
motor and does not perturb the `*_valuation()` numbers shared by Analisar / Garimpo /
Ranking, so the primary cross-mode surface is preserved.

No blockers found. Three warnings concern (1) a documented invariant the endpoint
guard does not actually enforce, (2) an unnormalized snapshot key type that diverges
from every sibling series and can silently zero the cyclical motor, and (3) a
newly-introduced cross-mode gap where the CLI `rank` surface runs `analisar_acao`
without stamping the deflators that Analisar stamps. Two info items note latent
shared-state and window-truncation edges.

## Warnings

### WR-01: `base_normalizada` endpoint guard can still return a negative base — violates its own documented invariant

**File:** `src/analista/core/normalizacao.py:93-94`
**Issue:** The degeneration guard is `if endpoint <= 0: return float(median(janela))`.
The docstring (lines 22, 75-77) promises this "nunca devolve base negativa que
quebraria RIM/DCF a jusante." But `median(janela)` is itself negative whenever the
window is majority-negative (e.g. `janela = [-5, -3, -1]` → endpoint ≤ 0 → median =
-3). The negative base then flows into `lpa_valuation`, `margem_valuation`
(numerator) and `roe_qualidade_atual` with no non-negativity clamp. Downstream
consumers do not crash (Gordon/DCF degrade and the report guards `intrinseco <= 0`),
but `margem_valuation` feeds the Ranking normalization and a negative ML can misplace
the ticker. The guard does not deliver the invariant it claims.
**Fix:** Either make the fallback honor the stated invariant, e.g.:
```python
if endpoint <= 0:
    m = float(median(janela))
    return m if m > 0 else None   # never leak a negative valuation base
```
or correct the docstring to state that a genuinely loss-making window yields a
negative base by design (and confirm each consumer tolerates it). Do not leave the
code and the promised invariant contradicting each other.

### WR-02: `carregar_snapshot` loads `ipca_deflatores` without int-key normalization, unlike every sibling series — silent cyclical-motor wipeout on string keys

**File:** `src/analista/backtest.py:58` (and consumed at `src/analista/report/report.py:264-270`)
**Issue:** Every annual series in `carregar_snapshot` is defensively re-keyed with
`destino[int(ano)] = float(valor)` (backtest.py:74-75) precisely because a
serialized snapshot can round-trip year keys as strings. The new global carimbo is
loaded as `ipca_deflatores = snap.get("ipca_deflatores") or {}` with no key
normalization. In the consumer, `_intrinseco_por_motor` filters with
`if an in c.lucro_liquido and an in defl`, where `an` is an `int` from
`anos_ordenados()`. If the snapshot ever carries string year keys (`"2020"`), then
`2020 in {"2020": ...}` is `False` for every year → `serie_lucro` becomes `[]` →
`media_ciclo([])` → `None` → the cyclical motor silently yields no valuation, while
the `if defl:` branch is still taken (dict is non-empty). The current bank snapshot
omits the key so this path is untested; the deflation tests only use in-memory int
keys and never round-trip through YAML.
**Fix:** Normalize keys on load, mirroring the sibling series:
```python
_defl_raw = snap.get("ipca_deflatores") or {}
ipca_deflatores = {int(ano): float(fator) for ano, fator in _defl_raw.items()}
```

### WR-03: CLI `rank` runs `analisar_acao` without stamping `ipca_deflatores` — cyclical ensemble/divergence disagrees with Analisar

**File:** `src/analista/cli.py:188` (contrast with the stamping at `src/analista/cli.py:83-86`)
**Issue:** `cmd_analyze` stamps `cfg["macro"]["ipca_deflatores"]` before calling
`analisar_acao`, but `cmd_rank` calls `report.analisar_acao(c, cfg)` with the config
as-is (no deflators, no fresh `rf_local`). For a cyclical ticker this means the
`ensemble_mid` / divergence signal printed by `rank` is computed on the *nominal*
lucro series, while Analisar computes the cyclical intrinsic on the *deflated* series
— the same ticker shows different `vmin/vmax` mid and possibly a different
"divergência entre lentes" verdict across the two surfaces. Cross-mode consistency is
the stated Core Value. (The `rf_local` half of this gap predates phase 10 and this
review does not re-open it; the deflator omission is newly introduced by this phase
and is what should be closed.)
**Fix:** Stamp the deflators in `cmd_rank` exactly as `cmd_analyze` does, once before
the ticker loop:
```python
cfg["macro"] = {
    **cfg.get("macro", {}),
    "ipca_deflatores": macro.ipca_deflatores_anuais(cfg["capm"].get("rf_ciclo_anos", 10)),
}
```
(Consider also aligning `rf_local` here so the CLI `rank` second lens matches
Analisar entirely.)

## Info

### IN-01: `app.py` mutates the module-global `CFG["macro"]` in the Analisar branch (shared state)

**File:** `app.py:879-882`
**Issue:** The deflator stamp assigns `CFG["macro"] = {**CFG.get("macro", {}), ...}`
on the module-global `CFG`. It is re-stamped idempotently on each Analisar run and no
other mode reads `cfg["macro"]["ipca_deflatores"]`, so it is harmless today. But it is
a persistent shared-state mutation: after an Analisar run the deflators linger in
`CFG` for any subsequent mode. If a future surface (Garimpar/Ranking) starts calling
`analisar_acao` for cyclicals, it would silently inherit stale deflators from the last
Analisar run.
**Fix:** Prefer passing a per-run copy to `analisar_acao` (as `backtest.rodar_cesta`
does with `cfg = {**cfg, "macro": {...}}`) rather than mutating the shared `CFG`.

### IN-02: Deflated cyclical series silently drops company years outside the IPCA 10y window

**File:** `src/analista/report/report.py:264-270` (window origin `src/analista/ingest/macro.py:119`)
**Issue:** The deflated branch keeps only years with `an in defl`. `_ipca_anual_dezembro`
fetches `anos*365` days back, so the oldest company year can fall just outside the
window and be dropped, making the deflated through-cycle sample shorter than the
nominal one for the same ticker — without any notice to the user. It never raises
(shorter list still averages), and the recent-year side is safe (December IPCA for
year Y publishes before that year's DFP, so `ult <= T` in practice), but the sample
asymmetry between the deflated and nominal paths is silent.
**Fix:** No action required for correctness; if precision matters, widen the IPCA fetch
window slightly (e.g. `anos+1`) so the full lucro window is always covered, or log when
a lucro year is dropped for lacking a deflator.

---

_Reviewed: 2026-07-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
