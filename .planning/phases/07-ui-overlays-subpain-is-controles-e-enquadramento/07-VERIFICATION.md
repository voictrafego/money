---
phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
verified: 2026-06-27T00:00:00Z
status: human_needed
score: 4/4 must-haves verified (automated); visual/behavioral aspects require human sign-off
overrides_applied: 0
human_verification:
  - test: "Fresh-reader test UI-06 — open app, analyze a paper rated SOBREAVALIADA or VERIFICAR with bullish technical indicators enabled, and confirm the fundamental veredito (top banner) is perceived as the decisive signal, not the consultive timing section below."
    expected: "A new user should clearly read the fundamentalist veredito (st.success/error/warning banner at the top) as the decision-maker. The technical section (expander closed by default, markdown/caption below the chart) should feel subordinate and consultive."
    why_human: "Visual hierarchy and perceived framing cannot be verified programmatically. This checkpoint was approved by the user during phase execution (07-05-SUMMARY Task 3 'approved'). Re-verify after any UI refactoring."
  - test: "Overlays and subpanels render correctly in Streamlit — open app, analyze TAEE11 or EGIE3, enable Tendencia (SMA 50/200), ADX, RSI, MACD; verify overlays appear on the price panel and oscilador subpanels appear below."
    expected: "SMA lines on the price panel; RSI/ADX/MACD in separate rows with reference lines (30/70 for RSI, 20/25 for ADX, 0 for MACD); toggling off removes them without re-fetching data."
    why_human: "Streamlit visual rendering and Plotly subplot layout cannot be exercised in a headless test environment."
  - test: "Donchian marker density — enable Canais (Donchian 20) on a stock with a sustained price breakout. Verify whether the chart shows a single entry-triangle or a dense cluster of triangles on consecutive bars."
    expected: "Ideally one marker per breakout entry (per code-review finding WR-02). Currently the code fires per-bar during a run. Assess whether visual density is acceptable or whether the WR-02 fix should be applied before release."
    why_human: "Behaviorally, the markers are at exact dates (correct) but there may be too many per event. Human judgment needed on the acceptable density threshold."
---

# Phase 7: UI Overlays / Subpainéis / Controles / Enquadramento Verification Report

**Phase Goal:** A aba Analisar passa a desenhar os overlays no eixo de preço e os osciladores em subpainéis dinâmicos, com controles para ligar/desligar e selecionar indicadores, marcadores de evento nas datas exatas, tooltips de glossário, e um enquadramento que mantém o veredito fundamentalista visivelmente decisório — tudo lendo `a.sinais` em modo read-only.
**Verified:** 2026-06-27
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Overlays (MMs/Donchian/Bollinger) desenhados no eixo de preço (UI-01) e osciladores (RSI/MACD/ADX) em subpainéis dinâmicos via make_subplots, criados só quando ativos (UI-02). | VERIFIED | `grafico.py` lines 88-173: `overlays_preco()` returns `OverlaySpec` list; `subpaineis_ativos()` returns `SubpainelSpec` list only for active toggles with valid series. `app.py:14` imports `make_subplots`; `app.py:207-267` consumes specs without hardcoding series names or reference levels. 10 golden tests in `test_grafico_ui.py` pass. Full suite: 148 passed. |
| 2 | Usuário liga/desliga e seleciona indicadores; estado por sessão (st.session_state); redesenha sem recomputar (UI-03). | VERIFIED | `app.py:149`: `st.session_state.setdefault("tec_estado", grafico.estado_padrao())`. `app.py:151`: `st.expander(..., expanded=False)` — off by default. `app.py:144`: `grafico_box = st.container()` slot reserved at top, filled after controls update `tec_estado` in the same rerun (no lag, no engine recompute). `grafico._merge()` tolerates partial state. Minor WR-01 warning: empty `janelas` selection falls back to `[20,50,200]` (see Anti-Patterns). |
| 3 | Eventos marcados nas datas exatas (UI-04); cada indicador tem tooltip de glossário acessível em paridade com o app (UI-05). | VERIFIED | UI-04: `grafico.marcadores_eventos()` computes golden/death-cross by sign-change on `sma50-sma200` (transition logic); Donchian markers per-bar (WR-02 warning: entry-only logic missing, see Anti-Patterns). `app.py:210`: `marcadores_eventos(a.sinais, a.sinais.close)` — read-only. UI-05: 11 `tec_*` keys confirmed in `glossario.py`; all referenced via `help=h("tec_*")` in app.py controls. `test_glossario.py` 2/2 pass. |
| 4 | Bloco técnico subordinado ao veredito fundamentalista (off por padrão, seção secundária, linguagem consultiva); fresh-reader test UI-06. | VERIFIED (human approval on record) | `app.py:151`: expander `expanded=False`. `app.py:113-118`: veredito via `st.success/error/warning` (top banner). `app.py:291-298`: timing/matriz rendered as `st.markdown`/`st.caption` (not a banner); degradation as `st.caption("Leitura técnica indisponível...")`. No "compre/venda" in tec_* glossary (`test_tom_consultivo` passes). Checkpoint "approved" by user during phase execution (07-05-SUMMARY Task 3). |

**Score:** 4/4 truths verified (automated checks). Visual rendering and fresh-reader framing require human sign-off (status: human_needed).

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/grafico.py` | Pure functions + dataclasses: `estado_padrao`, `overlays_preco`, `subpaineis_ativos`, `layout_subplots`, `marcadores_eventos`, `leitura_tecnica_disponivel`, `OverlaySpec`, `SubpainelSpec`, `Marcador` | VERIFIED | 237 lines; all 6 functions and 3 dataclasses present. Zero streamlit/plotly imports confirmed by grep. |
| `src/analista/glossario.py` | 11 `tec_*` keys accessible via `h()` | VERIFIED | Keys: tec_indicadores, tec_mm, tec_cross, tec_donchian, tec_bollinger, tec_squeeze, tec_rsi, tec_macd, tec_adx, tec_regressao, tec_timing. All confirmed non-empty. None contain "compre"/"venda". |
| `src/analista/core/indicators.py` | `SinaisTecnicos.close: pd.Series = None` (additive field) | VERIFIED | Line 91: `close: pd.Series = None`. Populated in `calcular()` as the same split-adjusted series used by indicators — read-only by construction. |
| `src/analista/report/report.py` | Holistic degradation: `not a.timing_resumo => matriz_leitura=""` | VERIFIED | Lines 267-271: `a.matriz_leitura` is set then overridden to `""` when `not a.timing_resumo`. Line 455: markdown guard by `not a.timing_resumo`. Lines 223-227: resample guard by `isinstance(ohlc.index, pd.DatetimeIndex)`. |
| `app.py` | `make_subplots`, `overlays_preco`, `subpaineis_ativos`, `marcadores_eventos`, session_state, `h("tec_*")`, degradation caption, veredito at top | VERIFIED | All 8 programmatic gates pass (AST parse + grep checks). Expander `expanded=False`. |
| `tests/test_glossario.py` | `test_chaves_tec_presentes` + `test_tom_consultivo` | VERIFIED | 2/2 tests pass. |
| `tests/test_grafico_ui.py` | Golden tests for all pure functions | VERIFIED | 10/10 tests pass including overlays/subpanels/layout/markers/degradation. |
| `tests/test_report.py` | `test_degradacao_so_de_forca` (holistic degradation) | VERIFIED | Test present at line 274; passes as part of suite. |
| `tests/test_indicators.py` | `test_sinais_close_paridade` + `test_sinais_close_frame_vazio` | VERIFIED | Both tests present and pass. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `app.py` (gráfico) | `grafico.overlays_preco / subpaineis_ativos / marcadores_eventos / layout_subplots` | `state = st.session_state["tec_estado"]` fed to pure functions | WIRED | `app.py:204-267`: reads estado, calls all 4 functions, consumes specs. No hardcoded name→series mapping or reference levels. |
| `app.py` (marcadores) | `a.sinais.close` | `marcadores_eventos(a.sinais, a.sinais.close)` | WIRED | `app.py:210`: exact pattern `a.sinais.close` present. |
| `app.py` (expander controls) | `st.session_state["tec_estado"]` | Toggles write to the dict initialized by `grafico.estado_padrao()` | WIRED | `app.py:149-187`: setdefault → write to est keys. |
| `app.py` (controles/seção técnica) | `analista.glossario.h` | `help=h("tec_*")` on each widget | WIRED | grep confirms: `h("tec_indicadores")`, `h("tec_mm")`, `h("tec_cross")`, `h("tec_donchian")`, `h("tec_bollinger")`, `h("tec_adx")`, `h("tec_rsi")`, `h("tec_macd")`, `h("tec_timing")` all present in app.py. |
| `report.py (analisar_acao)` | `a.matriz_leitura` | collapse when `not a.timing_resumo` | WIRED | Lines 266-271 confirmed. |
| `indicators.py (calcular)` | `SinaisTecnicos.close` | `close=close` in constructor | WIRED | `calcular()` assigns `close=close` (the split-adjusted series already in scope) when building SinaisTecnicos. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `app.py` (overlays) | `overlays` from `grafico.overlays_preco(estado, a.sinais)` | `a.sinais.tendencia.sma*/ema*` — real pd.Series from `indicators.calcular()` | Yes — series are computed from real OHLC in the engine | FLOWING |
| `app.py` (subpanels) | `specs` from `grafico.subpaineis_ativos(estado, a.sinais)` | `a.sinais.forca.adx`, `a.sinais.momentum.rsi/macd/macd_sinal/macd_hist` | Yes — real engine output series | FLOWING |
| `app.py` (markers) | `marcadores` from `grafico.marcadores_eventos(a.sinais, a.sinais.close)` | `a.sinais.tendencia.sma50/sma200`, `a.sinais.canais.donchian_sup/inf`, `a.sinais.close` | Yes — real series from engine + real close series | FLOWING |
| `app.py` (timing section) | `a.timing_resumo`, `a.matriz_leitura`, `a.alerta_reverificacao` | `report.analisar_acao(c, CFG)` | Yes — populated by Phase 6 engine logic | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| app.py AST valid | `python -c "import ast; ast.parse(open('app.py').read())"` | No error | PASS |
| make_subplots imported and used | `grep -q "make_subplots" app.py` | found | PASS |
| grafico.py has no UI imports | `grep "import streamlit\|import plotly" grafico.py` | 0 matches | PASS |
| All 11 tec_* glossary keys non-empty | Python assertion check | `ok 11 keys` | PASS |
| Full test suite | `python -m pytest -q` | 148 passed | PASS |
| Phase-relevant tests | `python -m pytest tests/test_glossario.py tests/test_grafico_ui.py tests/test_report.py tests/test_indicators.py -q` | 41 passed | PASS |

---

### Probe Execution

No conventional `scripts/*/tests/probe-*.sh` files defined for this phase. Step 7c: SKIPPED (no probes declared; phase relies on pytest golden tests).

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| UI-01 | Plans 03, 05 | Overlays (MMs/Donchian/Bollinger) on the price axis | SATISFIED | `overlays_preco()` in grafico.py; consumed in app.py row 1 |
| UI-02 | Plans 03, 05 | Osciladores in dynamic make_subplots subpanels, created only when active | SATISFIED | `subpaineis_ativos()` returns SubpainelSpec; make_subplots in app.py |
| UI-03 | Plans 03, 04, 05 | User can toggle/select indicators; state per session; redraws without recomputing | SATISFIED (with WR-01 caveat) | st.session_state["tec_estado"]; st.container() slot pattern |
| UI-04 | Plans 01, 03, 05 | Events marked at exact dates | SATISFIED (with WR-02 caveat) | `marcadores_eventos()` with sign-change logic for cross; per-bar Donchian (acceptable, WR-02) |
| UI-05 | Plans 02, 04 | Tooltips for each indicator via h("tec_*") | SATISFIED | 11 tec_* keys; all widgets use help=h("tec_*") |
| UI-06 | Plans 01, 03, 04, 05 | Technical block subordinate to fundamentalist veredito | SATISFIED | expander expanded=False; veredito as top banner; timing as markdown/caption; degradation caption |

All 6 required requirements (UI-01 through UI-06) are addressed and satisfied.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/analista/grafico.py` | 107 | `or [20, 50, 200]` falsy-check causes empty selection to draw all 3 MAs | WARNING (WR-01 from code review) | Empty `janelas` multiselect draws all MAs instead of none — contradicts user intent. Not a blocker; fix: `janelas = t.get("janelas"); if janelas is None: janelas = [...]` |
| `src/analista/grafico.py` | 219-226 | Donchian markers fire on every bar where `close > sup`, not only on breakout entry | WARNING (WR-02 from code review) | Sustained breakout produces dense cluster of identical markers. Golden test only asserts `markers[0].data`, not uniqueness. Not a goal blocker; fix: transition logic mirroring cross detection. |
| `src/analista/glossario.py` | 149, 171 | `tec_squeeze` and `tec_regressao` defined and tested but not exposed in any UI control | INFO (IN-02 from code review) | Dead glossary keys — no squeeze or regression toggle in app.py. Not a bug; the engine computes them but the UI doesn't surface them. |
| `app.py` | 235 | `line=dict(ov.estilo)` redundant dict() wrapper | INFO (IN-01 from code review) | Reads as defensive copy but is just `line=ov.estilo`. Works correctly. |

No `TBD`, `FIXME`, or `XXX` debt markers found in any Phase 7 modified file.

**CR-01/DATA-02 note (from 07-REVIEW.md):** The code review identified a critical issue (overlays/markers on split-adjusted basis drawn on a nominal price axis). This is explicitly documented as a **user-approved tradeoff** in `PROJECT.md` line 135: "Série do gráfico = Close nominal (auto_adjust=False) [...] Eixo Y do gráfico tem de ficar na mesma base da banda DDM (nominal); senão preços retroajustados distorcem a margem de segurança (CR-01) | ✓ Good — Phase 3". The verification task instructions confirm: "The CR-01/DATA-02 split-vs-nominal overlay alignment is a DOCUMENTED, user-approved tradeoff (PROJECT.md decision), not a defect." This is NOT a blocker.

---

### Human Verification Required

#### 1. Fresh-reader test UI-06

**Test:** Run `streamlit run app.py`, analyze a paper rated "SOBREAVALIADA" or "VERIFICAR". Enable Tendencia (SMA 50/200) and RSI so technical indicators show bullish timing. Look at the screen as a new user would.
**Expected:** The fundamental veredito banner (top, colored) is perceived as the decision-maker. The technical section (expander closed by default, markdown/caption below chart) feels consultive and secondary — not a buy recommendation.
**Why human:** Visual hierarchy and perceived framing cannot be determined programmatically. NOTE: this checkpoint was already approved by the user during phase execution (07-05-SUMMARY: Task 3 "APROVADO pelo usuário ('approved')"). Re-verify only if UI layout changes.

#### 2. Chart rendering — overlays and subpanels

**Test:** Analyze TAEE11 or EGIE3. Enable: Tendencia (SMA, janelas 50+200), ADX, RSI, MACD, Donchian 20, Bollinger. Confirm: MMs appear on the price panel; ADX/RSI/MACD appear in separate sub-rows with correct reference lines (ADX 20/25, RSI 30/70, MACD 0); disabling them removes the subpanels. No data re-fetch spinner when toggling.
**Expected:** Correct visual layout; no lag; toggles work.
**Why human:** Plotly make_subplots rendering and Streamlit interaction cannot be exercised in a headless environment.

#### 3. Donchian marker density (WR-02 severity assessment)

**Test:** Enable Canais (Donchian 20) on a stock that had a sustained breakout in the last 5 years. Observe whether a single entry-triangle appears or a dense cluster of triangles on consecutive bars.
**Expected:** Ideally one marker per breakout entry. Current behavior is per-bar (WR-02). Assess whether this is visually acceptable or if the fix should be applied before release.
**Why human:** The code behavior is deterministic but the visual acceptability is a product judgment call.

---

### Gaps Summary

No blockers. All 4 must-have truths are verified by code inspection and automated tests (148 passing, including 41 Phase 7-specific tests). The two code-review warnings (WR-01 empty-janelas fallback, WR-02 per-bar Donchian markers) are behavioral/UX issues, not correctness blockers. The CR-01/DATA-02 split alignment is a documented user-approved tradeoff.

Status is `human_needed` because the fresh-reader test (UI-06 framing quality), chart rendering (make_subplots visual layout), and Donchian marker density (WR-02 severity) require human judgment that cannot be verified programmatically.

---

_Verified: 2026-06-27_
_Verifier: Claude (gsd-verifier)_
