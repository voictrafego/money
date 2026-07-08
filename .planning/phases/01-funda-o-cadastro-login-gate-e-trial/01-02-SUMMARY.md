---
phase: 01-funda-o-cadastro-login-gate-e-trial
plan: 02
subsystem: auth
tags: [django, signup, b2c, email-verification, trial, anti-enumeration, lazari-capital]

# Dependency graph
requires:
  - "01-01: repo lazari-capital (fork-and-prune), User↔Conta 1:1, Conta.status/trial_ate, SignupForm/SignupView/provisionar_signup B2B importáveis"
provides:
  - "SignupForm B2C: email + first_name (Nome) + password1/2 + aceite_legal obrigatório; sem CPF/telefone/imobiliária/plano/cupom; validate_unique no-op (anti-enumeração)"
  - "provisionar_signup(*, nome, email, senha): Conta PENDENTE_PAGAMENTO + trial_ate=None + User is_active=False, sem auto-login"
  - "enviar_email_verificacao(user): link assinado /billing/verificar/<uid>/<token>/ via default_token_generator, best-effort"
  - "ativar_por_token(uidb64, token): check_token válido → is_active=True, status=ATIVO, trial_ate=hoje+7; inválido → None"
  - "SignupView (sem auto-login) + VerificacaoEnviadaView + VerificarEmailView + rotas verificar-email/verificacao-enviada"
  - "Templates Lazari Capital: signup (aceite+disclaimer), verificacao_enviada, verificar_ok (data-fim do trial), verificar_invalido, e-mail de verificação"
  - "EMAIL_BACKEND=console em dev (D-08)"
affects: [01-03-login-reset, 01-04-gate-trial, 02-billing-asaas]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Verificação-first: signup cria conta pendente sem trial; trial de 7d só arma na confirmação do e-mail (default_token_generator nativo, sem lib externa)"
    - "Anti-enumeração preservada: validate_unique no-op + SignupIntegrityError → mensagem genérica na view"
    - "E-mail best-effort: falha de SMTP loga só user.pk (nunca str(exc)) e não bloqueia a resposta"

key-files:
  created:
    - "~/projects/lazari-capital/apps/billing/tests/test_signup_b2c.py"
    - "~/projects/lazari-capital/templates/billing/email/verificacao_subject.txt"
    - "~/projects/lazari-capital/templates/billing/email/verificacao_corpo.txt"
    - "~/projects/lazari-capital/templates/billing/verificacao_enviada.html"
    - "~/projects/lazari-capital/templates/billing/verificar_ok.html"
    - "~/projects/lazari-capital/templates/billing/verificar_invalido.html"
  modified:
    - "~/projects/lazari-capital/apps/billing/forms.py"
    - "~/projects/lazari-capital/apps/billing/services.py"
    - "~/projects/lazari-capital/apps/billing/views.py"
    - "~/projects/lazari-capital/apps/billing/urls.py"
    - "~/projects/lazari-capital/templates/billing/signup.html"
    - "~/projects/lazari-capital/config/settings/dev.py"

key-decisions:
  - "TrialJaUsadoError + enviar_email_boas_vindas ficaram como dead code (Fase 2/webhook) — não removidos para não expandir escopo além dos arquivos do plano; AsaasClient/Assinatura/cupom_service permanecem importados em services.py porque _ativar_conta/_marcar_inadimplente (webhook Asaas Fase 2) ainda os usam"
  - "Links Termos/Privacidade no signup.html são âncoras placeholder (#termos/#privacidade) — intencional nesta fase (conteúdo legal entra depois); o texto do disclaimer educacional é definitivo"
  - "trial_ate renderizado com |date:'d/m/Y' no verificar_ok.html — formato estável e testável (evita fragilidade de L10N)"

requirements-completed: [AUTH-01, LEGAL-01, BILL-01, ACCT-01]

# Metrics
duration: ~11min
completed: 2026-07-08
---

# Phase 1 Plano 02: Cadastro self-serve B2C verificação-first Summary

**O signup B2B do crm-voic virou um cadastro self-serve B2C do Lazari Capital: o visitante informa nome+e-mail+senha e aceita Termos/Privacidade/disclaimer; a conta nasce PENDENTE sem trial e sem login, dispara um e-mail de verificação assinado, e só ao clicar o link o usuário é ativado, o trial de 7 dias é armado (status=ATIVO, trial_ate=hoje+7) e o login acontece — cobrindo AUTH-01, LEGAL-01, BILL-01 e ACCT-01, com a suíte inteira de billing verde (145 passed).**

## Performance
- **Duration:** ~11 min
- **Tasks:** 3 (todas TDD: RED → GREEN)
- **Repo alvo:** `~/projects/lazari-capital` (código); `analista_dividendos` só recebe este SUMMARY
- **Files:** 6 criados + 6 modificados no repo lazari-capital

## Accomplishments
- **SignupForm B2C** (Task 1): campos email + first_name (label "Nome") + password1/2 + `aceite_legal` (BooleanField required). Removidos cpf_cnpj/telefone/nome_imobiliaria/plano/cupom e os validadores mod-11 (`_valida_cpf`/`_valida_cnpj`/`clean_cpf_cnpj`). `validate_unique` mantido como no-op deliberado (anti-enumeração, T-01-08). `signup.html` reescrito com marca Lazari Capital, checkbox de aceite legal (links Termos/Privacidade) e disclaimer "software educacional, sem recomendação".
- **provisionar_signup B2C** (Task 2): `provisionar_signup(*, nome, email, senha)` cria `Conta(status=PENDENTE_PAGAMENTO)` (trial_ate=None) + `User(is_active=False, first_name=nome, conta=conta)` num único `transaction.atomic()`, sem auto-login; e-mail duplicado → `SignupIntegrityError`. `enviar_email_verificacao(user)` monta uid/token nativos e envia o link best-effort (loga só user.pk). `ativar_por_token(uidb64, token)`: token válido → is_active=True, status=ATIVO, trial_ate=hoje+7; inválido/adulterado → None sem alterar nada. `EMAIL_BACKEND=console` em dev (D-08).
- **Views + rotas + confirmação** (Task 3): `SignupView.form_valid` sem auto-login (provisiona, dispara e-mail, redireciona para `verificacao-enviada`); `@ratelimit 5/h` e o 429 mantidos. `VerificarEmailView` (GET read-only) ativa via token, faz login e renderiza `verificar_ok.html` com a data-fim do trial (SC1); token inválido → `verificar_invalido.html`. Rotas `verificacao-enviada/` e `verificar/<uidb64>/<token>/` (name=verificar-email).
- **Testes**: `test_signup_b2c.py` cobre form (5), serviço (5) e views (4) — POST /signup/ retorna 302 sem autenticar a sessão + outbox=1, rate-limit 429 na 6ª tentativa, verificação válida (login + trial_ate exibido) e inválida. Testes legados de signup (form/service/view) confirmados ausentes (aposentados no 01-01).

## Task Commits
Commits atômicos no repo NOVO `~/projects/lazari-capital`:
1. **Task 1: SignupForm B2C + template Lazari Capital** — `5623d58` (feat)
2. **Task 2: provisionar_signup verificação-first + e-mail + ativar_por_token** — `ffa81b7` (feat)
3. **Task 3: SignupView sem auto-login + VerificarEmailView + rotas + confirmação trial 7d** — `05106bf` (feat)

_SUMMARY.md commitado separadamente no repo `analista_dividendos`._

## TDD Gate Compliance
Cada task seguiu RED → GREEN explicitamente (teste falhando confirmado antes de implementar, depois verde). Por consistência com o padrão do Plano 01-01 (um commit atômico por task) e com a estrutura de 3 tasks do plano, cada task foi um único commit `feat` contendo teste + implementação, em vez de commits `test`/`feat` separados. Não há regressão silenciosa: a suíte inteira de billing (145) e do projeto (184) fecha verde.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Imports de webhook Asaas mantidos em services.py**
- **Found during:** Task 2
- **Issue:** O plano pede remover `AsaasClient`/`Assinatura`/`cupom_service` "órfãos". Mas `_ativar_conta`/`_marcar_inadimplente` (maquinário de webhook Asaas, herdado do fork, usado pela `AsaasWebhookView`) ainda os usam — removê-los quebraria o import de views.py e a suíte.
- **Fix:** Removidos de services.py só os imports que ficaram 100% órfãos após a reescrita do signup (`hashlib`, `hmac`, `Cupom`, `ResgateCupom`, `TrialCpf`, `_hash_cpf`, `set/clear_current_conta_id`). `AsaasClient`/`Assinatura`/`cupom_service` permanecem (webhook Fase 2). O critério de aceite ("grep dentro de provisionar_signup = 0") foi atendido literalmente.
- **Verification:** `awk` do corpo de `provisionar_signup` → 0 matches; suíte verde.
- **Committed in:** `ffa81b7` (Task 2) + reword de docstring em `05106bf` (Task 3)

**2. [Rule 3 - Blocking] Dead code deixado para não estourar escopo de arquivos**
- **Found during:** Task 3
- **Issue:** Após a reescrita, `TrialJaUsadoError` (services.py) e `enviar_email_boas_vindas` (services.py + templates boas_vindas_*.txt) ficaram sem uso. Removê-los tocaria arquivos/escopo além do plano e não afeta correção.
- **Fix:** Mantidos como leftover Fase 2/webhook; views.py deixou de importá-los. Nenhum efeito em runtime.
- **Verification:** manage.py check OK; suíte 184 passed.
- **Committed in:** `05106bf` (Task 3)

**Total deviations:** 2 auto-fixed (Rule 3). Sem mudança arquitetural, sem scope creep de features.

## Known Stubs
- **Links legais placeholder:** `signup.html` aponta Termos (`#termos`) e Política de Privacidade (`#privacidade`) para âncoras vazias — **intencional nesta fase** (o disclaimer educacional em si é definitivo e o aceite é obrigatório/validado). O conteúdo das páginas legais é trabalho de fase futura (não bloqueia AUTH-01/LEGAL-01, que exigem o aceite na borda do form, já implementado).
- **Dead code Fase 2:** `TrialJaUsadoError` e `enviar_email_boas_vindas` (com templates `boas_vindas_*.txt` de marca antiga "PocketLeads") permanecem no repo, sem uso no fluxo B2C. Serão reaproveitados/removidos quando o webhook Asaas entrar (Fase 2).

## Threat Flags
Nenhuma superfície nova fora do `<threat_model>` do plano. Mitigações aplicadas e cobertas por teste: T-01-05 (is_active=False + trial só na verificação), T-01-06 (token adulterado → None, teste), T-01-07 (trial_ate só server-side em ativar_por_token), T-01-08 (validate_unique no-op + mensagem genérica), T-01-09 (@ratelimit 5/h + 429, teste), T-01-10 (e-mail best-effort loga só user.pk), T-01-11 (CSRF ativo + {% csrf_token %}).

## Self-Check: PASSED
- Arquivos criados existem: `test_signup_b2c.py`, `verificacao_subject.txt`, `verificacao_corpo.txt`, `verificacao_enviada.html`, `verificar_ok.html`, `verificar_invalido.html`. FOUND
- Commits `5623d58`, `ffa81b7`, `05106bf` existem no repo lazari-capital. FOUND
- `pytest apps/billing` = 145 passed; `pytest` (projeto) = 184 passed; `manage.py check` sem issues. VERIFIED
- Legados `test_signup_form/service/view.py` ausentes; rota `verificar-email` com `<uidb64>`/`<token>`; `form_valid` sem `login(`; grep Asaas/TrialCpf/Assinatura/cupom dentro de `provisionar_signup` = 0. VERIFIED

## Next Phase Readiness
- Pronto para 01-03 (login/logout/reset — password_reset é novo, ausente no crm-voic) e 01-04 (GateView forward-auth + página trial-acabou). `Conta.status`/`trial_ate` já são a fonte de verdade que o gate lerá; o trial de 7 dias é armado na verificação.
- Nota Fase 2: a cobrança Asaas reusa `enviar_email_boas_vindas`/`_ativar_conta`/`_marcar_inadimplente` já presentes em billing.

---
*Phase: 01-funda-o-cadastro-login-gate-e-trial*
*Completed: 2026-07-08*
