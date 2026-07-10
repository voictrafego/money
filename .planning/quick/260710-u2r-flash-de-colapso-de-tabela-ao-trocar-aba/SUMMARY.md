---
type: quick
quick_id: 260710-u2r
slug: flash-de-colapso-de-tabela-ao-trocar-aba
status: complete
completed: 2026-07-10
files_modified: [app.py]
tests: 338 passed (./.venv/bin/python -m pytest -q)
commit: 4268eb9
---

# Quick 260710-u2r — Flash de colapso de tabela ao trocar de aba + artefato "0"

## O que foi feito

Na tela **Analisar uma ação** (`app.py`), as 3 sub-seções do resultado
(*Múltiplos & Crescimento*, *Valuation (DDM)*, *Fundamentos (10 anos)*) eram um
`st.tabs([...])`. O `st.tabs` mantém as abas inativas no DOM com `display:none` e o
Streamlit as **mede com largura 0 na 1a pintura**. Efeitos observados:

- **#2 (flash de colapso):** ao clicar numa aba nao-inicial, os `st.dataframe`
  (cenarios DDM, matriz de sensibilidade Ke x g, Fundamentos 10 anos) renderizavam
  por ~2s **so com a 1a coluna** (colunas de valores com largura 0) e depois se ajustavam.
- **#3 (artefato "0"):** o `st.bar_chart` de Fundamentos, medido a largura 0, aparecia
  reduzido so ao **eixo com o "0" da origem** — o "0 solto a esquerda" que o review flagou.

**Fix (raiz, nao paliativo):** troquei `st.tabs` por `st.segmented_control(...)` +
**render condicional** (`if/elif` por secao). Renderizando **so a secao ativa**, nada e
medido a largura 0 -> o flash e o "0" orfao somem na origem, para **todas** as tabelas e
para o grafico de uma vez.

So a **casca** mudou: `with tabN:` virou `if _aba == "...":`; o conteudo (nomes de coluna,
valores, `help=`, `column_config`, o `st.bar_chart`) ficou **igual** — nenhum recalculo,
nenhum valor do metodo tocado. `src/analista/**` intacto.

### Por que e seguro apesar do rerun

`st.segmented_control` dispara um rerun ao trocar de secao (o `st.tabs` era client-side).
Isso **nao** perde o resultado porque a analise ja e gateada por
`st.session_state["analise_ticker"]` (nao pelo retorno efemero do botao — ver comentario
em `app.py:836-840`) e `montar()` e `@st.cache_data`. E exatamente o mesmo padrao que os
toggles tecnicos abaixo ja usavam; nenhum custo de rerun novo alem do que ja existia.
Se o usuario clicar na secao ativa (deseleciona em modo single), o `or _secoes[0]` cai de
volta na 1a secao — sem tela vazia.

## Verificacao

- `./.venv/bin/python -m py_compile app.py` -> OK.
- `./.venv/bin/python -m pytest -q` -> **338 passed** (nenhuma falha nova).
- AppTest do padrao isolado (segmented_control + render condicional + dataframe + bar_chart)
  -> sem excecoes; a secao default renderiza; troca de secao nao quebra.
- **Smoke visual (manual):** abrir *Analisar uma acao* -> rodar um ticker (ex.: TAEE11) ->
  clicar entre *Multiplos & Crescimento* / *Valuation (DDM)* / *Fundamentos (10 anos)*
  varias vezes. Conferir que (a) **nenhuma coluna colapsa** na 1a pintura em nenhuma das
  tabelas e (b) **nao ha "0" solto** abaixo da tabela de Fundamentos (o `bar_chart` de
  Lucro Liquido renderiza com eixo completo).

## Notas (honestidade: eliminacao vs mitigacao)

- Esta e uma **eliminacao da causa-raiz** do lado do render (nao um paliativo de largura):
  ao nunca renderizar a secao inativa, o Streamlit nao tem o que medir a 0. Isso resolve
  #2 **e** #3 com uma so troca, incluindo as tabelas largas (sensibilidade, Fundamentos)
  que `st.column_config.Column(width=...)` ou trocar por `st.table` nao cobririam bem.
- **Sobre o artefato "0":** investiguei se era um `st.write`/expressao de magic renderizando
  `0`. Nao e: (i) a AST de `app.py` nao tem **nenhuma** expressao "solta" (bare expr), e
  (ii) o magic do Streamlit **nao** embrulha chamadas `st.*` (confirmado em
  `streamlit/runtime/scriptrunner/magic.py`, "Don't wrap function calls"). Reproduzir
  tabela + `bar_chart` em AppTest (largura cheia) **nao** emitiu nenhum elemento de texto
  "0". Ou seja, o "0" era **transitorio**: o eixo do `bar_chart` colapsado a largura 0 na
  troca de aba — o mesmo bug do flash. Com o render condicional o grafico nasce com largura
  cheia, entao o "0" orfao nao aparece. Trade-off aceito: a UI agora e um seletor
  segmentado (pilulas) em vez de abas — visual levemente diferente, comportamento equivalente.
- Fora de escopo (nao mexido): o warning de deprecacao `use_container_width` -> `width`
  (Streamlit remove apos 2025-12-31) aparece no app inteiro; e um item proprio, nao deste quick.
