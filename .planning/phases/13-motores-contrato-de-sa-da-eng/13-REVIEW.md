---
phase: 13-motores-contrato-de-sa-da-eng
reviewed: 2026-07-19T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - app.py
  - src/analista/cli.py
  - src/analista/core/arquetipo.py
  - src/analista/core/comparables.py
  - src/analista/core/motores.py
  - src/analista/core/valuation.py
  - src/analista/report/report.py
  - src/analista/report/selo.py
  - scripts/spike_eng_rim_104.py
  - config.yaml
  - calibracao.lock.yaml
  - tests/test_eng_validacao.py
  - tests/test_eng_contrato.py
  - tests/test_eng_ponte_pb.py
  - tests/test_cli_rank_consistencia.py
findings:
  critical: 1
  warning: 5
  info: 2
  total: 8
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-07-19T00:00:00Z
**Depth:** standard
**Files Reviewed:** 14 (`config.yaml`/`calibracao.lock.yaml` counted as reviewed but not in the phase's diff)
**Status:** issues_found

## Summary

Reviewed the collapse of 4 valuation motors into a single RIM (`core/motores.rim`), the
`report._valor_rim`/`_derivar_insumo` dispatch, the P/B bridge (`core/valuation.py`), the
never-raise contracts, the Ranking rebaix to a raw-multiples screener, and the
`calibracao.lock.yaml` 3-knob budget.

The core valuation path is sound: `motores.rim` and `core/valuation.pb_justo/payout_terminal`
are pure, never-raise, and their guards are exercised by real tests (`test_eng_contrato.py`,
`test_eng_ponte_pb.py`, `test_eng_validacao.py` all pass, 40/40, and the full suite is green:
470 passed, 1 skipped, 18 deselected — no failures). `report._valor_rim` correctly wraps the
whole derivation in `try/except Exception: return None`, preserving never-raise even though
`_derivar_insumo`/`motores.rim` themselves don't blanket-catch. `cli.cmd_rank`'s rebaix to raw
multiples (ENG-11) is internally consistent with `app.py`'s Ranking page and with
`test_cli_rank_consistencia.py`'s Core Value assertion.

The problems found are all in the **debris of the collapse**, not in the new RIM path itself:
one committed script that will crash on first use because it wasn't updated when `arquetipo.py`
split `PAGADORA_REGULADA` in a later commit of the same phase; several patches of dead code and
stale docstrings left behind after the ensemble/regression/macro-carimbo machinery was removed;
and two narrow, pre-existing (not introduced by this phase) numerical edge cases worth a note.

## Critical Issues

### CR-01: `scripts/spike_eng_rim_104.py` crashes — references a deleted arquétipo constant

**File:** `scripts/spike_eng_rim_104.py:90`
**Issue:** `_coorte()` does `if chave == arquetipo.PAGADORA_REGULADA:` — but `arquetipo.PAGADORA_REGULADA`
no longer exists. It was committed in `ad58045` (13-01), and two commits later `4d9053e` (13-02)
split it into `arquetipo.PAGADORA_MADURA` / `arquetipo.CONCESSAO_FINITA` and removed the old
string entirely ("A string do rótulo antigo deixa de ser devolvida" — `arquetipo.py:40`). The
spike script was never updated to match. Confirmed by direct import:
```
>>> hasattr(arquetipo, "PAGADORA_REGULADA")
False
```
`_coorte()` is called for every ticker in `main()`'s loop (`for tk, c in empresas.items(): ...
coorte = _coorte(c, arquetipo.classificar(c, cfg).chave)`), so running the script raises
`AttributeError` immediately on the first non-skipped ticker — 100% failure, not a partial
degradation. This is exactly the kind of drift the "prova por execução" convention exists to
catch (memory `guardrails-devem-ser-provados-por-execucao`), but the script sits outside
`tests/` and outside any CI gate, so nothing caught it.
**Fix:** Update `_coorte` to use the current split (mirroring what `report.py`/`arquetipo.py`
already do):
```python
def _coorte(c, chave: str) -> str:
    return {
        arquetipo.FINANCEIRA: "financeira",
        arquetipo.PAGADORA_MADURA: "madura",
        arquetipo.CONCESSAO_FINITA: "concessao",
        arquetipo.CICLICA: "ciclica",
        arquetipo.CRESCIMENTO: "crescimento",
        arquetipo.HOLDING: "holding",
    }.get(chave, chave)
```
(and drop the now-obsolete `c.eh_concessionaria` branch/docstring, since the classifier already
emits `CONCESSAO_FINITA` directly post-13-02). If this spike is intentionally throwaway/frozen
and won't be re-run, delete it instead of leaving broken code checked in under `scripts/`.

## Warnings

### WR-01: `scripts/spike_eng_rim_104.py` silently reads a config path that no longer exists

**File:** `scripts/spike_eng_rim_104.py:109, 128-129`
**Issue:** `_roe0_da_politica` reads `cic = (cfg.get("motores", {}) or {}).get("ciclica", {})`
and then `cic.get("anos_media", 10)` / `cic.get("winsor", 0.10)`. The `motores.ciclica` sub-block
was deleted from `config.yaml` in this same phase (ENG-10/13-05: "os sub-blocos `ciclica`/
`crescimento` colapsaram"; the surviving knob is `motores.rim.anos_ciclica`, which `report.py`'s
`_roe0_ciclico` reads via `(cfg or {}).get("motores", {}).get("rim", {})`). Because `cic` is
always `{}` now, the spike silently falls back to the hardcoded defaults (10, 0.10) instead of
reading the production value from `motores.rim.anos_ciclica`. Today the defaults happen to match
(`anos_ciclica: 10` in `config.yaml`), so the measurement is accidentally correct — but if that
knob is ever tuned, this spike will silently diverge from the engine it claims to measure,
without raising or logging anything.
**Fix:** Point at the same config path `report.py` uses:
```python
cic = (cfg.get("motores", {}) or {}).get("rim", {})
...
anos_media=cic.get("anos_ciclica", 10),
```
(and drop the `winsor` knob read — `report._roe0_ciclico` no longer takes it from config either;
it hardcodes `winsor=0.10`, per ENG-10's note that `ciclica.winsor` was deleted as inert).

### WR-02: `app.py` — dead ensemble/divergence UI blocks reference fields removed from `AnaliseAcao`

**File:** `app.py:936-986`, `app.py:1013-1054`
**Issue:** These blocks read `a.san01_reetiquetado`, `a.divergencia_ativa`, `a.divergencia_razao`,
`a.divergencia_hipotese`, `a.contraponto_valor`, `a.arquetipo_incerto`, `a.candidatos_intrinsecos`,
`a.veredito_range`, `a.banda_do_motor` — none of these fields exist on `AnaliseAcao` anymore
(the ensemble/divergence machinery was deleted from `report.py` in `83e3825`/13-03). Every access
is gated by `getattr(a, "...", False)`, so nothing crashes — but the guards always resolve to the
default, which makes the "Por que {motor} e não DDM?" expander, the "Classificação incerta"
banner, and the `_usa_motor` manchete-leads-with-motor-value logic (`_valor_intr` at line 1039,
`_label_intr` at 1034-1037) permanently unreachable. `_usa_motor` is always `False`, so
`a.contraponto_valor` at line 1050 is never actually evaluated (short-circuited by `and`), but
that's incidental — a future refactor that flips one of the `getattr` defaults or removes a
short-circuit term would turn this into a live `AttributeError`. This matches the phase's own
SUMMARY note that this cleanup is deferred, so it's not a blocker, but ~110 lines of dead,
increasingly-stale UI logic is worth tracking rather than leaving indefinitely.
**Fix:** Delete the dead blocks (they're proven unreachable by the `getattr` defaults) or, if
kept intentionally for a future SUMMARY-tracked follow-up, add an explicit `# DEAD (13-03): ...`
marker near each block referencing the deferred-items note, so the next person doesn't have to
re-derive that these fields no longer exist.

### WR-03: `core/comparables.py` — Cap. 12 P/L-regression apparatus is now dead in production

**File:** `src/analista/core/comparables.py:81-187`
**Issue:** `RegressaoPL`, `ajustar_regressao_pl`, `PrecoAlvo`, `preco_alvo_por_regressao`, and
their supporting constants (`LIMIAR_AMOSTRA`, `LIMIAR_R2`, `LIMIAR_UPSIDE_ABSURDO`) have no
caller left in `src/` or `app.py` — confirmed by grep across both. This is a direct consequence
of `43d69b8`/13-06 rebaixing the Ranking to a raw-multiples screener (ENG-11: "a 2ª lente
ensemble×DDM ... SAÍRAM"). The phase *did* clean up the sibling dead code in the same file
(`divergencia_entre_lentes`, deleted in `4cda48e`) but left this larger, still-tested-but-
uncalled apparatus in place. It's currently reachable only from `tests/test_comparables.py`,
`tests/test_consistencia_modos.py`, `tests/test_growth_robusto_multiticker.py`.
**Fix:** Either delete the regression apparatus and its now-orphaned tests (consistent with how
`divergencia_entre_lentes` was retired in this same phase), or, if it's being kept for a planned
re-introduction, add a short module-level note explaining why dead-but-tested code is being
retained (mirrors the `deferred-items.md` pattern already used elsewhere in this phase).

### WR-04: `core/motores.py::nav_contabil` is unused and its docstring misdescribes who calls it

**File:** `src/analista/core/motores.py:18, 143-149`
**Issue:** The module docstring (line 18, rewritten in this phase) claims: "NAV contábil
(derivador de piso patrimonial) ... Não é mais motor primário — o `report` o usa como derivador
de book para a política HOLDING do RIM." But `report._derivar_insumo`'s `nav_piso` branch
(`report.py:165-167`) computes the book value directly via `lentes.vpa(...)` (already computed
earlier in the function as `base_book`) and never calls `motores.nav_contabil`. A grep across
`src/` and `app.py` confirms `nav_contabil` has zero callers. The claim in the docstring is
factually wrong about the current call graph — it describes an intended design that wasn't
wired up, or was wired up and later bypassed.
**Fix:** Either call `motores.nav_contabil` from the `nav_piso` branch in
`report._derivar_insumo` (so the docstring becomes true), or delete `nav_contabil` and correct
the module docstring to state that the HOLDING/`nav_piso` policy derives book directly via
`lentes.vpa` in `report.py`, without going through a dedicated `motores` function.

### WR-05: `cli.py` — `_carimbar_macro` docstring claims `rank` calls it; it doesn't

**File:** `src/analista/cli.py:68-70, 160-200`
**Issue:** `_carimbar_macro`'s docstring states: "WR-03: `analyze` E `rank` chamam este MESMO
carimbo — sem a fonte única, os entry points DRIFTAM no que carimbam e a MESMA ação cíclica
mostra intrínseco diferente entre os menus." But `cmd_rank` (lines 160-200) never calls
`_carimbar_macro` — only `cmd_analyze` does (line 99). This is actually *correct* current
behavior (post-ENG-11 the Ranking no longer computes Ke/CAPM/intrínseco, and
`roe_valuation()`/`lpa_valuation()` don't take `cfg` or read macro at all — confirmed in
`core/fundamentals.py`), but the docstring wasn't updated when the 13-06 rebaix removed the need.
A maintainer reading this comment in isolation would believe `rank` still shares the macro
carimbo and could "fix" a phantom drift bug, or conversely fail to add the carimbo back if a
future change to `rank` reintroduces a need for `a.ke`.
**Fix:** Update the docstring to reflect the post-13-06 reality, e.g.: "Chamado apenas por
`cmd_analyze`. `cmd_rank` não precisa mais deste carimbo desde o rebaixamento a screener por
múltiplos crus (ENG-11/13-06): `roe_valuation`/`lpa_valuation` não dependem de macro/CAPM."

## Info

### IN-01: `arquetipo.HOLDING` / the `nav_piso` policy branch is unreachable in production

**File:** `src/analista/core/arquetipo.py:46, 58, 128-194`
**Issue:** `ARQUETIPO_ANCORA_ROE[HOLDING] = "nav_piso"` and `report._derivar_insumo`'s `nav_piso`
branch both exist and are exercised only by contrived call sites — `classificar()`'s decision
tree (lines 128-194) can only ever return `FINANCEIRA`, `CONCESSAO_FINITA`, `CICLICA`,
`CRESCIMENTO`, or `PAGADORA_MADURA`; `HOLDING` is never appended to `candidatos`. This predates
Phase 13 (the module comment already labels it "participações → NAV/SOTP (stretch)") and isn't a
regression introduced here, so it's informational rather than a defect to fix in this phase —
just worth knowing that the `nav_piso` code path in `report._derivar_insumo` is currently dead
until a holding-detection rule is added to the classifier.
**Fix:** No action required for this phase; note for whichever future phase adds
holding/participações detection to `arquetipo.classificar`.

### IN-02: `motores.rim` — `n=1` explicit window uses `fade_para` instead of `roe0` for the single year

**File:** `src/analista/core/motores.py:115`
**Issue:** `frac = (t - 1) / (n - 1) if n > 1 else 1.0`. For `n > 1`, `t=1` gives `frac=0`, so
`roe_t = roe0` in year 1, fading linearly to `fade_para` by year `n` — matches the documented
intent. But when `n == 1`, the `else` branch forces `frac = 1.0`, so the single explicit year
uses `roe_t = fade_para` (the *terminal* ROE), not `roe0` (the *current* ROE) — inconsistent with
the "janela é a TRANSIÇÃO de `roe0` até um excesso sustentável" description in the function's own
docstring. This is unreachable with the current config (`motores.rim.n_fade: 10`, and `n_fade`
is one of the 3 locked degrees of freedom, so it won't drift to 1 silently), and this line was
not touched by this phase's diff — it predates the RIM-collapse work. Flagging for awareness
since the RIM is now the *only* valuation path (ENG-01), so any future recalibration of `n_fade`
toward 1 would hit this silently.
**Fix:** If ever relevant, change to `frac = 0.0 if n == 1 else (t - 1) / (n - 1)` so a
single-year window uses `roe0`, consistent with `n > 1` windows' first year.

---

_Reviewed: 2026-07-19T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
