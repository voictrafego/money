---
phase: 08-saneamento-do-motor-ddm
verified: 2026-06-27T00:30:00Z
status: passed
score: 5/5 must-haves verificados
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
---

# Phase 8: Saneamento do motor DDM (caso VULC3) — Relatório de Verificação

**Phase Goal:** Corrigir a divergência estrutural do valuation fundamentalista (DDM/múltiplos) exposta pelo caso VULC3 (intrínseco R$ 167–334 vs preço R$ 14, veredito "SUBAVALIADA" sobre uma divergência de modelo) entregando FIX-04 (normalização de lucro), FIX-02 (reconciliação g×payout), FIX-03 (CAPM local com Selic ao vivo) e FIX-06 (guardrails/regressão), com rebaseline deliberado dos golden.
**Verificado:** 2026-06-27
**Status:** PASSED
**Re-verificação:** Não — verificação inicial

## Goal Achievement

### Observable Truths (Success Criteria do ROADMAP + must_haves dos planos)

| # | Truth | Status | Evidência |
|---|-------|--------|-----------|
| 1 | FIX-04: o lucro consumido por ROE/CAGR/payout/DY passa por camada de normalização (mediana/winsor N-anos), não lucro CVM cru | ✓ VERIFICADO | `core/normalizacao.py` (primitiva pura: `base_normalizada`, `media_winsorizada`, `serie_winsorizada`). `fundamentals.py:122-142` `base_lucro_normalizada`/`roe_valuation`/`lpa_valuation`/`serie_lucro_normalizada` consomem `norm.base_normalizada`. `report.py:58-68,75-78` os múltiplos de valuation e o CAGR saem da base normalizada. `config.yaml:56-58` bloco `normalizacao` (anos_media 3, winsor 0.10). 9 testes em `test_normalizacao.py` verdes. |
| 2 | FIX-02: g_alto reconciliado com g_fundamentos(payout_valuation); payout≥100% ⇒ g→0 | ✓ VERIFICADO | `report.py:81` `g_fundamentos = ROE_norm × (1−payout_valuation)`; `report.py:92-97` g_alto subordinado a g_fundamentos (teto), teto absoluto 0.25, **sem piso g_estavel**; `report.py:128-129` trava `g_alto ≤ Ke` (FIX-01) preservada. `test_growth_reconciliacao.py` (4) + `test_vulc3_regressao.py` asserts `g_fundamentos==0.0` e `g_alto==0.0` com `payout_valuation()==1.0`. |
| 3 | FIX-03: inputs do CAPM vêm de dado vivo (BCB/Selic) ou fallback; Ke coerente com small cap BR | ✓ VERIFICADO | `config.yaml:61-71` `capm.abordagem: local`, `erp_local: 0.06`, `selic_fallback/rf_local: 0.105`. `macro.selic_para_capm` = `selic_meta() or fallback`. Entry points injetam: `cli.py:68` e `app.py:103` sobrescrevem `cfg["capm"]["rf_local"]`. `report.py:112-117` branch local lê rf JÁ resolvido do cfg (engine offline). Ke VULC3 = 0,105 + 0,88×0,06 = **15,78%** (vs 9,43% legado). `test_capm_local.py` (5): live (monkeypatch 0.15), fallback (None→0.105), faixa small cap, engine determinística. |
| 4 | FIX-06: DY recorrente vs trailing, banda = sensibilidade real, setor correto; VULC3 como regressão | ✓ VERIFICADO | Banda: `report.py:163-171` `vmin/vmax = min/max` das células não-None da matriz Ke×g (`ddm.matriz_sensibilidade`), fallback gracioso p/ 2 cenários (T-08-07). DY: `fundamentals.py:173-180` `dpa_recorrente`/`dy_recorrente` sobre provento normalizado, exibido como "DY rec." (`report.py:68,381`). Setor: `data/ticker_map.json` VULC3 = `{cd_cvm:11762, setor:"Calçados (Consumo Cíclico)"}`; `universe.py:100-107` `resolver` aplica override display-only. Regressão: `test_vulc3_regressao.py` (2 testes) trava os 6 invariantes da cascata. |
| 5 | Golden rebaselinados deliberadamente com justificativa, não "verde a qualquer custo" | ✓ VERIFICADO | Commits de rebaseline com justificativa por valor: `e60d743` (08-01) muda assert para `== c.roe_valuation()` e ADICIONA `!= c.roe(ult)` (mais estrito); `d6dec48` (08-02) documenta g_alto 0,025→0,0 mantendo o assert de direção intacto; `601e521`/`3f77add` (08-03) rebaseline de Ke. Nenhum assert afrouxado — a igualdade cross-menu virou exata (`==`). 08-04 não exigiu rebaseline (banda só alarga simetricamente). |

**Score:** 5/5 truths verificados

### Verificação do caso âncora VULC3 (regressão)

| Vetor | Pré-fix (FINDINGS) | Pós-cascata (golden) | Assert no golden |
|-------|--------------------|----------------------|------------------|
| Base de lucro de valuation | cru 12000 (ano extraordinário) | mediana 4000 | `base < lucro_liquido[extraord]` |
| g_alto adotado | 25% | 0,0 (payout 100% ⇒ g_fund=0) | `a.g_alto == 0.0` |
| Ke | 9,43% (literais 2019) | 15,78% | `a.ke >= 0.15` |
| Intrínseco (teto banda) | 167–334 (11–23× preço) | ~32,72 (2,3× preço) | `a.vmax < 3.0 × preco` |
| Banda = sensibilidade real | toggle binário | matriz Ke×g | `vmin==min(células) and vmax==max(células)` |
| Veredito | SUBAVALIADA (verde) | VERIFICAR | `not startswith("SUBAVALIADA") and startswith("VERIFICAR")` |
| Cross-menu ROE/payout | — | iguais | `multiplos["ROE"]==roe_valuation()` e `["DP (payout)"]==payout_valuation()` |

### Invariante de consistência cross-menu (Core Value)

| Superfície | ROE | Payout | LPA | Evidência |
|-----------|-----|--------|-----|-----------|
| Analisar (engine) | `roe_valuation()` | `payout_valuation()` | `lpa_valuation()` | `report.py:63,65,58` |
| Ranking app | `roe_valuation()` | `payout_valuation()` | `lpa_valuation()` | `app.py:330,333,327,339` |
| Ranking cli | `roe_valuation()` | `payout_valuation()` | `lpa_valuation()` | `cli.py:146,149,143,159` |
| Screening (garimpo) | cru (inalterado) | cru | — | `core/screening.py` não tocado na Fase 8 (último commit fase 01) — fronteira documentada |

### Fronteira (offline/cru) — confirmada

| Verificação | Esperado | Resultado |
|-------------|----------|-----------|
| `selic_meta(` chamado em `report.py` | 0 | 0 (só comentários nas linhas 115/357) |
| Rede (requests/urllib/http/yfinance) em `report.py` | 0 | 0 (engine pura) |
| `screening.py` alterado na Fase 8 | NÃO | NÃO (último commit em fase 01: f0f8000) |
| Resolução de Selic ao vivo | só cli/app | `cli.py:68,89` e `app.py:41,103` |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suíte completa verde | `.venv/bin/python -m pytest -q` | 133 passed in 1.03s | ✓ PASS |
| Testes específicos da Fase 8 | `pytest test_normalizacao test_growth_reconciliacao test_capm_local test_vulc3_regressao test_guardrails_fix06 test_consistencia_modos` | 28 passed | ✓ PASS |
| Regressão VULC3 (cascata domada) | `pytest tests/test_vulc3_regressao.py` | 2 passed | ✓ PASS |

### Required Artifacts

| Artifact | Esperado | Status | Detalhes |
|----------|----------|--------|----------|
| `core/normalizacao.py` | Primitiva de normalização | ✓ VERIFICADO | 3 funções puras, sem ciclo de import |
| `core/fundamentals.py` | Métodos canônicos `_valuation` | ✓ VERIFICADO | roe/lpa/payout/dy + base/série normalizadas |
| `core/capm.py` | `ke_local` | ✓ VERIFICADO | `ke_local(beta, rf, erp)` |
| `ingest/macro.py` | Resolvedor rf (Selic+fallback) | ✓ VERIFICADO | `selic_para_capm` |
| `ingest/universe.py` + `data/ticker_map.json` | Override de setor | ✓ VERIFICADO | VULC3 = Calçados, display-only |
| `report/report.py` | g reconciliado + banda real + DY rec. | ✓ VERIFICADO | offline, lê cfg resolvido |
| `config.yaml` | blocos normalizacao + capm local | ✓ VERIFICADO | erp_local, selic_fallback, rf_local |
| `tests/test_*.py` (6 arquivos) | golden + regressão | ✓ VERIFICADO | 28 testes, todos reais e verdes |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | Nenhum marcador TBD/FIXME/XXX nos arquivos da fase; nenhum stub; banda/DY consomem dados reais | ℹ️ Info | Nenhum |

### Gaps Summary

Nenhum gap. Os 5 critérios de sucesso do ROADMAP e todos os must_haves dos 4 planos estão implementados no código e travados por testes determinísticos offline (133 verdes). O caso âncora VULC3 deixou de ser 11–23× o preço (agora ~2,3×, golden trava < 3×), o veredito é "VERIFICAR" (não-verde), g_alto≈0 com payout 100%, Ke na faixa small cap (15,78%), e a asserção cross-menu (ROE/payout do Analisar == base que o Ranking consome) está presente no golden de regressão. A fronteira está intacta: `screening.py` permanece cru/não tocado e a engine permanece offline (rede só em cli/app). O rebaseline foi deliberado e justificado por valor — nenhum assert foi afrouxado; ao contrário, a igualdade cross-menu virou exata e asserts mais estritos foram adicionados.

---

_Verificado: 2026-06-27_
_Verificador: Claude (gsd-verifier)_
