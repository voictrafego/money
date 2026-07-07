# Phase 16: Página Streamlit + Gráfico do Momento - Context

**Gathered:** 2026-06-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega o **4º menu** do app Streamlit — uma página read-only, separada e isolada
das 3 abas existentes — que renderiza o `SetupSwing` (Fase 15) como **thin renderer**: um
**gráfico candlestick "do momento"** com overlays liga/desliga e subpainéis RSI/MACD/ADX, o
**veredito de estudo** (Pontuação de confluência técnica + grade + decomposição peso-a-peso +
checklist + níveis), seletor de timeframe, botão Atualizar, selo de atraso e disclaimer
contextual (SWING-01, SWING-02, CHART-01).

**No escopo:** novo item de menu na sidebar; candlestick intraday/diário com overlays
toggleáveis + subpainéis; apresentação do score/decomposição/checklist/níveis lidos de
`SetupSwing`; input de ticker próprio da página; seletor de timeframe + botão Atualizar +
selo "~15min atraso" + timestamp da última barra; disclaimer e linguagem condicional;
verificação humana no navegador sem regressão nas 3 abas; goldens existentes verdes.

**Fora do escopo:** qualquer recálculo de método na view (`app.py` read-only — lógica vive na
engine das Fases 12–15); novos indicadores/padrões/score (já entregues); qualquer recomendação
de compra/venda (proibido por design — SWING-02); tocar na aba Analisar, no veredito
fundamentalista ou nos testes golden fundamentalistas.
</domain>

<decisions>
## Implementation Decisions

### Layout da página
- **D-01:** **Gráfico no topo full-width + veredito abaixo** (leitura top-down). O candlestick
  (com subpainéis RSI/MACD/ADX) ocupa a largura no topo; abaixo dele o card de veredito
  (grade+score, decomposição, checklist, tabela de níveis). Espelha o padrão da aba Analisar
  (gráfico respira) e mantém a ênfase visual no gráfico, não no número — coerente com o tom de
  estudo (evita "recomendação-first").

### Overlays default + controles
- **D-02:** Estado inicial dos overlays = **S/R + Médias Móveis + níveis do setup (entrada/stop/
  alvo + Fibonacci ancorado) LIGADOS**; **Bollinger, Donchian e padrões anotados DESLIGADOS**.
  Todos disponíveis via toggle. Foco no que monta o setup (Murphy: estrutura + tendência antes do
  gatilho); gráfico intraday limpo por padrão.
- **D-03:** Toggles num **expander "⚙️ Overlays" logo acima do gráfico**, com **estado técnico
  PRÓPRIO da página swing** (dicionário de estado isolado, ex. `swing_estado`/`tec_estado_swing`),
  **não** compartilhado com o `tec_estado` da aba Analisar. Preserva o isolamento read-only
  exigido por SWING-01 (mexer numa página não afeta a outra).

### Apresentação do veredito
- **D-04:** Score (0–100) + **grade em destaque** (Forte/Moderado/Fraco/Sem setup) e, abaixo, a
  decomposição peso-a-peso como **barra de contribuição por família** (Tendência/R:R/Padrões/
  Momentum/Volume → contribuição em pontos + rótulo neutro de origem). Explicabilidade visível
  na tela, não escondida em expander (atende D-02 da Fase 15: decomposição peso-a-peso visível).
  Lê direto de `SetupSwing.decomposicao` (`ContribFamilia.familia/sub_score/peso/contribuicao/detalhe`).
- **D-05:** Níveis (entrada-zona/stop/alvo/R:R) numa **tabela rotulada "Referências de estudo
  (não são ordens)"** + **checklist** de sinais como lista com **✓ (ativo) / ✗ (inativo)** e o
  detalhe neutro de cada sinal. **Disclaimer condicional inline** junto dos níveis. Evita
  `st.metric` para os níveis (risco de soar como alvo/ordem). Copy condicional é gate de aceite
  (SWING-02).

### Ticker / Timeframe / Atualizar
- **D-06:** **Input de ticker próprio** dentro do 4º menu (independente da aba Analisar).
  Reforça o isolamento (SWING-01) e permite analisar o técnico de um ticker diferente do
  fundamentalista.
- **D-07:** Seletor de timeframe expõe **Diário (default) + 1h + 30m + 5m** (os 4 frames de
  `frame_intraday`). Abre no **diário** — frame mais estável p/ swing (contexto antes do gatilho)
  e menos sujeito a "indisponível" por histórico curto. Intraday é best-effort com selo de atraso.
- **D-08:** **Linha de controle acima do gráfico** com: seletor de timeframe + botão **Atualizar**
  (invalida só `(ticker, timeframe)` via nonce — nunca `.clear()` global) + selo **"~15min atraso ·
  última barra HH:MM"** sempre visível. Reusa o wrapper `frame_intraday` (cache TTL 300s) da Fase 12.

### Claude's Discretion
- Anotação visual exata dos padrões no candlestick (neckline, rótulo "em formação/confirmado",
  alvo measured-move) e marcação da **barra viva em formação** → planner/research (CHART-01 exige,
  formato livre respeitando legibilidade).
- Tratamento de UI para "indisponível"/degradação graciosa (timeframe sem histórico p/ um
  indicador, série indisponível por Yahoo instável, `SetupSwing` "Sem setup") — espelhar o padrão
  de aviso da aba Analisar (`st.info`) sem quebrar a página.
- Decisão técnica de **reuso vs extensão do `grafico.py`**: a aba Analisar usa LINHA diária 5y;
  aqui é CANDLESTICK intraday. Avaliar reuso de `overlays_preco`/`subpaineis_ativos`/
  `layout_subplots`/`marcadores_eventos` vs novas funções/módulo p/ candlestick + zonas S/R
  (hrect) + Fibonacci + anotação de padrões → planner/research.
- Cores/tema dos elementos (candle up/down, zonas S/R, cores do checklist) → padrão Plotly/
  Streamlit existente.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisitos da fase
- `.planning/ROADMAP.md` §"Phase 16: Página Streamlit + Gráfico do Momento" — Goal + 5 Success
  Criteria (4º menu isolado, candlestick + overlays + subpainéis + barra viva, timeframe+Atualizar+
  selo de atraso, disclaimer condicional, goldens verdes + verificação humana no navegador).
- `.planning/REQUIREMENTS.md` §SWING-01 (menu separado read-only), §SWING-02 (disclaimer "exibe
  sinais, nunca recomenda" + linguagem condicional), §CHART-01 (candlestick + overlays liga/desliga
  + subpainéis RSI/MACD/ADX + reuso de `grafico.py` + barra viva marcada).

### Contrato consumido (read-only — a UI só LÊ campos)
- `src/analista/report/setup.py` — `SetupSwing` (score/grade/decomposicao/gate_rr_ok/rr_valor/
  conflito_mtf/entrada_zona/stop/alvo) e `ContribFamilia` (familia/sub_score/peso/contribuicao/
  detalhe). `montar_setup(sinais, cfg)` monta o setup; a página é thin renderer destes campos.
- `src/analista/core/indicators.py` — `calcular()` → `SinaisTecnicos` (séries de overlay: MMs,
  donchian_sup/inf, bb_sup/med/inf; subpainéis rsi/macd/macd_sinal/macd_hist/adx/pdi/ndi; pivôs
  pivot_high/low; níveis suportes/resistencias/entrada_zona/fib_retracoes/alvo/stop; padrões
  `Padroes.lista` (PadraoGrafico: tipo/estado/neckline/alvo/altura/pivos_envolvidos); checklist
  `Checklist.sinais` (Sinal: nome/ativo/detalhe)). Fonte de todos os overlays e marcadores.

### Reuso de renderização e cache
- `src/analista/report/grafico.py` — funções `overlays_preco`/`subpaineis_ativos`/`layout_subplots`/
  `marcadores_eventos`/`leitura_tecnica_disponivel` já usadas pela aba Analisar (LINHA diária). CHART-01
  pede "reuso de grafico.py" — avaliar reuso vs extensão p/ candlestick. (Confirmar caminho exato do
  módulo no scout do planner.)
- `app.py` §sidebar radio (linhas ~100–106: 3 menus atuais) — ponto de adição do 4º item de menu.
- `app.py` §`frame_intraday` (linha ~54: wrapper `@st.cache_data(ttl=300)` + nonce, sem `.clear()`
  global) — fetch/cache intraday targetado da Fase 12, reusado pelo botão Atualizar.
- `app.py` §chart da aba Analisar (linhas ~239–344: `make_subplots` + overlays + marcadores) —
  análogo direto do padrão de montagem de figura com overlays/subpainéis toggleáveis.

### Contexto de decisões anteriores
- `.planning/phases/15-montagem-do-setup-setupswing-score/15-CONTEXT.md` — decisões do score
  (pesos D-01, decomposição visível D-02, R:R gate D-03, grade 4 faixas D-05, copy "Pontuação de
  confluência técnica" D-06, conflito multi-TF penaliza D-07) que a UI desta fase apresenta.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frame_intraday(ticker, timeframe, nonce)` (`app.py` ~54): wrapper de cache targetado p/ o
  candlestick + botão Atualizar; já resolve o requisito de invalidação só de `(ticker, tf)`.
- `grafico.py` (`overlays_preco`/`subpaineis_ativos`/`layout_subplots`/`marcadores_eventos`/
  `leitura_tecnica_disponivel`): máquina de overlays/subpainéis já testada — base para os toggles
  e os subpainéis RSI/MACD/ADX (adaptar de linha p/ candlestick).
- Padrão de figura `make_subplots` com row 1 = preço + overlays e rows seguintes = osciladores
  (`app.py` ~263): molde direto p/ a figura desta página.
- `SetupSwing.decomposicao` (lista de `ContribFamilia`): pronta p/ a barra de contribuição por
  família (D-04) — zero recálculo na UI.

### Established Patterns
- `app.py` read-only / thin renderer: a UI só lê campos de dataclasses; toda lógica na engine.
  Replicar p/ a página swing (lê `SetupSwing` + `SinaisTecnicos`, nunca recalcula método).
- Degradação graciosa: a aba Analisar mostra `st.info` quando a série/técnico está indisponível
  sem quebrar — espelhar p/ timeframe sem histórico, Yahoo instável e `SetupSwing` "Sem setup".
- Estado técnico próprio (dicionário de toggles isolado) já existe como `tec_estado` na aba
  Analisar — criar um análogo independente p/ o swing (D-03).

### Integration Points
- Sidebar radio (`app.py` ~100): adicionar o 4º item de menu (ex.: "📐 Swing setup (técnico)").
- Bloco condicional novo no `app.py` p/ o modo swing, consumindo `montar_setup` + `calcular` +
  `frame_intraday`, isolado dos blocos das 3 abas.
</code_context>

<specifics>
## Specific Ideas

- O gráfico precisa ser legível como ferramenta de swing: candlestick com largura (D-01), níveis
  do setup e S/R visíveis de cara (D-02), e a barra viva/não-fechada marcada (CHART-01) — o
  usuário enfatizou nas fases anteriores que quer "ver por quê" (médias, Bollinger, as análises),
  não só um número.
- Tom "software educacional / exibe, nunca recomenda" é inegociável e gate de aceite (SWING-02):
  níveis sempre como "Referências de estudo (não são ordens)" (D-05), nada de `st.metric` que soe
  como alvo de preço, disclaimer condicional inline e contextual.
- Selo de atraso "~15min" + timestamp da última barra sempre visível (D-08) — honestidade sobre o
  best-effort intraday de custo-zero.
</specifics>

<deferred>
## Deferred Ideas

- Ponte read-only com o veredito fundamentalista do ticker (unir os dois produtos na mesma tela
  sem misturar veredito) → backlog (já listado no ROADMAP §Backlog).
- Padrões de continuação (triângulos, bandeiras) anotados no gráfico → backlog (diferidos por
  risco de falso positivo).
- Calibração fina de cores/tema e params curtos de indicadores por timeframe intraday → backlog.

None além desses — a discussão ficou dentro do escopo da fase.
</deferred>

---

*Phase: 16-p-gina-streamlit-gr-fico-do-momento*
*Context gathered: 2026-06-30 via /gsd-discuss-phase*
