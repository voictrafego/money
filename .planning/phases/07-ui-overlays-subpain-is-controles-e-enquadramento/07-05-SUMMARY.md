---
phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
plan: 05
subsystem: ui
tags: [app, make_subplots, overlays, subpaineis, marcadores, split-alinhamento, fresh-reader, ui-06]

# Dependency graph
requires:
  - phase: 07-ui-overlays-subpain-is-controles-e-enquadramento (07-03)
    provides: "grafico.py puro: overlays_preco/subpaineis_ativos (SubpainelSpec série+níveis), layout_subplots, marcadores_eventos, leitura_tecnica_disponivel"
  - phase: 07-ui-overlays-subpain-is-controles-e-enquadramento (07-04)
    provides: "st.session_state['tec_estado'] (chaves de grafico.estado_padrao()) capturado pelos controles híbridos"
  - phase: 07-ui-overlays-subpain-is-controles-e-enquadramento (07-01)
    provides: "SinaisTecnicos.close (close split-adjusted) p/ as datas exatas dos marcadores"
provides:
  - "app.py: gráfico migrado de go.Figure para make_subplots dinâmico — row 1 preço + banda DDM + rangeselector preservados, overlays no preço (UI-01), subpainéis só dos osciladores ativos via SubpainelSpec (UI-02), marcadores nas datas exatas (UI-04)"
  - "Redesenho-sem-recompute observável (UI-03): slot do gráfico reservado no topo, preenchido após os controles ⇒ toggle redesenha no mesmo rerun, sem lag de 1 clique"
  - "Enquadramento UI-06 aprovado no fresh-reader test (checkpoint humano), incl. alinhamento split ITSA4 (CR-01/DATA-02) e degradação graciosa"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "make_subplots dirigido inteiramente pelos specs do módulo puro: app.py itera spec.series e spec.referencias — sem mapeamento nome→série nem níveis (20/25,30/70,0) hardcoded"
    - "Slot do gráfico reservado via st.container() no topo e PREENCHIDO depois dos controles ⇒ o render lê o tec_estado já atualizado no mesmo rerun (UI-03 sem lag)"
    - "app.py read-only sobre a engine: lê a.sinais/a.sinais.close, nunca recomputa indicador"

key-files:
  created: []
  modified:
    - app.py

key-decisions:
  - "[07-05] Slot do gráfico reservado com st.container() no topo e preenchido APÓS os controles rodarem no mesmo rerun (Rule-3): o render consome o st.session_state['tec_estado'] recém-atualizado ⇒ toggle redesenha sem lag de 1 clique, preservando a ordem visual (gráfico no topo, controles/seção consultiva abaixo) e a observabilidade do UI-03"
  - "[07-05] Alinhamento split (CR-01/DATA-02) é tradeoff travado, não bug: preço NOMINAL (c.serie_precos) para casar com a banda DDM; overlays/marcadores leem a.sinais split-adjusted — descolamento vertical na época do split em ITSA4 é esperado; datas dos marcadores caem no evento, sem deslocamento temporal (validado no checkpoint)"
  - "[07-05] Degradação: not leitura_tecnica_disponivel(a.sinais) ou specs/overlays/marcadores vazios ⇒ só o painel de preço + banda (paridade com o gráfico anterior), sem subpainéis e sem exceção"

patterns-established:
  - "height do gráfico proporcional ao nº de rows (preço + N subpainéis ativos)"

requirements-completed: [UI-01, UI-02, UI-04]

# Metrics
duration: continuation
completed: 2026-06-27
---

# Phase 7 Plan 05: make_subplots dinâmico — overlays + subpainéis + marcadores + fresh-reader UI-06 Summary

**O gráfico de preço migrou de `go.Figure` para `make_subplots` dinâmico dirigido pelas funções puras do `grafico.py`: row 1 preserva preço NOMINAL + banda DDM + rangeselector e ganha os overlays ativos (MMs/Donchian/Bollinger, UI-01) e os marcadores de evento nas datas exatas (golden/death cross e rompimentos, UI-04); cada oscilador ligado (RSI/MACD/ADX) vira um subpainel montado a partir do SubpainelSpec — série(s) + níveis de referência — sem nada hardcoded no app.py (UI-02). O redesenho-sem-recompute é observável (UI-03) e o enquadramento foi aprovado no fresh-reader test do UI-06, incluindo o alinhamento com split do ITSA4 e a degradação graciosa.**

## Performance

- **Duration:** continuation (agente fresh pós-checkpoint aprovado)
- **Completed:** 2026-06-27
- **Tasks:** 3/3 (Tasks 1-2 já committados; Task 3 checkpoint humano APROVADO)
- **Files modified:** 1 (app.py)

## Accomplishments
- Import `from plotly.subplots import make_subplots`; bloco do gráfico reescrito como `make_subplots(rows, cols=1, shared_xaxes=True, row_heights=...)` com `rows, heights = grafico.layout_subplots(len(specs))`.
- Row 1: preço (`c.serie_precos`, mesmo trace/estilo), `add_hrect` da banda DDM (`a.vmin`/`a.vmax`), rangeselector e guarda de série indisponível preservados; overlays de `grafico.overlays_preco(estado, a.sinais)` como go.Scatter (UI-01).
- Subpainéis dinâmicos: cada `SubpainelSpec` de `grafico.subpaineis_ativos(estado, a.sinais)` vira um row — itera `spec.series` (go.Scatter) e desenha `add_hline` por nível em `spec.referencias`; nenhum mapeamento nome→série nem nível hardcoded (UI-02).
- Marcadores de evento: `grafico.marcadores_eventos(a.sinais, a.sinais.close)` ⇒ go.Scatter de markers no row 1, triângulo-up verde (golden_cross/nova_maxima) / down vermelho (death_cross/perda_minima), hover nomeando evento e data (UI-04).
- Degradação: técnico OFF/indisponível ⇒ só o painel de preço + banda (paridade com o gráfico anterior), sem exceção.
- Suíte completa: **148 testes verdes** (invariante TEST-07 preservada — app.py não toca a engine).
- Checkpoint humano (Task 3) APROVADO: overlays/subpainéis/marcadores, redesenho sem recoleta, alinhamento split ITSA4 (CR-01/DATA-02) e fresh-reader UI-06 (fundamento decisório, técnico consultivo) confirmados.

## Task Commits

1. **Task 1: make_subplots dinâmico — overlays + subpainéis (UI-01/UI-02)** - `4f86b59` (feat)
2. **Task 2: marcadores de evento nas datas exatas (UI-04)** - `e837b21` (feat)
3. **Task 3: checkpoint:human-verify (fresh-reader UI-06 + split ITSA4 + degradação)** - APROVADO pelo usuário ("approved")

## Files Created/Modified
- `app.py` - Gráfico migrado para make_subplots dinâmico (overlays, subpainéis via SubpainelSpec, marcadores), slot reservado via st.container() preenchido após os controles. Read-only sobre a engine.

## must_haves — atendidas
- Migração go.Figure → make_subplots: 1 painel de preço (banda DDM preservada) + N subpainéis só dos osciladores ativos. ✓
- Overlays ativos desenhados no eixo de preço via `grafico.overlays_preco` (UI-01). ✓
- Subpainéis montados a partir do SubpainelSpec (série(s)+níveis) — app.py não hardcoda nome→série nem níveis. ✓
- Marcadores nas datas exatas com hover nomeando o evento (UI-04). ✓
- Toggles redesenham o subconjunto sem recomputar a engine (UI-03 observável). ✓
- Fresh-reader: fundamento reconhecido como decisório numa tela "VERIFICAR/cara + timing bullish" (UI-06). ✓

## Threat model — atendido
- T-07-08 (timing parecer ordem de compra/venda): mitigado — marcadores/subpainéis consultivos; veredito mantém o banner decisório; fresh-reader checkpoint validou UI-06. ✓
- T-07-09 (a.sinais/close vazios — Yahoo instável): mitigado — guarda de série indisponível preservada + degradação para só-preço sem exceção. ✓

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Slot do gráfico reservado no topo, preenchido após os controles**
- **Found during:** Task 1 (integração render × estado dos toggles)
- **Issue:** No fluxo natural do Streamlit, o bloco do gráfico roda ANTES dos widgets de controle do mesmo rerun; o gráfico leria um `st.session_state['tec_estado']` defasado (estado do clique anterior), causando lag de 1 clique a cada toggle — o que quebraria a observabilidade do UI-03.
- **Fix:** Reservar o slot do gráfico no topo com `st.container()` (`grafico_box`) e PREENCHÊ-LO depois que os controles abaixo já escreveram em `st.session_state['tec_estado']`. Assim o render consome o estado recém-atualizado no MESMO rerun, preservando a ordem visual (gráfico no topo, controles/seção consultiva abaixo) sem lag.
- **Files modified:** app.py
- **Commit:** `4f86b59`

## Known Stubs
Nenhum. O gráfico consome estado real (`tec_estado`) e specs reais do módulo puro; overlays/subpainéis/marcadores leem campos reais de `a.sinais`/`a.sinais.close`. Fecha a cadeia técnica da fase (Plans 01-04 → 05).

## Self-Check: PASSED
- Arquivo: app.py modificado (make_subplots, overlays_preco, subpaineis_ativos, marcadores_eventos presentes).
- Commits: 4f86b59, e837b21 — ambos no histórico (`git log --grep="07-05"`).
- Testes: 148 passando.
