---
phase: 01-funda-o-cadastro-login-gate-e-trial
plan: 03
subsystem: auth
tags: [django, password-reset, login, logout, anti-enumeration, self-serve, lazari-capital]

# Dependency graph
requires:
  - "01-01: repo lazari-capital (fork-and-prune), User↔Conta 1:1, LoginView + EmailAuthenticationForm, EMAIL_BACKEND console/Resend"
  - "01-02: signup B2C verificação-first (is_active=False até confirmar), templates de marca Lazari Capital"
provides:
  - "4 rotas nativas password_reset/_done/_confirm/_complete em apps/users/urls.py (net-new; ausentes no crm-voic)"
  - "5 templates registration/password_reset_*.html + password_reset_subject.txt com marca Lazari Capital"
  - "login.html rebranded (Lazari Capital) com link 'Esqueci minha senha' -> password_reset e CTA de trial 7 dias"
  - "test_auth_flows.py: login verificado, recusa is_active=False, logout, reset ponta a ponta, anti-enumeração"
affects: [01-04-gate-trial, 02-billing-asaas]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reset de senha = 4 views nativas auth_views.PasswordReset* (sem lib externa); PasswordResetView já é anti-enumeração por padrão"
    - "Templates de reset reusam billing/base_billing.html (layout auth standalone de marca) em templates/registration/"

key-files:
  created:
    - "~/projects/lazari-capital/templates/registration/password_reset_form.html"
    - "~/projects/lazari-capital/templates/registration/password_reset_done.html"
    - "~/projects/lazari-capital/templates/registration/password_reset_confirm.html"
    - "~/projects/lazari-capital/templates/registration/password_reset_complete.html"
    - "~/projects/lazari-capital/templates/registration/password_reset_email.html"
    - "~/projects/lazari-capital/templates/registration/password_reset_subject.txt"
    - "~/projects/lazari-capital/apps/users/tests/test_auth_flows.py"
  modified:
    - "~/projects/lazari-capital/apps/users/urls.py"
    - "~/projects/lazari-capital/templates/registration/login.html"
    - "~/projects/lazari-capital/apps/users/tests/test_landing.py"

key-decisions:
  - "Templates de reset estendem billing/base_billing.html (mesmo layout auth standalone das telas de verificação do 01-02) em vez de base.html (bloco auth_content) — marca Lazari Capital consistente e sem shell autenticado"
  - "PasswordResetView com success_url=reverse_lazy(password_reset_done) e email/subject templates dedicados; confirm com success_url=reverse_lazy(password_reset_complete)"
  - "e-mail de reset em .html (autoescape off) com link {% url 'password_reset_confirm' uidb64 token %} -> /senha/reset/<uidb64>/<token>/"

requirements-completed: [AUTH-04, AUTH-01]

# Metrics
duration: ~15min
completed: 2026-07-08
---

# Phase 1 Plano 03: Login/logout + reset de senha self-serve Summary

**O fluxo self-serve de sessão do Lazari Capital ficou completo: login (e-mail+senha) e logout — já herdados do fork do crm-voic — foram validados por testes, e o que o crm-voic NÃO tinha (reset de senha por e-mail, AUTH-04) entrou como as 4 views nativas `PasswordReset*` do Django com 5 templates de marca Lazari Capital, link "Esqueci minha senha" no login e cobertura pytest ponta a ponta (e-mail → link → nova senha → login) incluindo anti-enumeração — suíte inteira verde (190 passed).**

## Performance
- **Duration:** ~15 min
- **Tasks:** 2
- **Repo alvo:** `~/projects/lazari-capital` (código); `analista_dividendos` só recebe este SUMMARY
- **Files:** 7 criados + 3 modificados no repo lazari-capital

## Accomplishments
- **Task 1 — rotas + templates de reset:** adicionadas as 4 rotas nativas em `apps/users/urls.py` (`senha/reset/`, `senha/reset/enviado/`, `senha/reset/<uidb64>/<token>/`, `senha/reset/ok/`) com `PasswordResetView` apontando para templates dedicados de e-mail/assunto e `success_url` encadeando done→confirm→complete. Criados os 5 templates `registration/password_reset_*.html` + `password_reset_subject.txt` com marca Lazari Capital (reusando `billing/base_billing.html`). `login.html` rebranded (CRM VoicTech → Lazari Capital), com link "Esqueci minha senha" → `password_reset` e CTA de trial ajustado para 7 dias.
- **Task 2 — testes dos fluxos:** `apps/users/tests/test_auth_flows.py` cobre login de User verificado (autentica + redireciona a `LOGIN_REDIRECT_URL`), senha errada (não autentica), recusa de `is_active=False` (não verificado), logout (encerra sessão), reset ponta a ponta (POST reset → 1 e-mail no outbox com link uidb64/token → GET confirm → POST nova senha → login com a nova senha) e anti-enumeração (e-mail inexistente = mesmo status/redirect que existente, sem enviar e-mail).

## Task Commits
Commits atômicos no repo `~/projects/lazari-capital`:
1. **Task 1: rotas nativas de password-reset + templates Lazari Capital** — `e2fbf65` (feat)
2. **Task 2: testes login/logout/reset + anti-enumeração** — `177d462` (test)

_SUMMARY.md commitado separadamente no repo `analista_dividendos`._

## Verification
- `reverse('password_reset')` = `/senha/reset/`, `reverse('password_reset_done')` = `/senha/reset/enviado/`, `reverse('password_reset_complete')` = `/senha/reset/ok/`, `reverse('password_reset_confirm', uidb64, token)` = `/senha/reset/<uidb64>/<token>/` — todos resolvem sem NoReverseMatch.
- `pytest apps/users/tests/test_auth_flows.py` = 6 passed; suíte do projeto = **190 passed**.
- `login.html` contém `{% url 'password_reset' %}` (link "Esqueci minha senha").

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Assertion de teste com copy desatualizada "30 dias" no login**
- **Found during:** Task 2 (ao rodar a suíte completa)
- **Issue:** `apps/users/tests/test_landing.py::test_login_contem_cta_signup` afirmava `"Experimente grátis por 30 dias" in content` — copy herdada do crm-voic (trial B2B de 30 dias). O trial B2C do Lazari Capital é de **7 dias** (BILL-01/D-03, armado na verificação de e-mail no 01-02), então o CTA correto no `login.html` é "7 dias". Manter os 30 dias contradiz a regra de negócio e quebrava a suíte após o rebranding.
- **Fix:** `login.html` já corrigido para "Experimente grátis por 7 dias" (parte do rebranding D-13 da Task 1); a asserção do teste foi atualizada para "7 dias" para refletir a realidade do produto.
- **Files modified:** apps/users/tests/test_landing.py (asserção); templates/registration/login.html (copy, na Task 1)
- **Committed in:** `177d462` (Task 2)

**Total deviations:** 1 auto-fixed (Rule 1). Sem mudança arquitetural, sem scope creep de features.

## Known Stubs
Nenhum. O fluxo de reset é o padrão nativo completo do Django (form → e-mail → confirm → complete), sem placeholders. Os links legais placeholder (`#termos`/`#privacidade`) do signup são escopo do 01-02, não deste plano.

## Threat Flags
Nenhuma superfície nova fora do `<threat_model>` do plano. Mitigações aplicadas e cobertas por teste:
- **T-01-12** (session fixation): Django roda `cycle_key()` no `login()` por padrão; teste de login confirma sessão autenticada.
- **T-01-13** (replay/adulteração de token de reset): `default_token_generator` (views nativas) expira e invalida ao trocar a senha; link inválido → template `validlink=False`.
- **T-01-14** (enumeração de e-mail no reset): `PasswordResetView` responde idêntico exista ou não o e-mail; teste `test_reset_anti_enumeracao` cobre (mesmo status/redirect, sem e-mail para inexistente).
- **T-01-15** (login de conta não verificada): backend padrão do Django recusa `is_active=False`; teste `test_login_conta_nao_verificada_recusada` cobre.
- **T-01-16** (CSRF nos POSTs de login/reset): `{% csrf_token %}` presente em `login.html`, `password_reset_form.html` e `password_reset_confirm.html`; `CsrfViewMiddleware` ativo.

## Self-Check: PASSED
- Templates criados existem: `password_reset_form/done/confirm/complete.html`, `password_reset_email.html`, `password_reset_subject.txt`. FOUND
- `apps/users/tests/test_auth_flows.py` existe. FOUND
- Commits `e2fbf65` e `177d462` existem no repo lazari-capital. FOUND
- 4 rotas de reset resolvem via `reverse()`; `login.html` tem `{% url 'password_reset' %}`. VERIFIED
- `pytest` (projeto) = 190 passed. VERIFIED

## Next Phase Readiness
- Pronto para 01-04 (GateView forward-auth + página `/trial-acabou/` + `SESSION_COOKIE_DOMAIN`). O fluxo self-serve de auth (cadastro/verificação/login/logout/reset) está completo e testado; o gate lerá `Conta.status`/`trial_ate` como fonte de verdade.

---
*Phase: 01-funda-o-cadastro-login-gate-e-trial*
*Completed: 2026-07-08*
