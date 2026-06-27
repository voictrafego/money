---
phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
plan: 02
subsystem: ui
tags: [glossario, tooltips, technical-analysis, pytest, ui-05, ui-06]

# Dependency graph
requires:
  - phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
    provides: "07-CONTEXT decisão UI-05 (reusar h() de glossario.py) + UI-06 (linguagem consultiva)"
provides:
  - "11 chaves tec_* em glossario.G (intro/mm/cross/donchian/bollinger/squeeze/rsi/macd/adx/regressao/timing) acessíveis por h()"
  - "Contrato travado por tests/test_glossario.py: existência das chaves + proibição de linguagem de ordem (compre/venda)"
affects: [controles-tecnicos-app, tooltips-secao-tecnica]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tooltips técnicos centralizados em glossario.G, lidos via help=h('tec_*') no app.py (paridade com o glossário fundamentalista)"
    - "Contrato de UI (chaves de tooltip + tom consultivo) travado por teste com lista canônica como fonte da verdade"

key-files:
  created:
    - tests/test_glossario.py
  modified:
    - src/analista/glossario.py

key-decisions:
  - "Lista canônica das 11 chaves tec_* definida no próprio teste (fonte da verdade do contrato com o Plan 04)."
  - "Proibição reforça tom consultivo via substrings 'compre'/'venda'; 'comprar'/'vender' (negados) permanecem permitidos por não conterem essas substrings exatas."

patterns-established:
  - "Glossário técnico segue o estilo das chaves existentes: markdown curto, termo em negrito, fala de timing/força/tendência e reverificação dos fundamentos, nunca ordem de operação."

requirements-completed: [UI-05]

# Metrics
duration: ~6min
completed: 2026-06-27
tasks: 2
files: 2
---

# Phase 7 Plan 02: Glossário dos indicadores técnicos Summary

Adiciona ao glossário (`glossario.G`) as 11 definições consultivas dos indicadores técnicos novos (médias móveis, cruzamentos, Donchian, Bollinger, squeeze, RSI, MACD, ADX, regressão e resumo de timing), acessíveis por `h('tec_*')`, com um teste de contrato que trava a existência das chaves e o tom consultivo (proíbe "compre"/"venda").

## What Was Built

- **Task 1** — 11 chaves `tec_*` no dict `G` de `glossario.py`, no mesmo estilo das chaves fundamentalistas (markdown curto, termo em negrito). Tom obrigatório consultivo: falam de timing, força, tendência e "reverificar os fundamentos"; nunca "compre/venda". Cobrem todos os indicadores exibíveis da seção técnica.
- **Task 2** — `tests/test_glossario.py` com dois testes: `test_chaves_tec_presentes` (todas as 11 chaves devolvem texto não-vazio) e `test_tom_consultivo` (nenhum valor `tec_*` contém "compre"/"venda", case-insensitive). A lista canônica de chaves vive no teste como fonte da verdade do contrato.

## How It Works

`app.py` (Plan 04 da seção técnica) passará `help=h('tec_<indicador>')` em cada controle/indicador, lendo o texto centralizado em `glossario.G` — mesma camada fina já usada pelo glossário fundamentalista. O teste de contrato falha se uma chave for removida ou se algum texto introduzir linguagem de ordem, travando UI-05 (tooltip por indicador) e UI-06 (enquadramento consultivo).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Texto inicial de `tec_bollinger` violava o critério de aceite consultivo**
- **Found during:** Task 1 (verificação automatizada)
- **Issue:** A frase "sem virar ordem de compra ou venda" continha a substring proibida "venda", fazendo a própria asserção de aceite falhar.
- **Fix:** Reescrita para "referência consultiva, nunca uma ordem de operação".
- **Files modified:** src/analista/glossario.py
- **Commit:** a7ab886

## Verification

- `./.venv/bin/python -c "...assert all(h(k) for k in ks)..."` → `ok 11`
- `./.venv/bin/python -m pytest tests/test_glossario.py -x -q` → 2 passed
- Suíte completa: `pytest -q` → 138 passed (sem regressão; invariante TEST-07 preservada)

## Self-Check: PASSED

- FOUND: src/analista/glossario.py (11 chaves tec_*)
- FOUND: tests/test_glossario.py
- FOUND commit a7ab886 (feat Task 1)
- FOUND commit 512b445 (test Task 2)
