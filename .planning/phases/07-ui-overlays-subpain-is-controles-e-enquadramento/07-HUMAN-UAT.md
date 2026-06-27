---
status: partial
phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
source: [07-VERIFICATION.md]
started: "2026-06-27T00:00:00Z"
updated: "2026-06-27T00:00:00Z"
---

## Current Test

[awaiting human testing — itens 1 e 2 já aprovados no checkpoint do plano 07-05]

## Tests

### 1. Fresh-reader test (UI-06)
expected: numa tela "cara + timing bullish", um leitor novo reconhece o fundamento (veredito no topo) como decisório; bloco técnico parece consultivo/secundário.
result: passed (aprovado pelo usuário no checkpoint do 07-05 em 2026-06-27)

### 2. Renderização do gráfico make_subplots
expected: overlays no preço, subpainéis dos osciladores ativos, linhas de referência (20/25 · 30/70 · 0) e marcadores nas datas exatas exibem corretamente no Streamlit.
result: passed (verificado pelo usuário no checkpoint do 07-05)

### 3. Densidade dos marcadores Donchian (WR-02)
expected: avaliar se os marcadores de rompimento Donchian (disparam por barra durante um rompimento sustentado) têm densidade visual aceitável, ou se a correção transition-only deve ser aplicada.
result: pending

## Summary

total: 3
passed: 2
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
