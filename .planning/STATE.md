---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Comercialização (Lazari Capital)
status: executing
stopped_at: Phase 3 — code plans done (03-01/03-02T2/03-03); deploy checkpoints pending
last_updated: "2026-07-08T18:23:08.391Z"
last_activity: 2026-07-08 -- Phase 03 code plans executed (landing, prod.py, stack)
progress:
  total_phases: 3
  completed_phases: 2
  total_plans: 13
  completed_plans: 10
  percent: 77
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-07)

**Core value:** O produto cobra de forma confiável e o acesso reflete fielmente o status de
assinatura — quem paga (ou está em trial) entra, quem não tem assinatura ativa não entra — sem
nunca prometer recomendação de investimento (software educacional / CVM).
**Current focus:** Phase 03 — go-live-e2e-pago (deploy checkpoints pendentes)

## Current Position

Phase: 03 (go-live-e2e-pago) — IN PROGRESS
Plans done (código): 03-01 (landing), 03-02 Task 2 (prod.py), 03-03 (stack unificado) — commitados em ambos os repos, 270 testes verdes
Pendente (checkpoints do usuário, sessão de deploy):
  - 03-02 Task 1: confirmar DNS grey-cloud (dig www/app → 31.97.130.40)
  - 03-02 Task 3: criar /opt/lazari-capital/.env prod (chmod 600, segredos Asaas/Resend/DB)
  - 03-04: build + docker stack deploy lazari na VPS + validar TLS/gate/WS + cutover + cron backup
  - 03-05: E2E pago (sandbox + smoke real R$19,90 estornado)
Status: aguardando o usuário para os passos de VPS/segredos/pagamento
Last activity: 2026-07-08 -- Phase 03 code plans executed

Progress: [███████░░░] ~70% (2.5 de 5 planos)

## Performance Metrics

**Velocity:**

- Total plans completed (v1.0–v1.7): 66+ plans em 21 fases (marcos arquivados)
- v2.0: 0 plans completed

**By Phase (v2.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | TBD | - | - |
| 2 | TBD | - | - |
| 3 | TBD | - | - |

**Recent Trend:**

- Último marco enviado: v1.7 (2026-07-04, 338 testes verdes)
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions são registradas na tabela Key Decisions do PROJECT.md. Governando o v2.0:

- **Gateway híbrido com Django** (não reescrever): front Django espelha o crm-voic; engine Streamlit (338 testes) fica intacto atrás do gate.
- **Django + webhooks nativos** no lugar de Supabase + n8n + React — reaproveita o crm-voic 1:1.
- **Gate = Traefik forward-auth**: Django valida sessão+status e injeta `X-User-Email` no Streamlit (menos código de segurança custom que JWT dentro do Streamlit).
- **Asaas em conta e chave próprias** (não as do crm-voic); só a estrutura de código é compartilhada.
- **Cadastro self-serve** (B2C/trial), diferente do crm-voic (invite-only).
- **AUTH-04 (reset de senha) na Phase 1**: acopla à camada de auth do app `accounts`; SMTP fica com backend de dev na Phase 1 e é ligado no deploy (Phase 3).
- **Plan 02-02 (cancel-at-period-end, D-05)**: cancelar chama `DELETE /subscriptions/{id}` e só transiciona local (`CANCELADO` + `grace_ate=paid-through`) APÓS sucesso do DELETE; `grace_ate` reusado como "acesso liberado até" (trial_ate se em trial, senão proximo_vencimento, fim-do-dia aware). `_parse_resposta` trata 204/no-body sem regredir 200+JSON. Página de conta (ACCT-02) sem dado de cartão; anti-IDOR via `request.user.conta`.
- **Plan 02-03 (BILL-04)**: `GateView` regra de 3 ramos fail-closed lendo só `Conta` — pago (`trial_ate is None`), trial vigente, grace de inadimplência (D-04) e paid-through de cancelamento (D-05, via `grace_ate`); corrige o bug em que o pagante (trial zerado por `_ativar_conta`) era bloqueado. `BillingGateMiddleware` isenta `billing-assinar`/`conta`/`cancelar-assinatura` (Pitfall 2) — os dois gates concordam.
- **Plan 02-03 (BILL-03)**: ciclo `assinar→PAYMENT_CONFIRMED→ativação` travado SÓ por teste (`test_webhook_ciclo.py`); `AsaasWebhookView`/`_ativar_conta`/`_marcar_inadimplente` NÃO reescritos — idempotência por `event_id` + convergência por `dueDate` absoluto comprovadas.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- **Websockets do Streamlit atrás do forward-auth:** o gate não pode quebrar os WS do Streamlit — validar na Phase 3 (e desde a Phase 1 ao montar o gate).
- **Repo separado:** o projeto Django vive em `~/projects/lazari-capital` (novo `git init`), distinto deste repo (engine Streamlit). Não misturar históricos.
- **Idempotência dos webhooks:** webhook repetido do Asaas não pode duplicar efeito no status (Phase 2).

## Deferred Items

Items carried forward do fechamento do marco anterior:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Docs engine | DDM-DOC-01 (docstring/teste de t em ddm.py, IN-06) | v2+ | 2026-06-04 |
| Refino | Payout-alvo por setor configurável | v2+ | 2026-06-27 |
| UI | Sinalização de "ano extraordinário" na tabela de Fundamentos | v2+ | 2026-06-27 |

## Session Continuity

Last session: 2026-07-08T17:46:02.426Z
Stopped at: Phase 3 context gathered
Resume file: .planning/phases/03-go-live-e2e-pago/03-CONTEXT.md

## Operator Next Steps

- Planejar a Phase 1 com `/gsd-plan-phase 1` (Fundação: cadastro, login, gate e trial).
- Considerar `/gsd-research-phase 1` para o gate Traefik forward-auth × websockets do Streamlit, se necessário.
