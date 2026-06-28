# Phase 10: Crescimento robusto + de-poison do screening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-27
**Phase:** 10-crescimento-robusto-de-poison-do-screening
**Areas discussed:** Estimador robusto do g, Base do crescimento no screening, Clamp do payout na regressão, Fallback p/ anos não-positivos

---

## Estimador robusto do g

| Option | Description | Selected |
|--------|-------------|----------|
| Regressão log-linear | OLS de ln(lucro) vs tempo; g = exp(slope)−1; usa todos os pontos; padrão de mercado; numpy.polyfit | ✓ |
| Theil-Sen | Mediana dos slopes par-a-par; ultra-robusto mas marginal com série curta já winsorizada | |
| Média aparada das variações YoY | Média das variações ano-a-ano sem extremos; sensível a base baixa | |

**User's choice:** Regressão log-linear
**Notes:** Sobre a série de lucro já normalizada/winsorizada (`serie_lucro_normalizada()`). Substitui o CAGR endpoint-a-endpoint em report.py:79.

---

## Base do crescimento no screening

| Option | Description | Selected |
|--------|-------------|----------|
| Mesmo log-linear + série normalizada | Screening reusa o MESMO estimador robusto sobre séries normalizadas; consistência total Analisar↔Screening | ✓ |
| Só trocar crua→normalizada, manter CAGR | Mudança mínima; segue sensível a endpoint e diverge do g exibido | |

| Option (séries) | Description | Selected |
|--------|-------------|----------|
| Lucro + dividendos + FCO | Normaliza os 3 fatores de crescimento do BSD | ✓ |
| Só lucro e dividendos | FCO 3a segue cru | |

**User's choice:** Mesmo log-linear + série normalizada; normalizar lucro + dividendos + FCO
**Notes:** Substitui cagr_serie (screening.py:264) nos 3 fatores; usa normalizacao.serie_winsorizada.

---

## Clamp do payout na regressão

| Option | Description | Selected |
|--------|-------------|----------|
| Clamp [0,1] só na entrada da regressão | min(payout,1.0) só em preco_alvo_por_regressao; payout_valuation segue sem clamp (D-03) | ✓ |
| Recalibrar a regressão p/ payout >1 | Mais correto mas mais risco/escopo | |
| Excluir tickers com payout >100% | Remove nomes legítimos (transmissoras) do preço-alvo | |

**User's choice:** Clamp [0,1] só na entrada da regressão
**Notes:** Exatamente o handoff de 09-CROSS-EFFECT-FASE10.md. Chamadas em cli.py:158-159 e app.py:472.

---

## Fallback p/ anos não-positivos

| Option | Description | Selected |
|--------|-------------|----------|
| None — sem g exibido | Ano ≤0 ⇒ g_historico = None; preserva fronteira de None do CAGR atual | ✓ |
| Média aritmética robusta das variações | Dá número com prejuízo mas errático; muda fronteira de None | |
| Regressão linear simples (nível, não-log) | Funciona com negativos mas taxa ambígua | |

**User's choice:** None — sem g exibido
**Notes:** Crescimento composto não é definível sobre prejuízo; piso g_alto=max(0,…) trata o resto.

---

## Claude's Discretion

- Localização/assinatura exata do estimador log-linear (função pura em growth.py).
- Existência de knob de config para o estimador (default sem knob é aceitável).
- Rebaseline deliberado dos golden tests afetados, com validação multi-ticker.

## Deferred Ideas

- Formatação `%` do DY rec. (bug app.py:324) e hierarquia de apresentação — Fase 11.
- DY recorrente híbrido p/ não subestimar quem distribui de reservas — insumo de metodologia.
- Payout-alvo por setor; sinalização de "ano extraordinário" na tabela — Future (v2+).
