# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Consistência entre menus** — Phases 1-2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- 🚧 **v1.2 — Indicadores de tendência (timing) na aba Analisar** — Phases 4-7 (in progress)

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

### 🚧 v1.2 — Indicadores de tendência (timing) na aba Analisar (In Progress)

**Milestone Goal:** Adicionar indicadores técnicos consultivos (médias móveis + cruzamentos, canais, força/inclinação, momentum) à aba Analisar para auxiliar o *timing* de entrada e disparar um alerta de reverificação ao rompimento de tendência. Estritamente consultivo: o veredito fundamentalista (DDM/múltiplos) continua sendo a base e nunca é sobrescrito. Sem nova chamada de rede, sem nova dependência de TA, `app.py` read-only, e os 64 testes golden continuam verdes.

- [x] **Phase 4: Encanamento de dados + série correta** - Preserva o frame OHLC já baixado e prepara a série split-adjusted para os indicadores, sem novo comportamento e sem quebrar os 64 golden tests
- [x] **Phase 5: Motor de indicadores puro** - `core/indicators.py` com as 4 famílias hand-rolled (SMA/EMA+cruzamentos, Donchian+Bollinger+squeeze, ADX+inclinação, RSI+MACD), travado por golden tests (Wilder, no-repaint, split)
- [x] **Phase 6: Integração na engine + composite + alerta + CLI** - Liga os sinais em `analisar_acao`, deriva o resumo de timing e a matriz fundamento×técnico, o alerta de reverificação e a paridade na CLI
- [x] **Phase 8: Saneamento do motor DDM (caso VULC3)** - Corrige a divergência estrutural do valuation fundamentalista (g×Ke, g×payout, CAPM ao vivo, normalização de lucro, guardrails) com rebaselining deliberado dos golden tests. Promovida do backlog 999.1; executa antes da Phase 7 — completed 2026-06-27
- [ ] **Phase 7: UI — overlays, subpainéis, controles e enquadramento** - Renderiza overlays e osciladores no gráfico com toggles, marcadores de evento, tooltips e enquadramento subordinado ao fundamento

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
- [ ] 07-03-PLAN.md — grafico.py: lógica pura de overlays/subpainéis/layout/marcadores (UI-01/02/03/04)
- [ ] 07-04-PLAN.md — app.py: controles HÍBRIDOS (session_state) + enquadramento subordinado + degradação (UI-03/05/06)
- [ ] 07-05-PLAN.md — app.py: make_subplots dinâmico + overlays + subpainéis + marcadores + fresh-reader checkpoint (UI-01/02/04/06)
**UI hint**: yes

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

## Progress

**Execution Order:**
Phases execute in numeric order: 4 → 5 → 6 → 8 → 7 (Phase 8 antes da 7 — saneamento do DDM antes da UI)

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Engine de Consistência | v1.0 | 5/5 | Complete | 2026-06-05 |
| 2. Apresentação e Travas de Consistência | v1.0 | 2/2 | Complete | 2026-06-05 |
| 3. Gráfico de Preço na aba Analisar | v1.1 | 2/2 | Complete | 2026-06-23 |
| 4. Encanamento de dados + série correta | v1.2 | 2/2 | Complete | 2026-06-26 |
| 5. Motor de indicadores puro | v1.2 | 3/3 | Complete | 2026-06-26 |
| 6. Integração na engine + composite + alerta + CLI | v1.2 | 2/2 | Complete | 2026-06-26 |
| 8. Saneamento do motor DDM (caso VULC3) | v1.2 | 4/4 | Complete | 2026-06-27 |
| 7. UI — overlays, subpainéis, controles e enquadramento | v1.2 | 0/TBD | Not started | - |

---
*Próximo passo: `/gsd-plan-phase 7` (UI — overlays/subpainéis, sobre o motor fundamentalista saneado). Phase 8 fechada (4/4).*

---

## Backlog

_Vazio. O item 999.1 (Saneamento do motor DDM) foi promovido para a **Phase 8** em 2026-06-26._
