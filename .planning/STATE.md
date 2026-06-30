---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: — Ferramenta de Swing Trade
status: complete
stopped_at: Phase 16 complete — v1.4 entregue
last_updated: "2026-06-30T13:23:01.802Z"
last_activity: 2026-06-30
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 15
  completed_plans: 15
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-29)

**Core value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação. No v1.4, a página de swing **EXIBE** sinais técnicos fiéis a Murphy e **NUNCA recomenda**.
**Current focus:** Phase 16 — p-gina-streamlit-gr-fico-do-momento

## Current Position

Phase: 16 (p-gina-streamlit-gr-fico-do-momento) — COMPLETE
Plan: 3 of 3 (todos completos)
Status: 16-03 aprovado (283 goldens verdes + verificação no navegador via Claude-in-Chrome, sem regressão) — milestone v1.4 entregue
Last activity: 2026-06-30

## Performance Metrics

**Velocity:**

- Total plans completed: 34 (v1.0 + v1.1 + v1.2) + v1.3 (Fases 9–11)
- Average duration: — min
- Total execution time: — hours

**By Phase (concluídas):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | - | - |
| 02 | 2 | - | - |
| 03 | 2 | - | - |
| 04 | 2 | - | - |
| 05 | 3 | - | - |
| 06 | 2 | - | - |
| 08 | 4 | - | - |
| 07 | 5 | - | - |
| 09 | 3 | - | - |
| 10 | 3 | - | - |
| 11 | 2 | - | - |
| 14 | 5 | - | - |
| 15 | 1 | - | - |

**Recent Trend:**

- Last milestone: v1.3 fechado (191 testes verdes; deployado na VPS)
- Trend: —

*Updated after each plan completion*
| Phase 12 P02 | ~4 min | 1 tasks | 1 files |
| Phase 13 P02 | 10min | 2 tasks | 2 files |
| Phase 13 P03 | ~9min | 2 tasks | 3 files |
| Phase 13 P04 | ~11min | 2 tasks | 2 files |
| Phase 14 P01 | ~8min | 2 tasks | 3 files |
| Phase 14 P02 | ~10min | 2 tasks | 2 files |
| Phase 14 P03 | ~12min | 2 tasks | 2 files |
| Phase 14 P04 | ~8min | 2 tasks | 2 files |
| Phase 14 P05 | ~6min | 2 tasks | 0 files |
| Phase 15 P01 | 15 | 2 tasks | 3 files |
| Phase 16 P01 | ~10min | 2 tasks | 1 files |
| Phase 16 P02 | ~8min | 2 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Decisões que governam o v1.4 (ferramenta de swing trade):

- **Swing trade = produto NOVO e separado** (4º menu): não mexe na aba Analisar nem no veredito fundamentalista; o método do livro de dividendos fica intacto e validado.
- **Setup EXIBE, nunca recomenda** (sem "compre/venda"): fronteira regulatória é gate de aceite das fases de score (15) e UI (16); linguagem condicional/de estudo obrigatória.
- **`app.py` read-only** (locked desde a Phase 2): toda lógica de setup vive na engine (`core/setups.py` + `report/setup.py`); a UI só lê campos de `SetupSwing` (espelha o contrato de `AnaliseAcao`).
- **Zero novas dependências de runtime**: tudo sobre `scipy.signal.find_peaks` + `pandas/numpy/yfinance/plotly/streamlit` já instalados; `requirements.txt` inalterado.
- **Pivôs (swing highs/lows) são o primitivo central** (Phase 13): desbloqueiam S/R, stop, Fibonacci, sequência de Dow e padrões. Construir primeiro, no-repaint/causal.
- **Custo-zero mantido**: intraday 1h/30m/5m é best-effort via Yahoo com aviso de atraso (~15min) e histórico limitado (5m/30m≈60d, 1h≈730d); streaming real-time é pago → fora de escopo.
- **Cache intraday isolado**: TTL curto 300s + nonce no botão Atualizar; nunca `st.cache_data.clear()` global (apagaria o cache da aba Analisar).
- **Firewall `report/setup.py` × `report/report.py`**: nunca se importam mutuamente — garante os 191 goldens e o veredito fundamentalista intactos.
- **MVP de padrões honesto** (Phase 14): só duplo topo/fundo + OCO; triângulos/bandeiras ficam fora do v1.4.
- [Phase 12]: Cache intraday em app.py: frame_intraday(ticker,timeframe,nonce) TTL 300s; nonce so na chave (invalidacao targetada por par), zero clear global (D-08)
- [Phase 13]: Dow no diário via sequência de pivôs (HH/HL) + desempate adx_wilder(>=20)/regressao_trailing(zona morta 5%/ano) → lateral (D-05); semanal por resample W-FRI do próprio frame (D-04, sem rede); conflito multi-TF é rótulo aditivo que modula, nunca bloqueia (D-06)
- [Phase 13]: S/R como ZONAS (low,high) por cluster single-linkage de pivôs (gap < cluster_k×ATR) + banda mínima 0.5×k×ATR → nunca pontos (D-10); Donchian 55 como faixa externa; param OPCIONAL ohlc_nominal em calcular rota famílias de PREÇO (pivôs+níveis) pelo nominal (D-02); família Volume (MM + flag rompimento na barra fechada iloc[-2], D-11) aditiva ao SinaisTecnicos
- [Phase 13]: Fibonacci ANCORADO no último impulso confirmado (par de pivôs coerente com dow_diario: alta=fundo→topo, baixa=topo→fundo) — retração entrada 38,2/50/61,8% + extensão alvo 161,8%, no-repaint, pivos_ancora auditável (D-07); stop = mais conservador entre swing estrutural e ATR×m (min em alta / max em baixa, D-08); R:R "1 : x,y" via np.divide sob np.errstate → "indisponivel" se risco≤0/NaN/inf, NUNCA infinito (D-09)
- [Phase ?]: [Phase 14]: contrato aditivo de padrões (PadraoGrafico/Padroes/Sinal/Checklist) + flag bidirecional volume_acima_mm (barra fechada, agnóstica de direção, Open Q2); detectores em core/indicators.py (OQ1); Padroes.lista é lista (OQ3)
- [Phase 14]: _padroes detecta duplo topo/fundo sobre pivôs confirmados (.dropna()) com neckline horizontal (vale.min/pico.max), estado em_formacao/confirmado (rompimento na barra fechada iloc[-2] + volume_acima_mm config-driven) e measured-move (altura projetada além da neckline); no-repaint provado por truncação; wiring em calcular deferido ao checklist (14-04)
- [Phase ?]: Neckline da OCO por POSIÇÃO inteira da barra (get_loc), nunca timestamp em ns (Pitfall 3 / T-14-06); guard de reta degenerada (pos_f2==pos_f1)
- [Phase 14]: _checklist agrega 6 sinais liga/desliga READ-ONLY (lê rótulos já computados, zero recálculo); calcular() popula padroes/checklist em SinaisTecnicos ponta-a-ponta; firewall de copy D-01 e degradação graciosa verdes (271 testes)
- [Phase ?]: [Phase 14]: limiares geométricos do bloco padroes: (A1–A7, ASSUMED) APROVADOS SEM AJUSTE após validação multi-ticker (6 tickers B3 reais, ~5a diário): 3 padrões no total, 1 único confirmado, 4/6 em zero — anti-pareidolia (Pitfall 1/11) satisfeito; config.yaml intocado, goldens preservados
- [Phase ?]: [Phase 15]: SetupSwing (report/setup.py) — score ponderado explicável (decomposição peso-a-peso, tendência 35), R:R gate duro sob np.errstate, grade PT-BR + floor (<fraco→Sem setup), conflito multi-TF penaliza×0.80 sem bloquear; firewall vs report.py; config-driven; copy neutra anti-imperativa; 283 verdes
- [Phase ?]: [Phase 16]: 4º menu monta read-only SinaisTecnicos+SetupSwing (ohlc_nominal=f.ohlc, Pitfall 6); estado de toggles ISOLADO tec_estado_swing (defaults D-02), nunca grafico.estado_padrao() nem tec_estado da Analisar (D-03/SWING-01); figura make_subplots candlestick nominal + overlays MM + subpainéis RSI/MACD/ADX (reuso golden de grafico.py), rangeslider OFF (Pitfall 4), selo de atraso sempre visível (D-08); S/R/Fib/padrões/card de veredito deferidos p/ 16-02
- [Phase 16]: overlays de nível na figura swing — S/R via add_hrect (bandas verde/vermelho, LEVEL-01), zona de entrada add_hrect + stop/alvo add_hline (gate niveis_setup_on), Fibonacci add_hline (gate fib_on), padrões via add_shape neckline horizontal + add_annotation rótulo em formação/confirmado + add_hline alvo (gate padroes_on, OFF default); card de veredito read-only abaixo do gráfico (grade+score "confluência técnica", decomposição peso-a-peso, checklist ✓/✗, tabela "Referências de estudo (não são ordens)" via fmt_rs/esc_md — nunca st.metric, Pitfall 5), disclaimer condicional inline; copy 100% não-imperativa (SWING-02); 283 goldens verdes

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- **Invariante dos 191 goldens:** devem seguir verdes ao final de **cada** fase do v1.4; mudança só por rebaseline deliberado e justificado. A engine fundamentalista e a aba Analisar não podem ser alteradas.
- **Lookahead/no-repaint:** pivôs e padrões devem ser causais (barras à esquerda E à direita já fechadas); teste de estabilidade no-repaint é obrigatório nas Fases 13 e 14.
- **Barra viva (repaint intraday):** descartar/marcar a última barra não fechada antes de calcular; sinais sempre sobre a barra fechada (`iloc[-2]`).
- **Fronteira "exibe, nunca recomenda":** score alto + entrada/stop/alvo é indistinguível de recomendação se a linguagem for imperativa — copy review é gate (Fases 15 e 16).
- **Calibração de `prominence`/`distance` (pivôs B3):** sem valor canônico — tratar como params em `config.yaml` desde o início; calibrar empiricamente na Fase 13 com múltiplos tickers (candidata a `/gsd-research-phase`).
- **Limites yfinance intraday (MEDIUM):** confirmar period×interval empiricamente na Fase 12 antes de cravar.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260629-ig6 | Aba Swing trade (MVP): candlestick intraday + timeframes + botão Atualizar (reusa engine Fase 12) | 2026-06-29 | 3c4eb15 | Verified | [260629-ig6-aba-swing-trade-mvp-candlestick-intraday](./quick/260629-ig6-aba-swing-trade-mvp-candlestick-intraday/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Docs engine | DDM-DOC-01 (alinhar docstring/teste de t em ddm.py, IN-06) | v2 | 2026-06-04 |
| Refino | Payout-alvo por setor configurável | v2+ | 2026-06-27 |
| UI | Sinalização explícita de "ano extraordinário" na tabela de Fundamentos por ano | v2+ | 2026-06-27 |
| quick_task | 260620-oa9-ajustar-tela-2-ranking-por-multiplos (arquivo ausente/obsoleto) | stale | 2026-06-28 (v1.3 close) |
| quick_task | 260622-cg9-robustez-da-resolucao-de-tickers-retry (arquivo ausente; coberto pelo fix single-entity + ticker_map +60) | stale/resolvido | 2026-06-28 (v1.3 close) |
| uat | Fase 10 10-HUMAN-UAT.md parcial (0 cenários abertos) — validado por checkpoint live aprovado + 191 testes | accepted | 2026-06-28 (v1.3 close) |
| verification | Fase 10 10-VERIFICATION.md human_needed — coberto por checkpoint live dos 5 tickers (aprovado) | accepted | 2026-06-28 (v1.3 close) |

## Session Continuity

Last session: 2026-06-30T13:25:00.000Z
Stopped at: Completed 16-02-PLAN.md
Resume file: None

## Operator Next Steps

- Planejar a primeira fase do v1.4 com `/gsd-plan-phase 12` (Ingestão Intraday + Timeframe).
- Considerar `/gsd-research-phase 14` (padrões gráficos — confiança LOW-MEDIUM) e, opcionalmente, `/gsd-research-phase 13` (calibração de pivôs) antes de planejar essas fases.
