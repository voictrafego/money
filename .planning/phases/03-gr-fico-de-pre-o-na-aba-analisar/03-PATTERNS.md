# Phase 3: Gráfico de Preço na aba Analisar - Pattern Map

**Mapped:** 2026-06-23
**Files analyzed:** 5 (todos modificados; zero novos)
**Analogs found:** 5 / 5 (todos os análogos vivem NO MESMO arquivo que será editado)

> Fase aditiva. Cada mudança imita um padrão **já presente no próprio arquivo** —
> não há arquivo novo nem fronteira arquitetural nova. O planner deve copiar a forma
> dos campos/linhas existentes, não inventar estrutura.

## File Classification

| Arquivo modificado | Role | Data Flow | Análogo (mesmo arquivo) | Match |
|--------------------|------|-----------|--------------------------|-------|
| `src/analista/ingest/prices.py` | model + service (dataclass `DadosMercado` + fetch) | request-response (Yahoo) | campos `beta`/`dpa_trailing_12m` no dataclass + atribuição em `coletar_mercado` | exato |
| `src/analista/ingest/build.py` | service (montagem) | transform (dm→c) | linhas `c.preco_atual = dm.preco_atual` etc. (35-39) | exato |
| `src/analista/core/fundamentals.py` | model (dataclass `CompanyData`) | — | campos `preco_atual`/`beta` no bloco "snapshot atual / mercado" (39-48) | exato |
| `app.py` (Tela 1 `🔎`) | UI / view | render | `st.bar_chart` (192), `st.warning` preço indisponível (115-120), `st.info` DDM não calculado (179) | exato |
| `requirements.txt` | config | — | linhas de pin `pandas>=2.0`, `streamlit>=1.30` | exato |

---

## Pattern Assignments

### `src/analista/ingest/prices.py` (model + service)

**Análogo:** o próprio dataclass `DadosMercado` e o bloco `if hist is not None and not hist.empty:` de `coletar_mercado`.

**Padrão de campo opcional no dataclass** (linhas 45-57) — copiar a forma exata dos campos `Optional`:
```python
@dataclass
class DadosMercado:
    ticker: str
    preco_atual: Optional[float] = None
    num_acoes: Optional[float] = None
    ...
    beta: Optional[float] = None
    desempenho_relativo_6m: Optional[float] = None
    ...
    dpa_trailing_12m: Optional[float] = None  # comentário explica o "porquê"
    ano_dpa: Optional[int] = None
```
> Novo campo segue idêntico: `serie_precos: Optional["pd.Series"] = None` com comentário curto
> ("close diário 5a, índice = datas"). `pd` NÃO está importado no topo — `typing` importa só
> `Dict, Optional` (linha 14). Usar forward-ref em string (`Optional["pd.Series"]`) OU importar
> `pandas` no topo. **Não** adicionar `import pandas` no topo do módulo só pelo type hint se a
> string-annotation resolver (mantém o módulo leve — ver Pitfall 4 da research).

**Padrão de preservação dentro do fetch** (linhas 98-102) — a série já existe em `hist["Close"]`; basta atribuir no bloco que JÁ existe, sem nova chamada de rede:
```python
if hist is not None and not hist.empty:
    if dm.preco_atual is None:
        dm.preco_atual = float(hist["Close"].iloc[-1])
    ult_ano = hist.tail(252)
    dm.volume_financeiro_diario = float((ult_ano["Close"] * ult_ano["Volume"]).mean())
```
> Inserir UMA linha aqui (ex.: `dm.serie_precos = hist["Close"].dropna()`), dentro do mesmo
> `if hist is not None and not hist.empty:` — mesma guarda que protege os outros usos de `hist`.
> `.dropna()` segue o tratamento de gaps já mencionado na research (Pitfall 3). `pd` já está
> importado localmente no bloco de dividendos (linha 125) como precedente do projeto para imports
> tardios — mas aqui não é necessário importar pandas: a série sai pronta de `hist["Close"]`.

**Falha graciosa já estabelecida** (linhas 93-96): o `try/except` que define `hist = None` em falha já garante que, quando Yahoo cai, `serie_precos` fica `None` — exatamente o estado que o fallback D-05/GRAF-03 consome. **Não** adicionar try/except novo; o existente já cobre.

---

### `src/analista/ingest/build.py` (service, transform)

**Análogo:** o bloco de cópia `dm → c` em `montar_empresa`.

**Padrão de threading dm→c** (linhas 35-39) — copiar UMA linha no mesmo estilo:
```python
c.preco_atual = dm.preco_atual
c.volume_financeiro_diario = dm.volume_financeiro_diario
c.beta = dm.beta
c.desempenho_relativo_6m = dm.desempenho_relativo_6m
c.dpa_trailing_12m = dm.dpa_trailing_12m  # DY corrente trailing-12m (WR-04)
c.ano_dpa = dm.ano_dpa
```
> Adicionar `c.serie_precos = dm.serie_precos` neste bloco (após a linha 39, junto dos outros
> campos de mercado). Mesma forma, mesma indentação. Nenhuma lógica condicional — é cópia direta
> de Optional (se `dm.serie_precos` for `None`, `c.serie_precos` herda `None`, e o fallback da UI
> trata). Não tocar no loop de anos (45-65), que é só fundamentos CVM.

---

### `src/analista/core/fundamentals.py` (model)

**Análogo:** o bloco "snapshot atual / mercado" do dataclass `CompanyData`.

**Padrão de campo de mercado** (linhas 38-48):
```python
    # snapshot atual / mercado
    preco_atual: Optional[float] = None
    volume_financeiro_diario: Optional[float] = None  # média R$/dia
    desempenho_relativo_6m: Optional[float] = None     # excesso de retorno vs Ibov
    g_lucro_esperado: Optional[float] = None
    beta: Optional[float] = None
    eh_concessionaria: bool = False
    ...
    dpa_trailing_12m: Optional[float] = None
    ano_dpa: Optional[int] = None  # comentário explica uso
```
> Adicionar `serie_precos: Optional["pd.Series"] = None` neste bloco (junto de `preco_atual`,
> conceptualmente "snapshot de mercado"). Imports atuais (linha 13): `from typing import Dict, List, Optional`.
> `pandas` NÃO é importado neste módulo. Usar forward-ref em string (`Optional["pd.Series"]`) para
> evitar import pesado no topo da engine (Pitfall 4: testes carregam este módulo; manter leve).
> **Não** adicionar métodos novos ao dataclass — a série é só transportada, lida direto pela UI.
> Construção por keyword args (linhas 29-34 de build.py) é imune a campo opcional novo → golden tests verdes.

---

### `app.py` — Tela 1 `if modo.startswith("🔎")` (UI / view)

**Análogo:** três padrões já presentes no MESMO bloco da Tela 1.

**1. Ponto de inserção (D-03)** — entre o loop de alertas (122-124) e `st.tabs` (126):
```python
            if a.alertas:
                for al in a.alertas:
                    st.warning(f"⚠️ {al}")

            # ◄── GRÁFICO ENTRA AQUI (depois dos alertas, antes do st.tabs)

            tab1, tab2, tab3 = st.tabs(["📈 Múltiplos & Crescimento", "💵 Valuation (DDM)", "📋 Fundamentos (10 anos)"])
```
> No escopo deste `else` (linha 91+), `c` (CompanyData) e `a` (AnaliseAcao) JÁ existem
> (`c = montar(...)` linha 87; `a = report.analisar_acao(c, CFG)` linha 92). Logo o gráfico lê
> `c.serie_precos`, `a.vmin`, `a.vmax`, `a.preco_atual` direto — a série NÃO precisa passar por
> `AnaliseAcao`. **Não mover** o `st.tabs` (linha 126).

**2. Fallback série indisponível (D-05 / GRAF-03)** — espelhar o tom/forma do aviso "preço atual indisponível" (linhas 115-120):
```python
            if a.preco_atual is None:
                st.warning(
                    "⚠️ Preço atual indisponível agora (fonte Yahoo instável). Os fundamentos e o "
                    "valor intrínseco (DDM, dados CVM) abaixo seguem válidos — só a comparação de "
                    "preço/veredito fica suspensa até o preço voltar."
                )
```
> Copiar este tom para o caso `c.serie_precos is None or len(c.serie_precos) == 0`: usar
> `st.info`/`st.warning` com mensagem do tipo "Gráfico de preço indisponível agora (fonte Yahoo
> instável); os fundamentos e o valor intrínseco abaixo seguem válidos." A aba **não pode quebrar**:
> o gráfico é um `if/else` — se a série falha, mostra o aviso e segue para `st.tabs`. Mesma
> filosofia "borda do sistema" (input externo Yahoo) do CLAUDE.md.

**3. Fallback DDM não calculado (D-06)** — análogo direto do `st.info` "DDM não calculado" (linha 179):
```python
                else:
                    st.info("DDM não calculado (faltou Beta/Ke, payout ou crescimento). Veja os alertas acima.")
```
> No gráfico, o equivalente é: **desenhar só a linha de preço, sem a banda**, quando
> `a.vmin is None or a.vmax is None`. Guardar a banda atrás de `if a.vmin is not None and a.vmax is not None:`
> — exatamente a mesma condição-sentinela que a UI já usa para o intervalo intrínseco
> (linha 107: `if a.vmin is not None and a.vmax is not None else "—"`) e para o veredito
> (linhas 118-124). **Reusar a mesma guarda** mantém os três fallbacks coerentes (CONTEXT.md:
> "sem inventar um terceiro padrão").

**4. Render de chart já no arquivo** — `st.bar_chart` (linha 192) é o precedente de "renderizar gráfico no fim de um bloco". Plotly entra como gráfico NOVO via `st.plotly_chart`. Import: hoje o topo do app importa `import pandas as pd` / `import streamlit as st` (linhas 11-12) e libs da engine (14-19). Adicionar `import plotly.graph_objects as go` — preferir no topo de `app.py` (consistente com os outros imports de topo); plotly NUNCA entra em módulos da engine (Pitfall 4).

> **Atenção à assinatura**: o resto do `app.py` usa `use_container_width=True` (linhas 83, 145, 146, 156, 167, 177, 191) — está DEPRECADO mas fora de escopo mudar. O gráfico NOVO deve nascer com `st.plotly_chart(fig, width="stretch")` (research State of the Art / Pitfall 2). Não replicar `use_container_width` no chart novo.

**5. Título de seção** — precedente de markdown como cabeçalho de bloco (linhas 131, 148, 160, 170). Usar `st.markdown("**...**")` (opcionalmente com `help=h(...)`) acima do gráfico, no mesmo estilo.

---

### `requirements.txt` (config)

**Análogo:** as linhas de pin existentes.
```
pandas>=2.0
numpy>=1.24
...
streamlit>=1.30
```
> Adicionar `plotly>=6.0` seguindo o padrão "minor floor, não exato" (research). plotly NÃO está
> instalado no venv — após editar, rodar `./.venv/bin/pip install "plotly>=6.0"`. Manter o estilo
> de blocos do arquivo (engine no topo, streamlit separado por linha em branco no fim — plotly pode
> ir junto do streamlit, ambos camada de apresentação).

---

## Shared Patterns

### Sentinela "None → degrada, não quebra"
**Fontes:** `prices.py` (try/except → `hist = None`, linhas 93-96), `app.py` (linhas 107, 115-124, 179).
**Aplica a:** todos os fallbacks do gráfico.
A engine deixa `serie_precos = None` em falha do Yahoo (mesmo try/except que zera `hist`); a UI já testa `is None` antes de usar (`if a.preco_atual is None`, `if a.vmin is not None and a.vmax is not None`). O gráfico reusa essas duas mesmas sentinelas:
- série `None`/vazia → aviso (espelha 115-120), pula o `go.Figure`;
- `vmin`/`vmax` `None` → linha sem banda (espelha guarda 107).

### Threading de campo Optional pela cadeia dm→c
**Fontes:** `prices.py` (dataclass `DadosMercado`) → `build.py` (linhas 35-39) → `fundamentals.py` (dataclass `CompanyData`).
**Aplica a:** o novo campo `serie_precos`.
Padrão repetido para CADA campo de mercado: declarar `Optional[...] = None` nos dois dataclasses, copiar `c.X = dm.X` em `montar_empresa`. Zero lógica condicional na cópia. `serie_precos` é o N-ésimo campo a percorrer o mesmo cano.

### Import pesado tardio / fora da engine
**Fontes:** `prices.py` (`import yfinance` em `_yf()` linha 28; `import pandas` local linha 125), `app.py` (imports de topo).
**Aplica a:** `import plotly` (só em `app.py`) e ao type-hint `pd.Series` (forward-ref em string nos dataclasses da engine).
Convenção do projeto: dependências pesadas/UI não entram no topo de módulos da engine que os testes carregam. plotly → só `app.py`. `pd.Series` em annotation → string forward-ref para não forçar `import pandas` no topo de `fundamentals.py`.

### Formatação e estética (discrição do executor)
**Fonte:** helpers `fmt_rs`/`fmt_pct`/`fmt_num` (app.py 48-57).
**Aplica a:** rótulos/hover do gráfico, se quiser exibir valores formatados em R$. Cor, opacidade, altura, annotation da banda são discrição (D-04 + Assumptions A2 da research).

---

## No Analog Found

Nenhum. Todos os 5 arquivos têm análogo direto no próprio arquivo. O único elemento "novo no stack" é a biblioteca **Plotly** (`go.Figure`/`add_hrect`/`st.plotly_chart`) — para a forma exata desse código (não há precedente Plotly no repo), o planner deve usar os exemplos da **RESEARCH.md** (Pattern 2, Code Examples linhas 227-252), que já estão prontos e alinhados a D-01..D-06.

| Elemento | Role | Fonte do padrão |
|----------|------|-----------------|
| `go.Figure` + `go.Scatter` + `add_hrect` + `st.plotly_chart(..., width="stretch")` | UI render | RESEARCH.md Pattern 2 / Code Examples (não há análogo Plotly no codebase) |

---

## Metadata

**Análogos buscados em:** `src/analista/ingest/`, `src/analista/core/`, `src/analista/report/`, `app.py`, `requirements.txt`.
**Arquivos lidos:** `prices.py` (142 ln, completo), `build.py` (69 ln, completo), `fundamentals.py` (1-75 + grep), `app.py` (1-200, Tela 1 completa), `report.py` (grep de vmin/vmax/preco_atual), `requirements.txt` (completo).
**Data de extração:** 2026-06-23
