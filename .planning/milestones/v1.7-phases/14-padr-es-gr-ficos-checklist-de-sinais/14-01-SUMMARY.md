---
phase: 14-padr-es-gr-ficos-checklist-de-sinais
plan: 01
subsystem: api
tags: [indicators, padroes-graficos, checklist, dataclass, config-yaml, no-repaint]

# Dependency graph
requires:
  - phase: 13-pivos-niveis-volume
    provides: "Pivos (pivot_high/low no-repaint), Volume (rompimento_com_volume, volume_mm na barra fechada iloc[-2]), idioma aditivo de SinaisTecnicos"
provides:
  - "Bloco `padroes:` no config.yaml com os 6 limiares geométricos A1–A7 (config-driven, pinado nos goldens)"
  - "Dataclasses PadraoGrafico / Padroes / Sinal / Checklist (chaves estáveis/neutras D-01)"
  - "Campos aditivos `padroes`/`checklist` em SinaisTecnicos (default None)"
  - "Flag bidirecional Volume.volume_acima_mm (barra fechada > MM, agnóstica de direção)"
affects: [14-02-detector-duplo-topo-fundo, 14-03-detector-oco, 14-04-checklist, 14-05-calibracao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Contrato interface-first 100% aditivo (campos novos com default; nenhum existente reordenado/removido)"
    - "Limiares geométricos config-driven em bloco novo, irmão de `indicadores:` (anti-rebaseline Pitfall 5)"
    - "Flag de confirmação direção-agnóstica reusando vmm_f/vol_f já computados (sem segunda MM)"

key-files:
  created: []
  modified:
    - config.yaml
    - src/analista/core/indicators.py
    - tests/test_indicators.py

key-decisions:
  - "OQ1: detectores ficam DENTRO de core/indicators.py (consistência com a Fase 13 / single-assembly em calcular) — NÃO criar core/padroes.py"
  - "OQ2: volume_acima_mm aditivo em Volume, avaliado na barra fechada iloc[-2], AGNÓSTICO de direção; o detector decide a direção pela neckline"
  - "OQ3: Padroes.lista é uma LISTA (ranqueamento deferido p/ Fase 15)"
  - "OQ4: max_largura_barras deferido p/ a calibração multi-ticker (plano 14-05)"

patterns-established:
  - "Aditividade de contrato: PadraoGrafico/Padroes/Sinal/Checklist + 2 campos em SinaisTecnicos + 1 em Volume, todos com default — 252 goldens intactos"
  - "Limiares A1–A7 em config.yaml `padroes:` com comentário do porquê (PT-BR), bloco indicadores: intocado"

requirements-completed: [PAT-01, SIG-01]

# Metrics
duration: ~8min
completed: 2026-06-29
---

# Phase 14 Plan 01: Contrato aditivo de padrões gráficos + checklist Summary

**Contrato interface-first da Fase 14: bloco `padroes:` (A1–A7) no config, dataclasses PadraoGrafico/Padroes/Sinal/Checklist, campos aditivos `padroes`/`checklist` em SinaisTecnicos e a flag de volume bidirecional `volume_acima_mm` — 252 goldens intactos (255 com os 3 novos).**

## Performance

- **Duration:** ~8 min
- **Completed:** 2026-06-29
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Bloco `padroes:` no config.yaml com os 6 limiares geométricos (lookback_pivos, price_tolerance_pct, shoulder_symmetry_pct, head_min_prominence_pct, min_pattern_height_pct, exigir_volume_confirma), cada um comentado em PT-BR — bloco `indicadores:` intocado.
- 4 dataclasses novos em indicators.py (PadraoGrafico, Padroes, Sinal, Checklist) com chaves estáveis/neutras (firewall de copy D-01), espelhando o idioma de Niveis/ContextoTendencia.
- SinaisTecnicos ganha `padroes`/`checklist` (default None) ao final; Volume ganha `volume_acima_mm` (default False) — todos aditivos.
- `_volume` popula `volume_acima_mm` na barra fechada (iloc[-2]), agnóstico de direção, reusando vmm_f/vol_f (sem segunda MM), mantendo `rompimento_com_volume` (só-alta) idêntico aos goldens.

## Task Commits

1. **Task 1: Bloco `padroes:` + dataclasses do contrato** - `89f466f` (feat)
2. **Task 2 (RED): golden da flag bidirecional** - `85c38ba` (test)
3. **Task 2 (GREEN): volume_acima_mm em _volume** - `8a4e398` (feat)

## Files Created/Modified
- `config.yaml` - bloco novo `padroes:` (6 limiares A1–A7, comentados); `indicadores:` intocado
- `src/analista/core/indicators.py` - dataclasses PadraoGrafico/Padroes/Sinal/Checklist; campo Volume.volume_acima_mm; campos SinaisTecnicos.padroes/checklist; flag direção-agnóstica em `_volume`
- `tests/test_indicators.py` - 3 goldens novos da flag bidirecional (rompimento de baixa, volume baixo, degradação)

## Decisions Made
- As 4 Open Questions do RESEARCH foram resolvidas conforme o `<objective>` do plano (OQ1 indicators.py, OQ2 volume_acima_mm aditivo, OQ3 lista, OQ4 deferida ao 14-05).
- Detector de padrões e measured-move ficam para os planos 14-02/03; este plano entrega só os contratos e a fonte de limiares.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Ambiente: o `python3` global do sistema não tem pandas; a suíte roda no `.venv` do projeto (`.venv/bin/python -m pytest`). Sem impacto no código.

## TDD Gate Compliance
Task 2 seguiu RED (`85c38ba`, test) → GREEN (`8a4e398`, feat). Sem refactor necessário.

## Next Phase Readiness
- Contratos e limiares prontos: os planos 14-02 (duplo topo/fundo) e 14-03 (OCO) podem implementar `_padroes` consumindo `Pivos` + `Volume.volume_acima_mm`; o plano 14-04 implementa `_checklist`.
- Invariante mantida: 255 testes verdes (252 prévios + 3 novos), nenhum golden rebaselinado.

## Self-Check: PASSED

Todos os arquivos e commits verificados (config.yaml, indicators.py, test_indicators.py, 14-01-SUMMARY.md; commits 89f466f, 85c38ba, 8a4e398). Suíte 255 testes verdes.

---
*Phase: 14-padr-es-gr-ficos-checklist-de-sinais*
*Completed: 2026-06-29*
