# Phase 10: Primitivas sem viés (PRIM) - Pattern Map

**Mapped:** 2026-07-15
**Files analyzed:** 8 modified sites (2 core primitives, 1 report engine site, 1 macro fetch, 2 entry points, 3 test surfaces)
**Analogs found:** 8 / 8 — every changed site has an in-repo analog to copy (this is a re-wiring phase, almost no new math)

> **Planner note:** this phase MODIFIES existing primitives. There is essentially no "new-file" work.
> Each change replicates a pattern that already exists in the codebase (`mediana_payout`,
> `_roe_through_cycle`, `_selic_historico`/`selic_ciclo_para_capm`, the `rf_local` stamping). The
> single most plan-shaping fact is in §Shared Pattern "Estimator split" — do not edit one shared
> function; the two consumers of `base_normalizada` need OPPOSITE estimators.

---

## File Classification

| Changed site | Role | Data Flow | Closest Analog | Match Quality |
|--------------|------|-----------|----------------|---------------|
| `normalizacao.py` `base_normalizada` (58-75) → Theil-Sen endpoint (PRIM-01) | core / pure primitive | transform | `media_winsorizada` (39-55) fallback-ladder in same file | exact (same shape, new estimator) |
| `fundamentals.py` `roe_valuation` (155-168) → median-of-annual-ROEs (PRIM-02) | model method | transform (aggregate) | `payout_valuation` (96-108) + `_roe_through_cycle` (report.py:184-198) | exact |
| `fundamentals.py` `serie_lucro_normalizada` (145-148) → raw series (PRIM-03) | model method | transform (pass-through) | `serie()` accessor (81-85) | exact |
| `report.py` `_intrinseco_por_motor` `"normalizado"` (253-262) → deflate then average (PRIM-04) | service / engine dispatch | transform | itself + `_selic_historico` deflation shape | role-match |
| `macro.py` `ipca_deflatores_anuais` (NEW) (PRIM-04) | ingest / fetch | request-response (BCB SGS) | `_selic_historico` (59-84) + `ipca_12m` (41-44) | exact (same API, same retry) |
| `cli.py` / `app.py` entry point — stamp IPCA deflators into `cfg`/snapshot (PRIM-04) | entry point / wiring | request-response → stamp | `cfg["capm"]["rf_local"] = macro.selic_ciclo_para_capm(...)` (cli.py:77-79) | exact |
| `backtest.py` `carregar_snapshot` — read stamped deflators (PRIM-04 tests) | test harness / loader | file-I/O | `rf_local = float(snap["rf_local"])` (backtest.py:55) | exact |
| `tests/` — new units, xfail removal, golden delete + YAML line (PRIM-01..05) | test | — | `test_mediana_payout_*` (test_normalizacao.py:88-128) | exact |

---

## Pattern Assignments

### `normalizacao.py` `base_normalizada` — Theil-Sen endpoint (PRIM-01, D-01/D-01b)

**Analog:** `media_winsorizada` (`normalizacao.py:39-55`) and the current `base_normalizada` (58-75) — copy the **exact N-ladder fallback structure** (`_limpar` → empty→None → N==1→value → short→simple → else→estimator). Only the final estimator changes.

**Current code to replace** (`normalizacao.py:66-75`):
```python
limpos = _limpar(valores)
if not limpos:
    return None
janela = limpos[-anos_media:] if anos_media else limpos
n = len(janela)
if n == 1:
    return janela[0]
if n < 5:
    return float(median(janela))
return media_winsorizada(janela, winsor)
```

**New estimator** — RESEARCH §Architecture Pattern 1 (endpoint + degeneration guard). Keep the same `_limpar`/janela/N-ladder wrapper; swap the median/winsor tail for:
```python
from scipy.stats import theilslopes  # scipy 1.17.1 already installed — no new dep
import numpy as np
# after janela/n computed:
if n == 1: return janela[0]          # D-01b (keep existing)
if n == 2: return sum(janela) / 2.0  # D-01b: 2 pts → média
slope, intercept, *_ = theilslopes(janela, np.arange(n))
endpoint = intercept + slope * (n - 1)
if endpoint <= 0:                    # GUARD: níveis degeneram negativos p/ prejuízo recente
    return float(median(janela))     # degrada p/ o comportamento antigo (never negative V)
return float(endpoint)
```
**Preserve:** the module docstring's promise "**Primitiva pura** — só numpy/statistics" holds (scipy is pure-python-callable, no engine import; `test_primitiva_e_pura_sem_import_de_fundamentals` still passes). Keep `anos_media`/`winsor` in the signature (knob-budget integrity — see §Shared Pattern "Knob budget").

**Window:** RESEARCH recommends **window=5 + guard** (Open Q1). If 3→5, it is a **congelado value change** → edit `normalizacao.anos_media` in **both** `config.yaml:57` and `calibracao.lock.yaml:194` in the same commit (BLIND-05 hook permits the pair).

**Anti-pattern (decisive):** do NOT route the cyclical engine (`anos_media=10`) through this — see §Shared Pattern.

---

### `fundamentals.py` `roe_valuation` — median of annual ROEs (PRIM-02, D-02)

**Analogs (two, combine them):**
1. `payout_valuation` (`fundamentals.py:96-108`) — the aggregation *shape* to mirror.
2. `_roe_through_cycle` (`report.py:184-198`) — **already computes the exact statistic**; delegate to the same median.

**Aggregation shape to copy** (`payout_valuation`, `fundamentals.py:107-108`):
```python
serie = [self.payout(a) for a in self.anos_ordenados()]
return norm.mediana_payout(serie)
```

**The statistic already exists** (`_roe_through_cycle`, `report.py:193-198`):
```python
serie = [c.roe(a) for a in c.anos_ordenados()]
validos = [r for r in serie if r is not None]
if len(validos) < 3:
    return None
stat = (rim_cfg or {}).get("roe_terminal_stat", "mediana")
return statistics.mean(validos) if stat == "media" else statistics.median(validos)
```

**Current `roe_valuation` to replace** (`fundamentals.py:160-168`, the cross-basis to kill):
```python
base = self.base_lucro_normalizada(anos_media, winsor)   # lucro 3a
...
pl_ini = self.patrimonio_liquido.get(ult - 1)
pl_fim = self.patrimonio_liquido.get(ult)                # ÷ PL do ÚLTIMO ano → cross-basis
return mult.roe_medio(base, pl_ini, pl_fim)
```

**New** (mirror `payout_valuation`, reuse `roe(a)`):
```python
def roe_valuation(self, anos_media: int = 3, winsor: float = 0.10):
    serie = [self.roe(a) for a in self.anos_ordenados()]   # roe(a): lucro_t ÷ PL médio(t-1,t)
    validos = [r for r in serie if r is not None]
    return float(median(validos)) if validos else None
```
**Consistency win:** after this, RIM's `roe0` (`c.roe_valuation()`, report.py:244) and `roe_terminal` (`_roe_through_cycle`, report.py:250) use the **same** statistic. Consider extracting a shared helper so they can't drift (RESEARCH §Don't-Hand-Roll). Reuse `roe(ano)` — do NOT invent a 2nd ROE semantics (Fronteira FIX-04, fundamentals.py:118-119).

**Boundary to preserve:** signature stays `roe_valuation()` callable **without args** across all 3 surfaces (Analisar + Ranking app + Ranking cli) — the established "número-síntese canônico" invariant (CONTEXT §Established Patterns).

---

### `fundamentals.py` `serie_lucro_normalizada` — raw series (PRIM-03, D-04)

**Analog:** the `serie()` accessor itself (`fundamentals.py:81-85`) — return the raw series, drop the winsor wrapper.

**Current** (`fundamentals.py:145-148`):
```python
def serie_lucro_normalizada(self, winsor: float = 0.10) -> List[float]:
    return norm.serie_winsorizada(self.serie("lucro_liquido"), winsor)
```
**New:** return `self.serie("lucro_liquido")` raw (no winsor). **Keep `norm.serie_winsorizada` the function alive** — `screening.py:253,272` still calls it (log-linear on tangible/lucro, Cap. 8 elegibilidade, out of PRIM scope, RESEARCH Open Q3). Only this valuation caller stops using it. Do NOT design the robust `g` here — that is Fase 11.

---

### `report.py` `_intrinseco_por_motor` `"normalizado"` — deflate then average (PRIM-04, D-03)

**Analog:** the `"normalizado"` branch itself (`report.py:253-262`) — feed it a **deflated** series; keep the AVERAGE estimator (`anos_media=10`), do NOT swap to Theil-Sen.

**Current** (`report.py:253-262`):
```python
if motor == "normalizado":
    cic = mot_cfg.get("ciclica", {})
    lpa_mid = mult.lpa(
        norm.base_normalizada(
            c.serie("lucro_liquido"),
            anos_media=cic.get("anos_media", 10), winsor=cic.get("winsor", 0.10),
        ),
        c.num_acoes.get(ult),
    )
    return motores.lucro_normalizado(lpa_mid, a.ke, g_estavel)
```

**New shape** (RESEARCH §Architecture Pattern 3): deflate `c.serie("lucro_liquido")` to last-year reais **before** `base_normalizada`, reading the deflators the entry point already stamped into `cfg`:
```python
anos = c.anos_ordenados()
defl = cfg["macro"]["ipca_deflatores"]      # {ano: fator p/ o último ano} — stamped, NOT fetched here
serie_real = [c.lucro_liquido[a] * defl[a] for a in anos if a in c.lucro_liquido and a in defl]
base = norm.base_normalizada(serie_real, anos_media=cic.get("anos_media", 10), winsor=cic.get("winsor", 0.10))
```
**Engine purity (FIX-03, Pitfall 4):** `analisar_acao` must stay offline/deterministic — resolve deflators at the entry point, never call `requests`/`macro` from inside the engine. This exactly mirrors how `rf_local` is handled today (see §Shared Pattern). `base_normalizada` here keeps its **median/winsorized-mean** behaviour (the cyclical wants mid-cycle power, not the endpoint). Keep `motores.ciclica.anos_media:10`/`winsor:0.10` congelados (config.yaml:266-267, lock:157-158) untouched.

---

### `macro.py` `ipca_deflatores_anuais` (NEW) — per-year IPCA deflators (PRIM-04)

**Analog:** `_selic_historico` (`macro.py:59-84`) — same BCB SGS date-range pull + 3-retry + graceful `[]`/None. And `ipca_12m` (41-44) for the fraction convention (`/100.0`).

**Copy the retry+degrade skeleton** (`macro.py:73-84`):
```python
for tentativa in range(3):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        dados = resp.json()
        if isinstance(dados, list) and dados:
            return [float(d["valor"].replace(",", ".")) / 100.0 for d in dados]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    if tentativa < 2:
        time.sleep(0.5 * (tentativa + 1))
return []
```
**New function:** fetch annual IPCA (SGS **13522 sampled at December**, or **433 monthly** accumulated per year — RESEARCH Assumption A1 / Open Q2), build `{ano: prod(1+ipca[y]) for y in (ano+1..T)}` where `T` = last year (reais do último ano, NOT a fixed base year — D-03 / §Specific Ideas). It is **objective BCB data, not a valuation knob** — no tunable, no free base-year choice (§Knob Budget). Follow the existing `SGS_URL` constant + `SELIC_META`/`IPCA_12M` code-constant convention (macro.py:15-19).

---

## Shared Patterns

### Estimator split (THE decisive structural constraint — PRIM-01 vs PRIM-04)
**Source of conflict:** `normalizacao.base_normalizada` is called by TWO consumers that need OPPOSITE estimators.
- `fundamentals.base_lucro_normalizada` (`anos_media=3`) → wants the **Theil-Sen endpoint** (reflect recent growth).
- `report.py:256` `"normalizado"` (`anos_media=10`) → wants the **through-cycle AVERAGE** (robust to a recent loss).

**Measured:** CSNA3 over 10y: through-cycle average = **+1.270M** vs Theil-Sen endpoint = **−891M**. A global swap breaks the cyclical engine.
**Apply to:** the plan must **split the estimator** — the endpoint path (3y valuation base) and the averaging path (10y cyclical). RESEARCH recommends a second named function (e.g. `media_ciclo`) for the cyclical path, or an explicit estimator flag. **Do NOT edit one shared function to Theil-Sen.**

### Offline entry-point stamping (rf_local mirror — PRIM-04, FIX-03/Pitfall 4)
**Apply to:** the IPCA deflators for PRIM-04. Resolve at entry, stamp into `cfg`, read offline in the engine — exactly like `rf_local`:

**Entry point** (`cli.py:77-79`):
```python
cfg["capm"]["rf_local"] = macro.selic_ciclo_para_capm(
    cfg["capm"]["selic_fallback"], cfg["capm"].get("rf_ciclo_anos", 10)
)
```
**Entry-point resolver, network here only** (`macro.py:87-100`, `selic_ciclo_para_capm`) — degrade gracefully spot→fallback.

**Engine reads stamped value, never the network** (`report.py:416-419`):
```python
# (cap["rf_local"]) é a Selic ao vivo do BCB, JÁ injetada pelos entry points
a.ke = capm.ke_local(c.beta, cap["rf_local"], cap["erp_local"])
```
**Test snapshot stamping** (`backtest.py:55`, `carregar_snapshot`):
```python
rf_local = float(snap["rf_local"])   # deflators go in the snapshot the same way
```
**Test injection into cfg copy** (`backtest.py:117`, pure — does not mutate caller):
```python
cfg = {**cfg, "capm": {**cfg.get("capm", {}), "rf_local": rf_local}}
```
For PRIM-04, add an analogous `cfg["macro"]["ipca_deflatores"]` stamped at cli/app and carried in the snapshot; the offline tests read it exactly like `rf_local`. Do NOT regenerate the snapshots (they hold inputs; the golden breaks from the *code*, RESEARCH §Runtime State).

### Knob budget integrity (BLIND-06 / `calibracao.lock.yaml`)
**Apply to:** every touch of a knob. `theilslopes` is **parameter-free → no 4th degree of freedom** (✅).
- **Recommended:** keep `normalizacao.anos_media:3`/`winsor:0.10` present in `config.yaml:56-58` (window for Theil-Sen; winsor inert at N<5). Then lock's `congelados` (lock:194,201) still match → `test_knobs_batem_com_o_lock` + `test_orcamento_de_knobs_e_exatamente_3` stay green, **no lock edit**.
- **If window 3→5:** congelado value change → edit `config.yaml:57` **and** `calibracao.lock.yaml:194` in the same commit.
- **One-line justification rule** (`-k justificativa` + `.githooks/commit-msg`): justify WITHOUT naming a ticker. "Removi a winsorização da série temporal porque enviesava a tendência" ✅; "para o CSNA3 sair do subvalorizado" ❌.

### Test authoring (unit primitives)
**Source/analog:** `test_mediana_payout_*` (`test_normalizacao.py:88-128`) — the template for the new PRIM-01/02/03/04 unit tests (pure-input → pure-output, no network, explicit boundary cases None/empty/single). Mirror it for: Theil-Sen endpoint + guard + short-series fallback; `roe_valuation == median(roe(a))`; raw-series (no winsor); deflated cyclical base > nominal.

---

## Tests — break/rewrite/delete map (from RESEARCH §Validation Architecture)

### Must FLIP (xfail → normal) — same commit as the `normalizacao.py` fix
- `test_invariantes_v24.py::test_normalizacao_nao_pune_crescimento` (BLIND-03) — **remove the `@pytest.mark.xfail(strict=True)` decorator** (test_invariantes_v24.py, ~line 160). `xfail_strict=true` turns a now-passing xfail into XPASS=FAIL (Pitfall 6). Stays `@pytest.mark.invariante`. NEVER swap xfail→skip, never loosen the assert.

### Must REWRITE (encode old median estimator, not a system invariant)
- `test_normalizacao.py::test_outlier_alto_suavizado_pela_mediana` (21-28) — asserts `base == 105` (median suavizes terminal outlier). Theil-Sen endpoint → chases it. **Rewrite** to the new invariant (window≥5 robustness to a single spike; RESEARCH: spike→144,7 at window=5).
- `test_normalizacao.py::test_none_ignorado_antes_de_normalizar` (42-46) — asserts `base == 105`. **Rewrite:** keep the None-skip assertion, drop the median-105 level.
- `test_normalizacao.py::test_apenas_os_ultimos_anos_media_entram_na_base` (57-60) — survives IFF the window is kept; keep window → survives, else rewrite.

### SURVIVE unchanged (verify green)
- `test_serie_estavel_base_igual_ao_valor` (63-65) — flat series → endpoint = value ✅
- `test_winsor_clampa_extremos_em_serie_longa` (31-39) — survives iff cyclical keeps the averaging estimator ✅
- `test_serie_winsorizada_*` (71-81) — survive iff `serie_winsorizada` fn kept (recommended: keep fn, stop *calling* it for the temporal series)
- all `test_mediana_payout_*` (88-128) — payout untouched ✅
- `test_primitiva_e_pura_sem_import_de_fundamentals` (134) — scipy is not a fundamentals import ✅

### Must DELETE (golden_nivel level-bands — DELETE test + its `classificacao.yaml` line, NEVER update)
Pitfall 5: an orphan YAML line breaks collection exactly like a missing entry — delete the function AND the line in the same change. No accept-list file exists; deleting both removes it from `ofensores` and `tolerados` simultaneously (BLIND-04a meta-test stays green).

| Test (delete) | classificacao.yaml line |
|---------------|-------------------------|
| `test_backtest_bancos.py::test_backtest_alvos_recalibrados` **← THE PRIM-05 exit golden (ITUB4 32,88 ±0,20)** | `classificacao.yaml:63` |
| `test_backtest_bancos.py::test_backtest_cesta_rota_por_ticker` (ITUB4 30-40) | `classificacao.yaml:61` |
| `test_backtest_bancos.py::test_backtest_gate_quorum_e_anotacao` | `classificacao.yaml:62` |
| `test_motores.py::test_rim_itub4_honesto_maior_que_ddm` (36-42) | `classificacao.yaml:332` |
| `test_motores.py::test_rim_itub4_live_alvo_32_40` | (find line) |
| `test_motores.py::test_rota_seguradora_nao_pega_banco` | (find line) |
| `test_vulc3_regressao.py::test_rim_itub4_dispatch_banda` | (find line) |

**Confirm with user (RESEARCH A3):** `test_guardrails_ddm.py::test_san01_reetiqueta_aberracao_itub4_like` (classificacao.yaml:162) and `test_arquetipo_roteamento.py::test_financeira_rim_destrava_vs_ddm_e_alimenta_veredito` (classificacao.yaml:49, tagged "Fase 10/13") — item 1 is the ONLY hard PRIM-05 requirement; 8–9 may ride to Fase 13.

**Surviving in test_backtest_bancos.py:** `test_backtest_determinismo` (invariante) + `test_backtest_rotulo_do_motor_consistente` (contrato) do NOT assert R$-levels → keep. Delete the 3 golden functions, not the whole file (unless user confirms retiring the harness — A5).

### DO NOT TOUCH (Fase 12 or guard fixtures — RESEARCH §Golden Disambiguation)
- `test_invariantes_v24.py::test_invariancia_inflacao_engine_itub4` (BLIND-02b, V 32,88→38,80 under +300bps) — goes green in **Fase 12**, not here.
- `helpers_blindagem.py:157,215` (`ALVOS = {"ITUB4": 32.88}`) — anti-pattern EXAMPLES inside the BLIND-04a detector's own fixtures; deleting them blinds the guard.
- `snapshot_bancos_2026-07-12.yaml:296 intrinseco_motor_observado: 32.88` — recorded input/observation, leave.
- Prose comments in `test_backtest_bancos.py:10,117` ("32,88 INALTERADO — o cap satura") — Fase 12 property.

---

## No Analog Found

None. Every changed site has an existing in-repo pattern to replicate.

## Exit criteria as METHOD assertions (not stale numbers — RESEARCH Pitfall 1)
The CONTEXT/ROADMAP anchors were measured on **pre-Phase-9 dirty data** and do not reproduce verbatim on the clean snapshot. Encode exits as method + re-measured targets:
- PRIM-01: BLIND-03 flips green; `base_normalizada` = Theil-Sen endpoint (not the middle-year median).
- PRIM-02: `roe_valuation == median(roe(a))`; lands ~18,0% for ITUB4 (bank snapshot exact), direction is slightly **down** from ~19,8% clean (NOT "16,1→18,0").
- PRIM-03: `serie_lucro_normalizada` returns raw; winsor no longer applied to the temporal series (record measured g-deltas, do NOT assert "36% disappears").
- PRIM-04: cyclical base deflated to last-year reais (real > nominal for an inflationary series); engine stays offline/deterministic.
- PRIM-05: `test_backtest_alvos_recalibrados` absent from repo (deleted + YAML line removed). Confirmed break: PRIM-02 alone moves ITUB4 RIM 32,88 → 31,52.

## Metadata

**Analog search scope:** `src/analista/core/` (normalizacao, fundamentals, capm, motores), `src/analista/report/report.py`, `src/analista/ingest/macro.py`, `src/analista/cli.py`, `src/analista/backtest.py`, `tests/` (test_normalizacao, test_invariantes_v24, classificacao.yaml), `config.yaml`, `calibracao.lock.yaml`
**Files scanned:** ~12
**Pattern extraction date:** 2026-07-15
</content>
</invoke>
