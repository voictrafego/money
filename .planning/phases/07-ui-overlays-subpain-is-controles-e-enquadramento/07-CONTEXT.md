# Phase 7: UI — overlays, subpainéis, controles e enquadramento — Context

**Gathered:** 2026-06-27 (discussão retomada após o saneamento do DDM — Phase 8)
**Status:** Ready for planning
**Source:** discuss-phase parcial (07-DISCUSS-CHECKPOINT.json, 2 áreas) + 3 áreas restantes decididas com o usuário em 2026-06-27.

<domain>
## Phase Boundary

A aba Analisar passa a desenhar os overlays técnicos no eixo de preço e os osciladores em
subpainéis dinâmicos, com controles para ligar/desligar e selecionar indicadores, marcadores de
evento nas datas exatas, tooltips de glossário, e um enquadramento que mantém o veredito
fundamentalista visivelmente decisório — tudo lendo `a.sinais` em modo **read-only** (`app.py`
não recalcula nada).

**Fora de escopo:** qualquer mudança no motor (engine/valuation/indicadores) — já entregue nas
Phases 4–6 (técnico) e 8 (saneamento DDM). Esta fase é só apresentação.
</domain>

<decisions>
## Implementation Decisions (LOCKED)

### Pré-tarefa — saneamento da degradação (CR-01/IN-02) [do checkpoint]
- **Regra HOLÍSTICA de degradação** (invariante única): se `timing_resumo` vazio (qualquer sinal
  "indisponivel"), então `matriz_leitura`, `alerta` e `timing_estado` colapsam coerentemente;
  nenhum campo derivado afirma algo sobre estado fabricado. Golden cobre série achatada E o caso
  só-de-força (ADX indisponível com MM200 ok). Inclui guard IN-02 (não dar append de linha vazia
  na CLI) e guarda da CLI por `not timing_resumo`.
- **UI quando a leitura degrada:** degradação graciosa (padrão GRAF-03) com mensagem explícita
  curta: *"Leitura técnica indisponível — histórico insuficiente para os indicadores"*.

### Controles — layout + granularidade [do checkpoint]
- **Granularidade HÍBRIDA:** 4 toggles por família (Tendência / Canais / Força / Momentum) +
  sub-opção onde faz sentido — Tendência: SMA⇄EMA + janelas 20/50/200; Canais: Donchian 20 vs 55,
  Bollinger on/off. Casa com o agrupamento do `SinaisTecnicos`.
- **Posição:** `st.expander("⚙️ Indicadores técnicos (consultivo)", expanded=False)` próximo ao
  gráfico. Off por padrão atende UI-06; controles perto do que afetam.
- Estado por sessão (`st.session_state`); o gráfico redesenha o subconjunto escolhido sem
  recomputar os sinais (UI-03).

### Arquitetura do gráfico (UI-01 + UI-02) [decidido 2026-06-27]
- **`make_subplots` dinâmico:** 1 painel de preço com overlays (MMs / Donchian / Bollinger) +
  N subpainéis criados **só** para os osciladores ativos (RSI / MACD / ADX), com `row_heights`
  proporcionais. Migra o `go.Figure` atual (`app.py:133-169`, `serie_precos` nominal,
  rangeselector, banda DDM via `add_hrect`) para `make_subplots`. Subpainel só existe quando o
  oscilador está ativo.

### Marcadores de evento (UI-04) [decidido 2026-06-27]
- **Marcadores no gráfico nas datas exatas + hover:** triângulos/setas para golden/death cross e
  rompimento de Donchian sobre a linha de preço, com tooltip nomeando o evento. Lê os eventos de
  `a.sinais` (datas exatas), sem recomputar.

### Enquadramento subordinado (UI-06) [decidido 2026-06-27, à luz do veredito saneado]
- **Técnico off por padrão, seção secundária:** veredito fundamentalista no topo é o selo
  decisório (incluindo o novo estado **"VERIFICAR"** do DDM saneado); bloco técnico off por padrão
  (expander), abaixo, linguagem consultiva ("timing", nunca "compre/venda").
- **Critério de aceite:** um leitor novo numa tela "VERIFICAR/cara + timing bullish" reconhece o
  fundamento como decisório, não o timing.
- **Nota pós-Phase 8:** o veredito agora é confiável (intrínseco do VULC3 deixou de ser 11–23× o
  preço; estado "VERIFICAR" existe). A matriz fundamento×técnico (Phase 6) é lida read-only e
  herda esse veredito saneado.

### Claude's Discretion
- Forma exata dos marcadores (símbolo/cor), `row_heights`, paleta dos overlays — seguir o estilo
  do gráfico atual.
- Texto exato dos tooltips de glossário (UI-05) — reusar o helper `h()` de `glossario.py`.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e decisões
- `.planning/ROADMAP.md` § Phase 7 (UI-01..06)
- `.planning/REQUIREMENTS.md` — UI-01..06
- `.planning/phases/06-integra-o-na-engine-composite-alerta-cli/06-CONTEXT.md` — D-01..D-13
  (composite/matriz/alerta consumidos read-only pela UI)
- `.planning/phases/06-integra-o-na-engine-composite-alerta-cli/06-REVIEW.md` — CR-01 + IN-02 (degradação)
- `.planning/phases/07-ui-overlays-subpain-is-controles-e-enquadramento/07-DISCUSS-CHECKPOINT.json`

### Código (fonte da verdade — read-only sobre a engine)
- `app.py:133-169` — gráfico Plotly atual (`go.Figure`, `serie_precos` nominal, rangeselector,
  banda DDM via `add_hrect`); migração para `make_subplots` nesta fase.
- `src/analista/core/indicators.py` — `SinaisTecnicos` (séries pd.Series por família: sma/ema,
  donchian/bb, adx/pdi/ndi, rsi/macd + sinais discretos + eventos com datas).
- `src/analista/report/report.py` — `a.sinais`, `timing_resumo`, `matriz_leitura`, `alerta`,
  `timing_estado` (já populados; UI só lê).
- `src/analista/glossario.py` — helper `h()` para tooltips (UI-05).
</canonical_refs>

<specifics>
## Specific Ideas
- Tudo via `st.session_state` para o estado dos toggles; nenhuma chamada de rede nova; `app.py`
  permanece read-only sobre a engine.
</specifics>

<deferred>
## Deferred Ideas
- Itens A–K do diagnóstico VULC3 = já resolvidos na Phase 8 (não eram da Phase 7).
- Recalcular a banda intrínseca mês-a-mês no gráfico (item I) — diferido na Phase 8, não entra aqui.
</deferred>

---

*Phase: 07-ui-overlays-subpain-is-controles-e-enquadramento*
*Context gathered: 2026-06-27*
