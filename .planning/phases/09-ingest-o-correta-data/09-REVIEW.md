---
phase: 09-ingest-o-correta-data
reviewed: 2026-07-15T00:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - src/analista/ingest/cvm.py
  - src/analista/ingest/build.py
  - src/analista/ingest/prices.py
  - src/analista/glossario.py
  - src/analista/report/presentation.py
  - scripts/capturar_snapshot_limpo.py
  - scripts/spike_data04_degrau_split.py
  - tests/test_cvm_distribuicoes.py
  - tests/test_dy_base.py
  - tests/test_ingest_split.py
  - tests/test_sanidade_baseline.py
  - tests/test_sanidade_insumos.py
  - tests/helpers_sanidade.py
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 9: Code Review Report

**Reviewed:** 2026-07-15
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Reviewed the Phase 09 (DATA) ingestion rewrite: CVM proventos broad-filter, controller-base
promotion, official share-count sourcing with per-year and series-internal scale detection, the
split-firewall regression guard, the DY-base declaration, and the clean-snapshot capture/ruler.

No crashes or security issues were found — the never-raise design (guarded `try/except`,
`.get()` on stubs, `None`-tolerant formatting) holds up. However, several **latent correctness
risks touch the project's core value** (num_acoes / c.dividendos fidelity). The strongest are: an
over-broad JCP regex that now feeds `c.dividendos` directly, and two scale-detection routines whose
power-of-1000 heuristic mis-classifies genuine >31.6× corporate variation — one of which can
silently *divide real share counts by 1000* for anchorless tickers. None are proven to fire on the
current 104-ticker universe (the suite is green), so they are classified WARNING, but each can
silently produce a wrong per-share number, which is exactly the disease this phase set out to cure.

## Warnings

### WR-01: Over-broad JCP regex can over-count `c.dividendos`

**File:** `src/analista/ingest/cvm.py:292`
**Issue:** `_distribuicoes_proventos_amplo` matches inclusion with
`"dividendo|juros sobre.*capital"`. The `.*` between "juros sobre" and "capital" matches ANY
financing-section (6.03.*) line that contains both tokens — e.g. "Juros pagos sobre capital de
giro", "Juros sobre capital de terceiros", "Juros sobre empréstimos ... capital". JCP is
specifically "juros sobre o capital **próprio**". Since DATA-01 promoted this broad filter to the
source of `c.dividendos` (build.py:234), a false match silently inflates the proventos total →
overstates payout → distorts the DDM. This is the core-value invariant ("números fiéis") and the
match runs against the raw CVM `DS_CONTA` text with no `capital próprio` anchor.
**Fix:**
```python
incluir = ds.str.contains(r"dividendo|juros sobre.*capital proprio", na=False, regex=True)
```
(`ds` is already NFKD-normalized/ascii-folded by `_norm`, so "próprio" → "proprio".)

### WR-02: Scale heuristic mis-classifies genuine 31.6×–316× share growth as a unit change

**File:** `src/analista/ingest/build.py:79`
**Issue:** `expoente = round(math.log10(implied / cru) / 3.0)` crosses from 0 to 1 when
`implied/cru ≥ 10**1.5 ≈ 31.62`, not at 1000×. So any year whose real raw count is between 1/31.6
and 1/316 of the current `implied` (i.e. genuine 31.6×–316× share growth over the window) gets a
spurious `× 1000`. The docstring's justification — "Variação societária REAL … é sempre < 1000× —
logo nunca é confundida com troca de unidade" — is **mathematically wrong**: the confusion
threshold is the rounding boundary (~31.6×), not 1000×. The `max(0, expoente)` guard prevents
shrinkage but not this spurious inflation.
**Fix:** Only treat a ratio as a unit change when it is *close to* an exact power of 1000, e.g.
require the residual to be near-integer before applying:
```python
raw_exp = math.log10(implied / cru) / 3.0
expoente = round(raw_exp)
# só corrige se o desvio à potência de 1000 for pequeno (troca de unidade real),
# senão deixa cru intacto (variação societária real fica visível ao SAN)
if abs(raw_exp - expoente) > 0.15:
    expoente = 0
escalado[ano] = cru * (1000 ** max(0, expoente))
```

### WR-03: `_alinhar_escala_interna` can silently DIVIDE real share counts by 1000

**File:** `src/analista/ingest/build.py:102-113`
**Issue:** For anchorless tickers (`implied` None — ELET3/ELET6/IGTI11), the band is
`round(log10(v)/3)` per year and each year is pulled to the reference band by
`v / 1000 ** (bandas[a] - ref)`. Unlike `_escala_por_ano` (which has a `max(0, expoente)` no-shrink
guard), this path **can shrink**: if a year's real count genuinely differs from the reference band
by ≥ ~31.6× (band delta ≥ 1), that year is divided by 1000, destroying real shares → wrong
num_acoes → wrong LPA/payout/DDM. The docstring claims "Variação corporativa REAL … sobrevive", but
a real 31.6×–316× jump shifts the band and IS mis-corrected. This reintroduces the dispersion
disease the phase set out to cure, for the anchorless subset.
**Fix:** Add the same no-shrink protection as `_escala_por_ano`, or gate the correction on the
band delta being an exact-power-of-1000 (residual near integer) before dividing; never apply a
band delta > 0 downward without confirming it is a unit change and not real growth.

### WR-04: DATA-03 silently self-disables if `cad_cia_aberta.csv` is absent

**File:** `src/analista/ingest/cvm.py:116-118`
**Issue:** `_mapa_cnpj_por_cd_cvm` reads `cad_cia_aberta.csv` from `CACHE_DIR` but nothing in this
module ever downloads it (only `baixar_dfp` fetches the DFP zips). On a fresh clone where that file
is missing, the map is `{}` → `contagem_oficial_do_ano` returns `None` for **every** ticker →
`build` falls back to `impliedSharesOutstanding` for the entire universe, silently retiring the
DATA-03 official-count fix with no log, warning, or SAN flag. Given the core value ("números
fiéis"), a wholesale silent fallback to a different num_acoes source should not be invisible.
**Fix:** Either ensure the cadastro is fetched (like the DFP zips) or emit an observable signal
(log / a SAN diagnostic) when the CNPJ map comes back empty, so the fallback is not silent.

### WR-05: `_composicao_capital` is not filtered by `ORDEM_EXERC`

**File:** `src/analista/ingest/cvm.py:130-149`, `152-184`
**Issue:** `_ler_demonstracao` filters `ORDEM_EXERC == "ÚLTIMO"` (cvm.py:105-106) to keep only the
current exercise, but `_composicao_capital` applies no such filter. `contagem_oficial_do_ano` then
relies solely on the `DT_REFER`/`VERSAO` sort + `iloc[-1]` to disambiguate. If the file carries
prior-period ("PENÚLTIMO") rows or multiple rows per `DT_REFER`, the last-row pick is fragile and
could select an unintended row (wrong share count) rather than failing loudly.
**Fix:** Filter `ORDEM_EXERC == "ÚLTIMO"` in `_composicao_capital` mirroring `_ler_demonstracao`,
so the disambiguation isn't load-bearing.

## Info

### IN-01: `VERSAO` tie-break may sort lexicographically

**File:** `src/analista/ingest/cvm.py:174-177`
**Issue:** `_composicao_capital` reads with no `dtype`, so if `VERSAO` is inferred as string,
`sort_values(["DT_REFER", "VERSAO"])` orders "10" before "2" — picking a lower version. Versions
rarely exceed 9 so impact is small, but it is not guaranteed. **Fix:** cast `VERSAO` to numeric
before sorting, or read it with `dtype={"VERSAO": "Int64"}`.

### IN-02: `_mapa_cnpj_por_cd_cvm` does not guard NaN CNPJ

**File:** `src/analista/ingest/cvm.py:124-126`
**Issue:** The loop checks `pd.notna(cd)` but not `pd.notna(cnpj)`, so a row with a valid CD_CVM
and a missing CNPJ maps `cd → NaN`. Downstream `df["CNPJ_CIA"] == NaN` matches nothing → `None`
(harmless fallback), but it silently masks a bad cadastro row. **Fix:** also require
`pd.notna(cnpj)` before inserting.

### IN-03: Unguarded `.iloc[-126]` on possibly-NaN adjusted series

**File:** `src/analista/ingest/prices.py:211-212`
**Issue:** `ajustado.iloc[-1] / ajustado.iloc[-126]` uses `hist["Adj Close"]` without `dropna()`;
a NaN at either end yields a NaN `desempenho_relativo_6m`. Low impact (diagnostic proxy) but
inconsistent with the `dropna()` applied to `serie_precos`. **Fix:** `dropna()` before indexing.

### IN-04: Spike relies on relative `sys.path` and CWD

**File:** `scripts/spike_data04_degrau_split.py:18`
**Issue:** `sys.path.insert(0, "src")` only resolves when run from the repo root, unlike
`capturar_snapshot_limpo.py` which computes `ROOT` from `__file__`. It is a throwaway spike, so
this is cosmetic. **Fix:** mirror the `ROOT = os.path.dirname(...)` pattern for robustness.

---

_Reviewed: 2026-07-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
