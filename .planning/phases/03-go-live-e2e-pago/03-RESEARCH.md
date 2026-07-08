# Phase 3: Go-live E2E pago - Research

**Researched:** 2026-07-08
**Domain:** Deploy integrado Docker Swarm + Traefik (Django gate forward-auth + Streamlit gated) sob domínio Lazari Capital; websockets do Streamlit atrás de forwardAuth; cutover DNS/TLS; segredos fora do git; teste E2E pago (Asaas sandbox + smoke real)
**Confidence:** HIGH (infra e código-fonte inspecionados diretamente; comportamento WS+forwardAuth confirmado por doc/comunidade Traefik)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Asaas **sandbox** p/ o fluxo automatizável + **1 smoke real manual** (R$ 19,90 no cartão próprio, com estorno logo em seguida). O E2E percorre cadastro → trial → `PAYMENT_CONFIRMED` (webhook simulado/sandbox) → acesso → cancelar → bloqueio.
- **D-02:** O E2E **reusa a suíte de billing da Phase 2** (`test_webhook_ciclo.py` etc.); a novidade é exercitá-la **ao vivo** (Traefik + gate + Streamlit reais). Simulação de webhook = POST assinado no endpoint público.
- **D-03:** Hostnames finais: `app.lazaricapital.com.br` → **Streamlit** (gated); `www.lazaricapital.com.br` → **Django** (cadastro/login/assinar/conta/webhook/gate). *(Ver Open Question #1 — conflito lazaricapital vs lazaritechcapital.)*
- **D-04:** `money.voictech.com.br` → **redirect 301 permanente** para o novo domínio. Hard-cut.
- **D-05:** Cookie de sessão no parent `.lazaricapital.com.br` (`SESSION_COOKIE_DOMAIN`); `CSRF_TRUSTED_ORIGINS`/`ALLOWED_HOSTS` cobrem ambos subdomínios.
- **D-06:** DNS `www`/`app`/apex no **Cloudflare → VPS 31.97.130.40**, **nuvem cinza (DNS-only)** nos hosts que emitem TLS via Let's Encrypt/Traefik.
- **D-07:** Go-live inclui **landing mínima de vendas** em `www` (o que é, R$ 19,90, disclaimer educacional, CTA assinar/cadastrar) + funil `/cadastro`,`/entrar`,`/conta`.
- **D-08:** Landing herda a marca Lazari Capital das telas da Phase 1 (Preline/Tailwind); enxuta.
- **D-09:** **Padrão crm-voic:** segredos num **`.env` fora do git em `/opt/lazari-capital`**, via `env_file` no `docker stack deploy`. **NÃO** usar docker secrets.
- **D-10:** `.env` prod carrega chaves **Asaas de PRODUÇÃO**, **Resend/SMTP prod**, `DATABASE_URL` do Postgres prod. Postgres dedicado em rede interna isolada.
- **D-11:** **Seed do `Plano` PRO (R$ 19,90, MONTHLY)** roda no deploy, idempotente.

### Claude's Discretion
- **Websockets do Streamlit atrás do forward-auth** (critério #3): abordagem técnica é do researcher/planner. Fallback aceitável fica com o planner; critério: app carrega e interage sem loop de auth. → **Coberto na seção "Websockets atrás do gate" abaixo.**
- Estrutura exata dos arquivos de deploy (adaptar o `docker-stack.yml` herdado), ordem de subida dos serviços, organização do `entrypoint.sh`.
- Onde exatamente mora o redirect 301 do `money.voictech.com.br` (router Traefik no stack do Streamlit vs no do Django) e a mecânica do apex.
- Se o Postgres sobe como serviço no stack ou reusa instância existente.

### Deferred Ideas (OUT OF SCOPE)
- Landing de marketing/SEO **completa** → pós-v2.0.
- Múltiplos planos/tiers, plano anual, cupons, afiliados, OAuth Google → Future.
- **Docker/Swarm secrets** (em vez de `.env`) → reavaliar depois; Phase 3 usa `.env` (D-09).
- Migração do front p/ React+Vite → Future.
- Poda do maquinário multi-tenant dormante → reavaliar.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OPS-01 | Deploy integrado (Django + gate + Streamlit) na VPS (Docker Swarm + Traefik) sob domínio Lazari Capital, com segredos (Asaas/DB) fora do git, e teste **E2E pago** (cadastro → trial → pagamento → acesso → cancelamento → bloqueio). | Stack unificado + labels Traefik (seção Architecture Patterns); `.env` em `/opt/lazari-capital` via `env_file` (Don't Hand-Roll + Code Examples); WS atrás do gate (seção dedicada); estratégia E2E sandbox+smoke (seção E2E). |
</phase_requirements>

## Summary

A Phase 3 é **quase toda infra/ops** — o código de auth, billing, gate e webhooks já está travado (Fases 1-2) e o seed do Plano PRO **já existe** como data migration idempotente. O trabalho é: (1) **re-branding do `docker-stack.yml` herdado** (hoje é cópia byte-a-byte do crm-voic, ainda apontando para `pocketleads`/`crm.voictech` e com um **worker quebrado** que chama `processar_fila_capi`, comando que foi podado na Phase 1); (2) colocar `web` (Django), `db` (Postgres) e `money` (Streamlit) **integrados sob os hosts Lazari Capital** com TLS; (3) resolver o cookie de sessão parent-domain e a resolução DNS de serviço no Swarm; (4) garantir que os **websockets do Streamlit sobrevivam ao forwardAuth**; (5) rodar o E2E pago.

O ponto crítico #3 (websockets) tem resposta clara e tranquilizadora: **o Traefik forwardAuth autentica apenas o handshake HTTP de upgrade** (`GET /_stcore/stream` com `Upgrade: websocket`), que carrega o cookie de sessão; após o upgrade, os frames WS fluem na conexão TCP aberta e **não são reautenticados** — é exatamente o comportamento desejado, sem config especial de WS no Traefik (o upgrade é nativo). O que precisa de cuidado é (a) o cookie de sessão chegar no host `app.` (parent-domain cookie, já configurado no `prod.py`), e (b) o Streamlit não recusar a conexão por CORS/XSRF atrás do proxy — mitigável com config `server.*` se o loop "Please wait..." aparecer.

O **maior risco escondido** não é o websocket — é a **resolução de nome de serviço no Swarm**: o `stack.yml` do Streamlit aponta `forwardauth.address=http://web:8000/gate/`, mas o próprio `.env.prod.example` do crm-voic documenta que **nomes curtos podem não resolver no Swarm** e exige o FQDN `stack_serviço` (ex.: `crm-voic_db`). Se `money` e `web` não estiverem no mesmo stack com naming consistente, o gate fica inalcançável e **tudo bloqueia**.

**Primary recommendation:** Unificar `web` + `worker` + `db` + `money` num **único `docker-stack.yml`** (stack `lazari`), corrigir o worker quebrado, apontar `forwardauth.address=http://lazari_web:8000/gate/` (FQDN), setar `SESSION_COOKIE_DOMAIN` e `ASAAS_BASE_URL` de produção no `.env` em `/opt/lazari-capital`, criar os registros DNS (nuvem cinza) **antes** do deploy, e validar WS via smoke manual no host `app.` logado.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Terminação TLS + roteamento por host | Traefik (ingress) | — | Único ingresso; Let's Encrypt via `letsencryptresolver` |
| Decisão de acesso (auth + status) | Django `web` (`/gate/`) | Postgres (`Conta`) | forwardAuth delega a decisão; fonte de verdade é `Conta` |
| Sessão/cookie de auth | Django `web` | Browser (cookie parent-domain) | Cookie `.dominio` emitido no `www.`, lido no `app.` |
| Render do app + websockets | Streamlit `money` | — | Engine intacto; WS em `/_stcore/stream` |
| Persistência (contas/assinaturas/webhook log) | Postgres `db` | — | Rede interna isolada, nunca exposta |
| Cobrança/checkout | Asaas (externo) | Django `billing` | Checkout hospedado; produto nunca toca cartão |
| Webhook de status | Django `web` (`/billing/webhook/`) | Postgres | Idempotente por `event_id` (Phase 2) |
| Redirect domínio antigo | Traefik (router) | — | 301 permanente `money.voictech` → novo host |
| Segredos | `.env` em `/opt/lazari-capital` (host) | `env_file` do stack | Fora do git; injetado no deploy (D-09) |
| Backup/restore | Cron no host VPS + `pg_dump` | Postgres `db` | Scripts do crm-voic (`backup.sh`/`restore_verify.sh`) |

## Standard Stack

### Core
| Componente | Versão (verificada) | Purpose | Why Standard |
|-----------|---------------------|---------|--------------|
| Django | **5.2.\*** (pin do projeto; PyPI atual 6.0.7 [VERIFIED: pypi.org]) | Front auth/billing/gate | Já é o pin do lazari-capital; **não bumpar** nesta fase (fora de escopo) |
| Streamlit | **>=1.37** (pin do projeto; PyPI atual 1.59.1 [VERIFIED: pypi.org]) | Engine gated; lê `X-User-Email` via `st.context.headers` | `st.context` requer >=1.37 (já garantido na Phase 1) |
| Traefik | versão instalada na VPS (não inspecionável daqui) [ASSUMED: v2.x, provider Swarm] | Ingress + TLS + forwardAuth | Já opera o crm-voic e o `money` atual |
| PostgreSQL | **17-alpine** [VERIFIED: crm-voic/docker-stack.yml] | Fonte de verdade | Padrão crm-voic replicado |
| Gunicorn | **23.\*** [VERIFIED: lazari-capital/requirements.txt] | WSGI do Django | 5 workers (2×cores+1) no `entrypoint.sh` |
| WhiteNoise | 6.12.0 [VERIFIED: requirements.txt] | Static files | `CompressedManifestStaticFilesStorage` (prod.py) |
| psycopg | 3.3.4 [VERIFIED: requirements.txt] | Driver Postgres | — |
| django-environ | 0.13.0 [VERIFIED: requirements.txt] | Ler `.env` | `env.list()` para hosts/origins |
| Docker Swarm | single-node na VPS [VERIFIED: crm-voic stack header] | Orquestração | Sem registry; imagem `:latest` local |

### Supporting
| Componente | Purpose | When to Use |
|-----------|---------|-------------|
| Resend (SMTP `smtp.resend.com:587`) | E-mail transacional (verificação/reset) | Caminho crítico do trial (D-10); `RESEND_API_KEY` no `.env` prod |
| Asaas API v3 | Checkout + webhooks | `ASAAS_BASE_URL=https://api.asaas.com/v3` em prod (default do base.py é **sandbox**) |
| `scripts/backup.sh` + `restore_verify.sh` | Backup diário + restore-test do Postgres | Cron root no VPS; retenção 7 dias |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Stack único (web+worker+db+money) | Dois stacks separados | Separados exigem FQDN cross-stack e complicam a resolução `web`→gate; **unificar é mais simples e evita o bug de DNS** |
| `.env` via `env_file` (D-09) | Docker secrets | Secrets fugiria do padrão crm-voic e exigiria mexer em entrypoint/settings — deferido |
| Postgres como serviço no stack | Reusar instância existente na VPS | Serviço dedicado (padrão crm-voic) isola dados e credenciais; **recomendado** |

**Installation (build local antes do deploy, na VPS):**
```bash
# em /opt/lazari-capital (Django) — repo ~/projects/lazari-capital
docker build -t lazari-web:latest .
# no diretório do engine Streamlit — repo analista_dividendos
docker build -t money:latest .
docker stack deploy -c docker-stack.yml lazari
```

**Version verification:** Django 5.2.\* e Streamlit >=1.37 são os pins **atuais e corretos** do projeto; PyPI já avançou (Django 6.0.7, Streamlit 1.59.1) mas **bumpar está fora do escopo desta fase**. Manter os pins.

## Architecture Patterns

### System Architecture Diagram

```
                          Cloudflare DNS (nuvem CINZA / DNS-only nos hosts com TLS)
                                        │  A records → 31.97.130.40
                                        ▼
   Internet ──────────────► Traefik (ingress único, :443 websecure, Let's Encrypt)
                                 │
      ┌──────────────────────────┼───────────────────────────────┬────────────────────────┐
      │ Host(www.lazari…)        │ Host(app.lazari…)              │ Host(money.voictech)   │
      │ router → lazari_web      │ router → money  [middleware:   │ router → redirect 301  │
      │                          │   lazari-gate forwardAuth]     │   → app.lazari…        │
      ▼                          ▼                                ▼
  ┌─────────┐   forwardAuth   ┌─────────────────────────────┐  (só responde 301)
  │ Django  │◄── GET /gate/ ──┤ Traefik intercepta ANTES de │
  │ web:8000│  (Cookie da     │ rotear ao Streamlit         │
  │         │   sessão vai    └──────────────┬──────────────┘
  │ /gate/  │   no header)          2xx + X-User-Email
  │ /billing│                              │  (só no handshake HTTP;
  │ /conta  │                              ▼   frames WS NÃO reautenticam)
  │ /signup │                       ┌──────────────┐
  └────┬────┘                       │ Streamlit    │  WS: /_stcore/stream
       │                            │ money:8501   │  HTTP: página + /_stcore/health
       │ crm_internal (isolada)     │ lê X-User-   │
       ▼                            │ Email header │
  ┌─────────┐                       └──────────────┘
  │ Postgres│  ◄── Asaas webhook (POST /billing/webhook/, idempotente) ── api.asaas.com
  │ db:5432 │  ◄── worker (processar_billing diário, sem HTTP)
  └─────────┘
```

Fluxo do caso principal (usuário pagante abrindo o app):
1. Browser pede `https://app.lazaricapital.com.br` com cookie `sessionid` (domínio-pai).
2. Traefik, antes de rotear, chama `GET http://lazari_web:8000/gate/` **encaminhando o Cookie**.
3. `GateView` resolve `request.user` via SessionMiddleware, checa `Conta.status`/datas → responde `200 + X-User-Email`.
4. Traefik roteia ao `money:8501`, promovendo `X-User-Email` como header confiável.
5. Streamlit renderiza; o browser abre WS `wss://app…/_stcore/stream` → novo handshake HTTP passa pelo gate (mesmo cookie) → 200 → upgrade → conexão persistente sem reautenticação.

### Recommended Project Structure (deploy)
```
/opt/lazari-capital/                # na VPS (rsync do repo Django + arquivos de deploy)
├── docker-stack.yml                # UNIFICADO: web + worker + db + money
├── .env                            # segredos prod (fora do git; chmod 600)
├── Dockerfile                      # build lazari-web:latest
├── entrypoint.sh                   # collectstatic + migrate (roda o seed) + gunicorn
└── scripts/{backup.sh,restore_verify.sh}

# imagem money:latest buildada a partir do repo analista_dividendos (Dockerfile próprio)
```

### Pattern 1: Stack unificado com FQDN de serviço no forwardAuth
**What:** Um único `docker-stack.yml` (nome `lazari`) com `web`, `worker`, `db`, `money`. O `money` referencia o gate pelo **nome de serviço qualificado do Swarm** `lazari_web`, não `web`.
**When to use:** Sempre nesta fase — resolve o risco #1 (DNS de serviço).
**Example:**
```yaml
# money.deploy.labels — CORRIGIDO (era http://web:8000)
- traefik.http.middlewares.lazari-gate.forwardauth.address=http://lazari_web:8000/gate/
- traefik.http.middlewares.lazari-gate.forwardauth.authResponseHeaders=X-User-Email
- traefik.http.middlewares.lazari-gate.forwardauth.trustForwardHeader=true
- traefik.http.routers.money.rule=Host(`app.lazaricapital.com.br`)
- traefik.http.routers.money.middlewares=lazari-gate
- traefik.http.services.money.loadbalancer.server.port=8501
```
> [CITED: crm-voic/.env.prod.example L31-34] "No Swarm o nome curto `db` pode não resolver — use o nome completo do serviço." O mesmo vale para `web` visto pelo `money`.

### Pattern 2: Websockets atrás do forwardAuth (critério #3)
**What:** O forwardAuth autentica **só o handshake de upgrade**; frames subsequentes fluem sem reautenticação.
**When to use:** É o comportamento nativo — nenhuma config especial de WS no Traefik é necessária (Traefik faz upgrade de WS out-of-the-box quando o backend responde `101`).
**Detalhes que importam:**
- O gate (`GET /gate/`) precisa responder **rápido e 2xx** no handshake; ele é read-only e barato (uma query em `Conta`). OK.
- **`trustForwardHeader=true`** e o default de `authRequestHeaders` (encaminha TODOS os headers, incluindo `Cookie`) são o que faz `request.user` resolver. **NÃO** setar `authRequestHeaders` restritivo (removeria o Cookie → loop de auth). Já correto no `stack.yml` atual.
- **replicas: 1** no `money` → sem necessidade de sticky sessions. Se algum dia escalar `>1`, o WS exige `loadbalancer.sticky.cookie=true` (Streamlit amarra a sessão a uma réplica). Registrar como nota, não implementar.
**Fallback aceitável (se o app entrar em loop "Please wait…"/WS 1006):**
```toml
# .streamlit/config.toml (ou flags no CMD) — só se o handshake XSRF/CORS recusar
[server]
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false
```
> [VERIFIED: discuss.streamlit.io/t/32075] Com `enableXsrfProtection=true` (default) o Streamlit exige CORS e manda cookie próprio; **atrás de proxy same-origin com `passHostHeader=true` isso normalmente funciona** — só desabilitar se o smoke falhar. O gate já provê a camada de auth, então perder o XSRF do Streamlit é risco baixo (same-origin + forwardAuth).

### Pattern 3: Redirect 301 do domínio antigo
**What:** Router Traefik dedicado para `money.voictech.com.br` com `redirectregex` permanente → `app.lazaricapital.com.br`, preservando path.
**When to use:** No cutover (D-04). Recomendo alojar no serviço **`web` (Django)**, espelhando o `pl_apex` do crm-voic (o serviço que "serve" o redirect é irrelevante — o middleware responde antes).
**Example:** ver Code Examples abaixo. Requer que `money.voictech.com.br` continue no DNS apontando à VPS e tenha cert (o `money` atual já emite; manter o host resolvível).

### Pattern 4: Seed idempotente do Plano PRO (D-11) — JÁ EXISTE
**What:** Data migration `apps/billing/migrations/0002_seed_plano_pro.py` usa `update_or_create(nome="PRO", ...preco_mensal=19.90...)`.
**When to use:** Roda automaticamente no `migrate` do `entrypoint.sh` a cada boot — **idempotente, sem trabalho novo**. O planner só precisa garantir que o `migrate` rode no deploy (roda). Não criar management command paralelo.
> [VERIFIED: lazari-capital/apps/billing/migrations/0002_seed_plano_pro.py]

### Anti-Patterns to Avoid
- **`forwardauth.address=http://web:8000`** com stacks separados → não resolve → gate inalcançável → **tudo bloqueado**. Use FQDN `lazari_web` (ou stack único com naming consistente).
- **Publicar porta do `money`** (`ports:`) → burla o gate; qualquer um seta `X-User-Email` na mão e spoofa identidade. O `stack.yml` atual **corretamente não publica porta** — manter.
- **`authRequestHeaders` restritivo no forwardAuth** → remove o `Cookie` → gate sempre "anônimo" → loop de redirect.
- **Deploy antes do DNS** → Let's Encrypt falha a emissão do cert (SAN) → 404/TLS quebrado. Criar DNS (nuvem cinza) **primeiro**.
- **`SESSION_COOKIE_DOMAIN` com nuvem laranja (proxy CF)** → CF pode reescrever/duplicar cookies e o Let's Encrypt HTTP-01 falha. Nuvem **cinza** (D-06).
- **Worker herdado quebrado** (`processar_fila_capi`) → o container do worker entra em crash-loop. Corrigir/remover (ver Runtime State Inventory).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Autenticar WS por frame | Middleware custom que valida cada mensagem | forwardAuth no handshake + trust da conexão | É o modelo nativo; validar por frame é impossível no proxy e desnecessário |
| Injeção de segredos | Hard-code / secrets no git / vault novo | `.env` em `/opt/lazari-capital` via `env_file` (D-09) | Padrão crm-voic já operante |
| Redirect do domínio antigo | View Django/redirect app-level | `redirectregex` middleware do Traefik | 301 no ingress, sem tocar app; espelha `pl_apex` |
| Seed do Plano | Script ad-hoc no deploy | Data migration existente (0002) | Já idempotente e roda no `migrate` |
| Backup do Postgres | Rotina nova | `scripts/backup.sh` + `restore_verify.sh` do crm-voic | Testados; retenção 7d + restore-test |
| TLS/cert | Certbot manual | `letsencryptresolver` do Traefik | Já configurado no host |
| Cookie cross-subdomínio | JWT custom no Streamlit | `SESSION_COOKIE_DOMAIN=.dominio` + forwardAuth | Decisão de arquitetura travada (menos código de segurança) |

**Key insight:** Praticamente tudo que a Phase 3 precisa **já existe** no par crm-voic/lazari-capital ou no `stack.yml` do `money`. O erro caro aqui é **inventar** (JWT no Streamlit, auth por frame, secrets novos) em vez de **corrigir e religar** os artefatos existentes aos hosts Lazari Capital.

## Runtime State Inventory

> Fase de **go-live/cutover** — grep de arquivos não captura o estado de runtime. Inventário explícito:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | Postgres de produção **ainda não existe** (dev usa `dev.sqlite3`). O `money.voictech.com.br` atual **não tem banco de contas** (é o app v1.7 sem gate). | **Criar** o Postgres prod no deploy; rodar `migrate` (cria schema + seed Plano PRO). Sem migração de dados legada — base nova. |
| **Live service config** | **Stack `money` já rodando na VPS** em `money.voictech.com.br` (v1.7, sem gate). DNS `money.voictech.com.br` → VPS ativo. Traefik com cert desse host. | Cutover: (a) subir stack `lazari` novo; (b) trocar o router do `money` para `Host(app.lazaricapital…)` + gate; (c) adicionar router 301 no host antigo. Confirmar se `money` roda em stack próprio hoje (provável) e **fundir** no stack `lazari`. |
| **OS-registered state** | Cron de backup do crm-voic existe no VPS (`0 2 * * *`). Nenhum cron para lazari ainda. | Registrar cron `backup.sh` para o novo Postgres (`CRM_DB_CONTAINER` = nome real do container Swarm, ex. `lazari_db`). |
| **Secrets/env vars** | `.env` dev do lazari-capital só tem 4 vars (DEBUG/SECRET_KEY/DATABASE_URL sqlite/ALLOWED_HOSTS). **Falta o `.env` prod em `/opt/lazari-capital`.** Base.py: **`ASAAS_BASE_URL` default = sandbox**; **`ASAAS_API_KEY` começa com `$`** (django-environ interpola `$` → escapar `$$` no `.env`). `SESSION_COOKIE_DOMAIN` default no prod.py = `.lazaritechcapital.com.br` (**ver Open Q#1**). | Criar `.env` prod completo (chaves Asaas **prod**, `ASAAS_BASE_URL=https://api.asaas.com/v3`, Resend prod, `DATABASE_URL` prod, `SESSION_COOKIE_DOMAIN` real, `ALLOWED_HOSTS`+`CSRF_TRUSTED_ORIGINS` www/app/localhost, `SECRET_KEY` novo). Escapar `$$` nas chaves Asaas. |
| **Build artifacts** | `docker-stack.yml` do lazari-capital é **cópia byte-a-byte do crm-voic** (aponta `pocketleads`/`crm.voictech`; volume `crm_postgres_data`; rede `crm_internal`; **worker chama `processar_fila_capi` — comando PODADO na Phase 1, não existe**). Imagem `lazari-web:latest` ainda não buildada. | Re-brandar o stack (hosts, nomes de volume/rede/stack, router). **Corrigir o worker**: `processar_fila_capi` não existe → deixar só `processar_billing` (existe) ou remover o worker se o billing diário não for necessário no go-live. |

**A pergunta canônica:** depois que o repo estiver atualizado, o que ainda carrega o nome/estado antigo? → o **`money` v1.7 em produção** (troca de router no cutover), o **DNS `money.voictech`** (mantém + 301), o **`docker-stack.yml` não-re-brandado** e o **worker com comando morto**.

## Common Pitfalls

### Pitfall 1: Nome de serviço curto não resolve no Swarm (gate inalcançável)
**What goes wrong:** `forwardauth.address=http://web:8000` retorna erro de conexão; o Traefik trata como falha do auth e bloqueia o `money` → app nunca abre.
**Why it happens:** No Swarm deste host, DNS de serviço por nome curto é instável entre/mesmo dentro de stacks (documentado no `.env` do crm-voic para o Postgres).
**How to avoid:** Stack único `lazari` + FQDN `lazari_web`. Testar de dentro do container `money`: `wget -qO- http://lazari_web:8000/health/`.
**Warning signs:** logs do Traefik com `dial tcp: lookup web ... no such host`; app em "Please wait…" eterno.

### Pitfall 2: Loop de redirect / gate sempre "anônimo" (cookie não chega)
**What goes wrong:** Usuário logado no `www.` é jogado ao login ao abrir `app.`.
**Why it happens:** `SESSION_COOKIE_DOMAIN` não é o parent-domain real, ou `authRequestHeaders` removeu o `Cookie`, ou `SESSION_COOKIE_SECURE`/`SECURE_PROXY_SSL_HEADER` mal configurados fazem o Django não reconhecer HTTPS no gate interno (HTTP).
**How to avoid:** `SESSION_COOKIE_DOMAIN=.<dominio-real>` (Open Q#1); manter `SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')` (já no prod.py); `trustForwardHeader=true`; não setar `authRequestHeaders`.
**Warning signs:** `/gate/` responde 302→login mesmo com sessão válida; cookie ausente no request do gate.

### Pitfall 3: Let's Encrypt falha na emissão do cert
**What goes wrong:** `app.`/`www.` respondem com cert inválido/`TRAEFIK DEFAULT CERT`.
**Why it happens:** DNS ainda não propagou, ou host em **nuvem laranja** (CF proxy) interceptando o HTTP-01.
**How to avoid:** Criar A records **nuvem cinza** e confirmar `dig +short app.lazaricapital.com.br` = 31.97.130.40 **antes** do `docker stack deploy`.
**Warning signs:** logs Traefik `unable to obtain ACME certificate`.

### Pitfall 4: `$` nas chaves Asaas some no `.env`
**What goes wrong:** `ASAAS_API_KEY` fica truncada/inválida → checkout e webhook falham em produção.
**Why it happens:** django-environ interpola `${...}`; a chave Asaas começa com `$aact_prod_...`.
**How to avoid:** Escapar `$$` no `.env` (base.py L31 documenta isso). Validar com um `assinar` no sandbox antes da virada.
**Warning signs:** 401 do Asaas; chave "curta" nos logs.

### Pitfall 5: `DisallowedHost` / healthcheck derruba o container
**What goes wrong:** Swarm reinicia `web` em loop.
**Why it happens:** `ALLOWED_HOSTS` sem `localhost,127.0.0.1` (o healthcheck bate em `http://localhost:8000/health/`).
**How to avoid:** `ALLOWED_HOSTS=www.lazari…,app.lazari…,localhost,127.0.0.1`; `start_period: 180s` (collectstatic+migrate demora).
**Warning signs:** container `unhealthy` repetido; 400 nos logs.

### Pitfall 6: `docker stack deploy` remove o `money` órfão / mata o app no meio do cutover
**What goes wrong:** subir o stack novo derruba o app antigo antes do novo estar pronto.
**Why it happens:** `--prune`/`--remove-orphans` ou fundir stacks sem cuidado.
**How to avoid:** Deploy do stack unificado, validar `web`/`db`/`money` healthy, **depois** trocar routers/DNS. Não usar prune agressivo durante a virada.
**Warning signs:** downtime observável no `money.voictech`.

## Code Examples

### Redirect 301 do domínio antigo (labels no serviço `web`, espelhando pl_apex)
```yaml
# Source: crm-voic/docker-stack.yml (pl_apex) adaptado
- "traefik.http.routers.money_old.rule=Host(`money.voictech.com.br`)"
- "traefik.http.routers.money_old.entrypoints=websecure"
- "traefik.http.routers.money_old.service=lazari_web"
- "traefik.http.routers.money_old.tls=true"
- "traefik.http.routers.money_old.tls.certresolver=letsencryptresolver"
- "traefik.http.routers.money_old.middlewares=money_301"
- "traefik.http.middlewares.money_301.redirectregex.regex=^https?://[^/]+/(.*)"
- "traefik.http.middlewares.money_301.redirectregex.replacement=https://app.lazaricapital.com.br/$${1}"
- "traefik.http.middlewares.money_301.redirectregex.permanent=true"
# $${1} (não ${1}): docker stack interpola $ — escapar com $$ p/ passar ${1} literal ao Traefik.
```

### `.env` de produção (/opt/lazari-capital/.env) — esqueleto
```bash
# Source: crm-voic/.env.prod.example adaptado
SECRET_KEY=<python -c "import secrets;print(secrets.token_urlsafe(64))">
DEBUG=False
ALLOWED_HOSTS=www.lazaricapital.com.br,app.lazaricapital.com.br,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://www.lazaricapital.com.br,https://app.lazaricapital.com.br
SESSION_COOKIE_DOMAIN=.lazaricapital.com.br   # confirmar domínio real (Open Q#1)
CSRF_COOKIE_DOMAIN=.lazaricapital.com.br

DATABASE_URL=postgres://lazari_user:<senha>@lazari_db:5432/lazari   # FQDN do serviço Swarm
POSTGRES_DB=lazari
POSTGRES_USER=lazari_user
POSTGRES_PASSWORD=<senha>
GUNICORN_WORKERS=5

RESEND_API_KEY=re_...
DEFAULT_FROM_EMAIL=no-reply@lazaricapital.com.br

ASAAS_API_KEY=$$aact_prod_...     # ESCAPAR o $ inicial com $$
ASAAS_BASE_URL=https://api.asaas.com/v3   # PROD (default do base.py é sandbox)
ASAAS_WEBHOOK_TOKEN=<token do painel Asaas prod>
```

### Smoke de resolução do gate (dentro do container money)
```bash
# valida Pitfall 1 antes de depender do Traefik
docker exec -it $(docker ps -qf name=lazari_money) sh -c "wget -qO- http://lazari_web:8000/health/"
# esperado: ok
```

### Config de fallback do Streamlit (só se WS recusar)
```toml
# .streamlit/config.toml no repo analista_dividendos (rebuild money:latest)
[server]
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false
```

## E2E pago — estratégia (OPS-01, critério #2)

**Camadas do teste (D-01/D-02):**
1. **Automatizável (sandbox/CI-friendly):** reusar a suíte da Phase 2 (`test_webhook_ciclo.py`, testes do GateView/billing) — já cobre cadastro→trial→`PAYMENT_CONFIRMED`→ativação→`PAYMENT_OVERDUE`→graça→cancelamento→bloqueio, com idempotência por `event_id`. Rodar contra a base (pytest) **e** exercitar o endpoint público `POST /billing/webhook/` com payload assinado (o `ASAAS_WEBHOOK_TOKEN`) contra o ambiente ao vivo.
2. **Ao vivo (a novidade da Phase 3):** com Traefik+gate+Streamlit reais no host `app.` — validar que cada transição de `Conta.status` **reflete no acesso**:
   - trial ativo → `app.` abre e o WS conecta;
   - webhook `PAYMENT_CONFIRMED` (sandbox) → segue liberado como ativo;
   - cancelar via página de conta → libera até paid-through, depois bloqueia (`/trial-acabou/`);
   - `PAYMENT_OVERDUE` + passar `grace_ate` → bloqueia.
3. **Smoke real manual (1×):** assinatura real R$ 19,90 no cartão próprio contra Asaas **prod** → confirma chaves prod + checkout hospedado real + webhook prod chegando + gate/WS reais → **estorno/cancelamento imediato**.

**Checklist de aceite E2E:**
- [ ] Cadastro self-serve no `www.` → e-mail de verificação (Resend prod) chega → trial 7d ativo.
- [ ] `app.` abre logado (gate 200 + `X-User-Email` visível no app) e o WS `/_stcore/stream` mantém a sessão (interação sem reload/loop).
- [ ] Acesso direto a `app.` sem sessão → 302 login (não vaza o app).
- [ ] Assinar (sandbox) → `PAYMENT_CONFIRMED` → ativo; webhook repetido não duplica.
- [ ] Cancelar → acesso até paid-through → depois `/trial-acabou/`.
- [ ] Smoke real R$ 19,90 → confirmado → estornado.
- [ ] `money.voictech.com.br/x` → 301 → `app.lazaricapital.com.br/x`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WS auth por-mensagem | forwardAuth no handshake + trust da conexão | consenso Traefik v2+ | Nenhuma config especial de WS; simplifica o gate |
| `STATICFILES_STORAGE` | `STORAGES` dict (WhiteNoise) | Django 4.2+ | prod.py já usa `STORAGES` (não misturar com o antigo) |
| n8n p/ webhooks | webhooks nativos Django idempotentes | v2.0 (Phase 2) | Menos dependência; E2E mais simples |

**Deprecated/outdated:**
- Pins Django 5.2 / Streamlit 1.37 estão **atrás** do PyPI (6.0.7 / 1.59.1) mas **corretos para esta fase** — bump é out-of-scope.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Domínio real é `lazaricapital.com.br` (CONTEXT/memória) e **não** `lazaritechcapital.com.br` (default do prod.py / PROJECT "domínio Lazari Tech Capital") | User Constraints / Open Q#1 | **Alto** — cookie parent-domain, ALLOWED_HOSTS, DNS e cert todos dependem do domínio exato; errar = loop de auth + cert inválido |
| A2 | Traefik na VPS é v2.x com provider Swarm e `letsencryptresolver` configurado | Standard Stack | Baixo — confirmado indiretamente pelo crm-voic/money em operação |
| A3 | O `money` v1.7 hoje roda em stack próprio na VPS (a fundir no stack `lazari`) | Runtime State Inventory | Médio — se estiver noutro arranjo, o cutover muda |
| A4 | Não há base de contas legada a migrar (Postgres prod é novo) | Runtime State Inventory | Baixo — dev usa sqlite; produção do gate nunca existiu |
| A5 | O worker (`processar_billing` diário) é desejável no go-live; senão pode ser removido | Runtime State Inventory | Baixo — decisão do planner |

## Open Questions

1. **Domínio exato: `lazaricapital.com.br` vs `lazaritechcapital.com.br`?** [BLOQUEANTE]
   - What we know: CONTEXT D-03/05/06 e a memória de DNS dizem `lazaricapital.com.br` (`www`/`app`). Mas o `prod.py` tem default `SESSION_COOKIE_DOMAIN=.lazaritechcapital.com.br` e o PROJECT.md diz "domínio **Lazari Tech** Capital".
   - What's unclear: qual domínio foi de fato **registrado no Cloudflare** e aponta à VPS.
   - Recommendation: **confirmar com o usuário / `dig` no Cloudflare antes de planejar**. Tudo (cookie, ALLOWED_HOSTS, CSRF, cert) deriva disso. Setar `SESSION_COOKIE_DOMAIN` explicitamente no `.env` prod (não confiar no default do código).

2. **Onde mora o Postgres de produção?** Serviço novo no stack `lazari` (recomendado, padrão crm-voic) vs instância existente. Recommendation: serviço dedicado `lazari_db` em rede interna isolada.

3. **O `money` v1.7 atual deve continuar servível durante a virada?** D-04 é hard-cut, mas convém um curto overlap para o smoke. Recommendation: subir `lazari` completo, validar, e só então trocar routers/301 (Pitfall 6).

4. **Worker no go-live?** `processar_billing` existe; `processar_fila_capi` (no stack herdado) **não**. Recommendation: manter só `processar_billing` ou omitir o worker nesta fase.

## Environment Availability

> Alvo é a **VPS 31.97.130.40** (Docker Swarm + Traefik), não a máquina local — não é possível sondar daqui via este agente. Itens a **verificar no VPS durante o deploy** (não bloqueiam o planejamento):

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker Swarm (single-node) | orquestração | ✓ [VERIFIED: crm-voic operante] | — | — |
| Traefik + `letsencryptresolver` | ingress/TLS | ✓ [VERIFIED: money/crm operantes] | v2.x [ASSUMED] | — |
| Overlay `network_swarm_public` | ingress | ✓ [VERIFIED: stack.yml external] | — | — |
| DNS Cloudflare do domínio Lazari | hosts www/app | ✗ a confirmar | — | criar A records nuvem cinza |
| `.env` em `/opt/lazari-capital` | segredos | ✗ criar | — | — |
| Cron backup (host) | PROD backup | ✗ registrar | — | `scripts/backup.sh` |
| SSH `id_ed25519_vps` | deploy (rsync/scp) | ✓ [CITED: memória] | — | — |

**Missing (a criar no deploy, não bloqueiam o plano):** registros DNS, `.env` prod, cron de backup, imagens `lazari-web:latest`/`money:latest` buildadas na VPS.

## Security Domain

> `security_enforcement` ausente no config (= habilitado). Fase de deploy — foco em superfície de exposição.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | sim | Sessão Django + gate forwardAuth (já implementado) |
| V3 Session Management | sim | Cookie `Secure`+`HttpOnly`+`SameSite=Lax`, parent-domain (prod.py) |
| V4 Access Control | sim | GateView fail-closed lendo `Conta`; `money` sem porta pública |
| V5 Input Validation | sim | Webhook idempotente + `ASAAS_WEBHOOK_TOKEN` (Phase 2) |
| V6 Cryptography | sim | TLS via Let's Encrypt; segredos fora do git; `SECRET_KEY` novo em prod |
| V14 Config | sim | `DEBUG=False`, HSTS, `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`, `.env` chmod 600 |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Spoof de `X-User-Email` (acesso direto ao Streamlit) | Spoofing | `money` **sem porta pública**; só via Traefik+gate (mantido no stack.yml) |
| Cookie roubado cross-site | Info Disclosure | `SameSite=Lax` + `Secure` + parent-domain (não `None`) |
| Webhook forjado do Asaas | Tampering | Token no header + idempotência por `event_id` |
| Cert/TLS quebrado (downgrade) | Info Disclosure | `SECURE_SSL_REDIRECT`+HSTS; DNS cinza p/ ACME |
| Segredo vazado no git | Info Disclosure | `.env` em `/opt/...` fora do repo; `$$` p/ chaves Asaas |
| DoS por porta de banco exposta | DoS | `db` só na rede interna `crm_internal`/`lazari_internal` |

## Sources

### Primary (HIGH confidence)
- Código inspecionado diretamente: `lazari-capital/{docker-stack.yml,Dockerfile,entrypoint.sh,config/settings/prod.py,apps/gate/views.py,apps/billing/migrations/0002_seed_plano_pro.py,requirements.txt,.env,.env.prod.example}`; `analista_dividendos/{stack.yml,Dockerfile,.streamlit/config.toml,app.py}`; `crm-voic/{docker-stack.yml,scripts/backup.sh,restore_verify.sh}`.
- CONTEXT/ROADMAP/REQUIREMENTS/PROJECT/STATE da Phase 3 e Fases 1-2.
- [VERIFIED: pypi.org] Django 6.0.7 / Streamlit 1.59.1 (pins do projeto 5.2 / >=1.37 mantidos).

### Secondary (MEDIUM confidence)
- [VERIFIED: community.traefik.io/t/20660 + oneuptime.com Traefik forwardAuth guide] forwardAuth autentica o handshake WS; frames não reautenticam.
- [VERIFIED: discuss.streamlit.io/t/32075] `enableXsrfProtection` força CORS; desabilitar só atrás de proxy se necessário.
- [CITED: github.com/streamlit/streamlit/issues/6305, /8188] WS 1006 / "Please wait…" atrás de proxy — fallback de config.

### Tertiary (LOW confidence)
- Versão exata do Traefik na VPS (assumida v2.x) — confirmar no deploy.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — arquivos e versões inspecionados.
- Architecture (WS + forwardAuth + FQDN Swarm): HIGH — comportamento confirmado por doc/comunidade e por evidência empírica do próprio infra (nota de DNS no `.env` do crm-voic).
- Pitfalls: HIGH — derivados de artefatos reais (worker quebrado, `$` nas chaves, domínio divergente).
- Domínio exato: LOW — conflito documental não resolvível sem o usuário (Open Q#1).

**Research date:** 2026-07-08
**Valid until:** 2026-08-07 (infra estável; reconfirmar apenas o domínio e a versão do Traefik no deploy)
