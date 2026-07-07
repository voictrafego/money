---
phase: 17-modo-trading-candlestick-tradingview-lightweight-charts
plan: 02
subsystem: ui
tags: [streamlit, lightweight-charts, tradingview, overlays, band-primitive, price-line, series-markers, swing-trade]

# Dependency graph
requires:
  - phase: 17-modo-trading-candlestick-tradingview-lightweight-charts
    plan: 01
    provides: "_render_lwc(f, sw, sinais, est, ticker, tf_key) — candlestick nominal LWC v5 (CDN pinado + SRI), tf_key na assinatura, template JS como ponto de extensão"
provides:
  - "Overlays da engine portados p/ o Modo Trading (LWC): zona de entrada + S/R como BANDAS (BandPrimitive), stop/alvo/Fibonacci como priceLines rotuladas, pivôs/padrões como markers + neckline (LineSeries)"
  - "Paridade 1:1 de gates com o Plotly (est[sr_on|niveis_setup_on|fib_on|padroes_on]); tudo read-only de sw/sinais, degradando sem quebrar em None/vazio"
affects: [17-03-verificacao]

# Tech tracking
tech-stack:
  added: []  # ZERO dependência Python nova — só serialização JSON + JS no template components.html
  patterns:
    - "BandPrimitive: series primitive v5 reutilizável (attachPrimitive, zOrder 'bottom', priceToCoordinate + fillRect em useBitmapCoordinateSpace) = equivalente LWC do add_hrect do Plotly"
    - "Overlays serializados read-only em CFG JSON estável (chaves sempre presentes; grupos desligados vão vazios) — gate no Python, iteração no JS"
    - "Cada bloco de overlay em try/catch + console.log independente; nenhum overlay quebra o render do candle"

key-files:
  created: []
  modified:
    - "app.py — _render_lwc: serialização Python dos níveis/padrões (gateada por est[...]) + BandPrimitive/createPriceLine/createSeriesMarkers/LineSeries no template JS"

key-decisions:
  - "Overlays lidos read-only de sw/sinais e serializados em um objeto CFG (OV) de CHAVES ESTÁVEIS — grupos desligados/ausentes vão vazios; o Python filtra por est[...], o JS só itera o que chegou (degradação graciosa sem branch no template)"
  - "BandPrimitive é o helper ÚNICO e reutilizável p/ zona de entrada (azul) e S/R (verde/vermelho) — porte fiel do spike 002 (zOrder 'bottom' desenha atrás dos candles, espelhando o add_hrect)"
  - "ts de pivô convertido pelo MESMO _ts_to_time do candle (string '%Y-%m-%d' diário / epoch UTC seg intraday) decidido por tf_key — markers e neckline caem exatamente sobre as barras"
  - "Neckline = LineSeries de 2 pontos (t0/t1 dos pivôs no mesmo p.neckline), lineStyle sólido se confirmado / tracejado se em formação; guard t0!==t1 evita reta degenerada — reta inclinada da OCO fica deferida (CONTEXT)"
  - "Copy dos títulos estritamente de estudo (gate SWING-02): 'stop (estudo)', 'alvo (estudo)', 'alvo (projeção de estudo)', marker 'pivô · em formação/confirmado' — zero linguagem imperativa"

patterns-established:
  - "Porte de overlay Plotly→LWC: BANDA→BandPrimitive, hline→createPriceLine, shape/marker→createSeriesMarkers/LineSeries, sempre gateado pelo mesmo est[...] e em try/catch isolado"

requirements-completed: [LWC-02]

# Metrics
duration: ~9min
completed: 2026-07-01
---

# Phase 17 Plan 02: Overlays da Engine no Modo Trading (Lightweight Charts) Summary

**As sobreposições da engine (zona de entrada + S/R como bandas, stop/alvo/Fibonacci como linhas rotuladas, pivôs/padrões como markers + neckline) foram portadas 1:1 do Plotly para o candlestick LWC de `_render_lwc`, lendo os MESMOS campos de `SetupSwing`/`sinais` sem recalcular o método, cada bloco gateado pelo mesmo toggle `est[...]` e degradando sem quebrar quando os campos são None/vazios — copy neutra de estudo mantida.**

## Performance

- **Duration:** ~9 min
- **Tasks:** 2
- **Files modified:** 1 (app.py)

## Accomplishments
- **Task 1 — bandas + linhas:** `_render_lwc` ganhou a serialização read-only dos níveis (gateada por `est["sr_on"|"niveis_setup_on"|"fib_on"]`) e, no template JS, o helper único `BandPrimitive` (series primitive v5, `zOrder 'bottom'`, `priceToCoordinate` + `fillRect` em `useBitmapCoordinateSpace`) para a zona de entrada (azul) e as zonas de S/R (suporte verde / resistência vermelho), mais `createPriceLine` para stop (vermelho tracejado, "stop (estudo)"), alvo (verde tracejado, "alvo (estudo)"), bordas da entrada (azul pontilhado) e Fibonacci (roxo pontilhado, "Fib {nome}").
- **Task 2 — markers + neckline:** serialização read-only de `sinais.padroes.lista` (gateada por `est["padroes_on"]`) com `ts`→time convertido pelo mesmo `_ts_to_time` do candle; no JS, `createSeriesMarkers` desenha 1 marker por pivô (cor por direção: alta verde `#2ca02c` / baixa vermelho `#d62728`), a neckline vira `LineSeries` de 2 pontos (sólido se confirmado, tracejado se em formação) e o alvo do padrão vira `createPriceLine` "alvo (projeção de estudo)".
- Cada grupo de overlay roda em `try/catch` + `console.log` independente; nenhum overlay derruba o candle.
- 283 testes golden verdes; `grafico.py` intacto; zero dependência Python nova.

## Task Commits

Each task was committed atomically:

1. **Task 1: BandPrimitive + priceLines (zona/S-R como bandas; stop/alvo/Fib como linhas)** - `ae59b2d` (feat)
2. **Task 2: Markers de pivôs/padrões + neckline opcional (createSeriesMarkers)** - `ab630b6` (feat)

## Files Created/Modified
- `app.py` — dentro de `_render_lwc`: (1) helper `_ts_to_time` (diário→string / intraday→epoch por `tf_key`); (2) montagem do dict `overlays` (chaves estáveis) filtrado por `est[...]` a partir de `sinais.niveis.suportes/resistencias/fib_retracoes`, `sw.entrada_zona/stop/alvo` e `sinais.padroes.lista`; (3) no template: `BandPrimitive`/`BandPaneView`, bloco `try/catch` de bandas + `createPriceLine`, bloco `try/catch` de `createSeriesMarkers` + `LineSeries` da neckline; `createSeriesMarkers`, `LineSeries` adicionados ao destructuring de `LightweightCharts`.

## Decisions Made

- **CFG de chaves estáveis (`OV`):** o objeto de overlays é sempre serializado com todas as chaves (`suportes`, `resistencias`, `entrada`, `stop`, `alvo`, `fib`, `padroes`); grupos desligados por `est[...]` ou ausentes na engine vão vazios/None. O Python é a camada de gate; o JS só itera o que chegou. Isso mantém o template sem lógica de decisão de método (thin renderer) e garante degradação graciosa sem `if` extra no JS.
- **`BandPrimitive` como helper único:** mesmo primitive reutilizado para entrada e S/R (só muda low/high/cor), porte fiel do spike 002 — `zOrder 'bottom'` desenha atrás dos candles, espelhando o `add_hrect` do Plotly.
- **Conversão de `ts` de pivô:** reutiliza o mesmo formato de time do candle via `_ts_to_time` decidido por `tf_key` (string `"%Y-%m-%d"` diário / epoch UTC segundos intraday), garantindo que markers e neckline caiam exatamente sobre as barras. `createSeriesMarkers` exige ordem crescente → markers ordenados por `ts` no Python e re-ordenados no JS por segurança.
- **Neckline como `LineSeries` de 2 pontos:** simplificação honesta do MVP (reta horizontal em `p.neckline` entre o primeiro e o último pivô); guard `t0 !== t1` evita reta degenerada. A reta inclinada da OCO fica deferida per CONTEXT.
- **Copy de estudo:** todos os títulos/rótulos neutros ("stop (estudo)", "alvo (estudo)", "alvo (projeção de estudo)", marker "pivô · em formação/confirmado") — gate SWING-02, sem linguagem imperativa.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. `grafico.py` não foi tocado; o bloco Plotly permanece inalterado (o porte só adiciona código no ramo LWC de `_render_lwc`).

## User Setup Required

None - nenhuma configuração externa. O CDN unpkg (herdado do plano 01) é carregado em runtime no browser.

## Next Phase Readiness
- Plano **17-03** (verificação): os três primitivos-alvo estão presentes no template (`BandPrimitive`, `createPriceLine`, `createSeriesMarkers`); a base fixa `.phase-base-sha` do plano 01 cobre o diff de invariância de `grafico.py`. Falta apenas o smoke visual no navegador (bandas/linhas/markers renderizando no Modo Trading), que é o checkpoint humano do plano 03.

---
*Phase: 17-modo-trading-candlestick-tradingview-lightweight-charts*
*Completed: 2026-07-01*

## Self-Check: PASSED

- FOUND: app.py
- FOUND commit: ae59b2d (Task 1)
- FOUND commit: ab630b6 (Task 2)
- 283 pytest passed; grafico.py intacto (git diff --name-only = só app.py); gates estáticos (BandPrimitive, createPriceLine, createSeriesMarkers, "(estudo)", "projeção de estudo", padroes_on) todos OK.
