---
phase: 07-blindagem-processual-blind
plan: 02
subsystem: test-harness
tags: [pytest, xfail-strict, invariancia, inflacao, normalizacao, blind-02, blind-03]
requires:
  - "07-01: xfail_strict=true no pyproject, marcador `invariante`, completude imposta na coleta"
provides:
  - "tests/test_invariantes_v24.py — as DUAS DOENCAS escritas como codigo executavel"
  - "helpers_blindagem.choque_nominal(empresas, cfg, bps) — choque de inflacao completo (taxa + lucro nominal)"
  - "helpers_blindagem.carregar_config_producao() / cfg_e_empresas_do_snapshot() — consumidos pelo 07-05 (BLIND-06)"
  - "BLIND-02(b) e BLIND-03: alarmes que ficam VERDES sozinhos nas Fases 12 e 10"
affects: [tests/]
tech-stack:
  added: []
  patterns:
    - "choque de config por deepcopy + mutacao de chave (config e' injetado por dependencia — zero monkeypatch)"
    - "limiar de teste fixado na PRIMEIRA escrita com a medicao na mao, justificado inline (anti-Pitfall 5)"
key-files:
  created:
    - tests/test_invariantes_v24.py
  modified:
    - tests/helpers_blindagem.py
    - tests/classificacao.yaml
decisions:
  - "O ROE entra no choque via DADO (escalar lucro_liquido e dividendos por k=(roe0+d)/roe0), nao via knob — nao existe knob de ROE. `base_normalizada` e' homogenea de grau 1, entao a escala e' exata."
  - "patrimonio_liquido e num_acoes NAO sao tocados: o book esta a custo historico. VPA intacto — verificado. E' a historia economica correta (inflacao levanta o lucro nominal, nao o book)."
  - "Limiar de 5% (nao 2%): o piso estrutural da janela explicita com n_fade=10 e' -4,68%. Fixado ANTES do primeiro assert, com a medicao na mao — nao e' afrouxar tolerancia."
metrics:
  duration: ~35min
  completed: 2026-07-13
  tasks: 3
  commits: 3
---

# Fase 7 Plano 02: As duas doencas como codigo (BLIND-02 + BLIND-03) — Summary

Tres testes novos: um invariante algebrico que **passa** (a prova de que a invariancia a inflacao e'
possivel) e dois `xfail(strict=True)` que **falham de proposito** (as duas doencas) e viram verdes
**sozinhos** nas Fases 12 e 10. **Zero numero movido**: `git diff` em `src/` e `config.yaml` vazio.

## O numero que faltava: o Delta MEDIDO sob o choque COMPLETO

A pesquisa mediu o choque **sem** a perna do ROE. Com a perna do ROE (que e' o que o BLIND-02
corrigido exige), os deltas sao **muito maiores**:

| Ticker | V base | V +300bps (choque completo) | Δ medido | Δ da pesquisa (sem ROE) |
|---|---:|---:|---:|---:|
| **ITUB4** | 32,88 | **38,80** | **+18,02%** | +7,69% |
| BBAS3 | 43,89 | 63,84 | +45,44% | +3,65% |
| **BBDC4** | 13,37 | 22,00 | **+64,63%** | +1,96% ⚠️ |
| BBSE3 | 39,87 | 42,46 | +6,49% | +2,93% |

Verificado no mesmo experimento: `roe_chocado − roe_base = +0,0300` **exato** nos 4 tickers;
`patrimonio_liquido` e `num_acoes` **inalterados** (VPA intacto); `deepcopy` idempotente (os
objetos originais nao sao mutados).

**Achado que muda a leitura do Pitfall 1:** o BBDC4 **deixou de passar por acidente**. Sob o choque
literal (só `rf`+`g`) ele variava +1,96% — abaixo do limiar antigo de 2%, e um `xfail(strict)`
sobre ele daria XPASS. Sob o choque **correto** ele e' o **pior** dos quatro (+64,63%). O Pitfall 1
morreu com a correcao da spec — mas **o teste continua sendo sobre o ITUB4**, como o plano manda
(o caso do livro), e o arquivo nao menciona BBDC4 (`grep -c BBDC4` → 0).

**Por que a perna do ROE amplifica em vez de cancelar:** o `ke_teto = 0,13` satura e congela o `Ke`
(a perna do `rf` e' integralmente absorvida pelo clamp). O `g` sobe (spread `Ke−g` encolhe) **e** o
ROE sobe (excesso de ROE sobre o `Ke` congelado cresce). As duas pernas empurram o `V` **para
cima**, na mesma direcao. O `V` **sobe**, nunca desce — os asserts sao sobre `abs(Δ)`, jamais sobre
o sinal (Pitfall 2).

## Os tres testes

| Teste | Marcador | Estado hoje | Vira verde |
|---|---|---|---|
| `test_invariancia_inflacao_identidade_pb_justo` | `invariante` | **passed** (Δ < 1e-9, exato) | ja' passa — e' algebra |
| `test_invariancia_inflacao_engine_itub4` | `invariante` + `xfail(strict)` | **xfailed** (+18,02% > 5%) | **Fase 12** (quando o `ke_teto` sair) |
| `test_normalizacao_nao_pune_crescimento` | `invariante` + `xfail(strict)` | **xfailed** (haircut −9,09%) | **Fase 10** (PRIM-01) |

**A diferenca entre (a) e (b) E' a Doenca 1.** O mesmo choque de +300 bps: exatamente invariante na
identidade fechada `P/B justo = 1 + (ROE−Ke)/(Ke−g)`, e +18% na engine. (a) e' **knob-proof** (nao
le o config, nao passa pela engine) → nenhum knob pode faze-lo passar ou falhar. E' a guarda
permanente da ponte auditavel do ENG-08.

**BLIND-03 le `anos_media` e `winsor` do `config.yaml` de PRODUCAO** — a fuga por
`anos_media: 1` (que faria o teste passar sem consertar `normalizacao.py`) vira uma alteracao de
knob **visivel**, e o teste de orcamento do BLIND-06 (plano 07-05) a pega, porque `anos_media`
**nao** e' um dos 3 graus de liberdade. **O intertravamento BLIND-03 × BLIND-06 so' existe se os
dois nascerem na mesma fase** — a metade (b) vem no 07-05.

## Estado da suite

```
.venv/bin/python -m pytest -q -rxX
  411 passed, 38 deselected, 2 xfailed in 3,85s     # 0 failed, 0 errors, 0 XPASS

.venv/bin/python -m pytest -q -m "" --collect-only
  451 tests collected                                # 448 + 3
```

Os 2 xfailed sao **exatamente** BLIND-02(b) e BLIND-03 — as duas doencas, versionadas.

## Desvios do plano

### 1. [Rule 3 - Bloqueio] Os 2 testes da Task 2 tiveram que entrar no `classificacao.yaml` na propria Task 2

O plano registra os 3 testes no YAML na **Task 3**. Impossivel: a completude imposta pelo
`conftest.py` do 07-01 **quebra a coleta** de qualquer teste nao classificado → sem a entrada no
YAML, o `verify` da Task 2 nem roda. Registrei os 2 na Task 2 e o 3º na Task 3. **E' o mecanismo do
07-01 funcionando exatamente como projetado**, nao um bug.

### 2. [Nota de operacao] `pytest tests/arquivo.py` nao funciona mais neste repo

Rodar a suite **por path** dispara `ERROR: CLASSIFICACAO ORFA` — o `conftest` ve as ~450 entradas
do YAML sem teste coletado. **Use `-k`** (que coleta tudo e deseleciona), como os criterios de
aceite ja' faziam. Consequencia (esperada) do check de orfao do BLIND-01; vale registrar porque
custa 5 minutos de confusao a quem nao souber.

### 3. [Anti-goal honrado] Nenhum numero movido

`git diff --stat HEAD~3 -- src/ config.yaml tests/test_motores.py tests/test_backtest_bancos.py`
→ **vazio**. Nenhum teste existente foi tocado. O `V` de nenhum ticker se moveu.

## O que a proxima fase precisa saber

- **Fase 10 (PRIM-01):** quando `normalizacao.base_normalizada` parar de punir crescimento,
  `test_normalizacao_nao_pune_crescimento` **fica vermelho por XPASS**. A acao correta e' **remover
  o `xfail`** — nunca mexer no `PI_CICLO` nem no assert.
- **Fase 11:** **BLIND-02(b) NAO vira verde aqui**, mesmo depois de o `g` ser consertado. O
  `ke_teto` continua saturando e absorvendo a perna do `rf`. Se o executor da Fase 11 vir o teste
  ainda xfailed, isso e' o **esperado** — nao "consertar" o teste.
- **Fase 12 (KE-04):** quando o `ke_teto` sair, BLIND-02(b) vira verde. **Remover o `xfail`**, nao
  alterar o limiar. Sobra um piso estrutural de −4,68% (`n_fade = 10`) — dentro dos 5%.
- **Plano 07-05 (BLIND-06):** consumir `helpers_blindagem.carregar_config_producao()`; e o teste de
  orcamento **precisa** deixar `normalizacao.anos_media` fora dos graus de liberdade, senao a
  defesa (b) do Pitfall 5 nao existe.

## Commits

| Hash | Task | Descricao |
|---|---|---|
| `9d40ec0` | 1 | `choque_nominal()` — perna da taxa + perna do lucro nominal; medicao |
| `000926c` | 2 | BLIND-02 (a) invariante exato + (b) `xfail(strict)` na engine, limiar 5% |
| `5bc28d8` | 3 | BLIND-03 — normalizacao pune crescimento (`xfail`), knobs de producao |

## Self-Check: PASSED

- `tests/test_invariantes_v24.py` — FOUND
- `tests/helpers_blindagem.py` (modificado, `def choque_nominal` presente) — FOUND
- commits `9d40ec0`, `000926c`, `5bc28d8` — FOUND
- `pytest -q -rxX` → `411 passed, 38 deselected, 2 xfailed` (0 failed, 0 errors, 0 xpassed)
- `pytest -q -k invariancia_inflacao_identidade` → 1 passed
- `git diff --stat -- src/ config.yaml` → vazio
