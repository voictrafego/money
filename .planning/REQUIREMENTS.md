# Requirements: Analista de Dividendos — v2.2 Motor de Valuation por Arquétipo

**Defined:** 2026-07-11
**Core Value:** Cada tipo de negócio é roteado para o motor de valuation certo antes de valuar, e **nenhum veredito final é puxado por um modelo que não serve àquele perfil** — um compounder de qualidade (banco) nunca mais é carimbado "evitar" porque o DDM de estágio único não cabe nele.
**Milestone goal:** Corrigir o erro de **arquitetura** (não de fórmula) em que a ferramenta aplica um único motor primário (DDM de estágio único) para todas as ações. Construir: (1) classificador de arquétipo, (2) registry de motores por arquétipo, (3) ensemble com bandeira de divergência, (4) guarda-corpos de sanidade anti-aberração, (5) agregação de veredito que consome o motor **do arquétipo** e assume a dúvida em casos-fronteira. Meta: acertar os ~85% de casos claros e assumir honestamente a dúvida nos ~15% fronteiriços.

**Contexto (caso ITUB4):** Preço R$43,59 · DDM ao vivo R$12,93–19,32 · Graham R$39,88 · Bazin R$28,97. Veredito estampado: SOBREAVALIADA / Qualidade Baixa / Evitar. Divergência de ~3× entre DDM e Graham/mercado é sinal de motor primário errado para o negócio. Raiz: Ke ~17,3% ao vivo (Selic alta via CAPM) comprime `V=D1/(Ke−g)`; normalização de payout 105%→46,7% derruba o DY de entrada 7,9%→4,0%; DDM ignora o lucro retido reinvestido (ROE 19,3%, retenção ~53%). Os modelos individuais estão matematicamente corretos — o defeito é a **ausência de roteamento** e a **agregação single-model do veredito**.

**Brief-fonte:** `.planning/BRIEF-motor-arquetipo.md` (mapa de código com âncoras `arquivo:linha`, ordem sugerida de fases). **Gargalo = o classificador (~60% do esforço), não os motores (~20%, fórmulas de livro-texto).**

## v2.2 Requirements

### Classificador de arquétipo (ARQ) — o coração

- [x] **ARQ-01**: A ferramenta classifica o **arquétipo do negócio antes de valuar**, a partir dos dados já puxados (CVM + Yahoo + BCB): filtro grosso por setor CVM como primeiro corte + refino quantitativo pelas métricas que a própria ação entrega (financeira → RIM; pagadora estável com payout comportado → DDM elegível; ROE alto e estável com retenção alta → compounder; margem/lucro oscilando violento ano a ano → cíclica).
- [x] **ARQ-02**: **Fallback honesto** — quando a confiança do classificador for baixa (caso-fronteira, híbrido, mudança de estágio), a ferramenta **não chuta**: marca a ação como fronteiriça e roda 2–3 lentes candidatas em vez de forçar um único arquétipo.

### Registro de motores (ENG)

- [x] **ENG-01**: Existe um **registry arquétipo→motor primário** que a agregação do veredito consome — a escolha do motor deixa de ser fixa (DDM) e passa a ser função do arquétipo classificado.
- [ ] **ENG-02**: **RIM (Residual Income Model)** — VPA + VP do excesso de ROE sobre Ke — disponível como motor primário para **banco/seguradora** (ITUB4, BBAS3, BBSE3). *(É o motor que destrava o ITUB4.)*
- [ ] **ENG-03**: **Lucro normalizado** (média 7–10 anos ou mid-cycle) → EV/EBITDA ou FCF disponível como motor primário para **cíclica de commodity** (VALE3, GGBR4, SUZB3), em vez do lucro de um ano só.
- [ ] **ENG-04**: **DCF de FCF multi-estágio** (ou múltiplo relativo) disponível como motor primário para **crescimento/capital-light** (WEGE3, tech, varejo em expansão), sem o DDM cuspir zero/lixo.
- [ ] **ENG-05**: **NAV / Soma das Partes (SOTP)** disponível como motor primário para **holding/imobiliária patrimonial**.
- [x] **ENG-06**: **DDM permanece** como motor primário para **pagadora madura/regulada** (TAEE11, SAPR11, EGIE3) — reaproveitando o motor atual, sem quebrar o que já funciona.

### Ensemble & divergência (ENS)

- [ ] **ENS-01**: A ferramenta **nunca crava um número único quando os modelos discordam muito**: roda o motor primário do arquétipo + ≥1 contraponto e, se a divergência passar do limiar (ex.: maior modelo > 2× o menor), **levanta uma bandeira de divergência** com hipótese exibida ("compounder subvalorizado pelo DDM", "cíclica no topo do ciclo", etc.). Divergência é informação exibida, não defeito escondido.

### Guarda-corpo de sanidade (SAN)

- [ ] **SAN-01**: Regras **anti-aberração** capturam o absurdo antes de virar selo. Ex.: SE `intrínseco < 0,5 × mediana dos pares` E `ROE > 15%` E `normalização de payout cortou o dividendo > 40%` ENTÃO **não estampar** "qualidade baixa / evitar" — estampar "DDM conservador demais para o perfil, ver motor primário do arquétipo". Todo veredito "evitar" passa pelos guarda-corpos antes de ser exibido.

### Veredito honesto (VER)

- [ ] **VER-01**: A **agregação do selo final** (hoje BSD × DDM) é refatorada para **consumir o motor do arquétipo**, não o DDM fixo — quando o DDM não é o motor do perfil, ele é rebaixado a "lente conservadora".
- [ ] **VER-02**: Em **caso-fronteira**, o veredito **assume a dúvida em voz alta** (range + bandeira de divergência) em vez de fingir certeza cravando um selo falso.

## v2 Requirements (deferido)

Rastreado, fora do roadmap atual.

- **BACKTEST-01**: Backtesting dos modelos contra retorno futuro (validar empiricamente qual motor acerta por arquétipo). Explicitamente fora de escopo desta fase.
- **ARQ-AUTO-01**: Acertar 100% dos tickers automaticamente. Meta do v2.2 é ~85% claros + assumir a dúvida nos ~15% fronteiriços.

## Out of Scope

Explicitamente excluído para manter o milestone fechado.

| Feature | Reason |
|---------|--------|
| Novas fontes de dados além de CVM, Yahoo e BCB | Princípio de custo zero; classificador e motores devem trabalhar só com o que já se puxa |
| Redesenho de UI além da lógica de veredito e da bandeira de divergência | Milestone é de engine; UI muda só onde o veredito/bandeira aparecem |
| Backtesting dos modelos contra retorno futuro | Fase posterior (ver BACKTEST-01); v2.2 é sobre roteamento correto, não validação empírica de retorno |
| Acertar 100% dos tickers automaticamente | Meta é ~85% claros + dúvida honesta nos ~15%; perseguir 100% seria over-fitting do classificador |
| Reescrever os modelos individuais (DDM/Graham/Bazin) | Estão matematicamente corretos; o defeito é ausência de roteamento e agregação single-model, não as fórmulas |

## Traceability

Quais fases cobrem quais requisitos. Preenchido na criação do roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARQ-01 | Phase 1 | Complete |
| ARQ-02 | Phase 1 | Complete |
| ENG-01 | Phase 1 | Complete |
| ENG-06 | Phase 1 | Complete |
| ENG-02 | Phase 2 | Pending |
| ENG-03 | Phase 2 | Pending |
| ENG-04 | Phase 2 | Pending |
| ENG-05 | Phase 2 | Pending |
| ENS-01 | Phase 3 | Pending |
| SAN-01 | Phase 3 | Pending |
| VER-01 | Phase 3 | Pending |
| VER-02 | Phase 3 | Pending |

**Coverage:**
- v2.2 requirements: 12 total
- Mapped to phases: 12 ✓
- Unmapped: 0

**Por fase:**
- Phase 1 (Classificador + Roteamento): ARQ-01, ARQ-02, ENG-01, ENG-06 (4)
- Phase 2 (Motores por Arquétipo): ENG-02, ENG-03, ENG-04, ENG-05 (4)
- Phase 3 (Veredito Honesto): ENS-01, SAN-01, VER-01, VER-02 (4)

---
*Requirements defined: 2026-07-11*
*Last updated: 2026-07-11 — roadmap criado; 12/12 requisitos mapeados em 3 fases (numeração reiniciada em Phase 1)*
