# Requirements: Analista de Dividendos — v2.0 Comercialização

**Defined:** 2026-06-28
**Core Value:** O produto cobra de forma confiável e o acesso reflete fielmente o status de assinatura — quem paga (ou está em trial) entra; quem não tem assinatura ativa não entra — sem nunca prometer recomendação de investimento.
**Milestone goal:** Transformar o protótipo de usuário único num produto que cobra: autenticação, trial de 7 dias → assinatura mensal (Asaas), gate de acesso e multiusuário, posicionado como **software educacional (sem recomendação)**.

**Arquitetura (decidida):** **Gateway híbrido** — o motor Streamlit (engine de valuation validado, 191 testes) fica **intacto atrás de um gate**. Front de entrada (landing + signup/login + checkout) no stack do usuário (React+Vite); fonte de verdade de contas/assinaturas no Supabase/Postgres; cobrança no Asaas; webhooks via n8n; proxy/token libera o Streamlit só p/ sessão autenticada com trial/assinatura ativa.

## v2.0 Requirements

### Auth & Acesso (AUTH)

- [ ] **AUTH-01**: Cadastro e login de usuário (e-mail/senha e/ou OAuth) numa camada de entrada própria, emitindo uma sessão/token que governa o acesso ao app.
- [ ] **AUTH-02**: O app Streamlit só é acessível autenticado **e** com trial/assinatura ativa — acesso direto à URL do Streamlit sem token válido é bloqueado (gate/proxy), sem vazar a aplicação.

### Assinatura & Billing (BILL)

- [ ] **BILL-01**: Trial de 7 dias ao cadastrar, **sem cobrança imediata**, com data de fim de trial clara para o usuário.
- [ ] **BILL-02**: Cobrança recorrente **mensal via Asaas** (criação de cliente + assinatura), com checkout hospedado pelo Asaas — o produto **nunca** manuseia dados de cartão.
- [ ] **BILL-03**: Webhooks do Asaas (via n8n) atualizam o status da assinatura (ativa / inadimplente / cancelada / trial) na fonte de verdade (Supabase/Postgres), de forma idempotente.
- [ ] **BILL-04**: O gate lê o status (trial ativo **OU** assinatura ativa) para liberar/bloquear; inadimplência/cancelamento bloqueia o acesso após o período devido.

### Conta & Multiusuário (ACCT)

- [ ] **ACCT-01**: Multiusuário real — cada usuário tem conta isolada e o app serve sessões simultâneas **sem vazar estado** entre usuários.
- [ ] **ACCT-02**: Página de conta: status da assinatura, gerenciar/cancelar e link para a cobrança (Asaas), sem o produto expor dados sensíveis de pagamento.

### Posicionamento & Legal (LEGAL)

- [ ] **LEGAL-01**: Copy e features reforçam "**software educacional, sem recomendação**" (sem "compre/venda", sem carteira personalizada); Termos de Uso + Política de Privacidade + disclaimer aceitos no cadastro.

### Go-live & Operação (OPS)

- [ ] **OPS-01**: Deploy integrado (front + gate + Streamlit) na VPS (Docker Swarm + Traefik) sob domínio de produto, com segredos (Asaas/Supabase) fora do git, e teste **E2E pago** (cadastro → trial → pagamento → acesso → cancelamento → bloqueio).

## Future Requirements (pós-v2.0)

- Múltiplos planos/tiers (ex.: free limitado, Pro, Pro+) e gate por feature
- Plano anual, cupons, programa de afiliados
- Watchlist/histórico por usuário, export PDF, alertas (WhatsApp via Evolution API)
- Migração do front do app para React+Vite (rebuild além do gateway híbrido)

## Out of Scope (v2.0)

- Reescrever a UI do app em React — o engine continua em Streamlit **atrás do gate**
- Múltiplos tiers/planos — v2.0 é **plano único** (trial → mensal)
- Qualquer recomendação/aconselhamento personalizado de investimento (regulatório CVM)
- Nova fonte de dados paga — segue só com CVM/Yahoo/BCB

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 13 | Pending |
| AUTH-02 | Phase 13 | Pending |
| BILL-01 | Phase 14 | Pending |
| BILL-02 | Phase 14 | Pending |
| BILL-03 | Phase 14 | Pending |
| BILL-04 | Phase 13/14 | Pending |
| ACCT-01 | Phase 13 | Pending |
| ACCT-02 | Phase 15 | Pending |
| LEGAL-01 | Phase 15 | Pending |
| OPS-01 | Phase 16 | Pending |

**Coverage:** 10 requisitos v2.0 mapeados (fonte de verdade na Phase 12 é a base que AUTH/BILL consomem).
