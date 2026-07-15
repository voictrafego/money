# Phase 10: Primitivas sem viés (PRIM) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-15
**Phase:** 10-primitivas-sem-vi-s-prim
**Areas discussed:** Estimador de normalização, roe_valuation, Deflação do motor cíclico, Winsorização

---

## Estimador de normalização do lucro (PRIM-01 / BLIND-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Endpoint de regressão robusta (Theil-Sen) | Ajusta tendência robusta e usa o valor no ano atual; reflete crescimento, mantém o recente, robusto a 1 outlier | ✓ |
| Lucro normalizado por margem | Margem líquida média × receita do último ano (estilo Graham/livro) | |
| Último ano cru (sem normalização) | Trivial, não pune crescimento, mas perde robustez a exercício atípico | |

**User's choice:** Endpoint de regressão robusta (Theil-Sen)
**Notes:** É o núcleo da fase e onde a memória avisa que "correções óbvias pioram o modelo" — o researcher valida contra os 104 tickers; precisa de fallback para série curta.

---

## roe_valuation (PRIM-02)

| Option | Description | Selected |
|--------|-------------|----------|
| roe(ano) por ano + mediana da série completa | Cada ROE = lucro_t ÷ PL médio(t-1,t), mediana da série toda (como mediana_payout) | ✓ |
| lucro_t ÷ PL de fim de ano + mediana completa | Mais simples, mas diverge do roe(ano) existente | |
| Janela de 3 anos | Mais curta, mais sensível ao recente | |

**User's choice:** roe(ano) por ano + mediana da série completa
**Notes:** Consistência com o roe já exibido por ano e com a filosofia de série-completa do payout. Alvo ITUB4 16,1%→18,0%.

---

## Deflação do motor cíclico (PRIM-04)

| Option | Description | Selected |
|--------|-------------|----------|
| IPCA (BCB SGS) → reais do último ano, só o motor cíclico | Traz a série a reais de hoje via macro.py; deixa CAGR/g p/ Fase 11 | ✓ |
| IPCA → ano-base fixo (ex.: 2015) | Reais constantes de base fixo; números menos intuitivos | |
| Deflacionar também a base do CAGR/g agora | Mais abrangente, mas entra no território do g (Fase 11) | |

**User's choice:** IPCA (BCB SGS) → reais do último ano, só o motor cíclico
**Notes:** Respeita a fronteira com a Fase 11 e reusa a infra do BCB. Alvo: CSNA3 deixa de sair 31,8% subvalorizada.

---

## Winsorização (PRIM-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Remover e deixar a série crua até a Fase 11 | Fase 10 tira o viés (g 36%/47% somem); Fase 11 desenha o g robusto | ✓ |
| Substituir já por slope de regressão em log | Robustez sem clampar tendência, mas é desenhar o g (Fase 11) | |
| Você decide | Seguir a recomendação e registrar como decisão do builder | |

**User's choice:** Remover e deixar a série crua até a Fase 11
**Notes:** Fronteira limpa entre as fases; escolha explícita mesmo com "Você decide" disponível.

---

## Claude's Discretion

- Detalhes de implementação dentro das decisões travadas: biblioteca do Theil-Sen (provável `scipy.stats.theilslopes`, respeitando custo zero), forma exata do fallback de série curta — a critério de researcher/planner.

## Deferred Ideas

- Deflação da base do CAGR/`g` → Fase 11.
- Desenho do `g` robusto (slope de regressão em log) → Fase 11.
- Conserto do `Ke`/`ke_teto` → Fase 12 (regra dura A).
