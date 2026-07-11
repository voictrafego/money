---
phase: 01-classificador-de-arqu-tipo-roteamento
plan: 07
subsystem: report
tags: [ddm, guardrail, valuation, streamlit, veredito, coerencia]

# Dependency graph
requires:
  - phase: 01-classificador-de-arqu-tipo-roteamento (01-02)
    provides: funil analisar_acao com vmin/vmax da matriz de sensibilidade + suspensão D-04 por motor_pendente
provides:
  - Guarda-corpo de emissão do DDM (_guarda_faixa_ddm): faixa negativa (vmax<=0) ou degenerada (0-0) nunca é emitida como intrínseco
  - Campo AnaliseAcao.ddm_inaplicavel (aditivo, read-only sobre o veredito)
  - Exibição honesta de inaplicabilidade no relatório markdown e na UI Streamlit
affects: [fase-3-veredito-honesto, ensemble-divergencia, ranking-freio-arquetipo]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guarda-corpo puro na borda de emissão (report.py) sem tocar as fórmulas (core/ddm.py)"
    - "Supressão via zeragem de vmin/vmax -> None reusa o ramo condicional 'não disponível' existente"

key-files:
  created:
    - tests/test_guardrails_ddm.py
  modified:
    - src/analista/report/report.py
    - app.py

key-decisions:
  - "A faixa DDM só dispara supressão quando o TETO é inválido (vmax<=0) ou 0-0; vmin<0 com vmax>0 (faixa cruza zero, teto positivo) preserva a faixa — o teto ainda carrega informação"
  - "Supressão marca ddm_inaplicavel e zera vmin/vmax -> None, reusando o caminho 'não disponível' já existente na métrica/tabela em vez de criar um novo ramo de veredito"
  - "Nota de 'inaplicável' é distinta de '_DDM não calculado_' (faltou insumo) — o usuário sabe que o DDM rodou mas não serve ao perfil"

patterns-established:
  - "Guarda-corpo read-only na borda de saída: engine->UI/relatório suprime output inválido sem alterar fórmula nem veredito primário"

requirements-completed: [SAN-01]

# Metrics
duration: 20min
completed: 2026-07-11
---

# Phase 01 Plan 07: Guarda-corpo do DDM (Achado 2) Summary

**Faixa intrínseca do DDM negativa (HAPV3 −2,20/−1,66; PCAR3 −7,67/−5,95) ou degenerada (PRIO3 0–0) nunca mais é emitida/exibida como preço-alvo — suprimida na borda com sinalização honesta de inaplicabilidade, sem tocar core/ddm.py nem o firewall selo↛report.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-11
- **Tasks:** 2
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments
- `_guarda_faixa_ddm` — guarda-corpo puro na borda de emissão de `analisar_acao`: `vmax<=0` OU `vmin==0 and vmax==0` → `ddm_inaplicavel=True`, `vmin/vmax=None`, alerta honesto.
- Fecha o Achado 2 da 01-AUDIT-COERENCIA.md: os casos reais degenerados (HAPV3/PCAR3 negativos, PRIO3 zero) deixam de aparecer na seção DDM do relatório/UI.
- Relatório markdown e UI Streamlit exibem nota honesta de "DDM estruturalmente inaplicável" (distinta de "DDM não calculado") em vez de faixa negativa/zero.
- Casos válidos positivos (TAEE11 29–47, EGIE3, SBSP3) seguem exibindo a faixa e o veredito idênticos — travado por golden inverso.
- `core/ddm.py` e `selo.py` provados intocados (`git diff --stat` vazio); firewall selo↛report preservado; nenhuma dependência nova.

## Task Commits

1. **Task 1 (RED): goldens do guarda-corpo** — `48a7a4c` (test)
2. **Task 1 (GREEN): supressão na borda de emissão + nota no markdown** — `ea96878` (feat)
3. **Task 2: nota honesta de inaplicabilidade na UI Streamlit** — `b51bfb6` (feat)

_Nota: a nota de markdown (report.relatorio_markdown), formalmente pertencente à Task 2, foi implementada junto do GREEN da Task 1 (ea96878) porque os goldens de render da Task 1 já a exercitavam — coeso, mesmo arquivo report.py._

## Files Created/Modified
- `tests/test_guardrails_ddm.py` - 7 goldens: 3 casos degenerados (HAPV3/PCAR3/PRIO3), 2 guard-rail inverso (TAEE11 positivo + faixa que cruza zero), 2 render markdown (inaplicável sem R$ negativo / válido mantém tabela).
- `src/analista/report/report.py` - `_guarda_faixa_ddm` (pura), campo `AnaliseAcao.ddm_inaplicavel`, chamada do guard após vmin/vmax e antes do veredito, ramo de nota honesta na seção DDM do `relatorio_markdown`.
- `app.py` - `st.caption` de inaplicabilidade quando `a.ddm_inaplicavel` (métrica "Intrínseco (DDM)" já cai em "—" via vmin/vmax None).

## Decisions Made
- **Só `vmax<=0` ou `0-0` disparam a supressão.** Faixa com `vmin<0` mas `vmax>0` (cruza zero, teto positivo) é preservada — o teto ainda carrega informação; suprimir seria falso-positivo (T-0107-03).
- **Supressão por zeragem de vmin/vmax → None**, reusando o ramo `elif a.vmin is not None ...` existente, em vez de criar novo ramo de veredito. Read-only sobre o veredito primário (os casos observados já são motor_pendente/VERIFICAR).
- **Mensagem "inaplicável" ≠ "não calculado".** O usuário distingue "o DDM rodou mas não serve a este perfil" de "faltou Beta/payout/g".

## Deviations from Plan

None - plan executed exactly as written. A nota de markdown da Task 2 foi antecipada para o commit GREEN da Task 1 por coesão de arquivo (ambos em report.py e exercitados pelos mesmos goldens); nenhum trabalho fora de escopo.

## Issues Encountered
None.

## Threat Model Compliance
- **T-0107-01 (Tampering):** faixa degenerada apresentada como preço-alvo → mitigada por supressão na emissão + goldens que travam os casos.
- **T-0107-02 (Repudiation):** número negativo confunde origem → mitigada por sinalização explícita de inaplicabilidade (markdown + UI).
- **T-0107-03 (DoS):** guard derruba caso válido por engano → mitigada por guard estrito (`vmax<=0`/`0-0`) + golden inverso TAEE11 + caso "cruza zero" preservado.

## Known Stubs
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Achado 2 fechado. Restam para a Fase 3: freio de arquétipo no modo Ranking (Achado 3), reconciliação/ensemble de divergência entre lentes (Achado 4) e normalização de lucro no pico do ciclo (PETR4 56–91, faixa POSITIVA — fora deste guarda-corpo, pertence à Fase 2).
- Suíte verde: 372 passed (365 baseline + 7 novos). Nenhuma dependência nova.

---
*Phase: 01-classificador-de-arqu-tipo-roteamento*
*Completed: 2026-07-11*
