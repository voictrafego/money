---
phase: 05-motor-de-indicadores-puro
plan: 02
subsystem: core
tags: [indicators, donchian, bollinger, squeeze, percentile, no-repaint, causal, golden-tests]

# Dependency graph
requires:
  - phase: 05
    plan: 01
    provides: "contrato SinaisTecnicos (dataclass Canais) + _wilder_rma_from + estilo de seção"
provides:
  - "src/analista/core/indicators.py — _canais: Donchian 20/55 causal (.shift(1)), Bollinger 20/2σ (ddof=0), squeeze percentil trailing (raw=True)"
  - "Canais estendido com donchian_sup_55/donchian_inf_55 (aditivo, default None) p/ overlay Phase 7"
  - "tests/test_indicators.py — golden Donchian no-repaint, Bollinger touch (anti-ddof=1), squeeze causal first-valid, histórico curto"
affects: [05-03 (calcular() entry-point agrega Canais), 06 (perda_minima = gatilho de reverificação), 07 (overlays de canais)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Donchian causal: high/low.rolling(n, min_periods=n).max/min().shift(1) — canal definido só pelo passado (no-repaint)"
    - "Bollinger TradingView: SMA20 +/- 2*std(ddof=0) (desvio POPULACIONAL)"
    - "Squeeze percentil trailing: largura.rolling(126).apply((x<=x[-1]).mean()*100, raw=True) — causal por construção"
    - "np.errstate + bb_med.replace(0, NaN): largura achatada vira NaN, nunca inf (mitiga T-05-03)"
    - "Extensão aditiva de dataclass travada (campos com default None) p/ não quebrar contrato anterior"

key-files:
  created: []
  modified:
    - src/analista/core/indicators.py
    - tests/test_indicators.py

key-decisions:
  - "Donchian-20 é o canal PRIMÁRIO p/ rompimento_donchian; o 55 é série de overlay (campos aditivos donchian_sup_55/inf_55)"
  - "squeeze_pct primeiro-válido no índice 144 (warmup BB 20 → largura válida em 19; + janela 126 → 19+125=144), NÃO 125: o '125' do método pressupõe uma série de largura sem NaN inicial"
  - "largura_bb protegida com np.errstate + replace(0,NaN) → squeeze lê 'indisponivel' em preço achatado em vez de propagar inf à UI (T-05-03)"
  - "Canais estendido aditivamente (default None) em vez de reescrever o contrato travado no 05-01"

patterns-established:
  - "Sinal de canal discreto: guarda NaN na ponta → 'indisponivel'; senão compara close.iloc[-1] vs canal.iloc[-1]"
  - "Teste no-repaint de canal: _canais(s[:k]).iloc[-1] == _canais(s)[k-1]"

requirements-completed: [CHAN-01, CHAN-02, CHAN-03, TEST-04]

# Metrics
duration: 12min
completed: 2026-06-26
---

# Phase 5 Plan 02: Canais (Donchian + Bollinger + squeeze percentil) Summary

**Família Canais travada — Donchian 20/55 com rompimento no-repaint via `.shift(1)`, Bollinger 20/2σ com desvio populacional (ddof=0) e toque de banda, e o squeeze percentil trailing (raw=True, causal por construção) — toda a matemática causal e congelada por golden tests, incluindo a causalidade do percentil e o no-repaint do Donchian.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-06-26
- **Tasks:** 2 (TDD RED/GREEN cada)
- **Files modified:** 2

## Accomplishments
- `_canais(ohlc, cfg)`: Donchian 20 (primário) e 55 (overlay) via `rolling(n, min_periods=n).max/min().shift(1)` — o `.shift(1)` torna o canal causal (definido só pelo passado); sem ele o rompimento nunca dispararia
- `rompimento_donchian` rotulado sobre o canal-20: `nova_maxima` / `perda_minima` / `nenhum` / `indisponivel` (`perda_minima` é o gatilho de reverificação da Phase 6)
- Bollinger 20/2σ com desvio POPULACIONAL (`std(ddof=0)`, convenção TradingView/StockCharts); `toque_bollinger` rotula `banda_superior`/`banda_inferior`/`nenhum`/`indisponivel`
- Squeeze percentil (D-02): `largura_bb = (sup-inf)/bb_med` normalizada, `squeeze_pct = rolling(126).apply((x<=x[-1]).mean()*100, raw=True)` — percentil TRAILING da largura contra a própria janela; `raw=True` é o que garante a causalidade (x[-1] = barra atual)
- `squeeze` rotulado `squeeze_on` (pct ≤ 20) / `squeeze_off` / `indisponivel`
- Golden tests: no-repaint do Donchian, Bollinger touch com cross-check ddof=0 (discriminando ddof=1), squeeze causal com first-valid verificado e sub-assert de no-repaint, degradação de histórico curto
- Suíte 82 → 86 (TEST-07 preservado: 64 goldens de valuation + Tendência/Momentum seguem verdes)

## Task Commits

1. **Task 1: Donchian 20/55 + Bollinger** - `9ca0fa9` (test RED) → `ad03dbb` (feat GREEN)
2. **Task 2: Bollinger squeeze (percentil trailing)** - `ec4b445` (test RED) → `ad7a9d6` (feat GREEN)

## Files Created/Modified
- `src/analista/core/indicators.py` - `_canais`; `Canais` estendido com `donchian_sup_55`/`donchian_inf_55` (aditivo)
- `tests/test_indicators.py` - `_frame_ohlc`, `test_donchian_breakout_causal`, `test_bollinger_touch`, `test_squeeze_percentil_causal`, `test_canais_historico_curto`

## Decisions Made
- **Donchian-20 primário, 55 como overlay:** o contrato `Canais` (travado no 05-01) só tem um par `donchian_sup/inf`; o canal-20 vira o primário (alimenta o rompimento) e o 55 é exposto via campos aditivos `donchian_sup_55`/`inf_55` (default `None`) para o plot da Phase 7, sem quebrar o contrato.
- **largura_bb com guard np.errstate + replace(0, NaN):** preço achatado (`bb_med == 0`) produziria `inf`; o guard transforma em NaN e o squeeze lê `indisponivel` (mitiga T-05-03).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] squeeze_pct first-valid é o índice 144, não 125**
- **Found during:** Task 2 (verificação em runtime antes de escrever o golden)
- **Issue:** O plan/RESEARCH afirmam "primeiro válido no índice 125 (0-based)". Isso é verdade para uma série de largura SEM NaN inicial. No pipeline real, o Bollinger (`min_periods=20`) deixa `largura_bb` NaN nos índices 0–18 (primeiro válido em 19); o `rolling(126, min_periods=126)` só junta 126 larguras válidas em `19 + 125 = 144`. Hardcodar 125 faria o teste falhar.
- **Fix:** O teste calcula `primeiro_valido = (jbb-1) + (jsq-1) = 144` a partir do config e assevera NaN antes e valor válido nele — robusto e correto (causalidade preservada). Implementação inalterada (já era causal).
- **Files modified:** tests/test_indicators.py
- **Commit:** ec4b445 (test), ad7a9d6 (feat)

**2. [Rule 2 - Missing functionality] Campos donchian_sup_55/donchian_inf_55 adicionados ao contrato**
- **Found during:** Task 1
- **Issue:** O must-have exige que "os canais Donchian 20 E 55 sejam computados", mas o `Canais` travado no 05-01 só tinha um par de séries Donchian — sem onde armazenar o 55.
- **Fix:** Estendi `Canais` com `donchian_sup_55`/`donchian_inf_55` (default `None`, aditivo) — backward-compatible, pois `calcular()` (05-03) ainda não foi montado. Ambos os canais agora são genuinamente computados e expostos.
- **Files modified:** src/analista/core/indicators.py
- **Commit:** ad03dbb

## Threat Model Compliance
- **T-05-03 (corrupção de exibição, `largura_bb` com `bb_med == 0`):** mitigado — `np.errstate(divide="ignore", invalid="ignore")` + `bb_med.replace(0.0, np.nan)`; largura achatada vira NaN, o squeeze lê `indisponivel`, nunca propaga `inf` à UI.
- **T-05-04 (DoS local, histórico < 126/55/20):** mitigado — `min_periods=janela` gera NaN; sinais discretos retornam `indisponivel` sem indexar slice vazio. Coberto por `test_canais_historico_curto` (15 bars).

## Issues Encountered
A first-valid do squeeze (144 vs 125 do método) foi pré-verificada em runtime antes de escrever o golden — ver Deviation 1.

## User Setup Required
None - módulo puro, sem serviços externos.

## Next Phase Readiness
- `_canais` pronto p/ o `calcular(ohlc, cfg)` do plan 05-03 (agregação das 4 famílias)
- Falta no plan 05-03/posterior: família Força (ADX dupla-Wilder via `_wilder_rma_from` + regressão linear) e o entry-point `calcular`
- Checkpoint de validação humana ainda pendente (STATE.md): cruzar fixture ADX com TradingView antes de travar o golden do ADX

## Self-Check: PASSED

- `src/analista/core/indicators.py` (`def _canais`) — FOUND
- `tests/test_indicators.py` (squeeze/donchian/bollinger) — FOUND
- Commits 9ca0fa9, ad03dbb, ec4b445, ad7a9d6 — FOUND
- Suíte completa: 86 passed (TEST-07 preservado)

---
*Phase: 05-motor-de-indicadores-puro*
*Completed: 2026-06-26*
