# Roadmap: Analista de Dividendos — Marco "Consistência entre menus"

## Overview

Marco de remediação que corrige as inconsistências mapeadas em `CONSISTENCY-REVIEW.md` (3 críticos + 7 warnings) para que a mesma ação produza números coerentes nos três modos do app (`Analisar`, `Garimpar BSD`, `Ranking por múltiplos`). A abordagem é **mudar o comportamento de agregação/apresentação**, não reescrever as fórmulas de valuation — que já estão corretas e têm implementação única. O trabalho divide-se em corrigir a engine (janela de payout, referência absoluta do BSD, fatores ausentes, ROE, DY, regressão robusta) e a camada de apresentação/UX dos modos, fechando com testes que travam a consistência entre os modos. Os testes golden existentes em `tests/` devem continuar passando do início ao fim.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Engine de Consistência** - Unificar a agregação/cálculo da engine (payout, BSD, fatores ausentes, ROE, DY, regressão) para que os modos parem de divergir na origem
- [ ] **Phase 2: Apresentação e Travas de Consistência** - Expor à UI o que a engine agora cumpre (ano-base, "indisponível", payouts rotulados, fatores faltantes) e travar a coerência entre modos com testes

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
- [ ] 01-04-PLAN.md — Analisar usa payout canônico no DDM e expõe vmin/vmax do intervalo intrínseco (report)
- [ ] 01-05-PLAN.md — Wire dos 3 modos: Garimpo ordena por filtros, Ranking usa payout canônico, Analisar reusa vmin/vmax (app.py)

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
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Engine de Consistência | 0/5 | Not started | - |
| 2. Apresentação e Travas de Consistência | 0/TBD | Not started | - |
