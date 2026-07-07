# Phase 12: Ingestão Intraday + Timeframe - Context

**Gathered:** 2026-06-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Entregar uma **camada de ingestão de OHLCV multi-timeframe** (diário + 1h/30m/5m) para um
ticker, **isolada** do pipeline diário fundamentalista (`coletar_mercado`/`montar_empresa`) e
do cache da aba Analisar, em **base nominal correta** (split-only-adjusted reutilizando
`_ajustar_por_split`), com timestamps em `America/Sao_Paulo` e **refresh targetado** (TTL curto
+ nonce, nunca `.clear()` global). É a fundação de dados da v1.4; **não** calcula indicadores,
pivôs, níveis nem desenha gráfico (Fases 13–16). Os 191 testes golden seguem verdes.

**Fora de escopo (pertence a outras fases):** detecção de pivôs/tendência/níveis (13), padrões
e checklist (14), montagem do `SetupSwing` + score (15), página Streamlit/gráfico (16).
</domain>

<decisions>
## Implementation Decisions

### Contrato de retorno (a forma que as Fases 13/16 consomem)
- **D-01:** A função de ingestão intraday entrega um **dataclass rico** (ex.: `FrameOHLC`),
  espelhando o padrão existente (`DadosMercado`, `SinaisTecnicos`) e mantendo `app.py` thin.
  Forma sugerida dos campos (o planner pode renomear, mas o conteúdo é fixo):
  `timeframe`, `ohlc` (nominal), `ohlc_ajustado` (split-only), `ultima_barra_ts`,
  `barra_viva: bool`, `idx_ultima_fechada`, `atraso_min`, `disponivel: bool`, `motivo`.
- **D-02:** O dataclass carrega **ambas** as séries — `ohlc` **nominal** (gráfico + níveis
  entrada/stop/alvo, p/ cumprir o critério #2: "mesma base nominal do gráfico") e
  `ohlc_ajustado` **split-only** (consumido por `indicators.calcular()`). Reutiliza
  `prices._ajustar_por_split` (sem nova chamada de rede). Espelha o diário (`ohlc` +
  `ohlc_ajustado`); split em janela intraday curta é raro, mas o contrato fica uniforme.

### Barra viva (última barra não fechada)
- **D-03:** Política **manter + marcar**: o frame inclui a barra viva, e o dataclass expõe
  `barra_viva` + `idx_ultima_fechada`. A Fase 16 desenha a barra "em formação"; a Fase 13
  calcula **sempre** sobre a barra fechada (`iloc[-2]`). Um único frame serve aos dois
  consumidores sem perder informação.
- **D-04:** Detecção **conservadora**: a última barra é **sempre** tratada como potencialmente
  viva/suspeita — cálculos usam `iloc[-2]` por contrato (alinha o STATE). Determinístico,
  testável em golden e **imune ao TZ da VPS (UTC) e a feriados/leilão**. Trade-off aceito:
  fora de pregão "perde" 1 barra fechada nos cálculos; o gráfico ainda mostra todas as barras.
  (Deliberadamente **NÃO** depende de relógio nem de calendário de pregão B3.)

### Profundidade do histórico por timeframe
- **D-05:** Buscar o **máximo disponível por timeframe** (teto do Yahoo): 5m/30m ≈ 60d,
  1h ≈ 730d, diário 5y. Maximiza indicadores viáveis e dá contexto p/ pivôs/padrões (Fases
  13/14). O que não tiver barras suficientes (ex.: MM200 em frame curto) cai para
  **"indisponível"** via o guard já existente em `indicators.calcular()` — sem quebrar.
  O `period × interval` exato deve ser **confirmado empiricamente** na implementação (limite
  yfinance é MEDIUM-confidence no roadmap).

### Falha / dados vazios (best-effort)
- **D-06:** A borda **nunca** retorna `None` nem levanta exceção (espelha o guard de
  `indicators.calcular()`): em qualquer falha retorna o dataclass com `disponivel=False`.
- **D-07:** O `motivo` é **categorizado** — conjunto fixo de causas (ex.: `fetch_falhou`,
  `sem_dados`, `historico_insuficiente`). A Fase 16 mapeia cada categoria para uma mensagem
  amigável. Mantém a copy de UI **fora** da camada de dados, é testável em golden e traduzível.

### Cache / refresh (travado pelo roadmap — registrado para o planner)
- **D-08:** Cache intraday **isolado** com TTL curto (300s) + **nonce** no botão Atualizar;
  re-buscar `(ticker, timeframe)` invalida **só** aquele cache. **Nunca** `st.cache_data.clear()`
  global (apagaria o cache da aba Analisar). Chave de cache mínima: `(ticker, timeframe)`
  (+ nonce). (Não rediscutido — herdado das decisões do milestone.)

### Claude's Discretion
- Nomes exatos de módulo/dataclass/campos e a localização do arquivo (novo `ingest/intraday.py`
  vs. extensão de `ingest/prices.py`) — decisão de arquitetura do planner, seguindo os padrões
  do projeto (`ingest/` + dataclasses ricas).
- `period × interval` concreto por timeframe (calibrar contra os limites reais do yfinance).
- Forma de expor as categorias de `motivo` (Enum vs. constantes string) e o escopo exato do nonce.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap / requisitos da fase
- `.planning/ROADMAP.md` §"Phase 12: Ingestão Intraday + Timeframe" — Goal, 5 Success Criteria, constraints inegociáveis do milestone v1.4.
- `.planning/REQUIREMENTS.md` — DATA-01 (ingestão intraday isolada), DATA-02 (timeframe + aviso de atraso + degradação "indisponível"), DATA-03 (Atualizar + cache TTL curto + invalidação targetada).
- `.planning/STATE.md` §"Accumulated Context" — decisões/blockers do v1.4 (no-repaint, barra viva, cache isolado, base nominal).

### Código a reutilizar (split-adjust, contrato OHLC, cache)
- `src/analista/ingest/prices.py` — `_ajustar_por_split()` (split-only puro, sem rede; REUSAR), `coletar_mercado()`/`yahoo_symbol()`, padrão de retry yfinance (`_MAX_TENTATIVAS`/`_BACKOFF_SEG`), dataclass `DadosMercado` (modelo do contrato rico, com `ohlc` + `ohlc_ajustado`).
- `src/analista/core/indicators.py` — `calcular(ohlc, cfg)` é **timeframe-agnostic** e já degrada para "indisponível" em frame curto/vazio (consumidor do `ohlc_ajustado` na Fase 13).
- `src/analista/ingest/build.py` — `montar_empresa()` (linhas ~46/65/66: wiring de `coletar_mercado` → `c.ohlc`/`c.ohlc_ajustado`); a ingestão intraday deve ficar **separada** desse fluxo.
- `app.py` — padrão `@st.cache_data(ttl=...)` (`montar`, `selic_atual`); `app.py` permanece **read-only**.
- `config.yaml` §`indicadores` — parâmetros canônicos (SMA/RSI/MACD/ADX, `base_temporal: diario`); base de onde virão params por TF nas fases seguintes.

### Livro (método de referência da v1.4 — análise técnica)
- `../Analise_Tecnica_dos_Mercados_Financeiros.pdf` (John Murphy) — fonte do método de swing/AT do milestone; pouco relevante p/ a Fase 12 (dados), central nas Fases 13–16.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `prices._ajustar_por_split(hist)`: função pura que deriva split-only-adjust da coluna "Stock Splits" do frame `auto_adjust=False` — reusar tal-qual para gerar `ohlc_ajustado` intraday.
- `prices.yahoo_symbol()` + retry (`_MAX_TENTATIVAS`/`_BACKOFF_SEG`): reaproveitar a resolução `.SA` e a tolerância a rate-limit intermitente do Yahoo.
- `DadosMercado`: molde do dataclass rico (carrega `ohlc` nominal + `ohlc_ajustado`).

### Established Patterns
- `indicators.calcular()` é agnóstico de timeframe e já tem guard de borda (None/vazio/sem colunas → frame vazio, "indisponível", nunca exceção) — a Fase 12 não precisa reimplementar degradação de indicador.
- Cache via `@st.cache_data(ttl=...)` em `app.py`; nunca `.clear()` global.
- `auto_adjust=False` para preservar Close **nominal** (mesma base da banda DDM/gráfico).

### Integration Points
- Nova ingestão intraday é **paralela** a `coletar_mercado`/`montar_empresa` (não os altera). O consumidor a jusante é `indicators.calcular()` (Fase 13) via `ohlc_ajustado`, e o gráfico (Fase 16) via `ohlc` nominal + metadados (`barra_viva`, `ultima_barra_ts`, `atraso_min`, `disponivel`/`motivo`).
- O fetch diário 5y da aba Analisar e seu cache permanecem **intactos**.

</code_context>

<specifics>
## Specific Ideas

- Contrato espelha explicitamente o diário (`ohlc` nominal + `ohlc_ajustado` split-only), para que entrada/stop/alvo (Fase 13) nasçam na mesma base nominal do gráfico.
- Regra "última barra sempre suspeita → `iloc[-2]`" é uma escolha consciente de **robustez/determinismo sobre precisão**: nada de relógio nem calendário B3 na detecção de barra viva.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 12-Ingestão Intraday + Timeframe*
*Context gathered: 2026-06-29*
