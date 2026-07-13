# Project Research Summary

**Project:** Analista de Dividendos — v1.4 Swing Trade Setup Page
**Domain:** Análise técnica (método John Murphy) integrada a app fundamentalista Streamlit existente
**Researched:** 2026-06-29
**Confidence:** HIGH (stack confirmada no ambiente; arquitetura derivada de leitura direta do código; método Murphy é autoridade do domínio)

## Executive Summary

O milestone v1.4 é uma página nova e isolada que exibe setups de swing trade baseados no método de John Murphy para um único ticker B3, sem recomendar operações. A conclusão central da pesquisa é que **nenhuma dependência de runtime nova é necessária**: toda a capacidade do milestone se constrói sobre a stack já instalada (pandas 3.0.3, numpy 2.4.6, scipy 1.17.1, yfinance 1.4.1, plotly 6.8.0, streamlit 1.58.0) por meio de 6 módulos puros novos em `core/` e extensões aditivas (nunca destrutivas) nas camadas existentes. O `requirements.txt` permanece inalterado, e o mecanismo central de detecção de pivôs (swing highs/lows via `scipy.signal.find_peaks`) é a peça que habilita S/R, stop swing, Fibonacci, sequência de Dow e detecção de padrões — tudo derivado de um único novo primitivo.

A arquitetura do app já impõe uma separação de 4 camadas (ingest → core → report → UI read-only) que deve ser respeitada e estendida, nunca dobrada. A regra mais crítica é que `app.py` permanece read-only: toda lógica de setup (S/R, padrões, stop, alvo, R:R, score) vive na engine (`core/setups.py` + `report/setup.py`) e é consumida pela UI como um dataclass read-only `SetupSwing`, espelhando exatamente o contrato de `AnaliseAcao`. O veredito fundamentalista existente e os 191 testes golden ficam intocados — a fronteira de isolamento é `report/setup.py` que nunca importa `report/report.py`.

Os dois riscos mais custosos do milestone são (1) o lookahead bias na detecção de padrões e pivôs — código que "vê o futuro" e repinta sinais passados, que exige detectores causais e testes de estabilidade no-repaint — e (2) a fronteira legal/educacional "exibe, nunca recomenda": um score alto com entrada/stop/alvo exibidos é operacionalmente indistinguível de uma recomendação se a linguagem for imperativa. Ambos são gates de aceite do marco, não detalhes de UI. A pesquisa de pitfalls mapeou 14 armadilhas específicas com fases de prevenção, das quais 7 são críticas e devem ser verificadas por testes explícitos e review de copy antes do deploy.

---

## Key Findings

### Recommended Stack

Nenhuma biblioteca nova é necessária. A decisão é deliberada: libs de chart pattern de prateleira (PatternPy, TradingPatternScanner, chart_patterns) são wrappers finos de `scipy` mal mantidos, sem golden tests, de qualidade inferior ao `indicators.py` atual. Adotar qualquer uma delas seria um retrocesso. A alternativa correta é escrever módulos puros in-house (~400–600 linhas totais) sobre `scipy.signal.find_peaks`, seguindo o mesmo contrato de `indicators.py` (dataclasses agrupadas, sinais discretos em chaves estáveis, degradação para `"indisponivel"`, golden-testáveis).

**Core technologies (todas já instaladas):**
- **scipy 1.17.1** — `find_peaks(prominence=, distance=)` para detecção de pivôs: o núcleo que habilita tudo. `linregress` para trendlines (já em uso). Não substituir por `argrelextrema` (sem `prominence`, pega ruído).
- **pandas 3.0.3** — resample, rolling, clustering de pivôs. Copy-on-write é default no 3.0; manter `.copy(deep=True)` antes de mutações (padrão já presente).
- **numpy 2.4.6** — `polyfit` para trendlines, aritmética de Fibonacci, score/R:R.
- **yfinance 1.4.1** — `history(interval=, period=, auto_adjust=False)` para intraday. Limites hard: 5m/30m≈60d, 1h≈730d, 1d=sem limite. Sempre `auto_adjust=False` + `_ajustar_por_split` (split-only), igual ao diário.
- **plotly 6.8.0** — `go.Candlestick` + `add_hline`/`add_hrect`/`add_shape` para overlays. Já é o motor de `grafico.py` — reuso alto.
- **streamlit 1.58.0** — `st.cache_data(ttl=300)` com nonce como cache-key extra para refresh manual por ticker sem limpar o cache fundamentalista global.

**Módulos novos in-house (nenhuma dep nova):**
- `core/pivots.py` — swing highs/lows via `find_peaks`. Primitivo central.
- `core/suporte_resistencia.py` — clustering 1-D de pivôs em zonas de S/R com contagem de toques.
- `core/trendlines.py` — reta por >= 2 pivôs do mesmo lado; valida toques e inclinação.
- `core/padroes.py` — OCO, topo/fundo duplo, triângulos, bandeiras com regras geométricas conservadoras.
- `core/fibonacci.py` — retrações (0.236/0.382/0.5/0.618/0.786) e extensões (1.272/1.618) entre 2 pivôs.
- `core/setup.py` — agrega contexto (reusa `SinaisTecnicos`) + score + R:R → dataclass read-only.

### Expected Features

A fronteira inegociável: a página **EXIBE** níveis e sinais; **NUNCA** emite ordem. Toda linguagem é condicional e impessoal ("o método de Murphy posicionaria o stop em..."), nunca imperativa ("compre/entre"). O detector de **PIVOTS** é o gargalo de habilitação: S/R robusto, stop swing, Fibonacci, sequência de Dow e padrões gráficos dependem dele — construir pivots primeiro é mandatório.

**Must have (table stakes):**
- Contexto de tendência (Dow + MMs diário) — reuso direto de `posicao_mm200`, `cruzamento`, `forca_adx`
- Níveis de S/R exibidos como faixas no gráfico (zona, não ponto) — pivôs + Donchian
- Zona de entrada, stop técnico e alvo como níveis geométricos (não ordens) — pivôs + ATR
- Relação Risco:Retorno calculada — aritmética pura com guards contra divisão por zero
- Checklist de sinais liga/desliga com decomposição visível — transparência educacional
- Score explicável ponderado (decomposição por componente, não caixa-preta) + grade
- Gráfico candlestick interativo + botão Atualizar com TTL
- Timeframe diário como default; 1h/30m/5m best-effort
- Aviso permanente de atraso ~15min + timestamp da última barra
- RSI/MACD/ADX em subpainéis — reuso 100% de `indicators.py`
- Disclaimer contextual na própria página (não só na sidebar)

**Should have (differentiators):**
- Alinhamento multi-timeframe semanal→diário explícito (top-down de Murphy real) — modula o score
- Stop técnico em 3 sabores (swing-low / ATR / S/R) lado a lado — educa o conceito
- Fibonacci (retração para entrada, extensão para alvo) ancorado em pivôs documentados
- Detecção de padrões com rótulo "em formação" vs "confirmado" + alvo medido — honesto sobre incerteza
- Inversão de papel S/R anotada (resistência rompida vira suporte)
- Família Volume nova — confirmação de rompimento; ATR exposto (TR já existe interno a `adx_wilder`)

**Defer (v2+ / fora de escopo v1.4):**
- Scanner de universo ("quais ações têm setup hoje") — explicitamente fora do v1.4
- Alertas/push de gatilho — exige backend e implica recomendação
- Backtesting / win rate — sugere promessa de retorno
- Position sizing — aconselhamento financeiro explícito
- Scalping 1m / book de ofertas — day-trade puro, fora do custo-zero
- Auto-refresh em segundos — martela o Yahoo; o scope é refresh manual
- Ponte com o veredito fundamentalista do ticker — baixo custo mas P3

### Architecture Approach

A arquitetura do projeto já impõe uma separação de 5 camadas verificada por leitura do código. O v1.4 slots em cada camada com extensões aditivas, sem alterar assinaturas existentes. A firewall crítica é `report/setup.py` vs `report/report.py` — as duas nunca se importam mutuamente, garantindo que o veredito fundamentalista e os 191 golden tests ficam intocados. `SetupSwing` é um dataclass brand-new que a UI consome exatamente como consome `AnaliseAcao`: somente lendo campos, nunca recalculando.

**Major components (novos):**
1. `ingest/prices.coletar_ohlc(ticker, timeframe)` — fetch intraday isolado; reusa `_ajustar_por_split`; `coletar_mercado()` inalterado
2. `core/setups.py` — toda a matemática nova (pivôs, S/R, Fibonacci, padrões, stop, alvo, R:R, score); pura, sem I/O, golden-testável
3. `report/setup.py` — `SetupSwing` dataclass + `montar_setup()` orquestra `indicators.calcular()` + `setups.*`; degrada graciosamente; nunca levanta exceção na UI
4. `grafico.py` (extensões aditivas) — `candles_setup`, `niveis_horizontais`, `formas_padroes` retornam spec dataclasses; app.py converte em traces (mesmo contrato atual)
5. `app.py` (bloco novo, read-only) — 4º radio, seletor de timeframe, botão Atualizar com nonce de cache, render de `SetupSwing`, disclaimer contextual

**Padrão de refresh manual (nonce):** O botão Atualizar incrementa `session_state["setup_nonce"]` que é passado como arg extra ao `@st.cache_data` wrapper — força re-fetch só para `(ticker, timeframe, nonce)` sem limpar o cache fundamentalista global. TTL curto (300s) alinhado ao atraso do Yahoo.

### Critical Pitfalls

1. **Repaint pela barra intraday viva** — descartar (ou marcar como provisória) a última barra não-fechada antes de `indicators.calcular()`; sinais do checklist/score sempre sobre `iloc[-2]` (barra fechada). Fase 12 + 15 + 16.

2. **Lookahead bias na detecção de padrões e pivôs** — pivôs com janela centrada "veem o futuro". Toda detecção deve ser causal: pivô só válido quando barras à esquerda E à direita já estão fechadas. Escrever teste de estabilidade no-repaint. Fase 14 (e 13).

3. **Setup lido como ORDEM** — linguagem condicional e impessoal obrigatória; disclaimer contextual na própria página; score com legenda "qualidade técnica do desenho, não é sinal de compra"; revisão de copy como gate de aceite. Fase 15 + 16.

4. **Misturar nominal × split-adjusted × Adj Close no intraday** — sempre `auto_adjust=False` + `_ajustar_por_split`; entrada/stop/alvo/R:R na mesma base nominal do gráfico. Fase 12.

5. **Cache intraday contaminando pipeline diário** — função + cache separados com TTL curto (300s); intraday NÃO entra em `montar()`; botão Atualizar usa nonce, nunca `st.cache_data.clear()` global. Fase 12 + 16.

6. **Quebrar os 191 goldens / violar read-only de app.py** — mudanças apenas aditivas; toda lógica de setup na engine; rodar suite completa antes e depois de cada fase. Todas as fases.

7. **Over-fitting de padrões → enxurrada de falsos positivos** — limiares geométricos conservadores em `config.yaml`; exigir confirmação (rompimento + volume) antes de marcar padrão como "ativo"; validar multi-ticker. Fase 14.

---

## Implications for Roadmap

A pesquisa aponta claramente para 5 fases (12–16), com dependências rígidas entre camadas: ingest → core → report → spec → UI. Cada fase é golden-testável de forma independente antes que a próxima dependa dela. Essa ordem não é negociável: a UI não pode existir sem o dataclass; o dataclass não pode existir sem a math pura; a math pura não pode existir sem o ingest.

### Phase 12: Ingestão Intraday (camada de dados)

**Rationale:** Fundação de tudo. Sem dados intraday confiáveis e isolados do pipeline diário, as fases seguintes não têm o que consumir. É também onde 4 pitfalls críticos são prevenidos.
**Delivers:** `prices.coletar_ohlc(ticker, timeframe)` com matriz period×interval, `auto_adjust=False` + `_ajustar_por_split`, normalização `America/Sao_Paulo`, limpeza de barras ilíquidas/vivas, cache separado TTL 300s; `test_ingest_intraday.py` cobrindo todas as edges.
**Addresses:** Fetch multi-timeframe, aviso de limite de histórico, flag de barra viva.
**Avoids:** Pitfalls 1 (barra viva), 3 (base ajustada), 7 (contaminação de cache), 8 (period×interval), 9 (timezone), 10 (ilíquidos).

### Phase 13: Contexto de Tendência + Níveis (core math — parte 1)

**Rationale:** Pivôs são o gargalo de habilitação de tudo abaixo. S/R e contexto multi-timeframe dependem de pivôs. Sem pivôs, Fibonacci, stop swing e padrões não existem. Reusar `calcular()` para contexto de tendência é custo baixo e imediato.
**Delivers:** `core/pivots.py` (swing highs/lows causal, `find_peaks`), `core/suporte_resistencia.py` (clustering em zonas com contagem de toques), alinhamento multi-timeframe semanal→diário (resample W-FRI já presente), ATR exposto como série, família Volume básica no contrato `SinaisTecnicos`.
**Uses:** `scipy.signal.find_peaks`, `numpy` clustering, `indicators.calcular()` reusado.
**Avoids:** Pitfalls 2 (lookahead/causal), 9 (timezone no alinhamento), 12 (S/R determinístico), 13 (alinhamento multi-TF sobre barras fechadas).

### Phase 14: Padrões Gráficos + Fibonacci (core math — parte 2)

**Rationale:** É a feature mais cara e mais frágil. Isolar em fase própria permite validar os detectores com rigor antes de qualquer montagem de setup. A detecção de padrões tem baixo-médio nível de confiança nos heurísticos — exige pesquisa mais profunda.
**Delivers:** `core/padroes.py` (MVP: topo/fundo duplo + OCO; triângulos/bandeiras se prazo permitir); `core/fibonacci.py` (retrações + extensões com regra determinística documentada); testes de no-repaint (rótulo t imutável em t+1).
**Uses:** Pivôs da Fase 13; numpy puro para Fibonacci; limiares geométricos em `config.yaml`.
**Avoids:** Pitfalls 2 (lookahead), 11 (over-fitting), 12 (ancoragem arbitrária de Fibonacci).

### Phase 15: Montagem do Setup (report layer + SetupSwing)

**Rationale:** Com todos os componentes puros prontos e golden-testados, montar o dataclass integrador é seguro. É aqui que os guards de borda críticos são aplicados e a linguagem do veredito é definida — gate de aceite do marco.
**Delivers:** `report/setup.py` com `SetupSwing` dataclass + `montar_setup(ohlc, cfg, timeframe)` (degradação graciosa); zona de entrada + stop em 3 sabores + alvo; R:R com guards (`np.errstate`); score ponderado explicável; checklist de sinais; gate de liquidez; `test_setup_report.py`.
**Implements:** Firewall `SetupSwing` vs `AnaliseAcao`; read-only contract para UI.
**Avoids:** Pitfalls 4 (linguagem condicional, gate de copy review), 6 (read-only, aditividade), 14 (guards R:R/stop).

### Phase 16: Página Streamlit + Gráfico do Momento (UI layer)

**Rationale:** Última fase deliberadamente — a UI é fina de render porque tudo que precisa calcular já existe como dataclass. Nenhuma lógica de método entra em `app.py`.
**Delivers:** 4º radio em `app.py` + bloco de render read-only; `grafico_tecnico.py` com `candles_setup`, `niveis_horizontais`, `formas_padroes`; seletor de timeframe; botão Atualizar (nonce); selo "~15min atraso" + timestamp da última barra; disclaimer contextual (CVM Res. 19/20 + "score não é sinal de compra"); chaves de glossário; `test_grafico_setup.py`.
**Uses:** `SetupSwing` (Phase 15), spec builders (este phase), `st.cache_data(ttl=300, nonce)`.
**Avoids:** Pitfalls 1 (barra viva marcada), 4 (disclaimer + copy review), 5 (selo de atraso), 6 (read-only verificado), 7 (Atualizar não recoleta fundamentos).

### Phase Ordering Rationale

- **Ingest antes de core:** o contrato de frame (colunas, split-adjust, timezone, TTL) precisa existir antes do report layer.
- **Core em 2 fases (13 e 14):** pivôs + S/R + tendência são base amplamente documentada; padrões gráficos têm heurísticos mais incertos — separar permite fatiar o risco e possibilitar MVP reduzido de padrões.
- **Report antes de UI:** app.py deve ser literalmente um thin renderer; introduzir a UI sem o dataclass forçaria lógica na view, quebrando a regra mais importante do projeto.
- **Aditividade em todas as fases:** nenhuma mudança destrói assinatura existente — gate explícito por fase (191 goldens + novos goldens da fase).

### Research Flags

**Fases com padrões bem documentados (skip `/gsd-research-phase`):**
- **Phase 12:** Ingestão yfinance e cache Streamlit têm padrões estáveis e bem pesquisados. A tabela period×interval está documentada; implementar diretamente.
- **Phase 15:** Montagem de dataclass e guards de borda seguem padrões já estabelecidos em `indicators.py`. Padrão `np.errstate` é reuso direto.
- **Phase 16:** UI Streamlit read-only é a camada mais simples; todos os padrões (nonce, seletor, render de specs) foram documentados na pesquisa com exemplos de código prontos.

**Fases que podem precisar de `/gsd-research-phase`:**
- **Phase 13** (S/R clustering, alinhamento multi-TF): `find_peaks` é well-known, mas os valores de `prominence`/`distance` para ações B3 precisam de calibração empírica. Nível médio de incerteza.
- **Phase 14** (padrões gráficos): **SINALIZADA para pesquisa mais profunda.** Heurísticos de OCO/triângulo/bandeira têm confiança LOW-MEDIUM. Os limiares geométricos (tolerância de simetria, proporção mínima, nº de toques) precisam de definição empírica antes de codar. Candidato forte para `/gsd-research-phase` com foco em: definições precisas de cada padrão em Murphy, limiares publicados em implementações Python de referência e estratégia de test fixture.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versões confirmadas via `pip list` no ambiente; padrões de ingest/cache verificados contra docs oficiais Streamlit e issues yfinance |
| Features | HIGH | Método Murphy é autoridade do domínio; limites yfinance verificados em múltiplas fontes concordantes; features derivadas diretamente do código existente |
| Architecture | HIGH | Derivada de leitura direta do código (`app.py`, `indicators.py`, `prices.py`, `grafico.py`, `report.py`). Exceção: limites yfinance intraday são MEDIUM — verificar empiricamente na Fase 12 |
| Pitfalls | HIGH | 14 pitfalls com raízes no código existente e na documentação yfinance/Streamlit; pitfalls críticos têm testes de verificação propostos |

**Overall confidence:** HIGH

### Gaps to Address

- **Calibração de `prominence`/`distance` para pivôs B3:** parâmetros ideais para separar swing relevante de ruído não têm valor canônico. Tratar como parâmetros em `config.yaml` desde o início; calibrar empiricamente na Fase 13 com múltiplos tickers.
- **Limites exatos de período yfinance verificados ao vivo:** a tabela period×interval é HIGH em fontes de treinamento, mas o comportamento do Yahoo pode variar. A Fase 12 deve confirmar empiricamente antes de cravar os limites na camada de ingestão.
- **Heurísticos de detecção de padrões:** limiares geométricos para OCO/triângulos/bandeiras são genuinamente não-canônicos. A Fase 14 precisa definir esses limiares com base em testes multi-ticker antes de escrever código final — considerar `/gsd-research-phase`.
- **MVP de padrões:** a pesquisa recomenda iniciar só com duplo topo/fundo + OCO; a decisão final (se inclui triângulos/bandeiras no v1.4) deve ser tomada durante o planejamento da Fase 14 com base na complexidade observada.

---

## Sources

### Primary (HIGH confidence)

- Código existente — `src/analista/core/indicators.py`, `src/analista/ingest/prices.py`, `src/analista/report/report.py`, `src/analista/grafico.py`, `app.py`, `config.yaml`, `tests/` (golden suite, 191 testes). Lido diretamente.
- `.planning/PROJECT.md` — key decisions (v1.4 scope, custo-zero, intraday best-effort, "EXIBE, nunca recomenda", Fase 12–16)
- `pip list` local — versões instaladas confirmadas (pandas 3.0.3, numpy 2.4.6, scipy 1.17.1, yfinance 1.4.1, plotly 6.8.0, streamlit 1.58.0)
- Streamlit docs — `st.cache_data(ttl=)`, `.clear()` targeted, `st.rerun()` — API atual e estável
- John Murphy — *Análise Técnica dos Mercados Financeiros* — autoridade do método

### Secondary (MEDIUM confidence)

- yfinance intraday limits — AlgoTrading101 / yfinance issues (#1010, #2451) — limites 1m<=7d, demais intraday<=60d, 1h<=730d. Múltiplas fontes concordam; confirmar empiricamente na Fase 12.
- PatternPy / TradingPatternScanner / chart_patterns — avaliados e descartados (wrappers finos de scipy, sem releases/golden)
- Alpaca Markets — "Detecting chart patterns w/ Python" — confirma abordagem scipy pivot + regras geométricas como padrão da indústria

### Tertiary (LOW confidence)

- Heurísticos de limiares geométricos para padrões gráficos — sem valor canônico único; inferidos de implementações de referência. Requer definição empírica na Fase 14.

---
*Research completed: 2026-06-29*
*Ready for roadmap: yes*
