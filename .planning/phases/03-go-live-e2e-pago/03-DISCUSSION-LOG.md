# Phase 3: Go-live E2E pago - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-08
**Phase:** 3-Go-live E2E pago
**Areas discussed:** Teste E2E pago, Domínios & cutover, Porta de entrada, Segredos & produção

---

## Teste E2E pago

| Option | Description | Selected |
|--------|-------------|----------|
| Asaas sandbox p/ o fluxo + 1 smoke real | E2E no sandbox (repetível/CI) + 1 cobrança real R$19,90 com estorno como smoke final | ✓ |
| Só sandbox Asaas | Todo E2E no sandbox, nunca cobrança real; não prova chaves de produção | |
| Cobrança real ponta a ponta | E2E inteiro com cobrança real; mais fiel, frágil p/ repetir/CI | |

**User's choice:** Asaas sandbox p/ o fluxo + 1 smoke real
**Notes:** Cobre o código (sandbox, automatizável) E valida as chaves/checkout de produção (smoke manual R$19,90, com estorno).

---

## Domínios & cutover

| Option | Description | Selected |
|--------|-------------|----------|
| app=Streamlit, www=Django; money→301 | Streamlit em app., Django em www., money.voictech→301, cookie no parent .lazaricapital.com.br | ✓ |
| Tudo em app + apex, sem www separado | Django e Streamlit no mesmo host; cookie same-host, mais simples | |
| Manter money.voictech.com.br | Reusar domínio atual só adicionando o gate; não estreia a marca | |

**User's choice:** app=Streamlit, www=Django; money→301
**Notes:** Implica `SESSION_COOKIE_DOMAIN=.lazaricapital.com.br` p/ o gate no host app. ler a sessão emitida no host www.

---

## Porta de entrada (escopo do go-live)

| Option | Description | Selected |
|--------|-------------|----------|
| Só cadastro/login (sem landing de vendas) | Entrega só o funil; landing de vendas fica pós-v2.0 | |
| Cadastro + landing mínima de vendas | Funil + landing simples (valor/preço/CTA/disclaimer) em www | ✓ |

**User's choice:** Cadastro + landing mínima de vendas
**Notes:** Landing enxuta, herda a marca das telas da Phase 1; marketing/SEO completo fica p/ fase própria.

---

## Segredos & produção

| Option | Description | Selected |
|--------|-------------|----------|
| Padrão crm-voic: .env em /opt via SSH | .env fora do git em /opt/lazari-capital, injetado via env_file (chaves Asaas prod, Resend, DATABASE_URL) | ✓ |
| Docker secrets / Swarm secrets | docker secret lido de /run/secrets; mais seguro, foge do padrão crm-voic | |

**User's choice:** Padrão crm-voic: .env em /opt via SSH
**Notes:** Virada de chaves Asaas sandbox→produção acontece no deploy; Resend/SMTP prod porque o e-mail de verificação é caminho crítico do trial.

---

## Claude's Discretion

- Abordagem técnica dos **websockets do Streamlit atrás do forward-auth** (critério #3) — researcher/planner.
- Estrutura exata dos arquivos de deploy (adaptar docker-stack.yml herdado), ordem de subida, entrypoint (migrate/collectstatic/seed do Plano PRO).
- Local do redirect 301 do money.voictech.com.br e mecânica do apex.
- Postgres como serviço no stack vs instância existente.

## Deferred Ideas

- Landing de marketing/SEO completa → pós-v2.0.
- Múltiplos planos/tiers, plano anual, cupons, afiliados, OAuth Google → Future.
- Docker secrets → reavaliar depois.
- Migração do front p/ React+Vite → Future.
- Poda do multi-tenant dormante → reavaliar.
