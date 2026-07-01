---
spike: 001
name: tv-feel-candlestick
type: standard
validates: "Given candles diários da BBSE3 num app Streamlit, when renderizados via TradingView Lightweight Charts v5 (components.html + CDN), then o usuário sente a UX do TV — scroll=zoom, pan, crosshair com rótulos nos eixos, Y auto-reescala, linha de último preço"
verdict: VALIDATED
related: [002]
tags: [ux, charting, lightweight-charts, streamlit, tradingview]
---

# Spike 001: tv-feel-candlestick

## O que valida
**Given** candles diários da BBSE3 num app Streamlit, **when** renderizados via TradingView
Lightweight Charts v5 embutido com `st.components.v1.html` + CDN (unpkg), **then** o usuário
sente a UX do TradingView: scroll = zoom, arrastar = pan, crosshair com rótulos nos eixos,
**Y reescala sozinho** na janela visível, e linha de último preço — tudo sem backend e sem
dependência Python nova.

## Research
- **Lib:** TradingView Lightweight Charts — **v5.2.0** (abr/2026), Apache-2.0, ~45KB, open-source.
- **API v5 (mudou vs v4):** `LightweightCharts.createChart(el, opts)` → `chart.addSeries(LightweightCharts.CandlestickSeries, {...})` (v4 era `chart.addCandlestickSeries`). `HistogramSeries` p/ volume. Crosshair via `CrosshairMode.Normal`. Último preço nativo (`priceLineVisible`/`lastValueVisible`, default true). Y-autoscale nativo (`rightPriceScale.autoScale`, default true).
- **Standalone global:** `https://unpkg.com/lightweight-charts@5.2.0/dist/lightweight-charts.standalone.production.js` expõe `window.LightweightCharts`.

| Abordagem | Prós | Contras | Status |
|-----------|------|---------|--------|
| **components.html + CDN** (escolhida) | zero dependência nova, API completa, controle total, alinha ao ethos custo-zero | iframe sandbox: sem callbacks p/ Python; rerun do Streamlit re-renderiza (perde zoom) | ✅ usada |
| pip `streamlit-lightweight-charts` | declarativo (config dict) | wrapper community, risco de defasar vs Streamlit 1.58 / lib v5 | não usada |

**Chosen approach:** components.html + CDN — decidido no checkpoint de alinhamento.

## How to Run
```bash
.venv/bin/streamlit run .planning/spikes/001-tv-feel-candlestick/spike_app.py \
  --server.port 8599 --server.headless true
# abrir http://localhost:8599
```
Dados: yfinance `BBSE3.SA` 1y diário (fallback sintético determinístico se yfinance falhar).

## What to Expect
Candlestick dark estilo TV + volume no rodapé, linha tracejada de último preço com etiqueta
no eixo. Scroll = zoom no tempo; arrastar = pan; cursor mostra crosshair com preço/data nos
eixos; ao dar zoom, o eixo Y reenquadra sozinho.

## Investigation Trail
1. **Happy path:** subiu de primeira. yfinance retornou 250 barras; última = **2026-06-30 @ R$ 39,17** — bate exatamente com a validação anterior contra o TradingView. Visual praticamente idêntico ao TV (candles, volume, logo TV embutido).
2. **Crosshair:** confirmado com rótulos nos DOIS eixos (screenshots: preço `37.75` / data `27 jan '26`; após zoom `38.97` / `20 mar '26`). É o comportamento nativo do `CrosshairMode.Normal` — zero código extra.
3. **Último preço:** linha tracejada + etiqueta `39.17` no eixo direito, nativa (o Plotly precisa de `add_hline` manual).
4. **Y-autoscale:** `rightPriceScale.autoScale` é default → o eixo Y reenquadra na janela visível ao dar zoom. É exatamente o recurso que o Plotly não entrega dentro do `st.plotly_chart`.
5. **Edge/limitações observadas:**
   - **Rerun do Streamlit re-renderiza o iframe → perde o estado de zoom/pan.** Mitigável guardando o range visível em `st.session_state` e re-aplicando via `timeScale().setVisibleRange()`, ou (melhor) minimizando reruns nessa aba.
   - **components.html é sandbox unidirecional:** dá pra enviar dados Python→JS, mas não ler zoom/click de volta sem um componente custom bidirecional. Para exibição pura (nosso caso) não é problema.
   - Fonte de dados: yfinance ajusta histórico por proventos; para bater 1:1 com valores nominais usar `auto_adjust=False` (já aplicado) — mesma ressalva já conhecida do app.

## Results
**VERDICT: VALIDATED ✓**

A lib open-source do próprio TradingView entrega, dentro da nossa stack (Streamlit + CDN, sem
backend, sem dependência Python nova), o "feeling" que o Plotly não dá: scroll-zoom fluido,
crosshair com rótulos nos eixos, **Y-autoscale**, linha de último preço — praticamente de graça
(defaults da lib). Dado real da BBSE3 confere com o TradingView (39,17).

**Surpresa positiva:** quase tudo que queríamos é default da lib — o esforço do chart base é
trivial (~40 linhas de JS). **O custo real do Modo Trading não está no chart base, e sim em
portar as SOBREPOSIÇÕES da nossa engine (zona/stop/alvo/padrões)** → é o Spike 002.

**Limitação a carregar para o build:** persistência de zoom entre reruns exige guardar/reaplicar
o range visível (session_state) — anotar como requisito.
