---
phase: 01-engine-de-consist-ncia
verified: 2026-06-05T15:00:00Z
status: passed
score: 5/5
overrides_applied: 0
---

# Phase 01: Engine de Consistência — Verification Report

**Phase Goal:** A engine produz, na origem, números coerentes entre os três modos (Analisar, Garimpar BSD, Ranking por múltiplos): mesma janela de payout, BSD reproduzível e absoluto, fatores ausentes neutros, ROE/DY com base correta e regressão robusta.
**Verified:** 2026-06-05T15:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A mesma ação tem o mesmo BSD independentemente de quais outros tickers estão no lote (referência fixa, não min-max do lote); "BSD > 80" volta a ser corte absoluto | VERIFIED | `REFERENCIA_BSD` em `screening.py:191` — 10 bandas fixas calibráveis; `_padronizar_absoluto` em `screening.py:292`; smoke confirma diff=0.00e+00 entre lote de 1 e lote de 3 |
| 2 | Para a mesma ação, o payout que decide o preço-alvo no Ranking é o mesmo (mesma janela e clamp, função única — `CompanyData.payout_valuation`) que decide o valor intrínseco no Analisar | VERIFIED | `fundamentals.py:73` — `payout_valuation(janela=3)` clampa em 1.0; `report.py:97` — DDM usa `c.payout_valuation()`; `app.py:264` — Ranking usa `c.payout_valuation()`; `_media_payout_3a` removido de report.py |
| 3 | No Garimpo, uma ação com DY abaixo da Selic não aparece recomendada no topo — ordena/filtra por "Passa filtros" | VERIFIED | `app.py:224` — `sort_values(["_passou", "BSD"], ascending=[False, False])`; `app.py:227-229` — aviso explícito "BSD > 80 sem 'Passa filtros' NÃO é recomendação"; `test_filtros_customizados_dy_abaixo_da_selic` confirma |
| 4 | Fatores do BSD com dado ausente entram como neutro/ausente (não 0/pior); DY corrente usa dividendos trailing-12m; ROE usa a mesma base de PL em todos os anos da série | VERIFIED | `screening.py:303-304` — `None → 50.0` (neutro); `fundamentals.py:101-109` — `dy_atual()` usa `dpa_trailing_12m` quando disponível; `fundamentals.py:88-99` — `roe()` usa PL médio, None sem PL inicial; `build.py:39-40` — propaga `dpa_trailing_12m` e `ano_dpa` |
| 5 | O Ranking aplica o mesmo clamp/alerta de payout fora de [0,1] que o Analisar antes da regressão; o intervalo de valor intrínseco vem de um único cálculo (vmin/vmax, sem recomputar min/max em dois lugares) | VERIFIED | `comparables.py:132-134` — `dp_clamp = min(max(dp, 0.0), 1.0)`; `comparables.py:115` — `payout_fora_faixa: bool = False`; `report.py:115-117` — `a.vmin, a.vmax = min(valores), max(valores)` (único cálculo); `app.py:107` — `fmt_rs(a.vmin)` lê campo diretamente |

**Score:** 5/5 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/fundamentals.py` | `payout_valuation`, `roe` PL médio, `dy_atual` trailing-12m, campos `dpa_trailing_12m`/`ano_dpa` | VERIFIED | Linha 73: `payout_valuation`; linha 88: `roe` (PL médio, None sem PL inicial); linha 101: `dy_atual`; linhas 47-48: campos `dpa_trailing_12m`/`ano_dpa` |
| `src/analista/ingest/prices.py` | `DadosMercado.dpa_trailing_12m`/`ano_dpa` calculados das datas reais de `tk.dividends` | VERIFIED | Linhas 41-42: campos declarados; linhas 106-112: cálculo trailing-12m por datas reais |
| `src/analista/ingest/build.py` | `montar_empresa` propaga `dpa_trailing_12m` e `ano_dpa` para `CompanyData` | VERIFIED | Linhas 39-40: propagação explícita `c.dpa_trailing_12m = dm.dpa_trailing_12m` e `c.ano_dpa = dm.ano_dpa` |
| `src/analista/core/comparables.py` | Clamp/sinalização de payout fora de [0,1] em `preco_alvo_por_regressao`; `PrecoAlvo.payout_fora_faixa` | VERIFIED | Linhas 132-134: clamp `min(max(dp,0),1)`; linha 115: `payout_fora_faixa: bool = False` |
| `src/analista/core/screening.py` | `REFERENCIA_BSD` (10 bandas fixas), `_padronizar_absoluto` (None→50 neutro), `bsd_ranking` absoluto + `fatores_faltantes`/`n_fatores_faltantes` | VERIFIED | Linha 191: `REFERENCIA_BSD`; linha 292: `_padronizar_absoluto`; linha 303: `notas.append(50.0)` para None; linhas 361-370: `fatores_faltantes` e `n_fatores_faltantes` |
| `src/analista/report/report.py` | `analisar_acao` usa `payout_valuation`; `AnaliseAcao.vmin`/`vmax` expostos do cálculo único | VERIFIED | Linha 97: `payout_proj = c.payout_valuation()`; linhas 37-38: `vmin`/`vmax` em `AnaliseAcao`; linhas 115-117: cálculo único `a.vmin, a.vmax = min(valores), max(valores)` |
| `app.py` | Garimpo ordena por `Passa filtros`; Ranking usa `payout_valuation`; Analisar lê `a.vmin`/`a.vmax` | VERIFIED | Linha 224: `sort_values(["_passou","BSD"])`; linha 264: `DP.append(c.payout_valuation())`; linha 271: `cmp.preco_alvo_por_regressao(reg, c.payout_valuation(), ...)`; linha 107: `fmt_rs(a.vmin)` |
| `src/analista/glossario.py` | Tooltip BSD com referência absoluta, proxy de crescimento e fatores neutros; tooltip ROE com PL médio | VERIFIED | Tooltip "bsd" descreve: corte absoluto, proxy ROE×(1-payout) por fundamentos, fatores ausentes neutros; tooltip "roe" descreve PL médio |
| `tests/test_fundamentals_consistencia.py` | Testes das 3 funções canônicas (payout_valuation, roe base, dy_atual trailing-12m) | VERIFIED | 9 testes, todos passando; cobertura: clamp, janela 3a, None-ignoring, ROE-None-1º-ano, PL-médio, trailing-12m, fallback, ano_dpa |
| `tests/test_screening.py` | Testes BSD atualizados para comportamento absoluto + reprodutibilidade + fatores faltantes | VERIFIED | `test_bsd_ranking_ordena_e_marca_acima_80`, `test_bsd_corte_80_absoluto_via_padronizar`, `test_bsd_reprodutivel_entre_lotes`, `test_bsd_fatores_faltantes_neutros` — todos passando |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `fundamentals.py::payout_valuation` | `report.analisar_acao` | `c.payout_valuation()` chamado em report.py:97 | WIRED | Único ponto de entrada; `_media_payout_3a` removido do módulo |
| `fundamentals.py::payout_valuation` | `app.py Ranking` | `c.payout_valuation()` em app.py:264,271 | WIRED | Vetor DP e dp do preço-alvo via função canônica |
| `prices.py::dpa_trailing_12m` | `CompanyData.dpa_trailing_12m` | `build.montar_empresa` propagação explícita | WIRED | build.py:39: `c.dpa_trailing_12m = dm.dpa_trailing_12m` |
| `report.py::AnaliseAcao.vmin/vmax` | `app.py métrica de valor intrínseco` | `a.vmin`/`a.vmax` lidos em app.py:107 | WIRED | Não recomputa min/max; fallback "—" quando None |
| `comparables.py::preco_alvo_por_regressao` | regressão P/L com clamp | `dp_clamp = min(max(dp,0),1)` antes de `reg.prever` | WIRED | comparables.py:133-135; `payout_fora_faixa` sinalizado em app.py:280 |
| `app.py Garimpo` | `filtros_customizados` (corte Selic) | `sort_values(["_passou","BSD"], ascending=[False,False])` | WIRED | app.py:224; empresas que reprovam no corte Selic ficam abaixo na tabela |
| `screening.py::REFERENCIA_BSD` | padronização BSD absoluta | `_padronizar_absoluto(coluna, lo, hi)` por fator | WIRED | screening.py:352-353; sem re-padronização min-max do lote |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `app.py` Garimpo tabela | `rc.passou` (Passa filtros) | `filtros_customizados(c, selic=...)` — usa `c.dy_atual()` | Sim — `dy_atual()` usa `dpa_trailing_12m` (trailing real) ou fallback | FLOWING |
| `app.py` Ranking DP vector | `c.payout_valuation()` | `CompanyData.payout_valuation` — média 3 últimos anos reais do CompanyData | Sim — dados vêm do CompanyData montado via CVM/yfinance | FLOWING |
| `app.py` Analisar intervalo | `a.vmin`/`a.vmax` | `report.analisar_acao` — calculado uma vez em report.py:115-117 | Sim — campo exposto; app lê diretamente | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| BSD reproducibility between lots | Python smoke: `bsd_sozinha` vs `bsd_no_lote` for same company | `diff = 0.00e+00` | PASS |
| payout_valuation clamps at 1.0 | Python smoke: 150% payout → `payout_valuation()` | Returns `1.0` | PASS |
| ROE None in first year (no PL base) | Python smoke: `roe(2023)` without PL 2022 | `None` | PASS |
| DY trailing-12m | Python smoke: `dpa_trailing_12m=0.8`, `preco_atual=10` | `0.0800` | PASS |
| BSD absent factor → neutral 50 | Python smoke: `_padronizar_absoluto([None], lo, hi)` | `50.0` | PASS |
| Selic cut excludes DY < Selic | Python smoke: company with DY 0.3% vs Selic 10.5% | `passou=False`, `dy_acima_corte=False` | PASS |
| Ranking payout clamp and flag | Python smoke: `preco_alvo_por_regressao(reg, dp=1.5, ...)` | Same price as `dp=1.0`; `payout_fora_faixa=True` | PASS |
| `app.py` syntax valid | `ast.parse(open('app.py').read())` | No SyntaxError | PASS |

---

## Probe Execution

Step 7c: No probe scripts found or declared for this phase. N/A.

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| GARIMPO-01 | 01-05-PLAN.md | Garimpo respeita corte Selic — DY < Selic não recomendado no topo | SATISFIED | `app.py:224` sort por `_passou` antes de BSD; `app.py:227` aviso explícito |
| GARIMPO-02 | 01-03-PLAN.md | BSD padronizado contra referência fixa, não min-max do lote | SATISFIED | `REFERENCIA_BSD` + `_padronizar_absoluto`; smoke zero-diff entre lotes |
| GARIMPO-03 | 01-03-PLAN.md | Fatores BSD ausentes como neutro; app indica quantos faltaram | SATISFIED | `screening.py:303` None→50; `bsd_ranking` expõe `fatores_faltantes`/`n_fatores_faltantes` |
| GARIMPO-04 | 01-03-PLAN.md | Proxy crescimento BSD usa mesma janela `anos_media` e documentado no tooltip | SATISFIED | `screening.py:256-258` usa média na janela `anos_media`; tooltip BSD atualizado |
| PAYOUT-01 | 01-01, 01-04, 01-05 | Analisar e Ranking usam mesma janela e clamp de payout — função única | SATISFIED | `fundamentals.py:73` `payout_valuation`; `report.py:97` e `app.py:264` consomem; `_media_payout_3a` removido |
| RANK-02 | 01-02, 01-05 | Ranking aplica mesmo clamp/alerta de payout fora de [0,1] que o Analisar | SATISFIED | `comparables.py:132-134` clamp; `comparables.py:115` flag; `app.py:280` sinaliza na tabela |
| ROE-01 | 01-01-PLAN.md | ROE usa mesma base (PL médio) em todos os anos; glossário alinhado | SATISFIED | `fundamentals.py:88-99` PL médio; None no 1º ano; `glossario.py` tooltip alinhado |
| DY-01 | 01-01-PLAN.md | DY do Garimpo usa dividendos trailing-12m | SATISFIED | `fundamentals.py:101-109` trailing-12m com fallback; `prices.py:106-112` cálculo das datas reais; `build.py:39` propagação |
| VAL-01 | 01-04, 01-05 | Intervalo de valor intrínseco vem de único cálculo, sem recomputar em dois lugares | SATISFIED | `report.py:115-117` único `min(valores)/max(valores)` → `a.vmin`/`a.vmax`; `app.py:107` lê campos |

**Coverage:** 9/9 Phase 1 requirements SATISFIED.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `app.py` | 81 | `placeholder=` (Streamlit API parameter) | Info | UI placeholder de exemplo de ticker — não é stub de código, é argumento de componente Streamlit |

No debt markers (TBD/FIXME/XXX) found in any file modified by this phase.
No stub implementations (empty returns, hardcoded empty data flowing to rendering) found.

---

## Hard Constraint: Golden Tests

```
44 passed in 0.05s
```

All 44 tests pass:
- `tests/test_ddm.py` — 7 golden tests (unchanged)
- `tests/test_multiples.py` — 11 golden tests (unchanged)
- `tests/test_comparables.py` — 3 golden tests + 3 new (clamp/flag)
- `tests/test_screening.py` — 5 original + 4 rewritten/new (BSD absolute + reprodutibilidade + faltantes)
- `tests/test_fundamentals_consistencia.py` — 9 new (payout_valuation, roe base, dy_atual trailing-12m)

Hard constraint SATISFIED: golden tests in `tests/` continue passing.

---

## Human Verification Required

The plan included one human-gated checkpoint (Plan 05, Task 3) for visual/functional verification of the three modes in the browser. The SUMMARY.md documents this as having been completed with the user responding "approved". Since this verification is goal-backward (verifying what the codebase delivers), and the programmatic evidence is comprehensive, no further human testing is surfaced here.

Items that remain inherently human-verifiable for Phase 2 (not Phase 1 scope):
- Visual appearance of "indisponível" vs "—" in the Ranking table (RANK-01, Phase 2)
- Year-base display in Ranking/Garimpo (ANO-01, Phase 2)

---

## Gaps Summary

No gaps. All 5 success criteria are VERIFIED with multi-level evidence:

1. **SC-01 (BSD absoluto):** `REFERENCIA_BSD` with 10 fixed bands replaces min-max normalization; smoke confirms zero diff between single and multi-company batches.
2. **SC-02 (payout único):** `CompanyData.payout_valuation()` is the sole definition; `_media_payout_3a` removed from report.py; both Analisar (report.py:97) and Ranking (app.py:264,271) consume it.
3. **SC-03 (Garimpo Selic cut):** `sort_values(["_passou","BSD"])` puts filter-passing companies first; warning banner present; `filtros_customizados` uses `dy_atual()` for the Selic comparison.
4. **SC-04 (absent factors neutral; DY trailing-12m; ROE consistent PL):** `_padronizar_absoluto` maps None to 50; `dpa_trailing_12m` propagated prices→build→CompanyData; `roe()` returns None for first year without prior PL, PL médio for subsequent years.
5. **SC-05 (clamp/vmin/vmax single calculation):** `preco_alvo_por_regressao` clamps dp before `reg.prever`; `AnaliseAcao.vmin`/`vmax` assigned once in report.py; app.py reads fields directly.

---

_Verified: 2026-06-05T15:00:00Z_
_Verifier: Claude (gsd-verifier)_
