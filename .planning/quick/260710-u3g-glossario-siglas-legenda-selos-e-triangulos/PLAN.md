---
type: quick
quick_id: 260710-u3g
slug: glossario-siglas-legenda-selos-e-triangulos
created: 2026-07-10
source: .planning/reviews/260710-ux-review-navegador.md (#5, #6, #7)
priority: media
relacionado: 260704-kps (tooltips help= por coluna — já feito; NÃO cobre tabela transposta)
---

# Quick Task: Clareza — glossário de siglas (tabelas transpostas) + legenda de selos e triângulos

## Objetivo

Fechar as lacunas de clareza que o `260704-kps` (tooltips `help=` por coluna) não cobriu:
tabelas **transpostas** (sigla no rótulo de LINHA, onde o Streamlit não faz tooltip) e as
**legendas de cor** (selos e triângulos do gráfico).

## Escopo

1. **Tabela Múltiplos e Crescimento (transpostas)** — como o `help=` não pega rótulo de linha:
   - trocar as siglas cruas por rótulos com nome curto (ex.: `ML → Margem Líq. (ML)`,
     `EY → Earnings Yield (EY)`, `CDC → Cobertura de Dividendos (CDC)`, `DY rec. → DY recorrente`),
     **ou** adicionar uma linha/legenda de definições logo abaixo (usar `glossario.h()`), **ou**
     um `st.expander("O que cada sigla significa")`.
   - Definir explicitamente **CDC** (o mais opaco) e `g alto adotado` / `g estável (perpetuidade)`.
2. **Legenda dos selos 🟢🔵🟡** nas telas Garimpar e Ranking — legenda curta abaixo da tabela
   (verde/azul/amarelo = faixas de qualidade), reaproveitando o texto que Comparar já usa.
3. **Legenda dos triângulos** no gráfico de preço (5A) da tela Analisar — nomear os marcadores
   verde/vermelho na legenda do Plotly (ou removê-los se forem ruído redundante ao "Modo Trading").

## Restrições

- Só apresentação; nomes de método não mudam de valor. 338 testes verdes.
- Reusar `src/analista/glossario.py` (`h()`); não duplicar definições.

## Verificação

- Smoke: nas 3 telas, todo termo/símbolo tem definição alcançável (tooltip, rótulo ou legenda).
- `pytest -q` → 338 passed.
