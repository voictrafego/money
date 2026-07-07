---
phase: 13-piv-s-contexto-de-tend-ncia-e-n-veis
plan: 03
subsystem: engine
tags: [niveis, suporte-resistencia, cluster, atr, donchian, volume, ohlc-nominal, no-repaint, indicators]

# Dependency graph
requires:
  - phase: 13-piv-s-contexto-de-tend-ncia-e-n-veis
    provides: "Pivos + _pivos (pivot_high/pivot_low confirmados) e atr_wilder/Forca.atr (plano 01)"
  - phase: 12-ingest-o-intraday-timeframe
    provides: "FrameOHLC (ohlc nominal + ohlc_ajustado) — D-02 herdado"
provides:
  - "Niveis dataclass (suportes/resistencias como zonas (low,high) + donchian_externo_inf/sup) + campo aditivo SinaisTecnicos.niveis"
  - "_niveis_sr: clustering single-linkage de pivôs por gap < cluster_k×ATR; banda mínima garante low<high (nunca ponto, D-10)"
  - "Volume dataclass (volume_mm + rompimento_com_volume) + campo aditivo SinaisTecnicos.volume; _volume com flag na barra fechada (D-04)"
  - "Param OPCIONAL ohlc_nominal em calcular: rota famílias de PREÇO (pivôs+níveis) pelo frame nominal (D-02), aditivo"
affects: [13-04-stop-rr, 14-padroes, 15-score, 16-overlays]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "S/R como FAIXAS (low,high), nunca pontos: clustering por proximidade < k×ATR com banda mínima (_SR_BANDA_MIN_FRAC×limiar) — D-10"
    - "Família de PREÇO roteada pelo frame nominal via param opcional ohlc_nominal em calcular (D-02), indicadores seguem no split-adjusted"
    - "Flag de volume avaliada na barra FECHADA (iloc[-2]) + Donchian causal .shift(1) — sem repaint da barra viva (D-04/D-11)"

key-files:
  created: []
  modified:
    - src/analista/core/indicators.py
    - config.yaml
    - tests/test_indicators.py

key-decisions:
  - "Clustering single-linkage (gap vs vizinho anterior < k×ATR); cada zona alargada para largura mínima 0.5×k×ATR → toda zona é banda (low<high), nunca ponto (D-10)"
  - "Classificação suporte/resistência pelo CENTRO da zona vs close da barra fechada (iloc[-2], D-04); ordenadas por proximidade ao preço"
  - "ohlc_nominal guardado por colunas OHLC; quando ausente/inválido cai no próprio ohlc → chamadas existentes idênticas (aditivo puro)"
  - "Volume usa o frame ohlc (split-adjusted) recebido; sem coluna Volume → Volume() default antes de qualquer cálculo (T-13-07)"

patterns-established:
  - "Constante de heurística documentada no módulo (_SR_BANDA_MIN_FRAC) quando não há param de config dedicado"
  - "Param opcional aditivo no entry-point (ohlc_nominal) com guard de colunas, espelhando o guard de borda de calcular"

requirements-completed: [LEVEL-01, VOL-01]

# Metrics
duration: ~9min
completed: 2026-06-29
---

# Phase 13 Plan 03: Zonas de S/R (cluster k×ATR) + Donchian externo + Família Volume Summary

**A engine agora deriva Suporte/Resistência como ZONAS (faixas (low,high) por clustering de pivôs com largura k×ATR, nunca pontos — D-10) com Donchian 20/55 como faixa externa, e a família Volume (MM + flag de rompimento confirmado na barra fechada); o param opcional `ohlc_nominal` honra D-02 roteando as famílias de PREÇO pelo frame nominal — tudo aditivo a `SinaisTecnicos`, com os 225 goldens anteriores intactos.**

## Performance

- **Duration:** ~9 min
- **Tasks:** 2/2
- **Files modified:** 3 (indicators.py, config.yaml, tests/test_indicators.py)
- **Tests:** 225 baseline → 238 (13 novos goldens), 100% verde

## Accomplishments
- `Niveis` dataclass (`suportes`/`resistencias` como `list[(low,high)]` + `donchian_externo_inf`/`sup`) + campo aditivo `SinaisTecnicos.niveis` (default None). `_niveis_sr` faz clustering single-linkage dos pivôs confirmados por gap < `cluster_k`×ATR, alarga cada zona para a largura mínima `0.5×k×ATR` (toda zona é faixa `low<high`, nunca ponto — D-10), classifica vs o close da barra FECHADA (`iloc[-2]`, D-04) em suportes (abaixo) e resistências (acima) ordenadas por proximidade, e expõe a ponta de `donchian_*_55` como faixa externa.
- Param OPCIONAL `ohlc_nominal` em `calcular`: rota as famílias de PREÇO (pivôs + níveis) pelo frame NOMINAL quando fornecido (D-02), mantendo indicadores/contexto no split-adjusted. Guard por colunas OHLC; ausência → usa o próprio `ohlc` (chamadas/goldens existentes idênticos).
- `Volume` dataclass (`volume_mm` + `rompimento_com_volume`) + campo aditivo `SinaisTecnicos.volume`. `_volume`: MM de volume com `min_periods==volume_janela`; flag True só quando o close da barra fechada rompe a Donchian superior causal (`.shift(1)`) E o volume fechado > MM. Degrada para `Volume()` sem coluna `Volume` (191 goldens fundamentalistas e técnicos sem Volume seguem verdes).
- `config.yaml`: `cluster_k: 1.0` e `volume_janela: 20` no bloco `indicadores` (com o "porquê").

## Task Commits

1. **Task 1: Zonas S/R (cluster k×ATR) + Donchian externo + ohlc_nominal (RED)** - `451dd31` (test)
2. **Task 1 (GREEN)** - `25f9fc6` (feat)
3. **Task 2: Família Volume (RED)** - `493f0ef` (test)
4. **Task 2 (GREEN)** - `d32d1af` (feat)

_TDD: cada task seguiu RED (test) → GREEN (feat); nenhum refactor necessário._

## Files Created/Modified
- `src/analista/core/indicators.py` - dataclasses `Niveis` e `Volume`; campos aditivos `SinaisTecnicos.niveis`/`volume`; constante `_SR_BANDA_MIN_FRAC`; helpers `_clusterizar_pivos`/`_zona_banda`; funções `_niveis_sr` e `_volume`; param opcional `ohlc_nominal` em `calcular` com roteamento de PREÇO por nominal (D-02).
- `config.yaml` - bloco `indicadores`: `cluster_k: 1.0` e `volume_janela: 20`.
- `tests/test_indicators.py` - 13 novos goldens: S/R (cluster funde/separa zonas, faixa low<high, suporte/resistência vs close fechado, Donchian externo, ohlc_nominal aditivo, degradação); Volume (rompimento com/sem volume, sem coluna, frame curto, min_periods, calcular popula/degrada).

## Decisions Made
- **Banda mínima garante "nunca ponto":** o clustering por gap pode produzir um cluster de 1 pivô (que seria um ponto). `_zona_banda` alarga toda zona degenerada para `0.5×k×ATR` simétrico — assim a invariante D-10 (S/R são faixas, nunca pontos) vale para QUALQUER cluster, não só os fundidos. Constante documentada no módulo (sem novo param de config — discrição do plano).
- **Classificação pelo CENTRO da zona:** suporte/resistência decidido por `(low+high)/2 ≤ ref` vs `ref = close.iloc[-2]` (barra fechada). Robusto quando a banda mínima faz a faixa cruzar levemente o preço; ordenação por proximidade ao close.
- **ATR de volatilidade no scale do split-adjusted:** `_niveis_sr` recebe `forca.atr` (cadeia do ADX sobre `ohlc`) como insumo de largura; os PREÇOS vêm do `nominal`. Sem split nas barras recentes os dois coincidem; o roteamento por nominal move os preços das zonas (D-02), provado em golden.

## Deviations from Plan
None - plano executado exatamente como escrito. (A dataclass `Volume`, escopo da Task 2, foi adicionada junto da `Niveis` no commit GREEN da Task 1 por proximidade física no arquivo; a função `_volume`, a montagem em `calcular` e o param de config ficaram inteiramente na Task 2 — gate TDD da Task 2 preservado: os testes RED falharam por `AttributeError`/`KeyError` antes do GREEN.)

## Issues Encountered
None.

## TDD Gate Compliance
- Task 1: RED `451dd31` (test) → GREEN `25f9fc6` (feat). OK.
- Task 2: RED `493f0ef` (test) → GREEN `d32d1af` (feat). OK.
- Nenhum teste passou inesperadamente na fase RED (falharam por `AttributeError`/`KeyError`/`niveis`/`volume` None antes da implementação).

## Verification
- `.venv/bin/python -m pytest tests/ -q` → **238 passed** (baseline 225 + 13 novos; nenhum golden existente alterado, 191 fundamentalistas intactos).
- Zonas S/R são faixas `(low,high)` com `low<high` (nunca pontos); cluster funde pivôs próximos e separa distantes.
- `ohlc_nominal` aditivo: pivôs/zonas de preço mudam com o nominal, ATR (indicador) inalterado (D-02).
- Volume: flag True só com rompimento + volume acima da MM na barra fechada; degrada sem coluna Volume.

## Known Stubs
None — `Niveis` (S/R + Donchian externo) e `Volume` estão totalmente populados via `calcular`. Os campos restantes de níveis geométricos (zona de entrada/Fibonacci, stop técnico, alvo, R:R — LEVEL-02/03/04, RR-01) são o plano 04 da Fase 13 (escopo declarado, não stubs); o consumo de níveis/volume pelos overlays e score são as Fases 15/16.

## Self-Check: PASSED
