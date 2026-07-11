---
phase: 01-classificador-de-arqu-tipo-roteamento
plan: 02
subsystem: report/valuation-routing
tags: [arquetipo, roteamento, veredito, suspensao-d04, funil, tdd]
requires:
  - "core/arquetipo.classificar(c, cfg) + ARQUETIPO_MOTOR (Plan 01)"
  - "report.analisar_acao — funil único de valuation (CAPM→DDM→veredito→selo)"
provides:
  - "AnaliseAcao expõe arquetipo/motor/arquetipo_fronteirico/arquetipo_candidatos/motor_pendente (read-only, aditivo)"
  - "roteamento por arquétipo plugado entre CAPM (:134) e DDM (:136) do funil"
  - "suspensão D-04: veredito primário suspenso via prefixo 'VERIFICAR' quando o motor do arquétipo chega só na Fase 2"
  - "render mínimo 'Arquétipo: X → motor Y' no cabeçalho do relatório"
affects:
  - "Fase 2 (motores por arquétipo): ao plugar motor no ARQUETIPO_MOTOR, motor_pendente vira False e o veredito passa a sair do motor certo"
  - "Fase 3 (veredito honesto/ensemble): consome arquetipo/candidatos já expostos em AnaliseAcao"
tech-stack:
  added: []
  patterns:
    - "roteamento read-only no ponto único de valuation (não recalcula método; lê classificar())"
    - "suspensão de veredito reusando prefixo existente 'VERIFICAR' (firewall selo↛report preservado por construção)"
    - "fidelity fix de fixture (eh_concessionaria=True) casa a ingestão real sem afrouxar asserção"
key-files:
  created:
    - tests/test_arquetipo_roteamento.py
  modified:
    - src/analista/report/report.py
    - tests/test_consistencia_modos.py
    - tests/test_selo.py
    - tests/test_guardrails_fix06.py
decisions:
  - "Roteamento é aditivo/read-only no funil: DDM segue rodando sempre como lente (popula sensibilidade/vmin/vmax), a suspensão só troca o texto do veredito primário"
  - "Suspensão D-04 é GENÉRICA por motor_pendente (não condicionada a arquetipo==financeira): crescimento/ciclica/holding também suspendem até a Fase 2"
  - "Reusar o prefixo 'VERIFICAR' (não criar token novo) preserva o par faixa_do_veredito↔_veredito_token e o firewall selo↛report intactos (T-01-05/T-01-08)"
  - "Fidelity fix nas fixtures reguladas (eh_concessionaria=True) em vez de estreitar a regra D-04 — casa a derivação real de build.py:68 sem enfraquecer teste"
metrics:
  duration: "~0h35m"
  completed: "2026-07-11"
  tasks: 3
  tests_added: 7
  suite: "354 passed (baseline 348 + 6 líquidos; 7 novos e2e, sem golden rebaseado)"
---

# Phase 1 Plan 02: Roteamento por Arquétipo no Funil + Suspensão D-04 Summary

Plugou o classificador da Fase 1 (`core/arquetipo.classificar`) no ponto único de valuation
`report.analisar_acao`, entre o CAPM e o DDM: `AnaliseAcao` passa a expor arquétipo/motor/
fronteiriço antes do valuation, e o veredito primário é honestamente **suspenso** (prefixo
"VERIFICAR", sem estampar 'evitar') sempre que o motor do arquétipo só chega na Fase 2 —
resolvendo o caso ITUB4 (banco carimbado "evitar" pelo DDM que não serve a ele) sem tocar
`selo.py` nem `core/ddm.py` e mantendo a pagadora regulada (TAEE11) idêntica ao baseline (ENG-06).

## What Was Built

- **`report.py` — import + 5 campos aditivos em `AnaliseAcao`** (`arquetipo`, `motor`,
  `arquetipo_fronteirico`, `arquetipo_candidatos`, `motor_pendente`), read-only.
- **Roteamento no funil (:134→:136):** `arquetipo.classificar(c, cfg)` chamado UMA vez após o
  CAPM; `ARQUETIPO_MOTOR.get(chave)` resolve o motor; `motor_pendente = (motor is None)`. O bloco
  DDM segue textualmente intacto e roda SEMPRE como lente conservadora (popula sensibilidade/
  vmin/vmax que a UI e `test_guardrails_fix06` exigem).
- **Suspensão D-04 no veredito:** guard `if a.motor_pendente:` ANTES do bloco DDM de veredito
  (que virou `elif`). No ramo pendente o veredito começa com o prefixo existente **"VERIFICAR"**
  (arquétipo X usa o motor Y da Fase 2; o DDM é lente, não o motor) + 1 alerta explicando a
  suspensão. Genérico por `motor_pendente` — vale para financeira/crescimento/cíclica/holding.
- **Render mínimo:** cabeçalho do `relatorio_markdown` exibe `Arquétipo: {chave} → motor {motor}`.
- **Fidelity fix das fixtures reguladas** (Energia Elétrica) que predavam o roteamento por não
  setarem `eh_concessionaria`: `_empresa_solida`/`_empresa_param`/`_empresa_param_crescente`
  (test_consistencia_modos), `_empresa_solida` (test_selo), `_empresa_crescente_solida`
  (test_guardrails_fix06) agora setam `eh_concessionaria = True` → roteiam `pagadora_regulada`
  → motor "ddm" → `motor_pendente=False` → mantêm o veredito DDM (AAA3 continua SUBAVALIADA).
- **`tests/test_arquetipo_roteamento.py`** — 7 goldens e2e via `analisar_acao`: regulada
  motor-ddm/veredito-não-suspenso, financeira suspensa + selo sem 'evitar', anti-Petróleo
  (eh_concessionaria=True não vira regulada), degradação 1-ano, fronteiriço-via-funil (ARQ-02),
  e render "Arquétipo → motor".

## Task Commits

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Campos em AnaliseAcao + import + roteamento no funil | c7b1b73 | src/analista/report/report.py |
| 2 | Fidelity fix fixtures reguladas (eh_concessionaria=True) | 42fa51c | tests/test_consistencia_modos.py, tests/test_selo.py, tests/test_guardrails_fix06.py |
| 3 (RED) | golden e2e falhando (suspensão + render) | 9ced033 | tests/test_arquetipo_roteamento.py |
| 3 (GREEN) | suspensão D-04 + render Arquétipo→motor | 62f2551 | src/analista/report/report.py |

## Verification

- `pytest tests/test_arquetipo_roteamento.py -q` → 7 passed (regulada / financeira-suspensa /
  anti-Petróleo / degradação / fronteiriço-via-funil / render).
- `pytest tests/test_ddm.py tests/test_selo.py tests/test_consistencia_modos.py
  tests/test_vulc3_regressao.py tests/test_guardrails_fix06.py -q` → verde (suíte-trava inteira,
  nenhum golden rebaseado).
- `pytest -q` → **354 passed** (baseline 348 + 6 líquidos; nenhuma asserção antiga quebrada).
- `git diff` NÃO lista `src/analista/report/selo.py` nem `src/analista/core/ddm.py` (firewall e
  DDM puro intactos).
- Auditoria Task 2: `classificar(AAA3, cfg).chave == "pagadora_regulada"` e
  `classificar(VAZIA3, cfg).chave == "pagadora_regulada"` (default degradado) — `audit-ok`.
- `git diff tests/` só ADICIONA `eh_concessionaria = True` — nenhuma asserção de veredito
  removida/afrouxada.

## Deviations from Plan

None - plan executado exatamente como escrito (Tasks 1-3, TDD RED/GREEN, sem REFACTOR necessário).

Nota sobre a ordem do guard: como o `if a.motor_pendente:` roda ANTES do bloco DDM de veredito,
o VULC3 sintético (setor "Têxtil e Vestuário", não-regulado) passa a receber o texto de suspensão
por roteamento (classifica cíclica, motor pendente) em vez do texto DDM-FIX-05 — mas AMBOS começam
com "VERIFICAR", então `test_vulc3_regressao` (que afirma `startswith("VERIFICAR")` e checa
`vmax`/`sensibilidade`, populados pelo DDM que roda sempre) continua verde sem alteração. Isso é
comportamento esperado da suspensão genérica (D-04), não um desvio.

## Threat Model Compliance

- **T-01-05 (prefixo novo quebraria faixa_do_veredito↔_veredito_token):** mitigado — reusado o
  prefixo existente "VERIFICAR"; `test_selo` (par de contrato) verde; nenhum token novo criado.
- **T-01-06 (regressão silenciosa em TAEE11/regulada):** mitigado — golden e2e afirma
  regulada→motor ddm com veredito não-suspenso; fidelity fix garante rota pagadora_regulada;
  test_ddm/test_consistencia_modos/test_guardrails_fix06 verdes travam o caminho DDM (ENG-06).
- **T-01-07 (DoS em CompanyData degradado):** mitigado — golden de degradação (VAZIA3, 1 ano)
  afirma que `analisar_acao` não levanta e popula o arquétipo (default pagadora_regulada,
  motor_pendente=False → veredito "").
- **T-01-08 (acoplamento selo→report na suspensão):** mitigado — suspensão feita 100% do lado do
  report (só string de veredito); `selo.py` não tocado (confirmado por `git diff --name-only`).

## Known Stubs

Nenhum stub que impeça o objetivo do plano. O `motor == "pendente_fase_2"` para os 4 arquétipos
sem motor é **pendência planejada da Fase 2** (motores RIM/normalizado/DCF/SOTP), exposta
honestamente via `motor_pendente=True` + suspensão do veredito — não um stub silencioso.

## Self-Check: PASSED

- Arquivos: tests/test_arquetipo_roteamento.py, src/analista/report/report.py,
  tests/test_consistencia_modos.py, tests/test_selo.py, tests/test_guardrails_fix06.py — todos FOUND.
- Commits: c7b1b73, 42fa51c, 9ced033, 62f2551 — todos FOUND no git log.
