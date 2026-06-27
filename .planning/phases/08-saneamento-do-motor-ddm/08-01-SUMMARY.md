---
phase: 08-saneamento-do-motor-ddm
plan: 01
subsystem: motor-fundamentalista / valuation
tags: [FIX-04, normalizacao-lucro, valuation, cross-menu, golden-rebaseline]
requires:
  - Phase 1 (payout_valuation canônico; guard cross-menu test_consistencia_modos)
provides:
  - "src/analista/core/normalizacao.py: primitiva de normalização de lucro (pura)"
  - "CompanyData.roe_valuation / lpa_valuation / base_lucro_normalizada / serie_lucro_normalizada"
  - "config.yaml: bloco normalizacao (anos_media, winsor)"
  - "Base normalizada como número canônico ÚNICO consumido por Analisar + Ranking (app+cli)"
affects:
  - 08-02 (FIX-02 reconcilia g_alto com g_fundamentos/payout — já lê roe_valuation/payout_valuation)
  - 08-03 (FIX-03 CAPM), 08-04 (FIX-06 guardrails/regressão VULC3)
tech-stack:
  added: []
  patterns:
    - "Método canônico chamado SEM args nas 3 superfícies → consistência entre menus por construção (espelha payout_valuation)"
    - "Primitiva pura sem ciclo de import com a engine (só numpy/statistics)"
key-files:
  created:
    - src/analista/core/normalizacao.py
    - tests/test_normalizacao.py
  modified:
    - config.yaml
    - src/analista/core/fundamentals.py
    - src/analista/report/report.py
    - app.py
    - src/analista/cli.py
    - tests/test_fundamentals_consistencia.py
    - tests/test_consistencia_modos.py
decisions:
  - "Primitiva: mediana p/ 2≤N<5, média winsorizada p/ N≥5 (winsor percentil não morde poucos pontos)"
  - "Defaults anos_media=3/winsor=0.10 baked nos métodos (espelham config), chamados bare nas 3 superfícies"
  - "Flags de risco (payout>100%, DY>15%) leem CRU — payout_valuation clampado nunca dispararia DDM-FIX-05"
  - "DY display roteado p/ dy_atual() canônico; ML segue cru (margem do ano, não síntese de valuation)"
metrics:
  duration: "~25 min"
  completed: 2026-06-26
  tasks: 3
  files: 9
  tests: "117 passed (era 103 + 9 normalizacao + 5 fundamentals)"
---

# Phase 8 Plan 01: Camada de normalização de lucro (FIX-04) Summary

Base de lucro normalizada (mediana/média winsorizada de N anos) vira o número-síntese canônico ÚNICO de valuation (ROE/LPA/CAGR/payout), consumido identicamente por Analisar, Ranking app e Ranking cli — cortando a raiz da cascata VULC3 onde o lucro CVM cru de 1 exercício contaminava todos os múltiplos.

## O que foi feito

**Task 1 — Primitiva + knob + golden unitário (`a26fc0c`)**
- `src/analista/core/normalizacao.py`: `base_normalizada` (mediana p/ 2≤N<5, média winsorizada p/ N≥5, valor único p/ N=1, None p/ vazio), `media_winsorizada` e `serie_winsorizada` (série mesmo-comprimento p/ o CAGR). Primitiva pura (sem import da engine de fundamentos/relatório).
- `config.yaml`: bloco novo `normalizacao` (`anos_media: 3`, `winsor: 0.10`), separado do `bsd` de propósito (valuation ≠ screening), documentado em comentário.
- `tests/test_normalizacao.py`: outlier alto suavizado, winsor nos extremos, None ignorado, série curta → fallback, "últimos N anos", série estável, pureza.

**Task 2 — Métodos canônicos + roteamento das 3 superfícies (`caad841`)**
- `fundamentals.py`: `base_lucro_normalizada`, `serie_lucro_normalizada`, `lpa_valuation`, `roe_valuation` (aplicam a primitiva sobre `lucro_liquido`; mesma fronteira de None que `roe(ano)`). `roe(ano)`/`lpa(ano)`/`payout(ano)` CRUS documentados como base de exibição-por-ano/screening.
- `report.py` (Analisar): múltiplos de valuation (ROE, LPA→P/L/EY, payout, DY), CAGR e `g_fundamentos` roteados aos canônicos; ciclo de vida (lucro_positivo/decrescente) e flags de risco seguem CRUS.
- `app.py` + `cli.py` (Ranking): vetores ROE/PL/EY e `preco_alvo_por_regressao` via `roe_valuation`/`lpa_valuation`; cli passa a usar `payout_valuation` (alinha divergência cli↔app pré-existente). app.py permanece read-only.
- `tests/test_fundamentals_consistencia.py`: golden de `roe_valuation`/`lpa_valuation` (estável==cru, ano atípico suavizado p/ 1/3, None sem PL inicial, crus por ano intactos).

**Task 3 — Guard cross-menu + rebaseline + suíte verde (`e60d743`)**
- `test_roe_coerente_analisar_vs_ranking` agora afirma `a.multiplos["ROE"] == c.roe_valuation()` (superfície-viva Analisar == método-canônico-vivo que o Ranking consome) + `!= c.roe(ult)` (prova que a normalização está ativa, não mascarando).
- `test_payout_coerente`: display de payout == `payout_valuation` (canônico único); cru segue na tabela por ano.
- `test_veredito_direcao_coerente`: vetores via `lpa_valuation`/`roe_valuation`/`payout_valuation` (mirror do Ranking vivo); séries constantes → direção inalterada.
- Suíte inteira verde: **117 passed**.

## Rebaseline dos golden (com justificativa)

| Asserção | Antes | Depois | Por que o novo número é o correto pelo método |
|----------|-------|--------|-----------------------------------------------|
| `a.multiplos["ROE"]` (_empresa_solida) | `== c.roe(ult)` = 0,29897 | `== c.roe_valuation()` = 0,28866 | Base de lucro normalizada = mediana dos 3 últimos (1350,1400,1450)=1400 sobre PL médio 4850; substitui o lucro cru do último ano (1450). É o ROE de qualidade, não o do ano de ponta. |
| `a.multiplos["DP (payout)"]` | `== c.payout(ult)` (cru) | `== c.payout_valuation()` (canônico) | O display de payout do Analisar passa a ser o MESMO número que o Ranking consome (Core Value); o payout cru por ano não some — vive na tabela "Fundamentos (por ano)". Nesta fixture ambos = 0,6 (payout estável). |

`test_ddm.py` e `test_multiples.py` (matemática pura com literais) permanecem inalterados.

## Deviations from Plan

### Auto-fixed / decisões de discrição (Rule 2/3)

**1. [Discrição CONTEXT] Primitiva usa mediana p/ N<5 e winsor p/ N≥5**
- O behavior do plano exigia mediana ≈105 para `[100,105,300]` (N=3) E "média winsorizada para 5+ pontos". Winsorização percentil em 3 pontos não dá 105. Resolvido com branch documentado: mediana p/ 2≤N<5, média winsorizada p/ N≥5. Coberto por golden.

**2. [Rule 2 - correção de fronteira] Flags de risco mantidas em dado CRU**
- Rotear o flag `payout>100%` ao `payout_valuation` (clampado em 1.0) desligaria silenciosamente o DDM-FIX-05 (o detector de armadilha nunca veria 124,7% do VULC3). Mantidos `c.payout(ult)` cru para os flags, com comentário explicando a fronteira. Não estava explícito no plano; é correção de correctness.

**3. [Escopo] DY display roteado a `dy_atual()`; ML mantido cru**
- O plano lista "DY" entre os múltiplos a rotear ao canônico, mas DY-recorrente é FIX-06. Optei pelo canônico JÁ existente (`dy_atual`, trailing-12m c/ fallback) — "rotear ao canônico" sem inventar normalização de dividendo. ML (margem do último ano) ficou cru: é métrica de exibição per-ano, não síntese de valuation.

## Known Stubs

Nenhum. Todas as superfícies de valuation consomem dados reais via os métodos canônicos.

## Self-Check: PASSED
