---
type: quick
quick_id: 260710-u3g
slug: glossario-siglas-legenda-selos-e-triangulos
status: complete
completed: 2026-07-10
files_modified: [app.py, src/analista/glossario.py]
tests: 338 passed (py_compile app.py OK)
---

# Quick 260710-u3g — glossário de siglas (tabelas transpostas) + legenda de selos e triângulos

Fecha os achados #5, #6 e #7 do review de UX `260710-ux` — as lacunas de clareza que o
`260704-kps` (tooltips `help=` por coluna) não cobriu. Só apresentação/UX: nenhum recálculo,
nenhum valor de célula muda.

## O que foi feito

### #5 — siglas nas tabelas TRANSPOSTAS (tela Analisar -> "Múltiplos & Crescimento")
Como o `help=` do Streamlit não pega rótulo de LINHA, foi adicionado um
`st.expander("O que cada sigla significa")` logo abaixo de **cada** tabela transposta, reusando o
glossário (`glossario.h(...)`) — sem tocar nos rótulos das linhas (evita rebaseline de golden):
- Abaixo de **Múltiplos** -> `h("tab_multiplos")`.
- Abaixo de **Crescimento e custo de capital** -> `h("tab_crescimento")` (já tinha g histórico,
  g por fundamentos, g alto, g estável, Beta, Ke completos).

`tab_multiplos` foi **ampliado** (reuso, não duplicação) para cobrir as duas siglas que faltavam:
- **CDC — Cobertura de Dividendos pelo Caixa**: `(FCO / nº de ações) / dividendo por ação`,
  definição confirmada no código (`core/multiples.py::cobertura_dividendos_caixa`, "CDC > 1 é
  adequado"). Era a mais opaca (`CDC = 1.50`).
- **DY rec. — DY recorrente**: DY sobre provento normalizado/sustentável.
- Também explicitados **Payout (último ano)** e **Payout p/ valuation (sustentável)** (os dois
  rótulos reais da tabela) e o rótulo de ROE.

### #6 — legenda dos selos nas telas Garimpar e Ranking
`st.caption` de legenda abaixo de cada tabela, com a régua de cor construída a partir do MESMO
config que o selo usa (`CFG["selo"]["cor"]` -> `selo.cor_do_bsd`), então fica fiel e sem hardcode:
verde >= 70 · azul 55-69 · amarelo 40-54 · vermelho < 40, com o eixo qualidade
(verde/azul = Alta; amarelo/vermelho = Baixa) — mesmo critério que Comparar já exibe em texto.

### #7 — legenda dos triângulos (gráfico de preço 5A, tela Analisar)
`st.caption` abaixo do gráfico Plotly (só quando há marcadores) nomeando o que os triângulos
representam: triângulo verde = fortalecimento (golden cross MM50xMM200 / rompimento de Donchian);
triângulo vermelho = enfraquecimento (death cross / perda da mínima). Copy consultiva (timing,
nunca ordem de compra/venda), coerente com o enquadramento técnico subordinado do app.

## Chaves de glossário
- **Nova chave:** nenhuma (abordagem por expander reusando os blocos existentes, para não duplicar).
- **Ampliada:** `tab_multiplos` (+CDC, +DY rec., +dois payouts, +rótulo ROE).
- Legendas de selo e triângulos ficam como texto de apresentação em `app.py` (a de selo puxa os
  cortes do `CFG` para não hardcodar; a de triângulo reusa `h("tec_indicadores")` no `help=`).

## Verificação
- `./.venv/bin/python -m pytest -q` -> **338 passed**.
- `python -m py_compile app.py src/analista/glossario.py` -> OK.
- `CFG["selo"]["cor"]` confirmado em `config.yaml` (verde_min/azul_min/amarelo_min).

## Diferido
- Nada. As três lacunas do escopo foram fechadas só com apresentação/UX.
