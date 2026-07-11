# Phase 1: Fundação — Cadastro, Login, Gate e Trial - Research

**Researched:** 2026-07-07
**Domain:** Django 5.2 auth layer (fork-and-prune do crm-voic) + Traefik forward-auth gate protegendo um app Streamlit + verificação de e-mail + modelagem de trial
**Confidence:** HIGH (o caminho Django é código testado do crm-voic lido diretamente; o glue novo — Traefik forwardAuth, `st.context.headers`, password-reset, verificação de e-mail — é MEDIUM-HIGH, verificado em docs oficiais)

## Summary

A Fase 1 ergue um projeto Django novo (`~/projects/lazari-capital`) por **fork-and-prune** do `crm-voic` — um CRM Django 5.2 multi-tenant testado e em produção. A maior parte do trabalho de auth (User com email-como-USERNAME_FIELD, `Conta` com `status`/`trial_ate`, signup com trial, LoginView, hardening de sessão/CSRF, Docker/Swarm/Traefik, Resend SMTP) **já existe e é copiável quase 1:1**. O valor do research está no **glue novo que o crm-voic não tem**: (1) o **gate Traefik forward-auth** que protege o Streamlit; (2) a **estratégia de cookie de sessão em domínio-pai** para o gate reconhecer a sessão; (3) o **`st.context.headers`** no boot do Streamlit para ler `X-User-Email`; (4) a **verificação de e-mail obrigatória antes do trial** (D-07); e (5) o **reset de senha** (AUTH-04) — que, surpreendentemente, **não existe no crm-voic** (só há `password_change`, não `password_reset`).

O mecanismo central do gate: Traefik chama um endpoint Django (`forwardAuth.address`) antes de rotear para o Streamlit. Traefik **encaminha por padrão TODOS os headers da requisição original — incluindo `Cookie`** — para o endpoint de auth [VERIFIED: doc.traefik.io]. Django resolve `request.user` a partir do cookie de sessão, valida `Conta.status ∈ {ativo}` **E** `trial_ate >= hoje`, e responde **2xx (libera) com header `X-User-Email`** ou **302/401 (bloqueia)**. O Traefik promove `X-User-Email` para o request upstream via `authResponseHeaders`, e o Streamlit lê via `st.context.headers.get("X-User-Email")`. Para o browser mandar o cookie tanto para o host de login quanto para o host do app, é preciso **`SESSION_COOKIE_DOMAIN=.<domínio-pai>`**.

**Primary recommendation:** Fork-and-prune do crm-voic mantendo `accounts/users/billing/webhooks/core` intactos; implementar o gate como uma **view Django dedicada e leve** (`GateView`, GET, read-only, sem CSRF) montada num router Traefik próprio de forwardAuth; adicionar o fluxo de **verificação de e-mail** (token nativo Django) que gateia a ativação do trial, e o **password-reset nativo** (5 views built-in do Django, ausentes no crm-voic). Bump do Streamlit para `>=1.37` (mínimo para `st.context.headers`).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Cadastro self-serve + aceite legal | API/Backend (Django view/form/service) | — | Regra de negócio, cria `Conta`+`User` atomicamente; nunca no cliente |
| Verificação de e-mail | API/Backend (Django) + Email (Resend SMTP) | — | Token assinado gerado/validado no servidor; e-mail é canal de saída |
| Login/logout/reset de senha | API/Backend (Django auth views) | — | Sessão emitida pelo Django; cookie governado pelo backend |
| Modelagem de trial (`status`/`trial_ate`) | Database/Storage (Postgres via `Conta`) | API/Backend | Fonte de verdade persistida; gate só lê |
| **Gate de acesso (forward-auth)** | **API/Backend (Django GateView)** | **CDN/Proxy (Traefik)** | Traefik delega a decisão ao Django; Django é a autoridade, Traefik só encaminha/promove headers |
| Roteamento + injeção de `X-User-Email` | CDN/Proxy (Traefik middleware) | — | `authResponseHeaders` copia o header da resposta de auth para o request upstream |
| Isolamento do Streamlit | CDN/Proxy (rede interna Swarm) | Infra | Streamlit sem porta publicada; só alcançável via Traefik |
| Leitura da identidade no app | Browser/App (Streamlit `st.context`) | — | App lê o header injetado; **nunca** decide auth |

**Anti-mapeamento a evitar:** qualquer lógica de auth/pagamento dentro do Streamlit (D-10). O Streamlit é um consumidor passivo de `X-User-Email`; a autoridade é 100% Django+Traefik.

## Standard Stack

### Core (herdado do crm-voic — copiar, não reinventar)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | `5.2.*` | Framework de auth/ORM/sessão/e-mail | [VERIFIED: crm-voic/requirements.txt] — já é a base testada; auth completo built-in |
| psycopg (binary) | `3.3.4` | Driver Postgres | [VERIFIED: crm-voic/requirements.txt] |
| whitenoise | `6.12.0` | Static serving sem CDN | [VERIFIED: crm-voic/requirements.txt] |
| django-environ | `0.13.0` | `.env` → settings (segredos fora do git) | [VERIFIED: crm-voic/requirements.txt] |
| gunicorn | `23.*` | WSGI server (5 workers) | [VERIFIED: crm-voic/entrypoint.sh] |
| django-ratelimit | `4.1.0` | Rate-limit do signup (5/h por IP) | [VERIFIED: crm-voic/requirements.txt + billing/views.py] |
| django-tailwind-cli | (unpinned; binário `4.1.3`) | CSS Tailwind sem Node | [VERIFIED: crm-voic/settings/base.py] |
| PostgreSQL | `17-alpine` | Fonte de verdade de contas | [VERIFIED: crm-voic/docker-stack.yml] |

### Supporting (novo nesta fase / a confirmar)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Streamlit | `>=1.37` (bump) | Ler `X-User-Email` via `st.context.headers` | [VERIFIED: docs.streamlit.io — `st.context` chegou na 1.37, jul/2024]. Repo atual pina `streamlit>=1.30` [VERIFIED: analista_dividendos/requirements.txt] → **precisa subir para `>=1.37`** |
| Traefik | `v3.x` (na VPS) | forwardAuth middleware | [ASSUMED] a VPS já roda Traefik v3 (labels v3 no stack do `money`); confirmar versão antes de escrever labels |
| Django built-in email verification | (stdlib Django) | Token de ativação (`default_token_generator` + `urlsafe_base64`) | Verificação de e-mail (D-07) — padrão nativo, **sem lib externa** |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Django `default_token_generator` (ativação) | `django-allauth` | allauth traz signup/verificação/social prontos, mas é um framework grande que **conflita com o User/signup custom já forkado** do crm-voic; não vale a reescrita para 1 fluxo. Ficar no nativo. [ASSUMED] |
| Traefik forwardAuth → Django | `thomseddon/traefik-forward-auth` (OAuth) | Container de forward-auth pronto, mas é para OAuth/OIDC (Google etc.), não para sessão Django própria. Não serve — a autoridade é o Django. [VERIFIED: escopo] |
| Cookie de sessão em domínio-pai | Subdomínio único (app e login no mesmo host) | Host único evita `SESSION_COOKIE_DOMAIN`, mas mistura o shell Django e o Streamlit no mesmo hostname (path-based routing) — mais frágil com websockets do Streamlit. Domínio-pai é mais limpo. [ASSUMED — decisão de infra da Fase 3] |

**Installation (lazari-capital, herdado):**
```bash
# requirements.txt copiado do crm-voic (idêntico); nada novo a instalar no Django
# No repo Streamlit, bump:
#   streamlit>=1.37   (era >=1.30)
```

**Version verification:** `django==5.2.*`, `psycopg==3.3.4`, `whitenoise==6.12.0`, `django-environ==0.13.0`, `django-ratelimit==4.1.0` — todos [VERIFIED: leitura direta de crm-voic/requirements.txt em 2026-07-07]. Streamlit `st.context` [VERIFIED: docs.streamlit.io, feature da 1.37, jul/2024]. Não confirmei via `pip index` a última versão de cada (offline-first no research); as versões pinadas do crm-voic são a fonte de verdade a espelhar.

## Architecture Patterns

### System Architecture Diagram

```
                                 ┌─────────────────────────────────────────────┐
   Browser  ──── GET /app ─────▶ │              TRAEFIK (VPS, Swarm)            │
   (cookie sessionid,            │  router app.lazari...  → middleware=gate     │
    domínio-pai .lazari...)      └───────────────┬─────────────────────────────┘
        ▲                                        │ forwardAuth.address
        │                                        │ (encaminha TODOS os headers
        │ 302 → /entrar (deny)                   │  da req original: Cookie, ...)
        │ ou conteúdo do Streamlit (allow)       ▼
        │                        ┌─────────────────────────────────────────────┐
        │                        │   DJANGO GateView  (GET, read-only, no CSRF) │
        │                        │   1. resolve request.user via sessionid      │
        │                        │   2. conta = user.conta                      │
        │                        │   3. status==ativo AND trial_ate>=hoje ?     │
        │                        │        SIM → 200 + header X-User-Email        │
        │                        │        NÃO → 302 /entrar  ou  /trial-acabou   │
        │                        └───────────────┬─────────────────────────────┘
        │                                        │ 2xx + X-User-Email
        │                                        ▼
        │                        ┌─────────────────────────────────────────────┐
        │   authResponseHeaders  │  TRAEFIK promove X-User-Email → req upstream │
        │   =X-User-Email        └───────────────┬─────────────────────────────┘
        │                                        │ (rede interna Swarm; sem porta pública)
        │                                        ▼
        │                        ┌─────────────────────────────────────────────┐
        └────────────────────────│  STREAMLIT (money)                           │
                                 │  st.context.headers.get("X-User-Email")      │
                                 │  (só LÊ a identidade; nunca decide acesso)    │
                                 └─────────────────────────────────────────────┘

   Fluxo paralelo de auth (mesmo Django, host de login conta.lazari...):
   /cadastro → cria Conta(status=pendente, sem trial) + envia e-mail verificação
   /verificar/<uid>/<token> → status=ativo, trial_ate=hoje+7d, login → /app
   /entrar /sair /senha/reset (fluxo nativo Django)
```

### Recommended Project Structure (lazari-capital, pós-prune)
```
lazari-capital/
├── config/
│   ├── settings/{base,dev,prod}.py   # copiar; podar refs a apps removidos
│   ├── urls.py                       # remover includes de leads/dashboard/integrations
│   └── wsgi.py
├── apps/
│   ├── core/         # MANTER: TenantModel, middleware tenant, managers, mixins (dormente D-02)
│   ├── accounts/     # MANTER: Conta (status/trial_ate/asaas_customer_id/grace_ate/plano)
│   ├── users/        # MANTER: User(email USERNAME_FIELD); PODAR papel corretor/gerente
│   ├── billing/      # MANTER: SignupForm/SignupView/services; adaptar (sem Asaas na Fase 1)
│   ├── webhooks/     # MANTER (dormente Fase 1; ativa na Fase 2)
│   └── gate/         # NOVO: GateView forward-auth + página "trial acabou"
├── templates/registration/  # login, password_reset*, verificação (marca Lazari)
├── Dockerfile · entrypoint.sh · docker-stack.yml   # copiar; renomear crm-voic→lazari
└── requirements.txt  # idêntico ao crm-voic
```

### Pattern 1: Gate como view Django dedicada (forward-auth endpoint)
**What:** Uma view GET leve, read-only, que o Traefik chama antes de rotear ao Streamlit. Não é um middleware do Django (o middleware `BillingGateMiddleware` do crm-voic protege *rotas Django*, não o Streamlit externo).
**When to use:** Sempre — é o coração da Fase 1 (AUTH-02/AUTH-03).
**Example:**
```python
# apps/gate/views.py  [pattern novo; deriva de BillingGateMiddleware do crm-voic]
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View

from apps.accounts.models import Conta

class GateView(View):
    """Endpoint chamado pelo Traefik forwardAuth. GET, read-only, SEM CSRF
    (é GET). 2xx → libera + injeta X-User-Email; 302 → bloqueia.
    O Traefik encaminha o header Cookie da requisição original, então
    request.user resolve normalmente via SessionMiddleware."""
    http_method_names = ["get"]

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect("login")                      # → 302, Traefik devolve ao browser
        conta = user.conta
        if conta is None:
            return redirect("login")
        ativo_ou_trial = (
            conta.status == Conta.Status.ATIVO
            and conta.trial_ate is not None
            and conta.trial_ate >= timezone.localdate()
        )
        if not ativo_ou_trial:
            return redirect("trial-acabou")               # página Django D-12
        resp = HttpResponse(status=200)
        resp["X-User-Email"] = user.email                 # promovido por authResponseHeaders
        return resp
```
> Nota: o gate lê `status == ATIVO` **E** `trial_ate >= hoje`. Na Fase 1 a conta ativa em trial tem ambos; quando o trial expira, `trial_ate < hoje` bloqueia mesmo com `status=ativo` (Fase 2 adiciona assinatura paga que zera `trial_ate` e mantém `ativo`). Confirmar com o planner se a semântica de "assinatura ativa sem trial" (Fase 2) deve ser `status=ativo AND (trial_ate>=hoje OR assinatura_paga)`.

### Pattern 2: Traefik forwardAuth via labels Swarm (router do Streamlit)
**What:** Adicionar um middleware forwardAuth ao router do `money` e apontar para a `GateView`.
**Example:**
```yaml
# stack.yml do Streamlit (money) — labels no deploy.labels (provider Swarm)
- "traefik.http.middlewares.lazari-gate.forwardauth.address=http://web:8000/gate/"
- "traefik.http.middlewares.lazari-gate.forwardauth.authResponseHeaders=X-User-Email"
- "traefik.http.middlewares.lazari-gate.forwardauth.trustForwardHeader=true"
- "traefik.http.routers.money.middlewares=lazari-gate"
# money continua sem porta publicada; só a rede interna Swarm o alcança (D-11)
```
- `address` aponta para o serviço Django (`web`) **na rede overlay compartilhada** — o Django precisa estar na mesma rede Swarm que o Traefik alcança para essa chamada [VERIFIED: doc.traefik.io].
- Por padrão o Traefik **encaminha todos os headers da req original, incluindo `Cookie`** — é o que faz `request.user` resolver no gate [VERIFIED: doc.traefik.io — "If authRequestHeaders is not set, all request headers are passed"].
- `authResponseHeaders=X-User-Email` copia o header da resposta 2xx do gate para o request que segue ao Streamlit [VERIFIED: doc.traefik.io].
- Se o gate responder não-2xx (302/401), o Traefik **devolve essa resposta ao browser** — é assim que o redirect ao login/trial-acabou chega ao usuário [VERIFIED: doc.traefik.io].

### Pattern 3: Cookie de sessão em domínio-pai
**What:** Para o browser enviar `sessionid` tanto ao host de login (`conta.lazari...`) quanto ao host do app (`app.lazari...`), o cookie precisa de escopo no domínio-pai.
**Example:**
```python
# config/settings/prod.py  (adicionar ao bloco de hardening já existente)
SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN", default=".lazaritechcapital.com.br")
SESSION_COOKIE_SECURE   = True   # já existe no crm-voic
SESSION_COOKIE_HTTPONLY = True   # default Django True — garantir
SESSION_COOKIE_SAMESITE = "Lax"  # default; suficiente p/ navegação entre subdomínios do mesmo site
CSRF_COOKIE_DOMAIN = env("CSRF_COOKIE_DOMAIN", default=".lazaritechcapital.com.br")
CSRF_TRUSTED_ORIGINS = [...]      # já derivado de ALLOWED_HOSTS no crm-voic; incluir os subdomínios
```
> `SAMESITE=Lax` funciona porque login e app são **subdomínios do mesmo site** (same-site, não cross-site). Não precisa de `None`. Domínio exato = [ASSUMED] (`lazaritechcapital.com.br` inferido da memória "Lazari Tech Capital"; confirmar o domínio real comprado antes de codar).

### Pattern 4: Verificação de e-mail nativa gateando o trial (D-07)
**What:** No signup, criar `Conta` **sem** iniciar o trial (`status=pendente`, `trial_ate=None`) e enviar e-mail com link assinado. Só ao clicar o link a `Conta` vira `ativo` com `trial_ate = hoje + 7`.
**Example:**
```python
# apps/billing/services.py  (adaptação do provisionar_signup existente)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

# No signup: NÃO setar trial_ate ainda; status=PENDENTE_PAGAMENTO (ou novo PENDENTE_VERIFICACAO)
# user.is_active = False  → bloqueia login até verificar (padrão Django)
uid = urlsafe_base64_encode(force_bytes(user.pk))
token = default_token_generator.make_token(user)
link = f"https://conta.lazari.../verificar/{uid}/{token}/"
# send_mail(...) reusando o EMAIL_BACKEND (console em dev, Resend em prod)

# View de confirmação:
def verificar(request, uidb64, token):
    uid = urlsafe_base64_decode(uidb64).decode()
    user = User.objects.get(pk=uid)
    if default_token_generator.check_token(user, token):
        user.is_active = True
        conta = user.conta
        conta.status = Conta.Status.ATIVO
        conta.trial_ate = timezone.localdate() + timedelta(days=7)   # trial começa AGORA
        conta.save(update_fields=["status", "trial_ate"])
        user.save(update_fields=["is_active"])
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("app")   # já entra logado no Streamlit
```
> Diferença-chave vs. crm-voic: lá o signup nasce `ATIVO` + `trial_ate=+30d` **imediatamente** (billing/services.py:136-142) e faz auto-login direto. Aqui, D-07 exige **verificação antes do trial** — o relógio do trial só arma na confirmação. `default_token_generator` já expira o token (`PASSWORD_RESET_TIMEOUT`, default 3 dias) e o invalida se a senha mudar. **Sem lib externa.**

### Pattern 5: Password-reset nativo (AUTH-04) — NÃO existe no crm-voic
**What:** As 4 views built-in de reset do Django. O crm-voic **só tem `password_change`** (troca autenticada), **não** `password_reset` [VERIFIED: grep em crm-voic apps/ config/ — zero matches para `password_reset`/`PasswordReset`]. Portanto AUTH-04 é **código novo**, ainda que trivial.
**Example:**
```python
# apps/users/urls.py  (adicionar)
from django.contrib.auth import views as auth_views
path("senha/reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
path("senha/reset/enviado/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
path("senha/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
path("senha/reset/ok/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
# reusa o mesmo EMAIL_BACKEND (console dev / Resend prod) já configurado
```

### Anti-Patterns to Avoid
- **Lógica de auth no Streamlit:** o app **nunca** valida sessão/pagamento. Só lê `X-User-Email`. [VERIFIED: D-10]
- **Confiar em `X-User-Email` vindo do browser:** o Streamlit deve tratar o header como confiável **só porque está atrás do gate**. Se o Streamlit ficar acessível fora do Traefik, um atacante seta `X-User-Email` na mão. Mitigação: **sem porta publicada, só rede interna Swarm** (D-11). [VERIFIED: D-11]
- **Reutilizar `BillingGateMiddleware` para proteger o Streamlit:** aquele middleware protege *rotas Django*, não um serviço externo. O gate do Streamlit é uma **view** chamada pelo Traefik, não um middleware do request Django do app. [VERIFIED: leitura de billing_gate.py]
- **`startswith` para isentar rotas do gate:** o crm-voic já ensina a resolver por `url_name`, não por prefixo de path (`/billing-xpto/` casaria `/billing/`). [VERIFIED: billing_gate.py:70-78]
- **CSRF no gate:** o gate é GET read-only; não precisa (e não deve depender) de CSRF. Não confundir com o webhook (`csrf_exempt` + token) da Fase 2.
- **`SESSION_COOKIE_SAMESITE=None` sem necessidade:** login e app são same-site (subdomínios). `Lax` basta e é mais seguro. [VERIFIED: MDN/Django semantics]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token de verificação de e-mail | Gerador de token/UUID caseiro em tabela | `django.contrib.auth.tokens.default_token_generator` + `urlsafe_base64` | Assinado, com expiração (`PASSWORD_RESET_TIMEOUT`), invalida ao trocar senha; auditado |
| Reset de senha | Fluxo próprio de "esqueci a senha" | 4 views `auth_views.PasswordReset*` | Fluxo padrão, e-mail + token + confirmação prontos |
| Hash de senha | Qualquer coisa | `User.set_password` / `create_user` (PBKDF2) | Já é o padrão; o crm-voic usa `create_user` no signup |
| Sessão/login | Cookie próprio | `django.contrib.sessions` + `login()` | O gate depende do `SessionMiddleware` resolvendo `request.user` |
| Forward-auth | Proxy/nginx `auth_request` caseiro | Traefik `forwardAuth` middleware | Já é o proxy da VPS; encaminha headers/cookies e promove `authResponseHeaders` nativamente |
| Ler header no Streamlit | Parsear WSGI/tornado na mão | `st.context.headers` (Streamlit ≥1.37) | API oficial read-only, case-insensitive |
| Rate-limit de signup | Contador próprio | `django-ratelimit` (já no crm-voic, 5/h por IP) | Chave resistente a spoof de XFF já implementada (`client_ip_key`) |
| Anti-enumeração de e-mail | Mensagem "e-mail já existe" | `validate_unique` no-op + `IntegrityError` genérico (crm-voic `SignupForm`) | Já resolvido no fork; **manter** |

**Key insight:** ~85% desta fase é **copiar código testado do crm-voic**. O trabalho genuinamente novo é: (a) a `GateView` + labels Traefik, (b) mover o start do trial para a confirmação de e-mail, (c) o password-reset nativo, (d) `st.context.headers` no `app.py`, (e) `SESSION_COOKIE_DOMAIN`. Tudo o mais é prune + rebranding.

## Runtime State Inventory

> Fase de **fork/scaffold + mudança de infra** — inventário aplicável ao que muda fora do código-fonte puro.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **Nenhum dado legado a migrar** — `lazari-capital` nasce com **DB Postgres novo e vazio** (D-05, repo/git novo). Não há contas/usuários pré-existentes. | Rodar `migrate` no boot (entrypoint já faz). Nenhuma migração de dados. |
| Live service config | **Traefik router do `money`** hoje: `Host(money.voictech.com.br)` **sem auth**, porta 8501 publicada via loadbalancer [VERIFIED: analista_dividendos/stack.yml]. Precisa ganhar o middleware `forwardAuth` e o Streamlit sair de acesso público direto. | Editar `stack.yml` do Streamlit (adicionar middleware) — **efetivado na Fase 3** (deploy); na Fase 1 só se escreve o pattern. |
| OS-registered state | Nenhum (sem Task Scheduler/cron/systemd embutindo strings desta fase). | Nenhuma. |
| Secrets/env vars | Novos no `.env` de `lazari-capital`: `SECRET_KEY`, `DATABASE_URL`, `RESEND_API_KEY`, `DEFAULT_FROM_EMAIL`, `SESSION_COOKIE_DOMAIN`, `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`. Herdados do padrão crm-voic; `ASAAS_*` ficam vazios/omitidos na Fase 1. | Criar `.env` (fora do git). Confirmar conta Asaas própria só na Fase 2. |
| Build artifacts | O fork copia `staticfiles/`, `db.sqlite3`, `__pycache__`, `.venv` do crm-voic se copiado bruto. | **Podar** esses artefatos após copiar; `git init` limpo; `.gitignore` do crm-voic já cobre a maioria. |

**Verificação explícita:** nenhum datastore com string legada a renomear; a "rename" aqui é de **identidade de projeto** (crm-voic → lazari-capital, pocketleads → Lazari Capital), não de dados de runtime.

## Common Pitfalls

### Pitfall 1: Streamlit acessível fora do Traefik = spoof de identidade
**What goes wrong:** Se o serviço `money` publicar porta ou ficar em rede alcançável sem passar pelo gate, qualquer requisição pode setar `X-User-Email: vitima@x.com` e o Streamlit confia.
**Why it happens:** O modelo de confiança do forward-auth assume que **só o Traefik** injeta o header. O stack atual do `money` **publica `loadbalancer.server.port=8501`** [VERIFIED: stack.yml] — aceitável hoje (sem auth), inaceitável com o gate.
**How to avoid:** Streamlit sem porta publicada; só na rede overlay interna; o Traefik é o único ingresso (D-11). Opcional defense-in-depth: o gate/Traefik **remove** qualquer `X-User-Email` de entrada antes de reinjetar (com `authResponseHeaders`, o valor do gate substitui headers conflitantes [VERIFIED: doc.traefik.io "replaces any conflicting headers"]).
**Warning signs:** `curl` direto no IP:porta do container retorna o app; header setado manualmente é refletido.

### Pitfall 2: Cookie de sessão não chega ao gate (login não reconhecido)
**What goes wrong:** O gate sempre responde "não autenticado" e redireciona ao login em loop, mesmo logado.
**Why it happens:** (a) `SESSION_COOKIE_DOMAIN` não é o domínio-pai → o browser não manda o cookie ao host do app; ou (b) `authRequestHeaders` foi configurado e **excluiu** `Cookie`; ou (c) `SESSION_COOKIE_SECURE=True` com o gate sendo chamado em HTTP interno sem `X-Forwarded-Proto`.
**How to avoid:** `SESSION_COOKIE_DOMAIN=.<pai>`; **não** setar `authRequestHeaders` (deixar o default que passa tudo, incluindo Cookie [VERIFIED: doc.traefik.io]); manter `SECURE_PROXY_SSL_HEADER` (já no crm-voic prod.py) para o Django enxergar HTTPS atrás do Traefik.
**Warning signs:** loop de redirect login↔app; `request.user.is_anonymous` no gate apesar de sessão válida no host de login.

### Pitfall 3: Websocket do Streamlit atrás do forward-auth (relevante Fase 3, mas modelar já)
**What goes wrong:** A página carrega (HTTP inicial passa no gate) mas o Streamlit não interage / cai em loop de reconexão — o upgrade de websocket (`/_stcore/stream`) também passa pelo gate e pode ser bloqueado ou perder o header.
**Why it happens:** `st.context.headers` lê os headers da **requisição inicial** [VERIFIED: docs.streamlit.io]; o websocket é uma requisição separada que também atravessa o middleware Traefik.
**How to avoid:** Garantir que o router/middleware do Traefik cobre **todos** os paths do Streamlit (o gate deve liberar a mesma sessão no upgrade). É explicitamente um critério da **Fase 3** (ROADMAP SC-3). Na Fase 1: apenas documentar e não assumir que "página carregou" = "app funciona".
**Warning signs:** app pisca e desconecta; erros de websocket no console.

### Pitfall 4: Prune quebrando migrations/imports (fork-and-prune)
**What goes wrong:** Remover `leads`/`dashboard`/`integrations` deixa `config/urls.py`, `INSTALLED_APPS`, `TEMPLATES` context_processors, e FKs órfãs quebradas → o projeto não sobe.
**Why it happens:** Acoplamentos concretos verificados no crm-voic:
- `config/urls.py` importa `_leads_urlpatterns`, `_dashboard_urlpatterns`, `_integrations_urlpatterns`, `_campos_urlpatterns`, `_pipeline_urlpatterns`, `_tags_urlpatterns` [VERIFIED: config/urls.py].
- `billing/services.py` importa `from apps.leads.services import provisionar_pipeline_padrao` e o chama dentro de `provisionar_signup` [VERIFIED: services.py:40,155] — **quebra o signup se `leads` sumir**.
- `settings/base.py` `context_processors` inclui `apps.core.context_processors.avisos_limite` (avisos de leads/assentos) [VERIFIED: base.py:104].
- `INSTALLED_APPS` lista os 4 apps B2B [VERIFIED: base.py:61-66].
**How to avoid:** Prune **sequenciado** (ver "Fork-and-prune sequencing" abaixo); rodar `python manage.py check` e `makemigrations --check` a cada remoção; adaptar `provisionar_signup` para **não** chamar `provisionar_pipeline_padrao` (não há pipeline no B2C).
**Warning signs:** `ModuleNotFoundError: apps.leads`, `NoReverseMatch`, `ImproperlyConfigured` no boot.

### Pitfall 5: Trial iniciando cedo demais (contra D-07)
**What goes wrong:** Copiar `provisionar_signup` 1:1 faz a conta nascer `ATIVO` + `trial_ate=+30d` e auto-login **sem verificar e-mail** [VERIFIED: services.py:136-163] — viola D-07 (verificação antes do trial) e D-03 (7 dias, não 30).
**How to avoid:** Signup cria `Conta` **pendente**, `trial_ate=None`, `user.is_active=False`, **sem auto-login**; só a view de verificação arma `trial_ate = hoje+7` e faz login. Trocar `timedelta(days=30)` → `timedelta(days=7)`.
**Warning signs:** usuário entra sem clicar no e-mail; trial de 30 dias; `trial_ate` setado no POST do signup.

### Pitfall 6: `X-Forwarded-For` e rate-limit atrás do Traefik
**What goes wrong:** Rate-limit por IP conta o IP do Traefik, não do cliente (todos batem no mesmo limite).
**Why it happens:** Atrás de proxy, `REMOTE_ADDR` é o proxy; o IP real está no **último** segmento de `X-Forwarded-For` (Traefik anexa ao final).
**How to avoid:** O crm-voic **já resolve** com `client_ip_key` (lê o último segmento do XFF) [VERIFIED: billing/views.py:62-75]. **Copiar tal qual.**
**Warning signs:** 6º signup de qualquer IP é bloqueado; um cliente bloqueia todos.

## Code Examples

### Ler `X-User-Email` no boot do Streamlit (app.py)
```python
# app.py — logo após st.set_page_config, antes de qualquer render de dados
# Requer streamlit >= 1.37 (st.context)
import streamlit as st

def _current_user_email() -> str | None:
    """Identidade injetada pelo gate Traefik (AUTH-03). Read-only.
    Fora do gate (dev local sem Traefik) retorna None — tratar como anônimo/dev."""
    try:
        return st.context.headers.get("X-User-Email")  # case-insensitive
    except Exception:
        return None

user_email = _current_user_email()
# NUNCA usar para autorizar acesso — o gate já garantiu que só quem passa chega aqui.
# Usar só para personalização / telemetria / "logado como fulano".
```
> Caveat [VERIFIED: docs.streamlit.io]: `st.context.headers` reflete os headers da **requisição inicial** da sessão. Se o gate não injetar (dev), fica `None` — planejar fallback dev.

### Signup adaptado (sem Asaas, sem pipeline, verificação-first)
```python
# Deriva de provisionar_signup mas ENXUTO para Fase 1 B2C:
# - remove: AsaasClient, Assinatura, TrialCpf (CPF opcional no B2C? — ver Open Q),
#   provisionar_pipeline_padrao, cupom
# - mantém: transaction.atomic, create_user, anti-enumeração, papel forçado
# - muda: status=PENDENTE, trial_ate=None, is_active=False, SEM auto-login
with transaction.atomic():
    conta = Conta.objects.create(nome=nome, status=Conta.Status.PENDENTE_PAGAMENTO)
    user = User.objects.create_user(
        email=email, password=senha, conta=conta,
        first_name=nome, is_active=False,   # bloqueia login até verificar (D-07)
    )
# fora do atomic: enviar e-mail de verificação (best-effort, não bloqueia resposta)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Streamlit sem acesso a headers | `st.context.headers`/`.cookies` | Streamlit 1.37 (jul/2024) | Habilita ler `X-User-Email` sem hacks de tornado [VERIFIED] |
| `STATICFILES_STORAGE` | `STORAGES` dict | Django 4.2+ | crm-voic já usa `STORAGES` (prod.py) — não regredir [VERIFIED] |
| Auth gate via nginx `auth_request` | Traefik `forwardAuth` | Traefik v2/v3 | Proxy da VPS já é Traefik; usar nativo |
| n8n para webhooks | app `webhooks` nativo Django | decisão v2.0 | Fase 2; na Fase 1 só carrega o app dormente |

**Deprecated/outdated:**
- Arquitetura Supabase + n8n dos requisitos originais (`milestones/v2.0-REQUIREMENTS.md`) — **substituída** por Django+Traefik. Ignorar. [VERIFIED: REQUIREMENTS.md nota]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Domínio é `lazaritechcapital.com.br` (inferido de "Lazari Tech Capital") | Cookie de domínio-pai | Cookie não escopa certo; ajuste trivial de env, mas bloqueia o gate se errado |
| A2 | VPS roda Traefik **v3.x** | Labels forwardAuth | Sintaxe de label muda pouco entre v2/v3, mas confirmar antes de deploy (Fase 3) |
| A3 | Django e Streamlit vão coexistir na **mesma rede overlay Swarm** para o `forwardauth.address` alcançar `web:8000` | Gate labels | Se em redes separadas, a chamada de auth falha (503) — decisão de infra da Fase 3 |
| A4 | B2C **não exige CPF/CNPJ** no signup (só nome+email+senha, D-06) → remover `TrialCpf`/validação CPF do fork | Signup adaptado | Se exigir CPF (p/ Asaas), reintroduzir campos; muda o form/serviço |
| A5 | Semântica do gate na Fase 1 = `status==ativo AND trial_ate>=hoje` | GateView | Se "assinatura paga" (Fase 2) usar `trial_ate=None`, a condição precisa `OR assinatura_ativa` — desenhar extensível já |
| A6 | `default_token_generator` (expira em `PASSWORD_RESET_TIMEOUT`=3 dias) é aceitável para link de verificação | Verificação e-mail | Se quiser expiração maior/menor p/ verificação, usar um token generator dedicado |
| A7 | Streamlit `>=1.37` sobe sem quebrar os 338 testes golden do engine | Stack | Bump de minor pode ter breaking change de API do Streamlit; rodar o app após bump |

**Estas 7 assunções precisam de confirmação do usuário no `/gsd-discuss-phase` ou pelo planner antes de virarem decisão travada** (especialmente A1, A4, A5 — afetam schema/rota/infra).

## Open Questions (RESOLVED)

1. **RESOLVED: CPF/CNPJ no signup B2C?** — Fase 1 SEM CPF (Plano 01-02 remove cpf_cnpj/telefone/plano/cupom do SignupForm e TrialCpf/AsaasClient de provisionar_signup); CPF será coletado no checkout Asaas na Fase 2.
   - What we know: crm-voic exige CPF/CNPJ (validação mod-11 + guarda `TrialCpf` anti-abuso de trial). D-06 do Lazari pede só **nome+email+senha+aceite**.
   - What's unclear: o Asaas (Fase 2) precisa de CPF/CNPJ do cliente; coletar já na Fase 1 ou só no checkout?
   - Recommendation: Fase 1 sem CPF (menos fricção, D-06); coletar no checkout Asaas (Fase 2). Remover `TrialCpf`/`_valida_cpf` do fork. Manter a guarda anti-abuso de trial por **e-mail verificado** (já que verificação é obrigatória, D-07).

2. **RESOLVED: Domínios exatos (login vs app).** — Plano 01-04 Task 3 usa `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` via env var com placeholder de domínio-pai (sem hard-block); o domínio real trava na Fase 3 (infra).
   - What we know: precisa domínio-pai compartilhado; marca "Lazari Tech Capital".
   - What's unclear: `conta.lazari...` + `app.lazari...`? ou `app.` + path? domínio real registrado.
   - Recommendation: confirmar o domínio comprado e definir 2 subdomínios same-site (login e app) sob o mesmo pai. Decisão de infra que trava na Fase 3 mas o cookie/settings dependem dela já.

3. **RESOLVED: Onde mora a `GateView`?** — no serviço `web` do Django (Plano 01-04: endpoint `/gate/` no app `apps/gate`); o forwardauth.address do Plano 01-05 aponta para `http://web:8000/gate/`.
   - What we know: precisa estar na rede que o Traefik alcança; é read-only e barato.
   - What's unclear: reaproveitar o gunicorn principal (5 workers) ou um endpoint isolado.
   - Recommendation: mesmo serviço `web` (endpoint `/gate/`); é 1 query indexada por request, custo desprezível. Reavaliar só se virar gargalo.

4. **RESOLVED: Página "trial acabou" (D-12).** — Plano 01-04 Task 2 serve `/trial-acabou/` como rota Django pública standalone (fora do endpoint `/gate/`, sem loop), com botão [Assinar] placeholder.
   - What we know: o gate responde 302 → Traefik devolve ao browser. A rota precisa ser servida pelo Django **sem passar pelo próprio gate** (senão loop).
   - Recommendation: rota Django pública (`/trial-acabou/`) no host de login (conta.lazari...), fora do middleware do Streamlit. Botão [Assinar] = placeholder (link para lista de espera na Fase 1).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Traefik (VPS) | Gate forwardAuth | ✓ (roda o `money` hoje) | v3.x [ASSUMED] | — (é a única via de ingresso) |
| Docker Swarm (VPS) | Deploy do stack | ✓ | — | — |
| PostgreSQL 17 | Fonte de verdade | ✓ (padrão crm-voic) | 17-alpine | — |
| Resend SMTP | Verificação de e-mail (D-08) | ✓ (chave no crm-voic prod) | — | Console backend em dev [VERIFIED: dev usa default console/locmem] |
| Streamlit ≥1.37 | `st.context.headers` | ✗ (repo pina `>=1.30`) | precisa bump | Sem fallback — 1.30 não tem `st.context`; bump obrigatório |

**Missing dependencies with no fallback:**
- Streamlit `>=1.37` no repo do app (bump de `requirements.txt` do `analista_dividendos`). Sem isso, `st.context.headers` inexiste e AUTH-03 não fecha.

**Missing dependencies with fallback:**
- Resend em dev: usar `EMAIL_BACKEND=console` (Django imprime o link de verificação no stdout) — já é o comportamento default do crm-voic em dev [VERIFIED].

## Validation Architecture

> `nyquist_validation: false` na config — seção incluída em modo leve (só seams naturais para gates posteriores), conforme pedido no output.

O crm-voic usa **pytest + factory-boy** (copiar o setup). Seams de validação naturais desta fase, mapeados aos success criteria da ROADMAP:

| Success Criterion | Seam de validação | Tipo |
|-------------------|-------------------|------|
| SC1 (signup+aceite+trial 7d) | Teste da view/serviço: POST cria `Conta` pendente + e-mail enviado; verificação arma `trial_ate=hoje+7` e `status=ativo` | unit/integration (Django test client) |
| SC2 (gate bloqueia/libera + `X-User-Email`) | Teste da `GateView`: anônimo→302; ativo+trial→200 com header; trial expirado→302 trial-acabou | unit (RequestFactory) |
| SC3 (login/logout/reset self-serve) | Teste dos fluxos `auth_views` + `PasswordReset*` (e-mail em `mail.outbox`) | integration |
| SC4 (2 usuários isolados) | Teste de 2 sessões: `X-User-Email` correto por sessão; `st.session_state` não vaza | integration (Django) + smoke manual (Streamlit) |
| SC5 (`status`/`trial_ate` fonte de verdade) | Teste de modelo: `Conta.trial_ate` DateField; gate lê exatamente esse campo | unit |

**Observabilidade:** o gate é um ponto natural de log de acesso (allow/deny por e-mail) — útil como seam de auditoria para as Fases 2/3. Não construir dashboard agora; só logar decisão + motivo (sem PII sensível além do e-mail já em trânsito).

**Wave 0 (infra de teste a portar do crm-voic):** `conftest.py` + factories de `Conta`/`User`; framework pytest-django. Se o fork copiar `apps/conftest.py` e os `tests/` dos apps mantidos, a base já existe — podar os testes de leads/dashboard/integrations.

## Security Domain

> `security_enforcement` não está `false` na config → habilitado. ASVS **Level 1** (conforme objetivo).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | **sim** | Django auth (PBKDF2, `AUTH_PASSWORD_VALIDATORS` já no base.py); verificação de e-mail obrigatória (D-07) |
| V3 Session Management | **sim** | `django.contrib.sessions`; `SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE=Lax`; `SESSION_COOKIE_DOMAIN` no pai; rotação de sessão no login (Django faz por padrão) |
| V4 Access Control | **sim** | `GateView` server-side (fail-closed: default nega); Streamlit isolado na rede interna; `authResponseHeaders` substitui `X-User-Email` de entrada |
| V5 Input Validation | **sim** | Forms Django (borda); anti-enumeração de e-mail (`validate_unique` no-op do crm-voic); `redirect` só a rotas nomeadas |
| V6 Cryptography | parcial | `default_token_generator` (HMAC assinado) p/ verificação e reset; TLS termina no Traefik; **nunca** hand-roll de token |
| V7 Errors/Logging | **sim** | Logar decisão do gate + falhas de e-mail **sem** vazar credenciais (crm-voic já loga só `conta.pk`, nunca `str(exc)` de SMTP/Asaas) |
| V11 Business Logic | **sim** | Rate-limit de signup 5/h por IP (`client_ip_key` resistente a XFF spoof); trial não inicia sem verificação |

### Known Threat Patterns (auth + gate)

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Acesso direto ao Streamlit contornando o gate | Elevation of Privilege / Spoofing | Streamlit **sem porta publicada**, só rede interna Swarm (D-11); Traefik único ingresso |
| Spoof de `X-User-Email` de fora | Spoofing | Gate/Traefik **substitui** header conflitante via `authResponseHeaders`; app confia só porque isolado [VERIFIED: doc.traefik.io] |
| Cookie de sessão roubado/hijack | Spoofing / Information Disclosure | `Secure`+`HttpOnly`+`SameSite=Lax`; HSTS (já no prod.py); TLS obrigatório |
| Session fixation | Spoofing | Django roda `cycle_key()` no login por padrão — não desabilitar |
| Bypass de verificação de e-mail | Elevation of Privilege | `is_active=False` até confirmar; trial só arma na view de verificação; token assinado com expiração |
| Enumeração de e-mail no signup/reset | Information Disclosure | `SignupForm.validate_unique` no-op + `IntegrityError` genérico (crm-voic); `PasswordResetView` do Django já é anti-enumeração (mesma resposta exista ou não) |
| Abuso de token de reset/verificação | Tampering | `default_token_generator` invalida ao trocar senha e expira (`PASSWORD_RESET_TIMEOUT`) |
| Trial-date tampering | Tampering | `trial_ate` só escrito server-side na verificação; gate read-only; nunca vem de input do cliente |
| Trial farming (múltiplos trials) | Business Logic Abuse | Verificação de e-mail obrigatória eleva o custo; (opcional) guarda por e-mail; CPF-guard do crm-voic removível (Open Q1) |
| CSRF em POSTs de auth | Tampering | `CsrfViewMiddleware` (base.py) + `CSRF_TRUSTED_ORIGINS` (prod.py); gate é GET, não exposto a CSRF |
| Brute-force de login/signup | DoS / Business Logic | `django-ratelimit` no signup (5/h); considerar rate-limit no login (não presente hoje — avaliar) |

## Project Constraints (from CLAUDE.md)

- **Idioma:** respostas e docs em **português brasileiro**. [do CLAUDE.md global]
- **Repo git dedicado:** `lazari-capital` é `git init` próprio; **não** commitar no repo `$HOME` (worktrees do GSD forkam do $HOME e quebram — usar `use_worktrees=false`). [memória + CLAUDE.md do analista]
- **GSD workflow:** edições só via comando GSD; planning artifacts sincronizados. [analista_dividendos/CLAUDE.md]
- **Testes golden do engine (338) devem continuar passando** — vivem no repo do Streamlit; a única mudança lá é o bump `streamlit>=1.37` + leitura de header. Rodar `pytest` do engine após o bump. [analista_dividendos/CLAUDE.md]
- **Segredos fora do git** (`.env`), padrão da infra compartilhada. [CLAUDE.md global]
- **Não adicionar features além do pedido; preferir editar a criar; validação só nas bordas.** [CLAUDE.md global]
- **Não criar docs extras sem pedir.** [CLAUDE.md global]

## Fork-and-prune Sequencing (D-04/D-05)

Ordem segura, verificada contra os acoplamentos reais do crm-voic:

1. **Copiar o repo inteiro** para `~/projects/lazari-capital`; **remover** `.git/`, `.venv/`, `db.sqlite3`, `staticfiles/`, `__pycache__/`; **`git init`** limpo (D-05).
2. **Grep dos acoplamentos** antes de remover qualquer app:
   ```bash
   grep -rn "apps.leads\|apps.dashboard\|apps.integrations\|provisionar_pipeline_padrao\|_leads_urlpatterns\|_dashboard_urlpatterns\|_integrations_urlpatterns\|_campos_urlpatterns\|_pipeline_urlpatterns\|_tags_urlpatterns\|avisos_limite\|corretor\|gerente\|Papel\." apps/ config/
   ```
3. **`config/urls.py`:** remover os 6 includes B2B (`leads/pipeline/campos/tags/dashboard/integracoes`) e seus imports. Manter `admin`, `health`, `signup`, `apps.users.urls`, `billing`, `accounts`, `webhooks`.
4. **`settings/base.py`:** tirar `apps.leads/dashboard/integrations` de `INSTALLED_APPS`; remover `avisos_limite` dos `context_processors` (ou reescrever para B2C sem leads).
5. **`billing/services.py`:** **cortar** `from apps.leads.services import provisionar_pipeline_padrao` e a chamada dentro de `provisionar_signup`; adaptar o serviço ao B2C (sem Asaas/Assinatura/cupom/TrialCpf na Fase 1 — ver Open Q1).
6. **`users/models.py`:** remover `Papel` (admin/gerente/corretor) e helpers `is_gerente/is_corretor/can_manage_users`; manter `email` USERNAME_FIELD e a FK `conta`. **Cuidado:** `users/views.py` (`CreateUserView`/`UserListView`/`AdminOuGerenteMixin`) e `forms.ContaUserCreationForm` dependem de `papel` — podar essas views B2B (gestão de equipe não existe no B2C) e o mixin.
7. **Deletar as pastas** `apps/leads/`, `apps/dashboard/`, `apps/integrations/` e seus `tests/`.
8. **Migrations do zero:** como o DB é novo (D-05), **resetar migrations** — apagar `apps/*/migrations/0*.py` (manter `__init__.py`) e rodar `makemigrations` limpo é mais simples que carregar migrations com FKs a apps removidos. (Alternativa: manter e criar migration de remoção — mais frágil. Recomendo reset, já que não há dado a preservar.)
9. **Validar:** `python manage.py check` → `makemigrations` → `migrate` (sqlite dev) → `pytest` (com os tests B2B removidos) → subir `runserver` e exercitar signup/login.
10. **Rebranding:** strings `crm-voic`→`lazari-capital`, `pocketleads`/`voictech`→`Lazari Capital`, `imobiliária`→terminologia B2C, `MARKETING_HOSTS`/hosts, templates (logo/paleta D-13).

## Sources

### Primary (HIGH confidence)
- Leitura direta do repo **crm-voic** (2026-07-07): `apps/users/{models,views,urls,forms}.py`, `apps/accounts/models.py`, `apps/billing/{views,services,forms}.py`, `apps/core/middleware/{billing_gate,tenant,forcar_troca_senha}.py`, `apps/core/managers.py`, `config/{urls}.py`, `config/settings/{base,prod,dev}.py`, `docker-stack.yml`, `Dockerfile`, `entrypoint.sh`, `requirements.txt`
- Leitura direta do repo **analista_dividendos**: `stack.yml`, `app.py`, `requirements.txt`, `.planning/{CONTEXT,REQUIREMENTS,ROADMAP}.md`
- doc.traefik.io — ForwardAuth middleware (reference/routing-configuration/http/middlewares/forwardauth): address, authResponseHeaders, authRequestHeaders default, trustForwardHeader, X-Forwarded-* headers, 2xx=allow/non-2xx=deny
- docs.streamlit.io — `st.context` (headers/cookies, read-only, case-insensitive, requisição inicial)

### Secondary (MEDIUM confidence)
- discuss.streamlit.io / release notes — `st.context` introduzido na **1.37.0** (25/jul/2024)
- doc.traefik.io v3.x — confirmação de que `authRequestHeaders` vazio = todos os headers (incl. Cookie) encaminhados

### Tertiary (LOW confidence / a confirmar)
- Versão exata do Traefik na VPS (v3.x assumido) — confirmar antes do deploy (Fase 3)
- Domínio real "Lazari Tech Capital" — confirmar string exata

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — versões lidas direto do crm-voic/requirements.txt
- Arquitetura do gate (forwardAuth + cookie): **MEDIUM-HIGH** — mecânica verificada em docs oficiais Traefik; a integração fim-a-fim (cookie de domínio-pai → gate → header) é padrão conhecido mas não testada nesta stack específica até a Fase 3
- Verificação de e-mail / password-reset: **HIGH** — padrões nativos Django; password-reset confirmado ausente no crm-voic (é novo)
- Pitfalls: **HIGH** — derivados de acoplamentos reais lidos no código
- Streamlit `st.context`: **HIGH** — versão e API confirmadas em docs

**Research date:** 2026-07-07
**Valid until:** ~2026-08-07 (stack estável; reconfirmar versão do Traefik e do Streamlit no deploy da Fase 3)

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | Cadastro self-serve (email+senha) + login numa camada Django | Fork de `SignupForm`/`SignupView`/`provisionar_signup` + `EmailAuthenticationForm`/`LoginView` do crm-voic (adaptados: sem Asaas/pipeline, verificação-first). Patterns 4-5. |
| AUTH-02 | Streamlit só acessível autenticado E com trial/assinatura ativa; acesso direto bloqueado sem vazar | `GateView` (Pattern 1) + Traefik forwardAuth (Pattern 2) + Streamlit sem porta pública (D-11). Threat model: bypass/spoof mitigados. |
| AUTH-03 | Identidade propagada ao Streamlit via `X-User-Email` confiável | `authResponseHeaders=X-User-Email` (Traefik) + `st.context.headers` (Streamlit ≥1.37). Code example incluído. |
| AUTH-04 | Reset de senha por link de e-mail, self-serve | **Novo** (ausente no crm-voic): 4 views `auth_views.PasswordReset*` nativas (Pattern 5); reusa EMAIL_BACKEND. |
| BILL-01 | Trial 7 dias sem cartão; `status`/`trial_ate` como fonte de verdade que o gate lê | `Conta.status`+`trial_ate` (DateField) já existem [VERIFIED: accounts/models.py]; trial 7d armado na verificação (Pattern 4). **SEM Asaas nesta fase.** |
| ACCT-01 | Multiusuário isolado, sessões simultâneas sem vazar estado | `User→Conta` 1:1 (D-01); `st.session_state` por sessão; `X-User-Email` por sessão. Pitfall/threat de vazamento modelados. |
| LEGAL-01 | "Software educacional, sem recomendação"; Termos+Privacidade+disclaimer aceitos no cadastro | Campo de aceite no `SignupForm` (borda) + copy nos templates (D-13); tom "sem recomendação" (CVM). Validação na borda (form). |
</phase_requirements>

## RESEARCH COMPLETE
