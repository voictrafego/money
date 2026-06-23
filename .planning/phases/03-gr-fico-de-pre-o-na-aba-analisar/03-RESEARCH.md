# Phase 3: Gráfico de Preço na aba Analisar - Research

**Researched:** 2026-06-23
**Domain:** Visualização interativa (Plotly) dentro de app Streamlit; threading de uma série temporal pandas por uma cadeia de dataclasses existente.
**Confidence:** HIGH

## Summary

Esta fase é **aditiva e de baixo risco**: a engine já baixa `hist = tk.history(period="5y", auto_adjust=True)` em `ingest/prices.py` (linha 94) e hoje só usa o `Close` para liquidez/beta/desempenho — a série inteira é descartada quando `coletar_mercado()` retorna. O trabalho é (1) **preservar** essa série num campo novo de `DadosMercado`, (2) **copiá-la** em `build.montar_empresa` para `CompanyData`, (3) **lê-la** em `app.py` Tela 1 e renderizar com **Plotly** (`go.Figure` + `st.plotly_chart`), sobrepondo a banda intrínseca DDM (`a.vmin`–`a.vmax`) já computada por `report.analisar_acao`. Nenhuma fórmula de valuation muda, nenhuma nova chamada de rede é feita (a série herda o cache de 1h de `montar()`), e os 62 golden tests continuam verdes (verificado: rodam offline em 0.85s e constroem `CompanyData` por keyword args, imunes a um campo opcional novo).

A escolha técnica central já está cravada pelo CONTEXT.md: **banda horizontal plana** entre vmin e vmax (D-01/D-02), no topo da aba antes de `st.tabs` (D-03), estilo limpo sem sombrear desconto/prêmio (D-04), com dois fallbacks que espelham padrões já existentes — série indisponível (D-05/GRAF-03) e DDM não calculado (D-06).

**Primary recommendation:** Adicionar campo `serie_precos: Optional[pd.Series] = None` em `DadosMercado` e `CompanyData`; preservar `hist["Close"]` em `prices.py`; copiar em `build.py`; em `app.py` construir `go.Figure` com um `go.Scatter` (linha de preço) + `fig.add_hrect(y0=vmin, y1=vmax, ...)` para a banda; renderizar com `st.plotly_chart(fig, width="stretch")`. Fallbacks via `if`/`else` antes do `st.tabs`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Baixar série 5a (já existe) | Ingest (`prices.py`) | — | Único ponto com acesso ao Yahoo; já faz o fetch |
| Preservar/transportar a série | Ingest → Build (`DadosMercado`→`CompanyData`) | — | Mesmo padrão dos campos `preco_atual`, `beta` já threaded |
| Computar banda intrínseca (vmin/vmax) | Report (`analisar_acao`) | — | Já calculado; **não tocar** — só ler |
| Renderizar o gráfico Plotly | UI (`app.py` Tela 1) | — | Streamlit é a única camada de apresentação interativa |
| Cache (evitar rede no re-render) | UI (`@st.cache_data(ttl=3600)` em `montar`) | — | Cache já existe; a série herda automaticamente |

**Insight:** Toda a fase mora em 3 camadas que já existem e já se comunicam. Não há nova fronteira arquitetural; é um campo a mais viajando pelo mesmo cano. A engine de valuation (core/) **não é tocada**.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| plotly | >=6.0 (latest 6.8.0) | Gráfico interativo (zoom + hover) exigido por GRAF-01 | Padrão de facto para gráficos interativos em Streamlit; `st.plotly_chart` é first-class no Streamlit `[VERIFIED: docs.streamlit.io]` |
| streamlit | 1.58.0 (já instalado) | Camada de UI; `st.plotly_chart` | Já é a UI do projeto `[VERIFIED: ./.venv import]` |
| pandas | >=2.0 (já instalado) | `pd.Series`/`DataFrame` da série de preços | Já é a estrutura nativa de `tk.history()` `[VERIFIED: requirements.txt]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| plotly.graph_objects (`go`) | parte do plotly | API explícita `go.Figure`/`go.Scatter` | Preferir sobre `plotly.express` aqui: controle fino do estilo limpo D-04, sem precisar montar DataFrame longo |

**Versões verificadas:**
- `plotly` última versão no PyPI: **6.8.0** (verificado via `pip index versions plotly`). **Plotly NÃO está instalado no venv ainda** — precisa entrar em `requirements.txt` e ser instalado. `[VERIFIED: pip index]`
- `streamlit`: **1.58.0** instalado. `[VERIFIED: import streamlit]`
- Recomendação de pin: `plotly>=6.0` (mesmo estilo dos outros pins do projeto — minor floor, não exato).

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `plotly` | `st.line_chart` nativo | Nativo é mais simples mas o roadmap/REQUIREMENTS exigem Plotly explicitamente (zoom+hover ricos, banda sobreposta). `st.line_chart` não desenha banda horizontal sombreada facilmente. **Locked: usar Plotly.** |
| `go` (graph_objects) | `plotly.express` (`px.line`) | `px` é conciso mas força pensar em DataFrame/colunas; para 1 linha + 1 banda, `go` é mais direto e legível. **Discrição do executor.** |
| `add_hrect` | dois `add_hline` | `add_hline` desenha só as bordas (sem preenchimento). `add_hrect` preenche a faixa com `opacity` baixa — exatamente o "banda sutil" de D-04. **Recomendado: `add_hrect`.** |

**Installation:**
```bash
echo "plotly>=6.0" >> requirements.txt
./.venv/bin/pip install "plotly>=6.0"
```

## Architecture Patterns

### System Architecture Diagram

```
[Yahoo Finance]
      │ tk.history(period="5y", auto_adjust=True)   ← JÁ ACONTECE (prices.py:94)
      ▼
┌─────────────────────────────────────────────┐
│ prices.coletar_mercado()                     │
│  hist["Close"]  →  liquidez/beta/desempenho  │  (uso atual)
│  hist["Close"]  →  dm.serie_precos  ◄── NOVO │  (preservar a série)
└─────────────────────────────────────────────┘
      │ DadosMercado(serie_precos=…)
      ▼
┌─────────────────────────────────────────────┐
│ build.montar_empresa()                       │
│  c.serie_precos = dm.serie_precos  ◄── NOVO  │  (mesma linha-padrão de c.preco_atual = dm.preco_atual)
└─────────────────────────────────────────────┘
      │ CompanyData(serie_precos=…)        ┌──────────────────────────────┐
      │                                    │ report.analisar_acao(c)      │
      │                                    │  a.vmin, a.vmax  (NÃO TOCAR) │
      ▼                                    └──────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ app.py  Tela 1 "🔎"  (depois do veredito/métricas,           │
│                        ANTES de st.tabs — D-03)               │
│                                                               │
│   série None/vazia? ──sim──► st.warning (espelha D-05) ──► fim│
│        │ não                                                  │
│        ▼                                                      │
│   go.Figure + go.Scatter(serie_precos)                        │
│   vmin/vmax None? ──não──► fig.add_hrect(y0=vmin,y1=vmax)     │
│        │ (D-06: pula a banda, só a linha)                     │
│        ▼                                                      │
│   st.plotly_chart(fig, width="stretch")                       │
└─────────────────────────────────────────────────────────────┘
      ▲
      └── @st.cache_data(ttl=3600) em montar()  → re-render NÃO refaz rede
```

### Recommended Project Structure
Nenhuma estrutura nova. Edições pontuais em 4 arquivos existentes:
```
src/analista/ingest/prices.py   # + campo serie_precos no dataclass; preservar hist["Close"]
src/analista/ingest/build.py    # + c.serie_precos = dm.serie_precos
src/analista/core/fundamentals.py # + campo serie_precos em CompanyData
app.py                          # + bloco de render do gráfico na Tela 1
requirements.txt                # + plotly>=6.0
```
> Nota: `report.py`/`AnaliseAcao` NÃO precisam carregar a série — `app.py` já tem o `c` (CompanyData) em mãos no mesmo escopo (`c = montar(...)`; `a = report.analisar_acao(c, CFG)`), então lê `c.serie_precos` e `a.vmin/a.vmax` direto. Isso simplifica: a série não precisa atravessar `AnaliseAcao`.

### Pattern 1: Preservar a série sem alterar o fetch (prices.py)
**What:** Adicionar campo opcional ao dataclass e atribuir dentro do bloco `if hist is not None and not hist.empty:` que já existe.
**When to use:** Ponto de origem.
**Example:**
```python
# Em DadosMercado (prices.py ~linha 45):
import pandas as pd  # já importado tardiamente no bloco de dividendos; subir ou importar local
@dataclass
class DadosMercado:
    ...
    serie_precos: Optional["pd.Series"] = None  # close diário 5a (índice = datas)

# Dentro de coletar_mercado(), no bloco existente (prices.py ~linha 98):
if hist is not None and not hist.empty:
    dm.serie_precos = hist["Close"].dropna()   # ◄── NOVO (uma linha)
    if dm.preco_atual is None:
        dm.preco_atual = float(hist["Close"].iloc[-1])
    ...
```
> `auto_adjust=True` já está ativo → o Close é ajustado por proventos/splits, coerente com uma série de "preço efetivo". `.dropna()` remove gaps de pregões sem fechamento (ver Pitfall 3).

### Pattern 2: Banda horizontal plana com add_hrect (app.py)
**What:** Linha de preço + retângulo horizontal infinito no eixo X entre vmin e vmax.
**When to use:** Render principal (GRAF-01 + GRAF-02).
**Example:**
```python
# Source: https://plotly.com/python/horizontal-vertical-shapes/  [CITED]
import plotly.graph_objects as go

serie = c.serie_precos
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=serie.index, y=serie.values,
    mode="lines", name="Preço",
    line=dict(color="#1f77b4", width=2),
    hovertemplate="%{x|%d/%m/%Y}<br>R$ %{y:.2f}<extra></extra>",
))
# Banda intrínseca DDM — só se calculada (D-06)
if a.vmin is not None and a.vmax is not None:
    fig.add_hrect(
        y0=a.vmin, y1=a.vmax,
        line_width=0, fillcolor="green", opacity=0.12,
        annotation_text="Valor intrínseco (DDM)", annotation_position="top left",
    )
fig.update_layout(
    height=380, margin=dict(l=10, r=10, t=30, b=10),
    yaxis_title="R$", xaxis_title=None, showlegend=False,
)
st.plotly_chart(fig, width="stretch")
```
> `add_hrect` desenha a faixa "plana" ao longo de todo o eixo X automaticamente (estende-se ao infinito em x) — é exatamente D-02 sem precisar repetir vmin/vmax como série. `opacity` baixa = "banda sutil" de D-04.

### Pattern 3: Fallback de série indisponível (D-05 / GRAF-03)
```python
serie = getattr(c, "serie_precos", None)
if serie is None or len(serie) == 0:
    st.info(
        "📉 Gráfico de preço indisponível agora (fonte Yahoo instável). "
        "Os fundamentos e o valor intrínseco abaixo seguem válidos."
    )  # espelha o tom do aviso "preço atual indisponível" (app.py:116-120)
else:
    # ... monta e renderiza o fig
```

### Anti-Patterns to Avoid
- **Recalcular intrínseco histórico:** D-01/D-02 cravam banda PLANA. Não desenhar uma série de vmin/vmax por data. A engine não produz valor intrínseco histórico e a fase proíbe inventá-lo.
- **`use_container_width=True`:** Deprecado no Streamlit (aviso até 2025-12-31). Usar `width="stretch"`. `[VERIFIED: docs.streamlit.io]`
- **Passar a série por `AnaliseAcao`:** desnecessário — `c` já está no escopo do render. Carregar em `report.py` aumenta a superfície de mudança e arrisca os testes de `analisar_acao`.
- **Sombrear área desconto/prêmio ou marcar o ponto do preço atual:** explicitamente deferido (D-04). Não fazer.
- **Reordenar o bloco da Tela 1:** o gráfico vai ENTRE as métricas/veredito (app.py ~linha 124, depois dos alertas) e `st.tabs` (linha 126). Não mover o `st.tabs`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Banda horizontal plana | Montar `go.Scatter` com `fill="tonexty"` entre duas linhas constantes | `fig.add_hrect(y0=vmin, y1=vmax)` | `add_hrect` é uma chamada, estende ao infinito em x, não precisa de série dummy |
| Cache de rede no re-render | Lógica manual de memoização | `@st.cache_data(ttl=3600)` em `montar()` (já existe) | A série herda o cache automaticamente; re-render não bate no Yahoo |
| Formatação de data no hover | String manual | `hovertemplate` com `%{x|%d/%m/%Y}` | Plotly formata datetime nativamente |
| Zoom/pan | Controles custom | Nativo do Plotly | GRAF-01 atendido sem código (zoom+hover são built-in) |

**Key insight:** A maior tentação é "calcular a banda como série temporal". Resista: a banda é uma constante visual (D-02), e `add_hrect` existe exatamente para isso.

## Runtime State Inventory

> Fase **greenfield-aditiva** (adiciona um campo + render). Não é rename/refactor/migração — sem estado runtime a migrar.

- **Stored data:** Nenhum. A série é volátil (vem do Yahoo em runtime, vive só no cache de 1h em memória). Nenhum datastore persiste a série. (Verificado: projeto não tem DB — Supabase morto, SQLite só no bot-trad.)
- **Live service config:** Nenhuma. Sem n8n/serviço externo envolvido nesta fase.
- **OS-registered state:** Nenhum.
- **Secrets/env vars:** Nenhum. Yahoo é acesso anônimo.
- **Build artifacts:** Instalar `plotly` no venv após adicioná-lo ao `requirements.txt` (`./.venv/bin/pip install plotly>=6.0`). Único artefato a atualizar.

## Common Pitfalls

### Pitfall 1: Cache do Streamlit e objeto pandas dentro de dataclass
**What goes wrong:** Medo de que `@st.cache_data` quebre ao retornar um `CompanyData` que agora contém um `pd.Series`.
**Why it happens:** `st.cache_data` serializa o retorno com pickle. Houve regressões em algumas versões (ex.: issue #11528 ~v1.44) com classes custom.
**How to avoid:** Um `@dataclass` simples contendo um `pd.Series`/`DataFrame` **é picklável** — pandas é pickle-compatível e dataclasses padrão também. O caso problemático é classe custom com `__reduce__`/slots exóticos, que NÃO é o caso aqui. `CompanyData` é dataclass puro. Risco baixo, mas: testar o app de ponta a ponta uma vez (`streamlit run app.py`) após a mudança. `[VERIFIED: docs.streamlit.io caching; CITED: github #11528]`
**Warning signs:** `UnserializableReturnValueError` ou warning de cache no terminal ao analisar uma ação.

### Pitfall 2: `use_container_width` deprecado
**What goes wrong:** Copiar exemplo antigo com `st.plotly_chart(fig, use_container_width=True)` → warning de deprecação no terminal.
**How to avoid:** Usar `width="stretch"` (Streamlit 1.58 já suporta). `[VERIFIED: docs.streamlit.io]`
**Warning signs:** Aviso amarelo de deprecação no console do Streamlit.

### Pitfall 3: Gaps/NaN na série e índice de datas
**What goes wrong:** `tk.history` pode trazer linhas com `NaN` no Close (pregões sem fechamento, feriados parciais); o índice é tz-aware (`DatetimeIndex` com timezone).
**How to avoid:** `hist["Close"].dropna()` na origem (Pattern 1). Plotly lida bem com `DatetimeIndex` no eixo X (formata sozinho). NaN remanescente vira gap na linha — `dropna` evita. Não converter timezone: Plotly só usa as datas para o eixo.
**Warning signs:** Buracos na linha do gráfico ou pontos de hover com "R$ nan".

### Pitfall 4: Quebrar os golden tests com import pesado
**What goes wrong:** Importar `plotly` no topo de um módulo da engine (`prices.py`, `fundamentals.py`) que os testes carregam.
**How to avoid:** **Plotly só é importado em `app.py`** (camada UI). A engine só ganha um campo de tipo `Optional[pd.Series]` (pandas já é dep). Testes não importam `app.py`. Verificado: 62 testes passam offline; nenhum constrói `DadosMercado` ou chama `coletar_mercado` (só `test_ingest_resolucao` mexe em ingest, e via resolução de ticker, não preços). `[VERIFIED: pytest run + grep]`
**Warning signs:** `ModuleNotFoundError: plotly` em pytest (não deveria acontecer se o import ficar em app.py).

## Code Examples

### Bloco completo de render na Tela 1 (entre alertas e st.tabs)
```python
# app.py — inserir após o loop de alertas (~linha 124), ANTES de `tab1, tab2, tab3 = st.tabs(...)` (D-03)
import plotly.graph_objects as go  # import local no bloco da Tela 1 (ou topo de app.py)

st.markdown("**Evolução do preço (5 anos) vs. valor intrínseco**")
serie = getattr(c, "serie_precos", None)
if serie is None or len(serie) == 0:
    st.info("📉 Gráfico de preço indisponível agora (fonte Yahoo instável). "
            "Os fundamentos e o valor intrínseco seguem válidos.")  # D-05 / GRAF-03
else:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=serie.index, y=serie.values, mode="lines", name="Preço",
        line=dict(color="#1f77b4", width=2),
        hovertemplate="%{x|%d/%m/%Y}<br>R$ %{y:.2f}<extra></extra>",
    ))
    if a.vmin is not None and a.vmax is not None:           # D-06: sem banda se DDM None
        fig.add_hrect(y0=a.vmin, y1=a.vmax, line_width=0,
                      fillcolor="green", opacity=0.12,
                      annotation_text="Valor intrínseco (DDM)",
                      annotation_position="top left")
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10),
                      yaxis_title="R$", showlegend=False)
    st.plotly_chart(fig, width="stretch")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `st.plotly_chart(fig, use_container_width=True)` | `st.plotly_chart(fig, width="stretch")` | Streamlit 2025 release; aviso até 2025-12-31 | Usar a nova assinatura para não logar deprecação |
| `st.plotly_chart(fig, **kwargs)` p/ config | `st.plotly_chart(fig, config={...})` | mesma janela | Se precisar de config Plotly, usar `config=` |

**Deprecated/outdated:**
- `use_container_width` em `st.plotly_chart`/`st.dataframe`: substituído por `width=`. (O resto do `app.py` ainda usa `use_container_width=True` nos `st.dataframe` — fora de escopo mudar agora; mas o gráfico novo já deve nascer com `width="stretch"`.)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `CompanyData` com `pd.Series` continua picklável sob `@st.cache_data` na 1.58.0 sem erro | Pitfall 1 | Baixo — dataclass puro + pandas é picklável; mitigação = teste manual 1x no app |
| A2 | Estilo exato (cor `#1f77b4`, `opacity=0.12`, altura 380, annotation) | Code Examples | Nenhum — D-04/discrição do executor; é só estética, ajustável |
| A3 | Importar `plotly` apenas em `app.py` mantém pytest offline | Pitfall 4 | Baixo — verificado que testes não importam app.py |

## Open Questions

1. **Campo: `pd.Series` vs. listas paralelas (datas[], closes[])?**
   - O que sabemos: `tk.history()` devolve `pd.Series` nativa; Plotly aceita `serie.index`/`serie.values` direto. A discrição é do executor (CONTEXT.md).
   - O que é incerto: se algum dia a série precisar ser serializada para JSON/cache disco (não é o caso). `pd.Series` é o caminho de menor atrito hoje.
   - Recomendação: **usar `pd.Series`** (zero conversão, picklável, índice de datas já pronto). Só migrar para listas se A1 falhar no teste manual.

2. **Annotation da banda polui o estilo limpo (D-04)?**
   - O que sabemos: D-04 pede "limpo". A annotation textual ajuda a legibilidade mas adiciona ruído.
   - Recomendação: incluir a annotation discreta (top-left, pequena) — comunica a banda sem cor de área. Executor pode remover se preferir e expor o intervalo só no hover/legenda. Não é bloqueante.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| plotly | GRAF-01/02 (gráfico) | ✗ (precisa instalar) | latest 6.8.0 no PyPI | Nenhum — é a lib central da fase; instalar |
| streamlit | UI render | ✓ | 1.58.0 | — |
| pandas | série de preços | ✓ | >=2.0 | — |
| yfinance | série já baixada (sem nova chamada) | ✓ | >=0.2.40 | Série None → D-05/GRAF-03 |

**Missing dependencies with no fallback:**
- `plotly` — não instalado. Bloqueante até `pip install plotly>=6.0` + linha no `requirements.txt`. Sem alternativa (Plotly é locked por roadmap/REQUIREMENTS).

**Missing dependencies with fallback:**
- Nenhuma.

## Project Constraints (from CLAUDE.md)

- **Stack:** Python 3 + Streamlit; sem backend próprio; **custo zero** (só dados grátis) → ✔ a fase não adiciona chamada de rede nem dado pago; reusa série já baixada.
- **Compatibility:** golden tests em `tests/` devem continuar verdes → ✔ verificado (62 passam offline; campo opcional não os afeta).
- **Idioma:** respostas em PT-BR; comentários só quando o "porquê" não é óbvio.
- **Não adicionar features além do pedido / preferir editar arquivos existentes a criar novos** → ✔ a fase edita 4 arquivos existentes, cria zero arquivos novos.
- **Validação só em bordas** → o fallback de série (D-05) é exatamente uma borda (input externo Yahoo).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Valor intrínseco vira **banda horizontal sombreada** entre `a.vmin` e `a.vmax` (não linha única, não ponto médio).
- **D-02:** Banda **horizontal/plana** ao longo dos 5 anos; sem recálculo de intrínseco histórico.
- **D-03:** Gráfico no **topo da aba Analisar**, abaixo das 5 métricas e do veredito colorido, **antes dos sub-tabs** (`st.tabs`).
- **D-04:** Estilo **limpo**: linha de preço + banda sutil. Sem sombrear área desconto/prêmio; sem marcar o ponto do preço atual.
- **D-05:** Série indisponível → aviso claro espelhando o padrão "preço atual indisponível" (app.py:116-120). A aba **não pode quebrar** (GRAF-03).
- **D-06:** DDM não calculado (`a.vmin`/`a.vmax` None) → desenhar **apenas a linha de preço**, sem banda.

### Claude's Discretion
- Conteúdo do hover, títulos de eixos, paleta exata da banda/linha, altura do gráfico, e **como exatamente a série é carregada** na estrutura `DadosMercado`/`CompanyData` (tipo do campo — `pd.Series` vs listas), desde que respeite as decisões acima e **não torne os golden tests dependentes de rede**.

### Deferred Ideas (OUT OF SCOPE)
- Sombrear área desconto/prêmio (verde/vermelho) e marcar o ponto do preço atual.
- Seletor de período além de 5a / gráficos nas Telas 2 e 3 (Garimpar/Ranking).
- Nova chamada de rede só para o gráfico; qualquer alteração em fórmula de valuation.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GRAF-01 | Gráfico interativo (Plotly) do preço de fechamento 5a, com zoom e hover | `go.Scatter` da série preservada de `hist["Close"]`; zoom/hover são nativos do Plotly (Pattern 1+2, Code Examples). Stack: `plotly>=6.0` + `st.plotly_chart(fig, width="stretch")`. |
| GRAF-02 | Sobrepor ao preço a banda do valor intrínseco DDM, evidenciando margem de segurança | `fig.add_hrect(y0=a.vmin, y1=a.vmax)` — banda horizontal plana (D-01/D-02); vmin/vmax já vêm de `analisar_acao` (não recalcular). Posição relativa preço-vs-banda comunica desconto/prêmio (D-04). |
| GRAF-03 | Série indisponível → degrada graciosamente com aviso, sem quebrar a aba | Fallback `if serie is None or len(serie)==0: st.info(...)` espelhando app.py:116-120 (D-05, Pattern 3). DDM None → só a linha (D-06). |
</phase_requirements>

## Sources

### Primary (HIGH confidence)
- Codebase: `src/analista/ingest/prices.py` (origem da série, linha 94/98), `build.py` (threading), `report.py` (`a.vmin/a.vmax`), `app.py` Tela 1 (ponto de render, padrão de aviso), `core/fundamentals.py` (`CompanyData`), `tests/` (62 testes offline, passam em 0.85s).
- `pip index versions plotly` → última versão 6.8.0; plotly não instalado no venv.
- `import streamlit` → 1.58.0 instalado.
- docs.streamlit.io/develop/api-reference/charts/st.plotly_chart — `use_container_width` deprecado → `width="stretch"`; `**kwargs`→`config`.

### Secondary (MEDIUM confidence)
- plotly.com/python/horizontal-vertical-shapes/ — `add_hrect(y0, y1, fillcolor, opacity)` para banda horizontal preenchida.
- docs.streamlit.io/develop/concepts/architecture/caching — `cache_data` usa pickle; objetos pandas em dataclass são pickláveis.

### Tertiary (LOW confidence)
- github.com/streamlit/streamlit/issues/11528 — regressão de serialização de classes custom em ~v1.44 (não aplicável a dataclass puro, mas motivou o teste manual recomendado em Pitfall 1).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versões verificadas no PyPI/venv; Plotly é locked pelo roadmap.
- Architecture: HIGH — cadeia de threading já existe e foi lida linha a linha; campo novo segue padrão idêntico aos campos existentes.
- Pitfalls: HIGH — testes rodados (62 verdes offline), deprecação confirmada na doc oficial; único risco residual (pickle de dataclass+Series) é baixo e tem mitigação por teste manual.

**Research date:** 2026-06-23
**Valid until:** 2026-07-23 (stack estável; revalidar se Streamlit subir major ou Plotly 7 sair)
