---
phase: 01-engine-de-consist-ncia
plan: 02
subsystem: engine/comparables (Ranking por regressão P/L)
tags: [consistencia, valuation, payout, clamp, RANK-02]
requires:
  - report.payout_valuation (clamp 1.0 canônico do Analisar, plano 01-01) como referência de tratamento
provides:
  - comparables.preco_alvo_por_regressao com clamp de payout em [0,1] antes da previsão
  - PrecoAlvo.payout_fora_faixa (flag para UI/Fase 2 exibir alerta equivalente ao do Analisar)
affects:
  - Preço-alvo do Ranking (parte b de CR-03 / RANK-02)
tech-stack:
  added: []
  patterns:
    - Clamp na PREVISÃO do alvo (não no ajuste da regressão) — mesma regra do Analisar antes do DDM
key-files:
  created: []
  modified:
    - src/analista/core/comparables.py
    - tests/test_comparables.py
decisions:
  - Clamp aplicado só no ponto de previsão (preco_alvo_por_regressao), espelhando report.py; ajustar_regressao_pl permanece intacto pois usa os pares do setor como observações
  - payout_fora_faixa derivado de (dp_clamp != dp) — cobre teto >1.0 e piso <0.0 numa única flag
metrics:
  duration: 4 min
  completed: 2026-06-05
---

# Phase 01 Plan 02: Clamp de payout fora de faixa no Ranking Summary

Clamp/sinalização de payout fora de [0,1] em `preco_alvo_por_regressao`, igualando o tratamento que o Analisar já aplica antes do DDM — payout >100% ou negativo não puxa mais o P/L esperado e o preço-alvo para valores sem sentido.

## What Was Built

- **Clamp na previsão (RANK-02 / CR-03 parte b):** antes de `reg.prever(dp, roe)`, o payout `dp` é clampado em `[0,1]` (`min(max(dp,0.0),1.0)`). O P/L esperado e o preço-alvo passam a usar o `dp` clampado, espelhando `report.py` (`payout_proj = min(media_3a, 1.0)`).
- **Sinalização:** novo campo `PrecoAlvo.payout_fora_faixa: bool = False`, `True` quando o `dp` original estava fora da faixa. Permite à UI/Fase 2 exibir o alerta equivalente ao ">100%" do Analisar, em vez de o ajuste sumir silenciosamente.
- **Escopo preservado:** `ajustar_regressao_pl` (OLS sobre os pares do setor) **não** foi alterado — o clamp é só no ponto da previsão do alvo, exatamente como o Analisar clampa só antes do DDM. Nenhuma fórmula de valuation foi reescrita.

## How It Works

`preco_alvo_por_regressao` mantém o guard de `None`/`lpa<=0`. Em seguida:
- `dp_clamp = min(max(dp, 0.0), 1.0)` (teto 1.0 para payout >100%; piso 0.0 para payout negativo de LPA<0, sem exceção).
- `payout_fora_faixa = dp_clamp != dp`.
- `pl_esperado = reg.prever(dp_clamp, roe)`; demais cálculos (preço-alvo, upside, subavaliada) inalterados.

## Verification

- Smoke test inline do plano: payout 1.5 produz o mesmo preço-alvo que 1.0 e `payout_fora_faixa is True`; payout 1.0 → `False`. Saída `ok`.
- `pytest tests/ -q`: **41 passed** (38 golden originais + 3 novos casos). Golden tests (test_ddm, test_multiples, test_comparables, test_screening) seguem verdes.

## TDD Gate Compliance

- RED: `test(01-02)` commit `c679417` — 3 testes falhos (clamp ausente + `AttributeError` em `payout_fora_faixa`).
- GREEN: `feat(01-02)` commit `e9908ec` — implementação mínima; todos os testes passam.
- REFACTOR: não necessário (implementação já mínima e clara).

## Deviations from Plan

None - plan executed exactly as written.

## Commits

- `c679417` test(01-02): teste falho p/ clamp+flag de payout fora de [0,1] (RED)
- `e9908ec` feat(01-02): clamp+flag de payout fora de [0,1] na regressão (GREEN)

## Self-Check: PASSED

- FOUND: .planning/phases/01-engine-de-consist-ncia/01-02-SUMMARY.md
- FOUND: commit c679417 (RED)
- FOUND: commit e9908ec (GREEN)
