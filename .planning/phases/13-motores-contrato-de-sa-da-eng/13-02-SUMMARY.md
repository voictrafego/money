---
phase: 13-motores-contrato-de-sa-da-eng
plan: 02
subsystem: valuation
tags: [arquetipo, ancora-roe, concessao-finita, pagadora-madura, carve-out, split-before-delete]

requires:
  - phase: 13-motores-contrato-de-sa-da-eng
    plan: 01
    provides: "Carve-out CONCESSAO_FINITA medido são (g_terminal=None); split madura→RIM de-riscado a 0 ofensores"
provides:
  - "Registry ARQUETIPO_ANCORA_ROE (arquétipo → política de derivação de ROE-âncora) — o mapa que o RIM único (Plano 03) consome"
  - "Split do arquétipo: PAGADORA_MADURA (default por eliminação) + CONCESSAO_FINITA (hard-route de eh_concessionaria)"
  - "ARQUETIPO_MOTOR legado mantido vivo (herdeiros → ddm) — freio.motor_pendente intacto até o Plano 06"
affects: [13-03, 13-06, mapa-de-ancoras, carve-out-concessao]

tech-stack:
  added: []
  patterns:
    - "Split-before-delete de rótulo de arquétipo: REWRITE dos invariantes que sobrevivem ao relabel, DELETE dos baselines de rota morta — mesmo diff, 0 órfão"

key-files:
  created: []
  modified:
    - src/analista/core/arquetipo.py
    - tests/test_arquetipo.py
    - tests/test_arquetipo_roteamento.py
    - tests/test_vulc3_regressao.py
    - tests/classificacao.yaml

key-decisions:
  - "Valores de ARQUETIPO_ANCORA_ROE seguem o §Mapa de âncoras (policy strings), NÃO a heurística grep da prose do acceptance"
  - "Baseline da rota DDM DELETADO (não reescrito p/ concessao_finita) — o motor vira RIM no Plano 03; reescrever criaria trabalho morto"
  - "Fixture órfã _taee11_regulada removida junto com seu único consumidor (limpeza de escopo)"

requirements-completed: [ENG-03, ENG-04]

duration: 15min
completed: 2026-07-19
---

# Phase 13 Plan 02: Registry de âncora + split do arquétipo Summary

**O classificador ganha o registry `ARQUETIPO_ANCORA_ROE` (arquétipo → política de derivação de ROE-âncora) que o RIM único do Plano 03 consome, e o antigo `PAGADORA_REGULADA` é cindido em `PAGADORA_MADURA` (novo default por eliminação) + `CONCESSAO_FINITA` (hard-route de `eh_concessionaria`, carve-out) — com todos os testes que asseveravam a string morta migrados/deletados no mesmo diff, suíte default 517 passed / 0 failed.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-07-19
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- **Registry `ARQUETIPO_ANCORA_ROE` adicionado** (ENG-03): dict arquétipo → política de derivação de ROE-âncora (6 chaves, strings de política do §Mapa de âncoras): `FINANCEIRA`/`PAGADORA_MADURA` → `through_cycle`, `CONCESSAO_FINITA` → `through_cycle_sem_g` (carve-out), `CICLICA` → `normalizado`, `CRESCIMENTO` → `atual_fade`, `HOLDING` → `nav_piso`. É o mapa que o RIM único (Plano 03) consome.
- **Split do arquétipo** (D-05/ENG-04): o antigo `PAGADORA_REGULADA` (rótulo removido) virou `PAGADORA_MADURA` (novo default-por-eliminação — empresa sem sinal roda RIM normal, não mais o balde da transmissora) + `CONCESSAO_FINITA` (hard-route de `eh_concessionaria`, carve-out declarado ANTES do hold-out). Só as duas linhas de split mudaram no corpo; a árvore de decisão sobrevive intocada.
- **Guarda anti-Petróleo preservada:** `_setor_casa_token(setor, regulada_excluir)` continua no hard-route, agora devolvendo `CONCESSAO_FINITA`.
- **`ARQUETIPO_MOTOR` legado mantido vivo:** ambos os herdeiros (`PAGADORA_MADURA`, `CONCESSAO_FINITA`) mapeiam para `"ddm"`, espelhando o antigo regulada → `"ddm"`; `freio.motor_pendente` (`freio.py:18`, `.get(chave) != "ddm"`) segue idêntico. Deleção do legado é o Plano 06.
- **Onda 2 mantida verde:** todos os testes que asseveravam a string `pagadora_regulada` ao vivo foram migrados (REWRITE) ou deletados (DELETE) no MESMO diff que mudou o rótulo — zero referência viva sobra em `tests/`.

## Task Commits

1. **Task 1: ARQUETIPO_ANCORA_ROE + split das constantes (ARQUETIPO_MOTOR legado mantido)** — `4d9053e` (feat)
2. **Task 2: Migrar/deletar os testes da string de arquétipo morta + classificacao no mesmo diff** — `a4ed8a8` (test)

## Files Modified

- `src/analista/core/arquetipo.py` — Constantes `PAGADORA_MADURA`/`CONCESSAO_FINITA` (remoção de `PAGADORA_REGULADA`); registry novo `ARQUETIPO_ANCORA_ROE`; `ARQUETIPO_MOTOR` atualizado (herdeiros → `ddm`, comentário LEGADO/Plano 06); split no corpo de `classificar` (hard-route → `CONCESSAO_FINITA`, default → `PAGADORA_MADURA`); docstrings re-rotuladas.
- `tests/test_arquetipo.py` — REWRITE de `test_concessionaria_vira_pagadora_regulada` → `..._vira_concessao_finita` e `test_petroleo_concessionaria_nao_vira_pagadora_regulada` → `..._nao_vira_concessao_finita`; import de `PAGADORA_REGULADA` trocado por `CONCESSAO_FINITA` (mantido `ARQUETIPO_MOTOR`); docstring de módulo re-rotulada.
- `tests/test_arquetipo_roteamento.py` — REWRITE de `test_petroleo_nao_vira_pagadora_regulada` → `..._nao_vira_concessao_finita`; DELETE de `test_regulada_mantem_motor_ddm_e_veredito_ddm` (baseline da rota DDM).
- `tests/test_vulc3_regressao.py` — DELETE de `test_capstone_taee11_baseline_ddm_identico` (asseverava `arquetipo == "pagadora_regulada"`) + fixture órfã `_taee11_regulada`.
- `tests/classificacao.yaml` — 3 entradas renomeadas (REWRITE) + 2 removidas (DELETE), no mesmo diff — 0 órfão na coleta.

## Decisions Made

- **Valores de `ARQUETIPO_ANCORA_ROE` seguem o §Mapa de âncoras (ACTION), não a heurística grep da prose.** O `acceptance_criteria` da Task 1 pede `grep 'normalizado'/'nav' DENTRO do dict == 0`, mas a própria ACTION do plano manda `CICLICA → "normalizado"` e `HOLDING → "nav_piso"`. A heurística é uma sanidade imperfeita (proíbe os valores que ela mesma manda); o `<verify><automated>` da task NÃO a inclui e passa. Segui os valores canônicos de política.
- **Baseline da rota DDM DELETADO, não reescrito.** `test_regulada_mantem_motor_ddm_e_veredito_ddm` e `test_capstone_taee11_baseline_ddm_identico` asseveravam a premissa "regulada usa o motor DDM" — demolida no Plano 03 (regulada passa a rodar o RIM). Reescrevê-los p/ `concessao_finita` só adiaria a deleção uma onda. A invariância motor==ddm da regulada sob esta onda segue coberta por `test_regulada_ddm_nao_suspenso_eng06` (que NÃO cita a string morta).
- **Fixture `_taee11_regulada` removida junto.** Era consumida só pelo capstone deletado — deixá-la seria código morto.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reword de comentários/docstrings em `arquetipo.py` p/ o gate da Task 1**
- **Found during:** Task 1 (após a 1ª rodada de edições)
- **Issue:** Os comentários novos que explicam o split e o legado mencionavam o token `PAGADORA_REGULADA` em prosa, quebrando o `<verify>` da Task 1 (`grep -c 'PAGADORA_REGULADA' src/…/arquetipo.py -eq 0`).
- **Fix:** Reescritas as menções para "o antigo rótulo regulada" / "a string do rótulo antigo"; docstring de `classificar` re-rotulada p/ `CONCESSAO_FINITA`/`PAGADORA_MADURA`.
- **Files modified:** src/analista/core/arquetipo.py
- **Committed in:** `4d9053e` (Task 1)

**Total deviations:** 1 auto-fixed (1 blocking). Nenhuma mudança arquitetural; escopo do plano respeitado.

## Anti-Goals Respeitados

- **NÃO consertou o `g` das transmissoras** — `CONCESSAO_FINITA` é só rótulo/rota; a mecânica do carve-out (g_terminal) é o Plano 03.
- **NÃO mudou o CORPO do classificador** além das duas linhas de split — a árvore de decisão sobrevive intocada (ENG-03).
- **NÃO deletou `ARQUETIPO_MOTOR`** — o freio depende dele até o Plano 06.
- **NÃO atualizou golden de nível** — baselines de rota morta foram DELETADOS (função + linha da classificacao no mesmo diff), nenhum nível vivo alterado.

## Verification

- `.venv/bin/python -m pytest -q` (default, onda 2): **517 passed, 1 skipped, 20 deselected, 0 failed** (baseline 519 − 2 testes deletados). Coleta sem `CLASSIFICACAO ORFA`.
- `grep -rn 'pagadora_regulada\|PAGADORA_REGULADA' tests/ | sed 's/#.*//' | grep -c …` = **0** referência viva; 6 menções sobram só em comentário (comment-aware gate).
- `grep -c 'PAGADORA_REGULADA' src/analista/core/arquetipo.py` = **0**; `ARQUETIPO_ANCORA_ROE` e `ARQUETIPO_MOTOR` presentes; `.get(chave) != "ddm"` preservado.
- `pytest -m golden_nivel`: **20 passed, 0 ORFA**.
- Fronteira: `git diff config.yaml calibracao.lock.yaml` VAZIO — orçamento de 3 graus intacto (nenhum knob de valuation tocado).

## Known Stubs

None — `CONCESSAO_FINITA` é rótulo/rota real (o hard-route dispara); a política `through_cycle_sem_g` é consumida pelo RIM único no Plano 03, não um placeholder que flui p/ UI nesta onda.

## Threat Flags

Nenhuma superfície de segurança nova. Os threats do plano (`T-13-03` mis-route, `T-13-04` crash sob rótulo novo, `T-13-20` golden atualizado) foram mitigados: guarda anti-Petróleo preservada; `ARQUETIPO_MOTOR` com os rótulos novos (`.get` não vira KeyError); baseline de rota morta DELETADO, nenhum nível atualizado.

## Next Phase Readiness

- **Plano 03 (RIM único) pode consumir `ARQUETIPO_ANCORA_ROE`** — o mapa arquétipo→política existe e o carve-out `CONCESSAO_FINITA` está roteado; a mecânica do `g_terminal=None` (medida no 13-01) aterrissa lá, junto com o guard `payout_T` meio-aberto.
- **Plano 06** remove o `ARQUETIPO_MOTOR` legado com o último consumidor (`freio.motor_pendente`).
- Os capstones de `test_vulc3_regressao.py` que não tocam a string (só motor/campos) e os invariantes de cascata/normalização quebram só na onda 3 (Plano 03) — fora do escopo desta onda.

## Self-Check: PASSED

- Files exist: `arquetipo.py`, `test_arquetipo.py`, `test_arquetipo_roteamento.py`, `test_vulc3_regressao.py`, `classificacao.yaml`, `13-02-SUMMARY.md` — all FOUND.
- Commits exist: `4d9053e` (Task 1), `a4ed8a8` (Task 2) — all FOUND.
- Suíte re-rodada: default 517 passed, 1 skipped, 20 deselected, 0 failed; `-m golden_nivel` 20 passed, 0 ORFA; 0 referência viva à string morta.

