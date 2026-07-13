---
phase: 07-blindagem-processual-blind
plan: 03
subsystem: test-harness
tags: [pytest, ast, meta-teste, jackknife, overfit, blind-04]
requires:
  - "07-01: detector AST (`detectar_ticker_com_valor_cravado`), `quarentenados()`, completude na coleta"
  - "07-02: os 2 xfail(strict) das duas doencas — um deles e' detectado pelo detector (ver Desvio 1)"
provides:
  - "tests/test_blindagem_meta.py — BLIND-04a (a porta do overfit, fechada) + BLIND-04b (harness do jackknife)"
  - "helpers_blindagem.mediana_jackknife(valores) -> (mediana, desvio_max_ao_remover_1) — funcao pura"
  - "helpers_blindagem.xfail_estritos() — 2a porta de tolerancia do BLIND-04a, ESTRUTURAL"
  - "helpers_blindagem.HOLDOUT_V24 — o caminho do fixture que a Fase 14 (VAL-02) precisa criar"
affects: [tests/]
tech-stack:
  added: []
  patterns:
    - "meta-teste: o AST dos testes e' o artefato sob teste (nao a engine)"
    - "veredito adiado por `skip` (dependencia de fase), nunca por `xfail` (doenca) — sinal trocado e' pior que sinal ausente"
key-files:
  created:
    - tests/test_blindagem_meta.py
  modified:
    - tests/helpers_blindagem.py
    - tests/classificacao.yaml
decisions:
  - "A 2a porta de tolerancia do BLIND-04a e' `xfail(strict=True)`, nao um allowlist por nome. Um golden existe para ficar VERDE; um xfail estrito esta VERMELHO por contrato e quebra a suite por XPASS ao passar -> ninguem calibra um numero por essa porta. E' propriedade ESTRUTURAL (medida no AST), nao uma lista que cresce em silencio."
  - "NAO quarentenei `test_invariancia_inflacao_engine_itub4` (a instrucao literal do plano): quarentena-lo tira o alarme central do marco do run default e contradiz o proprio criterio de aceite da Task 2 (`2 xfailed`)."
  - "O limiar do jackknife (1 pp) fica [ASSUMIDO] e o veredito SKIPa. Inventar o numero hoje seria calibrar um knob contra dado inexistente."
metrics:
  duration: ~30min
  completed: 2026-07-13
  tasks: 2
  commits: 2
---

# Fase 7 Plano 03: BLIND-04 — a porta do overfit, fechada — Summary

A porta pela qual o overfit voltaria (`assert V(TICKER) == R$ x`) esta **fechada por um teste que
comprovadamente morde**, e o substituto legitimo do golden-por-ticker (jackknife sobre distribuicao)
esta **implementado e provado em dados sinteticos** — com o veredito **honestamente adiado** para a
Fase 14, porque hoje nao existe substrato sobre o qual ele signifique alguma coisa.

**ESTE PLANO NAO MOVEU NENHUM NUMERO** (`git diff -- src/ config.yaml` → vazio).

## O que o detector acha hoje

| Metrica | Medido |
|---|---:|
| Ofensores detectados (AST) | **27** |
| ...na **quarentena** (`golden_nivel`) | **26** |
| ...tolerados por **`xfail(strict=True)`** | **1** (`test_invariancia_inflacao_engine_itub4`, do 07-02) |
| **Novos** (ofensores fora de qualquer porta) | **0** ✅ |

O 07-01 media 26 ofensores. O 27º **nasceu no 07-02** — e e' o achado que reorientou este plano
(Desvio 1).

## O canario do BLIND-04a (a prova de que o teste morde)

```
# tests/test_tmp_ofensor.py  ->  ticker "ITUB4" + assert 32.88 == 32.88, classificado `contrato`
E  AssertionError: Teste(s) cravando `ticker == valor de nivel` FORA da quarentena:
E      tests/test_tmp_ofensor.py::test_tmp_crava_nivel_do_itau
1 failed, 452 deselected in 0.90s

# arquivo e entrada do YAML deletados:
1 passed, 451 deselected in 0.88s
```

Vermelho → verde. **A porta fecha.**

## Estado da suite

```
.venv/bin/python -m pytest -q -rs
  413 passed, 1 skipped, 38 deselected, 2 xfailed in 3,61s   # 0 failed, 0 errors, 0 XPASS
```

O `1 skipped` e' o veredito do jackknife, com a razao citando **Fase 14 / VAL-02**. Os `2 xfailed`
continuam sendo exatamente as duas doencas do 07-02 — **nenhuma delas saiu do run default**.

## Desvios do plano

### 1. [Rule 4 - decisao estrutural, resolvida sem checkpoint] O 27º ofensor e' um teste do 07-02 — e quarentena-lo seria destruir o alarme do marco

- **Achado em:** Task 1, na primeira medicao (antes de escrever qualquer assert).
- **O ofensor:** `test_invariantes_v24.py::test_invariancia_inflacao_engine_itub4` — tem o literal
  `"ITUB4"` **e** a constante de modulo `LIMIAR_INFLACAO = 0.05` chegando a um assert (a rota (c) do
  detector, criada no 07-01). **Falso positivo semantico:** o teste **nao crava valor em reais** —
  ele afirma uma **invariancia relativa** (`|ΔV/V| < 5%`). Nenhum nivel aparece.
- **O plano manda:** *"a correcao e' classificar o teste como `golden_nivel`, NUNCA afrouxar o
  detector"*. **Nao segui.** Quarentena-lo:
  1. **tira o BLIND-02(b) do run default** (`golden_nivel` e' deselecionado por `addopts`) — o
     alarme central do marco pararia de rodar, e o XPASS que deve gritar na Fase 12 nunca gritaria;
  2. **contradiz o proprio criterio de aceite da Task 2 deste plano** (`pytest -q` → **2 xfailed`).
     Com ele quarentenado seriam 1. **O plano se auto-refuta por essa rota.**
  3. contradiz a decisao explicita do 07-02: *"Os dois com xfail(strict) NAO sao golden_nivel:
     nenhum knob os satisfaz. Rodam no default."*
- **O que fiz:** uma **segunda porta de tolerancia, ESTRUTURAL** — `helpers_blindagem.xfail_estritos()`
  (AST: decorador `mark.xfail(..., strict=True)` com literal `True`).
  `novos = ofensores - quarentenados - xfail_estritos`.
- **Por que isto NAO e' uma brecha** (o teste do plano era proteger contra exatamente isso):
  um golden de calibracao **existe para ficar VERDE** — e' assim que ele trava o numero. Um
  `xfail(strict=True)` esta **VERMELHO por contrato** e o pytest o **auto-policia**
  (`xfail_strict = true`): no dia em que passar, a suite **QUEBRA por XPASS**. Nao ha como calibrar
  um numero por essa porta — o unico jeito de o teste "ficar verde" e' a doenca ser curada, e nesse
  dia a suite grita. E, ao contrario de um allowlist por nome (que cresceria em silencio), a porta e'
  uma **propriedade estrutural do codigo**: ninguem se auto-inclui sem declarar o proprio teste como
  falho-hoje-de-proposito, que e' **o oposto de calibrar**.
- **Rotas rejeitadas:** (a) allowlist por nome — hole que cresce em silencio; (b) tirar o literal
  `"ITUB4"` do corpo do teste movendo-o para um helper — isso e' **evasao do detector** (o mesmo
  vicio que o 07-01 trabalhou para fechar), e ensinaria o padrao errado ao repo.
- **Commit:** `c5489bd`

### 2. [Rule 1 - premissa do plano falsa] O outlier NAO faz o jackknife explodir — a mediana e' robusta por construcao

- **Achado em:** Task 2, medindo antes de escrever o assert.
- **O plano dizia:** *"injetando um outlier dominante, o `desvio_max_ao_remover_1` **explode** → o
  harness detecta um ponto load-bearing"*. **Falso.** Medido:

  | Amostra | `desvio_max_ao_remover_1` |
  |---|---:|
  | homogenea, 31 pontos | **0,05** |
  | **a mesma + outlier de 1000** | **0,05** (identico) |
  | ponte entre 2 clusters `[0, 0, 10, 100, 100]` | **45,0** |

- **Causa:** a mediana e' **robusta a outlier por construcao** — e' precisamente por isso que ela, e
  nao a media, e' a estatistica certa aqui. O desvio do jackknife e' limitado pelo **espacamento
  central**, nao pela magnitude da cauda. Um teste escrito sobre a premissa do plano **falharia**.
- **O que o jackknife realmente detecta** (e e' o que importa): o **ponto-ponte** — uma observacao
  sozinha no centro, entre dois grupos afastados. **Sem ela a mediana pula.** E' load-bearing no
  sentido literal, e e' **a forma exata da doenca do v2.3**: uma cesta minuscula em que um ticker
  carrega a calibracao.
- **O teste prova as tres verdades medidas** (homogenea → desvio minusculo; outlier → desvio
  **identico**; ponte → desvio 20x maior), incluindo a robustez ao outlier **como assert explicito** —
  se um dia o harness comecar a reagir a outlier, ele esta medindo *extremidade* em vez de
  *dependencia de um ponto*, e reprovaria cauda gorda em vez de calibracao apoiada num ticker so'.
- **Commit:** `f97eaa9`

### 3. [Rule 3 - bloqueio] `xfail_estritos()` e `mediana_jackknife()` entraram em `helpers_blindagem.py`

O plano lista `helpers_blindagem.py` nos arquivos da Task 2, nao da Task 1. O `xfail_estritos()`
(Desvio 1) e' pre-requisito do teste da Task 1 → entrou na Task 1. Mesmo mecanismo do Desvio 1 do
07-02: o `verify` da task nao roda sem ele.

## Handoff — FASE 14 (VAL-02), explicito

1. **Criar `tests/fixtures/holdout_v24.yaml`** — cesta estratificada, ≥ 6 por arquetipo + 10
   "dificeis" deliberados. **Contrato do fixture** (ja' escrito no teste): mapa
   `ticker -> {v_modelo, fair_value}`. No minuto em que o arquivo existir,
   `test_nenhum_ticker_e_load_bearing` **para de SKIPar e vira um veredito de verdade** — sem tocar
   uma linha de codigo de teste.
2. **FIXAR `LIMIAR_JACKKNIFE_PP`** (hoje `0.01`, marcado **`[ASSUMIDO]`** no topo do arquivo) **com a
   distribuicao real da cesta na mao**. Este e' o unico numero deste plano que **nao foi medido** — e
   esta etiquetado como tal, em maiusculas, no codigo.
3. **A metrica e' `V / FairValue`** (VAL-05), **jamais** contra o preco de mercado: um modelo cuja
   mediana bate o mercado e' um **espelho do mercado**, e um espelho nao acha acao barata.

## Handoff — as duas portas do BLIND-04a, para quem vier depois

Um teste novo que cravar `ticker == R$` **quebra a suite**. So' ha duas saidas, e **nenhuma delas e'
"afrouxar o teste"**:

| Porta | Semantica | Custo para quem entra |
|---|---|---|
| `golden_nivel` no `classificacao.yaml` | divida **declarada**, com a fase da morte escrita ao lado | sai do run default — **o golden para de proteger quem o escreveu** |
| `xfail(strict=True)` | o teste **falha de proposito** | quebra a suite por **XPASS** no dia em que passar |

## Commits

| Hash | Task | Descricao |
|---|---|---|
| `c5489bd` | 1 | BLIND-04a — meta-teste AST + `xfail_estritos()`; canario vermelho→verde |
| `f97eaa9` | 2 | BLIND-04b — `mediana_jackknife()` + invariante sintetico + veredito em SKIP |

## Self-Check: PASSED

- `tests/test_blindagem_meta.py` — FOUND
- `tests/helpers_blindagem.py` (`def mediana_jackknife`, `def xfail_estritos`) — FOUND
- commits `c5489bd`, `f97eaa9` — FOUND
- `pytest -q -rs` → `413 passed, 1 skipped, 38 deselected, 2 xfailed` (0 failed, 0 errors, 0 xpassed)
- `pytest -q -k crava_ticker` → 1 passed · `-k jackknife` → 1 passed · `-k load_bearing` → 1 skipped
- `grep -c "ASSUMIDO"` → 2 (≥1) · `grep -c "FASE 14|Fase 14"` → 8 (≥2) · regex/`v_preco` → 0
- `git diff --stat -- src/ config.yaml` → **vazio**
