# Phase 6: Redeploy do app v2.3 na VPS - Context

**Gathered:** 2026-07-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Subir o código **v2.3** (engine `money` / Streamlit) para produção no Swarm da VPS, fechando o loop
até o usuário real. O app deployado (Lazari Capital) ainda roda comportamento **pré-v2.2** — então
o salto é **pré-v2.2 → v2.3**. Ao fim, ITUB4 no app ao vivo deve mostrar arquétipo (financeira→RIM),
o intrínseco calibrado do RIM (~R$32-40) e o veredito "ver motor primário", **não** mais "Evitar" com
faixa DDM R$12,93–19,32 (OPS-01).

**Dentro do escopo:** entrega do código à VPS, rebuild da imagem `money:latest`, redeploy no stack
`lazari`, rollback safety, e validação (smoke) pós-deploy. **Fora do escopo:** qualquer mudança de
engine/valuation (feito nas Fases 4-5), mudança de arquitetura do gate/Traefik, novas features.

</domain>

<decisions>
## Implementation Decisions

### Execução do deploy
- **D-01:** Claude **dirige o deploy via SSH direto** na VPS (`ssh -i ~/.ssh/id_ed25519_vps root@31.97.130.40`),
  executando os comandos de produção (rebuild, service update, cutover) e mostrando output. O operador
  optou por autonomia — **sem checkpoint humano por comando**.
- **D-02:** Fallback: se o SSH pedir auth interativa nesta sessão (chave com passphrase, host key
  prompt), Claude entrega o comando exato para o operador rodar via `! ssh ...` no prompt.

### Entrega do código v2.3 → VPS
- **D-03:** Fluxo **push → github → git pull**: `gh auth switch -u voictrafego` (a conta `voictrafego`
  é a única com permissão no remote `voictrafego/money`; `voicproducoes` dá 403) → `git push origin main`
  → `git pull` (checkout da tag, ver D-04) em `/root/money` na VPS. Github é a fonte de verdade.
- **D-04:** **Criar + push da tag git `v2.3`** e a VPS dá **checkout da tag** (deploy reproduzível
  amarrado a uma versão nomeada, consistente com v2.2/v1.7). A imagem Docker segue `money:latest`.

### Rebuild + redeploy (canônico, herdado do v2.0 — locked)
- **D-05:** `docker build -t money:latest .` a partir de `/root/money` → `docker service update --force
  --image money:latest lazari_money` no stack unificado `lazari`. **NUNCA `--remove-orphans`** (n8n/crm
  são orphans intencionais). O `money` roda **sem bloco `ports:`** (anti-spoof; único ingresso é o
  Traefik + gate forwardAuth).

### Rollback safety
- **D-06:** Antes do rebuild, **taguear a imagem atual** que roda em prod como `money:pre-v2.3`
  (`docker tag`). Se o novo container quebrar (import error, dep faltando, etc.), rollback em 1 comando:
  `docker service update --rollback lazari_money` (ou `--image money:pre-v2.3`). Salto multi-versão em
  réplica única exige rede de segurança barata e instantânea.

### Smoke pós-deploy (3 camadas — defesa em profundidade)
- **D-07:** **Navegador logado** — o operador loga em `app.lazaricapital.com.br` com **sua conta
  pessoal ativa**; Claude conduz a análise do ITUB4 via Claude-in-Chrome e confere visualmente
  arquétipo→RIM + intrínseco calibrado + veredito "ver motor primário". É o critério "smoke visual"
  do roadmap. (Sem criar usuário de teste em prod.)
- **D-08:** **`docker exec` CLI** — rodar a CLI dentro do container `money`
  (`docker exec <cid> python cli.py analisar ITUB4`, PYTHONPATH=/app/src) para confirmar que o código
  **servido** é v2.3, independente do gate/render da UI.
- **D-09:** **Healthcheck + infra** — confirmar o service `1/1` healthy, gate forwardAuth (2xx libera +
  promove `X-User-Email`) e websocket `101` atrás do gate — que o redeploy não quebrou a infra.

### Gate pré-deploy
- **D-10:** Rodar a **suíte completa verde** (447 testes) + firewall selo↛report intacto **antes** do
  deploy (critério de aceite OPS-01). Nenhum push/deploy com suíte vermelha.

### Claude's Discretion
- Ordem exata dos comandos, verificação de DNS/TLS já ativos (herdados do v2.0), e a mecânica de achar
  o container id / nome do service (`lazari_money`) ficam a critério do executor, seguindo o runbook v2.0.
- Warmup de cache/dados pós-restart (cold start do ITUB4 batendo CVM/Yahoo ao vivo) não foi levantado
  como preocupação; tratar como best-effort se surgir latência no smoke.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Runbook de deploy (v2.0 — fonte do procedimento canônico)
- `.planning/milestones/v2.0-phases/03-go-live-e2e-pago/.continue-here.md` — runbook vivo: SSH,
  redeploy após mudança de código, `docker service update --force`, **nunca `--remove-orphans`**,
  source `money:latest` = `/root/money`, chave SSH `id_ed25519_vps`.
- `.planning/milestones/v2.0-phases/03-go-live-e2e-pago/03-04-SUMMARY.md` — build+deploy do
  `money:latest` na VPS, cutover, 7 fixes de deploy, smoke do gate interno.
- `.planning/milestones/v2.0-phases/03-go-live-e2e-pago/03-03-SUMMARY.md` — decisão do **deploy
  canônico = stack unificado `lazari`** (money mora em `~/projects/lazari-capital/docker-stack.yml`);
  o `stack.yml` do engine é fallback anotado.
- `.planning/milestones/v2.0-phases/03-go-live-e2e-pago/03-RESEARCH.md` §~104,159,328 — `docker build
  -t money:latest .`, `.streamlit/config.toml`, pegadinhas do rebuild.

### Deploy artifacts (repo atual)
- `Dockerfile` — imagem `money` (python:3.13-slim, PYTHONPATH=/app/src, streamlit run app.py :8501).
- `stack.yml` — **FALLBACK anotado** (não é o canônico); documenta labels Traefik + gate forwardAuth
  (`lazari_web:8000/gate/`, `authResponseHeaders=X-User-Email`), `money` sem `ports:`. O canônico é
  `~/projects/lazari-capital/docker-stack.yml` (serviço `money` no stack `lazari`), fora deste repo.

### Requisito + aceite
- `.planning/REQUIREMENTS.md` §OPS-01 (linhas ~45-50) — critério de aceite verbatim do redeploy.
- `.planning/ROADMAP.md` §"Phase 6" — Success Criteria (código v2.3 no ar, ITUB4 correto ao vivo,
  suíte verde + firewall antes do deploy).

### Comportamento-alvo (o que provar ao vivo)
- Memória do projeto: `v2-2-shipped-not-deployed.md` — sintoma antigo (PDF do ITUB4 "Evitar" DDM
  R$12,93-19,32) + auth do push (`gh auth switch -u voictrafego`, remote `voictrafego/money`).

**Infra fora do repo (não versionada aqui, mas canônica para o deploy):**
- `~/projects/lazari-capital/docker-stack.yml` — stack unificado `lazari` (web+worker+db+**money**);
  onde o serviço `money` vive de fato. Deploy via `docker stack deploy -c docker-stack.yml lazari` ou
  `docker service update`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`Dockerfile`** (raiz): já builda `money:latest` sem mudança — `COPY . .` empacota código+data.
- **`cli.py`**: espelha a engine da UI — usar `python cli.py analisar ITUB4` dentro do container
  (D-08) prova o comportamento v2.3 sem depender do render Streamlit nem do gate.
- **Runbook v2.0**: o procedimento de redeploy já foi exercitado com sucesso no go-live; este phase
  o repete com a fonte atualizada para v2.3.

### Established Patterns
- Deploy canônico = **stack Swarm unificado `lazari`**, não o `stack.yml` local (fallback). O `money`
  compartilha a overlay `network_swarm_public` com `lazari_web` e alcança o gate pelo FQDN do serviço.
- **`--remove-orphans` é proibido** (n8n/crm dormentes são orphans intencionais).
- Escrita em prod = operador aprova/roda no v2.0; aqui o operador optou por Claude dirigir via SSH (D-01).

### Integration Points
- Gate Traefik forwardAuth (`lazari_web:8000/gate/`) fica **na frente** do `money` — validação ao vivo
  exige sessão logada (D-07, conta pessoal do operador).
- Git: remote `voictrafego/money` (github), auth via conta gh `voictrafego` (D-03).

</code_context>

<specifics>
## Specific Ideas

- O número-âncora do smoke: **ITUB4 ~R$32-40** (RIM calibrado), veredito "ver motor primário" — o
  oposto do sintoma antigo capturado no PDF ("Evitar", DDM R$12,93-19,32). A cesta 4/4 da Fase 4
  (ITUB4 32,88 · BBAS3 43,89 · BBDC4 13,37 · BBSE3 39,87) é o comportamento que deve chegar em prod.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (Warmup de cache pós-restart foi notado como best-effort,
não como escopo; ver Claude's Discretion.)

</deferred>

---

*Phase: 6-Redeploy do app v2.3 na VPS*
*Context gathered: 2026-07-13*
