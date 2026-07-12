---
phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo
plan: 04
subsystem: ui-streamlit
tags: [python, streamlit, ui, veredito, ensemble, divergencia, san01, ver02, capstone, e2e]

# Dependency graph
requires:
  - phase: 03-veredito-honesto (plan 01)
    provides: "campos divergencia_ativa/divergencia_razao/divergencia_hipotese/contraponto_valor/intrinseco_motor/motor_rotulo (ENS-01)"
  - phase: 03-veredito-honesto (plan 02)
    provides: "campo san01_reetiquetado + nota da reetiqueta anti-aberração (SAN-01)"
  - phase: 03-veredito-honesto (plan 03)
    provides: "campos arquetipo_incerto/candidatos_intrinsecos/veredito_range (VER-02)"
provides:
  - "Paridade CLI↔UI dos sinais do veredito honesto: bandeira de divergência, range fronteiriço e nota da reetiqueta SAN-01 renderizados no bloco veredito+selo do Analisar (app.py)"
  - "Rótulo honesto do intrínseco: 'Intrínseco (<motor>)' quando motor != ddm, 'Intrínseco (DDM)' só quando o motor é o DDM (T-0304-01)"
  - "Capstone e2e dos tickers-âncora (ITUB4/TAEE11/VALE3/WEGE3/VULC3) sobre o veredito FINAL da fase"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Render read-only dos sinais da engine no Streamlit via st.info/st.warning (guards getattr, zero recálculo) — paridade de copy com relatorio_markdown"
    - "Rótulo do intrínseco reflete o motor do arquétipo (a.motor_rotulo) para não chamar RIM/DCF/NAV/normalizado de 'DDM'"
    - "Capstone e2e com fixtures sintéticas OFFLINE nomeadas pelos tickers-âncora reais, espelhando os padrões de arquétipo já provados"

key-files:
  created: []
  modified:
    - "app.py"
    - "tests/test_vulc3_regressao.py"

key-decisions:
  - "Blocos de render dos novos sinais posicionados logo após o veredito colorido e antes do selo (anotam o veredito), sem redesenho (Out of Scope)"
  - "Guards defensivos com getattr(a, campo, default) antes de acessar os campos novos — degradação graciosa se um campo faltar (T-0304-03)"
  - "Help do metric mantido em h('valor_intrinseco') (glossário genérico de valor intrínseco, válido para qualquer motor) — só o LABEL muda por motor"
  - "Capstone via fixtures sintéticas OFFLINE (não puxa rede) nomeadas ITUB4/TAEE11/VALE3/WEGE3, roteamento confirmado por probe antes de escrever as asserções"

patterns-established:
  - "UI é read-only sobre AnaliseAcao: o mesmo número dos 3 modos, nunca recalculado na view (T-0304-02, travado por test_consistencia_modos)"

requirements-completed: [VER-01, ENS-01, SAN-01, VER-02]

# Metrics
duration: ~20min
completed: 2026-07-12
---

# Phase 3 Plan 04: Superfície de render Streamlit + capstone e2e Summary

**A UI do Analisar (`app.py`) passa a exibir os três sinais do veredito honesto — bandeira de divergência (ENS-01), range fronteiriço (VER-02) e nota da reetiqueta SAN-01 — e o rótulo do intrínseco reflete o motor do arquétipo (não chama mais o RIM/DCF/NAV/normalizado de "DDM"); tudo read-only sobre os campos já derivados na engine, fechado por um capstone e2e sobre os tickers-âncora (ITUB4 sem "Evitar", TAEE11 idêntica, VALE3 normalizado, WEGE3 dcf, VULC3 VERIFICAR) e a suíte completa de goldens da fase verde.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-12
- **Tasks:** 2
- **Files modified:** 2 (app.py, tests/test_vulc3_regressao.py)

## Accomplishments

- **Paridade CLI↔UI (Task 1):** o bloco veredito+selo do Analisar (`app.py`) agora renderiza, read-only, os sinais que o `relatorio_markdown` (CLI) já mostrava:
  - **Bandeira de divergência (ENS-01):** `st.warning` com a razão (~N×), os DOIS números (motor primário × DDM lente conservadora) e a hipótese curada, quando `a.divergencia_ativa`.
  - **Classificação incerta / range fronteiriço (VER-02):** lista os candidatos com seus intrínsecos + a frase "classificação incerta entre X e Y" + o range `[menor..maior]`, quando `a.arquetipo_incerto`.
  - **Nota da reetiqueta (SAN-01):** `st.info` honesto ("guarda-corpo anti-aberração: a referência é o motor do arquétipo; o DDM é conservador demais"), quando `a.san01_reetiquetado`.
- **Rótulo honesto do intrínseco (T-0304-01):** `m2.metric` passa a usar `f"Intrínseco ({a.motor_rotulo or motor})"` quando `motor != "ddm"`, mantendo "Intrínseco (DDM)" quando o motor é de fato o DDM (TAEE11) — a UI não chama mais o RIM/DCF/NAV/normalizado de "DDM".
- **Render read-only (firewall):** o diff de `app.py` só LÊ campos de `a` (guards `getattr`), zero chamadas a motores/ddm/comparables/selo — `python -c "ast.parse"` verde; `selo.py`/`report.py` intocados.
- **Capstone e2e (Task 2):** 5 testes novos em `tests/test_vulc3_regressao.py` sobre o veredito FINAL da fase com fixtures sintéticas OFFLINE nomeadas pelos âncora reais:
  - **ITUB4** → financeira/RIM alimenta o veredito, DDM como lente conservadora, selo NUNCA "Evitar".
  - **TAEE11** → motor DDM, baseline intocado (sem suspensão/reetiqueta/fronteiriço) e determinístico entre execuções.
  - **VALE3** → cíclica → motor "normalizado".
  - **WEGE3** → crescimento → motor "dcf", banda saudável (0 < vmin ≤ vmax, finita), sem faixa-lixo.
  - **VULC3** → invariante "VERIFICAR" por risco real (payout > 100%).
- **Suíte da fase verde + Core Value + firewall:** os 13 módulos de golden da fase saem 0 (164 passed); `test_consistencia_modos` trava o mesmo número nos 3 modos; `grep "import report" selo.py` vazio. Suíte completa: **434 passed** (era 429 no fim do 03-03; +5 capstone).

## Task Commits

1. **Task 1: render bandeira/range/reetiqueta + rótulo do intrínseco por motor (app.py)** — `06f501d` (feat)
2. **Task 2: capstone e2e dos tickers-âncora + suíte de goldens da fase** — `5df6ff3` (test)

## Files Created/Modified

- `app.py` — no bloco veredito do Analisar (após o veredito colorido, antes do selo): três blocos read-only novos (`st.info` SAN-01, `st.warning` classificação incerta VER-02, `st.warning` bandeira de divergência ENS-01) com guards `getattr`; `m2.metric` do intrínseco com label derivado de `a.motor_rotulo`/`a.motor`.
- `tests/test_vulc3_regressao.py` — 4 fixtures-âncora (`_itub4_financeira`, `_taee11_regulada`, `_vale3_ciclica`, `_wege3_crescimento`) + 5 testes capstone e2e sobre o veredito final; import de `math` e `selo` adicionados.

## Decisions Made

- **Posição dos blocos:** logo após o veredito colorido e antes do selo — anotam o veredito, sem redesenho (Out of Scope respeitado).
- **Guards defensivos** (`getattr(a, campo, False)`) antes de acessar os campos novos — degradação graciosa se um campo faltar (T-0304-03 mitigado).
- **Help do metric inalterado** (`h('valor_intrinseco')`, glossário genérico) — só o LABEL muda por motor; não há chave de glossário por motor e o texto do intrínseco vale para qualquer motor.
- **Capstone com fixtures OFFLINE nomeadas pelos âncora reais** — roteamento confirmado por probe (`financeira→rim`, `pagadora_regulada→ddm`, `ciclica→normalizado`, `crescimento→dcf`) antes de escrever as asserções, para o capstone não ser flaky.

## Deviations from Plan

None — plano executado exatamente como escrito. **Nenhum rebaseline de golden foi necessário**: Task 1 é render aditivo read-only (nenhum golden depende do markup do Streamlit) e Task 2 é aditivo (5 testes novos). Nenhum prefixo de veredito novo; `faixa_do_veredito`/`_veredito_token` não precisaram mudar; `selo.py`/`report.py` intocados (`git diff --exit-code` limpo).

## Threat Register Outcome

Todas as disposições `mitigate` do threat model do plano foram implementadas:

- **T-0304-01 (rótulo enganoso):** o label do `m2.metric` passa a refletir `a.motor_rotulo` quando `motor != "ddm"`; "Intrínseco (DDM)" só quando o DDM é o motor de fato. Capstone TAEE11 (ddm) vs. ITUB4/VALE3/WEGE3 (não-ddm) travam os dois lados.
- **T-0304-02 (UI recalcula e diverge):** o render é 100% read-only sobre `a` (grep do diff confirma zero chamadas a motores/ddm/comparables); `test_consistencia_modos` segue verde travando o mesmo número nos 3 modos.
- **T-0304-03 (campo None quebra o render):** guards `getattr(...)`/`if a.<campo>` antes de acessar `veredito_range`/`divergencia_*`/`candidatos_intrinsecos`; defaults degradáveis dos campos.

## Issues Encountered

Nenhum. O roteamento das 4 fixtures-âncora foi confirmado por probe antes das asserções; os 5 testes capstone passaram na primeira execução.

## Known Stubs

None — os três sinais do veredito honesto estão totalmente ligados ao render do Analisar (paridade com o CLI). Fecha os 4 requisitos da fase na UI (VER-01/ENS-01/SAN-01/VER-02).

## Next Phase Readiness

- **SC#1..SC#4 exibidos na UI:** ITUB4 sem "Evitar" + bandeira; range fronteiriço; reetiqueta SAN-01; rótulo do intrínseco por motor.
- **SC#5 (fecha):** firewall selo↛report intacto; suíte completa de goldens da fase verde; Core Value (3 modos) travado.
- Suíte completa: **434 passed**.

## Self-Check: PASSED

- Files modified present: app.py, tests/test_vulc3_regressao.py, 03-04-SUMMARY.md ✓
- Commits exist: 06f501d, 5df6ff3 ✓
- Full suite: 434 passed ✓
- Firewall selo↛report intacto; selo.py/report.py não tocados (git diff limpo) ✓

---
*Phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo*
*Completed: 2026-07-12*
