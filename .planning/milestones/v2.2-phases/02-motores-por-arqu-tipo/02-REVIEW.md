---
phase: 02-motores-por-arqu-tipo
reviewed: 2026-07-11T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - src/analista/core/motores.py
  - src/analista/core/arquetipo.py
  - src/analista/report/report.py
  - src/analista/cli.py
  - config.yaml
  - tests/test_motores.py
  - tests/test_arquetipo_roteamento.py
  - tests/test_ranking_freio.py
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-07-11
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the 5 valuation engines in `core/motores.py` (RIM, lucro normalizado, DCF de
crescimento, NAV), their wiring into `arquetipo.ARQUETIPO_MOTOR` and the `report.analisar_acao`
funnel, and the D-06 suspension migration (`motor is None` → `motor != "ddm"`) across
`report.py` and `cli.py`. The full suite (406 tests) passes.

The never-raise contract is essentially sound: every motor either guards its own inputs
(`rim`) or delegates to a primitive that guards None/zero (`lucro_normalizado`→`valor_gordon`,
`dcf_crescimento`→`ddm_dois_estagios`, `nav_contabil`→`lentes.vpa`/`_safe_div`). I could not
find a division-by-zero or unguarded-None crash path. The D-06 predicate migration is
consistent across the three enforcement surfaces (`report.py:281`, `cli.py:56`,
`alvo_regressao_confiavel`).

The material defect is a **consistency regression against the project's Core Value**: the new
motor-intrinsic path exhibits negative/degenerate values as the "referência primária" with no
guard, even though the codebase already has an explicit guard (`_guarda_faixa_ddm`) built to
suppress exactly this on the DDM path. Secondary issues: a now-stale `motor_pendente` field
carrying obsolete semantics, an invariant violation in `ke_rim` on the low-beta edge, and
non-defensive config access in the motor dispatch.

## Critical Issues

### CR-01: Motor intrinsic path exhibits negative/degenerate values as primary reference (no guard parity with DDM)

**File:** `src/analista/report/report.py:198-226, 291-292, 583-585`
**Issue:** The DDM path has an explicit guard-corpo (`_guarda_faixa_ddm`, report.py:65-93) that
suppresses a negative or degenerate intrinsic range because "essa faixa NÃO é preço-alvo, é
ruído que o usuário lê como intrínseco." The new motor dispatch reproduces that exact defect on
a different code path with **no equivalent guard**: `intrinseco_motor` is emitted verbatim as
"referência primária" in the veredito (line 291-292) and in the render (line 583-585) whenever
it is `not None`, including negative values. Confirmed empirically:

```
motores.nav_contabil(-5000.0, 1000.0)              -> -5.0     # negative equity holding
motores.lucro_normalizado(-2.0, ke=0.12, g=0.025)  -> -21.05   # deep-cycle trough earnings
```

A holding with negative book equity (NAV) or a cyclical whose winsorized mid-cycle earnings are
negative will render `intrínseco ≈ R$ -21,05 (...)` as the primary valuation reference — a
demonstrably wrong user-facing number that violates the Core Value ("números fiéis ao método e
consistentes entre si"). The DDM path guards this class of input; the motor path must too.

**Fix:** Add a guard on `intrinseco_motor` before it is stored/exhibited (mirror
`_guarda_faixa_ddm`): treat non-positive results as degraded and surface a honest note instead
of a negative "intrínseco". For example, in the dispatch block:

```python
if a.intrinseco_motor is not None and a.intrinseco_motor <= 0:
    a.alertas.append(
        f"Motor '{a.motor}' devolveu valor não-positivo (PL/lucro normalizado negativo): "
        "não é preço-alvo — não exibido como intrínseco."
    )
    a.intrinseco_motor = None
```

This makes the veredito fall into the `ref = f"motor '{a.motor}' ..."` branch (no negative R$)
and suppresses the "Valuation pelo motor do arquétipo" render line, matching DDM behavior.

## Warnings

### WR-01: `motor_pendente` field left with obsolete semantics after the D-06 migration

**File:** `src/analista/report/report.py:190` (field declared at :57)
**Issue:** The whole point of D-06 was to migrate the suspension predicate off
`motor is None`. Every other surface moved to `motor != "ddm"` (report.py:281, cli.py:56), but
`a.motor_pendente = motor is None` was left behind with its old definition. Because the registry
now maps all 5 arquetipo keys to a non-None motor, `a.motor_pendente` is now **always `False`**
for any known arquetipo — a financeira (`motor == "rim"`, veredito suspended) reports
`motor_pendente=False`. The field's docstring ("True quando o motor do arquétipo chega só na
Fase 2") is factually wrong post-plug. It is dead within the repo (only asserted `False` in
tests; `app.py` doesn't read it), but as a public field of the `AnaliseAcao` dataclass it is a
latent trap: any consumer that reads `motor_pendente` to decide suspension will now silently
fail to suspend financeira/ciclica/crescimento/holding.
**Fix:** Either remove the field, or realign it with the migrated predicate so it can't drift:

```python
a.motor_pendente = a.motor != "ddm"   # D-06: parity with the suspension predicate
```

### WR-02: `ke_rim` can exceed `ke_live`, violating its documented invariant

**File:** `src/analista/core/motores.py:116`
**Issue:** The docstring guarantees the RIM Ke "nunca excede o Ke ao vivo (`ke_live`)" (D-01).
`return max(ke_piso, min(ke, ke_teto, ke_live))` breaks that guarantee when `ke_live < ke_piso`:
the outer `max` floors the result to `ke_piso`, overriding the `ke_live` cap. Confirmed:

```
ke_rim(beta=0.0)  -> 0.11   while ke_live = rf_local = 0.105   # ke_rim > ke_live
```

Realistically the financeira hard-route means a bank (beta ~0.8-1.3, `ke_live` ~0.15-0.18), so
this edge requires an implausibly low beta and won't bite in production — hence Warning, not
Blocker. But the invariant is stated as absolute and is falsifiable.
**Fix:** Apply the `ke_live` cap after the floor, so it always wins:

```python
ke_clamp = max(rim_cfg["ke_piso"], min(ke, rim_cfg["ke_teto"]))
return min(ke_clamp, ke_live)
```

### WR-03: Motor dispatch uses non-defensive `cfg["motores"][...]` indexing

**File:** `src/analista/report/report.py:200-224`, `src/analista/core/motores.py:111-116`
**Issue:** `classificar` reads config defensively (`(cfg or {}).get("arquetipo", {})` with
per-key defaults), but the motor dispatch hard-indexes `cfg["motores"]["rim"]["n_fade"]`,
`cfg["motores"]["ciclica"]`, `cfg["motores"]["crescimento"]["n_anos_explicito"]`, and `ke_rim`
hard-indexes `cfg["capm"]` / `cfg["motores"]["rim"]`. If an older `config.yaml` (without the new
`motores:` block) is loaded and a company routes to a non-ddm motor, this raises `KeyError`,
breaking the never-raise philosophy at the config boundary — and it raises inside
`analisar_acao`, which the rank command calls per-company. The shipped config has the block, so
risk is contained to stale/custom configs.
**Fix:** Read the motor knobs through `.get` with the same defaults documented in `config.yaml`
(e.g. `cfg.get("motores", {}).get("rim", {}).get("n_fade", 10)`), or validate the block once at
the entry point.

## Info

### IN-01: Inconsistent setor matching — word-boundary for financeiro, substring for regulada exclusion

**File:** `src/analista/core/arquetipo.py:157` vs `:107-121`
**Issue:** `_setor_casa_token` deliberately upgraded financeiro matching to word-boundary regex
to prevent over-match ("banco" ⊄ "Bancoreal"). The anti-Petróleo exclusion guard still uses raw
substring matching: `not any(tok.lower() in setor for tok in regulada_excluir)`. It works for
the current tokens ("petróleo"/"petroleo"), but the two matching strategies are inconsistent and
the exclusion path is the more dangerous one to get wrong (a false exclusion mis-routes a
regulada).
**Fix:** Route the exclusion through `_setor_casa_token(setor, regulada_excluir)` for a single,
consistent matching strategy.

### IN-02: `dcf_crescimento` does not cap `g_alto <= ke` internally

**File:** `src/analista/core/motores.py:145-156`
**Issue:** The report caller pre-caps `a.g_alto` to `ke` (report.py:176-177), so the pipeline is
safe, but the motor itself accepts `g_alto > ke`. With `decrescente=False` (constant model) and
`g_alto > ke`, the explicit stage inflates rather than converges (the same artifact
`ddm.matriz_sensibilidade` guards per-cell at ddm.py:139). The engine is documented as a pure,
independently-callable primitive; a direct caller could get a silently inflated value. The
default `decrescente=True` (modelo-H) mitigates this.
**Fix:** Clamp defensively inside the motor: `g_alto = min(g_alto, ke)` when `ke is not None`,
matching the DDM sensitivity-matrix guard.

---

_Reviewed: 2026-07-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
