---
phase: 12-ingest-o-intraday-timeframe
plan: 01
subsystem: ingest
tags: [yfinance, intraday, ohlcv, timezone, pandas, swing-trade, timeframe]

# Dependency graph
requires:
  - phase: 03-grafico-interativo
    provides: "prices._ajustar_por_split (split-only puro), padrão DadosMercado, retry _MAX_TENTATIVAS/_BACKOFF_SEG"
provides:
  - "coletar_intraday(ticker, timeframe) -> FrameOHLC (diário/1h/30m/5m), engine de borda isolada do pipeline diário"
  - "FrameOHLC: ohlc nominal + ohlc_ajustado (split-only) + metadados de barra viva (barra_viva, idx_ultima_fechada, atraso_min)"
  - "_PERIODO_POR_TF cravado nos tetos da Yahoo (5y/730d/60d)"
  - "_normaliza_tz determinístico (America/Sao_Paulo, imune ao TZ do processo)"
  - "Categorias de motivo (timeframe_invalido/fetch_falhou/sem_dados/historico_insuficiente)"
affects: [13-indicadores-pivos, 16-pagina-swing-grafico]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Engine de ingestão parametrizada espelhando coletar_mercado (period×interval por tabela cravada)"
    - "Metadados clock-free de barra viva (idx_ultima_fechada=len-2, imune a relógio/calendário B3)"
    - "Normalização defensiva de timezone via tz_convert (idempotente para .SA)"

key-files:
  created:
    - src/analista/ingest/intraday.py
    - tests/test_ingest_intraday.py
  modified: []

key-decisions:
  - "FrameOHLC, _PERIODO_POR_TF e categorias de motivo vivem dentro de intraday.py (espelha prices.py)"
  - "auto_adjust=False obrigatório: preserva Close nominal + Stock Splits para reuso de _ajustar_por_split"
  - "Barra viva sempre suspeita (barra_viva=len>=1); cálculo da Fase 13 usa iloc[-2] via idx_ultima_fechada"
  - "Frame com 1 barra fica disponivel=True (há barra p/ gráfico) mas motivo=historico_insuficiente (A3)"
  - "atraso_min com agora injetável (default now(SP)) para golden determinístico (Pitfall 3)"

patterns-established:
  - "Pattern: ingestão multi-timeframe parametrizada e isolada do fetch diário 5y (firewall fundamentalista)"
  - "Pattern: contrato no-repaint clock-free separado da métrica informacional atraso_min"

requirements-completed: [DATA-01, DATA-02]

# Metrics
duration: 9min
completed: 2026-06-29
---

# Phase 12 Plan 01: Ingestão Intraday + Timeframe Summary

**Engine de borda `coletar_intraday(ticker, timeframe) -> FrameOHLC` para OHLCV multi-timeframe (diário/1h/30m/5m) via yfinance, isolada do pipeline diário, com split-adjust reusado, tz America/Sao_Paulo determinística e metadados de barra viva clock-free — nunca levanta exceção.**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-06-29T15:18:49Z
- **Completed:** 2026-06-29
- **Tasks:** 2
- **Files modified:** 2 (ambos criados)

## Accomplishments
- `src/analista/ingest/intraday.py`: `coletar_intraday` + dataclass rico `FrameOHLC` + tabela `_PERIODO_POR_TF` cravada nos tetos da Yahoo + categorias de `motivo`, reusando `prices.yahoo_symbol`/`_ajustar_por_split`/`_yf`/`_MAX_TENTATIVAS`/`_BACKOFF_SEG` (zero reimplementação).
- `_normaliza_tz`: índice → America/Sao_Paulo de forma idempotente e imune ao TZ do processo (VPS=UTC), com fallback para índice naive.
- Metadados de barra viva clock-free (`barra_viva`, `idx_ultima_fechada=len-2`, `atraso_min` com `agora` injetável) — contrato no-repaint para a Fase 13 (`iloc[-2]`).
- Borda graciosa: tf inválido / fetch falhou / vazio / histórico curto retornam `FrameOHLC(disponivel=...)` com `motivo` categorizado, nunca `None`/exceção.
- `tests/test_ingest_intraday.py`: 11 testes 100% offline (monkeypatch de `_yf`/`time.sleep`) cobrindo matriz period×interval, tz naive+SP, barra viva, atraso determinístico, frame curto, vazio/exceção/tf inválido.

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Engine de ingestão intraday (intraday.py)** - `d61377b` (feat)
2. **Task 2: Testes golden offline (test_ingest_intraday.py)** - `e94f789` (test)

_Task 1 era `tdd="true"`; a estrutura do plano dedica Task 2 inteiramente à suíte de testes, então o ciclo virou feat (engine) → test (suíte offline) seguindo a atribuição de arquivos por task do contrato._

## Files Created/Modified
- `src/analista/ingest/intraday.py` - Engine de ingestão OHLCV multi-timeframe (coletar_intraday, FrameOHLC, _PERIODO_POR_TF, _normaliza_tz, categorias de motivo).
- `tests/test_ingest_intraday.py` - 11 testes offline das edges (barra viva, period×interval, timezone, frame curto, vazio/exceção/tf inválido).

## Decisions Made
- Seguiu integralmente as decisões locked do RESEARCH/PATTERNS (D-01 a D-07): dataclass rico no mesmo módulo, `auto_adjust=False`, reuso de `_ajustar_por_split`, tz defensiva, barra viva clock-free.
- A engine NÃO importa `streamlit` (cache vive só em `app.py`, Fase 16) — mantém testabilidade offline.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. Suíte completa subiu de 191 para 202 testes (191 golden + 11 novos), nenhum golden regrediu.

## TDD Gate Compliance
Task 1 marcada `tdd="true"`; a divisão do plano (Task 1 = engine, Task 2 = suíte de testes) produziu commits `feat` (d61377b) seguido de `test` (e94f789). Os 11 testes validam o comportamento da engine e a suíte completa fica verde (202 passed). Sem regressão dos 191 golden.

## User Setup Required
None - nenhuma configuração de serviço externo. Zero novas dependências de runtime (yfinance/pandas/numpy já instalados).

## Next Phase Readiness
- Contrato `FrameOHLC` pronto para consumo: Fase 13 (indicadores/pivôs sobre `ohlc_ajustado` na barra fechada via `iloc[-2]`) e Fase 16 (gráfico sobre `ohlc` nominal + metadados de barra viva).
- Cache `@st.cache_data(ttl=300)` + nonce e botão "Atualizar" (DATA-03) ficam para a camada thin em `app.py` na Fase 16 — fora do escopo desta engine.
- Plano 02 da Fase 12 é o próximo passo sequencial.

## Self-Check: PASSED

- FOUND: src/analista/ingest/intraday.py
- FOUND: tests/test_ingest_intraday.py
- FOUND commit: d61377b (Task 1, feat)
- FOUND commit: e94f789 (Task 2, test)

---
*Phase: 12-ingest-o-intraday-timeframe*
*Completed: 2026-06-29*
