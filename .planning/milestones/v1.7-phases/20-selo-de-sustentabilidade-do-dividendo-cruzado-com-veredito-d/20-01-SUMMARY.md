---
phase: 20-selo-de-sustentabilidade-do-dividendo-cruzado-com-veredito-d
plan: 01
subsystem: engine
tags: [selo, bsd, ddm, quadrante, firewall, config-driven]

# Dependency graph
requires:
  - phase: 01-consistencia
    provides: "BSD com padronização absoluta reproduzível (bsd_ranking / REFERENCIA_BSD)"
  - phase: 09-11-valuation
    provides: "veredito de preço do DDM (SUBAVALIADA/NO INTERVALO/SOBREAVALIADA/VERIFICAR)"
provides:
  - "screening.bsd_empresa(c, cfg) — BSD absoluto de 1 empresa, reproduzível e never-raise"
  - "report/selo.py — Selo dataclass + cor_do_bsd + faixa_do_veredito + montar_selo (lógica pura, firewall)"
  - "bloco config.yaml selo.cor — cortes de cor do BSD tunáveis (verde 70 / azul 55 / amarelo 40)"
  - "campo a.selo populado em AnaliseAcao (cor + qualidade + faixa + rótulo de quadrante + overlay VERIFICAR)"
affects: [20-02-ui-selo, phase-21-comparador-multi-ativo]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Firewall report/selo.py × report/report.py (espelha SetupSwing): selo recebe só primitivos, nunca importa report"
    - "Matriz de rótulos fixa no código (copy estável) + limiares de cor no config (tunáveis) — separação de knobs"
    - "Derivação read-only sobre números já calculados (BSD + veredito): zero método novo, never-raise"

key-files:
  created:
    - src/analista/report/selo.py
    - tests/test_selo.py
  modified:
    - config.yaml
    - src/analista/core/screening.py
    - src/analista/report/report.py

key-decisions:
  - "Cor do selo derivada do BSD existente (D1), cortes em config.yaml (verde>=70/azul55-70/amarelo40-55/vermelho<40)"
  - "VERIFICAR é overlay separado (D2): marca verificar=True e suprime faixa/rótulo de preço, sem entrar na matriz"
  - "bsd_empresa reusa bsd_ranking([c]) — padronização absoluta torna o BSD de 1 empresa idêntico ao do lote"
  - "Matriz de quadrante (JOIA/VALUE TRAP/...) é copy fixa no código, NÃO tunável (gate 'exibe, nunca recomenda')"

patterns-established:
  - "Firewall de derivação: módulo puro recebe primitivos (bsd float, veredito str, cfg dict), never-raise"
  - "População aditiva de campo em AnaliseAcao envolta em try/except → degrada para None sem quebrar o veredito"

requirements-completed: [SELO-01, SELO-02]

# Metrics
duration: ~12min
completed: 2026-07-03
---

# Phase 20 Plan 01: Selo de Sustentabilidade × veredito de preço (engine) Summary

**Camada de derivação golden-testável que traduz o score BSD numa cor de selo e a cruza com o veredito de preço do DDM num rótulo de quadrante (JOIA/VALUE TRAP/...), com VERIFICAR como overlay — tudo na engine, antes de tocar app.py.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-03
- **Completed:** 2026-07-03
- **Tasks:** 3
- **Files modified:** 5 (2 criados, 3 modificados)

## Accomplishments
- `screening.bsd_empresa(c, cfg)`: BSD (0-100) de UMA empresa reusando `bsd_ranking([c])`, reproduzível (padronização absoluta) e never-raise para a UI.
- `report/selo.py` (módulo puro, firewall vs report.py): `Selo` dataclass, `cor_do_bsd` (config-driven), `_qualidade`, `faixa_do_veredito` (por prefixo), `_MATRIZ` (6 rótulos D2) e `montar_selo` (VERIFICAR como overlay, never-raise).
- Bloco `selo.cor` em config.yaml: único ponto de ajuste dos cortes de cor (verde 70 / azul 55 / amarelo 40).
- Campo aditivo `a.selo` populado em `analisar_acao` após o veredito, sem tocar a rede e sem quebrar os goldens.
- Suíte completa 320 verdes (307 baseline + 13 testes de selo), zero dependência nova.

## Task Commits

Each task was committed atomically:

1. **Task 1: bloco selo: no config.yaml + bsd_empresa em screening.py** - `c4f4d45` (feat)
2. **Task 2 (TDD): report/selo.py + wiring em report.py** - `1f8f36c` (test/RED) → `de0d6f7` (feat/GREEN)
3. **Task 3: tests/test_selo.py suíte golden completa** - `c784da6` (test)

**Plan metadata:** (final docs commit)

## Files Created/Modified
- `src/analista/report/selo.py` - módulo puro do selo (cor/qualidade/faixa/quadrante), firewall vs report.py
- `src/analista/core/screening.py` - `bsd_empresa(c, cfg=None)` reusável e reprodutível
- `config.yaml` - bloco de topo `selo.cor` (cortes de cor tunáveis)
- `src/analista/report/report.py` - import de screening/selo, campo `selo` em AnaliseAcao, população never-raise
- `tests/test_selo.py` - goldens: cortes+bordas, qualidade, faixa, matriz de 6 rótulos, overlay VERIFICAR, degradação, firewall, integração

## Decisions Made
- Seguido o plano como especificado. Reforço: matriz de rótulos vive no código (copy estável), só os limiares de cor no config — evita que afinar cores mexa na copy regulatória.

## Deviations from Plan

None - plan executed exactly as written.

(Ajuste menor durante a Task 2: o teste de firewall inicial casava "report.py" citado na docstring; corrigido para inspecionar apenas as linhas de `import`/`from`. Correção de teste dentro da própria tarefa TDD, sem mudança de escopo.)

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 02 (UI): pode desenhar o selo lendo `a.selo` (cor, qualidade, faixa_preco, rotulo, verificar) na aba Analisar e, com `screening.bsd_empresa`, montar a coluna de selo no Garimpo/Ranking. Nada a recalcular na view (app.py read-only).
- Firewall verificável e goldens verdes: fronteira "EXIBE, NUNCA recomenda" preservada antes da camada visual.

## Self-Check: PASSED

- Todos os arquivos criados/modificados existem no disco (selo.py, test_selo.py, config.yaml, screening.py, SUMMARY.md).
- Todos os commits de tarefa existem no histórico (c4f4d45, 1f8f36c, de0d6f7, c784da6).
- Suíte completa 320 verdes (307 baseline + 13 selo).

---
*Phase: 20-selo-de-sustentabilidade-do-dividendo-cruzado-com-veredito-d*
*Completed: 2026-07-03*
