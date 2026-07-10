---
type: quick
quick_id: 260710-u4n
slug: padronizar-formatacao-numerica-br
created: 2026-07-10
source: .planning/reviews/260710-ux-review-navegador.md (#13, #14, #15, #16)
priority: media
---

# Quick Task: Padronizar formatação numérica (BR) e nits de exibição

## Objetivo

Unificar o formato numérico no padrão brasileiro (vírgula decimal, ponto de milhar) e corrigir
pequenos defeitos de exibição. Hoje o banner e os cards divergem no separador decimal.

## Escopo

1. **Separador decimal — causa-raiz confirmada:** `src/analista/report/report.py:198–207` monta os
   vereditos (SUBAVALIADA / SOBREAVALIADA / NO INTERVALO / VERIFICAR) com `{...:.2f}` cru (ponto),
   enquanto os cards usam o helper BR `_num()` (`app.py:281`, `presentation.py:38`). → usar o helper
   BR nesses vereditos (`R$ 40,31 dentro de R$ 31,32–52,63`).
2. **Percentuais** — avaliar vírgula decimal (`8,2%`) para bater com os valores em R$; ao menos
   manter consistência dentro da mesma tela.
3. **`-0.0%` (Upside)** — normalizar zero negativo para `0,0%` no render do Ranking.
4. **Fórmula da regressão** — `+ -11.17·payout` → `− 11,17·payout` (sinal). Ver `cli.py:176` e o
   render equivalente em `app.py`.
5. **Rótulos truncados** — cards `VALOR INTRÍNSEC…`/`DIVIDEND YIELD …`/`KE (CUSTO CAPIT…)` e a linha
   `Valor d` (→ "Valor de mercado") em Comparar: encurtar os rótulos ou alargar a coluna de rótulos.

## Restrições

- Só apresentação; valores calculados não mudam. 338 testes verdes.
- Atenção: se algum golden de report compara a string do veredito, **rebaselinar deliberadamente**
  os goldens afetados (documentar no SUMMARY).

## Verificação

- `pytest -q` verde (rebaseline consciente se a string do veredito for testada).
- Smoke: banner e cards mostram o MESMO número no MESMO formato (`R$ 40,31`).
