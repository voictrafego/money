# Architecture Research

**Domain:** Streamlit fundamentals app (Analista de Dividendos) — adding a NEW, separate technical swing-setup page (Murphy method) on top of an existing pure-engine + read-only-UI architecture
**Researched:** 2026-06-29
**Confidence:** HIGH (design derived from reading the actual codebase: `app.py`, `report/report.py`, `core/indicators.py`, `ingest/prices.py`, `ingest/build.py`, `grafico.py`, `config.yaml`). MEDIUM on yfinance intraday limit specifics (flagged inline).

---

## Standard Architecture (as it exists today)

The codebase already enforces a clean 4-layer separation. The swing page must slot into it without bending any layer.

```
┌──────────────────────────────────────────────────────────────────────┐
│  UI LAYER — app.py (Streamlit)                                         │
│  RULE (Phase 2): READ-ONLY. Only reads fields off engine dataclasses;  │
│  never recomputes method, never hardcodes levels. Converts specs→traces│
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  [ NEW 4th menu ]      │
│  │ 🔎 Analisar│  │ ⛏️ Garimpar │  │ 📊 Ranking │  │ 📐 Swing setup │   │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘   │
├────────┼───────────────┼───────────────┼─────────────────┼────────────┤
│  SPEC LAYER — grafico.py (PURE: no streamlit/plotly)                   │
│  Decides WHAT to draw → OverlaySpec / SubpainelSpec / Marcador / layout │
│              [ NEW: candle + S/R + Fib + pattern-shape + zone specs ]   │
├────────────────────────────────────────────────────────────────────────┤
│  REPORT LAYER — report/report.py  →  AnaliseAcao + analisar_acao()      │
│  Orchestrates core into one verdict dataclass.  [ DO NOT TOUCH ]        │
│              [ NEW: report/setup.py → SetupSwing + montar_setup() ]     │
├────────────────────────────────────────────────────────────────────────┤
│  CORE LAYER — pure math (no I/O, no streamlit). Golden-tested.          │
│  ddm capm fundamentals growth screening lifecycle comparables          │
│  multiples normalizacao  indicators(SinaisTecnicos, timeframe-agnostic) │
│              [ NEW: core/setups.py → S/R · Fib · patterns · score · R:R]│
├────────────────────────────────────────────────────────────────────────┤
│  INGEST LAYER — ingest/ (the only layer that hits the network)         │
│  cvm · prices(coletar_mercado → 5y daily OHLCV) · macro · universe ·    │
│  build(montar_empresa → CompanyData)  [ daily pipeline UNTOUCHED ]      │
│              [ NEW: prices.coletar_ohlc(ticker, timeframe) — isolated ] │
└────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities (existing — confirmed by reading the code)

| Component | Responsibility | Key fact for integration |
|-----------|----------------|--------------------------|
| `core/indicators.py` | `calcular(ohlc, cfg) -> SinaisTecnicos` (4 families: Tendência/Canais/Força/Momentum) | **Already timeframe-agnostic** — "recebe o frame que lhe derem; o resample é da Phase 6". Reuse verbatim for the swing page's trend context + oscillators. |
| `report/report.py` | `analisar_acao(c, cfg) -> AnaliseAcao` — the fundamental verdict + consultative timing | The W-FRI resample + composite decision tree live here. **This is the fundamental tab; leave it byte-for-byte intact.** |
| `grafico.py` | Pure spec builders (`overlays_preco`, `subpaineis_ativos`, `marcadores_eventos`, `layout_subplots`) returning dataclasses, NOT figures | No streamlit/plotly import. app.py turns specs into traces. New chart elements follow the same spec pattern. |
| `ingest/prices.py` | `coletar_mercado(ticker)` → 5y daily `auto_adjust=False`: `serie_precos`, `ohlc`, `ohlc_ajustado` (split-only via `_ajustar_por_split`) | Single daily fetch builds the fundamental `DadosMercado`. **Do not add intraday branches here.** Reuse `_ajustar_por_split` (it is pure). |
| `ingest/build.py` | `montar_empresa()` wires CVM + prices into `CompanyData` | Fundamental assembly; the swing page does NOT need CompanyData. |
| `app.py` | Read-only render; sidebar `st.radio` (3 modes); `montar()` is `@st.cache_data(ttl=3600)`; `session_state["tec_estado"]` holds toggle state | The page-add pattern, cache pattern, and session_state pattern are all already here to copy. |

---

## Recommended Structure for the New Page

```
src/analista/
├── core/
│   ├── indicators.py        # EXISTING — reused as-is for trend context + oscillators
│   └── setups.py            # NEW (pure): S/R pivots · Fibonacci · chart patterns
│                            #             · entry-zone/stop/target · R:R · quality score
├── ingest/
│   └── prices.py            # MODIFIED (additive only): + coletar_ohlc(ticker, timeframe)
│                            #   reuses _ajustar_por_split; coletar_mercado() UNCHANGED
├── report/
│   ├── report.py            # UNTOUCHED (fundamental verdict)
│   └── setup.py             # NEW: SetupSwing dataclass + montar_setup(ohlc, cfg, timeframe)
├── grafico.py               # MODIFIED (additive only): + candle/S-R/Fib/pattern/zone specs
├── glossario.py             # MODIFIED (additive): + tooltip keys for new terms (setup_*, fib_*, …)
└── ...
config.yaml                  # MODIFIED (additive): + `setups:` block + timeframe→interval/period map
app.py                       # MODIFIED: + 4th radio option + new render block (read-only)
cli.py                       # OPTIONAL MODIFIED: mirror montar_setup for parity (like analisar_acao)
tests/
├── test_setups.py           # NEW: golden tests for core/setups.py
├── test_setup_report.py     # NEW: golden tests for SetupSwing assembly + degradation
├── test_ingest_intraday.py  # NEW: timeframe→interval/period map + split-adjust + empty-frame
└── test_grafico_setup.py    # NEW: spec builders for the swing chart (mirror test_grafico_ui)
```

### Structure Rationale

- **`core/setups.py` (single new pure module):** all new method math (pivots, Fibonacci ratios, pattern geometry, scoring weights, R:R) lives in ONE place, golden-tested, with zero streamlit/plotly/network imports — exactly like `indicators.py`. It **consumes** `indicators.calcular()` output for trend/oscillator context rather than re-deriving MMs/RSI. Split into `core/levels.py` only if S/R+Fib grows past ~300 lines; start unified.
- **`report/setup.py` (new, parallel to `report.py`):** keeps the fundamental orchestrator untouched. `SetupSwing` is a brand-new dataclass — the swing page never imports or mutates `AnaliseAcao`. This is the architectural firewall that guarantees "fundamental verdict + Analisar tab untouched."
- **`prices.coletar_ohlc` (additive function, not a branch in `coletar_mercado`):** isolates intraday's different fetch shape (interval/period, tighter Yahoo limits, no beta/dividends/info) from the daily 5y pipeline that feeds the whole fundamental side.
- **`grafico.py` additive specs:** the swing chart needs candles + horizontal levels + pattern shapes, but the existing spec→trace contract already proves out for overlays/subpanels. New builders return new spec dataclasses; app.py stays a thin renderer.

---

## Architectural Patterns to Follow

### Pattern 1: New pure dataclass, exposed by the engine (preserves read-only-UI)

**What:** The engine computes a `SetupSwing` and the page only reads its fields — same contract as `AnaliseAcao`.
**Why:** It is the mechanism that lets app.py stay read-only. app.py must never call `setups.detectar_padroes()` or hardcode a Fibonacci ratio.

```python
# report/setup.py  (NEW — sketch, not final)
@dataclass
class NivelPreco:
    valor: float
    tipo: str            # "suporte" | "resistencia" | "entrada" | "stop" | "alvo" | "fib_0.618"
    origem: str          # "pivot" | "fibonacci" | "padrao" | "donchian"

@dataclass
class SinalChecklist:
    chave: str           # "rompimento" | "cruz_mm" | "rsi" | "macd" | "padrao" | "volume"
    rotulo: str          # PT label for the UI
    disparado: bool      # liga/desliga
    detalhe: str         # short read-only explanation

@dataclass
class PadraoGrafico:
    tipo: str            # "oco" | "topo_duplo" | "fundo_duplo" | "triangulo" | "bandeira"
    pontos: list         # (data, preço) pivots that define the shape — for grafico.py to draw
    alvo_projetado: Optional[float]
    confirmado: bool

@dataclass
class SetupSwing:
    ticker: str
    timeframe: str                       # "diario" | "1h" | "30m" | "5m"
    contexto: "indicators.SinaisTecnicos" # REUSED, not recomputed
    niveis: list[NivelPreco]
    entrada: Optional[float]
    stop: Optional[float]
    alvo: Optional[float]
    risco_retorno: Optional[float]       # R:R from entrada/stop/alvo
    score: Optional[float]               # quality score 0–100
    checklist: list[SinalChecklist]
    padroes: list[PadraoGrafico]
    disponivel: bool                     # False ⇒ degraded (short history / Yahoo fail)
    aviso_dados: str                     # "~15min de atraso · histórico 5m ≈ 60 dias", etc.

def montar_setup(ohlc: "pd.DataFrame", cfg: dict, timeframe: str) -> SetupSwing:
    sinais = indicators.calcular(ohlc, cfg)          # reuse — trend/oscillator context
    niveis = setups.suporte_resistencia(ohlc, cfg)   # pure
    padroes = setups.detectar_padroes(ohlc, cfg)     # pure
    ...                                              # entry/stop/alvo, R:R, score
    return SetupSwing(...)                            # degrade gracefully, never raise
```

**Trade-off:** one more dataclass + orchestrator to maintain, but it is the only design that keeps the read-only rule and the fundamental firewall both intact.

### Pattern 2: Spec → trace (extend `grafico.py`, never draw in app.py)

**What:** `grafico.py` decides which candles/S-R lines/Fib levels/pattern shapes/zones to draw and returns spec dataclasses; app.py loops and emits Plotly traces — exactly as it already does for `OverlaySpec`/`SubpainelSpec`/`Marcador`.
**When:** Every visual element of the new chart.
**Why:** Visual verification in Streamlit is hard to automate; the codebase deliberately pushes "what to draw" into pure, golden-tested functions (`test_grafico_ui.py`). New builders: `candles_setup(ohlc)`, `niveis_horizontais(setup)` (S/R + entry/stop/alvo + Fib as `add_hline`/`add_hrect`), `formas_padroes(setup)` (pattern pivots as line shapes/annotations). Reuse `overlays_preco`/`subpaineis_ativos` for the MMs/RSI/MACD the user toggles on.

**Trade-off:** the swing chart uses a **candlestick** main trace (`go.Candlestick`) instead of the fundamental tab's line trace — a new render branch in app.py, but the spec contract is unchanged.

### Pattern 3: Manual Refresh via cache-busting nonce (not `ttl` alone, not global `.clear()`)

**What:** Intraday data must be cached (so toggles/timeframe re-reads don't re-hit Yahoo every rerun) yet a manual "🔄 Atualizar" must force a refetch. Use a `session_state` nonce as an extra cache-key arg.
**Why:** `@st.cache_data` keys on args. A nonce the button increments changes the key for THIS ticker/timeframe only; `func.clear()` would nuke every cached ticker. Pair with a short `ttl` because intraday is ~15 min delayed anyway.

```python
@st.cache_data(show_spinner=False, ttl=300)          # NEW — short TTL for intraday
def montar_setup_cached(ticker, timeframe, nonce):    # nonce only busts the cache
    ohlc = prices.coletar_ohlc(ticker, timeframe)     # network in ingest, not in app
    return report_setup.montar_setup(ohlc, CFG, timeframe)

st.session_state.setdefault("setup_nonce", 0)
if st.button("🔄 Atualizar"):
    st.session_state["setup_nonce"] += 1              # forces a fresh fetch for this key
setup = montar_setup_cached(ticker, timeframe, st.session_state["setup_nonce"])
```

**Trade-off:** the nonce is a tiny bit of UI state, but it gives a precise, per-key refresh that respects the read-only rule (app still only *reads* `SetupSwing`).

---

## Data Flow

### New page flow (mirrors the existing ingest→core→report→app spine)

```
[User picks ticker + timeframe, clicks Analisar / Atualizar]
        ↓
ingest/prices.coletar_ohlc(ticker, timeframe)        # ONLY OHLCV; split-adjusted; isolated
        ↓  (split-only-adjusted DataFrame, native interval — no resample needed)
core/indicators.calcular(ohlc, cfg)  ── trend/oscillator context (REUSED)
core/setups.suporte_resistencia / detectar_padroes / fibonacci / score / risco_retorno
        ↓
report/setup.montar_setup(...) → SetupSwing          # one read-only dataclass
        ↓
grafico.candles_setup / niveis_horizontais / formas_padroes (+ existing overlays/subpaineis)
        ↓
app.py renders Candlestick + hlines/hrects + pattern shapes + checklist + score + R:R
        (read-only: only reads SetupSwing fields; @st.cache_data + nonce; ~15min delay banner)
```

### Why no resample for intraday (contrast with the fundamental tab)

`report.py` resamples daily→W-FRI for the **fundamental** consultative timing. The swing page asks Yahoo for the **native** interval (`1d`/`60m`/`30m`/`5m`), so `montar_setup` feeds that frame straight into `indicators.calcular` (already timeframe-agnostic). No W-FRI resample, no touching `report.py`. Note: `config.indicadores` params (RSI14/SMA200/MACD12-26-9/squeeze126/regressão90) are **bar-count** based — they apply per-bar on whatever interval is chosen; the UI should make clear "200" means 200 bars *of the selected timeframe*.

### Ingest extension detail (the isolation that protects the daily pipeline)

```python
# ingest/prices.py — NEW function, additive; coletar_mercado() unchanged
_TIMEFRAME_YF = {            # → (yf interval, yf period)   [MEDIUM confidence: verify live]
    "diario": ("1d", "2y"),
    "1h":     ("60m", "730d"),   # yfinance: 60m history ~730d
    "30m":    ("30m", "60d"),    # yfinance: <1d intervals capped ~60d
    "5m":     ("5m", "60d"),     # PROJECT.md states 5m≈60d, 1m≈7d
}

def coletar_ohlc(ticker, timeframe="diario"):
    interval, period = _TIMEFRAME_YF.get(timeframe, _TIMEFRAME_YF["diario"])
    hist = _yf().Ticker(yahoo_symbol(ticker)).history(
        period=period, interval=interval, auto_adjust=False)
    return _ajustar_por_split(hist)   # REUSE the existing pure split-adjuster
```

This keeps every intraday concern (tighter limits, different shape, delay) out of `coletar_mercado`/`montar_empresa`, so the fundamental side cannot break and CompanyData is never asked to carry intraday frames.

---

## Build Order (dependency-aware — ingest → core → report → spec → UI)

Phase numbering continues from **12** (per PROJECT.md). Each phase is independently golden-testable before the next depends on it.

| Phase | Deliverable | Depends on | Why this order |
|-------|-------------|------------|----------------|
| **12 — Intraday ingest** | `prices.coletar_ohlc(ticker, timeframe)` + timeframe→interval/period map + reuse `_ajustar_por_split`; `test_ingest_intraday.py` | nothing (additive to ingest) | Foundational; no UI. Verifies Yahoo intraday limits empirically and proves the daily pipeline is untouched. |
| **13 — Setup math** | `core/setups.py`: S/R pivots, Fibonacci, pattern detection (OCO, double top/bottom, triangle, flag), entry/stop/target, R:R, quality score; `test_setups.py` (golden) | a known OHLCV frame shape (from 12, or fixtures) | Pure, deterministic, the riskiest correctness work — lock it with goldens before any UI. **Flag for deeper research** (pattern-detection heuristics are non-trivial). |
| **14 — Setup report** | `report/setup.py`: `SetupSwing` dataclass + `montar_setup()` wiring `indicators.calcular` context + `setups.*`; graceful degradation; `test_setup_report.py`. Optional `cli.py` mirror. | 12 + 13 + existing `indicators.py` | The read-only contract the UI will consume; assembles context + levels + checklist + score into one object. |
| **15 — Setup chart specs** | `grafico.py` additive builders: `candles_setup`, `niveis_horizontais`, `formas_padroes` (+ reuse `overlays_preco`/`subpaineis_ativos`); `test_grafico_setup.py` | 14 (reads `SetupSwing`) | Pure spec layer; golden-tested because Streamlit visuals can't be auto-verified. |
| **16 — UI page** | `app.py` 4th radio entry + new block: timeframe selector, 🔄 Atualizar (nonce cache, ttl=300), candlestick render from specs, checklist/score/R:R, ~15min delay + history-limit banner; `glossario.py` keys | 12–15 | Thin read-only renderer last; everything it needs already exists as engine fields/specs. |

Cross-cutting: add the `setups:` block to `config.yaml` in Phase 13 (pivot lookback, Fib ratios, swing-min %, score weights) and the `_TIMEFRAME_YF` map in Phase 12; add `glossario` tooltip keys incrementally, finalized in Phase 16.

---

## Anti-Patterns (specific to this integration)

### Anti-Pattern 1: Branching intraday inside `coletar_mercado` / `montar_empresa`
**What people do:** add an `interval=` param to the existing daily fetch and push intraday frames onto `CompanyData`.
**Why it's wrong:** couples the fundamental 5y pipeline to Yahoo's tighter intraday limits and delay; one intraday failure mode can break the Analisar/Garimpo/Ranking modes; CompanyData starts carrying state it shouldn't.
**Do this instead:** a separate `coletar_ohlc()` that only returns a split-adjusted OHLCV frame; the swing page never builds CompanyData.

### Anti-Pattern 2: Detecting patterns / computing Fibonacci / scoring inside `app.py`
**What people do:** "it's just a few lines" → compute S/R levels or Fib ratios in the render block.
**Why it's wrong:** violates the Phase-2 read-only rule; reintroduces method logic into the UI where it can't be golden-tested and drifts from the CLI.
**Do this instead:** all of it in `core/setups.py` + `report/setup.py`; app.py reads `SetupSwing` and draws specs from `grafico.py`.

### Anti-Pattern 3: Touching `AnaliseAcao` / `analisar_acao` / the W-FRI resample
**What people do:** bolt swing fields onto `AnaliseAcao` "to reuse the dataclass."
**Why it's wrong:** risks the validated fundamental verdict and the 191-test golden suite; couples two products that must stay independent.
**Do this instead:** a brand-new `SetupSwing` in `report/setup.py`; the fundamental verdict and Analisar tab stay byte-for-byte.

### Anti-Pattern 4: `ttl`-only cache, or `func.clear()` on Refresh
**What people do:** rely on `ttl` (stale until expiry) or call `montar_setup_cached.clear()` (nukes all tickers).
**Why it's wrong:** stale data ignores the manual Refresh intent; global clear throws away unrelated cached work.
**Do this instead:** per-key nonce arg incremented by the Atualizar button + short `ttl=300`.

### Anti-Pattern 5: Implying a recommendation
**What people do:** color the score green/red as a buy/sell, or label the entry zone "Compre aqui."
**Why it's wrong:** breaks the educational-software / non-recommendation posture baked into PROJECT.md key decisions.
**Do this instead:** display fired signals, levels, score and R:R neutrally; same disclaimer voice as the rest of the app.

---

## Integration Points

### Internal boundaries (new ↔ existing)

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `report/setup.py` → `core/indicators.py` | direct call `calcular(ohlc, cfg)` | Reused verbatim; already timeframe-agnostic. Zero changes to indicators.py. |
| `report/setup.py` → `core/setups.py` | direct calls (pure) | New math only; no I/O. |
| `app.py` → `report/setup.py` | reads `SetupSwing` fields only | Read-only firewall; no method calls in UI. |
| `app.py` → `grafico.py` | consumes new spec dataclasses | Same spec→trace contract as today. |
| `app.py` → `ingest/prices.coletar_ohlc` | via `@st.cache_data` wrapper + nonce | Only network touchpoint; isolated from `montar()`/`coletar_mercado`. |
| `report/setup.py` ↔ `report/report.py` | **none** | Deliberate firewall — guarantees the fundamental verdict is untouched. |

### External services

| Service | Integration pattern | Gotchas |
|---------|---------------------|---------|
| Yahoo Finance (yfinance) intraday | `Ticker.history(interval=, period=, auto_adjust=False)` then `_ajustar_por_split` | **~15min delay** (display banner); history caps: 5m/30m≈60d, 60m≈730d, 1m≈7d (MEDIUM — verify live in Phase 12); intermittent datacenter rate-limit (the existing 3-try backoff pattern in `prices.py` applies). |
| BCB / CVM | not used by the swing page | Swing page is price-only; no fundamentals fetch. |

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Layer placement (core/report/grafico/ingest split) | HIGH | Directly mirrors the existing, code-verified separation. |
| Read-only-UI preservation via new dataclass | HIGH | Same mechanism already used by `AnaliseAcao` + spec layer. |
| Intraday isolation (`coletar_ohlc`) | HIGH | `_ajustar_por_split` is pure and reusable; daily fetch left intact. |
| Refresh-vs-cache (nonce) | HIGH | Standard Streamlit cache-key technique; fits existing `@st.cache_data` usage. |
| yfinance intraday history/interval limits | MEDIUM | From training data + PROJECT.md; must be confirmed empirically in Phase 12. |
| Pattern-detection heuristics (OCO/triangles/flags) | LOW–MEDIUM | Geometry/thresholds are genuinely hard; flagged for deeper phase-13 research. |

## Sources

- Codebase (authoritative): `app.py`, `src/analista/report/report.py`, `src/analista/core/indicators.py`, `src/analista/ingest/prices.py`, `src/analista/ingest/build.py`, `src/analista/grafico.py`, `config.yaml`, `tests/` (golden suite)
- `.planning/PROJECT.md` — v1.4 milestone scope, key decisions, custo-zero/intraday constraints
- yfinance intraday interval/period limits — training data (MEDIUM; verify live)

---
*Architecture research for: technical swing-setup page integration into a pure-engine + read-only-UI Streamlit app*
*Researched: 2026-06-29*
