---
phase: 18-home-watchlist-noticias
plan: 02
subsystem: ui
tags: [streamlit, yfinance, watchlist, fragment, cache_data, streamlit-local-storage, home, metric]

# Dependency graph
requires:
  - phase: 18-01-esqueleto-home
    provides: "home_feed contrato (cotacoes/noticias never-raise, DEFAULT_WATCHLIST/MAX_WATCHLIST/validar_ticker, firewall D-06) + render_home thin com placeholder de watchlist + A2 (streamlit-local-storage==0.0.25 validada)"
provides:
  - "home_feed.cotacoes(tickers) real: UMA chamada yf.download em lote (period 5d, group_by=ticker), variação do dia close[-1]/close[-2]-1, degradação por item (ok=False), never-raise"
  - "app.py _cotacoes @st.cache_data(ttl=45) process-global (D-05) + _render_watchlist @st.fragment(run_every=45) com st.metric colorido + selo de atraso ~15min"
  - "editor de watchlist (add validado + teto 5, remove) FORA do fragment + persistência localStorage watchlist_v18 (streamlit-local-storage bidirecional, fallback session_state semeado pelos defaults)"
affects: [18-03-noticias, 18-04-verificacao]

# Tech tracking
tech-stack:
  added: []
  patterns: ["cache process-global com chave hashável tuple(sorted) (D-05, nunca clear global)", "fragment run_every≈TTL como tick visual sobre wrapper cacheado (porteiro do Yahoo)", "persistência client-side bidirecional via streamlit-local-storage com try/except por acesso + fallback session_state (LWC-03/Pitfall 4)", "controles de editor FORA do fragment (Pitfall 5)"]

key-files:
  created: [tests/test_home_feed.py]
  modified: [src/analista/core/home_feed.py, app.py]

key-decisions:
  - "A1: variação do dia = close[-1]/close[-2]-1 (batch daily-bars) MANTIDA vs fast_info.previous_close — divergência ~0.22pp em BBSE3 (−2.37% vs −2.15%); trocar exigiria 1 call/ticker e destruiria o batch anti-429 (D-05). Batch é fiel a 'preço de hoje vs fechamento da véspera' e está dentro da tolerância delayed ~15min"
  - "Persistência via streamlit-local-storage (dep de A2), NÃO fallback — mas cada acesso em try/except independente com fallback session_state semeado pelos defaults se o pacote/storage falhar"
  - "st.metric por ticker via col.metric (delta_color normal: + verde / − vermelho); item ok=False → metric '—'"
  - "Sem st.rerun() explícito após add/remove: o clique já dispara o rerun natural e o componente de setItem renderiza no caminho (rerun descartaria o write do localStorage)"

patterns-established:
  - "Cache process-global (D-05): _cotacoes(tuple(sorted(tickers))) @st.cache_data(ttl=45) — 1 chamada externa por conjunto por TTL, chave hashável, nunca clear global"
  - "Fragment run_every≈TTL (45s/45s): _render_watchlist re-roda só o bloco; o TTL do wrapper é o porteiro real do Yahoo"
  - "Persistência best-effort: seed no 1º load (localStorage → defaults), escrita a cada mudança, try/except por acesso, namespace próprio watchlist_v18"

requirements-completed: [WATCH-01, WATCH-02]

# Metrics
duration: ~12min
completed: 2026-07-01
---

# Phase 18 Plan 02: Watchlist da Home Summary

**home_feed.cotacoes() real (UMA chamada yf.download em lote + variação do dia + degradação por item) alimenta a watchlist da Home: st.metric colorido auto-atualizável via cache process-global (ttl=45) + fragment (run_every=45), editor validado (teto 5) persistido em localStorage (watchlist_v18) com fallback session_state, e selo de atraso ~15min.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-01T15:05Z (aprox.)
- **Completed:** 2026-07-01T15:17Z (aprox.)
- **Tasks:** 2
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments
- **WATCH-02 (fetch):** `home_feed.cotacoes(tickers)` implementada — UMA `yf.download(" ".join(syms), period="5d", interval="1d", group_by="ticker", ...)` em lote (anti-429), variação do dia `close[-1]/close[-2]-1` sobre barras diárias (robusto a fim de semana/pré-abertura), degradação por item (`ok=False`, `preco/pct=None`) sem derrubar a lista, never-raise. Reusa `prices.yahoo_symbol/_yf` por import tardio — **firewall D-06 intacto** (só importa `re`, `__future__`, `prices`).
- **WATCH-01 + WATCH-02 (UI):** bloco de watchlist real substituiu o placeholder no `render_home`: wrapper `_cotacoes` `@st.cache_data(ttl=45)` process-global (chave `tuple(sorted)`), fragment `_render_watchlist` `@st.fragment(run_every=45)` com `st.metric` colorido (delta + verde / − vermelho) e selo de atraso ~15min, editor (add validado por `validar_ticker` + teto 5, remove) FORA do fragment, persistência `watchlist_v18` via streamlit-local-storage bidirecional com fallback `session_state` semeado pelos defaults.
- **6 testes novos** (`tests/test_home_feed.py`) via monkeypatch de `prices._yf` (sem rede): contrato, variação do dia, uma-única-chamada-em-lote (period 5d), degradação por item, never-raise offline, watchlist vazia.
- **289 goldens verdes** (283 pré-existentes + 6 novos) — engine e aba Analisar intactas.
- **Smoke live:** `streamlit run app.py` sobe HTTP 200 sem erro de import/render.

## Task Commits

Cada tarefa foi commitada atomicamente:

1. **Task 1 (TDD RED): teste falho de home_feed.cotacoes** - `11d7d50` (test)
2. **Task 1 (TDD GREEN): home_feed.cotacoes real** - `c151456` (feat)
3. **Task 2: bloco de watchlist no app.py** - `5690443` (feat)

**Plan metadata:** (docs commit final)

## Files Created/Modified
- `tests/test_home_feed.py` - 6 testes do contrato never-raise de `cotacoes` (batch, variação do dia, degradação por item, offline, vazia) via monkeypatch de `prices._yf`
- `src/analista/core/home_feed.py` - corpo de `cotacoes(tickers)`: uma `yf.download` em lote (period fixo 5d), variação do dia, degradação por item, never-raise (firewall D-06 preservado)
- `app.py` - `_cotacoes` (cache ttl=45) + helpers de localStorage (`_watchlist_ls`/`_seed_watchlist`/`_persistir_watchlist`) + `render_home` com editor + fragment `_render_watchlist` (metric colorido + selo)

## Decisions Made
- **A1 — variação do dia MANTIDA no batch daily-bars.** Validação ao vivo (BBSE3, 2026-07-01): nosso `close[-1]/close[-2]-1` = **−2.37%** (38.24 vs fechamento da véspera 39.17) contra `fast_info.previous_close` (39.08) = **−2.15%** → divergência de **~0.22pp**. A divergência é pequena e atribuível ao `previous_close` do fast_info ser sourced/ajustado de forma diferente (timing intraday / possível ajuste de proventos). **Não trocamos** para `fast_info.previous_close` porque isso custaria **1 call por ticker** e destruiria o batch (D-05 / anti-429 — o núcleo da fase). O método batch é fiel a "preço de hoje vs fechamento da sessão anterior" (definição de variação do dia) e está dentro da tolerância do delayed ~15min.
- **Persistência = streamlit-local-storage (dep A2), não fallback-only.** Conforme decisão do plano 01. Robustez: cada `getItem`/`setItem` em `try/except` independente; se o pacote/storage falhar (SecurityError em iframe sandbox/anônima — Pitfall 4), cai no `session_state` semeado pelos defaults → a página SEMPRE renderiza. `LocalStorage.__init__` bloqueia só no 1º load da sessão (handshake `getAll`), então `getItem` é síncrono depois — retornar-usuário recupera a lista no 1º paint.
- **Sem `st.rerun()` após add/remove:** o clique de botão já dispara o rerun natural do Streamlit e o componente de `setItem` renderiza no caminho; um `st.rerun()` explícito descartaria o frame e o write do localStorage nunca chegaria ao browser.
- **`col.metric` (não `st.metric` direto):** para posicionar a métrica na coluna do ticker (idiomático). `delta_color` default colore automaticamente.

## Deviations from Plan
None - plan executed exactly as written. As 3 decisões acima são resoluções de pontos que o próprio plano deixou explícitos (A1, caminho de persistência), não desvios.

## Issues Encountered
- **TDD RED — fixture de watchlist vazia:** o teste `test_cotacoes_vazio` inicialmente falhava na CONSTRUÇÃO do fixture (`pd.MultiIndex.from_tuples([])` levanta "Cannot infer number of levels from empty list"), não na asserção. Trocado para `pd.DataFrame()` simples — `cotacoes(())` faz short-circuit antes de tocar a rede (assert `contador == []`).

## User Setup Required
None - as deps já foram instaladas no venv local no plano 01; em outros ambientes basta `pip install -r requirements.txt`.

## Next Phase Readiness
- Watchlist funcional ponta-a-ponta (fetch real + UI + persistência). Plano 03 preenche `home_feed.noticias()` (parse RSS feedparser) e substitui o placeholder de notícias no `render_home`.
- Plano 04 (verificação): a base do diff de invariância (`.phase-base-sha` 5ae5190) segue válida; os 289 testes (283 goldens + 6 de home_feed) estão verdes.

## Self-Check: PASSED

- FOUND: tests/test_home_feed.py
- FOUND: src/analista/core/home_feed.py
- FOUND: app.py
- FOUND: .planning/phases/18-home-watchlist-noticias/18-02-SUMMARY.md
- FOUND: commit 11d7d50 (Task 1 RED)
- FOUND: commit c151456 (Task 1 GREEN)
- FOUND: commit 5690443 (Task 2)

---
*Phase: 18-home-watchlist-noticias*
*Completed: 2026-07-01*
