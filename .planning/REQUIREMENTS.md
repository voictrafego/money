# Requirements: Analista de Dividendos — Marco "Consistência entre menus"

**Defined:** 2026-06-04
**Core Value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.
**Fonte do escopo:** `CONSISTENCY-REVIEW.md` (16 achados: 3 críticos, 7 warnings, 6 infos).

## v1 Requirements

Cada requisito mapeia a um achado do review. Abordagem decidida: **mudar o comportamento**.

### Garimpo / BSD

- [x] **GARIMPO-01**: No Garimpo, o ranking exibido respeita o corte por Selic prometido — uma ação com DY abaixo da Selic não aparece como recomendada no topo (ordenar/filtrar por "Passa filtros", não só por BSD). *(CR-01)*
- [x] **GARIMPO-02**: O BSD é padronizado contra uma referência fixa (não relativo ao lote): a mesma ação tem o mesmo BSD independentemente dos outros tickers colados, e "BSD > 80" volta a ser um corte absoluto válido. *(WR-06)*
- [x] **GARIMPO-03**: Fatores do BSD com dado ausente são tratados como neutro/ausente (não como pior valor 0), e o app indica quantos/quais fatores faltaram por empresa. *(WR-05)*
- [x] **GARIMPO-04**: O proxy de crescimento do BSD (ROE×(1−payout) na ausência de estimativa) usa a mesma janela dos demais fatores e é documentado no tooltip. *(WR-02)*

### Payout unificado

- [x] **PAYOUT-01**: Analisar e Ranking usam a mesma janela e clamp de payout (função única) — o payout que decide o preço-alvo no Ranking é o mesmo que decide o valor intrínseco no Analisar para a mesma ação. *(CR-02 / WR-03)*
- [x] **PAYOUT-02**: Quando o payout exibido (último ano) difere do payout usado pelo DDM (projetado, média 3a), o app mostra ambos rotulados, sem ambiguidade. *(WR-03)*

### Ranking robusto

- [x] **RANK-01**: O Ranking exibe "indisponível" (não "—" ambíguo lido como "cara") quando uma empresa é descartada da regressão por ROE/payout faltante. *(CR-03)*
- [x] **RANK-02**: O Ranking aplica o mesmo clamp/alerta de payout fora de [0,1] que o Analisar antes de alimentar a regressão. *(CR-03)*

### ROE consistente

- [x] **ROE-01**: O ROE usa a mesma base (PL inicial ou médio) em todos os anos da série; o 1º ano não cai silenciosamente para PL final, ou o glossário é alinhado à base real usada. *(WR-01)*

### DY corrente

- [x] **DY-01**: O DY do Garimpo usa dividendos dos últimos 12 meses (ou alinhado ao ano dos dividendos), não dividendos de ano antigo sobre o preço de hoje; o ano-base do DPA é sinalizado. *(WR-04)*

### Valuation sem duplicação

- [x] **VAL-01**: O intervalo de valor intrínseco exibido na métrica e o usado no veredito vêm de um único cálculo (sem recomputar min/max em dois lugares). *(WR-07)*

### Ano-base visível

- [x] **ANO-01**: Ranking e Garimpo exibem o ano-base efetivo de cada empresa (`ultimo_ano`), para o usuário enxergar quando há mistura de anos na comparação. *(CR-02, parte 2)*

### Testes de consistência

- [x] **TEST-01**: Teste automatizado garante que a mesma empresa (mesmo dado de entrada) produz payout/ROE/veredito coerentes entre os 3 modos.
- [x] **TEST-02**: Os testes golden existentes da engine continuam passando após as correções.

## v2 Requirements

### Documentação da engine

- **DDM-DOC-01**: Alinhar a docstring de `ddm.py` e o caso de teste de referência à mesma convenção de t (ano 0 vs ano 1) — fonte provável de confusão futura, sem divergência entre modos hoje. *(IN-06)*

---

# Milestone v1.1 — Gráfico de preço na aba "Analisar"

**Defined:** 2026-06-23
**Goal:** Mostrar a evolução do preço (5a) com a linha do valor intrínseco do DDM sobreposta,
evidenciando a margem de segurança — sem tocar em cálculo de valuation.

## v1.1 Requirements

### Gráfico de preço (Analisar)

- [x] **GRAF-01**: Ao analisar uma ação, o usuário vê um gráfico interativo (Plotly) da evolução do preço de fechamento nos últimos 5 anos, com zoom e hover.
- [x] **GRAF-02**: O gráfico sobrepõe ao preço a linha do valor intrínseco / preço-alvo do DDM já calculado pela engine, evidenciando visualmente a margem de segurança (preço abaixo = desconto; acima = prêmio).
- [x] **GRAF-03**: Quando a série histórica de preços está indisponível (falha do Yahoo), o gráfico degrada graciosamente com aviso claro, sem quebrar a aba — coerente com o aviso de "preço atual indisponível" já existente.

**Constraints (não são requisitos, mas governam a implementação):**
- A série histórica de 5a (hoje baixada e descartada em `ingest/prices.py`) deve ser preservada e
  entregue à UI pela cadeia `DadosMercado → build → report → app.py`, reusando o cache de 1h (sem
  nova chamada de rede só para o gráfico).
- `plotly` adicionado ao `requirements.txt`.
- Nenhuma fórmula de valuation é alterada; os golden tests de `tests/` continuam verdes.

## v1.1 Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GRAF-01 | Phase 3 | Complete |
| GRAF-02 | Phase 3 | Complete |
| GRAF-03 | Phase 3 | Complete |

**Coverage:**
- v1.1 requirements: 3 total
- Mapped to phases: 3 ✓
- Unmapped: 0

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Dados pagos / APIs premium | Projeto é custo zero por princípio |
| Reescrever as fórmulas de valuation | As fórmulas estão corretas (IN-01..05); o problema é consistência de apresentação/agregação |
| Quarto menu/ferramenta | O gráfico do v1.1 enriquece a aba "Analisar" existente, não cria um novo menu |
| Gráfico no CLI / relatório Markdown | Markdown não embute imagem sem salvar PNG; o valor está na UI interativa |
| Sobreposições extras (proventos, IBOV, faixa de DY) | Adiadas — escopo do v1.1 é núcleo (preço + valor intrínseco) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GARIMPO-01 | Phase 1 | Complete |
| GARIMPO-02 | Phase 1 | Complete |
| GARIMPO-03 | Phase 1 | Complete |
| GARIMPO-04 | Phase 1 | Complete |
| PAYOUT-01 | Phase 1 | Complete |
| RANK-02 | Phase 1 | Complete |
| ROE-01 | Phase 1 | Complete |
| DY-01 | Phase 1 | Complete |
| VAL-01 | Phase 1 | Complete |
| ANO-01 | Phase 2 | Complete |
| PAYOUT-02 | Phase 2 | Complete |
| RANK-01 | Phase 2 | Complete |
| TEST-01 | Phase 2 | Complete |
| TEST-02 | Phase 2 | Complete |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14 ✓
- Unmapped: 0

---
*Requirements defined: 2026-06-04*
*Last updated: 2026-06-23 — v1.1 traceability mapped (GRAF-01/02/03 → Phase 3)*
