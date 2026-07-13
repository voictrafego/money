# Phase 4: RIM com Valor Terminal + Ke Revisado — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-13
**Phase:** 04-rim-com-valor-terminal-ke-revisado (iteração 2 / reabertura via loop D-12)
**Areas discussed:** ROE forward vs atual, BBSE3 arquétipo seguradora, Alvo de aceite, Calibração global vs por arquétipo

---

## ROE forward vs. atual (BBAS3 + BBDC4)

| Option | Description | Selected |
|--------|-------------|----------|
| Normalizar ROE no valor terminal | ROE through-cycle só na perpetuidade; ROE atual na janela explícita; cirúrgico, não regride ITUB4 | ✓ |
| Aceitar como exceções cíclicas | Mantém ROE atual, anota BBAS3/BBDC4; simples mas não passam (2/4) | |
| Normalizar ROE na janela inteira | Agressivo; muda o intrínseco inteiro incl. ITUB4 — risco | |

**User's choice:** Normalizar ROE no valor terminal (recomendada)
**Notes:** BBAS3 e BBDC4 são o mesmo problema (ROE atual vs forward) em direções opostas → conserto único.

---

## BBSE3 — arquétipo seguradora

| Option | Description | Selected |
|--------|-------------|----------|
| Rota/tratamento próprio p/ seguradora | Fora do bank-RIM ancorado em book; cap próprio ou rota p/ DDM/franquia | ✓ |
| Manter no bank-RIM como exceção documentada | Aceita subvalorização, anota; número no app fica errado | |
| Excluir seguradoras do cesto de bancos | Tira BBSE3 do backtest; fecha loop sem resolver valuation | |

**User's choice:** Rota/tratamento próprio p/ seguradora (recomendada)
**Notes:** Minimalista — cap próprio ou rota p/ motor existente, não motor novo do zero.

---

## Alvo de aceite (fecha o loop D-12)

| Option | Description | Selected |
|--------|-------------|----------|
| 3/4 na banda + 1 exceção documentada | Conserta BBAS3+BBDC4 → 3/4 com ITUB4; BBSE3 exceção (regra D-08); honesto, sem overfit | ✓ |
| 4/4 dentro da banda ±15% | Exige consertar os 3; risco de overfit dos knobs | |
| 2/4 + exceções (mínimo p/ destravar) | Fecha rápido mas calibração fraca; não honra "generaliza" | |

**User's choice:** 3/4 na banda + 1 exceção documentada (recomendada)
**Notes:** BBSE3 é o slot de exceção esperado; se o tratamento de seguradora a fizer passar, vira 4/4. Piso 3/4.

---

## Calibração global vs. por arquétipo

| Option | Description | Selected |
|--------|-------------|----------|
| Global p/ banco + rota p/ seguradora | 1 knob de banco + seguradora por roteamento; turnaround via normalização do ROE | ✓ |
| Knobs por arquétipo (banco/seguradora/turnaround) | Cap distinto por tipo; mais superfície de calibração, mais overfit | |
| Um knob global único, aceitar desvios | Não proliferar; um cap p/ tudo; não fecha 3/4 | |

**User's choice:** Global p/ banco + rota p/ seguradora (recomendada)
**Notes:** Motor simples — divergência de arquétipo resolvida por roteamento + normalização, não por caps por sub-tipo.

## Claude's Discretion

- Forma exata da normalização through-cycle no terminal (blend, mean-reversion, teto de excesso).
- Mecanismo concreto do roteamento de seguradora (cap próprio vs. rota p/ DDM).

## Deferred Ideas

- Motor dedicado de seguradora (embedded value / P/EV) — fase própria se o minimalista não bastar.
- Normalização through-cycle na janela explícita inteira — reconsiderar só se o terminal não bastar.

## Ordem de ataque (registrada como D-09 no CONTEXT)

Primeiro descartar o bug de dado da BBAS3 (`num_acoes` dobrado) antes de atribuir o +54% à tese de ROE.
