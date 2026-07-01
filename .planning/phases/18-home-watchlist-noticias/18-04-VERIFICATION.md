---
phase: 18-home-watchlist-noticias
verified: 2026-07-01T18:33:45Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 18: Home — Watchlist + Notícias Verification Report

**Phase Goal:** O app ganha uma página inicial (landing default) que mostra (1) uma watchlist de até ~5 tickers escolhidos pelo usuário — cotação auto-atualizável (~30–60s) com efeito visual de alta/baixa e aviso de atraso (~15min) — e (2) um feed de notícias do mercado financeiro (manchete + submanchete + fonte + horário, clique abre o site original). Custo-zero, cache compartilhado no servidor, engines fundamentalista/técnica e os 283 goldens intactos.

**Verified:** 2026-07-01T18:33:45Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Home é a primeira tela (landing default); os 4 menus atuais continuam acessíveis, comportamento inalterado | ✓ VERIFIED | `app.py:377-383` — `"🏠 Início"` é o 1º item do radio stateless (sem `key=`/`index=`), tornando-se default automaticamente. `app.py:581` roteia com `if modo.startswith("🏠")` como bloco isolado ANTES da cadeia `if/elif` original (linha 588-1049) dos 4 menus. Diff de `app.py` contra a base (`git diff $BASE..HEAD -- app.py`) mostra **189 insertions / 1 deletion** — a única deleção é a linha do array de opções do radio, substituída apenas para prepender o novo item; o texto dos 4 menus existentes é idêntico. |
| 2 | Watchlist parte de lista default (~5 tickers), editável, persiste via `localStorage`; cada item mostra preço + variação do dia colorida | ✓ VERIFIED | `home_feed.py:24` `DEFAULT_WATCHLIST = ("BBSE3","TAEE11","EGIE3","ITUB4","BBAS3")`; `app.py:442-459 _seed_watchlist` lê `ls.getItem(_WATCHLIST_KEY)` (streamlit-local-storage) com fallback para os defaults; `app.py:495-519` editor (add validado por `validar_ticker` + teto `MAX_WATCHLIST=5`, remove) persiste via `_persistir_watchlist` → `ls.setItem`. `app.py:533-537` `col.metric(..., delta=f"{item['pct']*100:+.2f}%")` — Streamlit colore automaticamente (verde alta / vermelho baixa). Confirmado ao vivo: `streamlit run app.py` retornou HTTP 200 sem erros de console (smoke rodado nesta verificação, porta 8599). |
| 3 | Cotações atualizam sozinhas (~30–60s) com efeito visual e aviso de atraso ~15min; fetch usa cache compartilhado no servidor (1 chamada por conjunto por intervalo), degrada sem quebrar se um ticker falhar | ✓ VERIFIED | `app.py:404-413 _cotacoes` — `@st.cache_data(show_spinner=False, ttl=45)` process-global (chave `tuple(sorted(tickers))`); `app.py:523 @st.fragment(run_every=45)` re-roda só o bloco a cada 45s. `home_feed.py:99-107` faz **UMA** `yf.download` em lote (não um loop por ticker) — confirmado pelo teste `test_cotacoes_uma_unica_chamada_em_lote` (`tests/test_home_feed.py:73-85`, `assert len(contador)==1`). `app.py:541` selo `"⏱️ Cotações Yahoo com ~15min de atraso (best-effort)"` sempre visível. Degradação por item: `home_feed.py:112-120` cada ticker em `try/except` próprio → `ok=False` sem derrubar a lista; UI trata (`app.py:538-539` `col.metric(label=item["ticker"], value="—")`); coberto por `test_cotacoes_degrada_por_item` e `test_cotacoes_download_falha_never_raise`. |
| 4 | Feed de notícias lista manchete + submanchete + fonte + horário de RSS abertos (InfoMoney + Google News BR); clique abre o site original em nova aba, nunca reproduz texto completo | ✓ VERIFIED | `home_feed.py:40-45 _FEEDS` = InfoMoney (`/mercados/feed/`) + Google News BR RSS; `home_feed.py:152-171 noticias()` popula `fonte/titulo/resumo/link/quando` por entry, com `_texto_limpo` removendo HTML do resumo. `app.py:560-573` renderiza título via `st.markdown` (texto puro, sem `unsafe_allow_html`), fonte+hora via `st.caption` (`f"{it['fonte']} · {quando:%d/%m %H:%M}"`), submanchete via `st.write` só quando não é eco do título, e `st.link_button("Abrir no site ↗", it["link"])` só se `link.startswith("https://")`. `st.link_button` (Streamlit 1.58, confirmado via `help()`) abre **nova aba** por padrão — satisfaz "abre em nova aba" sem `st.markdown` de HTML customizado (evita tabnabbing). Apenas manchete + trecho são exibidos — nunca o corpo completo (o RSS não traz o corpo completo de qualquer forma). |
| 5 | Feed auto-atualiza (~5–15min) com cache compartilhado, degrada sem quebrar se uma fonte cair, zero dependência paga; 283 goldens seguem verdes e engines intactas | ✓ VERIFIED | `app.py:416-425 _noticias` — `@st.cache_data(ttl=600)` process-global; `app.py:549 @st.fragment(run_every=600)` (~10min, dentro da faixa 5–15min). `home_feed.py:152-157` cada feed em `try/except` independente — fonte que cai é pulada sem derrubar as demais (`test_noticias_feed_que_cai_nao_derruba`, `test_noticias_todos_falham_lista_vazia` → `[]`). Zero API paga (só RSS público via `feedparser`). **283 goldens + 13 novos = 296 passed** (`pytest -q`, rodado nesta verificação: `296 passed in 3.00s`). **Engines intactas**: `git diff --name-only $BASE..HEAD -- src/analista/report src/analista/core/indicators.py src/analista/core/multiples.py src/analista/core/screening.py src/analista/grafico.py` → **vazio** (rodado nesta verificação). |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/home_feed.py` | Módulo read-only, never-raise, contrato `cotacoes()`/`noticias()`, firewall D-06 | ✓ VERIFIED | 185 linhas, implementação completa (não esqueleto). Only imports at module top: `re`, `__future__`. Late imports: `..ingest.prices`, `feedparser`, `datetime`, `zoneinfo` — nenhum import de `report`/`build`/`indicators`/`multiples`/`screening`/`comparables`/`grafico` (grep confirmado, nenhuma ocorrência). |
| `app.py` (render_home + fragments) | Landing default, watchlist + notícias thin renderer | ✓ VERIFIED | `render_home` (linhas 473-578) sem `indicators.calcular(`, `montar_setup(`, `montar_empresa(` ou qualquer chamada de engine (grep confirmado dentro do range exato do corpo da função). Radio, cache wrappers, fragments, editor e render seguro todos presentes e funcionais. |
| `tests/test_home_feed.py` | Testes substantivos do contrato never-raise | ✓ VERIFIED | 267 linhas, 13 testes (`test_cotacoes_*` x6, `test_noticias_*` x7) via monkeypatch (sem rede), cobrindo contrato, lote único, degradação por item, never-raise, dedupe, sort/TZ, links https-only, HTML stripping. Assertions substantivas (não `assert True`/tautologias). |
| `requirements.txt` | Deps novas pinadas | ✓ VERIFIED | `feedparser==6.0.12` + `streamlit-local-storage==0.0.25`, ambas instaladas e importáveis no venv (confirmado nesta verificação). |
| `.planning/phases/18-home-watchlist-noticias/.phase-base-sha` | SHA-base fixo para diff de invariância | ✓ VERIFIED | Contém SHA de 40 chars válido (`5ae519034dce6cd3685e39b13ffd5ac19b070fd1`), `git cat-file -t` confirma que é um commit válido no histórico. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `app.py` render_home | `home_feed.cotacoes()` | `_cotacoes` cache wrapper + fragment | WIRED | `app.py:526 dados = _cotacoes(tickers)`; resultado renderizado em `col.metric` (linhas 530-539). |
| `app.py` render_home | `home_feed.noticias()` | `_noticias` cache wrapper + fragment | WIRED | `app.py:551 itens = _noticias()`; resultado renderizado em loop `st.markdown`/`st.caption`/`st.link_button` (linhas 560-574). |
| `app.py` editor | `streamlit-local-storage` | `_watchlist_ls`/`_seed_watchlist`/`_persistir_watchlist` | WIRED | Add/remove chamam `_persistir_watchlist(ls)` (linhas 510, 518) que executa `ls.setItem(...)`; `_seed_watchlist` lê `ls.getItem(...)` no 1º load. |
| Radio dispatcher | `render_home()` | `if modo.startswith("🏠")` | WIRED | `app.py:581-582`, bloco isolado antes da cadeia `if/elif` original — não interfere nos 4 menus (confirmado por diff aditivo). |
| `home_feed.cotacoes` | `ingest.prices` | import tardio `from ..ingest import prices` | WIRED | `home_feed.py:93` — reusa `yahoo_symbol`/`_yf` já validados na Fase de swing, sem duplicar lógica de resolução `.SA`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `_render_watchlist` fragment | `dados` | `_cotacoes(tickers)` → `home_feed.cotacoes()` → `yf.download` em lote real | Sim — chamada real ao Yahoo Finance, não estática | ✓ FLOWING |
| `_render_noticias` fragment | `itens` | `_noticias()` → `home_feed.noticias()` → `feedparser.parse` sobre feeds RSS reais | Sim — parse real de InfoMoney/Google News, não estático/vazio hardcoded | ✓ FLOWING |
| Watchlist editor | `wl` (session_state) | `_seed_watchlist` (localStorage ou `DEFAULT_WATCHLIST`) | Sim — lista real do usuário, com fallback funcional | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suite de testes (283 goldens + 13 novos) | `.venv/bin/python -m pytest -q` | `296 passed in 3.00s` | ✓ PASS |
| Diff de invariância das engines | `git diff --name-only $BASE..HEAD -- src/analista/report src/analista/core/indicators.py src/analista/core/multiples.py src/analista/core/screening.py src/analista/grafico.py` | (vazio) | ✓ PASS |
| Firewall D-06 (home_feed sem import de engine) | grep de imports em `home_feed.py` | só `re`, `__future__`, `..ingest.prices` (tardio), `feedparser`/`datetime`/`zoneinfo` (tardio) | ✓ PASS |
| Home thin renderer (sem recálculo de método) | grep de `indicators.calcular(`/`montar_setup(`/`montar_empresa(` no corpo de `render_home` (app.py:473-578) | nenhuma ocorrência | ✓ PASS |
| App sobe sem erro | `streamlit run app.py --server.headless true --server.port 8599` + `curl -o /dev/null -w "%{http_code}"` | `200`, sem erros no log | ✓ PASS |
| Deps novas instaladas e pinadas | `python -c "import streamlit_local_storage, feedparser"` + grep `requirements.txt` | ambas importam; `feedparser==6.0.12` + `streamlit-local-storage==0.0.25` pinadas | ✓ PASS |
| `st.link_button` abre nova aba por padrão | `help(st.link_button)` (Streamlit 1.58) | docstring confirma: "When clicked, a new tab will be opened to the specified URL" | ✓ PASS |
| Diff app.py é puramente aditivo (4 menus inalterados) | `git diff --stat $BASE..HEAD -- app.py` | `189 insertions(+), 1 deletion(-)` — a única deleção é a linha do array de opções do radio (substituída para prepender item) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| HOME-01 | 18-01-PLAN.md | Home landing default, aditiva, 4 menus inalterados | ✓ SATISFIED | Radio 1º item + branch isolado; diff aditivo confirmado |
| WATCH-01 | 18-02-PLAN.md | Watchlist ~5 tickers, default editável, persiste localStorage | ✓ SATISFIED | `DEFAULT_WATCHLIST`, editor com teto, `streamlit-local-storage` bidirecional |
| WATCH-02 | 18-02-PLAN.md | Preço+variação colorida, auto-refresh ~30-60s, cache compartilhado, degrada por item | ✓ SATISFIED | `st.metric` colorido, fragment 45s, cache ttl=45 em lote, degradação testada |
| NEWS-01 | 18-03-PLAN.md | Feed manchete+submanchete+fonte+horário, link nova aba, nunca texto completo | ✓ SATISFIED | Render seguro via `st.markdown`/`st.caption`/`st.link_button` (https-only) |
| NEWS-02 | 18-03-PLAN.md | Auto-refresh ~5-15min, cache compartilhado, degrada por fonte, custo-zero | ✓ SATISFIED | Fragment 600s, cache ttl=600, try/except por feed, só RSS gratuito |

Nenhum requisito órfão encontrado em `.planning/REQUIREMENTS.md` para Phase 18 além dos 5 já mapeados e reivindicados pelos planos.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `app.py` | 478 | Docstring de `render_home()` ainda diz "*O bloco de notícias segue placeholder até o plano 03*" — texto obsoleto do plano 02, não atualizado após o plano 03 substituir o placeholder por implementação real | ℹ️ Info | Não afeta comportamento (código funcional, só a docstring está desatualizada). Não é um debt-marker formal (TODO/FIXME/TBD), é prosa descritiva desalinhada com o estado atual. Não bloqueia o gate. |

Nenhum `TODO`/`FIXME`/`TBD`/`XXX`/`HACK`/`PLACEHOLDER` funcional encontrado nos arquivos modificados pela fase (`home_feed.py`, `app.py` linhas 377-578, `tests/test_home_feed.py`). Nenhum handler vazio, nenhum `return []`/`return {}` não justificado por never-raise contract, nenhuma prop hardcoded vazia no caminho de render.

### Human Verification Required

Nenhum item pendente de verificação humana automatizada — smoke visual já foi executado e aprovado pelo usuário conforme `18-04-SUMMARY.md` (2026-07-01, Claude-in-Chrome, `http://localhost:8501`, observado: Home default, watchlist com 5 tickers + cores + selo, editor presente, notícias com manchete/fonte/hora BR + botão "Abrir no site", não-regressão dos 4 menus). Esta verificação re-executou de forma independente os checks automatizados (pytest, diff de engines, firewall, smoke HTTP) e confirmou os mesmos resultados sem depender do relato do SUMMARY.

Itens não exercitados nem no smoke original nem nesta verificação automatizada (requerem interação humana real no navegador, fora do escopo de checks programáticos):
1. **Persistência cross-reload do localStorage** — comportamento de escrita/leitura do `streamlit-local-storage` através de um reload real de página (fechar/reabrir aba) não foi testado ao vivo; coberto apenas indiretamente pelos testes unitários de `home_feed` (que não tocam o bridge JS) e pela leitura de código do bridge em `app.py:428-470`.
2. **Tick visual do auto-refresh (~45s/~600s)** — o fragment `run_every` foi confirmado por leitura de código e smoke de subida (HTTP 200), mas o comportamento de "a cada 45s a tela pisca e atualiza sozinha sem interação" não foi observado em tempo real nesta verificação (só na aprovação humana do plano 04, já registrada).

Estes dois pontos já foram observados/aprovados no smoke humano documentado em `18-04-SUMMARY.md`; não são reabertos como gaps — apenas registrados como fora do escopo de re-verificação automatizada desta rodada.

### Gaps Summary

Nenhum gap bloqueante encontrado. Todos os 5 critérios de sucesso do ROADMAP e os 5 requisitos (HOME-01, WATCH-01, WATCH-02, NEWS-01, NEWS-02) foram verificados com evidência direta no código (não apenas nas alegações do SUMMARY.md), incluindo:
- Reexecução independente da suíte de testes (296 passed).
- Reexecução independente do diff de invariância das engines (vazio).
- Inspeção manual do firewall D-06 e do corpo de `render_home` linha a linha.
- Smoke HTTP real do app (`streamlit run` → 200, sem erros de console).
- Leitura completa dos 13 testes novos, confirmando que exercitam degradação real (não apenas caminho feliz).

O único achado é um item informativo (docstring desatualizada em `app.py:478`), sem impacto funcional — não é um gap de goal achievement.

---

_Verified: 2026-07-01T18:33:45Z_
_Verifier: Claude (gsd-verifier)_
