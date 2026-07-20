---
phase: 13-motores-contrato-de-sa-da-eng
plan: 04
subsystem: valuation
tags: [contrato-de-saida, ponte-pb, razao-implicita, guard-never-raise, regiao-da-ms, identidade-fechada]

requires:
  - phase: 13-motores-contrato-de-sa-da-eng
    plan: 03
    provides: "RIM único (_valor_rim/_derivar_insumo); região simétrica da MS já como vmin/vmax do veredito"
  - phase: 13-motores-contrato-de-sa-da-eng
    plan: 01
    provides: "Carve-out g_terminal=None (fade-only); nota load-bearing do guard payout_T meio-aberto"
provides:
  - "core/valuation.py: identidade fechada P/B (pb_justo/payout_terminal), fonte única do BLIND-02a"
  - "Ponte P/B auditável exposta em AnaliseAcao (pb_justo/v_ponte/payout_terminal); reusa _derivar_insumo"
  - "Guard runtime never-raise (D-10b): razão patológica degrada o veredito p/ VERIFICAR, não levanta"
  - "Contrato de saída coberto por testes de FORMATO/BORDA (triade por posição, região simétrica, never-raise)"
affects: [13-05, 13-06, mapa-de-ancoras]

tech-stack:
  added: []
  patterns:
    - "Ponte = decomposição steady-state (lente auditável), NÃO um segundo motor: reusa _derivar_insumo p/ não divergir do RIM"
    - "Guard de razão pega patologia de MODELO (P/B∉(0,6) / payout_T∉(0,1]); ortogonal ao bug de DADO (CGRA4 921×, VPA inflado)"
    - "payout_T meio-aberto (0,1]: terminal zerado crava 1,0 por IDENTIDADE (spike 13-01), não patologia"

key-files:
  created:
    - src/analista/core/valuation.py
    - tests/test_eng_ponte_pb.py
    - tests/test_eng_contrato.py
  modified:
    - src/analista/report/report.py
    - tests/test_invariantes_v24.py
    - tests/classificacao.yaml

key-decisions:
  - "A região da MS já era primária desde o 13-03 (vmin/vmax = intrínseco×(1∓ms)); este plano RELIGOU a ponte e o guard, não reescreveu a banda"
  - "Guard payout_T meio-aberto (0,1] (não (0,1) do must_have literal): honra a nota load-bearing do spike 13-01 — terminal zerado (carve-out/g_T=0) crava payout_T=1,0 por identidade, não é patologia"
  - "Veto de risco (payout>100%) permanece SÓ na SUBAVALIADA (questão aberta do 13-03 resolvida por NÃO-extensão): o guard novo é ortogonal (patologia de MODELO), a armadilha segue sempre nos alertas; anti-goal proíbe inventar contrato novo"

requirements-completed: [ENG-05, ENG-06, ENG-07, ENG-08, ENG-09]

duration: 30min
completed: 2026-07-19
---

# Phase 13 Plan 04: Contrato de saída sobre o RIM único Summary

**O contrato do livro (Cap. 17) foi religado ao RIM único: a identidade fechada P/B saiu para `core/valuation.py` (fonte única do BLIND-02a), a ponte auditável `pb_justo/v_ponte/payout_terminal` passou a ser computada e exposta em `AnaliseAcao` reusando o MESMO `_derivar_insumo` do motor, e um guard runtime never-raise degrada o veredito para VERIFICAR quando a razão implícita é patológica (P/B∉(0,6) ou payout_T∉(0,1]) — patologia de MODELO, ortogonal ao bug de DADO. A região simétrica da MS já era primária desde o 13-03; a tríade, a simetria e o never-raise agora têm testes de FORMATO/BORDA verdes, sem calibrar a MS e sem tocar o caso do livro (Fase 14).**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-07-19
- **Tasks:** 3
- **Files:** 6 (3 criados: 1 produção + 2 testes; 3 modificados: 1 produção + 2 testes/config)

## Task Commits

1. **Task 1: Extrair a identidade P/B para core/valuation.py + teste de correção da razão** — `f872a43` (test)
2. **Task 2: Religar a ponte P/B + guard runtime never-raise sobre o RIM único** — `824a6d8` (feat)
3. **Task 3: Testes de contrato (tríade/região/never-raise) + classificacao** — `5f013aa` (test)

## Accomplishments

- **Identidade P/B pura (ENG-08):** `core/valuation.py` nasce com `pb_justo(roe,ke,g) = 1+(roe−ke)/(ke−g)` e `payout_terminal(roe_t,g) = 1−g/roe_t`, ambas com None-guard de borda (`ke−g>0`, `roe_t≠0`) — never-raise (SAN-06/T-13-08). O BLIND-02a (`test_invariantes_v24`) passou a IMPORTAR de `core.valuation` em vez da cópia local: fonte única, sem divergência, o assert exato < 1e-9 INTACTO.
- **Ponte auditável exposta (ENG-08):** `report.analisar_acao` computa a ponte reusando o MESMO `_derivar_insumo(politica, …)` que o `_valor_rim` usa — ROE_T=`_roe_through_cycle`, Ke=`a.ke`, g=g_T (o g_terminal efetivo; None no carve-out ⇒ g_ponte=0). Expõe `pb_justo`/`v_ponte`/`payout_terminal` em `AnaliseAcao` (para a UI do Plano 06). Não é um segundo motor: é a decomposição steady-state (lente), não substitui `intrinseco_motor`.
- **Guard runtime em dois níveis (ENG-09/D-10b):** teste FALHA se a razão for patológica (test_eng_ponte_pb, RED-able); runtime DEGRADA never-raise — quando `pb_justo∉(0,6)` ou `payout_T∉(0,1]` o veredito vira VERIFICAR (com alerta detalhado), `analisar_acao` NUNCA levanta. O guard pega patologia de MODELO (spread/razão), NÃO o bug de DADO do CGRA4 (VPA inflado a 921×, P/B implícito ~1,4 são — ortogonal, sinalizado por SAN-01).
- **Região da MS primária confirmada (ENG-05/06):** a banda `vmin/vmax = intrínseco×(1∓ms)` já era o caminho único desde o 13-03 (o ensemble morreu lá); nenhum `min/max` de contraponto sobrevive no código (só menções em comentário). A MS é consumida de `cfg["veredito"]["margem_seguranca"]`, nunca recalibrada. A matriz Ke×g (ENG-07) segue montada sobre `a.ke` (herança da Fase 12).
- **Contrato coberto (ENG-05/06/09):** `test_eng_contrato.py` (contrato, fixtures sintéticas) prova a tríade por POSIÇÃO (preço vs `[V(1−MS),V(1+MS)]` → SUB/NO INTERVALO/SOBRE), a simetria da região que escala com a MS (dobrar a MS dobra a meia-largura dos dois lados), e o never-raise sob razão patológica — tudo FORMATO/BORDA, sem nível, sem ticker.

## Deviations from Plan

### Interpretação load-bearing (não é auto-fix de bug)

**1. Guard `payout_T` meio-aberto (0,1] em vez do (0,1) literal do must_have**
- **Onde:** Task 2 (guard runtime) e Task 1 (`_razao_sa` do teste)
- **Motivo:** o must_have escreve "teste FALHA se `payout_T ∉ (0,1)`", mas a nota LOAD-BEARING do spike 13-01 (registrada como decisão do 13-01 e no `<interfaces>` do próprio plano) exige meio-aberto: sob `g_terminal=None` (carve-out) ou g_T=0, o payout_T crava em 1,0 por IDENTIDADE definicional (terminal zerado, ICPC 01), não patologia. Um intervalo aberto marcaria TODA concessão por artefato de fronteira.
- **Resolução:** guard usa `not (0.0 < payout_T <= 1.0)` — reprova payout_T≤0 ou >1 (patologia real), aceita 1,0 (identidade). Consistente entre runtime e teste.

**Total:** 1 interpretação de spec (spike-driven), 0 bugs. Nenhuma mudança arquitetural. `config.yaml`/`calibracao.lock.yaml` INTOCADOS.

## Notas de projeto

- **Questão aberta do 13-03 (veto de risco além da SUBAVALIADA) — resolvida por NÃO-extensão.** O 13-03 pediu ao Plano 04 para decidir se o veto de risco (payout>100%) se estende além do ramo SUBAVALIADA. Decisão: **não estender.** O anti-goal do plano proíbe inventar contrato novo; a armadilha segue SEMPRE surfaçada nos alertas (independe do veredito). O guard novo (`razao_patologica`) é ORTOGONAL: pega patologia de MODELO (razão implícita), não a armadilha de risco de DADO — não é o mesmo eixo do veto.
- **Colisão heurística inexistente aqui:** o campo `a.pb_justo` (instância) e a função `valuation.pb_justo` (módulo) coexistem sem colisão (acesso qualificado); os verifies do plano (`grep pb_justo|payout_terminal`) passam.

## Known Stubs

None — a ponte produz razão real ou None (never-raise); nenhum placeholder flui para a UI. Os campos `pb_justo/v_ponte/payout_terminal` recebem valores reais do `_derivar_insumo`, não mock.

## Deferred Items

- **`app.py` (UI Streamlit)** segue com blocos mortos do ensemble (herança do 13-03, registrado em `deferred-items.md`). Fora do escopo do 13-04 (files_modified não inclui `app.py`); a exposição da ponte na UI é o **Plano 06**. Os campos novos de `AnaliseAcao` estão prontos para consumo.

## Verification

- `.venv/bin/python -m pytest -q` (default): **485 passed, 1 skipped, 18 deselected, 0 failed** (baseline 475 + 7 invariante da ponte + 3 contrato). `-m golden_nivel`: **18 passed, 0 CLASSIFICACAO ORFA**.
- `-k 'ponte_pb or invariantes_v24'`: 12 passed (identidade < 1e-9 do BLIND-02a intacta, importando de `core.valuation`). `-k eng_contrato`: 3 passed.
- **Guard provado, não decorativo:** `test_guarda_pega_payout_terminal_negativo` e `test_guarda_pega_pb_justo_explosivo` reprovam a razão-guarda sob insumos patológicos de MODELO (RED-able por construção).
- **Fronteira respeitada:** `git diff --stat config.yaml calibracao.lock.yaml` **VAZIO** — orçamento de 3 graus intacto (nenhum knob de valuation tocado; a MS não foi calibrada). Nenhum assert nomeia ticker+número-alvo (`grep -iE 'ITUB4|37[.,]22' tests/test_eng_contrato.py` == 0). Caso do livro NÃO validado (Fase 14).

## Self-Check: PASSED

- Files exist: `core/valuation.py`, `test_eng_ponte_pb.py`, `test_eng_contrato.py`, `13-04-SUMMARY.md` — all FOUND.
- Commits exist: `f872a43` (T1), `824a6d8` (T2), `5f013aa` (T3) — all FOUND.
- Suíte re-rodada: default 485 passed / 1 skipped / 18 deselected / 0 failed; `-m golden_nivel` 18 passed / 0 ORFA; config/lock diff VAZIO.

---
*Phase: 13-motores-contrato-de-sa-da-eng*
*Completed: 2026-07-19*

