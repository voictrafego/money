# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 + auditoria/correção de dados (shipped 2026-06-28)
- 🚧 **v2.0 — Comercialização (produto cobrável)** — fases a definir via `/gsd-new-milestone`

> Detalhes completos das fases concluídas (v1.0–v1.3) no snapshot `.planning/milestones/v1.3-ROADMAP.md` e requisitos em `.planning/milestones/v1.3-REQUIREMENTS.md`.

## v2.0 — Comercialização (produto cobrável)

**Goal:** Transformar o protótipo de usuário único num produto que cobra — auth, trial 7d →
assinatura mensal (Asaas), gate de acesso e multiusuário — posicionado como software educacional
(sem recomendação).

**Decisões travadas:**
- Monetização: assinatura paga, trial 7 dias → mensal (Asaas)
- Primeiro foco: produtizar (auth → planos/gate → billing recorrente → multiusuário)
- Regulatório: software educacional, sem recomendação (copy e features seguem isso)

**Decisão de arquitetura a resolver (discuss/requirements):** como colar auth+billing num app
Streamlit — provável híbrido com front/checkout no stack React+Vite+n8n+Asaas na frente do Streamlit.

## Phases

> Numeração continua do milestone anterior (v1.3 terminou na Phase 11). Gateway híbrido:
> o engine Streamlit fica intacto atrás de um gate; auth/billing/front no stack do usuário.

- [ ] **Phase 12: Fonte de verdade de contas & assinaturas (Supabase)** — modelo de dados de usuário + status de assinatura/trial no Supabase/Postgres; a base única que o gate e os webhooks leem/escrevem. _(funda AUTH/BILL)_
- [ ] **Phase 13: Gate de acesso ao Streamlit (auth + proxy/token)** — login/sessão e o mecanismo que só libera o Streamlit com token válido + trial/assinatura ativa; isolamento multiusuário. (AUTH-01, AUTH-02, ACCT-01, BILL-04 leitura)
- [ ] **Phase 14: Billing Asaas (trial 7d → mensal) + webhooks n8n** — cliente/assinatura no Asaas, checkout hospedado, e webhooks via n8n que escrevem status (ativa/inadimplente/cancelada) no Supabase de forma idempotente. (BILL-01, BILL-02, BILL-03, BILL-04)
- [ ] **Phase 15: Front de entrada — landing, signup/login, conta, legal** — landing de conversão + fluxo de cadastro/login + página de conta (status/cancelar) + Termos/Privacidade/disclaimer no cadastro. (ACCT-02, LEGAL-01; consome AUTH-01)
- [ ] **Phase 16: Go-live — deploy integrado + E2E pago** — orquestrar front+gate+Streamlit na VPS (Swarm/Traefik, domínio, segredos) e validar o fluxo ponta-a-ponta pago (cadastro → trial → pagamento → acesso → cancelamento → bloqueio). (OPS-01)

**Dependências:** 12 → 13 → 14 → 16 (linha principal); Phase 15 (front) pode correr em paralelo a 13/14 e converge no 16.

## Phase Details

### Phase 12: Fonte de verdade de contas & assinaturas
**Goal:** Existe um esquema em Supabase/Postgres que representa usuário + status de assinatura (trial/ativa/inadimplente/cancelada) com datas; é a única fonte de verdade lida pelo gate e escrita pelos webhooks.
**Depends on:** — (foundation)
**Requirements:** base para AUTH/BILL

### Phase 13: Gate de acesso ao Streamlit
**Goal:** Usuário se autentica e só alcança o Streamlit com sessão válida + trial/assinatura ativa; acesso direto à URL do Streamlit sem token é bloqueado; sessões de usuários distintos não vazam estado.
**Depends on:** Phase 12 (lê status na fonte de verdade)
**Requirements:** AUTH-01, AUTH-02, ACCT-01, BILL-04 (leitura)

### Phase 14: Billing Asaas + webhooks n8n
**Goal:** Cadastro inicia trial de 7 dias sem cobrança; ao fim, cobrança mensal recorrente via Asaas (checkout hospedado, sem cartão no produto); webhooks (n8n) atualizam o status no Supabase de forma idempotente.
**Depends on:** Phase 12 (escreve status); integra com Phase 13 (gate consome)
**Requirements:** BILL-01, BILL-02, BILL-03, BILL-04

### Phase 15: Front de entrada (landing, signup/login, conta, legal)
**Goal:** Landing de conversão + cadastro/login + página de conta (status, cancelar) + aceite de Termos/Privacidade/disclaimer; copy reforça "software educacional, sem recomendação".
**Depends on:** Phase 13 (auth) — pode iniciar em paralelo
**Requirements:** ACCT-02, LEGAL-01

### Phase 16: Go-live — deploy integrado + E2E pago
**Goal:** Front + gate + Streamlit no ar na VPS (Swarm/Traefik, domínio de produto, segredos fora do git), com o fluxo pago validado ponta-a-ponta.
**Depends on:** Phases 13, 14, 15
**Requirements:** OPS-01

## Backlog

- Payout-alvo por setor configurável (refino além do expurgo data-driven de não-recorrentes)
- Sinalização explícita de "ano extraordinário" na tabela de Fundamentos por ano
- DDM-DOC-01: alinhar docstring/teste de `t` em `ddm.py` (IN-06)
