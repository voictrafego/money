# Phase 2: Cobrança Asaas + Webhooks + Conta - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-08
**Phase:** 2-Cobrança Asaas + Webhooks + Conta
**Areas discussed:** Checkout & 1ª cobrança, Plano & preço, Graça/dunning, Cancelamento

---

## Checkout & 1ª cobrança

| Option | Description | Selected |
|--------|-------------|----------|
| No fim do trial | 1ª fatura no dia que o trial acaba (nextDueDate = trial_ate); preserva "7 dias grátis" | ✓ |
| Imediata ao assinar | Cobra na hora; abre mão dos dias de trial restantes | |
| Imediata + soma 30 dias | Cobra já e adiciona 30 dias ao trial restante | |

**User's choice:** No fim do trial
**Notes:** Checkout hospedado do Asaas (cliente + assinatura via API, redirect ao link); produto nunca toca cartão.

---

## Plano & preço

| Option | Description | Selected |
|--------|-------------|----------|
| PRO único R$19,90/mês | Plano único mensal a R$19,90 (pesquisa interna; break-even ~17 pagantes) | ✓ |
| PRO R$19,90/mês + anual | Mensal + opção anual com desconto | |
| Outro preço mensal | Plano único mensal com preço diferente | |

**User's choice:** PRO único R$19,90/mês
**Notes:** Seedar 1 Plano no banco; anual adiado.

---

## Graça / dunning (BILL-04)

| Option | Description | Selected |
|--------|-------------|----------|
| 3 dias | Equilíbrio churn involuntário vs freeloading | |
| 7 dias | Mais tolerância; menos churn involuntário | ✓ |
| 0 dias | Bloqueia ao vencer | |

**User's choice:** 7 dias
**Notes:** grace_ate = vencimento + 7 dias; gate libera enquanto now <= grace_ate.

---

## Cancelamento (ACCT-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Vale até o fim do período pago | Cancel-at-period-end; acesso até a data paga; status=cancelado mas gate libera até lá | ✓ |
| Corta na hora | Cancela e bloqueia imediatamente | |

**User's choice:** Vale até o fim do período pago
**Notes:** Botão chama API Asaas p/ não renovar; sem reembolso proporcional.

---

## Claude's Discretion

- Mapeamento fino dos eventos de webhook do Asaas → transições de status (estender handler existente em `apps/billing/views.py`).
- Poda de resíduos B2B (Cupom/ResgateCupom/cupom_service, TrialCpf) não usados no B2C.
- Usar `apps/billing` (não `apps/webhooks`) para o webhook Asaas.
- Manter padrão de idempotência por `AsaasWebhookLog.event_id`.

## Deferred Ideas

- Plano anual / descontos — começar com mensal único.
- Cupons de desconto — fora de escopo no B2C inicial.
- Deploy/E2E pago, Traefik, domínio, SMTP prod, páginas legais reais — Phase 3.
- Página de vendas www.lazaricapital.com.br — trabalho à parte.
