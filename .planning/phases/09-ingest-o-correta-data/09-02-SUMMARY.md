---
phase: 09-ingest-o-correta-data
plan: 02
subsystem: database
tags: [cvm, ingest, num_acoes, composicao_capital, escala, unit, sanidade]

# Dependency graph
requires:
  - phase: 08-sanidade-dos-dados-san
    provides: "impliedSharesOutstanding (ON+PN) e splits já lidos; detectores SAN-01/SAN-02 que provam o conserto"
  - phase: 09-ingest-o-correta-data
    plan: 01
    provides: "c.dividendos com JCP e a base do controlador (DATA-01/02) — não revertidos"
provides:
  - "c.num_acoes vindo da contagem OFICIAL da CVM (composicao_capital), por ano, com escala detectada"
  - "fallback de num_acoes = impliedSharesOutstanding (ON+PN), nunca sharesOutstanding"
  - "_fator_unit refeito sobre a contagem oficial (ALUP11 = 3, não 5)"
  - "cvm.contagem_oficial_do_ano — leitura nova, join CNPJ→CD_CVM"
affects: [10-prim, 09-05, valuation, sanidade]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fonte de verdade oficial por ano (composicao_capital) substitui derivação cruzada (LL/LPA)"
    - "Escala detectada por âncora (implied ON+PN) e arredondada à potência de 1000 — nunca contagem crua"
    - "Fator de unit derivado da contagem ON+PN correta (aposenta o _fator_unit corrompido)"

key-files:
  created: []
  modified:
    - src/analista/ingest/cvm.py
    - src/analista/ingest/build.py
    - tests/test_cvm_distribuicoes.py
    - tests/classificacao.yaml
  deleted:
    - tests/test_ingest_unit.py

key-decisions:
  - "DATA-03: num_acoes deixa de ser LL/LPA e passa a ser a contagem oficial da CVM (composicao_capital), escalada e ancorada no impliedSharesOutstanding."
  - "Escala (milhares×unidades) detectada cruzando a contagem oficial do último ano com o implied (ON+PN), arredondada à potência de 1000 (1 ou 1000) e aplicada à série inteira — nunca a contagem crua (Pitfall 4)."
  - "Fallback quando falta contagem oficial num ano = impliedSharesOutstanding (ON+PN), NUNCA sharesOutstanding (armadilha 1)."
  - "Option B (aprovada pelo usuário): diff-scope de teste expandido — dois stubs invariante/golden de test_cvm_distribuicoes completados com implied (valores asseridos intactos); test_ingest_unit.py DELETADO (4 goldens do método LL/LPA removido) + entradas em classificacao.yaml removidas no mesmo commit."

patterns-established:
  - "Quando o conserto move a FONTE de num_acoes, o golden/invariante que dependia da fonte antiga (LL/LPA) tem o stub completado com a nova fonte (implied) — sem alterar o valor asserido — ou, se ele encoda o método removido, é DELETADO (não atualizado) na fase que corrige o método."

requirements-completed: [DATA-03]

# Metrics
duration: 55min
completed: 2026-07-15
---

# Phase 09 Plan 02: Ingestão correta (DATA-03) Summary

**`c.num_acoes` passa a vir da contagem OFICIAL da CVM (`composicao_capital`) por ano — com escala milhares×unidades detectada contra o `impliedSharesOutstanding` e o fallback ancorado no ON+PN — aposentando a derivação `LL/LPA` que era a causa-raiz da dispersão em 41/104 tickers; suíte v2.4 verde (0 failed), zero motor/knob/config tocado.**

## Performance

- **Duration:** ~55 min (inclui um checkpoint de decisão + retomada — Option B)
- **Started:** 2026-07-15
- **Completed:** 2026-07-15
- **Tasks:** 2
- **Files:** 4 modificados + 1 deletado

## Accomplishments

- **Task 1 (cvm.py):** `contagem_oficial_do_ano(cd_cvm, ano)` lê `dfp_cia_aberta_composicao_capital_{ano}.csv` de dentro do ZIP já baixado e devolve `QT_ACAO_TOTAL_CAP_INTEGR − QT_ACAO_TOTAL_TESOURO` (ON+PN em circulação), CRUA (sem escala). O join CNPJ→CD_CVM sai de `cad_cia_aberta.csv` (armadilha 2 — o composicao é chaveado por CNPJ_CIA, não CD_CVM), cacheado com `lru_cache`. Never-raise: CNPJ ausente / arquivo faltando (o composicao só existe a partir de ~2020) / linha inexistente → `None`. Quando o mesmo CNPJ traz mais de um `DT_REFER`/`VERSAO` (período de transição), fica com o mais recente e a maior versão.
- **Task 2 (build.py):** `num_acoes[ano]` passa a vir de `cvm.contagem_oficial_do_ano`. A **escala** (armadilha 3 / Pitfall 4) é detectada por `_fator_escala_oficial`, que cruza a contagem oficial do último ano com o `impliedSharesOutstanding` e arredonda `implied/oficial` à potência de 1000 mais próxima (na prática 1 ou 1000), aplicando à série inteira — nunca a contagem crua. O **fallback** (armadilha 1) usa `impliedSharesOutstanding` (ON+PN), nunca `sharesOutstanding`. O `_fator_unit` foi **refeito** para consumir a contagem oficial ON+PN (ALUP11 = 3, não o 5 espúrio da contagem inflada por minoritários — Pitfall 5). `c.lpa_cvm` preservado como diagnóstico.
- **Medição manual (do `<verification>` do plano) — TODA verde:** ITUB4 2019 = **1,10e10** (bilhões, não milhões); GOAU4 `num_acoes×preço/market_cap = 1,0015` (era 2,969×); CGRA4 `0,925` (era 0,001×); BRSR6 `1,0000` (escala milhares detectada); ALUP11 na base de units (329,6M, fator 3). ITUB4 2019 é `yahoo_fallback` (implied) e 2020–2025 é `cvm` — origens diferentes na fronteira → SAN-02 isenta o par → **sem salto artificial ÷1000**.
- Suíte v2.4 verde: **default 459 passed, 1 skipped, 2 xfailed, 34 deselected, 0 failed**; `-m ""` **492 passed, 0 failed**; `-m golden_nivel` **34 passed, 0 failed, 0 CLASSIFICACAO ORFA**. **Zero mudança em `config.yaml`/`calibracao.lock.yaml`** (orçamento de 3 knobs intocado).

## Task Commits

1. **Task 1: cvm — contagem oficial (composicao_capital)** — `239fba4` (feat)
2. **Task 2: build — num_acoes da contagem oficial (aposenta LL/LPA) + edições de teste autorizadas** — `19abd42` (feat)

_Ambas `tdd="true"`; como no 09-01, a prova de regressão são os invariantes/contratos existentes + a medição manual dos alvos SAN-01/SAN-02 (a prova formal ticker-a-ticker via monotonicidade fica no plano 09-05, sobre snapshot limpo)._

## Files Created/Modified

- `src/analista/ingest/cvm.py` — `_mapa_cnpj_por_cd_cvm`, `_composicao_capital`, `contagem_oficial_do_ano`; docstring do módulo atualizada (DATA-03).
- `src/analista/ingest/build.py` — fonte de `num_acoes` trocada de LL/LPA para a contagem oficial; `_fator_escala_oficial` (novo) + `_fator_unit` refeito; fallback = implied; `import math`.
- `tests/test_cvm_distribuicoes.py` — dois stubs (`test_build_cai_para_yahoo_quando_cvm_sem_provento`, `invariante`; e `test_build_prefere_distribuicao_cvm_sobre_yahoo`, `golden_nivel`) completados com `dm.implied_shares_outstanding` (a nova fonte de fallback); `f["lpa"]` vestigial removido dos stubs. Valores asseridos **intactos**.
- `tests/test_ingest_unit.py` — **DELETADO** (4 goldens que asseriam `num_acoes == LL/LPA`, o método que o DATA-03 remove).
- `tests/classificacao.yaml` — 4 entradas do `test_ingest_unit.py` removidas (sem entrada órfã nem teste órfão).

## Decisions Made

- **A fonte oficial substitui a derivação, não a "corrige".** `LL/LPA` com bases cruzadas era a doença; `composicao_capital` (ON+PN, por ano) é a fonte oficial já no disco.
- **Escala jamais aplicada às cegas na leitura** — decidida no build, onde o `implied` (âncora ON+PN) está disponível; arredondamento à potência de 1000 tolera o ruído do implied de units.
- **Fallback é o `implied`, não o `sharesOutstanding`** — o `sharesOutstanding` é só a classe negociada e daria falso ~2× em toda empresa com PN (armadilha 1).

## Deviations from Plan

### Checkpoint de decisão (resolvido pelo usuário — Option B)

**1. [Rule 4 — Architectural / test discipline] Um teste `invariante` e um `golden` invalidados pela remoção da fonte LL/LPA**
- **Found during:** Task 2 (medido antes de commitar; suíte rodada).
- **Issue:** `test_build_cai_para_yahoo_quando_cvm_sem_provento` (`invariante`, no suíte verde) e `test_build_prefere_distribuicao_cvm_sobre_yahoo` (`golden_nivel`) — ambos em `test_cvm_distribuicoes.py` — populavam `num_acoes` via `LL/LPA` (setavam `dm.num_acoes` + `f["lpa"]`, mas **não** `dm.implied_shares_outstanding`). Com a fonte trocada, `num_acoes` ficava vazio → `KeyError`/`payout None`. O plano restringia o diff a `cvm.py`/`build.py` e proíbe usar `dm.num_acoes` como fallback (armadilha 1) — não havia conserto in-scope. Além disso, os 4 goldens de `test_ingest_unit.py` asseriam `num_acoes == LL/LPA` (o método removido) e quebravam sob `-m golden_nivel`.
- **Fix (Option B, autorizada pelo usuário):** diff-scope expandido para `tests/test_cvm_distribuicoes.py`, `tests/test_ingest_unit.py` e `tests/classificacao.yaml`. (a) Os dois stubs de `test_cvm_distribuicoes` completados com `dm.implied_shares_outstanding` (a nova fonte correta de fallback), **sem alterar nenhum valor asserido** (dividendos = `0,50 × 1e9`; payout = `14824/29172`). (b) `test_ingest_unit.py` DELETADO integralmente (4 goldens do método LL/LPA) + suas 4 entradas em `classificacao.yaml` removidas no MESMO commit — completude da coleta preservada (0 entrada órfã, 0 teste órfão).
- **Files:** `tests/test_cvm_distribuicoes.py`, `tests/test_ingest_unit.py` (del), `tests/classificacao.yaml`.
- **Verification:** default `0 failed`, 1 skipped, 2 xfailed; `-m golden_nivel` `0 failed` sem CLASSIFICACAO ORFA; `git diff` restrito aos arquivos autorizados; `config.yaml`/`calibracao.lock.yaml` VAZIOS.
- **Committed in:** `19abd42` (junto de build.py).

---

**Total deviations:** 1 checkpoint de decisão (Rule 4), resolvido pelo usuário (Option B).
**Impact on plan:** conserto entregue exatamente como especificado; a única expansão foi tornar dois stubs honestos com a nova fonte (sem afrouxar) e deletar os goldens do método removido (não atualizar).

## Issues Encountered

- Nenhum além do checkpoint. A dependência do composicao_capital só existir a partir de ~2020 é tratada pelo fallback ao `implied` para anos antigos, com a fronteira de origem (cvm↔yahoo_fallback) isentando o par no SAN-02.

## Known Stubs

Nenhum. `num_acoes` flui de fonte real (cache CVM) ou do `implied` (Yahoo) no fallback.

## Threat Flags

Nenhuma nova superfície. T-09-04 (escala) mitigado por `_fator_escala_oficial`; T-09-05 (chave errada) por join explícito via `cad_cia_aberta.csv` + never-raise; T-09-06 (âncora ausente) por degradação a fator 1 sem abortar.

## Next Phase Readiness

- A prova formal ticker-a-ticker (pares `("GOAU4"/"CGRA4","SAN-01")` e `("ITUB4"/"BRSR6","SAN-02")` sumindo da monotonicidade) é do **plano 09-05** (snapshot limpo desacoplado). Aqui o gate foi a suíte verde + a medição manual dos alvos — cumprido.
- DATA-04 (duplo split — spike de localização) e DATA-05 (base do DY — declarar bruto) seguem nos planos 09-03/09-04.

## Self-Check: PASSED

- `src/analista/ingest/cvm.py` — FOUND
- `src/analista/ingest/build.py` — FOUND
- `tests/test_ingest_unit.py` — DELETED (ok)
- `239fba4` (Task 1) — FOUND
- `19abd42` (Task 2) — FOUND
- classificacao.yaml orphan entries para `test_ingest_unit` — 0 (ok)

---
*Phase: 09-ingest-o-correta-data*
*Completed: 2026-07-15*
