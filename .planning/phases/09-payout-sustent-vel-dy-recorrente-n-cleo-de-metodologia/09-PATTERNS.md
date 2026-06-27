# Phase 9: Payout sustentável + DY recorrente (núcleo de metodologia) - Pattern Map

**Mapped:** 2026-06-27
**Files analyzed:** 7 (1 likely-new primitive + 3 modified source + 3 modified/new test)
**Analogs found:** 7 / 7 (all in-repo — this phase extends existing primitives, no greenfield)

> This is a pure-function Python analytics engine. "Role" here maps to engine concepts:
> **pure-primitive** (stateless transform on number sequences), **method** (CompanyData
> derived calc), **consumer** (report assembly), **golden test**. Every new/modified file
> has an exact sibling already in the codebase — copy its shape, do not invent a new one.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/core/normalizacao.py` (add payout-median primitive) | pure-primitive | transform | `base_normalizada` / `media_winsorizada` (same file) | exact |
| `src/analista/core/fundamentals.py` §`payout_valuation` (L77) | method | transform (aggregate) | `base_lucro_normalizada` (L122, same file) | exact |
| `src/analista/core/fundamentals.py` §`dpa_recorrente`/`dy_recorrente` (L173-181) | method | transform | `lpa_valuation` (L132) earnings-based pattern | exact |
| `src/analista/report/report.py` §`analisar_acao` (L50-107) | consumer | request-response | n/a (verify-only; call sites unchanged) | self |
| `tests/test_fundamentals_consistencia.py` (payout goldens) | golden test | assert | `test_normalizacao.py` (primitive golden) | role-match |
| `tests/test_vulc3_regressao.py` (rebaseline) | golden test | assert | self (existing capstone) | self |
| `tests/test_normalizacao.py` (add payout-median unit goldens) | golden test | assert | self (existing primitive golden) | self |

---

## Pattern Assignments

### `src/analista/core/normalizacao.py` — new payout-median primitive (pure-primitive, transform)

**Analog:** `base_normalizada` (L58-75) and `media_winsorizada` (L39-55), same file.

D-01/D-04 want **median over the COMPLETE payout series** (not 3a window, not winsorized
mean). This is a *sibling* of `base_normalizada` but with a different rule: plain median over
all valid points, with the same None-frontier and `_limpar` reuse. Mirror this exact shape.

**`_limpar` helper to reuse verbatim** (L34-36) — the established None-dropping convention:
```python
def _limpar(valores: Sequence[Number]) -> List[float]:
    """Descarta os None (não contam como 0) e converte para float."""
    return [float(v) for v in valores if v is not None]
```

**Primitive shape to mirror** (`base_normalizada`, L58-75) — note the fallback ladder
(empty→None, single→itself) that D-04 explicitly requires preserved:
```python
def base_normalizada(
    valores: Sequence[Number], anos_media: int = 3, winsor: float = 0.10
) -> Number:
    limpos = _limpar(valores)
    if not limpos:
        return None
    janela = limpos[-anos_media:] if anos_media else limpos
    n = len(janela)
    if n == 1:
        return janela[0]
    if n < 5:
        return float(median(janela))
    return media_winsorizada(janela, winsor)
```

**New primitive to write** (e.g. `payout_sustentavel` / `mediana_payout`): take the FULL
series (no `anos_media` slice — D-04), drop None via `_limpar`, return `None` for empty,
the single value for N==1, else `float(median(limpos))`. **No `min(..., 1.0)` clamp** (D-03 —
median can legitimately be >1.0, e.g. TAEE11 ≈ 2.16). Imports already present: `from
statistics import median`. Keep it purely numeric/statistics — the purity test below enforces it.

**Purity invariant to keep green** (`test_normalizacao.py` L87-92) — any new primitive must
not import the engine:
```python
def test_primitiva_e_pura_sem_import_de_fundamentals():
    src = inspect.getsource(norm)
    assert "fundamentals" not in src
    assert "report" not in src
```

---

### `src/analista/core/fundamentals.py` §`payout_valuation` (method, aggregate transform)

**Analog:** `base_lucro_normalizada` (L122-125) — the canonical "delegate the series to a
pure primitive" pattern. `payout_valuation` should be rewritten in that exact shape.

**Current implementation to REPLACE** (L77-90) — 3a window + clamp, both rejected by D-01/D-03/D-04:
```python
def payout_valuation(self, janela: int = 3) -> Optional[float]:
    anos = self.anos_ordenados()[-janela:]
    vals = [v for v in (self.payout(a) for a in anos) if v is not None]
    if not vals:
        return None
    return min(sum(vals) / len(vals), 1.0)   # ← drop the 3a window AND the clamp
```

**Target shape to copy** (from `base_lucro_normalizada`, L122-125 — feed the full per-year
series into the new pure primitive):
```python
def base_lucro_normalizada(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
    return norm.base_normalizada(self.serie("lucro_liquido"), anos_media, winsor)
```
New `payout_valuation` builds the COMPLETE payout series — `[self.payout(a) for a in
self.anos_ordenados()]` (keep the None entries; the primitive's `_limpar` drops them) — and
delegates to the new median primitive in `normalizacao`. No `janela` slice, no clamp.

**Canonical-call invariant (FIX-04, must hold):** all callers invoke it with **no args** so
the 3 surfaces stay consistent by construction. Do NOT add a required parameter. Call sites
that must keep working unchanged:
- `report.py` L66 `"DP (payout)": c.payout_valuation()`, L82 `crescimento_por_fundamentos(c.roe_valuation(), c.payout_valuation())`, L133 `payout_proj = c.payout_valuation()` (DDM dpa_inicial)
- `cli.py` L149, L159
- `app.py` L466, L472

**Fronteira to NOT touch (D-06):** `payout(ano)` raw (L74-75) keeps feeding the per-year
table, the trap detector (`report.py` L155-157 `payout_ult = c.payout(ult)`), and per-year
screening. Only the valuation aggregate changes base.

---

### `src/analista/core/fundamentals.py` §`dpa_recorrente`/`dy_recorrente` (method, transform)

**Analog:** `lpa_valuation` (L132-135) — "normalized earnings base × per-share op" — and the
new `payout_valuation`. D-05 redefines DY recorrente as **earnings-based**:
`payout_sustentável × lucro_normalizado_por_ação ÷ preço`, reusing `base_lucro_normalizada()`/
`lpa_valuation()` from Phase 8 — NOT the raw 3a median of the dividend series.

**Current implementation to REPLACE** (L173-181) — dividend-series median, rejected by D-05
(falls entirely into the >100% payout era for VULC3 → false 20.4%):
```python
def dpa_recorrente(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
    base = norm.base_normalizada(self.serie("dividendos"), anos_media, winsor)
    return mult.dpa(base, self.num_acoes.get(self.ultimo_ano()))

def dy_recorrente(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
    return mult.dividend_yield(self.dpa_recorrente(anos_media, winsor), self.preco_atual)
```

**Target composition (D-05):** recurring DPA = `payout_valuation() × lpa_valuation()` (i.e.
sustainable payout applied to normalized per-share earnings); DY recorrente =
`mult.dividend_yield(dpa_recorrente, self.preco_atual)`. Reuse the existing `mult.dividend_yield`
(L90-92) and `lpa_valuation` (L132-135). Keep the None-frontier (any input None → None).

**Sanity targets (CONTEXT specifics):** VULC3 DY rec. 20.4% → 6.2%; TAEE11 earnings-based
8.3% ≈ dividend-based 8.1%. Use as asserts.

---

### `src/analista/report/report.py` §`analisar_acao` (consumer — VERIFY ONLY)

No code change expected — only the *implementations* behind the same call sites change (CONTEXT
Integration Points). Confirm the existing floor absorbs payout >1.0.

**g_fundamentos + g_alto floor that handles unclamped payout >1.0** (L82, L93-98) — D-03 relies
on this *existing* `max(0.0, ...)`; add no new floor:
```python
a.g_fundamentos = growth.crescimento_por_fundamentos(c.roe_valuation(), c.payout_valuation())
...
g_alto = a.g_historico if a.g_historico is not None else a.g_fundamentos
if a.g_fundamentos is not None:
    g_alto = a.g_fundamentos if g_alto is None else min(g_alto, a.g_fundamentos)
if g_alto is not None:
    g_alto = max(0.0, min(g_alto, 0.25))   # ← payout>100% ⇒ g_fund<0 ⇒ g_alto=0 here
a.g_alto = g_alto
```
`crescimento_por_fundamentos` (growth.py L49-56) returns `roe * (1.0 - payout)` — with payout
>1.0 this goes negative, then `max(0.0, …)` clamps to 0. Correct for a mature cash-cow (D-03).

**DDM consumption to re-check** (L133-137): `dpa_inicial = lpa * (1 + a.g_alto) * payout_proj`
with `payout_proj = c.payout_valuation()` now possibly >1.0 (TAEE11 ≈2.16). Verify the DDM still
produces a finite intrinsic — this is a *behavioral* change to validate, not an edit.

---

### Golden tests — REBASELINE/EXTEND (golden test, assert)

This phase's success criterion 5 + the milestone invariant (REQUIREMENTS TEST-08, formally
Phase 11) require: goldens stay green OR are rebaselined **deliberately with justification**.
Two existing asserts WILL break under D-03 and must be rebaselined on purpose:

**1. `tests/test_fundamentals_consistencia.py` L15-21 — the clamp golden is now WRONG (D-03):**
```python
def test_payout_valuation_clamp_em_1():
    # payout médio 3a > 1.0 deve ser cravado em 1.0
    ...
    assert c.payout_valuation() == 1.0     # ← D-03 removes the clamp; rebaseline to median
```
Also L24-45 (`media_dos_3_ultimos_anos`, `ignora_none`, `none_sem_dados`) encode the **3a-window**
+ average semantics — rebaseline to **median-over-full-series** (D-01/D-04). Keep the None-frontier
case (`none_sem_dados` L43-45 stays: empty → None).

**2. `tests/test_vulc3_regressao.py` L83 — payout assert flips off the clamp:**
```python
assert c.payout_valuation() == 1.0     # ← becomes median of the >100% era; rebaseline
```
Note the synthetic VULC3 fixture (L37-64) has dividends ≥ lucro in *every* year, so its median
payout is itself >1.0 — confirm `g_fundamentos == 0.0` / `g_alto == 0.0` (L84-85) STILL hold via
the report floor (they should: payout>1 ⇒ g_fund<0 ⇒ max(0,…)=0). The `dy_recorrente() <=
dy_atual()` assert (L125) must hold under the new earnings-based formula — re-verify, do not relax.

**Golden test pattern to copy** (`test_normalizacao.py` L21-28) — pure-primitive unit goldens
with a one-line "why by method" comment + tight numeric tolerance:
```python
def test_outlier_alto_suavizado_pela_mediana():
    base = norm.base_normalizada([100, 105, 300], anos_media=3, winsor=0.10)
    assert base is not None
    assert abs(base - 105) < 1e-9
    assert base < (100 + 105 + 300) / 3
```
Add a sibling unit golden for the new payout-median primitive: a >100% series whose median is
>1.0 (TAEE11 spirit — assert NO clamp), and an outlier-year series whose median discards the spike.

**Engine-level golden pattern** (`test_vulc3_regressao.py` L37-64) — the offline synthetic
`CompanyData` builder + `report.analisar_acao(c, _cfg())`. Copy this to add the **multi-ticker
acceptance** asserts (success criterion 4): synthetic VULC3 (43%), TAEE11 (216%, preserved),
EGIE3 (49%), ITUB4 (31%), BBAS3 (20%) median-payout targets and the DY-rec targets (VULC3 6.2%,
TAEE11 8.3%) from CONTEXT `<specifics>`. `_cfg()` loads the shipped `config.yaml` for determinism.

---

## Shared Patterns

### Pure-primitive contract (None-frontier + `_limpar`)
**Source:** `src/analista/core/normalizacao.py` L34-36, L66-71
**Apply to:** the new payout-median primitive
```python
limpos = _limpar(valores)   # drops None, never treats as 0
if not limpos:
    return None              # empty / all-None → None (graceful degradation, D-04)
if len(limpos) == 1:
    return limpos[0]         # single value → itself
```

### Canonical no-arg valuation method (FIX-04 cross-menu consistency)
**Source:** `src/analista/core/fundamentals.py` L110-121 (doc) + call sites in report/cli/app
**Apply to:** the rewritten `payout_valuation`, `dy_recorrente`
Keep callable with **no required args** so Analisar / Ranking-app / Ranking-cli read the identical
number. `anos_media=3`/`winsor=0.10` defaults mirror the `normalizacao` block of `config.yaml`.

### CRU vs normalizado boundary (D-06 — do not cross)
**Source:** `fundamentals.py` L74-75 (`payout`), `report.py` L155 (`payout_ult = c.payout(ult)`)
**Apply to:** every change — only the valuation *aggregate* (`payout_valuation`/`dy_recorrente`)
moves to median base; raw `payout(ano)` keeps feeding per-year table, trap detector, screening.

### Config knob convention
**Source:** `config.yaml` L50-58 (`normalizacao:` block, `anos_media`/`winsor`)
**Apply to:** if a knob is needed for the payout methodology, add it under/near the `normalizacao`
block (D-discretion). Default values live in config; methods take them as defaulted kwargs.

---

## Cross-effect to REGISTER (do NOT resolve here — Phase 10)

**Source:** `src/analista/core/screening.py` §`bsd_ranking` (L327) + the P/L regression that
`app.py` L472 / `cli.py` L159 feed via `preco_alvo_por_regressao(reg, c.payout_valuation(), …)`.
Unclamped `payout_valuation` (TAEE11 ≈2.16) now flows into a P/L regression calibrated on payout
∈ [0,1] (CONTEXT canonical_refs + deferred). Phase 9 must leave a note; clamping only at the
regression input is a **Phase 10** decision. Per-year BSD payout (`screening.py` L218, L257
`media([c.payout(a) for a in anos])`) is raw per-year and unaffected (D-06).

---

## No Analog Found

None. Every file in scope extends or rebaselines an existing sibling in this repo.

## Metadata

**Analog search scope:** `src/analista/core/` (normalizacao, fundamentals, multiples, growth,
screening), `src/analista/report/`, `src/analista/cli.py`, `app.py`, `tests/`, `config.yaml`
**Files scanned:** 11
**Pattern extraction date:** 2026-06-27
