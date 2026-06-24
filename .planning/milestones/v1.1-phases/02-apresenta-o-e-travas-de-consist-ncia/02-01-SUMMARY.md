---
phase: 02-apresenta-o-e-travas-de-consist-ncia
plan: 01
subsystem: ui
tags: [streamlit, glossario, tooltips, valuation, dividendos]

# Dependency graph
requires:
  - phase: 01-engine-de-consistencia
    provides: "Campos canônicos da engine (ultimo_ano, payout, payout_valuation, preco_alvo_por_regressao com None) que a UI agora apenas lê e formata"
provides:
  - "Coluna 'Ano-base' (ultimo_ano) no Garimpo e no Ranking — torna visível mistura de anos na comparação (ANO-01)"
  - "Dois payouts rotulados na aba Múltiplos do Analisar: 'Payout (último ano)' (cru) e 'Payout p/ valuation (média 3a)' (canônico do DDM) (PAYOUT-02)"
  - "'indisponível' (estado neutro) no Ranking quando a empresa é descartada da regressão (pa is None), em vez de '—' ambíguo (RANK-01)"
  - "3 tooltips novos no glossário (ano_base, payout_dual, indisponivel) acessíveis por h()"
affects: [02-02-tests, travas-de-consistencia-cross-modo]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "UI lê campos da engine canônica e apenas formata (zero recálculo de método em app.py) — regra LOCKED da Fase 1 mantida"
    - "Lookup por ticker no Ranking (next(c.X for c in empresas if c.ticker == r['empresa'])) espelhando o idiom já usado em 'Preço atual'"

key-files:
  created: []
  modified:
    - src/analista/glossario.py
    - app.py

key-decisions:
  - "Em pa is None o Ranking mostra 'indisponível' como texto neutro (sem cor de erro), não '—' — '—' era lido como 'cara/barata' (RANK-01)"
  - "Aba Múltiplos desdobra 'DP (payout)' em duas linhas rotuladas quando o payout exibido (último ano cru) difere do usado pelo DDM (média 3a + clamp), sem ambiguidade (PAYOUT-02)"
  - "Nenhuma aritmética de payout/ROE/min-max nova em app.py: a UI só lê Optional[int]/Optional[float] já computados pela engine"

patterns-established:
  - "Apresentação read-only: app.py é camada de formatação; toda regra de método vive na engine (fundamentals/report/comparables)"

requirements-completed: [ANO-01, PAYOUT-02, RANK-01]

# Metrics
duration: 11min
completed: 2026-06-05
---

# Phase 2 Plan 01: UI — Ano-base, dual-payout e "indisponível" Summary

**Coluna Ano-base (Garimpo+Ranking), dois payouts rotulados na aba Múltiplos do Analisar e 'indisponível' neutro no Ranking, ligando à UI campos que a engine canônica da Fase 1 já expunha — sem recálculo de método em app.py — mais 3 tooltips no glossário; checkpoint human-verify APROVADO pelo usuário.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-06-05T15:50:29Z
- **Completed:** 2026-06-05T16:01:02Z
- **Tasks:** 3 (2 auto + 1 checkpoint human-verify aprovado)
- **Files modified:** 2

## Accomplishments
- **ANO-01:** Garimpo e Ranking passaram a exibir o ano-base efetivo (`ultimo_ano`) de cada empresa, deixando visível quando há mistura de anos na comparação.
- **PAYOUT-02:** Aba "📈 Múltiplos & Crescimento" do Analisar mostra duas linhas rotuladas — "Payout (último ano)" (cru, `c.payout(ult)`) e "Payout p/ valuation (média 3a)" (`c.payout_valuation()`, canônico do DDM) — quando os valores divergem.
- **RANK-01:** Ranking exibe "indisponível" (e "indisponível (ROE/payout ausente)" no veredito) como texto neutro quando `pa is None`, eliminando o "—" ambíguo lido como "cara".
- 3 tooltips novos no glossário (`ano_base`, `payout_dual`, `indisponivel`), wired via `h()`.
- Checkpoint human-verify (gate blocking) **APROVADO** pelo usuário ("approved") após verificação no navegador dos três comportamentos.

## Task Commits

Each task was committed atomically:

1. **Task 1: Adicionar 3 tooltips ao glossário** - `1b4eaf0` (feat)
2. **Task 2: ANO-01 + PAYOUT-02 + RANK-01 em app.py** - `e095c6d` (feat)
3. **Task 3: Checkpoint human-verify (gate blocking)** - APROVADO pelo usuário; sem commit de código (verificação visual/funcional)

**Plan metadata:** committed separately (docs: complete plan)

## Files Created/Modified
- `src/analista/glossario.py` - 3 chaves novas no dict G (ano_base, payout_dual, indisponivel), acessíveis por h(); função h() intacta
- `app.py` - Coluna "Ano-base" no Garimpo e no Ranking (leitura de ultimo_ano), dois payouts rotulados na aba Múltiplos (payout cru + payout_valuation), "indisponível" no branch pa is None do Ranking; helpers fmt_* (app.py:48-57) intactos

## Decisions Made
- "indisponível" renderizado como texto neutro (sem cor de erro) — estado neutro, não erro; substitui o "—" ambíguo apenas localmente no branch `pa is None`.
- Desdobramento de "DP (payout)" em duas linhas rotuladas apenas onde o payout cru difere do payout canônico usado pelo DDM, sem perder o tooltip de múltiplos existente.
- Zero recálculo de método em app.py: a UI lê os campos da engine (`ultimo_ano()`, `payout()`, `payout_valuation()`) e apenas formata — regra LOCKED da Fase 1 preservada.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Verification Results
- `.venv/bin/python -c "import ast; ast.parse(open('app.py').read())"` → parse OK (app.py compila)
- `.venv/bin/python -c "from analista.glossario import h; assert h('ano_base') and h('payout_dual') and h('indisponivel')"` → tooltips OK
- Literais presentes em app.py: "Ano-base" (4 ocorrências), "Payout (último ano)", "Payout p/ valuation (média 3a)", "indisponível", "payout_valuation" → todos OK
- `.venv/bin/pytest tests/ -q` → **44 passed** (golden verde, sem regressão)
- Checkpoint human-verify (navegador, TAEE11 + tickers default nos 3 modos) → **APROVADO** pelo usuário

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- UI honesta entrega: ANO-01, PAYOUT-02, RANK-01 cobertos e verificados no navegador.
- Pronto para 02-02 (TEST-01/TEST-02): travas de consistência cross-modo + golden verde — a UI agora consome exatamente os campos canônicos que os testes de consistência vão travar.
- Sem blockers.

---
*Phase: 02-apresenta-o-e-travas-de-consist-ncia*
*Completed: 2026-06-05*

## Self-Check: PASSED

- SUMMARY.md present
- Commits 1b4eaf0, e095c6d, e57f06c verified in git log
