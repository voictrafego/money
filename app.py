"""Interface web (Streamlit) do Analista de Dividendos.

Rode com:  ./.venv/bin/streamlit run app.py
Abre no navegador. Mesma engine do CLI, método do livro Orleans Martins & Felipe Pontes.
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analista import grafico
from analista.core import comparables as cmp
from analista.core import multiples as mult
from analista.core import screening as sc
from analista.glossario import h
from analista.ingest import build, macro
from analista.report import report

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
    ["🔎 Analisar uma ação", "⛏️ Garimpar carteira (BSD)", "📊 Ranking por múltiplos"],
    help=h("menu"),
)
st.sidebar.markdown("---")
st.sidebar.metric("Selic (corte do DY)", fmt_pct(selic_atual()), help=h("selic"))
st.sidebar.caption(f"Janela: {N_ANOS} anos · até {ANO_BASE} (quando já divulgado na CVM)")


# =========================================================================== #
# 1) ANALISAR UMA AÇÃO
# =========================================================================== #
if modo.startswith("🔎"):
    st.subheader("Analisar uma ação a fundo")
    col1, col2 = st.columns([3, 1])
    ticker = col1.text_input("Ticker da B3", value="TAEE11", placeholder="ex.: ITUB4, EGIE3, TAEE11",
                             help=h("ticker")).strip().upper()
    rodar = col2.button("Analisar", type="primary", use_container_width=True)

    if rodar and ticker:
        with st.spinner(f"Coletando dados de {ticker} (CVM + Yahoo)..."):
            c = montar(ticker, ANO_BASE, N_ANOS)
        if c is None or not c.anos:
            st.error(f"Não encontrei dados suficientes para {ticker}. "
                     "Confira o ticker ou adicione o mapeamento em data/ticker_map.json.")
        else:
            # FIX-03: injeta o rf do CAPM (Selic ao vivo) em CFG antes da engine. Reusa
            # selic_atual() — @st.cache_data garante UMA chamada de rede por execução,
            # compartilhada com a métrica da sidebar. app.py segue read-only: só injeta
            # input de config, não recalcula o método.
            CFG["capm"]["rf_local"] = selic_atual()
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
            m3.metric("Dividend Yield", fmt_pct(a.multiplos.get("DY")), help=h("dy"))
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

            # Gráfico de preço 5a + banda do valor intrínseco (DDM) — topo da aba, antes dos sub-tabs (D-03)
            st.markdown("**Evolução do preço (5 anos) vs. valor intrínseco**", help=h("valor_intrinseco"))
            serie = c.serie_precos
            if serie is None or len(serie) == 0:
                # D-05/GRAF-03: série indisponível → aviso sem quebrar a aba (espelha o aviso de preço atual)
                st.info(
                    "📉 Gráfico de preço indisponível agora (fonte Yahoo instável). Os fundamentos e o "
                    "valor intrínseco (DDM, dados CVM) abaixo seguem válidos."
                )
            else:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=serie.index, y=serie.values, mode="lines", name="Preço",
                    line=dict(color="#1f77b4", width=2),
                    hovertemplate="%{x|%d/%m/%Y}<br>R$ %{y:.2f}<extra></extra>",
                ))
                # D-01/D-02/D-06: banda horizontal plana entre vmin e vmax, só se o DDM calculou
                if a.vmin is not None and a.vmax is not None:
                    fig.add_hrect(
                        y0=a.vmin, y1=a.vmax, line_width=0, fillcolor="green", opacity=0.12,
                        annotation_text="Valor intrínseco (DDM)", annotation_position="top right",
                    )
                # Botões de período (range selector nativo do Plotly): 30 dias a 5 anos
                fig.update_xaxes(rangeselector=dict(
                    buttons=[
                        dict(count=30, label="30D", step="day", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(step="all", label="5A"),
                    ],
                    activecolor="#1f77b4", x=0, y=1.12,
                ))
                fig.update_layout(
                    height=400, margin=dict(l=10, r=10, t=50, b=10),
                    yaxis_title="R$", xaxis_title=None, showlegend=False,
                )
                st.plotly_chart(fig, width="stretch")

            # Controles técnicos consultivos (UI-03/UI-05): os widgets SÓ capturam estado em
            # st.session_state["tec_estado"] (mesmas chaves de grafico.estado_padrao()); o desenho
            # dos overlays/subpainéis a partir desse estado é o Plan 05. app.py segue read-only.
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
                    st.caption("Dois payouts: o do último ano e o usado no valuation (DDM).",
                               help=h("payout_dual"))
                    payout_ult = a.multiplos.get("DP (payout)")  # = c.payout(ult), último ano cru
                    payout_proj = c.payout_valuation()           # média 3a + clamp 1.0 (usado no DDM)
                    rows = []
                    for k, val in a.multiplos.items():
                        if k == "DP (payout)":
                            rows.append(("Payout (último ano)", fmt_pct(payout_ult)))
                            rows.append(("Payout p/ valuation (média 3a)", fmt_pct(payout_proj)))
                        elif k in ("ML", "ROE", "DY", "EY"):
                            rows.append((k, fmt_pct(val)))
                        else:
                            rows.append((k, fmt_num(val)))
                    st.dataframe(pd.DataFrame(rows, columns=["Múltiplo", "Valor"]),
                                 hide_index=True, use_container_width=True)
                with cmb:
                    st.markdown("**Crescimento e custo de capital (Cap. 14/16)**", help=h("tab_crescimento"))
                    st.dataframe(pd.DataFrame([
                        ("g histórico (CAGR lucro)", fmt_pct(a.g_historico)),
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
else:
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
                ML.append(mult.margem_liquida(c.lucro_liquido.get(u), c.vendas_liquidas.get(u)))
                ROE.append(c.roe_valuation())
                PL.append(mult.preco_lucro(c.preco_atual, lpa))
                EY.append(mult.earnings_yield(lpa, c.preco_atual))
                DP.append(c.payout_valuation())  # payout canônico (média 3a + clamp), igual ao Analisar
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
                # RANK-CONF-03: orientação fixa de mesmo segmento (sempre que há tabela).
                st.caption(
                    "ℹ️ Compare empresas do **mesmo segmento** (ex.: geração × transmissão × "
                    "distribuição de energia). Misturar segmentos distorce a regressão e o ranking."
                )
            else:
                st.info("Poucas empresas para a regressão (precisa de ≥4). Os preços-alvo ficam indisponíveis.")
