---
phase: 05-motor-de-indicadores-puro
plan: 03
subsystem: core
tags: [indicators, adx, wilder, dmi, regression, linregress, calcular, no-repaint, split, golden-tests, checkpoint]

# Dependency graph
requires:
  - phase: 05
    plan: 01
    provides: "contrato SinaisTecnicos + _wilder_rma_from + _tendencia/_momentum"
  - phase: 05
    plan: 02
    provides: "_canais (Donchian/Bollinger/squeeze)"
  - phase: 04
    provides: "prices._ajustar_por_split + fixture ITSA4 multisplit (test_ingest_ohlc)"
provides:
  - "src/analista/core/indicators.py — adx_wilder (dupla suavização de Wilder, 1º válido no índice 27)"
  - "regressao_trailing (scipy.stats.linregress, slope %/ano + R² sobre janela trailing de 90, D-04)"
  - "_forca (família Força: ADX/+DI/-DI + regressão + forca_adx por cortes 20/25)"
  - "calcular(ohlc, cfg) — entry-point único agregando as 4 famílias; guard de borda → fully-indisponivel"
  - "tests/test_indicators.py — ADX estrutural+no-repaint, regressão, calcular completo/degrada, split TEST-05"
affects: [06 (report.analisar_acao consome calcular()), 07 (overlays ADX/regressão)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ADX dupla-Wilder: 1ª suavização (+DM/-DM/TR) com start=1 (barra 0 é diff indefinido) → 1º DI no índice length; 2ª suavização do DX com start=length → 1º ADX no índice 2*length-1"
    - "Divisões do DMI protegidas com np.errstate (ATR==0 / +DI+−DI==0 → NaN, nunca inf; T-05-06)"
    - "Regressão trailing causal via scipy.stats.linregress; slope_ann = slope*252/média*100 (%/ano normalizado, D-04); r2 = rvalue²"
    - "Entry-point com guard de borda roteando frame vazio pelas funções de família (degradação single-sourced; T-05-05)"
    - "TEST-05 reusa a fixture ITSA4 multisplit de test_ingest_ohlc + contraste nominal×ajustado (teeth)"

key-files:
  created: []
  modified:
    - src/analista/core/indicators.py
    - tests/test_indicators.py

key-decisions:
  - "1ª suavização de Wilder do DMI usa start=1 (não start=0): a barra 0 é o diff indefinido (up/dn=NaN); seedar a SMA em arr[1:1+length] coloca o 1º +DI/-DI/ATR no índice length=14 — pré-requisito p/ o 1º ADX cair exatamente no índice 27"
  - "2ª suavização do DX com _wilder_rma_from(dx, length, start=length): seed no 1º DX válido (RESEARCH Pitfall 2); start=0 produziria ADX todo-NaN"
  - "forca_adx por cortes do método: <20 sem_tendencia, >25 forte, entre neutro, NaN indisponivel"
  - "calcular: frame None/vazio/sem colunas é substituído por frame vazio e roteado pelas famílias — a degradação para indisponivel mora em um lugar só (espelha o guard do ddm)"
  - "TEST-05 verifica per-barra (sem cross/perda_minima nas 5 datas de split do ITSA4 ajustado) + contraste com o nominal (que rompe de baixa nos degraus) para garantir teeth"

patterns-established:
  - "Família Força = adx_wilder + regressao_trailing montadas em _forca → Forca dataclass"
  - "Checkpoint humano de validação numérica (ADX × TradingView): structural+no-repaint travados primeiro; literais numéricos só após confirmação humana"

requirements-completed: [FORCE-01, FORCE-02, TEST-04, TEST-05]
requirements-pending: [TEST-03]

# Metrics
duration: in-progress (parado no checkpoint Task 3)
completed: 2026-06-26
---

# Phase 5 Plan 03: Força (ADX dupla-Wilder + regressão) + calcular() entry-point Summary

**Família Força travada — ADX(14) pela cadeia DMI completa com DUPLA suavização de Wilder (1º válido no índice 27, no-repaint exato) e a regressão linear trailing em %/ano + R² (scipy linregress, D-04) — e o entry-point `calcular(ohlc, cfg)` agregando as 4 famílias com degradação graciosa na borda; o split-stress ITSA4 (TEST-05) passa sem cross/breakout espúrio. PARADO no checkpoint humano TEST-03 (cruzar ADX × TradingView antes de congelar os literais).**

## Status: PAUSADO no checkpoint Task 3 (human-verify)

Tasks 1 e 2 concluídas e commitadas. Task 3 é um checkpoint humano (`type="checkpoint:human-verify"`, `autonomous: false`): a âncora numérica do ADX contra o TradingView não pode ser derivada offline (RESEARCH Assumption A1). Os valores de referência foram gerados e estão abaixo, aguardando confirmação humana antes de congelar `test_adx_wilder_referencia`.

## Performance

- **Completed (parcial):** 2026-06-26
- **Tasks:** 2 de 3 concluídas (Task 3 = checkpoint humano pendente)
- **Files modified:** 2

## Accomplishments
- `adx_wilder(ohlc, length)`: cadeia DMI completa (+DM/-DM/TR por barra) → 1ª suavização de Wilder (start=1) → +DI/-DI/ATR → DX → 2ª suavização (start=length); 1º ADX válido no índice 2*length-1 = 27; divisões protegidas com `np.errstate` (T-05-06)
- `regressao_trailing(close, win)`: regressão OLS trailing causal via `scipy.stats.linregress`; slope anualizado em %/ano normalizado pelo nível de preço + R² (D-04); 1º válido no índice win-1
- `_forca(ohlc, cfg)`: monta a família Força; `forca_adx` rotulado pelos cortes 20/25 com degradação para "indisponivel"
- `calcular(ohlc, cfg)`: entry-point único agregando Tendência/Canais/Força/Momentum; guard de borda (None/vazio/sem colunas) → SinaisTecnicos totalmente "indisponivel" sem exceção (T-05-05)
- TEST-05: o frame ITSA4 split-adjusted (5 splits) não gera cross/perda_minima espúrios nas 5 datas de evento; contraste com o nominal (que rompe de baixa nos degraus) garante teeth
- Suíte 86 → 91 (TEST-07 preservado: 64 goldens de valuation + Tendência/Momentum/Canais seguem verdes)

## Task Commits

1. **Task 1: ADX dupla-Wilder + regressão (Força)** - `0c6c0aa` (test RED) → `1d0f706` (feat GREEN)
2. **Task 2: calcular() entry-point + split TEST-05** - `6165230` (test RED) → `23d7ce3` (feat GREEN)
3. **Task 3: ADX × TradingView (TEST-03)** - PENDENTE (checkpoint humano)

## Files Created/Modified
- `src/analista/core/indicators.py` - `adx_wilder`, `regressao_trailing`, `_forca`, `calcular` (+ `_COLUNAS_OHLC`)
- `tests/test_indicators.py` - `_ohlc_adx_ref`, `test_adx_wilder_estrutural`, `test_regressao_slope_r2`, `_frame_ohlc_longo`, `test_calcular_completo`, `test_calcular_degrada`, `test_split_sem_cross_espurio`

## Checkpoint TEST-03 — valores de referência do ADX (aguardando confirmação)

Fixture canônica `_ohlc_adx_ref(n=80, seed=11)` (`np.random.default_rng(11)`):
`base = linspace(20,60,80) + N(0,1.5)`; `high = base + |N(0,0.8)| + 0.5`; `low = base − |N(0,0.8)| − 0.5`; `close = base`.

OHLC nas barras amostradas (High / Low / Close):

| idx | data | High | Low | Close |
|-----|------|------|-----|-------|
| 27 | 2020-02-07 | 33.3462 | 30.9304 | 31.8811 |
| 60 | 2020-03-25 | 51.0627 | 49.1407 | 50.0041 |
| 79 | 2020-04-21 | 61.0137 | 59.1174 | 59.8592 |

ADX(14) / +DI / -DI computados pelo app:

| idx | ADX | +DI | -DI |
|-----|-----|-----|-----|
| 27 | 33.2531 | 34.4017 | 18.8407 |
| 40 | 42.0324 | 35.9687 | 10.7024 |
| 60 | 40.2369 | 35.9882 | 17.4333 |
| 79 | 39.6431 | 38.3801 | 15.3219 |

`first valid ADX index = 27` (já asseverado automaticamente). Após a confirmação humana (ou os valores do TradingView), o executor adiciona `test_adx_wilder_referencia` congelando os literais (`np.testing.assert_allclose`, atol ~1e-2). Em caso de divergência, os literais NÃO são congelados e a discrepância é registrada aqui (o piso estrutural+no-repaint da Task 1 permanece).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 1ª suavização de Wilder do DMI precisa de start=1, não start=0**
- **Found during:** Task 1 (GREEN, ao rodar test_adx_wilder_estrutural)
- **Issue:** Com a 1ª suavização seedando em start=0, o +DI/-DI ficava válido no índice 13 (não 14), empurrando o 1º ADX para o índice 26 em vez de 27. A barra 0 é o diff indefinido (`high.diff()`/`low.diff()` = NaN), mas `np.where` transforma o NaN em 0.0 no +DM/-DM, contaminando a SMA-seed.
- **Fix:** 1ª suavização com `_wilder_rma_from(arr, length, start=1)` — a SMA-seed passa a usar `arr[1:1+length]`, colocando o 1º DI no índice length=14 e o 1º ADX no índice 27 (consistente com o RESEARCH).
- **Files modified:** src/analista/core/indicators.py
- **Commit:** 1d0f706

## Threat Model Compliance
- **T-05-05 (DoS local, calcular sobre frame None/vazio/sem colunas):** mitigado — guard no topo substitui por frame vazio e roteia pelas famílias → SinaisTecnicos totalmente "indisponivel", nunca levanta. Coberto por `test_calcular_degrada`.
- **T-05-06 (corrupção de exibição, divisão por zero no DMI/regressão):** mitigado — `np.errstate` em +DI/-DI/DX (ATR==0, +DI+−DI==0 → NaN) e guard `media != 0` na regressão; nunca propaga inf/NaN-poison.

## Issues Encountered
Nenhum além do Deviation 1 (start=1). Os valores estruturais do ADX foram verificados em runtime; a âncora numérica TradingView é o checkpoint humano pendente (Task 3).

## User Setup Required
Checkpoint humano TEST-03: cruzar os valores de ADX(14) acima com o TradingView (ou fornecer os valores do TradingView para a série canônica), e então o executor congela `test_adx_wilder_referencia`.

## Next Phase Readiness
- `calcular(ohlc, cfg)` pronto p/ a Phase 6 (`report.analisar_acao` consome o SinaisTecnicos completo)
- Pendente: confirmação humana do ADX × TradingView + congelamento de `test_adx_wilder_referencia` (TEST-03) para fechar o plano

## Self-Check: PASSED

- `src/analista/core/indicators.py` (`def adx_wilder`, `def regressao_trailing`, `def calcular`) — FOUND
- `tests/test_indicators.py` (ADX/regressão/calcular/split) — FOUND
- Commits 0c6c0aa, 1d0f706, 6165230, 23d7ce3 — FOUND
- Suíte completa: 91 passed (TEST-07 preservado)

---
*Phase: 05-motor-de-indicadores-puro*
*Status: PAUSADO no checkpoint humano Task 3 (TEST-03)*
*Completed (parcial): 2026-06-26*
