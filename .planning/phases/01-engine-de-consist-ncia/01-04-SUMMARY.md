---
phase: 01-engine-de-consist-ncia
plan: 04
subsystem: engine
tags: [valuation, ddm, payout, valor-intrinseco, report]

# Dependency graph
requires:
  - phase: 01-engine-de-consist-ncia (Plano 01)
    provides: "CompanyData.payout_valuation() (média 3a + clamp 1.0) — consumida pelo DDM do Analisar"
provides:
  - "DDM do Analisar usa a função canônica de payout (payout_valuation), compartilhada com o Ranking — já entregue por 01-01"
  - "AnaliseAcao.vmin/vmax: intervalo de valor intrínseco calculado uma única vez no veredito e exposto para a UI reusar (sem recomputar min/max)"
affects: [analisar, fase-2-apresentacao, app-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cálculo de agregação/intervalo feito UMA vez na engine e exposto no dataclass; UI lê o campo em vez de recomputar (anti-duplicação WR-07)"

key-files:
  created: []
  modified:
    - src/analista/report/report.py

key-decisions:
  - "vmin/vmax do veredito viram campos de AnaliseAcao (Optional[float], default None); o texto do veredito passa a usar a.vmin/a.vmax — texto e campos vêm da MESMA fonte"
  - "vmin/vmax são preenchidos sempre que há DDM (mesmo sem preço_atual); o veredito textual continua exigindo preço_atual"

patterns-established:
  - "AnaliseAcao.vmin/vmax: intervalo intrínseco da fonte única, consumível pela UI (Plano 05) sem recálculo"

requirements-completed: [PAYOUT-01, VAL-01]

# Metrics
duration: 6min
completed: 2026-06-05
---

# Phase 01 Plan 04: Alinhar Analisar à fonte canônica e expor intervalo intrínseco Summary

**Expôs `vmin`/`vmax` em `AnaliseAcao` a partir do cálculo único do veredito (eliminando a duplicação UI×report — WR-07/VAL-01); a parte de payout canônico do DDM (PAYOUT-01/CR-02/WR-03) já havia sido entregue por 01-01 e foi verificada como satisfeita.**

## Performance

- **Duration:** ~6 min
- **Tasks:** 2 (Task 1 já satisfeita por 01-01; Task 2 implementada)
- **Files modified:** 1

## Accomplishments
- Task 1 (DDM usa payout canônico) confirmada como já entregue por 01-01: `report.analisar_acao` já consome `c.payout_valuation()` e o `_media_payout_3a` já não existe em report.py — verificado pelos smokes do plano (sem edição/commit duplicado).
- Task 2: `AnaliseAcao` ganhou `vmin`/`vmax` (`Optional[float]`, default None); o intervalo intrínseco é calculado uma única vez no bloco do veredito e o texto do veredito passou a usar `a.vmin`/`a.vmax` — texto e campos compartilham a mesma fonte. A UI (Plano 05) poderá ler `a.vmin`/`a.vmax` em vez de recomputar `min/max` em app.py (linhas 107-108).

## Task Commits

1. **Task 1: DDM usa payout canônico** — sem commit (já satisfeita por 01-01, commit `e475470`); verificada pelos smokes automatizados do plano.
2. **Task 2: expor vmin/vmax no AnaliseAcao** — `534430e` (feat)

## Files Created/Modified
- `src/analista/report/report.py` — adicionados campos `vmin`/`vmax` ao dataclass `AnaliseAcao`; bloco do veredito atribui `a.vmin`/`a.vmax` do `min/max` único e usa esses campos na formatação do texto.

## Decisions Made
- vmin/vmax passam a ser campos de AnaliseAcao alimentados pela computação única do veredito; o texto do veredito agora lê os campos (`a.vmin`/`a.vmax`), garantindo que UI, campos e texto nunca divirjam.
- vmin/vmax são populados sempre que há DDM (independe de preço_atual), refletindo a `<behavior>` do plano ("quando há DDM, vmin/vmax são o min/max").

## Deviations from Plan

### Task 1 já entregue por 01-01 (Rule 2 — evitar duplicação)
- **Contexto:** O objetivo do executor sinalizou que 01-01 já trocara `report.analisar_acao` para `c.payout_valuation()` e removera o `_media_payout_3a` local. Verificação confirmou: `payout_valuation` presente em report.py, `_media_payout_3a` ausente (sobra apenas como palavra em docstring de `fundamentals.py`, não como identificador em report.py).
- **Ação:** Não duplicar a Task 1. Rodados os smokes automatizados da Task 1 do plano (passaram) e seguido direto para a Task 2. Nenhum commit gerado para a Task 1.
- **Impacto:** Nenhum scope creep; o requisito PAYOUT-01 (parte engine) permanece satisfeito pela entrega de 01-01.

### Ajuste em relação ao texto literal da Task 2
- No plano o `vmin/vmax` eram calculados dentro do `if valores and a.preco_atual`. A `<behavior>` exige que com DDM presente vmin/vmax sejam preenchidos. Movi a atribuição de `a.vmin/a.vmax` para um `if valores:` (antes da checagem de preço), de modo que o intervalo fique exposto mesmo quando o preço atual está ausente; o veredito textual continua sob `if valores and a.preco_atual`. Alinha campos com a behavior sem mudar a semântica do texto.

---

**Total deviations:** 1 task já entregue (verificada, não duplicada) + 1 ajuste de posicionamento alinhado à behavior.
**Impact on plan:** Sem scope creep. Fórmulas de valuation intactas (constraint respeitada).

## Issues Encountered
None.

## Verification

- Smoke Task 1: `payout_valuation` em uso e `_media_payout_3a` ausente de report.py → ok.
- Smoke Task 2: `AnaliseAcao(...).vmin/vmax` existem e default None → ok.
- `pytest tests/ -q` → **44 passed** (golden de ddm/multiples/comparables/screening + consistência intactos).

## Next Phase Readiness
- Plano 05 (UI) pode ler `a.vmin`/`a.vmax` diretamente e remover o recálculo `min/max` em app.py (107-108), fechando WR-07/VAL-01 na apresentação.

## Self-Check: PASSED
- FOUND: src/analista/report/report.py (vmin/vmax em AnaliseAcao + uso no veredito)
- FOUND: commit 534430e
- pytest: 44 passed

---
*Phase: 01-engine-de-consist-ncia*
*Completed: 2026-06-05*
