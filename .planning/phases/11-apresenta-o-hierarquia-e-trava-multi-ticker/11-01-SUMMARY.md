---
phase: 11-apresenta-o-hierarquia-e-trava-multi-ticker
plan: 01
subsystem: ui
tags: [streamlit, presentation, formatting, dividend-yield, payout, golden-test, pytest]

# Dependency graph
requires:
  - phase: 09-payout-sustentavel-dy-recorrente
    provides: "payout_valuation() / dy_recorrente() / lpa_valuation() (campos sustentáveis já expostos pela engine)"
provides:
  - "src/analista/report/presentation.py — camada de apresentação pura (header_dy/linhas_multiplos/fmt_pct/fmt_num) importável sem Streamlit"
  - "Golden de propriedade multi-ticker da apresentação (layer a da trava TEST-08)"
  - "Fixes de formatação travados: DYR-02 (DY rec. como %), PAY-02 (payout cru x sustentável distintos), HIER-01 (header recorrente principal + trailing delta neutro)"
affects: [11-02-rewiring-app, app.py, checkpoint-live]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Helpers de apresentação PUROS (sem import streamlit, sem efeito de import) — testáveis offline (D-09)"
    - "Golden de PROPRIEDADE: assert trava regra do método, não número de mercado; importa from analista.report (nunca do app)"

key-files:
  created:
    - src/analista/report/presentation.py
    - tests/test_presentation_multiticker.py
  modified: []

key-decisions:
  - "fmt_pct/fmt_num movidos (não importados) de app.py — em-dash '—' mantido distinto do hífen do report._pct (UI-SPEC trava o separador da superfície do app)"
  - "header_dy retorna dict (label/value/delta/delta_color/help/fallback) — Streamlit-agnóstico; o app.py (Plan 02) consome o dict"
  - "linhas_multiplos recebe payout_ult e payout_proj como params explícitos — o caller passa c.payout(ult) CRU vs c.payout_valuation(), corrigindo o colapso atual do app.py L317-323"

patterns-established:
  - "Camada de apresentação extraída do Streamlit como módulo puro importável"
  - "Golden de propriedade multi-ticker para a camada (a) de apresentação"

requirements-completed: [TEST-08]

# Metrics
duration: 12 min
completed: 2026-06-28
---

# Phase 11 Plan 01: Camada de Apresentação Pura + Golden Multi-Ticker Summary

**Módulo `presentation.py` puro (sem Streamlit) com header_dy/linhas_multiplos/fmt_pct/fmt_num, travado por golden de propriedade nos 5 perfis de ticker — fixa DYR-02 (DY rec. como %), PAY-02 (payout cru distinto do sustentável) e HIER-01 (recorrente como valor principal do header) sem tocar a engine de valuation.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-06-28T01:02:35Z
- **Tasks:** 2
- **Files modified:** 2 (ambos criados)

## Accomplishments
- `src/analista/report/presentation.py`: helpers puros, importáveis sem subir o Streamlit (zero `import streamlit`, zero efeito de import — D-09).
- `header_dy(dy_recorrente, dy_atual)`: elege o DY recorrente como valor principal com o trailing como delta neutro (`delta_color="off"`); cai para o trailing (fallback=True, label "Dividend Yield (trailing)") quando o recorrente é indisponível.
- `linhas_multiplos(...)`: roteia "DY rec." pelo ramo % (fix DYR-02, paridade com report.py L397) e emite duas linhas de payout distintas — cru do último ano x sustentável p/ valuation (fix PAY-02/D-05/D-06).
- Golden `tests/test_presentation_multiticker.py`: 4 testes de propriedade nos perfis VULC3 / normal estável (EGIE3) / TAEE11 / fallback (sem lucro), todos verdes.
- Engine de valuation intocada → nenhum golden de valuation rebaselina (D-10).

## Task Commits

1. **Task 1: Criar src/analista/report/presentation.py (helpers puros, sem Streamlit)** - `f268eb1` (feat)
2. **Task 2: Golden de propriedade multi-ticker da apresentação** - `ac032f5` (test)

**Plan metadata:** ver commit `docs(11-01)` abaixo.

## Files Created/Modified
- `src/analista/report/presentation.py` (99 linhas) - Helpers puros fmt_pct/fmt_num + header_dy + linhas_multiplos. Sem Streamlit.
- `tests/test_presentation_multiticker.py` (165 linhas) - Golden de propriedade multi-ticker (layer a da trava TEST-08).

## Decisions Made
- Helpers movidos de `app.py` (não importados) para o módulo puro; em-dash "—" mantido distinto do hífen do CLI (`report._pct`), por contrato da UI-SPEC.
- `header_dy` retorna um dict Streamlit-agnóstico — o rewiring do `app.py` (Plan 02) o consome diretamente.
- `linhas_multiplos` recebe os dois payouts como params explícitos, deixando ao caller passar `c.payout(ult)` CRU vs `c.payout_valuation()` (corrige o colapso de ambas as linhas no mesmo valor clampado, app.py L317-323).

## Deviations from Plan

None - plan executed exactly as written. Todos os comportamentos do bloco `<behavior>` e os critérios de aceite das duas tasks foram implementados como especificado.

## Issues Encountered

**Invocação da suíte completa — `.venv/bin/pytest` vs `.venv/bin/python -m pytest` (pré-existente, fora de escopo):**
O comando literal do plano (`.venv/bin/pytest -q`) falha na COLETA — mas isso é **pré-existente no HEAD, independente deste plano** (reproduz com o arquivo novo removido via `git stash -u`). Causa: `tests/test_indicators.py` faz `from tests.test_ingest_ohlc import ...`, que exige o diretório-raiz do projeto em `sys.path` — o console-script `.venv/bin/pytest` não o adiciona; `.venv/bin/python -m pytest` adiciona (cwd em `sys.path[0]`).

- Invocação canônica verde: **`.venv/bin/python -m pytest -q` → 175 passed** (inclui os 4 testes novos), **zero rebaseline de golden de valuation** (gate D-10 satisfeito).
- Não corrigido aqui: os arquivos envolvidos (`test_indicators.py`, `test_ingest_ohlc.py`) não foram tocados por este plano (scope boundary — falha pré-existente em arquivo não relacionado). Registrado para um ajuste futuro de configuração de testes (ex.: `tests/__init__.py` ou `pythonpath` incluindo `.`).

## Next Phase Readiness
- `presentation.py` pronto para o rewiring do `app.py` (Plan 02): `app.py` passa a chamar `header_dy(...)` para o `m3` e `linhas_multiplos(...)` para a tabela de Múltiplos.
- Fundação da fase (D-09) entregue antes do rewiring e do checkpoint live, conforme planejado.

## Self-Check: PASSED
- `src/analista/report/presentation.py` existe no disco ✓
- `tests/test_presentation_multiticker.py` existe no disco ✓
- Commit `f268eb1` (Task 1) presente no log ✓
- Commit `ac032f5` (Task 2) presente no log ✓
- `.venv/bin/python -m pytest -q` → 175 passed (suíte verde, sem rebaseline de valuation) ✓
- `grep -c "import streamlit" src/analista/report/presentation.py` == 0 ✓
- `grep -c "from app import" tests/test_presentation_multiticker.py` == 0 ✓

---
*Phase: 11-apresenta-o-hierarquia-e-trava-multi-ticker*
*Completed: 2026-06-28*
