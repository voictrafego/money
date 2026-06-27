---
phase: 06-integra-o-na-engine-composite-alerta-cli
reviewed: 2026-06-26
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/analista/report/report.py
  - config.yaml
  - tests/test_report.py
findings:
  critical: 1
  warning: 2
  info: 3
  total: 6
status: issues_found
---

# Phase 6: Code Review Report

**Depth:** standard
**Status:** issues_found

## Resumo

A árvore de decisão composite (D-01/D-02), o resample W-FRI (D-10) e o alerta OR-of-three (D-07/D-08/D-09) estão corretos e bem cobertos por golden. As frases-âncora D-05/D-06 batem verbatim, e o alerta degrada corretamente para `None` quando os sinais são `indisponivel`.

O problema central está na **assimetria da degradação graciosa**: quando o read técnico é degradado, `timing_resumo` e `alerta_reverificacao` colapsam para vazio/None corretamente, mas `timing_estado` colapsa para `"sem_tendencia"` e a `matriz_leitura` keya em cima desse estado fabricado — produzindo uma afirmação técnica confiante ("sem tendência técnica definida") onde, na verdade, não há leitura técnica. Há um caminho de entrada (preços achatados/illíquidos com ADX indefinido) em que isso vaza visivelmente na CLI.

## Critical Issues

### CR-01: Degradação inconsistente — matriz_leitura fabrica uma leitura técnica quando os sinais são "indisponivel" (e a guarda da CLI não pega o caso só-de-força)

**File:** `src/analista/report/report.py:165-167, 194, 378-379`

Na degradação, o ramo `if pos == "indisponivel" or forca == "indisponivel"` faz `a.timing_estado = "sem_tendencia"` e `a.timing_resumo = ""`. Logo abaixo, `a.matriz_leitura = _matriz_leitura(a.veredito, a.timing_estado)` keya em `"sem_tendencia"`. Como o veredito DDM depende de fundamentos e de `c.preco_atual` (não do OHLC), ele pode estar preenchido mesmo sem histórico de preço. Resultado: a engine emite uma afirmação técnica confiante para uma ação que simplesmente **não tem dado técnico** — saída internamente contraditória (`timing_resumo == ""` diz "sem read", `matriz_leitura` afirma um read). No default `"semanal"` (MM200 exige ~200 barras semanais / ~4 anos), a maioria das ações cai nesse caminho degradado e popula a matriz incorretamente — campo que a Phase 7 consome read-only.

A guarda da CLI (`a.sinais is None or a.timing_estado == "" or posicao_mm200 == "indisponivel"`) tem condição morta (`timing_estado == ""` nunca ocorre) e não cobre o caso `forca_adx == "indisponivel"` com `posicao_mm200` disponível (série achatada/illíquida, ADX = NaN). Caminho user-visible já shipado.

**Fix:** degradar a matriz junto com o timing (`a.matriz_leitura = ""` no ramo degradado) e basear o fallback da CLI em `not a.timing_resumo` em vez de só `posicao_mm200 == "indisponivel"`.

## Warnings

### WR-01: resample W-FRI roda antes da guarda única de degradação e assume DatetimeIndex + colunas OHLC

**File:** `src/analista/report/report.py:154-159`

O resample acontece **antes** de `indicators.calcular` (o "ponto único de degradação"). Com DataFrame não-vazio mas `RangeIndex`, `ohlc.resample("W-FRI")` levanta `TypeError`; sem alguma coluna OHLC, `.agg(...)` levanta `KeyError` — `analisar_acao` quebra antes da guarda, contrariando DATA-03. Gatilho real improvável (yfinance entrega índice datetime), mas a afirmação de "ponto único" não é verdadeira como está.

**Fix:** checar `isinstance(ohlc.index, pd.DatetimeIndex)` e presença das colunas OHLC antes do resample.

### WR-02: cobertura de teste não trava a degradação só-de-força (ADX indisponível com MM200 disponível)

**File:** `tests/test_report.py:246-256`

O único teste de degradação usa `ohlc_ajustado=None` (caminho `posicao_mm200 == "indisponivel"`, já coberto pela guarda). Nenhum teste exercita `forca_adx == "indisponivel"` com `posicao_mm200` disponível, nem afirma `matriz_leitura == ""` quando o read degrada. O bug CR-01 passa silencioso.

**Fix:** golden com série achatada (close ~constante por ≥200 barras, `base_temporal="diario"`) afirmando `timing_resumo == ""`, `matriz_leitura == ""` e ausência da linha de timing/matriz no markdown.

## Info

### IN-01: condição morta na guarda da CLI
**File:** `src/analista/report/report.py:378` — `a.timing_estado == ""` nunca é verdadeiro após `analisar_acao`. Remover ou substituir por `not a.timing_resumo`.

### IN-02: matriz_leitura vazia gera linha em branco espúria
**File:** `src/analista/report/report.py:386` — quando veredito DDM é `""`, `L.append(a.matriz_leitura)` insere linha em branco. `if a.matriz_leitura: L.append(...)`.

### IN-03: anotação de tipo frouxa no dict da matriz
**File:** `src/analista/report/report.py:206` — `Dict[tuple, str]` → `Dict[Tuple[str, str], str]`.

---

**Escopo de segurança:** sem vetores nesta fase (engine pura, sem rede/eval/IO persistente). Árvore composite, resample W-FRI, alerta OR-of-three e frases-âncora D-05/D-06 corretos e travados. Eixo de risco real: assimetria de degradação (CR-01).
