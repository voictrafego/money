---
phase: 05-motor-de-indicadores-puro
verified: 2026-06-26T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 5: Motor de Indicadores Puro — Verification Report

**Phase Goal:** Um módulo puro `core/indicators.py` calcula as 4 famílias de indicadores a partir do OHLC e devolve séries prontas para plotar + sinais discretos, com a matemática correta travada por golden tests antes de qualquer integração com a UI.
**Verified:** 2026-06-26
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `indicators.calcular(ohlc, cfg)` devolve SinaisTecnicos cobrindo as 4 famílias (TREND-01..04, CHAN-01..03, FORCE-01..02, MOM-01..02) | VERIFIED | Runtime confirma tipo SinaisTecnicos com .tendencia/.canais/.forca/.momentum populados; todos os sinais discretos não-"indisponivel" em histórico longo; `test_calcular_completo` verde |
| 2 | RSI e ADX usam suavização de Wilder (seed SMA) e batem com fixtures TradingView (TEST-03) | VERIFIED | Runtime: RSI(14) = 70.5328 (tolerância 1e-3); ADX primeiro válido no índice 27 (= 2×14-1); literais ADX congelados em `test_adx_wilder_referencia` (checkpoint humano aprovado, commit `5d330a8`) |
| 3 | Nenhum sinal usa dados futuros (TEST-04 no-repaint) | VERIFIED | Runtime: `rsi(s[:k])[-1] == rsi(s)[k-1]` e `adx(s[:k])[-1] == adx(s)[k-1]` para k=60,120,200,300 — diferença < 1e-9 em todos os casos; Donchian usa `.shift(1)`; squeeze usa `raw=True` (trailing) |
| 4 | Série split-adjusted ITSA4 (5 splits) não gera cruzamentos/rompimentos espúrios (TEST-05) | VERIFIED | `test_split_sem_cross_espurio` passa; contraste com série nominal confirma teeth (nominal dispara perda_minima espúria nos splits) |
| 5 | Zero novas dependências (só numpy/pandas/scipy); parâmetros canônicos em config; golden tests verdes (TEST-07) | VERIFIED | scipy já estava em requirements.txt antes desta fase; `grep -Eq 'yfinance|requests|pandas_ta|talib' indicators.py` retorna não-zero; `config.yaml` tem seção `indicadores:` com todos os params canônicos; 92 testes passam (15 do indicadores + 77 de valuation/ingest anteriores) |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/indicators.py` | Módulo puro com SinaisTecnicos + 4 famílias + helpers | VERIFIED | 422 linhas; dataclasses Tendencia/Canais/Forca/Momentum/SinaisTecnicos; funções `_wilder_rma_from`, `_tendencia`, `rsi_wilder`, `_canais`, `adx_wilder`, `regressao_trailing`, `_forca`, `_momentum`, `calcular`; sem frozen=True; sem imports externos (yfinance/ta/etc.) |
| `tests/test_indicators.py` | 15 golden tests cobrindo RSI anchor, tendência, MACD, canais, ADX, regressão, calcular, split | VERIFIED | 380 linhas; 15 testes todos verdes: `test_rsi_wilder_canonico`, `test_sinais_tendencia_sma`, `test_historico_curto_tendencia`, `test_macd_cross`, `test_no_repaint_momentum`, `test_donchian_breakout_causal`, `test_bollinger_touch`, `test_squeeze_percentil_causal`, `test_canais_historico_curto`, `test_adx_wilder_estrutural`, `test_adx_wilder_referencia`, `test_regressao_slope_r2`, `test_calcular_completo`, `test_calcular_degrada`, `test_split_sem_cross_espurio` |
| `config.yaml` | Seção `indicadores:` com parâmetros canônicos | VERIFIED | Seção presente com: `sma_emas: [20,50,200]`, `donchian: [20,55]`, `bollinger: {janela:20, sigma:2.0}`, `squeeze_janela: 126`, `squeeze_percentil: 20`, `adx_janela: 14`, `rsi_janela: 14`, `rsi_faixas: [30,70]`, `macd: [12,26,9]`, `regressao_janela: 90` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `rsi_wilder` | `_wilder_rma_from` | SMA-seeded Wilder (alpha=1/length, seed=SMA dos primeiros length) | WIRED | `rsi_wilder` chama `_wilder_rma_from(gain.iloc[1:].to_numpy(float), length)` e idem para loss |
| `_tendencia` sinais discretos | `sma50`, `sma200` (não EMA) | golden/death cross e posicao_mm200 sobre SMA (D-03) | WIRED | `diff = (sma50 - sma200).dropna()` — EMA só composta para séries de plot, nunca para sinais |
| `adx_wilder` 2ª suavização | `_wilder_rma_from(..., start=length)` | seed no primeiro DX válido | WIRED | `adx_arr = _wilder_rma_from(dx, length, start=length)` — confirma que start=length posiciona o 1º ADX no índice 27 |
| `indicators.calcular` | `_tendencia`, `_canais`, `_forca`, `_momentum` | monta SinaisTecnicos a partir das 4 funções de família | WIRED | `return SinaisTecnicos(tendencia=_tendencia(...), canais=_canais(...), forca=_forca(...), momentum=_momentum(...))` |
| `test_split_sem_cross_espurio` | `prices._ajustar_por_split` + fixture ITSA4 | frame split-adjusted → calcular → assert sem cross/perda_minima nas 5 datas de evento | WIRED | importa `_hist_itsa4_multisplit, _ITSA4_EVENTOS` de `tests.test_ingest_ohlc`; executa `prices._ajustar_por_split(hist)` e verifica per-barra |

---

### Data-Flow Trace (Level 4)

Módulo puro: não há estado externo nem busca de rede — todos os dados fluem do argumento `ohlc` (DataFrame in-memory) para as séries de saída via transformações NumPy/Pandas. Nenhum dado hardcoded relevante detectado.

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `calcular()` | SinaisTecnicos | `ohlc` arg (OHLCV in-memory) | Sim — transformações NumPy/Pandas sobre o frame recebido | FLOWING |
| `rsi_wilder` | `rsi` Series | `close.diff()` → `_wilder_rma_from` | Sim — derivado de close real via cadeia Wilder | FLOWING |
| `adx_wilder` | `adx, pdi, ndi` | `high/low/close.diff()` → `_wilder_rma_from` × 2 | Sim — cadeia DMI completa | FLOWING |
| `regressao_trailing` | `slope_ann, r2` | `scipy.stats.linregress` sobre janela trailing | Sim — OLS real por barra | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| RSI(14) Wilder = 70.5328 (âncora canônica) | runtime Python inline | `70.5328` (abs diff < 1e-9) | PASS |
| ADX primeiro válido no índice 27 | runtime Python inline | índice 27 confirmado | PASS |
| `calcular(ohlc, cfg)` retorna SinaisTecnicos com 4 famílias | runtime Python inline | tipos corretos, todos os sinais não-"indisponivel" em histórico longo | PASS |
| `calcular(None, cfg)` degrada sem exceção | runtime Python inline | `posicao_mm200: indisponivel`, `forca_adx: indisponivel` | PASS |
| No-repaint RSI e ADX (k=60,120,200,300) | runtime Python inline | diferença < 1e-9 em todos os k | PASS |
| Suíte completa | `.venv/bin/python -m pytest -q` | 92 passed in 1.37s | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Descrição | Status | Evidence |
|-------------|------------|-----------|--------|----------|
| TREND-01 | 05-01 | SMA 20/50/200 computadas | SATISFIED | `_tendencia`: sma20/sma50/sma200 via rolling |
| TREND-02 | 05-01 | Posição vs MM200 rotulada | SATISFIED | `posicao_mm200` string "acima"/"abaixo"/"indisponivel" |
| TREND-03 | 05-01 | Golden/death cross sinalizado | SATISFIED | `cruzamento` string "golden_cross"/"death_cross"/"nenhum"/"indisponivel" |
| TREND-04 | 05-01 | EMA disponível além da SMA | SATISFIED | ema20/ema50/ema200 também computadas em toda chamada (D-03) |
| CHAN-01 | 05-02 | Donchian 20/55 com rompimentos | SATISFIED | `donchian_sup/inf` (shift(1) causal) + `rompimento_donchian`; donchian_sup_55/inf_55 para overlay |
| CHAN-02 | 05-02 | Bollinger 20/2σ com toque de banda | SATISFIED | `bb_sup/med/inf` (ddof=0) + `toque_bollinger` |
| CHAN-03 | 05-02 | Bollinger squeeze sinalizado | SATISFIED | `squeeze_pct` (rolling percentil causal, raw=True) + `squeeze` |
| FORCE-01 | 05-03 | ADX(14) com leitura de força (engine) | SATISFIED | `adx_wilder()` + `forca_adx` labels (<20/20-25/>25); UI em Phase 7 |
| FORCE-02 | 05-03 | Regressão linear trailing %/ano + R² (engine) | SATISFIED | `regressao_trailing()` via scipy.stats.linregress; UI em Phase 7 |
| MOM-01 | 05-01 | RSI(14) Wilder com faixas 30/70 | SATISFIED | `rsi_wilder()` + `nivel_rsi` |
| MOM-02 | 05-01 | MACD(12/26/9) com cruzamento de sinal | SATISFIED | `_momentum()`: macd/macd_sinal/macd_hist + `cruzamento_macd` |
| TEST-03 | 05-01/05-03 | RSI e ADX travados contra TradingView | SATISFIED | `test_rsi_wilder_canonico` (70.5328) + `test_adx_wilder_referencia` (literais congelados, checkpoint humano aprovado) |
| TEST-04 | 05-01/05-02/05-03 | No-repaint | SATISFIED | `test_no_repaint_momentum`, `test_donchian_breakout_causal` (no-repaint sub-assert), `test_adx_wilder_estrutural` (no-repaint sub-assert), `test_squeeze_percentil_causal` (causal sub-assert) |
| TEST-05 | 05-03 | Split-adjusted sem cross/breakout espúrio (ITSA4) | SATISFIED | `test_split_sem_cross_espurio` passa; contraste com nominal (teeth) confirmado |
| TEST-07 | invariante | 64 golden tests de valuation verdes | SATISFIED | 92 passed total (77 pré-existentes + 15 novos) |

**Nota sobre REQUIREMENTS.md:** O arquivo `.planning/REQUIREMENTS.md` foi atualizado na última vez no commit `1f3eadb` (plan 05-02). Após o plan 05-03 completar, a tabela de rastreabilidade não foi atualizada: TEST-05 ainda aparece como "Pending" e FORCE-01/FORCE-02 como "Pending". TEST-05 está implementado e passa — documentação apenas desatualizada. FORCE-01/02 permanecerão "Pending" até que a Phase 7 construa a UI que exibe esses valores ao usuário, o que é semanticamente correto (o requisito diz "User vê...").

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| Nenhum | — | — | — | Sem TBD/FIXME/XXX/HACK/PLACEHOLDER nos arquivos da fase. Ocorrências de "todo" nos comentários são a palavra portuguesa ("todo o canal"), não marcadores de dívida técnica. |

---

### Human Verification Required

Nenhum item requer verificação humana nesta fase.

O único checkpoint humano desta fase (Task 3 do plan 05-03 — cruzamento do ADX com TradingView) foi resolvido durante a execução: o desenvolvedor aprovou os valores e o executor congelou os literais no commit `5d330a8`. O teste `test_adx_wilder_referencia` passa com os valores aprovados.

---

### Gaps Summary

Nenhuma lacuna encontrada. Todos os 5 critérios de sucesso foram verificados com evidência direta no codebase:

1. `calcular()` retorna SinaisTecnicos completo — confirmado em runtime e por 15 testes passando
2. RSI 70.5328 e ADX índice 27 — confirmados em runtime com precisão > 1e-9
3. No-repaint RSI/MACD/ADX/Donchian/squeeze — confirmados em runtime para múltiplos k
4. ITSA4 split-adjusted sem sinal espúrio — `test_split_sem_cross_espurio` verde com contraste de teeth
5. Zero dependências novas, config completo, 92 testes verdes

---

_Verified: 2026-06-26_
_Verifier: Claude (gsd-verifier)_
