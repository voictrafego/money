---
phase: 21-comparador-multi-ativo-lado-a-lado-m-ltiplos-selo-por-coluna
verified: 2026-07-03T00:00:00Z
status: human_needed
score: 7/7 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Smoke visual do 5º menu 'Comparar ações' com dados reais/rede."
    expected: "Ao digitar 3 tickers do mesmo setor (ex.: TAEE11, EGIE3, CMIG4) e a página carregar, a tabela renderiza com os 3 tickers nas colunas, o Selo (badge com emoji+rótulo) na primeira linha de cada coluna, os 5 múltiplos abaixo, '—' em métrica ausente, e sem erros visuais no Streamlit (progress bar aparece e some, dataframe não quebra o layout)."
    why_human: "Depende de renderização real do Streamlit e de fetch de rede ao vivo (Yahoo/CVM) — não verificável por grep/pytest. O próprio plano (21-01-PLAN.md, bloco <verification>) declara este smoke como checkpoint humano fora do escopo automatizável do plano."
---

# Phase 21: Comparador multi-ativo lado a lado (múltiplos + selo por coluna) — Verification Report

**Phase Goal:** Promover o embrião "Comparador de pares" a um comparador lado a lado de N tickers escolhidos pelo usuário — 5º menu dedicado — exibindo os 5 múltiplos (P/L, P/VP, ROE, DY, Valor de Mercado) e o Selo COMPLETO da Phase 20 (quadrante) por coluna.
**Verified:** 2026-07-03
**Status:** human_needed (todos os checks automatizados passaram; falta apenas o smoke visual/rede que o próprio plano reserva para humano)
**Re-verification:** No — verificação inicial

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Existe um 5º item "Comparar ações" no menu lateral, abrindo página dedicada | ✓ VERIFIED | `app.py:591` adiciona `"Comparar ações"` à lista do `st.sidebar.radio`; `app.py:1395` `elif modo.startswith("Comparar"):` abre o bloco dedicado |
| 2 | Entrada de N tickers normalizada (upper + dedup preservando ordem + cap soft de 6) | ✓ VERIFIED | `lentes.normalizar_tickers` em `src/analista/core/lentes.py:199-208`; chamado em `app.py:1402` com `cap=6`; 5 testes cobrindo todos os comportamentos em `tests/test_lentes.py:169-198`; checagem manual `normalizar_tickers('TAEE11, taee11 EGIE3', 6)==['TAEE11','EGIE3']` → OK |
| 3 | Com ≥2 tickers resolvidos, tabela com tickers em COLUNAS e métricas em LINHAS | ✓ VERIFIED | `comparador.montar_comparativo` (`src/analista/report/comparador.py:81-96`) monta `pd.DataFrame` via dict-de-dicts + `.reindex(_ORDEM_LINHAS)`; `test_transposto_colunas_sao_tickers_e_linhas_ordem_fixa` assevera `df.columns == tickers` e `df.index == ORDEM_FIXA` |
| 4 | Cada coluna mostra Selo COMPLETO (quadrante) no topo + P/L, P/VP, ROE, DY, Valor de Mercado | ✓ VERIFIED | `_ORDEM_LINHAS = ["Selo","P/L","P/VP","ROE","DY","Valor de Mercado"]`; `_selo_completo()` usa `report.analisar_acao(c, cfg).selo` + `presentation.selo_badge(...)` (NÃO o atalho só-cor); `test_linha_selo_e_o_badge_completo_nao_so_a_cor` compara a célula com o badge completo esperado |
| 5 | Métrica/selo faltante → "—"; <2 tickers resolvidos → st.info neutro (sem tabela) | ✓ VERIFIED | Degradação testada em `test_metrica_ausente_vira_em_dash_e_valor_mercado_em_bilhoes` e `test_never_raise_contexto_quebrado_degrada_so_a_coluna`; `app.py:1413-1417` faz `if tabela.suficiente: st.dataframe(...) else: st.info(...)` |
| 6 | Sem sort/ranking/ticker-alvo/destaque — ordem de entrada preservada | ✓ VERIFIED | `montar_comparativo` não ordena (acumula em dict na ordem de iteração de `contextos`); `test_ordem_das_colunas_preserva_entrada_sem_sort_nem_alvo` confirma `df.columns == ["CCCC3","AAAA3","BBBB3"]` (ordem de entrada) e ausência de "➤" |
| 7 | Suíte de testes golden 100% verde | ✓ VERIFIED | `python -m pytest tests/ -q` → **338 passed** (rodado ao vivo nesta verificação, não copiado do SUMMARY) |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/lentes.py` | `normalizar_tickers(texto, cap)` never-raise, upper+dedup(ordem)+cap | ✓ VERIFIED | Linhas 199-208; `grep -n "def normalizar_tickers("` → 1 match; lógica confirmada por leitura direta |
| `src/analista/report/presentation.py` | `fmt_rs` ptBR de reais, fonte única | ✓ VERIFIED | Linhas 31-38; idêntica ao `fmt_rs` original de `app.py:252-253` (comparação byte-a-byte da expressão de formatação) |
| `src/analista/report/comparador.py` | `montar_comparativo` DataFrame transposto + `.suficiente` ≥2, never-raise, usa selo COMPLETO | ✓ VERIFIED | Módulo novo, 97 linhas; `grep -c "analisar_acao\|selo_badge"` = 5 (usa a porta correta); `grep -c "selo_emoji\|cor_do_bsd"` = 0 (não usa o atalho só-cor); `grep -c "import app\|from app\|montar("` = 0 (não importa app nem faz fetch) |
| `tests/test_comparador.py` | Cobertura de transposição, selo por coluna, degradação, suficiência | ✓ VERIFIED | Módulo novo, 9 testes cobrindo todos os comportamentos do plano (transposição, selo completo, métrica ausente, ordem preservada, suficiência ≥2, never-raise) |
| `app.py` | Item "Comparar ações" no sidebar + `elif modo.startswith("Comparar")` read-only | ✓ VERIFIED | Sidebar (linha 591) + bloco elif (linhas 1395-1417); nenhuma fórmula/threshold/montagem de tabela no bloco — só `normalizar_tickers`, `montar()` cacheado e `comparador.montar_comparativo` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `app.py` (bloco Comparar) | `lentes.normalizar_tickers` | parse do `st.text_input` | ✓ WIRED | `app.py:1402`: `_cmp_tickers = lentes.normalizar_tickers(_cmp_txt, 6)` |
| `app.py` (bloco Comparar) | `montar(ticker, ANO_BASE, N_ANOS)` | loop de fetch cacheado | ✓ WIRED | `app.py:1407`: `c = montar(t, ANO_BASE, N_ANOS)` dentro do loop `for i, t in enumerate(_cmp_tickers)` |
| `app.py` (bloco Comparar) | `comparador.montar_comparativo` | montagem da tabela na engine | ✓ WIRED | `app.py:1412`: `_cmp_tabela = comparador.montar_comparativo(_cmp_contextos, CFG)`; import em `app.py:28` |
| `src/analista/report/comparador.py` | `report.analisar_acao(...).selo` + `presentation.selo_badge` | selo COMPLETO por coluna | ✓ WIRED | `comparador.py:46-50`: `a = report.analisar_acao(c, cfg)`; `presentation.selo_badge(a.selo.cor, a.selo.rotulo, a.selo.qualidade, a.selo.verificar)` |
| `src/analista/report/comparador.py` | `lentes.metricas_par` | 5 múltiplos por ticker | ✓ WIRED | `comparador.py:60`: `p = lentes.metricas_par(c)` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `_cmp_tabela.df` (app.py:1412) | `_cmp_contextos` (lista de `CompanyData`) | `montar(t, ANO_BASE, N_ANOS)` — fetch real cacheado, reusa a única porta de rede já existente (Ranking/Analisar) | Sim — `montar()` não é novo nesta fase; já produz dados reais de CVM/Yahoo em produção | ✓ FLOWING (herdado, não modificado) |
| Célula "Selo" | `a.selo` | `report.analisar_acao(c, cfg)` — engine CPU-pura já existente (Phase 20) | Sim — reusa a mesma porta que já alimenta Selo em Analisar/Garimpo/Ranking | ✓ FLOWING |

Nenhum prop hardcoded vazio encontrado no caminho `app.py → comparador.montar_comparativo` — `_cmp_contextos` é preenchido pelo loop de fetch antes de ser passado à engine.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `normalizar_tickers` dedup+upper+cap | `python -c "from analista.core import lentes; assert lentes.normalizar_tickers('TAEE11, taee11 EGIE3', 6)==['TAEE11','EGIE3']"` | exit 0, sem AssertionError | ✓ PASS |
| `app.py` compila (sintaxe válida) | `python -c "import ast; ast.parse(open('app.py').read())"` | exit 0 | ✓ PASS |
| Suíte completa | `python -m pytest tests/ -q` | `338 passed in 3.21s` | ✓ PASS |
| Render Streamlit real (5º menu) | requer `streamlit run app.py` + navegador | não executável neste ambiente (sem servidor/rede ao vivo) | ? SKIP — roteado para verificação humana |

### Probe Execution

Não há probes convencionais (`scripts/*/tests/probe-*.sh`) neste projeto nem referências a probes no PLAN/SUMMARY da fase. Step 7c: SKIPPED (fase não é migração/CLI e não declara probes).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| COMP-01 | 21-01-PLAN.md | Entrada de N tickers normalizada (upper+dedup+cap) | ✓ SATISFIED | `lentes.normalizar_tickers`, testado, chamado em `app.py:1402` |
| COMP-02 | 21-01-PLAN.md | Tabela comparativa de múltiplos, tickers em colunas | ✓ SATISFIED | `comparador.montar_comparativo` — DataFrame transposto testado |
| COMP-03 | 21-01-PLAN.md | Selo COMPLETO por coluna | ✓ SATISFIED | `_selo_completo()` usa `analisar_acao(...).selo` + `selo_badge`, testado explicitamente contra o atalho só-cor |

**Nota sobre REQUIREMENTS.md:** o arquivo `.planning/REQUIREMENTS.md` documenta formalmente até v1.7 (VAL/RET/PEER) e não contém entradas explícitas para COMP-01/02/03 (nem para SELO-01/02/03 da Phase 20). Isso é uma lacuna de rastreabilidade PRÉ-EXISTENTE no arquivo de requisitos (não introduzida por esta fase) — as descrições completas de COMP-01/02/03 estão em `.planning/ROADMAP.md:237-243` e no frontmatter do próprio plano, ambos usados como fonte de verdade nesta verificação. Não bloqueia o veredito da Phase 21, mas fica registrado como item de higiene do projeto.

### Anti-Patterns Found

Nenhum encontrado nos arquivos modificados/criados pela fase (`lentes.py`, `presentation.py`, `comparador.py`, `app.py`, `test_lentes.py`, `test_comparador.py`): sem `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`, sem `return null`/`{}`/`[]` órfãos, sem props hardcoded vazias no caminho de dados do comparador.

### Gate Checks (executados ao vivo, não copiados do SUMMARY)

| Gate | Comando | Resultado |
|------|---------|-----------|
| `normalizar_tickers` existe (1 match) | `grep -n "def normalizar_tickers(" src/analista/core/lentes.py` | 1 match ✓ |
| Testes de `normalizar_tickers` | `grep -c "normalizar_tickers" tests/test_lentes.py` | 14 ✓ |
| `fmt_rs` existe (1 match) | `grep -n "def fmt_rs(" src/analista/report/presentation.py` | 1 match ✓ |
| `montar_comparativo` existe (1 match) | `grep -n "def montar_comparativo(" src/analista/report/comparador.py` | 1 match ✓ |
| Usa porta correta do selo | `grep -c "analisar_acao\|selo_badge" src/analista/report/comparador.py` | 5 (≥1) ✓ |
| NÃO usa atalho só-cor | `grep -c "selo_emoji\|cor_do_bsd" src/analista/report/comparador.py` | 0 ✓ |
| NÃO importa app nem faz fetch | `grep -c "import app\|from app\|montar(" src/analista/report/comparador.py` | 0 ✓ |
| 5º menu elif (1 match) | `grep -c 'elif modo.startswith("Comparar")' app.py` | 1 ✓ |
| Item no sidebar (1 match) | `grep -c '"Comparar ações"' app.py` | 1 ✓ |
| Import + chamada comparador (≥2) | `grep -c "comparador" app.py` | 5 (≥2) ✓ |
| Parse não reimplementado na view (1 match) | `grep -c "lentes.normalizar_tickers" app.py` | 1 ✓ |
| Loop reusa fetch cacheado (≥2) | `grep -c "montar(t, ANO_BASE, N_ANOS)" app.py` | 3 (≥2) ✓ |
| Expander "Comparador de pares (contexto)" intacto | `grep -c "Comparador de pares (contexto)" app.py` (esperado 1 pelo plano) | **2** — gate do plano é impreciso (a string já aparecia 2x na baseline: comentário + título do expander). Verificado via `git diff 4a231dc~1 4a231dc -- app.py`: o diff da Task 3 NÃO toca as linhas do expander (938-979) — apenas adiciona import, item no sidebar radio e o novo bloco `elif`. Expander confirmado intacto por comparação de diff, não pela contagem literal. ✓ |
| Suíte golden completa | `python -m pytest tests/ -q` | **338 passed** ✓ |
| `app.py` compila | `python -c "import ast; ast.parse(open('app.py').read())"` | exit 0 ✓ |
| Zero deps 3rd-party novas | `git diff HEAD~6 HEAD -- requirements.txt pyproject.toml setup.py` | diff vazio ✓ |

Todos os gates do plano se sustentam (a exceção documentada — contagem do expander — foi investigada e confirmada como imprecisão do próprio plano, não como regressão real; a intenção do gate está satisfeita).

### Human Verification Required

### 1. Smoke visual do 5º menu com dados reais

**Test:** Abrir o app (`streamlit run app.py`), navegar até "Comparar ações" no menu lateral, digitar 3 tickers do mesmo setor (ex.: o default "TAEE11, EGIE3, CMIG4") e aguardar o fetch.
**Expected:** A tabela renderiza com os 3 tickers nas colunas, o Selo (badge com emoji+rótulo) na primeira linha, os 5 múltiplos abaixo em ordem fixa, "—" em qualquer métrica ausente, progress bar aparece e desaparece sem travar a página, sem exceções não tratadas no Streamlit.
**Why human:** Depende de renderização real do Streamlit e de fetch ao vivo (Yahoo/CVM) — a lógica de montagem já está 100% coberta por teste unitário (DataFrame transposto, selo completo, degradação, suficiência), mas o comportamento end-to-end com rede real e UI real não é verificável por grep/pytest. O próprio 21-01-PLAN.md reserva este smoke como "Checkpoint humano (fora deste plano, no gate da fase)".

### Gaps Summary

Nenhum gap bloqueante encontrado. Todas as 7 truths observáveis, os 5 artefatos e os 5 key links foram verificados diretamente no código (não apenas no SUMMARY.md), com testes unitários existentes e passando ao vivo (338/338). O único item pendente é o smoke visual/rede que o próprio plano da fase classifica como checkpoint humano — não uma lacuna de implementação.

---

_Verified: 2026-07-03_
_Verifier: Claude (gsd-verifier)_
