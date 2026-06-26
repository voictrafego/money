---
phase: 05-motor-de-indicadores-puro
reviewed: 2026-06-26T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/analista/core/indicators.py
  - tests/test_indicators.py
  - config.yaml
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-06-26
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Revisão do motor puro de indicadores técnicos (`indicators.py`): SMA/EMA + crosses,
RSI/MACD, Donchian/Bollinger/squeeze, ADX dupla-Wilder, regressão trailing e o entry-point
`calcular()`. A matemática nominal está sólida e bem ancorada: a suíte `test_indicators.py`
(15 testes) passa integralmente, incluindo as âncoras canônicas de Wilder (RSI 70,5328),
o cross-check do ADX contra TradingView, e os testes de no-repaint/causalidade. Não há
vulnerabilidades de segurança (módulo puro, sem I/O nem entrada externa direta) — **0 BLOCKER**.

As três WARNINGs são todas sobre **caminhos de preço degenerado (flat / ilíquido)** e sobre
**assimetria de degradação graciosa** — exatamente o tipo de cenário comum em small-caps de
dividendos com pregão ralo, que a suíte golden (séries sintéticas com ruído) não exercita.
Dado o Core Value do projeto ("números fiéis e consistentes"), valem correção antes de expor
na UI.

## Warnings

### WR-01: NaN no DX envenena o ADX inteiro a partir daquele ponto (sem recuperação)

**File:** `src/analista/core/indicators.py:94-108` (`_wilder_rma_from`) e `:286-294` (`adx_wilder`)
**Issue:** Quando não há movimento direcional sobre a janela de suavização (`sm_pdm == 0`
e `sm_ndm == 0` simultaneamente → `denom == 0`), o DX vira `np.nan` (linha 291). A 2ª
suavização de Wilder é recursiva e **não trata NaN**: `out[i] = a*arr[i] + (1-a)*out[i-1]`.
Basta um único DX NaN para que:
1. se ele cair na janela-semente `dx[length:2*length]`, o seed `arr[start:start+length].mean()`
   (numpy mean propaga NaN) fique NaN → **ADX todo-NaN para sempre** → `forca_adx` =
   "indisponivel" mesmo com anos de histórico;
2. se cair depois da semente, `out[i-1]` NaN → `a*dx[i] + (1-a)*NaN = NaN` → **todo o ADX
   subsequente vira NaN**, permanentemente.
Cenário real: small-cap de dividendos com um trecho de preço travado (highs/lows iguais) no
início ou no meio da série. A docstring afirma "ATR==0 ou +DI+−DI==0 → NaN, nunca inf", mas
não cobre a propagação destrutiva do NaN pela recursão. Não há teste para preço flat.
**Fix:** tornar a RMA de Wilder robusta a NaN — semear com `np.nanmean` e, na recursão,
carregar o valor anterior quando a amostra atual for NaN (forward-fill do estado), ou
substituir o DX NaN por 0 antes da 2ª suavização (DX=0 = sem direção, semanticamente correto):
```python
# em adx_wilder, antes da 2ª suavização:
dx = np.where(np.isnan(dx) & ~np.isnan(atr), 0.0, dx)  # sem direção ⇒ DX 0, não NaN
adx_arr = _wilder_rma_from(dx, length, start=length)
```
ou, mais geral, em `_wilder_rma_from`:
```python
seed = arr[start:start + length]
out[start + length - 1] = np.nanmean(seed)
for i in range(start + length, len(arr)):
    prev = out[i - 1]
    out[i] = prev if np.isnan(arr[i]) else a * arr[i] + (1 - a) * prev
```

### WR-02: volatilidade zero (sd==0) colapsa as bandas e dispara "banda_superior" falso

**File:** `src/analista/core/indicators.py:213-224`
**Issue:** Com 20 closes idênticos (preço travado / ilíquido), `sd = std(ddof=0) == 0`, então
`bb_sup == bb_med == bb_inf == close`. O teste de toque usa `close.iloc[-1] >= bb_sup.iloc[-1]`
(igualdade satisfaz) → reporta **"banda_superior"** para uma ação completamente parada — um
sinal claramente enganoso. O squeeze também mente nesse caso: `largura_bb = 0` para toda a
janela → `(x <= x[-1]).mean() == 1.0` → 100% → `squeeze_off`, quando a realidade é largura
nula (squeeze máximo). Nenhum dos dois é coberto por teste.
**Fix:** tratar largura/desvio nulo como ausência de sinal:
```python
if len(close) == 0 or pd.isna(bb_sup.iloc[-1]) or pd.isna(bb_inf.iloc[-1]) \
        or bb_sup.iloc[-1] == bb_inf.iloc[-1]:
    toque = "indisponivel"   # bandas colapsadas ⇒ sem informação de toque
elif close.iloc[-1] >= bb_sup.iloc[-1]:
    ...
```

### WR-03: MACD/EMA sem guarda de warmup — emitem sinal "confiante" com histórico curto

**File:** `src/analista/core/indicators.py:125-127` (EMA) e `:362-388` (MACD + cruzamento_macd)
**Issue:** `close.ewm(span=, adjust=False).mean()` não usa `min_periods`, então produz valores
desde a barra 0 — o MACD (span lento 26) devolve um número aparentemente válido mesmo com 12
barras, e `cruzamento_macd` reporta "cruz_alta"/"cruz_baixa"/"nenhum" (nunca "indisponivel")
nesse regime. Isso quebra a simetria de degradação graciosa do resto do módulo (SMA usa
`min_periods=janela` → NaN → "indisponivel"; RSI degrada via seed NaN). `test_calcular_degrada`
verifica que posicao/forca/rompimento/rsi/squeeze degradam no caso de 12 barras, mas
**não** verifica `cruzamento_macd` — justamente o que não degrada. As EMA20/50/200 expostas
para o plot (Phase 7) também ficam ≈ preço nas primeiras barras (sem warmup), podendo enganar
visualmente. Contradiz o Core Value de consistência.
**Fix:** mascarar o MACD (e opcionalmente as EMAs do plot) até o slow EMA aquecer:
```python
slow_ema = close.ewm(span=slow, adjust=False).mean()
warmup = close.notna().cumsum() < slow      # < 26 observações
macd = (close.ewm(span=fast, adjust=False).mean() - slow_ema).mask(warmup)
macd_sinal = macd.ewm(span=signal, adjust=False).mean()
```
e o bloco de `cruzamento_macd` já degrada para "indisponivel" via `dropna()` (`len(d) < 2`).

## Info

### IN-01: imports não utilizados

**File:** `src/analista/core/indicators.py:20-21,27`
**Issue:** `field` (de `dataclasses`), `List` e `Sequence` (de `typing`) não são usados; o alias
`Number = Optional[float]` (e portanto `Optional`) também não é referenciado em lugar nenhum.
**Fix:** remover `field`, `List`, `Sequence`, e o alias `Number`/`Optional` — reduzir o cabeçalho a
`from dataclasses import dataclass` e remover a linha 27.

### IN-02: anotação de tipo incoerente com o default

**File:** `src/analista/core/indicators.py:59-60`
**Issue:** `donchian_sup_55: pd.Series = None` (e `_inf_55`) declara `pd.Series` mas tem default
`None` — incoerente com a anotação.
**Fix:** `donchian_sup_55: Optional[pd.Series] = None` (e idem `_inf_55`).

### IN-03: r2 da regressão pode virar NaN em série flat (não guardado)

**File:** `src/analista/core/indicators.py:320-323`
**Issue:** Para janela de preço perfeitamente flat, `stats.linregress` produz `rvalue` indefinido
(variância de y = 0 → 0/0), logo `r2 = rvalue**2` pode ser NaN. `slope_ann` já é 0 corretamente
(testado), mas o r2 nesse caso não é testado nem documentado. Degradação para NaN é aceitável,
porém silenciosa.
**Fix:** opcional — `r2[i] = res.rvalue ** 2 if np.isfinite(res.rvalue) else np.nan` e documentar
o comportamento flat.

### IN-04: comparação de igualdade decide o lado em posicao_mm200

**File:** `src/analista/core/indicators.py:132`
**Issue:** `posicao = "acima" if close > sma200 else "abaixo"` — empate exato (`close == sma200`)
cai em "abaixo". Irrelevante numericamente (probabilidade ~nula com floats reais), apenas nota
de simetria com WR-02 (preferir igualdade explícita onde colapso é possível).
**Fix:** nenhuma ação necessária; registrado por completude.

---

_Reviewed: 2026-06-26_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
