---
gsd_state_version: 1.0
milestone: v2.3
milestone_name: Calibração do Valuation à Realidade (RIM com Valor Terminal)
status: executing
stopped_at: Completed 05-04-PLAN.md (loop D-12 aberto)
last_updated: "2026-07-13T12:36:05.089Z"
last_activity: 2026-07-13 -- Phase 04 planning complete
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 7
  completed_plans: 5
  percent: 71
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-11)

**Core value:** Cada tipo de negócio é roteado para o motor de valuation certo antes de valuar,
e nenhum veredito final é puxado por um modelo que não serve àquele perfil — um compounder de
qualidade (banco) nunca mais é carimbado "evitar" porque o DDM de estágio único não cabe nele.
**Current focus:** Phase 04 — RIM recalibração (iteração 2 / loop D-12) — CONTEXT capturado, pronto p/ planejar

## Current Position

Phase: 4 (reaberta pelo loop D-12; Fase 6 bloqueada até fechar)
Plan: Not started (recalibração — iteração 2)
Status: Ready to execute
Last activity: 2026-07-13 -- Phase 04 planning complete

## Deferred Items

Itens reconhecidos e adiados no fechamento do marco v2.2 (2026-07-12):

| Category | Item | Status |
|----------|------|--------|
| quick_task | 260620-oa9-ajustar-tela-2-ranking-por-multiplos-com | missing (era v1.x) |
| quick_task | 260622-cg9-robustez-da-resolucao-de-tickers-retry-y | missing (era v1.x) |
| quick_task | 260629-ig6-aba-swing-trade-mvp-candlestick-intraday | missing (era v1.x) |
| quick_task | 260630-g0b-adicionar-auto-refresh-opcional-ao-4-men | missing (era v1.x) |

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed (v1.0–v2.0): marcos arquivados (v1.7 = 66+ plans/21 fases; v2.0 = 3 fases)
- v2.2: 0 plans completed

**By Phase (v2.2):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Classificador + Roteamento | TBD | - | - |
| 2. Motores por Arquétipo | TBD | - | - |
| 3. Veredito Honesto | TBD | - | - |
| 01 | 8 | - | - |
| 02 | 2 | - | - |
| 03 | 4 | - | - |
| 04 | 1 | - | - |
| 05 | 4 | - | - |

**Recent Trend:**

- Último marco enviado: v2.0 Comercialização/Lazari Capital (2026-07-10, produto no ar, E2E pago concluído)
- Trend: —

*Updated after each plan completion*
| Phase 01 P01 | 0h30m | 2 tasks | 3 files |
| Phase 01 P02 | 0h35m | 3 tasks | 5 files |
| Phase 01 P03 | 0h20m | 2 tasks | 3 files |
| Phase 01 P04 | 0h08m | 1 tasks | 1 files |
| Phase 01 P05 | 0h25m | 2 tasks | 3 files |
| Phase 01 P07 | 0h20m | 2 tasks | 3 files |
| Phase 01 P08 | 0h22m | 2 tasks | 3 files |
| Phase 01 P06 | 0h20m | 1 tasks | 4 files |
| Phase 02 P01 | 18min | 3 tasks | 3 files |
| Phase 02 P02 | 16min | 3 tasks | 5 files |
| Phase 03 P02 | 25min | 2 tasks | 3 files |
| Phase 03 P03 | 0h20m | 2 tasks | 2 files |
| Phase 03 P04 | 0h20m | 2 tasks | 2 files |
| Phase 04 P01 | 0h04m | 3 tasks | 5 files |
| Phase 05 P02 | 12min | 3 tasks | 1 files |
| Phase 05 P03 | 0h18m | 2 tasks | 2 files |
| Phase 05 P04 | 0h14m | 2 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions são registradas na tabela Key Decisions do PROJECT.md. Governando o v2.2:

- **O problema do ITUB4 é erro de arquitetura, não de fórmula.** DDM/Graham/Bazin estão matematicamente corretos; o defeito é aplicar DDM de estágio único como motor primário para TODO negócio e agregar o veredito por ele. Conserto = roteamento por arquétipo.
- **Gargalo = classificador (~60% do esforço), não os motores (~20%, fórmulas de livro-texto).** Priorizar a árvore de decisão do classificador (Fase 1) primeiro, depois plugar os motores nela (Fase 2).
- **Fallback honesto:** quando a confiança do classificador for baixa (caso-fronteira/híbrido), NÃO chutar — marcar como fronteiriço e rodar 2–3 lentes candidatas com bandeira de divergência.
- **RIM é o motor que destrava o ITUB4** (banco/seguradora): VPA + VP do excesso de ROE sobre Ke. DDM permanece como primário só para pagadora madura/regulada (TAEE11/SAPR11/EGIE3) — não quebrar o que funciona.
- **Nota técnica (repo):** golden `tests/test_ddm.py` trava DDM Itaú ≈ R$ 37,22 com Ke fixo de livro (12,48%). A run ao vivo injeta Rf via Selic → Ke ~17,3% → comprime para ~R$ 16. A refatoração NÃO deve quebrar o golden (input fixo), mas confirma a hipersensibilidade do DDM ao vivo ao Ke.
- [Phase ?]: Classificador de arquétipo = função pura config-driven em core/arquetipo.py (espelha lifecycle.py); consome sinais canônicos de CompanyData sem recalcular método
- [Phase ?]: candidatos sempre populado no ResultadoArquetipo; o flag fronteirico é o que distingue conflito real de rota crava
- [Phase 01]: Roteamento por arquétipo plugado no funil analisar_acao é aditivo/read-only — DDM roda sempre como lente; a suspensão D-04 só troca o texto do veredito primário
- [Phase 01]: Suspensão D-04 é genérica por motor_pendente e reusa o prefixo VERIFICAR — preserva o firewall selo↛report sem tocar selo.py/ddm.py
- [Phase 01]: Sinal de ciclicidade = CV dos retornos ano-a-ano (detrended), não do nível bruto — fecha CR-01/Gap 1 (WEGE3 deixa de misroutar para cíclica)
- [Phase ?]: [Phase 01]: UI Streamlit (app.py) expõe 'Arquétipo → motor' no caption principal, incondicional em motor_pendente — fecha Gap 2 (paridade CLI/UI, inclui pagadora_regulada/TAEE11)
- [Phase ?]: [Phase 01]: Sinal de ciclicidade = dispersão dos resíduos de ajuste log-linear do lucro (substitui CV dos retornos ano-a-ano); prejuízo na janela = evidência cíclica forte que precede o guard de <3 pontos; ciclica_cv_min recalibrado 0.50 para 0.35 com margem — fecha Achado 1a/CR-01 (WEGE3/RADL3 reais viram crescimento)
- [Phase 01]: Guarda-corpo do DDM (Achado 2/SAN-01): faixa negativa (vmax<=0) ou degenerada (0-0) suprimida na borda de emissão — vmin/vmax->None + ddm_inaplicavel + nota honesta; faixa que só cruza zero (vmax>0) preservada. core/ddm.py e selo.py intocados.
- [Phase ?]: [Phase 01]: Freio do modo Ranking (Achado 3): cmd_rank só estampa alvo de regressão quando reg não é frágil (r2_baixo/amostra_pequena), upside não é degenerado (>−0,90) e o arquétipo tem motor (não motor_pendente) — paridade com a suspensão D-04 do Analisar; a NOTA do ranque fica intacta.
- [Phase ?]: [Phase 01]: Divergência entre lentes (Achado 4) é SINALIZAÇÃO honesta (helper puro divergencia_entre_lentes + LIMIAR_DIVERGENCIA=2×), não reconciliação — o ensemble real (DDM × motor do arquétipo) depende da Fase 2 e é escopo da Fase 3.
- [Phase ?]: [Phase 01]: Achado 1b (MDIA3): misroute era de RESOLUÇÃO (empresa errada), não do classificador — o estágio 'contém' de universe._resolver_base casou o fragmento CVM 'rci' (de 'Banco RCI Brasil') dentro de 'comeRCIo' no nome do MDIA3, trazendo setor 'Bancos'. Fix: override determinístico no ticker_map (MDIA3->{20338,'Alimentos'}) + hard-route financeiro por limite de palavra (defesa T-0106-01). ITUB4/BBAS3 seguem financeira.
- [Phase ?]: [Phase 02]: RIM honesto ~R$28 (faixa R$26-34, sem premio terminal D-02) vence o alvo aproximado ~R$40 de D-01 — materialmente > DDM ao vivo ~R$16, destrava o ITUB4
- [Phase ?]: [Phase 02]: ke_rim = rf-ciclo + beta×erp_banco (0.045 sem premio small-cap), clamp [0.11,0.14] e nunca > ke_live (D-01); motores puros config-driven compoem primitivas testadas sem tocar ddm/lentes/capm/normalizacao
- [Phase 02]: Suspensão do veredito migrada de motor_pendente → motor != 'ddm' nas 3 superfícies (report/cli/goldens) no mesmo wave do plug do registry — o motor do arquétipo já existe mas o selo só o consome na Fase 3 (VER-01); sem a migração o ITUB4 regride de VERIFICAR para 'evitar'
- [Phase 02]: Registry ARQUETIPO_MOTOR 5/5 plugado + dispatch dos 4 motores no funil analisar_acao consumindo insumos canônicos; motor CALCULA e EXIBE intrínseco (D-06), DDM rebaixado a lente conservadora onde motor != ddm
- [Phase ?]: [Phase 03]: SAN-01 = guarda-corpo anti-aberração na borda do veredito (_guarda_san01 à la _guarda_faixa_ddm); gatilho SOBREAVALIADA + ROE>15% E corte payout>40% reetiqueta 'DDM conservador demais para este perfil' mantendo o número; prefixo não-casado suprime a faixa do selo sem tocar selo.py
- [Phase ?]: [Phase 03]: funil single-stock usa valor_pares=None (D-04) — condição de pares neutra, gate cai para 2 condições, sem rede (custo-zero); aberração-âncora ITUB4 capturada pelas 2
- [Phase ?]: [Phase 03]: VER-02 = ramo fronteiriço na borda do veredito — roda o motor de cada arquétipo candidato (helper _intrinseco_por_motor extraído), monta range [menor..maior] + bandeira 'classificação incerta entre X e Y'; prefixo VERIFICAR suprime a faixa do selo sem tocar selo.py; degradação 1 candidato -> valor único, 0 -> VERIFICAR informativo
- [Phase ?]: [Phase 03]: UI Streamlit (app.py) renderiza read-only os sinais do veredito honesto (bandeira de divergência ENS-01, range fronteiriço VER-02, nota da reetiqueta SAN-01) no bloco veredito+selo do Analisar — paridade CLI↔UI, zero recálculo
- [Phase ?]: [Phase 03]: rótulo do intrínseco reflete a.motor_rotulo quando motor != ddm (T-0304-01) — a UI não chama mais RIM/DCF/NAV/normalizado de 'DDM'; 'Intrínseco (DDM)' só quando o DDM é o motor de fato (TAEE11)
- [Phase ?]: [Phase 04]: RIM ganha valor terminal (perpetuidade de Gordon via reuso de ddm.valor_gordon); ITUB4 R$23->R$32,9 (terminal ~17%), gate duro R$32-40 em teste unit+integracao
- [Phase ?]: [Phase 04]: ke_teto revisado 0.14->0.13 (CAL-02); Selic-ciclo ja embute risco-pais (erp_banco=0.045 sem double-count); ajuste fino secundario, alavanca principal e o valor terminal (CAL-01)
- [Phase ?]: [Phase 04]: guarda anti-bad-bank fade_para=ke+min(roe0-ke,cap) sem clampar a >=ke; banco ROE<Ke valua <book; knobs config-driven recalibraveis na Fase 5
- [Phase ?]: [Phase 05]: fair_values_bancos.yaml aprovado pelo usuario ANTES de versionar (D-01) — faixas de consenso de target prices (jul/2026), independentes de Graham/Bazin/RIM; ancora-verdade do gate vive em tests/fixtures/ nao em config.yaml (D-03)
- [Phase ?]: [Phase 05]: cruzando as faixas aprovadas com o RIM congelado, apenas ITUB4 cai na banda +-15% (1/4, abaixo do quorum 3/4) — sinal legitimo, nao bug; tratamento e do gate/loop D-12 no Plan 05-04, nao se afrouxam as faixas
- [Phase ?]: [Phase 05]: rodar_cesta pura em src/analista/backtest.py CONSOME report.analisar_acao (intrinseco_motor) — nunca reimplementa RIM; teste 05-04 e script compartilham a MESMA funcao e provam o mesmo numero
- [Phase ?]: [Phase 05]: harness roda 100% offline injetando rf_local congelado do snapshot em cfg[capm][rf_local]; medianas P/VP e P/L da propria cesta (D-11) como ancora setorial, zero fonte externa
- [Phase ?]: [Phase 05]: reproduz o snapshot exatamente (ITUB4 32.88 PASS in-band; BBAS3/BBDC4/BBSE3 FAIL) — desvios reportados no out/backtest_bancos.md nao mascarados (D-12); quorum/loop e do Plan 05-04
- [Phase 05]: backtest da cesta REPROVA o quórum (1/4 na banda ±15% < 3/4) — calibração RIM da Fase 4 nao generaliza; gate encoda a regra verbatim + xfail(strict), NAO afrouxa banda/quorum; achado registrado, loop D-12 reabre a Fase 04 (05-04)

### Estrutura do Roadmap v2.2 (criado 2026-07-11)

- **Fase 1 — Classificador de Arquétipo + Roteamento** (ARQ-01, ARQ-02, ENG-01, ENG-06): classifica antes de valuar + fallback honesto + registry arquétipo→motor com DDM plugado para pagadora regulada. Roteamento entra em `report.py` entre CAPM (:113) e DDM (:136).
- **Fase 2 — Motores por Arquétipo** (ENG-02 RIM, ENG-03 lucro normalizado, ENG-04 DCF, ENG-05 NAV/SOTP): pluga no registry os motores primários que faltam; DDM puro (`core/ddm.py`) não é tocado.
- **Fase 3 — Veredito Honesto** (ENS-01, SAN-01, VER-01, VER-02): selo consome o motor do arquétipo + ensemble/divergência + guarda-corpos + dúvida honesta em caso-fronteira. Preservar firewall selo↛report.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

- **Backlog v2.1 (polish de UX) — deferido.** Achados 6–18 do review de UX de 2026-07-10
  (`.planning/reviews/260710-ux-review-navegador.md`): notícias duplicadas, rótulo "carteira"
  engana, menu Streamlit exposto, responsivo não validado, etc. Top-5 já entregues como quick
  tasks (u1f/u2r/u3g/u4n/u5c). Não faz parte do v2.2 (engine).

### Blockers/Concerns

[Issues that affect future work]

- **🔴 LOOP D-12 ABERTO — recalibrar a Fase 4 antes de qualquer deploy (bloqueia a Fase 6).**
  O backtest da Fase 5 (BACKTEST-01) provou que a calibração RIM da Fase 4 **não generaliza**: sobre o
  snapshot congelado (`tests/fixtures/snapshot_bancos_2026-07-12.yaml`) cruzado com as faixas de consenso
  ao vivo aprovadas (`tests/fixtures/fair_values_bancos.yaml`), só **1/4 (ITUB4)** cai na banda ±15% —
  abaixo do quórum 3/4. Falha em **dois sentidos opostos** (não é viés uniforme):

  - **BBAS3 RIM 45,60 (+54,6%, acima de todo target ≤39)** → super-avalia. Hipótese: `num_acoes` dobrado / lucro por ação inflado.
  - **BBSE3 RIM 25,38 (−35,7%, abaixo do piso ≥33)** → sub-avalia a seguradora capital-light. Hipótese: RIM ancorado em book penaliza alto-ROE/baixo-capital.
  - **BBDC4 RIM 10,47 (−46,3%, abaixo do book)** → sub-avalia no vale de ROE. Hipótese: guarda anti-bad-bank apertando demais.
  O gate **não foi afrouxado**: a reprovação está travada como `xfail(strict=True, raises=AssertionError)`
  em `tests/test_backtest_bancos.py` — vira `XPASS→FAIL` automaticamente quando a Fase 4 recalibrar e o
  cesto cruzar 3/4, fechando o loop. Evidência completa: `05-04-SUMMARY.md` + `out/backtest_bancos.md`.
  **Fase 4 precisa reabrir; Fase 6 (redeploy) fica bloqueada até o cesto passar.**

- **Não quebrar os golden do valuation sem intenção:** `test_ddm.py` (DDM Itaú R$37,22 input fixo),
  `test_selo.py` (cortes de cor + rótulos da matriz + firewall selo↛report), `test_vulc3_regressao.py`
  (capstone e2e; veredito começa com "VERIFICAR"), `test_guardrails_fix06.py`, `test_consistencia_modos.py`
  (mesmo número entre Analisar/Garimpo/Ranking — Core Value). Se a refatoração mudar prefixos/rótulos
  de veredito, atualizar `faixa_do_veredito` (selo.py:88) e `report._veredito_token` (report.py:355) juntos.

- **Firewall selo↛report:** `selo.py` NÃO importa `report.py` (recebe só primitivos) — preservar ao
  refatorar a agregação do veredito (Fase 3).

- **Consistência cross-modo:** métodos canônicos `*_valuation()` em `fundamentals.py` são fonte única
  — mexer neles reverbera nos 3 modos (Analisar/Garimpo/Ranking).

- LOOP D-12 ABERTO (05-04): backtest da cesta reprovou (1/4 na banda ±15% < quórum 3/4). Calibração RIM da Fase 4 NÃO generaliza — BBAS3 super-avaliado +54.6%, BBSE3 −35.7%, BBDC4 −46.3%. Reabrir Fase 04 para recalibrar; Fase 06 (deploy) bloqueada até fechar. Gate xfail(strict) vira XPASS→FAIL ao recalibrar.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260710-u1f | Feedback de carregamento nas análises (spinner/status em Analisar/Garimpar/Ranking) | 2026-07-10 | 1e6524e | [260710-u1f-feedback-de-carregamento-nas-analises](./quick/260710-u1f-feedback-de-carregamento-nas-analises/) |
| 260710-u2r | Flash de tabela colapsada ao trocar de aba + artefato "0" (st.tabs → segmented_control) | 2026-07-10 | 4268eb9 | [260710-u2r-flash-de-colapso-de-tabela-ao-trocar-aba](./quick/260710-u2r-flash-de-colapso-de-tabela-ao-trocar-aba/) |
| 260710-u4n | Formatação numérica BR no veredito + nits (-0.0%, sinal regressão, rótulos) | 2026-07-10 | 3a04ac8 | [260710-u4n-padronizar-formatacao-numerica-br](./quick/260710-u4n-padronizar-formatacao-numerica-br/) |
| 260710-u3g | Glossário de siglas (tabelas transpostas) + legenda de selos e triângulos | 2026-07-10 | fa1cc4f | [260710-u3g-glossario-siglas-legenda-selos-e-triangulos](./quick/260710-u3g-glossario-siglas-legenda-selos-e-triangulos/) |
| 260710-u5c | Renomeia menus/termos (Garimpar ações, Selic piso DY, Análise técnica) + corrige contagem | 2026-07-10 | 7d8d70b | [260710-u5c-consistencia-de-copia-contagem-menus](./quick/260710-u5c-consistencia-de-copia-contagem-menus/) |
| 260712-p6r | Freio do Ranking no Streamlit (paridade CLI↔UI: ITUB4 deixa de ser "Cara") + label ENS-01 em cmd_rank | 2026-07-12 | f9ace2d | [260712-p6r-freio-ranking-streamlit](./quick/260712-p6r-freio-ranking-streamlit/) |

## Deferred Items

Items carried forward do fechamento do marco anterior:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Docs engine | DDM-DOC-01 (docstring/teste de t em ddm.py, IN-06) | v2+ | 2026-06-04 |
| Refino | Payout-alvo por setor configurável | v2+ | 2026-06-27 |
| UI | Sinalização de "ano extraordinário" na tabela de Fundamentos | v2+ | 2026-06-27 |
| Fiscal/NF | NFS-e automática por assinatura IMPLEMENTADA + VALIDADA (2026-07-09). RETOMAR: conferir no painel Asaas se a nota do smoke (`inv_000021028809`) autorizou; contador confirmar alíquota ISS oficial (usado 2,01%). | done | 2026-07-09 |
| UI | NF-e: exibir link da nota emitida (webhook Asaas) na página "Minha conta" → botão "Baixar nota fiscal". | v2.1 | 2026-07-09 |

## Session Continuity

Last session: 2026-07-13T08:00:33.390Z
Stopped at: Completed 05-04-PLAN.md (loop D-12 aberto)
Resume file: None

## Operator Next Steps

- **v2.2:** aprovar o roadmap e rodar `/gsd-discuss-phase 1` (ou `/gsd-plan-phase 1`) para a Fase 1 (classificador de arquétipo — o coração/gargalo do milestone).
- **v2.0 (encerrado):** estornar (ou não) o smoke real R$19,90 PIX no painel Asaas — decisão do operador.
- **Backlog v2.1 (UX, deferido):** ativar NFS-e no painel Asaas + link da NF na página de conta; achados 6–18 do review de UX.
