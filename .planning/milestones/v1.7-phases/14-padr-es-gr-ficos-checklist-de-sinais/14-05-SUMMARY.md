---
phase: 14-padr-es-gr-ficos-checklist-de-sinais
plan: 05
subsystem: testing
tags: [calibracao, padroes-graficos, multi-ticker, anti-pareidolia, config-driven, b3]

# Dependency graph
requires:
  - phase: 14-padr-es-gr-ficos-checklist-de-sinais
    plan: 04
    provides: "calcular() popula SinaisTecnicos.padroes/.checklist ponta-a-ponta (read-only) — alvo da varredura"
  - phase: 14-padr-es-gr-ficos-checklist-de-sinais
    plan: 02
    provides: "_padroes (duplo topo/fundo) + contrato Padroes/PadraoGrafico"
  - phase: 14-padr-es-gr-ficos-checklist-de-sinais
    plan: 03
    provides: "_padroes estendida com OCO/OCO invertido (neckline inclinada por posição)"
provides:
  - "Limiares geométricos do bloco `padroes:` VALIDADOS multi-ticker (A1–A7 confirmados, anti-pareidolia)"
  - "Evidência empírica (6 tickers B3 reais) de que os detectores não geram enxurrada de falso positivo"
affects: [15-score, 16-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Calibração por varredura efêmera no scratchpad (script throwaway, NÃO commitado): mede plausibilidade sem poluir o repo (CLAUDE.md: não criar arquivos extras)"
    - "Aceite por checkpoint humano: limiares ASSUMED só viram 'confirmados' após validação multi-ticker contra dados reais"

key-files:
  created: []
  modified: []

key-decisions:
  - "Limiares `padroes:` (A1–A7) APROVADOS SEM AJUSTE — sobreviveram à validação multi-ticker (6 tickers B3, 5a de barras diárias): 3 padrões no total, 1 único 'confirmado', 4/6 tickers com zero. Oposto de pareidolia."
  - "config.yaml NÃO foi tocado (anti-rebaseline Pitfall 5): nenhum golden afetado, sem necessidade de re-rodar pytest."

patterns-established:
  - "Varredura de calibração multi-ticker como gate de aceite de limiares geométricos config-driven"

requirements-completed: [PAT-01]

# Metrics
duration: ~6min
completed: 2026-06-29
---

# Phase 14 Plan 05: Calibração multi-ticker dos limiares de padrões Summary

**Os limiares geométricos do bloco `padroes:` (A1–A7, ASSUMED LOW-MEDIUM) foram VALIDADOS contra dados reais de 6 tickers B3 variados (~5 anos de barras diárias cada) e APROVADOS SEM AJUSTE: a varredura achou 3 padrões no total (1 único "confirmado"), com 4/6 tickers em zero — o oposto de pareidolia (Pitfall 1/11). Geometria 100% coerente (necklines entre os pivôs, alvos measured-move na direção correta). config.yaml intocado; nenhum golden afetado.**

## Performance
- **Duration:** ~6 min
- **Completed:** 2026-06-29
- **Tasks:** 2 (1 auto + 1 checkpoint humano aprovado)
- **Files modified:** 0 (código/config intocados; só SUMMARY + state/roadmap)

## Accomplishments
- Varredura de calibração sobre **6 tickers B3 reais** (PETR4, ITUB4, VALE3, WEGE3, BBAS3, MGLU3) via `prices.coletar_mercado(ticker).ohlc` → `indicators.calcular(ohlc, cfg, ohlc_nominal=ohlc)`, todos coletados com sucesso (sem falha de rede). Script efêmero no scratchpad, NÃO commitado.
- **Tabela de contagem por ticker** (avaliação de enxurrada vs. alta confiança):

  | Ticker | Pivôs confirmados | Total padrões | em_formacao | confirmado |
  | ------ | ----------------- | ------------- | ----------- | ---------- |
  | PETR4  | 331 | 0 | 0 | 0 |
  | ITUB4  | 321 | 1 | 1 | 0 |
  | VALE3  | 333 | 2 | 1 | 1 |
  | WEGE3  | 326 | 0 | 0 | 0 |
  | BBAS3  | 319 | 0 | 0 | 0 |
  | MGLU3  | 290 | 0 | 0 | 0 |

- **Padrões detectados (geometria auditada):**
  - ITUB4 — `duplo_topo:em_formacao` — topos 40.82/41.63 (simetria ~2% < 3%), neckline=38.43, alvo=35.64 (measured-move p/ baixo).
  - VALE3 — `duplo_topo:confirmado` — topos 82.74/81.58 (simetria ~1.4%), neckline=78.88, alvo=75.60. Rompimento+volume → "confirmado" (checklist `padrao` ativo).
  - VALE3 — `duplo_fundo:em_formacao` — fundos 78.88/77.16 (simetria ~2.2%), neckline=81.58, alvo=85.14 (measured-move p/ cima).
- **Checkpoint humano aprovado** (Task 2): plausibilidade multi-ticker confirmada, limiares mantidos sem ajuste (A1–A7 confirmados).

## Task Commits
1. **Task 1: Varredura multi-ticker (6 tickers B3 reais)** - sem commit (script efêmero no scratchpad; nenhuma mudança em git)
2. **Task 2: Checkpoint humano — limiares aprovados sem ajuste** - sem commit (config.yaml intocado)

**Plan metadata:** este commit (docs: complete plan — SUMMARY + STATE + ROADMAP)

## Files Created/Modified
- Nenhum arquivo de código/config modificado. O plano é de calibração/validação: confirmou que os limiares `padroes:` (config.yaml linhas 125–137) já estavam adequados.
- Script de varredura: efêmero no scratchpad da sessão (`scan_padroes.py`), NÃO commitado por design (CLAUDE.md: scripts throwaway não entram no git).

## Decisions Made
- **Limiares aprovados sem ajuste.** Em 6 gráficos com ~300 pivôs confirmados cada, o detector achou apenas 3 padrões no total e 1 único "confirmado" (exige rompimento + volume). 4/6 tickers retornaram zero. Isto satisfaz Success Criterion 3 (validação multi-ticker) e o Pitfall 1/11 (anti-pareidolia): poucos padrões de alta confiança, sem enxurrada.
- **config.yaml intocado** → nenhum golden que pina o config foi afetado → re-rodar `pytest` não é necessário (a suíte estava verde com estes mesmos valores no plano 14-04, 271 testes).
- **OQ4 (max_largura_barras) deferida no RESEARCH não foi necessária:** os limiares atuais (`lookback_pivos`/`price_tolerance_pct`/`min_pattern_height_pct`) já contêm a contagem sem precisar de uma trava adicional de largura. Mantida em aberto para o v2 se a sensibilidade precisar subir.

## Deviations from Plan
None - plan executed exactly as written. Task 1 mediu (script efêmero), Task 2 (checkpoint humano) aprovou os limiares sem ajuste; nenhum config tocado, nenhum re-baseline.

## Issues Encountered
None. Todos os 6 tickers coletaram OHLC real sem falha de rede (degradação graciosa não precisou ser exercida nesta rodada).

## Observação neutra (carregada para o v2, sem ação)
4/6 tickers deram zero padrões. Como o critério de aceite da fase é explicitamente anti-falso-positivo, o comportamento conservador o satisfaz. Se em uso real a sensibilidade parecer baixa demais, candidatos a afrouxamento cauteloso (v2): `lookback_pivos` 8→10 ou `price_tolerance_pct` 0.03→0.04, sempre re-rodando varredura + `pytest -q`.

## Next Phase Readiness
- Limiares `padroes:` confirmados multi-ticker → a Fase 15 (score) pode consumir `SinaisTecnicos.checklist`/`.padroes` com confiança de que "confirmado" é raro e plausível (não inflado por ruído).
- PAT-01 fechado e validado empiricamente (já estava marcado Complete no 14-04; este plano cumpre o aceite de calibração da fase).
- Invariante dos goldens mantida (config intocado; suíte permanece nos 271 testes verdes do 14-04).

## Self-Check: PASSED

Varredura rodou sobre 6 tickers B3 reais sem exceção; tabela de contagem produzida e revisada; checkpoint humano aprovou os limiares sem ajuste; config.yaml não foi tocado (nenhum golden afetado); SUMMARY criado. PAT-01 validado.

---
*Phase: 14-padr-es-gr-ficos-checklist-de-sinais*
*Completed: 2026-06-29*
