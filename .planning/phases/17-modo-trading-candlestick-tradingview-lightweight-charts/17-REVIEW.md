---
phase: 17-modo-trading-candlestick-tradingview-lightweight-charts
reviewed: 2026-07-01T00:00:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - app.py
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 17: Code Review Report

**Reviewed:** 2026-07-01
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues_found

## Summary

Escopo revisado: o toggle "Modo Trading" na aba Swing, a função `_render_lwc(...)`
(Lightweight Charts v5 renderizado via `st.components.v1.html` com template HTML/JS
inline) e os overlays da engine portados para o JS (BandPrimitive, createPriceLine,
createSeriesMarkers, neckline LineSeries).

Pontos positivos confirmados:
- **SRI/CDN pinning está correto.** Baixei o bundle real `lightweight-charts@5.2.0`
  e recalculei `sha384` — bate exatamente com o `integrity` da linha 200
  (`q1KYLSKHgBnW5tWYGGR8+6YV4/iPy31dILoF2I1OD7XiVUvHEp/TaxIQVmB0j3R2`). Versão
  exata + SRI + `crossorigin` mitigam o tampering do bundle de terceiros.
- **Invariante read-only respeitado.** `_render_lwc` só lê `f.ohlc`, `sw`, `sinais`,
  `est`; não há recompute da engine (o `sorted(...)` é apenas ordenação de pivôs).
- **Degradação dos campos da engine** (S/R, entrada, stop, alvo, fib, padrões) está
  bem gateada por `est[...]` e por `is not None`/listas vazias — grupos desligados
  serializam vazios sem quebrar o JS.

A preocupação central é a **serialização Python->JS sem escape para o contexto
`<script>`**, que abre uma superfície de injeção via o ticker (input do usuário) e
também quebra o render em entradas legítimas com caracteres especiais. Há ainda
lacunas de degradação (CDN offline) e de robustez a NaN/timezone.

## Critical Issues

### CR-01: `json.dumps` interpolado em `<script>` sem escape — breakout `</script>` / XSS via ticker

**File:** `app.py:141,200-334` (interpolação em `app.py:228,312,335`)
**Issue:**
`range_key_json = json.dumps(f"lwc_range_{ticker}_{tf_key}")` (linha 141) é embutido
cru no template como `const RANGE_KEY = {range_key_json};` (linha 312), dentro de um
bloco `<script>`. `ticker` vem de `st.text_input(...).strip().upper()` (linha 835) e
**não é validado/sanitizado**. `json.dumps` **não escapa** `<`, `>`, `/` nem os
separadores de linha U+2028/U+2029. O parser HTML fecha o `<script>` ao encontrar a
sequência `</script>` (case-insensitive — `</SCRIPT>` maiúsculo também fecha), então
um ticker como `</SCRIPT><IMG SRC=X ONERROR=...>` injeta markup/JS arbitrário no
iframe do componente. Além do vetor de injeção (self-XSS, mas o iframe do Streamlit
roda com `allow-scripts`), o mesmo defeito **quebra o render** para qualquer input
benigno contendo `<`, `>` ou `/`, deixando o candle em branco. Os mesmos
`json.dumps` de `candles`/`vols`/`overlays` (linhas 136-137,196) carregam strings da
engine (`tipo`, fib `nome`) com o mesmo risco de breakout, embora hoje sejam valores
controlados.
**Fix:**
Escapar a saída de `json.dumps` para o contexto de script (padrão de mercado), em
TODAS as interpolações que entram no `<script>`. Substituir os caracteres `<`, `>`,
`&` e os separadores de linha U+2028 e U+2029 por seus escapes JS:
```python
def _js(obj):
    return (json.dumps(obj)
            .replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))

candles_json = _js(candles)
vols_json    = _js(vols)
overlays_json = _js(overlays)
range_key_json = _js(f"lwc_range_{ticker}_{tf_key}")
```
Complementarmente, restringir o ticker na borda a `[A-Z0-9]` (ex.:
`re.sub(r"[^A-Z0-9]", "", ticker)`).

## Warnings

### WR-01: Falha silenciosa se o bundle da CDN não carregar (sem degradação)

**File:** `app.py:200-202`
**Issue:**
A linha 202 desestrutura `const { createChart, ... } = LightweightCharts;` **fora de
qualquer try/catch**. Se o unpkg estiver indisponível/bloqueado, ou se o SRI não
casar (ex.: proxy corporativo alterando o corpo), o browser recusa executar o
`<script src=...>` e `LightweightCharts` fica `undefined` → `ReferenceError` no topo
do segundo `<script>`. O usuário vê um bloco vazio de 580px, **sem mensagem**,
enquanto a vista Plotly (mesmos dados) funciona. Os try/catch existentes cobrem só os
overlays, não o carregamento da lib.
**Fix:**
Guardar o boot atrás de uma checagem e emitir fallback visível no próprio HTML:
```javascript
if (typeof LightweightCharts === 'undefined') {
  el.innerHTML = '<div style="color:#d1d4dc;padding:16px">' +
    'Não foi possível carregar o gráfico TradingView (CDN indisponível). ' +
    'Volte para a vista Plotly.</div>';
} else {
  const { createChart, /* ... */ } = LightweightCharts;
  /* ... resto do boot ... */
}
```

### WR-02: OHLC/Volume com NaN serializa como token `NaN` e quebra o LWC

**File:** `app.py:128-134,136-137`
**Issue:**
`float(row["Open"])` etc. não filtram NaN, e `json.dumps` (com `allow_nan=True`
default) emite o token literal `NaN`. Em `candle.setData([... {"open": NaN} ...])` o
Lightweight Charts rejeita/renderiza quebrado o ponto (ou a série). O volume tenta
guardar `None` com `float(row.get("Volume", 0) or 0)`, mas `NaN or 0` mantém `NaN`
(NaN é truthy). A vista Plotly tolera gaps/NaN; a de LWC não. Frames intraday
best-effort do Yahoo podem trazer barras com NaN.
**Fix:**
Descartar/limpar linhas com NaN antes de serializar (mantém read-only, é só filtro de
apresentação):
```python
import math
...
if any(math.isnan(x) for x in (o, h, lo, c)):
    continue
vol_val = float(row.get("Volume", 0) or 0)
if math.isnan(vol_val):
    vol_val = 0.0
```

### WR-03: Tempo intraday em epoch UTC — eixo/crosshair deslocado e dependente do tz do frame

**File:** `app.py:127,151`
**Issue:**
Para intraday, `int(ts.timestamp())` gera epoch UTC e o LWC (`UTCTimestamp`) exibe o
eixo/crosshair **em UTC**. Se o índice de `f.ohlc` for tz-naive, `ts.timestamp()`
assume o tz local do servidor (a VPS), deslocando as barras conforme o fuso da
máquina; se for tz-aware, o horário exibido fica em UTC (≈3h à frente do BRT) e
**inconsistente com a vista Plotly**, que mostra o horário local. Para o usuário, a
mesma barra aparece em horários diferentes nas duas vistas.
**Fix:**
Fixar o fuso explicitamente ao converter (converter para America/Sao_Paulo e ajustar
o epoch, ou configurar o LWC com `timeScale.timezone`/formatação local), garantindo
paridade com a leitura da vista Plotly. Documentar a premissa de tz do frame.

## Info

### IN-01: Indentação de 2 espaços no bloco `if vista == "Modo Trading":` / `else`

**File:** `app.py:979-984`
**Issue:**
Dentro de `with grafico_box:` o `if/else` que escolhe LWC vs Plotly usa indentação de
2 espaços, enquanto o restante do arquivo usa 4. É Python válido, mas visualmente
destoante e propenso a erro em edições futuras (o corpo do `else` fica com um nível de
recuo diferente do padrão do arquivo).
**Fix:**
Reindentar o bloco para 4 espaços, alinhado ao restante do módulo.

### IN-02: Comentário do SRI parece placeholder truncado

**File:** `app.py:109-110`
**Issue:**
O comentário mostra `sha384-q1KYLSKHgBnW5tWYGGR8+6YV4/...` com reticências, dando a
impressão de hash placeholder/incompleto — embora o `integrity` real da linha 200
esteja correto (verificado). Pode induzir um mantenedor a "consertar" um SRI que já
está certo.
**Fix:**
Substituir as reticências pelo hash completo no comentário, ou remover o comentário e
deixar só o `integrity` da tag.

---

_Reviewed: 2026-07-01_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
