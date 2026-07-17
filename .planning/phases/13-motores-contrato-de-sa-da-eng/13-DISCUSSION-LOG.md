# Phase 13: Motores + contrato de saída (ENG) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-17
**Phase:** 13-motores-contrato-de-sa-da-eng
**Areas discussed:** Âncora de ROE por arquétipo, CONCESSAO_FINITA + default, Contrato de saída + UI, Guard P/B + Ranking

---

## Âncora de ROE por arquétipo (ENG-01/ENG-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Arquétipo→política de ROE-âncora | `ARQUETIPO_MOTOR`→`ARQUETIPO_ANCORA_ROE`; cada arquétipo mapeia para uma política de derivação do ROE-âncora/base do RIM único; os 3 ex-motores viram derivadores de insumo; fórmula RIM idêntica. Erro limitado (ENG-03). | ✓ |
| Âncora única through-cycle p/ todos | Um RIM com ROE-âncora sempre = mediana through-cycle; arquétipo só ajusta fade/n. Mais simples, menos fiel. | |
| Você decide | Deixar a granularidade para researcher/planner. | |

**User's choice:** Arquétipo→política de ROE-âncora
**Notes:** É a leitura literal do ENG-03 (escolher âncora, não modelo).

---

## CONCESSAO_FINITA + novo default (ENG-04)

| Option | Description | Selected |
|--------|-------------|----------|
| eh_concessionaria→CONCESSAO_FINITA; default→MADURA | Hard-route `eh_concessionaria` vira CONCESSAO_FINITA (carve-out: book=VP da RAP, não conserta g); default-por-eliminação (:180) vira PAGADORA_MADURA. Empresa sem sinal deixa de cair no carve-out. | ✓ |
| Sinal explícito para AMBAS + sem default no carve-out | Exigir sinal dedicado p/ ambas; nenhuma por eliminação. Rigoroso, mas exige nova fonte de sinal e pode deixar tickers sem rota. | |
| Você decide | Deixar mecânica exata para o researcher. | |

**User's choice:** eh_concessionaria→CONCESSAO_FINITA; default→MADURA
**Notes:** Resolve a raiz do bug do ENG-04 (default-por-eliminação caía na transmissora).

---

## Contrato de saída — escopo engine × UI (ENG-05/06/07/08)

| Option | Description | Selected |
|--------|-------------|----------|
| Engine completa + UI mínima de exibição | Engine entrega tríade V-vs-região, MS parâmetro (default config, simétrica 5-10%, nunca calibrada), ponte P/B + assert payout_T, matriz Ke×g; tela recebe mínimo (widget MS, tríade, matriz; remove Evitar/Qualidade Baixa). | ✓ |
| Engine-only; toda a UI deferida | Só o contrato na engine; tela Streamlit para fase de UI dedicada. | |
| Você decide | Deixar o corte engine×UI para o planner. | |

**User's choice:** Engine completa + UI mínima de exibição
**Notes:** UI hint do roadmap = yes; a mudança visual é mínima, o peso é na engine.

---

## Guarda-corpo P/B justo + Ranking (ENG-08/ENG-09/ENG-11)

### Guard P/B (ENG-08/09)

| Option | Description | Selected |
|--------|-------------|----------|
| Dois níveis: teste de correção + runtime never-raise | TESTE: identidade P/B justo e payout_T viram assert (negativo/>100% ou P/B fora de (0,6) FALHA). RUNTIME: fora da faixa degrada never-raise (VERIFICAR), não levanta. CGRA4 921× sinalizado. | ✓ |
| Só assert em teste (sem degradação runtime) | Guard só como teste; runtime cru. Deixa CGRA4 921× na tela sem sinalização. | |
| Você decide | Deixar teste×runtime para o researcher. | |

**User's choice:** Dois níveis: teste de correção + runtime never-raise

### Ranking (ENG-11)

| Option | Description | Selected |
|--------|-------------|----------|
| Sai nível de preço; ficam múltiplos crus | Colunas preço-alvo/upside/veredito saem (imputam nível de preço); screener mostra múltiplos crus (P/L, P/VP, DY, BSD); ensemble×DDM+divergência removidos (ENG-02); comparativo por múltiplos permanece. | ✓ |
| Manter regressão de pares visível, só renomear rótulos | Preservar a coluna renomeando; risco de continuar exibindo nível de preço imputado (cego ao nível). | |
| Você decide | Deixar o conjunto de colunas para researcher/planner. | |

**User's choice:** Sai nível de preço; ficam múltiplos crus

---

## Claude's Discretion

O usuário escolheu a opção recomendada em **todas** as 5 perguntas (nenhum "Você decide" acionado).
Ficam ao researcher/planner: o mapa exato arquétipo→política de âncora; a mecânica do carve-out
CONCESSAO_FINITA; as ≤5 chaves finais de `motores:` e o destino de `ciclica.anos_media`/
`crescimento.n_anos_explicito`; o formato exato da ponte P/B e rótulos; a divisão em waves e ordem dos
commits atômicos; o conjunto exato de colunas do screener.

## Deferred Ideas

- Validação honesta / hold-out / caso do livro (ITUB4 = R$ 37,22) — Fase 14 (VAL).
- Motor `nav`/SOTP real para holdings — Future Requirement.
- Score BSD por arquétipo — Future Requirement.
- Reforma visual pesada da tela Streamlit — depois, se necessário.
- Deflator no `dpa_recorrente` e séries longas de dividendo — Future Requirement.
