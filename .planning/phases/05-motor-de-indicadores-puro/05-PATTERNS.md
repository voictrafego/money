# Phase 5: Motor de indicadores puro - Pattern Map

**Mapped:** 2026-06-26
**Files analyzed:** 3 (2 new, 1 modified)
**Analogs found:** 3 / 3 (exact analogs for all)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/core/indicators.py` (NEW) | core / pure-calc module | transform (OHLC frame -> SinaisTecnicos) | `src/analista/core/ddm.py` | exact (dataclass + funcoes puras + entry-point) |
| `tests/test_indicators.py` (NEW) | test | golden (offline, fixtures literais) | `tests/test_ddm.py` + `tests/test_ingest_ohlc.py` | exact (asserts numericos + fixture ITSA4 reusavel) |
| `config.yaml` (MODIFIED) | config | declarative params | `config.yaml` secao `ddm:` / `capm:` | exact (mesma estrutura de secao aninhada comentada) |

Secondary analogs studied: `src/analista/core/multiples.py`, `src/analista/core/growth.py` (mesmo padrao de funcao pura `Number = Optional[float]` + guarda de borda), `src/analista/core/fundamentals.py` (shape do input `CompanyData.ohlc_ajustado`).

---

## Pattern Assignments

### `src/analista/core/indicators.py` (core, transform)

**Analog:** `src/analista/core/ddm.py` (espelho direto: dataclass + funcoes puras + entry-point `Optional`).

#### Module-header docstring pattern (ddm.py lines 1-16)
Todo modulo de `core/` abre com docstring que (1) nomeia o conceito, (2) da a formula, (3) cita uma referencia canonica de conferencia. Para indicators.py: cite Wilder + o valor-ancora RSI=70.5328 (paralelo ao "Itau Cap.17 Tabela 41" do ddm).
```python
"""Modelo de Desconto de Dividendos (MDD) - Cap. 13, 15 e 17 do livro.

Valor intrinseco = VP do somatorio dos dividendos do periodo explicito + VP do valor residual.
    ...
Conferencia (Itau, Cap. 17, Tabela 41): DPA_2020 = 2,362; g = 10,24%; n = 10; ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

Number = Optional[float]
```
**Copy exactly:** `from __future__ import annotations` no topo, o alias `Number = Optional[float]` (usado em ddm/multiples/growth), imports de `dataclasses`/`typing`. indicators.py adiciona `import numpy as np`, `import pandas as pd`, `from scipy import stats` (ja no env, ver RESEARCH Standard Stack).

#### Dataclass pattern + derived field (ddm.py lines 21-34) - base do `SinaisTecnicos`
```python
@dataclass
class ResultadoDDM:
    valor_intrinseco: float
    vp_dividendos: float
    vp_residual: float
    valor_residual_futuro: float
    dividendos_projetados: List[float]
    vp_por_ano: List[float]
    peso_residual: float = field(init=False)        # <- campo DERIVADO

    def __post_init__(self) -> None:
        self.peso_residual = (
            self.vp_residual / self.valor_intrinseco if self.valor_intrinseco else 0.0
        )
```

**How `SinaisTecnicos` mirrors `ResultadoDDM`:**
- **Mesmo decorador `@dataclass` simples (NAO `frozen=True`).** `ResultadoDDM` nao e frozen: usa `__post_init__` mutavel para preencher `peso_residual` via `field(init=False)`. House style = dataclass mutavel com derivacoes em `__post_init__`, nao frozen. Espelhe isso: se algum sinal discreto for derivado das series (ex.: `posicao_mm200` a partir de `sma200`/`close`), compute-o em `__post_init__` com `field(init=False)` - exatamente o idiom de `peso_residual`. (Alternativa valida: derivar tudo nas funcoes `_familia` e passar pronto ao construtor; ambas sao house-consistent. So NAO use `frozen=True` - diverge do analog.)
- **Campos diretos sem `Optional` default quando sempre presentes** (como `valor_intrinseco: float`). Series sao sempre `pd.Series` (podem conter NaN, mas o campo existe) -> tipar `pd.Series`, nao `Optional[pd.Series]`.
- **Series e sinais discretos coexistem no mesmo dataclass** - em `ResultadoDDM` convivem listas (`dividendos_projetados`) e escalares (`peso_residual`). O mesmo: `SinaisTecnicos` carrega `pd.Series` (plot Phase 7) + `str` (sinal discreto). D-01 so exige agrupamento por familia -> use os 4 sub-dataclasses (`Tendencia`/`Canais`/`Forca`/`Momentum`) propostos no RESEARCH (lines 329-371), cada um com o mesmo padrao `ResultadoDDM` (series + strings discretas), e o `SinaisTecnicos` raiz agrega os 4.
- **Naming:** snake_case, sem prefixo hungaro, nomes do dominio em PT (`peso_residual`, `vp_dividendos`). Para indicators: `sma200`, `posicao_mm200`, `golden_cross`/`death_cross` - chaves discretas estaveis e neutras (D-01).

#### Entry-point pattern: `Optional[Resultado]` com guarda de borda (ddm.py lines 78-115)
```python
def ddm_dois_estagios(...) -> Optional[ResultadoDDM]:
    if ke is None or g_estavel is None or ke - g_estavel <= 0:
        return None                  # <- guarda de borda no topo
    if dpa_inicial is None or n <= 0:
        return None
    ...
    return ResultadoDDM(
        valor_intrinseco=vp_dividendos + vp_residual,
        ...
    )
```
**Adapt for `calcular(ohlc, cfg) -> SinaisTecnicos`:** a funcao canonica e o paralelo de `ddm_dois_estagios`. Diferenca de degradacao: ddm devolve `None` quando inviavel; o RESEARCH (Pitfall 4 / DATA-03) define que indicators NAO levanta excecao nem devolve `None` no caso de historico curto - devolve series com **NaN inicial** (`min_periods=window`) e sinais discretos `"indisponivel"`. Mantenha a guarda de borda no topo (`ohlc` None/vazio -> degradacao graciosa, nao excecao; ver Security V5 do RESEARCH e CLAUDE.md "validacao so em bordas").

#### Funcoes puras por sub-calculo (ddm.py: `valor_gordon`, `projetar_dividendos`; multiples.py: helper `_safe_div`)
multiples.py linha 16-21 mostra o helper privado de borda - espelha o `_wilder_rma` / `_wilder_rma_from` do RESEARCH:
```python
def _safe_div(num: float, den: float) -> Number:
    if den is None or num is None:
        return None
    if den == 0:
        return None
    return num / den
```
**Copy idiom:** helpers privados com prefixo `_` (`_wilder_rma_from`, `_tendencia`, `_canais`, `_forca`, `_momentum`), cada um puro e sem rede. RESEARCH lock: as funcoes de familia sao puras (D-01 discricionario: uma por familia). Use secoes com comentario-regua como em multiples.py:
```python
# --------------------------------------------------------------------------- #
# 10.1 Multiplos de lucros
# --------------------------------------------------------------------------- #
```
-> replicar como `# --- Tendencia (TREND-01..04) ---`, etc.

#### Input shape (fundamentals.py lines 45-47)
```python
serie_precos: Optional["pd.Series"] = None  # close diario 5a (indice = datas) p/ o grafico
ohlc: Optional["pd.DataFrame"] = None           # frame OHLCV nominal 5a (Yahoo cru)
ohlc_ajustado: Optional["pd.DataFrame"] = None  # OHLCV split-only-adjusted p/ indicadores (Phase 5)
```
`calcular` consome **`ohlc_ajustado`** (split-adjusted, locked CR-01). Colunas do frame (confirmado em `tests/test_ingest_ohlc.py` linha 42-46): `"Open"`, `"High"`, `"Low"`, `"Close"`, `"Volume"` (+ `"Adj Close"`/`"Stock Splits"`/`"Dividends"` que indicators IGNORA). Indice = `pd.DatetimeIndex`. Acesse via `ohlc["Close"]`, `ohlc["High"]`, etc. (capitalizadas).

---

### `tests/test_indicators.py` (test, golden)

**Analog:** `tests/test_ddm.py` (import idiom + asserts numericos) + `tests/test_ingest_ohlc.py` (fixtures OHLC literais + reuso ITSA4).

#### Exact import/test idiom to match house style (test_ddm.py lines 1-9)
```python
"""Valida o DDM e o CAPM contra o caso Itau do livro (Cap. 16 e 17)."""

import pytest

from analista.core import capm
from analista.core import ddm
from analista.core import growth
```
**Copy exactly for test_indicators.py:**
```python
"""Trava a matematica dos indicadores (Wilder vs TradingView, no-repaint, split ITSA4)."""

import numpy as np
import pandas as pd
import pytest

from analista.core import indicators
```
- Docstring de uma linha nomeando o que o arquivo trava (paralelo ao "Valida o DDM e o CAPM...").
- Import absoluto `from analista.core import indicators` (NAO `from analista.core.indicators import ...`) - `pythonpath=["src"]` no pyproject resolve. Chamadas qualificadas: `indicators.calcular(...)`, `indicators.rsi_wilder(...)`.
- `import numpy as np` / `import pandas as pd` adicionados (nao estao em test_ddm.py porque DDM e escalar; indicators opera sobre series - seguir test_ingest_ohlc.py linhas 8-10 que ja importa os tres).

#### Numeric-assert pattern (test_ddm.py lines 34-48)
```python
def test_ddm_itau_crescimento_constante():
    # Cap. 17, Tabela 41 (...): DPA_2020 = 2,362; g = 10,24%; ...
    res = ddm.ddm_dois_estagios(dpa_inicial=2.362, g_alto=0.1024, n=10, g_estavel=0.025, ke=0.1248)
    assert res is not None
    assert abs(res.dividendos_projetados[-1] - 5.68) < 0.05
    assert abs(res.vp_dividendos - 19.23) < 0.15
    assert abs(res.valor_intrinseco - 37.22) < 0.20
```
**Copy idiom:** (1) comentario no topo do teste citando a fonte canonica + os numeros esperados; (2) `assert abs(valor - esperado) < tol` para escalares. Para o golden RSI use o valor-ancora embutido como literal: `assert abs(rsi.dropna().iloc[0] - 70.5328) < 1e-3` e a lista seguinte `[66.3186, 66.5498, 69.4063, 66.3552, 57.9749]` (RESEARCH line 467). Para **series**, use `np.testing.assert_allclose` (ja house style em test_ingest_ohlc.py, ver abaixo) em vez do `abs(...) < tol` escalar.

#### Helper `aprox` opcional (test_multiples.py lines 9-10)
```python
def aprox(a, b, tol=0.01):
    return a is not None and abs(a - b) <= tol
```
test_multiples.py define um helper local de tolerancia. Para indicators prefira `np.testing.assert_allclose` (series) e `pytest.approx` (escalares) - ambos citados no RESEARCH como house style do golden offline.

#### Fixture OHLC sintetica literal (test_ingest_ohlc.py lines 19-46)
O padrao de fixture e uma funcao `_hist_*()` que constroi um `pd.DataFrame` OHLCV deterministico com indice `pd.date_range` e colunas literais. Replicar para a serie ancora de Wilder (33 closes literais) e para a serie ADX sintetica (`np.linspace` + ruido seedado, RESEARCH line 468).

#### Reuso exato da fixture ITSA4 para TEST-05 (test_ingest_ohlc.py lines 214-262)
A fixture `_hist_itsa4_multisplit()` (5 splits) e a constante `_ITSA4_EVENTOS` (linha 204) ja existem. Idiom de consumo no teste de split:
```python
hist, A = _hist_itsa4_multisplit()
aj = prices._ajustar_por_split(hist)
...
np.testing.assert_allclose(aj["Close"].values, A.values, rtol=1e-9)
```
**Para TEST-05:** importe/replique `_hist_itsa4_multisplit` + `_ITSA4_EVENTOS`, gere `aj = prices._ajustar_por_split(hist)`, passe `aj` (o frame split-adjusted) a `indicators.calcular(aj, cfg)` e assevere ausencia de golden/death cross e de breakout Donchian nas 5 datas de `_ITSA4_EVENTOS`. Como `_hist_itsa4_multisplit` esta em `tests/test_ingest_ohlc.py`, importe-a (`from tests.test_ingest_ohlc import _hist_itsa4_multisplit, _ITSA4_EVENTOS`) ou copie a fixture para o novo arquivo - o planner decide; reuso por import evita drift. Note o uso de `np.testing.assert_allclose(..., rtol=...)` como assert canonico de serie (linha 261/271).

---

### `config.yaml` (config, declarative) - nova secao `indicadores:`

**Analog:** secoes `ddm:` (lines 61-68) e `capm:` (lines 50-59) do proprio `config.yaml`.

**Structure pattern** (config.yaml lines 61-68):
```yaml
# --- Cap. 14/15/17: crescimento e DDM ---
ddm:
  n_anos_explicito: 10        # estagio de alto crescimento (livro: 5 a 10)
  g_estavel: 0.025            # crescimento na perpetuidade <= PIB (Focus/BCB ~2,5%)
  tributacao_dividendos: 0.0  # toggle: imposto sobre dividendos (ex.: 0.15)
  sensibilidade:
    delta_ke: [-0.02, -0.01, 0.0, 0.01, 0.02]
    delta_g: [-0.01, -0.005, 0.0, 0.005, 0.01]
```
**Copy idiom for `indicadores:`:**
- Header-comment `# --- <ref> : <titulo> ---` (aqui sem capitulo de livro - usar `# --- v1.2: indicadores tecnicos (consultivos) - parametros canonicos ---`).
- Comentario inline em cada chave explicando origem/convencao (paralelo a `# crescimento na perpetuidade <= PIB`). Marque Wilder e janelas: `adx_janela: 14  # Wilder`, `squeeze_janela: 126  # ~6 meses`.
- Sub-mapeamentos aninhados quando ha grupo (como `sensibilidade:`) -> ex.: `bollinger: {janela: 20, sigma: 2.0}`.
- Listas inline para conjuntos de parametros (como `delta_ke: [...]`) -> `sma_emas: [20, 50, 200]`, `macd: [12, 26, 9]`.

Secao proposta (RESEARCH lines 375-390), defaults canonicos:
```yaml
# --- v1.2: indicadores tecnicos (consultivos) - parametros canonicos ---
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
`cfg` e carregado como dict YAML aninhado; indicators le `cfg["indicadores"][...]` (mesmo acesso que ddm faz a `cfg["ddm"]`).

---

## Shared Patterns

### Pure-module house style
**Source:** `src/analista/core/ddm.py`, `multiples.py`, `growth.py`
**Apply to:** `indicators.py`
- `from __future__ import annotations` no topo.
- `Number = Optional[float]` alias para escalares que podem ser indefinidos.
- Funcoes puras, sem rede, sem I/O; helpers privados com prefixo `_`.
- Guarda de borda no topo de cada funcao publica (`if x is None or ...: return None` para escalares; para series -> `min_periods=window` gera NaN, sinal discreto `"indisponivel"`).
- Comentarios so onde o "porque" nao e obvio (CLAUDE.md) - cite Wilder/no-repaint nas docstrings.

### Golden-test house style
**Source:** `tests/test_ddm.py`, `tests/test_multiples.py`, `tests/test_ingest_ohlc.py`
**Apply to:** `tests/test_indicators.py`
- Docstring de uma linha por arquivo.
- `import pytest` + `from analista.core import <modulo>` (import qualificado, NAO from-import de funcoes).
- Comentario no topo de cada teste citando a fonte/valor esperado.
- Escalar: `assert abs(x - esperado) < tol` ou `pytest.approx`. Serie: `np.testing.assert_allclose(...)`.
- Fixtures deterministicas embutidas (literais ou `np.linspace`/seed), zero rede.
- Reusar `_hist_itsa4_multisplit()` + `_ITSA4_EVENTOS` de `test_ingest_ohlc.py` para TEST-05.

### Config house style
**Source:** `config.yaml` (secoes `ddm:`, `capm:`, `screening:`)
**Apply to:** nova secao `indicadores:`
- Header-comment `# --- ... ---` antes da secao.
- Comentario inline justificando cada parametro (origem/convencao).
- Aninhamento para grupos; listas inline para vetores de parametros.

### Input contract
**Source:** `src/analista/core/fundamentals.py` (CompanyData.ohlc_ajustado), `src/analista/ingest/prices.py` (_ajustar_por_split)
**Apply to:** `indicators.calcular(ohlc, cfg)`
- Recebe `pd.DataFrame` com colunas capitalizadas `Open/High/Low/Close/Volume`, indice `DatetimeIndex`.
- SEMPRE consome `ohlc_ajustado` (split-adjusted), nunca `ohlc` nominal (locked CR-01 / TEST-05).

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| - | - | - | Todos os 3 arquivos tem analog exato no codebase. |

Sub-padrao sem analog direto no projeto: a **suavizacao de Wilder seedada por SMA** (`_wilder_rma_from`) nao existe em nenhum modulo atual - e o unico pedaco genuinamente novo (RESEARCH "Don't Hand-Roll" / Pattern 2-3). O planner deve copiar o excerpt verificado do RESEARCH (lines 304-312), nao buscar analog no codebase. Demais calculos (SMA/EMA/BB/Donchian/MACD/regressao) usam primitivas pandas/scipy - tambem sem analog interno, vem dos Patterns 1/4/5/6 do RESEARCH.

## Metadata

**Analog search scope:** `src/analista/core/` (ddm, multiples, growth, fundamentals), `tests/` (test_ddm, test_multiples, test_ingest_ohlc), `config.yaml`.
**Files scanned:** 8.
**Pattern extraction date:** 2026-06-26
