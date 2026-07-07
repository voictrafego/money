# Phase 21: Comparador multi-ativo lado a lado (múltiplos + selo por coluna) - Research

**Researched:** 2026-07-03
**Domain:** Camada de UI/derivação Streamlit sobre engine Python já existente (sem novo método, sem nova dependência)
**Confidence:** HIGH (todas as afirmações verificadas lendo o código-fonte do próprio repo)

## Summary

A Phase 21 é **100% camada de exibição + derivação leve**. Todos os números e todo o selo já
são produzidos por funções puras da engine que existem, estão testadas por golden e são chamadas
hoje na aba Analisar/Ranking/Garimpo. Não há tecnologia nova a pesquisar, nenhuma dependência a
instalar, nenhuma decisão de biblioteca. O trabalho real é **wiring correto** de três coisas que já
existem: `montar()` (fetch cacheado por ticker), `lentes.metricas_par()` (os 5 múltiplos) e o selo
completo (quadrante).

A única incerteza técnica de fato — sinalizada como D3 no CONTEXT — é **como obter o Selo COMPLETO
(quadrante JOIA/VALUE TRAP, não só a cor) por coluna**. Investigação do código resolve isso de forma
definitiva: o rótulo do quadrante depende da `faixa_preco`, que vem do **prefixo da string de veredito
do DDM** (`faixa_do_veredito` em `selo.py`). Essa string de veredito **só é produzida dentro de
`report.analisar_acao(c, cfg)`** — construída a partir da matriz de sensibilidade Ke×g vs. preço
(report.py §184-207). Não existe função-atalho que devolva só o veredito do DDM. Portanto, para o selo
completo, **é obrigatório rodar `analisar_acao` por ticker**. A boa notícia: `analisar_acao` é CPU-pura
sobre o `CompanyData` já carregado — **não toca a rede** (a rede toda está em `montar()`, que é
cacheado). O custo é acotado pelo cap de N (2–6).

**Primary recommendation:** Reusar `report.analisar_acao(c, CFG).selo` por ticker para o selo completo
(garante paridade visual exata com a aba Analisar via `presentation.selo_badge`), e `lentes.metricas_par(c)`
para os 5 múltiplos, ambos operando sobre o MESMO `c = montar(t, ANO_BASE, N_ANOS)` cacheado. Renderizar
transposto com `st.dataframe(pd.DataFrame)` (tickers nas colunas, métricas nas linhas + linha de selo no topo).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Entrada de N tickers (COMP-01) | UI (app.py) | — | Parse/upper/dedup/cap é borda de input; padrão idêntico ao Ranking |
| Fetch dos N tickers | Data/Ingest (`montar` cacheado) | — | `@st.cache_data(ttl=3600)` já isola a rede; comparador NÃO refaz fetch |
| 5 múltiplos por ticker (COMP-02) | Engine (`lentes.metricas_par`) | — | Função pura never-raise já existente; fonte canônica dos múltiplos |
| Veredito de preço (DDM) | Engine (`report.analisar_acao`) | — | Único ponto que produz a string de veredito; base da `faixa_preco` do selo |
| BSD → cor do selo | Engine (`screening.bsd_empresa`) | — | Puro sobre `CompanyData`, sem rede; reproduzível fora de universo |
| Montagem do selo (quadrante) | Engine (`selo.montar_selo`) | — | Cruza bsd×veredito; já embutido em `analisar_acao().selo` |
| Render do selo (badge) | UI (`presentation.selo_badge`) | — | Render ÚNICO; mesmo helper de Analisar/Garimpo/Ranking |
| Tabela transposta / degradação | UI (app.py) | — | Layout e regra de suficiência ≥2 vivem na view (read-only) |

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D1 — Onde vive o comparador**
- Novo item no `st.sidebar.radio` ("Comparar ações") — 5º menu/página dedicado, porque o roadmap
  pede "N tickers escolhidos pelo usuário", independentes de qualquer ticker analisado.
- O expander atual na aba Analisar fica INTACTO (propósito diferente: auto-insere `ticker_ativo` e
  marca `alvo`). NÃO mexer nele nesta fase.
- Reusa as funções da engine (`lentes`, `screening`, `selo`) — nada de lógica nova em `app.py`.

**D2 — Layout "lado a lado"**
- Tickers em COLUNAS (transposto): as métricas viram LINHAS e cada ticker é uma COLUNA. As duas
  expressões do roadmap — "lado a lado" e "selo por coluna" — só fecham assim.
- O selo é a linha de cabeçalho (um badge por coluna, no topo de cada ticker).
- O embrião atual é linha-por-ticker; aqui transpõe para coluna-por-ticker.

**D3 — Profundidade do selo por coluna**
- Selo completo (quadrante), não só a cor. COMP-03 diz "o Selo da Phase 20 por coluna", e o Selo da
  Phase 20 É o quadrante (cor do BSD × veredito do DDM → JOIA / VALUE TRAP / …). Só a cor do BSD não
  seria "o Selo da Phase 20".
- ⚠ Custo a investigar: o veredito por ticker exige rodar o DDM (`report.analisar_acao`, que já computa
  `.selo`). Mitigação obrigatória: reusar o cache de `montar()` e limitar N (mesmo padrão de fetch do Ranking).

**D4 — Ordenação & destaque**
- Ordem de entrada fixa, sem sort, sem ticker-alvo. Fiel ao embrião (`tabela_pares` "NÃO ordena nem
  recomenda") e ao gate EXIBE, NUNCA recomenda. Num comparador livre não há "alvo" → sem destaque.
- ⚠ Nova regra de suficiência/degradação: sem alvo, `pares_suficientes` (que exige ≥2 linhas NÃO-alvo)
  não se aplica. Regra nova: exibe a tabela se ≥2 tickers resolvem com dado; células de métrica faltante
  viram "—"; `st.info` neutro se <2 tickers resolvem.

**D5 — Entrada de N tickers (COMP-01)**
- `st.text_input` separado por vírgula/espaço (mesmo padrão do Ranking/embrião), depois upper + dedup
  + cap de N (soft, faixa ~2–6 para não travar o app com o custo do DDM por ticker).

### Claude's Discretion
- Formato exato de render da tabela transposta (ex.: `st.dataframe` de um `pd.DataFrame` com tickers
  nas colunas + linha de selo, vs. `st.columns` com um "card" por ticker) — decisão do plano, desde que
  o selo apareça como badge por coluna e `app.py` siga read-only.
- Valor default do cap de N e placeholder de tickers do `text_input` — a critério do plano.

### Deferred Ideas (OUT OF SCOPE)
- Sort neutro por coluna (clicar num múltiplo para ordenar) — adiado por tensão com "EXIBE, NUNCA recomenda".
- Destaque de um ticker "foco" no comparador livre — adiado (sem alvo natural nesta fase).
- Colunas extras (veredito de preço textual, preço atual, payout) além das 5 múltiplos + selo — o selo já
  embute o veredito; ampliar fica para fase futura.
- Scanner/comparação sobre universo (não só tickers digitados) — fora de escopo do marco.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COMP-01 | Entrada de N tickers | Padrão exato já usado em Garimpo (app.py §1220-1222) e Ranking (§1287-1290): `st.text_input`/`text_area` → `[t.strip().upper() for t in txt.replace(",", " ").split() if t.strip()]`. Acrescentar dedup (preservando ordem) e cap soft de N. |
| COMP-02 | Tabela comparativa de múltiplos | `lentes.metricas_par(c)` já devolve `ParComparavel(pl, pvp, roe, dy, valor_mercado)` — os 5 múltiplos, never-raise, `None` quando falta insumo. Fonte canônica idêntica ao embrião (app.py §959). Transpor para colunas=tickers. |
| COMP-03 | Selo por coluna | Selo completo = `report.analisar_acao(c, CFG).selo` (objeto `Selo` já montado). Render via `presentation.selo_badge(cor, rotulo, qualidade, verificar)` — MESMO helper da aba Analisar (app.py §848), garantindo paridade visual. |
</phase_requirements>

## Standard Stack

Nenhuma dependência nova. Tudo já está importado no topo de `app.py` (§14-28):

| Módulo | Já importado como | Papel na fase | Fonte |
|--------|-------------------|---------------|-------|
| `pandas` | `pd` (§14) | `pd.DataFrame` transposto para `st.dataframe` | [VERIFIED: app.py §14] |
| `analista.core.lentes` | `lentes` (§23) | `metricas_par` → 5 múltiplos | [VERIFIED: app.py §23] |
| `analista.core.screening` | `sc` (§25) | `bsd_empresa` (se optar por compor; ver D3) | [VERIFIED: app.py §25] |
| `analista.report.report` | `report` (§28) | `analisar_acao` → `.selo` + veredito | [VERIFIED: app.py §28] |
| `analista.report.selo` | `selo` (§28) | `cor_do_bsd`, `montar_selo`, `faixa_do_veredito` | [VERIFIED: app.py §28] |
| `analista.report.presentation` | `presentation` (§28) | `selo_badge`, `selo_emoji` | [VERIFIED: app.py §28] |
| `montar(ticker, ano_base, n)` | função local (§204) | fetch cacheado por ticker | [VERIFIED: app.py §203-205] |

**Installation:** N/A — ZERO novas dependências (gate do projeto). Confirmado: os módulos necessários já
constam nos imports do `app.py`; adicionar o bloco `elif` do comparador não introduz `import` novo.

## Architecture Patterns

### System Architecture Diagram

```
[st.text_input "TAEE11, EGIE3, CMIG4"]
          │  parse → upper → dedup(preserva ordem) → cap N (2–6)         (COMP-01, UI/borda)
          ▼
   para cada ticker t:
          │
          ▼
   c = montar(t, ANO_BASE, N_ANOS)   ◄── @st.cache_data(ttl=3600)  (ÚNICA fonte de rede; cacheada)
          │
          ├─ resolve? (c is not None and c.anos) ── não ──► descarta (célula/coluna ausente)
          │                                                          │
          ▼ sim                                                      │
   ┌──────┴───────────────────────────┐                             │
   │ metricas_par(c)  → 5 múltiplos    │  (CPU-pura, never-raise)    │  COMP-02
   │ analisar_acao(c, CFG).selo        │  (CPU-pura, DDM+indicadores)│  COMP-03
   └──────┬───────────────────────────┘                             │
          ▼                                                          ▼
   contagem de tickers resolvidos ──── <2 ──► st.info neutro (D4: sem tabela)
          │ ≥2
          ▼
   pd.DataFrame transposto: colunas = tickers, linhas = [Selo(badge), P/L, P/VP, ROE, DY, Valor Mercado]
   selo por coluna via presentation.selo_badge(...)   ·   células None → "—" (fmt_*)
          ▼
   st.dataframe(..., use_container_width=True)   +   caption "não é ranking nem recomendação"
```

### Recommended Project Structure

```
app.py
├── (§587) st.sidebar.radio   → ACRESCENTAR "Comparar ações" à lista        (D1)
└── novo bloco elif modo.startswith("Comparar"):                            (D1, espelha §1216/§1283)
        ├── st.text_input + parse/upper/dedup/cap                           (COMP-01, D5)
        ├── loop montar(t) cacheado → metricas_par + analisar_acao          (COMP-02/03)
        ├── regra de suficiência ≥2 resolvidos                              (D4)
        └── pd.DataFrame transposto + st.dataframe + selo_badge por coluna  (D2, COMP-03)
```

Nenhum arquivo de engine é tocado. Toda derivação já existe; o `elif` só LÊ e desenha (firewall read-only).

### Pattern 1: Fetch cacheado de N tickers (REUSAR EXATAMENTE)

**What:** O padrão canônico de coletar N tickers, provado em Garimpo e Ranking.
**When to use:** No loop de tickers do comparador — obrigatório reusar `montar()` cacheado (mitigação D3).
```python
# Source: app.py §1222-1229 (Garimpo) e §1290-1298 (Ranking) — VERIFIED
tickers = [t.strip().upper() for t in txt.replace(",", " ").split() if t.strip()]
empresas = []
prog = st.progress(0.0, text="Coletando dados...")
for i, t in enumerate(tickers):
    c = montar(t, ANO_BASE, N_ANOS)          # @st.cache_data(ttl=3600) — sem re-fetch
    if c is not None and c.anos:             # "resolve com dado" == este teste
        empresas.append(c)
    prog.progress((i + 1) / len(tickers), text=f"Coletando {t}...")
prog.empty()
```
`ANO_BASE`, `N_ANOS`, `CFG` já são globais no topo do app (app.py §239-241). [VERIFIED]

### Pattern 2: Selo completo por ticker (RECOMENDADO — reusar analisar_acao)

**What:** Obter o objeto `Selo` completo (quadrante) e renderizá-lo com o helper único.
**When to use:** COMP-03 — uma vez por ticker resolvido.
```python
# Source: report.py §303-311 (montagem do selo) + app.py §847-851 (render único) — VERIFIED
a = report.analisar_acao(c, CFG)             # produz a.selo (Selo completo) + a.veredito
if a.selo is not None and a.selo.cor is not None:
    badge = presentation.selo_badge(
        a.selo.cor, a.selo.rotulo, a.selo.qualidade, a.selo.verificar
    )   # ex.: "🟢 Qualidade Alta · JOIA"  |  cor None → "—"
```
`selo_badge` já degrada `cor=None → "—"` e trata o overlay VERIFICAR (presentation.py §129-137). [VERIFIED]

### Pattern 3: Render transposto (Claude's Discretion — recomendação com evidência)

**What:** DataFrame com tickers nas colunas, métricas + selo nas linhas.
**Evidência de que `st.dataframe(pd.DataFrame)` é o padrão da casa:** o embrião de pares (§976),
Garimpo (§1262) e Ranking (§1351-ish) TODOS usam `st.dataframe(pd.DataFrame(...), hide_index=True,
use_container_width=True)`. Não há uso de `st.columns`-cards para tabelas comparativas no app. Manter
o mesmo idioma garante consistência visual e zero deps. [VERIFIED: app.py §976, §1262, §1209]
```python
# Transposição: índice = nomes das linhas; colunas = tickers
import pandas as pd  # já importado como pd
dados = {}   # {ticker: {"Selo": badge, "P/L": ..., "P/VP": ..., "ROE": ..., "DY": ..., "Valor de Mercado": ...}}
df = pd.DataFrame(dados)   # DataFrame(dict-de-dicts) já vem transposto: métricas=linhas, tickers=colunas
st.dataframe(df, use_container_width=True)
```
Células None viram "—" ao formatar ANTES de montar o dict: `fmt_num(pl)`, `fmt_pct(roe)`,
`fmt_pct(dy)`, e Valor de Mercado no padrão do embrião `fmt_rs(vm/1e9, casas=1)+" B"` (app.py §964-966).
`fmt_num`/`fmt_pct`/`fmt_rs` já retornam `"—"` para None (app.py §244-252). [VERIFIED]

### Anti-Patterns to Avoid

- **Compor o veredito do DDM à mão em app.py:** replicaria ~130 linhas de DDM/CAPM/sensibilidade
  (report.py §53-207), violaria o firewall read-only e romperia a paridade de números. NUNCA fazer.
- **Usar só `bsd_empresa` → `cor_do_bsd` para o selo:** isso dá só a COR (como o Ranking faz, §1343),
  não o quadrante. D3 exige o selo COMPLETO. Insuficiente para COMP-03. (Ver Don't Hand-Roll.)
- **Ordenar/destacar por métrica:** viola D4 e o gate "EXIBE, NUNCA recomenda".
- **Chamar `st.cache_data.clear()`:** apagaria o cache global de `montar/selic/rf_capm` (D-08 do projeto).
- **Mexer no expander de pares da aba Analisar:** D1 manda deixá-lo INTACTO.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Veredito de preço (Barato/Justo/Caro) por ticker | Recalcular DDM/CAPM/sensibilidade em app.py | `report.analisar_acao(c, CFG).veredito`/`.selo` | Único ponto canônico; produz a string exata que `faixa_do_veredito` casa; garante paridade de números com Analisar |
| Selo/quadrante (JOIA, VALUE TRAP…) | Montar a matriz qualidade×preço na view | `selo.montar_selo` (já embutido em `analisar_acao().selo`) | Matriz `_MATRIZ` e cortes de cor são config/engine; render via `selo_badge` (ponto único) |
| Cor do BSD por cortes | Hardcodar 70/55/40 na view | `selo.cor_do_bsd(bsd, CFG)` | Cortes vêm de `cfg["selo"]["cor"]` (config.yaml §165-169); zero threshold espalhado |
| Os 5 múltiplos | Calcular P/L, P/VP, ROE, DY, VM na view | `lentes.metricas_par(c)` | Usa LPA/ROE canônicos (consistência entre menus); never-raise |
| Formatação None → "—" | `if x is None else ...` | `fmt_num`/`fmt_pct`/`fmt_rs` | Já centralizam o sentinela "—" (app.py §244-252) |

**Key insight:** O selo COMPLETO (quadrante) é indivisível do veredito do DDM. Como não existe função que
devolva só o veredito do DDM barato, a decisão D3 se resolve por eliminação: **reusar `analisar_acao`**.
Ele é a única porta que produz `.selo` idêntico ao da aba Analisar — o que também satisfaz o princípio de
"render ÚNICO do selo" da Phase 20.

## D3 RESOLVIDO — Recomendação concreta de wiring (custo × benefício)

**Pergunta:** Reusar `analisar_acao(c, CFG)` por ticker (traz `.selo`) vs. compor
`screening.bsd_empresa(c, cfg)` + a string de veredito?

**Onde nasce a string de veredito:** `report.py §184-207` — construída de `a.vmin`/`a.vmax` (min/max da
matriz de sensibilidade Ke×g, §175-177) vs. `a.preco_atual`, com salvaguarda VERIFICAR (§189-201). Ou
seja, o veredito é um SUBPRODUTO do DDM completo. **Não existe atalho** que devolva só o veredito. [VERIFIED: report.py §184-207]

**Como `faixa_preco` do selo lê o veredito:** `selo.faixa_do_veredito(veredito)` casa o PREFIXO da string
(`SUBAVALIADA→Barato`, `NO INTERVALO→Justo`, `SOBREAVALIADA→Caro`; `VERIFICAR`/outro→None). Sem essa
string, `faixa_preco=None` → `rotulo=None` → o quadrante colapsa em só-cor. [VERIFIED: selo.py §88-127]

**Custo de `analisar_acao`:** roda múltiplos + crescimento + CAPM + DDM dois-estágios + matriz de
sensibilidade + indicadores técnicos (resample OHLC W-FRI + MM/ADX/RSI/MACD). **Porém é CPU-pura sobre o
`CompanyData` já carregado — NÃO toca a rede.** A prova: a aba Analisar já chama `analisar_acao(c, CFG)`
(app.py §828) sobre um `c = montar(...)` (§816) e nenhuma coleta extra ocorre; o CAPM lê `cfg["capm"]
["rf_local"]` já injetado no topo (report.py §117-122). Toda a rede está em `montar()` (cacheado ttl=3600). [VERIFIED: app.py §816/§828, report.py §113-128]

**Alternativa (compor bsd_empresa + veredito):** para o veredito você teria que rodar o DDM de qualquer
jeito → nenhum ganho real. `bsd_empresa` sozinho só te dá a cor (é o que o Ranking usa, §1343). Insuficiente para D3.

**RECOMENDAÇÃO:** **Reusar `report.analisar_acao(c, CFG)` por ticker** e ler `.selo`. Para os 5 múltiplos,
usar `lentes.metricas_par(c)` (mais barato e é a fonte canônica do embrião; `analisar_acao.multiplos` traz
ROE/P/L/DY mas NÃO P/VP nem Valor de Mercado). Ambos sobre o MESMO `c` cacheado. Custo total por ticker =
1 `montar()` (cacheado) + 1 `metricas_par()` (trivial) + 1 `analisar_acao()` (CPU, sem rede). Acotado pelo
cap N (2–6). Mitigação D3 (cache + cap) satisfeita.

**Trade-off honesto:** `analisar_acao` é a chamada mais pesada em CPU do app (DDM + resample OHLC). Com N=6
são 6 execuções sequenciais no rerun. Aceitável para triagem; o cap soft de N (recomendo default 5,
teto 6) protege a responsividade. Se algum dia N precisar crescer, aí sim valeria uma função enxuta que
rode só DDM→veredito sem indicadores — mas isso é engine nova, FORA do escopo desta fase (deixar como Open Question).

## D4 RESOLVIDO — Suficiência/degradação sem alvo

- **"≥2 tickers resolvem com dado"** = mesmo teste de fetch de Garimpo/Ranking: `c is not None and c.anos`
  (app.py §1227/§1295). Conte `len(empresas)` após o loop. [VERIFIED]
- **`pares_suficientes` NÃO se aplica** (exige ≥2 linhas NÃO-`alvo`, e aqui não há alvo — lentes.py §199-209).
  Regra nova vive na view: `if len(empresas) >= 2: render else: st.info(...)`. [VERIFIED]
- **Célula de métrica faltante → "—":** `ParComparavel` já traz `None` por campo (metricas_par never-raise,
  lentes.py §143-178); `fmt_num`/`fmt_pct`/`fmt_rs` convertem `None→"—"`. O selo com `cor=None` vira "—"
  via `selo_badge`. [VERIFIED]
- **`st.info` neutro se <2:** copy neutra tipo "Informe ao menos 2 tickers com dados para comparar."
  (não é erro; é degradação graciosa, espelha §979).

## Code Examples

### Selo só-cor vs. selo completo (a distinção que fundamenta D3)
```python
# Source: app.py §1343 (Ranking) — SÓ A COR (NÃO serve para COMP-03):
"Selo": presentation.selo_emoji(selo.cor_do_bsd(sc.bsd_empresa(_c_sel, CFG), CFG))

# Source: app.py §847-851 (Analisar) — SELO COMPLETO (é o alvo de COMP-03):
badge = presentation.selo_badge(a.selo.cor, a.selo.rotulo, a.selo.qualidade, a.selo.verificar)
```

### Formatação de Valor de Mercado (reusar do embrião)
```python
# Source: app.py §964-966 — VERIFIED
vm = fmt_rs(p.valor_mercado / 1e9, casas=1) + " B" if p.valor_mercado is not None else "—"
```

## State of the Art

Não se aplica — a fase reusa engine interna estável; não há tecnologia externa evoluindo. Os padrões de
Selo/DDM/múltiplos foram fixados nas Phases 19-20 do próprio projeto e têm cobertura golden.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Cap default de N = 5, teto 6 é adequado para não travar o rerun com `analisar_acao`×N | D3/D5 | Baixo — é Claude's Discretion; ajustar o número é trivial e não afeta arquitetura |

*Todas as demais afirmações foram VERIFICADAS lendo o código-fonte nesta sessão.*

## Open Questions (RESOLVED)

1. **RESOLVED: Função enxuta "só veredito DDM" (sem indicadores técnicos)?**
   - What we know: `analisar_acao` também roda o read técnico (resample OHLC + MM/ADX/RSI/MACD), que o
     comparador não exibe — é custo de CPU "desperdiçado" por coluna.
   - What's unclear: se o custo com N≤6 justifica criar um caminho mais enxuto na engine.
   - Recommendation: NÃO criar agora (seria método/engine novo, fora do escopo e do gate "sem lógica nova
     em app.py / reusar o existente"). Ficar com `analisar_acao` e o cap de N. Reavaliar só se surgir demanda por N grande.

## Environment Availability

Sem dependências externas novas. A fase é UI/derivação sobre engine já instalada. `montar()` usa a mesma
rede (CVM/Yahoo/BCB) que as abas existentes já usam, cacheada. Nada a probar.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (configurado em `pyproject.toml [tool.pytest.ini_options]`) |
| Config file | `pyproject.toml` (§14-16: `pythonpath=["src"]`, `testpaths=["tests"]`) |
| Quick run command | `python -m pytest tests/test_lentes.py tests/test_selo.py tests/test_presentation_multiticker.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COMP-01 | parse/upper/dedup/cap de tickers | unit (helper puro, se extraído) | `python -m pytest tests/test_lentes.py -q` | ✅ (lentes coberto); helper de parse é UI — ver Wave 0 |
| COMP-02 | 5 múltiplos por ticker | unit | `python -m pytest tests/test_lentes.py -q` | ✅ `metricas_par`/`tabela_pares` já testados |
| COMP-03 | selo completo por coluna | unit | `python -m pytest tests/test_selo.py tests/test_presentation_multiticker.py -q` | ✅ `montar_selo`/`selo_badge` já testados |
| (gate) | golden da engine intacto | regression | `python -m pytest -q` | ✅ 30 arquivos de teste |

**Nota:** `app.py` é read-only e não tem teste unitário direto (é UI Streamlit). A defesa é: (1) toda a
lógica derivada vive em funções de engine JÁ testadas por golden; (2) a suíte completa verde garante que
o wiring não quebrou nada. Não há lógica nova a testar em app.py além do parse de input.

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_lentes.py tests/test_selo.py tests/test_presentation_multiticker.py -q`
- **Per wave merge:** `python -m pytest -q`
- **Phase gate:** suíte completa verde antes de `/gsd-verify-work` (gate do projeto: golden verde).

### Wave 0 Gaps
- [ ] Se o parse/dedup/cap de tickers (COMP-01) for extraído para um helper puro na engine
      (ex.: `lentes.normalizar_tickers(texto, cap)`), adicionar caso em `tests/test_lentes.py`.
      Se ficar inline em app.py (UI), não há teste unitário — coberto pela inspeção manual + goldens.
- [ ] Nenhum outro gap: `metricas_par`, `montar_selo`, `cor_do_bsd`, `selo_badge` já têm cobertura golden
      (test_lentes.py, test_selo.py, test_presentation_multiticker.py).

## Security Domain

Não aplicável no sentido de authn/authz/crypto — app Streamlit local/single-tenant, sem login, sem dados
sensíveis persistidos, sem endpoints. A única "borda" é o input de tickers do usuário (V5 Input Validation).

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Parse defensivo: `strip/upper/split`, dedup, cap de N; ticker inexistente degrada via `montar()→None` (never-raise). `esc_md()` já usado ao exibir strings de ticker no app (app.py §969) para evitar quebra de markdown. |
| V2/V3/V4/V6 | no | Sem auth/sessão/crypto nesta aplicação |

**Threat relevante:** input malformado (vírgulas duplas, espaços, ticker inexistente) → mitigado pelo
parse defensivo e pela degradação never-raise da engine (célula "—" / `st.info` se <2 resolvem). Sem
injeção de código: nenhum `eval`/SQL/shell no caminho; `esc_md` neutraliza markdown no render do ticker.

## Sources

### Primary (HIGH confidence) — leitura direta do código-fonte nesta sessão
- `src/analista/core/lentes.py` §140-209 — `ParComparavel`, `metricas_par`, `tabela_pares`, `pares_suficientes`
- `src/analista/report/report.py` §22-51, §53-313 — `AnaliseAcao`, `analisar_acao` (DDM→veredito→`.selo`)
- `src/analista/report/selo.py` §46-127 — `_MATRIZ`, `cor_do_bsd`, `faixa_do_veredito`, `montar_selo`
- `src/analista/report/presentation.py` §102-138 — `selo_emoji`, `selo_badge`
- `src/analista/core/screening.py` §384-409 — `bsd_empresa`
- `app.py` §197-205 (`montar` cacheado), §239-241 (globais), §244-256 (fmt/esc), §587-593 (sidebar radio),
  §828/§847-859 (Analisar: `analisar_acao`+`selo_badge`), §938-979 (embrião de pares), §1216-1276 (Garimpo),
  §1283-1351 (Ranking: fetch N + selo só-cor)
- `config.yaml` §165-169 — cortes de cor do selo
- `pyproject.toml` §14-16 — config pytest
- `.planning/ROADMAP.md` §225-241 — Phase 20/21
- `.planning/phases/21-.../21-CONTEXT.md` — decisões D1-D5

### Secondary / Tertiary
- Nenhuma. Fase inteiramente interna; nenhuma fonte externa necessária.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — todos os módulos verificados nos imports do app.py; zero deps novas
- Architecture (wiring D3/D4): HIGH — caminho do veredito→selo rastreado linha a linha em report.py/selo.py
- Pitfalls: HIGH — padrões extraídos dos blocos existentes (Analisar/Garimpo/Ranking) verbatim
- Custo de `analisar_acao` sem rede: HIGH — provado pela chamada já existente na aba Analisar

**Research date:** 2026-07-03
**Valid until:** estável enquanto a engine das Phases 19-20 não mudar (sem prazo curto; ~90 dias)
