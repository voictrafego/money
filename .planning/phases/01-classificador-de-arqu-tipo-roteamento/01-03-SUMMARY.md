---
phase: 01-classificador-de-arqu-tipo-roteamento
plan: 03
subsystem: core/valuation-routing
tags: [arquetipo, ciclicidade, detrend, gap-closure, tdd, CR-01]
gap_closure: true
requires:
  - "core/arquetipo._cv_lucro — sinal de oscilação consumido por classificar()"
  - "CompanyData.serie('lucro_liquido') — série de lucro (fonte CVM cacheada)"
provides:
  - "core/arquetipo._cv_lucro — CV da oscilação DETRENDED (retornos ano-a-ano), invariante à tendência"
  - "config.yaml arquetipo.ciclica_cv_min recalibrado (0.40->0.50) para a escala da nova métrica"
  - "tests/test_arquetipo.test_compounder_realista_wege_vira_crescimento — golden anti-regressão >=18%/ano"
affects:
  - "Fecha Gap 1 (BLOCKER, SC#1 / CR-01) da 01-VERIFICATION.md — WEGE3 deixa de misroutar para cíclica"
  - "ARQ-01 (refino quantitativo compounder vs. cíclica) passa a satisfazer a metade quebrada"
tech-stack:
  added: []
  patterns:
    - "detrend antes de medir oscilação — CV dos retornos ano-a-ano em vez do nível bruto"
    - "guards None preservados (< 3 pontos, < 2 retornos, média 0) — função pura sem I/O"
key-files:
  created: []
  modified:
    - tests/test_arquetipo.py
    - src/analista/core/arquetipo.py
    - config.yaml
decisions:
  - "Sinal de ciclicidade = CV dos retornos ano-a-ano (detrended), não CV do nível bruto (dominado pela tendência)"
  - "ciclica_cv_min 0.40->0.50: compounder monotônico ~0.00-0.01, cíclico que alterna sinal >1.3 — corte com folga entre regimes"
  - "Fix é no SINAL, não no desempate distintos[0]: WEGE3-like produz candidato único crescimento (cv abaixo do corte)"
metrics:
  duration: "~0h20m"
  completed: "2026-07-11"
  tasks: 2
  tests_added: 1
  suite: "355 passed (baseline 354 + 1 novo golden)"
---

# Phase 1 Plan 03: Detrend do sinal de ciclicidade (Gap 1 / CR-01) Summary

Fecha o BLOCKER da 01-VERIFICATION.md (SC#1 / CR-01): `_cv_lucro()` media o coeficiente de
variação do NÍVEL BRUTO da série de lucro, dominado pela tendência de crescimento — qualquer
compounder real (WEGE3: ROE≈25.8%, CV cru≈0.46) estourava `ciclica_cv_min` e caía em `ciclica`
fronteiriço em vez de `crescimento`. A correção mede a oscilação DETRENDED (CV dos retornos
ano-a-ano), invariante à tendência: compounder monotônico pontua ~0.001, cíclico que alterna
sinal pontua >1.3.

## What Was Built

- **`tests/test_arquetipo.py` — golden anti-regressão** (`test_compounder_realista_wege_vira_crescimento`):
  réplica WEGE3-shape com o helper `_empresa` existente — `lucros = [round(1000 * (1.18 ** i)) for i in range(10)]`
  (18%/ano composto, monotônico), `payout=0.20` (retenção 0.80 >= 0.50), `pl=15000` calibrado
  para `roe_valuation()≈0.251` (WEGE3 real ≈0.258), setor não-financeiro/não-concessionário
  ("Máquinas e Equipamentos"). Afirma `chave == CRESCIMENTO`, `fronteirico is False`,
  `CICLICA not in candidatos`. O golden de 3%/ano intocado (mascarava o defeito com CV≈0.08).
- **`src/analista/core/arquetipo.py::_cv_lucro`** — reescrito para medir a dispersão dos
  RETORNOS ano-a-ano `(lucro[t]-lucro[t-1])/|lucro[t-1]|` (pula `lucro[t-1]==0`) e retornar
  `pstdev(ret)/abs(mean(ret))`. Guards preservados: `None` se < 3 pontos, < 2 retornos válidos,
  ou média dos retornos == 0. Função pura, O(n) sobre <=10 pontos, sem I/O. Docstring atualizado
  (não afirma mais "lucro CRU") + comentário da árvore em `classificar()` alinhado.
- **`config.yaml` bloco `arquetipo:`** — `ciclica_cv_min` recalibrado `0.40 -> 0.50` com
  comentário inline descrevendo a nova escala (compounder ~0.00-0.01 vs. cíclico >1.3).

## Task Commits

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 (RED) | golden que reproduz o misroute do WEGE3 | cd31e52 | tests/test_arquetipo.py |
| 2 (GREEN) | detrend em _cv_lucro + recalibrar o corte | 413927d | src/analista/core/arquetipo.py, config.yaml |

## Verification

- `python -m pytest tests/test_arquetipo.py tests/test_arquetipo_roteamento.py -q` → 17 passed.
- `python -m pytest -q` → **355 passed** (baseline 354 + o novo golden), 0 failed.
- RED confirmado antes do fix: `chave='ciclica'` (fronteiriço) → após o fix `chave='crescimento'`.
- Cíclica genuína (`test_lucro_oscilante_vira_ciclica`, detrend_cv≈1.39) e conflito real
  (`test_conflito_de_sinais_marca_fronteirico`, detrend_cv≈1.67) continuam detectados.
- Degradação sob sinais None (`test_sinais_none_degrada_sem_typeerror`) verde (guards preservados).
- `git diff --name-only` limitado a tests/test_arquetipo.py, src/analista/core/arquetipo.py,
  config.yaml. `src/analista/core/ddm.py` e `src/analista/report/selo.py` intocados.

## Separação dos regimes (evidência do fix)

| Fixture | forma | detrend_cv | rota |
|---------|-------|-----------|------|
| WEGE3-like (18%/ano) | compounder monotônico | 0.0013 | crescimento ✓ |
| GROW3 (3%/ano) | compounder lento | 0.0087 | crescimento ✓ |
| CICL3 oscilante | cíclico alterna sinal | 1.386 | ciclica ✓ |
| FRON3 conflito | oscila + últimos anos altos | 1.669 | fronteiriço ✓ |

O corte `0.50` senta com folga (>2.7x) entre os dois regimes.

## Deviations from Plan

None — plano executado exatamente como escrito. REFACTOR não necessário (código limpo na
primeira passada da fase GREEN).

## Threat Model Compliance

- **T-01-03-01 (config `ciclica_cv_min`):** accept — recalibração local de threshold, sem PII,
  sem borda de rede; superfície mínima documentada honestamente.
- **T-01-03-02 (DoS em `_cv_lucro`):** mitigado — O(n) sobre <=10 pontos, guards `None` para
  < 3 pontos / < 2 retornos / divisão por zero preservados; sem loop não-limitado nem recursão.

Nenhuma nova superfície de ameaça (endpoint/auth/arquivo/schema) introduzida — refactor de
função pura + valor de config.

## Known Stubs

Nenhum. O fix wire dados reais (série de lucro CVM já ingerida) por um sinal correto.

## TDD Gate Compliance

- RED: `test(01-03)` cd31e52 — golden falhando (`chave='ciclica' != 'crescimento'`), reproduz Gap 1.
- GREEN: `feat(01-03)` 413927d — detrend + recalibração; 355/355 verdes.
- REFACTOR: não necessário.

## Self-Check: PASSED

- Arquivos: tests/test_arquetipo.py, src/analista/core/arquetipo.py, config.yaml — todos FOUND.
- Commits: cd31e52, 413927d — ambos FOUND no git log.
