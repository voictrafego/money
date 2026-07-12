# Roadmap: Analista de Dividendos

## Milestones

- ✅ **v1.0 — Engine de Consistência** — Phases 1–2 (shipped 2026-06-05)
- ✅ **v1.1 — Gráfico de preço na aba Analisar** — Phase 3 (shipped 2026-06-23)
- ✅ **v1.2 — Indicadores de tendência (timing)** — Phases 4–8 (shipped 2026-06-27)
- ✅ **v1.3 — Saneamento residual do valuation** — Phases 9–11 (shipped 2026-06-28)
- ✅ **v1.4–v1.7 — Swing Trade / Modo Trading / Home / Lentes-Selo-Comparador** — Phases 12–21 (shipped 2026-07-04, tag `v1.7`)
- ✅ **v2.0 — Comercialização (Lazari Capital)** — Phases 1–3 (shipped 2026-07-10, produto no ar, E2E pago concluído)
- ✅ **v2.2 — Motor de Valuation por Arquétipo** — Phases 1–3 (shipped 2026-07-12, tag `v2.2`, auditoria de milestone passed)

> Marcos concluídos são arquivados em `.planning/milestones/` (roadmap + requisitos + fases por
> marco). Histórico narrado em `.planning/MILESTONES.md`. Cada marco major reinicia a numeração de
> fases em Phase 1 (padrão deste repo).

---

## v2.2 — Motor de Valuation por Arquétipo (SHIPPED 2026-07-12)

Corrigiu o erro de **arquitetura** (não de fórmula) em que a ferramenta aplicava um único motor
(DDM de estágio único) para toda ação, carimbando compounders de qualidade (banco ITUB4) como
"evitar". Três movimentos: **classificador de arquétipo + roteamento** (Fase 1), **motores por
arquétipo** RIM/normalizado/DCF/NAV (Fase 2) e **veredito honesto** — selo consome o motor do
arquétipo, ensemble com bandeira de divergência, guarda-corpos anti-aberração SAN-01 e dúvida
honesta no caso-fronteira (Fase 3). 12/12 requisitos verificados; suíte 437 verde; firewall
selo↛report intacto.

**Detalhes completos arquivados:** `.planning/milestones/v2.2-ROADMAP.md` ·
`.planning/milestones/v2.2-REQUIREMENTS.md` · `.planning/milestones/v2.2-phases/`
**Auditoria:** `.planning/v2.2-MILESTONE-AUDIT.md` (passed; blocker da aba Ranking do Streamlit
fechado por quick task 260712-p6r antes do arquivamento).

---

## Próximo marco

Nenhum marco ativo. Inicie o próximo com `/gsd-new-milestone` (questionamento → pesquisa →
requisitos → roadmap). Um novo `.planning/REQUIREMENTS.md` é criado nesse fluxo.
