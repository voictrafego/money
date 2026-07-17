---
gsd_state_version: 1.0
milestone: v2.4
milestone_name: Fidelidade do Valuation
status: planning
stopped_at: Phase 13 context gathered
last_updated: "2026-07-17T23:53:09.792Z"
last_activity: 2026-07-17
progress:
  total_phases: 8
  completed_phases: 6
  total_plans: 27
  completed_plans: 27
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md · .planning/REQUIREMENTS.md · .planning/research/SUMMARY.md

**Core value:** Os números que o app mostra precisam ser **fiéis ao método do livro e consistentes
entre si** — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.

**Critério de aceite soberano do marco v2.4:** o app reproduz o **caso-exemplo do próprio livro** —
ITUB4, Cap. 17 (Tabelas 41/43): `g` = 10,24% · `Ke` = 12,48% → **V = R$ 37,22** (região R$ 35–39,
MS ±5%). **Hoje o app entrega R$ 16,13.**

**Current focus:** Phase 12 — Custo de capital / Ke (KE)

## Current Position

Milestone: v2.4 — Fidelidade do Valuation (Phases 7–14)
Phase: 13
Plan: Not started
Status: Ready to plan
Last activity: 2026-07-17

Progress: [██████████] 100%

**Suíte:** `519 passed, 1 skipped, 20 deselected, 0 failed, 0 xfailed, 0 XPASS` (517 do pós-12-03 +
os 2 testes de validação KE-04 do 12-04). `-m golden_nivel` **20 passed, 0 CLASSIFICACAO ORFA**.
**AS DUAS DOENÇAS DO v2.4 ESTÃO CURADAS** (BLIND-03 na Fase 10, BLIND-02b no 12-02): `xfail_estritos()`
== **0**; a guarda de seleção foi reconciliada à cura (0 pendentes é válido; as ex-doenças rodam como
invariantes selecionadas). Sobra só **1 skipped** = jackknife (Fase 14). **PRIM-05 cumprido: o golden
ITUB4=32,88 NÃO existe mais no repo** (DELETADO — critério de saída da Fase 10).

**12-03 (commit de knob SANCIONADO):** `config.yaml` + `calibracao.lock.yaml` mudaram JUNTOS —
`capm.erp_local` 0,06 → **0,045** (ERP unificado) e as folhas do clamp (`erp_banco`/`ke_piso`/`ke_teto`)
REMOVIDAS de config+lock; escopo do lock **29 → 26 folhas** (motores 10 → 7), congelados 26 → 23,
**orçamento intacto em 3 graus**. A suíte NÃO se moveu (a invariância do BLIND-02b independe do nível
do ERP). Commit `615843f`, trailer sem ticker, sem `--no-verify`. **KE-02 e KE-04 completos.**

**⚠ DÍVIDA WR-04 — MAIS AVANÇADA (10-04 + 11-03):** o Phase 7 cindiu só 2 de ~20 funções mistas; o
10-04 curou as 3 mistas dentre os 7 goldens de nível ITUB4; o **11-03 curou `test_growth_reconciliacao`
(3 funções → adoção/teto/trava Ke como `invariante`), a rota seguradora (contrato `motor=='seguradora'`)
e a VULC3 cascata** (banda `vmax<3× preço` do g=2,5% deletada; estrutura extraída) — todos
split-before-delete, invariantes extraídos ANTES no MESMO diff, zero órfão (superfície de
constrangimento AUMENTOU). **Ainda ABERTO** para as funções mistas de Ke (`SAN-01 reetiqueta`,
`test_financeira_rim_destrava`, bandas de Ke) que a **Fase 12** vai deletar — aplicar o mesmo padrão.
Fila de triagem e varredor AST: `07-VERIFICATION.md` (apêndice).

**⚠ `core.hooksPath` é estado local por clone.** Todo clone novo nasce sem a proteção do BLIND-05;
`test_hook_do_blind05_esta_instalado` é o que torna isso vermelho em vez de proteção fantasma.

## A ordem é a decisão de arquitetura mais importante do marco

**Provada por simulação sobre os 104 tickers, não deduzida.** Violá-la piora o modelo.

```
7  BLIND — blindagem processual   (quarentena de goldens + invariantes)
8  SAN   — sanidade dos dados     (asserts ANTES dos consertos; eles SÃO o teste de regressão)
9  DATA  — ingestão correta
10 PRIM  — primitivas sem viés    (o golden ITUB4 32.88 QUEBRA e é DELETADO — critério de saída)
11 GROW  — crescimento / g        (BLIND-02 vira verde AQUI)
12 KE    — custo de capital / Ke  (SEPARADA da 11 de propósito)
13 ENG   — motores + contrato     (motores: ~20 → ≤5 chaves, CONTADO)
14 VAL   — validação honesta      (o caso do livro passa: V = R$ 37,22)
```

### As três regras duras

| # | Regra | Prova |
|---|-------|-------|
| **A** | **NÃO fundir a Fase 11 (`g`) com a Fase 12 (`Ke`)** | Consertar o Ke ANTES do g **piora**: ITUB4 0,75→0,64; BBDC4 0,71→**0,52**. O `ke_teto` é uma **muleta que compensa o viés do `g`**. Ke sozinho é líquido zero (0,68→0,67). Fundir dá um número e zero diagnóstico. |
| **B** | **O golden `ITUB4: 32.88 ± 0.20` DEVE quebrar e ser DELETADO** | Critério de saída **explícito** da Fase 10. Ele foi calibrado para cancelar o haircut de −9,1% da normalização — dois erros se anulando. **Deletar, não atualizar** (atualizar mantém o reflexo vivo). |
| **C** | **A deleção de knobs é CONTADA** | Bloco `motores:` do `config.yaml`: **~20 chaves → ≤ 5** (Fase 13). Orçamento travado: **3 graus de liberdade** (`ERP`, `n_fade`, `PIB_real`). Sem contagem, não acontece. |

## Performance Metrics

**Velocity:**

- Marcos arquivados: v1.7 (66+ plans / 21 fases), v2.0 (3 fases), v2.2 (3 fases / 14 plans), v2.3 (3 fases / 10 plans)
- v2.4: 0 plans completed

**By Phase (v2.4):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 7. Blindagem processual (BLIND) | TBD | - | - |
| 8. Sanidade dos dados (SAN) | TBD | - | - |
| 9. Ingestão correta (DATA) | TBD | - | - |
| 10. Primitivas sem viés (PRIM) | TBD | - | - |
| 11. Crescimento / g (GROW) | TBD | - | - |
| 12. Custo de capital / Ke (KE) | TBD | - | - |
| 13. Motores + contrato de saída (ENG) | TBD | - | - |
| 14. Validação honesta (VAL) | TBD | - | - |
| 08 | 6 | - | - |
| 09 | 5 | - | - |
| 10 | 4 | - | - |
| 12 | 4 | - | - |

**Recent Trend:**

- Último marco enviado: v2.3 Calibração do Valuation (2026-07-13, tag `v2.3`, deployado) — **auditado
  como overfit**: ~8 graus de liberdade sobre 4 observações; o "4/4 PASS" real é **2/4**.

- Trend: o v2.4 corrige a causa que os knobs do v2.3 mascaravam.

| Phase 7 P04 | 25min | 2 tasks | 3 files |
| Phase 08 P01 | 22min | 3 tasks | 6 files |
| Phase 08 P02 | 15min | 2 tasks | 5 files |
| Phase 08 P03 | 35min | 2 tasks | 5 files |
| Phase 08 P04 | 18min | 3 tasks | 4 files |
| Phase 08 P05 | 20min | 2 tasks | 4 files |
| Phase 09 P01 | 40min | 2 tasks | 3 files |
| Phase 09 P02 | 55min | 2 tasks | 4 files |
| Phase 09 P03 | 20min | 2 tasks | 4 files |
| Phase 09 P04 | 12min | 2 tasks | 4 files |
| Phase 09 P05 | 256min | 2 tasks | 7 files |
| Phase 10 P01 | 65 | 3 tasks | 10 files |
| Phase 10 P02 | 26min | 2 tasks | 9 files |
| Phase 10 P03 | 12min | 3 tasks | 13 files |
| Phase 10 P04 | 40min | 2 tasks | 4 files |
| Phase 11 P01 | 14min | 2 tasks | 4 files |
| Phase 11 P03 | 35min | 3 tasks | 5 files |
| Phase 12 P01 | 15min | 2 tasks | 10 files |
| Phase 12 P02 | 30min | 3 tasks | 9 files |
| Phase 12 P03 | 15min | 1 tasks | 2 files |
| Phase 12 P04 | 20min | 2 tasks | 2 files |

## Accumulated Context

### Decisions (v2.4)

- **KE-04 (Fase 12 / plano 12-04) — "nada explode sem clamp" PROVADO POR EXECUÇÃO; o gate final da
  fase.** `tests/test_ke_validacao.py` (2 testes `invariante`, arquivo novo) fecha a Doença 3 com
  evidência de RODAR a regressão, não com "suíte verde" genérica (memória `guardrails-devem-ser-
  provados-por-execucao`). **(a)** `test_ke_min_estrutural_acima_do_g_cap`: a DESIGUALDADE `rf +
  0,33 × erp_local > g_cap` lida do config DINAMICAMENTE (robusta ao drift do rf; passaria com ERP
  0,06 e com 0,045) — o **11,07%** (Ke_min no rf AO VIVO ~9,58%) aparece só em comentário, NUNCA
  cravado num assert; offline dá ~11,99% > 7,28%. O **piso do Blume 0,33** asseverado no INTERCEPTO
  (`beta_blume(0)==0,33` + monotonicidade), provando que `Ke_min` INDEPENDE de outlier de β.
  **(b)** `test_regressao_104_sem_explosao`: roda `report.analisar_acao` sobre os **104 REAIS**
  (`hs.CAMINHO_SNAPSHOT_LIMPO`) com o **β setorial carimbado** (`macro.carimbar_beta_setorial` —
  Ke offline idêntico ao app, D-06); **93 tickers com Ke, ZERO ofensor:** todo `Ke ≥ Ke_min > g_cap`,
  `intrinseco_motor` finito e `> 0`, spread `Ke − g_T > 0` (`g_T = max(0, min(ROE_T×ret, g_cap))`),
  e `V < 50× preço` (max medido 4,7×). `None` aceitável (never-raise). **NENHUM guard novo, nenhum
  clamp sob outro nome** — a perpetuidade converge pela aritmética do piso do Blume; se explodisse,
  o bug seria ROE_T/spread (Fase 13). **BLIND-04a limpo** (sem `ticker==nível`; `test_blindagem_meta`
  verde na varredura AST). **Fronteira: validação PURA** — `git diff config.yaml calibracao.lock.yaml`
  VAZIO (o commit sancionado foi o 12-03), orçamento em 3 graus, g_cap da Fase 11 não recalibrado,
  nenhum motor tocado. Ambas as entradas em `classificacao.yaml` no mesmo diff (0 órfão). Suíte
  **519 passed, 1 skipped, 20 deselected, 0 failed, 0 xfailed, 0 xpassed**; `-m golden_nivel` 20
  passed, 0 ORFA. **KE-04 completo por validação — a Fase 12 está pronta para fechar.** Commits:
  `7d85b65` (T1), `6f008d0` (T2).

- **KE-02/KE-04 (Fase 12 / plano 12-03) — o commit de knob SANCIONADO: ERP unificado em 4,5% e o
  clamp removido do ORÇAMENTO.** `capm.erp_local` **0,06 → 0,045** (ERP de mercado maduro puro,
  Damodaran; o prêmio small-cap/iliquidez de +1,5% do config antigo removido — a Selic já precifica
  risco-país/inflação) em `config.yaml` E no grau `ERP` do `calibracao.lock.yaml` (`valor: 0.045`),
  no MESMO commit. As três folhas do clamp (`erp_banco`/`ke_piso`/`ke_teto`) **DELETADAS de config+lock**,
  **sem nenhuma menção stale** (grep dos tokens proibidos == 0 nos dois arquivos; a citação de `ke_piso`
  no comentário de `ke_g_spread_min` foi scrubada — folha e valor `0.03` intactos). Escopo do lock
  **29 → 26 folhas** (motores 10 → 7); congelados 26 → 23; comentários de contagem coerentes nos 3
  lugares (escopo/header/partição). **Orçamento intacto em 3 graus** (ERP, n_fade, PIB_real):
  `test_orcamento_de_knobs_e_exatamente_3` (partição `folhas == graus | congelados`) e
  `test_knobs_batem_com_o_lock` verdes porque config e lock mudaram juntos. **Nenhum clamp
  reintroduzido sob outro nome** — a perpetuidade converge pelo **piso do Blume** (`β_blume ≥ 0,33 ⇒
  Ke_min 11,07% > g_cap 7,28%`) por aritmética; se um V explodir sem clamp, o bug é `ROE_T`/spread
  (Fase 13), não o Ke. Trailer `Knob-Change-Justification:` de razão econômica **sem ticker**; hook
  BLIND-05 (par config+lock sancionado) e teste `-k justificativa` passaram **sem `--no-verify`**.
  **Fronteira respeitada:** g_cap da Fase 11 NÃO recalibrado; nenhum motor tocado (corte `motores:`
  ~11 → ≤5 é a Fase 13). Suíte default **517 passed, 1 skipped, 20 deselected, 0 failed, 0 xfailed**
  (idêntica ao pós-12-02: a invariância do BLIND-02b independe do NÍVEL do ERP). Commit: `615843f`.

- **KE-01/KE-04/KE-05 (Fase 12 / plano 12-02) — o Ke COLAPSA num só, o clamp SAI por código e a
  metade Ke da Doença 1 morre (BLIND-02b curado).** `a.ke = ke_local(beta_blume(c.beta, c.setor,
  cfg["capm"]["beta_setorial"]), rf_local, erp_local)` (report.py:470): o Ke exibido (L982) == o que
  alimenta o RIM (L261, `ke=a.ke`, NÃO recomputa) == o centro da matriz (L540). **`motores.ke_rim`
  DELETADO inteiro** (clamp `max(ke_piso, min(ke, ke_teto))` + teto `ke_live`), **SEM guard
  substituto** — a perpetuidade converge pelo **piso do Blume** (`β_blume = 0,33+0,67×base ≥ 0,33`
  ⇒ `Ke_min > g_cap`) por ARITMÉTICA, não por trava. **BLIND-02b** (`test_invariancia_inflacao_
  engine_itub4`) vira **invariante NORMAL verde**: sem o clamp, o Ke reage ao `rf` (a perna do `rf`
  sobe o Ke na mesma proporção que sobe o `g`, o spread `Ke−g` se preserva, o `V` fica quase
  invariante); `xfail_estritos()` **1→0**, `assert variacao < LIMIAR_INFLACAO` INTOCADO. **Guarda de
  seleção reconciliada à cura** (BLOQUEADOR Correção #3): de "a doença é `xfail(strict)` selecionado"
  para "a ex-doença é `invariante` selecionada" — 0 doenças pendentes é VÁLIDO; nada deletado/skipado/
  afrouxado (o alarme migrou do XPASS para o próprio assert, que agora executa). **Bracket-read
  condenado** `rim_cfg["ke_teto"]` em `test_terminal_load_bearing` reescrito estruturalmente
  (`rf_local+1,0×erp_local`) — imune à remoção das folhas no Plano 03; busca global confirma NENHUM
  consumidor vivo de `ke_teto`/`ke_piso`/`erp_banco` fora de `motores.py`/config/lock. **2 goldens de
  banda de Ke DELETADOS** (`test_ke_local_na_faixa_small_cap_br`, `test_ke_rim_na_banda_estrutural`) +
  entradas de `classificacao.yaml` no mesmo diff (0 órfão). **DESVIOS (auto-fix, asserts intactos):**
  (1) recalibração do β da fixture `TETO` 3,0→5,0 em `test_growth_reconciliacao` (β cru 3,0 dava Ke
  0,285 no modelo antigo; sob Blume dá 0,245 < 0,25 e quebrava a PRECONDIÇÃO `Ke>0,25` — doutrina teto
  absoluto 0,25 intacta, mirror PRIM-02); (2) higiene do detector BLIND-04a (Pitfall 6) — literal
  `"ITUB4"` movido p/ `helpers_blindagem.empresa_itub4` (fora de `test_*`), pois pós-cura o ex-BLIND-02b
  viraria falso-positivo do detector; detector NÃO afrouxado, varredura não excluída. **Fronteira
  respeitada:** `git diff config.yaml calibracao.lock.yaml` **VAZIO** (o corte ERP 0,06→0,045 e a
  remoção das folhas mortas são o **Plano 03**, commit sancionado config+lock; orçamento de 3 graus
  intacto); g_cap da Fase 11 NÃO recalibrado. Suíte default **517 passed, 1 skipped, 20 deselected,
  0 failed, 0 xfailed**; `-m golden_nivel` **20 passed, 0 ORFA**. Commits: `d750c34` (T1), `c291ae9`
  (T2), `94e03d4` (T3).

- **KE-03 infra (Fase 12 / plano 12-01) — beta setorial+Blume montado, PURAMENTE ADITIVO (a.ke
  inalterado).** Gerador offline (`scripts/gerar_beta_setorial.py`) + artefato versionado
  `data/beta_setorial.yaml` (14 setores, **mediana do beta CRU**, limiar estrutural **n>=3** — a
  propriedade da mediana que rejeita 1 outlier, nunca alvo de ticker; `_normalizar_setor` strip do
  prefixo "Emp. Adm. Part. - " agrupa holding+operadora, fallback 42→24 de 104). `capm.beta_blume`
  aplica Blume `0,33+0,67×base` **uma vez** (setorial > individual, fallback D-04 ao β cru), com
  contrato de borda **`β None → None`** (never-raise, como `ke_rim`) — decidido a favor do
  `<behavior>` do plano sobre o pseudo-código do RESEARCH. Carimbo de **fonte única** nos **3** entry
  points (`cli._carimbar_macro`, `app.py`, `backtest._CHAVES_GLOBAIS`+`rodar_cesta`); `report/setup.py`
  **NÃO** (Correção #2). **D-06 provado por teste DURO cross-menu:** `test_cli_rank_consistencia`
  assevera `beta_setorial` **E** `a.ke` idênticos entre `analyze` e `rank`. **Fronteira respeitada:**
  NADA consome `beta_blume` ainda (a engine segue `capm.ke_local(c.beta,…)` com β cru e ERP 0,06) —
  a mudança de Ke é o **plano 12-02**; `BLIND-02b permanece xfailed` (viraria XPASS=FAIL se `a.ke`
  tivesse mudado). `capm` importa `ingest.macro` para a normalização (sem ciclo, sem acoplar à rede).
  Suíte default **517 passed, 1 skipped, 22 deselected, 1 xfailed, 0 failed** (+18 testes; base
  inalterada); `-m golden_nivel` **22 passed, 0 ORFA**; `git diff config.yaml calibracao.lock.yaml`
  **VAZIO** (β setorial é DADO fora do lock, D-07; orçamento de 3 knobs intacto). **KE-03 fica
  Pending** — co-reivindicado por 12-02, onde a behavior (Ke muda) de fato aterrissa. Commits:
  `d0af0ac`/`8804622` (T1), `17b43c2`/`5a03a40` (T2).

- **GROW-04/05 (Fase 11 / plano 11-03) — o método antigo do `g` SAI do repo (split-before-delete)
  e os 2 knobs decorativos viram load-bearing por COBERTURA; a fase fecha.** **(1) Goldens de nível
  do `g` antigo DELETADOS, nunca atualizados** — `test_g_fund_menor_que_cagr`/`test_teto_absoluto_025`/
  `test_trava_ke` (`test_growth_reconciliacao`), `test_rota_seguradora_bbse3` (nível 39,87, lia
  `cfg["ddm"]["g_estavel"]` REMOVIDO na Fase 11) e — **extensão de escopo** — `test_vulc3_cascata_domada`
  (golden_nivel JÁ vermelho desde 11-02: o `g_cap` explodiu a banda `vmax < 3× preço` do g=2,5% para
  ~3,6×). Os **invariantes estruturais presos foram EXTRAÍDOS ANTES da deleção, no MESMO diff (WR-04)**:
  adoção de `g_fundamentos` (GROW-04), teto absoluto 0,25, trava Ke (FIX-01/D-02), rota seguradora
  (`motor=="seguradora"`, finito>0), e da VULC3 (norm robusta / `g_fund≤0` sob payout>100% / Ke
  relacional / matriz de sensibilidade / veredito VERIFICAR / cross-menu). Função + linha do
  `classificacao.yaml` juntas (zero órfão). **NENHUM nível novo asserido** (deletar, não reajustar).
  **(2) Cobertura D-07 (GROW-05):** o RI terminal do RIM sob o spread `Ke − g` apertado que o `g_cap`
  produz (~5,7pp: `ke_rim` 0,13 − `g_cap` 0,0728) **não explode** (`vp_terminal < V`) e **degrada
  honesto** (spread < `ke_g_spread_min` ⇒ `vp_terminal == 0`, fade-only, never-raise; `valor_gordon`
  → None em ke−g≤0). `excesso_sustentavel`/`ke_g_spread_min` **LIDOS de config**, não recalibrados —
  load-bearing por COBERTURA, não por knob move. **(3) Não-regressão contra o MAPA REAL dos 104**
  (`hs.CAMINHO_SNAPSHOT_LIMPO`, NÃO fixtures sintéticas): TAEE11 (regulada — `intrinseco_motor` é None
  por arquitetura; valida pela banda DDM `vmin/vmax` 37–75), BBSE3 (85,85, seguradora), VULC3 (11,55,
  normalizado) finitos/positivos/sensatos; os 104 (menos as falhas de mercado) sem NaN/inf/exceção
  (None aceitável), com limite de sanidade 50× preço sem nomear ticker (BLIND-04a-safe). Medido:
  `g_cap = 0,0728`; ITUB4 `g_fundamentos = 0,0959`, `g_alto = min(g_fund, ke)`. **Fronteira respeitada:
  BLIND-02b PERMANECE xfail (não XPASS — a metade Ke da Doença 1 é a Fase 12); `git diff config.yaml
  calibracao.lock.yaml` VAZIO (só ADIÇÃO de cobertura, nenhum knob movido); orçamento em 3 graus.**
  Suíte default **499 passed, 1 skipped, 22 deselected, 1 xfailed, 0 failed**; `-m golden_nivel`
  **22 passed, 0 CLASSIFICACAO ORFA**. Commits: `dcfd1a2` (Task 1), `cebe32f` (Task 2), `20bb97d`
  (Task 3). **WR-04 avançado:** as funções mistas do `test_growth_reconciliacao` e a VULC3 cascata
  (que a dívida listava para "Fases 11/12/13") foram curadas aqui.

- **GROW-01/02 (Fase 11 / plano 11-01) — o insumo `π_ciclo` está CARIMBADO; a engine segue intocada.**
  `macro.ipca_ciclo_para_g(fallback, anos=10)` é o **irmão exato** de `selic_ciclo_para_capm`: **média
  ARITMÉTICA** de `_ipca_anual_dezembro(anos).values()` (SGS 13522 reusada da PRIM-04 — zero fonte de
  rede nova), degradação graciosa → `fallback`. Resolvido UMA vez nos entry points e carimbado em
  `cfg["macro"]["pi_ciclo"]` na **MESMA janela `rf_ciclo_anos`** do rf/deflatores (a simetria rf↔π_ciclo
  do GROW-02 — o que torna o valuation invariante à inflação). `cli._carimbar_macro` é a fonte única
  (analyze+rank, WR-03); `app.py` ganhou o wrapper cacheado `pi_ciclo_capm` (@st.cache_data ttl=3600,
  espelha `ipca_deflatores_capm`) + o carimbo no fluxo analyze (read-only preservado). `config.yaml`
  ganhou o default offline `macro.pi_ciclo: 0.0518` (mirror do `selic_fallback`). **Bloco `macro` FORA
  do escopo do lock** (motores/capm/ddm/normalizacao), como `ipca_deflatores` — dado objetivo do BCB,
  NÃO knob: **orçamento de 3 graus intacto** (`git diff calibracao.lock.yaml` VAZIO; `config.yaml` só
  adiciona `macro.pi_ciclo`). **Pureza:** `grep ipca_ciclo_para_g src/analista/report/` VAZIO — a engine
  não chama o helper. **Fronteira respeitada:** ZERO derivação de `g_cap` (é o Plano 02), ZERO knob de
  valuation tocado, **BLIND-02b permanece xfailed** (vira verde só na Fase 12 — se ficasse verde aqui,
  seria bug). Suíte default **490 passed, 1 skipped, 27 deselected, 1 xfailed, 0 failed**. Nota de
  ambiente: BCB acessível na execução → a verificação "offline" do helper retornou o valor ao vivo
  (`0,05138` ≈ default `0,0518`); o ramo de fallback é exercitado por construção. Commits: `47574e6`
  (Task 1), `9069e3a` (Task 2).

- **PRIM-05 (Fase 10 / plano 10-04) — CRITÉRIO DE SAÍDA CUMPRIDO: o golden ITUB4=32,88 foi DELETADO,
  não atualizado; a Fase 10 está CONCLUÍDA.** `test_backtest_bancos.py::test_backtest_alvos_recalibrados`
  (o golden soberano `ITUB4 32,88 ±0,20`) e mais 6 goldens de nível ITUB4 puros (banda RIM ×3, gate de
  quórum, cesta-rota-por-ticker, rota-seguradora-não-pega-banco, dispatch-banda) foram removidos —
  função E linha do `classificacao.yaml` no MESMO diff (Pitfall 5, zero órfão). **Deletar, nunca
  atualizar** (Armadilha 3: o `32,88` existe para cancelar o haircut de −9,1% da normalização — dois
  erros se anulando; atualizar o número mantém o reflexo do overfit do v2.3 vivo). **WR-04 curado para
  os 3 mistos (checkpoint:decision → Option A):** a §Golden Disambiguation da RESEARCH chamava os 7 de
  "bandas puras", mas a auditoria AST do WR-04 (07-VERIFICATION Gap 2) prova invariantes estruturais
  presos em 2/3/6 sem sobrevivente equivalente — a dívida "OBRIGATÓRIA ANTES DA FASE 10" que o Phase 7
  não fechou. Antes de apagar cada banda, o invariante foi EXTRAÍDO para uma função `invariante`
  (BLIND-04a-safe, sem ticker/reais): `test_nenhuma_rota_diferente_de_rim_e_silenciosa` (D-08
  no-silent-routing), `test_nenhuma_reprovacao_de_banda_e_silenciosa` (D-08 no-silent-FAIL — o CONTADOR
  de quórum era o golden de nível e morreu; a disciplina de anotação sobrevive), e
  `test_setor_de_banco_nao_casa_o_token_seguradora` (roteamento-negativo, puro no casador de token).
  Itens 1,4,5,7 deletados direto (item 1 é banda pura; 4/5/7 já cobertos por sobreviventes). **Itens
  8-9 → adiar Fase 13** (RESEARCH A3: item 1 é o único requisito DURO; 8-9 são guardas cujas substitutas
  nascem na 13). Suíte default **486 passed, 1 skipped, 27 deselected, 1 xfailed, 0 failed**; orçamento
  de 3 knobs intacto (`git diff config.yaml calibracao.lock.yaml` VAZIO); meta-teste BLIND-04a verde;
  nenhum assert vivo de nível ITUB4 sobra (só prosa BLIND-02b/Fase-12 e honeypots do detector).
  Commit: `abcb584` (test). **ZERO código de produção tocado** (4 arquivos, todos de teste).

- **PRIM-04 (Fase 10 / plano 10-03) — o motor CÍCLICO consome a série de lucro DEFLACIONADA por
  IPCA a reais do último ano.** `macro.ipca_deflatores_anuais(anos)` puxa a série anual do IPCA do
  BCB (SGS **13522 amostrado em dezembro** = IPCA do ano-calendário, sem escolha livre de ano-base;
  reusa a constante `IPCA_12M`) e a compõe em `{ano: prod(1+ipca[y]) para y in (ano+1..T)}`,
  `defl[T]=1.0` — com separação limpa **rede** (`_ipca_anual_dezembro`, esqueleto do `_selic_historico`:
  date-range + 3 retries + degradação graciosa para `{}`) × **pura** (`_compor_deflatores`, testável
  offline). O ramo `"normalizado"` de `report._intrinseco_por_motor` deflaciona `c.serie('lucro_liquido')`
  lendo `cfg['macro']['ipca_deflatores']` **OFFLINE** ANTES de `norm.media_ciclo` (a MÉDIA through-cycle,
  NÃO o endpoint Theil-Sen), com **fallback nominal never-raise** quando os deflatores estão
  ausentes/vazios. Stamping resolvido UMA vez nos entry points (`cli.py`/`app.py` via `@st.cache_data`,
  na MESMA janela do `rf` — a simetria que torna o valuation invariante à inflação) e carimbado em `cfg`;
  `backtest.carregar_snapshot` lê o carimbo do snapshot (`ipca_deflatores` em `_CHAVES_GLOBAIS`,
  defensivo → `{}`) e `rodar_cesta` o injeta numa CÓPIA do cfg — **disciplina idêntica ao `rf_local`,
  engine determinística** (`test_backtest_determinismo` verde). **Bloco `macro` NOVO no `config.yaml`,
  FORA do escopo do lock** (`motores/capm/ddm/normalizacao`): dado objetivo do BCB (como o `rf`), NÃO
  grau de liberdade — **orçamento de 3 knobs intacto** (`git diff calibracao.lock.yaml` VAZIO;
  `motores.ciclica.anos_media/winsor` congelados intocados). **ZERO dependência nova.** **Nenhum snapshot
  modificado** (o de bancos roteia 100% p/ RIM/seguradora — não exercita o motor cíclico; `carregar_snapshot`
  lê o carimbo defensivamente). **Desvio mecânico:** `carregar_snapshot` virou 3-tupla → 4 call sites
  atualizados (bancos degradam a `{}`). **4 golden_nivel vermelhos são TODOS pré-10-03** (verificado por
  execução no commit `abeab5a`, fim do 10-02): ITUB4 32,88 + BBSE3 (seguradora) + 2 de `g`
  (`test_growth_reconciliacao`) — nenhum passa pelo ramo `"normalizado"` alterado; ficam intactos/
  quarentenados (10-04 / Fase 11). Suíte default **483 passed, 1 skipped, 34 deselected, 1 xfailed,
  0 failed**. Commits: `0f44dae`/`69766c2` (Task 1), `701d6ea`/`c14aee5` (Task 2), `5528819` (Task 3).

- **PRIM-02/PRIM-03 (Fase 10 / plano 10-02) — `roe_valuation` virou a MEDIANA da série de `roe(a)`
  e `serie_lucro_normalizada` virou CRUA, com um SIGNAL SPLIT do ROE (Option A).** `roe_valuation`
  deixou de cruzar bases temporais (base de lucro de 3a ÷ PL do último ano) e passou a ser
  `median([roe(a) for a in anos_ordenados() se não None])` — reusando a definição única `roe(ano)`
  (lucro_t ÷ PL médio(t-1,t)), a MESMA estatística de `report._roe_through_cycle`, então o `roe0` e o
  `roe_terminal` do RIM não divergem mais. `serie_lucro_normalizada` devolve a série de `lucro_liquido`
  CRUA (winsorização temporal removida — a Fase 10 só REMOVE o viés; o desenho do `g` robusto é a Fase
  11); `norm.serie_winsorizada` continua VIVA para o screening (FCO/dividendos/tangível, Cap. 8).
  **Checkpoint de decisão (Option A, resolvido pelo usuário):** `roe_valuation` é consumido também pelo
  ROTEAMENTO de `arquetipo.py` — a mediana through-cycle SUBESTIMA um compounder de ROE crescente
  (fica no meio da subida; medido: uma série `[0,063…0,329]` tem mediana 0,113 < limiar `roe_alto_min`
  0,15) e o desrotearia de CRESCIMENTO. **Signal split (espelha o estimator split do PRIM-01):** novo
  helper `roe_qualidade_atual` (o ROE-endpoint pré-PRIM-02, só-roteamento); `arquetipo` consome-o; o
  `roe_valuation` (mediana) segue servindo RIM/display. `roe_alto_min` NÃO tocado. **Core Value
  preservado:** o `crescimento_lucro_3a` do screening foi repointado à MESMA `serie_lucro_normalizada`
  crua → `crescimento_lucro_3a == g_historico` por CONSTRUÇÃO (era coincidência winsor). **3 deviations
  mecânicas (asserts intactos):** rewrite do invariante do endpoint p/ a mediana; rewrite do contrato do
  spike p/ a série crua; recalibração dos NÚMEROS das fixtures da coerência de direção pela própria
  doutrina do teste. **Nada afrouxado, nenhum xfail→skip, nenhum assert de guarda removido; ZERO knob**
  (`config.yaml`/`calibracao.lock.yaml` intactos; 3 graus). **2 golden_nivel de `g`
  (`test_growth_reconciliacao`, tagged "→ Fase 11 (GROW)") quebram como CONSEQUÊNCIA do `g_fund` novo —
  NÃO atualizados (contrato v2.4: golden de nível é DELETADO pela fase que corrige o método, nunca
  atualizado); a lógica de teto/trava está intocada, é o nível da fixture que mudou. Golden ITUB4=32,88
  segue vivo (10-04).** Suíte default **477 passed, 1 skipped, 34 deselected, 1 xfailed, 0 failed**.
  Commits: `e6bdb5f` (RED), `10b54fc` (GREEN).

- **PRIM-01 (Fase 10 / plano 10-01) — a base de valuation trocou o `median()`-do-meio pelo ENDPOINT
  de tendência robusta (Theil-Sen).** `normalizacao.base_normalizada` deixou de devolver o ano-do-meio
  (que punia crescimento com o haircut fechado `−g/(1+g)` = −9,1% em g=10%) e passa a devolver o valor
  da regressão robusta (`scipy.stats.theilslopes`) AVALIADO NO ANO ATUAL — reflete o crescimento recente,
  robusto a 1 exercício atípico; ladder curta (vazio→None, N=1→valor, N=2→média) + GUARD
  `endpoint<=0 → median(janela)` (nunca base negativa a jusante do RIM/DCF). **Split do estimador
  (decisão estrutural, RESEARCH §Estimator split):** os dois consumidores de `base_normalizada` querem
  estimadores OPOSTOS — a base de valuation (3a) quer o endpoint; o motor cíclico (10a) quer a MÉDIA
  through-cycle (CSNA3: endpoint = −891M vs média = +1.270M). Criada `norm.media_ciclo` (a média/mediana
  antiga) e o ramo `"normalizado"` de `report.py` repontado para ela — o cíclico NÃO recebe o endpoint.
  **BLIND-03 curado:** removido o `xfail` de `test_normalizacao_nao_pune_crescimento` (vira invariante
  normal; nunca skip, nunca afrouxado). **Checkpoint de decisão (janela 3 vs 5, resolvido pelo usuário):
  janela=5** — com 3 pontos a regressão persegue um pico terminal, com 5 ela o separa da tendência;
  co-change SANCIONADO `config.yaml:57` + `calibracao.lock.yaml:194` (`anos_media: 3→5`) no MESMO commit
  com trailer `Knob-Change-Justification:` sem ticker. **Orçamento intacto: 3 graus** (ERP, n_fade,
  PIB_real) — Theil-Sen é parameter-free. **2º checkpoint (Option A, resolvido pelo usuário):** 4 testes
  a jusante quebraram (não previstos pela RESEARCH break-table) — 2 `invariante` que codificavam a mediana
  antiga (reescritos para a invariância do endpoint, mais fortes) e 2 `contrato` Core Value cross-modo
  (a igualdade cross-menu preservada; a fixture de coerência de direção RECALIBRADA pela própria doutrina
  escrita do teste, com as 3 asserts intactas). **Nada afrouxado, nenhum xfail→skip, nenhum assert de
  guarda removido; golden ITUB4=32,88 NÃO tocado (é do 10-04).** Suíte default **472 passed, 1 skipped,
  34 deselected, 1 xfailed, 0 failed** (sobra BLIND-02b→Fase 12 e o skip do jackknife→Fase 14). Commits:
  `8b983ae` (RED), `4301f10` (GREEN).

- **DATA-06 (Fase 9 / plano 09-05) — a régua ENXERGA o progresso + o invariante virou um RATCHET
  honesto.** O snapshot LIMPO novo (`scripts/capturar_snapshot_limpo.py`, produto do código
  consertado) desacopla a medição de "hoje" da régua (baseline sujo) e da evidência (snapshot sujo);
  `_pares_e_buckets_de_hoje` lê o limpo → a monotonicidade deixa de ser tautologia sujo-vs-sujo e
  ENCOLHE (os 9 alvos DATA-01/02/03 somem, ticker a ticker; `test_os_alvos_consertados_sumiram_de_hoje`).
  **A régua expôs um bug real do DATA-03 (09-02):** a escala do `composicao_capital` era aplicada por
  SÉRIE (fator do último ano), deixando o ÷1000 preso nos anos de escala divergente (o `composicao`
  troca MILHARES↔UNIDADES entre anos do mesmo ticker). **Escopo expandido/autorizado p/ `build.py`:**
  `_escala_por_ano` (âncora `implied` por ano; some 8 SAN-02 espúrios em PETR4/BBDC4/VIVT3/RENT3/…) +
  `_alinhar_escala_interna` (sem âncora: ELET3/ELET6/IGTI11, infere a unidade da própria série).
  Variação real (<1000×) preservada; anomalia não-potência-de-1000 fica visível (IGTI11 reorg 2021;
  CMIN3 2025 = 10× erro no arquivo da CVM). **Ratchet reformulado (aprovado):** subconjunto puro era
  impossível p/ uma cura que troca a fonte → `pares_hoje ⊆ (baseline ∪ pares_aceitos)` e
  `buckets_hoje ⊆ baseline` (+ `buckets_aceitos`), com accept-list VERSIONADA (`pares_aceitos_sanidade.yaml`:
  9 pares + 2 buckets, motivos por categoria, sem ticker+número — BLIND-04a-safe). **Provado RED-able
  por execução:** par sujo não-documentado e bucket novo não-documentado deixam a suíte vermelha (a
  accept-list NÃO é regeneração silenciosa do baseline). `snapshot_bancos` **não** regenerado (Fase 10).
  **Zero motor/knob/config** (`config.yaml`/`calibracao.lock.yaml` intactos; 3 graus). Suíte default
  **467 passed, 1 skipped, 34 deselected, 2 xfailed, 0 failed**; `-m ""` 500 passed; `-m golden_nivel`
  34 passed, 0 CLASSIFICACAO ORFA. Sujo/baseline intactos. **Checkpoint de decisão (Rule 4) ×2 +
  1 desvio de premissa** resolvidos pelo usuário: expansão de escopo p/ build.py (bug de escala) e
  reformulação do invariante (ratchet + bucket-accept); IGTI11·SAN-02 aceito (reorg real, não escala).

- **DATA-05 (Fase 9 / plano 09-04) — o DY passa a DECLARAR sua base: é BRUTO, sem calcular imposto.**
  `header_dy` (help nos DOIS caminhos, recorrente e fallback) e o glossário (verbete `dy` + bloco
  `tab_multiplos`) declaram que o DY é bruto (proventos brutos sobre o preço; IR sobre dividendos/JCP
  **não** descontado). Decisão travada (09-RESEARCH Open Question 4 / A2): **NÃO** aplicar IRRF
  especulativo da Lei 15.270/2025 (não verificada juridicamente) — declarar "bruto" satisfaz o
  requisito sem cravar alíquota/vigência frágeis. **Zero motor/knob/cálculo:** `multiples.dividend_yield`,
  `config.yaml` e `calibracao.lock.yaml` (3 graus) **INTOCADOS** (scope check `git diff` VAZIO). Teste
  de contrato `tests/test_dy_base.py` (3 asserts, string "bruto", BLIND-04a limpo) + 3 entradas
  `contrato` em `classificacao.yaml` no MESMO commit. Suíte default **465 passed, 1 skipped, 34
  deselected, 2 xfailed, 0 failed**. Sem checkpoint (mudança de rótulo aditiva; nenhum teste diagnóstico
  invalidado, ao contrário de 09-01/09-02).

- **DATA-04 (Fase 9 / plano 09-03) — o degrau artificial de ~13% do ITUB4 NÃO existe mais na série
  por-ação de valuation (MEDIDO, não suposto).** A ref do requisito (`prices.py:71-111`) é OBSOLETA
  (Fases 3-4 reescreveram o módulo); o site REAL do split é `prices._ajustar_por_split` (`prices.py:93-133`),
  que alimenta só `dm.ohlc_ajustado` (candle `report.py:682` + indicadores) — **nunca cruzado com
  `num_acoes`**. Os dois ingredientes do double-count EXISTEM (spike): `num_acoes` 2024→2025 = **1,1311×**
  (bonificação real, degrau legítimo único) e o Yahoo `.splits` registra a mesma bonif. como 1,1 × 1,03 =
  **1,133** (o "~13%"). Mas ficam em **trilhos separados**: firewall das Fases 3-4 (`serie_precos` = Close
  nominal) + `num_acoes` oficial por ano do 09-02. **Conserto = guarda de regressão, SEM edição de produção**
  (o plano previu esse desfecho): `tests/test_ingest_split.py` (3 `invariante` adimensionais, ticker
  sintético `BON3` — BLIND-04a limpo) trava a ausência do degrau e é **RED-able provado por execução**
  (regressão simulada `serie_precos = _ajustar_por_split(...)` → 3 asserts vermelhos). **Zero motor/knob/
  config** (`config.yaml`/`calibracao.lock.yaml` intactos; 3 graus). Suíte default **462 passed, 1 skipped,
  2 xfailed, 0 failed**; `-m golden_nivel` **34 passed, 0 CLASSIFICACAO ORFA**. Sem checkpoint (mudança
  aditiva; nenhum teste diagnóstico existente invalidado, ao contrário de 09-01/09-02).

- **DATA-03 (Fase 9 / plano 09-02) — `num_acoes` deixa de ser `LL/LPA` e passa à contagem OFICIAL
  da CVM.** `cvm.contagem_oficial_do_ano` lê `composicao_capital` (ON+PN em circulação =
  `QT_ACAO_TOTAL_CAP_INTEGR − QT_ACAO_TOTAL_TESOURO`), join CNPJ→CD_CVM via `cad_cia_aberta.csv`
  (armadilha 2). No `build`, a **escala** (milhares×unidades — armadilha 3 / Pitfall 4) é detectada
  cruzando a contagem do último ano com o `impliedSharesOutstanding` e arredondada à potência de 1000,
  aplicada à série; **fallback** = `impliedSharesOutstanding` (ON+PN), NUNCA `sharesOutstanding`
  (armadilha 1); `_fator_unit` refeito sobre a contagem oficial (**ALUP11 = 3, não 5** — Pitfall 5).
  **Medido:** ITUB4 2019 = 1,10e10 (bilhões, não milhões); GOAU4 SAN-01 1,0015 (era 2,969×); CGRA4
  0,925 (era 0,001×); BRSR6 1,0000. `composicao_capital` só existe a partir de ~2020 → anos antigos
  caem no `implied` (fronteira de origem cvm↔fallback isenta o par no SAN-02, sem salto ÷1000).
  **Zero motor/knob/config** (`config.yaml`/`calibracao.lock.yaml` intactos; 3 graus). Suíte **default
  459 passed, 1 skipped, 2 xfailed, 0 failed**; `-m golden_nivel` 34 passed, 0 CLASSIFICACAO ORFA.
  **Checkpoint de decisão (Rule 4, resolvido pelo usuário — Option B):** dois stubs de
  `test_cvm_distribuicoes` (`test_build_cai_para_yahoo…` `invariante` e `test_build_prefere…`
  `golden_nivel`) populavam `num_acoes` por `LL/LPA` e quebravam com a fonte trocada; foram
  **completados com `implied_shares_outstanding`** (nova fonte de fallback), **sem alterar valor
  asserido**. `test_ingest_unit.py` (4 goldens que asseriam `num_acoes == LL/LPA`, o método removido)
  foi **DELETADO** + suas 4 entradas em `classificacao.yaml`, no mesmo commit — completude da coleta
  preservada (0 órfão). Prova formal ticker-a-ticker (monotonicidade, snapshot limpo) fica no 09-05.

- **DATA-01/02 (Fase 9 / plano 09-01) — insumos limpos da Fase 8 PROMOVIDOS a fonte-de-verdade.**
  `cvm.fundamentos_do_ano` aponta `dividendos_distribuidos` para `_distribuicoes_proventos_amplo`
  (dividendo OU JCP): `c.dividendos` captura o JCP — **BRSR6 amplo/estreito = 5,43×**; os 4 grandes
  bancos (ITUB4/BBDC4/BBAS3) **amplo == estreito (ratio 1,0)**, sem contagem em dobro (T-09-01
  medido). `montar_empresa` decide lucro E PL por um **gate ÚNICO** em `lucro_controlador`: com
  controlador → `LL = controlador` e `PL = consolidado − minoritários` (juntos); sem controlador →
  ambos no consolidado (fallback) e minoritários NÃO subtraídos, mesmo com `pl_nao_controladores`
  presente (Pitfall 3 — nunca base cruzada). **Zero motor/knob/config tocado** (`config.yaml`/
  `calibracao.lock.yaml` intactos; 3 graus). Suíte **459 passed, 1 skipped, 38 deselected, 2 xfailed,
  0 failed**. **Checkpoint de decisão (Rule 4, resolvido pelo usuário — Option A):** dois testes-
  diagnóstico da Fase 8 (`test_o_filtro_estreito_da_cvm_perde_o_jcp`,
  `test_montar_empresa_carimba_o_lucro_do_controlador`, `contrato`) rodam o pipeline LIVE e
  asseriam a doença via `c.dividendos`/`c.lucro_liquido`; o conserto os invalidava. Foram
  **re-apontados aos insumos CRUS** (filtro estreito vs amplo direto no DFC; `lucro_controlador` vs
  consolidado bruto) + novos invariantes do conserto — **sem afrouxar, sem deletar, sem mexer em
  `classificacao.yaml`** (nomes mantidos; diff-scope de teste expandido e autorizado). CSNA3 muda de
  sinal no lucro (controlador em prejuízo) — conserto funcionando, visível quando o snapshot limpo
  for regenerado (09-05). Prova formal ticker-a-ticker (monotonicidade) fica no plano 09-05.

- **SAN Wave 3 (Fase 8 / plano 08-04) — os 5 checks aritméticos viram código.** `core/sanidade.py`
  (funções puras, espelho de `normalizacao.py`, zero I/O, zero dependência nova) entrega SAN-01
  (escala `num_acoes×preço≈market_cap`), SAN-02 (salto temporal simétrico 3×, isenção por split D-12,
  fronteira de fonte), SAN-03 (DOIS sinais: detector direto de JCP perdido interno à CVM + reconciliação
  CVM↔Yahoo que **reporta divergência sem eleger verdade**), SAN-04 (base dos minoritários, `sinal_invertido`
  do CSNA3) e SAN-05 (clean surplus como DADO). Os limiares (D-10) são **constantes de módulo**, fora do
  `config.yaml` e do `calibracao.lock.yaml` (limiar de detecção **não é knob de valuation** — o lock segue
  com 3 graus) e congelados por teste `invariante` (D-11). `_bucket` é string e **nunca levanta** com fator
  ≤ 0. **NADA conserta nada** — os asserts SÃO o teste de regressão da Fase 9 (`git diff src/analista/ingest/`
  vazio). **DESVIOS MEDIDOS (o check funcionando, não bug):** (1) o **BBAS3 flaga SAN-04** — o LL consolidado
  do BB supera o do controlador em ~22% (minoritário REAL de subsidiárias consolidadas), então saiu da lista
  "bancos limpos" do teste (ITUB4/BBDC4/BRSR6); a premissa do plano era a % de minoritário no **PL** (2,3%),
  não no lucro. (2) A **ALUP11 flaga SAN-01** no snapshot congelado (0,586×), além do SAN-04 — sem quebrar
  teste (nenhum assert exige ALUP11 limpa no SAN-01). Suíte: **450 passed, 1 skipped, 38 deselected, 2 xfailed,
  0 failed**. SAN-05 marcado completo (SAN-01..04 já vinham dos planos 08-01/08-03).

- **SAN Wave 2 (Fase 8 / plano 08-03) — o snapshot congelado dos 104 é a evidência intocada do dado
  SUJO.** `tests/fixtures/snapshot_sanidade_2026-07-14.yaml` (104 tickers, 13.756 linhas) congela
  **`market_cap` E `splits`, não só o preço** — o EQTL3 (a 0,5% do limiar do SAN-01) não pisca, e os
  12 splits do ITUB4 (incluindo o de **2018**, fora da janela de 5y do `prices.py`) ficam disponíveis
  para a isenção D-12. **Degradação por ticker (SAN-06, never-raise):** **11 tickers dão 404 no Yahoo
  HOJE** (AZUL4, BRFS3, CCRO3, CPLE6, ELET3, ELET6, EMBR3, JBSS3, MRFG3, ODPV3, TRPL4) — congelados
  **com a CVM intacta e sem mercado**, listados no bloco `falhas:`. **NÃO é rate-limit** (verificado:
  Yahoo serve ITUB4/PETR4/WEGE3 na mesma sessão fresca; os 11 falham nos endpoints `info` **E**
  `history` por símbolo; re-rodar reproduz os mesmos 11). Parte são renames/fusões reais
  (BRFS3→MBRF, CCRO3→MOTV3, TRPL4→ISAE4, JBSS3→NYSE, MRFG3→MBRF); ELET3/EMBR3/ODPV3 é quirk do
  `quoteSummary`. **Zero R$ derivado por ticker** (nenhum `intrinseco`/`motor`/`arquetipo`; o
  `report` não é tocado). Loader offline `tests/helpers_sanidade.py` reconstrói `CompanyData` nascendo
  `confianca='nao_avaliada'` (D-03). Suíte: **435 passed, 1 skipped, 38 deselected, 2 xfailed, 0
  failed**. SAN-01/SAN-02/SAN-06 marcados completos.

- **SAN-07 (Fase 8 / plano 08-02) — o TERCEIRO bug de dados NÃO existe (medido, não deduzido).**
  Spike `.planning/spikes/san-07-ihcd-at1-fvoci.md` + `scripts/spike_san07_bancos.py` (offline, do
  cache CVM), nos 4 bancos: **(1) IHCD/AT1 NÃO estão no PL** da DFP da CVM — não há linha de
  instrumento perpétuo/híbrido dentro do bloco do PL (no BRSR6 o subordinado está no **passivo**,
  `2.01.01`); o `B0` que o RIM consome **não está inflado por AT1**. **(2) dirty surplus FVOCI é
  imaterial** — OCI/PL entre **0,03% e 0,59%** (ruído contra o clean surplus). **Premissa do
  requisito estava errada:** `2.03` não é o PL de banco nenhum (é "Passivos ao Custo Amortizado" no
  ITUB4, "Provisões" nos demais); o PL real é **`2.08`** (ITUB4) / **`2.07`** (BBAS3/BBDC4/BRSR6),
  casado pelo **nome** — o parser já estava certo. **Nenhum knob se move** (D-15; Armadilha 3).
  Ressalva honesta registrada: nas DFs IFRS *próprias* do Itaú os AT1 **são** equity — mas a DFP da
  CVM (que este pipeline lê) não os expõe assim. Anomalia declarada: `Ajustes de Avaliação
  Patrimonial` (estoque de OCI) lê 0,00 nos 4 bancos apesar do fluxo não-zero — não muda a
  materialidade. **Também matou dois números fantasma no REQUIREMENTS/ROADMAP:** o "ITUB4 2019 =
  1.131×" (era o salto real 2024→2025 = **1,1286×**, bonificação legítima mal-rotulada; SAN-02 agora
  usa limiar **simétrico** `max(r,1/r) ≥ 3×`) e a conta `2.03`. E registrou para a Fase 9: a
  **direção INVERTIDA do BUG-JCP** no DATA-01 (a **CVM** perde o JCP, 18× no BRSR6; o **Yahoo** o tem
  — a correção é ampliar o filtro, não trocar de fonte) e o **`composicao_capital`** no DATA-03 (com
  as 2 armadilhas: chave por `CNPJ_CIA`, escala inconsistente MILHARES×unidades). Suíte intocada:
  **430 passed, 0 failed**.

- **SAN Wave 0 (Fase 8 / plano 08-01) — insumos de diagnóstico são PARALELOS; leitura ≠ conserto.**
  `cvm.py` lê `3.11.01` (lucro do controlador), minoritários no PL e proventos por **filtro amplo**
  (`dividendo` OU `juros sobre.*capital` — o literal `"juros sobre capital"` não casava "Juros sobre
  **O** Capital Próprio" do BRSR6). `prices.py` lê `marketCap`/`impliedSharesOutstanding`/`splits`.
  `CompanyData` nasce `confianca='nao_avaliada'`. **Nenhum número consumido pelos motores mudou**
  (`num_acoes`/`_fator_unit`/`lpa`/`lucro_liquido`/`dividendos` byte a byte iguais). O comentário
  BUG-JCP de `build.py` estava com a **direção invertida** e foi corrigido: é a **CVM** que perde o
  JCP (18× no BRSR6, medido), o **Yahoo** é que o tem. `_distribuicoes_proventos_amplo` é função
  **separada** (não parâmetro) de propósito — preserva o filtro estreito sujo como teste de regressão
  do DATA-01 (Fase 9). Suíte: **430 passed, 0 failed, 38 deselected, 2 xfailed, 1 skipped**.

- **BLIND-05 (Fase 7 / plano 07-04) — o co-change knob+golden agora é rejeitado pelo git.**
  `.githooks/commit-msg` (versionado, `sh` puro, zero dep) bloqueia `config.yaml` + `tests/(fixtures|test_)`
  no MESMO commit — a assinatura exata do overfit do v2.3. A escapatória é **obrigatória** (2 dos 5
  co-changes históricos são legítimos) e **auditável**: o trailer `Knob-Change-Justification:` fica no
  `git log` para sempre. A regra escrita do ROADMAP (*"uma justificativa legítima de knob nunca menciona
  um ticker"*) virou **executável** — e o candidato da regex é validado contra `ticker_map.json`, porque
  a regex nua casa `MACD12` (que existe no próprio `config.yaml`).

- **⚠️ `core.hooksPath` é estado LOCAL, por clone.** É o único item da Fase 7 que **não vive em arquivo
  versionado**: todo `git clone` novo nasce **SEM** a proteção do BLIND-05. Rode
  `git config core.hooksPath .githooks`. O `test_hook_do_blind05_esta_instalado` deixa a suíte
  **vermelha** se ela sumir — sem ele, é proteção fantasma. O `--no-verify` tem backstop próprio:
  `test_historico_do_v24_sem_co_change_knob_e_golden` varre `955e73d..HEAD` (este repo **não tem CI**).

- **São duas doenças independentes, não uma calibração.** **Doença 1 — VIÉS (erro de unidade):** `Ke`
  nominal (rf = Selic-ciclo 9,58%, embute ~5,2pp de inflação) contra `g_estavel` de 2,5% **real** — o
  modelo trata inflação como destruição de valor, impondo teto de P/L = `1/(Ke−g)` = **7,8x** contra
  P/L mediano de mercado de **9,9x**. É o único parâmetro que os 4 motores compartilham.
  **Doença 2 — DISPERSÃO (dados):** `num_acoes = lucro/LPA` com bases cruzadas (`build.py:87`) quebra
  a escala em **41 dos 104 tickers**; JCP perdido em 13 empresas (`cvm.py:169`); split ajustado duas
  vezes (`prices.py:71-111`); zero reconciliação. Não move a mediana — move cada ticker de −48% a +193%.

- **A ordem das 8 fases é obrigatória** (provada por simulação, não deduzida). A separação `g`/`Ke` é
  a única que *parece* redundante e **não é** — é a regra dura A.

- **O contrato de saída já é o do livro — não inventar outro.** O PDF foi lido em 2026-07-13:
  "preço-teto" = **0 ocorrências**, "Bazin" = **0**, "valor intrínseco" = **39**. O livro prescreve
  valor intrínseco + região de valor + tríade `SUBAVALIADA / NO INTERVALO / SOBREAVALIADA` (Cap. 17),
  **MS simétrica escolhida pelo usuário** (*"se 5%, 10% ou qualquer outro valor, é você quem decide"*)
  e a **matriz de sensibilidade Ke×g** (*"a que mais gostamos"*). Sai só o que nunca veio do livro:
  `"Evitar"` e `"Qualidade Baixa"`. **Descartados:** preço-teto à la Bazin, viés binário
  Comprar/Aguardar, MS escalonada da Morningstar.

- **Sob clean surplus (Ohlson 1995), RIM ≡ DDM ≡ DCF-equity** — logo os 4 motores **não são 4
  opiniões: são 4 implementações do mesmo modelo com inputs inconsistentes**, e a dispersão
  (0,81/0,63/0,63/0,48) **é a assinatura dos bugs**. O ensemble (ENS-01) estava **medindo os próprios
  bugs do projeto** e chamando isso de "divergência de método" — morre junto (Fase 13). O
  classificador **sobrevive e melhora**: deixa de escolher um *modelo* (erro ilimitado) e passa a
  escolher uma *âncora de ROE* (erro limitado).

- **A MS morre como armadilha por construção** — sendo escolha explícita do usuário, ela não pode ser
  calibrada para maquiar resultado (Armadilha 4).

- **Nenhuma dependência nova.** Único componente novo: `macro.ipca_ciclo(anos=10)` (BCB SGS 13522,
  **mesma janela do `rf`** — é essa simetria que torna o valuation invariante à inflação).
  `pandera`/`great-expectations` **rejeitados** (peso/indireção para 4 asserts aritméticos; custo zero).

### As cinco armadilhas (com os números que as provam)

1. **Remover `ke_teto: 0.13` antes de consertar o `g`** → ITUB4 0,75→0,64; BBDC4 0,71→**0,52**. O clamp
   é indefensável (a justificativa "Blume" do `config.yaml:235` é *aritmeticamente falsa* — Blume daria
   15,9%, não 13%) **mas é uma muleta que compensa o viés do `g`**. → Fase 12, **nunca antes**.

2. **"Consertar" `dcf_crescimento` com FCFE (`lpa × payout`)** → vira DDM (teorema, não bug).
   WEGE3 0,58 → **0,26**. → proibido na Fase 13.

3. **Reajustar knobs quando o golden `ITUB4: 32.88 ± 0.20` quebrar.** Ele **VAI** quebrar e **isso é o
   conserto funcionando** — critério de saída da Fase 10, não regressão. **Deletar, não atualizar.**
   Regra escrita: *"uma justificativa legítima de knob nunca menciona um ticker"* (compare
   `config.yaml:237` — "Move ITUB4 ~R$2").

4. **A margem de segurança virar o novo `ke_teto`.** Se calibrada até os resultados ficarem bonitos, é
   o post-mortem do v2.3 num endereço novo. **Neutralizada pelo livro:** MS é do usuário.

5. **O conserto do `g` cria a própria fragilidade.** Com `g` = 7,28%, o spread `Ke−g` cai de 10,5pp
   para ~5,5pp e **o peso do valor terminal quase DOBRA**. `excesso_sustentavel` e `ke_g_spread_min`,
   hoje decorativos, viram **load-bearing**. → prever na Fase 11, não descobrir depois.

### Pending Todos

- **Suspeita aberta (spike SAN-07, Fase 8, ANTES de calibrar qualquer coisa):** clean surplus violado
  em bancos (IFRS 9 FVOCI: marcação a mercado vai direto ao PL) → `B0` deprimido → **o RIM subvaloriza
  o banco de qualidade** — que é *exatamente o sintoma que o v2.3 combateu com knobs*. Se confirmado, os
  knobs mascaravam um **terceiro bug de dados**. Idem IHCD/AT1 dentro do PL (`2.03`). Correção sem knob:
  usar o **resultado abrangente** (DRA).

- **Research flags** (podem exigir `/gsd-research-phase` no planejamento fino): prazo remanescente `T`
  das concessões (Fase 13, não confirmado como disponível de graça); escolha de `ROE_T` terminal
  (through-cycle vs. histórico vs. setorial — a premissa que mais move o valor terminal); viabilidade
  de PIT real (Fase 14 — decidir **na Fase 13**, não descobrir na 14).

- **Backlog v2.1 (polish de UX) — deferido.** Achados 6–18 do review de 2026-07-10.

### Blockers/Concerns

- **A suíte de testes atual é decorativa e não constrange mais o modelo.** 448 testes ficam verdes
  sobre um snapshot em que o **ITUB4 tem 10 milhões de ações em 2019**. ~150 deles são goldens de um
  método errado. **Isso é o que a Fase 7 existe para consertar — e nenhuma outra fase pode começar
  antes dela.**

- **O repo contém a instrução escrita de cometer a Armadilha 3.** `config.yaml:237` ("Move ITUB4 ~R$2")
  e `config.yaml:258` ("NÃO mexer... mudariam o ITUB4"). O executor vai encontrar isso e vai ser tentado.

- **Firewall selo↛report:** `selo.py` NÃO importa `report.py` — preservar ao refatorar a Fase 13.
- **Consistência cross-modo:** métodos canônicos `*_valuation()` em `fundamentals.py` são fonte única —
  mexer neles reverbera nos 3 modos (Analisar/Garimpo/Ranking). É o Core Value.

### Quick Tasks Completed

| # | Description | Date | Commit |
|---|-------------|------|--------|
| 260712-p6r | Freio do Ranking no Streamlit (paridade CLI↔UI) | 2026-07-12 | f9ace2d |
| 260713-hoo | Card intrínseco lidera com o motor primário (ITUB4 → "RIM R$ 32,88") | 2026-07-13 | 9897bd9 |

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Engine | Motor `nav`/SOTP real para holdings (ITSA4/B3SA3 caem em RIM de banco por hard-route de setor) | v2.5+ | 2026-07-13 |
| Engine | Score BSD por arquétipo (`cobertura_juros` é a constante 50 para todo o universo) | v2.5+ | 2026-07-13 |
| Engine | Deflator no `dpa_recorrente` e nas séries longas de dividendo | v2.5+ | 2026-07-13 |
| Docs | DDM-DOC-01 (docstring/teste de t em ddm.py) | v2+ | 2026-06-04 |
| UI | NF-e: link da nota emitida na página "Minha conta" | v2.1 | 2026-07-09 |
| Quick tasks | 4 quick-tasks obsoletas da era v1.x | missing | 2026-07-12 |

## Session Continuity

Last session: 2026-07-17T23:53:09.781Z
Stopped at: Phase 13 context gathered
Resume file: .planning/phases/13-motores-contrato-de-sa-da-eng/13-CONTEXT.md

## Operator Next Steps

- Aprovar o roadmap e rodar `/gsd-plan-phase 7` — **Blindagem processual**. Ela **não move nenhum
  número**; ela redefine o que "suíte verde" significa. É a única fase que pode começar.

- **NÃO pular para a Fase 11/12** ("é só trocar o `g` e o `Ke`") — foi exatamente essa a tentação que
  produziu o v2.3.
