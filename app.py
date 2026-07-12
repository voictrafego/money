"""Interface web (Streamlit) do Analista de Dividendos.

Rode com:  ./.venv/bin/streamlit run app.py
Abre no navegador. Mesma engine do CLI. Referências da metodologia: página "Metodologia e referências" (rodapé).
"""

from __future__ import annotations

import json
import math
import os
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from plotly.subplots import make_subplots

from analista import grafico
from analista.core import comparables as cmp
from analista.core import indicators
from analista.core import lentes
from analista.core import multiples as mult
from analista.core import screening as sc
from analista.glossario import h
from analista.ingest import build, macro
from analista.report import comparador, presentation, report, selo, setup

ROOT = os.path.dirname(os.path.abspath(__file__))
import yaml

st.set_page_config(page_title="Analista de Dividendos", layout="wide")

# Logout: o app roda atrás do gate Django (sessão no domínio .lazaricapital.com.br).
# O botão aponta para o endpoint GET de logout no host www (encerra a sessão e
# redireciona ao login). Override por env em dev/outros ambientes.
LOGOUT_URL = os.environ.get(
    "WWW_LOGOUT_URL", "https://www.lazaricapital.com.br/sair-app/"
)


def _current_user_email() -> str | None:
    """Identidade injetada pelo gate Traefik forwardAuth (AUTH-03). Read-only.

    O Traefik promove `X-User-Email` (via authResponseHeaders) para o request
    upstream depois que o gate Django já validou a sessão/trial. Aqui só LEMOS
    esse header — requer streamlit>=1.37 (st.context). Fora do gate (dev local
    sem Traefik) `st.context` pode não trazer o header → retorna None (anônimo/dev).

    ATENÇÃO: NUNCA usar este valor para autorizar acesso — o gate já garantiu que
    só quem tem trial/assinatura ativa chega aqui. Serve apenas para
    personalização / telemetria / "logado como fulano".
    """
    try:
        return st.context.headers.get("X-User-Email")  # case-insensitive
    except Exception:
        return None


user_email = _current_user_email()  # noqa: F841 — read-only; personalização/telemetria (não autoriza)

# --------------------------------------------------------------------------- #
# Design system (visual only — não altera dados nem fluxo). Mescla de 3 refs:
# Financial SaaS Metrics (base dark institucional + verde #00E55F), Analytics
# Remixed (azul #3A83FF + esmeralda, hover-lift, entrada escalonada) e Aura
# (degradês/glow de fundo, cantos arredondados, pills). Fontes Inter + JetBrains
# Mono. Injetado uma vez, no boot; sem custo por rerun.
# --------------------------------------------------------------------------- #
_DESIGN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root{
  --bg:#09090B; --surface:#161618; --surface-2:#1C1C20; --border:#27272A;
  --text:#FAFAFA; --muted:#A1A1AA;
  --green:#00E55F; --green-deep:#008A39; --emerald:#34D399;
  --blue:#3A83FF; --lime:#A3E635; --red:#FB5E7E;
  --r-card:16px; --r-ctl:10px;
}

/* Base ------------------------------------------------------------------ */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stSidebar"], .stMarkdown, p, span, div, label, input, button{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
}
.stApp{
  background:
    radial-gradient(1200px 620px at 10% -10%, rgba(0,229,95,0.10), transparent 58%),
    radial-gradient(1000px 520px at 92% -14%, rgba(58,131,255,0.11), transparent 55%),
    radial-gradient(900px 500px at 50% 120%, rgba(163,230,53,0.05), transparent 60%),
    var(--bg);
  color:var(--text);
}
/* faixa fina em degradê no topo da página */
[data-testid="stAppViewContainer"]::before{
  content:""; position:fixed; top:0; left:0; right:0; height:2px; z-index:1000;
  background:linear-gradient(90deg, var(--green), var(--blue) 55%, var(--lime));
  opacity:.9;
}
[data-testid="stMain"] .block-container{ animation:hf-fade .55s ease both; padding-top:3.2rem; }
@keyframes hf-fade{ from{opacity:0; transform:translateY(6px);} to{opacity:1; transform:none;} }

/* Tipografia ------------------------------------------------------------ */
h1{
  font-weight:800!important; letter-spacing:-.025em; font-size:2.55rem!important; line-height:1.05!important;
  background:linear-gradient(92deg,#FFFFFF 0%, #EAFFEC 28%, var(--green) 66%, var(--blue) 108%);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
h2,h3{ font-weight:700!important; letter-spacing:-.012em; color:var(--text); }
h3{ font-size:1.16rem!important; }
[data-testid="stMarkdownContainer"] h3{ position:relative; padding-left:15px; margin-top:.4rem; }
[data-testid="stMarkdownContainer"] h3::before{
  content:""; position:absolute; left:0; top:.18em; bottom:.18em; width:4px; border-radius:9999px;
  background:linear-gradient(180deg,var(--green),var(--blue));
}

/* Sidebar --------------------------------------------------------------- */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0D0D11 0%, var(--bg) 100%);
  border-right:1px solid var(--border);
}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label{
  padding:.5rem .7rem; margin:.12rem 0; border-radius:var(--r-ctl);
  border:1px solid transparent; transition:background .18s ease, border-color .18s ease, transform .18s ease;
}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover{
  background:rgba(255,255,255,0.045); border-color:var(--border); transform:translateX(2px);
}

/* Cards de métrica (watchlist) ------------------------------------------ */
[data-testid="stMetric"]{
  background:linear-gradient(160deg, var(--surface-2), var(--surface));
  border:1px solid var(--border); border-radius:var(--r-card); padding:1rem 1.05rem;
  box-shadow:0 1px 0 rgba(255,255,255,0.03) inset, 0 10px 26px -20px rgba(0,0,0,.95);
  transition:transform .2s ease, border-color .2s ease, box-shadow .2s ease;
  animation:hf-rise .5s cubic-bezier(.2,.7,.2,1) both;
}
[data-testid="stMetric"]:hover{
  transform:translateY(-3px); border-color:rgba(0,229,95,0.38);
  box-shadow:0 20px 44px -24px rgba(0,229,95,0.4);
}
[data-testid="stMetricValue"]{
  font-family:'JetBrains Mono',monospace!important; font-weight:600; letter-spacing:-.03em;
  font-variant-numeric:tabular-nums; font-size:1.55rem!important;
}
[data-testid="stMetricValue"] > *{ overflow:visible!important; text-overflow:clip!important; white-space:nowrap!important; }
[data-testid="stMetricLabel"] p{
  font-family:'JetBrains Mono',monospace!important; text-transform:uppercase; letter-spacing:.09em;
  font-size:.72rem!important; color:var(--muted)!important; font-weight:600;
}
[data-testid="stMetricDelta"]{ font-family:'JetBrains Mono',monospace!important; font-weight:600; }
@keyframes hf-rise{ from{opacity:0; transform:translateY(12px);} to{opacity:1; transform:none;} }
[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stMetric"]{ animation-delay:.03s; }
[data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetric"]{ animation-delay:.09s; }
[data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetric"]{ animation-delay:.15s; }
[data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stMetric"]{ animation-delay:.21s; }
[data-testid="stHorizontalBlock"] > div:nth-child(5) [data-testid="stMetric"]{ animation-delay:.27s; }

/* Sidebar metric (Selic) ------------------------------------------------ */
[data-testid="stSidebar"] [data-testid="stMetric"]{ animation:none; }

/* Botões ---------------------------------------------------------------- */
.stButton > button{
  border-radius:var(--r-ctl)!important; border:1px solid var(--border)!important;
  background:var(--surface-2)!important; color:var(--text)!important; font-weight:600!important;
  transition:transform .18s ease, border-color .18s ease, box-shadow .18s ease, color .18s ease;
}
.stButton > button:hover{
  border-color:var(--green)!important; color:#fff!important; transform:translateY(-1px);
  box-shadow:0 12px 26px -18px rgba(0,229,95,.65);
}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"]{
  background:linear-gradient(92deg,var(--green),var(--emerald))!important; color:#04140A!important;
  border:none!important; box-shadow:0 10px 26px -16px rgba(0,229,95,.7)!important;
}
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{
  filter:brightness(1.06); transform:translateY(-1px);
}

/* Link button (Abrir no site) ------------------------------------------- */
[data-testid="stLinkButton"] a{
  border-radius:9999px!important; border:1px solid var(--border)!important; background:transparent!important;
  color:var(--text)!important; font-weight:600!important;
  transition:border-color .18s ease, color .18s ease, transform .18s ease;
}
[data-testid="stLinkButton"] a:hover{ border-color:var(--blue)!important; color:#fff!important; transform:translateY(-1px); }

/* Expander -------------------------------------------------------------- */
[data-testid="stExpander"]{
  border:1px solid var(--border)!important; border-radius:var(--r-card)!important;
  background:var(--surface)!important; overflow:hidden;
}
[data-testid="stExpander"] summary:hover{ color:var(--green)!important; }

/* Inputs ---------------------------------------------------------------- */
.stTextInput input, [data-baseweb="input"]{
  background:var(--surface-2)!important; border-radius:var(--r-ctl)!important;
  border:1px solid var(--border)!important; color:var(--text)!important;
}
.stTextInput input:focus{ border-color:var(--green)!important; box-shadow:0 0 0 3px rgba(0,229,95,.16)!important; }

/* Abas ------------------------------------------------------------------ */
.stTabs [data-baseweb="tab-list"]{ gap:4px; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"]{ font-weight:600!important; }
.stTabs [aria-selected="true"]{ color:var(--green)!important; }
.stTabs [data-baseweb="tab-highlight"]{ background:var(--green)!important; }

/* Alertas --------------------------------------------------------------- */
[data-testid="stAlert"]{ border-radius:var(--r-ctl)!important; }

/* Captions / divisores -------------------------------------------------- */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p{ color:var(--muted)!important; }
hr, [data-testid="stDivider"] hr{ border-color:var(--border)!important; }

/* DataFrame / tabelas --------------------------------------------------- */
[data-testid="stDataFrame"], [data-testid="stTable"]{
  border:1px solid var(--border); border-radius:var(--r-card); overflow:hidden;
}
</style>
"""
st.markdown(_DESIGN_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def carregar_config():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


@st.cache_data(show_spinner=False, ttl=3600)
def montar(ticker: str, ano_base: int, n: int):
    return build.montar_empresa(ticker, ano_base, n)


@st.cache_data(show_spinner=False, ttl=3600)
def selic_atual():
    return macro.selic_meta() or 0.105


@st.cache_data(show_spinner=False, ttl=3600)
def rf_capm(fallback, anos):
    """rf do CAPM/DDM: Selic through-the-cycle (média ~10 anos), não a spot — numa
    perpetuidade a taxa de desconto reflete o juro de LP. Uma chamada de rede por execução."""
    return macro.selic_ciclo_para_capm(fallback, anos)


@st.cache_data(show_spinner=False, ttl=300)
def frame_intraday(ticker: str, timeframe: str, nonce: int):
    """Wrapper de cache do OHLCV intraday — TTL curto (300s), invalidação por nonce.

    `nonce` entra SÓ na chave de cache (não é repassado à engine): incrementá-lo no
    botão Atualizar (Fase 16) cria uma nova entrada só para aquele (ticker, timeframe)
    e a antiga expira pelo TTL — nunca um clear global, que apagaria o cache de
    montar/selic_atual/rf_capm da aba Analisar (D-08)."""
    from analista.ingest import intraday  # import tardio: isola o módulo intraday

    return intraday.coletar_intraday(ticker, timeframe)


def _nonce_key(ticker: str, timeframe: str) -> str:
    """Chave de st.session_state do nonce por par (ticker, timeframe) — o botão
    Atualizar (Fase 16) faz setdefault(k, 0) e incrementa só este par."""
    return f"nonce_intraday::{ticker}::{timeframe}"


CFG = carregar_config()
ANO_BASE = CFG["universo"]["ano_base"]
N_ANOS = CFG["universo"]["anos_historico"]


def fmt_pct(x, casas=1):
    if x is None:
        return "—"
    v = x * 100
    if round(v, casas) == 0:  # evita "-0.0%" (zero negativo) → "0.0%"
        v = 0.0
    return f"{v:.{casas}f}%"


def fmt_num(x, casas=2):
    return "—" if x is None else f"{x:.{casas}f}"


def fmt_rs(x, casas=2):
    return "—" if x is None else f"R$ {x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def esc_md(s: str) -> str:
    """Escapa '$' p/ contextos markdown (metric, alertas): dois 'R$' na mesma
    string fariam o Streamlit interpretar o miolo como LaTeX e quebrar o layout."""
    return s.replace("$", r"\$")


# --------------------------------------------------------------------------- #
# "Modo Trading" — candlestick TradingView (Lightweight Charts v5) via CDN.
# Camada de RENDER alternativa ao Plotly (LWC-01): ZERO dependência Python nova
# (só st.components.v1.html + CDN pinado). NÃO recalcula a engine — serializa o
# OHLC nominal (`f.ohlc`) e os campos de setup já montados. `grafico.py` intacto.
# CDN pinado por versão exata (@5.2.0) + SRI (integrity sha384) + crossorigin
# mitigam a ameaça T-17-01 (tampering do bundle de terceiros).
_LWC_CDN_URL = (
    "https://unpkg.com/lightweight-charts@5.2.0/dist/"
    "lightweight-charts.standalone.production.js"
)
# SRI real do bundle @5.2.0, inline no <script> abaixo
# (openssl dgst -sha384 -binary | openssl base64 -A): sha384-q1KYLSKHgBnW5tWYGGR8+6YV4/...


def _js_json(obj):
    """json.dumps seguro p/ embutir dentro de <script>.

    Neutraliza `</script>` e os separadores de linha U+2028/U+2029 escapando
    `<`, `>`, `&` para `\\uXXXX`. Os escapes continuam sendo JS/JSON válidos e
    decodificam para os mesmos caracteres, então o dado legítimo não muda — só
    perde o poder de fechar a tag e injetar markup (CR-01).
    """
    return (json.dumps(obj)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def _render_lwc(f, sw, sinais, est, ticker, tf_key):
    """Renderiza o candlestick nominal do ticker via Lightweight Charts v5.

    `tf_key` está na assinatura (module-level, sem closure) porque as waves
    seguintes dependem dela: a persistência de range (Task 2) compõe a chave do
    localStorage por (ticker, tf_key) e o plano 02 usa `tf_key` p/ converter ts
    de pivô em epoch. Serializa `f.ohlc` (nominal, Pitfall 6) — sem recálculo.
    Time: diário → string "%Y-%m-%d"; intraday → epoch UTC segundos (UTCTimestamp
    do LWC), p/ crosshair e eixo de tempo corretos nas barras datetime.
    """
    df = f.ohlc
    intraday = tf_key != "diario"
    candles, vols = [], []
    for ts, row in df.iterrows():
        t = int(ts.timestamp()) if intraday else ts.strftime("%Y-%m-%d")
        o, h, lo, c = (float(row["Open"]), float(row["High"]),
                       float(row["Low"]), float(row["Close"]))
        # WR-02: json.dumps emite `NaN` (token que quebra o setData do LWC). Pula a barra
        # se qualquer OHLC for NaN — o Plotly tolera buracos; aqui a série precisa ser limpa.
        if any(math.isnan(v) for v in (o, h, lo, c)):
            continue
        candles.append({"time": t, "open": round(o, 2), "high": round(h, 2),
                        "low": round(lo, 2), "close": round(c, 2)})
        up = c >= o
        vol_v = float(row.get("Volume", 0) or 0)
        if math.isnan(vol_v):
            vol_v = 0.0
        vols.append({"time": t, "value": vol_v,
                     "color": "rgba(38,166,154,0.5)" if up else "rgba(239,83,80,0.5)"})

    # CR-01: os JSON abaixo são embutidos crus dentro de <script>. `_js_json` escapa
    # `<`/`>`/`&` (e U+2028/29) p/ nenhum valor (ex.: ticker) conseguir fechar a tag e injetar markup.
    candles_json = _js_json(candles)
    vols_json = _js_json(vols)
    time_visible = "true" if intraday else "false"
    # Chave de persistência de range por (ticker, timeframe) — evita "vazar" zoom de um par
    # para outro. Ticker restrito a [A-Z0-9] (defesa em profundidade) + _js_json no contexto <script>.
    safe_ticker = re.sub(r"[^A-Z0-9]", "", (ticker or "").upper())
    range_key_json = _js_json(f"lwc_range_{safe_ticker}_{tf_key}")

    # --- Overlays da engine (LWC-02): read-only de sw/sinais, gateados por est[...] ---------
    # Espelha 1:1 o bloco Plotly (app.py: add_hrect/add_hline/add_shape): S/R e zona de entrada
    # como BANDAS (BandPrimitive), stop/alvo/Fibonacci como priceLines rotuladas, pivôs/padrões
    # como markers. Cada grupo é condicionado ao MESMO flag est[...] e degrada sem quebrar quando
    # os campos da engine são None/vazios (o Python filtra; o JS itera só o que chegou). O JSON é
    # SEMPRE serializado com as mesmas chaves (estrutura estável) — grupos desligados vão vazios.
    # Copy dos títulos NEUTRA/de estudo (gate SWING-02): "stop (estudo)", "alvo (estudo)".
    def _ts_to_time(ts):
        return int(ts.timestamp()) if intraday else ts.strftime("%Y-%m-%d")

    overlays = {"suportes": [], "resistencias": [], "entrada": None,
                "stop": None, "alvo": None, "fib": [], "padroes": []}

    if est.get("sr_on") and sinais.niveis is not None:
        overlays["suportes"] = [[round(float(lo), 2), round(float(hi), 2)]
                                for (lo, hi) in sinais.niveis.suportes]
        overlays["resistencias"] = [[round(float(lo), 2), round(float(hi), 2)]
                                    for (lo, hi) in sinais.niveis.resistencias]

    if est.get("niveis_setup_on") and sw.entrada_zona:
        lo, hi = sw.entrada_zona
        overlays["entrada"] = [round(float(lo), 2), round(float(hi), 2)]
        if sw.stop is not None:
            overlays["stop"] = round(float(sw.stop), 2)
        if sw.alvo is not None:
            overlays["alvo"] = round(float(sw.alvo), 2)

    if est.get("fib_on") and sinais.niveis is not None and sinais.niveis.fib_retracoes:
        overlays["fib"] = [{"nome": str(nome), "preco": round(float(preco), 2)}
                           for nome, preco in sinais.niveis.fib_retracoes.items()]

    # Padrões (OFF por padrão, D-02): pivôs → markers, neckline → LineSeries de 2 pontos, alvo →
    # priceLine "projeção de estudo". Cor por direção (espelha _COR_PAD do Plotly): alta verde,
    # baixa vermelho. `ts` convertido p/ o MESMO formato de time do candle via _ts_to_time (string
    # diário / epoch intraday). Markers ordenados por ts (createSeriesMarkers exige ordem crescente).
    if est.get("padroes_on") and sinais.padroes is not None:
        _ALTA = {"duplo_fundo", "oco_invertido"}
        for p in sinais.padroes.lista:
            if not p.pivos_envolvidos:
                continue
            piv = sorted(p.pivos_envolvidos.items(), key=lambda kv: kv[0])
            pivos = [{"time": _ts_to_time(ts), "price": round(float(pr), 2)} for ts, pr in piv]
            overlays["padroes"].append({
                "cor": "#2ca02c" if p.tipo in _ALTA else "#d62728",
                "alta": p.tipo in _ALTA,
                "confirmado": p.estado == "confirmado",
                "estado": "confirmado" if p.estado == "confirmado" else "em formação",
                "tipo": p.tipo.replace("_", " "),
                "neckline": round(float(p.neckline), 2) if p.neckline is not None else None,
                "alvo": round(float(p.alvo), 2) if p.alvo is not None else None,
                "pivos": pivos,
            })

    overlays_json = _js_json(overlays)  # CR-01: idem candles — embutido cru em <script>

    html = f"""
<div id="lwc-chart" style="width:100%;height:560px"></div>
<script src="{_LWC_CDN_URL}" integrity="sha384-q1KYLSKHgBnW5tWYGGR8+6YV4/iPy31dILoF2I1OD7XiVUvHEp/TaxIQVmB0j3R2" crossorigin="anonymous"></script>
<script>
  const el = document.getElementById('lwc-chart');
  // WR-01: se o CDN cair ou o SRI não bater, `LightweightCharts` fica undefined e o
  // destructure lança — sem este try o usuário vê um box preto de 560px sem explicação.
  try {{
  const {{ createChart, CandlestickSeries, HistogramSeries, LineSeries, CrosshairMode, createSeriesMarkers }} = LightweightCharts;
  const chart = createChart(el, {{
    layout: {{ background: {{ color: '#0e1117' }}, textColor: '#d1d4dc', fontSize: 12 }},
    grid: {{ vertLines: {{ color: '#1c2030' }}, horzLines: {{ color: '#1c2030' }} }},
    crosshair: {{ mode: CrosshairMode.Normal }},
    rightPriceScale: {{ borderColor: '#2a2e39', autoScale: true }},
    timeScale: {{ borderColor: '#2a2e39', rightOffset: 6, timeVisible: {time_visible} }},
    handleScroll: true, handleScale: true,
  }});

  const candle = chart.addSeries(CandlestickSeries, {{
    upColor: '#26a69a', downColor: '#ef5350',
    wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    borderVisible: false, priceLineVisible: true, lastValueVisible: true,
  }});
  candle.setData({candles_json});

  const vol = chart.addSeries(HistogramSeries, {{
    priceFormat: {{ type: 'volume' }}, priceScaleId: '',
    lastValueVisible: false, priceLineVisible: false,
  }});
  vol.priceScale().applyOptions({{ scaleMargins: {{ top: 0.82, bottom: 0 }} }});
  vol.setData({vols_json});

  // LWC-02 — sobreposições da engine (read-only de sw/sinais; espelha o bloco Plotly).
  const OV = {overlays_json};

  // Series primitive v5: banda de preço horizontal preenchida (equivalente ao add_hrect do Plotly).
  // zOrder 'bottom' → atrás dos candles; priceToCoordinate + fillRect em useBitmapCoordinateSpace.
  class BandPrimitive {{
    constructor(series, low, high, color) {{ this._s = series; this._low = low; this._high = high; this._color = color; this._pv = new BandPaneView(this); }}
    updateAllViews() {{}}
    paneViews() {{ return [this._pv]; }}
  }}
  class BandPaneView {{
    constructor(src) {{ this._src = src; }}
    zOrder() {{ return 'bottom'; }}
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

  try {{
    // Zonas S/R (bandas): suporte verde, resistência vermelho — espelha o add_hrect verde/vermelho.
    (OV.suportes || []).forEach(z => candle.attachPrimitive(new BandPrimitive(candle, z[0], z[1], 'rgba(38,166,154,0.10)')));
    (OV.resistencias || []).forEach(z => candle.attachPrimitive(new BandPrimitive(candle, z[0], z[1], 'rgba(239,83,80,0.10)')));
    // Zona de entrada: banda azul preenchida + bordas pontilhadas (createPriceLine azul).
    if (OV.entrada) {{
      candle.attachPrimitive(new BandPrimitive(candle, OV.entrada[0], OV.entrada[1], 'rgba(41,98,255,0.18)'));
      candle.createPriceLine({{ price: OV.entrada[0], color: '#2962ff', lineWidth: 1, lineStyle: 3, axisLabelVisible: false, title: 'entrada' }});
      candle.createPriceLine({{ price: OV.entrada[1], color: '#2962ff', lineWidth: 1, lineStyle: 3, axisLabelVisible: false, title: '' }});
    }}
    // Stop / alvo: linhas rotuladas de estudo (copy neutra, gate SWING-02).
    if (OV.stop != null) candle.createPriceLine({{ price: OV.stop, color: '#ef5350', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'stop (estudo)' }});
    if (OV.alvo != null) candle.createPriceLine({{ price: OV.alvo, color: '#26a69a', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'alvo (estudo)' }});
    // Fibonacci: linhas pontilhadas roxas rotuladas.
    (OV.fib || []).forEach(fb => candle.createPriceLine({{ price: fb.preco, color: '#9467bd', lineWidth: 1, lineStyle: 3, axisLabelVisible: true, title: 'Fib ' + fb.nome }}));
    console.log('[lwc] overlays de nível OK');
  }} catch (e) {{
    console.error('[lwc] overlay de nível error', e);
  }}

  try {{
    // Padrões: 1 marker por pivô (cor por direção), neckline como LineSeries de 2 pontos
    // (simplificação honesta do MVP — reta inclinada da OCO fica deferida), alvo como priceLine
    // "projeção de estudo". Copy NEUTRA (gate SWING-02); markers ordenados por time (crescente).
    const allMarkers = [];
    (OV.padroes || []).forEach(pd => {{
      (pd.pivos || []).forEach(pv => allMarkers.push({{
        time: pv.time, position: pd.alta ? 'belowBar' : 'aboveBar',
        color: pd.cor, shape: 'circle', text: 'pivô · ' + pd.estado,
      }}));
      if (pd.neckline != null && pd.pivos && pd.pivos.length >= 2) {{
        const t0 = pd.pivos[0].time, t1 = pd.pivos[pd.pivos.length - 1].time;
        if (t0 !== t1) {{
          const nl = chart.addSeries(LineSeries, {{
            color: pd.cor, lineWidth: 1, lineStyle: pd.confirmado ? 0 : 2,
            lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false,
          }});
          nl.setData([{{ time: t0, value: pd.neckline }}, {{ time: t1, value: pd.neckline }}]);
        }}
      }}
      if (pd.alvo != null) candle.createPriceLine({{ price: pd.alvo, color: pd.cor, lineWidth: 1, lineStyle: 3, axisLabelVisible: true, title: 'alvo (projeção de estudo)' }});
    }});
    if (allMarkers.length && createSeriesMarkers) {{
      allMarkers.sort((a, b) => (a.time > b.time ? 1 : a.time < b.time ? -1 : 0));
      createSeriesMarkers(candle, allMarkers);
    }}
    console.log('[lwc] markers de padrão OK');
  }} catch (e) {{
    console.error('[lwc] markers de padrão error', e);
  }}

  // LWC-03 — persistência de range entre reruns do Streamlit. `components.html` re-renderiza
  // o iframe a cada rerun (togglar overlay / auto-refresh), o que resetaria o zoom p/ fitContent.
  // Como a ponte é unidirecional (Python→JS), a persistência é CLIENT-SIDE via localStorage por
  // par (ticker, timeframe). Robustez OBRIGATÓRIA: o iframe pode ter origem opaca/sandbox e QUALQUER
  // acesso a localStorage pode lançar SecurityError — cada acesso vai em try/catch INDEPENDENTE p/
  // o candle SEMPRE renderizar (best-effort; a renderização nunca depende da persistência).
  const RANGE_KEY = {range_key_json};
  try {{
    const saved = window.localStorage.getItem(RANGE_KEY);
    if (saved) {{
      chart.timeScale().setVisibleLogicalRange(JSON.parse(saved));
    }} else {{
      chart.timeScale().fitContent();
    }}
  }} catch (e) {{
    chart.timeScale().fitContent();  // fallback: SecurityError não impede o candle de renderizar
  }}
  chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {{
    if (!range) return;
    try {{
      window.localStorage.setItem(RANGE_KEY, JSON.stringify(range));
    }} catch (e) {{
      console.log('[lwc] localStorage indisponível');
    }}
  }});

  new ResizeObserver(() => chart.applyOptions({{ width: el.clientWidth }})).observe(el);
  }} catch (e) {{
    console.error('[lwc] init error', e);
    el.innerHTML = '<div style="padding:24px;color:#d1d4dc;font:14px system-ui,sans-serif">'
      + 'Não foi possível carregar o gráfico interativo (Lightweight Charts). '
      + 'Verifique a conexão de rede/CDN — a vista <b>Plotly</b> continua disponível.</div>';
  }}
</script>
"""
    components.html(html, height=580)


# --------------------------------------------------------------------------- #
st.title("Analista de Ações de Dividendos")
st.caption("Análise fundamentalista de ações de dividendos da B3 · "
           "dados grátis: CVM + Yahoo + Banco Central")


def _render_metodologia() -> None:
    """Página 'velada' de metodologia e referências — acessada só pelo link do rodapé.

    Concentra toda a atribuição bibliográfica que antes ficava espalhada na interface,
    em linguagem descritiva/educacional (nunca recomendação — CVM Res. 19/20)."""
    if st.button("← Voltar ao app"):
        st.query_params.clear()
        st.rerun()
    st.header("Metodologia e referências")
    st.markdown(
        "Esta ferramenta descreve, de forma **educacional**, uma metodologia de análise "
        "fundamentalista de ações pagadoras de dividendos. Ela **não emite recomendação de "
        "compra ou venda** nem consultoria/análise de valores mobiliários (CVM Res. 19/20): "
        "apresenta cálculos e critérios para o usuário estudar e decidir por conta própria.\n\n"
        "### O fluxo da análise\n"
        "1. **Garimpo (BSD)** — filtra várias empresas por estabilidade e segurança dos dividendos.\n"
        "2. **Ranking por múltiplos** — ordena candidatas e estima um preço-alvo por regressão.\n"
        "3. **Análise a fundo** — valuation por Desconto de Dividendos (DDM), múltiplos e fundamentos.\n"
        "4. **Timing técnico (consultivo)** — indicadores de preço, sempre subordinados ao fundamento.\n\n"
        "### Fundamentação e referências\n"
        "A metodologia central segue o livro **_O Investidor em Ações de Dividendos_** "
        "(Orleans Martins & Felipe Pontes) — do garimpo de empresas ao valuation por desconto de "
        "dividendos. O mapeamento por tema:\n\n"
        "- **Múltiplos** (ML, ROE, P/L, EY, Payout, DY) — Cap. 10.\n"
        "- **Ranking por múltiplos + preço-alvo** (padronização e regressão P/L) — Cap. 11–12.\n"
        "- **Valuation por Desconto de Dividendos** (Gordon e modelo H, sensibilidade) — Cap. 13–17.\n"
        "- **Crescimento e custo de capital** (g e Ke pelo CAPM) — Cap. 14/16.\n\n"
        "Referências clássicas complementares, de domínio público, usadas como lentes de estudo:\n\n"
        "- **Preço-justo de Benjamin Graham** — raiz do produto de LPA, VPA e um fator fixo.\n"
        "- **Preço-teto de Décio Bazin** — DPA médio dividido por um dividend yield mínimo.\n"
        "- **BSD — Big, Safe Dividend** (Charles Carlson) — nota 0–100 de estabilidade dos dividendos; "
        "corte de referência acima de 80.\n\n"
        "### Fontes de dados (todas gratuitas e públicas)\n"
        "- **CVM** — Dados Abertos (DFP): fundamentos de até 10 anos (lucro, patrimônio, caixa, receita, dívida).\n"
        "- **Yahoo Finance** — preços, dividendos, número de ações e beta.\n"
        "- **Banco Central** — API SGS: Selic e IPCA.\n\n"
        "Os números podem conter erros ou dados desatualizados; rentabilidade passada não garante "
        "resultados futuros. Verifique sempre na fonte primária (CVM/RI) antes de decidir."
    )
    st.caption("Uso educacional. Não é recomendação de investimento (CVM Res. 19/20).")


# A página de metodologia é acessada apenas pelo link discreto do rodapé (?p=metodologia).
if st.query_params.get("p") == "metodologia":
    _render_metodologia()
    st.stop()

modo = st.sidebar.radio(
    "O que você quer fazer?",
    ["Início",  # 1º item → vira o default (radio stateless, sem key=/index=)
     "Analisar uma ação", "Garimpar ações (BSD)", "Ranking por múltiplos",
     "Comparar ações", "Análise técnica (timing)"],
    help=h("menu"),
)
st.sidebar.markdown("---")
st.sidebar.metric("Selic (piso do dividend yield)", fmt_pct(selic_atual()), help=h("selic"))
st.sidebar.caption(f"Janela: {N_ANOS} anos · até {ANO_BASE} (quando já divulgado na CVM)")

st.sidebar.markdown("---")
st.sidebar.caption(
    "**Aviso.** Ferramenta de apoio à análise, de caráter educacional. "
    "**Não é recomendação de compra ou venda** nem consultoria/análise de valores "
    "mobiliários (CVM Res. 19/20). Os números podem conter erros ou dados desatualizados; "
    "rentabilidade passada não garante resultados futuros. Toda decisão de investimento é "
    "de responsabilidade exclusiva do usuário — verifique os dados na fonte (CVM/RI) antes de decidir."
)

st.sidebar.markdown("---")
st.sidebar.link_button("Sair", LOGOUT_URL, use_container_width=True)


# =========================================================================== #
# 0) INÍCIO (Home — landing default: watchlist + notícias)
# =========================================================================== #
_WATCHLIST_KEY = "watchlist_v18"  # namespace próprio no localStorage (Pitfall 7: não colidir c/ LWC-03)


@st.cache_data(show_spinner=False, ttl=45)
def _cotacoes(tickers: tuple):
    """Wrapper de cache PROCESS-GLOBAL do fetch de cotações (D-05) — TTL 45s.

    Garante 1 chamada externa por conjunto de tickers por TTL, independente do nº de
    usuários e dos reruns do fragment (run_every≈TTL). A chave DEVE ser hashável →
    sempre chamado com `tuple(sorted(...))`, NUNCA list. Nunca `st.cache_data.clear()`
    global (apagaria o cache de montar/selic_atual/rf_capm da aba Analisar — D-08)."""
    from analista.core import home_feed  # import tardio: isola o módulo
    return home_feed.cotacoes(tickers)


@st.cache_data(show_spinner=False, ttl=600)
def _noticias():
    """Wrapper de cache PROCESS-GLOBAL do feed RSS (D-05) — TTL 600s (~10min).

    Garante ~1 hit por feed por intervalo, independente do nº de usuários e dos
    reruns do fragment (run_every≈TTL) — o porteiro real das fontes (Pitfall 3:
    InfoMoney throttla). Sem argumentos → chave de cache única e process-global.
    NUNCA `st.cache_data.clear()` global (apagaria montar/selic da aba Analisar — D-08)."""
    from analista.core import home_feed  # import tardio: isola feedparser (firewall D-06)
    return home_feed.noticias()


def _watchlist_ls():
    """Instância do bridge streamlit-local-storage (A2, plano 01) ou None se indisponível.

    Bloqueia só no 1º load da sessão (handshake getAll do browser); depois lê do
    session_state interno. CADA acesso a jusante vai em try/except INDEPENDENTE — a
    página SEMPRE renderiza mesmo com SecurityError (iframe sandbox/anônima — Pitfall 4/
    LWC-03); o fallback é o session_state semeado pelos defaults."""
    try:
        from streamlit_local_storage import LocalStorage
        return LocalStorage()
    except Exception:
        return None


def _seed_watchlist(ls):
    """Semeia st.session_state['watchlist'] no 1º load: localStorage se houver, senão defaults."""
    from analista.core import home_feed
    if "watchlist" in st.session_state:
        return
    seed = list(home_feed.DEFAULT_WATCHLIST)
    if ls is not None:
        try:
            import json
            salvo = ls.getItem(_WATCHLIST_KEY)
            if isinstance(salvo, str) and salvo.strip():
                validos = [home_feed.validar_ticker(t) for t in json.loads(salvo)]
                validos = [t for t in validos if t]
                if validos:
                    seed = validos[: home_feed.MAX_WATCHLIST]
        except Exception:
            pass  # storage indisponível/corrompido → cai nos defaults
    st.session_state["watchlist"] = seed


def _persistir_watchlist(ls):
    """Escreve a watchlist atual no localStorage (best-effort; nunca quebra o render)."""
    if ls is None:
        return
    try:
        import json
        ls.setItem(_WATCHLIST_KEY, json.dumps(st.session_state["watchlist"]), key="wl_set")
    except Exception:
        pass


def render_home():
    """Landing default (HOME-01). Camada fina, read-only, sem recálculo de método.

    Watchlist real (cotação + variação do dia auto-atualizável via cache compartilhado
    + editor persistido em localStorage) e feed de notícias real (RSS InfoMoney +
    Google News com render seguro). O contrato de dados vive em `analista.core.home_feed`
    (never-raise, firewall D-06)."""
    from analista.core import home_feed

    st.subheader("Início — seu painel de acompanhamento")
    st.caption("Cotações da sua watchlist e notícias do mercado, num só lugar. "
               "Os menus ao lado continuam disponíveis.")

    st.markdown("### Minha watchlist")

    ls = _watchlist_ls()
    _seed_watchlist(ls)
    wl = st.session_state["watchlist"]

    # --- Editor: add (valida + teto) e remove — FORA do fragment (Pitfall 5: mexer num
    #     widget fora dispara rerun full e re-decora o fragment). Sem st.rerun() explícito:
    #     o clique já dispara o rerun natural e o componente de setItem renderiza no caminho.
    with st.expander("Editar watchlist", expanded=False):
        ca, cb = st.columns([3, 1])
        novo = ca.text_input("Adicionar ticker", key="wl_novo", placeholder="ex.: PETR4",
                             label_visibility="collapsed")
        if cb.button("Adicionar", use_container_width=True):
            t = home_feed.validar_ticker(novo)
            if t is None:
                st.warning("Ticker inválido. Use 4–6 letras/números (ex.: BBSE3).")
            elif t in wl:
                st.info(f"{t} já está na watchlist.")
            elif len(wl) >= home_feed.MAX_WATCHLIST:
                st.warning(f"Watchlist cheia (máximo {home_feed.MAX_WATCHLIST}). Remova um ticker antes.")
            else:
                wl.append(t)
                st.session_state["watchlist"] = wl
                _persistir_watchlist(ls)

        if wl:
            st.caption("Remover:")
            cols_rm = st.columns(len(wl))
            for i, t in enumerate(wl):
                if cols_rm[i].button(f"✕ {t}", key=f"wl_rm_{t}", use_container_width=True):
                    st.session_state["watchlist"] = [x for x in wl if x != t]
                    _persistir_watchlist(ls)
        st.caption(f"Até {home_feed.MAX_WATCHLIST} tickers. Persiste no navegador (best-effort).")

    # --- Fragment de auto-refresh (~45s): re-roda SÓ este bloco; o TTL=45s do wrapper
    #     cacheado é o porteiro real do Yahoo (1 chamada por conjunto por intervalo — D-05).
    @st.fragment(run_every=45)
    def _render_watchlist():
        tickers = tuple(sorted(st.session_state["watchlist"]))
        dados = _cotacoes(tickers)
        if not dados:
            st.info("Sua watchlist está vazia. Use **Editar watchlist** para adicionar tickers.")
        else:
            cols = st.columns(len(dados))
            for col, item in zip(cols, dados):
                if item["ok"]:
                    col.metric(
                        label=item["ticker"],
                        value=esc_md(fmt_rs(item["preco"])),
                        delta=f"{item['pct'] * 100:+.2f}%",  # delta_color normal: + verde / − vermelho
                    )
                else:
                    col.metric(label=item["ticker"], value="—")
        # Selo de atraso SEMPRE visível: honestidade sobre o best-effort (D-04).
        st.caption("Cotações Yahoo com ~15min de atraso (best-effort) · variação do dia.")

    _render_watchlist()

    st.markdown("### Notícias do mercado")

    # --- Fragment de auto-refresh (~10min): re-roda SÓ este bloco; o TTL=600s do
    #     wrapper cacheado é o porteiro real das fontes RSS (D-05 / Pitfall 3).
    @st.fragment(run_every=600)
    def _render_noticias():
        itens = _noticias()
        if not itens:
            # Estado vazio (todas as fontes caíram): avisa sem quebrar (never-raise a jusante).
            st.info("Sem notícias no momento. As fontes públicas podem estar indisponíveis — "
                    "tente novamente em alguns minutos.")
            return
        # Render SEGURO (V7 / T-18-06, RSS untrusted): título como TEXTO via st.markdown
        # (sem unsafe_allow_html; nunca components.html com conteúdo do feed). Só manchete
        # + trecho + link — NUNCA o texto completo (zona segura de copyright).
        for it in itens[:15]:
            st.markdown(f"**{esc_md(it['titulo'])}**")
            quando = it.get("quando")
            selo = f"{it['fonte']} · {quando:%d/%m %H:%M}" if quando else it["fonte"]
            st.caption(selo)
            # Submanchete só quando acrescenta (Google News ecoa o título → suprime a redundância).
            resumo = it["resumo"]
            t_low, r_low = it["titulo"].strip().lower(), resumo.strip().lower()
            if resumo and r_low != t_low and r_low not in t_low and t_low not in r_low:
                st.write(esc_md(resumo))
            # Link só se https:// (T-18-07): st.link_button monta âncora nativa segura
            # (rel seguro, sem tabnabbing — T-18-08), abre o site original em nova aba.
            if it["link"].startswith("https://"):
                st.link_button("Abrir no site ↗", it["link"])
            st.divider()
        st.caption("Manchetes de fontes públicas (RSS) · atualiza a cada ~10min · "
                   "o clique abre o site original da fonte.")

    _render_noticias()


if modo.startswith("Início"):
    render_home()


# =========================================================================== #
# 1) ANALISAR UMA AÇÃO
# =========================================================================== #
if modo.startswith("Analisar"):
    st.subheader("Analisar uma ação a fundo")
    col1, col2 = st.columns([3, 1])
    ticker = col1.text_input("Ticker da B3", value="TAEE11", placeholder="ex.: ITUB4, EGIE3, TAEE11",
                             help=h("ticker")).strip().upper()
    rodar = col2.button("Analisar", type="primary", use_container_width=True)

    # Persiste o ticker analisado em session_state em vez de gatear a análise no retorno
    # EFÊMERO do botão. `rodar` só é True no rerun do clique; ao mexer num toggle técnico o
    # Streamlit reexecuta com rodar=False e o bloco inteiro (veredito + gráfico + controles)
    # sumiria — quebrando o UI-03. Gatear pelo ticker ativo deixa o toggle redesenhar o
    # gráfico sem recoleta (montar() é @st.cache_data → barato nos reruns).
    if rodar and ticker:
        st.session_state["analise_ticker"] = ticker

    ticker_ativo = st.session_state.get("analise_ticker")
    if ticker_ativo:
        # UX (quick-260710-u1f): feedback no CORPO da página durante os ~35s de coleta.
        # st.status mostra o passo atual (CVM/Yahoo → BCB → valuation) em vez de deixar a
        # tela parada com só o ícone do Streamlit no canto. Apenas apresentação — nenhum
        # cálculo do método muda; as chamadas são as mesmas, só embrulhadas no status.
        with st.status(f"Analisando {ticker_ativo}… (pode levar ~30s)", expanded=True) as _status:
            st.write("Baixando fundamentos (CVM) e preço/dividendos (Yahoo)…")
            c = montar(ticker_ativo, ANO_BASE, N_ANOS)
            _dados_ok = c is not None and c.anos
            if _dados_ok:
                st.write("Selic/IPCA (BCB) para o custo de capital…")
                # FIX-03: injeta o rf do CAPM em CFG antes da engine. Rf = Selic through-the-cycle
                # (média ~10 anos), não a spot — numa perpetuidade a taxa reflete o juro de LP (a
                # sidebar/corte de DY seguem na Selic spot via selic_atual()). @st.cache_data
                # garante UMA chamada de rede por execução. app.py segue read-only.
                CFG["capm"]["rf_local"] = rf_capm(
                    CFG["capm"]["selic_fallback"], CFG["capm"].get("rf_ciclo_anos", 10)
                )
                st.write("Calculando valuation (DDM + múltiplos)…")
                a = report.analisar_acao(c, CFG)
                _status.update(label=f"Análise de {ticker_ativo} concluída",
                               state="complete", expanded=False)
            else:
                _status.update(label=f"Sem dados suficientes para {ticker_ativo}",
                               state="error", expanded=False)

        if not _dados_ok:
            st.error(f"Não encontrei dados suficientes para {ticker_ativo}. "
                     "Confira o ticker ou adicione o mapeamento em data/ticker_map.json.")
        else:
            st.markdown(f"### {a.ticker} — {a.nome}")
            st.caption(f"Setor: {a.setor or '—'}  ·  Estágio: {a.estagio}")
            st.caption(f"Arquétipo: {esc_md(a.arquetipo or '—')} → motor {esc_md(a.motor or '—')}")

            # Veredito colorido
            v = a.veredito or "Indeterminado"
            if v.startswith("SUBAVALIADA"):
                st.success(esc_md(v))
            elif v.startswith("SOBREAVALIADA"):
                st.error(esc_md(v))
            else:
                st.warning(esc_md(v))

            # ----------------------------------------------------------------- #
            # Sinais do veredito honesto (Fase 3 — VER-01/ENS-01/SAN-01/VER-02) —
            # READ-ONLY: só LÊ campos já derivados na engine (a.san01_reetiquetado /
            # a.arquetipo_incerto / a.divergencia_*), zero recálculo. Paridade de copy
            # com relatorio_markdown (report.py). Descritivo, nunca recomendação.
            # ----------------------------------------------------------------- #
            # Guarda-corpo anti-aberração SAN-01 (03-02): o veredito "evitar" foi
            # reetiquetado — o número é do motor primário do arquétipo; o DDM de estágio
            # único é conservador demais para este perfil (reetiqueta, não supressão).
            if getattr(a, "san01_reetiquetado", False):
                st.info(
                    "**Guarda-corpo anti-aberração (SAN-01):** veredito reetiquetado — a "
                    "referência primária é o motor do arquétipo (números abaixo); o DDM de "
                    "estágio único é conservador demais para este perfil."
                )

            # Classificação incerta (VER-02 / 03-03, caso-fronteira): conflito real de
            # sinais → roda o motor de cada arquétipo candidato e assume a dúvida (range +
            # bandeira "classificação incerta entre X e Y"), em vez de cravar um selo.
            if getattr(a, "arquetipo_incerto", False):
                if a.candidatos_intrinsecos:
                    _linhas = "\n".join(
                        f"- {esc_md(str(cand))}: {esc_md(fmt_rs(val))} "
                        f"(motor do arquétipo {esc_md(str(cand))})"
                        for cand, val in a.candidatos_intrinsecos
                    )
                    _primeiro = a.candidatos_intrinsecos[0][0]
                    _ultimo = a.candidatos_intrinsecos[-1][0]
                    _txt = (
                        "**Classificação incerta (caso-fronteira):**\n\n"
                        f"{_linhas}\n\n"
                        f"Classificação incerta entre {esc_md(str(_primeiro))} e "
                        f"{esc_md(str(_ultimo))} — a ferramenta assume a dúvida em vez de "
                        "cravar um selo."
                    )
                    if a.veredito_range is not None:
                        _menor, _maior = a.veredito_range
                        _txt += (
                            "\n\nRange do intrínseco conforme o arquétipo assumido: "
                            f"{esc_md(fmt_rs(_menor))} – {esc_md(fmt_rs(_maior))}."
                        )
                    st.warning(_txt)
                else:
                    st.warning(
                        "**Classificação incerta (caso-fronteira):** os motores dos "
                        "arquétipos candidatos não estimaram preço-alvo confiável."
                    )

            # Bandeira de divergência (ENS-01 / 03-01): motor × contraponto DDM discordam
            # além do limiar (2×) → EXIBIR os dois números + a hipótese curada. Divergência
            # é informação mostrada, nunca escondida cravando o pior número.
            if getattr(a, "divergencia_ativa", False):
                _razao = fmt_num(a.divergencia_razao, 1) if a.divergencia_razao is not None else "—"
                _msg = (
                    f"**Bandeira de divergência:** as lentes divergem ~{_razao}×: "
                    f"**{esc_md(a.motor_rotulo or a.motor or '—')} "
                    f"{esc_md(fmt_rs(a.intrinseco_motor))}** × DDM (lente conservadora) "
                    f"{esc_md(fmt_rs(a.contraponto_valor))}."
                )
                if a.divergencia_hipotese:
                    _msg += f"\n\nHipótese: {esc_md(a.divergencia_hipotese)}"
                st.warning(_msg)

            # ----------------------------------------------------------------- #
            # Selo de Sustentabilidade (Fase 20 / SELO-03) — READ-ONLY: só LÊ os
            # campos já derivados na engine (a.selo), zero fórmula/recálculo aqui.
            # Destaque perto do veredito + rótulo do quadrante (qualidade × preço).
            # ----------------------------------------------------------------- #
            if a.selo is not None and a.selo.cor is not None:
                badge = presentation.selo_badge(
                    a.selo.cor, a.selo.rotulo, a.selo.qualidade, a.selo.verificar
                )
                st.markdown(f"### {esc_md(badge)}")
                st.caption("Selo = qualidade do dividendo (BSD) × preço (DDM). "
                           "Descreve a combinação, não é recomendação.")
                if a.selo.verificar:
                    st.warning(
                        "**Verificar dados:** o veredito de preço saiu como VERIFICAR "
                        "(payout ou DY fora do razoável). O selo mostra só a qualidade do "
                        "dividendo — o cruzamento com preço fica suspenso até revisar os dados."
                    )

            # Métricas principais — intervalo intrínseco vem do cálculo único do veredito (WR-07)
            intervalo = f"{fmt_rs(a.vmin)} – {fmt_rs(a.vmax)}" if a.vmin is not None and a.vmax is not None else "—"
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Preço atual", esc_md(fmt_rs(a.preco_atual)), help=h("preco"))
            # Rótulo honesto do intrínseco (T-0304-01): quando o motor do arquétipo NÃO é o
            # DDM (RIM/normalizado/DCF/NAV), a faixa vem do motor primário — não chamar o
            # motor de "DDM" (enganaria o usuário). "Intrínseco (DDM)" só quando motor==ddm.
            _motor = a.motor or "ddm"
            # CR-01: o rótulo do motor só é honesto quando a banda vem DE FATO do motor
            # (banda_do_motor True). Se o motor degradou e a faixa exibida é 100% do DDM,
            # rotular com o nome do motor enganaria o usuário → cai para "Intrínseco (DDM)".
            _label_intr = (
                "Intrínseco (DDM)"
                if _motor == "ddm" or not getattr(a, "banda_do_motor", False)
                else f"Intrínseco ({a.motor_rotulo or _motor})"
            )
            m2.metric(_label_intr, esc_md(intervalo), help=h("valor_intrinseco"))
            hdr = presentation.header_dy(a.multiplos.get("DY rec."), a.multiplos.get("DY"))
            m3.metric(hdr["label"], hdr["value"], delta=hdr["delta"],
                      delta_color="off", help=hdr["help"])
            m4.metric("ROE", fmt_pct(a.multiplos.get("ROE")), help=h("roe"))
            m5.metric("Ke (custo)", fmt_pct(a.ke), help=h("ke"))

            # Guarda-corpo do DDM (Achado 2 / SAN-01): quando a faixa saiu negativa/zero a
            # engine já zerou vmin/vmax (Intrínseco cai em "—"). Aqui só a nota honesta do
            # porquê — nunca exibimos faixa negativa/degenerada como preço-alvo.
            if getattr(a, "ddm_inaplicavel", False):
                st.caption(
                    "DDM estruturalmente inaplicável a este perfil (payout baixo / alto capex "
                    "ou lucro negativo): a faixa por dividendos ficou negativa ou zero e NÃO é "
                    "preço-alvo — por isso o Intrínseco (DDM) não é exibido."
                )

            if a.preco_atual is None:
                st.warning(
                    "Preço atual indisponível agora (fonte Yahoo instável). Os fundamentos e o "
                    "valor intrínseco (DDM, dados CVM) abaixo seguem válidos — só a comparação de "
                    "preço/veredito fica suspensa até o preço voltar."
                )

            if a.alertas:
                for al in a.alertas:
                    st.warning(esc_md(al))

            # ----------------------------------------------------------------- #
            # Lentes de referência (Fase 19) — camada fina READ-ONLY, além do DDM.
            # app.py só LÊ a engine (lentes.*); nenhuma fórmula/recálculo na view.
            # Copy de estudo, jamais recomendação (VAL-01/VAL-02).
            # ----------------------------------------------------------------- #
            st.markdown("#### Lentes de referência (além do DDM)")
            st.caption(
                "Fórmulas clássicas complementares — o valor intrínseco (DDM) acima segue "
                "sendo a análise principal. São referências de estudo, não recomendações."
            )
            lente_graham, lente_bazin = st.columns(2)
            with lente_graham:
                _ult = c.ultimo_ano()
                _vpa = lentes.vpa(c.patrimonio_liquido.get(_ult), c.num_acoes.get(_ult))
                graham = lentes.preco_justo_graham(c.lpa_valuation(), _vpa)
                if graham is not None:
                    st.metric(
                        "Preço-Justo (Graham)", esc_md(fmt_rs(graham)),
                        delta=fmt_pct(lentes.upside(graham, a.preco_atual)) + " vs preço",
                        delta_color="off",
                    )
                    st.caption("Referência clássica de Benjamin Graham (raiz do produto de LPA, VPA e um fator fixo).")
                else:
                    st.metric("Preço-Justo (Graham)", "indisponível")
                    st.caption("A fórmula de Graham não vale para empresa sem lucro/PL positivo.")
            with lente_bazin:
                _dpas = [c.dpa(ano) for ano in c.anos_ordenados()]
                _dpa_med = lentes.dpa_medio(_dpas, n=5)
                bazin = lentes.preco_teto_bazin(_dpa_med)
                if bazin is not None:
                    st.metric(
                        "Preço-Teto (Bazin)", esc_md(fmt_rs(bazin)),
                        delta=fmt_pct(lentes.upside(bazin, a.preco_atual)) + " vs preço",
                        delta_color="off",
                    )
                    st.caption("DPA médio de até 5 anos ÷ DY-mínimo de 6%.")
                else:
                    st.metric("Preço-Teto (Bazin)", "indisponível")
                    st.caption("Só vale para boas pagadoras de dividendos (DPA médio positivo).")

            # RET-01 — "Quanto teria rendido" (Adj Close 5a: já embute dividendos reinvestidos).
            # Read-only: só LÊ lentes.retorno_periodo sobre c.serie_precos_ajustada (Plano 02).
            # Janela None (histórico insuficiente) é OCULTADA; ambas None → caption neutra.
            _r1 = lentes.retorno_periodo(c.serie_precos_ajustada, anos=1)
            _r5 = lentes.retorno_periodo(c.serie_precos_ajustada, anos=5)
            if _r1 is not None or _r5 is not None:
                st.markdown("**Quanto R\\$ 1.000 teriam rendido** (com dividendos reinvestidos)")
                if _r1 is not None:
                    st.markdown(f"- R\\$ 1.000 há **1 ano** valeriam **{esc_md(fmt_rs(_r1))}** hoje.")
                if _r5 is not None:
                    st.markdown(f"- R\\$ 1.000 há **5 anos** valeriam **{esc_md(fmt_rs(_r5))}** hoje.")
                st.caption("Rentabilidade passada não garante retorno futuro.")
            else:
                st.caption("Histórico de preços insuficiente para o cálculo de rentabilidade.")

            # PEER-01 — Comparador de pares (contexto). Reusa o padrão do Ranking: text_input
            # editável + montar() por ticker (cache). PEER-01 é a única exceção à regra "zero
            # rede nova" (buscar pares não-cacheados dispara fetch, igual à aba Ranking hoje).
            # Só CONTEXTO: nunca ordena/recomenda; degrada em st.info neutro. Read-only.
            with st.expander("Comparador de pares (contexto)", expanded=False):
                st.caption(
                    "Compara múltiplos com pares do setor — apenas contexto, sem ranking nem "
                    "recomendação. Edite a lista (de preferência do mesmo setor)."
                )
                _pares_txt = st.text_input(
                    "Comparáveis", value="TAEE11, EGIE3, CMIG4, ALUP11, CPFE3",
                    key="pares_comparador",
                )
                _pares_tickers = [t.strip().upper() for t in _pares_txt.replace(",", " ").split() if t.strip()]
                if ticker_ativo not in _pares_tickers:
                    _pares_tickers.insert(0, ticker_ativo)
                _companies_pares = []
                for _t in _pares_tickers:
                    _cp = montar(_t, ANO_BASE, N_ANOS)
                    if _cp is not None and _cp.anos:
                        _companies_pares.append(_cp)
                _metricas_pares = [lentes.metricas_par(_cp) for _cp in _companies_pares]
                _tabela_pares = lentes.tabela_pares(_metricas_pares, ticker_ativo)
                if lentes.pares_suficientes(_tabela_pares):
                    _rows_pares = []
                    for p in _tabela_pares:
                        _vm = (
                            fmt_rs(p.valor_mercado / 1e9, casas=1) + " B"
                            if p.valor_mercado is not None else "—"
                        )
                        _rows_pares.append({
                            "Ticker": esc_md(("➤ " if p.alvo else "") + p.ticker),
                            "P/L": fmt_num(p.pl),
                            "P/VP": fmt_num(p.pvp),
                            "ROE": fmt_pct(p.roe),
                            "DY": fmt_pct(p.dy),
                            "Valor de Mercado": _vm,
                        })
                    st.dataframe(pd.DataFrame(_rows_pares), hide_index=True, use_container_width=True,
                                 column_config={
                                     "Ticker": st.column_config.Column("Ticker", help=h("ticker")),
                                     "P/L": st.column_config.Column("P/L", help=h("pl")),
                                     "P/VP": st.column_config.Column("P/VP", help=h("pvp")),
                                     "ROE": st.column_config.Column("ROE", help=h("roe")),
                                     "DY": st.column_config.Column("DY", help=h("dy")),
                                     "Valor de Mercado": st.column_config.Column("Valor de Mercado", help=h("valor_mercado"), width="medium"),
                                 })
                    st.caption("➤ marca o ticker analisado. Contexto de comparação — não é ranking nem recomendação.")
                else:
                    st.info("Pares insuficientes do mesmo setor para comparar.")

            # Gráfico de preço 5a + banda do valor intrínseco (DDM) — topo da aba, antes dos sub-tabs (D-03).
            # Reservamos o slot do gráfico AQUI (topo) com st.container() e só o PREENCHEMOS depois que os
            # controles abaixo rodarem: assim o render lê o st.session_state["tec_estado"] já atualizado pelos
            # widgets no MESMO rerun (UI-03 — toggle redesenha na hora, sem lag de um clique). Read-only.
            grafico_box = st.container()

            # Controles técnicos consultivos (UI-03/UI-05): os widgets SÓ capturam estado em
            # st.session_state["tec_estado"] (mesmas chaves de grafico.estado_padrao()); o gráfico
            # acima consome esse estado para desenhar overlays/subpainéis. app.py segue read-only.
            st.session_state.setdefault("tec_estado", grafico.estado_padrao())
            est = st.session_state["tec_estado"]
            with st.expander("Indicadores técnicos (consultivo)", expanded=False):
                st.caption(
                    "Consultivo — auxilia o *timing*. O veredito do método (acima) continua o decisório.",
                    help=h("tec_indicadores"),
                )
                ct, cc, cf, cm = st.columns(4)
                with ct:
                    st.markdown("**Tendência**", help=h("tec_mm"))
                    est["tendencia"]["on"] = st.toggle(
                        "Médias móveis", value=est["tendencia"]["on"], help=h("tec_mm"))
                    est["tendencia"]["tipo"] = st.radio(
                        "Tipo", ["sma", "ema"],
                        index=0 if est["tendencia"]["tipo"] == "sma" else 1,
                        format_func=str.upper, horizontal=True, help=h("tec_mm"))
                    est["tendencia"]["janelas"] = st.multiselect(
                        "Janelas", [20, 50, 200], default=est["tendencia"]["janelas"],
                        help=h("tec_cross"))
                with cc:
                    st.markdown("**Canais**", help=h("tec_donchian"))
                    est["canais"]["donchian_on"] = st.toggle(
                        "Donchian", value=est["canais"]["donchian_on"], help=h("tec_donchian"))
                    est["canais"]["donchian_janela"] = st.radio(
                        "Janela Donchian", [20, 55],
                        index=0 if est["canais"]["donchian_janela"] == 20 else 1,
                        horizontal=True, help=h("tec_donchian"))
                    est["canais"]["bollinger_on"] = st.toggle(
                        "Bollinger", value=est["canais"]["bollinger_on"], help=h("tec_bollinger"))
                with cf:
                    st.markdown("**Força**", help=h("tec_adx"))
                    est["forca"]["on"] = st.toggle(
                        "ADX", value=est["forca"]["on"], help=h("tec_adx"))
                with cm:
                    st.markdown("**Momentum**", help=h("tec_rsi"))
                    est["momentum"]["rsi_on"] = st.toggle(
                        "RSI", value=est["momentum"]["rsi_on"], help=h("tec_rsi"))
                    est["momentum"]["macd_on"] = st.toggle(
                        "MACD", value=est["momentum"]["macd_on"], help=h("tec_macd"))

            # Render do gráfico no slot reservado no topo, JÁ com o estado atualizado pelos controles
            # acima. make_subplots dinâmico: row 1 = preço + banda DDM + overlays ativos (UI-01);
            # rows seguintes = subpainéis SÓ dos osciladores ligados, montados a partir do SubpainelSpec
            # (série(s) + níveis de referência vindos do módulo puro — app.py não mapeia nome→série nem
            # hardcoda 20/25, 30/70, 0). Read-only: lê a.sinais, não recomputa indicador.
            with grafico_box:
                st.markdown("**Evolução do preço (5 anos) vs. valor intrínseco**", help=h("valor_intrinseco"))
                serie = c.serie_precos
                if serie is None or len(serie) == 0:
                    # D-05/GRAF-03: série indisponível → aviso sem quebrar a aba (espelha o aviso de preço atual)
                    st.info(
                        "Gráfico de preço indisponível agora (fonte Yahoo instável). Os fundamentos e o "
                        "valor intrínseco (DDM, dados CVM) abaixo seguem válidos."
                    )
                else:
                    estado = st.session_state["tec_estado"]
                    # Técnico OFF/degradado ⇒ specs/overlays/marcadores vazios ⇒ só o painel de preço.
                    if grafico.leitura_tecnica_disponivel(a.sinais):
                        overlays = grafico.overlays_preco(estado, a.sinais)
                        specs = grafico.subpaineis_ativos(estado, a.sinais)
                        # Datas EXATAS dos eventos (UI-04): lê a.sinais + close split-adjusted; sem recompute.
                        marcadores = grafico.marcadores_eventos(a.sinais, a.sinais.close)
                    else:
                        overlays, specs, marcadores = [], [], []
                    layout = grafico.layout_subplots(len(specs))
                    fig = make_subplots(
                        rows=layout["rows"], cols=1, shared_xaxes=True,
                        row_heights=layout["row_heights"], vertical_spacing=0.03,
                    )
                    # Row 1 — preço nominal (mesmo trace/estilo do gráfico atual; alinha com a banda DDM)
                    fig.add_trace(go.Scatter(
                        x=serie.index, y=serie.values, mode="lines", name="Preço",
                        line=dict(color="#1f77b4", width=2),
                        hovertemplate="%{x|%d/%m/%Y}<br>R$ %{y:.2f}<extra></extra>",
                    ), row=1, col=1)
                    # D-01/D-02/D-06: banda horizontal plana entre vmin e vmax, só se o DDM calculou
                    if a.vmin is not None and a.vmax is not None:
                        fig.add_hrect(
                            y0=a.vmin, y1=a.vmax, line_width=0, fillcolor="green", opacity=0.12,
                            annotation_text="Valor intrínseco (DDM)", annotation_position="top right",
                            row=1, col=1,
                        )
                    # Overlays (MMs/Donchian/Bollinger) no eixo de preço — série + estilo vêm do OverlaySpec
                    for ov in overlays:
                        fig.add_trace(go.Scatter(
                            x=ov.serie.index, y=ov.serie.values, mode="lines", name=ov.nome,
                            line=dict(ov.estilo),
                            hovertemplate=f"{ov.nome}<br>%{{x|%d/%m/%Y}}<br>R$ %{{y:.2f}}<extra></extra>",
                        ), row=1, col=1)
                    # Marcadores de evento no row do preço (UI-04): triângulo-up verde p/ golden_cross/nova_maxima,
                    # triângulo-down vermelho p/ death_cross/perda_minima; hover nomeia o evento e a data. Lista
                    # vazia (degradação) ⇒ nenhum marcador, sem exceção.
                    _ESTILO_MARCADOR = {
                        "golden_cross": ("triangle-up", "#2ca02c"),
                        "nova_maxima": ("triangle-up", "#2ca02c"),
                        "death_cross": ("triangle-down", "#d62728"),
                        "perda_minima": ("triangle-down", "#d62728"),
                    }
                    for m in marcadores:
                        simbolo, cor = _ESTILO_MARCADOR.get(m.tipo, ("circle", "#888888"))
                        fig.add_trace(go.Scatter(
                            x=[m.data], y=[m.y], mode="markers", showlegend=False,
                            marker=dict(symbol=simbolo, color=cor, size=11,
                                        line=dict(width=1, color="white")),
                            hovertext=[m.rotulo],
                            hovertemplate="%{hovertext}<br>%{x|%d/%m/%Y}<br>R$ %{y:.2f}<extra></extra>",
                        ), row=1, col=1)
                    # Subpainéis dos osciladores ativos — série(s) + linhas de referência do SubpainelSpec
                    for i, spec in enumerate(specs):
                        r = i + 2
                        for rotulo, s in spec.series:
                            # AUD-IND-01 (plot): o histograma do MACD é (MACD − Sinal) e deve ser
                            # BARRAS (verde ≥0 / vermelho <0), não uma linha — como linha no mesmo
                            # eixo das linhas MACD/Sinal ele somia e parecia "reto".
                            if rotulo == "Histograma":
                                fig.add_trace(go.Bar(
                                    x=s.index, y=s.values, name=rotulo,
                                    marker_color=["#2ca02c" if (v is not None and v >= 0) else "#d62728"
                                                  for v in s.values],
                                    hovertemplate=f"{rotulo}<br>%{{x|%d/%m/%Y}}<br>%{{y:.2f}}<extra></extra>",
                                ), row=r, col=1)
                                continue
                            fig.add_trace(go.Scatter(
                                x=s.index, y=s.values, mode="lines", name=rotulo,
                                hovertemplate=f"{rotulo}<br>%{{x|%d/%m/%Y}}<br>%{{y:.2f}}<extra></extra>",
                            ), row=r, col=1)
                        for ref in spec.referencias:
                            fig.add_hline(y=ref, line_width=1, line_dash="dot",
                                          line_color="#aaaaaa", row=r, col=1)
                        fig.update_yaxes(title_text=spec.nome.upper(), row=r, col=1)
                    # Botões de período (range selector nativo do Plotly) na linha do preço
                    fig.update_xaxes(rangeselector=dict(
                        buttons=[
                            dict(count=30, label="30D", step="day", stepmode="backward"),
                            dict(count=6, label="6M", step="month", stepmode="backward"),
                            dict(count=1, label="1A", step="year", stepmode="backward"),
                            dict(step="all", label="5A"),
                        ],
                        activecolor="#1f77b4", x=0, y=1.12,
                    ), row=1, col=1)
                    fig.update_yaxes(title_text="R$", row=1, col=1)
                    fig.update_layout(
                        height=400 + 140 * len(specs), margin=dict(l=10, r=10, t=50, b=10),
                        xaxis_title=None, showlegend=bool(overlays or specs),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                    )
                    st.plotly_chart(fig, width="stretch")
                    # Legenda dos triângulos (quick-260710-u3g #7): os marcadores só tinham hover;
                    # aqui a legenda fixa nomeia o que cada cor representa. Sinais de timing,
                    # consultivos — nunca ordem de compra/venda (subordinados ao fundamento).
                    if marcadores:
                        st.caption(
                            "**Marcadores no gráfico** (sinais de *timing*, consultivos — nunca ordem): "
                            "▲ triângulo **verde** = fortalecimento da tendência "
                            "(*golden cross* MM50×MM200 ou rompimento da máxima de Donchian); "
                            "▼ triângulo **vermelho** = enfraquecimento "
                            "(*death cross* ou perda da mínima de Donchian). "
                            "Passe o mouse em cada marcador para ver o evento e a data.",
                            help=h("tec_indicadores"),
                        )

            # Enquadramento subordinado (UI-06): o veredito fundamentalista (acima) é o selo
            # decisório; a leitura técnica é CONSULTIVA e secundária — markdown/caption discreto,
            # nunca banner de veredito, voz de timing/reverificação (jamais "compre/venda").
            st.markdown("---")
            if grafico.leitura_tecnica_disponivel(a.sinais) and a.timing_resumo:
                st.markdown(f"**Timing (consultivo):** {esc_md(a.timing_resumo)}", help=h("tec_timing"))
                if a.matriz_leitura:                       # fundamento-primeiro (D-04)
                    st.markdown(esc_md(a.matriz_leitura))
                if a.alerta_reverificacao:                 # voz de reverificação, nunca venda
                    st.info(esc_md(a.alerta_reverificacao))
            else:
                # Degradação holística (Plan 01): timing_resumo vazio ⇒ sem leitura, sem quebrar a aba.
                st.caption("Leitura técnica indisponível — histórico insuficiente para os indicadores")

            # Sub-seções da análise — quick-260710-u2r: trocamos st.tabs por
            # st.segmented_control + render condicional. O st.tabs mantém as abas
            # inativas no DOM (display:none) e o Streamlit as mede com largura 0 na
            # 1ª pintura → os st.dataframe colapsam para a 1ª coluna por ~2s (achado #2)
            # e o st.bar_chart de Fundamentos aparecia só com o eixo "0" solto (achado #3).
            # Renderizando SÓ a seção ativa, nada é medido a largura 0: o flash e o "0"
            # órfão somem na raiz. A troca de seção dispara rerun, mas a análise é gateada
            # por session_state["analise_ticker"] (montar() é @st.cache_data), então o
            # resultado não some — mesmo padrão dos toggles técnicos abaixo. Só
            # apresentação: nomes, colunas e valores das tabelas seguem intactos.
            _secoes = ["Múltiplos & Crescimento", "Valuation (DDM)", "Fundamentos (10 anos)"]
            _aba = st.segmented_control(
                "Detalhes da análise", _secoes, default=_secoes[0],
                key="analise_aba", label_visibility="collapsed",
            ) or _secoes[0]

            if _aba == "Múltiplos & Crescimento":
                cma, cmb = st.columns(2)
                with cma:
                    st.markdown("**Múltiplos**", help=h("tab_multiplos"))
                    st.caption("Dois payouts: o cru do último ano e o sustentável usado no valuation (DDM).",
                               help=h("payout_dual"))
                    payout_ult = c.payout(c.ultimo_ano())  # CRU do último ano (paridade report.py L156)
                    payout_proj = c.payout_valuation()     # sustentável (mediana sem clamp) usado no DDM
                    rows = presentation.linhas_multiplos(a.multiplos, payout_ult, payout_proj)
                    st.dataframe(pd.DataFrame(rows, columns=["Múltiplo", "Valor"]),
                                 hide_index=True, use_container_width=True)
                    # UX (quick-260710-u3g #5): tabela transposta — o help= por coluna não pega o
                    # rótulo de LINHA, então o glossário das siglas fica alcançável neste expander.
                    with st.expander("O que cada sigla significa"):
                        st.markdown(h("tab_multiplos"))
                with cmb:
                    st.markdown("**Crescimento e custo de capital**", help=h("tab_crescimento"))
                    st.dataframe(pd.DataFrame([
                        ("g histórico (tendência log-linear)", fmt_pct(a.g_historico)),
                        ("g por fundamentos", fmt_pct(a.g_fundamentos)),
                        ("g alto adotado", fmt_pct(a.g_alto)),
                        ("g estável (perpetuidade)", fmt_pct(a.g_estavel)),
                        ("Beta", fmt_num(a.beta)),
                        ("Ke (CAPM)", fmt_pct(a.ke)),
                    ], columns=["Indicador", "Valor"]), hide_index=True, use_container_width=True)
                    # UX (quick-260710-u3g #5): idem — glossário das siglas de crescimento/Ke.
                    with st.expander("O que cada sigla significa"):
                        st.markdown(h("tab_crescimento"))

            elif _aba == "Valuation (DDM)":
                if a.ddm_constante and a.ddm_h:
                    st.markdown("**Valor intrínseco por Desconto de Dividendos**", help=h("tab_ddm"))
                    st.dataframe(pd.DataFrame([
                        ("Otimista (g constante)", fmt_rs(a.ddm_constante.valor_intrinseco),
                         fmt_rs(a.ddm_constante.vp_dividendos), fmt_rs(a.ddm_constante.vp_residual)),
                        ("Conservador (modelo H)", fmt_rs(a.ddm_h.valor_intrinseco),
                         fmt_rs(a.ddm_h.vp_dividendos), fmt_rs(a.ddm_h.vp_residual)),
                    ], columns=["Cenário", "Valor intrínseco", "VP dividendos", "VP residual"]),
                        hide_index=True, use_container_width=True,
                        column_config={
                            "Valor intrínseco": st.column_config.Column("Valor intrínseco", help=h("valor_intrinseco_col")),
                            "VP dividendos": st.column_config.Column("VP dividendos", help=h("vp_dividendos")),
                            "VP residual": st.column_config.Column("VP residual", help=h("vp_residual")),
                        })

                    if a.sensibilidade:
                        st.markdown("**Sensibilidade do valor (linhas = Ke, colunas = g)**", help=h("tab_sensibilidade"))
                        sens = CFG["ddm"]["sensibilidade"]
                        cols = [fmt_pct(a.g_alto + dg) for dg in sens["delta_g"]]
                        idx = [fmt_pct((a.ke or 0) + dk) for dk in sens["delta_ke"]]
                        df = pd.DataFrame(
                            [[fmt_rs(v) for v in linha] for linha in a.sensibilidade],
                            columns=cols, index=idx)
                        st.dataframe(df, use_container_width=True)
                else:
                    st.info("DDM não calculado (faltou Beta/Ke, payout ou crescimento). Veja os alertas acima.")

            elif _aba == "Fundamentos (10 anos)":
                anos = c.anos_ordenados()
                df = pd.DataFrame({
                    "Ano": anos,
                    "Lucro Líq. (R$ mi)": [round(c.lucro_liquido.get(x, 0) / 1e6) for x in anos],
                    "Patrim. Líq. (R$ mi)": [round(c.patrimonio_liquido.get(x, 0) / 1e6) for x in anos],
                    "FCO (R$ mi)": [round(c.fco.get(x, 0) / 1e6) for x in anos],
                    "ROE": [fmt_pct(c.roe(x)) for x in anos],
                    "Payout": [fmt_pct(c.payout(x)) for x in anos],
                })
                st.dataframe(df, hide_index=True, use_container_width=True,
                             column_config={
                                 "Lucro Líq. (R$ mi)": st.column_config.Column("Lucro Líq. (R$ mi)", help=h("lucro_liq")),
                                 "Patrim. Líq. (R$ mi)": st.column_config.Column("Patrim. Líq. (R$ mi)", help=h("patrim_liq")),
                                 "FCO (R$ mi)": st.column_config.Column("FCO (R$ mi)", help=h("fco")),
                                 "ROE": st.column_config.Column("ROE", help=h("roe")),
                                 "Payout": st.column_config.Column("Payout", help=h("payout_col")),
                             })
                st.bar_chart(df.set_index("Ano")["Lucro Líq. (R$ mi)"])


# =========================================================================== #
# 2) GARIMPAR CARTEIRA (BSD)
# =========================================================================== #
elif modo.startswith("Garimpar"):
    st.subheader("Garimpar ações — ranking Big, Safe Dividend (BSD)", help=h("bsd"))
    st.caption("Cole vários tickers (separados por vírgula ou espaço). "
               "BSD > 80 = 'dividendo grande e seguro'.")
    txt = st.text_area("Tickers", value="TAEE11, EGIE3, CMIG4, ALUP11, CPFE3, EQTL3, ITUB4, BBAS3")
    if st.button("Garimpar", type="primary"):
        tickers = [t.strip().upper() for t in txt.replace(",", " ").split() if t.strip()]
        empresas = []
        prog = st.progress(0.0, text="Coletando dados...")
        for i, t in enumerate(tickers):
            c = montar(t, ANO_BASE, N_ANOS)
            if c is not None and c.anos:
                empresas.append(c)
            prog.progress((i + 1) / len(tickers), text=f"Coletando {t}...")
        if not empresas:
            prog.empty()
            st.error("Nenhuma empresa com dados suficientes.")
        else:
            # UX (quick-260710-u1f): mantém o feedback no corpo durante a consolidação
            # (Selic/BCB + BSD + filtros) em vez de esvaziar a barra e "sumir" a tela.
            prog.progress(1.0, text="Consolidando ranking (BSD + filtros)…")
            selic = selic_atual()
            csc = CFG["screening"]["custom"]
            bsd = sc.bsd_ranking(empresas, pesos=CFG["screening"]["bsd"]["pesos"],
                                 anos_media=CFG["screening"]["bsd"]["anos_media"],
                                 winsor=CFG["screening"]["bsd"]["winsor"])
            bsd_map = {b["ticker"]: b for b in bsd}
            rows = []
            for c in empresas:
                rc = sc.filtros_customizados(c, selic=selic, n_anos=N_ANOS,
                                             volume_min=csc["volume_min_diario"], roe_min=csc["roe_min"])
                b = bsd_map.get(c.ticker, {})
                rows.append({
                    "Ticker": c.ticker,
                    "_passou": bool(rc.passou),
                    "Ano-base": c.ultimo_ano(),
                    "BSD": round(b.get("bsd") or 0, 1),
                    # Selo READ-ONLY: cor sai da função pura da engine (selo.cor_do_bsd),
                    # o emoji da presentation. Nenhum threshold de cor vive aqui.
                    "Selo": presentation.selo_emoji(selo.cor_do_bsd(b.get("bsd"), CFG)),
                    "BSD > 80": "Sim" if b.get("acima_de_80") else "Não",
                    "Passa filtros": "Sim" if rc.passou else "Não",
                    "Fatores faltando": b.get("n_fatores_faltantes") or 0,
                    "Setor": c.setor,
                })
            # CR-01: o corte por Selic (DY > Selic) vive em "Passa filtros"; ordena por ele
            # ANTES do BSD para que quem reprova no corte não apareça no topo.
            df = pd.DataFrame(rows).sort_values(["_passou", "BSD"], ascending=[False, False])
            df = df.drop(columns=["_passou"])
            prog.empty()
            st.dataframe(df, hide_index=True, use_container_width=True,
                         column_config={
                             "Ticker": st.column_config.Column("Ticker", help=h("ticker")),
                             "Ano-base": st.column_config.Column("Ano-base", help=h("ano_base")),
                             "BSD": st.column_config.Column("BSD", help=h("bsd")),
                             "Selo": st.column_config.Column("Selo", help=h("selo")),
                             "BSD > 80": st.column_config.Column("BSD > 80", help=h("bsd_maior_80")),
                             "Passa filtros": st.column_config.Column("Passa filtros", help=h("passa_filtros")),
                             "Fatores faltando": st.column_config.Column("Fatores faltando", help=h("fatores_faltando")),
                             "Setor": st.column_config.Column("Setor", help=h("setor")),
                         })
            # Legenda dos selos (quick-260710-u3g #6): a coluna Selo é só a bolinha; a régua de
            # cores vem dos MESMOS cortes de config que o selo usa (selo.cor_do_bsd) — fiel, sem recálculo.
            _cor = CFG["selo"]["cor"]
            st.caption(
                f"**Legenda do selo** (cor = nota BSD): 🟢 verde ≥ {_cor['verde_min']} · "
                f"🔵 azul {_cor['azul_min']}–{_cor['verde_min'] - 1} · "
                f"🟡 amarelo {_cor['amarelo_min']}–{_cor['azul_min'] - 1} · "
                f"🔴 vermelho < {_cor['amarelo_min']}. Verde/azul = qualidade **Alta**; "
                "amarelo/vermelho = qualidade **Baixa**. Triagem visual, não recomendação.",
                help=h("selo"),
            )
            st.warning("**BSD > 80 sem 'Passa filtros' NÃO é recomendação.** O BSD é uma nota "
                       "de estabilidade do dividendo; o corte por Selic (DY > Selic) e os demais "
                       "filtros vivem na coluna 'Passa filtros'. Comece pelas que passam nos filtros.")
            bsd_fig = go.Figure(go.Bar(
                x=df["Ticker"], y=df["BSD"], marker_color="#7fb3ff",
                hovertemplate="%{x}<br>BSD %{y:.1f}<extra></extra>",
            ))
            bsd_fig.add_hline(y=80, line_width=1, line_dash="dash", line_color="#2ca02c",
                              annotation_text="Corte 80", annotation_position="top left")
            bsd_fig.update_xaxes(categoryorder="array", categoryarray=list(df["Ticker"]), title_text=None)
            bsd_fig.update_yaxes(range=[0, 100], title_text="BSD")
            bsd_fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
            st.plotly_chart(bsd_fig, width="stretch")
            st.caption("Próximo passo: rode o Ranking nas melhores e depois analise as finalistas a fundo.")


# =========================================================================== #
# 3) RANKING POR MÚLTIPLOS
# =========================================================================== #
elif modo.startswith("Ranking"):
    st.subheader("Ranking por múltiplos + preço-alvo", help=h("ranking"))
    st.caption("Padroniza os múltiplos em nota 0–100 e estima o preço justo por regressão "
               "P/L ~ f(payout, ROE). Upside positivo = candidata a estar barata.")
    txt = st.text_area("Tickers (de preferência do mesmo setor)",
                       value="TAEE11, EGIE3, CMIG4, ALUP11, CPFE3, EQTL3")
    if st.button("Rankear", type="primary"):
        tickers = [t.strip().upper() for t in txt.replace(",", " ").split() if t.strip()]
        empresas = []
        prog = st.progress(0.0, text="Coletando dados...")
        for i, t in enumerate(tickers):
            c = montar(t, ANO_BASE, N_ANOS)
            if c is not None and c.anos:
                empresas.append(c)
            prog.progress((i + 1) / len(tickers), text=f"Coletando {t}...")
        if not empresas:
            prog.empty()
            st.error("Nenhuma empresa com dados suficientes.")
        else:
            # UX (quick-260710-u1f): feedback no corpo enquanto roda a regressão/ranking,
            # em vez de esvaziar a barra e deixar a tela parada.
            prog.progress(1.0, text="Calculando ranking e preço-alvo (regressão)…")
            nomes, ML, ROE, PL, EY, DP = [], [], [], [], [], []
            for c in empresas:
                # FIX-04: ROE/LPA de valuation saem dos métodos canônicos normalizados —
                # o MESMO número que o Analisar exibe (Core Value). app.py segue read-only:
                # só troca QUAL método canônico lê, não recalcula método.
                u = c.ultimo_ano(); lpa = c.lpa_valuation()
                nomes.append(c.ticker)
                ML.append(c.margem_valuation())  # AUD-RANK-01: ML normalizada, igual a ROE/PL/EY do ranque
                ROE.append(c.roe_valuation())
                PL.append(mult.preco_lucro(c.preco_atual, lpa))
                EY.append(mult.earnings_yield(lpa, c.preco_atual))
                DP.append(c.payout_valuation())  # payout canônico sustentável (mediana), igual ao Analisar
            ranking = cmp.ranking_por_multiplos(nomes, {"ML": ML, "ROE": ROE, "PL": PL, "EY": EY})
            reg = cmp.ajustar_regressao_pl(PL, DP, ROE)
            alvos = {}
            if reg:
                for c in empresas:
                    pa = cmp.preco_alvo_por_regressao(reg, c.payout_valuation(), c.roe_valuation(), c.lpa_valuation(), c.preco_atual)
                    if pa:
                        alvos[c.ticker] = pa
            rows = []
            for r in ranking:
                pa = alvos.get(r["empresa"])
                if pa is None:
                    # RANK-01: empresa descartada da regressão (ROE/payout ausente).
                    # "indisponível" é estado neutro de dado ausente, não "cara" — distingue do "—" genérico.
                    preco_alvo_txt = "indisponível"
                    upside_txt = "indisponível"
                    veredito = "indisponível (ROE/payout ausente)"
                else:
                    preco_alvo_txt = fmt_rs(pa.preco_alvo)
                    upside_txt = fmt_pct(pa.upside) if pa.upside is not None else "—"
                    veredito = "Subavaliada" if pa.subavaliada else "Cara"
                    if pa.payout_fora_faixa:  # espelha o alerta ">100%" do Analisar
                        veredito += " (payout ajustado)"
                _c_sel = next(c for c in empresas if c.ticker == r["empresa"])
                rows.append({
                    "Ticker": r["empresa"],
                    "Nota (0–100)": round(r["nota"], 1) if r["nota"] is not None else None,
                    # Selo READ-ONLY: BSD por empresa vem da engine (sc.bsd_empresa, sem rede —
                    # dados já carregados), cor de selo.cor_do_bsd. Zero recálculo na view.
                    "Selo": presentation.selo_emoji(selo.cor_do_bsd(sc.bsd_empresa(_c_sel, CFG), CFG)),
                    "Ano-base": next(c.ultimo_ano() for c in empresas if c.ticker == r["empresa"]),
                    "Preço atual": fmt_rs(next(c.preco_atual for c in empresas if c.ticker == r["empresa"])),
                    "Preço-alvo": preco_alvo_txt,
                    "Upside": upside_txt,
                    "Veredito": veredito,
                })
            prog.empty()
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                         column_config={
                             "Ticker": st.column_config.Column("Ticker", help=h("ticker")),
                             "Nota (0–100)": st.column_config.Column("Nota (0–100)", help=h("nota_padronizada")),
                             "Selo": st.column_config.Column("Selo", help=h("selo")),
                             "Ano-base": st.column_config.Column("Ano-base", help=h("ano_base")),
                             "Preço atual": st.column_config.Column("Preço atual", help=h("preco")),
                             "Preço-alvo": st.column_config.Column("Preço-alvo", help=h("preco_alvo")),
                             "Upside": st.column_config.Column("Upside", help=h("upside")),
                             "Veredito": st.column_config.Column("Veredito", help=h("veredito")),
                         })
            # Legenda dos selos (quick-260710-u3g #6): mesma régua de config do Garimpar.
            _cor = CFG["selo"]["cor"]
            st.caption(
                f"**Legenda do selo** (cor = nota BSD): 🟢 verde ≥ {_cor['verde_min']} · "
                f"🔵 azul {_cor['azul_min']}–{_cor['verde_min'] - 1} · "
                f"🟡 amarelo {_cor['amarelo_min']}–{_cor['azul_min'] - 1} · "
                f"🔴 vermelho < {_cor['amarelo_min']}. Verde/azul = qualidade **Alta**; "
                "amarelo/vermelho = qualidade **Baixa**. Triagem visual, não recomendação.",
                help=h("selo"),
            )
            if reg:
                _t_payout = f"{'−' if reg.coeficientes[1] < 0 else '+'} {abs(reg.coeficientes[1]):.2f}·payout"
                _t_roe = f"{'−' if reg.coeficientes[2] < 0 else '+'} {abs(reg.coeficientes[2]):.2f}·ROE"
                st.caption(f"Regressão: P/L = {reg.coeficientes[0]:.2f} {_t_payout} "
                           f"{_t_roe}  (R²={reg.r2:.2f}, n={reg.n})")
                # RANK-CONF-01: amostra pequena → regressão instável, veredito pouco confiável.
                if reg.amostra_pequena:
                    st.warning(
                        f"**Amostra pequena (n={reg.n}).** Com poucas empresas, a regressão "
                        f"P/L ~ f(payout, ROE) fica instável e o veredito *Subavaliada/Cara* é "
                        f"pouco confiável. Adicione mais comparáveis **do mesmo setor** para "
                        f"firmar o preço-alvo."
                    )
                # RANK-CONF-02: ROE com coeficiente negativo contraria Gordon (caso TAEE11).
                if reg.roe_sinal_invertido:
                    st.warning(
                        "**Coeficiente do ROE saiu negativo** — isso *contraria* a teoria "
                        "(modelo de Gordon: o P/L justo cresce com o ROE). Em geral é sinal de "
                        "overfitting/multicolinearidade e acaba penalizando as empresas mais "
                        "rentáveis. Aqui o preço-alvo da regressão pode discordar do **Analisar "
                        "a fundo** (DDM); nesse caso, confie mais no DDM."
                    )
                # RANK-CONF-04 (AUD-CMP-02): R² baixo → regressão explica pouco do P/L do setor.
                if reg.r2_baixo:
                    st.warning(
                        f"**R² baixo ({reg.r2:.2f}).** A regressão explica pouco da variação de "
                        f"P/L entre as comparáveis — o preço-alvo e o veredito *Subavaliada/Cara* "
                        f"são pouco confiáveis. Use comparáveis mais homogêneas (mesmo segmento) ou "
                        f"confie mais no **Analisar a fundo** (DDM)."
                    )
                # RANK-CONF-03: orientação fixa de mesmo segmento (sempre que há tabela).
                st.caption(
                    "Compare empresas do **mesmo segmento** (ex.: geração × transmissão × "
                    "distribuição de energia). Misturar segmentos distorce a regressão e o ranking."
                )
            else:
                st.info("Poucas empresas para a regressão (precisa de ≥4). Os preços-alvo ficam indisponíveis.")


# =========================================================================== #
# 3b) COMPARAR AÇÕES — comparador lado a lado (COMP-01/02/03). Read-only: só
#     normaliza a entrada, faz fetch cacheado (montar) e renderiza a tabela
#     transposta que a engine (comparador.montar_comparativo) monta. Sem sort,
#     sem ticker-alvo, sem destaque — só triagem lado a lado (D2/D4).
# =========================================================================== #
elif modo.startswith("Comparar"):
    st.subheader("Comparar ações — múltiplos e selo lado a lado", help=h("comparar_metricas"))
    st.caption(
        "Compare múltiplos e o selo de vários tickers lado a lado — apenas triagem, "
        "não é ranking nem recomendação. De preferência do mesmo setor."
    )
    _cmp_txt = st.text_input("Tickers", value="TAEE11, EGIE3, CMIG4")
    _cmp_tickers = lentes.normalizar_tickers(_cmp_txt, 6)
    _cmp_contextos = []
    if _cmp_tickers:
        _cmp_prog = st.progress(0.0, text="Coletando dados...")
        for i, t in enumerate(_cmp_tickers):
            c = montar(t, ANO_BASE, N_ANOS)
            if c is not None and c.anos:
                _cmp_contextos.append(c)
            _cmp_prog.progress((i + 1) / len(_cmp_tickers), text=f"Coletando {t}...")
        _cmp_prog.empty()
    _cmp_tabela = comparador.montar_comparativo(_cmp_contextos, CFG)
    if _cmp_tabela.suficiente:
        st.dataframe(_cmp_tabela.df, use_container_width=True)
        st.caption("Não é ranking nem recomendação — apenas contexto lado a lado.")
    else:
        st.info("Informe ao menos 2 tickers com dados para comparar.")


# =========================================================================== #
# 4) SWING TRADE (ANÁLISE TÉCNICA) — MVP visual: candlestick intraday/diário
# =========================================================================== #
elif modo.startswith("Análise técnica"):
    st.subheader("Análise técnica (timing) — leitura do candlestick (intraday/diário)")
    st.caption(
        "Visão de candlestick de tickers da B3 via Yahoo (grátis, best-effort com atraso ~15min). "
        "Apenas exibe o gráfico — **não é recomendação de compra ou venda**."
    )

    col1, col2, col3 = st.columns([3, 2, 1])
    ticker = col1.text_input("Ticker da B3", value="TAEE11",
                             placeholder="ex.: PETR4, VALE3, TAEE11").strip().upper()
    # Rótulos pt-BR → chaves da engine (timeframes válidos de _PERIODO_POR_TF)
    _TF_MAP = {"Diário": "diario", "1h": "1h", "30m": "30m", "5m": "5m"}
    tf_label = col2.selectbox("Timeframe", list(_TF_MAP.keys()), index=0)
    tf_key = _TF_MAP[tf_label]

    # Invalidação targetada por nonce (NUNCA clear global): o botão Atualizar só incrementa
    # o nonce do par (ticker, timeframe) — cria uma nova entrada de cache p/ esse par e a
    # antiga expira pelo TTL, sem tocar o cache da aba Analisar (D-08).
    k = _nonce_key(ticker, tf_key)
    st.session_state.setdefault(k, 0)
    if col3.button("Atualizar", use_container_width=True):
        st.session_state[k] += 1

    # Auto-refresh OPCIONAL via st.fragment(run_every=...) — nativo no Streamlit, zero dependência.
    # toggle/intervalo são o "tick visual"; o porteiro dos dados segue sendo o TTL=300s de
    # frame_intraday, por isso o auto-refresh NÃO incrementa o nonce (anti rate-limit do Yahoo).
    # Ficam FORA do fragment de propósito: mexer neles dispara um rerun que re-decora o fragment.
    _INTERVALOS = {"30 segundos": 30, "1 minuto": 60, "5 minutos": 300}
    cauto1, cauto2 = st.columns([2, 2])
    auto_on = cauto1.toggle(
        "Atualização automática", value=False, disabled=(tf_key == "diario"),
        help="Re-roda só o gráfico de swing no intervalo escolhido, sem recarregar a página. "
             "Reusa o cache — a Yahoo é consultada no máximo uma vez a cada 5min por par.",
    )
    auto_intervalo = cauto2.selectbox(
        "Intervalo", list(_INTERVALOS),
        disabled=(not auto_on or tf_key == "diario"),
    )
    if tf_key == "diario":
        st.caption("A atualização automática só faz sentido em timeframes intraday "
                   "(1h/30m/5m); no Diário ela é desnecessária.")
    run_every = _INTERVALOS[auto_intervalo] if (auto_on and tf_key != "diario") else None

    # Gateia pelo ticker preenchido (não pelo retorno efêmero do botão): o gráfico persiste
    # entre reruns ao trocar de timeframe sem exigir novo clique.
    if ticker:
        # Render do bloco swing isolado num fragment: com run_every!=None ele re-roda
        # sozinho no intervalo escolhido, sem recarregar a página nem re-renderizar as
        # outras abas. Engloba fetch + figura + selo de atraso + card de veredito p/ manter
        # candle, selo e veredito coerentes num mesmo snapshot. Captura ticker/tf_key/tf_label/
        # k/CFG/run_every por closure; LÊ st.session_state[k] (nonce) sem incrementar.
        @st.fragment(run_every=run_every)
        def _render_swing():
            with st.spinner(f"Coletando candles de {ticker} ({tf_label})..."):
                f = frame_intraday(ticker, tf_key, st.session_state[k])

            if f.disponivel is False:
                # D-07: a copy amigável mora na UI, não na engine. fallback genérico p/ motivo desconhecido.
                _MSG_MOTIVO = {
                    "timeframe_invalido": "Timeframe inválido.",
                    "sem_dados": "Sem candles para esse ticker/timeframe — a Yahoo não retornou dados. "
                                 "Confira o ticker.",
                    "fetch_falhou": "Falha ao buscar os dados (instabilidade na fonte). "
                                    "Tente o botão Atualizar.",
                }
                st.error(_MSG_MOTIVO.get(f.motivo, "Não foi possível carregar os candles agora. "
                                                   "Tente o botão Atualizar."))
            else:
                # Cadeia de engine read-only (zero recálculo na UI): SinaisTecnicos + SetupSwing.
                # ohlc_nominal=f.ohlc mantém pivôs/S-R/Fibonacci em escala NOMINAL, coerentes com o
                # candlestick nominal (Pitfall 6); os indicadores rodam sobre o frame ajustado por split.
                sinais = indicators.calcular(f.ohlc_ajustado, CFG, ohlc_nominal=f.ohlc)
                sw = setup.montar_setup(sinais, CFG)

                # Estado dos overlays ISOLADO da aba Analisar (D-03 / SWING-01): chave e defaults
                # próprios — NUNCA grafico.estado_padrao() (tudo OFF) nem a chave "tec_estado".
                # D-02: MMs/ADX/RSI/MACD/S-R/Fibonacci/níveis do setup LIGADOS; Donchian/Bollinger/
                # padrões DESLIGADOS. As 4 primeiras chaves casam com o schema de overlays_preco/
                # subpaineis_ativos; sr_on/fib_on/niveis_setup_on/padroes_on são extras lidos só aqui.
                st.session_state.setdefault("tec_estado_swing", {
                    "tendencia": {"on": True, "tipo": "sma", "janelas": [20, 50, 200]},
                    "canais": {"donchian_on": False, "donchian_janela": 20, "bollinger_on": False},
                    "forca": {"on": True},
                    "momentum": {"rsi_on": True, "macd_on": True},
                    "sr_on": True, "fib_on": True, "niveis_setup_on": True, "padroes_on": False,
                })
                est = st.session_state["tec_estado_swing"]

                # Controle de vista (LWC-01): Plotly é o DEFAULT; "Modo Trading" troca só a
                # camada de render sobre os MESMOS dados (f.ohlc/sw/sinais já montados) — não
                # refaz fetch nem recálculo. Estado isolado em chave própria "swing_vista"
                # (NUNCA a chave da aba Analisar). Selo de atraso, card de veredito e Overlays
                # continuam iguais nas duas vistas.
                st.session_state.setdefault("swing_vista", "Plotly")
                vista = st.radio(
                    "Vista", ["Plotly", "Modo Trading"],
                    index=0 if st.session_state["swing_vista"] == "Plotly" else 1,
                    horizontal=True, key="swing_vista",
                    help="Plotly (multi-painel com subpainéis) é a vista padrão. "
                         "Modo Trading é o candlestick TradingView (scroll-zoom, pan, "
                         "crosshair com rótulos nos eixos, Y-autoscale e último preço).",
                )

                # Slot do gráfico reservado ANTES do expander para o render ler o `est` já
                # atualizado pelos toggles no MESMO rerun (sem lag de um clique) — padrão Analisar.
                grafico_box = st.container()

                with st.expander("Overlays", expanded=False):
                    ct, cc, cf, cm = st.columns(4)
                    with ct:
                        st.markdown("**Tendência**", help=h("tec_mm"))
                        est["tendencia"]["on"] = st.toggle(
                            "Médias móveis", value=est["tendencia"]["on"], help=h("tec_mm"))
                        est["tendencia"]["tipo"] = st.radio(
                            "Tipo", ["sma", "ema"],
                            index=0 if est["tendencia"]["tipo"] == "sma" else 1,
                            format_func=str.upper, horizontal=True, help=h("tec_mm"))
                        est["tendencia"]["janelas"] = st.multiselect(
                            "Janelas", [20, 50, 200], default=est["tendencia"]["janelas"],
                            help=h("tec_cross"))
                    with cc:
                        st.markdown("**Canais**", help=h("tec_donchian"))
                        est["canais"]["donchian_on"] = st.toggle(
                            "Donchian", value=est["canais"]["donchian_on"], help=h("tec_donchian"))
                        est["canais"]["bollinger_on"] = st.toggle(
                            "Bollinger", value=est["canais"]["bollinger_on"], help=h("tec_bollinger"))
                    with cf:
                        st.markdown("**Força**", help=h("tec_adx"))
                        est["forca"]["on"] = st.toggle(
                            "ADX", value=est["forca"]["on"], help=h("tec_adx"))
                    with cm:
                        st.markdown("**Momentum**", help=h("tec_rsi"))
                        est["momentum"]["rsi_on"] = st.toggle(
                            "RSI", value=est["momentum"]["rsi_on"], help=h("tec_rsi"))
                        est["momentum"]["macd_on"] = st.toggle(
                            "MACD", value=est["momentum"]["macd_on"], help=h("tec_macd"))
                    # Overlays extras (lidos só pelo render do app.py — grafico.py os ignora).
                    cs, cfi, cn, cp = st.columns(4)
                    with cs:
                        st.markdown("**Suporte/Resistência**", help=h("tec_donchian"))
                        est["sr_on"] = st.toggle("Zonas S/R", value=est["sr_on"])
                    with cfi:
                        st.markdown("**Fibonacci**")
                        est["fib_on"] = st.toggle("Retrações", value=est["fib_on"])
                    with cn:
                        st.markdown("**Níveis do setup**")
                        est["niveis_setup_on"] = st.toggle(
                            "Entrada/stop/alvo", value=est["niveis_setup_on"])
                    with cp:
                        st.markdown("**Padrões**")
                        est["padroes_on"] = st.toggle("Anotar padrões", value=est["padroes_on"])

                with grafico_box:
                  if vista == "Modo Trading":
                    # LWC-01: candlestick TradingView sobre os MESMOS dados (sem novo fetch nem
                    # recálculo da engine). Overlays da engine entram no plano 02.
                    _render_lwc(f, sw, sinais, est, ticker, tf_key)
                  else:
                    # Figura multi-painel: candlestick (row 1) + overlays MM + subpainéis RSI/MACD/ADX.
                    # Reuso direto das funções puras de grafico.py (golden-pinned) com o `est` isolado;
                    # a diferença LINHA→CANDLESTICK vive só no trace de preço, não nos specs.
                    specs = grafico.subpaineis_ativos(est, sinais)
                    layout = grafico.layout_subplots(len(specs))
                    fig = make_subplots(
                        rows=layout["rows"], cols=1, shared_xaxes=True,
                        row_heights=layout["row_heights"], vertical_spacing=0.03,
                    )
                    # Row 1 — candlestick NOMINAL (D-02); rangeslider OFF (Pitfall 4: rouba altura das rows).
                    fig.add_trace(go.Candlestick(
                        x=f.ohlc.index,
                        open=f.ohlc["Open"], high=f.ohlc["High"],
                        low=f.ohlc["Low"], close=f.ohlc["Close"],
                        name=ticker,
                    ), row=1, col=1)
                    fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
                    # Overlays MM/Donchian/Bollinger no eixo de preço (mesmo loop da aba Analisar).
                    for ov in grafico.overlays_preco(est, sinais):
                        fig.add_trace(go.Scatter(
                            x=ov.serie.index, y=ov.serie.values, mode="lines", name=ov.nome,
                            line=dict(ov.estilo),
                        ), row=1, col=1)

                    # --- Overlays de NÍVEL (read-only de sinais.niveis / sw) -------------------
                    # Toda a copy é NEUTRA ("estudo"/"projeção de estudo") — gate SWING-02 / Pitfall 5.
                    # Cada bloco é gateado pelo seu toggle em `est` e degrada sem quebrar quando os
                    # campos da engine são None / listas vazias (LEVEL-01: zonas como BANDAS, nunca pontos).
                    if est["sr_on"] and sinais.niveis is not None:
                        for (lo, hi) in sinais.niveis.suportes:
                            fig.add_hrect(y0=lo, y1=hi, line_width=0, fillcolor="green",
                                          opacity=0.08, row=1, col=1)
                        for (lo, hi) in sinais.niveis.resistencias:
                            fig.add_hrect(y0=lo, y1=hi, line_width=0, fillcolor="red",
                                          opacity=0.08, row=1, col=1)
                    if est["niveis_setup_on"] and sw.entrada_zona:
                        lo, hi = sw.entrada_zona
                        fig.add_hrect(y0=lo, y1=hi, line_width=0, fillcolor="blue", opacity=0.10,
                                      annotation_text="zona de entrada (estudo)", row=1, col=1)
                        if sw.stop is not None:
                            fig.add_hline(y=sw.stop, line_dash="dash", line_color="#d62728",
                                          annotation_text="stop (estudo)", row=1, col=1)
                        if sw.alvo is not None:
                            fig.add_hline(y=sw.alvo, line_dash="dash", line_color="#2ca02c",
                                          annotation_text="alvo (estudo)", row=1, col=1)
                    if est["fib_on"] and sinais.niveis is not None and sinais.niveis.fib_retracoes:
                        for nome, preco in sinais.niveis.fib_retracoes.items():
                            fig.add_hline(y=preco, line_dash="dot", line_color="#9467bd",
                                          annotation_text=f"Fib {nome}", row=1, col=1)
                    # Anotação de padrões (OFF por padrão, D-02): neckline horizontal (simplificação
                    # honesta do MVP — reta inclinada da OCO deferida), rótulo "em formação"/"confirmado"
                    # e alvo measured-move. Cor por direção (espelha setup._PADROES_ALTA/_BAIXA).
                    if est["padroes_on"] and sinais.padroes is not None:
                        _COR_PAD = {"duplo_fundo": "#2ca02c", "oco_invertido": "#2ca02c",
                                    "duplo_topo": "#d62728", "oco": "#d62728"}
                        for p in sinais.padroes.lista:
                            ts = sorted(p.pivos_envolvidos)
                            if not ts:
                                continue
                            cor = _COR_PAD.get(p.tipo, "#888888")
                            dash = "solid" if p.estado == "confirmado" else "dot"
                            rotulo = "confirmado" if p.estado == "confirmado" else "em formação"
                            fig.add_shape(type="line", x0=ts[0], x1=ts[-1],
                                          y0=p.neckline, y1=p.neckline,
                                          line=dict(color=cor, width=1.5, dash=dash), row=1, col=1)
                            fig.add_annotation(x=ts[-1], y=p.neckline,
                                               text=f"{p.tipo.replace('_', ' ')} · {rotulo}",
                                               showarrow=False, yshift=12,
                                               font=dict(color=cor, size=10), row=1, col=1)
                            fig.add_hline(y=p.alvo, line_width=1, line_dash="dot", line_color=cor,
                                          annotation_text="alvo (projeção de estudo)",
                                          annotation_position="right", row=1, col=1)
                            fig.add_trace(go.Scatter(
                                x=list(p.pivos_envolvidos), y=list(p.pivos_envolvidos.values()),
                                mode="markers", marker=dict(symbol="circle-open", color=cor, size=9),
                                showlegend=False, hoverinfo="skip",
                            ), row=1, col=1)
                    # D-04: a última barra pode estar em formação (viva) — marca sem derivar nível dela.
                    if f.barra_viva and f.ultima_barra_ts is not None:
                        fig.add_vline(x=f.ultima_barra_ts, line_width=1, line_dash="dot",
                                      line_color="#888888", row=1, col=1)
                    # Subpainéis dos osciladores ativos — série(s) + linhas de referência do SubpainelSpec.
                    for i, spec in enumerate(specs):
                        r = i + 2
                        for rotulo, s in spec.series:
                            # O histograma do MACD é (MACD − Sinal) e deve ser BARRAS (verde ≥0 /
                            # vermelho <0), não uma linha — como na aba Analisar.
                            if rotulo == "Histograma":
                                fig.add_trace(go.Bar(
                                    x=s.index, y=s.values, name=rotulo,
                                    marker_color=["#2ca02c" if (v is not None and v >= 0) else "#d62728"
                                                  for v in s.values],
                                ), row=r, col=1)
                                continue
                            fig.add_trace(go.Scatter(
                                x=s.index, y=s.values, mode="lines", name=rotulo,
                            ), row=r, col=1)
                        for ref in spec.referencias:
                            fig.add_hline(y=ref, line_width=1, line_dash="dot",
                                          line_color="#aaaaaa", row=r, col=1)
                        fig.update_yaxes(title_text=spec.nome.upper(), row=r, col=1)
                    fig.update_layout(
                        height=400 + 140 * len(specs), margin=dict(l=10, r=10, t=40, b=10),
                        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                    )
                    st.plotly_chart(fig, width="stretch")

                # Selo de atraso SEMPRE visível (D-08): honestidade sobre o best-effort intraday.
                atraso = f" · última barra {f.ultima_barra_ts:%H:%M}" if f.ultima_barra_ts is not None else ""
                st.caption(f"~15min de atraso (best-effort){atraso}.")

                # Histórico insuficiente: <2 barras ⇒ sem barra fechada p/ leitura técnica (Fases 13+).
                if f.idx_ultima_fechada is None:
                    st.warning("Histórico insuficiente — menos de duas barras fechadas neste timeframe.")

                # --- Card de veredito read-only (D-01/D-04/D-05) ---------------------------
                # Tudo LIDO de `sw` + `sinais` (zero recálculo). NUNCA st.metric p/ níveis (Pitfall 5):
                # entrada/stop/alvo vão numa TABELA "Referências de estudo (não são ordens)". Copy
                # estritamente NÃO-imperativa (gate SWING-02) — mesmo firewall do test_setup_report.
                st.divider()
                st.markdown(f"### Veredito de estudo · **{sw.grade}**")
                st.caption(f"Pontuação de confluência técnica: **{sw.score:.0f}** / 100")
                if sinais.contexto is not None:
                    st.caption(
                        f"Tendência: {sinais.contexto.dow_diario} · "
                        f"MTF: {sinais.contexto.alinhamento_mtf}"
                    )

                # Decomposição peso-a-peso (D-04). "Sem setup"/decomposição vazia → mensagem neutra
                # (Pitfall 3) — o checklist abaixo vem independente do gate.
                _FAM_LABEL = {
                    "tendencia": "Tendência", "risco_retorno": "Risco/retorno",
                    "padroes": "Padrões", "momentum": "Momentum", "volume": "Volume",
                }
                if sw.decomposicao:
                    st.markdown("**Decomposição do score (por família)**")
                    linhas = ["| Família | Contribuição | Peso | Leitura |", "|---|---|---|---|"]
                    for c in sw.decomposicao:
                        fam = _FAM_LABEL.get(c.familia, c.familia)
                        linhas.append(
                            f"| {fam} | {c.contribuicao:.1f} pts | {c.peso} | "
                            f"{esc_md(c.detalhe)} |"
                        )
                    st.markdown("\n".join(linhas))
                else:
                    st.info("Sem confluência suficiente para um setup de estudo.")

                # Checklist (D-05): ✓ quando o sinal está ativo, ✗ quando inativo. Independe do gate.
                if sinais.checklist is not None and sinais.checklist.sinais:
                    st.markdown("**Checklist técnico**")
                    chk = []
                    for s in sinais.checklist.sinais:
                        marca = "✓" if s.ativo else "✗"
                        chk.append(f"- {marca} **{s.nome}** — {esc_md(s.detalhe)}")
                    st.markdown("\n".join(chk))

                # Tabela de níveis — rótulo EXATO D-05. fmt_rs trata None→"—"; esc_md escapa o "$".
                st.markdown("**Referências de estudo (não são ordens)**")
                if sw.entrada_zona is not None:
                    _lo, _hi = sw.entrada_zona
                    _entrada = f"{fmt_rs(_lo)} – {fmt_rs(_hi)}"
                else:
                    _entrada = "—"
                _rr = sinais.niveis.risco_retorno if sinais.niveis is not None else "indisponivel"
                niveis_linhas = [
                    "| Referência | Valor |", "|---|---|",
                    f"| Zona de entrada (estudo) | {esc_md(_entrada)} |",
                    f"| Stop (estudo) | {esc_md(fmt_rs(sw.stop))} |",
                    f"| Alvo (estudo) | {esc_md(fmt_rs(sw.alvo))} |",
                    f"| Risco : retorno | {esc_md(_rr)} |",
                ]
                st.markdown("\n".join(niveis_linhas))

                # Disclaimer condicional inline (SWING-02): ajusta o tom quando não há setup.
                if sw.grade == "Sem setup":
                    st.caption(
                        "Esta página exibe sinais técnicos de estudo e não recomenda compra ou venda. "
                        "No momento não há confluência suficiente para uma referência de setup."
                    )
                else:
                    st.caption(
                        "Esta página exibe sinais técnicos de estudo e não recomenda compra ou venda. "
                        "Os níveis acima são referências de estudo, jamais ordens."
                    )
        _render_swing()


# --------------------------------------------------------------------------- #
# Rodapé — link discreto para a página velada de metodologia e referências.
st.markdown("---")
st.markdown(
    "<div style='text-align:center; opacity:0.55; font-size:0.85em'>"
    "<a href='?p=metodologia' target='_self' style='color:inherit'>Metodologia e referências</a>"
    "</div>",
    unsafe_allow_html=True,
)
