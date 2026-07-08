---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Comercialização (Lazari Capital)
status: executing
stopped_at: Phase 1 context gathered
last_updated: "2026-07-08T01:03:27.552Z"
last_activity: 2026-07-08 -- Phase 01 planning complete
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 5
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-07)

**Core value:** O produto cobra de forma confiável e o acesso reflete fielmente o status de
assinatura — quem paga (ou está em trial) entra, quem não tem assinatura ativa não entra — sem
nunca prometer recomendação de investimento (software educacional / CVM).
**Current focus:** v2.0 Comercialização — Phase 1 (Fundação: cadastro, login, gate e trial).

## Current Position

Phase: 1 of 3 (Fundação — Cadastro, Login, Gate e Trial)
Plan: — (roadmap criado; próxima etapa é planejar a Phase 1)
Status: Ready to execute
Last activity: 2026-07-08 -- Phase 01 planning complete

Progress: [░░░░░░░░░░] 0%

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

Last session: 2026-07-08T00:15:50.084Z
Stopped at: Phase 1 context gathered
Resume file: .planning/phases/01-funda-o-cadastro-login-gate-e-trial/01-CONTEXT.md

## Operator Next Steps

- Planejar a Phase 1 com `/gsd-plan-phase 1` (Fundação: cadastro, login, gate e trial).
- Considerar `/gsd-research-phase 1` para o gate Traefik forward-auth × websockets do Streamlit, se necessário.
