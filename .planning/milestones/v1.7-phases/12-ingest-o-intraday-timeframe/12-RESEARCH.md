# Phase 12: Ingestão Intraday + Timeframe - Research

**Researched:** 2026-06-29
**Domain:** Ingestão de OHLCV multi-timeframe via yfinance (Yahoo Finance), tz-handling, cache Streamlit targetado
**Confidence:** HIGH (limites e timezone confirmados empiricamente contra a API ao vivo + mensagens de erro da própria Yahoo)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** A função de ingestão intraday entrega um **dataclass rico** (ex.: `FrameOHLC`), espelhando o padrão existente (`DadosMercado`, `SinaisTecnicos`) e mantendo `app.py` thin. Campos (planner pode renomear, conteúdo fixo): `timeframe`, `ohlc` (nominal), `ohlc_ajustado` (split-only), `ultima_barra_ts`, `barra_viva: bool`, `idx_ultima_fechada`, `atraso_min`, `disponivel: bool`, `motivo`.
- **D-02:** O dataclass carrega **ambas** as séries — `ohlc` **nominal** (gráfico + níveis entrada/stop/alvo) e `ohlc_ajustado` **split-only** (consumido por `indicators.calcular()`). Reutiliza `prices._ajustar_por_split` (sem nova chamada de rede). Espelha o diário.
- **D-03:** Política **manter + marcar**: o frame inclui a barra viva, e o dataclass expõe `barra_viva` + `idx_ultima_fechada`. Fase 16 desenha a barra "em formação"; Fase 13 calcula **sempre** sobre a barra fechada (`iloc[-2]`).
- **D-04:** Detecção **conservadora**: a última barra é **sempre** tratada como potencialmente viva/suspeita — cálculos usam `iloc[-2]` por contrato. Determinístico, testável em golden e **imune ao TZ da VPS (UTC) e a feriados/leilão**. **NÃO** depende de relógio nem de calendário de pregão B3.
- **D-05:** Buscar o **máximo disponível por timeframe** (teto do Yahoo): 5m/30m ≈ 60d, 1h ≈ 730d, diário 5y. Indicadores inviáveis (ex.: MM200 em frame curto) caem para **"indisponível"** via o guard já existente em `indicators.calcular()`. `period × interval` exato **confirmado empiricamente** (ver §Standard Stack).
- **D-06:** A borda **nunca** retorna `None` nem levanta exceção: em qualquer falha retorna o dataclass com `disponivel=False`.
- **D-07:** O `motivo` é **categorizado** — conjunto fixo de causas (ex.: `fetch_falhou`, `sem_dados`, `historico_insuficiente`). Copy de UI fica **fora** da camada de dados.
- **D-08:** Cache intraday **isolado** com TTL curto (300s) + **nonce** no botão Atualizar; re-buscar `(ticker, timeframe)` invalida **só** aquele cache. **Nunca** `st.cache_data.clear()` global. Chave mínima: `(ticker, timeframe)` (+ nonce).

### Claude's Discretion

- Nomes exatos de módulo/dataclass/campos e a localização do arquivo (novo `ingest/intraday.py` vs. extensão de `ingest/prices.py`).
- `period × interval` concreto por timeframe (calibrar contra os limites reais do yfinance).
- Forma de expor as categorias de `motivo` (Enum vs. constantes string) e o escopo exato do nonce.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. Fora de escopo da fase (pertence a 13–16): detecção de pivôs, indicadores além do guard, padrões/checklist, `SetupSwing`/score, página Streamlit/gráfico.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | OHLCV intraday (1h/30m/5m) por timeframe via ingestão parametrizada **isolada** do pipeline diário (`auto_adjust=False` + split-adjust reusados; tz America/Sao_Paulo; sem perturbar fetch diário 5y nem cache da aba Analisar) | Empiricamente confirmado: `tk.history(period, interval, auto_adjust=False)` retorna OHLCV + `Stock Splits` + `Adj Close` para `.SA` em todos os timeframes; `_ajustar_por_split` reusável tal-qual; índice já vem tz-aware `America/Sao_Paulo`. Layer separada de `coletar_mercado`/`montar_empresa` (ver §Architecture). |
| DATA-02 | Usuário escolhe timeframe (diário + 1h/30m/5m); página avisa atraso (~15min) e limite de histórico; degrada indicadores inviáveis para "indisponível" sem quebrar | `atraso_min` derivável de `now(SP) − ultima_barra_ts` (~15min confirmado: última barra 11:35, relógio 11:50). Degradação já garantida por `indicators.calcular()` (guard de borda existente). Limites de histórico documentados em §Standard Stack. |
| DATA-03 | Botão "Atualizar" re-busca ticker/timeframe; cache TTL curto + invalidação **targetada** (não `.clear()` global) | Padrão `@st.cache_data(ttl=300)` com chave `(ticker, timeframe, nonce)`; nonce em `st.session_state` incrementado pelo botão (ver §Code Examples). |
</phase_requirements>

## Summary

A camada de ingestão intraday é uma **réplica paralela e parametrizada** do fetch de preços que já existe em `ingest/prices.py` — só muda `period`/`interval` e o empacotamento no dataclass `FrameOHLC`. As duas dúvidas MEDIUM-confidence do roadmap foram **resolvidas empiricamente contra a API ao vivo** (yfinance 1.4.1, ticker `PETR4.SA`, 2026-06-29):

1. **Limites period×interval (HIGH):** os tetos da Yahoo são exatamente os do roadmap. `5m` e `30m` (e `15m`) → **≤ 60 dias corridos**; `1h` → **≤ 730 dias corridos**; `1d` → 5y+ sem problema. **Exceder o teto NÃO clampa: retorna DataFrame vazio** (a Yahoo loga `"...must be within the last 60/730 days"`). Logo a implementação deve **cravar `period` no teto documentado**, nunca confiar em clamp. Usar strings explícitas (`"60d"`, `"730d"`), **não** `"max"` (que se mostrou inconsistente para intraday).

2. **Timezone (HIGH, melhor que o esperado):** o yfinance **já devolve o índice tz-aware em `America/Sao_Paulo`** (offset `-03:00`) para tickers `.SA`, e isso é **imune ao TZ do processo** — confirmado forçando `TZ=UTC` + `time.tzset()`. `idx.tz_convert("America/Sao_Paulo")` é **idempotente** no caso normal e serve como normalizador defensivo determinístico.

A barra viva é real e observável (última barra de 5m com `Volume=0` enquanto a anterior tinha 110.100), o que **valida a política conservadora D-04** (`iloc[-2]` sempre). O `Stock Splits` vem presente em todos os frames intraday, então `_ajustar_por_split` funciona sem alteração (frames sem split → cópia inalterada).

**Primary recommendation:** Criar `src/analista/ingest/intraday.py` com uma função `coletar_intraday(ticker, timeframe) -> FrameOHLC`, que (1) mapeia timeframe→(period, interval) por uma tabela cravada nos tetos, (2) reusa `yahoo_symbol` + o retry `_MAX_TENTATIVAS`/`_BACKOFF_SEG`, (3) chama `tk.history(period, interval, auto_adjust=False)`, (4) normaliza o índice via `tz_convert("America/Sao_Paulo")` defensivo, (5) deriva `ohlc_ajustado` com `prices._ajustar_por_split`, (6) preenche os metadados de barra viva de forma **clock-free** (`idx_ultima_fechada = len−2`), e (7) nunca levanta exceção (D-06/D-07). O cache vive em `app.py` como wrapper `@st.cache_data(ttl=300)` com nonce — fora da engine.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fetch OHLCV multi-TF da Yahoo | Engine — `ingest/intraday.py` (novo) | — | Espelha `ingest/prices.py`; é I/O + transformação pura, fora da UI |
| Split-adjust (nominal→ajustado) | Engine — `ingest/prices._ajustar_por_split` (reuso) | — | Função pura já golden-testada; não reimplementar |
| Normalização tz `America/Sao_Paulo` | Engine — `ingest/intraday.py` | — | Determinismo independe do TZ da VPS; pertence à borda de dados |
| Metadados de barra viva (`idx_ultima_fechada`, `barra_viva`) | Engine — `ingest/intraday.py` | — | Contrato clock-free consumido por Fases 13 (cálculo) e 16 (desenho) |
| `atraso_min` (delta relógio) | Engine — `ingest/intraday.py` (com `agora` injetável) | UI Fase 16 (exibe) | Informacional; isolado do contrato no-repaint para manter golden determinístico |
| Cache TTL + invalidação por nonce | UI thin — `app.py` (`@st.cache_data`) | — | `app.py` read-only é o único lugar com `st.cache_data`; engine não conhece Streamlit |
| Mensagem amigável de `motivo` | UI Fase 16 | — | Copy mapeada da categoria; **fora** da camada de dados (D-07) |
| Degradação de indicador (frame curto) | Engine — `core/indicators.calcular` (reuso) | — | Guard de borda já existe; Fase 12 não reimplementa |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | 1.4.1 (instalado; `requirements.txt` pede `>=0.2.40`) | Fetch OHLCV diário+intraday da Yahoo | Já é a fonte de preços do projeto (`prices.coletar_mercado`); custo zero `[VERIFIED: .venv/bin/python import]` |
| pandas | 3.0.3 | Manipulação de frame OHLCV, índice tz-aware, `iloc` | Já no stack; índice `DatetimeIndex` tz-aware é nativo `[VERIFIED]` |
| streamlit | 1.58.0 | `@st.cache_data(ttl=...)` + `st.session_state` para o nonce | Já no stack; padrão de cache existente em `app.py` `[VERIFIED]` |
| numpy | 2.4.6 | suporte ao split-adjust e cálculos | Já no stack `[VERIFIED]` |

**Zero novas dependências** (locked, STATE.md). Toda a fase é parametrização + empacotamento sobre o que já existe.

### Tabela period×interval (CRAVAR nos tetos — confirmada empiricamente)

| timeframe | `interval` | `period` recomendado | Teto Yahoo (HARD) | Barras obtidas (PETR4.SA, 2026-06-29) |
|-----------|-----------|----------------------|-------------------|----------------------------------------|
| diário | `"1d"` | `"5y"` | anos (sem aperto prático) | 1247 |
| 1h | `"1h"` | `"730d"` | **≤ 730 dias corridos** | 5090 |
| 30m | `"30m"` | `"60d"` | **≤ 60 dias corridos** | 830 |
| 5m | `"5m"` | `"60d"` | **≤ 60 dias corridos** | 4890 |

`[VERIFIED: tk.history() ao vivo contra PETR4.SA]` + `[CITED: mensagem de erro da Yahoo "The requested range must be within the last 60 days" / "last 730 days"]`

**Comportamento ao exceder o teto (CRÍTICO):** não clampa — retorna **DataFrame vazio** e a Yahoo loga `"$TICKER: possibly delisted; no price data found"`. Indistinguível de "sem dados". Por isso a tabela acima é a fonte da verdade; **não** tentar `period > teto`.

**Colunas retornadas (todos os timeframes, `auto_adjust=False`):** `['Open','High','Low','Close','Adj Close','Volume','Dividends','Stock Splits']` `[VERIFIED]`. → `_ajustar_por_split` funciona sem mudança.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `period="730d"`/`"60d"` explícito | `period="max"` | `"max"` retornou **menos** barras que `"60d"` para 5m em chamadas consecutivas (inconsistente). Não-determinístico → rejeitado. |
| Layer nova `coletar_intraday` p/ o diário também | Reusar `coletar_mercado` 5y | Reusar fere o isolamento (D-01/DATA-01) e mistura beta/dividendos. Recomendado: o diário do swing é um fetch próprio `("5y","1d")` empacotado no mesmo `FrameOHLC`. |
| `tz_convert` defensivo | Confiar que yfinance sempre devolve `America/Sao_Paulo` | Custo ~zero e protege contra índice naive/UTC em edge (download multi-símbolo, versões futuras). Manter. |

**Installation:** nenhuma — todas as libs já estão no `.venv` e no `requirements.txt`.

**Version verification:** `[VERIFIED]` via `.venv/bin/python -c "import yfinance; print(yfinance.__version__)"` → `1.4.1`; pandas `3.0.3`; streamlit `1.58.0`; numpy `2.4.6`; Python `3.14.5`.

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
  Usuário (Fase 16) │  app.py  (UI thin, read-only)            │
  escolhe TF /      │                                          │
  clica "Atualizar" │  st.session_state["nonce_intraday"] ++   │  ← botão Atualizar (DATA-03)
        │           │           │                              │
        ▼           │           ▼                              │
  ┌───────────────────────────────────────────────┐           │
  │ @st.cache_data(ttl=300)                         │           │
  │ frame_intraday(ticker, timeframe, nonce):       │  ← chave de cache = (ticker, timeframe, nonce)
  │     return intraday.coletar_intraday(...)       │     invalidação TARGETADA, nunca .clear() (D-08)
  └───────────────────────────────────────────────┘           │
        │                                          └───────────┘
        ▼   (NÃO toca em montar()/coletar_mercado — firewall)
  ┌──────────────────────────────────────────────────────────────┐
  │ ingest/intraday.py   coletar_intraday(ticker, timeframe)        │
  │                                                                 │
  │  timeframe ──► _PERIODO_POR_TF[timeframe] = (period, interval)  │
  │       │                                                         │
  │       ▼   yahoo_symbol(ticker)  +  retry (_MAX_TENTATIVAS)      │
  │  tk.history(period, interval, auto_adjust=False) ──► hist        │
  │       │                                                         │
  │       ├─ vazio/exceção ─► FrameOHLC(disponivel=False,           │
  │       │                            motivo="sem_dados"|"fetch_falhou")   (D-06/D-07)
  │       ▼                                                         │
  │  normaliza índice: tz_convert("America/Sao_Paulo")  (defensivo) │
  │       ▼                                                         │
  │  ohlc        = hist (nominal)                                   │
  │  ohlc_ajust. = prices._ajustar_por_split(hist)  (reuso, 0 rede) │
  │       ▼                                                         │
  │  metadados clock-free:                                          │
  │    ultima_barra_ts  = índice[-1]                                │
  │    idx_ultima_fechada = len-2  (None se len<2 ─► historico_insuf)│
  │    barra_viva = (len>=1)        (sempre suspeita — D-04)        │
  │    atraso_min = (agora - ultima_barra_ts)  [agora injetável]    │
  │       ▼                                                         │
  │  FrameOHLC(...)  disponivel=True                                │
  └──────────────────────────────────────────────────────────────┘
        │                                   │
        ▼ ohlc_ajustado                     ▼ ohlc nominal + metadados
   indicators.calcular()              gráfico candlestick (Fase 16)
   (Fase 13, sobre iloc[-2])          (desenha barra viva marcada)
```

### Recommended Project Structure

```
src/analista/ingest/
├── prices.py          # EXISTENTE — coletar_mercado (diário 5y), _ajustar_por_split, yahoo_symbol, retry
├── intraday.py        # NOVO — coletar_intraday() + FrameOHLC + _PERIODO_POR_TF + categorias de motivo
└── build.py           # EXISTENTE — montar_empresa (NÃO tocar; firewall com intraday)
```

### Pattern 1: Função de ingestão parametrizada espelhando `coletar_mercado`

**What:** Uma função pura-de-borda que recebe `(ticker, timeframe)`, faz o fetch com retry, e devolve o dataclass rico — nunca exceção.
**When to use:** ponto de entrada único da Fase 12, consumido pelo wrapper de cache em `app.py`.
**Example:**
```python
# Source: padrão derivado de prices.coletar_mercado (este repo) + probe empírico
# src/analista/ingest/intraday.py
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from . import prices  # reuso de yahoo_symbol, _ajustar_por_split, _MAX_TENTATIVAS, _BACKOFF_SEG, _yf

_TZ_B3 = "America/Sao_Paulo"

# CRAVADO nos tetos da Yahoo (confirmados empiricamente; exceder => frame vazio)
_PERIODO_POR_TF = {
    "diario": ("5y",   "1d"),
    "1h":     ("730d", "1h"),
    "30m":    ("60d",  "30m"),
    "5m":     ("60d",  "5m"),
}

# Categorias de motivo (D-07) — UI mapeia para copy amigável (Fase 16)
MOTIVO_OK = ""
MOTIVO_TF_INVALIDO = "timeframe_invalido"
MOTIVO_FETCH_FALHOU = "fetch_falhou"
MOTIVO_SEM_DADOS = "sem_dados"
MOTIVO_HIST_INSUF = "historico_insuficiente"

@dataclass
class FrameOHLC:
    timeframe: str
    ohlc: Optional["pd.DataFrame"] = None           # nominal (gráfico + níveis)
    ohlc_ajustado: Optional["pd.DataFrame"] = None  # split-only (indicators.calcular)
    ultima_barra_ts: Optional["pd.Timestamp"] = None
    barra_viva: bool = False
    idx_ultima_fechada: Optional[int] = None
    atraso_min: Optional[float] = None
    disponivel: bool = False
    motivo: str = MOTIVO_SEM_DADOS

def _normaliza_tz(df: "pd.DataFrame") -> "pd.DataFrame":
    """Índice -> America/Sao_Paulo, determinístico e imune ao TZ do processo (VPS=UTC).
    yfinance .SA já vem tz-aware America/Sao_Paulo; tz_convert é idempotente nesse caso."""
    idx = df.index
    if getattr(idx, "tz", None) is None:        # edge: índice naive -> assume UTC
        df.index = idx.tz_localize("UTC").tz_convert(_TZ_B3)
    else:
        df.index = idx.tz_convert(_TZ_B3)
    return df

def coletar_intraday(ticker: str, timeframe: str,
                     agora: Optional["pd.Timestamp"] = None) -> FrameOHLC:
    if timeframe not in _PERIODO_POR_TF:
        return FrameOHLC(timeframe=timeframe, disponivel=False, motivo=MOTIVO_TF_INVALIDO)
    period, interval = _PERIODO_POR_TF[timeframe]
    sym = prices.yahoo_symbol(ticker)
    yf = prices._yf()

    hist = None
    for tentativa in range(prices._MAX_TENTATIVAS):
        try:
            hist = yf.Ticker(sym).history(period=period, interval=interval, auto_adjust=False)
        except Exception:
            hist = None
        if hist is not None and not hist.empty:
            break
        if tentativa < prices._MAX_TENTATIVAS - 1:
            time.sleep(prices._BACKOFF_SEG[min(tentativa, len(prices._BACKOFF_SEG) - 1)])

    if hist is None:
        return FrameOHLC(timeframe=timeframe, disponivel=False, motivo=MOTIVO_FETCH_FALHOU)
    if hist.empty:
        return FrameOHLC(timeframe=timeframe, disponivel=False, motivo=MOTIVO_SEM_DADOS)

    hist = _normaliza_tz(hist)
    ohlc_aj = prices._ajustar_por_split(hist)

    n = len(hist)
    ultima_ts = hist.index[-1]
    idx_fechada = n - 2 if n >= 2 else None         # clock-free (D-04)
    if agora is None:
        agora = pd.Timestamp.now(tz=_TZ_B3)
    atraso = float((agora - ultima_ts).total_seconds() / 60.0)

    return FrameOHLC(
        timeframe=timeframe,
        ohlc=hist, ohlc_ajustado=ohlc_aj,
        ultima_barra_ts=ultima_ts,
        barra_viva=(n >= 1),                        # última barra SEMPRE suspeita
        idx_ultima_fechada=idx_fechada,
        atraso_min=atraso,
        disponivel=True,
        motivo=(MOTIVO_HIST_INSUF if idx_fechada is None else MOTIVO_OK),
    )
```

### Pattern 2: Cache targetado com nonce (em `app.py`, fora da engine)

**What:** wrapper `@st.cache_data(ttl=300)` cuja chave inclui um nonce de `session_state`; o botão Atualizar só incrementa o nonce daquele `(ticker, timeframe)`.
**When to use:** DATA-03. Mantém o cache da aba Analisar (`montar`, `selic_atual`) intacto — nunca `.clear()`.
**Example:**
```python
# Source: padrão @st.cache_data existente em app.py + docs Streamlit caching
# app.py (camada thin)
@st.cache_data(show_spinner=False, ttl=300)
def frame_intraday(ticker: str, timeframe: str, nonce: int):
    from analista.ingest import intraday
    return intraday.coletar_intraday(ticker, timeframe)   # nonce só entra na CHAVE de cache

def _nonce_key(ticker, timeframe):
    return f"nonce_intraday::{ticker}::{timeframe}"

# no corpo da página de swing:
k = _nonce_key(ticker, timeframe)
st.session_state.setdefault(k, 0)
if st.button("Atualizar"):
    st.session_state[k] += 1          # invalida SÓ este (ticker, timeframe)
frame = frame_intraday(ticker, timeframe, st.session_state[k])
```
Por que funciona: `st.cache_data` chaveia pela tupla de argumentos. Mudar só o `nonce` de um par `(ticker, timeframe)` cria uma nova entrada e a antiga expira pelo TTL — sem tocar nas demais entradas nem no cache de `montar()`. `[CITED: docs.streamlit.io/develop/concepts/architecture/caching]`

### Anti-Patterns to Avoid

- **`st.cache_data.clear()` global no botão Atualizar:** apagaria o cache da aba Analisar (`montar`, `selic_atual`, `rf_capm`) — viola D-08/DATA-03. Use nonce.
- **`period="max"` para intraday:** inconsistente (retornou menos barras que `"60d"`). Use a tabela cravada.
- **Confiar em clamp ao exceder o teto:** Yahoo retorna **frame vazio**, não clampa. Sempre usar `period` ≤ teto.
- **Detectar barra viva pelo relógio/calendário B3:** viola D-04 (não-determinístico, sensível a feriado/leilão/TZ). Use `idx_ultima_fechada = len−2` constante.
- **Usar `Adj Close` como base ajustada:** mistura proventos (anti-pattern já documentado em `_ajustar_por_split`). Os indicadores querem split-only.
- **Importar `streamlit` na engine (`ingest/intraday.py`):** o cache vive só em `app.py`; a engine permanece testável offline.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Conversão de timezone do índice | Cálculo manual de offset / `-3h` | `idx.tz_convert("America/Sao_Paulo")` | yfinance já entrega tz-aware; offset manual quebra no DST e no TZ da VPS |
| Ajuste por split intraday | Nova lógica de split | `prices._ajustar_por_split(hist)` (reuso) | Função pura golden-testada (incl. multi-split ITSA4); funciona idêntica em frames intraday |
| Resolução `.SA` | Concatenar sufixo | `prices.yahoo_symbol(ticker)` | Já trata casing/`.SA` duplicado |
| Retry de rate-limit | `try/except` novo | Padrão `_MAX_TENTATIVAS`/`_BACKOFF_SEG` de `prices.py` | Tolera o rate-limit intermitente do Yahoo já calibrado |
| Degradação de indicador em frame curto | Checagens de `len` na ingestão | `indicators.calcular()` guard (Fase 13) | O guard de borda já degrada MM200/ADX para "indisponivel" sem quebrar |
| Cache + invalidação | Dict manual / arquivo | `@st.cache_data(ttl=300)` + nonce | TTL e chaveamento por argumentos são nativos do Streamlit |

**Key insight:** A Fase 12 é ~90% **reuso e parametrização**. O único código genuinamente novo é a tabela `period×interval`, o normalizador de tz (3 linhas) e o cálculo clock-free dos metadados de barra viva. Tudo o mais já existe e está golden-testado.

## Common Pitfalls

### Pitfall 1: Exceder o teto retorna frame vazio (não erro, não clamp)
**What goes wrong:** pedir `5m`/`30m` com `period > 60d` ou `1h` com `period > 730d` devolve DataFrame vazio + log "possibly delisted".
**Why it happens:** a API da Yahoo rejeita o range e o yfinance trata como sem-dados.
**How to avoid:** cravar `period` na tabela `_PERIODO_POR_TF`. Nunca derivar `period` de input do usuário.
**Warning signs:** `disponivel=False, motivo="sem_dados"` para um ticker que claramente negocia.

### Pitfall 2: Tratar a última barra como fechada
**What goes wrong:** calcular sinais sobre `iloc[-1]` repinta a cada refresh (a barra viva muda OHLC dentro do mesmo intervalo).
**Why it happens:** a última barra intraday é a barra em formação — empiricamente vista com `Volume=0` enquanto a anterior tinha 110.100, e ~15min atrás do relógio.
**How to avoid:** contrato D-04 — `idx_ultima_fechada = len−2`, cálculos sempre sobre a barra fechada. Clock-free.
**Warning signs:** valores de indicador/score que oscilam a cada "Atualizar" sem barra nova.

### Pitfall 3: `atraso_min` quebra os golden tests
**What goes wrong:** `now()` no cálculo de `atraso_min` torna o dataclass não-determinístico → golden test flaky.
**Why it happens:** o delay depende do relógio.
**How to avoid:** parâmetro `agora` injetável (default `pd.Timestamp.now(tz=SP)`); o golden injeta um `agora` fixo. Mantém o **contrato no-repaint separado** da métrica informacional.
**Warning signs:** teste que passa local e falha no CI por diferença de minutos.

### Pitfall 4: Frame com < 2 barras
**What goes wrong:** `idx_ultima_fechada = len−2` vira índice negativo/inválido com 0–1 barra.
**Why it happens:** ticker novo, ilíquido, ou janela onde a Yahoo só tem 1 barra.
**How to avoid:** `idx_ultima_fechada = None` quando `len < 2` → `motivo = "historico_insuficiente"` (mas `disponivel=True` se há barras p/ o gráfico — decisão do planner).
**Warning signs:** `IndexError` na Fase 13 ao acessar `iloc[-2]`.

### Pitfall 5: Índice naive em edge (multi-símbolo / versão futura)
**What goes wrong:** `tz_convert` num índice naive levanta `TypeError`.
**Why it happens:** alguns caminhos do yfinance (download em lote) retornam índice naive UTC.
**How to avoid:** `_normaliza_tz` checa `idx.tz is None` → `tz_localize("UTC").tz_convert(SP)`.
**Warning signs:** `TypeError: Cannot convert tz-naive timestamps`.

## Code Examples

### Mapear timeframe → (period, interval) e fazer o fetch
Ver Pattern 1 acima (`coletar_intraday`). Os valores de `_PERIODO_POR_TF` são `[VERIFIED]` contra a API.

### Normalização de timezone determinística
```python
# Source: probe empírico (TZ=UTC + time.tzset() => índice continua America/Sao_Paulo)
idx = df.index
if getattr(idx, "tz", None) is None:
    df.index = idx.tz_localize("UTC").tz_convert("America/Sao_Paulo")
else:
    df.index = idx.tz_convert("America/Sao_Paulo")   # idempotente no caso .SA normal
```

### Testes offline (espelhar test_ingest_ohlc.py)
```python
# Source: padrão de monkeypatch de test_ingest_ohlc.py (este repo)
class _TkIntraday:
    def history(self, *a, **k):
        idx = pd.date_range("2026-06-29 10:00", periods=6, freq="5min",
                            tz="America/Sao_Paulo")
        close = pd.Series([10,11,12,13,14,15], index=idx, dtype=float)
        return pd.DataFrame({"Open": close-.1, "High": close+.2, "Low": close-.2,
                             "Close": close, "Adj Close": close*.9,
                             "Volume": [100,100,100,100,100,0],  # última barra viva (vol 0)
                             "Stock Splits": [0.0]*6, "Dividends": [0.0]*6}, index=idx)

def test_idx_ultima_fechada_clock_free(monkeypatch):
    monkeypatch.setattr(intraday.prices, "_yf",
                        lambda: type("YF", (), {"Ticker": staticmethod(lambda s: _TkIntraday())}))
    monkeypatch.setattr(intraday.time, "sleep", lambda *_: None)
    f = intraday.coletar_intraday("PETR4", "5m",
                                  agora=pd.Timestamp("2026-06-29 10:40", tz="America/Sao_Paulo"))
    assert f.disponivel and f.idx_ultima_fechada == len(f.ohlc) - 2
    assert f.atraso_min == pytest.approx(15.0)   # 10:40 - 10:25 (iloc[-1] = 10:25)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yfinance `0.2.x` (training-era) | `1.4.1` instalado | 2025 (versionamento 1.x) | API `Ticker.history(period, interval, auto_adjust=...)` estável; nenhum breaking observado no probe |
| Assumir índice naive/UTC | Índice tz-aware na timezone do exchange (`America/Sao_Paulo` p/ `.SA`) | yfinance moderno | Normalização vira `tz_convert` defensivo, não localização do zero |

**Deprecated/outdated:**
- Lógica manual de offset de -3h para B3: desnecessária e frágil (DST/TZ do processo). yfinance já resolve.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Tetos 60d/730d são iguais para **todos** os tickers `.SA` (não só PETR4) | Standard Stack | BAIXO — o limite é da API Yahoo por `interval`, não por ticker; mensagem de erro é genérica. Tickers ilíquidos podem ter menos barras dentro do mesmo teto (→ `historico_insuficiente`, já tratado). |
| A2 | O atraso ~15min vale para todos os `.SA` em pregão | DATA-02 | BAIXO — `atraso_min` é calculado, não hardcoded; o "~15min" é só copy de UI (Fase 16). |
| A3 | `motivo="historico_insuficiente"` deve ser reservado para `len<2`; frames curtos porém >2 barras ficam `disponivel=True` e degradam via `indicators` | Pattern 1 | MÉDIO — se o planner quiser um piso de barras maior (ex.: bloquear timeframe sem N barras), é decisão de produto. Recomendação: deixar o guard de `indicators` decidir, não a ingestão. |
| A4 | O diário do swing deve ser um fetch próprio `("5y","1d")`, não reuso de `coletar_mercado` | Alternatives | BAIXO — isolamento é requisito (DATA-01); custo é 1 fetch extra de rede (cacheado 300s). |

**Confirmação recomendada com o usuário/planner:** A3 (piso de barras por timeframe) e A4 (diário próprio vs. ponte read-only com o fetch existente) são as duas escolhas de produto que valem um aceno antes do plano.

## Open Questions

1. **Piso mínimo de barras por timeframe antes de marcar `historico_insuficiente`?**
   - What we know: `indicators.calcular()` já degrada indicador a indicador; `idx_ultima_fechada` exige ≥ 2 barras.
   - What's unclear: se o produto quer bloquear um timeframe inteiro abaixo de N barras (ex.: 5m de um ticker recém-listado).
   - Recommendation: NÃO bloquear na ingestão — `disponivel=True` sempre que houver ≥ 1 barra; deixar a degradação para `indicators` (Fase 13). Reservar `historico_insuficiente` para `len < 2`.

2. **Weekly (semanal) entra na Fase 12?**
   - What we know: escopo lista "diário + 1h/30m/5m"; TREND-02 (multi-TF semanal→diário) é Fase 13.
   - What's unclear: —
   - Recommendation: **não** fetchar weekly aqui; o semanal será `resample("W-FRI")` do diário na Fase 13 (alinhado ao padrão `base_temporal` já existente). Fora de escopo da Fase 12.

3. **Ticker ilíquido com buracos de pregão (barras faltando):**
   - What we know: frames vêm densos para líquidos; ilíquidos podem ter lacunas.
   - What's unclear: impacto em janelas de indicador (Fase 13), não na ingestão.
   - Recommendation: ingestão entrega o frame como veio (sem reindex/forward-fill — não inventar barras); golden test com fixture ilíquida cobre a edge.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| yfinance | fetch OHLCV | ✓ | 1.4.1 | — |
| pandas | frame/tz | ✓ | 3.0.3 | — |
| streamlit | cache (app.py) | ✓ | 1.58.0 | — |
| numpy | split-adjust | ✓ | 2.4.6 | — |
| Acesso de rede à Yahoo (`query*.finance.yahoo.com`) | fetch ao vivo | ✓ (probe ao vivo funcionou) | — | retry + `disponivel=False` (D-06); testes são 100% offline (monkeypatch) |

**Missing dependencies with no fallback:** nenhuma.
**Missing dependencies with fallback:** a rede Yahoo pode rate-limitar (intermitente, por IP de datacenter) — o retry `_MAX_TENTATIVAS`/`_BACKOFF_SEG` e o `disponivel=False` cobrem; os testes não dependem de rede.

## Validation Architecture (Test Strategy)

> `workflow.nyquist_validation` está **false** no `.planning/config.json` — a validação Nyquist formal está desligada. Esta seção é incluída a pedido explícito do briefing (golden + edges) e é **advisory**: o gate real são os **191 testes golden** verdes + novos testes offline da fase.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (config em `pyproject.toml`: `pythonpath=["src"]`, `testpaths=["tests"]`) |
| Quick run | `.venv/bin/python -m pytest tests/test_ingest_intraday.py -x -q` |
| Full suite | `.venv/bin/python -m pytest -q` (191 atuais → deve continuar 100% verde) |
| Net policy | **Offline obrigatório** — todos os testes via `monkeypatch` de `_yf`/`time.sleep` (padrão de `test_ingest_ohlc.py`/`test_ingest_resolucao.py`) |

### Phase Requirements → Test Map (novo `tests/test_ingest_intraday.py`)
| Req | Behavior | Test (offline) |
|-----|----------|----------------|
| DATA-01 | `_PERIODO_POR_TF` mapeia os 4 TFs; fetch usa `auto_adjust=False`; `ohlc_ajustado` derivado de `_ajustar_por_split` | `test_mapa_tf_period_interval`, `test_ohlc_ajustado_reusa_split` |
| DATA-01 | tz normalizada para `America/Sao_Paulo` mesmo com índice naive | `test_tz_normaliza_naive`, `test_tz_idempotente_sao_paulo` |
| DATA-02 | `atraso_min` com `agora` injetável (determinístico); barra viva = `iloc[-1]`, fechada = `iloc[-2]` | `test_idx_ultima_fechada_clock_free`, `test_atraso_min_injetavel` |
| DATA-02 | frame curto degrada sem quebrar (delega a `indicators`); `len<2` → `historico_insuficiente` | `test_frame_curto_historico_insuficiente`, `test_disponivel_true_frame_curto` |
| DATA-02/D-06 | fetch vazio/exceção → `disponivel=False` + `motivo` categorizado, nunca exceção | `test_vazio_sem_dados`, `test_excecao_fetch_falhou`, `test_tf_invalido` |
| DATA-03 | (em `app.py`/manual) nonce invalida só `(ticker, timeframe)`; `montar()`/cache da aba Analisar intactos | checkpoint humano no navegador (Fase 16) + revisão de que `app.py` não chama `.clear()` |

### Edges explícitas pedidas no briefing
- **Barra viva:** fixture com última barra `Volume=0` → `idx_ultima_fechada == len-2`, `barra_viva True`.
- **Matriz period×interval:** assert do dicionário `_PERIODO_POR_TF` (cravado nos tetos).
- **Timezone:** fixture naive UTC e fixture já-SP → ambas terminam em `America/Sao_Paulo`.
- **Barras ilíquidas:** fixture com 1 barra → `historico_insuficiente`; fixture com lacunas → entregue como veio (sem reindex).

### Gate invariante (STATE.md, blocker)
- [ ] `.venv/bin/python -m pytest -q` → **191 verdes** antes e depois (a engine fundamentalista, a aba Analisar e `coletar_mercado`/`montar_empresa` permanecem **intactos**).

## Security Domain

> `security_enforcement` ausente no `.planning/config.json`. Esta é uma camada de **leitura** de dados públicos de mercado (custo zero): **sem autenticação, sem secrets, sem PII, sem persistência, sem entrada não-confiável de terceiros**. A maioria das categorias ASVS é N/A.

### Applicable ASVS Categories
| ASVS | Applies | Standard Control |
|------|---------|------------------|
| V2 Authentication | no | sem auth nesta camada |
| V3 Session Management | no | sem sessão (Streamlit `session_state` só guarda o nonce, não credencial) |
| V4 Access Control | no | sem dados sensíveis |
| V5 Input Validation | **sim (leve)** | `ticker` é a única entrada; já normalizado por `yahoo_symbol` (upper/strip/`.SA`). Recomendado validar formato (`^[A-Z]{4}\d{1,2}$`) antes do fetch para evitar chamadas degeneradas. `timeframe` validado contra o conjunto fechado `_PERIODO_POR_TF`. |
| V6 Cryptography | no | sem cripto |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| DoS por auto-refresh / loop de fetch martelando a Yahoo | Denial of Service | Refresh **manual** + cache TTL 300s (DATA-03, já decidido); sem auto-refresh (out of scope explícito no REQUIREMENTS) |
| Rate-limit / IP ban do Yahoo | Availability | retry com backoff + `disponivel=False` (degradação graciosa, D-06) |
| Input de `ticker` degenerado (string arbitrária) | (baixo) Tampering | validação de formato + conjunto fechado de `timeframe`; falha → `motivo` categorizado, sem exceção |

Sem SSRF: o host (`finance.yahoo.com`) é fixo dentro do yfinance; o `ticker` não controla o domínio.

## Sources

### Primary (HIGH confidence)
- **Probe empírico ao vivo** (`PETR4.SA`, yfinance 1.4.1, 2026-06-29) — limites period×interval, timezone tz-aware `America/Sao_Paulo`, imunidade a `TZ=UTC`, colunas retornadas, barra viva `Volume=0`, atraso ~15min. `[VERIFIED]`
- **Mensagens de erro da API Yahoo** capturadas no probe: `"...must be within the last 60 days"` (5m/15m/30m) e `"...last 730 days"` (1h). `[CITED: Yahoo Finance API runtime error]`
- **Código do repo:** `src/analista/ingest/prices.py` (`_ajustar_por_split`, `coletar_mercado`, `yahoo_symbol`, retry), `src/analista/core/indicators.py` (guard de borda), `tests/test_ingest_ohlc.py` (padrão de fixture/monkeypatch), `app.py` (`@st.cache_data`). `[VERIFIED]`
- **Versões instaladas:** `.venv/bin/python` import — yfinance 1.4.1, pandas 3.0.3, streamlit 1.58.0, numpy 2.4.6, Python 3.14.5. `[VERIFIED]`

### Secondary (MEDIUM confidence)
- **Streamlit caching docs** — padrão `@st.cache_data(ttl=...)` + chaveamento por argumentos para invalidação targetada via nonce. `[CITED: docs.streamlit.io/develop/concepts/architecture/caching]`

### Tertiary (LOW confidence)
- Nenhuma — todos os pontos críticos foram verificados contra a API ao vivo ou o código do repo.

## Metadata

**Confidence breakdown:**
- Standard stack (limites period×interval, timezone): **HIGH** — confirmado contra a API ao vivo + mensagens de erro da própria Yahoo.
- Architecture (reuso de `_ajustar_por_split`/retry/yahoo_symbol, dataclass rico, cache+nonce): **HIGH** — espelha padrões existentes e golden-testados no repo.
- Pitfalls (barra vazia ao exceder teto, barra viva, atraso determinístico): **HIGH** — observados empiricamente.
- Cache nonce: **MEDIUM-HIGH** — padrão Streamlit consolidado; validação final é o checkpoint de navegador da Fase 16.

**Research date:** 2026-06-29
**Valid until:** ~2026-07-29 (yfinance/Yahoo é fast-moving; os tetos 60d/730d são estáveis há anos, mas re-confirmar o probe se a Yahoo mudar a política de intraday gratuito).
