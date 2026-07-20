---
phase: 14-valida-o-honesta-val
plan: 03
subsystem: validação (substrato do hold-out — cesta estratificada, Commit 1 do D-09)
tags: [VAL-02, VAL-03, D-05, D-06, D-07, D-09, hold-out, fair-value, Graham, Bazin]
requires:
  - "arquetipo.classificar (fonte única de roteamento) — CONSUMIDO"
  - "core/lentes.py (preco_justo_graham, preco_teto_bazin, dpa_medio, vpa) — CONSUMIDO"
  - "helpers_sanidade.carregar_snapshot_sanidade + CAMINHO_SNAPSHOT_LIMPO (loader offline dos 104)"
  - "build.py:168 (eh_concessionaria) — REPLICADO (o loader não persiste o campo)"
provides:
  - "scripts/montar_cesta_holdout.py: montador determinístico (fair-value-only | fill-v-modelo)"
  - "tests/fixtures/holdout_v24.yaml: Commit 1 do D-09 — 38 tickers, SÓ fair_value, sem v_modelo"
  - "test_holdout_estratificado_composicao: prova estrutural da composição (VAL-02)"
affects:
  - "test_nenhum_ticker_e_load_bearing: guarda de wake-up ajustada ao split D-09 (skip sem v_modelo)"
tech-stack:
  added: []
  patterns:
    - "regra de seleção escrita ANTES + gravada no cabeçalho do YAML + snapshot-hash: prova (por git) que a cesta não foi montada olhando o resultado do modelo"
    - "estratificação por market_cap desc (proxy de robustez de dado), ordinal não threshold — evita 4º grau de liberdade"
    - "10 difíceis por baldes de atributo disjuntos da cota (balde raso inteiro + extremos dos fartos em round-robin)"
    - "degradação D-03 representada (sem fair_value ⇒ lentes: []), nunca exclusão silenciosa"
    - "campos em linhas separadas: pré-condição do git blame por linha (prova de ordem do D-09)"
key-files:
  created:
    - scripts/montar_cesta_holdout.py
    - tests/fixtures/holdout_v24.yaml
    - tests/test_holdout_cesta.py
  modified:
    - tests/classificacao.yaml
    - tests/test_blindagem_meta.py
decisions:
  - "Universo = os 104 COMPLETOS (NÃO filtra falhas): o hold-out mede contra âncoras de lucro/dividendo (Graham+Bazin), não de preço/β — filtrar falhas era artefato do spike que rodava o modelo, e esconderia o caso D-03"
  - "eh_concessionaria replicado de build.py:168 no montador — sem isso CONCESSAO_FINITA fica vazio e a cesta valida um roteamento que a produção não usa (warning sign: 0 membros)"
  - "fair_value = ponto médio da faixa [min(Graham,Bazin), max] (escalar, casa o teste que acorda); min/max ao lado, auditáveis"
  - "VAL-02 completo; VAL-03/05 co-reivindicados (a prova de ordem por git + o jackknife acordado fecham no 14-04)"
metrics:
  duration: ~25min
  tasks: 2
  files: 5
  completed: "2026-07-20"
---

# Phase 14 Plan 03: Cesta estratificada do hold-out (Commit 1 do D-09) Summary

O substrato de validação HONESTO do v2.4 nasceu: uma cesta estratificada por arquétipo (≥6 por
estrato onde o universo permite) + 10 "difíceis" deliberados, montada por **regra determinística
escrita ANTES** e gravada como **Commit 1** do D-09 — `holdout_v24.yaml` com **SÓ `fair_value`**
(faixa Graham+Bazin, que parte de lucro/dividendo real, independente do modelo e do preço),
**ZERO `v_modelo`**. É a metade load-bearing da ordem: o `git log` provará que as âncoras foram
cravadas ANTES de o modelo rodar (o `v_modelo` é o Commit 2 / Plano 04). **Nenhum knob de
valuation tocado** — orçamento intacto em 3 graus.

## What Was Built

### Task 1 — Montador determinístico da cesta (commit `a9db387`)
- **`scripts/montar_cesta_holdout.py`** (offline, never-raise, ~template de `spike_eng_rim_104.py`):
  carrega os **104** via `carregar_snapshot_sanidade`, **replica `build.py:168`**
  (`eh_concessionaria = any(token in setor …)`) ANTES de classificar — a LANDMINE crítica do
  RESEARCH: sem o mirror, os ~19 utilities caem em CICLICA e o estrato **CONCESSAO_FINITA fica
  vazio**, validando um roteamento que a produção não usa.
- **Universo = os 104 COMPLETOS, sem filtrar `falhas`** (desvio de escopo consciente, ver abaixo):
  o hold-out mede o modelo contra âncoras Graham+Bazin (lucro/dividendo, não preço/β), então um
  ticker sem dado de mercado ainda tem fair_value e é um "difícil" legítimo.
- **Seleção determinística (D-05/D-06/D-07):** cota 6/estrato por `market_cap` desc (desempate
  alfabético; `None` por último); estrato com universo <6 usa todos e MARCA `cota_incompleta`
  (CRESCIMENTO=4); **10 difíceis** por 4 baldes (P/B<1, prejuízo≤0 nos últimos 3a, payout>100%,
  menor book) DISJUNTOS da cota — todos do balde raso (payout>100%) + extremos ordinais dos fartos
  em round-robin (ordinais, não thresholds mágicos → sem 4º grau de liberdade).
- **`fair_value`** = faixa [min(Graham,Bazin), max] entre as lentes DEFINIDAS (D-02); nenhuma
  definida → **sem fair_value** (D-03, degradação reportada com `lentes: []`, never exclusão
  silenciosa). Modos `--fair-value-only` (Commit 1, default) e `--fill-v-modelo` (Plano 04, recusa
  aqui). **Verificado por execução:** CONCESSAO_FINITA=8 (≥6), 10 difíceis, CRESCIMENTO=4 marcado.

### Task 2 — Commit 1: grava o fixture + teste de composição (commit `a5899b0`)
- **`tests/fixtures/holdout_v24.yaml`** (38 tickers): **cabeçalho** com a regra de seleção completa +
  `snapshot_sha256_12: ea1dba555131` (prova que a cesta não foi montada olhando o resultado); cada
  campo em sua **PRÓPRIA LINHA** (`fair_value`/`fair_value_min`/`fair_value_max`/`lentes`/`arquetipo`/
  `dificil`/`cota_incompleta`/`fonte`/`data`) — pré-condição do git blame por linha (Plano 04).
  **ZERO `v_modelo`**, **ZERO `excecao_nota`** (verificado por parse: 38 entradas limpas). A entrada
  do caso D-03 (book negativo + sem dividendo) entra na cesta **sem `fair_value`**, marcada difícil.
- **`test_holdout_estratificado_composicao`** (`@pytest.mark.contrato`, sem literal de ticker — BLIND-04a-safe):
  5 verdades estruturais — (1) Commit 1 puro (nenhuma entrada com `v_modelo`/`excecao_nota`); (2) cota
  ≥6/estrato OU inteiramente marcado `cota_incompleta`; (3) CRESCIMENTO existe, <6, marcado; (4) ≥10
  difíceis disjuntos por construção; (5) degradação D-03 (sem fair_value ⇒ `lentes: []`). Entrada em
  `classificacao.yaml` no mesmo diff.

## Verification

- `pytest -k "holdout_estratificado or blindagem_meta or load_bearing"`: **5 passed, 1 skipped**.
- **Suíte default: 471 passed, 1 skipped, 18 deselected, 0 failed** (+1 vs 14-02 = o novo contrato de
  composição; o 1 skipped segue sendo `test_nenhum_ticker_e_load_bearing`, aguardando o `v_modelo` do
  Plano 04). `-m golden_nivel`: **18 passed, 0 CLASSIFICACAO ORFA**.
- `holdout_v24.yaml`: **0 `v_modelo`, 0 `excecao_nota`** (parse das 38 entradas), campos em linhas
  separadas, cabeçalho com regra + snapshot-hash. CONCESSAO_FINITA=8 (não-vazio), CRESCIMENTO=4
  marcado, 10 difíceis, entrada D-03 sem fair_value.
- **`git diff -- config.yaml calibracao.lock.yaml` VAZIO** — orçamento intacto em 3 graus (ERP,
  n_fade, PIB_real). Nenhum knob de valuation tocado.
- **Ordem load-bearing (D-09) honrada:** o Commit 1 (`a5899b0`) grava SÓ `fair_value`; o `v_modelo`
  é o Commit 2 (Plano 04). A prova de ordem por `git blame` por linha é o teste do Plano 04.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `test_nenhum_ticker_e_load_bearing` acordou cedo demais ao nascer o fixture**
- **Found during:** Task 2 (verificação — o `pytest -k` do plano ficou vermelho).
- **Issue:** a guarda de skip era `if not h.HOLDOUT_V24.exists()`, que assumia um fixture COMPLETO
  (com `v_modelo`). O D-09 divide o fixture em dois commits: Commit 1 (só fair_value) e Commit 2
  (v_modelo). Com o fixture existindo mas SEM `v_modelo`, `razoes` fica vazia → `mediana_jackknife([])`
  levanta `ValueError` (jackknife exige n≥3). O plano exige que este teste siga **skipped** até o
  Plano 04.
- **Fix:** corrigida a guarda para refletir a readiness REAL do substrato — **skip enquanto não há
  `v_modelo`** (`if not razoes: pytest.skip(...)`), dependência de FASE (never xfail: sinal trocado é
  pior que sinal ausente, como o próprio docstring já argumenta). O **assert do jackknife ficou
  INTACTO** — nada afrouxado, deletado ou trocado por skip casual. É a mesma natureza da guarda
  original (skip por dependência de fase), só com o predicado certo para o split do D-09.
- **Files modified:** tests/test_blindagem_meta.py
- **Commit:** a5899b0 (corrigido antes do commit da tarefa).

**2. [Rule 1 - Escopo do universo] Não filtrar `falhas` (o montador diverge do template do spike)**
- **Found during:** Task 1 (a entrada D-03 esperada — book negativo, sem lente — sumia da cesta).
- **Issue:** o template `spike_eng_rim_104.py` pula `falhas` (tickers sem dado de mercado) porque
  RODAVA `report.analisar_acao` (que exige Ke → β → dado de mercado). O caso D-03 esperado está em
  `falhas` (sem preço/β), então filtrar o excluía — contrariando o critério de aceite ("aparece na
  cesta SEM fair_value, nunca omitido").
- **Fix:** o montador classifica os **104 completos**, sem filtro de `falhas` — coerente com a
  natureza do hold-out (âncoras de lucro/dividendo, não de preço) e com a distribuição do RESEARCH
  (que somava 104). Tickers sem `market_cap` sortam por último na cota (não viram cota indevidamente);
  no Plano 04 eles degradam para sem `v_modelo` (never-raise) e caem fora do jackknife
  automaticamente — o mesmo tratamento D-03.
- **Files modified:** scripts/montar_cesta_holdout.py (documentado no docstring do loop)

Fora isso, o plano foi executado exatamente como escrito.

## Known Stubs

Nenhum. Fase de validação/substrato: nenhum dado mockado ou placeholder. O `holdout_v24.yaml` nasce
deliberadamente sem `v_modelo` — isso NÃO é stub, é a **disciplina D-09** (Commit 1 datado antes do
Commit 2). O `v_modelo` é preenchido no Plano 04, e `test_nenhum_ticker_e_load_bearing` acorda ali
automaticamente.

## Threat Flags

Nenhum. A superfície é leitura de YAML congelado (`safe_load`) e geração determinística offline —
sem endpoint de rede, sem auth, sem entrada de usuário. As mitigações do threat register da fase
(T-14-08 roteamento real via eh_concessionaria; T-14-09 regra escrita ANTES + snapshot-hash;
T-14-10 difíceis por atributo + CRESCIMENTO marcado; T-14-04b fixture sem excecao_nota) estão TODAS
implementadas e cobertas pelo teste de composição.

## Self-Check: PASSED
- `scripts/montar_cesta_holdout.py` — FOUND
- `tests/fixtures/holdout_v24.yaml` — FOUND (38 entradas, 0 v_modelo, 0 excecao_nota)
- `tests/test_holdout_cesta.py` — FOUND
- Commit `a9db387` (montador) — FOUND
- Commit `a5899b0` (Commit 1 do D-09) — FOUND
