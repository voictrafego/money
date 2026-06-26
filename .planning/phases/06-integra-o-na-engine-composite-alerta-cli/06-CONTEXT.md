# Phase 6: Integração na engine + composite + alerta + CLI - Context

**Gathered:** 2026-06-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Os sinais técnicos calculados pelo módulo puro `core/indicators.py` (Phase 5) passam a viver em
`AnaliseAcao.sinais`, populados em `report.analisar_acao` — ponto único compartilhado por CLI e UI.
A partir desse campo, a fase entrega quatro coisas:

1. Um **resumo de "timing de entrada" composite** consultivo, em linguagem natural PT, com três
   estados macro — **tendência de alta / sem tendência / atenção** (TIMING-01).
2. Uma **matriz fundamento×técnico** que cruza o veredito DDM já calculado (`a.veredito`/`vmin`/`vmax`)
   com o estado técnico, **lendo sem recalcular nem sobrescrever** o fundamento (TIMING-02).
3. Um **alerta de reverificação** ("reveja os fundamentos") ao rompimento de tendência, enquadrado
   como gatilho de reolhar os números — nunca como ordem de venda (TIMING-03).
4. Uma **base temporal diário/semanal** (default semanal) para o read técnico; o gráfico visual
   permanece diário (TIMING-04).

Tudo espelhado na CLI via uma seção "Sinais técnicos (consultivos)" em `relatorio_markdown` (CLI-01),
com as regras de desempate do composite travadas por golden test (TEST-06) e os 64 golden tests de
valuation continuando verdes (TEST-07).

**Fora de escopo (Phase 7):** overlays no eixo de preço, osciladores em subpainéis, toggles de
ligar/desligar/selecionar indicadores, marcadores de evento no gráfico e tooltips de glossário. A
engine desta fase é consumida em modo read-only pela UI da Phase 7.

</domain>

<decisions>
## Implementation Decisions

### Lógica do composite de timing (TIMING-01 / TEST-06)
- **D-01:** **Árvore de decisão explícita, não voto ponderado.** A **MM200 dá a direção** (posição
  preço×MM200) e o **ADX confirma a força**: só vira "tendência de alta" quando o preço está acima da
  MM200 **e** o ADX confirma tendência (forte). Abaixo da MM200 ou ADX fraco puxa o estado para "sem
  tendência" / "atenção". Decisão explícita e travável por teste (rejeitados: voto ponderado das 4
  famílias; ADX-primeiro-como-gate puro).
- **D-02:** **Caso-limite TEST-06 — preço ACIMA da MM200 mas ADX < 20 → estado "sem tendência"
  (lateral).** O ADX fraco vence: sem força confirmada não é timing de entrada, mesmo com viés de alta
  pela MM200. Conservador e coerente com o método (não entra em rompimento não confirmado). Este é o
  caso-limite canônico que o golden test de desempate deve congelar.
- **D-03:** **Momentum (RSI/MACD) é matiz fino dentro do estado, não muda o estado.** A tendência
  (MM200+ADX) define o estado macro; RSI/MACD refinam a frase consultiva dentro dele (ex.: "alta, mas
  sobrecomprado — pode esperar um pullback"). Não entra no voto que decide alta/sem tendência/atenção.

### Matriz fundamento×técnico (TIMING-02)
- **D-04:** **Frase curada por célula**, não template composicional. Cada combinação relevante
  (veredito DDM barato/justo/caro × estado técnico alta/sem tendência/atenção) tem uma frase consultiva
  pré-escrita, travável por golden test. **O fundamento sempre lidera a frase** e a parte técnica entra
  subordinada — garante por construção que o veredito DDM é decisório (alinha com UI-06 da Phase 7).
- **D-05:** Célula **BARATO + ATENÇÃO** (subavaliada que perdeu a tendência) → leitura "atrativa, mas
  reverifique antes": *"Fundamentalmente descontada, porém o preço perdeu a tendência — confirme que os
  fundamentos seguem intactos antes de entrar."* Esta célula **liga diretamente ao alerta de
  reverificação** (TIMING-03).
- **D-06:** Célula **CARO + ALTA** (sobreavaliada subindo forte) → leitura "o método não paga caro":
  *"Tecnicamente em alta, porém acima do valor intrínseco — o método não compra caro; aguarde um preço
  melhor."* O fundamento veta a euforia técnica.

### Alerta de reverificação (TIMING-03)
- **D-07:** **Gatilho = OR dos três sinais de baixa** — perda da MM200 **ou** death cross (MM50×MM200)
  **ou** rompimento da mínima do Donchian. Qualquer um já pede reolhar os fundamentos (mais sensível,
  pega a perda de tendência cedo). É o conjunto exato citado no ROADMAP/REQ. (Rejeitados: só MM200;
  exigir 2 de 3.)
- **D-08:** **Alerta dispara sempre que rompe, independente do veredito DDM.** Não é condicionado a
  "era barata/justa". Simples, previsível e fácil de travar por teste; o texto da matriz (D-04) já
  contextualiza com o fundamento.
- **D-09:** **Alerta único consolidado** quando mais de um gatilho aciona — uma mensagem "reveja os
  fundamentos" listando quais gatilhos dispararam. Evita repetição e mantém o enquadramento consultivo
  num lugar só. **Frasing nunca soa como ordem de venda** — sempre "reverifique os fundamentos".

### Base temporal diário/semanal (TIMING-04)
- **D-10:** **Modo "semanal" = resample do OHLC para candles semanais e recálculo dos indicadores
  nessa série** (não "indicadores diários checados só na sexta"). Menos ruído, menos falsos
  rompimentos — é o sentido clássico de "tendência semanal". Exige golden test próprio para o resample.
- **D-11:** **A base escolhida afeta todo o read técnico — resumo de timing (TIMING-01) E alerta
  (TIMING-03)** — para ficarem coerentes entre si. Apenas o gráfico/overlays (Phase 7) permanecem
  diários.
- **D-12:** **A escolha diário/semanal vive em `cfg`** (parâmetro canônico, **default "semanal"**) —
  ponto único CLI/UI, espelhando o padrão de parâmetros dos indicadores. A CLI usa o default; o toggle
  da UI (Phase 7) sobrescreve via `st.session_state`. (Rejeitado: argumento explícito de `analisar_acao`.)

### CLI (CLI-01)
- **D-13:** A seção "Sinais técnicos (consultivos)" em `relatorio_markdown` **espelha o mesmo read da
  engine** — resumo composite + leitura da matriz + alerta de reverificação. Paridade CLI↔UI é gratuita
  porque ambos consomem `a.sinais`/`analisar_acao` (ponto único). Formato exato da seção é discrição do
  planner, seguindo o padrão das demais seções de `relatorio_markdown`.

### Claude's Discretion
- Nomes exatos dos campos novos em `AnaliseAcao` (ex.: `sinais`, `timing_resumo`, `alerta_reverificacao`)
  e a forma do(s) novo(s) dataclass(es) do composite — desde que read-only sobre o fundamento e
  testáveis por golden.
- Limiares exatos de ADX no composite (ex.: "forte" ≥ 25, "sem tendência" < 20) — reusar os já
  definidos em `indicators._forca` (`forca_adx`) em vez de redefinir.
- Texto exato das células da matriz não cobertas explicitamente em D-05/D-06 (as combinações
  não-conflitantes), mantendo fundamento-primeiro e tom consultivo.
- Chaves/defaults de `cfg` para a base temporal (ex.: `base_temporal="semanal"`, regra do resample
  `W-FRI`) — desde que canônicas e documentadas.
- Formato exato da seção CLI e tratamento de histórico curto/`ohlc=None` (degradação graciosa
  espelhando o padrão GRAF-03/DATA-03 já existente).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e roadmap do marco
- `.planning/ROADMAP.md` § "Phase 6: Integração na engine + composite + alerta + CLI" — goal,
  depends-on (Phase 5), success criteria 1-5 (composite, matriz read-only, alerta, base temporal, CLI+TEST-06).
- `.planning/REQUIREMENTS.md` — TIMING-01, TIMING-02, TIMING-03, TIMING-04, CLI-01, TEST-06 (Phase 6);
  TEST-07 (invariante contínuo 4-7: 64 golden tests verdes).
- `.planning/PROJECT.md` — Key Decisions: "técnica é consultiva, nunca altera o veredito";
  "rompimento dispara reverificação, não venda"; "app.py read-only". Core Value (fidelidade ao livro).
- `.planning/STATE.md` § "Accumulated Context" — decisões de pesquisa v1.2 (`a.sinais` em
  `analisar_acao` = ponto único CLI/UI; SinaisTecnicos nested por família; cross/posição sobre SMA).

### Entrada da engine (Phase 5 — já entregue, NÃO modificar)
- `src/analista/core/indicators.py` — `SinaisTecnicos` (nested: `tendencia`/`canais`/`forca`/`momentum`)
  e `calcular(ohlc, cfg) -> SinaisTecnicos`. Sinais discretos consumidos pelo composite:
  `tendencia.posicao_mm200` ("acima"/"abaixo"), `tendencia.cruzamento` ("golden_cross"/"death_cross"/"nenhum"),
  `canais.rompimento_donchian` ("nova_maxima"/"perda_minima"/"nenhum"), `forca.forca_adx`
  ("sem_tendencia"/"forte"/"neutro"), `momentum.nivel_rsi`, `momentum.cruzamento_macd`.
- `src/analista/core/fundamentals.py` — `CompanyData.ohlc_ajustado` (split-adjusted, input dos
  indicadores) e `CompanyData.ohlc` (nominal). Input do resample semanal (D-10).
- `.planning/phases/05-motor-de-indicadores-puro/05-CONTEXT.md` — contrato D-01..D-04 do SinaisTecnicos.

### Ponto de integração (a MODIFICAR nesta fase)
- `src/analista/report/report.py` — `AnaliseAcao` (dataclass, linha ~20: ganha campo `sinais` + campos
  do composite/alerta); `analisar_acao(c, cfg)` (linha ~43: chama `indicators.calcular` e deriva o
  composite/matriz/alerta, lendo `a.veredito`/`a.vmin`/`a.vmax` já calculados ~linha 117-124);
  `relatorio_markdown(c, a, cfg)` (linha ~155: nova seção "Sinais técnicos (consultivos)", CLI-01).

### Padrão de teste a espelhar
- `tests/test_ddm.py`, `tests/test_multiples.py` — padrão golden do projeto (fixtures + asserts).
  TEST-06 trava as regras de desempate do composite (caso-limite D-02). TEST-07: 64 golden tests
  de valuation verdes ao final.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `report.analisar_acao(c, cfg)` — ponto único onde `a.sinais = indicators.calcular(c.ohlc_ajustado, cfg)`
  deve ser populado; CLI e UI herdam paridade de graça.
- `a.veredito` / `a.vmin` / `a.vmax` (report.py ~117-124) — já calculados pelo DDM; a matriz fundamento×técnico
  os LÊ, nunca recalcula (TIMING-02). Veredito tem 3 estados: SUBAVALIADA / NO INTERVALO / SOBREAVALIADA.
- `indicators._forca` (`forca_adx`) — já classifica força do ADX em "sem_tendencia"/"forte"/"neutro";
  reusar esses limiares no composite em vez de redefinir.

### Established Patterns
- `cfg` como home canônica de parâmetros (indicadores já vivem lá) → base temporal diário/semanal segue (D-12).
- Degradação graciosa GRAF-03/DATA-03: quando `ohlc`/histórico vem vazio, campos `=None` sem quebrar a aba.
- `relatorio_markdown` monta seções via lista `L.append(...)` — a seção CLI segue esse formato.

### Integration Points
- `AnaliseAcao` dataclass ganha campos novos (sinais + composite + alerta) — aditivo, read-only sobre o fundamento.
- Resample semanal (D-10) opera sobre `CompanyData.ohlc_ajustado` antes de chamar `indicators.calcular`.

</code_context>

<specifics>
## Specific Ideas

- **Três estados macro do composite:** "tendência de alta" / "sem tendência" / "atenção".
- **Frases-âncora da matriz já definidas:**
  - Barato + atenção/queda → "Fundamentalmente descontada, porém o preço perdeu a tendência — confirme
    que os fundamentos seguem intactos antes de entrar."
  - Caro + alta → "Tecnicamente em alta, porém acima do valor intrínseco — o método não compra caro;
    aguarde um preço melhor."
- **Alerta sempre na voz "reveja/reverifique os fundamentos"** — nunca "venda".
- **Default da base temporal = semanal** (REQ TIMING-04); resample sugerido `W-FRI` (fechamento sexta).
- **Caso-limite de teste canônico (TEST-06):** acima da MM200 + ADX < 20 → "sem tendência".

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (Overlays/subpainéis/toggles/tooltips de indicador → Phase 7;
divergências RSI/MACD MOM-03 e outros indicadores já deferidos no marco v1.2.)

</deferred>

---

*Phase: 06-integra-o-na-engine-composite-alerta-cli*
*Context gathered: 2026-06-26 via /gsd-discuss-phase*
