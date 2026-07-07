---
phase: 21-comparador-multi-ativo-lado-a-lado-m-ltiplos-selo-por-coluna
plan: 01
subsystem: ui
tags: [comparador, streamlit, selo, multiplos, pandas, dataframe-transposto]

# Dependency graph
requires:
  - phase: 20-selo-de-sustentabilidade
    provides: "report.analisar_acao(...).selo + presentation.selo_badge (Selo COMPLETO por quadrante)"
  - phase: 19-lentes-de-valuation
    provides: "lentes.metricas_par (5 múltiplos canônicos, never-raise) + o embrião Comparador de pares"
provides:
  - "core.lentes.normalizar_tickers — parse/upper/dedup/cap da entrada livre de tickers (COMP-01)"
  - "report.comparador.montar_comparativo — DataFrame transposto (tickers em colunas) + selo por coluna + suficiência ≥2 (COMP-02/03)"
  - "report.presentation.fmt_rs — fonte única de formatação ptBR de reais na engine"
  - "5º menu 'Comparar ações' no app.py (bloco elif read-only)"
affects: [comparador, triagem-multi-ativo, futuras-lentes-de-comparacao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Firewall read-only: toda derivação nova vive na engine (lentes/comparador/presentation) com testes; app.py só faz fetch cacheado + render"
    - "DataFrame transposto via dict-de-dicts + reindex para ordem fixa de linhas"
    - "never-raise por coluna: contexto quebrado degrada isoladamente sem derrubar a tabela"

key-files:
  created:
    - src/analista/report/comparador.py
    - tests/test_comparador.py
  modified:
    - src/analista/core/lentes.py
    - src/analista/report/presentation.py
    - tests/test_lentes.py
    - app.py

key-decisions:
  - "Toda lógica nova na engine (gate do projeto vence a sugestão do pattern-mapper de fazer tudo em app.py)"
  - "Selo COMPLETO por coluna via analisar_acao(...).selo + selo_badge — não o atalho só-cor (selo_emoji/cor_do_bsd)"
  - "Regra de suficiência ≥2 sem ticker-alvo (substitui pares_suficientes) — comparador não tem alvo"
  - "never-raise reforçado por coluna (try/except envolvendo o bloco inteiro por ticker, não só analisar_acao)"

patterns-established:
  - "Comparador: tickers em COLUNAS, métricas em LINHAS na ordem fixa [Selo, P/L, P/VP, ROE, DY, Valor de Mercado]"
  - "fmt_rs em presentation como fonte única de reais ptBR (espelha o helper de app.py)"

requirements-completed: [COMP-01, COMP-02, COMP-03]

# Metrics
duration: 6min
completed: 2026-07-03
---

# Phase 21 Plan 01: Comparador multi-ativo lado a lado Summary

**Comparador lado a lado de N tickers (5º menu 'Comparar ações') exibindo os 5 múltiplos e o Selo COMPLETO da Phase 20 por coluna, com toda a derivação na engine testada por golden e app.py 100% read-only.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-07-03T11:13:14Z
- **Completed:** 2026-07-03T11:18:54Z
- **Tasks:** 3
- **Files modified:** 6 (2 criados, 4 modificados)

## Accomplishments
- `lentes.normalizar_tickers` (COMP-01): borda de input never-raise que faz parse (vírgula+espaço), upper, dedup preservando ordem e cap — sem ordenar nem recomendar.
- `comparador.montar_comparativo` (COMP-02/03): monta o DataFrame transposto (tickers em colunas, 6 linhas na ordem fixa com "Selo" no topo), usando `lentes.metricas_par` para os 5 múltiplos e `analisar_acao(...).selo` + `selo_badge` para o Selo COMPLETO por coluna; regra de suficiência ≥2 e degradação never-raise por coluna.
- `presentation.fmt_rs`: fonte única de formatação ptBR de reais na engine.
- 5º menu "Comparar ações" no `app.py` — bloco `elif` read-only (normaliza entrada, fetch cacheado via `montar`, render da tabela ou `st.info` neutro com <2 resolvidos).
- Suíte golden completa verde: 338 passed (de 325 na baseline; +13 testes novos).

## Task Commits

Cada tarefa foi comitada atomicamente (TDD RED→GREEN nas Tasks 1 e 2):

1. **Task 1 RED: testes de normalizar_tickers** - `2d6c9ac` (test)
2. **Task 1 GREEN: lentes.normalizar_tickers** - `1330fa5` (feat)
3. **Task 2 RED: testes de montar_comparativo + fmt_rs** - `fabeb57` (test)
4. **Task 2 GREEN: comparador.montar_comparativo + presentation.fmt_rs** - `66ba454` (feat)
5. **Task 3: wiring read-only do 5º menu em app.py** - `4a231dc` (feat)

## Files Created/Modified
- `src/analista/core/lentes.py` - Adicionada `normalizar_tickers(texto, cap)` (COMP-01, never-raise).
- `src/analista/report/comparador.py` - **NOVO** módulo: `ComparativoTabela` + `montar_comparativo` (DataFrame transposto + selo por coluna + suficiência ≥2).
- `src/analista/report/presentation.py` - Adicionada `fmt_rs(x, casas)` (reais ptBR, None→"—").
- `tests/test_lentes.py` - 5 casos novos cobrindo os comportamentos de `normalizar_tickers`.
- `tests/test_comparador.py` - **NOVO** golden do comparador (transposto, selo COMPLETO por coluna, degradação, suficiência, fmt_rs, never-raise).
- `app.py` - Import interno `comparador`, item "Comparar ações" no sidebar radio e bloco `elif modo.startswith("Comparar")` read-only.

## Decisions Made
- Firewall read-only: toda derivação nova (parse, montagem de tabela, suficiência, formatação de reais) vive na engine com testes; `app.py` só orquestra fetch cacheado + render. O gate do projeto vence a sugestão do pattern-mapper.
- Selo COMPLETO por coluna via `analisar_acao(...).selo` + `selo_badge` (COMP-03) — deliberadamente NÃO o atalho só-cor `selo_emoji(cor_do_bsd(...))`.
- Suficiência ≥2 sem ticker-alvo (regra nova que substitui `pares_suficientes`, que exige alvo).

## Deviations from Plan

### Ajustes de execução (não Rules 1-4; refinamentos de fidelidade ao spec)

**1. Exemplo degenerado do bloco `<behavior>` inconsistente com a implementação mandatada (Task 1)**
- **Issue:** O `<behavior>` lista `",, ;" → []`, mas o `<action>` manda replicar EXATAMENTE o idioma da casa (`texto.replace(",", " ").split()`), no qual `;` NÃO é separador e sobreviveria como token (`[";"]`).
- **Decisão:** Segui o `<action>` (idioma da casa, fonte de verdade da implementação). O teste do caso degenerado usa entrada só com vírgula/espaço (`",,  ,"` → `[]`), que exercita fielmente o "never-raise → []" sem depender do `;`. Nenhum acceptance_criteria da Task 1 pinava `",, ;"`.
- **Arquivos:** tests/test_lentes.py
- **Commit:** 2d6c9ac / 1330fa5

**2. never-raise reforçado por coluna (Task 2)**
- **Issue:** O `<action>` sugere try/except só ao redor de `analisar_acao`. Mas o `<behavior>` exige que "um contexto que faça analisar_acao falhar não derrube a função — a coluna degrada e as demais aparecem". Um stub quebrado também derruba `metricas_par`.
- **Decisão (Rule 2 — robustez/never-raise como contrato):** Envolvi o bloco inteiro por ticker em try/except (selo já resolvido isoladamente + métricas degradam para "—"), garantindo degradação por coluna mesmo quando `metricas_par` falha. Estritamente mais never-raise; satisfaz todos os comportamentos.
- **Arquivos:** src/analista/report/comparador.py
- **Commit:** 66ba454

**3. Expectativa de teste corrigida: selo não degrada para "—" só por dados esparsos (Task 2)**
- **Issue:** Um `CompanyData(ticker="NONE3", anos=[2023])` (sem preço/nº ações) ainda produz um Selo com cor (BSD computável) — logo a célula "Selo" NÃO é "—".
- **Fix:** Removida a assertiva incorreta `Selo["NONE3"]=="—"`; o teste passou a focar no que o caso realmente exercita (múltiplos ausentes → "—"). A degradação do selo para "—" já é coberta pelo teste de never-raise (stub `_Quebrado`).
- **Arquivos:** tests/test_comparador.py
- **Commit:** 66ba454

## Issues Encountered

**Gate `grep -c "Comparador de pares (contexto)" == 1` (Task 3):** o valor real é **2**, mas isso é uma imprecisão do plano — a string aparece em DUAS linhas pré-existentes no `app.py` (um comentário em §938 e o título do expander em §942), já assim na baseline (HEAD). Meu diff NÃO toca o expander (confirmado por `git diff`), e a contagem não mudou (2→2). A INTENÇÃO do gate — "expander da aba Analisar intacto" — está plenamente satisfeita.

## User Setup Required
None - nenhuma configuração de serviço externo. Zero dependências 3rd-party novas (só `analista.*` + pandas já instalado).

## Next Phase Readiness
- Comparador funcional e testado; pronto para o checkpoint humano da fase (smoke: 3 tickers do mesmo setor → tickers nas colunas, selo no topo de cada coluna, "—" em métrica faltante, `st.info` com <2).
- Todos os gates do projeto respeitados: golden 100% verde (338 passed), `app.py` read-only para lógica, zero deps novas, custo-zero (só `montar` cacheado), expander de pares intacto.

## Self-Check: PASSED

- Arquivos criados verificados: comparador.py, test_comparador.py (+ lentes.py/presentation.py modificados).
- Commits verificados no git log: 2d6c9ac, 1330fa5, fabeb57, 66ba454, 4a231dc.
- `python -m pytest tests/ -q` → 338 passed.

---
*Phase: 21-comparador-multi-ativo-lado-a-lado-m-ltiplos-selo-por-coluna*
*Completed: 2026-07-03*
