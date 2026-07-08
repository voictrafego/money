# Requirements: Lazari Capital — v2.0 Comercialização

**Defined:** 2026-07-07 (reabertura; requisitos originais de 2026-06-28 em `milestones/v2.0-REQUIREMENTS.md`)
**Core Value:** O produto cobra de forma confiável e o acesso reflete fielmente o status de assinatura — quem paga (ou está em trial) entra; quem não tem assinatura ativa não entra — sem nunca prometer recomendação de investimento.
**Milestone goal:** Transformar o app de usuário único num produto cobrável sob a marca **Lazari Capital**: cadastro self-serve, trial de 7 dias → assinatura mensal (Asaas), gate de acesso e multiusuário, posicionado como **software educacional (sem recomendação)**.

**Arquitetura (decidida):** **Gateway híbrido com Django.** Projeto Django novo (repo separado,
`~/projects/lazari-capital`) espelha os apps do `crm-voic` — `accounts`, `users` (User custom com
email como USERNAME_FIELD, sem username), `billing` (`asaas_client.py`, `cupom_service.py`),
`webhooks` (idempotentes, **nativos Django, sem n8n**). O engine de valuation continua em
**Streamlit intacto atrás de um gate**. Gate = **Traefik forward-auth**: o Django valida
sessão + status de assinatura e injeta um header `X-User-Email` confiável no Streamlit. Fonte de
verdade de contas/assinaturas no **Postgres**. Asaas em **conta e chave próprias**. Stack Django
5.2 + HTMX + Alpine + Tailwind/Preline + Postgres, Docker/Traefik na VPS.

## v2.0 Requirements

### Auth & Acesso (AUTH)

- [ ] **AUTH-01**: Usuário faz **cadastro self-serve** (email + senha) e login numa camada Django própria, emitindo uma sessão que governa o acesso ao app.
- [ ] **AUTH-02**: O app Streamlit só é acessível **autenticado E com trial/assinatura ativa** — acesso direto à URL do Streamlit sem sessão válida é bloqueado pelo gate (Traefik forward-auth), sem vazar a aplicação.
- [ ] **AUTH-03**: A identidade do usuário autenticado é propagada ao Streamlit de forma confiável (header `X-User-Email` injetado pelo gate), permitindo que o app saiba quem é o usuário da sessão.
- [ ] **AUTH-04**: Usuário consegue **redefinir a senha** por link enviado ao e-mail (fluxo self-serve, sem intervenção manual).

### Assinatura & Billing (BILL)

- [ ] **BILL-01**: **Trial de 7 dias** ao cadastrar, **sem cobrança imediata e sem cartão**, com data de fim de trial clara para o usuário; o status inicial (`status_assinatura`) já é a fonte de verdade que o gate consulta.
- [x] **BILL-02**: Cobrança recorrente **mensal via Asaas** (criação de cliente + assinatura), com **checkout hospedado pelo Asaas** — o produto **nunca** manuseia dados de cartão.
- [ ] **BILL-03**: **Webhooks do Asaas nativos Django** (idempotentes, sem n8n) atualizam o status da assinatura (ativa / inadimplente / cancelada / trial) na fonte de verdade (Postgres).
- [ ] **BILL-04**: O gate lê o status (**trial ativo OU assinatura ativa**) para liberar/bloquear; inadimplência/cancelamento bloqueia o acesso após o período devido.

### Conta & Multiusuário (ACCT)

- [ ] **ACCT-01**: **Multiusuário real** — cada usuário tem conta isolada e o app serve sessões simultâneas **sem vazar estado** entre usuários.
- [x] **ACCT-02**: **Página de conta**: status da assinatura, gerenciar/cancelar e link para a cobrança (Asaas), sem o produto expor dados sensíveis de pagamento.

### Posicionamento & Legal (LEGAL)

- [ ] **LEGAL-01**: Copy e features reforçam "**software educacional, sem recomendação**" (sem "compre/venda", sem carteira personalizada); **Termos de Uso + Política de Privacidade + disclaimer** aceitos no cadastro.

### Go-live & Operação (OPS)

- [ ] **OPS-01**: Deploy integrado (Django + gate + Streamlit) na VPS (Docker Swarm + Traefik) sob **domínio Lazari Capital**, com segredos (Asaas/DB) fora do git, e teste **E2E pago** (cadastro → trial → pagamento → acesso → cancelamento → bloqueio).

## Future Requirements (pós-v2.0)

- Múltiplos planos/tiers (free limitado, Pro, Pro+) e gate por feature
- Plano anual, cupons, programa de afiliados
- OAuth (Google) no login, além de email+senha
- Landing page de marketing/SEO própria da marca Lazari Capital
- Watchlist/histórico por usuário, export PDF, alertas (WhatsApp via Evolution API)
- Migração do front do app para React+Vite (rebuild além do gateway híbrido)

## Out of Scope (v2.0)

- Reescrever a UI do app em React ou Django — o engine continua em **Streamlit atrás do gate**
- Múltiplos tiers/planos — v2.0 é **plano único** (trial → mensal)
- **n8n** para webhooks — substituído por app `webhooks` nativo Django
- Qualquer recomendação/aconselhamento personalizado de investimento (regulatório CVM)
- Nova fonte de dados paga — segue só com CVM/Yahoo/BCB

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| BILL-01 | Phase 1 | Pending |
| ACCT-01 | Phase 1 | Pending |
| LEGAL-01 | Phase 1 | Pending |
| BILL-02 | Phase 2 | Complete |
| BILL-03 | Phase 2 | Pending |
| BILL-04 | Phase 2 | Pending |
| ACCT-02 | Phase 2 | Complete |
| OPS-01 | Phase 3 | Pending |

**Coverage:** 12 requisitos v2.0 mapeados. Phase 1 = Login/Cadastro + Gate + status de trial
(fundação que Billing consome); Phase 2 = Asaas + webhooks + conta; Phase 3 = deploy E2E pago.
