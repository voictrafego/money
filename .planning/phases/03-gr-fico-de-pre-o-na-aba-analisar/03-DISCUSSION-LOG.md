# Phase 3: Gráfico de Preço na aba Analisar - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-23
**Phase:** 3-Gráfico de Preço na aba Analisar
**Areas discussed:** Representação do intrínseco, Posição do gráfico, Margem de segurança

---

## Representação do intrínseco

| Option | Description | Selected |
|--------|-------------|----------|
| Banda sombreada vmin–vmax | Faixa horizontal entre conservador e otimista; coerente com o "intervalo intrínseco" já mostrado na UI; honesto sobre a incerteza | ✓ |
| Duas linhas rotuladas | Linha do conservador (modelo H) + linha do otimista (g constante), cada uma rotulada; polui mais | |
| Linha única (ponto médio) | Uma linha no ponto médio do intervalo; mais limpo, mas esconde a faixa de incerteza | |

**User's choice:** Banda sombreada vmin–vmax
**Notes:** Mantém coerência com as métricas e o veredito que já exibem o intervalo `R$ vmin–vmax`.

---

## Posição do gráfico

| Option | Description | Selected |
|--------|-------------|----------|
| 4º sub-tab "📉 Preço (5 anos)" | Novo sub-tab ao lado dos existentes; segue padrão, não empurra conteúdo | |
| Topo, abaixo do veredito | Logo abaixo das 5 métricas e do veredito colorido, antes dos sub-tabs; máxima visibilidade | ✓ |
| Dentro do sub-tab Valuation (DDM) | Junto dos cenários DDM; contextual mas menos visível | |

**User's choice:** Topo, abaixo do veredito
**Notes:** Quer a margem de segurança visível de cara, junto do veredito.

---

## Margem de segurança

| Option | Description | Selected |
|--------|-------------|----------|
| Limpo: preço + banda intrínseca | Linha de preço + banda com cor sutil; desconto/prêmio pela posição relativa; baixo risco visual | ✓ |
| Sombrear desconto/prêmio + marcar preço atual | Sombreia área entre preço e intrínseco (verde/vermelho) + ponto do preço atual; mais expressivo, mais trabalho | |
| Só preço + referência, sem extra | Apenas linha + referência, sem destaque; mínimo absoluto | |

**User's choice:** Limpo: preço + banda intrínseca
**Notes:** Comunicar pela posição relativa, sem sombrear área nem marcar ponto.

---

## Claude's Discretion

- Conteúdo do hover, títulos/eixos, paleta exata, altura do gráfico.
- Tipo do campo que carrega a série em `DadosMercado`/`CompanyData` (pandas Series vs listas).

## Deferred Ideas

- Sombrear desconto/prêmio + marcar preço atual — considerado e descartado nesta fase (preferência por gráfico limpo); possível refinamento futuro.
- Seletor de período além de 5a e gráficos nas Telas 2/3 — fora do escopo de v1.1.
