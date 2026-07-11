---
phase: 01-classificador-de-arqu-tipo-roteamento
plan: 06
subsystem: classificador-de-arquetipo
tags: [arquetipo, hard-route, resolucao, ticker-map, over-match, tdd, gap-closure]
requires: [ARQ-01]
provides:
  - "MDIA3 (M. Dias Branco, Alimentos) roteada corretamente — fora de 'financeira'"
  - "resolução determinística de MDIA3 via ticker_map (precedência sobre match por nome)"
  - "hard-route financeiro por LIMITE DE PALAVRA (defesa anti over-match de substring embutida)"
affects:
  - "qualquer ticker de consumo cujo nome contenha fragmento colidente com nome de banco no cadastro CVM"
tech-stack:
  added: []
  patterns:
    - "override {cd_cvm, setor} no ticker_map fecha a resolução por nome envenenada (atalho 100% offline)"
    - "casamento de token de setor por \\b (word boundary) + sufixo de plural, não substring solta"
key-files:
  created: []
  modified:
    - src/analista/core/arquetipo.py
    - config.yaml
    - data/ticker_map.json
    - tests/test_arquetipo.py
decisions:
  - "Causa-raiz do misroute do MDIA3 é de RESOLUÇÃO (empresa errada), não do casamento do classificador: o estágio 'contém' de universe._resolver_base casou o fragmento CVM 'rci' (sobra de 'Banco RCI Brasil S.A.' após stripar tokens jurídicos) dentro de 'comeRCIo' no nome do MDIA3 → cd 21466 → setor 'Bancos'. O token 'banco' casava CORRETAMENTE nesse setor envenenado."
  - "Fix operativo = override determinístico no ticker_map (MDIA3 → {20338, 'Alimentos'}), que tem precedência sobre o match por nome e usa o atalho 100% offline do resolver."
  - "Defesa em profundidade (T-0106-01): hard-route financeiro passa a casar por limite de palavra (\\b) com plural tolerado — token curto não casa dentro de palavra não-financeira (ex.: 'banco' ⊄ 'Bancoreal'). NÃO afrouxa banco/seguradora/intermediação genuínos (plural coberto)."
metrics:
  duration: 0h20m
  tasks: 1
  files: 4
  completed: 2026-07-11
---

# Phase 1 Plan 06: Fechamento do Over-match do Hard-route Financeiro (MDIA3) — Achado 1b Summary

Corrigiu o misroute do **MDIA3** (M. Dias Branco, alimentos), que o audit classificou como
`financeira`. A causa-raiz REPRODUZIDA não foi um bug de substring no classificador (como
supunha o `<interfaces>` do plano), mas um **erro de resolução de empresa**: o override
determinístico no `ticker_map` fecha a porta, e o casamento por limite de palavra no hard-route
adiciona defesa em profundidade.

## Causa-raiz reproduzida (reproduce-first, W5)

Rodando a resolução real que `build.montar_empresa('MDIA3', ...)` dispara:

```
resolver('MDIA3', 'M. Dias Branco S.A. Industria e Comercio de Alimentos')
  → cd_cvm 21466, setor 'Bancos'   (BANCO RCI BRASIL S.A.)
```

- **Setor real capturado que chegou ao classificador:** `'Bancos'` (envenenado).
- **Token que casou:** o `financeiro_token` **`banco`** dentro de `'bancos'` — casamento
  **correto** para um setor que diz "Bancos"; o classificador não estava errado.
- **Onde nasceu o veneno:** MDIA3 não estava no `ticker_map`, então resolvia por NOME. O
  estágio **"contém"** de `universe._resolver_base` casa nomes CVM cujo `_norm` é substring do
  alvo. `'BANCO RCI BRASIL S.A.'` vira `_norm='rci'` (após stripar `banco`/`brasil`/`s.a.`), e
  `'rci'` é substring de `come`**`rci`**`o` no nome do MDIA3. Escolhendo o **nome mais curto**
  (`argmin` no comprimento), `'rci'` (3 chars) venceu → cd 21466 (Banco RCI Brasil) → `'Bancos'`.

Ou seja: o over-match acontece na camada de RESOLUÇÃO (empresa errada), não no `tok in setor`
do classificador. O plan-checker (W5) antecipou exatamente isto.

## O que mudou

1. **`data/ticker_map.json`** — `MDIA3 → {cd_cvm: 20338, setor: "Alimentos"}` (mesma forma do
   VULC3). Precedência sobre o match por nome; dispara o atalho 100% offline do `resolver`
   (`cd_override + setor_override → retorno imediato`, sem cadastro/rede). Resolução determinística.
2. **`src/analista/core/arquetipo.py`** — novo `_setor_casa_token`: casa `financeiro_tokens` por
   `\b` (limite de palavra) com sufixo de plural tolerado (`Bancos`/`Seguradoras`), em vez de
   substring solta. Defesa em profundidade (T-0106-01) contra token curto embutido em palavra
   não-financeira. Frase multi-palavra (`intermediação financeira`) casa como frase.
3. **`config.yaml`** — comentário documentando o casamento por limite de palavra em `financeiro_tokens`.
4. **`tests/test_arquetipo.py`** — 3 goldens.

## Tasks

| Task | Fase | Commit | Arquivos |
|------|------|--------|----------|
| 1 (RED) | goldens de resolução + fim-a-fim + defesa de substring falham | 9715d80 | tests/test_arquetipo.py |
| 1 (GREEN) | override MDIA3 no ticker_map + hard-route por limite de palavra | b980974 | data/ticker_map.json, arquetipo.py, config.yaml |

## Guard rail (financeiras genuínas preservadas)

Verificado com resolução + classificação reais:

| Ticker | setor resolvido | arquétipo |
|--------|-----------------|-----------|
| ITUB4 | Bancos | **financeira** ✓ |
| BBAS3 | Bancos | **financeira** ✓ |
| MDIA3 | Alimentos | pagadora_regulada (≠ financeira) ✓ |

`test_banco_vira_financeira`, `test_seguradora_vira_financeira`,
`test_financeira_hard_route_soberana_ignora_quantitativo` seguem verdes (plural coberto pela
regex `\btoken(?:s|es)?\b`).

## Deviations from Plan

None — o plano previa `podendo combinar as duas` causas; o reproduce apontou a causa (b)
resolução como operativa, e a (a) casamento foi aplicada como defesa em profundidade, exatamente
como a Task action autorizava. Nenhuma regra 1-4 disparada; nenhum gate de autenticação.

## TDD Gate Compliance

Sequência RED → GREEN confirmada no git log:
- RED: `test(01-06): reproduce MDIA3 over-match...` (9715d80) — 3 falhas reproduzem o achado
- GREEN: `fix(01-06): MDIA3 fora de financeira...` (b980974) — suíte verde

## Verification

- `python -m pytest tests/test_arquetipo.py -q` → 24 passed
- `python -m pytest -q` → **389 passed, 0 failed** (baseline 386 + 3 novos; nenhum regride)
- `git diff --stat` confirma só 4 arquivos tocados; `ddm.py`/`selo.py` **intocados** (firewall preservado)
- `grep -n "MDIA3" tests/test_arquetipo.py` mostra os goldens novos; `grep -n "20338" data/ticker_map.json` confirma a entrada

## Self-Check: PASSED

Todos os arquivos modificados existem no disco; ambos os commits (9715d80, b980974) confirmados no git log.
