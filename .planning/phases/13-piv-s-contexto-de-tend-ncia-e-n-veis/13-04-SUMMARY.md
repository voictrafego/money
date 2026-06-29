---
phase: 13-piv-s-contexto-de-tend-ncia-e-n-veis
plan: 04
subsystem: engine
tags: [fibonacci, retracao, extensao, stop, atr, risco-retorno, niveis, no-repaint, indicators]

# Dependency graph
requires:
  - phase: 13-piv-s-contexto-de-tend-ncia-e-n-veis
    provides: "Pivos (pivot_high/pivot_low confirmados) + ContextoTendencia.dow_diario (planos 01/02) e Niveis + Forca.atr/atr_wilder (planos 01/03)"
  - phase: 12-ingest-o-intraday-timeframe
    provides: "FrameOHLC (ohlc nominal) — D-02 herdado: níveis de PREÇO sobre o nominal"
provides:
  - "Niveis estendido (aditivo): entrada_zona/fib_retracoes/alvo (Fibonacci ancorado), pivos_ancora (auditável), stop (mais conservador) e risco_retorno (formatado/degradável)"
  - "_niveis_fib(niveis, pivos, contexto, ohlc_nominal, cfg): retração de entrada 38,2/50/61,8% + extensão de alvo 161,8% ancoradas no último impulso confirmado (D-07)"
  - "_niveis_stop_rr(niveis, contexto, atr, ohlc_nominal, cfg): stop = mais distante entre swing estrutural e ATR×m (D-08); R:R '1 : x,y' com degradação para 'indisponivel' (D-09)"
affects: [14-padroes, 15-score, 16-overlays]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fibonacci ancorado em PAR de pivôs CONFIRMADOS (no-repaint por construção) coerente com dow_diario; âncora documentada para auditabilidade (D-07)"
    - "Stop 'mais conservador' = o mais DISTANTE da entrada entre swing e ATR×m (min em alta / max em baixa) — ATR reusado, nunca recalculado (D-08)"
    - "Razão R:R protegida com np.divide sob np.errstate → risco<=0/NaN/inf vira string 'indisponivel', NUNCA infinito (D-09)"

key-files:
  created: []
  modified:
    - src/analista/core/indicators.py
    - tests/test_indicators.py

key-decisions:
  - "Âncora coerente com a tendência: alta → último topo + último fundo ANTES dele (fundo→topo); baixa → último fundo + último topo antes dele (topo→fundo)"
  - "entrada_zona sempre (low,high): alta=(61,8%,38,2%) descendo do topo; baixa=(38,2%,61,8%) subindo do fundo; range = topo−fundo (guard range<=0 → não ancora)"
  - "entrada_ref = ponto médio da entrada_zona; stop em alta=min(swing,entrada_ref−m·ATR), baixa=max(swing,entrada_ref+m·ATR); m=stop_atr_m (1,5)"
  - "R:R formatado com vírgula decimal BR 1 casa via f-string + replace; np.divide(retorno,risco) sob errstate evita ZeroDivisionError do float Python"

patterns-established:
  - "Funções de níveis que MUTAM o objeto Niveis já construído (merge aditivo no fluxo de calcular), testáveis em isolamento com Niveis()/ContextoTendencia() sintéticos"

requirements-completed: [LEVEL-02, LEVEL-03, LEVEL-04, RR-01]

# Metrics
duration: ~11min
completed: 2026-06-29
---

# Phase 13 Plan 04: Fibonacci ancorado (entrada+alvo) + stop conservador + R:R Summary

**A engine fecha os níveis geométricos da Fase 13: zona de entrada por retração de Fibonacci (38,2/50/61,8%) e alvo por extensão 161,8% ancorados no último impulso CONFIRMADO (par de pivôs documentado, no-repaint — D-07), stop técnico = o mais conservador entre swing estrutural e ATR×m (D-08), e a relação Risco:Retorno formatada "1 : 2,5" que degrada para "indisponivel" sem jamais propagar infinito (D-09) — tudo aditivo a `SinaisTecnicos`, com os 238 goldens anteriores intactos.**

## Performance

- **Duration:** ~11 min
- **Tasks:** 2/2
- **Files modified:** 2 (indicators.py, tests/test_indicators.py)
- **Tests:** 238 baseline → 251 (13 novos goldens), 100% verde

## Accomplishments
- `Niveis` estendido de forma 100% aditiva: `entrada_zona` (faixa 61,8↔38,2%), `fib_retracoes` (3 níveis nomeados), `alvo` (extensão 161,8%), `pivos_ancora` (os dois pivôs com timestamps+preços — auditabilidade D-07), `stop` (Number) e `risco_retorno` (str, default `"indisponivel"`).
- `_niveis_fib`: seleciona o par de pivôs mais recente coerente com `contexto.dow_diario` — em "alta" o último topo confirmado e o último fundo confirmado ANTES dele (impulso fundo→topo); em "baixa" o último fundo e o último topo antes dele (topo→fundo). Calcula retração de entrada e extensão de alvo sobre `(topo−fundo)`. Como ambos os pivôs são CONFIRMADOS (imutáveis — gate do plano 01), os níveis NUNCA repaint (mitiga T-13-10). Degrada para `None` em `lateral`/`indisponivel`/sem par/range≤0 (mitiga T-13-11).
- `_niveis_stop_rr`: stop = o mais DISTANTE da entrada entre o swing estrutural (fundo âncora em alta, topo âncora em baixa) e ATR×m — `min` em alta, `max` em baixa (D-08); `entrada_ref` = ponto médio da `entrada_zona`; ATR REUSADO de `atr_wilder` (último valor válido), nunca recalculado. R:R = `"1 : {retorno/risco}"` com vírgula decimal BR (1 casa); `np.divide` sob `np.errstate` → `risco<=0`/NaN/inf ou sem entrada/alvo/âncora → `"indisponivel"`, NUNCA infinito (mitiga T-13-09).
- Ambas as funções MUTAM o `Niveis` já montado por `_niveis_sr` dentro de `calcular` (merge aditivo no fluxo), com `contexto` extraído para variável antes da montagem do `SinaisTecnicos`.

## Task Commits

1. **Task 1: Fibonacci ancorado (RED)** - `1f859b0` (test)
2. **Task 1: Fibonacci ancorado (GREEN)** - `6889b39` (feat)
3. **Task 2: Stop conservador + R:R (RED)** - `f9b9d7b` (test)
4. **Task 2: Stop conservador + R:R (GREEN)** - `5ec51dd` (feat)

_TDD: cada task seguiu RED (test) → GREEN (feat); nenhum refactor necessário._

## Files Created/Modified
- `src/analista/core/indicators.py` - campos aditivos em `Niveis` (entrada_zona/fib_retracoes/alvo/pivos_ancora/stop/risco_retorno); constantes `_FIB_RETRACOES`/`_FIB_EXTENSAO`; funções `_niveis_fib` e `_niveis_stop_rr`; merge das duas dentro de `calcular` (após `_niveis_sr`), com `contexto`/`niveis` extraídos para variáveis.
- `tests/test_indicators.py` - 13 novos goldens: Fibonacci alta (fundo→topo), baixa (espelhado), degradação lateral, sem par confirmado, calcular popula+âncora auditável; stop swing-mais-distante vs ATR×m-mais-distante, stop baixa (max), R:R "1 : 2,5", risco==0 → indisponivel (sem inf), lateral degrada (stop None), calcular popula stop/RR, guard de errstate no R:R.

## Decisions Made
- **entrada_zona sempre como faixa `(low, high)`:** em alta `(topo−R·0.618, topo−R·0.382)` (61,8% é o nível mais fundo); em baixa `(fundo+R·0.382, fundo+R·0.618)`. Mantém a invariante `low<high` para qualquer direção, espelhando a convenção das zonas de S/R do plano 03.
- **`np.divide` sob `errstate` em vez de divisão de float Python:** divisão de `float` Python por zero levanta `ZeroDivisionError` (o `np.errstate` só captura ops numpy). `np.divide(retorno, risco)` retorna `inf` sob `errstate`, depois filtrado por `np.isfinite` → `"indisponivel"`. É o que torna o guard de div-zero efetivo (D-09).
- **Preços nominais sem nova rota:** `pivos` já é computado sobre o frame NOMINAL em `calcular` (D-02 do plano 03), logo os preços de pivô usados pelo Fibonacci já são nominais — sem necessidade de reler `ohlc_nominal` (parâmetro mantido na assinatura para coerência e uso futuro).

## Deviations from Plan
None - plano executado exatamente como escrito. (As dataclasses receberam os campos da Task 2 — `stop`/`risco_retorno` — apenas na fase GREEN da Task 2; o gate RED da Task 2 falhou por `AttributeError` em `_niveis_stop_rr` antes da implementação.)

## Issues Encountered
None.

## TDD Gate Compliance
- Task 1: RED `1f859b0` (test) → GREEN `6889b39` (feat). OK.
- Task 2: RED `f9b9d7b` (test) → GREEN `5ec51dd` (feat). OK.
- Nenhum teste passou inesperadamente na fase RED (falharam por `AttributeError` em `entrada_zona`/`_niveis_fib`/`_niveis_stop_rr` antes da implementação).

## Verification
- `.venv/bin/python -m pytest tests/ -q` → **251 passed** (baseline 238 + 13 novos; nenhum golden existente alterado, 191 fundamentalistas intactos).
- Fibonacci ancorado em par de pivôs CONFIRMADOS (no-repaint), com âncora documentada (`pivos_ancora` traz ts+preço dos dois pivôs).
- Stop = mais conservador provado nos dois lados (swing mais distante → stop==swing; ATR×m mais distante → stop==atr_stop).
- R:R "1 : 2,5" formatado; `risco==0`/lateral → `"indisponivel"`; `np.isinf` nunca aparece; `errstate` cobre o cálculo da razão.

## Known Stubs
None — `Niveis` agora está completo (S/R + Donchian externo + entrada/stop/alvo Fibonacci + R:R). O consumo desses níveis pelo score (R:R como gate) é a Fase 15 e a renderização/overlays é a Fase 16 (escopo declarado, não stubs). "Exibe, nunca recomenda" continua sendo gate das Fases 15/16 — aqui são apenas níveis numéricos neutros.

## Self-Check: PASSED
- `src/analista/core/indicators.py` contém `def _niveis_fib` e `def _niveis_stop_rr`, e `Niveis` tem `entrada_zona`/`alvo`/`stop`/`risco_retorno` (FOUND).
- `tests/test_indicators.py` contém goldens de `fib` e `stop_rr` (FOUND).
- Commits `1f859b0`, `6889b39`, `f9b9d7b`, `5ec51dd` presentes no log (FOUND).
- Suíte 251 verde (FOUND).
