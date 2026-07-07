# Phase 12: Ingestão Intraday + Timeframe - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-29
**Phase:** 12-Ingestão Intraday + Timeframe
**Areas discussed:** Contrato de retorno, Barra viva, Profundidade do histórico, Falha / dados vazios

---

## Contrato de retorno — forma da entrega

| Option | Description | Selected |
|--------|-------------|----------|
| Dataclass rico | `FrameOHLC(ohlc, timeframe, ultima_barra_ts, barra_viva, idx_ultima_fechada, atraso_min, disponivel, motivo)`; espelha DadosMercado/SinaisTecnicos; mantém app.py thin | ✓ |
| DataFrame OHLC puro | Retorna só o DataFrame; joga derivação de metadados pra Fases 13/16 (risco de duplicação) | |
| Você decide | Planner escolhe a forma | |

**User's choice:** Dataclass rico
**Notes:** A Fase 16 precisa de timestamp/atraso pro selo e a 13 precisa do índice da barra fechada — metadados pertencem ao contrato.

## Contrato de retorno — séries carregadas

| Option | Description | Selected |
|--------|-------------|----------|
| Ambas: nominal + split-adj | Espelha o diário; gráfico/níveis usam nominal, indicadores usam split-adjusted; contrato uniforme | ✓ |
| Só split-adjusted | Mais simples (split raro em janela curta), mas quebra a base nominal do critério #2 se houver split | |
| Você decide | Planner decide | |

**User's choice:** Ambas: nominal + split-adj
**Notes:** Cumpre o critério de aceite #2 (entrada/stop/alvo na mesma base nominal do gráfico).

## Barra viva — política

| Option | Description | Selected |
|--------|-------------|----------|
| Manter + marcar | Frame inclui a barra viva; dataclass expõe barra_viva + idx_ultima_fechada; gráfico desenha "em formação", cálculos em iloc[-2] | ✓ |
| Descartar na ingestão | Camada corta a barra viva; no-repaint trivial mas a Fase 16 perde a barra "do momento" | |
| Você decide | Planner decide | |

**User's choice:** Manter + marcar

## Barra viva — detecção

| Option | Description | Selected |
|--------|-------------|----------|
| Conservador: última sempre suspeita | Trata sempre a última como potencialmente viva; cálculos em iloc[-2]; determinístico, imune a TZ/feriados | ✓ |
| Por relógio + intervalo | Compara ult_ts + intervalo vs now em America/Sao_Paulo; mais preciso mas depende de relógio e calendário B3 | |
| Você decide | Planner decide | |

**User's choice:** Conservador: última sempre suspeita
**Notes:** Robustez/determinismo (VPS em UTC, goldens sem relógio) sobre precisão; aceita "perder" 1 barra fora de pregão.

## Profundidade do histórico

| Option | Description | Selected |
|--------|-------------|----------|
| Máximo disponível por TF | Teto do Yahoo por timeframe (5m/30m≈60d, 1h≈730d, diário 5y); maximiza indicadores e contexto pra pivôs/padrões | ✓ |
| Janela calculada por indicador | Só o necessário pro indicador mais longo; mais leve mas encurta contexto de pivôs/padrões | |
| Você decide | Planner calibra | |

**User's choice:** Máximo disponível por TF
**Notes:** period×interval exato a confirmar empiricamente (limite yfinance MEDIUM no roadmap).

## Falha / dados vazios

| Option | Description | Selected |
|--------|-------------|----------|
| Motivo categorizado | Conjunto fixo de causas (fetch_falhou/sem_dados/historico_insuficiente); Fase 16 mapeia copy; testável | ✓ |
| Mensagem livre | String pronta pra exibir montada na ingestão; mistura copy de UI na camada de dados | |
| Você decide | Planner define | |

**User's choice:** Motivo categorizado
**Notes:** Borda nunca retorna None/exceção (espelha guard de calcular()); disponivel=False + motivo.

---

## Claude's Discretion

- Nomes de módulo/dataclass/campos e localização do arquivo (novo `ingest/intraday.py` vs. extensão de `ingest/prices.py`).
- `period × interval` concreto por timeframe.
- Forma de expor as categorias de `motivo` (Enum vs. constantes) e escopo exato do nonce de cache.

## Deferred Ideas

None — discussion stayed within phase scope.
