---
phase: 11-crescimento-g-grow
plan: 01
subsystem: infra
tags: [macro, bcb, ipca, sgs-13522, valuation, entry-point-stamping]

# Dependency graph
requires:
  - phase: 10-primitivas-sem-vies-prim
    provides: "macro._ipca_anual_dezembro (SGS 13522) + o padrão de carimbo cfg['macro']['ipca_deflatores'] em cli/app (PRIM-04)"
provides:
  - "macro.ipca_ciclo_para_g(fallback, anos=10) — π_ciclo = média aritmética do IPCA na janela do rf, irmão exato de selic_ciclo_para_capm"
  - "carimbo cfg['macro']['pi_ciclo'] em cli._carimbar_macro (analyze+rank) e no fluxo analyze do app.py (wrapper cacheado pi_ciclo_capm)"
  - "default offline config.yaml macro.pi_ciclo = 0.0518 (determinismo/testes; mirror do selic_fallback)"
affects: [11-02-plan (g_cap = (1+π_ciclo)(1+PIB_real)−1), 12-ke, 14-val]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Simetria de janela rf↔π_ciclo: o π_ciclo usa a MESMA rf_ciclo_anos do rf/deflatores — o que torna o valuation invariante à inflação (GROW-02)"
    - "Insumo macro carimbado uma vez nos entry points (rede só em cli/app); engine lê cfg e permanece offline/determinística"

key-files:
  created: []
  modified:
    - src/analista/ingest/macro.py
    - config.yaml
    - src/analista/cli.py
    - app.py

key-decisions:
  - "π_ciclo é média ARITMÉTICA (sum/len), forma idêntica a selic_ciclo_para_capm — a simetria exata com o rf, não geométrica (D-06)"
  - "bloco macro está FORA do escopo do lock (motores/capm/ddm/normalizacao), como ipca_deflatores — π_ciclo é dado objetivo do BCB, NÃO knob; orçamento de 3 graus intacto"
  - "carimbo usa cfg['macro'].get('pi_ciclo', selic_fallback) como fallback offline — degradação graciosa quando o BCB falha"

patterns-established:
  - "helper macro through-cycle: reusa _ipca_anual_dezembro (zero fonte de rede nova), degrada para fallback"
  - "app.py: wrapper @st.cache_data(ttl=3600) por insumo de rede (pi_ciclo_capm espelha ipca_deflatores_capm), read-only"

requirements-completed: [GROW-01, GROW-02]

# Metrics
duration: 14min
completed: 2026-07-16
---

# Phase 11 Plan 01: Insumo carimbado de inflação de ciclo (π_ciclo) Summary

**`macro.ipca_ciclo_para_g` (IPCA médio 10a, SGS 13522, mesma janela do rf) mais o carimbo `cfg['macro']['pi_ciclo']` em cli/app e o default offline `0.0518` no config — o insumo que o `g_cap` do Plano 02 vai consumir mantendo a engine determinística.**

## Performance

- **Duration:** ~14 min
- **Completed:** 2026-07-16
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `macro.ipca_ciclo_para_g(fallback, anos=10)`: espelho exato de `selic_ciclo_para_capm` — média aritmética de `_ipca_anual_dezembro(anos).values()`, degradação graciosa para `fallback`, docstring com o ethos de pureza (chamado só nos entry points, engine nunca chama a rede).
- `config.yaml` ganhou `macro.pi_ciclo: 0.0518` (default offline/determinístico, mirror do `selic_fallback`) — os entry points o sobrescrevem com o valor ao vivo do BCB.
- `cli._carimbar_macro` carimba `cfg['macro']['pi_ciclo']` na MESMA janela `rf_ciclo_anos` (fonte única para `analyze` e `rank`, WR-03).
- `app.py`: wrapper cacheado `pi_ciclo_capm(@st.cache_data, ttl=3600)` espelhando `ipca_deflatores_capm`, e o carimbo `CFG['macro']['pi_ciclo']` no bloco analyze (read-only preservado).

## Task Commits

1. **Task 1: helper ipca_ciclo_para_g + default macro.pi_ciclo no config** — `47574e6` (feat)
2. **Task 2: carimbar pi_ciclo nos entry points (cli + app)** — `9069e3a` (feat)

## Files Created/Modified
- `src/analista/ingest/macro.py` - novo helper `ipca_ciclo_para_g` (irmão de `selic_ciclo_para_capm`, reusa SGS 13522)
- `config.yaml` - `macro.pi_ciclo: 0.0518` (default offline, fora do escopo do lock)
- `src/analista/cli.py` - carimbo `cfg['macro']['pi_ciclo']` em `_carimbar_macro` (janela `rf_ciclo_anos`)
- `app.py` - wrapper `pi_ciclo_capm` + carimbo `CFG['macro']['pi_ciclo']` no fluxo analyze

## Decisions Made
None além das já registradas no CONTEXT (D-06/D-06a): média aritmética, bloco macro fora do lock, fallback offline pelo default do config. Seguido o plano como escrito.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Nota de ambiente (não é problema): o BCB estava acessível durante a execução, então a verificação do helper "offline" retornou o valor ao vivo (`0.05138`, ≈ default `0.0518`) em vez do fallback estático. A degradação graciosa (`por_ano` vazio → `fallback`) está exercitada por construção e pelos testes de determinismo existentes; o caminho de rede apenas confirmou que a série SGS 13522 reusada resolve o valor esperado.

## Verification
- `pytest -q` → **490 passed, 1 skipped, 27 deselected, 1 xfailed, 0 failed** (suíte verde per CLAUDE.md: golden_nivel em quarentena, BLIND-02b xfailed, jackknife skipped).
- `pytest -k "orcamento_de_knobs or knobs_batem_com_o_lock"` → 2 passed (orçamento de 3 graus intacto; partição de 30 folhas inalterada — `macro` está fora do escopo).
- `git diff HEAD~2 -- calibracao.lock.yaml` VAZIO; `config.yaml` só adiciona `macro.pi_ciclo`.
- `grep -rn ipca_ciclo_para_g src/analista/report/` VAZIO — a engine não chama o helper (pureza preservada).

## Next Phase Readiness
- O insumo `cfg['macro']['pi_ciclo']` está carimbado e disponível para o Plano 02 derivar `g_cap = (1+π_ciclo)(1+PIB_real)−1` na engine (offline), com o default do config garantindo determinismo nos testes.
- Fronteira respeitada: **nenhum knob de valuation tocado**, **nenhuma derivação de `g_cap`**, **BLIND-02b permanece xfailed** (vira verde só na Fase 12). Este plano entregou apenas o insumo.

## Self-Check: PASSED

- Files: `11-01-SUMMARY.md`, `macro.py`, `config.yaml`, `cli.py`, `app.py` — all FOUND.
- Commits: `47574e6`, `9069e3a` — all FOUND in git log.

---
*Phase: 11-crescimento-g-grow*
*Completed: 2026-07-16*
