---
phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia
plan: 03
subsystem: testing
tags: [payout, mediana, dy-recorrente, golden, multi-ticker, cross-effect, validacao-live]

# Dependency graph
requires:
  - phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia
    provides: "payout_valuation() mediana sem clamp (PAY-01) e dy_recorrente() earnings-based (DYR-01) — Plan 02"
  - phase: 08-normalizacao-do-lucro
    provides: "lpa_valuation / base_lucro_normalizada (base de lucro normalizada por ação)"
provides:
  - "golden OFFLINE de propriedade multi-ticker (4 perfis sintéticos calibrados a VULC3/TAEE11/EGIE3+ITUB4+BBAS3) que travam as PROPRIEDADES do método sem rede"
  - "guarda direta do success criterion 3: payout >100% num único ano ⇒ g_fundamentos > 0 (contraste com payout >100% em todos os anos ⇒ g_fund ≤ 0)"
  - "validação LIVE dos 5 tickers reais aprovada contra os números-alvo da metodologia (checkpoint human-verify)"
  - "registro do cross-effect payout-sem-clamp → regressão P/L do screening (handoff Fase 10)"
affects: [Fase 10 (de-poison do screening — cross-effect registrado), Fase 11 (trava multi-ticker formal TEST-08)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "golden de propriedade multi-ticker: um helper sintético por perfil (forma de _vulc3_sintetica), cada assert com 1 comentário 'pelo método' e tolerância justificada — trava PROPRIEDADES, não números de mercado (esses ficam no checkpoint live)"
    - "duas camadas de validação: offline determinístico (propriedades) + live human-verify (números-alvo reais), separando o que o golden offline não reproduz sem fixtures congelados"

key-files:
  created:
    - tests/test_payout_sustentavel_multiticker.py
    - .planning/phases/09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia/09-CROSS-EFFECT-FASE10.md
  modified: []

key-decisions:
  - "Golden offline trava PROPRIEDADES (no-clamp >1.0, descarte de spike, mediana no regime, g_fund volta a existir); números-alvo reais ficam no checkpoint live (não há fixtures congelados de rede)"
  - "Perfil 'payout >100% num único ano' usa report.analisar_acao para assert g_fundamentos > 0 — guarda direta do success criterion 3, contrastada com perfil >100% em todos os anos (g_fund ≤ 0)"
  - "Cross-effect payout-sem-clamp → regressão P/L registrado para a Fase 10, NÃO resolvido aqui (D-06); screening.py intocado"

patterns-established:
  - "Validação multi-ticker em 2 camadas (offline propriedades + live números-alvo) como modelo do critério de aceite 'vale para qualquer ticker, não tuna a um'"

requirements-completed: [PAY-01, DYR-01]

# Metrics
duration: ~25min (inclui checkpoint human-verify)
completed: 2026-06-27
---

# Phase 9 Plan 03: Trava de validação multi-ticker (offline + live) + registro do cross-effect Fase 10 Summary

**Golden OFFLINE de propriedade multi-ticker (4 perfis sintéticos calibrados a VULC3/TAEE11/EGIE3+ITUB4+BBAS3) que trava as propriedades do payout sustentável sem rede — incl. a guarda direta do success criterion 3 (payout >100% num único ano ⇒ g_fund > 0) — mais a validação LIVE dos 5 tickers reais aprovada contra os números-alvo e o registro do cross-effect payout-sem-clamp → regressão P/L para a Fase 10.**

## Performance

- **Duration:** ~25 min (inclui o checkpoint human-verify)
- **Started:** 2026-06-27
- **Completed:** 2026-06-27
- **Tasks:** 2 (1 auto + 1 checkpoint human-verify aprovado)
- **Files modified:** 2 (ambos criados)

## Accomplishments
- `tests/test_payout_sustentavel_multiticker.py`: 5 testes verdes cobrindo 4 perfis sintéticos OFFLINE — TAEE11 (payout >100% todo ano ⇒ mediana preservada >1.0, NÃO clampada/zerada), VULC3 (recorrente ~0.43 + spike ⇒ mediana descarta o spike <1.0), normal estável (mediana no regime + DY rec. earnings-based finito e ≤ trailing inflado), e payout >100% num único ano (g_fundamentos > 0) com contraste explícito >100% em todos os anos (g_fund ≤ 0).
- Validação LIVE dos 5 tickers reais aprovada (checkpoint human-verify): os números-alvo da metodologia bateram, com TAEE11 preservado >100% e VULC3 caindo para payout sustentável <100% e DY recorrente muito abaixo do trailing falso.
- `09-CROSS-EFFECT-FASE10.md`: handoff registrando o payout sem clamp (TAEE11 ≈ 2.16) fluindo para `preco_alvo_por_regressao` (cli.py L158-159 / app.py L472) calibrada em payout ∈ [0,1]; item de de-poison para a Fase 10. `screening.py` intocado (D-06); BSD per-ano CRU não afetado.

## Task Commits

1. **Task 1: Golden offline multi-ticker + nota cross-effect Fase 10** - `7048fa3` (test)
2. **Task 2: Validação live dos 5 tickers reais** - checkpoint human-verify (sem commit de código; aprovado pelo usuário)

**Plan metadata:** (este commit) `docs(09-03)`

## Files Created/Modified
- `tests/test_payout_sustentavel_multiticker.py` - 4 perfis sintéticos OFFLINE (helper `_mk` na forma de `_vulc3_sintetica`) travando as propriedades do método: no-clamp >1.0, descarte de spike <1.0, mediana no regime + DY rec. earnings-based, e `g_fundamentos > 0` para payout >100% num único ano (success criterion 3) vs `g_fund ≤ 0` para >100% em todos os anos.
- `.planning/phases/09-.../09-CROSS-EFFECT-FASE10.md` - registro do efeito cruzado payout-sem-clamp → regressão P/L do screening (handoff Fase 10, não resolvido aqui).

## Decisions Made
- O golden offline trava PROPRIEDADES (deterministas, sem rede); os números-alvo REAIS são confirmados pelo checkpoint live — não há fixtures de rede congelados, então misturar os dois seria frágil.
- O perfil "payout >100% num único ano" usa `report.analisar_acao(c, _cfg())` e assert `g_fundamentos > 0` (guarda direta do success criterion 3), contrastado com o perfil ">100% em todos os anos" (g_fund ≤ 0) — prova que o crescimento por fundamentos VOLTA a existir para quem só estourou 100% num ano.
- Cross-effect registrado, não resolvido (D-06): `screening.py` não foi editado.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
- O interpretador `python` não está no PATH; usado `.venv/bin/python` (venv do projeto) para pytest. Sem impacto no código.

## Verification

### Offline (automated)
- `pytest tests/test_payout_sustentavel_multiticker.py -q` → 5 passed.
- Suíte completa: `pytest -q` → 160 passed (nada regrediu; nenhum arquivo de `src/` editado).
- `git diff --quiet src/analista/core/screening.py` → screening.py intocado (D-06).

### Live (checkpoint human-verify — APROVADO)
Os 5 tickers reais rodaram sem exceção e bateram os números-alvo da metodologia:

| Ticker | Payout (DP) obtido | Alvo | DY rec. obtido | Alvo |
|--------|--------------------|------|----------------|------|
| VULC3  | 43.1%  | ~43%  | 6.3% | ~6.2% |
| TAEE11 | 217.9% | ~216% (>100% PRESERVADO, não clampado) | 8.4% | ~8.3% |
| EGIE3  | 49.9%  | ~49%  | 4.0% | — |
| ITUB4  | 31.2%  | ~31%  | 2.8% | — |
| BBAS3  | 18.8%  | ~20%  | 4.7% | — |

Sentido qualitativo confirmado: TAEE11 segue >100% (a mediana não rebaixou o pagador recorrente); VULC3 caiu para payout sustentável <100% com DY recorrente muito abaixo do trailing falso (antigo ~20,4%).

## Threat Surface
- T-09-06 (método passar nos sintéticos mas falhar em dados reais) **mitigado** — o checkpoint human-verify confrontou os 5 tickers reais contra os alvos e aprovou.
- T-09-07 / T-09-08 (rede pública / superfície offline de testes) **accept** — sem credenciais/PII; APIs públicas gratuitas já em uso.

## Next Phase Readiness
- Núcleo de metodologia da Fase 9 validado ponta a ponta (offline + live). Fase 10 (de-poison do screening) tem o cross-effect registrado em `09-CROSS-EFFECT-FASE10.md` como item de verificação. A trava multi-ticker FORMAL/completa (TEST-08) é da Fase 11.

## Self-Check: PASSED
- FOUND: tests/test_payout_sustentavel_multiticker.py
- FOUND: .planning/phases/09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia/09-CROSS-EFFECT-FASE10.md
- FOUND commit: 7048fa3 (Task 1 test)

---
*Phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia*
*Completed: 2026-06-27*
