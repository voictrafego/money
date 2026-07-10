---
type: quick
quick_id: 260710-u2r
slug: flash-de-colapso-de-tabela-ao-trocar-aba
created: 2026-07-10
source: .planning/reviews/260710-ux-review-navegador.md (#2, #3)
priority: alta
---

# Quick Task: Flash de tabela colapsada ao trocar de aba + artefato "0"

## Objetivo

Nas abas *Valuation (DDM)* e *Fundamentos (10 anos)* da análise a fundo, ao clicar a tabela
renderiza ~2s **só com a 1ª coluna** (colunas de valores com largura 0) e depois se ajusta. Eliminar
o flash. Remover também o artefato "0" solto abaixo da tabela de Fundamentos.

## Escopo

1. **`app.py`** — investigar o render das tabelas dentro de `st.tabs`. Opções:
   - forçar largura das colunas via `st.column_config.Column(width=...)` ou `st.dataframe(...,
     use_container_width=True)` de forma que não colapse na 1ª pintura;
   - avaliar `st.table` (largura estável) para as tabelas pequenas (cenários DDM);
   - se persistir, considerar renderizar as abas sem `st.tabs` (ex.: `st.segmented_control` +
     container) para evitar o bug de largura-0 do dataframe em aba inativa.
2. **Artefato "0"** — localizar o widget/plot que emite o "0" abaixo da tabela de Fundamentos e
   suprimir (provável eixo/label órfão ou `st.write` de retorno).

## Restrições

- Só apresentação; método intacto. 338 testes verdes.

## Verificação

- Smoke visual: abrir Analisar → trocar entre as 3 abas várias vezes; nenhuma coluna colapsa e não
  há "0" solto.
- `pytest -q` → 338 passed.
