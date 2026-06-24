# Phase 3: Gráfico de Preço na aba Analisar - Context

**Gathered:** 2026-06-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Marco aditivo pequeno (v1.1). Preservar a série diária de preço de fechamento dos
últimos 5 anos que `ingest/prices.py` já baixa para liquidez/beta/desempenho e hoje
**descarta**, conduzi-la pela cadeia `DadosMercado → build → report → app.py`, e
renderizá-la com **Plotly** na aba "Analisar", sobrepondo a referência do valor
intrínseco do DDM já calculado pela engine.

**Dentro do escopo:** preservar a série; threading pela cadeia existente; gráfico Plotly
de preço 5a; banda intrínseca sobreposta; degradação graciosa quando a série falha;
`plotly` no `requirements.txt`.

**Fora do escopo:** nova chamada de rede só para o gráfico (reusar o cache de 1h e o
fetch que já acontece); qualquer alteração em fórmula de valuation; seletor de período
além dos 5a (zoom nativo do Plotly já cobre); gráficos nas Telas 2/3 (Garimpar/Ranking).

</domain>

<decisions>
## Implementation Decisions

### Representação do valor intrínseco
- **D-01:** A engine produz um **intervalo** (`a.vmin`–`a.vmax` = conservador modelo H /
  otimista g constante, já calculado em `report.analisar_acao`). No gráfico isso vira uma
  **banda horizontal sombreada** entre `vmin` e `vmax` — coerente com o que a UI já mostra
  ("intervalo intrínseco R$ vmin–vmax" nas métricas e no veredito). Não usar linha única
  nem ponto médio (esconderia a faixa de incerteza que o resto do app expõe).
- **D-02:** A banda é **horizontal/plana** ao longo dos 5 anos (referência do "quanto vale
  hoje", conforme SC #2 do roadmap: "linha/referência horizontal"). Não há tentativa de
  recalcular intrínseco histórico.

### Posição na aba Analisar
- **D-03:** O gráfico fica no **topo da aba Analisar, logo abaixo das 5 métricas e do
  veredito colorido, antes dos sub-tabs** (Múltiplos / Valuation DDM / Fundamentos).
  Máxima visibilidade — a margem de segurança aparece junto do veredito. Não vira sub-tab
  nem entra dentro do sub-tab Valuation.

### Destaque da margem de segurança
- **D-04:** Estilo **limpo**: linha de preço + banda intrínseca com cor sutil. A relação
  desconto/prêmio é comunicada pela posição relativa preço-vs-banda, sem sombrear a área
  entre preço e intrínseco e sem marcar o ponto do preço atual. Baixo risco visual, menos
  código.

### Degradação e fallbacks (derivadas das escolhas acima + padrões existentes)
- **D-05:** **Série de preço indisponível** (Yahoo falhou; `hist` vazio/None em
  `prices.py`): no lugar do gráfico, exibir aviso claro seguindo o padrão já existente do
  aviso "preço atual indisponível agora (fonte Yahoo instável)" em `app.py` (Tela 1). A
  aba **não pode quebrar** (GRAF-03).
- **D-06:** **DDM não calculado** (faltou Beta/Ke/payout → `a.vmin`/`a.vmax` = None, mesmo
  caso do `st.info` "DDM não calculado" no sub-tab Valuation): desenhar **apenas a linha de
  preço, sem a banda** intrínseca.

### Claude's Discretion
- Conteúdo do hover, títulos de eixos, paleta exata da banda/linha, altura do gráfico, e
  como exatamente a série é carregada na estrutura `DadosMercado`/`CompanyData` (ex.: tipo
  do campo — pandas Series vs listas de datas/closes) ficam a critério do planner/executor,
  desde que respeitem as decisões acima e não tornem os golden tests dependentes de rede.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap e requisitos
- `.planning/ROADMAP.md` — Phase 3 "Gráfico de Preço na aba Analisar" (Goal + 4 Success
  Criteria; marco v1.1).
- `.planning/REQUIREMENTS.md` — GRAF-01 (linha de preço 5a interativa Plotly), GRAF-02
  (banda/linha intrínseca sobreposta evidenciando margem de segurança), GRAF-03 (degradação
  graciosa) + bloco "Constraints" (reusar série já baixada, `plotly` no requirements,
  nenhuma fórmula alterada, golden tests verdes).

### Código a preservar/threading (cadeia da série)
- `src/analista/ingest/prices.py` — `coletar_mercado()` baixa `hist = tk.history(period="5y")`
  (close auto-ajustado) e usa só para liquidez/beta/desempenho; a série de close é
  **descartada**. É o ponto de origem onde a série deve ser preservada no `DadosMercado`.
- `src/analista/ingest/build.py` — `montar_empresa()` copia campos de `DadosMercado` para
  `CompanyData` (ex.: `c.preco_atual = dm.preco_atual`). Aqui a série passa de `dm` para `c`.
- `src/analista/report/report.py` — `AnaliseAcao` / `analisar_acao()`; expõe `a.vmin`,
  `a.vmax`, `a.preco_atual`, `a.ddm_constante`/`a.ddm_h`. Origem da banda intrínseca.
- `app.py` (Tela 1, bloco `if modo.startswith("🔎")`, ~linhas 78–192) — onde o gráfico é
  renderizado (topo, abaixo do veredito/métricas, antes de `st.tabs`). Contém o padrão do
  aviso "preço atual indisponível" (linhas 115–120) a ser espelhado em GRAF-03 e o `st.info`
  de "DDM não calculado" (linha 179).
- `tests/` — golden tests `test_ddm.py`, `test_multiples.py`, `test_comparables.py`,
  `test_screening.py` (mais `test_consistencia_modos.py`, `test_fundamentals_consistencia.py`,
  `test_ingest_resolucao.py`) devem continuar verdes.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `prices.coletar_mercado()`: já faz `tk.history(period="5y", auto_adjust=True)` — a série
  de close existe em memória; basta não descartá-la (sem nova chamada de rede).
- Cache de 1h: `@st.cache_data(ttl=3600)` em `montar()` (app.py) — a série herda esse cache,
  não há custo extra de rede ao re-renderizar.
- `DadosMercado` (dataclass em prices.py) e `CompanyData` (campos copiados em build.py) são
  os carregadores naturais da série até a UI.
- Padrão de aviso de indisponibilidade do Yahoo já existe em app.py (Tela 1) — reusar tom e
  formato para GRAF-03.

### Established Patterns
- A UI já distingue "preço atual indisponível" (preço None) e "DDM não calculado"
  (vmin/vmax None) com mensagens próprias — os fallbacks do gráfico devem se encaixar nesses
  dois estados sem inventar um terceiro padrão.
- Streamlit já é a camada de apresentação; hoje usa `st.bar_chart`/`st.dataframe`. Plotly é
  novo no stack (entra via `st.plotly_chart` + `plotly` no requirements.txt).

### Integration Points
- Origem: `prices.py` (`hist["Close"]`).
- Transporte: `DadosMercado` → `build.montar_empresa` → `CompanyData`.
- Consumo: `app.py` Tela 1, lendo a série de `c` e a banda de `a.vmin`/`a.vmax`.

</code_context>

<specifics>
## Specific Ideas

- "Margem de segurança visível": preço abaixo da banda = desconto; acima = prêmio — mas
  comunicado pela posição relativa, sem cores de área (D-04).
- Plotly escolhido explicitamente pelo roadmap/requisitos por zoom + hover interativos.

</specifics>

<deferred>
## Deferred Ideas

- Sombrear a área desconto/prêmio (verde/vermelho) e marcar o ponto do preço atual —
  considerado e **descartado para esta fase** (preferência por gráfico limpo, D-04). Pode
  voltar como refinamento visual futuro.
- Seletor de período além de 5a / gráficos nas Telas 2 e 3 — fora do escopo de v1.1.

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 3-Gráfico de Preço na aba Analisar*
*Context gathered: 2026-06-23*
