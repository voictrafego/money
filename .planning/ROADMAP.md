# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 (shipped 2026-06-28)
- ✅ **v1.4–v1.7 — Swing Trade / Modo Trading / Home / Lentes-Selo-Comparador** — Phases 12–21 (shipped 2026-07-04, tag `v1.7`)
- ✅ **v2.0 — Comercialização (Lazari Capital)** — Phases 1–3 (shipped 2026-07-10, produto no ar, E2E pago concluído)
- 🚧 **v2.2 — Motor de Valuation por Arquétipo** — Phases 1–3 (planejada, numeração reiniciada)

> **Marco major novo (v2.2):** a numeração de fases foi **reiniciada em Phase 1** (padrão deste
> repo — o v2.0 também reiniciou). As fases do v2.0 foram arquivadas em
> `.planning/milestones/v2.0-phases/`; `.planning/phases/` está vazio para o v2.2. Requisitos
> ativos do v2.2 em `.planning/REQUIREMENTS.md`; brief-fonte em `.planning/BRIEF-motor-arquetipo.md`.

## Overview

O erro é de **arquitetura, não de fórmula**: a ferramenta aplica um único motor primário
(DDM de estágio único) para toda ação e agrega o veredito por ele, carimbando compounders de
qualidade (banco ITUB4) como "evitar". O conserto tem três movimentos. **Fase 1** ergue o coração
do milestone — um **classificador de arquétipo** que decide o tipo de negócio (banco, pagadora
regulada, cíclica, crescimento, holding) *antes* de valuar, com **fallback honesto** em
casos-fronteira, e um **registry arquétipo→motor** que passa a escolher o motor (com o DDM já
plugado para a pagadora regulada, sem quebrar o que funciona). **Fase 2** implementa os motores
que faltam e os pluga no registry — **RIM** (destrava o ITUB4), **lucro normalizado** (cíclicas),
**DCF multi-estágio** (crescimento) e **NAV/SOTP** (holdings) — cada arquétipo passando a calcular
o intrínseco pelo modelo certo. **Fase 3** refatora a agregação do veredito para consumir o motor
**do arquétipo** (não o DDM fixo), roda um contraponto e **levanta bandeira de divergência**,
adiciona **guarda-corpos anti-aberração** antes de estampar "evitar", e em caso-fronteira **assume
a dúvida em voz alta** (range + bandeira) em vez de cravar um selo falso. Meta: acertar os ~85% de
casos claros e assumir honestamente a dúvida nos ~15% fronteiriços.

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

<details>
<summary>✅ v2.0 — Comercialização (Lazari Capital) (Phases 1–3, numeração reiniciada) — SHIPPED 2026-07-10</summary>

Camada Django (repo `lazari-capital`) espelhando o `crm-voic`: cadastro self-serve + trial 7d +
gate Traefik forward-auth (Fase 1), cobrança recorrente Asaas + webhooks nativos idempotentes +
página de conta (Fase 2), go-live integrado na VPS sob domínio Lazari Capital + E2E pago (smoke real
R$19,90 PIX confirmado ao vivo) + NFS-e automática (Fase 3). Único item aberto (não-técnico):
operador decidir estorno do smoke. Fases arquivadas em `.planning/milestones/v2.0-phases/`;
snapshot do roadmap em `.planning/milestones/v2.0-ROADMAP.md`.

</details>

### 🚧 v2.2 — Motor de Valuation por Arquétipo

**Milestone Goal:** Corrigir o erro de **arquitetura** em que a ferramenta aplica um único motor
primário (DDM de estágio único) para todas as ações. Rotear cada tipo de negócio para o motor
certo **antes** de valuar (classificador + registry), implementar os motores que faltam (RIM/lucro
normalizado/DCF/SOTP), e nunca deixar o veredito final ser puxado por um modelo que não serve
àquele perfil (ensemble + divergência + guarda-corpos + selo que consome o arquétipo).

- [ ] **Phase 1: Classificador de Arquétipo + Roteamento** - Classifica o negócio antes de valuar (setor CVM + refino quantitativo), com fallback honesto, e roteia via registry arquétipo→motor (DDM já plugado para pagadora regulada)
- [ ] **Phase 2: Motores por Arquétipo** - Implementa e pluga no registry os motores primários que faltam: RIM (banco), lucro normalizado (cíclica), DCF multi-estágio (crescimento), NAV/SOTP (holding)
- [ ] **Phase 3: Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo** - Selo consome o motor do arquétipo (não o DDM fixo), roda contraponto + bandeira de divergência, guarda-corpos anti-aberração, e assume a dúvida em caso-fronteira

## Phase Details

### Phase 1: Classificador de Arquétipo + Roteamento
**Goal**: Erguer o coração do milestone — a etapa de **classificação/roteamento que hoje não
existe**. A ferramenta decide o arquétipo do negócio (financeira, pagadora regulada, compounder,
cíclica, holding) **antes de valuar**, a partir dos dados já puxados (setor CVM como filtro grosso +
refino quantitativo por ROE/retenção/oscilação de margem). Quando a confiança é baixa
(caso-fronteira, híbrido, mudança de estágio), **não chuta**: marca como fronteiriço e guarda 2–3
lentes candidatas. A escolha do motor deixa de ser fixa (DDM hard-coded) e passa por um **registry
arquétipo→motor**, com o DDM já plugado como primário da pagadora regulada — o roteamento entra no
funil de `report.py` entre o CAPM (`:113`) e a montagem do DDM (`:136`), sem tocar nos motores.
**Depends on**: Nothing (primeira fase do marco; engine de valuation já existe)
**Requirements**: ARQ-01, ARQ-02, ENG-01, ENG-06
**Success Criteria** (what must be TRUE):
  1. Rodar a engine (CLI/UI) em ITUB4, TAEE11, VALE3 e WEGE3 classifica e exibe o arquétipo do negócio (banco, pagadora regulada, cíclica, crescimento) **antes** do bloco de valuation.
  2. A escolha do motor vem do **registry arquétipo→motor** (não mais de DDM fixo no código); um arquétipo cujo motor primário ainda não existe cai num fallback explícito, não em crash.
  3. TAEE11 (pagadora regulada) é roteada para **DDM como primário** e seus números/veredito permanecem idênticos aos de hoje — `test_ddm`, `test_selo`, `test_consistencia_modos` continuam verdes.
  4. Um ticker de confiança baixa (híbrido/fronteiriço) é marcado como **fronteiriço** e o classificador expõe 2–3 arquétipos candidatos em vez de cravar um único.
**Plans**: 8 plans (2 execução + 6 gap-closure)
- [x] 01-01-PLAN.md — Classificador puro (core/arquetipo.py) + registry ARQUETIPO_MOTOR + bloco config arquetipo: + golden (Wave 1)
- [x] 01-02-PLAN.md — Roteamento no funil report.py + suspensão D-04 (reuso "VERIFICAR") + render mínimo + golden e2e (Wave 2)
- [x] 01-03-PLAN.md — [gap] Detrend do sinal de ciclicidade (_cv_lucro) + golden WEGE3 realista — fecha Gap 1 CR-01/SC#1 (Wave 1)
- [x] 01-04-PLAN.md — [gap] Expõe Arquétipo → motor na UI Streamlit (app.py), inclusive não-suspenso — fecha Gap 2/SC#1 (Wave 1)
- [ ] 01-05-PLAN.md — [gap Achado 1a] Sinal de ciclicidade = resíduos log-lineares + recalibra ciclica_cv_min + goldens REAIS (WEGE3/RADL3→crescimento; VALE3/GGBR4/SUZB3/PETR4→ciclica) — reabre ARQ-01/ARQ-02 (Wave 1)
- [ ] 01-06-PLAN.md — [gap Achado 1b] Corrige over-match do hard-route financeiro (MDIA3/alimentos ≠ financeira) (Wave 2, depende de 01-05)
- [ ] 01-07-PLAN.md — [gap Achado 2 · SAN-01 puxado da Fase 3] Guarda-corpos DDM: não emitir/exibir faixa degenerada (vmax≤0/0-0: HAPV3/PCAR3/PRIO3) (Wave 1)
- [ ] 01-08-PLAN.md — [gap Achado 3+4 · SAN-01/ENS-01 puxados da Fase 3] Freio do modo Ranking (R²≈0/ROMI3 + suspensão por arquétipo) + sinalização de divergência entre lentes (reconciliação DEFERIDA à Fase 3) (Wave 1)

### Phase 2: Motores por Arquétipo
**Goal**: Plugar no registry os motores primários que faltam — as fórmulas de livro-texto (~20% do
esforço) que, roteadas pelo classificador da Fase 1, fazem cada arquétipo calcular o intrínseco pelo
modelo certo. **RIM** (VPA + VP do excesso de ROE sobre Ke) para banco/seguradora — é o motor que
destrava o ITUB4; **lucro normalizado** (média 7–10a/mid-cycle, reaproveitando `normalizacao.py`)
para cíclicas; **DCF de FCF multi-estágio** (ou múltiplo relativo) para crescimento/capital-light;
**NAV/SOTP** para holding/imobiliária patrimonial. O DDM puro (`core/ddm.py`) não é tocado — os
motores novos entram como pares no registry, e o DDM rebaixa a "lente conservadora" onde não é o
primário do arquétipo.
**Depends on**: Phase 1
**Requirements**: ENG-02, ENG-03, ENG-04, ENG-05
**Success Criteria** (what must be TRUE):
  1. ITUB4, roteado para **RIM**, produz um valor intrínseco coerente com Graham/mercado (~R$40), não o ~R$16 do DDM comprimido pelo Ke alto; o DDM aparece rebaixado a "lente conservadora".
  2. VALE3 (cíclica) valua sobre **lucro normalizado** (média 7–10a/mid-cycle), não sobre o lucro de um ano só.
  3. WEGE3 (crescimento) usa **DCF multi-estágio** (ou múltiplo relativo) e não recebe mais DDM cuspindo zero/lixo.
  4. Um arquétipo holding/imobiliária patrimonial usa **NAV/SOTP** como motor primário.
  5. O golden `test_ddm` (DDM Itaú ≈ R$37,22, input fixo de livro) continua verde — os motores novos não alteram o DDM puro.
**Plans**: TBD

### Phase 3: Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo
**Goal**: Fechar o loop na **agregação do veredito**, que hoje é single-model (BSD × DDM). Refatorar
`selo.py`/`report.py` para o selo consumir o motor **do arquétipo** classificado (não o DDM fixo),
preservando o firewall testado (selo não importa report — só recebe primitivos). Rodar o motor
primário + ≥1 contraponto e, quando a divergência passar do limiar (maior > 2× menor), **levantar
bandeira de divergência** com hipótese exibida ("compounder subvalorizado pelo DDM", "cíclica no
topo do ciclo") em vez de cravar número único. Interpor **guarda-corpos anti-aberração** antes de
estampar "evitar" (regra do SAN-01). E, em caso-fronteira, **assumir a dúvida em voz alta**
(range + bandeira) em vez de fingir certeza. Se prefixos/rótulos de veredito mudarem, atualizar
`faixa_do_veredito` (`selo.py:88`) e `report._veredito_token` (`report.py:355`) juntos.
**Depends on**: Phase 2
**Requirements**: ENS-01, SAN-01, VER-01, VER-02
**Success Criteria** (what must be TRUE):
  1. **ITUB4 não é mais estampado "evitar"**: o selo final consome o motor do arquétipo (RIM), com o DDM rebaixado a "lente conservadora" — não mais SOBREAVALIADA/Qualidade Baixa/Evitar via DDM sozinho.
  2. Quando motor primário e contraponto divergem além do limiar (maior > 2× menor), a ferramenta exibe **range + bandeira de divergência** com hipótese, em vez de um número único cravado.
  3. Todo veredito "evitar" passa pelos **guarda-corpos** antes de exibir: uma aberração (intrínseco < 0,5× mediana dos pares **E** ROE > 15% **E** corte de payout > 40%) é reetiquetada "DDM conservador demais para o perfil — ver motor primário do arquétipo", não "qualidade baixa/evitar".
  4. Em caso-fronteira, o veredito **assume a dúvida** (range + bandeira de divergência) em vez de estampar um selo falso.
  5. O firewall **selo↛report** é preservado e `test_selo`, `test_vulc3_regressao`, `test_guardrails_fix06` e `test_consistencia_modos` continuam verdes (prefixos/rótulos rebaseline apenas se mudados deliberadamente).
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Fases executam em ordem numérica: 1 → 2 → 3

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Classificador de Arquétipo + Roteamento | v2.2 | 4/8 | Gap closure | - |
| 2. Motores por Arquétipo | v2.2 | 0/TBD | Not started | - |
| 3. Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo | v2.2 | 0/TBD | Not started | - |
