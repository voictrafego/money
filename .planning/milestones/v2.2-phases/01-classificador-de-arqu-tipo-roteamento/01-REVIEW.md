---
phase: 01-classificador-de-arqu-tipo-roteamento
reviewed: 2026-07-11T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - src/analista/core/arquetipo.py
  - src/analista/report/report.py
  - config.yaml
  - tests/test_arquetipo.py
  - tests/test_arquetipo_roteamento.py
  - tests/test_consistencia_modos.py
  - tests/test_selo.py
  - tests/test_guardrails_fix06.py
findings:
  critical: 1
  warning: 4
  info: 2
  total: 7
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-07-11T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the new archetype classifier (`core/arquetipo.py`), its wiring into
`report.analisar_acao`, the `config.yaml` `arquetipo:` block, and the five golden
suites. The 37 tests pass, but green tests mask two real routing defects that the
module's own docstring says it exists to prevent.

The central finding (CR-01) is structural, not cosmetic: the cyclicality signal is the
coefficient of variation of the **raw earnings level**, which is dominated by the growth
trend for any strongly-growing company. A textbook compounder (the exact `crescimento`
archetype the module advertises) is therefore misrouted to `ciclica` and flagged
`fronteiriço`. The existing growth test only uses 3%/yr growth, which stays under the
threshold and hides the problem — a 20%/yr compounder crosses it (reproduced below).

Secondary concerns center on config-driven "mandatory" guards that silently disable when
the config block is absent, and a couple of contract/message inconsistencies. None of the
selo/guardrail/consistency suites changed behavior that I could fault; those files are
sound.

## Critical Issues

### CR-01: Cyclicality signal (CV of raw earnings level) misroutes compounders to `ciclica`/`fronteiriço`

**File:** `src/analista/core/arquetipo.py:58-69` (`_cv_lucro`) and `:113` (threshold use)
**Issue:** `_cv_lucro` computes `pstdev(vals) / abs(mean(vals))` over the **raw** earnings
series. For a company with a strong upward trend, that dispersion is driven almost entirely
by the trend, not by oscillation — even though the docstring asserts "a oscilação É o sinal
de ciclicidade" (line 59). A clean compounder therefore trips `ciclica_cv_min` **and** the
`crescimento` rule (high ROE + high retention), producing a false conflict:

```
# reproduced against the shipped config.yaml
20% compounder -> chave= ciclica | fronteirico= True | candidatos= ['ciclica','crescimento']
  CV(raw lucro) = 0.509 (ciclica_cv_min=0.40)
  roe_val= 1.433  retencao= 0.8
```

This directly defeats the module's stated purpose ("ROE alto + retenção → compounder",
docstring lines 30-31): the primary `chave` returned is `ciclica` (arbitrary
`distintos[0]` ordering), and the archetype the header displays for an unambiguous growth
name is wrong. It is not a threshold-calibration issue deferred to BACKTEST-01 — raising
`ciclica_cv_min` to spare compounders would also blind the detector to genuine cyclicals,
because raw-level CV cannot separate "trends up" from "oscillates around a flat mean."
The existing golden `test_roe_alto_retencao_alta_vira_crescimento` uses only 3%/yr growth
(CV≈0.08), so it passes while the general case fails.

**Fix:** Detrend before measuring oscillation. Measure dispersion of the residuals around
the log-linear fit (the module already imports the concept elsewhere), or use the CV of
year-over-year growth rates, so a monotonic compounder scores low and a mean-reverting
cyclical scores high:

```python
def _cv_lucro(serie: list) -> Optional[float]:
    vals = [float(v) for v in serie if v is not None]
    if len(vals) < 3:
        return None
    # oscilação = dispersão dos retornos ano-a-ano, não do nível cru (que carrega a tendência)
    ret = [(b - a) / abs(a) for a, b in zip(vals, vals[1:]) if a != 0]
    if len(ret) < 2:
        return None
    m = mean(ret)
    # CV dos retornos: compounder (retornos ~constantes) → baixo; cíclico (retornos alternam sinal) → alto
    return pstdev(ret) / abs(m) if m != 0 else None
```

Add a golden with a fast (>=15%/yr) compounder asserting `chave == CRESCIMENTO` and
`fronteirico is False` to lock the regression.

## Warnings

### WR-01: "Mandatory" anti-Petróleo guard and financeira hard-route silently disable under absent config

**File:** `src/analista/core/arquetipo.py:89-90, 98, 102`
**Issue:** `financeiro_tokens` and `regulada_excluir_tokens` default to `[]`
(`arq.get(..., [])`). The docstring calls the anti-Petróleo guard "OBRIGATÓRIA" (lines
79-80), but with an empty/missing `arquetipo:` block both hard-routes vanish and every
company falls through to the quantitative refino. Reproduced:

```
bank, empty cfg                   -> crescimento          # should be financeira
petroleo concessionaria, empty cfg -> pagadora_regulada    # the ITUB4/Petrobras anti-pattern the guard prevents
```

`test_bloco_config_ausente_nao_quebra` masks this: it only asserts
`r.chave in ARQUETIPO_MOTOR`, so a misrouted bank still passes. Unlike the numeric
thresholds (which have sensible defaults 0.15/0.40/0.50), the safety-critical token lists
have no floor.
**Fix:** Give the token lists real defaults in code (mirroring the shipped config) instead
of `[]`, so the guard degrades safe rather than off:

```python
_FIN_DEFAULT = ["banco", "intermediação financeira", "seguradora", ...]
_REG_EXCL_DEFAULT = ["petróleo", "petroleo"]
financeiro_tokens = arq.get("financeiro_tokens", _FIN_DEFAULT)
regulada_excluir = arq.get("regulada_excluir_tokens", _REG_EXCL_DEFAULT)
```

Tighten the config-absent test to assert the bank still routes to `FINANCEIRA` and a
petróleo-concessionária does **not** route to `PAGADORA_REGULADA`.

### WR-02: `candidatos` contract violated on hard-route returns

**File:** `src/analista/core/arquetipo.py:47-49, 99, 103` vs comment at `:122-123`
**Issue:** The dataclass docstring and the inline comment ("`candidatos` sempre populado")
promise `candidatos` is always filled for debug/Phase-3 display. But the two hard-route
returns (`FINANCEIRA` line 99, `PAGADORA_REGULADA` line 103) construct
`ResultadoArquetipo` with the default empty `candidatos=[]`. Any downstream consumer that
trusts the "sempre populado" contract (e.g. Phase 3 "inclui X nos candidatos") will see an
empty list for the most common routes.
**Fix:** Populate the single-candidate list on the hard-route returns:
```python
return ResultadoArquetipo(FINANCEIRA, candidatos=[FINANCEIRA], confianca="alta")
...
return ResultadoArquetipo(PAGADORA_REGULADA, candidatos=[PAGADORA_REGULADA], confianca="alta")
```

### WR-03: Suspended-verdict message interpolates the placeholder motor, not the real engine

**File:** `src/analista/report/report.py:211-215`
**Issue:** When `motor_pendente`, the verdict reads
`f"...arquétipo {a.arquetipo} usa o motor '{a.motor}', que chega na Fase 2..."`, but
`a.motor` is the placeholder `"pendente_fase_2"` (set at line 152). The rendered text
becomes "usa o motor 'pendente_fase_2', que chega na Fase 2" — redundant and it never tells
the user which real engine the archetype actually needs (RIM/DCF/lucro-normalizado/SOTP),
which is the whole point of the D-04 message.
**Fix:** Maintain an archetype→engine-name map for display and interpolate that instead of
the placeholder, e.g. `financeira → "RIM"`, `crescimento → "DCF multi-estágio"`, so the
message reads "…usa o motor RIM, que chega na Fase 2."

### WR-04: Suspended-verdict message asserts "o DDM abaixo" even when the DDM did not run

**File:** `src/analista/report/report.py:203-215`
**Issue:** The `motor_pendente` branch is entered before checking whether the DDM produced
a band. When a pendente archetype also lacks valuation inputs (e.g. a financeira with
insufficient data → `ddm_constante is None`, `vmin/vmax is None`), the hardcoded phrase
"o DDM abaixo é lente conservadora" references a table that is absent, and no alert names
the missing inputs (the AUD-VAL-03 branch at 256-269 still runs, but the verdict text
itself is misleading).
**Fix:** Make the "DDM as lens" clause conditional on `a.ddm_constante is not None`, or drop
the reference to "o DDM abaixo" when the band did not compute.

## Info

### IN-01: `dict.fromkeys` dedup on `candidatos` is a no-op

**File:** `src/analista/core/arquetipo.py:124`
**Issue:** `distintos = list(dict.fromkeys(candidatos))` deduplicates, but each of
`CICLICA`/`CRESCIMENTO`/`PAGADORA_REGULADA` is appended at most once, so duplicates are
impossible. The line reads as defensive against a scenario that cannot occur.
**Fix:** Either drop the dedup and use `candidatos` directly, or add a comment noting it is
purely future-proofing so a reader does not assume duplicates are expected.

### IN-02: Primary `chave` in a real conflict is arbitrary and undocumented

**File:** `src/analista/core/arquetipo.py:126-127`
**Issue:** On a `ciclica`/`crescimento` conflict, `chave = distintos[0]` is always `ciclica`
solely because it is appended first (line 113 before 117). Nothing documents why cyclical
wins the tie for the displayed primary route; combined with CR-01 this is what surfaces a
compounder as "cíclica" in the header.
**Fix:** Document the tie-break rationale, or set the primary `chave` deliberately (e.g. the
higher-confidence signal) rather than by append order.

---

_Reviewed: 2026-07-11T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
