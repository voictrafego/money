---
phase: 20-selo-de-sustentabilidade-do-dividendo-cruzado-com-veredito-d
plan: 02
subsystem: ui
tags: [selo, presentation, read-only, firewall, exibe-nunca-recomenda]

# Dependency graph
requires:
  - phase: 20-01
    provides: "a.selo (cor/qualidade/faixa/rótulo/verificar) + selo.cor_do_bsd + screening.bsd_empresa"
provides:
  - "presentation.selo_emoji(cor) — emoji fixo por cor, em-dash na ausência"
  - "presentation.selo_badge(cor, rotulo, qualidade, verificar) — render único do selo (3 sítios)"
  - "app.py: selo em destaque na Analisar + coluna Selo em Garimpo e Ranking (read-only)"
affects: [phase-21-comparador-multi-ativo]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Render único do selo: mesma função pura (selo_badge/selo_emoji) nos três sítios da UI"
    - "View read-only: app.py só LÊ a.selo ou chama funções puras da engine (cor_do_bsd/bsd_empresa) — zero threshold/rótulo hardcoded"

key-files:
  created: []
  modified:
    - src/analista/report/presentation.py
    - app.py
    - tests/test_presentation_multiticker.py

key-decisions:
  - "selo_badge recebe PRIMITIVOS (cor/rotulo/qualidade/verificar), não o objeto Selo — desacopla presentation de report/selo.py"
  - "VERIFICAR na Analisar vira st.warning separado (overlay D2), suprimindo o rótulo de preço no badge"
  - "Coluna Selo posicionada logo após BSD (Garimpo) e após a Nota (Ranking); emoji idêntico via selo_emoji"

patterns-established:
  - "Formatação do selo centralizada em presentation.py (pura, sem streamlit) → idêntica nos 3 sítios por construção"

requirements-completed: [SELO-03]

# Metrics
duration: ~10min
completed: 2026-07-03
---

# Phase 20 Plan 02: Render read-only do Selo de Sustentabilidade (UI) Summary

**Camada fina read-only que DESENHA o selo derivado no Plan 01 em três lugares — selo em destaque + rótulo de quadrante na aba Analisar, e coluna de selo (mesma cor/emoji) em Garimpo e Ranking — com render único e zero fórmula em `app.py`.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-07-03
- **Completed:** 2026-07-03
- **Tasks:** 3 (2 auto + 1 checkpoint human-verify aprovado)
- **Files modified:** 3 (0 criados, 3 modificados)

## Accomplishments
- `presentation.selo_emoji(cor)`: mapa fixo 🟢/🔵/🟡/🔴, degradando para o em-dash "—" (GRAF-03) em ausência/cor desconhecida.
- `presentation.selo_badge(cor, rotulo, qualidade, verificar)`: string curta comum aos três sítios (emoji + qualidade + rótulo do quadrante); `verificar=True` insere "· Verificar dados" e suprime a faixa de preço; cor None degrada para "—". Copy 100% descritiva.
- Aba **Analisar**: selo em destaque (`st.markdown` do badge) logo abaixo do veredito colorido, lendo só `a.selo.*` (read-only), com `st.caption` explicativo e `st.warning` separado quando `a.selo.verificar`.
- Aba **Garimpo**: coluna **Selo** via `selo.cor_do_bsd(b.get("bsd"), CFG)` → `selo_emoji`, ao lado da coluna BSD (BSD já em mãos, sem recálculo).
- Aba **Ranking**: coluna **Selo** via `sc.bsd_empresa(c, CFG)` + `selo.cor_do_bsd` (read-only, sem rede — dados já carregados), casada pela empresa de cada linha.
- Suíte completa **325 verdes** (320 baseline + 5 novos de selo/presentation), zero dependência nova.
- Gate verificado: `grep -nE 'JOIA|VALUE TRAP|verde_min|>= *70|>= *55' app.py` retorna vazio — nenhum threshold de cor nem rótulo de quadrante vazou para a view.

## Task Commits

Each task was committed atomically:

1. **Task 1 (TDD): selo_emoji/selo_badge em presentation.py** - `9301a26` (test/RED) → `9fa4699` (feat/GREEN)
2. **Task 2: render read-only do selo em Analisar/Garimpo/Ranking** - `665f933` (feat)
3. **Task 3: checkpoint human-verify** - APROVADO pelo usuário (selo idêntico nos 3 lugares, VERIFICAR como alerta, copy não-imperativa)

**Plan metadata:** (final docs commit)

## Files Created/Modified
- `src/analista/report/presentation.py` - `selo_emoji` + `selo_badge` (formatação pura do selo, sem streamlit)
- `app.py` - import de `selo`; render do selo na Analisar (destaque + overlay VERIFICAR) e coluna Selo em Garimpo e Ranking
- `tests/test_presentation_multiticker.py` - 5 testes: mapa de emoji + ausência, badge JOIA, overlay Verificar sem faixa de preço, degradação em-dash, gate anti-imperativo

## Decisions Made
- `selo_badge` recebe primitivos (não o objeto `Selo`) para não acoplar `presentation` a `report/selo.py`; o `app.py` lê os campos de `a.selo` e passa adiante.
- VERIFICAR na Analisar renderizado como `st.warning` separado (overlay D2), preservando a fronteira "exibe, nunca recomenda".

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 21 (comparador multi-ativo) pode reusar `presentation.selo_emoji`/`selo_badge` para a coluna de selo por ativo, com o mesmo render read-only sobre a engine.

## Self-Check: PASSED

- Arquivos modificados existem no disco (presentation.py, app.py, tests/test_presentation_multiticker.py, este SUMMARY.md).
- Commits de tarefa existem no histórico (9301a26, 9fa4699, 665f933).
- Suíte completa 325 verdes; grep de vazamento de lógica em app.py vazio; app.py compila e importa `selo`.

---
*Phase: 20-selo-de-sustentabilidade-do-dividendo-cruzado-com-veredito-d*
*Completed: 2026-07-03*
