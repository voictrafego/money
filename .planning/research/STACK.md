# Stack Research

**Domain:** Análise técnica / setups de swing-trade (página nova no app Streamlit existente)
**Researched:** 2026-06-29
**Confidence:** HIGH

## Headline

**Nenhuma dependência de runtime nova é necessária.** Tudo que o v1.4 pede
— ingestão diária/intraday, detecção de pivôs, padrões gráficos, S/R, trendlines,
Fibonacci, score + Risco:Retorno, gráfico candlestick e refresh sob demanda —
se constrói sobre a stack já instalada e validada: `pandas 3.0.3`, `numpy 2.4.6`,
`scipy 1.17.1`, `yfinance 1.4.1`, `plotly 6.8.0`, `streamlit 1.58.0`.

Isso respeita o princípio custo-zero/minimal-deps e mantém a arquitetura que já
funciona: cálculo puro em `core/` + specs puros em `grafico.py` + `app.py` fino de
render. As libs de "chart pattern" de prateleira são reimplementações finas de
`scipy.signal` mal mantidas e sem golden — adicioná-las seria um retrocesso de
qualidade frente ao `indicators.py` atual (Wilder/TradingView-grade, golden-testado).

## Recommended Stack

### Core Technologies (TODAS já instaladas — reusar, não adicionar)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| yfinance | 1.4.1 (já instalado) | Ingestão OHLCV diária + intraday (1h/30m/5m) free | Mesma fonte custo-zero do projeto; `history(interval=, period=)` cobre intraday sem dep nova. NOTA: 1.x é major (breaking vs 0.2.x) mas já está em uso no projeto e estável. |
| pandas | 3.0.3 (já instalado) | Resample, rolling, agregação de pivôs/clusters S/R | Já é a espinha dorsal de `indicators.py`/`prices.py`. Copy-on-write é default no 3.0 — manter o padrão `.copy(deep=True)` que `_ajustar_por_split` já usa. |
| numpy | 2.4.6 (já instalado) | Geometria de trendline (`polyfit`), Fibonacci, aritmética de score/R:R | Zero-custo, já onipresente. numpy 2.x já é a base do projeto. |
| scipy | 1.17.1 (já instalado) | **Detecção de pivôs** via `scipy.signal.find_peaks` (e `linregress` p/ ajuste de reta de trendline, já usado em `regressao_trailing`) | Já é dependência (RSI/ADX seed, regressão). `find_peaks(prominence=, distance=)` é o detector de topos/fundos correto e robusto — é o núcleo de toda detecção de padrão/S-R/trendline. Não precisa de lib de pattern externa. |
| plotly | 6.8.0 (já instalado) | Gráfico candlestick (`go.Candlestick`) + overlays (linhas S/R, trendlines, Fibonacci via `add_hline`/`add_shape`) + markers de padrão | Já é o motor do gráfico da aba Analisar (`grafico.py`/Phase 7). `go.Candlestick` é nativo — não precisa de `mplfinance`. Reusa o padrão de spec puro existente. |
| streamlit | 1.58.0 (já instalado) | Página nova, seletor de timeframe, botão "Atualizar", cache TTL | `st.cache_data(ttl=...)` + `.clear()` + `st.rerun()` cobrem o refresh sob demanda nativamente. Sem `streamlit-autorefresh`. |

### Supporting Libraries — IN-HOUSE (novos módulos puros, sem dep nova)

A recomendação é escrever módulos puros novos em `src/analista/core/` espelhando o
contrato de `indicators.py` (dataclasses agrupadas, sinais discretos em chaves
estáveis, degradação para `"indisponivel"`, golden-testável). Estimativa: ~400–600
linhas no total, totalmente cobríveis por golden — muito menos custo de manutenção
que adotar e auditar uma lib externa de padrões.

| Módulo novo (in-house) | Constrói sobre | Purpose | When to Use |
|---------|---------|---------|-------------|
| `core/pivots.py` | `scipy.signal.find_peaks` | Topos/fundos (swing highs/lows) com `prominence` (ruído) e `distance` (separação mínima). Base de TUDO. | Sempre — entrada para S/R, trendlines e padrões. |
| `core/suporte_resistencia.py` | pivôs + clustering 1-D (numpy) | Agrupa pivôs próximos em zonas de S/R; pontua por nº de toques + recência. | Níveis de preço, zona de entrada, stop técnico. |
| `core/trendlines.py` | pivôs + `np.polyfit`/`scipy.stats.linregress` | Reta por ≥2-3 pivôs de mesmo lado; valida nº de toques e inclinação; canais. | Triângulos, bandeiras, suporte/resistência diagonal. |
| `core/padroes.py` | pivôs + regras geométricas | OCO/OCOI, topo/fundo duplo, triângulos (asc/desc/simétrico), bandeiras — regras de simetria/neckline sobre a sequência de pivôs. Projeção de alvo por altura do padrão. | Checklist de padrões + alvo. |
| `core/fibonacci.py` | numpy puro | Retração (0.236/0.382/0.5/0.618/0.786) e extensão (1.272/1.618) entre dois pivôs (swing). Aritmética trivial. | Alvos/retrações; NÃO justifica lib. |
| `core/setup.py` | tudo acima + `indicators.py` | Agrega contexto (Dow+MMs reusando `SinaisTecnicos`) → score de qualidade + Risco:Retorno de (entrada, stop, alvo). Dataclass de saída read-only. | Veredito final do setup (EXIBE, não recomenda). |
| `grafico_tecnico.py` | (espelha `grafico.py`) | Specs puros de candlestick + overlays (S/R, trendlines, Fibonacci, markers de padrão) p/ o `app.py` renderizar. | Gráfico "do momento". |

### Ingestão intraday — extensão de `ingest/prices.py` (sem dep nova)

Adicionar uma função tipo `coletar_ohlc(ticker, timeframe)` que chama
`tk.history(interval=<intervalo>, period=<período>, auto_adjust=False)` e devolve o
OHLCV (reaproveitando o `_ajustar_por_split` para a base split-adjusted dos
indicadores). **Limites do free tier do Yahoo (HARD limits — não contornáveis sem feed pago):**

| Timeframe | `interval` | `period` máx (Yahoo) | Observação |
|-----------|-----------|----------------------|------------|
| Diário (padrão swing) | `1d` | `max`/`5y` (já em uso) | Robusto — caminho principal. |
| 1 hora | `1h` | **~730 dias (2 anos)** | Bom histórico p/ swing intraday. |
| 30 min | `30m` | **~60 dias** | Best-effort. |
| 5 min | `5m` | **~60 dias** | Best-effort. |
| (1 min) | `1m` | **~7 dias** | Fora do escopo declarado; citado só p/ contexto. |

Caveats a tratar na borda (degradação graciosa, como o resto do projeto):
- **Atraso ~15 min** nos dados intraday do Yahoo — exibir aviso explícito na UI
  (já é decisão registrada no PROJECT.md). Não é tempo real.
- **Sem split-adjust intraday confiável** em janelas curtas — para 5m/30m em 60d
  splits são raros; manter `auto_adjust=False` + ajuste por "Stock Splits" como no diário.
- **`.SA` da B3 + rate-limit por IP**: o retry com backoff que `coletar_mercado` já
  implementa (`_MAX_TENTATIVAS`/`_BACKOFF_SEG`) deve ser reusado; intraday falha vazio
  com mais frequência. Degradar para "dados indisponíveis neste timeframe" sem exceção.
- **Pregão B3** (10h–17h BRT): fora do horário o último candle 5m fica estático.

## Streamlit — padrão de refresh + cache sob demanda

Pattern recomendado (nativo, sem lib):

```python
@st.cache_data(ttl="15m", show_spinner="Buscando dados…")
def carregar_ohlc(ticker: str, timeframe: str):
    return prices.coletar_ohlc(ticker, timeframe)   # função pura de ingestão

# seletor + botão na página nova
tf = st.selectbox("Timeframe", ["Diário", "1h", "30m", "5m"])
if st.button("Atualizar"):
    carregar_ohlc.clear()        # limpa SÓ esta função (targeted), não o cache global
    st.session_state["ult_fetch"] = datetime.now()
    st.rerun()

ohlc = carregar_ohlc(ticker, tf)  # cache key = (ticker, timeframe)
```

Princípios:
- **Cache key = `(ticker, timeframe)`** — trocar de ticker/timeframe re-busca sozinho.
- **`ttl="15m"`** alinhado ao atraso do Yahoo: evita marteladas no Yahoo sem mostrar dado "velho demais".
- **Botão "Atualizar" → `carregar_ohlc.clear()` (escopo da função) + `st.rerun()`** — NÃO usar `st.cache_data.clear()` global (apagaria o cache da engine fundamentalista da aba Analisar).
- **`st.session_state`** guarda o timestamp do último fetch p/ exibir "atualizado às HH:MM (atraso ~15min)".
- Cálculos (pivôs/padrões/score) ficam em funções puras → podem ser memoizados à parte ou recomputados (são baratos sobre poucos milhares de candles).

## Installation

```bash
# Nada a instalar. Toda a capacidade do v1.4 usa deps já presentes em requirements.txt.
# requirements.txt permanece inalterado:
#   pandas>=2.0  numpy>=1.24  scipy>=1.11  yfinance>=0.2.40  streamlit>=1.30  plotly>=6.0
# (ambiente já roda pandas 3.0.3 / numpy 2.4.6 / scipy 1.17.1 / yfinance 1.4.1 /
#  streamlit 1.58.0 / plotly 6.8.0 — todas compatíveis.)
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `scipy.signal.find_peaks` | `scipy.signal.argrelextrema` | `argrelextrema` é mais cru (sem `prominence`/`distance`), tende a pegar ruído. Use só se quiser o extremo local bruto; `find_peaks` é estritamente melhor p/ pivôs de swing e já está disponível. |
| Detecção de padrões in-house | `pandas-ta` (indicadores) | Só faria sentido se NÃO existisse `indicators.py`. O projeto já tem indicadores Wilder golden-testados — `pandas-ta` seria redundante e menos fiel ao TradingView. |
| `go.Candlestick` (Plotly) | `mplfinance` | Use `mplfinance` apenas p/ PNG estático server-side. Aqui o gráfico é interativo no Streamlit → Plotly nativo já em uso. |
| `st.cache_data(ttl)` + botão | `streamlit-autorefresh` | Só se quisesse polling automático em loop (terminal de trade). O escopo é refresh MANUAL ("botão Atualizar") → nativo basta e é mais barato. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **TA-Lib** | Lib C com build de sistema (não-pip-puro); pesada; quebra "minimal deps" e deploy Docker simples. | `indicators.py` in-house (já existe) + `scipy.signal`. |
| **pandas-ta** | Redundante com `indicators.py`; menos fiel ao TradingView (sem o seed-SMA de Wilder que o projeto já acertou). | Reusar `core/indicators.py`. |
| **PatternPy / TradingPatternScanner / chart_patterns (zeta-zetra)** | Repos GitHub pouco mantidos, sem releases estáveis no PyPI, sem testes golden, qualidade abaixo do padrão do projeto. São wrappers finos de `scipy`/rolling-window que você escreve melhor in-house. | `core/padroes.py` in-house sobre pivôs. |
| **mplfinance** | Render estático matplotlib; não é interativo no Streamlit. | `plotly.graph_objects.Candlestick`. |
| **streamlit-autorefresh** | Polling automático = "cara de terminal de trade" + martela o Yahoo (rate-limit). Escopo é refresh manual. | Botão "Atualizar" + `st.cache_data(ttl)`. |
| **brapi pago / feeds premium / websockets / ccxt** | Viola custo-zero; tempo real puro já declarado fora de escopo no v1.4. | yfinance free com aviso de atraso ~15min. |
| **scikit-learn / ML p/ padrões** | Over-engineering; padrões clássicos de Murphy são regras geométricas determinísticas, não ML. Adiciona dep pesada e não-determinismo. | Regras geométricas in-house (golden-testáveis). |

## Stack Patterns by Variant

**Se o timeframe for Diário:**
- Reusar o caminho de `period="5y"`/`max` já validado em `prices.py`.
- Pivôs com `distance` maior (ex.: 5 candles) p/ swing clássico.

**Se o timeframe for intraday (1h/30m/5m):**
- Usar `interval=`/`period=` dentro dos limites do Yahoo (tabela acima); exibir aviso de atraso e de histórico limitado.
- Pivôs com `prominence` relativo à volatilidade do timeframe (ATR-scaled) p/ não pegar microruído.

**Se o histórico vier curto (intraday best-effort falha):**
- Degradar para `"indisponivel"` (mesmo padrão de `indicators.calcular`/`grafico`), nunca exceção na UI.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| yfinance 1.4.1 | pandas 3.0.3 | `history(interval=, period=)` estável; 1.x é major (breaking vs 0.2.x) mas já adotado no projeto. Conferir que `tk.history` ainda devolve "Stock Splits" (consumido por `_ajustar_por_split`). |
| pandas 3.0.3 | numpy 2.4.6 | Copy-on-write é DEFAULT no pandas 3.0 — manter `.copy(deep=True)` antes de mutar frames (padrão já presente). Evitar assignment encadeado. |
| scipy 1.17.1 | numpy 2.4.6 | `find_peaks`/`linregress`/`argrelextrema` estáveis; sem mudança de API relevante. |
| plotly 6.8.0 | streamlit 1.58.0 | `st.plotly_chart` + `go.Candlestick` ok; reusar o padrão de spec puro de `grafico.py`. |
| streamlit 1.58.0 | — | `st.cache_data(ttl=...)`, `<func>.clear()` (targeted) e `st.rerun()` são API atual e estável. |

## Integration Points (resumo p/ o roadmap)

1. **`ingest/prices.py`** → nova função `coletar_ohlc(ticker, timeframe)` reusando retry/backoff e `_ajustar_por_split`.
2. **`core/indicators.py`** → `calcular(ohlc, cfg)` já é agnóstico de timeframe (docstring confirma) → recebe o frame intraday sem mudança. Reusar `SinaisTecnicos` p/ o "contexto de tendência (Dow+MMs)".
3. **Novos `core/*`** (pivots, suporte_resistencia, trendlines, padroes, fibonacci, setup) → módulos puros golden-testáveis.
4. **`grafico_tecnico.py`** → specs puros (espelha `grafico.py`) p/ candlestick + overlays.
5. **`app.py`** → página/menu novo (4º menu), seletor de timeframe, botão "Atualizar", cache TTL — camada fina de render, sem recalcular método (regra `app.py` read-only).

## Sources

- Ambiente local (`pip list`) — versões instaladas confirmadas: yfinance 1.4.1, pandas 3.0.3, numpy 2.4.6, scipy 1.17.1, plotly 6.8.0, streamlit 1.58.0 — HIGH.
- [yfinance intraday limits — AlgoTrading101 / issue #2451](https://github.com/ranaroussi/yfinance/issues/2451) — 1m=7d, intraday<1d=60d, 1h=730d — MEDIUM (múltiplas fontes concordam, comportamento do Yahoo).
- [st.cache_data — Streamlit Docs](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data) — `ttl`, `.clear()` targeted, botão de refresh — HIGH.
- [PatternPy](https://github.com/keithorange/PatternPy) / [TradingPatternScanner](https://github.com/white07S/TradingPatternScanner) / [chart_patterns](https://github.com/zeta-zetra/chart_patterns) — avaliados e descartados (wrappers finos de scipy, sem releases/golden) — MEDIUM.
- [Detecting chart patterns w/ Python — Alpaca](https://alpaca.markets/learn/algorithmic-trading-chart-pattern-python) — confirma abordagem `scipy` pivot + regras geométricas como padrão da indústria — MEDIUM.
- Código existente lido: `core/indicators.py`, `ingest/prices.py`, `grafico.py`, `requirements.txt`, `.planning/PROJECT.md` — HIGH.

---
*Stack research for: análise técnica / setups de swing-trade (v1.4)*
*Researched: 2026-06-29*
