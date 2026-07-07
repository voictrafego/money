# Phase 16: Página Streamlit + Gráfico do Momento - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-30
**Phase:** 16-p-gina-streamlit-gr-fico-do-momento
**Areas discussed:** Layout da página, Overlays default + controles, Apresentação do veredito, Ticker/Timeframe + Atualizar

---

## Layout da página

| Option | Description | Selected |
|--------|-------------|----------|
| Gráfico topo + veredito abaixo | Candlestick full-width no topo + card de veredito abaixo (top-down) | ✓ |
| Números à esquerda + gráfico à direita | Coluna de score/níveis/checklist à esquerda, candlestick à direita (dashboard) | |
| Veredito topo + gráfico abaixo | Score/grade/níveis em destaque no topo, candlestick abaixo | |

**User's choice:** Gráfico topo + veredito abaixo
**Notes:** Candlestick respira (largura), espelha o padrão da aba Analisar; ênfase no gráfico evita "recomendação-first".

---

## Overlays default + controles

| Option | Description | Selected |
|--------|-------------|----------|
| S/R + MMs + níveis do setup | Ligados: S/R, médias, entrada/stop/alvo+Fib. Desligados: Bollinger/Donchian/padrões | ✓ |
| Só MMs + níveis do setup | Mais minimalista: só médias + níveis ligados | |
| Tudo ligado | Todos overlays ligados de saída | |

**User's choice (default overlays):** S/R + MMs + níveis do setup

| Option | Description | Selected |
|--------|-------------|----------|
| Expander acima do gráfico, estado próprio | Toggles em expander "⚙️ Overlays" + tec_estado próprio isolado | ✓ |
| Sidebar, estado próprio | Toggles na sidebar, estado próprio | |
| Reusar tec_estado da aba Analisar | Compartilha estado técnico com a aba Analisar | |

**User's choice (controles):** Expander acima do gráfico, estado próprio
**Notes:** Preserva o isolamento read-only do 4º menu (SWING-01); Murphy → estrutura/tendência primeiro.

---

## Apresentação do veredito

| Option | Description | Selected |
|--------|-------------|----------|
| Grade + barra de contribuição por família | Grade+score em destaque + barra de contribuição peso-a-peso | ✓ |
| Grade + tabela de decomposição | Grade+score + tabela densa (família/sub-score/peso/contribuição/detalhe) | |
| Gauge + expander de decomposição | Medidor do score + decomposição recolhida em expander | |

**User's choice (score/decomposição):** Grade + barra de contribuição por família

| Option | Description | Selected |
|--------|-------------|----------|
| Tabela de referências + checklist ✓/✗, disclaimer inline | Níveis em tabela "Referências de estudo (não são ordens)" + checklist ✓/✗ + disclaimer inline | ✓ |
| Métricas (st.metric) + checklist colorido | Entrada/stop/alvo/R:R como st.metric + chips coloridos | |
| Você decide | Deixar formato p/ planner/research | |

**User's choice (níveis/checklist):** Tabela de referências + checklist ✓/✗, disclaimer inline
**Notes:** Evita st.metric (risco de soar como alvo/ordem); copy condicional é gate de aceite (SWING-02).

---

## Ticker/Timeframe + Atualizar

| Option | Description | Selected |
|--------|-------------|----------|
| Input próprio na página swing | Campo de ticker dedicado, isolado da aba Analisar | ✓ |
| Compartilha o ticker da aba Analisar | Reusa o último ticker via session_state | |

**User's choice (ticker):** Input próprio na página swing

| Option | Description | Selected |
|--------|-------------|----------|
| Diário (default) + 1h + 30m + 5m | Todos os 4 timeframes, abrindo no diário | ✓ |
| Diário + 1h + 30m (sem 5m) | Tira o 5m do MVP | |
| Diário + 60m, default 60m | Foco intraday horário | |

**User's choice (timeframe):** Diário (default) + 1h + 30m + 5m

| Option | Description | Selected |
|--------|-------------|----------|
| Linha de controle acima do gráfico | Seletor + Atualizar + selo "~15min atraso · última barra" acima do candlestick | ✓ |
| Sidebar (timeframe+Atualizar) + selo no gráfico | Controles na sidebar, selo no canto do gráfico | |

**User's choice (Atualizar/selo):** Linha de controle acima do gráfico
**Notes:** Selo sempre visível; reusa o wrapper frame_intraday (cache TTL 300s, nonce, sem .clear() global) da Fase 12.

---

## Claude's Discretion

- Anotação visual exata dos padrões no candlestick + marcação da barra viva em formação.
- Tratamento de UI para "indisponível"/degradação graciosa (espelhar st.info da aba Analisar).
- Reuso vs extensão do `grafico.py` (linha diária → candlestick intraday).
- Cores/tema dos elementos do gráfico/checklist.

## Deferred Ideas

- Ponte read-only com o veredito fundamentalista do ticker (já no ROADMAP §Backlog).
- Padrões de continuação (triângulos, bandeiras) anotados no gráfico (backlog, falso positivo).
- Calibração fina de cores/tema e params curtos de indicadores por timeframe intraday.
