---
phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia
verified: 2026-06-27T22:00:00Z
status: passed
score: 7/7
overrides_applied: 0
---

# Phase 9: Payout sustentável + DY recorrente (núcleo de metodologia) — Relatório de Verificação

**Phase Goal:** O payout-para-valuation e o DY recorrente passam a refletir a renda sustentável de qualquer ticker — expurgando anos não-recorrentes por regra geral, não por ajuste de caso — em vez da média/mediana crua de 3 anos que satura no clamp de 100%.
**Verificado:** 2026-06-27T22:00:00Z
**Status:** PASSED
**Re-verificação:** Não — verificação inicial.

---

## Goal Achievement

### Observable Truths

| # | Truth (critério de sucesso ROADMAP) | Status | Evidência |
|---|--------------------------------------|--------|-----------|
| 1 | `payout_valuation()` expurga anos não-recorrentes por regra geral: mediana sobre série completa, sem clamp 1.0 — payout sustentável <100% para VULC3 (ano extraordinário), >100% preservado para TAEE11 (recorrente) | VERIFIED | `fundamentals.py` L88-89: `serie=[self.payout(a) for a in self.anos_ordenados()]` + `return norm.mediana_payout(serie)`. Sem `min(...,1.0)`. Série toda 2.0 → `payout_valuation()` retorna 2.0. |
| 2 | DY recorrente deriva de **lucro normalizado × payout sustentável** (earnings-based), não mais mediana crua de 3 anos de dividendos | VERIFIED | `fundamentals.py` L178-182: `p = self.payout_valuation()`, `l = self.lpa_valuation(...)`, `return p * l`. `dy_recorrente` usa `dpa_recorrente / preco_atual`. Nenhuma referência a `base_normalizada(self.serie("dividendos"))`. |
| 3 | Com payout sustentável <100%, `g_fundamentos = ROE_norm × (1 − payout)` deixa de ser zerado por saturação do clamp em tickers cujo payout cru passou de 100% num único ano | VERIFIED | `test_payout_sustentavel_multiticker.py::test_perfil_payout_acima_100_em_um_ano_g_fund_volta_a_existir` passa: `a.g_fundamentos > 0`. Contraste explícito: perfil payout>100% em todos os anos → `g_fund ≤ 0`. |
| 4 | Validado em VULC3 (caso-limite) E em ≥2 tickers normais: o expurgo só atua sobre anos realmente extraordinários e não rebaixa quem distribui muito de forma sustentável | VERIFIED | 5 testes multi-ticker offline verdes (4 perfis: TAEE11 no-clamp, VULC3 spike-discard, EGIE3 estável, XPTO3 único-ano-anomalo). Validação live dos 5 tickers reais aprovada pelo usuário (Task 2 checkpoint human-verify, resultados registrados no 09-03-SUMMARY). |
| 5 | Fronteira per-ano preservada: `payout(ano)` CRU segue intacto (tabela por ano, detector de armadilha, screening per-ano); screening.py NÃO editado; golden rebaselinados deliberadamente | VERIFIED | `payout(ano)` em `fundamentals.py` L74-75 intacto. Commit log confirma `screening.py` sem toque na Fase 9. `09-CROSS-EFFECT-FASE10.md` registra o cross-effect para a Fase 10. `test_vulc3_regressao.py` L83 rebaselinado para `> 1.0` (sem clamp) com justificativa. |
| 6 | `normalizacao.py` livre de imports de `fundamentals` / `report` (sem ciclo de import) — primitiva pura preservada | VERIFIED | `inspect.getsource(norm)` → `"fundamentals" not in src` e `"report" not in src`. Imports: apenas `from statistics import median`, `typing`, `numpy`. Teste `test_primitiva_e_pura_sem_import_de_fundamentals` verde. |
| 7 | Suíte completa verde (160 testes), incluindo goldens rebaselinados com justificativa pelo método | VERIFIED | `pytest -q`: **160 passed, 0 failed** em 1.35s. Nenhuma regressão. |

**Score:** 7/7 truths verificadas.

---

### Required Artifacts

| Artifact | Fornece | Status | Detalhes |
|----------|---------|--------|----------|
| `src/analista/core/normalizacao.py` | Primitiva pura `mediana_payout` (irmã de `base_normalizada`, reusando `_limpar`) | VERIFIED | L78-91: `def mediana_payout(valores)` — `_limpar` → vazio→None → len==1→valor → `float(median(limpos))`. Sem janela, sem clamp. |
| `tests/test_normalizacao.py` | 5 goldens unitários de `mediana_payout` (no-clamp >1.0, descarte de spike, série completa, None, fronteira) | VERIFIED | L88-128: 5 testes cobrindo D-01/D-03/D-04. Todos passam. |
| `src/analista/core/fundamentals.py` | `payout_valuation` mediano/sem-clamp + `dpa_recorrente`/`dy_recorrente` earnings-based | VERIFIED | L77-89 (`payout_valuation` delega a `norm.mediana_payout`), L172-187 (`dpa_recorrente = p × l`, `dy_recorrente = dpa_rec / preco`). |
| `tests/test_fundamentals_consistencia.py` | Goldens rebaselinados para mediana-sobre-série-completa (sem clamp) | VERIFIED | L15-33: 2 goldens rebaselinados com justificativa pelo método. Docstring de módulo atualizado para "PAY-01: mediana sobre série completa, SEM clamp". |
| `tests/test_vulc3_regressao.py` | Capstone VULC3 rebaselinado: `payout_valuation() > 1.0`, `g_fundamentos <= 0.0`; `g_alto == 0.0` intacto | VERIFIED | L83: `assert a.g_fundamentos <= 0.0`. L87: `assert a.g_alto == 0.0`. Todos verdes. |
| `tests/test_payout_sustentavel_multiticker.py` | Golden offline de propriedade multi-ticker (4 perfis sintéticos calibrados) | VERIFIED | 151 linhas, 5 testes verdes cobrindo 4 perfis (TAEE11, VULC3, EGIE3 estável, XPTO3 único-ano). |
| `.planning/phases/09-.../09-CROSS-EFFECT-FASE10.md` | Registro do cross-effect payout-sem-clamp → regressão P/L (handoff Fase 10) | VERIFIED | Arquivo existe, 32 linhas, cita `preco_alvo_por_regressao`, `screening.py`, `cli.py L158-159`, `app.py L472`. |

---

### Key Link Verification

| From | To | Via | Status | Evidência |
|------|----|-----|--------|-----------|
| `fundamentals.py::payout_valuation` | `norm.mediana_payout` | delegação da série completa de `payout(ano)` | WIRED | L89: `return norm.mediana_payout(serie)`. Grep confirma 1 ocorrência. |
| `fundamentals.py::dpa_recorrente` | `payout_valuation() × lpa_valuation()` | composição earnings-based (D-05) | WIRED | L178-182: `p = self.payout_valuation()`, `l = self.lpa_valuation(...)`, `return p * l`. Resposta correta: `pv=0.49`, `lpa=1.0` → `dpa_rec=0.49`. |
| `normalizacao.py::mediana_payout` | `_limpar` | reuso do convênio de descarte de None | WIRED | L86: `limpos = _limpar(valores)`. |
| `tests/test_payout_sustentavel_multiticker.py` | `report.analisar_acao` / `payout_valuation` / `dy_recorrente` | construtores sintéticos por perfil | WIRED | L135: `report.analisar_acao(c, _cfg())`, L83: `c.payout_valuation()`, L116: `c.dy_recorrente()`. |

---

### Data-Flow Trace (Level 4)

| Artifact | Variável | Fonte | Produz dado real | Status |
|----------|----------|-------|-----------------|--------|
| `payout_valuation()` | `serie` (list de `payout(ano)`) | `self.anos_ordenados()` + `self.payout(a)` (CRU por ano) | Sim — série completa histórica, delegates para `mediana_payout` | FLOWING |
| `dpa_recorrente()` | `p * l` | `payout_valuation()` × `lpa_valuation()` | Sim — composição de duas fontes vivas da engine | FLOWING |
| `dy_recorrente()` | `dpa_recorrente / preco_atual` | `mult.dividend_yield(dpa_recorrente(...), self.preco_atual)` | Sim — None-safe | FLOWING |

---

### Behavioral Spot-Checks

| Comportamento | Comando | Resultado | Status |
|---------------|---------|-----------|--------|
| `payout_valuation()` sem clamp: série toda 2.0 → retorna 2.0 (não 1.0) | `.venv/bin/python -c "... print(c.payout_valuation())"` | `2.0` | PASS |
| Earnings-based: `dpa_recorrente() == payout_valuation() × lpa_valuation()` | `.venv/bin/python -c "... print(abs(dpa_rec - pv*lpa_v) < 1e-9)"` | `True` | PASS |
| `payout(ano)` CRU intacto: payout(2023)=1.5 (div=150, lucro=100) | `.venv/bin/python -c "... print(c.payout(2023))"` | `1.5` | PASS |
| Suíte completa 160 testes verdes | `.venv/bin/python -m pytest -q` | `160 passed in 1.35s` | PASS |
| 5 goldens de `mediana_payout` passam | `.venv/bin/python -m pytest tests/test_normalizacao.py -k mediana_payout` | `5 passed` | PASS |
| 5 goldens multi-ticker passam | `.venv/bin/python -m pytest tests/test_payout_sustentavel_multiticker.py -v` | `5 passed` | PASS |
| Assinatura canônica sem `janela` | `inspect.signature(payout_valuation).parameters` | `['self']` | PASS |
| Pureza: sem imports de `fundamentals`/`report` em `normalizacao.py` | `inspect.getsource(norm)` checks | `False, False` | PASS |

---

### Probe Execution

Não aplicável — sem probes declarados nesta fase.

---

### Requirements Coverage

| Requirement | Plano(s) | Descrição | Status | Evidência |
|-------------|---------|-----------|--------|-----------|
| PAY-01 | 09-01, 09-02, 09-03 | Payout-para-valuation expurga anos não-recorrentes por regra geral (mediana, sem clamp) | SATISFIED | `norm.mediana_payout` + `payout_valuation()` delegando + 14 testes green |
| DYR-01 | 09-02, 09-03 | DY recorrente = lucro normalizado × payout sustentável (não mediana crua de dividendos) | SATISFIED | `dpa_recorrente = p × l` + `dy_recorrente = dpa_rec / preco` + guardrails FIX-06 verdes |

---

### Anti-Patterns Found

| Arquivo | Padrão | Severidade | Impacto |
|---------|--------|-----------|---------|
| Nenhum | — | — | — |

Nota: Ocorrências de "TODO" e "TODOS" nos arquivos de teste são palavras em português ("em TODO ano" = "em CADA ano", "TODOS os pontos" = "ALL points"), não marcadores de dívida técnica.

---

### Human Verification Required

Nenhum item requer verificação humana adicional.

A validação live dos 5 tickers reais (Task 2 do Plan 03) foi executada como checkpoint `type="checkpoint:human-verify"` durante a execução e aprovada explicitamente pelo usuário. Os resultados estão documentados no `09-03-SUMMARY.md` (tabela com VULC3 43.1%, TAEE11 217.9%, EGIE3 49.9%, ITUB4 31.2%, BBAS3 18.8%). As propriedades matemáticas que sustentam esses números estão cobertas pelos goldens offline determinísticos, que passam sem rede.

---

### Gaps Summary

Nenhum gap. Todos os 7 critérios verificados, suíte completa verde (160 testes), artifacts substantivos e devidamente conectados, sem anti-patterns bloqueadores.

---

## Deferred Items

Nenhum item desta fase está adiado — os 5 critérios de sucesso do ROADMAP foram integralmente satisfeitos.

O **cross-effect payout-sem-clamp → regressão P/L do screening** é intencionalmente deferido para a Fase 10 (de-poison do screening), conforme registrado em `09-CROSS-EFFECT-FASE10.md`. Não é um gap desta fase: D-06 é uma decisão de fronteira, não um requisito não-cumprido.

| Item | Abordado em | Evidência |
|------|-------------|-----------|
| De-poison do `preco_alvo_por_regressao` para `payout_valuation() > 1.0` (TAEE11 ≈ 2.16) | Phase 10 | ROADMAP Phase 10 SC 2: "Garimpo/Ranking calculando crescimento sobre série normalizada, não CRU"; `09-CROSS-EFFECT-FASE10.md` registrado. |

---

_Verified: 2026-06-27T22:00:00Z_
_Verifier: Claude (gsd-verifier) — sonnet-4-6_
