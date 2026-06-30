# Phase 16: Página Streamlit + Gráfico do Momento - Pattern Map

**Mapped:** 2026-06-30
**Files analyzed:** 1 modified (`app.py`), 3 read-only contracts reused as-is
**Analogs found:** 1 / 1 (exact in-file analog) + 3 reused-as-is modules

## Resumo

Fase 100% camada de render. O único arquivo **modificado** é `app.py` — o bloco swing MVP
(linhas 584–649) é **estendido**, não recriado. Os três módulos da engine
(`grafico.py`, `report/setup.py`, `core/indicators.py`) são **consumidos read-only** (zero
edição). O analog direto do código de figura novo é o bloco de gráfico da aba Analisar
(`app.py` ~262–344): mesmo molde `make_subplots` + `overlays_preco`/`subpaineis_ativos`/
`layout_subplots`, trocando só o trace de preço (LINHA → CANDLESTICK).

## File Classification

| Arquivo | Tipo | Role | Data Flow | Analog mais próximo | Match |
|---------|------|------|-----------|---------------------|-------|
| `app.py` (bloco swing ~584–649) | **MODIFY** | view / thin renderer | request-response (input→fetch→render) | `app.py` aba Analisar chart (~190–344) | exact (mesmo arquivo, mesmo molde) |
| `src/analista/grafico.py` | reuse as-is | report/render-spec (puro) | transform (sinais→specs) | — (já é o módulo a reusar) | n/a |
| `src/analista/report/setup.py` | reuse as-is | report/aggregator (puro) | transform (sinais→veredito) | — (contrato consumido) | n/a |
| `src/analista/core/indicators.py` | reuse as-is | core/engine (puro) | transform (OHLC→sinais) | — (contrato consumido) | n/a |

> **Read-only locked:** `app.py` é a única edição. `grafico.py`/`setup.py`/`indicators.py`
> são golden-pinned (283 testes verdes) — NÃO estender/parametrizar (a diferença LINHA vs
> CANDLESTICK vive só no trace, não nos specs).

## Pattern Assignments

### `app.py` — bloco swing estendido (view, request-response)

**Analog 1 (estrutura input/fetch/cache/degradação):** o próprio bloco MVP `app.py` L584–649.
**Analog 2 (figura make_subplots + overlays + subpainéis):** aba Analisar `app.py` L262–344.

#### Imports a adicionar (atualmente AUSENTES no topo do app.py)

`app.py` L16–22 importa `grafico`, `comparables`, `multiples`, `screening as sc`, `glossario.h`,
`ingest.build/macro`, `report.presentation/report`. **Faltam** os dois módulos que esta fase
precisa chamar pela primeira vez na UI:

```python
from analista.core import indicators        # calcular() — hoje só report.py:257 o chama
from analista.report import setup           # montar_setup() — hoje não é chamado em lugar nenhum
```
> Sem colisão: `sc` já é `screening`; `setup` é nome livre. `go`, `make_subplots`, `grafico`,
> `frame_intraday`, `_nonce_key`, `fmt_rs`, `esc_md`, `h` já estão importados/definidos (L12–92).

#### Cadeia de engine a "wire" (NOVO — coração da fase)

Espelha `report.py:257`, mas passando os DOIS frames (pivôs/S-R/Fib em escala NOMINAL coerente
com o candle nominal):

```python
sinais = indicators.calcular(f.ohlc_ajustado, CFG, ohlc_nominal=f.ohlc)   # SinaisTecnicos
sw     = setup.montar_setup(sinais, CFG)                                  # SetupSwing
```
> `montar_setup` degrada para `SetupSwing(grade="Sem setup", decomposicao=[])` quando o gate
> R:R falha (setup.py L164–177) — nunca levanta. O card DEVE tratar `decomposicao==[]`.

#### Estado isolado dos toggles (NOVO — D-03) — analog: `tec_estado` da Analisar (L198–199)

A Analisar faz `st.session_state.setdefault("tec_estado", grafico.estado_padrao())`. O swing
usa chave PRÓPRIA e default PRÓPRIO (NÃO `grafico.estado_padrao()`, que é tudo OFF):

```python
# Analog do padrão (app.py L198-199), com chave isolada e default que reflete D-02
st.session_state.setdefault("tec_estado_swing", {
    "tendencia": {"on": True, "tipo": "sma", "janelas": [20, 50, 200]},   # MMs ON
    "canais": {"donchian_on": False, "donchian_janela": 20, "bollinger_on": False},  # OFF
    "forca": {"on": True},                                                # ADX subpainel ON
    "momentum": {"rsi_on": True, "macd_on": True},                        # RSI/MACD ON
    "sr_on": True, "fib_on": True, "niveis_setup_on": True, "padroes_on": False,  # extras
})
est = st.session_state["tec_estado_swing"]
```
> As 4 primeiras chaves casam com o schema que `overlays_preco`/`subpaineis_ativos` esperam
> (mesmo de `estado_padrao()`). `sr_on/fib_on/niveis_setup_on/padroes_on` são EXTRAS lidos só
> pelo render do app.py (grafico.py os ignora).

#### Expander de toggles (NOVO) — analog: expander da Analisar (app.py L200–236)

Copiar o padrão do expander "⚙️ Indicadores técnicos" L200–236 (colunas + `st.toggle` gravando
direto em `est[...]`, com `help=h(...)`). Trocar título para "⚙️ Overlays", adicionar toggles
extras para `est["sr_on"]/["fib_on"]/["niveis_setup_on"]/["padroes_on"]`. Excerpt do molde:

```python
with st.expander("⚙️ Overlays", expanded=False):
    ct, cc, cf, cm = st.columns(4)
    with ct:
        st.markdown("**Tendência**", help=h("tec_mm"))
        est["tendencia"]["on"] = st.toggle("Médias móveis", value=est["tendencia"]["on"], help=h("tec_mm"))
        est["tendencia"]["tipo"] = st.radio("Tipo", ["sma", "ema"],
            index=0 if est["tendencia"]["tipo"] == "sma" else 1,
            format_func=str.upper, horizontal=True, help=h("tec_mm"))
        est["tendencia"]["janelas"] = st.multiselect("Janelas", [20, 50, 200],
            default=est["tendencia"]["janelas"], help=h("tec_cross"))
    # ... cc=Canais, cf=Força(ADX), cm=Momentum(RSI/MACD) — idêntico a L217-236
```
> Padrão "slot reservado no topo" (Analisar L190–193): usar `grafico_box = st.container()` ANTES
> do expander para o gráfico ler `est` já atualizado no MESMO rerun (toggle redesenha na hora).

#### Figura make_subplots candlestick + overlays + subpainéis (NOVO) — analog: Analisar L262–344

Molde EXATO da Analisar, trocando o trace LINHA (L268–272) por `go.Candlestick`:

```python
# layout + subplots: idêntico à Analisar L262-266
layout = grafico.layout_subplots(len(specs))
fig = make_subplots(rows=layout["rows"], cols=1, shared_xaxes=True,
                    row_heights=layout["row_heights"], vertical_spacing=0.03)
# Row 1: CANDLESTICK (no lugar do go.Scatter "Preço" da Analisar L268-272) — usa f.ohlc NOMINAL
fig.add_trace(go.Candlestick(x=f.ohlc.index, open=f.ohlc["Open"], high=f.ohlc["High"],
                             low=f.ohlc["Low"], close=f.ohlc["Close"], name=ticker), row=1, col=1)
fig.update_xaxes(rangeslider_visible=False, row=1, col=1)   # Pitfall 4 — rangeslider rouba altura
# Overlays: MESMO loop da Analisar L281-286
for ov in grafico.overlays_preco(est, sinais):
    fig.add_trace(go.Scatter(x=ov.serie.index, y=ov.serie.values, mode="lines",
                             name=ov.nome, line=dict(ov.estilo)), row=1, col=1)
```

Subpainéis RSI/MACD/ADX — **copiar verbatim** o loop da Analisar L306–327 (MACD-Histograma como
`go.Bar` colorido verde≥0/vermelho<0; demais como `go.Scatter`; `add_hline` por referência;
`update_yaxes(title_text=spec.nome.upper(), row=r)`):

```python
# Source: app.py L306-327 (reuso direto)
for i, spec in enumerate(specs):
    r = i + 2
    for rotulo, s in spec.series:
        if rotulo == "Histograma":
            fig.add_trace(go.Bar(x=s.index, y=s.values, name=rotulo,
                marker_color=["#2ca02c" if (v is not None and v >= 0) else "#d62728" for v in s.values]),
                row=r, col=1)
            continue
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=rotulo), row=r, col=1)
    for ref in spec.referencias:
        fig.add_hline(y=ref, line_width=1, line_dash="dot", line_color="#aaaaaa", row=r, col=1)
    fig.update_yaxes(title_text=spec.nome.upper(), row=r, col=1)
```

`update_layout` / `st.plotly_chart`: copiar Analisar L339–344
(`height=400 + 140*len(specs)`, `legend=dict(orientation="h", y=1.02)`, `st.plotly_chart(fig, width="stretch")`).

#### Zonas S/R + níveis (NOVO, sem analog em grafico.py) — molde `add_hrect`/`add_hline` da Analisar

A Analisar já usa `add_hrect` para a banda DDM (L275–279) e `add_hline` nos subpainéis. Reusar
essas APIs para S/R (bandas) e setup/Fib (linhas), lendo `sinais.niveis.*` e `sw.*`:

```python
# Molde add_hrect: app.py L275-279 (banda DDM) → zonas S/R
if est["sr_on"] and sinais.niveis is not None:
    for (lo, hi) in sinais.niveis.suportes:       # list[(low,high)] — bandas, nunca pontos
        fig.add_hrect(y0=lo, y1=hi, line_width=0, fillcolor="green", opacity=0.08, row=1, col=1)
    for (lo, hi) in sinais.niveis.resistencias:
        fig.add_hrect(y0=lo, y1=hi, line_width=0, fillcolor="red", opacity=0.08, row=1, col=1)
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
```
> Copy dos rótulos NEUTRA ("zona de entrada (estudo)"/"stop (estudo)"/"alvo (estudo)") — gate
> SWING-02. Nunca "alvo de compra". Ver Shared Pattern "Copy não-imperativa".

#### Anotação de padrões (NOVO, Claude's Discretion CHART-01) — `add_shape`/`add_annotation`/`add_hline`

OFF por padrão (`est["padroes_on"]`). Lê `sinais.padroes.lista` (PadraoGrafico:
tipo/estado/neckline/alvo/altura/pivos_envolvidos). Cores espelham `setup._PADROES_ALTA/_BAIXA`
(setup.py L57–58: duplo_fundo/oco_invertido=verde; duplo_topo/oco=vermelho). Neckline horizontal
(`add_shape` line entre `ts[0]` e `ts[-1]`), rótulo "em formação"/"confirmado" (`add_annotation`),
alvo measured-move (`add_hline` "alvo (projeção de estudo)"). Reta inclinada da OCO deferida.

#### Barra viva (REUSO — já no MVP, app.py L636–644)

```python
# Source: app.py L637-644 — manter como está; iloc[-1] é cosmético (no-repaint preservado)
if f.barra_viva and f.ultima_barra_ts is not None:
    fig.add_vline(x=f.ultima_barra_ts, line_width=1, line_dash="dot", line_color="#888888", row=1, col=1)
# selo de atraso (D-08)
if f.barra_viva:
    atraso_txt = f" · atraso ~{f.atraso_min:.0f} min" if f.atraso_min is not None else ""
    st.caption(f"⏱️ Última barra possivelmente em formação (não fechada){atraso_txt}.")
```

#### Card de veredito (NOVO, abaixo do gráfico — D-01/D-04/D-05) — lê `sw` + `sinais.checklist`

Sem analog 1:1 (a Analisar tem veredito fundamentalista, não swing). Padrão: markdown/tabela,
NUNCA `st.metric` para níveis (Pitfall 5). Lê read-only:
- Grade + score em destaque (`sw.grade`, `sw.score`).
- Barra de contribuição por família: iterar `sw.decomposicao` (`ContribFamilia.familia/
  contribuicao/peso/detalhe`); tratar `[]` → "Sem confluência suficiente para um setup de estudo".
- Checklist: iterar `sinais.checklist.sinais` (`Sinal.nome/ativo/detalhe`) → lista ✓/✗ (D-05).
- Tabela "Referências de estudo (não são ordens)" com entrada-zona/stop/alvo/R:R
  (`sinais.niveis.risco_retorno` já vem formatado BR "1 : 2,5"; usar `fmt_rs` para preços).
- Disclaimer condicional inline.

## Degradação graciosa (REUSO — analog: Analisar L246–251 + MVP L613–648)

**Gate da página:** renderizar candlestick+S/R+Fib+veredito SEMPRE que `f.disponivel` (Pitfall 1
— NÃO gatear tudo por `leitura_tecnica_disponivel`). Reusar o bloco `f.disponivel is False` →
`st.error(_MSG_MOTIVO...)` já no MVP (L613–623) e o `st.warning` de histórico insuficiente
(L646–648). Para série/overlay indisponível, espelhar o `st.info` da Analisar (L248–251).
`overlays_preco`/`subpaineis_ativos` já pulam série toda-NaN sozinhos (grafico.py L80–83, L165–176).

## Shared Patterns

### Cache targetado (REUSO — não reimplementar)
**Source:** `app.py` L53–69 (`frame_intraday` `@st.cache_data(ttl=300)` + `_nonce_key`)
**Apply to:** fetch do candlestick + botão Atualizar. Botão faz `st.session_state[k] += 1`
(MVP L602–605). **NUNCA `st.cache_data.clear()` global** (apagaria cache de
`montar`/`selic_atual`/`rf_capm` da Analisar — D-08).

### Read-only / thin renderer (REGRA travada desde Phase 2)
**Source:** `grafico.py` L1–11 (docstring), `setup.py` L8–14, app.py inteiro
**Apply to:** todo o bloco swing. A UI só LÊ campos de dataclasses (`SinaisTecnicos`/`SetupSwing`/
`FrameOHLC`); zero recálculo de método. Qualquer cálculo na UI viola a regra e arrisca divergir
dos goldens.

### Copy não-imperativa (gate de aceite SWING-02)
**Source:** `setup.py` L13–14 (princípio) + `test_setup_report.py::test_setup_sem_copy_imperativa`
**Apply to:** toda copy que a UI adiciona (rótulos de níveis, anotações Plotly, card). Proibido:
`compre/venda/comprar/vender/entre/recomend/sugiro/indico`. Usar "estudo"/"referência"/
"em formação"/"projeção". Níveis sempre "Referências de estudo (não são ordens)".

### Helpers de formatação BR (REUSO)
**Source:** `app.py` L77–92 — `fmt_rs(x)` (R$ BR, None→"—"), `fmt_pct`, `fmt_num`,
`esc_md(s)` (escapa `$` p/ markdown/metric).
**Apply to:** preços do card de veredito e tabela de níveis.

## No Analog Found

| Elemento | Role | Razão | Mitigação |
|----------|------|-------|-----------|
| Card de veredito swing (grade/score/decomposição/checklist) | view | A Analisar só tem veredito fundamentalista (estrutura diferente) | Usar markdown/tabela seguindo RESEARCH §Code Examples `_render_veredito`; NUNCA `st.metric` p/ níveis |
| Anotação de padrões no candle (neckline/rótulo/alvo) | view | grafico.py não cobre; CHART-01 é Claude's Discretion | Seguir RESEARCH Q2 (add_shape horizontal + add_annotation + add_hline); reta OCO inclinada deferida |
| Zonas S/R como `add_hrect` + Fib `add_hline` | view | grafico.py devolve só overlays MM/Donchian/Bollinger | Molde `add_hrect` da banda DDM (Analisar L275–279) lendo `sinais.niveis.suportes/resistencias/fib_retracoes` |

## Metadata

**Analog search scope:** `app.py` (bloco Analisar L190–344, bloco swing MVP L580–649, helpers
L53–92), `src/analista/grafico.py` (completo), `src/analista/report/setup.py` (L1–60, L161–190),
`src/analista/core/indicators.py` (contratos via RESEARCH, verificados).
**Files scanned:** 4
**Pattern extraction date:** 2026-06-30
