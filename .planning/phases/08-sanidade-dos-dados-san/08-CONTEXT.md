# Phase 08: Sanidade dos dados (SAN) - Context

**Gathered:** 2026-07-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Fazer o pipeline **saber quando o dado está errado**. Sete checks (SAN-01..07) que **detectam e
reportam** — e **não consertam nada**.

Os asserts vêm antes dos consertos de propósito: eles **são** o teste de regressão da Fase 9.
Precisam existir, falhar e **ser vistos falhando** antes que qualquer dado seja corrigido — senão
a Fase 9 não tem como provar, ticker a ticker, que o conserto funcionou.

**Fora de escopo (do ROADMAP, inegociável):**
- **NÃO consertar nenhum dado** — consertar aqui destrói o teste de regressão da Fase 9.
- **NÃO calibrar nada com base no spike SAN-07** — o spike responde uma pergunta contábil, não move
  um knob (Armadilha 3).
- **NÃO instalar `pandera` / `great-expectations`** — peso e indireção para 4 asserts aritméticos,
  num projeto cujo constraint é custo zero.

</domain>

<decisions>
## Implementation Decisions

### Onde o diagnóstico mora

- **D-01:** Os avisos viram **campos no `CompanyData`** (`src/analista/core/fundamentals.py:20`):
  `c.avisos` (lista de flags disparadas) + `c.confianca` (síntese). O objeto que já atravessa
  ingest → motores → app carrega o próprio diagnóstico junto; a Fase 13 (contrato de saída) herda
  pronto, sem costura.
- **D-02:** Quem popula é uma **função explícita `aplicar_sanidade(c)`** — a lógica dos 7 checks
  vive isolada e testável, e **não** roda automaticamente dentro de `montar_empresa`.
- **D-03:** O default de `c.confianca` é **`nao_avaliada`**, nunca `alta`. Um `CompanyData`
  construído à mão (teste, snapshot) **não pode nascer parecendo limpo** sem ter sido auditado.
- **D-04:** Como D-02 abre a porta para o esquecimento silencioso (ninguém chama `aplicar_sanidade`
  → o app roda liso e cego), a chamada é **provada por execução**: um teste roda o pipeline real de
  ponta a ponta e exige que a saída **não** esteja `nao_avaliada`. Remover a chamada fica vermelho
  na hora. Mesma filosofia do BLIND: guarda que não é exercitada é guarda fantasma.

### O baseline dos sujos (o núcleo — é o teste de regressão da Fase 9)

- **D-05:** Um **baseline versionado** congela, por ticker, **quais flags disparam hoje** — nunca um
  R$, nunca um preço. Não é golden de nível; é golden de **detecção**. (O meta-teste do BLIND-04a
  proíbe `ticker == R$`; um mapa `ticker → flag` não viola isso, e o desenho precisa deixar essa
  distinção óbvia para o próximo leitor.)
- **D-06:** Vale a **regra da monotonicidade**: a lista de sujos só pode **encolher**. O conserto da
  Fase 9 remove entradas; uma regressão que ressuscite uma flag fica vermelha. Progresso
  **mensurável** (41 sujos → 0), não declarado — e, crucialmente, isso mata o reflexo de "atualizar
  o baseline", que é o mesmo reflexo que produziu o overfit do v2.3.
- **D-07:** O baseline registra **flag + ordem de grandeza (bucket)**, não a magnitude exata.
  Ex.: `GOAU4: [SAN-01: fator ~1e0..1e1]`, `CGRA4: [SAN-01: fator ~1e3]`. Um re-download do Yahoo
  mexendo no terceiro decimal **não** pode deixar o teste vermelho (teste que pisca sem motivo é
  teste que será desinstalado) — mas **silenciar a flag sem corrigir a escala** tem que quebrar.
- **D-08:** O baseline e os checks rodam sobre um **snapshot congelado dos 104 tickers, capturado
  nesta fase com o dado SUJO do jeito que ele está**, e versionado. Determinístico e offline —
  teste que chama a rede não é teste. Esse snapshot é a **evidência intocada** contra a qual a Fase
  9 mede o conserto. (O snapshot de bancos que existe hoje, `scripts/capturar_snapshot_bancos.py`,
  **não serve**: cobre só bancos, e GOAU4/CGRA4/CSNA3/MRFG3/ALUP11/EQTL3 — que o ROADMAP nomeia como
  alvos obrigatórios — ficariam de fora. O ROADMAP da Fase 9 já prevê que esse snapshot antigo seja
  regenerado, porque ele hoje dá verde **contendo** a doença: ITUB4 a 10 milhões de ações.)

### Limiares de detecção

- **D-09:** Limiares **folgados**. SAN-01 (`num_acoes × preço ≈ market cap`) dispara com desvio
  **> 50%** (fator ≥ 1,5×). Os bugs conhecidos são escandalosos — GOAU4 3×, CGRA4 1000×, ITUB4 2019
  1.131×, BRSR6 205.000× — e um limiar folgado pega **todos** com folga, deixando o ruído normal
  (market cap defasado do Yahoo, free float vs total, preço intraday) abaixo da linha. **Falso
  positivo desinstala a guarda tão rápido quanto o furo a inutiliza**: a guarda só grita quando há
  doença de verdade, e por isso sobrevive.
- **D-10:** Os limiares são **constantes no módulo de sanidade** — **não** vão para `config.yaml`
  (longe dos knobs) e **não** entram no `calibracao.lock.yaml`. Limiar de detecção **não é knob de
  valuation**: não move `Ke`, `g` nem preço. O lock tem exatamente 3 graus de liberdade (`ERP`,
  `n_fade`, `PIB_real`); um 4º deixaria a suíte vermelha por construção, e colocar limiar lá
  confundiria as duas coisas.
- **D-11:** Um teste **congela os valores dos limiares**. Afrouxar um limiar tem que ficar
  **vermelho** e ser encarado no diff — porque afrouxar o limiar até a flag calar é o atalho mais
  tentador da Fase 9, e é um diff de uma linha que ninguém nota.
- **D-12:** SAN-02 (salto de `num_acoes` ano-a-ano **sem evento societário**) usa **limiar alto +
  os `.splits` do Yahoo como isenção**: o salto acima do limiar dispara, mas se o `yfinance`
  registra um desdobramento naquele ano com fator compatível, a flag é isenta. Pega ITUB4 (1.131×) e
  BRSR6 (205.000×) sem acusar quem apenas desdobrou. Se o `.splits` faltar, o falso positivo é
  **visível** (flag levantada), não silencioso — falha na direção segura.

### Forma do veredito e visibilidade

- **D-13:** `c.confianca` é uma **escala discreta**: `alta` / `media` / `baixa` / `nao_avaliada`.
  Derivada das flags — sem flag = `alta`; flag leve = `media`; flag grave (escala quebrada) =
  `baixa`; nunca checado = `nao_avaliada` (D-03). **Nada de score numérico 0-100**: inventaria
  precisão que não existe, e todo número por ticker convida a virar knob — exatamente o reflexo que
  o v2.4 está extirpando.
- **D-14:** O veredito é **interno nesta fase**. Nada muda na tela do app. O diagnóstico é consumido
  por teste e por um **relatório CLI** (ferramenta de trabalho para medir o conserto ticker a ticker
  durante a Fase 9). A apresentação ao usuário é decidida **uma vez, na Fase 13** (contrato de
  saída), com o dado já consertado pela Fase 9.
  **Razão de negócio:** o app está no ar e vendido (v2.0). Acender o selo de "baixa confiança" agora
  exporia 41 dos 104 tickers como "dado suspeito" para cliente pagante durante semanas, por um
  problema que será resolvido antes. Detectar não é apresentar — e apresentar aqui invadiria o
  escopo da Fase 13.

### SAN-07 (spike contábil)

- **D-15:** Entregável = **documento escrito em `.planning/spikes/` + a medição que sustenta a
  resposta**. O doc responde por escrito: IHCD/AT1 entram no PL dos bancos (conta `2.03`)? O dirty
  surplus por IFRS 9 FVOCI é material? A resposta vem acompanhada da **medição nos dados reais dos
  bancos** (quanto do PL é AT1, qual o tamanho do FVOCI) — porque "é material?" é uma pergunta
  **quantitativa**, e sem medir a resposta é palpite informado, e a Fase 9 herdaria a dúvida.
  **Nenhum knob é movido pelo spike.** A conclusão (o 3º bug de dados existe ou não) é o que a Fase
  9 consome.

### Claude's Discretion

- Nome e localização exatos do módulo de sanidade, formato de serialização do baseline e do snapshot,
  e a estrutura interna do objeto de aviso (desde que respeitem D-01..D-15).
- Os limiares específicos de SAN-02..SAN-05 (o de SAN-01 está fixado em >50% por D-09) — devem seguir
  o princípio de D-09: folgados o bastante para zero falso positivo, apertados o bastante para pegar
  os tickers que o ROADMAP nomeia.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contrato do marco (o que não pode ser violado)
- `CLAUDE.md` — a definição de "suíte verde" do v2.4; a regra "golden de nível quebrou? DELETE, não
  atualize"; a proibição de mencionar ticker em justificativa de knob.
- `calibracao.lock.yaml` — os **3** graus de liberdade (`ERP`, `n_fade`, `PIB_real`). Limiar de
  detecção **não entra aqui** (D-10).
- `.planning/ROADMAP.md` §"Phase 8: Sanidade dos dados (SAN)" — goal, 5 critérios de sucesso e a
  lista "NÃO fazer nesta fase".
- `.planning/REQUIREMENTS.md` §SAN-01..SAN-07 (linhas 84-95) — os 7 requisitos, com os tickers-alvo
  nomeados.

### Herança da Fase 7 (blindagem)
- `.planning/phases/07-blindagem-processual-blind/07-VERIFICATION.md` — o que a blindagem garante, e
  o **gap WR-04 ainda ABERTO**: 21 funções em quarentena carregam invariantes estruturais presos;
  19 continuam por cindir. **Obrigatório antes da Fase 10**, não desta — mas quem planejar a Fase 8
  precisa saber que existe.
- `tests/classificacao.yaml` — todo teste novo desta fase precisa de entrada aqui, senão **quebra a
  coleta** (`CLASSIFICACAO ORFA`).
- `.githooks/commit-msg` — o hook do BLIND-05. `core.hooksPath` é estado local por clone.

### Código que a fase toca
- `src/analista/ingest/build.py:40` (`montar_empresa`) — onde `num_acoes` nasce de `LL / LPA`; a
  origem dos 41 tickers de escala quebrada. Já documenta BUG-UNIT (linha 91) e BUG-JCP (linha 104).
- `src/analista/core/fundamentals.py:20` (`CompanyData`) — o dataclass que ganha `c.avisos` e
  `c.confianca` (D-01). **Hoje não tem nenhum campo de aviso ou confiança.**
- `scripts/capturar_snapshot_bancos.py` — o snapshot atual, **insuficiente** (só bancos) e
  **contaminado** (verde com ITUB4 a 10 milhões de ações). Serve de referência de forma, não de
  conteúdo (D-08).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/capturar_snapshot_bancos.py`: o padrão de captura/congelamento de snapshot já existe —
  reaproveitar a **forma** para capturar os 104 tickers sujos (D-08).
- `ingest/prices.py` (`coletar_mercado`): já traz `num_acoes` (Yahoo `sharesOutstanding`), preço e
  beta — os insumos de SAN-01. O `.splits` do `yfinance` (D-12) sai da mesma fonte.
- `ingest/cvm.py` (`fundamentos_do_ano`): já traz `lucro_liquido`, `patrimonio_liquido`, `lpa` e
  `dividendos_distribuidos` — os insumos de SAN-03, SAN-04 e SAN-05.

### Established Patterns
- **Contrato never-raise (SAN-06):** existe hoje como *prática* (o ingest degrada em vez de
  levantar), mas **não como estrutura** — não há campo de aviso nem de confiança. Esta fase o torna
  estrutural. Nenhum dos 7 checks pode levantar exceção: rodar a engine num ticker sujo continua
  produzindo resposta.
- **Guarda provada por execução:** a Fase 7 estabeleceu que suíte verde não é evidência de blindagem
  — rodar a evasão é. Daí D-04 e D-11.
- **Nada de golden de nível:** nenhum artefato desta fase pode estampar um R$ por ticker (D-05/D-07).

### Integration Points
- `montar_empresa` (`ingest/build.py:40`) é o ponto onde o pipeline real chama `aplicar_sanidade(c)`
  — e é o que o teste de D-04 exercita de ponta a ponta.
- Os motores (`core/motores.py`) e o app (`app.py`) **leem** `c.confianca` mas **não a exibem** nesta
  fase (D-14).

</code_context>

<specifics>
## Specific Ideas

- Os tickers que a fase **tem que** pegar, nomeados pelo ROADMAP — é por eles que o baseline será
  julgado: escala quebrada (**GOAU4** 3×, **CGRA4** 1000×), salto ano-a-ano (**ITUB4** 2019 1.131×,
  **BRSR6** 205.000×), base `PL`×`lucro` divergente (**MRFG3**, **CSNA3**, **ALUP11**, **EQTL3**), e
  o JCP perdido (bancos).
- O **clean surplus** (`ΔB ≈ LL − DIV`, SAN-05) é reportado **como dado, não como exceção**: é
  simultaneamente detector de bug **e** pré-condição de validade do RIM.

</specifics>

<deferred>
## Deferred Ideas

- **Exibir o selo de confiança na tela** — Fase 13 (contrato de saída), com o dado já consertado
  (D-14).
- **Cindir as 19 funções mistas restantes (gap WR-04)** — obrigatório **antes da Fase 10**, não é
  escopo da Fase 8. Registrado em `07-VERIFICATION.md`.

</deferred>

---

*Phase: 08-sanidade-dos-dados-san*
*Context gathered: 2026-07-14*
