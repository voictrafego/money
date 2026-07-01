---
phase: 18-home-watchlist-noticias
plan: 04
subsystem: verification
tags: [acceptance, goldens, engines-intactas, smoke-navegador, claude-in-chrome, home]

# Dependency graph
requires:
  - phase: 18-01-esqueleto-home
    provides: "Home landing default + home_feed contrato + .phase-base-sha (base fixa do diff de invariância)"
  - phase: 18-02-watchlist
    provides: "watchlist real (cotações + fragment + editor localStorage + metric colorido + selo de atraso)"
  - phase: 18-03-noticias
    provides: "feed de notícias real (RSS InfoMoney + Google News, render seguro, link em nova aba)"
provides:
  - "Gate de aceite consolidado da Phase 18 (HOME-01/WATCH-01/WATCH-02/NEWS-01/NEWS-02): goldens verdes + engines intactas + Home thin renderer + smoke humano aprovado"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: ["diff de invariância contra SHA-base FIXO da fase (nunca HEAD~N) p/ provar engines intactas", "smoke humano via Claude-in-Chrome como gate blocking de checkpoint"]

key-files:
  created: [.planning/phases/18-home-watchlist-noticias/18-04-SUMMARY.md]
  modified: []

key-decisions:
  - "O heurístico awk do <verify> automatizado da Task 1 acusou FAIL_RECALC_HOME — FALSO POSITIVO: render_home é o ÚLTIMO `def` de app.py, então o awk mantém o flag ligado e captura o dispatch de módulo (branch Swing em app.py:1120-1121, indicators.calcular/montar_setup). Verificação manual delimitou o corpo real de render_home (app.py:473..580, até o 1º statement em coluna 0 `if modo.startswith(\"🏠\")` na linha 581) e confirmou ZERO chamadas de recálculo no caminho da Home. Home é comprovadamente thin renderer."
  - "pytest reporta 296 passed (não 283): os 283 goldens originais seguem verdes + 6 testes de watchlist (18-02) + 7 de notícias (18-03). O gate 'engines intactas' é provado pelo diff vazio contra a base, não pela contagem de testes."

# Verification results
automated:
  pytest: "296 passed in ~3s (283 goldens intactos + 13 novos home_feed) — zero regressão"
  engines_diff: "git diff --name-only 5ae5190..HEAD -- report/ indicators.py multiples.py screening.py grafico.py → VAZIO (engines não tocadas)"
  firewall_d06: "home_feed.py sem import de report/build/indicators/multiples/screening/comparables/grafico (só re, __future__, prices tardio)"
  home_thin: "corpo de render_home (473..580) sem indicators.calcular( / montar_setup( / montar_empresa("
human_smoke:
  status: "APROVADO pelo usuário (2026-07-01)"
  app: "streamlit run app.py :8501 → HTTP 200, sem console errors"
  observado:
    - "🏠 Início é o 1º item do radio e a tela default (sem clicar em nada)"
    - "Watchlist: 5 tickers default (BBAS3/BBSE3/EGIE3/ITUB4/TAEE11) com preço + variação do dia COLORIDA (verde ↑ / vermelho ↓) e selo '~15min de atraso'"
    - "Editor 'Editar watchlist' presente (add validado + teto 5 / remove)"
    - "Notícias: manchete + fonte + horário em fuso BR (ex.: 'Google News · 01/07 15:07') + submanchete + botão 'Abrir no site ↗'"
    - "Não-regressão: menu 'Analisar uma ação' inalterado (input Ticker + botão Analisar); demais menus presentes no radio"
  nao_exercitado_no_smoke:
    - "Persistência localStorage cross-reload, tick de auto-refresh ~45s e abertura do link em nova aba não foram exercidos ao vivo no smoke; cobertos pelos 13 testes unitários novos e presentes no render."
---

# Plan 18-04 — Verificação de Aceite da Phase 18

Gate de aceite consolidado da Home (HOME-01/WATCH-01/WATCH-02/NEWS-01/NEWS-02).

## Task 1 — Verificação automatizada (PASS)

- **Goldens:** `296 passed` — os 283 goldens originais intactos + 13 novos (6 watchlist + 7 notícias). Zero regressão.
- **Engines intactas:** `git diff --name-only 5ae5190..HEAD` restrito a `report/`, `indicators.py`, `multiples.py`, `screening.py`, `grafico.py` → **vazio**. As engines fundamentalista/técnica não foram tocadas na fase.
- **Firewall D-06:** `home_feed.py` não importa nenhuma engine (só `re`, `__future__`, `prices` por import tardio).
- **Home thin renderer:** `render_home` (app.py:473–580) sem `indicators.calcular(`, `montar_setup(` ou `montar_empresa(`. O `FAIL_RECALC_HOME` do `<verify>` do plano foi falso positivo (render_home é o último `def`, o awk capturou o dispatch de módulo Swing em app.py:1120).

## Task 2 — Smoke no navegador (Claude-in-Chrome) — APROVADO

App em `http://localhost:8501` (HTTP 200, sem console errors). Confirmado visualmente:
- 🏠 Início como landing default (1º item do radio, pré-selecionado).
- Watchlist com preço + variação do dia colorida e selo de atraso ~15min.
- Feed de notícias com manchete/fonte/horário BR + link "Abrir no site".
- Não-regressão do menu "Analisar uma ação" e presença dos 4 menus.

**Resultado:** usuário aprovou o aceite. Phase 18 pronta para fechar.

## Self-Check: PASSED
