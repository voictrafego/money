# Requirements — v2.4 Fidelidade do Valuation

**Milestone goal:** Fazer os números do app servirem de **guia real de decisão**. Hoje ele
subvaloriza quase toda a B3 (mediana intrínseco/preço do motor exibido: **0,68**) e carimba "caro"
em 4 de cada 5 ações. Corrigir as **duas doenças independentes** na única ordem que a simulação
provou segura.

> ## Critério de aceite soberano
>
> **O app reproduz o caso-exemplo do próprio livro.** ITUB4, Cap. 17 (Tabelas 41 e 43):
> `g` = 10,24% · `Ke` = 12,48% → **`V` = R$ 37,22** (região R$ 35 – R$ 39, MS ±5%).
> **Hoje o app entrega R$ 16,13 para o mesmo ativo.**
>
> O `g` do livro é praticamente o `g` por fundamentos que o app **calcula e descarta** (10,29%),
> adotando o histórico de 6,94%. O Core Value do projeto é fidelidade ao método — e o app falha no
> caso-teste do próprio método. Qualquer requisito abaixo que conflite com o livro **perde**.
> _(O PDF foi lido diretamente em 2026-07-13. "preço-teto": 0 ocorrências. "Bazin": 0. "valor
> intrínseco": 39.)_

**Diagnóstico (auditoria forense de 2026-07-13 — 5 agentes, 104 tickers, engine ao vivo):**

- **Doença 1 — VIÉS (erro de unidade).** `Ke` é **nominal** (rf = Selic-ciclo 9,58%); `g_estavel` é
  **2,5% de PIB real**. O modelo trata inflação como destruição de valor. Teto de P/L = `1/(Ke−g)`
  = **7,8x** contra P/L mediano de mercado de **9,9x** → o motor é *matematicamente incapaz* de
  justificar a ação mediana da bolsa. Único parâmetro que os **quatro** motores compartilham.
- **Doença 2 — DISPERSÃO (dados).** `num_acoes` com escala quebrada em **41 dos 104 tickers**; JCP
  perdido em 13 empresas; split ajustado duas vezes; **zero reconciliação** no pipeline.

Mapa completo: https://claude.ai/code/artifact/cfdb3a4f-fffe-4465-b98a-bf3e9d4aa679

---

## Blindagem processual (BLIND) — precede tudo

Sem isto, os consertos das fases seguintes são revertidos por um knob e ninguém nota. É a lição
direta do post-mortem do v2.3.

- [x] **BLIND-01**: Os 448 testes estão classificados num arquivo commitado em três categorias —
  **INVARIANTE** (verdade algébrica que knob nenhum satisfaz), **GOLDEN-DE-NÍVEL** (trava um número,
  logo trava o método atual) e **CONTRATO** (formato/borda). Os GOLDEN-DE-NÍVEL entram em quarentena
  em vez de bloquear o marco.
- [x] **BLIND-02**: Existem **dois** testes de **invariância à inflação**, e o choque é aplicado a
  **`rf`, `g_cap` E `ROE` simultaneamente** (+300 bps):
  - **(a) invariante algébrico** sobre a identidade fechada `P/B justo = 1 + (ROE−Ke)/(Ke−g)` —
    exato (< 1e-9), knob-proof, **passa hoje**; guarda a ponte auditável do ENG-08.
  - **(b) o `xfail(strict=True)`** — choque completo na **engine**, limiar **5%**. Ele **é a Doença 1
    escrita como código** e vira verde sozinho na **Fase 12**.

  **Por que o `ROE` entra no choque** (medido, 2026-07-13): chocar só `rf` e `g_cap` derruba `V` em
  **−27,67%** *mesmo com o `Ke`/`g` exatos do livro e zero clamps* — o choque preserva `(Ke−g)` mas
  **comprime `(ROE−Ke)`** em exatamente δ. Inflação levanta o **lucro nominal**, não só a taxa de
  desconto; um `ROE` congelado no snapshot é um `ROE` **real** comparado com um `Ke` **nominal** — ou
  seja, **é a própria Doença 1 uma camada abaixo**. A spec original era insatisfazível por álgebra.

  **Por que 5% e não 2%**: com `n_fade = 10` o resíduo estrutural da janela explícita é **−4,68%**
  (a perpetuidade é exatamente invariante; a janela finita não é) — os 2% eram **inalcançáveis** sem
  amarrar o `n_fade`, que é 1 dos 3 graus de liberdade. Isto **não é afrouxar tolerância** (Pitfall
  5): é fixar um limiar alcançável **na primeira escrita**, com a medição na mão. O proibido é mexer
  no limiar **depois** que o teste fica vermelho.

  **Por que Fase 12 e não 11**: até a Fase 12 o `ke_teto = 0,13` **satura** sob o choque — o `Ke` não
  se move 1 bp e o `V` **sobe**. A perna do `rf` só passa a existir quando o clamp sai. A **regra dura
  (A)** (não fundir 11 e 12) continua válida: ela é sobre a **ordem do conserto**, provada por
  simulação, não sobre onde um teste fica verde.

  ⚠️ **NÃO escrever este teste sobre BBDC4** — ele passa hoje **por acidente** (+1,96%) e daria XPASS
  → suíte vermelha na hora.
- [x] **BLIND-03**: Existe teste de que a normalização **não pune crescimento** — série de lucro de
  +10%/ano *pura* (zero outlier) não pode produzir base normalizada abaixo do último ano menos
  inflação. Hoje produz haircut medido de **−9,1%**.
- [x] **BLIND-04**: **Nenhum teste de calibração afirma `ticker == valor em reais`.** A validação é
  por **distribuição** (mediana + IQR) mais **jackknife**: `test_nenhum_ticker_e_load_bearing` falha
  se remover um único ticker mover a mediana além do limiar.
- [x] **BLIND-05**: Um hook de pre-commit **bloqueia** commit que altere `config.yaml` e um
  golden/fixture ao mesmo tempo — é a assinatura exata de "calibrei o knob até o teste passar".
- [x] **BLIND-06**: Orçamento de knobs explícito e travado por teste: **exatamente 3 graus de
  liberdade** (`ERP`, `n_fade`, `PIB_real`). Regra escrita: *"uma justificativa legítima de knob
  nunca menciona um ticker"* — compare `config.yaml:237` ("Move ITUB4 ~R$2").

## Sanidade dos dados (SAN)

Os asserts vêm **antes** dos consertos, de propósito: eles **são** o teste de regressão do bloco DATA.

- [ ] **SAN-01**: A ingestão reconcilia `num_acoes × preço ≈ market cap` e rebaixa a confiança do
  ticker quando diverge. Pega GOAU4 (3× errado) e CGRA4 (escala de 1000×).
- [ ] **SAN-02**: Detecta salto de `num_acoes` ano-a-ano sem evento societário. Pega ITUB4 2019
  (1.131×) e BRSR6 (205.000×).
- [ ] **SAN-03**: Reconcilia `dividendos_CVM ≈ DPA_yahoo × num_acoes`. Pega o JCP perdido.
- [ ] **SAN-04**: Verifica que `PL` e `lucro` estão na **mesma base**. Pega MRFG3, CSNA3, ALUP11, EQTL3.
- [ ] **SAN-05**: Verifica **clean surplus** (`ΔB ≈ LL − DIV`) e reporta a violação como **dado**, não
  exceção. É detector de bug **e** pré-condição de validade do RIM — o mais valioso dos asserts.
- [ ] **SAN-06**: Nenhum assert levanta exceção — todos degradam para aviso + confiança rebaixada
  (contrato `never-raise` que o ingest já tem).
- [ ] **SAN-07**: *(spike, ANTES de calibrar qualquer coisa)* Verificar se IHCD/AT1 entram no PL dos
  bancos (`2.03`) e se o dirty surplus por IFRS 9 FVOCI é material. Se for, `B0` está deprimido e o
  RIM subvaloriza banco de qualidade — **um terceiro bug de dados que os knobs do v2.3 mascaravam**.

## Ingestão correta (DATA)

- [ ] **DATA-01**: JCP capturado nas 13 empresas que hoje o perdem (`cvm.py:169` filtra só
  "dividendo"). BRSR6 sai de payout 10,3% para 55,9%.
- [ ] **DATA-02**: `lucro` e `PL` usam a base do **controlador**, não o consolidado com minoritários.
- [ ] **DATA-03**: `num_acoes` deixa de ser derivado de `lucro/LPA` com bases cruzadas
  (`build.py:87`); o fallback usa `impliedSharesOutstanding` (ON+PN), não `sharesOutstanding` (só a
  classe).
- [ ] **DATA-04**: O duplo ajuste de split é removido (`prices.py:71-111` — o `Close` do Yahoo já vem
  ajustado; a engine **cria** um degrau artificial de 13% no ITUB4).
- [ ] **DATA-05**: O DY reflete o **IRRF de 17,5% sobre JCP** (Lei 15.270/2025, desde 01/01/2026) ou
  declara explicitamente que é bruto.
- [ ] **DATA-06**: O snapshot de teste é regenerado — o atual tem ITUB4 com **10 milhões de ações** em
  2019 e dá verde nos 448 testes.

## Primitivas sem viés (PRIM)

Maior alavancagem por linha do repositório: atinge todos os motores, todos os múltiplos, todas as telas.

- [ ] **PRIM-01**: A base de lucro do valuation deixa de descartar o ano mais recente
  (`normalizacao.py:73-75`: `anos_media=3` cai em `median()` de 3 = **o ano do meio**).
- [ ] **PRIM-02**: `roe_valuation` deixa de cruzar bases temporais (lucro de 2023 ÷ PL de 2024). Passa
  a ser a **mediana da série de ROEs anuais**. ITUB4: 16,1% → 18,0%.
- [ ] **PRIM-03**: A winsorização não é aplicada a série **temporal** — ela clampa a tendência e
  **ressuscita ano de prejuízo**, fabricando `g` de 36% (VULC3) e 47% (CYRE3), exibidos no app.
- [ ] **PRIM-04**: A base do motor cíclico é **deflacionada** (hoje soma reais de 2015 com reais de
  2024; IPCA acumulado de 58%; CSNA3 sai 31,8% subvalorizada só por isso).
- [ ] **PRIM-05**: **CRITÉRIO DE SAÍDA — o golden `ITUB4: 32.88 ± 0.20` QUEBRA e é DELETADO, não
  atualizado.** Atualizar mantém vivo o reflexo que causou o overfit. Vai parecer errado no momento;
  é o conserto funcionando.

## Crescimento (GROW)

- [ ] **GROW-01**: `g_cap` é derivado, não digitado: `(1 + π_ciclo) × (1 + PIB_real) − 1` = **7,28%**
  (π_ciclo = 5,18%, IPCA médio 10a, BCB SGS 13522 — medido).
- [ ] **GROW-02**: A janela do IPCA é **a mesma** do `rf`. É isso que torna o valuation invariante à
  inflação. **BLIND-02 NÃO vira verde aqui** — vira na **Fase 12**, quando o `ke_teto` (que satura
  sob o choque e absorve a perna do `rf`) é removido. Esta fase entrega a **metade `g`** da cura;
  esperar o teste verde aqui faria o executor "consertar" o teste em vez do código.
- [ ] **GROW-03**: `g_T = min(ROE_T × retenção, g_cap)` — identidade fechada, não constante.
- [ ] **GROW-04**: O `g` da fase explícita é reconciliado com o **livro**, que usa o `g` por
  fundamentos (10,24% no Itaú) — o app calcula 10,29% e **descarta**, adotando o histórico de 6,94%.
- [ ] **GROW-05**: A **Armadilha 5 é endereçada aqui**: com `g` = 7,28%, o spread `Ke − g` cai de
  10,5 pp para ~5,5 pp e **o peso do valor terminal quase dobra**. `excesso_sustentavel` e
  `ke_g_spread_min`, hoje decorativos, viram load-bearing. Prever, não descobrir depois.

## Custo de capital (KE)

**Bloco separado do GROW de propósito.** Fundir dá um número e zero diagnóstico — e a Armadilha 1
prova que a ordem importa: consertar o `Ke` antes do `g` **piora** (ITUB4 0,75 → 0,64).

- [ ] **KE-01**: Um único `Ke` no sistema. Hoje há dois simultâneos (17,3% no DDM, 13,0% no RIM) e **o
  que produz o número da manchete nunca é exibido**.
- [ ] **KE-02**: ERP de 4,5% (Damodaran mature market), **sem** o prêmio small-cap de 1,5% —
  injustificável num universo filtrado por liquidez de R$ 15M/dia.
- [ ] **KE-03**: Beta **setorial + Blume** (`0,33 + 0,67 × β`), não individual bruto. BB e Bradesco têm
  o mesmo risco de negócio e hoje recebem `Ke` com 1,7 pp de diferença — ruído que produz **2,7× de
  espalhamento** no valor final.
- [ ] **KE-04**: `ke_piso` e `ke_teto` são **removidos**. Com `Ke_min` = 11,07% (piso estrutural do
  Blume) > `g_cap` = 7,28%, nenhuma perpetuidade pode explodir — **por aritmética, não por clamp**.
  (O `config.yaml:235` justifica o teto com "Blume" e isso é *aritmeticamente falso*: Blume daria 15,9%.)
- [ ] **KE-05**: O `Ke` exibido é **o mesmo** que produziu o número exibido, e a matriz de
  sensibilidade é construída em torno dele.

## Motores e contrato de saída (ENG)

- [ ] **ENG-01**: Um único motor de valor (**RIM**). Sob clean surplus, os 4 motores não são 4
  opiniões — são **4 implementações do mesmo modelo com inputs inconsistentes**. A dispersão
  (0,81/0,63/0,63/0,48) é a assinatura dos bugs.
- [ ] **ENG-02**: O **ensemble morre junto** — ele mede os próprios bugs do projeto e chama isso de
  "divergência de método". Idem `_guarda_san01` e `_guarda_faixa_ddm`: são **cicatrizes do viés, não
  features**. Removidos, não portados.
- [ ] **ENG-03**: O classificador de arquétipo **sobrevive e melhora** — deixa de escolher um *modelo*
  (erro ilimitado) e passa a escolher uma *âncora de ROE* (erro limitado).
- [ ] **ENG-04**: `PAGADORA_REGULADA` é separada em `PAGADORA_MADURA` + `CONCESSAO_FINITA`. Hoje ela é
  **também o default por eliminação** (`arquetipo.py:176`) — empresa sem sinal cai no balde da
  transmissora. E transmissoras sob ICPC 01 usam **modelo de ativo financeiro**: o book **já é** o VP
  da RAP e o ROE dispara em ano de IPCA alto → consertar o `g` causaria **double-count de inflação**.
- [ ] **ENG-05**: **O contrato de saída é o do livro** — valor intrínseco + **região de valor** +
  tríade **SUBAVALIADA / NO INTERVALO / SOBREAVALIADA**. Sai apenas o que nunca veio do livro:
  **"Evitar"** e **"Qualidade Baixa"**.
- [ ] **ENG-06**: A **margem de segurança é controle do usuário**, simétrica, default 5-10%
  (*"se 5%, 10% ou qualquer outro valor, é você quem decide"* — Cap. 17). **Nunca calibrada** contra
  dispersão, preço ou taxa de "compra" — é assim que a Armadilha 4 morre por construção.
- [ ] **ENG-07**: A **matriz de sensibilidade `Ke × g` vive** — o livro a chama de *"a que mais
  gostamos"*, é a estratégia **preferida** dele para a região de valor. Construída sobre `Ke` e `g`
  **corretos**.
- [ ] **ENG-08**: A **ponte auditável** é exibida: `P/B justo = 1 + (ROE_T − Ke)/(Ke − g)` × VPA = `V`,
  com o **payout terminal implícito** (`payout_T = 1 − g/ROE_T`). É um **teste de correção**, não
  decoração: payout terminal negativo ou > 100% **é bug** e vira assert.
- [ ] **ENG-09**: Guarda-corpo sobre a **razão implícita**, não sobre o resultado: `0 < P/B justo < 6`.
  (O RIM **não** impede sozinho o CGRA4 a 921× — `VPA = PL/num_acoes` infla junto e o motor herda o
  erro 1:1, com P/B justo de 1,4×.)
- [ ] **ENG-10**: O bloco `motores:` do `config.yaml` vai de **~20 chaves para ≤ 5**. A deleção é
  **contada** — senão não acontece.
- [ ] **ENG-11**: O Ranking é **rebaixado e re-rotulado**, não deletado (deletar jogaria fora os
  Cap. 11-12 do livro). Vira **screener comparativo por múltiplos**; as colunas
  preço-alvo/upside/veredito saem. A regressão de pares é *matematicamente cega ao nível de preço*:
  multiplicando o preço de todas as elétricas por 1,5, os upsides saem **bit a bit idênticos**.

## Validação (VAL)

- [ ] **VAL-01**: **O caso do livro passa.** ITUB4 com os inputs do Cap. 17 reproduz `V` ≈ R$ 37,22.
  Critério de aceite soberano do marco.
- [ ] **VAL-02**: Cesta estratificada (≥ 6 por arquétipo + **10 "difíceis" deliberados**: P/B < 1,
  prejuízo recente, payout > 100%, book pequeno). Sem os difíceis, valida-se só o meio da
  distribuição — que é onde o modelo já funcionava.
- [ ] **VAL-03**: Fair values **commitados ANTES** de rodar o modelo. O `git log` prova a ordem.
  Hoje não prova.
- [ ] **VAL-04**: Hold-out roda **uma única vez**. Se falhar, **re-arquiteta-se — não recalibra**.
- [ ] **VAL-05**: A métrica é `V/FairValue`, **nunca** `V/preço`. Um modelo com mediana `V/preço` = 1,00
  é um espelho do mercado e não serve para nada.
- [ ] **VAL-06**: **Nenhuma regra de exceção pode salvar um ticker.** O `excecao_nota` do v2.3 é uma
  *lavanderia de overfit*: com quórum 3/4 + "exceção documentada passa", **o gate não pode reprovar**.
  (Recontagem: o v2.3 gastou **~8 graus de liberdade sobre 4 observações**, e o "4/4 PASS" real é
  **2/4** — BBAS3 e BBDC4 estão fora do consenso e passam só pelo acolchoamento de ±15%.)
- [ ] **VAL-07**: Backtest temporal **só com point-in-time real** (a DFP de 2022 só existiu em
  mar/2023). **Se não der para fazer PIT direito, NÃO fazer** — um backtest ingênuo produz um número
  confiante e falso, pior que nenhum.

---

## Future Requirements (deferidos)

- **Motor `nav`/SOTP real para holdings.** ITSA4 e B3SA3 hoje caem em RIM de banco por hard-route de
  setor. A afirmação "`nav` é o 1º termo do RIM" é **meia-verdade** — vale para o NAV contábil e é
  falsa justamente para holdings (participações por equivalência patrimonial, não a mercado).
- **Score BSD por arquétipo.** Hoje `cobertura_juros` é a constante 50 para **todo** o universo
  (`despesa_juros` nunca é ingerido), e FCO de banco é captação, não qualidade de lucro. 20% do peso
  do selo é placeholder ou ruído — e o selo do ITUB4 é decidido por 0,63 ponto.
- **Deflator no `dpa_recorrente`** e nas séries longas de dividendo.

## Out of Scope (com razão)

- **Preço-teto à la Bazin** — **não é o método do livro** (zero ocorrências no PDF). Se um teto
  existir, é derivado do `V` (`V × (1 − MS)`), nunca substituto dele.
- **Margem de segurança escalonada por incerteza (Morningstar)** — o livro tem regra própria (MS
  simétrica, escolhida pelo usuário) e ela tem **precedência** por fidelidade ao método.
- **Viés binário Comprar/Aguardar** — destrói a categoria "valor justo", que o livro tem.
- **Bibliotecas de validação de dados** (`pandera`, `great-expectations`) — peso e indireção para 4
  asserts aritméticos, num projeto cujo constraint declarado é custo zero.
- **Provedor pago de dados** — viola o posicionamento do produto.

---

## Traceability

**Cobertura: 52/52 requisitos mapeados (100%). Zero órfãos. Zero duplicatas.**
Cada requisito pertence a **exatamente uma** fase. A ordem das fases (7→14) é obrigatória e foi
provada por simulação sobre os 104 tickers — ver `.planning/ROADMAP.md`.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BLIND-01 | Phase 7 | Complete |
| BLIND-02 | Phase 7 | Complete |
| BLIND-03 | Phase 7 | Complete |
| BLIND-04 | Phase 7 | Complete |
| BLIND-05 | Phase 7 | Complete |
| BLIND-06 | Phase 7 | Complete |
| SAN-01 | Phase 8 | Pending |
| SAN-02 | Phase 8 | Pending |
| SAN-03 | Phase 8 | Pending |
| SAN-04 | Phase 8 | Pending |
| SAN-05 | Phase 8 | Pending |
| SAN-06 | Phase 8 | Pending |
| SAN-07 | Phase 8 | Pending |
| DATA-01 | Phase 9 | Pending |
| DATA-02 | Phase 9 | Pending |
| DATA-03 | Phase 9 | Pending |
| DATA-04 | Phase 9 | Pending |
| DATA-05 | Phase 9 | Pending |
| DATA-06 | Phase 9 | Pending |
| PRIM-01 | Phase 10 | Pending |
| PRIM-02 | Phase 10 | Pending |
| PRIM-03 | Phase 10 | Pending |
| PRIM-04 | Phase 10 | Pending |
| PRIM-05 | Phase 10 | Pending |
| GROW-01 | Phase 11 | Pending |
| GROW-02 | Phase 11 | Pending |
| GROW-03 | Phase 11 | Pending |
| GROW-04 | Phase 11 | Pending |
| GROW-05 | Phase 11 | Pending |
| KE-01 | Phase 12 | Pending |
| KE-02 | Phase 12 | Pending |
| KE-03 | Phase 12 | Pending |
| KE-04 | Phase 12 | Pending |
| KE-05 | Phase 12 | Pending |
| ENG-01 | Phase 13 | Pending |
| ENG-02 | Phase 13 | Pending |
| ENG-03 | Phase 13 | Pending |
| ENG-04 | Phase 13 | Pending |
| ENG-05 | Phase 13 | Pending |
| ENG-06 | Phase 13 | Pending |
| ENG-07 | Phase 13 | Pending |
| ENG-08 | Phase 13 | Pending |
| ENG-09 | Phase 13 | Pending |
| ENG-10 | Phase 13 | Pending |
| ENG-11 | Phase 13 | Pending |
| VAL-01 | Phase 14 | Pending |
| VAL-02 | Phase 14 | Pending |
| VAL-03 | Phase 14 | Pending |
| VAL-04 | Phase 14 | Pending |
| VAL-05 | Phase 14 | Pending |
| VAL-06 | Phase 14 | Pending |
| VAL-07 | Phase 14 | Pending |

### Resumo por fase

| Fase | Categoria | Requisitos | Qtd | Papel na ordem obrigatória |
|------|-----------|------------|-----|----------------------------|
| 7 | BLIND | BLIND-01..06 | 6 | Redefine "suíte verde" ANTES de tocar código |
| 8 | SAN | SAN-01..07 | 7 | Os asserts SÃO o teste de regressão da Fase 9 |
| 9 | DATA | DATA-01..06 | 6 | Cura a Doença 2 (dispersão); os asserts viram verde |
| 10 | PRIM | PRIM-01..05 | 5 | **Critério de saída: o golden ITUB4 32.88 quebra e é DELETADO** |
| 11 | GROW | GROW-01..05 | 5 | Metade da Doença 1 (o `g`); BLIND-02 **NÃO** vira verde aqui — vira na 12 |
| 12 | KE | KE-01..05 | 5 | **Separada do GROW de propósito** (regra dura A) |
| 13 | ENG | ENG-01..11 | 11 | 4 motores → RIM único; `motores:` ~20 → ≤5 chaves (contado) |
| 14 | VAL | VAL-01..07 | 7 | **Critério soberano: ITUB4 = R$ 37,22 (o caso do livro)** |
