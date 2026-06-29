---
phase: 12-ingest-o-intraday-timeframe
verified: 2026-06-29T15:45:00Z
status: passed
score: 5/5
overrides_applied: 0
re_verification: false
---

# Fase 12: Ingestão Intraday + Timeframe — Relatório de Verificação

**Objetivo da Fase:** Existe uma camada de ingestão que entrega OHLCV de um ticker em múltiplos timeframes (diário + 1h/30m/5m), isolada do pipeline diário e do cache fundamentalista, em base nominal correta e com refresh targetado.
**Verificado em:** 2026-06-29T15:45:00Z
**Status:** APROVADO
**Re-verificação:** Não — verificação inicial

---

## Conquista do Objetivo

### Verdades Observáveis

| #  | Verdade | Status | Evidência |
|----|---------|--------|-----------|
| 1  | `coletar_intraday(ticker, timeframe)` retorna `FrameOHLC` para diário/1h/30m/5m via `_PERIODO_POR_TF`, isolada de `coletar_mercado`/`montar_empresa`, nunca levanta exceção (todas as arestas → `FrameOHLC` com `motivo` categorizado) | VERIFICADO | `intraday.py` l.32-37: tabela `_PERIODO_POR_TF` cravada. Sem import de `build`/`montar_empresa`/`coletar_mercado`. `test_tf_invalido`, `test_vazio_sem_dados`, `test_excecao_fetch_falhou` todos verdes. |
| 2  | Timestamps normalizados para `America/Sao_Paulo` de forma idempotente; engine offline (sem import `streamlit`); reusa `prices._ajustar_por_split` sem nova chamada de rede; `auto_adjust=False` | VERIFICADO | `intraday.py` l.61-73: `_normaliza_tz` trata índice naive (UTC→SP) e tz-aware (`tz_convert`). `grep 'import streamlit' = 0`. L.106: `prices._ajustar_por_split(hist)` reusado. L.91: `auto_adjust=False`. |
| 3  | Barra viva clock-free (`idx_ultima_fechada=len-2`); `ohlc` nominal e `ohlc_ajustado` ambos presentes; `atraso_min` injetável | VERIFICADO | L.111: `idx_fechada = n - 2 if n >= 2 else None`. L.121: `barra_viva=(n >= 1)`. L.77: `agora: Optional["pd.Timestamp"] = None` (injetável). L.118-119: `ohlc=hist, ohlc_ajustado=ohlc_aj`. `test_idx_ultima_fechada_clock_free` e `test_atraso_min_injetavel` verdes. |
| 4  | `app.py` expõe `frame_intraday` com `@st.cache_data(ttl=300)` chamando `intraday.coletar_intraday`; `_nonce_key` por par; ZERO `st.cache_data.clear()` em qualquer lugar | VERIFICADO | `app.py` l.53-69: `@st.cache_data(show_spinner=False, ttl=300)` + `def frame_intraday(ticker, timeframe, nonce)` + `return intraday.coletar_intraday(ticker, timeframe)` + `def _nonce_key`. `grep -v comment \| grep cache_data.clear = 0`. |
| 5  | Suíte completa verde: 202 passados (191 golden + 11 novos); sem regressão | VERIFICADO | `pytest -q`: **202 passed in 1.79s**. `pytest tests/test_ingest_intraday.py -v`: 11/11 passados. |

**Pontuação:** 5/5 verdades verificadas

---

## Artefatos Obrigatórios

| Artefato | Esperado | Status | Detalhes |
|----------|----------|--------|----------|
| `src/analista/ingest/intraday.py` | Engine `coletar_intraday` + `FrameOHLC` + `_PERIODO_POR_TF` + `_normaliza_tz` + categorias de motivo | VERIFICADO | 126 linhas (mín. 70 exigido). Contém `def coletar_intraday`, `class FrameOHLC`, `_PERIODO_POR_TF`, `_normaliza_tz`, constantes `MOTIVO_*`. |
| `tests/test_ingest_intraday.py` | 11 testes offline cobrindo todas as arestas | VERIFICADO | 213 linhas (mín. 80 exigido). Contém `def test_idx_ultima_fechada_clock_free` e `def test_tz_normaliza_naive`. Monkeypatch `_yf` presente. Fixture de barra viva (`Volume=0`) presente. |
| `app.py` | `frame_intraday` (wrapper `@st.cache_data ttl=300`) + `_nonce_key` | VERIFICADO | `def frame_intraday` (l.54), `def _nonce_key` (l.66), `ttl=300` (l.53), `intraday.coletar_intraday(` (l.63). Sintaxe válida (`py_compile` retorna 0). |

---

## Verificação de Ligações-Chave (Wiring)

| De | Para | Via | Status | Detalhes |
|----|------|-----|--------|----------|
| `intraday.py` | `prices._ajustar_por_split` | reuso de função pura split-only (sem rede) | LIGADO | `intraday.py` l.106: `ohlc_aj = prices._ajustar_por_split(hist)` |
| `intraday.py` | `prices.yahoo_symbol` + `prices._yf` + `prices._MAX_TENTATIVAS` | resolução `.SA` + retry yfinance reaproveitados | LIGADO | L.84: `prices.yahoo_symbol(ticker)`, l.85: `prices._yf()`, l.89/96: `prices._MAX_TENTATIVAS`, l.97: `prices._BACKOFF_SEG`. Chamadas verificadas em execução. |
| `app.py frame_intraday` | `intraday.coletar_intraday` | wrapper `@st.cache_data(ttl=300)` com nonce só na chave de cache | LIGADO | L.61-63: import tardio + `return intraday.coletar_intraday(ticker, timeframe)`. `nonce` não é repassado à engine. |
| `app.py` | (firewall) cache da aba Analisar | ausência de `st.cache_data.clear()` | LIGADO | `grep -v '^[[:space:]]*#' app.py \| grep -c 'cache_data\.clear'` = **0**. |

---

## Rastreabilidade de Firewall

| Firewall | Verificação | Resultado |
|----------|-------------|-----------|
| `intraday.py` não importa `streamlit` | `grep -c 'import streamlit' src/analista/ingest/intraday.py` | **0** |
| `intraday.py` não chama `coletar_mercado`/`montar_empresa`/`build` | `grep -n 'import build\|montar_empresa\|coletar_mercado'` | sem ocorrências |
| `app.py` sem `.clear()` global | `grep -v comment \| grep -c 'cache_data\.clear'` | **0** |
| `auto_adjust=False` presente | `grep -c 'auto_adjust=False'` | **1** (l.91) |
| Split-adjust reusado (não reimplementado) | `grep -c 'prices\._ajustar_por_split'` | **1** (l.106) |

---

## Cobertura de Requisitos

| Requisito | Plano | Descrição | Status | Evidência |
|-----------|-------|-----------|--------|-----------|
| DATA-01 | 12-01 | Ingestão OHLCV intraday isolada, `auto_adjust=False` + split-adjust, tz `America/Sao_Paulo`, sem perturbar o fetch diário | SATISFEITO | `_PERIODO_POR_TF` cravado; `_normaliza_tz` idempotente; `prices._ajustar_por_split` reusado; `auto_adjust=False` na l.91; sem import de `build` |
| DATA-02 | 12-01 | Timeframe parametrizado; aviso de atraso; degradação para "indisponível" sem quebrar | SATISFEITO | `atraso_min` injetável; `motivo=MOTIVO_HIST_INSUF` para frame curto; `disponivel=False` para vazio/exceção/tf inválido — todos testados e verdes |
| DATA-03 | 12-02 | Re-busca com cache TTL curto (300s) e invalidação targetada por nonce, sem `.clear()` global | SATISFEITO | `@st.cache_data(ttl=300)` em `frame_intraday`; `nonce` só na chave de cache; zero `cache_data.clear()` em `app.py` |

---

## Anti-Padrões Encontrados

| Arquivo | Linha | Padrão | Severidade | Impacto |
|---------|-------|--------|------------|---------|
| `app.py` | 125 | `placeholder="..."` | Info | Parâmetro de UI do `st.text_input` — uso legítimo da API Streamlit, não é stub de código. Irrelevante. |

Nenhum marcador de dívida técnica (`TBD`, `FIXME`, `XXX`) encontrado nos arquivos da fase.

---

## Verificações Comportamentais Spot-Check

| Comportamento | Comando | Resultado | Status |
|---------------|---------|-----------|--------|
| `coletar_intraday('PETR4','tf_invalido')` retorna `FrameOHLC(disponivel=False)` sem exceção | `python -c "from analista.ingest import intraday; f=intraday.coletar_intraday('PETR4','tf_invalido'); assert f.disponivel is False and f.motivo=='timeframe_invalido'"` | OK | PASSOU |
| `_PERIODO_POR_TF` contém exatamente 4 TFs com valores `[VERIFIED]` | `assert intraday._PERIODO_POR_TF == {'diario':('5y','1d'),'1h':('730d','1h'),'30m':('60d','30m'),'5m':('60d','5m')}` | OK | PASSOU |
| `FrameOHLC` tem exatamente os 9 campos do contrato | `dataclasses.fields` verifica `timeframe, ohlc, ohlc_ajustado, ultima_barra_ts, barra_viva, idx_ultima_fechada, atraso_min, disponivel, motivo` | OK | PASSOU |
| `app.py` compila sem erro de sintaxe | `python -m py_compile app.py` | exit 0 | PASSOU |
| Suíte completa verde | `pytest -q` | **202 passed in 1.79s** | PASSOU |

---

## Commits Verificados

| Commit | Descrição | Status |
|--------|-----------|--------|
| `d61377b` | feat(12-01): engine de ingestão intraday (`coletar_intraday` + `FrameOHLC`) | ENCONTRADO em `git log` |
| `e94f789` | test(12-01): suíte offline da ingestão intraday (11 testes) | ENCONTRADO em `git log` |
| `34e08cc` | feat(12-02): wrapper de cache intraday `frame_intraday` + helper `_nonce_key` | ENCONTRADO em `git log` |

---

## Resumo dos Gaps

Nenhum gap. Todas as 5 verdades verificadas, todos os 3 artefatos substantivos e ligados, todos os 3 requisitos satisfeitos, sem anti-padrões bloqueadores, sem marcadores de dívida não rastreados.

A fase 12 atingiu integralmente seu objetivo.

---

_Verificado: 2026-06-29T15:45:00Z_
_Verificador: Claude (gsd-verifier)_
