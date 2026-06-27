---
phase: 07-ui-overlays-subpain-is-controles-e-enquadramento
plan: 04
subsystem: ui
tags: [app, session-state, controles, expander, enquadramento, consultivo, degradacao, tooltips]

# Dependency graph
requires:
  - phase: 07-ui-overlays-subpain-is-controles-e-enquadramento (07-01)
    provides: "report.analisar_acao popula timing_resumo/matriz_leitura/alerta_reverificacao; degradação holística (timing_resumo vazio colapsa matriz)"
  - phase: 07-ui-overlays-subpain-is-controles-e-enquadramento (07-02)
    provides: "glossário técnico: 11 chaves tec_* lidas por h('tec_*')"
  - phase: 07-ui-overlays-subpain-is-controles-e-enquadramento (07-03)
    provides: "grafico.estado_padrao() (técnico OFF) e grafico.leitura_tecnica_disponivel(sinais)"
provides:
  - "app.py: expander '⚙️ Indicadores técnicos (consultivo)' (expanded=False) com 4 famílias híbridas, estado em st.session_state['tec_estado']"
  - "app.py: seção consultiva subordinada (timing/matriz/alerta) abaixo do gráfico/controles + mensagem de degradação graciosa"
  - "Contrato de estado dos controles pronto para o Plan 05 consumir (desenho dos overlays/subpainéis)"
affects: [07-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Controles capturam estado em st.session_state com as MESMAS chaves de grafico.estado_padrao() (sem reimplementar o contrato no app.py)"
    - "Enquadramento UI-06: fundamento no banner colorido (decisório), técnico em markdown/caption discreto (consultivo); nunca st.success/error na seção técnica"
    - "app.py read-only sobre a engine: só lê a.* e escreve session_state; nenhum cálculo do método"

key-files:
  created: []
  modified:
    - app.py

key-decisions:
  - "Controles HÍBRIDOS por família (toggle on/off + sub-opções): Tendência (SMA⇄EMA + multiselect janelas 20/50/200), Canais (Donchian on/off + radio 20/55 + Bollinger), Força (ADX), Momentum (RSI + MACD)"
  - "Os widgets só CAPTURAM estado (Plan 04); o desenho de overlays/subpainéis a partir do estado é o Plan 05 — escopo mantido estrito"
  - "Seção técnica renderizada como markdown/caption (não banner) p/ mitigar T-07-06: o técnico nunca passa como veredito decisório"
  - "Degradação holística (Plan 01): timing_resumo vazio ⇒ caption 'Leitura técnica indisponível — histórico insuficiente para os indicadores', sem quebrar a aba"

patterns-established:
  - "esc_md() aplicado em timing_resumo/matriz_leitura/alerta antes do markdown (consistente com o resto da aba)"

requirements-completed: [UI-03, UI-05, UI-06]

# Metrics
duration: 8min
completed: 2026-06-27
---

# Phase 7 Plan 04: Controles técnicos (session_state) + enquadramento subordinado Summary

**O app.py ganhou o ANDAIME da seção técnica: um expander de controles híbridos (UI-03) cujo estado vive em `st.session_state['tec_estado']` (chaves de `grafico.estado_padrao()`), com tooltips de glossário (UI-05), e o enquadramento subordinado (UI-06) — veredito fundamentalista decisório no topo, leitura técnica consultiva e secundária abaixo, com degradação graciosa quando o read técnico não está disponível.**

## Performance

- **Duration:** ~8 min
- **Completed:** 2026-06-27
- **Tasks:** 2/2
- **Files modified:** 1 (app.py)

## Accomplishments
- Import `from analista import grafico` + `st.session_state.setdefault("tec_estado", grafico.estado_padrao())` (técnico OFF por padrão).
- Expander `⚙️ Indicadores técnicos (consultivo)` (`expanded=False`) com 4 colunas/famílias e sub-opções híbridas do CONTEXT; cada widget escreve nas chaves de `estado_padrao()` e recebe `help=h("tec_*")` (paridade de tooltip).
- Seção consultiva SECUNDÁRIA abaixo do gráfico/controles: `Timing (consultivo)` + `matriz_leitura` (fundamento-primeiro) + `alerta_reverificacao` via `st.info` (voz de reverificação, nunca venda), com `help=h("tec_timing")`.
- Degradação holística: `timing_resumo` vazio ⇒ `st.caption("Leitura técnica indisponível — histórico insuficiente para os indicadores")` sem quebrar a aba.
- Veredito fundamentalista (incl. "VERIFICAR" no ramo `st.warning`) intacto no topo como selo decisório.
- Suíte completa: 148 testes verdes (invariante TEST-07 preservada).

## Task Commits

1. **Task 1: expander de controles técnicos com estado em session_state (UI-03/UI-05)** - `f647064` (feat)
2. **Task 2: enquadramento subordinado — seção consultiva + degradação (UI-06)** - `9ef0409` (feat)

## Files Created/Modified
- `app.py` - Import de `grafico`; init de `st.session_state['tec_estado']`; expander de controles híbridos com tooltips; seção consultiva subordinada (timing/matriz/alerta) + caption de degradação. app.py permanece read-only sobre a engine.

## must_haves — atendidas
- Veredito fundamentalista (incl. "VERIFICAR") segue no topo; bloco técnico é secundário, off por padrão, consultivo (UI-06). ✓
- `st.expander('⚙️ Indicadores técnicos (consultivo)', expanded=False)` com 4 toggles por família + sub-opções, estado em `st.session_state` (UI-03). ✓
- Cada controle/indicador com tooltip `?` via `help=h('tec_*')` (UI-05). ✓
- Degradação: "Leitura técnica indisponível — histórico insuficiente para os indicadores" sem quebrar a aba. ✓

## Threat model — atendido
- T-07-06 (técnico passar como veredito): mitigado — seção técnica em markdown/caption, veredito mantém o banner colorido. ✓
- T-07-07 (session_state parcial): aceito — estado iniciado por `estado_padrao()`; `grafico._merge` tolera estado parcial; widgets só sobrescrevem chaves conhecidas. ✓

## Deviations from Plan
None - plano executado exatamente como escrito.

## Known Stubs
Nenhum. Os controles capturam estado real (consumido pelo Plan 05); a seção consultiva lê campos reais da engine (`a.timing_resumo`/`a.matriz_leitura`/`a.alerta_reverificacao`). O não-desenho de overlays neste plano é intencional e por escopo — o Plan 05 liga o gráfico ao estado já capturado aqui.

## Self-Check: PASSED
- Arquivo: app.py modificado (expander + seção consultiva presentes).
- Commits: f647064, 9ef0409 — ambos no histórico.
</content>
</invoke>
