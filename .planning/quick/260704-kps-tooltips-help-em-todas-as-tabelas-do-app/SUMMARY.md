---
type: quick
quick_id: 260704-kps
slug: tooltips-help-em-todas-as-tabelas-do-app
status: complete
completed: 2026-07-04
files_modified:
  - src/analista/glossario.py
  - app.py
tests: 338 passed
---

# Summary: Tooltips (help=) em todas as tabelas do app

## O que foi feito

- **`glossario.py`**: +20 chaves de definição curta (markdown) para os termos das colunas
  das tabelas — `selo`, `passa_filtros`, `bsd_maior_80`, `fatores_faltando`, `setor`, `pl`,
  `pvp`, `valor_mercado`, `nota_padronizada`, `preco_alvo`, `upside`, `veredito`, `lucro_liq`,
  `patrim_liq`, `fco`, `payout_col`, `valor_intrinseco_col`, `vp_dividendos`, `vp_residual`,
  `comparar_metricas`.
- **`app.py`**: `column_config={col: st.column_config.Column(col, help=h(chave))}` ligado em
  todas as tabelas largas (Pares, Garimpar, Ranking, Histórico, DDM cenários). Na tela
  **Comparar** (tabela transposta) a explicação foi para o `help=` do `st.subheader`, já que
  o Streamlit não expõe tooltip em rótulo de linha. Reaproveitou chaves já existentes
  (`ticker`, `roe`, `dy`, `preco`, `bsd`, `ano_base`).

## Verificação

- `pytest -q` → **338 passed** (engine e goldens intactos; mudança é só de apresentação).
- Compile OK; todas as 26 chaves referenciadas resolvem (nenhuma retorna `None`).
- Smoke visual no navegador: hover no cabeçalho **"Passa filtros"** da tela Garimpar mostra
  o ícone "?" e o tooltip com markdown renderizado.

## Notas

- `app.py` permaneceu read-only; nenhum nome/valor de coluna mudou.
- Zero novas dependências (mecanismo nativo do Streamlit).
