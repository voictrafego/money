---
phase: 06-redeploy-do-app-v2-3-na-vps
plan: 02
subsystem: ops/deploy
tags: [deploy, vps, docker-swarm, rollback, redeploy, v2.3]
requires:
  - "git tag v2.3 no remote voictrafego/money (06-01)"
provides:
  - "Imagem money:pre-v2.3 na VPS (rede de rollback em 1 comando, D-06)"
  - "money:latest reconstruída da tag v2.3 (código servido = v2.3)"
  - "service lazari_money convergido 1/1 rodando money:latest (v2.3)"
affects:
  - "06-03 (smoke pós-deploy: infra/gate/WS, CLI no container, visual)"
tech-stack:
  added: []
  patterns:
    - "Rollback safety: taguear a imagem de prod atual ANTES do rebuild (D-06)"
    - "Deploy canônico v2.0: docker build money:latest + service update --force (D-05)"
    - "Proibido --remove-orphans; money sem ports: (anti-spoof, único ingresso = gate)"
key-files:
  created:
    - ".planning/phases/06-redeploy-do-app-v2-3-na-vps/06-02-SUMMARY.md"
  modified: []
decisions:
  - "Claude dirigiu o deploy inline via SSH (D-01), autorizado pelo operador; auto-mode bloqueava SSH em prod por subagente"
  - "money:pre-v2.3 pinado ao Id 28cabd94 (imagem que a task rodava há 3 dias, pré-v2.2)"
  - "Checkout da tag v2.3 (a0fb0be) em /root/money — detached HEAD, deploy reproduzível"
metrics:
  duration: "~10min"
  completed: "2026-07-13"
  tasks: 2
  files: 1
---

# Phase 6 Plan 02: Rollback safety + redeploy v2.3 na VPS — Summary

Rede de rollback (`money:pre-v2.3`) estabelecida ANTES do rebuild, código v2.3 reconstruído e
servido: o service `lazari_money` converge **1/1** rodando `money:latest` = build da tag `v2.3`.

## What Was Built

- **Rollback safety (Task 1, D-06):** descoberta a imagem que `lazari_money` rodava em prod
  (`money:latest` = `sha256:28cabd94…`, há 3 dias, código pré-v2.2) e tagueada como
  `money:pre-v2.3` **antes** de qualquer rebuild. O Id de `money:pre-v2.3` bate exatamente com o
  da imagem do container em execução (`25dd2dce5469`), garantindo rollback em 1 comando.
- **Rebuild + redeploy (Task 2, D-04/D-05):** na VPS, em `/root/money`: `git fetch --tags`
  (trouxe as tags `v2.2`/`v2.3`), `git checkout v2.3` (detached HEAD em `a0fb0be`),
  `docker build -t money:latest .` (novo Id `sha256:138b5fa9…`; layers de deps em cache, `COPY . .`
  reconstruído), `docker service update --force --image money:latest lazari_money` no stack `lazari`.
  Service **converged** 1/1; container novo `8ef8487e9193` roda a imagem `138b5fa9`.

## Verification

| Critério | Resultado |
|----------|-----------|
| `docker image inspect money:pre-v2.3` | `sha256:28cabd94…` (== imagem que rodava antes; rollback pronto) |
| Checkout `/root/money` | `git describe --tags` → `v2.3`; HEAD `a0fb0be` |
| Novo `money:latest` Id | `sha256:138b5fa9…` (build da tag v2.3) |
| `money:pre-v2.3` após rebuild | ainda `sha256:28cabd94…` (rollback preservado) |
| `docker service ls lazari_money` | `1/1`, imagem `money:latest` |
| `docker service ps lazari_money` | task nova `Running` (24s), antiga `Shutdown` — sem Failed/Rejected |
| Container em execução | `8ef8487e9193`, img `sha256:138b5fa9…` (v2.3) |
| `--remove-orphans` usado | Não |
| bloco `ports:` no money | Não adicionado (invariante anti-spoof mantida) |

## Deviations from Plan

- **Execução inline em vez de subagente (metodologia, não escopo):** o classificador de auto-mode
  do harness bloqueia SSH root em prod tanto para o orquestrador quanto para subagentes
  gsd-executor. O operador autorizou explicitamente (AskUserQuestion → "Claude dirige via SSH",
  D-01), e o deploy foi conduzido inline pelo orquestrador, comando a comando com output visível —
  mais controle/visibilidade num deploy de prod. O conteúdo do plano foi seguido à risca.
- Plano tinha `autonomous: true` (D-01), coerente com a condução por Claude.

## Authentication Gates

Nenhum gate de auth interativa disparado (D-02 não acionado): SSH com `-i ~/.ssh/id_ed25519_vps`
em `BatchMode=yes` conectou sem passphrase/host-key prompt; o `git fetch` do `/root/money` acessou
o repo público `voictrafego/money` sem credenciais.

## Notes for Next Plan (06-03)

- Rollback disponível se o smoke divergir: `docker service update --image money:pre-v2.3 lazari_money`
  (ou `--rollback`).
- Smoke 3 camadas: (D-09) infra — `docker service ls` 1/1 + gate forwardAuth 2xx/X-User-Email + WS 101;
  (D-08) código servido — `docker exec $(docker ps -q -f name=lazari_money) python -m analista analyze ITUB4`
  deve mostrar arquétipo→RIM e intrínseco ~R$32-40 (âncora 32,88), não DDM ~R$12-19; (D-07) visual —
  operador loga com conta pessoal, Claude confere ITUB4 via Claude-in-Chrome.

## Self-Check: PASSED

- FOUND: `.planning/phases/06-redeploy-do-app-v2-3-na-vps/06-02-SUMMARY.md`
- FOUND: `money:pre-v2.3` na VPS (`sha256:28cabd94…`) — rollback pronto
- FOUND: `lazari_money` 1/1 rodando `money:latest` = `sha256:138b5fa9…` (build da tag v2.3)
