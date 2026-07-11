---
gsd_state_version: 1.0
milestone: v2.2
milestone_name: Motor de Valuation por Arquétipo
status: verifying
stopped_at: Phase 1 context gathered
last_updated: "2026-07-11T20:45:11.924Z"
last_activity: 2026-07-11
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 8
  completed_plans: 6
  percent: 75
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-11)

**Core value:** Cada tipo de negócio é roteado para o motor de valuation certo antes de valuar,
e nenhum veredito final é puxado por um modelo que não serve àquele perfil — um compounder de
qualidade (banco) nunca mais é carimbado "evitar" porque o DDM de estágio único não cabe nele.
**Current focus:** Phase 01 — classificador-de-arqu-tipo-roteamento

## Current Position

Phase: 01 (classificador-de-arqu-tipo-roteamento) — EXECUTING
Plan: 2 of 2
Status: Phase complete — ready for verification
Last activity: 2026-07-11

Progress: [████████░░] 75%

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

- **Não quebrar os golden do valuation sem intenção:** `test_ddm.py` (DDM Itaú R$37,22 input fixo),
  `test_selo.py` (cortes de cor + rótulos da matriz + firewall selo↛report), `test_vulc3_regressao.py`
  (capstone e2e; veredito começa com "VERIFICAR"), `test_guardrails_fix06.py`, `test_consistencia_modos.py`
  (mesmo número entre Analisar/Garimpo/Ranking — Core Value). Se a refatoração mudar prefixos/rótulos
  de veredito, atualizar `faixa_do_veredito` (selo.py:88) e `report._veredito_token` (report.py:355) juntos.

- **Firewall selo↛report:** `selo.py` NÃO importa `report.py` (recebe só primitivos) — preservar ao
  refatorar a agregação do veredito (Fase 3).

- **Consistência cross-modo:** métodos canônicos `*_valuation()` em `fundamentals.py` são fonte única
  — mexer neles reverbera nos 3 modos (Analisar/Garimpo/Ranking).

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260710-u1f | Feedback de carregamento nas análises (spinner/status em Analisar/Garimpar/Ranking) | 2026-07-10 | 1e6524e | [260710-u1f-feedback-de-carregamento-nas-analises](./quick/260710-u1f-feedback-de-carregamento-nas-analises/) |
| 260710-u2r | Flash de tabela colapsada ao trocar de aba + artefato "0" (st.tabs → segmented_control) | 2026-07-10 | 4268eb9 | [260710-u2r-flash-de-colapso-de-tabela-ao-trocar-aba](./quick/260710-u2r-flash-de-colapso-de-tabela-ao-trocar-aba/) |
| 260710-u4n | Formatação numérica BR no veredito + nits (-0.0%, sinal regressão, rótulos) | 2026-07-10 | 3a04ac8 | [260710-u4n-padronizar-formatacao-numerica-br](./quick/260710-u4n-padronizar-formatacao-numerica-br/) |
| 260710-u3g | Glossário de siglas (tabelas transpostas) + legenda de selos e triângulos | 2026-07-10 | fa1cc4f | [260710-u3g-glossario-siglas-legenda-selos-e-triangulos](./quick/260710-u3g-glossario-siglas-legenda-selos-e-triangulos/) |
| 260710-u5c | Renomeia menus/termos (Garimpar ações, Selic piso DY, Análise técnica) + corrige contagem | 2026-07-10 | 7d8d70b | [260710-u5c-consistencia-de-copia-contagem-menus](./quick/260710-u5c-consistencia-de-copia-contagem-menus/) |

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

Last session: 2026-07-11T20:44:57.983Z
Stopped at: Phase 1 context gathered
Resume file: None

## Operator Next Steps

- **v2.2:** aprovar o roadmap e rodar `/gsd-discuss-phase 1` (ou `/gsd-plan-phase 1`) para a Fase 1 (classificador de arquétipo — o coração/gargalo do milestone).
- **v2.0 (encerrado):** estornar (ou não) o smoke real R$19,90 PIX no painel Asaas — decisão do operador.
- **Backlog v2.1 (UX, deferido):** ativar NFS-e no painel Asaas + link da NF na página de conta; achados 6–18 do review de UX.
