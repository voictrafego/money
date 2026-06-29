# Phase 13: Pivôs, Contexto de Tendência e Níveis - Pattern Map

**Mapped:** 2026-06-29
**Files analyzed:** 5 (3 source/config modified + 2 test groups)
**Analogs found:** 5 / 5 — all in-repo (no RESEARCH.md; defaults from método per D-02)

> **Constraint reminder (CLAUDE.md + STATE.md):** custo zero (no new deps), os **191 goldens devem continuar verdes** (toda mudança é ADITIVA ao `SinaisTecnicos`), **no-repaint causal obrigatório** (`.shift(1)` idiom + truncation test as gate), degradação graciosa para `"indisponivel"` (nunca exceção, nunca inf/div-zero). "Exibe, nunca recomenda" — copy é da Fase 16, NÃO desta fase.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/core/indicators.py` (MODIFY — novos dataclasses + funções de pivô/tendência/níveis/volume; estender `SinaisTecnicos` aditivamente) | engine/transform | batch / transform (Series→discrete labels) | self (família `_canais`/`_forca` existentes) | exact |
| `config.yaml` (MODIFY — novos params `indicadores.*`: N pivô, m ATR, k cluster, donchian S/R, janela volume) | config | static config | bloco `indicadores:` existente (linhas 96-114) | exact |
| `tests/test_indicators.py` (MODIFY/ADD — novos goldens: no-repaint pivô, S/R zona, stop/RR, volume) | test | batch | self (estrutura golden existente) | exact |
| (resample semanal W-FRI para TREND-02) — provável dentro de `indicators.py` ou helper consumido por `report.py` | engine/transform | transform | `report.py` linhas 253-255 | exact |
| (consumo do `FrameOHLC`) — entrada de dados | ingest (read-only) | request-response | `intraday.coletar_intraday` | exact (já existe; não modificar) |

**Discretion (D, CONTEXT §Claude's Discretion):** nomes exatos dos dataclasses/campos novos e organização interna ficam a critério do planner, desde que **aditivos** (default `None`/`"indisponivel"`) — espelhar exatamente como `donchian_sup_55`/`close` foram adicionados como campos opcionais ao final dos dataclasses (linhas 59-60, 91).

---

## Pattern Assignments

### `src/analista/core/indicators.py` — novos dataclasses (pivôs, tendência, níveis, volume)

**Analog:** `Canais` / `Forca` dataclasses + campos aditivos `donchian_sup_55`, `close` (mesmo arquivo).

**Aditividade de contrato** (lines 45-61, 83-91) — TODO campo novo entra como opcional com default, NUNCA reordena/remove existentes (é o que mantém os 191 goldens verdes):
```python
@dataclass
class Canais:
    donchian_sup: pd.Series
    # ... campos travados ...
    rompimento_donchian: str
    # Aditivas (default None) para não quebrar o contrato travado no plan 05-01.
    donchian_sup_55: pd.Series = None
    donchian_inf_55: pd.Series = None

@dataclass
class SinaisTecnicos:
    tendencia: Tendencia
    canais: Canais
    forca: Forca
    momentum: Momentum
    # Aditiva (default None) p/ não quebrar o contrato do plan 05-01.
    close: pd.Series = None
```
> Para pivôs/tendência/níveis/volume: ou novos dataclasses-família (ex.: `Pivos`, `Niveis`, `Volume`) referenciados por novos campos opcionais em `SinaisTecnicos`, ou campos opcionais diretos. Ambos são aditivos. Rótulos discretos devem usar o vocabulário estável existente: strings minúsculas, `"indisponivel"` para degradação (ver lines 41, 54-56, 70, 79-80).

**Convenção de string-labels** (lines 41-42, 54-56): chaves estáveis/neutras, NUNCA copy em linguagem natural.
```python
posicao_mm200: str          # "acima" | "abaixo" | "indisponivel"
rompimento_donchian: str    # "nova_maxima" | "perda_minima" | "nenhum" | "indisponivel"
```
Aplicar a: rótulo de Dow (`"alta"|"baixa"|"lateral"|"indisponivel"`), alinhamento (`"alinhado_alta"|"alinhado_baixa"|"conflito"|"indisponivel"`), R:R (string formatada ou `"indisponivel"`), flag volume (booleana — VOL-01).

---

### Pivôs fractal de Williams (PIVOT-01) — função causal no-repaint

**Analog (causalidade):** `_canais` Donchian `.shift(1)` (lines 198-211) — o padrão de "canal só olha o passado".

**O idioma causal `.shift(1)`** (lines 198-202) — base direta para D-10 (Donchian já entra como faixa S/R externa) e referência conceitual para o fractal:
```python
j_curto, j_longo = ind["donchian"]                 # [20, 55] — 20 é o canal primário
donchian_sup = high.rolling(j_curto, min_periods=j_curto).max().shift(1)
donchian_inf = low.rolling(j_curto, min_periods=j_curto).min().shift(1)
donchian_sup_55 = high.rolling(j_longo, min_periods=j_longo).max().shift(1)
donchian_inf_55 = low.rolling(j_longo, min_periods=j_longo).min().shift(1)
```
**Docstring explicando o porquê da causalidade** (lines 188-193) — replicar esse nível de justificativa para o fractal (por que `t+N` confirma e não repaint):
```python
"""... Todo o canal é CAUSAL: o Donchian usa `.shift(1)` — o canal é definido só pelas
barras PASSADAS. Sem o shift, o max/min dos últimos n inclui o próprio close e o
rompimento nunca dispara ..."""
```
> **Fractal de Williams (D-01):** topo em `t` = `High[t]` estritamente maior que os `N` Highs de cada lado; só confirmado quando `t+N` fecha; os `N` candidatos mais recentes ficam "não confirmados" (D-03). NÃO usar `scipy.signal.find_peaks` (prominence pode repaint). O `scipy` já está importado (line 25, `from scipy import stats`) mas NÃO é o caminho aqui.

---

### Contexto de tendência diário + Dow (TREND-01, D-05) — reuso de ADX/SMA

**Analog (leitura de rótulo já classificado):** `_forca` (lines 330-353) e `report.py` decision tree (lines 261-274).

**Reuso de `adx_wilder` + threshold de força** (lines 336-347) — D-05 manda reusar, NÃO reimplementar ADX/SMA para desempate de Dow:
```python
ind = cfg["indicadores"]
adx, pdi, ndi = adx_wilder(ohlc, ind["adx_janela"])
slope, r2 = regressao_trailing(ohlc["Close"], ind["regressao_janela"])
if len(adx.dropna()) == 0 or pd.isna(adx.iloc[-1]):
    forca_adx = "indisponivel"
elif adx.iloc[-1] < 20.0:
    forca_adx = "sem_tendencia"
elif adx.iloc[-1] > 25.0:
    forca_adx = "forte"
else:
    forca_adx = "neutro"
```
**Padrão de "ler o rótulo já classificado, não relê o float"** (`report.py` lines 261-262) — o classificador de Dow deve consumir os rótulos/MMs existentes para desempate ambíguo→`"lateral"`:
```python
pos = a.sinais.tendencia.posicao_mm200
forca = a.sinais.forca.forca_adx
```

---

### Alinhamento semanal→diário (TREND-02, D-04) — resample W-FRI

**Analog:** `report.py` lines 253-255 (resample W-FRI JÁ existe e é golden-coberto em `tests/test_report.py::test_resample_semanal_w_fri`).

**O resample exato** (line 253-255) — reusar este idioma; D-04 proíbe buscar `1wk` do Yahoo:
```python
ohlc = ohlc.resample("W-FRI").agg(
    {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
).dropna()
```
**Guard antes do resample** (lines 246-252) — só roda em DatetimeIndex com colunas OHLC, senão cai no frame original e a degradação de `calcular` cuida:
```python
if (
    base == "semanal"
    and ohlc is not None
    and len(ohlc) > 0
    and isinstance(ohlc.index, pd.DatetimeIndex)
    and set(indicators._COLUNAS_OHLC).issubset(ohlc.columns)
):
```
> **D-04:** semanal = resample W-FRI do `ohlc_ajustado` (5y ≈ 260 barras semanais). Alinhamento rotula `alinhado_alta`/`alinhado_baixa`/`conflito`; **conflito penaliza/modula o score, NUNCA bloqueia** (D-06).

---

### Níveis: stop ATR×m (D-08) — ATR a partir do TR já calculado

**Analog:** `adx_wilder` (lines 269-285) — o True Range já é computado lá.

**TR/ATR já existem na cadeia do ADX** (lines 276-285) — D-08 manda **expor**, NÃO recalcular:
```python
prev_close = close.shift(1)
tr = pd.concat([
    (high - low),
    (high - prev_close).abs(),
    (low - prev_close).abs(),
], axis=1).max(axis=1)
# 1ª suavização de Wilder ...
atr = _wilder_rma_from(tr.to_numpy(float), length, start=1)
```
> **Ação para o planner:** `adx_wilder` hoje devolve `(adx, pdi, ndi)` e descarta `atr`/`tr`. Para D-08, expor o ATR de forma **aditiva** — opções (discretion): (a) helper novo `atr_wilder(ohlc, length)` que reaproveita `_wilder_rma_from(tr, ...)`; ou (b) retorno opcional. Manter a assinatura atual de `adx_wilder` intacta para não tocar `_forca`/goldens. Stop = mais conservador (mais distante) entre swing estrutural e `ATR×m`; `m` em config (default 1,5).

---

### R:R (RR-01, D-09) — degradação graciosa, nunca div-zero

**Analog:** `rsi_wilder` proteção div-zero (lines 172-177) + idioma `np.errstate` em `_canais` (lines 231-232) e `adx_wilder` (lines 289-294).

**Proteção contra divisão por zero / inf** (lines 172-177):
```python
with np.errstate(divide="ignore", invalid="ignore"):
    rs = avg_gain / avg_loss
    rsi = 100.0 - 100.0 / (1.0 + rs)
rsi = np.where((avg_loss == 0) & (avg_gain > 0), 100.0, rsi)
rsi = np.where((avg_loss == 0) & (avg_gain == 0), 50.0, rsi)
```
**`np.errstate` para razão NaN, não inf** (`_canais` lines 231-232):
```python
with np.errstate(divide="ignore", invalid="ignore"):
    largura_bb = (bb_sup - bb_inf) / bb_med.replace(0.0, np.nan)
```
> **D-09:** risco zero/indefinido → R:R degrada para `"indisponivel"` (string), NUNCA infinito/divisão por zero. Formato esperado: `"1 : 2,5"`.

---

### `config.yaml` — novos params

**Analog:** bloco `indicadores:` (lines 96-114).

**Idioma config-driven** (lines 97-114) — listas `[a, b]` ou subchaves; comentário explicando o porquê do default (espelhar densidade dos comentários `squeeze_janela`/`base_temporal`):
```yaml
indicadores:
  sma_emas: [20, 50, 200]
  donchian: [20, 55]
  squeeze_janela: 126        # ~6 meses
  adx_janela: 14             # Wilder
  rsi_faixas: [30, 70]
  macd: [12, 26, 9]
  regressao_janela: 90       # ~1 trimestre
```
Como lido no código (`_canais` line 195-198, `_forca` line 336): `ind = cfg["indicadores"]; j_curto, j_longo = ind["donchian"]`.
> **Novos params (D-02/08/10/11 + discretion):** `pivo_n` (default **2**), `stop_atr_m` (default **1,5**), `cluster_k` (×ATR — default sensato), `donchian_sr` (janela S/R — pode reusar `donchian` 20/55), `volume_janela` (MM volume). Todos com comentário do "porquê". Os goldens carregam o `config.yaml` shipado via `_cfg_ind()` — defaults novos têm que ser coerentes com os asserts.

---

### `tests/test_indicators.py` — novos goldens

**Analog:** mesmo arquivo, suíte existente (lines 1-408).

**Carregamento do config canônico** (lines 15-19) — todo teste pina os params reais do `config.yaml`:
```python
def _cfg_ind() -> dict:
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
```
**Padrão GATE no-repaint / truncation** (line 154-158, 203-206, 251-254) — `ind(s[:k]).iloc[-1] == ind(s)[k-1]`. **Obrigatório** para pivôs (D-03 gate):
```python
# Causal/no-repaint: f(serie[:k]).iloc[-1] == f(serie)[k-1].
for k in (40, 50):
    ck = indicators._canais(df.iloc[:k], cfg)
    assert ck.donchian_sup.iloc[-1] == pytest.approx(c.donchian_sup.iloc[k - 1], abs=1e-9)
```
**Padrão "teeth" anti-falso-positivo** (lines 160-162, 179-181) — provar que sem a causalidade o sinal NÃO dispararia:
```python
# Sem o .shift(1) o max dos últimos 20 incluiria a própria barra → nunca romperia.
hi20_sem_shift = df["High"].rolling(20, min_periods=20).max()
assert df["Close"].iloc[-1] <= hi20_sem_shift.iloc[-1]
```
**Fixtures OHLC determinísticas** (lines 136-142, 222-233, 299-308) — `np.linspace`/`np.random.default_rng(seed)` + `pd.date_range(freq="B")`, colunas capitalizadas `High`/`Low`/`Close`:
```python
def _frame_ohlc(close, high=None, low=None, start="2021-01-01"):
    close = np.asarray(close, dtype=float)
    high = close + 0.5 if high is None else np.asarray(high, dtype=float)
    low = close - 0.5 if low is None else np.asarray(low, dtype=float)
    idx = pd.date_range(start, periods=len(close), freq="B")
    return pd.DataFrame({"High": high, "Low": low, "Close": close}, index=idx)
```
**Teste de degradação graciosa** (lines 209-218, 323-339) — frame curto/None → todos os novos rótulos `"indisponivel"`, sem exceção.
> Para volume os goldens precisam de coluna `Volume` na fixture (ver `test_ingest_intraday._frame_5min` lines 26-32 como referência de OHLCV com Volume).

---

## Shared Patterns

### Degradação graciosa para "indisponivel"
**Source:** `indicators.py` — `_tendencia` (lines 132-135), `_canais` (lines 204-211), `_forca` (lines 340-347), entry guard `calcular` (lines 415-416).
**Apply to:** TODOS os novos rótulos discretos (pivô, Dow, alinhamento, S/R, stop, R:R, volume).
```python
if len(close) == 0 or pd.isna(serie.iloc[-1]):
    rotulo = "indisponivel"
elif <condição>:
    rotulo = "<estado>"
else:
    rotulo = "nenhum"
```
Entry-point guard (lines 415-416) — None/vazio/sem-colunas vira frame vazio e roteia, NUNCA exceção:
```python
if ohlc is None or len(ohlc) == 0 or not set(_COLUNAS_OHLC).issubset(ohlc.columns):
    ohlc = pd.DataFrame({c: pd.Series(dtype=float) for c in _COLUNAS_OHLC})
```

### Config-driven
**Source:** `indicators.py` lines 124, 195-198, 336, 362-363.
**Apply to:** todas as janelas/limiares novos.
```python
ind = cfg["indicadores"]
j_curto, j_longo = ind["donchian"]
```

### min_periods=janela → NaN (não valor parcial)
**Source:** `_tendencia` lines 125-127, `_canais` lines 199-200, 215-216.
**Apply to:** toda rolling-window nova (volume MM, etc.) — garante NaN com histórico curto, alimentando a degradação.
```python
sma200 = close.rolling(j200, min_periods=j200).mean()
```

### Frame nominal vs ajustado (D-02 herdado da Fase 12)
**Source:** CONTEXT §code_context / `report.py` line 242, `intraday.FrameOHLC` lines 51-52.
**Apply to:** níveis de PREÇO (entrada/stop/alvo/S-R) usam `.ohlc` **nominal**; indicadores/cálculos usam `.ohlc_ajustado`.

### Ponto de entrada único `calcular(ohlc, cfg)`
**Source:** `indicators.py` lines 406-425.
**Apply to:** as novas famílias devem ser populadas DENTRO de `calcular` (como `_tendencia`/`_canais`/`_forca`/`_momentum`), mantendo o construtor do `SinaisTecnicos` como o único ponto de montagem.
```python
return SinaisTecnicos(
    tendencia=_tendencia(close, cfg),
    canais=_canais(ohlc, cfg),
    forca=_forca(ohlc, cfg),
    momentum=_momentum(close, cfg),
    close=close,
)
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (nenhum) | — | — | Toda a matemática nova tem analog direto no mesmo módulo. O **fractal de Williams** em si não existe no codebase, mas seu padrão de causalidade no-repaint é coberto pelo idioma `.shift(1)` do Donchian + gate de truncation. Defaults vêm do método (D-02), não de RESEARCH.md. |

## Metadata

**Analog search scope:** `src/analista/core/indicators.py`, `src/analista/ingest/intraday.py`, `src/analista/ingest/prices.py`, `src/analista/report/report.py`, `tests/test_indicators.py`, `tests/test_ingest_intraday.py`, `tests/test_report.py`, `config.yaml`.
**Files scanned:** 8
**Pattern extraction date:** 2026-06-29
