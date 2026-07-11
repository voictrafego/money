---
phase: 01-funda-o-cadastro-login-gate-e-trial
plan: 05
subsystem: auth
tags: [streamlit, traefik, forward-auth, header, identity, x-user-email, stack-swarm]

# Dependency graph
requires:
  - "01-04: contrato do gate — endpoint GET /gate/ (web:8000) responde 200 + header X-User-Email para sessão ATIVA+trial; 302 caso contrário (apenas strings, sem arquivo compartilhado)"
provides:
  - "app.py: _current_user_email() lê X-User-Email via st.context.headers (read-only, AUTH-03) — fallback None fora do gate (dev)"
  - "requirements.txt: streamlit>=1.37 (pino mínimo para st.context.headers)"
  - "stack.yml: middleware Traefik forwardAuth (lazari-gate) apontando ao gate + authResponseHeaders=X-User-Email + Streamlit sem porta pública (D-11)"
affects: [02-billing-asaas, 03-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Streamlit como consumidor PASSIVO de identidade: lê X-User-Email injetado pelo gate/Traefik; NUNCA autoriza acesso (autoridade é 100% Django+Traefik, D-10)"
    - "Ingresso único via Traefik+gate: money sem bloco ports: (só rede overlay), forwardAuth roda antes do roteamento — spoof de X-User-Email só é possível se o app vazar fora do Traefik (D-11/Pitfall 1)"
    - "st.context.headers (>=1.37) como leitura oficial read-only e case-insensitive, sem hacks de tornado/WSGI"

key-files:
  created:
    - ".planning/phases/01-funda-o-cadastro-login-gate-e-trial/01-05-SUMMARY.md"
  modified:
    - "app.py"
    - "requirements.txt"
    - "stack.yml"

key-decisions:
  - "Leitura do header em try/except retornando None: fora do gate (dev local sem Traefik) o app trata como anônimo/dev sem quebrar o boot (T-01-26)"
  - "user_email atribuído no boot mas não consumido ainda (marcado noqa F841) — o ponto de personalização/telemetria fica cabeado no lugar certo; consumo real (ex.: 'logado como') é escopo posterior"
  - "stack.yml preserva loadbalancer.server.port=8501 como alvo INTERNO do router (não porta pública) e não introduz bloco ports: — ingresso só via Traefik+gate"
  - "forwardauth.address=http://web:8000/gate/ assume money e web (Django lazari-capital) na mesma rede overlay Swarm — efetivação/deploy é Fase 3 (RESEARCH A3)"

requirements-completed: [AUTH-03, AUTH-02]

# Metrics
duration: ~4min
completed: 2026-07-08
---

# Phase 1 Plano 05: Propagação de identidade no Streamlit (X-User-Email) + forwardAuth Summary

**A identidade do usuário chega confiável ao Streamlit (AUTH-03): o `app.py` agora lê `X-User-Email` no boot via `st.context.headers` (streamlit bumpado para `>=1.37`) de forma estritamente read-only — o gate Django/Traefik do Plano 04 já decidiu quem entra, então o app só usa o e-mail para personalização/telemetria, nunca para autorizar; e o `stack.yml` fecha a infra de AUTH-02 declarando o middleware Traefik `forwardAuth` (`lazari-gate`) que chama `http://web:8000/gate/` antes de rotear ao app, promove `X-User-Email` via `authResponseHeaders`, e mantém o Streamlit sem porta pública (só rede overlay, D-11) — os 338 testes golden do engine seguem verdes após o bump.**

## Performance
- **Duration:** ~4 min
- **Tasks:** 3 (Task 1 código app/deps; Task 2 validação golden; Task 3 infra stack.yml)
- **Repo alvo:** `analista_dividendos` (ESTE repo — plano normal single-repo)
- **Files:** 1 criado (SUMMARY) + 3 modificados (app.py, requirements.txt, stack.yml)

## Accomplishments
- **Task 1 — bump streamlit + leitura de X-User-Email:** `requirements.txt` subiu de `streamlit>=1.30` para `>=1.37` (mínimo para `st.context`). Em `app.py`, logo após `st.set_page_config(...)`, adicionada `_current_user_email() -> str | None` que faz `st.context.headers.get("X-User-Email")` dentro de try/except (retornando None fora do gate), e `user_email = _current_user_email()`. Docstring/comentário deixam explícito: read-only, injetado pelo gate (AUTH-03), NUNCA autoriza acesso. Nenhuma lógica de dados/engine tocada.
- **Task 2 — suíte golden verde após o bump:** `pytest -q` = **338 passed** com o streamlit já em 1.58.0 (>=1.37, já presente no `.venv`). Nenhuma quebra de API entre 1.30→1.37+; nenhuma fórmula do engine (`src/analista/**`) alterada — compatibilidade preservada (CLAUDE.md). `ast.parse(app.py)` OK (boot não quebra com a nova referência a `st.context`).
- **Task 3 — forwardAuth no stack.yml:** no bloco `deploy.labels` do service `money`, adicionadas as 4 labels: `middlewares.lazari-gate.forwardauth.address=http://web:8000/gate/`, `...authResponseHeaders=X-User-Email`, `...trustForwardHeader=true`, e `routers.money.middlewares=lazari-gate`. Comentários documentam D-11 (sem `ports:`, ingresso só via Traefik+gate), a necessidade de `money` e `web` na mesma rede overlay, e que deploy/websockets são Fase 3. `loadbalancer.server.port=8501` preservado como alvo interno do router (não porta pública). YAML válido.

## Task Commits
Commits atômicos no repo `analista_dividendos`:
1. **Task 1: bump streamlit>=1.37 + leitura read-only de X-User-Email** — `4198e08` (feat)
2. **Task 2: validação da suíte golden (338 passed)** — sem commit (validação, nenhum arquivo alterado)
3. **Task 3: stack.yml forwardAuth + Streamlit sem porta pública** — `df35721` (feat)

_Este SUMMARY.md é commitado separadamente._

## Verification
- `grep streamlit>=1.37 requirements.txt` OK; `streamlit>=1.30` removido.
- `grep st.context.headers app.py` OK; `_current_user_email` com fallback None; comentário read-only/não-autoriza presente.
- `python -c "import ast; ast.parse(open('app.py').read())"` sem SyntaxError.
- `pytest -q` = **338 passed** (suíte golden do engine intacta pós-bump).
- `stack.yml`: 4 labels forwardAuth presentes; `! grep -qE '^[[:space:]]*ports:'` (sem publicação de host); `yaml.safe_load` sem erro.

## Deviations from Plan
None - plan executed exactly as written.

Observação (não-desvio): o `.venv` do projeto já continha `streamlit 1.58.0` (>=1.37), portanto não foi necessário reinstalar para rodar a Task 2 — o pino em `requirements.txt` foi ajustado como especificado.

## Threat Flags
Nenhuma superfície de segurança nova fora do `<threat_model>` do plano. Mitigações aplicadas:
- **T-01-23** (spoof de X-User-Email): stack.yml sem `ports:` (só rede overlay/Traefik, D-11); `authResponseHeaders` do gate substitui headers conflitantes de entrada.
- **T-01-24** (EoP via header): `_current_user_email` é read-only e documentado como NÃO-autorizador; decisão de acesso é 100% do gate (Plano 04).
- **T-01-25** (bump quebrar o engine): Task 2 rodou a suíte golden com 0 failures (338 passed) antes de aceitar o bump; nenhuma fórmula tocada.
- **T-01-26** (exceção em dev sem header): leitura em try/except → None fora do gate; nenhum stack trace vazado.

## Known Stubs
- **`user_email` ainda não consumido na UI:** o valor é lido e atribuído no boot (ponto de personalização/telemetria posicionado no lugar certo), mas nenhum render usa "logado como fulano" ainda. Intencional para a Fase 1 — o objetivo do plano é fechar a PROPAGAÇÃO da identidade (AUTH-03), não o consumo visual. Não bloqueia AUTH-03: o header é lido de forma confiável.
- **Efetivação na VPS (deploy + E2E + websockets):** as labels forwardAuth e o header-read estão versionados/validados em isolamento, mas o deploy real, o teste E2E do gate→app e a validação de websockets atrás do Traefik são escopo da **Fase 3** (OPS-01), conforme o plano.

## Self-Check: PASSED
- Arquivos modificados existem e contêm o esperado: `requirements.txt` (streamlit>=1.37), `app.py` (st.context.headers + _current_user_email), `stack.yml` (forwardauth.address, authResponseHeaders=X-User-Email, routers.money.middlewares=lazari-gate). FOUND
- SUMMARY criado: `.planning/phases/01-funda-o-cadastro-login-gate-e-trial/01-05-SUMMARY.md`. FOUND
- Commits `4198e08` (Task 1) e `df35721` (Task 3) existem no repo `analista_dividendos`. FOUND
- `pytest -q` = 338 passed; `yaml.safe_load(stack.yml)` OK; `ast.parse(app.py)` OK. VERIFIED

## Next Phase Readiness
- **Fase 2 (billing Asaas):** quando a assinatura paga entrar (trial_ate=None mantendo status=ATIVO), a extensão está no gate Django (`GateView`, já comentada) — o lado Streamlit não muda; `X-User-Email` continua sendo a chave de identidade para atrelar telemetria/personalização por assinante.
- **Fase 3 (deploy/infra):** confirmar `money` e `web` na mesma rede overlay Swarm (RESEARCH A3), efetivar as labels via `docker stack deploy`, e validar E2E (gate 302/200) + websockets do Streamlit atravessando o middleware. Domínio/host real do gate a travar na Fase 3.

---
*Phase: 01-funda-o-cadastro-login-gate-e-trial*
*Completed: 2026-07-08*
