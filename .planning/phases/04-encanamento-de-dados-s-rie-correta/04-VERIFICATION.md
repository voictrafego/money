---
phase: 04-encanamento-de-dados-s-rie-correta
verified: 2026-06-26T18:30:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 4: Encanamento de dados + série correta — Verification Report

**Phase Goal:** O frame OHLCV de 5 anos que o Yahoo já baixa deixa de ser descartado e fica disponível na engine (DadosMercado.ohlc → CompanyData.ohlc), com uma série ajustada por SPLITS (não dividendos) pronta para os cálculos de indicador — sem novo comportamento visível, sem nova chamada de rede, e sem qualquer fórmula de valuation alterada.
**Verified:** 2026-06-26T18:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | OHLCV de 5 anos preservado em `DadosMercado.ohlc` e conduzido até `CompanyData.ohlc`, sem nova chamada ao Yahoo (DATA-01) | ✓ VERIFIED | `prices.py:154` `dm.ohlc = hist`; `build.py:42` `c.ohlc = dm.ohlc`; única chamada `tk.history` é a pré-existente em `prices.py:146`, compartilhada com `serie_precos` |
| 2 | Série ajustada por splits (não dividendos) disponível; gráfico permanece Close nominal (DATA-02, CR-01); validada em ticker com split conhecido (ITSA4) — sem cruzamentos espúrios (D-08) | ✓ VERIFIED | `_ajustar_por_split` usa coluna `"Stock Splits"` exclusivamente (prices.py:95-108); "Adj Close" só aparece em comentários dentro da função (linhas 74/83); `serie_precos` inalterado em `prices.py:153`; 3 testes offline ITSA4 (5 eventos) passam; checkpoint humano de rede real aprovado e documentado em 04-02-SUMMARY.md |
| 3 | Histórico curto/vazio → encanamento degrada graciosamente (ohlc=None) sem quebrar (DATA-03) | ✓ VERIFIED | `_ajustar_por_split`: guard `if hist is None or hist.empty: return None` em `prices.py:88-89`; campos `ohlc`/`ohlc_ajustado` só são atribuídos dentro do guard `if hist is not None and not hist.empty:` em `prices.py:150`; `test_dm_ohlc_none_quando_hist_vazio` PASSA |
| 4 | Os 64 golden tests de valuation continuam verdes (TEST-07) | ✓ VERIFIED | 77 testes passam na suíte completa; 64 pré-existentes intactos (49 golden de valuation + 15 de `test_ingest_resolucao.py`); fase puramente aditiva — nenhuma fórmula do livro alterada |

**Score:** 4/4 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/ingest/prices.py` | Campos `ohlc`/`ohlc_ajustado` em `DadosMercado` + `_ajustar_por_split` pura + atribuição no bloco hist | ✓ VERIFIED | `DadosMercado.ohlc` em linha 59, `DadosMercado.ohlc_ajustado` em linha 60; `def _ajustar_por_split(` em linha 70; `dm.ohlc = hist` em linha 154; `dm.ohlc_ajustado = _ajustar_por_split(hist)` em linha 155 |
| `src/analista/ingest/build.py` | Cópia `c.ohlc = dm.ohlc` e `c.ohlc_ajustado = dm.ohlc_ajustado` em `montar_empresa` | ✓ VERIFIED | `build.py:42` `c.ohlc = dm.ohlc`; `build.py:43` `c.ohlc_ajustado = dm.ohlc_ajustado` |
| `src/analista/core/fundamentals.py` | Campos `ohlc`/`ohlc_ajustado` no dataclass `CompanyData` | ✓ VERIFIED | `fundamentals.py:46` `ohlc: Optional["pd.DataFrame"] = None`; `fundamentals.py:47` `ohlc_ajustado: Optional["pd.DataFrame"] = None` |
| `tests/test_ingest_ohlc.py` | Testes offline de preservação do frame, função de split e degradação graciosa; validação ITSA4 (D-08) | ✓ VERIFIED | 13 testes, todos offline (monkeypatch), 13/13 PASSAM |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `prices.py` (`DadosMercado`) | `build.py` (`montar_empresa`) | `dm.ohlc` / `dm.ohlc_ajustado` lidos em `montar_empresa` | ✓ WIRED | `build.py:42-43` — cópia direta, sem condicional |
| `build.py` | `fundamentals.py` (`CompanyData`) | Atribuição `c.ohlc` / `c.ohlc_ajustado` | ✓ WIRED | Campos declarados em `CompanyData` e recebem os valores de `dm` |
| `test_ingest_ohlc.py` | `prices.py` (`_ajustar_por_split`) | Chamada direta + fixture ITSA4 multi-split | ✓ WIRED | `prices._ajustar_por_split` importado e chamado em todos os 13 testes |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `DadosMercado.ohlc` | `hist` (DataFrame) | `tk.history(period="5y", auto_adjust=False)` — chamada pré-existente | Sim — frame cru do Yahoo (toda a largura OHLCV) | ✓ FLOWING |
| `DadosMercado.ohlc_ajustado` | `_ajustar_por_split(hist)` | `"Stock Splits"` dentro do `hist` já em memória — sem nova rede | Sim — derivado do hist em memória | ✓ FLOWING |
| `CompanyData.ohlc` / `CompanyData.ohlc_ajustado` | `dm.ohlc` / `dm.ohlc_ajustado` | Propagados de `DadosMercado` via `montar_empresa` | Sim — cópia direta | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 13 testes offline de OHLC/split | `.venv/bin/pytest tests/test_ingest_ohlc.py -q` | 13 passed in 0.20s | ✓ PASS |
| Suíte completa (77 testes) | `.venv/bin/pytest tests/ -q` | 77 passed in 0.48s | ✓ PASS |
| Subconjunto golden de valuation | `.venv/bin/pytest tests/test_ddm.py tests/test_multiples.py tests/test_screening.py tests/test_comparables.py tests/test_fundamentals_consistencia.py tests/test_consistencia_modos.py -q` | 49 passed | ✓ PASS |

### Probe Execution

Nenhum probe declarado para esta fase. Step 7c: SKIPPED (fase sem probes convencionais; a verificação é coberta pelos spot-checks acima).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | 04-01-PLAN | Frame OHLCV preservado sem nova chamada de rede | ✓ SATISFIED | `prices.py:154-155`; `_ajustar_por_split` é pura; única `tk.history` é pré-existente |
| DATA-02 | 04-01-PLAN / 04-02-PLAN | Série split-adjusted via "Stock Splits", não "Adj Close"; gráfico em Close nominal | ✓ SATISFIED | `_ajustar_por_split` usa coluna "Stock Splits" (prices.py:95-108); "Adj Close" não tocado como base; `serie_precos` usa `hist["Close"]` (prices.py:153) |
| DATA-03 | 04-01-PLAN | Degradação graciosa quando hist vazio/None | ✓ SATISFIED | Guard em `prices.py:88-89` e `prices.py:150`; teste `test_dm_ohlc_none_quando_hist_vazio` PASSA |
| TEST-07 | 04-02-PLAN | 64 golden tests de valuation continuam verdes | ✓ SATISFIED | 64 testes pré-existentes intactos (49 de valuation + 15 de ingest_resolucao); 77 total PASSAM |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | Nenhum encontrado nos 4 arquivos modificados. Zero TBD/FIXME/XXX/TODO nos arquivos desta fase. |

### Human Verification Required

Nenhum item pendente. O checkpoint humano de validação de rede real do ITSA4 (Task 2 do 04-02-PLAN, `gate=blocking`) foi realizado e aprovado durante a execução da fase, com evidências documentadas em 04-02-SUMMARY.md:

- `dm.ohlc_ajustado` != None para ITSA4
- Ponta recente: ajustado == nominal (13.52 == 13.52, fator cumulativo = 1 após último split de dez/2025)
- Close mais antigo: nominal 8.6712, ajustado 6.6760 (< nominal, produto dos 5 fatores confirmado)
- 5 eventos detectados nas datas corretas; produto ≈ 1.2989 confere com 8.6712/1.2989 = 6.676
- Controle TAEE4 (0 splits): ajustado == nominal

Não há necessidade de re-executar este checkpoint.

### Gaps Summary

Nenhuma lacuna identificada. Todos os 4 critérios de sucesso do ROADMAP estão verificados com evidência direta no código.

---

## Nota: Contagem dos "64 golden tests"

O ROADMAP cita "64 golden tests de valuation". A contagem se divide em:
- 49 testes nos 6 arquivos de valuation/screening/comparáveis (ddm, multiples, screening, comparables, fundamentals_consistencia, consistencia_modos)
- 15 testes em `test_ingest_resolucao.py` (ingest pré-existente, anterior à Phase 4)
- **Total pré-existente: 64** — todos intactos na suíte de 77 (77 − 13 novos OHLC = 64).

---

_Verified: 2026-06-26T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
