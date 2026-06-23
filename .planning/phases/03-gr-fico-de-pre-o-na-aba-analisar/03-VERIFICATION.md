---
phase: 03-gr-fico-de-pre-o-na-aba-analisar
verified: 2026-06-23T00:00:00Z
status: human_needed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification: false
human_verification:
  - test: "Abrir o app com `streamlit run app.py`, analisar TAEE11 (ou EGIE3). Confirmar que na aba Analisar aparece um gráfico de linha (preço 5a) ANTES dos sub-tabs, com zoom por arrastar/scroll e tooltip de data+R$ ao passar o mouse."
    expected: "Gráfico aparece acima do st.tabs, zoom e hover funcionam nativamente (Plotly go.Scatter)."
    why_human: "Zoom e hover são comportamentos de runtime do navegador — não verificáveis por grep/AST. O checkpoint do Plano 02 foi reportado como aprovado no SUMMARY, mas SUMMARYs não são evidência."
  - test: "Com a mesma análise de TAEE11, verificar a banda verde horizontal do valor intrínseco (DDM) sobreposta ao gráfico."
    expected: "Uma faixa verde sutil (opacity 0.12) entre vmin e vmax do DDM é visível, com a annotation 'Valor intrínseco (DDM)'."
    why_human: "A visibilidade da banda (cor, opacidade, posição relativa ao preço) é qualidade de exibição que só o navegador pode confirmar."
  - test: "Verificar no terminal do Streamlit a ausência de: (a) warning de deprecação de `use_container_width`; (b) `UnserializableReturnValueError` de cache; (c) qualquer traceback."
    expected: "Terminal limpo — nenhum dos três warnings."
    why_human: "Warnings de runtime do Streamlit não são verificáveis em AST estático."
---

# Phase 3: Gráfico de Preço na aba Analisar — Verification Report

**Phase Goal:** Ao analisar uma ação, o usuário vê na aba "Analisar" um gráfico interativo da evolução do preço dos últimos 5 anos com a linha do valor intrínseco do DDM sobreposta, deixando a margem de segurança visível — reaproveitando a série que a engine já baixa (sem nova chamada de rede) e sem alterar nenhum cálculo de valuation.
**Verified:** 2026-06-23
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Na aba "Analisar", o usuário vê uma linha do preço de fechamento dos últimos 5 anos, com zoom e hover interativos (Plotly). | VERIFIED (code) / HUMAN NEEDED (runtime UX) | `app.py:12` `import plotly.graph_objects as go`; `app.py:137-142` `go.Figure()` + `go.Scatter(x=serie.index, y=serie.values, mode="lines")` com `hovertemplate`. Zoom/hover são nativos do Plotly — mas comportamento de browser requer confirmação humana. |
| 2 | Uma linha/referência horizontal marca o valor intrínseco do DDM sobre a série de preço, tornando a margem de segurança visível. | VERIFIED (code) / HUMAN NEEDED (visibilidade) | `app.py:144-148` `fig.add_hrect(y0=a.vmin, y1=a.vmax, line_width=0, fillcolor="green", opacity=0.12, annotation_text="Valor intrínseco (DDM)")`, guardado por `if a.vmin is not None and a.vmax is not None`. |
| 3 | Quando a série histórica de preços está indisponível (falha do Yahoo), a aba mostra um aviso claro em vez de quebrar. | VERIFIED | `app.py:130-135`: `if serie is None or len(serie) == 0: st.info(...)`. `tab1, tab2, tab3 = st.tabs([...])` na linha 155 está FORA do bloco if/else — a aba continua para st.tabs independentemente do fallback. Espelha tom do aviso de preço atual (linha 117-121). |
| 4 | `pytest` continua verde — nenhum golden test quebra (nenhuma fórmula de valuation alterada). | VERIFIED | `./.venv/bin/python -m pytest -q` → `62 passed in 0.60s`. Nenhum arquivo em `tests/` modificado (grep `serie_precos tests/` retornou vazio — campo novo não foi adicionado nos testes, mas os 62 testes existentes passam). |

**Score:** 4/4 truths verified in code. 3 items require human runtime confirmation.

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/ingest/prices.py` | Campo `serie_precos` em `DadosMercado` + `dm.serie_precos = hist["Close"].dropna()` no fetch existente | VERIFIED | L58: `serie_precos: Optional["pd.Series"] = None`; L100: `dm.serie_precos = hist["Close"].dropna()` dentro do `if hist is not None and not hist.empty:` existente. `auto_adjust=True` (L95) — ver nota CR-01 abaixo. |
| `src/analista/core/fundamentals.py` | Campo `serie_precos` em `CompanyData` (snapshot de mercado) | VERIFIED | L45: `serie_precos: Optional["pd.Series"] = None` no bloco "snapshot atual / mercado". Forward-ref `Optional["pd.Series"]` — sem `import pandas` no topo. |
| `src/analista/ingest/build.py` | `c.serie_precos = dm.serie_precos` em `montar_empresa` | VERIFIED | L41: `c.serie_precos = dm.serie_precos` no bloco de campos de mercado (entre `ano_dpa` e `eh_concessionaria`). Cópia direta de Optional, sem lógica condicional. |
| `requirements.txt` | Pin de `plotly` | VERIFIED | Linha 11: `plotly>=6.0`. Versão instalada no venv: `6.8.0`. |
| `app.py` | Bloco de render Plotly na Tela 1, entre o loop de alertas e `st.tabs` (D-03) | VERIFIED | L12: `import plotly.graph_objects as go`; L127-153: bloco de gráfico inserido após o loop de alertas (L123-125) e antes de `tab1, tab2, tab3 = st.tabs([...])` (L155). `st.plotly_chart(fig, width="stretch")` na L153 — sem `use_container_width`. Sintaxe válida (`ast.parse` limpo). |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `prices.py` | `DadosMercado.serie_precos` | `dm.serie_precos = hist["Close"].dropna()` dentro do bloco `if hist` existente | WIRED | L100 — atribuição confirmada, sem nova rede. |
| `build.py` | `CompanyData.serie_precos` | `c.serie_precos = dm.serie_precos` em `montar_empresa` | WIRED | L41 — cópia direta; padrão idêntico aos demais campos de mercado (`preco_atual`, `beta`, etc.). |
| `app.py Tela 1` | `c.serie_precos` | `serie = c.serie_precos` → `go.Scatter(x=serie.index, y=serie.values)` | WIRED | L129, L138-142 — série lida do escopo e usada no render. |
| `app.py Tela 1` | `a.vmin / a.vmax` | `fig.add_hrect(y0=a.vmin, y1=a.vmax, ...)` guardado por sentinela `None` (D-01/D-02/D-06) | WIRED | L144-148 — mesma sentinela `if a.vmin is not None and a.vmax is not None` que o veredito usa (L108). |
| `app.py import` | `plotly.graph_objects` | `import plotly.graph_objects as go` no topo de `app.py` | WIRED | L12 — importado na camada UI; engine permanece sem plotly. |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `app.py` render block | `serie = c.serie_precos` | `hist["Close"].dropna()` de `tk.history(period="5y", auto_adjust=True)` (Yahoo Finance) | Sim — fetch real do Yahoo; `None` apenas em falha de rede (tratada pelo fallback) | FLOWING |
| `app.py` render block | `a.vmin`, `a.vmax` | `report.analisar_acao(c, CFG)` — DDM real da engine (fases anteriores) | Sim — cálculo DDM real; `None` quando beta/payout/crescimento faltam (tratado pelo guard D-06) | FLOWING |

**Nota CR-01 (price basis):** A série que flui para o gráfico usa `auto_adjust=True` (preços retroajustados por proventos/desdobramentos), enquanto `preco_atual` (mostrado na métrica acima) e `vmin/vmax` (banda DDM) são valores nominais em R$ correntes. Para pagadoras de dividendos com histórico longo, os preços antigos da série aparecem sistematicamente abaixo do valor nominal histórico real. Isso não impede o render, mas cria uma inconsistência de base entre o eixo Y da série e a banda DDM. Classificado como WARNING — ver seção de Anti-Patterns.

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| pytest verde, nenhuma fórmula alterada | `./.venv/bin/python -m pytest -q` | `62 passed in 0.60s` | PASS |
| `app.py` tem sintaxe Python válida | `./.venv/bin/python -c "import ast; ast.parse(open('app.py').read())"` | `app.py parses OK` (exit 0) | PASS |
| plotly importável no venv | `./.venv/bin/python -c "import plotly; print(plotly.__version__)"` | `6.8.0` | PASS |
| engine modules importam sem deps novas | `./.venv/bin/python -c "import analista.ingest.prices; import analista.core.fundamentals; import analista.ingest.build"` | `engine imports clean` (exit 0) | PASS |
| st.plotly_chart sem `use_container_width` | `grep -n 'use_container_width' app.py | grep -i plotly` | sem output | PASS |
| `c.serie_precos` lida no render de app.py | `grep -n 'c\.serie_precos' app.py` | `129: serie = c.serie_precos` | PASS |
| `add_hrect` presente em app.py | `grep -n 'add_hrect' app.py` | `145: fig.add_hrect(...)` | PASS |
| gráfico inserido antes de `st.tabs` (D-03) | `grep -n 'tab1.*st.tabs\|add_hrect\|st.plotly_chart' app.py` (comparar linhas) | `add_hrect` L145, `st.plotly_chart` L153, `st.tabs` L155 — gráfico antes dos tabs | PASS |

---

## Probe Execution

Não aplicável — fase não declara probes e não é fase de migração/tooling.

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| GRAF-01 | 03-01-PLAN, 03-02-PLAN | Gráfico interativo (Plotly) de preço de fechamento 5a com zoom e hover | VERIFIED (code) / HUMAN NEEDED (browser) | `go.Scatter(mode="lines")` em app.py; zoom/hover nativos do Plotly — confirmação visual necessária |
| GRAF-02 | 03-01-PLAN, 03-02-PLAN | Sobreposição do valor intrínseco/preço-alvo do DDM no gráfico (margem de segurança visível) | VERIFIED (code) / HUMAN NEEDED (visual) | `fig.add_hrect(y0=a.vmin, y1=a.vmax)` em app.py:145-148 |
| GRAF-03 | 03-01-PLAN, 03-02-PLAN | Degradação graciosa com aviso quando série indisponível | VERIFIED | `if serie is None or len(serie) == 0: st.info(...)` em app.py:130-135; st.tabs segue na L155 |

Todos os 3 requisitos mapeados. Nenhum requisito da fase ficou sem plano (0 orphaned).

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/analista/ingest/prices.py` | 95 | `tk.history(period="5y", auto_adjust=True)` — série exibida no gráfico é retroajustada por proventos; `preco_atual` e banda DDM são nominais (CR-01 do REVIEW.md) | WARNING | Inconsistência de base de preço entre o eixo Y da série e a banda DDM; para pagadoras de dividendos em 5 anos, os preços históricos aparecem sistematicamente abaixo dos reais, podendo induzir leitura de "margem de segurança" distorcida. |
| `src/analista/ingest/prices.py` | 94 | `except Exception: hist = None` — captura qualquer exceção silenciosamente, incluindo bugs de programação | WARNING | Um typo ou `KeyError` futuro no bloco de fetch fica indistinguível de instabilidade do Yahoo; falhas estruturais ficam mudas. (WR-04 do REVIEW.md) |
| `app.py` | 23 | `import yaml` após `ROOT = ...` (L22) — fora do bloco de imports do topo (L9-20) | INFO | Viola PEP 8; cosmético, sem impacto funcional. (IN-01 do REVIEW.md) |
| `src/analista/ingest/prices.py` | 127 | `import pandas as pd` tardio dentro do `try` de dividendos | INFO | Dependência oculta, re-importada a cada chamada; não economiza nada pois o módulo já usa pandas extensivamente. (IN-02 do REVIEW.md) |

**Notas sobre classificação:**

- **CR-01 (auto_adjust=True)**: O code review classificou como BLOCKER, mas para fins de verificação de *goal achievement* a feature está entregue — o gráfico renderiza, a banda é sobreposta, e o usuário PODE identificar margem de segurança. No entanto, a inconsistência de base viola o "core value" do projeto ("a mesma ação não pode parecer barata num lugar e cara em outro sem explicação"). Classifico como WARNING de verificação, mas recomendo fortemente correção antes de uso em produção. Não há override declarado no PLAN para este ponto.
- **WR-01 (nenhum teste para serie_precos)**: O campo entrou sem cobertura de teste, em especial sem nenhum teste que trave o CR-01. Classificado como WARNING.
- **WR-02 (vmin == vmax → banda invisible)**: Caso de borda documentado no REVIEW.md — quando os dois cenários DDM convergem para o mesmo valor, `add_hrect` produz um retângulo de altura zero. Sem override. WARNING.
- **WR-03 (period="5y" fixo vs. ano_base)**: O gráfico vai de hoje - 5 anos, mas a análise é ancorada em `ano_base`. Se `ano_base=2024` e hoje é 2026, a curva inclui 2 anos além da janela de fundamentos. WARNING.
- Nenhum marcador de dívida (`TBD`, `FIXME`, `XXX`) encontrado em nenhum dos arquivos modificados.

---

## Human Verification Required

### 1. Gráfico renderiza com zoom e hover (SC #1 / GRAF-01)

**Test:** Rodar `cd "/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos" && ./.venv/bin/streamlit run app.py`, abrir no navegador, modo "Analisar", ticker TAEE11, clicar "Analisar". Arrastar o gráfico para zoom e passar o mouse para ver o tooltip.
**Expected:** Gráfico de linha do preço aparece abaixo das métricas/veredito e ANTES das tabs de "Múltiplos & Crescimento". Zoom e tooltip (data + R$) funcionam interativamente.
**Why human:** Zoom e hover são comportamentos de runtime do navegador — não verificáveis estaticamente. O checkpoint do Plano 02 foi aprovado pelo usuário segundo o SUMMARY, mas SUMMARYs não são evidência verificável.

### 2. Banda DDM visível sobre o gráfico (SC #2 / GRAF-02)

**Test:** Na mesma análise de TAEE11 (cujo DDM deve calcular com vmin/vmax não-None), verificar se uma faixa verde horizontal aparece sobre a linha de preço.
**Expected:** Banda verde sutil (opacity 0.12) entre vmin e vmax, com annotation "Valor intrínseco (DDM)" no canto superior esquerdo. Preço abaixo da banda = desconto; acima = prêmio.
**Why human:** A visibilidade da banda (cor, posição, contraste, se o preço atual está de fato visualmente próximo ao topo/fundo da série) é qualidade de display que só o navegador confirma.

### 3. Ausência de warnings no terminal do Streamlit

**Test:** Observar o terminal onde o Streamlit está rodando durante a análise de TAEE11.
**Expected:** Sem `StreamlitAPIWarning: use_container_width is deprecated`; sem `UnserializableReturnValueError`; sem tracebacks Python.
**Why human:** Warnings de runtime do Streamlit não são verificáveis em análise estática.

---

## Gaps Summary

Nenhum gap de goal achievement detectado. Todos os 4 Success Criteria têm implementação completa e verificável no código. O status `human_needed` se deve exclusivamente à natureza interativa de GRAF-01/GRAF-02 (zoom/hover/visibilidade da banda no browser).

**Itens de qualidade para endereçar após confirmação humana (não bloqueiam o goal, mas são relevantes para o core value do projeto):**

1. **CR-01 (preço ajustado vs. nominal):** Corrigir `auto_adjust=False` (ou usar `Adj Close` apenas para beta/retornos e `Close` sem ajuste para `serie_precos`). Adicionar teste golden que trave `serie_precos.iloc[-1] ≈ preco_atual`.
2. **WR-01 (sem teste para serie_precos):** Adicionar teste que cubra: (a) serie_precos preenchida corretamente; (b) serie_precos None quando hist vazio; (c) consistência com preco_atual.
3. **WR-02 (vmin == vmax → banda invisível):** Adicionar guard `if a.vmin == a.vmax: fig.add_hline(...)` como alternativa visual.
4. **WR-03 (period="5y" fixo vs. ano_base):** Alinhar janela da série ao horizonte da análise ou rotular explicitamente no gráfico.

---

_Verified: 2026-06-23_
_Verifier: Claude (gsd-verifier)_
