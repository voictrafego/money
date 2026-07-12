---
phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo
plan: 02
subsystem: valuation-engine
tags: [python, veredito, san01, guarda-corpo, anti-aberracao, selo, ddm, reetiqueta]

# Dependency graph
requires:
  - phase: 03-veredito-honesto (plan 01)
    provides: "banda do ensemble motor×contraponto DDM (VER-01) + campos intrinseco_motor/motor/motor_rotulo/vmin/vmax alimentando o veredito"
provides:
  - "_guarda_san01: guarda-corpo anti-aberração na borda do veredito (reetiqueta 'DDM conservador demais para este perfil' quando SOBREAVALIADA + ROE>15% E corte payout>40%)"
  - "campo san01_reetiquetado em AnaliseAcao + nota honesta no relatorio_markdown"
  - "config veredito.san01.{fator_pares,roe_min,corte_payout_min}"
  - "backstop 'zero aberração silenciosa': todo veredito 'evitar' passa pelo guarda-corpo antes do selo (SC#3)"
affects: [03-03-VER-02-fronteirico, app.py-render, cli-render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guarda-corpo anti-aberração na borda do veredito, modelado em _guarda_faixa_ddm (flag + reetiqueta só do veredito + alerta honesto, sem tocar core/selo)"
    - "Degradação D-04 custo-zero: valor_pares=None → condição de pares neutra, gate cai para as 2 restantes, nunca puxa rede"
    - "Reetiqueta via prefixo não-casado por selo.faixa_do_veredito → faixa None → selo suprime 'Evitar' sem tocar selo.py (firewall)"

key-files:
  created: []
  modified:
    - "src/analista/report/report.py"
    - "config.yaml"
    - "tests/test_guardrails_ddm.py"

key-decisions:
  - "SAN-01 = guarda-corpo na borda do veredito (à la _guarda_faixa_ddm); gatilho SOBREAVALIADA + ROE>15% E corte payout>40% reetiqueta mantendo o número visível"
  - "Funil single-stock usa valor_pares=None (D-04): condição de pares neutra, gate cai para 2 condições, custo-zero; ITUB4 capturada pelas 2"
  - "corte de payout = 1 − (payout_valuation / payout_cru) quando payout_cru > 0 — o 'antes' (cru do último ano) vs. o 'depois' (mediana normalizada)"
  - "Never-raise: ROE/payout None → não dispara (não inventa aberração sobre dado ausente)"

patterns-established:
  - "Reetiqueta honesta, não supressão: o número intrínseco segue no texto + alerta lista as condições que dispararam"
  - "Backstop defense-in-depth: com VER-01 a maioria dos não-DDM já não cai em 'evitar'; o SAN-01 pega o caso residual"

requirements-completed: [SAN-01]

# Metrics
duration: ~25min
completed: 2026-07-12
---

# Phase 3 Plan 02: SAN-01 — Guarda-corpo anti-aberração antes do selo Summary

**Todo veredito que resultaria em "evitar" (SOBREAVALIADA) agora passa por `_guarda_san01` antes de virar selo: uma aberração (ROE > 15% E corte de payout > 40%, E intrínseco < 0,5× pares quando disponível) é reetiquetada para "DDM conservador demais para este perfil — ver motor primário do arquétipo", mantendo o número visível — o ITUB4-like deixa de ser carimbado "Evitar" sem tocar `selo.py` nem puxar rede.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-07-12
- **Tasks:** 2 (ambas TDD RED → GREEN)
- **Files modified:** 3 (report.py, config.yaml, test_guardrails_ddm.py)

## Accomplishments

- **SAN-01 (Task 1):** `_guarda_san01(a, c, cfg, valor_pares=None)` modelado exatamente em `_guarda_faixa_ddm` — marca a flag `san01_reetiquetado`, mexe SÓ no veredito e adiciona alerta honesto, na borda de emissão, sem tocar `core/`, `ddm.py` nem `selo.py`. Gatilho: prefixo `SOBREAVALIADA` (o quadrante Baixa×Caro = "Evitar"). Condições: `ROE_valuation > roe_min` (0.15) **E** `corte de payout > corte_payout_min` (0.40), onde `corte = 1 − (payout_valuation / payout_cru)`; a condição de pares (`intrínseco < fator_pares × valor_pares`) só entra quando `valor_pares` está disponível.
- **Plug no funil (Task 2):** `_guarda_san01(a, c, cfg, valor_pares=None)` é chamado APÓS a cadeia de veredito e ANTES de `montar_selo`, de modo que o selo consuma o veredito JÁ reetiquetado. No funil single-stock `valor_pares=None` (degradação D-04) → o gate cai para as 2 condições, sem nenhuma chamada de rede (custo-zero, constraint inegociável).
- **Firewall preservado:** o texto reetiquetado ("DDM conservador demais…") não casa nenhum prefixo que `selo.faixa_do_veredito` reconhece → `faixa = None` → `montar_selo` não estampa "Evitar". `selo.py` intocado.
- **Render honesto:** nota na seção Veredito do `relatorio_markdown` quando `san01_reetiquetado` — a referência primária é o motor do arquétipo (número acima), o DDM de estágio único é conservador demais para este perfil.
- **Config-driven:** `veredito.san01.{fator_pares: 0.5, roe_min: 0.15, corte_payout_min: 0.40}` com leitura defensiva `.get`; ajuste sem deploy.
- **ITUB4 sem "Evitar" (SC#1 fecha / SC#3):** golden e2e sobre a aberração-âncora (financeira SOBREAVALIADA, ROE 19,3%, corte payout ~55%) confirma reetiqueta antes do selo, `faixa_do_veredito is None` e número visível. Backstop não regride a pagadora regulada (motor==ddm, sem corte de payout → não dispara).

## Task Commits

Each task committed atomically (TDD RED → GREEN):

1. **Task 1: `_guarda_san01` + campo + knobs** — `9fcfc49` (test/RED) → `8f77a4f` (feat/GREEN)
2. **Task 2: plug no funil antes do selo + render + golden e2e** — `0a08f59` (test/RED) → `682305d` (feat/GREEN)

## Files Created/Modified

- `src/analista/report/report.py` — campo `san01_reetiquetado` em `AnaliseAcao`; função `_guarda_san01`; chamada no funil `analisar_acao` após a cadeia de veredito e antes de `montar_selo`; nota da reetiqueta na seção Veredito de `relatorio_markdown`.
- `config.yaml` — sub-bloco `veredito.san01` (`fator_pares`, `roe_min`, `corte_payout_min`) com o racional do brief.
- `tests/test_guardrails_ddm.py` — unit tests do `_guarda_san01` (aberração ITUB4-like, ROE baixo, veredito não-SOBREAVALIADA, never-raise, degradação D-04, config) + golden e2e `analisar_acao` (ITUB4 sem "Evitar" + regulada intocada).

## Decisions Made

- **Gatilho = prefixo SOBREAVALIADA** (o único quadrante que o selo cruzaria para Baixa×Caro="Evitar"). Um veredito SUB/NO INTERVALO nunca é reetiquetado.
- **`corte de payout = 1 − (payout_valuation / payout_cru)`** quando `payout_cru > 0` — o "antes" (payout cru do último ano) vs. o "depois" (mediana normalizada de `payout_valuation`). Consome os sinais canônicos (FIX-04), o MESMO número dos 3 modos.
- **Degradação D-04 sem rede:** `valor_pares=None` no funil single-stock torna a condição de pares neutra (não bloqueia o gate); a aberração-âncora (ROE 19,3% E corte ~55%) é capturada pelas 2 restantes.
- **Reetiqueta, não supressão (D-05):** o número intrínseco (do motor, ou o mid da banda como fallback) segue no texto e o alerta lista as condições que dispararam.
- **Never-raise:** ROE, payout cru ou payout normalizado None → não dispara.

## Deviations from Plan

None — plano executado exatamente como escrito. Nenhum rebaseline de golden foi necessário (SAN-01 é ADITIVO: `test_guardrails_ddm`/`test_guardrails_fix06`/`test_selo`/`test_report`/`test_vulc3_regressao`/`test_ddm`/`test_arquetipo_roteamento` seguem verdes sem alteração). Nenhum prefixo de veredito novo foi introduzido; `selo.faixa_do_veredito`/`_veredito_token` não precisaram mudar.

## Threat Register Outcome

Todas as disposições `mitigate` do threat model do plano foram implementadas:

- **T-0302-01 (falso-positivo):** dispara SÓ sobre SOBREAVALIADA + as 3/2 condições; insumo None → não dispara; número mantido visível.
- **T-0302-02 (rede indevida):** `valor_pares=None` no funil single-stock → NUNCA chama ingest/prices; gate cai para 2 condições offline.
- **T-0302-03 (esconder aberração):** reetiqueta, não supressão — número no texto + alerta com as condições disparadas.
- **T-0302-04 (firewall selo↛report):** reetiqueta muda só a string do veredito; `selo.py` intocado; teste de firewall (`grep import report` vazio) trava.

## Issues Encountered

- Chamadas ao `gsd-sdk query state.record-metric`/`state.add-decision` exigiram args por flag (`--phase/--plan/--duration`, `--summary`) em vez de posicionais — ajustado sem impacto no conteúdo.

## Known Stubs

None — SAN-01 está totalmente ligado ao veredito/render/selo. VER-02 (dúvida honesta no fronteiriço) é escopo explícito de 03-03.

## Next Phase Readiness

- **03-03 (VER-02):** os campos `arquetipo_fronteirico`/`arquetipo_candidatos` seguem prontos; o range dos candidatos + bandeira usa o mesmo dispatch de motor e o mesmo mecanismo de supressão de faixa via prefixo não-casado.
- Suíte completa: **423 passed** (era 415 no fim do 03-01; +8 testes SAN-01).

## Self-Check: PASSED

- Files created/modified present: report.py, config.yaml, tests/test_guardrails_ddm.py, 03-02-SUMMARY.md ✓
- Commits exist: 9fcfc49, 8f77a4f, 0a08f59, 682305d ✓
- Full suite: 423 passed ✓
- Firewall selo↛report intacto; core/ddm/comparables/selo não tocados ✓

---
*Phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo*
*Completed: 2026-07-12*
