---
phase: 17-modo-trading-candlestick-tradingview-lightweight-charts
plan: 01
subsystem: ui
tags: [streamlit, lightweight-charts, tradingview, candlestick, components-html, localStorage, swing-trade]

# Dependency graph
requires:
  - phase: 16-swing-trade-ui
    provides: "bloco _render_swing (fragment) com f.ohlc/sw/sinais/est/tf_key já montados e grafico_box reservado"
provides:
  - "Vista 'Modo Trading' (toggle radio 'swing_vista') no bloco de swing; Plotly permanece default"
  - "_render_lwc(f, sw, sinais, est, ticker, tf_key) — candlestick nominal via Lightweight Charts v5 (CDN pinado + SRI)"
  - "Persistência client-side do range visível entre reruns via localStorage por par (ticker, tf_key)"
  - ".phase-base-sha (base fixa da fase p/ gates de invariância dos planos 02/03)"
affects: [17-02-overlays-engine, 17-03-verificacao]

# Tech tracking
tech-stack:
  added: []  # ZERO dependência Python nova — só st.components.v1.html + CDN unpkg
  patterns:
    - "components.html + CDN pinado (@5.2.0) com integrity sha384 inline + crossorigin — mitiga T-17-01"
    - "Persistência client-side via localStorage (ponte components.html é unidirecional Python→JS)"
    - "try/catch independentes em todo acesso a localStorage; catch da leitura cai p/ fitContent"

key-files:
  created: []
  modified:
    - "app.py — imports (json, components), _render_lwc module-level, toggle de vista, gate Plotly/LWC"
    - ".planning/.../.phase-base-sha — SHA base da fase"

key-decisions:
  - "Modo Trading = vista alternativa (radio 'swing_vista', Plotly default) que troca só a camada de render sobre os mesmos dados (zero fetch/recálculo)"
  - "_render_lwc é module-level com tf_key na assinatura desde já (contrato p/ waves 02/03: chave de localStorage e conversão de epoch de pivô)"
  - "SRI sha384 REAL computado do bundle @5.2.0, inline no <script> (não via variável) p/ satisfazer o gate literal e a mitigação T-17-01"
  - "time diário = string '%Y-%m-%d'; intraday = epoch UTC segundos (UTCTimestamp) p/ crosshair/eixo corretos"
  - "Persistência de range é CLIENT-SIDE (localStorage por par) — o CONTEXT citava session_state+setVisibleRange, mas components.html não tem round-trip JS→Python; localStorage entrega o mesmo comportamento observável"

patterns-established:
  - "CDN de terceiro em components.html sempre pinado por versão + integrity sha384 + crossorigin"
  - "Acesso a localStorage em iframe sandbox sempre em try/catch; a renderização do chart nunca depende da persistência"

requirements-completed: [LWC-01, LWC-03]

# Metrics
duration: 10min
completed: 2026-07-01
---

# Phase 17 Plan 01: Modo Trading — Candlestick TradingView (Lightweight Charts) Summary

**Vista 'Modo Trading' (toggle) no bloco de swing renderiza candlestick + volume + linha de último preço via Lightweight Charts v5 (CDN unpkg @5.2.0 pinado + SRI), reusando f.ohlc/sw/sinais já montados sem novo fetch, com range visível persistido entre reruns via localStorage por par.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-07-01T14:00:00Z (aprox.)
- **Completed:** 2026-07-01T14:08:00Z (aprox.)
- **Tasks:** 2
- **Files modified:** 1 (app.py) + 1 criado (.phase-base-sha)

## Accomplishments
- Toggle de vista "Plotly | Modo Trading" (chave isolada `swing_vista`, Plotly default) dentro de `_render_swing`; o bloco Plotly roda inalterado quando "Plotly" está selecionado.
- Função module-level `_render_lwc(f, sw, sinais, est, ticker, tf_key)` que serializa `f.ohlc` nominal em `candles`/`vols` JSON e monta o template `components.html` (candlestick + volume histograma + linha de último preço) espelhando o spike 001.
- CDN unpkg `lightweight-charts@5.2.0` pinado com `integrity="sha384-q1KYLSKHgBnW5tWYGGR8+6YV4/iPy31dILoF2I1OD7XiVUvHEp/TaxIQVmB0j3R2"` (hash REAL computado via `openssl dgst -sha384`) + `crossorigin="anonymous"` — mitiga T-17-01.
- Persistência do range visível entre reruns via `localStorage` por par (`lwc_range_<ticker>_<tf_key>`): leitura na criação (`setVisibleLogicalRange` se salvo, senão `fitContent`) + gravação no callback `subscribeVisibleLogicalRangeChange`, com try/catch independentes.
- 283 testes golden verdes; `grafico.py` intacto; zero dependência Python nova.

## Task Commits

Each task was committed atomically:

1. **Task 1: Toggle de vista + _render_lwc (candlestick base)** - `beee763` (feat)
2. **Task 2: Persistência do range visível entre reruns (LWC-03)** - `041af2b` (feat)

## Files Created/Modified
- `app.py` — imports `json` e `streamlit.components.v1 as components`; função module-level `_render_lwc`; toggle de vista `swing_vista` antes de `grafico_box`; ramo condicional `if vista == "Modo Trading": _render_lwc(...)` else Plotly (bloco Plotly inalterado, apenas re-aninhado sob `else`).
- `.planning/phases/17-.../.phase-base-sha` — SHA base fixa da fase (`5a93e24f05bcb336bce99115e9c29b3f57a0aeae`), ponto de comparação p/ os gates de invariância dos planos 02/03 (evita `HEAD~N` de contagem imprevisível).

## Decisions Made

- **SHA base da fase gravado:** `5a93e24f05bcb336bce99115e9c29b3f57a0aeae` em `.phase-base-sha`. É o ponto contra o qual o plano 03 diffa para provar `grafico.py` intacto.
- **Mecanismo de persistência de range escolhido:** **localStorage client-side por par (ticker, tf_key)**, não `session_state`. O CONTEXT (LWC-03) cita "session_state + setVisibleRange", mas `components.html` é uma ponte **unidirecional** (Python→JS): não há round-trip JS→Python para ler o range de volta e guardar em `session_state`. O `localStorage` por-iframe entrega o **mesmo comportamento observável** de persistência (zoom/pan sobrevive a rerun) sem sair do sandbox. Chave por par evita "vazar" zoom de um ticker/timeframe para outro.
- **Hash SRI aplicado:** `sha384-q1KYLSKHgBnW5tWYGGR8+6YV4/iPy31dILoF2I1OD7XiVUvHEp/TaxIQVmB0j3R2` — computado do bundle real `@5.2.0` (196.203 bytes) via `curl -sL … | openssl dgst -sha384 -binary | openssl base64 -A`. **Inline** no `<script>` (não via variável) para que o gate literal `grep 'integrity="sha384-'` passe e a mitigação T-17-01 fique auditável no fonte.
- **Formato de time diário vs intraday:** diário → string `"%Y-%m-%d"` (como o spike); intraday (1h/30m/5m) → `int(ts.timestamp())` = epoch UTC **segundos** (UTCTimestamp do LWC), porque o spike só cobriu diário e o eixo de tempo/crosshair do LWC quebra com string em barras datetime.
- **Robustez do localStorage:** `getItem` (leitura) e `setItem` (gravação) em blocos `try/catch` **independentes**; o `catch` da leitura cai para `fitContent()`, garantindo que um `SecurityError` de iframe sandbox/origem opaca **nunca** impeça o candlestick de renderizar (best-effort).

## Deviations from Plan

None - plan executed exactly as written.

Ajuste menor de implementação (não é desvio de escopo): o bloco Plotly existente (app.py) foi **re-aninhado** sob um `else:` do novo gate de vista usando indentação de 2 espaços para o `if`/`else` (18 col) mantendo o corpo Plotly no seu nível original de 20 col — evitou re-indentar ~100 linhas e mantém o diff mínimo. Sintaxe validada por `ast.parse` e os 283 goldens.

## Issues Encountered

- **Gate `integrity="sha384-` falhava com a variável:** a primeira versão usou `integrity="{_LWC_CDN_SRI}"` (f-string placeholder), então o literal não aparecia no fonte e o `grep` do critério de aceite falhava. Resolvido inlinando o hash literal no `<script>` e removendo a variável (mantida só como comentário de proveniência).

## User Setup Required

None - no external service configuration required. O CDN unpkg é carregado em runtime no browser (rede do usuário); sem chaves/segredos.

## Next Phase Readiness
- Plano **17-02** (overlays da engine): pronto — `_render_lwc` já recebe `tf_key` (usado p/ converter `ts` de pivô em epoch) e `sw`/`sinais`; o template JS é o ponto de extensão p/ `createPriceLine` (stop/alvo/fib), `BandPrimitive` (zona/S-R) e `createSeriesMarkers` (pivôs), espelhando o spike 002.
- Plano **17-03** (verificação): a base fixa `.phase-base-sha` está gravada para o diff de invariância de `grafico.py`; o smoke visual no navegador (candlestick TV-like, toggle, persistência de zoom) fica para o checkpoint humano.

---
*Phase: 17-modo-trading-candlestick-tradingview-lightweight-charts*
*Completed: 2026-07-01*

## Self-Check: PASSED

- FOUND: app.py
- FOUND: .planning/phases/17-.../.phase-base-sha
- FOUND commit: beee763 (Task 1)
- FOUND commit: 041af2b (Task 2)
- 283 pytest passed; grafico.py intacto; gates estáticos (def _render_lwc, lightweight-charts@5.2.0, integrity="sha384-, sem addCandlestickSeries, setVisibleLogicalRange + localStorage + fitContent) todos OK.
