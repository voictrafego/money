# Phase 21: Comparador multi-ativo lado a lado (múltiplos + selo por coluna) - Context

**Gathered:** 2026-07-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Promover o embrião "Comparador de pares" (`core/lentes.py` — `metricas_par`/`tabela_pares`,
hoje um expander dentro da aba Analisar preso ao `ticker_ativo`) a um **comparador lado a lado
de N tickers escolhidos pelo usuário**, exibindo os múltiplos (P/L, P/VP, ROE, DY, Valor de
Mercado) e o **Selo da Phase 20 por coluna** para triagem rápida.

É camada de **exibição + derivação leve** sobre números que a engine já calcula (`metricas_par`,
`screening.bsd_empresa`, `selo.montar_selo`, veredito do DDM). Não é novo método.

**Requisitos:** COMP-01 (entrada de N tickers), COMP-02 (tabela comparativa de múltiplos),
COMP-03 (selo por coluna). Depende da Phase 20 (usa o selo).

</domain>

<decisions>
## Implementation Decisions

### D1 — Onde vive o comparador
- **Novo item no `st.sidebar.radio`** ("Comparar ações") — um 5º menu/página dedicado, porque
  o roadmap pede "N tickers **escolhidos pelo usuário**", independentes de qualquer ticker analisado.
- O **expander atual na aba Analisar fica INTACTO** (é contexto de pares do ticker analisado —
  propósito diferente: auto-insere `ticker_ativo` e marca `alvo`). Não mexer nele nesta fase.
- Reusa as funções da engine (`lentes`, `screening`, `selo`) — nada de lógica nova em `app.py`.

### D2 — Layout "lado a lado"
- **Tickers em COLUNAS (transposto):** as métricas viram LINHAS e cada ticker é uma COLUNA.
  As duas expressões do roadmap — "lado a lado" e "selo **por coluna**" — só fecham assim.
- O **selo é a linha de cabeçalho** (um badge por coluna, no topo de cada ticker).
- O embrião atual é linha-por-ticker; aqui transpõe para coluna-por-ticker.

### D3 — Profundidade do selo por coluna
- **Selo completo (quadrante), não só a cor.** COMP-03 diz "o **Selo da Phase 20** por coluna",
  e o Selo da Phase 20 É o quadrante (cor do BSD × veredito do DDM → JOIA / VALUE TRAP / …).
  Só a cor de fundamento (BSD) não seria "o Selo da Phase 20".
- **⚠ Custo a investigar no research/plan:** o veredito por ticker exige rodar o DDM
  (`report.analisar_acao`, que já computa `.selo`), bem mais pesado que `metricas_par`. O planner
  decide o wiring: reusar `analisar_acao(...)` por ticker (que já traz `.selo`) vs. compor
  `screening.bsd_empresa(c, cfg)` + a string de veredito. Mitigação obrigatória: **reusar o cache
  de `montar()`** e **limitar N** (mesmo padrão de fetch da aba Ranking).

### D4 — Ordenação & destaque
- **Ordem de entrada fixa, sem sort, sem ticker-alvo.** Fiel ao embrião (`tabela_pares`
  "NÃO ordena nem recomenda") e ao gate **EXIBE, NUNCA recomenda** — auto-ordenar por métrica
  soa a ranking/recomendação. Num comparador livre não há "alvo" natural → sem destaque de linha/coluna.
- **⚠ Nova regra de suficiência/degradação:** sem alvo, `pares_suficientes` (que exige ≥2 linhas
  NÃO-alvo) não se aplica. Regra nova: exibe a tabela se **≥2 tickers resolvem com dado**; células
  de métrica faltante viram "—"; `st.info` neutro se <2 tickers resolvem.

### D5 — Entrada de N tickers (COMP-01)
- `st.text_input` separado por vírgula/espaço (mesmo padrão do Ranking/embrião), depois
  **upper + dedup + cap de N** (soft, na faixa ~2–6 para não travar o app com o custo do DDM por ticker).

### Claude's Discretion
- Formato exato de render da tabela transposta (ex.: `st.dataframe` de um `pd.DataFrame` com
  tickers nas colunas + linha de selo, vs. `st.columns` com um "card" por ticker) — decisão do plano,
  desde que o selo apareça como badge por coluna e `app.py` siga read-only.
- Valor default do cap de N e placeholder de tickers do `text_input` — a critério do plano.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & fase anterior
- `.planning/ROADMAP.md` → "### Phase 21" (goal, requisitos COMP-01/02/03, gates) e "### Phase 20" (o selo).
- `.planning/phases/20-selo-de-sustentabilidade-do-dividendo-cruzado-com-veredito-d/20-CONTEXT.md`
  — decisões do Selo (cortes de cor, matriz do quadrante, render único, alerta VERIFICAR).

### Engine a reusar (o comparador é derivação + UI)
- `src/analista/core/lentes.py` — `metricas_par(c)` → `ParComparavel` (P/L, P/VP, ROE, DY, Valor de
  Mercado); `tabela_pares(...)`; `pares_suficientes(...)` (referência da regra de suficiência a substituir).
- `src/analista/core/screening.py` §384 — `bsd_empresa(c, cfg)` → BSD (0–100) de 1 ticker (reproduzível/estável).
- `src/analista/report/selo.py` — `montar_selo(bsd, veredito, cfg)` → `Selo` (cor, qualidade, rótulo, alerta).
- `src/analista/report/presentation.py` §103 — `selo_emoji(cor)` / `selo_badge(...)` (render ÚNICO do selo).
- `src/analista/report/report.py` §49, §303 — `analisar_acao(...)` já computa `.selo` e o veredito do DDM por ticker.

### UI / padrão existente
- `app.py` §938–979 — o expander "Comparador de pares (contexto)" atual (referência de padrão; NÃO alterar).
- `app.py` §587–596 — o `st.sidebar.radio` dos menus (onde entra o novo item "Comparar ações").
- `app.py` (aba Ranking, ~§1216+) — padrão de fetch de N tickers via `montar()` cacheado.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lentes.metricas_par(c)`: já entrega as 5 métricas por ticker (never-raise, None quando falta insumo).
- `screening.bsd_empresa(c, cfg)`: BSD de 1 empresa, isolado e reproduzível (não depende de universo).
- `selo.montar_selo(...)` + `presentation.selo_emoji/selo_badge`: derivam e renderizam o selo — usar
  os MESMOS para o comparador ficar visualmente idêntico à Analisar/Garimpo/Ranking.
- `report.analisar_acao(...)`: caminho já pronto que traz `.selo` + veredito por ticker (avaliar custo).
- `montar(ticker, ANO_BASE, N_ANOS)` em `app.py`: fetch cacheado por ticker (reusar p/ os N tickers).

### Established Patterns
- **Firewall `app.py` read-only:** toda derivação (múltiplos, BSD, selo) vive na engine; `app.py` só lê e desenha.
- **Anti-recomendação:** o embrião foi deliberado em NÃO ordenar; manter esse princípio (D4).
- **Config-driven:** cortes de cor do selo e pesos do BSD vêm de `cfg` (mesmos do Garimpo → consistência entre menus).

### Integration Points
- Novo bloco `elif modo.startswith("Comparar")` em `app.py`, espelhando a estrutura das outras abas.
- Reaproveitar a leitura de `cfg`/`ANO_BASE`/`N_ANOS` já existentes no topo do `app.py`.

</code_context>

<specifics>
## Specific Ideas

- "Selo por coluna" = literalmente uma linha de badges no topo, um por ticker (layout transposto).
- Triagem rápida: o usuário digita 3–5 tickers do mesmo setor e bate o olho no selo + múltiplos lado a lado.

</specifics>

<deferred>
## Deferred Ideas

- **Sort neutro por coluna** (clicar num múltiplo para ordenar) — considerado e adiado por tensão com o gate
  "EXIBE, NUNCA recomenda"; candidato a fase futura se ficar claro que ordenar ≠ recomendar.
- **Destaque de um ticker "foco"** no comparador livre — adiado (sem alvo natural nesta fase).
- **Colunas extras** (veredito de preço textual, preço atual, payout) além das 5 múltiplos + selo — o selo já
  embute o veredito; ampliar colunas fica para fase futura se houver demanda.
- **Scanner/comparação sobre universo** (não só tickers digitados) — fora de escopo do marco.

None foldados de todos (nenhum todo pendente cruzou com a fase).

</deferred>

---

*Phase: 21-comparador-multi-ativo-lado-a-lado-m-ltiplos-selo-por-coluna*
*Context gathered: 2026-07-03*
