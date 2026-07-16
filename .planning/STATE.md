---
gsd_state_version: 1.0
milestone: v2.4
milestone_name: Fidelidade do Valuation
status: executing
stopped_at: Phase 10 context gathered
last_updated: "2026-07-16T12:20:29.552Z"
last_activity: 2026-07-16
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 20
  completed_plans: 19
  percent: 95
---

# Project State

## Project Reference

See: .planning/PROJECT.md · .planning/REQUIREMENTS.md · .planning/research/SUMMARY.md

**Core value:** Os números que o app mostra precisam ser **fiéis ao método do livro e consistentes
entre si** — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.

**Critério de aceite soberano do marco v2.4:** o app reproduz o **caso-exemplo do próprio livro** —
ITUB4, Cap. 17 (Tabelas 41/43): `g` = 10,24% · `Ke` = 12,48% → **V = R$ 37,22** (região R$ 35–39,
MS ±5%). **Hoje o app entrega R$ 16,13.**

**Current focus:** Phase 10 — primitivas-sem-vi-s-prim

## Current Position

Milestone: v2.4 — Fidelidade do Valuation (Phases 7–14)
Phase: 10 (primitivas-sem-vi-s-prim) — EXECUTING
Plan: 4 of 4
Status: Ready to execute
Last activity: 2026-07-16

Progress: [██████████] 95%

**Suíte:** `483 passed, 1 skipped, 34 deselected, 1 xfailed` — 0 XPASS. **BLIND-03 curado no 10-01**
(virou invariante normal). Sobra **1 xfailed** = BLIND-02b (vira verde na Fase 12) e **1 skipped** =
jackknife (Fase 14). Golden de nível que quebrar deve ser **DELETADO, nunca atualizado** (contrato do
CLAUDE.md) — o golden ITUB4=32,88 ainda vive: sua deleção é o critério de saída do plano **10-04** (PRIM-05).

**⚠ DÍVIDA OBRIGATÓRIA ANTES DA FASE 10 (gap WR-04):** 21 das 38 funções quarentenadas carregam
invariantes estruturais presos (`a.motor == 'rim'`, contratos de roteamento, reetiquetagem SAN-01).
Já não rodam. A Fase 10 deleta esses goldens — os invariantes morreriam junto, em silêncio.
Cindir as funções mistas antes. Fila de triagem e varredor AST: `07-VERIFICATION.md` (apêndice).

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

## Accumulated Context

### Decisions (v2.4)

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

Last session: 2026-07-16T12:19:45.788Z
Stopped at: Phase 10 context gathered
Resume file: None

## Operator Next Steps

- Aprovar o roadmap e rodar `/gsd-plan-phase 7` — **Blindagem processual**. Ela **não move nenhum
  número**; ela redefine o que "suíte verde" significa. É a única fase que pode começar.

- **NÃO pular para a Fase 11/12** ("é só trocar o `g` e o `Ke`") — foi exatamente essa a tentação que
  produziu o v2.3.
