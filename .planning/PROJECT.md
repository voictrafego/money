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

**v1.3 shipped 2026-06-28.** Quatro marcos completos (v1.0 consistência · v1.1 gráfico ·
v1.2 indicadores de timing · v1.3 saneamento do valuation). Suíte 191 testes verdes; app
deployado na VPS (Streamlit em money.voictech.com.br).

**v1.3 — Saneamento residual do valuation (fases 9–11):** payout sustentável geral (mediana
sem clamp), DY recorrente earnings-based, g histórico log-linear robusto, screening sobre série
normalizada e trava multi-ticker (8/8 requisitos).

**Auditoria online + correção de dados (2026-06-28, mesma sessão, deployado):** a auditoria do
app ao vivo revelou 4/4 ações saindo "sobreavaliada" — 4 bugs de dados/método corrigidos:
(1) **unit XXXX11** (num_acoes na base de units — P/L 3×/5× inflado); (2) **proventos sem JCP**
(payout-mediana vinha pela metade nos bancos — agora div+JCP da DFC da CVM); (3) **Ke usava
Selic spot** → agora Selic through-the-cycle (média 10a); (4) **empresas single-entity** sumiam
(seleção consolidado/individual agora por empresa) + ticker_map ampliado em 60 tickers via FCA.
Mais disclaimer legal (software educacional, não recomendação). Continuação natural do tema v1.3
(fidelidade do valuation para qualquer ticker).

**Próximo marco: v2.0 — Comercialização (produto cobrável).** Decisões: assinatura paga (trial
7d → mensal, Asaas); começar produtizando (auth → planos/gate → billing recorrente →
multiusuário); posicionamento como software educacional (sem recomendação).

## Current Milestone: v2.0 — Comercialização (produto cobrável)

**Goal:** Transformar o protótipo de usuário único num produto que cobra: autenticação, trial de
7 dias → assinatura mensal (Asaas), gate de acesso e multiusuário — posicionado como software
educacional (sem recomendação). Decisão de arquitetura-chave a resolver no discuss/requirements:
como colar auth+billing num app Streamlit (provável híbrido: front/checkout no stack
React+Vite+n8n+Asaas na frente do Streamlit). Requisitos detalhados via `/gsd-new-milestone`.

_(v1.3 e marcos anteriores arquivados em `.planning/milestones/`.)_

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

<!-- Marco v1.3 — saneamento residual do valuation (generalização). REQ-IDs em REQUIREMENTS.md. -->

- [ ] DY recorrente sustentável (lucro normalizado × payout sustentável) e formatado como % na UI
- [ ] Payout sustentável que expurga não-recorrentes por regra geral (não a média 3a que encosta em 100%)
- [ ] g histórico robusto + screening (BSD/Ranking) sem CAGR sobre lucro/dividendo cru
- [ ] Hierarquia do header com DY recorrente em destaque; payout "último ano" cru exibido

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
*Last updated: 2026-06-27 — Marco v1.3 iniciado (saneamento residual do valuation); v1.2 concluído (Fase 7, 150 testes verdes)*
