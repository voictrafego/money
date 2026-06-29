# Phase 12: Ingestão Intraday + Timeframe - Pattern Map

**Mapped:** 2026-06-29
**Files analyzed:** 3 (1 novo módulo de engine, 1 modificação thin em UI, 1 novo arquivo de teste)
**Analogs found:** 3 / 3 (todos exact — a fase é ~90% reuso/parametrização)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/ingest/intraday.py` (NOVO) | service / ingest (engine de borda) | request-response (fetch rede) + transform (split-adjust, tz, metadados) | `src/analista/ingest/prices.py` | exact (mesma camada `ingest/`, mesmo fetch yfinance, mesmo dataclass rico) |
| `app.py` (MODIFICADO, thin) | config / UI cache wrapper | request-response + cache TTL | wrappers `montar`/`selic_atual`/`rf_capm` no próprio `app.py` (linhas 36-50) | exact (mesmo arquivo, mesmo decorator) |
| `tests/test_ingest_intraday.py` (NOVO) | test (offline) | event-driven (monkeypatch de `_yf`/`time.sleep`) | `tests/test_ingest_ohlc.py` | exact (mesmo tipo de módulo, mesma estratégia de fixture + monkeypatch) |

**Nota de arquitetura (Claude's Discretion D-01):** o dataclass `FrameOHLC`, a tabela `_PERIODO_POR_TF`
e as categorias de `motivo` vivem **dentro** de `intraday.py` (não em arquivo separado) — espelha
`prices.py`, que define `DadosMercado` no mesmo arquivo da função `coletar_mercado`. RESEARCH §"Recommended
Project Structure" confirma `intraday.py` como módulo único novo.

---

## Pattern Assignments

### `src/analista/ingest/intraday.py` (service / ingest, request-response + transform)

**Analog:** `src/analista/ingest/prices.py`

**Imports pattern** — copiar o cabeçalho de `prices.py` linhas 10-29 (import tardio de yfinance,
`dataclass`/`field`, retry consts) e **importar o próprio `prices` como módulo** para reusar `yahoo_symbol`,
`_ajustar_por_split`, `_yf`, `_MAX_TENTATIVAS`, `_BACKOFF_SEG` sem reimplementar:
```python
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Optional
from . import prices  # reuso de yahoo_symbol, _ajustar_por_split, _yf, _MAX_TENTATIVAS, _BACKOFF_SEG
```
> `prices.py:10-14` usa `from __future__ import annotations` + `import time` + `from dataclasses import dataclass, field`. Mantenha o mesmo estilo.

**Dataclass rico (D-01/D-02)** — molde direto de `DadosMercado` (`prices.py:45-60`): campos com
`Optional[...]` e defaults, anotação de tipo pandas em string (`"pd.DataFrame"`) para evitar import
pesado no topo, comentários inline explicando cada campo:
```python
# prices.py:45-60 — molde a espelhar
@dataclass
class DadosMercado:
    ticker: str
    preco_atual: Optional[float] = None
    ...
    ohlc: Optional["pd.DataFrame"] = None           # frame OHLCV nominal 5a (Yahoo cru, auto_adjust=False)
    ohlc_ajustado: Optional["pd.DataFrame"] = None  # OHLCV split-only-adjusted p/ indicadores (Phase 5)
```
Novo `FrameOHLC` segue exatamente esse padrão (campos exatos em RESEARCH Pattern 1, linhas 196-206).

**Retry yfinance (D-06)** — copiar o laço de retry de `coletar_mercado` (`prices.py:120-132`),
adaptando a condição de sucesso de "tem nome/preço" para "frame não-vazio":
```python
# prices.py:121-132 — molde do laço de retry com backoff
for tentativa in range(_MAX_TENTATIVAS):
    try:
        info = _fetch_info(tk)
    except Exception:
        info = {}
    ...
    if tem_nome or tem_preco:
        break
    if tentativa < _MAX_TENTATIVAS - 1:
        time.sleep(_BACKOFF_SEG[min(tentativa, len(_BACKOFF_SEG) - 1)])
```
No `intraday.py` a condição de break vira `hist is not None and not hist.empty` (ver RESEARCH Pattern 1
linhas 227-235). Reusar `prices._MAX_TENTATIVAS` / `prices._BACKOFF_SEG` / `prices.time.sleep` — **não**
redefinir as constantes (o teste monkeypatcha `intraday.time.sleep` via o `import time` local).

**Fetch com `auto_adjust=False` + reuso de split-adjust (D-02)** — molde de `coletar_mercado`
(`prices.py:145-155`):
```python
# prices.py:146-155
hist = tk.history(period="5y", auto_adjust=False)   # auto_adjust=False => Close NOMINAL + Adj Close + Stock Splits
...
dm.ohlc = hist                               # frame nominal completo (nada descartado)
dm.ohlc_ajustado = _ajustar_por_split(hist)  # split-only-adjusted (D-03/D-05)
```
No `intraday.py`: `tk.history(period=period, interval=interval, auto_adjust=False)` (period/interval da
tabela `_PERIODO_POR_TF`) e `ohlc_ajustado = prices._ajustar_por_split(hist)` — **reuso direto da função
pura golden-testada** (ver `_ajustar_por_split` em `prices.py:70-110`; não reimplementar — "Don't Hand-Roll").

**Resolução de símbolo** — `sym = prices.yahoo_symbol(ticker)` (`prices.py:40-42`, trata casing/`.SA` duplicado).

**Guard de borda / nunca exceção (D-06/D-07)** — espelha o guard de `indicators.calcular`
(`indicators.py:415-416`) e o tratamento `try/except → None` de `coletar_mercado` (`prices.py:145-148`).
A função **retorna sempre o dataclass** com `disponivel=False` + `motivo` categorizado, nunca `None`/exceção.
Categorias de `motivo` como constantes string a nível de módulo (RESEARCH Pattern 1 linhas 190-194).

**Normalizador de tz (código genuinamente novo, 3 linhas)** — não há analog; seguir RESEARCH §"Normalização
de timezone determinística" (linhas 349-356): `tz_convert("America/Sao_Paulo")` defensivo, com fallback
`tz_localize("UTC")` para índice naive.

**Metadados clock-free de barra viva (código novo, D-04)** — `idx_ultima_fechada = len-2` (None se `len<2`),
`barra_viva = (n>=1)`, `atraso_min` com parâmetro `agora` injetável (default `pd.Timestamp.now(tz=...)`).
Sem analog direto; especificado em RESEARCH Pattern 1 linhas 245-261. Pitfall 3 (linhas 325-329): `agora`
injetável é **obrigatório** para os golden tests serem determinísticos.

---

### `app.py` (config / UI cache wrapper, request-response + cache) — MODIFICAÇÃO THIN

**Analog:** wrappers de cache existentes no próprio `app.py` (linhas 36-50)

**Cache TTL pattern (D-08/DATA-03)** — copiar a forma dos wrappers existentes, mudando só o `ttl` para 300
e adicionando o `nonce` como argumento (que entra só na CHAVE de cache):
```python
# app.py:36-50 — molde dos wrappers de cache
@st.cache_data(show_spinner=False, ttl=3600)
def montar(ticker: str, ano_base: int, n: int):
    return build.montar_empresa(ticker, ano_base, n)

@st.cache_data(show_spinner=False, ttl=3600)
def selic_atual():
    return macro.selic_meta() or 0.105
```
Novo wrapper (RESEARCH Pattern 2 linhas 272-285): `@st.cache_data(show_spinner=False, ttl=300)` chamando
`intraday.coletar_intraday(ticker, timeframe)` com `nonce` na assinatura. Import tardio do módulo dentro
da função (espelha como `app.py` já isola imports pesados).

**Nonce via session_state** — `app.py` já usa `st.session_state.setdefault(...)` (ex.: linha 178
`st.session_state.setdefault("tec_estado", grafico.estado_padrao())`) e `st.button(...)` (linhas 409, 465).
Reusar exatamente esse idioma: `setdefault(nonce_key, 0)` + `if st.button("Atualizar"): st.session_state[k] += 1`.

**ANTI-PATTERN travado:** **NUNCA** `st.cache_data.clear()` (apagaria o cache de `montar`/`selic_atual`/`rf_capm`
da aba Analisar — viola D-08). RESEARCH §"Anti-Patterns" linha 291. `app.py` permanece read-only quanto à engine.

---

### `tests/test_ingest_intraday.py` (test, offline/monkeypatch) — NOVO

**Analog:** `tests/test_ingest_ohlc.py`

**Docstring + import pattern** (linhas 1-12): docstring declarando "offline, zero rede", imports
`numpy`/`pandas`/`pytest` + `from analista.ingest import ...`.

**Fixtures de hist OHLCV** — molde de `_hist_com_split()` / `_hist_sem_split()` (linhas 19-58): constrói
`pd.DataFrame` com colunas `Open/High/Low/Close/Adj Close/Volume/Stock Splits/Dividends` sobre um
`pd.date_range`. Para intraday, usar `freq="5min"` + `tz="America/Sao_Paulo"` e última barra com `Volume=0`
(barra viva — RESEARCH §"Testes offline" linhas 361-369).

**Monkeypatch de yfinance + time.sleep** — copiar `_monkeypatch_yf` (linhas 154-162):
```python
# test_ingest_ohlc.py:154-162 — molde exato do monkeypatch offline
def _monkeypatch_yf(monkeypatch, tk_cls):
    class _YF:
        @staticmethod
        def Ticker(sym):
            return tk_cls()
    monkeypatch.setattr(prices, "_yf", lambda: _YF())
    monkeypatch.setattr(prices.time, "sleep", lambda *_: None)
    monkeypatch.setattr(prices, "_fetch_info", lambda tk: {})
```
Para `intraday`, patchar `intraday.prices._yf` e `intraday.time.sleep` (RESEARCH linhas 371-378). Classe-fake
`_TkIntraday` com método `.history(*a, **k)` espelha `_TkComOHLC`/`_TkVazio` (linhas 136-152).

**Estrutura de teste por requisito** — espelhar o estilo de um teste = uma asserção de comportamento, com
docstring explicando o "porquê" (linhas 65-129). Mapa Req→Test em RESEARCH §"Phase Requirements → Test Map"
(linhas 444-452). Cobertura mínima: `test_mapa_tf_period_interval`, `test_ohlc_ajustado_reusa_split`,
`test_tz_normaliza_naive`, `test_tz_idempotente_sao_paulo`, `test_idx_ultima_fechada_clock_free`,
`test_atraso_min_injetavel`, `test_frame_curto_historico_insuficiente`, `test_vazio_sem_dados`,
`test_excecao_fetch_falhou`, `test_tf_invalido`.

---

## Shared Patterns

### Reuso de funções puras de `prices.py` (split-adjust, símbolo, retry)
**Source:** `src/analista/ingest/prices.py`
**Apply to:** `intraday.py` (via `from . import prices`)
- `prices._ajustar_por_split(hist)` (linhas 70-110) — split-only, função pura, sem rede, golden-testada (incl. multi-split ITSA4). **Reusar tal-qual.**
- `prices.yahoo_symbol(ticker)` (linhas 40-42) — resolução `.SA`.
- `prices._yf()` (linhas 27-29) — import tardio de yfinance (mockável).
- `prices._MAX_TENTATIVAS` / `prices._BACKOFF_SEG` (linhas 23-24) — retry calibrado.

### Guard de borda "indisponível" / nunca exceção
**Source:** `src/analista/core/indicators.py:415-416` + `src/analista/ingest/prices.py:145-148`
**Apply to:** `intraday.coletar_intraday` (borda nunca levanta — D-06)
```python
# indicators.py:415-416 — guard que substitui frame inválido por vazio e degrada
if ohlc is None or len(ohlc) == 0 or not set(_COLUNAS_OHLC).issubset(ohlc.columns):
    ohlc = pd.DataFrame({c: pd.Series(dtype=float) for c in _COLUNAS_OHLC})
```
`indicators.calcular()` já degrada indicadores inviáveis (MM200/ADX em frame curto) para `"indisponivel"`
sem quebrar (ver os blocos em `indicators.py:132-133, 204-205, 340-341, 371-372`). **A Fase 12 NÃO reimplementa
essa degradação** — entrega o frame e deixa o guard da Fase 13 decidir.

### Cache `@st.cache_data(ttl=...)` sem `.clear()` global
**Source:** `app.py:30-50`
**Apply to:** o novo wrapper de cache intraday em `app.py`
```python
# app.py:36-38 — molde do wrapper de cache
@st.cache_data(show_spinner=False, ttl=3600)
def montar(ticker: str, ano_base: int, n: int):
    return build.montar_empresa(ticker, ano_base, n)
```
Invalidação targetada via nonce em `session_state` (chave `(ticker, timeframe, nonce)`). Nunca `.clear()`.

### Isolamento (firewall) do pipeline fundamentalista
**Source:** `src/analista/ingest/build.py` (`montar_empresa`) — NÃO TOCAR
**Apply to:** toda a Fase 12 — `intraday.py` é paralelo a `coletar_mercado`/`montar_empresa`; o fetch diário
5y da aba Analisar e seu cache permanecem intactos. Gate: 191 testes golden verdes antes e depois.

---

## No Analog Found

Trechos genuinamente novos (sem analog no código; usar RESEARCH como fonte):

| Trecho | Onde | Reason | Fonte |
|--------|------|--------|-------|
| `_normaliza_tz` (tz_convert defensivo) | `intraday.py` | Nenhum módulo do repo faz normalização tz de índice (o diário não precisava) | RESEARCH §"Normalização de timezone" linhas 349-356 + Pitfall 5 |
| Metadados clock-free de barra viva (`idx_ultima_fechada=len-2`, `barra_viva`, `atraso_min` injetável) | `intraday.py` | Conceito de "barra viva"/no-repaint é novo no milestone v1.4 | RESEARCH Pattern 1 linhas 245-261 + Pitfalls 2-4 |
| Tabela `_PERIODO_POR_TF` (cravada nos tetos Yahoo) | `intraday.py` | Parametrização period×interval inexistente no fetch diário fixo `"5y"` | RESEARCH §"Tabela period×interval" linhas 80-91 `[VERIFIED]` |
| Nonce + botão "Atualizar" | `app.py` | `app.py` usa `session_state` para `tec_estado`, mas não para invalidação de cache | RESEARCH Pattern 2 linhas 264-287 |

## Metadata

**Analog search scope:** `src/analista/ingest/` (prices.py, build.py), `src/analista/core/indicators.py`, `app.py`, `tests/test_ingest_ohlc.py`
**Files scanned:** 5 (prices.py 199 linhas lido integral; indicators.py via grep+leitura targetada do guard 406-425 e cabeçalho 1-80; app.py cabeçalho 1-55 + grep de cache_data; test_ingest_ohlc.py 301 linhas lido integral)
**Pattern extraction date:** 2026-06-29
