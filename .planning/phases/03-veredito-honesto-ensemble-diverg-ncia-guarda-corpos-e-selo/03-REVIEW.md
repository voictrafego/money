---
phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo
reviewed: 2026-07-12T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - app.py
  - config.yaml
  - src/analista/report/report.py
  - tests/test_arquetipo_roteamento.py
  - tests/test_guardrails_ddm.py
  - tests/test_report.py
  - tests/test_vulc3_regressao.py
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-07-12
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Reviewed the Phase 03 "veredito honesto" surface: the ensemble band + divergence
banner (ENS-01), the SAN-01 anti-aberration reetiqueta (SAN-01), the VER-02
borderline range verdict (VER-02) in `report.py`, plus the Streamlit render surface
in `app.py`. The firewall (`selo.py` must not import `report.py`) is **respected** —
`selo.py` imports only `dataclasses`/`typing`; "report" appears only in docstrings.
Never-raise/degradation handling is generally solid and the golden suite is thorough.

However, the review surfaced defects that bear directly on this project's Core Value
("os números precisam ser fiéis ao método e consistentes entre si"). The most serious
is a **misleading source attribution**: when a non-DDM motor degrades but the DDM band
survives, the verdict and the "Intrínseco (<motor>)" metric are produced entirely from
the DDM while being labeled with the motor's name, with no disclaimer. Two further
WARNINGs concern numbers that can contradict each other on the same screen (VER-02
metric vs. banner) and a SAN-01 reetiqueta whose premise is broken by the VER-01
ensemble (so its "DDM conservador demais" message can be misleading).

## Critical Issues

### CR-01: Motor degrades but DDM band survives → verdict/metric are DDM-derived yet labeled as the motor (no disclaimer)

**File:** `src/analista/report/report.py:495-503` (and `520-570`); `app.py:982-988`; `src/analista/report/report.py:880-889`

**Issue:** In `analisar_acao`, the ensemble block only overrides the band and sets the
"lente conservadora" alert **when `a.intrinseco_motor is not None`**:

```python
if a.motor != "ddm" and a.intrinseco_motor is not None:
    ...  # ensemble band, banda_do_motor=True, divergence, alert at 548
# no else
```

`motores.rim()`/`ke_rim()` (and the other motors) legitimately return `None` under
degenerate inputs (`motores.py:80,110`). When the motor returns `None` **but the DDM
band `vmin/vmax` is valid**, control falls into the normal price-verdict branch at
line 520, which produces `SUBAVALIADA/NO INTERVALO/SOBREAVALIADA` **from the DDM band
alone** for a non-DDM archetype. Because `banda_do_motor` stays `False`:
- the "DDM é lente conservadora" alert (line 548) is **not** emitted;
- the motor-degradation alert (line 567) is **not** emitted either — it lives in the
  `elif a.motor != "ddm":` branch, which requires `vmin/vmax is None`.

So there is **zero indication** the motor failed. Downstream:
- `app.py:982-988` labels the metric `f"Intrínseco ({a.motor_rotulo or _motor})"` →
  e.g. "Intrínseco (RIM — VPA + VP...)" while the displayed band is 100% the DDM.
- `report.py:880-889` still prints the DDM section as `"_(lente conservadora — não é o
  motor deste arquétipo)_"`, calling the DDM a "lente" even though it is the *only*
  and *primary* valuation being shown.

This directly violates the Core Value: a DDM number is presented under the motor's
name with no explanation. The `test_ver01_motor_sem_banda_degrada_para_verificar`
golden only covers motor `None` **and** DDM `None`; the motor-None/DDM-survives path is
untested.

**Fix:** Add an explicit branch for "non-DDM motor degraded but a DDM band exists" so
the surface is honest. For example, after the ensemble `if`:

```python
elif a.motor != "ddm" and a.vmin is not None and a.vmax is not None:
    # motor degradou mas o DDM sobreviveu: a banda é do DDM, não do motor.
    a.banda_do_motor = False
    a.alertas.append(
        f"Motor '{a.motor}' ({a.motor_rotulo or a.motor}) degradou; a faixa exibida "
        "vem do DDM (contraponto), não do motor do arquétipo."
    )
```

and make the metric label / markdown fall back to "Intrínseco (DDM)" whenever
`a.banda_do_motor is False`, instead of keying purely off `a.motor`.

## Warnings

### WR-01: VER-02 borderline case — the "Intrínseco (<motor>)" metric contradicts the uncertainty banner

**File:** `app.py:976-988` vs `app.py:912-939`; `src/analista/report/report.py:267-305`

**Issue:** For a fronteiriço, `_veredito_fronteirico` overwrites `a.veredito` with the
`VERIFICAR — classificação incerta ... range R$ x–y` string and populates
`candidatos_intrinsecos`/`veredito_range`, **but never touches `vmin/vmax`** — those
stay as the *primary* archetype's ensemble band from VER-01. In the render, the m2
metric (`app.py:976`) unconditionally shows `f"{fmt_rs(vmin)} – {fmt_rs(vmax)}"` under
the label "Intrínseco (<primary motor>)". So the same stock, on the same screen, shows:
- a **candidatos range** in the "Classificação incerta" banner, and
- a **different primary-motor band** in the metric.

Worst case: the 0-candidate branch (`report.py:296-305`) sets the verdict to
"nenhum motor candidato estimou preço-alvo confiável", yet the m2 metric still proudly
displays a healthy band — the metric flatly contradicts the verdict.

**Fix:** In the fronteiriço path, suppress/replace the m2 band when `arquetipo_incerto`
is set (mirror the selo suppression). E.g. gate the metric:

```python
if getattr(a, "arquetipo_incerto", False):
    intervalo = "—"  # a classificação é incerta; a faixa vive no banner de candidatos
```

or render the `veredito_range` there instead of the primary band.

### WR-02: SAN-01 reetiqueta premise is broken by the VER-01 ensemble — can mislabel a genuine overvaluation

**File:** `src/analista/report/report.py:107-180` (`_guarda_san01`), interaction with `495-503`

**Issue:** SAN-01 fires only when `a.veredito.startswith("SOBREAVALIADA")` and the
quality/payout gate passes (ROE > roe_min, corte_payout > corte_payout_min; pares
neutral in the funil). But after VER-01 the band is `max(intrinseco_motor,
contraponto)`, so `SOBREAVALIADA` means **preço > max(motor, DDM)** — i.e. the price is
above *both* lenses, including the archetype's own motor. In that situation the
reetiqueta text "DDM conservador demais para este perfil — ver motor primário do
arquétipo (intrínseco ≈ R$ X)" is misleading: the motor's own intrínseco `X` is *also*
below the price (that's why it was SOBREAVALIADA in the first place). The gate never
checks that the motor actually disagrees with the DDM directionally, so a genuinely
overvalued high-ROE name gets its "Evitar" quadrant suppressed and is re-framed as
"the DDM is being too harsh" even when the motor agrees it is expensive. The e2e
golden `test_san01_e2e_itub4_nao_estampa_evitar` (preço 70, VPA 5.18 → RIM ≈ single
digits) locks in exactly this behavior.

**Fix:** Add a directional guard so SAN-01 only reetiquets when the motor genuinely
supports a materially higher valuation than the DDM/price — e.g. require
`a.intrinseco_motor is not None and a.intrinseco_motor >= a.preco_atual` (or
`>= contraponto * k`) before reetiquetando. Otherwise keep the SOBREAVALIADA verdict
(the number honestly says expensive) rather than asserting the DDM is too conservative.

### WR-03: "Intrínseco (<motor>)" band silently blends motor + DDM contraponto; representation differs from the CLI

**File:** `app.py:976-988` vs `src/analista/report/report.py:880-884`

**Issue:** The ensemble band `[min(motor, contraponto), max(motor, contraponto)]` is
labeled solely by the motor ("Intrínseco (RIM)"), so one bound is actually the DDM
contraponto. On **non-divergent** cases (ratio < 2×) no divergence banner is emitted
(`app.py:944`), so nothing tells the user that a bound of the "RIM" band is really the
DDM. Meanwhile `relatorio_markdown` (`report.py:882-883`) shows the motor intrínseco as
a **single point** ("RIM: R$ 28.00"), not a band. Same stock, two surfaces (app metric
vs. CLI markdown), two different representations of "intrínseco" — the exact
cross-surface inconsistency the Core Value warns against.

**Fix:** Either label the app metric honestly as an ensemble ("Intervalo motor × DDM")
or, when not divergent, add a one-line caption noting the band spans the motor and the
DDM contraponto. Align the CLI markdown to present the same band representation.

## Info

### IN-01: Fronteiriço "entre X e Y" names first/last candidate by list order, not range endpoints

**File:** `src/analista/report/report.py:274-278`

**Issue:** `primeiro, ultimo = pares[0][0], pares[-1][0]` names the first and last
candidatos in *insertion order*, while `menor, maior = min/max(valores)` are the actual
range endpoints. With ≥3 resolved candidatos the pair named in "classificação incerta
entre {primeiro} e {ultimo}" may not be the archetypes holding the min/max, so the
prose can name a narrower pair than the range implies.

**Fix:** Derive the named pair from the archetypes at the min/max values, or state the
range without implying the two named archetypes are its endpoints.

### IN-02: Redundant local `import json` shadows the module-level import

**File:** `app.py:696` and `app.py:713` (vs top-level `import json` at `app.py:9`)

**Issue:** `_seed_watchlist` and `_persistir_watchlist` each do a local `import json`
that shadows the already-imported top-level `json`. Harmless but dead/duplicated.

**Fix:** Remove the two local `import json` lines and use the module-level import.

---

_Reviewed: 2026-07-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
