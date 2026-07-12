# Analista de Dividendos

## What This Is

Engine Python + app Streamlit que replica o método do livro *O Investidor em Ações de Dividendos*
(Orleans Martins & Felipe Pontes) para analisar ações de dividendos da B3, usando apenas dados
gratuitos (CVM + Yahoo Finance + Banco Central). Voltado ao investidor pessoa física que quer
aplicar o método do livro sem pagar por terminais de dados.

A partir do marco v2.0 o produto é comercializado sob a marca **Lazari Capital** (domínio
*Lazari Tech Capital*): assinatura mensal com trial, front comercial próprio e o engine atrás
de um gate de acesso. Posicionamento: **software educacional, sem recomendação de investimento**.

## Core Value

Os números que o app mostra precisam ser **fiéis ao método do livro e consistentes entre si** —
a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.

## Current State

**v2.0 Comercialização (Lazari Capital) shipped 2026-07-10.** Produto no ar sob a marca Lazari
Capital: Django (auth + Asaas + webhooks nativos) na frente, engine Streamlit atrás de gate
Traefik forward-auth. `www.lazaricapital.com.br` + `app.lazaricapital.com.br`, cutover do
`money.voictech.com.br` (301) concluído. E2E pago (03-05) concluído — smoke real R$19,90 PIX
confirmado ao vivo. Fases v2.0 arquivadas em `.planning/milestones/v2.0-phases/`.

**Agora: v2.2 — Motor de Valuation por Arquétipo** (trabalho de engine). Ver seção Current
Milestone abaixo e `.planning/BRIEF-motor-arquetipo.md`.

<details>
<summary>Histórico v1.7 (Swing Trade / Modo Trading / Home / Lentes-Selo-Comparador) — shipped 2026-07-04</summary>

**v1.7 shipped 2026-07-04 (tag única `v1.7`, cobrindo v1.4–v1.7).** Oito marcos completos:
v1.0 consistência · v1.1 gráfico · v1.2 timing · v1.3 saneamento do valuation ·
v1.4 Swing Trade (setups de análise técnica, Fases 12–16) · v1.5 Modo Trading (candlestick
estilo TradingView, Fase 17) · v1.6 Home (watchlist + notícias, Fase 18) · v1.7 Lentes de
valuation + Selo DDM + Comparador multi-ativo (Fases 19–21). Suíte **338 testes verdes**;
Fase 21 com smoke visual do 5º menu "Comparar ações" validado. App na VPS (money.voictech.com.br)
— redeploy do v1.7 pendente.

<details>
<summary>Histórico v1.3 (saneamento do valuation) — shipped 2026-06-28</summary>

**v1.3 shipped 2026-06-28.** Suíte 191 testes verdes; app deployado na VPS.

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

**Marco v2.0 — Comercialização (produto cobrável): DEFINIDO e ADIADO.** Requisitos
(AUTH/BILL/ACCT/LEGAL/OPS) e arquitetura de gateway híbrido já escritos e preservados em
`.planning/milestones/v2.0-REQUIREMENTS.md`. Decisão (2026-06-29): **construir o v1.4 antes** —
agregar valor de produto à ferramenta antes de cobrar. A v2.0 retoma depois.

</details>

</details>

## Current Milestone: v2.2 — Motor de Valuation por Arquétipo

**Goal:** Corrigir o erro de **arquitetura** (não de fórmula) em que a ferramenta aplica um
único motor primário (DDM de estágio único) para todas as ações, gerando vereditos falsos
("qualidade baixa / evitar") em compounders de qualidade. Rotear cada tipo de negócio para o
motor certo **antes** de valuar, e nunca deixar o veredito final ser puxado por um modelo que
não serve àquele perfil. Meta: acertar os ~85% de casos claros e assumir honestamente a dúvida
nos ~15% fronteiriços.

**Target features:**
- **Classificador de arquétipo** (o coração, ~60% do esforço): filtro grosso por setor CVM +
  refino quantitativo (financeira→RIM; pagadora estável→DDM; ROE alto+retenção→compounder;
  margem/lucro oscilando→cíclica), com **fallback honesto** quando a confiança é baixa
- **Registro de motores** arquétipo→motor primário: RIM (banco/seguradora), DDM (pagadora
  regulada — já existe), lucro normalizado (cíclica), DCF multi-estágio (crescimento), NAV/SOTP
  (holding — stretch)
- **Ensemble com bandeira de divergência**: motor primário + ≥1 contraponto; se maior > 2× menor,
  levantar bandeira com hipótese em vez de cravar número único
- **Guarda-corpos de sanidade** anti-aberração antes de virar selo (caso ITUB4)
- **Veredito honesto**: agregação do selo consome o motor **do arquétipo**, não o DDM fixo; em
  caso-fronteira assume a dúvida (range + bandeira) em vez de fingir certeza

**Natureza:** trabalho de **engine** (arquitetura do valuation), não de comercialização. Brief
completo (Core Value, requisitos ARQ/ENG/ENS/SAN/VER, critérios de aceite, mapa de código com
âncoras `arquivo:linha`, ordem sugerida de fases) em `.planning/BRIEF-motor-arquetipo.md`.

_(Marcos v1.0–v1.7 e v2.0 Comercialização arquivados em `.planning/milestones/`. v2.0 shipped
2026-07-10 com 1 item deferido — 03-05 E2E pago, depende de pagamento real do operador.)_

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
- ✓ **Classificador de arquétipo + registry arquétipo→motor** (ARQ) — Validated in Phase 1 (v2.2)
- ✓ **4 motores primários implementados e plugados: RIM (banco), lucro normalizado (cíclica), DCF multi-estágio (crescimento), NAV (holding)** (ENG-02..05) — Validated in Phase 2 (v2.2); consumo pelo selo/veredito é Fase 3

### Active

<!-- Marco v2.2 — Motor de Valuation por Arquétipo. REQ-IDs em REQUIREMENTS.md. -->

- [ ] Ensemble com bandeira de divergência (motor primário + contraponto; bandeira quando maior > 2× menor) (ENS)
- [ ] Guarda-corpos de sanidade anti-aberração antes de estampar veredito "evitar" (SAN)
- [ ] Veredito honesto: selo consome o motor do arquétipo, não o DDM fixo; assume a dúvida em caso-fronteira (VER)

<!-- v2.0 Comercialização — SHIPPED 2026-07-10 (1 item deferido: 03-05 E2E pago). -->

_(v1.4–v1.7 — Swing Trade / Modo Trading / Home / Lentes-Selo-Comparador — SHIPPED 2026-07-04, tag `v1.7`.
v2.0 Comercialização/Lazari Capital — SHIPPED 2026-07-10, produto no ar, E2E pago concluído.)_

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
- **Estado atual (2026-07-12): marco v2.2 em andamento — Phase 1 e Phase 2 completas.** Phase 1
  entregou o classificador de arquétipo (setor CVM + refino quantitativo) + registry arquétipo→motor
  com fallback honesto (5/5 verificado). Phase 2 (5/5 verificado) implementou os 4 motores que
  faltavam como funções puras config-driven em `core/motores.py` — RIM+Ke estrutural (destrava o
  ITUB4 a ~R$28 honesto, materialmente > DDM ~R$16), lucro normalizado (cíclica), DCF multi-estágio
  (crescimento), NAV contábil (holding) — plugou-os no registry e no funil, e migrou a suspensão do
  veredito (`motor != "ddm"`) sem regredir o ITUB4 de "VERIFICAR" para "evitar". Code review pós-fase:
  6 achados corrigidos (guarda de intrínseco não-positivo no motor, paridade com `_guarda_faixa_ddm`).
  Suite: 406 passed. Falta a Phase 3 (selo consome o motor do arquétipo + ensemble/divergência +
  guarda-corpos anti-aberração completos SAN-01).

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
| Construir v1.4 (ferramenta de swing) antes da v2.0 Comercialização | Agregar valor de produto antes de cobrar; v2.0 já está definida e esperando | — Pending (2026-06-29) |
| Swing trade = menu/produto NOVO e separado, não mexe na aba Analisar nem no veredito fundamentalista | Mantém o método do livro de dividendos intacto e validado; análise técnica é outro "produto" dentro do app | — Pending |
| Setup técnico EXIBE sinais, nunca recomenda (sem "compre/venda") | Coerente com o posicionamento de software educacional; o investidor decide | — Pending |
| Tempo real puro fora de escopo no v1.4 (custo-zero); intraday via Yahoo é best-effort com aviso de atraso (~15min) | Feed real-time da B3 é pago e quebraria o princípio de custo zero | — Pending |
| Marca comercial = **Lazari Capital** (domínio Lazari Tech Capital) | Construir imagem de produto desde a etapa comercial | — Pending (v2.0) |
| Comercialização = **gateway híbrido com Django** (front Django + Streamlit atrás de gate), não reescrever o app | Reusa código testado do crm-voic e o engine Streamlit (338 testes) intacto; robusto/seguro/escalável sem retrabalho | — Pending (v2.0) |
| Pivô da arquitetura v2.0: **Django + webhooks nativos** no lugar de Supabase + n8n + React | Cortar dependência de n8n e reaproveitar o crm-voic 1:1; CRM já roda bem nesse padrão | — Pending (v2.0) |
| Gate = **Traefik forward-auth** (Django valida sessão+status, injeta X-User-Email no Streamlit) | Menos código de segurança custom que JWT lido dentro do Streamlit; usa infra Traefik existente | — Pending (v2.0) |
| Asaas em **conta e chave próprias** (não as do crm-voic) | Produto separado; só a estrutura de código é compartilhada | — Pending (v2.0) |
| Cadastro **self-serve** (B2C/trial), diferente do crm-voic (invite-only) | Aquisição de clientes pessoa física precisa de cadastro aberto com trial | — Pending (v2.0) |
| Abrir v2.2 (Motor por Arquétipo) fechando v2.0 (E2E pago concluído; só resta operador decidir estorno do smoke R$19,90) | v2.0 está no ar, funcional e validado end-to-end; nada bloqueia o trabalho de engine | — Pending (2026-07-11) |
| O problema do ITUB4 é erro de **arquitetura** (ausência de roteamento), não de fórmula | DDM/Graham/Bazin estão matematicamente corretos; o defeito é aplicar DDM de estágio único como motor primário para todo negócio e agregar o veredito por ele | — Pending (v2.2) |
| Gargalo do v2.2 = **classificador** (~60%), não os motores (~20%, fórmulas de livro-texto) | Priorizar a árvore de decisão do classificador primeiro, depois plugar os motores nela | — Pending (v2.2) |

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
*Last updated: 2026-07-11 — Marco v2.0 Comercialização (Lazari Capital) SHIPPED (1 item deferido: 03-05 E2E pago); aberto v2.2 — Motor de Valuation por Arquétipo (trabalho de engine: classificador + registry de motores + ensemble/divergência + guarda-corpos + veredito honesto)*
