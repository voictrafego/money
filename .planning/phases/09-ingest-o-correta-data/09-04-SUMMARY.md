---
phase: 09-ingest-o-correta-data
plan: 04
subsystem: ui
tags: [dividend-yield, presentation, glossario, contrato, DATA-05]

# Dependency graph
requires:
  - phase: 09-ingest-o-correta-data
    provides: "multiples.dividend_yield = DPA/Preço (proventos brutos, sem imposto) — a base cujo rótulo esta fase declara"
provides:
  - "header_dy declara explicitamente que o DY é BRUTO (antes de IRRF) — ambos os caminhos (recorrente e fallback)"
  - "glossário (verbete 'dy' e bloco 'tab_multiplos') declara a base bruta do DY"
  - "teste de contrato tests/test_dy_base.py travando a declaração da base (substring 'bruto')"
affects: [10-primitivas, 13-motores-contrato-saida]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Rótulo/contrato de STRING (substring 'bruto') como prova — BLIND-04a limpo (sem ticker+número no mesmo assert)"

key-files:
  created:
    - tests/test_dy_base.py
  modified:
    - src/analista/report/presentation.py
    - src/analista/glossario.py
    - tests/classificacao.yaml

key-decisions:
  - "DATA-05 resolvido por DECLARAÇÃO, não cálculo: o DY é rotulado BRUTO; nenhum IRRF especulativo (Lei 15.270/2025 não verificada juridicamente — 09-RESEARCH A2) é aplicado"
  - "Zero motor/knob/cálculo tocado: multiples.dividend_yield, config.yaml e calibracao.lock.yaml (3 graus) intocados"

patterns-established:
  - "Base de um múltiplo é declarada onde o usuário LÊ o número (help do st.metric + glossário), não só na docstring"

requirements-completed: [DATA-05]

# Metrics
duration: 12min
completed: 2026-07-15
---

# Phase 09 Plan 04: Base do DY declarada (DATA-05) Summary

**O Dividend Yield passa a DECLARAR sua base ao usuário — é BRUTO (proventos brutos sobre o preço, sem descontar IR sobre dividendos/JCP) — no header e no glossário, sem calcular nenhum imposto especulativo e sem mover nenhum número de valuation.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-07-15
- **Tasks:** 2
- **Files modified:** 4 (2 produção, 1 teste novo, 1 classificação)

## Accomplishments
- `presentation.header_dy` declara "bruto" no `help` nos DOIS caminhos (recorrente principal e fallback trailing) — o ponto onde o usuário lê o número.
- Glossário atualizado em dois lugares: o verbete individual `"dy"` e a linha do DY no bloco `"tab_multiplos"`.
- Teste de contrato `tests/test_dy_base.py` (3 asserts) trava a AUSÊNCIA de ambiguidade — header (2 caminhos) + glossário declaram "bruto".
- Nenhum cálculo alterado: `multiples.dividend_yield` (DPA/Preço) intocado; nenhum valor de valuation muda.

## Task Commits

1. **Task 1: Declarar a base BRUTA do DY no header e no glossário** - `23b07ac` (feat)
2. **Task 2: Teste de contrato da base do DY (classificado)** - `1dfc0e8` (test)

_Nota: Task 2 (`tdd="true"`) saiu como um único commit `test` — o contrato que ela trava já havia sido estabelecido pela Task 1 (a ordem do plano é implementação → teste), então a fase RED-first não se aplicou; o teste nasce verde sobre a declaração da Task 1. Sem MVP/TDD gate ativo (o orquestrador não passou MVP_MODE/TDD_MODE)._

## Files Created/Modified
- `src/analista/report/presentation.py` - `header_dy`: help (normal e fallback) declara DY bruto (IR não descontado)
- `src/analista/glossario.py` - verbete `"dy"` e linha do DY em `"tab_multiplos"` declaram base bruta
- `tests/test_dy_base.py` - contrato: header (2 caminhos) + glossário contêm "bruto"
- `tests/classificacao.yaml` - 3 entradas `contrato` para o teste novo (no mesmo commit da Task 2)

## Decisions Made
- **Declarar, não calcular (decisão travada do plano/09-RESEARCH Open Question 4):** aplicar IRRF exigiria decompor JCP por ano e cravar alíquota/vigência frágeis sobre a Lei 15.270/2025 não verificada juridicamente. Declarar "bruto" satisfaz DATA-05 ("o DY declara sua base") sem afirmar uma conta de imposto não verificada.
- **Sem citar alíquota específica:** o texto declara "o imposto de renda sobre dividendos/JCP não é descontado" — fato verificável (DPA/Preço sem imposto), sem cravar percentual (mitiga T-09-09, Repudiation).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Threat Flags
Nenhuma superfície de segurança nova introduzida — mudança de rótulo/texto que não cruza fonte de dado externa nem input de usuário (consistente com o threat_model do plano: T-09-09 mitigado, T-09-10 aceito).

## Verification
- `.venv/bin/python -m pytest -k "presentation or glossario or report"` → 47 passed (Task 1).
- `.venv/bin/python -m pytest -k "dy_base"` → 3 passed (Task 2).
- `.venv/bin/python -m pytest -q` → **465 passed, 1 skipped, 34 deselected, 2 xfailed, 0 failed** (v2.4 verde; +3 vs. baseline 462, dos novos contratos).
- Scope check `git diff config.yaml calibracao.lock.yaml src/analista/core/multiples.py` → **VAZIO** (nenhum knob, nenhum cálculo).

## Next Phase Readiness
- DATA-05 completo. Resta DATA-06 (plano 09-05: snapshot limpo + monotonicidade), que fecha a Fase 9.
- Nenhum bloqueador. A declaração "bruto" é neutra ao valuation e não antecipa nenhuma quebra da Fase 10.

---
*Phase: 09-ingest-o-correta-data*
*Completed: 2026-07-15*

## Self-Check: PASSED

Todos os arquivos e commits declarados existem (2 arquivos de produção, 1 teste novo, 1 classificação, 1 SUMMARY; commits 23b07ac + 1dfc0e8).
