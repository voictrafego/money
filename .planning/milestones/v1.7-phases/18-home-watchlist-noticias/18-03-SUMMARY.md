---
phase: 18-home-watchlist-noticias
plan: 03
subsystem: ui
tags: [streamlit, feedparser, rss, noticias, fragment, cache_data, home, zoneinfo, security]

# Dependency graph
requires:
  - phase: 18-01-esqueleto-home
    provides: "home_feed contrato (noticias() never-raise, firewall D-06) + render_home thin com placeholder de notícias"
  - phase: 18-02-watchlist
    provides: "padrões _cotacoes @st.cache_data(ttl=) process-global + _render_watchlist @st.fragment(run_every=) reusados literalmente no bloco de notícias"
provides:
  - "home_feed.noticias() real: feedparser InfoMoney + Google News BR, User-Agent de browser, try/except por feed, dedupe por título normalizado, sort por data desc, pubDate UTC→America/Sao_Paulo, link só https, resumo como texto sem HTML, never-raise→[]"
  - "app.py _noticias @st.cache_data(ttl=600) process-global (D-05) + _render_noticias @st.fragment(run_every=600) com render seguro (título via st.markdown texto, fonte/hora via st.caption, st.link_button só https) + estado vazio tratado"
affects: [18-04-verificacao]

# Tech tracking
tech-stack:
  added: []
  patterns: ["feedparser.parse(url, agent=UA) por feed em try/except (Pitfall 3 throttle InfoMoney)", "pubDate struct_time UTC → datetime(*ts[:6], tzinfo=utc).astimezone(ZoneInfo(America/Sao_Paulo)) (Pitfall 6)", "render RSS untrusted como TEXTO (st.markdown sem unsafe_allow_html; nunca components.html com conteúdo do feed) + link_button só https (T-18-06/07/08)", "sort tz-aware homogêneo com datetime.min UTC como chave p/ itens sem data"]

key-files:
  created: []
  modified: [src/analista/core/home_feed.py, app.py, tests/test_home_feed.py]

key-decisions:
  - "A3 (Google News qualidade): no momento da execução (2026-07-01) o InfoMoney respondeu 200/bozo=False mas com 0 entries (comportamento consistente c/ Pitfall 3 — CDN/throttle), então o feed degradou graciosamente e veio 100% do Google News (41 entries → cap 20). A submanchete do Google ECOA o título (description HTML pobre → após strip, resumo≈título); no render, suprimimos o eco (só exibe submanchete quando ela acrescenta) para não duplicar texto. Mantida a query do plano (`when:1d` + termos de mercado/dividendos) — ruído moderado (alguns itens são páginas de cotação tipo 'BBDC4 - ... Cotação'), aceitável; InfoMoney segue sendo a fonte primária de submanchete quando presente. Nenhuma mudança de query necessária."
  - "Resumo (submanchete) limpo de HTML JÁ no home_feed (_texto_limpo: strip de tags + colapso de espaços), não só no render — defesa em profundidade sobre a sanitização do feedparser (T-18-06) e evita mostrar âncoras cruas do Google News."
  - "Link não-https vira string vazia no home_feed (não None) — o render só faz st.link_button quando startswith('https://'); esquema perigoso (javascript:) e http:// são descartados na borda (T-18-07)."
  - "Fragment run_every=600 ≈ TTL=600 do wrapper: o cache process-global é o porteiro real das fontes (poucos hits, respeita o throttle do InfoMoney); o fragment é só o tick visual do auto-refresh."

patterns-established:
  - "noticias() multi-feed never-raise: import tardio de feedparser+zoneinfo (fallback→[]), try/except por feed E por entry, cap ~20/feed, dedupe título normalizado, sort data desc (sem data ao fim)"
  - "Render seguro de conteúdo externo (RSS): título/resumo como TEXTO via st.markdown/st.write (HTML não renderiza por default), fonte/hora via st.caption, navegação externa só via st.link_button com link https (âncora nativa, sem tabnabbing)"

requirements-completed: [NEWS-01, NEWS-02]

# Metrics
duration: ~15min
completed: 2026-07-01
---

# Phase 18 Plan 03: Feed de Notícias da Home Summary

**home_feed.noticias() real (feedparser sobre InfoMoney + Google News BR, User-Agent de browser, try/except por feed, dedupe/sort por data desc, pubDate→America/Sao_Paulo, link só https, resumo texto sem HTML, never-raise) alimenta o bloco de notícias da Home: _noticias() @st.cache_data(ttl=600) process-global + _render_noticias @st.fragment(run_every=600) com render seguro (título via st.markdown texto, st.link_button só https, nunca texto completo) e estado vazio tratado.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-07-01
- **Tasks:** 2 (Task 1 via TDD RED→GREEN)
- **Files modified:** 3 (0 criados, 3 modificados)

## Accomplishments
- **NEWS-01 (fetch):** `home_feed.noticias()` implementada — `feedparser.parse(url, agent=_UA)` sobre InfoMoney (`/mercados/feed/`) + Google News BR (query com `when:1d`), **User-Agent de browser** (Pitfall 3: InfoMoney throttla robô), **try/except por feed** (fonte que cai não derruba as demais) E por entry, cap ~20/feed, `published_parsed` (UTC struct_time) → `datetime` em `America/Sao_Paulo` (Pitfall 6), dedupe por título normalizado (strip+lower), sort por data desc (itens sem data ao fim), **never-raise** (fallback→`[]`). **Firewall D-06 intacto** (só importa `re`/`feedparser`/`datetime`/`zoneinfo` — nenhuma engine).
- **NEWS-01 + NEWS-02 (UI):** bloco de notícias real substituiu o placeholder no `render_home`: wrapper `_noticias` `@st.cache_data(show_spinner=False, ttl=600)` process-global (D-05, porteiro real das fontes), fragment `_render_noticias` `@st.fragment(run_every=600)` (auto-refresh ~10min). **Render seguro (T-18-06):** título via `st.markdown` como TEXTO (sem `unsafe_allow_html`; nunca `components.html` com conteúdo do feed), fonte+hora via `st.caption`, submanchete via `st.write` (suprimindo o eco do Google News), `st.link_button` só quando `link.startswith("https://")` (T-18-07/08, âncora nativa segura). **Nunca reproduz o texto completo** (só manchete/trecho + link — zona segura de copyright). Estado vazio ("sem notícias no momento") tratado sem quebra.
- **Segurança RSS untrusted:** link não-https descartado na borda (`home_feed`), resumo limpo de HTML já no `home_feed` (`_texto_limpo`) — defesa em profundidade sobre o feedparser.
- **7 testes novos** (`tests/test_home_feed.py`) via monkeypatch de `feedparser.parse` (sem rede): contrato+ordenação+TZ, dedupe, feed que cai não derruba, todos falham→[], link só https, item sem data ao fim, resumo texto sem HTML.
- **296 goldens verdes** (283 pré-existentes + 6 de watchlist + 7 novos de notícias) — engine e aba Analisar intactas.
- **Smoke live:** `streamlit run app.py` (headless :8599) sobe **HTTP 200** sem erro no log; `noticias()` ao vivo retornou 20 itens reais com hora BRT e links https.

## Task Commits

Cada tarefa foi commitada atomicamente:

1. **Task 1 (TDD RED): testes falhos de home_feed.noticias** - `7e2a25c` (test)
2. **Task 1 (TDD GREEN): home_feed.noticias real** - `a6e67e3` (feat)
3. **Task 2: bloco de notícias no app.py** - `094f4b7` (feat)

**Plan metadata:** (docs commit final)

## Files Created/Modified
- `src/analista/core/home_feed.py` - corpo de `noticias()`: multi-feed feedparser + `_FEEDS`/`_UA`/`_TZ_B3`/`_texto_limpo`; try/except por feed+entry, dedupe/sort, TZ B3, link https, never-raise (firewall D-06 preservado)
- `app.py` - `_noticias` (cache ttl=600) + `render_home` com fragment `_render_noticias` (run_every=600, render seguro texto + link_button + estado vazio)
- `tests/test_home_feed.py` - 7 testes do contrato never-raise de `noticias` via monkeypatch de `feedparser.parse`

## Decisions Made
- **A3 — Google News dominou nesta execução; eco de título suprimido.** No momento do run (2026-07-01) o InfoMoney respondeu **200 / bozo=False / 0 entries** (consistente com Pitfall 3: CDN/throttle serve payload vazio a "robô"), então o feed **degradou graciosamente** e as 20 manchetes vieram 100% do Google News (41 → cap 20). A submanchete do Google **ecoa o título** (description HTML pobre → após strip vira ≈ título); no render, só exibimos a submanchete quando ela **acrescenta** (não é substring nem igual ao título) para não duplicar texto. **Query mantida** (a do plano, com `when:1d` + termos de mercado/dividendos) — ruído moderado (alguns itens são páginas agregadoras de cotação), aceitável; **InfoMoney segue sendo a fonte primária de submanchete** quando presente. A robustez do never-raise + multi-feed é justamente o que garante a Home sempre populada mesmo com uma fonte vazia.
- **Feeds efetivamente incluídos:** InfoMoney (`https://www.infomoney.com.br/mercados/feed/`) + Google News BR (`https://news.google.com/rss/search?q=mercado+financeiro+bolsa+dividendos+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419`). Ambos com User-Agent de browser e try/except independente.
- **Limpeza de HTML na borda (home_feed), não só no render:** `_texto_limpo` remove tags e colapsa espaços do resumo — defesa em profundidade sobre a sanitização do feedparser (T-18-06) e evita âncoras cruas do Google News aparecerem como texto.
- **Fragment run_every=600 ≈ TTL=600:** o `@st.cache_data` process-global é o porteiro real das fontes (poucos hits, respeita o throttle); o fragment é só o tick visual do auto-refresh (~10min), dentro da faixa NEWS-02 (5–15min).

## Deviations from Plan
None - plan executed exactly as written. A supressão do eco de submanchete do Google News e a limpeza de HTML na borda são refinamentos de qualidade/segurança dentro do escopo do render seguro que o próprio plano pede (título/resumo como texto), não desvios.

## Issues Encountered
- **InfoMoney com 0 entries no run:** 200/bozo=False mas feed vazio (Pitfall 3). Não é bug — o contrato never-raise + multi-feed cobre exatamente esse caso: a Home ficou populada só com Google News. Confirmado por probe direto dos dois feeds.

## Known Stubs
Nenhum. `noticias()` está totalmente implementada e wired ao render; o placeholder ("⏳ Carregando as notícias… em construção") foi removido.

## User Setup Required
None - `feedparser==6.0.12` já estava em `requirements.txt` e instalado no venv desde o plano 01; em outros ambientes basta `pip install -r requirements.txt`.

## Next Phase Readiness
- Notícias funcionais ponta-a-ponta (fetch RSS real + cache compartilhado + fragment + render seguro + estado vazio). Com o plano 02 (watchlist), a Home está completa; falta só o plano 04 (verificação): 283 goldens + engines intactas + smoke no navegador (Home default sem regressão).
- Base do diff de invariância segue válida; os 296 testes (283 goldens + 6 watchlist + 7 notícias) estão verdes.

## Self-Check: PASSED

- FOUND: src/analista/core/home_feed.py
- FOUND: app.py
- FOUND: tests/test_home_feed.py
- FOUND: .planning/phases/18-home-watchlist-noticias/18-03-SUMMARY.md
- FOUND: commit 7e2a25c (Task 1 RED)
- FOUND: commit a6e67e3 (Task 1 GREEN)
- FOUND: commit 094f4b7 (Task 2)

---
*Phase: 18-home-watchlist-noticias*
*Completed: 2026-07-01*
