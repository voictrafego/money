---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Comercialização (Lazari Capital)
status: executing
stopped_at: Phase 3 — GO-LIVE no ar (03-01..03-04 done); falta só o E2E pago (03-05)
last_updated: "2026-07-08T18:23:08.391Z"
last_activity: 2026-07-08 -- Phase 03 deploy ao vivo: Lazari Capital no ar (www+app, TLS, gate, 301, backup)
progress:
  total_phases: 3
  completed_phases: 2
  total_plans: 13
  completed_plans: 12
  percent: 92
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-07)

**Core value:** O produto cobra de forma confiável e o acesso reflete fielmente o status de
assinatura — quem paga (ou está em trial) entra, quem não tem assinatura ativa não entra — sem
nunca prometer recomendação de investimento (software educacional / CVM).
**Current focus:** Phase 03 — go-live-e2e-pago (produto NO AR; falta só o E2E pago 03-05)

## Current Position

Phase: 03 (go-live-e2e-pago) — 4 de 5 planos completos; **GO-LIVE no ar**
Completos: 03-01 (landing), 03-02 (DNS+.env+prod.py), 03-03 (stack unificado), 03-04 (deploy+cutover+gate+WS+backup)

**LAZARI CAPITAL NO AR (2026-07-08):**
  - www.lazaricapital.com.br → Django (landing/auth/billing), TLS Let's Encrypt
  - app.lazaricapital.com.br → Analista de Ações (Streamlit) atrás do gate forwardAuth; WS 101 sem loop
  - money.voictech.com.br → 301/308 → app (cutover do money v1.7 concluído; n8n/crm intactos)
  - Stack `lazari` (web+db+money+worker) 1/1 healthy; cron de backup diário do lazari_db
  - Pós-login vai ao produto (app.), não ao /painel/ placeholder do fork

Pendente: **03-05 — E2E pago** (suíte Phase 2 ao vivo + webhook idempotente + transições de status no navegador + 1 cobrança real R$19,90 estornada). Precisa do usuário (pagamento real).

Last activity: 2026-07-10 -- Completed quick task 260710-u1f: feedback de carregamento nas análises

Progress: [█████████░] ~92% (4 de 5 planos; falta o E2E pago)

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

- **Review de UX no navegador (2026-07-10)** — 18 achados de acabamento (engine Streamlit) em
  `.planning/reviews/260710-ux-review-navegador.md`. Semente do **v2.1 (polish de UX)**. Fundação
  sólida; itens são de acabamento. Top-5 já viraram quick tasks:
  - `260710-u1f` 🔴 feedback de carregamento (~35s sem spinner no corpo)
  - `260710-u2r` 🔴 flash de tabela colapsada ao trocar de aba + artefato "0"
  - `260710-u3g` 🟠 glossário de siglas (tabelas transpostas) + legenda de selos/triângulos
    (complementa `260704-kps`, que não cobre rótulo de linha)
  - `260710-u4n` 🟠 padronizar formatação numérica BR (banner `.` vs card `,`; `-0.0%`; `+ -11.17`)
  - `260710-u5c` 🟡 cópia inconsistente ("3 ferramentas"/"4 menus"/5 itens) + termos
  - Achados 6–18 (notícias duplicadas, "carteira" engana, menu Streamlit exposto, responsivo não
    validado, etc.) ficam no doc de review como backlog do v2.1.

### Blockers/Concerns

[Issues that affect future work]

- **Websockets do Streamlit atrás do forward-auth:** o gate não pode quebrar os WS do Streamlit — validar na Phase 3 (e desde a Phase 1 ao montar o gate).
- **Repo separado:** o projeto Django vive em `~/projects/lazari-capital` (novo `git init`), distinto deste repo (engine Streamlit). Não misturar históricos.
- **Idempotência dos webhooks:** webhook repetido do Asaas não pode duplicar efeito no status (Phase 2).

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260710-u1f | Feedback de carregamento nas análises (spinner/status em Analisar/Garimpar/Ranking) | 2026-07-10 | 1e6524e | [260710-u1f-feedback-de-carregamento-nas-analises](./quick/260710-u1f-feedback-de-carregamento-nas-analises/) |

## Deferred Items

Items carried forward do fechamento do marco anterior:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Docs engine | DDM-DOC-01 (docstring/teste de t em ddm.py, IN-06) | v2+ | 2026-06-04 |
| Refino | Payout-alvo por setor configurável | v2+ | 2026-06-27 |
| UI | Sinalização de "ano extraordinário" na tabela de Fundamentos | v2+ | 2026-06-27 |
| Fiscal/NF | **NFS-e AUTOMÁTICA IMPLEMENTADA + VALIDADA (2026-07-09).** Módulo Asaas via Portal Nacional montado (serviço **01.03.01** / tributação nacional **010301**, ISS **2,01%**, Simples, inscrição 3813487, certificado A1). CNAE **6319-4/00**. **Emissão automática por assinatura implementada no código** (lazari-capital `ac0528d`+`15a93eb`): o `assinar` chama `POST /subscriptions/{id}/invoiceSettings` (emite na confirmação do pagamento) e o checkout agora coleta **CEP + número** (exigidos pela NFS-e — sem endereço o Asaas rejeita). Settings env: `ASAAS_NF_AUTO_EMIT`/`_SERVICE_CODE`/`_ISS_ALIQUOTA`. **Validado ao vivo:** invoiceSettings 200; nota de teste do R$19,90 (`inv_000021028809`) foi forçada (`POST /invoices/{id}/authorize` → 200) e está **`SYNCHRONIZED`** (enviada à prefeitura de Londrina, SEM erro) — aguardando retorno assíncrono p/ virar `AUTHORIZED`. **RETOMAR AQUI:** conferir se essa nota autorizou (painel Asaas → Notas Fiscais → Todas, ou reconsultar `/invoices`); se `ERROR`, corrigir o dado recusado. Depois: contador confirmar alíquota ISS oficial (usado 2,01%). Fluxo de venda real já pronto (emite no ato do pagamento). | done | 2026-07-09 |
| UI | NF-e: exibir link da nota emitida (vem no webhook Asaas) na página "Minha conta" → botão "Baixar nota fiscal". Depende da NF ativa no Asaas. | v2.1 | 2026-07-09 |

## Session Continuity

Last session: 2026-07-09 (E2E pago concluído — smoke real R$19,90 PIX confirmado ao vivo)
Stopped at: Phase 3 COMPLETA (03-01..03-05). Milestone v2.0 (Comercialização/Lazari Capital) fechado.
Resume file: **.planning/phases/03-go-live-e2e-pago/03-05-SUMMARY.md**

## Operator Next Steps

- Estornar (ou não) o smoke real R$19,90 PIX no painel Asaas — decisão do operador (deixado na conta por ora).
- Arquivar o milestone v2.0 com `/gsd-complete-milestone` quando quiser.
- Backlog v2.1 (ver Deferred Items): ativar NFS-e no painel Asaas + link da NF na página de conta.
