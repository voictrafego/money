---
phase: 11-crescimento-g-grow
plan: 03
subsystem: blindagem-testes
tags: [split-before-delete, wr-04, golden-nivel, d-07, cobertura, nao-regressao, doenca-1-g]

# Dependency graph
requires:
  - phase: 11-crescimento-g-grow
    provides: "g_cap derivado + adocao de g_fundamentos (Plano 02, a461147)"
provides:
  - "metodo antigo do g REMOVIDO do repo: goldens de nivel do g antigo DELETADOS (nao atualizados), invariantes estruturais extraidos ANTES no MESMO diff (WR-04)"
  - "excesso_sustentavel e ke_g_spread_min load-bearing por COBERTURA (D-07/GROW-05): terminal nao explode + degrada honesto (fade-only) sob spread apertado"
  - "nao-regressao contra o MAPA REAL dos 104 (snapshot LIMPO): TAEE11/BBSE3/VULC3 finitos/sensatos; universo sem NaN/inf/excecao"
  - "golden_nivel 22 passed, 0 CLASSIFICACAO ORFA; suite default 499 passed, 0 failed, BLIND-02 xfail"
affects: [12-ke (BLIND-02 vira verde quando ke_teto sair; bandas de Ke residuais split-before-delete), 13-eng (rota seguradora revisitada), 14-val (soberano ITUB4 R$37,22)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "split-before-delete (WR-04): extrair o invariante estrutural ANTES de deletar a banda de nivel, no MESMO diff (funcao + linha classificacao.yaml juntas, zero orfao)"
    - "cobertura, nao recalibracao: knob decorativo vira load-bearing por um teste que exercita seu ramo (LIDO de config), sem mover o valor (GROW-05/D-07)"
    - "BLIND-04a-safe por SPLIT: funcao que nomeia ticker sem constante nao-trivial em assert + funcao com o limite de sanidade sem nomear ticker"
    - "regulada (DDM-motor) tem intrinseco_motor None por arquitetura -> valida-se pela banda vmin/vmax"

key-files:
  created:
    - tests/test_nao_regressao_grow.py
  modified:
    - tests/test_growth_reconciliacao.py
    - tests/test_motores.py
    - tests/test_vulc3_regressao.py
    - tests/test_invariantes_v24.py
    - tests/classificacao.yaml

key-decisions:
  - "goldens de nivel do g antigo DELETADOS, NUNCA atualizados (regra dura CLAUDE.md): test_g_fund_menor_que_cagr/test_teto_absoluto_025/test_trava_ke, rota seguradora (nivel 39,87, lia cfg[ddm][g_estavel] REMOVIDO), e VULC3 cascata (banda vmax<3x preco do g=2,5%)"
  - "invariantes estruturais SOBREVIVEM (extraidos ANTES, MESMO diff): adocao g_fundamentos, teto 0.25, trava Ke, rota seguradora finito>0, VULC3 (norm/g_fund<=0/Ke relacional/matriz/veredito/cross-menu)"
  - "EXTENSAO DE ESCOPO: VULC3 cascata (golden_nivel ja vermelho desde 11-02) nao estava na lista de arquivos do plano, mas e casualidade DIRETA do g_cap (Fase 11) e bloqueava a AC 'golden_nivel -> 0 failed'; curada por split-before-delete"
  - "D-07: excesso_sustentavel/ke_g_spread_min LIDOS de config (nao hardcoded) -> load-bearing por cobertura; git diff config.yaml/lock VAZIO (nenhum knob movido)"
  - "nao-regressao contra o MAPA REAL (hs.CAMINHO_SNAPSHOT_LIMPO), NAO fixtures sinteticas (essas exercitam patologia ja corrigida)"

patterns-established:
  - "para asserir sanidade de magnitude sem tripar o detector BLIND-04a: o limite (50x preco) mora na varredura do universo que nao nomeia ticker; a funcao dos 3 sensiveis so assere finitude/positividade (constantes triviais)"

metrics:
  duration: 35min
  tasks: 3
  completed: 2026-07-17
---

# Phase 11 Plan 03: Fechamento da Fase — split-before-delete do g antigo + cobertura D-07 + nao-regressao real Summary

**One-liner:** O metodo antigo do `g` some do repo por split-before-delete (goldens de nivel DELETADOS, invariantes estruturais extraidos ANTES no mesmo diff), `excesso_sustentavel`/`ke_g_spread_min` viram load-bearing por COBERTURA (terminal nao explode + degrada honesto sob o spread apertado do `g_cap`), e o mapa REAL dos 104 confirma que a cura do `g` nao regride TAEE11/BBSE3/VULC3 — suite verde, BLIND-02 ainda xfail.

## What Was Built

### Task 1 — split-before-delete dos goldens do `g` antigo (`dcfd1a2`)
- **`test_growth_reconciliacao.py`**: as 3 funcoes `golden_nivel` que codificavam a doutrina revogada ("subordinacao ao historico") foram DELETADAS e substituidas por 3 `invariante` estruturais — `test_g_alto_adota_g_fundamentos_nao_subordina_ao_historico` (GROW-04: `g_alto == g_fundamentos`), `test_g_alto_respeita_o_teto_absoluto_de_025`, `test_g_alto_trava_no_ke_quando_fundamentos_supera_ke`. Fixtures sinteticas re-montadas COM o novo `g_fundamentos` (mediana de ROE), asserts ESTRUTURAIS (`== g_fundamentos`, `== 0.25`, `== ke`), sem nivel. `test_payout_acima_de_100_zera_g_alto_sem_piso` (contrato) mantido.
- **`test_motores.py`**: o golden de nivel `test_rota_seguradora_bbse3_gordon_franquia` (assertia 39,87 e lia `cfg["ddm"]["g_estavel"]`, chave REMOVIDA na Fase 11) virou o contrato `test_rota_seguradora_roteia_e_da_intrinseco_finito_positivo` (`motor=="seguradora"`, finito>0, sem nivel).
- **`test_vulc3_regressao.py` (extensao de escopo)**: o golden de nivel `test_vulc3_cascata_domada_regressao` (JA vermelho em `-m golden_nivel` desde 11-02 — o `g_cap` explodiu a banda `vmax < 3× preco` do g=2,5% de ~2,3× para ~3,6×) virou o `invariante` `test_vulc3_cascata_estrutural_sobrevive`: bandas de nivel deletadas (`vmax<3× preco` [Fase 11] e `ke>=0,15` [Fase 12]), estrutura extraida (norm robusta, `g_fund≤0` sob payout>100%, Ke relacional `>0,094`, matriz `vmin/vmax==min/max`, veredito VERIFICAR, cross-menu ROE).
- Cada funcao deletada teve sua linha em `classificacao.yaml` removida no MESMO diff; cada invariante/contrato novo registrado. Zero orfao.

### Task 2 — cobertura D-07 (GROW-05) (`cebe32f`)
Dois `invariante` em `test_invariantes_v24.py` (registrados, NAO golden_nivel):
- `test_g_cap_derivado_e_adocao_de_g_alto_no_itub4`: `g_cap` DERIVADO — igualdade EXATA da recomposicao a partir de `pi_ciclo`/`pib_real` LIDOS de cfg (sem nivel/tolerancia); ITUB4 `g_alto == min(g_fundamentos, ke)` (adocao travada pelo Ke); intrinseco finito/positivo. Sem constante nao-trivial em assert (BLIND-04a-safe apesar de nomear ITUB4).
- `test_terminal_load_bearing_nao_explode_e_degrada_para_fade_only`: exercita o ramo `motores.py:128` sob o spread apertado (`ke_teto` 0,13 − `g_cap` 0,0728 ≈ 5,7pp). RELEASE: `vp_terminal > 0` (load-bearing) e `< valor_intrinseco` (nao explode). FADE: `g_terminal` tal que `ke − g < ke_g_spread_min` (LIDO de config) ⇒ `vp_terminal == 0` (fade-only), never-raise; `ddm.valor_gordon(ke−g≤0) is None`. `excesso_sustentavel`/`ke_g_spread_min` LIDOS de config — load-bearing por cobertura.

### Task 3 — nao-regressao contra o MAPA REAL de 104 tickers (`20bb97d`)
`tests/test_nao_regressao_grow.py` (novo, 2 contratos) carrega `hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO)` — o mapa REAL congelado dos 104, NAO fixtures sinteticas — com macro-inputs carimbados OFFLINE (`rf=selic_fallback`, `pi_ciclo` default):
- `test_tickers_sensiveis_nao_regridem_sob_o_g_novo`: TAEE11/BBSE3/VULC3 produzem valuation FINITA/POSITIVA. TAEE11 (regulada/DDM tem `intrinseco_motor` None por arquitetura) valida pela banda `vmin/vmax`. Assert so de finitude/positividade (sem nivel).
- `test_varredura_dos_104_sem_nan_inf_ou_excecao`: os 104 (menos as 11 falhas de mercado) nunca viram NaN/inf nem levantam; None aceitavel; limite de sanidade 50× preco SEM nomear ticker (BLIND-04a-safe). Reporta ofensores na mensagem.

## Deviations from Plan

### Extensao de escopo (auto-aplicada — Rule 3: desbloqueio da AC + regra dura do golden)

**1. [Extensao de escopo] VULC3 cascata split-before-delete (`test_vulc3_regressao.py`)**
- **Found during:** Task 1 (verificacao `-m golden_nivel`).
- **Issue:** `test_vulc3_cascata_domada_regressao` (golden_nivel) estava vermelho — confirmado por `git stash` como PRE-EXISTENTE desde 11-02 (`d26d5b7`), NAO causado pelas minhas mudancas. O `g_cap` (Fase 11) encolheu o spread `Ke−g` da perpetuidade e a banda `vmax < 3× preco` (calibrada ao g=2,5% REAL) subiu de ~2,3× para ~3,6× (medido: vmax 52,07 vs 3× preco 43,2). O 11-02 nao rodou `-m golden_nivel`, entao a casualidade nao foi vista la.
- **Por que curei (nao adiei):** bloqueava a AC deste plano (`golden_nivel -> 0 failed`, exigida em Task 1 E Task 3); e uma casualidade DIRETA da cura do `g` que ESTA fase possui (objetivo do plano: "o metodo antigo do g some sem manter reflexos vivos"); a resolucao e 100% prescrita pela disciplina (extrair invariante, deletar nivel — nunca atualizar). STATE ja listava "VULC3 cascata" como divida WR-04 das "Fases 11/12/13".
- **Fix:** split-before-delete — `test_vulc3_cascata_estrutural_sobrevive` (invariante) preserva toda a estrutura; DELETA so as 2 bandas de nivel (`vmax<3× preco` da Fase 11; `ke>=0,15` da Fase 12, mantendo o relacional `ke>0,094`). Funcao + linha classificacao no mesmo diff.
- **Files:** `tests/test_vulc3_regressao.py`, `tests/classificacao.yaml`. **Commit:** `dcfd1a2`.

**2. [Rule 1 - reconciliacao] Assert de TAEE11 adaptado a arquitetura da regulada**
- **Issue:** o plano pedia `intrinseco_motor` FINITO para TAEE11, mas a regulada usa o DDM como MOTOR-lente e seu `intrinseco_motor` e None POR ARQUITETURA (a valuation vive na banda `vmin/vmax`). None nao e regressao.
- **Fix:** helper `_valor_efetivo` (intrinseco_motor, senao o meio da banda DDM) — TAEE11 valida pela banda (37–75, mid 56, preco 40,92: finito/positivo/sensato). Captura o intento (Blocker 2: o `g` nao quebra TAEE11) sem falso-positivo.
- **Files:** `tests/test_nao_regressao_grow.py`. **Commit:** `20bb97d`.

**3. [Rule 3 - BLIND-04a] Contrato seguradora simplificado + import limpo (`test_motores.py`)**
- **Issue:** a versao inicial do contrato seguradora reusava `ddm.valor_gordon(...) < 1e-9` para auto-consistencia — `1e-9` (constante nao-trivial) + ticker "BBSE3" tripou o detector BLIND-04a (`test_nenhum_teste_de_calibracao_crava_ticker_em_reais`). O plano so exigia `motor=="seguradora"` + finito>0.
- **Fix:** removido o bloco de auto-consistencia (e o import `ddm` orfao). **Commit:** `dcfd1a2`.

Nenhum knob movido; nenhuma tolerancia afrouxada; nenhum xfail->skip; nenhum assert deletado para esconder mudanca de sistema.

## Verification (registrada — verificacao da fase)
- `pytest -q` (default) -> **499 passed, 1 skipped, 22 deselected, 1 xfailed, 0 failed**.
- `pytest -m golden_nivel -q` -> **22 passed, 0 failed, 0 CLASSIFICACAO ORFA**.
- `pytest -k invariancia_inflacao_engine_itub4 -rX` -> **1 xfailed** (BLIND-02, NUNCA XPASS — `xfail_strict` deixaria o default vermelho; a metade Ke da Doenca 1 e a Fase 12).
- `pytest -k "orcamento_de_knobs or knobs_batem_com_o_lock or justificativa_de_knob"` -> **3 passed** (3 graus de liberdade).
- `pytest -k crava_ticker` (BLIND-04a) -> **1 passed** (nenhum teste novo crava ticker em reais).
- `git diff config.yaml calibracao.lock.yaml` -> **VAZIO** (so cobertura de teste; nenhum knob movido).
- **Numeros da fase (medidos):** `g_cap = 0,0728` (de `pi_ciclo=0,0518`, `pib_real=0,02`); ITUB4 `g_fundamentos = 0,0959`, `g_alto = min(g_fund, ke) = 0,0959`; intrinsecos do mapa real — TAEE11 banda DDM 37,04–75,14 (mid 56,09, motor `ddm`, `intrinseco_motor` None por arquitetura), BBSE3 `intrinseco_motor` 85,85 (motor `seguradora`), VULC3 `intrinseco_motor` 11,55 (motor `normalizado`). Contagem final: 499 passed.

## Known Stubs
Nenhum. Este plano so ADICIONA cobertura de teste e remove reflexos do metodo antigo; nenhum codigo de producao tocado.

## Next Phase Readiness
- **Metade `g` da Doenca 1 CURADA e MEDIVEL:** o `g` da perpetuidade deixou de ser 2,5% real; o metodo antigo do `g` nao tem mais reflexo vivo no repo (goldens de nivel deletados, invariantes estruturais no lugar).
- **BLIND-02b permanece xfail de proposito** — a outra metade (`Ke` nominal + `ke_teto` muleta) e a **Fase 12**, quando o invariante de inflacao vira verde (o `ke_teto` sai). **NAO fundir 11 com 12** (regra dura A).
- **Divida WR-04 para a Fase 12:** as funcoes mistas de Ke (bandas de Ke, `SAN-01 reetiqueta`, `test_financeira_rim_destrava`) que a Fase 12 vai deletar — aplicar o mesmo split-before-delete.

## Self-Check: PASSED
- Files: `tests/test_nao_regressao_grow.py`, `11-03-SUMMARY.md` — all FOUND. Modified test files (`test_growth_reconciliacao.py`, `test_motores.py`, `test_vulc3_regressao.py`, `test_invariantes_v24.py`, `classificacao.yaml`) tracked in commits `dcfd1a2`/`cebe32f`/`20bb97d`.
- Commits: `dcfd1a2` (Task 1), `cebe32f` (Task 2), `20bb97d` (Task 3) — all FOUND in git log.
- Suite: default 499 passed, 0 failed; golden_nivel 22 passed, 0 orfao; BLIND-02 1 xfailed (not XPASS); `git diff config.yaml calibracao.lock.yaml` VAZIO.
