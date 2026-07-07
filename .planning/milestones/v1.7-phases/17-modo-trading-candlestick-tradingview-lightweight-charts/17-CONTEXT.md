# Phase 17: Modo Trading — Candlestick TradingView (Lightweight Charts) - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning
**Source:** Spikes validados (`.planning/spikes/001`, `002`, `CONVENTIONS.md`) — decisões travadas experimentalmente, substituem discuss-phase.

<domain>
## Phase Boundary

**Entrega:** uma vista **"Modo Trading"** (toggle) DENTRO da aba de swing trade (4º menu, Phase 16) que
renderiza o candlestick puro do ticker/timeframe via **TradingView Lightweight Charts v5**, com a UX que o
Plotly não dá (scroll-zoom, pan, crosshair com rótulos nos eixos, Y-autoscale, linha de último preço) e as
**sobreposições da engine** (zona de entrada, stop, alvo, S/R, Fibonacci, padrões/pivôs) portadas.

**Fora de escopo:** substituir o Plotly (permanece como vista default e na análise densa); subpainéis
RSI/MACD/ADX no LWC (continuam no Plotly); desenho livre/alertas/persistência estilo TradingView Advanced
Charts; qualquer mudança no método/engine; streaming/tempo real pago.

**Não-objetivo:** recalcular método na UI. `app.py` continua **thin renderer** que só lê `SetupSwing`/`SinaisTecnicos`.
</domain>

<decisions>
## Implementation Decisions

### Biblioteca & Integração (LWC-01)
- **TradingView Lightweight Charts v5.x** (Apache-2.0), **pinada por versão** no CDN unpkg (`lightweight-charts.standalone.production.js`, global `LightweightCharts`). Validado com `@5.2.0`.
- Carregada via **`st.components.v1.html`** com os dados serializados em JSON no template — **ZERO dependência Python nova**. NÃO usar o wrapper pip `streamlit-lightweight-charts`.
- API v5: `createChart` → `chart.addSeries(LightweightCharts.CandlestickSeries, …)` (NÃO `addCandlestickSeries` da v4); volume via `HistogramSeries` sobreposto (priceScaleId próprio, scaleMargins).
- Defaults nativos assumidos (não codar do zero): crosshair `CrosshairMode.Normal` (rótulos nos eixos), `rightPriceScale.autoScale`, `priceLineVisible`/`lastValueVisible`.

### Vista & Coexistência com Plotly (LWC-01)
- O "Modo Trading" é um **toggle/segmented control** na aba de swing; o **Plotly permanece a vista default**. Alternar não recalcula a engine — só troca a camada de render sobre os mesmos dados.
- Reusar o OHLC nominal já buscado no bloco de swing (`f.ohlc`, base `auto_adjust=False`) e os campos de `SetupSwing`/`sinais` — sem novo fetch.

### Sobreposições da engine (LWC-02)
- **stop / alvo / Fibonacci** → `series.createPriceLine({price, color, lineStyle, axisLabelVisible, title})` (nativo, rótulo no eixo).
- **zona de entrada / S-R** → **`BandPrimitive`**: um único *series primitive* v5 reutilizável (`attachPrimitive`, `zOrder='bottom'`, `priceToCoordinate`+`fillRect` em `useBitmapCoordinateSpace`). ~30 linhas JS. Cores: entrada azul, suporte verde, resistência vermelho (espelha o Plotly atual).
- **pivôs / padrões** → `createSeriesMarkers`. Neckline de padrão (opcional) → `LineSeries` de 2 pontos (time/price). Copy neutra "estudo"/"projeção de estudo" mantida (fronteira SWING-02).
- Cada bloco gateado pelo mesmo toggle de overlay do Plotly (`est[...]`) e degrada sem quebrar quando campos da engine são None/vazios (paridade com `app.py:751-799`).

### Robustez Streamlit (LWC-03)
- **Persistir o range visível** entre reruns: guardar em `st.session_state` e reaplicar via `timeScale().setVisibleRange()` (o iframe de `components.html` re-renderiza a cada rerun). Requisito de aceite.
- `components.html` é sandbox unidirecional (Python→JS): OK para exibição; sem necessidade de callback de volta.

### Invariantes (gates herdados da v1.4)
- **`app.py` permanece read-only** quanto a método (thin renderer); toda a lógica continua na engine. A nova camada é **só render**.
- **`grafico.py` NÃO é tocado** (funções puras golden-pinned) — o LWC é um caminho de render alternativo, não substitui o pipeline Plotly.
- **283+ testes golden verdes** ao final; **zero dependência de runtime nova**; **custo-zero**.

### Claude's Discretion
- Nome/rótulo exato do toggle ("Modo Trading" vs "Gráfico TV") e sua posição na aba.
- Organização do código JS (helper `BandPrimitive` inline no template vs string module) e do wrapper Python (função `_render_lwc(...)` em `app.py` ou helper de UI).
- Altura do chart, paleta fina, formato de data do eixo, chave de `session_state` para o range.
- Estratégia de teste do wrapper (o JS não é testável por golden; validar a montagem do payload Python + smoke no navegador).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Spikes validados (contrato de design desta fase)
- `.planning/spikes/001-tv-feel-candlestick/README.md` — chart base + interações; API v5; limitações (rerun perde zoom).
- `.planning/spikes/001-tv-feel-candlestick/spike_app.py` — template `components.html` + CDN funcional (candlestick + volume + último preço).
- `.planning/spikes/002-overlays-da-engine/README.md` — porte das sobreposições; tabela de esforço; `BandPrimitive`.
- `.planning/spikes/002-overlays-da-engine/spike_app.py` — `createPriceLine` + `BandPrimitive` + `createSeriesMarkers` funcionais.
- `.planning/spikes/CONVENTIONS.md` — stack, padrões e gotchas consolidados.

### Código a integrar/reusar (NÃO alterar a lógica)
- `app.py:583-836` — bloco atual da aba de swing (Plotly): fetch/cache do OHLC, montagem da figura, overlays `add_hrect`/`add_hline` (`app.py:751-799`) que serão espelhados no LWC.
- `report/setup.py` / `SetupSwing` — campos lidos (`entrada_zona`, `stop`, `alvo`, `sinais.niveis`, `sinais.padroes`). Read-only.
- `src/.../grafico.py` — funções puras golden-pinned (referência de cores/estilos; **não modificar**).

### Requisitos & gates
- `.planning/REQUIREMENTS.md` — LWC-01, LWC-02, LWC-03 (v1.5).
- `.planning/ROADMAP.md` — Phase 17 (success criteria) + gates inegociáveis da v1.4 (app.py read-only, goldens, zero deps).
</canonical_refs>

<specifics>
## Specific Ideas
- Dado de teste canônico: **BBSE3 diário** (validado 1:1 contra o TradingView: fechamento 30/jun @ R$39,17; setup entrada 38,50–39,12 / stop 37,50 / alvo 41,74 / RR 2,2).
- CDN pinado: `https://unpkg.com/lightweight-charts@5.2.0/dist/lightweight-charts.standalone.production.js`.
</specifics>

<deferred>
## Deferred Ideas
- Subpainéis RSI/MACD/ADX no LWC (multipane v5) — ficam no Plotly por ora.
- Neckline inclinada de OCO e histograma measured-move no LWC (baixo risco, follow-on).
- TradingView Advanced Charts (desenho/alertas/persistência) — Caminho D, fora de escopo.
- Sincronização bidirecional (ler zoom/click de volta para Python) via componente custom.
</deferred>

---

*Phase: 17-modo-trading-candlestick-tradingview-lightweight-charts*
*Context seeded 2026-07-01 from validated spikes (001, 002) — substitui discuss-phase.*
