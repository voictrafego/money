# Pitfalls Research

**Domain:** Adding consultative trend/technical indicators (SMA/EMA + crossovers, Donchian + Bollinger, ADX + slope, RSI + MACD) to a fundamentals-first, zero-cost, long-term B3 dividend-analysis app (Python + Streamlit + yfinance daily OHLC)
**Researched:** 2026-06-24
**Confidence:** HIGH (computation + price-adjustment + timeframe findings cross-verified with multiple sources and matched against the actual codebase in `src/analista/ingest/prices.py` and `app.py`)

---

## TL;DR for the roadmapper

Three pitfalls are project-defining and must be designed for up front, not patched later:

1. **Look-ahead / off-by-one bias** — the signal you show must be computable with only closed candles. Get this wrong and every alert is a lie. (Computation phase)
2. **Nominal-vs-adjusted price series** — the v1.1 chart deliberately plots NOMINAL `Close` (`auto_adjust=False`) to align with the DDM band. Indicators computed on that same nominal series get *split-distorted* (false crossovers/breakouts at every split). **Recommendation: compute indicators on a SPLIT-adjusted, dividend-UNADJUSTED series; keep the chart axis nominal.** (Computation phase — this is the subtle one and the quality gate calls it out explicitly.)
3. **The philosophical trap** — the moment a technical signal reads as "this overrides barato/caro," the product betrays its core value. Framing is a first-class requirement, not polish. (UX/framing phase)

Everything else (Wilder smoothing, warm-up/NaN, whipsaws, over-alerting, weekly-vs-daily, yfinance gaps) is real but secondary and well-understood.

---

## Critical Pitfalls

### Pitfall 1: Look-ahead bias / off-by-one — using today's (still-forming) close as if it were known

**What goes wrong:**
You compute a crossover or breakout using `serie.iloc[-1]` (today's close) and present it as a confirmed, actionable signal. But during the trading day today's "close" is the *current intraday price* — it isn't closed yet. The signal flips mid-session and flips back by the actual close, so the alert the user saw at 11:00 is gone at 18:00. Worse, any internal "did this signal fire?" logic that peeks at a bar's close to decide something *about that same bar* is classic look-ahead bias: it looks great on history and is unrepeatable live.

**Why it happens:**
- yfinance's last row during market hours is a live, mutable quote, not a settled candle. Devs treat the whole series uniformly.
- Crossover detection is naturally written as "is fast > slow today AND was fast <= slow yesterday" — correct only if "today" is a *closed* bar.
- This app's current code already uses `iloc[-1]` for `preco_atual` fallback and 6m performance — copying that pattern into signal logic silently imports the bug.

**How to avoid:**
- Define signals on **closed daily candles only**. Treat the last row as "current/provisional" and base any *fired* alert on the last *completed* bar (or, since B3 daily bars settle after close, simply recompute daily and accept that today's signal is provisional until close — and *label it provisional*).
- A crossover at bar *t* must use only `[…, t]` data; a "fresh crossover" test compares bar *t* vs bar *t-1*, never bar *t* vs *t+1*.
- Write a golden test that asserts: `indicator(series[:k])[-1] == indicator(series)[k-1]` for several `k` (causality / no-repaint test). If an indicator's past value changes when future bars are appended, it has look-ahead.
- For RSI/ADX/EMA the value at *t* legitimately depends on the seed and all prior bars, but never on bars after *t* — the test above catches violations.

**Warning signs:**
- A signal that visibly changes between two page refreshes on the same day.
- Backtest/example output that looks suspiciously clean.
- Any code that indexes `+1` ahead, or compares an indicator at *t* to a price at *t+1*.

**Phase to address:** Computation/engine phase (indicator module), locked by golden tests before any UI wiring.

---

### Pitfall 2: Nominal vs. adjusted price series — split distortion (and the DDM-band tension)

**What goes wrong:**
The v1.1 decision (Key Decisions table, Phase 3) is that the chart's Y-axis uses **nominal `Close`** (`auto_adjust=False`) so it sits on the same base as the DDM intrinsic-value band (`vmin`/`vmax` are nominal). If v1.2 computes MA/Bollinger/Donchian/RSI/MACD on that **same nominal series**, then at every **stock split** the nominal price gaps (e.g. a 2:1 split halves the price overnight). The indicators read that artificial gap as a real move: a death cross, a Donchian/Bollinger downside breakout, an RSI crash — all spurious. On a 5-year B3 series, splits/grupamentos and bonificações are common enough (BBAS3, ITUB4, WEGE3 have all had events) that this is not hypothetical.

Ordinary **dividends** are different: an ex-dividend adjustment shifts the *entire* historical series by a (roughly) uniform proportion, so the *relationships* MAs, highs and lows have to each other are preserved — signals are largely stable whether or not you dividend-adjust. So dividends are the *minor* concern; **splits are the signal-killer**.

**Why it happens:**
- The natural, lazy choice is "use the series I already have" — and the series the app already has (`dm.serie_precos`) is the nominal one, built for the chart.
- Devs conflate "adjusted" into one switch (`auto_adjust=True/False`), not realizing yfinance's `auto_adjust` folds *both* split and dividend adjustment together.

**How to avoid (the recommendation the quality gate asks for):**
- **Compute indicators on a SPLIT-adjusted, dividend-UNADJUSTED price series. Keep the chart axis on nominal `Close`.**
  - Rationale: split adjustment is *non-negotiable* (it removes the artificial gaps that fabricate signals); dividend adjustment is *optional* and, for a buy-and-hold timing tool, arguably *undesirable* because it pulls historical prices below what actually traded and muddies the relationship to the nominal DDM band the user is reading.
  - This keeps the visible price (nominal) consistent with the DDM band — honoring the Phase-3 decision (CR-01) — while the math underneath is run on a series that won't false-trigger at splits.
- Practical sourcing with yfinance: request the raw OHLCV with `auto_adjust=False` (which the code already does) and reconstruct a split-only-adjusted series using the `Stock Splits` column (`tk.splits` / `actions`), or derive the split factor from `Close` vs `Adj Close` minus the dividend component. Simplest robust path: build split-adjusted closes by dividing nominal `Close` by the cumulative split ratio. Add a golden test on a known-split ticker (e.g. a synthetic 2:1) asserting no spurious crossover at the split date.
- Document the chosen series explicitly in code comments, mirroring the existing detailed comment block in `prices.py` (lines 94-99) that already explains the nominal/Adj-Close split — extend that same comment to cover the *indicator* series so the next dev doesn't "simplify" it back to nominal.
- If split-adjustment is deemed too costly for the first cut: at minimum, **detect** split events (large overnight gap that matches a `splits` entry) and either suppress signals across that boundary or warn. Never silently emit a signal generated by a split.

**Warning signs:**
- A golden/death cross or breakout dated exactly on a known split/grupamento date.
- Indicators that look fine on tickers with no corporate actions and bizarre on ones that split.
- MA200 line with a visible discontinuity that the nominal price line also shows.

**Phase to address:** Computation/engine phase — pick and implement the indicator series here, before plotting. This is the single most important computation decision in the milestone.

---

### Pitfall 3: Wrong EMA seeding / using simple EMA where Wilder's smoothing is required

**What goes wrong:**
RSI, ADX (and ATR, which Bollinger may relate to) are defined with **Wilder's smoothing (RMA/SMMA)**, which uses `alpha = 1/length`. Standard EMA uses `alpha = 2/(length+1)`. Implementing RSI/ADX with a plain `ewm(span=length)` (standard EMA) produces numbers that look like RSI/ADX but disagree with TradingView, the book's reference, and every other terminal — e.g. a "14-period RSI" that reads 58 where everyone else sees 64. Separately, EMA/RSI **seeding** matters: the canonical seed is an SMA of the first `length` values (Wilder), not the first value alone; getting the seed wrong skews the early portion of the series.

**Why it happens:**
- pandas `ewm` defaults invite `span`-based (standard) EMA; Wilder's needs `ewm(alpha=1/length, adjust=False)` after a proper seed.
- "An EMA is an EMA" — the 1/length vs 2/(length+1) distinction is easy to miss.

**How to avoid:**
- Use a vetted library so you don't hand-roll Wilder's: `ta` (technical-analysis-library-in-python) or `pandas-ta`/`stockstats`, all pure-Python and zero-cost. If hand-rolling, RSI/ADX = `ewm(alpha=1/length, adjust=False)` seeded by the SMA of the first `length` bars.
- Use **canonical periods** and don't expose them as knobs (see Pitfall 6): RSI 14, MACD 12/26/9, ADX 14, SMA/EMA 20/50/200, Bollinger 20±2σ, Donchian 20.
- Add a golden test pinning RSI/ADX values against a small hand-checked fixture or a value cross-checked on TradingView for one liquid ticker, so a future refactor that swaps Wilder's for plain EMA fails loudly.

**Warning signs:**
- RSI/ADX numbers consistently off vs TradingView by a few points.
- ADX that never gets as smooth/lagged as expected (too jumpy → you used standard EMA).

**Phase to address:** Computation/engine phase. Library choice + golden value tests.

---

### Pitfall 4: Warm-up / NaN handling for the first N bars (and short-history tickers)

**What goes wrong:**
MA200 needs 200 closed bars before it has *any* valid value; ADX needs ~2×length warm-up to stabilize. A 5-year daily series (~1250 bars) is plenty for MA200 — but newly listed B3 tickers, recent IPOs, or tickers where yfinance only returns a thin history will have fewer bars. Naive code either (a) plots a flat/garbage MA200 over the warm-up region, (b) crashes on NaN, or (c) emits a "price below MA200 → reverify" alert when MA200 is actually undefined/just-born and meaningless.

**Why it happens:**
- `rolling(200).mean()` returns NaN for the first 199 bars; devs forget to gate signals on "indicator is defined AND has enough warm-up."
- The app already handles "short/missing series" for the chart (`if serie is None or len(serie)==0`) but that check is *binary*; an indicator needs a *per-indicator minimum-length* check.

**How to avoid:**
- Per indicator, define a minimum-bars requirement and **only show the indicator (and only allow its signal to fire) when bars >= requirement** (MA200 → ≥200; add a buffer for ADX/RSI warm-up, e.g. require length×3).
- When an indicator can't be computed, degrade gracefully *per indicator*, consistent with the existing pattern: don't hide the whole chart — just omit that line and, if the user toggled it on, show a small caption like "MM200 indisponível (histórico < 200 pregões)" mirroring the tone of the existing "preço indisponível (Yahoo)" / "Gráfico de preço indisponível" messages.
- Never emit the MA200-breakout reverify alert when MA200 is undefined or within its warm-up window.

**Warning signs:**
- MA200 line that starts at a weird flat value or appears for a ticker with 8 months of data.
- Exceptions/`NaN` reaching Plotly or the alert text.
- Reverify alert firing on a freshly-listed ticker.

**Phase to address:** Computation phase (define min-bars per indicator) + UX phase (per-indicator graceful degradation).

---

## Moderate Pitfalls

### Pitfall 5: Whipsaws / false crossovers in choppy markets (signal quality)

**What goes wrong:**
In sideways/choppy price action, fast and slow MAs cross repeatedly, RSI oscillates through 30/70, MACD flips sign — generating a stream of contradictory "buy now / sell now" signals. For a buy-and-hold dividend investor this is pure noise dressed as guidance.

**Why it happens:**
- MA crossovers are inherently whipsaw-prone in range-bound markets; daily timeframe amplifies it.
- No trend filter: a crossover is acted on even when there's no trend to ride.

**How to avoid:**
- Use **ADX as a gate**: only treat MA crossovers / breakouts as meaningful when ADX indicates an actual trend (commonly ADX > ~20-25). The milestone already includes ADX "to say IF there is a trend" — wire it as the gate, not a standalone display. This is the single highest-leverage anti-whipsaw move.
- Prefer **weekly timeframe** for the long-horizon signals (see Pitfall 7).
- Optionally require a small confirmation buffer (e.g. crossover must persist N bars, or price must clear the band by a margin) rather than firing on the exact touch.

**Warning signs:** Multiple crossover/breakout flips within a few weeks; signal summary that changes direction often.

**Phase to address:** Signal-logic phase (ADX gating + confirmation rules).

---

### Pitfall 6: Parameter overfitting — tuning periods to look good on chosen examples

**What goes wrong:**
While building/demoing, you nudge the MA lengths or RSI thresholds until the signals "line up nicely" on the handful of tickers you're testing (PETR4, BBAS3…). Those tuned parameters are overfit to the demo and generalize poorly; you've also silently invented a strategy the book never endorsed.

**Why it happens:**
- Visual feedback loop: it's tempting to make the demo impressive.
- No out-of-sample discipline in a hand-built tool.

**How to avoid:**
- **Hard-code canonical periods** (RSI 14, MACD 12/26/9, ADX 14, SMA 20/50/200, Bollinger 20±2σ, Donchian 20) and do not expose them as tunable inputs. The control panel toggles *which* indicators show — never their parameters.
- Frame the tool as "standard indicators, standard settings," consistent with the book-fidelity core value (the app's whole identity is faithful reproduction, not bespoke tuning).

**Warning signs:** Non-standard periods in the code; a settings UI exposing lengths; signals that look great only on the tickers used during development.

**Phase to address:** Computation phase (constants) + UX phase (controls expose toggles, not parameters).

---

### Pitfall 7: Daily timeframe over-alerting on a buy-and-hold horizon (daily vs weekly)

**What goes wrong:**
Daily RSI/MACD/crossovers fire constantly. A buy-and-hold dividend investor who checks in monthly gets a "signal" that's already stale and a history littered with contradictory daily flips. RSI/MACD "spam" trains the user to ignore the panel — or worse, to churn.

**Why it happens:**
- yfinance defaults to daily; daily feels like the natural granularity.
- The horizon mismatch (daily signals for a multi-year holder) is easy to overlook.

**How to avoid (with the requested argument):**
- **Argument for weekly:** weekly crossovers flip far less often than daily, filtering intraday/short-term noise, and a weekly golden cross carries materially more weight than a daily one — exactly the trade-off a buy-and-hold investor wants (fewer, more meaningful signals; slower response is *acceptable* because the holding period is years). Sources consistently rate weekly/daily as the reliable timeframes and daily as the more whipsaw-prone of the two.
- **Recommendation:** default the *trend/timing signal* (MA crossovers, ADX, MA200 reverify alert) to **weekly resampled candles** (`resample("W-FRI").last()` for OHLC), while the *chart* can stay daily for visual smoothness. Optionally let the user toggle daily/weekly, but default to weekly. Momentum (RSI/MACD) is fine to compute but should be presented as *fine-timing context*, not as standalone alerts.
- Resampling note: weekly resample must use proper OHLC aggregation (open=first, high=max, low=min, close=last) and align to a consistent weekday; partial current week is *provisional* (ties back to Pitfall 1 — label it).

**Warning signs:** Signal summary that contradicts itself week-to-week; users reporting "it's always telling me something."

**Phase to address:** Signal-logic phase (choose weekly as the default signal timeframe).

---

### Pitfall 8: yfinance data risk — gaps, holidays, illiquid B3 tickers, timezone/index issues

**What goes wrong:**
- B3 holidays/missing sessions create gaps; illiquid tickers have flat/repeated closes and stale prints that fabricate or suppress signals.
- The existing code already fights yfinance's intermittent IP rate-limiting (retry/backoff in `prices.py`) — the same flakiness can return a *short* or *partial* series silently.
- Timezone/index mismatches: yfinance returns tz-aware timestamps; resampling/comparison or merging with the DDM band (a flat hrect, so safe) can still trip on tz-aware vs tz-naive indices, and `resample` behaves differently across tz.

**Why it happens:**
- Treating yfinance as clean, complete daily data.
- Mixing tz-aware (yfinance) and tz-naive timestamps.

**How to avoid:**
- Reuse and extend the existing graceful-degradation pattern (`serie is None or len(serie)==0` → friendly "indisponível" info box) to the indicator layer, per-indicator (Pitfall 4).
- Drop NaNs/forward-fill *deliberately* and minimally; for illiquid tickers consider a liquidity gate (the app already computes `volume_financeiro_diario`) — optionally suppress/footnote technical signals for very illiquid names where they're meaningless.
- Normalize the index timezone once (the codebase already handles tz-aware dividend windows with `pd.Timedelta`; follow that precedent). Don't introduce a second timezone convention.
- Don't trust a single fetch: the existing retry/backoff stays; additionally validate the returned series length before computing long indicators.

**Warning signs:** Flat MA on an illiquid ticker; `tz-aware/naive` comparison errors; series shorter than requested 5y with no warning.

**Phase to address:** Data/ingest phase (extend `prices.py` to expose the split-adjusted indicator series + length validation) + UX phase (per-indicator degradation).

---

## The Philosophical / Product Pitfall (the one the core value hinges on)

### Pitfall 9: Letting technicals override — or appear to override — the fundamentalist verdict

**What goes wrong:**
The project's core value is *book-faithful, fundamentals-first* analysis; the Key Decisions table states technical analysis is **strictly consultative and never overwrites barato/caro**. The pitfall is *presentation*, not logic: a prominent green "COMPRAR (timing)" badge next to a "caro" valuation verdict reads, to a human, as a contradiction the user resolves in favor of the louder/newer signal. Suddenly the app is nudging market timing and churn — the opposite of a dividend buy-and-hold method, and a betrayal of its identity. Presenting any signal as a certainty ("MM200 rompida: VENDA") compounds it.

**Why it happens:**
- Visual hierarchy leaks meaning: a big colored badge implies authority regardless of disclaimer text.
- Trader-tool conventions (buy/sell signals) imported wholesale into an investor tool.
- The reverify alert is easy to phrase as an *instruction* ("venda") instead of a *prompt* ("reveja os fundamentos").

**How to avoid:**
- **Subordinate the technical block visually and verbally** to the fundamental verdict: fundamentals verdict stays primary and prominent; the timing panel is clearly secondary, off by default or visually muted, and labeled "consultivo / não altera o veredito."
- **Frame signals as uncertain prompts, never commands:** the sell alert is exactly what the Key Decisions table says — "rompimento técnico → *reveja os fundamentos*," never "venda." Use language of suggestion ("possível," "consultivo," "verifique"), never imperative certainty.
- **Never compute a combined buy/sell verdict** that mixes technical + fundamental into one score. Keep them in separate, clearly-labeled regions. The fundamental engine output must be untouched (consistent with the `app.py` read-only rule — UI reads engine fields, never recomputes/merges method).
- Add glossary tooltips (the app already has the `?` glossary pattern) defining each indicator *and* stating it's consultive and lagging.
- Consider defaulting the whole technical panel OFF (toggle to enable), reinforcing "opt-in extra," matching the "ligável/desligável" decision already made.

**Warning signs:** A reviewer reads the screen and thinks the timing signal and the valuation verdict "disagree"; any imperative verb ("compre/venda") in signal copy; a single merged score.

**Phase to address:** UX/framing phase — and it should be an explicit acceptance criterion, not an afterthought. Verify by showing a "caro + bullish-timing" case to a fresh reader and confirming they still read the fundamental verdict as the decision.

---

### Pitfall 10: Chart clutter — turning an investor tool into a trading terminal

**What goes wrong:**
Stacking SMA20/50/200 + EMA + Bollinger + Donchian + RSI subplot + MACD subplot + ADX subplot onto one screen turns the clean v1.1 price-vs-DDM chart into an unreadable terminal, burying the one thing that matters (price vs intrinsic value).

**Why it happens:** Feature completeness pressure — all the indicators in the milestone exist, so all get shown.

**How to avoid:**
- Honor the existing decision: **indicators are toggle-able and default to a minimal set** (e.g. only MA200 + the DDM band on by default). Oscillators (RSI/MACD/ADX) go in collapsible sub-panels, off by default.
- Keep the DDM band and nominal price as the visual anchor; overlays are additive and removable.

**Warning signs:** Default view looks busy; the DDM band is hard to find; users can't tell price from indicator lines.

**Phase to address:** UX phase (controls + sensible defaults).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Compute indicators on the existing nominal `serie_precos` | Reuse data already in `DadosMercado`; zero new fetch | Spurious signals at every split/grupamento; silent wrongness on exactly the tickers with corporate actions | Only if split *detection + suppression* is added as a stopgap; never as the final state |
| Hand-roll Wilder's RSI/ADX with `ewm(span=…)` | No new dependency | Values disagree with every terminal/the book; users distrust the tool | Never — use `ta`/`pandas-ta` or `ewm(alpha=1/length)` with proper seed |
| Fire signals on the live last bar (`iloc[-1]`) | "Up to date" feel | Repainting signals; look-ahead; unrepeatable alerts | Acceptable only if clearly labeled "provisório (pregão em curso)" |
| Daily timeframe for all signals | Simpler (no resample) | Over-alerting/whipsaw on a buy-and-hold horizon | MVP only if signals are visibly de-emphasized; weekly should be the target default |
| Hide the whole chart when one indicator can't compute | One code path | Loses the working price/DDM chart over a missing MA200 | Never — degrade per-indicator |
| Expose indicator periods as user inputs | Looks flexible | Invites overfitting; breaks book-fidelity framing | Never for this product |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| yfinance OHLC | Using `auto_adjust=True` (folds split+dividend together) or nominal-only | `auto_adjust=False` for the chart (already done) + a separate **split-adjusted, dividend-unadjusted** series for indicators |
| yfinance last row | Treating intraday live quote as a closed candle | Mark last bar provisional; fire alerts on closed bars |
| yfinance reliability | Assuming one fetch returns full 5y | Keep existing retry/backoff; validate series length before long indicators |
| pandas resample (weekly) | `resample("W")` on close only / wrong weekday / tz drift | OHLC-aware aggregation, fixed `W-FRI`, single tz convention; current week provisional |
| Plotly multi-indicator | Cramming oscillators onto the price axis | Separate sub-panels (shared x-axis), off by default |
| Streamlit `$`/LaTeX | New signal/alert strings with `R$` re-trigger LaTeX mode | Reuse the existing `esc_md()` for any new metric/alert copy containing `$` |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Recomputing all indicators on every Streamlit rerun | Sluggish "Analisar" tab on every widget toggle | Cache the computed indicator frame (`@st.cache_data`) keyed by ticker; toggles only change which traces render, not the math | Noticeable even at 1 user with many toggles |
| Re-fetching yfinance per indicator toggle | Extra latency + rate-limit hits | Fetch once into `DadosMercado`; indicators are pure functions of the cached series | Immediately, given yfinance flakiness |

*(Single-user Streamlit app — no real scale concerns beyond per-interaction responsiveness.)*

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Presenting signals as financial advice ("compre/venda") | Misleads a retail user into churn/loss; reputational + ethical | Consultive framing, suggestion language, "não é recomendação" disclaimer (ties to Pitfall 9) |

*(No secrets/PII in this milestone; the real "safety" issue here is advice framing, covered above.)*

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Loud buy/sell badge beside the valuation verdict | Reads as overriding the fundamental verdict | Subordinate, muted, opt-in technical panel; fundamentals stay primary |
| Imperative alert copy ("VENDA: perdeu a MM200") | Triggers panic selling, contradicts the book | "Possível perda de tendência (MM200) — reveja os fundamentos" |
| Over-alerting on daily RSI/MACD | User tunes out the panel | Weekly default; oscillators as context, not alerts |
| Cluttered default chart | DDM band/price buried | Minimal default overlays; oscillators collapsible/off |
| No explanation of lag/uncertainty | User treats indicator as predictive | Glossary tooltips: "indicador atrasado, consultivo, não preditivo" |

## "Looks Done But Isn't" Checklist

- [ ] **Crossover/breakout signals:** Often missing the *closed-bar* guarantee — verify the no-repaint golden test (`indicator(series[:k])[-1] == indicator(series)[k-1]`).
- [ ] **MA/Bollinger/Donchian:** Often computed on nominal price — verify they run on the **split-adjusted** series and produce no spurious signal at a known split date.
- [ ] **RSI/ADX:** Often use standard EMA — verify Wilder's smoothing against a TradingView/hand-checked fixture value.
- [ ] **MA200 & reverify alert:** Often fires during warm-up — verify the alert is gated on `bars >= 200` and MA200 is defined.
- [ ] **Short-history / missing series:** Often crashes or hides the whole chart — verify per-indicator graceful degradation with an "indisponível" caption matching the existing tone.
- [ ] **Weekly resample:** Often close-only / wrong weekday — verify OHLC aggregation and provisional current-week labeling.
- [ ] **Framing:** Often a loud badge — verify a "caro + bullish timing" screen still reads fundamentals-first to a fresh viewer.
- [ ] **New alert copy with `R$`:** Often re-triggers Streamlit LaTeX — verify `esc_md()` applied.
- [ ] **Golden tests:** Often only cover the engine — verify new indicator tests are added and the existing 64 stay green.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Indicators built on nominal series (split distortion) | MEDIUM | Introduce split-adjusted series in ingest; re-point indicator functions; add split-date golden test; chart axis unchanged |
| Standard EMA used for RSI/ADX | LOW | Swap to Wilder's (`alpha=1/length`)/vetted lib; pin a fixture value |
| Look-ahead/repaint shipped | MEDIUM | Add no-repaint test, refactor signals to closed-bar; mark live bar provisional |
| Over-alerting/whipsaw complaints | LOW | Switch signal timeframe to weekly default; add ADX gate |
| Technicals reading as overriding verdict | LOW (copy/layout) but HIGH if shipped (trust) | Demote panel, rewrite copy to suggestion/reverify language, default-off |

## Pitfall-to-Phase Mapping

Suggested phases: **(A) Indicator engine/computation**, **(B) Signal logic (gating, timeframe, alert rules)**, **(C) UX/framing & controls in `app.py`**, with **data/ingest** extension folded into A.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. Look-ahead / off-by-one | A (engine) | No-repaint golden test passes |
| 2. Nominal vs split-adjusted series | A (engine/ingest) | No spurious signal at a known split date; chart stays nominal |
| 3. Wilder vs standard EMA | A (engine) | RSI/ADX match a hand-checked/TradingView fixture |
| 4. Warm-up / NaN / short history | A (min-bars) + C (per-indicator degrade) | MA200 alert never fires < 200 bars; missing indicator shows caption, not crash |
| 5. Whipsaws / false crossovers | B (signal logic) | ADX gate suppresses crossovers in low-ADX regimes |
| 6. Parameter overfitting | A (constants) + C (toggles only) | No period inputs in UI; canonical constants in code |
| 7. Daily vs weekly over-alerting | B (timeframe default) | Signals default to weekly; alert frequency demonstrably lower |
| 8. yfinance gaps / tz / illiquid | A/ingest + C | Length validation; single tz; graceful per-indicator degradation |
| 9. Technicals overriding the verdict | C (framing) — explicit acceptance criterion | Fresh-reader test: fundamentals read as primary in a conflicting case |
| 10. Chart clutter | C (controls/defaults) | Default view = price + DDM band (+ MA200); oscillators off by default |

## Sources

- [Wilder's Moving Average / Smoothed MA guide — Dutch Algotrading](https://www.dutchalgotrading.com/2025/11/28/wilders-moving-average-smoothed-ma-guide/) — Wilder's `alpha = 1/length` vs standard EMA `alpha = 2/(length+1)` (HIGH; matches multiple sources)
- [Smoothed Moving Average (Wilder's) — QuantifiedStrategies](https://www.quantifiedstrategies.com/smoothed-moving-average/) — confirms Wilder smoothing for RSI/ATR/ADX
- [Technical Analysis Library in Python (`ta`) docs](https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html) — vetted zero-cost library for correct Wilder-based indicators
- [stockstats (PyPI)](https://pypi.org/project/stockstats/) — alternative pure-Python indicator lib
- [Wilder's RSI in pandas — alpharithms/indicators](https://github.com/alpharithms/indicators/blob/main/wilders_rsi_pandas.py) — reference pandas implementation of Wilder seeding
- [Ordinary Dividends: To Adjust or Not — trendinvestorpro.com](https://trendinvestorpro.com/ordinary-dividends-to-adjust-for-or-not-to-adjust/) — dividend adjustment shifts series uniformly, preserving relationships (signals stable)
- [To dividend adjust or not — Alvarez Quant Trading](https://alvarezquanttrading.com/blog/to-dividend-adjust-or-not-to-dividend-adjust-that-is-the-question/) — splits create false bearish signals on unadjusted charts; splits must be adjusted
- [Price Data Adjustments — StockCharts](https://help.stockcharts.com/data-and-ticker-symbols/data-availability/price-data-adjustments) — split-induced gaps cause false sell signals; adjust for accurate TA
- [Adjusted vs Unadjusted Closing Prices and your Trading Algorithm — Raposa](https://raposa.trade/blog/adjusted-vs-unadjusted-closing-prices-and-your-trading-algorithm/) — look-ahead/adjustment pitfalls in algo signals
- [Different Moving Averages for Different Time Frames — StockCharts](https://stockcharts.com/articles/decisionpoint/2015/07/different-moving-averages-for-different-time-frames.html) — higher timeframe = more significant, fewer whipsaws
- [Moving Average Crossover Rules That Reduce Whipsaws — trendsandbreakouts](https://trendsandbreakouts.com/ma-crossover) — weekly flips less than daily; ADX/trend filtering reduces whipsaws
- Codebase: `src/analista/ingest/prices.py` (nominal/Adj-Close decision, retry/backoff, tz-aware dividend window) and `app.py` (chart, graceful-degradation `indisponível` pattern, `esc_md()`, glossary tooltips, read-only UI rule)
- `.planning/PROJECT.md` Key Decisions (nominal-Close decision CR-01, consultive-technical decision, ligável/desligável, app.py read-only)

---
*Pitfalls research for: consultative technical indicators in a fundamentals-first B3 dividend app*
*Researched: 2026-06-24*
