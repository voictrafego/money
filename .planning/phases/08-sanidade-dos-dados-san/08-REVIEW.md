---
phase: 08-sanidade-dos-dados-san
reviewed: 2026-07-15T00:43:25Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - src/analista/core/sanidade.py
  - src/analista/core/fundamentals.py
  - src/analista/ingest/build.py
  - src/analista/ingest/cvm.py
  - src/analista/ingest/prices.py
  - scripts/capturar_snapshot_sujo.py
  - scripts/gerar_baseline_sanidade.py
  - scripts/relatorio_sanidade.py
  - scripts/spike_san07_bancos.py
  - tests/helpers_sanidade.py
  - tests/test_sanidade_checks.py
  - tests/test_sanidade_insumos.py
  - tests/test_sanidade_limiares.py
  - tests/test_sanidade_pipeline.py
  - tests/test_sanidade_snapshot.py
  - tests/test_sanidade_baseline.py
findings:
  critical: 0
  warning: 1
  info: 3
  total: 4
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-07-15T00:43:25Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Phase 08 "Sanidade dos Dados" adds five pure arithmetic checks (SAN-01..SAN-05) over
`CompanyData`, a never-raise synthesis (`aplicar_sanidade`, SAN-06), diagnostic insumos in
the CVM/Yahoo ingestion layer, a frozen 104-ticker snapshot, a detection baseline, and a set
of contract/invariant tests.

I reviewed with the explicit Phase-08 design intent in mind: the checks are supposed to
*detect and report* dirty data (flagging ~62 tickers is correct behavior, the Phase-9
regression baseline), must never raise (degrade to warnings + lowered confidence), and the
detection thresholds intentionally live outside `calibracao.lock.yaml`. I did **not** flag any
of those as defects.

I traced the five checks against their docstrings and edge cases (empty series, zero/negative
denominators, sign-inverted ratios, missing market data, unit-factor fallback, source-boundary
skips, split exemption). The threshold directions, symmetry, `abs()` denominators, and the
`_bucket` never-raise guard are all internally consistent with the stated contract, and the
`try/except`-per-check structure makes `aplicar_sanidade` structurally non-raising. **No
correctness or security BLOCKER was found in the pipeline.**

The findings below are one real crash path in a standalone diagnostic script and three
minor quality items.

## Warnings

### WR-01: `spike_san07_bancos.py` crashes when a bank has no OCI (4.02) line

**File:** `scripts/spike_san07_bancos.py:168` and `scripts/spike_san07_bancos.py:169`
**Issue:** `oci_pl_pct` (i.e. `razao`) is `None` whenever `oci_v is None` (missing DRA line
`4.02`) or `vl_pl == 0` (line 143). The per-bank print at line 168 formats it unconditionally:

```python
print(f"  {r['ticker']}: OCI/PL = {r['oci_pl_pct']:.2f} %")
```

`f"{None:.2f}"` raises `TypeError: unsupported format string passed to NoneType.__format__`,
crashing the whole spike. Line 169 has the sibling problem:

```python
pior = max(abs(r["oci_pl_pct"]) for r in resultados if r["oci_pl_pct"] is not None)
```

If *every* bank yields `None`, the generator is empty and `max()` raises `ValueError: max()
arg is an empty sequence`. Note the code already guards `None` correctly at the earlier prints
(lines 145–150 use `... if v is not None else "(ausente)"`), so the veredito block at 168–169
is an inconsistent omission of the same guard. This is a diagnostic script over a fixed offline
cache, so impact is limited — but it fails loudly on exactly the "no data" case the script is
meant to survive.
**Fix:**
```python
for r in resultados:
    pct = r["oci_pl_pct"]
    print(f"  {r['ticker']}: OCI/PL = " + (f"{pct:.2f} %" if pct is not None else "(indisponível)"))
validos = [abs(r["oci_pl_pct"]) for r in resultados if r["oci_pl_pct"] is not None]
if validos:
    pior = max(validos)
    print(f"  -> NÃO — o maior |OCI/PL| é {pior:.2f} % do PL/ano; contra o clean surplus, é ruído.")
else:
    print("  -> OCI/PL indisponível para todos os bancos (sem linha 4.02 na DRA).")
```

## Info

### IN-01: Unused import `List` in `build.py`

**File:** `src/analista/ingest/build.py:11`
**Issue:** `from typing import Dict, List, Optional` — `List` is never referenced (annotations
use `Dict[...]`, `Optional[...]` and the builtin `list(range(...))`).
**Fix:** `from typing import Dict, Optional`.

### IN-02: `_fator_unit` computes an upper-middle element, not a true median

**File:** `src/analista/ingest/build.py:36-38`
**Issue:** The docstring says "usamos a mediana das razões anuais, arredondada", but the code
takes `razoes[len(razoes) // 2]`, which for an even number of ratios returns the upper of the
two middle elements (not their average). Because the result is `round()`ed to a small integer
unit factor (3, 5, …) that is stable across years, this practically never changes the outcome —
but the comment overstates what the code does.
**Fix:** Use `statistics.median` (already imported elsewhere in the codebase pattern) or update
the comment to "elemento central superior das razões anuais, arredondado". Also note
`round(2.5) == 2` (banker's rounding) at exact `.5` boundaries — irrelevant for real unit
factors, but worth a one-line comment if precision ever matters.

### IN-03: Redundant re-application of `aplicar_sanidade` in the CLI/baseline scripts

**File:** `scripts/relatorio_sanidade.py:158-159` (and `scripts/gerar_baseline_sanidade.py:73`)
**Issue:** In `--ao-vivo` mode, `build.montar_empresa` already calls `aplicar_sanidade(c)`
internally (`build.py:142`); `relatorio_sanidade.main` then calls it again on every company at
lines 158–159. It is harmless because `aplicar_sanidade` resets `c.avisos` and is idempotent,
but the double pass is dead work and obscures which call produces the reported state.
**Fix:** Skip the re-application for companies produced by `_empresas_ao_vivo` (they are already
sanitized), or document that the loop exists to sanitize the `--snapshot` path (whose companies
arrive `nao_avaliada`) and gate it accordingly.

---

_Reviewed: 2026-07-15T00:43:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
