---
phase: 05-backtest-01-valida-o-na-cesta-de-bancos
plan: 03
subsystem: backtest-harness
tags: [backtest, valuation, rim, ancoras, offline, harness]
requires:
  - tests/fixtures/snapshot_bancos_2026-07-12.yaml   # 05-01 (RIM congelado por ticker)
  - tests/fixtures/fair_values_bancos.yaml           # 05-02 (faixas de consenso aprovadas)
  - src/analista/report/report.py::analisar_acao     # fonte unica do intrinseco RIM
  - src/analista/core/lentes.py                      # Graham/Bazin/metricas_par
provides:
  - src/analista/backtest.py::rodar_cesta            # harness puro reusado por teste+script
  - src/analista/backtest.py::carregar_snapshot
  - src/analista/backtest.py::carregar_fair_values
  - scripts/backtest_bancos.py                       # standalone → out/backtest_bancos.md
affects:
  - Plan 05-04 (gate quorum-3/4) consome rodar_cesta
tech-stack:
  added: []          # zero dep nova: yaml/statistics/tabulate ja no projeto
  patterns:
    - "harness CONSOME o motor (analisar_acao), nunca reimplementa a formula RIM"
    - "rf_local congelado injetado em cfg[capm][rf_local] → offline/deterministico"
    - "medianas P/VP e P/L da propria cesta (D-11) como ancora setorial"
key-files:
  created:
    - src/analista/backtest.py
    - scripts/backtest_bancos.py
  modified: []
decisions:
  - "rodar_cesta pura reusada por teste (05-04) e script → mesmo numero (RESEARCH Open Q3)"
  - "constante nomeada BANDA_PASS=0.15 (D-07); zero numero solto"
  - "desvios reportados, nao mascarados (D-12): ticker fora da banda aparece com veredito+nota"
metrics:
  duration: 0h18m
  completed: 2026-07-13
  tasks: 2
  files: 2
---

# Phase 05 Plan 03: Harness de validação BACKTEST-01 (rodar_cesta + script) Summary

Harness reprodutível e offline que roda o RIM calibrado nos 4 bancos e triangula 4 âncoras de
realidade — `rodar_cesta` pura em `src/analista/backtest.py` (reusada pelo teste 05-04 e pelo
script) + wrapper `scripts/backtest_bancos.py` que gera `out/backtest_bancos.md`.

## O que foi construído

**Task 1 — `src/analista/backtest.py` (commit 60e0f2b):**
- `carregar_snapshot(caminho) -> (list[CompanyData], float)` — reconstrói os 4 `CompanyData` a
  partir dos raw fundamentals congelados (não `vpa0/roe0/ke` derivados → imune a mudança de
  assinatura interna de `motores.rim`) + devolve o `rf_local` carimbado (0.105).
- `carregar_fair_values(caminho) -> dict` — lê as faixas de consenso aprovadas.
- `rodar_cesta(empresas, fair_values, cfg, rf_local) -> list[dict]` — **PURA** (sem I/O, sem rede).
  Injeta `rf_local` em `cfg["capm"]["rf_local"]` antes do loop (`analisar_acao` não muta cfg).
  Por ticker: extrai o RIM via `report.analisar_acao(...).intrinseco_motor` (never-raise → None
  tratado como fora-da-banda), calcula as 4 âncoras — (a) Graham+Bazin via `lentes`, (b) preço,
  (c) faixa FV, (d) medianas P/VP e P/L da própria cesta via `lentes.metricas_par` +
  `statistics.median` (D-11) — o desvio RIM×FV e o veredito PASS/FAIL com `BANDA_PASS = 0.15` (D-07).
  A fórmula RIM **não** é reimplementada (zero `motores.rim(` no módulo).

**Task 2 — `scripts/backtest_bancos.py` (commit 740f1ab):**
- Wrapper fino, invocável por `python scripts/backtest_bancos.py`, que chama a MESMA `rodar_cesta`.
- Monta a tabela D-10 (12 colunas: Ticker · Motor · RIM · Graham · Bazin · Preço · FV faixa ·
  P/VP med · P/L med · Desvio RIM×FV · PASS/FAIL · Nota exceção) com `tabulate(..., tablefmt="github")`
  e grava `out/backtest_bancos.md` (out/ gitignored — saída gerada, esperado).

## Resultado (reproduz o snapshot congelado)

| Ticker | RIM   | FV faixa      | Desvio | Veredito |
|--------|-------|---------------|--------|----------|
| ITUB4  | 32.88 | 30.50–50.00   | -18.3% | **PASS** |
| BBAS3  | 45.60 | 20.00–39.00   | +54.6% | FAIL     |
| BBSE3  | 25.38 | 33.00–46.00   | -35.7% | FAIL     |
| BBDC4  | 10.47 | 15.00–24.00   | -46.3% | FAIL     |

Só ITUB4 cai na banda ±15% (1/4) — sinal legítimo já antecipado pelo 05-02, **reportado e não
mascarado** (D-12). O tratamento do quórum 3/4 e do loop D-12 é do Plan 05-04.

## Deviations from Plan

None - plan executed exactly as written. As duas tasks passaram na verificação automatizada na
primeira execução; nenhum bug, funcionalidade crítica ausente ou bloqueio encontrado.

## Verification

- `rodar_cesta` devolve 4 dicts com RIM + 4 âncoras + PASS/FAIL; ITUB4 motor `rim`, RIM 32.88 (30–40). ✓
- `python scripts/backtest_bancos.py` gera `out/backtest_bancos.md` com a tabela D-10 (4 linhas, 12 colunas). ✓
- `grep -v '^#' src/analista/backtest.py | grep -c 'BANDA_PASS'` = 2 (≥1, constante nomeada). ✓
- Nenhum `motores.rim(` em `backtest.py`; RIM extraído só de `analisar_acao`. ✓
- `git diff --name-only HEAD~2 HEAD` = apenas `backtest.py` + `backtest_bancos.py`; core/motores/lentes/ddm/selo/config **intocados**. ✓
- Golden regression: `test_vulc3_regressao.py` + `test_ddm.py` = 16 passed. ✓

## Self-Check: PASSED

- FOUND: src/analista/backtest.py
- FOUND: scripts/backtest_bancos.py
- FOUND commit: 60e0f2b (Task 1)
- FOUND commit: 740f1ab (Task 2)
