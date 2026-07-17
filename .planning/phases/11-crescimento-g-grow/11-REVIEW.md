---
phase: 11-crescimento-g-grow
reviewed: 2026-07-17T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/analista/report/report.py
  - src/analista/ingest/macro.py
  - src/analista/cli.py
  - app.py
  - config.yaml
  - calibracao.lock.yaml
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-07-17
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

The central change — deriving `g_cap = (1+π_ciclo)(1+PIB_real)−1` in the engine and making it
the single source of terminal growth — is implemented correctly and consistently. The two
derivation sites (`_intrinseco_por_motor` report.py:222 and `analisar_acao` report.py:433) are
byte-identical. The old `g_estavel`/`g_terminal` knobs are fully removed (no dangling
`NameError`: every remaining `g_estavel` token is the dataclass field, the `a.g_estavel = g_cap`
label assignment, or a comment). FIX-01 (`g_alto = min(g_alto, ke)`, report.py:478-479) remains
intact and separate from the terminal cap. The DDM convergence guard (`a.ke > g_cap`,
report.py:528) degrades gracefully into the honest "Ke ≤ g_cap" alert (report.py:715-716) rather
than crashing, and with the through-the-cycle `rf` (~9.6%) `ke` stays above `g_cap` (~7.28%) in
realistic cases. The macro helper `ipca_ciclo_para_g` and the CLI/app stamping mirror the
existing `selic_ciclo_para_capm` pattern faithfully (network only at entry points; engine stays
offline/deterministic). Config/lock migration was verified out-of-scope and not re-litigated.

Two real defects remain: (1) a latent correctness bug where an unclamped `payout_valuation()`
(median, legitimately > 1) drives retention — and therefore the new RIM terminal growth `g_T` —
negative; and (2) hardcoded fallback constants that silently duplicate a locked knob and the
config default across two code sites.

## Warnings

### WR-01: Negative retention drives RIM terminal growth `g_T` negative (unclamped payout)

**File:** `src/analista/report/report.py:252-254`
**Issue:** The new per-company terminal identity computes
```python
_retencao = (1.0 - (c.payout_valuation() or 0.0))
_roe_term = _roe_through_cycle(c, rim_cfg)
_g_T = min(_roe_term * _retencao, g_cap) if _roe_term is not None else g_cap
```
`payout_valuation()` is deliberately **not** clamped to 1.0 — its own docstring
(`fundamentals.py:97-109`) states the median "pode ser legitimamente >100% ... (TAEE11 ≈ 216%)".
When the median payout exceeds 1, `_retencao` goes **negative**, so `_roe_term * _retencao` is
negative and `_g_T` becomes negative. This is then passed as `g_terminal` to `motores.rim`. The
RIM terminal is still *liberated* (with `g_T < 0`, `ke − g_T` is large and clears
`ke_g_spread_min`), and `ri_terminal = ri_terminal_base * (1 + g_terminal)` (motores.py:136)
silently shrinks the terminal for moderate negatives and — for extreme payout where `g_T < −1` —
**flips the sign** of the RI terminal, producing an economically meaningless value. The old code
passed a fixed positive `g_terminal` (0.025) here, so this is a regression introduced by the
phase. never-raise is preserved (no crash), but the number is silently wrong — the exact failure
mode the project's Core Value ("números fiéis") is meant to prevent. Reachable path: any
`rim`-motor ticker (bank; seguradora is intercepted earlier) whose median payout > 100%.
**Fix:** floor the retention used for the growth identity (and clamp `g_T` non-negative), so a
high-distribution payer yields low/zero sustainable growth instead of negative:
```python
_retencao = 1.0 - (c.payout_valuation() or 0.0)
_roe_term = _roe_through_cycle(c, rim_cfg)
_g_sust = _roe_term * max(0.0, _retencao) if _roe_term is not None else None
_g_T = min(_g_sust, g_cap) if _g_sust is not None else g_cap
_g_T = max(0.0, _g_T)  # sustainable terminal growth is never negative
```
(Keep the separate `retencao=_retencao` argument to `motores.rim` as-is if the book-growth
behavior there is intentional; only the `g_T` derivation needs the floor.)

### WR-02: Hardcoded `g_cap` fallback constants duplicate a locked knob and drift silently

**File:** `src/analista/report/report.py:222-224` and `src/analista/report/report.py:433-435`
**Issue:** Both derivation sites hardcode the fallback defaults inline:
```python
g_cap = (1.0 + cfg.get("macro", {}).get("pi_ciclo", 0.0518)) * (
    1.0 + cfg["ddm"].get("pib_real", 0.02)
) - 1.0
```
The `0.02` literal is the value of `ddm.pib_real`, which is one of the three locked degrees of
freedom (`calibracao.lock.yaml` → `PIB_real.caminho: ddm.pib_real`). Hardcoding a locked knob's
value as a fallback — in two places — means a future recalibration of `pib_real` in
config+lock would leave these fallbacks silently pointing at the old value, exactly the kind of
"two numbers that should be one" divergence the knob-discipline regime exists to prevent. The
`0.0518` (π_ciclo default) is likewise duplicated across both sites and `config.yaml:69`. The
comment asserts "fallback == default do config" but nothing enforces that invariant.
**Fix:** derive `g_cap` once in a single helper that reads the config without a magic-number
fallback (or with a single module-level constant), and call it from both sites:
```python
def _derivar_g_cap(cfg: dict) -> float:
    pi = cfg.get("macro", {}).get("pi_ciclo", cfg["ddm"].get("pib_real"))  # or a named default
    pib = cfg["ddm"].get("pib_real")
    return (1.0 + pi) * (1.0 + pib) - 1.0
```
At minimum, extract the two identical expressions into one helper so the fallbacks cannot drift
apart between the two call sites.

## Info

### IN-01: Second-level π_ciclo fallback uses `selic_fallback` (0.105), not the config default (0.0518)

**File:** `src/analista/cli.py:90` and `app.py:892-894`
**Issue:** The stamping passes
`cfg["macro"].get("pi_ciclo", cfg["capm"]["selic_fallback"])` as the offline fallback. If
`macro.pi_ciclo` were ever missing from config, this resolves to `selic_fallback` (0.105),
producing `g_cap ≈ 1.105 × 1.02 − 1 = 12.7%` — far from the intended ~7.28%. The natural default
is the config's own `pi_ciclo` (0.0518). Low probability (config ships the key), but the
second-level default is inconsistent with the value it is meant to mirror.
**Fix:** use a constant/module default that matches `config.yaml`'s `pi_ciclo` (0.0518) as the
miss value instead of `selic_fallback`.

### IN-02: `g_cap` line sits outside the `try` in `_intrinseco_por_motor` (never-raise nuance)

**File:** `src/analista/report/report.py:222-224`
**Issue:** The function's docstring promises "Never-raise: qualquer insumo degenerado/erro →
None", but the `g_cap` derivation (which does a hard `cfg["ddm"][...]` subscript via `.get` on
`cfg["ddm"]`) is placed *before* the `try:` at line 226. A malformed `cfg` missing the `ddm` key
would raise `KeyError` out of the function rather than degrading to `None`. In practice `cfg`
always contains `ddm` (and `analisar_acao` makes the same assumption at line 433, 526), so this
is consistent with the file's existing trusted-config contract and is low-risk — but if the
helper extraction from WR-02 is done, moving `g_cap` inside the guarded region (or computing it
via the shared helper) would make the never-raise contract literally true.
**Fix:** compute `g_cap` inside the `try` block (or via the WR-02 helper wrapped in the caller's
guard).

---

_Reviewed: 2026-07-17_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
