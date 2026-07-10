---
type: quick
quick_id: 260710-u5c
slug: consistencia-de-copia-contagem-menus
status: complete
completed: 2026-07-10
files_modified: [app.py, src/analista/glossario.py]
tests: 338 passed (pytest -q, ~3.2s) — sem rebaseline de golden
commit: 7d8d70b
---

# Quick 260710-u5c — Consistência de cópia + renomeações aprovadas

## Renomeações aplicadas (decisões do dono)

1. **Menu**: "Garimpar carteira (BSD)" → **"Garimpar ações (BSD)"** (`app.py:623`).
   Subtítulo da tela alinhado: "Garimpar uma carteira — …" → "Garimpar ações — …" (`app.py:1321`).
2. **Sidebar**: "Selic (corte do DY)" → **"Selic (piso do dividend yield)"** (`app.py:628`).
3. **Menu**: "Swing trade (análise técnica)" → **"Análise técnica (timing)"** (`app.py:624`).
   Subtítulo da tela alinhado: "Swing trade — leitura técnica…" → "Análise técnica (timing) — leitura do candlestick…" (`app.py:1577`).

"watchlist" mantida como está (não mexida).

## Roteamento — ajuste e verificação

O `app.py` roteia por `modo.startswith(...)`. A única rota afetada foi a ex-"Swing":
`elif modo.startswith("Swing")` → **`elif modo.startswith("Análise técnica")`** (`app.py:1576`).
As demais renomeações preservam o prefixo de rota ("Garimpar…" continua começando com "Garimpar";
a Selic é label de métrica, sem rota).

Verificação por leitura do código (as 6 rotas, na ordem do if/elif):

| Item do menu | Condicional que casa | Tela |
|---|---|---|
| Início | `startswith("Início")` (827, bloco `if` próprio) | Home |
| Analisar uma ação | `startswith("Analisar")` (834) | Analisar |
| Garimpar ações (BSD) | `startswith("Garimpar")` (1320) | Garimpar |
| Ranking por múltiplos | `startswith("Ranking")` (1411) | Ranking |
| Comparar ações | `startswith("Comparar")` (1548) | Comparar |
| Análise técnica (timing) | `startswith("Análise técnica")` (1576) | Técnica |

**Colisão Analisar × Análise técnica descartada:** "Análise" (com acento, termina em `-e`) NÃO
começa com "Analisar" (sem acento, termina em `-ar`) — `"Análise técnica (timing)".startswith("Analisar")`
é `False`. Cada um dos 6 itens casa exatamente uma condicional. O `st.radio` é stateless (1º item
= default), não há default em `session_state` referenciando texto antigo.

## Correção de contagem (#8, #9)

- `app.py:730` — "Os **4 menus** ao lado continuam disponíveis." → "Os menus ao lado continuam
  disponíveis." (número removido; robusto a futuras adições de menu).
- `src/analista/glossario.py:13` (tooltip "menu") — "**Três ferramentas**, na ordem do método:" →
  "**As ferramentas, na ordem do método:**"; item 2 renomeado para "Garimpar ações (BSD)"; adicionada
  linha final citando **Comparar ações** e **Análise técnica (timing)** como apoios complementares
  (agora cobre os 6 itens, sem cravar um número).

## Golden / testes

- **Nenhum golden rebaselinado.** Nenhum teste travava os rótulos de menu/sidebar nem o texto do
  tooltip "menu". `tests/test_glossario.py` só valida chaves `tec_*` e ausência de linguagem de ordem.
- `pytest -q` → **338 passed**. `py_compile` OK.

## Fora de escopo (não alterado, por decisão de escopo)

Ocorrências de "corte do DY" e "Swing" em superfícies internas (não-UI Streamlit) foram deixadas
intactas: `src/analista/cli.py:68,93` (saída de CLI/stderr), `src/analista/ingest/macro.py:3`
(docstring), e a classe de engine `SetupSwing` (`src/analista/report/setup.py`, `tests/`). A tarefa
visava os rótulos do app; mexer nessas quebraria/poluiria a engine sem ganho de UX.

## Self-Check: PASSED
- app.py e glossario.py modificados e commitados em 7d8d70b.
- 6 rotas verificadas por leitura; 338 testes verdes.
