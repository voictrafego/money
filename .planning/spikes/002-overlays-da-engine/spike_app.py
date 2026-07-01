"""Spike 002 — overlays-da-engine (DESCARTÁVEL).

Estende o Spike 001: sobrepõe os níveis da NOSSA engine no chart Lightweight Charts,
para medir o esforço de portar o que hoje é add_hrect/add_hline no Plotly (app.py:751-767):

  - stop / alvo   -> priceLines nativos (título + rótulo no eixo)   [TRIVIAL]
  - zona de entrada -> BANDA preenchida via series primitive v5      [a parte incerta]
  - marcadores de padrão (pivôs) -> markers                          [fácil]

Níveis reais da BBSE3 (validados contra o TradingView):
  entrada 38,50–39,12 · stop 37,50 · alvo 41,74 · RR ~2,2

Rodar:
    .venv/bin/streamlit run .planning/spikes/002-overlays-da-engine/spike_app.py --server.port 8600 --server.headless true
"""
from __future__ import annotations

import json
import math

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Spike 002 — overlays", layout="wide")
st.title("Spike 002 · Modo Trading — sobreposições da engine (zona / stop / alvo)")

# Níveis da engine (hardcoded para o spike — no build viriam de sinais.niveis / sw)
ENTRADA = (38.50, 39.12)
STOP = 37.50
ALVO = 41.74
mostrar = st.toggle("Mostrar sobreposições da engine", value=True)

TICKER = "BBSE3.SA"


@st.cache_data(show_spinner=False)
def carregar_ohlc() -> tuple[list[dict], str]:
    try:
        import yfinance as yf

        df = yf.download(TICKER, period="1y", interval="1d", auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        if df.empty:
            raise RuntimeError("vazio")
        out = [
            {"time": ts.strftime("%Y-%m-%d"), "open": round(float(r["Open"]), 2),
             "high": round(float(r["High"]), 2), "low": round(float(r["Low"]), 2),
             "close": round(float(r["Close"]), 2)}
            for ts, r in df.iterrows()
        ]
        return out, "yfinance (real)"
    except Exception as exc:  # noqa: BLE001
        st.warning(f"yfinance indisponível ({exc}); série sintética.")
        out, base, preco = [], pd.Timestamp("2025-07-01"), 34.0
        for i in range(250):
            drift = 0.02 + 0.6 * math.sin(i / 18.0)
            ruido = ((i * 2654435761) % 1000) / 1000.0 - 0.5
            o, c = preco, max(5.0, preco + drift + ruido)
            out.append({"time": (base + pd.Timedelta(days=i)).strftime("%Y-%m-%d"),
                        "open": round(o, 2), "high": round(max(o, c) + abs(ruido) * 0.8, 2),
                        "low": round(min(o, c) - abs(ruido) * 0.8, 2), "close": round(c, 2)})
            preco = c
        return out, "sintético (fallback)"


candles, fonte = carregar_ohlc()
st.caption(
    f"Fonte: **{fonte}** · última {candles[-1]['time']} @ R$ {candles[-1]['close']} · "
    f"níveis: entrada {ENTRADA[0]}–{ENTRADA[1]} · stop {STOP} · alvo {ALVO}"
)

cfg = {
    "candles": candles,
    "mostrar": mostrar,
    "entrada": list(ENTRADA),
    "stop": STOP,
    "alvo": ALVO,
    # marcadores de padrão (exemplo: 2 pivôs de um "fundo duplo em formação")
    "pivos": [
        {"time": candles[max(0, len(candles) - 60)]["time"], "price": candles[max(0, len(candles) - 60)]["low"]},
        {"time": candles[max(0, len(candles) - 25)]["time"], "price": candles[max(0, len(candles) - 25)]["low"]},
    ],
}

html = f"""
<div id="chart" style="width:100%;height:560px"></div>
<script src="https://unpkg.com/lightweight-charts@5.2.0/dist/lightweight-charts.standalone.production.js"></script>
<script>
  const CFG = {json.dumps(cfg)};
  const {{ createChart, CandlestickSeries, CrosshairMode, createSeriesMarkers }} = LightweightCharts;
  const el = document.getElementById('chart');
  const chart = createChart(el, {{
    layout: {{ background: {{ color: '#0e1117' }}, textColor: '#d1d4dc', fontSize: 12 }},
    grid: {{ vertLines: {{ color: '#1c2030' }}, horzLines: {{ color: '#1c2030' }} }},
    crosshair: {{ mode: CrosshairMode.Normal }},
    rightPriceScale: {{ borderColor: '#2a2e39', autoScale: true }},
    timeScale: {{ borderColor: '#2a2e39', rightOffset: 6 }},
  }});
  const candle = chart.addSeries(CandlestickSeries, {{
    upColor: '#26a69a', downColor: '#ef5350', wickUpColor: '#26a69a',
    wickDownColor: '#ef5350', borderVisible: false,
  }});
  candle.setData(CFG.candles);

  // --- PRIMITIVE: banda de preço horizontal preenchida (equivalente ao add_hrect) ---
  class BandPrimitive {{
    constructor(series, low, high, color) {{ this._s = series; this._low = low; this._high = high; this._color = color; this._pv = new BandPaneView(this); }}
    updateAllViews() {{}}
    paneViews() {{ return [this._pv]; }}
  }}
  class BandPaneView {{
    constructor(src) {{ this._src = src; }}
    zOrder() {{ return 'bottom'; }}                       // atrás dos candles
    renderer() {{
      const src = this._src;
      return {{ draw(target) {{
        target.useBitmapCoordinateSpace((scope) => {{
          const yH = src._s.priceToCoordinate(src._high);
          const yL = src._s.priceToCoordinate(src._low);
          if (yH == null || yL == null) return;
          const ctx = scope.context, vr = scope.verticalPixelRatio;
          ctx.fillStyle = src._color;
          ctx.fillRect(0, yH * vr, scope.bitmapSize.width, (yL - yH) * vr);
        }});
      }} }};
    }}
  }}

  let overlaysInfo = 'ligadas';
  if (CFG.mostrar) {{
    try {{
      // 1) stop / alvo -> priceLines nativos (TRIVIAL, com rótulo no eixo)
      candle.createPriceLine({{ price: CFG.stop, color: '#ef5350', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'stop' }});
      candle.createPriceLine({{ price: CFG.alvo, color: '#26a69a', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'alvo' }});
      // bordas da zona (linha pontilhada), além da banda preenchida
      candle.createPriceLine({{ price: CFG.entrada[0], color: '#2962ff', lineWidth: 1, lineStyle: 3, axisLabelVisible: false, title: 'entrada' }});
      candle.createPriceLine({{ price: CFG.entrada[1], color: '#2962ff', lineWidth: 1, lineStyle: 3, axisLabelVisible: false, title: '' }});
      // 2) zona de entrada -> BANDA preenchida (a parte incerta)
      candle.attachPrimitive(new BandPrimitive(candle, CFG.entrada[0], CFG.entrada[1], 'rgba(41,98,255,0.18)'));
      // 3) marcadores de padrão (pivôs) -> markers
      if (createSeriesMarkers) {{
        createSeriesMarkers(candle, CFG.pivos.map(p => ({{
          time: p.time, position: 'belowBar', color: '#2ca02c', shape: 'circle', text: 'pivô'
        }})));
      }}
      console.log('[spike002] overlays OK');
    }} catch (e) {{
      overlaysInfo = 'ERRO: ' + e.message;
      console.error('[spike002] overlay error', e);
    }}
  }} else {{ overlaysInfo = 'desligadas'; }}
  console.log('[spike002] status=' + overlaysInfo);

  chart.timeScale().fitContent();
  new ResizeObserver(() => chart.applyOptions({{ width: el.clientWidth }})).observe(el);
</script>
"""

components.html(html, height=580)
st.caption(
    "Compare com o Plotly atual (`app.py:751-767`): stop/alvo = `createPriceLine` (nativo, com rótulo no eixo) · "
    "zona = **banda via series primitive** (~30 linhas JS) · pivôs = `createSeriesMarkers`. "
    "Ligue/desligue no toggle acima."
)
