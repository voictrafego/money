# Phase 6: Integração na engine + composite + alerta + CLI - Pattern Map

**Mapped:** 2026-06-26
**Files analyzed:** 3 (1 modified core, 1 modified config, 1 new test)
**Analogs found:** 3 / 3 (every concern has an in-repo analog; only the OHLC weekly resample is partly novel)

> All work happens **inside the existing engine**. There are no new modules to create — Phase 6 is
> additive editing of `report.py` + one config key + one new golden test file. Every pattern the
> planner needs already exists in `report.py`, `indicators.py`, or the test suite. Copy them; do not
> invent new shapes.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/report/report.py` (MODIFY) | service / report-builder | transform (read fundamentals+sinais → consultative text) | itself (existing `analisar_acao` veredito block + `relatorio_markdown` sections) | exact (self) |
| ↳ `AnaliseAcao` dataclass field additions | model | — | `AnaliseAcao` lines 20-40; `Forca`/`Momentum` in indicators.py | exact |
| ↳ composite/matrix/alert derivation helpers | service | transform / decision-tree | `_forca` / `_momentum` discrete-label classifiers (indicators.py 327-394); veredito block (report.py 114-124) | exact |
| ↳ weekly resample of OHLC | utility | transform (daily→weekly candle aggregation) | none (novel — pandas `.resample("W-FRI")`); shape mirrors `calcular(ohlc, cfg)` boundary guard | partial |
| ↳ `relatorio_markdown` "Sinais técnicos (consultivos)" section | view | request-response (string build) | Veredito + Alertas section (report.py 233-241); DDM degraded-fallback (204-231) | exact |
| `config.yaml` (MODIFY) — base temporal key | config | — | `indicadores:` block (config.yaml 70-84) | exact |
| `tests/test_report.py` (NEW) — TEST-06 + resample | test | — | `tests/test_indicators.py` (fixtures + label asserts) + `tests/test_ddm.py` (exact-value asserts) | exact |

There is **no `tests/test_report.py` today** — it is a new file. Existing tests in `tests/`:
`test_ddm`, `test_multiples`, `test_indicators`, `test_comparables`, `test_consistencia_modos`,
`test_fundamentals_consistencia`, `test_ingest_ohlc`, `test_ingest_resolucao`, `test_screening`.

---

## Pattern Assignments

### `AnaliseAcao` dataclass — add `sinais` + composite + alert fields (model)

**Analog:** the dataclass itself, `report.py` lines 20-40. Mirror its conventions exactly: every
new field is `Optional[...] = None` (or `field(default_factory=...)` for collections), placed at the
**end** of the existing fields (additive, never reordering — same discipline as `Canais.donchian_sup_55`
in indicators.py line 59 which was appended with a default to avoid breaking the locked contract).

**Existing shape to copy** (`report.py` 20-40):
```python
@dataclass
class AnaliseAcao:
    ticker: str
    nome: str
    setor: str
    preco_atual: Optional[float]
    multiplos: Dict[str, Optional[float]] = field(default_factory=dict)
    ...
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    veredito: str = ""
    alertas: List[str] = field(default_factory=list)
```

**Apply (Claude's Discretion on exact names, per CONTEXT D-92/discretion block):**
```python
    # --- Phase 6: read técnico consultivo (aditivo, read-only sobre o fundamento) ---
    sinais: Optional["indicators.SinaisTecnicos"] = None   # populado por indicators.calcular
    timing_estado: str = ""                                # "tendencia_de_alta"|"sem_tendencia"|"atencao"
    timing_resumo: str = ""                                # frase PT consultiva (TIMING-01)
    matriz_leitura: str = ""                               # frase curada fundamento×técnico (TIMING-02)
    alerta_reverificacao: Optional[str] = None             # None se nada rompeu (degradação graciosa)
```
Note the **string-default-`""`** convention for present-but-empty (mirrors `veredito: str = ""`,
`estagio: str = ""`) vs **`None`** for "not computed / degraded" (mirrors `vmin`, `ke`). Use `""`
for fields always derivable and `None` for the alert (which is absent when no breakout — D-07).

Import nuance: `indicators` is **not** yet imported in `report.py`. The existing core imports are at
lines 15-17 (`from ..core import capm, ddm, growth, lifecycle`). Add `indicators` to that line.

---

### `analisar_acao` — populate `sinais` + derive composite/matrix/alert (service, transform)

**Analog A — where to populate `sinais`:** insert AFTER the veredito block (report.py 114-124), so
the matrix derivation can read `a.veredito`/`a.vmin`/`a.vmax` already computed. CONTEXT C-148 confirms
`analisar_acao` is the single point. The function already ends with `return a` (line 141) right after
the alerts block — the new derivation goes between the alerts block and `return a`, OR right after
veredito. Recommended: right after veredito (line 124) so the alert can also be appended into the same
flow.

**Analog B — discrete-label classifier (the composite decision tree, D-01/D-02):** copy the EXACT
threshold→string→"indisponivel" idiom from `indicators._forca` (indicators.py 337-344). This is the
canonical "read the tip, branch on thresholds, degrade gracefully" pattern the composite must mirror:
```python
    if len(adx.dropna()) == 0 or pd.isna(adx.iloc[-1]):
        forca_adx = "indisponivel"
    elif adx.iloc[-1] < 20.0:
        forca_adx = "sem_tendencia"
    elif adx.iloc[-1] > 25.0:
        forca_adx = "forte"
    else:
        forca_adx = "neutro"
```
The composite does NOT re-read the ADX float — per CONTEXT discretion ("reusar os já definidos em
`indicators._forca`"), it reads the **already-classified** discrete labels off `a.sinais`:
`a.sinais.tendencia.posicao_mm200` ("acima"/"abaixo"/"indisponivel"),
`a.sinais.forca.forca_adx` ("sem_tendencia"/"forte"/"neutro"/"indisponivel"),
`a.sinais.tendencia.cruzamento`, `a.sinais.canais.rompimento_donchian`,
`a.sinais.momentum.nivel_rsi`, `a.sinais.momentum.cruzamento_macd`.

**Decision tree to implement (D-01/D-02/D-03) — MM200 direction, ADX confirms force:**
```python
    pos = a.sinais.tendencia.posicao_mm200
    forca = a.sinais.forca.forca_adx
    if pos == "indisponivel" or forca == "indisponivel":
        a.timing_estado = "sem_tendencia"        # degradação graciosa (DATA-03)
    elif pos == "acima" and forca == "forte":
        a.timing_estado = "tendencia_de_alta"
    elif pos == "abaixo":
        a.timing_estado = "atencao"
    else:                                         # acima mas ADX fraco/neutro → TEST-06 canônico (D-02)
        a.timing_estado = "sem_tendencia"
```
D-03: RSI/MACD only refine the `timing_resumo` PHRASE inside the chosen state — they never change
`timing_estado`.

**Analog C — veredito-style string composition for the matrix (D-04, fundamento lidera):** copy the
veredito block's "branch on computed state → format a natural-language string" idiom (report.py 118-124):
```python
    if a.preco_atual < a.vmin:
        a.veredito = f"SUBAVALIADA — preço R$ {a.preco_atual:.2f} abaixo do intervalo ..."
    elif a.preco_atual > a.vmax:
        a.veredito = f"SOBREAVALIADA — ..."
    else:
        a.veredito = f"NO INTERVALO — ..."
```
The matrix READS `a.veredito` (parse its leading token SUBAVALIADA/NO INTERVALO/SOBREAVALIADA) ×
`a.timing_estado` and selects a **pre-written curated phrase per cell** (D-04 — NOT a composing
template). The two anchor cells are verbatim from CONTEXT D-05/D-06:
- BARATO + atenção → `"Fundamentalmente descontada, porém o preço perdeu a tendência — confirme que os fundamentos seguem intactos antes de entrar."`
- CARO + alta → `"Tecnicamente em alta, porém acima do valor intrínseco — o método não compra caro; aguarde um preço melhor."`

**Analog D — alert assembly (D-07/D-09, consolidated OR-of-three):** copy the `a.alertas.append(...)`
accumulation idiom (report.py 126-140), but consolidate into ONE message (D-09). Read the three
already-classified bearish labels off `a.sinais`:
```python
    gatilhos = []
    if a.sinais.tendencia.posicao_mm200 == "abaixo":
        gatilhos.append("preço abaixo da MM200")
    if a.sinais.tendencia.cruzamento == "death_cross":
        gatilhos.append("cruzamento de baixa MM50×MM200")
    if a.sinais.canais.rompimento_donchian == "perda_minima":
        gatilhos.append("rompimento da mínima do canal")
    if gatilhos:
        a.alerta_reverificacao = (
            "Reverifique os fundamentos: " + "; ".join(gatilhos)
            + ". Não é sinal de venda — confirme se os números seguem intactos."
        )
```
Voice is ALWAYS "reverifique os fundamentos", never "venda" (D-09). Fires regardless of veredito (D-08).

**Analog E — weekly resample boundary (D-10/D-11/D-12) — PARTLY NOVEL:** there is no existing resample
in the repo, but the **boundary guard** to copy is `calcular`'s None/empty handling (indicators.py
412-413) and the cfg-default idiom `cfg.get("universo", {}).get("ano_base")` (report.py 136). Read the
base from cfg with a default, resample `c.ohlc_ajustado` (NOT `c.ohlc` — split-adjusted is the
indicator input per CR-01, fundamentals.py line 47), then feed the result to `indicators.calcular`
(which is explicitly timeframe-agnostic per its docstring, indicators.py 409-410):
```python
    base = cfg.get("indicadores", {}).get("base_temporal", "semanal")   # default semanal (D-12)
    ohlc = c.ohlc_ajustado
    if base == "semanal" and ohlc is not None and len(ohlc) > 0:
        ohlc = ohlc.resample("W-FRI").agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
        ).dropna()
    a.sinais = indicators.calcular(ohlc, cfg)   # calcular tolera None/curto → "indisponivel"
```
`calcular` already substitutes an empty frame and degrades to "indisponivel" if `ohlc` is None/short
(indicators.py 412-413) — DO NOT add a second guard; route through it (single degradation point).

---

### `relatorio_markdown` — "Sinais técnicos (consultivos)" section (view, CLI-01/D-13)

**Analog:** the Veredito + Alertas section (report.py 233-241) — the closest in shape (a heading,
a bold line, then a conditional bulleted sub-block) — plus the DDM section's degraded fallback
(report.py 229-231) for the short-history / `ohlc=None` case.

**Veredito+Alertas pattern to mirror** (report.py 233-241):
```python
    L.append("## Veredito")
    L.append(f"**{a.veredito or 'Indeterminado'}**")
    if a.alertas:
        L.append("")
        L.append("### Alertas")
        for al in a.alertas:
            L.append(f"- ⚠️ {al}")
    L.append("")
```

**Degraded-fallback pattern to mirror** (report.py 229-231) — for when sinais are all "indisponivel":
```python
    else:
        L.append("_DDM não calculado (faltam Beta/Ke, payout ou crescimento)._")
        L.append("")
```

**Apply (placement: after Veredito, before final `return "\n".join(L)` at line 242):**
```python
    L.append("## Sinais técnicos (consultivos)")
    if a.sinais is None or a.timing_estado == "" or a.sinais.tendencia.posicao_mm200 == "indisponivel":
        L.append("_Histórico de preços insuficiente para o read técnico._")
        L.append("")
    else:
        L.append(f"**Timing de entrada:** {a.timing_resumo}")
        L.append("")
        L.append(a.matriz_leitura)              # fundamento-primeiro (D-04)
        if a.alerta_reverificacao:
            L.append("")
            L.append(f"- ⚠️ {a.alerta_reverificacao}")
        L.append("")
```
Section format is planner discretion (D-13) but MUST use the `L.append(...)` list idiom and end with a
blank `L.append("")` like every other section. The same `⚠️` bullet glyph as the Alertas block keeps
visual parity.

---

### `config.yaml` — base temporal key (config, D-12)

**Analog:** the `indicadores:` block (config.yaml 70-84). Add the canonical key INSIDE `indicadores:`
(the home `analisar_acao` reads via `cfg["indicadores"]`, and `cfg.get("indicadores", {}).get(...)`
gives a safe default for tests that pass partial cfgs):
```yaml
indicadores:
  sma_emas: [20, 50, 200]
  ...
  regressao_janela: 90       # ~1 trimestre
  base_temporal: "semanal"   # "semanal" (resample W-FRI) | "diario" — default semanal (TIMING-04 / D-12)
```
Document inline with a `#` comment (every parameter in this file carries a justifying comment — see
lines 71-84). Default MUST be `"semanal"` (REQ TIMING-04).

---

## Shared Patterns

### Graceful degradation ("indisponivel" / `None`, never raise)
**Source:** `indicators._forca` (337-344), `calcular` boundary guard (412-413), veredito guard
(`if valores and a.preco_atual:` report.py 118).
**Apply to:** every composite/matrix/alert derivation and the CLI section. When `a.sinais` tip is
"indisponivel", set `timing_estado="sem_tendencia"`, leave `alerta_reverificacao=None`, and the CLI
prints the degraded fallback line. Single degradation point = route through `indicators.calcular`;
do not pre-guard the OHLC twice. This is the GRAF-03/DATA-03 contract called out in CONTEXT.

### cfg as the single home for parameters (with `.get` defaults)
**Source:** `cfg["indicadores"][...]` (indicators.py 121, 192, 333, 359); `cfg.get("universo", {}).get("ano_base")` (report.py 136); `cfg["ddm"].get("tributacao_dividendos", 0.0)` (report.py 99).
**Apply to:** base temporal read (`cfg.get("indicadores", {}).get("base_temporal", "semanal")`).
Never thread an explicit argument into `analisar_acao` (D-12 rejected that). cfg flows CLI→engine
(cli.py 30-32, 65) and app→engine (app.py 30-31, 99) identically — paridade CLI↔UI is free.

### Markdown section assembly via `L.append`
**Source:** `relatorio_markdown` lines 156-242 (every section: heading → content → blank line).
**Apply to:** the new CLI section. Use `tabulate(...)` only if tabular (the technical read is prose,
so plain bold + bullets, mirroring the Veredito section, not the Múltiplos table).

### Read-only over the fundamento (the cardinal rule)
**Source:** veredito computed once at report.py 114-124; PROJECT.md "técnica é consultiva, nunca altera
o veredito".
**Apply to:** matrix (D-04) reads `a.veredito`/`a.vmin`/`a.vmax`, never recomputes or overwrites.
Alert fires independent of veredito (D-08). All Phase 6 fields are **appended** to `AnaliseAcao`.

---

## Golden Test Patterns (`tests/test_report.py` — NEW)

**Two analogs combined:**

1. **`tests/test_indicators.py`** — deterministic fixture builders + cfg loader + discrete-label asserts.
   Copy the `_cfg_ind()` loader (test_indicators.py 15-19) verbatim — it loads the shipped `config.yaml`
   so TEST-06 pins the SAME thresholds the engine uses:
   ```python
   def _cfg_ind() -> dict:
       raiz = Path(__file__).resolve().parents[1]
       with open(raiz / "config.yaml", encoding="utf-8") as f:
           return yaml.safe_load(f)
   ```
   Copy the `np.linspace`/`np.concatenate` + `pd.date_range(..., freq="B")` series-builder idiom
   (test_indicators.py 22-28, 81-87, 222-233). For TEST-06 you must craft a close series that is
   **above its own MM200 but with ADX < 20** (sideways drift just above the long average) and assert
   the composite returns `"sem_tendencia"` — the D-02 canonical tiebreak.

2. **`tests/test_ddm.py`** — exact-value / exact-label asserts with a justifying comment per test
   (test_ddm.py 34-48). Mirror its "comment states the expected, assert pins it" style:
   ```python
   def test_composite_acima_mm200_adx_fraco_eh_sem_tendencia():
       # TEST-06 / D-02: preço ACIMA da MM200 mas ADX < 20 → "sem_tendencia" (ADX fraco vence).
       cfg = _cfg_ind()
       c = _fixture_acima_mm200_adx_fraco()      # CompanyData com ohlc_ajustado sintético
       a = report.analisar_acao(c, cfg)
       assert a.timing_estado == "sem_tendencia"
   ```

**Fixture for `analisar_acao`:** unlike `test_indicators` (which calls `_tendencia`/`_canais`
directly), TEST-06 goes through `analisar_acao(c, cfg)`, so it needs a `CompanyData` with at least
`ticker`, `ohlc_ajustado` set (the resample reads it). Build a minimal `CompanyData` (see
`fundamentals.py` — `ohlc_ajustado` is an `Optional[pd.DataFrame]` field, line 47) with a synthetic
OHLC frame; the fundamental fields can be empty (DDM degrades to "" veredito, which is fine — TEST-06
only asserts `timing_estado`). A second test should assert the **W-FRI resample** itself: feed a known
daily frame, assert the weekly frame has the expected number of rows / Friday-stamped index and that
`Open=first, High=max, Low=min, Close=last` aggregation is correct (D-10 requires a dedicated resample
golden).

**TEST-07 invariant:** the 64 existing valuation golden tests (test_ddm.py, test_multiples.py, etc.)
MUST stay green — Phase 6 is purely additive to `AnaliseAcao` and appends a markdown section, so no
existing assert should move. Run the full suite after the edit.

---

## No Analog Found

| Concern | Role | Data Flow | Reason / Mitigation |
|---------|------|-----------|---------------------|
| Weekly OHLC resample (`.resample("W-FRI").agg(...)`) | utility | transform | No resample exists in the repo yet. Use stock pandas; the boundary-guard and cfg-default idioms are copied from `calcular` (indicators.py 412) and report.py 136. Needs its own golden test (D-10). |

Everything else maps to an exact in-repo analog.

---

## Metadata

**Analog search scope:** `src/analista/report/`, `src/analista/core/` (indicators, fundamentals, ddm),
`src/analista/cli.py`, `app.py`, `config.yaml`, `tests/`.
**Files scanned:** report.py, indicators.py, fundamentals.py (ohlc fields), cli.py, config.yaml,
test_ddm.py, test_multiples.py, test_indicators.py.
**Pattern extraction date:** 2026-06-26
