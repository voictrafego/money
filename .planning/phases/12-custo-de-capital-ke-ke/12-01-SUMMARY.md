---
phase: 12-custo-de-capital-ke-ke
plan: 01
subsystem: valuation-engine
tags: [capm, beta, blume, beta-setorial, carimbo, fonte-unica, ke, yaml, tdd]

# Dependency graph
requires:
  - phase: 11-crescimento-g-grow
    provides: "padrão de carimbo de fonte única (pi_ciclo/ipca_deflatores) espelhado aqui; g_cap=7,28% que o Ke_min do Blume terá de superar"
  - phase: 09-ingestao-correta-data
    provides: "snapshot_sanidade_limpo_2026-07-15.yaml (104 tickers com setor+beta) — a fonte offline do artefato"
provides:
  - "data/beta_setorial.yaml — mapa versionado setor_normalizado -> mediana(beta cru), 14 setores (n>=3)"
  - "macro.mapa_beta_setorial / _normalizar_setor / carregar_beta_setorial / carimbar_beta_setorial"
  - "capm.beta_blume(beta_cru, setor, mapa) — Blume 0,33+0,67xbase uma vez, setorial>individual, never-raise"
  - "carimbo do beta setorial nos 3 entry points (cli/app/backtest) — fonte única analyze==rank (D-06)"
affects: [12-02-ke-consumo, 13-motores-contrato-eng, 14-validacao-honesta-val]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "beta setorial = DADO derivado do mercado, carimbado em cfg (fora do lock, D-07) — espelha rf_local/pi_ciclo"
    - "engine pura lê cfg[capm][beta_setorial]; a rede/artefato vive na borda (entry points); nunca recomputa a mediana por run (WR-03)"

key-files:
  created:
    - data/beta_setorial.yaml
    - scripts/gerar_beta_setorial.py
    - tests/test_beta_setorial.py
  modified:
    - src/analista/ingest/macro.py
    - src/analista/core/capm.py
    - src/analista/cli.py
    - app.py
    - src/analista/backtest.py
    - tests/test_cli_rank_consistencia.py
    - tests/classificacao.yaml

key-decisions:
  - "Limiar estrutural = 3 (menor n em que a mediana rejeita 1 outlier — propriedade da mediana, nunca alvo de ticker)"
  - "_normalizar_setor faz strip do prefixo 'Emp. Adm. Part. - ' (holding e operadora agrupam; fallback 42->24 de 104)"
  - "beta_blume(None,...) -> None ANTES de olhar o mapa: contrato de borda 'beta None -> None' da engine (como ke_rim), mesmo com setor no mapa"
  - "capm importa ingest.macro para a normalização de setor (fonte única) — sem ciclo, sem acoplar a engine à rede (função pura)"
  - "backtest: beta_setorial em _CHAVES_GLOBAIS + injetado na cópia do cfg em rodar_cesta (degrada {} quando ausente)"

patterns-established:
  - "Artefato derivado, não digitado: scripts/gerar_beta_setorial.py regenera data/beta_setorial.yaml do snapshot limpo"
  - "Teste de derivação: o artefato == recomputação do mapa sobre o universo real (prova o limiar de quebra)"

requirements-completed: [KE-03]

# Metrics
duration: 15min
completed: 2026-07-17
---

# Phase 12 Plan 01: Infraestrutura do beta setorial + Blume (KE-03) Summary

**Gerador offline + artefato versionado `data/beta_setorial.yaml` (14 setores, mediana do beta cru), `capm.beta_blume` never-raise (setorial > individual) e carimbo de fonte única nos 3 entry points — PURAMENTE ADITIVO: nada consome o mapa ainda, `a.ke` inalterado, suíte verde e sem knob tocado.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-17T17:44:32Z
- **Completed:** 2026-07-17T17:59:03Z
- **Tasks:** 2 (ambas TDD)
- **Files modified:** 10 (3 criados, 7 modificados)

## Accomplishments

- **Gerador offline + artefato versionado.** `macro.mapa_beta_setorial` agrupa por setor normalizado, coleta os `c.beta` não-None e emite a **mediana** só para setores com `n_betas >= 3` (limiar estrutural). `scripts/gerar_beta_setorial.py` roda offline sobre o snapshot limpo (104 tickers) e produziu `data/beta_setorial.yaml` com **14 setores** — números idênticos à distribuição medida no RESEARCH (Energia Elétrica 0,615, Bancos 1,216, Comércio 1,154, …).
- **`capm.beta_blume`** aplica Blume `0,33 + 0,67 × base` **uma vez** sobre a mediana setorial (fallback ao β individual quando o setor está ausente do mapa, D-04), com contrato `beta None → None` (never-raise, como `ke_rim`).
- **Carimbo de fonte única nos TRÊS entry points** (`cli._carimbar_macro`, `app.py`, `backtest`) — a engine lê `cfg["capm"]["beta_setorial"]`, nunca recomputa a mediana (anti-padrão WR-03). `report/setup.py` **não** foi tocado (Correção #2 do RESEARCH).
- **D-06 provado por teste DURO cross-menu:** `test_cli_rank_consistencia` agora assevera que `beta_setorial` **e** `a.ke` são **idênticos** entre `analyze` e `rank` para a mesma ação.

## Task Commits

Cada task foi committada atomicamente (TDD: RED test → GREEN feat):

1. **Task 1: Gerador offline do mapa setorial + artefato**
   - `d0af0ac` (test — RED: mapa/normalizar/carregar + derivação)
   - `8804622` (feat — GREEN: 3 funções em macro.py + script + artefato)
2. **Task 2: capm.beta_blume + carimbo nos 3 entry points + D-06 cross-menu**
   - `17b43c2` (test — RED: beta_blume + carimbo + spy estendido)
   - `5a03a40` (feat — GREEN: beta_blume + carimbar_beta_setorial + 3 sítios)

## Files Created/Modified

- `data/beta_setorial.yaml` — mapa versionado setor→mediana(β), 14 setores (n≥3), derivado do snapshot limpo
- `scripts/gerar_beta_setorial.py` — build offline (irmão de `capturar_snapshot_limpo.py`)
- `tests/test_beta_setorial.py` — 18 testes (gerador, artefato, beta_blume, carimbo)
- `src/analista/ingest/macro.py` — `_normalizar_setor`, `mapa_beta_setorial`, `carregar_beta_setorial`, `carimbar_beta_setorial`
- `src/analista/core/capm.py` — `beta_blume` (importa `ingest.macro` para a normalização; `ke_local` intocado)
- `src/analista/cli.py` — `_carimbar_macro` carimba o mapa (analyze==rank)
- `app.py` — carimbo do mapa no bloco Streamlit (espelha `rf_capm`)
- `src/analista/backtest.py` — `beta_setorial` em `_CHAVES_GLOBAIS` + injeção em `rodar_cesta`
- `tests/test_cli_rank_consistencia.py` — spy `vistos` estendido (beta_setorial + a.ke cross-menu)
- `tests/classificacao.yaml` — +18 entradas (invariante/contrato), 0 órfão

## Decisions Made

- **Limiar = 3, justificativa estrutural.** É o menor n em que a mediana rejeita 1 outlier — propriedade da mediana amostral (D-02), nunca um alvo de ticker (passa no hook `commit-msg` e no `-k justificativa`).
- **`beta_blume(None, setor, mapa) → None` antes de consultar o mapa.** O contrato de borda da engine é "β None → None" (mesmo do `ke_rim`, citado no CONTEXT). A ambiguidade do pseudo-código do RESEARCH (que retornaria a base setorial mesmo com β cru None) foi resolvida a favor do contrato de borda explícito do bloco `<behavior>` do plano.
- **`capm` importa `ingest.macro`** para a normalização de setor (fonte única, sem drift) — verificado sem ciclo de import e sem acoplar a engine à rede (`_normalizar_setor` é pura).

## Deviations from Plan

None - plan executed exactly as written. Nenhum bug, funcionalidade crítica faltante ou bloqueio encontrado; as duas tasks seguiram o `<behavior>`/`<action>` do plano. Zero knob/lock/golden tocado.

## Issues Encountered

None. A única sutileza foi a ambiguidade do caso `beta_blume(None, "Bancos", mapa)` entre o pseudo-código do RESEARCH e o bloco `<behavior>` do plano — resolvida a favor do `<behavior>` (contrato de borda "β None → None"), consistente com o `ke_rim`.

## Additive-only (não é stub)

Este plano é declaradamente **ADITIVO**: `capm.beta_blume` **ainda não é consumido** por `a.ke` (a engine segue lendo `capm.ke_local(c.beta, ...)` com β cru e ERP 0,06). Isso é **intencional e planejado** — o consumo do mapa (que muda o Ke, remove o clamp e destrava BLIND-02b) é o **Plano 02**. Não é um stub de dado vazio fluindo para a UI: é infra montada antes da mudança de comportamento, de propósito (separar montagem da fonte-única da mudança de Ke). Prova: `BLIND-02b permanece xfailed` (viraria XPASS=FAIL se o Ke tivesse mudado aqui).

## Verification

- `pytest -k "beta_setorial or capm or cli_rank_consistencia"` → **28 passed**.
- `pytest` (suíte default) → **517 passed, 1 skipped, 22 deselected, 1 xfailed, 0 failed** (era 499; +18 testes novos; base inalterada).
- `pytest -m golden_nivel` → **22 passed, 0 CLASSIFICACAO ORFA**.
- `BLIND-02b` (`test_invariancia_inflacao_engine_itub4`) **permanece xfailed** (não XPASS) — prova de que `a.ke` não mudou.
- `grep beta_setorial` casa nos **3** entry points; `report/setup.py` = **0** (Correção #2).
- `git diff config.yaml calibracao.lock.yaml` **VAZIO** — orçamento de 3 knobs intacto (β setorial é DADO, fora do lock, D-07).

## Next Phase Readiness

- **Plano 02 (KE consumo)** pode agora: apontar `a.ke` para `capm.beta_blume(c.beta, c.setor, cfg["capm"]["beta_setorial"])`, baixar ERP 0,06→0,045 (com o lock no mesmo diff), deletar `motores.ke_rim`/`ke_piso`/`ke_teto` e destravar BLIND-02b. Toda a infra de fonte-única e o invariante DURO analyze==rank já estão no lugar e verdes.
- Nenhum blocker. A régua dos 104 tickers (`helpers_sanidade`) e o carimbo em `backtest` já suportam a validação D-11 do Plano 02.

## Self-Check: PASSED

- Arquivos criados verificados no disco: `data/beta_setorial.yaml`, `scripts/gerar_beta_setorial.py`, `tests/test_beta_setorial.py`.
- Commits verificados no git log: `d0af0ac`, `8804622`, `17b43c2`, `5a03a40`.

---
*Phase: 12-custo-de-capital-ke-ke*
*Completed: 2026-07-17*
