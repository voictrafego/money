---
phase: 13-piv-s-contexto-de-tend-ncia-e-n-veis
reviewed: 2026-06-29T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/analista/core/indicators.py
  - config.yaml
  - tests/test_indicators.py
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: resolved
---

# Phase 13: Code Review Report

**Reviewed:** 2026-06-29
**Depth:** standard (Python, foco em no-repaint/causalidade)
**Files Reviewed:** 3
**Status:** issues_found

## Summary

A implementação é, no geral, sólida e disciplinada: o contrato `SinaisTecnicos` é estendido de
forma 100% aditiva (todos os campos novos com default `None`/`field(default_factory=list)`), o
firewall é respeitado (`indicators.py` importa apenas numpy/pandas/scipy — não toca `report.py`,
`setup.py` nem `app.py`), o ATR reusa o TR da cadeia do ADX sem recalcular (D-08), o semanal vem
de resample `W-FRI` sem rede (D-04), e o R:R degrada corretamente para `"indisponivel"` sem nunca
propagar infinito (verifiquei o `np.divide`+`np.isfinite`+`risco<=0`).

Porém o concern #1 da fase — **no-repaint / causalidade sobre a barra fechada (`iloc[-2]`)** — está
**parcialmente violado**. O motor de ingestão (`intraday.py`) documenta explicitamente que "a última
barra é SEMPRE tratada como potencialmente viva" e que "cálculos da Fase 13 usam a barra fechada via
`iloc[-2]`". `_volume` e `_niveis_sr` honram isso, mas **`_pivos` confirma o pivô mais recente usando
a barra viva no seu janela à direita** (BLOCKER), e `_dow`/`_contexto` leem o tip da barra viva
(WARNINGs). Como os pivôs são a fundação de S/R, Fibonacci, Dow e `ultimo_topo/fundo`, esse defeito
se propaga por toda a fase quando o motor roda intraday.

Há ainda um bug de unidade: `regressao_trailing` anualiza por 252 (diário) mas é reusada no frame
SEMANAL pelo desempate de Dow, inflando o slope ~4,85×.

## Critical Issues

### CR-01: `_pivos` confirma o pivô mais recente usando a barra VIVA (repaint) — viola a invariante `iloc[-2]` da Fase 13

**File:** `src/analista/core/indicators.py:505-516` (loop em `509`)

**Issue:**
O fractal de Williams varre `for i in range(N, n_bar - N)`, ou seja, o último candidato é
`i = n_bar - 1 - N`, cuja janela à direita termina em `i + N = n_bar - 1` — **a última barra do
frame**. O motor de ingestão (`src/analista/ingest/intraday.py:12-13,121`) declara que a última barra
é SEMPRE tratada como potencialmente viva (`barra_viva = (n >= 1)`) e que os cálculos da Fase 13
devem usar a barra fechada (`iloc[-2]`). Logo o pivô em `n_bar-1-N` é "confirmado" comparando contra
uma barra **não fechada**: se a barra viva mudar de High/Low até fechar, esse pivô pode aparecer ou
sumir → **repaint**.

Não é hipotético no contexto desta fase: `_volume` (`:841-843`) e `_niveis_sr` (`:659`) usam
`iloc[-2]` exatamente porque a última barra é viva. `_pivos` é o único da família de PREÇO que NÃO
respeita essa convenção. E o pivô que repinta é justamente o mais recente — o que alimenta
`ultimo_topo`/`ultimo_fundo`, a âncora do Fibonacci (`_niveis_fib`) e a sequência HH/HL do Dow.

O gate de no-repaint (`test_pivos_no_repaint_truncacao`) **não pega isso**: ele só prova estabilidade
contra barras FUTURAS (truncação), não contra a última barra não-fechada. E `test_pivos_lag_confirmacao`
afirma apenas `iloc[-N:].isna()` (2 barras), codificando o off-by-one.

**Fix:** confirmar somente pivôs cuja janela à direita seja inteiramente de barras FECHADas
(`i + N <= n_bar - 2`), deixando `N+1` barras finais como não-confirmadas:

```python
# Precisa de N vizinhos à esquerda E N FECHADOS à direita (i+N <= n_bar-2, barra viva excluída).
if n_bar >= 2 * N + 2:
    h = high.to_numpy(float)
    l = low.to_numpy(float)
    for i in range(N, n_bar - N - 1):        # antes: range(N, n_bar - N)
        jan_h = h[i - N:i + N + 1]
        if h[i] == jan_h.max() and (jan_h == h[i]).sum() == 1:
            pivot_high.iloc[i] = h[i]
        jan_l = l[i - N:i + N + 1]
        if l[i] == jan_l.min() and (jan_l == l[i]).sum() == 1:
            pivot_low.iloc[i] = l[i]
```

Atualizar `test_pivos_lag_confirmacao` para `iloc[-(N+1):].isna().all()` e adicionar um golden que
prove que o pivô confirmado mais recente NÃO depende da última barra (ex.: mutar `High.iloc[-1]` e
verificar que nenhum pivô confirmado muda). Alternativa equivalente: em `calcular`, rotear as famílias
de PREÇO por `nominal.iloc[:-1]` quando a barra é viva (mas a correção no loop é mais local e mantém o
índice intacto).

## Warnings

### WR-01: `regressao_trailing` anualiza por 252 (diário) mas é reusada no frame SEMANAL → slope inflado ~4,85×

**File:** `src/analista/core/indicators.py:403` (fórmula) consumida em `:568` (`_dow`) via `:883` (`_contexto`)

**Issue:**
`slope_ann[i] = res.slope * 252.0 / media * 100.0` — o fator 252 assume ~252 períodos/ano (barra
DIÁRIA). Mas `_contexto` (`:880-883`) faz `resample("W-FRI")` e chama `_dow(_pivos(semanal), semanal)`,
que no desempate ambíguo chama `regressao_trailing(semanal["Close"], 90)`. Em barras semanais o fator
correto é ~52, não 252 → o `slope_ann` semanal sai **~4,85× inflado**. Como o desempate usa a zona
morta `_DOW_SLOPE_BAND = 5.0` %/ano (`:533`), o efeito é que quase qualquer inclinação semanal vira
"claramente direcional" (alta/baixa) em vez de "lateral", enviesando `alinhamento_mtf`. Não quebra
(só rotula), mas distorce sistematicamente o contexto multi-TF nos casos ambíguos.

**Fix:** tornar a anualização ciente da frequência (passar períodos/ano como parâmetro):

```python
def regressao_trailing(close: pd.Series, win: int = 90, periodos_ano: float = 252.0):
    ...
        slope_ann[i] = res.slope * periodos_ano / media * 100.0 if media != 0 else np.nan
```

e no caminho semanal de `_contexto`/`_dow` passar `periodos_ano=52` (ou derivar do índice). Como
`regressao_trailing` é pública e tem golden próprio (diário), manter o default 252.

### WR-02: `_contexto` inclui a SEMANA PARCIAL corrente no resample → tendência/alinhamento semanal repinta intra-semana

**File:** `src/analista/core/indicators.py:880-883`

**Issue:**
`ohlc.resample("W-FRI").agg({...}).dropna()` agrega a semana corrente com os dias já ocorridos; o
`Close` da última barra semanal é o último close diário (a barra viva). `_dow` sobre o semanal lê
`adx.iloc[-1]`/`slope.iloc[-1]` e os pivôs do tip dessa semana incompleta. À medida que a semana
avança, o último candle semanal muda → o rótulo de Dow semanal (e portanto `alinhamento_mtf`) pode
mudar dia a dia dentro da mesma semana. Mesma classe da CR-01 (uso da barra viva), agora no semanal.
Só modula o score (D-06), mas contraria a invariante `iloc[-2]` declarada para a fase.

**Fix:** descartar a última barra semanal quando a semana ainda não fechou, p.ex. comparar o
`period_end` da última linha semanal com a última data diária e dropá-la se for futura:

```python
semanal = ohlc.resample("W-FRI").agg({...}).dropna()
if len(semanal) and semanal.index[-1].normalize() > ohlc.index[-1].normalize():
    semanal = semanal.iloc[:-1]            # semana corrente ainda aberta → não confirmada
```

### WR-03: desempate de Dow no DIÁRIO lê `adx.iloc[-1]`/`slope.iloc[-1]` (barra viva) em vez da barra fechada

**File:** `src/analista/core/indicators.py:567-577`

**Issue:**
No ramo ambíguo, `_dow` decide por `adx.iloc[-1]` e `slope.iloc[-1]` — o tip = barra viva. Pela
invariante da Fase 13 (`iloc[-2]`), esses sinais deveriam ler a barra fechada. Reconheço que isso
espelha o padrão pré-existente de `_forca` (`forca_adx` também lê `adx.iloc[-1]`, fora do escopo desta
fase), mas `_dow` é código NOVO e deveria seguir a convenção explícita da fase. O efeito é que o
rótulo `dow_diario` pode mudar quando a barra viva fecha, mesmo sem novos pivôs.

**Fix:** ler o penúltimo válido fechado, p.ex. `adx.dropna().iloc[-2]`/`slope.dropna().iloc[-2]`
(com guarda de comprimento ≥ 2), coerente com `_volume`/`_niveis_sr`.

### WR-04: o gate de no-repaint dos pivôs não testa a barra viva (mascarando a CR-01)

**File:** `tests/test_indicators.py:433-465`

**Issue:**
`test_pivos_no_repaint_truncacao` só compara `iloc[:k-N]` entre série truncada e cheia — prova
estabilidade contra barras FUTURAS, que vale por construção (o pivô em `k-1-N` só depende de barras
≤ `k-1`, idênticas nos dois frames). Ele NÃO prova que o pivô confirmado mais recente independe da
ÚLTIMA barra (não-fechada). `test_pivos_lag_confirmacao` afirma só `iloc[-N:].isna()`, codificando o
off-by-one da CR-01. Os goldens passam, mas o defeito real de repaint passa batido.

**Fix:** adicionar um teste que mute `df["High"].iloc[-1]` (e `Low`) para um extremo e verifique que
nenhuma barra com pivô CONFIRMADO mudou de valor; e, após o fix da CR-01, ajustar o lag esperado para
`N+1` barras finais NaN.

## Info

### IN-01: `dow_diario` vem dos pivôs do frame AJUSTADO, mas a âncora de Fibonacci usa pivôs do frame NOMINAL

**File:** `src/analista/core/indicators.py:931-937`

**Issue:**
`calcular` computa `pivos = _pivos(nominal, cfg)` (preço, D-02), enquanto `_contexto(ohlc, cfg)`
recomputa `_pivos(ohlc, cfg)` sobre o split-adjusted para rotular `dow_diario`. `_niveis_fib` então
combina `contexto.dow_diario` (derivado de pivôs ajustados) com `pivos` (nominais) para achar a
âncora. Em papéis com split DENTRO da janela do impulso recente, as posições/contagens de pivôs podem
divergir entre os dois frames, fazendo `_niveis_fib` não encontrar par coerente e **silenciosamente**
zerar os níveis de Fibonacci (degradação para `None`). Sem splits recentes (caso comum) os dois
coincidem. Não quebra, mas pode suprimir níveis sem aviso.

**Fix:** derivar `dow_diario` dos MESMOS pivôs (nominais) usados pela âncora, ou documentar
explicitamente a escolha de base por família.

### IN-02: `_volume` recomputa a Donchian superior em vez de reusar `canais.donchian_sup`

**File:** `src/analista/core/indicators.py:838-839`

**Issue:**
`_volume` recalcula `ohlc["High"].rolling(j_curto).max().shift(1)` em vez de reusar a série já
computada em `_canais` e disponível em `calcular` (`canais.donchian_sup`). Duplicação de lógica:
se um lado mudar de fonte/janela no futuro, os dois podem divergir silenciosamente. Hoje ambos usam
o mesmo `ohlc` split-adjusted e a mesma janela, então o resultado coincide.

**Fix:** passar `canais.donchian_sup` para `_volume` (ou extrair um helper único de Donchian causal).

### IN-03: limiar de cluster S/R usa ATR (escala ajustada) sobre pivôs nominais de escalas mistas entre splits

**File:** `src/analista/core/indicators.py:655-661`

**Issue:**
`_niveis_sr` clusteriza pivôs NOMINAIS de toda a história com `limiar = k × atr_tip`, onde `atr_tip`
é o ATR recente (escala recente). Para papéis com split, os pivôs nominais ANTIGOS estão em escala
diferente dos recentes (é o motivo da própria existência do ajuste), então o limiar único de
proximidade fica calibrado para a escala recente e mal calibrado para os níveis antigos. No tip os
valores coincidem (ajustado≈nominal nas barras recentes), então S/R próximas ao preço estão corretas;
o efeito é só em zonas antigas distantes. É um tradeoff da decisão travada D-02 (níveis sobre o
nominal), não um bug introduzido — registrado para auditabilidade.

**Fix (opcional):** considerar limitar o clustering S/R a pivôs pós-último-split, ou normalizar o
limiar por região de escala.

---

## Resolution

**Resolvido em:** 2026-06-29 — todos os findings Critical + Warning corrigidos. Os 3 Info
(IN-01/02/03) ficam como tradeoffs aceitos da decisão travada D-02 (níveis sobre o nominal),
fora de escopo desta rodada.

Suíte completa verde após os fixes: **252 passed** (baseline 251 + 1 novo golden de no-repaint
da barra viva). Os goldens fundamentalistas (fora de `test_indicators.py`, 185 testes) seguem
inalterados; nenhum arquivo da engine fundamentalista, `app.py`, `report/` foi tocado.

| Finding | Commit | Resumo |
|---------|--------|--------|
| CR-01 + WR-04 | `ffe5ed6` | Pivôs no-repaint: janela à direita só usa barras FECHADAS (`i+N <= n_bar-2`); as N+1 barras finais ficam NaN. Goldens: lag N+1, `lim=k-N-1` na truncação, e novo `test_pivos_no_repaint_barra_viva`. |
| WR-01 | `82fc3d5` | `regressao_trailing` ganha `periodos_ano` (default 252); desempate de Dow semanal passa 52 (corrige slope ~4,85× inflado). |
| WR-02 | `8ffebf5` | `_contexto` descarta a semana parcial corrente (period_end futuro vs último dia) no resample W-FRI. |
| WR-03 | `c606c0e` | Desempate de Dow lê a barra FECHADA (`dropna().iloc[-2]`) com guarda ≥ 2, coerente com `_volume`/`_niveis_sr`. |

**Verificação humana sugerida:** WR-03 e WR-02 mudam a SEMÂNTICA do rótulo (barra fechada vs
viva / semana confirmada) — os goldens cobrem os caminhos, mas vale confirmar o comportamento
no fluxo intraday real.

---

_Reviewed: 2026-06-29_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
