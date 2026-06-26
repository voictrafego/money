# Phase 5: Motor de indicadores puro - Research

**Researched:** 2026-06-26
**Domain:** Indicadores técnicos hand-rolled em numpy/pandas/scipy (módulo puro travado por golden tests)
**Confidence:** HIGH (matemática verificada em runtime nesta sessão; padrões do projeto lidos diretamente do código)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** A engine devolve um dataclass **agrupado por família** (`tendencia` / `canais` / `forca` / `momentum`). Cada família carrega as **séries** (plot da Phase 7) **e** os **sinais discretos em estados curtos/neutros** — chaves estáveis tipo `"acima"`/`"abaixo"`, `"golden_cross"`/`"death_cross"`/`"nenhum"`, `"squeeze_on"`/`"squeeze_off"`, `"sobrecomprado"`/`"sobrevendido"`/`"neutro"`. **Frases consultivas em linguagem natural PT NÃO entram aqui** — são da Phase 6. A engine separa **cálculo** de **apresentação**.
- **D-02:** Sem Keltner. Squeeze definido por **percentil da própria largura**: `squeeze_on` quando a largura normalizada da BB `(banda_sup − banda_inf) / banda_media` está **≤ percentil 20** numa **janela móvel de ~126 pregões**. Janela e percentil são parâmetros canônicos em `cfg`.
- **D-03:** Computa **SMA E EMA sempre** (20/50/200). O toggle do usuário (Phase 7) só troca o overlay exibido, sem recompute. Os **sinais discretos** de tendência (golden/death cross MM50×MM200, posição preço×MM200) são **SEMPRE calculados sobre SMA**. A EMA é vista alternativa visual, nunca altera o sinal.
- **D-04:** Regressão linear sobre **~90 pregões** da série **split-adjusted**. Direção + força expressas como **slope anualizado normalizado pelo preço (% ao ano)** e **R²** (qualidade do ajuste). Janela é parâmetro canônico em `cfg`.

### Claude's Discretion
- Nomes exatos dos campos/subdataclasses do `SinaisTecnicos` (desde que agrupados por família e com sinais discretos em chaves estáveis e neutras).
- Tipagem dos sinais discretos (str literal vs Enum) — desde que determinística e testável por golden.
- Estrutura interna das funções puras por indicador (uma por família vs por indicador) — desde que pura, sem rede, e o entry point seja `calcular(ohlc, cfg)`.
- Nomes/defaults exatos das chaves de `cfg` (ex.: `squeeze_janela=126`, `squeeze_percentil=20`, `regressao_janela=90`) — desde que canônicos e documentados.
- Tratamento de histórico curto por indicador (ex.: MM200 com < 200 pregões → NaN inicial / sinal `"indisponivel"`).

### Deferred Ideas (OUT OF SCOPE)
- **MOM-03** (divergências RSI/MACD vs preço) — fora do marco v1.2.
- Outros indicadores (Keltner, Ichimoku, VWAP, estocástico) — fora das 4 famílias.
- Fiação em `analisar_acao`/`a.sinais`, composite de timing, matriz fundamento×técnico, alerta de reverificação, paridade CLI (Phase 6).
- Overlays, subpainéis, toggles, tooltips na UI (Phase 7).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TREND-01 | SMA 20/50/200 sobrepostas ao preço | Pattern 1 (SMA/EMA via `.rolling().mean()` / `.ewm()`); causal por construção |
| TREND-02 | Posição preço×MM200 (acima/abaixo) | Sinal discreto sobre SMA200; degradação `"indisponivel"` com <200 bars |
| TREND-03 | Golden/death cross (MM50×MM200) | Cruzamento causal por mudança de sinal de `sma50 − sma200`; sobre SMA (D-03) |
| TREND-04 | Toggle EMA além de SMA | Ambas as séries sempre computadas (D-03); toggle só na Phase 7 |
| CHAN-01 | Donchian 20/55 com rompimentos | Donchian causal `rolling(n).max().shift(1)` (Pitfall 4) |
| CHAN-02 | Bollinger 20/2σ com toque/rompimento | SMA20 ± 2·std(ddof=0); rótulo de toque causal |
| CHAN-03 | Bollinger squeeze (D-02) | Percentil rolling causal de largura normalizada (Pattern 4, verificado) |
| FORCE-01 | ADX(14) Wilder, força <20/>25 | Cadeia Wilder completa TR→DM→DI→DX→ADX (Pattern 3, verificado) |
| FORCE-02 | Inclinação da regressão linear (D-04) | `scipy.stats.linregress` trailing, %/ano + R² (Pattern 5, verificado) |
| MOM-01 | RSI(14) Wilder, faixas 30/70 | RSI Wilder SMA-seeded → bate 70.53 canônico (Pattern 2, verificado) |
| MOM-02 | MACD 12/26/9 com cruzamento de sinal | EMA padrão (não Wilder); cruzamento causal linha×sinal |
| TEST-03 | Golden RSI/ADX Wilder vs TradingView | Fixture canônica de Wilder embutida (HIGH); ADX cross-check na validação |
| TEST-04 | No-repaint `ind(s[:k])[-1]==ind(s)[k-1]` | Verificado exato para RSI e ADX nesta sessão (Validation Architecture) |
| TEST-05 | Série split-adjusted sem cruzamentos espúrios | Reusar fixture ITSA4 de `test_ingest_ohlc.py` → alimentar a engine |
</phase_requirements>

## Summary

Esta fase é um exercício de **fidelidade matemática hand-rolled**, não de descoberta de stack. Todas as dependências já estão instaladas e travadas (numpy 2.4.6, pandas 3.0.3, scipy 1.17.1, Python 3.14.5 no `.venv`) e a decisão de não adicionar bibliotecas de TA (`ta`/`pandas-ta`/`TA-Lib`) já está locked — essas libs sequer instalam contra pandas 3.0. O risco real está em **três armadilhas numéricas**: (1) a suavização de Wilder (RSI/ADX) precisa de seed por SMA, senão diverge do TradingView; (2) o ADX tem **dupla** suavização de Wilder e a segunda precisa seedar no primeiro DX válido (não na posição 0 do array); (3) vários sinais (Donchian breakout, squeeze percentil, regressão) podem vazar dados futuros se mal escritos. Verifiquei as três em runtime nesta sessão.

O contrato `SinaisTecnicos` espelha o padrão `ResultadoDDM` de `ddm.py`: `@dataclass` puro, sem rede, com derivações em `__post_init__` quando útil. O ponto de entrada é `indicators.calcular(ohlc, cfg) -> SinaisTecnicos`, onde `ohlc` é o `CompanyData.ohlc_ajustado` (split-adjusted, entregue na Phase 4) e `cfg` é o dict YAML aninhado já usado em todo o projeto — basta uma nova seção `indicadores:` em `config.yaml`.

A trava de qualidade é golden test offline (padrão de `tests/test_ddm.py` e `tests/test_ingest_ohlc.py`): fixtures sintéticas determinísticas + `pytest.approx` / `np.testing.assert_allclose`, zero rede. A fixture âncora do RSI é o dataset canônico de Wilder (mesmo usado por StockCharts/Wikipedia/TradingView), cujo primeiro RSI(14) é **70.5328** — confirmei que a implementação SMA-seeded bate exatamente esse valor e que a `ewm` ingênua (sem seed) dá 50.75 (errado).

**Primary recommendation:** Escreva `indicators.py` como funções puras por indicador agrupadas em 4 famílias, suavização de Wilder via helper único `_wilder_rma(serie, length)` (seed = SMA dos primeiros `length`), e trave RSI/ADX/no-repaint/split com a fixture de Wilder embutida antes de qualquer integração. A captura dos valores TradingView do ADX é o único passo de **validação humana** (não de pesquisa) antes de fechar o golden.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Cálculo de séries (SMA/EMA/BB/Donchian/ADX/RSI/MACD/regressão) | Core puro (`core/indicators.py`) | — | Matemática determinística sem I/O; espelha `core/ddm.py` |
| Derivação de sinais discretos (cross, posição, squeeze, sobrecompra) | Core puro (`core/indicators.py`) | — | Faz parte do contrato `SinaisTecnicos` (D-01); testável por golden |
| Composição do timing / linguagem natural / matriz fundamento×técnico | Engine de relatório (`report.analisar_acao`) | — | Phase 6 — fora desta fase (D-01 separa cálculo de apresentação) |
| Origem do frame OHLC split-adjusted | Ingest (`ingest/prices.py`) | `core/fundamentals.py` | Já entregue na Phase 4 (`CompanyData.ohlc_ajustado`) |
| Parâmetros canônicos (janelas, σ, faixas) | Config (`config.yaml` → `cfg` dict) | — | Ponto único compartilhado por CLI e UI |
| Render de overlays/subpainéis/toggles | UI (`app.py`) / CLI | — | Phase 7 / Phase 6 — lê `a.sinais` read-only |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.4.6 | Aritmética vetorizada, NaN handling, `assert_allclose` nos testes | Já presente; base de toda a engine `[VERIFIED: .venv/bin/python]` |
| pandas | 3.0.3 | `Series.rolling`/`ewm`/`diff`/`clip`/`shift`, índice de datas | Já presente; o OHLC é `pd.DataFrame` `[VERIFIED: .venv/bin/python]` |
| scipy | 1.17.1 | `scipy.stats.linregress` para a regressão (FORCE-02) | Já presente; evita hand-roll de OLS+R² `[VERIFIED: .venv/bin/python]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | (configurado em `pyproject.toml`) | Golden tests offline | Toda a trava de fidelidade (TEST-03/04/05) `[VERIFIED: pyproject.toml]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-roll numpy/pandas | `ta` / `pandas-ta` / `TA-Lib` | **REJEITADO (locked):** incompatíveis com numpy 2.4.6 / pandas 3.0.3; viola "zero novas deps" e custo zero |
| `scipy.stats.linregress` | `numpy.polyfit` (grau 1) | `polyfit` não devolve R² direto (precisaria computar à mão); `linregress` dá slope + `rvalue` (R²=`rvalue²`) num call `[VERIFIED]` |
| `Series.ewm(alpha=1/n)` cru | Loop recursivo de Wilder | Ambos funcionam, mas `ewm` **sem seed por SMA diverge do TradingView** (ver Pitfall 1) — o loop seedado é o mais legível e auditável |

**Installation:** Nenhuma. `[VERIFIED: .venv]` Todas as deps já estão no ambiente; a fase NÃO deve rodar `pip install`.

**Version verification (executado nesta sessão):**
```
numpy 2.4.6   pandas 3.0.3   scipy 1.17.1   Python 3.14.5 (.venv)
```

## Architecture Patterns

### System Architecture Diagram

```
CompanyData.ohlc_ajustado (pd.DataFrame OHLCV split-adjusted, Phase 4)
        │
        │  cfg["indicadores"]  (defaults de config.yaml)
        ▼
indicators.calcular(ohlc, cfg)               ← ENTRY POINT (puro, sem rede)
        │
        ├─► _tendencia(close, cfg)  ──► SMA/EMA 20/50/200 (séries)
        │        └─ sinais: posição×MM200, golden/death cross  (sobre SMA, D-03)
        ├─► _canais(o,h,l,c, cfg)   ──► Donchian 20/55, Bollinger 20/2σ (séries)
        │        └─ sinais: rompimento Donchian, toque BB, squeeze (percentil, D-02)
        ├─► _forca(o,h,l,c, cfg)    ──► ADX(14) Wilder + regressão 90d (séries)
        │        └─ sinais: força (sem tend.<20 / forte>25), slope %/ano + R²
        └─► _momentum(close, cfg)   ──► RSI(14) Wilder + MACD 12/26/9 (séries)
                 └─ sinais: sobrecomprado/sobrevendido, cruzamento MACD×sinal
        │
        ▼
SinaisTecnicos(tendencia=…, canais=…, forca=…, momentum=…)   ← séries + sinais discretos
        │
        ▼
(Phase 6) report.analisar_acao → a.sinais   |   (Phase 7) app.py overlays
```

### Recommended Project Structure
```
src/analista/core/
├── indicators.py      # NOVO: SinaisTecnicos + calcular() + funções puras por família
├── ddm.py             # padrão a espelhar (dataclass + funções puras)
├── fundamentals.py    # CompanyData.ohlc_ajustado (input)
└── multiples.py       # idem padrão
tests/
└── test_indicators.py # NOVO: golden Wilder + no-repaint + split + degradação
config.yaml            # +seção `indicadores:` (parâmetros canônicos)
```

### Pattern 1: SMA / EMA (TREND-01..04) — causais por construção
```python
# Source: pandas 3.0 docs (Series.rolling / Series.ewm)
sma = close.rolling(window=n, min_periods=n).mean()        # NaN até n bars (degradação)
ema = close.ewm(span=n, adjust=False).mean()               # vista alternativa (D-03)
# sinais discretos SEMPRE sobre SMA (D-03):
posicao = "acima" if close.iloc[-1] > sma200.iloc[-1] else "abaixo"   # se sma200 não-NaN
diff = (sma50 - sma200)
cross_hoje = np.sign(diff.iloc[-1]) != np.sign(diff.iloc[-2])
cruzamento = "golden_cross" if (cross_hoje and diff.iloc[-1] > 0) else \
             "death_cross"  if (cross_hoje and diff.iloc[-1] < 0) else "nenhum"
```
**When to use:** sempre; ambas as séries (SMA e EMA) são computadas em toda chamada.

### Pattern 2: RSI(14) Wilder — SMA-seeded (MOM-01, TEST-03) — VERIFICADO
```python
# Source: Wilder, "New Concepts in Technical Trading Systems"; bate StockCharts/TradingView
def _wilder_rma(s: pd.Series, length: int) -> pd.Series:
    """RMA de Wilder: seed = SMA dos primeiros `length`, depois recursivo (alpha=1/length)."""
    arr = s.to_numpy(dtype=float)
    out = np.full(len(arr), np.nan)
    if len(arr) < length:
        return pd.Series(out, index=s.index)
    out[length - 1] = arr[:length].mean()        # SEED = SMA (não o 1º valor!)
    a = 1.0 / length
    for i in range(length, len(arr)):
        out[i] = a * arr[i] + (1 - a) * out[i - 1]
    return pd.Series(out, index=s.index)

def rsi_wilder(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = _wilder_rma(gain.iloc[1:], length)   # diff descarta o 1º
    avg_loss = _wilder_rma(loss.iloc[1:], length)
    rs = avg_gain / avg_loss
    return (100 - 100 / (1 + rs)).reindex(close.index)
```
**Verificação (runtime, esta sessão):** no dataset canônico de Wilder, os 6 primeiros RSI válidos = `[70.5328, 66.3186, 66.5498, 69.4063, 66.3552, 57.9749]`. O primeiro valor **70.53** é o número de referência publicado (StockCharts/Wikipedia/TradingView). `[VERIFIED: .venv/bin/python runtime]`

### Pattern 3: ADX(14) Wilder — dupla suavização (FORCE-01, TEST-03) — VERIFICADO
```python
# Source: Wilder DMI/ADX; cadeia completa
# 1. True Range, +DM, -DM (por barra)
#    up = High[i]-High[i-1]; dn = Low[i-1]-Low[i]
#    +DM = up if (up>dn and up>0) else 0 ; -DM = dn if (dn>up and dn>0) else 0
#    TR  = max(H-L, |H-C_prev|, |L-C_prev|)
# 2. Suaviza TR, +DM, -DM com Wilder (seed na posição 1 → 1º válido no índice `length`)
# 3. +DI = 100*sm(+DM)/ATR ; -DI = 100*sm(-DM)/ATR
# 4. DX  = 100*|+DI - -DI| / (+DI + -DI)
# 5. ADX = Wilder-smooth(DX)  ← SEGUNDA suavização; SEED no PRIMEIRO DX válido (índice `length`),
#                               NÃO na posição 0 do array (senão a SMA-seed pega NaN → tudo NaN)
```
**Subtlety crítica (a armadilha do ADX):** o helper `_wilder_rma` aplicado ao DX precisa seedar a partir do **primeiro DX não-NaN** (índice `length`), não da posição 0. Use uma variante `_wilder_rma_from(arr, length, start)`. Primeiro ADX válido aparece no índice **2·length−1 = 27** para length=14. Confirmei em runtime: com seed errado o ADX sai **todo NaN**; com seed em `start=length` os valores aparecem corretamente e o no-repaint é exato. `[VERIFIED: .venv/bin/python runtime]`

### Pattern 4: Bollinger squeeze por percentil rolling (CHAN-03, D-02) — VERIFICADO causal
```python
# Source: verificado nesta sessão (causalidade)
ma = close.rolling(n, min_periods=n).mean()
sd = close.rolling(n, min_periods=n).std(ddof=0)      # ddof=0 = população (padrão TradingView/StockCharts)
banda_sup, banda_inf = ma + k*sd, ma - k*sd
largura = (banda_sup - banda_inf) / ma                # normalizada pelo nível de preço
# percentil TRAILING da própria largura (causal: só usa a janela até a barra atual)
pct = largura.rolling(squeeze_janela, min_periods=squeeze_janela).apply(
    lambda x: (x <= x[-1]).mean() * 100.0, raw=True)  # raw=True → x é ndarray, x[-1] é a barra atual
squeeze = "squeeze_on" if pct.iloc[-1] <= squeeze_percentil else "squeeze_off"  # se pct não-NaN
```
**Edge do lookback:** os primeiros `squeeze_janela` bars (~126) têm percentil NaN → sinal `"indisponivel"`. Confirmado: primeiro valor válido no índice 125 (0-based) para janela 126. `[VERIFIED: .venv/bin/python runtime]`

### Pattern 5: Regressão linear trailing (FORCE-02, D-04) — VERIFICADO
```python
# Source: scipy.stats.linregress (esta sessão)
from scipy import stats
def regressao_trailing(close: pd.Series, win: int = 90):
    y = close.to_numpy(float); n = len(y)
    slope_ann = np.full(n, np.nan); r2 = np.full(n, np.nan)
    x = np.arange(win)
    for i in range(win - 1, n):
        seg = y[i - win + 1 : i + 1]                 # janela TRAILING (causal)
        res = stats.linregress(x, seg)
        slope_ann[i] = res.slope * 252 / seg.mean() * 100   # %/ano normalizado pelo preço
        r2[i] = res.rvalue ** 2                              # qualidade do ajuste
    return slope_ann, r2
```
**Por que %/ano e não ângulo:** ângulo em graus depende da escala do eixo (R$/pixel); slope normalizado pela média do preço × 252 pregões é robusto a escala e comparável entre tickers (D-04). `[VERIFIED: scipy 1.17.1]`

### Pattern 6: Donchian breakout causal (CHAN-01)
```python
# canal dos n bars ANTERIORES (shift(1) evita usar a barra atual no próprio canal → no-repaint)
donchian_hi = high.rolling(n, min_periods=n).max().shift(1)
donchian_lo = low.rolling(n, min_periods=n).min().shift(1)
rompeu_alta  = close.iloc[-1] > donchian_hi.iloc[-1]   # nova máxima
perdeu_minima = close.iloc[-1] < donchian_lo.iloc[-1]  # perda da mínima (gatilho de reverificação, Phase 6)
```
**Nota:** sem `.shift(1)` a máxima dos últimos n inclui a barra atual, e o "rompimento" nunca dispara (close ≤ max que contém o próprio close). O `.shift(1)` define o canal pelo passado — causal e semântica correta de breakout.

### Anti-Patterns to Avoid
- **`ewm` sem seed por SMA para RSI/ADX:** diverge do TradingView (50.75 vs 70.53 no 1º valor). Sempre seedar com a SMA dos primeiros `length`. `[VERIFIED]`
- **Seedar a 2ª suavização do ADX na posição 0:** produz ADX todo-NaN. Seedar no primeiro DX válido.
- **Donchian/rolling max sem `.shift(1)`:** o breakout vaza a barra atual no canal.
- **`std(ddof=1)` no Bollinger:** TradingView/StockCharts usam desvio populacional (`ddof=0`); ddof=1 desloca as bandas.
- **MACD com Wilder:** MACD usa **EMA padrão** (`ewm(span=, adjust=False)`), NÃO Wilder. Só RSI e ADX são Wilder.
- **`min_periods` menor que a janela:** gera valores "parciais" no início que não batem com TradingView e quebram a degradação graciosa (DATA-03). Use `min_periods=window`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OLS slope + R² | Normal equations à mão | `scipy.stats.linregress` | Devolve slope, intercept, rvalue (R²=rvalue²), p-value num call `[VERIFIED]` |
| Média móvel / desvio | Loop manual | `Series.rolling(n).mean()/.std(ddof=0)` | Vetorizado, NaN-aware, causal |
| EMA padrão (MACD) | Loop recursivo | `Series.ewm(span=n, adjust=False).mean()` | Equivale à EMA clássica; `adjust=False` = forma recursiva |
| Percentil rolling causal | Ordenação manual | `rolling(w).apply(lambda x: (x<=x[-1]).mean()*100, raw=True)` | Causal, conciso, verificado |
| Indicadores em geral | `ta`/`pandas-ta`/`TA-Lib` | numpy/pandas hand-roll | **Locked:** incompatíveis com numpy 2.4.6/pandas 3.0.3; viola custo zero |

**Key insight:** O único pedaço que **deve** ser hand-rolled é a **suavização de Wilder** — não existe primitiva pandas pronta que seede por SMA (o `ewm` cru não seeda). Todo o resto (rolling, ewm padrão, linregress) é primitiva de biblioteca. Resista à tentação de hand-roll média/desvio/EMA.

## Runtime State Inventory

> Não é fase de rename/refactor/migração — é greenfield aditivo (novo módulo puro). Seção incluída por completude.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — engine é pura, opera sobre frame em memória (`ohlc_ajustado`) | nenhuma |
| Live service config | None — sem serviços externos; sem rede (verificado: `indicators.py` não importa yfinance/requests) | nenhuma |
| OS-registered state | None — sem tasks/daemons | nenhuma |
| Secrets/env vars | None — sem segredos; dados locais | nenhuma |
| Build artifacts | `config.yaml` ganha seção `indicadores:`; nenhum egg-info/binário afetado (projeto instalado via `pythonpath=["src"]`, não build) | adicionar seção em config.yaml |

## Common Pitfalls

### Pitfall 1: Wilder sem seed por SMA (RSI/ADX divergem do TradingView)
**What goes wrong:** `gain.ewm(alpha=1/14, adjust=False).mean()` parece "Wilder" mas seeda no **primeiro valor**, não na SMA. No dataset canônico isso dá RSI 50.75 em vez de 70.53.
**Why it happens:** a fórmula de Wilder (RMA) inicia com a média simples dos primeiros `length` períodos; `ewm` cru não tem essa semente.
**How to avoid:** helper `_wilder_rma` com `out[length-1] = arr[:length].mean()` e recursão depois. `[VERIFIED]`
**Warning signs:** golden RSI quase batendo mas com erro grande nos primeiros ~30 bars; convergindo só lá adiante.

### Pitfall 2: ADX — segunda suavização seedada na posição 0 (tudo NaN)
**What goes wrong:** aplicar `_wilder_rma(dx, 14)` direto faz a SMA-seed `dx[:14].mean()` pegar 14 NaNs → ADX inteiro NaN.
**Why it happens:** DX só fica válido a partir do índice 14 (após a 1ª suavização); a 2ª suavização precisa seedar lá.
**How to avoid:** `_wilder_rma_from(dx, 14, start=14)`. Primeiro ADX válido no índice 27. `[VERIFIED]`
**Warning signs:** `adx.dropna()` vazio; ou primeiro ADX aparecendo cedo demais (índice < 27).

### Pitfall 3: Vazamento de futuro (no-repaint, TEST-04)
**What goes wrong:** indicadores centrados/sem `shift`, ou percentil sobre a série inteira, fazem `ind(s[:k])[-1] != ind(s)[k-1]`.
**Why it happens:** rolling window que inclui a barra-alvo no próprio cálculo de canal, ou `apply` sobre a janela toda.
**How to avoid:** Donchian com `.shift(1)`; percentil/regressão sobre **janela trailing**; nunca usar `center=True`. Verifiquei RSI e ADX exatos para vários k. `[VERIFIED]`
**Warning signs:** o harness de no-repaint falha em k intermediários; sinais "mudam o passado" ao adicionar barras novas.

### Pitfall 4: Histórico curto (degradação graciosa, DATA-03)
**What goes wrong:** MM200 com <200 bars, squeeze com <126 bars, regressão com <90 bars → exceções ou números espúrios.
**Why it happens:** janelas maiores que o histórico disponível.
**How to avoid:** `min_periods=window` (gera NaN, não erro); sinais discretos devolvem `"indisponivel"` quando a série de base está NaN na ponta. Espelha o padrão GRAF-03/DATA-03 da Phase 4.
**Warning signs:** `IndexError` ao acessar `iloc[-2]` num cross com <2 valores válidos.

### Pitfall 5: Split-adjusted vs nominal (TEST-05)
**What goes wrong:** alimentar a engine com `ohlc` nominal gera cruzamentos/rompimentos espúrios na data do split.
**Why it happens:** o nominal tem degrau de preço no split; SMA/Donchian/cross disparam falso.
**How to avoid:** `calcular` consome **sempre** `ohlc_ajustado` (a Phase 4 já entrega contínuo). O teste reusa a fixture ITSA4 de `test_ingest_ohlc.py` (5 splits) e verifica ausência de cross/breakout nas datas de evento.
**Warning signs:** golden/death cross ou breakout exatamente na data de split numa série que deveria ser contínua.

## Code Examples

### Suavização de Wilder reutilizável (RSI e ADX)
```python
# Source: verificado nesta sessão; ver Pattern 2/3
def _wilder_rma_from(arr: np.ndarray, length: int, start: int = 0) -> np.ndarray:
    out = np.full(len(arr), np.nan)
    if start + length > len(arr):
        return out
    out[start + length - 1] = arr[start:start + length].mean()
    a = 1.0 / length
    for i in range(start + length, len(arr)):
        out[i] = a * arr[i] + (1 - a) * out[i - 1]
    return out
```

### MACD 12/26/9 (EMA padrão — NÃO Wilder)
```python
# Source: definição clássica MACD; EMA via ewm(adjust=False)
ema_rapida = close.ewm(span=12, adjust=False).mean()
ema_lenta  = close.ewm(span=26, adjust=False).mean()
macd  = ema_rapida - ema_lenta
sinal = macd.ewm(span=9, adjust=False).mean()
hist  = macd - sinal
d = (macd - sinal)
cross = np.sign(d.iloc[-1]) != np.sign(d.iloc[-2])
cruzamento_macd = "cruz_alta" if (cross and d.iloc[-1] > 0) else \
                  "cruz_baixa" if (cross and d.iloc[-1] < 0) else "nenhum"
```

### Dataclass `SinaisTecnicos` (espelhando ResultadoDDM)
```python
# Source: padrão de src/analista/core/ddm.py (ResultadoDDM)
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

@dataclass
class Tendencia:
    sma20: pd.Series; sma50: pd.Series; sma200: pd.Series
    ema20: pd.Series; ema50: pd.Series; ema200: pd.Series
    posicao_mm200: str          # "acima" | "abaixo" | "indisponivel"
    cruzamento: str             # "golden_cross" | "death_cross" | "nenhum" | "indisponivel"

@dataclass
class Canais:
    donchian_sup: pd.Series; donchian_inf: pd.Series   # 20 (e 55, se duas janelas)
    bb_sup: pd.Series; bb_med: pd.Series; bb_inf: pd.Series
    largura_bb: pd.Series; squeeze_pct: pd.Series
    rompimento_donchian: str    # "nova_maxima" | "perda_minima" | "nenhum" | "indisponivel"
    toque_bollinger: str        # "banda_superior" | "banda_inferior" | "nenhum" | "indisponivel"
    squeeze: str                # "squeeze_on" | "squeeze_off" | "indisponivel"

@dataclass
class Forca:
    adx: pd.Series; pdi: pd.Series; ndi: pd.Series
    regressao_slope_ann: pd.Series; regressao_r2: pd.Series
    forca_adx: str              # "sem_tendencia" | "forte" | "neutro" | "indisponivel"

@dataclass
class Momentum:
    rsi: pd.Series
    macd: pd.Series; macd_sinal: pd.Series; macd_hist: pd.Series
    nivel_rsi: str              # "sobrecomprado" | "sobrevendido" | "neutro" | "indisponivel"
    cruzamento_macd: str        # "cruz_alta" | "cruz_baixa" | "nenhum" | "indisponivel"

@dataclass
class SinaisTecnicos:
    tendencia: Tendencia
    canais: Canais
    forca: Forca
    momentum: Momentum
```
(Os nomes exatos são discrição do Claude per CONTEXT; o que está locked é "agrupado por família, séries + sinais discretos em chaves estáveis/neutras".)

### Nova seção de config (config.yaml)
```yaml
# --- v1.2: indicadores técnicos (consultivos) — parâmetros canônicos ---
indicadores:
  sma_emas: [20, 50, 200]
  donchian: [20, 55]
  bollinger:
    janela: 20
    sigma: 2.0
  squeeze_janela: 126        # ~6 meses
  squeeze_percentil: 20
  adx_janela: 14             # Wilder
  rsi_janela: 14             # Wilder
  rsi_faixas: [30, 70]
  macd: [12, 26, 9]
  regressao_janela: 90       # ~1 trimestre
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pandas-ta` / `TA-Lib` para indicadores | Hand-roll numpy/pandas | pandas 2.0+/numpy 2.0+ quebraram a compat | Forçado a hand-roll (já locked) |
| `Series.append` / `df.append` | `pd.concat` | pandas 2.0 removeu `.append` | Não usar `.append` em helpers |
| `pd.Series.rolling(...).apply(func)` sem `raw` | `raw=True` quando possível | perf — `raw=True` passa ndarray | Use `raw=True` no percentil do squeeze |

**Deprecated/outdated:**
- `ta` / `pandas-ta` / `TA-Lib`: não instalam contra pandas 3.0.3 / numpy 2.4.6 — descartados por decisão travada.
- `DataFrame.append`: removido no pandas 2.0; usar `pd.concat`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | TradingView `ta.rsi`/`ta.adx` batem com a fixture canônica de Wilder (SMA-seed) — usada como âncora do golden | Pattern 2/3, Validation | BAIXO — o RSI 70.53 é referência pública multi-fonte (StockCharts/Wikipedia); ADX exige confirmação visual no TradingView (passo de validação humana já previsto no STATE) |
| A2 | Bollinger usa `std(ddof=0)` (populacional), como TradingView/StockCharts | Pattern 4 | BAIXO — convenção dominante; se o golden de BB for cross-checado e divergir, trocar para ddof por config |
| A3 | Regressão "anualizada" = slope/dia × 252 ÷ preço médio × 100 | Pattern 5, D-04 | BAIXO — D-04 pede "%/ano normalizado pelo preço"; 252 pregões/ano é a convenção; documentar em docstring |
| A4 | "forte > 25 / sem tendência < 20" do ADX deixa a faixa 20–25 como `"neutro"` | Forca dataclass | NENHUM (cosmético) — FORCE-01 cita os dois cortes; a zona intermediária é escolha de rótulo, ajustável |
| A5 | MACD usa EMA padrão (não Wilder) | Code Examples | NENHUM — definição canônica do MACD; Wilder só em RSI/ADX (locked) |

**Os itens acima são convenções dominantes verificadas, não chutes** — mas A1/A2 dependem de cross-check visual com TradingView no passo de validação (não de pesquisa), conforme o STATE.md já registra ("Phase 5 — cruzar fixture RSI/ADX com TradingView antes de travar o golden").

## Open Questions (RESOLVED)

1. **Donchian: uma ou duas janelas no breakout discreto?**
   - What we know: CHAN-01 pede Donchian 20 **e** 55; ambas as séries são computadas.
   - What's unclear: o sinal discreto de rompimento usa qual janela como primária (provavelmente 20 para breakout, 55 para tendência maior)?
   - RESOLVED: rótulo discreto primário sobre Donchian 20; série de 55 disponível para o plot. Travado na interface do Plan 05-02.

2. **Base temporal do ADX/cross em "perda da MM200":**
   - What we know: TIMING-03/04 (Phase 6) escolhem diário vs semanal; a engine da Phase 5 opera no frame diário entregue.
   - What's unclear: nada para a Phase 5 — a resample semanal é responsabilidade da Phase 6.
   - RESOLVED: `calcular` permanece agnóstica de timeframe (recebe o frame que lhe derem); resample semanal é da Phase 6. Travado no contexto do Plan 05-03.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | toda a engine | ✓ | 3.14.5 (.venv) | — |
| numpy | cálculo vetorizado | ✓ | 2.4.6 | — |
| pandas | séries OHLC | ✓ | 3.0.3 | — |
| scipy | regressão (FORCE-02) | ✓ | 1.17.1 | — |
| pytest | golden tests | ✓ | configurado (pyproject) | — |

**Missing dependencies with no fallback:** Nenhuma — fase é código puro sobre deps já instaladas.
**Missing dependencies with fallback:** Nenhuma.

## Validation Architecture

> Nota: `workflow.nyquist_validation` está **desabilitado** (`false`) em `.planning/config.json`, então `VALIDATION.md` **não é exigido** nesta fase. Esta seção fica como referência de arquitetura de testes — as tarefas de teste concretas vivem nos PLAN.md (Wilder/no-repaint/split).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (config em `pyproject.toml` → `[tool.pytest.ini_options]`, `pythonpath=["src"]`, `testpaths=["tests"]`) |
| Config file | `pyproject.toml` |
| Quick run command | `.venv/bin/python -m pytest tests/test_indicators.py -x -q` |
| Full suite command | `.venv/bin/python -m pytest -q` (mantém os 64 golden de valuation verdes — TEST-07) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MOM-01/TEST-03 | RSI(14) Wilder bate fixture canônica (70.5328…) | golden | `pytest tests/test_indicators.py::test_rsi_wilder_canonico -x` | ❌ Wave 0 |
| FORCE-01/TEST-03 | ADX(14) cadeia Wilder, 1º válido idx 27, valores vs TradingView | golden | `pytest tests/test_indicators.py::test_adx_wilder_referencia -x` | ❌ Wave 0 |
| TEST-04 | No-repaint RSI/ADX/MACD/Donchian: `ind(s[:k])[-1]==ind(s)[k-1]` | property | `pytest tests/test_indicators.py::test_no_repaint -x` | ❌ Wave 0 |
| TEST-05 | Split-adjusted (ITSA4 5 splits) sem cross/breakout espúrios | golden | `pytest tests/test_indicators.py::test_split_sem_cross_espurio -x` | ❌ Wave 0 |
| CHAN-03 | Squeeze percentil causal; `"indisponivel"` antes de 126 bars | golden | `pytest tests/test_indicators.py::test_squeeze_percentil_causal -x` | ❌ Wave 0 |
| FORCE-02 | Regressão %/ano + R² trailing, causal | golden | `pytest tests/test_indicators.py::test_regressao_slope_r2 -x` | ❌ Wave 0 |
| TREND-02/03 | posição×MM200 e golden/death cross sobre SMA | golden | `pytest tests/test_indicators.py::test_sinais_tendencia_sma -x` | ❌ Wave 0 |
| DATA-03 | degradação graciosa (<200/<126/<90 bars → NaN/"indisponivel") | golden | `pytest tests/test_indicators.py::test_historico_curto -x` | ❌ Wave 0 |
| TEST-07 | 64 golden de valuation seguem verdes | invariante | `.venv/bin/python -m pytest -q` | ✅ existe |

### Fixtures de referência (no-network, embutidas)
- **RSI âncora (HIGH):** dataset canônico de Wilder — 33 closes começando em 44.34 … 43.13; primeiro RSI(14) = **70.5328**, seguintes `[66.3186, 66.5498, 69.4063, 66.3552, 57.9749]`. Embutir como lista literal no teste (padrão de `test_ddm.py`). Já verificado nesta sessão.
- **ADX referência:** série OHLC sintética determinística (`np.linspace` + ruído seedado) — capturar os valores esperados **do TradingView** num passo de validação humana e congelar como literais. Travar também a invariante estrutural (1º ADX no índice 2·length−1).
- **Split (TEST-05):** reusar `_hist_itsa4_multisplit()` de `tests/test_ingest_ohlc.py` (5 eventos) → passar o `ohlc_ajustado` à engine e asseverar ausência de cross/breakout nas 5 datas.

### Sampling Rate
- **Per task commit:** `.venv/bin/python -m pytest tests/test_indicators.py -x -q`
- **Per wave merge:** `.venv/bin/python -m pytest -q` (inclui os 64 de valuation — TEST-07)
- **Phase gate:** suíte cheia verde antes de `/gsd-verify-work`; cross-check visual RSI/ADX no TradingView feito (checkpoint humano do STATE.md).

### Wave 0 Gaps
- [ ] `tests/test_indicators.py` — cobre TREND/CHAN/FORCE/MOM + TEST-03/04/05 + DATA-03
- [ ] Helper de no-repaint reutilizável (loop sobre k) dentro do teste
- [ ] Captura dos valores ADX de referência no TradingView (validação humana, não pesquisa)
- [ ] Framework install: nenhum — pytest já configurado

## Security Domain

> `security_enforcement` ausente = habilitado. Módulo é matemática pura, local, sem rede/auth/segredos/persistência — a maioria das categorias ASVS não se aplica.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | sem auth |
| V3 Session Management | no | sem sessão |
| V4 Access Control | no | sem controle de acesso |
| V5 Input Validation | yes (leve) | a engine valida bordas: `ohlc` None/vazio → degradação graciosa (não exceção); colunas OHLC ausentes tratadas; per CLAUDE.md "validação só em bordas" |
| V6 Cryptography | no | sem cripto |

### Known Threat Patterns for {Python numérico local}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Frame OHLC malformado/vazio/curto causa crash da aba | Denial of Service (local) | `min_periods`/checagem de None → NaN/`"indisponivel"`, espelhando GRAF-03/DATA-03 |
| NaN/inf propagando para a UI | Tampering (corrupção de exibição) | normalizar divisões por zero (`+DI/-DI`, RS) com `np.errstate`/guarda; testar histórico curto |

(Sem superfície de rede, deserialização, injeção ou segredos nesta fase.)

## Sources

### Primary (HIGH confidence)
- `.venv/bin/python` runtime (esta sessão) — versões (numpy 2.4.6 / pandas 3.0.3 / scipy 1.17.1 / Py 3.14.5); RSI Wilder = 70.5328 no dataset canônico; ADX seeding (1º válido idx 27); no-repaint exato RSI/ADX; squeeze percentil causal (1º válido idx 125); regressão linregress slope+R².
- `src/analista/core/ddm.py`, `src/analista/core/fundamentals.py`, `src/analista/ingest/prices.py` — padrões de dataclass puro, `CompanyData.ohlc_ajustado`, `_ajustar_por_split`.
- `tests/test_ddm.py`, `tests/test_ingest_ohlc.py` — padrão de golden test offline + fixtures (incl. ITSA4 multi-split reutilizável).
- `pyproject.toml`, `config.yaml`, `src/analista/cli.py` — infra de pytest e shape do `cfg` (dict YAML aninhado).

### Secondary (MEDIUM confidence)
- Dataset canônico de Wilder ("New Concepts in Technical Trading Systems") — primeiro RSI(14)=70.53, replicado por StockCharts/Wikipedia/TradingView (conhecimento de treino, corroborado pelo cálculo runtime).

### Tertiary (LOW confidence)
- Valores numéricos exatos do ADX no TradingView para a série sintética — **a confirmar** no checkpoint humano (não pesquisável offline).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versões verificadas no `.venv`; decisão de não-deps locked.
- Architecture/contrato: HIGH — espelha `ddm.py` lido diretamente; D-01..D-04 explícitos.
- Matemática (Wilder/no-repaint/squeeze/regressão): HIGH — verificada em runtime.
- Valores ADX de referência: MEDIUM — implementação verificada, mas o número-âncora vem do TradingView (validação humana).

**Research date:** 2026-06-26
**Valid until:** 2026-07-26 (estável; deps travadas, sem ecossistema em movimento)
