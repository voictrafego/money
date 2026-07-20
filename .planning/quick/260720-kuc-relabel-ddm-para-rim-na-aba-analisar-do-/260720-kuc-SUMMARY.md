---
phase: quick
plan: 260720-kuc
subsystem: ui
tags: [streamlit, app, copy, relabel, rim, ddm, dead-code]

requires:
  - phase: 13-eng
    provides: "RIM único como motor; campos do ensemble removidos de AnaliseAcao"
provides:
  - "Manchete do intrínseco na aba Analisar exibe 'Intrínseco (RIM)' (bug do rótulo corrigido)"
  - "Código morto do ensemble (gated por campos removidos do dataclass) removido de app.py"
  - "Copy visível relabelada DDM→RIM onde nomeia o motor atual; DDM preservado onde é a lente genuína"
affects: [ui, analisar-tab]

tech-stack:
  added: []
  patterns: ["Rótulo não pode mentir: RIM só onde é o motor; DDM só onde é a lente/fórmula real"]

key-files:
  created: []
  modified: [app.py]

key-decisions:
  - "Rótulo estático 'Intrínseco (RIM)' (curto para st.metric) em vez de a.motor_rotulo (longo)"
  - "ddm_inaplicavel: bloco mantido (campo existe), cláusula stale 'Intrínseco (DDM) não é exibido' removida"
  - "Sub-tab 'Valuation (DDM)' e CFG[ddm] mantidos como DDM — a lente/fórmula ainda existe de fato"

patterns-established:
  - "Subtração de código gated por getattr(a, campo_removido, False) → sempre-False → morto"

requirements-completed: [UI-RELABEL-RIM]

duration: 12min
completed: 2026-07-20
---

# Phase quick Plan 260720-kuc: Relabel DDM→RIM na aba Analisar Summary

**Manchete do intrínseco corrigida para "Intrínseco (RIM)", código morto do ensemble removido de app.py, e copy visível relabelada DDM→RIM onde nomeia o motor atual — DDM preservado onde é a lente/fórmula genuína.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-20
- **Completed:** 2026-07-20
- **Tasks:** 2
- **Files modified:** 1 (app.py)

## Accomplishments
- Bug do rótulo corrigido: a manchete `m2.metric` pendia de `banda_do_motor` (campo removido → sempre False), estampando "Intrínseco (DDM)" enquanto o número exibido é a região do RIM. Agora rótulo estático "Intrínseco (RIM)".
- Código morto do ensemble removido: expander de divergência, bloco "Classificação incerta", supressão por `arquetipo_incerto`, máquina `_motor`/`_usa_motor`, e caption do contraponto — todos gated por campos já removidos de `AnaliseAcao` na Fase 13.
- Copy DDM→RIM aplicada onde nomeia o motor atual (intro passo 3, spinner, caption do selo, aviso de preço indisponível, header/caption das lentes de referência, comentários e annotation do gráfico, docstring rf_capm).
- Nota `ddm_inaplicavel` reescrita: descreve a lente DDM sem afirmar "o Intrínseco (DDM) não é exibido" (cláusula stale).
- DDM preservado (honesto) onde é a lente/fórmula real: sub-tab "Valuation (DDM)", header "Valor intrínseco por Desconto de Dividendos", mensagem "DDM não calculado", e `CFG["ddm"]`.

## Task Commits

Cada task committed atomicamente (hooks on, sem --no-verify):

1. **Task 1: manchete Intrínseco (RIM) + remove código morto do ensemble** - `bb102d4` (fix)
2. **Task 2: relabel copy DDM→RIM onde nomeia o motor atual** - `f8e7ef9` (docs)

## Files Created/Modified
- `app.py` - Aba Analisar: rótulo honesto (RIM), remoção do código morto do ensemble, e relabel de copy DDM→RIM (motor atual) preservando DDM (lente genuína)

## Decisions Made
- Rótulo estático `"Intrínseco (RIM)"` em vez de `a.motor_rotulo` (longo demais para `st.metric`).
- Bloco `ddm_inaplicavel` mantido (o campo existe no dataclass); só a cláusula stale que nomeava a manchete foi removida.
- Sub-tab "Valuation (DDM)", header por Desconto de Dividendos, e `CFG["ddm"]` mantidos como DDM — a lente/fórmula renderiza `a.ddm_constante`/`a.ddm_h` de verdade; relabelar mentiria (viola o Core Value).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. O `_valor_intr` continua exibindo `intervalo` (faixa vmin–vmax) — nenhum número mudou; só o rótulo e a copy.

## Verification
- `python3 -c "import ast; ast.parse(open('app.py').read())"` — OK após cada task.
- `grep -E "banda_do_motor|arquetipo_incerto|san01_reetiquetado|divergencia_|contraponto_valor|candidatos_intrinsecos|veredito_range|_usa_motor" app.py` — 0 linhas (nenhum símbolo morto restante).
- `grep -c 'Intrínseco (DDM)' app.py` — 0. `grep -c 'Intrínseco (RIM)' app.py` — 2.
- Menções restantes de "DDM" em app.py: só a lente genuína (sub-tab, header, "DDM não calculado", guarda ddm_inaplicavel reescrita) e comentários honestos.
- `git diff config.yaml calibracao.lock.yaml` — VAZIO (fronteira inviolável).
- `git diff --name-only bb102d4^..HEAD` — só `app.py`.
- `pytest -q` — **473 passed, 0 failed, 18 deselected** (suíte verde; nenhum teste toca app.py).

## Next Phase Readiness
- Aba Analisar com rótulos honestos e sem código morto do ensemble. Nenhum blocker.

## Self-Check: PASSED
- `app.py` modificado e commitado (bb102d4, f8e7ef9) — ambos presentes em `git log`.
- SUMMARY criado neste caminho.

---
*Phase: quick*
*Completed: 2026-07-20*
