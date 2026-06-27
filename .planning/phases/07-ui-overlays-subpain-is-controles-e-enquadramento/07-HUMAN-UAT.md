---
status: complete
phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
source: [07-VERIFICATION.md]
started: "2026-06-27T00:00:00Z"
updated: "2026-06-27T00:00:00Z"
---

## Current Test

[concluído — UAT visual no app no ar (money.voictech.com.br) em 2026-06-27; itens 1–4 verificados]

## Tests

### 1. Fresh-reader test (UI-06)
expected: numa tela "cara + timing bullish", um leitor novo reconhece o fundamento (veredito no topo) como decisório; bloco técnico parece consultivo/secundário.
result: passed (aprovado pelo usuário no checkpoint do 07-05 em 2026-06-27)

### 2. Renderização do gráfico make_subplots
expected: overlays no preço, subpainéis dos osciladores ativos, linhas de referência (20/25 · 30/70 · 0) e marcadores nas datas exatas exibem corretamente no Streamlit.
result: passed (UAT visual no app no ar 2026-06-27 — SMA20/50/200 no preço, subpainel ADX dinâmico com refs 20/25, marcadores verdes/vermelhos)

### 3. Densidade dos marcadores Donchian (WR-02)
expected: avaliar se os marcadores de rompimento Donchian (disparam por barra durante um rompimento sustentado) têm densidade visual aceitável, ou se a correção transition-only deve ser aplicada.
result: resolved (correção transition-only aplicada em 1b4dd7f — um marcador por rompimento; golden trava)

### 4. UI-03 — toggle redesenha sem apagar a análise
expected: ligar/desligar um indicador técnico redesenha o gráfico no lugar, SEM des-renderizar veredito/gráfico/controles.
result: resolved (UAT visual 2026-06-27 expôs o anti-pattern do botão — a aba inteira estava gated por `if rodar and ticker:`, então o rerun do toggle apagava a análise. Fix cb56862: persistir `analise_ticker` em session_state; revalidado ao vivo — toggle redesenha overlays/subpainéis sem recoleta)

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
