---
phase: 06-integra-o-na-engine-composite-alerta-cli
plan: 02
subsystem: report
tags: [composite, matriz, alerta, cli, golden-test, read-only]

# Dependency graph
requires:
  - phase: 06-integra-o-na-engine-composite-alerta-cli
    plan: 01
    provides: "AnaliseAcao com a.sinais populado + timing_estado/timing_resumo + campos matriz_leitura/alerta_reverificacao vazios (contrato aditivo)"
provides:
  - "matriz_leitura: frase curada fundamento×técnico (token do veredito × timing_estado), fundamento-primeiro, células-âncora D-05/D-06 verbatim (TIMING-02)"
  - "alerta_reverificacao: OR-of-three (perda MM200 / death cross / perda mínima Donchian) consolidado numa única mensagem, voz reverificação, nunca venda (TIMING-03)"
  - "relatorio_markdown imprime a seção 'Sinais técnicos (consultivos)' com fallback gracioso de histórico curto (CLI-01)"
  - "Helpers puros _matriz_leitura/_alerta_reverificacao read-only sobre o fundamento, travados por golden direto"
affects: [Phase 07 (UI overlays consumindo matriz_leitura/alerta_reverificacao em modo read-only)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Matriz como dict de tuplas (token, estado) → frase curada (D-04), não template composicional"
    - "Alerta consolidado OR-of-three numa única mensagem (D-09), voz 'reverifique os fundamentos' — nunca 'venda'"
    - "Derivação extraída em helpers puros (input pinado) para golden travável sem montar CompanyData fundamentado"

key-files:
  created: []
  modified:
    - src/analista/report/report.py
    - tests/test_report.py

key-decisions:
  - "Matriz e alerta extraídos em helpers puros de módulo (_matriz_leitura/_alerta_reverificacao) — comportamento idêntico ao inline, mas travável por golden com input pinado (a matriz só LÊ o veredito, conforme antecipado no plano)"
  - "Token líder do veredito via startswith (SUBAVALIADA/SOBREAVALIADA/NO INTERVALO) — 'NO INTERVALO' é bi-palavra, não dá p/ usar split()[0]"
  - "9 células da matriz mapeadas explicitamente (3 vereditos × 3 estados); 2 âncora verbatim (D-05/D-06), 7 curadas fundamento-primeiro e consultivas"

patterns-established:
  - "Seção CLI segue o idiom L.append + linha em branco final, glifo ⚠️ da seção Alertas reaproveitado p/ paridade visual"
  - "Guard degradado da seção CLI espelha o fallback do DDM (sinais None / timing_estado '' / posicao_mm200 'indisponivel')"

requirements-completed: [TIMING-02, TIMING-03, CLI-01]

# Metrics
duration: 5min
completed: 2026-06-27
---

# Phase 6 Plan 02: Matriz fundamento×técnico + alerta de reverificação + CLI Summary

**analisar_acao agora fecha o read técnico consultivo: matriz_leitura cruza o veredito DDM com o estado técnico numa frase curada fundamento-primeiro (células-âncora D-05/D-06 verbatim), alerta_reverificacao dispara no OR dos três gatilhos de baixa numa mensagem consolidada que nunca soa como venda, e relatorio_markdown espelha tudo na seção "Sinais técnicos (consultivos)" com fallback gracioso — tudo read-only sobre o fundamento e travado por golden, com os 64 goldens de valuation intactos.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-27T00:39:33Z
- **Completed:** 2026-06-27T00:44:44Z
- **Tasks:** 2
- **Files modified:** 2 (ambos modificados)

## Accomplishments
- `matriz_leitura` (TIMING-02): dict explícito de 9 células `(token do veredito × timing_estado) → frase curada`, fundamento sempre liderando a oração; as duas âncora D-05 (BARATO×ATENÇÃO) e D-06 (CARO×ALTA) gravadas verbatim; veredito vazio degrada para `""` sem inventar frase.
- `alerta_reverificacao` (TIMING-03): OR dos três gatilhos discretos (`posicao_mm200=="abaixo"` / `cruzamento=="death_cross"` / `rompimento_donchian=="perda_minima"`), consolidado numa única mensagem "Reverifique os fundamentos: …. Não é sinal de venda — confirme se os números seguem intactos."; dispara independente do veredito (D-08); `None` quando nenhum gatilho aciona (inclui sinais "indisponivel").
- Seção CLI "Sinais técnicos (consultivos)" (CLI-01) em `relatorio_markdown`, após o Veredito: timing + matriz + alerta ⚠️ no caso normal; fallback em itálico no caso degradado, espelhando o fallback do DDM.
- 9 novos golden tests em `tests/test_report.py` (âncoras verbatim, fundamento-lidera, veredito vazio, alerta consolidado/None, independência do veredito, "venda" só na negação, seção CLI normal+degradada).

## Task Commits

1. **Task 1: matriz fundamento×técnico + alerta de reverificação em analisar_acao** - `6103dd0` (feat)
2. **Task 2: seção CLI + golden matriz/alerta/CLI + invariante TEST-07** - `d9f7158` (test)

## Files Created/Modified
- `src/analista/report/report.py` - `analisar_acao` passa a gravar `a.matriz_leitura`/`a.alerta_reverificacao` via dois helpers puros novos (`_matriz_leitura`, `_alerta_reverificacao` + `_veredito_token` + dict `_MATRIZ_LEITURA`); `relatorio_markdown` ganhou a seção "Sinais técnicos (consultivos)" com guard degradado.
- `tests/test_report.py` - estendido de 2 → 11 testes; nova fixture `_ohlc_baixa_rompimento` (queda íngreme p/ acionar perda da MM200 + perda da mínima do Donchian).

## Decisions Made
- A matriz e o alerta foram extraídos em **helpers puros de módulo** em vez de ficarem inline em `analisar_acao`. Comportamento idêntico, mas torna os goldens das células-âncora traváveis com input **pinado** (`_matriz_leitura("SUBAVALIADA — …", "atencao")`) — exatamente a abordagem que o plano antecipa ("o teste pode pinar a.veredito porque a matriz só LÊ esse campo"), sem precisar montar um `CompanyData` com fundamentos completos que produzam SUBAVALIADA/SOBREAVALIADA.
- Token do veredito extraído por `startswith` (não `split()[0]`), porque "NO INTERVALO" é bi-palavra.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixture do alerta com declínio raso não acionava perda_minima do Donchian**
- **Found during:** Task 2 (golden do alerta)
- **Issue:** A 1ª versão de `_ohlc_baixa_rompimento` usava `linspace(150, 80, 300)` (passo ~0,23/barra), menor que o offset `Low = Close - 0.3`. Como `donchian_inf` é a mínima causal das 20 barras anteriores (≈ Low da barra -2), o Close da ponta NÃO rompia abaixo dela → `rompimento_donchian == "nenhum"` e o teste de pré-condição falhava.
- **Fix:** Tornar a queda mais íngreme (`linspace(200, 60, 300)`, passo ~0,47/barra > 0,3) para o Close romper abaixo da mínima causal das 20 barras anteriores. Segue terminando bem abaixo da MM200 (≈106 no tip).
- **Files modified:** tests/test_report.py
- **Commit:** d9f7158

## TDD Gate Compliance
Task 1 (`tdd="true"`) é a implementação da matriz/alerta; o golden correspondente foi entregue na Task 2 conforme a estrutura do plano (a verify da Task 1 — `pytest -k "matriz or alerta"` — refere-se aos testes criados na Task 2, mesma disciplina da Plan 01). Sequência de gates no git log: `feat` (6103dd0, implementação) seguido de `test` (d9f7158, golden travando o comportamento). Suíte completa verde após cada commit (94 → 103).

## Issues Encountered
- Ver desvio Rule 3 acima (calibração da fixture de queda). Sem outros bloqueios.

## Known Stubs
None — `matriz_leitura` e `alerta_reverificacao` estão totalmente cabeados aos campos reais da engine; nenhum valor placeholder.

## Next Phase Readiness
- O read técnico consultivo está completo na engine (timing + matriz + alerta) e espelhado na CLI. A Phase 7 (UI) consome `a.matriz_leitura`/`a.alerta_reverificacao`/`a.timing_resumo` em modo read-only para os overlays/subpainéis.
- Suíte: 103 testes verdes (94 anteriores + 9 novos de report). Invariante TEST-07 preservada — nenhuma fórmula de valuation tocada.

## Self-Check: PASSED

---
*Phase: 06-integra-o-na-engine-composite-alerta-cli*
*Completed: 2026-06-27*
