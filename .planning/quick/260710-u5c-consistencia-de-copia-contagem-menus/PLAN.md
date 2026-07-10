---
type: quick
quick_id: 260710-u5c
slug: consistencia-de-copia-contagem-menus
created: 2026-07-10
source: .planning/reviews/260710-ux-review-navegador.md (#8, #9, #11, #12)
priority: baixa
---

# Quick Task: Consistência de cópia (contagem de menus, termos)

## Objetivo

Alinhar textos que ficaram desatualizados quando Comparar e Swing trade foram adicionados, e
suavizar dois termos que confundem.

## Escopo

1. **Contagem (confirmado no código):**
   - `app.py:725` — "Os **4 menus** ao lado continuam disponíveis." → refletir os 5 itens reais
     (ou reescrever sem número: "Os menus ao lado continuam disponíveis.").
   - `src/analista/glossario.py:13` — "**Três ferramentas**, na ordem do método:" → o tooltip só
     descreve 3 dos 6 itens; ou generalizar a frase ou incluir Comparar/Swing trade.
2. **"Garimpar carteira (BSD)" → "carteira" engana** (é triagem de uma lista, não das posições do
   usuário). Avaliar renomear rótulo/subtítulo para "Garimpar uma lista" / "Triagem de ações".
   ⚠️ "watchlist" fica como está (decisão do dono — ver review #10).
3. **"SELIC (CORTE DO DY)"** (sidebar) — rótulo críptico; avaliar "Piso de dividend yield (Selic)".
4. **"Swing trade (análise técnica)"** — nome em inglês destoa do produto de dividendos; avaliar
   "Análise técnica (timing)". (Decisão de posicionamento — confirmar com o dono.)

## Restrições

- Mudanças de texto/rótulo; nenhum comportamento de método. 338 testes verdes.
- Itens 2–4 têm componente de **decisão do dono** — não renomear sem confirmar.

## Verificação

- `grep` garante que não sobrou "4 menus"/"Três ferramentas" desalinhados.
- `pytest -q` → 338 passed.
