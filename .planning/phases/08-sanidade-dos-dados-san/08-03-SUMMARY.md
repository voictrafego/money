---
phase: 08-sanidade-dos-dados-san
plan: 03
subsystem: database
tags: [snapshot, fixture, sanidade, yfinance, cvm, splits, market-cap, never-raise, offline]

# Dependency graph
requires:
  - phase: 08-sanidade-dos-dados-san
    provides: "CompanyData com market_cap/implied_shares_outstanding/splits + proventos_filtro_amplo/origem_num_acoes (plano 08-01)"
provides:
  - "tests/fixtures/snapshot_sanidade_2026-07-14.yaml — 104 tickers com o dado SUJO congelado (market_cap + splits inclusos)"
  - "tests/helpers_sanidade.py — carregar_snapshot_sanidade(path) -> Dict[str, CompanyData], offline, sem verificacao (BLIND-04a-safe)"
  - "scripts/capturar_snapshot_sujo.py — captura dos 104 com degradacao por ticker (never-raise, SAN-06)"
affects: [09-ingestao-correta-data, 10-primitivas-sem-vies-prim]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Embrulho de prices.coletar_mercado p/ capturar o DadosMercado cru (shares_outstanding) sem 2a chamada de rede"
    - "Snapshot com degradacao por ticker: bloco falhas: torna a ausencia VISIVEL; so return 1 se 0 capturados"
    - "Helper de fixture que so CONSTROI (zero assert) p/ nao acordar o detector BLIND-04a"

key-files:
  created:
    - "scripts/capturar_snapshot_sujo.py"
    - "tests/fixtures/snapshot_sanidade_2026-07-14.yaml"
    - "tests/helpers_sanidade.py"
    - "tests/test_sanidade_snapshot.py"
  modified:
    - "tests/classificacao.yaml"

key-decisions:
  - "11 tickers 404 no Yahoo HOJE (nao rate-limit, verificado) sao congelados COM a CVM e SEM mercado, no bloco falhas: — SAN-06 em acao, MRFG3 era o caso antecipado"
  - "Snapshot congela market_cap E splits (nao so o preco) — EQTL3 nao pisca; o split de 2018 do ITUB4 fica disponivel p/ a isencao D-12"
  - "shares_outstanding cru do Yahoo capturado embrulhando prices.coletar_mercado — sem 2a chamada de rede, uma unica passagem"

requirements-completed: [SAN-01, SAN-02, SAN-06]

# Metrics
duration: 35min
completed: 2026-07-14
---

# Phase 8 Plan 03: Snapshot Sujo dos 104 (Wave 2) Summary

**Congela a evidência intocada do dado SUJO — os 104 tickers da B3 com `market_cap` e `splits` inclusos, capturados uma única vez ao vivo, degradando por ticker (11 dão 404 no Yahoo hoje, congelados com a CVM intacta e sem mercado), sem nenhum R$ derivado dentro — e o loader que reconstrói `CompanyData` 100% offline. É contra este snapshot que a Fase 9 vai medir o conserto, ticker a ticker.**

## Performance

- **Duration:** ~35 min (dos quais ~10 min de captura ao vivo da rede)
- **Completed:** 2026-07-14
- **Tasks:** 2
- **Files:** 4 criados + 1 modificado

## Accomplishments

- `scripts/capturar_snapshot_sujo.py` captura os **104 tickers** de `data/ticker_map.json` (universo lido do arquivo, `ano_base`/`anos_historico` de `config.yaml`), **degradando por ticker** (never-raise, SAN-06): um ticker que falhe não aborta a captura; só devolve `1` se **nenhum** ticker for capturado. Um bloco `falhas:` no topo do YAML torna a ausência **visível**.
- `tests/fixtures/snapshot_sanidade_2026-07-14.yaml` — 104 tickers, **13.756 linhas**, dado **SUJO intacto**. Congela `market_cap` **e** `splits` (não só o preço): o EQTL3 (a 0,5% do limiar SAN-01) não pisca, e os **12 splits do ITUB4** (incluindo o de **2018**, fora da janela de 5y do `prices.py`) ficam disponíveis para a isenção D-12.
- **11 tickers 404 no Yahoo hoje** — AZUL4, BRFS3, CCRO3, CPLE6, ELET3, ELET6, EMBR3, JBSS3, MRFG3, ODPV3, TRPL4 — congelados **com a CVM completa e sem mercado**. O **MRFG3** (o caso vivo antecipado do SAN-06) tem `lucro_liquido`/`proventos_filtro_amplo` de 10 anos e `market_cap: null`, `splits: {}`.
- **Zero R$ derivado por ticker** (D-05/D-07): o script não toca a camada de veredito, não carimba `intrinseco`/`motor`/`arquetipo`. `grep` no YAML confirma 0 ocorrências.
- `tests/helpers_sanidade.py` reconstrói `CompanyData` **offline**, nascendo `confianca='nao_avaliada'` (D-03); é um helper que **só constrói** (zero verificação) para não acordar o detector BLIND-04a.
- `tests/test_sanidade_snapshot.py` — 5 testes `contrato` (cobertura de conjunto, market_cap+splits congelados, caso MRFG3, zero R$ derivado, reconstrução offline), **sem nenhum assert numérico**. Suíte: **435 passed, 1 skipped, 38 deselected, 2 xfailed, 0 failed**.

## Task Commits

1. **Task 1: script de captura dos 104 com degradação por ticker** — `c5864bb` (feat)
2. **Task 2: snapshot congelado + loader offline + prova de contrato** — `5f969ef` (feat)

## Files Created/Modified

- `scripts/capturar_snapshot_sujo.py` — captura standalone, molde do `capturar_snapshot_bancos.py`, com as 3 diferenças duras (104 tickers, degradação por ticker, zero R$)
- `tests/fixtures/snapshot_sanidade_2026-07-14.yaml` — a evidência congelada dos 104 (criado)
- `tests/helpers_sanidade.py` — `carregar_snapshot_bruto`/`carregar_snapshot_sanidade`/`tickers_do_snapshot`/`falhas_do_snapshot` (criado; sem `assert`)
- `tests/test_sanidade_snapshot.py` — 5 testes `contrato` (criado)
- `tests/classificacao.yaml` — 5 entradas `contrato` para os testes novos (08-03)

## Decisions Made

- **Uma única chamada de rede por ticker.** Para capturar o `shares_outstanding` cru do Yahoo (que `montar_empresa` consome mas não expõe em `CompanyData`), o script **embrulha `prices.coletar_mercado`** e guarda o último `DadosMercado` — sem uma 2ª chamada de rede que dobraria o risco de rate-limit em 104 tickers.
- **Os 11 tickers degradados ficam no snapshot E em `falhas:`.** A ausência de mercado é registrada em dois lugares: na entrada do ticker (campos `null`) e no bloco `falhas:` — visível, não silenciosa. O `test_snapshot_cobre_o_universo_conhecido` usa `set(snap) >= tickers_conhecidos() − falhas` (superset), então tickers com mercado ausente não desqualificam a cobertura.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `\$` inválido nos docstrings quebrava a coleta com SyntaxWarning**
- **Found during:** Task 2 (coleta dos nodeids)
- **Issue:** Os docstrings usavam `R\$` (escape inválido em Python 3.14 → `SyntaxWarning`).
- **Fix:** Trocado `R\$` por `R$` em `tests/test_sanidade_snapshot.py`.
- **Files modified:** tests/test_sanidade_snapshot.py
- **Committed in:** `5f969ef`

**2. [Rule 1 - Bug] A palavra "assert" no docstring do helper falhava o critério de aceite**
- **Found during:** Task 2 (verificação `grep -c "assert" tests/helpers_sanidade.py -eq 0`)
- **Issue:** O docstring do helper mencionava a palavra `assert` (3×) ao explicar por que ele não pode conferir — o critério de aceite é um `grep` literal por `assert`, que contava as menções do docstring.
- **Fix:** Reescrito o docstring para usar "verificação/checagem" no lugar da palavra reservada. Nenhum `assert` real havia (o detector BLIND-04a usa AST, não texto — mas o critério de aceite é literal).
- **Files modified:** tests/helpers_sanidade.py
- **Committed in:** `5f969ef`

### Observação (não é desvio, é a instrução do plano em ação)

**11 tickers em `falhas:` (o plano previa "um punhado" e mandava re-rodar se passasse disso).**
O plano diz: *"Se o bloco falhas: sair com mais de um punhado de tickers, é rate-limit do Yahoo — re-rode."* Saíram **11**. **Investiguei e descartei rate-limit** (o gatilho da instrução): na mesma sessão fresca o Yahoo serve ITUB4/PETR4/WEGE3, mas os 11 falham **nos dois endpoints (`info` e `history`) por símbolo** e **re-rodar reproduz exatamente os mesmos 11**. Parte são renames/fusões reais (BRFS3→MBRF, CCRO3→MOTV3, TRPL4→ISAE4, JBSS3→NYSE via BDR, MRFG3→MBRF); ELET3/ELET6/EMBR3/ODPV3/AZUL4/CPLE6 é o quirk conhecido do `quoteSummary` do Yahoo. Como **não é rate-limit**, re-rodar seria fútil (idempotente). O snapshot congela a realidade suja de hoje — que é exatamente o que a Fase 8 existe para fazer; a Fase 9 conserta a ingestão. O SAN-06 (never-raise) foi projetado para este caso: o MRFG3 era o exemplo antecipado, e 10 outros compartilham o mesmo mecanismo hoje.

## Issues Encountered

Nenhum além dos dois desvios acima. A captura tocou a rede uma única vez (~10 min, 104 tickers), sem abortar.

## Known Stubs

None. Todos os campos são lidos de fonte real (CVM cache / Yahoo) ou têm `null`/`{}` explícito para os 11 tickers sem mercado — que é o estado sujo real de hoje, não um placeholder.

## Threat Flags

Nenhuma superfície nova além da já registrada no `<threat_model>` do plano (T-08-07 DoS por rate-limit — mitigado pela degradação por ticker; T-08-08 tampering do snapshot — mitigado por `test_snapshot_nao_estampa_reais_por_ticker`).

## User Setup Required

None. (Lembrete de estado local: `git config core.hooksPath .githooks` num clone novo — já configurado neste repo.)

## Next Phase Readiness

- O baseline do D-05 (Fase 9) tem a evidência congelada: `carregar_snapshot_sanidade()` devolve 104 `CompanyData` offline, com `market_cap`/`splits`/`proventos_filtro_amplo`/`origem_num_acoes` prontos para os detectores SAN.
- **Decisão pendente para o operador (fora do escopo desta fase):** os 11 tickers 404 (especialmente os renomeados/fundidos: BRFS3→MBRF, CCRO3→MOTV3, TRPL4→ISAE4, JBSS3, MRFG3→MBRF) devem sair/atualizar `data/ticker_map.json`? Isso é **dado, não detecção**, e mexer em `ticker_map.json` tem efeito colateral no `tickers_conhecidos()` do BLIND-04a. Registrar para a Fase 9.
- **Nada consertado, de propósito:** os números do snapshot são exatamente os que o pipeline produz hoje — o teste de regressão da Fase 9.

## Self-Check: PASSED

- Arquivos criados existem: `scripts/capturar_snapshot_sujo.py`, `tests/fixtures/snapshot_sanidade_2026-07-14.yaml`, `tests/helpers_sanidade.py`, `tests/test_sanidade_snapshot.py` — todos FOUND.
- Commits no histórico: `c5864bb` (Task 1), `5f969ef` (Task 2) — ambos FOUND.
- Critérios de aceite: 104 tickers, `market_cap`/`proventos_filtro_amplo` em 104, `^MRFG3:` = 1, 5 entradas em `classificacao.yaml`, 0 `intrinseco/analisar_acao/arquetipo` no YAML, 0 `assert` no helper — todos verificados.
- `pytest -k sanidade_snapshot` verde offline; `pytest` inteiro **435 passed, 0 failed**.

---
*Phase: 08-sanidade-dos-dados-san*
*Completed: 2026-07-14*
