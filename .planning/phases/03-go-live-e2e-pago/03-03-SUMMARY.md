---
phase: 03-go-live-e2e-pago
plan: 03
subsystem: infra
tags: [docker-swarm, traefik, forwardauth, streamlit, django, postgres, backup, lazari-capital]

# Dependency graph
requires:
  - "fork crm-voic: docker-stack.yml + scripts/backup.sh (byte-idênticos ao crm-voic) — base a re-brandar"
  - "engine analista_dividendos/stack.yml: bloco money (gate forwardAuth, sem porta) — dobrado no stack unificado"
  - "01: worker processar_fila_capi podado (crash-loop se mantido); entrypoint.sh roda migrate->seed Plano PRO"
provides:
  - "~/projects/lazari-capital/docker-stack.yml: stack UNIFICADO `lazari` (web+worker+db+money) — deploy canônico da Fase 3"
  - "money referencia o gate pelo FQDN Swarm http://lazari_web:8000/gate/ (resolve o risco #1 — nome curto `web` não resolve entre stacks)"
  - "worker corrigido: só `processar_billing` (comando de fila legado removido → sem crash-loop)"
  - "router 301 money_old: money.voictech.com.br -> app.lazaricapital.com.br (permanente, preserva path, $${1} escapado)"
  - "db Postgres isolado em lazari_internal (nunca em network_swarm_public); volume lazari_postgres_data"
  - "~/projects/lazari-capital/scripts/backup.sh: re-brandado p/ lazari_db, prefixo/retenção lazari-*.sql.gz"
  - "analista_dividendos/stack.yml: anotado como fallback standalone + host/gate corrigidos (invariante sem-porta mantida)"
affects: [03-02-env, 03-04-deploy, 03-05-e2e]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Stack unificado por FQDN: money e web no mesmo stack `lazari` p/ o forwardauth alcançar lazari_web (Pitfall 1)"
    - "Traefik labels no NÍVEL DO SERVIÇO (provider Swarm ignora labels de container)"
    - "$$ escaping: $${1} no 301 e $$(date) no loop do worker (docker stack interpola $)"
    - "Postgres só em overlay interna (lazari_internal); money sem bloco ports: (anti-spoof X-User-Email)"
    - "start_period 180s no healthcheck do web (boot = collectstatic+migrate+seed)"

key-files:
  created: []
  modified:
    - "~/projects/lazari-capital/docker-stack.yml"
    - "~/projects/lazari-capital/scripts/backup.sh"
    - "~/projects/Analista de Investimentos/analista_dividendos/stack.yml"

key-decisions:
  - "Deploy canônico = stack unificado `lazari` (money mora no lazari-capital/docker-stack.yml); engine stack.yml vira fallback anotado"
  - "money só em network_swarm_public — o gate FQDN é chamado PELO Traefik (não pelo money), então não precisa de lazari_internal"
  - "worker mantido (não removido): faz o fechamento diário processar_billing (overdue->graça->bloqueio, D-04), gate por hora às 03:00"
  - "NÃO setar authRequestHeaders no gate (default encaminha Cookie; setar removeria e causaria loop de auth)"

patterns-established:
  - "Cross-stack service reachability por nome qualificado <stack>_<service> (lazari_web)"

requirements-completed: [OPS-01]

# Metrics
duration: ~18min
completed: 2026-07-08
---

# Phase 3 · Plan 03: Stack unificado `lazari` Summary

**Os artefatos de deploy da Lazari Capital estão prontos e consistentes: um `docker-stack.yml` unificado (web+worker+db+money) que resolve o gate por FQDN, corrige o worker quebrado, adiciona o 301 do domínio antigo e isola o Postgres — mais o `backup.sh` e o `stack.yml` do engine re-brandados.**

## Performance

- **Duration:** ~18 min
- **Completed:** 2026-07-08
- **Tasks:** 3/3
- **Files modified:** 3 (2 repos)

## Accomplishments

- **Task 1** — `docker-stack.yml` reescrito como stack único `lazari`: `web` (Django, `www.`), `money` (Streamlit gated, `app.`, gate via `http://lazari_web:8000/gate/`), `db` (Postgres 17 isolado em `lazari_internal`), `worker` (só `processar_billing`), e router `money_old` 301 `money.voictech.com.br → app.` com `$${1}` escapado. Zero referências a pocketleads/crm.voictech/processar_fila_capi/crm_internal/crm_postgres_data.
- **Task 2** — `scripts/backup.sh` re-brandado: `CRM_DB_CONTAINER:-lazari_db`, prefixo/retenção `lazari-*.sql.gz`, cabeçalho Lazari Capital.
- **Task 3** — `analista_dividendos/stack.yml` anotado como fallback (canônico = stack `lazari`) e corrigido: `Host(app.lazaricapital.com.br)` + gate FQDN `lazari_web`; invariante sem-porta preservada.

## Verification

- docker-stack.yml: YAML válido, serviços {web,worker,db,money}; gate FQDN ×1; Host(app.) ×1; 301 money.voictech ×1 com `$${1}`; `processar_billing` ×1; zero termos herdados; money sem `ports:`.
- backup.sh: `lazari` ×5, zero `crm-*.sql.gz`/`crm-voic-db-1`, `bash -n` ok.
- engine stack.yml: `money.voictech` ×0, gate FQDN ×1, sem `ports:`, header cita stack `lazari`; YAML válido.

## Notes for downstream

- **03-04 deploy** builda `lazari-web:latest` (em /opt/lazari-capital) + `money:latest` (repo engine) e roda `docker stack deploy -c docker-stack.yml lazari` — **nunca** `--remove-orphans` (n8n é orphan). Cutover: remover o stack `money` v1.7 antigo SÓ depois do novo validado (Pitfall 6).
- O nome real do container Postgres (`lazari_db`) só se confirma pós-deploy — `backup.sh`/cron dependem de `CRM_DB_CONTAINER` bater (03-04 Task 3).

## Self-Check: PASSED
