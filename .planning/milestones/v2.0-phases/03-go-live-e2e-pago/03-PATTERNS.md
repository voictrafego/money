# Phase 03: Go-live E2E pago - Pattern Map

**Mapped:** 2026-07-08
**Files analyzed:** 9 deploy/config artifacts (+ 1 test procedure, 1 landing)
**Analogs found:** 8 / 9 (all deploy artifacts have a direct analog; landing/E2E reuse Phase 1/2 assets)

> Infra/ops phase — the "files" are deploy artifacts (Swarm stacks, `.env`, entrypoint, settings, backup script) split across THREE repos:
> - Django front: `/Users/giovanelazari/projects/lazari-capital`
> - Streamlit engine: `/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos`
> - Reference deploy: `/Users/giovanelazari/projects/crm-voic`
>
> Key upstream finding (RESEARCH primary recommendation): **unify `web` + `worker` + `db` + `money` into a single `docker-stack.yml` (stack name `lazari`)** so the Streamlit `money` service can reach the gate via the qualified Swarm name `lazari_web` instead of the short name `web` (which may not resolve). This changes where the `money` service definition lives (moves from `analista_dividendos/stack.yml` into `lazari-capital/docker-stack.yml`), so several patterns below cross repos.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `~/projects/lazari-capital/docker-stack.yml` (modify) | config/deploy | request-response | `~/projects/crm-voic/docker-stack.yml` | exact (it IS a byte-for-byte fork) |
| `/opt/lazari-capital/.env` (create on VPS) | config/secrets | — | `~/projects/crm-voic/.env.prod.example` | exact |
| `~/projects/lazari-capital/config/settings/prod.py` (modify) | config | request-response | itself (already 95% done) | self / exact |
| `~/projects/lazari-capital/entrypoint.sh` (keep/verify) | config/boot | batch | itself = `~/projects/crm-voic` entrypoint | exact |
| `~/projects/lazari-capital/Dockerfile` (likely no change) | config/build | batch | itself | exact |
| `analista_dividendos/stack.yml` (modify OR fold into `lazari`) | config/deploy | request-response + WS | itself + crm-voic labels | self / role-match |
| `analista_dividendos/.streamlit/config.toml` (modify — fallback only) | config | streaming (WS) | itself | self |
| `~/projects/lazari-capital/scripts/backup.sh` (create) | utility | file-I/O / batch | `~/projects/crm-voic/scripts/backup.sh` | exact |
| E2E pago (live exercise, not a new file) | test | request-response + event-driven | Phase 2 `test_webhook_ciclo.py` / GateView tests | reuse (see No Analog) |
| Landing mínima de vendas em `www` (Django templates) | component | request-response | Phase 1 telas (Preline/Tailwind) | reuse (not inspected here) |

## Pattern Assignments

### `~/projects/lazari-capital/docker-stack.yml` (config/deploy, request-response) — CENTRAL FILE

**Analog:** `/Users/giovanelazari/projects/crm-voic/docker-stack.yml` (the lazari copy is currently byte-identical to it — still pointing at `pocketleads`/`crm.voictech`, volume `crm_postgres_data`, network `crm_internal`, and a **broken worker** calling `processar_fila_capi`, a command pruned in Phase 1).

**read_first:** `/Users/giovanelazari/projects/crm-voic/docker-stack.yml` (full, 124 lines); `/Users/giovanelazari/projects/lazari-capital/docker-stack.yml` (the file to edit — identical); `/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos/stack.yml` (source of the `money` service block to fold in).

**`web` service skeleton** (crm-voic lines 15-39) — copy, re-brand image to `lazari-web:latest`, add `lazari_internal` network:
```yaml
services:
  web:
    image: lazari-web:latest            # was crm-voic:latest
    command: ["/app/entrypoint.sh"]
    env_file:
      - .env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
    networks:
      - network_swarm_public   # Traefik (overlay externa, compartilhada)
      - lazari_internal        # fala com o Postgres dedicado (isolada)   # was crm_internal
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health/ || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 180s       # boot = collectstatic + migrate + seed; NÃO baixar (Pitfall 5)
    deploy:
      replicas: 1
      restart_policy: { condition: any, delay: 10s }
```

**Traefik router labels — service level** (crm-voic lines 40-54) — re-brand hosts to `www`/`app` Lazari:
```yaml
      labels:
        - "traefik.enable=true"
        - "traefik.docker.network=network_swarm_public"
        # DNS (nuvem cinza) do www./app. PRECISA existir ANTES do deploy senão o SAN falha no Let's Encrypt.
        - "traefik.http.routers.lazari_web.rule=Host(`www.lazaricapital.com.br`)"
        - "traefik.http.routers.lazari_web.entrypoints=websecure"
        - "traefik.http.routers.lazari_web.service=lazari_web"
        - "traefik.http.routers.lazari_web.tls=true"
        - "traefik.http.routers.lazari_web.tls.certresolver=letsencryptresolver"
        - "traefik.http.services.lazari_web.loadbalancer.server.port=8000"
        - "traefik.http.services.lazari_web.loadbalancer.passHostHeader=true"
```

**301 redirect for the old domain** — mirror the `pl_apex` pattern (crm-voic lines 55-65). Alojar nas labels do `web` (RESEARCH Pattern 3); note the `$${1}` escape:
```yaml
        - "traefik.http.routers.money_old.rule=Host(`money.voictech.com.br`)"
        - "traefik.http.routers.money_old.entrypoints=websecure"
        - "traefik.http.routers.money_old.service=lazari_web"
        - "traefik.http.routers.money_old.tls=true"
        - "traefik.http.routers.money_old.tls.certresolver=letsencryptresolver"
        - "traefik.http.routers.money_old.middlewares=money_301"
        - "traefik.http.middlewares.money_301.redirectregex.regex=^https?://[^/]+/(.*)"
        - "traefik.http.middlewares.money_301.redirectregex.replacement=https://app.lazaricapital.com.br/$${1}"
        - "traefik.http.middlewares.money_301.redirectregex.permanent=true"
```

**`worker` service — MUST FIX** (crm-voic lines 75-93): the herdado command calls `processar_fila_capi` (pruned in Phase 1 → crash-loop). Keep only `processar_billing` or omit the worker (Open Q#4):
```yaml
  worker:
    image: lazari-web:latest
    command: >
      sh -c "while true; do
        if [ \"$$(date +%H%M)\" = \"0300\" ]; then python manage.py processar_billing; fi;
        sleep 60;
      done"
    env_file: [.env]
    environment: { DJANGO_SETTINGS_MODULE: config.settings.prod }
    networks: [lazari_internal]
    deploy: { replicas: 1, restart_policy: { condition: any, delay: 10s } }
```

**`db` service** (crm-voic lines 95-112) — copy verbatim, rename volume/network:
```yaml
  db:
    image: postgres:17-alpine
    env_file: [.env]
    volumes:
      - lazari_postgres_data:/var/lib/postgresql/data/   # was crm_postgres_data
    networks: [lazari_internal]           # SÓ interna — nunca ao Traefik/internet
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy: { replicas: 1, restart_policy: { condition: any } }
```

**`money` service — fold in from `analista_dividendos/stack.yml`** (see that file lines 4-38) with the FQDN fix (RESEARCH Pattern 1):
```yaml
  money:
    image: money:latest
    networks: [network_swarm_public]      # + lazari_internal só se precisar do gate FQDN
    deploy:
      replicas: 1
      labels:
        - traefik.enable=true
        - traefik.docker.network=network_swarm_public
        - traefik.http.routers.money.rule=Host(`app.lazaricapital.com.br`)   # was money.voictech.com.br
        - traefik.http.routers.money.entrypoints=websecure
        - traefik.http.routers.money.tls=true
        - traefik.http.routers.money.tls.certresolver=letsencryptresolver
        - traefik.http.services.money.loadbalancer.server.port=8501
        # FQDN do serviço Swarm (era http://web:8000 → não resolve) — Pitfall 1
        - traefik.http.middlewares.lazari-gate.forwardauth.address=http://lazari_web:8000/gate/
        - traefik.http.middlewares.lazari-gate.forwardauth.authResponseHeaders=X-User-Email
        - traefik.http.middlewares.lazari-gate.forwardauth.trustForwardHeader=true
        - traefik.http.routers.money.middlewares=lazari-gate
```

**volumes/networks footer** (crm-voic lines 114-123) — rename to `lazari_*`:
```yaml
volumes:
  lazari_postgres_data:
networks:
  network_swarm_public:
    external: true
  lazari_internal:
    driver: overlay
```

---

### `/opt/lazari-capital/.env` (config/secrets, VPS-only, chmod 600)

**Analog:** `/Users/giovanelazari/projects/crm-voic/.env.prod.example` (exact structure).

**read_first:** `/Users/giovanelazari/projects/crm-voic/.env.prod.example` (full, 80 lines); `/Users/giovanelazari/projects/lazari-capital/config/settings/prod.py` (to know which vars are consumed).

**Core pattern** (crm-voic `.env.prod.example` lines 14-79) — re-branded, with the three phase-critical gotchas flagged in RESEARCH (`$$` escaping, prod Asaas base URL, FQDN DB host):
```bash
SECRET_KEY=<python -c "import secrets;print(secrets.token_urlsafe(64))">   # NOVO em prod
DEBUG=False
# localhost/127.0.0.1 OBRIGATÓRIOS — healthcheck bate em localhost:8000/health/ (Pitfall 5)
ALLOWED_HOSTS=www.lazaricapital.com.br,app.lazaricapital.com.br,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://www.lazaricapital.com.br,https://app.lazaricapital.com.br
SESSION_COOKIE_DOMAIN=.lazaricapital.com.br   # D-05 — confirmar domínio real (Open Q#1)
CSRF_COOKIE_DOMAIN=.lazaricapital.com.br

# HOST = nome do serviço Postgres no Swarm = stack_serviço = lazari_db (NÃO `db`) — crm .env L31-34
DATABASE_URL=postgres://lazari_user:<senha>@lazari_db:5432/lazari
POSTGRES_DB=lazari
POSTGRES_USER=lazari_user
POSTGRES_PASSWORD=<senha>
GUNICORN_WORKERS=5

RESEND_API_KEY=re_...
DEFAULT_FROM_EMAIL=no-reply@lazaricapital.com.br

ASAAS_API_KEY=$$aact_prod_...     # ESCAPAR o $ inicial com $$ (django-environ interpola $) — Pitfall 4
ASAAS_BASE_URL=https://api.asaas.com/v3   # PROD (default do base.py é sandbox) — virada acontece aqui
ASAAS_WEBHOOK_TOKEN=<token do painel Asaas prod>

# Backup (crm .env L57-62)
CRM_DB_CONTAINER=lazari_db          # confirmar nome real: docker ps --format '{{.Names}}' | grep db
CRM_BACKUP_DIR=/backups
```

---

### `~/projects/lazari-capital/config/settings/prod.py` (config, request-response)

**Analog:** itself — already implements the parent-domain cookie, `SECURE_PROXY_SSL_HEADER`, HSTS and Resend SMTP. **Minimal or no code change**; the phase work is driving `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` from the `.env` (never trust the hard-coded default).

**read_first:** `/Users/giovanelazari/projects/lazari-capital/config/settings/prod.py` (full, 65 lines).

**Cookie / proxy block already present** (prod.py lines 40-49) — the default is `.lazaritechcapital.com.br`; the `.env` MUST override it with the real domain (Open Q#1, Pitfall 2):
```python
SESSION_COOKIE_DOMAIN = env('SESSION_COOKIE_DOMAIN', default='.lazaritechcapital.com.br')
CSRF_COOKIE_DOMAIN = env('CSRF_COOKIE_DOMAIN', default='.lazaritechcapital.com.br')
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')   # MANTER — sem isto o gate em HTTP interno não vê HTTPS
SECURE_SSL_REDIRECT = True
```
**CSRF_TRUSTED_ORIGINS** (prod.py lines 9-12) derives from `ALLOWED_HOSTS` but is overridable via env — set it explicitly in `.env` for the www/app pair.
**Resend SMTP** (prod.py lines 58-64) already wired; only needs `RESEND_API_KEY`/`DEFAULT_FROM_EMAIL` in `.env` (D-10).

---

### `~/projects/lazari-capital/entrypoint.sh` (config/boot, batch)

**Analog:** itself (= crm-voic entrypoint pattern). **No change expected** — the Plano PRO seed runs automatically via `migrate` (RESEARCH Pattern 4: `apps/billing/migrations/0002_seed_plano_pro.py`, idempotent `update_or_create`). Do NOT add a parallel management command.

**read_first:** `/Users/giovanelazari/projects/lazari-capital/entrypoint.sh` (full, 25 lines).

**Boot sequence** (entrypoint.sh lines 9-24) — collectstatic → migrate (runs the seed) → gunicorn:
```bash
python manage.py collectstatic --noinput
python manage.py migrate --noinput           # roda a data migration 0002 (seed Plano PRO) — idempotente
python manage.py createcachetable --no-color 2>/dev/null || true
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-5} --timeout 120 ...
```

---

### `~/projects/lazari-capital/Dockerfile` (config/build, batch)

**Analog:** itself. Likely **no change** for go-live (builds `lazari-web:latest`, Tailwind CSS at build time, `curl` for healthcheck).

**read_first:** `/Users/giovanelazari/projects/lazari-capital/Dockerfile` (full, 31 lines).

Note: the build-time placeholders (SECRET_KEY/DATABASE_URL/CAPI_ENCRYPTION_KEY, lines 23-28) are discardable — real values come from `.env` at runtime. Don't confuse them with prod secrets.

---

### `analista_dividendos/stack.yml` (config/deploy, request-response + WS)

**Analog:** itself + crm-voic labels. **Decision point (Claude's Discretion / RESEARCH primary rec):** either (a) keep this standalone stack but change host + FQDN + shared network, or (b) fold the `money` block into the unified `lazari` stack and retire this file. RESEARCH recommends (b) to avoid the cross-stack DNS bug.

**read_first:** `/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos/stack.yml` (full, 43 lines).

**Two mandatory edits regardless of (a)/(b)** — the current file (lines 23, 35) still targets the old host and short-name gate:
```yaml
# stack.yml line 23 — CHANGE host
- traefik.http.routers.money.rule=Host(`app.lazaricapital.com.br`)   # was money.voictech.com.br
# stack.yml line 35 — CHANGE to FQDN (short `web` may not resolve in Swarm) — Pitfall 1
- traefik.http.middlewares.lazari-gate.forwardauth.address=http://lazari_web:8000/gate/   # was http://web:8000/gate/
```
The **no-public-port** invariant (stack.yml lines 7-14, no `ports:` block) is correct and MUST be preserved (anti-spoof of `X-User-Email`).

---

### `analista_dividendos/.streamlit/config.toml` (config, streaming/WS) — FALLBACK ONLY

**Analog:** itself. **Only touch if the WS smoke fails** ("Please wait…" loop / WS 1006). Default behavior (RESEARCH Pattern 2) needs no WS config — forwardAuth authenticates only the HTTP upgrade handshake.

**read_first:** `/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos/.streamlit/config.toml` (full, 9 lines — currently only `[browser]` + `[theme]`).

**Fallback to append (conditional)** — requires `docker build -t money:latest` rebuild:
```toml
[server]
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false
```

---

### `~/projects/lazari-capital/scripts/backup.sh` (utility, file-I/O)

**Analog:** `/Users/giovanelazari/projects/crm-voic/scripts/backup.sh` (exact) + `restore_verify.sh` sibling.

**read_first:** `/Users/giovanelazari/projects/crm-voic/scripts/backup.sh` (full, 26 lines).

**Core pattern** (backup.sh lines 11-25) — copy, drive `DB_CONTAINER` from `.env` (`CRM_DB_CONTAINER=lazari_db`), register in root crontab `0 2 * * *`:
```bash
DB_CONTAINER="${CRM_DB_CONTAINER:-lazari_db}"     # confirmar nome real do container Swarm
BACKUP_FILE="${BACKUP_DIR:-/backups}/lazari-$(date +%F).sql.gz"
docker exec "${DB_CONTAINER}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_FILE}"
find "${BACKUP_DIR}" -name "lazari-*.sql.gz" -mtime +7 -delete   # retenção 7 dias
```

---

## Shared Patterns

### Swarm single-node deploy (no registry)
**Source:** `/Users/giovanelazari/projects/crm-voic/docker-stack.yml` lines 6-11 (header) + comment on `build:`.
**Apply to:** both stacks (`lazari-web:latest`, `money:latest`).
```bash
docker build -t lazari-web:latest .   # em /opt/lazari-capital (repo Django)
docker build -t money:latest .        # no repo analista_dividendos
docker stack deploy -c docker-stack.yml lazari
```
Images are built LOCALLY on the VPS before deploy (`build:` is ignored by `stack deploy`).

### Traefik service-level labels + gray-cloud-DNS-before-deploy
**Source:** crm-voic/docker-stack.yml lines 40-54 (labels at SERVICE level, not container) + line 46-47 comment.
**Apply to:** every service with a router (`web`, `money`, 301). Swarm provider ignores container labels. DNS (nuvem cinza / DNS-only) MUST exist before `stack deploy` or Let's Encrypt SAN emission fails (Pitfall 3, D-06).

### Secrets via `.env` env_file (D-09, never docker secrets)
**Source:** crm-voic/docker-stack.yml lines 18-20 (`env_file: - .env`) + `.env.prod.example`.
**Apply to:** `web`, `worker`, `db`. `.env` lives at `/opt/lazari-capital/.env` (chmod 600), outside git. Postgres creds in `.env` must match both `DATABASE_URL` and `POSTGRES_*`.

### Postgres isolated on internal overlay (never exposed)
**Source:** crm-voic/docker-stack.yml lines 102-103 + 121-123 (`db` only on `crm_internal`, `driver: overlay`).
**Apply to:** `db` service → rename to `lazari_internal`. `db` never joins `network_swarm_public`.

### `$$` escaping for `$` in stack labels and `.env`
**Source:** crm-voic/docker-stack.yml line 56/64 (`$${1}`) and `.env` Asaas key (base.py L31 doc).
**Apply to:** the 301 `redirectregex.replacement` (`$${1}`) AND the `ASAAS_API_KEY` (`$$aact_prod_...`). Pitfall 4.

## No Analog Found

| File / Item | Role | Data Flow | Reason |
|-------------|------|-----------|--------|
| E2E pago live exercise | test | request-response + event-driven | Not a new file — reuses Phase 2 suite (`test_webhook_ciclo.py`, GateView/billing tests). Novelty is running it against live Traefik+gate+Streamlit + 1 real R$19,90 smoke (D-01/D-02). See RESEARCH "E2E pago — estratégia". Planner should read `lazari-capital/apps/billing/tests/` (Phase 2) as the base. |
| Landing mínima de vendas em `www` | component/template | request-response | Django templates that reuse Phase 1 Lazari Capital screens (Preline/Tailwind, D-08). Not inspected in this pass — planner should read the Phase 1 templates under `lazari-capital/` (marketing/landing views + `templates/`) as the analog. Intentionally enxuta (no SEO/copywriting this phase). |

## Metadata

**Analog search scope:** `/Users/giovanelazari/projects/crm-voic` (reference deploy), `/Users/giovanelazari/projects/lazari-capital` (Django front), `/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos` (Streamlit engine).
**Files scanned/read:** crm-voic/docker-stack.yml, crm-voic/.env.prod.example, crm-voic/scripts/backup.sh, lazari-capital/docker-stack.yml, lazari-capital/entrypoint.sh, lazari-capital/Dockerfile, lazari-capital/config/settings/prod.py, analista_dividendos/stack.yml, analista_dividendos/.streamlit/config.toml.
**Pattern extraction date:** 2026-07-08
