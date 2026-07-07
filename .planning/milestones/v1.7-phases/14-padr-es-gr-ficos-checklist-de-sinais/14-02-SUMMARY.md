---
phase: 14-padr-es-gr-ficos-checklist-de-sinais
plan: 02
subsystem: api
tags: [indicators, padroes-graficos, duplo-topo, duplo-fundo, measured-move, no-repaint]

# Dependency graph
requires:
  - phase: 14-padr-es-gr-ficos-checklist-de-sinais
    plan: 01
    provides: "Dataclasses PadraoGrafico/Padroes; flag bidirecional Volume.volume_acima_mm; bloco padroes: (limiares A1–A7) no config.yaml"
  - phase: 13-pivos-niveis-volume
    provides: "Pivos (pivot_high/low no-repaint via .dropna()); idioma iloc[-2] barra fechada; helpers de teste _pivos_ts/_frame_ohlcv"
provides:
  - "_padroes(pivos, nominal, volume, cfg) detectando duplo_topo/duplo_fundo sobre pivôs confirmados"
  - "Máquina de estado em_formacao/confirmado (rompimento da neckline na barra fechada iloc[-2] + volume config-driven)"
  - "Alvo measured-move (altura da neckline projetada: p/ baixo no duplo topo, p/ cima no duplo fundo)"
  - "GATE de no-repaint do duplo (truncação) verde + 5 goldens novos"
affects: [14-03-detector-oco, 14-04-checklist, 14-05-calibracao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Composição geométrica sobre pivôs no-repaint (consome .dropna(), nunca recalcula pivô)"
    - "Confirmação SEMPRE na barra fechada iloc[-2] (no-repaint) + flag volume_acima_mm bidirecional"
    - "Razões (simetria/altura) protegidas com np.errstate + np.isfinite (neckline ~0 não explode)"
    - "Goldens injetando pivôs determinísticos via _pivos_ts (geometria isolada) + gate de truncação"

key-files:
  created: []
  modified:
    - src/analista/core/indicators.py
    - tests/test_indicators.py

key-decisions:
  - "_padroes consome Pivos.pivot_high/low via .dropna() (pivôs confirmados da Fase 13) — não recalcula"
  - "Neckline do duplo é HORIZONTAL: vale.min() (duplo topo) / pico.max() (duplo fundo) entre os 2 extremos"
  - "Goldens unitários injetam Volume(volume_acima_mm=...) (contrato consumido) — integração real do _volume coberta pelo gate de no-repaint (pipeline completo) e pelos goldens de volume da Fase 14-01"
  - "Gate no-repaint: geometria (neckline/alvo/altura) imutável ao truncar; estado só avança em_formacao→confirmado (forward-only, nunca repinta)"

patterns-established:
  - "Detector de padrão como função pura RETORNANDO Padroes(lista) — espelha _niveis_sr/_volume; degradação graciosa → Padroes(lista=[])"
  - "Fixture sintética _frame_duplo_topo (33 barras) + gate de truncação por k mirroring test_pivos_no_repaint_truncacao"

requirements-completed: [PAT-01]

# Metrics
duration: ~10min
completed: 2026-06-29
---

# Phase 14 Plan 02: Detector de duplo topo / duplo fundo Summary

**`_padroes(pivos, nominal, volume, cfg)` detecta duplo topo e duplo fundo sobre pivôs no-repaint da Fase 13, com neckline horizontal, máquina de estado em_formacao/confirmado (rompimento na barra fechada `iloc[-2]` + volume bidirecional, config-driven) e alvo measured-move — provado no-repaint por truncação; 260 testes verdes (255 prévios + 5 novos, zero rebaseline).**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-06-29
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `_padroes` em `indicators.py`: detecção determinística de duplo_topo e duplo_fundo sobre `Pivos.pivot_high/pivot_low` confirmados (`.dropna()`), no frame nominal (família de PREÇO, D-02).
- Neckline horizontal: `vale.min()` entre os dois topos (duplo topo) / `pico.max()` entre os dois fundos (duplo fundo). Simetria de preço e altura mínima validadas contra `price_tolerance_pct`/`min_pattern_height_pct` (config-driven, anti-pareidolia).
- Máquina de estado: geometria casando → `em_formacao`; rompimento da neckline lido na barra FECHADA (`Close.iloc[-2]`) + `volume.volume_acima_mm` (exigido quando `exigir_volume_confirma`) → `confirmado`.
- Alvo measured-move: `neckline - altura` (p/ baixo no duplo topo), `neckline + altura` (p/ cima no duplo fundo).
- Degradação graciosa (`pivos=None`/frame curto/sem Close → `Padroes(lista=[])`, nunca levanta) e guards `np.errstate` + `np.isfinite` nas razões (T-14-03/04/05 mitigados).
- 5 goldens novos incluindo o GATE de no-repaint por truncação: geometria imutável ao truncar, estado só avança em_formacao→confirmado (forward-only).

## Task Commits

1. **Task 1: `_padroes` — detecção de duplo topo/fundo** - `f29246a` (feat)
2. **Task 2: goldens duplo topo/fundo + GATE no-repaint** - `d3ce6b7` (test)

## Files Created/Modified
- `src/analista/core/indicators.py` - função `_padroes` (perto de `_niveis_stop_rr`/`_volume`); consome pivôs confirmados, retorna `Padroes(lista=[...])`
- `tests/test_indicators.py` - helpers `_padrao`/`_frame_duplo_topo` + 5 goldens (geometria, confirmado, duplo fundo, simetria frouxa, gate no-repaint)

## Decisions Made
- `_padroes` NÃO foi cravado em `calcular(...)` neste plano: o wiring final em `SinaisTecnicos.padroes` é da montagem do checklist (plano 14-04), evitando expor padrão parcial antes da OCO (14-03). O contrato `Padroes` já existe (14-01); o detector é chamável e golden-testado isoladamente.
- Goldens unitários injetam `Volume(volume_acima_mm=...)` (o campo que `_padroes` consome) para isolar a geometria; a integração real com `_volume` é exercida no gate de no-repaint (pipeline `_pivos`+`_volume`+`_padroes` completo).

## Deviations from Plan

None - plan executed exactly as written. O detector ficou em `indicators.py` (OQ1), neckline horizontal via min/max do vale/pico, measured-move cheio (A5), confirmação `iloc[-2]` + volume (A7).

## Issues Encountered
- Ambiente: a suíte roda no `.venv` do projeto (`.venv/bin/python -m pytest`); o `python3` global não tem pandas. Sem impacto no código.

## TDD Gate Compliance
Plano `type: execute` (não-TDD). Task 1 (implementação) → Task 2 (goldens + gate) na ordem do plano; o GATE obrigatório de no-repaint do duplo está presente e verde.

## Next Phase Readiness
- `_padroes` pronto para o plano 14-03 ESTENDER com OCO/OCO invertido (neckline inclinada, 5 pivôs) reusando a mesma função e os mesmos limiares do bloco `padroes:`.
- O plano 14-04 (checklist) pode consumir `Padroes.lista` (`any(p.estado == "confirmado" ...)`) e cravar `padroes`/`checklist` em `calcular`.
- Invariante mantida: 260 testes verdes (255 prévios + 5 novos), nenhum golden rebaselinado.

## Self-Check: PASSED

Arquivos e commits verificados (indicators.py, test_indicators.py; commits f29246a, d3ce6b7). Suíte: 260 testes verdes; gate no-repaint do duplo verde.

---
*Phase: 14-padr-es-gr-ficos-checklist-de-sinais*
*Completed: 2026-06-29*
