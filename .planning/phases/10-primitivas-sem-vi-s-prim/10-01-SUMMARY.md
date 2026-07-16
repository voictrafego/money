---
phase: 10-primitivas-sem-vi-s-prim
plan: 01
subsystem: testing
tags: [theil-sen, scipy, normalizacao, valuation, estimator-split, blind-03, knob-budget]

# Dependency graph
requires:
  - phase: 09-ingestao-correta-data
    provides: "insumos limpos (num_acoes oficial, JCP capturado, lucro/PL do controlador) que a base normalizada consome"
provides:
  - "base_normalizada = ENDPOINT de tendência robusta (Theil-Sen) no ano atual (reflete crescimento; robusto a 1 outlier; guard endpoint<=0->median; fallback N=0/1/2)"
  - "media_ciclo (NOVA): a média/mediana through-cycle antiga, para o motor cíclico (anos_media=10)"
  - "BLIND-03 curado: test_normalizacao_nao_pune_crescimento vira invariante normal (era xfail)"
  - "report.py ramo 'normalizado' repontado para media_ciclo (o cíclico não recebe o endpoint)"
  - "janela do endpoint = 5 (co-change config.yaml + calibracao.lock.yaml, orçamento intacto em 3 graus)"
affects: [11-crescimento-grow, 12-custo-de-capital-ke, 10-02, 10-03, 10-04]

# Tech tracking
tech-stack:
  added: [scipy.stats.theilslopes]
  patterns:
    - "Estimator split: uma primitiva compartilhada por dois consumidores com estimadores OPOSTOS é dividida em duas funções, não editada in-place"
    - "Guard de degeneração: endpoint<=0 -> median(janela), nunca propaga base negativa a RIM/DCF"

key-files:
  created: []
  modified:
    - src/analista/core/normalizacao.py
    - src/analista/core/motores.py
    - src/analista/report/report.py
    - tests/test_normalizacao.py
    - tests/test_invariantes_v24.py
    - tests/test_fundamentals_consistencia.py
    - tests/test_consistencia_modos.py
    - tests/classificacao.yaml
    - config.yaml
    - calibracao.lock.yaml

key-decisions:
  - "Janela do Theil-Sen = 5 (checkpoint:decision resolvido pelo usuário): separa um exercício atípico terminal da tendência; co-change sancionado config+lock"
  - "Dividir o estimador em vez de editar base_normalizada globalmente: o motor cíclico precisa da MÉDIA through-cycle, não do endpoint (CSNA3 endpoint = -891M vs média = +1.270M)"
  - "Guard endpoint<=0 -> median(janela): Theil-Sen sobre níveis degenera negativo em prejuízo recente"

patterns-established:
  - "Estimator split (base_normalizada endpoint x media_ciclo média) — RESEARCH §Estimator split"
  - "Reescrita (não afrouxamento) de testes que codificavam o método antigo, com a invariância NOVA + guarda de robustez preservada"

requirements-completed: [PRIM-01]

# Metrics
duration: 65min
completed: 2026-07-16
---

# Phase 10 Plan 01: Primitivas sem viés — endpoint Theil-Sen + split do estimador Summary

**A base de lucro de valuation trocou o `median()`-do-meio (que punia crescimento com haircut −g/(1+g)) pelo ENDPOINT de uma regressão robusta Theil-Sen no ano atual, com o motor cíclico preservando a média through-cycle via a nova `media_ciclo` — BLIND-03 curado, orçamento de 3 knobs intacto.**

## Performance

- **Duration:** ~65 min (inclui 2 checkpoints de usuário)
- **Started:** 2026-07-16T08:01Z (Task 2 RED)
- **Completed:** 2026-07-16T11:21Z
- **Tasks:** 3 (Task 1 decisão; Task 2 RED; Task 3 GREEN)
- **Files modified:** 10

## Accomplishments
- `base_normalizada` = endpoint Theil-Sen (`scipy.stats.theilslopes`) avaliado no ano atual: reflete o crescimento recente, robusto a 1 outlier; ladder curta (vazio→None, N=1→valor, N=2→média) + GUARD `endpoint<=0 → median(janela)` (nunca base negativa).
- `media_ciclo` (nova função) preserva EXATAMENTE a média/mediana through-cycle antiga para o motor cíclico; `report.py` ramo `"normalizado"` repontado para ela — o cíclico NÃO recebe o endpoint (anti-pattern decisivo).
- BLIND-03 curado: removido o `@pytest.mark.xfail` de `test_normalizacao_nao_pune_crescimento` (vira invariante normal), nunca trocado por skip, nunca afrouxado.
- Janela do endpoint = 5, co-change sancionado `config.yaml:57` + `calibracao.lock.yaml:194` no mesmo diff, com trailer `Knob-Change-Justification:` sem ticker; orçamento continua em 3 graus (ERP, n_fade, PIB_real) — Theil-Sen é parameter-free.
- Suíte default: **472 passed, 1 skipped, 34 deselected, 1 xfailed, 0 failed** (sobra BLIND-02b → Fase 12, skip do jackknife → Fase 14).

## Task Commits

1. **Task 1: Decidir a janela do Theil-Sen (3 vs 5)** — checkpoint:decision, resolvido pelo usuário: **janela-5**.
2. **Task 2: Testes RED (endpoint + guard + split)** — `8b983ae` (test)
3. **Task 3: Split do estimador + swap Theil-Sen + remoção do xfail BLIND-03 + co-change janela-5** — `4301f10` (feat)

**Plan metadata:** _(este commit)_ `docs(10-01)`

## Files Created/Modified
- `src/analista/core/normalizacao.py` — `base_normalizada` → endpoint Theil-Sen + guard + ladder; `media_ciclo` (nova, lógica antiga); import scipy; docstring dos dois estimadores.
- `src/analista/core/motores.py` — docstring de `lucro_normalizado` aponta para `media_ciclo`.
- `src/analista/report/report.py` — ramo `"normalizado"`: `base_normalizada` → `media_ciclo`.
- `tests/test_normalizacao.py` — testes do endpoint/guard/fallback/split; reescrita dos 2 testes de mediana antiga; winsor repontado para `media_ciclo`.
- `tests/test_invariantes_v24.py` — xfail do BLIND-03 removido; cabeçalho atualizado.
- `tests/test_fundamentals_consistencia.py` — #1/#2 reescritos para a invariância do endpoint (mais fortes: robustez + reflete-crescimento + endpoint exato).
- `tests/test_consistencia_modos.py` — #3 guarda Core Value cross-menu preservada, proxy da mediana removido; #4 fixture de coerência de direção recalibrada (asserts intactos).
- `tests/classificacao.yaml` — entradas renomeadas/adicionadas (0 órfão).
- `config.yaml` / `calibracao.lock.yaml` — `normalizacao.anos_media: 3 → 5` (co-change).

## Decisions Made
- **Janela-5** (checkpoint): a regressão robusta com 3 pontos persegue um pico terminal; com 5 separa o outlier da tendência (RESEARCH Open Q1).
- **Split do estimador**: `base_normalizada` (endpoint, valuation) vs `media_ciclo` (média, cíclico) — editar uma função global quebraria o motor cíclico (CSNA3).

## Deviations from Plan

### Rewrites autorizados (Option A — checkpoint de decisão do usuário)

**1. [Rule 1 - Escopo] 4 testes a jusante do endpoint reescritos (fora da lista literal do plano)**
- **Found during:** Task 3 (suíte default vermelha em 4 testes não enumerados pela RESEARCH)
- **Issue:** `base_lucro_normalizada`/`lpa_valuation` (consumidores de valuation) passaram a receber o endpoint (comportamento do plano), quebrando 2 testes `invariante` que codificavam a mediana antiga e 2 testes `contrato` cross-modo.
- **Fix:** Após checkpoint (Option A aprovado): #1/#2 (`invariante`) reescritos para a invariância do endpoint (robustez preservada + reflete-crescimento + endpoint exato); #3 (`contrato`, Core Value) — igualdade cross-menu preservada, removido só o proxy `!= roe(ult)` preso à mediana; #4 (`contrato`, Core Value) — as 3 asserts de coerência de direção mantidas intactas, só os NÚMEROS das fixtures recalibrados (exatamente a doutrina escrita do próprio teste), restaurando a coerência (regressão +31% / DDM SUBAVALIADA).
- **Files modified:** tests/test_fundamentals_consistencia.py, tests/test_consistencia_modos.py, tests/classificacao.yaml
- **Verification:** os 4 passam; suíte default 0 failed; nenhuma tolerância afrouxada, nenhum xfail→skip, nenhum assert de guarda Core Value removido.
- **Committed in:** `4301f10`

**2. [Rule 1 - Doc] Docstring de `motores.lucro_normalizado` atualizada para `media_ciclo`**
- **Found during:** Task 3
- **Issue:** a docstring citava `base_normalizada` como o estimador do cíclico — falso após o split.
- **Fix:** referência trocada para `media_ciclo` (a média through-cycle).
- **Files modified:** src/analista/core/motores.py
- **Committed in:** `4301f10`

---

**Total deviations:** 2 (reescrita de testes autorizada por checkpoint + correção de docstring). Ambas dentro do espírito do PRIM-01; nenhum scope creep de produção (só `normalizacao.py`/`report.py`/`motores.py` docstring). Golden ITUB4=32.88 NÃO tocado (é do plano 10-04).

## Issues Encountered
- 4 testes a jusante quebraram (não previstos pela RESEARCH break-table). Resolvidos via checkpoint de decisão (Option A) sem afrouxar guardas — ver Deviations.

## Threat Flags
Nenhuma superfície nova. T-10-02 (endpoint negativo/degenerado) mitigado como planejado: guard `endpoint<=0 → median` + ladder N=0/1/2.

## User Setup Required
None.

## Next Phase Readiness
- PRIM-01 entregue. Base de valuation reflete o ano recente; motor cíclico preserva a média through-cycle.
- Pronto para 10-02 (PRIM-02 `roe_valuation` = mediana dos ROEs anuais — vai mover o RIM do ITUB4 32,88→31,52), 10-03 (PRIM-03/04 winsor + deflação IPCA) e 10-04 (PRIM-05 deletar o golden ITUB4=32,88).
- **Blocker/nota:** o golden ITUB4=32,88 continua no repo (deleção é do 10-04, não deste plano).

## Self-Check: PASSED
- FOUND: 10-01-SUMMARY.md
- FOUND commit 8b983ae (Task 2 RED)
- FOUND commit 4301f10 (Task 3 GREEN)
- theilslopes present in normalizacao.py; media_ciclo wired in report.py

---
*Phase: 10-primitivas-sem-vi-s-prim*
*Completed: 2026-07-16*
