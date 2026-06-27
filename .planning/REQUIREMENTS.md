# Requirements: Analista de Dividendos — v1.3

**Defined:** 2026-06-27
**Core Value:** Os números do app são fiéis ao método do livro e consistentes entre si — a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.
**Milestone goal:** Saneamento residual do valuation — tornar DY recorrente, payout sustentável e crescimento histórico fiéis e robustos **para qualquer ticker** (expurgando não-recorrentes por regra geral, não por ajuste de caso) e impedir que esses números contaminem Garimpo/Ranking. VULC3 é diagnóstico; a correção vale para todo o universo e não regride tickers normais.

## v1.3 Requirements

### Renda recorrente (DYR)

- [x] **DYR-01**: O DY recorrente reflete o provento **sustentável** (lucro normalizado × payout sustentável), robusto a anos de distribuição extraordinária — não a mediana crua dos últimos 3 anos de dividendos, que pode cair inteira numa era de payout >100% (vale para qualquer ticker)
- [ ] **DYR-02**: O DY recorrente é exibido formatado como **%** na tabela de Múltiplos do app (paridade com ML/ROE/DY), nunca como decimal cru ("0.20")

### Payout sustentável (PAY)

- [x] **PAY-01**: O payout-para-valuation **expurga anos não-recorrentes** (distribuição extraordinária / payout >100%) por regra geral, devolvendo um payout sustentável para qualquer ticker — não a média crua de 3 anos que encosta no clamp de 100% e zera o crescimento por fundamentos
- [ ] **PAY-02**: O app exibe o payout **cru do último ano** (valor real, ex.: 124,7%) como número distinto do payout sustentável de valuation — hoje as duas linhas ("Payout (último ano)" e "Payout p/ valuation") mostram o mesmo valor clampado

### Crescimento robusto (GROW)

- [x] **GROW-01**: O **g histórico** exibido usa uma estimativa **robusta** de crescimento (não CAGR endpoint-a-endpoint, sensível a um único ano de fundo/topo), fiel à trajetória do lucro normalizado
- [x] **GROW-02**: O screening de **Garimpo (BSD)** e **Ranking** calcula crescimento de lucro/dividendos sobre a série **normalizada** (não o lucro/dividendo CRU da CVM), impedindo que um ano extraordinário envenene o ranqueamento

### Hierarquia de apresentação (HIER)

- [ ] **HIER-01**: O cabeçalho do Analisar dá **destaque ao DY recorrente** (sustentável) e rebaixa/rotula o DY trailing como histórico/inflado, evitando induzir o usuário à armadilha de dividendos que o próprio app sinaliza

### Travas de fidelidade (TEST)

- [ ] **TEST-08**: A mudança de metodologia é validada contra um conjunto de **tickers normais** (ITUB4, EGIE3, TAEE11, BBAS3) além do caso-limite VULC3 — golden de valuation seguem verdes OU são rebaselinados **deliberadamente com justificativa**, garantindo que tickers sem distorção não regridem (extensão do invariante TEST-07)

## Future Requirements (v2+)

- Payout-alvo por setor configurável (refino além do expurgo data-driven de não-recorrentes)
- Detecção/sinalização explícita de "ano extraordinário" na tabela de Fundamentos por ano

## Out of Scope

- Reescrever o modelo DDM ou as fórmulas do livro (Cap. 13-17) — o saneamento ajusta **inputs normalizados**, não a mecânica do valuation
- Tunar constantes por empresa específica (princípio: regra geral para qualquer ticker)
- Nova fonte de dados paga ou de não-recorrentes detalhados por nota explicativa (segue só com CVM/Yahoo/BCB)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DYR-01 | Phase 9 | Complete |
| PAY-01 | Phase 9 | Complete |
| GROW-01 | Phase 10 | Complete |
| GROW-02 | Phase 10 | Complete |
| DYR-02 | Phase 11 | Pending |
| PAY-02 | Phase 11 | Pending |
| HIER-01 | Phase 11 | Pending |
| TEST-08 | Phase 11 | Pending |

**Coverage:** 8/8 requisitos v1.3 mapeados — sem órfãos, sem duplicatas.
