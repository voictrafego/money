# Spike Conventions

Padrões estabelecidos nos spikes do "Modo Trading". Novos spikes seguem isto salvo se a pergunta exigir outro caminho.

## Stack
- **Chart TV-like:** TradingView Lightweight Charts **v5.x** (Apache-2.0), carregada via **CDN unpkg** (`lightweight-charts.standalone.production.js`, global `LightweightCharts`), pinada por versão.
- **Ponte Streamlit↔JS:** `st.components.v1.html(html, height=...)` com os dados serializados em JSON no template. **Zero dependência Python nova.** NÃO usar o wrapper pip `streamlit-lightweight-charts`.
- **Dados:** `yfinance` (`auto_adjust=False`, nominal) com fallback sintético determinístico para o spike rodar offline.

## Structure
- Spikes descartáveis em `.planning/spikes/NNN-nome/spike_app.py` + `README.md` + `run.log`.
- Portas: 001 → 8599, 002 → 8600 (uma por spike, headless).
- Rodar: `.venv/bin/streamlit run <app> --server.port <p> --server.headless true`.

## Patterns
- **Chart base:** `createChart` (tema dark) → `addSeries(CandlestickSeries, …)`; crosshair `CrosshairMode.Normal`; `rightPriceScale.autoScale` e último preço são **default** (não codar).
- **Overlays da engine:**
  - stop / alvo / fib / bordas de zona → `series.createPriceLine({price, color, lineStyle, axisLabelVisible, title})`.
  - zona/suporte/resistência (retângulo de preço) → **`BandPrimitive`** (series primitive v5, `attachPrimitive`, `zOrder='bottom'`, `priceToCoordinate`+`fillRect` em `useBitmapCoordinateSpace`). Helper único e reutilizável.
  - pivôs/padrões → `createSeriesMarkers`.
- **Degradação graciosa:** envolver as sobreposições em `try/catch` + `console.log('[spikeNNN] …')`; ler com `read_console_messages`.
- **Verificação:** rodar headless + abrir no browser + screenshot + checar console. UX = "sentir", não só stdout.

## Tools & Libraries
- ✅ `lightweight-charts@5.2.0` via CDN (funcionou; API v5 = `addSeries(CandlestickSeries,…)`, não `addCandlestickSeries`).
- ✅ `streamlit 1.58.0`, `yfinance 1.4.1` (já no `.venv`).
- ⚠️ Evitar: wrapper pip community (risco de defasagem); `Math.random`/estado não-determinístico no template.
- ⚠️ Carregar p/ o build: rerun do Streamlit re-renderiza o iframe → persistir range visível em `session_state` e reaplicar via `timeScale().setVisibleRange()`.
