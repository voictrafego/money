# Phase 18: Home — Watchlist + Notícias - Pattern Map

**Mapped:** 2026-07-01
**Files analyzed:** 3 (1 novo + 2 modificados)
**Analogs found:** 3 / 3 (todos com analogia forte no próprio codebase)

Fase puramente aditiva de UI. Toda a arquitetura já existe no codebase e deve ser **reusada literalmente** (não reinventada): fetch Yahoo (`prices.py`), degradação graciosa/TZ (`intraday.py`), `@st.cache_data(ttl=)`, `@st.fragment(run_every=)`, radio dispatcher, `st.metric(delta=)`, selo de atraso, ponte `localStorage`. O trabalho real é **cablagem fina + o cache process-global (D-05)**.

## File Classification

| Novo/Modificado | Role | Data Flow | Closest Analog | Match Quality |
|-----------------|------|-----------|----------------|---------------|
| `src/analista/core/home_feed.py` | service / data-module (read-only) | request-response + transform (fetch Yahoo em lote + parse RSS) | `src/analista/ingest/prices.py` (`coletar_mercado`) + `src/analista/ingest/intraday.py` (`FrameOHLC` never-raises) | role-match (fetch Yahoo idêntico; RSS é novo mas o contrato never-raise é o mesmo) |
| `app.py` (bloco Home + roteamento) | controller / view (camada fina) | request-response + polling | `app.py:912-1203` (fragment Swing), `app.py:377` (radio), `app.py:35-68` (cache), `app.py:334-358` (bridge localStorage) | exact (mesmos padrões, mesmo arquivo) |
| `requirements.txt` | config | — | bloco de deps existente (`streamlit>=1.30`, `yfinance>=0.2.40`) | exact |

---

## Pattern Assignments

### `src/analista/core/home_feed.py` (service / data-module read-only)

**Analog primário (fetch Yahoo + degradação):** `src/analista/ingest/prices.py`
**Analog secundário (contrato never-raise + TZ):** `src/analista/ingest/intraday.py`

> Firewall D-06: este módulo **NÃO** importa `report`/`build`/`indicators`/`multiples`/`screening`. Só reusa `prices` (import tardio) e `feedparser`. Nunca levanta exceção — degrada por item (padrão `FrameOHLC(disponivel=False)`).

**Reuso obrigatório de `prices` — resolução `.SA` + import tardio do yfinance** (`prices.py:27-42`):
```python
def _yf():
    import yfinance as yf  # import tardio: dependência pesada
    return yf

def yahoo_symbol(ticker: str) -> str:
    t = ticker.upper().strip()
    return t if t.endswith(".SA") else f"{t}.SA"
```
→ Em `home_feed.cotacoes`, fazer `from ..ingest import prices` (import tardio) e `syms = [prices.yahoo_symbol(t) for t in tickers]`. NÃO reescrever `.SA`.

**Padrão de fetch Yahoo tolerante a falha — retry calibrado + try/except que nunca estoura** (`prices.py:20-24, 113-148`):
```python
_MAX_TENTATIVAS = 3           # reusar prices._MAX_TENTATIVAS
_BACKOFF_SEG = (0.5, 1.0)     # reusar prices._BACKOFF_SEG
# ...
try:
    hist = tk.history(period="5y", auto_adjust=False)
except Exception:
    hist = None
if hist is not None and not hist.empty:
    ...
```
→ Para a watchlist, trocar a chamada por-ticker por **UMA** chamada em lote `yf.download(" ".join(syms), period="5d", interval="1d", group_by="ticker", auto_adjust=False, progress=False, threads=True)` (anti-429; ver anti-pattern "1 chamada por ticker num loop" no RESEARCH). Variação do dia = `close[-1]/close[-2]-1` sobre barras diárias (robusto a fim de semana; Pitfall 2). Cada ticker em `try/except` próprio → item degrada para `{"ok": False, "preco": None, "pct": None}` sem derrubar a lista (espelha `coletar_mercado`, que segue com `info={}` ao esgotar tentativas, `prices.py:132`).

**Contrato "nunca levanta exceção / nunca None" + `motivo` categorizado** (`intraday.py:8-14, 76-81`):
```python
# coletar_intraday(...) NUNCA levanta exceção nem devolve None:
# qualquer falha/vazio retorna FrameOHLC(disponivel=False) com motivo categorizado.
if timeframe not in _PERIODO_POR_TF:
    return FrameOHLC(timeframe=timeframe, disponivel=False, motivo=MOTIVO_TF_INVALIDO)
```
→ `home_feed.cotacoes` e `home_feed.noticias` seguem o mesmo contrato: retornam sempre `list[dict]` (vazia se tudo falhar), nunca `raise`. Feed que cai é pulado por `try/except` por feed (Pitfall 3).

**Normalização de timezone para as notícias** (`intraday.py:27, 61-73`):
```python
_TZ_B3 = "America/Sao_Paulo"
def _normaliza_tz(df):
    idx = df.index
    if getattr(idx, "tz", None) is None:
        df.index = idx.tz_localize("UTC").tz_convert(_TZ_B3)
    else:
        df.index = idx.tz_convert(_TZ_B3)
    return df
```
→ `pubDate` do RSS vem em UTC (RFC-822). Reusar a MESMA constante/lógica: `feedparser` dá `published_parsed` (UTC struct_time) → `datetime(*ts[:6], tzinfo=timezone.utc).astimezone(ZoneInfo("America/Sao_Paulo"))` (Pitfall 6). Não exibir hora crua.

**RSS parse (novo — sem analog no codebase, seguir RESEARCH §Code Examples):** `feedparser.parse(url, agent="Mozilla/5.0 ...")` por feed, User-Agent de browser (Pitfall 3), `try/except` por feed, dedupe por título normalizado, sort por data desc. Título/resumo/link tratados como **untrusted** (V5/V7 — validar `link.startswith("https://")`).

---

### `app.py` — bloco Home + roteamento (controller / view fina)

**Analog:** o próprio `app.py` (padrões do Swing/Analisar). Cinco excertos a espelhar:

**1. Roteamento do radio — prepend "🏠 Início" vira default (index 0)** (`app.py:377-382`):
```python
modo = st.sidebar.radio(
    "O que você quer fazer?",
    ["🔎 Analisar uma ação", "⛏️ Garimpar carteira (BSD)", "📊 Ranking por múltiplos",
     "📈 Swing trade (análise técnica)"],
    help=h("menu"),
)
```
→ Prepender `"🏠 Início"` como **1º item** da lista. O radio é **stateless (sem `key=`)** → o 1º item vira default automaticamente, sem `index=` e sem migração de estado (RESEARCH Pattern 1 / gotcha). Adicionar branch ADITIVO **antes** de `if modo.startswith("🔎")` (`app.py:400`):
```python
if modo.startswith("🏠"):
    render_home()   # camada fina; os 4 branches existentes ficam IDÊNTICOS
```
> Decisão do plano: `st.title`/`st.caption` (`app.py:373-375`) e a sidebar de Selic/aviso (`app.py:384-394`) hoje rodam **sempre** (globais) — manter global é aceitável; não movê-los para dentro dos branches sem necessidade.

**2. `@st.cache_data(ttl=)` wrapper process-global — D-05, o item mais crítico** (`app.py:58-68`):
```python
@st.cache_data(show_spinner=False, ttl=300)
def frame_intraday(ticker: str, timeframe: str, nonce: int):
    from analista.ingest import intraday  # import tardio: isola o módulo
    return intraday.coletar_intraday(ticker, timeframe)
```
→ Criar dois wrappers idênticos em estrutura no `app.py`:
```python
@st.cache_data(show_spinner=False, ttl=45)      # cotações ~30–60s
def _cotacoes(tickers: tuple[str, ...]):
    from analista.core import home_feed
    return home_feed.cotacoes(tickers)

@st.cache_data(show_spinner=False, ttl=600)     # RSS ~5–15min
def _noticias():
    from analista.core import home_feed
    return home_feed.noticias()
```
> Chave do cache DEVE ser hashável → passar `tuple(sorted(tickers))`, **nunca `list`** (anti-pattern do RESEARCH; idêntico ao contrato de `frame_intraday(ticker, tf, nonce)`). Nunca `st.cache_data.clear()` global (apagaria `montar`/`selic_atual`/`rf_capm`, `app.py:41-55`).

**3. `@st.fragment(run_every=)` auto-refresh escopado** (`app.py:912-915` + invocação `app.py:1203`):
```python
@st.fragment(run_every=run_every)   # int seg | None(desliga)
def _render_swing():
    with st.spinner(...):
        f = frame_intraday(ticker, tf_key, st.session_state[k])
    ...
# ao final do branch:
_render_swing()
```
→ Dois fragmentos independentes na Home, cada um chamando seu wrapper cacheado:
```python
@st.fragment(run_every=45)          # watchlist ~30–60s
def _render_watchlist(): ...        # chama _cotacoes(tuple(sorted(tickers)))
@st.fragment(run_every=600)         # notícias ~5–15min
def _render_noticias(): ...         # chama _noticias()
```
> Regra `run_every ≈ TTL` (45s/45s, 600s/600s — Pitfall 1). Gotchas (`app.py:884-887`): controles que disparam rerun (editor de tickers, toggle pausar) ficam **FORA** do fragment de propósito — mexer num widget fora re-decora o fragment. `run_every=None` desliga (útil p/ toggle pausar).

**4. Preço + variação colorida via `st.metric(delta=)`** (`app.py:446-453`):
```python
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Preço atual", esc_md(fmt_rs(a.preco_atual)), help=h("preco"))
m3.metric(hdr["label"], hdr["value"], delta=hdr["delta"], delta_color="off", help=...)
```
→ Na watchlist usar `delta_color` DEFAULT ("normal") para colorir automaticamente: `st.metric(label=ticker, value=fmt_rs(preco), delta=f"{pct*100:+.2f}%")` → `+` verde / `−` vermelho. Reusar `fmt_rs`/`fmt_pct`/`esc_md` já existentes (`app.py:82-97`); `esc_md` evita quebra de layout por `$` (Pitfall 8). Item inválido → `st.metric(ticker, "—")`. "Flash" na mudança de preço: **deferir** (a cor do delta já entrega o essencial — RESEARCH Q4).

**5. Selo de atraso ~15min sempre visível** (`app.py:1126-1128`):
```python
# Selo de atraso SEMPRE visível: honestidade sobre o best-effort.
atraso = f" · última barra {f.ultima_barra_ts:%H:%M}" if f.ultima_barra_ts is not None else ""
st.caption(f"⏱️ ~15min de atraso (best-effort){atraso}.")
```
→ Espelhar na watchlist: `st.caption("⏱️ ~15min de atraso (best-effort).")`. Não passar sensação de tempo-real (D-04).

**6. Ponte `localStorage` (Python→JS, best-effort) — base para a persistência da watchlist** (`app.py:334-358`):
```python
const RANGE_KEY = {range_key_json};
try {
  const saved = window.localStorage.getItem(RANGE_KEY);
  if (saved) { chart.timeScale().setVisibleLogicalRange(JSON.parse(saved)); }
  else { chart.timeScale().fitContent(); }
} catch (e) { chart.timeScale().fitContent(); }   // SecurityError não impede render
chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
  try { window.localStorage.setItem(RANGE_KEY, JSON.stringify(range)); }
  catch (e) { console.log('[lwc] localStorage indisponível'); }
});
```
→ Lição a herdar (LWC-03): **cada acesso a `localStorage` em `try/catch` INDEPENDENTE**; a página SEMPRE renderiza mesmo se o storage lançar `SecurityError` (iframe sandbox / aba anônima — Pitfall 4). **Limitação:** esta ponte é **só de escrita** (Python→JS). A watchlist precisa **ler de volta** para o Python (saber quais tickers buscar) → usar `streamlit-local-storage` (bidirecional) **com fallback `st.session_state`** semeado pelos 5 defaults. Namespace próprio `"watchlist_v18"` (Pitfall 7 — não colidir com a chave do gráfico). Fonte de verdade em runtime = `st.session_state`; escrever no localStorage a cada mudança; ler só no load inicial (Pitfall 5).

---

### `requirements.txt` (config)

**Analog:** bloco de deps existente:
```
yfinance>=0.2.40
...
streamlit>=1.30
plotly>=6.0
```
→ Adicionar (versões pinadas, verificadas no RESEARCH):
```
feedparser==6.0.12
streamlit-local-storage==0.0.25   # (ou omitir se optar pela bridge dep-free)
```
> Convenção do arquivo: deps de runtime usam `>=` (faixa), mas as duas novas o RESEARCH recomenda **pinar exato** (single-maintainer / feed volátil). Validar `streamlit-local-storage 0.0.25` contra `streamlit 1.58` no início do plano (A2 — MEDIUM); fallback `session_state` cobre se falhar.

---

## Shared Patterns

### Degradação graciosa (never-raise) — aplicar a TODO fetch da Home
**Source:** `src/analista/ingest/intraday.py:8-14` (contrato) + `src/analista/ingest/prices.py:145-148` (try/except silencioso)
**Apply to:** `home_feed.cotacoes`, `home_feed.noticias`, e os dois fragments do `app.py`.
Nenhuma função de dados levanta exceção; falha vira estado (`ok=False` / feed pulado / item "—"). Ticker inválido, feed fora do ar ou Yahoo 429 degradam **por item**, nunca derrubam a página (D-02/NEWS-02).

### Cache process-global (1 chamada externa por TTL) — D-05
**Source:** `app.py:58-68` (`frame_intraday`)
**Apply to:** os wrappers `_cotacoes` (ttl≈45) e `_noticias` (ttl≈600).
Memoização por processo, compartilhada entre TODAS as sessões → N usuários fazendo polling ainda produzem 1 chamada por ticker-set/feed por TTL. Chave hashável (`tuple`, nunca `list`). Nunca `clear()` global.

### Formatação e escaping de valores R$/% — evita quebra de markdown
**Source:** `app.py:82-97` (`fmt_pct`, `fmt_rs`, `esc_md`)
**Apply to:** todo render de preço/variação na watchlist.
Reusar as funções existentes; `esc_md()` em qualquer `R$` dentro de markdown/metric (Pitfall 8 — LaTeX).

### Import tardio para isolar dependência pesada / módulo
**Source:** `prices.py:27-29` (`_yf`), `app.py:66` (import de `intraday` dentro do wrapper)
**Apply to:** `home_feed` importa `prices` e `feedparser` tardiamente; wrappers do `app.py` importam `home_feed` dentro da função cacheada.

### Output encoding seguro (RSS untrusted) — V5/V7
**Source:** RESEARCH §Security (sem analog de RSS no codebase; padrão Streamlit)
**Apply to:** render de cada notícia.
`st.markdown(f"**{titulo}**")` (HTML escapado por default — nunca `unsafe_allow_html`/`components.html` com conteúdo do feed), `st.link_button("Abrir no site ↗", link)` só se `link.startswith("https://")` (nova aba segura, sem tabnabbing). Ticker do usuário validado por `^[A-Z0-9]{4,6}$` antes de `yahoo_symbol()`.

---

## No Analog Found

| Aspecto | Role | Data Flow | Motivo |
|---------|------|-----------|--------|
| Parse de RSS (`feedparser`) | data-module | transform | Não existe consumo de RSS no codebase — seguir RESEARCH §Code Examples (feeds InfoMoney + Google News, UA de browser, dedupe/sort/TZ). Contrato never-raise herda de `intraday.py`. |
| Leitura bidirecional de `localStorage` no Python | client-bridge | request-response | A ponte atual (`app.py:334-358`) é só escrita. `streamlit-local-storage` preenche a lacuna; fallback `session_state` herda a robustez try/catch do LWC-03. |

---

## Metadata

**Analog search scope:** `app.py`, `src/analista/ingest/` (prices.py, intraday.py), `requirements.txt`
**Files scanned:** 4 (app.py 1203 linhas — lidos ranges não sobrepostos; prices.py integral; intraday.py cabeçalho+contrato; requirements.txt)
**Pattern extraction date:** 2026-07-01
</content>
</invoke>
