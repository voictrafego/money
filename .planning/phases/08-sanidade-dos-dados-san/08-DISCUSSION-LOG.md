# Phase 08: Sanidade dos dados (SAN) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-14
**Phase:** 08-sanidade-dos-dados-san
**Areas discussed:** Onde o diagnóstico mora, O baseline dos sujos, Limiares de detecção, Forma do veredito + visibilidade

---

## Onde o diagnóstico mora

### Q1 — Onde os avisos de sanidade devem viver?

| Option | Description | Selected |
|--------|-------------|----------|
| Campo no CompanyData | `c.avisos` + `c.confianca` no dataclass; motor e tela leem sem costura; Fase 13 herda pronto | ✓ |
| Módulo à parte (sanidade.py) | Relatório separado; CompanyData intacto; custo de costura na Fase 13 | |
| Módulo à parte + um campo só | Lógica isolada, resultado anexado em `c.sanidade` | |

**User's choice:** Campo no CompanyData
**Notes:** `CompanyData` (`core/fundamentals.py:20`) hoje não tem nenhum campo de aviso/confiança — a estrutura nasce nesta fase.

### Q2 — Quem popula, e qual o default de um CompanyData nunca checado?

| Option | Description | Selected |
|--------|-------------|----------|
| montar_empresa roda + default `nao_avaliada` | Checks automáticos no ingest; objeto sintético nasce não-auditado | |
| montar_empresa roda + default `alta` | Mais simples de consumir; objeto sintético passa por limpo | |
| Função explícita `aplicar_sanidade(c)` | Controle total, testável isolado; risco: esquecer de chamar | ✓ |

**User's choice:** Função explícita `aplicar_sanidade(c)`
**Notes:** Claude sinalizou o risco — esquecimento silencioso é a forma mais comum de guarda morrer, e é exatamente o que a Fase 7 existiu para eliminar. Endereçado na Q3.

### Q3 — Como impedir que "esquecer de chamar" passe despercebido?

| Option | Description | Selected |
|--------|-------------|----------|
| Default `nao_avaliada` + teste que prova a chamada | Teste roda o pipeline real e exige saída ≠ `nao_avaliada`; guarda provada por execução | ✓ |
| Só o default `nao_avaliada` | Estado errado fica visível, mas nada quebra se a chamada sumir | |
| Teste + assert no ponto de consumo | Motores recusam operar sobre `nao_avaliada` — colide com o never-raise (SAN-06) | |

**User's choice:** Default `nao_avaliada` + teste que prova a chamada
**Notes:** Fecha o buraco aberto pela escolha da Q2, no estilo do BLIND.

---

## O baseline dos sujos

### Q1 — Como a Fase 9 prova, ticker a ticker, que o conserto funcionou?

| Option | Description | Selected |
|--------|-------------|----------|
| Baseline versionado + monotonicidade | Lista só encolhe; flag ressuscitada fica vermelha; progresso mensurável (41 → 0) | ✓ |
| Baseline versionado, sem monotonicidade | Atualizado à mão — reinstala o reflexo que produziu o overfit do v2.3 | |
| Relatório CLI sob demanda | Inspeção humana; sem teste de regressão automático (contraria o ROADMAP) | |

**User's choice:** Baseline versionado + regra da monotonicidade
**Notes:** Claude alertou que um mapa `ticker → flag` **não** viola o BLIND-04a (que proíbe `ticker == R$`), mas o desenho precisa deixar a distinção óbvia para o próximo leitor.

### Q2 — O que o baseline registra por ticker?

| Option | Description | Selected |
|--------|-------------|----------|
| Flag + ordem de grandeza (bucket) | Ex.: `CGRA4: [SAN-01: ~1e3]`; robusto a refresh do Yahoo, mas quebra se a flag for silenciada sem conserto | ✓ |
| Só o nome da flag | Estável, mas não distingue "consertei a escala" de "afrouxei o limiar até calar" | |
| Flag + magnitude exata | Frágil por construção — vermelho a cada refresh de dado | |

**User's choice:** Flag + ordem de grandeza (bucket)

### Q3 — Sobre qual dado o baseline é calculado?

| Option | Description | Selected |
|--------|-------------|----------|
| Snapshot congelado dos 104 (capturado nesta fase) | Determinístico, offline, cobre os 41; evidência intocada contra a qual a Fase 9 mede | ✓ |
| Reusar o snapshot de bancos | Zero captura, mas cego em GOAU4/CGRA4/CSNA3/MRFG3/ALUP11/EQTL3 — os alvos nomeados | |
| Baseline sobre dado vivo (rede) | Sempre atual; inviável como teste (lento, flaky, muda sozinho) | |

**User's choice:** Snapshot congelado dos 104, capturado nesta fase com o dado sujo
**Notes:** O snapshot de bancos atual está contaminado — dá verde contendo a doença (ITUB4 a 10 milhões de ações). O ROADMAP da Fase 9 já prevê sua regeneração.

---

## Limiares de detecção

### Q1 — Qual o limiar do SAN-01 (`num_acoes × preço ≈ market cap`)?

| Option | Description | Selected |
|--------|-------------|----------|
| Folgado: desvio > 50% (fator ≥ 1,5×) | Pega os 4 escândalos com folga, zero falso positivo; a guarda sobrevive | ✓ |
| Apertado: desvio > 10% | Pega o sutil, mas dispara em ticker saudável (defasagem do Yahoo) — vira barulho | |
| Dois níveis: aviso (>20%) + grave (>50%) | Graduado, mas a faixa 20-50% é onde o ruído do Yahoo vive | |

**User's choice:** Folgado — desvio > 50%
**Notes:** Coerente com a lição já registrada: falso positivo desinstala a guarda tão rápido quanto o furo a inutiliza.

### Q2 — Onde os limiares ficam, e como impedir que virem knob?

| Option | Description | Selected |
|--------|-------------|----------|
| Constantes no módulo + teste que congela os valores | Longe do config e do lock; afrouxar fica vermelho e vira evento visível | ✓ |
| Constantes no módulo, sem teste | Afrouxar é um diff de uma linha que ninguém nota | |
| Entrada no `calibracao.lock.yaml` | Seria um 4º grau de liberdade — deixa a suíte vermelha por construção | |

**User's choice:** Constantes no módulo + teste que congela os valores
**Notes:** Limiar de detecção não move `Ke`, `g` nem preço — não é knob de valuation. Mas mora perto o bastante para ser confundido com um.

### Q3 — Como o SAN-02 distingue split legítimo de dado quebrado?

| Option | Description | Selected |
|--------|-------------|----------|
| Limiar alto + `.splits` do Yahoo como isenção | Pega ITUB4 (1.131×) e BRSR6 (205.000×) sem acusar quem desdobrou; falha na direção visível | ✓ |
| Só o limiar, sem checar split | Acusa split legítimo — falso positivo desinstala a guarda | |
| Limiar tão alto que split não alcança (>10×) | Simples, mas deixaria escapar quebra de fator 3× (coberta pelo SAN-01) | |

**User's choice:** Limiar alto + `.splits` do Yahoo como isenção

---

## Forma do veredito + visibilidade

### Q1 — Qual a forma de `c.confianca`?

| Option | Description | Selected |
|--------|-------------|----------|
| Escala discreta: alta/media/baixa/nao_avaliada | Legível sem tradução, testável, não inventa precisão | ✓ |
| Score numérico 0-100 | Precisão falsa; todo número por ticker convida a virar knob | |
| Só a lista de flags crua | Honesto, mas empurra a decisão de "grave" para cada tela | |

**User's choice:** Escala discreta

### Q2 — A confiança aparece na tela já nesta fase?

| Option | Description | Selected |
|--------|-------------|----------|
| Interno agora; tela só na Fase 13 | Mantém a fase no escopo (detectar ≠ apresentar); não alarma cliente pagante | ✓ |
| Tela já nesta fase | Máxima honestidade, mas 41/104 exibiriam "dado suspeito" por semanas | |
| Interno + report CLI | Igual à primeira, com ferramenta de inspeção | |

**User's choice:** Interno agora; tela só na Fase 13
**Notes:** O app está no ar e vendido (v2.0). O relatório CLI foi incorporado como ferramenta de trabalho para medir o conserto durante a Fase 9 (D-14).

### Q3 — Qual o entregável do spike SAN-07?

| Option | Description | Selected |
|--------|-------------|----------|
| Doc escrito + medição que sustenta a resposta | "É material?" é pergunta quantitativa — sem medir, é palpite | ✓ |
| Só o doc escrito | Mais rápido; a Fase 9 herdaria a dúvida | |
| Código de medição, sem doc | ROADMAP pede resposta por escrito | |

**User's choice:** Doc escrito + medição
**Notes:** Nenhum knob é movido pelo spike (Armadilha 3).

---

## Claude's Discretion

- Nome/localização exatos do módulo de sanidade, formato de serialização do baseline e do snapshot,
  estrutura interna do objeto de aviso.
- Limiares específicos de SAN-02..SAN-05 (o de SAN-01 está fixado em >50%), seguindo o princípio de
  D-09.

## Deferred Ideas

- Exibir o selo de confiança na tela — Fase 13 (contrato de saída).
- Cindir as 19 funções mistas restantes (gap WR-04) — obrigatório antes da **Fase 10**, fora do
  escopo da Fase 8.
