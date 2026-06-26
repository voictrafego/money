---
phase: 04-encanamento-de-dados-s-rie-correta
plan: 01
subsystem: ingest
tags: [ohlc, split-adjustment, data-pipeline, yfinance]
requires: []
provides:
  - "DadosMercado.ohlc (frame OHLCV nominal 5a, Yahoo cru)"
  - "DadosMercado.ohlc_ajustado (OHLCV split-only-adjusted)"
  - "CompanyData.ohlc / CompanyData.ohlc_ajustado"
  - "prices._ajustar_por_split (função pura de ajuste por split)"
affects:
  - "Phase 5 (indicadores técnicos consomem ohlc_ajustado)"
tech-stack:
  added: []
  patterns:
    - "função pura module-level (espelha _retornos_mensais)"
    - "fator de split cumulativo reverso via cumprod invertido"
    - "campos aditivos propagados ingest → build → CompanyData (espelha serie_precos)"
key-files:
  created:
    - tests/test_ingest_ohlc.py
  modified:
    - src/analista/ingest/prices.py
    - src/analista/ingest/build.py
    - src/analista/core/fundamentals.py
decisions:
  - "ohlc_ajustado deriva de Stock Splits (split-only), nunca de Adj Close (que mistura proventos) — CR-01"
  - "nenhuma chamada de rede extra: reusa o hist já em memória de coletar_mercado (D-04)"
  - "fator cumulativo = produto dos splits APÓS cada data; ponta recente coincide com nominal (D-05)"
metrics:
  duration: "~15 min"
  completed: "2026-06-26"
  tasks: 2
  files_changed: 4
---

# Phase 4 Plan 01: Encanamento OHLCV (série split-adjusted correta) Summary

Frame OHLCV nominal de 5 anos (hoje descartado) preservado em `DadosMercado.ohlc`/`CompanyData.ohlc` e uma série OHLCV **ajustada só por splits** derivada por função pura (`_ajustar_por_split`) em `ohlc_ajustado`, sem nenhuma chamada de rede nova — espelhando 1:1 o fluxo de `serie_precos` da v1.1.

## What Was Built

- **`prices._ajustar_por_split(hist)`** — função pura module-level. Calcula o fator de split cumulativo de trás para frente (`cumprod` reverso de `Stock Splits`, dividido pelo fator do próprio dia) de modo que após o último split o fator seja 1.0 e a ponta recente da série ajustada coincida com a nominal. Divide O/H/L/C pelo fator e multiplica Volume no sentido inverso; copia as demais colunas inalteradas. Tolera coluna `Stock Splits` ausente (retorna cópia inalterada) e frame vazio/None (retorna None). Não muta a entrada e nunca usa `Adj Close` como base.
- **`DadosMercado.ohlc` / `DadosMercado.ohlc_ajustado`** — campos novos; preenchidos no bloco `if hist is not None and not hist.empty:` existente (`dm.ohlc = hist`, `dm.ohlc_ajustado = _ajustar_por_split(hist)`). Degradação graciosa coberta pelo guard existente (D-06).
- **`montar_empresa`** — copia `c.ohlc = dm.ohlc` e `c.ohlc_ajustado = dm.ohlc_ajustado` logo após `serie_precos` (cópia direta, sem condicional).
- **`CompanyData.ohlc` / `CompanyData.ohlc_ajustado`** — campos aditivos no dataclass; nenhum método alterado.
- **`tests/test_ingest_ohlc.py`** — 10 testes offline (zero rede): ponta recente == nominal, pré-split escalado pelo fator cumulativo, sem salto na data do split, 0 eventos → ajustado == nominal, coluna ausente sem estourar, pureza (não muta entrada), frame vazio → None, e fluxo de `coletar_mercado` (frame cru preservado, None quando hist vazio, `serie_precos` não regrediu).

## Task Commits

| Task | Name | Commit |
| ---- | ---- | ------ |
| RED  | Testes falhando (sessão anterior) | b6f64ed |
| 1    | `_ajustar_por_split` + campos OHLC em DadosMercado | c4c4b7a |
| 2    | Propagação ohlc/ohlc_ajustado → CompanyData | e05d676 |

## Verification

- `.venv/bin/pytest tests/test_ingest_ohlc.py tests/test_ingest_resolucao.py -q` → 25 passed.
- Suíte completa: `.venv/bin/pytest -q` → **74 passed** (golden tests de valuation intactos — nenhuma fórmula alterada, TEST-07 preservado).
- Acceptance greps: `ohlc_ajustado` x2 em prices.py; `c.ohlc = dm.ohlc` e `c.ohlc_ajustado = dm.ohlc_ajustado` presentes em build.py; 2 campos `ohlc` em fundamentals.py; `serie_precos` intacto nas três camadas.

## Deviations from Plan

Nenhuma deviation funcional. Nota de execução: este plano foi iniciado em sessão anterior — os testes (RED) já estavam commitados em `b6f64ed` e a implementação de `prices.py` (Task 1 + wiring) já estava no working tree. A implementação foi commitada como Task 1 (`c4c4b7a`); o wiring de prices.py acompanhou esse commit por residir no mesmo arquivo, com Task 2 (`e05d676`) restrita a build.py + fundamentals.py.

## Known Stubs

Nenhum. Os campos são populados a partir do `hist` real do Yahoo; ficam `None` apenas na degradação graciosa esperada (D-06).

## Self-Check: PASSED

- FOUND: tests/test_ingest_ohlc.py
- FOUND: commit c4c4b7a (feat 04-01 _ajustar_por_split)
- FOUND: commit e05d676 (feat 04-01 propagate ohlc to CompanyData)
- FOUND: 74 passed na suíte completa
