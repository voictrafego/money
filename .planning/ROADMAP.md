# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 + auditoria/correção de dados (shipped 2026-06-28)
- ✅ **v1.4 — Ferramenta de Swing Trade (setups de análise técnica)** — Phases 12–16 (shipped 2026-07-04, tag v1.7)
- ✅ **v1.5 — Modo Trading (UX de gráfico estilo TradingView)** — Phase 17 (shipped 2026-07-04, tag v1.7)
- ✅ **v1.6 — Central de Acompanhamento (Home)** — Phase 18 (shipped 2026-07-04, tag v1.7)
- ✅ **v1.7 — Lentes de valuation, Selo DDM e Comparador** — Phases 19–21 (shipped 2026-07-04)
- 📋 **v2.0 — Comercialização (produto cobrável)** — planejada (fases renumeradas quando reaberta)

> **v1.4–v1.7 foram enviados juntos sob a tag única `v1.7` (2026-07-04).** Snapshot completo do
> roadmap dessas fases em `.planning/milestones/v1.7-ROADMAP.md` e requisitos em
> `.planning/milestones/v1.7-REQUIREMENTS.md`.
> Snapshots anteriores: v1.1/v1.3 em `.planning/milestones/`.
> Requisitos e arquitetura da v2.0 preservados em `.planning/milestones/v2.0-REQUIREMENTS.md`.

## Phases

<details>
<summary>✅ v1.0–v1.3 — Engine, gráfico, timing, saneamento (Phases 1–11) — SHIPPED</summary>

Detalhes completos: `.planning/milestones/v1.3-ROADMAP.md` (e v1.1-ROADMAP.md).

</details>

<details>
<summary>✅ v1.4–v1.7 — Swing Trade, Modo Trading, Home, Lentes/Selo/Comparador (Phases 12–21) — SHIPPED 2026-07-04 (tag v1.7)</summary>

- [x] Phase 12: Ingestão Intraday + Timeframe (2/2 plans) — completed 2026-06-29
- [x] Phase 13: Pivôs, Contexto de Tendência e Níveis (4/4 plans) — completed 2026-06-29
- [x] Phase 14: Padrões Gráficos + Checklist de Sinais (5/5 plans) — completed 2026-06-29
- [x] Phase 15: Montagem do Setup (SetupSwing) + Score (1/1 plan) — completed 2026-06-30
- [x] Phase 16: Página Streamlit + Gráfico do Momento (SWING/CHART) — completed 2026-06-30
- [x] Phase 17: Modo Trading — Candlestick TradingView (Lightweight Charts v5) — completed 2026-07-01
- [x] Phase 18: Home — Watchlist + Notícias (RSS + Yahoo, custo-zero) — completed 2026-07-01
- [x] Phase 19: Lentes de valuation e contexto na aba Analisar — completed 2026-07-02
- [x] Phase 20: Selo de Sustentabilidade do Dividendo × veredito DDM (quadrante) — completed 2026-07-02
- [x] Phase 21: Comparador multi-ativo lado a lado (múltiplos + selo por coluna) — completed 2026-07-03

Detalhes completos (goals, success criteria, plans por fase): `.planning/milestones/v1.7-ROADMAP.md`.

</details>

## Próximo marco

### 📋 v2.0 — Comercialização (produto cobrável)

Assinatura paga (trial 7 dias → mensal via Asaas), gate na frente do app Streamlit, produtização.
Requisitos e arquitetura preservados em `.planning/milestones/v2.0-REQUIREMENTS.md`.
Reabrir com `/gsd-new-milestone` (renumera as fases).
