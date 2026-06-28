# Phase 11: Apresentação, hierarquia e trava multi-ticker - Pattern Map

**Mapped:** 2026-06-27
**Files analyzed:** 4 (1 new module, 1 new test, 2 modified)
**Analogs found:** 4 / 4 (all exact or strong role-match — codebase is self-analogous)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/report/presentation.py` (NEW) | utility (pure presentation helpers) | transform | `src/analista/report/report.py` (`_pct`/`_num` + Múltiplos `%`-branch L396-401) | exact (same layer, same library) |
| `tests/test_presentation_multiticker.py` (NEW) | test (golden/property) | transform | `tests/test_payout_sustentavel_multiticker.py` + `tests/test_growth_robusto_multiticker.py` | exact (same 2-layer lock pattern) |
| `app.py` (MODIFIED — header m3 §L131-147; tab §L309-339; helpers §L51-56) | config/view (Streamlit thin caller) | request-response (read-only) | self (existing `fmt_pct`/`fmt_num` + `report.relatorio_markdown` parity) | exact |
| `src/analista/glossario.py` (MODIFIED — `payout_dual` L105-110, `tab_crescimento` L54-62) | config (copy/tooltip strings) | self (existing dict entries) | exact |

---

## Pattern Assignments

### `src/analista/report/presentation.py` (NEW — utility, transform)

**Analog:** `src/analista/report/report.py` — same `report/` package, already houses the
markdown/CLI presentation layer. The new module is the **Streamlit-side twin** of the CLI
formatting that already lives there. It must be **pure and importable without Streamlit**
(no `import streamlit`, no import-time side effects) — D-09.

**Module header / imports pattern** (mirror `report.py` L1-18 — module docstring tying it to
the method, `from __future__ import annotations`, `Optional` typing, NO streamlit import):
```python
from __future__ import annotations
from typing import Optional
# pure: NO `import streamlit`. Only stdlib + (optionally) the AnaliseAcao type for hints.
```

**Format-helper pattern to MOVE from `app.py` L51-56** (these are the canonical sentinels —
keep `"—"` em-dash exactly; the UI-SPEC §Formatting locks `fmt_pct(x, casas=1)` =
`"—" if x is None else f"{x*100:.1f}%"`):
```python
def fmt_pct(x, casas=1):
    return "—" if x is None else f"{x*100:.{casas}f}%"

def fmt_num(x, casas=2):
    return "—" if x is None else f"{x:.{casas}f}"
```
Note `report.py` has its OWN `_pct`/`_num` (L357-362) that use `"-"` (hyphen) sentinel and
`{x*100:.1f}%`. The app uses `"—"` (em-dash). **Do NOT unify the sentinel** — UI-SPEC L99-101
locks the em-dash for the app surface and "do not change separators this phase". The new module
serves the app, so it uses the em-dash `"—"` variant (move `app.py`'s versions, don't import
report's).

**Core transform pattern — the `%`-vs-`fmt_num` routing branch** (this is the bug locus DYR-02).
Analog is the CLI loop at `report.py` L396-401 which ALREADY routes `"DY rec."` through `_pct`:
```python
# report.py L396-401 (the CORRECT parity target — includes "DY rec.")
for k, v in a.multiplos.items():
    if k in ("ML", "ROE", "DP (payout)", "DY", "DY rec.", "EY"):
        mlin.append([k, _pct(v)])
    else:
        mlin.append([k, _num(v)])
```
The app's branch at `app.py` L324 is the BUGGY one — `("ML","ROE","DY","EY")` **omits "DY rec."**
(and "DP (payout)" is special-cased above it). The extracted helper must format `"DY rec."` as
`%`. Recommended helper: a pure `linhas_multiplos(multiplos: dict, payout_ult, payout_proj) -> list[tuple[str,str]]`
that returns the assembled `(label, formatted_value)` rows, so the test asserts on the rows
directly.

**Header-selection pattern (HIER-01 / D-01,D-02,D-03)** — pure function that picks recorrente vs
trailing and returns the primary value + delta + label, with the None-fallback. No analog exists
(app currently just reads one field at L134); model it on the engine's own CRU-vs-sustentável
boundary (`report.py` L155-158). Suggested signature:
```python
def header_dy(dy_recorrente: Optional[float], dy_atual: Optional[float]) -> dict:
    # returns {"label","value","delta","delta_color","help","fallback":bool}
    # primary = recorrente as %; delta = "trailing {fmt_pct(dy_atual)}" with delta_color="off"
    # fallback (recorrente is None): primary = trailing, label "Dividend Yield (trailing)", no delta
```
Copy exact pt-BR strings from UI-SPEC §Copywriting Contract L146-153 (labels) and L148-149
(fallback help). The `delta_color="off"` is a firm lock (UI-SPEC §Color L80-85, D-02) — the
helper returns it, the app passes it to `st.metric`.

---

### `tests/test_presentation_multiticker.py` (NEW — test, transform)

**Analog (primary):** `tests/test_payout_sustentavel_multiticker.py` (read in full).
**Analog (secondary, identical scaffold):** `tests/test_growth_robusto_multiticker.py` L1-60.

This is layer (a) of the **2-layer lock** (D-08): offline golden of PROPERTIES across the
5-ticker set. Layer (b) — live manual checkpoint of VULC3 + ITUB4/EGIE3/TAEE11/BBAS3 — is
human-verified, not code (UI-SPEC §Verification Lock L197-211).

**Module-docstring pattern** (both analogs open with a docstring stating: synthetic offline
`CompanyData` calibrated to each of the 5 tickers' *spirit*, each assert locks a *property* of
the method not a market number, and the real-number confirmation is the human-verify checkpoint).
Copy this framing — see `test_payout_sustentavel_multiticker.py` L1-24 and
`test_growth_robusto_multiticker.py` L1-25.

**Offline `_cfg()` + synthetic `_mk(...)` builder** (identical in both analogs —
`test_payout_sustentavel_multiticker.py` L36-72): loads the shipped `config.yaml`
deterministically, builds a `CompanyData` with per-year consistent series. Reuse this `_mk`
shape verbatim (lucros/divs lists, `dpa_trailing` for inflated-trailing cases like EGIE3 at L109).
```python
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)
```

**Per-property assert pattern** (one `# pelo método (...)` comment per assert — see L84-86,
L98-101, L119-121). For Phase 11 the properties to lock (UI-SPEC L201-207):
- DY rec. renders as **`%`** string (e.g. asserts the formatted row value endswith `"%"` and
  equals `fmt_pct(dy_recorrente)`), NOT the raw `0.06` decimal that `fmt_num` would produce.
- "Payout (último ano)" row == `fmt_pct(c.payout(ult))` **CRU**, and is **distinct** from the
  "Payout p/ valuation" row == `fmt_pct(c.payout_valuation())` (VULC3 anchors: 124.7% cru vs
  ~43% sustentável — mirror the VULC3 spike profile at `test_payout_..._multiticker.py` L93-101).
- Header picks **recorrente** as primary; **fallback to trailing** when `dy_recorrente` is None
  (build a prejuízo-year profile so `dy_recorrente()` returns None).
- Normal tickers (ITUB4/EGIE3/TAEE11/BBAS3 spirit) do not regress.

Test imports the new module directly — `from analista.report import presentation` — **never**
`from app import ...` (D-09 explicitly rejects importing the Streamlit app).

---

### `app.py` (MODIFIED — thin caller, read-only)

**Constraint:** read-only w.r.t. the method (UI-SPEC §Read-Only L186-195). Only reads fields
already on `a.multiplos` / calls `c.payout(ult)` / `c.payout_valuation()` and formats/labels.
Becomes a thin caller delegating to `presentation.py`.

**Header m3 change (C-1/C-2, L131-136)** — current single-field read:
```python
# app.py L134 (current — reads trailing "DY")
m3.metric("Dividend Yield", fmt_pct(a.multiplos.get("DY")), help=h("dy"))
```
Replace with a call to `presentation.header_dy(a.multiplos.get("DY rec."), a.multiplos.get("DY"))`
and feed the returned dict into `st.metric(label, value, delta=..., delta_color="off", help=...)`.
`st.metric`'s `delta`/`delta_color` params already exist in the codebase pattern — confirm
delta_color="off" passes through. Keep `esc_md(...)` wrapping if any `R$`/`$` enters the string
(see L132 pattern; DY strings are `%` so esc not needed, but follow existing style).

**Tab Múltiplos change (C-3/C-4/C-5, L313-329)** — current assembly to replace with the pure
helper. Current buggy code:
```python
# app.py L315-327 (current)
st.caption("Dois payouts: o do último ano e o usado no valuation (DDM).", help=h("payout_dual"))
payout_ult = a.multiplos.get("DP (payout)")  # WRONG comment: this is payout_valuation, NOT c.payout(ult)
payout_proj = c.payout_valuation()           # stale comment "média 3a + clamp 1.0"
rows = []
for k, val in a.multiplos.items():
    if k == "DP (payout)":
        rows.append(("Payout (último ano)", fmt_pct(payout_ult)))     # BUG: shows valuation value
        rows.append(("Payout p/ valuation (média 3a)", fmt_pct(payout_proj)))
    elif k in ("ML", "ROE", "DY", "EY"):     # BUG DYR-02: omits "DY rec."
        rows.append((k, fmt_pct(val)))
    else:
        rows.append((k, fmt_num(val)))
```
Fixes (UI-SPEC §Component Inventory L127-130, §Formatting L110-117):
- `payout_ult` MUST read `c.payout(c.ultimo_ano())` CRU (the value the engine itself uses at
  `report.py` L156: `payout_ult = c.payout(ult)`), NOT `a.multiplos["DP (payout)"]`.
- Add `"DY rec."` to the `%` branch (parity with `report.py` L397).
- Relabel "Payout p/ valuation (média 3a)" → **"Payout p/ valuation (sustentável)"** (drop "(média 3a)").
- Update the stale caption (L315) and the wrong/stale comments (L317-318).
- Delegate the row assembly to `presentation.linhas_multiplos(...)`.

**Tab Crescimento relabel (C-6, L333)**: `"g histórico (CAGR lucro)"` → `"g histórico (tendência
log-linear)"` (Fase 10 made this a log-linear regression — `report.py` L73-80, `growth.crescimento_log_linear`).

---

### `src/analista/glossario.py` (MODIFIED — config/copy)

**Analog:** the existing dict entries themselves (string-valued keys consumed by `h(chave)` at L186).
Pure string edits, no logic. Stale wording to sweep (D-07, UI-SPEC L131, L158-166):
- `payout_dual` (L105-110): replace "*Payout p/ valuation (média 3a)* é a média projetada dos
  últimos 3 anos (com teto de 100%)" with the **sustentável** framing — median of the full
  historical series (no clamp), used by the DDM (Fase 9).
- `tab_crescimento` (L54-62): change the "**g histórico (CAGR)**" bullet (L56) to reflect the
  **log-linear trend** over the normalized earnings series (Fase 10).

`tests/test_glossario.py` exists — check it doesn't assert on the exact stale strings before editing.

---

## Shared Patterns

### Format sentinels (em-dash None boundary — GRAF-03)
**Source:** `app.py` L51-56 (`fmt_pct`/`fmt_num`, em-dash `"—"`)
**Apply to:** new `presentation.py` helpers (move these here) and the presentation test.
```python
def fmt_pct(x, casas=1):
    return "—" if x is None else f"{x*100:.{casas}f}%"
```
Note the parallel `report.py._pct/_num` (L357-362) use hyphen `"-"` — that's the CLI surface;
do not cross-wire. UI-SPEC L99-101 locks em-dash for the app/presentation surface.

### CRU vs sustentável field boundary (read-only invariant)
**Source:** `report.py` L155-158 (engine reads `c.payout(ult)` CRU for the armadilha detector;
`payout_valuation()` is the clamped/median sustainable value for the DDM).
**Apply to:** the payout-row helper — "último ano" = `c.payout(ult)` CRU; "p/ valuation" =
`c.payout_valuation()`. The phase only makes this distinction VISIBLE (today both rows collapse).

### CLI presentation as parity target
**Source:** `report.relatorio_markdown` `%`-branch `report.py` L396-401 (already correct).
**Apply to:** the new Streamlit presentation module — match the CLI's field-to-format routing so
Analisar (app) and the CLI report agree (Core Value: consistency across surfaces).

### 2-layer multi-ticker lock (Phases 9-10 → 11)
**Source:** `tests/test_payout_sustentavel_multiticker.py` (full) + `tests/test_growth_robusto_multiticker.py` L1-60.
**Apply to:** the new presentation golden test. Layer (a) offline property golden via synthetic
`_mk`/`_cfg`; layer (b) live human checkpoint (not code). No valuation-golden rebaseline (D-10).

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | Every Phase 11 file has a strong in-repo analog. The header-selection helper (`header_dy`) is the only piece with no exact prior shape, but its CRU-vs-sustentável selection logic mirrors `report.py` L155-158, and its output is consumed by the existing `st.metric` pattern (`app.py` L132-136). |

---

## Metadata

**Analog search scope:** `src/analista/report/`, `src/analista/core/fundamentals.py`,
`src/analista/glossario.py`, `app.py`, `tests/`
**Files scanned:** app.py (header + tab + helpers), report.py (analisar_acao, relatorio_markdown,
_pct/_num), fundamentals.py (method signatures), glossario.py, 2 Phase 9-10 golden tests
**Pattern extraction date:** 2026-06-27
