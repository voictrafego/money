---
phase: 05-motor-de-indicadores-puro
plan: 01
subsystem: core
tags: [indicators, wilder, rsi, macd, sma, ema, pandas, numpy, golden-tests]

# Dependency graph
requires:
  - phase: 04
    provides: CompanyData.ohlc_ajustado (frame OHLCV split-adjusted, colunas capitalizadas)
provides:
  - "src/analista/core/indicators.py — contrato SinaisTecnicos (4 famílias, nested) + _wilder_rma_from"
  - "Família Tendencia: SMA/EMA 20/50/200 + golden/death cross + posição×MM200 (sobre SMA, D-03)"
  - "Família Momentum: RSI(14) Wilder (âncora 70.5328) + MACD 12/26/9 (EMA padrão) + cruzamento"
  - "config.yaml seção indicadores: com parâmetros canônicos"
  - "tests/test_indicators.py — golden RSI Wilder, golden cross SMA, MACD cross, no-repaint, histórico curto"
affects: [05-02 (Canais/Forca), 05-03 (calcular() entry-point), 06 (report.analisar_acao), 07 (UI overlays)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Módulo puro espelhando ddm.py: from __future__ import annotations, dataclasses não-frozen por família"
    - "Suavização de Wilder hand-rolled (_wilder_rma_from): seed por SMA dos primeiros length, recursão alpha=1/length"
    - "Sinais discretos em chaves estáveis/neutras (sem linguagem natural PT — D-01)"
    - "Degradação graciosa: min_periods=janela → NaN; sinais → 'indisponivel' (DATA-03)"
    - "Golden tests offline com fixtures literais (dataset canônico de Wilder) + no-repaint harness"

key-files:
  created:
    - src/analista/core/indicators.py
    - tests/test_indicators.py
  modified:
    - config.yaml

key-decisions:
  - "SinaisTecnicos nested por família (Tendencia/Canais/Forca/Momentum); cada família = séries + sinais discretos (D-01)"
  - "Cross e posição×MM200 derivados SEMPRE de SMA, nunca EMA (D-03); ambas as séries computadas em toda chamada"
  - "RSI Wilder SMA-seeded via _wilder_rma_from — bate 70.5328 (EMA ingênua daria 50.75)"
  - "MACD usa EMA padrão (ewm adjust=False), NÃO Wilder (anti-pattern do RESEARCH)"
  - "RS protegida contra divisão por zero com np.errstate: só ganhos → RSI 100, só perdas → RSI 0"

patterns-established:
  - "Família de indicador = função privada _familia(close/ohlc, cfg) pura retornando dataclass"
  - "Detecção de cross via mudança de sinal de diff.dropna() nas duas últimas barras (guard <2 → indisponivel)"

requirements-completed: [TREND-01, TREND-02, TREND-03, TREND-04, MOM-01, MOM-02, TEST-03, TEST-04]

# Metrics
duration: 18min
completed: 2026-06-26
---

# Phase 5 Plan 01: Motor de indicadores puro (contrato + Tendência + Momentum) Summary

**Módulo puro `indicators.py` com contrato `SinaisTecnicos` nested por família, RSI Wilder travado na âncora 70.5328, MACD 12/26/9 e cross/posição de tendência derivados de SMA — tudo coberto por golden tests offline (no-repaint inclusos).**

## Performance

- **Duration:** ~18 min
- **Completed:** 2026-06-26
- **Tasks:** 3
- **Files modified:** 3 (2 criados, 1 modificado)

## Accomplishments
- Contrato `SinaisTecnicos` agrupado por família (Tendencia/Canais/Forca/Momentum), não-frozen, espelhando o house style de `ddm.py` (D-01)
- Helper genuinamente novo `_wilder_rma_from` (RMA de Wilder seedada por SMA) — único hand-roll, reutilizável pela 2ª suavização do ADX no plan 05-02
- Família Tendência: SMA/EMA 20/50/200 sempre computadas; golden/death cross e posição×MM200 derivados SEMPRE de SMA (D-03)
- Família Momentum: RSI(14) Wilder batendo a âncora pública 70.5328 (+5 seguintes), MACD 12/26/9 em EMA padrão com cruzamento de sinal rotulado
- Golden tests: âncora canônica de Wilder, golden cross sobre SMA (com discriminação anti-EMA), MACD cross, no-repaint RSI/MACD, degradação de histórico curto
- 64+ golden tests de valuation preexistentes seguem verdes (TEST-07): suíte 77 → 82

## Task Commits

1. **Task 1: Config section + module contract + Wilder helper** - `f4a91b1` (feat)
2. **Task 2: Tendencia family** - `d31a0aa` (test RED) → `098f7de` (feat GREEN)
3. **Task 3: Momentum family (RSI Wilder + MACD)** - `0b05a4c` (test RED) → `ea970fd` (feat GREEN)

## Files Created/Modified
- `src/analista/core/indicators.py` - Contrato SinaisTecnicos (4 dataclasses por família + raiz), `_wilder_rma_from`, `_tendencia`, `rsi_wilder`, `_momentum`
- `tests/test_indicators.py` - Golden RSI Wilder (70.5328), golden cross SMA, MACD cross, no-repaint, histórico curto
- `config.yaml` - Nova seção `indicadores:` com parâmetros canônicos (sma_emas, donchian, bollinger, squeeze, adx, rsi, macd, regressao)

## Decisions Made
- Sinais discretos como `str` literals em chaves estáveis/neutras (discrição do Claude per CONTEXT; testável por golden)
- Cross detectado por mudança de sinal de `(sma50 - sma200).dropna()` nas duas últimas barras; guard `<2 válidos → indisponivel` evita IndexError (mitiga T-05-01)
- `rsi_wilder` protege RS com `np.errstate` e normaliza casos só-ganhos/só-perdas (mitiga T-05-02)
- Canais e Força NÃO implementados aqui (stubs desnecessários): `calcular()` é montado no plan 05-03 após todas as funções de família existirem

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. A âncora 70.5328 foi pré-verificada em runtime sobre o dataset canônico de Wilder (4 casas decimais) antes de escrever o golden, garantindo `abs=1e-3`.

## Threat Model Compliance
- **T-05-01 (DoS local, histórico curto):** mitigado — `min_periods=janela` gera NaN; guards de sinal retornam "indisponivel" em vez de indexar `iloc[-2]` com <2 válidos. Coberto por `test_historico_curto_tendencia`.
- **T-05-02 (corrupção de exibição, divisão por zero no RS):** mitigado — `rs = avg_gain/avg_loss` sob `np.errstate`; só-ganhos → RSI 100, só-perdas → RSI 0, neutro 50; nunca propaga inf.

## User Setup Required
None - módulo puro, sem serviços externos.

## Next Phase Readiness
- Contrato `SinaisTecnicos` e `_wilder_rma_from` prontos para o plan 05-02 (Canais/Forca: Donchian, Bollinger, squeeze percentil, ADX dupla-Wilder, regressão linear)
- Entry-point `calcular(ohlc, cfg)` será montado no plan 05-03 agregando as 4 famílias
- Checkpoint de validação humana pendente (STATE.md): cruzar fixture ADX com TradingView antes de travar o golden do ADX (plan 05-02)

## Self-Check: PASSED

- `src/analista/core/indicators.py` — FOUND
- `tests/test_indicators.py` — FOUND
- `config.yaml` indicadores: section — FOUND
- Commits f4a91b1, d31a0aa, 098f7de, 0b05a4c, ea970fd — FOUND
- Suíte completa: 82 passed (TEST-07 preservado)

---
*Phase: 05-motor-de-indicadores-puro*
*Completed: 2026-06-26*
