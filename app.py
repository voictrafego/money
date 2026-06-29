"""Interface web (Streamlit) do Analista de Dividendos.

Rode com:  ./.venv/bin/streamlit run app.py
Abre no navegador. Mesma engine do CLI, método do livro Orleans Martins & Felipe Pontes.
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from analista import grafico
from analista.core import comparables as cmp
from analista.core import multiples as mult
from analista.core import screening as sc
from analista.glossario import h
from analista.ingest import build, macro
from analista.report import presentation, report

ROOT = os.path.dirname(os.path.abspath(__file__))
import yaml

st.set_page_config(page_title="Analista de Dividendos", page_icon="💰", layout="wide")


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
    return "—" if x is None else f"{x*100:.{casas}f}%"


def fmt_num(x, casas=2):
    return "—" if x is None else f"{x:.{casas}f}"


def fmt_rs(x, casas=2):
    return "—" if x is None else f"R$ {x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def esc_md(s: str) -> str:
    """Escapa '$' p/ contextos markdown (metric, alertas): dois 'R$' na mesma
    string fariam o Streamlit interpretar o miolo como LaTeX e quebrar o layout."""
    return s.replace("$", r"\$")


# --------------------------------------------------------------------------- #
st.title("💰 Analista de Ações de Dividendos")
st.caption("Método do livro *O Investidor em Ações de Dividendos* (Orleans Martins & Felipe Pontes) · "
           "dados grátis: CVM + Yahoo + Banco Central")

modo = st.sidebar.radio(
    "O que você quer fazer?",
    ["🔎 Analisar uma ação", "⛏️ Garimpar carteira (BSD)", "📊 Ranking por múltiplos",
     "📈 Swing trade (análise técnica)"],
    help=h("menu"),
)
st.sidebar.markdown("---")
st.sidebar.metric("Selic (corte do DY)", fmt_pct(selic_atual()), help=h("selic"))
st.sidebar.caption(f"Janela: {N_ANOS} anos · até {ANO_BASE} (quando já divulgado na CVM)")

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ **Aviso.** Ferramenta de apoio à análise, de caráter educacional. "
    "**Não é recomendação de compra ou venda** nem consultoria/análise de valores "
    "mobiliários (CVM Res. 19/20). Os números podem conter erros ou dados desatualizados; "
    "rentabilidade passada não garante resultados futuros. Toda decisão de investimento é "
    "de responsabilidade exclusiva do usuário — verifique os dados na fonte (CVM/RI) antes de decidir."
)


# =========================================================================== #
# 1) ANALISAR UMA AÇÃO
# =========================================================================== #
if modo.startswith("🔎"):
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
        with st.spinner(f"Coletando dados de {ticker_ativo} (CVM + Yahoo)..."):
            c = montar(ticker_ativo, ANO_BASE, N_ANOS)
        if c is None or not c.anos:
            st.error(f"Não encontrei dados suficientes para {ticker_ativo}. "
                     "Confira o ticker ou adicione o mapeamento em data/ticker_map.json.")
        else:
            # FIX-03: injeta o rf do CAPM em CFG antes da engine. Rf = Selic through-the-cycle
            # (média ~10 anos), não a spot — numa perpetuidade a taxa reflete o juro de LP (a
            # sidebar/corte de DY seguem na Selic spot via selic_atual()). @st.cache_data
            # garante UMA chamada de rede por execução. app.py segue read-only.
            CFG["capm"]["rf_local"] = rf_capm(
                CFG["capm"]["selic_fallback"], CFG["capm"].get("rf_ciclo_anos", 10)
            )
            a = report.analisar_acao(c, CFG)

            st.markdown(f"### {a.ticker} — {a.nome}")
            st.caption(f"Setor: {a.setor or '—'}  ·  Estágio: {a.estagio}")

            # Veredito colorido
            v = a.veredito or "Indeterminado"
            if v.startswith("SUBAVALIADA"):
                st.success(f"✅ {esc_md(v)}")
            elif v.startswith("SOBREAVALIADA"):
                st.error(f"🔺 {esc_md(v)}")
            else:
                st.warning(f"➖ {esc_md(v)}")

            # Métricas principais — intervalo intrínseco vem do cálculo único do veredito (WR-07)
            intervalo = f"{fmt_rs(a.vmin)} – {fmt_rs(a.vmax)}" if a.vmin is not None and a.vmax is not None else "—"
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Preço atual", esc_md(fmt_rs(a.preco_atual)), help=h("preco"))
            m2.metric("Valor intrínseco (DDM)", esc_md(intervalo), help=h("valor_intrinseco"))
            hdr = presentation.header_dy(a.multiplos.get("DY rec."), a.multiplos.get("DY"))
            m3.metric(hdr["label"], hdr["value"], delta=hdr["delta"],
                      delta_color="off", help=hdr["help"])
            m4.metric("ROE", fmt_pct(a.multiplos.get("ROE")), help=h("roe"))
            m5.metric("Ke (custo capital)", fmt_pct(a.ke), help=h("ke"))

            if a.preco_atual is None:
                st.warning(
                    "⚠️ Preço atual indisponível agora (fonte Yahoo instável). Os fundamentos e o "
                    "valor intrínseco (DDM, dados CVM) abaixo seguem válidos — só a comparação de "
                    "preço/veredito fica suspensa até o preço voltar."
                )

            if a.alertas:
                for al in a.alertas:
                    st.warning(f"⚠️ {esc_md(al)}")

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
            with st.expander("⚙️ Indicadores técnicos (consultivo)", expanded=False):
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
                        "📉 Gráfico de preço indisponível agora (fonte Yahoo instável). Os fundamentos e o "
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

            # Enquadramento subordinado (UI-06): o veredito fundamentalista (acima) é o selo
            # decisório; a leitura técnica é CONSULTIVA e secundária — markdown/caption discreto,
            # nunca banner de veredito, voz de timing/reverificação (jamais "compre/venda").
            st.markdown("---")
            if grafico.leitura_tecnica_disponivel(a.sinais) and a.timing_resumo:
                st.markdown(f"**Timing (consultivo):** {esc_md(a.timing_resumo)}", help=h("tec_timing"))
                if a.matriz_leitura:                       # fundamento-primeiro (D-04)
                    st.markdown(esc_md(a.matriz_leitura))
                if a.alerta_reverificacao:                 # voz de reverificação, nunca venda
                    st.info(f"🔎 {esc_md(a.alerta_reverificacao)}")
            else:
                # Degradação holística (Plan 01): timing_resumo vazio ⇒ sem leitura, sem quebrar a aba.
                st.caption("Leitura técnica indisponível — histórico insuficiente para os indicadores")

            tab1, tab2, tab3 = st.tabs(["📈 Múltiplos & Crescimento", "💵 Valuation (DDM)", "📋 Fundamentos (10 anos)"])

            with tab1:
                cma, cmb = st.columns(2)
                with cma:
                    st.markdown("**Múltiplos (Cap. 10)**", help=h("tab_multiplos"))
                    st.caption("Dois payouts: o cru do último ano e o sustentável usado no valuation (DDM).",
                               help=h("payout_dual"))
                    payout_ult = c.payout(c.ultimo_ano())  # CRU do último ano (paridade report.py L156)
                    payout_proj = c.payout_valuation()     # sustentável (mediana sem clamp) usado no DDM
                    rows = presentation.linhas_multiplos(a.multiplos, payout_ult, payout_proj)
                    st.dataframe(pd.DataFrame(rows, columns=["Múltiplo", "Valor"]),
                                 hide_index=True, use_container_width=True)
                with cmb:
                    st.markdown("**Crescimento e custo de capital (Cap. 14/16)**", help=h("tab_crescimento"))
                    st.dataframe(pd.DataFrame([
                        ("g histórico (tendência log-linear)", fmt_pct(a.g_historico)),
                        ("g por fundamentos", fmt_pct(a.g_fundamentos)),
                        ("g alto adotado", fmt_pct(a.g_alto)),
                        ("g estável (perpetuidade)", fmt_pct(a.g_estavel)),
                        ("Beta", fmt_num(a.beta)),
                        ("Ke (CAPM)", fmt_pct(a.ke)),
                    ], columns=["Indicador", "Valor"]), hide_index=True, use_container_width=True)

            with tab2:
                if a.ddm_constante and a.ddm_h:
                    st.markdown("**Valor intrínseco por Desconto de Dividendos (Cap. 13-17)**", help=h("tab_ddm"))
                    st.dataframe(pd.DataFrame([
                        ("Otimista (g constante)", fmt_rs(a.ddm_constante.valor_intrinseco),
                         fmt_rs(a.ddm_constante.vp_dividendos), fmt_rs(a.ddm_constante.vp_residual)),
                        ("Conservador (modelo H)", fmt_rs(a.ddm_h.valor_intrinseco),
                         fmt_rs(a.ddm_h.vp_dividendos), fmt_rs(a.ddm_h.vp_residual)),
                    ], columns=["Cenário", "Valor intrínseco", "VP dividendos", "VP residual"]),
                        hide_index=True, use_container_width=True)

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

            with tab3:
                anos = c.anos_ordenados()
                df = pd.DataFrame({
                    "Ano": anos,
                    "Lucro Líq. (R$ mi)": [round(c.lucro_liquido.get(x, 0) / 1e6) for x in anos],
                    "Patrim. Líq. (R$ mi)": [round(c.patrimonio_liquido.get(x, 0) / 1e6) for x in anos],
                    "FCO (R$ mi)": [round(c.fco.get(x, 0) / 1e6) for x in anos],
                    "ROE": [fmt_pct(c.roe(x)) for x in anos],
                    "Payout": [fmt_pct(c.payout(x)) for x in anos],
                })
                st.dataframe(df, hide_index=True, use_container_width=True)
                st.bar_chart(df.set_index("Ano")["Lucro Líq. (R$ mi)"])


# =========================================================================== #
# 2) GARIMPAR CARTEIRA (BSD)
# =========================================================================== #
elif modo.startswith("⛏️"):
    st.subheader("Garimpar uma carteira — ranking Big, Safe Dividend (Cap. 8)", help=h("bsd"))
    st.caption("Cole vários tickers (separados por vírgula ou espaço). "
               "BSD > 80 = 'dividendo grande e seguro' (Carlson).")
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
        prog.empty()
        if not empresas:
            st.error("Nenhuma empresa com dados suficientes.")
        else:
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
                    "BSD > 80": "✅" if b.get("acima_de_80") else "",
                    "Passa filtros": "✅" if rc.passou else "",
                    "Fatores faltando": b.get("n_fatores_faltantes") or 0,
                    "Setor": c.setor,
                })
            # CR-01: o corte por Selic (DY > Selic) vive em "Passa filtros"; ordena por ele
            # ANTES do BSD para que quem reprova no corte não apareça no topo.
            df = pd.DataFrame(rows).sort_values(["_passou", "BSD"], ascending=[False, False])
            df = df.drop(columns=["_passou"])
            st.dataframe(df, hide_index=True, use_container_width=True,
                         column_config={"Ano-base": st.column_config.Column("Ano-base", help=h("ano_base"))})
            st.warning("⚠️ **BSD > 80 sem 'Passa filtros' NÃO é recomendação.** O BSD é uma nota "
                       "de estabilidade do dividendo; o corte por Selic (DY > Selic) e os demais "
                       "filtros vivem na coluna 'Passa filtros'. Comece pelas que passam nos filtros.")
            st.bar_chart(df.set_index("Ticker")["BSD"])
            st.caption("Próximo passo: rode o Ranking nas melhores e depois analise as finalistas a fundo.")


# =========================================================================== #
# 3) RANKING POR MÚLTIPLOS
# =========================================================================== #
elif modo.startswith("📊"):
    st.subheader("Ranking por múltiplos + preço-alvo (Cap. 11-12)", help=h("ranking"))
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
        prog.empty()
        if not empresas:
            st.error("Nenhuma empresa com dados suficientes.")
        else:
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
                    veredito = "Subavaliada ✅" if pa.subavaliada else "Cara 🔺"
                    if pa.payout_fora_faixa:  # espelha o alerta ">100%" do Analisar
                        veredito += " ⚠️ payout ajustado"
                rows.append({
                    "Ticker": r["empresa"],
                    "Nota (0–100)": round(r["nota"], 1) if r["nota"] is not None else None,
                    "Ano-base": next(c.ultimo_ano() for c in empresas if c.ticker == r["empresa"]),
                    "Preço atual": fmt_rs(next(c.preco_atual for c in empresas if c.ticker == r["empresa"])),
                    "Preço-alvo": preco_alvo_txt,
                    "Upside": upside_txt,
                    "Veredito": veredito,
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                         column_config={"Ano-base": st.column_config.Column("Ano-base", help=h("ano_base"))})
            if reg:
                st.caption(f"Regressão: P/L = {reg.coeficientes[0]:.2f} + {reg.coeficientes[1]:.2f}·payout "
                           f"+ {reg.coeficientes[2]:.2f}·ROE  (R²={reg.r2:.2f}, n={reg.n})")
                # RANK-CONF-01: amostra pequena → regressão instável, veredito pouco confiável.
                if reg.amostra_pequena:
                    st.warning(
                        f"⚠️ **Amostra pequena (n={reg.n}).** Com poucas empresas, a regressão "
                        f"P/L ~ f(payout, ROE) fica instável e o veredito *Subavaliada/Cara* é "
                        f"pouco confiável. Adicione mais comparáveis **do mesmo setor** para "
                        f"firmar o preço-alvo."
                    )
                # RANK-CONF-02: ROE com coeficiente negativo contraria Gordon (caso TAEE11).
                if reg.roe_sinal_invertido:
                    st.warning(
                        "⚠️ **Coeficiente do ROE saiu negativo** — isso *contraria* a teoria "
                        "(modelo de Gordon: o P/L justo cresce com o ROE). Em geral é sinal de "
                        "overfitting/multicolinearidade e acaba penalizando as empresas mais "
                        "rentáveis. Aqui o preço-alvo da regressão pode discordar do **Analisar "
                        "a fundo** (DDM); nesse caso, confie mais no DDM."
                    )
                # RANK-CONF-04 (AUD-CMP-02): R² baixo → regressão explica pouco do P/L do setor.
                if reg.r2_baixo:
                    st.warning(
                        f"⚠️ **R² baixo ({reg.r2:.2f}).** A regressão explica pouco da variação de "
                        f"P/L entre as comparáveis — o preço-alvo e o veredito *Subavaliada/Cara* "
                        f"são pouco confiáveis. Use comparáveis mais homogêneas (mesmo segmento) ou "
                        f"confie mais no **Analisar a fundo** (DDM)."
                    )
                # RANK-CONF-03: orientação fixa de mesmo segmento (sempre que há tabela).
                st.caption(
                    "ℹ️ Compare empresas do **mesmo segmento** (ex.: geração × transmissão × "
                    "distribuição de energia). Misturar segmentos distorce a regressão e o ranking."
                )
            else:
                st.info("Poucas empresas para a regressão (precisa de ≥4). Os preços-alvo ficam indisponíveis.")


# =========================================================================== #
# 4) SWING TRADE (ANÁLISE TÉCNICA) — MVP visual: candlestick intraday/diário
# =========================================================================== #
elif modo.startswith("📈"):
    st.subheader("Swing trade — leitura técnica do candlestick (intraday/diário)")
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

    # Gateia pelo ticker preenchido (não pelo retorno efêmero do botão): o gráfico persiste
    # entre reruns ao trocar de timeframe sem exigir novo clique.
    if ticker:
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
            # D-02: o gráfico usa o OHLC NOMINAL (f.ohlc), não o ajustado por split.
            fig = go.Figure(data=[go.Candlestick(
                x=f.ohlc.index,
                open=f.ohlc["Open"], high=f.ohlc["High"],
                low=f.ohlc["Low"], close=f.ohlc["Close"],
                name=ticker,
            )])
            fig.update_layout(
                height=520, margin=dict(l=10, r=10, t=30, b=10),
                xaxis_rangeslider_visible=False,
            )
            # D-04: a última barra pode estar em formação (viva) — sinaliza e mostra o atraso.
            if f.barra_viva and f.ultima_barra_ts is not None:
                fig.add_vline(x=f.ultima_barra_ts, line_width=1, line_dash="dot",
                              line_color="#888888")
            st.plotly_chart(fig, width="stretch")

            if f.barra_viva:
                atraso_txt = f" · atraso ~{f.atraso_min:.0f} min" if f.atraso_min is not None else ""
                st.caption(f"⏱️ Última barra possivelmente em formação (não fechada){atraso_txt}.")

            # Histórico insuficiente: <2 barras ⇒ sem barra fechada p/ leitura técnica (Fases 13+).
            if f.idx_ultima_fechada is None:
                st.warning("Histórico insuficiente — menos de duas barras fechadas neste timeframe.")
