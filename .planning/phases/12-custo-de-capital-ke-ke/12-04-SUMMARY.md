---
phase: 12-custo-de-capital-ke-ke
plan: 04
subsystem: valuation-validacao
tags: [ke, ke-min, piso-blume, g-cap, clamp-removido, anti-explosao, blind-04a, prova-por-execucao, wave-4]

# Dependency graph
requires:
  - phase: 12-custo-de-capital-ke-ke
    plan: 03
    provides: "capm.erp_local == 0.045 no config+lock; folhas do clamp (erp_banco/ke_piso/ke_teto) REMOVIDAS; orcamento em 3 graus. O estado final (ERP 0,045, sem clamp) que este plano valida por execucao"
  - phase: 12-custo-de-capital-ke-ke
    plan: 02
    provides: "Ke unico (a.ke) via beta_blume; ke_rim/clamp DELETADO por codigo; a perpetuidade converge pelo piso do Blume por aritmetica"
provides:
  - "test_ke_validacao.py: invariante estrutural Ke_min (rf + 0,33 x erp_local) > g_cap como DESIGUALDADE lida do config (robusta ao drift do rf), sem cravar 11,07%"
  - "regressao anti-explosao sobre os 104 tickers REAIS (snapshot limpo) com o Ke setorial+Blume carimbado (identico ao app): todo Ke >= Ke_min > g_cap, V finito/positivo, spread Ke-g_T > 0, V < 50x preco — SEM clamp, nenhum guard novo"
  - "KE-04 fechado por PROVA DE EXECUCAO (memoria guardrails-devem-ser-provados-por-execucao): 93 tickers com Ke rodados, zero ofensor; Doenca 3 encerrada"
affects: [13-motores-contrato-eng, 14-validacao-honesta-val]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "guardrail provado por EXECUCAO, nao por suite verde: o teste RODA o dispatch da engine sobre o mapa real dos 104 e OBSERVA (never-raise, None aceitavel), nunca corrige — se explodisse, o bug seria ROE_T/spread (Fase 13), nao um clamp"
    - "invariante como DESIGUALDADE, nunca numero cravado: Ke_min > g_cap lido dinamicamente do config (passaria com ERP 0,06 e com 0,045); o piso do Blume 0,33 e' o intercepto estrutural, sem alvo de ticker (BLIND-04a-safe)"

key-files:
  created:
    - tests/test_ke_validacao.py
  modified:
    - tests/classificacao.yaml

key-decisions:
  - "invariante escrito como DESIGUALDADE (Ke_min > g_cap), 11,07% so' em comentario (rf ao vivo) — cravar o numero seria overfit ao Selic-ciclo de hoje; a desigualdade e' robusta ao drift do rf (offline da ~11,99%)"
  - "piso do Blume asseverado no INTERCEPTO (beta_blume(0)==0,33) e nao com beta negativo: o codigo e' 0,33+0,67xbase (sem floor), entao o piso 0,33 vale honestamente para todo beta>=0 (o equity) — guarda honesta, nao rubber stamp"
  - "a regressao carimba o beta_setorial (macro.carimbar_beta_setorial) para o Ke offline usar o beta SETORIAL identico ao app (D-06), nao o beta individual — senao a validacao divergiria do produto"
  - "ambos os testes classificados invariante (verdade estrutural + anti-explosao adimensional), no MESMO diff em classificacao.yaml (zero orfao)"

patterns-established:
  - "espelho do GROW-04/05 (test_nao_regressao_grow): mesmo harness offline dos 104 (snapshot limpo), mesmo _valor_efetivo (motor OU meio-da-banda OU None), mesmo FATOR_SANIDADE 50x sem nomear ticker — agora para o Ke"

requirements-completed: [KE-04]

# Metrics
duration: 20min
completed: 2026-07-17
---

# Phase 12 Plan 04: Validacao por execucao — nada explode sem clamp Summary

**O gate final da Fase 12: "nada explode sem clamp" (KE-04 / Doenca 3) fica provado por EXECUCAO, nao por suite verde. `tests/test_ke_validacao.py` traz as duas formas exigidas — (a) o invariante estrutural `Ke_min = rf + 0,33 x erp_local > g_cap` como DESIGUALDADE lida do config (nunca cravando 11,07%; o piso do Blume 0,33 asseverado no intercepto), e (b) a regressao anti-explosao rodando o dispatch da engine sobre os 104 tickers REAIS com o Ke setorial+Blume carimbado (identico ao app): os 93 com Ke satisfazem todos `Ke >= Ke_min > g_cap`, `V` finito/positivo, spread `Ke - g_T > 0` e `V < 50x preco` — ZERO ofensor, NENHUM guard novo. A perpetuidade converge pela aritmetica do piso do Blume, nao por trava. Suite 519 passed, 1 skipped, 0 failed/xfailed/xpassed; config/lock intocados (validacao pura).**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2 (ambas `auto`, `tdd`)
- **Files created:** 1 · **modified:** 1

## Accomplishments

- **Invariante estrutural `Ke_min > g_cap` como DESIGUALDADE (Task 1).** `test_ke_min_estrutural_acima_do_g_cap` le `erp_local`, `rf` e o `g_cap` (derivado `(1+pi_ciclo)(1+pib_real)-1`, a FONTE UNICA da engine) do config DINAMICAMENTE e assevera `rf + 0,33 x erp_local > g_cap` — robusta ao drift do rf (passaria com ERP 0,06 e com 0,045). O "11,07%" (que corresponde ao rf AO VIVO ~9,58%) aparece **so' em comentario**, nunca num assert (`grep` de `0.1107`/`0.11065`/`11,07` em linha de assert == 0; as 2 ocorrencias sao docstring). O **piso do Blume 0,33** e' asseverado no INTERCEPTO (`beta_blume(0.0, "setor_inexistente", {}) == 0,33`) + monotonicidade (`beta_blume(2.0, ...) >= 0,33`), provando que `Ke_min` INDEPENDE de outlier de beta.
- **Regressao anti-explosao dos 104 REAIS (Task 2).** `test_regressao_104_sem_explosao` carrega as empresas do `hs.CAMINHO_SNAPSHOT_LIMPO` (OFFLINE, 104 tickers) e **carimba o beta_setorial** (`macro.carimbar_beta_setorial(cfg)`) para o Ke offline usar o beta SETORIAL+Blume identico ao app (D-06). Roda `report.analisar_acao` por ticker (pulando as `falhas_do_snapshot`) e observa, por ticker COM Ke: `a.ke >= Ke_min` (piso do Blume), `intrinseco_motor` finito e `> 0`, spread `a.ke - g_T > 0` (com `g_T = max(0, min(ROE_T x retencao, g_cap))` derivado como a engine), e o limite adimensional `V < 50x preco`. **Medido por execucao: 93 tickers com Ke, ZERO ofensor.** `None` e' aceitavel (never-raise / falha de mercado); nenhuma excecao levantada.
- **Guardrail provado por EXECUCAO, nao por suite verde (memoria `guardrails-devem-ser-provados-por-execucao`).** O teste RODA a regressao end-to-end e OBSERVA — nao corrige. **Nenhum guard novo introduzido, nenhum clamp sob outro nome.** Se algum V explodisse, o assert reportaria o ofensor e o bug seria no ROE_T/spread (Fase 13), nunca a reintroducao do `ke_teto`.
- **BLIND-04a limpo.** Nenhuma assertiva cruza `ticker == valor de nivel`: os limiares sao estruturais/adimensionais (intercepto 0,33; desigualdade Ke_min > g_cap; multiplo de preco 50x sem nomear ticker). `test_blindagem_meta` (varredura AST) segue **verde** com o arquivo novo — os tickers so' aparecem interpolados em mensagens de erro, nunca num assert com constante.
- **Fronteira respeitada — validacao PURA.** `git diff 615843f..HEAD -- config.yaml calibracao.lock.yaml` **VAZIO**: nenhum knob de valuation tocado (o commit sancionado config+lock foi o 12-03). Orcamento em 3 graus intacto; g_cap da Fase 11 nao recalibrado; nenhum motor tocado (o corte `motores:` e' a Fase 13). `xfail_estritos()` segue **0**.

## Task Commits

1. **Task 1: invariante estrutural Ke_min (piso do Blume) > g_cap** — `7d85b65` (test)
2. **Task 2: regressao anti-explosao dos 104 tickers sem clamp (D-11a)** — `6f008d0` (test)

## Files Created / Modified

- `tests/test_ke_validacao.py` (**criado**) — 2 testes `invariante`: `test_ke_min_estrutural_acima_do_g_cap` (desigualdade + piso do Blume) e `test_regressao_104_sem_explosao` (mapa real + beta setorial carimbado + spread/limite adimensional); helpers `_g_cap`, `_cfg_offline_com_beta_setorial`, `_valor_efetivo`, `_g_terminal` (constroem, nao conferem)
- `tests/classificacao.yaml` — 2 entradas `invariante` para os testes novos, no MESMO diff (completude da coleta preservada, 0 orfao)

## Decisions Made

- **DESIGUALDADE, nunca numero cravado.** O `11,07%` e' o Ke_min no rf AO VIVO; cravar seria overfit ao Selic-ciclo de hoje e quebraria quando o rf driftar. A desigualdade `Ke_min > g_cap` lida do config e' a forma honesta e robusta (Pitfall 3 do RESEARCH).
- **Piso do Blume no intercepto, honestamente.** O codigo e' `0,33 + 0,67 x base` (sem floor explicito). O piso 0,33 vale para todo `base >= 0` (o equity); assevero `beta_blume(0)==0,33` (intercepto exato) + monotonicidade, em vez de um beta negativo — que matematicamente daria `< 0,33` e tornaria a guarda um falso positivo. Guarda tight e honesta, nunca rubber stamp (CLAUDE.md).
- **Ke setorial carimbado na regressao.** Sem `carimbar_beta_setorial`, o Ke offline cairia no beta individual e divergiria do app (WR-03/D-06). Carimbar espelha os entry points (`cli._carimbar_macro`/`app.py`) — a validacao mede o MESMO Ke que o produto entrega.

## Deviations from Plan

None - plano executado exatamente como escrito. (Empiricamente confirmado ANTES de fixar a estritude do assert: os 93 tickers com Ke satisfazem `Ke >= Ke_min` e nenhum se aproxima de g_cap; max V/preco = 4,7x, folgado sob o limite de 50x — o assert estrito e' honesto e passa.)

## Threat Flags

Nenhuma superficie nova (T-12-06 accept): validacao OFFLINE sobre snapshot congelado dos 104 + artefato beta_setorial versionado; sem rede, auth, secrets ou input nao confiavel. O teste OBSERVA, nao muta estado nem introduz endpoint.

## Verification

- `pytest -k "ke_min_estrutural"` -> **1 passed** (desigualdade + piso do Blume).
- `pytest -k "regressao_104 or ke_min_estrutural or blindagem_meta"` -> **4 passed, 1 skipped** (o skip e' o jackknife do BLIND-04a/Fase 14); o arquivo novo NAO e' flagado pela varredura AST.
- `pytest` (suite default) -> **519 passed, 1 skipped, 20 deselected, 0 failed, 0 xfailed, 0 xpassed** (517 do pos-12-03 + os 2 testes novos).
- `pytest -m golden_nivel` -> **20 passed, 0 CLASSIFICACAO ORFA**.
- `grep -Ec "0\.1107|0\.11065|11,07" tests/test_ke_validacao.py` -> 2, ambos em docstring/comentario; **0 em linha de assert**.
- `grep -v '^#' tests/classificacao.yaml | grep -c "ke_min_estrutural"` -> **1**; idem `regressao_104` -> **1**.
- `grep -c "beta_setorial\|carimbar_beta_setorial" tests/test_ke_validacao.py` -> **>= 1** (o Ke offline usa o mapa).
- `git diff 615843f..HEAD -- config.yaml calibracao.lock.yaml` -> **VAZIO** (validacao pura; orcamento de 3 graus intacto).
- Medicao por execucao (script offline): 93 tickers com Ke analisados, 0 abaixo de Ke_min, 0 <= g_cap, max V/preco 4,7x.

## Next Phase Readiness

- **KE-04 fechado por prova de execucao — a Fase 12 esta pronta para fechar.** As duas metades da Doenca 1 (vies) foram curadas (BLIND-02b no 12-02) e a Doenca 3 (clamp) morreu por codigo (12-02), por orcamento (12-03) e agora por VALIDACAO (12-04). Nenhum clamp reintroduzido; a perpetuidade converge pela aritmetica do piso do Blume.
- **Fronteira respeitada:** g_cap da Fase 11 nao recalibrado; orcamento em 3 graus; nenhum motor tocado (o corte `motores:` ~11 -> <=5 e' a Fase 13).
- Nenhum blocker.

## Self-Check: PASSED

- Arquivos verificados no disco: `tests/test_ke_validacao.py`, `tests/classificacao.yaml`, `.planning/phases/12-custo-de-capital-ke-ke/12-04-SUMMARY.md`.
- Commits verificados no git log: `7d85b65`, `6f008d0`.
- Grep: `ke_min_estrutural` (nao-comentario) == 1; `regressao_104` == 1; `beta_setorial` >= 1; config/lock diff VAZIO.

---
*Phase: 12-custo-de-capital-ke-ke*
*Completed: 2026-07-17*
