---
phase: 13-motores-contrato-de-sa-da-eng
plan: 05
subsystem: config-lock-motores
tags: [ENG-06, ENG-10, knob-cut, calibracao-lock, margem-seguranca]
requires: [13-03, 13-04]
provides: [motores-5-folhas, MS-default-5pct, san01-removido]
affects: [config.yaml, calibracao.lock.yaml, report._roe0_ciclico]
tech-stack:
  added: []
  patterns: [co-change-config-lock, knob-cut-contado, trailer-sem-ticker]
key-files:
  created: []
  modified:
    - config.yaml
    - calibracao.lock.yaml
    - src/analista/report/report.py
decisions:
  - "MS default = 0.05 (5% simétrico do livro, Cap. 17), não 0.10"
  - "ciclica.anos_media migrou para motores.rim.anos_ciclica (política de input do RIM)"
metrics:
  duration: 15min
  completed: 2026-07-20
  tasks: 2
  files: 3
---

# Phase 13 Plano 05: Knob-cut motores 7→5 + MS default (ENG-06/ENG-10) Summary

Corte contado do bloco `motores:` de 7 para 5 folhas com o `calibracao.lock.yaml` reescrito no
mesmo commit e o orçamento intacto em 3 graus; MS default de 0.15 para 5% simétrico (ENG-06) e
remoção do config morto `veredito.san01`.

## What Was Built

### Task 1 — Knob-cut motores 7→5 (config + lock + consumidor coeso) — `a638142`

O bloco `motores:` do `config.yaml` foi de **7 folhas para 5 CONTADAS** (uma única chave `rim`
com 5 folhas: `n_fade`, `excesso_sustentavel`, `ke_g_spread_min`, `roe_terminal_stat`,
`anos_ciclica`). Os sub-blocos `motores.ciclica` e `motores.crescimento` **colapsaram** porque
`dcf_crescimento`/`lucro_normalizado` deixaram de ser motores no RIM único (Plano 03):

- `ciclica.anos_media` → **MOVIDA** para `motores.rim.anos_ciclica` (política de input do RIM
  único: a janela da média through-cycle que ancora o ROE0 do arquétipo cíclico).
- `ciclica.winsor` → **DELETADA** (inerte desde PRIM-02).
- `crescimento.n_anos_explicito` → **DELETADA** (o DCF morreu; o RIM usa `n_fade`).

O `calibracao.lock.yaml` foi reescrito **no mesmo commit**: escopo **26→24 folhas** (motores 5)
nos 3 lugares (escopo :34 / header dos congelados :122 / comentário de partição :136); congelados
renomeados (`motores.rim (4)`→`(5)`, `anos_media`→`rim.anos_ciclica`) e as 2 folhas mortas
removidas; **`graus_de_liberdade` INTOCADO** (ERP 0.045, n_fade 10, PIB_real 0.02 — os 3 graus).
O único consumidor da knob movida, `report._roe0_ciclico`, passou a ler
`cfg["motores"]["rim"]["anos_ciclica"]` (winsor agora hardcoded 0.10) **no mesmo diff** — sem
estado quebrado. Trailer `Knob-Change-Justification:` de razão econômica sem ticker; hook
BLIND-05 passou sem `--no-verify`.

### Task 2 — MS default 5% simétrico (ENG-06) + remove san01 morto — `9c264b1`

- `veredito.margem_seguranca`: **0.15 → 0.05** (MS simétrica do usuário, default do livro Cap. 17
  — o valor do caso-exemplo). **Co-change** no `user_control` do `calibracao.lock.yaml` (`valor:
  0.05`), mesmo commit. A MS segue **fora dos 3 graus** (é controle do usuário, não grau de
  liberdade) — orçamento intacto.
- Bloco morto `veredito.san01` **removido** do config (`_guarda_san01` morreu no Plano 03);
  `grep -c san01 config.yaml == 0`. `veredito` está fora do escopo do lock (exceto `margem_seguranca`
  no user_control), então a remoção não mexe na partição.

Verificação: `pytest -q` **485 passed, 1 skipped, 18 deselected, 0 failed** (baseline pós-13-04
preservado); `pytest -k 'orcamento or knobs_batem_com_o_lock or justificativa'` **4 passed**;
`git diff tests/` VAZIO nos dois commits.

## Deviations from Plan

**1. [Rule 1 - Bug] Comentário do config mencionava ticker na justificativa da MS**
- **Found during:** Task 2 (primeira execução do `pytest -k justificativa`)
- **Issue:** o comentário novo de `veredito.margem_seguranca` no `config.yaml` citava o ticker do
  caso-exemplo ("usa ±5% no caso-exemplo ITUB4"), disparando
  `test_nenhuma_justificativa_de_knob_menciona_ticker` (CR-05: o user_control é varrido). Uma
  justificativa de knob NUNCA menciona ticker.
- **Fix:** reescrito para "a MS simétrica do livro (Cap. 17), o valor do caso-exemplo" — sem nomear
  o papel. A economia (fidelidade ao livro) é a mesma; o ticker sai.
- **Files modified:** config.yaml
- **Commit:** 9c264b1 (corrigido antes do commit; a suíte só ficou verde depois)

**Decisão de nível:** `margem_seguranca = 0.05` (não 0.10). O plano permitia 5–10%; escolhido
**5%** porque é o valor exato do caso-exemplo do livro (Cap. 17, região R$ 35–39, MS ±5%),
alinhado ao critério de aceite soberano do marco v2.4. Não é ajuste contra dispersão/preço.

## Threat Surface

Nenhuma superfície de segurança nova (config/lock/report). As 3 mitigações do threat_model do
plano foram honradas:
- **T-13-11** (justificativa com ticker): trailer sem ticker + `test_..._menciona_ticker` verde
  (o desvio Rule 1 acima foi exatamente esta guarda pegando o furo antes do commit).
- **T-13-12** (4º grau escondido): `graus_de_liberdade` intocado; `n_fade` preservado;
  `test_orcamento_de_knobs_e_exatamente_3` verde (partição folhas==graus|congelados consistente).
- **T-13-13** (co-change escondido com tests): `git diff tests/` VAZIO nos dois commits; o plano
  tocou só config+lock+report → não disparou o hook BLIND-05.

## Self-Check: PASSED

- Arquivos modificados existem: config.yaml, calibracao.lock.yaml, report.py, 13-05-SUMMARY.md.
- Commits existem: `a638142` (Task 1), `9c264b1` (Task 2).
- `motores:` == 5 folhas contadas; `graus_de_liberdade` intocado (3 graus); `pytest -q` 485/1/18/0.
