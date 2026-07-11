---
phase: 02-motores-por-arqu-tipo
plan: 02
subsystem: engine
tags: [valuation, roteamento, registry, rim, dcf, nav, lucro-normalizado, veredito, golden-tests, python]

# Dependency graph
requires:
  - phase: 02-motores-por-arqu-tipo
    plan: 01
    provides: "core/motores.py (rim/ke_rim/lucro_normalizado/dcf_crescimento/nav_contabil + MOTOR_ROTULO)"
provides:
  - "ARQUETIPO_MOTOR 5/5 preenchido (financeira→rim, ciclica→normalizado, crescimento→dcf, holding→nav, pagadora_regulada→ddm)"
  - "dispatch dos 4 motores no funil analisar_acao, gravando a.intrinseco_motor + a.motor_rotulo (D-06: motor calcula e EXIBE)"
  - "suspensão do veredito migrada de motor_pendente → motor != 'ddm' em 3 superfícies (report + cli + goldens), sem regredir o ITUB4"
  - "render: intrínseco do motor do arquétipo como referência primária + DDM rebaixado a 'lente conservadora'"
affects: [03-veredito-honesto, ensemble-divergencia]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dispatch por id de motor no funil consumindo SEMPRE insumos canônicos (*_valuation/base_normalizada/lentes.vpa), nunca o cru (Pitfall 2/FIX-04)"
    - "Suspensão do veredito como predicado 'o selo ainda não consome este motor' (motor != 'ddm'), migrada NO MESMO wave do plug do registry para evitar janela de regressão (D-06)"

key-files:
  created: []
  modified:
    - src/analista/core/arquetipo.py
    - src/analista/report/report.py
    - src/analista/cli.py
    - tests/test_arquetipo_roteamento.py
    - tests/test_ranking_freio.py

key-decisions:
  - "Suspensão migra de motor_pendente (registry None) → motor != 'ddm' nas 3 superfícies no mesmo plano/wave que o plug — o motor JÁ EXISTE mas o selo só o consome na Fase 3 (VER-01); sem isso o ITUB4 regride de VERIFICAR para 'evitar'"
  - "Anchor e2e do RIM usa comparação RELATIVA ao DDM da própria fixture (> 1,3× o DDM ao vivo) + > VPA, robusta ao ke_rim real (~0,14), NÃO piso absoluto R$25/28 (checker Warning 1)"
  - "Holding: o classificador da Fase 1 ainda não emite a chave 'holding'; o dispatch NAV é validado e2e via monkeypatch da rota (o motor está plugado e wired — o classificador emitir holding é escopo ARQ futuro)"

requirements-completed: [ENG-02, ENG-03, ENG-04, ENG-05]

# Metrics
duration: 16min
completed: 2026-07-11
---

# Phase 2 Plan 02: Plug dos Motores no Registry + Funil Summary

**Os 4 motores do Plan 01 plugados no registry `ARQUETIPO_MOTOR` (5/5) e wired no funil único de `analisar_acao` — cada arquétipo agora CALCULA e EXIBE o intrínseco pelo motor certo (RIM/normalizado/DCF/NAV), com a suspensão do veredito migrada de `motor_pendente` → `motor != "ddm"` nas 3 superfícies no mesmo wave, de modo que o ITUB4 segue "VERIFICAR" (não regride para "evitar") e o DDM é rebaixado a "lente conservadora".**

## Performance

- **Duration:** ~16 min
- **Completed:** 2026-07-11
- **Tasks:** 3
- **Files modified:** 5 (0 criados, 5 modificados)

## Accomplishments
- **Registry 5/5 (Task 1)** — `ARQUETIPO_MOTOR` sem nenhum `None`: financeira→rim, cíclica→normalizado, crescimento→dcf, holding→nav, pagadora_regulada→ddm (intocado). Dispatch por `a.motor` no funil grava `a.intrinseco_motor` + `a.motor_rotulo`, consumindo SEMPRE os insumos canônicos (`roe_valuation`/`lpa_valuation`/`payout_valuation`/`base_normalizada`/`lentes.vpa`) — nenhum lucro cru no dispatch.
- **Migração D-06 (Task 2, o elemento load-bearing)** — a suspensão do veredito migrou de `if a.motor_pendente:` para `if a.motor != "ddm":` nas TRÊS superfícies (`report.py`, `cli._motor_pendente`, goldens), NO MESMO plano/wave que o plug. O ITUB4/financeira segue "VERIFICAR" com o motor "rim" plugado — **não regride para "evitar"**. `selo.py` e `report._veredito_token` intocados (firewall preservado).
- **Render + anchors (Task 3)** — `relatorio_markdown` exibe o intrínseco do motor do arquétipo como referência primária e rebaixa o DDM a "lente conservadora" onde `motor != "ddm"`. 6 anchors e2e novos cobrem os 4 motores + regulada, cada um assertando `a.motor` e `a.intrinseco_motor`.
- **Suíte completa: 406 passed** (400 baseline + 6 anchors), sem regressão. `test_ddm`, `test_selo`, `test_consistencia_modos`, `test_vulc3_regressao`, `test_guardrails_fix06` todos verdes.

## Task Commits

1. **Task 1: Plug no registry + dispatch dos motores + campos de resultado** — `277f239` (feat)
2. **Task 2: Migração D-06 da suspensão em 3 superfícies (report + cli + goldens)** — `e9df65c` (fix)
3. **Task 3: Render (DDM rebaixado + intrínseco do motor) + anchors e2e por motor** — `a08d6c6` (feat)

## Files Created/Modified
- `src/analista/core/arquetipo.py` — `ARQUETIPO_MOTOR` 5/5 preenchido (4 `None` trocados pelos ids); comentário atualizado para a Fase 2 + o predicado de suspensão migrado
- `src/analista/report/report.py` — campos `intrinseco_motor`/`motor_rotulo` em `AnaliseAcao`; dispatch dos 4 motores após a resolução do motor; suspensão migrada (`motor != "ddm"`) com o intrínseco do motor exibido como referência; render do motor + DDM rebaixado a lente
- `src/analista/cli.py` — `_motor_pendente` migrado para `!= "ddm"` (paridade Analisar × Ranking, D-06); docstring atualizada
- `tests/test_arquetipo_roteamento.py` — asserts da Fase 1 atualizados (financeira `motor=='rim'`, petróleo `motor in {dcf,normalizado}`) + fixtures `_ciclica`/`_holding` + 6 anchors e2e por motor
- `tests/test_ranking_freio.py` — docstrings dos testes de suspensão atualizadas (motor rim existe; predicado migrado)

## Decisions Made
- **Suspensão migra no mesmo wave que o plug (D-06 / Pitfall 1).** O motor do arquétipo JÁ EXISTE após o Plan 01, mas o selo só o consome na Fase 3 (VER-01). Trocar os `None` do registry por ids torna `motor is None` sempre `False`; se a suspensão simplesmente caísse, o ITUB4 atravessaria para o veredito DDM e voltaria a "evitar". Por isso o predicado migrou para "o selo ainda não consome este motor" (`motor != "ddm"`) nas 3 superfícies, no mesmo plano.
- **Anchor RIM por comparação relativa, não piso absoluto.** Com o `ke_rim()` real (~0,14, maior que o 0,125 do golden unitário do Plan 01) o intrínseco fica abaixo do golden. O anchor assere `intrinseco_motor > VPA` (estrutural, ROE>Ke) E `> 1,3× o DDM ao vivo da própria fixture` — robusto ao ke real, sem hardcodar R$25/28 (checker Warning 1). Na `_financeira` sintética: RIM ≈ R$6,29 > VPA R$5,00 > 1,3× DDM ≈ R$2,08.
- **Holding validada por monkeypatch.** Ver "Known Gaps".

## Deviations from Plan

### Auto-fixed / ajustes

**1. [Rule 3 - Ajuste de assert] Golden de alerta da financeira atualizado junto com o texto do alerta**
- **Found during:** Task 2
- **Issue:** A ação da Task 2 (1) manda "atualizar o alerta correspondente" da suspensão; o texto do alerta deixou de conter a frase literal "motor pendente" (agora "motor '{motor}' ... suspenso"). O golden `test_financeira_...` assertava `any("motor pendente" in al.lower() ...)`, que passaria a falhar.
- **Fix:** assert migrado para `any("suspenso" in al.lower() ...)`, robusto ao novo texto e coerente com a semântica D-06.
- **Files modified:** tests/test_arquetipo_roteamento.py
- **Committed in:** e9df65c

**Total deviations:** 1 (ajuste de golden acompanhando a edição de texto sancionada pela ação da Task 2). Nenhum desvio de escopo ou comportamento.

## Known Gaps

- **Classificador não emite a chave `holding`.** `core/arquetipo.classificar` produz apenas `financeira`/`pagadora_regulada`/`ciclica`/`crescimento`/`pagadora_regulada` (default) — nunca `holding`. O motor NAV (ENG-05) está PLUGADO no registry e WIRED no dispatch; o anchor `test_holding_roteia_nav_igual_vpa` força a rota via `monkeypatch` de `classificar` para validar o dispatch NAV ponta-a-ponta (`a.motor == "nav"`, `intrinseco == VPA`). Fazer o classificador EMITIR `holding` (sinal de participações/SOTP) é escopo ARQ futuro, não deste plano de motores. Não é um stub: o motor calcula corretamente; o que falta é a rota do classificador, documentada aqui para a Fase 3 / backlog ARQ.

## Verification
- `python -m pytest` (suíte completa) → **406 passed** (400 baseline + 6 anchors)
- `python -m pytest tests/test_arquetipo_roteamento.py tests/test_ranking_freio.py tests/test_selo.py` → 39 passed
- ITUB4/financeira: `a.motor == "rim"`, `a.intrinseco_motor > VPA` e `> 1,3× DDM da fixture`, veredito "VERIFICAR", selo sem 'evitar' ✓
- TAEE11/regulada: `a.motor == "ddm"`, veredito NÃO suspenso (ENG-06 preservado) ✓
- `git diff --name-only 2531656 HEAD -- src/` NÃO lista `core/ddm.py`/`core/lentes.py`/`report/selo.py` (firewall + primitivas intactas) ✓
- Ranking (`cli._motor_pendente`) mantém paridade com a suspensão do Analisar (`motor != "ddm"`) ✓

## Self-Check: PENDING
