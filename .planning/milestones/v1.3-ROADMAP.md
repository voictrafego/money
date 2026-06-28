# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Consistência entre menus** — Phases 1-2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing) na aba Analisar** — Phases 4-8 (shipped 2026-06-27)
- 🚧 **v1.3 — Saneamento residual do valuation** — Phases 9-11 (in progress)

## Phases

<details>
<summary>✅ v1.0 — Consistência entre menus (Phases 1-2) — SHIPPED 2026-06-05</summary>

- [x] Phase 1: Engine de Consistência (5/5 plans) — completed 2026-06-05
- [x] Phase 2: Apresentação e Travas de Consistência (2/2 plans) — completed 2026-06-05

Detalhes completos: `.planning/milestones/v1.1-ROADMAP.md`

</details>

<details>
<summary>✅ v1.1 — Gráfico de preço na aba Analisar (Phase 3) — SHIPPED 2026-06-23</summary>

- [x] Phase 3: Gráfico de Preço na aba Analisar (2/2 plans) — completed 2026-06-23

Detalhes completos: `.planning/milestones/v1.1-ROADMAP.md`

</details>

<details>
<summary>✅ v1.2 — Indicadores de tendência (timing) na aba Analisar (Phases 4-8) — SHIPPED 2026-06-27</summary>

**Milestone Goal:** Adicionar indicadores técnicos consultivos (médias móveis + cruzamentos, canais, força/inclinação, momentum) à aba Analisar para auxiliar o *timing* de entrada e disparar um alerta de reverificação ao rompimento de tendência. Estritamente consultivo: o veredito fundamentalista (DDM/múltiplos) continua sendo a base e nunca é sobrescrito. Sem nova chamada de rede, sem nova dependência de TA, `app.py` read-only.

- [x] **Phase 4: Encanamento de dados + série correta** (2/2 plans) — completed 2026-06-26
- [x] **Phase 5: Motor de indicadores puro** (3/3 plans) — completed 2026-06-26
- [x] **Phase 6: Integração na engine + composite + alerta + CLI** (2/2 plans) — completed 2026-06-26
- [x] **Phase 8: Saneamento do motor DDM (caso VULC3)** (4/4 plans) — completed 2026-06-27 (executou antes da 7)
- [x] **Phase 7: UI — overlays, subpainéis, controles e enquadramento** (5/5 plans) — completed 2026-06-27 (150 testes verdes)

Detalhes das fases concluídas mantidos abaixo em "Phase Details".

</details>

### 🚧 v1.3 — Saneamento residual do valuation (In Progress)

**Milestone Goal:** Tornar os múltiplos de renda/crescimento (DY recorrente, payout sustentável, g histórico) fiéis e robustos **para qualquer ticker** — expurgando não-recorrentes por **regra geral**, nunca por ajuste de caso — e impedir que esses números contaminem Garimpo/Ranking. O caso VULC3 (lucro/dividendo extraordinário, payout >100%) é apenas o diagnóstico; a correção precisa valer para todo o universo e não regredir tickers normais (ITUB4/EGIE3/TAEE11/BBAS3). Estende a camada de normalização (`normalizacao.py`) já existente — não reescreve o DDM.

- [x] **Phase 9: Payout sustentável + DY recorrente (núcleo de metodologia)** - Define um payout sustentável geral que expurga anos não-recorrentes (>100%) e deriva o DY recorrente de lucro normalizado × payout sustentável, robusto para qualquer ticker (completed 2026-06-27)
- [x] **Phase 10: Crescimento robusto + de-poison do screening** - g histórico robusto (não endpoint-a-endpoint) e Garimpo/Ranking calculando crescimento sobre a série normalizada, não sobre lucro/dividendo CRU (completed 2026-06-27)
- [x] **Phase 11: Apresentação, hierarquia e trava multi-ticker** - DY recorrente em destaque e formatado como %, payout cru do último ano exibido, e trava de validação multi-ticker com rebaseline deliberado dos golden (completed 2026-06-28)

## Phase Details

### Phase 4: Encanamento de dados + série correta
**Goal**: O frame OHLC que o Yahoo já baixa deixa de ser descartado e fica disponível na engine, com uma série ajustada por splits pronta para os cálculos de indicador — sem novo comportamento visível e sem qualquer fórmula de valuation alterada.
**Depends on**: Phase 3 (v1.1 — padrão `serie_precos` é o blueprint)
**Requirements**: DATA-01, DATA-02, DATA-03, TEST-07
**Success Criteria** (what must be TRUE):
  1. O OHLCV de 5 anos já buscado em `coletar_mercado` é preservado em `DadosMercado.ohlc` e conduzido até `CompanyData.ohlc`, sem nenhuma nova chamada ao Yahoo (DATA-01).
  2. Existe uma série ajustada por **splits** (não por dividendos) disponível para os cálculos, enquanto a série/eixo do gráfico permanece em Close nominal (DATA-02, decisão CR-01); validada num ticker com split conhecido — sem cruzamentos espúrios na data do split.
  3. Quando o histórico é curto ou o `hist` vem vazio/None, o encanamento degrada graciosamente (campos `ohlc=None`) sem quebrar nada, espelhando o padrão GRAF-03 (DATA-03).
  4. Os 64 golden tests de valuation existentes continuam verdes após o encanamento (TEST-07) — invariante que se mantém ao longo de todas as fases do marco.
**Plans**: 2 plans
- [x] 04-01-PLAN.md — Encanamento ohlc/ohlc_ajustado (ingest→build→CompanyData) + função pura de split + testes offline
- [x] 04-02-PLAN.md — Validação multi-split ITSA4 + invariante TEST-07 (64 golden tests verdes)

### Phase 5: Motor de indicadores puro
**Goal**: Um módulo puro `core/indicators.py` calcula as 4 famílias de indicadores a partir do OHLC e devolve séries prontas para plotar + sinais discretos, com a matemática correta travada por golden tests antes de qualquer integração com a UI.
**Depends on**: Phase 4 (precisa do campo OHLC no dataclass; funções puras testáveis com frames sintéticos em paralelo)
**Requirements**: TREND-01, TREND-02, TREND-03, TREND-04, CHAN-01, CHAN-02, CHAN-03, FORCE-01, FORCE-02, MOM-01, MOM-02, TEST-03, TEST-04, TEST-05
**Success Criteria** (what must be TRUE):
  1. `indicators.calcular(ohlc, cfg)` devolve um `SinaisTecnicos` cobrindo as 4 famílias: SMA/EMA 20/50/200 + golden/death cross + posição preço×MM200 + toggle EMA (TREND-01..04); Donchian 20/55 + Bollinger 20/2σ + squeeze com rompimentos rotulados (CHAN-01..03); ADX(14) Wilder + inclinação de regressão (FORCE-01..02); RSI(14) Wilder + MACD 12/26/9 com cruzamento de sinal (MOM-01..02).
  2. RSI e ADX usam suavização de **Wilder** (`ewm(alpha=1/length, adjust=False)`, seed SMA) e batem com fixtures de referência cruzadas com TradingView (TEST-03).
  3. Nenhum sinal usa dados futuros — `indicador(série[:k])[-1] == indicador(série)[k-1]` para vários k (TEST-04 no-repaint).
  4. A série split-adjusted não gera cruzamentos/rompimentos espúrios num ticker com split conhecido (TEST-05).
  5. Zero novas dependências instaladas (só numpy/pandas/scipy já presentes); parâmetros canônicos vivem em config; os 64 golden tests seguem verdes (TEST-07).
**Plans**: 3 plans
- [x] 05-01-PLAN.md — Contrato SinaisTecnicos + config + Wilder helper + Tendência (SMA/EMA+cross) + Momentum (RSI Wilder 70.5328 + MACD); golden + no-repaint
- [x] 05-02-PLAN.md — Canais: Donchian 20/55 (shift1) + Bollinger 20/2σ (ddof=0) + squeeze percentil 126/20 (D-02); causal + no-repaint
- [x] 05-03-PLAN.md — Força: ADX(14) double-Wilder (1º válido idx 27) + regressão %/ano+R² (D-04) + montagem do calcular() + split ITSA4 (TEST-05) + checkpoint ADX×TradingView (TEST-03 aprovado, literais congelados)

### Phase 6: Integração na engine + composite + alerta + CLI
**Goal**: Os sinais técnicos passam a viver em `AnaliseAcao` via `analisar_acao`, com um resumo de timing composite que lê (sem recalcular) o veredito DDM numa matriz fundamento×técnico, um alerta de reverificação ao rompimento de tendência e a base temporal diária/semanal dos alertas — tudo espelhado na CLI.
**Depends on**: Phase 5 (engine só pode chamar `indicators.calcular` depois que o módulo existe e está travado)
**Requirements**: TIMING-01, TIMING-02, TIMING-03, TIMING-04, CLI-01, TEST-06
**Success Criteria** (what must be TRUE):
  1. `a.sinais` é populado em `analisar_acao` e expõe um resumo de "timing de entrada" composite consultivo em linguagem natural — tendência de alta / sem tendência / atenção (TIMING-01).
  2. O resumo cruza o veredito DDM (barato/caro) com o sinal técnico numa matriz fundamento×técnico, lendo `a.veredito`/`vmin`/`vmax` já calculados, sem recalcular nem sobrescrever o fundamento (TIMING-02).
  3. Quando o preço perde a tendência (perda da MM200 / death cross / rompimento da mínima do Donchian) é gerado um alerta de "reveja os fundamentos", enquadrado como reverificação e nunca como ordem de venda (TIMING-03).
  4. O usuário pode escolher a base temporal dos alertas (diário ou semanal; padrão semanal), com o gráfico visual permanecendo diário (TIMING-04).
  5. `relatorio_markdown` imprime uma seção "Sinais técnicos (consultivos)" espelhando os mesmos sinais da engine (CLI-01), e as regras de desempate do composite estão travadas por golden test em casos-limite — ex.: acima da MM200 mas ADX < 20 (TEST-06).
**Plans**: 2 plans
- [x] 06-01-PLAN.md — Engine: popular a.sinais + composite de timing (MM200/ADX) + base temporal semanal (W-FRI) + golden TEST-06
- [x] 06-02-PLAN.md — Matriz fundamento×técnico + alerta de reverificação + seção CLI consultiva + invariante TEST-07

### Phase 8: Saneamento do motor DDM (caso VULC3)
**Goal**: Corrigir a divergência estrutural do valuation fundamentalista exposta pelo caso VULC3 (intrínseco R$ 167–334 vs preço R$ 14, veredito "SUBAVALIADA" sobre uma divergência de modelo). Promovida do backlog 999.1. FIX-01 (trava `g_alto ≤ Ke`) e FIX-05 (veredito consome flags) já aplicados; restam FIX-02/03/04/06 — mudanças de metodologia com rebaselining deliberado dos golden tests.
**Depends on**: Phase 6 (a matriz fundamento×técnico lê `a.veredito`; saneamento melhora a qualidade do token líder). Executa antes da Phase 7.
**Requirements**: DDM-FIX-02, DDM-FIX-03, DDM-FIX-04, DDM-FIX-06 (FIX-01, FIX-05 ✅ feitos). Detalhes verificados linha-a-linha em `08-saneamento-do-motor-ddm/FINDINGS.md`.
**Success Criteria** (what must be TRUE):
  1. **FIX-04 (raiz):** o lucro consumido por ROE/CAGR/payout/DY passa por uma camada de normalização (expurgo de não-recorrentes) em vez do lucro CVM cru.
  2. **FIX-02:** o `g_alto` adotado é reconciliado com `g_fundamentos`/payout (payout ≥100% ⇒ g sustentável → 0), não mais um haircut arbitrário do CAGR.
  3. **FIX-03:** os inputs do CAPM (rf/ERP/EMBI) vêm de dado vivo (BCB/Selic) ou abordagem local, não dos literais de 2019; Ke resultante coerente com small cap BR.
  4. **FIX-06:** guardrails de apresentação — DY recorrente vs trailing, banda intrínseca = sensibilidade real (não 2 cenários binários), setor correto; VULC3 vira caso de regressão.
  5. Os golden tests são **rebaselinados deliberadamente** (valores corretos mudam) e voltam a ficar verdes com os novos números justificados — não "verde a qualquer custo".
**Plans**: 4 plans (sequenciais — cascata FIX-04 → FIX-02 → FIX-03 → FIX-06)
- [x] 08-01-PLAN.md — FIX-04: camada de normalização de lucro (raiz) + roteamento no valuation + rebaseline cascata ✅ 2026-06-26
- [x] 08-02-PLAN.md — FIX-02: reconciliação g_alto × g_fundamentos (payout≥100%⇒g=0) + golden ✅ 2026-06-26
- [x] 08-03-PLAN.md — FIX-03: CAPM 'local' com Selic ao vivo (BCB) + fallback gracioso + rebaseline de Ke ✅ 2026-06-26
- [x] 08-04-PLAN.md — FIX-06: banda = sensibilidade real + DY recorrente + setor + golden de regressão VULC3 ✅ 2026-06-27

### Phase 7: UI — overlays, subpainéis, controles e enquadramento
**Goal**: A aba Analisar passa a desenhar os overlays no eixo de preço e os osciladores em subpainéis dinâmicos, com controles para ligar/desligar e selecionar indicadores, marcadores de evento nas datas exatas, tooltips de glossário, e um enquadramento que mantém o veredito fundamentalista visivelmente decisório — tudo lendo `a.sinais` em modo read-only.
**Depends on**: Phase 6 (`app.py` lê `a.sinais`, que precisa existir em `AnaliseAcao`)
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06
**Success Criteria** (what must be TRUE):
  1. Overlays (MMs / Donchian / Bollinger) são desenhados no eixo de preço do gráfico existente (UI-01) e os osciladores (RSI / MACD / ADX) em subpainéis dinâmicos via `make_subplots`, criados só quando ativos (UI-02).
  2. O usuário liga/desliga e seleciona quais indicadores exibir; o estado é mantido por sessão (`st.session_state`) e o gráfico redesenha o subconjunto escolhido sem recomputar (UI-03).
  3. Eventos (cruzamentos / rompimentos) aparecem marcados nas datas exatas no gráfico (UI-04) e cada novo indicador tem tooltip de glossário (ícone ?) com definição acessível, em paridade com o glossário do app (UI-05).
  4. O bloco técnico é apresentado como subordinado ao veredito fundamentalista (off por padrão, seção secundária, linguagem consultiva); critério de aceite: um leitor novo numa tela "cara + timing bullish" reconhece o fundamento como decisório (UI-06).
**Plans**: 5 plans (3 waves)
- [x] 07-01-PLAN.md — Engine read-side: degradação holística (CR-01/IN-02) + close exposta em SinaisTecnicos + golden
- [x] 07-02-PLAN.md — Glossário dos indicadores técnicos (tooltips UI-05)
- [x] 07-03-PLAN.md — grafico.py: lógica pura de overlays/subpainéis/layout/marcadores (UI-01/02/03/04)
- [x] 07-04-PLAN.md — app.py: controles HÍBRIDOS (session_state) + enquadramento subordinado + degradação (UI-03/05/06)
- [x] 07-05-PLAN.md — app.py: make_subplots dinâmico + overlays + subpainéis + marcadores + fresh-reader checkpoint (UI-01/02/04/06)
**UI hint**: yes

### Phase 9: Payout sustentável + DY recorrente (núcleo de metodologia)
**Goal**: O payout-para-valuation e o DY recorrente passam a refletir a renda **sustentável** de qualquer ticker — expurgando anos não-recorrentes (payout >100% / distribuição extraordinária) por **regra geral**, não por ajuste de caso — em vez da média/mediana crua de 3 anos que satura no clamp de 100% num único ano atípico. É o núcleo de metodologia do marco: estende a primitiva de `normalizacao.py` para payout e provento; o DDM (Cap. 13-17) não é reescrito, só passa a consumir inputs saneados.
**Depends on**: Phase 8 (a camada `normalizacao.py` / `payout_valuation` / `roe_valuation` já existe; esta fase generaliza o expurgo de não-recorrentes sobre elas)
**Requirements**: DYR-01, PAY-01
**Success Criteria** (what must be TRUE):
  1. `payout_valuation()` deixa de ser a média crua de 3 anos clampada em 1.0: anos não-recorrentes (payout >100%) são expurgados por **regra geral data-driven** (sem constante por empresa), devolvendo um payout sustentável < 100% para VULC3 e estável para tickers de payout alto legítimo.
  2. O **DY recorrente** passa a derivar de **lucro normalizado × payout sustentável** (não a mediana crua de 3 anos de dividendos), permanecendo robusto mesmo quando o dividendo cru de toda a janela cai numa era de payout >100%.
  3. Com payout sustentável < 100%, `g_fundamentos` (`ROE_norm × (1 − payout_sustentável)`) deixa de ser zerado por saturação do clamp em tickers cujo payout cru passou de 100% num único ano — o crescimento por fundamentos volta a existir.
  4. Validado em VULC3 (caso-limite) **e** em ≥2 tickers normais (ex.: TAEE11/EGIE3, payout alto recorrente): o expurgo só atua sobre anos realmente extraordinários e não rebaixa o payout de quem distribui muito de forma sustentável.
  5. A fronteira per-ano é preservada — `payout(ano)` cru segue alimentando a tabela "Fundamentos (por ano)", o detector de armadilha (payout >100%) e a elegibilidade do screening (Cap. 8); só o agregado de valuation muda de base. Golden de valuation (TEST-07) verdes ou rebaselinados deliberadamente.
**Plans**: 3 plans (3 waves)
- [x] 09-01-PLAN.md — Primitiva pura `mediana_payout` (mediana sobre série completa, sem clamp) + goldens unitários (PAY-01)
- [x] 09-02-PLAN.md — `payout_valuation` mediano/sem-clamp + DY recorrente earnings-based + rebaseline deliberado dos goldens (PAY-01, DYR-01)
- [x] 09-03-PLAN.md — Trava de validação multi-ticker (offline + live VULC3/TAEE11/EGIE3/ITUB4/BBAS3) + registro do cross-effect Fase 10

### Phase 10: Crescimento robusto + de-poison do screening
**Goal**: O crescimento histórico exibido e o crescimento usado no screening (Garimpo BSD + Ranking por múltiplos) passam a vir de uma estimativa **robusta** sobre a série **normalizada** — não CAGR endpoint-a-endpoint nem CAGR sobre lucro/dividendo CRU — impedindo que um único ano extraordinário envenene o g exibido e o ranqueamento. GROW-02 gateia as telas: a metodologia (Fase 9) já aterrissou antes das telas que a consomem.
**Depends on**: Phase 9 (consome a base normalizada e o payout sustentável saneados; o screening de-poisoned não pode ranquear sobre um payout cru saturado)
**Requirements**: GROW-01, GROW-02
**Success Criteria** (what must be TRUE):
  1. O `g_historico` exibido usa uma estimativa **robusta** de crescimento (ex.: regressão log-linear / inclinação sobre a série normalizada), não mais o `cagr(lucros[0], lucros[-1])` endpoint-a-endpoint — um único ano de fundo/topo deixa de mandar no g.
  2. `indicadores_bsd` (Garimpo) calcula os fatores de crescimento de lucro, dividendos e fundamentos sobre a série **normalizada**, não `cagr_serie(c.lucro_liquido)`/`c.dividendos` crus — um ano extraordinário deixa de inflar/envenenar o BSD.
  3. O Ranking por múltiplos consome crescimento/ROE/payout normalizados (consistente com o Analisar), de modo que a mesma empresa não ranqueia barata por um g cru inflado num único ano.
  4. Validado: em VULC3 o ano extraordinário não infla o BSD nem o g exibido; em tickers normais (ITUB4/EGIE3/TAEE11/BBAS3) o ranqueamento e o g não regridem materialmente vs. o estado atual.
  5. A fronteira per-ano permanece intacta — `roe(ano)`/`payout(ano)`/lucro CRU seguem alimentando a elegibilidade per-ano (Cap. 8) e a tabela "Fundamentos (por ano)"; só os **agregados de crescimento** mudam de base.
**Plans**: 3 plans (3 waves)
- [x] 10-01-PLAN.md — GROW-01: estimador puro `crescimento_log_linear` (growth.py) + swap do g_historico (report.py)
- [x] 10-02-PLAN.md — GROW-02: BSD calcula crescimento via log-linear sobre série winsorizada (screening.py) + clamp do payout no fit da regressão de preço-alvo (comparables.py, D-06)
- [x] 10-03-PLAN.md — Validação multi-ticker (VULC3 + ITUB4/EGIE3/TAEE11/BBAS3) offline + live + rebaseline deliberado dos golden (suíte 171 verde SEM rebaseline; checkpoint live aprovado) ✅ 2026-06-27

### Phase 11: Apresentação, hierarquia e trava multi-ticker
**Goal**: A UI passa a destacar a renda sustentável (DY recorrente formatado como % e em destaque no header), rebaixar o DY trailing inflado a contexto rotulado, e exibir o payout **cru real** do último ano como número distinto do payout sustentável de valuation. O marco fecha com a trava de validação multi-ticker (ITUB4/EGIE3/TAEE11/BBAS3 + VULC3) e o rebaseline **deliberado e justificado** dos golden — extensão do invariante TEST-07.
**Depends on**: Phase 10 (a UI lê os campos saneados da engine em modo read-only; a trava valida a cascata de metodologia completa — payout sustentável + DY recorrente + crescimento robusto — ponta a ponta)
**Requirements**: DYR-02, PAY-02, HIER-01, TEST-08
**Success Criteria** (what must be TRUE):
  1. Na tabela de Múltiplos do app, **"DY rec." é formatado como %** (paridade com ML/ROE/DY/EY), nunca como decimal cru "0.20" — hoje cai no ramo `fmt_num` por não estar na lista de campos percentuais (DYR-02).
  2. A linha **"Payout (último ano)" exibe o payout cru real** do último ano (ex.: 124,7% em VULC3), distinto da linha "Payout p/ valuation" (sustentável) — hoje ambas leem `payout_valuation()` clampado e mostram o mesmo valor (PAY-02).
  3. O **header do Analisar dá destaque ao DY recorrente** (sustentável) como métrica principal e rebaixa/rotula o DY trailing como histórico/inflado, evitando induzir o usuário à armadilha de dividendos que o próprio app sinaliza (HIER-01).
  4. A mudança de metodologia é validada contra **ITUB4, EGIE3, TAEE11, BBAS3** além de VULC3: os golden de valuation seguem verdes **OU** são rebaselinados **deliberadamente com justificativa registrada**, comprovando que tickers sem distorção não regridem (TEST-08).
  5. `app.py` permanece read-only — o destaque/rotulagem/formatação é apresentação sobre `dy_recorrente`/`dy_atual`/`payout`/`payout_valuation` já expostos pela engine, sem recalcular método.
**Plans**: 3 plans (3 waves)
- [x] 11-01-PLAN.md — Helpers puros de apresentação (presentation.py: header_dy, linhas_multiplos, fmt_pct/num) + golden multi-ticker (TEST-08 layer a)
- [x] 11-02-PLAN.md — app.py religa header m3 (HIER-01) + tabela Múltiplos % e payout duplo (DYR-02/PAY-02) + varredura de rótulos no glossário
- [x] 11-03-PLAN.md — Checkpoint live dos 5 tickers no Streamlit (TEST-08 layer b)
**UI hint**: yes

## Progress

**Execution Order:**
Fases concluídas executaram em ordem numérica (4 → 5 → 6 → 8 → 7). v1.3 executa 9 → 10 → 11 (metodologia antes das telas que a consomem; UI + trava por último).

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Engine de Consistência | v1.0 | 5/5 | Complete | 2026-06-05 |
| 2. Apresentação e Travas de Consistência | v1.0 | 2/2 | Complete | 2026-06-05 |
| 3. Gráfico de Preço na aba Analisar | v1.1 | 2/2 | Complete | 2026-06-23 |
| 4. Encanamento de dados + série correta | v1.2 | 2/2 | Complete | 2026-06-26 |
| 5. Motor de indicadores puro | v1.2 | 3/3 | Complete | 2026-06-26 |
| 6. Integração na engine + composite + alerta + CLI | v1.2 | 2/2 | Complete | 2026-06-26 |
| 8. Saneamento do motor DDM (caso VULC3) | v1.2 | 4/4 | Complete | 2026-06-27 |
| 7. UI — overlays, subpainéis, controles e enquadramento | v1.2 | 5/5 | Complete | 2026-06-27 |
| 9. Payout sustentável + DY recorrente (núcleo de metodologia) | v1.3 | 3/3 | Complete   | 2026-06-27 |
| 10. Crescimento robusto + de-poison do screening | v1.3 | 3/3 | Complete    | 2026-06-27 |
| 11. Apresentação, hierarquia e trava multi-ticker | v1.3 | 2/3 | In Progress|  |

---
*Próximo passo: `/gsd-plan-phase 9` (núcleo de metodologia — payout sustentável + DY recorrente).*

---

## Backlog

_Vazio. O item 999.1 (Saneamento do motor DDM) foi promovido para a **Phase 8** em 2026-06-26._
