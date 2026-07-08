# Phase 1: Fundação — Cadastro, Login, Gate e Trial - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-07
**Phase:** 1-Fundação — Cadastro, Login, Gate e Trial
**Areas discussed:** Modelo de conta (schema), Scaffold do repo Django, Telas de entrada + cadastro, Trial expirado na Fase 1

---

## Modelo de conta (schema)

| Option | Description | Selected |
|--------|-------------|----------|
| Reusar Conta+User+Assinatura do crm-voic | Conta shell 1:1, gate lê Conta.status/trial_ate, billing copiado 1:1 na Fase 2 | ✓ |
| Achatar no User (B2C puro) | status/trial/asaas no próprio User, sem tenant; billing da Fase 2 vira retrabalho | |

**User's choice:** Reusar Conta+User+Assinatura do crm-voic (recomendado)
**Notes:** Aceita o custo do maquinário multi-tenant ocioso em troca de reusar o billing sem reescrever.

---

## Scaffold do repo Django

| Option | Description | Selected |
|--------|-------------|----------|
| Fork-and-prune do crm-voic | Copia tudo, remove leads/dashboard/import/campos; mantém accounts/users/billing/webhooks/core + settings/Docker/Traefik/Resend/pytest | ✓ |
| startproject limpo | Projeto novo trazendo só os apps; refaz settings/Docker/Traefik/e-mail/CI | |

**User's choice:** Fork-and-prune do crm-voic (recomendado)
**Notes:** Preserva a infra que já funciona; poda a cruft B2B.

---

## Telas de entrada + cadastro

| Option | Description | Selected |
|--------|-------------|----------|
| Nome+email+senha, trial imediato, verifica depois | Menos fricção; verificação não bloqueia | |
| Verificar e-mail antes de liberar o trial | Confirma e-mail (link) antes de o trial começar; mais seguro, mais fricção | ✓ |
| Só email+senha, trial imediato | Mínimo, sem nome | |

**User's choice:** Verificar e-mail antes de liberar o trial
**Notes:** Pareado com nome+email+senha (Claude): nome é útil pro Asaas/personalização; usuário confirmou ao fechar o contexto. Coloca Resend/SMTP no caminho crítico da Fase 1. Visual Preline branded (crm-voic) aceito por não-veto.

---

## Trial expirado na Fase 1

| Option | Description | Selected |
|--------|-------------|----------|
| Tela "trial acabou" placeholder | Gate bloqueia + página com botão [Assinar] (aviso na Fase 1, checkout Asaas na Fase 2) | ✓ |
| Só bloqueia e volta pro login | Nega acesso + redirect login com aviso | |

**User's choice:** Tela "trial acabou" placeholder (recomendado)
**Notes:** Deixa o ponto de conversão pronto no lugar.

---

## Claude's Discretion

- Nomes de rotas/URLs, estrutura de templates, backend de e-mail em dev, organização de settings.
- Implementação exata do endpoint forward-auth (view/middleware).
- Pareamento nome+email+senha com a verificação obrigatória (confirmado pelo usuário).

## Deferred Ideas

- Cobrança Asaas + webhooks + página de conta/cancelamento → Fase 2.
- Deploy integrado + E2E pago → Fase 3.
- Landing page de marketing da marca → Future.
- OAuth (Google), múltiplos planos/tiers, plano anual/cupons/afiliados → Future.
- Poda do maquinário multi-tenant se o B2C nunca precisar de equipes → reavaliar.
