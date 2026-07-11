# Phase 2: Motores por Arquétipo - Context

**Gathered:** 2026-07-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Plugar no registry `ARQUETIPO_MOTOR` os **4 motores primários que hoje estão `None`** — as fórmulas de
livro-texto (~20% do esforço) que, roteadas pelo classificador da Fase 1, fazem cada arquétipo calcular
o intrínseco pelo modelo certo:

- `financeira` → **RIM** (VPA + VP do excesso de ROE sobre Ke) — o motor que destrava o ITUB4
- `ciclica` → **lucro normalizado** (P/L justo × lucro médio 7–10a)
- `crescimento` → **DCF/multi-estágio** sobre lucro/FCF
- `holding` → **NAV contábil** (piso patrimonial simplificado)

**`pagadora_regulada` → DDM já está plugado na Fase 1 (ENG-06) e não muda.** O `core/ddm.py` puro **NÃO é
tocado** — os motores novos entram como pares no registry; onde o DDM não é o primário do arquétipo, ele é
rebaixado a "lente conservadora" (exibida, não estampada).

**Requisitos cobertos:** ENG-02 (RIM), ENG-03 (lucro normalizado), ENG-04 (DCF/multi-estágio crescimento),
ENG-05 (NAV/SOTP holding).

**Dentro do escopo:** implementar os 4 motores como funções puras, plugá-los no registry, calcular e
**exibir** o intrínseco de cada arquétipo. Custo-zero (só CVM + Yahoo + BCB).
**Fora do escopo (Fase 3):** o selo/veredito passar a **consumir** o motor do arquétipo (VER-01), ensemble +
bandeira de divergência (ENS-01), guarda-corpos anti-aberração completos (SAN-01), dúvida honesta no
caso-fronteira (VER-02). Nesta fase o selo **continua suspenso** (não estampa "evitar" para arquétipo
não-DDM), evitando regressão — ver D-06.
</domain>

<decisions>
## Implementation Decisions

### RIM — custo de capital e persistência do excesso (ENG-02)
- **D-01: RIM usa um Ke estrutural/mid-cycle (~12,5%), não o Ke do CAPM ao vivo (~17%).** Com o ITUB4
  (ROE ~19,3%), um Ke estrutural ~12,5% dá excesso de ~6,8% e o RIM destrava o ~R$40 do critério de aceite
  #1; o **DDM com o Ke do CAPM ao vivo** (~17% → ~R$16) fica como a **lente conservadora**.
  - **⚠ Nota factual para o researcher (corrige a premissa do brief):** o app **já** injeta a Selic
    **through-the-cycle** (`macro.selic_ciclo_para_capm`, média 10a) no `rf_local` (`cli.py:113`,
    `app.py:245`/`:865`) — **não** a Selic spot. Ainda assim o Ke do CAPM ao vivo de um banco fica ~17%
    porque (a) a média 10a da Selic segue elevada no regime atual e (b) `Ke = rf + beta×ERP` com beta de
    banco. Ou seja: **trocar spot→through-the-cycle já está feito e é insuficiente** — o ~R$16 do DDM vem do
    Ke estrutural alto para bancos, não de uma Selic do dia. A alavanca do critério #1 é o RIM usar um Ke
    **mais baixo** que o CAPM ao vivo. O golden `test_ddm` usa Ke 12,48% (input fixo de livro) como
    referência do que é um Ke estrutural razoável para o Itaú.
  - **A critério do researcher/planner:** de onde o Ke estrutural do RIM sai — rf normalizado + ERP
    apropriado a banco, um Ke ancorado no livro (~12,48%), ou um teto sobre o Ke do CAPM. O importante é o
    RIM não herdar o Ke ~17% que comprime o DDM.
- **D-02: Excesso de ROE faz *fade* até o Ke.** No RIM, o excesso `(ROE − Ke)` decai gradualmente rumo a
  zero num horizonte explícito (~7–10a) + valor terminal ancorado no VPA — prática-padrão do RIM. Nenhum
  banco rende acima do custo de capital para sempre; coerente com a filosofia de honestidade/conservadorismo
  do projeto. Evita inflar o intrínseco acima do mercado por assumir excesso perpétuo.

### NAV/SOTP — escopo do motor de holding (ENG-05)
- **D-03: NAV contábil simplificado (não SOTP por segmento).** Motor holding = patrimônio líquido/ações
  (VPA, já existe em `lentes.vpa`), **rotulado honestamente** como "NAV contábil (piso patrimonial), não
  SOTP por segmento". Racional: SOTP real precisa de NAV por segmento que a CVM não entrega limpo de graça
  para holdings arbitrárias; e **nenhum ticker-âncora** (ITUB4/TAEE11/VALE3/WEGE3) é holding. Mantém o
  registry **5/5 completo** e cumpre o critério de aceite #4 de forma honesta, custo-zero. (Considerado e
  recusado: deferir ENG-05; SOTP real por segmento — ver Deferred.)

### Método sob custo-zero — cíclica e crescimento (ENG-03, ENG-04)
- **D-04: Cíclica = P/L justo sobre lucro normalizado.** O núcleo do critério #2 é valuar sobre o **lucro
  médio normalizado** (7–10a, `serie_lucro_normalizada` já existe), não sobre o lucro de um ano só. Aplica-se
  um P/L justo (mediana própria/setorial/regressão existente — fonte a critério do planner) sobre esse lucro
  médio. **Não** usa EV/EBITDA (evita depender de dívida líquida + D&A da CVM, mais frágil).
- **D-05: Crescimento = multi-estágio sobre lucro/FCF.** Projeta o lucro (≈ FCF em capital-light) com o `g`
  já calculado (`g_alto` na fase explícita → `g_estável` na perpetuidade), descontado ao Ke normalizado
  (D-01). Captura o reinvestimento a ROE alto — a tese que o DDM ignorava (por isso cuspia zero/lixo com
  payout baixo, ex.: WEGE3). **Reusa a mecânica de dois estágios** (do próprio `ddm.ddm_dois_estagios` como
  função pura, ou um helper genérico extraído), alimentada por lucro/FCF em vez de dividendo, **sem tocar
  `core/ddm.py`** nem depender de capex limpo. (Não escolhido: múltiplo relativo de 1 passo — comprime a tese
  multi-estágio; DCF de FCF puro — depende de capex frágil.)

### Fronteira Fase 2 × Fase 3 — o que o motor faz com o veredito
- **D-06: Motor calcula e EXIBE o intrínseco; selo/veredito continua SUSPENSO.** Nesta fase os 4 motores
  produzem e mostram o número (ex.: "arquétipo financeira → RIM: ~R$40" como referência), mas o
  **selo/veredito NÃO passa a consumir o motor ainda** (isso é VER-01, Fase 3). **Armadilha crítica:** hoje a
  suspensão D-04 da Fase 1 dispara por `motor_pendente`; quando o RIM for plugado, `motor_pendente` vira
  `False` para financeira — se a suspensão simplesmente cair, o **ITUB4 regride para "evitar"** via DDM
  (porque o selo ainda consome DDM até a Fase 3). **Portanto a condição de suspensão migra de
  `motor_pendente` → "selo ainda não consome o motor do arquétipo"** (permanece suspenso para todo arquétipo
  não-DDM). O selo (`selo.py`), o firewall selo↛report e `report._veredito_token` **não mudam nesta fase** —
  o refactor que faz o selo consumir o arquétipo é VER-01/Fase 3.

### Claude's Discretion
- **Fonte do "P/L justo"** da cíclica (mediana histórica própria vs. setorial vs. a regressão P/L ~ f(payout,
  ROE) já existente no Ranking/comparables) — planner/researcher escolhe conforme o que o pipeline entrega de
  forma confiável.
- **Thresholds e horizontes numéricos:** anos exatos do fade do RIM (~7–10a), número de anos da normalização
  da cíclica, horizonte/estágios do multi-estágio de crescimento — planner/researcher deriva seguindo a
  prática-padrão de cada modelo e os goldens.
- **Estrutura de código dos motores:** assinaturas das funções puras, se reusa `ddm.ddm_dois_estagios`
  diretamente ou extrai um helper genérico de PV multi-estágio, forma exata de rotular o intrínseco de cada
  motor no report/CLI e o rebaixamento do DDM a "lente conservadora".
- **Como resolver o VPA/PL para o NAV e o RIM** (ano-base efetivo) — reusar `lentes.vpa` e os métodos
  canônicos de `CompanyData`.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Brief e requisitos do milestone
- `.planning/BRIEF-motor-arquetipo.md` — brief-fonte: diagnóstico do ITUB4, tabela arquétipo→motor primário
  (§ final), mapa de código com âncoras `arquivo:linha`, ordem sugerida de fases. **Leitura obrigatória.**
- `.planning/REQUIREMENTS.md` — requisitos ENG-02/ENG-03/ENG-04/ENG-05 (e o restante do milestone para
  contexto de sequência: VER-01/ENS-01/SAN-01 são da Fase 3).
- `.planning/ROADMAP.md` §"Phase 2: Motores por Arquétipo" — goal + 5 success criteria da fase.
- `.planning/phases/01-classificador-de-arqu-tipo-roteamento/01-CONTEXT.md` — decisões da Fase 1
  (D-01..D-04): 5 chaves 1:1 com motores, registry, hard-route financeiro, suspensão D-04.

### Registry e classificador (Fase 1 — entrada dos motores)
- `src/analista/core/arquetipo.py` — `ARQUETIPO_MOTOR` (`:45`, hoje 4 chaves `None` + `pagadora_regulada:"ddm"`)
  e `ResultadoArquetipo`/`classificar()` (`:121`). É aqui que os 4 motores novos são plugados no registry.
- `src/analista/report/report.py` — `analisar_acao()` (`:92`). Roteamento por arquétipo em `:175-186`
  (após CAPM `:152`, antes do DDM `:188`); campos `a.motor` (`:185`)/`a.motor_pendente` (`:186`). O bloco DDM
  (`:188+`) roda sempre como lente. `AnaliseAcao` dataclass em `:23`; **suspensão D-04 em `:240-249`**
  (`if a.motor_pendente:` → prefixo "VERIFICAR") — é exatamente esta condição que D-06 migra de
  `motor_pendente` para "selo não consome o motor".

### Motores — fórmulas e insumos
- `src/analista/core/ddm.py` — `ddm_dois_estagios()` (função pura de PV de fluxo crescente em 2 estágios).
  **NÃO tocar** (golden `test_ddm` R$37,22 input fixo). Reusável como mecânica do multi-estágio de crescimento
  (D-05) passando lucro/FCF em vez de dividendo, ou extrair helper genérico.
- `src/analista/core/lentes.py` — `vpa()` (`:51`, base do RIM e do NAV D-03), `preco_justo_graham` (`:37`),
  `preco_teto_bazin` (`:75`), comparador de pares (`:140-221`). Contrapontos naturais (uso pleno é Fase 3).
- `src/analista/core/normalizacao.py` + `CompanyData.serie_lucro_normalizada()` — normalização estatística
  de lucro (winsor/mediana) já existe: base do lucro normalizado da cíclica (D-04).
- `src/analista/core/fundamentals.py` — `CompanyData` (`:20`): `roe_valuation()` (ROE do RIM), série `roe(ano)`,
  `payout_valuation()`, `lpa_valuation()`, `serie_lucro_normalizada()`, `patrimonio_liquido`, `num_acoes`,
  `fco`, `beta`, `eh_concessionaria`. Fonte única dos sinais — não recalcular método (consistência cross-modo).
- `src/analista/core/capm.py` — `ke_local`/`ke_eua_ajustada`. O Ke ao vivo entra via `cfg["capm"]["rf_local"]`,
  que os entry points **já resolvem com a Selic through-the-cycle** (`selic_ciclo_para_capm`, média 10a) — ver
  D-01: o RIM precisa de um Ke **mais baixo** que este CAPM ao vivo (~17% p/ banco), não de outra fonte de rf.
- `src/analista/ingest/macro.py` — `selic_ciclo_para_capm` (`:87`, Selic média 10a through-the-cycle) e
  `selic_para_capm` (`:47`, spot). Contexto do rf; **o app usa a versão ciclo, não a spot** (D-01 nota factual).

### Testes que travam comportamento (não quebrar sem intenção)
- `tests/test_ddm.py` — golden do livro: DDM Itaú ≈ R$37,22 (input FIXO, Ke 12,48%). Fase 2 **não toca**
  `core/ddm.py` → deve continuar verde (success criterion #5).
- `tests/test_selo.py` — cortes de cor + rótulos + **firewall selo↛report**. Fase 2 **não muda o selo**
  (D-06) → preservar.
- `tests/test_consistencia_modos.py` — mesmo número entre Analisar/Garimpo/Ranking (Core Value). Os motores
  novos não podem divergir os 3 modos.
- `tests/test_vulc3_regressao.py` — capstone e2e (veredito começa com "VERIFICAR"); `tests/test_guardrails_fix06.py`.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`lentes.vpa(patrimonio_liquido, num_acoes)`** (`lentes.py:51`): base direta do RIM (VPA₀ + VP do excesso)
  e do NAV contábil (D-03) — pronto, sem recalcular.
- **`ddm.ddm_dois_estagios()`**: mecânica pura de PV de fluxo crescente em 2 estágios — reusável para o
  multi-estágio de crescimento (D-05) alimentando lucro/FCF em vez de dividendo, sem tocar o módulo.
- **`CompanyData.serie_lucro_normalizada()` + `normalizacao.py`**: lucro normalizado (winsor/mediana) da
  cíclica (D-04) já disponível.
- **`CompanyData.roe_valuation()` / `payout_valuation()` / `lpa_valuation()`**: sinais-síntese normalizados;
  os motores consomem sem recalcular (mantém consistência cross-modo — FIX-04).
- **`ingest/macro.selic_ciclo_para_capm`** (`:87`, Selic média 10a) — **já** é o rf do CAPM ao vivo; NÃO é a
  alavanca do D-01 (o RIM precisa de um Ke mais baixo que este CAPM, ver nota factual em D-01).
- **`g_alto` / `g_estável` / `g_fundamentos`** já calculados em `report.py` (`:118-149`): entrada pronta do
  multi-estágio de crescimento (D-05).

### Established Patterns
- **Registry arquétipo→motor** (`arquetipo.ARQUETIPO_MOTOR`): plugar os 4 motores é trocar `None` pelo id do
  motor + adicionar o cálculo no funil; padrão já estabelecido pela Fase 1.
- **Funil único de valuation** em `analisar_acao()`: os motores calculam num único ponto do funil, após o
  roteamento (`report.py:180-188`), não espalhados.
- **Firewall selo↛report** (testado): preservar — nesta fase o selo **não muda** (D-06); a suspensão continua
  do lado do `report`/veredito.
- **Fronteira CRU × valuation (FIX-04)**: usar os `*_valuation()` como número-síntese dos motores; os `*(ano)`
  crus são para tabela/screening.
- **Motores como funções puras config-driven** (espelham `ddm.py`/`lifecycle.py`): testáveis com golden,
  sem I/O.

### Integration Points
- **Registry:** `arquetipo.ARQUETIPO_MOTOR` — trocar os 4 `None` pelos ids dos motores novos (RIM/normalizado/
  DCF/NAV).
- **Cálculo:** funil de `report.py` após o roteamento (`:186`) — cada arquétipo dispara seu motor; o resultado
  vai para novos campos em `AnaliseAcao` (`:23`) e é **exibido** (D-06), sem alimentar o selo ainda.
- **Suspensão D-06:** a condição de suspensão do veredito primário (`report.py:240`, hoje `if a.motor_pendente:`)
  migra de `motor_pendente` para "selo ainda não consome o motor do arquétipo" (todo arquétipo não-DDM
  permanece suspenso) — no bloco de veredito de `report.py`, sem tocar `selo.py`.
- **Render mínimo:** `relatorio_markdown` (`report.py:~410`) e CLI exibem o intrínseco do motor do arquétipo +
  DDM rebaixado a "lente conservadora"; UX rica da bandeira/veredito é Fase 3.
</code_context>

<specifics>
## Specific Ideas

- **Caso-âncora ITUB4:** nesta fase o RIM produz ~R$40 (Ke normalizado + fade), **exibido** como o motor do
  arquétipo financeira; o DDM ao vivo (~R$16) aparece rotulado "lente conservadora". O selo passar a consumir
  o RIM (não mais estampar "evitar") fecha na Fase 3.
- **Tickers-âncora dos success criteria:** ITUB4 (RIM ~R$40), TAEE11 (regulada, DDM, idêntica), VALE3
  (cíclica, lucro normalizado), WEGE3 (crescimento, multi-estágio, sem zero/lixo).
- **DDM como "lente conservadora":** onde o DDM não é o primário do arquétipo, ele continua rodando e sendo
  exibido — só perde o status de motor primário. É o par natural de contraponto do ensemble da Fase 3.
</specifics>

<deferred>
## Deferred Ideas

- **SOTP real por segmento** (holding) → recusado nesta fase (D-03: NAV contábil simplificado); reconsiderar
  só se surgir fonte de dados de segmento confiável e custo-zero.
- **EV/EBITDA para cíclica** → não escolhido (D-04); pode virar refino se a dívida líquida/D&A da CVM se
  mostrarem confiáveis num backlog futuro.
- **DCF de FCF puro (com capex projetado)** para crescimento → não escolhido (D-05, depende de capex frágil);
  refino futuro se o capex da CVM vier limpo.
- **Selo consumir o motor do arquétipo (VER-01), ensemble + bandeira de divergência (ENS-01), guarda-corpos
  anti-aberração completos (SAN-01), dúvida honesta no caso-fronteira (VER-02)** → **Fase 3** por design
  (D-06). Nesta fase os motores só calculam/exibem.
- **Validação empírica / backtesting** de qual motor acerta por arquétipo → BACKTEST-01, explicitamente fora
  do milestone.

Nenhum dos itens acima altera o escopo da Fase 2 — a discussão permaneceu dentro do domínio.
</deferred>

---

*Phase: 2-Motores por Arquétipo*
*Context gathered: 2026-07-11*
