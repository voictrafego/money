---
phase: 01-engine-de-consist-ncia
plan: 03
subsystem: screening
tags: [bsd, carlson, garimpo, padronizacao-absoluta, glossario, pytest]

# Dependency graph
requires:
  - phase: 01-engine-de-consist-ncia (plan 01)
    provides: payout_valuation canônico, ROE em PL médio (None no 1º ano), dy_atual trailing-12m
provides:
  - "BSD padronizado contra referência fixa (REFERENCIA_BSD, 10 bandas calibráveis) — reproduzível entre lotes"
  - "Corte 'BSD > 80' absoluto (não rank relativo ao lote)"
  - "Fatores ausentes entram como neutro (50), não como pior valor (0)"
  - "bsd_ranking expõe fatores_faltantes (List[str]) e n_fatores_faltantes (int) por empresa"
  - "Proxy de crescimento (crescimento_lucro_lp) usa média roe/payout na janela anos_media"
  - "Tooltip do BSD documenta nota absoluta, proxy de crescimento e fatores ausentes"
affects: [app.py (exibição do BSD e dos fatores faltantes), ranking, garimpo]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Padronização absoluta por bandas fixas calibráveis (clamp linear contra referência), substituindo min-max do lote"
    - "Ausente (None) tratado como neutro (50) e contado, distinto de pior valor (0)"

key-files:
  created: []
  modified:
    - src/analista/core/screening.py
    - src/analista/glossario.py
    - tests/test_screening.py

key-decisions:
  - "REFERENCIA_BSD é o único ponto calibrável do corte 80 (comentário CALIBRÁVEL no topo do módulo); a lógica de padronização não muda ao ajustar bandas"
  - "Winsorização aposentada no caminho do BSD — o clamp das bandas fixas já limita extremos; parâmetro winsor mantido só por compatibilidade de assinatura"
  - "Fator ausente recebe nota neutra 50 (não 0), distinguindo 'ausente' de 'pior valor'"
  - "Proxy crescimento_lucro_lp usa média de roe/payout na mesma janela anos_media (ignora None, incl. roe do 1º ano sem PL inicial)"

patterns-established:
  - "Padronização absoluta (_padronizar_absoluto) contra banda (lo,hi): nota = clamp((v-lo)/(hi-lo),0,1)*100; reproduzível entre execuções"
  - "Smoke do corte 80 via monkeypatch de indicadores_bsd (perfis forte/fraca posicionados nas bandas)"

requirements-completed: [GARIMPO-02, GARIMPO-03, GARIMPO-04]

# Metrics
duration: 5min
completed: 2026-06-05
---

# Phase 01 Plan 03: BSD absoluto, ausentes neutros e proxy de crescimento padronizado Summary

**BSD do Garimpo reproduzível e absoluto (bandas fixas calibráveis em REFERENCIA_BSD), fatores ausentes neutros e contados, e proxy de crescimento na janela anos_media — fechando WR-06, WR-05 e WR-02.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-06-05T11:58:32Z
- **Completed:** 2026-06-05T12:02:43Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- BSD agora é absoluto: a mesma ação tem o mesmo BSD sozinha ou dentro de um lote (reprodutibilidade < 1e-6); "BSD > 80" voltou a ser corte absoluto de Carlson, não rank relativo ao conjunto submetido (GARIMPO-02).
- Fatores com dado ausente entram como neutro (50), não como pior valor (0); `bsd_ranking` expõe `fatores_faltantes` e `n_fatores_faltantes` por empresa (GARIMPO-03).
- O proxy `crescimento_lucro_lp` passou a usar a média de roe/payout na janela `anos_media` (não mais ano único), ignorando None, e o tooltip documenta que é ROE×(1−payout) por fundamentos (GARIMPO-04).
- Suíte completa verde (44 testes), com o golden de BSD reescrito para o novo comportamento e novos smokes do corte 80, da reprodutibilidade e dos fatores faltantes.

## Task Commits

Cada task foi commitada atomicamente (TDD: RED via verify inline → GREEN):

1. **Task 1: Padronização absoluta do BSD (REFERENCIA_BSD)** - `6a2b81c` (feat)
2. **Task 2: Fatores ausentes neutros + contagem; proxy na janela anos_media** - `f0f8000` (feat)
3. **Task 3: Tooltip do BSD, golden e smoke do corte 80** - `2810256` (test)

_Nota: a RED de cada task TDD foi comprovada pelos blocos `<verify>` inline do plano (reprodutibilidade falhava 50 vs 100; chaves de faltantes inexistentes) antes da implementação._

## Files Created/Modified
- `src/analista/core/screening.py` - `REFERENCIA_BSD` (10 bandas fixas calibráveis); `_padronizar_absoluto` (clamp linear, ausente→50 neutro); `bsd_ranking` reescrito (padronização absoluta, sem re-padronização min-max, expõe fatores faltantes); proxy de crescimento na janela `anos_media`.
- `src/analista/glossario.py` - chave `bsd` reescrita: nota absoluta (corte 80 válido), proxy ROE×(1−payout) por fundamentos, fatores ausentes neutros/contados.
- `tests/test_screening.py` - `test_bsd_ranking_ordena_e_marca_acima_80` reescrito (novo comportamento absoluto); novos `test_bsd_corte_80_absoluto_via_padronizar`, `test_bsd_reprodutivel_entre_lotes`, `test_bsd_fatores_faltantes_neutros`.

## Decisions Made
- `REFERENCIA_BSD` marcada como `# CALIBRÁVEL` no topo do módulo — único ponto de ajuste do corte 80; ajustar bandas não toca a lógica de padronização.
- Winsorização aposentada no caminho do BSD; `winsor` mantido só por compatibilidade de assinatura (documentado no docstring de `bsd_ranking`).
- Ausente → nota neutra 50 (não 0), distinguindo "ausente" de "pior valor" (WR-05).
- Proxy de crescimento usa média na janela `anos_media`, ignorando `roe(ano)=None` do 1º ano (comportamento LOCKED de WR-01, aceito e documentado).

## Deviations from Plan

None - plan executed exactly as written.

(Remoção da variável `ult`, agora ociosa em `indicadores_bsd` após o proxy passar a usar a média da janela, é limpeza inerente à Task 2, não desvio de escopo.)

## Issues Encountered
- O golden `test_bsd_ranking_ordena_e_marca_acima_80` falhava após Task 1/2 por afirmar `bsd==100.0/0.0` (comportamento min-max do lote que GARIMPO-02 elimina). Era esperado pelo plano e foi reescrito na Task 3 para o comportamento absoluto. Os demais testes de screening (customizados, graham) e os golden de valuation (ddm/multiples/comparables) permaneceram intactos.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BSD reproduzível e absoluto; pronto para o app expor `n_fatores_faltantes`/`fatores_faltantes` na UI do Garimpo (fora do escopo deste plano de engine).
- Sem blockers introduzidos. Restrição dura (golden tests verdes) mantida.

## Self-Check: PASSED

---
*Phase: 01-engine-de-consist-ncia*
*Completed: 2026-06-05*
