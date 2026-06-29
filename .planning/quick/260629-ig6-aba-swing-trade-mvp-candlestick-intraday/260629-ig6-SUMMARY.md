---
phase: quick-260629-ig6
plan: 01
subsystem: ui-streamlit
tags: [swing-trade, candlestick, intraday, plotly, streamlit]
requires: [frame_intraday, _nonce_key, intraday.coletar_intraday]
provides: [modo-swing-trade-ui, candlestick-mvp]
affects: [app.py]
tech-stack:
  added: []
  patterns: [nonce-targeted-cache-invalidation, copy-na-ui-nao-na-engine]
key-files:
  created: []
  modified: [app.py]
decisions:
  - "Roteamento explícito: Ranking deixou de ser else: e virou elif modo.startswith('📊') para abrir espaço ao 4º modo sem fall-through"
  - "Aviso de histórico insuficiente fica APENAS na cláusula f.idx_ultima_fechada is None; o dict de motivos cobre só timeframe_invalido/sem_dados/fetch_falhou (warning do plan-checker resolvido)"
metrics:
  duration: ~3 min
  completed: 2026-06-29
---

# Quick Task 260629-ig6: Aba Swing Trade (Candlestick MVP) Summary

Adicionado um 4º modo "📈 Swing trade (análise técnica)" na sidebar do app.py que renderiza um candlestick Plotly (`go.Candlestick`) a partir do OHLC nominal (`f.ohlc`) da engine intraday da Fase 12, com invalidação de cache targetada por nonce e zero impacto na aba fundamentalista e nos 202 testes golden.

## O que foi feito

- **Rádio da sidebar:** acrescentada a 4ª opção `"📈 Swing trade (análise técnica)"`, mantendo `help=h("menu")` inalterado.
- **Roteamento:** o bloco Ranking, antes capturado pelo `else:` (fall-through), passou a `elif modo.startswith("📊")`. A cadeia agora é explícita: `if 🔎 / elif ⛏️ / elif 📊 / elif 📈`. A lógica interna do Ranking permaneceu byte-a-byte idêntica.
- **Novo bloco swing (`elif modo.startswith("📈")`):**
  - Controles em colunas: `text_input` de ticker (default TAEE11), `selectbox` de timeframe com rótulos pt-BR mapeados para as chaves da engine (`{"Diário": "diario", "1h": "1h", "30m": "30m", "5m": "5m"}`) e botão `Atualizar`.
  - Invalidação targetada: `k = _nonce_key(ticker, tf_key)`, `setdefault(k, 0)`, e o botão Atualizar incrementa só `st.session_state[k]`, passado como `nonce` para `frame_intraday`. Nunca `cache_data.clear()` global.
  - Gateamento pelo ticker preenchido (não pelo retorno efêmero do botão) dentro de `st.spinner`.
  - Candlestick a partir de `f.ohlc` NOMINAL (D-02), `xaxis_rangeslider_visible=False`, altura/margens no estilo da aba Analisar.
  - Barra viva (D-04): `add_vline` na `f.ultima_barra_ts` + `st.caption` com o atraso (`f.atraso_min`).
  - Indisponibilidade (D-07): `f.disponivel is False` → `st.error` com copy pt-BR via dict `.get(f.motivo, fallback)` cobrindo `timeframe_invalido`/`sem_dados`/`fetch_falhou`.
  - Histórico insuficiente: `f.idx_ultima_fechada is None` → `st.warning`, mesmo com `f.disponivel is True`.

## Decisões e nota do plan-checker

O warning não-bloqueante do plan-checker foi resolvido conforme orientado: a entrada `historico_insuficiente` NÃO foi incluída no dict de motivos de indisponibilidade (seria código morto — a engine só emite `MOTIVO_HIST_INSUF` junto de `disponivel=True`). O aviso de histórico curto vive exclusivamente na cláusula `f.idx_ultima_fechada is None`. O dict usa `.get(..., fallback)` para robustez contra motivos desconhecidos.

## Deviations from Plan

None - plan executado exatamente como escrito.

## Verificação

- `.venv/bin/python -m py_compile app.py` → exit 0 (PYCOMPILE_OK)
- `grep -v '^[[:space:]]*#' app.py | grep -c 'cache_data\.clear'` → 0 (NO_GLOBAL_CLEAR_OK)
- greps confirmam: `modo.startswith("📈")`, opção do rádio, `frame_intraday(`/`_nonce_key(`, `go.Candlestick`, e `frame_intraday(ticker, tf_key, st.session_state[k])`
- `.venv/bin/python -m pytest -q` → **202 passed in 1.74s**
- Engine (`src/analista/`) não modificada; aba fundamentalista intacta.

## Commits

- `3c4eb15`: feat(quick-260629-ig6): aba Swing trade (candlestick MVP) em app.py

## Self-Check: PASSED

- app.py modificado e commitado (1 file changed, 73 insertions, 2 deletions)
- Commit 3c4eb15 presente no histórico
- Nenhuma deleção de arquivo no commit
