---
phase: 03-go-live-e2e-pago
plan: 02
subsystem: infra
tags: [dns, cloudflare, env, secrets, asaas, resend, prod-settings, lazari-capital]

# Dependency graph
requires:
  - "fork crm-voic: config/settings/{base,prod}.py + .env.prod.example — base dos segredos/hosts"
provides:
  - "DNS grey-cloud confirmado: www/app.lazaricapital.com.br → 31.97.130.40 (dig)"
  - "/opt/lazari-capital/.env de produção (chmod 600, fora do git): Asaas prod, Resend prod, DATABASE_URL, SECRET_KEY novo, cookie parent-domain, ALLOWED_HOSTS com localhost, STREAMLIT_APP_URL"
  - "config/settings/prod.py: default de SESSION_COOKIE_DOMAIN/CSRF_COOKIE_DOMAIN corrigido p/ .lazaricapital.com.br"
affects: [03-04-deploy, 03-05-e2e]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Segredos via .env em /opt/lazari-capital (chmod 600, env_file), NUNCA no git (D-09)"

key-files:
  created:
    - "/opt/lazari-capital/.env (VPS-only)"
  modified:
    - "~/projects/lazari-capital/config/settings/prod.py"

key-decisions:
  - "DESVIO CRÍTICO vs Pitfall 4 do plano: env_file do docker NÃO interpola `$` (ao contrário de `environment:`). A chave Asaas deve ir com UM `$` (ASAAS_API_KEY=$aact_prod_...), não `$$`. O `$$` do plano dobrava a chave no runtime → 401. Confirmado contra o crm-voic (prod) que usa `$` único. Corrigido no .env."
  - "DNS já estava resolvendo grey-cloud (dig retorna a VPS, não IP do Cloudflare) — Task 1 verificada por dig + confirmação visual do usuário"
  - "STREAMLIT_APP_URL=https://app.lazaricapital.com.br adicionado ao .env (usado pelo redirect pós-login — ver 03-04)"

patterns-established:
  - "env_file é literal: escapar `$` só vale para valores interpolados no compose file (labels/command), nunca no .env"

requirements-completed: [OPS-01]

# Metrics
duration: ~25min (inclui troubleshooting Resend/Asaas ao vivo)
completed: 2026-07-08
---

# Phase 3 · Plan 02: Prep de produção Summary

**DNS grey-cloud confirmado, `prod.py` com o domínio de cookie correto, e o `.env` de produção criado na VPS (chmod 600, fora do git) com os segredos reais de Asaas/Resend/DB — com a correção crítica do `$` da chave Asaas que o plano tinha invertido.**

## Accomplishments

- **Task 1 (DNS)** — `dig www/app.lazaricapital.com.br` → `31.97.130.40` (grey-cloud, o `dig` retorna a VPS e não IP do Cloudflare). `money.voictech.com.br` ainda resolve (p/ o 301).
- **Task 2 (prod.py)** — default de `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` `.lazaritechcapital`→`.lazaricapital.com.br`. `test_deploy_check` verde.
- **Task 3 (.env)** — `/opt/lazari-capital/.env` criado (chmod 600) com SECRET_KEY novo, DATABASE_URL→`lazari_db`, ALLOWED_HOSTS c/ localhost, cookie parent-domain, Asaas prod, Resend prod, webhook token, STREAMLIT_APP_URL. Segredos preenchidos pelo usuário direto na VPS (nunca pelo chat).

## Deviations (importante)

- **Asaas `$$` → `$`**: o plano mandava escapar `$`→`$$` (Pitfall 4), mas isso vale só para valores interpolados no *compose file*. `env_file` é literal → `$$aact` chegava dobrado no container e a API Asaas daria 401. Corrigido para `$aact_prod_...` (um `$`), confirmado contra o crm-voic em produção.

## Self-Check: PASSED
