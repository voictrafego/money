---
phase: 10-crescimento-robusto-de-poison-do-screening
verified: 2026-06-27T00:00:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Rodar CLI ao vivo nos 5 tickers (VULC3, ITUB4, EGIE3, TAEE11, BBAS3) e confirmar que g histórico, BSD e preço-alvo TAEE11 ainda estão sensatos com os dados atuais da CVM/Yahoo/BCB"
    expected: "VULC3 g < CAGR endpoint cru; normais g finito/positivo; TAEE11 preço-alvo finito; BSD VULC3 não saturado por ano extraordinário pós-winsorização"
    why_human: "Exige chamadas a serviços externos (CVM, Yahoo Finance, BCB) — não verificável programaticamente. SUMMARY 10-03 documenta aprovação prévia do usuário; esta verificação confirma que o estado do codebase segue produzindo resultados sensatos com dados atuais."
---

# Phase 10: Crescimento Robusto + De-poison do Screening — Verification Report

**Phase Goal:** O crescimento histórico exibido e o usado no screening (Garimpo BSD + Ranking por múltiplos) passam a vir de uma estimativa robusta sobre a série normalizada — não CAGR endpoint-a-endpoint nem CAGR sobre lucro/dividendo CRU.
**Verified:** 2026-06-27
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | `g_historico` usa regressão log-linear (OLS de ln) sobre a série normalizada, não `cagr(lucros[0], lucros[-1])` | ✓ VERIFIED | `report.py:80` chama `growth.crescimento_log_linear(lucros)`; chamada CAGR antiga removida (grep retorna vazio) |
| 2  | `indicadores_bsd` calcula crescimento de lucro/dividendos/FCO via `crescimento_log_linear` sobre `serie_winsorizada` completa — sem `cagr_serie` | ✓ VERIFIED | `screening.py:267-268` tem `crescimento_serie(attr)` = `growth.crescimento_log_linear(normalizacao.serie_winsorizada(c.serie(attr)))`; `cagr_serie` não existe no arquivo |
| 3  | Ranking (fit OLS) clampa payout em `[0,1]` na ENTRADA do ajuste, sem reintroduzir clamp em `payout_valuation()` | ✓ VERIFIED | `comparables.py:113` tem `min(max(d, 0.0), 1.0)` no list-comprehension `linhas`; `payout_valuation()` sem clamp confirmado por grep em `fundamentals.py` |
| 4  | Validado multi-ticker: VULC3 não infla g/BSD; tickers normais não regridem; TAEE11 não distorce regressão | ✓ VERIFIED | `tests/test_growth_robusto_multiticker.py` com 5 funções test_ passa; suíte completa 171 passed em 1.71s |
| 5  | Fronteira per-ano intacta: `roe(ano)`, `payout(ano)`, `lucros_raw` seguem alimentando elegibilidade per-ano e tabela "Fundamentos por ano" | ✓ VERIFIED | `report.py:77` preserva `lucros_raw = c.serie("lucro_liquido")` (CRU); linhas 104-105 usam `lucros_raw` para `lucro_positivo`/`lucro_decrescente`; tabela por ano em `relatorio_markdown` usa `c.roe(ano)`, `c.payout(ano)` direto |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/growth.py` | `def crescimento_log_linear` + `import numpy as np` + sem ciclo de import | ✓ VERIFIED | Linha 51: `def crescimento_log_linear`; linha 13: `import numpy as np`; sem import de fundamentals/report/screening |
| `src/analista/report/report.py` | `g_historico = growth.crescimento_log_linear(lucros)` + `lucros_raw` preservado + `g_alto` teto 25% intacto | ✓ VERIFIED | Linha 80: chamada log-linear; linha 77: `lucros_raw` presente; linha 98: `max(0.0, min(g_alto, 0.25))` presente |
| `src/analista/core/screening.py` | `from . import normalizacao`; 3 fatores via `crescimento_log_linear`; `var_tangivel` via CAGR; sem `cagr_serie` | ✓ VERIFIED | Linha 18: `from . import growth, normalizacao`; linha 268: `crescimento_log_linear(normalizacao.serie_winsorizada(...))`; linha 247: `growth.cagr(tangivel...)`; `cagr_serie` ausente |
| `src/analista/core/comparables.py` | Clamp `min(max(d,0),1)` no fit de `ajustar_regressao_pl`; 2 ocorrências de `min(max(` (fit + predição) | ✓ VERIFIED | Linha 113: `(p, min(max(d, 0.0), 1.0), r)` em `linhas`; linha 156: clamp da predição já existente |
| `tests/test_growth_robusto_multiticker.py` | ≥4 funções test_ cobrindo VULC3 (a), normais (b), TAEE11 (c), consistência D-04 | ✓ VERIFIED | 5 funções test_: VULC3 spike, D-04 consistência, normais, TAEE11 fit, TAEE11 preço-alvo |
| `tests/test_growth.py` | Golden unitário do estimador: PG exata, série constante, decrescente, ponto ≤0 → None, len<2 → None | ✓ VERIFIED | 6 testes, todos passam |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `report.py` | `growth.crescimento_log_linear` | linha 80: chamada sobre `lucros = serie_lucro_normalizada()` | ✓ WIRED | Grep confirma `growth.crescimento_log_linear(lucros)` em report.py; variável `lucros` vem de `c.serie_lucro_normalizada()` linha 78 |
| `screening.py` | `growth.crescimento_log_linear` | `crescimento_serie(attr)` linha 267-268 | ✓ WIRED | Grep confirma `crescimento_log_linear` e `serie_winsorizada` em screening.py; 3 atributos (fco, dividendos, lucro_liquido) chamados nas linhas 278-280 |
| `comparables.ajustar_regressao_pl` | OLS fit | clamp `min(max(d,0),1)` na montagem de `linhas` | ✓ WIRED | Confirmado em linha 113; property-check: `ajustar_regressao_pl(dp=2.16) == ajustar_regressao_pl(dp=1.0)` validado pelo golden de propriedade |
| `growth.py` | `numpy.polyfit` | OLS de `ln(serie)` vs tempo | ✓ WIRED | Linha 74: `np.polyfit(x, np.log(serie), 1)[0]` |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `report.py:analisar_acao` | `a.g_historico` | `c.serie_lucro_normalizada()` → `growth.crescimento_log_linear(lucros)` | Sim — série winsorizada via fundamentals.py, estimador OLS puro | ✓ FLOWING |
| `screening.py:indicadores_bsd` | `crescimento_lucro_3a` | `c.serie("lucro_liquido")` → `normalizacao.serie_winsorizada(...)` → `growth.crescimento_log_linear(...)` | Sim — série completa winsorizada por atributo | ✓ FLOWING |
| `comparables.py:ajustar_regressao_pl` | `linhas` (design matrix) | payout `d` clampado inline em `[0,1]` antes de `np.linalg.lstsq` | Sim — clamp aplicado na entrada do fit, não é fallback estático | ✓ FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Estimador retorna None p/ ponto ≤0 | `.venv/bin/python -c "from analista.core import growth; print(growth.crescimento_log_linear([100,-5,120]))"` | `None` | ✓ PASS |
| Estimador recupera taxa de PG exata | `.venv/bin/python -c "from analista.core import growth; g=growth.crescimento_log_linear([100,110,121,133.1]); print(round(g,4))"` | `0.1` | ✓ PASS |
| Suíte completa de testes | `.venv/bin/python -m pytest -q` | `171 passed in 1.71s` | ✓ PASS |

---

### Probe Execution

Step 7c: Nenhum probe-*.sh declarado nos planos; fase não é de migração/tooling. SKIPPED (sem probes convencionais).

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| GROW-01 | 10-01-PLAN.md | g histórico usa estimativa robusta, não CAGR endpoint-a-endpoint | ✓ SATISFIED | `crescimento_log_linear` em growth.py + swap em report.py; golden test_growth.py verde |
| GROW-02 | 10-02-PLAN.md | Screening calcula crescimento sobre série normalizada, não cagr_serie cru | ✓ SATISFIED | `crescimento_serie(attr)` em screening.py via log-linear/winsorizado + clamp do fit em comparables.py; test_growth_robusto_multiticker.py verde |

Nenhum requisito órfão: REQUIREMENTS.md mapeia apenas GROW-01 e GROW-02 para Phase 10, ambos cobertos pelos planos e satisfeitos.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/analista/core/growth.py` | 65 | Docstring afirma "Fronteira de None IDÊNTICA ao CAGR (D-03)" mas implementa fronteira MAIS ESTRITA: `cagr` retorna None só para endpoints ≤0; `crescimento_log_linear` retorna None para QUALQUER ponto interno ≤0 | ⚠️ WARNING (WR-02) | Documentação contraditória — empresa com lucro interno negativo mas extremidades positivas agora tem `g_historico = None` (antes teria g finito via CAGR). Impacto real em tickers cíclicos. Não afeta SC-5 (fronteira per-ano usa `lucros_raw`). Fix: corrigir docstring para "fronteira mais estrita que o CAGR: qualquer ponto interior ≤0 também retorna None". |
| `src/analista/report/report.py` | 406 | Label de usuário diz `"- g histórico (CAGR do lucro)"` após troca para regressão log-linear | ⚠️ WARNING (WR-04) | Infidelidade com o Core Value ("os números precisam ser fiéis ao método"): o label diz "CAGR" mas o cálculo é OLS log-linear. Fix: `"- g histórico (tendência log-linear do lucro)"`. |
| `src/analista/report/report.py` | 134 | Comentário `# média 3a + clamp 1.0 (função canônica única)` para `payout_valuation()` — desde Fase 9 a função retorna mediana da série completa SEM clamp | ⚠️ WARNING (WR-03) | Comentário factualmente errado induz o próximo mantenedor a achar que o DDM clampa o payout. Fix: `# mediana do payout sobre a série completa, SEM clamp (pode ser >1.0, ex. TAEE11)`. |
| `src/analista/core/comparables.py` | 154-155 | Comentário `"Mesmo clamp do Analisar antes do DDM (report.py: payout_proj = min(media_3a, 1.0))"` — o DDM não clampa payout desde Fase 9; a paridade declarada é falsa | ⚠️ WARNING (WR-03) | Comentário irmão do WR-03 acima: induz mantedor a achar que Analisar e Ranking clampam da mesma forma quando são deliberadamente diferentes. Fix: explicitar que o clamp é local ao domínio do fit e que o DDM intencionalmente não clampa. |
| `src/analista/core/growth.py` | 73-75 | Eixo de tempo `x = np.arange(len(serie))` assume espaçamento uniforme de 1 ano; series com anos faltantes (ex.: 2015,2016,2018,2019) são regredidas como se fossem consecutivas, gerando g mal-anualizado | ⚠️ WARNING (WR-01) | Defeito HERDADO do CAGR antigo (que usava `n = len-1` igualmente), agora exposto pela docstring que afirma "passo de x = 1 ano... anualizado por construção". Não é regressão introduzida por esta fase, mas a docstring nova cria um contrato que o pipeline não garante. Não afeta nenhum SC diretamente. Fix futuro: ancorar `x` aos anos reais. |

Nenhum marcador TBD/FIXME/XXX não-referenciado encontrado nos arquivos modificados.

---

### Human Verification Required

#### 1. Checkpoint live com 5 tickers reais (dados externos CVM/Yahoo/BCB)

**Test:**
```bash
.venv/bin/python -m analista.cli analisar VULC3
.venv/bin/python -m analista.cli analisar ITUB4
.venv/bin/python -m analista.cli analisar EGIE3
.venv/bin/python -m analista.cli analisar TAEE11
.venv/bin/python -m analista.cli analisar BBAS3
.venv/bin/python -m analista.cli rank --tickers VULC3,ITUB4,EGIE3,TAEE11,BBAS3
.venv/bin/python -m analista.cli screen --tickers VULC3,ITUB4,EGIE3,TAEE11,BBAS3
```

**Expected:**
- VULC3: `g histórico` exibido abaixo do CAGR endpoint cru (~47%); BSD não saturado pelo spike de 2025 pós-winsorização
- ITUB4/EGIE3/TAEE11/BBAS3: `g histórico` finito e positivo, sem colapso de ranqueamento
- TAEE11: preço-alvo de regressão finito e sensato; `b1` do fit não explodido por payout ~2.16
- BSD: buckets de `crescimento_*_3a` sem migração abrupta que distorça a ordenação

**Why human:** Chamadas a CVM, Yahoo Finance e BCB — não verificável programaticamente. O 10-03-SUMMARY.md documenta aprovação prévia do usuário com os números observados (VULC3 g=31,5% < CAGR 47,2%; TAEE11 P/L alvo 40,06; ranking sem colapso). Confirmar que o codebase atual segue produzindo resultados coerentes com dados frescos.

---

### Gaps Summary

Nenhum gap bloqueador. Todos os 5 success criteria do ROADMAP.md foram verificados no codebase. As 4 findings de WARNING (WR-01 a WR-04) identificadas na 10-REVIEW.md são defeitos reais mas nenhum invalida um success criterion:

- **WR-02** (docstring "IDÊNTICA ao CAGR"): a fronteira mais estrita é consistente com o PLAN (D-03 diz "qualquer ponto ≤0 → None"), apenas a afirmação de paridade com CAGR está errada. SC-5 (fronteira per-ano) usa `lucros_raw` e é genuinamente intocada.
- **WR-04** (label "CAGR do lucro"): problema de fidelidade de apresentação, não de cálculo.
- **WR-03** (comentários payout): stale, mas as funções chamadas são corretas.
- **WR-01** (espaçamento uniforme): defeito herdado, documentado para resolução futura.

Todos os 4 warnings são candidatos naturais para correção na **Phase 11** (foco em apresentação e fidelidade de labels). Não são necessários antes de avançar.

---

_Verified: 2026-06-27_
_Verifier: Claude (gsd-verifier)_
