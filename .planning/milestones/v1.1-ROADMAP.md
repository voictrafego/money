# Roadmap: Analista de Dividendos

## Overview

Dois marcos vivem neste roadmap. **v1.0 — "Consistência entre menus"** (Phases 1-2, completo): marco de remediação que corrige as inconsistências de `CONSISTENCY-REVIEW.md` (3 críticos + 7 warnings) para que a mesma ação produza números coerentes nos três modos do app (`Analisar`, `Garimpar BSD`, `Ranking por múltiplos`), mudando o comportamento de agregação/apresentação sem reescrever as fórmulas de valuation. **v1.1 — "Gráfico de preço na aba Analisar"** (Phase 3): marco aditivo pequeno que mostra a evolução do preço (5 anos) com a linha do valor intrínseco do DDM sobreposta, reaproveitando a série diária que `ingest/prices.py` já baixa e hoje descarta — sem nova chamada de rede e sem tocar em nenhum cálculo de valuation. Os testes golden existentes em `tests/` devem continuar passando do início ao fim.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

**v1.0 — Consistência entre menus**

- [x] **Phase 1: Engine de Consistência** - Unificar a agregação/cálculo da engine (payout, BSD, fatores ausentes, ROE, DY, regressão) para que os modos parem de divergir na origem (completed 2026-06-05)
- [x] **Phase 2: Apresentação e Travas de Consistência** - Expor à UI o que a engine agora cumpre (ano-base, "indisponível", payouts rotulados, fatores faltantes) e travar a coerência entre modos com testes (completed 2026-06-05)

**v1.1 — Gráfico de preço na aba Analisar**

- [x] **Phase 3: Gráfico de Preço na aba Analisar** - Preservar a série diária de 5 anos que a engine já baixa e renderizá-la com Plotly na aba "Analisar", sobrepondo a linha do valor intrínseco do DDM, com degradação graciosa quando o Yahoo falha (completed 2026-06-23)

## Phase Details

### Phase 1: Engine de Consistência
**Goal**: A engine produz, na origem, números coerentes entre os três modos — mesma janela de payout, BSD reproduzível e absoluto, fatores ausentes neutros, ROE/DY com base correta e regressão robusta a dados anômalos.
**Depends on**: Nothing (first phase)
**Requirements**: GARIMPO-01, GARIMPO-02, GARIMPO-03, GARIMPO-04, PAYOUT-01, RANK-02, ROE-01, DY-01, VAL-01
**Success Criteria** (what must be TRUE):
  1. A mesma ação tem o mesmo BSD independentemente de quais outros tickers foram colados no lote (referência fixa, não relativa ao lote), e "BSD > 80" volta a ser um corte absoluto válido.
  2. Para a mesma ação, o payout que decide o preço-alvo no Ranking é o mesmo (mesma janela e clamp, função única) que decide o valor intrínseco no Analisar.
  3. No Garimpo, uma ação com DY abaixo da Selic não aparece como recomendada no topo — o ranking respeita de fato o corte por Selic prometido (ordena/filtra por "Passa filtros").
  4. Fatores do BSD com dado ausente entram como neutro/ausente (não como 0/pior valor), e o DY corrente usa dividendos dos últimos 12 meses; o ROE usa a mesma base de PL em todos os anos da série.
  5. O Ranking aplica o mesmo clamp/alerta de payout fora de [0,1] que o Analisar antes da regressão, e o intervalo de valor intrínseco vem de um único cálculo (sem recomputar min/max em dois lugares).
**Plans**: 5 plans
Plans:
- [x] 01-01-PLAN.md — Engine canônica: payout-para-valuation, ROE base consistente, DY trailing-12m (fundamentals/prices/build)
- [x] 01-02-PLAN.md — Clamp/sinalização de payout fora de [0,1] na regressão de preço-alvo (comparables)
- [x] 01-03-PLAN.md — BSD absoluto e reprodutível, fatores ausentes neutros, proxy de crescimento com janela padrão (screening/glossário)
- [x] 01-04-PLAN.md — Analisar usa payout canônico no DDM e expõe vmin/vmax do intervalo intrínseco (report)
- [x] 01-05-PLAN.md — Wire dos 3 modos: Garimpo ordena por filtros, Ranking usa payout canônico, Analisar reusa vmin/vmax (app.py)

### Phase 2: Apresentação e Travas de Consistência
**Goal**: A UI mostra de forma honesta o que a engine agora cumpre — ano-base efetivo, dado "indisponível", payouts duplos rotulados e fatores faltantes — e a coerência entre os três modos fica travada por testes automatizados, com os golden existentes ainda passando.
**Depends on**: Phase 1
**Requirements**: ANO-01, PAYOUT-02, RANK-01, TEST-01, TEST-02
**Success Criteria** (what must be TRUE):
  1. Ranking e Garimpo exibem o ano-base efetivo (`ultimo_ano`) de cada empresa, deixando visível quando há mistura de anos na comparação.
  2. O Ranking exibe "indisponível" (não "—" ambíguo lido como "cara") quando uma empresa é descartada da regressão por ROE/payout faltante.
  3. Quando o payout exibido (último ano) difere do payout usado pelo DDM (média 3a projetada), o app mostra ambos rotulados, sem ambiguidade.
  4. Um teste automatizado garante que a mesma empresa (mesmo dado de entrada) produz payout/ROE/veredito coerentes entre os 3 modos.
  5. `pytest` passa: os testes golden existentes da engine continuam verdes após todas as correções.
**Plans**: 2 plans
Plans:
- [x] 02-01-PLAN.md — UI: coluna Ano-base (Garimpo+Ranking), dual-payout no Analisar, "indisponível" no Ranking + 3 tooltips (app.py/glossario)
- [x] 02-02-PLAN.md — Travas de consistência cross-modo (TEST-01) e golden verde (TEST-02) (tests)
**UI hint**: yes

### Phase 3: Gráfico de Preço na aba Analisar
**Goal**: Ao analisar uma ação, o usuário vê na aba "Analisar" um gráfico interativo da evolução do preço dos últimos 5 anos com a linha do valor intrínseco do DDM sobreposta, deixando a margem de segurança visível — reaproveitando a série que a engine já baixa (sem nova chamada de rede) e sem alterar nenhum cálculo de valuation.
**Depends on**: Phase 2 (UX da aba Analisar já consolidada; herda os campos vmin/vmax expostos pela engine na Phase 1)
**Requirements**: GRAF-01, GRAF-02, GRAF-03
**Success Criteria** (what must be TRUE):
  1. Na aba "Analisar", o usuário vê uma linha do preço de fechamento dos últimos 5 anos, com zoom e hover interativos (Plotly).
  2. Uma linha/referência horizontal marca o valor intrínseco do DDM já calculado pela engine sobre a série de preço, tornando a margem de segurança visível (preço abaixo = desconto; acima = prêmio).
  3. Quando a série histórica de preços está indisponível (falha do Yahoo), a aba mostra um aviso claro em vez de quebrar, coerente com o aviso de "preço atual indisponível" já existente.
  4. `pytest` continua verde — nenhum golden test (test_ddm, test_multiples, test_comparables, test_screening) quebra, pois nenhuma fórmula de valuation foi alterada.
**Plans**: 2 plans
Plans:
- [x] 03-01-PLAN.md — Preservar a série 5a e thread DadosMercado→CompanyData; plotly no requirements; golden verde (prices/build/fundamentals/requirements)
- [x] 03-02-PLAN.md — Render Plotly da série + banda DDM na aba Analisar, com fallbacks de série/DDM indisponíveis (app.py)
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Engine de Consistência | 5/5 | Complete | 2026-06-05 |
| 2. Apresentação e Travas de Consistência | 2/2 | Complete | 2026-06-05 |
| 3. Gráfico de Preço na aba Analisar | 2/2 | Complete   | 2026-06-23 |
