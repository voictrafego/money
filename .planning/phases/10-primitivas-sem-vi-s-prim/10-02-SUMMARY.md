---
phase: 10-primitivas-sem-vi-s-prim
plan: 02
subsystem: valuation
tags: [roe-valuation, median-of-roes, winsor-removal, serie-crua, roe-signal-split, core-value, knob-budget]

# Dependency graph
requires:
  - phase: 10-primitivas-sem-vi-s-prim
    plan: 01
    provides: "base_normalizada = endpoint Theil-Sen (a base de lucro que roe_qualidade_atual consome); split de estimador estabelecido como padrão"
provides:
  - "roe_valuation = MEDIANA da série de roe(a) anuais (não mais base_lucro_normalizada ÷ PL do último ano) — mesma estatística que report._roe_through_cycle (roe0 e roe_terminal do RIM não divergem mais)"
  - "serie_lucro_normalizada = série CRUA de lucro (winsorização temporal removida; g robusto = Fase 11). norm.serie_winsorizada preservada para o screening (Cap. 8)"
  - "roe_qualidade_atual (NOVO helper só-roteamento): o ROE-endpoint pré-PRIM-02, consumido por arquetipo para não desrotear compounders de ROE crescente"
  - "Core Value: crescimento_lucro_3a do screening == g_historico do Analisar por construção (ambos consomem serie_lucro_normalizada crua)"
affects: [11-crescimento-grow, 12-custo-de-capital-ke, 10-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Signal split (espelha o estimator split do PRIM-01): uma primitiva (roe_valuation) consumida por dois clientes com estatísticas OPOSTAS — RIM/display quer a mediana through-cycle, roteamento quer a qualidade CORRENTE — é dividida em duas funções (roe_valuation + roe_qualidade_atual), não editada in-place"

key-files:
  created:
    - tests/test_fundamentals_valuation.py
  modified:
    - src/analista/core/fundamentals.py
    - src/analista/core/arquetipo.py
    - src/analista/core/screening.py
    - src/analista/report/report.py
    - tests/test_fundamentals_consistencia.py
    - tests/test_growth_robusto_multiticker.py
    - tests/test_consistencia_modos.py
    - tests/classificacao.yaml

key-decisions:
  - "Option A (checkpoint resolvido pelo usuário): dividir o sinal de ROE. roe_valuation vira a mediana through-cycle (PRIM-02); o roteamento de arquétipo passa a consumir roe_qualidade_atual (o endpoint pré-PRIM-02) para não desrotear um compounder de ROE crescente que a mediana subestima. Sem tocar knob/threshold (roe_alto_min intacto)."
  - "Preservar o Core Value quebrado como efeito colateral do PRIM-03: como g_historico virou cru, o crescimento_lucro_3a do screening foi repointado à MESMA serie_lucro_normalizada crua — a identidade crescimento_lucro_3a == g_historico volta a valer POR CONSTRUÇÃO (não por coincidência winsor)."
  - "2 golden_nivel de g (test_growth_reconciliacao) quebram como consequência do g_fund novo — NÃO atualizados (contrato v2.4); são tagged '→ Fase 11 (GROW)' na classificacao e ficam quarentenados."

patterns-established:
  - "Signal split do ROE (roe_valuation mediana × roe_qualidade_atual endpoint) — Option A, espelha o estimator split do 10-01"

requirements-completed: [PRIM-02, PRIM-03]

# Metrics
duration: 26min
completed: 2026-07-16
---

# Phase 10 Plan 02: roe_valuation por mediana-de-ROEs + série de lucro crua (PRIM-02/PRIM-03) Summary

**`roe_valuation` deixou de cruzar bases temporais e virou a MEDIANA da série de `roe(a)` anuais (a mesma estatística do `roe_terminal` do RIM), e `serie_lucro_normalizada` passou a devolver a série CRUA (winsorização temporal removida) — com um split de sinal (Option A) que dá ao roteamento de arquétipo um `roe_qualidade_atual` endpoint para não desrotear compounders, e a identidade Screening↔Analisar do `g` preservada por construção. Orçamento de 3 knobs intacto; nenhum golden de nível tocado.**

## Performance

- **Duration:** ~26 min (inclui 1 checkpoint de decisão do usuário)
- **Started:** 2026-07-16T11:29Z
- **Completed:** 2026-07-16T11:56Z
- **Tasks:** 2 (Task 1 RED; Task 2 GREEN + Option A + 3 deviations mecânicas)
- **Files:** 1 criado, 8 modificados

## Accomplishments
- **PRIM-02:** `roe_valuation` = `median([roe(a) for a in anos_ordenados() se roe(a) is not None])`, reusando a definição única `roe(ano)` (lucro_t ÷ PL médio(t-1,t)). Espelha `payout_valuation` e usa EXATAMENTE a estatística de `report._roe_through_cycle` — `roe0` e `roe_terminal` do RIM não divergem mais. A mediana descarta naturalmente um ano de prejuízo (não vira negativa).
- **PRIM-03:** `serie_lucro_normalizada` devolve `self.serie("lucro_liquido")` cru (o wrapper `norm.serie_winsorizada` saiu de `fundamentals`). A Fase 10 apenas REMOVE o viés da winsorização temporal; o desenho do `g` robusto é a Fase 11. `norm.serie_winsorizada` continua VIVA para o screening (screening.py, FCO/dividendos/tangível — Cap. 8 elegibilidade).
- **Signal split (Option A):** novo helper `roe_qualidade_atual` (o ROE-endpoint pré-PRIM-02, `base_lucro_normalizada ÷ PL médio`), consumido só pelo roteamento de `arquetipo.py`. Sem ele, a mediana through-cycle (que fica no MEIO da subida) desrotearia um compounder de ROE crescente de CRESCIMENTO (medido: uma série de roe(a) `[0,063 … 0,329]` tem mediana 0,113 < limiar 0,15). `roe_valuation` (mediana) segue servindo RIM/display.
- **Core Value preservado:** `crescimento_lucro_3a` do screening repointado à mesma `serie_lucro_normalizada()` crua → `crescimento_lucro_3a == g_historico` volta a valer POR CONSTRUÇÃO (era coincidência quando ambos eram a série winsorizada).
- Suíte default: **477 passed, 1 skipped, 34 deselected, 1 xfailed, 0 failed**. Orçamento de 3 knobs intacto (`git diff config.yaml calibracao.lock.yaml` VAZIO). Nenhum golden de nível atualizado/deletado.

## Task Commits

1. **Task 1: RED — testes de método de PRIM-02/PRIM-03** — `e6bdb5f` (test)
2. **Task 2: GREEN — roe_valuation mediana + serie crua + Option A split + 3 deviations** — `10b54fc` (feat)

**Plan metadata:** _(este commit)_ `docs(10-02)`

## Files Created/Modified
- `tests/test_fundamentals_valuation.py` (novo) — 5 testes de MÉTODO (roe_valuation == median(roe(a)); mesma estatística de _roe_through_cycle; ignora prejuízo pela mediana; fronteira None chamável sem args; serie_lucro_normalizada == série crua com winsor viva p/ screening).
- `src/analista/core/fundamentals.py` — `roe_valuation` → mediana de `roe(a)`; `serie_lucro_normalizada` → série crua; novo `roe_qualidade_atual` (endpoint, só-roteamento); `import median`.
- `src/analista/core/arquetipo.py` — refino quantitativo consome `roe_qualidade_atual` (qualidade corrente), não `roe_valuation` (mediana through-cycle).
- `src/analista/core/screening.py` — `crescimento_lucro_3a` → `serie_lucro_normalizada()` cru (identidade Core Value); FCO/dividendos/tangível seguem winsorizados (Cap. 8).
- `src/analista/report/report.py` — comentário do `g_historico` corrigido (série crua, PRIM-03).
- `tests/test_fundamentals_consistencia.py` — rewrite do invariante do endpoint p/ a mediana (+ `import median`).
- `tests/test_growth_robusto_multiticker.py` — rewrite do contrato do spike p/ a realidade da série crua (identidade Core Value preservada).
- `tests/test_consistencia_modos.py` — recalibração dos NÚMEROS das fixtures da coerência de direção (asserts intactos).
- `tests/classificacao.yaml` — 5 entradas novas + 1 renome, no mesmo diff (0 órfão).

## Decisions Made
- **Option A — signal split do ROE** (checkpoint resolvido pelo usuário): o `roe_valuation` vira mediana through-cycle (consistente com o RIM), mas o roteamento de arquétipo precisa da qualidade CORRENTE — então recebe `roe_qualidade_atual` (endpoint). Espelha exatamente o estimator split do PRIM-01 (uma primitiva, dois consumidores com estatísticas opostas → dividir, não editar in-place). `roe_alto_min` (config) NÃO tocado.

## Deviations from Plan

### Checkpoint (Rule 4 — decisão arquitetural do usuário)

**1. [Rule 4 — Arquitetura] Split de sinal de ROE + repoint do arquetipo (fora da lista literal de files_modified do plano)**
- **Found during:** Task 2 (suíte default vermelha em 2 testes `contrato` de roteamento de arquétipo não enumerados pelo plano/RESEARCH)
- **Issue:** `roe_valuation` é consumido também por `arquetipo.py:163` (roteamento). Virando a mediana through-cycle, um compounder de ROE crescente (WEGE3 real: roe(a) `[0,063…0,329]`, mediana 0,113) cai abaixo de `roe_alto_min=0,15` e deixa de rotear CRESCIMENTO — mudança de comportamento de MOTOR não escopada.
- **Fix:** Após checkpoint (Option A aprovado pelo usuário): novo helper `roe_qualidade_atual` (o ROE-endpoint pré-PRIM-02); `arquetipo.py` repointado para ele. Roteamento correto restaurado sem mexer em knob/threshold.
- **Files modified:** src/analista/core/fundamentals.py (+helper), src/analista/core/arquetipo.py
- **Committed in:** `10b54fc`

### Auto-fixed (Rule 1/3 — asserts intactos, nada afrouxado)

**2. [Rule 1 — Core Value] `crescimento_lucro_3a` do screening repointado à série crua**
- **Found during:** Task 2 (`test_consistencia_crescimento_lucro_3a_igual_g_historico` vermelho)
- **Issue:** PRIM-03 tornou `g_historico` cru, mas o screening ainda winsorizava o crescimento de LUCRO → a identidade Core Value `crescimento_lucro_3a == g_historico` (D-04, a ação não pode ranquear num g diferente do que o Analisar exibe) quebrou.
- **Fix:** o crescimento de LUCRO do screening passou a consumir `serie_lucro_normalizada()` (mesma fonte do `g_historico`); FCO/dividendos/tangível seguem winsorizados (elegibilidade Cap. 8, fora do escopo PRIM). Identidade preservada POR CONSTRUÇÃO.
- **Files modified:** src/analista/core/screening.py, src/analista/report/report.py (comentário)
- **Committed in:** `10b54fc`

**3. [Rule 1 — Testes que codificavam o método antigo] 3 testes reescritos/recalibrados**
- `test_roe_valuation_reflete_endpoint_nao_a_mediana_do_meio` (invariante) → renomeado `..._e_mediana_dos_roe_anuais_nao_o_endpoint`: reescrito para a invariância NOVA (`roe_valuation == median(roe(a))`, e `< roe_qualidade_atual` provando o split). Entrada de `classificacao.yaml` renomeada no mesmo diff.
- `test_perfil_vulc3_spike_extraordinario_nao_infla_g_nem_bsd` (contrato): removida a comparação incoerente (g cru × endpoint WINSORIZADO); mantidos os guards significativos (log-linear sobre TODOS os pontos < CAGR endpoint-a-endpoint da série CRUA; identidade Core Value). Nenhum guard real afrouxado.
- `test_veredito_direcao_coerente` (contrato, Core Value): recalibrados os NÚMEROS das fixtures dos comparáveis (ROE ~0,34 → ~0,23, bracketando a mediana da alvo) pela DOUTRINA ESCRITA do próprio teste ("recalibram-se os NÚMEROS, nunca se relaxa o assert"). As 2 asserts de direção intactas.
- **Committed in:** `10b54fc`

**Total deviations:** 3 (1 checkpoint arquitetural + 2 auto-fix de Core Value/testes-do-método-antigo). Nenhuma tolerância afrouxada, nenhum `xfail`→`skip`, nenhum assert de guarda removido, nenhum knob movido.

## Nota de correção do ROADMAP (OBRIGATÓRIA — RESEARCH §Pitfall 1)

Os anchors numéricos LITERAIS do `ROADMAP.md` §"Phase 10" foram medidos em dado SUJO pré-Fase-9 e **NÃO reproduzem no snapshot limpo** — os Criteria #3 e #4 são satisfeitos pela mudança de **MÉTODO** (asserção estrutural provada pelos testes), NÃO pelos números literais:
- **Criterion #3** — "roe_valuation ITUB4 16,1 → 18,0": o valor NÃO vai "de 16,1 para 18,0"; do dado limpo vem levemente PARA BAIXO (~19,8 → 18,5; snapshot de bancos exato 18,0). O critério de método é: `roe_valuation == median(roe(a))`, consistente com `_roe_through_cycle`.
- **Criterion #4** — "g fabricado de 36% VULC3 / 47% CYRE3 desaparece": NÃO desaparece; o `g` bruto do VULC3 SOBE (≈36,1%) e o CYRE3 é None nos dois modos. O critério de método é: `serie_lucro_normalizada` devolve a série CRUA; a winsorização temporal não é mais aplicada (medido: raw ≠ winsor, provado pelo teste de método).

**Sinal ao autor do resumo de fase / validação da Fase 14:** substituir os alvos numéricos literais dos Criteria #3 e #4 do `ROADMAP.md` pelo critério de MÉTODO, para não gerar leitura falsa de "critério não atingido".

## Issues Encountered / Golden de nível quebrado (reportado, NÃO atualizado)

Como CONSEQUÊNCIA do `g_fund` novo (que consome `roe_valuation`), **2 golden_nivel quebraram** — deixados INTACTOS por contrato (v2.4: golden de nível quebrado é DELETADO pela fase que corrige o método, NUNCA atualizado):
- `tests/test_growth_reconciliacao.py::test_teto_absoluto_025_quando_g_fund_e_cagr_explodem`
- `tests/test_growth_reconciliacao.py::test_trava_ke_quando_g_fund_supera_ke`

Ambos já classificados `golden_nivel` com o tag **"→ Fase 11 (GROW)"** na `classificacao.yaml` — são asserções de NÍVEL de `g_fund`/`g_alto` cujas fixtures foram calibradas contra o `roe_valuation` antigo; a lógica de teto (`0,25`) e trava (`≤ Ke`) em `report.py` está intocada (não é regressão de lógica, é o nível da fixture que mudou). Ficam quarentenados (deselecionados por default) até a Fase 11 os DELETAR. **O golden de ITUB4 (32,88) segue vivo — deleção é do 10-04.**

## Threat Flags
Nenhuma superfície nova. T-10-04 (roe_valuation sobre série vazia/só-None) mitigado: fronteira `None` explícita (`float(median(validos)) if validos else None`); chamável sem args preservado (número-síntese canônico das 3 superfícies).

## Known Stubs
Nenhum.

## User Setup Required
None.

## Next Phase Readiness
- PRIM-02 e PRIM-03 entregues. `roe_valuation` consistente com o `roe_terminal`; série de lucro crua alimenta o `g_historico` (e o screening, por construção).
- **Para a Fase 11 (GROW):** os 2 golden_nivel de `test_growth_reconciliacao` (tagged "→ Fase 11") aguardam DELEÇÃO quando o `g` robusto for desenhado; a série de lucro do CAGR está crua (fronteira limpa, sem winsor).
- **Blocker/nota:** o golden ITUB4=32,88 continua no repo (deleção é do 10-04, não deste plano). O RIM do ITUB4 se move (PRIM-02 sozinho: 32,88 → 31,52 no snapshot de bancos).

## Self-Check: PASSED
- FOUND: 10-02-SUMMARY.md
- FOUND commit e6bdb5f (Task 1 RED)
- FOUND commit 10b54fc (Task 2 GREEN)
- roe_valuation body = median(roe(a)); serie_winsorizada removida de fundamentals (0), preservada no screening (2); roe_qualidade_atual presente; config.yaml/calibracao.lock.yaml diff VAZIO.

---
*Phase: 10-primitivas-sem-vi-s-prim*
*Completed: 2026-07-16*
