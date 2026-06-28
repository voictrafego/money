# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 + auditoria/correção de dados (shipped 2026-06-28)
- 🚧 **v2.0 — Comercialização (produto cobrável)** — fases a definir via `/gsd-new-milestone`

> Detalhes completos das fases concluídas (v1.0–v1.3) no snapshot `.planning/milestones/v1.3-ROADMAP.md` e requisitos em `.planning/milestones/v1.3-REQUIREMENTS.md`.

## v2.0 — Comercialização (produto cobrável)

**Goal:** Transformar o protótipo de usuário único num produto que cobra — auth, trial 7d →
assinatura mensal (Asaas), gate de acesso e multiusuário — posicionado como software educacional
(sem recomendação).

**Decisões travadas:**
- Monetização: assinatura paga, trial 7 dias → mensal (Asaas)
- Primeiro foco: produtizar (auth → planos/gate → billing recorrente → multiusuário)
- Regulatório: software educacional, sem recomendação (copy e features seguem isso)

**Decisão de arquitetura a resolver (discuss/requirements):** como colar auth+billing num app
Streamlit — provável híbrido com front/checkout no stack React+Vite+n8n+Asaas na frente do Streamlit.

_Requisitos e fases detalhados serão gerados por `/gsd-new-milestone`._

## Phases

_(Vazio até o `/gsd-new-milestone` do v2.0 popular as fases.)_

## Backlog

- Payout-alvo por setor configurável (refino além do expurgo data-driven de não-recorrentes)
- Sinalização explícita de "ano extraordinário" na tabela de Fundamentos por ano
- DDM-DOC-01: alinhar docstring/teste de `t` em `ddm.py` (IN-06)
