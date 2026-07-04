---
type: quick
quick_id: 260704-kps
slug: tooltips-help-em-todas-as-tabelas-do-app
created: 2026-07-04
---

# Quick Task: Tooltips (help=) em todas as tabelas do app

## Objetivo

Ao passar o mouse no cabeçalho de coluna de qualquer tabela do app, mostrar uma breve
explicação do termo. Reaproveita o glossário existente (`src/analista/glossario.py`, função
`h()`) e o mecanismo nativo `st.column_config.Column(..., help=...)` do Streamlit.

## Escopo

1. **`glossario.py`** — 20 chaves novas para termos de coluna: `selo`, `passa_filtros`,
   `bsd_maior_80`, `fatores_faltando`, `setor`, `pl`, `pvp`, `valor_mercado`,
   `nota_padronizada`, `preco_alvo`, `upside`, `veredito`, `lucro_liq`, `patrim_liq`, `fco`,
   `payout_col`, `valor_intrinseco_col`, `vp_dividendos`, `vp_residual`, `comparar_metricas`.

2. **`app.py`** — `column_config` com `help=` por coluna:
   - Pares (Analisar): Ticker, P/L, P/VP, ROE, DY, Valor de Mercado
   - Garimpar: Ticker, Ano-base, BSD, Selo, BSD>80, Passa filtros, Fatores faltando, Setor
   - Ranking: Ticker, Nota (0–100), Selo, Ano-base, Preço atual, Preço-alvo, Upside, Veredito
   - Histórico (Analisar): Lucro Líq., Patrim. Líq., FCO, ROE, Payout
   - DDM cenários: Valor intrínseco, VP dividendos, VP residual
   - Comparar: `help=` no subheader (tabela transposta — Streamlit não faz tooltip em rótulo de linha)

## Restrições

- `app.py` continua read-only (só apresentação; nenhum recálculo de método)
- Nenhuma coluna muda de nome ou valor
- 338 testes golden verdes; zero novas dependências

## Verificação

- `./.venv/bin/python -m pytest -q` → 338 passed
- Smoke visual: hover no cabeçalho "Passa filtros" (Garimpar) revela o "?" + tooltip markdown
