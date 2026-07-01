"""Spike 001 — tv-feel-candlestick (DESCARTÁVEL).

Objetivo: sentir a UX do TradingView (scroll-zoom, pan, crosshair com rótulos
nos eixos, Y auto-reescala na janela visível, linha de último preço) usando a
lib open-source TradingView Lightweight Charts v5 embutida no Streamlit via
`components.html` + CDN (unpkg) — ZERO dependência nova.

Rodar:
    .venv/bin/streamlit run .planning/spikes/001-tv-feel-candlestick/spike_app.py --server.port 8599 --server.headless true

NÃO é código de produção. Não importa nada do app real. Descartar após decidir.
"""
from __future__ import annotations

import json
import math

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Spike 001 — TV feel", layout="wide")
st.title("Spike 001 · Modo Trading (Lightweight Charts) — candlestick BBSE3")
st.caption(
    "UX-alvo: scroll = zoom · arrastar = pan · crosshair com rótulos nos eixos · "
    "Y reescala sozinho no zoom · linha de último preço. Lib: TradingView Lightweight Charts v5 (CDN)."
)

TICKER = "BBSE3.SA"


@st.cache_data(show_spinner=False)
def carregar_ohlc() -> tuple[list[dict], list[dict], str]:
    """Tenta yfinance (dado real); cai para série sintética determinística se falhar,
    para o spike de UX ser sempre demonstrável (inclusive offline)."""
    fonte = "yfinance (real)"
    try:
        import yfinance as yf

        df = yf.download(
            TICKER, period="1y", interval="1d", auto_adjust=False, progress=False
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        if df.empty:
            raise RuntimeError("yfinance vazio")
        candles, vols = [], []
        for ts, row in df.iterrows():
            t = ts.strftime("%Y-%m-%d")
            candles.append(
                {
                    "time": t,
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                }
            )
            up = float(row["Close"]) >= float(row["Open"])
            vols.append(
                {
                    "time": t,
                    "value": float(row.get("Volume", 0) or 0),
                    "color": "rgba(38,166,154,0.5)" if up else "rgba(239,83,80,0.5)",
                }
            )
        return candles, vols, fonte
    except Exception as exc:  # noqa: BLE001 — spike: qualquer falha vira fallback
        st.warning(f"yfinance indisponível ({exc}). Usando série SINTÉTICA só p/ sentir a UX.")
        # random walk determinístico (sem Math.random): senoide + ruído pseudo por índice
        candles, vols = [], []
        base = pd.Timestamp("2025-07-01")
        preco = 34.0
        for i in range(250):
            drift = 0.02 + 0.6 * math.sin(i / 18.0)
            ruido = ((i * 2654435761) % 1000) / 1000.0 - 0.5  # hash → [-0.5, 0.5]
            o = preco
            c = max(5.0, preco + drift + ruido)
            h = max(o, c) + abs(ruido) * 0.8
            lo = min(o, c) - abs(ruido) * 0.8
            t = (base + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
            candles.append(
                {"time": t, "open": round(o, 2), "high": round(h, 2),
                 "low": round(lo, 2), "close": round(c, 2)}
            )
            up = c >= o
            vols.append(
                {"time": t, "value": 5_000_000 + (i % 30) * 200_000,
                 "color": "rgba(38,166,154,0.5)" if up else "rgba(239,83,80,0.5)"}
            )
            preco = c
        return candles, vols, "sintético (fallback)"


candles, vols, fonte = carregar_ohlc()
st.caption(f"Fonte dos dados: **{fonte}** · {len(candles)} barras diárias · última: {candles[-1]['time']} @ R$ {candles[-1]['close']}")

CANDLES_JSON = json.dumps(candles)
VOLS_JSON = json.dumps(vols)

html = f"""
<div id="chart" style="width:100%;height:560px"></div>
<script src="https://unpkg.com/lightweight-charts@5.2.0/dist/lightweight-charts.standalone.production.js"></script>
<script>
  const {{ createChart, CandlestickSeries, HistogramSeries, CrosshairMode }} = LightweightCharts;
  const el = document.getElementById('chart');
  const chart = createChart(el, {{
    layout: {{ background: {{ color: '#0e1117' }}, textColor: '#d1d4dc', fontSize: 12 }},
    grid: {{ vertLines: {{ color: '#1c2030' }}, horzLines: {{ color: '#1c2030' }} }},
    crosshair: {{ mode: CrosshairMode.Normal }},              // crosshair + rótulos nos eixos
    rightPriceScale: {{ borderColor: '#2a2e39', autoScale: true }},  // Y reescala sozinho
    timeScale: {{ borderColor: '#2a2e39', rightOffset: 6, timeVisible: false }},
    handleScroll: true, handleScale: true,                    // scroll=zoom, arrastar=pan
  }});

  const candle = chart.addSeries(CandlestickSeries, {{
    upColor: '#26a69a', downColor: '#ef5350',
    wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    borderVisible: false,
    priceLineVisible: true, lastValueVisible: true,           // linha de último preço (padrão)
  }});
  candle.setData({CANDLES_JSON});

  // Volume como histograma sobreposto no rodapé (price scale própria, invisível)
  const vol = chart.addSeries(HistogramSeries, {{
    priceFormat: {{ type: 'volume' }}, priceScaleId: '',
    lastValueVisible: false, priceLineVisible: false,
  }});
  vol.priceScale().applyOptions({{ scaleMargins: {{ top: 0.82, bottom: 0 }} }});
  vol.setData({VOLS_JSON});

  chart.timeScale().fitContent();
  new ResizeObserver(() => chart.applyOptions({{ width: el.clientWidth }})).observe(el);
</script>
"""

components.html(html, height=580)

st.divider()
st.markdown(
    "**Teste a UX:** role o mouse sobre o gráfico (zoom no tempo) · arraste (pan) · "
    "passe o cursor (crosshair com preço/data nos eixos) · repare que o **eixo Y reenquadra sozinho** "
    "ao dar zoom — o recurso que o Plotly não entrega. A **linha tracejada de último preço** também é nativa."
)
