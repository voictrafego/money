---
type: quick
quick_id: 260710-u1f
slug: feedback-de-carregamento-nas-analises
status: complete
completed: 2026-07-10
files_modified:
  - app.py
tests: 338 passed in 3.92s
---

# Quick Task: Feedback de carregamento nas análises (~35s sem sinal)

## O que foi feito

- **Analisar uma ação** (a mais lenta): trocado o `st.spinner` simples — que só embrulhava
  `montar()` (CVM+Yahoo) — por `st.status("Analisando {ticker}…", expanded=True)` com passos
  no corpo da página:
  1. "Baixando fundamentos (CVM) e preço/dividendos (Yahoo)…" → `montar()`
  2. "Selic/IPCA (BCB) para o custo de capital…" → `rf_capm()`
  3. "Calculando valuation (DDM + múltiplos)…" → `report.analisar_acao()`
  Ao final o status fecha (`state="complete"`, `expanded=False`); se faltar dado, fecha em
  `state="error"`. Agora as chamadas de rede que antes rodavam **fora** do spinner (BCB e
  valuation) também ficam sob feedback visível.
- **Garimpar (BSD)** e **Ranking**: já tinham `st.progress` durante o loop de coleta por ticker
  (a parte lenta). A barra deixava de aparecer (`prog.empty()`) antes da consolidação
  (Selic/BCB + BSD + regressão), criando um pequeno "vazio". Agora a barra é mantida em 100%
  com texto "Consolidando ranking…" / "Calculando ranking e preço-alvo…" e só é esvaziada
  imediatamente antes de renderizar a tabela.

## Restrições respeitadas

- `app.py` read-only quanto ao MÉTODO: nenhum recálculo, nome ou valor de coluna mudou — só
  apresentação/UX. `src/analista/**` não foi tocado.
- Zero novas dependências (`st.status`/`st.spinner`/`st.progress` são nativos do Streamlit).

## Verificação

- `./.venv/bin/python -m pytest -q` → **338 passed in 3.92s** (nenhuma falha nova).
- `./.venv/bin/python -m py_compile app.py` → OK (compila).

## Notas

- Commit atômico só de código: `1e6524e`. Docs/SUMMARY não commitados (a cargo do orquestrador).
- Untracked deixados intocados (`.DS_Store`, `docs/`, `Referencias/`, `03-PATTERNS.md`).
