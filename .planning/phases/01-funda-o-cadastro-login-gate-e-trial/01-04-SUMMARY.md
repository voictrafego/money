---
phase: 01-funda-o-cadastro-login-gate-e-trial
plan: 04
subsystem: auth
tags: [django, forward-auth, gate, traefik, trial, session-cookie, lazari-capital]

# Dependency graph
requires:
  - "01-01: repo lazari-capital (fork-and-prune), Conta.status/trial_ate como fonte de verdade, User↔Conta 1:1, config/urls + settings limpos"
  - "01-02: trial de 7 dias armado na verificação de e-mail (status=ATIVO, trial_ate=hoje+7)"
provides:
  - "apps/gate: GateView (GET, read-only, sem CSRF) que o Traefik forwardAuth chama — 200 + header X-User-Email quando status=ATIVO E trial_ate>=hoje; 302 login p/ anônimo/sem conta; 302 /trial-acabou/ p/ trial expirado ou trial_ate=None (fail-closed)"
  - "Rota /gate/ (name=gate) montada na raiz — alvo do forwardAuth.address do Plano 05 (http://web:8000/gate/)"
  - "TrialAcabouView + rota /trial-acabou/ (name=trial-acabou): página pública standalone fora do gate (sem loop) com botão [Assinar] placeholder (D-12)"
  - "templates/gate/trial_acabou.html na marca Lazari Capital, tom software-educacional"
  - "Hardening de cookie em domínio-pai no prod.py: SESSION_COOKIE_DOMAIN/CSRF_COOKIE_DOMAIN via env (default de domínio-pai), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax'; SECURE_PROXY_SSL_HEADER preservado"
affects: [01-05-traefik-labels-header-streamlit, 02-billing-asaas, 03-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate como VIEW Django dedicada (não middleware): read-only, fail-closed por default, chamada pelo Traefik forwardAuth — deriva de core/middleware/billing_gate.py mas protege um serviço externo (Streamlit), não rotas Django"
    - "Semântica de acesso extensível p/ Fase 2: status==ATIVO AND trial_ate>=hoje hoje; comentado o OR assinatura_paga (trial_ate=None) da Fase 2 (RESEARCH A5)"
    - "Rota de bloqueio (trial-acabou) fora do endpoint /gate/ p/ não recursar pelo próprio gate (T-01-21 / Open Q4)"

key-files:
  created:
    - "~/projects/lazari-capital/apps/gate/__init__.py"
    - "~/projects/lazari-capital/apps/gate/apps.py"
    - "~/projects/lazari-capital/apps/gate/views.py"
    - "~/projects/lazari-capital/apps/gate/urls.py"
    - "~/projects/lazari-capital/apps/gate/tests/__init__.py"
    - "~/projects/lazari-capital/apps/gate/tests/test_gate.py"
    - "~/projects/lazari-capital/templates/gate/trial_acabou.html"
  modified:
    - "~/projects/lazari-capital/config/settings/base.py"
    - "~/projects/lazari-capital/config/urls.py"
    - "~/projects/lazari-capital/config/settings/prod.py"

key-decisions:
  - "GateView referencia trial-acabou por NAME (redirect('trial-acabou')) e login por NAME (redirect('login')) — resolvem para /trial-acabou/ e /entrar/; sem hard-code de path"
  - "Gate montado em include('apps.gate.urls') ANTES de users.urls na raiz — /gate/ e /trial-acabou/ não colidem com as rotas de auth existentes"
  - "trial_ate=None com status=ATIVO cai como bloqueio (fail-closed) na Fase 1; será o gancho de 'assinatura paga sem trial' na Fase 2 (adicionar OR)"
  - "Página trial-acabou estende billing/base_billing.html (mesmo layout standalone das telas de verificação/status), sem sidebar autenticada"

requirements-completed: [AUTH-02, ACCT-01]

# Metrics
duration: ~3min
completed: 2026-07-08
---

# Phase 1 Plano 04: Gate de acesso (forward-auth) + trial-acabou + cookie domínio-pai Summary

**O gate de acesso (AUTH-02) está no ar: uma `GateView` Django leve, GET e read-only — que o Traefik forwardAuth chamará antes de rotear ao Streamlit — resolve a sessão pelo cookie, lê a fonte de verdade `Conta.status`/`trial_ate` e decide fail-closed: 200 + header `X-User-Email` para sessão ATIVA com trial no futuro, 302 login para anônimo/sem conta, 302 para a página pública "seu trial acabou" (com [Assinar] placeholder, D-12) quando o trial expirou; somando o hardening de cookie em domínio-pai (`SESSION_COOKIE_DOMAIN`) para o cookie chegar ao gate — suíte inteira verde (200 passed, +10 do gate).**

## Performance
- **Duration:** ~3 min
- **Tasks:** 3 (Task 1 e 2 TDD RED→GREEN; Task 3 settings)
- **Repo alvo:** `~/projects/lazari-capital` (código); `analista_dividendos` só recebe este SUMMARY
- **Files:** 7 criados + 3 modificados no repo lazari-capital

## Accomplishments
- **Task 1 — GateView + rota /gate/:** app `apps/gate` novo (registrado em INSTALLED_APPS). `GateView(View)` com `http_method_names=["get"]`: anônimo → `redirect("login")`; `conta=user.conta` None → `redirect("login")`; `ativo_ou_trial = status==ATIVO AND trial_ate is not None AND trial_ate>=timezone.localdate()`; senão → `redirect("trial-acabou")`; senão `HttpResponse(200)` com `resp["X-User-Email"]=user.email`. Extensão Fase 2 (assinatura paga com trial_ate=None) comentada. Rota `path("gate/", …, name="gate")` incluída na raiz do `config/urls.py`. Sem decorator de CSRF nem login_required (grep confirma — a lógica de auth é a própria view).
- **Task 2 — página trial-acabou (D-12):** `TrialAcabouView(TemplateView)` + `path("trial-acabou/", …, name="trial-acabou")`. `templates/gate/trial_acabou.html`: standalone na marca Lazari Capital, copy "Seu período de teste terminou", tom software-educacional, botão **[Assinar]** placeholder (âncora `#assinar`; Fase 2 = checkout Asaas) e link de logout. Pública, fora do endpoint /gate/ (sem loop de redirect).
- **Task 3 — cookie em domínio-pai:** no bloco de hardening do `config/settings/prod.py`, `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` via `env(...)` com default `.lazaritechcapital.com.br` (placeholder, sem hard-block), `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`; `SECURE_PROXY_SSL_HEADER` preservado (Pitfall 2). Comentário documenta NÃO setar `authRequestHeaders` no Traefik e que o domínio real trava na Fase 3.
- **Testes:** `apps/gate/tests/test_gate.py` (10) — allow (200+X-User-Email==email), anon→302 login, POST→405, conta None→302 login, read-only (não muta Conta), trial expirado→302 trial-acabou, trial_ate=None→302 trial-acabou, GET /trial-acabou/→200 com "Assinar", página pública sem login, standalone sem sidebar.

## Task Commits
Commits atômicos no repo `~/projects/lazari-capital`:
1. **Task 1: app gate — GateView forward-auth + rota /gate/** — `4470fca` (feat)
2. **Task 2: página trial-acabou (D-12) + rota + casos de bloqueio** — `8ab545e` (feat)
3. **Task 3: hardening de cookie em domínio-pai (prod.py)** — `ed9d80e` (feat)

_SUMMARY.md commitado separadamente no repo `analista_dividendos`._

## TDD Gate Compliance
Task 1 e Task 2 seguiram RED→GREEN: os testes de decisão (allow/anon/método) foram escritos e rodados antes da lógica (falha por app/rota inexistentes), depois verdes. Por consistência com o padrão dos Planos 01-01/01-02/01-03 (um commit atômico por task), cada task foi um único commit `feat` contendo teste + implementação, em vez de commits `test`/`feat` separados. Sem regressão: a suíte inteira (200) fecha verde.

## Verification
- `reverse('gate')` = `/gate/`, `reverse('trial-acabou')` = `/trial-acabou/` — ambos resolvem sem NoReverseMatch.
- `pytest apps/gate/tests/test_gate.py` = 10 passed; suíte do projeto = **200 passed** (era 190 no 01-03; +10 do gate).
- `config/settings/prod.py` carrega com `SESSION_COOKIE_DOMAIN='.lazaritechcapital.com.br'`, `SESSION_COOKIE_SAMESITE='Lax'`, `SESSION_COOKIE_HTTPONLY=True`, `CSRF_COOKIE_DOMAIN='.lazaritechcapital.com.br'`, `SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')`.
- `manage.py check` sem issues; grep confirma ausência de csrf_exempt/login_required em `apps/gate/views.py`.

## Deviations from Plan
None - plan executed exactly as written.

Observação: a rota do gate foi incluída como `path("", include("apps.gate.urls"))` (montando `/gate/` e `/trial-acabou/` na raiz), consistente com o forwardAuth.address `/gate/` previsto para o Plano 05 — dentro da discricionariedade de rota do plano, não é um desvio.

## Known Stubs
- **Botão [Assinar] placeholder (D-12, intencional):** em `templates/gate/trial_acabou.html` o CTA aponta para a âncora `#assinar` — na Fase 1 é o ponto de conversão posicionado no lugar certo; o destino real (checkout Asaas) é cabeado na **Fase 2**. Não bloqueia AUTH-02: o gate já bloqueia/libera corretamente e a página é servida.
- O par Traefik-labels (`forwardauth.address`/`authResponseHeaders`) + a leitura de `X-User-Email` no Streamlit (`st.context.headers`) são escopo do **Plano 05** (repo analista_dividendos), não deste plano. O gate lado-Django está completo e testado em isolamento.

## Threat Flags
Nenhuma superfície de segurança nova fora do `<threat_model>` do plano. Mitigações aplicadas e cobertas por teste:
- **T-01-17** (bypass de auth / EoP): GateView fail-closed — anônimo/sem conta → 302 login; só ATIVO+trial futuro → 200; testes `anon`/`conta_none`/`allow`.
- **T-01-18** (vazar o app ao anônimo): 302 redirect antes de qualquer proxy ao Streamlit (o app só é alcançado após 200).
- **T-01-19** (tampering de trial/status): gate read-only — teste `read_only_nao_muta_conta` prova status/trial_ate inalterados; comparação server-side com `timezone.localdate()`.
- **T-01-20** (cookie roubado/hijack): `SESSION_COOKIE_SECURE`+`HTTPONLY`+`SameSite=Lax` (prod.py) + HSTS já presente; domínio-pai limita escopo.
- **T-01-21** (loop de redirect gate↔trial-acabou/login): trial-acabou e login são rotas públicas fora do endpoint /gate/ (não recursam); testes de página pública.
- **T-01-22** (CSRF no gate): aceito — gate é GET read-only sem efeito colateral; grep confirma ausência de csrf/login_required.

## Self-Check: PASSED
- Arquivos criados existem: `apps/gate/{__init__,apps,views,urls}.py`, `apps/gate/tests/{__init__,test_gate}.py`, `templates/gate/trial_acabou.html`. FOUND
- Commits `4470fca`, `8ab545e`, `ed9d80e` existem no repo lazari-capital. FOUND
- `pytest apps/gate/tests/test_gate.py` = 10 passed; suíte do projeto = 200 passed; `manage.py check` sem issues. VERIFIED
- `reverse('gate')`/`reverse('trial-acabou')` resolvem; prod.py com SESSION_COOKIE_DOMAIN/CSRF_COOKIE_DOMAIN/SAMESITE/HTTPONLY + SECURE_PROXY_SSL_HEADER. VERIFIED

## Next Phase Readiness
- Pronto para o **Plano 05** (repo `analista_dividendos`): adicionar as labels Traefik forwardAuth (`address=http://web:8000/gate/`, `authResponseHeaders=X-User-Email`) ao router do `money`, tirar o Streamlit de acesso público (só rede interna Swarm — D-11), e ler `X-User-Email` via `st.context.headers` no boot do `app.py` (bump `streamlit>=1.37`).
- Nota Fase 2: quando a assinatura paga entrar (trial_ate=None mantendo status=ATIVO), estender `ativo_ou_trial` para `... OR assinatura_paga` na `GateView` (já comentado no código).
- Nota Fase 3 (infra): confirmar o domínio real comprado e travar `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` (hoje placeholder via env); confirmar a versão do Traefik (v3.x assumido).

---
*Phase: 01-funda-o-cadastro-login-gate-e-trial*
*Completed: 2026-07-08*
