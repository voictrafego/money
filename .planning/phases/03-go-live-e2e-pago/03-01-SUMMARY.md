---
phase: 03-go-live-e2e-pago
plan: 01
subsystem: ui
tags: [django, landing, marketing, tailwind, preline, lazari-capital, re-brand]

# Dependency graph
requires:
  - "fork crm-voic: templates/marketing/{landing,base_marketing}.html + LandingPageView (MARKETING_HOSTS/app_base_url) — reusados, só o conteúdo trocou"
  - "02-01: Plano PRO R$ 19,90 (seed 0002) — preço exibido na landing"
provides:
  - "templates/marketing/landing.html re-brandado para Lazari Capital: hero de análise de dividendos da B3 (garimpo por múltiplos + preço-teto por DDM + indicadores de tendência), plano único PRO R$ 19,90/mês (trial 7d sem cartão), disclaimer educacional (CVM), CTAs Criar conta grátis (/signup/) + Entrar (/entrar/)"
  - "templates/marketing/base_marketing.html: <title>/<meta description> Lazari Capital"
  - "apps/users/tests/test_landing.py: regressão atualizada (22 testes verdes) cobrindo marca, headline, recursos do método, preço PRO, disclaimer, ausência de Pocket Leads/Kanban, split vitrine×app por host"
affects: [03-04-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Landing estática (D-08): mesma estrutura Tailwind/Preline/Alpine, zero HTMX/sortable/kanban; só o conteúdo re-brandou"
    - "CTAs via {{ app_base_url }} (não hard-code de domínio) — dev usa hrefs relativos, prod injeta https://www.lazaricapital.com.br"
    - "Plano único PRO (não 3 tiers herdados) — landing reflete o único Plano semeado (02-01)"

key-files:
  created: []
  modified:
    - "~/projects/lazari-capital/templates/marketing/landing.html"
    - "~/projects/lazari-capital/templates/marketing/base_marketing.html"
    - "~/projects/lazari-capital/apps/users/tests/test_landing.py"

key-decisions:
  - "Disclaimer educacional na landing: 'software educacional — não constitui recomendação de investimento (CVM)' (LEGAL-01/D-07)"
  - "Removidos os 3 planos (R$47/97/127) → 1 card PRO R$ 19,90; removido ?plano= dos CTAs (plano único)"
  - "Removido o import ocioso apps.billing.models.Plano do teste (não mais usado)"
  - "Rebrand dos hosts de teste pocketleads→lazaricapital no split vitrine×app (coerência; funcionalmente MARKETING_HOSTS aceita qualquer host)"

patterns-established:
  - "Re-brand de template herdado: preservar layout/JS, trocar só copy + marca + preço; manter {{ app_base_url }}"

requirements-completed: [OPS-01]

# Metrics
duration: ~12min
completed: 2026-07-08
---

# Phase 3 · Plan 01: Landing Lazari Capital Summary

**A vitrine pública em `/` deixou de mostrar o CRM Pocket Leads e passou a apresentar a Lazari Capital — análise de ações de dividendos da B3 pelo método do livro, plano PRO R$ 19,90/mês, com disclaimer educacional (CVM) e CTAs para cadastro/login.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-07-08
- **Tasks:** 2/2 (landing + teste)
- **Files modified:** 3

## Accomplishments

- **Task 1** — `landing.html` + `base_marketing.html` reescritos para a marca Lazari Capital: hero de dividendos, seção de 6 recursos do método (garimpo por múltiplos, preço-teto por DDM, indicadores de tendência, números consistentes, dados gratuitos, fiel ao livro), card único PRO R$ 19,90/mês (trial 7d sem cartão), disclaimer educacional, CTAs `Criar conta grátis`→`/signup/` e `Entrar`→`/entrar/`. Zero conteúdo de CRM (Pocket Leads/Kanban/pipeline/leads).
- **Task 2** — `test_landing.py` reescrito: 22 testes verdes cobrindo marca, headline, recursos, preço PRO, disclaimer educacional, ausência de conteúdo herdado, split vitrine×app por host e regressão de rota autenticado→`/painel/`.

## Verification

- `grep -Ec "Pocket Leads|Kanban|pipeline|leads" landing.html` == 0
- `grep -Ec "R\$ 19,90|Lazari Capital" landing.html` == 5 (>= 2)
- landing contém disclaimer educacional + `{{ app_base_url }}/signup/` e `/entrar/`
- `pytest apps/users/tests/test_landing.py -q` → **22 passed**

## Notes for downstream

- A landing entra na imagem `lazari-web:latest` que o deploy (03-04) builda — nada extra a wire.
- `base_marketing.html` mantém um comentário técnico (invariante "sem htmx/sortable/kanban") — intencional, não é conteúdo de CRM.

## Self-Check: PASSED
