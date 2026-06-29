---
phase: 12-ingest-o-intraday-timeframe
plan: 02
subsystem: ui-cache
tags: [streamlit, cache, intraday, nonce, swing]
requires:
  - "analista.ingest.intraday.coletar_intraday (Plan 12-01)"
provides:
  - "app.py frame_intraday(ticker, timeframe, nonce) — contrato de cache intraday (TTL 300s)"
  - "app.py _nonce_key(ticker, timeframe) — chave de session_state do nonce por par"
affects:
  - "Fase 16 (botão Atualizar da página de swing consome frame_intraday + _nonce_key)"
tech-stack:
  added: []
  patterns:
    - "wrapper @st.cache_data(ttl=300) com nonce só na chave (invalidação targetada, sem clear global)"
    - "import tardio do módulo intraday dentro da função (isola import pesado)"
key-files:
  created: []
  modified:
    - "app.py (+19 linhas: frame_intraday + _nonce_key, junto aos wrappers de cache existentes)"
decisions:
  - "nonce entra SÓ na chave de cache — nunca repassado a coletar_intraday (a engine não o conhece)"
  - "TTL 300s (curto), distinto do 3600 dos wrappers fundamentalistas — refresh intraday best-effort"
  - "D-08 travado: zero st.cache_data.clear() em app.py — cache da aba Analisar intacto"
metrics:
  duration: "~4 min"
  completed: "2026-06-29"
  tasks: 1
  files: 1
---

# Phase 12 Plan 02: Contrato de cache intraday em app.py Summary

Wrapper de cache `frame_intraday(ticker, timeframe, nonce)` (TTL 300s) + helper `_nonce_key` adicionados a `app.py`, entregando o contrato de cache intraday com invalidação targetada por nonce — sem nenhum `.clear()` global que apagaria o cache da aba Analisar.

## O que foi feito

Modificação thin em `app.py`, junto aos wrappers de cache existentes (`montar`/`selic_atual`/`rf_capm`):

- **`frame_intraday(ticker, timeframe, nonce)`** decorado com `@st.cache_data(show_spinner=False, ttl=300)`. Corpo: import tardio `from analista.ingest import intraday` e `return intraday.coletar_intraday(ticker, timeframe)`. O `nonce` entra **apenas na assinatura/chave de cache** — não é repassado à engine. Incrementá-lo (botão Atualizar da Fase 16) cria nova entrada só para aquele par `(ticker, timeframe)`; a antiga expira pelo TTL.
- **`_nonce_key(ticker, timeframe)`** retorna `f"nonce_intraday::{ticker}::{timeframe}"` — chave de `st.session_state` por par, que o botão Atualizar vai incrementar.

Anti-pattern D-08 respeitado: nenhum `st.cache_data.clear()` em `app.py`. `app.py` permanece read-only quanto à engine (toda lógica em `intraday.py`).

## Verificação

- `.venv/bin/python -m py_compile app.py` → exit 0.
- `grep -v '^[[:space:]]*#' app.py | grep -c 'cache_data\.clear'` → **0** (firewall do cache da aba Analisar).
- `grep -c 'cache_data\.clear' app.py` (arquivo inteiro) → 0.
- `def frame_intraday`, `def _nonce_key`, `ttl=300`, `intraday.coletar_intraday(` todos presentes.
- `.venv/bin/python -m pytest -q` → **202 passed** (sem regressão; engine fundamentalista e 191 goldens intactos).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Literal `st.cache_data.clear()` na docstring quebrava o gate de aceite**
- **Found during:** Task 1 (verificação automatizada)
- **Issue:** A docstring de `frame_intraday` mencionava o literal `st.cache_data.clear()` para documentar o anti-pattern. O gate `grep -v '^[[:space:]]*#' | grep -c 'cache_data\.clear'` filtra apenas linhas de comentário `#`, não docstrings — então a menção era contada como 1 ocorrência, falhando o critério `== 0`.
- **Fix:** Reescrita a docstring para "nunca um clear global" (sem o literal proibido), preservando o sentido.
- **Files modified:** app.py
- **Commit:** 34e08cc

## Self-Check: PASSED

- FOUND: app.py contém `def frame_intraday` e `def _nonce_key`
- FOUND: commit 34e08cc
- FOUND: 12-02-SUMMARY.md
