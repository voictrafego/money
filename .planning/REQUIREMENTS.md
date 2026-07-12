# Requirements — v2.3 Calibração do Valuation à Realidade (RIM com Valor Terminal / BACKTEST-01)

**Milestone goal:** Corrigir a subestimação sistemática do motor RIM (bancos) dando-lhe um **valor
terminal**, para que bancos de qualidade valuem coerente com âncoras de realidade — validado numa
cesta de bancos. Escopo cirúrgico: **só RIM/bancos** neste marco.

**Contexto (diagnóstico 2026-07-12):** RIM ao vivo dá ITUB4 = R$23,01 vs alvo ~R$40 do SC#1 do
v2.2. Causa raiz é a estrutura **fade-sem-valor-terminal (D-02)** que ancora o RIM no VPA (~R$19),
NÃO o Ke (que move só ~R$3 no range 10,5%–17,3%). Um residual income COM perpetuidade / P/B justo
((ROE−g)/(Ke−g)) leva o ITUB4 a ~R$32-38. Ver `.planning/v2.2-MILESTONE-AUDIT.md`.

---

## v2.3 Requirements

### Calibração do modelo (CAL)

- [ ] **CAL-01**: O motor **RIM ganha um valor terminal** — uma perpetuidade de residual income (ou
  P/B justo `(ROE−g)/(Ke−g)` equivalente) que substitui/complementa o fade-para-zero-sem-terminal
  atual (D-02), de forma que o valor deixe de ancorar no VPA para um banco que sustenta ROE > Ke. A
  formulação tem **fundamento teórico** (não um fator de fudge), é **parametrizada em `config.yaml`**
  (nada hard-coded), e o motor permanece puro/never-raise, sem tocar `ddm.py`/`selo.py`/`lentes.py`.
  **Critério de aceite:** ITUB4 (roteado para RIM) produz intrínseco na faixa **~R$32–40** — na mesma
  ordem de grandeza de Graham (R$39,88) e do preço (R$44,30), NÃO os ~R$23 atuais. *(Este é o alvo
  quantitativo que o v2.2 não cobrou; verificação deve cobrar o NÚMERO, não só "não é Evitar".)*

- [ ] **CAL-02**: O **Ke do RIM por arquétipo (banco)** é revisado como ajuste secundário — rever o
  teto de 14% que hoje binda o `ke_rim` (e o `erp_banco`), documentando a escolha. É a alavanca fina
  (≈R$3), aplicada **por cima** do valor terminal do CAL-01, não como conserto principal. Não pode
  produzir intrínseco explosivo (manter clamps sãos).

### Validação / Backtest (VAL)

- [ ] **VAL-01**: Existe um **harness de validação (BACKTEST-01)** que roda o RIM calibrado numa
  **cesta de bancos** (ITUB4, BBAS3, BBSE3, BBDC4) e reporta o intrínseco de cada um contra âncoras
  de realidade, para provar que a calibração generaliza (não só ITUB4). Reproduzível (script + teste).

- [ ] **VAL-02**: A validação **triangula 4 âncoras** por ticker: (a) Graham + Bazin (já calculados);
  (b) preço de mercado atual; (c) **tabela manual de fair values** (valores-alvo por ticker, fornecidos
  pelo usuário ou pesquisados de consenso — a definir na fase); (d) múltiplos de pares (P/VP, P/L do
  setor bancário). **Critério de aceite:** para a cesta, o intrínseco do RIM não fica cronicamente
  ~40-50% abaixo das âncoras (o sintoma "descolado da verdade"); desvios remanescentes são explicados,
  não escondidos.

### Operação (OPS)

- [ ] **OPS-01**: O **app é redeployado na VPS** com o código v2.3 (o v2.2 nunca subiu — o app em
  produção ainda roda comportamento pré-arquétipo). **Critério de aceite:** ITUB4 no app ao vivo mostra
  o arquétipo (financeira→RIM), o intrínseco calibrado do RIM e o veredito "ver motor primário" —
  **não** mais "Evitar" com faixa DDM R$12,93–19,32. Suíte verde e firewall intacto antes do deploy.

---

## Future Requirements (deferidas)

- **Valor terminal / conservadorismo nos OUTROS motores** (DCF de crescimento, lucro normalizado de
  cíclica): o mesmo viés fade-sem-terminal pode subestimar compounders e cíclicas. Fora do escopo
  cirúrgico deste marco; auditar/tratar em marco futuro se a cesta de validação sugerir o padrão.
- **Backtest histórico com preços realizados** (calibração empírica out-of-sample, não só snapshot vs
  âncoras) — evolução natural do BACKTEST-01.

## Out of Scope (v2.3)

- **Reescrever DDM/Graham/Bazin** — estão matematicamente corretos; o alvo é só o RIM (bancos).
- **Novos arquétipos ou motores** — o registry do v2.2 fica intocado; só a fórmula interna do RIM muda.
- **Mudança na filosofia do selo/veredito** (ensemble, SAN-01, fronteiriço do v2.2) — permanecem.

---

## Traceability

Quais fases cobrem quais requisitos. Preenchido na criação do roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CAL-01 | TBD | Pending |
| CAL-02 | TBD | Pending |
| VAL-01 | TBD | Pending |
| VAL-02 | TBD | Pending |
| OPS-01 | TBD | Pending |

**Coverage:**
- v2.3 requirements: 5 total
- Mapped to phases: 0 (roadmap pendente)

---
*Requirements defined: 2026-07-12*
