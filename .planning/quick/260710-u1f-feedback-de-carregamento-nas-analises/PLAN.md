---
type: quick
quick_id: 260710-u1f
slug: feedback-de-carregamento-nas-analises
created: 2026-07-10
source: .planning/reviews/260710-ux-review-navegador.md (#1)
priority: alta
---

# Quick Task: Feedback de carregamento nas análises (~35s sem sinal)

## Objetivo

Enquanto a análise busca dados (CVM + Yahoo + BCB), o usuário deve ver um indicador claro no
**corpo da página** — não só o ícone minúsculo do Streamlit no canto. Hoje "Analisar uma ação"
fica ~35s aparentemente parada; risco de abandono e de clique duplo.

## Escopo

1. **`app.py`** — envolver as chamadas de análise das telas Analisar / Garimpar / Ranking em
   `st.spinner("Analisando {ticker}… buscando CVM + Yahoo (pode levar ~30s)")` (ou
   `st.status(...)` com passos: "Baixando fundamentos (CVM)…", "Preço e dividendos (Yahoo)…",
   "Selic/IPCA (BCB)…", "Calculando valuation…").
2. Preferir `st.status` na tela **Analisar** (é a mais lenta) para dar a sensação de progresso.

## Restrições

- Só apresentação; nenhum recálculo do método muda.
- 338 testes golden verdes.
- Zero novas dependências.

## Verificação

- `./.venv/bin/python -m pytest -q` → 338 passed.
- Smoke: clicar Analisar → spinner/status aparece imediatamente no corpo e some ao renderizar.
