---
phase: quick-260620-oa9
plan: 01
subsystem: comparables-ui
tags: [ui, transparencia, regressao, ranking, tela-2]
requires: [src/analista/core/comparables.py RegressaoPL]
provides:
  - "RegressaoPL.amostra_pequena / RegressaoPL.roe_sinal_invertido (flags de diagnóstico)"
  - "Tela 2 (Ranking): 3 avisos de confiabilidade (amostra pequena, ROE invertido, mesmo setor)"
affects: [app.py Tela 2 Ranking]
tech-stack:
  added: []
  patterns: ["@property derivada em dataclass (sem campos posicionais novos)"]
key-files:
  created: []
  modified:
    - src/analista/core/comparables.py
    - tests/test_comparables.py
    - app.py
decisions:
  - "LIMIAR_AMOSTRA=10: abaixo disso, 3 params sobre poucas obs deixa a regressão instável"
  - "Flags como @property (não campos do dataclass) p/ não quebrar as 5 construções posicionais (4 golden + 1 engine)"
  - "RANK-CONF-02 liga o caso TAEE11 ao Core Value: ROE invertido → preferir DDM, explicando a divergência de menus"
metrics:
  duration: 6
  completed: 2026-06-20
  tasks: 2
  files: 3
---

# Quick 260620-oa9: Ajustar Tela 2 (Ranking por múltiplos) com avisos de confiabilidade — Summary

Avisos aditivos na Tela 2 do Analista de Dividendos que tornam transparente quando o veredito da
regressão P/L = f(payout, ROE) é estatisticamente frágil — sem mudar nenhum cálculo de valuation
nem a lógica da regressão.

## O que foi feito

**Task 1 — flags de diagnóstico em RegressaoPL** (commit `41fda00`)
- Constante de módulo `LIMIAR_AMOSTRA = 10` em `comparables.py`.
- `@property amostra_pequena` → `self.n < LIMIAR_AMOSTRA`.
- `@property roe_sinal_invertido` → `float(self.coeficientes[2]) < 0` (b_ROE negativo contraria Gordon).
- Propriedades derivadas, sem novos campos posicionais — as 5 construções existentes seguem intactas.
- 2 testes novos em `tests/test_comparables.py` (amostra_pequena n=6/n=10; roe_sinal_invertido neg/pos/zero).

**Task 2 — avisos na Tela 2 (Ranking)** (commit `0e573da`)
- RANK-CONF-01: `st.warning` de amostra pequena (mostra `reg.n`) quando `reg.amostra_pequena`.
- RANK-CONF-02: `st.warning` de ROE com coeficiente negativo quando `reg.roe_sinal_invertido`, explicando
  a divergência com o "Analisar a fundo" (DDM) e orientando a confiar mais no DDM — liga o caso TAEE11
  ao Core Value.
- RANK-CONF-03: `st.caption` fixo orientando comparar empresas do mesmo segmento.
- Inseridos logo após o `st.caption` da fórmula da regressão; tabela, preços-alvo e o ramo `else` (poucas empresas <4) inalterados.

## Verification

- `pytest tests/ -q` → **49 passed** (golden intactos, incluindo os 7 golden de test_comparables + 2 novos).
- `ast.parse(open('app.py'))` → OK.
- Gates `grep amostra_pequena` / `grep roe_sinal_invertido` em app.py → OK.

## Deviations from Plan

None - plano executado exatamente como escrito.

Observação: o plano cita "9 testes golden" em test_comparables.py; o arquivo tinha 7 funções de teste
(todas preservadas sem alteração). Os 2 testes novos foram adicionados sem tocar nos existentes.

## Known Stubs

None.

## Status

Tasks 1 e 2 concluídas e commitadas atomicamente. **Task 3 é um checkpoint:human-verify (gate
blocking)** — a execução parou aqui aguardando verificação humana via `streamlit run app.py`.

## Self-Check: PASSED

- src/analista/core/comparables.py — FOUND (modificado, contém `def amostra_pequena`)
- app.py — FOUND (modificado, contém `amostra_pequena` e `roe_sinal_invertido`)
- tests/test_comparables.py — FOUND (modificado, +2 testes)
- Commit 41fda00 — FOUND
- Commit 0e573da — FOUND
