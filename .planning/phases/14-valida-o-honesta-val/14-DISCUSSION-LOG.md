# Phase 14: Validação honesta (VAL) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-20
**Phase:** 14-valida-o-honesta-val
**Areas discussed:** Âncora de fair value, Composição da cesta, Backtest temporal (VAL-07), Rigor: ordem + limiar

---

## Âncora de fair value

### Q1 — Qual âncora faz o papel de `fair_value` na razão V/FairValue?

| Option | Description | Selected |
|--------|-------------|----------|
| Lentes clássicas (Graham+Bazin) | Independente do modelo E do sell-side; partem de lucro/dividendo real, não de preço | ✓ |
| Consenso SEM acolchoamento | Mantém faixa de target price, mata ±15% e excecao_nota; risco de circularidade/espelho | |
| Hold-out mede FORMA, não acurácia | Aceita que não existe fair_value verdadeiro para 104 tickers; veredito = robustez | |

**User's choice:** Lentes clássicas (Graham+Bazin)
**Notes:** Resolve a proibição do VAL-05 (consenso é circular) mantendo uma âncora de valor real.

### Q2 — Como formar o `fair_value` único (Graham≠Bazin; indefinidos nos difíceis)?

| Option | Description | Selected |
|--------|-------------|----------|
| Faixa [min,max] das que valem | fair_value = faixa das lentes definidas; ticker sem lente → degradação observada, fora do jackknife | ✓ |
| Ponto médio das definidas | Média/mediana; descarta o sinal de incerteza Graham≠Bazin | |
| Você decide (researcher) | Regra exata ao researcher | |

**User's choice:** Faixa [min,max] das que valem
**Notes:** Difícil sem lente não pode ser silenciosamente excluído (re-introduziria viés do "meio").

### Q3 — fair_value do ITUB4 na cesta: verdade do livro ou regra geral?

| Option | Description | Selected |
|--------|-------------|----------|
| Mesma regra dos outros | ITUB4 na cesta usa Graham+Bazin; R$37,22 vive só no VAL-01 closed-form | ✓ |
| Verdade do livro (R$37,22) | ITUB4 usa 37,22 na cesta; risco de virar âncora privilegiada da mediana | |

**User's choice:** Mesma regra dos outros
**Notes:** Mantém a cesta homogênea e o jackknife honesto; VAL-01 fica separado do hold-out.

---

## Composição da cesta

### Q1 — Como selecionar os tickers de cada arquétipo (fora os difíceis)?

| Option | Description | Selected |
|--------|-------------|----------|
| Determinístico por regra | Regra fixa escrita ANTES; zero escolha discricionária; git log prova | ✓ |
| Curadoria manual sua | Escolha por conhecimento de mercado; abre acusação de montar pra passar | |
| Universo inteiro (104) | Sem amostragem; maior poder mas dado ruim suja a distribuição | |

**User's choice:** Determinístico por regra
**Notes:** Elimina a suspeita de cherry-picking que afundou o v2.3.

### Q2 — Como escolher os 10 difíceis, e são separados da cota ≥6?

| Option | Description | Selected |
|--------|-------------|----------|
| Filtro por atributo, disjuntos | 4 baldes determinísticos; difíceis somam, separados dos ≥6 por arquétipo | ✓ |
| Filtro por atributo, podem contar | Difícil também conta pra cota do arquétipo; risco de cota dominada por extremos | |
| Você decide (researcher) | Limiares exatos dos baldes ao researcher | |

**User's choice:** Filtro por atributo, disjuntos

### Q3 — Como tratar arquétipos exóticos (CONCESSAO_FINITA; <6 nomes)?

| Option | Description | Selected |
|--------|-------------|----------|
| Reporta por estrato + pooled | Distribuição pooled + por arquétipo; carve-out isolado; cota faltante marcada | ✓ |
| Só pooled, tudo junto | Um jackknife só; carve-out pode virar outlier estrutural | |
| Carve-out fora da distribuição | Validado à parte; risco de virar "quarto onde não se olha" | |

**User's choice:** Reporta por estrato + pooled

---

## Backtest temporal (VAL-07)

### Q1 — PIT real ou não fazer e documentar?

| Option | Description | Selected |
|--------|-------------|----------|
| Não fazer, documentar | Backtest ingênuo = vazamento de futuro, número confiante e falso, pior que nenhum | ✓ |
| PIT real, escopo mínimo | Poucos tickers/datas onde dá pra provar disponibilidade da DFP | |
| Adiar para próximo marco | Future Requirement v2.5+ com desenho do PIT escrito | |

**User's choice:** Não fazer, documentar
**Notes:** VAL-07 é satisfeito pela decisão escrita durável (o que o requisito pede).

---

## Rigor: ordem + limiar

### Q1 — Como o git log prova a ordem fair_value → modelo (VAL-03)?

| Option | Description | Selected |
|--------|-------------|----------|
| Dois commits + teste de ordem | Commit 1 só fair_value; Commit 2 v_modelo; teste checa timestamps por git log/blame | ✓ |
| Hash selado do fair_value | Prova conteúdo, não a ordem temporal tão diretamente | |
| Você decide (researcher) | Mecanismo exato ao researcher | |

**User's choice:** Dois commits + teste de ordem

### Q2 — Como fixar LIMIAR_JACKKNIFE_PP e PASS a priori (VAL-04)?

| Option | Description | Selected |
|--------|-------------|----------|
| Derivado da teoria + pré-registrado | LIMIAR = f(n), independente dos valores, commitado no Commit 1 antes dos v_modelo | ✓ |
| Pré-registrado por julgamento | Número escolhido/justificado no commit 1, sem fórmula | |
| Você decide (researcher) | Forma exata ao researcher | |

**User's choice:** Derivado da teoria + pré-registrado
**Notes:** À prova de overfit por construção e por timestamp.

### Q3 — O que constitui PASS do hold-out (dispara re-arquiteta)?

| Option | Description | Selected |
|--------|-------------|----------|
| Robustez é gate; viés é detector | PASS = VAL-01 soberano + jackknife robusto + zero exceção; mediana reportada, nunca alvo | ✓ |
| Viés também é gate | Teto de viés sistêmico na mediana; risco de calibrar pra bater a âncora (proibido por VAL-05) | |
| Você decide (researcher) | Definição exata de gate vs diagnóstico ao researcher | |

**User's choice:** Robustez é gate; viés é detector
**Notes:** Honra VAL-05 — mediana nunca vira alvo de calibração (o espelho do mercado).

---

## Claude's Discretion

O usuário escolheu a opção recomendada em todas as 11 perguntas — nenhum "Você decide" acionado.
Deixado ao researcher/planner (dentro das decisões travadas): a regra determinística exata de seleção;
os limiares dos 4 baldes de dificuldade; a forma fechada/simulação do `LIMIAR_JACKKNIFE_PP(n)`; o
mecanismo exato do teste de ordem; onde registrar a decisão VAL-07; a divisão em waves e a ordem dos
dois commits.

## Deferred Ideas

- Backtest temporal PIT real → Future Requirement (v2.5+).
- Motor `nav`/SOTP real para holdings e score BSD por arquétipo → Future Requirements herdados.
- Reforma visual pesada da tela Streamlit / como o app exibe o veredito do hold-out → plano de UI dedicado.
