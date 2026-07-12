# Phase 3: Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo - Context

**Gathered:** 2026-07-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Fechar o loop na **agregação do veredito** (`report.py` + `selo.py`), que hoje é single-model e,
após as Fases 1-2, deixa todo arquétipo **não-DDM com o veredito SUSPENSO** (`report.py:296`,
prefixo `VERIFICAR` — o motor CALCULA e EXIBE o intrínseco, mas o selo ainda **não o consome**).
Esta fase destrava esse último passo:

- **VER-01** — o selo/veredito passa a **consumir o motor do arquétipo** (RIM p/ ITUB4), não o DDM
  fixo; o DDM é rebaixado a "lente conservadora". A suspensão D-06 (`motor != "ddm"` → VERIFICAR) é
  **substituída** por veredito real derivado de `a.intrinseco_motor`.
- **ENS-01** — roda o motor primário + ≥1 contraponto; quando a divergência passa do limiar
  (maior > 2× menor), levanta **bandeira de divergência** com hipótese exibida, em vez de cravar
  número único.
- **SAN-01** — **guarda-corpos anti-aberração** completos antes de estampar "evitar": a regra
  `intrínseco < 0,5× mediana dos pares` **E** `ROE > 15%` **E** `corte de payout > 40%` reetiqueta
  para "DDM conservador demais para o perfil — ver motor primário do arquétipo".
- **VER-02** — em **caso-fronteira** (`arquetipo_fronteirico`), o veredito **assume a dúvida**
  (range + bandeira) em vez de fingir certeza.

**Dentro do escopo:** refatorar a agregação em `report.py`/`selo.py` para consumir o motor do
arquétipo, o ensemble motor×contraponto + bandeira de divergência, o guarda-corpo SAN-01 completo,
a dúvida honesta no fronteiriço, e o render/CLI dessas superfícies. Custo-zero (CVM+Yahoo+BCB).
**Fora do escopo:** reescrever os motores/DDM (estão corretos — Fases 1-2); novas fontes de dados;
redesenho de UI além da lógica de veredito e da bandeira; acertar 100% dos tickers (BACKTEST-01 /
ARQ-AUTO-01 deferidos).

**Firewall inegociável:** `selo.py` NUNCA importa `report.py` — recebe só primitivos (bsd, veredito
str, cfg). Toda mudança de comportamento acontece do lado do `report`/veredito ou como novos
primitivos passados ao selo; `selo.py` só ganha, no máximo, um novo prefixo/faixa a reconhecer.
</domain>

<decisions>
## Implementation Decisions

O usuário delegou as 4 decisões ("você decide"). Abaixo, as **recomendações locked-in por padrão**
(com racional e pitfalls travados) — o planner/researcher pode ajustar SE o pipeline exigir, mas a
direção-default está definida para não re-perguntar.

### VER-01 — como o intrínseco único do motor vira faixa Barato/Justo/Caro
- **D-01 (recomendado):** **Range do ensemble** como banda do veredito. Hoje o veredito nasce de
  `preço` vs. banda `vmin/vmax` (min/max da matriz de sensibilidade Ke×g do DDM — `report.py:283-291`).
  Os motores da Fase 2 devolvem **um número único** (`a.intrinseco_motor`), sem banda. Recomendação:
  `vmin/vmax = min/max entre o motor primário e o(s) contraponto(s) do ENS-01` (ex.: RIM × DDM). A
  **mesma banda** que gera a bandeira de divergência gera a faixa do selo — unifica VER-01 e ENS-01 e
  reusa `selo.faixa_do_veredito` sem inventar knob novo.
  - **Fallback:** se o contraponto degradar (None), banda = intrínseco ± margem de segurança fixa
    (config-driven) — nunca deixar o motor sem faixa por falta de par.
  - **A critério do planner:** se a evidência mostrar que o range motor×contraponto fica largo demais
    (bandeira quase sempre), pode-se preferir margem de segurança fixa como banda primária e usar o
    contraponto só para a bandeira. O importante: **o preço é comparado a uma banda vinda do motor do
    arquétipo, não mais do DDM**, e o selo consome esse veredito.

### ENS-01 — contraponto e hipótese da bandeira
- **D-02 (recomendado):** **DDM "lente conservadora" como contraponto universal.** O DDM já roda
  SEMPRE (mesmo rebaixado onde não é o primário), então é um contraponto pronto, custo-zero, e é
  exatamente o par do caso-âncora (ITUB4: RIM ~R$28 × DDM ~R$16 → >2× → bandeira). Reusar o helper
  puro **já existente** `comparables.divergencia_entre_lentes()` (`comparables.py:87`, devolve
  `(divergiu, razão=maior/menor)` com limiar) — hoje só usado no comparador multi-ticker da CLI
  (`cli.py:243`); a Fase 3 pluga o mesmo helper no funil single-stock.
  - **A critério do planner:** adicionar Graham/Bazin (`lentes.py:37`/`:75`) como 2º contraponto por
    arquétipo, se agregar sinal sem inflar bandeiras espúrias.
- **D-03 (recomendado):** **Hipótese por template arquétipo × direção.** Frase curada por
  `(arquétipo, sinal da divergência)` — ex.: financeira com `motor > DDM` → "compounder subvalorizado
  pelo DDM (Ke alto comprime o DDM)"; cíclica com `motor < DDM` → "possível topo de ciclo". Copy
  estável, testável por golden, espelha o padrão do `_MATRIZ` do `selo.py:48`. O brief pede
  explicitamente o **"porquê"** exibido — divergência genérica ("modelos divergem ~Nx") só como
  fallback quando arquétipo/direção não resolvem uma frase.

### SAN-01 — fonte da "mediana dos pares" e ação do guarda-corpo
- **D-04 (recomendado):** **Proxy da regressão P/L como "valor dos pares".** O funil `analisar_acao()`
  recebe **uma empresa só** — não há lista de pares carregada (o comparador exige tickers explícitos e
  puxar o setor inteiro custa rede, o que fere o custo-zero/latência). Recomendação: usar o preço-alvo
  implicado pela regressão `P/L = f(payout, ROE)` (`comparables.preco_alvo_por_regressao`,
  `comparables.py:181`) como o "valor dos pares" — já é uma síntese setorial custo-zero que roda sem
  puxar tickers extras. A condição vira `intrínseco < 0,5 × valor-implicado-pelos-pares`.
  - **Degradação:** quando a regressão não roda (R² baixo / amostra pequena — os freios de `01-08` já
    existem em `comparables.RegressaoPL.r2_baixo`/`amostra_pequena`), a condição de pares **não é
    avaliada** e o guarda-corpo cai para as **2 restantes** (`ROE > 15%` **E** `corte de payout > 40%`).
    Nunca puxa rede; a aberração clássica (ITUB4) ainda é capturada pelas 2.
- **D-05 (recomendado):** **Reetiqueta honesta, não supressão.** Quando o guarda-corpo dispara, trocar
  "qualidade baixa / evitar" por **"DDM conservador demais para este perfil — ver motor primário do
  arquétipo"** (texto literal do SAN-01/brief), mantendo o número visível. Feito na **borda do
  veredito em `report.py`**, sem tocar `selo.py` (firewall).
  - **Nota de arquitetura:** com o VER-01, a maioria dos arquétipos não-DDM já **não** cai em "evitar"
    via DDM (o veredito vem do motor certo). O SAN-01 vira **backstop defense-in-depth** — pega o caso
    residual em que o DDM ainda é o primário (pagadora regulada) OU em que o motor degrada e o DDM
    reassume. Manter o guarda-corpo mesmo assim: "todo veredito 'evitar' passa pelos guarda-corpos"
    (success criterion #3 / brief item 6 "zero aberração silenciosa").

### VER-02 — como assumir a dúvida no caso-fronteira
- **D-06 (recomendado):** **Range dos candidatos + bandeira.** Quando `a.arquetipo_fronteirico` é True,
  a Fase 1 já guarda 2-3 candidatos em `a.arquetipo_candidatos`. Recomendação: rodar o motor de cada
  arquétipo candidato, exibir o **range [menor..maior]** desses intrínsecos + bandeira "classificação
  incerta entre X e Y" — é o "range + bandeira" literal do VER-02; o usuário vê o span da dúvida em
  vez de um selo cravado.
  - **Degradação:** se um motor candidato falha (None), listar os candidatos que resolveram e o
    intrínseco de cada um lado a lado, sem forçar um range de 1 ponto. Selo **não estampa** faixa/rótulo
    no fronteiriço (reusar o mecanismo de supressão de faixa que o prefixo VERIFICAR já dá em
    `selo.py:119`, agora com o range/candidatos exibidos como conteúdo).

### Claude's Discretion (delegado explicitamente pelo usuário)
- **Todas as 4 decisões acima** foram delegadas ("você decide"). As recomendações D-01..D-06 são a
  direção-default; o planner tem liberdade para ajustar dentro do racional documentado, desde que
  preserve: (a) o selo consome o motor do arquétipo, não o DDM fixo; (b) limiar de divergência 2×;
  (c) a regra literal do SAN-01 e "todo evitar passa pelos guarda-corpos"; (d) o firewall selo↛report;
  (e) os goldens travados verdes (ver Canonical Refs).
- **Thresholds/knobs numéricos:** margem de segurança fixa (fallback D-01), limiar exato do "corte de
  payout > 40%", horizonte da hipótese — derivar da prática-padrão e dos goldens; expor em `config.yaml`
  quando fizer sentido (padrão do projeto).
- **Estrutura de código:** onde a banda-do-ensemble e a bandeira vivem (helper puro em `comparables`/
  novo módulo vs. inline no funil), assinatura dos novos campos em `AnaliseAcao`, forma exata do render
  no `relatorio_markdown`/CLI/`app.py`.
- **Rebaseline de goldens:** se prefixos/rótulos de veredito mudarem deliberadamente, atualizar
  `faixa_do_veredito` (`selo.py:88`) e `report._veredito_token` (`report.py:491`) **juntos** e
  rebaselinar `test_selo`/`test_vulc3_regressao` **com intenção declarada** — nunca por acidente.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Brief e requisitos do milestone
- `.planning/BRIEF-motor-arquetipo.md` — brief-fonte: diagnóstico do ITUB4 (preço R$43,59 · DDM
  R$12,93–19,32 · Graham R$39,88 · Bazin R$28,97 · veredito falso "Evitar"), § Ensemble/SAN/VER,
  critérios de aceite (itens 5-6: fronteiriço com range+bandeira; zero aberração silenciosa), mapa de
  código com âncoras `arquivo:linha`. **Leitura obrigatória.**
- `.planning/REQUIREMENTS.md` — requisitos ENS-01, SAN-01, VER-01, VER-02 (parciais ENS-01/SAN-01 já
  entregues na Fase 1 gap-closure — ver traceability; a Fase 3 fecha o restante).
- `.planning/ROADMAP.md` §"Phase 3: Veredito Honesto" — goal + 5 success criteria (inclui a lista de
  testes que devem continuar verdes).

### Contexto das fases anteriores (decisões que a Fase 3 herda/estende)
- `.planning/phases/02-motores-por-arqu-tipo/02-CONTEXT.md` — D-06 (motor calcula/EXIBE, selo suspenso)
  é exatamente o que a Fase 3 destrava; D-01 (RIM usa Ke estrutural ~12,5%, DDM ao vivo ~17% é a lente
  conservadora); campos `intrinseco_motor`/`motor_rotulo`/`motor`.
- `.planning/phases/01-classificador-de-arqu-tipo-roteamento/01-CONTEXT.md` — D-01 (fronteiriço = só
  conflito real de sinais; ~85%/~15%); campos `arquetipo_fronteirico`/`arquetipo_candidatos` que o
  VER-02 consome.

### Código do funil de veredito (onde a Fase 3 refatora)
- `src/analista/report/report.py` — `analisar_acao()` (`:96`). **Bloco de veredito `:278-343`**:
  banda `vmin/vmax` a partir da matriz de sensibilidade (`:283-291`); guarda-corpo DDM `_guarda_faixa_ddm`
  (`:65`, chamado `:295`); **suspensão D-06 `:296-319`** (`if a.motor != "ddm":` → VERIFICAR) — é ESTE
  ramo que o VER-01 substitui por veredito real do motor; ramo DDM `:320-343` (a lógica SUB/NO INTERVALO/
  SOBRE que o motor do arquétipo passará a alimentar). `AnaliseAcao` dataclass `:23-62`. Selo montado
  `:443-447`. `_veredito_token` `:491`; render `relatorio_markdown` `:546` (bloco motor `:594-606`).
- `src/analista/report/selo.py` — `montar_selo()` (`:105`), `faixa_do_veredito()` (`:88`, casa prefixos
  SUBAVALIADA/NO INTERVALO/SOBREAVALIADA → Barato/Justo/Caro; VERIFICAR → None suprime faixa `:119`),
  `_MATRIZ` (`:48`, quadrante qualidade×preço). **FIREWALL: selo.py não importa report.py** — preservar.
- `src/analista/core/comparables.py` — `divergencia_entre_lentes()` (`:87`, helper puro
  `(divergiu, razão)` — REUSAR no ensemble ENS-01); `preco_alvo_por_regressao()` (`:181`) +
  `RegressaoPL` (`:116`, com `.r2_baixo()`/`.amostra_pequena()`/`.roe_sinal_invertido()`) — fonte do
  "valor dos pares" do SAN-01 (D-04) e freios de degradação.
- `src/analista/core/lentes.py` — `preco_justo_graham` (`:37`), `preco_teto_bazin` (`:75`), `vpa` (`:51`),
  comparador de pares (`:140-221`). Contrapontos candidatos do ensemble (D-02).
- `src/analista/core/motores.py` — `MOTOR_ROTULO` (`:31`), `rim`/`ke_rim`/`lucro_normalizado`/
  `dcf_crescimento`/`nav_contabil`. Motores que a Fase 3 passa a **consumir** no veredito.
- `src/analista/core/arquetipo.py` — `ARQUETIPO_MOTOR` (`:45`), `classificar()`/`ResultadoArquetipo`.

### Testes que travam comportamento (não quebrar sem intenção declarada)
- `tests/test_selo.py` — cortes de cor + rótulos da matriz + **firewall selo↛report**. Preservar; só
  rebaselinar se um prefixo/faixa mudar deliberadamente.
- `tests/test_vulc3_regressao.py` — capstone e2e (veredito começa com "VERIFICAR" por sinais de risco —
  NÃO confundir com a suspensão D-06; VULC3 é armadilha real, não roteamento).
- `tests/test_guardrails_fix06.py` / `tests/test_guardrails_ddm.py` — guarda-corpos DDM já existentes.
- `tests/test_consistencia_modos.py` — mesmo número entre Analisar/Garimpo/Ranking (Core Value). O
  ensemble/veredito novo não pode divergir os 3 modos.
- `tests/test_ddm.py` — DDM Itaú ≈ R$37,22 (input fixo). `core/ddm.py` **não é tocado**.
- `tests/test_ranking_freio.py` / `tests/test_report.py` / `tests/test_arquetipo*.py` — regressões do
  roteamento e do freio do Ranking (01-08).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`comparables.divergencia_entre_lentes()`** (`comparables.py:87`): helper PURO já pronto que devolve
  `(divergiu, razão=maior/menor)` com limiar — é o motor da bandeira ENS-01. Hoje só na CLI multi-ticker
  (`cli.py:243`); a Fase 3 o pluga no funil single-stock.
- **`comparables.preco_alvo_por_regressao()` + `RegressaoPL`** (`comparables.py:181`/`:116`): síntese
  setorial custo-zero com freios de qualidade (R²/amostra) — fonte do "valor dos pares" do SAN-01 sem
  puxar rede.
- **`selo.faixa_do_veredito()` + prefixo VERIFICAR** (`selo.py:88`/`:119`): o mecanismo de suprimir
  faixa/rótulo por prefixo já existe — reusável tanto no fronteiriço (VER-02) quanto na reetiqueta SAN-01,
  sem tocar o firewall.
- **`a.intrinseco_motor`/`a.motor`/`a.motor_rotulo`** (`report.py:54-60`): o número do motor do arquétipo
  já está calculado e no dataclass — o VER-01 só precisa fazê-lo **alimentar o veredito/selo**.
- **`a.arquetipo_fronteirico`/`a.arquetipo_candidatos`** (`report.py:55-56`): entrada pronta do VER-02.
- **`_guarda_faixa_ddm()`** (`report.py:65`): precedente exato de guarda-corpo na borda do veredito
  (marca flag + zera faixa + alerta honesto, sem tocar `core`/firewall) — molde do SAN-01.

### Established Patterns
- **Funil único de valuation** em `analisar_acao()`: veredito montado num ponto só (`report.py:278-343`),
  não espalhado. Ensemble/bandeira/guarda-corpos entram nesse ponto.
- **Firewall selo↛report** (testado): mudanças de comportamento do lado do `report`/veredito; o selo só
  recebe primitivos. O prefixo VERIFICAR é a "válvula" já existente para suprimir faixa sem acoplar.
- **Fronteira CRU × valuation (FIX-04)**: usar os `*_valuation()` como número-síntese; consistência
  cross-modo é travada por `test_consistencia_modos`.
- **Guarda-corpo config-driven na borda**: `cfg["..."]` para thresholds; alertas honestos em `a.alertas`.
- **Precedente de bandeira**: `report.py:333-337` já emite "possível divergência de modelo" por flags de
  risco (VULC3) — ponto natural de extensão da bandeira de divergência do ensemble.

### Integration Points
- **VER-01:** substituir o ramo de suspensão `report.py:296-319` (`if a.motor != "ddm":` → VERIFICAR)
  por veredito real derivado de `a.intrinseco_motor` + banda do ensemble; o selo (`:445`) passa a
  consumir esse veredito.
- **ENS-01:** novo cálculo motor×contraponto no funil (após o dispatch do motor `:192-230`), gravando
  divergência/razão/hipótese em campos novos de `AnaliseAcao`; render no `relatorio_markdown` e CLI/app.
- **SAN-01:** guarda-corpo na borda do veredito (à la `_guarda_faixa_ddm`) reetiquetando "evitar" antes
  do selo; consome a regressão de pares e os sinais canônicos (ROE/payout).
- **VER-02:** ramo fronteiriço no funil que roda os motores dos candidatos e monta range+bandeira.
- **Render:** `relatorio_markdown` (`report.py:546`), CLI (`cli.py`), `app.py` — exibir bandeira,
  range e reetiqueta; UI muda só onde o veredito/bandeira aparecem (Out of Scope: redesenho maior).
</code_context>

<specifics>
## Specific Ideas

- **Caso-âncora ITUB4 (success criterion #1):** o selo final consome o **RIM** (motor da financeira),
  DDM rebaixado a lente conservadora — ITUB4 **deixa de ser "SOBREAVALIADA/Qualidade Baixa/Evitar"**.
  RIM ~R$28 × DDM ~R$16 é justamente o par >2× que aciona a bandeira de divergência com a hipótese
  "compounder subvalorizado pelo DDM".
- **Tickers-âncora dos success criteria:** ITUB4 (RIM, não mais "evitar"), TAEE11 (regulada, DDM,
  idêntica), VALE3 (cíclica, lucro normalizado), WEGE3 (crescimento, DCF sem zero/lixo).
- **VULC3** continua começando com "VERIFICAR" por **flags de risco reais** (payout>100%) — é
  distinto da suspensão D-06 por roteamento; `test_vulc3_regressao` trava isso.
- **Divergência é informação exibida, não defeito escondido** (brief): a bandeira mostra os dois
  números + o "porquê"; nunca esconde a discordância cravando o pior.
</specifics>

<deferred>
## Deferred Ideas

- **Graham/Bazin como 2º contraponto do ensemble** → possível refino do D-02 se agregar sinal sem
  inflar bandeiras; default é DDM-only como contraponto.
- **Sensibilidade própria por motor** (banda RIM/normalizado/DCF via Ke±/g±) → não escolhido no D-01
  (mais código/goldens); revisitar se a banda do ensemble se mostrar larga demais.
- **Puxar o setor inteiro para mediana de pares real** (em vez do proxy da regressão) → recusado no
  D-04 por custo de rede/latência; reconsiderar só com cache setorial custo-zero.
- **Backtesting / validação empírica** de qual motor acerta por arquétipo → BACKTEST-01, explicitamente
  fora do milestone.
- **Acertar 100% dos tickers** → ARQ-AUTO-01, fora de escopo (meta ~85% + dúvida honesta nos ~15%).

Nenhum dos itens acima altera o escopo da Fase 3 — a discussão permaneceu dentro do domínio.
</deferred>

---

*Phase: 3-Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo*
*Context gathered: 2026-07-12*
</content>
</invoke>
