---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: — Indicadores de tendência
status: executing
stopped_at: "Completed 08-04-PLAN.md (FIX-06 guardrails + golden de regressão VULC3). Fase 8 completa (4/4). Próximo: Phase 7 (UI)."
last_updated: "2026-06-27T12:19:03.059Z"
last_activity: 2026-06-27
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 16
  completed_plans: 13
  percent: 81
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-24)

**Core value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.
**Current focus:** Phase 07 — ui-overlays-subpain-is-controles-e-enquadramento

## Current Position

Phase: 07 (ui-overlays-subpain-is-controles-e-enquadramento) — EXECUTING
Plan: 3 of 5
Status: Ready to execute
Last activity: 2026-06-27

Progress: [████████░░] 81%

## Performance Metrics

**Velocity:**

- Total plans completed: 14 (v1.0 + v1.1)
- Average duration: — min
- Total execution time: — hours

**By Phase (concluídas):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | - | - |
| 02 | 2 | - | - |
| 03 | 2 | - | - |
| 05 | 3 | - | - |
| 06 | 2 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 04 P02 | 10 | 2 tasks | 1 files |
| Phase 05 P01 | 18 | 3 tasks | 3 files |
| Phase 06 P01 | 4 | 3 tasks | 3 files |
| Phase 06 P02 | 5 | 2 tasks | 2 files |
| Phase 08 P01 | — | 3 tasks | 6 files |
| Phase 08 P02 | ~20 | 2 tasks | 3 files |
| Phase 08 P03 | ~25 | 2 tasks | 7 files |
| Phase 08 P04 | ~35 | 2 tasks | 6 files |
| Phase 07 P01 | 12 | 3 tasks | 4 files |
| Phase 07 P02 | 6 | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- app.py é read-only: só lê campos da engine, nunca recalcula método (locked, Phase 2).
- Série do gráfico = Close nominal (`auto_adjust=False`); indicadores usam série split-adjusted (não dividend-adjusted) — eixo nominal preserva alinhamento com a banda DDM (CR-01).
- Análise técnica (v1.2) é **consultiva**, nunca altera o veredito fundamentalista; rompimento técnico dispara **reverificação** dos fundamentos, não venda.
- [v1.2 research]: OHLC já está em memória em `coletar_mercado` (`tk.history(period="5y", auto_adjust=False)`) — preservar `dm.ohlc`, não fazer nova chamada de rede (espelha o padrão `serie_precos`).
- [v1.2 research]: hand-roll total dos indicadores em numpy/pandas/scipy — **sem nova dependência de TA** (`ta`/`pandas-ta`/`TA-Lib` incompatíveis com numpy 2.4.6 / pandas 3.0.3).
- [v1.2 research]: RSI/ADX exigem suavização de **Wilder** (`ewm(alpha=1/length, adjust=False)`, seed SMA), não EMA padrão — travar com golden test cruzado com TradingView.
- [v1.2 research]: `a.sinais` (`SinaisTecnicos`) calculado em `report.analisar_acao` — ponto único compartilhado por CLI e UI; paridade gratuita.
- [Phase ?]: [05-01] SinaisTecnicos nested por família; cross/posição×MM200 SEMPRE sobre SMA (D-03); RSI Wilder SMA-seeded = 70.5328; MACD usa EMA padrão, não Wilder.
- [05-03] ADX dupla-Wilder: 1ª suavização do DMI com start=1 (barra 0 = diff indefinido) → 1º DI no índice 14; 2ª suavização do DX com start=length → 1º ADX no índice 27. calcular() agrega as 4 famílias com guard de borda → fully-indisponivel. Checkpoint TEST-03 (ADX × TradingView) APROVADO e literais congelados em test_adx_wilder_referencia.
- [Phase ?]: [06-02] Matriz e alerta extraídos em helpers puros (_matriz_leitura/_alerta_reverificacao) read-only sobre o fundamento — golden travável com input pinado; token do veredito via startswith porque 'NO INTERVALO' é bi-palavra
- [08-01] FIX-04: base de lucro normalizada (`normalizacao.py`) vira o número-síntese canônico ÚNICO do valuation. `roe_valuation()`/`lpa_valuation()`/`payout_valuation()` chamados SEM args nas 3 superfícies (Analisar/Ranking app/Ranking cli) → consistência entre menus por construção (espelha o padrão payout_valuation).
- [08-01] Primitiva: mediana p/ 2≤N<5, média winsorizada p/ N≥5 (winsor percentil não morde poucos pontos); knob `normalizacao` no config separado do `bsd` (valuation ≠ screening).
- [08-01] Fronteira travada: `roe(ano)`/`lpa(ano)`/`payout(ano)`/`lucro_liquido` CRUS seguem na tabela "Fundamentos (por ano)" e no screening (elegibilidade per-ano Cap. 8). Flags de risco (payout>100%, DY>15%) leem CRU — payout_valuation clampado em 1.0 nunca dispararia o DDM-FIX-05.
- [08-01] CAGR de valuation usa série winsorizada (`serie_lucro_normalizada`); lucro_positivo/decrescente do ciclo de vida seguem na série crua (fatos per-ano).
- [08-02] FIX-02: o g_alto da fase explícita é subordinado ao g sustentável — TETO = g_fundamentos (ROE_norm × (1−payout_valuation)), precedência g_fund → teto absoluto 0.25 → trava ≤Ke (FIX-01). Payout ≥100% ⇒ g_fund ≤0 ⇒ g_alto=0; piso artificial g_estavel REMOVIDO da seleção do g_alto (g_estavel segue só como taxa da perpetuidade no DDM). VULC3 (payout_valuation=100%): g_alto adotado = 0,0 (antes 25%), DDM ainda finito.
- [08-02] g_fund é TETO (min com o CAGR), não substituto: série constante (CAGR=0) ⇒ g_alto=0 mesmo com g_fund>0 — a empresa que não cresceu o lucro não projeta crescimento.
- [08-03] FIX-03: CAPM 'local' vira o default — Ke = rf (Selic ao vivo do BCB) + beta × ERP Brasil (0,06), com fallback gracioso (`macro.selic_para_capm`: selic_meta() or selic_fallback de config). Pureza da engine: rede só nos entry points (cli/app injetam `cfg['capm']['rf_local']`); `analisar_acao` lê o rf de cfg e permanece offline (grep selic_meta em report.py == 0). VULC3 Ke: 9,43% (2019) → 15,78% (fallback) / 19,53% (Selic viva 14,25% em 2026) — faixa small cap BR.
- [08-03] Rebaseline de caso-limite recalibra a FIXTURE, nunca o assert: o Ke maior fez a alvo SUBAVALIADA flipar (série constante cola o intrínseco no limiar DY>15% ⇒ vira "VERIFICAR") — corrigido tornando a alvo crescente (g_alto>0); TRKE PL 1987→1700 p/ g_fund>Ke. test_ke_itau_capm (literais do livro) intacto.
- [08-04] FIX-06 (capstone): banda intrínseca vmin/vmax = min/max da matriz Ke×g (sensibilidade REAL, já calculada), não o toggle binário ddm_constante×ddm_h; fallback gracioso p/ matriz só-None (T-08-07). DY recorrente (dy_recorrente sobre provento normalizado, reusa a primitiva do Plan 01) distinto do dy_atual() trailing — ambos exibidos, trailing preservado. Setor override display-only por ticker (dict {cd_cvm,setor} no ticker_map; resolver() vira wrapper sobre _resolver_base) — VULC3=11762, "Calçados (Consumo Cíclico)".
- [08-04] Golden de regressão VULC3 (test_vulc3_regressao.py) trava a cascata domada end-to-end: base normalizada 4000<12000 extraordinário (FIX-04), g_alto=0 (FIX-02), Ke 15,78% (FIX-03), intrínseco 2,3× preço — não 11–23× (FIX-01/06), veredito VERIFICAR não verde (FIX-05), ROE/payout Analisar==Ranking. Nenhum golden existente precisou rebaseline (banda mais larga não virou caso algum). Suíte 133 verde.
- [Phase ?]: [07-01] Degradacao holistica: timing_resumo vazio colapsa matriz_leitura (CR-01); markdown por not a.timing_resumo (IN-01); resample W-FRI por DatetimeIndex+colunas (WR-01).
- [Phase ?]: [07-01] SinaisTecnicos.close (campo aditivo default None) expoe a close split-adjusted ja usada, read-only, para os marcadores de evento da UI (UI-04).
- [Phase ?]: [07-02] Glossário técnico: 11 chaves tec_* em glossario.G lidas por h('tec_*'); contrato (existência + tom consultivo, sem 'compre'/'venda') travado por tests/test_glossario.py.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- Invariante TEST-07: os 64 golden tests de valuation existentes devem continuar verdes ao final de cada fase do marco — nenhuma fórmula do livro pode mudar.
- Pontos de validação (não pesquisa): Phase 4 — testar série split-adjusted com ticker de split conhecido antes de fechar; Phase 5 — cruzar fixture RSI/ADX com TradingView antes de travar o golden; Phase 7 — fresh-reader test ("cara + timing bullish") como critério de aceite explícito de UI-06.
- Degradação graciosa (DATA-03) deve seguir o padrão do aviso GRAF-03 já existente, sem quebrar a aba quando `hist`/OHLC vier vazio.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Docs engine | DDM-DOC-01 (alinhar docstring/teste de t em ddm.py, IN-06) | v2 | 2026-06-04 |

## Session Continuity

Last session: 2026-06-27T12:18:42.222Z
Stopped at: Completed 08-04-PLAN.md (FIX-06 guardrails + golden de regressão VULC3). Fase 8 completa (4/4). Próximo: Phase 7 (UI).
Resume file: None

## Operator Next Steps

- Planejar a primeira fase com `/gsd-plan-phase 4`
