---
phase: 20-selo-de-sustentabilidade-do-dividendo-cruzado-com-veredito-d
verified: 2026-07-03T01:01:31Z
status: passed
score: 11/11 must-haves verified
overrides_applied: 0
---

# Phase 20: Selo de Sustentabilidade do Dividendo cruzado com veredito de preço (DDM) — Verificação

**Phase Goal:** A aba Analisar (e, onde couber, Garimpar/Ranking) exibe um Selo de Sustentabilidade do Dividendo em 4 cores, derivado do score BSD já calculado pela engine, cruzado com o veredito de preço do DDM num quadrante (JOIA/VALUE TRAP/etc.), fronteira "EXIBE, NUNCA recomenda".
**Verificado:** 2026-07-03T01:01:31Z
**Status:** PASS
**Re-verificação:** Não — verificação inicial.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidência |
|---|-------|--------|-----------|
| 1 | Engine deriva cor de selo (verde/azul/amarelo/vermelho) a partir do score BSD (0-100) | ✓ VERIFIED | `src/analista/report/selo.py:58-76` `cor_do_bsd()`, config-driven via `config.yaml:161-170` (`selo.cor.{verde_min,azul_min,amarelo_min}` = 70/55/40). Testado com bordas exatas em `tests/test_selo.py:37-52`. |
| 2 | Engine cruza qualidade (cor) × preço (veredito DDM) num rótulo de quadrante (JOIA/VALUE TRAP/etc.) | ✓ VERIFIED | `selo.py:105-127` `montar_selo()` + matriz fixa `_MATRIZ` (6 rótulos). Testado nos 6 rótulos em `tests/test_selo.py:81-98`. |
| 3 | Quando veredito é VERIFICAR, o selo marca alerta e NÃO atribui faixa de preço | ✓ VERIFIED | `selo.py:119-122` overlay `verificar=True`, `faixa_preco=None`, `rotulo=None`. Testado em `tests/test_selo.py:105-112`. |
| 4 | `analisar_acao` popula `a.selo` para 1 ticker sem tocar a rede e sem quebrar os goldens pré-existentes | ✓ VERIFIED | `report.py:16,19,50,306-311` — `bsd_empresa(c, cfg)` é puro sobre `CompanyData` já carregado; `montar_selo` never-raise. Suíte completa 325/325 verde (baseline 307 preservado). |
| 5 | Cortes de cor vivem em `config.yaml` (tunáveis), não hardcoded espalhados | ✓ VERIFIED | Bloco `selo.cor` em `config.yaml:160-170`; `cor_do_bsd` lê de `cfg["selo"]["cor"]`; matriz de rótulos (não tunável por design) fica em código, conforme decisão D2. |
| 6 | Usuário vê na aba Analisar um selo colorido em destaque, perto do veredito atual | ✓ VERIFIED | `app.py:842-859` — bloco imediatamente após o veredito colorido (`st.markdown` do badge via `presentation.selo_badge`). |
| 7 | Usuário vê na aba Analisar o rótulo do quadrante cruzando qualidade × preço | ✓ VERIFIED | `app.py:848-853` — `selo_badge` inclui `a.selo.rotulo`; `st.caption` explica o cruzamento BSD×DDM. |
| 8 | Quando VERIFICAR, usuário vê alerta "Verificar dados" em vez de rótulo de preço | ✓ VERIFIED | `app.py:854-859` — `st.warning` condicional a `a.selo.verificar`; `selo_badge` (presentation.py:134-137) suprime o rótulo de preço nesse caso. |
| 9 | Usuário vê coluna de selo (mesma cor) em Garimpo e Ranking, por linha | ✓ VERIFIED | Garimpo: `app.py:1252` (`"Selo": presentation.selo_emoji(selo.cor_do_bsd(b.get("bsd"), CFG))`); Ranking: `app.py:1343` (`sc.bsd_empresa(_c_sel, CFG)` + `cor_do_bsd`). Ambas colunas presentes no `rows`/DataFrame. |
| 10 | Selo é visualmente idêntico nos três lugares (mesma função de render) | ✓ VERIFIED | Os três sítios chamam `presentation.selo_emoji`/`presentation.selo_badge` — única fonte de formatação (`presentation.py:112-138`), sem `import streamlit`. |
| 11 | Nenhuma fórmula de selo vive em `app.py` — view só LÊ campos da engine | ✓ VERIFIED | `grep -nE 'JOIA|VALUE TRAP|verde_min|azul_min|amarelo_min|>= *70|>= *55|>= *40' app.py` retorna vazio. `app.py` só chama `cor_do_bsd`/`bsd_empresa`/`selo_emoji`/`selo_badge` e lê `a.selo.*`. |

**Score:** 11/11 truths verified

### Required Artifacts

| Artefato | Esperado | Status | Detalhes |
|----------|----------|--------|----------|
| `src/analista/report/selo.py` | `Selo` dataclass + `cor_do_bsd` + `faixa_do_veredito` + `montar_selo`, firewall vs report.py | ✓ VERIFIED | 128 linhas, todas as funções presentes, comportamento conferido contra `<behavior>` do plan; sem `import ... report`. |
| `src/analista/core/screening.py::bsd_empresa` | BSD absoluto de 1 empresa reusando `bsd_ranking` | ✓ VERIFIED | `screening.py:384-409`; idêntico a `bsd_ranking([c])[0]["bsd"]` (testado, `tests/test_selo.py:172-179`), never-raise. |
| `config.yaml` bloco `selo:` | Cortes de cor do BSD | ✓ VERIFIED | `config.yaml:160-170`, valores 70/55/40 conforme plano. |
| `src/analista/report/report.py` | Campo `selo` em `AnaliseAcao` + população em `analisar_acao` | ✓ VERIFIED | `report.py:50` campo aditivo default `None`; `report.py:306-311` população never-raise. |
| `tests/test_selo.py` | Goldens de cortes, matriz, overlay VERIFICAR, degradação, firewall | ✓ VERIFIED | 13 testes, cobrindo todos os casos exigidos incluindo bordas exatas e teste de firewall por introspecção de imports. |
| `src/analista/report/presentation.py::selo_emoji/selo_badge` | Formatação pura do selo (sem streamlit) | ✓ VERIFIED | `presentation.py:112-138`; sem `import streamlit` no módulo; testado. |
| `app.py` | Render read-only do selo em Analisar (destaque+quadrante) e coluna em Garimpo/Ranking | ✓ VERIFIED | 3 sítios de render confirmados (linhas 847-859, 1250-1252, 1341-1343); import de `selo` em `app.py:28`. |

### Key Link Verification

| From | To | Via | Status | Detalhes |
|------|-----|-----|--------|----------|
| `report.py::analisar_acao` | `screening.py::bsd_empresa` | chamada para obter BSD de 1 empresa | ✓ WIRED | `report.py:308` `bsd = screening.bsd_empresa(c, cfg)` |
| `report.py::analisar_acao` | `selo.py::montar_selo` | cruza BSD+veredito, atribui `a.selo` | ✓ WIRED | `report.py:309` `a.selo = selo_mod.montar_selo(bsd, a.veredito, cfg)` |
| `app.py` (Analisar) | `a.selo` | leitura dos campos já derivados | ✓ WIRED | `app.py:847-859` |
| `app.py` (Garimpo/Ranking) | `selo.cor_do_bsd`/`screening.bsd_empresa` | cor por linha a partir do BSD já em mãos | ✓ WIRED | `app.py:1252`, `app.py:1343` |
| `app.py` | `presentation.selo_emoji`/`selo_badge` | função única de render nos três lugares | ✓ WIRED | `app.py:848-849` (badge), `app.py:1252`/`1343` (emoji) |

### Data-Flow Trace (Level 4)

| Artefato | Variável de dado | Fonte | Dado real | Status |
|----------|-------------------|-------|-----------|--------|
| Analisar (badge do selo) | `a.selo` | `analisar_acao(c, CFG)` → `montar_selo(bsd_empresa(c,cfg), a.veredito, cfg)` sobre `CompanyData` já carregado do ticker digitado | Sim — deriva de dados fundamentalistas reais (não estático) | ✓ FLOWING |
| Garimpo (coluna Selo) | `b.get("bsd")` | `sc.bsd_ranking(empresas, ...)` sobre a lista de tickers efetivamente coletada (`montar(t, ANO_BASE, N_ANOS)`) | Sim | ✓ FLOWING |
| Ranking (coluna Selo) | `sc.bsd_empresa(_c_sel, CFG)` | `_c_sel` vem de `empresas` (dados já coletados por ticker do ranking) | Sim | ✓ FLOWING |

Nota de desempenho (não-bloqueante): no Ranking, `bsd_empresa` é recalculado por linha via `bsd_ranking([c])` individual, ao invés de reusar um `bsd_ranking(empresas)` em lote como o Garimpo faz. Funcionalmente correto (padronização absoluta garante que `bsd_ranking([c])[0]["bsd"] == bsd_ranking(empresas)[i]["bsd"]`, testado em `test_bsd_empresa_reproduzivel_vs_ranking`), mas é O(n) chamadas a `bsd_ranking` numa lista de 1 elemento por linha do Ranking. Não é um gap de goal — é uma nota de eficiência para revisão futura se o Ranking crescer muito.

### Behavioral Spot-Checks

| Comportamento | Comando | Resultado | Status |
|---|---|---|---|
| `cor_do_bsd` respeita os 4 cortes de cor + None | `python -c "...selo.cor_do_bsd(85/60/45/30/None, cfg)..."` | verde/azul/amarelo/vermelho/None | ✓ PASS |
| `montar_selo` produz JOIA / VALUE TRAP / overlay VERIFICAR | `python -c "...selo.montar_selo(85,'SUBAVALIADA...'), (30,'SUBAVALIADA...'), (85,'VERIFICAR...')..."` | JOIA / VALUE TRAP / verificar=True sem rótulo | ✓ PASS |
| `presentation.selo_emoji`/`selo_badge` formatam corretamente | `python -c "...p.selo_emoji/p.selo_badge..."` | 🟢/🔴/— corretos; badge contém emoji+rótulo; badge com verificar contém "Verificar" | ✓ PASS |
| `app.py` importa `selo` e usa os 4 símbolos de render | `python -c "ast.parse(...); assert 'selo' importado; 'a.selo'/'cor_do_bsd'/'bsd_empresa'/'selo_emoji' in src"` | ok | ✓ PASS |
| `app.py` compila sem erro de sintaxe | `python -m py_compile app.py` | sucesso | ✓ PASS |
| Suíte completa de testes | `./.venv/bin/python -m pytest -q` | **325 passed in 3.05s** | ✓ PASS |

### Requirements Coverage

| Requisito | Plano de origem | Descrição | Status | Evidência |
|-----------|------------------|-----------|--------|-----------|
| SELO-01 | 20-01-PLAN.md | Cálculo do selo na engine (BSD → cor/qualidade) | ✓ SATISFIED | `selo.py::cor_do_bsd`+`_qualidade`, `screening.py::bsd_empresa`, `config.yaml::selo.cor` |
| SELO-02 | 20-01-PLAN.md | Cruzamento selo × veredito de preço → rótulo de quadrante | ✓ SATISFIED | `selo.py::faixa_do_veredito`+`_MATRIZ`+`montar_selo` (6 rótulos + overlay VERIFICAR) |
| SELO-03 | 20-02-PLAN.md | Exibição na UI (Analisar em destaque + quadrante; colunas em Garimpo/Ranking) | ✓ SATISFIED | `app.py` 3 sítios de render + `presentation.selo_emoji`/`selo_badge` |

Nota: `.planning/REQUIREMENTS.md` neste repo está escopado ao milestone anterior (v1.4 Ferramenta de Swing Trade) e não lista IDs `SELO-*` — a fonte de verdade dos requisitos da Fase 20 é o `ROADMAP.md` (que declara `SELO-01/02/03` no bloco da fase) e o `must_haves.requirements` de cada plano, ambos conferidos acima. Nenhum requisito órfão identificado dentro do escopo desta fase.

### Anti-Patterns Found

Nenhum. Varredura em `selo.py`, `presentation.py`, `report.py`, `screening.py`, `config.yaml`, `app.py` (sítios do selo), `test_selo.py`, `test_presentation_multiticker.py`:
- Sem `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` relacionados ao selo (o único match de "TODO" em `report.py` é a palavra "TODOS", falso positivo).
- Sem `st.metric`/imperativos de compra/venda vazando na copy do selo — todas as ocorrências de "compre/venda/recomend" no repo são negações/disclaimers (ex. "não é recomendação"), nenhuma é instrução.
- `selo.py` não importa `report.py` (firewall confirmado por grep e por teste de introspecção).
- `presentation.py` não importa `streamlit` (módulo puro).

### Human Verification Required

Nenhum item pendente. O checkpoint humano bloqueante do Plan 02 (`Task 3: Verificação visual do selo`) já foi executado e **aprovado** durante a fase — evidência: `20-02-SUMMARY.md` ("Task 3: checkpoint human-verify - APROVADO pelo usuário: selo idêntico nos 3 lugares, VERIFICAR como alerta, copy não-imperativa") e `.planning/STATE.md:30` ("Status: Phase complete — 20-02 verificado e aprovado (checkpoint humano)"). Este verificador confirmou independentemente, por leitura de código e testes automatizados, que os mesmos comportamentos aprovados visualmente (badge em destaque, quadrante, overlay VERIFICAR, colunas em Garimpo/Ranking, copy não-imperativa) estão de fato implementados e wired — não há discrepância entre o que foi aprovado e o que está no código atual (mesmo commit `665f933`, sem alterações posteriores nos arquivos do selo).

### Gaps Summary

Nenhum gap bloqueante ou de incerteza encontrado. As 11 verdades observáveis derivadas do goal da Fase 20 (roadmap + must_haves dos dois planos) estão todas verificadas em código, com testes golden dedicados (13 em `test_selo.py` + 5 em `test_presentation_multiticker.py`), suíte completa 325/325 verde, firewall preservado (`selo.py` não importa `report.py`; `presentation.py` não importa `streamlit`), e nenhum threshold/rótulo de selo vazado para `app.py` (grep vazio). O checkpoint humano de verificação visual já foi conduzido e aprovado durante a execução da fase.

Única observação não-bloqueante: no Ranking, o BSD é recalculado por linha (`sc.bsd_empresa` chamado uma vez por empresa) em vez de reusar um `bsd_ranking` em lote — correto e testado quanto à reprodutibilidade, mas potencialmente ineficiente se a lista de Ranking crescer. Não afeta o goal da fase; registrado apenas como nota de eficiência para consideração futura (não estruturado como gap).

---

*Verificado: 2026-07-03T01:01:31Z*
*Verificador: Claude (gsd-verifier)*
