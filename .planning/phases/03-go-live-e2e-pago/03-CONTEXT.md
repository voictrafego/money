# Phase 3: Go-live E2E pago - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Colocar tudo **no ar** sob a marca **Lazari Capital**, na VPS (Docker Swarm + Traefik):
o front **Django** (auth + billing + conta, do repo `~/projects/lazari-capital`), o **gate
Traefik forward-auth** e o engine **Streamlit** (`analista_dividendos`, intacto atrás do gate)
integrados, com **segredos (Asaas/DB/SMTP) fora do git**, e validado por um **teste E2E pago**
(cadastro → trial → pagamento → acesso → cancelamento → bloqueio). Requisito único: **OPS-01**.

Ponto de atenção travado pelo ROADMAP: os **websockets do Streamlit** têm de funcionar atrás do
forward-auth (app carrega e interage sem quebra de sessão nem loop de auth) — critério de sucesso #3.

**Em escopo:** buildar/deployar as duas imagens (`web` Django + `money` Streamlit) na mesma
overlay `network_swarm_public`; DNS/TLS dos hosts Lazari Capital; roteamento Traefik + gate
forward-auth ao vivo; cookie de sessão compartilhado entre os dois hosts; `.env` de produção fora
do git (chaves Asaas de produção, Resend/SMTP prod, DATABASE_URL); seed do `Plano` PRO; redirect
301 do domínio antigo; landing mínima de vendas em `www`; teste E2E pago (sandbox + smoke real);
verificação de que os websockets do Streamlit sobrevivem ao gate.

**Fora de escopo (Future / pós-v2.0):** landing de marketing/SEO completa, múltiplos planos/tiers,
OAuth, afiliados/cupons, migração do front p/ React. Nada de recomendação de investimento (CVM).
</domain>

<decisions>
## Implementation Decisions

### Teste E2E pago (OPS-01, critério #2)
- **D-01:** **Asaas sandbox p/ o fluxo automatizável + 1 smoke real manual.** O E2E percorre
  cadastro → trial → `PAYMENT_CONFIRMED` (webhook simulado/sandbox) → acesso → cancelar → bloqueio
  no **sandbox do Asaas** (sem dinheiro, repetível/CI-friendly). Depois, **1 cobrança real de
  R$ 19,90** no cartão próprio como smoke final antes de anunciar — confirma chaves de produção +
  checkout real + Traefik/gate reais — **com estorno** logo em seguida.
- **D-02:** O E2E do fluxo reusa a suíte de billing já travada na Phase 2 (`test_webhook_ciclo.py`
  etc.) como base — a novidade da Phase 3 é exercitá-lo **ao vivo** (Traefik + gate + Streamlit
  reais), não reescrever a lógica. Simulação de webhook = POST assinado no endpoint público, como
  os testes de idempotência já fazem.

### Domínios, TLS e cutover
- **D-03:** **Hostnames finais:** `app.lazaricapital.com.br` → **Streamlit** (gated);
  `www.lazaricapital.com.br` → **Django** (cadastro/login/assinar/conta/webhook/gate).
- **D-04:** `money.voictech.com.br` (app atual, hoje sem gate) → **redirect 301 permanente** para o
  novo domínio. Cutover é hard-cut (não manter os dois indefinidamente); 301 preserva quem tiver o
  link antigo.
- **D-05:** **Cookie de sessão no parent `.lazaricapital.com.br`** (`SESSION_COOKIE_DOMAIN`) para o
  gate (chamado pelo Traefik no host `app.`) reconhecer a sessão emitida pelo Django no host `www.`.
  Consequência técnica direta da escolha app/www separados — os dois hosts precisam do domínio-pai
  comum. `CSRF_TRUSTED_ORIGINS`/`ALLOWED_HOSTS` cobrem ambos os subdomínios.
- **D-06:** DNS: `www` e `app` (e apex, se usado p/ redirect) no **Cloudflare → VPS 31.97.130.40**;
  **nuvem cinza (DNS-only)** nos hosts que emitem TLS pelo Let's Encrypt/Traefik, senão a emissão do
  certificado falha (mesma pegadinha registrada no `docker-stack.yml` do crm-voic p/ o SAN `www`).

### Porta de entrada / escopo do go-live
- **D-07:** Go-live inclui uma **landing mínima de vendas** em `www` (o que é, preço R$ 19,90,
  disclaimer educacional "sem recomendação", CTA assinar/cadastrar) + o funil `/cadastro`,`/entrar`,
  `/conta`. Estreia a marca de forma apresentável. A landing de marketing/SEO **completa** fica
  para fase própria pós-v2.0.
- **D-08:** A landing herda a marca Lazari Capital das telas da Phase 1 (Preline/Tailwind); é
  intencionalmente enxuta — não é trabalho de copywriting/SEO de conversão nesta fase.

### Segredos e virada de produção
- **D-09:** **Padrão crm-voic:** segredos num **`.env` fora do git em `/opt/lazari-capital`** na VPS,
  injetado via `env_file` no `docker stack deploy` (como o crm-voic já opera). NÃO usar docker
  secrets nesta fase (fugiria do padrão e exigiria mexer em entrypoint/settings).
- **D-10:** O `.env` de produção carrega as **chaves Asaas de PRODUÇÃO** (virada de sandbox→prod
  acontece aqui, no deploy), **Resend/SMTP de produção** (o e-mail de verificação é caminho crítico
  do trial — D-08 da Phase 1) e a `DATABASE_URL` do Postgres de produção. Postgres dedicado numa
  rede interna isolada (padrão `db` + `crm_internal` do crm-voic).
- **D-11:** **Seed do `Plano` PRO (R$ 19,90, MONTHLY)** roda no deploy (data migration ou management
  command no entrypoint), idempotente — sem ele o checkout não tem plano p/ assinar.

### Claude's Discretion
- **Websockets do Streamlit atrás do forward-auth** (critério #3): abordagem técnica é do
  **researcher/planner** — Streamlit usa WS em `/_stcore/stream`; garantir que o Traefik faça
  upgrade de WS e que o forward-auth não reautentique cada frame WS (a sessão/cookie deve bastar).
  Decisão de fallback aceitável fica com o planner, mas o critério é: app carrega e interage sem
  loop de auth.
- Estrutura exata dos arquivos de deploy (adaptar o `docker-stack.yml` herdado do crm-voic — hoje
  aponta p/ pocketleads — para os hosts/serviços Lazari Capital), ordem de subida dos serviços,
  organização do `entrypoint.sh` (migrate/collectstatic/seed).
- Onde exatamente mora o redirect 301 do `money.voictech.com.br` (router Traefik no stack do
  Streamlit vs no do Django) e a mecânica do apex.
- Se o Postgres sobe como serviço no stack ou reusa instância existente — planner decide pela infra
  atual da VPS.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos & roadmap (repo analista_dividendos)
- `.planning/REQUIREMENTS.md` — **OPS-01** (fonte do critério) + arquitetura decidida (gateway híbrido)
- `.planning/ROADMAP.md` §"Phase 3: Go-live E2E pago" — goal + 3 success criteria (inclui websockets)
- `.planning/PROJECT.md` §"Current Milestone"/"Key Decisions" — marca Lazari Capital, gate Traefik forward-auth, Asaas conta própria, Postgres fonte de verdade
- `.planning/phases/01-funda-o-cadastro-login-gate-e-trial/01-CONTEXT.md` — D-10/D-11 (contrato do gate + Streamlit sem porta pública) + integration point cookie/domínio compartilhado
- `.planning/phases/02-cobran-a-asaas-webhooks-conta/02-CONTEXT.md` — Plano PRO R$19,90, checkout hospedado, política de graça/cancelamento (o que o E2E deve exercitar)

### Deploy / infra a adaptar
- `/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos/stack.yml` — deploy do Streamlit `money`: **já tem** o middleware `lazari-gate.forwardauth` → `http://web:8000/gate/`, `authResponseHeaders=X-User-Email`, sem porta pública. Só falta host final + rede compartilhada com `web`.
- `~/projects/lazari-capital/docker-stack.yml` — stack Django herdado do crm-voic (hoje aponta pocketleads/crm.voictech) — **adaptar** hosts/serviços p/ Lazari Capital; contém as pegadinhas (labels no nível do serviço, `$$` p/ escapar `${1}`, DNS antes do deploy p/ TLS, `start_period` 180s).
- `~/projects/lazari-capital/Dockerfile` + `entrypoint.sh` — build + migrate/collectstatic no boot (onde entra o seed do Plano PRO).
- `~/projects/lazari-capital/config/settings/prod.py` — settings prod + Resend/SMTP; onde setar `SESSION_COOKIE_DOMAIN`/`CSRF_TRUSTED_ORIGINS`/`ALLOWED_HOSTS` p/ o par www/app.

### Padrão de deploy de referência (crm-voic, já operando na VPS)
- `~/projects/crm-voic/docker-stack.yml` — padrão Swarm single-node (build `:latest` local → `docker stack deploy`, `env_file: .env`, `db` em rede interna, worker, healthcheck, redirect apex→www).
- `~/projects/crm-voic/scripts/backup.sh`, `restore_verify.sh` — rotina de backup do Postgres (referência p/ produção).

### Infra compartilhada da VPS
- VPS `31.97.130.40` (root via SSH, chave `id_ed25519_vps`), Docker Swarm + Traefik, overlay externa `network_swarm_public`, `letsencryptresolver`. Domínio `lazaricapital.com.br` no Cloudflare.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`stack.yml` do Streamlit** já wired com o gate forward-auth e sem porta pública (D-11 da Phase 1) — a Phase 3 só finaliza host, rede compartilhada e valida ao vivo.
- **`docker-stack.yml`/`Dockerfile`/`entrypoint.sh` do lazari-capital** (fork do crm-voic) — base de deploy pronta, precisa de re-branding de hosts/domínio.
- **Padrão crm-voic completo** (Traefik labels, `.env` via env_file, `db` isolado, worker, backup scripts, redirect apex→www) — copiar/adaptar em vez de inventar.
- **Suíte de billing/gate da Phase 2** (`test_webhook_ciclo.py`, testes do GateView, `test_billing_gate.py`) — base do E2E; a Phase 3 a exercita ao vivo.

### Established Patterns
- Swarm single-node **sem registry**: imagem `:latest` buildada localmente antes do `docker stack deploy`.
- Traefik como **único ingresso**; gate forward-auth na frente do Streamlit; Streamlit nunca publica porta (anti-spoof de `X-User-Email`).
- Migrate/collectstatic no entrypoint a cada boot; `start_period` alto (180s) p/ o Swarm não matar o container como unhealthy durante o boot.

### Integration Points
- **`money` (Streamlit) ↔ `web` (Django)**: os dois serviços PRECISAM compartilhar a overlay `network_swarm_public` p/ o `forwardauth.address=http://web:8000/gate/` alcançar o Django (RESEARCH A3 da Phase 1).
- **Cookie Django ↔ host do Streamlit**: `SESSION_COOKIE_DOMAIN=.lazaricapital.com.br` (D-05) — o gate no host `app.` lê a sessão emitida no host `www.`.
- **Websockets Streamlit ↔ Traefik ↔ gate** (`/_stcore/stream`): ponto crítico #3 — Traefik precisa fazer upgrade de WS e o forward-auth não pode reautenticar cada frame.
- **Seed `Plano` PRO ↔ deploy**: management command/migration no entrypoint (Phase 2 deixou isso p/ o deploy).

</code_context>

<specifics>
## Specific Ideas

- Estreia sob **Lazari Capital**: `app.lazaricapital.com.br` (produto) + `www.lazaricapital.com.br`
  (Django/landing mínima). `money.voictech.com.br` vira 301.
- **1 smoke real de R$ 19,90 no cartão próprio** antes de anunciar, com estorno — o resto do E2E no
  sandbox do Asaas.
- Espelhar o deploy do crm-voic (padrão que "vai bem" na VPS), divergindo só nos hosts/marca.
</specifics>

<deferred>
## Deferred Ideas

- **Landing de marketing/SEO completa** da Lazari Capital (copy de conversão, blog, SEO) → fase própria pós-v2.0. A Phase 3 entrega só a landing mínima (D-07).
- **Múltiplos planos/tiers, plano anual, cupons, afiliados, OAuth Google** → Future (pós-v2.0).
- **Docker secrets / Swarm secrets** (em vez de `.env`) → reavaliar depois; Phase 3 usa `.env` (D-09).
- **Migração do front p/ React+Vite** → Future; o engine segue em Streamlit atrás do gate.
- **Poda do maquinário multi-tenant dormante** → reavaliar se o B2C nunca precisar de equipes.

None além dos acima — a discussão permaneceu no escopo do OPS-01.

</deferred>

---

*Phase: 3-Go-live E2E pago*
*Context gathered: 2026-07-08*
