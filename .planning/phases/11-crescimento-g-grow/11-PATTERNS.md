# Phase 11: Crescimento / `g` (GROW) - Pattern Map

**Mapped:** 2026-07-16
**Files analyzed:** 7 (macro.py, cli.py, app.py, report.py, motores.py + ddm.py consumers, calibracao.lock.yaml, config.yaml, tests)
**Analogs found:** 7 / 7 (this is a within-codebase mirror phase — every new piece has an exact sibling)

> **Nature of this phase:** there is almost no greenfield here. Every new artifact is a *mirror* of
> an existing one in the same repo (the `π_ciclo` helper mirrors `selic_ciclo_para_capm`; the
> `pi_ciclo` stamp mirrors the `ipca_deflatores` stamp; the derived `g_cap` mirrors the way
> `rf_local` is read from `cfg`). The planner's job is to copy the sibling's exact shape, not invent
> structure. Line numbers below are the copy-from targets.

---

## File Classification

| File (modified unless noted) | Role | Data Flow | Closest Analog | Match Quality |
|------------------------------|------|-----------|----------------|---------------|
| `src/analista/ingest/macro.py` (NEW helper `ipca_ciclo_para_g`) | ingest/macro | request-response (network, entry-point only) | `macro.selic_ciclo_para_capm` (macro.py:160) | exact sibling |
| `src/analista/cli.py` (`_carimbar_macro`) | entry-point/stamping | transform (resolve-once → stamp cfg) | its own `rf_local`/`ipca_deflatores` stamp (cli.py:80-86) | exact (add one line) |
| `app.py` (analyze flow) | entry-point/stamping | transform (resolve-once → stamp cfg) | its own stamp block (app.py:874-882) | exact (add one line) |
| `src/analista/report/report.py` (g_cap derivation + g_alto selection) | report/engine | transform (cfg → per-company g) | in-file `g_estavel = cfg["ddm"]["g_estavel"]` reads (report.py:217, 416) | exact (in-file) |
| `src/analista/core/growth.py` (adopt `crescimento_por_fundamentos`) | core/valuation | transform (pure fn) | `crescimento_por_fundamentos` (growth.py:78) already exists — just adopt | exact (no code change to fn) |
| `src/analista/core/motores.py` / `ddm.py` (terminal `g` consumers) | core/valuation | transform (pure fn) | `motores.rim` (motores.py:65), `ddm.valor_gordon` (ddm.py:37) | exact (call-site swap) |
| `calibracao.lock.yaml` (PIB_real caminho + partition) | config/lock | declarative | grau `PIB_real` (lock:84-101) + congelados (lock:129-152) | exact (edit in place) |
| `config.yaml` (new `macro.pi_ciclo` default) | config | declarative | `capm.selic_fallback` default pattern | exact (mirror) |
| `tests/test_invariantes_v24.py` (D-07 coverage test — NEW) | test | request-response (engine call) | `test_invariancia_inflacao_engine_itub4` (test_invariantes_v24.py:111) | role-match (see notes) |
| `tests/test_blindagem_orcamento.py` (partition reflects lock edit) | test | declarative assertion | `test_orcamento_de_knobs_e_exatamente_3` (line 44), `test_knobs_batem_com_o_lock` (line 119) | exact (auto-checks lock/config) |

---

## Pattern Assignments

### `src/analista/ingest/macro.py` — NEW helper `ipca_ciclo_para_g` (D-06)

**Analog:** `macro.selic_ciclo_para_capm` (macro.py:160-173) — the arithmetic-mean-through-cycle
helper. Consumes `macro._ipca_anual_dezembro` (macro.py:109-140), the SGS-13522 series already
built in Phase 10 (PRIM-04) — **zero new network source**.

**Sibling to mirror exactly** (macro.py:160-173):
```python
def selic_ciclo_para_capm(fallback: float, anos: int = 10) -> float:
    """rf do CAPM/DDM = Selic MÉDIA dos últimos `anos` anos (through-the-cycle)."""
    hist = _selic_historico(anos)
    if hist:
        return sum(hist) / len(hist)
    return selic_para_capm(fallback)
```

**The series it consumes** — already exists, returns `{ano: ipca_fração}` (macro.py:109-140):
```python
def _ipca_anual_dezembro(anos: int = 10) -> Dict[int, float]:
    # SGS 13522 (IPCA_12M), dez de cada ano, 3 retries+backoff, {} em falha.
    # já usado por ipca_deflatores_anuais (PRIM-04)
```

**Target shape (from D-06, arithmetic mean = exact symmetry with rf `sum(hist)/len(hist)`):**
```python
def ipca_ciclo_para_g(fallback: float, anos: int = 10) -> float:
    por_ano = _ipca_anual_dezembro(anos)             # SGS 13522, reuso PRIM-04
    if por_ano:
        return sum(por_ano.values()) / len(por_ano)  # aritmética, = rf
    return fallback
```

**Purity docstring to mirror** (verbatim ethos from macro.py:151-155 / 166-168): "Chamado SÓ nos
entry points (a engine lê cfg e permanece determinística). Degradação graciosa: rede falha →
fallback." The helper must NOT be called from `analisar_acao`.

---

### `src/analista/cli.py` — stamp `pi_ciclo` (D-06)

**Analog:** `_carimbar_macro` (cli.py:66-86) — the single-source stamp for ALL CLI entry points
(both `analyze` and `rank` call it; WR-03 fixed the drift). Add one line in the SAME function.

**Copy-from site** (cli.py:80-86):
```python
def _carimbar_macro(cfg: dict) -> None:
    cfg["capm"]["rf_local"] = macro.selic_ciclo_para_capm(
        cfg["capm"]["selic_fallback"], cfg["capm"].get("rf_ciclo_anos", 10)
    )
    cfg["macro"] = {
        **cfg.get("macro", {}),
        "ipca_deflatores": macro.ipca_deflatores_anuais(cfg["capm"].get("rf_ciclo_anos", 10)),
    }
```
New `pi_ciclo` stamp follows the exact same shape — into `cfg["macro"]["pi_ciclo"]`, using the SAME
window `cfg["capm"].get("rf_ciclo_anos", 10)` (the rf↔π_ciclo window symmetry the phase formalizes),
with `cfg["macro"].get("pi_ciclo")` / a new fallback as the offline default (D-06a).

---

### `app.py` — stamp `pi_ciclo` (D-06)

**Analog:** the analyze-flow stamp block (app.py:874-882). Uses local wrappers `rf_capm` (app.py:246)
and `ipca_deflatores_capm` (app.py:254) that delegate to `macro.*`, all `@st.cache_data`d.

**Copy-from site** (app.py:874-882):
```python
CFG["capm"]["rf_local"] = rf_capm(
    CFG["capm"]["selic_fallback"], CFG["capm"].get("rf_ciclo_anos", 10)
)
CFG["macro"] = {
    **CFG.get("macro", {}),
    "ipca_deflatores": ipca_deflatores_capm(CFG["capm"].get("rf_ciclo_anos", 10)),
}
```
Add a `pi_ciclo` line + a cached `pi_ciclo_capm(...)` wrapper mirroring `ipca_deflatores_capm`
(app.py:250-254). `app.py segue read-only` (comment at app.py:873) — respect it.

---

### `src/analista/report/report.py` — derive `g_cap`, revert `g_alto` selection (D-01..D-04)

**Analog (in-file, how engine reads a cfg macro value today):** `g_estavel = cfg["ddm"]["g_estavel"]`
appears at report.py:217 (inside `_intrinseco_por_motor`) and report.py:416 (inside `analisar_acao`).
The derived `g_cap` reads `cfg["macro"]["pi_ciclo"]` + `cfg[...]["PIB_real"]` at the SAME two sites
and replaces `g_estavel` as the single terminal source (D-04).

**Read-from-cfg pattern to mirror** (report.py:416-417):
```python
g_estavel = cfg["ddm"]["g_estavel"]
a.g_estavel = g_estavel
```
Becomes a derivation `g_cap = (1 + cfg["macro"]["pi_ciclo"]) * (1 + <PIB_real>) - 1` (D-03) —
the engine derives, never types; tests stamp `pi_ciclo`, not `g_cap`.

**`g_alto` selection to REVERT (D-01)** — report.py:426-431 (the `min(g_hist, g_fund)` to remove;
the `DDM-FIX-02` comment at report.py:418 is reverted):
```python
g_alto = a.g_historico if a.g_historico is not None else a.g_fundamentos
if a.g_fundamentos is not None:
    g_alto = a.g_fundamentos if g_alto is None else min(g_alto, a.g_fundamentos)
if g_alto is not None:
    g_alto = max(0.0, min(g_alto, 0.25))  # teto absoluto 25% a.a.
a.g_alto = g_alto
```
Target (D-01): adopt `g_fundamentos`, `g_historico` becomes sanity-display + fallback only:
```python
g_alto = a.g_fundamentos if a.g_fundamentos is not None else a.g_historico
g_alto = max(0.0, min(g_alto, 0.25))   # teto absoluto inalterado
```
`a.g_fundamentos` is already computed at report.py:415 via
`growth.crescimento_por_fundamentos(c.roe_valuation(), c.payout_valuation())`.

**FIX-01 Ke cap — DO NOT TOUCH** (report.py:462-463, D-02 keeps it): `a.g_alto = min(a.g_alto, a.ke)`.
`g_cap` locks ONLY the terminal, never the explicit stage (D-02, critical for VAL-01).

**Terminal/perpetuity consumers where the single `g_cap` plugs in (D-04)** — every current
`g_estavel`/`g_terminal` call site (from grep):
- report.py:234 — `ddm.valor_gordon(dpa_sust * (1 + g_estavel), a.ke, g_estavel)` (seguradora Gordon)
- report.py:248 — `motores.rim(..., g_terminal=rim_cfg.get("g_terminal"), ...)` (RIM terminal)
- report.py:293 — `motores.lucro_normalizado(lpa_mid, a.ke, g_estavel)` (cíclica Gordon)
- report.py:295-296 — `motores.dcf_crescimento(c.lpa_valuation(), a.g_alto, g_estavel, a.ke, ...)`
- report.py:512-522 — `ddm.ddm_dois_estagios(dpa_inicial, a.g_alto, n, g_estavel, a.ke, ...)` (DDM lens)
- report.py:699 — guard `a.ke <= g_estavel`

**Report markdown labels to update (presentation, D-108/Discretion)** — report.py:960-962:
```python
L.append(f"- g alto adotado: **{_pct(a.g_alto)}**  |  g estável (perpetuidade): **{_pct(a.g_estavel)}**")
```
Relabel `g estável` 2,5% → `g_cap` (derived ~7,28%); sensitivity header at report.py:1013.

---

### `src/analista/core/growth.py` — adopt (no fn change)

**Analog = target:** `crescimento_por_fundamentos(roe, payout)` (growth.py:78-85) already implements
`ROE × (1 − payout)`. GROW-04 only makes report.py **adopt** its output instead of discarding it —
no change to the function body. `crescimento_log_linear` (growth.py:51-75, the `g_historico` source)
and `crescimento_estavel` (growth.py:88-95) are the other `g` formulas; `crescimento_estavel`'s
`teto_pib` semantics move into the derived `g_cap` clamp.

---

### `src/analista/core/motores.py` / `ddm.py` — terminal consumers (signatures stable, D-04)

**Analogs (pure primitives — signatures must NOT change, only the value passed):**
- `motores.rim(...)` (motores.py:65-76): `g_terminal: Optional[float] = None`,
  `excesso_sustentavel`, `ke_g_spread_min` — the terminal is released only if
  `g_terminal is not None AND Ke − g_terminal ≥ ke_g_spread_min` (motores.py:91-93). This is the
  exact **degrade-to-fade-only** branch the D-07 coverage test must exercise.
- `ddm.valor_gordon(dpa1, ke, g)` (ddm.py:37-46): returns None when `ke - g <= 0` (never-raise) —
  the safety the D-07 test asserts against "explode".
- `motores.lucro_normalizado(lpa, ke, g_estavel)` (motores.py:175-184) and
  `motores.dcf_crescimento(...)` (motores.py:187-218) both delegate to `ddm.valor_gordon` /
  `ddm.ddm_dois_estagios`. The single derived `g_cap` flows in as the `g_estavel`/`g_terminal` arg.

---

### `calibracao.lock.yaml` — migrate `PIB_real` caminho + repartition (D-05, SAME diff)

**Analog:** the `PIB_real` grau block (lock:84-101) literally instructs the migration:
```yaml
  PIB_real:
    caminho: ddm.g_estavel      # <-- migrate to the derived g_cap home in the SAME commit
    valor: 0.025
    # GROW-01 (Fase 11) troca isto por um `g_cap` DERIVADO ...
    # QUANDO ISSO ACONTECER, ATUALIZE O `caminho` AQUI, NO MESMO COMMIT.
```
Degree of freedom stays ONE (PIB_real); only its home/consumption changes.

**Congelados leaves affected (lock:144-152)** — these two frozen leaves LEAVE the frozen list
because their config keys are being removed/replaced (the 30-leaf partition changes):
```yaml
  motores.rim.excesso_sustentavel: 0.045   # GROW-05: stays frozen, becomes load-bearing (D-07)
  motores.rim.g_terminal: 0.025            # GROW-01: leaf removed (replaced by derived g_cap)
  motores.rim.ke_g_spread_min: 0.03        # GROW-05: stays frozen, becomes load-bearing (D-07)
```
Plus `ddm.g_estavel: 0.025` (was the `PIB_real` home). Removing `g_terminal`/`g_estavel` as frozen
leaves must keep the partition complete — see the two guardian tests below, which will go RED if the
lock and config diverge in the same diff.

---

### `config.yaml` — new `macro.pi_ciclo` default (D-06a)

**Analog:** the `capm.selic_fallback` default pattern (config.yaml, `ddm.g_estavel: 0.025` at
config.yaml:96; rim knobs at config.yaml:256/261/264). Add `macro.pi_ciclo: ~0.0518` for offline
determinism (mirrors `rf_local`'s `selic_fallback`). If a `macro:` block does not yet exist in
config.yaml it must be created — the stamp reads it as the graceful-degradation default.

---

## Shared Patterns

### Engine purity (rf/IPCA resolved once at entry points, stamped in cfg)
**Source:** `macro.py:151-155` docstring + `cli.py:66-86` + `app.py:874-882`
**Apply to:** the new `pi_ciclo` stamp and the `g_cap` derivation.
> Network lives ONLY in `_ipca_anual_dezembro` / entry points. `analisar_acao` reads the stamped
> value from `cfg` and stays offline/deterministic. Tests stamp `cfg["macro"]["pi_ciclo"]` directly.

### rf ↔ π_ciclo window symmetry
**Source:** `cli.py:81` / `app.py:875` — `cfg["capm"].get("rf_ciclo_anos", 10)`
**Apply to:** the `pi_ciclo` stamp must use the SAME `rf_ciclo_anos` window (GROW-02, lock:166-168).
This symmetry is what makes valuation invariant to inflation.

### Single source of the terminal `g` (D-04)
**Source:** the six `g_estavel`/`g_terminal` call sites in report.py (217, 234, 248, 293, 296, 512-522)
**Apply to:** one derived `g_cap` feeds both the DDM perpetuity (`ddm.valor_gordon`) and the RIM
terminal (`motores.rim(g_terminal=...)`) — eliminates the twin 2.5% constants.

### Knob-budget partition (any valuation knob touched ⇒ lock in the same diff)
**Source:** `calibracao.lock.yaml` + `tests/test_blindagem_orcamento.py`
- `test_orcamento_de_knobs_e_exatamente_3` (line 44): asserts `folhas(escopo) == graus | congelados`
  (PARTITION, not count) and `len(graus_de_liberdade) == 3`. Adding a config key without declaring it,
  or leaving a dead leaf in the lock, both go RED.
- `test_knobs_batem_com_o_lock` (line 119): every frozen leaf value must match config.yaml.
**Apply to:** the `PIB_real` caminho migration and the removed `g_terminal`/`g_estavel` leaves — the
lock edit and the config edit MUST land together or the suite goes red.

### Blindagem oracle stays xfail (do NOT chase it green in this phase)
**Source:** `test_invariancia_inflacao_engine_itub4` (test_invariantes_v24.py:103-152),
`xfail(strict=True)` at lines 104-110.
**Apply to:** this test MUST remain xfail at end of Phase 11 (it goes green in Phase 12 when `ke_teto`
leaves — motores.py:171 clamp). If it turns green here (XPASS), that is a bug — investigate. The
sibling algebraic invariant `test_invariancia_inflacao_identidade_pb_justo` (line 68) PASSES today;
the gap between them IS Doença 1. `pytest tests/arquivo.py` does NOT work in this repo — use `-k`.

---

## D-07 Coverage Test — where the NEW test lives, and its analog

**Where:** `tests/test_invariantes_v24.py` (alongside the other `@pytest.mark.invariante` engine tests)
is the natural home — it already imports `helpers_blindagem as h`, `report`, and uses the snapshot
fixture `h.cfg_e_empresas_do_snapshot()`. It must be registered in `tests/classificacao.yaml`
(collection BREAKS on an unclassified test — CLAUDE.md). NOT a golden_nivel; classify as invariante/coverage.

**Closest analog test pattern** — `test_invariancia_inflacao_engine_itub4` (test_invariantes_v24.py:135-152):
```python
empresas, cfg = h.cfg_e_empresas_do_snapshot()
...
v_base = report.analisar_acao(base, cfg).intrinseco_motor
assert v_base and v_chocado, "sem intrinseco: ..."
variacao = abs(v_chocado / v_base - 1)
assert variacao < LIMIAR_INFLACAO, "..."
```

**What D-07 must assert (from CONTEXT D-07):** exercise the RIM terminal under the tight spread
`Ke − g` ~5,5pp (both `excesso_sustentavel` and `ke_g_spread_min` binding) and assert the terminal
(a) does not explode and (b) degrades honestly to fade-only (never-raise) when
`Ke − g_terminal < ke_g_spread_min`. The exact branch is at **motores.py:91-93** (`rim`'s terminal
release condition) and **ddm.valor_gordon → None when ke - g <= 0** (ddm.py:44). "Prever, não
descobrir" — this is coverage, NOT recalibration; the two knobs stay frozen (config.yaml:256/264,
lock:144/151).

---

## No Analog Found

None. Every artifact in this phase is a within-codebase mirror of an existing sibling. The planner
should copy the sibling's exact shape (arithmetic mean, graceful fallback, entry-point stamping,
cfg read) rather than reference RESEARCH.md abstractions.

---

## Metadata

**Analog search scope:** `src/analista/ingest/macro.py`, `src/analista/cli.py`, `app.py`,
`src/analista/report/report.py`, `src/analista/core/{growth,motores,ddm}.py`,
`calibracao.lock.yaml`, `config.yaml`, `tests/test_invariantes_v24.py`,
`tests/test_blindagem_orcamento.py`.
**Files scanned:** 10
**Pattern extraction date:** 2026-07-16
