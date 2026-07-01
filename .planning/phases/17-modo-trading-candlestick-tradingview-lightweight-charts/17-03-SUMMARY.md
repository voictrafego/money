---
phase: 17-modo-trading-candlestick-tradingview-lightweight-charts
plan: 03
subsystem: testing
tags: [verification, golden-tests, lightweight-charts, tradingview, streamlit, browser-smoke, claude-in-chrome, swing-trade]

# Dependency graph
requires:
  - phase: 17-modo-trading-candlestick-tradingview-lightweight-charts
    plan: 01
    provides: "_render_lwc (candlestick LWC v5, CDN pinado + SRI) + toggle de vista + persistência de range; .phase-base-sha"
  - phase: 17-modo-trading-candlestick-tradingview-lightweight-charts
    plan: 02
    provides: "overlays da engine no Modo Trading (BandPrimitive, createPriceLine, createSeriesMarkers + neckline)"
provides:
  - "Gate de aceite consolidado da Phase 17: 283 goldens verdes + grafico.py intacto (diff vs .phase-base-sha vazio) + app.py thin renderer (_render_lwc read-only) + smoke humano no navegador aprovado"
  - "Evidência de mitigação de T-17-05: chart LWC v5 renderiza no navegador (SRI não bloqueou; console sem erro de integridade)"
affects: [v1.4-close]

# Tech tracking
tech-stack:
  added: []  # verificação — zero código de produto novo
  patterns:
    - "Gate de invariância por SHA base fixo da fase (.phase-base-sha), nunca HEAD~N (contagem de commits imprevisível → falso PASS)"
    - "Prova estática de thin-renderer: awk isola o corpo de _render_lwc + grep proíbe indicators.calcular/montar_setup (recálculo de método na UI)"
    - "Smoke visual via Claude-in-Chrome contra app Streamlit ao vivo + read_console_messages para provar console limpo"

key-files:
  created:
    - ".planning/phases/17-modo-trading-candlestick-tradingview-lightweight-charts/17-03-SUMMARY.md"
  modified: []

key-decisions:
  - "Aceite da fase é duplo: automatizado (goldens + invariantes estáticos) + humano (smoke no navegador do Modo Trading sem regressão); ambos exigidos para fechar"
  - "Scroll-zoom não foi exercitado por máquina (wheel sobre o iframe do componente rola a página-pai, não o chart); pan + crosshair confirmados na mesma instância LWC ao vivo — scroll-zoom é default padrão do LWC v5 (handleScroll/handleScale ligados); humano aprovou com a ressalva"

patterns-established:
  - "Verificação de fase de UI-render sem produto novo: automatizado (pytest + diff de invariância + grep de thin-renderer) na Task 1, humano (browser smoke + console limpo) na Task 2"

requirements-completed: [LWC-01, LWC-02, LWC-03]

# Metrics
duration: ~6min
completed: 2026-07-01
---

# Phase 17 Plan 03: Verificação de Aceite do Modo Trading (goldens + smoke no navegador) Summary

**Gate de aceite consolidado da Phase 17: 283 goldens verdes, `grafico.py` intacto (diff vs `.phase-base-sha` vazio) e `app.py` comprovadamente thin renderer (`_render_lwc` read-only), somados ao smoke humano via Claude-in-Chrome que aprovou o Modo Trading (candlestick LWC v5 + overlays da engine + crosshair) sem regressão em Plotly, Analisar, Ranking e Garimpo.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-07-01 (aprox.)
- **Completed:** 2026-07-01
- **Tasks:** 2 (1 automatizada + 1 checkpoint humano aprovado)
- **Files modified:** 0 de produto (só criado 17-03-SUMMARY.md)

## Accomplishments

- **Task 1 — verificação automatizada (executor anterior):** `.venv/bin/python -m pytest -q` → 283 passed (zero falhas/regressão); `git diff --name-only "$BASE"..HEAD -- src/analista/grafico.py` (BASE = `.phase-base-sha`) VAZIO → `grafico.py` intacto; o corpo de `_render_lwc` isolado por `awk` não contém `indicators.calcular(` nem `setup.montar_setup(` → `app.py` comprovadamente thin renderer no caminho LWC.
- **Task 2 — smoke humano no navegador (via Claude-in-Chrome, APROVADO):** o orquestrador rodou o app ao vivo (`http://localhost:8501`), navegou o Modo Trading do 4º menu com BBSE3/Diário e o humano aprovou os resultados (evidência detalhada abaixo).
- Fase 17 pronta para fechar: LWC-01 (candlestick TV-like), LWC-02 (overlays da engine) e LWC-03 (persistência de range) verificados ponta-a-ponta, invariantes da v1.4 preservados.

## Browser Smoke Evidence (Task 2 — aprovado pelo humano)

Smoke via Claude-in-Chrome contra o app ao vivo (`http://localhost:8501`):

- **Vista default = Plotly** no carregamento; Modo Trading é opt-in. ✓
- **Modo Trading renderiza candlestick Lightweight Charts v5 ao vivo** — a watermark "TradingView" visível confirma que o bundle do CDN `@5.2.0` + SRI carregou com sucesso → **T-17-05 mitigado** (o SRI não bloqueou; hash bateu).
- **Dataset canônico BBSE3/Diário:** linhas de preço rotuladas com os valores exatos esperados — alvo (estudo) **41,74**; Fib 382 **39,12** / Fib 500 **38,81** / Fib 618 **38,50**; stop (estudo) **37,50**; linha de último preço **32,97**.
- **Overlays presentes:** banda de zona de entrada + bandas de S/R + linhas de Fibonacci renderizadas; histograma de volume, Y-autoscale e linha tracejada de último preço presentes.
- **Crosshair com rótulos de preço nos eixos confirmado** (arrastar produziu crosshair + leitura no eixo Y de 43,82).
- **Copy de estudo íntegra:** rótulos "(estudo)" nas linhas + disclaimer na sidebar presentes (neutralidade SWING-02 mantida).
- **Console limpo:** logs "[lwc] overlays de nível OK", **ZERO** erros/exceções durante toda a sessão.
- **Regressão negativa:** voltar para Plotly restaurou a vista completa de indicadores (SMA20/50/200, ADX, RSI, MACD, Sinal, Histograma) com overlays intactos; abas Analisar, Ranking (Cap. 11-12) e Garimpar (BSD, Cap. 8) renderizam sem exceção.
- **Limitação conhecida (não é defeito):** o scroll-zoom por roda do mouse sobre o iframe do componente Streamlit rola a página-pai em vez do chart, então o scroll-zoom não foi exercitado por máquina. Pan + crosshair foram confirmados na MESMA instância LWC ao vivo; scroll-zoom é default padrão do LWC v5 (`handleScroll`/`handleScale` ligados). O humano aprovou com essa ressalva registrada.

## Task Commits

Cada task foi tratada atomicamente:

1. **Task 1: Verificação automatizada (goldens + invariantes)** — read-only, sem commit de código (283 passed; grafico.py intacto; _render_lwc thin renderer) — executada pelo agente anterior.
2. **Task 2: Smoke no navegador do Modo Trading (checkpoint human-verify)** — aprovado pelo humano; evidência registrada neste SUMMARY.

**Plan metadata:** commit `docs(17-03)` deste SUMMARY + STATE.md + ROADMAP.md.

## Files Created/Modified

- `.planning/phases/17-modo-trading-candlestick-tradingview-lightweight-charts/17-03-SUMMARY.md` — registro do gate de aceite (automatizado + humano) e da evidência de smoke no navegador.

Nenhum arquivo de produto tocado (plano de verificação).

## Decisions Made

- **Aceite duplo exigido:** a fase só fecha com AMBOS — automatizado (283 goldens + `grafico.py` intacto por diff contra `.phase-base-sha` + `_render_lwc` read-only por grep) e humano (smoke no navegador do Modo Trading sem regressão). Ambos satisfeitos.
- **Scroll-zoom aceito por default do LWC:** o wheel automatizado sobre o iframe do componente rola a página-pai (limitação do sandbox Streamlit-component), não o chart; pan e crosshair foram confirmados na instância LWC ao vivo, e scroll-zoom é comportamento default do LWC v5 (`handleScroll`/`handleScale` habilitados por padrão). Registrado como limitação conhecida, não defeito; humano aprovou.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Scroll-zoom não exercitável por máquina:** roda do mouse sobre o iframe do componente rola a página-pai em vez de dar zoom no chart. Resolução: verificação da mesma capacidade por vias equivalentes (pan + crosshair ao vivo) + reconhecimento de que scroll-zoom é default do LWC v5; humano aprovou com a ressalva. Não bloqueia o aceite.

## User Setup Required

None - nenhuma configuração externa. O CDN unpkg (herdado do plano 01) é carregado em runtime no navegador do usuário.

## Next Phase Readiness

- **Phase 17 pronta para fechar:** LWC-01/02/03 verificados; invariantes da v1.4 (283 goldens, `grafico.py` intacto, `app.py` thin renderer) preservados; smoke humano aprovado sem regressão.
- Próximo passo do operador: o gsd-verifier roda a seguir para o gate de verificação da fase; depois, fechar a fase/milestone v1.4.

---
*Phase: 17-modo-trading-candlestick-tradingview-lightweight-charts*
*Completed: 2026-07-01*

## Self-Check: PASSED

- FOUND: .planning/phases/17-.../17-03-SUMMARY.md
- FOUND commit: beee763 (17-01 Task 1) / 041af2b (17-01 Task 2)
- FOUND commit: ae59b2d (17-02 Task 1) / ab630b6 (17-02 Task 2)
- Task 1 (automatizada) verde no agente anterior: 283 pytest passed; grafico.py intacto; _render_lwc thin renderer.
- Task 2 (human-verify): APROVADO — candlestick LWC v5 ao vivo, valores canônicos BBSE3 (alvo 41,74 / stop 37,50 / Fib 39,12-38,50), crosshair, console limpo, sem regressão em Plotly/Analisar/Ranking/Garimpo.
