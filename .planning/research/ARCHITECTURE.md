# Architecture Research

**Domain:** Consultative technical indicators on top of a fundamentalist dividend-analysis engine (Python + Streamlit, B3 stocks)
**Researched:** 2026-06-24
**Confidence:** HIGH (grounded in the actual v1.1 code; mirrors a pattern the codebase already shipped for `serie_precos`)

## Verdict (one line)

Indicators are COMPUTED in a new pure engine module `src/analista/core/indicators.py`, fed by a full OHLC DataFrame threaded through the SAME existing yfinance fetch (`DadosMercado.ohlc` → `CompanyData.ohlc`), exposed on `AnaliseAcao` as a nested `SinaisTecnicos` dataclass produced inside `report.analisar_acao` (the single source of truth that CLI and UI already share). `app.py` only READS `a.sinais` and renders the user-selected subset — it never recomputes. Caching is free because all of it runs inside the already-cached `montar()` → `analisar_acao()` path.

This is the **exact same threading pattern** v1.1 used to ship the price chart (`serie_precos`), upgraded from a single `Close` Series to a full OHLC frame. No new network calls.

## Standard Architecture

### System Overview (current + v1.2 additions marked ▲)

```
┌──────────────────────────────────────────────────────────────────────┐
│  PRESENTATION (read-only)                                             │
│  ┌──────────────────┐                    ┌──────────────────────┐     │
│  │ app.py (Streamlit)│  same engine call │ cli.py (analyze cmd) │     │
│  │  Analisar tab     │◄──────────────────►│  prints signals ▲   │     │
│  │  - Plotly overlay▲│                    └──────────────────────┘     │
│  │  - toggles ▲      │   READS a.sinais.*  (NEVER recomputes)          │
│  │  - timing summary▲│                                                 │
│  │  - reverify alert▲│                                                 │
│  └────────┬─────────┘                                                 │
├───────────┼──────────────────────────────────────────────────────────┤
│  ENGINE (single source of truth)                                     │
│  ┌────────▼─────────────────────────────────────────────────────┐    │
│  │ report/report.py : analisar_acao(c, cfg) -> AnaliseAcao       │    │
│  │   ...existing valuation (DDM/CAPM/múltiplos) UNTOUCHED...     │    │
│  │   + a.sinais = indicators.calcular(c.ohlc, cfg) ▲            │    │
│  └────────┬──────────────────────────────────────────────────────┘   │
│  ┌────────▼──────────────────┐  ┌──────────────────────────────┐     │
│  │ core/indicators.py ▲      │  │ core/ ddm capm multiples ...  │     │
│  │  pure: OHLC -> series+sig │  │  (unchanged)                  │     │
│  └────────┬──────────────────┘  └──────────────────────────────┘     │
├───────────┼──────────────────────────────────────────────────────────┤
│  INGEST                                                               │
│  ┌────────▼─────────────────────────────────────────────────────┐    │
│  │ ingest/build.py montar_empresa -> CompanyData (+ .ohlc ▲)     │    │
│  │ ingest/prices.py coletar_mercado -> DadosMercado (+ .ohlc ▲)  │    │
│  │   tk.history(period="5y", auto_adjust=False)  ← SAME fetch    │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | v1.2 change |
|-----------|----------------|-------------|
| `ingest/prices.py` | Fetch Yahoo OHLCV once; build `DadosMercado` | **MODIFY**: keep full OHLC frame in `dm.ohlc` (already has `hist`; today it discards everything but `Close`) |
| `ingest/build.py` | Assemble `CompanyData` from CVM + market | **MODIFY**: copy `dm.ohlc` → `c.ohlc` (one line, mirrors `c.serie_precos = dm.serie_precos`) |
| `core/fundamentals.py` (`CompanyData`) | Carry data into the engine | **MODIFY**: add `ohlc: Optional["pd.DataFrame"] = None` field (forward-ref, no top-level pandas import) |
| `core/indicators.py` | **NEW**: pure functions OHLC → indicator series + discrete signals | **NEW FILE** |
| `report/report.py` | Compute `AnaliseAcao`; single source of truth | **MODIFY**: add `SinaisTecnicos` dataclass + `a.sinais = indicators.calcular(...)`; valuation code untouched |
| `app.py` | Render Analisar tab; READ-ONLY | **MODIFY**: toggles + overlay traces + timing summary + reverify alert, all reading `a.sinais` |
| `cli.py` | CLI parity | **MODIFY**: `cmd_analyze`/`relatorio_markdown` print the same signals |

## Recommended Project Structure

```
src/analista/
├── core/
│   ├── indicators.py        ▲ NEW — pure OHLC -> SinaisTecnicos (no I/O, no Streamlit)
│   ├── ddm.py capm.py multiples.py growth.py lifecycle.py ...  (unchanged)
│   └── fundamentals.py      △ MODIFY — CompanyData gains `ohlc` field
├── ingest/
│   ├── prices.py            △ MODIFY — DadosMercado gains `ohlc`; keep full frame
│   └── build.py             △ MODIFY — thread dm.ohlc -> c.ohlc
├── report/
│   └── report.py            △ MODIFY — SinaisTecnicos dataclass + a.sinais; markdown section
└── cli.py                   △ MODIFY — print signals in analyze
app.py                       △ MODIFY — toggles, Plotly overlays, timing + reverify alert
tests/
└── test_indicators.py       ▲ NEW — golden tests for the pure module
└── test_consistencia_modos.py  △ MODIFY (optional) — assert CLI/UI read same a.sinais
```

### Structure Rationale

- **`core/indicators.py` lives next to `ddm.py`/`multiples.py`**: it is a *pure* domain calculator (input data → numbers/labels), exactly like the other `core/` modules. It must have **no Streamlit, no I/O, no network** — that is what makes it CLI-shareable and golden-testable.
- **OHLC rides the existing fetch, not a new one**: `prices.coletar_mercado` already calls `tk.history(period="5y", auto_adjust=False)` and binds it to `hist`. v1.1 kept only `hist["Close"]` as `serie_precos`. ADX/Donchian/Bollinger need High/Low; the data is **already in memory** — we just stop throwing it away. Zero new network calls, zero new rate-limit exposure.
- **Signals computed inside `analisar_acao`**: this function is the one place CLI (`cli.cmd_analyze`) and UI (`app.py`) both call. Putting indicators there guarantees parity for free and keeps `app.py` read-only.

## Architectural Patterns

### Pattern 1: Thread-through data plumbing (mirror `serie_precos`)

**What:** Carry the OHLC frame the same way the Close series was carried in v1.1 — as an optional field on each dataclass in the chain, copied one hop at a time. Use **forward-ref type hints** so the engine never imports pandas at module top (matches `serie_precos: Optional["pd.Series"]`).

**When:** Always for this milestone — it is the locked convention.

**Trade-offs:** A few extra fields; negligible. Avoids any second fetch and keeps the lazy-pandas import discipline (`import pandas as pd` only inside functions / inside `app.py`).

**Example:**
```python
# ingest/prices.py — DadosMercado
ohlc: Optional["pd.DataFrame"] = None   # OHLCV 5a nominal (Open/High/Low/Close/Volume)

# inside coletar_mercado, where `hist` already exists:
if hist is not None and not hist.empty:
    nominal = hist["Close"].dropna()
    dm.serie_precos = nominal                 # v1.1, unchanged
    dm.ohlc = hist[["Open", "High", "Low", "Close", "Volume"]].dropna()  # v1.2 ▲

# ingest/build.py — montar_empresa
c.serie_precos = dm.serie_precos              # existing
c.ohlc = dm.ohlc                              # v1.2 ▲ (one line)

# core/fundamentals.py — CompanyData
ohlc: Optional["pd.DataFrame"] = None         # forward-ref; no top-level pandas
```

### Pattern 2: Pure indicator module → discrete signals dataclass

**What:** `indicators.calcular(ohlc, cfg) -> SinaisTecnicos` returns BOTH the plot-ready series (so the UI can overlay them) AND the discrete, human-readable signals/labels (so CLI can print them and the UI can show the timing summary + reverify alert). All thresholds (periods 20/50/200, RSI bounds, ADX cutoff) come from `cfg` so they live in `config.yaml` like every other parameter.

**When:** The core of v1.2.

**Trade-offs:** Returning pandas Series in a dataclass that's cached by Streamlit is fine (Series are picklable; `montar` already caches a `CompanyData` holding a Series). Keep the discrete signals as plain Python (`str`/`float`/`bool`) so CLI printing and tests don't need pandas.

**Example (shape, not final):**
```python
# core/indicators.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class SinaisTecnicos:
    # plot-ready series (UI overlays these; None when OHLC missing)
    series: Dict[str, "pd.Series"] = field(default_factory=dict)   # "SMA20","EMA50","BB_sup","DONCH_max",...
    # discrete signals (CLI prints / UI summarizes — plain Python)
    tendencia: Optional[str] = None         # "alta" | "baixa" | "lateral"  (ADX + slope)
    adx: Optional[float] = None
    cruzamento: Optional[str] = None        # "golden_cross" | "death_cross" | None
    preco_vs_mm200: Optional[str] = None     # "acima" | "abaixo"
    rsi: Optional[float] = None             # 0-100
    macd_sinal: Optional[str] = None         # "compra" | "venda" | None
    rompimento: Optional[str] = None         # "rompeu_topo" | "rompeu_fundo" | None
    timing_entrada: Optional[str] = None     # consultive summary string
    alerta_reverificacao: Optional[str] = None  # set when price loses trend (e.g. < MM200)

def calcular(ohlc, cfg) -> SinaisTecnicos:
    s = SinaisTecnicos()
    if ohlc is None or ohlc.empty:
        return s                  # graceful degradation, mirrors GRAF-03
    import pandas as pd          # lazy, inside the function
    close = ohlc["Close"]
    # ... SMA/EMA, crossovers, Donchian, Bollinger, ADX+slope, RSI, MACD ...
    return s
```

### Pattern 3: Read-only UI with widget-driven view, not widget-driven compute

**What:** Streamlit toggles (`st.checkbox` / `st.multiselect`) select WHICH precomputed series to draw. The chart re-renders by adding `go.Scatter` traces from `a.sinais.series[name]` — it never calls `indicators.calcular`. Toggling an indicator triggers a Streamlit rerun, but `montar()` (and therefore `analisar_acao` if you keep it in the cached path — see Caching) returns the cached object, so flipping a checkbox is instant and computes nothing.

**When:** The entire UI layer of v1.2.

**Trade-offs:** Widget state lives in `st.session_state` (implicit via widget keys) and survives reruns within a session. This is exactly the "app.py read-only" rule the project locked in Phase 2 (Key Decision: *"app.py é read-only: só lê campos da engine, nunca recalcula método"*). Indicators are method-adjacent; treat them identically.

**Example:**
```python
# app.py — after `a = report.analisar_acao(c, CFG)`  (a.sinais already computed)
disponiveis = ["Médias móveis", "Canais (Donchian/Bollinger)", "ADX/Inclinação", "RSI/MACD"]
escolhidos = st.multiselect("Indicadores no gráfico", disponiveis, default=[])
# build the price fig exactly as v1.1, then:
if "Médias móveis" in escolhidos:
    for nome in ("SMA20", "SMA50", "SMA200"):
        serie = a.sinais.series.get(nome)
        if serie is not None:
            fig.add_trace(go.Scatter(x=serie.index, y=serie.values, name=nome, mode="lines"))
# ... same per family ...
if a.sinais.alerta_reverificacao:
    st.warning(f"⚠️ {esc_md(a.sinais.alerta_reverificacao)}")
if a.sinais.timing_entrada:
    st.info(f"⏱️ Timing (consultivo): {a.sinais.timing_entrada}")
```

## Data Flow

### Analisar-tab flow (v1.2)

```
[User types ticker, clicks Analisar]
    ↓
montar(ticker, ANO_BASE, N_ANOS)            ← @st.cache_data ttl=3600
    ↓  build.montar_empresa
prices.coletar_mercado  →  ONE yfinance fetch (5y OHLCV)  →  dm.ohlc
    ↓
CompanyData c (now carries c.ohlc + c.serie_precos)
    ↓
report.analisar_acao(c, CFG)
    ├─ DDM/CAPM/múltiplos  (unchanged)  → a.vmin/a.vmax/a.veredito
    └─ indicators.calcular(c.ohlc, CFG) → a.sinais (series + discrete signals)
    ↓
app.py reads a.* and a.sinais.* only  →  Plotly overlay (selected subset)
                                          + timing summary + reverify alert
CLI: cmd_analyze → analisar_acao → relatorio_markdown prints a.sinais (parity)
```

### State management (Streamlit)

```
Widget keys (multiselect/checkbox) → st.session_state (per session)
        ↓ rerun
app.py re-reads CACHED CompanyData/AnaliseAcao  → redraws traces from a.sinais.series
        (no recomputation; no network)
```

### Key data flows

1. **OHLC reuse:** the `hist` DataFrame already fetched in `coletar_mercado` is preserved as `dm.ohlc` instead of being reduced to `Close`. This is the only new data the indicators need, and it costs zero requests.
2. **Single computation site:** `analisar_acao` computes `a.sinais` once; both CLI and UI consume it. Parity is structural, not duplicated.

## Caching Considerations

- **The ~1h cache is on `montar()`** (`@st.cache_data ttl=3600`), which returns `CompanyData`. `report.analisar_acao` is currently called **outside** the cache, on every rerun, in `app.py` (line ~99). Today that's cheap (pure arithmetic). Adding indicators makes it slightly heavier but still pure-CPU on an in-memory 5y frame (~1250 rows) — fine on a rerun.
- **Recommendation:** keep `indicators.calcular` inside `analisar_acao` (engine-owned). If profiling shows toggle-rerun lag, wrap the analysis in a tiny cached helper in `app.py` (e.g. `@st.cache_data def analisar_cached(ticker, ...): return report.analisar_acao(montar(...), CFG)`), keyed by inputs — this caches the whole `AnaliseAcao` including `a.sinais` so checkbox flips never recompute. Do NOT compute indicators directly in `app.py`: that would (a) violate the read-only rule and (b) recompute on every rerun (thrash).
- **No new cache entries needed for OHLC** — it travels inside the already-cached `CompanyData`.

## CLI Parity

`cli.cmd_analyze` already does `a = report.analisar_acao(c, cfg)` then `relatorio_markdown(c, a, cfg)`. Because `a.sinais` is now part of `AnaliseAcao`, the CLI gets it automatically. Add a "## Sinais técnicos (consultivos)" section to `relatorio_markdown` that prints `a.sinais.tendencia`, `cruzamento`, `rsi`, `timing_entrada`, and the reverify alert. This satisfies the "CLI espelhando a engine da UI" validated requirement with no logic duplication.

## Suggested Build Order (dependency-respecting)

1. **Data plumbing (no behavior change).** Add `ohlc` to `DadosMercado` (`prices.py`), populate from existing `hist`; add `ohlc` to `CompanyData` (`fundamentals.py`, forward-ref); copy in `build.py`. Verify existing 64 golden tests still green. *Depends on: nothing. Lowest risk.*
2. **Indicator engine.** Create `core/indicators.py` with `SinaisTecnicos` + `calcular(ohlc, cfg)` covering the 4 families. Add config keys to `config.yaml`. *Depends on: step 1 (needs OHLC type) for integration, but the pure functions can be written/tested against synthetic frames in parallel.*
3. **Engine integration + signals/summary.** In `report.analisar_acao`, set `a.sinais = indicators.calcular(c.ohlc, cfg)`; derive `timing_entrada` and `alerta_reverificacao`. Keep valuation untouched. *Depends on: 1, 2.*
4. **UI overlay + toggles.** In `app.py`, add `st.multiselect`/checkboxes and add Plotly traces from `a.sinais.series`; render the timing summary. Read-only. *Depends on: 3.*
5. **Sell/reverify alert.** Surface `a.sinais.alerta_reverificacao` (e.g. price < MM200) as an `st.warning` near the veredito, worded as "reveja os fundamentos" (never overrides the fundamentalist verdict). *Depends on: 3, 4.*
6. **CLI parity.** Extend `relatorio_markdown` to print the signals. *Depends on: 3.*
7. **Tests.** `tests/test_indicators.py` golden values (known OHLC → known SMA/RSI/etc.); optionally extend `test_consistencia_modos.py` to assert CLI/UI read the same `a.sinais`. *Depends on: 2, 3.*

## Anti-Patterns

### Anti-Pattern 1: Computing indicators in `app.py`

**What people do:** Call a `ta`/pandas indicator inside the Streamlit render block so the chart "just shows" the line.
**Why it's wrong:** Violates the locked "app.py read-only / engine is single source of truth" rule; recomputes on every rerun (toggle thrash); breaks CLI parity (CLI would never see those signals).
**Do this instead:** Compute in `core/indicators.py` via `analisar_acao`; `app.py` reads `a.sinais`.

### Anti-Pattern 2: A second yfinance fetch for OHLC

**What people do:** Add `tk.history(...)` inside the indicator code to "get High/Low".
**Why it's wrong:** Doubles Yahoo requests, worsens the known intermittent rate-limit (the very reason `prices.py` has retry/backoff), and risks a different time window than the chart.
**Do this instead:** Preserve the `hist` frame already fetched in `coletar_mercado` as `dm.ohlc`. Zero new calls.

### Anti-Pattern 3: Letting a technical signal flip the veredito

**What people do:** Downgrade a "SUBAVALIADA" to a sell because RSI is high.
**Why it's wrong:** Contradicts the project's founding principle and the explicit Key Decision that technicals are **consultivos** and never overwrite the fundamentalist verdict.
**Do this instead:** Keep `a.veredito` (DDM/múltiplos) authoritative; technicals only populate `timing_entrada` and `alerta_reverificacao` ("reveja os fundamentos").

### Anti-Pattern 4: Importing pandas/numpy at the top of `core/indicators.py` "for convenience"

**What people do:** `import pandas as pd` at module top of an engine file.
**Why it's wrong:** The engine deliberately defers heavy imports (lazy `import pandas as pd` inside functions; `_yf()` helper; forward-ref `"pd.Series"` hints) so importing the engine stays light and testable. `numpy` is the one accepted top-level dep (`comparables.py`), so numpy-only math is OK; reach for pandas lazily inside `calcular`.
**Do this instead:** `import pandas as pd` inside `calcular`; use forward-ref hints for any `pd.*` field types.

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `prices.py` → `build.py` | `DadosMercado.ohlc` field | mirror `serie_precos` copy; one line |
| `build.py` → `report.py` | `CompanyData.ohlc` field | engine never re-fetches |
| `indicators.py` → `report.py` | `calcular(ohlc, cfg) -> SinaisTecnicos` | pure; cfg-driven thresholds |
| `report.py` → `app.py` | read `a.sinais.*` | READ-ONLY (locked rule) |
| `report.py` → `cli.py` | `relatorio_markdown` prints `a.sinais` | parity, no duplication |
| `config.yaml` → `indicators.py` | periods/thresholds | same convention as `cfg["ddm"]`, `cfg["capm"]` |

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Yahoo Finance (yfinance) | **No change** — reuse the single 5y OHLCV fetch in `coletar_mercado` | Has retry/backoff for intermittent rate-limit; do not add a 2nd call |

## Confidence Assessment

| Area | Confidence | Why |
|------|------------|-----|
| Data plumbing (`ohlc` threading) | HIGH | Verbatim mirror of the `serie_precos` pattern already in the code (prices.py L58/108, build.py L41, fundamentals.py L45) |
| Engine compute site (`analisar_acao`) | HIGH | Confirmed it's the single function CLI (cli.py L65) and UI (app.py L99) both call |
| Read-only UI / toggles | HIGH | Locked Key Decision (PROJECT.md L119); Streamlit multiselect/session_state is the standard mechanism |
| Caching | HIGH | `montar` is `@st.cache_data ttl=3600` (app.py L34); OHLC rides inside it |
| Indicator math libraries | MEDIUM | Recommend numpy/pandas-native implementations (no new dep, keeps custom-zero discipline); a `ta`/`pandas-ta` dependency is optional and out of this doc's scope — flag for STACK.md |

## Sources

- Actual codebase (read 2026-06-24): `src/analista/ingest/prices.py`, `ingest/build.py`, `core/fundamentals.py`, `report/report.py`, `cli.py`, `app.py`
- `.planning/PROJECT.md` — Key Decisions (app.py read-only; técnico consultivo; reverify-not-sell), Constraints (custo zero, golden tests must pass)

---
*Architecture research for: consultative technical indicators on a fundamentalist dividend engine*
*Researched: 2026-06-24*
