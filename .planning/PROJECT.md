# Analista de Dividendos

## What This Is

Engine Python + app Streamlit que replica o método do livro *O Investidor em Ações de Dividendos*
(Orleans Martins & Felipe Pontes) para analisar ações de dividendos da B3, usando apenas dados
gratuitos (CVM + Yahoo Finance + Banco Central). Voltado ao investidor pessoa física que quer
aplicar o método do livro sem pagar por terminais de dados.

## Core Value

Os números que o app mostra precisam ser **fiéis ao método do livro e consistentes entre si** —
a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.

## Current State

**v1.1 shipped 2026-06-23.** A aba "Analisar" agora mostra um gráfico Plotly do preço de
fechamento de 5 anos com a banda do valor intrínseco do DDM sobreposta, botões de período
(30D/6M/1A/5A) e degradação graciosa quando o Yahoo falha. Dois marcos completos (v1.0
consistência + v1.1 gráfico); 64 testes golden verdes.

**Marco ativo: v1.2 — Indicadores de tendência (timing) na aba Analisar.**

**Fase 5 completa (2026-06-26):** o módulo puro `core/indicators.py` calcula as 4 famílias
(Tendência SMA/EMA+cross, Canais Donchian/Bollinger/squeeze, Força ADX/inclinação, Momentum
RSI/MACD) a partir do OHLC via `indicators.calcular(ohlc, cfg) → SinaisTecnicos`, com a matemática
travada por golden tests (Wilder, no-repaint, split ITSA4, ADX×TradingView). Suíte: 92 testes
verdes. Próximo: Fase 6 — integração na engine + composite + alerta + CLI.

**Fase 6 completa (2026-06-26):** os sinais técnicos passam a viver em `AnaliseAcao` via
`analisar_acao` (popula `a.sinais` por `indicators.calcular`), com o composite de *timing de entrada*
(3 estados macro pela árvore MM200×ADX), a matriz fundamento×técnico (fundamento sempre líder), o
alerta de reverificação (OR de perda-MM200 / death cross / perda da mínima do Donchian — voz
"reverifique os fundamentos", nunca venda) e a base temporal diária/semanal (default semanal, W-FRI)
em `cfg`. Tudo espelhado na CLI em `relatorio_markdown`. Suíte: 103 testes verdes; invariante TEST-07
(valuation) preservada. Pendência advisory do code review (CR-01: assimetria de degradação da
`matriz_leitura`) registrada em `06-REVIEW.md` para corrigir antes da Fase 7. Próximo: Fase 7 — UI.

## Current Milestone: v1.2 Indicadores de tendência (timing) na aba Analisar

**Goal:** Adicionar indicadores técnicos de tendência — consultivos, ligáveis/desligáveis — à aba
Analisar para auxiliar o *timing* de entrada e disparar um alerta de reverificação quando o preço
rompe a tendência (possível perda de fundamentos). Estritamente consultivo: o veredito
fundamentalista (DDM/múltiplos) continua sendo a base e nunca é sobrescrito.

**Target features:**
- Médias móveis (SMA/EMA 20/50/200) + cruzamentos (golden/death cross) e posição preço×MM200
- Canais de alta/baixa (Donchian máx/mín + Bandas de Bollinger) com rompimentos
- Força/inclinação da tendência (ADX + inclinação) para dizer SE há tendência e a direção
- Momentum (RSI + MACD) para o timing fino de entrada
- Painel de controles na aba Analisar para ligar/desligar e selecionar quais indicadores exibir
- Resumo de sinal de *timing de entrada* (consultivo)
- Alerta de venda/reverificação: rompimento técnico (ex.: perda da MM200) → "reveja os fundamentos"

## Requirements

### Validated

<!-- Capacidades já existentes no código, em uso. -->

- ✓ Analisar uma ação a fundo: múltiplos (Cap. 10), valuation por DDM de dois estágios
  (Cap. 13-17), CAPM/Ke (Cap. 16), crescimento (Cap. 14) e tabela de fundamentos de 10 anos — existing
- ✓ Garimpar carteira por ranking BSD de Carlson (Cap. 8) + filtros customizados — existing
- ✓ Ranking por múltiplos com preço-alvo por regressão P/L ~ f(payout, ROE) (Cap. 11-12) — existing
- ✓ Ingestão gratuita de dados: CVM (fundamentos), Yahoo (preços/dividendos/beta), BCB (Selic/macro) — existing
- ✓ CLI espelhando a engine da UI — existing
- ✓ Tooltips de glossário (ícone ?) com definições do livro em todos os termos da UI — existing
- ✓ Testes golden da engine (pytest) — existing
- ✓ **Corte por Selic real no Garimpo** (CR-01) — Validated in Phase 1
- ✓ **Janela de payout unificada entre modos** (CR-02/WR-03) — Validated in Phase 1 (função canônica `payout_valuation()`)
- ✓ **Clamp/alerta de payout fora de [0,1] no Ranking, igual ao Analisar** (CR-03 parte) — Validated in Phase 1
- ✓ **"indisponível" em vez de "—" no Ranking quando ROE/payout faltam** (CR-03 parte / RANK-01) — Validated in Phase 2
- ✓ **ROE com base de PL consistente** (WR-01) — Validated in Phase 1
- ✓ **Proxy de crescimento padronizado em janela** (WR-02) — Validated in Phase 1
- ✓ **DY corrente com dividendos dos últimos 12m** (WR-04) — Validated in Phase 1
- ✓ **Fatores ausentes no BSD tratados como neutro/ausente** (WR-05) — Validated in Phase 1
- ✓ **BSD com padronização absoluta (referência fixa), reproduzível** (WR-06) — Validated in Phase 1
- ✓ **Intervalo de valor intrínseco vindo de um único cálculo (sem duplicação)** (WR-07) — Validated in Phase 1
- ✓ **Coluna Ano-base efetivo (ultimo_ano) no Garimpo e Ranking** (ANO-01) — Validated in Phase 2
- ✓ **Payouts duplos rotulados no Analisar** (último ano vs. média 3a do DDM) (PAYOUT-02) — Validated in Phase 2
- ✓ **Trava de testes de coerência cross-modo** (ROE/payout/direção do veredito) (TEST-01/TEST-02) — Validated in Phase 2
- ✓ **Gráfico interativo (Plotly) de preço 5a na aba Analisar, com zoom/hover e botões de período** (GRAF-01) — Validated in Phase 3 (v1.1)
- ✓ **Banda do valor intrínseco do DDM sobreposta ao preço** (GRAF-02) — Validated in Phase 3 (v1.1)
- ✓ **Degradação graciosa quando a série de preços do Yahoo falha** (GRAF-03) — Validated in Phase 3 (v1.1)

### Active

<!-- Marco v1.2 — indicadores de tendência (timing) na aba Analisar. REQ-IDs em REQUIREMENTS.md. -->

- [ ] Indicadores de tendência consultivos (médias móveis, canais, força/inclinação, momentum) na aba Analisar
- [ ] Controles para ligar/desligar e selecionar quais indicadores ver no gráfico
- [ ] Sinal de timing de entrada (consultivo, não altera o veredito barato/caro)
- [ ] Alerta de venda/reverificação ao rompimento técnico (preço perde a tendência → revisar fundamentos)

### Out of Scope

- Dados pagos / APIs premium (brapi pago, terminais) — projeto é custo zero por princípio
- Reescrever a engine de valuation — o cálculo está correto; o problema é consistência de
  apresentação/agregação entre menus, não as fórmulas
- Novas ferramentas/menus além dos 3 atuais — o gráfico do v1.1 é um enriquecimento da aba
  "Analisar" existente, não um quarto menu

## Context

- Stack: Python 3, Streamlit 1.58, pandas, numpy, yfinance, pytest. Engine em `src/analista/`
  (core: ddm, capm, fundamentals, growth, screening, lifecycle, comparables, multiples;
  ingest: cvm, prices, macro, universe, build; report). UI em `app.py`, CLI em `cli.py`.
- **Auditoria de consistência já feita** — `CONSISTENCY-REVIEW.md` na raiz documenta os 16
  achados (3 críticos, 7 warnings, 6 infos), cada um com arquivo:linha, o que diverge e a
  correção sugerida. É a fonte de verdade do escopo deste marco.
- O que está confirmado correto (não mexer): fórmulas únicas de ROE/P-L/DY/payout/ML/EY em
  `multiples.py`/`fundamentals.py`; unidades decimais com ×100 só na borda; UI lê valores da
  engine sem recalcular Ke/Beta/g/DDM; CLI e UI compartilham a mesma engine.
- **Estado atual: marco v1.0 completo.** Phase 1 (engine de consistência, 5/5 verificado) tornou
  os números coerentes na origem; Phase 2 (apresentação + travas, 5/5 verificado) expôs ano-base,
  "indisponível" e payouts rotulados na UI e travou a coerência cross-modo com pytest (47 passed).
  Os 16 achados do `CONSISTENCY-REVIEW.md` estão endereçados.

## Constraints

- **Tech stack**: Python 3 + Streamlit; sem backend próprio; custo zero (só dados gratuitos)
- **Compatibility**: testes golden existentes em `tests/` devem continuar passando após as correções
- **Infra/git**: este projeto agora é um **repositório git dedicado** (`git init` próprio),
  desacoplado do repositório do `$HOME`. `.planning/` vive dentro do projeto.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Abordagem das correções = mudar o comportamento (não só rótulos) | Fidelidade ao método do livro; a engine deve cumprir o que a UI promete | ✓ Good — Fases 1-2 |
| Padronizar BSD contra referência fixa em vez do lote | "BSD > 80" do Carlson é corte absoluto; relativo ao lote torna a nota não-reproduzível | ✓ Good — Phase 1 |
| Repo git dedicado para o projeto | Resolve a dor do git root no `$HOME`; isola histórico e o `.planning/` | ✓ Good |
| Marco cobre todos os 16 achados (3 críticos + 7 warnings; infos conforme couber) | Usuário pediu cobertura total | ✓ Good — endereçado nas Fases 1-2 |
| app.py é read-only: só lê campos da engine, nunca recalcula método | Garante que a UI não reintroduz divergência entre modos | ✓ Good — Phase 2 |
| Série do gráfico = Close nominal (`auto_adjust=False`), beta/retornos seguem em Adj Close | Eixo Y do gráfico tem de ficar na mesma base da banda DDM (nominal); senão preços retroajustados distorcem a margem de segurança (CR-01) | ✓ Good — Phase 3 |
| Botões de período nativos do Plotly (30D/6M/1A/5A) | Zoom por janela sem JS nem dependência extra | ✓ Good — Phase 3 |
| `esc_md()` escapa `$` em metric/alertas (não no `fmt_rs` global) | Dois `R$` na mesma string acionavam o modo LaTeX do Streamlit; tabelas continuam com texto cru | ✓ Good — Phase 3 |
| Análise técnica (v1.2) é **consultiva**, nunca altera o veredito fundamentalista | O projeto é fundamentalista por princípio (método do livro); indicadores ajudam o timing/alerta, não o "barato/caro" | — Pending |
| Sinal de venda = rompimento técnico **dispara reverificação** dos fundamentos (não vende sozinho) | O livro vende por perda de fundamento; o técnico serve de gatilho antecipado para o investidor reolhar os números | — Pending |
| Indicadores ligáveis/desligáveis e selecionáveis na aba Analisar | Evita poluir o gráfico; o investidor escolhe o que quer ver sem virar um terminal de trade | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-26 — Fase 6 completa (integração engine + composite + alerta + CLI); 103 testes verdes*
