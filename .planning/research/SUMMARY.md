# Project Research Summary

**Project:** Analista de Dividendos — indicadores técnicos consultivos (marco v1.2)
**Domain:** Indicadores de tendência/momentum sobrepostos a um app fundamentalista de dividendos B3 (Python + Streamlit + yfinance)
**Researched:** 2026-06-24
**Confidence:** HIGH

## Executive Summary

O marco v1.2 adiciona 7 famílias de indicadores técnicos consultivos (SMA/EMA, crossovers, Donchian, Bollinger, ADX + inclinação, RSI, MACD) à aba "Analisar" de um app que já implementa o método fundamentalista do livro *O Investidor em Ações de Dividendos*. O ponto central da pesquisa é que o projeto roda numpy 2.4.6 + pandas 3.0.3 — versões bleeding edge que tornam as bibliotecas de TA populares (`ta`, `pandas-ta`, `finta`, `TA-Lib`) incompatíveis ou demasiado pesadas. A recomendação unânime é: **calcular todos os indicadores à mão em pandas/numpy/scipy, sem nenhuma nova dependência**, usando o stack já instalado. Os 7 indicadores são fórmulas de poucas linhas; o custo de manutenção do hand-roll é menor que o risco de versão de qualquer biblioteca externa neste ambiente.

A arquitetura correta espelha exatamente o padrão que o v1.1 já usou para `serie_precos`: criar um campo `ohlc` no dataclass `DadosMercado` preservando o frame OHLCV que o yfinance já busca (sem nova chamada de rede), criar um módulo puro `core/indicators.py` que devolve um dataclass `SinaisTecnicos` com séries prontas para plotar + sinais discretos em Python puro, e calcular tudo dentro de `report.analisar_acao` — o único ponto que CLI e UI já compartilham. O `app.py` permanece read-only: lê `a.sinais`, nunca recalcula. Caching é gratuito porque tudo roda dentro do caminho `montar()` → `analisar_acao()` já cacheado.

Os riscos principais são dois erros silenciosos de cálculo e um erro de produto. No cálculo: (1) RSI e ADX exigem suavização de Wilder (`ewm(alpha=1/length, adjust=False)`) — não a EMA padrão (`span`) — e a diferença produz valores materialmente errados; (2) indicadores calculados sobre a série nominal sofrem distorção em splits/grupamentos, gerando cruzamentos e rompimentos espúrios. No produto: indicadores técnicos apresentados de forma proeminente ao lado do veredito DDM/múltiplos podem ser lidos pelo usuário como substituindo o fundamento — o que contradiz o Core Value do app. Todos os três riscos têm prevenção conhecida e devem ser travados com golden tests e critérios de aceite explícitos antes da entrega.

---

## Resolução de Conflito: Wilder vs. dependência de biblioteca

STACK.md e PITFALLS.md divergem em um ponto:

- **STACK.md** conclui que `ta`, `pandas-ta` e `finta` são incompatíveis com numpy 2.4.6 / pandas 3.0.3 do projeto, e que `TA-Lib` viola o princípio custo-zero. Recomenda hand-roll total — zero novas dependências.
- **PITFALLS.md** alerta que RSI e ADX DEVEM usar suavização de Wilder (não a EMA padrão), e sugeriu `ta`/`pandas-ta` como forma de acertar o cálculo.

**Resolução adotada (definitiva):** hand-roll total sem nova dependência (conforme STACK), mas implementar explicitamente a suavização de Wilder via `ewm(alpha=1/length, adjust=False)` com seed de SMA nos primeiros `length` valores — e **travar a correção com golden tests dedicados** que comparam o resultado contra fixtures calculados manualmente ou validados no TradingView. Não adicionar `ta`, `pandas-ta` ou qualquer biblioteca de TA. O roadmapper NÃO deve incluir fase de instalação de dependência de TA.

---

## Key Findings

### Recommended Stack

O stack já instalado cobre 100% das necessidades: pandas 3.0.3 (`rolling`/`ewm` para SMA/EMA/Bollinger/RSI/MACD/ADX), numpy 2.4.6 (`polyfit`/`maximum`/`where` para slope/True Range/sinais), scipy 1.17.1 (`linregress` para slope + R²), plotly 6.8.0 (`make_subplots` para painéis de osciladores) e streamlit 1.58.0 (toggles/multiselect). O yfinance já busca o frame OHLCV completo em `prices.py` — só `Close` é preservado hoje; `Open/High/Low` precisam ser mantidos para ADX e Donchian.

**Core technologies (todas já presentes, zero a instalar):**
- **pandas 3.0.3** — `rolling(n).mean()` / `ewm(alpha=1/n, adjust=False)` cobrem SMA, EMA, Bollinger, RSI, MACD, ADX; espinha dorsal de todos os cálculos
- **numpy 2.4.6** — `polyfit`/`maximum`/`where` para regressão linear, True Range e sinais; motivo central para não usar libs de TA congeladas no numpy 1.x
- **scipy 1.17.1** — `linregress` para slope + R² da regressão (já no `requirements.txt`)
- **plotly 6.8.0** — `make_subplots(rows=n, shared_xaxes=True)` para painéis separados de RSI/MACD/ADX
- **streamlit 1.58.0** — `st.multiselect` / `st.toggle` / `st.checkbox` para controles ligar/desligar
- **yfinance** (já em uso) — `tk.history(period="5y", auto_adjust=False)` já devolve OHLCV; preservar o frame, não refazer fetch

**O que NÃO usar (incompatível ou viola custo-zero):**
- `ta` 0.11.0 — congelado nov/2023, pré-numpy-2/pandas-3; `np.NaN` removido no numpy 2
- `pandas-ta` 0.3.14b — pede `numpy<2`; conflita com 2.4.6
- `pandas-ta` 0.4.71b0 — beta, exige Python ≥3.12 + numba
- `TA-Lib` — wrapper de C; viola custo-zero/instalação-simples
- `finta` — abandonado, sem suporte a numpy 2 / pandas 3

### Expected Features

Todos os indicadores são **consultivos**: respondem *quando* entrar numa ação já barata pelo DDM/múltiplos, e sinalizam *quando rever os fundamentos* — nunca substituem o veredito fundamentalista.

**Must have (table stakes — v1.2):**
- SMA/EMA 20/50/200 sobrepostas ao preço + posição preço × MM200 (filtro primário de tendência de longo prazo)
- Golden cross / death cross (MM50 × MM200) — evento de virada de longo prazo essencial
- RSI(14) com faixas 30/70 — oscilador de momentum mais reconhecido pelo público
- MACD(12/26/9) com cruzamento de sinal — timing de momentum esperado pelo público
- ADX(14) + inclinação de regressão linear — responde "SE há tendência" (evita erro nº1: aplicar timing em mercado lateral)
- Donchian 20/55 + Bollinger 20/2σ — canais com rompimentos rotulados
- Controles ligar/desligar por família de indicadores (decisão JÁ travada)
- **Resumo de timing de entrada (composite consultivo)** — coração do valor do marco
- **Alerta de reverificação** ao romper tendência → "reveja os fundamentos" (nunca "venda")
- Tooltips de glossário e degradação graciosa por indicador (paridade com v1.1)

**Should have (diferenciadores):**
- Composite que cruza veredito DDM com sinal técnico (matriz barato/caro × em tendência/perdeu tendência)
- ADX como filtro de whipsaw: crossovers só sinalizados quando ADX > 20-25
- Timeframe semanal como padrão para alertas de crossover/MM200 (menos whipsaw para buy-and-hold)
- Marcadores de eventos (cross/rompimentos) plotados nas datas exatas no gráfico

**Defer (v2+):**
- +DI/−DI plotados junto do ADX
- Exportar resumo de timing no relatório/CLI
- Bollinger squeeze como contexto extra de volatilidade
- Alertas push/e-mail/preço-gatilho (exige backend — violaria custo-zero)

**Anti-features (proibidas para este público):**
- Sinais intraday / timeframes < diário
- "COMPRE/VENDA AGORA" — recomendação automática
- Score técnico único que rivaliza com o veredito fundamentalista
- Backtest/otimização de parâmetros (data-mining, fora de escopo)
- Stochastic, Williams %R, CCI, Ichimoku, Fibonacci, Elliott (spam de day trade)

### Architecture Approach

A arquitetura segue exatamente o padrão já validado no v1.1 para `serie_precos`: thread o frame OHLC pelos dataclasses existentes (`DadosMercado.ohlc` → `CompanyData.ohlc`), criar módulo puro `core/indicators.py` que recebe OHLC e devolve `SinaisTecnicos`, calcular dentro de `report.analisar_acao` (ponto único compartilhado por CLI e UI). O `app.py` permanece read-only. Caching é gratuito.

**Componentes e responsabilidades:**

1. **`ingest/prices.py`** — MODIFICAR: preservar `hist[["Open","High","Low","Close","Volume"]]` em `dm.ohlc`; adicionar série split-adjusted para indicadores; manter `dm.serie_precos` intocado
2. **`ingest/build.py`** — MODIFICAR: copiar `dm.ohlc` → `c.ohlc` (uma linha, espelha `c.serie_precos`)
3. **`core/fundamentals.py`** — MODIFICAR: `ohlc: Optional["pd.DataFrame"] = None` em `CompanyData` (forward-ref, sem import pandas no topo)
4. **`core/indicators.py`** — NOVO: funções puras `OHLC → SinaisTecnicos`; sem I/O, sem Streamlit; thresholds via `cfg`
5. **`report/report.py`** — MODIFICAR: dataclass `SinaisTecnicos` + `a.sinais = indicators.calcular(c.ohlc, cfg)`; valuation intocado
6. **`app.py`** — MODIFICAR: toggles + traces Plotly de `a.sinais.series`; leitura pura, nunca recalcula
7. **`cli.py`** — MODIFICAR: seção "Sinais técnicos (consultivos)" em `relatorio_markdown`
8. **`tests/test_indicators.py`** — NOVO: golden tests por indicador

**Padrões obrigatórios:**
- Forward-ref nos type hints de `pd.*` (convenção já usada no projeto)
- `import pandas as pd` lazy dentro de funções, não no topo do módulo engine
- Thresholds em `config.yaml` (mesma convenção de `cfg["ddm"]`, `cfg["capm"]`)
- `st.session_state` para persistência dos toggles dentro da sessão

### Critical Pitfalls

1. **Distorção por splits na série nominal (CRÍTICO)** — Calcular indicadores sobre `Close` nominal gera cruzamentos e rompimentos espúrios em datas de splits/grupamentos B3 (BBAS3, WEGE3 etc.). Solução: usar série split-adjusted (não dividend-adjusted) para os cálculos internos; manter eixo do gráfico em nominal (CR-01). Derivar split factor de `tk.splits` ou do ratio `Close/Adj Close` menos componente de dividendo. Travar com golden test em ticker sintético com split 2:1.

2. **Suavização errada no RSI e ADX — usar Wilder, não EMA padrão (CRÍTICO)** — RSI e ADX usam `ewm(alpha=1/length, adjust=False)`, não `ewm(span=length)` (que dá `alpha=2/(length+1)`). A diferença produz valores materialmente divergentes de qualquer terminal de referência. Seed = SMA dos primeiros `length` valores. Travar com golden test contra fixture manual ou TradingView. Não adicionar dependência de biblioteca para resolver isso (ver Resolução de Conflito acima).

3. **Look-ahead / off-by-one (CRÍTICO)** — Sinais não podem usar dados de candles ainda abertos. Crossovers e rompimentos comparam barra *t* com barra *t-1*, nunca *t+1*. Travar com no-repaint test: `indicator(series[:k])[-1] == indicator(series)[k-1]` para vários `k`.

4. **Framing: técnico sobrepondo o veredito fundamentalista (CRÍTICO — produto)** — Badge verde "timing favorável" ao lado de veredito "CARA" leva usuário a agir pelo técnico. O bloco técnico deve ser subordinado visual e verbalmente ao fundamento, off by default, em seção claramente secundária. Nenhum imperativo ("compre/venda") — sempre linguagem consultiva ("reveja os fundamentos"). Critério de aceite: tela "cara + bullish-timing" lida por leitor novo; ele deve reconhecer o fundamento como decisório.

5. **Warm-up / NaN em tickers com histórico curto (MODERADO)** — MM200 requer ≥200 pregões; ADX exige ~2×length de aquecimento. Degradar graciosamente por indicador (nunca esconder o gráfico inteiro), exibindo "MM200 indisponível (histórico < 200 pregões)" — espelhando o padrão GRAF-03 já existente.

---

## Implications for Roadmap

A pesquisa aponta para 4 fases naturais, definidas pelas dependências técnicas e pelos pontos de risco.

### Fase A: Data plumbing + série correta para indicadores

**Rationale:** Zero comportamento novo, risco zero de quebrar os 64 golden tests existentes. É a fundação que todas as outras fases dependem. O OHLC já está em memória — só precisa parar de ser descartado. A decisão sobre série split-adjusted deve ser tomada aqui, antes de qualquer cálculo.
**Delivers:** `DadosMercado.ohlc`, `CompanyData.ohlc`, série split-adjusted em `prices.py`, testes existentes verdes.
**Addresses:** Pitfall 2 (split distortion) — a decisão de cálculo mais importante do marco.
**Avoids:** Nova chamada de rede ao yfinance; uso de `Adj Close` como base do gráfico (CR-01).
**Research flag:** Padrão bem estabelecido (espelha `serie_precos`). Sem necessidade de pesquisa adicional. Ponto de validação: testar série split-adjusted com ticker de split conhecido antes de avançar.

### Fase B: Motor de indicadores puro (`core/indicators.py`)

**Rationale:** Com OHLC disponível, implementar os cálculos como funções puras testáveis. É o ponto de maior risco técnico (Wilder, look-ahead, NaN). Os golden tests devem estar verdes antes de qualquer integração com a UI.
**Delivers:** `SinaisTecnicos` dataclass, `calcular(ohlc, cfg)` cobrindo as 4 famílias, `tests/test_indicators.py` com golden values para RSI/ADX (Wilder) + no-repaint test + split-date test.
**Uses:** pandas `ewm(alpha=1/length, adjust=False)`, `rolling`, `polyfit`/`linregress` — zero novas dependências.
**Implements:** Módulo puro → dataclass de sinais (Pattern 2 da arquitetura).
**Addresses:** Pitfall 1 (look-ahead), Pitfall 3 (Wilder — ver Resolução de Conflito), Pitfall 4 (warm-up/NaN), Pitfall 6 (parâmetros canônicos fixos em `config.yaml`).
**Research flag:** Fórmulas canônicas bem documentadas. Atenção especial ao seed de Wilder + split-adjusted series — ambos com referências claras nas fontes. Ponto de validação: fixture RSI/ADX cruzado com TradingView antes de travar o golden test.

### Fase C: Integração na engine e paridade CLI

**Rationale:** Com o módulo puro pronto e testado, conectar em `analisar_acao` é operação de baixo risco. O composite "timing de entrada" e o alerta de reverificação vivem aqui — são lógica de negócio, não de apresentação.
**Delivers:** `a.sinais` disponível em `AnaliseAcao`; campos `timing_entrada` e `alerta_reverificacao` como strings consultivas; seção "Sinais técnicos" em `relatorio_markdown` (CLI parity gratuita).
**Implements:** Threading `ohlc` via `analisar_acao`; integração em `report.py`.
**Addresses:** Pitfall 9 (framing) — copy consultivo e hierarquia fundamento > técnico nascem aqui.
**Research flag:** Padrão bem estabelecido. Ponto de atenção: formalizar as regras de desempate do composite como golden test antes de expor na UI (ex.: "MM200 acima mas ADX < 20 → qual é o estado?").

### Fase D: UI — overlays, subplots, toggles e framing

**Rationale:** Fase exclusivamente de apresentação — `app.py` read-only lendo `a.sinais`. O risco é de produto (framing e clutter), não técnico. Subplots para osciladores (RSI/MACD/ADX) exigem migração de `go.Figure()` para `make_subplots` dinâmico.
**Delivers:** Overlays no eixo de preço (SMA/EMA/Bollinger/Donchian), subplots dinâmicos para osciladores, toggles/multiselect, resumo de timing e alerta de reverificação na UI, tooltips de glossário para os novos indicadores.
**Uses:** `plotly.subplots.make_subplots`, `st.multiselect`, `st.session_state`, `esc_md()` (já existente).
**Addresses:** Pitfall 9 (framing — critério de aceite do fresh-reader test), Pitfall 10 (clutter — osciladores off by default), Pitfall 7 (daily vs weekly — padrão semanal para alertas de crossover/MM200).
**Research flag:** `make_subplots` dinâmico com número de linhas variável tem padrão documentado no STACK.md. Risco real é de UX/framing — incluir critério de aceite explícito no plano da fase: mostrar tela "cara + bullish-timing" a leitor externo.

### Phase Ordering Rationale

- A antes de B: o módulo de indicadores precisa do campo OHLC no dataclass para integração; as funções puras podem ser escritas/testadas com frames sintéticos em paralelo (A e B podem sobrepor parcialmente).
- B antes de C: `analisar_acao` só pode chamar `indicators.calcular` depois que o módulo existe e tem golden tests verdes.
- C antes de D: a UI lê `a.sinais` — esse campo precisa existir em `AnaliseAcao` antes de `app.py` tentar acessá-lo.
- Os 64 golden tests existentes devem permanecer verdes ao longo de todas as fases como invariante contínuo.

### Research Flags

Fases que NÃO precisam de pesquisa adicional (padrões bem estabelecidos):
- **Fase A:** threading de dataclass é cópia literal do padrão `serie_precos` já no código
- **Fase C:** integração em `analisar_acao` é adição cirúrgica; padrão CLI parity já existe
- **Fase D:** `make_subplots` e toggles têm documentação direta no STACK.md

Pontos de validação durante execução (não pesquisa, mas verificação antes de avançar):
- **Fase A:** testar série split-adjusted com ticker de split conhecido antes de fechar a fase
- **Fase B:** cruzar fixture RSI/ADX com TradingView antes de travar o golden test
- **Fase D:** fresh-reader test com tela "cara + bullish-timing" como critério de aceite explícito

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verificado diretamente no `.venv` do projeto; incompatibilidades com libs de TA cruzadas com PyPI e migration guides do numpy 2 |
| Features | HIGH | Parâmetros canônicos são literatura estabelecida; enquadramento consultivo derivado do PROJECT.md e do livro |
| Architecture | HIGH | Grounded no código real v1.1; padrão `serie_precos` é o blueprint exato; ponto único de compute (`analisar_acao`) confirmado em `cli.py` e `app.py` |
| Pitfalls | HIGH | Computação, ajuste de preço e framing cruzados com múltiplas fontes independentes e com o código atual |

**Overall confidence:** HIGH

### Gaps to Address

- **Split-adjusted series (implementação concreta):** a pesquisa confirma que é necessário e como fazê-lo conceitualmente, mas a implementação robusta no yfinance deve ser validada com um ticker de split conhecido durante a Fase A.
- **Timeframe semanal (decisão de produto):** PITFALLS.md recomenda padrão semanal para alertas de crossover/MM200; FEATURES.md trata como diferenciador. Recomendação desta síntese: entrar no v1.2 como padrão dos alertas (não do gráfico visual). Roadmapper deve confirmar esse escopo.
- **Composite timing — regras de desempate:** a hierarquia (MM200 > ADX/slope > crossovers > RSI/MACD) está especificada; as regras exatas de casos-limite devem ser formalizadas como golden test na Fase C antes de expor na UI.

---

## Sources

### Primary (HIGH confidence)
- `.venv` do projeto (verificação direta) — numpy 2.4.6, pandas 3.0.3, scipy 1.17.1, plotly 6.8.0, streamlit 1.58.0
- `src/analista/ingest/prices.py` + `app.py` + `report/report.py` + `cli.py` (leitura do código real v1.1)
- `.planning/PROJECT.md` — Key Decisions (CR-01 nominal, consultivo, app.py read-only, ligável/desligável)
- [Dutch Algotrading — Wilder's Moving Average Guide](https://www.dutchalgotrading.com/2025/11/28/wilders-moving-average-smoothed-ma-guide/) — alpha = 1/length vs 2/(length+1)
- [Fidelity — Average Directional Index (ADX)](https://www.fidelity.com/viewpoints/active-investor/average-directional-index-ADX) — thresholds ADX < 20 / > 25
- [Alvarez Quant Trading — dividend adjust or not](https://alvarezquanttrading.com/blog/to-dividend-adjust-or-not-to-dividend-adjust-that-is-the-question/) — splits criam falsos sinais bearish; dividendos preservam relacionamentos

### Secondary (MEDIUM confidence)
- [Lizard Indicators — Donchian Channel Strategy](https://www.lizardindicators.com/donchian-channel-strategy/) — períodos 20/55 Turtle System
- [Chart Guys — ADX Indicator](https://www.chartguys.com/articles/adx-indicator) — thresholds ADX
- [StockCharts — Price Data Adjustments](https://help.stockcharts.com/data-and-ticker-symbols/data-availability/price-data-adjustments) — split gaps causam falsos sinais de TA
- [trendsandbreakouts — MA Crossover Rules](https://trendsandbreakouts.com/ma-crossover) — semanal vs diário, ADX como filtro de whipsaw
- PyPI `ta` 0.11.0 e `pandas-ta` 0.4.71b0 — datas de release e requisitos confirmados

---
*Research completed: 2026-06-24*
*Ready for roadmap: yes*
