---
phase: 13-motores-contrato-de-sa-da-eng
plan: 03
subsystem: valuation
tags: [rim-unico, ensemble-morto, carve-out-concessao, seguradora-financeira, sweep-onda-3, split-before-delete]

requires:
  - phase: 13-motores-contrato-de-sa-da-eng
    plan: 01
    provides: "Carve-out CONCESSAO_FINITA g_terminal=None (fade-only); RIM único medido são; guard payout_T meio-aberto"
  - phase: 13-motores-contrato-de-sa-da-eng
    plan: 02
    provides: "Registry ARQUETIPO_ANCORA_ROE (arquétipo → política) + split PAGADORA_MADURA/CONCESSAO_FINITA"
provides:
  - "Caminho ÚNICO de valor: report._valor_rim/_derivar_insumo chamam SEMPRE motores.rim; a política do arquétipo só varia o insumo"
  - "Ensemble/guardas-cicatriz/divergência/fronteiriço REMOVIDOS de report.py (campos + funções + render)"
  - "Rota+chave seguradora e os motores dcf_crescimento/lucro_normalizado DELETADOS; nav_contabil sobrevive como derivador"
  - "Suíte default verde na onda 3 (475 passed, 0 failed); testes do método antigo delete/rewrite com classificacao no mesmo diff"
affects: [13-04, 13-05, 13-06, mapa-de-ancoras]

tech-stack:
  added: []
  patterns:
    - "Dispatch colapsado: política-string (ARQUETIPO_ANCORA_ROE) escolhe o INSUMO do RIM único, nunca um motor por nome"
    - "Split-before-delete de onda 3: invariantes (WR-04 seguradora, cascata VULC3) RESCRITOS; baselines de ensemble DELETADOS — mesmo diff"

key-files:
  created: []
  modified:
    - src/analista/core/motores.py
    - src/analista/report/report.py
    - tests/test_report.py
    - tests/test_vulc3_regressao.py
    - tests/test_arquetipo_roteamento.py
    - tests/test_motores.py
    - tests/test_backtest_bancos.py
    - tests/test_deflacao_ciclica.py
    - tests/test_cli_rank_consistencia.py
    - tests/test_guardrails_fix06.py
    - tests/fixtures/fair_values_bancos.yaml
    - tests/classificacao.yaml

key-decisions:
  - "Dispatch por POLÍTICA (não por nome de motor): _derivar_insumo ramifica em ARQUETIPO_ANCORA_ROE — a colisão da string 'normalizado'/'nav_piso' com ids antigos é falso-positivo do grep heurístico (segue precedente do 13-02)"
  - "Veto de risco (payout>100%) permanece só no ramo SUBAVALIADA; sob a banda estreita da MS a armadilha pode cair NO INTERVALO mas é SEMPRE surfaçada nos alertas — refinar no Plano 04"
  - "excecao_nota órfã da rota seguradora removida do fair_values (a rota morreu); app.py (UI do ensemble morto) diferido"

requirements-completed: [ENG-01, ENG-02]

duration: 95min
completed: 2026-07-19
---

# Phase 13 Plan 03: RIM único + morte do ensemble Summary

**Os 4 motores + rota seguradora + ensemble colapsaram num CAMINHO ÚNICO de valor — `report._valor_rim` deriva o insumo pela política do arquétipo e chama SEMPRE `motores.rim`; guardas-cicatriz, divergência e fronteiriço foram removidos, `dcf_crescimento`/`lucro_normalizado` deletados, e TODO teste do método antigo foi delete/rewrite no mesmo diff — suíte default verde (475 passed, 0 failed) na onda 3.**

## Performance

- **Duration:** ~95 min
- **Completed:** 2026-07-19
- **Tasks:** 3
- **Files modified:** 12 (2 produção, 10 testes/fixtures)

## Task Commits

1. **Task 1: Colapsar o dispatch num RIM único + remover a rota/chave seguradora** — `9612798` (refactor)
2. **Task 2: Remover ensemble, guardas-cicatriz e render de divergência** — `83e3825` (refactor)
3. **Task 3: Sweep exaustivo — delete/rewrite dos testes do método antigo (onda 3)** — `6e7e2be` (test)

## Accomplishments

- **Caminho ÚNICO de valor (ENG-01/ENG-02):** `_intrinseco_por_motor` (6 ramos: rim/normalizado/dcf/nav/ddm + rota seguradora) colapsou em `_valor_rim` → `_derivar_insumo(politica, ...)` → `motores.rim(...)`. A política de `ARQUETIPO_ANCORA_ROE[a.arquetipo]` (13-02) só escolhe o **insumo** (roe0-âncora, roe_terminal, g_terminal, base_book); a fórmula é sempre o RIM, com `a.ke` (Fase 12) e `g_T` (Fase 11) consumidos prontos.
- **Carve-out CONCESSAO_FINITA aplicado:** política `through_cycle_sem_g` → `g_terminal = None` (fade-only, decisão do spike 13-01); nenhuma reintrodução do g de inflação no terminal (double-count IPCA sob ICPC 01 evitado).
- **`dcf_crescimento` e `lucro_normalizado` DELETADOS** de `motores.py` (não substituídos por FCFE — Armadilha 2); `nav_contabil` sobrevive como derivador de piso patrimonial (política `nav_piso`); chave `"seguradora"` removida de `MOTOR_ROTULO` (só `"rim"` sobra).
- **Ensemble morto:** campos de ensemble de `AnaliseAcao` (banda_do_motor, contraponto_valor, divergencia_*, arquetipo_incerto/fronteirico, candidatos_intrinsecos, veredito_range, san01_reetiquetado, motor_pendente), as funções `_guarda_faixa_ddm`/`_guarda_san01`/`_hipotese_divergencia`/`_veredito_fronteirico` e o render de divergência/incerto — todos REMOVIDOS (não portados). `vmin/vmax` do veredito viraram a região SIMÉTRICA da MS sobre o intrínseco do RIM.
- **Invariante WR-04 da seguradora preservado (não morto em silêncio):** a seguradora capital-light é uma FINANCEIRA que roda o RIM único (`motor=="rim"`), com intrínseco FINITO e > 0 — o finite-positive SOBREVIVE como REWRITE, só a rota `a.motor=='seguradora'` saiu; o `test_setor_de_banco_nao_casa_o_token_seguradora` (token puro) ficou INTOCADO.
- **Sweep exaustivo da onda 3:** todo teste não-quarentenado que assevera campo/motor/função deletado foi DELETADO (baseline) ou RESCRITO (invariante), com a entrada em `classificacao.yaml` casada no MESMO diff (0 órfão).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `_veredito_fronteirico` co-removido na Task 1**
- **Found during:** Task 1
- **Issue:** `_veredito_fronteirico` consome o `_intrinseco_por_motor` (deletado na Task 1) e o `ARQUETIPO_MOTOR` (proibido em report.py pelo acceptance). Deixá-lo na Task 1 quebraria o import/runtime.
- **Fix:** removido junto com a chamada `if a.arquetipo_fronteirico:` na Task 1 (o resto do ensemble/guardas ficou para a Task 2).
- **Commit:** `9612798`

**2. [Rule 3 - Blocking] Stragglers de behavior-change fora do inventário do plano**
- **Found during:** Task 3 (rodada da suíte completa após Tasks 1-2)
- **Issue:** O inventário grep do plano (símbolos deletados) não pega testes que quebram por MUDANÇA DE COMPORTAMENTO (não por referência de símbolo): 6 focos fora dos 6 arquivos listados.
- **Fix:**
  - `test_deflacao_ciclica.py` (3) — chamavam `_intrinseco_por_motor("normalizado", ...)` (deletado); REWRITE para `_valor_rim(c, a, cfg)` com `a.arquetipo="ciclica"` (a deflação PRIM-04 sobrevive em `_roe0_ciclico`).
  - `test_cli_rank_consistencia.py` (1) — `motor=="normalizado"` → `=="rim"` (o invariante cross-menu de a.ke/intrínseco sobrevive).
  - `test_guardrails_fix06.py` — `test_banda_vem_da_matriz_de_sensibilidade` DELETADO (banda-de-matriz-DDM é método morto); `test_banda_degrada_quando_ddm_nao_roda` → REWRITE `..._quando_rim_nao_roda` (degradação never-raise sobrevive; veredito vira VERIFICAR).
  - `test_report.py::test_alerta_independe_do_veredito_d08` — REWRITE (drop `veredito==""`; o alerta técnico independe do veredito é o invariante).
  - `test_vulc3_regressao.py::test_capstone_vulc3_verifica_por_risco_real` — planejado KEEP, mas o veredito virou "NO INTERVALO" (banda estreita da MS); REWRITE `..._nao_vende_armadilha_como_barganha` (não-SUBAVALIADA + armadilha nos alertas).
  - `tests/fixtures/fair_values_bancos.yaml` — `excecao_nota` da seguradora ficou ÓRFÃ (BBSE3 agora roteia `rim`); removida (senão `test_nenhuma_nota_de_excecao_e_orfa` quebra).
- **Commit:** `6e7e2be`

**Total deviations:** 2 auto-fixed (ambos blocking). Nenhuma mudança arquitetural; config.yaml/calibracao.lock.yaml intocados.

## Notas de projeto (para o Plano 04)

- **Veto de risco só na SUBAVALIADA:** sob o RIM único a banda é a região SIMÉTRICA da MS (±15%) sobre o intrínseco — estreita. O veto de risco (payout>100% / DY>15%) continua vivo SÓ no ramo SUBAVALIADA (como o fallback antigo). Consequência: uma armadilha de payout>100% cujo preço caia DENTRO da banda estreita recebe "NO INTERVALO" no veredito de preço (a armadilha segue SEMPRE surfaçada na seção Alertas). O `VERIFICAR` do método antigo dependia da banda DDM larga (preço abaixo de vmin). O Plano 04, ao formalizar a "região da MS primária", deve decidir se o veto de risco se estende além da SUBAVALIADA.
- **Colisão do grep heurístico (acceptance #1):** `_derivar_insumo` ramifica em `politica == "normalizado"`/`"nav_piso"` (valores de `ARQUETIPO_ANCORA_ROE`), que aliam os ids de motor antigos e casam o grep `== .normalizado.`/`== .nav.`. É dispatch por POLÍTICA, não por nome de motor (a intenção do acceptance); o `<verify><automated>` da Task 1 NÃO inclui esse grep e passa. Segue o precedente registrado no 13-02.

## Known Stubs

None — nenhum valor placeholder flui para a UI; o RIM único produz intrínseco real ou None (never-raise).

## Deferred Items

- `app.py` (UI Streamlit) tem blocos MORTOS do ensemble/divergência/fronteiriço (referenciam campos removidos via `getattr(..., False)` / short-circuit; não renderizam, não crasham; nenhum teste importa `app.py`). Fora do escopo (Task 2 = report.py). Registrado em `deferred-items.md` — limpeza é do Plano 04 / UI.

## Verification

- `.venv/bin/python -m pytest -q` (default, onda 3): **475 passed, 1 skipped, 18 deselected, 0 failed, 0 xfailed** (baseline 517 − 42 testes de método antigo deletados; 2 golden_nivel a menos no deselected). `-m golden_nivel`: **18 passed, 0 CLASSIFICACAO ORFA**. `-m ""`: 492 passed, 2 skipped, 0 failed.
- **Inventário VIVO (comment-aware) de símbolos deletados == 0 em `tests/`** (grep da acceptance da Task 3).
- **Dispatch sem nome de motor / rota-chave seguradora:** `grep -c "'seguradora'|\"seguradora\"" report.py == 0`; `motores.rim` é o único chamado; `def dcf_crescimento`/`def lucro_normalizado` == 0; `def nav_contabil` == 1.
- **WR-04 seguradora RESCRITO** (finite>0 sobre FINANCEIRA→RIM); token-test INTOCADO; cascata VULC3 repontada à região da MS; deflação cíclica via `_valor_rim`.
- **Fronteira respeitada:** `git diff 1cc9b7d..HEAD -- config.yaml calibracao.lock.yaml` **VAZIO** — orçamento de 3 graus intacto (nenhum knob de valuation tocado; o knob-cut é o Plano 05).

## Self-Check: PASSED

- Files exist: `motores.py`, `report.py`, `13-03-SUMMARY.md`, `deferred-items.md` — all FOUND; `test_guardrails_ddm.py` DELETADO (confirmado).
- Commits exist: `9612798` (T1), `83e3825` (T2), `6e7e2be` (T3) — all FOUND.
- Suíte re-rodada: default 475 passed / 1 skipped / 0 failed; `-m golden_nivel` 18 passed / 0 ORFA; inventário vivo 0; config/lock diff VAZIO.

---
*Phase: 13-motores-contrato-de-sa-da-eng*
*Completed: 2026-07-19*
