---
phase: 14-padr-es-gr-ficos-checklist-de-sinais
plan: 03
subsystem: api
tags: [indicators, padroes-graficos, oco, oco-invertido, neckline-inclinada, no-repaint]

# Dependency graph
requires:
  - phase: 14-padr-es-gr-ficos-checklist-de-sinais
    plan: 02
    provides: "_padroes (duplo topo/fundo) com máquina de estado em_formacao/confirmado (iloc[-2] + volume_acima_mm), measured-move e gate de no-repaint por truncação"
  - phase: 13-pivos-niveis-volume
    provides: "Pivos (pivot_high/low no-repaint via .dropna()); _pivos (fractal Williams N=2); _volume (volume_acima_mm bidirecional); helpers de teste _pivos_ts/_frame_ohlcv"
provides:
  - "_padroes estendida com oco/oco_invertido sobre 5 pivôs intercalados (3 topos + 2 fundos, ou espelho)"
  - "Neckline INCLINADA por regressão dos 2 pivôs intermediários usando POSIÇÃO inteira da barra (get_loc), nunca timestamp em ns (Pitfall 3)"
  - "Cabeça proeminente (head_min_prominence_pct) + ombros simétricos (shoulder_symmetry_pct); measured-move cabeça→neckline projetado do rompimento"
  - "GATE de no-repaint da OCO (truncação) verde + 6 goldens novos"
affects: [14-04-checklist, 14-05-calibracao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Neckline inclinada por POSIÇÃO inteira da barra (nominal.index.get_loc) como eixo-x — guard pos_f2==pos_f1; nunca timestamp em ns (T-14-06)"
    - "Extensão da MESMA função _padroes (não função paralela): OCO/invertido ANEXAM à mesma lista, reusando limiares do bloco padroes: e o idioma iloc[-2] + volume_acima_mm"
    - "5 pivôs âncora (ts:preco) em pivos_envolvidos p/ auditabilidade (espelha Niveis.pivos_ancora)"
    - "Razões (proeminência/simetria/altura) protegidas com np.errstate + np.isfinite; degradação graciosa → Padroes(lista=[]) sem levantar"

key-files:
  created: []
  modified:
    - src/analista/core/indicators.py
    - tests/test_indicators.py

key-decisions:
  - "Eixo-x da neckline = POSIÇÃO inteira da barra via nominal.index.get_loc(ts), não timestamp em ns (Pitfall 3 / T-14-06); guard pos_f2==pos_f1 contra reta degenerada"
  - "Cabeça = pivô do MEIO dos 3 mais recentes; deve exceder AMBOS os ombros por head_min_prominence_pct (prom_e/prom_d), ombros ~simétricos por shoulder_symmetry_pct"
  - "Fundos/topos intermediários escolhidos pelo extremo (min p/ fundos da OCO, max p/ topos do invertido) dentro de cada intervalo — neckline ancorada nas reações reais"
  - "altura = cabeca - neckline(sob a cabeça); filtro altura/cabeca >= min_pattern_height_pct; alvo measured-move = neckline_rompimento ∓ altura (baixo OCO / cima invertido)"

patterns-established:
  - "_frame_oco (24 barras) gera 5 pivôs reais via _pivos (N=2) p/ o gate de truncação; ks=(22,23,len) cobrem em_formacao→confirmado"
  - "Teste de neckline inclinada prova o eixo POSICIONAL: extrapolação ALÉM dos dois fundos (97 > f2=94), alvo finito — não colapsa em ~f1 como o eixo-ns"

requirements-completed: [PAT-01]

# Metrics
duration: ~12min
completed: 2026-06-29
---

# Phase 14 Plan 03: Detector OCO / OCO invertido (neckline inclinada) Summary

**`_padroes` agora cobre os 4 padrões de Murphy (duplo topo/fundo + OCO/OCO invertido): a OCO compõe 5 pivôs intercalados (cabeça proeminente, ombros simétricos config-driven) e calcula a neckline INCLINADA por regressão dos 2 fundos usando a POSIÇÃO inteira da barra como eixo-x (nunca timestamp em ns — Pitfall 3), com measured-move cabeça→neckline projetado do rompimento na barra fechada `iloc[-2]` + volume; provado no-repaint por truncação. 266 testes verdes (260 prévios + 6 novos, zero rebaseline).**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-06-29
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `_padroes` estendida (mesma função, mesma `lista`) com `tipo="oco"` e `tipo="oco_invertido"`.
- **OCO:** 3 topos mais recentes (LS / cabeça / RS) + 2 fundos intercalados; cabeça (do meio) excede ambos os ombros por `head_min_prominence_pct` (`prom_e`/`prom_d`); ombros ~simétricos por `shoulder_symmetry_pct`.
- **Neckline INCLINADA** pelos 2 fundos com eixo-x = POSIÇÃO inteira da barra (`nominal.index.get_loc`), `m = (f2-f1)/(pos_f2-pos_f1)` com guard de reta degenerada; extrapolada até a barra fechada (`pos_fechada = len-2`). `altura = cabeca - neckline(sob a cabeça)`; casa só se `altura/cabeca >= min_pattern_height_pct`.
- Estado: `confirmado` se `Close.iloc[-2] < neckline_rompimento` E (`volume_acima_mm` quando `exigir_volume_confirma`), senão `em_formacao`; `alvo = neckline_rompimento - altura` (p/ BAIXO).
- **OCO invertido (espelho):** cabeça = fundo mais BAIXO; neckline pelos 2 topos intermediários; rompe p/ CIMA; `alvo = neckline + altura`.
- 5 pivôs âncora (ts:preco) em `pivos_envolvidos`; degradação graciosa preservada (poucos pivôs / razões não-finitas → não anexa, nunca levanta).
- 6 goldens novos incluindo o GATE de no-repaint da OCO por truncação (geometria imutável; estado forward-only) e a prova explícita do eixo POSICIONAL (Pitfall 3 mitigado: alvo finito/plausível).

## Task Commits

1. **Task 1: `_padroes` — OCO/OCO invertido (neckline inclinada por posição)** - `64e4509` (feat)
2. **Task 2: goldens OCO/invertido + GATE no-repaint da OCO** - `01e5f5d` (test)

## Files Created/Modified
- `src/analista/core/indicators.py` - blocos OCO + OCO invertido anexados a `_padroes`; helper interno `_pos(ts)` (posição inteira); limiares `shoulder_symmetry_pct`/`head_min_prominence_pct` do bloco `padroes:`.
- `tests/test_indicators.py` - helper `_frame_oco` (24 barras, 5 pivôs reais via `_pivos`) + 6 goldens (geometria, confirmado, invertido, ombros assimétricos, neckline inclinada por posição, gate no-repaint).

## Decisions Made
- A neckline usa **posição inteira** (`get_loc`) e não timestamp em ns: o teste `test_padroes_oco_neckline_inclinada_usa_posicao` prova que a reta extrapola ALÉM dos dois fundos (neckline 97 > f2=94) e mantém alvo finito — o eixo-ns colapsaria a inclinação para ~0 (neckline ≈ f1), dando geometria errada.
- A cabeça e os ombros vêm dos **3 topos mais recentes** (`topos.iloc[-3:]`, já cronológicos por `.dropna()`); os fundos intermediários são selecionados pelo extremo (`min`) em cada intervalo entre ombros.
- O wiring final em `SinaisTecnicos.padroes`/`calcular` permanece para o plano 14-04 (checklist), evitando expor padrão parcial; o detector é chamável e golden-testado isoladamente (consistente com a decisão do 14-02).

## Deviations from Plan

None - plan executed exactly as written. OCO/OCO invertido anexados à mesma `_padroes`, neckline por `get_loc` (Pitfall 3), measured-move cabeça→neckline, confirmação `iloc[-2]` + volume, degradação graciosa preservada.

## Issues Encountered
- Ambiente: a suíte roda no `.venv` do projeto (`.venv/bin/python -m pytest`); o `python3` global não tem pandas. Sem impacto no código.

## TDD Gate Compliance
Plano `type: execute` (não-TDD). Task 1 (implementação) → Task 2 (goldens + gate) na ordem do plano; o GATE obrigatório de no-repaint da OCO está presente e verde.

## Next Phase Readiness
- `_padroes` cobre os 4 tipos (`duplo_topo`/`duplo_fundo`/`oco`/`oco_invertido`); pronto p/ o plano 14-04 (checklist) consumir `Padroes.lista` (`any(p.estado == "confirmado" ...)`) e cravar `padroes`/`checklist` em `calcular`.
- Invariante mantida: 266 testes verdes (260 prévios + 6 novos), nenhum golden rebaselinado; gate de no-repaint da OCO verde.

## Self-Check: PASSED

Arquivos e commits verificados (indicators.py, test_indicators.py; commits 64e4509, 01e5f5d). Suíte: 266 testes verdes; gate no-repaint da OCO verde; PAT-01 coberto (4 padrões).

---
*Phase: 14-padr-es-gr-ficos-checklist-de-sinais*
*Completed: 2026-06-29*
