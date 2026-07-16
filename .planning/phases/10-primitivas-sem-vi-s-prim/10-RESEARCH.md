# Phase 10: Primitivas sem viés (PRIM) - Research

**Researched:** 2026-07-15
**Domain:** Numerical methods (robust trend estimation, deflation) applied to valuation primitives in a pure-Python engine
**Confidence:** HIGH (every core claim was executed against the live snapshots, not reasoned from training)

> **Reading note for the planner:** this is a numerical-methods phase. The CONTEXT locked the
> *WHAT* (Theil-Sen, median-of-ROEs, remove winsor, deflate cyclical). This research validated the
> *HOW* by running the proposed methods against the 104-ticker clean snapshot and the bank snapshot.
> The three findings that change the plan shape are: (1) the 32,88 golden **does** break — confirmed;
> (2) `base_normalizada` **cannot** be globally swapped to Theil-Sen — the cyclical engine needs the
> opposite estimator; (3) the CONTEXT/ROADMAP anchor numbers (16,1% → 18,0%, "fabricated g 36%/47%")
> were measured on **pre-Phase-9 dirty data** and do not reproduce verbatim on the clean snapshot —
> the exit criteria must be **method-based**, not number-based.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Substituir o `median()` de 3 anos em `base_normalizada` (`normalizacao.py:58-75`) por um
  **endpoint de regressão robusta (Theil-Sen)**: ajustar tendência robusta na série de lucro e usar o
  valor ajustado **no ano atual**.
- **D-01a (validado nesta pesquisa):** o estimador Theil-Sen foi rodado contra o mapa de 104 tickers +
  o snapshot de bancos. Não overshoota de forma sistemática (mediana endpoint/último = 1,00 na janela
  de 3), o BLIND-03 vira verde e o golden 32,88 quebra. **Ressalva descoberta:** Theil-Sen sobre a
  série de **níveis** degenera (endpoint negativo) para tickers com prejuízo recente — precisa de guarda.
- **D-01b:** fallback para séries curtas — N=1 → o próprio valor; N=2 → média/mediana; série vazia → None.
- **D-02:** `roe_valuation` passa a ser a **mediana da série de ROEs anuais** (cada ROE via `roe(ano)`,
  `fundamentals.py:110`, lucro_t ÷ PL médio(t-1,t)), sobre a **série completa** — espelhando
  `mediana_payout`. Alvo de ancoragem: ITUB4 → 18,0%.
- **D-03:** Deflacionar a base do **motor cíclico** por IPCA (BCB SGS, via `macro.py`), trazendo a
  série a **reais do último ano**. **Escopo limitado ao motor cíclico** — a base do CAGR/`g` fica p/ a Fase 11.
- **D-04:** **Remover** a winsorização da série temporal (`serie_winsorizada`/`serie_lucro_normalizada`)
  e deixar a série do CAGR/`g_historico` **crua até a Fase 11**.

### Claude's Discretion
- Biblioteca do Theil-Sen (`scipy.stats.theilslopes` — **confirmado presente**, `scipy 1.17.1`) e a forma
  exata do fallback de série curta.
- Janela do Theil-Sen (3 / 5 / série completa) — **research recomenda janela curta com guarda de
  degeneração**; ver §Architecture.

### Deferred Ideas (OUT OF SCOPE — Fase 11+)
- Deflação da base do CAGR/`g` → Fase 11.
- Desenho do `g` robusto (slope de regressão em log etc.) → Fase 11.
- Conserto do `Ke`/`ke_teto` → Fase 12.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRIM-01 | Base de lucro deixa de descartar o ano recente (`normalizacao.py:73-75`, `median()` de 3 = ano do meio) | Theil-Sen endpoint validado: janela=3 → endpoint ≈ último ano (mediana 1,00 nos 104); BLIND-03 verde. **Não aplicar ao motor cíclico.** |
| PRIM-02 | `roe_valuation` deixa de cruzar bases → mediana da série de ROEs anuais; ITUB4 → 18,0% | Rodado: método = median(`roe(a)`). ITUB4 = **18,0%** no snapshot de bancos (exato), 18,5% no clean. `_roe_through_cycle` **já** faz isso — reusar. |
| PRIM-03 | Winsorização não aplicada à série temporal | Rodado: VULC3 `g_historico` 31,5% (winsor) → 36,1% (cru). CYRE3: None em ambos (prejuízos bloqueiam log-linear no clean). |
| PRIM-04 | Base do motor cíclico deflacionada por IPCA | Rodado: CSNA3 base cíclica nominal 1.270M → real 1.899M (**+49,6%**). `macro.py` puxa BCB; precisa de série IPCA anual nova. |
| PRIM-05 | **CRITÉRIO DE SAÍDA:** golden `ITUB4 32,88 ± 0,20` QUEBRA e é DELETADO | Rodado: só PRIM-02 já move o RIM do ITUB4 de **32,88 → 31,52**. Golden = `test_backtest_bancos.py::test_backtest_alvos_recalibrados`. |
</phase_requirements>

---

## Summary

Phase 10 removes four independent biases from the valuation primitives. Each was validated by running
the proposed method against the frozen 104-ticker clean snapshot (`snapshot_sanidade_limpo_2026-07-15.yaml`)
and the bank snapshot (`snapshot_bancos_2026-07-12.yaml`). All four are implementable with the current
dependency set (`scipy 1.17.1` is already installed — `theilslopes` needs **no** new package), and none
adds a tunable parameter, so the 3-knob budget is preserved.

The single most important structural finding: **`base_normalizada` is called by two consumers that want
opposite estimators.** The valuation base (`base_lucro_normalizada`, `anos_media=3`) wants a Theil-Sen
**endpoint** (reflect recent growth — PRIM-01). The cyclical engine (`report.py:256`, `anos_media=10`)
wants a through-cycle **average** (robust to a recent loss — PRIM-04). Swapping the shared function to
Theil-Sen globally breaks the cyclical engine: CSNA3's Theil endpoint over 10y is **−891M** (a loss),
while its through-cycle average is **+1.270M**. The plan must therefore **split the estimator**, not
edit one function.

The exit criterion is confirmed: changing `roe_valuation` alone (PRIM-02) moves ITUB4's RIM from exactly
**32,88 → 31,52** on the bank snapshot, breaking the `± 0,20` golden. The golden to delete is
unambiguously `tests/test_backtest_bancos.py::test_backtest_alvos_recalibrados`.

**Primary recommendation:** Introduce **two** estimators in `normalizacao.py` — a parameter-free
Theil-Sen endpoint (with a degeneration guard) for the 3-year valuation base, and keep the existing
median/winsorized-mean averaging for the cyclical engine but feed it an **IPCA-deflated** series.
Delegate `roe_valuation` to the median-of-annual-ROEs computation that `_roe_through_cycle` already
implements. Verify all exit criteria as **method assertions**, not against the stale anchor numbers.

---

## Architectural Responsibility Map

| Capability | Primary Site | Estimator it needs | Rationale |
|------------|-------------|--------------------|-----------|
| Valuation profit level (LPA/EY/P-L/Graham/DCF) | `fundamentals.base_lucro_normalizada` (`anos_media=3`) | **Theil-Sen endpoint** (recent-weighted, robust) | PRIM-01: must reflect the recent year, not the middle one |
| Valuation ROE (RIM roe0, displayed ROE, Ranking) | `fundamentals.roe_valuation` | **Median of annual `roe(a)`** (full series) | PRIM-02: stop crossing lucro(t-2y)÷PL(t); robust to a loss year |
| Cyclical engine base (`lucro_normalizado` motor) | `report._intrinseco_por_motor` `"normalizado"` (`anos_media=10`) | **Through-cycle AVERAGE** on a **deflated** series | PRIM-04: wants mid-cycle earnings power, NOT an endpoint; deflate first |
| `g_historico` (CAGR trend) | `report.py:378` via `serie_lucro_normalizada` | **RAW series** (winsor removed), leave to Fase 11 | PRIM-03: remove the temporal-winsor bias; do not design robust g here |

---

## Empirical Validation (the crux — measured, not assumed)

All numbers below were produced by executing the proposed methods. Scripts and raw output are reproducible
from the snapshots named. `[VERIFIED: execution 2026-07-15]` on every row.

### PRIM-01 / BLIND-03 — Theil-Sen endpoint on the pure-growth test series

Test series `[100, 110, 121, 133.1, 146.41]` (+10%/yr, zero outlier); floor `piso = 146.41 × (1−0.0518) = 138.83`.

| Estimator | Result | BLIND-03 |
|-----------|--------|----------|
| Current `median()`-of-3 (production) | **133.10** | FAIL (this is the xfail today) |
| Theil-Sen endpoint, window=3 | **145.81** | ✅ PASS |
| Theil-Sen endpoint, window=5 | **144.20** | ✅ PASS |
| Theil-Sen endpoint, full series | **144.15** | ✅ PASS |

**BLIND-03 flips green with Theil-Sen at any window.** `[VERIFIED: execution]`

### PRIM-01 — window choice across the 104-ticker universe (endpoint ÷ last-year)

| Window | median | p10 | p90 | overshoot >1.5× last | negative endpoint |
|--------|--------|-----|-----|----------------------|-------------------|
| 3 | 1.00 | 0.75 | 1.40 | 7 | **2** |
| 5 | 0.95 | 0.29 | 1.28 | 7 | **5** |
| full | 0.94 | 0.59 | 2.16 | — | — |

**Robustness to a single terminal spike** (inject a 2× jump at the year before last):

| Estimator | Pure +10% | With 2× spike | Robust? |
|-----------|-----------|---------------|---------|
| `median()`-of-3 | 146.4 | 146.4 | yes (but fails BLIND-03) |
| Theil-Sen window=3 | 145.8 | **159.1** | weak — chases the spike |
| Theil-Sen window=5 | 144.2 | **144.7** | strong — barely moves |

**Conclusion:** window=3 has the tightest cross-sectional distribution and the fewest degenerate
(negative) endpoints, **but** with only 3 points Theil-Sen cannot separate a terminal outlier from
trend (spike → 159). window=5 is far more outlier-robust (D-01's actual requirement) but produces
more negative endpoints on loss-recent tickers. **Neither dominates.** Recommendation in §Architecture.

### PRIM-02 — `roe_valuation` = median of annual ROEs

| Ticker | CURRENT `roe_valuation` (base/PL, cross-basis) | NEW median-of-annual-ROEs | Book/target |
|--------|-----------------------------------------------|---------------------------|-------------|
| ITUB4 (bank snapshot) | 19,3% | **18,0%** | 18,0% ✅ exact |
| ITUB4 (clean snapshot) | 19,8% | 18,5% | ~18% |
| VULC3 | 25,1% | 26,7% | — |
| CYRE3 | 17,2% | 12,7% | — |
| CSNA3 | −15,9% | **+7,8%** | — (median ignores the loss year) |

`[VERIFIED: execution]`. **The CONTEXT "16,1% → 18,0%" is stale (pre-Phase-9).** On clean data the
current value is ~19–20%, and the new method lands ~18% — i.e. the *direction* is slightly **down**,
not up, but it converges on the book's 18,0%. **Plan the exit check as "roe_valuation ≈ median of
annual ROEs and lands near 18% for ITUB4", not as "goes from 16,1 to 18,0".**

### PRIM-05 — the 32,88 golden breaks

On the bank snapshot, with everything else held, swapping `roe_valuation` to median-of-annual-ROEs:

| roe0 fed to RIM | ITUB4 RIM |
|-----------------|-----------|
| CURRENT 19,3% | **32,88** (reproduces the golden exactly) |
| NEW 18,0% | **31,52** |

`31,52` vs `32,88 ± 0,20` → **BREAKS.** `[VERIFIED: execution]`. PRIM-02 alone is sufficient to break
it; the Theil-Sen base and deflation move it further. Exit criterion materialises.

### PRIM-03 — winsor removal changes `g_historico`

| Ticker | `g_historico` winsorized (today) | `g_historico` raw (Phase 10) |
|--------|----------------------------------|------------------------------|
| VULC3 | 31,5% | **36,1%** |
| CYRE3 | None (loss years) | None (loss years) |

`[VERIFIED: execution]`. **The ROADMAP framing "winsorization fabricates 36%/47%" does not reproduce on
the clean snapshot.** On clean data the winsor actually *suppresses* VULC3's slope (raising the low 2016
base), so raw is *higher* (36,1%), and CYRE3's g is `None` both ways because raw loss years block the
log. The 36%/47% figures were displayed on the **pre-Phase-9 dirty data**. **Verify PRIM-03
structurally** (`serie_lucro_normalizada` returns the raw series; winsor no longer applied to the
temporal series) and record the measured g-deltas — do **not** assert "the 36% disappears".

### PRIM-04 — IPCA deflation of the cyclical base

CSNA3, `anos_media=10`, approximate calendar IPCA (SGS 13522 at each December):

| Base | Value |
|------|-------|
| Nominal through-cycle average (today) | 1.270M |
| IPCA-deflated to last-year reais | **1.899M** |
| Uplift | **+49,6%** |

`[VERIFIED: execution, IPCA approximate]`. Direction confirms the "undervalued by nominality" claim
(ROADMAP: 31,8% on `V`; +49,6% here is on the *base*, before the engine). The planner **must** pull the
real BCB IPCA series — the numbers above use hand-entered IPCA and are indicative only.

### The estimator conflict (decisive)

CSNA3, cyclical window=10: **through-cycle average = +1.270M** vs **Theil-Sen endpoint = −891M**
(last year = −2.002M). `[VERIFIED: execution]`. A cyclical company with a recent loss must be valued on
its mid-cycle power, not its worst year. **Do not route the cyclical engine through the Theil-Sen
endpoint.**

---

## Standard Stack

No new dependencies. Everything is already declared in `pyproject.toml` and installed.

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `scipy` | 1.17.1 (installed) | `scipy.stats.theilslopes` — robust (Theil-Sen) slope+intercept | `[VERIFIED: .venv import]` |
| `numpy` | ≥1.24 | array plumbing for the estimator | present |
| `requests` | ≥2.31 | `macro.py` BCB SGS pull (IPCA) | present |
| `statistics` (stdlib) | — | `median` for roe_valuation / payout | present |

**No install step. No lock/budget impact from dependencies.** `theilslopes(y, x)` returns
`(slope, intercept, low_slope, high_slope)`; endpoint prediction = `intercept + slope × x[-1]`. It is
**parameter-free** (no 4th degree of freedom).

---

## Architecture Patterns

### Recommended change shape

```
normalizacao.py
├── base_normalizada(...)        # PRIM-01: swap median→Theil-Sen ENDPOINT + degeneration guard
│                                #   used ONLY by the 3y valuation base after the split below
├── media_ciclo(...)  (NEW/renamed)  # PRIM-04: the EXISTING median/winsorized-mean averaging,
│                                #   kept for the cyclical engine, fed a DEFLATED series
├── serie_winsorizada(...)       # PRIM-03: callers stop using it for the temporal series
└── (mediana_payout unchanged)

fundamentals.py
├── base_lucro_normalizada()     # calls the Theil-Sen base_normalizada (endpoint)
├── roe_valuation()              # PRIM-02: delegate to median-of-annual-roe(a) — same as _roe_through_cycle
└── serie_lucro_normalizada()    # PRIM-03: return c.serie("lucro_liquido") RAW (no winsor)

report.py
└── _intrinseco_por_motor "normalizado"  # PRIM-04: deflate the lucro series by IPCA before averaging

macro.py
└── ipca_deflatores_anuais(anos) (NEW)   # BCB SGS annual IPCA → {ano: fator para o último ano}
```

### Pattern 1: Theil-Sen endpoint with a degeneration guard (PRIM-01, D-01/D-01b)
**What:** robust trend, value at current year; degrade gracefully for short/negative series.
**When:** the 3-year valuation base only.
```python
# Source: scipy.stats.theilslopes (VERIFIED present); guard is this project's requirement
from scipy.stats import theilslopes
import numpy as np

def _endpoint_theilsen(vals, anos_media=3):
    v = [float(x) for x in vals if x is not None]
    v = v[-anos_media:] if anos_media else v
    n = len(v)
    if n == 0: return None            # D-01b: série vazia
    if n == 1: return v[0]            # D-01b: 1 ponto
    if n == 2: return sum(v) / 2.0    # D-01b: 2 pontos → média
    slope, intercept, *_ = theilslopes(v, np.arange(n))
    endpoint = intercept + slope * (n - 1)
    # GUARD (discovered in research): Theil-Sen sobre níveis degenera negativo p/ prejuízo recente.
    # Sem guarda, roe/lpa_valuation viram negativos e o RIM/DCF quebra. Recomendação: se endpoint<=0
    # ou endpoint diverge do último ano além de um múltiplo, degradar para median(v) (comportamento antigo).
    if endpoint <= 0:
        return float(np.median(v))
    return float(endpoint)
```
**Anti-pattern:** applying this to the cyclical engine (`anos_media=10`) — see the conflict above.

### Pattern 2: `roe_valuation` = median of annual ROEs (PRIM-02, D-02)
**What:** stop the cross-basis; reuse the exact computation `_roe_through_cycle` already uses.
```python
# Source: report.py:184 _roe_through_cycle ALREADY does this — extract a shared helper.
def roe_valuation(self):
    serie = [self.roe(a) for a in self.anos_ordenados()]   # roe(a): lucro_t ÷ PL médio(t-1,t)
    validos = [r for r in serie if r is not None]
    return float(median(validos)) if validos else None
```
**Consistency win:** after this, the RIM's `roe0` (=`roe_valuation`) and `roe_terminal`
(=`_roe_through_cycle`) use the **same** statistic — today they disagree (base/PL vs median).

### Pattern 3: Deflate then average (PRIM-04, D-03)
**What:** express every year's lucro in last-year reais before the cyclical average.
```python
# reais do último ano (real-terms "de hoje"), NÃO ano-base fixo (D-03 / §Specific Ideas)
anos = c.anos_ordenados(); T = anos[-1]
defl = macro.ipca_deflatores_anuais(anos)      # {ano: prod(1+ipca[y]) para y in (ano+1..T)}
serie_real = [c.lucro_liquido[a] * defl[a] for a in anos if a in c.lucro_liquido]
base = norm.media_ciclo(serie_real, anos_media=10)   # o estimador de MÉDIA, não o endpoint
```
**Engine purity (FIX-03):** `analisar_acao` must stay offline/deterministic. Resolve the IPCA
deflators at the **entry points** (cli/app) and **carimbar no snapshot** for tests, exactly like `rf`
is resolved by `selic_ciclo_para_capm` and injected into `cfg`. Do **not** call `requests` from inside
the engine.

### Anti-Patterns to Avoid
- **Global `base_normalizada` swap** → breaks the cyclical engine (CSNA3 → −891M). Split the estimator.
- **Theil-Sen over the full series for the valuation base** → erratic on declining tickers (p90 = 2,16×
  last). Keep a short window + guard.
- **Deflating the CAGR/`g` base here** → explicitly Fase 11 (D-03 boundary). Only the cyclical engine.
- **Designing the robust `g`** (log-slope etc.) here → Fase 11. Phase 10 only *removes* winsor.
- **Updating the 32,88 golden to a new number** → Armadilha 3. DELETE it.

---

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Robust slope estimator | custom median-of-pairwise-slopes | `scipy.stats.theilslopes` | already installed, vetted, parameter-free |
| Median-of-ROEs | new ROE semantics | reuse `roe(ano)` + `statistics.median` (as `_roe_through_cycle` does) | avoids a 2nd ROE definition (Fronteira FIX-04) |
| IPCA series | scraping IBGE / new provider | `macro.py` BCB SGS (série 13522 or 433) | custo-zero; `macro.py` already does BCB date-range pulls for Selic |
| Snapshot loading | new loader | `helpers_sanidade.carregar_snapshot_sanidade(path)` | already reconstructs 104 CompanyData offline |

**Key insight:** the two hardest pieces (robust trend, through-cycle ROE) already exist in the codebase
or in scipy. The phase is mostly **re-wiring + splitting an estimator + a deflation pass**, not new math.

---

## Runtime State Inventory

Phase 10 touches only Python source, `config.yaml`, `calibracao.lock.yaml`, and test files. No stored
data / OS state migration — **except** the frozen test snapshots, which encode inputs (not results):

| Category | Items found | Action required |
|----------|-------------|-----------------|
| Stored data | None — engine is stateless; datastores unaffected. | None |
| Live service config | None. | None |
| OS-registered state | None. | None |
| Secrets/env vars | None. | None |
| Build artifacts | None (no package rename). | None |
| **Test fixtures** | `snapshot_bancos_2026-07-12.yaml` (bank golden data) and `snapshot_sanidade_limpo_2026-07-15.yaml` (104 clean). These hold **inputs**; the RIM value is recomputed by current code, so the 32,88 golden breaks from the **code** change, not a fixture edit. | Do **not** regenerate snapshots. Delete the golden **test**, keep the fixture. |

---

## Common Pitfalls

### Pitfall 1: Trusting the CONTEXT/ROADMAP anchor numbers verbatim
**What goes wrong:** planning "ITUB4 16,1% → 18,0%" or "VULC3 g 36% → gone" as literal exit checks; they
were measured on pre-Phase-9 dirty data and don't reproduce (measured: 19,8% → 18,5%; VULC3 raw = 36,1%).
**Avoid:** encode exit criteria as **method assertions** + re-measured targets on the clean snapshot.
**Warning sign:** a test asserting a specific R$/% that "should" appear — that is exactly a level-golden.

### Pitfall 2: Theil-Sen chasing a terminal outlier (n=3)
**What goes wrong:** with a 3-point window, a single high last-but-one year passes straight through
(spike → 159 vs 146). The old `test_outlier_alto_suavizado_pela_mediana` asserts the opposite and will break.
**Avoid:** window ≥ 5 (spike → 144,7) **or** a guard; and consciously **rewrite** the median-specific
unit tests in `test_normalizacao.py` (see §Validation Architecture) to encode the new method's invariants.
**Warning sign:** `test_outlier_alto_suavizado_pela_mediana`, `test_none_ignorado_antes_de_normalizar`
turning red — they encode the *old* estimator, not a system invariant.

### Pitfall 3: Negative Theil-Sen endpoint on loss-recent tickers
**What goes wrong:** CSNA3-like series produce a negative endpoint → `lpa_valuation`/DCF/Graham go
negative or None; silent NaN downstream.
**Avoid:** the `endpoint <= 0 → median(v)` guard in Pattern 1.
**Warning sign:** new `None`/negative `V` on tickers that had a value before.

### Pitfall 4: Deflating inside the engine (breaks determinism)
**What goes wrong:** calling `macro`/`requests` from `analisar_acao` makes the engine non-deterministic
and network-bound; tests over the frozen snapshot can't reproduce.
**Avoid:** resolve deflators at entry points and stamp them into `cfg`/snapshot, mirroring `rf`.
**Warning sign:** a test needs the network, or two runs differ.

### Pitfall 5: Deleting a golden test but leaving its `classificacao.yaml` line
**What goes wrong:** `tests/conftest.py` enforces completeness **both ways** — an orphan YAML entry
(test deleted, line kept) **breaks collection**, exactly like a missing entry.
**Avoid:** delete the test function **and** its `classificacao.yaml` line in the same change.
**Warning sign:** `pytest` collection error mentioning an órfão nodeid.

### Pitfall 6: Leaving the BLIND-03 `xfail` after the cure
**What goes wrong:** `xfail_strict = true` (pyproject) turns the now-passing `xfail` into **XPASS = FAIL**.
**Avoid:** in the same change that fixes `normalizacao.py`, **remove** the
`@pytest.mark.xfail(...)` on `test_normalizacao_nao_pune_crescimento` (`test_invariantes_v24.py:161`).
It stays classified `invariante` — never loosen the assert, never swap xfail→skip.

---

## Golden Disambiguation (PRIM-05) — DEFINITIVE

There are several `32.88` occurrences. Classified by what to do in Phase 10:

| Location | What it is | Phase 10 action |
|----------|------------|-----------------|
| `tests/test_backtest_bancos.py::test_backtest_alvos_recalibrados` (`alvos={"ITUB4":32.88,...}` ±0,20) | **THE PRIM-05 exit golden.** `golden_nivel` in `classificacao.yaml:63` with "DELETAR na Fase 10 (PRIM-05)". Runs current code over the bank snapshot → RIM 32,88 today, 31,52 after. | **DELETE** test + its YAML line. |
| `tests/test_backtest_bancos.py:10,117` header comment "32,88 INALTERADO — o cap satura, não regride" | Prose referring to the **inflation-shock invariance** (BLIND-02b), a **Fase 12** property — *not* a primitive-level golden. | Leave the prose; it dies with the file only if the file is removed. |
| `tests/test_invariantes_v24.py::test_invariancia_inflacao_engine_itub4` (V 32,88→38,80 under +300bps) | BLIND-02b `xfail(strict)`. Goes green in **Fase 12** (ke_teto removal), not here. | **DO NOT TOUCH.** |
| `tests/helpers_blindagem.py:157,215` (`ALVOS = {"ITUB4": 32.88}`, `_confere(v, 32.88)`) | **Anti-pattern EXAMPLES** inside the BLIND-04a AST detector's own fixtures/docstrings. | **DO NOT DELETE** — deleting them blinds the guard. |
| `tests/fixtures/snapshot_bancos_2026-07-12.yaml:296 intrinseco_motor_observado: 32.88` | A recorded observation in the fixture. | Leave (fixture holds inputs/observations, not the assert). |
| `tests/test_motores.py:248` (`≈R$32,88, dentro da faixa 30–40`) | Prose in a docstring of a band test. | Handled via the band golden below. |

### Full golden_nivel set tagged for Phase 10 (from `classificacao.yaml`)

These all assert an ITUB4 R$-level band and **break** when the primitives change. Per the v2.4 rule
(golden_nivel that breaks is **DELETED**, never updated), delete each **with its YAML line**:

1. `test_backtest_bancos.py::test_backtest_alvos_recalibrados` — ITUB4 32,88 ±0,20 ← canonical exit
2. `test_backtest_bancos.py::test_backtest_cesta_rota_por_ticker` — ITUB4 band 30–40
3. `test_backtest_bancos.py::test_backtest_gate_quorum_e_anotacao` — quorum over `fair_values_bancos`
4. `test_motores.py::test_rim_itub4_honesto_maior_que_ddm` — ITUB4 band 36–42
5. `test_motores.py::test_rim_itub4_live_alvo_32_40` — ITUB4 band 32–40
6. `test_motores.py::test_rota_seguradora_nao_pega_banco` — ITUB4 band 30–40
7. `test_vulc3_regressao.py::test_rim_itub4_dispatch_banda` — ITUB4 intrínseco > 30
8. `test_guardrails_ddm.py::test_san01_reetiqueta_aberracao_itub4_like` — ITUB4-like level in veredito
9. `test_arquetipo_roteamento.py::test_financeira_rim_destrava_vs_ddm_e_alimenta_veredito` — tagged "Fase 10/13"

> **Planner judgement (surface to discuss-phase):** items 1–7 are pure ITUB4-level bands → delete now.
> Item 8 is a re-labelling guardrail; item 9 is tagged "Fase 10/13". Confirm with the user whether 8–9
> die now or ride to Fase 13. The **hard** requirement of PRIM-05 is item **1**.

**Surviving tests in `test_backtest_bancos.py`** (`test_backtest_determinismo` = invariante,
`test_backtest_rotulo_do_motor_consistente` = contrato) do **not** assert R$-levels and survive — so
delete the 3 golden functions, not the whole file (unless the planner prefers to retire the whole
bank-backtest harness, which the user should confirm).

---

## Knob Budget Integrity (BLIND-06 / `calibracao.lock.yaml`)

`calibracao.lock.yaml` declares **30 leaves** = motores 11 + capm 12 + ddm 5 + normalizacao 2; a
partition of **3 graus de liberdade** (`ERP`, `n_fade`, `PIB_real`) + **27 congelados**. Relevant facts:

- `normalizacao.anos_media: 3` and `normalizacao.winsor: 0.1` are **congelados**, explicitly labelled
  "**NÃO É GRAU DE LIBERDADE — É A TRAVA DO BLIND-03**". `motores.ciclica.anos_media: 10` and
  `motores.ciclica.winsor: 0.1` are also congelados.
- **Theil-Sen is parameter-free → adds NO 4th degree of freedom.** ✅ (the CONTEXT's core worry.)
- **Recommended path (keep `anos_media` in config):** swap only the *estimator*, leave
  `normalizacao.anos_media: 3` and `normalizacao.winsor: 0.1` present in `config.yaml`. Then the lock's
  `congelados` still match config (`test_knobs_batem_com_o_lock` green) and the 30-leaf partition is
  intact (`test_orcamento_de_knobs_e_exatamente_3` green). **No lock edit needed.** `winsor` becomes
  *inert* for the 3y base (it already was — at N=3 winsor never bites; the 3y base was already a median),
  and `anos_media` remains the Theil-Sen window.
- **If the planner instead removes `anos_media`/`winsor` from `config.yaml`** (making them fixed method):
  the lock's `congelados` list and the escopo leaf-count must be edited to 28 **in the same commit**, and
  the BLIND-03 test — which reads `cfg["normalizacao"]["anos_media"]`/`["winsor"]` — must be updated.
  This is the sanctioned path (config + lock in one commit; the BLIND-05 hook *permits* that pair) but is
  higher blast radius. **Discouraged unless there's a reason.**
- **If the planner changes the window (e.g. 3 → 5)** for robustness: that is a **congelado value change**
  → edit `normalizacao.anos_media` in `config.yaml` **and** `calibracao.lock.yaml` in the same commit
  (visible, sanctioned). This is exactly the "visible knob change" the BLIND-03 intertravamento is
  designed to surface — legitimate when paired with the method change.
- **PRIM-04 IPCA deflator is NOT a valuation knob.** It is objective BCB macro data (like `rf`), resolved
  at entry points. It must not introduce a tunable. Note GROW-02 (Fase 11) requires the IPCA *window* to
  equal the `rf` window (`rf_ciclo_anos: 10`); PRIM-04's *per-year calendar deflators* are a different
  use of the same source — keep them objective (no free choice of base year: D-03 says last-year reais).

**One-line justification rule:** any knob touch must be justified **without naming a ticker**
(`-k justificativa` test + `.githooks/commit-msg`). "Removi a winsorização da série temporal porque ela
enviesava a tendência" is legitimate; "para o CSNA3 sair do subvalorizado" is not.

---

## Validation Architecture

`workflow.nyquist_validation` is not disabled → this section applies.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (`[tool.pytest.ini_options]` in `pyproject.toml`) |
| Config | `pyproject.toml`: `xfail_strict = true`, `addopts = "-m 'not golden_nivel' --strict-markers"` |
| Quick run | `.venv/bin/python -m pytest -k normalizacao` (per CLAUDE.md: `pytest tests/arquivo.py` breaks — use `-k`) |
| Full suite | `.venv/bin/python -m pytest` (golden_nivel deselected by default) |
| Quarantine run | `.venv/bin/python -m pytest -m golden_nivel` |
| Everything | `.venv/bin/python -m pytest -m ""` |

### "Suíte verde" for Phase 10 (per CLAUDE.md v2.4)
0 failed, with `golden_nivel` quarantined, the remaining doença xfail (BLIND-02b) still xfailed, and the
jackknife skip pending Fase 14. **BLIND-03 stops being xfail here** (it flips green → remove the xfail).

### Phase Requirements → Test Map
| Req | Behavior | Test type | Command | Exists? |
|-----|----------|-----------|---------|---------|
| PRIM-01 | pure-growth series not haircut | invariante | `pytest -k normalizacao_nao_pune_crescimento` | ✅ (flip xfail→normal) |
| PRIM-01 | Theil-Sen endpoint + guard (short/negative series) | unit | new tests in `test_normalizacao.py` | ❌ Wave 0 |
| PRIM-02 | `roe_valuation` = median of annual ROEs | unit | new test asserting `roe_valuation == median(roe(a))` | ❌ Wave 0 |
| PRIM-03 | `serie_lucro_normalizada` returns raw (no winsor) | unit | new/updated test in `test_normalizacao.py` | ❌ Wave 0 |
| PRIM-04 | cyclical base deflated to last-year reais | unit | new test: real base > nominal for an inflationary series | ❌ Wave 0 |
| PRIM-04 | engine stays deterministic/offline | contrato | reuse determinism pattern | ✅ pattern exists |
| PRIM-05 | 32,88 golden absent from repo | meta | `test_backtest_alvos_recalibrados` deleted + YAML line removed | delete |

### Tests that WILL break and the required action
| Test | Class | Why it breaks | Action |
|------|-------|---------------|--------|
| `test_invariantes_v24.py::test_normalizacao_nao_pune_crescimento` | invariante | method fixed → XPASS | **remove the `xfail` decorator** |
| `test_normalizacao.py::test_outlier_alto_suavizado_pela_mediana` | invariante | asserts median suavizes a terminal outlier to 105; Theil-Sen-endpoint → 300 | **rewrite** to the new invariant (e.g. window≥5 robustness) |
| `test_normalizacao.py::test_none_ignorado_antes_de_normalizar` | contrato | asserts median 105 with an outlier | **rewrite** (keep the None-skip assertion, drop the median-105 level) |
| `test_normalizacao.py::test_apenas_os_ultimos_anos_media_entram_na_base` | invariante | survives **iff** the window is kept; breaks if window removed | keep window → survives; else rewrite |
| `test_normalizacao.py::test_serie_estavel_base_igual_ao_valor` | invariante | flat series → Theil-Sen endpoint = value | **survives** ✅ |
| `test_normalizacao.py::test_winsor_clampa_extremos_em_serie_longa` | invariante | tests the winsorized-mean (win10) path | **survives iff** the cyclical keeps the averaging estimator (recommended) |
| `test_normalizacao.py::test_serie_winsorizada_*` | invariante/contrato | if `serie_winsorizada` stays as a function, they pass; if deleted, remove them | planner decision (recommend: keep the fn, stop *calling* it for the temporal series) |
| `test_normalizacao.py::test_mediana_payout_*` | invariante/contrato | payout untouched | **survive** ✅ |
| 9 golden_nivel level-band tests (see §Golden Disambiguation) | golden_nivel | ITUB4 R$ moves | **delete** test + YAML line |

### BLIND-04a meta-test interaction (verified mechanism)
`test_blindagem_meta.py::test_nenhum_teste_de_calibracao_crava_ticker_em_reais` computes
`novos = detectar_ticker_com_valor_cravado() - (quarentenados() | xfail_estritos())`. There is **no
separate accept-list file** — tolerance *is* the `golden_nivel` classification. Deleting a golden test
**and** its YAML line removes it from both `ofensores` (AST no longer sees it) and `tolerados`
(no longer golden_nivel) simultaneously → the meta-test stays green. **No accept-list to edit.**

### Wave 0 Gaps
- [ ] `test_normalizacao.py` — new unit tests for the Theil-Sen endpoint + degeneration guard + short-series fallback (D-01b)
- [ ] `test_normalizacao.py` — rewrite the 2–3 median-specific invariants (see table)
- [ ] `test_fundamentals_consistencia.py` (or new) — `roe_valuation == median(roe(a))` and consistency with `_roe_through_cycle`
- [ ] A deflation unit test (macro deflators × cyclical base) that runs offline against stamped IPCA
- [ ] Framework install: none (scipy present)

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| scipy `theilslopes` | PRIM-01 | ✅ | 1.17.1 | (small median-of-slopes impl — not needed) |
| numpy | PRIM-01 | ✅ | ≥1.24 | — |
| BCB SGS API (IPCA) | PRIM-04 | ✅ (public, `macro.py` already calls it) | — | stamp IPCA into snapshot/cfg for offline tests |
| Clean 104 snapshot | validation | ✅ | `snapshot_sanidade_limpo_2026-07-15.yaml` | — |
| Bank snapshot | golden check | ✅ | `snapshot_bancos_2026-07-12.yaml` | — |

**No blocking gaps.** Only caveat: PRIM-04 needs a *historical annual* IPCA series that `macro.py` does
not yet fetch (it fetches the last 12-month accumulated value, SGS 13522, and a Selic date-range). See
Open Question 2.

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | **LOCKED (Open Q2):** annual calendar IPCA = **SGS 13522 sampled at December** (reuses `IPCA_12M=13522`); documented identical alternative = SGS 433 monthly compounded per year | PRIM-04 / Open Q2 (resolved) | Wrong deflators → cyclical base off; direction/materiality still hold, magnitude wrong. Test validates composition independent of series. |
| A2 | The correct Theil-Sen window is a **short** window (3–5) with a guard, not the full series | PRIM-01 | Full-series is erratic (p90 2,16×); if planner picks full, expect wide `V` swings on decliners |
| A3 | Items 8–9 of the golden list belong to Phase 10 (vs Fase 13) | Golden Disambiguation | Deleting too early removes a guard before its replacement; PRIM-05 only *needs* item 1 |
| A4 | Keeping `anos_media`/`winsor` in `config.yaml` (inert) is preferable to removing them | Knob Budget | If removed, lock + BLIND-03 test must change in the same commit (higher blast radius) |
| A5 | Deleting the 3 golden functions (not the whole `test_backtest_bancos.py`) is the intended scope | Golden Disambiguation | User may want the whole bank-backtest harness retired |

**All A-items are `[ASSUMED]` and should be confirmed in discuss-phase before locking the plan.**

---

## Open Questions (RESOLVED — see PLAN.md task gates)

1. **Theil-Sen window: 3 vs 5 vs full?** — **RESOLVED** by the Plan 10-01 checkpoint
   (`checkpoint:decision`, window 3 vs 5). Recommendation stands: **window=5 with the
   `endpoint<=0 → median` guard**; a 3→5 change is a visible, sanctioned lock edit.

2. **Which BCB SGS series for the deflators, and where do they live?** — **RESOLVED / LOCKED.**
   Series: **SGS 13522 sampled at each December** (the existing `IPCA_12M = 13522` constant in
   `macro.py:18-19`). The 12-month accumulated IPCA at the December close **is** the calendar-year
   IPCA by definition — no free choice of base year (D-03: reais do último ano). Documented identical
   alternative if a December datapoint is missing: **SGS 433** (IPCA monthly %) compounded
   `prod(1+m/100)` per calendar year, which yields the same calendar-year figure. Offline discipline
   is locked too: resolve at entry points and stamp into `cfg`/snapshot, mirroring `rf` (Pattern 3 /
   Pitfall 4). Cited concretely in Plan 10-03 Task 1's action; the test validates the compositional
   math independent of the series, so correctness does not hinge on the choice — only numeric precision
   does, and 13522-at-December is exact.

3. **Does removing winsor from the temporal series leave `norm.serie_winsorizada` orphaned?** —
   **RESOLVED** by the baked design (Plan 10-02): keep `norm.serie_winsorizada` alive
   (`screening.py:253,272` still uses it — Cap. 8 elegibilidade, out of PRIM scope) and make
   `fundamentals.serie_lucro_normalizada` return the raw series.

4. **CSNA3 with a negative recent year — is the guard's `median` fallback acceptable for valuation?** —
   **RESOLVED** by the baked design: the `endpoint<=0 → median(v)` guard (Plan 10-01) only protects the
   growth-base path from NaN; PRIM-04's deflated cyclical engine (Plan 10-03) is the intended home for
   genuinely loss-recent tickers.

---

## State of the Art

| Old approach | Phase 10 approach | Impact |
|--------------|-------------------|--------|
| `base_normalizada` = `median()` of last 3 (middle year) | Theil-Sen endpoint at current year | stops the −9,1% growth haircut; BLIND-03 green |
| `roe_valuation` = normalized-lucro(3y) ÷ PL(last) | median of annual `roe(a)` (full series) | no cross-basis; consistent with `_roe_through_cycle`; 32,88 breaks |
| `serie_lucro_normalizada` winsorized | raw series | winsor bias off; robust `g` deferred to Fase 11 |
| cyclical base summed in nominal reais | IPCA-deflated to last-year reais | CSNA3 base +49,6% |

**Deprecated by this phase:** the 9 ITUB4 level-band golden tests; the `winsor`/`anos_media`-as-live-knob
mental model for the valuation base (they become fixed method — winsor was already inert at N=3).

---

## Sources

### Primary (HIGH — executed / read this session)
- Live execution over `tests/fixtures/snapshot_sanidade_limpo_2026-07-15.yaml` (104 tickers) and
  `snapshot_bancos_2026-07-12.yaml` — all before/after numbers `[VERIFIED: execution 2026-07-15]`.
- `src/analista/core/normalizacao.py`, `fundamentals.py` (roe/roe_valuation/base_lucro_normalizada),
  `growth.py`, `motores.py`, `report.py` (`_intrinseco_por_motor`, `_roe_through_cycle`), `ingest/macro.py`.
- `tests/test_invariantes_v24.py` (BLIND-03/02), `test_backtest_bancos.py`, `test_normalizacao.py`,
  `helpers_blindagem.py` (BLIND-04a detector), `helpers_sanidade.py` (loader), `tests/classificacao.yaml`,
  `tests/conftest.py` (completeness), `pyproject.toml`, `config.yaml`, `calibracao.lock.yaml`.
- `.venv` import check: `scipy 1.17.1`, `theilslopes` present `[VERIFIED]`.

### Secondary (MEDIUM)
- CONTEXT.md (D-01..D-04), REQUIREMENTS.md (PRIM-01..05, BLIND-03), ROADMAP.md §Phase 10, CLAUDE.md
  ("suíte verde" v2.4), MEMORY.md (`duas-doencas-do-valuation`, `rim-terminal-value-root-cause`).

### Tertiary (LOW — flagged)
- Approximate calendar IPCA values used in the CSNA3 deflation demo (hand-entered) — planner must pull
  the real BCB series.

---

## Metadata

**Confidence breakdown:**
- Standard stack (scipy/theilslopes present, no new deps): **HIGH** — verified by import.
- Estimator behaviour + 32,88 break + roe target: **HIGH** — executed on real snapshots.
- Exact IPCA magnitudes for PRIM-04: **MEDIUM** — direction verified, values approximate.
- Which of golden items 8–9 belong to Phase 10: **MEDIUM** — item 1 is the hard exit criterion.
- Window choice (3/5/full): **MEDIUM** — tradeoff measured; final pick is a discuss-phase decision.

**Research date:** 2026-07-15
**Valid until:** ~2026-08-15 for the numerical findings (stable; tied to the frozen snapshots). Re-run the
validation scripts if the clean snapshot is regenerated.
