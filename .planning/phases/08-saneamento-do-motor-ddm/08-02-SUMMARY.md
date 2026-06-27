---
phase: 08-saneamento-do-motor-ddm
plan: 02
subsystem: valuation
tags: [FIX-02, crescimento, g-sustentavel, payout-valuation, ddm, golden-rebaseline]

requires:
  - phase: 08-01 (FIX-04)
    provides: "roe_valuation()/payout_valuation() canônicos (base de lucro normalizada) que alimentam o g_fundamentos"
provides:
  - "Seleção de g_alto subordinada ao g sustentável: teto = g_fund = ROE_norm × (1 − payout_valuation)"
  - "Payout ≥ 100% ⇒ g_fund ≤ 0 ⇒ g_alto = 0 (piso artificial g_estavel removido da fase explícita)"
  - "tests/test_growth_reconciliacao.py: golden da reconciliação (payout≥100%→0; teto g_fund; teto 0.25; trava ≤Ke)"
affects: [08-03 (FIX-03 CAPM/Ke — a trava ≤Ke do g_alto consome o novo Ke), 08-04 (FIX-06 regressão VULC3)]

tech-stack:
  added: []
  patterns:
    - "g_alto subordinado ao reinvestimento real: precedência g_fund (sustentável) → teto absoluto 0.25 → trava ≤ Ke"
    - "g_estavel deixa de ser piso do g_alto da fase explícita; permanece SÓ como taxa da perpetuidade no DDM"

key-files:
  created:
    - tests/test_growth_reconciliacao.py
  modified:
    - src/analista/report/report.py
    - tests/test_consistencia_modos.py

key-decisions:
  - "g_fund é TETO do g_alto (min com o CAGR), não o substituto direto: série constante (CAGR=0) ⇒ g_alto=0 mesmo com g_fund>0"
  - "Piso g_estavel removido da seleção do g_alto da fase explícita; g_estavel segue sendo a taxa da perpetuidade no DDM"
  - "g_alto nunca negativo: max(0.0, ...) substitui o antigo max(g_estavel, ...)"

patterns-established:
  - "Reconciliação g × fundamentos travada por golden de relação (g_alto==g_fund / ==0 / ==0.25 / ==Ke), robusto a winsorização"

requirements-completed: [DDM-FIX-02]

duration: ~20min
completed: 2026-06-26
---

# Phase 8 Plan 02: Reconciliação g × fundamentos (FIX-02) Summary

**O `g_alto` da fase explícita deixa de ser um haircut arbitrário do CAGR e passa a ser subordinado ao crescimento sustentável `g_fund = ROE_norm × (1 − payout_valuation)`: payout ≥ 100% (caso VULC3) zera o g_alto, matando a fonte do valuation explosivo.**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2
- **Files modified:** 3 (1 criado, 2 modificados)
- **Tests:** 121 passed (era 117 + 4 de reconciliação)

## Accomplishments

- Nova regra de seleção do g_alto em `analisar_acao`: o teto passa a ser `g_fundamentos` (calculado com o MESMO payout do valuation), com precedência **g_fund (sustentável) → teto absoluto 0.25 → trava ≤ Ke** (FIX-01 preservada).
- Piso artificial `g_estavel` REMOVIDO da fase explícita: quando os fundamentos não sustentam crescimento (payout ≥ 100% ⇒ g_fund ≤ 0), o g_alto cai para 0 em vez de travar no piso de 2,5%.
- Golden de reconciliação cobrindo os 4 contratos: payout≥100%→g_alto=0 (sem piso), g_fund<CAGR→g_alto=g_fund, teto absoluto 0.25, trava ≤Ke.
- **VULC3 (payout_valuation = 100%): g_alto adotado = 0,0** (antes 25%), com o DDM ainda degradando para um intrínseco finito (sanity sintético: 13,58) — sem exceção.

## Task Commits

1. **Task 1 (RED): golden de reconciliação** - `523c35a` (test)
2. **Task 1 (GREEN): subordinar g_alto ao g sustentável** - `bc6f332` (feat)
3. **Task 2: rebaseline justificado do veredito** - `d6dec48` (test)

_TDD: Task 1 = RED (test) → GREEN (feat). Sem fase REFACTOR (mudança pontual)._

## Files Created/Modified

- `src/analista/report/report.py` — seleção do g_alto reescrita: teto = g_fundamentos (min com CAGR), clamp `max(0.0, min(g_alto, 0.25))`, piso g_estavel removido; trava `min(a.g_alto, a.ke)` (FIX-01) intacta.
- `tests/test_growth_reconciliacao.py` (novo) — 4 goldens de relação, fixtures offline calibradas (g_fund=0.02/0.32/0.15; CAGR/Ke controlados via beta).
- `tests/test_consistencia_modos.py` — comentário de rebaseline em `test_veredito_direcao_coerente` (g_alto da fixture-alvo 0,025→0,0; direção SUBAVALIADA preservada).

## Rebaseline dos golden (com justificativa)

| Asserção / fixture | Antes | Depois | Por que o novo número é o correto pelo método |
|--------------------|-------|--------|-----------------------------------------------|
| `g_alto` da fixture-alvo (`test_veredito_direcao_coerente`, série constante) | 0,025 (piso g_estavel) | 0,0 | Série constante ⇒ CAGR=0; o g_fund=0,125 é só TETO (não eleva o CAGR=0) e o piso g_estavel foi removido. Empresa que não cresceu o lucro não projeta crescimento. vmin≈6,79 > preço 6,00 ⇒ direção SUBAVALIADA mantida, **assert intacto** (sem recalibrar preço/lucro/PL). |

`test_ddm.py`/`test_multiples.py` (matemática pura com literais) e os goldens de `test_fundamentals_consistencia.py` (ROE/LPA de valuation, não dependem da seleção de g) permanecem inalterados.

## Decisions Made

- **g_fund como TETO (min com o CAGR), não substituto.** O behavior do plano ("g_fund > 0 e < CAGR ⇒ g_alto == g_fund") e os must_haves ("o teto do g_alto adotado é o g sustentável") definem g_fund como limite superior. Consequência: numa série constante (CAGR=0), g_alto = min(0, g_fund) = 0 — o crescimento histórico nulo vence o sustentável. Honesto: a empresa não cresceu.
- **Piso substituído por `max(0.0, ...)`.** g_estavel sai da seleção do g_alto (CONTEXT FIX-02: "sem piso artificial g_estavel quando fundamentos não sustentam"); continua sendo a taxa da perpetuidade no DDM (`ddm_dois_estagios`/`g_estavel`), que **não** foi tocada.

## Deviations from Plan

None - plan executed exactly as written. As 4 fixtures de reconciliação saíram bem calibradas de primeira (RED falhou nos casos discriminantes 1 e 2; GREEN passou os 4); a fixture existente não precisou de recalibração de preço porque a direção do veredito se manteve.

## Issues Encountered

None.

## Known Stubs

Nenhum. Toda a lógica consome dados reais via os métodos canônicos (`roe_valuation`/`payout_valuation`).

## Threat Flags

Nenhuma nova superfície. T-08-03 (DoS div/zero no DDM com g_alto=0) mitigado: o guard `ke > g_estavel` segue valendo e o sanity sintético confirma intrínseco finito com g_alto=0. T-08-04 (alteração deliberada do valuation pela remoção do piso) aceito e travado por golden.

## Next Phase Readiness

- 08-03 (FIX-03 CAPM): a trava `g_alto ≤ Ke` agora consome o Ke vivo que a próxima fase vai recalibrar — a reconciliação fica robusta a um Ke mais alto (small cap BR).
- 08-04 (FIX-06): VULC3 como caso de regressão pode agora cravar g_alto ≈ 0 para payout ≥ 100%.

## Self-Check: PASSED

- Arquivos verificados: report.py, test_growth_reconciliacao.py, test_consistencia_modos.py, 08-02-SUMMARY.md — todos presentes.
- Commits verificados: 523c35a (test RED), bc6f332 (feat GREEN), d6dec48 (test rebaseline) — todos no histórico.
- Suíte: 121 passed.

---
*Phase: 08-saneamento-do-motor-ddm*
*Completed: 2026-06-26*
