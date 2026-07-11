# Phase 2: Cobrança Asaas + Webhooks + Conta - Research

**Researched:** 2026-07-08
**Domain:** Recurring billing (Asaas hosted checkout) + native Django webhooks + access gate + account page
**Confidence:** HIGH (Asaas API verified against official docs; existing code read line-by-line)

## Summary

Phase 2 does **not** start from a blank slate. The `lazari-capital` repo was forked from `crm-voic`,
and the fork already ships most of the billing machinery: an `AsaasClient` with `criar_cliente`,
`criar_assinatura` (billingType `UNDEFINED`, cycle `MONTHLY`, `nextDueDate`), `atualizar_assinatura`
(PUT) and `primeira_fatura_url` (hosted invoice link); a fully hardened idempotent `AsaasWebhookView`
that already handles `PAYMENT_CONFIRMED`/`PAYMENT_RECEIVED`/`PAYMENT_OVERDUE`; the `Assinatura`,
`Plano`, `AsaasWebhookLog` models; and the `_ativar_conta`/`_marcar_inadimplente` transition services.
The webhook auth (constant-time compare of the `asaas-access-token` header), idempotency key
(`AsaasWebhookLog.event_id` = payload `id`), and unscoped tenant correlation are all in place and
match the current Asaas contract [VERIFIED: Asaas docs].

The real Phase 2 work is the pieces the fork did **not** carry over because the B2C signup was
rebuilt as trial-first (`provisionar_signup` creates a trial account with NO Asaas customer, NO CPF,
NO subscription). Those gaps: (1) a **net-new authenticated "Assinar" checkout flow** that collects a
CPF (Asaas *requires* `cpfCnpj` to create a customer — the B2C signup form deliberately omits it),
creates the customer + subscription, and redirects to the Asaas-hosted invoice URL; (2) a **cancel
flow** (`DELETE /v3/subscriptions/{id}` — a method the `AsaasClient` does not yet have); (3) the
**GateView extension** to honor paid-active / grace / cancel-at-period-end; (4) the **Plano PRO seed**;
(5) the **account page** (ACCT-02); and (6) reconciling the still-active `BillingGateMiddleware`
(inherited from crm-voic) so the account/checkout routes stay reachable for non-active accounts.

**Primary recommendation:** Extend the existing `apps/billing` infrastructure — do NOT rewrite it.
Add a CPF-collecting `assinar` service + view, a `cancelar_assinatura` (DELETE) client method + view,
seed the single PRO plano via a data migration, extend `GateView` to read paid/grace/cancel states
from `Conta` alone, and exempt the new billing routes from `BillingGateMiddleware`.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Assinatura via **checkout hospedado do Asaas** — backend cria customer + subscription via
  `AsaasClient` e redireciona ao link hospedado. O produto **nunca** manuseia/armazena dados de cartão.
- **D-02:** A **1ª cobrança cai no fim do trial**: ao assinar durante o trial, `nextDueDate = Conta.trial_ate`.
  (Se já fora do trial, cobrança na próxima data padrão.)
- **D-03:** **Plano único "PRO", mensal, R$ 19,90** (ciclo `MONTHLY`). Seedar exatamente 1 `Plano`
  (data migration ou management command). `valor_mensal`/`preco_mensal` da `Assinatura` é snapshot na contratação.
- **D-04:** Após `PAYMENT_OVERDUE`, **7 dias de graça** antes do gate bloquear. Overdue seta
  `Conta.status = inadimplente` e `grace_ate = data_vencimento + 7 dias`; gate libera enquanto
  `now <= grace_ate`, bloqueia depois.
- **D-05:** Cancelamento **vale até o fim do período já pago** (cancel-at-period-end). Botão chama a
  API do Asaas para não renovar; `Conta.status = cancelado`, mas o **gate continua liberando até a
  data paga** (paid-through / `trial_ate` se ainda em trial). Sem reembolso proporcional.

### Claude's Discretion
- Mapeamento fino dos eventos de webhook → transições de status (reusar/estender o handler existente).
- Poda de resíduos B2B (`Cupom`/`ResgateCupom`/`cupom_service`, `TrialCpf`) — manter dormente ou podar;
  **NÃO introduzir cupom nesta fase**.
- App do webhook: usar **`apps/billing`**, NÃO `apps/webhooks`.
- Idempotência: manter o padrão existente (insert-and-catch atômico em `AsaasWebhookLog.event_id`).

### Deferred Ideas (OUT OF SCOPE)
- Plano anual / descontos.
- Cupons de desconto (infra `Cupom`/`ResgateCupom` — manter dormente).
- Deploy/E2E pago ao vivo, Traefik/domínio, SMTP prod, páginas legais reais — Phase 3 (OPS-01).
- Página de vendas www.lazaricapital.com.br.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **BILL-02** | Cobrança recorrente mensal via Asaas, checkout **hospedado** (produto nunca toca cartão) | `AsaasClient.criar_cliente`/`criar_assinatura` (billingType `UNDEFINED` = método escolhido no checkout hospedado) + `primeira_fatura_url` já existem; falta o fluxo `assinar` autenticado + coleta de CPF (obrigatório no Asaas). Ver §Standard Stack, §Pitfall 1, §Code Examples. |
| **BILL-03** | Webhooks nativos Django idempotentes atualizam o status (Postgres) | `AsaasWebhookView` já implementa auth+idempotência+correlação+dispatch; `_ativar_conta`/`_marcar_inadimplente` já cobrem PAYMENT_CONFIRMED/RECEIVED/OVERDUE. Confirmado que esses eventos bastam para a máquina de estado. Ver §Architecture, §Pitfall 3. |
| **BILL-04** | Gate lê trial-OU-ativa; bloqueia após período devido | `GateView` (Phase 1) lê `Conta.status`/`trial_ate`. Extensão precisa cobrir paid-active (`trial_ate is None`), grace (`inadimplente`+`grace_ate`) e cancel-at-period-end. Regra precisa em §Gate Status Machine. |
| **ACCT-02** | Página de conta: status + link de cobrança + cancelar, sem expor dados sensíveis | Nova view lê `Conta`+`Assinatura`; link = `Assinatura.invoice_url`; cancelar chama `AsaasClient.cancelar_assinatura` (DELETE — método NOVO). Ver §Architecture, §Pitfall 2/6. |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Criar customer + subscription (hosted checkout) | API/Backend (`apps/billing.services.assinar` + `AsaasClient`) | External (Asaas) | Card data lives ONLY at Asaas hosted checkout; backend só orquestra e persiste ids. |
| Coleta de CPF (obrigatório p/ Asaas) | Frontend Server (form Django) | API/Backend (validação) | Asaas exige `cpfCnpj`; borda de validação no form (CLAUDE.md: validar só nas bordas). |
| Redirect ao checkout hospedado | API/Backend (302 → `invoiceUrl`) | External (Asaas) | Nunca renderizar formulário de cartão próprio (D-01). |
| Webhook status machine | API/Backend (`AsaasWebhookView` + services) | Database (Postgres source of truth) | Idempotente, sem n8n (PROJECT.md). |
| Access gate | API/Backend (`GateView`, forward-auth) | Database | Traefik chama; decisão fail-closed lendo `Conta`. |
| Route gate (Django) | API/Backend (`BillingGateMiddleware`) | — | Bloqueia rotas Django p/ status não-ativo; precisa exemption p/ conta/checkout. |
| Account page (status/cancel/link) | API/Backend (view) + Frontend (template) | Database | Lê `Conta`/`Assinatura`; nunca expõe dado de cartão. |
| Plano seed | Database (data migration) | — | Roda no `migrate` do deploy (Phase 3). |

## Standard Stack

### Core (already present in `lazari-capital` — reuse, don't rebuild)
| Component | File / Symbol | Purpose | Status |
|-----------|---------------|---------|--------|
| Asaas HTTP client | `apps/billing/asaas_client.py :: AsaasClient` | v3 API (customers/subscriptions/payments), retry classificado por segurança de re-entrega | Reuse; **add `cancelar_assinatura` (DELETE)** |
| Create customer | `AsaasClient.criar_cliente(name, cpf_cnpj, email, mobile_phone, external_reference)` | `POST /v3/customers` (retry_safe=True, Asaas dedup por CNPJ) | Reuse as-is |
| Create subscription | `AsaasClient.criar_assinatura(customer, next_due_date, value, description, discount=None)` | `POST /v3/subscriptions` — billingType `UNDEFINED`, cycle `MONTHLY`, non-idempotent (retry_safe=False) | Reuse; ignore `discount` (no coupons this phase) |
| Hosted invoice link | `AsaasClient.primeira_fatura_url(sub_id)` | `GET /v3/payments?subscription={id}&limit=1` → `invoiceUrl` | Reuse; handle `''` (fatura ainda não gerada) |
| Update subscription | `AsaasClient.atualizar_assinatura(sub_id, discount, update_pending_payments)` | `PUT /v3/subscriptions/{id}` | Present but coupon-only — not needed this phase |
| Webhook endpoint | `apps/billing/views.py :: AsaasWebhookView` (`POST /billing/webhook/`) | csrf_exempt, header auth, idempotência, correlação unscoped, dispatch | Reuse; extend dispatch if new events chosen |
| Idempotency log | `apps/billing/models.py :: AsaasWebhookLog` (`event_id` unique) | insert-and-catch atômico antes de efeito colateral | Reuse as-is |
| Subscription model | `apps/billing/models.py :: Assinatura` (`asaas_sub_id`, `ciclo_status`, `preco_mensal` snapshot, `invoice_url`, `proximo_vencimento`, `ultimo_pagamento`, UniqueConstraint(conta)) | Vínculo conta–plano (TenantModel) | Reuse; **1 por conta** (see Pitfall 5) |
| Plan model | `apps/billing/models.py :: Plano` (`preco_mensal`, `grace_period_dias` default 7, `max_usuarios`) | GLOBAL (não TenantModel) | Reuse; **seed 1 PRO** |
| Activation service | `apps/billing/services.py :: _ativar_conta(conta, assinatura, payment)` | PAYMENT_CONFIRMED/RECEIVED → ATIVO, trial_ate=None, ciclo PAGO, proximo_vencimento absoluto | Reuse; drop `cupom_service.confirmar` call if pruning coupons |
| Overdue service | `apps/billing/services.py :: _marcar_inadimplente(conta, assinatura, payment)` | PAYMENT_OVERDUE → INADIMPLENTE, grace_ate = now + grace_period_dias | Reuse as-is |
| Access gate | `apps/gate/views.py :: GateView` | forward-auth, read-only, fail-closed | **Extend** (BILL-04) |
| Route gate | `apps/core/middleware/billing_gate.py :: BillingGateMiddleware` | Bloqueia rotas Django p/ status não-ativo | **Exempt** conta/checkout routes |
| Daily billing job | `apps/billing/management/commands/processar_billing.py` | Safety-net: trial vencido→inadimplente, grace vencido→suspenso | Reuse (wiring do cron é Phase 3) |
| Tenant context | `apps/core/middleware/tenant.py` + `apps/core/managers.py` | Seta `conta_id` do `request.user` p/ views autenticadas | Reuse — account page reads `Assinatura` scoped automatically |

### Supporting (external)
| Dependency | Version | Purpose |
|------------|---------|---------|
| Asaas API | v3 | `ASAAS_BASE_URL` default `https://api-sandbox.asaas.com/v3` (sandbox); prod trava na Phase 3 [VERIFIED: config/settings/base.py:35] |
| requests | (already vendored) | `AsaasClient` usa `requests.Session` — sem SDK novo |

**No new libraries required.** Everything is Django 5.2 + `requests` + the existing app structure
(Python 3.12, Postgres). [VERIFIED: apps/billing/asaas_client.py imports only `requests`, `django.conf`]

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Redirect ao `invoiceUrl` da 1ª fatura | Um "link de assinatura" único do Asaas | Assinaturas Asaas NÃO têm URL de checkout única; cada fatura (payment) tem seu `invoiceUrl`. Redirecionar à 1ª fatura é o caminho hospedado correto (já implementado em `primeira_fatura_url`). [VERIFIED: Asaas docs — subscription cria payments; invoiceUrl é por payment] |
| Data migration p/ seed do Plano | Management command | Data migration roda automática no `migrate` (deploy Phase 3) sem passo manual — recomendado (D-03). Command exigiria lembrar de rodar. |
| Novos eventos de subscription no webhook | Só eventos PAYMENT_* | Eventos PAYMENT_* já dirigem toda a máquina de estado; subscription events (SUBSCRIPTION_*) são de fila separada e não necessários (cancel é app-initiated). Ver §Webhook Events. |

## Architecture Patterns

### System Architecture Diagram

```
TRIAL USER (autenticado, status=ATIVO, trial_ate>=hoje)
   │
   │ clica [Assinar]  (na página trial-acabou ou na conta)
   ▼
┌──────────────────────────────────────────────────────────────┐
│ AssinarView (NOVA, autenticada)                              │
│   GET  → form de CPF (Asaas exige cpfCnpj)                    │
│   POST → services.assinar(conta, cpf):                       │
│     1. AsaasClient.criar_cliente(cpf) ──► Asaas POST /customers
│        └─ Conta.asaas_customer_id = id                        │
│     2. AsaasClient.criar_assinatura(                          │
│          customer, next_due_date=Conta.trial_ate,            │
│          value=Plano.preco_mensal, cycle=MONTHLY) ──► Asaas   │
│        └─ Assinatura(asaas_sub_id, preco_mensal snapshot,    │
│                      proximo_vencimento=trial_ate)            │
│     3. Conta.plano = PRO                                      │
│     4. invoice_url = AsaasClient.primeira_fatura_url(sub_id)  │
│   302 REDIRECT ──────────────────────────────► Asaas HOSTED  │
│                                                  CHECKOUT      │
└──────────────────────────────────────────────────────────────┘        (cartão/PIX/boleto —
                                                                          nunca toca o backend)
   user paga no Asaas
   │
   ▼
┌──────────────────────────────────────────────────────────────┐
│ Asaas  ──POST /billing/webhook/──►  AsaasWebhookView         │
│   header asaas-access-token (constant-time compare)          │
│   1. AUTH  → 401 se token inválido                           │
│   2. PARSE → 400 se não-JSON                                 │
│   3. IDEMPOTÊNCIA → insert AsaasWebhookLog(event_id) atômico │
│   4. CORRELAÇÃO → Assinatura.unscoped() por payment.subscription
│   5. DISPATCH (set_current_conta_id):                        │
│        PAYMENT_CONFIRMED/RECEIVED → _ativar_conta            │
│           (status=ATIVO, trial_ate=None, ciclo=PAGO,         │
│            proximo_vencimento = dueDate + 30d)               │
│        PAYMENT_OVERDUE → _marcar_inadimplente               │
│           (status=INADIMPLENTE, grace_ate = now + 7d)        │
└──────────────────────────────────────────────────────────────┘
   │ (Postgres = source of truth)
   ▼
┌──────────────────────────────────────────────────────────────┐
│ Traefik forward-auth ──GET /gate/──► GateView (EXTENDIDA)   │
│   allow (200 + X-User-Email) se:                            │
│     ATIVO   & (trial_ate is None  OR trial_ate>=hoje)       │
│     INADIMPLENTE & now<=grace_ate                           │
│     CANCELADO   & now<=grace_ate (=paid-through, D-05)      │
│   senão 302 → /trial-acabou/                                │
└──────────────────────────────────────────────────────────────┘

ACCOUNT PAGE (NOVA, autenticada, ACCT-02)
   lê Conta + Assinatura → mostra status, proximo_vencimento,
   [link de cobrança = Assinatura.invoice_url], [Cancelar]
   [Cancelar] POST → services.cancelar(conta):
       AsaasClient.cancelar_assinatura(sub_id)  ──► Asaas DELETE /subscriptions/{id}
       Conta.status = CANCELADO
       Conta.grace_ate = Assinatura.proximo_vencimento   (paid-through, D-05)
```

### Recommended Structure (additions to existing apps/billing + apps/accounts)
```
apps/billing/
├── asaas_client.py     # + cancelar_assinatura (DELETE) ; + _delete no _request
├── services.py         # + assinar(conta, cpf) ; + cancelar(conta)
├── forms.py            # + CpfForm (borda de validação do CPF)
├── views.py            # + AssinarView (GET form / POST cria+redirect)
├── migrations/         # + 0002_seed_plano_pro.py (data migration, D-03)
apps/accounts/
├── views.py            # + ContaView (ACCT-02) ; + CancelarAssinaturaView
├── urls.py             # + rotas conta / cancelar
apps/gate/
├── views.py            # GateView estendida (BILL-04)
templates/
├── billing/assinar.html, accounts/conta.html
```

### Pattern 1: Hosted-checkout subscription (D-01/D-02)
**What:** Backend cria customer + subscription com `billingType='UNDEFINED'`; o cliente escolhe o
meio de pagamento no checkout **hospedado** do Asaas (`invoiceUrl`). `nextDueDate = trial_ate` adia a
1ª cobrança para o fim do trial.
**When:** No clique [Assinar] de um usuário autenticado em trial (ou fora do trial → data padrão).
**Verified:** `billingType` aceita `UNDEFINED|BOLETO|CREDIT_CARD|PIX`; `nextDueDate` = "data de
vencimento da primeira cobrança"; `cycle` aceita `MONTHLY` [CITED: docs.asaas.com/reference/criar-nova-assinatura].

### Pattern 2: Idempotent native webhook (BILL-03)
**What:** insert-and-catch atômico em `AsaasWebhookLog.event_id` (= payload `id`) ANTES de qualquer
efeito colateral; correlação por `payment.subscription` via `Assinatura.objects.unscoped()`; tenant
setado só após resolver a conta; sempre 200 (Asaas pausa a fila após não-2xx consecutivos).
**Verified:** payload event id = `"id"`, event type = `"event"`; Asaas exige HTTP 200 p/ considerar
entregue [CITED: docs.asaas.com/docs/webhook-para-cobrancas, docs.asaas.com/docs/about-webhooks].
Já implementado em `AsaasWebhookView` — reusar intacto.

### Pattern 3: Cancel-at-period-end (D-05)
**What:** `DELETE /v3/subscriptions/{id}` para de gerar novas cobranças; faturas já pagas permanecem;
pendentes/vencidas são removidas. App seta `status=CANCELADO` e `grace_ate=proximo_vencimento` para o
gate continuar liberando até o paid-through.
**Verified:** DELETE remove renovações futuras, mantém histórico de pagas, remove pendentes/vencidas
[CITED: docs.asaas.com/reference/remover-assinatura].

### Anti-Patterns to Avoid
- **Renderizar formulário de cartão próprio:** proibido (D-01). O PAN nunca toca o backend — só o
  `invoiceUrl` hospedado. `AsaasClient` nunca monta dados de cartão (docstring do módulo confirma).
- **Check-then-insert na idempotência:** usar SEMPRE insert-and-catch atômico (já é o padrão).
- **Ler `asaas_sub_id`/`conta_id` do cliente:** cancel deriva de `request.user.conta` (V4/IDOR), nunca
  de um id vindo do POST.
- **Gate lendo TenantModel em forward-auth:** manter `GateView` lendo só `Conta` (ver Gate Machine) —
  evita depender do tenant thread-local no caminho do Traefik.

## Gate Status Machine (BILL-04) — precise boolean

The gate must decide in real time from `Conta` alone (keep `GateView` reading only `Conta`, as today).
Recommended rule — **allow (200 + `X-User-Email`) if ANY**:

```python
from django.utils import timezone
now = timezone.now()
today = timezone.localdate()
S = Conta.Status
allow = (
    (conta.status == S.ATIVO and (conta.trial_ate is None or conta.trial_ate >= today))  # paid OR trial
    or (conta.status == S.INADIMPLENTE and conta.grace_ate is not None and now <= conta.grace_ate)  # grace (D-04)
    or (conta.status == S.CANCELADO   and conta.grace_ate is not None and now <= conta.grace_ate)  # paid-through (D-05)
)
```
Otherwise 302 `/trial-acabou/`.

**Why this works with the existing model** [VERIFIED: apps/accounts/models.py, apps/billing/services.py]:
- **Trial:** `_ativar_por_token` sets `status=ATIVO, trial_ate=hoje+7`. → `trial_ate >= today`.
- **Paid active:** `_ativar_conta` sets `status=ATIVO, trial_ate=None, grace_ate=None` on
  PAYMENT_CONFIRMED. → `trial_ate is None` branch. (No need to read `Assinatura` — the `None` is the flag.)
- **Grace (overdue):** `_marcar_inadimplente` sets `status=INADIMPLENTE, grace_ate=now+7d`. → grace branch.
- **Cancel-at-period-end:** the NEW cancel service sets `status=CANCELADO` and **`grace_ate =
  Assinatura.proximo_vencimento`** (reuse `grace_ate` as the generic "acesso liberado até" date). →
  cancel branch. This keeps the gate reading `Conta` only.
- **Blocked:** `SUSPENSO`, `PENDENTE_PAGAMENTO`, `ATIVO` with expired trial (`trial_ate < today`),
  grace expired, cancel past paid-through.

`grace_ate` is a `DateTimeField`; `trial_ate` is a `DateField` — compare with `timezone.now()` and
`timezone.localdate()` respectively (mismatch is a real bug source; `_marcar_inadimplente` already
uses `timezone.now()`).

**Note:** `GateView`'s current comment anticipates only `... OR assinatura_paga` — that captures the
paid-active case but NOT grace/cancel. The planner should implement the full three-branch rule above.
The `processar_billing` daily job is a safety-net that converges blocked states to `SUSPENSO`/
`INADIMPLENTE`, but the gate must be correct in real time regardless of whether the job has run.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chamar a API Asaas | HTTP client novo | `AsaasClient` existente | Já tem retry classificado por segurança de re-entrega, tratamento de erro sem vazar API key, timeouts. |
| Idempotência de webhook | Cache/set custom | `AsaasWebhookLog.event_id` insert-and-catch | Já atômico, à prova de corrida, testado. |
| Auth do webhook | HMAC de assinatura custom | header `asaas-access-token` + `hmac.compare_digest` | É o mecanismo do Asaas (não há assinatura HMAC de corpo). Já implementado constant-time. |
| Máquina de estado de pagamento | Novo dispatcher | `_ativar_conta`/`_marcar_inadimplente` | Já convergem idempotentemente (PAYMENT_CONFIRMED+RECEIVED 2×) via datas absolutas. |
| Checkout de cartão | Form de cartão | Redirect ao `invoiceUrl` hospedado | PCI: o cartão nunca toca o backend (D-01). |
| Seed de plano | Script ad-hoc | Data migration idempotente | Roda no `migrate` do deploy. |

**Key insight:** ~70% do Phase 2 já existe no fork. O risco NÃO é construir do zero — é (a) descobrir
os buracos B2C que o fork deixou (CPF, fluxo de assinatura autenticado, cancel DELETE) e (b) não
duplicar/regredir a infra hardened que já passa nos testes.

## Webhook Events → status machine (Claude's Discretion resolved)

Canonical Asaas payment events [CITED: docs.asaas.com/docs/webhook-para-cobrancas]:
`PAYMENT_CREATED, PAYMENT_UPDATED, PAYMENT_CONFIRMED, PAYMENT_RECEIVED, PAYMENT_OVERDUE,
PAYMENT_REFUNDED, PAYMENT_DELETED, PAYMENT_RESTORED, PAYMENT_CHARGEBACK_*`, etc. Subscription-cycle
events (`SUBSCRIPTION_*`) exist but are a **separate sync queue** and are not required here.

| Asaas event | Transition | Handler | Status |
|-------------|-----------|---------|--------|
| `PAYMENT_CONFIRMED` | → ATIVO (paid), trial_ate=None, ciclo=PAGO, avança proximo_vencimento | `_ativar_conta` | ✅ present |
| `PAYMENT_RECEIVED` | idem (mesmo pagamento, event_id distinto — converge por data) | `_ativar_conta` | ✅ present |
| `PAYMENT_OVERDUE` | → INADIMPLENTE, grace_ate=now+7d (arma a graça) | `_marcar_inadimplente` | ✅ present |
| others | log-only (já persistido em `AsaasWebhookLog`) | — | ✅ default |

**Recommendation:** The three handled events are **sufficient** for BILL-02/03/04. Cancel is
app-initiated (account page → DELETE + set status), so no `SUBSCRIPTION_DELETED` webhook is needed.
`PAYMENT_REFUNDED`/`PAYMENT_DELETED` handling is a future enhancement (out of scope). Correlation is by
`payment.subscription`; pure subscription events (no `payment`) correlate to `sub_id=''` → 200 silent
(safely ignored) [VERIFIED: apps/billing/views.py:207-218].

## Idempotency & Delivery (confirmed)

- **Idempotency key:** `AsaasWebhookLog.event_id` = payload `"id"` — a stable per-event id from Asaas.
  Insert-and-catch on the `unique` constraint is the correct pattern [VERIFIED: models.py:167,
  views.py:198-205; CITED: Asaas webhook payload id field].
- **Delivery:** Asaas delivers sequentially and **pauses the queue after consecutive non-2xx
  responses** — hence the view returns 200 even on internal error (event already logged for audit)
  [CITED: docs.asaas.com/docs/about-webhooks — "HTTP status must be 200"; VERIFIED: views.py:229-237].
- **Card double-fire:** `PAYMENT_CONFIRMED` and `PAYMENT_RECEIVED` fire for the same card payment with
  DIFFERENT event_ids — `event_id` dedup does NOT collapse them; `_ativar_conta` converges via absolute
  `payment["dueDate"]` (only advances if greater) [VERIFIED: services.py:210-298].

## Webhook Security (feeds threat model)

- **Auth:** Asaas sends the configured token in the `asaas-access-token` header on every call; the
  endpoint compares it constant-time against `settings.ASAAS_WEBHOOK_TOKEN` and returns 401 before any
  DB write [VERIFIED: views.py:177-181; CITED: docs.asaas.com/docs/about-webhooks]. Asaas has **no
  body-signature HMAC** — the header token is the sole credential.
- **Token strength:** Asaas now enforces token complexity (no short/predictable/sequential/repeated,
  not the API key) and auto-generates a strong token if none is provided at webhook creation
  [CITED: docs.asaas.com/changelog — token complexity/auto-generation]. Set a strong `ASAAS_WEBHOOK_TOKEN`.
- **csrf_exempt** is correct for M2M (credential = header, no cookie/session) [VERIFIED: views.py:153].
- Order-of-operations (AUTH→PARSE→IDEMPOTÊNCIA→CORRELAÇÃO→DISPATCH) already documented as threat model
  T-17-07..T-17-13 in the view docstring — reuse.

## Runtime State Inventory

> Phase 2 is greenfield feature work (new views/services/migration) on a fresh Django app — not a
> rename/migration of existing runtime state. The one stateful concern is external:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `Conta.asaas_customer_id`, `Assinatura.asaas_sub_id` — populated by the NEW checkout flow (empty today; no user has subscribed yet) | New writes only; no migration of existing records |
| Live service config | Asaas **webhook must be registered in the Asaas dashboard/API** pointing at `POST /billing/webhook/` with the `asaas-access-token`. This config lives at Asaas, NOT in git. | Register in Phase 3 (deploy); note as env/ops dependency |
| OS-registered state | None — verified (no cron/scheduler wired this phase; `processar_billing` cron is Phase 3) | None |
| Secrets/env vars | `ASAAS_API_KEY`, `ASAAS_BASE_URL`, `ASAAS_WEBHOOK_TOKEN` (read via `os.environ.get`/`env`) — code reads by name; real values are prod secrets (Phase 3) | None this phase (sandbox defaults present) |
| Build artifacts | None — verified (no packaging/egg-info; pure Django app) | None |

## Common Pitfalls

### Pitfall 1: Asaas REQUIRES `cpfCnpj` — the B2C signup never collects it
**What goes wrong:** `POST /v3/customers` fails without `cpfCnpj` (it is a **required** field)
[CITED: docs.asaas.com/reference/criar-novo-cliente]. But `SignupForm` deliberately omits CPF/CNPJ,
and `provisionar_signup` creates no Asaas customer [VERIFIED: forms.py docstring, services.py:60-103].
**Why:** The fork's original signup collected CPF; the B2C rebuild made signup trial-first with no CPF.
**How to avoid:** Collect CPF in the **new `assinar` checkout flow** (a `CpfForm`), validate it at the
border, then call `criar_cliente(cpf_cnpj=...)`. Persist `Conta.asaas_customer_id`. Do NOT try to
collect CPF at signup (would break the frictionless trial).
**Warning sign:** `AsaasError` with "cpfCnpj" in the description on first subscribe.

### Pitfall 2: `BillingGateMiddleware` will redirect non-active accounts AWAY from the account/checkout page
**What goes wrong:** `BillingGateMiddleware` (inherited from crm-voic, **still active** in
`MIDDLEWARE`) redirects `PENDENTE_PAGAMENTO`/`SUSPENSO`/`CANCELADO` accounts to
`pagamento-pendente`/`conta-suspensa` for ANY non-exempt route [VERIFIED: base.py:80,
billing_gate.py]. A cancelled user opening the account page (to re-subscribe or view status) would be
bounced.
**Why:** The exemption list (`EXEMPT_URL_NAMES`) has reserved slots (`billing-signup`,
`billing-webhook`) but NOT the new account/checkout routes.
**How to avoid:** Add the new `assinar` and account-page route names to `EXEMPT_URL_NAMES` (and cancel
route). Decide explicitly whether cancelled/suspended users should reach checkout (they should, to
re-subscribe). Note the two-gate architecture: `BillingGateMiddleware` guards Django routes;
`GateView` guards Streamlit — they must agree.
**Warning sign:** 302 loop or redirect to `conta-suspensa` when opening `/conta/`.

### Pitfall 3: DateField vs DateTimeField in the gate/grace comparison
**What goes wrong:** `trial_ate` is `DateField`, `grace_ate` is `DateTimeField`. Comparing `grace_ate`
with `date.today()` (or `trial_ate` with `timezone.now()`) yields TypeErrors or off-by-hours bugs.
**How to avoid:** `grace_ate` → `timezone.now()`; `trial_ate` → `timezone.localdate()`
[VERIFIED: services.py:321 uses `timezone.now()`; gate/views.py:43 uses `timezone.localdate()`].

### Pitfall 4: First invoice `invoiceUrl` may not exist immediately
**What goes wrong:** `primeira_fatura_url` returns `''` when the subscription's first payment hasn't
been generated yet [VERIFIED: asaas_client.py:127-134]. Redirecting to `''` breaks the checkout.
**Why:** With `nextDueDate` in the future (trial end), the first fatura is generated but there can be a
brief lag; a malformed/empty response also yields `''`.
**How to avoid:** Handle empty `invoiceUrl` — persist `Assinatura.invoice_url` when available; if empty,
show a "pagamento pendente" page (there is already `PagamentoPendenteView`/`pagamento_pendente.html`)
that can re-fetch the link, rather than 302 to an empty URL.

### Pitfall 5: `Assinatura` has `UniqueConstraint(conta)` — re-subscribe after cancel collides
**What goes wrong:** Only ONE `Assinatura` per `Conta` [VERIFIED: models.py:137-140]. A user who
cancels then subscribes again would violate the constraint if the flow blindly `create()`s.
**How to avoid:** `assinar` must `update_or_create`/reuse the existing `Assinatura` row (new
`asaas_sub_id`, reset `ciclo_status=AGUARDANDO`, new `proximo_vencimento`) instead of inserting a
second. Also reset `Conta.grace_ate=None`/`status` appropriately on re-subscribe.

### Pitfall 6: Account page must not expose sensitive payment data (ACCT-02)
**What goes wrong:** Rendering card/PII would breach ACCT-02.
**How to avoid:** The backend never holds card data (hosted checkout). Show only: plano name/price,
`Conta.status`, `Assinatura.proximo_vencimento`, and the Asaas hosted link (`Assinatura.invoice_url`)
+ a Cancel button. Nothing else. Cancel derives the subscription from `request.user.conta` (no id from
the client).

### Pitfall 7: `AsaasClient._request` has no DELETE verb
**What goes wrong:** Cancel needs `DELETE /v3/subscriptions/{id}` but `_request` only wires
`get`/`post`/`put` [VERIFIED: asaas_client.py:145-166 — `getattr(self._session, method)` supports
`delete`, but there's no `_delete`/`cancelar_assinatura` public method].
**How to avoid:** Add `cancelar_assinatura(sub_id)` → `self._request('delete', f'/subscriptions/{sub_id}', retry_safe=True)` (DELETE is idempotent — retry-safe). `getattr(session,'delete')` already works;
just add the public method. Note DELETE returns `{deleted: true}` with 200 (no fixed body documented).

## Code Examples

### Create customer + subscription (hosted, D-02) — new `services.assinar`
```python
# Uses existing AsaasClient (asaas_client.py). Illustrative — planner owns final shape.
from apps.billing.asaas_client import AsaasClient
from apps.billing.models import Assinatura, Plano

def assinar(conta, *, cpf, email, telefone):
    plano = Plano.objects.get(nome="PRO", ativo=True)   # global manager (not TenantModel)
    client = AsaasClient()
    cliente = client.criar_cliente(
        name=conta.nome, cpf_cnpj=cpf, email=email,
        mobile_phone=telefone, external_reference=str(conta.pk),
    )
    conta.asaas_customer_id = cliente["id"]
    conta.plano = plano
    conta.save(update_fields=["asaas_customer_id", "plano"])

    sub = client.criar_assinatura(
        customer=cliente["id"],
        next_due_date=conta.trial_ate.isoformat(),   # D-02: 1ª cobrança no fim do trial
        value=plano.preco_mensal,                     # Decimal — client faz float() na borda
        description="Assinatura PRO — Lazari Capital",
    )
    assinatura, _ = Assinatura.objects.update_or_create(   # Pitfall 5: 1 por conta
        conta=conta,
        defaults=dict(
            plano=plano, preco_mensal=plano.preco_mensal,
            asaas_sub_id=sub["id"],
            ciclo_status=Assinatura.CicloStatus.AGUARDANDO,
            proximo_vencimento=conta.trial_ate,
        ),
    )
    assinatura.invoice_url = client.primeira_fatura_url(sub["id"])  # Pitfall 4: pode vir ''
    assinatura.save(update_fields=["invoice_url"])
    return assinatura   # view redireciona p/ assinatura.invoice_url (302) OU pagamento-pendente se ''
```

### Cancel-at-period-end (D-05) — new client method + service
```python
# asaas_client.py — add:
def cancelar_assinatura(self, sub_id):
    """DELETE /subscriptions/{id} — para renovações futuras (idempotente → retry_safe=True)."""
    return self._request('delete', f'/subscriptions/{sub_id}', retry_safe=True)

# services.py — add:
def cancelar(conta):
    assinatura = Assinatura.objects.get(conta=conta)   # tenant-scoped (TenantMiddleware setou)
    AsaasClient().cancelar_assinatura(assinatura.asaas_sub_id)
    conta.status = Conta.Status.CANCELADO
    conta.grace_ate = _paid_through(assinatura)   # proximo_vencimento (ou trial_ate se em trial)
    conta.save(update_fields=["status", "grace_ate"])
    assinatura.ciclo_status = Assinatura.CicloStatus.CANCELADO
    assinatura.save(update_fields=["ciclo_status"])
```

### Plano PRO seed (D-03) — data migration
```python
# apps/billing/migrations/0002_seed_plano_pro.py
from django.db import migrations
from decimal import Decimal

def seed(apps, schema_editor):
    Plano = apps.get_model("billing", "Plano")
    Plano.objects.update_or_create(
        nome="PRO",
        defaults=dict(preco_mensal=Decimal("19.90"), max_usuarios=1,
                      max_leads=None, ativo=True, ordem=0, grace_period_dias=7),
    )

def unseed(apps, schema_editor):
    apps.get_model("billing", "Plano").objects.filter(nome="PRO").delete()

class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
```

## B2B Residue (Claude's Discretion)

| Asset | File | Recommendation |
|-------|------|----------------|
| `Cupom`, `ResgateCupom` | models.py:215-395 | **Leave dormant.** No coupon UI/flow this phase. Do NOT wire into `assinar` (pass no `discount`). |
| `cupom_service` | cupom_service.py | Leave dormant. `_ativar_conta` currently calls `cupom_service.confirmar(conta)` — it is a **no-op when no resgate exists** [VERIFIED: cupom_service.py:79-86], so it is harmless. Optionally remove the call to simplify, but not required. |
| `TrialCpf` (1-trial-per-CPF) | models.py:291-322 | Leave dormant. CPF is now collected at **checkout**, not signup; trial anti-abuse is email-verification-first (Phase 1). `TrialCpf` is irrelevant to Phase 2. |
| `Conta.cupom_primeiro_ciclo_pendente` | models.py:55-58 | Default `False`; the `_ativar_conta` discount-removal branch is skipped when False [VERIFIED: services.py:252]. Harmless. |

**Recommendation:** Prune nothing structurally this phase (avoids migration churn); just don't
introduce coupon flows. If the planner wants a clean `_ativar_conta`, dropping the `cupom_service.confirmar`
call + discount branch is a safe, optional simplification.

## State of the Art

| Old (crm-voic) | Current (lazari-capital B2C) | Impact |
|----------------|------------------------------|--------|
| Signup creates Asaas customer + subscription immediately (CPF at signup) | Signup is trial-first, NO Asaas, NO CPF | Subscription creation is a NET-NEW authenticated flow (Pitfall 1) |
| Access governed by `BillingGateMiddleware` (Django routes) | Access governed by Traefik forward-auth `GateView` (Streamlit) + middleware still present for Django routes | Two gates must agree; new routes need exemption (Pitfall 2) |
| Multi-tenant CRM (many users per conta) | B2C single user per conta (`max_usuarios=1`) | Plano seed `max_usuarios=1`; `max_leads` irrelevant |

**Deprecated/irrelevant for this phase:** coupons, CPF-at-signup, per-tier plans, `max_leads`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Redirecting to the first payment's `invoiceUrl` is the correct hosted-checkout path (Asaas subscriptions have no single checkout URL) | Alternatives / Pattern 1 | If Asaas exposes a subscription-level hosted link, we'd use a suboptimal URL. Low risk — `primeira_fatura_url` already encodes this assumption and the fork used it in prod. |
| A2 | Reusing `Conta.grace_ate` as the generic "access-until" date for cancel-at-period-end is acceptable | Gate Machine / Pattern 3 | If a future feature needs to distinguish overdue-grace from cancel-paid-through, a separate field would be cleaner. Cosmetic; behavior is correct. |
| A3 | The three PAYMENT_* events already handled are sufficient; no SUBSCRIPTION_* webhook needed | Webhook Events | If a user cancels via the Asaas dashboard (not the app), we'd miss it until next payment cycle. Edge case, acceptable for MVP. |
| A4 | Setting `max_usuarios=1` on the PRO plano fits B2C | Plano seed | If multi-seat is wanted later, re-seed. No risk now. |
| A5 | `DELETE /v3/subscriptions/{id}` returns 200 with `{deleted: true}` and the client's existing 200-only success path handles it | Pitfall 7 / Code Examples | If DELETE returns 204 (no body), `_parse_resposta` (`resp.json()`) would raise. Planner should verify DELETE response code/body against sandbox and, if needed, special-case 200-no-body in `_request`. |

## Open Questions (RESOLVED)

> Todas as 4 questões foram resolvidas nos planos 02-01/02-02/02-03 (rastreabilidade).

1. **DELETE response shape** — Does Asaas sandbox return 200 (with JSON `{deleted:true}`) or 204 for
   `DELETE /subscriptions/{id}`? `_parse_resposta` requires status 200 AND valid JSON.
   - **(RESOLVED)** Tratado defensivamente em 02-02 Task 1: `_request`/`_parse_resposta` ganham um ramo no-body (`204` ou corpo vazio → `{}`) sem regredir o caminho 200+JSON; ambos os ramos têm teste. Verificar o shape real no sandbox durante a implementação.
2. **CPF validation depth** — Validate CPF format only (11 digits + check digits) at the border, or
   also CNPJ?
   - **(RESOLVED)** 02-01 Task 2: CPF-only (11 dígitos + dígitos verificadores) na borda do `CpfForm`; CNPJ fora de escopo (B2C).
3. **Where does [Assinar] live?** trial-acabou placeholder `#assinar` anchor.
   - **(RESOLVED)** 02-01 Task 3 liga o `#assinar` da trial-acabou à rota `billing-assinar`; 02-02 Task 2 também expõe [Assinar] na página de conta para usuários expirados/cancelados.
4. **Should cancelled/suspended users reach checkout to re-subscribe?**
   - **(RESOLVED)** Sim — 02-03 Task 2 adiciona `billing-assinar`/`conta`/`cancelar-assinatura` ao `EXEMPT_URL_NAMES` do `BillingGateMiddleware`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Asaas sandbox API | Dev/test of subscribe/cancel/webhook | ✓ (config) | v3 (`api-sandbox.asaas.com/v3`) | — |
| `ASAAS_API_KEY` | Any live Asaas call | ✗ locally (empty default) | — | Tests mock `AsaasClient` (see `tests/test_asaas_client.py`); no live key needed to build/test |
| `ASAAS_WEBHOOK_TOKEN` | Webhook auth | ✗ locally (empty default) | — | Tests set it; prod value is Phase 3 secret |
| Postgres | Source of truth | ✓ (project stack) | 17 | — |
| Asaas webhook registration | End-to-end paid flow | ✗ (dashboard/API, not code) | — | Register in Phase 3 (OPS-01) |

**Missing dependencies with no fallback:** None block Phase 2 *implementation* (build + unit tests run
against a mocked `AsaasClient`, following the existing `apps/billing/tests/` pattern). Live paid E2E is
explicitly Phase 3.

**Missing dependencies with fallback:** Asaas credentials → mock the client in tests (established pattern).

## Project Constraints (from CLAUDE.md)

`lazari-capital/CLAUDE.md` is the inherited **crm-voic** file (STACK confirms Django 5.2 LTS, Python
3.12, Postgres 17, HTMX 2.x, Alpine 3.x, Tailwind v4, pytest-django). Actionable directives that bind
Phase 2:
- **Multi-tenant isolation is inegociável** — a conta never sees another's data. Cancel/account views
  derive `conta` from `request.user`, never from a client-supplied id.
- **Validation only at borders** (root CLAUDE.md) — validate CPF in the form/view, not deep in services.
- **Responses in pt-BR**, comments only when the "why" isn't obvious.
- **Don't add features beyond what's asked; prefer editing existing files** — extend `apps/billing`,
  don't create parallel structures. Do NOT introduce coupons.
- **GSD workflow enforcement** — changes go through GSD commands.
- **Money fields are `DecimalField(max_digits=8, decimal_places=2)`** — never float (models.py rule);
  `AsaasClient` does `float()` only at the JSON border.

## Security Domain

`security_enforcement` not set in config → treated as **enabled**. This phase handles payment
provisioning + a public webhook + account management — a real attack surface.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Webhook: constant-time `asaas-access-token` compare (already). Checkout/account: `LoginRequiredMixin` (session from Phase 1). |
| V3 Session Management | yes | Reuse Phase 1 session hardening (HttpOnly/SameSite=Lax/parent-domain cookie). |
| V4 Access Control | yes | Cancel/account derive `conta` from `request.user.conta` — no id from client (anti-IDOR). Tenant scoping via `TenantMiddleware`. |
| V5 Input Validation | yes | Validate CPF at the form border; webhook body parsed defensively (`.get()`, 400 on non-JSON) — already. |
| V6 Cryptography | yes | No hand-rolled crypto; `hmac.compare_digest` for the token; never log `ASAAS_API_KEY`/`ASAAS_WEBHOOK_TOKEN` (client scrubs errors). |
| V7 Error/Logging | yes | Webhook never leaks `str(exc)`/stack trace in the response body; logs only `conta.pk`/path, never secrets (already). |
| V13 API/Webhook (M2M) | yes | `csrf_exempt` correct for header-authenticated M2M; 401 before any DB write; idempotent. |

### Known Threat Patterns for {Django billing + Asaas webhook}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Forged webhook call | Spoofing | Constant-time `asaas-access-token` compare → 401 before DB write (T-17-07/12) |
| Replayed webhook (duplicate effect) | Tampering | insert-and-catch on `AsaasWebhookLog.event_id` before side effects (T-17-08) |
| Cross-tenant payment applied to wrong conta | Elevation / Info-disclosure | `Assinatura.unscoped()` correlation by `asaas_sub_id`; partial-unique excludes empty ids (T-17-09) |
| IDOR on cancel (cancel someone else's sub) | Elevation | Derive subscription from `request.user.conta`, never from POST body |
| Secret leakage (API key/webhook token) | Info-disclosure | `AsaasError` never contains the key; logs scrub; never in URL/body (T-p4r-03) |
| Enumeration of unknown conta via webhook | Info-disclosure | Unknown `sub_id` → 200 identical to "processed & ignored" (T-17-10) |
| Card data touching the backend | Info-disclosure / Compliance | Hosted checkout only; backend never renders/stores PAN (D-01) |
| DoS by returning non-2xx (Asaas pauses queue) | DoS | Always 200 after logging; internal errors don't propagate (T-17-11) |

## Sources

### Primary (HIGH confidence)
- Existing code (read line-by-line): `lazari-capital/apps/billing/{asaas_client,models,views,services,cupom_service}.py`, `apps/accounts/models.py`, `apps/gate/views.py`, `apps/core/middleware/{tenant,billing_gate}.py`, `apps/core/managers.py`, `apps/billing/management/commands/processar_billing.py`, `apps/billing/forms.py`, `config/urls.py`, `config/settings/base.py`
- docs.asaas.com/reference/criar-nova-assinatura — subscription fields (customer, billingType, value, nextDueDate, cycle=MONTHLY; billingType UNDEFINED|BOLETO|CREDIT_CARD|PIX)
- docs.asaas.com/reference/criar-novo-cliente — customer: **name + cpfCnpj required**; email/mobilePhone/externalReference optional
- docs.asaas.com/reference/remover-assinatura — DELETE /v3/subscriptions/{id}: stops renewals, keeps paid, removes pending/overdue
- docs.asaas.com/docs/webhook-para-cobrancas — payment event list; event id = `id`, type = `event`
- docs.asaas.com/docs/about-webhooks — auth via `asaas-access-token` header; HTTP 200 required; queue pauses on failures

### Secondary (MEDIUM confidence)
- docs.asaas.com/changelog — webhook token complexity + auto-generation (WebSearch, official domain)

### Tertiary (LOW confidence)
- Exact DELETE response body (200+`{deleted:true}` vs 204) — not shown in docs; verify in sandbox (Open Q1 / A5)

## Metadata

**Confidence breakdown:**
- Existing code inventory: HIGH — read directly, symbols cited with file:line.
- Asaas API (create/cancel/webhook/fields): HIGH — official docs; billingType/cycle/nextDueDate/cpfCnpj/DELETE semantics all confirmed.
- Gate status machine: HIGH — derived from the actual model + service state transitions.
- DELETE response shape: LOW — verify in sandbox.

**Research date:** 2026-07-08
**Valid until:** ~2026-08-07 (Asaas API stable; existing code frozen unless Phase 2 edits it)

## RESEARCH COMPLETE
