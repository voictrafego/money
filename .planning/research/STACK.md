# Stack Research

**Domain:** Indicadores técnicos de tendência (consultivos) sobre série OHLC diária, em app Python + Streamlit + Plotly (custo zero)
**Researched:** 2026-06-24
**Confidence:** HIGH

## TL;DR (recomendação)

**Calcular todos os 7 indicadores à mão em pandas/numpy/scipy — NÃO adicionar nenhuma biblioteca de TA.**

O ambiente roda **numpy 2.4.6 + pandas 3.0.3** (verificado no `.venv` do projeto). Toda
biblioteca de TA candidata ou (a) está congelada antes do numpy 2 / pandas 3 e quebra, ou (b)
exige dependência compilada em C, ou (c) força Python ≥3.12 + numba. Os 7 indicadores pedidos
(SMA, EMA, crossovers, Donchian, Bollinger, ADX, inclinação por regressão, RSI, MACD) são todos
fórmulas de poucas linhas em pandas. Hand-roll = **zero novas dependências, zero risco de
versão, controle total e testável com golden tests** (que o projeto já usa). É a escolha que
melhor honra o princípio "custo zero / instalação simples / base pandas".

**Única dependência nova opcional:** nenhuma. `scipy>=1.11` já está no `requirements.txt`
(scipy 1.17.1 instalado) e cobre a inclinação por regressão linear via
`scipy.stats.linregress` — mas isso também é trivial em numpy puro (`numpy.polyfit`), então
nem scipy é estritamente necessário.

## Recommended Stack

### Core Technologies (já presentes — reaproveitar)

| Technology | Version (instalada) | Purpose | Why Recommended |
|------------|---------------------|---------|-----------------|
| pandas | 3.0.3 (req `>=2.0`) | `rolling()`, `ewm()`, médias móveis, bandas, RSI/MACD | Já é a espinha dorsal do projeto; `rolling`/`ewm` cobrem SMA/EMA/Donchian/Bollinger/ADX/RSI/MACD nativamente |
| numpy | 2.4.6 (req `>=1.24`) | `polyfit`/`maximum`/`where` para slope, True Range, sinais | Já presente; numpy 2.x é o motivo nº1 para NÃO trazer libs de TA congeladas |
| scipy | 1.17.1 (req `>=1.11`) | `scipy.stats.linregress` p/ inclinação + R² da tendência | Já presente (usado no valuation); dá slope + p-value/R² de graça |
| plotly | 6.8.0 (req `>=6.0`) | Overlays no gráfico existente + subplots dos osciladores | Já é o motor do gráfico da aba Analisar; `make_subplots` cobre os painéis RSI/MACD/ADX |
| streamlit | 1.58.0 (req `>=1.30`) | Toggles/multiselect dos indicadores + render do gráfico | Já é a UI; `st.toggle`/`st.multiselect`/`st.segmented_control` cobrem o painel de controles |

### Supporting Libraries

**Nenhuma nova biblioteca recomendada.** Esta é a conclusão central da pesquisa, não uma omissão.

Se no futuro o conjunto de indicadores crescer muito (dezenas) e a manutenção do código
manual virar fardo, reavaliar `ta` (ver "Alternatives") — mas hoje, para 7 indicadores, o
custo de manutenção do hand-roll é menor que o risco de versão de qualquer lib.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest (já em uso) | Golden tests dos indicadores | Validar cada indicador contra valores conhecidos (ex.: RSI/MACD de uma série sintética com resultado calculado à mão ou contra uma planilha). O projeto já tem 64 golden tests — seguir o mesmo padrão garante fidelidade sem depender de lib externa |

## Disponibilidade de OHLC (ponto crítico de integração)

**Diagnóstico do código atual** (`src/analista/ingest/prices.py`):

- A chamada `tk.history(period="5y", auto_adjust=False)` (linha 101) **já retorna o frame OHLC
  completo** (`Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`).
- Hoje só `Close` é preservado em `dm.serie_precos` (linha 108, `hist["Close"].dropna()`);
  `Open`/`High`/`Low` são descartados após calcular liquidez/beta.

**Caminho mais barato (recomendado): preservar o frame OHLC já buscado — ZERO chamadas de rede novas.**

- ADX precisa de High/Low/Close; Donchian precisa de High/Low. Os demais (SMA/EMA/Bollinger/
  RSI/MACD/slope) usam só Close. Tudo isso já está no `hist`.
- Adicionar um campo ao dataclass `DadosMercado`, ex.:
  `serie_ohlc: Optional["pd.DataFrame"] = None` (Open/High/Low/Close, índice = datas),
  populado de `hist[["Open","High","Low","Close"]].dropna()`.
- Manter `serie_precos` (Close) como está, para não quebrar o gráfico/banda DDM atuais nem os
  golden tests — `serie_precos` pode inclusive virar `serie_ohlc["Close"]`.

**Implicações de formato dos dados:**

- **Mesma base nominal**: usar **Close nominal** (`auto_adjust=False`), igual à `serie_precos`
  atual — os indicadores têm de ficar na mesma escala da banda DDM (decisão já registrada em
  PROJECT.md / CR-01). NÃO usar `Adj Close` para os indicadores do gráfico (distorceria os
  níveis vs. o eixo de preço). `Adj Close` segue só para beta/desempenho relativo.
- **Índice tz-aware**: o `tk.history` retorna índice `DatetimeIndex` tz-aware (America/Sao_Paulo
  via Yahoo). `rolling`/`ewm` lidam bem; só atenção se for cruzar datas com outra série.
- **Janela mínima**: MM200 e Donchian/ADX de janela longa precisam de ≥200 pregões válidos.
  Com 5 anos (~1250 pregões) há folga, mas o código deve degradar com elegância para tickers
  novos/ilíquidos (poucos pontos → indicador devolve NaN no início; não renderizar linha vazia).
- **NaN no aquecimento**: os primeiros N-1 valores de qualquer média/banda são NaN por
  construção. Plotly ignora NaN em `Scatter` (linha quebra), então não precisa de tratamento
  especial — mas o "resumo de timing" deve checar `pd.notna(...)` antes de comparar.

## Plotly: overlays e subplots (ponto de integração na UI)

O gráfico atual usa `go.Figure()` com um único eixo de preço (`app.py` ~linha 143-169).
Para os novos indicadores há duas categorias com necessidades distintas:

**1. Overlays no MESMO eixo de preço (sobrepõem direto na escala R$):**

- **Médias móveis (SMA/EMA 20/50/200):** um `fig.add_trace(go.Scatter(mode="lines", ...))`
  por média ligada. Cores/legendas distintas.
- **Bollinger Bands:** três traces — média central + banda superior + banda inferior. Para o
  preenchimento entre bandas, adicionar a banda superior e depois a inferior com
  `fill="tonexty"` e `fillcolor` translúcido.
- **Donchian Channel:** mesma técnica das Bollinger — máx/mín de N períodos como duas linhas
  com `fill="tonexty"`.
- **Crossovers (golden/death cross):** marcadores pontuais (`go.Scatter(mode="markers")`) nos
  pregões em que MM-curta cruza MM-longa, ou apenas comunicar no "resumo de timing" (mais limpo).

**2. Osciladores em SUBPLOT/painel separado (escala diferente — NÃO cabem no eixo R$):**

- **RSI** (0-100), **MACD** (em torno de 0, escala de preço-diff) e **ADX** (0-100) têm escala
  própria e **precisam de painéis separados abaixo do preço**. Sobrepô-los no eixo R$
  esmagaria o gráfico.
- Trocar `go.Figure()` por **`plotly.subplots.make_subplots`** com linhas empilhadas,
  `shared_xaxes=True` e `row_heights` (ex.: preço 60%, e cada oscilador ligado ~13%). Exemplo
  de assinatura:
  ```python
  from plotly.subplots import make_subplots
  fig = make_subplots(rows=n, cols=1, shared_xaxes=True,
                      vertical_spacing=0.03, row_heights=[...])
  fig.add_trace(trace_preco, row=1, col=1)
  fig.add_trace(trace_rsi,   row=2, col=1)   # só se RSI estiver ligado
  ```
- **Número de linhas dinâmico:** montar a lista de painéis conforme os toggles ligados (1 fixo
  do preço + 1 por oscilador ativo). Com nenhum oscilador ligado, manter o `go.Figure()` simples
  atual (ou `make_subplots(rows=1)`).
- O **`rangeselector`** de período (30D/6M/1A/5A) atual continua funcionando — aplicar ao xaxis
  do painel de preço; com `shared_xaxes=True` os subplots seguem o zoom.
- `add_hrect` da banda DDM (linha 151) só deve ir no painel de preço (`row=1`). Em
  `make_subplots`, usar `fig.add_hrect(..., row=1, col=1)`.

**Controles Streamlit (painel de seleção):** `st.toggle`/`st.checkbox` por família, ou
`st.multiselect`/`st.segmented_control` para escolher quais exibir. Reexecuta o app e
re-renderiza o `fig` — barato porque não há nova chamada de rede (OHLC já em memória/cache).

## Installation

```bash
# NADA a instalar. Todas as dependências necessárias já estão no requirements.txt:
#   pandas>=2.0   numpy>=1.24   scipy>=1.11   plotly>=6.0   streamlit>=1.30   yfinance>=0.2.40
# (instaladas: pandas 3.0.3, numpy 2.4.6, scipy 1.17.1, plotly 6.8.0, streamlit 1.58.0)

# Verificação rápida (opcional):
./.venv/bin/python -c "import pandas, numpy, scipy, plotly, streamlit; print('ok')"
```

## Fórmulas hand-roll (referência de implementação, pandas puro)

| Indicador | Implementação (esboço) | Entrada |
|-----------|------------------------|---------|
| SMA 20/50/200 | `close.rolling(n).mean()` | Close |
| EMA 20/50/200 | `close.ewm(span=n, adjust=False).mean()` | Close |
| Golden/Death cross | sinal de `sma_curta - sma_longa` muda de sinal | Close |
| Preço × MM200 | `close.iloc[-1] vs sma200.iloc[-1]` | Close |
| Donchian (N) | `high.rolling(n).max()`, `low.rolling(n).min()` | High/Low |
| Bollinger (20, 2σ) | `sma20 ± 2*close.rolling(20).std()` | Close |
| RSI (14) | Wilder: ganho/perda médios via `ewm(alpha=1/14)` ou rolling | Close |
| MACD (12,26,9) | `ema12 - ema26`; sinal = `ema9` do MACD; hist = MACD−sinal | Close |
| ADX (14) | True Range + +DI/−DI suavizados (Wilder) → DX → ADX | High/Low/Close |
| Inclinação | `scipy.stats.linregress(x, close_recente)` → slope + R² | Close |

**Cuidado de fidelidade (golden test obrigatório):** RSI e ADX usam suavização de **Wilder**
(EMA com `alpha = 1/n`), não SMA simples. Implementar Wilder corretamente e travar com golden
test — é o ponto onde implementações ingênuas divergem das ferramentas de mercado.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Hand-roll (pandas) | **`ta` 0.11.0** (bukosabino) | Se um dia precisar de dezenas de indicadores e topar o risco de versão. Pure-Python (sem C), cobre todos os 7. MAS: último release **nov/2023**, anterior ao numpy 2.0 e pandas 3.0; risco real de quebra (`np.NaN` removido no numpy 2; APIs de pandas 3). Só usaria com numpy/pandas pinados — o que conflita com este projeto |
| Hand-roll | **`pandas-ta` (rewrite 0.4.71b0, set/2025)** | Se rodar Python ≥3.12 e aceitar numba como dependência pesada. A reescrita é beta, exige `Python>=3.12` + numba/numpy; o original (0.3.14b) é não-mantido e pede `numpy<2`. Dependência pesada demais para 7 fórmulas |
| Hand-roll | **`TA-Lib`** | Se performance em milhões de barras importasse (não é o caso: 1 ticker × ~1250 barras). Exige a **lib C nativa** instalada no SO antes do `pip install` — quebra "instalação simples / custo zero" e complica o deploy |
| Hand-roll | **`finta`** | Nunca. Praticamente abandonado, sem garantias de numpy 2 / pandas 3 |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **TA-Lib** | Wrapper de lib C: precisa compilar/instalar a `ta-lib` nativa antes do pip; falha de instalação é o problema nº1 da lib; viola custo-zero/instalação-simples | Hand-roll em pandas |
| **`ta` 0.11.0** (sem pin) | Congelado em nov/2023, antes de numpy 2 / pandas 3; risco de `AttributeError: np.NaN` e APIs depreciadas de pandas com o ambiente atual (numpy 2.4.6 / pandas 3.0.3) | Hand-roll em pandas |
| **`pandas-ta` original (0.3.14b)** | Não-mantido; documentação pede `numpy<2`; incompatível com numpy 2.4.6 do projeto | Hand-roll; ou, em último caso, rewrite com Python 3.12+numba |
| **`finta`** | Abandonado, sem suporte a numpy 2 / pandas 3 | Hand-roll em pandas |
| Nova chamada de rede para OHLC | O `tk.history(period="5y")` já traz OHLC; refazer fetch dobra latência e exposição ao rate-limit do Yahoo | Preservar o frame OHLC já buscado em `prices.py` |
| `Adj Close` para os indicadores do gráfico | Quebra a base nominal compartilhada com a banda DDM (CR-01) | Close nominal, igual a `serie_precos` |

## Stack Patterns by Variant

**Se nenhum oscilador (RSI/MACD/ADX) estiver ligado:**
- Manter `go.Figure()` simples (como hoje) ou `make_subplots(rows=1)`.
- Médias/Bollinger/Donchian entram como traces no único eixo de preço.

**Se ≥1 oscilador ligado:**
- Migrar para `make_subplots(rows=1+k, shared_xaxes=True)` com `k` = nº de osciladores ativos.
- `row_heights` priorizando o painel de preço; banda DDM e rangeselector no `row=1`.

**Se o ticker tiver < 200 pregões (novo/ilíquido):**
- MM200/Donchian longo devolvem NaN → não renderizar a linha; exibir aviso suave no resumo de
  timing ("histórico curto: MM200 indisponível"), espelhando o padrão de degradação graciosa
  já usado quando o Yahoo falha (GRAF-03).

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| numpy 2.4.6 | pandas 3.0.3, scipy 1.17.1 | Stack moderna e coerente; motivo central para evitar libs de TA congeladas |
| `ta` 0.11.0 | numpy <2, pandas <2.x | ❌ INCOMPATÍVEL com o ambiente (nov/2023, pré-numpy-2/pandas-3) |
| `pandas-ta` 0.3.14b | numpy <2 | ❌ pede numpy<2; conflita com 2.4.6 |
| `pandas-ta` 0.4.71b0 | Python ≥3.12 + numba | ⚠️ beta + dependência pesada; desnecessário p/ 7 indicadores |
| plotly 6.8.0 | streamlit 1.58.0 | ✓ `st.plotly_chart` + `make_subplots` ok |

## Sources

- `.venv` do projeto (verificação direta) — numpy 2.4.6, pandas 3.0.3, scipy 1.17.1, plotly 6.8.0, streamlit 1.58.0 — **HIGH** (executado localmente)
- `src/analista/ingest/prices.py` (leitura do código) — confirma que `tk.history(period="5y", auto_adjust=False)` já traz OHLC e só Close é preservado — **HIGH**
- `app.py` linhas 143-169 (leitura do código) — gráfico atual em `go.Figure()`, banda via `add_hrect`, rangeselector nativo — **HIGH**
- https://pypi.org/project/ta/ — `ta` 0.11.0, release nov/2023, declara Python 3.6/3.7 — **HIGH**
- https://github.com/bukosabino/ta — `ta` cobre SMA/EMA/RSI/MACD/ADX/Bollinger/Donchian (43 indicadores) — **HIGH** (cobertura), maintenance status — **MEDIUM**
- https://pypi.org/project/pandas-ta/ — rewrite 0.4.71b0 (set/2025), Python ≥3.12, numba — **HIGH**
- numpy 2.0 migration guide + issue #55519 (pandas) — `np.NaN` removido; libs antigas quebram em numpy 2 — **HIGH**
- pandas-ta-openbb (fork p/ numpy 2) na PyPI — evidência de que o pandas-ta original não suporta numpy 2 nativamente — **MEDIUM**

---
*Stack research for: indicadores técnicos de tendência (consultivos) em Python/Streamlit/Plotly, custo zero*
*Researched: 2026-06-24*
