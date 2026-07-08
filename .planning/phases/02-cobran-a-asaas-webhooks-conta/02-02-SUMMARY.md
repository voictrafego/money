---
phase: 02-cobran-a-asaas-webhooks-conta
plan: 02
subsystem: billing
tags: [django, asaas, cancelamento, cancel-at-period-end, conta, idor, tenant, lazari-capital]

# Dependency graph
requires:
  - "02-01: services.assinar cria Assinatura (asaas_sub_id, invoice_url, proximo_vencimento) + Plano PRO seed — a página de conta lê e o cancelar usa esses campos"
  - "01: LoginRequiredMixin + TenantMiddleware (conta_id do request.user) + BillingGateMiddleware — views autenticadas escopam Assinatura automaticamente"
  - "fork crm-voic: AsaasClient._request (getattr(session,'delete') já suportado) + modelos Assinatura/Conta — reusados"
provides:
  - "apps/billing/asaas_client.py::cancelar_assinatura(sub_id) — DELETE /v3/subscriptions/{id} (retry_safe=True); _parse_resposta trata 204/corpo vazio devolvendo {} sem regredir o caminho 200+JSON (A5/Pitfall 7)"
  - "apps/billing/services.py::cancelar(conta) — cancel-at-period-end (D-05): DELETE no Asaas, depois status=CANCELADO + grace_ate=paid-through (proximo_vencimento, ou trial_ate se em trial) convertido para datetime aware fim-do-dia; só transiciona após sucesso do DELETE"
  - "apps/accounts/views.py::ContaView (ACCT-02) — status + próximo vencimento + link de cobrança hospedado (invoice_url) + flag pode_cancelar; CTA [Assinar] se sem assinatura"
  - "apps/accounts/views.py::CancelarAssinaturaView — POST-only, valida assinatura cancelável server-side (WARNING 5), deriva conta de request.user.conta (anti-IDOR), trata AsaasError/DoesNotExist sem vazar detalhe"
  - "rotas accounts:conta (/conta/) e accounts:cancelar-assinatura (/conta/cancelar/); templates/accounts/conta.html sem NENHUM dado de cartão (Pitfall 6)"
affects: [02-03-gate-webhook-exemptions, 03-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DELETE no-body defensivo (A5): _parse_resposta aceita 200+JSON OU 204/corpo vazio (→ {}); nenhum resp.json() cru em resposta sem corpo"
    - "cancel-at-period-end (D-05): chamada ao Asaas FORA do transaction.atomic; estado local (CANCELADO + grace_ate) só transiciona APÓS o DELETE retornar — falha do Asaas propaga sem corromper o local"
    - "grace_ate reusado como 'acesso liberado até' genérico (A2): paid-through = trial_ate se em trial, senão proximo_vencimento; DateField→datetime aware fim-do-dia (Pitfall 3)"
    - "anti-IDOR (V4/T-02-08): ContaView/CancelarAssinaturaView derivam conta de request.user.conta; endpoint de cancelar sem parâmetro de id — impossível cancelar/ver assinatura alheia"
    - "guard server-side antes de services.cancelar (WARNING 5): usuário só-trial que POSTe direto recebe mensagem amigável em vez de Assinatura.DoesNotExist"
    - "testes de view que tocam TenantModel usam Client()+force_login (middleware completo), não RequestFactory nu (TenantManager exige conta_id no thread-local)"

key-files:
  created:
    - "~/projects/lazari-capital/apps/billing/tests/test_cancelar.py"
    - "~/projects/lazari-capital/apps/accounts/tests/test_conta_view.py"
    - "~/projects/lazari-capital/templates/accounts/conta.html"
  modified:
    - "~/projects/lazari-capital/apps/billing/asaas_client.py"
    - "~/projects/lazari-capital/apps/billing/services.py"
    - "~/projects/lazari-capital/apps/accounts/views.py"
    - "~/projects/lazari-capital/apps/accounts/urls.py"

key-decisions:
  - "paid-through: trial_ate se trial vigente (trial_ate>=hoje), senão proximo_vencimento — cobre tanto o usuário que assinou durante o trial quanto o já pago (D-05)"
  - "grace_ate (DateTimeField) recebe fim-do-dia (time.max) do paid-through via timezone.make_aware — acesso vale por todo o dia do vencimento (Pitfall 3)"
  - "_parse_resposta trata sucesso em (200, 204): 204 OU corpo vazio → {}; 200+JSON inalterado — sem regressão nos 34 testes existentes de asaas_client"
  - "CancelarAssinaturaView valida `exists()` cancelável antes de chamar services.cancelar (defesa em profundidade dupla: guard + except DoesNotExist)"
  - "conta.status=CANCELADO ainda é bloqueado pelo BillingGateMiddleware nesta fase; a isenção de /conta/ e /conta/cancelar/ é responsabilidade do Plan 03 (por isso os testes usam conta ATIVO para exercitar a view)"
  - "Task 1 seguiu TDD (RED→GREEN); Task 2 é type=auto (implementação + testes juntos)"

patterns-established:
  - "DELETE idempotente com tratamento 204/no-body no cliente Asaas"
  - "cancel-at-period-end: transição local só após sucesso da chamada externa"

requirements-completed: [ACCT-02]

# Metrics
duration: ~15min
completed: 2026-07-08
---

# Phase 2 Plano 02: Página de conta + cancelamento (cancel-at-period-end) Summary

**A página de conta está no ar (ACCT-02): o usuário autenticado vê status, próximo vencimento e o link de cobrança hospedado do Asaas, e cancela a assinatura pela própria conta. Cancelar chama `DELETE /v3/subscriptions/{id}` (método NOVO no `AsaasClient`, com o ramo 204/no-body tratado defensivamente — A5/Pitfall 7), para as renovações futuras e, só após o DELETE retornar sucesso, seta `Conta.status=CANCELADO` + `Conta.grace_ate=paid-through` (D-05: o gate segue liberando até o fim do período já pago). Tudo derivado de `request.user.conta` (anti-IDOR) e sem NENHUM dado de cartão na página (Pitfall 6). Suíte completa verde: 245 passed (+25 desta fase), sem migrations pendentes.**

## Performance
- **Duration:** ~15 min
- **Completed:** 2026-07-08
- **Tasks:** 2 (Task 1 TDD RED→GREEN; Task 2 auto)
- **Repo alvo:** `~/projects/lazari-capital` (código); `analista_dividendos` só recebe este SUMMARY + tracking
- **Files:** 3 criados + 4 modificados no repo lazari-capital

## Accomplishments
- **Task 1 (TDD) — `cancelar_assinatura` (DELETE) + `services.cancelar`:** `AsaasClient.cancelar_assinatura(sub_id)` faz `self._request('delete', f'/subscriptions/{sub_id}', retry_safe=True)` (DELETE idempotente). `_parse_resposta` agora aceita sucesso em `(200, 204)`: `204` OU `not resp.content` → `{}` (evita `resp.json()` cru em resposta sem corpo, A5/Open Q1), enquanto `200`+JSON continua devolvendo o dict (sem regressão). `services.cancelar(conta)`: `Assinatura.objects.get(conta=conta)`, chama o DELETE FORA do `transaction.atomic` (falha do Asaas propaga sem tocar o estado local), calcula paid-through (`trial_ate` se trial vigente, senão `proximo_vencimento`), converte para datetime aware fim-do-dia (`time.max` + `make_aware`) em `conta.grace_ate`, seta `conta.status=CANCELADO` e `assinatura.ciclo_status=CANCELADO` dentro do atomic.
- **Task 2 — ContaView + CancelarAssinaturaView + rotas + template:** `ContaView(LoginRequiredMixin, TemplateView)` expõe SOMENTE `conta.status` (display), `assinatura.proximo_vencimento`, `assinatura.invoice_url` e o flag `pode_cancelar`; CTA `[Assinar]` (→ `billing-assinar`) quando não há assinatura. `CancelarAssinaturaView(LoginRequiredMixin, View)` POST-only: valida server-side `Assinatura.objects.filter(conta).exclude(ciclo_status=CANCELADO).exists()` ANTES de chamar `services.cancelar` (WARNING 5 — usuário só-trial não estoura `DoesNotExist`); deriva a conta SEMPRE de `request.user.conta` (anti-IDOR, sem id do cliente); `AsaasError`/`DoesNotExist` viram mensagem amigável sem vazar `str(exc)`. Rotas `accounts:conta` (`/conta/`) e `accounts:cancelar-assinatura` (`/conta/cancelar/`). `templates/accounts/conta.html` estende `base_billing`, mostra status/vencimento/link/cancelar e NÃO renderiza nenhum dado de cartão (grep de `card|cartao|cartão|cvv|pan|numero_cartao` = 0).

## Task Commits
Commits atômicos no repo `~/projects/lazari-capital`:
1. **Task 1 (RED): testes falhando de cancelar_assinatura + services.cancelar** — `7e8410e` (test)
2. **Task 1 (GREEN): cancelar_assinatura (DELETE, trata 204) + services.cancelar** — `32d8af4` (feat)
3. **Task 2: ContaView + CancelarAssinaturaView + rotas + template (ACCT-02)** — `f5d5f36` (feat)

## Files Created/Modified
- `~/projects/lazari-capital/apps/billing/asaas_client.py` — + `cancelar_assinatura` (DELETE); `_parse_resposta` trata 204/no-body
- `~/projects/lazari-capital/apps/billing/services.py` — + `cancelar(conta)` (cancel-at-period-end)
- `~/projects/lazari-capital/apps/accounts/views.py` — + `ContaView` + `CancelarAssinaturaView`
- `~/projects/lazari-capital/apps/accounts/urls.py` — + rotas conta / cancelar
- `~/projects/lazari-capital/templates/accounts/conta.html` — página de conta (novo)
- `~/projects/lazari-capital/apps/billing/tests/test_cancelar.py` — testes de cliente+serviço (novo)
- `~/projects/lazari-capital/apps/accounts/tests/test_conta_view.py` — testes de view+rota+template (novo)

## Decisions Made
Ver `key-decisions` no frontmatter. Destaques: paid-through = trial_ate (se em trial) senão proximo_vencimento; grace_ate recebe fim-do-dia aware; `_parse_resposta` sucesso em (200,204); cancelar só transiciona local após DELETE OK.

## Verification
- `pytest apps/billing/tests/test_cancelar.py apps/accounts/tests/test_conta_view.py` → **24 passed** (12 + 12).
- `pytest apps/billing/tests/test_asaas_client.py` → **verde** (o ramo 204 não regride o caminho 200+JSON).
- `pytest apps/billing apps/accounts` → **195 passed** (baseline 170 do Plan 01; +25 desta fase, sem regressão).
- `pytest` (suíte completa) → **245 passed**.
- `python manage.py makemigrations --check --dry-run` → **No changes detected**.
- grep `card|cartao|cartão|cvv|pan|numero_cartao` em `templates/accounts/conta.html` → **0 ocorrências**.

## Threat Model Coverage
- **T-02-08 (Elevation/IDOR):** `conta`/`assinatura` derivados de `request.user.conta`; endpoint de cancelar sem parâmetro de id → impossível cancelar/ver assinatura alheia. ✅ (teste `test_post_autenticado_chama_cancelar_e_redireciona` confirma `arg.pk == conta.pk`)
- **T-02-09 (Info-disclosure, conta.html):** só status/vencimento/invoice_url; nenhum dado de cartão/PAN. ✅ (testes `test_nao_expoe_dado_sensivel_de_pagamento` + `test_template_conta_nao_contem_termos_de_cartao`)
- **T-02-10 (Info-disclosure, AsaasError):** view não renderiza `str(exc)`; `AsaasClient` já scrub a API key. ✅
- **T-02-11 (Tampering/CSRF):** cancelar é POST com `{% csrf_token %}`; GET → 405. ✅ (teste `test_get_nao_permitido`)
- **T-02-12 (Robustness):** DELETE 204/no-body tratado sem `resp.json()` cru; falha do Asaas não corrompe estado local. ✅ (testes `test_delete_204_...` + `test_falha_do_asaas_nao_transiciona_estado_local`)

## Deviations from Plan
None — plano executado exatamente como escrito.

## TDD Gate Compliance
Task 1 (`tdd="true"`) seguiu RED→GREEN:
- RED: `7e8410e` (test) — `ImportError: cannot import name 'cancelar'` confirmado antes da implementação.
- GREEN: `32d8af4` (feat) — implementação; 35 testes passando (cancelar + asaas_client sem regressão).
- REFACTOR: não necessário.

## Known Stubs
Nenhum. `cancelar` está totalmente cabeado (AsaasClient real em produção / mockado em teste). A página lê dados reais de `Conta`/`Assinatura`.

## Issues Encountered
None.

## Next Phase Readiness
- Pronto para o Plan 03 (mesma fase): estender o `GateView` (BILL-04) para honrar paid-through/grace/cancel-at-period-end via `grace_ate`, e adicionar `accounts:conta`/`accounts:cancelar-assinatura`/`billing-assinar` ao `EXEMPT_URL_NAMES` do `BillingGateMiddleware` (hoje uma conta CANCELADO é redirecionada para conta-suspensa ANTES de alcançar /conta/ — Pitfall 2; por isso os testes de view usam conta ATIVO).

## Self-Check: PASSED
- Arquivos criados/modificados verificados no repo lazari-capital.
- Commits `7e8410e`, `32d8af4`, `f5d5f36` presentes em `git log`.

---
*Phase: 02-cobran-a-asaas-webhooks-conta*
*Completed: 2026-07-08*
