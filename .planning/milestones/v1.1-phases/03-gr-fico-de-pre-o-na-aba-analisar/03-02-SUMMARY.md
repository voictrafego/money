---
phase: 03-gr-fico-de-pre-o-na-aba-analisar
plan: 02
subsystem: ui
tags: [streamlit, plotly, graph_objects, render, fallback]

# Dependency graph
requires:
  - phase: 03-gr-fico-de-pre-o-na-aba-analisar
    provides: serie_precos (close 5a) em CompanyData + plotly instalado (Plano 01)
  - phase: 01-engine-consistencia
    provides: a.vmin/a.vmax do DDM expostos em AnaliseAcao (banda sobreposta)
provides:
  - Gráfico Plotly (linha de preço 5a + banda horizontal do valor intrínseco DDM) na Tela 1 (aba Analisar)
  - Fallback gracioso de série indisponível (D-05/GRAF-03) e de DDM não calculado sem banda (D-06)
affects: [app.py aba Analisar]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Plotly go.Figure + go.Scatter + add_hrect renderizado com st.plotly_chart(width=\"stretch\") — render read-only que lê c.serie_precos e a.vmin/a.vmax já em escopo, sem passar pela engine"]

key-files:
  created:
    - .planning/phases/03-gr-fico-de-pre-o-na-aba-analisar/03-02-SUMMARY.md
  modified:
    - app.py

key-decisions:
  - "Banda horizontal plana via fig.add_hrect(y0=vmin, y1=vmax) — uma chamada, estende ao infinito em x, opacity 0.12 para 'banda sutil' (D-01/D-02/D-04)"
  - "Render lê c.serie_precos e a.vmin/a.vmax direto no escopo da Tela 1 — a série NÃO atravessa AnaliseAcao (menor superfície, golden tests intocados)"
  - "import plotly.graph_objects as go só no topo de app.py (camada UI); engine permanece sem plotly (Pitfall 4)"
  - "st.plotly_chart(fig, width=\"stretch\") em vez de use_container_width (deprecado) — Pitfall 2"

patterns-established:
  - "Gráfico interativo na UI = go.Figure read-only que consome campos já em escopo, guardado pelas mesmas sentinelas None que o resto da Tela 1"

requirements-completed: [GRAF-01, GRAF-02, GRAF-03]

# Metrics
duration: 6min
completed: 2026-06-23
---

# Phase 3 Plan 02: Render do gráfico de preço + banda DDM na aba Analisar Summary

**A aba "Analisar" agora renderiza, no topo (antes dos sub-tabs), um gráfico Plotly da evolução do preço de close de 5 anos (`c.serie_precos`) com a banda horizontal do valor intrínseco do DDM (`a.vmin`–`a.vmax`) sobreposta via `add_hrect`, com zoom/hover nativos e dois fallbacks graciosos (série indisponível → aviso sem quebrar; DDM None → só a linha).**

## Performance

- **Duration:** ~6 min (inclui checkpoint human-verify)
- **Tasks:** 3 (Task 3 = checkpoint human-verify, aprovado pelo usuário)
- **Files modified:** 1 (`app.py`)

## Accomplishments
- `import plotly.graph_objects as go` adicionado ao topo de `app.py` (camada UI; engine permanece sem plotly).
- Bloco de render inserido ENTRE o loop de alertas e `tab1, tab2, tab3 = st.tabs([...])` (D-03) — `st.tabs` não foi movido.
- Título de seção `st.markdown("**Evolução do preço (5 anos) vs. valor intrínseco**", help=h("valor_intrinseco"))` no estilo dos cabeçalhos existentes.
- `go.Figure` + `go.Scatter(x=serie.index, y=serie.values, mode="lines")` com `hovertemplate` formatando data (`%d/%m/%Y`) e `R$ %{y:.2f}` — zoom/hover nativos do Plotly (GRAF-01).
- Banda intrínseca via `fig.add_hrect(y0=a.vmin, y1=a.vmax, line_width=0, fillcolor="green", opacity=0.12, annotation_text="Valor intrínseco (DDM)")` — horizontal plana, guardada por `if a.vmin is not None and a.vmax is not None` (GRAF-02 / D-01 / D-02 / D-06).
- `st.plotly_chart(fig, width="stretch")` — sem `use_container_width` deprecado (Pitfall 2).
- Fallback `if serie is None or len(serie) == 0` → `st.info` espelhando o aviso "preço atual indisponível", sem desenhar o gráfico; a aba segue para `st.tabs` (D-05 / GRAF-03).
- Suíte completa verde (62 passed), `tests/` intocado, plotly importável (Task 2; trava de regressão SC #4).
- Checkpoint human-verify aprovado pelo usuário: gráfico aparece com linha+banda, zoom/hover funcionam, sem warnings de deprecação nem `UnserializableReturnValueError` no terminal.

## Task Commits

1. **Task 1: Render Plotly da série 5a + banda DDM na Tela 1, com os dois fallbacks** — `fdc6802` (feat)
2. **Task 2: Confirmar pytest verde e app importa com plotly** — verification-only (sem edição de source; 62 passed, tests intocados, plotly importável)
3. **Task 3: Checkpoint human-verify** — aprovado pelo usuário (verificação visual no navegador)

**Plan metadata:** docs commit (este SUMMARY + STATE.md + ROADMAP.md)

## Files Created/Modified
- `app.py` — `import plotly.graph_objects as go` no topo; bloco de render Plotly (linha de preço + banda DDM + fallbacks) entre o loop de alertas e `st.tabs` na Tela 1.

## Decisions Made
- Render lê `c.serie_precos` e `a.vmin/a.vmax` direto no escopo da Tela 1 (ambos já presentes); a série não atravessa `AnaliseAcao` — menor superfície de mudança, golden tests imunes.
- `add_hrect` em vez de série de vmin/vmax por data ou de dois `add_hline`: uma chamada, faixa preenchida plana ao longo de todo o eixo X (D-02), `opacity=0.12` = "banda sutil" (D-04). Sem recálculo de intrínseco histórico.
- Cor `#1f77b4` para a linha, banda verde `opacity=0.12`, altura 380, annotation top-left — discrição do executor (D-04 / Assumptions A2 da research).
- `width="stretch"` no chart novo (não replicar o `use_container_width` deprecado que o resto do `app.py` ainda usa — fora de escopo mudar os demais).

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs
None — o gráfico é alimentado por `c.serie_precos` (dado real do Yahoo preservado no Plano 01) e `a.vmin/a.vmax` (DDM real da engine). Nenhum valor hardcoded/placeholder.

## Issues Encountered
None.

## User Setup Required
None — `plotly>=6.0` já está instalado no venv (Plano 01); em outros ambientes basta `pip install -r requirements.txt`.

## Next Phase Readiness
- GRAF-01/02/03 entregues end-to-end (backbone no Plano 01 + render neste plano); Phase 3 (último plano do marco v1.1) completo.
- A degradação graciosa GRAF-03 está coberta pelos dois fallbacks (série None/vazia → aviso; DDM None → só a linha).

## Self-Check: PASSED

---
*Phase: 03-gr-fico-de-pre-o-na-aba-analisar*
*Completed: 2026-06-23*
