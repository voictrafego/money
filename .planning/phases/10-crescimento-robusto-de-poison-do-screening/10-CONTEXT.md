# Phase 10: Crescimento robusto + de-poison do screening - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

O **g histórico exibido** (aba Analisar) e os **fatores de crescimento do screening**
(Garimpo BSD + Ranking por múltiplos) passam a vir de uma estimativa **robusta sobre a série
NORMALIZADA** — não mais CAGR endpoint-a-endpoint (`report.py:79`) nem CAGR sobre lucro/dividendo/FCO
**CRU** da CVM (`screening.py:264`). Um único ano extraordinário (fundo/topo) deixa de mandar no g
exibido e no ranqueamento. Vale **para qualquer ticker** por regra geral — VULC3 é só o diagnóstico.

Entrega **GROW-01** (g histórico robusto, fiel à trajetória do lucro normalizado) e **GROW-02**
(screening calcula crescimento de lucro/dividendos/FCO sobre a série normalizada). Resolve também o
**efeito cruzado da Fase 9** (payout sem clamp envenenando a regressão de preço-alvo do Ranking).

Fora de escopo (outras fases do marco): formatação/% e hierarquia de UI, exibição do payout cru do
último ano (Fase 11). A camada de normalização (`normalizacao.py`) é **estendida/reusada** — o DDM
(Cap. 13-17) não é reescrito.
</domain>

<decisions>
## Implementation Decisions

### Estimador robusto do g histórico (GROW-01)
- **D-01:** O `g_historico` usa **regressão log-linear** — OLS de `ln(lucro)` contra o tempo sobre a
  série de lucro **normalizada** (`serie_lucro_normalizada()`, já winsorizada); g anualizado =
  `exp(slope) − 1`. Substitui `growth.cagr(lucros[0], lucros[-1], …)` (endpoint-a-endpoint) em
  `report.py:79`. Usa **todos os pontos** (mata a sensibilidade a um único ano de base/ponta), é o
  padrão de mercado, explicável ("tendência de crescimento") e simples (`numpy.polyfit`).
- **D-02:** Theil-Sen e média aparada de YoY **rejeitados**: a série tem ≤8-10 pontos e já vem
  winsorizada, então o ganho de robustez extra é marginal e custa explicabilidade/código.

### Fallback p/ anos não-positivos (GROW-01)
- **D-03:** Se a série normalizada tem **qualquer ano ≤ 0** (prejuízo) — onde `ln` é indefinido —
  `g_historico = None`. Mantém a fronteira de None do CAGR atual (que já exige endpoints positivos):
  crescimento composto não é definível sobre prejuízo. O piso já existente `g_alto = max(0, …)`
  (`report.py:97`) trata o downstream. **Não** introduzir fallback aritmético que mudaria a fronteira
  de None (risco de regressão nos golden).

### Base e estimador do crescimento no screening (GROW-02)
- **D-04:** O screening (BSD em `indicadores_bsd` + Ranking por múltiplos) reusa o **MESMO estimador
  log-linear** sobre as séries **normalizadas**, substituindo `cagr_serie` (`screening.py:261-264`).
  Consistência total Analisar↔Screening **por construção**: a mesma empresa não ranqueia diferente do
  que o Analisar exibe.
- **D-05:** Normalizar as **três** séries de crescimento do BSD via `normalizacao.serie_winsorizada`
  (a primitiva já existe): `crescimento_lucro_3a`, `crescimento_dividendos_3a`, `crescimento_fc_3a`
  (lucro + dividendos + FCO). Um ano extraordinário de provento/caixa também envenena, não só o lucro.

### Clamp do payout na regressão de preço-alvo (efeito cruzado Fase 9)
- **D-06:** Aplicar `min(payout, 1.0)` **APENAS na entrada** de `preco_alvo_por_regressao`
  (`comparables.py` §L133; chamadas em `cli.py:158-159` e `app.py:472`). **NÃO** reintroduzir clamp
  no `payout_valuation()` canônico (D-03 da Fase 9 preservado — a mediana pode ser legitimamente >100%,
  TAEE11 ≈ 216%). É exatamente o que o handoff `09-CROSS-EFFECT-FASE10.md` recomendou: localizado e
  mínimo. Recalibrar a regressão / excluir tickers >100% foram **rejeitados** (mais escopo/risco;
  removeria nomes legítimos do preço-alvo).

### Fronteira CRU per-ano preservada (invariante do marco)
- **D-07:** Só os **agregados de crescimento** mudam de base. `roe(ano)`/`payout(ano)`/lucro **CRU**
  seguem alimentando a elegibilidade per-ano (Cap. 8), o detector de armadilha e a tabela "Fundamentos
  (por ano)". A banda absoluta `REFERENCIA_BSD` (`screening.py:192`, `payout: (0.0, 0.80)`) e o
  proxy per-ano `crescimento_por_fundamentos(roe_medio, payout_medio)` per-ano (`screening.py:256-258`)
  ficam intactos — só o fator de crescimento de série (lucro/div/FCO) muda de base.

### Claude's Discretion
- Onde colocar o estimador log-linear (função pura nova em `growth.py` recebendo a série, espelhando
  `cagr`/`crescimento_aritmetico`; só `numpy`/`statistics`, sem ciclo de import) e a assinatura exata
  ficam a critério do planner.
- Se haverá knob de config para o estimador — segue o padrão do bloco `normalizacao` do config.yaml se
  necessário; default sem knob novo é aceitável.
- Rebaseline deliberado dos golden tests afetados pela troca de estimador (com validação multi-ticker,
  ver `<specifics>`) é esperado e fica a critério do planner/executor.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engine de crescimento / normalização (a estender)
- `src/analista/core/growth.py` — `cagr` (L16), `crescimento_aritmetico` (L32),
  `crescimento_por_fundamentos` (L49) — padrão de função pura; o estimador log-linear é uma irmã delas.
- `src/analista/core/normalizacao.py` — `serie_winsorizada` (L97) / `base_normalizada` — a primitiva de
  normalização a aplicar nas séries de dividendos e FCO do screening.
- `src/analista/core/fundamentals.py` §`serie_lucro_normalizada` (L126), `serie` — séries por ano.

### Pontos de cálculo a corrigir
- `src/analista/report/report.py` §`analisar_acao` L72-98 — `g_historico` (L79, o CAGR a substituir),
  `g_alto` (precedência L93-98, piso `max(0,…)` L97), `g_fundamentos` (L82).
- `src/analista/core/screening.py` §`indicadores_bsd` L242-277 — `cagr_serie` (L261-264, a substituir),
  fatores `crescimento_lucro_3a`/`crescimento_dividendos_3a`/`crescimento_fc_3a` (L274-276); fronteira
  per-ano a preservar: `REFERENCIA_BSD` (L192-201), proxy per-ano (L256-258).
- `src/analista/core/comparables.py` §`preco_alvo_por_regressao` (L133) — clamp do payout na entrada;
  chamadas em `cli.py:158-159` e `app.py:472`.

### Requisitos, roadmap e handoff
- `.planning/REQUIREMENTS.md` — GROW-01, GROW-02 (e invariante de não-regressão multi-ticker do marco).
- `.planning/ROADMAP.md` §Phase 10 — goal e 5 success criteria.
- `.planning/phases/09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia/09-CROSS-EFFECT-FASE10.md`
  — o efeito cruzado do payout sem clamp na regressão (origem de D-06).
- `.planning/phases/09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia/09-CONTEXT.md` — decisões
  da Fase 9 (D-01..D-06: payout sem clamp, base normalizada, fronteira CRU vs valuation).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `growth.cagr` / `crescimento_aritmetico`: padrão de função pura (recebe sequência, devolve `Number`
  com fronteira de None). O estimador log-linear deve ser uma irmã: pura, `numpy`/`statistics` só.
- `normalizacao.serie_winsorizada`: já aplicada ao lucro; estender para dividendos e FCO no screening.
- `fundamentals.serie_lucro_normalizada()`: a série winsorizada que o g_historico log-linear consome.

### Established Patterns
- Métodos canônicos `*_valuation` chamados sem args nas 3 superfícies (Analisar / Ranking app /
  Ranking cli) → consistência entre menus por construção (FIX-04, Fase 8). O estimador de crescimento
  do screening deve seguir a mesma lógica de fonte única.
- Fronteira CRU vs normalizado (D-06 Fase 9): valores per-ano crus alimentam tabela/screening per-ano;
  só o agregado de crescimento usa a base normalizada. Manter.

### Integration Points
- `report.analisar_acao` consome `g_historico` → muda só a fórmula (CAGR → log-linear); `g_alto` e o
  resto do report seguem iguais (g_alto já lê g_historico).
- `screening.indicadores_bsd` consome `cagr_serie` → trocar pela chamada ao estimador log-linear sobre
  série normalizada; o resto do dict de indicadores e a banda `REFERENCIA_BSD` ficam iguais.
- `comparables.preco_alvo_por_regressao` recebe `payout_valuation()` → clampar na entrada (sem mexer no
  método canônico).
</code_context>

<specifics>
## Specific Ideas

- **Validação multi-ticker é critério de aceite explícito** (princípio do marco): VULC3 (caso-limite)
  + TAEE11/EGIE3/ITUB4/BBAS3 (normais). Asserts da fase: (a) em VULC3 o ano extraordinário NÃO infla o
  BSD nem o g exibido; (b) em tickers normais o g exibido e o ranqueamento NÃO regridem materialmente
  vs. o estado atual; (c) TAEE11 (payout ≈ 2.16) NÃO distorce o preço-alvo/Ranking após o clamp de
  entrada (D-06).
- Os golden tests afetados pela troca CAGR→log-linear devem ser **rebaselinados deliberadamente** (não
  silenciosamente), documentando o delta esperado por ticker.
</specifics>

<deferred>
## Deferred Ideas

- Formatação `%` do DY rec. e hierarquia/destaque de apresentação, payout cru do último ano exibido —
  **Fase 11** (já no roadmap). Inclui o bug de formatação de `DY rec.` em `app.py:324`
  (cai no `else`/`fmt_num` em vez do `fmt_pct`).
- Revisitar se o DY recorrente earnings-based deve virar híbrido p/ não subestimar quem distribui de
  reservas (TAEE11) — insumo de metodologia, não escopo da Fase 10.
- Payout-alvo por setor configurável; sinalização explícita de "ano extraordinário" na tabela de
  Fundamentos por ano — Future Requirements (v2+).
- Knob de config para escolher estimador de g (log-linear vs CAGR) — só se houver demanda; default
  log-linear sem knob é aceitável.

</deferred>

---

*Phase: 10-Crescimento robusto + de-poison do screening*
*Context gathered: 2026-06-27*
