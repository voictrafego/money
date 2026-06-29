---
phase: 14-padr-es-gr-ficos-checklist-de-sinais
plan: 04
subsystem: api
tags: [indicators, checklist, sinais, agregacao-read-only, wiring, firewall-copy]

# Dependency graph
requires:
  - phase: 14-padr-es-gr-ficos-checklist-de-sinais
    plan: 02
    provides: "_padroes (duplo topo/fundo) chamável e golden-testado isoladamente; contrato Padroes/PadraoGrafico"
  - phase: 14-padr-es-gr-ficos-checklist-de-sinais
    plan: 03
    provides: "_padroes estendida com OCO/OCO invertido (neckline inclinada por posição); 4 padrões de Murphy cobertos"
  - phase: 13-pivos-niveis-volume
    provides: "Rótulos discretos das famílias (rompimento_donchian, cruzamento, nivel_rsi, cruzamento_macd, rompimento_com_volume) já golden-testados"
provides:
  - "_checklist(tend, canais, mom, vol, padroes) — agregação READ-ONLY de 6 sinais liga/desliga, zero recálculo de indicador"
  - "Wiring aditivo de _padroes/_checklist em calcular(): SinaisTecnicos.padroes e .checklist populados ponta-a-ponta"
  - "tendencia/momentum/volume computados UMA vez em calcular e reusados no return (sem recomputo)"
  - "Firewall de copy D-01 provado por teste (sem linguagem imperativa nos rótulos) + degradação graciosa via calcular"
affects: [14-05-calibracao, 15-score, 16-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Agregação read-only duck-typed: _checklist só LÊ rótulos/flags (strings já validadas), nunca recalcula — booleanos derivam das strings"
    - "Wiring aditivo em calcular: famílias extraídas para variáveis (uma computação) e reusadas no return; padroes/checklist anexados sem reordenar kwargs"
    - "Detalhe do sinal 'padrao' = resumo neutro 'tipo:estado' (junção) ou 'nenhum' — chave estável, sem copy natural"
    - "Goldens duck-typed via SimpleNamespace isolam a agregação; integração/degradação exercidas via calcular()"

key-files:
  created: []
  modified:
    - src/analista/core/indicators.py
    - tests/test_indicators.py

key-decisions:
  - "_checklist lê rótulos via duck-typing (só acessa .rompimento_donchian/.cruzamento/.nivel_rsi/.cruzamento_macd/.rompimento_com_volume e padroes.lista) — zero acoplamento ao resto das dataclasses"
  - "Sinal 'volume' usa o campo direcional rompimento_com_volume (RESEARCH §Pattern 4), NÃO volume_acima_mm (este é insumo de _padroes p/ confirmar quebra de baixa)"
  - "'indisponivel' nunca conta como ativo (degradação) — a checagem é por allow-list de rótulos disparadores, não por != 'nenhum'"
  - "Teste anti-copy usa word boundary (\\b): 'sobrecomprado'/'sobrevendido' são rótulos neutros estáveis (contêm radical, não a palavra imperativa) e NÃO são copy"

patterns-established:
  - "_familias_stub (SimpleNamespace) + _sinal(checklist, nome) como harness do checklist read-only"
  - "Firewall de copy como teste de fase: proibidos imperativos por \\b-regex sobre nome+detalhe de todos os sinais"

requirements-completed: [SIG-01, PAT-01]

# Metrics
duration: ~8min
completed: 2026-06-29
---

# Phase 14 Plan 04: Checklist de sinais + wiring ponta-a-ponta Summary

**`_checklist(tend, canais, mom, vol, padroes)` agrega 6 sinais liga/desliga (rompimento, cruzamento_mm, rsi, macd, padrao, volume) LENDO rótulos JÁ computados pelas famílias (zero recálculo de indicador), e o wiring aditivo em `calcular()` popula os campos `padroes` e `checklist` de `SinaisTecnicos` ponta-a-ponta — `tendencia`/`momentum`/`volume` computados uma vez e reusados, padrões sobre o frame nominal (família de PREÇO, D-02). Firewall de copy D-01 provado (sem linguagem imperativa), degradação graciosa verde (frame curto → lista vazia + todos ativo=False, sem exceção). 271 testes verdes (266 prévios + 5 novos, zero rebaseline).**

## Performance
- **Duration:** ~8 min
- **Completed:** 2026-06-29
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `_checklist` em `indicators.py`: composição read-only de `Checklist(sinais=[Sinal(nome, ativo, detalhe)×6])`. Cada `ativo` deriva de uma allow-list de rótulos disparadores (`rompimento_donchian not in ("nenhum","indisponivel")`; `cruzamento in ("golden_cross","death_cross")`; `nivel_rsi in ("sobrecomprado","sobrevendido")`; `cruzamento_macd in ("cruz_alta","cruz_baixa")`; `any(p.estado=="confirmado")`; `bool(rompimento_com_volume)`). `detalhe` carrega o rótulo neutro já existente; o do `padrao` é o resumo `tipo:estado | ...` (ou `"nenhum"`).
- Guard de degradação (T-14-09): `padroes is None` → lista vazia tratada; nunca levanta.
- Wiring ADITIVO em `calcular()`: `tendencia`/`momentum`/`volume` extraídos para variáveis (computação única), `padroes = _padroes(pivos, nominal, volume, cfg)` (família de PREÇO → frame nominal) e `checklist = _checklist(...)` anexados aos kwargs do `return SinaisTecnicos(...)` sem reordenar os campos existentes. Chamadas existentes de `calcular` permanecem idênticas.
- 5 goldens novos: liga/desliga por rótulo, padrão confirmado ativa/em_formacao desliga/None degrada, integração via `calcular`, degradação de frame curto, e o firewall de copy D-01 (anti-imperativo por word boundary).

## Task Commits
1. **Task 1: `_checklist` + wiring de _padroes/_checklist em `calcular`** - `f7bf6e6` (feat)
2. **Task 2: goldens de checklist + integração + degradação graciosa** - `5592830` (test)

## Files Created/Modified
- `src/analista/core/indicators.py` - função `_checklist` (após `_padroes`); `calcular` reusa `tendencia`/`momentum`/`volume` e popula `padroes`/`checklist`.
- `tests/test_indicators.py` - helpers `_sinal`/`_familias_stub` (SimpleNamespace) + 5 goldens; imports `re`/`SimpleNamespace`.

## Decisions Made
- O sinal `volume` do checklist usa `rompimento_com_volume` (campo direcional, RESEARCH §Pattern 4), distinto de `volume_acima_mm` (insumo bidirecional consumido por `_padroes` para confirmar quebra de baixa). Os dois não foram confundidos.
- `_checklist` é duck-typed: acessa só os atributos de rótulo, permitindo goldens unitários via `SimpleNamespace` sem montar dataclasses completas.
- O teste anti-copy compara por **word boundary** (`\b`): `sobrecomprado`/`sobrevendido` contêm o radical de "compra/vende" mas são chaves estáveis neutras — não são copy imperativo. O firewall barra a forma imperativa/recomendatória ("compre", "venda", "comprar", "vender", "entre", "recomend"...).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Teste anti-copy por substring gerava falso positivo em rótulo neutro**
- **Found during:** Task 2 (`test_checklist_sem_copy_natural`)
- **Issue:** A checagem inicial por substring (`"compra" in texto`) acusava o rótulo neutro `sobrecomprado` (RSI) como copy imperativo — o rótulo é uma chave estável legítima, não recomendação.
- **Fix:** Trocada a checagem para word boundary (`re.search(rf"\b{termo}", texto)`) e a lista de proibidos para formas imperativas/recomendatórias reais; `import re` adicionado.
- **Files modified:** tests/test_indicators.py
- **Commit:** 5592830

## Issues Encountered
- Ambiente: a suíte roda no `.venv` do projeto (`.venv/bin/python -m pytest`); o `python3` global não tem pandas. Sem impacto no código.

## TDD Gate Compliance
Plano `type: execute` (não-TDD). Task 1 (implementação) → Task 2 (goldens + firewall + degradação) na ordem do plano; gate de degradação graciosa e firewall de copy presentes e verdes.

## Next Phase Readiness
- `SinaisTecnicos` agora expõe `padroes` (Padroes) e `checklist` (Checklist de 6 sinais) ponta-a-ponta via `calcular` — pronto para o plano 14-05 (calibração multi-ticker dos limiares) e para a Fase 15 (score que consome o checklist) consumirem read-only.
- Invariante mantida: 271 testes verdes (266 prévios + 5 novos), nenhum golden rebaselinado; firewall de copy e degradação graciosa verdes.

## Self-Check: PASSED

Arquivos e commits verificados (indicators.py, test_indicators.py; commits f7bf6e6, 5592830). Suíte: 271 testes verdes; `calcular` popula padroes/checklist; firewall de copy verde; degradação graciosa verde; SIG-01 + PAT-01 cobertos.

---
*Phase: 14-padr-es-gr-ficos-checklist-de-sinais*
*Completed: 2026-06-29*
