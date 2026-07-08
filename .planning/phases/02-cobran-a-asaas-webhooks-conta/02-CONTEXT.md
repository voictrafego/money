# Phase 2: Cobrança Asaas + Webhooks + Conta - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Transformar o trial em receita. O usuário em trial assina o **plano mensal via checkout
hospedado pelo Asaas** (o produto nunca toca dados de cartão), **webhooks nativos Django
idempotentes** mantêm o `Conta.status` em dia (trial → ativo → inadimplente → cancelado), o
**gate honra esse status** (libera enquanto trial OU assinatura ativa; bloqueia após a graça), e
a **página de conta** deixa o usuário ver status, obter o link de cobrança do Asaas e cancelar.

Requisitos: **BILL-02** (checkout hospedado / assinatura mensal), **BILL-03** (webhooks nativos
idempotentes), **BILL-04** (gate lê status trial-OU-ativa; bloqueia pós-inadimplência), **ACCT-02**
(página de conta: status + link cobrança + cancelar, sem expor dados de pagamento).

**Fora de escopo (outras fases):** deploy/E2E pago ao vivo, Traefik/domínio, SMTP prod, páginas
legais reais (Phase 3 / OPS-01); qualquer recomendação de investimento (regulatório CVM — proibido).
</domain>

<decisions>
## Implementation Decisions

### Checkout & primeira cobrança
- **D-01:** Assinatura via **checkout hospedado do Asaas** — o backend cria o cliente (customer) e
  a assinatura (subscription) via `AsaasClient` e redireciona o usuário para o link hospedado do
  Asaas. O produto **nunca** manuseia/armazena dados de cartão (BILL-02).
- **D-02:** A **1ª cobrança cai no fim do trial**: ao assinar durante o trial, definir
  `nextDueDate = Conta.trial_ate`. Preserva a promessa "7 dias grátis", acesso contínuo, conversão
  sem fricção. (Se o usuário já estiver fora do trial, cobrança na próxima data padrão.)

### Plano & preço
- **D-03:** **Plano único "PRO", mensal, R$ 19,90** (ciclo `MONTHLY`). Seedar exatamente 1 `Plano`
  no banco (data migration ou management command). Preço da pesquisa de mercado interna
  (break-even ~17 pagantes). `valor_mensal` da `Assinatura` é snapshot no momento da contratação.

### Graça / dunning (BILL-04)
- **D-04:** Após `PAYMENT_OVERDUE`, **7 dias de graça** antes do gate bloquear. Webhook de overdue
  seta `Conta.status = inadimplente` e `grace_ate = data_vencimento + 7 dias`; o gate libera
  enquanto `now <= grace_ate`, bloqueia depois. Asaas re-tenta a cobrança nesse período — 7 dias
  reduz churn involuntário (cartão que falhou) sem dar acesso grátis prolongado.

### Cancelamento (ACCT-02)
- **D-05:** Cancelamento **vale até o fim do período já pago** (cancel-at-period-end). O botão de
  cancelar chama a API do Asaas para não renovar; `Conta.status = cancelado`, mas o **gate continua
  liberando até a data paga** (paid-through / `trial_ate` se ainda em trial). Padrão SaaS, menor
  atrito. Sem reembolso proporcional.

### Claude's Discretion
- **Mapeamento fino dos eventos de webhook → transições de status** (quais eventos do Asaas mapeiam
  para ativo/inadimplente/cancelado): reusar/estender o handler existente em `apps/billing/views.py`
  (já trata `PAYMENT_CONFIRMED`/`PAYMENT_RECEIVED`/`PAYMENT_OVERDUE`; a Phase 2 acrescenta o ciclo de
  subscription — confirmação renova o paid-through, overdue arma a graça, cancelamento/deleção fecha).
  Researcher confirma a lista canônica de eventos do Asaas para assinaturas.
- **Poda de resíduos B2B do crm-voic** não usados no B2C: `Cupom`/`ResgateCupom`/`cupom_service` e
  `TrialCpf` (anti-abuso por CPF) — o trial B2C é verificação-first por e-mail (Phase 1), sem CPF.
  Manter dormentes ou podar conforme o planner achar mais limpo; NÃO introduzir cupom nesta fase.
- **App do webhook:** usar **`apps/billing`** (onde já vivem `AsaasWebhookLog` + `billing/views.py`),
  **NÃO** o `apps/webhooks` (que era o importer de leads do Meta e ficou como shell vazio após a
  Phase 1). Ver [[analista-dividendos-*]] / 01-01-SUMMARY.
- **Idempotência:** manter o padrão existente (insert-and-catch atômico em `AsaasWebhookLog.event_id`
  antes de qualquer efeito colateral).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos & roadmap (repo analista_dividendos)
- `.planning/REQUIREMENTS.md` — BILL-02, BILL-03, BILL-04, ACCT-02 (fonte dos critérios)
- `.planning/ROADMAP.md` § "Phase 2" — goal + 4 success criteria
- `.planning/PROJECT.md` — Key Decisions do v2.0 (Asaas conta/chave próprias; webhooks nativos sem n8n; gate Traefik forward-auth; Postgres fonte de verdade)
- `.planning/phases/01-funda-o-cadastro-login-gate-e-trial/01-04-SUMMARY.md` — contrato do GateView (o que a Phase 2 precisa manter honrado)

### Infra de billing reutilizável (repo ~/projects/lazari-capital — onde o código vive)
- `~/projects/lazari-capital/apps/billing/asaas_client.py` — cliente da API Asaas (criar cliente/assinatura)
- `~/projects/lazari-capital/apps/billing/models.py` — `Plano`, `Assinatura` (com `asaas_sub_id`, `ciclo_status`, snapshot de preço), `AsaasWebhookLog` (idempotência por `event_id`), `Cupom`/`TrialCpf` (resíduo B2B a podar)
- `~/projects/lazari-capital/apps/billing/views.py` — webhook público `POST /billing/webhook/` idempotente (base a estender)
- `~/projects/lazari-capital/apps/billing/services.py` — `provisionar_signup` (B2C, Phase 1); ponto de entrada da criação de assinatura
- `~/projects/lazari-capital/apps/accounts/models.py` — `Conta` (`status`, `trial_ate`, `grace_ate`, `asaas_customer_id`, `plano`) — fonte de verdade do gate
- `~/projects/lazari-capital/apps/gate/views.py` — `GateView` (Phase 1) que passa a honrar assinatura ativa além do trial
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AsaasClient` (`apps/billing/asaas_client.py`): já encapsula chamadas à API Asaas — estender para criar customer + subscription com `nextDueDate` e obter o link hospedado.
- `Assinatura` model: já tem `asaas_sub_id`, `ciclo_status`, snapshot de `valor_mensal`, `UniqueConstraint` (1 assinatura ativa por conta). Reusar como está.
- `AsaasWebhookLog` + webhook view: já implementam idempotência por `event_id` (insert-and-catch atômico) e tratam PAYMENT_CONFIRMED/RECEIVED/OVERDUE — estender p/ o ciclo de subscription e a política de graça.
- `Conta` (accounts): campos `status`/`trial_ate`/`grace_ate`/`asaas_customer_id`/`plano` já existem — Phase 2 só popula/transiciona.

### Established Patterns
- Webhook idempotente nativo Django (sem n8n) — padrão travado no PROJECT.md.
- Gate fail-closed lê `Conta.status`/datas como fonte de verdade (Phase 1) — Phase 2 acrescenta "assinatura ativa OU trial" + respeito a `grace_ate`.
- Multi-tenant dormante (`TenantModel`, `set_current_conta_id()` p/ acesso cross-tenant do webhook/worker).

### Integration Points
- `GateView` (Phase 1) → passa a liberar também para `status=ativo`; bloqueia `inadimplente` só após `grace_ate`; `cancelado` libera até paid-through.
- Página de conta (nova, ACCT-02) → lê `Assinatura`/`Conta`, expõe link do Asaas e botão cancelar (chama `AsaasClient`).
- Seed do `Plano` PRO → data migration/management command rodando no deploy (Phase 3).
</code_context>

<specifics>
## Specific Ideas

- Checkout **hospedado** (redirect ao Asaas), nunca formulário de cartão próprio.
- 1ª fatura ancorada em `trial_ate` (não cobrar durante o trial).
- Preço-âncora: **R$ 19,90/mês**, plano único PRO.
</specifics>

<deferred>
## Deferred Ideas

- **Plano anual / descontos** — considerado e adiado; começar com plano único mensal. Reavaliar após validar conversão.
- **Cupons de desconto** (infra `Cupom`/`ResgateCupom` do crm-voic) — fora de escopo no B2C inicial; manter dormente.
- **Deploy/E2E pago ao vivo, Traefik, domínio, SMTP prod, páginas legais reais** — Phase 3 (OPS-01).
- **Página de vendas www.lazaricapital.com.br** — não existe ainda; landing de conversão é trabalho à parte (Phase 3 ou fase própria).

None além dos acima — discussão permaneceu no escopo da fase.
</deferred>

---

*Phase: 2-Cobrança Asaas + Webhooks + Conta*
*Context gathered: 2026-07-08*
