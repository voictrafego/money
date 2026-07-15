---
phase: 09-ingest-o-correta-data
plan: 01
subsystem: database
tags: [cvm, ingest, jcp, controlador, minoritarios, dividendos, sanidade]

# Dependency graph
requires:
  - phase: 08-sanidade-dos-dados-san
    provides: "insumos limpos já lidos (proventos_filtro_amplo, lucro_controlador, pl_nao_controladores) e os detectores SAN-03/SAN-04 que provam o conserto"
provides:
  - "c.dividendos capturando o JCP (filtro amplo dentro da CVM)"
  - "c.lucro_liquido e c.patrimonio_liquido na base do controlador com fallback ao consolidado"
  - "gate único controlador→(lucro+PL) que nunca cruza bases (evita a doença do SAN-04)"
affects: [10-prim, 09-05, valuation, sanidade]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Promoção de insumo-diagnóstico a fonte-de-verdade (a Fase 8 leu; a Fase 9 aponta)"
    - "Gate único acoplando lucro e PL na MESMA base (controlador xor consolidado)"
    - "Teste de disease re-apontado ao insumo cru quando o conserto move a fonte (preserva a verdade permanente sem afrouxar)"

key-files:
  created: []
  modified:
    - src/analista/ingest/cvm.py
    - src/analista/ingest/build.py
    - tests/test_sanidade_insumos.py

key-decisions:
  - "DATA-01: dividendos_distribuidos passa a sair de _distribuicoes_proventos_amplo (dividendo OU JCP) — ampliar o filtro DENTRO da CVM, sem trocar de fonte para o Yahoo."
  - "DATA-02: gate ÚNICO em lucro_controlador acopla lucro E PL; sem controlador, ambos ficam no consolidado (fallback) e minoritários NÃO são subtraídos — nunca base cruzada."
  - "Option A (aprovada pelo usuário): dois testes-diagnóstico da Fase 8 re-apontados aos insumos CRUS (filtros e consolidado direto na fonte), preservando o diagnóstico permanente; nenhum assert afrouxado, classificacao.yaml intacto."

patterns-established:
  - "Quando um conserto de dado move a FONTE de um campo, o teste que media a doença via esse campo é re-apontado ao insumo cru (verdade permanente), não deletado nem afrouxado."

requirements-completed: [DATA-01, DATA-02]

# Metrics
duration: 40min
completed: 2026-07-15
---

# Phase 09 Plan 01: Ingestão correta (DATA-01 + DATA-02) Summary

**c.dividendos passa a capturar o JCP (filtro amplo interno à CVM) e c.lucro_liquido/c.patrimonio_liquido migram para a base do controlador com fallback — sem tocar em motor, knob ou config; suíte v2.4 verde (0 failed).**

## Performance

- **Duration:** ~40 min (inclui um checkpoint de decisão + retomada)
- **Started:** 2026-07-15
- **Completed:** 2026-07-15
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- **DATA-01:** `cvm.fundamentos_do_ano` aponta `dividendos_distribuidos` para `_distribuicoes_proventos_amplo` — `c.dividendos` agora casa "dividendo OU juros sobre capital". Medido no cache CVM: BRSR6 `amplo/estreito = 5,43×` (JCP recuperado); os 4 grandes bancos (ITUB4/BBDC4/BBAS3) `amplo == estreito` (ratio 1,0) — **sem contagem de JCP em dobro** (T-09-01 mitigado por medição).
- **DATA-02:** `montar_empresa` decide lucro e PL por um **gate único** em `lucro_controlador`: com controlador → `LL = controlador` e `PL = consolidado − minoritários` (juntos); sem controlador → ambos no consolidado (fallback), minoritários **não** subtraídos mesmo com `pl_nao_controladores` presente (Pitfall 3 evitado — nunca base cruzada).
- Os campos-diagnóstico (`c.lucro_controlador`, `c.pl_nao_controladores`, `c.proventos_filtro_amplo`) seguem intactos; os detectores SAN-03/SAN-04 continuam existindo.
- Suíte completa verde: **459 passed, 1 skipped, 38 deselected, 2 xfailed, 0 failed**. Zero mudança em `config.yaml`/`calibracao.lock.yaml` (orçamento de 3 knobs intocado).

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: DATA-01 — filtro amplo (JCP capturado)** — `019c501` (feat)
2. **Task 2: DATA-02 — base do controlador (lucro+PL, gate único + fallback)** — `f3b8387` (feat)

_Ambas as tasks são `tdd="true"`; aqui a prova de regressão são os asserts existentes (Fase 8) re-apontados + os novos invariantes de conserto, no mesmo commit da task._

## Files Created/Modified
- `src/analista/ingest/cvm.py` — `dividendos_distribuidos` → filtro amplo; docstring do módulo atualizada (DATA-01, não mais "conserto é da Fase 9").
- `src/analista/ingest/build.py` — gate único controlador→(lucro+PL) com fallback e `.get()` nas leituras de `f`.
- `tests/test_sanidade_insumos.py` — dois asserts-diagnóstico re-apontados aos insumos crus + helper `_dfc_real` e imports `cvm`/`universe`.

## Decisions Made
- **Ampliar o filtro DENTRO da CVM (não trocar para o Yahoo)** — a direção do BUG-JCP é a CVM que perde, medida na Fase 8; a gêmea ampla já existia e já era testada.
- **Acoplar lucro↔PL sob um único gate** — mover só um dos dois recriaria a base cruzada que o SAN-04 detecta.
- **`.get()` nas leituras de `f`** — o stub de `test_cvm_distribuicoes` devolve um dict sem as chaves de diagnóstico; acesso por colchete quebrava `test_build_cai_para_yahoo_quando_cvm_sem_provento`.

## Deviations from Plan

### Checkpoint de decisão (resolvido pelo usuário — Option A)

**1. [Rule 4 — Architectural / test discipline] Dois testes-diagnóstico da Fase 8 invalidados pelo conserto**
- **Found during:** Task 1 e Task 2 (medido antes de commitar)
- **Issue:** `test_o_filtro_estreito_da_cvm_perde_o_jcp` e `test_montar_empresa_carimba_o_lucro_do_controlador` (ambos `contrato`, plano 08-01) rodam o pipeline LIVE e asseriam a relação SUJA através de `c.dividendos`/`c.lucro_liquido`. DATA-01/02 curam a doença → `c.dividendos == proventos_filtro_amplo` (medido `655978000.0 > 655978000.0` falha) e `c.lucro_liquido == c.lucro_controlador` (medido `44857000000.0 != 44857000000.0` falha). O plano restringia o diff a `cvm.py`/`build.py` e o CLAUDE.md proíbe afrouxar/deletar assert para ficar verde — conflito real que o plano não previu.
- **Fix (Option A, autorizada pelo usuário):** os dois asserts foram **re-apontados aos insumos CRUS** — `_distribuicoes_proventos` vs `_distribuicoes_proventos_amplo` direto no DFC real (o filtro estreito segue perdendo o JCP: verdade permanente; ITUB4 escapa por acidente: estreito == amplo) e `c.lucro_controlador` vs o consolidado bruto de `cvm.fundamentos_do_ano(...)["lucro_liquido"]` (ainda difere no ITUB4). Adicionados os **novos invariantes do conserto** (`c.dividendos == c.proventos_filtro_amplo`, `c.lucro_liquido == c.lucro_controlador`). Nenhum número não-trivial em função `test_` (BLIND-04a preservado); `classificacao.yaml` intocado (nomes mantidos).
- **Files modified:** `tests/test_sanidade_insumos.py` (diff-scope expandido e autorizado)
- **Verification:** suíte completa `0 failed`; `git diff` restrito aos 3 arquivos autorizados.
- **Committed in:** `019c501` (assert do JCP) e `f3b8387` (assert do controlador)

---

**Total deviations:** 1 checkpoint de decisão (Rule 4), resolvido pelo usuário (Option A) + 1 auto-fix `.get()` embutido (Rule 3, robustez de stub).
**Impact on plan:** conserto entregue exatamente como especificado; a única expansão foi tornar dois testes-diagnóstico honestos após a fonte mudar, sem afrouxar nada.

## Issues Encountered
- Um terceiro teste (`test_build_cai_para_yahoo_quando_cvm_sem_provento`) quebrou transitoriamente por acesso `f["lucro_controlador"]` contra o stub sem a chave; resolvido com `.get()` (o stub cai corretamente no ramo de fallback). Isolado por medição antes do commit.

## Known Stubs
Nenhum. Todos os campos consertados fluem de fontes reais (cache CVM).

## Threat Flags
Nenhuma nova superfície. T-09-01 (contagem de JCP em dobro) e T-09-02 (linha do controlador ausente) mitigados por medição + fallback explícito, conforme o `<threat_model>` do plano.

## Next Phase Readiness
- A prova formal ticker-a-ticker (pares SAN-03/SAN-04 sumindo da monotonicidade) é do **plano 09-05** (snapshot limpo desacoplado). Aqui o gate foi a suíte verde + nenhum motor/knob tocado — cumprido.
- DATA-03 (num_acoes), DATA-04 (duplo split, spike), DATA-05 (base do DY) e DATA-06 (snapshot limpo) seguem nos planos 09-02..09-05.
- **CSNA3** muda de sinal no lucro (controlador em prejuízo) — é o conserto funcionando, não regressão; será visível quando o snapshot limpo for regenerado (09-05).

## Self-Check: PASSED

- `019c501` (DATA-01) — FOUND
- `f3b8387` (DATA-02) — FOUND
- `.planning/phases/09-ingest-o-correta-data/09-01-SUMMARY.md` — FOUND

---
*Phase: 09-ingest-o-correta-data*
*Completed: 2026-07-15*
