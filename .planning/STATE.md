---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: — Ferramenta de Swing Trade
status: verified
stopped_at: Phase 21 executed and verified (7/7 must-haves; smoke visual pendente)
last_updated: "2026-07-03T11:20:54.603Z"
last_activity: 2026-07-03 -- Phase 21 executada e verificada
progress:
  total_phases: 7
  completed_phases: 7
  total_plans: 22
  completed_plans: 22
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-29)

**Core value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação. No v1.4, a página de swing **EXIBE** sinais técnicos fiéis a Murphy e **NUNCA recomenda**.
**Current focus:** Phase 21 — comparador-multi-ativo-lado-a-lado-múltiplos-selo-por-coluna

## Current Position

Phase: 21 — COMPLETE (verificada)
Plan: 1 of 1 (21-01 concluído)
Status: Verificada — 7/7 must-haves automatizados; falta apenas o smoke visual humano do 5º menu
Last activity: 2026-07-03

## Performance Metrics

**Velocity:**

- Total plans completed: 41 (v1.0 + v1.1 + v1.2) + v1.3 (Fases 9–11)
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
| 17 | 3 | - | - |
| 19 | 4 | - | - |

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
| Phase 17 P01 | 10min | 2 tasks | 1 files |
| Phase 17 P02 | ~9min | 2 tasks | 1 files |
| Phase 17 P03 | ~6min | 2 tasks | 0 files |
| Phase 18 P01 | ~8min | 2 tasks | 4 files |
| Phase 18 P02 | 12min | 2 tasks | 3 files |
| Phase 18 P03 | 15min | 2 tasks | 3 files |
| Phase 19 P01 | 10min | 3 tasks | 2 files |
| Phase 19 P02 | ~2min | 3 tasks | 3 files |
| Phase 19 P03 | ~8min | 2 tasks | 1 files |
| Phase 19 P04 | 5min | 2 tasks | 0 files |
| Phase 20 P01 | 12 | 3 tasks | 5 files |
| Phase 20 P02 | ~10min | 3 tasks | 3 files |
| Phase 21 P01 | 6min | 3 tasks | 6 files |

## Accumulated Context

### Roadmap Evolution

- Phase 19 added (v1.7): Lentes de valuation e contexto na aba Analisar — Graham, Bazin, "quanto teria rendido", comparador de pares. Motivada pelo estudo do concorrente Investidor10.
- Phase 20 added: Selo de Sustentabilidade do Dividendo cruzado com veredito de preço (DDM). Onda 1 do roadmap de diferenciação (estudo de mercado — inspiração AUVP "Selo de Viabilidade", mas cruzando com preço, o que a AUVP não faz). Reusa engine (BSD + veredito DDM); independente da Phase 19.
- Phase 21 added: Comparador multi-ativo lado a lado (múltiplos + selo por coluna). Onda 1 de diferenciação (inspiração AUVP/TC). Depende da Phase 20.

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
- [Phase ?]: [Phase 17]: Modo Trading = vista alternativa (radio swing_vista, Plotly default) troca só a camada de render sobre f.ohlc/sw/sinais já montados (zero fetch/recálculo); _render_lwc module-level com tf_key na assinatura; CDN unpkg @5.2.0 pinado + integrity sha384 inline + crossorigin (mitiga T-17-01); time diário=string / intraday=epoch UTC seg
- [Phase ?]: [Phase 17]: persistência de range LWC-03 CLIENT-SIDE via localStorage por par (lwc_range_ticker_tfkey) — components.html unidirecional (sem round-trip JS→Python); getItem/setItem em try/catch independentes, catch da leitura cai p/ fitContent (SecurityError de iframe sandbox nunca impede o candle de renderizar)
- [Phase ?]: [Phase 17]: overlays da engine no Modo Trading LWC — BandPrimitive (zona/S-R), createPriceLine (stop/alvo/Fib), createSeriesMarkers+LineSeries (pivos/neckline); read-only de sw/sinais, gateado por est[...], degrada em None/vazio; copy de estudo; 283 goldens verdes
- [Phase 17]: aceite da fase é DUPLO — automatizado (283 goldens + grafico.py intacto por diff contra .phase-base-sha, nunca HEAD~N + _render_lwc thin renderer por grep) + humano (smoke Claude-in-Chrome do Modo Trading sem regressão); ambos aprovados. T-17-05 mitigado (chart LWC v5 renderiza ao vivo; SRI não bloqueou; console limpo). Scroll-zoom não exercitável por máquina (wheel sobre iframe rola página-pai) — pan+crosshair confirmados ao vivo, scroll-zoom é default do LWC v5; aceito como limitação conhecida
- [Phase ?]: [Phase 18]: Home vira landing default via 1o item do radio (stateless); render_home() thin + core/home_feed.py read-only never-raise (firewall D-06); A2 validada -> streamlit-local-storage==0.0.25 + feedparser==6.0.12 pinados; .phase-base-sha 5ae5190 gravado; 283 goldens verdes
- [Phase ?]: [Phase 18]: watchlist real — cotacoes() UMA yf.download em lote (5d) + variacao do dia close[-1]/close[-2]-1 (A1 mantida vs fast_info.previous_close, ~0.22pp; batch preserva D-05); _cotacoes cache ttl=45 + _render_watchlist fragment run_every=45 metric colorido + selo ~15min; editor validado teto 5 FORA do fragment; persistencia watchlist_v18 streamlit-local-storage + fallback session_state; 289 verdes
- [Phase ?]: 18-03 A3: noticias multi-feed degrada graciosamente — InfoMoney vazio (throttle) => Home 100% Google News; eco de submanchete suprimido; render seguro (texto + link_button https)
- [Phase 19]: 4 lentes puras em core/lentes.py (Graham, Bazin, retorno Adj Close, comparador de pares) never-raise; P/L do comparador usa lpa_valuation canonico p/ consistencia entre menus; app.py e modulos de metodo intocados (307 verdes)
- [Phase 19]: serie_precos_ajustada (Adj Close 5a) exposto em DadosMercado->CompanyData reaproveitando o ajustado ja baixado no tk.history do beta (zero rede nova); fonte separada da serie_precos nominal (grafico/DDM), so p/ RET-01; never-raise default None (307 verdes)
- [Phase ?]: [Phase 19]: 4 lentes renderizadas read-only na aba Analisar (cards Graham+Bazin ao lado do DDM, retorno 1a/5a via Adj Close, comparador de pares em expander com alvo destacado); app.py so LE lentes.*, zero formula na view; degradacao por lente e copy exibe-nunca-recomenda; 307 verdes
- [Phase 19]: fase fechada por verificacao dupla — gate automatizado (307 verdes = 296 baseline + 11 de test_lentes.py, zero dep nova, metodo intocado, app.py read-only) + smoke humano das 4 lentes aprovado sem regressao
- [Phase 20]: Selo derivado do BSD (cor config-driven verde70/azul55/amarelo40) cruzado com veredito DDM num quadrante (JOIA/VALUE TRAP/...); VERIFICAR e overlay separado; report/selo.py puro com firewall vs report.py; a.selo populado never-raise em analisar_acao; 320 verdes
- [Phase 20]: selo renderizado read-only em Analisar (destaque+quadrante) e como coluna em Garimpo/Ranking via render único (presentation.selo_badge/selo_emoji); app.py só lê a.selo/cor_do_bsd/bsd_empresa, zero threshold hardcoded; 325 verdes
- [Phase ?]: Comparador (Fase 21): derivação nova na engine (normalizar_tickers, montar_comparativo, fmt_rs); app.py read-only; selo COMPLETO por coluna

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
| 260630-g0b | Auto-refresh opcional no 4º menu (Swing) via st.fragment(run_every): toggle + intervalo 30s/1min/5min; cache TTL=300s como porteiro do Yahoo | 2026-06-30 | ed9cf2e | — | [260630-g0b-adicionar-auto-refresh-opcional-ao-4-men](./quick/260630-g0b-adicionar-auto-refresh-opcional-ao-4-men/) |

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

Last session: 2026-07-03T11:20:23.168Z
Stopped at: Phase 21 context gathered
Resume file: None

## Operator Next Steps

- Planejar a primeira fase do v1.4 com `/gsd-plan-phase 12` (Ingestão Intraday + Timeframe).
- Considerar `/gsd-research-phase 14` (padrões gráficos — confiança LOW-MEDIUM) e, opcionalmente, `/gsd-research-phase 13` (calibração de pivôs) antes de planejar essas fases.
