# Phase 3: Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-12
**Phase:** 3-Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo
**Areas discussed:** Motor→faixa (VER-01), Contraponto ensemble (ENS-01), Guarda-corpo SAN-01, Fronteiriço (VER-02)

---

## Motor → faixa de veredito (VER-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Margem de segurança fixa | Banda = intrínseco ± X% (config); uniforme p/ todos os motores | |
| Range do ensemble | vmin/vmax = min/max motor primário × contraponto; unifica VER-01+ENS-01 | (recomendado) |
| Sensibilidade por motor | Cada motor gera matriz Ke±/g± própria; mais fiel, muito mais código | |
| Você decide | Delega ao planner | ✓ |

**User's choice:** Você decide
**Notes:** Recomendação registrada no CONTEXT (D-01): range do ensemble como default, margem fixa como fallback quando o contraponto degrada. Planner pode preferir margem fixa se o range ficar largo demais.

---

## Contraponto do ensemble (ENS-01)

| Option | Description | Selected |
|--------|-------------|----------|
| DDM lente conservadora | Só o DDM (já roda sempre); par do ITUB4; reusa comparables.divergencia_entre_lentes | (recomendado) |
| DDM + Graham/Bazin | Painel de ≥2 contrapontos por arquétipo; mais robusto, risco de inflar bandeiras | |
| Você decide | Delega ao planner | ✓ |

**User's choice:** Você decide
**Notes:** Recomendação D-02: DDM-only como contraponto universal, reusando o helper puro já existente; Graham/Bazin como refino opcional.

## Hipótese da bandeira (ENS-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Template por arquétipo | Frase curada por (arquétipo, direção); estável, testável por golden | (recomendado) |
| Divergência genérica | "Modelos divergem ~Nx" sem hipótese causal; perde o "porquê" do brief | |
| Você decide | Delega ao planner | ✓ |

**User's choice:** Você decide
**Notes:** Recomendação D-03: template arquétipo×direção (brief pede o "porquê" exibido), genérico como fallback.

---

## Guarda-corpo SAN-01 — fonte da mediana de pares

| Option | Description | Selected |
|--------|-------------|----------|
| Proxy da regressão P/L | preco_alvo_por_regressao como "valor dos pares"; custo-zero, sem puxar rede | (recomendado) |
| Condição degrada | Sem pares → cai para as 2 restantes (ROE>15% E corte payout>40%) | (fallback) |
| Você decide | Delega ao planner | ✓ |

**User's choice:** Você decide
**Notes:** Recomendação D-04: proxy da regressão como valor-de-pares, degradando para as 2 condições restantes quando a regressão não roda (freios R²/amostra de 01-08).

## Guarda-corpo SAN-01 — ação (reetiqueta vs suprime)

| Option | Description | Selected |
|--------|-------------|----------|
| Reetiqueta honesta | "DDM conservador demais para o perfil — ver motor primário"; texto literal do brief | (recomendado) |
| Suprime estilo VERIFICAR | Reusa prefixo VERIFICAR; menos superfície nova | |
| Você decide | Delega ao planner | ✓ |

**User's choice:** Você decide
**Notes:** Recomendação D-05: reetiqueta honesta (texto literal SAN-01) na borda do veredito. Nota: com VER-01, SAN-01 vira backstop — a maioria dos não-DDM já não cai em "evitar".

---

## Fronteiriço: assumir a dúvida (VER-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Range dos candidatos + bandeira | Roda motor de cada candidato; exibe range + bandeira "incerto entre X e Y" | (recomendado) |
| Supressão + candidatos listados | Selo suprimido; candidatos lado a lado sem range único | (degradação) |
| Você decide | Delega ao planner | ✓ |

**User's choice:** Você decide
**Notes:** Recomendação D-06: range dos candidatos + bandeira (literal "range + bandeira" do VER-02), degradando para listar candidatos quando um motor falha.

---

## Claude's Discretion

O usuário delegou **as 4 áreas** ("você decide" em todas). As recomendações D-01..D-06 no CONTEXT.md são a direção-default; o planner pode ajustar dentro do racional documentado, preservando os invariantes travados (selo consome o motor do arquétipo; limiar 2×; regra literal SAN-01; firewall selo↛report; goldens verdes).

## Deferred Ideas

- Graham/Bazin como 2º contraponto do ensemble (refino do D-02).
- Sensibilidade própria por motor (banda RIM/normalizado/DCF) — não escolhido no D-01.
- Puxar o setor inteiro para mediana de pares real — recusado no D-04 (custo de rede).
- Backtesting / validação empírica por arquétipo — BACKTEST-01, fora do milestone.
- Acertar 100% dos tickers — ARQ-AUTO-01, fora de escopo.
</content>
