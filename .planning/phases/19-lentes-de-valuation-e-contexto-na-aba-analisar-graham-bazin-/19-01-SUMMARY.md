---
phase: 19-lentes-de-valuation-e-contexto-na-aba-analisar-graham-bazin-
plan: 01
subsystem: engine/core
tags: [valuation, graham, bazin, retorno, comparador-pares, funcoes-puras, golden-tests]
requires:
  - src/analista/core/multiples.py (_safe_div, preco_lucro)
  - src/analista/core/fundamentals.py (CompanyData: lpa_valuation/roe_valuation/dy_atual)
provides:
  - src/analista/core/lentes.py (4 lentes puras: Graham, Bazin, retorno, comparador)
affects:
  - Fase 19-02+ (wiring read-only na aba Analisar)
tech-stack:
  added: []
  patterns:
    - modulo-puro-golden-testavel (espelha ddm.py/multiples.py)
    - never-raise (None em entradas degeneradas)
    - reuso via import multiples (sem duplicar formula de divisao)
key-files:
  created:
    - src/analista/core/lentes.py
    - tests/test_lentes.py
  modified: []
decisions:
  - "P/L do comparador usa lpa_valuation (LPA canonico do Analisar) p/ consistencia entre menus"
  - "pares_suficientes conta pelo flag .alvo, nao por string de ticker (remove ambiguidade)"
  - "retorno_periodo envolve tudo em try/except p/ garantir never-raise sobre pd.Series"
metrics:
  duration: ~10min
  completed: 2026-07-02
---

# Phase 19 Plan 01: Lentes de valuation e contexto (engine) Summary

Módulo puro `core/lentes.py` com as 4 lentes da Fase 19 — Graham (√22,5×LPA×VPA), Bazin
(DPA médio ÷ 6%), "quanto teria rendido" (Adj Close) e comparador de pares (P/L, P/VP, ROE,
DY, valor de mercado) — todas funções puras never-raise, travadas por golden tests, sem tocar
`app.py` nem nenhum módulo de método existente.

## What Was Built

- **`src/analista/core/lentes.py`** (novo, aditivo):
  - `preco_justo_graham(lpa, vpa)` — VAL-01, √(22,5×LPA×VPA); None se LPA≤0 ou VPA≤0.
  - `vpa(patrimonio_liquido, num_acoes)` — VPA do ano-base via `multiples._safe_div`.
  - `dpa_medio(dpas, n=5)` — média dos últimos n DPAs não-None.
  - `preco_teto_bazin(dpa_med, dy_minimo=0.06)` — VAL-02; None se DPA médio≤0.
  - `upside(referencia, preco_atual)` — upside vs. preço atual (Graham/Bazin).
  - `retorno_periodo(serie_adj, anos, valor_inicial=1000.0)` — RET-01, R$ via Adj Close;
    None se série vazia ou histórico insuficiente (never-raise sobre pandas).
  - `ParComparavel` (dataclass) + `metricas_par`, `tabela_pares`, `pares_suficientes` — PEER-01.
  - Constantes `GRAHAM_K = 22.5`, `BAZIN_DY_MIN = 0.06`.
- **`tests/test_lentes.py`** (novo): 11 golden tests cobrindo todas as funções públicas com
  valores conhecidos + degradação never-raise.

## Key Decisions

- **Consistência entre menus:** o P/L do comparador usa `lpa_valuation()` (o mesmo LPA
  canônico que a aba Analisar exibe), não um LPA de um único ano — evita que a ação pareça
  barata num menu e cara em outro (Core Value do projeto).
- **`pares_suficientes` conta pelo flag `.alvo`** (não por string de ticker), removendo
  ambiguidade quando o alvo aparece na lista.
- **`retorno_periodo` totalmente envolto em try/except** para garantir never-raise sobre
  qualquer `pd.Series` (índices sem data, tipos inesperados) sem quebrar a aba.

## Deviations from Plan

None - plano executado exatamente como escrito. As 3 tasks foram implementadas em TDD
(RED → GREEN); a Task 3 (suíte golden) foi materializada pelos commits de teste das Tasks 1-2
e validada pela suíte completa.

## TDD Gate Compliance

- RED gate: commit `test(19-01)` (1b34940) — testes falhando antes da implementação.
- GREEN gate: commits `feat(19-01)` (41bec8f fórmulas, 514dc80 comparador).
- Sequência test→feat verificada no git log.

## Verification

- `.venv/bin/python -m pytest -q` → **307 passed** (296 existentes + 11 novos).
- `git diff --quiet` em `comparables.py`, `multiples.py`, `ddm.py`, `report.py` → intocados.
- `app.py` intocado.
- `grep -c "GRAHAM_K = 22.5"` == 1; `grep -c "BAZIN_DY_MIN = 0.06"` == 1; `import multiples` presente.

## Self-Check: PASSED

- FOUND: src/analista/core/lentes.py
- FOUND: tests/test_lentes.py
- FOUND commit: 1b34940 (test), 41bec8f (feat formulas), 514dc80 (feat comparador)
