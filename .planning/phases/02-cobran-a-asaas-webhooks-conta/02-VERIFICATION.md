---
phase: 02-cobran-a-asaas-webhooks-conta
verified: 2026-07-08T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 2: Cobrança Asaas + Webhooks + Conta Verification Report

**Phase Goal:** Transformar o trial em receita: assinatura mensal via checkout HOSPEDADO Asaas (sem PCI no backend), webhooks nativos idempotentes atualizando o status da conta, página de conta (ver/cancelar), e o acesso (gate) honrando fielmente o status de assinatura. Requisitos: BILL-02, BILL-03, BILL-04, ACCT-02.

**Verified:** 2026-07-08
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria, Phase 2)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Usuário em trial assina o plano mensal via checkout hospedado do Asaas (cliente+assinatura) e retorna com assinatura ativa, sem o produto manusear cartão | ✓ VERIFIED | `apps/billing/services.py::assinar()` (linhas 210-282) chama `AsaasClient().criar_cliente`/`criar_assinatura`, persiste `invoice_url`; `AssinarView.form_valid` (`apps/billing/views.py:173-194`) faz `redirect(assinatura.invoice_url)` (302 externo). `grep -in "card\|cartao\|cartão\|number\|cvv" templates/billing/assinar.html` — 0 campos de cartão (só menção textual "NENHUM campo de cartão"). Testes: `test_assinar_service.py`, `test_assinar_view.py` verdes. |
| 2 | Pagamento confirmado dispara webhook que ativa a assinatura; falta de pagamento/cancelamento atualiza para inadimplente/cancelada, de forma idempotente | ✓ VERIFIED | `apps/billing/views.py::AsaasWebhookView` — insert-and-catch atômico em `AsaasWebhookLog.event_id` (unique=True no model, `apps/billing/models.py:167-171`) ANTES de qualquer efeito; dispatch `PAYMENT_CONFIRMED/RECEIVED → _ativar_conta`, `PAYMENT_OVERDUE → _marcar_inadimplente` (`services.py:341-459`). Teste de regressão ponta-a-ponta em `test_webhook_ciclo.py`: `test_reenvio_mesmo_event_id_nao_duplica_efeito` prova 1 log + estado idêntico após 2 POSTs; `test_confirmed_e_received_convergem_sem_avancar_vencimento_em_dobro` prova convergência por `dueDate` absoluto (sem duplicar +30d). |
| 3 | O gate libera enquanto trial OU assinatura estiver ativa e bloqueia após inadimplência/cancelamento, passado o período devido | ✓ VERIFIED | `apps/gate/views.py::GateView.get` (linhas 38-58) implementa a regra de 3 ramos lendo só `Conta`: `ATIVO & (trial_ate None|>=hoje)` OR `INADIMPLENTE & now<=grace_ate` OR `CANCELADO & now<=grace_ate`; fail-closed no resto. Testes em `apps/gate/tests/test_gate.py` cobrem pago (trial_ate=None), grace vigente/expirado, cancelado vigente/expirado, suspenso/pendente. `BillingGateMiddleware.EXEMPT_URL_NAMES` (`apps/core/middleware/billing_gate.py:43-45`) isenta `billing-assinar`/`conta`/`cancelar-assinatura` — contas bloqueadas ainda alcançam conta/checkout para re-assinar (testado em `test_billing_gate.py`). |
| 4 | Página de conta mostra status, link de cobrança do Asaas e permite cancelar, sem expor dados sensíveis de pagamento | ✓ VERIFIED | `apps/accounts/views.py::ContaView` expõe só `conta.status`, `assinatura.proximo_vencimento`, `assinatura.invoice_url`, `pode_cancelar`. `templates/accounts/conta.html` renderiza `invoice_url` e form POST para `accounts:cancelar-assinatura`; `grep -in "card\|cartao\|cartão\|cvv" templates/accounts/conta.html` → 0 ocorrências. `CancelarAssinaturaView.post` deriva `conta` só de `request.user.conta` (anti-IDOR) e valida cancelabilidade server-side antes de chamar `services.cancelar`. Cancelamento chama `AsaasClient.cancelar_assinatura` (DELETE) e só transiciona local (`CANCELADO` + `grace_ate=paid-through`) após sucesso do DELETE (D-05). |

**Score:** 4/4 truths (roadmap) + 5/5 must-haves de plano (checkout hospedado, sem cartão, 1ª cobrança em trial_ate, re-assinar não duplica, webhook idempotente) verificados.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `apps/billing/migrations/0002_seed_plano_pro.py` | Data migration idempotente do Plano PRO | ✓ VERIFIED | `RunPython(seed, unseed)`, `update_or_create(nome="PRO", preco_mensal=Decimal("19.90"), max_usuarios=1, grace_period_dias=7)`. `makemigrations --check --dry-run billing` → "No changes detected". |
| `apps/billing/forms.py::CpfForm` | Validação de CPF na borda | ✓ VERIFIED | `clean_cpf` normaliza + valida dígitos verificadores; mensagem genérica nunca ecoa o CPF. |
| `apps/billing/services.py::assinar` | Checkout hospedado + 1ª cobrança em trial_ate + update_or_create | ✓ VERIFIED | `next_due = conta.trial_ate if trial_vigente else hoje`; `Assinatura.objects.update_or_create(conta=conta, ...)`. |
| `apps/billing/services.py::cancelar` | Cancel-at-period-end via DELETE Asaas | ✓ VERIFIED | DELETE fora do atomic; transição local só após sucesso; `grace_ate` = paid-through (trial_ate ou proximo_vencimento) convertido para datetime aware. |
| `apps/billing/asaas_client.py::cancelar_assinatura` | DELETE /subscriptions/{id} com tratamento 204 | ✓ VERIFIED | `_request('delete', ...)`; `_parse_resposta` trata 204/corpo vazio → `{}`. |
| `apps/billing/views.py::AssinarView` | GET form CPF / POST redirect ao checkout | ✓ VERIFIED | `LoginRequiredMixin`, `form_class=CpfForm`, redirect a `invoice_url` ou `pagamento-pendente`. |
| `apps/accounts/views.py::ContaView` / `CancelarAssinaturaView` | Ver/cancelar assinatura sem dado de cartão | ✓ VERIFIED | Ambas `LoginRequiredMixin`; conta derivada de `request.user.conta`; sem lookup por id do cliente. |
| `apps/gate/views.py::GateView` | Regra de 3 ramos (BILL-04) | ✓ VERIFIED | Implementado exatamente como especificado; lê só `Conta`. |
| `apps/core/middleware/billing_gate.py::EXEMPT_URL_NAMES` | Isenção das rotas de conta/checkout | ✓ VERIFIED | Contém `billing-assinar`, `conta`, `cancelar-assinatura`. |
| `apps/billing/tests/test_webhook_ciclo.py` | Regressão do ciclo idempotente | ✓ VERIFIED | 5 testes (confirmed/reenvio/convergência/overdue/ciclo completo) todos passando. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `AssinarView` | `services.assinar` | POST válido | WIRED | `services.assinar(conta, cpf=..., email=..., telefone=...)` chamado no `form_valid`. |
| `services.assinar` | `AsaasClient` | criar_cliente/criar_assinatura/primeira_fatura_url | WIRED | Chamadas reais, fora do `transaction.atomic`. |
| `templates/gate/trial_acabou.html` | `billing-assinar` | botão [Assinar] | WIRED | `href="{% url 'billing-assinar' %}"` confirmado (linha 20). |
| `CancelarAssinaturaView` | `services.cancelar` | POST autenticado | WIRED | Chamado após validação server-side de cancelabilidade. |
| `services.cancelar` | `AsaasClient.cancelar_assinatura` | DELETE | WIRED | Chamado antes da transição de estado local. |
| `templates/accounts/conta.html` | `Assinatura.invoice_url` | link de cobrança | WIRED | `{% if assinatura.invoice_url %}` + `<a href="{{ assinatura.invoice_url }}">`. |
| `GateView` | `Conta.status/trial_ate/grace_ate` | decisão fail-closed | WIRED | Regra de 3 ramos lê exclusivamente esses 3 campos. |
| `BillingGateMiddleware::EXEMPT_URL_NAMES` | rotas de conta/checkout | isenção por url_name | WIRED | Testado em `test_billing_gate.py` (CANCELADO alcança `/conta/`, `/conta/cancelar/`, `/billing/assinar/`; `/dashboard/` continua bloqueado). |
| `AsaasWebhookView` | `_ativar_conta`/`_marcar_inadimplente` | dispatch por event_type | WIRED | Correlacionado por `asaas_sub_id`; travado por `test_webhook_ciclo.py`. |

### Behavioral Spot-Checks / Test Suite Execution

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suíte completa da fase (billing+gate+accounts) | `cd ~/projects/lazari-capital && .venv/bin/python -m pytest apps/billing apps/gate apps/accounts -q` | **226 passed**, 0 failed (8.79s) | ✓ PASS |
| Sem migrations pendentes | `.venv/bin/python manage.py makemigrations --check --dry-run billing` | "No changes detected in app 'billing'" | ✓ PASS |
| Sem dado de cartão em `assinar.html` | `grep -in "card\|cartao\|cartão\|number\|cvv" templates/billing/assinar.html` | Só texto explicativo "NENHUM campo de cartão" — nenhum input | ✓ PASS |
| Sem dado de cartão em `conta.html` | `grep -in "card\|cartao\|cartão\|cvv" templates/accounts/conta.html` | 0 ocorrências | ✓ PASS |
| Idempotência do webhook (unique constraint real) | `grep -n "unique=True" apps/billing/models.py` (AsaasWebhookLog.event_id) | `event_id` é `unique=True, db_index=True` | ✓ PASS |
| Commits da fase presentes | `git log --oneline` no repo lazari-capital | 11 commits `02-01`/`02-02`/`02-03` presentes, working tree limpo | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| BILL-02 | 02-01 | Checkout hospedado Asaas, sem manuseio de cartão | ✓ SATISFIED | `services.assinar` + `AssinarView` + template sem cartão; testes verdes |
| BILL-03 | 02-03 | Webhooks nativos idempotentes atualizando status | ✓ SATISFIED | `AsaasWebhookView` + `test_webhook_ciclo.py` (idempotência + convergência provadas) |
| BILL-04 | 02-03 | Gate lê trial-OU-ativa; bloqueia pós-graça/cancelamento | ✓ SATISFIED | `GateView` 3 ramos + `test_gate.py` |
| ACCT-02 | 02-02 | Página de conta: status/link/cancelar, sem dado sensível | ✓ SATISFIED | `ContaView`/`CancelarAssinaturaView`/`conta.html` + testes; grep de termos de cartão = 0 |

Nenhum requisito órfão: `.planning/REQUIREMENTS.md` mapeia exatamente BILL-02/03/04 e ACCT-02 para a Phase 2, e todos os 4 aparecem no campo `requirements:` de algum plano (02-01/02-02/02-03).

### Anti-Patterns Found

Nenhum bloqueador. Varredura de TODO/FIXME/XXX/HACK/PLACEHOLDER/"not implemented" nos 13 arquivos-chave modificados na fase (`services.py`, `views.py` de billing/accounts/gate, `asaas_client.py`, `billing_gate.py`, migrations, templates) não retornou nenhuma ocorrência real (um falso-positivo do grep casou a substring "TODO" dentro da palavra portuguesa "TODOS" em um comentário de `gate/views.py` — não é um marcador de débito).

`Known Stubs` de todas as 3 SUMMARYs declaram "Nenhum" e a inspeção de código confirma: nenhum handler vazio, nenhum `return None`/`{}`/`[]` estático em caminho de dado real, nenhum `console.log`/`print` substituindo lógica.

### Human Verification Required

Nenhum item. A fase é essencialmente backend/plumbing (formulários, serviços, webhook, gate) coberta por testes automatizados substantivos que exercitam o ciclo completo (assinar → webhook → gate → cancelar). A validação visual/E2E ao vivo do checkout Asaas real (sandbox/produção) está explicitamente fora do escopo desta fase — é a Phase 3 ("Go-live E2E pago") conforme o próprio ROADMAP.md e a seção `<deferred>` do 02-CONTEXT.md.

### Gaps Summary

Nenhum gap encontrado. Todas as truths do ROADMAP (SC1-SC4) e todos os must-haves de frontmatter dos 3 planos (02-01/02-02/02-03) foram verificados diretamente no código-fonte do repo `~/projects/lazari-capital` (não apenas nas SUMMARYs) — checkout hospedado sem cartão, âncora da 1ª cobrança em `trial_ate`, `update_or_create` evitando 2ª Assinatura, DELETE de cancelamento com paid-through, gate de 3 ramos fail-closed, isenção de middleware coerente com o gate do Traefik, e idempotência de webhook comprovada por teste de regressão de ciclo completo. A suíte de 226 testes (billing+gate+accounts) passa integralmente e não há migrations pendentes.

---

*Verified: 2026-07-08*
*Verifier: Claude (gsd-verifier)*
