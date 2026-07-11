---
phase: 02-cobran-a-asaas-webhooks-conta
plan: 01
subsystem: billing
tags: [django, asaas, checkout-hospedado, cpf, assinatura, data-migration, tdd, lazari-capital]

# Dependency graph
requires:
  - "01-02: trial de 7 dias armado na verificação de e-mail (status=ATIVO, trial_ate=hoje+7) — âncora da 1ª cobrança (D-02)"
  - "01-04: página trial-acabou (botão [Assinar] placeholder #assinar) — agora ligada ao checkout real"
  - "fork crm-voic: AsaasClient (criar_cliente/criar_assinatura/primeira_fatura_url), modelos Plano/Assinatura, transaction.atomic — reusados intactos"
provides:
  - "apps/billing/migrations/0002_seed_plano_pro: data migration idempotente (RunPython) que semeia o Plano PRO único (R$ 19,90, mensal, max_usuarios=1, grace 7d) — roda no migrate do deploy (D-03)"
  - "apps/billing/forms.py::CpfForm — borda de validação do CPF (11 dígitos + dígitos verificadores módulo-11, rejeita repetidos, normaliza; nunca ecoa o documento)"
  - "apps/billing/services.py::assinar(conta, *, cpf, email, telefone) — cria customer+subscription hospedada no Asaas, ancora a 1ª cobrança em trial_ate (D-02), update_or_create(conta) (1 por conta), persiste invoice_url"
  - "apps/billing/views.py::AssinarView (LoginRequiredMixin/FormView) + rota name=billing-assinar (/billing/assinar/): GET form CPF → POST redirect 302 ao checkout hospedado do Asaas"
  - "templates/billing/assinar.html: form de CPF sem NENHUM campo de cartão (D-01); trial-acabou.html agora aponta para billing-assinar"
affects: [02-02-cancelamento-conta, 02-03-gate-webhook-exemptions, 03-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Checkout HOSPEDADO (D-01): backend cria customer+subscription e redireciona 302 ao invoiceUrl; o PAN nunca toca o backend — nenhum campo de cartão no template"
    - "1ª cobrança ancorada em trial_ate (D-02): next_due_date = conta.trial_ate se trial vigente, senão hoje"
    - "update_or_create(conta=...) respeita UniqueConstraint(conta) — re-assinar reusa a linha (Pitfall 5), nunca cria 2ª Assinatura"
    - "Chamadas ao Asaas FORA do transaction.atomic; só o par persistência conta+assinatura é atômico"
    - "Data migration idempotente via update_or_create(nome='PRO') — migrate 2x não duplica (D-03)"
    - "Validação de CPF na borda (CpfForm), NÃO no serviço (CLAUDE.md: validar só nas bordas); mensagem de erro nunca contém o documento (T-02-02)"

key-files:
  created:
    - "~/projects/lazari-capital/apps/billing/migrations/0002_seed_plano_pro.py"
    - "~/projects/lazari-capital/apps/billing/tests/test_seed_plano_pro.py"
    - "~/projects/lazari-capital/apps/billing/tests/test_assinar_service.py"
    - "~/projects/lazari-capital/apps/billing/tests/test_assinar_view.py"
    - "~/projects/lazari-capital/templates/billing/assinar.html"
  modified:
    - "~/projects/lazari-capital/apps/billing/forms.py"
    - "~/projects/lazari-capital/apps/billing/services.py"
    - "~/projects/lazari-capital/apps/billing/views.py"
    - "~/projects/lazari-capital/apps/billing/urls.py"
    - "~/projects/lazari-capital/templates/gate/trial_acabou.html"

key-decisions:
  - "CpfForm valida CPF-only (11 dígitos + dígitos verificadores); CNPJ fora de escopo (B2C, Open Q2). Rejeita sequências repetidas (11111111111 passa na aritmética mas é inválido)"
  - "next_due_date derivado de conta.trial_ate quando trial_ate is not None AND trial_ate>=hoje; caso contrário (trial expirado ou None) → hoje (D-02, 2ª cláusula)"
  - "assinar NÃO altera Conta.status — a transição para pago/ATIVO é do webhook (Plan 03); assinar só cria customer+subscription e persiste ids/invoice_url"
  - "assinar NÃO passa discount ao criar_assinatura (sem cupom nesta fase)"
  - "invoice_url vazio ('' — Pitfall 4) é persistido como '' e a view redireciona para pagamento-pendente em vez de 302 a URL vazia"
  - "AssinarView deriva conta de request.user.conta (anti-IDOR V4); telefone via getattr(request.user,'telefone','') — nem User nem Conta têm o campo (WARNING 4)"
  - "AsaasError na view vira mensagem amigável no form, sem renderizar str(exc) (T-02-07)"
  - "Testes de serviço/view usam @pytest.mark.django_db (não transaction=True): TransactionTestCase trunca o Plano PRO semeado pela data migration"

requirements-completed: [BILL-02]

# Metrics
duration: ~20min
completed: 2026-07-08
---

# Phase 2 Plano 01: Checkout hospedado (CPF + assinatura Asaas) Summary

**O fluxo [Assinar] está no ar (BILL-02): um usuário autenticado em trial clica [Assinar], informa o CPF (o Asaas exige `cpfCnpj` para criar o customer), e o backend cria customer + subscription via `AsaasClient` (billingType `UNDEFINED`, cycle `MONTHLY`, `nextDueDate = trial_ate` per D-02) e redireciona 302 ao checkout HOSPEDADO do Asaas (`invoiceUrl`) — o produto nunca toca dados de cartão (D-01). Somado a isso: a data migration idempotente que semeia o Plano PRO único (R$ 19,90, mensal), a `CpfForm` como borda de validação (módulo-11, sem vazar o documento) e o botão [Assinar] da página trial-acabou ligado à rota real. Suíte de billing inteira verde: 170 passed (+25 desta fase), sem migrations pendentes.**

## Performance
- **Duration:** ~20 min
- **Tasks:** 3 (Task 1 auto; Task 2 TDD RED→GREEN; Task 3 auto)
- **Repo alvo:** `~/projects/lazari-capital` (código); `analista_dividendos` só recebe este SUMMARY + tracking
- **Files:** 5 criados + 5 modificados no repo lazari-capital

## Accomplishments
- **Task 1 — data migration Plano PRO (D-03):** `0002_seed_plano_pro.py` com `RunPython(seed, unseed)`, dependência em `("billing","0001_initial")`. `seed` faz `Plano.objects.update_or_create(nome="PRO", defaults=...)` com `preco_mensal=Decimal("19.90")`, `max_usuarios=1`, `max_leads=None`, `ativo=True`, `ordem=0`, `grace_period_dias=7`. Idempotente (migrate 2x não duplica). Usa `apps.get_model("billing","Plano")` — nunca o modelo real. Testes: estado pós-migrate (1 PRO com campos corretos) + idempotência (seed 2x) + unseed remove.
- **Task 2 (TDD) — CpfForm + services.assinar:** `CpfForm` valida CPF na borda (normaliza removendo pontuação, dígitos verificadores módulo-11, rejeita sequências repetidas), mensagem de erro genérica que nunca ecoa o CPF (T-02-02). `assinar(conta, *, cpf, email, telefone)`: `Plano.objects.get(nome="PRO", ativo=True)` (manager global), `criar_cliente(cpf_cnpj=cpf)`, `next_due_date` = trial_ate vigente ou hoje (D-02), `criar_assinatura` sem discount, `Assinatura.objects.update_or_create(conta=...)` (1 por conta, Pitfall 5), persiste `invoice_url` (pode vir '', Pitfall 4). Chamadas ao Asaas fora do `transaction.atomic`; par conta+assinatura atômico. NÃO altera `Conta.status` (é do webhook, Plan 03).
- **Task 3 — AssinarView + rota + template + fio do botão:** `AssinarView(LoginRequiredMixin, FormView)` com `form_class=CpfForm`, `template_name="billing/assinar.html"`. GET renderiza o form; POST válido chama `services.assinar` derivando a conta de `request.user.conta` (anti-IDOR V4) e `telefone=getattr(request.user,"telefone","")` (WARNING 4); `invoice_url` não-vazio → `redirect(invoice_url)` (302 externo), vazio → `redirect("pagamento-pendente")` (Pitfall 4); `AsaasError` → mensagem amigável no form sem vazar `str(exc)` (T-02-07). Rota `path("assinar/", …, name="billing-assinar")`. `templates/billing/assinar.html` estende `base_billing`, com o form de CPF, microcopy "software educacional, sem recomendação" e SEM qualquer campo de cartão. `trial_acabou.html`: `href="#assinar"` → `href="{% url 'billing-assinar' %}"`.

## Task Commits
Commits atômicos no repo `~/projects/lazari-capital`:
1. **Task 1: data migration semeia o Plano PRO único (D-03)** — `04b19ca` (feat)
2. **Task 2 (RED): testes falhando de CpfForm + services.assinar** — `67ec8bc` (test)
3. **Task 2 (GREEN): CpfForm (borda) + services.assinar (checkout hospedado)** — `a6987a0` (feat)
4. **Task 3: AssinarView + rota + template + fio do botão [Assinar]** — `daf9fcf` (feat)

## Verification
- `pytest apps/billing/tests/test_seed_plano_pro.py apps/billing/tests/test_assinar_service.py apps/billing/tests/test_assinar_view.py` → **25 passed**.
- `pytest apps/billing/tests/` (suíte completa, regressão) → **170 passed** (baseline era 145; +25 desta fase; nenhuma regressão no webhook/idempotência).
- `python manage.py makemigrations --check --dry-run` → **No changes detected** (sem migrations pendentes).

## Threat Model Coverage
- **T-02-01 (Tampering/Input, CpfForm):** CPF validado (11 dígitos + dígitos verificadores) antes de `criar_cliente`. ✅
- **T-02-02 (Info-disclosure, CpfForm/assinar):** mensagem de erro nunca contém o CPF; documento não é logado. ✅ (teste `test_erro_nunca_ecoa_o_cpf`)
- **T-02-03 (Info-disclosure/Compliance, HIGH):** checkout hospedado — nenhum campo de cartão no template; redirect 302 ao invoiceUrl; backend nunca monta/armazena PAN. ✅ (teste `test_com_sessao_renderiza_form_sem_cartao`)
- **T-02-04 (Elevation/IDOR):** `conta = request.user.conta`; nunca aceita conta_id/sub_id do cliente. ✅
- **T-02-05 (Tampering):** `update_or_create(conta=...)` + UniqueConstraint(conta) → re-assinar não duplica. ✅ (teste `test_reassinar_nao_cria_segunda_assinatura`)
- **T-02-06 (Spoofing):** `LoginRequiredMixin` — anônimo → 302 login. ✅ (teste `test_sem_sessao_redireciona_login`)
- **T-02-07 (Info-disclosure):** `AsaasError` na view não renderiza `str(exc)` cru. ✅ (teste `test_asaas_error_reexibe_form_sem_vazar_detalhe`)

## Deviations from Plan
None — plano executado exatamente como escrito. Único ajuste de implementação (dentro da discrição do executor): os testes de `assinar`/`AssinarView` usam `@pytest.mark.django_db` em vez de `transaction=True` porque o `TransactionTestCase` trunca o Plano PRO semeado pela data migration; a lógica testada é idêntica.

## TDD Gate Compliance
Task 2 (`tdd="true"`) seguiu RED→GREEN:
- RED: `67ec8bc` (test) — testes falhando com ImportError (CpfForm/assinar inexistentes), confirmado antes da implementação.
- GREEN: `a6987a0` (feat) — implementação mínima; 13 testes passando.
- REFACTOR: não necessário.

## Known Stubs
Nenhum. `assinar` está totalmente cabeada (Plano real via manager global, AsaasClient real em produção / mockado em teste). O único caminho "pendente" é intencional e documentado: `invoice_url == ''` (1ª fatura ainda não gerada pelo Asaas, Pitfall 4) redireciona para a página `pagamento-pendente` existente — comportamento correto, não stub.

## Self-Check: PASSED
- Arquivos criados/modificados verificados no repo lazari-capital (git status limpo pós-commit).
- Commits `04b19ca`, `67ec8bc`, `a6987a0`, `daf9fcf` presentes em `git log`.
