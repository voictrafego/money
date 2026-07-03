# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 + auditoria/correção de dados (shipped 2026-06-28)
- 🚧 **v1.4 — Ferramenta de Swing Trade (setups de análise técnica)** — Phases 12–16
- 🚧 **v1.5 — Modo Trading (UX de gráfico estilo TradingView)** — Phase 17
- 🚧 **v1.6 — Central de Acompanhamento (Home)** — Phase 18
- 🚧 **v1.7 — Lentes de valuation e contexto na aba Analisar** — Phase 19
- 📋 **v2.0 — Comercialização (produto cobrável)** — planejada após v1.7 (fases renumeradas quando reaberta)

> Detalhes completos das fases concluídas (v1.0–v1.3) no snapshot `.planning/milestones/v1.3-ROADMAP.md` e requisitos em `.planning/milestones/v1.3-REQUIREMENTS.md`.
> Requisitos e arquitetura da v2.0 preservados em `.planning/milestones/v2.0-REQUIREMENTS.md`.

## 🚧 v1.4 — Ferramenta de Swing Trade (setups de análise técnica)

**Milestone goal:** Adicionar um **4º menu/página novo e separado** ao app que monta *setups* de
análise técnica (método de John Murphy) para preparar **swing trades** de um ticker escolhido —
**exibe** contexto, níveis e sinais de forma explicável e determinística e **NUNCA recomenda**.
Não toca no método fundamentalista validado (v1.0–v1.3), na aba "Analisar", nos **191 testes golden**
nem na regra `app.py` read-only.

**Constraints inegociáveis (gates do marco):**
- `app.py` permanece **read-only** — toda lógica de setup vive na engine (`core/setups.py` + `report/setup.py`); a UI só lê campos de `SetupSwing`.
- Os **191 testes golden** seguem verdes ao final de **cada** fase; a engine fundamentalista e a aba Analisar ficam **intactas**.
- **Zero novas dependências de runtime** (tudo sobre `scipy.signal.find_peaks` + `pandas/numpy/yfinance/plotly/streamlit` já instalados).
- A fronteira **"exibe sinais, NUNCA recomenda"** é critério de aceite explícito das fases de score/UI (pitfall regulatório).
- **Custo-zero** mantido; intraday é **best-effort** com aviso de atraso (~15min).
- **Pivôs (swing highs/lows)** são o primitivo central que desbloqueia S/R, stop, Fibonacci, Dow e padrões.

## Phases

**Phase Numbering:**
- Numeração **continua** do milestone anterior (v1.3 terminou na Phase 11). v1.4 começa na **Phase 12**.
- Integer phases (12, 13…): trabalho planejado. Decimal phases (12.1…): inserções urgentes.
- Dependência rígida entre camadas: **ingest → core math → report/dataclass → UI**. A ordem não é negociável.

- [x] **Phase 12: Ingestão Intraday + Timeframe** — Camada de dados OHLCV multi-timeframe isolada do pipeline diário (DATA-01/02/03) (completed 2026-06-29)
- [x] **Phase 13: Pivôs, Contexto de Tendência e Níveis** — Pivôs no-repaint → Dow/multi-TF, S/R, stop, Fibonacci, R:R, volume (PIVOT/TREND/LEVEL/RR/VOL)
- [x] **Phase 14: Padrões Gráficos + Checklist de Sinais** — Duplo topo/fundo + OCO sobre pivôs e checklist liga/desliga (PAT-01, SIG-01) (completed 2026-06-29)
- [x] **Phase 15: Montagem do Setup (SetupSwing) + Score** — Dataclass read-only firewall + score ponderado explicável com R:R como gate (SCORE-01) (completed 2026-06-30)
- [x] **Phase 16: Página Streamlit + Gráfico do Momento** — 4º menu read-only, candlestick com overlays, botão Atualizar e disclaimer (SWING-01/02, CHART-01) (completed 2026-06-30)

### v1.5 — Modo Trading (UX de gráfico estilo TradingView)

- [x] **Phase 17: Modo Trading — Candlestick TradingView (Lightweight Charts)** — Vista "Modo Trading" na aba de swing com candlestick estilo TradingView (Lightweight Charts v5 via CDN) e overlays da engine portados (LWC-01/02/03) (completed 2026-07-01)

### v1.6 — Central de Acompanhamento (Home)

- [x] **Phase 18: Home — Watchlist + Notícias** — Página inicial (landing default) com watchlist de ~5 ações auto-atualizável (efeito alta/baixa, aviso de atraso ~15min) + feed de notícias do mercado (manchete/submanchete + link pra fonte), tudo custo-zero via RSS + Yahoo com cache compartilhado (HOME-01, WATCH-01/02, NEWS-01/02) (completed 2026-07-01)

## Phase Details

### Phase 12: Ingestão Intraday + Timeframe
**Goal**: Existe uma camada de ingestão que entrega OHLCV de um ticker em múltiplos timeframes (diário + 1h/30m/5m), isolada do pipeline diário e do cache fundamentalista, em base nominal correta e com refresh targetado.
**Depends on**: Nothing (fundação da v1.4; reusa `_ajustar_por_split` existente)
**Requirements**: DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. A engine retorna OHLCV de um ticker para diário, 1h, 30m e 5m via função parametrizada isolada — o fetch diário 5y da aba Analisar e o seu cache permanecem intactos.
  2. As séries intraday usam `auto_adjust=False` + split-adjust e timestamps normalizados para `America/Sao_Paulo` (independente do TZ da VPS em UTC); entrada/stop/alvo nascerão na mesma base nominal do gráfico.
  3. A última barra (viva/não fechada) é identificável e os cálculos podem operar sobre a barra fechada anterior; timeframes sem histórico suficiente para um indicador (ex.: MM200 em frame curto) reportam "indisponível" sem quebrar.
  4. Re-buscar os dados de um `(ticker, timeframe)` invalida só aquele cache (TTL curto 300s / nonce), nunca o `.clear()` global que apagaria o cache da aba Analisar.
  5. Os 191 testes golden seguem verdes e novos testes cobrem as edges (barra viva, matriz period×interval, timezone, barras ilíquidas).
**Plans**: 2 plans
- [x] 12-01-PLAN.md — Engine de ingestão intraday (`ingest/intraday.py`: `coletar_intraday` + `FrameOHLC` + `_PERIODO_POR_TF` + tz/barra-viva clock-free) + testes golden offline (DATA-01, DATA-02)
- [x] 12-02-PLAN.md — Cache targetado em `app.py` (`frame_intraday` wrapper `@st.cache_data(ttl=300)` + `_nonce_key`, sem `.clear()` global) (DATA-03)

### Phase 13: Pivôs, Contexto de Tendência e Níveis
**Goal**: A engine deriva, a partir de pivôs determinísticos e sem lookahead, o contexto de tendência (Dow + multi-TF) e todos os níveis geométricos de preço (S/R em zonas, entrada, stop, alvo Fibonacci), com R:R e confirmação por volume.
**Depends on**: Phase 12 (consome o contrato de frame OHLC multi-timeframe)
**Requirements**: PIVOT-01, TREND-01, TREND-02, LEVEL-01, LEVEL-02, LEVEL-03, LEVEL-04, RR-01, VOL-01
**Success Criteria** (what must be TRUE):
  1. A engine detecta pivôs (swing highs/lows) de forma determinística e no-repaint — o rótulo de um pivô em t é imutável em t+1 para barras fechadas.
  2. A engine rotula a tendência do ticker no diário (alta/baixa/lateral via sequência de Dow + MMs/ADX reusados) e o alinhamento semanal→diário (alinhado_alta / alinhado_baixa / conflito).
  3. A engine produz S/R como faixas/zonas (clusters de pivôs + Donchian), e os níveis de entrada (pullback / retração Fibonacci), stop (swing-low/high e/ou ATR×m) e alvo (retração 38,2/50/61,8% + extensão 161,8%) ancorados em dois pivôs documentados.
  4. A engine calcula a relação Risco:Retorno como razão ("1 : 2,5") e degrada para "indisponível" quando o risco é zero/indefinido (sem infinito).
  5. A família Volume (MM de volume + flag "rompimento com volume acima da média") é adicionada de forma aditiva ao contrato `SinaisTecnicos`; 191 goldens verdes + novos goldens da fase.
**Plans**: 4 plans
- [x] 13-01-PLAN.md — Pivôs fractal de Williams (no-repaint) + ATR exposto do TR do ADX (PIVOT-01)
- [x] 13-02-PLAN.md — Contexto de tendência: Dow diário + alinhamento semanal→diário (W-FRI) (TREND-01, TREND-02)
- [x] 13-03-PLAN.md — Zonas S/R (cluster k×ATR + Donchian) + família Volume (LEVEL-01, VOL-01)
- [x] 13-04-PLAN.md — Fibonacci entrada/alvo + stop conservador + R:R (LEVEL-02/03/04, RR-01)
**Research**: dispensado por decisão D-02 (CONTEXT) — defaults derivados do método; params em `config.yaml` (calibração empírica deferida).

### Phase 14: Padrões Gráficos + Checklist de Sinais
**Goal**: A engine detecta padrões gráficos (duplo topo/fundo + OCO) sobre pivôs com rótulo "em formação" vs "confirmado" e alvo measured-move, e compõe um checklist explícito de sinais disparados.
**Depends on**: Phase 13 (pivôs e níveis são insumo dos padrões e do checklist)
**Requirements**: PAT-01, SIG-01
**Success Criteria** (what must be TRUE):
  1. A engine detecta duplo topo, duplo fundo e OCO sobre pivôs, rotulando "em formação" vs "confirmado" (confirmação exige rompimento + volume) com alvo measured-move.
  2. Os detectores são causais/no-repaint: o rótulo de um padrão em t não muda em t+1 — teste de estabilidade no-repaint obrigatório e verde.
  3. Os limiares geométricos (tolerância de simetria, proporção mínima, nº de toques) vivem no `config.yaml` e foram validados multi-ticker para evitar enxurrada de falso positivo.
  4. A engine expõe um checklist de sinais (rompimento, cruzamento de MM, RSI/MACD, padrão, volume) com status liga/desliga, tornando explícito *por que* o setup existe.
  5. 191 goldens verdes + novos goldens da fase; triângulos/bandeiras ficam explicitamente **fora** do MVP da v1.4.
**Plans**: 5 plans
- [x] 14-01-PLAN.md — Contrato: bloco config `padroes:` + dataclasses PadraoGrafico/Padroes/Sinal/Checklist + flag bidirecional `volume_acima_mm` (PAT-01, SIG-01)
- [x] 14-02-PLAN.md — Detector duplo topo/fundo (neckline horizontal) + measured-move + no-repaint (PAT-01)
- [x] 14-03-PLAN.md — Detector OCO/OCO invertido (neckline inclinada por posição) + no-repaint (PAT-01)
- [x] 14-04-PLAN.md — Checklist de sinais (`_checklist`) + wiring em `calcular` + integração/degradação (SIG-01, PAT-01)
- [x] 14-05-PLAN.md — Calibração multi-ticker dos limiares (checkpoint humano anti-pareidolia) (PAT-01)
**Research**: **fortemente recomendado** (`/gsd-research-phase`) — heurísticos de OCO/duplo topo-fundo têm confiança LOW-MEDIUM; definir limiares geométricos e estratégia de fixtures antes de codar.

### Phase 15: Montagem do Setup (SetupSwing) + Score
**Goal**: Um dataclass read-only `SetupSwing` integra contexto + níveis + sinais + padrões num score ponderado explicável, com R:R como gate, em linguagem de estudo que exibe e nunca recomenda.
**Depends on**: Phases 13 e 14 (consome todos os componentes puros golden-testados)
**Requirements**: SCORE-01
**Success Criteria** (what must be TRUE):
  1. `report/setup.py` monta `SetupSwing` como firewall (nunca importa `report/report.py`), consumindo `indicators.calcular()` + `setups.*`, e degrada graciosamente sem levantar exceção para a UI.
  2. O score é ponderado e explicável (decomposição visível peso a peso, tendência domina) com grade qualitativa; o R:R atua como gate/modulador e o conflito multi-TF penaliza sem bloquear o setup.
  3. Os pesos e limiares do score são parametrizados no `config.yaml` (sem hardcode na montagem).
  4. Os guards de borda estão aplicados (R:R sem divisão por zero via `np.errstate`, stop/alvo coerentes, gate de liquidez) e toda a linguagem do veredito é condicional/de estudo — copy review é gate de aceite.
  5. Todos os goldens existentes verdes (271 na coleta atual após as Fases 12–14) + `test_setup_report.py`; a engine fundamentalista e a aba Analisar permanecem intactas.
**Plans**: 1 plan
- [x] 15-01-PLAN.md — bloco `score:` no config + engine `setup.py` (SetupSwing/montar_setup, gate R:R, firewall) + goldens `test_setup_report.py` (grades, gate, decomposição, anti-copy) (SCORE-01)

### Phase 16: Página Streamlit + Gráfico do Momento
**Goal**: Um 4º menu read-only renderiza o `SetupSwing` — gráfico candlestick "do momento" com overlays liga/desliga, seletor de timeframe, botão Atualizar, selo de atraso e disclaimer contextual.
**Depends on**: Phase 15 (a UI é thin renderer do dataclass; Phase 12 provê o fetch/cache)
**Requirements**: SWING-01, SWING-02, CHART-01
**Success Criteria** (what must be TRUE):
  1. Usuário acessa um 4º menu separado de swing setups que não altera a aba Analisar nem o veredito fundamentalista; `app.py` é thin renderer (lê campos de `SetupSwing`, nunca recalcula método).
  2. Usuário vê um candlestick interativo "do momento" com overlays liga/desliga (S/R, Fibonacci, padrões anotados, MMs/Donchian/Bollinger) e subpainéis RSI/MACD/ADX, com a barra viva em formação marcada.
  3. Usuário escolhe o timeframe e usa o botão Atualizar para re-buscar os dados; um selo "~15min atraso" + timestamp da última barra fica sempre visível.
  4. A página exibe disclaimer contextual "exibe sinais, nunca recomenda" e usa linguagem condicional para todos os níveis (entrada/stop/alvo como referências de estudo, jamais ordens).
  5. Todos os goldens existentes verdes (271+ após as Fases 12–15); verificação humana no navegador aprova o 4º menu sem regressão nas 3 abas existentes.
**Plans**: 3 plans
- [x] 16-01-PLAN.md — Wire da cadeia de engine (calcular→montar_setup, ohlc_nominal) + estado isolado `tec_estado_swing` + figura make_subplots candlestick + overlays MM + subpainéis RSI/MACD/ADX + barra viva (SWING-01, CHART-01)
- [x] 16-02-PLAN.md — Zonas S/R (add_hrect) + níveis do setup/Fibonacci + anotação de padrões + card de veredito (grade/score/decomposição/checklist/níveis) + disclaimer não-imperativo (CHART-01, SWING-02)
- [x] 16-03-PLAN.md — Goldens 283 verdes + verificação no navegador (via Claude-in-Chrome) do 4º menu sem regressão nas 3 abas (SWING-01, SWING-02, CHART-01)
**UI hint**: yes

### Phase 17: Modo Trading — Candlestick TradingView (Lightweight Charts)
**Goal**: A aba de swing ganha uma vista **"Modo Trading"** (toggle) que renderiza o candlestick puro via **TradingView Lightweight Charts v5** (carregada por `st.components.v1.html` + CDN unpkg pinado, **zero dependência Python nova**), entregando a UX que o Plotly não dá (scroll-zoom, pan, crosshair com rótulos nos eixos, **Y-autoscale**, linha de último preço); as **sobreposições da engine** (zona de entrada, stop, alvo, S/R, Fibonacci, padrões/pivôs) são portadas para `createPriceLine` / um helper `BandPrimitive` / `createSeriesMarkers`, lendo campos de `SetupSwing` **sem recálculo**. O **Plotly permanece** na análise densa; `grafico.py`, os 283+ goldens e a regra `app.py` read-only ficam intactos.
**Depends on**: Phase 16 (consome `SetupSwing` + fetch/cache intraday já existentes; reusa `sw.entrada_zona/stop/alvo`, `sinais.niveis`, `sinais.padroes`)
**Requirements**: LWC-01, LWC-02, LWC-03
**Success Criteria** (what must be TRUE):
  1. Usuário liga o **"Modo Trading"** na aba de swing e vê um candlestick estilo TradingView (scroll = zoom, arrastar = pan, crosshair com rótulos nos eixos, **Y reescala sozinho**, linha de último preço) sobre os **mesmos dados OHLC nominais** do setup; o gráfico Plotly continua disponível (default).
  2. As **sobreposições da engine** aparecem no chart LWC: zona de entrada como **banda** (`BandPrimitive`), stop/alvo/Fibonacci como **linhas rotuladas** (`createPriceLine`), S/R como bandas, padrões/pivôs como **markers** — todas lendo campos de `SetupSwing`, **sem recalcular** o método; copy neutra de estudo mantida.
  3. **Zero dependência Python nova**: Lightweight Charts **v5.x pinada por versão** via `st.components.v1.html` + CDN; `grafico.py` intacto; `app.py` permanece **thin renderer** (só lê a engine).
  4. O **range visível** do chart **persiste entre reruns** do Streamlit (`session_state` + `timeScale().setVisibleRange()`); disclaimer/linguagem de estudo preservados.
  5. Os **283+ testes golden** seguem verdes; verificação humana no navegador aprova o "Modo Trading" **sem regressão** nas abas existentes.
**Plans**: 3 plans
- [x] 17-01-PLAN.md — Toggle "Modo Trading" + `_render_lwc` (candlestick LWC v5 via CDN pinado/SRI) + persistência do range visível entre reruns (LWC-01, LWC-03)
- [x] 17-02-PLAN.md — Overlays da engine portados: BandPrimitive (zona/S-R) + createPriceLine (stop/alvo/Fib) + createSeriesMarkers (pivôs/padrões), read-only de SetupSwing (LWC-02)
- [x] 17-03-PLAN.md — Verificação: 283+ goldens verdes + grafico.py intacto + smoke no navegador (Claude-in-Chrome) sem regressão (LWC-01/02/03)
**UI hint**: yes
**Spikes**: `.planning/spikes/001-tv-feel-candlestick/` (✅ VALIDATED) + `.planning/spikes/002-overlays-da-engine/` (✅ VALIDATED) + `.planning/spikes/CONVENTIONS.md`

### Phase 18: Home — Watchlist + Notícias
**Goal**: O app ganha uma **página inicial (landing default)** que, ao abrir, mostra (1) uma **watchlist** de até ~5 tickers escolhidos pelo usuário — cotação **auto-atualizável** (~30–60s) com **efeito visual de alta/baixa no dia** e **aviso de atraso (~15min)** — e (2) um **feed de notícias** do mercado financeiro exibindo **só manchete + submanchete + fonte + horário**, onde o clique abre o **site original** da fonte. Tudo **custo-zero** (RSS + Yahoo/brapi grátis, **sem API paga, sem tempo-real tick-a-tick, sem IA de sentimento**) e com **cache compartilhado no servidor** para não multiplicar chamadas externas por usuário. Não toca nas engines fundamentalista/técnica nem nos **283 goldens**; os menus atuais (Analisar/Garimpar/Ranking/Swing) continuam acessíveis.
**Depends on**: Nada de bloqueante — reusa o fetch Yahoo já usado no swing (`ingest`) e o padrão `st.fragment` de auto-refresh da Fase 16/17. É camada de UI + um módulo novo, leve e read-only, de agregação (ex.: `core/home_feed.py`).
**Requirements**: HOME-01, WATCH-01, WATCH-02, NEWS-01, NEWS-02
**Success Criteria** (what must be TRUE):
  1. Ao abrir o app, a **Home é a primeira tela** (landing default); os 4 menus atuais continuam acessíveis no lateral e nenhum deles muda de comportamento.
  2. A **watchlist** parte de uma lista default (~5 tickers de dividendos), é **editável** pelo usuário e a escolha **persiste entre sessões** via `localStorage` (sem backend); cada item mostra preço e **variação do dia colorida (verde/vermelho)**.
  3. As cotações **atualizam sozinhas** (~30–60s) com **efeito visual** na mudança e **aviso claro de atraso (~15min)**; o fetch usa **cache compartilhado no servidor** (`st.cache_data` TTL), fazendo **1 chamada por ticker por intervalo** independentemente do nº de usuários (anti rate-limit do Yahoo), e degrada sem quebrar se um ticker falhar.
  4. O **feed de notícias** lista **manchete + submanchete + fonte + horário** de fontes com RSS aberto (**InfoMoney + Google News RSS de mercado BR + outras validadas**); clicar abre o **site original da fonte** em nova aba (**nunca** reproduz o texto completo — só manchete/trecho + link, zona segura de copyright).
  5. O feed **auto-atualiza** (~5–15min) com **cache compartilhado**, degrada sem quebrar se uma fonte cair, e **zero dependência paga**; os **283 goldens** seguem verdes e as engines existentes ficam intactas.
**Plans**: 4 plans
- [x] 18-01-PLAN.md — Scaffold da Home (landing default no radio) + core/home_feed.py (contrato never-raise) + deps novas (HOME-01)
- [x] 18-02-PLAN.md — Watchlist: cotacoes em lote + cache compartilhado + auto-refresh + persistencia localStorage + metric colorido (WATCH-01, WATCH-02)
- [x] 18-03-PLAN.md — Feed de noticias: feedparser InfoMoney + Google News, render seguro + link em nova aba, auto-refresh cacheado (NEWS-01, NEWS-02)
- [x] 18-04-PLAN.md — Verificacao: 283 goldens verdes + engines intactas + smoke no navegador (Home default sem regressao) (HOME-01, WATCH-01/02, NEWS-01/02)
**UI hint**: yes

## Progress

**Execution Order:** Phases execute in numeric order: 12 → 13 → 14 → 15 → 16

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 12. Ingestão Intraday + Timeframe | v1.4 | 2/2 | Complete   | 2026-06-29 |
| 13. Pivôs, Contexto e Níveis | v1.4 | 3/4 | In Progress|  |
| 14. Padrões Gráficos + Checklist | v1.4 | 5/5 | Complete    | 2026-06-29 |
| 15. Montagem do Setup + Score | v1.4 | 1/1 | Complete    | 2026-06-30 |
| 16. Página Streamlit + Gráfico | v1.4 | 3/3 | Complete   | 2026-06-30 |
| 17. Modo Trading (Lightweight Charts) | v1.5 | 3/3 | Complete    | 2026-07-01 |
| 18. Home — Watchlist + Notícias | v1.6 | 4/4 | Complete   | 2026-07-01 |
| 19. Lentes de valuation e contexto (Analisar) | v1.7 | 4/4 | Complete    | 2026-07-02 |

## 🚧 v1.7 — Lentes de valuation e contexto na aba Analisar

**Milestone goal:** Enriquecer a aba Analisar com lentes de valuation clássicas e contexto de mercado,
sem tocar na engine do método (v1.0–v1.3) nem no custo-zero (CVM + Yahoo + BCB) e mantendo os 296 testes
golden verdes. Motivado pelo estudo do concorrente Investidor10 (features de alto apelo que eles bloqueiam
no PRO e que nós já temos os dados para entregar de graça).

### Phase 19: Lentes de valuation e contexto na aba Analisar

**Goal:** Adicionar, read-only e sem recalcular o método: (1) Preço-Justo de Graham [√(22,5×LPA×VPA)] e
Preço-Teto de Bazin [DPA médio 5a ÷ DY-mínimo 6%] como cards ao lado do DDM; (2) "Quanto teria rendido"
R$ 1.000 com reinvestimento de dividendos (Adj Close 5a já coletado); (3) Comparador de pares do setor
(tabela P/L, P/VP, ROE, DY, Valor de Mercado) reusando comparables.py/multiples.py.
**Requirements**: VAL-01, VAL-02, RET-01, PEER-01
**Depends on:** Phase 18
**Plans:** 4/4 plans complete
- [x] 19-01-PLAN.md — Engine `core/lentes.py`: Graham, Bazin, "quanto teria rendido" e comparador de pares (funções puras) + goldens `test_lentes.py` (VAL-01, VAL-02, RET-01, PEER-01)
- [x] 19-02-PLAN.md — Expor Adj Close 5a já baixado (`serie_precos_ajustada` em prices/CompanyData/build) para o retorno total, sem rede nova (RET-01)
- [x] 19-03-PLAN.md — Render read-only na aba Analisar: cards Graham/Bazin, retorno 1a/5a, comparador de pares com alvo destacado (VAL-01, VAL-02, RET-01, PEER-01)
- [x] 19-04-PLAN.md — Verificação: 296+ goldens verdes, método intocado, zero dep nova + smoke no navegador (VAL-01, VAL-02, RET-01, PEER-01)

## 📋 v2.0 — Comercialização (produto cobrável) — planejada após v1.7

**Goal:** Transformar o protótipo de usuário único num produto que cobra — auth, trial 7d →
assinatura mensal (Asaas), gate de acesso e multiusuário — posicionado como software educacional
(sem recomendação). Arquitetura provável: gateway híbrido (Streamlit intacto atrás de um gate;
auth/billing/front no stack React+Vite+n8n+Asaas).

> Requisitos (AUTH/BILL/ACCT/LEGAL/OPS) e decisões preservados em `.planning/milestones/v2.0-REQUIREMENTS.md`.
> Fases serão numeradas em sequência (a partir da **20**) quando o marco for (re)aberto via `/gsd-new-milestone`,
> após o fechamento da v1.7.

## Backlog

- Padrões de continuação (triângulos, bandeiras, retângulos) com alvo measured-move — diferidos (alto risco de falso positivo)
- Inversão de papel S/R anotada (resistência rompida vira suporte); Fibonacci de extensão como alvo alternativo
- Ponte read-only com o veredito fundamentalista do ticker (une os dois produtos sem misturar veredito)
- Trendlines automáticas (Dow) sobre pivôs; OBV / volume relativo avançado
- Calibração fina de `prominence`/`distance` por timeframe (ATR-scaling) e params curtos de indicadores por TF intraday
- Payout-alvo por setor configurável; sinalização de "ano extraordinário" na tabela de Fundamentos por ano; DDM-DOC-01 (docstring/teste de `t` em `ddm.py`)

### Phase 20: Selo de Sustentabilidade do Dividendo cruzado com veredito de preço (DDM)

**Goal:** A aba Analisar (e, onde couber, Garimpar/Ranking) exibe um **Selo de Sustentabilidade do Dividendo** em 4 cores, derivado de fatores que a engine JÁ calcula (score BSD em `core/screening.py` — payout peso 30% + `cobertura_juros` + `crescimento_lucro_lp` + bandas `REFERENCIA_BSD`; payout sustentável/mediana; CDC; endividamento), **cruzado com o veredito de preço do DDM** (`report/report.py`: SUBAVALIADA/NO INTERVALO/SOBREAVALIADA/VERIFICAR) num quadrante: bom+barato=joia · bom+caro=espere · ruim+barato=value trap · ruim+caro=evitar. Diferencial vs AUVP (mostra só a cor de fundamento e ignora preço).
**Requirements**: SELO-01 (cálculo do selo na engine), SELO-02 (cruzamento selo×veredito), SELO-03 (exibição na UI)
**Depends on:** Nenhuma — reusa a engine existente (BSD + veredito DDM); independente da Phase 19.
**Constraints (gates do projeto):** `app.py` read-only (lógica na engine); os testes golden seguem verdes; **zero novas dependências de runtime**; custo-zero; fronteira **"EXIBE, NUNCA recomenda"**.
**Plans:** 1/2 plans executed

Plans:
- [x] 20-01-PLAN.md — Selo na engine: cor do BSD + cruzamento com veredito (quadrante) + wiring em analisar_acao (SELO-01/02)
- [ ] 20-02-PLAN.md — Exibição read-only: selo em destaque + quadrante na Analisar, coluna de selo em Garimpo e Ranking (SELO-03)

### Phase 21: Comparador multi-ativo lado a lado (múltiplos + selo por coluna)

**Goal:** Promover o embrião "Comparador de pares" (`core/lentes.py`: `metricas_par`/`tabela_pares` — P/L, P/VP, ROE, DY, Valor de Mercado) a um **comparador lado a lado de N tickers escolhidos pelo usuário**, exibindo os múltiplos e o **Selo da Phase 20 por coluna** para triagem rápida.
**Requirements**: COMP-01 (entrada de N tickers), COMP-02 (tabela comparativa de múltiplos), COMP-03 (selo por coluna)
**Depends on:** Phase 20 (usa o selo).
**Constraints (gates do projeto):** `app.py` read-only (lógica na engine); os testes golden seguem verdes; **zero novas dependências de runtime**; custo-zero; fronteira **"EXIBE, NUNCA recomenda"**.
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 21 to break down)
