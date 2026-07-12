---
phase: 02-motores-por-arqu-tipo
plan: 01
subsystem: engine
tags: [valuation, rim, dcf, nav, lucro-normalizado, motores, config-driven, golden-tests, python]

# Dependency graph
requires:
  - phase: 01-classificador-roteamento
    provides: "registry arquétipo→motor com DDM plugado; slots RIM/normalizado/DCF/NAV vazios (None)"
provides:
  - "core/motores.py — rim() + ResultadoRIM, ke_rim(), lucro_normalizado(), dcf_crescimento(), nav_contabil() (funções puras never-raise, config-driven)"
  - "MOTOR_ROTULO — rótulos humanos por motor para o render do Plan 02"
  - "config.yaml bloco motores: (rim/ciclica/crescimento) aditivo, anti-rebaseline"
  - "tests/test_motores.py — golden puro por motor (RIM ~R$28, ke_rim<ke_live, normalizado 7-10a, dcf>0 finito, nav=vpa)"
affects: [02-02-plug-registry-funil, 03-veredito-honesto, ensemble-divergencia]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Motor como função pura config-driven que COMPÕE primitivas testadas (ddm/lentes/normalizacao) — nunca recalcula método (FIX-04)"
    - "Ke estrutural do RIM derivado com clamp piso/teto/ke_live (D-01) — nunca herda o CAPM ao vivo de banco"
    - "Bloco config novo irmão de arquetipo:, aditivo (anti-rebaseline, Pitfall 5)"

key-files:
  created:
    - src/analista/core/motores.py
    - tests/test_motores.py
  modified:
    - config.yaml

key-decisions:
  - "RIM honesto ~R$28 (faixa R$26–34) vence o alvo aproximado ~R$40 de D-01 — modelo conservador sem prêmio terminal (D-02), materialmente > DDM ao vivo (~R$16)"
  - "ke_rim = rf-ciclo + beta×erp_banco (0.045, sem prêmio small-cap), clampado a [0.11, 0.14] e nunca > ke_live — destrava o ITUB4 (D-01)"
  - "dcf_crescimento é reuso PURO de ddm.ddm_dois_estagios (LUCRO no lugar de dividendo, modelo-H), ddm.py INTOCADO (D-05)"

patterns-established:
  - "Motor puro config-driven espelhando ddm.py: dataclass de resultado + Number=Optional[float] + guard never-raise no topo"
  - "Motores consomem números já-síntese (roe_valuation/lpa_valuation/base_normalizada/lentes.vpa), fronteira FIX-04"

requirements-completed: [ENG-02, ENG-03, ENG-04, ENG-05]

# Metrics
duration: 18min
completed: 2026-07-11
---

# Phase 2 Plan 01: Motores por Arquétipo Summary

**Os 4 motores de valuation que faltavam (RIM, lucro normalizado, DCF de crescimento, NAV contábil) como funções puras config-driven em `core/motores.py`, com o Ke estrutural do RIM (D-01) que destrava o ITUB4 (~R$28 honesto, > DDM ao vivo ~R$16), golden-testados sem tocar nenhum módulo `core/` existente.**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-07-11T22:50Z
- **Completed:** 2026-07-11
- **Tasks:** 3
- **Files modified:** 3 (2 criados, 1 modificado)

## Accomplishments
- **RIM (ENG-02)** com fade linear do excesso de ROE até o Ke e clean surplus, SEM prêmio terminal — ancora o valor no VPA; inputs tipo-ITUB4 rendem **R$28,20** (verificado aritmeticamente, faixa R$26–34), materialmente acima do DDM ao vivo (~R$16), cumprindo a intenção do critério de aceite #1.
- **`ke_rim` (D-01)** — Ke estrutural = rf-ciclo + beta×erp_banco (0,045, sem prêmio small-cap), clampado a [0,11; 0,14] e nunca acima do Ke ao vivo; para beta 1,0 dá **0,14 < 0,165** (ke_live de banco).
- **Lucro normalizado (ENG-03)**, **DCF de crescimento (ENG-04)** e **NAV contábil (ENG-05)** — todos por composição de primitivas já testadas (`ddm.valor_gordon`, `ddm.ddm_dois_estagios`, `lentes.vpa`), never-raise.
- **13 goldens** novos verdes; suíte completa **400 passed**; `test_ddm.py` intocado (regressão-guarda do aceite #5).

## Task Commits

1. **Task 1: RIM (ENG-02) + Ke estrutural (D-01) + bloco config motores:** — `e7472eb` (feat)
2. **Task 2: Cíclica (ENG-03), Crescimento (ENG-04), NAV (ENG-05)** — co-committed em `e7472eb` (ver Deviations)
3. **Task 3: Golden puro por motor** — `9a1a0fc` (test)

_Nota: Tasks 1 e 2 são o mesmo módulo novo (`core/motores.py`) + o mesmo bloco config novo; escritos e commitados juntos no commit da Task 1 (a ação da Task 1 sancionava criar os 3 sub-blocos config ali)._

## Files Created/Modified
- `src/analista/core/motores.py` — 5 motores puros (rim/ke_rim/lucro_normalizado/dcf_crescimento/nav_contabil) + ResultadoRIM + MOTOR_ROTULO
- `config.yaml` — bloco novo `motores:` (rim: erp_banco/ke_piso/ke_teto/n_fade; ciclica: anos_media/winsor; crescimento: n_anos_explicito), aditivo
- `tests/test_motores.py` — golden puro por motor + casos never-raise

## Decisions Made
- **Número honesto vence o alvo aproximado (desvio aprovado no plano):** o "~R$40" de D-01 era alvo aproximado; o RIM conservador (Ke estrutural ~12,5% + fade do excesso a zero, sem prêmio terminal — D-02) rende ~R$28. Calibrado contra ~R$28, não ~R$40. O golden usa `valor_intrinseco >= 25` (não `> 2×16`), já que o modelo honesto não alcança R$32 sem violar D-02.
- **`ResultadoRIM` ganhou `peso_residual`** (init=False, `__post_init__`) espelhando `ResultadoDDM` — coerência de contrato entre motores.

## Deviations from Plan

### Estrutura de commit

**1. [Organização] Tasks 1 e 2 co-commitadas em `e7472eb`**
- **Found during:** Task 1 (escrita de `core/motores.py`)
- **Issue:** As 5 funções vivem no mesmo módulo novo; escrevi o arquivo inteiro de uma vez em vez de fatiar rim/ke_rim (Task 1) das outras 3 (Task 2). A ação da Task 1 explicitamente permitia "já criar os três sub-blocos config aqui — coordenar com Task 2".
- **Fix:** Task 2 ficou como verificação (funções presentes, `dcf` referencia `ddm.ddm_dois_estagios`, `nav` referencia `lentes.vpa`, config com os 3 sub-blocos) — todos os critérios de aceite da Task 2 confirmados sem novo diff.
- **Files modified:** src/analista/core/motores.py, config.yaml (ambos no commit da Task 1)
- **Verification:** `python -c "from analista.core import motores; assert all(hasattr(motores,n) for n in ('lucro_normalizado','dcf_crescimento','nav_contabil'))"` OK; goldens da Task 3 verdes.
- **Committed in:** e7472eb

---

**Total deviations:** 1 organizacional (agrupamento de commit, sancionado pela ação da Task 1). Nenhum desvio de escopo ou de comportamento.
**Impact on plan:** Nulo — todos os critérios de aceite das 3 tasks cumpridos; nenhum arquivo `core/` existente tocado; config puramente aditivo.

## Issues Encountered
Nenhum. A aritmética do RIM foi verificada por script antes de escrever o golden (R$28,20; RI terminal = 0; no-fade = R$34,15 = teto da faixa); `ke_rim` e `dcf_crescimento` idem.

## Verification
- `python -m pytest tests/test_motores.py tests/test_ddm.py -x` → 19 passed
- `python -m pytest` (suíte completa) → **400 passed**
- `git diff --name-only 2531656 HEAD` lista apenas `config.yaml`, `src/analista/core/motores.py`, `tests/test_motores.py` — `core/ddm.py`/`lentes.py`/`capm.py`/`normalizacao.py`/`fundamentals.py`/`report/selo.py` INTOCADOS
- `git diff config.yaml` sem deleções (bloco `motores:` puramente aditivo; capm/ddm/arquetipo intactos)

## Next Phase Readiness
- Os 5 motores estão prontos e golden-testados para o **Plan 02** apenas os **plugar no registry** e wirear no funil (`report.py` após a resolução do motor, `report.py:186`), sem regredir o ITUB4.
- **Atenção do Plan 02 (herdado do RESEARCH Pitfall 1):** ao trocar `ARQUETIPO_MOTOR[financeira]` de `None`→`"rim"`, migrar o predicado de suspensão de `motor is None` para `motor != "ddm"` em 3 superfícies (`report.py`, `cli.py`, goldens `test_arquetipo_roteamento`/`test_ranking_freio`) NO MESMO plano — senão o ITUB4 atravessa para o DDM e volta a "evitar".
- Firewall selo↛report preservado (nenhum toque em `selo.py`).

## Self-Check: PASSED

- FOUND: src/analista/core/motores.py
- FOUND: tests/test_motores.py
- FOUND: .planning/phases/02-motores-por-arqu-tipo/02-01-SUMMARY.md
- FOUND commit: e7472eb (Tasks 1+2)
- FOUND commit: 9a1a0fc (Task 3)

---
*Phase: 02-motores-por-arqu-tipo*
*Completed: 2026-07-11*
