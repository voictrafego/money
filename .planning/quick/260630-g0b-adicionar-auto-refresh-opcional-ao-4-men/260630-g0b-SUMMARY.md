---
phase: quick-260630-g0b
plan: 01
subsystem: app-streamlit-swing
tags: [streamlit, swing-trade, auto-refresh, st-fragment, intraday]
requires: [frame_intraday (TTL=300s), _nonce_key, _TF_MAP, indicators.calcular, setup.montar_setup, grafico.*]
provides: "Auto-refresh opcional no 4º menu (Swing trade) via st.fragment(run_every=...)"
affects: [app.py]
tech-stack:
  added: []          # zero dependência nova — st.fragment é nativo do Streamlit 1.58.0
  patterns: [st.fragment(run_every=...) p/ re-render isolado de bloco; controles fora do fragment como "tick visual"]
key-files:
  created: []
  modified: [app.py]
decisions:
  - "run_every é o tick VISUAL; o tick de DADOS continua sendo o TTL=300s de frame_intraday — auto-refresh NÃO incrementa o nonce."
  - "Controles (toggle/intervalo) ficam FORA do fragment: mexer neles dispara rerun completo que re-decora o fragment com o novo run_every."
  - "Fragment engloba fetch + figura + selo de atraso + card de veredito (snapshot coerente), não só fetch+figura."
metrics:
  duration: ~6 min
  completed: 2026-06-30
---

# Quick Task 260630-g0b: Auto-refresh opcional no 4º menu (Swing trade) Summary

Auto-refresh OPCIONAL na aba Swing trade via `st.fragment(run_every=...)` (nativo, zero dependência): toggle "Atualização automática" (default OFF) + selectbox de intervalo (30s/1min/5min) re-rodam só o bloco do gráfico no intervalo escolhido, sem recarregar a página nem tocar Analisar/Garimpar/Ranking — preservando o custo-zero porque o porteiro do Yahoo segue sendo o cache TTL=300s.

## O que mudou (Task 1)

Duas mudanças, ambas dentro do bloco `elif modo.startswith("📈"):` de `app.py`, sem tocar a engine:

1. **Controles fora do fragment** (após o botão "Atualizar", antes de `if ticker:`):
   - `_INTERVALOS = {"30 segundos": 30, "1 minuto": 60, "5 minutos": 300}`
   - `st.toggle("Atualização automática", value=False, disabled=(tf_key == "diario"), help=...)` → `auto_on`
   - `st.selectbox("Intervalo", ..., disabled=(not auto_on or tf_key == "diario"))` → `auto_intervalo`
   - No timeframe "Diário": `st.caption("ℹ️ ... no Diário ela é desnecessária.")`
   - `run_every = _INTERVALOS[auto_intervalo] if (auto_on and tf_key != "diario") else None`

2. **Fragment de render**: todo o corpo de `if ticker:` (spinner + fetch + branch de indisponível + cadeia read-only `indicators.calcular`/`setup.montar_setup` + estado isolado `tec_estado_swing` + `grafico_box` + figura/overlays + selo de atraso + card de veredito) virou uma função aninhada `@st.fragment(run_every=run_every)` `def _render_swing():`, chamada em seguida. Captura `ticker/tf_key/tf_label/k/CFG/run_every` por closure e LÊ `st.session_state[k]` (nonce) sem incrementar.

**Invariante preservada:** o único `st.session_state[k] += 1` continua sendo o do botão "Atualizar". O fragment só lê o nonce e chama `frame_intraday(ticker, tf_key, st.session_state[k])`; o re-fetch no timer é barrado pelo TTL=300s.

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- `.venv/bin/python -m pytest -q` → **283 passed in 2.75s** (nenhum golden tocado).
- `import ast; ast.parse(open('app.py').read())` → **syntax ok**.
- `grep 'st.fragment(run_every='` → presente (linha 636).
- `grep 'Atualização automática'` → presente (linha 615).
- `grep -c 'st.session_state\[k\] += 1'` → **1** (nonce-bump único, só no botão Atualizar).
- `git diff --stat` → apenas `app.py` (291 inserções, 263 deleções — a maioria é reindentação do corpo embrulhado no fragment).
- `requirements.txt` intocado (zero dependência nova).

## Threat Mitigations (do plano)

- **T-g0b-01 (self-DoS / rate-limit):** mitigado — auto-refresh não incrementa o nonce; `frame_intraday` mantém `@st.cache_data(ttl=300)`, então a Yahoo é consultada no máx. 1×/5min por par, independentemente do intervalo visual.
- **T-g0b-02 (vazamento de re-render p/ outras abas/engine):** mitigado — fragment envolve só o bloco swing; controles fora do fragment; nenhuma chamada à engine fundamentalista ou aos menus 1/2/3 alterada; 283 goldens verdes.

## Commits

- `ed9cf2e`: feat(swing): auto-refresh opcional via st.fragment(run_every=...) no 4º menu

## Self-Check: PASSED

- `app.py` modificado e presente (FOUND).
- Commit `ed9cf2e` presente em `git log` (FOUND).
- SUMMARY.md criado neste caminho.
