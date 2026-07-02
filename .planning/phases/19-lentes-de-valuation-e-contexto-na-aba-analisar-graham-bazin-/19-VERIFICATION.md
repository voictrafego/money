---
phase: 19-lentes-de-valuation-e-contexto-na-aba-analisar-graham-bazin-
verified: 2026-07-02T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 19: Lentes de valuation e contexto na aba Analisar (Graham, Bazin) — Verification Report

**Phase Goal:** Adicionar, read-only e sem recalcular o método: (1) Preço-Justo de Graham
[√(22,5×LPA×VPA)] e Preço-Teto de Bazin [DPA médio 5a ÷ DY-mínimo 6%] como cards ao lado do
DDM; (2) "Quanto teria rendido" R$ 1.000 com reinvestimento de dividendos (Adj Close 5a); (3)
Comparador de pares do setor (tabela P/L, P/VP, ROE, DY, Valor de Mercado) reusando
comparables.py/multiples.py.

**Verified:** 2026-07-02
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Graham (VAL-01) card ao lado do DDM, com upside, degrada p/ "indisponível" | ✓ VERIFIED | `src/analista/core/lentes.py:37-48` `preco_justo_graham` implementa `√(22,5×LPA×VPA)` com degradação `lpa<=0 or vpa<=0 or None -> None`; `app.py:826-840` chama `lentes.vpa`+`lentes.preco_justo_graham` no branch Analisar, logo após m1..m5, com `st.metric`/`delta=upside` e ramo `else` "indisponível" + disclaimer. Golden `test_graham`/`test_graham_degrada` passam. |
| 2 | Bazin (VAL-02) card com upside, degrada quando sem histórico de dividendos | ✓ VERIFIED | `lentes.py:59-81` `dpa_medio`/`preco_teto_bazin` (DPA médio últimos 5a ÷ 0,06); `app.py:841-854` chama a cadeia e degrada com "indisponível" + "só vale para boas pagadoras". Golden `test_dpa_medio`/`test_bazin` passam. |
| 3 | "Quanto teria rendido" R$1.000 em 1a/5a via Adj Close, sem rede nova | ✓ VERIFIED | `lentes.py:97-131` `retorno_periodo` never-raise sobre `pd.Series`; `app.py:856-869` chama para `anos=1` e `anos=5` sobre `c.serie_precos_ajustada`, oculta janela `None`, caption neutra se ambas `None`. Fonte de dados: `prices.py:155` persiste `ajustado.dropna()` no MESMO bloco `try` de `tk.history` já existente (só 1 `tk.history` no arquivo) — zero chamada de rede nova confirmada por grep. `test_retorno_periodo` cobre valor conhecido + série curta + série vazia/None. |
| 4 | Comparador de pares (P/L, P/VP, ROE, DY, Valor de Mercado) com alvo destacado, degrada sem quebrar | ✓ VERIFIED | `lentes.py:137-206` `ParComparavel`/`metricas_par`/`tabela_pares`/`pares_suficientes`; `app.py:875-912` expander com `text_input` editável, monta a tabela com as 5 colunas exatas, destaca `➤` na linha `alvo`, `st.info` neutro quando insuficiente. `test_metricas_par`, `test_tabela_pares`, `test_pares_insuficientes` passam. |
| 5 | Copy exibe, nunca recomenda; 296 goldens seguem verdes; engine de método intocada | ✓ VERIFIED | `grep -i "compre\|venda"` no bloco novo não retorna linhas novas de recomendação; `pytest -q` → 307 passed (296 baseline + 11 novos, confirmado por execução direta); `git diff 50551cd~1 -- ddm.py multiples.py comparables.py screening.py report/report.py report/presentation.py` vazio. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/lentes.py` | Módulo puro com as 4 lentes | ✓ VERIFIED | Existe, 207 linhas, exporta `preco_justo_graham`, `vpa`, `dpa_medio`, `preco_teto_bazin`, `upside`, `retorno_periodo`, `ParComparavel`, `metricas_par`, `tabela_pares`, `pares_suficientes`; `GRAHAM_K=22.5`/`BAZIN_DY_MIN=0.06` presentes 1x cada; `from . import multiples as mult` confirmado. |
| `tests/test_lentes.py` | Golden tests das 4 lentes | ✓ VERIFIED | 11 funções de teste, todas passam isoladamente (`pytest tests/test_lentes.py -q` → 11 passed). |
| `src/analista/ingest/prices.py` | Campo `serie_precos_ajustada` em `DadosMercado` | ✓ VERIFIED | Campo declarado (linha 61) + atribuído em `coletar_mercado` (linha 155) no mesmo bloco try do `ajustado` pré-existente; `dm.serie_precos = nominal` intacto. |
| `src/analista/core/fundamentals.py` | Campo `serie_precos_ajustada` em `CompanyData` | ✓ VERIFIED | Campo declarado (linha 49), default `None`, posicionado após campos Optional existentes (não desloca args posicionais). |
| `src/analista/ingest/build.py` | Wiring `c.serie_precos_ajustada = dm.serie_precos_ajustada` | ✓ VERIFIED | Linha 65, único ponto de wiring, sem nova chamada de rede. |
| `app.py` | Render read-only das 4 lentes no branch Analisar | ✓ VERIFIED | `from analista.core import lentes` (linha 23); seção "Lentes de referência (além do DDM)" com 2 cards + bloco retorno + expander comparador (linhas 816-912); zero aritmética de método na view (`grep -c "22.5\|sqrt\|0.06" app.py` == 0). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `app.py` (branch Analisar) | `src/analista/core/lentes.py` | `lentes.preco_justo_graham/preco_teto_bazin/retorno_periodo/tabela_pares` | ✓ WIRED | Todas as 4 funções chamadas dentro do branch `if modo.startswith("Analisar")`, resultado usado em `st.metric`/`st.markdown`/`st.dataframe` (não descartado). |
| `app.py` (retorno) | `c.serie_precos_ajustada` | `retorno_periodo(c.serie_precos_ajustada, anos)` | ✓ WIRED | `app.py:859-860` passa `c.serie_precos_ajustada` diretamente para `retorno_periodo` para `anos=1` e `anos=5`. |
| `src/analista/ingest/build.py` | `src/analista/core/fundamentals.py` | `c.serie_precos_ajustada = dm.serie_precos_ajustada` | ✓ WIRED | Confirmado por grep exato, 1 ocorrência. |
| `src/analista/core/lentes.py` | `src/analista/core/multiples.py` | reuso de `preco_lucro`/`_safe_div` (sem duplicar fórmula) | ✓ WIRED | `mult.preco_lucro` usado em `metricas_par`; `mult._safe_div` usado em `vpa`/`preco_teto_bazin`/`metricas_par` (pvp). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| Card Graham | `graham` | `lentes.preco_justo_graham(c.lpa_valuation(), lentes.vpa(...))` sobre `CompanyData` real vindo de `montar()` (fetch CVM/Yahoo) | Sim — dados reais de `c.patrimonio_liquido`/`c.num_acoes`/`c.lpa_valuation()` populados por `build.montar_empresa` | ✓ FLOWING |
| Card Bazin | `bazin` | `lentes.preco_teto_bazin(lentes.dpa_medio([c.dpa(ano) for ano in c.anos_ordenados()]))` | Sim — `c.dpa(ano)` deriva de `c.dividendos`/`c.num_acoes` reais | ✓ FLOWING |
| Bloco retorno | `_r1`/`_r5` | `lentes.retorno_periodo(c.serie_precos_ajustada, anos=...)`; `c.serie_precos_ajustada` vem de `dm.serie_precos_ajustada` = `ajustado.dropna()` do `tk.history` real | Sim — série real do Yahoo (mesma fonte do gráfico/beta), não estática | ✓ FLOWING |
| Tabela de pares | `_tabela_pares` | `lentes.tabela_pares([lentes.metricas_par(cp) for cp in _companies_pares], ticker_ativo)`; `_companies_pares` vem de `montar(_t, ...)` por ticker (fetch real, cacheado) | Sim — cada `ParComparavel` deriva de `CompanyData` real buscado por ticker | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Graham fórmula bate valor conhecido | `pytest tests/test_lentes.py::test_graham -q` | 1 passed | ✓ PASS |
| Bazin fórmula bate valor conhecido | `pytest tests/test_lentes.py::test_bazin -q` | 1 passed | ✓ PASS |
| Retorno periodo (janela real + insuficiente + vazia) | `pytest tests/test_lentes.py::test_retorno_periodo -q` | 1 passed | ✓ PASS |
| Comparador marca alvo e degrada | `pytest tests/test_lentes.py::test_tabela_pares tests/test_lentes.py::test_pares_insuficientes -q` | 2 passed | ✓ PASS |
| Suíte completa (regressão) | `.venv/bin/python -m pytest -q` | 307 passed | ✓ PASS |
| Sintaxe de app.py | `python -c "import ast; ast.parse(open('app.py').read())"` | sem erro | ✓ PASS |
| Zero dependência nova | `git diff 50551cd~1 -- requirements.txt` | vazio | ✓ PASS |
| Engine de método intocada | `git diff 50551cd~1 -- ddm.py multiples.py comparables.py screening.py report/report.py report/presentation.py` | vazio | ✓ PASS |
| Zero chamada de rede nova em ingestão | `grep -c "tk.history" prices.py` == 1 | 1 | ✓ PASS |

### Probe Execution

Não aplicável — fase não declara probes (`scripts/*/tests/probe-*.sh`); verificação usa pytest + grep de invariantes, conforme o próprio 19-04-PLAN.md.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| VAL-01 | 19-01, 19-03 | Preço-Justo de Graham como card, com upside, degrada sem quebrar | ✓ SATISFIED | `lentes.preco_justo_graham` + card em `app.py:827-840`; golden `test_graham*`. |
| VAL-02 | 19-01, 19-03 | Preço-Teto de Bazin como card, com upside, degrada sem quebrar | ✓ SATISFIED | `lentes.preco_teto_bazin`/`dpa_medio` + card em `app.py:841-854`; golden `test_bazin`/`test_dpa_medio`. |
| RET-01 | 19-01, 19-02, 19-03 | "Quanto teria rendido" R$1.000 via Adj Close, sem rede nova, degrada quando histórico insuficiente | ✓ SATISFIED | `lentes.retorno_periodo` + `serie_precos_ajustada` (prices/fundamentals/build) + bloco em `app.py:856-869`; golden `test_retorno_periodo`; zero chamada de rede nova confirmada. |
| PEER-01 | 19-01, 19-03 | Comparador de pares (P/L, P/VP, ROE, DY, Valor de Mercado), destaca alvo, degrada sem quebrar, não recomenda | ✓ SATISFIED | `lentes.metricas_par`/`tabela_pares`/`pares_suficientes` + expander em `app.py:875-912`; golden `test_tabela_pares`/`test_pares_insuficientes`. Nota abaixo sobre reuso de `comparables.py`. |

Nenhum requisito órfão: os 4 IDs mapeados à Fase 19 em REQUIREMENTS.md (linhas 104-107, 147-150)
aparecem no campo `requirements` de todos os 4 planos e têm evidência de implementação.

**Nota sobre PEER-01 — reuso de `comparables.py`:** o texto de REQUIREMENTS.md/ROADMAP.md diz
"reusando comparables.py/multiples.py". Na prática, `lentes.py` importa e reusa apenas
`multiples.py` (`preco_lucro`, `_safe_div`); `comparables.py` permanece intocado
(`git diff --quiet` confirmado) e serve só de referência de estilo, não de import. Isso foi uma
decisão explícita tomada em fase de planejamento (19-01-PLAN.md, Task 2: "NÃO alterar
comparables.py ... reuso é por import de multiples") — `comparables.py` contém lógica de
ranking/regressão (Cap. 11/12) que produziria nota/veredito, o que violaria a exigência
"não emite recomendação" desta fase. O resultado funcional (tabela com as 5 métricas exigidas,
alvo destacado, degradação graciosa, sem recomendação) está integralmente satisfeito. Não é
tratado como gap porque a decisão foi documentada no PLAN antes da execução (não uma
descoberta pós-hoc do verificador), mas fica registrado aqui para rastreabilidade.

### Anti-Patterns Found

Nenhum bloqueador. Varredura em `src/analista/core/lentes.py`, `tests/test_lentes.py`,
`src/analista/ingest/prices.py`, `src/analista/core/fundamentals.py`,
`src/analista/ingest/build.py` e `app.py` (seções novas) não encontrou `TBD`/`FIXME`/`XXX`/
`TODO`/`HACK`/`PLACEHOLDER` genuínos (os 2 hits de grep — "TODOS" em português e um "XXXX" de
exemplo de escape JSON — são falsos positivos, não marcadores de débito técnico).

### Human Verification Required

Nenhum item pendente. O checkpoint humano bloqueante do plano 19-04 (Task 2, smoke no
navegador: Graham/Bazin/retorno/comparador na aba Analisar + ausência de regressão nas demais
abas) já foi executado durante a fase e aprovado explicitamente pelo usuário
("approved", registrado em `19-04-SUMMARY.md`). Não há evidência de que esse gate tenha sido
pulado — é um checkpoint interativo real do workflow de execução, distinto de uma alegação de
SUMMARY não verificável.

### Gaps Summary

Nenhum gap encontrado. Todos os must-haves (roadmap + frontmatter dos 4 planos) foram
verificados diretamente no código: engine pura com degradação never-raise, dado real
(Adj Close) propagado sem nova chamada de rede, render read-only em `app.py` sem nenhuma
fórmula de Graham/Bazin na view, suíte completa em 307 (296 baseline + 11 novos), zero
dependência nova, e nenhum módulo de método (ddm/multiples/comparables/screening/report/
presentation) alterado.

---

_Verified: 2026-07-02_
_Verifier: Claude (gsd-verifier)_
</content>
