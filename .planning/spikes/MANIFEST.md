# Spike Manifest

## Idea
"Modo Trading" (Caminho C do plano de UX): dar ao app Analista de Dividendos uma experiência de
gráfico próxima à do TradingView na aba de swing trade, sem sair da stack (Streamlit + custo zero,
sem backend). Estratégia híbrida: **manter o Plotly** na análise densa (fiel ao método, golden tests
intactos) e adicionar uma vista **"Modo Trading"** que usa a lib open-source **TradingView Lightweight
Charts** só para o candlestick puro — onde a interação estilo TV (scroll-zoom, pan, crosshair,
Y-autoscale, linha de último preço) importa. Objetivo do spike: sentir a UX e medir o esforço de
portar as sobreposições da nossa engine (zona de entrada, stop, alvo, padrões) antes de decidir integrar.

## Requirements
Decisões que emergiram durante o spike (não-negociáveis para o build real):

- **Integração via `st.components.v1.html` + CDN (unpkg)** — zero dependência Python nova; NÃO usar o wrapper pip community.
- **Lightweight Charts v5.x** (API `chart.addSeries(CandlestickSeries, …)`), pinado por versão no CDN.
- **Plotly permanece** na aba de análise densa; Lightweight Charts só no candlestick do swing. `grafico.py` e os golden tests não são tocados.
- **Persistência de zoom entre reruns** do Streamlit precisa ser tratada (guardar/reaplicar range visível via `session_state`).
- Dados com `auto_adjust=False` (nominal) para bater com o app/TradingView.

## Spikes

| # | Name | Type | Validates | Verdict | Tags |
|---|------|------|-----------|---------|------|
| 001 | tv-feel-candlestick | standard | Candlestick BBSE3 via Lightweight Charts em Streamlit entrega UX do TV (zoom/pan/crosshair/Y-autoscale/último preço) | ✅ VALIDATED | ux, charting, lightweight-charts, streamlit |
| 002 | overlays-da-engine | standard | Portar zona de entrada (banda) + stop/alvo (priceLines) + padrões da engine para o chart, medindo esforço vs add_hrect/add_hline | ✅ VALIDATED | overlays, pricelines, band, porting |
