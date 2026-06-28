---
phase: 10-crescimento-robusto-de-poison-do-screening
plan: 03
subsystem: testing
tags: [growth, screening, comparables, multi-ticker, golden, de-poison, validacao-de-aceite]

# Dependency graph
requires:
  - phase: 10-crescimento-robusto-de-poison-do-screening
    provides: growth.crescimento_log_linear (Plan 01) + BSD log-linear/winsorizado e clamp do fit (Plan 02)
  - phase: 09-payout-sustent-vel-dy-recorrente-n-cleo-de-metodologia
    provides: trava de validação multi-ticker em 2 camadas (golden offline + checkpoint live) — template espelhado
provides:
  - "Golden offline de propriedade multi-ticker do estimador robusto + de-poison (tests/test_growth_robusto_multiticker.py)"
  - "Trava de aceite do marco fechada: VULC3 não infla g/BSD, normais não regridem, TAEE11 não distorce preço-alvo — confirmado offline E live nos 5 tickers reais"
  - "Suíte completa verde (171 testes) sem rebaseline — confirmação de que a troca CAGR→log-linear preservou todos os goldens de valor"
affects: [11 (apresentação + trava de fechamento TEST-08 estende esta validação multi-ticker)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Golden de PROPRIEDADE multi-ticker (perfis sintéticos VULC3/normais/TAEE11, asserts de desigualdade/igualdade estrutural, offline) como trava de aceite de marco — espelha test_payout_sustentavel_multiticker.py"

key-files:
  created:
    - tests/test_growth_robusto_multiticker.py
  modified: []

key-decisions:
  - "Nenhum golden precisou de rebaseline: a suíte ficou verde de verdade (171 passed). Os goldens de valor exato sobreviveram à troca CAGR→log-linear porque as séries de teste são planas/monótonas (direção preservada) e não há assert de valor exato sobre g_historico nem crescimento_*_3a (D-04/D-07 confirmados)"
  - "VULC3 (a): assert g_historico < CAGR endpoint do MESMO par (winsorizado E cru) — o spike na ponta deixa de mandar no g; idem para crescimento_lucro_3a do BSD"
  - "Consistência Analisar↔Screening travada por igualdade EXATA: indicadores_bsd(c)['crescimento_lucro_3a'] == report.analisar_acao(c,cfg).g_historico (D-04)"
  - "TAEE11 (c): assert np.allclose(fit(2.16), fit(1.0)) — o clamp [0,1] na entrada do fit neutraliza payout >100% (D-06); preço-alvo finito/positivo + flag payout_fora_faixa"
  - "Bandas REFERENCIA_BSD NÃO alteradas (D-07): a inspeção de bucket é só leitura/anotação"

requirements-completed: [GROW-01, GROW-02]

# Metrics
duration: 22min
completed: 2026-06-27
---

# Phase 10 Plan 03: Validação multi-ticker + rebaseline deliberado Summary

**Trava de aceite do marco fechada: novo golden offline de propriedade multi-ticker (VULC3/normais/TAEE11) prova por regra geral que o de-poison vale para qualquer ticker; a suíte completa (171 testes) ficou verde SEM rebaseline; e o checkpoint live dos 5 tickers reais foi aprovado pelo usuário — VULC3 não infla g/BSD (31,5% < endpoint-CAGR 47,2%), normais não regridem, TAEE11 com preço-alvo sensato após o clamp do fit, buckets do BSD sem colapso e REFERENCIA_BSD intacta.**

## Performance

- **Duration:** ~22 min (inclui o checkpoint live com rede)
- **Completed:** 2026-06-27
- **Tasks:** 3 (2 auto + 1 checkpoint human-verify)
- **Files modified:** 1 (1 criado)

## Accomplishments

- **Task 1 — Golden offline de propriedade multi-ticker** (`tests/test_growth_robusto_multiticker.py`, 5 testes, verde): espelha `test_payout_sustentavel_multiticker.py` (helper `_mk` sintético, offline, config.yaml shipado, 1 comentário "pelo método" por assert). Cobre os 3 critérios de aceite + a consistência D-04:
  - (a) VULC3 (recorrente 1000×9 + spike 4000): `g_historico` log-linear < CAGR endpoint-a-endpoint do mesmo par (winsorizado **e** cru); idem `crescimento_lucro_3a`.
  - (D-04) `indicadores_bsd(c)["crescimento_lucro_3a"] == report.analisar_acao(c,cfg).g_historico` (igualdade estrutural exata).
  - (b) normais (ITUB4/EGIE3 spirit, crescentes): `g_historico` finito/positivo, os 3 fatores `crescimento_*_3a` finitos e positivos (sem colapso).
  - (c) TAEE11: `np.allclose(ajustar_regressao_pl(payout=2.16), ajustar_regressao_pl(payout=1.0))` + preço-alvo finito/positivo e `payout_fora_faixa is True`.
- **Task 2 — Suíte completa + rebaseline deliberado:** `pytest -q` = **171 passed**, exit 0. **Nenhum golden precisou de rebaseline** (ver tabela abaixo). Nenhuma propriedade afrouxada. Bandas `REFERENCIA_BSD` não tocadas (D-07).
- **Task 3 — Checkpoint live (5 tickers reais), APROVADO pelo usuário:** rodei `analyze`/`rank`/`screen` ao vivo (rede CVM/Yahoo/BCB) e apresentei a evidência; o usuário aprovou explicitamente os 4 critérios.

## Tabela de rebaseline (delta deliberado)

| Ticker/Teste | Antigo → Novo | Justificativa |
|--------------|---------------|---------------|
| (nenhum) | — | **Zero rebaselines.** A suíte ficou verde de verdade (171 passed). Os goldens de valor exato (`test_report.py`, `test_screening.py`, `test_comparables.py`, `test_consistencia_modos.py`, `test_ddm.py`) sobreviveram à troca CAGR→log-linear porque (1) usam séries **planas/monótonas** onde log-linear e CAGR coincidem em direção/valor, e (2) **nenhum** assert de valor exato incide sobre `g_historico` nem sobre `crescimento_*_3a` (confirmado por grep — zero ocorrências). As desigualdades de `test_growth_reconciliacao.py` (séries monótonas) seguem intactas. |

## Inspeção de bucket — fatores crescimento_*_3a vs bandas REFERENCIA_BSD (live, D-07)

Bandas inalteradas (lucro_3a `(-0.05, 0.15)`, dividendos_3a `(0.0, 0.12)`, fc_3a `(-0.05, 0.15)`). Notas observadas ao vivo:

| Ticker | lucro_3a | nota | dividendos_3a | nota | fc_3a | nota | BSD |
|--------|----------|------|---------------|------|-------|------|-----|
| VULC3 | 31,5% | 100 | 113,9% | 100 | 16,4% | 100 | 69,9 |
| ITUB4 | 6,9% | 60 | 13,1% | 100 | 11,3% | 81 | 67,6 |
| EGIE3 | 7,0% | 60 | 6,2% | 51 | 7,9% | 65 | 67,5 |
| TAEE11 | 8,0% | 65 | 5,7% | 48 | 0,0% | 25 | 58,7 |
| BBAS3 | 9,1% | 71 | 19,5% | 100 | None | AUSENTE(50) | 54,9 |

**Movimento de bucket:** nenhum normal colapsou para nota 0 nem migrou de banda de forma a distorcer o ranqueamento — as notas dos normais ficam médias-altas e o ordenamento é plausível (VULC3 > ITUB4 ≈ EGIE3 > TAEE11 > BBAS3). VULC3 satura os 3 fatores por crescimento **genuíno** (o spike 2025 foi winsorizado de 1165 → 629,5, então não é ele que pontua). BBAS3 sem FCO → neutro 50 (degradação esperada, não regressão). Bandas REFERENCIA_BSD preservadas (D-07).

## Confirmação live dos 5 tickers reais (Task 3, aprovado)

- **VULC3 (a):** g histórico = **31,5%** (log-linear) < endpoint-CAGR cru **47,2%** e winsorizado **37,4%** — o spike não infla. `g_alto` adotado = 14,3% (capado por g_fundamentos), nem chega ao valuation.
- **Normais (b):** g histórico ITUB4 6,9% / EGIE3 7,0% / TAEE11 8,0% / BBAS3 9,1% — finitos, positivos, coerentes; não regridem.
- **TAEE11 (c):** regressão `P/L = 5,01 + 27,43·DP − 28,73·ROE` (R²=0,92, n=5) — b1 não explode; P/L alvo 40,06, upside +1% (sensato). g_fundamentos −25,6% ⇒ g_alto 0,0% (piso, esperado para payout >100%).
- **Ranking:** VULC3 76,8 > BBAS3 68,6 > EGIE3 57,1 > TAEE11 53,4 > ITUB4 44,6 — sem colapso.

## Decisions Made

None novas — seguiu o plano e as decisões D-01/D-04/D-06/D-07 das fases 10/9.

## Deviations from Plan

None - plan executed exactly as written. (Task 2 não exigiu rebaseline; isso é um resultado esperado/documentado do plano, não um desvio — o gate dos goldens de valor exato rodou e passou.)

## Threat Model Compliance

- **T-10-07** (DoS na rede do checkpoint live): accept — checkpoint manual, dado público, degradação graciosa observada (BBAS3 FCO ausente → campo None, sem crash).
- **T-10-08** (info disclosure no golden offline): accept — perfis 100% sintéticos, sem dado real/PII no código de teste.

## Known Stubs

Nenhum.

## Issues Encountered

- `python`/`python3` do sistema sem pandas; testes e CLI rodam com `.venv/bin/python` (já documentado nos Plans 01/02). Sem impacto no código.
- `out/` é gitignored; os artefatos do live (out/*.md, out/screen.csv) não poluem o repo.

## Next Phase Readiness

- Marco de metodologia (payout sustentável + DY recorrente + crescimento robusto + de-poison) validado ponta a ponta, offline e live.
- Phase 11 (apresentação + TEST-08) estende esta trava multi-ticker; o golden de propriedade `test_growth_robusto_multiticker.py` é reutilizável como base do TEST-08.

## Self-Check: PASSED

- FOUND: tests/test_growth_robusto_multiticker.py (5 funções test_, verde)
- FOUND: commit 7b9568a (test 10-03 golden multi-ticker)
- VERIFIED: pytest -q = 171 passed, exit 0
- VERIFIED: live analyze/rank/screen nos 5 tickers + aprovação do usuário

---
*Phase: 10-crescimento-robusto-de-poison-do-screening*
*Completed: 2026-06-27*
