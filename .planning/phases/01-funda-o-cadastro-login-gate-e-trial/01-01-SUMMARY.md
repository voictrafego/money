---
phase: 01-funda-o-cadastro-login-gate-e-trial
plan: 01
subsystem: infra
tags: [django, fork-and-prune, multi-tenant, auth, sqlite, pytest, lazari-capital]

# Dependency graph
requires: []
provides:
  - "Repo git próprio novo ~/projects/lazari-capital (fork-and-prune do crm-voic, sem histórico do crm-voic)"
  - "Projeto Django que sobe verde: manage.py check + migrate + pytest (170 passed) num DB sqlite novo/vazio"
  - "User(AbstractUser) email-como-USERNAME_FIELD, sem username, sem Papel B2B; FK conta 1:1 (related_name=usuarios)"
  - "Conta com status/trial_ate/asaas_customer_id/grace_ate/plano intacta (fonte de verdade do gate)"
  - "Apps mantidos: accounts, users, billing (com AsaasWebhookLog), core (multi-tenant dormente), webhooks (shell dormente)"
  - "3 apps B2B removidos: leads, dashboard, integrations"
affects: [01-02-signup-b2c, 01-03-login-reset, 01-04-gate-trial, 02-billing-asaas, 03-deploy]

# Tech tracking
tech-stack:
  added: [django==5.2.*, psycopg[binary]==3.3.4, whitenoise, django-environ, django-ratelimit, pytest-django, factory-boy]
  patterns:
    - "Fork-and-prune sequenciado: grep de acoplamentos → cortar imports → deletar apps → reset migrations → regen 0001"
    - "User↔Conta 1:1 (B2C = cada usuário é sua própria Conta); maquinário multi-tenant dormente (D-01/D-02)"

key-files:
  created:
    - "~/projects/lazari-capital/ (repo git novo)"
    - "~/projects/lazari-capital/apps/accounts/migrations/0001_initial.py + 0002_initial.py"
    - "~/projects/lazari-capital/apps/billing/migrations/0001_initial.py"
    - "~/projects/lazari-capital/apps/users/migrations/0001_initial.py"
  modified:
    - "~/projects/lazari-capital/config/urls.py"
    - "~/projects/lazari-capital/config/settings/base.py"
    - "~/projects/lazari-capital/apps/users/{models,views,urls,forms,admin}.py"
    - "~/projects/lazari-capital/apps/billing/{services,asaas_client}.py"
    - "~/projects/lazari-capital/apps/accounts/management/commands/createconta.py"
    - "~/projects/lazari-capital/apps/webhooks/{models,urls}.py (gutado p/ shell dormente)"
    - "~/projects/lazari-capital/templates/partials/sidebar.html"

key-decisions:
  - "webhooks do crm-voic era o webhook de lead-ads do Meta (acoplado a leads), NÃO infra Asaas reusável — o webhook Asaas já vive em billing (AsaasWebhookLog + billing/views.py); app webhooks reduzido a shell dormente honrando 'apps/webhooks/ existe'"
  - "Reset total das migrations (DB novo/vazio) + regen 0001 — mais limpo que migration de remoção com FKs órfãs"
  - "sidebar.html reduzido a shell B2C mínimo (links B2B revertiam namespaces inexistentes e quebravam toda página autenticada)"

patterns-established:
  - "Grep-gate de acoplamento (apps.leads|apps.dashboard|apps.integrations|provisionar_pipeline_padrao|Papel.|avisos_limite) = 0 como prova de prune completo"
  - "Testes B2B (papel/leads/seed/rotas removidas) podados; cobertura B2C nova entra nos Planos 01-02+"

requirements-completed: [ACCT-01]

# Metrics
duration: ~55min
completed: 2026-07-08
---

# Phase 1 Plano 01: Fundação do repo lazari-capital (fork-and-prune) Summary

**Repo Django próprio novo `~/projects/lazari-capital` erguido por fork-and-prune do crm-voic: 3 apps B2B (leads/dashboard/integrations) e os papéis corretor/gerente removidos, acoplamentos cortados, migrations regeneradas do zero — sobe verde (check/migrate/pytest 170 passed) com User↔Conta 1:1 preservado (ACCT-01).**

## Performance

- **Duration:** ~55 min
- **Tasks:** 3
- **Files modified:** ~20 (source) + 4 migrations criadas; 12 arquivos de teste podados; 6 módulos B2B removidos
- **Repo alvo:** `~/projects/lazari-capital` (NÃO tocou `analista_dividendos` além do SUMMARY)

## Accomplishments
- Fork limpo de crm-voic para `~/projects/lazari-capital` (sem `.git`/`.venv`/`.env`/`db.sqlite3`/`staticfiles`/`__pycache__`), `git init` próprio — 3 commits, zero histórico/remotes do crm-voic.
- Removidos os 3 apps B2B (leads/dashboard/integrations) e todo o maquinário de papéis (Papel + helpers is_admin_conta/is_gerente/is_corretor/can_manage_users + views de gestão de usuário + ContaUserCreationForm + AdminOuGerenteMixin em uso).
- Cortadas TODAS as dependências órfãs para o projeto importar: config/urls.py, settings/base.py, billing/services.py (provisionar_pipeline_padrao), createconta, context_processors (avisos_limite), e o app webhooks (era lead-ads do Meta).
- Migrations regeneradas do zero; `migrate` limpo em sqlite novo; `makemigrations --check` sem drift; `pytest` 170 passed.
- User↔Conta 1:1 preservado (FK `conta`, related_name `usuarios`, `USERNAME_FIELD='email'`, `username=None`); Conta com status/trial_ate/asaas_customer_id/grace_ate intacta.

## Task Commits

Commits atômicos no repo NOVO `~/projects/lazari-capital`:

1. **Task 1: Fork + prune 3 apps B2B + reset migrations** - `c8e6ac8` (chore)
2. **Task 2: Cortar imports/refs órfãos** - `2f854b0` (fix)
3. **Task 3: Migrations do zero + poda de testes + rebranding** - `f26bd4c` (feat)

_SUMMARY.md + metadados: commitados separadamente no repo `analista_dividendos`._

## Files Created/Modified
Ver frontmatter `key-files`. Destaques:
- `config/urls.py` — sem includes/imports de leads/pipeline/campos/tags/dashboard/integracoes; mantém admin/health/signup/users.urls/billing/accounts/webhooks.
- `apps/users/models.py` — sem Papel/papel/helpers; mantém email USERNAME_FIELD + FK conta + deve_trocar_senha.
- `apps/billing/services.py` — sem `provisionar_pipeline_padrao` e sem `papel=Papel.ADMIN`; resto de `provisionar_signup` intacto (reescrita é do Plano 01-02).
- `apps/webhooks/{models,urls}.py` — shell dormente (o webhook Asaas vive em billing).
- `apps/*/migrations/0001*.py` — regeneradas.

## Decisions Made
- **webhooks = shell dormente, não infra Asaas.** O app webhooks do crm-voic é 100% o webhook de lead-ads do Meta (WebhookEndpoint com corretor_ids/distribuicao_tipo, importa apps.leads.importacao). O webhook de pagamento do Asaas já existe em `billing` (AsaasWebhookLog + billing/views.py + test_asaas_webhook_view.py). Mantido o diretório `apps/webhooks/` (honra o critério de aceite "webhooks existe") mas gutado para shell vazio; a Fase 2 usa o billing.
- **Reset total de migrations** em vez de migration de remoção — DB novo/vazio (D-05), sem dado a preservar.
- **Rebranding mínimo** só em `settings/base.py` (comentário MARKETING_HOSTS: pocketleads/voictech → lazaritechcapital) + `sidebar.html` (nome "Lazari Capital"); templates de marca ficam para os Planos 02/03/04 (D-13).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] App `webhooks` acoplado a `leads` — gutado para shell dormente**
- **Found during:** Task 2
- **Issue:** O plano lista `webhooks` entre os apps MANTIDOS (dormente p/ Asaas na Fase 2), mas o app webhooks do crm-voic é o webhook de lead-ads do Meta, totalmente acoplado a `apps.leads` (services importa `apps.leads.importacao.services`; views usam `AdminOuGerenteMixin`; conftest importa `apps.leads.conftest`). Mantê-lo intacto quebra o boot e reprova o grep-gate. O webhook Asaas já vive em `billing` — a premissa do plano/CONTEXT de que webhooks era infra Asaas reusável estava equivocada.
- **Fix:** Removidos services/views/forms/conftest/tests do webhooks; `models.py` esvaziado; `urls.py` com `_webhooks_urlpatterns = []`. Diretório e registro do app preservados (honra o critério de aceite "apps/webhooks/ existe").
- **Files modified:** apps/webhooks/{models,urls}.py; removidos services/views/forms/conftest/tests
- **Verification:** grep-gate=0, manage.py check OK, pytest 170 passed
- **Committed in:** `2f854b0` (Task 2)

**2. [Rule 3 - Blocking] `createconta` e `users/admin.py` referenciavam leads/papel**
- **Found during:** Task 2
- **Issue:** Fora da lista de arquivos do plano: `apps/accounts/management/commands/createconta.py` importava `apps.leads.services` e setava `papel=Papel.ADMIN`; `apps/users/admin.py` listava o campo `papel` (removido) em list_display/fieldsets → `manage.py check` falharia.
- **Fix:** Cortados o import de leads, a chamada de pipeline e `papel=` do createconta; removidas as refs a `papel` do admin.
- **Files modified:** apps/accounts/management/commands/createconta.py, apps/users/admin.py
- **Verification:** manage.py check OK
- **Committed in:** `2f854b0` (Task 2)

**3. [Rule 3 - Blocking] `sidebar.html` do shell revertia namespaces removidos**
- **Found during:** Task 3
- **Issue:** `base.html` (shell autenticado) inclui `partials/sidebar.html`, que fazia `{% url 'dashboard:dashboard' %}` / `{% url 'leads:lead_list' %}` etc. (namespaces removidos) sem guarda → NoReverseMatch em TODA página autenticada (quebrava os testes do gate `/trocar-senha/`).
- **Fix:** `sidebar.html` reduzido a shell B2C mínimo (logo "Lazari Capital" + link para /painel/ + e-mail do usuário), sem links B2B nem gate por papel. O modal de onboarding e o banner "perto do teto" já ficam guardados por condições agora falsas (não renderizam).
- **Files modified:** templates/partials/sidebar.html
- **Verification:** pytest 170 passed (testes do BillingGateMiddleware verdes)
- **Committed in:** `f26bd4c` (Task 3)

**4. [Rule 3 - Blocking] Testes B2B acoplados a papel/leads/seed/rotas removidas**
- **Found during:** Task 3
- **Issue:** Testes herdados quebravam após o prune: papel (test_models/test_views/test_seat_enforcement de users, test_onboarding/test_createconta de accounts, test_banner_perto_teto de core), rota `/dashboard/` removida (test_banner_inadimplencia), e seed de planos da migration 0002 removida (test_seed_planos_existem, test_signup_pre_seleciona_plano_por_slug).
- **Fix:** Podados esses testes + os 3 testes de signup legados (test_signup_form/service/view) conforme o plano; `apps/conftest.py` UserFactory sem `papel`. Cobertura B2C nova entra no Plano 01-02.
- **Files modified:** ver Task 3 commit
- **Verification:** pytest 170 passed
- **Committed in:** `f26bd4c` (Task 3)

**5. [Rule 3 - Blocking] `.gitignore` não cobria `dev.sqlite3`**
- **Found during:** Task 3
- **Issue:** O `.gitignore` herdado cobria `db.sqlite3`/`db_dev.sqlite3`, mas o DATABASE_URL de dev usa `dev.sqlite3` — que teria sido versionado.
- **Fix:** Adicionado `*.sqlite3` ao `.gitignore`.
- **Files modified:** .gitignore
- **Verification:** `git check-ignore dev.sqlite3` OK; nenhum sqlite/.env/.venv staged
- **Committed in:** `f26bd4c` (Task 3)

---

**Total deviations:** 5 auto-fixed (todas Rule 3 - blocking)
**Impact on plan:** Todas necessárias para o projeto subir verde e passar o grep-gate. Sem scope creep — o único item além da letra do plano (gutar webhooks) corrige uma premissa equivocada do plano (webhooks ≠ infra Asaas). Escopo Fase 2 (Asaas/webhooks) e templates de marca (D-13) intocados.

## Issues Encountered
- **Ambiente Python 3.14.5** (venv local): Django 5.2.16 instalou e rodou sem incidentes; suíte verde.
- **`.env` ausente** (excluído por segurança T-01-01): criado `.env` local gitignorado só para dev/test (SECRET_KEY throwaway, sqlite), fora do git.

## Known Stubs
- `apps/webhooks/` é um shell dormente intencional (sem modelos/rotas). Resolvido conforme necessidade na Fase 2 (o webhook Asaas efetivo está em `billing`). Não bloqueia o objetivo do plano.
- `apps/billing/services.py::provisionar_signup` ainda é o serviço B2B do crm-voic (CPF/Asaas/cupom/trial 30d) — importável, mas reescrito para B2C no Plano 01-02 (conforme o plano).

## Threat Flags
Nenhuma superfície de segurança nova introduzida. As mitigações do threat model (T-01-01 exclusão de segredos, T-01-02 remoção de papéis, T-01-03 reset de migrations, T-01-04 boot sem import órfão) foram todas aplicadas e verificadas.

## Self-Check: PASSED
- `~/projects/lazari-capital/.git` existe; 3 commits; sem remotes do crm-voic. FOUND
- `apps/accounts/migrations/0001_initial.py`, `apps/users/migrations/0001_initial.py`, `apps/billing/migrations/0001_initial.py` FOUND
- Commits `c8e6ac8`, `2f854b0`, `f26bd4c` existem no repo lazari-capital. FOUND
- `apps/leads`/`apps/dashboard`/`apps/integrations` ausentes; `apps/{accounts,users,billing,webhooks,core}` presentes. FOUND
- grep-gate=0; manage.py check OK; migrate limpo; pytest 170 passed. VERIFIED

## Next Phase Readiness
- Base pronta para o Plano 01-02 (signup B2C verificação-first: reescrever `provisionar_signup` sem CPF/Asaas/pipeline, trial 7d na verificação de e-mail) e 01-03/01-04 (login/reset, GateView + trial).
- Nota p/ Fase 2: webhook Asaas usa `apps/billing` (AsaasWebhookLog + billing/views.py), não o app webhooks (shell dormente).

---
*Phase: 01-funda-o-cadastro-login-gate-e-trial*
*Completed: 2026-07-08*
