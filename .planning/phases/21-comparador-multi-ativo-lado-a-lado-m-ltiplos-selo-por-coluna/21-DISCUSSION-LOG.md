# Phase 21: Comparador multi-ativo lado a lado (múltiplos + selo por coluna) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-03
**Phase:** 21-comparador-multi-ativo-lado-a-lado-m-ltiplos-selo-por-coluna
**Areas discussed:** Onde vive, Layout lado a lado, Profundidade do selo, Ordenação & destaque

**Nota de fluxo:** o usuário estava ausente no momento da pergunta multi-seleção (timeout). Claude
apresentou recomendações fundamentadas nas 4 áreas cinzentas e o usuário aprovou o conjunto ("aprovado").

---

## Onde vive o comparador

| Option | Description | Selected |
|--------|-------------|----------|
| Novo menu no sidebar ("Comparar ações") | 5º item; N tickers livres, independentes do ticker analisado | ✓ |
| Promover o expander atual na Analisar | Reaproveitar o bloco existente preso ao `ticker_ativo` | |
| Ambos | Menu novo + expander | |

**User's choice:** Novo menu no sidebar; expander da Analisar fica intacto.
**Notes:** Roadmap pede "N tickers escolhidos pelo usuário" → view dedicada. Expander tem propósito diferente (pares de contexto do ticker analisado).

---

## Layout "lado a lado"

| Option | Description | Selected |
|--------|-------------|----------|
| Tickers em COLUNAS (transposto) | Métricas nas linhas, selo é a linha de cabeçalho (um badge por coluna) | ✓ |
| Tickers em LINHAS (formato atual) | Formato do embrião; selo vira uma coluna | |

**User's choice:** Colunas (transposto).
**Notes:** "lado a lado" + "selo por coluna" só fecham com tickers como colunas.

---

## Profundidade do selo por coluna

| Option | Description | Selected |
|--------|-------------|----------|
| Selo completo (quadrante) | Cor do BSD × veredito DDM → JOIA/VALUE TRAP/… (mais pesado: DDM por ticker) | ✓ |
| Só a cor de fundamento (BSD) | Leve, sem cruzar com preço | |

**User's choice:** Selo completo.
**Notes:** COMP-03 pede "o Selo da Phase 20", que É o quadrante. Custo do DDM por ticker é ⚠ a investigar no plano (reusar cache de `montar()` + cap de N).

---

## Ordenação & destaque

| Option | Description | Selected |
|--------|-------------|----------|
| Ordem de entrada fixa, sem sort, sem alvo | Fiel ao embrião e ao gate EXIBE-nunca-recomenda | ✓ |
| Sort neutro / destaque de foco | Permitir ordenar por coluna e/ou destacar um ticker | |

**User's choice:** Ordem de entrada fixa, sem sort, sem alvo.
**Notes:** Auto-ordenar soa a ranking. Nova regra de suficiência (≥2 tickers com dado) substitui `pares_suficientes` (que depende de alvo).

---

## Claude's Discretion

- Formato exato de render da tabela transposta (`st.dataframe` transposto vs. `st.columns` com card por ticker).
- Default do cap de N e placeholder de tickers do `text_input`.

## Deferred Ideas

- Sort neutro por coluna (tensão com o gate anti-recomendação).
- Destaque de um ticker "foco" no comparador livre.
- Colunas extras (veredito textual, preço atual, payout) — o selo já embute o veredito.
- Scanner/comparação sobre universo (não só tickers digitados) — fora de escopo do marco.
