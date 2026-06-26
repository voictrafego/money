# Requirements: Analista de Dividendos — v1.2

**Defined:** 2026-06-24
**Core Value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.
**Milestone goal:** Indicadores de tendência **consultivos** (timing de entrada + alerta de reverificação) na aba Analisar. Nunca alteram o veredito fundamentalista (DDM/múltiplos); o fundamento manda, o técnico só diz o *quando* e quando *re-olhar*.

## v1.2 Requirements

### Dados de mercado (DATA)

- [x] **DATA-01**: O app preserva o frame OHLC que o Yahoo já baixa (sem nova chamada de rede) para alimentar os indicadores
- [x] **DATA-02**: Indicadores são calculados sobre série ajustada por **splits** (não por dividendos), evitando cruzamentos/rompimentos espúrios; o eixo do gráfico permanece em Close nominal (decisão CR-01)
- [x] **DATA-03**: Cada indicador degrada graciosamente quando falta histórico mínimo (ex.: "MM200 indisponível — histórico < 200 pregões"), sem quebrar o gráfico (paridade com GRAF-03)

### Médias móveis e cruzamentos (TREND)

- [ ] **TREND-01**: User vê SMA 20/50/200 sobrepostas ao preço na aba Analisar
- [ ] **TREND-02**: User vê a posição do preço vs. MM200 rotulada (acima/abaixo) como filtro primário de tendência de longo prazo
- [ ] **TREND-03**: User vê a sinalização de golden cross / death cross (MM50 × MM200)
- [ ] **TREND-04**: User pode alternar para EMA além da SMA (toggle; padrão SMA)

### Canais de alta/baixa (CHAN)

- [ ] **CHAN-01**: User vê o canal de Donchian (20/55) com rompimentos rotulados (nova máxima / perda da mínima)
- [ ] **CHAN-02**: User vê as Bandas de Bollinger (20, 2σ) com toque/rompimento de banda rotulado como contexto
- [ ] **CHAN-03**: User vê a sinalização de Bollinger squeeze (bandas estreitas → baixa volatilidade)

### Força e direção da tendência (FORCE)

- [ ] **FORCE-01**: User vê o ADX(14) com leitura de força (sem tendência < 20 / forte > 25), calculado com suavização de Wilder
- [ ] **FORCE-02**: User vê a inclinação da regressão linear dos preços (direção + força da tendência)

### Momentum (MOM)

- [ ] **MOM-01**: User vê o RSI(14) com faixas 30/70 (sobrevendido/sobrecomprado), calculado com suavização de Wilder
- [ ] **MOM-02**: User vê o MACD(12/26/9) com o cruzamento da linha de sinal

### Timing consultivo (TIMING)

- [ ] **TIMING-01**: User vê um resumo de "timing de entrada" (composite consultivo: tendência de alta / sem tendência / atenção) em linguagem natural
- [ ] **TIMING-02**: O resumo cruza o veredito DDM (barato/caro) com o sinal técnico numa matriz fundamento×técnico, sem recalcular nem sobrescrever o fundamento
- [ ] **TIMING-03**: User recebe um alerta de "reveja os fundamentos" quando o preço perde a tendência (perda da MM200 / death cross / rompimento da mínima do Donchian), enquadrado como reverificação e nunca como ordem de venda
- [ ] **TIMING-04**: User pode escolher a base temporal dos alertas de tendência (diário ou semanal; padrão semanal); o gráfico visual permanece diário

### Apresentação e controles (UI)

- [ ] **UI-01**: Overlays (MMs / Donchian / Bollinger) desenhados no eixo de preço do gráfico existente
- [ ] **UI-02**: Osciladores (RSI / MACD / ADX) renderizados em subpainéis dinâmicos (make_subplots), criados só quando ativos
- [ ] **UI-03**: User pode ligar/desligar e selecionar quais indicadores exibir; estado mantido por sessão; o gráfico redesenha o subconjunto escolhido
- [ ] **UI-04**: Eventos (cruzamentos / rompimentos) marcados nas datas exatas no gráfico
- [ ] **UI-05**: Tooltips de glossário (ícone ?) para cada novo indicador, com definições acessíveis (paridade com o glossário do app)
- [ ] **UI-06**: O bloco técnico é apresentado como **subordinado** ao veredito fundamentalista (off por padrão, seção secundária, linguagem consultiva) — critério de aceite: leitor novo numa tela "cara + timing bullish" reconhece o fundamento como decisório

### Paridade de engine (CLI)

- [ ] **CLI-01**: A CLI imprime uma seção "Sinais técnicos (consultivos)" espelhando os mesmos sinais da engine (mesmo padrão CLI↔UI já validado)

### Travas de fidelidade (TEST)

> Continua a numeração de TEST-01/TEST-02 (coerência cross-modo, marco v1.0).

- [ ] **TEST-03**: Golden test trava RSI e ADX com suavização de **Wilder** (`ewm(alpha=1/length, adjust=False)`, seed SMA) contra fixtures de referência (cruzados com TradingView)
- [ ] **TEST-04**: No-repaint test garante que os sinais não usam dados futuros — `indicador(série[:k])[-1] == indicador(série)[k-1]`
- [ ] **TEST-05**: Test cobre a série split-adjusted num ticker com split conhecido (sem cruzamentos espúrios na data do split)
- [ ] **TEST-06**: Test trava as regras de desempate do composite de timing (casos-limite: ex.: "acima da MM200 mas ADX < 20")
- [x] **TEST-07**: Invariante — os 64 golden tests de valuation existentes permanecem verdes (nenhuma fórmula do livro alterada)

## Future Requirements (v2+)

### Indicadores

- **DMI-01**: +DI / −DI plotados junto do ADX (direção via DMI)
- **MOM-03**: Divergências RSI/MACD vs. preço

### Dados

- **VOL-01**: Volume / OBV como confirmação de tendência (exige dados extras; benefício marginal p/ buy-and-hold)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Sinais intraday / timeframes < diário | App é fundamentalista de longo prazo; dados gratuitos são diários; viraria day trade |
| Recomendação automática "COMPRE/VENDA AGORA" | Viola a regra travada: técnico é consultivo, nunca ordem; desautorizaria o veredito do livro |
| Venda automática ao romper a MM200 | O livro vende por **perda de fundamento**, não por preço; rompimento é gatilho de revisão |
| Score técnico único que sobrescreve barato/caro | Quebra o Core Value e a hierarquia fundamento > técnico; usar matriz de 2 eixos, não nota fundida |
| Stochastic / Williams %R / CCI / Ichimoku / Fibonacci / Elliott / candlestick patterns | Spam de day trade; fora das 4 famílias escolhidas |
| Backtest / otimização de parâmetros do indicador | Convida data-mining e a ilusão de que o técnico bate o fundamento; parâmetros canônicos fixos |
| Alertas push / e-mail / preço-gatilho | Exige backend e estado persistente; projeto é custo zero, sem backend |
| Sinais de venda a descoberto / short | Investidor de dividendos não opera vendido |
| Nova chamada de rede / `Adj Close` como base do gráfico | OHLC já está em memória (DATA-01); Adj Close divergiria da banda DDM (CR-01) |

## Traceability

Mapeamento requisito → fase. Preenchido na criação do roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 4 | Complete |
| DATA-02 | Phase 4 | Complete |
| DATA-03 | Phase 4 | Complete |
| TREND-01 | Phase 5 | Pending |
| TREND-02 | Phase 5 | Pending |
| TREND-03 | Phase 5 | Pending |
| TREND-04 | Phase 5 | Pending |
| CHAN-01 | Phase 5 | Pending |
| CHAN-02 | Phase 5 | Pending |
| CHAN-03 | Phase 5 | Pending |
| FORCE-01 | Phase 5 | Pending |
| FORCE-02 | Phase 5 | Pending |
| MOM-01 | Phase 5 | Pending |
| MOM-02 | Phase 5 | Pending |
| TIMING-01 | Phase 6 | Pending |
| TIMING-02 | Phase 6 | Pending |
| TIMING-03 | Phase 6 | Pending |
| TIMING-04 | Phase 6 | Pending |
| UI-01 | Phase 7 | Pending |
| UI-02 | Phase 7 | Pending |
| UI-03 | Phase 7 | Pending |
| UI-04 | Phase 7 | Pending |
| UI-05 | Phase 7 | Pending |
| UI-06 | Phase 7 | Pending |
| CLI-01 | Phase 6 | Pending |
| TEST-03 | Phase 5 | Pending |
| TEST-04 | Phase 5 | Pending |
| TEST-05 | Phase 5 | Pending |
| TEST-06 | Phase 6 | Pending |
| TEST-07 | Phase 4 | Complete |

**Coverage:**
- v1.2 requirements: 30 total
- Mapped to phases: 30 ✓
- Unmapped: 0

> Nota: TEST-07 (os 64 golden tests existentes continuam verdes) é um **invariante contínuo** — ancorado na Phase 4 mas verificado ao final de todas as fases do marco (4-7).

---
*Requirements defined: 2026-06-24*
*Last updated: 2026-06-24 — roadmap criado (Phases 4-7 mapeadas)*
