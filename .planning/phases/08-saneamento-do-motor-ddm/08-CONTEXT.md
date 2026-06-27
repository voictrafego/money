# Phase 8: Saneamento do motor DDM (caso VULC3) — Context

**Gathered:** 2026-06-26
**Status:** Ready for planning
**Source:** Diagnóstico externo VULC3 + verificação linha-a-linha (`08-saneamento-do-motor-ddm/FINDINGS.md`) + decisões de metodologia capturadas com o usuário.

<domain>
## Phase Boundary

Corrigir a divergência estrutural do valuation fundamentalista (DDM/múltiplos) exposta pelo
caso VULC3: intrínseco R$ 167–334 vs preço R$ 14, veredito "SUBAVALIADA" sobre uma divergência
de modelo. FIX-01 (trava `g_alto ≤ Ke`) e FIX-05 (veredito consome flags) **já aplicados**.
Esta fase entrega os 4 fixes restantes: FIX-04 (normalização de lucro — raiz), FIX-02
(reconciliação g×payout), FIX-03 (CAPM ao vivo), FIX-06 (guardrails/regressão).

**Fora de escopo:** Phase 7 (UI dos indicadores técnicos). A camada de indicadores técnicos
(v1.2, Phases 4-6) não é tocada aqui — esta fase mexe só no motor fundamentalista.
</domain>

<decisions>
## Implementation Decisions (LOCKED)

### FIX-04 — Normalização de lucro (raiz a montante)
- **DECISÃO:** Base de lucro normalizada = **mediana (ou média winsorizada/aparada) do lucro
  líquido de N anos**, usada como base para ROE, CAGR, payout e DY — em vez do lucro CVM cru de
  um único exercício.
- Robusto a um ano atípico (recuperação de créditos fiscais, distribuição extraordinária),
  escala para toda a B3, custo zero.
- **Consistência com o livro:** o BSD (Cap. 8.4) já usa médias trienais + winsorização 10%
  (`config.yaml: bsd.anos_media: 3`, `bsd.winsor: 0.10`). Reaproveitar esse espírito; janela `N`
  vem de config (provável `anos_media`/novo knob), não hardcoded.
- A série de lucro para CAGR (`growth.cagr`) e o `lucro_liquido.get(ult)` que alimenta
  ROE/payout/DY passam pela camada normalizada.

### FIX-02 — Reconciliação g × fundamentos
- **DECISÃO:** O teto do `g_alto` adotado passa a ser o **g sustentável por fundamentos
  calculado com o MESMO payout usado no valuation** (`g_fund = ROE_normalizado × (1 − payout_valuation)`).
- Payout ≥ 100% ⇒ `g_fund ≤ 0` ⇒ `g_alto` cai para 0 (**sem o piso artificial `g_estavel`** na
  fase explícita quando os fundamentos não sustentam crescimento).
- Hoje (`report.py:76-78`) `g_alto = CAGR clampado [g_estavel, 0.25]` e ignora `g_fundamentos`.
  A nova regra subordina o g ao reinvestimento real, mantendo o teto absoluto e a trava `≤ Ke`
  (FIX-01) que já existe.

### FIX-03 — CAPM / Ke
- **DECISÃO:** Trocar a abordagem padrão para **`local` com Selic ao vivo do BCB**:
  `rf = macro.selic_meta()` (já existe), `ERP Brasil` fixo razoável (~6–8% — valor exato a
  definir no plano, documentado), `beta` atual. `ke_local(beta, rf, erp)` já existe.
- **Fallback:** se o BCB estiver indisponível (`selic_meta()` → None), degradar para os literais
  atuais (ou último valor conhecido) sem quebrar — espelhar o padrão de degradação graciosa do
  encanamento (GRAF-03/DATA-03).
- Objetivo: Ke coerente com small cap BR (faixa ~16–19%), não os 9,4% dos literais de 2019.

### FIX-06 — Guardrails e regressão (obrigatório, sem fork)
- DY recorrente vs trailing: expor/usar uma noção de DY recorrente (sobre dividendo normalizado),
  não só o trailing sobre extraordinários.
- Banda intrínseca: confirmar que `vmin/vmax` reflete sensibilidade real (a matriz
  `ddm.matriz_sensibilidade` já existe) e não só o toggle binário `ddm_constante` × `ddm_h`.
- Setor: corrigir o mapeamento (VULC3 = Calçados/Consumo Cíclico, não Têxtil) na ingestão.
- **VULC3 vira caso de regressão** explícito (golden) — intrínseco deixa de ser 11–23× o preço.

### Rebaseline dos golden tests (LOCKED)
- Os 64 golden tests de valuation **mudam de valor deliberadamente** — os números antigos
  estavam errados. Recalcular os esperados com justificativa documentada (não "manter verde a
  qualquer custo"). Cada novo esperado precisa de uma linha explicando por que o novo número é
  o correto pelo método.

### Claude's Discretion
- Estrutura interna (nova camada/módulo de normalização vs métodos em `fundamentals.py`).
- Janela `N` exata da normalização e valor exato do ERP Brasil — propor no plano com base no
  livro/dados, documentar.
- Onde mora o fallback do CAPM e o mapa de setor.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Diagnóstico verificado
- `.planning/phases/08-saneamento-do-motor-ddm/FINDINGS.md` — sintoma, verificação linha-a-linha
  (itens A–K), cascata de dependência, fixes priorizados.

### Código do motor (fonte da verdade)
- `src/analista/report/report.py` — seleção de g (L67-79), CAPM (L88-106), DDM (L108-124),
  flags+veredito (L126+). Orquestra tudo.
- `src/analista/core/ddm.py` — `ddm_dois_estagios`, `valor_gordon`, `matriz_sensibilidade`.
- `src/analista/core/fundamentals.py` — `payout`, `payout_valuation` (L76, média 3a + clamp 1.0),
  `roe`, `serie`, `lucro_liquido` (CVM cru).
- `src/analista/core/growth.py` — `crescimento_por_fundamentos` (g=ROE×(1-payout)), `cagr`,
  `crescimento_estavel`.
- `src/analista/core/capm.py` — `ke_local`, `ke_eua_ajustada`, `CapmParams`.
- `src/analista/ingest/macro.py` — `selic_meta()`, `ipca_12m()` (BCB SGS ao vivo).
- `config.yaml` — bloco `capm` (literais 2019), `ddm`, `bsd` (winsor/médias trienais).
- `tests/` — golden de valuation a rebaselinar: `test_ddm.py`, `test_fundamentals_consistencia.py`,
  `test_multiples.py`, `test_report.py`, `test_consistencia_modos.py`.
</canonical_refs>

<specifics>
## Specific Ideas

- Caso de teste âncora: **VULC3** (Vulcabras), relatório 26/06/2026. Critério de sucesso visível:
  intrínseco deixa de ser 11–23× o preço; veredito não volta a "SUBAVALIADA" verde; Ke sobe p/
  faixa de small cap BR; g adotado coerente com payout ≥100% (→ ~0).
- Ordem de ataque (cascata da FINDINGS): FIX-04 (raiz) → FIX-02 → FIX-03 → FIX-06.
</specifics>

<deferred>
## Deferred Ideas

- Comparáveis/beta setorial usando o setor corrigido (só relevante se algum cálculo passar a
  consumir setor — hoje é display).
- Reescrita do gráfico "preço vs intrínseco" para recalcular a banda mês-a-mês com fundamentos da
  época (item I) — fica como melhoria; nesta fase basta o caso de regressão.
</deferred>

---

*Phase: 08-saneamento-do-motor-ddm*
*Context gathered: 2026-06-26*
