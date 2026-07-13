---
phase: 05-backtest-01-valida-o-na-cesta-de-bancos
plan: 02
subsystem: testing
tags: [backtest, fixtures, fair-value, bancos, yaml, consenso]

requires:
  - phase: 05-01
    provides: "snapshot congelado dos 4 bancos (tests/fixtures/snapshot_bancos_2026-07-12.yaml) — janela temporal 2026-07-12 à qual as faixas de fair value se alinham"
provides:
  - "tests/fixtures/fair_values_bancos.yaml — 4ª âncora do backtest (VAL-02): faixa mín–máx de fair value por ticker, aprovada pelo usuário, versionada como âncora-verdade do gate (D-06)"
affects: [05-03, 05-04]

tech-stack:
  added: []
  patterns:
    - "Fixture de config-data (âncora-verdade) vive em tests/fixtures/, NÃO em config.yaml (D-03) — separa verdade de validação dos knobs do motor"
    - "Faixa mín–máx por ticker (não ponto) para acomodar a dispersão do consenso (D-02); gate consome min/max com banda ±15% (D-07)"

key-files:
  created:
    - tests/fixtures/fair_values_bancos.yaml
  modified: []

key-decisions:
  - "Faixas de consenso aprovadas pelo usuário ANTES de versionar (bloqueio D-01) — números vêm de agregadores de target prices, não de Graham/Bazin/RIM (âncora independente)"
  - "Sem campo excecao_nota nesta fase — reservado ao gate do Plan 05-04 (D-08)"
  - "data=2026-07-12 alinhada ao snapshot capturado no 05-01 (D-05)"

patterns-established:
  - "Âncora-verdade versionada com fonte+data citáveis por ticker (proveniência auditável no diff git — mitiga T-05-04/T-05-05)"

requirements-completed: [VAL-02]

duration: 12min
completed: 2026-07-13
---

# Phase 5 Plan 02: Fixture de Fair Values dos Bancos Summary

**Fixture `fair_values_bancos.yaml` com as faixas de consenso (target prices, jul/2026) aprovadas pelo usuário para ITUB4/BBAS3/BBSE3/BBDC4 — a 4ª âncora-verdade que o gate do backtest (Plan 05-04) vai cobrar.**

## Performance

- **Duration:** ~12 min (inclui checkpoint de aprovação humana entre Task 1 e Task 3)
- **Completed:** 2026-07-13
- **Tasks:** 3 (Task 1 pesquisa, Task 2 checkpoint aprovado, Task 3 gravação)
- **Files modified:** 1

## Accomplishments

- Pesquisa de consenso de fair value (faixa de target prices) para os 4 bancos da cesta, a partir de agregadores (investing.com) corroborados por casas individuais (XP, BTG, Itaú BBA, Bradesco BBI, Genial, UBS BB, HSBC, Safra).
- Checkpoint de aprovação humana (D-01) resolvido: usuário aprovou as faixas exatas ANTES de qualquer versionamento.
- `tests/fixtures/fair_values_bancos.yaml` versionado com min/max/data/fonte por ticker; sem `excecao_nota` (reservado ao Plan 05-04, D-08).
- Verificação automatizada do plano passou: os 4 tickers presentes, todas as chaves presentes, config.yaml intocado.

## Task Commits

1. **Task 1: Pesquisa/curadoria do consenso de fair value** — sem commit por design (research-only, nada versionado até a aprovação, D-01)
2. **Task 2: Checkpoint de aprovação do usuário** — resolvido (usuário respondeu "APPROVED" com as faixas exatas)
3. **Task 3: Gravar o fixture aprovado** — `b95a4e0` (feat)

**Plan metadata:** commit final desta SUMMARY + STATE + ROADMAP

## Files Created/Modified

- `tests/fixtures/fair_values_bancos.yaml` — âncora-verdade do gate: faixa mín–máx de fair value por ticker (ITUB4 30.50–50.00, BBAS3 20.00–39.00, BBSE3 33.00–46.00, BBDC4 15.00–24.00), com data 2026-07-12 e fonte citável.

## Faixas versionadas (aprovadas pelo usuário)

| Ticker | min | max | data | fonte |
|--------|-----|-----|------|-------|
| ITUB4 | 30.50 | 50.00 | 2026-07-12 | Consenso de casas de análise (agregadores + XP/BTG/Itaú BBA/Bradesco BBI/Genial/UBS BB/HSBC/Safra) |
| BBAS3 | 20.00 | 39.00 | 2026-07-12 | idem |
| BBSE3 | 33.00 | 46.00 | 2026-07-12 | idem |
| BBDC4 | 15.00 | 24.00 | 2026-07-12 | idem |

## Decisions Made

- **Faixas aprovadas versionadas verbatim** — números fornecidos e aprovados pelo usuário não foram alterados (proveniência pública de consenso, sem viés do desenvolvedor).
- **Sem `excecao_nota`** nesta fase — o campo opcional é propriedade do gate do Plan 05-04, que decidirá quais tickers ficam fora da banda e precisam de anotação (D-08).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. O checkpoint de aprovação (D-01) foi o único gate; foi resolvido pela resposta explícita do usuário.

## Nota para o Plan 05-04 (implicação do gate 1/4)

Cruzando as faixas aprovadas com o RIM congelado do snapshot (05-01), **apenas ITUB4 cai dentro da banda ±15%** de alguma borda da faixa — 1/4 dos bancos. Isto está **abaixo do quórum QUORUM_MIN=3** exigido pelo gate (D-08). Este é um **sinal legítimo, não bug** — o usuário confirmou que não se deve afrouxar as faixas. O tratamento é responsabilidade do gate/loop **D-12 no Plan 05-04**: se a calibração da Fase 4 falhar para os demais bancos, o achado é registrado e a Fase 4 é reajustada (loop), e cada falha fora da banda DEVE receber `excecao_nota` (senão FAIL silencioso). O harness do Plan 05-03 e o gate do 05-04 é que decidem PASS/FAIL e anotam exceções — não este plano.

## Next Phase Readiness

- As 4 âncoras de realidade agora existem versionadas: Graham+Bazin (motor), preço (snapshot), múltiplos de pares (harness), e fair values manuais (este fixture).
- Plan 05-03 pode consumir `tests/fixtures/fair_values_bancos.yaml` via `.get("excecao_nota")` e min/max no harness compartilhado `rodar_cesta`.
- **Atenção herdada:** o gate do 05-04 deve tratar o cenário 1/4 (abaixo do quórum) explicitamente — ver nota acima.

## Self-Check

- Fixture existe e carrega via yaml.safe_load: PASSED
- Commit b95a4e0 existe: verificado abaixo

---
*Phase: 05-backtest-01-valida-o-na-cesta-de-bancos*
*Completed: 2026-07-13*
