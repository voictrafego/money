---
phase: 01-classificador-de-arqu-tipo-roteamento
plan: 08
subsystem: engine
tags: [ranking, comparables, regressao-pl, arquetipo, divergencia, cli, python]

# Dependency graph
requires:
  - phase: 01 (P01–P05, P07)
    provides: "classificador de arquétipo (core/arquetipo.py) + registry ARQUETIPO_MOTOR + suspensão D-04 no Analisar (report.py)"
provides:
  - "Freio do modo Ranking (Achado 3): cmd_rank não estampa alvo de regressão frágil (R²≈0 / n<10), degenerado (ROMI3 −98%) nem de ticker suspenso por arquétipo (motor_pendente)"
  - "Helper puro alvo_regressao_confiavel(reg, pa, motor_pendente) em cli.py (gate testável do alvo)"
  - "Helper puro comparables.divergencia_entre_lentes(v_a, v_b, limiar) + LIMIAR_DIVERGENCIA (SINALIZAÇÃO do Achado 4)"
  - "cmd_rank emite AVISO quando as duas lentes (DDM absoluto × regressão relativa) divergem além do limiar"
affects: [fase-2-motores-por-arquetipo, fase-3-veredito-honesto, reconciliacao-ensemble]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Freio de output como helper puro/testável (recebe reg + arquétipo, devolve se/como exibir) — a NOTA do ranque fica intacta, só a coluna alvo/upside é governada"
    - "Divergência como SINALIZAÇÃO honesta (não reconciliação): helper puro (divergiu, razão=maior/menor) tratando None/0/negativo com segurança"
    - "Suspensão por arquétipo replicada no Ranking via arquetipo.classificar + ARQUETIPO_MOTOR (paridade cross-modo com a D-04 do Analisar)"

key-files:
  created:
    - "tests/test_ranking_freio.py"
  modified:
    - "src/analista/cli.py"
    - "src/analista/core/comparables.py"

key-decisions:
  - "Freio do Ranking (Achado 3): alvo de regressão só é estampado como preço-alvo quando reg NÃO é frágil (r2_baixo/amostra_pequena), o upside NÃO é degenerado (>LIMIAR_UPSIDE_ABSURDO=−0,90) e o arquétipo tem motor (não motor_pendente) — paridade com a suspensão D-04 do Analisar. A NOTA do ranque permanece intacta."
  - "Divergência entre lentes (Achado 4) é SINALIZAÇÃO, não reconciliação: LIMIAR_DIVERGENCIA=2× (const de módulo); a reconciliação/ensemble real (DDM × motor do arquétipo) depende da Fase 2 e é escopo da Fase 3 — explicitamente deferida."
  - "Sem config.yaml novo: limiares como constantes de módulo em comparables.py (padrão LIMIAR_R2/LIMIAR_AMOSTRA já existente). ddm.py/selo.py intocados."

patterns-established:
  - "Gate do alvo antes de imprimir (cmd_rank → RegressaoPL.r2_baixo/.amostra_pequena + motor_pendente)"
  - "2ª lente (DDM mid) obtida read-only via report.analisar_acao dentro do cmd_rank apenas para sinalizar divergência"

requirements-completed: [SAN-01, ENS-01]

# Metrics
duration: 22min
completed: 2026-07-11
---

# Phase 1 Plan 08: Freio do Ranking + Sinalização de Divergência Summary

**cmd_rank passa a frear alvos de regressão frágeis/absurdos/suspensos por arquétipo (Achado 3) e a AVISAR honestamente quando as duas lentes da mesma ação divergem >2× (Achado 4 — sinalização, reconciliação deferida à Fase 3).**

## Performance

- **Duration:** ~22 min
- **Completed:** 2026-07-11
- **Tasks:** 2 (ambas TDD: RED → GREEN)
- **Files modified:** 3 (2 modificados + 1 criado)

## Accomplishments
- **Achado 3 fechado:** `cmd_rank` não estampa mais alvo de regressão cru como verdade. Freio em quatro condições — sem alvo, regressão frágil (`r2_baixo` R²≈0 ITUB4/BBAS3, ou `amostra_pequena` n<10), alvo degenerado (ROMI3 R$0,10 / −98%), e `motor_pendente` (suspensão por arquétipo, paridade D-04). A coluna alvo vira "—" com o motivo; a NOTA do ranque fica intacta.
- **Achado 4 (sinalização) fechado:** helper puro `divergencia_entre_lentes` + `LIMIAR_DIVERGENCIA=2×`; `cmd_rank` obtém a faixa DDM (read-only via `analisar_acao`) e emite `⚠ TICKER: lentes divergem ~Nx ...` quando DDM × regressão divergem além do limiar (WEGE3 ~3×, ITUB4 ~2,2×).
- **Escopo honesto:** reconciliação/ensemble real (DDM × motor do arquétipo) explicitamente DEFERIDA à Fase 3 (pós-Fase 2) — comentário no código e nesta SUMMARY. Nenhuma lógica de reconciliação adicionada.

## Task Commits

1. **Task 1 (RED): tests do freio** - `14c3483` (test)
2. **Task 1 (GREEN): freio R²/n + suspensão por arquétipo** - `50f2fba` (feat)
3. **Task 2 (RED): tests de divergência** - `456d0f9` (test)
4. **Task 2 (GREEN): sinalização de divergência entre lentes** - `e8be1a9` (feat)

_TDD: cada task com commit RED (test falhando) → GREEN (implementação)._

## Files Created/Modified
- `tests/test_ranking_freio.py` (criado) - 14 testes: freio (r2/n/degenerado/motor_pendente/guard inverso), resolução de motor_pendente por arquétipo, e helper de divergência (WEGE3/ITUB4/guard/None-zero-neg).
- `src/analista/cli.py` (modificado) - `_motor_pendente(c, cfg)`, `alvo_regressao_confiavel(reg, pa, motor_pendente)`, e wiring no `cmd_rank` (freio na coluna alvo + avisos de divergência via DDM mid read-only).
- `src/analista/core/comparables.py` (modificado) - constantes `LIMIAR_UPSIDE_ABSURDO=−0.90` e `LIMIAR_DIVERGENCIA=2.0`; helper puro `divergencia_entre_lentes`.

## Decisions Made
- Freio como helper puro em `cli.py` (satisfaz key_link "cli.py contains r2_baixo") consumindo as propriedades `RegressaoPL.r2_baixo/.amostra_pequena` já existentes; helper de divergência em `comparables.py` (const de módulo + função pura).
- Ordem do freio: sem-alvo → frágil (r2/n) → degenerado → motor_pendente. Na prática todos os casos reais do audit têm n=4–5 (< LIMIAR_AMOSTRA=10), então o freio já suprime a maioria dos alvos crus — que é exatamente o defeito do Achado 3.
- Divergência é computada sobre o alvo de regressão CRU (mesmo quando o freio o suprime no display), porque o sinal honesto é "as lentes brutas discordam" — independente da supressão de exibição. WEGE3/ITUB4 (motor_pendente) disparam o aviso.

## Deviations from Plan

None - plan executed exactly as written. Ambas as tasks seguiram o ciclo TDD (RED→GREEN) e os limiares/casos-alvo do audit sem necessidade de auto-fix.

## Issues Encountered
None.

## Known Stubs
None. O freio e a sinalização estão ligados a dados reais (RegressaoPL/PrecoAlvo/arquétipo/faixa DDM). A reconciliação/ensemble NÃO é stub — é escopo declarado da Fase 3, não uma pendência silenciosa desta plan.

## Scope Boundary (honrada)
Achado 4 FULL (ensemble/reconciliação DDM × motor do arquétipo) depende da Fase 2 e ficou FORA de escopo. Implementado apenas o SINAL honesto de divergência. Nenhuma fórmula de valuation alterada; `core/ddm.py` e `report/selo.py` intocados (verificado por `git diff`).

## TDD Gate Compliance
Ambas as tasks têm par de commits `test(...)` (RED) → `feat(...)` (GREEN) no git log — gate RED/GREEN satisfeito para as duas.

## Next Phase Readiness
- Fase 2 (motores por arquétipo) pluga os motores primários no registry; quando um arquétipo deixa de ser `motor_pendente`, o freio do Ranking passa a exibir o alvo automaticamente (sem mexer no cmd_rank).
- Fase 3 (veredito honesto) consome o sinal de divergência já emitido aqui para construir a reconciliação/ensemble real (DDM × motor). O helper `divergencia_entre_lentes` e `LIMIAR_DIVERGENCIA` são a base pronta.

---
*Phase: 01-classificador-de-arqu-tipo-roteamento*
*Completed: 2026-07-11*
