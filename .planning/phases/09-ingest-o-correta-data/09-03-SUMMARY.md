---
phase: 09-ingest-o-correta-data
plan: 03
subsystem: ingest
tags: [split, bonificacao, prices, itub4, degrau, guarda-regressao, spike]

# Dependency graph
requires:
  - phase: 09-ingest-o-correta-data
    plan: 01
    provides: "c.dividendos amplo (JCP) + base do controlador (DATA-01/02) — não revertidos"
  - phase: 09-ingest-o-correta-data
    plan: 02
    provides: "num_acoes da contagem oficial da CVM por ano (DATA-03) — carrega a bonificação real uma vez"
provides:
  - "medição do onde-está-o-degrau-hoje: o double-count de split NÃO existe mais na série por-ação de valuation (ref prices.py:71-111 obsoleta; site real = _ajustar_por_split, prices.py:93-133)"
  - "guarda de regressão (3 asserts adimensionais) que fica vermelha se serie_precos regredir para o preço ajustado por split"
affects: [10-prim, valuation, indicadores]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Requisito com referência de linha obsoleta → spike de localização por MEDIÇÃO antes de qualquer edição (Pitfall 6)"
    - "Conserto que já foi entregue por refactors anteriores → o entregável é uma guarda de regressão RED-able, sem edição de produção"
    - "Guarda de split provada por execução (regressão simulada → 3 asserts vermelhos), não por suíte verde passiva"

key-files:
  created:
    - scripts/spike_data04_degrau_split.py
    - .planning/spikes/data-04-degrau-split.md
    - tests/test_ingest_split.py
  modified:
    - tests/classificacao.yaml
  deleted: []

key-decisions:
  - "DATA-04: o degrau artificial de ~13% do ITUB4 NÃO existe mais na série por-ação de valuation — medido, não suposto. Eliminado pelo firewall das Fases 3-4 (serie_precos = Close nominal; ajuste por split isolado em ohlc_ajustado, que nunca cruza num_acoes) + 09-02 (num_acoes = contagem oficial da CVM por ano, que carrega a bonificação real UMA vez)."
  - "Conserto = guarda de regressão, SEM edição de produção (o plano previu esse desfecho). Os dois ingredientes do double-count existem (num_acoes ×1,1311 real; Yahoo .splits 1,1×1,03=1,133) mas estão em trilhos separados que nunca se multiplicam."
  - "A ref do requisito prices.py:71-111 é obsoleta (hoje é o dataclass DadosMercado + _retornos_mensais); o site real do split é prices._ajustar_por_split (93-133)."

patterns-established:
  - "Quando um requisito de conserto aponta uma linha reescrita por fases anteriores, a task 1 é um SPIKE de localização (mede o estado atual) e a task 2 pode ser só a guarda que trava a ausência — o entregável muda de 'consertar' para 'provar que já está consertado e travar a regressão'."

requirements-completed: [DATA-04]

# Metrics
duration: 20min
completed: 2026-07-15
---

# Phase 09 Plan 03: Ingestão correta (DATA-04) Summary

**O "degrau artificial de ~13% do ITUB4" foi LOCALIZADO por medição e provado INEXISTENTE na série por-ação de valuation — a ref do requisito (`prices.py:71-111`) estava obsoleta, e o double-count já fora eliminado pelo firewall das Fases 3-4 (`serie_precos` nominal; ajuste de split confinado a `ohlc_ajustado`) somado ao 09-02 (`num_acoes` oficial por ano); entregue uma guarda de regressão de 3 asserts adimensionais, provada RED-able, sem tocar produção, knob ou config.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-07-15
- **Completed:** 2026-07-15
- **Tasks:** 2
- **Files:** 3 criados + 1 modificado

## Accomplishments

- **Task 1 (spike de localização):** `scripts/spike_data04_degrau_split.py` reconstrói a série por-ação do ITUB4 (2015–2025) sobre o estado JÁ consertado (pós-09-01/09-02) e mede a fronteira da bonificação. **Medido:** `num_acoes` 2024→2025 = **1,1311×** (a bonificação real ≈1,1286× — degrau LEGÍTIMO, aparece uma única vez, no ano do evento). O Yahoo `.splits` do ITUB4 registra a MESMA bonificação como `2025-03-18: 1,1` e `2025-12-26: 1,03` → produto **1,133** (o "~13%" do requisito). **Leitura estática (`grep src/`)** confirma o firewall: o único ajuste por split (`prices._ajustar_por_split`, `prices.py:93-133` — o site REAL, não a linha 71-111 do requisito) alimenta só `dm.ohlc_ajustado`, consumido por `report.py:682` (candle) e `intraday.py`/indicadores — **nunca cruzado com `num_acoes`**. `serie_precos` (valuation) = Close NOMINAL. Registrado em `.planning/spikes/data-04-degrau-split.md`.
- **Task 2 (guarda de regressão, sem produção):** `tests/test_ingest_split.py` (3 testes `invariante`) trava a ausência do degrau via razões **adimensionais** e ticker **sintético** (`BON3`, fora do `ticker_map.json` — BLIND-04a limpo): (1) `serie_precos` preserva a queda nominal na data da bonificação (razão ≈ 1/F < 1); (2) o produto `preço-nominal × num_acoes` atravessa a fronteira SEM salto (razão ≈ 1) — se `serie_precos` fosse o ajustado, saltaria ×F ≈ 1,13 (o degrau); (3) o ajuste por split fica confinado a `ohlc_ajustado`. **RED-able provado por execução:** aplicando a regressão simulada (`serie_precos = _ajustar_por_split(hist)["Close"]`), os **3 asserts ficam vermelhos**; restaurado o código, verdes. Entrada em `classificacao.yaml` no MESMO commit.
- **Suíte v2.4 verde:** default **462 passed, 1 skipped, 2 xfailed, 34 deselected, 0 failed**; `-m golden_nivel` **34 passed, 0 CLASSIFICACAO ORFA**; BLIND-04a passa (a guarda nova não é ofensor). **Zero mudança em `config.yaml`/`calibracao.lock.yaml`** (orçamento de 3 knobs intocado).

## Task Commits

1. **Task 1: spike DATA-04 — localiza (por medição) o degrau de split do ITUB4** — `d52851d` (feat)
2. **Task 2: trava a ausência do degrau de split do ITUB4 (DATA-04) + classificação** — `8b7bc92` (test)

## Files Created/Modified

- `scripts/spike_data04_degrau_split.py` — diagnóstico offline (cache CVM): série por-ação, razão de bonificação, firewall dos consumidores de séries ajustadas por split.
- `.planning/spikes/data-04-degrau-split.md` — o veredito medido (site real, ingredientes, firewall, consequência para a Task 2).
- `tests/test_ingest_split.py` — 3 guardas `invariante` de regressão do double-count de split (adimensionais, ticker sintético).
- `tests/classificacao.yaml` — 3 entradas novas (coleta completa; 0 órfão).

## Decisions Made

- **Medir antes de editar (Pitfall 6).** A ref do requisito (`prices.py:71-111`) foi reescrita nas Fases 3-4; escrever a task de conserto sobre ela não endereçaria nada. O spike substituiu a suposição pela medição.
- **O entregável mudou de "consertar" para "provar que já está consertado + travar a regressão".** O plano previu explicitamente esse desfecho ("Se o spike concluir que o degrau já não existe: o teste apenas TRAVA essa ausência, sem edição de produção").
- **Guarda provada por execução, não por suíte verde passiva** (lição do CLAUDE.md/MEMORY: "guarda só vale se for provada por execução"). A regressão simulada foi rodada e produziu 3 asserts vermelhos.

## Deviations from Plan

None — plano executado exatamente como escrito. A Task 2 caiu no ramo previsto pelo próprio plano (degrau já inexistente → guarda de regressão sem edição de produção). Nenhum arquivo fora do `files_modified` declarado foi tocado; nenhum checkpoint de decisão necessário (diferente de 09-01/09-02, nenhum teste diagnóstico existente foi invalidado — a mudança é aditiva).

## Issues Encountered

Nenhum. O `composicao_capital` não existe para ITUB4 antes de 2020 (LPA_cru None em 2015-2019 no spike) — irrelevante para a medição da fronteira 2024→2025, que é onde a bonificação vive.

## Known Stubs

Nenhum. A guarda exercita o pipeline real (`prices.coletar_mercado` com yfinance mockado) e séries construídas, não valores placeholder.

## Threat Flags

Nenhuma superfície nova. T-09-07 (double-count split × num_acoes) — disposição `mitigate` — endereçado: medido inexistente e travado por guarda de regressão RED-able. T-09-08 (Yahoo 404 / série vazia) segue `accept` (never-raise em `prices.py`).

## Next Phase Readiness

- DATA-05 (base do DY — declarar bruto) segue no plano 09-04; DATA-06 (snapshot limpo + monotonicidade) no 09-05.
- O firewall split↛valuation está agora travado por teste: a Fase 10 (PRIM) pode mexer em primitivas sem reintroduzir o double-count sem a suíte avisar.

## Self-Check: PASSED

- `.planning/spikes/data-04-degrau-split.md` — FOUND
- `scripts/spike_data04_degrau_split.py` — FOUND
- `tests/test_ingest_split.py` — FOUND
- `d52851d` (Task 1) — FOUND
- `8b7bc92` (Task 2) — FOUND
- classificacao.yaml: 3 entradas novas, 0 órfão (`-m golden_nivel` sem CLASSIFICACAO ORFA)

---
*Phase: 09-ingest-o-correta-data*
*Completed: 2026-07-15*
