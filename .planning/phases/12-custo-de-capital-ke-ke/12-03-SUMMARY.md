---
phase: 12-custo-de-capital-ke-ke
plan: 03
subsystem: valuation-config-lock
tags: [ke, erp, capm, clamp-removido, knob, lock, orcamento-3-graus, blind-05, blind-06]

# Dependency graph
requires:
  - phase: 12-custo-de-capital-ke-ke
    plan: 02
    provides: "ke_rim DELETADO por codigo (clamp ke_piso/ke_teto removido) + Ke unico (a.ke) — as folhas viraram config MORTO, apagaveis sem quebrar a coleta; nenhum bracket-read vivo de ke_teto/ke_piso/erp_banco"
provides:
  - "capm.erp_local == 0.045 no config E no grau ERP do lock (commit sancionado config+lock, trailer sem ticker)"
  - "motores.rim.erp_banco/ke_piso/ke_teto NAO existem no config nem no lock — inclusive nenhuma mencao stale em comentario"
  - "escopo do lock 29 -> 26 folhas (motores 10 -> 7); orcamento intacto em 3 graus (ERP, n_fade, PIB_real); congelados 26 -> 23"
affects: [13-motores-contrato-eng, 14-validacao-honesta-val]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ERP unico (KE-02): um so' premio de risco de equity no sistema (capm.erp_local 4,5%); o 2o ERP dos bancos era sintoma, nao design"
    - "clamp removido do orcamento (KE-04 lado-config): o piso aritmetico do Blume substitui a trava; a partido do lock cai 3 folhas mantendo os 3 graus"

key-files:
  created: []
  modified:
    - config.yaml
    - calibracao.lock.yaml

key-decisions:
  - "ERP unificado em 4,5% (Damodaran mercado maduro puro); o premio small-cap/iliquidez de +1,5% do config antigo removido — a Selic ja' precifica risco-pais/inflacao"
  - "erp_banco/ke_piso/ke_teto deletados de config+lock no MESMO commit; nenhum clamp reintroduzido sob outro nome — a convergencia vem do piso do Blume (beta_blume >= 0,33 => Ke_min > g_cap)"
  - "commit sancionado config+lock (par permitido pelo hook BLIND-05, que bloqueia config+tests/*); trailer Knob-Change-Justification sem ticker; partido dinamica 26 == 3 graus | 23 congelados"

patterns-established:
  - "a remocao de knobs do orcamento e' CONTADA e visivel no diff do lock (29->26 folhas), com os comentarios de contagem coerentes em 3 lugares (escopo/congelados/particao)"

requirements-completed: [KE-02, KE-04]

# Metrics
duration: 15min
completed: 2026-07-17
---

# Phase 12 Plan 03: ERP unificado em 4,5% + clamp removido do orcamento Summary

**O commit de knob SANCIONADO do marco: `capm.erp_local` baixa 0,06 -> 0,045 (ERP de mercado maduro puro) e as tres folhas do clamp (`erp_banco`/`ke_piso`/`ke_teto`) somem de `config.yaml` E de `calibracao.lock.yaml` no MESMO commit — sem nenhuma mencao stale remanescente. O orcamento continua em 3 graus (ERP, n_fade, PIB_real): o escopo do lock cai de 29 para 26 folhas (motores 10 -> 7) e os congelados de 26 -> 23, com a particao dinamica verde. Suite intacta em 517 passed.**

## Performance

- **Duration:** ~15 min
- **Tasks:** 1 (`auto`)
- **Files modified:** 2 (0 criados)

## Accomplishments

- **ERP unificado em 4,5% (KE-02).** `capm.erp_local` 0.06 -> **0.045** em `config.yaml` e no grau `ERP` do `calibracao.lock.yaml` (`valor: 0.045`). O comentario do config perdeu a narrativa do "+1,5% de premio small-cap/iliquidez" (agora ERP = mercado maduro puro, Damodaran; a Selic ja' precifica risco-pais/inflacao). O bloco `fonte` do grau ERP no lock foi reescrito de acordo, e o comentario que descrevia os "DOIS ERPs simultaneos" foi atualizado para a unificacao — **sem citar a folha morta pelo nome** (grep dos tokens proibidos == 0).
- **Clamp removido do orcamento (KE-04 lado-config).** As tres folhas `motores.rim.erp_banco` / `motores.rim.ke_piso` / `motores.rim.ke_teto` foram DELETADAS de `config.yaml` (linhas + comentarios) e das entradas `congelados` do lock. O plano 12-02 ja' havia deletado o unico consumidor vivo (`motores.ke_rim`) e reescrito o bracket-read condenado, entao apagar as folhas **nao quebrou a coleta nem a suite**. **Nenhum clamp reintroduzido sob outro nome** — a perpetuidade converge pelo piso do Blume (`beta_blume >= 0,33 => Ke_min > g_cap` por aritmetica).
- **Mencao stale a `ke_piso` scrubada (Warning 4 do checker).** O comentario de `motores.rim.ke_g_spread_min` citava "Com g=0,025 e ke_piso=0,11 o spread real e' folgado" — a folha `ke_g_spread_min` e seu valor `0.03` ficaram **intactos**, so' o texto mudou para nao citar a folha que deixou de existir (agora "Com o Ke do CAPM local (piso do Blume) acima de g_cap...").
- **Orcamento CONTADO e coerente (BLIND-06).** Os tres comentarios de contagem do lock foram atualizados juntos: escopo `29 folhas (motores 10 ...)` -> `26 folhas (motores 7 ...)`; header dos congelados `26 folhas (29 - 3 graus)` -> `23 folhas (26 - 3 graus)`; a nota da particao `os 26 congelados ... das 29 folhas` -> `os 23 congelados ... das 26 folhas`. `test_orcamento_de_knobs_e_exatamente_3` (particao `folhas(escopo) == graus | congelados`) e `test_knobs_batem_com_o_lock` (valor a valor) ficam verdes porque config e lock mudaram juntos.
- **Commit sancionado limpo (BLIND-05).** Um unico commit com EXATAMENTE `config.yaml` + `calibracao.lock.yaml` (par permitido pelo hook, que bloqueia `config.yaml` + `tests/*`), com trailer `Knob-Change-Justification:` de razao ECONOMICA e **sem nenhuma mencao a ticker** — o hook e o teste `-k justificativa` passaram.

## Task Commits

1. **Task 1: ERP 0,06 -> 0,045 + remover erp_banco/ke_piso/ke_teto (config + lock, mesmo commit)** — `615843f` (feat)

## Files Modified

- `config.yaml` — `capm.erp_local` 0.06 -> 0.045 (comentario do small-cap removido); `motores.rim.erp_banco`/`ke_piso`/`ke_teto` DELETADOS (linhas + comentarios), comentario do bloco `rim:` reescrito para a unificacao; comentario de `ke_g_spread_min` scrubado da mencao a `ke_piso` (folha e valor intactos)
- `calibracao.lock.yaml` — grau `ERP` `valor` 0.06 -> 0.045 + `fonte`/comentario reescritos (nota "NAO escrever o alvo aqui hoje" removida); tres entradas `congelados` deletadas; comentarios de contagem 29->26 / 26->23 coerentes nos 3 lugares (escopo, header de congelados, nota da particao)

## Decisions Made

- **ERP unico, sem 2o premio de risco.** Dois ERPs no mesmo modelo (`capm.erp_local` 0,06 + o premio estrutural dos bancos 0,045) era sintoma — o segundo nasceu para baixar o Ke dos bancos, exatamente o papel que o clamp cumpria. Unificar em 4,5% (mercado maduro puro) e' o design honesto.
- **Sem clamp reintroduzido.** O plano proibiu explicitamente recriar a trava sob outro nome. Se algum V explodir sem clamp, o bug esta no `ROE_T`/spread (Fase 13), nao no Ke — `Ke_min` do Blume (11,07%) > `g_cap` (7,28%), entao nenhuma perpetuidade diverge por aritmetica.
- **Contagem do orcamento e' load-bearing.** Baixar 29 -> 26 folhas sem tocar os 3 graus e' a prova de que a remocao de knobs FOI contada (regra dura C do marco). Os comentarios de contagem em 3 lugares foram atualizados no mesmo diff para nao ficarem stale.

## Deviations from Plan

None - plano executado exatamente como escrito.

## Threat Flags

Nenhuma superficie nova. T-12-05 (Tampering config/lock) mitigado por construcao: o par config+lock e' auditavel no diff (BLIND-06), travado pela particao dinamica do orcamento e pelo trailer obrigatorio (BLIND-05). Mudanca de config offline; sem rede/auth/secrets/endpoint novo.

## Verification

- `grep -c "erp_local: 0.045" config.yaml` == **1**; `grep -c "erp_local: 0.06" config.yaml` == **0**.
- `grep -Ec "erp_banco|ke_piso|ke_teto" config.yaml` == **0**; idem `calibracao.lock.yaml` == **0** (folhas E mencoes em comentario).
- `grep -c "ke_g_spread_min" config.yaml` == **1** (folha permanece; so' o texto mudou).
- `grep -c "valor: 0.045" calibracao.lock.yaml` == **1** (grau ERP).
- `grep -Ec "29 folhas|29 -|das 29" calibracao.lock.yaml` == **0** (contagens stale atualizadas para 26/23).
- `pytest -k "orcamento or knobs_batem or justificativa"` -> **4 passed, 534 deselected** (particao 26 == 3 graus | 23 congelados; valores casam; justificativa sem ticker).
- `pytest` (suite default) -> **517 passed, 1 skipped, 20 deselected, 0 failed, 0 xfailed** (identico ao pos-12-02: BLIND-02b segue passando — a invariancia independe do NIVEL do ERP).
- `git show --stat HEAD` -> EXATAMENTE `config.yaml` + `calibracao.lock.yaml` (2 files, 31 insertions / 42 deletions); `git diff --diff-filter=D` do commit VAZIO (nenhum arquivo deletado — so' linhas dentro dos arquivos).
- Commit passou o hook `.githooks/commit-msg` (par sancionado config+lock, trailer sem ticker) — sem `--no-verify`.

## Next Phase Readiness

- **KE-02 e KE-04 completos.** O ERP e' unico (4,5%) e o clamp saiu do codigo (12-02) e do orcamento (12-03). A Fase 12 (Custo de capital / Ke) esta pronta para fechar apos o plano 04.
- **Fronteira respeitada:** g_cap da Fase 11 NAO recalibrado; orcamento em 3 graus intacto; nenhum motor tocado (o corte `motores:` ~11 -> <=5 e' a Fase 13).
- Nenhum blocker.

## Self-Check: PASSED

- Arquivos verificados no disco: `config.yaml`, `calibracao.lock.yaml`, `.planning/phases/12-custo-de-capital-ke-ke/12-03-SUMMARY.md`.
- Commit verificado no git log: `615843f`.
- Grep: erp_local 0.045 == 1, erp_local 0.06 == 0, tokens proibidos == 0 (config e lock), valor 0.045 == 1 (lock), "29" stale == 0.

---
*Phase: 12-custo-de-capital-ke-ke*
*Completed: 2026-07-17*
