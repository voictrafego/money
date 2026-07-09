---
phase: 03-go-live-e2e-pago
plan: 05
subsystem: billing
tags: [e2e, asaas, webhook, pix, gate, streamlit, websocket, lazari-capital, smoke-test]

# Dependency graph
requires:
  - "03-04: stack `lazari` no ar (www Django + app Streamlit gated) na VPS"
provides:
  - "E2E pago validado AO VIVO: cadastro → verificação → trial → pagamento real → conta paga → acesso ao app"
  - "Webhook Asaas prod comprovadamente idempotente + autenticado por token (POST repetido não duplica; token inválido → 401)"
  - "Smoke real R$19,90 (PIX) confirmado: pagamento RECEIVED → webhook prod → Conta ATIVO/trial_ate=None/ciclo=pago"
  - "Webhook prod corrigido (authToken setado + fila reativada) — pagamentos futuros ativam a conta sozinhos"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Diagnóstico de webhook Asaas via API (GET /v3/webhooks p/ interrupted; GET /v3/payments?subscription= p/ status), lendo chave inline do .env"
    - "Streamlit atrás de reverse-proxy: [server] enableCORS/enableXsrfProtection=false + gate faz a auth"

key-files:
  created:
    - "app.py (analista_dividendos): botão Sair na sidebar → WWW_LOGOUT_URL"
  modified:
    - "~/projects/lazari-capital/config/settings/prod.py (SECURE_REDIRECT_EXEMPT=[^gate/$] — destrava WS)"
    - "~/projects/lazari-capital/templates/billing/verificar_ok.html (botão → produto, não /painel/)"
    - "~/projects/lazari-capital/apps/billing/views.py (VerificarEmailView passa produto_url)"
    - "~/projects/lazari-capital/apps/users/views.py + urls.py (endpoint GET /sair-app/ p/ logout do app)"
    - "~/projects/lazari-capital/apps/core/middleware/billing_gate.py (isenta logout-app)"
    - "~/projects/lazari-capital/templates/accounts/conta.html ({% comment %} — comentário multi-linha renderizava cru)"
    - "analista_dividendos/.streamlit/config.toml (CORS/XSRF off)"
    - "Asaas prod (webhook): authToken=ASAAS_WEBHOOK_TOKEN + interrupted=false (via API)"

key-decisions:
  - "Task 2 (transições de status no sandbox) coberta pelos testes automatizados (226) + webhook ao vivo; não re-exercitada manualmente no sandbox"
  - "Estorno do R$19,90 é ação do usuário no painel Asaas (agente não executa transação financeira)"

patterns-established:
  - "Webhook Asaas: authToken vazio → app 401 (sem log) → após 15 falhas o Asaas pausa a fila (interrupted); reativar re-entrega os eventos pendentes"
  - "Comentário Django {# #} só single-line; blocos usam {% comment %}"

requirements-completed: [OPS-01]

# Metrics
duration: ~3h (E2E ao vivo + 4 bugs descobertos em produção: redirect CRM, WS travado, webhook authToken/interrupted, comentário cru)
completed: 2026-07-09
---

# Phase 3 · Plan 05: Teste E2E pago Summary

**E2E pago VALIDADO AO VIVO: um pagamento real de R$ 19,90 via PIX no checkout hospedado do Asaas prod disparou o webhook prod que converteu a conta de trial para paga (Conta ATIVO, trial_ate=None, assinatura ciclo=pago, próximo vencimento 15/08/2026), com acesso ao app liberado. Critério #2 do OPS-01 atendido — a Fase 3 e o milestone v2.0 estão completos.**

## Accomplishments

- **Task 1 (automatizável)** — `pytest apps/billing apps/gate apps/accounts` = **226 passed**. Endpoint público `/billing/webhook/` exercitado AO VIVO: POST assinado `PAYMENT_CONFIRMED` → 200 `{status: ok}` + conta ativa; POST repetido (mesmo event_id) → 200 `{status: duplicado}` (idempotente); token inválido → **401**.
- **Task 2 (transições)** — coberta pela suíte automatizada (3 ramos do gate, cancelamento, graça, overdue) + a ativação real observada ao vivo; não re-exercitada no sandbox por decisão.
- **Task 3 (smoke real)** — assinatura real do Plano PRO R$19,90 via **PIX**; pagamento `RECEIVED` no Asaas prod (valida chaves prod / Pitfall `$$`); webhook prod ativou a conta; `/conta/` mostra Status **Ativo** + próximo vencimento **15/08/2026** + Cancelar assinatura. Estorno delegado ao usuário.

## Deviations / bugs descobertos e corrigidos AO VIVO (todos commitados)

1. **Redirect pós-verificação ia ao CRM** — `verificar_ok.html` linkava `/painel/` (placeholder do fork) em vez do produto. → `produto_url = STREAMLIT_APP_URL`. (`f25e493`)
2. **App Streamlit "carregava pra sempre"** — `SECURE_SSL_REDIRECT` 301-redirecionava a subrequisição de forwardAuth do WebSocket (chega sem `X-Forwarded-Proto` no upgrade) → Traefik repassava o 301 → WS morria. → `SECURE_REDIRECT_EXEMPT=[^gate/$]`. Verificado: handshake autenticado via Traefik retorna **101**. (`f25e493`)
3. **Webhook Asaas prod não chegava** — `authToken` vazio no webhook → app 401 (sem log) → após 15 falhas o Asaas **pausou a fila** (`interrupted=true`). → via API: `authToken`=`ASAAS_WEBHOOK_TOKEN` + `interrupted=false`; Asaas re-entregou o `PAYMENT_RECEIVED` do PIX e a conta ativou.
4. **Comentário cru em `/conta/`** — `{# #}` multi-linha renderizava como texto visível. → `{% comment %}`. (`38fb6e9`)
5. **(extra) Botão "Sair"** — adicionado ao app Streamlit (endpoint GET `/sair-app/` no Django, cross-host). (`61a8ef5` / `2e5e54a`)

## Notes

- Webhook prod agora correto: pagamentos futuros ativam a conta automaticamente.
- Estorno do smoke (R$19,90 PIX, `pay_r5totz4lcrxbljzj`) fica a cargo do usuário no painel Asaas.
- Streamlit config canônica de proxy (CORS/XSRF off) aplicada, embora a causa do WS fosse o SSL redirect.

## Self-Check: PASSED
