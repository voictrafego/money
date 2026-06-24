---
phase: 01-engine-de-consist-ncia
plan: 05
subsystem: ui
tags: [streamlit, app, garimpo, ranking, analisar, bsd, payout, valor-intrinseco]

# Dependency graph
requires:
  - phase: 01-engine-de-consist-ncia (Plano 01)
    provides: "CompanyData.payout_valuation() (média 3a + clamp 1.0) — payout canônico consumido pelo Ranking"
  - phase: 01-engine-de-consist-ncia (Plano 02)
    provides: "preco_alvo_por_regressao com clamp + PrecoAlvo.payout_fora_faixa — sinalização no Ranking"
  - phase: 01-engine-de-consist-ncia (Plano 03)
    provides: "bsd_ranking absoluto/reprodutível + fatores_faltantes/n_fatores_faltantes por linha"
  - phase: 01-engine-de-consist-ncia (Plano 04)
    provides: "AnaliseAcao.vmin/vmax — intervalo intrínseco da fonte única, lido pela UI"
provides:
  - "Garimpo ordena por 'Passa filtros' (corte Selic) antes do BSD; quem reprova no corte não fica no topo, com aviso explícito de que BSD>80 sem 'Passa filtros' não é recomendação"
  - "Ranking monta o vetor DP com payout_valuation() (canônico, mesmo do Analisar) e sinaliza payout_fora_faixa na tabela"
  - "Analisar exibe o intervalo de valor intrínseco lendo a.vmin/a.vmax (report.py), sem recomputar min/max na UI"
affects: [fase-2-apresentacao, app-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "UI consome a engine canônica na borda: ordena/filtra por campos já calculados (Passa filtros, payout_valuation, vmin/vmax) sem recomputar lógica de método na camada de apresentação"

key-files:
  created: []
  modified:
    - app.py

key-decisions:
  - "Garimpo ordena por ['Passa filtros', 'BSD'] (filtro Selic primeiro, BSD desc depois) — o corte por Selic prometido na sidebar passa a valer de fato na ordenação"
  - "Ranking usa payout_valuation() como vetor DP e como dp do preço-alvo; payout_fora_faixa é sinalizado na tabela espelhando o alerta do Analisar"
  - "Analisar lê a.vmin/a.vmax em vez de recomputar min/max([ddm_h, ddm_constante]); fallback '—' mantido quando None"

patterns-established:
  - "Camada de apresentação (app.py) não recalcula agregações do método — apenas formata campos já expostos pela engine (Passa filtros, payout_valuation, vmin/vmax)"

requirements-completed: [GARIMPO-01, PAYOUT-01, RANK-02, VAL-01]

# Metrics
duration: ~15min
completed: 2026-06-05
---

# Phase 01 Plan 05: Wire dos 3 modos do app à engine canônica Summary

**Conectou os três modos do `app.py` à engine corrigida nos Planos 01–04: Garimpo ordena por "Passa filtros" (corte Selic) antes do BSD, Ranking monta o payout via `payout_valuation()` com sinalização de payout fora de faixa, e Analisar exibe o intervalo intrínseco lendo `a.vmin`/`a.vmax` — fechando GARIMPO-01/PAYOUT-01/RANK-02/VAL-01 na borda da UI. Verificação humana dos três modos no navegador APROVADA.**

## Performance

- **Duration:** ~15 min
- **Tasks:** 3 (2 auto + 1 checkpoint:human-verify)
- **Files modified:** 1

## Accomplishments
- **Garimpo respeita o corte Selic na ordenação:** a tabela ordena por "Passa filtros" antes do BSD, com aviso explícito de que BSD>80 sem "Passa filtros" não é recomendação. Empresas com DY < Selic deixam de aparecer recomendadas no topo (CR-01).
- **Ranking consome o payout canônico:** o vetor DP e o dp do preço-alvo vêm de `c.payout_valuation()` (mesma janela/clamp do Analisar), e `payout_fora_faixa` é sinalizado na tabela — espelhando o alerta do Analisar.
- **Analisar reusa o intervalo único:** a métrica de valor intrínseco lê `a.vmin`/`a.vmax` (cálculo único do veredito em report.py), sem recomputar min/max na UI (fechando WR-07/VAL-01 na apresentação).
- **Verificação humana aprovada:** os três modos foram validados manualmente no navegador (Garimpo com lote de energia + reprodutibilidade do BSD entre lotes, Ranking com sinalização de payout ajustado, Analisar com valor intrínseco coerente com o veredito). Resposta do usuário: "approved".

## Task Commits

Cada task auto foi commitada atomicamente:

1. **Task 1: Garimpo ordena/realça por "Passa filtros" (corte Selic) antes do BSD** — `3654002` (feat)
2. **Task 2: Ranking usa payout canônico (clamp/flag) e Analisar reusa vmin/vmax** — `ad17e9c` (feat)
3. **Task 3: Verificação humana dos três modos no navegador** — checkpoint:human-verify (gate blocking), APROVADO pelo usuário ("approved"); sem commit de código (verificação visual/funcional).

## Files Created/Modified
- `app.py` — modo Garimpar ordena por `["Passa filtros", "BSD"]` com aviso de não-recomendação; modo Ranking monta `DP` via `c.payout_valuation()` e sinaliza `payout_fora_faixa`; modo Analisar lê `a.vmin`/`a.vmax` no lugar do recálculo `min/max`.

## Decisions Made
- Garimpo ordena por "Passa filtros" antes de BSD para que o corte Selic prometido na sidebar valha de fato na lista exibida.
- Ranking usa `payout_valuation()` tanto no vetor DP quanto no dp do preço-alvo, garantindo que o payout que decide o preço-alvo seja o mesmo que decide o valor intrínseco no Analisar (PAYOUT-01/RANK-02).
- Ajuste da regressão em si NÃO foi alterado (pares do setor seguem como na engine) — escopo restrito à borda de apresentação.
- Analisar passa a depender de `a.vmin`/`a.vmax`, mantendo fallback "—" quando None (intervalo único, sem duplicação de cálculo).

## Deviations from Plan

None - plan executed exactly as written (Tasks 1-2 implementadas e commitadas conforme o plano; Task 3 é checkpoint humano, aprovado).

## Issues Encountered
None.

## Verification

- `python -c "import ast; ast.parse(open('app.py').read())"` → app.py parseia sem erro.
- Marcadores na borda presentes em app.py: `Passa filtros`, `sort_values`, `payout_valuation`, `a.vmin`, `a.vmax`.
- `pytest tests/ -q` → **44 passed** (golden de ddm/multiples/comparables/screening + consistência intactos — engine não tocada).
- Checkpoint humano (Task 3): três modos validados no navegador, resposta "approved".

## Next Phase Readiness
- Fase 01 (Engine de Consistência) concluída: a UI agora cumpre o que a engine promete nos três modos.
- Fase 02 (Apresentação e Travas de Consistência) pode prosseguir: expor ano-base efetivo, "indisponível" no Ranking, payouts rotulados, e travar a coerência entre modos com testes automatizados.

## Self-Check: PASSED
- FOUND: app.py (Passa filtros / payout_valuation / a.vmin / a.vmax presentes)
- FOUND: commit 3654002 (Task 1)
- FOUND: commit ad17e9c (Task 2)
- pytest: 44 passed
- Checkpoint humano: approved

---
*Phase: 01-engine-de-consist-ncia*
*Completed: 2026-06-05*
