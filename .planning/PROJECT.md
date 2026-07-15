# Analista de Dividendos

## What This Is

Engine Python + app Streamlit que replica o método do livro *O Investidor em Ações de Dividendos*
(Orleans Martins & Felipe Pontes) para analisar ações de dividendos da B3, usando apenas dados
gratuitos (CVM + Yahoo Finance + Banco Central). Voltado ao investidor pessoa física que quer
aplicar o método do livro sem pagar por terminais de dados.

A partir do marco v2.0 o produto é comercializado sob a marca **Lazari Capital** (domínio
*Lazari Tech Capital*): assinatura mensal com trial, front comercial próprio e o engine atrás
de um gate de acesso. Posicionamento: **software educacional, sem recomendação de investimento**.

## Core Value

Os números que o app mostra precisam ser **fiéis ao método do livro e consistentes entre si** —
a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.

## Current State

**v2.0 Comercialização (Lazari Capital) shipped 2026-07-10.** Produto no ar sob a marca Lazari
Capital: Django (auth + Asaas + webhooks nativos) na frente, engine Streamlit atrás de gate
Traefik forward-auth. `www.lazaricapital.com.br` + `app.lazaricapital.com.br`, cutover do
`money.voictech.com.br` (301) concluído. E2E pago (03-05) concluído — smoke real R$19,90 PIX
confirmado ao vivo. Fases v2.0 arquivadas em `.planning/milestones/v2.0-phases/`.

**v2.2 — Motor de Valuation por Arquétipo SHIPPED 2026-07-12 (tag `v2.2`).** Fase 1 (classificador +
roteamento arquétipo→motor), Fase 2 (RIM/lucro normalizado/DCF/NAV plugados no registry) e Fase 3
(veredito honesto: selo consome o motor do arquétipo, ensemble com bandeira de divergência, guarda-corpos
anti-aberração SAN-01, dúvida honesta no caso-fronteira) concluídas e verificadas; 12/12 requisitos.
Auditoria de milestone **passed** — blocker da aba Ranking do Streamlit (paridade de freio CLI↔UI)
fechado por quick task `260712-p6r` antes do arquivamento. Suíte **437 testes verdes**; firewall
selo↛report intacto. Marco arquivado em `.planning/milestones/v2.2-*`.

**Agora: v2.4 Fidelidade do Valuation em andamento. Fase 8 (Sanidade dos Dados / SAN) completa 2026-07-15.**
O pipeline agora **sabe quando o dado está errado**: 5 checks aritméticos (SAN-01..05) + reconciliação
de JCP + clean surplus em `core/sanidade.py`, ligados ao `build.py` e provados por execução (D-04),
sob contrato never-raise (SAN-06). O spike SAN-07 respondeu **NÃO** às duas perguntas contábeis
(IHCD/AT1 fora do PL da CVM; dirty surplus FVOCI imaterial) — o terceiro bug de dados não existe.
Congelado o baseline de regressão dos sujos (62 tickers / 117 pares, flag+bucket, zero R$) que a
Fase 9 leva a zero, ticker a ticker. 7/7 requisitos verificados; suíte 459 verdes. **Nenhum dado
consertado nesta fase** (de propósito — os asserts são o teste de regressão da Fase 9). Próximo:
Fase 9 (Ingestão correta / DATA).

<details>
<summary>Histórico v1.7 (Swing Trade / Modo Trading / Home / Lentes-Selo-Comparador) — shipped 2026-07-04</summary>

**v1.7 shipped 2026-07-04 (tag única `v1.7`, cobrindo v1.4–v1.7).** Oito marcos completos:
v1.0 consistência · v1.1 gráfico · v1.2 timing · v1.3 saneamento do valuation ·
v1.4 Swing Trade (setups de análise técnica, Fases 12–16) · v1.5 Modo Trading (candlestick
estilo TradingView, Fase 17) · v1.6 Home (watchlist + notícias, Fase 18) · v1.7 Lentes de
valuation + Selo DDM + Comparador multi-ativo (Fases 19–21). Suíte **338 testes verdes**;
Fase 21 com smoke visual do 5º menu "Comparar ações" validado. App na VPS (money.voictech.com.br)
— redeploy do v1.7 pendente.

<details>
<summary>Histórico v1.3 (saneamento do valuation) — shipped 2026-06-28</summary>

**v1.3 shipped 2026-06-28.** Suíte 191 testes verdes; app deployado na VPS.

**v1.3 — Saneamento residual do valuation (fases 9–11):** payout sustentável geral (mediana
sem clamp), DY recorrente earnings-based, g histórico log-linear robusto, screening sobre série
normalizada e trava multi-ticker (8/8 requisitos).

**Auditoria online + correção de dados (2026-06-28, mesma sessão, deployado):** a auditoria do
app ao vivo revelou 4/4 ações saindo "sobreavaliada" — 4 bugs de dados/método corrigidos:
(1) **unit XXXX11** (num_acoes na base de units — P/L 3×/5× inflado); (2) **proventos sem JCP**
(payout-mediana vinha pela metade nos bancos — agora div+JCP da DFC da CVM); (3) **Ke usava
Selic spot** → agora Selic through-the-cycle (média 10a); (4) **empresas single-entity** sumiam
(seleção consolidado/individual agora por empresa) + ticker_map ampliado em 60 tickers via FCA.
Mais disclaimer legal (software educacional, não recomendação). Continuação natural do tema v1.3
(fidelidade do valuation para qualquer ticker).

**Marco v2.0 — Comercialização (produto cobrável): DEFINIDO e ADIADO.** Requisitos
(AUTH/BILL/ACCT/LEGAL/OPS) e arquitetura de gateway híbrido já escritos e preservados em
`.planning/milestones/v2.0-REQUIREMENTS.md`. Decisão (2026-06-29): **construir o v1.4 antes** —
agregar valor de produto à ferramenta antes de cobrar. A v2.0 retoma depois.

</details>

</details>

## Current Milestone: v2.4 — Fidelidade do Valuation

**Goal:** Fazer os números do app servirem de **guia real de decisão** — hoje ele subvaloriza quase
toda a B3 e diz "está caro" para 4 de cada 5 ações. Corrigir as **duas doenças independentes** na
única ordem que a simulação provou segura.

**Diagnóstico que originou o marco (auditoria forense de 2026-07-13 — 5 agentes, 104 tickers, engine
ao vivo).** Mediana intrínseco/preço: `rim` 0,81 · `dcf` 0,63 · `normalizado` 0,63 (53 tickers, metade
do universo) · `ddm` 0,48. Motor primário exibido: **0,68**.
Mapa completo: https://claude.ai/code/artifact/cfdb3a4f-fffe-4465-b98a-bf3e9d4aa679

**Doença 1 — VIÉS (erro de unidade, não calibração).** O `Ke` é **nominal** (rf = Selic-ciclo 9,58%,
embutindo ~5,2% de inflação da década) e o `ddm.g_estavel` é **2,5% de PIB real**. O modelo trata
inflação como destruição de valor. Isso impõe um teto de P/L = `1/(Ke−g)` = **7,8x** contra um P/L
mediano de mercado de **9,9x** — o motor é *matematicamente incapaz* de justificar a ação mediana da
bolsa. É o único parâmetro que os **quatro** motores compartilham.

**Doença 2 — DISPERSÃO (dados).** `num_acoes = lucro/LPA` (`build.py:87`) com bases cruzadas (lucro
consolidado ÷ LPA do controlador): **escala quebrada em 41 dos 104 tickers**. CGRA4 → I/P 1.018×;
ITUB4 2019 = 10 milhões de ações em vez de 10 bilhões — dentro do snapshot que dá verde nos 448
testes. JCP descartado em 13 empresas (`cvm.py:169`). Split ajustado duas vezes (`prices.py:71-111`).
**Zero reconciliação** no pipeline. Não move a mediana; move cada ticker de −48% a +193%.

### A ÂNCORA DE VERDADE — o caso-exemplo do próprio livro

Lido direto do PDF (Cap. 17, Tabelas 41 e 43). O livro valua a ITUB4 assim:

```
LIVRO:   g = 10,24%   ·   Ke = 12,48%   →   V = R$ 37,22   (região R$ 35 – R$ 39, MS ±5%)
APP HOJE: g = 6,94%   ·   Ke = 17,30%   →   DDM R$ 16,13
```

O `g` do livro (10,24%) é praticamente o **`g` por fundamentos** que o app calcula e **descarta**
(10,29%) — o app adota o histórico de 6,94%. **O app está tão longe do próprio livro que replica o
caso-exemplo do livro com menos da metade do valor.** Isso não é calibração: é o Core Value
("fiel ao método do livro") violado no caso-teste do próprio método.

**O caso do livro é o critério de aceite mais duro do marco.**

### O CONTRATO DE SAÍDA — o livro já o define; NÃO inventar outro

Verificado no PDF: **"preço-teto" e "Bazin" têm ZERO ocorrências**; "valor intrínseco" tem 39.
O livro prescreve **valor intrínseco + região de valor**, com uma regra de decisão de **três**
estados (Cap. 17):

> *"a ITUB4 só estaria interessante para uma **compra descontada** se o preço estivesse abaixo de
> R$ 35 … em que momento ela poderia estar **cara e se tornar uma venda interessante** … observar
> R$ 39. Mas se o preço estivesse **dentro do intervalo**, poderia assumir que a ação estaria sendo
> negociada por um **valor justo**."*

Isso é **exatamente** o `SUBAVALIADA / NO INTERVALO / SOBREAVALIADA` que o app já tem. **O contrato
de saída atual é FIEL — não trocar por "preço-teto + viés binário"** (proposta descartada: não é do
livro, e o binário destrói a categoria "valor justo"). O que **sai** é só o que nunca veio do livro:
`"Evitar"` e `"Qualidade Baixa"`.

**A margem de segurança é do livro e é do USUÁRIO:** percentual **simétrico** sobre o `V`
(*"+5% e −5%, por exemplo … se 5%, 10% ou qualquer outro valor, **é você quem decide**"*). Isso
**mata a Armadilha 4 por construção** — uma MS que é controle explícito do usuário não pode ser
calibrada para maquiar resultado. A tabela escalonada da Morningstar **não se aplica**: o livro tem
regra própria e ela tem precedência.

**A matriz de sensibilidade Ke×g VIVE.** O livro a chama de *"a que mais gostamos"* — é a estratégia
**preferida** dele para definir a região de valor. Proposta de matá-la: **descartada**. Ela deve ser
construída sobre o `Ke` e o `g` **corretos**, não sobre os errados de hoje.

**Target features (a ordem é obrigatória — cada passo depende do anterior):**
0. **Blindagem processual** — quarentenar os goldens pinados e escrever os **INVARIANTES** no lugar
   (deriváveis da teoria, escrevíveis hoje). O principal: **`V` invariante a um choque de +300bps de
   inflação — deslocando `rf`, `g_cap` E `ROE` juntos — com variação < 5%**, escrito como
   `xfail(strict=True)` que vira verde na fase do **`Ke` (Fase 12)**. Isso É a definição da Doença 1.
   Sem isso, os consertos das fases seguintes são revertidos por um knob e ninguém nota.

   > **O `ROE` entra no choque, e o limiar é 5% — ambos medidos, não escolhidos.** Chocar só `rf` e
   > `g_cap` derruba `V` em **−27,67%** *mesmo com o motor perfeito*: o choque preserva `(Ke−g)` mas
   > comprime `(ROE−Ke)`. Inflação levanta o **lucro nominal**, não só a taxa de desconto — um `ROE`
   > congelado é a Doença 1 uma camada abaixo. E com `n_fade = 10` o piso estrutural da janela
   > explícita é **−4,68%**, o que torna os 2% originais inalcançáveis. Detalhes em
   > `.planning/phases/07-blindagem-processual-blind/07-RESEARCH.md`.
1. **Reconciliação de sanidade na ingestão** — os asserts que teriam pego os bugs de dados.
   Incluir o **assert de clean surplus** (`ΔB = LL − DIV`): é simultaneamente detector de bug **e**
   pré-condição de validade do RIM.
2. **Ingestão correta** — JCP, lucro/PL do controlador, duplo ajuste de split, `sharesOutstanding`.
3. **Primitivas sem viés** — `normalizacao.py:73-75` (mediana de 3 = o ano do MEIO → haircut medido
   de −9,1% num crescedor de 10%) e `fundamentals.py:137-150` (ROE de bases temporais cruzadas).
   Maior alavancagem por linha do repositório.
4. **Identidade do `g` fechada** — `g_cap = (1+π_ciclo)(1+PIB_real)−1 = **7,28%**` (medido no BCB:
   π_ciclo = 5,18%, SGS 13522, mesma janela do `rf`). Reconciliar `g_alto` com o livro (que usa o `g`
   de fundamentos, não o histórico).
5. **E SÓ ENTÃO o Ke** — ERP único de 4,5%, beta setorial + Blume, e o `ke_teto` sai. Fase separada
   da 4 **de propósito**: fundir as duas dá um número e zero diagnóstico.
6. **Colapso dos motores no RIM** — sob clean surplus, os 4 motores não são 4 opiniões: são **4
   implementações do mesmo modelo com inputs inconsistentes**. Logo a dispersão 0,81/0,63/0,63/0,48
   é a assinatura dos bugs, e o **ensemble (ENS-01) está medindo os próprios bugs do projeto e
   chamando isso de "divergência de método"** — o ensemble morre junto. Os motores viram **políticas
   de input** do RIM: o classificador de arquétipo deixa de escolher um *modelo* (erro ilimitado) e
   passa a escolher uma *âncora de ROE* (erro limitado). Carve-out real: transmissoras sob ICPC 01
   usam **modelo de ativo financeiro** — o book **já é** o VP da RAP e o ROE dispara em ano de IPCA
   alto, logo consertar o `g` causaria **double-count de inflação** nelas. Separar
   `PAGADORA_REGULADA` (hoje também o *default por eliminação*, `arquetipo.py:176` — bug latente) em
   `PAGADORA_MADURA` + `CONCESSAO_FINITA`.
7. **Revalidação honesta** — cesta estratificada, fair values commitados ANTES de rodar, **3 graus de
   liberdade** (não ~8). Métrica: distribuição + jackknife (`nenhum ticker é load-bearing`), nunca
   assert de ticker+reais. Validar contra consenso é **circular** (o consenso é ancorado no preço); a
   âncora dura e grátis é **invariantes algébricos + centro da seção transversal**. Backtest temporal
   só com point-in-time de verdade — **se não der para fazer PIT direito, NÃO fazer**: um backtest
   ingênuo produz um número confiante e falso, pior que nenhum.

**CINCO ARMADILHAS — as 3 primeiras provadas por simulação; as 2 últimas achadas na pesquisa:**
1. **Remover `ke_teto: 0.13` antes de consertar o `g`** → ITUB4 0,75→0,64; BBDC4 0,71→**0,52**. O clamp
   é indefensável (3 de 4 bancos saturam; a justificativa "Blume" do `config.yaml:235` é
   *aritmeticamente falsa* — Blume daria 15,9%, não 13%) **mas é uma muleta que compensa o viés do
   `g`**. O Ke DEPENDE do `g`. Ke sozinho é líquido zero (0,68 → 0,67).
2. **"Consertar" `dcf_crescimento` com FCFE (`lpa × payout`)** → vira DDM. WEGE3 0,58→**0,26**.
3. **Reajustar knobs quando o golden `ITUB4: 32.88 ± 0.20` quebrar.** Ele VAI quebrar e **isso é o
   conserto funcionando** — é **critério de saída** da fase 3, não regressão. O golden deve ser
   **DELETADO, não atualizado**: atualizar mantém o reflexo vivo. Regra escrita: *"uma justificativa
   legítima de knob nunca menciona um ticker"* (compare `config.yaml:237` — "Move ITUB4 ~R$2").
4. **A margem de segurança virar o novo `ke_teto`.** Ela multiplica o `V` — se for calibrada até os
   resultados ficarem bonitos, é o post-mortem do v2.3 num endereço novo. **Neutralizada pelo livro:**
   MS é escolha do usuário (±5%/±10%), nunca calibrada contra dispersão, preço ou taxa de "compra".
5. **O conserto do `g` cria a própria fragilidade.** Com `g` = 7,28%, o spread `Ke−g` cai de 10,5pp
   para ~5,5pp e **o peso do valor terminal quase DOBRA**. `excesso_sustentavel` e `ke_g_spread_min`,
   hoje decorativos, viram **load-bearing na fase do `g`**. Prever isso na fase 4, não descobrir depois.

**Correções a afirmações anteriores deste documento (registradas para não se repetirem):**
- ~~"O RIM tem teto estrutural, logo é incapaz de produzir o CGRA4 a 921×"~~ — **FALSO**. O bug é
  escala de `num_acoes`, e `VPA = PL/num_acoes` infla junto: **o RIM herda o erro 1:1**, com P/B justo
  de 1,4×. A guarda real é o assert `0 < pb_justo < 6`, não o motor.
- ~~"`nav` é o 1º termo do RIM"~~ — **meia-verdade**. Vale para o NAV *contábil*; falso justamente para
  **holdings**, cujas participações entram por equivalência patrimonial, não a mercado.
- ~~"O gate do v2.3 passou 4/4"~~ — **é 2/4**. Com ±15% sobre faixas de consenso já largas, a banda
  efetiva tem 2,2–2,6× de largura; BBAS3 (43,89 vs teto 39,00) e BBDC4 (13,37 vs piso 15,00) estão
  **fora do consenso** e passam só pelo acolchoamento. Contando a rota de seguradora e a regra de
  exceção, o v2.3 gastou **~8 graus de liberdade sobre 4 observações**, não 4.

**Suspeita aberta (spike na fase 1, ANTES de calibrar):** clean surplus violado em bancos (IFRS 9
FVOCI: marcação a mercado vai direto ao PL) → `B0` deprimido → **o RIM subvaloriza o banco de
qualidade**. Que é *exatamente o sintoma que o v2.3 combateu com knobs*. Se confirmado, os knobs
mascaravam um **terceiro bug de dados**. Idem: IHCD/AT1 dentro do PL (`2.03`) inflaria o book do
ordinário. Correção sem knob: usar o **resultado abrangente** (DRA) no RI.

**Escopo:** engine inteira — ingestão, primitivas, motores, contrato de saída e validação. **Não é
cirúrgico**, ao contrário do v2.3. ~150 dos 448 testes são goldens de um método errado e serão
reescritos; isso é a correção, não regressão.

_(Marcos v1.0–v2.3 arquivados/registrados em `.planning/`. O v2.3 shipped 2026-07-13 (tag `v2.3`,
deployado) — a auditoria posterior mostrou que sua calibração era um overfit sobre 4 observações
com ~4 knobs livres; o v2.4 corrige a causa que aqueles knobs mascaravam.)_

## Requirements

### Validated

<!-- Capacidades já existentes no código, em uso. -->

- ✓ Analisar uma ação a fundo: múltiplos (Cap. 10), valuation por DDM de dois estágios
  (Cap. 13-17), CAPM/Ke (Cap. 16), crescimento (Cap. 14) e tabela de fundamentos de 10 anos — existing
- ✓ Garimpar carteira por ranking BSD de Carlson (Cap. 8) + filtros customizados — existing
- ✓ Ranking por múltiplos com preço-alvo por regressão P/L ~ f(payout, ROE) (Cap. 11-12) — existing
- ✓ Ingestão gratuita de dados: CVM (fundamentos), Yahoo (preços/dividendos/beta), BCB (Selic/macro) — existing
- ✓ CLI espelhando a engine da UI — existing
- ✓ Tooltips de glossário (ícone ?) com definições do livro em todos os termos da UI — existing
- ✓ Testes golden da engine (pytest) — existing
- ✓ **Corte por Selic real no Garimpo** (CR-01) — Validated in Phase 1
- ✓ **Janela de payout unificada entre modos** (CR-02/WR-03) — Validated in Phase 1 (função canônica `payout_valuation()`)
- ✓ **Clamp/alerta de payout fora de [0,1] no Ranking, igual ao Analisar** (CR-03 parte) — Validated in Phase 1
- ✓ **"indisponível" em vez de "—" no Ranking quando ROE/payout faltam** (CR-03 parte / RANK-01) — Validated in Phase 2
- ✓ **ROE com base de PL consistente** (WR-01) — Validated in Phase 1
- ✓ **Proxy de crescimento padronizado em janela** (WR-02) — Validated in Phase 1
- ✓ **DY corrente com dividendos dos últimos 12m** (WR-04) — Validated in Phase 1
- ✓ **Fatores ausentes no BSD tratados como neutro/ausente** (WR-05) — Validated in Phase 1
- ✓ **BSD com padronização absoluta (referência fixa), reproduzível** (WR-06) — Validated in Phase 1
- ✓ **Intervalo de valor intrínseco vindo de um único cálculo (sem duplicação)** (WR-07) — Validated in Phase 1
- ✓ **Coluna Ano-base efetivo (ultimo_ano) no Garimpo e Ranking** (ANO-01) — Validated in Phase 2
- ✓ **Payouts duplos rotulados no Analisar** (último ano vs. média 3a do DDM) (PAYOUT-02) — Validated in Phase 2
- ✓ **Trava de testes de coerência cross-modo** (ROE/payout/direção do veredito) (TEST-01/TEST-02) — Validated in Phase 2
- ✓ **Gráfico interativo (Plotly) de preço 5a na aba Analisar, com zoom/hover e botões de período** (GRAF-01) — Validated in Phase 3 (v1.1)
- ✓ **Banda do valor intrínseco do DDM sobreposta ao preço** (GRAF-02) — Validated in Phase 3 (v1.1)
- ✓ **Degradação graciosa quando a série de preços do Yahoo falha** (GRAF-03) — Validated in Phase 3 (v1.1)
- ✓ **Classificador de arquétipo + registry arquétipo→motor** (ARQ) — Validated in Phase 1 (v2.2)
- ✓ **4 motores primários implementados e plugados: RIM (banco), lucro normalizado (cíclica), DCF multi-estágio (crescimento), NAV (holding)** (ENG-02..05) — Validated in Phase 2 (v2.2); consumo pelo selo/veredito é Fase 3
- ✓ **Ensemble com bandeira de divergência** (motor primário do arquétipo × contraponto DDM; bandeira com razão + hipótese curada quando maior > 2× menor) (ENS-01) — Validated in Phase 3 (v2.2)
- ✓ **Guarda-corpos anti-aberração** (`_guarda_san01`: intrínseco < 0,5× pares E ROE>15% E corte payout >40% → reetiqueta "DDM conservador demais para o perfil", número visível; degradável sem rede) (SAN-01) — Validated in Phase 3 (v2.2)
- ✓ **Veredito honesto: selo consome o motor do arquétipo** (não o DDM fixo; DDM rebaixado a "lente conservadora") e **assume a dúvida em caso-fronteira** (range dos motores candidatos + bandeira "classificação incerta") (VER-01/VER-02) — Validated in Phase 3 (v2.2)

### Active

<!-- Marco v2.3 — Calibração do Valuation à Realidade (RIM com Valor Terminal / BACKTEST-01). REQ-IDs em REQUIREMENTS.md. -->

- [ ] RIM com valor terminal (perpetuidade de residual income / P/B justo) — banco de qualidade valua coerente com a realidade, não ancorado no VPA (CAL)
- [ ] Ke do RIM por arquétipo revisado como ajuste secundário (rever teto/erp de banco) (CAL)
- [ ] Harness de validação BACKTEST-01: cesta de bancos triangulada contra 4 âncoras (Graham+Bazin, preço, fair values manuais, múltiplos de pares) (VAL)
- [ ] Redeploy do app v2.3 na VPS (o v2.2 nunca subiu) (OPS)

<!-- v2.0 Comercialização — SHIPPED 2026-07-10 (1 item deferido: 03-05 E2E pago). -->

_(v1.4–v1.7 — Swing Trade / Modo Trading / Home / Lentes-Selo-Comparador — SHIPPED 2026-07-04, tag `v1.7`.
v2.0 Comercialização/Lazari Capital — SHIPPED 2026-07-10, produto no ar, E2E pago concluído.)_

### Out of Scope

- Dados pagos / APIs premium (brapi pago, terminais) — projeto é custo zero por princípio
- Reescrever a engine de valuation — o cálculo está correto; o problema é consistência de
  apresentação/agregação entre menus, não as fórmulas
- Novas ferramentas/menus além dos 3 atuais — o gráfico do v1.1 é um enriquecimento da aba
  "Analisar" existente, não um quarto menu

## Context

- Stack: Python 3, Streamlit 1.58, pandas, numpy, yfinance, pytest. Engine em `src/analista/`
  (core: ddm, capm, fundamentals, growth, screening, lifecycle, comparables, multiples;
  ingest: cvm, prices, macro, universe, build; report). UI em `app.py`, CLI em `cli.py`.
- **Auditoria de consistência já feita** — `CONSISTENCY-REVIEW.md` na raiz documenta os 16
  achados (3 críticos, 7 warnings, 6 infos), cada um com arquivo:linha, o que diverge e a
  correção sugerida. É a fonte de verdade do escopo deste marco.
- O que está confirmado correto (não mexer): fórmulas únicas de ROE/P-L/DY/payout/ML/EY em
  `multiples.py`/`fundamentals.py`; unidades decimais com ×100 só na borda; UI lê valores da
  engine sem recalcular Ke/Beta/g/DDM; CLI e UI compartilham a mesma engine.
- **Estado atual (2026-07-12): marco v2.2 em andamento — Phase 1 e Phase 2 completas.** Phase 1
  entregou o classificador de arquétipo (setor CVM + refino quantitativo) + registry arquétipo→motor
  com fallback honesto (5/5 verificado). Phase 2 (5/5 verificado) implementou os 4 motores que
  faltavam como funções puras config-driven em `core/motores.py` — RIM+Ke estrutural (destrava o
  ITUB4 a ~R$28 honesto, materialmente > DDM ~R$16), lucro normalizado (cíclica), DCF multi-estágio
  (crescimento), NAV contábil (holding) — plugou-os no registry e no funil, e migrou a suspensão do
  veredito (`motor != "ddm"`) sem regredir o ITUB4 de "VERIFICAR" para "evitar". Code review pós-fase:
  6 achados corrigidos (guarda de intrínseco não-positivo no motor, paridade com `_guarda_faixa_ddm`).
  Suite: 406 passed. Falta a Phase 3 (selo consome o motor do arquétipo + ensemble/divergência +
  guarda-corpos anti-aberração completos SAN-01).

## Constraints

- **Tech stack**: Python 3 + Streamlit; sem backend próprio; custo zero (só dados gratuitos)
- **Compatibility** (REVISTO no v2.4 — a regra antiga era o próprio bug): os testes de **CONTRATO** e
  de **INVARIANTE** devem continuar passando. Os **GOLDEN-DE-NÍVEL** (que travam um número, logo travam
  o método atual) **devem quebrar** conforme cada fase os alcança — e são **DELETADOS, nunca
  atualizados**. A regra antiga ("todos os goldens devem continuar passando") era literalmente a
  instrução de preservar o método errado; é o reflexo que produziu o overfit do v2.3.
- **Infra/git**: este projeto agora é um **repositório git dedicado** (`git init` próprio),
  desacoplado do repositório do `$HOME`. `.planning/` vive dentro do projeto.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Abordagem das correções = mudar o comportamento (não só rótulos) | Fidelidade ao método do livro; a engine deve cumprir o que a UI promete | ✓ Good — Fases 1-2 |
| Padronizar BSD contra referência fixa em vez do lote | "BSD > 80" do Carlson é corte absoluto; relativo ao lote torna a nota não-reproduzível | ✓ Good — Phase 1 |
| Repo git dedicado para o projeto | Resolve a dor do git root no `$HOME`; isola histórico e o `.planning/` | ✓ Good |
| Marco cobre todos os 16 achados (3 críticos + 7 warnings; infos conforme couber) | Usuário pediu cobertura total | ✓ Good — endereçado nas Fases 1-2 |
| app.py é read-only: só lê campos da engine, nunca recalcula método | Garante que a UI não reintroduz divergência entre modos | ✓ Good — Phase 2 |
| Série do gráfico = Close nominal (`auto_adjust=False`), beta/retornos seguem em Adj Close | Eixo Y do gráfico tem de ficar na mesma base da banda DDM (nominal); senão preços retroajustados distorcem a margem de segurança (CR-01) | ✓ Good — Phase 3 |
| Botões de período nativos do Plotly (30D/6M/1A/5A) | Zoom por janela sem JS nem dependência extra | ✓ Good — Phase 3 |
| `esc_md()` escapa `$` em metric/alertas (não no `fmt_rs` global) | Dois `R$` na mesma string acionavam o modo LaTeX do Streamlit; tabelas continuam com texto cru | ✓ Good — Phase 3 |
| Análise técnica (v1.2) é **consultiva**, nunca altera o veredito fundamentalista | O projeto é fundamentalista por princípio (método do livro); indicadores ajudam o timing/alerta, não o "barato/caro" | — Pending |
| Sinal de venda = rompimento técnico **dispara reverificação** dos fundamentos (não vende sozinho) | O livro vende por perda de fundamento; o técnico serve de gatilho antecipado para o investidor reolhar os números | — Pending |
| Indicadores ligáveis/desligáveis e selecionáveis na aba Analisar | Evita poluir o gráfico; o investidor escolhe o que quer ver sem virar um terminal de trade | — Pending |
| Construir v1.4 (ferramenta de swing) antes da v2.0 Comercialização | Agregar valor de produto antes de cobrar; v2.0 já está definida e esperando | — Pending (2026-06-29) |
| Swing trade = menu/produto NOVO e separado, não mexe na aba Analisar nem no veredito fundamentalista | Mantém o método do livro de dividendos intacto e validado; análise técnica é outro "produto" dentro do app | — Pending |
| Setup técnico EXIBE sinais, nunca recomenda (sem "compre/venda") | Coerente com o posicionamento de software educacional; o investidor decide | — Pending |
| Tempo real puro fora de escopo no v1.4 (custo-zero); intraday via Yahoo é best-effort com aviso de atraso (~15min) | Feed real-time da B3 é pago e quebraria o princípio de custo zero | — Pending |
| Marca comercial = **Lazari Capital** (domínio Lazari Tech Capital) | Construir imagem de produto desde a etapa comercial | — Pending (v2.0) |
| Comercialização = **gateway híbrido com Django** (front Django + Streamlit atrás de gate), não reescrever o app | Reusa código testado do crm-voic e o engine Streamlit (338 testes) intacto; robusto/seguro/escalável sem retrabalho | — Pending (v2.0) |
| Pivô da arquitetura v2.0: **Django + webhooks nativos** no lugar de Supabase + n8n + React | Cortar dependência de n8n e reaproveitar o crm-voic 1:1; CRM já roda bem nesse padrão | — Pending (v2.0) |
| Gate = **Traefik forward-auth** (Django valida sessão+status, injeta X-User-Email no Streamlit) | Menos código de segurança custom que JWT lido dentro do Streamlit; usa infra Traefik existente | — Pending (v2.0) |
| Asaas em **conta e chave próprias** (não as do crm-voic) | Produto separado; só a estrutura de código é compartilhada | — Pending (v2.0) |
| Cadastro **self-serve** (B2C/trial), diferente do crm-voic (invite-only) | Aquisição de clientes pessoa física precisa de cadastro aberto com trial | — Pending (v2.0) |
| Abrir v2.2 (Motor por Arquétipo) fechando v2.0 (E2E pago concluído; só resta operador decidir estorno do smoke R$19,90) | v2.0 está no ar, funcional e validado end-to-end; nada bloqueia o trabalho de engine | — Pending (2026-07-11) |
| O problema do ITUB4 é erro de **arquitetura** (ausência de roteamento), não de fórmula | DDM/Graham/Bazin estão matematicamente corretos; o defeito é aplicar DDM de estágio único como motor primário para todo negócio e agregar o veredito por ele | — Pending (v2.2) |
| Gargalo do v2.2 = **classificador** (~60%), não os motores (~20%, fórmulas de livro-texto) | Priorizar a árvore de decisão do classificador primeiro, depois plugar os motores nela | — Pending (v2.2) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-15 — v2.4 Fidelidade do Valuation em andamento: Fase 8 (Sanidade dos Dados / SAN) completa — o pipeline detecta dado sujo (5 checks + JCP + clean surplus em `core/sanidade.py`, never-raise), spike SAN-07 fecha o 3º bug de dados como inexistente, baseline de regressão dos sujos (62 tickers) congelado para a Fase 9. Zero conserto de dado (de propósito). Próximo: Fase 9 (Ingestão correta / DATA).*
