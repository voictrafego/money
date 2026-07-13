---
phase: 04-rim-com-valor-terminal-ke-revisado
plan: 03
subsystem: report dispatch (rota de arquétipo) + gate BACKTEST-01
tags: [rim, seguradora, gordon-franquia, arquetipo, CAL-01, loop-d12, tdd, alavanca-3]
requires:
  - "report._intrinseco_por_motor (dispatch motor→intrínseco, ramo motor=='rim')"
  - "core/ddm.py::valor_gordon (perpetuidade de Gordon — reuso PURO)"
  - "core/fundamentals.py::CompanyData.dpa_recorrente (dividendo sustentável — reuso PURO)"
  - "core/arquetipo.py::_setor_casa_token (detecção por limite de palavra — reuso PURO)"
provides:
  - "report._intrinseco_por_motor: ramo de seguradora (Gordon-franquia) ANTES do bank-RIM"
  - "a.motor='seguradora' + intrinseco_motor≈39,87 para BBSE3 (rota documentada, não silenciosa)"
  - "tests/fixtures/fair_values_bancos.yaml::BBSE3.excecao_nota — descreve a ROTA (D-03/D-05)"
  - "cesta 4/4 na banda ±15% (loop D-12 fechado; Fase 06 destravada)"
affects:
  - "veredito de BBSE3 (25,38→39,87; motor rim→seguradora); bancos INALTERADOS"
  - "gate test_backtest_gate_quorum_e_anotacao (3/4→4/4) e test_backtest_cesta_rota_por_ticker"
tech-stack:
  added: []
  patterns:
    - "roteamento de arquétipo em report._intrinseco_por_motor (ponto de corte D-04, antes do RIM)"
    - "reuso PURO de primitiva testada (ddm.valor_gordon) — zero knob numérico novo (D-08)"
    - "never-raise: dado degenerado (dpa/ke None, ke−g≤0) degrada p/ RIM legado, não força a rota"
    - "Gordon de estágio único sobre dividendo SUSTENTÁVEL (dpa_recorrente), não trailing (Pitfall 4)"
key-files:
  created: []
  modified:
    - "src/analista/report/report.py"
    - "tests/test_motores.py"
    - "tests/fixtures/fair_values_bancos.yaml"
decisions:
  - "seguradora capital-light → rota Gordon-franquia (D-03), fora do bank-RIM ancorado em book; mudança minimalista, sem motor novo"
  - "ke da rota = a.ke (CAPM ao vivo), NÃO o ke_rim de balanço large-cap (Pitfall 3); g = g_estavel (2,5%, zero knob)"
  - "a.motor='seguradora' exige excecao_nota no gate (Pitfall 5) — a nota é o que torna a rota documentada, não silenciosa"
metrics:
  duration: 0h20m
  completed: "2026-07-13"
---

# Phase 4 Plan 03: Rota de Seguradora (Gordon-franquia) — Cesta 4/4 Summary

A cesta de bancos fechou **4/4 na banda ±15%**: a BBSE3 — única não-banco — deixou de sair
subvalorizada pelo bank-RIM (R$25,38, ancorado no book minúsculo VPA≈5,35) e passou a rotear por
uma **rota de seguradora capital-light** (Alavanca 3, D-03/D-04). A rota é o **reuso PURO** de
`ddm.valor_gordon` sobre o dividendo sustentável (`dpa_recorrente`), com o Ke do CAPM ao vivo e
g=2,5% — **zero knob numérico novo**, `ddm.py`/`fundamentals.py`/`arquetipo.py` **intocados**.
Resultado: **BBSE3 25,38→R$39,87** (em cima do mid de consenso 39,5), bancos inalterados, loop
D-12 fechado e a Fase 06 (redeploy) destravada.

## What Was Built

- **Ramo de seguradora em `report._intrinseco_por_motor`** (Task 1): inserido **ANTES** do
  `if motor == "rim"`. Quando `motor == "rim"` **E** `arquetipo._setor_casa_token((c.setor or "").lower(),
  ["seguradora"])` casa (BBSE3 setor CVM = "Emp. Adm. Part. - Seguradoras e Corretoras"),
  curto-circuita o RIM e devolve `ddm.valor_gordon(dpa_recorrente×(1+g_estavel), a.ke, g_estavel)`.
  Usa **`a.ke`** (CAPM ao vivo, beta 0,31 → 12,36% — NÃO o `ke_rim` de banco de balanço, Pitfall 3)
  e **`dpa_recorrente()`** (payout×LPA normalizados — NÃO o `dpa_trailing_12m`, Pitfall 4).
  Seta `a.motor = "seguradora"` (rótulo honesto). **Never-raise**: se `dpa_recorrente()`/`a.ke` forem
  None ou `valor_gordon` devolver None (ke−g ≤ 0), **não força a rota** — cai (fall-through) para o
  RIM legado.
- **`test_rota_seguradora_bbse3_gordon_franquia` + `test_rota_seguradora_nao_pega_banco`** (Task 1,
  TDD): a rota é exercitada de ponta a ponta via `report.analisar_acao` sobre o snapshot congelado
  (carregado por `backtest.carregar_snapshot`). Um teste crava BBSE3 → `motor=="seguradora"` e
  `intrinseco_motor ≈ 39,87 (±R$1)` com **auto-consistência** (igualdade < 1e-9 contra o
  `valor_gordon` recomputado dos insumos congelados). O outro é a **regressão negativa**: ITUB4
  (setor "Bancos") NÃO casa o token → segue pelo RIM (30–40).
- **`fair_values_bancos.yaml::BBSE3.excecao_nota`** (Task 2): reescrita de "falha documentada" para
  **"ROTA documentada"** — "seguradora capital-light → rota DDM-franquia (Gordon sobre o dividendo
  sustentável), fora do bank-RIM ancorado em book — arquétipo documentado (D-03/D-05)". Com BBSE3
  roteando `motor != "rim"`, a nota é o que impede a **rota silenciosa** que o gate
  `test_backtest_cesta_rota_por_ticker` barra (Pitfall 5).

## TDD Cycle (Task 1)

- **RED** (commit `82e8ef3`, `test(04-03)`): teste da rota escrito primeiro. Falha confirmada —
  `AssertionError: assert 'rim' == 'seguradora'` (o ramo não existe → BBSE3 sai R$25,38 pelo RIM).
- **GREEN** (commit `3474419`, `feat(04-03)`): ramo de seguradora implementado. `pytest
  tests/test_motores.py -k seguradora` verde (2 passed); `test_motores.py` completo verde (16 passed),
  incluindo os goldens do RIM (não-regressão).
- **REFACTOR**: nenhum necessário.

## Verified Numbers (batem com o research §Alavanca 3 e §Números Finais)

| Ticker | RIM antes | Depois | Motor | Banda ±15% | Alavanca | Veredito |
|--------|-----------|--------|-------|------------|----------|----------|
| ITUB4 | 32,88 | **32,88** (inalterado) | rim | 25,93–57,50 | — | ✅ PASS |
| BBAS3 | 43,89 | **43,89** (inalterado) | rim | 17,00–44,85 | 2 (it. 04-02) | ✅ PASS |
| BBDC4 | 13,37 | **13,37** (inalterado) | rim | 12,75–27,60 | 2 (it. 04-02) | ✅ PASS |
| BBSE3 | 25,38 | **39,87** | seguradora | 28,05–52,90 | 3 (Gordon-franquia) | ✅ PASS (rota documentada) |

→ **4/4 na banda ±15%** — supera o piso D-05 (3/4+1) e fecha o loop D-12. Inputs congelados do BBSE3:
`dpa_recorrente=3,83404 · ke_live=0,123572 · g=0,025 → valor_gordon(3,83404×1,025; 0,123572; 0,025) = 39,868`.

## Deviations from Plan

None — plan executado exatamente como escrito. O alvo pré-computado (BBSE3 ≈ R$39,87) foi atingido
dentro de ±R$1 sem afrouxar bounds nem tocar nos motores; os bancos ficaram bit-idênticos.

## Escopo respeitado (reuso PURO)

`git diff` do plano tocou APENAS: `src/analista/report/report.py`, `tests/test_motores.py`,
`tests/fixtures/fair_values_bancos.yaml`. **NÃO** inclui `ddm.py`, `fundamentals.py`, `arquetipo.py`,
`selo.py` nem `lentes.py` — as primitivas foram só CHAMADAS. Zero knob numérico novo (reusa
`cfg["ddm"]["g_estavel"]` e `a.ke`).

## Threat Surface Scan

Nenhuma superfície nova. Roteamento numérico puro reusando primitiva já testada (`ddm.valor_gordon`);
sem rede, sem I/O, sem input não-confiável novo (T-04-03 accept). Never-raise preservado
(T-04-04 mitigate): dpa/ke None ou ke−g ≤ 0 → degrada para o RIM legado, não força a rota.

## Authentication Gates

Nenhum.

## Known Stubs

Nenhum. A cesta chega a 4/4 real (BBSE3 roteia e valua ao vivo pela rota Gordon-franquia). A nota
observada no ramo fronteiriço (`_veredito_fronteirico` também chama `_intrinseco_por_motor`) é
inócua na prática: BBSE3 hard-roteia financeira (soberano, não-fronteiriço), então só o dispatch
primário aciona a rota — os candidatos do ramo fronteiriço não quebram.

## Nota de honestidade (fora de escopo, não-bloqueante)

`a.motor_rotulo` é computado ANTES do dispatch (a partir de `a.motor="rim"`), então para a BBSE3 o
rótulo de exibição na UI segue o de "rim" mesmo com `a.motor="seguradora"`. O gate e os critérios de
aceite checam `a.motor`/`intrinseco_motor` (corretos); o label de display não estava no escopo
(files_modified = report.py apenas; `MOTOR_ROTULO` vive em `motores.py`, fora do escopo). Registrado
para um polish futuro de UI se desejado — a `excecao_nota` já documenta a rota.

## Test Results

- `pytest tests/test_motores.py -k seguradora -x -q`: **2 passed** (rota + regressão negativa).
- `pytest tests/test_motores.py -q`: **16 passed** (inclui goldens do RIM — não-regressão).
- `pytest tests/test_backtest_bancos.py -q`: **4 passed** (cesta 4/4; BBSE3 motor="seguradora" com nota).
- `pytest -q` (suíte completa): **447 passed** (baseline 445 pós-04-02 + 2 testes novos; goldens
  ddm/vulc3/selo/consistência intactos).
- `ddm.py`/`fundamentals.py`/`arquetipo.py`/`selo.py`/`lentes.py`: intocados.

## Self-Check: PASSED

- `src/analista/report/report.py` — FOUND (ramo de seguradora antes do RIM)
- `tests/test_motores.py` — FOUND (test_rota_seguradora_*)
- `tests/fixtures/fair_values_bancos.yaml` — FOUND (BBSE3.excecao_nota descreve a rota)
- Commit `82e8ef3` (RED) — FOUND
- Commit `3474419` (GREEN feat) — FOUND
- Commit `9cf3279` (docs excecao_nota) — FOUND
- Cesta via rodar_cesta: 4/4 (ITUB4 32,88 · BBAS3 43,89 · BBDC4 13,37 · BBSE3 39,87/seguradora)
- Suíte completa: 447 passed, 0 failed
