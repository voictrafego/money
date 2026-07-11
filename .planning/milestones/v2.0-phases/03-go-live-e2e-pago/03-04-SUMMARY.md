---
phase: 03-go-live-e2e-pago
plan: 04
subsystem: infra
tags: [docker-swarm, traefik, forwardauth, letsencrypt, streamlit, django, deploy, cutover, backup, lazari-capital]

# Dependency graph
requires:
  - "03-01: landing Lazari Capital (na imagem lazari-web:latest)"
  - "03-02: .env prod (chmod 600) + DNS grey-cloud + prod.py cookie domain"
  - "03-03: docker-stack.yml unificado `lazari` + backup.sh + engine stack.yml"
provides:
  - "Stack `lazari` no ar na VPS (31.97.130.40): lazari_web + lazari_db + lazari_money + lazari_worker, todos 1/1 healthy"
  - "TLS Let's Encrypt válido em www.lazaricapital.com.br (Django) e app.lazaricapital.com.br (Streamlit gated)"
  - "Gate forwardAuth ao vivo: anônimo no app → 302 https://www.lazaricapital.com.br/entrar/; logado+ativo → Analista (Streamlit) com WS 101 sem loop"
  - "301/308 money.voictech.com.br → app.lazaricapital.com.br (cutover do money v1.7 concluído)"
  - "Cron de backup diário do lazari_db (0 2 * * *) + dump validado"
  - "Pós-login vai ao produto (app. Streamlit), não ao /painel/ placeholder do fork crm-voic"
affects: [03-05-e2e]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deploy Swarm single-node sem registry: build :latest local → docker stack deploy (nunca --remove-orphans; n8n é orphan)"
    - "Cutover por remoção do stack antigo só após o novo validado (Pitfall 6)"
    - "Django atrás de proxy: USE_X_FORWARDED_HOST + SECURE_PROXY_SSL_HEADER para o forwardAuth"
    - "Redirects cross-host (gate, email, pós-login) usam URL absoluta do host correto (app/www)"

key-files:
  created:
    - "VPS: /opt/lazari-capital (repo Django rsyncado) + imagens lazari-web:latest, money:latest"
    - "VPS: /backups/lazari-*.sql.gz + crontab root (backup diário)"
  modified:
    - "~/projects/lazari-capital/config/settings/prod.py (USE_X_FORWARDED_HOST)"
    - "~/projects/lazari-capital/config/settings/base.py (STREAMLIT_APP_URL + LOGIN_REDIRECT_URL)"
    - "~/projects/lazari-capital/apps/gate/views.py (redirect www absoluto)"
    - "~/projects/lazari-capital/apps/billing/services.py (link de verificação absoluto)"
    - "~/projects/lazari-capital/apps/users/views.py (landing-autenticada → app)"
    - "~/projects/lazari-capital/scripts/backup.sh (resolução dinâmica do container no Swarm)"
    - "/opt/lazari-capital/.env (Asaas $ único; STREAMLIT_APP_URL)"

key-decisions:
  - "Engine money rebuildado do /root/money (app.py atual) e servido pelo stack lazari (money:latest); stack money v1.7 antigo removido no cutover"
  - "Resend exige domínio verificado: lazaricapital.com.br verificado no painel Resend (DNS no Cloudflare) — sem isso o e-mail de verificação dá SMTP 550 e o trial não arma"

patterns-established:
  - "Todo redirect que sai do host do request (gate→login, email→verificar, login→app) precisa de URL absoluta do host de destino, senão quebra/loop atrás do Traefik+forwardAuth"

requirements-completed: [OPS-01]

# Metrics
duration: ~2h (deploy ao vivo + 6 fixes descobertos em produção)
completed: 2026-07-08
---

# Phase 3 · Plan 04: Deploy + cutover Lazari Capital Summary

**A Lazari Capital está NO AR: `www.lazaricapital.com.br` (Django/landing/auth/billing) + `app.lazaricapital.com.br` (Analista de Ações em Streamlit, atrás do gate forwardAuth), com TLS Let's Encrypt, cutover do domínio antigo (301) concluído e backup diário agendado. Critérios #1 (produto no ar) e #3 (websockets atrás do gate) atendidos.**

## Accomplishments

- **Build + deploy** — `lazari-web:latest` (Django) e `money:latest` (engine) buildados na VPS; `docker stack deploy lazari` sobe web/db/money/worker 1/1 healthy; migrate rodou o seed do Plano PRO R$19,90; smoke do gate interno (`money → http://lazari_web:8000/health/`) = `ok`.
- **TLS + gate ao vivo** — Let's Encrypt válido em www e app; anônimo no `app.` → 302 login no `www.`; usuário logado+trial → Analista (Streamlit) carrega e interage sem loop (WS 101).
- **Cutover** — stack `money` v1.7 antigo removido (após o novo validado); `money.voictech.com.br` → 301/308 → `app.`; n8n/crm-voic intactos (sem `--remove-orphans`).
- **Backup** — `backup.sh` resolve o container Swarm dinamicamente; run manual gerou dump não-vazio; cron `0 2 * * *` registrado.

## Deviations / bugs achados e corrigidos AO VIVO (todos commitados no repo lazari-capital)

1. **Asaas `$$`→`$`** (03-02): `env_file` não interpola `$`; a chave chegava dobrada → 401. Corrigido p/ `$` único.
2. **`USE_X_FORWARDED_HOST=True`** (prod.py): o Traefik chama o gate com `Host: lazari_web:8000` (fora do ALLOWED_HOSTS) → DisallowedHost 400 e o gate nunca rodava. Confiar no `X-Forwarded-Host` do Traefik resolve.
3. **Gate redireciona ao www por URL absoluta** (gate/views.py): com app/www em hosts separados, Location relativo caía no próprio `app.` (gated) → loop, e o Traefik absolutizava contra o host interno. Prefixa `APP_BASE_URL`.
4. **Link de verificação de e-mail absoluto** (billing/services.py): o e-mail vinha com path relativo, não clicável. Prefixa `APP_BASE_URL`.
5. **Pós-login vai ao produto** (base.py/users/views.py): `LOGIN_REDIRECT_URL` e a landing-autenticada iam ao `/painel/` (placeholder do CRM do fork) em vez do Streamlit. Agora vão a `STREAMLIT_APP_URL` (app.).
6. **`backup.sh` resolve container no Swarm** (scripts/backup.sh): nome real é `lazari_db.1.<taskid>` (muda a cada deploy); resolve por filtro em vez de nome fixo.
7. **Resend domain verify**: `lazaricapital.com.br` verificado no Resend (senão SMTP 550 e trial não arma).

## Notes for downstream (03-05)

- Webhook Asaas prod deve apontar p/ `https://www.lazaricapital.com.br/billing/webhook/` com o `ASAAS_WEBHOOK_TOKEN` do `.env`.
- Verificação de e-mail arma o trial (status ATIVO + trial_ate hoje+7). CRM dormente do fork ainda existe (poda = pós-v2.0).

## Self-Check: PASSED
