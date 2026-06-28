# Phase 9: Payout sustentável + DY recorrente (núcleo de metodologia) - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Tornar o **payout-para-valuation** e o **DY recorrente** fiéis à renda **sustentável** de
**qualquer ticker**, expurgando anos não-recorrentes por **regra geral data-driven** (sem constante
por empresa, sem limiar absoluto). Estende a primitiva de `normalizacao.py` para o payout e o
provento; o DDM (Cap. 13-17) NÃO é reescrito — só passa a consumir inputs saneados.

Entrega os requisitos **DYR-01** (DY recorrente = lucro normalizado × payout sustentável) e
**PAY-01** (payout sustentável que expurga não-recorrentes de forma geral).

Fora de escopo desta fase (outras fases do marco): formatação/% e hierarquia de UI (Fase 11),
g histórico robusto e de-poison do screening (Fase 10), exibição do payout cru do último ano (Fase 11).
</domain>

<decisions>
## Implementation Decisions

### Estimador do payout sustentável (PAY-01)
- **D-01:** `payout_sustentável` = **mediana de `payout(ano)` sobre a série histórica COMPLETA**
  (todos os anos com payout não-None), NÃO a média/mediana crua dos últimos 3 anos. Robusto por
  construção: um desvio do normal da própria empresa é naturalmente descartado pela mediana, sem
  precisar marcar/excluir anos explicitamente.
- **D-02:** Critério REJEITADO: "expurgar anos com payout >100%". O **TAEE11 é o contraexemplo
  decisivo** — paga >100% em TODOS os 10 anos (política recorrente de transmissora, distribui de
  caixa regulatório acima do lucro contábil). Esse critério zeraria o TAEE11 (zero anos restantes) e
  rebaixaria injustamente quem distribui muito de forma sustentável. Limiar absoluto é errado;
  "extraordinário" = desvio do próprio histórico, capturado pela mediana.
- **D-03:** **Sem clamp em 1.0.** A mediana pode legitimamente ficar >100% (TAEE11 ≈ 216%). Remover
  o `min(..., 1.0)` do payout de valuation. Para o `g_fundamentos` (`ROE_norm × (1 − payout)`),
  payout >100% ⇒ g_fund ≤ 0 ⇒ o **piso já existente** `g_alto = max(0, …)` (report.py) o trata
  (g_alto 0 — correto para uma cash-cow madura). Nenhum piso novo.

### Janela e fallback (PAY-01)
- **D-04:** Janela = **série completa** (não 3a). A janela curta de 3a é o que satura o clamp num
  único regime anômalo (VULC3 2023-25; TAEE11 todos os anos). Fallback gracioso: série vazia/só-None
  → `None` (como hoje); 1 ano de payout → o próprio valor; preserva a fronteira de None existente.

### Derivação do DY recorrente (DYR-01)
- **D-05:** `DY_recorrente` = **`payout_sustentável × lucro_normalizado_por_ação ÷ preço`**
  (earnings-based), reusando `base_lucro_normalizada()` / `lpa_valuation()` da Fase 8. NÃO mais a
  mediana crua de 3 anos da série de dividendos (que, no VULC3, cai inteira na era de payout >100% e
  devolvia 20,4% falso). Consistente com o `g_fund` (mesmo `payout_sustentável`). Validado:
  TAEE11 earnings-based 8,3% ≈ dividend-based real 8,1% (sanidade); VULC3 cai de 20,4% → 6,2%
  sustentável.

### Fronteira preservada (PAY-01, invariante)
- **D-06:** Só o **agregado de valuation** muda de base. `payout(ano)` CRU continua alimentando a
  tabela "Fundamentos (por ano)", o detector de armadilha (payout >100%) e a elegibilidade do
  screening por-ano (Cap. 8). Não tocar essas superfícies nesta fase.

### Claude's Discretion
- Nome/assinatura exatos dos métodos (ex.: estender `payout_valuation` vs. novo `payout_sustentavel`)
  e onde colocar a primitiva (em `normalizacao.py` como função pura recebendo a série de payouts, ou
  em `fundamentals.py`) ficam a critério do planner — desde que a primitiva pura siga sem ciclo de
  import (só numpy/statistics), espelhando `base_normalizada`.
- Knob de config (se algum) para a metodologia segue o padrão do bloco `normalizacao` do config.yaml.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engine de valuation / normalização (a estender)
- `src/analista/core/normalizacao.py` — primitiva pura existente (`base_normalizada` = mediana p/
  2≤N<5, média winsorizada p/ N≥5; `serie_winsorizada`). A mediana-de-payout segue este espírito.
- `src/analista/core/fundamentals.py` §`payout_valuation` (L77), §`base_lucro_normalizada`/
  `lpa_valuation` (L122-135), §`dpa_recorrente`/`dy_recorrente` (L173-181) — os métodos a corrigir.
- `src/analista/report/report.py` §`analisar_acao` (L50-107) — `g_fundamentos`, `g_alto` (piso
  `max(0,…)` em L96-97), `multiplos["DP (payout)"]`, `multiplos["DY rec."]`.

### Requisitos e roadmap
- `.planning/REQUIREMENTS.md` — DYR-01, PAY-01 (e o invariante TEST-08 do marco).
- `.planning/ROADMAP.md` §Phase 9 — goal e success criteria (5 critérios).

### Efeito cruzado a verificar na Fase 10 (NÃO resolver aqui)
- `src/analista/core/screening.py` §`bsd_ranking`/regressão de P/L — o `payout_valuation` SEM clamp
  (ex.: TAEE11 216%) passa a alimentar a regressão P/L ~ f(payout, ROE), calibrada com payout em
  [0,1]. Registrar e verificar na Fase 10 (de-poison do screening) que isso não distorce o Ranking;
  decisão de clampar só na entrada da regressão fica para lá.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `normalizacao.base_normalizada` / `media_winsorizada`: padrão de primitiva pura (recebe sequência
  de números com None, devolve número robusto). A mediana-de-payout deve ser uma irmã dela.
- `fundamentals.base_lucro_normalizada()` / `lpa_valuation()`: o "lucro normalizado por ação" que o
  DY recorrente earnings-based vai multiplicar pelo payout sustentável.
- `fundamentals.serie("dividendos")` / `payout(ano)`: séries por ano já disponíveis.

### Established Patterns
- FIX-04 (Fase 8): métodos canônicos de valuation (`*_valuation`) chamados sem args nas 3 superfícies
  (Analisar / Ranking app / Ranking cli) → consistência entre menus por construção. O payout
  sustentável deve seguir o mesmo padrão canônico.
- Fronteira CRU vs normalizado: valores per-ano crus alimentam tabela/screening; só o agregado de
  valuation usa a base normalizada. Manter.

### Integration Points
- `report.analisar_acao` consome `payout_valuation()` e `dy_recorrente()` → muda só a implementação
  desses métodos; a chamada e o resto do report ficam iguais.
- `g_fundamentos = ROE_norm × (1 − payout_sustentável)` já existe; com payout sem clamp, o piso do
  g_alto trata >100%.
</code_context>

<specifics>
## Specific Ideas

- Validação multi-ticker é critério de aceite explícito (princípio do marco): VULC3 (caso-limite) +
  TAEE11/EGIE3/ITUB4/BBAS3 (normais). Números-alvo da discussão (mediana de payout): VULC3 43%,
  TAEE11 216% (preservado), EGIE3 49%, ITUB4 31%, BBAS3 20%. DY recorrente novo: VULC3 6,2%,
  TAEE11 8,3%. Usar como golden/asserts da fase.
</specifics>

<deferred>
## Deferred Ideas

- Clampar o payout só na entrada da regressão de P/L do Ranking — decisão da **Fase 10** (de-poison),
  não desta fase.
- Payout-alvo por setor configurável (refino além do data-driven) — Future Requirements (v2+).
- Sinalização explícita de "ano extraordinário" na tabela de Fundamentos por ano — Future (v2+).
</deferred>

---

*Phase: 9-Payout sustentável + DY recorrente (núcleo de metodologia)*
*Context gathered: 2026-06-27*
