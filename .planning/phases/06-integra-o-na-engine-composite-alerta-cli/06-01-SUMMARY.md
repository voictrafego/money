---
phase: 06-integra-o-na-engine-composite-alerta-cli
plan: 01
subsystem: api
tags: [pandas, indicators, composite, resample, timing, golden-test]

# Dependency graph
requires:
  - phase: 05-motor-de-indicadores-puro
    provides: "indicators.calcular(ohlc, cfg) -> SinaisTecnicos com rótulos discretos por família (posicao_mm200, forca_adx, etc.)"
  - phase: 04-encanamento-de-dados
    provides: "CompanyData.ohlc_ajustado (split-adjusted) como input dos indicadores (CR-01)"
provides:
  - "AnaliseAcao expõe sinais/timing_estado/timing_resumo/matriz_leitura/alerta_reverificacao (contrato aditivo)"
  - "analisar_acao popula a.sinais via indicators.calcular — ponto único compartilhado por CLI e UI (TIMING-01)"
  - "Árvore de decisão composite MM200-direção/ADX-força → 3 estados macro em PT (tendência de alta / sem tendência / atenção)"
  - "Base temporal canônica em cfg (base_temporal, default semanal) com resample W-FRI antes dos indicadores (TIMING-04)"
  - "Golden TEST-06 (desempate acima-da-MM200-com-ADX<20 → sem_tendencia) + golden do resample W-FRI"
affects: [Phase 06 Plan 02 (matriz fundamento×técnico + alerta de reverificação + paridade CLI), Phase 07 (UI overlays)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Composite lê rótulos discretos já classificados (não relê o float do ADX) — reusa indicators._forca"
    - "Degradação graciosa por ponto único: rota via indicators.calcular (frame vazio → indisponivel), sem segundo guard"
    - "Resample W-FRI (Open=first/High=max/Low=min/Close=last + dropna) como fronteira diário→semanal"

key-files:
  created:
    - tests/test_report.py
  modified:
    - src/analista/report/report.py
    - config.yaml

key-decisions:
  - "Os 5 campos do read técnico são aditivos no FINAL de AnaliseAcao (disciplina idêntica a Canais.donchian_sup_55); matriz_leitura/alerta_reverificacao já fixados no contrato mas preenchidos na Plan 02"
  - "RSI/MACD são matiz fino que refina a FRASE do timing_resumo, nunca mudam timing_estado (D-03)"
  - "TEST-06 cravado no timeframe diário (base_temporal=diario na cópia do cfg) para não exigir ~200 barras semanais; a árvore composite é idêntica nos dois timeframes — o resample tem golden dedicado separado"

patterns-established:
  - "Read técnico consultivo inserido após o bloco de alertas, imediatamente antes de return a — lê veredito/vmin/vmax já calculados (necessário p/ a Plan 02)"
  - "cfg como casa única dos parâmetros via .get com default (base_temporal); paridade CLI↔UI gratuita"

requirements-completed: [TIMING-01, TIMING-04, TEST-06]

# Metrics
duration: 4min
completed: 2026-06-27
---

# Phase 6 Plan 01: Integração na engine + composite Summary

**analisar_acao agora popula a.sinais (resample W-FRI quando semanal) e deriva um timing de entrada composite consultivo de três estados via árvore MM200-direção/ADX-força, com o desempate canônico (acima da MM200 + ADX<20 → sem tendência) travado por golden test.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-27T00:33:00Z
- **Completed:** 2026-06-27T00:37:00Z
- **Tasks:** 3
- **Files modified:** 3 (2 modified, 1 created)

## Accomplishments
- `AnaliseAcao` ganhou os 5 campos do read técnico consultivo (sinais + timing_estado/timing_resumo/matriz_leitura/alerta_reverificacao), aditivos e read-only sobre o fundamento.
- `analisar_acao` popula `a.sinais` via `indicators.calcular` (ponto único CLI/UI) e deriva o timing pela árvore composite: acima+ADX forte → tendência de alta; abaixo → atenção; acima mas ADX fraco/neutro ou indisponível → sem tendência.
- Base temporal `base_temporal` (default `"semanal"`) vive no `cfg`; resample W-FRI do `ohlc_ajustado` (split-adjusted, CR-01) roda antes dos indicadores.
- Dois golden tests novos: o desempate D-02/TEST-06 e a regra de agregação W-FRI.

## Task Commits

Each task was committed atomically:

1. **Task 1: Campos da AnaliseAcao + import indicators + chave base_temporal** - `11f7d35` (feat)
2. **Task 2: analisar_acao — resample semanal + popular sinais + árvore composite** - `84a68ec` (feat)
3. **Task 3: tests/test_report.py — golden TEST-06 + golden resample W-FRI** - `f72cb29` (test)

## Files Created/Modified
- `src/analista/report/report.py` - import de `indicators`; 5 campos novos em `AnaliseAcao`; bloco do read técnico (resample W-FRI + `indicators.calcular` + árvore de decisão + timing_resumo refinado por momentum) inserido antes de `return a`.
- `config.yaml` - chave canônica `base_temporal: "semanal"` no bloco `indicadores`.
- `tests/test_report.py` - novo arquivo de golden tests com `_cfg_ind()` (config shipado), `test_composite_acima_mm200_adx_fraco_eh_sem_tendencia` e `test_resample_semanal_w_fri`.

## Decisions Made
- TEST-06 fixado no timeframe diário (cópia do cfg com `base_temporal="diario"`) — a árvore composite é a mesma nos dois timeframes; o resample tem seu próprio golden dedicado, evitando precisar de ~200 barras semanais.
- timing_resumo usa as palavras-chave de estado ("tendência de alta" / "sem tendência" / "atenção") no texto PT, com RSI sobrecomprado e MACD cruz_baixa como matizes finos que não alteram o estado.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- O protótipo da fixture TEST-06 falhou inicialmente porque um `CompanyData` sem `anos` deixa `ultimo_ano()` em None e `c.roe(None)` levanta `TypeError` no bloco de múltiplos (anterior ao read técnico). Resolvido fornecendo `anos=[2023]` na fixture (sem fundamentos reais; o DDM degrada para veredito vazio, irrelevante para o assert de timing_estado). Não é desvio de plano — é detalhe de construção da fixture, antecipado pelo próprio plano ("os campos fundamentais podem ficar vazios").

## TDD Gate Compliance
Task 2 (`tdd="true"`) é a implementação; o golden correspondente foi entregue na Task 3 conforme a estrutura do plano (a verificação da Task 2 antecipa explicitamente que `test_report.py` é criado na Task 3). Sequência de gates no git log: `feat` (84a68ec, implementação) seguido de `test` (f72cb29, golden travando o comportamento). Suíte completa verde após cada commit.

## Next Phase Readiness
- Contrato do dataclass `AnaliseAcao` já fixado com `matriz_leitura` e `alerta_reverificacao` (vazios), prontos para a Plan 02 preencher a matriz fundamento×técnico e o alerta de reverificação consolidado + a seção CLI em `relatorio_markdown`.
- Suíte: 94 testes verdes (92 anteriores + 2 novos); invariante TEST-07 preservada (nenhuma fórmula de valuation tocada).

## Self-Check: PASSED

---
*Phase: 06-integra-o-na-engine-composite-alerta-cli*
*Completed: 2026-06-27*
