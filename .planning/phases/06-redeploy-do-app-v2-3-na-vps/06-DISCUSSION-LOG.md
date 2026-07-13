# Phase 6: Redeploy do app v2.3 na VPS - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-13
**Phase:** 6-Redeploy do app v2.3 na VPS
**Areas discussed:** Execução do deploy, Código→VPS, Smoke pós-deploy, Rollback

---

## Execução do deploy

| Option | Description | Selected |
|--------|-------------|----------|
| Eu dirijo via SSH | Claude executa comandos direto na VPS via Bash/SSH, mostrando output. Rápido, sem gate humano por comando. | ✓ |
| Runbook + você aprova | Claude para em checkpoints nos passos irreversíveis para o operador aprovar/rodar (padrão v2.0). | |
| Você decide | Claude escolhe a abordagem mais segura. | |

**User's choice:** Eu dirijo via SSH.
**Notes:** Fallback acordado: se o SSH pedir auth interativa, Claude entrega o comando exato para o operador rodar via `! ssh`.

---

## Código→VPS

| Option | Description | Selected |
|--------|-------------|----------|
| push→github→git pull | push origin main (conta gh voictrafego) + git pull em /root/money. Github fonte de verdade; depende da auth voictrafego. | ✓ |
| rsync local→VPS | rsync direto p/ /root/money, pulando o github. Sem fricção de push, mas github desatualiza. | |
| rsync + push depois | rsync agora + push/tag depois. Dois passos. | |

**User's choice:** push→github→git pull.
**Notes (sub-decisão — Versionar):** escolhido **Criar tag v2.3** (vs. só HEAD da main / você decide) — VPS dá checkout da tag; deploy reproduzível amarrado a versão nomeada; imagem segue `money:latest`.

---

## Smoke pós-deploy

| Option | Description | Selected |
|--------|-------------|----------|
| Navegador logado | app.lazaricapital.com.br logado, analisar ITUB4 e conferir arquétipo→RIM visualmente. | ✓ |
| docker exec CLI | Rodar CLI dentro do container money p/ confirmar código v2.3, independente do gate/render. | ✓ |
| Healthcheck + WS | Confirmar service 1/1, gate forwardAuth 2xx e websocket 101 atrás do gate. | ✓ |

**User's choice:** As três (defesa em profundidade).
**Notes (sub-decisão — Login):** escolhido **Sua conta pessoal** (vs. criar usuário de teste trial / você decide) — operador loga com conta real ativa; Claude conduz a análise via Claude-in-Chrome; sem escrita de usuário em prod.

---

## Rollback

| Option | Description | Selected |
|--------|-------------|----------|
| Taguear imagem anterior | docker tag da imagem atual → money:pre-v2.3 antes do rebuild; rollback em 1 comando. | ✓ |
| Só para frente | Sem backup; corrigir/rebuild se quebrar. App fora do ar durante o conserto. | |
| Você decide | Claude escolhe. | |

**User's choice:** Taguear imagem anterior.
**Notes:** Salto multi-versão (pré-v2.2→v2.3) em réplica única justifica rede de segurança barata/instantânea.

---

## Claude's Discretion

- Ordem exata dos comandos, verificação de DNS/TLS herdados do v2.0, mecânica de achar container id / nome do service (`lazari_money`).
- Warmup de cache/dados pós-restart (cold start do ITUB4) — best-effort se surgir latência no smoke.

## Deferred Ideas

Nenhuma — a discussão ficou dentro do escopo do phase.
