---
phase: 03-gr-fico-de-pre-o-na-aba-analisar
plan: 01
subsystem: ingest
tags: [yfinance, pandas, plotly, dataclass, threading]

# Dependency graph
requires:
  - phase: 01-engine-consistencia
    provides: vmin/vmax do DDM expostos em AnaliseAcao (linha intrínseca a sobrepor no Plano 02)
provides:
  - Campo serie_precos (close diário 5a) preservado em DadosMercado a partir do fetch existente
  - serie_precos conduzido até CompanyData via build.montar_empresa (sem nova chamada de rede)
  - plotly>=6.0 pinado em requirements.txt e instalado no venv (6.8.0)
affects: [03-02 render do gráfico, app.py aba Analisar]

# Tech tracking
tech-stack:
  added: [plotly>=6.0]
  patterns: ["Forward-ref Optional[\"pd.Series\"] em dataclass para manter a engine leve (sem import pandas no topo)"]

key-files:
  created: []
  modified:
    - src/analista/ingest/prices.py
    - src/analista/core/fundamentals.py
    - src/analista/ingest/build.py
    - requirements.txt

key-decisions:
  - "serie_precos = hist[Close].dropna() reusa o fetch tk.history existente — zero rede nova"
  - "Forward-ref em string para não forçar import pandas no topo dos módulos da engine (Pitfall 4)"
  - "Estado serie_precos=None em falha do Yahoo é o gancho do fallback gracioso GRAF-03 (Plano 02)"

patterns-established:
  - "Campos de mercado novos viajam DadosMercado → build.montar_empresa → CompanyData por cópia direta de Optional"

requirements-completed: [GRAF-01, GRAF-02, GRAF-03]

# Metrics
duration: 2min
completed: 2026-06-23
---

# Phase 3 Plan 01: Backbone da série de preço (serie_precos) Summary

**A série diária de close de 5 anos que `prices.py` já baixava e descartava agora é preservada em `DadosMercado.serie_precos` e conduzida até `CompanyData` sem nova chamada de rede; plotly>=6.0 pinado e instalado.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-23T13:23:58Z
- **Completed:** 2026-06-23T13:25:38Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- `serie_precos: Optional["pd.Series"]` adicionado a `DadosMercado`, preenchido com `hist["Close"].dropna()` dentro do bloco `if hist is not None and not hist.empty:` já existente — sem novo try/except e sem nova chamada ao Yahoo.
- `serie_precos` adicionado a `CompanyData` e copiado em `build.montar_empresa` (`c.serie_precos = dm.serie_precos`), junto dos demais campos de mercado.
- `plotly>=6.0` adicionado a `requirements.txt` e instalado no venv (6.8.0).
- Suíte completa de testes verde (62 passed) — nenhuma fórmula de valuation alterada (SC #4 / TEST-02); engine não importa plotly.

## Task Commits

Each task was committed atomically:

1. **Task 1: Preservar a série em prices.py** - `7d8b736` (feat)
2. **Task 2: Thread serie_precos em build.py/CompanyData + plotly** - `33c0bd7` (feat)
3. **Task 3: Garantir golden tests verdes** - verification-only (sem edição de source; 62 passed)

**Plan metadata:** docs commit (este SUMMARY + STATE.md + ROADMAP.md)

## Files Created/Modified
- `src/analista/ingest/prices.py` - Campo `serie_precos` em `DadosMercado` + `dm.serie_precos = hist["Close"].dropna()` no fetch existente.
- `src/analista/core/fundamentals.py` - Campo `serie_precos` no bloco de snapshot de mercado de `CompanyData`.
- `src/analista/ingest/build.py` - Cópia `c.serie_precos = dm.serie_precos` em `montar_empresa`.
- `requirements.txt` - Pin `plotly>=6.0` na camada de apresentação.

## Decisions Made
- Forward-ref `Optional["pd.Series"]` em string nos dois dataclasses para manter a engine leve (sem `import pandas` no topo) — segue o Pitfall 4 do RESEARCH.
- Nenhuma lógica condicional no threading: cópia direta de Optional, idêntica aos demais campos de mercado.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. `plotly>=6.0` já instalado no venv local; em outros ambientes basta `pip install -r requirements.txt`.

## Next Phase Readiness
- `CompanyData.serie_precos` está disponível em escopo na Tela 1 do `app.py`, pronto para o render do Plano 02.
- O estado `serie_precos=None` em falha do Yahoo já está estabelecido como gancho do fallback gracioso (GRAF-03).
- Plotly disponível para `st.plotly_chart` no Plano 02.

## Self-Check: PASSED

---
*Phase: 03-gr-fico-de-pre-o-na-aba-analisar*
*Completed: 2026-06-23*
