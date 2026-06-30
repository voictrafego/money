# Phase 16: Página Streamlit + Gráfico do Momento - Research

**Researched:** 2026-06-30
**Domain:** Streamlit/Plotly thin-renderer UI sobre engine técnica já existente (candlestick + overlays + subpainéis + veredito de setup)
**Confidence:** HIGH (todos os contratos lidos diretamente do código-fonte; APIs Plotly confirmadas pelo próprio `app.py` em produção)

## Summary

Esta fase é **100% camada de render**. Toda a lógica (indicadores, pivôs, S/R, Fibonacci, padrões, score, grade, R:R, checklist) já existe e está golden-testada (283 testes verdes). O 4º menu **já existe** em `app.py` (linhas 582–649) como MVP visual: candlestick intraday + seletor de timeframe + botão Atualizar + selo de atraso + marcação da barra viva. Phase 16 **estende esse bloco existente** — não cria página nova do zero — adicionando: overlays toggleáveis (MMs/Donchian/Bollinger/S-R/Fibonacci/padrões), subpainéis RSI/MACD/ADX, e o card de veredito (score/grade/decomposição/checklist/níveis), tudo lido read-only de `SetupSwing` + `SinaisTecnicos`.

A cadeia de engine que a página precisa montar (read-only, zero recálculo):
```python
f = frame_intraday(ticker, tf_key, st.session_state[k])          # FrameOHLC (cache TTL 300s + nonce) — JÁ EXISTE
sinais = indicators.calcular(f.ohlc_ajustado, CFG, ohlc_nominal=f.ohlc)   # SinaisTecnicos — A WIRE
setup  = setup.montar_setup(sinais, CFG)                          # SetupSwing — A WIRE
```
`indicators.calcular` e `montar_setup` **ainda não são chamados** no bloco swing do `app.py` (a única chamada de `calcular` hoje é em `report.py:257`, e `montar_setup` não é chamado em lugar nenhum). Wire-las é o coração desta fase.

**Primary recommendation:** Reusar DIRETAMENTE as três funções puras de `grafico.py` (`overlays_preco`, `subpaineis_ativos`, `layout_subplots`) alimentando-as com o `SinaisTecnicos` do frame swing + um dicionário de estado PRÓPRIO da página (`tec_estado_swing`, isolado do `tec_estado` da aba Analisar). O candlestick (`go.Candlestick`), as zonas S/R (`add_hrect`), os níveis Fibonacci/setup (`add_hline`) e a anotação de padrões (`add_shape`/`add_annotation`) são código de render NOVO no bloco swing do `app.py`, espelhando o molde `make_subplots` da aba Analisar (linhas 263–344). NÃO estender/parametrizar `grafico.py` (golden-pinned; LINHA vs CANDLESTICK é diferença só de trace, não de spec).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fetch OHLCV intraday + cache | Ingest (`intraday.coletar_intraday`) | UI wrapper (`frame_intraday` @cache_data) | Já isolado do pipeline diário; nonce dá invalidação targetada |
| Cálculo de indicadores/pivôs/níveis/padrões | Core (`indicators.calcular`) | — | Engine pura golden-testada; UI só consome |
| Score/grade/decomposição/R:R-gate | Report (`setup.montar_setup`) | — | Agregador read-only; firewall vs `report.py` |
| Decisão de QUAIS overlays/subpainéis desenhar | Report/Core puro (`grafico.py`) | UI render | Spec golden-pinned; sem plotly/streamlit |
| Render candlestick + S/R + Fib + padrões + veredito | UI (`app.py` bloco swing) | — | Plotly/Streamlit; verificação é visual (humano no navegador) |
| Copy/disclaimer condicional "exibe, nunca recomenda" | UI (`app.py`) | — | Gate de aceite SWING-02; copy mora na borda |

## Standard Stack

### Core (zero novas dependências — REQUIREMENTS exige)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | 1.58.0 | UI web read-only | Já é a UI do app inteiro [VERIFIED: `.venv` import] |
| plotly | 6.8.0 | Candlestick + subplots + shapes/annotations | Já usado em `app.py` (make_subplots, add_hrect, add_hline, add_vline, go.Candlestick) [VERIFIED] |
| pandas | 3.0.3 | Séries OHLC e índices temporais | Já no stack [VERIFIED] |

**Installation:** Nenhuma. `Zero novas dependências de runtime` é requisito travado (REQUIREMENTS.md §Arquitetura). Tudo sobre `pandas/numpy/scipy/yfinance/plotly/streamlit` já instalados.

**Version verification:**
```
plotly 6.8.0 · streamlit 1.58.0 · pandas 3.0.3  [VERIFIED: ./.venv/bin/python import 2026-06-30]
```

## Architecture Patterns

### System Architecture Diagram

```
[input ticker] ─┐
[selectbox TF] ─┼──> frame_intraday(ticker, tf, nonce)  ──> FrameOHLC
[botão Atualizar→nonce++]      (@st.cache_data ttl=300)        │  .ohlc (nominal)
                                                                │  .ohlc_ajustado (split-adj)
                                                                │  .barra_viva / .ultima_barra_ts / .atraso_min
                                                                │  .idx_ultima_fechada / .disponivel / .motivo
                                                                ▼
        indicators.calcular(ohlc_ajustado, CFG, ohlc_nominal=ohlc) ──> SinaisTecnicos
                                                                │  tendencia/canais/forca/momentum (séries+rótulos)
                                                                │  niveis (suportes/resistencias/entrada_zona/fib/alvo/stop/rr)
                                                                │  padroes.lista[PadraoGrafico] / checklist.sinais[Sinal]
                                                                ▼
                          setup.montar_setup(sinais, CFG) ──> SetupSwing
                                                                │  score/grade/decomposicao[ContribFamilia]
                                                                │  gate_rr_ok/rr_valor/conflito_mtf/entrada_zona/stop/alvo
                                                                ▼
        ┌───────────────────────── RENDER (app.py bloco swing) ─────────────────────────┐
        │  controles: expander "⚙️ Overlays" → tec_estado_swing (dict ISOLADO)           │
        │  fig = make_subplots(rows=1+n_subpaineis, shared_xaxes=True)                    │
        │   row1: go.Candlestick(f.ohlc) + overlays_preco(estado,sinais)                  │
        │         + add_hrect(S/R zones) + add_hline(fib/entrada/stop/alvo)               │
        │         + add_shape/add_annotation(padrões) + add_vline(barra viva)             │
        │   rows2+: subpaineis_ativos(estado,sinais)  [RSI/MACD/ADX, MACD-hist=go.Bar]    │
        │  veredito: grade+score · barra de contribuição (decomposicao) · checklist ·     │
        │            tabela "Referências de estudo (não são ordens)" · disclaimer inline  │
        └────────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Structure (onde o código vive)
```
app.py
└── elif modo.startswith("📈"):     # bloco swing JÁ EXISTE (584–649) → ESTENDER aqui
     ├── input ticker + selectbox TF + botão Atualizar (nonce)   # já implementado
     ├── f = frame_intraday(...)                                  # já implementado
     ├── sinais = indicators.calcular(f.ohlc_ajustado, CFG, ohlc_nominal=f.ohlc)  # NOVO
     ├── setup  = setup.montar_setup(sinais, CFG)                 # NOVO
     ├── st.session_state.setdefault("tec_estado_swing", {...})   # NOVO (dict isolado)
     ├── expander "⚙️ Overlays" → widgets sobre tec_estado_swing  # NOVO
     ├── make_subplots candlestick + overlays + S/R + fib + padrões + subpainéis  # NOVO
     └── card de veredito (score/grade/decomposição/checklist/níveis/disclaimer)  # NOVO
```
Nenhum módulo novo é obrigatório. `grafico.py` (`src/analista/grafico.py`) é reusado as-is.

### Pattern 1: Cadeia de engine read-only (espelha report.py:257)
**What:** Montar `SinaisTecnicos` e `SetupSwing` a partir do `FrameOHLC`, passando os DOIS frames.
**When:** Sempre que `f.disponivel is True`.
**Example:**
```python
# Source: indicators.calcular() docstring L1233-1236 + setup.montar_setup() L161
# ohlc_ajustado → indicadores/contexto (split-adj); ohlc (nominal) → família de PREÇO (pivôs/S-R/Fib) — D-02
sinais = indicators.calcular(f.ohlc_ajustado, CFG, ohlc_nominal=f.ohlc)
setup  = setup.montar_setup(sinais, CFG)   # lê CFG["score"]; degrada p/ "Sem setup", nunca levanta
```
> `report.py:257` chama `indicators.calcular(ohlc, cfg)` SEM `ohlc_nominal` (aba Analisar, diário). A página swing DEVE passar `ohlc_nominal=f.ohlc` para que pivôs/S-R/Fibonacci fiquem em preço NOMINAL, coerentes com o candlestick nominal (`f.ohlc`).

### Pattern 2: make_subplots candlestick + subpainéis (molde Analisar 263–344)
**What:** Reusar o molde exato da aba Analisar, trocando o trace de preço LINHA por CANDLESTICK.
**Example:**
```python
# Source: app.py L262-344 (aba Analisar) adaptado p/ candlestick
layout = grafico.layout_subplots(len(specs))          # reuso direto (rows + row_heights)
fig = make_subplots(rows=layout["rows"], cols=1, shared_xaxes=True,
                    row_heights=layout["row_heights"], vertical_spacing=0.03)
fig.add_trace(go.Candlestick(x=f.ohlc.index, open=f.ohlc["Open"], high=f.ohlc["High"],
                             low=f.ohlc["Low"], close=f.ohlc["Close"], name=ticker),
              row=1, col=1)
fig.update_xaxes(rangeslider_visible=False, row=1, col=1)   # rangeslider quebra make_subplots
# overlays (MMs/Donchian/Bollinger) — MESMO loop da Analisar L281-286
for ov in grafico.overlays_preco(estado, sinais):
    fig.add_trace(go.Scatter(x=ov.serie.index, y=ov.serie.values, mode="lines",
                             name=ov.nome, line=dict(ov.estilo)), row=1, col=1)
# subpainéis RSI/MACD/ADX — MESMO loop da Analisar L306-327 (MACD-hist como go.Bar colorido)
```
**Anti-patterns to avoid:**
- **Não usar `go.Figure` single-panel** (como o MVP atual L626) se quiser subpainéis — RSI/MACD/ADX precisam de `make_subplots` com rows próprias.
- **Não setar `xaxis_rangeslider_visible`** no candlestick dentro de make_subplots — o rangeslider rouba altura das rows; o MVP atual desliga com `xaxis_rangeslider_visible=False` (L634); no make_subplots use `fig.update_xaxes(rangeslider_visible=False, row=1, col=1)`.
- **Não recalcular método na UI** — só LER campos das dataclasses (regra `app.py` read-only, locked desde Phase 2).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Candlestick | desenhar barras OHLC manuais | `go.Candlestick(x,open,high,low,close)` | Nativo Plotly, já no MVP L626 |
| Layout de subplots (preço dominante + osciladores) | calcular row_heights na mão | `grafico.layout_subplots(n)` | golden-pinned (preço 0.55, resto proporcional) |
| Decidir quais MMs/canais desenhar do estado | mapear nome→série no app.py | `grafico.overlays_preco(estado, sinais)` | golden-pinned; já trata estado parcial e séries NaN |
| Subpainéis RSI/MACD/ADX + níveis de ref | hardcodar 30/70, 20/25, 0 | `grafico.subpaineis_ativos(estado, sinais)` | golden-pinned; pula série toda-NaN (degradação) |
| Score/decomposição/grade/R:R-gate | recomputar na UI | `setup.montar_setup(sinais, CFG)` | golden-testado; firewall vs report.py |
| Níveis S/R/Fib/stop/alvo/R:R | calcular geometria na UI | `sinais.niveis.*` (já em `calcular`) | golden-testado, no-repaint via iloc[-2] |
| R:R formatado BR | formatar razão na UI | `sinais.niveis.risco_retorno` ("1 : 2,5") | já formatado com vírgula BR / "indisponivel" |
| Invalidação de cache do botão Atualizar | `st.cache_data.clear()` global | nonce por `(ticker, tf)` via `frame_intraday` | clear global apagaria o cache da aba Analisar (D-08) |
| Moeda R$ | format string na mão | `fmt_rs(x)` (app.py L85) | trata separador BR + None→"—" |

**Key insight:** A engine já entrega TODOS os números prontos e golden-pinados. O único trabalho desta fase é converter dataclasses em traces Plotly e markdown Streamlit. Qualquer cálculo na UI viola a regra read-only e arrisca divergência com os goldens.

## Research Questions — Respostas Concretas

### Q1 — Reuso vs extensão de `grafico.py` (RECOMENDAÇÃO: reusar as 3 funções puras as-is; render novo no app.py)

**Caminho real do módulo:** `src/analista/grafico.py` (NÃO `src/analista/report/grafico.py` como o CONTEXT supôs). Importado em `app.py` como `from analista import grafico`. [VERIFIED: leitura do arquivo + app.py L16]

**Assinaturas reais (todas PURAS — sem streamlit/plotly, devolvem specs/dados):**
| Função | Assinatura | Devolve | Reuso na swing? |
|--------|-----------|---------|------------------|
| `overlays_preco(estado, sinais)` | `(dict\|None, SinaisTecnicos) → List[OverlaySpec]` | linhas MM/Donchian/Bollinger (lê `sinais.tendencia`/`sinais.canais`) | **SIM, direto** |
| `subpaineis_ativos(estado, sinais)` | `(dict\|None, SinaisTecnicos) → List[SubpainelSpec]` | ordem fixa `["adx","rsi","macd"]`; só toggles ON c/ série válida | **SIM, direto** |
| `layout_subplots(n_subpaineis)` | `(int) → {"rows":int,"row_heights":[...]}` | preço 0.55 + resto proporcional | **SIM, direto** |
| `marcadores_eventos(sinais, close)` | `(SinaisTecnicos, pd.Series) → List[Marcador]` | golden/death cross + rompimento Donchian | OPCIONAL (off no MVP — clutter intraday; D-02 não pede) |
| `leitura_tecnica_disponivel(sinais)` | `(SinaisTecnicos) → bool` | False se `posicao_mm200=="indisponivel"` | usar só p/ gatear OVERLAYS de MM, **não a página inteira** |
| `estado_padrao()` | `() → dict` | tudo OFF | **NÃO usar** — criar default próprio swing (ver abaixo) |

**Specs (dataclasses puras que o app.py converte em traces):**
- `OverlaySpec(nome:str, serie:pd.Series, estilo:dict)` — vira `go.Scatter(row=1)`.
- `SubpainelSpec(nome:str, series:List[Tuple[str,pd.Series]], referencias:List[float])` — vira linhas + `add_hline` numa row própria.

**Por que reusar e NÃO estender:** essas funções são **agnósticas de timeframe e de tipo de trace** — leem só rótulos/séries do `SinaisTecnicos`. A diferença LINHA (Analisar) vs CANDLESTICK (swing) está **só no trace do preço**, que o `app.py` desenha, não no spec. Estendê-las (ex.: flag `candlestick=True`) misturaria responsabilidade de render num módulo de spec golden-pinned (`test_grafico_ui.py` trava o comportamento atual). [VERIFIED: test_grafico_ui.py existe e trava overlays/subpainéis/marcadores]

**O que NÃO é coberto por `grafico.py` (render novo no bloco swing):**
1. `go.Candlestick` do `f.ohlc` (nominal).
2. Zonas S/R como bandas → `add_hrect` lendo `sinais.niveis.suportes`/`.resistencias` (listas de `(low,high)`).
3. Níveis Fibonacci/entrada/stop/alvo → `add_hline` lendo `sinais.niveis.entrada_zona`/`.fib_retracoes`/`.stop`/`.alvo` (ou `setup.entrada_zona/stop/alvo`).
4. Anotação de padrões → `add_shape`+`add_annotation` lendo `sinais.padroes.lista` (ver Q2).
5. Barra viva → `add_vline` (ver Q3).

**Estado isolado (D-03):** NÃO reusar `grafico.estado_padrao()` (tudo OFF) nem o `tec_estado` da Analisar. Criar dict próprio, ex.:
```python
st.session_state.setdefault("tec_estado_swing", {
    "tendencia": {"on": True, "tipo": "sma", "janelas": [20, 50, 200]},   # MMs ON (D-02)
    "canais": {"donchian_on": False, "donchian_janela": 20, "bollinger_on": False},  # OFF (D-02)
    "forca": {"on": True},          # ADX subpainel ON (CHART-01 pede RSI/MACD/ADX)
    "momentum": {"rsi_on": True, "macd_on": True},
    # chaves PRÓPRIAS p/ overlays que grafico.py não conhece (render lê direto):
    "sr_on": True, "fib_on": True, "niveis_setup_on": True, "padroes_on": False,  # D-02
})
```
> As chaves `tendencia/canais/forca/momentum` casam com o que `overlays_preco`/`subpaineis_ativos` esperam (mesmo schema de `estado_padrao()`). As chaves `sr_on/fib_on/niveis_setup_on/padroes_on` são EXTRAS lidos só pelo render do app.py (grafico.py as ignora).

### Q2 — Anotação visual de padrões no candlestick

**Contrato `PadraoGrafico`** (lido de `sinais.padroes.lista`): [VERIFIED: indicators.py L137-146]
| Campo | Tipo | Conteúdo |
|-------|------|----------|
| `tipo` | str | `"duplo_topo"`/`"duplo_fundo"`/`"oco"`/`"oco_invertido"` |
| `estado` | str | `"em_formacao"`/`"confirmado"` |
| `neckline` | float | linha de pescoço (no duplo é horizontal; na OCO é o valor extrapolado à barra de rompimento) |
| `alvo` | float | measured-move (altura projetada além da neckline) |
| `altura` | float | base da projeção |
| `pivos_envolvidos` | dict | `{Timestamp: preco}` dos pivôs âncora (2 no duplo, 5 na OCO) |

**Como desenhar (Plotly — APIs confirmadas pelo uso em app.py):**
```python
# Cores por direção (espelha setup._PADROES_ALTA/_BAIXA L57-58)
COR_PAD = {"duplo_fundo": "#2ca02c", "oco_invertido": "#2ca02c",   # alta = verde
           "duplo_topo": "#d62728", "oco": "#d62728"}              # baixa = vermelho
for p in sinais.padroes.lista:
    ts = sorted(p.pivos_envolvidos)            # timestamps âncora ordenados
    cor = COR_PAD.get(p.tipo, "#888888")
    dash = "solid" if p.estado == "confirmado" else "dot"
    # 1) Neckline limitada ao span do padrão (add_shape line — mais limpo que add_hline full-width)
    fig.add_shape(type="line", x0=ts[0], x1=ts[-1], y0=p.neckline, y1=p.neckline,
                  line=dict(color=cor, width=1.5, dash=dash), row=1, col=1)
    # 2) Rótulo "em formação"/"confirmado"
    rotulo = {"em_formacao": "em formação", "confirmado": "confirmado"}[p.estado]
    fig.add_annotation(x=ts[-1], y=p.neckline, text=f"{p.tipo.replace('_',' ')} · {rotulo}",
                       showarrow=False, yshift=12, font=dict(color=cor, size=10), row=1, col=1)
    # 3) Alvo measured-move (linha pontilhada + anotação "projeção")
    fig.add_hline(y=p.alvo, line_width=1, line_dash="dot", line_color=cor,
                  annotation_text="alvo (projeção de estudo)", annotation_position="right",
                  row=1, col=1)
    # 4) Marcar os pivôs âncora
    fig.add_trace(go.Scatter(x=list(p.pivos_envolvidos), y=list(p.pivos_envolvidos.values()),
                             mode="markers", marker=dict(symbol="circle-open", color=cor, size=9),
                             showlegend=False, hoverinfo="skip"), row=1, col=1)
```
**Notas de legibilidade / honestidade:**
- Para OCO a neckline real é INCLINADA; o dataclass expõe só `neckline` (float no ponto de rompimento). Uma `add_shape` horizontal é uma **simplificação honesta** para o MVP. Se quiser a reta inclinada, dá pra reconstruí-la dos 2 fundos (OCO) / 2 topos (OCO invertido) em `pivos_envolvidos` — mas isso exige distinguir quais entradas são os fundos vs ombros (a ordem do dict é `{LS, F1, cabeça, F2, RS}`). **Recomendação: horizontal no MVP** (deferir reta inclinada).
- Padrões DESLIGADOS por padrão (D-02) — só desenhar quando `tec_estado_swing["padroes_on"]`.
- A copy do rótulo deve ser NEUTRA ("em formação"/"confirmado"/"projeção de estudo") — NUNCA "alvo de compra" (gate SWING-02).

### Q3 — Marcação da barra viva (no-repaint preservado)

**Já implementado no MVP atual** (app.py L636-644) e é o padrão correto:
```python
# Source: app.py L637-639 — barra viva via add_vline
if f.barra_viva and f.ultima_barra_ts is not None:
    fig.add_vline(x=f.ultima_barra_ts, line_width=1, line_dash="dot", line_color="#888888", row=1, col=1)
# opcional: anotação textual
fig.add_annotation(x=f.ultima_barra_ts, y=f.ohlc["High"].iloc[-1], text="em formação",
                   showarrow=False, yshift=10, font=dict(size=9, color="#888"), row=1, col=1)
# caption de atraso (app.py L642-644)
if f.barra_viva:
    atraso = f" · atraso ~{f.atraso_min:.0f} min" if f.atraso_min is not None else ""
    st.caption(f"⏱️ Última barra possivelmente em formação (não fechada){atraso}.")
```
**Garantia de no-repaint:** TODOS os sinais/níveis/padrões da engine leem a **barra FECHADA** via `iloc[-2]` (`idx_ultima_fechada = len-2`) — confirmado em `_dow`/`_volume`/`_padroes`/`_niveis_sr`/`_niveis_stop_rr` (todos usam `iloc[-2]`/`close_f = Close.iloc[-2]`). [VERIFIED: indicators.py L717, L909, L1154; intraday.py L111] A barra viva (`iloc[-1]`) é **puramente cosmética** — marcá-la NÃO altera nenhum sinal. **Regra:** nunca desenhar um nível/marcador derivado de `iloc[-1]`. A `add_vline` em `ultima_barra_ts` é a marcação correta e segura.

### Q4 — Contratos reais já existentes no app.py (para reusar sem reinventar)

**`frame_intraday(ticker, timeframe, nonce)`** — app.py L53-63, `@st.cache_data(ttl=300)`:
- Retorna `FrameOHLC` (intraday.py L48-58). Campos lidos pela UI: [VERIFIED]
  | Campo | Tipo | Uso na render |
  |-------|------|----------------|
  | `disponivel` | bool | gate: `if f.disponivel is False` → `st.error` por motivo |
  | `motivo` | str | `""`/`"timeframe_invalido"`/`"sem_dados"`/`"fetch_falhou"`/`"historico_insuficiente"` → copy amigável (app.py L615-623) |
  | `ohlc` | `pd.DataFrame\|None` | **NOMINAL** — colunas `Open/High/Low/Close/Volume` → candlestick + `ohlc_nominal` p/ calcular |
  | `ohlc_ajustado` | `pd.DataFrame\|None` | split-adjusted → 1º arg de `indicators.calcular` |
  | `ultima_barra_ts` | `pd.Timestamp\|None` | `add_vline` da barra viva |
  | `barra_viva` | bool | True = última barra suspeita (sempre, conservador) |
  | `idx_ultima_fechada` | `int\|None` | `len-2`; None se <2 barras → "histórico insuficiente" |
  | `atraso_min` | `float\|None` | selo "~X min" |
  | `timeframe` | str | echo |
- Invalidação: `_nonce_key(ticker, tf)` (L66-69) + `st.session_state.setdefault(k,0)`; botão Atualizar faz `st.session_state[k]+=1` (L604-605). **NUNCA `.clear()` global** (apagaria cache de `montar`/`selic_atual`/`rf_capm` da Analisar — D-08).
- Timeframes válidos: `_TF_MAP = {"Diário":"diario","1h":"1h","30m":"30m","5m":"5m"}` (app.py L595); tetos Yahoo: diário 5y, 1h≤730d, 30m/5m≤60d (intraday.py L32-37).

**Molde `make_subplots` da aba Analisar** — app.py L262-344:
- `layout = grafico.layout_subplots(len(specs))`; `make_subplots(rows=layout["rows"], cols=1, shared_xaxes=True, row_heights=layout["row_heights"], vertical_spacing=0.03)`.
- Row 1 = trace de preço + overlays (`for ov in overlays: add_trace(go.Scatter(... line=dict(ov.estilo)), row=1)`).
- Banda de referência via `add_hrect(y0,y1, fillcolor, opacity=0.12, annotation_text=..., row=1)` (L275) — molde direto p/ zonas S/R.
- Subpainéis: `for i,spec in enumerate(specs): r=i+2; ... ` — MACD-`Histograma` como `go.Bar` colorido verde≥0/vermelho<0 (L312-318), demais como `go.Scatter`; `for ref in spec.referencias: add_hline(y=ref, line_dash="dot", row=r)`; `update_yaxes(title_text=spec.nome.upper(), row=r)`.
- `update_layout(height=400+140*len(specs), margin=..., showlegend=bool(overlays or specs), legend=dict(orientation="h", y=1.02))`.
- `st.plotly_chart(fig, width="stretch")`.

**Helpers reusáveis:** `fmt_rs(x)` (R$ BR, None→"—", L85), `fmt_pct`, `fmt_num`, `esc_md(s)` (escapa `$` p/ markdown/metric — L89), `h("chave")` (glossário/tooltip).

### Q5 — Campos exatos que a UI vai LER (read_first / acceptance_criteria)

**`SetupSwing`** (`report/setup.py` L41-53): [VERIFIED]
| Campo | Tipo | Default | Conteúdo |
|-------|------|---------|----------|
| `score` | float | — | 0–100, já com penalização multi-TF |
| `grade` | str | — | `"Forte"`/`"Moderado"`/`"Fraco"`/`"Sem setup"` |
| `decomposicao` | `list[ContribFamilia]` | `[]` | barra de contribuição (D-04); VAZIA quando gate falha/"Sem setup" |
| `gate_rr_ok` | bool | False | passou no gate de R:R |
| `rr_valor` | `float\|None` | None | razão retorno/risco recomputada |
| `conflito_mtf` | bool | False | penalização multi-TF aplicada (D-07) |
| `entrada_zona` | `tuple\|None` | None | `(low, high)` — zona, NUNCA ponto/ordem |
| `stop` | `float\|None` | None | stop técnico de estudo |
| `alvo` | `float\|None` | None | alvo measured-move/Fibonacci |

**`ContribFamilia`** (`report/setup.py` L30-38) — cada item de `decomposicao`: [VERIFIED]
| Campo | Tipo | Conteúdo |
|-------|------|----------|
| `familia` | str | `"tendencia"`/`"risco_retorno"`/`"padroes"`/`"momentum"`/`"volume"` |
| `sub_score` | float | ∈ [0,1] leitura crua da família |
| `peso` | int | 35/20/20/15/10 (do config) |
| `contribuicao` | float | `sub_score*peso` → pontos no total (barra D-04) |
| `detalhe` | str | rótulo neutro de origem (`"alta+forte"`, `"duplo_fundo:confirmado"`, `"rr=2,5"`...) |

**`SinaisTecnicos`** (`core/indicators.py` L172-198) — campos que a UI lê: [VERIFIED]
- `tendencia: Tendencia` → `sma20/50/200`, `ema20/50/200` (pd.Series), `posicao_mm200` (`"acima"/"abaixo"/"indisponivel"`), `cruzamento`. (consumido por `overlays_preco`)
- `canais: Canais` → `donchian_sup/inf`, `donchian_sup_55/inf_55`, `bb_sup/med/inf` (pd.Series), `rompimento_donchian`, `toque_bollinger`, `squeeze`. (consumido por `overlays_preco`)
- `forca: Forca` → `adx/pdi/ndi` (pd.Series), `forca_adx`, `atr`. (consumido por `subpaineis_ativos` → subpainel ADX)
- `momentum: Momentum` → `rsi`, `macd`, `macd_sinal`, `macd_hist` (pd.Series), `nivel_rsi`, `cruzamento_macd`. (subpainéis RSI/MACD)
- `close: pd.Series\|None` → split-adjusted (p/ marcadores, se usados).
- `pivos: Pivos\|None` → `pivot_high/low` (pd.Series, NaN exceto nos pivôs), `ultimo_topo/fundo`, `n`. (marcar pivôs, opcional)
- `contexto: ContextoTendencia\|None` → `dow_diario` (`"alta"/"baixa"/"lateral"/"indisponivel"`), `alinhamento_mtf` (`"alinhado_alta"/"alinhado_baixa"/"conflito"/"indisponivel"`). (badge de tendência/MTF)
- `niveis: Niveis\|None` → `suportes`/`resistencias` (`list[(low,high)]`), `donchian_externo_inf/sup`, `entrada_zona` (`(low,high)`), `fib_retracoes` (`{"382","500","618"}→preço`), `alvo`, `pivos_ancora`, `stop`, `risco_retorno` (str `"1 : 2,5"`/`"indisponivel"`). (S/R hrects, fib hlines, R:R formatado)
- `volume: Volume\|None` → `volume_mm`, `rompimento_com_volume`, `volume_acima_mm`.
- `padroes: Padroes\|None` → `.lista: list[PadraoGrafico]` (Q2).
- `checklist: Checklist\|None` → `.sinais: list[Sinal]`.

**`Sinal`** (`core/indicators.py` L156-162) — cada item de `checklist.sinais`: [VERIFIED]
| Campo | Tipo | Conteúdo |
|-------|------|----------|
| `nome` | str | `"rompimento"`/`"cruzamento_mm"`/`"rsi"`/`"macd"`/`"padrao"`/`"volume"` (6 sinais) |
| `ativo` | bool | liga/desliga → ✓/✗ (D-05) |
| `detalhe` | str | rótulo neutro (`"nova_maxima"`, `"duplo_topo:confirmado"`, `"nenhum"`...) |

## Common Pitfalls

### Pitfall 1: Gatear a página inteira por `leitura_tecnica_disponivel`
**What goes wrong:** A aba Analisar zera overlays/marcadores quando `posicao_mm200=="indisponivel"` (app.py L255). Se a swing copiar isso para gatear TUDO, frames intraday curtos (sem MM200) não mostrariam nem candlestick nem S/R.
**How to avoid:** Renderizar candlestick + S/R + Fib + veredito SEMPRE que `f.disponivel`. Usar `leitura_tecnica_disponivel`/`_tem_ponto_valido` só para decidir overlays/subpainéis individuais (que `overlays_preco`/`subpaineis_ativos` já fazem — pulam série toda-NaN).
**Confidence:** HIGH [VERIFIED: grafico.py L80-83, L165-176 já degradam por série]

### Pitfall 2: Overlays de MM em escala AJUSTADA sobre candlestick NOMINAL
**What goes wrong:** `overlays_preco` lê `sinais.tendencia.sma*` computadas sobre `ohlc_ajustado` (split-adjusted), mas o candlestick usa `f.ohlc` (nominal). Em janelas COM split, as MMs/Bollinger ficam deslocadas verticalmente em relação aos candles.
**Why:** `calcular` roda indicadores no frame ajustado (CR-01) e só a família de PREÇO (pivôs/S-R/Fib) usa o nominal via `ohlc_nominal`.
**How to avoid:** No MVP, aceitar (intraday 60d/730d raramente tem split; D-02 já garante pivôs/S-R/Fib nominais coerentes com o candle). Documentar como limitação. Se virar problema visível no diário 5y de ticker com split, planner decide (render MM sobre nominal exige recomputo — fora do read-only).
**Confidence:** MEDIUM [VERIFIED no código que as fontes diferem; impacto visual ASSUMED depende de split na janela]

### Pitfall 3: `SetupSwing` "Sem setup" com `decomposicao` vazia
**What goes wrong:** Quando o gate de R:R falha ou score < piso, `montar_setup` retorna `decomposicao=[]` mas ainda pode trazer `entrada_zona`/`stop`/`alvo` (branch L174-177). Card que assume decomposição não-vazia quebra.
**How to avoid:** Render do card deve tratar `grade=="Sem setup"`/`decomposicao==[]` com mensagem neutra ("Sem confluência suficiente para um setup de estudo"); checklist ainda vem de `sinais.checklist.sinais` (independente do gate).
**Confidence:** HIGH [VERIFIED: setup.py L165, L173-177]

### Pitfall 4: `rangeslider` do candlestick dentro de `make_subplots`
**What goes wrong:** `go.Candlestick` ativa rangeslider por padrão, que rouba altura e desalinha as rows dos subpainéis.
**How to avoid:** `fig.update_xaxes(rangeslider_visible=False, row=1, col=1)` (o MVP single-panel já desliga via `xaxis_rangeslider_visible=False` L634).
**Confidence:** HIGH [VERIFIED: app.py L634]

### Pitfall 5: Copy imperativa nos níveis/veredito (gate de aceite SWING-02)
**What goes wrong:** `st.metric` para entrada/stop/alvo ou rótulos tipo "alvo de compra" soam como ordem.
**How to avoid:** Níveis numa TABELA rotulada "Referências de estudo (não são ordens)" (D-05), NUNCA `st.metric`. Disclaimer condicional inline. O firewall de copy já é testado na engine (`test_setup_report.py::test_setup_sem_copy_imperativa` proíbe `compre/venda/comprar/vender/entre/recomend/sugiro/indico`) — a UI deve manter o mesmo padrão na copy que ELA adiciona.
**Confidence:** HIGH [VERIFIED: test_setup_report.py L160-178; CONTEXT D-05]

### Pitfall 6: Esquecer `ohlc_nominal` em `calcular`
**What goes wrong:** Chamar `calcular(f.ohlc_ajustado, CFG)` sem `ohlc_nominal` faria pivôs/S-R/Fibonacci saírem em escala ajustada, desalinhando das zonas desenhadas sobre o candlestick nominal.
**How to avoid:** Sempre `indicators.calcular(f.ohlc_ajustado, CFG, ohlc_nominal=f.ohlc)`.
**Confidence:** HIGH [VERIFIED: indicators.py L1233-1262]

## Code Examples

### Cadeia completa de render (esqueleto do bloco swing estendido)
```python
# Source: composição de app.py L584-649 (MVP) + L262-344 (molde Analisar) + contratos lidos
if ticker and f.disponivel:
    sinais = indicators.calcular(f.ohlc_ajustado, CFG, ohlc_nominal=f.ohlc)
    sw = setup.montar_setup(sinais, CFG)

    st.session_state.setdefault("tec_estado_swing", _DEFAULT_SWING)   # dict isolado (D-03)
    est = st.session_state["tec_estado_swing"]
    with st.expander("⚙️ Overlays", expanded=False):
        # toggles → est["tendencia"]["on"], est["canais"][...], est["forca"]["on"],
        #           est["momentum"][...], est["sr_on"], est["fib_on"], est["niveis_setup_on"], est["padroes_on"]
        ...

    specs = grafico.subpaineis_ativos(est, sinais)
    layout = grafico.layout_subplots(len(specs))
    fig = make_subplots(rows=layout["rows"], cols=1, shared_xaxes=True,
                        row_heights=layout["row_heights"], vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(x=f.ohlc.index, open=f.ohlc["Open"], high=f.ohlc["High"],
                                 low=f.ohlc["Low"], close=f.ohlc["Close"], name=ticker), row=1, col=1)
    fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
    for ov in grafico.overlays_preco(est, sinais):
        fig.add_trace(go.Scatter(x=ov.serie.index, y=ov.serie.values, mode="lines",
                                 name=ov.nome, line=dict(ov.estilo)), row=1, col=1)
    if est["sr_on"]:
        for (lo, hi) in sinais.niveis.suportes:      # bandas, nunca pontos (LEVEL-01)
            fig.add_hrect(y0=lo, y1=hi, line_width=0, fillcolor="green", opacity=0.08, row=1, col=1)
        for (lo, hi) in sinais.niveis.resistencias:
            fig.add_hrect(y0=lo, y1=hi, line_width=0, fillcolor="red", opacity=0.08, row=1, col=1)
    if est["niveis_setup_on"] and sw.entrada_zona:   # entrada/stop/alvo como referência
        lo, hi = sw.entrada_zona
        fig.add_hrect(y0=lo, y1=hi, line_width=0, fillcolor="blue", opacity=0.10,
                      annotation_text="zona de entrada (estudo)", row=1, col=1)
        if sw.stop is not None:
            fig.add_hline(y=sw.stop, line_dash="dash", line_color="#d62728",
                          annotation_text="stop (estudo)", row=1, col=1)
        if sw.alvo is not None:
            fig.add_hline(y=sw.alvo, line_dash="dash", line_color="#2ca02c",
                          annotation_text="alvo (estudo)", row=1, col=1)
    if est["fib_on"] and sinais.niveis.fib_retracoes:
        for nome, preco in sinais.niveis.fib_retracoes.items():
            fig.add_hline(y=preco, line_dash="dot", line_color="#9467bd",
                          annotation_text=f"Fib {nome[0]}{nome[1]},{nome[2]}%", row=1, col=1)
    if est["padroes_on"]:
        ... # Q2: add_shape neckline + add_annotation rótulo + add_hline alvo
    if f.barra_viva and f.ultima_barra_ts is not None:
        fig.add_vline(x=f.ultima_barra_ts, line_dash="dot", line_color="#888888", row=1, col=1)
    for i, spec in enumerate(specs):                 # subpainéis RSI/MACD/ADX (molde Analisar L306-327)
        r = i + 2
        for rotulo, s in spec.series:
            if rotulo == "Histograma":
                fig.add_trace(go.Bar(x=s.index, y=s.values, name=rotulo,
                    marker_color=["#2ca02c" if (v is not None and v>=0) else "#d62728" for v in s.values]), row=r, col=1)
            else:
                fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=rotulo), row=r, col=1)
        for ref in spec.referencias:
            fig.add_hline(y=ref, line_width=1, line_dash="dot", line_color="#aaaaaa", row=r, col=1)
        fig.update_yaxes(title_text=spec.nome.upper(), row=r, col=1)
    fig.update_layout(height=420 + 140*len(specs), margin=dict(l=10,r=10,t=40,b=10),
                      showlegend=True, legend=dict(orientation="h", y=1.02))
    st.plotly_chart(fig, width="stretch")
    # selo de atraso (D-08)
    atraso = f" · última barra {f.ultima_barra_ts:%H:%M}" if f.ultima_barra_ts is not None else ""
    st.caption(f"⏱️ ~15min de atraso (best-effort){atraso}.")
    # --- card de veredito (abaixo, D-01) ---
    _render_veredito(sw, sinais)   # grade+score, barra decomposicao, checklist, tabela níveis, disclaimer
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| 4º menu = candlestick nu (MVP, commit 3c4eb15) | candlestick + overlays + subpainéis + veredito (Phase 16) | Esta fase fecha o produto v1.4 |
| `go.Figure` single-panel (MVP L626) | `make_subplots` multi-row | Necessário p/ RSI/MACD/ADX em rows próprias |

**Deprecated/outdated:** nada — o MVP atual é a base a estender, não a substituir.

## Project Constraints (from CLAUDE.md)

- Respostas/copy em **português brasileiro** (toda a UI desta página).
- **Não adicionar features além do pedido** — escopo travado em CONTEXT (sem ponte fundamentalista, sem padrões de continuação, sem alertas).
- **Preferir editar arquivos existentes** — estender o bloco swing em `app.py`, reusar `grafico.py`; evitar módulos novos salvo se golden-coverage justificar.
- **Validação só em bordas** — ticker/timeframe já validados na engine (`coletar_intraday` valida timeframe contra conjunto fechado; ticker resolvido em `prices.yahoo_symbol`); a UI só repassa.
- Comentários só quando o "porquê" não é óbvio.

## Security Domain

> `security_enforcement` ausente em config.json (= habilitado). Página read-only sem auth/sessão/persistência; superfície mínima.

### Applicable ASVS Categories
| ASVS | Applies | Standard Control |
|------|---------|-----------------|
| V2 Authentication | no | sem login (app público read-only) |
| V3 Session | no | `st.session_state` só guarda toggles/nonce (não-sensível) |
| V4 Access Control | no | sem dados de usuário |
| V5 Input Validation | yes | ticker (`.strip().upper()`, resolvido em `yahoo_symbol`), timeframe (whitelist `_PERIODO_POR_TF` — `coletar_intraday` rejeita inválido com `MOTIVO_TF_INVALIDO`) [VERIFIED: intraday.py L80] |
| V6 Cryptography | no | nenhum segredo nesta camada |

### Known Threat Patterns
| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Timeframe arbitrário do usuário | Tampering | whitelist fechada em `_PERIODO_POR_TF` (já implementado) |
| Martelar Yahoo (rate-limit/DoS próprio) | DoS | refresh manual + `@st.cache_data(ttl=300)` + retry com backoff limitado (já implementado); auto-refresh em segundos é explicitamente fora de escopo |
| `$` em string markdown quebra layout (LaTeX) | — (robustez) | `esc_md()` ao exibir valores R$ em metric/markdown |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Overlays de MM (escala ajustada) sobre candlestick nominal são visualmente aceitáveis no MVP (split raro em janelas intraday) | Pitfall 2 | MMs deslocadas em ticker com split no diário 5y; planner pode optar por ocultar MM no diário ou aceitar |
| A2 | Neckline horizontal (add_shape) é legível o suficiente para OCO no MVP (reta inclinada deferida) | Q2 | OCO com neckline muito inclinada parece "errada"; reconstrução da reta exige distinguir fundos/ombros em `pivos_envolvidos` |
| A3 | `marcadores_eventos` (golden/death cross + Donchian) ficam OFF no candlestick swing (clutter); D-02 não os lista | Q1 | Se o usuário quiser esses marcadores, é toggle extra trivial |
| A4 | Defaults de `tec_estado_swing` (MMs+S/R+níveis+Fib ON; Bollinger/Donchian/padrões OFF; RSI/MACD/ADX ON) refletem D-02 | Q1 | Ajuste de toggle inicial, baixo risco |

## Open Questions (RESOLVED)

1. **Badge de tendência/MTF no card?** `sinais.contexto.dow_diario`/`alinhamento_mtf` existem e seriam um badge útil ("Tendência: alta · MTF: conflito"). CONTEXT não pede explicitamente, mas reforça explicabilidade (D-04). Recomendação: incluir como linha discreta no card (neutro, sem recomendação). — **RESOLVED:** implementado em 16-02 Task 2 como linha discreta neutra no card.
2. **Reta inclinada da OCO** — deferir p/ pós-MVP (A2). Recomendação: horizontal agora. — **RESOLVED:** deferido; neckline horizontal no MVP (16-02 Task 1), inclinada fica para pós-Phase 16.
3. **Marcadores de pivôs visíveis?** `sinais.pivos.pivot_high/low` permitem marcar swings no candle. Útil para "ver por quê", mas pode poluir. Recomendação: toggle opcional OFF por padrão. — **RESOLVED:** deferido para pós-Phase 16 — não é requisito de CHART-01 nem decisão travada em CONTEXT; fora do escopo desta fase.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| streamlit | UI inteira | ✓ | 1.58.0 | — |
| plotly | candlestick/subplots | ✓ | 6.8.0 | — |
| pandas | séries OHLC | ✓ | 3.0.3 | — |
| yfinance (rede Yahoo) | dados intraday | ✓ (best-effort) | instalado | `FrameOHLC(disponivel=False)` → `st.error` por motivo (degradação graciosa já implementada) |

**Missing dependencies with no fallback:** nenhuma. **Com fallback:** instabilidade da Yahoo já degrada via `motivo` + botão Atualizar.

## Runtime State Inventory

Não se aplica — fase **greenfield aditiva** (estende um bloco de UI existente; nenhum rename/refactor/migração). Nenhum estado runtime armazenado, config de serviço, registro de SO, secret ou artefato de build é tocado. Verificado: a página só LÊ dataclasses em memória e usa `st.session_state` efêmero (toggles + nonce de cache).

## Sources

### Primary (HIGH confidence — código-fonte lido nesta sessão)
- `app.py` L53-69 (`frame_intraday`/`_nonce_key`), L100-105 (sidebar radio, 4º menu já presente), L262-344 (molde make_subplots Analisar), L584-649 (bloco swing MVP a estender)
- `src/analista/grafico.py` (completo) — `overlays_preco`/`subpaineis_ativos`/`layout_subplots`/`marcadores_eventos`/`leitura_tecnica_disponivel`/`estado_padrao` + dataclasses `OverlaySpec`/`SubpainelSpec`/`Marcador`
- `src/analista/report/setup.py` (completo) — `SetupSwing`/`ContribFamilia`/`montar_setup`
- `src/analista/core/indicators.py` — contratos `SinaisTecnicos`/`Niveis`/`PadraoGrafico`/`Padroes`/`Sinal`/`Checklist`/`ContextoTendencia` + `calcular()` (L1222-1284, com `ohlc_nominal`)
- `src/analista/ingest/intraday.py` — `FrameOHLC` + `coletar_intraday` (whitelist timeframe, barra viva clock-free)
- `config.yaml` §`indicadores`/`padroes`/`score` (pesos 35/20/20/15/10, rr_minimo 1.5, cortes_grade 70/50/25)
- `tests/test_setup_report.py` L160-178 (firewall de copy imperativa), `tests/test_grafico_ui.py` (golden das funções puras)
- `.planning/STATE.md` (read-only locked, firewall setup×report, 283 verdes), `.planning/config.json` (nyquist_validation=false)

### Version verification
- `./.venv/bin/python` import: plotly 6.8.0, streamlit 1.58.0, pandas 3.0.3 [VERIFIED 2026-06-30]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero deps novas, versões verificadas via import
- Contratos (SetupSwing/SinaisTecnicos/FrameOHLC/grafico.py): HIGH — lidos linha a linha do fonte
- APIs Plotly (Candlestick/add_hrect/add_hline/add_vline/add_shape/add_annotation/make_subplots): HIGH — todas já em uso no próprio `app.py` em produção
- Reuso vs extensão: HIGH — funções puras agnósticas de trace, golden-pinned
- Pitfall escala MM nominal×ajustada (A1): MEDIUM — fontes divergentes verificadas; impacto visual depende de split na janela

**Research date:** 2026-06-30
**Valid until:** ~30 dias (stack estável; contratos travados por goldens)
