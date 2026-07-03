# Phase 21: Comparador multi-ativo lado a lado (múltiplos + selo por coluna) - Pattern Map

**Mapped:** 2026-07-03
**Files analyzed:** 1 (modificado: `app.py`)
**Analogs found:** 1 / 1 (todos os analogs vivem DENTRO do próprio `app.py`)

> **Firewall do projeto:** `app.py` é read-only sobre a engine — só LÊ funções puras (`lentes`,
> `screening`, `selo`, `report`, `presentation`) e desenha. NENHUM arquivo de engine é tocado nesta
> fase. O único código novo é um bloco `elif modo.startswith("Comparar")` em `app.py` + 1 item no
> `st.sidebar.radio`. Todos os analogs já existem no mesmo arquivo — é wiring, não invenção.

## File Classification

| Arquivo (modificado) | Role | Data Flow | Analog mais próximo | Match |
|----------------------|------|-----------|---------------------|-------|
| `app.py` → novo bloco `elif modo.startswith("Comparar")` | view / page (Streamlit) | request-response (rerun) + fetch cacheado | aba **Ranking** (`app.py` §1283-1351) para o loop de N tickers; **embrião de pares** (§942-979) para a tabela transposta; aba **Analisar** (§847-851) para o selo completo | exact (mesmo arquivo, mesmo idioma) |
| `app.py` → item no `st.sidebar.radio` (§587-593) | config / nav | — | a própria lista de menus (§589-591) | exact |

**Sem novos arquivos de engine.** Toda derivação (múltiplos, BSD, veredito, selo) já é função pura
existente e testada por golden. Ver "No Analog Found" (vazio) abaixo.

---

## Pattern Assignments

### `app.py` — item no `st.sidebar.radio` (config/nav)

**Analog:** a própria lista de menus, `app.py` §587-593.

```python
# app.py §587-593 (VERIFIED) — acrescentar "Comparar ações" à lista.
# Radio é STATELESS (sem key=/index=); "Início" é o 1º item e vira o default.
modo = st.sidebar.radio(
    "O que você quer fazer?",
    ["Início",  # 1º item → vira o default (radio stateless, sem key=/index=)
     "Analisar uma ação", "Garimpar carteira (BSD)", "Ranking por múltiplos",
     "Swing trade (análise técnica)"],
    help=h("menu"),
)
```

**A copiar:** inserir `"Comparar ações"` na lista (posição a critério do plano; sugerido logo após
"Ranking por múltiplos", pois é vizinho conceitual). O guard do novo bloco casa por prefixo:
`elif modo.startswith("Comparar")` — mesmo padrão de todos os outros blocos (§798 `startswith("Analisar")`,
§1216 `startswith("Garimpar")`, §1283 `startswith("Ranking")`, §1392 `startswith("Swing")`).

---

### `app.py` — novo bloco `elif modo.startswith("Comparar")` (view, request-response + fetch cacheado)

Este bloco combina TRÊS analogs já existentes no arquivo. Cada sub-padrão abaixo tem fonte verbatim.

#### Sub-padrão A — Fetch cacheado de N tickers (COMP-01, D5)

**Analog:** aba Ranking `app.py` §1287-1298 (idêntico ao Garimpo §1220-1230).

```python
# app.py §1287-1298 (VERIFIED) — parse + loop montar() cacheado + progress bar.
txt = st.text_area("Tickers (de preferência do mesmo setor)",
                   value="TAEE11, EGIE3, CMIG4, ALUP11, CPFE3, EQTL3")
if st.button("Rankear", type="primary"):
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

**A copiar + adaptar (D5):** após o parse, aplicar **dedup preservando ordem** e **cap soft de N**
(faixa 2–6; default sugerido 5 — ver A1 do RESEARCH). Ex.: `tickers = list(dict.fromkeys(tickers))[:CAP]`.
O embrião de pares (§951) usa o MESMO parse inline `[t.strip().upper() for t in txt.replace(",", " ").split() if t.strip()]`
— manter esse idioma exato. `ANO_BASE`, `N_ANOS`, `CFG` já são globais (§239-241). `montar` é `@st.cache_data(ttl=3600)` (§203-205).

#### Sub-padrão B — Selo COMPLETO por ticker (COMP-03, D3)

**Analog:** aba Analisar `app.py` §828 + §847-851 (produção do selo + render único).

```python
# app.py §828 (VERIFIED) — analisar_acao produz a.selo (Selo completo) + a.veredito, CPU-pura sobre c.
a = report.analisar_acao(c, CFG)

# app.py §847-851 (VERIFIED) — render ÚNICO do selo via presentation.selo_badge.
if a.selo is not None and a.selo.cor is not None:
    badge = presentation.selo_badge(
        a.selo.cor, a.selo.rotulo, a.selo.qualidade, a.selo.verificar
    )
    st.markdown(f"### {esc_md(badge)}")
```

**Assinatura do helper** (`src/analista/report/presentation.py` §117-138, VERIFIED):
`selo_badge(cor, rotulo, qualidade, verificar) -> str`. Já degrada `cor=None → "—"` (§129-130) e trata o
overlay VERIFICAR sufixando "· Verificar dados" e omitindo o rótulo de preço (§134-137). Campos do `Selo`
(`src/analista/report/selo.py` §27-43): `cor`, `qualidade`, `rotulo`, `verificar`.

**A copiar:** por ticker resolvido, `a = report.analisar_acao(c, CFG)` e ler `a.selo`; montar o badge com
`presentation.selo_badge(...)` para pôr como a linha de cabeçalho da coluna do ticker (D2). **NÃO** usar
`selo_emoji(cor_do_bsd(...))` como no Ranking/Garimpo (§1252, §1343) — aquilo dá SÓ a cor, não o quadrante;
insuficiente para COMP-03 (ver Anti-Patterns).

#### Sub-padrão C — 5 múltiplos por ticker (COMP-02)

**Analog:** embrião de pares `app.py` §959 + §963-975.

```python
# app.py §959 (VERIFIED) — fonte canônica dos 5 múltiplos, never-raise.
p = lentes.metricas_par(c)          # ParComparavel(ticker, pl, pvp, roe, dy, valor_mercado, alvo)

# app.py §964-975 (VERIFIED) — formatação None→"—" + Valor de Mercado em bilhões.
vm = fmt_rs(p.valor_mercado / 1e9, casas=1) + " B" if p.valor_mercado is not None else "—"
linha = {
    "P/L": fmt_num(p.pl),
    "P/VP": fmt_num(p.pvp),
    "ROE": fmt_pct(p.roe),
    "DY": fmt_pct(p.dy),
    "Valor de Mercado": vm,
}
```

**Campos de `ParComparavel`** (`src/analista/core/lentes.py` §141-148, VERIFIED): `ticker`, `pl`, `pvp`,
`roe`, `dy`, `valor_mercado`, `alvo`. `metricas_par` é never-raise (§151) — campos `None` quando falta insumo.
`fmt_num`/`fmt_pct`/`fmt_rs` já retornam `"—"` para `None` (app.py §244-253). **A copiar exatamente** a
fórmula de Valor de Mercado (`/1e9 ... + " B"`) do §965 para paridade com a aba Analisar.

#### Sub-padrão D — Regra de suficiência ≥2 (D4) + degradação neutra

**Analog:** guard `if not empresas: st.error(...)` do Ranking (§1299-1300) + `st.info` neutro do embrião (§979).

```python
# app.py §979 (VERIFIED) — degradação graciosa, copy NEUTRA (não é erro).
st.info("Pares insuficientes do mesmo setor para comparar.")
```

**A copiar + adaptar (D4):** `pares_suficientes` NÃO se aplica (exige ≥2 linhas NÃO-alvo; aqui não há alvo —
`lentes.py` §199-209). Regra nova na view: contar `len(empresas)` após o loop; `if len(empresas) >= 2:` renderiza
a tabela, senão `st.info("Informe ao menos 2 tickers com dados para comparar.")`. Sem sort, sem ticker-alvo,
sem `➤`, sem destaque de linha/coluna (o embrião marca `➤` no alvo em §969 — **omitir** aqui, D4).

#### Sub-padrão E — Render transposto: tickers nas COLUNAS (D2, Claude's Discretion)

**Analog:** `st.dataframe(pd.DataFrame(...))` do embrião (§976), Garimpo (§1262) e Ranking (§1350).

```python
# app.py §976 (VERIFIED) — idioma da casa: st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
st.dataframe(pd.DataFrame(_rows_pares), hide_index=True, use_container_width=True)
st.caption("Contexto de comparação — não é ranking nem recomendação.")
```

**A copiar + adaptar (D2 — a diferença-chave):** o embrião é **linha-por-ticker** (`rows` = lista, cada dict
é um ticker). Aqui **transpõe** para **coluna-por-ticker**: montar um dict `{ticker: {"Selo": badge, "P/L": ...,
"P/VP": ..., "ROE": ..., "DY": ..., "Valor de Mercado": ...}}` e `pd.DataFrame(dict_de_dicts)` já vem transposto
(métricas = linhas do índice, tickers = colunas). O "Selo" (badge do sub-padrão B) é a primeira linha (topo de
cada coluna, D2). `pd` já importado (app.py §14). Fechar com `st.caption` neutro espelhando §977/§1264 ("não é
ranking nem recomendação"). Usar `esc_md()` (app.py §256) no nome do ticker exibido (§969 usa em contexto de par).

---

## Shared Patterns

### Fetch cacheado (nunca `st.cache_data.clear()`)
**Source:** `app.py` §203-205 (`montar`), §239-241 (globais `CFG`/`ANO_BASE`/`N_ANOS`)
**Apply to:** o loop do comparador.
```python
@st.cache_data(show_spinner=False, ttl=3600)
def montar(ticker: str, ano_base: int, n: int):
    return build.montar_empresa(ticker, ano_base, n)
```
`montar` é a ÚNICA porta de rede (CVM/Yahoo/BCB) e é cacheada. `analisar_acao`/`metricas_par` são CPU-puras
sobre o `c` já carregado — não tocam a rede (provado: aba Analisar chama `analisar_acao(c, CFG)` sem coleta
extra, §828 sobre §816). NUNCA chamar `st.cache_data.clear()` (apagaria cache global de montar/selic/rf_capm — D-08).

### Formatação None → "—"
**Source:** `app.py` §244-253
**Apply to:** toda célula de métrica.
```python
def fmt_pct(x, casas=1): return "—" if x is None else f"{x*100:.{casas}f}%"
def fmt_num(x, casas=2): return "—" if x is None else f"{x:.{casas}f}"
def fmt_rs(x, casas=2):  return "—" if x is None else f"R$ {x:,.{casas}f}"...  # ptBR
```
Centralizam o sentinela "—". Não escrever `if x is None else ...` inline.

### Escape de markdown no ticker
**Source:** `app.py` §256-259 (`esc_md`)
**Apply to:** qualquer string exibida via `st.markdown`/`metric` que possa conter "$" (e nomes de ticker no
render — o embrião usa em §969). Neutraliza LaTeX/markdown quebrado.

### Selo como render ÚNICO (paridade visual entre menus)
**Source:** `presentation.selo_badge` (§117-138) / `selo_emoji` (§112-114)
**Apply to:** o selo do comparador DEVE usar `selo_badge` (não reconstruir a matriz do quadrante na view).
Mesmo helper de Analisar (§848). Garante que a mesma ação mostra o mesmo selo em todos os menus (Core Value).

---

## Anti-Patterns to Avoid (do RESEARCH, verificados)

| Anti-pattern | Por quê | O certo |
|--------------|---------|---------|
| `selo_emoji(cor_do_bsd(bsd, CFG))` para o selo (como Ranking §1343 / Garimpo §1252) | Dá SÓ a cor, não o quadrante JOIA/VALUE TRAP. D3 exige o selo COMPLETO. | `report.analisar_acao(c, CFG).selo` → `selo_badge(...)` |
| Compor o veredito do DDM à mão em `app.py` | Replicaria ~130 linhas de DDM/CAPM/sensibilidade (report.py §53-207); quebra firewall + paridade. | `analisar_acao(c, CFG)` (única porta do veredito → `.selo`) |
| Ordenar/destacar por métrica; marcar `➤` alvo | Viola D4 e o gate "EXIBE, NUNCA recomenda"; não há alvo natural. | Ordem de entrada fixa, sem sort, sem destaque |
| `st.cache_data.clear()` | Apagaria o cache global de montar/selic/rf_capm (D-08). | Confiar no TTL do `montar` |
| Mexer no expander de pares da aba Analisar (§942-979) | D1 manda deixá-lo INTACTO (propósito diferente: auto-insere `ticker_ativo`, marca `alvo`). | Bloco novo e separado; expander não é tocado |
| Recalcular os 5 múltiplos na view | Perde consistência com Analisar/Ranking. | `lentes.metricas_par(c)` |

---

## No Analog Found

Nenhum. Todos os padrões necessários (fetch de N tickers, selo completo, tabela `st.dataframe`, degradação
neutra, formatação) já existem verbatim em `app.py` e nas funções de engine testadas por golden. O único
elemento "novo" é a **transposição** do DataFrame (dict-de-dicts em vez de lista-de-dicts) — que é rearranjo
do mesmo `st.dataframe(pd.DataFrame(...))`, não um padrão inédito.

## Metadata

**Analog search scope:** `app.py` (blocos Início/Analisar/Garimpar/Ranking/Swing + helpers globais),
`src/analista/core/lentes.py`, `src/analista/report/{report,selo,presentation}.py`, `src/analista/core/screening.py`.
**Files scanned:** 5 (1 view + 4 engine).
**Line numbers:** todos re-verificados via grep nesta sessão (batem com CONTEXT/RESEARCH).
**Pattern extraction date:** 2026-07-03
