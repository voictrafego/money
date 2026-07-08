---
phase: 01-funda-o-cadastro-login-gate-e-trial
verified: 2026-07-08T00:00:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
deferred:
  - truth: "Gate ponta-a-ponta via Traefik real (forwardAuth ativo entre serviços Docker Swarm), com Postgres em produção e teste E2E pago"
    addressed_in: "Phase 3"
    evidence: "ROADMAP.md Phase 3 goal: 'Deploy integrado (Django + gate + Streamlit) na VPS sob domínio Lazari Capital, segredos fora do git, teste E2E pago completo'; 01-04-PLAN.md e 01-05-PLAN.md dizem explicitamente 'Deploy/E2E/websockets = Fase 3'"
human_verification:
  - test: "Abrir /signup/, /entrar/, /senha/reset/, /billing/verificar/<uid>/<token>/ e /trial-acabou/ num navegador (runserver local) e conferir renderização visual real (Preline/Tailwind, marca Lazari Capital, legibilidade do checkbox de aceite legal e da data de fim do trial)"
    expected: "Telas consistentes com a marca, sem quebra de layout, checkbox de aceite e data do trial claramente visíveis"
    why_human: "Verificação de aparência visual/UX não é possível via grep/pytest — o HTML foi inspecionado estaticamente (classes Tailwind presentes, strings corretas) mas não renderizado num browser real"
  - test: "Rodar o docker stack real (money + web na mesma rede overlay) e confirmar que o Traefik forwardAuth de fato chama http://web:8000/gate/ e propaga X-User-Email para o Streamlit em produção/staging"
    expected: "GET no domínio do Streamlit sem cookie redireciona para /entrar/; com cookie válido e trial ativo, o Streamlit recebe e injeta o e-mail corretamente"
    why_human: "Explicitamente fora de escopo desta fase (Fase 3 = Go-live E2E); os testes desta fase cobrem GateView isolada (RequestFactory) e a leitura do header no app.py isolada — não a integração real Traefik↔Django↔Streamlit"
---

# Phase 1: Fundação — Cadastro, Login, Gate e Trial Verification Report

**Phase Goal:** Erguer a camada Django (repo `~/projects/lazari-capital`, espelhando o crm-voic) que governa o acesso: qualquer visitante se cadastra self-serve (email+senha), aceita os termos, ganha trial de 7 dias sem cartão, loga/desloga/redefine senha, e o gate Traefik forward-auth só libera o Streamlit para quem está autenticado E com status ativo/trial — propagando X-User-Email.
**Verified:** 2026-07-08
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Visitante cria conta email+senha, aceita Termos+Privacidade+disclaimer educacional, entra logado com trial 7 dias (data de fim clara), sem cartão | ✓ VERIFIED | `apps/billing/forms.py::SignupForm.aceite_legal` (required, texto Termos+Privacidade+disclaimer); `apps/billing/services.py::provisionar_signup`+`ativar_por_token` (Conta PENDENTE→ATIVO, trial_ate=hoje+7 só na verificação); `templates/billing/verificar_ok.html` exibe `{{ trial_ate|date:"d/m/Y" }}`; `test_signup_b2c.py` (14 testes) cobre form/serviço/views ponta a ponta; nenhum campo de cartão/CPF/Asaas no form |
| 2 | Acessar URL do Streamlit sem sessão válida é bloqueado (redireciona login) sem vazar o app; sessão autenticada+ativa entra e recebe X-User-Email confiável | ✓ VERIFIED | `apps/gate/views.py::GateView` — anônimo/sem conta → 302 login; ativo+trial futuro → 200 + header `X-User-Email`; trial expirado → 302 trial-acabou; `test_gate.py` (10 testes) cobre todos os ramos + read-only; `stack.yml` declara `forwardauth.address=http://web:8000/gate/` + `authResponseHeaders=X-User-Email` + SEM bloco `ports:`; `app.py::_current_user_email()` lê `st.context.headers.get("X-User-Email")` no boot. Integração real Traefik↔Django↔Streamlit não testada em ambiente vivo — deferido à Fase 3 (ver Human Verification) |
| 3 | Usuário loga, desloga e redefine senha por link no e-mail — self-serve completo | ✓ VERIFIED | `apps/users/urls.py` (login/logout herdados + 4 rotas nativas `PasswordReset*`, net-new); `test_auth_flows.py::test_reset_ponta_a_ponta` cobre e-mail→link→nova senha→login real; `test_login_conta_nao_verificada_recusada` confirma `is_active=False` bloqueia login; `test_reset_anti_enumeracao` confirma resposta idêntica exista ou não o e-mail |
| 4 | Dois usuários simultâneos têm contas isoladas, sem vazar estado entre sessões | ✓ VERIFIED | `User.conta` FK 1:1 (cada usuário B2C é dona de sua própria `Conta`); `User.email` unique; `apps/core/tests/test_tenant_isolation.py` (TEN-01..TEN-04) prova isolamento do `TenantManager`/thread-local herdado; sessões Django são isoladas por design (cookie de sessão por usuário). Teste "dois browsers simultâneos" real (Streamlit) não executado — natureza do `st.session_state`/cookie por conexão não foi alterada nesta fase |
| 5 | Status/trial da Conta é fonte de verdade (novo usuário = trial 7 dias) e é o campo que o gate consulta | ✓ VERIFIED | `apps/accounts/models.py::Conta.status`/`trial_ate` (únicos campos lidos); `GateView.get` lê exatamente `conta.status`/`conta.trial_ate` — nenhum outro sinal considerado; `ativar_por_token` arma `trial_ate=hoje+7` no momento da verificação (novo usuário nasce sem trial até confirmar, então ganha 7 dias) |

**Score:** 5/5 truths verified

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Gate ponta-a-ponta via Traefik real (Docker Swarm), Postgres em prod, teste E2E pago completo | Phase 3 | ROADMAP.md: "Phase 3: Go-live E2E pago — Deploy integrado (Django + gate + Streamlit) na VPS ... teste E2E pago completo"; explicitamente fora de escopo em 01-04-PLAN.md/01-05-PLAN.md ("Deploy/E2E/websockets = Fase 3") |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `~/projects/lazari-capital/apps/accounts/models.py` | `class Conta` com status/trial_ate/asaas_customer_id/grace_ate/plano | ✓ VERIFIED | Todos os campos presentes; `Status.ATIVO`/`PENDENTE_PAGAMENTO`/etc |
| `~/projects/lazari-capital/apps/users/models.py` | `User` email-USERNAME_FIELD, sem Papel B2B | ✓ VERIFIED | `USERNAME_FIELD='email'`, `username=None`, FK `conta`, sem `class Papel`/campo `papel` |
| `~/projects/lazari-capital/apps/billing/forms.py` | `SignupForm` B2C com `aceite_legal` | ✓ VERIFIED | Campo presente, required=True, sem CPF/telefone/imobiliaria/plano/cupom |
| `~/projects/lazari-capital/apps/billing/services.py` | `provisionar_signup`+`enviar_email_verificacao`+`ativar_por_token` | ✓ VERIFIED | Todas implementadas conforme especificado; `default_token_generator` usado |
| `~/projects/lazari-capital/apps/billing/views.py` | `SignupView` sem auto-login + `VerificarEmailView` | ✓ VERIFIED | `form_valid` não chama `login(`; `VerificarEmailView.get` ativa+loga só com token válido |
| `~/projects/lazari-capital/apps/users/urls.py` | Rotas password_reset/_done/_confirm/_complete | ✓ VERIFIED | 4 rotas nativas presentes com nomes corretos |
| `~/projects/lazari-capital/apps/gate/views.py` | `GateView` (GET, read-only) | ✓ VERIFIED | Implementação idêntica ao especificado no plano |
| `~/projects/lazari-capital/templates/gate/trial_acabou.html` | Página com [Assinar] placeholder | ✓ VERIFIED | Contém "Assinar", marca Lazari Capital, standalone |
| `~/projects/lazari-capital/config/settings/prod.py` | `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` | ✓ VERIFIED | Via `env(...)`, default `.lazaritechcapital.com.br`; `SAMESITE='Lax'`; `SECURE_PROXY_SSL_HEADER` preservado |
| `app.py` (analista_dividendos) | Leitura `st.context.headers['X-User-Email']` | ✓ VERIFIED | `_current_user_email()` implementada, read-only, try/except→None |
| `requirements.txt` (analista_dividendos) | `streamlit>=1.37` | ✓ VERIFIED | Presente; `.venv` já tem 1.58.0 instalado |
| `stack.yml` (analista_dividendos) | Labels forwardAuth + sem `ports:` | ✓ VERIFIED | 4 labels presentes; YAML válido; sem bloco `ports:` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `apps/users/models.py User` | `apps/accounts/models.py Conta` | FK `conta` | ✓ WIRED | `conta = models.ForeignKey('accounts.Conta', related_name='usuarios')` |
| `apps/billing/views.py SignupView.form_valid` | `apps/billing/services.py provisionar_signup`+`enviar_email_verificacao` | chamada de serviço | ✓ WIRED | Chamado dentro de `form_valid`, com tratamento de `SignupIntegrityError` |
| `apps/billing/views.py VerificarEmailView` | `apps/accounts/models.py Conta.trial_ate` | `ativar_por_token` seta `trial_ate=hoje+7` | ✓ WIRED | Testado em `test_signup_b2c.py::test_ativar_por_token_valido_arma_trial_7d` |
| `apps/gate/views.py GateView.get` | `apps/accounts/models.py Conta.status`+`trial_ate` | leitura de `request.user.conta` | ✓ WIRED | Lógica de decisão lê exatamente esses 2 campos |
| `config/urls.py` | `apps/gate/urls.py` | `include("apps.gate.urls")` | ✓ WIRED | `path("", include("apps.gate.urls"))` presente; `reverse('gate')`/`reverse('trial-acabou')` resolvem |
| `stack.yml router money middleware` | `GateView` (`/gate/`) | `forwardauth.address` | ✓ WIRED (pattern versionado) | `forwardauth.address=http://web:8000/gate/`; efetivação real (rede overlay compartilhada, deploy) é Fase 3 |
| `app.py boot` | header `X-User-Email` | `st.context.headers.get` | ✓ WIRED (isolado) | Implementado e testado via `ast.parse`/import; leitura real do header em produção depende do Traefik ativo (Fase 3) |

### Data-Flow Trace (Level 4)

Não aplicável na maior parte — esta fase é predominantemente backend Django (views/services/models), sem componentes de UI dinâmica que rendem dados de fontes assíncronas. Os pontos relevantes (trial_ate exibido em `verificar_ok.html`, X-User-Email lido no boot do `app.py`) foram verificados diretamente: `trial_ate` vem do model `Conta` (não hardcoded); `user_email` vem de `st.context.headers` (não hardcoded, com fallback `None` real).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suíte pytest do lazari-capital (Django) | `cd ~/projects/lazari-capital && pytest -q` | 200 passed | ✓ PASS |
| `manage.py check` sem erros | `cd ~/projects/lazari-capital && python manage.py check` | "System check identified no issues (2 silenced)" | ✓ PASS |
| Suíte golden do engine (analista_dividendos) | `cd analista_dividendos && python -m pytest -q` | 338 passed | ✓ PASS |
| `reverse()` das rotas de reset/gate resolvem | `python -c "... reverse('password_reset')..."` (via testes) | Todas resolvem sem NoReverseMatch | ✓ PASS |
| `stack.yml` YAML válido + sem `ports:` | `python -c "import yaml; yaml.safe_load(...)"` + grep | Válido; sem bloco `ports:` | ✓ PASS |
| Grep-gate de acoplamento B2B (leads/dashboard/integrations/Papel) | `grep -rn "apps.leads\|apps.dashboard\|apps.integrations\|provisionar_pipeline_padrao\|Papel\."` | 0 ocorrências | ✓ PASS |

### Probe Execution

Não há probes formais (`scripts/*/tests/probe-*.sh`) declarados nos planos ou summaries desta fase. SKIPPED (nenhum probe convencional/documentado encontrado).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|--------------|--------|----------|
| AUTH-01 | 01-02, 01-03 | Cadastro self-serve + login numa camada Django própria | ✓ SATISFIED | SignupForm/SignupView + LoginView + `test_auth_flows.py` |
| AUTH-02 | 01-04, 01-05 | App só acessível autenticado E trial/assinatura ativa; bloqueio sem vazar app | ✓ SATISFIED | GateView (302/200) + stack.yml forwardAuth + Streamlit sem porta pública |
| AUTH-03 | 01-05 | Identidade propagada via X-User-Email confiável | ✓ SATISFIED | `_current_user_email()` em app.py + `authResponseHeaders=X-User-Email` no stack.yml |
| AUTH-04 | 01-03 | Reset de senha self-serve por link de e-mail | ✓ SATISFIED | 4 rotas nativas `PasswordReset*` + teste ponta a ponta |
| BILL-01 | 01-01, 01-02 | Trial 7 dias sem cobrança/cartão; status fonte de verdade que o gate consulta | ✓ SATISFIED | `Conta.status`/`trial_ate`; `ativar_por_token` arma trial_ate=hoje+7; GateView lê esses campos |
| ACCT-01 | 01-01, 01-02, 01-04 | Multiusuário real — conta isolada por usuário | ✓ SATISFIED | User↔Conta FK 1:1; `test_tenant_isolation.py` prova isolamento do manager multi-tenant dormente |
| LEGAL-01 | 01-02 | Aceite de Termos+Privacidade+disclaimer educacional no cadastro | ✓ SATISFIED | `SignupForm.aceite_legal` obrigatório + texto no template `signup.html` |

Nenhum requisito órfão: os 7 IDs do frontmatter (`.planning/REQUIREMENTS.md`) aparecem distribuídos entre os 5 planos e todos têm evidência de implementação.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `~/projects/lazari-capital/apps/core/mixins.py` | 13-42 | `AdminMixin`/`AdminOuGerenteMixin` referenciam `is_admin_conta`/`can_manage_users` — atributos removidos de `User` (Task 2 do Plano 01-01) | ℹ️ Info | Dead code confirmado (nenhum import em `apps/`/`config/`/`templates/`); não é chamado por nenhuma rota, não quebra `manage.py check` nem a suíte. Se algum dia for importado, levantaria `AttributeError` em runtime — mas não afeta o objetivo desta fase. Não listado como "Known Stub" nos SUMMARYs (achado nesta verificação) |
| `~/projects/lazari-capital/apps/users/urls.py` | 1-9 | Docstring do módulo ainda descreve um bloco "2. Gestão de usuários (namespace 'usuarios')" que não existe mais nas `urlpatterns` (removido no Plano 01-01) | ℹ️ Info | Comentário desatualizado, sem efeito funcional |
| `~/projects/lazari-capital/apps/billing/views.py` | 9-13 | Docstring de `SignupView` ainda cita um "PIVÔ TRIAL" com "auto-login e redireciona DIRETO para o dashboard" — comportamento antigo do crm-voic, contradito pelo código real (`form_valid` não faz login) | ℹ️ Info | Comentário desatualizado (herdado do fork), não reflete o comportamento atual verificado por teste; não é um bug funcional |
| `~/projects/lazari-capital/templates/billing/signup.html` | 109-111 | Links `#termos`/`#privacidade` são âncoras placeholder (conteúdo legal real ainda não escrito) | ⚠️ Warning | Intencional e documentado nos SUMMARYs como "Known Stub"; o aceite em si (checkbox obrigatório + disclaimer) é funcional — mas os documentos legais reais (Termos/Privacidade) ainda não existem como páginas de conteúdo. Não bloqueia LEGAL-01 no sentido estrito (aceite na borda do form), mas é um gap de conteúdo legal real que qualquer usuário clicando nos links notaria |

Nenhum marcador de dívida não referenciado (`TODO`/`FIXME`/`XXX`/`TBD`) encontrado nos arquivos tocados por esta fase.

### Human Verification Required

1. **Renderização visual real das telas de auth/trial**
   - **Test:** Rodar `python manage.py runserver` em `~/projects/lazari-capital` e abrir no navegador `/signup/`, `/entrar/`, `/senha/reset/`, a página de verificação (`/billing/verificar/<uid>/<token>/` com um token real gerado em dev) e `/trial-acabou/`.
   - **Expected:** Layout Preline/Tailwind renderiza corretamente, marca Lazari Capital visível, checkbox de aceite legal e data de fim do trial legíveis e destacados.
   - **Why human:** Verificação de aparência/UX não é possível via grep/pytest; o HTML foi inspecionado estaticamente (classes presentes, strings corretas) mas não visualmente renderizado.

2. **Integração real Traefik → Django gate → Streamlit (E2E)**
   - **Test:** Subir o stack Docker Swarm real (money + web na mesma rede overlay) e acessar a URL pública do Streamlit sem cookie, depois com cookie de sessão válido (trial ativo) e depois com trial expirado.
   - **Expected:** Sem cookie → redireciona a `/entrar/`; com sessão ativa → app carrega e recebe `X-User-Email` real; trial expirado → redireciona a `/trial-acabou/`.
   - **Why human:** Explicitamente fora do escopo desta fase — 01-04-PLAN.md e 01-05-PLAN.md declaram que o "gate ponta-a-ponta com Traefik + websockets é escopo da Fase 3"; os testes desta fase cobrem a `GateView` isolada (RequestFactory) e a leitura do header no `app.py` isolada, não a integração viva entre os 3 serviços.

### Gaps Summary

Nenhum gap bloqueante encontrado. Todas as 5 truths do ROADMAP e os 7 requisitos (AUTH-01..04, BILL-01, ACCT-01, LEGAL-01) têm evidência de implementação real no código (não placeholders) e cobertura de teste automatizada — 200 testes verdes no repo `lazari-capital` e 338 testes verdes no `analista_dividendos` (suíte golden intacta). O único item potencialmente sensível ("gate ponta-a-ponta real via Traefik") está explicitamente fora do escopo desta fase (Phase 3 no ROADMAP) e foi tratado como item deferido, não como gap.

O status final é `human_needed` — não porque falte algo no código, mas porque (a) a aparência visual real das telas não pode ser confirmada por grep/pytest, e (b) a integração viva Traefik+Django+Streamlit está fora do escopo automatizável desta fase por design. Nenhum destes dois itens impede o avanço para a Fase 2 — são checkpoints de confirmação humana/infra, não bugs.

Achado de qualidade (não-bloqueante): `apps/core/mixins.py` (`AdminMixin`/`AdminOuGerenteMixin`) ficou como dead code referenciando atributos de `User` que foram removidos no Plano 01-01 — não é usado em lugar nenhum e não afeta o objetivo da fase, mas vale uma limpeza futura.

---

*Verified: 2026-07-08*
*Verifier: Claude (gsd-verifier)*
