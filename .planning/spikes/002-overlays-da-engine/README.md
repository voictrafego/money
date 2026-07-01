---
spike: 002
name: overlays-da-engine
type: standard
validates: "Given os níveis da engine (entrada 38,50–39,12 / stop 37,50 / alvo 41,74), when desenhados no Lightweight Charts, then stop/alvo viram priceLines nativos e a zona de entrada vira banda preenchida — medindo o esforço de portar vs add_hrect/add_hline"
verdict: VALIDATED
related: [001]
tags: [overlays, pricelines, band, series-primitive, porting]
---

# Spike 002: overlays-da-engine

## O que valida
**Given** os níveis da nossa engine (entrada 38,50–39,12 · stop 37,50 · alvo 41,74), **when**
desenhados no chart Lightweight Charts, **then** stop/alvo viram `priceLines` nativos, a **zona de
entrada vira uma banda preenchida** (equivalente ao `add_hrect` do Plotly) e os pivôs de padrão
viram `markers` — medindo o esforço de portar `app.py:751-767`.

## Research
API de desenho no Lightweight Charts v5:
- **`series.createPriceLine({price, color, lineStyle, lineWidth, axisLabelVisible, title})`** — linha horizontal NATIVA, já com rótulo no eixo de preço. Cobre stop, alvo e as bordas da zona. Trivial.
- **Banda preenchida (retângulo de preço ao longo do tempo):** NÃO é nativa. Precisa de um **series primitive** (`series.attachPrimitive(p)`), onde `p.paneViews()[].renderer().draw(target)` desenha na canvas via `target.useBitmapCoordinateSpace` usando `series.priceToCoordinate(preço)`. `zOrder()='bottom'` coloca a banda atrás dos candles. ~30 linhas de JS, reutilizável.
- **`createSeriesMarkers(series, [{time, position, color, shape, text}])`** — marcadores nos pivôs (fundo duplo etc.). Trivial.

## How to Run
```bash
.venv/bin/streamlit run .planning/spikes/002-overlays-da-engine/spike_app.py \
  --server.port 8600 --server.headless true
# abrir http://localhost:8600 — toggle liga/desliga as sobreposições
```

## What to Expect
Banda azul (zona 38,50–39,12) atrás dos candles; linha tracejada vermelha `stop` @ 37,50 e verde
`alvo` @ 41,74, ambas com rótulo no eixo; bordas da zona pontilhadas; bolinhas `pivô` abaixo das
barras. Toggle desliga tudo.

## Observability
Log no console do browser: `[spike002] overlays OK` / `status=ligadas`. Bloco `try/catch` em volta
das sobreposições → se a API divergir, o chart base ainda renderiza e o erro vai pro console
(degradação graciosa). Verificado: **sem erros**.

## Investigation Trail
1. **priceLines (stop/alvo/bordas):** funcionaram de primeira, com rótulo no eixo — na prática **melhor** que o Plotly, que precisa de `annotation_text` manual em `add_hline`.
2. **Banda de zona (a incerteza):** o `series primitive` v5 renderizou a banda preenchida atrás dos candles corretamente (`priceToCoordinate` + `fillRect` em bitmap space). **Anexou limpo, sem erro** (console `overlays OK`). Este era o único ponto de risco de porte — resolvido em ~30 linhas.
3. **markers:** `createSeriesMarkers` colocou os pivôs sem atrito.
4. **Verificação visual:** screenshot confirma banda + stop/alvo rotulados + pivôs + linha de último preço nativa, tudo sobre dado real BBSE3 (39,17).

## Results
**VERDICT: VALIDATED ✓**

Todas as sobreposições da engine portam para o Lightweight Charts:

| Overlay (Plotly hoje) | Lightweight Charts | Esforço |
|-----------------------|--------------------|---------|
| stop/alvo (`add_hline`) | `createPriceLine` (nativo, rótulo no eixo) | **Trivial** — e melhor |
| zona de entrada (`add_hrect`) | `BandPrimitive` (series primitive) | **Baixo** — ~30 linhas, reutilizável |
| suportes/resistências (`add_hrect`) | mesmo `BandPrimitive` (verde/vermelho) | Reuso |
| fib (`add_hline` pontilhado) | `createPriceLine` lineStyle dotted | Trivial |
| padrões: neckline + pivôs | `LineSeries` (2 pts) + `createSeriesMarkers` | Baixo (não testado a neckline, mas API é a mesma família) |

**Conclusão:** o custo de porte das sobreposições é **baixo e concentrado num único helper** (o
`BandPrimitive`, escrito uma vez). O resto é API nativa igual ou melhor que o Plotly. Combinado
com o Spike 001, o **Modo Trading é viável e barato** — nenhuma dependência Python nova, sem tocar
`grafico.py`/golden tests.

**Não testado (follow-on, baixo risco):** neckline inclinada de OCO (LineSeries com 2 pontos time/price),
histograma measured-move, e a persistência de zoom entre reruns (herdada do Spike 001).
