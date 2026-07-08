# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 (shipped 2026-06-28)
- ✅ **v1.4–v1.7 — Swing Trade / Modo Trading / Home / Lentes-Selo-Comparador** — Phases 12–21 (shipped 2026-07-04, tag `v1.7`)
- 🚧 **v2.0 — Comercialização (Lazari Capital)** — Phases 1–3 (planejada, numeração reiniciada)

> **Marco major novo (v2.0):** a numeração de fases foi **reiniciada em Phase 1**. Os diretórios
> das fases v1.x foram arquivados em `.planning/milestones/v1.7-phases/`; `.planning/phases/` está
> vazio para o v2.0. Snapshots dos roadmaps/requisitos anteriores em `.planning/milestones/`.
> Requisitos ativos do v2.0 em `.planning/REQUIREMENTS.md`.

## Overview

O engine de valuation (Streamlit, 338 testes verdes) fica **intacto atrás de um gate**. Constrói-se
na frente um projeto **Django novo** (repo separado `~/projects/lazari-capital`) que espelha o
`crm-voic` (`accounts`, `users` com email-como-login, `billing`/`asaas_client.py`, `webhooks`
nativos — **sem n8n**). A jornada: **Fase 1** ergue a fundação (cadastro self-serve, login, trial de
7 dias modelado como fonte de verdade, gate Traefik forward-auth propagando `X-User-Email`, aceite
legal); **Fase 2** transforma trial em receita (Asaas checkout hospedado + webhooks idempotentes +
página de conta); **Fase 3** integra tudo na VPS sob o domínio Lazari Capital e valida o fluxo pago
ponta a ponta. Posicionamento: **software educacional, sem recomendação (CVM)**.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

<details>
<summary>✅ v1.0–v1.7 — Engine, gráfico, timing, saneamento, swing, home, lentes (Phases 1–21 do ciclo antigo) — SHIPPED 2026-07-04 (tag v1.7)</summary>

Numeração antiga (1–21). Detalhes completos: `.planning/milestones/v1.7-ROADMAP.md`,
`.planning/milestones/v1.3-ROADMAP.md`, `.planning/milestones/v1.1-ROADMAP.md`.
Diretórios de fase arquivados em `.planning/milestones/v1.7-phases/`.

</details>

### 🚧 v2.0 — Comercialização (Lazari Capital)

**Milestone Goal:** Transformar o app de usuário único num produto cobrável sob a marca **Lazari
Capital** — front Django (auth + Asaas + webhooks) na frente, engine Streamlit intacto atrás de um
gate Traefik forward-auth, com trial de 7 dias → assinatura mensal, como software educacional.

- [ ] **Phase 1: Fundação — Cadastro, Login, Gate e Trial** - Projeto Django espelhando o crm-voic: cadastro self-serve + login/reset + trial modelado + gate forward-auth + aceite legal
- [x] **Phase 2: Cobrança Asaas + Webhooks + Conta** - Assinatura mensal via checkout hospedado Asaas, webhooks nativos idempotentes atualizando o status, página de conta
- [ ] **Phase 3: Go-live E2E pago** - Deploy integrado (Django + gate + Streamlit) na VPS sob domínio Lazari Capital, segredos fora do git, teste E2E pago completo

## Phase Details

### Phase 1: Fundação — Cadastro, Login, Gate e Trial
**Goal**: Erguer a camada Django (repo `~/projects/lazari-capital`, espelhando o `crm-voic`) que
governa o acesso: qualquer visitante se cadastra self-serve (email+senha), aceita os termos, ganha
um trial de 7 dias sem cartão, loga/desloga/redefine senha, e o gate Traefik forward-auth só libera
o Streamlit para quem está autenticado **E** com status ativo/trial — propagando `X-User-Email`.
**Depends on**: Nothing (primeira fase do marco; engine Streamlit já existe e fica intacto)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, BILL-01, ACCT-01, LEGAL-01
**Success Criteria** (what must be TRUE):
  1. Um visitante cria conta com email+senha, aceita Termos + Privacidade + disclaimer educacional, e entra logado com trial de 7 dias exibido (data de fim clara), sem informar cartão.
  2. Acessar a URL do Streamlit sem sessão válida é bloqueado pelo gate (redirecionado ao login) sem vazar o app; uma sessão autenticada+ativa entra e o Streamlit recebe o header `X-User-Email` confiável.
  3. Usuário loga, desloga e redefine a senha por link enviado ao e-mail — todo o fluxo self-serve, sem intervenção manual.
  4. Dois usuários simultâneos têm contas isoladas e não vazam estado entre sessões.
  5. `status_assinatura` existe como fonte de verdade no Postgres (novo usuário = trial 7 dias) e é o campo que o gate consulta: trial ativo libera, trial expirado bloqueia.
**Plans**: 5 plans in 4 waves
  - [x] 01-01-PLAN.md — Fork-and-prune scaffold do lazari-capital (remove leads/dashboard/integrations + papéis; check/migrate/pytest verdes)
  - [x] 01-02-PLAN.md — Cadastro self-serve + verificação de e-mail + armar trial 7d + aceite legal
  - [x] 01-03-PLAN.md — Login/logout + reset de senha nativo (net-new; ausente no crm-voic)
  - [x] 01-04-PLAN.md — Gate Traefik forward-auth (GateView) + página trial-acabou + cookie domínio-pai
  - [x] 01-05-PLAN.md — Traefik forwardAuth labels + leitura de X-User-Email no Streamlit + bump streamlit>=1.37
**UI hint**: yes

### Phase 2: Cobrança Asaas + Webhooks + Conta
**Goal**: Transformar o trial em receita — o usuário assina o plano mensal via checkout **hospedado
pelo Asaas** (produto nunca toca cartão), webhooks nativos Django (idempotentes, sem n8n) mantêm o
`status_assinatura` em dia (ativa / inadimplente / cancelada), o gate honra esse status, e a página
de conta deixa o usuário ver status, obter o link de cobrança e cancelar.
**Depends on**: Phase 1
**Requirements**: BILL-02, BILL-03, BILL-04, ACCT-02
**Success Criteria** (what must be TRUE):
  1. Usuário em trial assina o plano mensal via checkout hospedado do Asaas (criação de cliente + assinatura) e retorna com assinatura ativa, sem o produto manusear dados de cartão.
  2. Um pagamento confirmado no Asaas dispara webhook que ativa a assinatura; falta de pagamento/cancelamento atualiza o status para inadimplente/cancelada — de forma idempotente (webhook repetido não duplica efeito).
  3. O gate libera enquanto trial OU assinatura estiver ativa e bloqueia o acesso após inadimplência/cancelamento, passado o período devido.
  4. A página de conta mostra o status da assinatura, o link de cobrança do Asaas e permite cancelar, sem expor dados sensíveis de pagamento.
**Plans**: 3 plans in 3 waves
  - [x] 02-01-PLAN.md — Checkout hospedado: seed Plano PRO + CpfForm + services.assinar + AssinarView (BILL-02)
  - [x] 02-02-PLAN.md — Página de conta + cancelamento (DELETE Asaas, cancel-at-period-end) (ACCT-02)
  - [x] 02-03-PLAN.md — Gate honra status (3 ramos) + isenção de middleware + ciclo de webhook idempotente (BILL-03, BILL-04)
**UI hint**: yes

### Phase 3: Go-live E2E pago
**Goal**: Integrar tudo no ar sob o domínio **Lazari Capital** (Docker Swarm + Traefik): Django +
gate forward-auth + Streamlit, com segredos (Asaas/DB) fora do git, e validar o fluxo pago completo
ponta a ponta — cuidando de os websockets do Streamlit funcionarem atrás do forward-auth.
**Depends on**: Phase 2
**Requirements**: OPS-01
**Success Criteria** (what must be TRUE):
  1. O produto responde no domínio Lazari Capital com Django, gate e Streamlit integrados na VPS (Docker Swarm + Traefik), com segredos (Asaas/DB) fora do git.
  2. Um teste E2E pago percorre cadastro → trial → pagamento → acesso ao app → cancelamento → bloqueio, e cada transição de status reflete corretamente no acesso.
  3. Os websockets do Streamlit funcionam atrás do gate forward-auth: o app carrega e interage sem quebra de sessão nem loop de autenticação.
**Plans**: 5 plans in 3 waves
  - [ ] 03-01-PLAN.md — Landing mínima Lazari Capital (www) re-brandada (D-07/D-08)
  - [ ] 03-02-PLAN.md — Prep de produção: DNS grey-cloud + .env prod + fix domínio prod.py
  - [ ] 03-03-PLAN.md — Stack unificado `lazari` (web+worker+db+money, gate FQDN, 301) + backup
  - [ ] 03-04-PLAN.md — Deploy + cutover + validação de gate/websockets + cron backup
  - [ ] 03-05-PLAN.md — Teste E2E pago (sandbox + live + smoke real R$19,90 estornado)

## Progress

**Execution Order:**
Fases executam em ordem numérica: 1 → 2 → 3

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Fundação — Cadastro, Login, Gate e Trial | v2.0 | 0/5 | Planned | - |
| 2. Cobrança Asaas + Webhooks + Conta | v2.0 | 0/TBD | Not started | - |
| 3. Go-live E2E pago | v2.0 | 0/5 | Planned | - |
