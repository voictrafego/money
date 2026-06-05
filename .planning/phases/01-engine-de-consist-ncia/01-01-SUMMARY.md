---
phase: 01-engine-de-consist-ncia
plan: 01
subsystem: engine
tags: [valuation, payout, roe, dividend-yield, fundamentals, screening, ingest]

# Dependency graph
requires: []
provides:
  - "CompanyData.payout_valuation(): função canônica única de payout-para-valuation (média 3a + clamp 1.0) reusada por Analisar e Ranking"
  - "CompanyData.roe(): base de PL única em toda a série (PL médio; None quando falta o PL inicial)"
  - "CompanyData.dy_atual(): DY corrente por trailing-12m com fallback; campos dpa_trailing_12m e ano_dpa expostos"
  - "Propagação prices→build→CompanyData do DPA trailing-12m e ano-base do DPA"
affects: [ranking, garimpo-bsd, analisar, fase-2-apresentacao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Função canônica única na ORIGEM (engine) consumida por todos os modos — evita divergência de agregação por modo"
    - "Dado faltante na borda vira None/fallback (nunca pior-valor silencioso)"

key-files:
  created:
    - tests/test_fundamentals_consistencia.py
  modified:
    - src/analista/core/fundamentals.py
    - src/analista/report/report.py
    - src/analista/glossario.py
    - src/analista/core/screening.py
    - src/analista/ingest/prices.py
    - src/analista/ingest/build.py

key-decisions:
  - "Payout-para-valuation canônico = média dos 3 últimos anos com clamp em 1.0 (igual ao que o Analisar já fazia em _media_payout_3a)"
  - "ROE usa PL médio ((PL_ini+PL_fim)/2); no 1º ano da janela sem PL anterior retorna None em vez de cair para PL final — série nunca mistura bases"
  - "DY corrente usa dpa_trailing_12m (soma das datas reais dos últimos 12 meses) quando disponível; ano_dpa exposto para a Fase 2 sinalizar o ano-base"

patterns-established:
  - "payout_valuation: única definição de payout que decide valuation/regressão"
  - "dy_atual: trailing-12m com fallback de ano-base; ano_dpa exposto p/ apresentação"

requirements-completed: [PAYOUT-01, ROE-01, DY-01]

# Metrics
duration: 18min
completed: 2026-06-05
---

# Phase 01 Plan 01: Engine de Consistência (payout/ROE/DY) Summary

**Unificou na origem três cálculos divergentes entre modos — payout-para-valuation (CR-02/WR-03), base de PL do ROE (WR-01) e DY corrente trailing-12m (WR-04) — numa engine única consumida por Analisar, Garimpo e Ranking.**

## Performance

- **Duration:** ~18 min
- **Tasks:** 3 completas (TDD: RED + 3 GREEN)
- **Files modified:** 6 (+1 criado)

## Accomplishments
- `CompanyData.payout_valuation()` é a definição ÚNICA de payout-para-valuation (média 3a + clamp 1.0); `report.analisar_acao` passou a consumi-la, removendo o `_media_payout_3a` local — Analisar e Ranking deixam de divergir para a mesma ação.
- `CompanyData.roe()` agora usa PL médio consistente em toda a série e retorna None no 1º ano sem PL inicial (em vez de cair silenciosamente para o PL final); glossário alinhado à base real.
- `CompanyData.dy_atual()` usa o DPA dos últimos 12 meses reais (datas do Yahoo) quando disponível, com fallback para o ano-base; `dpa_trailing_12m` e `ano_dpa` são propagados pelo caminho real `prices → build → CompanyData`.

## Task Commits

1. **RED — testes falhando** - `9e3a12b` (test)
2. **Task 1: payout_valuation canônico** - `e475470` (feat)
3. **Task 2: ROE com base de PL única + glossário + fix screening** - `65b1288` (feat)
4. **Task 3: DY trailing-12m propagado** - `f8c5f8c` (feat)

## Files Created/Modified
- `tests/test_fundamentals_consistencia.py` - Testes das 3 funções canônicas (payout_valuation, roe-base, dy_atual trailing-12m + ano_dpa).
- `src/analista/core/fundamentals.py` - `payout_valuation()`; `roe()` em PL médio (None sem PL inicial); `dy_atual()` trailing-12m; campos `dpa_trailing_12m`/`ano_dpa`.
- `src/analista/report/report.py` - Removido `_media_payout_3a`; DDM usa `c.payout_valuation()`.
- `src/analista/glossario.py` - Tooltip "roe" alinhado à base real (PL médio; indisponível no 1º ano).
- `src/analista/core/screening.py` - `filtros_customizados` avalia `roe_min` só nos anos com ROE definido (deviation, ver abaixo).
- `src/analista/ingest/prices.py` - `DadosMercado.dpa_trailing_12m`/`ano_dpa` calculados das datas reais de `tk.dividends`.
- `src/analista/ingest/build.py` - `montar_empresa` propaga `dm.dpa_trailing_12m` e `dm.ano_dpa` para o CompanyData.

## Verification

- `pytest tests/ -q` → **38 passed** (29 golden + 9 novos). Golden de ddm/multiples/comparables/screening intactos.
- Smokes inline do plano (payout_valuation, roe, dy_atual, propagação em montar_empresa via inspect) verdes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `filtros_customizados` quebrava com o novo ROE=None no 1º ano**
- **Found during:** Task 2
- **Issue:** O teste golden `test_screening.py::test_filtros_customizados_aprova_solida` falhou porque o critério `roe_min` exigia `all(r is not None and r > roe_min)` para TODOS os anos da janela. Com a correção WR-01, o 1º ano agora retorna None por definição (sem PL inicial), reprovando empresas válidas.
- **Fix:** O critério passou a avaliar `roe_min` apenas nos anos com ROE definido (filtrando os None do 1º ano) e a exigir pelo menos um ano avaliável. Mantém o significado do filtro (ROE persistente acima do mínimo) sem penalizar a indisponibilidade estrutural do 1º ano.
- **Files modified:** `src/analista/core/screening.py`
- **Commit:** `65b1288`

## Self-Check: PASSED
- FOUND: tests/test_fundamentals_consistencia.py
- FOUND: src/analista/core/fundamentals.py (payout_valuation, roe, dy_atual)
- FOUND: commit 9e3a12b, e475470, 65b1288, f8c5f8c
- pytest: 38 passed
