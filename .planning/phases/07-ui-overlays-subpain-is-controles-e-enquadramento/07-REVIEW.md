---
phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
reviewed: 2026-06-27T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - app.py
  - src/analista/core/indicators.py
  - src/analista/glossario.py
  - src/analista/grafico.py
  - src/analista/report/report.py
  - tests/test_glossario.py
  - tests/test_grafico_ui.py
  - tests/test_indicators.py
  - tests/test_report.py
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-06-27
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Phase 7 adds the technical-overlay UI: a `make_subplots` chart (price + DDM band +
moving-average/Donchian/Bollinger overlays + oscillator subpanels + event markers), the
pure spec layer in `grafico.py`, the `SinaisTecnicos.close` field, glossary tooltips, and the
subordinate consultative framing. The read-only contract over the engine is respected
(no recompute of the método; the fundamentalist veredito stays the only banner; the technical
section is rendered as discreet markdown/caption). Degradation paths are well covered by golden
tests.

However, there is one provable correctness defect that undermines the chart for any stock that
split in the last 5 years: the overlays and event markers are drawn on a **different price
basis** than the price line itself. The team explicitly documented this divergence risk in
`prices.py` (the price line is kept *nominal* precisely so it aligns with the nominal DDM band),
and Phase 7 then layers *split-adjusted* indicator series on top of that nominal line. Two
secondary logic issues (an "all windows" fallback that overrides an empty selection, and
breakout markers firing per-bar instead of per-event) round out the actionable findings.

## Critical Issues

### CR-01: Technical overlays/markers (split-adjusted) drawn on the nominal price axis — misaligned/false visual signals for split stocks

**File:** `app.py:196` (price line) + `app.py:232-237`, `app.py:247-255` (overlays/markers)
**Issue:**
The price line is built from the **nominal** close:
```python
serie = c.serie_precos   # app.py:196
```
`serie_precos` is the non-adjusted close (`prices.py:153` → `dm.serie_precos = nominal`, from
`tk.history(period="5y", auto_adjust=False)["Close"]`). The comment at `prices.py:141-143`
is explicit: the nominal series is used *on purpose* so the chart aligns with the nominal DDM
band, warning that an adjusted series "mostraria preços históricos retroajustados abaixo do
nominal".

The overlays and markers, however, come from `a.sinais`, which the engine computes on the
**split-adjusted** frame (`report.py:223` → `ohlc = c.ohlc_ajustado`, where
`ohlc_ajustado = _ajustar_por_split(hist)`), additionally resampled to weekly W-FRI. So
`overlays_preco(...)` returns split-adjusted SMA/EMA/Donchian/Bollinger series and
`marcadores_eventos(...)` returns marker `y` values at split-adjusted SMA50/Donchian levels —
all plotted on the same `row=1` y-axis as the *nominal* price line.

For any ticker with a stock split inside the 5-year window (e.g., the multi-split ITSA4 used by
the test fixtures), the pre-split portion of every overlay and every event marker is drawn at the
retro-adjusted (lower) level while the price line stays at the nominal (higher) level. The result
is a chart where the moving averages appear to cross the price where they do not, and event
triangles float detached from the price — i.e. **false/misleading technical signals** in the
exact layer that is meant to be a trustworthy consultative aid. Stocks without a split in the
window happen to look correct, which makes the defect easy to miss in spot checks.

**Fix:** Put the price line and the technical overlays/markers on a single, consistent price
basis. Either (a) draw the price line from the same split-adjusted close the indicators use
(`a.sinais.close`) and convert the nominal DDM band / `preco_atual` to that basis, or (b) keep the
nominal price line and feed the overlay layer a nominal-based indicator series. Minimal option (a):
```python
# app.py — use the same split-adjusted close the overlays/markers are computed on
serie = a.sinais.close if grafico.leitura_tecnica_disponivel(a.sinais) else c.serie_precos
```
Whichever basis is chosen, document and enforce that the price trace, the DDM band, the overlays
and the markers all share it; add a golden/UI test on a split ticker asserting that an overlay
value and the price at the same date are on the same scale.

## Warnings

### WR-01: Empty "Janelas" selection silently redraws all three moving averages

**File:** `src/analista/grafico.py:107`
**Issue:**
```python
for j in t.get("janelas") or [20, 50, 200]:
```
The multiselect in `app.py:165-167` writes `est["tendencia"]["janelas"]`. If the user enables the
"Médias móveis" toggle but deselects every window, `janelas` is `[]` (falsy), so the `or` falls
back to `[20, 50, 200]` and the chart draws all three MAs — the opposite of the user's explicit
deselection. The toggle being ON with zero windows should draw nothing.
**Fix:** Only fall back when the key is missing, not when it is an explicit empty list:
```python
janelas = t.get("janelas")
if janelas is None:
    janelas = [20, 50, 200]
for j in janelas:
    ...
```

### WR-02: Donchian breakout markers fire on every bar in a breakout run, not on the transition

**File:** `src/analista/grafico.py:219-226` (and the per-marker trace loop in `app.py:247-255`)
**Issue:**
Golden/death-cross markers are correctly emitted only on a sign *transition* (`grafico.py:207-215`).
The Donchian block, however, appends a `nova_maxima`/`perda_minima` marker for **every** bar where
`close > sup` / `close < inf`:
```python
for data in close.index.intersection(sup.index):
    ...
    if pd.notna(c) and pd.notna(s) and c > s:
        out.append(Marcador(data, float(s), "nova_maxima", ...))
```
A sustained breakout therefore produces a dense cluster of identical markers rather than one event
marker per breakout. `test_marcador_rompimento_maxima_data_exata` only asserts `novas[0].data`, so
the duplication is not caught. In `app.py` each marker becomes its own `go.Scatter` trace
(`app.py:247-255`), so the chart accumulates dozens of traces for a single breakout, cluttering the
plot and the hover.
**Fix:** Emit a Donchian marker only on the entry into the breakout state (transition), mirroring
the cross logic:
```python
above = (close > sup).reindex(sup.index).fillna(False)
entradas = above & ~above.shift(1, fill_value=False)
for data in sup.index[entradas]:
    out.append(Marcador(data, float(sup.loc[data]), "nova_maxima", ...))
```
(and symmetrically for `perda_minima`). Optionally collapse the per-marker traces in `app.py` into
one trace per marker `tipo`.

## Info

### IN-01: Redundant `dict(...)` wrapper on the overlay line style

**File:** `app.py:235`
**Issue:** `line=dict(ov.estilo)` builds a shallow copy of a dict that is already a dict; the intent
reads as `line=ov.estilo`. It works, but the wrapper is misleading (it is not `dict(**ov.estilo)`).
**Fix:** `line=ov.estilo` (or `line=dict(**ov.estilo)` if a defensive copy is actually wanted).

### IN-02: Glossary keys `tec_squeeze` and `tec_regressao` are defined and tested but never surfaced in the UI

**File:** `src/analista/glossario.py:149` (`tec_squeeze`), `src/analista/glossario.py:171` (`tec_regressao`)
**Issue:** `test_glossario.py` pins both keys as present, but no Phase 7 widget exposes a squeeze or
regression control (`app.py` uses only `tec_mm/tec_cross/tec_donchian/tec_bollinger/tec_adx/tec_rsi/
tec_macd/tec_timing/tec_indicadores`). The corresponding indicators are computed by the engine but
have no toggle, so the help text is currently dead for this UI.
**Fix:** Either expose the squeeze/regression overlays (they already exist in `SinaisTecnicos`) or
drop the unused keys from the contract list to keep the glossary honest about what the UI offers.

---

_Reviewed: 2026-06-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
