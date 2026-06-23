---
phase: 03-gr-fico-de-pre-o-na-aba-analisar
reviewed: 2026-06-23T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - app.py
  - src/analista/ingest/prices.py
  - src/analista/core/fundamentals.py
  - src/analista/ingest/build.py
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-06-23
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

A Fase 3 adiciona uma série de preços diários de 5 anos (`serie_precos`) que flui de
`prices.coletar_mercado` → `build.montar_empresa` → `CompanyData` → gráfico Plotly no app.
A mudança é pequena e bem isolada, com tratamento de indisponibilidade (`st.info`) espelhando
o padrão já existente do preço atual.

A preocupação central é de **consistência de dados** — o valor declarado de projeto é que
"a mesma ação não pode parecer barata num menu e cara em outro sem explicação". O gráfico
desta fase coloca lado a lado três grandezas que **não estão na mesma base de preço**: a série
do gráfico é ajustada por proventos/desdobramentos (`auto_adjust=True`), enquanto o `preco_atual`
e a banda DDM não são. Isso é o BLOCKER abaixo. Há também ausência total de cobertura de teste
para o novo campo, num projeto que se sustenta em testes golden.

## Critical Issues

### CR-01: Série do gráfico (preço ajustado) é incomparável com o preço atual e com a banda DDM

**File:** `src/analista/ingest/prices.py:95,100` (em conjunto com `:88` e `app.py:137-153`)
**Issue:**
O gráfico foi criado explicitamente para comparar **preço observado × valor intrínseco (DDM)** —
título "Evolução do preço (5 anos) vs. valor intrínseco" e a banda verde `vmin..vmax`. Mas as três
grandezas plotadas não estão na mesma base de preço:

- `serie_precos = hist["Close"]` é coletado com `tk.history(period="5y", auto_adjust=True)` (linha 95).
  Com `auto_adjust=True`, o histórico é **retroajustado** por desdobramentos e proventos: os preços
  antigos são empurrados para baixo. Em uma pagadora de dividendos (todo o universo do app), o efeito
  é grande e acumula ao longo de 5 anos.
- `preco_atual` (linha 88) vem de `info["currentPrice"]`/`regularMarketPrice` — preço **bruto, não
  ajustado**.
- A banda DDM (`vmin/vmax`) é um valor intrínseco em R$ nominais correntes.

Consequência prática: o ponto mais recente da curva não bate com o `preco_atual` mostrado na métrica
logo acima do gráfico (o último ponto da série ajustada ≈ preço de hoje só por coincidência, porque o
ajuste é ancorado no fim), e os pontos antigos da curva ficam sistematicamente **abaixo** do que o
preço realmente foi. O leitor vê uma ação cuja "evolução" parece muito mais barata no passado do que
foi, e compara essa curva ajustada com uma banda DDM nominal — exatamente o tipo de "barata num lugar,
cara em outro sem explicação" que o `CLAUDE.md` proíbe. O hovertemplate ainda rotula como "R$ %{y:.2f}",
reforçando a leitura de que são reais nominais.

**Fix:**
Plotar preço **não ajustado** (o mesmo conceito do `preco_atual` e da banda DDM). Coletar a série com
`auto_adjust=False` e usar o close não ajustado, mantendo o histórico ajustado só para beta/retornos se
desejado:

```python
# prices.py — separar a base ajustada (beta/retorno) da série exibida (nominal)
try:
    hist = tk.history(period="5y", auto_adjust=False)
except Exception:
    hist = None

if hist is not None and not hist.empty:
    # "Close" com auto_adjust=False é o fechamento bruto (sem retroajuste de proventos);
    # mesma base do currentPrice e da banda DDM nominal.
    dm.serie_precos = hist["Close"].dropna()
    ...
```

Se o cálculo de beta/desempenho relativo precisar do ajuste, use a coluna `"Adj Close"` para esses
cálculos e reserve `"Close"` para `serie_precos`. Qualquer que seja a escolha, a série exibida e o
`preco_atual`/banda DDM precisam estar na **mesma base**, e isso deve ter um teste golden travando o
último ponto da série ≈ preço atual.

## Warnings

### WR-01: Nenhuma cobertura de teste para `serie_precos` em projeto guiado por golden tests

**File:** `src/analista/ingest/prices.py:58,100`, `src/analista/ingest/build.py:41`
**Issue:**
`grep -rln "serie_precos" tests/` não retorna nada. O `CLAUDE.md` define que "testes golden
existentes em `tests/` devem continuar passando" e o valor de projeto é consistência de dados. Um
campo novo que alimenta uma comparação visual preço × valor intrínseco entrou sem nenhum teste — em
particular sem nada que detecte a divergência de base do CR-01, nem o caminho `serie is None/vazia`.
**Fix:**
Adicionar teste em `tests/` que, com um `tk` mockado (já há `_fetch_info` mockável e os testes de
ingestão em `test_ingest_resolucao.py`), verifique: (a) `serie_precos` é preenchida e é uma `pd.Series`;
(b) `serie_precos.iloc[-1]` está próximo de `preco_atual` (trava o CR-01); (c) quando `hist` vem
vazio, `serie_precos is None` e o app não quebra.

### WR-02: Banda DDM com `vmin == vmax` vira um retângulo de altura zero (invisível)

**File:** `app.py:144-148` (origem em `report.py:115-117`)
**Issue:**
`vmin, vmax = min(valores), max(valores)` onde `valores` pode ter um único elemento (só `ddm_h`
ou só `ddm_constante` calculado — embora o caminho atual calcule ambos juntos, nada garante isso no
futuro). Com `vmin == vmax`, `add_hrect(y0=vmin, y1=vmax)` desenha um retângulo de altura zero: a
"banda" some e a anotação "Valor intrínseco (DDM)" aparece flutuando sem faixa. O usuário não recebe
nenhuma indicação de que o intervalo colapsou para um ponto.
**Fix:**
Quando `vmin == vmax`, usar `add_hline(y=vmin, annotation_text="Valor intrínseco (DDM)")` em vez de
`add_hrect`, ou expandir levemente a faixa para legibilidade. Mínimo:

```python
if a.vmin is not None and a.vmax is not None:
    if a.vmin == a.vmax:
        fig.add_hline(y=a.vmin, line_dash="dash", line_color="green",
                      annotation_text="Valor intrínseco (DDM)", annotation_position="top left")
    else:
        fig.add_hrect(y0=a.vmin, y1=a.vmax, line_width=0, fillcolor="green", opacity=0.12,
                      annotation_text="Valor intrínseco (DDM)", annotation_position="top left")
```

### WR-03: Janela de 5 anos do gráfico não respeita `ano_base` (mistura horizonte do gráfico com o da análise)

**File:** `src/analista/ingest/prices.py:95`, `src/analista/ingest/build.py:28,41`
**Issue:**
Toda a análise é ancorada em `ano_base`/`N_ANOS` (build.py:28 monta `anos = range(ano_base-n+1, ano_base+1)`),
e o sidebar do app diz "Janela: N anos · até ANO_BASE". O gráfico, porém, usa `period="5y"` fixo a
partir de *hoje*, independente de `ano_base` e de `N_ANOS`. Se `ano_base` for um ano fechado da CVM
(ex.: 2024) e hoje for 2026, a curva inclui ~2 anos posteriores à janela de fundamentos sobre os quais
a banda DDM foi calculada. O leitor compara um preço de 2026 com um valor intrínseco derivado de
fundamentos até 2024 sem aviso. É mais leve que o CR-01 (não é base de preço incompatível, é horizonte),
mas contradiz a promessa de "Janela: N anos até ANO_BASE" exibida ao usuário.
**Fix:**
Ou alinhar o `period` da série ao mesmo horizonte da análise (derivar de `N_ANOS`/`ano_base`), ou
rotular o gráfico deixando claro que a curva vai até hoje enquanto os fundamentos vão até `ANO_BASE`.
No mínimo, ajustar o `period` para `f"{N_ANOS}y"` em vez do literal `"5y"` para que o número no título
("5 anos") e a janela real não divirjam quando `N_ANOS != 5`.

### WR-04: `coletar_mercado` engole silenciosamente qualquer falha do histórico, mascarando bugs

**File:** `src/analista/ingest/prices.py:94-97,140-141`
**Issue:**
`except Exception: hist = None` (94-97) e o `except Exception: pass` (140-141) capturam *qualquer*
exceção, incluindo erros de programação (ex.: um typo de coluna, um `KeyError` introduzido numa refatoração
futura do bloco de beta/volume). O resultado é `serie_precos = None` (gráfico "indisponível") sem
nenhum log, então um bug real fica indistinguível de instabilidade do Yahoo. Num pipeline cujo valor é
fidelidade dos dados, falhas mudas são caras.
**Fix:**
Estreitar o `except` para as exceções esperadas do yfinance/rede, ou ao menos registrar via `logging`
o `repr(exc)` antes de cair para `None`/`pass`, para que falhas estruturais apareçam:

```python
except Exception as exc:
    logging.getLogger(__name__).warning("history() falhou p/ %s: %r", sym, exc)
    hist = None
```

## Info

### IN-01: Import `import yaml` fora do topo do arquivo

**File:** `app.py:23`
**Issue:**
`import yaml` aparece na linha 23, depois de `st.set_page_config` na linha 25? Não — está antes, mas
ainda assim isolado abaixo da atribuição `ROOT = ...` (linha 22) e separado do bloco de imports do
topo (linhas 9-20). Quebra PEP 8 (imports no topo) e a convenção do próprio arquivo.
**Fix:** Mover `import yaml` para o bloco de imports padrão (junto a `import os`, linhas 9-13).

### IN-02: `import pandas as pd` tardio dentro do laço de dividendos

**File:** `src/analista/ingest/prices.py:127`
**Issue:**
`import pandas as pd` está dentro do `try` do bloco de dividendos. O módulo já depende fortemente de
pandas (resample, pct_change em `_retornos_mensais`, `.dropna()` em `serie_precos`), então o import
tardio não economiza nada — só esconde a dependência e é reexecutado a cada chamada. A annotation
`Optional["pd.Series"]` (linha 58) inclusive já assume `pd` no namespace conceitual.
**Fix:** Mover `import pandas as pd` para o topo do módulo junto com os demais imports.

### IN-03: `serie.values`/índice tz-aware passado direto ao Plotly sem normalização

**File:** `app.py:139`
**Issue:**
`x=serie.index` usa o `DatetimeIndex` retornado pelo yfinance, que costuma ser **tz-aware**
(America/Sao_Paulo ou UTC). O Plotly lida com isso, mas o `hovertemplate` formata `%{x|%d/%m/%Y}` sem
considerar fuso, o que em datas próximas à meia-noite pode exibir o dia anterior/seguinte. Cosmético,
mas vale normalizar para data pura (sem hora/fuso) já que a granularidade é diária.
**Fix:** Normalizar antes de plotar, ex.: `x=serie.index.tz_localize(None).normalize()` (ou
`.date`), garantindo rótulos diários estáveis.

---

_Reviewed: 2026-06-23_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
