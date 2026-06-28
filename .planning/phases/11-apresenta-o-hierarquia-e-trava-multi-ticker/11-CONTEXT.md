# Phase 11: Apresentação, hierarquia e trava multi-ticker - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

A aba **Analisar** passa a destacar a **renda sustentável**: o **DY recorrente** vira a métrica
principal do header (formatado como **%**), o **DY trailing** inflado é rebaixado a contexto
rotulado, e o **payout cru real do último ano** é exibido como número distinto do payout
sustentável de valuation. Fecha o marco v1.3 com a **trava de validação multi-ticker**
(VULC3 + ITUB4/EGIE3/TAEE11/BBAS3).

Entrega **DYR-02** (DY rec. formatado como %), **PAY-02** (payout cru do último ano vs. payout
sustentável), **HIER-01** (header destaca o recorrente, rebaixa o trailing) e **TEST-08**
(trava multi-ticker).

Tudo é **apresentação sobre campos que a engine JÁ expõe** (`dy_recorrente`/`dy_atual`/`payout`/
`payout_valuation`). **`app.py` permanece read-only** quanto ao método — não recalcula nem
reescreve fórmula. A engine de valuation NÃO é tocada nesta fase, logo os golden de valuation
seguem **verdes sem rebaseline**.

Fora de escopo: qualquer mudança de metodologia/engine (já fechada nas Fases 9-10); payout-alvo
por setor; sinalização de "ano extraordinário" na tabela por ano (Future v2+).
</domain>

<decisions>
## Implementation Decisions

### Header — hierarquia do DY (HIER-01)
- **D-01:** A coluna **m3** do header (`app.py:131-136`, hoje `"Dividend Yield"` lendo
  `a.multiplos["DY"]` = trailing) passa a exibir o **DY recorrente** (`a.multiplos["DY rec."]` =
  `dy_recorrente`, sustentável) como **valor principal**. Rótulo do tipo "Dividend Yield
  (recorrente)".
- **D-02:** O **DY trailing** (`dy_atual`) aparece como `st.metric(delta=…)` logo abaixo, com
  **`delta_color="off"`** (cinza neutro — NÃO verde/vermelho), rotulado "trailing X%". Motivo: o
  trailing costuma ser MAIOR que o recorrente (inflado); o delta positivo padrão pintaria verde e
  passaria conotação enganosa de "bom" justamente onde se quer alertar.
- **D-03:** **Fallback** quando `dy_recorrente` é None (anos de prejuízo → lucro normalizado
  indefinido): o header cai para o **DY trailing como valor principal**, com rótulo explícito
  ("trailing — recorrente indisponível"). Degrada gracioso, sempre mostra um número útil, espelha a
  fronteira de None do resto do app (padrão GRAF-03).

### Sinalização do DY inflado (HIER-01)
- **D-04:** **Sem badge/chip novo.** A própria hierarquia (recorrente em destaque, trailing
  rebaixado e neutro) + os **alertas de armadilha que a engine já emite** (`a.alertas`, via
  `flag_dy`/`flag_payout` em `report.py:155-200`, já renderizados como avisos amarelos em
  `app.py:145-147`) bastam para comunicar o risco. Não adicionar elemento novo evita redundância e
  ruído visual; alinhado ao "app.py mínimo/read-only". Limiar de divergência e legenda fixa foram
  **rejeitados**.

### Payout duplo — rótulos e fonte (PAY-02)
- **D-05:** A linha **"Payout (último ano)"** passa a ler `c.payout(ult)` **CRU** (sem clamp; ex.:
  VULC3 124,7%). **Bug atual:** `app.py:317` lê `a.multiplos["DP (payout)"]`, que em
  `report.py:66` é `c.payout_valuation()` (sustentável) — então hoje AS DUAS linhas mostram o mesmo
  valor. O valor cru já está disponível (a engine usa `c.payout(ult)` em `report.py:156` para o
  detector de armadilha). Continua read-only: só lê outro campo já exposto.
- **D-06:** A linha do payout sustentável é rotulada **"Payout p/ valuation (sustentável)"**,
  removendo o obsoleto "(média 3a)" — desde a Fase 9 é a **mediana da série histórica completa**
  (sem clamp), não média de 3 anos. Mantém o vínculo "p/ valuation" com o DDM.

### Varredura de rótulos/comentários obsoletos (apresentação)
- **D-07:** Corrigir rótulos defasados das Fases 9-10 nesta fase (fidelidade de apresentação,
  baixo risco):
  - `app.py:333` "g histórico (CAGR lucro)" → fiel à Fase 10 (regressão **log-linear** sobre série
    normalizada), ex.: "g histórico (tendência log-linear)".
  - Comentários/captions defasados, ex.: `app.py:318` "média 3a + clamp 1.0", `app.py:323`
    rótulo "(média 3a)", e o comentário errado em `app.py:317` ("= c.payout(ult), último ano cru"
    quando na verdade lê `payout_valuation()`).

### Trava de validação multi-ticker (TEST-08)
- **D-08:** Trava em **duas camadas** (mesmo padrão das Fases 9-10):
  (a) **Teste automatizado de apresentação** — extrair a lógica de formatação/montagem do `app.py`
  (inline no Streamlit, hoje não-testável) para **helpers puros** e travar por golden nos 5 tickers:
  DY rec. → formatado como %; payout último ano → cru (`c.payout(ult)`); header → escolhe o
  recorrente (e o fallback p/ trailing).
  (b) **Checkpoint manual ao vivo** dos 5 tickers (VULC3 + ITUB4/EGIE3/TAEE11/BBAS3) confirmando
  visualmente a apresentação real do Streamlit (delta cinza, layout, %).
- **D-09:** Os **helpers puros** extraídos moram em **novo módulo sob `src/` (ex.:
  `src/analista/report/presentation.py`)**, importado tanto pelo `app.py` (que vira chamador fino)
  quanto pelos testes. Espelha a separação já existente da camada de report (`relatorio_markdown`).
  Devem ser **puros e importáveis sem subir o Streamlit** (sem efeito colateral de import). Testar
  via `from app import …` foi **rejeitado** (arrasta efeitos colaterais do app Streamlit).
- **D-10:** **Sem rebaseline dos golden de valuation** — a engine não é tocada nesta fase. Os
  golden existentes seguem verdes; a única massa nova de teste é o golden de apresentação (D-08a).

### Claude's Discretion
- Texto exato dos rótulos/labels do header e das linhas (seguindo o tom dos demais e o glossário
  `h(...)`), desde que: DY rec. apareça como %, "média 3a" suma, e o g histórico não diga mais
  "CAGR".
- Nome/assinatura exatos dos helpers puros e do módulo (`report/presentation.py` é sugestão), desde
  que puros e importáveis sem Streamlit.
- Rótulo/texto do tooltip `help` das métricas/linhas afetadas.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### UI a alterar (apresentação read-only)
- `app.py` §header do Analisar L88-147 — métricas m1..m5 (L131-136; m3 `"Dividend Yield"` L134 é o
  alvo do DY recorrente); fallback de preço/alertas L138-147.
- `app.py` §aba "Múltiplos & Crescimento" L309-339 — montagem de linhas (L317-327: `payout_ult`,
  `payout_proj`, ramo `%` `("ML","ROE","DY","EY")` que NÃO inclui `"DY rec."` → bug DYR-02);
  rótulos obsoletos (L315 caption, L318 comentário, L323 "média 3a", L333 "CAGR lucro").
- `app.py` §helpers de formatação L51-55 — `fmt_pct` (L51), `fmt_num` (L55); padrão de função pura
  local que os novos helpers de apresentação espelham/movem para `src/`.

### Campos da engine que a UI consome (JÁ expostos — não recalcular)
- `src/analista/report/report.py` §`analisar_acao` — `a.multiplos` (L61-69): `"DP (payout)"` =
  `payout_valuation()` (L66), `"DY"` = `dy_atual()` trailing (L68), `"DY rec."` = `dy_recorrente()`
  sustentável (L69); `a.alertas`/armadilha (`flag_dy`/`flag_payout` L155-200); `payout_ult =
  c.payout(ult)` CRU (L156); ramo % do CLI que JÁ formata DY rec. certo (L396-397 — referência de
  paridade).
- `src/analista/core/fundamentals.py` — `payout(ano)` CRU, `payout_valuation()` (mediana série
  completa, sem clamp), `dy_atual()`, `dy_recorrente()` (earnings-based).

### Requisitos, roadmap e contexto das fases anteriores
- `.planning/REQUIREMENTS.md` — DYR-02, PAY-02, HIER-01, TEST-08 (e invariante de não-regressão
  multi-ticker do marco).
- `.planning/ROADMAP.md` §Phase 11 — goal e 5 success criteria.
- `.planning/phases/09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia/09-CONTEXT.md` —
  payout sustentável (mediana série completa, sem clamp, D-01..D-04) e DY recorrente earnings-based
  (D-05); fronteira CRU vs valuation (D-06).
- `.planning/phases/10-crescimento-robusto-de-poison-do-screening/10-CONTEXT.md` — g histórico
  log-linear (D-01, origem do rótulo a corrigir) e nota diferida explícita da Fase 11 (bug de
  formatação `DY rec.` + hierarquia + payout cru).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app.py:fmt_pct` / `fmt_num`: padrão de função pura local de formatação — base dos helpers de
  apresentação a extrair para `src/analista/report/presentation.py`.
- `report.relatorio_markdown` (CLI): JÁ formata `"DY rec."` como % (`report.py:396-397`) — é a
  paridade-alvo do app e prova de que o campo existe e o bug é só do `app.py`.
- Campos `dy_recorrente`/`dy_atual`/`payout(ano)`/`payout_valuation()` já expostos pela engine —
  a fase só os apresenta/rotula, sem recalcular (read-only).

### Established Patterns
- **`app.py` read-only quanto ao método** (invariante do marco): a UI lê campos saneados e formata;
  nunca recalcula o valuation. Manter.
- **Fronteira CRU vs sustentável**: `c.payout(ult)` cru alimenta a linha "último ano" e o detector
  de armadilha; `payout_valuation()` sustentável alimenta o DDM e a linha "p/ valuation". A Fase 11
  só torna essa distinção VISÍVEL (hoje as duas linhas colapsam no mesmo valor).
- **Trava multi-ticker em 2 camadas** (golden offline de propriedade + checkpoint live dos 5
  tickers) — padrão das Fases 9 e 10; reaplicar aos helpers de apresentação.

### Integration Points
- Header (m3) e tabela de Múltiplos consomem `a.multiplos` / `c.payout(ult)` → mudam só a
  apresentação (qual campo, formato %, rótulo, delta neutro).
- Novo módulo `report/presentation.py` ↔ `app.py` (chamador fino) ↔ testes (import direto, sem
  Streamlit).
</code_context>

<specifics>
## Specific Ideas

- **Conjunto de validação multi-ticker (critério de aceite explícito do marco):** VULC3 (caso-limite)
  + ITUB4/EGIE3/TAEE11/BBAS3 (normais). Asserts esperados: VULC3 mostra DY rec. ~6% (não 20% trailing)
  e Payout (último ano) 124,7% cru distinto do sustentável ~43%; tickers normais não regridem na
  apresentação.
- **Delta do header em cinza** (`delta_color="off"`) é decisão de design firme — não deixar o
  Streamlit pintar verde/vermelho no trailing.
</specifics>

<deferred>
## Deferred Ideas

- Revisitar se o DY recorrente earnings-based deve virar híbrido para não subestimar quem distribui
  de reservas (TAEE11) — insumo de metodologia (engine), não escopo de apresentação.
- Payout-alvo por setor configurável; sinalização explícita de "ano extraordinário" na tabela de
  Fundamentos por ano — Future Requirements (v2+).
- None — discussão ficou dentro do escopo de apresentação da fase.

</deferred>

---

*Phase: 11-Apresentação, hierarquia e trava multi-ticker*
*Context gathered: 2026-06-27*
