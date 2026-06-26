---
phase: 04-encanamento-de-dados-s-rie-correta
plan: 02
subsystem: ingest
tags: [ohlc, split-adjustment, validation, test, itsa4]
requires:
  - "prices._ajustar_por_split (04-01)"
  - "DadosMercado.ohlc / .ohlc_ajustado (04-01)"
  - "CompanyData.ohlc / .ohlc_ajustado (04-01)"
provides:
  - "Validação multi-split estilo ITSA4 (5 eventos, offline) — sem saltos espúrios"
  - "Confirmação do invariante TEST-07 (64+ golden tests verdes após o encanamento)"
  - "Validação de rede real ITSA4 confirmada por checkpoint humano (critério de aceite #2)"
affects:
  - "Phase 5 (TEST-05 reusa o padrão de fixture split-adjusted para os golden de indicadores)"
tech-stack:
  added: []
  patterns:
    - "fixture multi-split construída por inversão: nominal = caminho_continuo × fator_cumulativo"
    - "asserção de continuidade no evento (razão ajustado ≈ 1 vs. degrau no nominal)"
key-files:
  created: []
  modified:
    - tests/test_ingest_ohlc.py
decisions:
  - "fixture ITSA4 construída a partir de um caminho A contínuo escalado pelo fator cumulativo — a função deve RECUPERAR A (prova de ausência de salto), não só não-estourar"
  - "validação de rede real do ITSA4 fica no checkpoint humano (Task 2), nunca nos testes (zero rede)"
  - "import correto é analista.ingest (não src.analista.ingest) — pacote instalado na .venv"
metrics:
  duration: "~10 min"
  completed: "2026-06-26"
  tasks: 2
  files_changed: 1
---

# Phase 4 Plan 02: Validação multi-split ITSA4 + invariante TEST-07 Summary

Prova de que o ajuste por split de 04-01 está correto sob estresse de 5 eventos (estilo ITSA4, D-08): 3 testes offline novos demonstram que a série ajustada recupera um caminho contínuo sem saltos/cruzamentos espúrios nas 5 datas de split, com a ponta recente == nominal; e a suíte completa segue verde (TEST-07), com a validação de rede real do ITSA4 confirmada por checkpoint humano (critério de aceite #2).

## What Was Built

- **`tests/test_ingest_ohlc.py` (+110 linhas, 3 testes novos + fixture)** — nova seção "Validação multi-split estilo ITSA4 (D-08)":
  - **`_hist_itsa4_multisplit()`** — fixture offline com 5 eventos de split em ~5 anos de pregões diários (datas espelhando os eventos reais do ITSA4: dez/2021, nov/2022, nov/2023, dez/2024, dez/2025). Construída por inversão: parte de um caminho econômico **contínuo** `A` (a série split-adjusted "verdadeira", suave/crescente R$5→R$12) e multiplica pelo fator de split **cumulativo** (produto dos splits estritamente posteriores a cada data) para obter o Close **nominal** cheio de degraus — exatamente a relação dos dados crus do Yahoo (`auto_adjust=False`) com a série split-adjusted. Volume nominal inverso; `Adj Close` presente mas nunca usado como base.
  - **`test_itsa4_5_splits_ponta_recente_coincide_com_nominal`** — após o último split (dez/2025) o fator cumulativo = 1 → cauda do ajustado == nominal == `A`.
  - **`test_itsa4_5_splits_serie_ajustada_continua_sem_saltos`** — (1) o ajustado reconstrói o caminho contínuo `A` em toda a janela; (2) em cada uma das 5 datas de split a razão nominal cai (degrau ~1/fator, < 0.97) enquanto a razão ajustada permanece contínua (|razão − 1| < 0.01) — sem cruzamento espúrio.
  - **`test_itsa4_fator_cumulativo_pre_primeiro_split`** — datas anteriores ao 1º split são escaladas pelo produto dos 5 fatores → ajustado = nominal / produto; o Close ajustado mais antigo é estritamente menor que o nominal e o volume ajustado é maior (sentido inverso).

## Task Commits

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 | Teste de validação multi-split estilo ITSA4 (offline) + suíte golden verde | `7cbbef0` |
| 2 | Validação de rede real no ITSA4 (checkpoint:human-verify, gate=blocking) | aprovado pelo humano (sem commit de código) |

## Verification

- `.venv/bin/pytest tests/ -q` → **77 passed** (era 74; exatamente +3 testes novos, zero regressão).
- Subconjunto golden de valuation `.venv/bin/pytest tests/test_ddm.py tests/test_multiples.py tests/test_screening.py tests/test_comparables.py tests/test_fundamentals_consistencia.py tests/test_consistencia_modos.py -q` → exit 0 (49 passed). **TEST-07 preservado** — nenhuma fórmula do livro alterada (fase aditiva).
- **Checkpoint Task 2 (validação de rede real ITSA4)** — APROVADO pelo humano. Critérios confirmados pelo orquestrador:
  - `dm.ohlc` com colunas OHLCV completas (Open/High/Low/Close/Adj Close/Volume/Dividends/Stock Splits); `dm.ohlc_ajustado` ≠ None.
  - Ponta recente: ajustado == nominal (13.52 == 13.52, fator cumulativo = 1 após o último split).
  - Close mais antigo: nominal 8.6712 → ajustado 6.6760 (< nominal, escalado pelo produto dos 5 fatores).
  - 5 eventos detectados (2021-12-21, 2022-11-11, 2023-11-28, 2024-12-03, 2025-12-19), produto ≈ 1.2989, confere 8.6712/1.2989 = 6.676.
  - Controle TAEE4 (0 splits): ajustado == nominal.

## Deviations from Plan

Nenhuma deviation funcional. Nota: a one-liner de verificação do plano usava `from src.analista.ingest import prices`; o import correto (pacote instalado na `.venv`, idêntico ao usado pela suíte) é `from analista.ingest import prices`. Comunicado ao humano junto do comando do checkpoint.

## Known Stubs

Nenhum. Plano só adiciona testes offline; nenhum código de produção foi tocado nesta entrega.

## Self-Check: PASSED

- FOUND: tests/test_ingest_ohlc.py (3 testes ITSA4 novos)
- FOUND: commit 7cbbef0 (test 04-02 validação multi-split ITSA4)
- FOUND: 77 passed na suíte completa; golden subset exit 0 (49 passed)
- CONFIRMED: checkpoint Task 2 aprovado pelo humano (validação de rede real ITSA4)
