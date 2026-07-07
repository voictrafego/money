# Phase 15: Montagem do Setup (SetupSwing) + Score - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-29
**Phase:** 15-montagem-do-setup-setupswing-score
**Areas discussed:** Pesos do score, R:R (gate ou modulador), Grade qualitativa, Conflito multi-TF + copy

---

## Pesos do score

| Option | Description | Selected |
|--------|-------------|----------|
| Tendência forte (35%) | Tendência 35 / R:R 20 / Padrões 20 / Momentum 15 / Volume 10 | ✓ |
| Tendência moderada (25%) | Tendência 25 / R:R 20 / Padrões 20 / Momentum 20 / Volume 15 | |
| Você decide | Ancora no research, tendência sempre dominando | |

**User's choice:** Tendência forte (35%)
**Notes:** Coerente com Murphy (operar a favor da tendência). Pesos no config.yaml, calibráveis.

---

## R:R — gate ou modulador

| Option | Description | Selected |
|--------|-------------|----------|
| Gate duro (zera) | R:R < mínimo (≈1.5) zera o setup → "Sem setup" | ✓ |
| Modulador pesado | Penaliza forte mas não zera | |
| Híbrido | Modulador na faixa normal, gate abaixo de piso crítico | |

**User's choice:** Gate duro (zera)
**Notes:** Mais conservador, coerente com "exibe sinais, nunca recomenda". R:R mínimo exato calibrável no config.

---

## Grade qualitativa

| Option | Description | Selected |
|--------|-------------|----------|
| 4 faixas PT | Forte / Moderado / Fraco / Sem setup | ✓ |
| Letras A/B/C/D | Grade por letra estilo rating | |
| 3 faixas | Alto / Médio / Baixo | |

**User's choice:** 4 faixas PT (Forte / Moderado / Fraco / Sem setup)
**Notes:** Legível pro investidor PF, tom de estudo. "Sem setup" também é o resultado do gate de R:R. Cortes calibráveis.

---

## Conflito multi-TF + copy

| Option | Description | Selected |
|--------|-------------|----------|
| Confluência técnica | "Pontuação de confluência técnica" — factual, neutro | ✓ |
| Força do setup (estudo) | "Força técnica do setup (estudo)" com selo | |
| Você decide | Ancora no research/copy-review | |

**User's choice:** Confluência técnica
**Notes:** Conflito multi-TF penaliza sem bloquear (Critério 2). Disclaimer "exibe sinais, nunca recomenda". Copy review é gate de aceite.

---

## Claude's Discretion

- Normalização do score (0–100 vs 0–1) e cortes numéricos das 4 faixas → research, no config.yaml.
- Valor exato do R:R mínimo (~1.5) e piso crítico; magnitude da penalização multi-TF → research ancora valores iniciais.
- Estrutura interna do dataclass `SetupSwing` → planner/research, respeitando read-only e degradação graciosa.
- Gate de liquidez (volume mínimo) como pré-condição → research avalia se cabe no MVP.

## Deferred Ideas

- Renderização/gráfico/página com overlays (médias, Bollinger, padrões anotados, RSI/MACD/ADX) → Fase 16.
- Padrões de continuação (triângulos, bandeiras) como insumo do score → backlog.
- Ranqueamento entre múltiplos padrões além do peso → refinar na Fase 16.
