---
phase: 17-modo-trading-candlestick-tradingview-lightweight-charts
verified: 2026-07-01T14:35:33Z
status: passed
score: 5/5 must-haves verified (roadmap success criteria)
overrides_applied: 0
---

# Phase 17: Modo Trading — Candlestick TradingView (Lightweight Charts) Verification Report

**Phase Goal:** A aba de swing ganha uma vista "Modo Trading" (toggle) que renderiza o candlestick puro via TradingView Lightweight Charts v5 (carregada por `st.components.v1.html` + CDN unpkg pinado, zero dependência Python nova), entregando UX que o Plotly não dá (scroll-zoom, pan, crosshair com rótulos nos eixos, Y-autoscale, linha de último preço); as sobreposições da engine (zona de entrada, stop, alvo, S/R, Fibonacci, padrões/pivôs) são portadas para createPriceLine / helper BandPrimitive / createSeriesMarkers, lendo campos de SetupSwing SEM recálculo. O Plotly permanece na análise densa; `grafico.py`, os 283+ goldens e a regra `app.py` read-only ficam intactos.

**Verified:** 2026-07-01T14:35:33Z
**Status:** passed
**Re-verification:** No — initial verification

**Note on human verification:** A human browser smoke test (via Claude-in-Chrome) was already run and approved against the canonical BBSE3/Diário dataset (documented in `17-03-SUMMARY.md`, "Browser Smoke Evidence"), with no regression in Plotly/Analisar/Ranking/Garimpo. Per verification scope, interactive/visual criteria are treated as human-confirmed; this report focuses on independently re-verifying the code-level invariants (not merely trusting the SUMMARY narrative).

## Goal Achievement

### Observable Truths (ROADMAP.md Success Criteria, Phase 17)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Usuário liga "Modo Trading" e vê candlestick TV-like (scroll=zoom, pan, crosshair com rótulos, Y-autoscale, linha de último preço) sobre os MESMOS dados OHLC; Plotly continua default | ✓ VERIFIED | `app.py:920-928` — `st.radio("Vista", ["Plotly","Modo Trading"], key="swing_vista")`, default `"Plotly"` via `setdefault`. `_render_lwc` (app.py:113-335) builds chart with `crosshair: {mode: CrosshairMode.Normal}` (line 207), `rightPriceScale: {autoScale: true}` (208), `handleScroll: true, handleScale: true` (210), `priceLineVisible: true, lastValueVisible: true` on candle series (216). Data source is `f.ohlc` (same frame the Plotly branch uses), no new fetch. Interactive/visual behavior additionally confirmed by human browser smoke (17-03-SUMMARY.md) — candlestick rendered live, crosshair with axis labels confirmed, pan+crosshair exercised on live instance. |
| 2 | Sobreposições da engine aparecem no chart LWC: entrada como banda (BandPrimitive), stop/alvo/Fibonacci como linhas rotuladas (createPriceLine), S/R como bandas, padrões/pivôs como markers — lendo SetupSwing sem recalcular; copy neutra | ✓ VERIFIED | `app.py:232-253` defines `BandPrimitive`/`BandPaneView` (series primitive, zOrder 'bottom', priceToCoordinate+fillRect). Used for suportes/resistencias (257-258) and entrada (261). `createPriceLine` used for entrada borders (262-263), stop "stop (estudo)" (266), alvo "alvo (estudo)" (267), Fibonacci "Fib {nome}" (269), pattern target "alvo (projeção de estudo)" (295). `createSeriesMarkers` for pivots (297-299), neckline as 2-point `LineSeries` (285-293). All values sourced read-only from `sw.entrada_zona/stop/alvo` (162-168), `sinais.niveis.suportes/resistencias/fib_retracoes` (156-172), `sinais.padroes.lista` (178-194) — no recomputation, only `round(float(...))` formatting. Copy verified neutral: "(estudo)"/"projeção de estudo"/"em formação" present, zero imperative language found. |
| 3 | Zero dependência Python nova; LWC v5.x pinada por versão via components.html+CDN; `grafico.py` intacto; `app.py` thin renderer | ✓ VERIFIED | `requirements.txt` unchanged (no new packages). `git diff` of app.py vs phase base adds only `import json` and `import streamlit.components.v1 as components` (both stdlib/Streamlit-native). CDN URL pinned: `https://unpkg.com/lightweight-charts@5.2.0/dist/lightweight-charts.standalone.production.js` (app.py:105-108), loaded with `integrity="sha384-q1KYLSKHgBnW5tWYGGR8+6YV4/iPy31dILoF2I1OD7XiVUvHEp/TaxIQVmB0j3R2" crossorigin="anonymous"` (line 200) — **independently re-verified**: downloaded the exact `@5.2.0` bundle from unpkg (196,203 bytes) and computed `openssl dgst -sha384` myself; hash matches the one in app.py exactly. `addSeries(CandlestickSeries,...)` used (v5 API); `grep -c addCandlestickSeries app.py` = 0. `grafico.py`: `git diff --name-only "$(cat .phase-base-sha)"..HEAD -- src/analista/grafico.py` is EMPTY (confirmed independently). `_render_lwc` body (lines 113-335, manually bounded) contains no `indicators.calcular(` / `montar_setup(` calls — confirmed by direct `sed`+`grep` on the exact function body (the plan's own `awk`-based automated gate is a false positive: `_render_swing` is a nested `def` not starting at column 0, so the awk flag never resets and the gate over-captures the rest of the file; manual inspection of the real function boundary confirms zero recompute). |
| 4 | Range visível persiste entre reruns (`session_state`/localStorage + `setVisibleRange`); disclaimer/linguagem de estudo preservados | ✓ VERIFIED | `app.py:312-330` — `RANGE_KEY = lwc_range_<ticker>_<tf_key>`; on create: `localStorage.getItem` in `try/catch`, applies `setVisibleLogicalRange` if saved else `fitContent()` (313-322); on change: `subscribeVisibleLogicalRangeChange` writes via `localStorage.setItem` in its own independent `try/catch` (323-330), catch falls back to console.log without breaking render. Sidebar disclaimer ("Ferramenta de apoio à análise... Não é recomendação de compra ou venda...") unchanged (app.py:354-360), verified still present and untouched by the phase diff. Note: mechanism is client-side `localStorage` per (ticker, tf_key), not `session_state` as originally worded in ROADMAP/CONTEXT — documented explicitly in 17-01-SUMMARY.md as an informed adaptation (components.html has no JS→Python round-trip); observable behavior (range persists across reruns) is delivered and was human-confirmed in the browser smoke (17-03-SUMMARY.md: zoom/pan preserved after toggling an overlay). |
| 5 | 283+ testes golden verdes; verificação humana no navegador aprova o Modo Trading sem regressão | ✓ VERIFIED | `.venv/bin/python -m pytest -q` → **283 passed** (re-run independently, 2.67s, zero failures). Human browser smoke documented in `17-03-SUMMARY.md` — approved with candlestick TV-like rendering, overlays with exact canonical values (BBSE3: alvo 41,74 / Fib 39,12-38,50 / stop 37,50), crosshair with axis labels, clean console, and explicit negative-regression check across Plotly/Analisar/Ranking/Garimpo — all confirmed working. Per verification scope for this run, this human checkpoint is accepted as already satisfied (not re-executed). |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app.py` — `def _render_lwc(...)` | Function renders LWC candlestick | ✓ VERIFIED | `app.py:113`, signature `def _render_lwc(f, sw, sinais, est, ticker, tf_key):` matches plan contract exactly |
| `app.py` — CDN `lightweight-charts@5.2.0` pinned + SRI | Version-pinned CDN with real SRI hash | ✓ VERIFIED | `app.py:105-108,200`; hash independently re-computed and matches |
| `app.py` — toggle "Modo Trading" | Radio/segmented control gating Plotly vs LWC | ✓ VERIFIED | `app.py:920-928`, key `swing_vista`, default `"Plotly"` |
| `app.py` — `BandPrimitive` helper | Series primitive for bands | ✓ VERIFIED | `app.py:232-253`, reused for entrada/suportes/resistencias |
| `app.py` — `createPriceLine` for stop/alvo/Fib | Labeled lines | ✓ VERIFIED | `app.py:262-269,295` |
| `app.py` — `createSeriesMarkers` for pivots/patterns | Markers | ✓ VERIFIED | `app.py:279-300` |
| `.phase-base-sha` | Fixed base SHA for invariance gate | ✓ VERIFIED | Exists at `.planning/phases/17-.../.phase-base-sha` = `5a93e24f05bcb336bce99115e9c29b3f57a0aeae`; confirmed present and used correctly in diff checks |
| `17-03-SUMMARY.md` | Registro da verificação (goldens + smoke) | ✓ VERIFIED | Present, documents automated + human evidence |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `app.py:_render_lwc` | `f.ohlc` | Serialização OHLC → JSON candles/vols | ✓ WIRED | `app.py:123-134`, no recalculation, direct `df = f.ohlc` iteration |
| toggle de vista | `_render_lwc` vs bloco Plotly | ramo condicional | ✓ WIRED | `app.py:979-983` (`if vista == "Modo Trading": _render_lwc(...)` else Plotly branch) |
| `_render_lwc` | `sw.entrada_zona/sw.stop/sw.alvo` | serialização read-only | ✓ WIRED | `app.py:162-168` |
| `_render_lwc` | `sinais.niveis` / `sinais.padroes` | serialização read-only | ✓ WIRED | `app.py:156-194` |
| overlay JS | `est["sr_on"\|"niveis_setup_on"\|"fib_on"\|"padroes_on"]` | flags Python passadas ao template | ✓ WIRED | `app.py:156,162,170,178` — same `est` dict as Plotly branch (line 913), true parity |

### Behavioral Spot-Checks / Automated Gates Re-Run Independently

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Golden suite green | `.venv/bin/python -m pytest -q` | `283 passed in 2.67s` | ✓ PASS |
| `grafico.py` untouched vs phase base | `git diff --name-only "$BASE"..HEAD -- src/analista/grafico.py` | empty | ✓ PASS |
| Syntax valid | `python -c "import ast; ast.parse(open('app.py').read())"` | `app.py OK syntax` | ✓ PASS |
| `_render_lwc` present | `grep -n "def _render_lwc" app.py` | line 113 | ✓ PASS |
| CDN pinned to v5.2.0 | `grep -c "lightweight-charts@5.2.0" app.py` | 1 | ✓ PASS |
| SRI hash present and real | `grep -n 'integrity="sha384-' app.py` + independent `curl`+`openssl dgst -sha384` re-computation | matches exactly | ✓ PASS |
| No legacy v4 API | `grep -c "addCandlestickSeries" app.py` | 0 | ✓ PASS |
| Zero new Python deps | `git diff` import lines added | only `json`, `streamlit.components.v1` | ✓ PASS |
| `_render_lwc` does not recompute engine | manual `sed -n '113,335p' app.py \| grep "indicators.calcular\|montar_setup"` | no match | ✓ PASS (plan's own `awk` gate is a false positive due to a nested `def` not at column 0 later in the file — see truth #3 note) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|-------------|--------------|--------|----------|
| LWC-01 | 17-01 | Toggle "Modo Trading" + candlestick LWC v5 base (scroll-zoom, pan, crosshair, Y-autoscale, last price) | ✓ SATISFIED | `app.py:920-983`, `_render_lwc` chart config; human smoke confirmed |
| LWC-02 | 17-02 | Overlays da engine portados (BandPrimitive/createPriceLine/createSeriesMarkers), read-only, gated by `est[...]` | ✓ SATISFIED | `app.py:143-330` |
| LWC-03 | 17-01 | Persistência do range visível entre reruns | ✓ SATISFIED | `app.py:306-330`, localStorage-based mechanism (documented deviation from literal "session_state" wording, same observable behavior) |

No orphaned requirements found — `.planning/REQUIREMENTS.md` maps only LWC-01/02/03 to Phase 17 and all three are claimed by the plans and satisfied in code.

**Documentation note (non-blocking):** `.planning/REQUIREMENTS.md` line 96-98 summary table still shows LWC-01/02/03 status as "Planned" while the detailed checklist (lines 108-110) below already marks them `[x]` (completed 2026-07-01, consistent with ROADMAP.md marking Phase 17 complete). This is a stale status label in the summary table, not a code or requirements-traceability defect — flagged as info only.

### Anti-Patterns Found

None. Scanned the phase's added code (`app.py` lines 95-335, the entire `_render_lwc` region plus toggle wiring) for `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`/"coming soon"/"not yet implemented" — zero matches. All `localStorage`/overlay JS blocks are wrapped in `try/catch` with graceful degradation (no silent empty-return stubs affecting rendering).

### Human Verification Required

None outstanding. The one interactive/visual checkpoint required by the phase plan (Task 2 of 17-03-PLAN.md, browser smoke via Claude-in-Chrome) was already executed and approved, with detailed evidence recorded in `17-03-SUMMARY.md` (canonical BBSE3/Diário values, crosshair, console-clean, explicit regression check across Plotly/Analisar/Ranking/Garimpo). Per this verification's scope, that checkpoint is accepted as satisfied rather than re-run.

One residual limitation was disclosed and accepted by the human reviewer: scroll-zoom could not be exercised by an automated/machine actor because the mouse wheel over the Streamlit `components.html` iframe scrolls the parent page rather than the chart; pan and crosshair were confirmed live on the same chart instance, and scroll-zoom is LWC v5's default behavior (`handleScroll`/`handleScale` both enabled in the config at `app.py:210`). This is a known tooling limitation, not a code defect, and does not block phase acceptance.

### Gaps Summary

No gaps. All 5 ROADMAP.md success criteria for Phase 17 are verified in code (re-verified independently, not merely trusted from SUMMARY.md), all 3 requirement IDs (LWC-01/02/03) are satisfied, the 283 golden tests pass, `grafico.py` is provably untouched since the phase's recorded base SHA, `app.py`'s `_render_lwc` is confirmed read-only by direct inspection of its true function boundary, the SRI hash was independently re-computed and matches, and the human browser-smoke checkpoint was already completed and approved with detailed evidence. The only documentation nit (stale "Planned" status label in REQUIREMENTS.md's summary table) is informational and does not affect the phase's functional completeness.

---

*Verified: 2026-07-01T14:35:33Z*
*Verifier: Claude (gsd-verifier)*
