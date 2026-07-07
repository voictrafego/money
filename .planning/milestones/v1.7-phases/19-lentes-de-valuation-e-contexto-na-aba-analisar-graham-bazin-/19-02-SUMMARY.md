---
phase: 19-lentes-de-valuation-e-contexto-na-aba-analisar-graham-bazin-
plan: 02
subsystem: ingest/core
tags: [valuation, retorno-total, adj-close, ret-01, aditivo, custo-zero]
requires:
  - src/analista/ingest/prices.py (coletar_mercado: variável `ajustado` já baixada)
  - src/analista/core/fundamentals.py (CompanyData dataclass)
provides:
  - src/analista/ingest/prices.py (DadosMercado.serie_precos_ajustada)
  - src/analista/core/fundamentals.py (CompanyData.serie_precos_ajustada)
affects:
  - Fase 19-03+ (RET-01 consome c.serie_precos_ajustada via lentes.retorno_periodo)
tech-stack:
  added: []
  patterns:
    - mudanca-aditiva-pura (campo Optional default None, never-raise)
    - reuso-sem-rede (persiste o Adj Close já baixado no mesmo tk.history do beta)
key-files:
  created: []
  modified:
    - src/analista/ingest/prices.py
    - src/analista/core/fundamentals.py
    - src/analista/ingest/build.py
decisions:
  - "Adj Close reaproveita o `ajustado` já derivado do tk.history do beta — zero chamada de rede nova"
  - "serie_precos (nominal) permanece a fonte do gráfico/veredito; serie_precos_ajustada é fonte separada só para RET-01"
metrics:
  duration: ~2min
  completed: 2026-07-02
---

# Phase 19 Plan 02: Fonte de dados do RET-01 (Adj Close 5a) Summary

Mudança 100% aditiva que expõe a série 5a de **Adj Close** (retorno total, dividendos
reinvestidos) — que `prices.coletar_mercado()` **já baixava e descartava** — num campo próprio
propagado `prices.py -> DadosMercado -> CompanyData`, dando ao RET-01 sua fonte de dados sem
nenhuma chamada de rede nova.

## What Was Built

- **`src/analista/ingest/prices.py`**: campo `serie_precos_ajustada: Optional[pd.Series] = None`
  no dataclass `DadosMercado`; em `coletar_mercado`, atribuição `dm.serie_precos_ajustada =
  ajustado.dropna()` no mesmo bloco `try` onde o `ajustado` (Adj Close) já era derivado do
  `hist` para alimentar beta/desempenho. `dm.serie_precos = nominal` e o uso de `ajustado` no
  beta seguem intactos.
- **`src/analista/core/fundamentals.py`**: campo `serie_precos_ajustada: Optional[pd.Series] =
  None` no dataclass `CompanyData`, junto de `serie_precos`/`ohlc` para coesão.
- **`src/analista/ingest/build.py`**: wiring `c.serie_precos_ajustada = dm.serie_precos_ajustada`
  no bloco de atribuição `dm -> c` de `montar_empresa`. Mesma assinatura, mesmo nº de chamadas
  de rede.

## Key Decisions

- **Reuso sem rede:** o Adj Close vem do mesmo `tk.history(period="5y", auto_adjust=False)` que
  já alimenta o beta; só faltava persistir a variável local `ajustado`. Nenhum novo
  `tk.history`/`yf.download`/`requests` foi introduzido.
- **Fonte separada da nominal:** `serie_precos` (Close nominal) continua sendo a base do
  gráfico e da banda DDM da aba Analisar (decisão CR-01 da Fase 3); `serie_precos_ajustada`
  existe apenas para o RET-01, que precisa de retorno total.
- **Never-raise:** campo default `None`; se o Yahoo falhar, o bloco `except` existente cobre e
  o campo permanece `None` — RET-01 (que já é never-raise no Plan 01) degrada graciosamente.

## Deviations from Plan

None - plano executado exatamente como escrito.

## Verification

- `.venv/bin/python -c "... 'serie_precos_ajustada' in DadosMercado.__dataclass_fields__"` → True
- `.venv/bin/python -c "... 'serie_precos_ajustada' in CompanyData.__dataclass_fields__"` → True
- `grep -c "dm.serie_precos_ajustada = ajustado" prices.py` == 1; `dm.serie_precos = nominal` intacto
- `grep -c "c.serie_precos_ajustada = dm.serie_precos_ajustada" build.py` == 1
- Nenhuma chamada de rede nova em `coletar_mercado`/`montar_empresa` (só persiste o `ajustado` já baixado)
- `.venv/bin/python -m pytest -q` → **307 passed** (296 baseline + 11 do Plan 01; este plano não adiciona testes)

## Self-Check: PASSED

- FOUND: src/analista/ingest/prices.py (serie_precos_ajustada)
- FOUND: src/analista/core/fundamentals.py (serie_precos_ajustada)
- FOUND: src/analista/ingest/build.py (wiring)
- FOUND commit: 3c2df90 (feat prices), 3778830 (feat CompanyData + wiring)
