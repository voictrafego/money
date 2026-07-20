---
phase: 14-valida-o-honesta-val
plan: 01
subsystem: validação (engine + testes de blindagem)
tags: [VAL-01, VAL-06, VAL-07, blindagem, closed-form, subtração]
requires:
  - "motores.rim (RIM único, Fase 13)"
  - "a.ke único + g_cap (Fases 11–12) — CONSUMIDOS, não tocados"
provides:
  - "test_soberano_itub4: prova por execução que o motor reproduz o caso do livro em [35,39]"
  - "insumos_itub4_livro (helper BLIND-04a-safe com os insumos do Cap.17)"
  - "excecao_nota morto na árvore viva (nenhuma exceção pode salvar um ticker)"
  - "ADR VAL-07 durável + âncora no backtest.py"
affects:
  - "backtest.rodar_cesta (dict de resultado sem excecao_nota)"
  - "scripts/backtest_bancos.py (coluna de nota removida)"
tech-stack:
  added: []
  patterns:
    - "closed-form soberano: injeta o Ke do livro em motores.rim, assere REGIÃO nunca ponto"
    - "higiene BLIND-04a: literal do ticker + números no helper fora de test_"
    - "subtração fechada por construção: grep do símbolo == 0 na árvore viva"
    - "ADR leve em .planning/decisions/ + comentário-âncora no ponto de tropeço do código"
key-files:
  created:
    - tests/test_soberano_itub4.py
    - .planning/decisions/VAL-07-backtest-temporal.md
  modified:
    - tests/helpers_blindagem.py
    - tests/classificacao.yaml
    - src/analista/backtest.py
    - tests/test_backtest_bancos.py
    - scripts/backtest_bancos.py
decisions:
  - "VAL-01 assere a região [35,39], nunca o ponto 37,22 (== seria golden de nível → BLIND-04a)"
  - "VAL-01 injeta SÓ o Ke do livro (0,1248); zero knob de valuation tocado (config/lock diff vazio)"
  - "VAL-06 fechado por construção: grep excecao_nota == 0 em src/tests/scripts"
  - "VAL-07 = NÃO fazer backtest temporal; PIT honesto inviável com dados gratuitos (registro durável)"
metrics:
  duration: ~18min
  tasks: 3
  files: 7
  completed: "2026-07-20"
---

# Phase 14 Plan 01: Validação honesta (VAL) — landar VAL-01/06/07 Summary

Os três artefatos de validação que NÃO dependem do fixture do hold-out foram landados: o teste
soberano VAL-01 (o critério de aceite mais duro do marco) passa **por execução** — injetando o Ke do
livro (0,1248) no motor RIM com os insumos do Cap. 17, `valor_intrinseco` cai na região de valor do
livro [35, 39]; a lavanderia de overfit `excecao_nota` do v2.3 foi morta e fechada por construção
(grep == 0 na árvore viva); e a decisão de **não fazer** backtest temporal ficou registrada de forma
durável (ADR + âncora no código). **Nenhum knob de valuation tocado** — orçamento intacto em 3 graus.

## What Was Built

### Task 1 — Teste soberano VAL-01 (commit `3b422aa`)
- **`insumos_itub4_livro()`** em `tests/helpers_blindagem.py`, ao lado de `empresa_itub4`, FORA de
  qualquer função `test_`: devolve os insumos do Cap. 17 (`vpa0=19,0`, `roe0=0,1798`, `ke=0,1248`,
  `retencao=0,5331`, `n=10`, `excesso_sustentavel=0,045`, `g_terminal=0,0728`, `roe_terminal=0,1798`)
  com a proveniência documentada. O `g` do livro (10,24%) entra por `roe0×retencao ≈ 9,58%`, não por
  um parâmetro `g_alto` (o RIM não tem esse argumento).
- **`tests/test_soberano_itub4.py`** com `test_soberano_itub4_reproduz_caso_do_livro`
  (`@pytest.mark.contrato`): chama `motores.rim(**insumos_itub4_livro())` e asserta `35,0 <= V <= 39,0`.
  Zero literal de ticker no corpo do teste (`grep -c ITUB4 == 0`), zero `37` (`grep -c 37 == 0`).
- Entrada em `tests/classificacao.yaml` (contrato), sem citar ticker no comentário (hook `-k justificativa`).
- O detector BLIND-04a não flagra o novo teste (`test_detectar_ticker`/`blindagem_meta` verdes).

### Task 2 — Matar o excecao_nota / VAL-06 (commit `2d01ddf`)
- Removida a linha `"excecao_nota": fv.get("excecao_nota")` do dict de `rodar_cesta` (`backtest.py`).
- Deletados os 2 testes da bijeção nota⟺rota-não-rim (`test_nenhuma_rota_diferente_de_rim_e_silenciosa`,
  `test_nenhuma_nota_de_excecao_e_orfa`): sob o RIM único (Fase 13) todo ticker roteia para `rim`, a
  bijeção é vacuamente satisfeita e protegia uma máquina do v2.3. **Preservados**
  `test_backtest_determinismo` e `test_backtest_rotulo_do_motor_consistente`.
- Removida a coluna `r["excecao_nota"]` de `scripts/backtest_bancos.py` (senão KeyError) + scrub das
  docstrings (test + script).
- Removidas as 2 entradas órfãs de `classificacao.yaml` **no mesmo diff** (sem CLASSIFICACAO ORFA).
- **Fechado por construção:** `grep -rn excecao_nota src/ tests/ scripts/` (fora de comentário/`.md`) == 0.
- `tests/fixtures/fair_values_bancos.yaml` NÃO deletado (é referência anti-padrão; só deixa de ser lido).

### Task 3 — ADR VAL-07 (commit `2796678`)
- **`.planning/decisions/VAL-07-backtest-temporal.md`** (ADR leve, 4 seções): contexto, decisão =
  não fazer, justificativa (PIT honesto exige data de publicação de cada DFP — lag ~2–3 meses — e
  reconstruir preço/rf da época, inviável só com dados gratuitos; backtest ingênuo = **vazamento de
  futuro** → número confiante e falso, pior que nenhum), consequência (Future Requirement v2.5+).
- Comentário-âncora em `src/analista/backtest.py` perto de `carregar_snapshot` citando `VAL-07` e
  apontando para o ADR — onde um futuro implementador de backtest tropeça primeiro.

## Verification

- `pytest -k soberano_itub4`: 1 passed (assert `35 <= V <= 39`, região não ponto).
- `grep -rn excecao_nota src/ tests/ scripts/` (árvore viva): **0**.
- `python3 -c "ast.parse(...)"` OK para `backtest.py` e `scripts/backtest_bancos.py`.
- ADR contém "point-in-time" e "vazamento de futuro"; `grep VAL-07 backtest.py` retorna a âncora.
- **Suíte default: 469 passed, 1 skipped, 18 deselected, 0 failed.** `-m golden_nivel`: 18 passed, 0 ORFA.
- **`git diff -- config.yaml calibracao.lock.yaml` VAZIO** — orçamento intacto em 3 graus (ERP, n_fade, PIB_real).

## Deviations from Plan

**1. [Rule 1 - Bug] Literal "ITUB4" vazou para a docstring do teste**
- **Found during:** Task 1 (verificação dos critérios de aceite)
- **Issue:** o primeiro rascunho de `test_soberano_itub4.py` tinha "para o ITUB4" na docstring do
  módulo, violando o critério `grep -c "ITUB4" == 0` (o literal deve viver só no helper).
- **Fix:** trocado por "para o book"; `grep -c ITUB4 == 0` confirmado. O helper segue com o único literal.
- **Files modified:** tests/test_soberano_itub4.py
- **Commit:** 3b422aa (corrigido antes do commit da tarefa)

Fora isso, o plano foi executado exatamente como escrito.

## TDD Gate Compliance

Task 1 marcada `tdd="true"`, mas é um teste de **validação de comportamento existente** (o motor RIM
já reproduz o caso do livro — VERIFIED no RESEARCH, V=38,69 ∈ [35,39]). Não há código de produção a
adicionar: o artefato é o próprio teste (characterization/contract). O teste passou na primeira
execução por construção — esperado numa fase de validação/subtração, não uma falha de gate. Nenhum
motor foi tocado para "fazer passar". Commit único `test(14-01): ...`.

## Known Stubs

Nenhum. Esta é uma fase de validação/subtração; nenhum dado mockado ou placeholder introduzido.

## Self-Check: PASSED
- `tests/test_soberano_itub4.py` — FOUND
- `.planning/decisions/VAL-07-backtest-temporal.md` — FOUND
- Commit 3b422aa — FOUND
- Commit 2d01ddf — FOUND
- Commit 2796678 — FOUND
