---
type: quick
quick_id: 260710-u4n
slug: padronizar-formatacao-numerica-br
status: complete
completed: 2026-07-10
commit: 3a04ac8
files_modified:
  - app.py
  - src/analista/report/report.py
  - src/analista/cli.py
tests: 338 passed (sem falhas novas); py_compile OK
golden_rebaseline: nenhum
---

# Quick 260710-u4n — Padronizar formatacao numerica (BR) + nits

## O que foi feito

### #13 — Separador decimal do veredito (principal)
`src/analista/report/report.py` construia os vereditos (SUBAVALIADA / SOBREAVALIADA /
NO INTERVALO / VERIFICAR) com `{...:.2f}` cru (ponto US), divergindo dos cards que ja usavam
formatacao BR (`fmt_rs`). O helper existente do modulo `_num()` NAO e BR (usa ponto — e a
superficie CLI, documentada como intencional em `presentation.py`). Por isso adicionei um helper
BR local `_br()` (milhar `.`, decimal `,`, espelhando `fmt_rs`) e apliquei nos 5 numeros dos
vereditos. Resultado: `NO INTERVALO — preco R$ 40,31 dentro de R$ 31,32-52,63`.
- Nenhum VALOR calculado mudou — so formato de exibicao.
- O PREFIXO do veredito (consumido por `selo.faixa_do_veredito` / `_matriz_leitura` via
  `startswith`) permanece intacto; nada parseia os numeros de dentro da string.

### #14 — `-0.0%` no Upside (Ranking)
`app.py:fmt_pct` normaliza zero-negativo: se o valor arredondado as casas exibidas da 0, forca
`0.0` (positivo). `fmt_pct(-0.0001)` -> `0.0%`. Correcao geral em todos os percentuais do app.

### #15 — Sinal duplo na formula da regressao
`P/L = 24.51 + -11.17.payout + -35.46.ROE` -> cada termo agora imprime `menos` quando o
coeficiente e negativo: `24.51 - 11.17.payout - 35.46.ROE`. Corrigido em `app.py` (o render que
aparece no navegador) e espelhado em `src/analista/cli.py` (saida stderr do `rank`).

### #16 — Rotulos truncados
- Cards da analise: `Valor intrinseco (DDM)` -> `Intrinseco (DDM)`; `Ke (custo capital)` ->
  `Ke (custo)`. Encurtados o suficiente para caber na coluna (help/tooltip preserva o significado).
- Comparar: coluna `Valor de Mercado` (que truncava para `Valor d`) recebeu `width="medium"`,
  alargando a coluna em vez de encurtar o rotulo.

## Goldens rebaselinados
Nenhum. Verificado que:
- Os unicos usos de strings de veredito em `tests/` (`test_report.py:116,128`) sao inputs
  fixos passados a `_matriz_leitura`, que so le o prefixo/token — o formato numerico e irrelevante.
- `test_selo.py` testa apenas prefixos (`startswith`).
- Nenhum teste assere a string da regressao (`app.py`/`cli.py` — st.caption/stderr).
- Suite completa: 338 passed antes e depois.

## Diferido (fora de escopo / bloqueado)
- Rotulo do card Dividend Yield (`DIVIDEND YIELD (RECORRENTE)` truncado): o texto do label vem
  de `presentation.header_dy` e e contrato de golden (`test_presentation_multiticker.py:117,162`
  asserem `"Dividend Yield (recorrente)"` / `"(trailing)"`). Encurta-lo exigiria rebaselinar um
  golden de TEXTO, fora da regra de rebaseline deste quick (so separador decimal). Deixado como
  esta; requer decisao deliberada para mudar o contrato do label.
- Percentuais com virgula (`8,2%`) (item opcional 5 do plano): deixado como esta por ser de maior
  risco de churn e menor prioridade que os itens 1-4.

## Verificacao
- `./.venv/bin/python -m pytest -q` -> 338 passed.
- `py_compile app.py src/analista/report/report.py src/analista/cli.py` -> OK.
- Smoke dos helpers: veredito `R$ 40,31 dentro de R$ 31,32-52,63`; `_br(1234.5)` -> `1.234,50`;
  `fmt_pct(-0.0001)` -> `0.0%`; termo regressao negativo -> `- 11.17.payout`.
