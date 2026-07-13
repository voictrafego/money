# Phase 5: BACKTEST-01 — Validação na cesta de bancos - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-12
**Phase:** 5-BACKTEST-01 — Validação na cesta de bancos
**Areas discussed:** Tabela de fair values, Reprodutibilidade dos dados, Critério de aceite, Formato do harness

---

## Tabela manual de fair values

### Origem dos valores-alvo

| Option | Description | Selected |
|--------|-------------|----------|
| Eu pesquiso consenso | Claude busca fair values/target prices de consenso e traz proposta para aprovação antes de versionar | ✓ |
| Você fornece os números | Usuário passa os 4 valores direto | |
| Deriva de Graham/Bazin | Sem tabela manual separada; combina âncoras já calculadas | |

**User's choice:** Eu pesquiso consenso
**Notes:** Usuário revisa a proposta, mas não precisa cavar os números. Mantém a 4ª âncora manual independente exigida por VAL-02.

### Estrutura / versionamento

| Option | Description | Selected |
|--------|-------------|----------|
| Arquivo YAML dedicado | tests/fixtures/fair_values_bancos.yaml — valor, data, fonte; separado do config.yaml | ✓ |
| Dentro do config.yaml | Seção backtest.fair_values no config existente | |
| Tabela markdown | .md legível, teste teria que parsear/duplicar | |

**User's choice:** Arquivo YAML dedicado
**Notes:** Separa "verdade externa de validação" de "knobs do motor".

### Ponto vs faixa

| Option | Description | Selected |
|--------|-------------|----------|
| Faixa (mín–máx) | Intervalo de fair value por ticker; casa com "cai na banda razoável" | ✓ |
| Número único | Alvo pontual; critério vira ±X% do ponto | |
| Você decide | Claude escolhe conforme o consenso | |

**User's choice:** Faixa (mín–máx)

---

## Reprodutibilidade dos dados

### Live vs congelado

| Option | Description | Selected |
|--------|-------------|----------|
| Snapshots congelados | Congela VPA/ROE/preço num fixture; teste determinístico (golden) | ✓ |
| Live com bandas frouxas | Roda ao vivo toda vez; teste flaky/depende de rede | |
| Híbrido | Script ao vivo + teste sobre snapshot congelado | |

**User's choice:** Snapshots congelados
**Notes:** "Reproduzível" do VAL-01 exige determinismo; não quebra com oscilação de preço nem queda de fonte.

### Data-base

| Option | Description | Selected |
|--------|-------------|----------|
| Hoje (captura única ao vivo) | montar_empresa ao vivo agora (~2026-07-12), congela com data; consenso alinhado à janela | ✓ |
| Último fechamento CVM | Ancora no último ITR/exercício fechado | |
| Você decide | Claude escolhe ao capturar | |

**User's choice:** Hoje (captura única ao vivo)

---

## Critério de aceite

### Âncora-verdade do gate

| Option | Description | Selected |
|--------|-------------|----------|
| Tabela manual de fair values | RIM cobrado contra a faixa FV; outras 3 âncoras como contexto | ✓ |
| Consenso das 4 âncoras | Faixa derivada da combinação das 4 | |
| Preço de mercado | RIM cobrado contra preço atual | |

**User's choice:** Tabela manual de fair values
**Notes:** Casa com o sintoma "~40-50% abaixo das âncoras".

### Banda numérica

| Option | Description | Selected |
|--------|-------------|----------|
| ±15% da faixa | PASS se dentro da faixa ou até 15% fora de qualquer borda | ✓ |
| ±25% da faixa | Mais frouxo | |
| Dentro da faixa (0%) | Estrito; risco de overfit | |

**User's choice:** ±15% da faixa
**Notes:** Ponto de partida honesto e calibrável.

### Quórum / exceção

| Option | Description | Selected |
|--------|-------------|----------|
| 3 de 4, exceção explicada | ≥3 na banda; 4º fora só se documentado; não-explicado = FAIL | ✓ |
| 4 de 4 (todos) | Gate duro sem exceção | |
| Média da cesta | Cobra viés agregado | |

**User's choice:** 3 de 4, exceção explicada
**Notes:** Espelha SC#2 (maioria na banda) + SC#4 (exceção explicada, não escondida). Teste trava o quórum numérico; explicação é nota humana no fixture/relatório.

---

## Formato do harness

### Entrega

| Option | Description | Selected |
|--------|-------------|----------|
| Teste pytest + script | Teste determinístico trava o gate + script standalone imprime tabela | ✓ |
| Só teste pytest | Tabela embutida no assert | |
| Subcomando CLI 'backtest' | Adiciona comando ao cli.py | |

**User's choice:** Teste pytest + script
**Notes:** Cobre "reproduzível: script + teste" do VAL-01.

### Saída do script

| Option | Description | Selected |
|--------|-------------|----------|
| Markdown em out/ | out/backtest_bancos.md com a tabela completa; segue padrão out/TICKER.md | ✓ |
| Stdout/stderr | Só imprime no terminal | |
| Markdown + CSV | .md + .csv de dados crus | |

**User's choice:** Markdown em out/

### Âncora de múltiplos de pares

| Option | Description | Selected |
|--------|-------------|----------|
| Da própria cesta | P/VP e P/L medianos dos 4 bancos; reusa comparables.py/multiples.py | ✓ |
| Referência setorial fixa | P/VP e P/L do setor pesquisados e versionados | |
| Você decide | Claude escolhe conforme comparables.py | |

**User's choice:** Da própria cesta

---

## Claude's Discretion

- Local exato do fixture de fair values e do snapshot (fixtures/ vs data/).
- Estrutura interna do snapshot congelado (raw fundamentals vs CompanyData serializado).
- Forma de invocar o script standalone (`python -m`, scripts/, função).

## Deferred Ideas

- Redeploy do v2.3 na VPS — Fase 6 (OPS-01), depende desta.
- Expandir o backtest para não-bancos / outros arquétipos — marco futuro.
- Backtest histórico multi-período — fora do escopo (snapshot único).
