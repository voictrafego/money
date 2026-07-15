---
phase: 09-ingest-o-correta-data
plan: 05
subsystem: testing
tags: [data-06, sanidade, snapshot, monotonicidade, ratchet, escala, composicao_capital, accept-list]

# Dependency graph
requires:
  - phase: 09-ingest-o-correta-data
    plan: 01
    provides: "c.dividendos com JCP + base do controlador (DATA-01/02) — surfaced no snapshot limpo"
  - phase: 09-ingest-o-correta-data
    plan: 02
    provides: "num_acoes da contagem oficial da CVM (DATA-03) — cuja escala por-ano este plano completou"
  - phase: 08-sanidade-dos-dados-san
    provides: "snapshot sujo + baseline (régua) + detectores SAN-01..05 + monotonicidade tautológica"
provides:
  - "snapshot LIMPO desacoplado (medição de 'hoje' sobre o código consertado) — a régua enxerga o progresso"
  - "_escala_por_ano: escala do composicao_capital detectada POR ANO (corrige ÷1000 residual do DATA-03)"
  - "_alinhar_escala_interna: escala interna à série p/ tickers sem âncora (implied None)"
  - "ratchet honesto do DATA-06: pares_hoje ⊆ (baseline ∪ pares_aceitos); buckets_hoje ⊆ baseline (+aceitos)"
  - "accept-list VERSIONADA (9 pares + 2 buckets) com justificativa por categoria (BLIND-04a-safe)"
affects: [10-prim, valuation, sanidade]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Régua (baseline sujo), objeto medido (snapshot limpo) e evidência (snapshot sujo) são 3 arquivos distintos"
    - "Escala do composicao_capital é detectada POR ANO (MILHARES↔UNIDADES trocam entre anos do mesmo ticker)"
    - "Sem âncora externa, a unidade de cada ano é inferida da própria série (banda mais frequente)"
    - "Ratchet anti-overfit: par/bucket novo só entra via accept-list versionada e justificada; provado RED-able"

key-files:
  created:
    - scripts/capturar_snapshot_limpo.py
    - tests/fixtures/snapshot_sanidade_limpo_2026-07-15.yaml
    - tests/fixtures/pares_aceitos_sanidade.yaml
  modified:
    - src/analista/ingest/build.py
    - tests/helpers_sanidade.py
    - tests/test_sanidade_baseline.py
    - tests/classificacao.yaml
  deleted: []

key-decisions:
  - "DATA-06: preservar sujo+baseline, gerar snapshot LIMPO novo, apontar SÓ _pares_e_buckets_de_hoje ao limpo (loader desacoplado) — a monotonicidade deixa de ser tautologia e ENCOLHE."
  - "Escopo expandido e autorizado p/ build.py: a régua expôs que o DATA-03 (09-02) aplicava um fator de escala único de série, deixando ÷1000 preso nos anos de escala divergente. Corrigido para detecção POR ANO."
  - "Escala interna à série (sem âncora) p/ ELET3/ELET6/IGTI11 (implied None): infere a unidade de cada ano da própria série; corrige só desvios potência-de-1000, preserva variação real."
  - "Ratchet reformulado (aprovado pelo usuário): subconjunto puro vira 'targets removidos + nenhum curado ressuscita + pares_hoje ⊆ (baseline ∪ aceitos)'; bucket vira ⊆ + buckets_aceitos."
  - "snapshot_bancos NÃO regenerado (decisão travada: Fase 10, onde o golden ITUB4 32,88 é formalmente deletado)."

patterns-established:
  - "Quando a cura MUDA a fonte de dados, o invariante de regressão não pode exigir subconjunto puro — reformula-se para um ratchet com accept-list versionada, que segue pegando regressão silenciosa (provado por injeção RED-able) sem fingir que a cura não mexe em nada."

requirements-completed: [DATA-06]

# Metrics
duration: 256min
completed: 2026-07-15
---

# Phase 09 Plan 05: Ingestão correta (DATA-06) Summary

**A régua enxerga o progresso: o snapshot LIMPO (produto do código consertado) desacopla a medição de "hoje" da régua (baseline sujo) e da evidência (snapshot sujo), a monotonicidade da Fase 8 deixa de ser tautologia e ENCOLHE (os 9 alvos DATA-01/02/03 somem, ticker a ticker); a régua ainda expôs um ÷1000 residual do DATA-03 (escala do composicao_capital aplicada por série, não por ano) — corrigido com detecção por-ano + escala interna à série para tickers sem âncora; e o invariante virou um ratchet honesto (accept-list versionada, provado RED-able) em vez de um subconjunto puro que a cura tornou impossível.**

## Performance

- **Duration:** ~256 min de wall-clock (inclui 3 rodadas de checkpoint com o usuário: o descobrimento dos ressuscitados, a autorização do fix de escala, e a aprovação do ratchet + bucket-accept)
- **Started / Completed:** 2026-07-15
- **Tasks:** 2 (Task 1 captura; Task 2 desacople + ratchet) + 2 fixes de escala autorizados como expansão de escopo
- **Files:** 3 criados + 4 modificados

## Accomplishments

- **Task 1 — snapshot LIMPO (`scripts/capturar_snapshot_limpo.py` + fixture):** reusa a forma provada do `capturar_snapshot_sujo.py` (universo `ticker_map.json`, never-raise SAN-06, mesmas SERIES_NUM, zero R$ derivado, congela market_cap+splits+origem) com `DATA_BASE=2026-07-15` e destino próprio. Live: 104 capturados, 11 tickers 404 degradam ao bloco `falhas:` com a CVM intacta. **ITUB4 2019 = 11,02 bi de ações** (bilhões, não milhões) — a cura visível.
- **Fix de escala #1 — por-ano (`_escala_por_ano`, build.py):** a régua expôs que o DATA-03 (09-02) inferia UM fator de escala do último ano e o aplicava à série inteira; mas o `composicao_capital` troca de MILHARES para UNIDADES **entre anos** do mesmo ticker, deixando o ×1000 preso nos anos de escala divergente (PETR4 2020, BBDC4 2020-23, VIVT3/RENT3/PETR3/BBDC3/ASAI3/UNIP6). Agora cada ano é ancorado no `impliedSharesOutstanding` pela potência de 1000 mais próxima. **8 pares SAN-02 espúrios somem**; variação societária real (<1000×) preservada (VIVT3 2025, RENT3 fusão, AGRO3 2020).
- **Fix de escala #2 — interna à série (`_alinhar_escala_interna`, build.py):** para tickers sem âncora (`implied=None`: ELET3/ELET6/IGTI11, 404 no Yahoo), a unidade de cada ano é inferida da PRÓPRIA série (banda `round(log10(n)/3)`, referência = a mais frequente; empate → ano mais recente). Corrige só desvios potência-de-1000. **ELET3/ELET6·SAN-02 somem**; o resíduo real não-potência-de-1000 do IGTI11 (reorganização de 2021, ~12,8× além do ×1000) sobrevive — de propósito.
- **Task 2 — loader desacoplado + monotonicidade encolhendo:** `helpers_sanidade.CAMINHO_SNAPSHOT_LIMPO` separa "hoje" (limpo) da régua e dos detectores (que seguem no sujo). `_pares_e_buckets_de_hoje` passa a ler o limpo → **os 9 alvos DATA-01/02/03 somem de `pares_hoje`** (`test_os_alvos_consertados_sumiram_de_hoje`, contrato novo). `test_sanidade_checks` (detectores) segue verde no sujo.
- **Ratchet honesto (reformulação aprovada):** o subconjunto puro `pares_hoje ⊆ pares_baseline` era impossível para uma cura que TROCA a fonte de dados. Reformulado para `pares_hoje ⊆ (pares_baseline ∪ pares_aceitos)`; o bucket de igualdade estrita para `buckets_hoje ⊆ buckets_baseline` (+ `buckets_aceitos`). A `pares_aceitos_sanidade.yaml` (versionada) documenta 9 pares + 2 buckets, cada um com justificativa por CATEGORIA (sem ticker+número — BLIND-04a-safe).
- **Suíte v2.4 verde:** default **467 passed, 1 skipped, 34 deselected, 2 xfailed, 0 failed**; `-m ""` **500 passed, 2 skipped, 2 xfailed, 0 failed**; `-m golden_nivel` **34 passed, 0 CLASSIFICACAO ORFA**. Sujo/baseline intactos (`git diff --quiet` OK). `config.yaml`/`calibracao.lock.yaml` INTOCADOS (3 knobs).

## O set final de ressuscitados — todos ACEITOS por medição

Depois dos dois fixes de escala, restaram 9 pares novos em `pares_hoje` (não no baseline sujo), todos legítimos e documentados na accept-list:

| Par | Categoria | Justificativa (medida) |
|-----|-----------|------------------------|
| IGTI11·SAN-02 | salto societário real | 2020→2021 = 1000 (unidade) × ~12,8 (reorganização 2021); sem split no Yahoo p/ isentar |
| CMIN3·SAN-01/03/05 | dado-fonte CVM anômalo | `composicao_capital` 2025 = 54,3 bi vs 2024 = 5,48 bi (mesmo tesouro) — erro 10× no arquivo, não potência-de-1000; SAN corretamente pega |
| GOAU4·SAN-03, EQTL3·SAN-03, GRND3·SAN-03 | cascata legítima DATA-01 | sinal (a) = 1,0 (JCP capturado); a divergência é a reconciliação CVM↔Yahoo (sinal b), que o check reporta sem eleger verdade |
| EQTL3·SAN-05, AGRO3·SAN-05 | consequência DATA-02 | resíduo de superávit-limpo do PL na base do controlador + evento real de capital |

Buckets genuinamente novos (par persistente, bucket deslocado pela cura): **TIMS3·SAN-03** (reconciliação deslocada pelo JCP) e **BRKM5·SAN-05** (resíduo deslocado pelo PL do controlador). CSAN3·SAN-02 encolheu o conjunto de buckets (ocorrência curada) → passa livre sob `⊆`, sem entrada.

## As duas provas de execução (o ratchet é load-bearing)

Regra do projeto: guarda só vale se provada por execução. Injetei temporariamente em `_pares_e_buckets_de_hoje`, rodei os testes, confirmei RED, e reverti:

- **Prova (a) — subset ratchet:** injetado `("__FAKE__", "SAN-99")` (par sujo NÃO-documentado) → `test_baseline_de_sujos_so_encolhe` ficou **RED** ("Pares NOVOS e NÃO DOCUMENTADOS apareceram"). Revertido → verde.
- **Prova (b) — bucket ratchet:** injetado bucket `~1e9` novo no par persistente `("CSAN3","SAN-02")` (NÃO-documentado) → `test_bucket_nao_muda_sem_a_flag_sumir` ficou **RED** ("Um bucket NOVO apareceu num par persistente sem estar documentado"). Revertido → verde.

Isto prova que a accept-list NÃO é regeneração silenciosa do baseline: um par/bucket novo não-justificado quebra a suíte.

## Files Created/Modified

- `scripts/capturar_snapshot_limpo.py` (novo) — captura live do snapshot limpo, forma do sujo, destino próprio.
- `tests/fixtures/snapshot_sanidade_limpo_2026-07-15.yaml` (novo) — dado LIMPO congelado, medido de "hoje", regenerável.
- `tests/fixtures/pares_aceitos_sanidade.yaml` (novo) — accept-list versionada (9 pares + 2 buckets), justificativas categóricas.
- `src/analista/ingest/build.py` — `_fator_escala_oficial` → `_escala_por_ano` (por-ano) + `_alinhar_escala_interna` (sem âncora).
- `tests/helpers_sanidade.py` — `CAMINHO_SNAPSHOT_LIMPO` desacoplado.
- `tests/test_sanidade_baseline.py` — `_pares_e_buckets_de_hoje` no limpo; ratchets reformulados; 2 contratos novos (alvos somem; accept-list disjunta/sem-reais); loaders de accept-list.
- `tests/classificacao.yaml` — 2 entradas novas (`contrato`), sem órfãos.

## Deviations from Plan

### Expansão de escopo autorizada (Rule 4, resolvida pelo usuário — Option 1)

**1. [Rule 4 — bug real exposto pela régua] O DATA-03 aplicava escala de série única, deixando ÷1000 residual por-ano**
- **Found during:** Task 2 (a monotonicidade limpa mostrou 19 ressuscitados, não o zero que o plano assumia).
- **Issue:** `_fator_escala_oficial` inferia UM fator do último ano; o `composicao_capital` troca de unidade ENTRE anos → 19 pares novos (11 após o 1º fix). Conserto exigia `src/analista/ingest/build.py`, FORA do `files_modified` declarado (só arquivos de teste/script).
- **Fix (autorizado):** escopo expandido para build.py. Dois fixes: por-ano (implied-âncora) e interno à série (sem âncora). Commits atômicos `e2caf17` e `dc71e4f`.
- **Files:** `src/analista/ingest/build.py`.

**2. [Rule 4 — reformulação de invariante] O subconjunto puro do DATA-06 é impossível para uma cura que troca a fonte**
- **Found during:** Task 2 (após os fixes, restaram 9 ressuscitados legítimos + 2 buckets deslocados que quebravam os dois invariantes).
- **Issue:** `pares_hoje ⊆ pares_baseline` (e o bucket de igualdade estrita) exigiam "a cura introduz ZERO flag/magnitude nova" — impossível ao trocar LL/LPA→oficial e filtro estreito→amplo. CLAUDE.md proíbe afrouxar/regenerar/xfail.
- **Fix (aprovado pelo usuário):** reformulação para ratchet com accept-list versionada (targets removidos + nenhum curado ressuscita + `pares_hoje ⊆ baseline ∪ aceitos`; `buckets_hoje ⊆ baseline` + `buckets_aceitos`), provado RED-able por execução. Commit `ac297e1`.
- **Files:** `tests/test_sanidade_baseline.py`, `tests/fixtures/pares_aceitos_sanidade.yaml`, `tests/helpers_sanidade.py`, `tests/classificacao.yaml`.

**3. [Desvio de premissa] IGTI11·SAN-02 não era escala pura**
- Decisão #1 do usuário assumia ELET3/ELET6/IGTI11·SAN-02 como escala pura. Medição: IGTI11 2020→2021 = 1000 (unidade) × ~12,8 (reorganização real). O fix de escala remove o ×1000; o resíduo real sobrevive → aceito como 9º par de `pares_aceitos` (reportado e ratificado pelo usuário).

---

**Total deviations:** 2 expansões de escopo autorizadas (Rule 4) + 1 desvio de premissa, todos resolvidos por checkpoint com o usuário.

## Task Commits

1. `1720f62` (feat) — Task 1: captura + snapshot limpo inicial
2. `e2caf17` (fix) — escala por-ano (÷1000 residual do DATA-03)
3. `cfabe1f` (chore) — regenera snapshot com escala por-ano
4. `dc71e4f` (fix) — escala interna à série (ELET3/ELET6/IGTI11)
5. `a844875` (chore) — regenera snapshot com escala interna
6. `ac297e1` (feat) — Task 2: loader desacoplado + ratchet honesto + accept-list

## Known Stubs

Nenhum. O snapshot limpo flui do pipeline real (cache CVM + Yahoo); a accept-list é dado versionado justificado.

## Threat Flags

Nenhuma superfície nova. T-09-11 (régua corrompida) mitigado: sujo/baseline intactos, arquivo NOVO para o limpo. T-09-12 (Yahoo 404) mitigado: degradação never-raise. T-09-13 (tautologia) mitigado: loader desacoplado + `test_os_alvos_consertados_sumiram_de_hoje`.

## Next Phase Readiness

- **Fase 10 (PRIM):** o golden `ITUB4 32,88` é formalmente deletado lá; o `snapshot_bancos` é regenerado lá (decisão travada, não antecipada aqui).
- **Dívida de dados registrada:** (1) CMIN3 2025 = erro 10× no `composicao_capital` da CVM — hoje só detectado (aceito na accept-list); um guarda de outlier não-potência-de-1000 poderia corrigi-lo automaticamente no futuro. (2) ELET3/ELET6 sem market_cap alinham à escala de milhares (internamente consistente, mas absolutamente pequeno) — sem impacto de valuation (estão em `falhas:`), mas registrado.

## Self-Check: PASSED

- `scripts/capturar_snapshot_limpo.py` — FOUND
- `tests/fixtures/snapshot_sanidade_limpo_2026-07-15.yaml` — FOUND
- `tests/fixtures/pares_aceitos_sanidade.yaml` — FOUND
- `src/analista/ingest/build.py` (_escala_por_ano + _alinhar_escala_interna) — FOUND
- Commits `1720f62`, `e2caf17`, `cfabe1f`, `dc71e4f`, `a844875`, `ac297e1` — FOUND
- Suíte default 0 failed; `-m golden_nivel` 0 ORFA; sujo/baseline `git diff --quiet` OK

---
*Phase: 09-ingest-o-correta-data*
*Completed: 2026-07-15*
