# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 (shipped 2026-06-28)
- ✅ **v1.4–v1.7 — Swing Trade / Modo Trading / Home / Lentes-Selo-Comparador** — Phases 12–21 (shipped 2026-07-04, tag `v1.7`)
- ✅ **v2.0 — Comercialização (Lazari Capital)** — Phases 1–3 (shipped 2026-07-10, produto no ar, E2E pago concluído)
- ✅ **v2.2 — Motor de Valuation por Arquétipo** — Phases 1–3 (shipped 2026-07-12, tag `v2.2`, auditoria passed)
- ✅ **v2.3 — Calibração do Valuation à Realidade** — Phases 4–6 (shipped 2026-07-13, tag `v2.3`, deployado)
- 🚧 **v2.4 — Fidelidade do Valuation** — Phases 7–14 (ativo)

> Marcos concluídos são arquivados em `.planning/milestones/` (roadmap + requisitos + fases por
> marco). Histórico narrado em `.planning/MILESTONES.md`. Marcos major reiniciam a numeração em
> Phase 1; marcos minor (como o v2.3 e o v2.4) continuam a numeração do marco anterior.

---

## v2.3 — Calibração do Valuation à Realidade (SHIPPED 2026-07-13)

Deu ao RIM um valor terminal (perpetuidade de residual income), validou numa cesta de 4 bancos
(quórum 3/4 na banda ±15%) e redeployou o app na VPS. **Post-mortem (auditoria forense de
2026-07-13):** a calibração era um **overfit sobre 4 observações com ~8 graus de liberdade**; o
"4/4 PASS" real é **2/4** (BBAS3 e BBDC4 estão fora do consenso e passam só pelo acolchoamento de
±15%). Os knobs que ela introduziu (`ke_teto`, `roe_terminal_stat`, `excesso_sustentavel`, rota de
seguradora) **mascaram** as duas doenças que o v2.4 corrige na raiz. Fases 4–6 detalhadas em
`.planning/milestones/v2.3-*`.

---

## 🚧 v2.4 — Fidelidade do Valuation (Phases 7–14)

**Milestone Goal:** Fazer os números do app servirem de **guia real de decisão**. Hoje o app
subvaloriza quase toda a B3 (mediana intrínseco/preço do motor exibido: **0,68**) e carimba "caro"
em 4 de cada 5 ações. Corrigir as **duas doenças independentes** na única ordem que a simulação
sobre os 104 tickers provou segura — e provar o conserto no **caso-exemplo do próprio livro**:
ITUB4, Cap. 17, `g` = 10,24% · `Ke` = 12,48% → **V = R$ 37,22** (região R$ 35–39). Hoje entrega
**R$ 16,13**.

### Critério de aceite soberano do marco

> **O app reproduz o caso-exemplo do próprio livro.** ITUB4 (Cap. 17, Tabelas 41/43): `V ≈ R$ 37,22`,
> região R$ 35–39, MS ±5%. Enquanto isso não for verdade, o Core Value do projeto ("fiel ao método
> do livro") está violado **no caso-teste do próprio método**. Aparece como success criterion da
> Fase 14 (VAL-01).

### As duas doenças

- **Doença 1 — VIÉS (erro de unidade, não calibração).** `Ke` é **nominal** (rf = Selic-ciclo 9,58%,
  embute ~5,2pp de inflação) e `ddm.g_estavel` é **2,5% de PIB real**. O modelo trata inflação como
  destruição de valor → teto de P/L = `1/(Ke−g)` = **7,8x** contra P/L mediano de mercado de **9,9x**.
  O motor é *matematicamente incapaz* de justificar a ação mediana da bolsa. Único parâmetro que os
  **quatro** motores compartilham.
- **Doença 2 — DISPERSÃO (dados).** `num_acoes = lucro/LPA` com bases cruzadas (`build.py:87`) quebra
  a escala em **41 dos 104 tickers**; JCP descartado em 13 empresas (`cvm.py:169`); split ajustado
  duas vezes (`prices.py:71-111`); **zero reconciliação** no pipeline. Não move a mediana — move cada
  ticker de −48% a +193%.

## Overview

**A ORDEM DAS FASES É OBRIGATÓRIA E NÃO-NEGOCIÁVEL.** Ela foi **provada por simulação** sobre os 104
tickers, não deduzida. Cada fase depende causalmente do dado/parâmetro corrigido na anterior.
Violá-la piora o modelo:

| Regra dura | Prova |
|---|---|
| **(A) NÃO fundir `g` (Fase 11) com `Ke` (Fase 12)** | Consertar o Ke ANTES do g **piora**: ITUB4 0,75→0,64; BBDC4 0,71→**0,52**. O `ke_teto` é uma **muleta que compensa o viés do `g`**. Ke sozinho é líquido zero (0,68→0,67). Fundir dá **um número e zero diagnóstico**; separar dá **duas medições limpas** contra o mapa de 104 tickers. |
| **(B) O golden `ITUB4: 32.88 ± 0.20` DEVE quebrar e ser DELETADO** | É **critério de saída explícito** da Fase 10 (primitivas), não regressão. Ele foi calibrado para cancelar o haircut de −9,1% da normalização — **dois erros se anulando**. Vai parecer errado no momento em que acontecer; sem isso escrito, o executor "conserta" o teste em vez do código. **Deletar, não atualizar** — atualizar mantém o reflexo vivo. |
| **(C) A deleção de knobs é CONTADA** | O bloco `motores:` do `config.yaml` vai de **~20 chaves para ≤ 5** (Fase 13). Se não for contado, não acontece. Orçamento travado: **exatamente 3 graus de liberdade** (`ERP`, `n_fade`, `PIB_real`). |

**Escopo:** engine inteira — ingestão, primitivas, motores, contrato de saída e validação. **Não é
cirúrgico**, ao contrário do v2.3. ~150 dos 448 testes são goldens de um método errado e serão
quarentenados/deletados; **isso é a correção, não regressão.**

## Phases

- [x] **Phase 7: Blindagem processual (BLIND)** - quarentena dos 38 goldens de nível + invariantes algébricos que knob nenhum satisfaz; redefine o que "suíte verde" significa ANTES de tocar código. **Gap aberto (WR-04): 21 funções quarentenadas carregam invariantes estruturais presos — cindir ANTES da Fase 10, que deleta os goldens e mataria esses invariantes em silêncio.**
- [ ] **Phase 8: Sanidade dos dados (SAN)** - os asserts vêm ANTES dos consertos, de propósito: eles SÃO o teste de regressão da Fase 9
- [ ] **Phase 9: Ingestão correta (DATA)** - JCP, base do controlador, duplo split, `impliedSharesOutstanding`; os asserts da Fase 8 viram verde ticker a ticker
- [ ] **Phase 10: Primitivas sem viés (PRIM)** - maior alavancagem por linha do repo; **critério de saída: o golden ITUB4 32.88 quebra e é DELETADO**
- [ ] **Phase 11: Crescimento / `g` (GROW)** - `g_cap = (1+π_ciclo)(1+PIB_real)−1 = 7,28%`; metade da Doença 1 (o `g`) — o teste de invariância (BLIND-02) só vira verde na Fase 12, quando o `ke_teto` sai
- [ ] **Phase 12: Custo de capital / `Ke` (KE)** - ERP único 4,5%, beta setorial + Blume, `ke_teto`/`ke_piso` deletados; **separada da Fase 11 de propósito**
- [ ] **Phase 13: Motores + contrato de saída (ENG)** - os 4 motores colapsam num RIM único com políticas de input; contrato do livro (tríade + MS do usuário + matriz Ke×g); `motores:` ~20 → ≤5 chaves
- [ ] **Phase 14: Validação honesta (VAL)** - **o caso do livro passa (V ≈ R$ 37,22)**; hold-out roda uma vez, 3 graus de liberdade, distribuição + jackknife

## Phase Details

### Phase 7: Blindagem processual (BLIND)
**Goal**: Redefinir o que "suíte verde" significa **antes de tocar uma linha de código de método**.
Hoje 448 testes ficam verdes sobre um snapshot em que o ITUB4 tem 10 milhões de ações — a suíte é
decorativa e não constrange mais o modelo. Sem esta fase, os consertos das Fases 9–13 são revertidos
por um knob e **ninguém nota** (é a lição literal do post-mortem do v2.3).
**Depends on**: Nothing (primeira fase do marco)
**Requirements**: BLIND-01, BLIND-02, BLIND-03, BLIND-04, BLIND-05, BLIND-06
**Success Criteria** (what must be TRUE):
  1. Um arquivo commitado classifica os 448 testes em **INVARIANTE** / **GOLDEN-DE-NÍVEL** / **CONTRATO**, e os GOLDEN-DE-NÍVEL **não bloqueiam mais o marco** (quarentena) — rodar a suíte deixa de significar "o método atual está preservado".
  2. Existem **dois** testes de **invariância à inflação**, com o choque de **+300 bps** aplicado simultaneamente a **`rf`, `g_cap` E `ROE`**: **(a)** um invariante algébrico sobre `P/B justo = 1 + (ROE−Ke)/(Ke−g)` (exato, knob-proof, passa hoje); **(b)** o `xfail(strict=True)` sobre a **engine**, limiar **5%**, que **falha se passar** — ele **é a Doença 1 escrita como código** e vira verde sozinho na **Fase 12**. **O `ROE` entra no choque porque, sem ele, a spec é insatisfazível por álgebra:** chocar só `rf` e `g_cap` dá **−27,67%** mesmo com o motor perfeito (preserva `(Ke−g)`, mas comprime `(ROE−Ke)`) — inflação levanta o **lucro nominal**, e um `ROE` congelado é a Doença 1 uma camada abaixo. **O limiar é 5% porque `n_fade = 10` impõe um piso estrutural de −4,68%** (a perpetuidade é exatamente invariante; a janela finita não é) — fixar um limiar alcançável **na primeira escrita** não é afrouxar tolerância; afrouxar é mexer nele **depois** que fica vermelho.
  3. Existe um teste que prova que a normalização **pune crescimento hoje**: série de lucro de +10%/ano *pura* (zero outlier) produz base normalizada **abaixo** do último ano menos inflação (haircut medido de −9,1%).
  4. **Nenhum teste de calibração afirma `ticker == valor em reais`** — a validação é por distribuição (mediana + IQR) + `test_nenhum_ticker_e_load_bearing` (jackknife).
  5. Um hook de pre-commit **bloqueia** commit que toque `config.yaml` e um golden/fixture no mesmo commit, e o orçamento de **exatamente 3 graus de liberdade** (`ERP`, `n_fade`, `PIB_real`) está travado por teste.
**NÃO fazer nesta fase**:
  - **NÃO consertar nenhum número.** Esta fase não move `V` de ticker nenhum. Se o intrínseco de alguma ação mudar aqui, algo saiu do escopo.
  - **NÃO "atualizar" golden de nível para o valor novo** — a operação é *quarentenar agora, deletar quando a fase chegar*. Atualizar mantém vivo o reflexo que causou o overfit.
  - **NÃO afrouxar tolerância, marcar `xfail` casual ou deletar assert** para a suíte ficar verde (Pitfall 5 — "o executor conserta o teste em vez do código").
**Plans**: 5 plans (5 waves — serializados: todos escrevem em `tests/classificacao.yaml`)
Plans:
- [x] 07-01-PLAN.md — BLIND-01: quarentena dos goldens (448 testes classificados via YAML + `conftest.py`; zero edição nos testes existentes)
- [x] 07-02-PLAN.md — BLIND-02 + BLIND-03: as duas doenças escritas como código (invariante algébrico exato + 2 `xfail(strict)`)
- [x] 07-03-PLAN.md — BLIND-04: meta-teste AST (`ticker == R$` proibido) + harness do jackknife (veredito adiado p/ a Fase 14)
- [x] 07-04-PLAN.md — BLIND-05: hook versionado (`.githooks/commit-msg` + `core.hooksPath`) + backstop contra `--no-verify`
- [x] 07-05-PLAN.md — BLIND-06: `calibracao.lock.yaml` (3 graus de liberdade) + limpeza dos comentários com ticker + **canário**

### Phase 8: Sanidade dos dados (SAN)
**Goal**: Fazer o pipeline **saber quando o dado está errado**. Os asserts vêm **antes** dos
consertos de propósito: eles **são** o teste de regressão da Fase 9 — precisam existir antes para
provar que o conserto funcionou, ticker a ticker. Inclui o spike que pode revelar um **terceiro bug
de dados** que os knobs do v2.3 mascaravam.
**Depends on**: Phase 7
**Requirements**: SAN-01, SAN-02, SAN-03, SAN-04, SAN-05, SAN-06, SAN-07
**Success Criteria** (what must be TRUE):
  1. A ingestão **reporta os 41 tickers de escala quebrada** hoje invisíveis: `num_acoes × preço ≈ market cap` pega GOAU4 (3×) e CGRA4 (1000×); salto ano-a-ano sem evento societário, com limiar **simétrico** `max(r, 1/r) ≥ 3×`, pega ITUB4 2019 (÷1000) e 2020 (×780), BRSR6 2020/21 (×205.000), CGRA4 2025 (÷1000) — números **medidos** contra o cache CVM (2026-07-14, `08-RESEARCH.md` §Achado 2). *(O salto que antes se atribuía ao ITUB4 2019 era um número fantasma — é o salto real 2024→2025 = 1,1286×, bonificação legítima, mal-rotulado como 2019; um limiar calibrado para ele dispararia em toda bonificação de 10% da B3.)*
  2. A reconciliação `dividendos_CVM ≈ DPA_yahoo × num_acoes` **aponta o JCP perdido** e a checagem de base `PL`×`lucro` **aponta MRFG3, CSNA3, ALUP11, EQTL3** — antes de qualquer conserto.
  3. O **clean surplus** (`ΔB ≈ LL − DIV`) é medido e a violação é reportada **como dado, não como exceção** — é simultaneamente detector de bug **e** pré-condição de validade do RIM.
  4. **Nenhum assert levanta exceção**: todos degradam para aviso + confiança rebaixada do ticker (contrato `never-raise` que o ingest já tem). Rodar a engine num ticker sujo continua produzindo resposta.
  5. O spike SAN-07 responde por escrito (`.planning/spikes/san-07-ihcd-at1-fvoci.md`): IHCD/AT1 entram no PL dos bancos? O dirty surplus por IFRS 9 FVOCI é material? **As duas respostas são NÃO; o terceiro bug de dados não existe; nenhum knob se move.** Correção de premissa: `2.03` **não é o PL de banco nenhum** — o PL é `2.08` (ITUB4) / `2.07` (BBAS3/BBDC4/BRSR6), casado pelo nome "Patrimônio Líquido Consolidado". Não há AT1 dentro do PL (o `B0` do RIM não está inflado) e o OCI fica entre 0,03% e 0,59% do PL — ruído. A Fase 9 herda um "não" fundamentado.
**NÃO fazer nesta fase**:
  - **NÃO consertar nenhum dado.** Consertar aqui destrói o teste de regressão da Fase 9 (os asserts precisam falhar primeiro, e ser *vistos* falhando).
  - **NÃO calibrar nada com base no spike** — o spike responde uma pergunta contábil, não move um knob (Armadilha 3).
  - **NÃO instalar `pandera`/`great-expectations`** — peso e indireção para 4 asserts aritméticos, num projeto cujo constraint é custo zero.
**Plans**: 6 plans (5 waves — a Wave 0 dos insumos precede os checks; o spike roda em paralelo)
Plans:
- [x] 08-01-PLAN.md — Wave 0 dos insumos: `cvm.py` lê `3.11.01` + minoritários; `prices.py` lê `marketCap`/`impliedSharesOutstanding`/`splits`; `CompanyData` ganha `avisos`/`confianca` (default `nao_avaliada`). **Leitura nova, zero conserto.**
- [x] 08-02-PLAN.md — SAN-07: o spike (as duas respostas são **NÃO**; o 3º bug de dados não existe) + correção dos números fantasma no REQUIREMENTS/ROADMAP (o salto fantasma do ITUB4 2019 e a conta `2.03`) + o legado do `composicao_capital` para a Fase 9
- [x] 08-03-PLAN.md — o snapshot congelado dos 104 tickers com o dado **SUJO** (congela `marketCap` e `splits`; degrada por ticker — o MRFG3 dá 404 e **não aborta**)
- [x] 08-04-PLAN.md — `core/sanidade.py`: os 5 checks (SAN-01..05) + os limiares (D-10, fora do lock) + o teste que os congela (D-11)
- [x] 08-05-PLAN.md — `aplicar_sanidade` + agregação da confiança + a chamada no pipeline real **provada por execução** (D-04) + never-raise nos 104 (SAN-06)
- [x] 08-06-PLAN.md — o baseline dos sujos (YAML, flag + bucket, **zero R$**) + a monotonicidade por par `(ticker, check)` (D-06) + o relatório CLI da Fase 9

### Phase 9: Ingestão correta (DATA)
**Goal**: Curar a **Doença 2 (dispersão)**. Os asserts da Fase 8 viram verde ticker a ticker —
progresso mensurável, não declarado. É a fase em que o snapshot de teste (que hoje dá verde nos 448
testes com o ITUB4 a 10 milhões de ações) é regenerado.
**Depends on**: Phase 8
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06
**Success Criteria** (what must be TRUE):
  1. **Os asserts da Fase 8 param de disparar** nos tickers-alvo: JCP capturado nas 13 empresas (BRSR6 sai de payout 10,3% para **55,9%**); `lucro`/`PL` na base do **controlador**; o duplo ajuste de split some (o degrau artificial de **13% no ITUB4** desaparece).
  2. `num_acoes` **deixa de ser derivado** de `lucro/LPA` com bases cruzadas (`build.py:87`); o fallback usa `impliedSharesOutstanding` (ON+PN), não `sharesOutstanding` (só uma classe). Os 41 tickers de escala quebrada caem.
  3. O DY **declara sua base**: reflete o IRRF de 17,5% sobre JCP (Lei 15.270/2025, desde 01/01/2026) ou diz explicitamente que é bruto — não fica ambíguo.
  4. O **snapshot de teste é regenerado** e o novo snapshot **passa nos asserts da Fase 8** — o ITUB4 de 2019 tem bilhões de ações, não milhões.
**NÃO fazer nesta fase**:
  - **NÃO tocar em primitiva, `g`, `Ke` ou motor.** Esta fase move dados de entrada, e só. Misturar conserto de dado com conserto de método torna impossível atribuir a variação de `V` a uma causa.
  - **NÃO "reajustar" um knob porque um número ficou feio depois do conserto de dado** — a variação por ticker (−48% a +193%) é o conserto funcionando.
  - **NÃO comprar dado pago** para resolver a base de ações — viola o custo zero (constraint do produto).
**Plans**: 5 plans (4 waves — serializados pelo compartilhamento de cvm.py/build.py e pela
regra de regressão: DATA-06 mede o progresso só depois dos consertos de dado)
Plans:
- [ ] 09-01-PLAN.md — DATA-01 + DATA-02: JCP capturado (filtro amplo) + base do controlador (lucro E PL juntos), em cvm.py/build.py
- [ ] 09-02-PLAN.md — DATA-03: num_acoes da contagem oficial (composicao_capital + join CNPJ→CD_CVM + escala detectada); _fator_unit refeito
- [ ] 09-03-PLAN.md — DATA-04: spike de localização do degrau de ~13% (ref obsoleta) + conserto do duplo split + teste-guarda
- [ ] 09-04-PLAN.md — DATA-05: DY declara base BRUTA (rótulo + glossário), sem imposto especulativo
- [ ] 09-05-PLAN.md — DATA-06: snapshot limpo novo + loader desacoplado + monotonicidade encolhendo (snapshot_bancos fica p/ Fase 10)

### Phase 10: Primitivas sem viés (PRIM)
**Goal**: **Maior alavancagem por linha do repositório** — as primitivas atingem todos os motores,
todos os múltiplos e todas as telas. `normalizacao.py:73-75` faz `median()` de 3 anos, que é **o ano
do MEIO** (haircut medido de −9,1% num crescedor de 10%); `fundamentals.py:137-150` cruza bases
temporais (lucro de 2023 ÷ PL de 2024). Só faz sentido depois da Fase 9: **sem dado correto,
primitiva correta não significa nada.**
**Depends on**: Phase 9
**Requirements**: PRIM-01, PRIM-02, PRIM-03, PRIM-04, PRIM-05
**Success Criteria** (what must be TRUE):
  1. **O golden `ITUB4: 32.88 ± 0.20` QUEBRA e é DELETADO — este é o CRITÉRIO DE SAÍDA da fase, não uma regressão.** Ele foi calibrado para cancelar o haircut da normalização (dois erros se anulando). Vai parecer errado no momento em que acontecer. **Deletar, não atualizar.** A fase não está concluída enquanto ele existir no repositório.
  2. **O teste BLIND-03 (normalização não pune crescimento) vira verde**: a base de lucro do valuation deixa de descartar o ano mais recente.
  3. `roe_valuation` deixa de cruzar bases temporais e passa a ser a **mediana da série de ROEs anuais** — ITUB4 sai de 16,1% para **18,0%**.
  4. A winsorização **não é mais aplicada à série temporal** — ela clampava a tendência e **ressuscitava ano de prejuízo**, fabricando `g` de **36% (VULC3)** e **47% (CYRE3)** exibidos no app. Esses `g` somem.
  5. A base do motor cíclico é **deflacionada** — hoje soma reais de 2015 com reais de 2024 (IPCA acumulado de 58%); CSNA3 deixa de sair **31,8% subvalorizada só por isso**.
**NÃO fazer nesta fase**:
  - **NÃO atualizar o golden do ITUB4 para o valor novo.** É a Armadilha 3, a mais provável de todas: "atualizar mantém o reflexo vivo". A regra escrita é *"uma justificativa legítima de knob nunca menciona um ticker"* (compare `config.yaml:237` — "Move ITUB4 ~R$2").
  - **NÃO mexer em `g_cap`, `Ke`, `ke_teto` nem em motor.** As primitivas mudam sozinhas; se algo ficar exagerado, é esperado — o `g` e o `Ke` ainda estão errados e serão consertados nas Fases 11 e 12, nessa ordem.
  - **NÃO compensar o novo nível de lucro com nenhum knob** ("o intrínseco subiu demais, vou abaixar X") — é o post-mortem do v2.3 se repetindo.
**Plans**: TBD

### Phase 11: Crescimento / `g` (GROW)
**Goal**: Curar **metade da Doença 1** — a metade que precede o `Ke`. Fechar a identidade do `g`:
`g_cap = (1 + π_ciclo) × (1 + PIB_real) − 1 = **7,28%**`, com π_ciclo (5,18%, IPCA médio 10a, BCB SGS
13522) medido na **mesma janela do `rf`** — é essa simetria de janela, e nada mais, que torna o
valuation invariante à inflação. E reconciliar o `g` da fase explícita com o **livro**, que usa o `g`
por fundamentos (10,24% no Itaú) — o app calcula 10,29% e **descarta**, adotando o histórico de 6,94%.
**Depends on**: Phase 10
**Requirements**: GROW-01, GROW-02, GROW-03, GROW-04, GROW-05
**Success Criteria** (what must be TRUE):
  1. **A metade `g` da Doença 1 está curada, e isso é medível — mas o BLIND-02 ainda NÃO fica verde aqui.** Ele vira verde na **Fase 12**: enquanto o `ke_teto = 0,13` existir, ele **satura** sob o choque de +300 bps, o `Ke` não se move 1 bp, a perna do `rf` é absorvida e o `V` até **sobe**. **Se o BLIND-02 ficar verde nesta fase, algo está errado — investigue, não comemore.** O `xfail(strict=True)` permanece, e será removido na Fase 12 porque o código passou a satisfazê-lo, não porque alguém o afrouxou. **A regra dura (A) continua intacta:** ela é sobre a *ordem do conserto* (provada por simulação), não sobre onde um teste fica verde. O progresso desta fase se mede pelo `g_cap` derivado (7,28%) e pela reconciliação com o livro (critérios 2 e 3), não pelo BLIND-02.
  2. `g_cap` é **derivado, não digitado**: sai de `(1+π_ciclo)(1+PIB_real)−1` com a janela do IPCA igual à do `rf`. `g_T = min(ROE_T × retenção, g_cap)` é identidade fechada, não constante.
  3. O `g` do ITUB4 se **reconcilia com o livro**: o app deixa de descartar o `g` por fundamentos (10,29%) em favor do histórico (6,94%) — o número do livro é 10,24%.
  4. A **Armadilha 5 está endereçada, não descoberta**: com `g` = 7,28% o spread `Ke − g` cai de 10,5pp para ~5,5pp e o **peso do valor terminal quase dobra**. `excesso_sustentavel` e `ke_g_spread_min`, hoje decorativos, foram tratados como **load-bearing** — o comportamento sob spread apertado está coberto por teste.
**NÃO fazer nesta fase**:
  - **NÃO tocar no `Ke`. NÃO remover `ke_teto` nem `ke_piso`. NÃO mexer no ERP nem no beta.** **Regra dura (A).** Consertar o Ke antes do g piora o modelo: ITUB4 0,75→0,64; BBDC4 0,71→**0,52** — porque o `ke_teto` é uma muleta que compensa exatamente o viés do `g` que esta fase remove. O Ke é a Fase 12.
  - **NÃO fundir esta fase com a Fase 12 "para economizar tempo".** A tentação vai ser forte e está errada: fundir dá **um número e zero diagnóstico**; separar dá duas medições limpas contra o mapa de 104 tickers.
  - **NÃO calibrar `PIB_real`** contra resultado — é 1 dos 3 graus de liberdade e é constante estrutural (2,0%), não série ajustável.
**Plans**: TBD

### Phase 12: Custo de capital / `Ke` (KE)
**Goal**: Curar a **outra metade da Doença 1**, e **só agora** — porque tirar o clamp só é seguro
depois do `g`. Hoje há **dois `Ke` simultâneos no sistema** (17,3% no DDM, 13,0% no RIM) e **o que
produz o número da manchete nunca é exibido**. Alvo do livro: `Ke` = 12,48%.
**Depends on**: Phase 11
**Requirements**: KE-01, KE-02, KE-03, KE-04, KE-05
**Success Criteria** (what must be TRUE):
  1. **Existe um único `Ke` no sistema**, e o `Ke` **exibido é o mesmo** que produziu o número exibido — a matriz de sensibilidade é construída em torno dele. Hoje o usuário vê um `Ke` que não é o do cálculo.
  2. `ke_piso` e `ke_teto` **foram removidos do código e do config** e **nada explode**: com `Ke_min` = 11,07% (piso estrutural do Blume) > `g_cap` = 7,28%, nenhuma perpetuidade pode divergir — **por aritmética, não por clamp**. (A justificativa "Blume" do `config.yaml:235` era *aritmeticamente falsa*: Blume daria 15,9%, não 13%.)
  3. O ERP é **4,5%** (Damodaran mature market), **sem** o prêmio small-cap de 1,5% — injustificável num universo já filtrado por liquidez de R$ 15M/dia.
  4. O beta é **setorial + Blume** (`0,33 + 0,67 × β`): BB e Bradesco, que têm o mesmo risco de negócio, param de receber `Ke` com 1,7pp de diferença — **o ruído que produzia 2,7× de espalhamento no valor final some**.
**NÃO fazer nesta fase**:
  - **NÃO reintroduzir um clamp com outro nome** quando algum ticker ficar feio sem o `ke_teto`. Se um valor explodir sem clamp, o bug está em `ROE_T` ou no spread — não no Ke.
  - **NÃO recalibrar o `g` da Fase 11** para "acomodar" o Ke novo. As duas fases são medições independentes; misturá-las apaga o diagnóstico que é o ponto do marco.
  - **NÃO criar prêmio de risco por ticker/setor** para explicar um caso — é grau de liberdade fora do orçamento de 3 (BLIND-06).
**Plans**: TBD

### Phase 13: Motores + contrato de saída (ENG)
**Goal**: Colapsar os 4 motores num **RIM único**. Sob clean surplus (Ohlson 1995), RIM ≡ DDM ≡
DCF-equity — logo os 4 motores **não são 4 opiniões: são 4 implementações do mesmo modelo com inputs
inconsistentes**, e a dispersão medida (0,81/0,63/0,63/0,48) **é a assinatura dos bugs**, não
divergência de método. O classificador de arquétipo **sobrevive e melhora**: deixa de escolher um
*modelo* (erro ilimitado) e passa a escolher uma *âncora de ROE* (erro limitado). E o contrato de
saída é o **do livro** — que o app já tem quase certo e **não deve trocar**.
**Depends on**: Phase 12
**Requirements**: ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, ENG-06, ENG-07, ENG-08, ENG-09, ENG-10, ENG-11
**Success Criteria** (what must be TRUE):
  1. **O bloco `motores:` do `config.yaml` foi de ~20 chaves para ≤ 5 — e a contagem está no critério de verificação.** (Regra dura C: sem número contável, a deleção não acontece.) `dcf_crescimento`, `lucro_normalizado` e `nav_contabil` deixam de ser motores e viram **políticas de input** do RIM.
  2. O **ensemble (ENS-01) morreu**, junto com `_guarda_san01` e `_guarda_faixa_ddm` — **removidos, não portados**. Eles mediam os próprios bugs do projeto e chamavam isso de "divergência de método"; consertadas as doenças, são um segundo erro cancelando o primeiro.
  3. **A ponte auditável é exibida e é um teste de correção**: `P/B justo = 1 + (ROE_T − Ke)/(Ke − g)`, `V = P/B justo × VPA`, com o **payout terminal implícito** `payout_T = 1 − g/ROE_T`. Payout terminal negativo ou > 100% **é bug e falha o teste**. O guarda-corpo é sobre a **razão** (`0 < P/B justo < 6`), não sobre o resultado — o RIM sozinho **não** impede o CGRA4 a 921× (`VPA = PL/num_acoes` infla junto e o motor herda o erro 1:1).
  4. **O contrato de saída é o do livro**: valor intrínseco + região de valor + tríade **SUBAVALIADA / NO INTERVALO / SOBREAVALIADA**; a **margem de segurança é controle do usuário**, simétrica, default 5–10% (*"é você quem decide"*, Cap. 17); a **matriz de sensibilidade Ke×g vive** (*"a que mais gostamos"*), agora sobre `Ke` e `g` corretos. Saem **apenas** `"Evitar"` e `"Qualidade Baixa"` — que nunca vieram do livro.
  5. `PAGADORA_REGULADA` foi separada em `PAGADORA_MADURA` + `CONCESSAO_FINITA` (hoje é **também o default por eliminação**, `arquetipo.py:176` — empresa sem sinal cai no balde da transmissora), e o Ranking foi **rebaixado a screener comparativo por múltiplos** (colunas preço-alvo/upside/veredito saem; a regressão de pares é *matematicamente cega ao nível de preço*) — **não deletado**, porque é o Cap. 11-12 do livro.
**NÃO fazer nesta fase**:
  - **NÃO calibrar a margem de segurança contra dispersão, preço ou taxa de "compra".** **Armadilha 4:** a MS multiplica o `V` — se calibrada até os resultados ficarem bonitos, é o post-mortem do v2.3 num endereço novo. Ela é **escolha do usuário** e morre por construção.
  - **NÃO inventar contrato de saída novo.** "Preço-teto" e "Bazin" têm **ZERO ocorrências** no PDF do livro; "valor intrínseco" tem 39. **Nada de preço-teto à la Bazin, nada de viés binário Comprar/Aguardar** (destrói a categoria "valor justo", que o livro tem), nada de MS escalonada da Morningstar (o livro tem regra própria e ela tem precedência).
  - **NÃO "consertar" o `dcf_crescimento` com FCFE (`lpa × payout`)** — **Armadilha 2:** vira DDM matematicamente (teorema, não bug). WEGE3 0,58 → **0,26**.
  - **NÃO consertar o `g` das transmissoras sob ICPC 01.** Elas usam **modelo de ativo financeiro**: o book **já é** o VP da RAP e o ROE dispara em ano de IPCA alto → corrigir o `g` nelas causa **double-count de inflação**. É o carve-out `CONCESSAO_FINITA`, declarado **antes** do hold-out.
  - **NÃO deletar o Ranking** — rebaixar e re-rotular. Deletar joga fora os Cap. 11-12.
**Plans**: TBD
**UI hint**: yes

### Phase 14: Validação honesta (VAL)
**Goal**: Provar o marco **sem se enganar**. Aqui mora o **critério de aceite soberano**: o app
reproduz o caso-exemplo do próprio livro (ITUB4, Cap. 17 → `V` ≈ **R$ 37,22**, contra os R$ 16,13 de
hoje). Por último, porque **qualquer coisa antes queima o hold-out**. O v2.3 gastou ~8 graus de
liberdade sobre 4 observações e chamou de "4/4 PASS" um resultado que era **2/4**.
**Depends on**: Phase 13
**Requirements**: VAL-01, VAL-02, VAL-03, VAL-04, VAL-05, VAL-06, VAL-07
**Success Criteria** (what must be TRUE):
  1. **O CASO DO LIVRO PASSA — critério de aceite soberano do marco.** ITUB4 com os inputs do Cap. 17 (`g` = 10,24%, `Ke` = 12,48%) reproduz `V` ≈ **R$ 37,22**, região R$ 35–39. Enquanto isso não for verdade, o marco **não está entregue**, independente de qualquer outra métrica.
  2. O hold-out roda numa **cesta estratificada** (≥ 6 por arquétipo + **10 "difíceis" deliberados**: P/B < 1, prejuízo recente, payout > 100%, book pequeno) — sem os difíceis, valida-se só o meio da distribuição, que é onde o modelo já funcionava.
  3. Os fair values estão **commitados ANTES** de rodar o modelo e **o `git log` prova a ordem**; o hold-out roda **uma única vez**; **nenhuma regra de exceção pode salvar um ticker** (o `excecao_nota` do v2.3 é lavanderia de overfit — com quórum 3/4 + "exceção documentada passa", o gate **não pode reprovar**).
  4. A métrica é `V/FairValue`, medida por **distribuição + jackknife** — **nunca** `V/preço` (um modelo com mediana `V/preço` = 1,00 é um espelho do mercado e não serve para nada) e **nunca** assert de `ticker == valor em reais`.
  5. A decisão sobre o backtest temporal está **tomada e escrita**: PIT real (a DFP de 2022 só existiu em mar/2023) **ou não fazer** — um backtest ingênuo produz um número confiante e falso, **pior que nenhum**.
**NÃO fazer nesta fase**:
  - **Se o hold-out falhar, RE-ARQUITETA-SE — NÃO se recalibra.** Esta é a linha que o v2.3 cruzou. Um knob mexido aqui invalida o hold-out inteiro e o marco vira o v2.3 de novo, num endereço novo.
  - **NÃO validar contra consenso de sell-side.** É **circular**: target price é preço com um chapéu, e o preço é exatamente o que está sendo julgado. As âncoras não-circulares são **invariantes algébricos** (grátis) + **centro da seção transversal** (detector de viés, **nunca alvo de calibração**).
  - **NÃO criar carve-out/rota nova depois de ver um ticker falhar** (foi assim que a BBSE3 ganhou uma rota de seguradora no v2.3). Carve-outs são declarados na Fase 13, antes do hold-out. **Zero exceções aqui.**
  - **NÃO alargar a banda de tolerância** para o quórum passar — o "±15% sobre faixas de consenso já largas" do v2.3 dava uma banda efetiva de 2,2–2,6× de largura.
**Plans**: TBD

## Progress

**Execution Order:**
Fases executam em ordem numérica estrita: 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14.
**A ordem é provada por simulação, não é preferência.** Nenhuma fase pode ser antecipada, e as
Fases 11 (`g`) e 12 (`Ke`) **não podem ser fundidas** (regra dura A).

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 7. Blindagem processual (BLIND) | v2.4 | 5/5 | Complete (gap WR-04 aberto) | 2026-07-13 |
| 8. Sanidade dos dados (SAN) | v2.4 | 1/6 | In Progress|  |
| 9. Ingestão correta (DATA) | v2.4 | 0/5 | Planned | - |
| 10. Primitivas sem viés (PRIM) | v2.4 | 0/? | Not started | - |
| 11. Crescimento / g (GROW) | v2.4 | 0/? | Not started | - |
| 12. Custo de capital / Ke (KE) | v2.4 | 0/? | Not started | - |
| 13. Motores + contrato de saída (ENG) | v2.4 | 0/? | Not started | - |
| 14. Validação honesta (VAL) | v2.4 | 0/? | Not started | - |

## Requirement Coverage (v2.4)

**52 requisitos · 8 categorias · 8 fases · cobertura 52/52 (100%), zero órfãos, zero duplicatas.**

| Fase | Categoria | Requisitos | Qtd |
|------|-----------|------------|-----|
| 7 | BLIND | BLIND-01..06 | 6 |
| 8 | SAN | SAN-01..07 | 7 |
| 9 | DATA | DATA-01..06 | 6 |
| 10 | PRIM | PRIM-01..05 | 5 |
| 11 | GROW | GROW-01..05 | 5 |
| 12 | KE | KE-01..05 | 5 |
| 13 | ENG | ENG-01..11 | 11 |
| 14 | VAL | VAL-01..07 | 7 |
