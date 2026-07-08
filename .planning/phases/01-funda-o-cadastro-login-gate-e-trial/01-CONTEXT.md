# Phase 1: Fundação — Cadastro, Login, Gate e Trial - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Erguer a **camada Django** (repo novo `~/projects/lazari-capital`, marca **Lazari Capital**)
que governa o acesso ao produto: cadastro **self-serve** (nome+email+senha), verificação de
e-mail, login/logout/reset de senha, **trial de 7 dias** modelado como fonte de verdade, e um
**gate Traefik forward-auth** que só libera o app Streamlit (o engine de valuation atual, que
fica **intacto**) para quem está autenticado **E** com trial/assinatura ativa — propagando a
identidade via header `X-User-Email`. Aceite de Termos/Privacidade/disclaimer no cadastro.

**Em escopo:** projeto Django + apps auth/conta (fork-and-prune do crm-voic), cadastro/login/
logout/reset, verificação de e-mail, modelagem de `Conta.status`/`trial_ate` (novo = trial 7d),
gate forward-auth bloqueando o Streamlit, propagação de `X-User-Email`, página "trial acabou"
placeholder, aceite legal.

**Fora de escopo (outras fases):** integração de cobrança Asaas + webhooks (Fase 2), página de
conta/cancelamento (Fase 2), deploy integrado na VPS + E2E pago (Fase 3), múltiplos planos/tiers,
OAuth, landing page de marketing.

Requisitos cobertos: AUTH-01, AUTH-02, AUTH-03, AUTH-04, BILL-01 (só modelagem de status/trial,
SEM Asaas), ACCT-01, LEGAL-01.

</domain>

<decisions>
## Implementation Decisions

### Modelo de conta / schema
- **D-01:** **Reusar o par `Conta`+`User`+`Assinatura` do crm-voic** (relação 1:1 — cada usuário
  B2C é sua própria `Conta`, um shell de assinante). O gate lê `Conta.status` e `Conta.trial_ate`,
  exatamente como já funciona no crm-voic. Isso permite copiar billing/webhooks/`asaas_client.py`
  praticamente 1:1 na Fase 2.
- **D-02:** Aceitar o custo de carregar o maquinário multi-tenant do crm-voic (thread-local
  `conta_id`, `TenantManager`) mesmo ocioso no B2C — a compatibilidade com o billing vale mais
  que a poda agora. (Não há tabelas de negócio tenant-scoped na Fase 1; o scoping fica dormente.)
- **D-03:** `Conta` já tem os campos que o gate precisa: `status` (pendente/ativo/inadimplente/
  suspenso/cancelado), `trial_ate` (DateField), `asaas_customer_id`, `grace_ate`, `plano` FK.
  Novo cadastro → `Conta` com `trial_ate = hoje + 7 dias` e status inicial de trial.

### Scaffold do repositório
- **D-04:** **Fork-and-prune do crm-voic**: copiar o repo inteiro para `~/projects/lazari-capital`
  e remover o que é B2B/CRM — apps `leads`, `dashboard`, `integrations` (kanban/import/campos
  customizados) e os papéis corretor/gerente do `User`. **Manter** `accounts`, `users`, `billing`,
  `webhooks`, `core`, e toda a base que já funciona: `config/settings/*`, Docker, Traefik, Resend
  (SMTP), pytest/factory-boy.
- **D-05:** `lazari-capital` é **repo git próprio** (novo `git init`), separado do repo do app
  Streamlit e do crm-voic. O app Streamlit (`analista_dividendos`) não é tocado nesta fase além
  de ler o header `X-User-Email`.

### Cadastro / verificação / trial
- **D-06:** Cadastro **self-serve** pede **nome + e-mail + senha + aceite legal** (Termos +
  Privacidade + disclaimer educacional). `nome` entra porque é barato e útil para o Asaas customer
  e personalização.
- **D-07:** **Verificação de e-mail obrigatória antes de liberar o trial** — cadastro envia link
  de confirmação; o acesso (e a contagem do trial) só libera após clicar. Escolha deliberada por
  segurança contra e-mails falsos, aceitando mais fricção no funil.
- **D-08:** Consequência: **Resend/SMTP fica no caminho crítico da Fase 1** (o e-mail de
  verificação bloqueia o acesso, não é só o reset de senha). Em dev, usar o console email backend
  do Django; em prod/staging, Resend como no crm-voic.
- **D-09:** Reset de senha (AUTH-04) via link por e-mail, fluxo padrão do Django (reusa a config
  do crm-voic).

### Gate / acesso
- **D-10:** **Traefik forward-auth**: o Traefik chama um endpoint Django que valida a sessão +
  `Conta.status`/`trial_ate` e responde liberar/bloquear, injetando `X-User-Email` confiável no
  Streamlit. O Streamlit **nunca** contém lógica de auth/pagamento.
- **D-11:** O Streamlit (`money`) hoje é 1 serviço atrás do Traefik em `:8501` sem auth — o gate
  é adicionado como middleware forward-auth na frente desse roteamento. Garantir que o Streamlit
  **não** fique acessível fora do Traefik (rede interna do Swarm).
- **D-12:** **Trial expirado na Fase 1:** o gate bloqueia o Streamlit e mostra uma **página Django
  "seu trial acabou"** com botão **[Assinar]** placeholder (na Fase 1 leva a aviso/lista de espera;
  na Fase 2 vira o checkout Asaas). Deixa o ponto de conversão pronto no lugar certo.

### Visual / UX
- **D-13:** Telas de entrada (cadastro/login/reset/verificação/"trial acabou") em **Preline +
  Tailwind reusando os componentes do crm-voic**, com a **marca Lazari Capital** (logo, nome,
  paleta) e o tom "software educacional, sem recomendação".

### Claude's Discretion
- Nomes de rotas/URLs, estrutura de templates, backend de e-mail em dev, organização de settings.
- Como exatamente o forward-auth endpoint é implementado (view/middleware) — dentro de D-10.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e arquitetura desta fase
- `.planning/REQUIREMENTS.md` — requisitos ativos v2.0 (AUTH/BILL/ACCT/LEGAL/OPS) + arquitetura decidida
- `.planning/ROADMAP.md` §"Phase 1" — goal + 5 critérios de sucesso
- `.planning/PROJECT.md` §"Current Milestone" / "Key Decisions" — marca Lazari Capital + gateway híbrido
- `.planning/milestones/v2.0-REQUIREMENTS.md` — requisitos originais (histórico; arquitetura Supabase/n8n foi substituída por Django/Traefik)

### Padrão a replicar — crm-voic (repo separado, fonte do fork)
- `/Users/giovanelazari/projects/crm-voic/apps/users/models.py` — `User(AbstractUser)` email-como-USERNAME_FIELD, sem username
- `/Users/giovanelazari/projects/crm-voic/apps/users/{views,urls,forms}.py` — auth (LoginView/reset/PasswordChange), `ContaUserCreationForm`, `EmailAuthenticationForm`
- `/Users/giovanelazari/projects/crm-voic/apps/accounts/models.py` — `Conta` (status/trial_ate/asaas_customer_id/grace_ate/plano) = fonte de verdade que o gate lê
- `/Users/giovanelazari/projects/crm-voic/apps/billing/models.py` — `Plano` (global) + `Assinatura` (TenantModel); referência para Fase 2
- `/Users/giovanelazari/projects/crm-voic/apps/billing/asaas_client.py` — cliente Asaas (Fase 2)
- `/Users/giovanelazari/projects/crm-voic/apps/webhooks/` — webhooks nativos idempotentes (Fase 2)
- `/Users/giovanelazari/projects/crm-voic/apps/core/` — `TenantModel`, middleware/manager multi-tenant, mixins
- `/Users/giovanelazari/projects/crm-voic/config/settings/{base,prod}.py` — settings + e-mail Resend (SMTP)
- `/Users/giovanelazari/projects/crm-voic/CLAUDE.md` — stack (Django 5.2 + HTMX + Alpine + Tailwind/Preline + Postgres) e anti-patterns multi-tenant

### App Streamlit a proteger (intacto atrás do gate)
- `/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos/stack.yml` — deploy atual (`money`, Traefik, `:8501`)
- `/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos/app.py` — engine Streamlit (usa `st.session_state`; ler `X-User-Email` será código novo, ex. `st.context.headers`)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **crm-voic `apps/users` + `apps/accounts`**: auth completo (User email-login, LoginView, reset,
  PasswordChange, `Conta` com trial/status). Base do fork-and-prune desta fase.
- **crm-voic `config/settings/prod.py`**: Resend (SMTP) já configurado — reusar para verificação
  de e-mail + reset.
- **crm-voic Docker/Traefik/pytest**: infra de projeto pronta para copiar.
- **crm-voic `ContaUserCreationForm` + signup com `trial_ate`**: já existe um fluxo de signup que
  seta o trial na `Conta` (pivô trial da Fase 15 deles) — ponto de partida direto para o cadastro.

### Established Patterns
- **Multi-tenant `conta_id`** (thread-local + `TenantManager`): presente no crm-voic; na Fase 1
  fica dormente (sem tabelas de negócio tenant-scoped), mas o `User→Conta` é mantido.
- **Streamlit `st.session_state`** para estado por sessão; o app não lê headers hoje — a
  propagação de `X-User-Email` (D-03/AUTH-03) requer código novo no boot do `app.py`.

### Integration Points
- **Gate ↔ Streamlit**: Traefik forward-auth → endpoint Django → header `X-User-Email` → `app.py`.
- **Cookie/sessão Django ↔ domínio do Streamlit**: precisam de domínio pai compartilhado para o
  gate reconhecer a sessão (detalhe de infra a resolver no research/Fase 3).

</code_context>

<specifics>
## Specific Ideas

- Marca **Lazari Capital** (domínio comprado: *Lazari Tech Capital*) presente nas telas de entrada.
- Espelhar o crm-voic o mais fielmente possível (é código testado, "vai bem"), divergindo só onde
  o B2C self-serve exige (cadastro aberto, trial, sem papéis corretor/gerente).

</specifics>

<deferred>
## Deferred Ideas

- **Cobrança Asaas + webhooks nativos + página de conta/cancelamento** → Fase 2.
- **Deploy integrado (Django + gate + Streamlit) na VPS + teste E2E pago** → Fase 3.
- **Landing page de marketing/SEO da marca Lazari Capital** → Future (pós-v2.0).
- **OAuth (Google) no login**, múltiplos planos/tiers, plano anual/cupons/afiliados → Future.
- **Poda do maquinário multi-tenant** (se o B2C nunca precisar de equipes) → reavaliar depois.

None além das acima — a discussão ficou dentro do escopo da fase.

</deferred>

---

*Phase: 1-Fundação — Cadastro, Login, Gate e Trial*
*Context gathered: 2026-07-07*
