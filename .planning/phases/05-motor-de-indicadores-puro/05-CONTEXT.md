# Phase 5: Motor de indicadores puro - Context

**Gathered:** 2026-06-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Um módulo **puro** `src/analista/core/indicators.py` que recebe o frame OHLC (a série split-adjusted de `CompanyData.ohlc_ajustado`, entregue na Phase 4) e devolve um dataclass `SinaisTecnicos` com **séries prontas para plotar** + **sinais discretos**, cobrindo as 4 famílias do marco:

- **Tendência:** SMA/EMA 20/50/200 + golden/death cross (MM50×MM200) + posição preço×MM200 + toggle EMA (TREND-01..04)
- **Canais:** Donchian 20/55 + Bollinger 20/2σ + squeeze, com rompimentos rotulados (CHAN-01..03)
- **Força:** ADX(14) com suavização de Wilder + inclinação da regressão linear (FORCE-01..02)
- **Momentum:** RSI(14) Wilder + MACD 12/26/9 com cruzamento de sinal (MOM-01..02)

A matemática é **travada por golden tests** (Wilder cruzado com TradingView, no-repaint, série split-adjusted) **antes** de qualquer integração. Função canônica: `indicators.calcular(ohlc, cfg) -> SinaisTecnicos`. Zero novas dependências (só numpy/pandas/scipy já presentes); parâmetros canônicos vivem em `cfg`.

**Fora de escopo (outras fases):** fiação em `analisar_acao`/`a.sinais`, resumo de timing composite, matriz fundamento×técnico, alerta de reverificação e paridade CLI (Phase 6); overlays, subpainéis, toggles e tooltips na UI (Phase 7).

</domain>

<decisions>
## Implementation Decisions

### Formato e contrato do `SinaisTecnicos` (TREND/CHAN/FORCE/MOM)
- **D-01:** A engine devolve um dataclass **agrupado por família** (`tendencia` / `canais` / `forca` / `momentum`). Cada família carrega as **séries** (para o plot da Phase 7) **e** os **sinais discretos em estados curtos/neutros** — chaves estáveis tipo `"acima"`/`"abaixo"` (posição vs MM200), `"golden_cross"`/`"death_cross"`/`"nenhum"`, `"squeeze_on"`/`"squeeze_off"`, `"sobrecomprado"`/`"sobrevendido"`/`"neutro"`. **Frases consultivas em linguagem natural PT NÃO entram aqui** — o resumo de timing composite (linguagem natural) é responsabilidade da Phase 6. A engine separa **cálculo** de **apresentação**. (Escolhido: nested por família; rejeitados: flat e "só valores crus".)

### Definição do Bollinger squeeze (CHAN-03)
- **D-02:** Sem Keltner no escopo (só Donchian + Bollinger). O squeeze é definido por **percentil da própria largura**: `squeeze_on` quando a largura normalizada da BB `(banda_sup − banda_inf) / banda_media` está **≤ percentil 20 da própria largura** numa **janela móvel de ~126 pregões (~6 meses)**. Auto-normaliza por ticker e por nível de preço; mais informativo que mínimo absoluto (binário/ruidoso) ou limiar absoluto fixo (frágil entre tickers). Janela e percentil são parâmetros canônicos em `cfg`.

### Toggle EMA e base dos sinais discretos (TREND-04)
- **D-03:** A engine computa as **séries SMA E EMA sempre** (20/50/200) — o toggle do usuário (Phase 7) só troca **qual overlay é exibido**, sem recompute. Os **sinais discretos** de tendência — golden/death cross (MM50×MM200) e posição preço×MM200 — são **SEMPRE calculados sobre SMA** (base primária do método, padrão do marco). A EMA é uma **vista alternativa visual**, nunca altera o sinal. Isso casa com UI-03 (redesenhar o subconjunto sem recomputar) e evita contradição entre bases SMA/EMA.

### Inclinação da regressão linear (FORCE-02)
- **D-04:** Regressão linear sobre **~90 pregões (~1 trimestre)** da série **split-adjusted**. Direção + força expressas como **slope anualizado normalizado pelo preço (% ao ano)** e **R²** como qualidade do ajuste ("quão limpa" é a tendência). %/ano normalizado é robusto a escala/eixo (diferente de ângulo em graus). Janela é parâmetro canônico em `cfg`.

### Claude's Discretion
- Nomes exatos dos campos/subdataclasses do `SinaisTecnicos` (ex.: `tendencia.cross` vs `tendencia.sinal_cross`), desde que agrupados por família e com sinais discretos em chaves estáveis e neutras.
- Tipagem dos sinais discretos (str literal vs Enum) — desde que determinística e testável por golden.
- Estrutura interna das funções puras por indicador (uma função por família vs por indicador) — desde que cada uma seja pura, sem rede, e o ponto de entrada seja `calcular(ohlc, cfg)`.
- Nomes/defaults exatos das chaves de `cfg` (ex.: `squeeze_janela=126`, `squeeze_percentil=20`, `regressao_janela=90`) — desde que canônicos e documentados.
- Tratamento de histórico curto por indicador (ex.: MM200 com < 200 pregões → série com NaN inicial / sinal `"indisponivel"`) — degradação graciosa coerente com o padrão da Phase 4.

</decisions>

<inherited_decisions>
## Decisões travadas (de marcos/fases anteriores — NÃO re-perguntadas)

- **Série dos indicadores = split-adjusted** (`CompanyData.ohlc_ajustado`), não dividend-adjusted; o eixo/série do gráfico permanece Close nominal (decisão CR-01, Phase 4 D-03). [[analista-dividendos-mvp]]
- **RSI e ADX exigem suavização de Wilder** (`ewm(alpha=1/length, adjust=False)`, seed SMA), não EMA padrão — travar com golden cruzado com TradingView (TEST-03).
- **No-repaint** (TEST-04): nenhum sinal usa dados futuros — `indicador(série[:k])[-1] == indicador(série)[k-1]`.
- **Split-adjusted sem cruzamentos espúrios** num ticker com split conhecido (TEST-05; ITSA4 validado na Phase 4 D-08).
- **Zero novas dependências de TA** (`ta`/`pandas-ta`/`TA-Lib` incompatíveis com numpy 2.4.6 / pandas 3.0.3) — hand-roll em numpy/pandas/scipy.
- **Parâmetros canônicos vivem em `cfg`** — ponto único compartilhado por CLI e UI.
- **`a.sinais` é calculado em `analisar_acao`** (Phase 6) — ponto único, paridade CLI/UI gratuita. A Phase 5 só entrega o módulo puro consumido lá.
- **Análise técnica é consultiva** — nunca sobrescreve o veredito fundamentalista; o framing decisório é da Phase 6/7, não da engine.
- **Invariante TEST-07:** os 64 golden tests de valuation continuam verdes ao final de cada fase do marco — fase aditiva, nenhuma fórmula do livro muda.

</inherited_decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e roadmap do marco
- `.planning/ROADMAP.md` § "Phase 5: Motor de indicadores puro" — goal, depends-on (Phase 4), success criteria (params canônicos, Wilder, no-repaint, split).
- `.planning/REQUIREMENTS.md` — TREND-01..04, CHAN-01..03, FORCE-01..02, MOM-01..02, TEST-03, TEST-04, TEST-05 (Phase 5); TEST-07 (invariante contínuo 4-7).
- `.planning/STATE.md` § "Accumulated Context / Decisions" — decisões de pesquisa v1.2 (Wilder; sem nova dep de TA; `a.sinais` em `analisar_acao`; OHLC em memória).
- `.planning/PROJECT.md` — Core Value (fidelidade ao livro + consistência); decisão CR-01 (eixo nominal vs indicadores split-adjusted).

### Entrada da engine (Phase 4 — já entregue)
- `src/analista/core/fundamentals.py` — `CompanyData.ohlc` (nominal) e `CompanyData.ohlc_ajustado` (split-adjusted, **input dos indicadores**).
- `src/analista/ingest/prices.py` — `_ajustar_por_split` (como o ajuste foi derivado) + frame `ohlc` cru.
- `.planning/phases/04-encanamento-de-dados-s-rie-correta/04-CONTEXT.md` e `04-02-SUMMARY.md` — CR-01, regra do fator de split, validação ITSA4.

### Padrão de módulo puro a espelhar (dataclass + funções puras + golden tests)
- `src/analista/core/ddm.py` — `ResultadoDDM` dataclass + funções puras; modelo de "módulo de core puro travado por teste".
- `src/analista/core/multiples.py`, `src/analista/core/growth.py` — mesmo padrão de cálculo puro.
- `tests/test_ddm.py`, `tests/test_multiples.py` — padrão de golden test do projeto (fixtures + asserts numéricos).

### Consumidores a jusante (contexto, não modificar nesta fase)
- `src/analista/report/report.py` — `AnaliseAcao` (ganha campo `sinais` na Phase 6) + `analisar_acao(c, cfg)` (ponto único de chamada da engine na Phase 6).
- `src/analista/glossario.py` — dict `G` de tooltips (padrão dos tooltips de glossário que a Phase 7 vai estender para os indicadores).

</canonical_refs>

<specifics>
## Specific Ideas

- **Parâmetros canônicos sugeridos** (default em `cfg`, ajustáveis): SMA/EMA 20/50/200; Donchian 20/55; Bollinger 20, 2σ; squeeze janela 126 / percentil 20; ADX 14 (Wilder); RSI 14 (Wilder), faixas 30/70; MACD 12/26/9; regressão janela 90.
- **Fixtures de referência:** RSI(14) e ADX(14) devem bater com valores cruzados do TradingView (TEST-03) — o researcher deve capturar uma série de referência + valores esperados.
- **Ticker de estresse de split:** ITSA4 (5 eventos, já validado na Phase 4) para o teste TEST-05.

</specifics>

<deferred>
## Deferred Ideas

- **MOM-03** (divergências RSI/MACD vs preço) — explicitamente fora do marco v1.2 (já marcado como deferido em REQUIREMENTS.md).
- Outros indicadores (Keltner, Ichimoku, VWAP, estocástico) — novas capacidades, fora do escopo das 4 famílias definidas.

</deferred>

---

*Phase: 05-motor-de-indicadores-puro*
*Context gathered: 2026-06-26 via /gsd-discuss-phase*
