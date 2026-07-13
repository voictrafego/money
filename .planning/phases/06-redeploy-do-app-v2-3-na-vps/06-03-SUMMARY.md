---
phase: 06-redeploy-do-app-v2-3-na-vps
plan: 03
subsystem: ops/deploy
tags: [smoke, deploy, verificacao, gate, rim, v2.3]
requires:
  - "service lazari_money 1/1 rodando money:latest (v2.3) (06-02)"
provides:
  - "OPS-01 verificado ao vivo: v2.3 em prod, ITUB4 arquétipo→RIM ~R$32-40, 'ver motor primário'"
  - "Smoke 3 camadas aprovado (infra D-09, código servido D-08, visual D-07)"
affects:
  - "Fecha a Fase 6; feedback de produto (card INTRÍNSECO + clutter + valor terminal) roteado p/ investigação de valuation"
tech-stack:
  added: []
  patterns:
    - "Smoke em profundidade: infra + código servido (docker exec CLI) + visual (browser logado)"
key-files:
  created:
    - ".planning/phases/06-redeploy-do-app-v2-3-na-vps/06-03-SUMMARY.md"
  modified: []
decisions:
  - "Smoke visual (D-07) conduzido via Claude-in-Chrome na sessão logada do operador; sessão do perfil herdada pela nova aba"
  - "Deploy verificado inline pelo orquestrador com evidência primária (SSH + screenshots), não por subagente (auto-mode bloqueia SSH prod)"
metrics:
  duration: "~15min"
  completed: "2026-07-13"
  tasks: 3
  files: 1
---

# Phase 6 Plan 03: Smoke pós-deploy (3 camadas) — Summary

Redeploy v2.3 verificado ao vivo em produção nas 3 camadas. OPS-01 atendido: ITUB4 no app logado
mostra arquétipo→RIM, intrínseco R$ 32,88 e veredito "ver motor primário" — não mais "Evitar" DDM.

## What Was Built (verificação)

- **Camada 1 — infra (D-09):** `docker service ps lazari_money` → task nova `Running` (sem Failed/Rejected);
  container money com Streamlit up; `lazari_web` (gate) 1/1; requisição anônima a
  `https://app.lazaricapital.com.br` → **302** → `www.lazaricapital.com.br/entrar/` (forwardAuth
  interceptando). Sessão válida → app renderiza atrás do gate (2xx + X-User-Email promovido), WS do
  Streamlit ativo (app interativo com cotações ao vivo).
- **Camada 2 — código servido (D-08):** `docker exec $(docker ps -q -f name=lazari_money) python -m
  analista analyze ITUB4` → arquétipo `financeira` → motor **RIM R$ 32,88**; veredito "DDM conservador
  demais — ver motor primário do arquétipo (≈ R$ 32,88)". Prova independente do render/gate.
- **Camada 3 — visual (D-07):** app logado (sessão real do operador), análise de ITUB4 conduzida via
  Claude-in-Chrome. Na tela: `Arquétipo: financeira → motor rim`; veredito verde "ver motor primário
  (≈ R$ 32,88)"; sintoma antigo "Evitar" DDM R$12,93–19,32 ausente.

## Verification

| Camada | Critério | Resultado |
|--------|----------|-----------|
| D-09 | service replicas | `lazari_money` 1/1, task Running |
| D-09 | gate anônimo | 302 → login em www |
| D-09 | sessão válida | app renderiza (2xx + X-User-Email), WS ativo |
| D-08 | CLI no container | RIM R$ 32,88, "ver motor primário" |
| D-07 | app ao vivo | arquétipo→RIM, R$ 32,88, "ver motor primário", sem "Evitar" |

## Deviations from Plan

- Verificação conduzida inline pelo orquestrador (evidência primária: SSH + screenshots), não por
  subagente — o classificador de auto-mode bloqueia SSH root em prod para subagentes. Operador
  autorizou (D-01).

## Follow-up de PRODUTO levantado no smoke (NOVO escopo — não é falha do deploy)

O operador validou que o comportamento v2.3 chegou a prod (OPS-01 ok), mas o smoke visual expôs
problemas de apresentação/valuation que são escopo NOVO (milestone "Calibração do Valuation"):

1. **Card INTRÍNSECO enganoso:** o card headline `INTRÍNSECO (RIM — VPA +…)` mostra a faixa
   `R$ 16,13 – R$ 32,88` (piso do DDM como manchete), fazendo o usuário ler "intrínseco = R$ 16,13".
   Fere o core value (consistência entre views). Deveria liderar com o RIM primário R$ 32,88.
2. **Poluição de banners:** a mensagem "é RIM, o DDM é conservador" repete-se em 4–5 banners
   empilhados (veredito + SAN-01 ×2 + VER-01 + divergência + Payout>100%) antes de qualquer número.
3. **Dúvida de calibração (a investigar):** mesmo o RIM primário (R$ 32,88) fica ABAIXO do preço
   (R$ 43,86). Hipótese registrada na memória `rim-terminal-value-root-cause`: a alavanca sub-calibrada
   é o VALOR TERMINAL do RIM, não o Ke. Operador optou por **investigar o valuation primeiro** antes
   de qualquer ajuste de UI.

## Self-Check: PASSED

- FOUND: `.planning/phases/06-redeploy-do-app-v2-3-na-vps/06-03-SUMMARY.md`
- VERIFIED (ao vivo): ITUB4 em prod → arquétipo RIM, R$ 32,88, "ver motor primário"
- OPS-01 atendido; follow-up de produto roteado para investigação de valuation (fora desta fase)
