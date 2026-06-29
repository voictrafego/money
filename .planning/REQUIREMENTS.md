# Requirements: Analista de Dividendos — v1.4 Ferramenta de Swing Trade (análise técnica)

**Defined:** 2026-06-29
**Core Value:** A página de swing **EXIBE** contexto, níveis e sinais técnicos fiéis ao método de John Murphy, de forma **explicável e determinística** — e **NUNCA recomenda** (sem "compre/venda"). "Entrada/stop/alvo" são níveis geométricos de estudo, não ordens.
**Milestone goal:** Adicionar um **menu/página novo e separado** ao app que monta *setups* de análise técnica (Murphy) para preparar **swing trades** de um ticker escolhido, sem tocar no método fundamentalista validado (v1.0–v1.3), na aba "Analisar", nos 191 testes golden nem na regra `app.py` read-only.

**Arquitetura (decidida, da pesquisa):** extensão **aditiva** das 4 camadas existentes (ingest → core → report → UI read-only). **Zero novas dependências de runtime** — tudo sobre `scipy.signal.find_peaks` + `pandas/numpy/yfinance/plotly/streamlit` já instalados. Novos módulos puros (`core/setups.py`, novo dataclass `SetupSwing` em `report/`) **consomem** `core/indicators.py` sem alterá-lo. `app.py` ganha um 4º menu como camada fina read-only. **Pivôs (swing highs/lows)** são o primitivo central que desbloqueia S/R, stop, Fibonacci, Dow e padrões.

**Dados (custo-zero mantido):** diário/semanal robustos via Yahoo; intraday 1h/30m/5m **best-effort** (1h≈730d, 30m/5m≈60d) com **aviso de atraso (~15min)**. Tempo real puro (streaming) é pago → fora de escopo.

## v1.4 Requirements

### Página & Fronteira (SWING)

- [ ] **SWING-01**: Usuário acessa um **menu/página novo e separado** de swing setups, isolado — não altera a aba Analisar, o veredito fundamentalista nem recalcula método na view (lógica na engine, UI read-only).
- [ ] **SWING-02**: A página exibe **disclaimer "exibe sinais, nunca recomenda"** e usa linguagem condicional/de estudo para todos os níveis (entrada/stop/alvo como referências, jamais ordens).

### Dados & Timeframe (DATA)

- [x] **DATA-01**: Usuário obtém OHLCV **intraday** (1h/30m/5m) por timeframe via ingestão parametrizada **isolada do pipeline diário** (`auto_adjust=False` + split-adjust reusados; timezone America/Sao_Paulo; sem perturbar o fetch diário 5y nem o cache da aba Analisar).
- [x] **DATA-02**: Usuário escolhe o **timeframe** (diário padrão + 1h/30m/5m) e a página **avisa do atraso (~15min)** e do limite de histórico, degradando indicadores inviáveis (ex.: MM200 em frame curto) para **"indisponível"** sem quebrar.
- [x] **DATA-03**: Usuário clica **"Atualizar"** e a página re-busca os dados mais recentes do ticker/timeframe (cache TTL curto, invalidação **targetada** — não o `.clear()` global que apagaria o cache da aba Analisar).

### Contexto de Tendência (TREND)

- [x] **TREND-01**: A página exibe o **contexto de tendência** do ticker no diário (sequência de Dow via pivôs + MMs/ADX reusados de `indicators.py`), rotulado **alta / baixa / lateral**.
- [x] **TREND-02**: A página exibe o **alinhamento multi-timeframe** semanal→diário (alinhado_alta / alinhado_baixa / **conflito**), e o conflito **modula (penaliza) o score** sem bloquear o setup.

### Pivôs & Níveis de Preço (PIVOT / LEVEL)

- [x] **PIVOT-01**: A engine detecta **pivôs (swing highs/lows)** de forma determinística e **sem lookahead** (no-repaint: série truncada em t == em t+1 para barras fechadas).
- [x] **LEVEL-01**: A página exibe **suporte/resistência** (pivôs em cluster + Donchian) como **faixas/zonas** rotuladas ("Suporte ~R$ X" / "Resistência ~R$ Y"), nunca pontos exatos.
- [ ] **LEVEL-02**: A página exibe uma **zona de entrada** sugerida como nível (pullback / retração de Fibonacci), apresentada como referência de estudo.
- [ ] **LEVEL-03**: A página exibe o **stop técnico** ancorado em estrutura — **swing-low/high** e/ou **ATR×m** (ATR exposto a partir do TR já calculado no ADX) — como nível.
- [ ] **LEVEL-04**: A página exibe **alvo/projeção** via **Fibonacci** (retração 38,2/50/61,8% para entrada; extensão 161,8% para alvo) ancorado em dois pivôs.

### Risco, Volume & Sinais (RR / VOL / SIG)

- [ ] **RR-01**: A página calcula e exibe a **relação Risco:Retorno** de entrada/stop/alvo como razão ("1 : 2,5"), com **degradação para "indisponível"** quando o risco é zero/indefinido (sem infinito).
- [x] **VOL-01**: A engine adiciona a família **Volume** (média móvel de volume + flag "rompimento com volume acima da média") como confirmação, de forma aditiva ao contrato `SinaisTecnicos`.
- [ ] **SIG-01**: A página exibe um **checklist de sinais técnicos disparados** (rompimento, cruzamento de MM, RSI/MACD, padrão, volume) com status **liga/desliga**, tornando explícito *por que* o setup existe.

### Padrões & Score (PAT / SCORE)

- [ ] **PAT-01**: A engine detecta **duplo topo/fundo + OCO (ombro-cabeça-ombro)** sobre pivôs, com rótulo **"em formação" vs "confirmado"** (exige rompimento + volume) e **alvo measured-move** — escopo MVP honesto (triângulos/bandeiras ficam fora do v1.4).
- [ ] **SCORE-01**: A página exibe um **score ponderado explicável** (decomposição visível peso a peso: tendência domina) + **grade qualitativa**, com **R:R como gate/modulador**; pesos parametrizados no `config.yaml`.

### Gráfico (CHART)

- [ ] **CHART-01**: A página renderiza um **gráfico candlestick interativo "do momento"** com overlays liga/desliga (S/R, Fibonacci, padrões anotados, MMs/Donchian/Bollinger) e subpainéis RSI/MACD/ADX (reuso de `grafico.py`), com a barra viva em formação marcada.

## Future Requirements (pós-v1.4)

- Padrões gráficos de **continuação** (triângulos, bandeiras, retângulos) com alvo measured-move — diferidos por alto custo/risco de falso positivo
- **Inversão de papel S/R** anotada (resistência rompida vira suporte) e Fibonacci de extensão como alvo alternativo
- **Ponte read-only com o veredito fundamentalista** do ticker ("este ticker no Garimpo está caro/barato?") — une os dois produtos sem misturar veredito
- **Trendlines automáticas** (Dow) desenhadas sobre pivôs; **OBV / volume relativo** avançado
- Calibração fina de `prominence`/`distance` dos pivôs por timeframe (ATR-scaling) e params curtos de indicadores por TF intraday

## Out of Scope (v1.4 — exclusões explícitas)

- **Botão/sinal "COMPRAR" ou "VENDER"** — viraria recomendação; quebra o posicionamento educacional e cria risco legal
- **Streaming / cotação em tempo real** — feed B3 real-time é pago; quebra o custo-zero (intraday é best-effort + aviso de atraso)
- **Alertas/push de gatilho** ("avise quando romper") — exige backend/scheduler inexistente e empurra para operar
- **Scanner de universo** ("quais ações têm setup hoje") — explicitamente um ticker por vez no v1.4
- **Backtest / "win rate" do setup** — sugere promessa de retorno (recomendação) e induz overfitting
- **Position sizing / "quanto investir" / alavancagem** — é aconselhamento financeiro explícito (só R:R como razão)
- **Scalping 1m / book de ofertas (DOM)** — empurra para day-trade; 1m só 7 dias e atrasado
- **Auto-refresh em segundos** — martela o Yahoo (rate-limit) e simula streaming; refresh é **manual** + cache TTL
- **Reescrever a engine fundamentalista, a aba Analisar ou os 191 testes golden** — análise técnica é um produto **separado** e aditivo

## Traceability

<!-- REQ-ID → Fase (preenchido pelo roadmapper 2026-06-29). Cobertura: 18/18. -->

| REQ-ID | Fase | Status |
|--------|------|--------|
| DATA-01 | Phase 12 | Complete |
| DATA-02 | Phase 12 | Complete |
| DATA-03 | Phase 12 | Complete |
| PIVOT-01 | Phase 13 | Complete |
| TREND-01 | Phase 13 | Complete |
| TREND-02 | Phase 13 | Complete |
| LEVEL-01 | Phase 13 | Complete |
| LEVEL-02 | Phase 13 | Pending |
| LEVEL-03 | Phase 13 | Pending |
| LEVEL-04 | Phase 13 | Pending |
| RR-01 | Phase 13 | Pending |
| VOL-01 | Phase 13 | Complete |
| PAT-01 | Phase 14 | Pending |
| SIG-01 | Phase 14 | Pending |
| SCORE-01 | Phase 15 | Pending |
| SWING-01 | Phase 16 | Pending |
| SWING-02 | Phase 16 | Pending |
| CHART-01 | Phase 16 | Pending |
