---
phase: 14-valida-o-honesta-val
plan: 02
subsystem: validação (harness de blindagem — estatística do jackknife)
tags: [VAL-05, D-10, jackknife, LIMIAR, pre-registro, blindagem]
requires:
  - "mediana_jackknife (helpers_blindagem, Fase 7) — CONSUMIDO como estatístico de forma"
  - "test_nenhum_ticker_e_load_bearing (o call-site que dormia, Fase 7)"
provides:
  - "LIMIAR_JACKKNIFE_PP(n): função de n derivada de null neutro (Monte-Carlo seed-fixo), pura/determinística"
  - "desvio_jackknife_normalizado(valores): estatístico do jackknife normalizado por MAD (escala-invariante)"
  - "test_limiar_jackknife_mede_o_que_promete: prova as duas direções (saudável abaixo / ponte acima)"
affects:
  - "test_nenhum_ticker_e_load_bearing: call-site agora consome LIMIAR(n) + desvio normalizado (acorda no Plano 04)"
tech-stack:
  added: []
  patterns:
    - "pré-registro estatístico por timestamp: o limiar nasce na Wave 2, antes de qualquer v_modelo (Wave 4)"
    - "estatístico escala-invariante: desvio do jackknife / MAD → limiar depende só de n e da forma do null"
    - "null neutro seed-fixo (lognormal suave): a única premissa de modelagem é a forma, não a escala"
    - "mesma unidade nos dois lados do gate: LIMIAR e desvio observado ambos em MADs"
key-files:
  created: []
  modified:
    - tests/helpers_blindagem.py
    - tests/test_blindagem_meta.py
    - tests/classificacao.yaml
decisions:
  - "LIMIAR_JACKKNIFE_PP(n) = percentil 95 do desvio-do-jackknife-normalizado-por-MAD sobre um null lognormal(σ=0,35), M=10000, seed literal 20260720"
  - "Normalizar por MAD (não absoluto): o limiar fica imune à dispersão que a cesta acabou tendo — depende só de n e da forma do null"
  - "n pequeno (3–6) tem limiar legitimamente > 1 (com 3–6 pontos não dá para distinguir ponte de granularidade) — honesto, não clampado; o hold-out exige ≥6/estrato por isso"
  - "VAL-05 NÃO marcado completo: este plano entrega só o LIMIAR; a métrica V/FairValue + jackknife acordado landam no 14-04 (co-reivindicação)"
metrics:
  duration: ~20min
  tasks: 2
  files: 3
  completed: "2026-07-20"
---

# Phase 14 Plan 02: LIMIAR_JACKKNIFE_PP(n) — o gate honesto do jackknife Summary

A constante mágica `LIMIAR_JACKKNIFE_PP = 0.01 [ASSUMIDO]` morreu e virou uma **função de n**
derivada de um **null neutro por Monte-Carlo com seed fixo** — o item de maior incerteza da fase,
entregue como tarefa de derivação estatística. O limiar responde "quanto um único ponto PODE mover
a mediana numa distribuição saudável de n pontos, em MADs" — depende **só de n e da forma do null**,
**nunca** dos valores reais, e foi commitado na Wave 2, **antes de existir qualquer `v_modelo`**
(Plano 04, Wave 4): overfit-proof por construção **e** por timestamp (D-10). Um teste prova as duas
direções por construção (saudável abaixo, ponte load-bearing acima). **Nenhum knob de valuation
tocado** — orçamento intacto em 3 graus.

## What Was Built

### Task 1 — Derivar LIMIAR_JACKKNIFE_PP(n) do null neutro (commit `2702d9d`)
- **`LIMIAR_JACKKNIFE_PP(n)`** em `tests/helpers_blindagem.py`, ao lado de `mediana_jackknife`,
  pura/determinística (`@lru_cache`): simula `M=10000` draws de um null lognormal suave
  (`exp(N(0, σ=0,35))`) com **seed literal `20260720`**, computa o estatístico normalizado de cada,
  e devolve o **percentil 95**. Os 4 parâmetros (seed, σ, M, percentil) são literais fixos no módulo,
  cada um comentado como premissa auditável (T-14-05/T-14-07). A σ (dispersão saudável) é crença
  prévia, jamais medida do hold-out.
- **`desvio_jackknife_normalizado(valores)`** (função-irmã): `mediana_jackknife` desvio ÷ `_mad`.
  Adimensional e escala-invariante — mata a landmine de escala do RESEARCH ("que dispersão a cesta
  acabou tendo"). **NÃO** alterou a assinatura de `mediana_jackknife` (o teste `:88` segue verde).
- **`_mad`** (desvio absoluto mediano) e **`_percentil`** (interpolação linear canônica) como helpers.
- Verificado por execução: **determinística** (bit-a-bit), `LIMIAR(23)=0,286 ∈ (0,1)`, **monótona
  não-crescente** (`LIMIAR(11)=0,50 ≥ LIMIAR(99)=0,069`). A função é grep-clean: zero referência a
  `v_modelo`/`fair_value`/fixture no corpo.

### Task 2 — Call-site de constante para função + teste no null (commit `15950de`)
- Removida a constante `LIMIAR_JACKKNIFE_PP = 0.01` e o parágrafo `[ASSUMIDO]` de
  `test_blindagem_meta.py`, e o parágrafo stale "NA FASE 14: fixar LIMIAR..." do `test_nenhum_
  ticker_e_load_bearing`. `grep -c "LIMIAR_JACKKNIFE_PP = 0.01" == 0`; `grep -c "ASSUMIDO" == 0`.
- **Call-site convertido:** o desvio observado passou de `mediana_jackknife(razoes)` (desvio bruto)
  para `desvio_jackknife_normalizado(razoes)`, e a comparação de `LIMIAR_JACKKNIFE_PP` (constante)
  para `h.LIMIAR_JACKKNIFE_PP(len(razoes))` (função) — **mesma unidade (MADs) nos dois lados**. A
  construção de razões (`:160-165`) **não** foi tocada; `test_nenhum_ticker_e_load_bearing` continua
  `skipped` (o fixture nasce no Plano 03/04).
- **`test_limiar_jackknife_mede_o_que_promete`** (`@pytest.mark.invariante`), espelhando o analog de
  3-verdades: `LIMIAR(31) ∈ (0,1)`; sample saudável (suave) desvio normalizado `0,062 < 0,214`;
  ponte load-bearing (`[0]*15 + [10] + [100]*15`) desvio normalizado `4,5 > 0,214`. Duas direções
  provadas por construção.
- Entrada em `classificacao.yaml` (`invariante`) no mesmo diff, comentário sem ticker.

## Verification

- `pytest -k "limiar_jackknife or mediana_jackknife or blindagem_meta"`: 3 passed, 1 skipped.
- **Suíte default: 470 passed, 1 skipped, 18 deselected, 0 failed** (+1 vs 14-01 = o novo invariante;
  o 1 skipped segue sendo `test_nenhum_ticker_e_load_bearing`, aguardando o fixture do Plano 03/04).
- `-m golden_nivel`: **18 passed, 0 CLASSIFICACAO ORFA**.
- Determinismo e monotonia provados por execução direta (não por suíte verde).
- **`git diff -- config.yaml calibracao.lock.yaml` VAZIO** — orçamento intacto em 3 graus (ERP,
  n_fade, PIB_real). Nenhum knob de valuation tocado.
- Ordem load-bearing (D-10) honrada: o LIMIAR foi commitado (Wave 2) **antes** de qualquer `v_modelo`
  (Wave 4, Plano 04); a derivação vem de um null Monte-Carlo, nunca dos valores reais dos tickers.

## Deviations from Plan

**1. [Rule 1 - Higiene] Os tokens `v_modelo`/`fair_value`/`fixture`/`ASSUMIDO` vazaram para prosa**
- **Found during:** verificação dos critérios de aceite (grep) das Tasks 1 e 2.
- **Issue:** o docstring/comentário da função LIMIAR mencionava `v_modelo`/`fair_value`/fixture (na
  frase "NÃO olha nenhum dado real: nem v_modelo…"), e a prosa do Task 2 reintroduziu `[ASSUMIDO]`
  ao descrever o que morreu — disparando os greps de aceite (`==0`) por falso-positivo textual.
- **Fix:** reescrito com paráfrases ("valores do modelo", "âncoras independentes", "constante mágica")
  mantendo o sentido; função grep-clean e `grep -c ASSUMIDO == 0` confirmados antes do commit.
- **Files modified:** tests/helpers_blindagem.py, tests/test_blindagem_meta.py
- **Commits:** 2702d9d (T1), 15950de (T2) — corrigido antes de cada commit.

**2. [Nota de escopo — não desvio] n pequeno tem limiar > 1**
- Para `n` de 3 a 6 o `LIMIAR_JACKKNIFE_PP` é legitimamente > 1 (o desvio normalizado é intrínseco e
  não-limitado quando um ponto é grande fração da amostra). Isso é a afirmação **honesta** de que com
  3–6 pontos não se distingue ponte de granularidade — por isso o hold-out exige ≥6/estrato e
  `mediana_jackknife` levanta para n < 3. O critério "(0,1) para n típicos" vale para os tamanhos de
  cesta em que o gate roda (n ≳ 9); documentado no docstring, **não clampado** (clampar seria
  dishonesto). O `<verify>` executável (n=23,11,99) passa.

Fora isso, o plano foi executado exatamente como escrito.

## TDD Gate Compliance

Task 2 marcada `tdd="true"`. É um teste de **validação de artefato existente**: a função
`LIMIAR_JACKKNIFE_PP` já nasceu na Task 1 (mesmo plano), então `test_limiar_jackknife_mede_o_que_
promete` passou na primeira execução por construção — esperado numa tarefa de derivação/validação,
não uma falha de gate. Nenhum código de produção foi escrito para "fazer passar" (a função é o
artefato da Task 1; o teste prova que ela mede o que promete). Commit único `test(14-02): ...`.

## Known Stubs

Nenhum. Fase de validação/harness; nenhum dado mockado ou placeholder introduzido. O
`test_nenhum_ticker_e_load_bearing` segue `skipped` **por dependência de fase** (o fixture nasce no
Plano 03/04), não por stub — o comportamento acorda automaticamente quando o `holdout_v24.yaml`
existir.

## Self-Check: PASSED
- `tests/helpers_blindagem.py::LIMIAR_JACKKNIFE_PP` — FOUND (grep `def LIMIAR_JACKKNIFE_PP`)
- `tests/helpers_blindagem.py::desvio_jackknife_normalizado` — FOUND
- `tests/test_blindagem_meta.py::test_limiar_jackknife_mede_o_que_promete` — FOUND (3 passed)
- Commit 2702d9d — FOUND
- Commit 15950de — FOUND
