---
phase: 01-classificador-de-arqu-tipo-roteamento
plan: 05
subsystem: classificador-de-arquetipo
tags: [arquetipo, ciclicidade, calibracao, tdd, gap-closure]
requires: [ARQ-01, ARQ-02]
provides:
  - "sinal de ciclicidade robusto a variância de TAXA de crescimento (resíduos log-lineares)"
  - "ciclica_cv_min recalibrado (0.35) validado contra >=3 compounders + >=4 cíclicas reais"
  - "goldens de séries CVM REAIS anti-regressão (compounders e cíclicas)"
affects:
  - "Fase 2 SC#3: WEGE3 (crescimento) → DCF multi-estágio agora tem a pré-condição satisfeita"
tech-stack:
  added: []
  patterns:
    - "ajuste OLS de ln(lucro) ~ tempo + pstdev dos resíduos como sinal de desvio-de-tendência"
    - "override de prejuízo precede o guard de degradação (<3 pontos)"
    - "fixtures congeladas com séries CVM reais (cd_cvm citado), nunca progressão geométrica"
key-files:
  created: []
  modified:
    - src/analista/core/arquetipo.py
    - config.yaml
    - tests/test_arquetipo.py
decisions:
  - "Sinal de ciclicidade = dispersão dos resíduos de ajuste log-linear do lucro (não CV dos retornos ano-a-ano) — só mede desvio de tendência, não penaliza crescimento desigual de compounders reais (fecha CR-01/Gap 1)."
  - "Ano de prejuízo (log indefinido) = evidência cíclica forte: override devolve sinal-sentinela acima do corte e PRECEDE o guard de <3 pontos (W2)."
  - "ciclica_cv_min recalibrado 0.50 → 0.35 com folga (W1): acima dos compounders reais (<=0.22), abaixo das cíclicas reais (>=0.49); NÃO fixado na borda de VALE3 (0.49)."
metrics:
  duration: 0h25m
  tasks: 2
  files: 3
  completed: 2026-07-11
---

# Phase 1 Plan 05: Sinal de Ciclicidade por Resíduos Log-Lineares (GAP CLOSURE — Achado 1a) Summary

Substituiu o sinal de ciclicidade `_cv_lucro` (CV dos retornos ano-a-ano) pela **dispersão dos
resíduos de um ajuste log-linear** do lucro, recalibrou `ciclica_cv_min` para 0.35 com margem, e
travou a correção com goldens de **séries CVM reais** — fechando o BLOCKER que misrouteava
compounders reais de crescimento desigual (WEGE3, RADL3) para `ciclica`/fronteiriço.

## O que mudou

**Causa raiz (Achado 1a / CR-01 / 01-VERIFICATION.md):** o sinal antigo media a variância da
TAXA de crescimento. Compounders reais crescem de forma DESIGUAL (WEGE3: retornos de -3% a +53%
ao ano), produzindo CV≈0.80 — indistinguível de uma cíclica genuína. O golden sintético (`1.18**i`,
crescimento perfeitamente suave, CV≈0.001) mascarava o defeito porque não existe em nenhuma empresa
real.

**Correção:** ajuste OLS de `ln(lucro) ~ tempo` sobre os anos de lucro positivo; o sinal passa a ser
o `pstdev` dos resíduos. Isso mede apenas o desvio da TENDÊNCIA — um compounder monotônico (mesmo
desigual) gruda na reta em log (resíduos ~0.15-0.22); um cíclico oscila em torno dela (~0.49+).

**Escala real medida (CVM 2015-2023):**

| Regime | Tickers | resid log-linear |
|--------|---------|------------------|
| Compounder/defensivo | WEGE3 0.174 · RADL3 0.156 · ABEV3 0.158 · LREN3 0.220 | 0.15–0.22 |
| Cíclico (com prejuízo na janela) | VALE3 0.49 · GGBR4 0.61 · SUZB3 0.87 · PETR4 1.24 | 0.49–1.24 |

Corte `ciclica_cv_min = 0.35` — folga de ~0.13 acima dos compounders e ~0.14 abaixo das cíclicas.

## Tasks

| Task | Nome | Commit | Arquivos |
|------|------|--------|----------|
| 1 (RED) | Goldens reais WEGE3/RADL3 falhando | 3642a2a | tests/test_arquetipo.py |
| 1 (GREEN) | `_cv_lucro` = resíduos log-lineares + recalibração | b783b4e | arquetipo.py, config.yaml |
| 2 | Golden parametrizado multi-ticker + ARQ-02 preservado | a5adfbf | tests/test_arquetipo.py |

## Warnings do plan-checker aplicados

- **W1 (margem do corte):** os resíduos reais foram COMPUTADOS a partir das séries (não das figuras
  arredondadas da tabela) antes de fixar o número. VALE3 computou 0.4879 (não 0.500); o corte 0.35
  fica bem abaixo, com margem visível — não foi pinado à borda.
- **W2 (precedência do prejuízo):** o override de prejuízo (`lucro <= 0` → sinal-sentinela acima do
  corte) precede EXPLICITAMENTE o guard de `<3 pontos → None`, documentado no código. GGBR4 (3 anos
  de prejuízo, só 6 pontos positivos) → `ciclica`, testável e verde.

## Deviations from Plan

None — plano executado exatamente como escrito. Nenhuma regra 1-4 disparada; nenhum gate de
autenticação.

## TDD Gate Compliance

Sequência RED → GREEN confirmada no git log:
- RED: `test(01-05): add failing real-series goldens...` (3642a2a) — 2 falhas reproduzem o gap
- GREEN: `feat(01-05): cyclicality signal = log-linear residual dispersion` (b783b4e) — verde

## Verification

- `python -m pytest tests/test_arquetipo.py -q` → 21 passed
- `python -m pytest -q` → **365 passed, 0 failed** (baseline 355 + 10 novos; nenhum regride)
- WEGE3, RADL3 reais → `crescimento`, `fronteirico=False`
- ABEV3 (defensivo real) → `!= ciclica`
- VALE3, GGBR4, SUZB3, PETR4 reais → `ciclica`
- `test_conflito_de_sinais_marca_fronteirico` verde (ARQ-02 preservado)
- `git diff --stat` prova apenas 3 arquivos tocados; `ddm.py`/`selo.py` intocados (firewall preservado)
- `grep -F "1.18**i"` em tests → 0 (golden sintético removido; único hit de regex `1.18` é
  coincidência de dígitos no literal real de ABEV3)

## Self-Check: PASSED

Todos os arquivos criados/modificados existem no disco; todos os 3 commits (3642a2a, b783b4e, a5adfbf) confirmados no git log.
