# Phase 11: Crescimento / `g` (GROW) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-16
**Phase:** 11-crescimento-g-grow
**Areas discussed:** Seleção do g explícito (GROW-04), Topologia do g_cap no config, Fonte/janela do π_ciclo, Postura dos knobs sob spread apertado (GROW-05)

---

## Seleção do `g` da fase explícita (GROW-04)

**Pergunta 1 — regra que substitui `min(g_historico, g_fundamentos)`:**

| Option | Description | Selected |
|--------|-------------|----------|
| Adotar g_fundamentos; histórico vira display+fallback | g por fundamentos passa a ser O g adotado (reproduz o livro, ITUB4 → 10,29%); g_historico só exibido/fallback | ✓ |
| Adotar fundamentos com trava/reconciliação documentada | Adota fundamentos mas registra alerta quando diverge do histórico | |
| Você decide (dentro do GROW-04) | Planner escolhe a forma, contanto que adote fundamentos | |

**Pergunta 2 — onde entra o teto de cada g (nuance levantada pelo Claude: g_cap trava só o terminal):**

| Option | Description | Selected |
|--------|-------------|----------|
| g_cap trava só o terminal; explícito mantém teto Ke | g_alto = g_fundamentos, teto Ke (FIX-01) + 0,25; g_T = min(ROE_T×retenção, g_cap). Preserva os dois estágios; ITUB4 explícito ≈ 10,29% reproduz o livro | ✓ |
| g_cap trava ambos | Simplifica mas ITUB4 explícito cai para 7,28% e VAL-01 não reproduz | |

**User's choice:** Adotar g_fundamentos como o g explícito; g_historico vira display/fallback; g_cap trava SÓ o terminal.
**Notes:** O Claude sinalizou que o preview inicial travava g_alto em g_cap — o que quebraria o caso soberano do marco (ITUB4 = R$ 37,22 com g = 10,24%). O usuário confirmou a correção: estrutura de dois estágios (explícito alto → fade → terminal ≤ g_cap).

---

## Topologia do `g_cap` no config

**Pergunta 1 — onde o g_cap é derivado:**

| Option | Description | Selected |
|--------|-------------|----------|
| Engine deriva de π_ciclo (carimbado) + PIB_real (knob) | Engine calcula g_cap em tempo de cálculo; torna "derivado não digitado" literal e testável | ✓ |
| Entry points carimbam o g_cap pronto | Simétrico ao rf_local mas esconde a derivação | |
| Você decide | Planner escolhe o ponto | |

**Pergunta 2 — fonte única vs. derivação local:**

| Option | Description | Selected |
|--------|-------------|----------|
| Fonte única: um g_cap, consumido por DDM e RIM | Elimina as duas constantes de 2,5%; ajuda ENG-10 | ✓ |
| Derivação local em cada bloco | Preserva independência do motor mas duplica folha | |

**User's choice:** Engine deriva; fonte única consumida por DDM + RIM.
**Notes:** O `caminho` do grau `PIB_real` no calibracao.lock.yaml migra de `ddm.g_estavel` para o novo home no mesmo commit (o lock:97-101 já manda isso).

---

## Fonte/janela do π_ciclo

| Option | Description | Selected |
|--------|-------------|----------|
| Média aritmética de _ipca_anual_dezembro(10), carimbada | Irmão de selic_ciclo_para_capm (sum/len); mesma série SGS 13522 dos deflatores; espelha o rf | ✓ |
| Média geométrica (IPCA acumulado 10a anualizado) | Mais "correto" como taxa composta mas quebra a simetria exata com o rf | |
| Você decide | Planner fixa o método | |

**User's choice:** Média aritmética de `_ipca_anual_dezembro(10)`, carimbada nos entry points.
**Notes:** O rf agrega por `sum(hist)/len(hist)` (macro.py:161); o π_ciclo espelha para a simetria do GROW-02. Precisa de default `macro.pi_ciclo` no config para determinismo offline/testes.

---

## Postura dos knobs sob spread apertado (GROW-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Congelar valores + cobrir o comportamento com teste | Mantém 0,045 e 0,03; teste exercita o terminal sob spread ~5,5pp (knobs binding); load-bearing por cobertura, não recalibração | ✓ |
| Revisitar valores agora | Knob move + lock; abre porta para calibrar contra resultado (Armadilha 4) | |
| Você decide | Planner decide, com a regra do lock/ticker | |

**User's choice:** Congelar `excesso_sustentavel` (0,045) e `ke_g_spread_min` (0,03) + cobrir com teste.
**Notes:** "Prever, não descobrir depois" — o teste garante que o terminal não explode e degrada de forma honesta (fade-only, never-raise) sob o spread apertado.

---

## Claude's Discretion

- O usuário escolheu a opção recomendada em todas as 4 áreas (nenhum "Você decide" selecionado).
- Detalhes deixados ao planner/researcher: nome exato da chave do novo home do PIB_real/g_cap e do
  caminho no lock; assinatura do helper `ipca_ciclo_para_g`; forma exata do teste de cobertura do
  GROW-05; rótulos do report markdown (report.py:960-962) refletindo a nova semântica.

## Deferred Ideas

- Conserto do Ke/ke_teto/ke_piso/ERP/beta → Fase 12 (regra dura A; BLIND-02 vira verde lá).
- Colapso dos 4 motores num RIM único + contrato de saída do livro + corte de knobs `motores:` → Fase 13 (ENG).
- Reforma de UI do contrato de saída → Fase 13 (UI hint: yes).
- Validação honesta / hold-out / caso do livro (ITUB4 = R$ 37,22) → Fase 14 (VAL).
