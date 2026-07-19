---
phase: 13-motores-contrato-de-sa-da-eng
plan: 01
subsystem: testing
tags: [spike, rim, arquetipo, valuation, concessao-finita, carve-out, offline-regression]

# Dependency graph
requires:
  - phase: 12-custo-de-capital-ke
    provides: "a.ke único (β setorial+Blume), consumido pronto pelo RIM"
  - phase: 11-crescimento-g
    provides: "g_cap derivado na engine (7,28%), g_T fechado por empresa"
provides:
  - "Medição por coorte do RIM único sobre os 104 (financeira/madura/concessão/cíclica/crescimento)"
  - "Decisão do g_terminal do carve-out CONCESSAO_FINITA: None (fade-only)"
  - "De-risco do split D-05 (madura sai do DDM para o RIM: 0 ofensores)"
  - "Nota load-bearing p/ o guard payout_T do Plano 03 (meio-aberto (0,1] quando g_terminal is None)"
affects: [13-02, 13-03, mapa-de-ancoras, carve-out-concessao, guard-pb-payout]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Spike offline throwaway espelhando test_ke_validacao (snapshot LIMPO + β setorial carimbado)"
    - "Medição por distribuição de coorte (BLIND-04a-safe), nunca por caso/ticker"

key-files:
  created:
    - scripts/spike_eng_rim_104.py
    - .planning/spikes/eng-rim-104.md
  modified: []

key-decisions:
  - "Carve-out CONCESSAO_FINITA usa g_terminal = None (fade-only) — gatilho de subvalorização não disparou; payout_T=1,0 é identidade de terminal zerado (ICPC 01), não patologia"
  - "O RIM único é seguro para o colapso das Ondas 2-4: nada explode (max V/preço 2,82 « 50x) em nenhum coorte"
  - "Guard payout_T do Plano 03 deve ser meio-aberto (0,1] ou skip quando g_terminal is None"

patterns-established:
  - "Reconstrução offline de eh_concessionaria a partir do setor (mirror de build.py) para o coorte de concessão existir sem persistir o sinal no snapshot"

requirements-completed: [ENG-01, ENG-04]

# Metrics
duration: 40min
completed: 2026-07-19
---

# Phase 13 Plan 01: Spike de medição do RIM único sobre os 104 Summary

**O RIM único não explode em nenhum coorte (max V/preço 2,82 « 50x) e o carve-out CONCESSAO_FINITA fica decidido por medição em `g_terminal = None` (fade-only), com o split madura→RIM de-riscado a 0 ofensores.**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-07-19
- **Tasks:** 2
- **Files created:** 2 (ambos fora de produção)

## Accomplishments
- Script offline throwaway que roda o RIM único proposto sobre os 104 do snapshot limpo, por coorte, com o Ke da Fase 12 e o g_cap da Fase 11 consumidos prontos.
- Medido que **regulada (madura + concessão) e cíclica ficam sãs** sob o RIM único: V/preço não explode, P/B justo ∈ (0,6) na mediana, payout_T ∈ (0,1) no corpo — a preocupação MEDIUM do research resolvida a favor do colapso.
- **Decisão do carve-out CONCESSAO_FINITA fixada por execução:** `g_terminal = None`, com as duas variantes (None × PIB_real) medidas lado a lado sobre o mesmo coorte.
- Identificada e registrada a **nota load-bearing** para o guard `payout_T` do Plano 03 (o terminal zerado crava payout_T=1,0, a fronteira do intervalo aberto — o guard deve ser meio-aberto ou skip).

## Task Commits

1. **Task 1: Script de medição offline do RIM único sobre os 104** — `ad58045` (feat)
2. **Task 2: Registrar a medição + decidir o g_terminal do carve-out** — `bb32a3c` (docs)

## Files Created/Modified
- `scripts/spike_eng_rim_104.py` — Spike offline: carrega os 104 (snapshot LIMPO, β setorial carimbado), classifica arquétipo, deriva o roe0-âncora pela política do arquétipo, chama `motores.rim` com `ke=a.ke`, roda 2 variantes de `g_terminal` para a concessão, agrega por coorte (V/preço, P/B justo, payout_T, ofensores). Never-raise por ticker; saída agregada sem nomear ticker.
- `.planning/spikes/eng-rim-104.md` — Doc de spike: medição por coorte, sanidade de regulada/cíclica sob o RIM único, decisão do carve-out (None) com evidência de coorte, nota do guard payout_T, fronteira com a Fase 14.

## Decisions Made
- **`g_terminal = None` para CONCESSAO_FINITA.** Ambas as variantes ficam sãs; o gatilho do research para preferir PIB_real ("subvaloriza demais") não disparou (V/preço mediana 0,77 vs 0,85). O único diferenciador — payout_T=1,0 na variante None — é a identidade definicional de um terminal zerado (ICPC 01: book já capitaliza a receita regulatória; `g_cap` embute inflação → double-count), não uma patologia. É a mecânica mais limpa (`motores.rim` já a suporta nativamente).
- **Guard payout_T meio-aberto para o carve-out.** Registrado para o Plano 03 (ENG-08/09): sob `g_terminal=None` a checagem `payout_T ∈ (0,1)` aberta marcaria toda concessão por artefato de fronteira.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reconstrução offline de `eh_concessionaria`**
- **Found during:** Task 1 (após a 1ª execução do script)
- **Issue:** O coorte CONCESSAO_FINITA saiu VAZIO na primeira rodada — o loader offline (`helpers_sanidade.carregar_snapshot_sanidade`) não persiste `eh_concessionaria` (é derivado do setor no `build.py:168`, não gravado no snapshot). Sem esse sinal, o hard-route de concessão do classificador nunca dispara e as concessões se dispersam nos outros coortes — o que impossibilitaria medir o carve-out, o objetivo central do spike.
- **Fix:** Adicionado `_eh_concessionaria(setor)` no script, mirror EXATO dos tokens de `build.py:139` (`Energia`/`Saneamento`/`Água`/`Gás`), setado em `c.eh_concessionaria` após o load. Isso reconstrói o sinal derivado offline sem tocar produção nem o snapshot.
- **Files modified:** scripts/spike_eng_rim_104.py
- **Verification:** Após o fix, coorte `concessao` com n=15; classificação idêntica ao pipeline (mesmos tokens). Produção intocada (`git diff src/` vazio).
- **Committed in:** `ad58045` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** O fix era necessário para o spike medir o coorte de concessão (seu propósito). Mirror exato do pipeline, zero produção tocada, sem scope creep.

## Issues Encountered
- Duas interrupções por erro transitório de conexão de API ao emitir o Write inicial do script (payload grande). Resolvido escrevendo o arquivo em um esqueleto curto + Edits pequenos incrementais. Nenhum progresso durável perdido.

## Known Stubs
None — o spike é throwaway e produz medição real; nenhum valor placeholder flui para produção.

## User Setup Required
None — nenhuma configuração de serviço externo. O spike é 100% offline.

## Next Phase Readiness
- **Plano 02/03 podem declarar o mapa de âncoras e o carve-out ANTES do hold-out (Fase 14):** o RIM único está medido como seguro (nada explode); o split D-05 (madura→RIM) está de-riscado; a escolha `g_terminal=None` está fundamentada por coorte.
- **Fronteira com a Fase 14 respeitada:** nenhum caso do livro validado; nenhum knob movido (`git diff config.yaml calibracao.lock.yaml` vazio); suíte inalterada (519 passed, 1 skipped).
- **Nota pendente para o Plano 03:** implementar o guard `payout_T` como meio-aberto `(0,1]` (ou skip quando `g_terminal is None`) para não flagar a concessão por artefato de fronteira.

## Self-Check: PASSED

- Files exist: `scripts/spike_eng_rim_104.py`, `.planning/spikes/eng-rim-104.md`, `13-01-SUMMARY.md` — all FOUND.
- Commits exist: `ad58045` (Task 1), `bb32a3c` (Task 2) — all FOUND.
- Verification re-run: `.venv/bin/python scripts/spike_eng_rim_104.py` exit 0; `git diff --stat src/ config.yaml calibracao.lock.yaml` VAZIO; suíte default 519 passed, 1 skipped (baseline inalterado).

---
*Phase: 13-motores-contrato-de-sa-da-eng*
*Completed: 2026-07-19*
