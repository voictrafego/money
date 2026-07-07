# Phase 18: Home — Watchlist + Notícias - Research

**Researched:** 2026-07-01
**Domain:** Streamlit UI (landing page) + agregação read-only de cotações (yfinance) e RSS (feedparser) — custo-zero
**Confidence:** HIGH (padrões do próprio código verificados; feeds RSS testados ao vivo hoje; versões confirmadas no PyPI e no venv)

## Summary

Esta fase adiciona uma **página inicial (landing default)** ao app Streamlit com dois blocos independentes: uma **watchlist** (~5 tickers, preço + variação do dia, auto-refresh ~30–60s, persistida em `localStorage`) e um **feed de notícias** RSS (manchete + submanchete + fonte + hora, link para o site original, auto-refresh ~5–15min). É uma fase **puramente aditiva de UI**: nenhuma engine fundamentalista/técnica é tocada, os 283 goldens ficam intactos, `app.py` ganha uma camada fina e a lógica nova vive num módulo read-only novo (`core/home_feed.py`).

Os três pilares de arquitetura já existem no próprio codebase e devem ser **reusados literalmente**, não reinventados: (1) o padrão `@st.fragment(run_every=...)` para auto-refresh escopado a um bloco (usado no Swing, `app.py:912`); (2) o `@st.cache_data(ttl=...)` process-global para garantir 1 chamada externa por TTL independente do nº de usuários (D-05, o item mais crítico da fase); (3) a ponte unidirecional Python→JS via `components.html` + `localStorage` best-effort com `try/catch` por acesso (LWC-03, `app.py:334-358`). A única lacuna real de arquitetura é que a watchlist **precisa ler o `localStorage` de volta para o Python** (para saber quais tickers buscar) — e a ponte atual é só de escrita.

**Primary recommendation:** Prepender uma opção "🏠 Início" como **primeiro item** do `st.sidebar.radio` (vira default automaticamente, index 0) + novo bloco `if modo.startswith("🏠")` antes dos 4 existentes. Cotações via **uma** chamada `yf.download(tickers, period="5d", interval="1d")` cacheada com `ttl≈45s`; variação do dia = `close[-1]/close[-2]-1`. Notícias via **feedparser 6.0.12** sobre InfoMoney (`.../mercados/feed/`) + Google News RSS (`hl=pt-BR&gl=BR&ceid=BR:pt-419`), cacheado com `ttl≈600s`. Persistência da watchlist via **streamlit-local-storage** (bidirecional) com fallback para `st.session_state` semeado pelos 5 defaults. Links via `st.link_button` (nova aba nativa, sem HTML cru → sem XSS). Fragmentos com `run_every ≈ TTL`.

<phase_requirements>
## Phase Requirements

| ID | Descrição | Suporte da pesquisa |
|----|-----------|---------------------|
| HOME-01 | Landing default de acompanhamento; 4 menus atuais intactos, aditiva | §Q1 Roteamento do radio (prepend "🏠 Início" → index 0); dispatch por `if modo.startswith(...)` (padrão existente em `app.py:400`) |
| WATCH-01 | Watchlist ≤5 tickers, default editável, persiste via `localStorage`, tickers inválidos degradam | §Q5 streamlit-local-storage + fallback session_state; §Q7 validação `^[A-Z0-9]{4,6}$`; degradação graciosa herdada do padrão `FrameOHLC`/`coletar_mercado` |
| WATCH-02 | Preço + variação do dia colorida, auto ~30–60s, efeito visual, aviso atraso ~15min, cache compartilhado, degrada sem quebrar | §Q2 fragment run_every; §Q3 batch yfinance + day%; §Q4 cache_data ttl; `st.metric(delta=...)` colore verde/vermelho |
| NEWS-01 | Feed manchete+submanchete+fonte+hora, abre site original em nova aba, só RSS aberto | §Q6 feeds validados ao vivo; feedparser; §Q7 `st.link_button` nova aba segura |
| NEWS-02 | Auto ~5–15min, cache compartilhado, degrada se fonte cair, custo-zero | §Q2/§Q4 fragment+cache; try/except por feed; sem API paga |
</phase_requirements>

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01..D-06)
- **D-01 — Home é nova landing default.** Ao abrir o app, a Home é a primeira tela. Os 4 menus atuais (Analisar/Garimpar/Ranking/Swing) continuam no radio lateral **sem mudança de comportamento**. Reorganizar o roteamento do `app.py` de forma **aditiva** — hoje o default é "Analisar uma ação".
- **D-02 — Watchlist: lista default editável + persistência `localStorage`.** ~5 tickers default de dividendos (sugestão: BBSE3, TAEE11, EGIE3, ITUB4, BBAS3 — confirmar no plano). Usuário edita (add/remove, teto ~5), persiste entre sessões por navegador, sem backend. Ponte Python↔JS unidirecional — reusar a lição da Fase 17. Tickers inválidos degradam sem quebrar.
- **D-03 — Fontes: InfoMoney + Google News RSS + o que tiver RSS aberto.** Valor/Folha têm RSS fraco/paywall → validar feed a feed, incluir só o que retornar manchete utilizável. Parser: `feedparser` (possível única dep Python nova — pinnar; stdlib como alternativa custo-zero-de-dep).
- **D-04 — Refresh cotações: auto ~30–60s + aviso de atraso ~15min.** `st.fragment` escopado só à watchlist. Efeito verde/vermelho na variação; flash na mudança de preço se viável sem complicar. Aviso de atraso ~15min explícito. Notícias auto ~5–15min.
- **D-05 — Cache compartilhado no servidor (obrigatório).** `@st.cache_data(ttl=...)` no fetch de cotações e RSS → 1 chamada por ticker/feed por intervalo, independente do nº de usuários. **Item de arquitetura mais importante da fase.** TTL: cotações ~30–60s; RSS ~5–15min.
- **D-06 — UI fina + módulo novo read-only.** Agregação num módulo leve (`core/home_feed.py` / `core/watchlist.py`): busca cotações (reusa fetch Yahoo do swing) e parseia RSS. `app.py` ganha a Home como camada fina. Custo-zero, 283 goldens intactos, engines não tocadas.

### Claude's Discretion
- Lista default exata de tickers e teto (5 fixo?).
- `feedparser` vs parse por stdlib.
- Quais feeds RSS além de InfoMoney/Google News entram.
- Formato do aviso de atraso e do estado vazio.
- Estrutura interna do módulo novo.

### Deferred Ideas (OUT OF SCOPE)
- Tempo-real tick-a-tick (feed pago) — fica no delayed ~15min do Yahoo.
- Camada de IA de sentimento / "ativos mais citados" à la TradersClub.
- Reproduzir texto completo das notícias (só manchete/trecho + link).
- Backend/login/persistência server-side da watchlist (vem no v2.0).
- Gráficos/sparkline na watchlist (só número + variação).
- Qualquer mudança nas engines ou nos 283 goldens.
- Casar notícia↔ativo (chip de ticker na notícia).
</user_constraints>

## Architectural Responsibility Map

App single-process Streamlit; "tiers" aqui são camadas lógicas dentro do mesmo processo + o browser.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Roteamento / landing default | UI (`app.py` sidebar radio) | — | radio já é o dispatcher dos 4 menus; Home é só +1 branch |
| Render watchlist (metric colorido, selo atraso) | UI (`app.py`, fragment) | — | camada fina; lê dados já agregados |
| Fetch cotações (batch, day%) | Data module (`core/home_feed.py`) | External (Yahoo/yfinance) | read-only; reusa `prices.yahoo_symbol/_yf` |
| Fetch + parse RSS | Data module (`core/home_feed.py`) | External (InfoMoney, Google News) | agregação/dedupe/sort fora da UI |
| Cache compartilhado (1 chamada/TTL) | Data module (`@st.cache_data`) | — | process-global; garante D-05 para N usuários |
| Auto-refresh (polling visual) | UI (`@st.fragment run_every`) | — | re-roda só o bloco; TTL é o porteiro real dos dados |
| Persistência da watchlist | Client (browser `localStorage`) | UI (bridge component + session_state fallback) | sem backend; best-effort por navegador |
| Abrir notícia no site original | Client (nova aba) | UI (`st.link_button`) | link nativo seguro; sem reproduzir conteúdo |

## Standard Stack

### Core (já instalado — reuso)
| Library | Version (venv) | Latest PyPI | Purpose | Why Standard |
|---------|----------------|-------------|---------|--------------|
| streamlit | 1.58.0 | — | UI, radio, fragment, cache_data, metric, link_button | Já é a base do app; `st.fragment(run_every)` GA desde 1.37; `st.link_button` desde 1.28 — ambos disponíveis [VERIFIED: `pip show streamlit`] |
| yfinance | 1.4.1 | 1.5.1 | Cotações delayed ~15min (last price + prev close) | Já usado em `prices.py`/`intraday.py`; reusar `prices.yahoo_symbol()` e `prices._yf()` [VERIFIED: `pip index versions yfinance`] |
| pandas | ≥2.0 | — | Manipular o frame do `yf.download` | Já é dependência |

### Supporting (novas — a instalar)
| Library | Version to pin | Purpose | When to Use |
|---------|----------------|---------|-------------|
| feedparser | 6.0.12 (2025-09-10) | Parse robusto de RSS/Atom (title, link, summary, published_parsed, tags) | NEWS-01/NEWS-02 — parse dos feeds; lida com CDATA, encodings, sanitização HTML básica [VERIFIED: pypi.org/pypi/feedparser/json] |
| streamlit-local-storage | 0.0.25 (2024-11-18) | Leitura **bidirecional** de `localStorage` para o Python (watchlist) | WATCH-01 — persistência entre sessões; requer streamlit≥0.63, python≥3.7 [VERIFIED: pypi.org/pypi/streamlit-local-storage/json] — MEDIUM: não testado contra 1.58 nesta sessão, single-maintainer |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| feedparser | stdlib `xml.etree.ElementTree` + parse manual | Zero dep, mas você reimplementa CDATA/encoding/campos Atom vs RSS/timezone parsing — feedparser resolve isso de graça. **Recomendo feedparser** (D-03 já o prevê como "o pragmático"). |
| streamlit-local-storage | bridge dep-free custom (`components.html` + `Streamlit.setComponentValue`) | Zero dep, mas é reimplementar o próprio pacote — mais código/risco. Só se o usuário quiser teto de deps. |
| streamlit-local-storage | `st.query_params` + JS reload | Causa loop de reload/flicker; frágil. Descartado. |
| yfinance batch | brapi.dev free | brapi passou a exigir token e o free **não serve** para B3 completa [CITED: memória `b3-dados-gratuitos.md` / `analista-dividendos-mvp.md`]. Descartado. |

**Installation:**
```bash
pip install "feedparser==6.0.12" "streamlit-local-storage==0.0.25"
# adicionar em requirements.txt:
#   feedparser==6.0.12
#   streamlit-local-storage==0.0.25   # (ou omitir se optar pelo fallback dep-free)
```

**Version verification (nesta sessão):**
- streamlit 1.58.0 instalado [VERIFIED: `pip show streamlit`]
- yfinance 1.4.1 instalado; latest 1.5.1 [VERIFIED: `pip index versions yfinance`] — 1.4.1 já usa `curl_cffi` (impersonation de browser), relevante p/ rate-limit
- feedparser **não instalado**; latest 6.0.12, 2025-09-10, requires_python ≥3.6 [VERIFIED: PyPI JSON]
- streamlit-local-storage **não instalado**; latest 0.0.25, 2024-11-18 [VERIFIED: PyPI JSON]

## Architecture Patterns

### System Architecture Diagram

```
                          ┌─────────────────────────── BROWSER ───────────────────────────┐
   usuário abre o app     │  localStorage["watchlist_v18"]  ◄──write── (bridge component)  │
        │                 │        │ read-back (1 rerun de atraso)                          │
        ▼                 └────────┼───────────────────────────────────────────────────────┘
  st.sidebar.radio ["🏠 Início"(default), 🔎, ⛏️, 📊, 📈]
        │ modo.startswith("🏠")
        ▼
  ┌──────────────────────────── HOME PAGE (app.py, camada fina) ────────────────────────────┐
  │                                                                                          │
  │  @st.fragment(run_every≈45s)          @st.fragment(run_every≈600s)                       │
  │  ┌── WATCHLIST ──────────────┐        ┌── NOTÍCIAS ───────────────────┐                  │
  │  │ editor de tickers          │        │ lista densa (headline+fonte+  │                  │
  │  │ st.metric(delta colorido)  │        │  hora + st.link_button)       │                  │
  │  │ selo "⏱ atraso ~15min"     │        │                               │                  │
  │  └──────────┬─────────────────┘        └──────────┬────────────────────┘                  │
  └─────────────┼──────────────────────────────────────┼──────────────────────────────────────┘
                ▼ (tuple de tickers)                    ▼
     home_feed.cotacoes(tuple)              home_feed.noticias()
     @st.cache_data(ttl≈45s)                @st.cache_data(ttl≈600s)   ◄── PROCESSO-GLOBAL:
                │  cache hit → sem I/O             │  cache hit → sem I/O    1 chamada por TTL
                ▼ cache miss                       ▼ cache miss             p/ TODOS os usuários (D-05)
   yf.download(syms, period="5d",         feedparser.parse(url) por feed
     interval="1d", threads=True)           (try/except por feed)
   day% = close[-1]/close[-2]-1           merge → dedupe → sort by pubDate desc
                │                                  │
                ▼                                  ▼
        Yahoo Finance (delayed ~15min)   InfoMoney RSS · Google News RSS
```

O leitor traça o caso principal: usuário abre → cai na Home → dois fragmentos independentes fazem polling visual → cada um chama uma função cacheada process-global → só sai I/O quando o TTL expira.

### Recommended Project Structure
```
src/analista/core/
├── home_feed.py     # NOVO, read-only: cotacoes(tickers)->list[dict], noticias()->list[dict]
│                    #   NÃO importa engines; reusa prices.yahoo_symbol/_yf; try/except total
app.py               # + opção "🏠 Início" no radio (index 0) e branch if modo.startswith("🏠")
                     # + as funções @st.cache_data(ttl=...) wrapper e os 2 @st.fragment
requirements.txt     # + feedparser==6.0.12 [+ streamlit-local-storage==0.0.25]
```
> Nota D-06: o módulo pode ser um só (`home_feed.py`) ou dividido (`watchlist.py`+`noticias.py`) — discricionário. Mantê-lo **sem import de `report`/`build`/`indicators`** garante o firewall com as engines.

### Pattern 1: Landing default via radio (index 0) — HOME-01
**What:** Prepender a opção Home faz dela o default sem `index=` explícito (radio stateless → default = primeiro item).
**When to use:** sempre que precisar de nova primeira tela mantendo as antigas.
**Example:**
```python
# app.py — hoje (app.py:377): 4 opções, default = "🔎 Analisar" (index 0)
modo = st.sidebar.radio(
    "O que você quer fazer?",
    ["🏠 Início",                       # NOVO 1º item → vira o default automaticamente
     "🔎 Analisar uma ação", "⛏️ Garimpar carteira (BSD)",
     "📊 Ranking por múltiplos", "📈 Swing trade (análise técnica)"],
    help=h("menu"),
)
# ... e um novo bloco ADITIVO antes do "if modo.startswith('🔎')":
if modo.startswith("🏠"):
    render_home()        # camada fina; os 4 branches existentes ficam idênticos
```
> Gotcha: o radio hoje **não tem `key=`** → é stateless, então adicionar um 1º item muda o default sem migração de estado. Se algum dia ganhar `key=`, aí sim precisaria de `index=`.
> O `st.title`/`st.caption` (app.py:373-375) e a sidebar de Selic/aviso (384-394) hoje rodam **sempre**. Decidir no plano se ficam globais (ok) ou movem para dentro dos branches.

### Pattern 2: Auto-refresh escopado com fragment — WATCH-02/NEWS-02
**What:** `@st.fragment(run_every=...)` re-roda **só aquele bloco** no intervalo, sem recarregar a página nem os outros menus. Padrão já usado no Swing.
**When to use:** polling de um bloco isolado.
**Example (padrão vigente, app.py:912-915):**
```python
@st.fragment(run_every=run_every)   # int seg | timedelta | "30s"/"5m" | None(desliga)
def _render_swing():
    with st.spinner(...):
        f = frame_intraday(ticker, tf_key, st.session_state[k])  # função @st.cache_data
    ...
```
Aplicado à Home — **dois fragmentos independentes**:
```python
@st.fragment(run_every=45)          # watchlist ~30–60s (D-04)
def _render_watchlist(): ...        # chama home_feed.cotacoes(tuple(tickers))

@st.fragment(run_every=600)         # notícias ~5–15min (D-04)
def _render_noticias(): ...         # chama home_feed.noticias()
```
> Gotchas de fragment: (1) `run_every` continua disparando mesmo com a aba em background (o browser pode throttlar timers de aba oculta — ok para nós). (2) mexer num widget FORA do fragment dispara rerun full e **re-decora** o fragment — por isso os controles de intervalo ficam fora dele de propósito (ver comentário em app.py:887). (3) o fragment não deve escrever widgets fora do próprio container. (4) `run_every=None` desliga o auto-refresh (útil para um toggle "pausar").

### Pattern 3: Cache process-global — D-05 (o mais crítico)
**What:** `@st.cache_data(ttl=...)` é memoização **por processo**, compartilhada entre todas as sessões/usuários. N usuários fazendo polling ⇒ ainda **1 chamada externa por TTL** por ticker-set/feed.
**Example:**
```python
@st.cache_data(show_spinner=False, ttl=45)          # cotações ~30–60s
def cotacoes(tickers: tuple[str, ...]) -> list[dict]:
    return home_feed.cotacoes(tickers)              # tuple = chave hashável (NUNCA list)

@st.cache_data(show_spinner=False, ttl=600)         # RSS ~5–15min
def noticias() -> list[dict]:
    return home_feed.noticias()
```
> **Interação TTL × run_every:** o fragment re-roda e chama a função cacheada; dentro do TTL retorna o valor memoizado (sem rede). Regra: **`run_every ≈ TTL`**. Se `run_every < TTL` → só re-renderiza o mesmo dado (barato). Se `run_every > TTL` → dado fica velho até o próximo tick. Recomendo `run_every == TTL` para watchlist (45s/45s) e notícias (600s/600s).
> A chave do cache deve ser **hashável** → passar `tuple(sorted(tickers))`, não `list`. Padrão idêntico ao `frame_intraday(ticker, tf, nonce)` do código (app.py:58).

### Pattern 4: Preço + variação colorida — WATCH-02
```python
# variação do dia colore verde/vermelho AUTOMATICAMENTE via delta do st.metric
st.metric(label=ticker, value=fmt_rs(preco),
          delta=f"{pct*100:+.2f}%")   # delta_color="normal" (default): + verde / − vermelho
```
> Reusar `fmt_rs`/`fmt_pct` já existentes (app.py:82-91). "Flash" na mudança de preço (D-04 "se viável sem complicar") exige CSS/JS extra → **deferir** ou aplicar CSS leve; a cor do delta já entrega o essencial.

### Pattern 5: Bridge localStorage bidirecional — WATCH-01
A ponte atual (LWC-03, app.py:334-358) é **só escrita** (Python→JS, aplicada dentro do iframe, nunca lida de volta). A watchlist **precisa ler de volta** para saber os tickers a buscar. Ver §Q5 para a recomendação (streamlit-local-storage + fallback session_state).

### Anti-Patterns to Avoid
- **`st.cache_data.clear()` global:** apagaria o cache de `montar`/`selic_atual`/`rf_capm` da aba Analisar (D-08). Nunca. TTL curto já cuida da invalidação.
- **Passar `list` para função cacheada:** unhashable → erro. Use `tuple`.
- **RSS cru em `unsafe_allow_html=True` ou `components.html`:** XSS. Ver §Q7.
- **Derivar `period` do input do usuário no yfinance:** exceder teto retorna frame vazio (comentário em intraday.py:31). Use período fixo.
- **1 chamada yfinance por ticker num loop:** N chamadas = risco de 429. Use `yf.download` batch.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parse de RSS/Atom | parser XML manual | `feedparser` | CDATA, encodings, published_parsed→struct_time, RSS vs Atom, sanitização — dezenas de edge cases |
| Ler localStorage no Python | reload hacks com query_params | `streamlit-local-storage` (ou bridge component) | roundtrip JS→Python é async; o pacote resolve o handshake |
| Auto-refresh | `time.sleep`+`st.rerun` loop | `@st.fragment(run_every=...)` | sleep bloqueia a sessão inteira; fragment escopa e é nativo |
| Cache multiusuário | dict global + locks | `@st.cache_data(ttl=...)` | process-global, thread-safe, TTL nativo |
| Símbolo Yahoo / retry | reescrever `.SA`/backoff | `prices.yahoo_symbol()`, `prices._MAX_TENTATIVAS`, `prices._BACKOFF_SEG` | já calibrado e testado |
| Link em nova aba seguro | `<a target=_blank>` cru | `st.link_button(label, url)` | Streamlit monta a âncora com segurança; sem HTML cru |

**Key insight:** quase tudo desta fase já existe no codebase (fragment, cache, bridge, fetch Yahoo) ou num pacote maduro. O trabalho real é **cablagem fina + o cache process-global (D-05)** — não lógica nova.

## Common Pitfalls

### Pitfall 1: Fragment re-fetch × TTL desalinhados
**What goes wrong:** `run_every` muito menor que TTL desperdiça reruns; muito maior deixa o dado velho.
**Why:** são dois relógios distintos (render vs. I/O).
**How to avoid:** `run_every == TTL` (45s/45s watchlist, 600s/600s notícias).
**Warning signs:** preço "congelado" apesar do fragment rodando, ou spinner sem nova rede.

### Pitfall 2: Mercado fechado / pré-abertura → variação estranha ou vazia
**What goes wrong:** com `period="5d"`, antes do 1º negócio do dia a última barra pode ser o fechamento anterior → variação ~0%; feriado/fim de semana mostra a última sessão.
**Why:** Yahoo delayed e barra diária ainda não formada.
**How to avoid:** computar `close[-1]/close[-2]-1` sobre barras diárias (robusto a fins de semana); exibir selo "⏱ atraso ~15min" (D-04) e tolerar `—` quando faltar barra.
**Warning signs:** todos os tickers 0,00% de manhã cedo.

### Pitfall 3: Feed RSS cai ou é throttado
**What goes wrong:** InfoMoney está atrás de CDN (WordPress/Cloudflare) e **throttla requisições repetidas rápidas** — nesta sessão o 3º hit voltou truncado (1344 bytes) [VERIFIED nesta sessão].
**Why:** WAF/rate-limit por IP.
**How to avoid:** cache TTL≥600s (poucos hits), **User-Agent** de browser no request, `try/except` por feed (uma fonte cair não derruba as outras), `feedparser.parse(url, agent="Mozilla/5.0 ...")`.
**Warning signs:** feed vazio intermitente; `bozo=1` no objeto do feedparser.

### Pitfall 4: localStorage SecurityError em iframe sandbox / aba anônima
**What goes wrong:** acesso a `localStorage` lança SecurityError em iframe de origem opaca ou modo privado.
**Why:** política de storage do browser (já documentado no próprio código, app.py:337).
**How to avoid:** `try/catch` por acesso (padrão LWC-03) e **fallback para `st.session_state`** semeado pelos 5 tickers default → a página sempre funciona; persistência entre sessões é best-effort.
**Warning signs:** watchlist volta ao default a cada reload em certos browsers.

### Pitfall 5: Rerun full reseta estado do editor da watchlist
**What goes wrong:** trocar de menu ou um widget fora do fragment re-roda tudo e pode perder edições não persistidas.
**Why:** modelo de execução do Streamlit.
**How to avoid:** guardar a lista em `st.session_state` (fonte de verdade em runtime) e escrever no localStorage a cada mudança; ler o localStorage só no load inicial.
**Warning signs:** ticker adicionado some ao navegar.

### Pitfall 6: Timezone das notícias e do "atraso"
**What goes wrong:** `pubDate` vem em GMT/UTC; exibir hora "crua" confunde o usuário BR.
**Why:** RSS usa RFC-822 em GMT.
**How to avoid:** converter para `America/Sao_Paulo` (padrão já usado em `intraday._normaliza_tz`); `feedparser` dá `published_parsed` (UTC struct_time) → localizar/converter.
**Warning signs:** notícia "3h no futuro".

### Pitfall 7: Colisão de chaves no localStorage
**What goes wrong:** reusar a chave do LWC-03 (range do gráfico) sobrescreveria dados.
**How to avoid:** namespace próprio, ex.: `"watchlist_v18"`.

### Pitfall 8: `$` em markdown quebra layout (LaTeX)
Reusar `esc_md()` (app.py:94) ao renderizar valores em `R$` dentro de markdown/alertas.

## Code Examples

### Cotações em lote + variação do dia (WATCH-02, Q3)
```python
# core/home_feed.py — read-only, nunca levanta exceção (padrão FrameOHLC)
def cotacoes(tickers: tuple[str, ...]) -> list[dict]:
    from ..ingest import prices
    yf = prices._yf()
    syms = [prices.yahoo_symbol(t) for t in tickers]      # reuso: adiciona ".SA"
    out = []
    try:
        # UMA chamada em lote: 5d p/ ter close[-1] (dia) e close[-2] (dia anterior)
        df = yf.download(" ".join(syms), period="5d", interval="1d",
                         group_by="ticker", auto_adjust=False,
                         progress=False, threads=True)
    except Exception:
        df = None
    for t, sym in zip(tickers, syms):
        try:
            close = df[sym]["Close"].dropna() if df is not None else None
            preco = float(close.iloc[-1])
            prev  = float(close.iloc[-2])
            pct   = preco / prev - 1.0
            out.append({"ticker": t, "preco": preco, "pct": pct, "ok": True})
        except Exception:
            out.append({"ticker": t, "preco": None, "pct": None, "ok": False})  # degrada, não quebra
    return out
```
> Fonte: assinatura de `yf.download` [VERIFIED: `help(yf.download)` no venv] + reuso de `prices.py`. Variação do dia = `close[-1]/close[-2]-1` [ASSUMED: mapeia "variação do dia" — validar contra `previousClose` do site em 1 ticker no plano].

### Parse de notícias multi-feed (NEWS-01, Q6)
```python
import feedparser
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("America/Sao_Paulo")
_FEEDS = {
    "InfoMoney": "https://www.infomoney.com.br/mercados/feed/",
    "Google News": ("https://news.google.com/rss/search?"
                    "q=mercado+financeiro+bolsa+dividendos&hl=pt-BR&gl=BR&ceid=BR:pt-419"),
}
_UA = "Mozilla/5.0 (compatible; AnalistaDividendos/1.0)"

def noticias() -> list[dict]:
    itens = []
    for fonte, url in _FEEDS.items():
        try:
            fp = feedparser.parse(url, agent=_UA)     # nunca levanta; checar fp.bozo
        except Exception:
            continue
        for e in fp.entries[:20]:
            ts = e.get("published_parsed")
            dt = datetime(*ts[:6], tzinfo=timezone.utc).astimezone(_TZ) if ts else None
            itens.append({
                "fonte": fonte,
                "titulo": e.get("title", ""),          # untrusted → render como texto (Q7)
                "resumo": e.get("summary", ""),        # untrusted → strip HTML / texto
                "link": e.get("link", ""),             # validar https:// antes de usar
                "quando": dt,
            })
    # dedupe por título normalizado; sort por data desc
    vistos, dedup = set(), []
    for it in sorted(itens, key=lambda x: x["quando"] or datetime.min.replace(tzinfo=_TZ),
                     reverse=True):
        k = it["titulo"].strip().lower()
        if k and k not in vistos:
            vistos.add(k); dedup.append(it)
    return dedup
```
> Estrutura dos feeds [VERIFIED ao vivo 2026-07-01]: InfoMoney é WordPress RSS 2.0 (title/link/pubDate/dc:creator/category/description-CDATA/content:encoded). Google News RSS: `title="Manchete - Fonte"`, `link` é redirect `news.google.com/rss/articles/...`, tem `<source url=>` e `pubDate`; **description do Google é HTML pobre** (âncoras) → submanchete boa vem do InfoMoney, não do Google.

### Render seguro de item de notícia (Q7)
```python
st.markdown(f"**{item['titulo']}**")          # texto: st.markdown NÃO renderiza HTML (default)
st.caption(f"{item['fonte']} · {item['quando']:%d/%m %H:%M}")
if item["link"].startswith("https://"):
    st.link_button("Abrir no site ↗", item["link"])   # nova aba nativa + rel seguro; sem HTML cru
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `streamlit-autorefresh` / `st_autorefresh` (3rd-party) | `st.fragment(run_every=...)` nativo | Streamlit 1.37 (GA) | Zero dep; escopo por bloco (o autorefresh recarregava a página toda) |
| `<a target=_blank>` via `unsafe_allow_html` | `st.link_button(label, url)` | Streamlit 1.28 | Nova aba segura sem HTML cru |
| yfinance `requests` puro | yfinance sobre `curl_cffi` (impersonation) | yfinance 0.2.52+ (1.x default) | Menos 429; ainda intermitente em IP de datacenter/VPS |
| Yahoo endpoint `v7/quote` (quote em lote) | protegido por crumb/consent; yfinance evita | ~2024 | Usar `yf.download` (chart endpoint) em vez do quote endpoint |

**Deprecated/outdated:**
- brapi.dev free para B3: exige token e não cobre o universo [CITED: memória do projeto].
- `st.experimental_fragment` → renomeado `st.fragment` (estável).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | "variação do dia" = `close[-1]/close[-2]-1` (barras diárias) casa com o número que corretoras exibem | Code Examples / Q3 | Baixo — validar 1 ticker vs. site; alternativa é `fast_info.previous_close` (custa 1 call/ticker) |
| A2 | streamlit-local-storage 0.0.25 funciona com streamlit 1.58 | Standard Stack / Q5 | Médio — pacote single-maintainer, última release 2024-11; testar no início do plano; fallback session_state cobre |
| A3 | Google News RSS query genérica traz manchetes BR relevantes de mercado sem muito ruído | Q6 | Baixo — ajustar a query (`when:1d`, termos) no plano; InfoMoney é a fonte primária de qualidade |
| A4 | feedparser 6.0.12 roda em Python ≥3.10 do projeto | Standard Stack | Baixo — requires_python ≥3.6; amplamente usado em 3.10-3.12 |
| A5 | Lista default BBSE3/TAEE11/EGIE3/ITUB4/BBAS3 resolve no Yahoo `.SA` | D-02 | Baixo — todos são tickers líquidos; teto 5 confirmar no plano |

## Open Questions (RESOLVED)

1. **Lista default exata + teto rígido de 5?**
   - RESOLVED: 5 tickers default (BBSE3/TAEE11/EGIE3/ITUB4/BBAS3), teto 5 fixo (limita chamadas Yahoo), editável — adotado no plano 18-02.
2. **streamlit-local-storage vs. bridge dep-free?**
   - RESOLVED: usar `streamlit-local-storage` (bidirecional) com fallback `st.session_state`; validado como Assumption A2 no início do plano 18-01, com bridge custom `components.html`+`setComponentValue` como plano B se o pacote falhar contra streamlit 1.58.
3. **Query do Google News (ruído vs. cobertura)?**
   - RESOLVED: começar com termos de mercado BR + `when:1d`; ajuste fino durante a execução do plano 18-03 após ver o feed real.
4. **"Flash" na mudança de preço (D-04) entra no v1?**
   - RESOLVED: deferido; a cor do delta do `st.metric` já cumpre o essencial (registrado como fora de escopo no plano 18-02).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| streamlit | UI/fragment/cache/link_button | ✓ | 1.58.0 | — |
| yfinance | cotações | ✓ | 1.4.1 (latest 1.5.1) | — |
| pandas | frame yfinance | ✓ | ≥2.0 | — |
| feedparser | parse RSS | ✗ | — (pin 6.0.12) | stdlib xml.etree (mais código) |
| streamlit-local-storage | ler localStorage no Python | ✗ | — (pin 0.0.25) | bridge custom `components.html` + `st.session_state` |
| Internet → Yahoo Finance | cotações | ✓ (query.finance.yahoo.com) | — | selo "dados indisponíveis" + `—` |
| Internet → InfoMoney RSS | notícias | ✓ (live 2026-07-01) | — | pular feed (try/except) |
| Internet → Google News RSS | notícias | ✓ (live 2026-07-01) | — | pular feed |

**Missing dependencies with no fallback:** nenhuma bloqueia — feedparser tem fallback stdlib e streamlit-local-storage tem fallback session_state.
**Missing dependencies with fallback:** feedparser (→stdlib), streamlit-local-storage (→session_state/bridge custom). Ambas recomendadas instalar.

## Security Domain

> `security_enforcement` ausente no config → tratado como habilitado.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Sem login (D-02) |
| V3 Session Management | no | Sem sessão server-side; estado em session_state/localStorage |
| V4 Access Control | no | App público read-only |
| V5 Input Validation | **yes** | Ticker `^[A-Z0-9]{4,6}$` (`.strip().upper()` já no código); RSS tratado como untrusted |
| V6 Cryptography | no | Sem segredos nesta fase |
| V7/V14 Output Encoding | **yes** | `st.markdown`/`st.write` (HTML escapado por default) para títulos/resumos RSS; `st.link_button` para links |

### Known Threat Patterns for {Streamlit + RSS + yfinance}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via título/resumo RSS malicioso | Tampering / Info Disclosure | Renderizar como **texto** (`st.markdown` sem `unsafe_allow_html`; nunca `components.html` com o conteúdo). feedparser já sanitiza markup, mas defesa em profundidade = texto puro |
| Link RSS com esquema perigoso (`javascript:`) | Tampering | Validar `link.startswith("https://")` antes de `st.link_button`; ignorar demais |
| Injeção via ticker do usuário (→ símbolo Yahoo / HTML) | Tampering | Regex `^[A-Z0-9]{4,6}$`; rejeitar antes de `yahoo_symbol()` |
| DoS/rate-limit ao poll de feeds/Yahoo | DoS | `@st.cache_data(ttl)` (poucos hits), retry com backoff limitado (já em prices.py), UA header |
| Tabnabbing em link nova aba | Tampering | `st.link_button` monta âncora com `rel` seguro (não usar `<a target=_blank>` cru) |
| localStorage SecurityError (iframe sandbox/anônima) | (robustez) | `try/catch` por acesso + fallback session_state |

## Sources

### Primary (HIGH confidence)
- Codebase local: `app.py` (radio :377, fragment :884-915, bridge localStorage :334-358, cache :35-68), `src/analista/ingest/prices.py` (yahoo_symbol/_yf/retry/coletar_mercado), `src/analista/ingest/intraday.py` (FrameOHLC never-raises, TZ America/Sao_Paulo)
- `pip show streamlit` → 1.58.0; `pip index versions yfinance` → 1.4.1 instalado / 1.5.1 latest; `help(yf.download)` → assinatura de batch [VERIFIED nesta sessão]
- PyPI JSON: feedparser 6.0.12 (2025-09-10); streamlit-local-storage 0.0.25 (2024-11-18) [VERIFIED]
- Feeds testados ao vivo 2026-07-01: `https://www.infomoney.com.br/mercados/feed/` (WordPress RSS 2.0, lastBuildDate hoje), `https://news.google.com/rss/search?q=...&hl=pt-BR&gl=BR&ceid=BR:pt-419` (itens com pubDate/source) [VERIFIED]

### Secondary (MEDIUM confidence)
- Estrutura de campos do WordPress RSS (title/link/pubDate/dc:creator/category/description/content:encoded) — padrão do gerador WordPress 6.9.4 identificado no `<generator>` do feed [CITED]
- feedspot.com — catálogo de RSS InfoMoney/Brasil trading (descoberta de feeds) [WebSearch]
- Memória do projeto: brapi free não serve; B3 dados gratuitos = CVM+yfinance+BCB [CITED]

### Tertiary (LOW confidence)
- Compatibilidade streamlit-local-storage 0.0.25 × streamlit 1.58 — não testada nesta sessão (validar no plano)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versões verificadas no venv/PyPI; fragment/cache/link_button confirmados em 1.58
- Architecture: HIGH — todos os padrões (fragment, cache process-global, bridge localStorage, fetch Yahoo) já existem e foram lidos no próprio código
- RSS feeds: HIGH (live) — InfoMoney e Google News testados hoje; qualidade do Google News query = MEDIUM
- Persistência localStorage bidirecional: MEDIUM — recomendação sólida mas dep single-maintainer não testada contra 1.58
- Pitfalls: HIGH — a maioria já documentada no próprio codebase (SecurityError, TZ, $ markdown, teto period×interval, clear global)

**Research date:** 2026-07-01
**Valid until:** ~2026-07-31 (feeds RSS e rate-limit do Yahoo podem mudar; reverificar URLs de feed e versões antes de executar se passar de 30 dias)
