---
phase: 10-crescimento-robusto-de-poison-do-screening
plan: 02
subsystem: core
tags: [screening, bsd, regression, log-linear, winsorize, de-poison, valuation]

# Dependency graph
requires:
  - phase: 10-crescimento-robusto-de-poison-do-screening
    provides: growth.crescimento_log_linear (estimador log-linear, Plan 01) reusado como fonte única
  - phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia
    provides: payout_valuation()/mediana_payout sem clamp (D-03) — cross-effect resolvido aqui no fit
provides:
  - "BSD calcula crescimento_lucro/_dividendos/_fc_3a via growth.crescimento_log_linear sobre normalizacao.serie_winsorizada (série completa, D-04/D-05)"
  - "crescimento_lucro_3a do screening == report.g_historico por construção (fonte única Analisar↔Screening)"
  - "ajustar_regressao_pl clampa payout em [0,1] na entrada do fit (de-poison de b1 em fonte única, D-06)"
affects: [10-03 (rebaseline deliberado de golden de valor + travas de consistência)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fatores de crescimento de série do screening reusam o estimador robusto do valuation (log-linear sobre série winsorizada) — consistência por construção, não duplicação"
    - "Clamp de domínio aplicado na ENTRADA do fit OLS (fonte única) em vez de em cada call site (FIX-04)"

key-files:
  created: []
  modified:
    - src/analista/core/screening.py
    - src/analista/core/comparables.py

key-decisions:
  - "BSD usa a série COMPLETA winsorizada (não a janela 3a): com <5 pontos a winsorização não morde, então a janela 3a tornaria D-05 inócuo; série completa também faz o lucro do screening coincidir com g_historico do Analisar (D-04)"
  - "Clamp do payout vive em ajustar_regressao_pl (fit), não nos call sites: a previsão já clampava (L148); o vetor DP que alimenta o fit era a origem real do poison de b1 (TAEE11 ~2.16) — clampar no fit cobre cli e app de uma vez (FIX-04, D-06)"
  - "payout_valuation()/mediana_payout canônicos permanecem SEM clamp (D-03 Fase 9 preservado)"
  - "Chaves crescimento_*_3a mantidas (são chaves de REFERENCIA_BSD); per-ano CRU, var_tangivel CAGR, proxy cresc_lucro_lp e bandas intactos (D-07)"

patterns-established:
  - "Estimador de crescimento de série único entre menus (valuation e screening)"

requirements-completed: [GROW-02]

# Metrics
duration: 9min
completed: 2026-06-27
---

# Phase 10 Plan 02: De-poison do Garimpo/Ranking via estimador único Summary

**Os 3 fatores de crescimento de série do BSD passam a vir do estimador log-linear do Plan 01 sobre a série completa winsorizada (crescimento_lucro_3a = g_historico por construção), e a regressão de preço-alvo clampa o payout em [0,1] na entrada do fit — TAEE11 ~2.16 deixa de envenenar b1 — sem reintroduzir clamp no canônico payout_valuation().**

## Performance

- **Duration:** ~9 min
- **Completed:** 2026-06-27
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- **Task 1 (screening.py):** `import normalizacao` adicionado; closure `cagr_serie` substituído por `crescimento_serie(attr)` = `growth.crescimento_log_linear(normalizacao.serie_winsorizada(c.serie(attr)))`. Aplicado aos 3 atributos (`lucro_liquido`, `dividendos`, `fco`) nas chaves `crescimento_lucro_3a`/`crescimento_dividendos_3a`/`crescimento_fc_3a`. Série COMPLETA (não a janela 3a). Verificada a consistência por construção: `indicadores_bsd(c)["crescimento_lucro_3a"]` == `crescimento_log_linear(serie_winsorizada(serie("lucro_liquido")))` (= g_historico). Preservados intactos: `payout`, `cobertura`, `fc_sobre_lucro`, `var_tangivel` (CAGR, D-07), proxy `cresc_lucro_lp` (roe/payout CRU médios), janela `anos` e bandas REFERENCIA_BSD.
- **Task 2 (comparables.py):** `ajustar_regressao_pl` clampa `d` via `min(max(d, 0.0), 1.0)` no list-comprehension que monta `linhas`, antes da matriz de design. Fonte única — cobre cli.py:154 e app.py:468 (FIX-04). Propriedade de de-poison verificada: fit com `dp=2.16` produz coeficientes idênticos ao fit com `dp=1.0`. `preco_alvo_por_regressao` (clamp da previsão, L148) e `payout_valuation()`/`mediana_payout` (canônicos sem clamp, D-03) não tocados.
- Suíte completa verde: 166 testes (inclui test_screening, test_comparables, test_consistencia_modos) sem regressão e sem rebaseline.

## Task Commits

1. **Task 1: BSD via log-linear/winsorizado** — `61cdd2e` (feat)
2. **Task 2: clamp payout no fit da regressão P/L** — `fc942af` (feat)

## Files Created/Modified

- `src/analista/core/screening.py` — `from . import growth, normalizacao`; helper `crescimento_serie(attr)` substitui `cagr_serie`; 3 fatores via log-linear sobre série winsorizada; comentário atualizado.
- `src/analista/core/comparables.py` — clamp `min(max(d,0),1)` na montagem de `linhas` em `ajustar_regressao_pl`; docstring documenta o de-poison (D-06, ref 09-CROSS-EFFECT-FASE10.md).

## Decisions Made

None novas — seguiu o plano (D-04, D-05, D-06, D-07) e as decisões da Fase 9 (D-03) como especificado.

## Deviations from Plan

None - plan executed exactly as written.

## Threat Model Compliance

- **T-10-04** (DoS numérico em indicadores_bsd → log-linear): mitigado — a fronteira de None do estimador (qualquer ponto ≤0 / len<2 → None) e o `_limpar` de `serie_winsorizada` (descarta None) impedem `ln` de não-positivo. Verificado pelos testes verdes.
- **T-10-05** (tampering/envenenamento de modelo em ajustar_regressao_pl): mitigado — clamp de payout em [0,1] no fit impede que payout >100% legítimo distorça os coeficientes. Property-check `fit(2.16) == fit(1.0)` verde.

## Known Stubs

Nenhum.

## Issues Encountered

- `python`/`python3` do sistema não têm pandas; testes rodam com `.venv/bin/python` (já documentado no Plan 01). Sem impacto no código.

## Next Phase Readiness

- Fonte única de crescimento de série agora compartilhada entre Analisar e Screening; consistência factor==g_historico travável por assert no 10-03/T1.
- Valores exatos de `crescimento_*_3a` no BSD (e eventual movimento de bucket pela troca janela 3a → série completa) ficam para o rebaseline deliberado no 10-03/T2 — não foram gate aqui (golden de valor seguiram verdes).

## Self-Check: PASSED

- FOUND: src/analista/core/screening.py (`crescimento_log_linear` + `serie_winsorizada`, sem `cagr_serie`)
- FOUND: src/analista/core/comparables.py (`min(max(` no fit de `ajustar_regressao_pl`)
- FOUND: commit 61cdd2e, fc942af

---
*Phase: 10-crescimento-robusto-de-poison-do-screening*
*Completed: 2026-06-27*
