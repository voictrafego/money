# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 + auditoria/correção de dados (shipped 2026-06-28)
- 🚧 **v1.4 — Ferramenta de Swing Trade (setups de análise técnica)** — Phases 12–16
- 📋 **v2.0 — Comercialização (produto cobrável)** — planejada após v1.4 (fases renumeradas a partir da 17)

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

## Progress

**Execution Order:** Phases execute in numeric order: 12 → 13 → 14 → 15 → 16

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 12. Ingestão Intraday + Timeframe | v1.4 | 2/2 | Complete   | 2026-06-29 |
| 13. Pivôs, Contexto e Níveis | v1.4 | 3/4 | In Progress|  |
| 14. Padrões Gráficos + Checklist | v1.4 | 5/5 | Complete    | 2026-06-29 |
| 15. Montagem do Setup + Score | v1.4 | 1/1 | Complete    | 2026-06-30 |
| 16. Página Streamlit + Gráfico | v1.4 | 3/3 | Complete   | 2026-06-30 |

## 📋 v2.0 — Comercialização (produto cobrável) — planejada após v1.4

**Goal:** Transformar o protótipo de usuário único num produto que cobra — auth, trial 7d →
assinatura mensal (Asaas), gate de acesso e multiusuário — posicionado como software educacional
(sem recomendação). Arquitetura provável: gateway híbrido (Streamlit intacto atrás de um gate;
auth/billing/front no stack React+Vite+n8n+Asaas).

> Requisitos (AUTH/BILL/ACCT/LEGAL/OPS) e decisões preservados em `.planning/milestones/v2.0-REQUIREMENTS.md`.
> Fases serão renumeradas a partir da **17** quando o marco for (re)aberto via `/gsd-new-milestone`,
> após o fechamento da v1.4.

## Backlog

- Padrões de continuação (triângulos, bandeiras, retângulos) com alvo measured-move — diferidos (alto risco de falso positivo)
- Inversão de papel S/R anotada (resistência rompida vira suporte); Fibonacci de extensão como alvo alternativo
- Ponte read-only com o veredito fundamentalista do ticker (une os dois produtos sem misturar veredito)
- Trendlines automáticas (Dow) sobre pivôs; OBV / volume relativo avançado
- Calibração fina de `prominence`/`distance` por timeframe (ATR-scaling) e params curtos de indicadores por TF intraday
- Payout-alvo por setor configurável; sinalização de "ano extraordinário" na tabela de Fundamentos por ano; DDM-DOC-01 (docstring/teste de `t` em `ddm.py`)
