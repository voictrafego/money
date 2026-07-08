---
phase: 02-cobran-a-asaas-webhooks-conta
plan: 03
subsystem: gate-billing
tags: [django, gate, forward-auth, billing-gate-middleware, webhook, idempotencia, asaas, lazari-capital]

# Dependency graph
requires:
  - "02-01: services.assinar cria Assinatura (asaas_sub_id, proximo_vencimento) e Plano PRO — o teste de ciclo prepara a Assinatura no mesmo formato; rota billing-assinar isentada"
  - "02-02: rotas accounts:conta + accounts:cancelar-assinatura, services.cancelar (seta CANCELADO + grace_ate=paid-through) — o gate agora honra CANCELADO via grace_ate; as rotas ficam isentas do middleware"
  - "01: GateView (forward-auth) + BillingGateMiddleware + _ativar_conta/_marcar_inadimplente/AsaasWebhookView (fork crm-voic hardened) — estendidos/travados, não reescritos"
provides:
  - "apps/gate/views.py::GateView — regra de 3 ramos fail-closed lendo SÓ Conta: ATIVO&(trial_ate None|>=hoje) OU INADIMPLENTE&now<=grace_ate OU CANCELADO&now<=grace_ate; senão 302 trial-acabou (BILL-04)"
  - "apps/core/middleware/billing_gate.py::EXEMPT_URL_NAMES — + billing-assinar, conta, cancelar-assinatura: contas CANCELADO/SUSPENSO alcançam conta/checkout p/ re-assinar (Pitfall 2); os dois gates concordam"
  - "apps/billing/tests/test_webhook_ciclo.py — regressão do ciclo assinar→webhook→ativação idempotente + gate (BILL-03)"
affects: [03-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "gate fail-closed de 3 ramos: pago reconhecido por trial_ate is None (bandeira de _ativar_conta), grace/paid-through por grace_ate — sem ler TenantModel no caminho do Traefik (RESEARCH Anti-Patterns)"
    - "Pitfall 3 respeitado no gate: grace_ate (DateTimeField)~timezone.now(); trial_ate (DateField)~timezone.localdate() — nunca misturar os tipos"
    - "dois gates concordantes (T-02-14): GateView (Streamlit) e BillingGateMiddleware (rotas Django) isentam as mesmas rotas de conta/checkout por url_name (sem namespace, sem prefixo de path)"
    - "regressão de infra hardened sem reescrita: AsaasWebhookView/_ativar_conta/_marcar_inadimplente só exercitados por teste de ciclo (idempotência por event_id + convergência por dueDate absoluto)"

key-files:
  created:
    - "~/projects/lazari-capital/apps/billing/tests/test_webhook_ciclo.py"
  modified:
    - "~/projects/lazari-capital/apps/gate/views.py"
    - "~/projects/lazari-capital/apps/gate/tests/test_gate.py"
    - "~/projects/lazari-capital/apps/core/middleware/billing_gate.py"
    - "~/projects/lazari-capital/apps/billing/tests/test_billing_gate.py"

key-decisions:
  - "trial_ate is None é a bandeira de 'pago' (setada por _ativar_conta): o gate libera pago por esse ramo — corrige o bug em que a regra antiga (trial_ate not None AND >=hoje) BLOQUEAVA o pagante"
  - "grace_ate reusado como 'acesso liberado até' genérico serve tanto grace de inadimplência (D-04) quanto paid-through de cancelamento (D-05) — um único ramo now<=grace_ate cobre ambos"
  - "SUSPENSO e PENDENTE_PAGAMENTO nunca liberam, mesmo com grace_ate futuro (fail-closed)"
  - "Task 3 é test-only (BILL-03): a infra de webhook já estava hardened+testada; o novo teste amarra o CICLO ponta-a-ponta (assinar→webhook→ativação→gate) e prova idempotência sem tocar view/serviço"
  - "Task 1 seguiu TDD (RED→GREEN); Tasks 2 e 3 são type=auto"

patterns-established:
  - "regra de acesso fail-closed derivada só de Conta (status/trial_ate/grace_ate), sem estado de tenant"
  - "isenção de middleware por url_name coerente entre os dois gates de acesso"

requirements-completed: [BILL-03, BILL-04]

# Metrics
duration: ~20min
completed: 2026-07-08
---

# Phase 2 Plano 03: Gate de acesso (3 ramos) + isenção de middleware + ciclo de webhook idempotente Summary

**O acesso agora honra fielmente o status de assinatura (BILL-04) e o ciclo de webhooks está travado por regressão (BILL-03). A `GateView` passou a decidir por 3 ramos lendo SÓ a `Conta`: libera quem está pago (`ATIVO` + `trial_ate=None`) ou em trial vigente, quem está no grace de inadimplência (`now<=grace_ate`, D-04) e quem cancelou dentro do paid-through (`CANCELADO` + `now<=grace_ate`, D-05); bloqueia o resto (302 `/trial-acabou/`) — corrigindo o bug central em que um PAGANTE (trial zerado por `_ativar_conta`) era bloqueado. O `BillingGateMiddleware` passou a isentar `billing-assinar`/`conta`/`cancelar-assinatura`, de modo que contas `CANCELADO`/`SUSPENSO` alcançam a página de conta e o checkout para re-assinar — os dois gates agora concordam (Pitfall 2). E um teste de ciclo ponta-a-ponta amarra `assinar→PAYMENT_CONFIRMED→ativação` provando idempotência (event_id repetido não duplica efeito) e convergência (CONFIRMED+RECEIVED não avançam o vencimento em dobro), sem reescrever a `AsaasWebhookView` nem os serviços. Verificação: 57 verdes nos 4 arquivos-alvo, 226 na suíte billing/gate/accounts, sem migrations pendentes.**

## Performance
- **Duration:** ~20 min
- **Completed:** 2026-07-08
- **Tasks:** 3 (Task 1 TDD RED→GREEN; Tasks 2 e 3 auto; Task 3 test-only)
- **Repo alvo:** `~/projects/lazari-capital` (código); `analista_dividendos` só recebe este SUMMARY + tracking
- **Files:** 1 criado + 4 modificados no repo lazari-capital

## Accomplishments
- **Task 1 (TDD) — GateView regra de 3 ramos (BILL-04):** substituída a expressão `ativo_ou_trial` por `allow` de 3 ramos (RESEARCH § Gate Status Machine): `(ATIVO and (trial_ate is None or trial_ate>=today))` OR `(INADIMPLENTE and grace_ate and now<=grace_ate)` OR `(CANCELADO and grace_ate and now<=grace_ate)`. Comparações corretas por tipo (`now=timezone.now()` p/ `grace_ate`, `today=timezone.localdate()` p/ `trial_ate` — Pitfall 3). Anônimo/conta None → 302 login; `not allow` → 302 trial-acabou; allow → 200 + `X-User-Email`. Docstring da Fase 2 atualizado. RED provou o bug do pagante (trial_ate=None bloqueado) antes do fix.
- **Task 2 — Isenção do BillingGateMiddleware (Pitfall 2):** adicionados `billing-assinar`, `conta`, `cancelar-assinatura` ao `EXEMPT_URL_NAMES` (resolvem sem prefixo de namespace). Contas `CANCELADO`/`SUSPENSO` agora passam em `/conta/`, `/conta/cancelar/` e `/billing/assinar/`; rotas não-isentas (ex.: `/dashboard/`) seguem bloqueadas (302 → conta-suspensa). Reservas existentes preservadas.
- **Task 3 (test-only) — ciclo de webhook idempotente (BILL-03):** `test_webhook_ciclo.py` exercita o ciclo real sem tocar a view/serviços: (1) conta em trial + Assinatura `asaas_sub_id=sub_000001`; (2) `PAYMENT_CONFIRMED` → 200, conta `ATIVO`+`trial_ate=None`, e o gate então libera; (3) reenvio do MESMO `event_id` → 200 "duplicado", exatamente 1 `AsaasWebhookLog`, estado idêntico (sem 2ª transição); (4) `CONFIRMED`+`RECEIVED` (event_ids distintos, mesmo `dueDate`) convergem — `proximo_vencimento` = dueDate+30d, não avança em dobro; (5) `PAYMENT_OVERDUE` → `INADIMPLENTE` + `grace_ate` armado e o gate libera durante o grace (D-04).

## Task Commits
Commits atômicos no repo `~/projects/lazari-capital`:
1. **Task 1 (RED): testes falhando do gate de 3 ramos** — `2d5e72d` (test)
2. **Task 1 (GREEN): GateView regra de 3 ramos** — `f60ebb6` (feat)
3. **Task 2: isenção conta/checkout no BillingGateMiddleware** — `f8e1580` (feat)
4. **Task 3 (test-only): trava do ciclo de webhook idempotente** — `44733d6` (test)

## Files Created/Modified
- `~/projects/lazari-capital/apps/gate/views.py` — GateView regra de 3 ramos (BILL-04)
- `~/projects/lazari-capital/apps/gate/tests/test_gate.py` — +9 casos (pago/grace/cancelado vigente-expirado/suspenso/pendente); corrigido o caso trial_ate=None (agora 200 pago)
- `~/projects/lazari-capital/apps/core/middleware/billing_gate.py` — +3 url_names no EXEMPT_URL_NAMES
- `~/projects/lazari-capital/apps/billing/tests/test_billing_gate.py` — +8 casos (conta/checkout isentos p/ CANCELADO/SUSPENSO; regressão de bloqueio de /dashboard/)
- `~/projects/lazari-capital/apps/billing/tests/test_webhook_ciclo.py` — teste de ciclo idempotente ponta-a-ponta (novo)

## Decisions Made
Ver `key-decisions` no frontmatter. Destaques: `trial_ate is None` = bandeira de pago; `grace_ate` cobre grace-de-inadimplência (D-04) e paid-through-de-cancelamento (D-05) num só ramo; SUSPENSO/PENDENTE nunca liberam; Task 3 trava a infra hardened só por teste (não reescreve).

## Verification
- `pytest apps/gate/tests/test_gate.py apps/billing/tests/test_billing_gate.py apps/billing/tests/test_webhook_ciclo.py apps/billing/tests/test_asaas_webhook_view.py` → **57 passed**.
- `pytest apps/billing apps/gate apps/accounts` → **226 passed** (sem regressão).
- `python manage.py makemigrations --check --dry-run` → **No changes detected**.
- Baseline pré-execução dos 3 arquivos tocados: **36 passed** (verde antes de começar).

## Threat Model Coverage
- **T-02-13 (Elevation, GateView):** regra de 3 ramos fail-closed — cancelado/overdue além do grace, trial expirado, SUSPENSO/PENDENTE → 302; nunca libera estado bloqueado. ✅ (testes de grace/paid-through expirado + suspenso/pendente → 302)
- **T-02-14 (Elevation, GateView vs BillingGateMiddleware):** ambos leem `Conta` e isentam as mesmas rotas de conta/checkout; sem desacordo que vaze ou trave indevidamente. ✅ (testes de CANCELADO alcançando /conta/, /billing/assinar/ + gate liberando pago)
- **T-02-15 (Spoofing, AsaasWebhookView):** auth constant-time `asaas-access-token` → 401 antes de DB write. ✅ (já travado em test_asaas_webhook_view; não regredido)
- **T-02-16 (Tampering/Replay, AsaasWebhookView):** insert-and-catch em `event_id` antes de efeito; reenvio prova zero efeito duplicado. ✅ (teste `test_reenvio_mesmo_event_id_nao_duplica_efeito`)
- **T-02-18 (DoS, AsaasWebhookView):** sempre 200 após log; erro interno não propaga. ✅ (comportamento existente preservado; não reescrito)

## Deviations from Plan
None — plano executado exatamente como escrito. A infra de webhook (AsaasWebhookView + serviços) NÃO foi reescrita; Task 3 apenas a travou por regressão, e o comportamento esperado (idempotência + convergência) bateu com os testes.

## TDD Gate Compliance
Task 1 (`tdd="true"`) seguiu RED→GREEN:
- RED: `2d5e72d` (test) — 3 falhas nos casos de liberação (pago, grace vigente, cancelado vigente) confirmadas antes do fix (o código antigo bloqueava tudo que não fosse trial).
- GREEN: `f60ebb6` (feat) — implementação; 18 testes do gate verdes.
- REFACTOR: não necessário.

## Known Stubs
Nenhum. O gate lê dados reais de `Conta`; o middleware isenta rotas reais e resolvíveis; o teste de ciclo exercita a view/serviços reais (AsaasClient não é chamado no caminho do webhook — o webhook só lê/escreve estado local).

## Issues Encountered
None.

## Next Phase Readiness
- Phase 2 (cobrança + webhooks + conta) fechada: BILL-02 (02-01), ACCT-02 (02-02), BILL-03 + BILL-04 (02-03). Pronto para a Phase 3 (deploy/OPS-01): registrar o webhook no dashboard Asaas apontando para `POST /billing/webhook/` com `ASAAS_WEBHOOK_TOKEN` forte, cabear o cron do `processar_billing`, e validar o `GateView` forward-auth × websockets do Streamlit atrás do Traefik.

## Self-Check: PASSED
- Arquivos criados/modificados verificados no repo lazari-capital.
- Commits `2d5e72d`, `f60ebb6`, `f8e1580`, `44733d6` presentes em `git log`.

---
*Phase: 02-cobran-a-asaas-webhooks-conta*
*Completed: 2026-07-08*
