---
phase: 18-home-watchlist-noticias
plan: 01
subsystem: ui
tags: [streamlit, feedparser, streamlit-local-storage, yfinance, radio, home, watchlist, rss]

# Dependency graph
requires:
  - phase: 17-modo-trading
    provides: "padrões app.py (radio dispatcher, @st.cache_data process-global, @st.fragment, bridge localStorage) reusados aditivamente"
provides:
  - "Opção '🏠 Início' como 1º item do radio (landing default, stateless) — HOME-01"
  - "render_home() thin no dispatch de app.py (2 blocos placeholder: watchlist + notícias)"
  - "core/home_feed.py read-only never-raise: contrato cotacoes()/noticias() + DEFAULT_WATCHLIST/MAX_WATCHLIST/validar_ticker (firewall D-06)"
  - "deps novas pinadas: feedparser==6.0.12 + streamlit-local-storage==0.0.25 (A2 validada)"
  - ".phase-base-sha (5ae5190) — base fixa do diff de invariância dos goldens/engines no plano 04"
affects: [18-02-watchlist, 18-03-noticias, 18-04-verificacao]

# Tech tracking
tech-stack:
  added: [feedparser==6.0.12, streamlit-local-storage==0.0.25]
  patterns: ["home_feed firewall D-06 (módulo read-only sem import de engine)", "contrato never-raise espelhando FrameOHLC/coletar_mercado", "landing default via 1º item do radio stateless (sem index=)"]

key-files:
  created: [src/analista/core/home_feed.py, .planning/phases/18-home-watchlist-noticias/.phase-base-sha]
  modified: [app.py, requirements.txt]

key-decisions:
  - "A2 validada: streamlit-local-storage==0.0.25 importa contra streamlit 1.58 (py3.14) — dep adicionada; NÃO será usado fallback session_state-only no plano 02"
  - "Home é o 1º item do radio (stateless, sem key=/index=) → vira default automaticamente sem migração de estado"
  - "st.title/st.caption e sidebar de Selic/aviso permanecem globais (não movidos para dentro dos branches)"
  - "Deps novas pinadas exato (single-maintainer / feed volátil), diferente do >= das deps de runtime existentes"

patterns-established:
  - "Firewall D-06: home_feed.py read-only, zero import de report/build/indicators/multiples/screening/comparables/grafico (nem tardio)"
  - "Contrato never-raise: cotacoes()/noticias() sempre retornam list, degradam por item, nunca raise"
  - "Landing default aditiva: novo branch modo.startswith('🏠') ANTES do branch Analisar; 4 branches existentes idênticos"

requirements-completed: [HOME-01]

# Metrics
duration: ~8min
completed: 2026-07-01
---

# Phase 18 Plan 01: Esqueleto da Home (landing default) Summary

**Home vira a landing default do app (1º item do radio, stateless) roteando para render_home() thin, com core/home_feed.py read-only expondo o contrato never-raise cotacoes()/noticias() (firewall D-06) e as deps novas (feedparser + streamlit-local-storage) pinadas e validadas.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-07-01T14:58Z (aprox.)
- **Completed:** 2026-07-01T15:05Z (aprox.)
- **Tasks:** 2
- **Files modified:** 4 (2 criados, 2 modificados)

## Accomplishments
- **HOME-01 satisfeito:** "🏠 Início" é o 1º item do radio → vira o default automaticamente (radio stateless, sem `key=`/`index=`); os 4 menus (Analisar/Garimpar/Ranking/Swing) continuam idênticos.
- **core/home_feed.py criado** (read-only, never-raise, firewall D-06): `cotacoes(tickers)`/`noticias()` retornam `list` sem levantar; `DEFAULT_WATCHLIST` (BBSE3/TAEE11/EGIE3/ITUB4/BBAS3), `MAX_WATCHLIST==5`, `validar_ticker` (defesa V5, `^[A-Z0-9]{4,6}$`).
- **Deps novas pinadas e A2 decidida:** feedparser==6.0.12 e streamlit-local-storage==0.0.25 no requirements.txt; A2 validada (LocalStorage importa contra streamlit 1.58).
- **.phase-base-sha gravado** (5ae5190) como base fixa do diff de invariância do plano 04.
- **283 goldens verdes** — scaffold não regride a engine nem a aba Analisar.

## Task Commits

Cada tarefa foi commitada atomicamente:

1. **Task 1: Fixar SHA-base + deps novas (validar A2)** - `8334159` (chore)
2. **Task 2: core/home_feed.py + roteamento Home no app.py** - `2158741` (feat)

## Files Created/Modified
- `.planning/phases/18-home-watchlist-noticias/.phase-base-sha` - SHA-base fixo da fase (5ae5190) para o diff de invariância do plano 04
- `requirements.txt` - `feedparser==6.0.12` + `streamlit-local-storage==0.0.25` (pin exato)
- `src/analista/core/home_feed.py` - módulo agregador read-only never-raise (esqueleto dos contratos cotacoes/noticias; firewall D-06)
- `app.py` - "🏠 Início" como 1º item do radio + `render_home()` thin + branch `modo.startswith("🏠")` antes do branch Analisar

## Decisions Made
- **A2 (streamlit-local-storage × streamlit 1.58):** import de `LocalStorage` OK → dep adicionada ao requirements.txt. O plano 02 usará o pacote para persistência cross-session (não o fallback session_state-only). O warning "missing ScriptRunContext" no teste é benigno (execução em bare mode, fora de uma sessão Streamlit).
- **Home = 1º item do radio (stateless):** o radio não tem `key=`, então prepender o item o torna default sem `index=` e sem migração de estado.
- **Globais preservados:** `st.title`/`st.caption` e a sidebar de Selic/aviso continuam rodando sempre (não movidos), conforme discrição do plano.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
- O grep de firewall pelo padrão de nomes de engine casou a linha 9 (docstring que descreve o próprio firewall), não um import. Reverificado com grep de linhas `^\s*(import|from)` + grep específico por `(import|from).*(engine)` → confirmado: home_feed.py só importa `re` e `__future__`. Firewall D-06 intacto.

## User Setup Required
None - as deps foram instaladas no venv local; em outros ambientes basta `pip install -r requirements.txt`.

## Next Phase Readiness
- Contratos `cotacoes()`/`noticias()` e o roteamento existem → plano 02 preenche o corpo do fetch Yahoo (watchlist) e plano 03 o parse RSS (notícias).
- streamlit-local-storage disponível para a persistência da watchlist (plano 02).
- .phase-base-sha pronto para o diff de invariância do plano 04.

## Self-Check: PASSED

- FOUND: src/analista/core/home_feed.py
- FOUND: .planning/phases/18-home-watchlist-noticias/.phase-base-sha
- FOUND: commit 8334159 (Task 1)
- FOUND: commit 2158741 (Task 2)

---
*Phase: 18-home-watchlist-noticias*
*Completed: 2026-07-01*
