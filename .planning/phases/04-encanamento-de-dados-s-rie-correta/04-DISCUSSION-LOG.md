# Phase 4: Encanamento de dados + série correta - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-24
**Phase:** 4-Encanamento de dados + série correta
**Areas discussed:** Estratégia split-adjusted, Conteúdo do campo ohlc, Ticker de validação do split

---

## Entrega da Fase 4 (conteúdo do `ohlc` + onde mora o ajuste por split)

| Option | Description | Selected |
|--------|-------------|----------|
| Bruto + ajustada, no ingest | `ohlc` = frame OHLCV nominal completo (preserva o `hist`, incl. Stock Splits) + Fase 4 deriva e guarda a versão split-adjusted (função pura, da coluna Stock Splits em memória). Nominal p/ o eixo (CR-01) + split-adjusted p/ indicadores (DATA-02). | ✓ |
| Só bruto; ajuste na Fase 5 | `ohlc` = só o frame nominal; todo o ajuste por split fica no módulo puro da Phase 5 (golden tests TEST-05). Fase 4 100% encanamento. | |
| Frame enxuto | Guardar só High/Low/Close/Volume + coluna de splits, descartando Open/Adj Close. | |

**User's choice:** Bruto + ajustada, no ingest
**Notes:** Fato técnico verificado antes da escolha: o `hist` que `coletar_mercado` já baixa contém a coluna `Stock Splits` → reconstrução do ajuste é de graça, sem violar DATA-01 (sem nova chamada de rede). Ajuste é dividend-free (não usar Adj Close).

---

## Ticker de validação do split

| Option | Description | Selected |
|--------|-------------|----------|
| ITSA4 | 5 eventos de split/bonificação nos últimos 5a (recorrentes); ação de dividendos clássica do público do app. | ✓ |
| Deixe a pesquisa escolher | Sem preferência; pesquisador/planejador seleciona na hora de validar. | |

**User's choice:** ITSA4
**Notes:** Verificado em runtime que ITSA4 tem 5 eventos (2021-2025) e TAEE4 tem 0 — ITSA4 é o caso que de fato estressa o ajuste.

---

## Claude's Discretion

- Nomenclatura exata do(s) campo(s) da série ajustada e assinatura/local da função pura de ajuste — a critério do planner, mantendo nominal + split-adjusted ambos acessíveis e seguindo o padrão `serie_precos`.

## Deferred Ideas

Nenhuma — a discussão permaneceu dentro do escopo da fase.
