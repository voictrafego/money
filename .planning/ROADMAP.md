# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 (shipped 2026-06-28)
- ✅ **v1.4–v1.7 — Swing Trade / Modo Trading / Home / Lentes-Selo-Comparador** — Phases 12–21 (shipped 2026-07-04, tag `v1.7`)
- ✅ **v2.0 — Comercialização (Lazari Capital)** — Phases 1–3 (shipped 2026-07-10, produto no ar, E2E pago concluído)
- ✅ **v2.2 — Motor de Valuation por Arquétipo** — Phases 1–3 (shipped 2026-07-12, tag `v2.2`, auditoria de milestone passed)
- 🚧 **v2.3 — Calibração do Valuation à Realidade (RIM com Valor Terminal / BACKTEST-01)** — Phases 4–6 (ativo)

> Marcos concluídos são arquivados em `.planning/milestones/` (roadmap + requisitos + fases por
> marco). Histórico narrado em `.planning/MILESTONES.md`. Marcos major reiniciam a numeração em
> Phase 1; marcos minor (como o v2.3) continuam a numeração do marco anterior.

---

## v2.2 — Motor de Valuation por Arquétipo (SHIPPED 2026-07-12)

Corrigiu o erro de **arquitetura** (não de fórmula) em que a ferramenta aplicava um único motor
(DDM de estágio único) para toda ação, carimbando compounders de qualidade (banco ITUB4) como
"evitar". Três movimentos: **classificador de arquétipo + roteamento** (Fase 1), **motores por
arquétipo** RIM/normalizado/DCF/NAV (Fase 2) e **veredito honesto** — selo consome o motor do
arquétipo, ensemble com bandeira de divergência, guarda-corpos anti-aberração SAN-01 e dúvida
honesta no caso-fronteira (Fase 3). 12/12 requisitos verificados; suíte 437 verde; firewall
selo↛report intacto.

**Detalhes completos arquivados:** `.planning/milestones/v2.2-ROADMAP.md` ·
`.planning/milestones/v2.2-REQUIREMENTS.md` · `.planning/milestones/v2.2-phases/`
**Auditoria:** `.planning/v2.2-MILESTONE-AUDIT.md` (passed; blocker da aba Ranking do Streamlit
fechado por quick task 260712-p6r antes do arquivamento).

---

## 🚧 v2.3 — Calibração do Valuation à Realidade (RIM com Valor Terminal / BACKTEST-01)

**Milestone Goal:** Corrigir a subestimação sistemática do motor RIM (bancos) dando-lhe um **valor
terminal**, para que bancos de qualidade valuem coerente com âncoras de realidade — ITUB4 na ordem
de **~R$32-40, não R$23** — validado numa cesta de bancos, e então redeployado. É o BACKTEST-01 que
a Fase 2 do v2.2 deixou explicitamente adiado.

**Diagnóstico (2026-07-12):** o RIM ao vivo dá ITUB4 = R$23,01 vs alvo ~R$40 do SC#1 do v2.2. Causa
raiz **não é o Ke** (varrer 10,5%→17,3% move só ~R$3); é a estrutura **fade-sem-valor-terminal (D-02)**
que ancora o RIM no VPA (~R$19). Um residual income COM perpetuidade / P/B justo leva o ITUB4 a
~R$32-38. Escopo cirúrgico: **só RIM/bancos** — DCF/normalizado/DDM não são tocados. Ver
`.planning/v2.2-MILESTONE-AUDIT.md` e a memória do projeto.

## Overview

Três movimentos. **Fase 4** dá ao RIM um valor terminal (perpetuidade de residual income / P/B
justo), parametrizado em config, e revisa o Ke de banco como ajuste fino — o número do ITUB4 sai do
VPA e passa a bater com Graham/mercado. **Fase 5** constrói o harness de validação (BACKTEST-01) que
prova a calibração numa cesta de bancos (ITUB4/BBAS3/BBSE3/BBDC4), triangulando 4 âncoras de
realidade. **Fase 6** redeploya o app na VPS — o v2.2 nunca subiu, então produção ainda mostra o
comportamento antigo ("Evitar"/DDM).

## Phases

- [ ] **Phase 4: RIM com Valor Terminal + Ke revisado** - o RIM ganha uma perpetuidade de residual income (fim do fade-sem-terminal); ITUB4 sai de R$23 para ~R$32-40; Ke de banco revisado como ajuste secundário
- [ ] **Phase 5: BACKTEST-01 — Validação na cesta de bancos** - harness reproduzível que roda o RIM calibrado em ITUB4/BBAS3/BBSE3/BBDC4 e triangula 4 âncoras (Graham+Bazin, preço, fair values manuais, múltiplos de pares); calibração generaliza, não só ITUB4
- [ ] **Phase 6: Redeploy do app v2.3 na VPS** - subir o código v2.3 para produção; ITUB4 no app ao vivo mostra arquétipo→RIM calibrado, não mais "Evitar"/DDM R$12,93-19,32

## Phase Details

### Phase 4: RIM com Valor Terminal + Ke revisado
**Goal**: Consertar a alavanca principal — dar ao motor RIM um **valor terminal** (perpetuidade de
residual income, ou P/B justo `(ROE−g)/(Ke−g)` equivalente) que substitui/complementa o
fade-para-zero-sem-terminal (D-02), para que o intrínseco de um banco que sustenta ROE > Ke deixe de
ancorar no VPA. Revisar o Ke do RIM de banco (teto/`erp_banco`) como ajuste fino aplicado por cima.
A formulação tem fundamento teórico, é parametrizada em `config.yaml`, e o motor continua
puro/never-raise sem tocar `ddm.py`/`selo.py`/`lentes.py`.
**Depends on**: Nothing (primeira fase do marco; o motor RIM já existe do v2.2)
**Requirements**: CAL-01, CAL-02
**Success Criteria** (what must be TRUE):
  1. **ITUB4 (roteado para RIM) produz intrínseco na faixa ~R$32–40** — mesma ordem de grandeza de Graham (R$39,88) e do preço (R$44,30), NÃO os ~R$23 atuais. *(Alvo quantitativo cravado — a verificação DEVE cobrar o número, não só "não é Evitar".)*
  2. O valor terminal do RIM é **parametrizado em `config.yaml`** (perpetuidade/P/B justo com knobs), sem constantes mágicas hard-coded no código, e tem justificativa teórica documentada.
  3. O Ke do RIM de banco foi revisado (teto/erp_banco) e documentado; não produz intrínseco explosivo (clamps sãos preservados).
  4. **Não quebrou nada**: golden `test_ddm` (DDM puro) verde, pagadora regulada (TAEE11) idêntica ao v2.2, firewall selo↛report intacto, suíte completa verde.

### Phase 5: BACKTEST-01 — Validação na cesta de bancos
**Goal**: Provar que a calibração da Fase 4 **generaliza** — não é overfit no ITUB4. Construir um
harness reproduzível (script + teste) que roda o RIM calibrado numa cesta de bancos
(ITUB4, BBAS3, BBSE3, BBDC4) e reporta cada intrínseco contra **4 âncoras de realidade**:
(a) Graham + Bazin; (b) preço de mercado; (c) tabela manual de fair values (valores-alvo por ticker
— coletados do usuário ou de consenso de casas de análise nesta fase); (d) múltiplos de pares
(P/VP, P/L do setor bancário). Desvios remanescentes são explicados, não escondidos.
**Depends on**: Phase 4
**Requirements**: VAL-01, VAL-02
**Success Criteria** (what must be TRUE):
  1. Existe um harness reproduzível (script + teste) que roda a cesta de bancos e imprime, por ticker, o intrínseco do RIM lado a lado com as 4 âncoras.
  2. Para a cesta, o intrínseco do RIM **não fica cronicamente ~40-50% abaixo das âncoras** (o sintoma "descolado da verdade") — a maioria cai na banda razoável de fair value, e cada exceção tem explicação.
  3. A tabela manual de fair values existe (valores por ticker definidos com o usuário) e está versionada como âncora do backtest.
  4. Se a validação revelar que a calibração da Fase 4 falha para algum banco, o achado é registrado e a Fase 4 é ajustada (loop), não ignorado.

### Phase 6: Redeploy do app v2.3 na VPS
**Goal**: Fechar o loop até produção. O v2.2 (e agora v2.3) nunca subiu — o app deployado na VPS
(Lazari Capital) ainda roda comportamento pré-arquétipo. Redeployar o código v2.3 com a suíte verde.
**Depends on**: Phase 4, Phase 5
**Requirements**: OPS-01
**Success Criteria** (what must be TRUE):
  1. O app na VPS roda o código v2.3 (redeploy concluído, healthcheck ok, gate/WS intactos).
  2. **ITUB4 no app ao vivo** mostra arquétipo (financeira→RIM), o intrínseco calibrado do RIM (~R$32-40) e o veredito "ver motor primário" — **não** mais "Evitar" com faixa DDM R$12,93–19,32.
  3. Suíte verde e firewall intacto antes do deploy; smoke visual pós-deploy aprovado.

## Progress

**Execution Order:**
Fases executam em ordem numérica: 4 → 5 → 6

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 4. RIM com Valor Terminal + Ke revisado | v2.3 | 0/? | Planned | - |
| 5. BACKTEST-01 — Validação na cesta de bancos | v2.3 | 0/? | Planned | - |
| 6. Redeploy do app v2.3 na VPS | v2.3 | 0/? | Planned | - |
