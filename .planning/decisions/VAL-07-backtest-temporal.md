# VAL-07 — Não fazer backtest temporal nesta fase (v2.4)

**Status:** Aceita
**Data:** 2026-07-20
**Fase:** 14 (Validação honesta / VAL)
**Requisito:** VAL-07 — "decisão tomada e escrita: PIT real ou não fazer"

## Contexto

O marco v2.4 pergunta se o motor de valuation é validado por um **backtest temporal** — rodar o
modelo sobre fundamentos históricos e comparar o veredito com o que o preço fez depois. É uma
âncora tentadora porque parece "objetiva". Mas o v2.3 já mostrou o custo de uma validação
mal-desenhada: gastou **~8 graus de liberdade sobre 4 observações** e chamou de "4/4 PASS" um
resultado que era 2/4. Uma métrica temporal ingênua repetiria o erro com uma cara de rigor.

## Decisão

**NÃO fazer backtest temporal nesta fase.** A validação do v2.4 é o hold-out estratificado
(distribuição + jackknife contra Graham+Bazin) + o teste soberano do caso do livro (VAL-01) —
âncoras que não dependem de reconstrução histórica.

## Justificativa

Um backtest temporal **honesto** exige informação **point-in-time (PIT)**: para cada data de
decisão, usar apenas o que estava **disponível naquela data**. Isso é inviável de forma confiável
só com dados gratuitos:

1. **Lag de disponibilidade da DFP.** Uma demonstração financeira anual não existe no fechamento
   do ano — ela é publicada com ~2–3 meses de atraso (a DFP de 2022 só passou a existir em
   mar/2023). Um PIT correto teria de mapear a **data de publicação** de cada DFP, não a data de
   competência.
2. **Reconstrução de preço e taxa livre de risco da época.** O `Ke` e a margem de segurança
   dependem do `rf` (Selic) e do preço **vigentes na data de decisão** — reconstruí-los sem viés
   exige uma série histórica limpa que não temos de graça de forma auditável.
3. **Um backtest ingênuo é vazamento de futuro.** Usar a DFP na data de **competência** (fechamento)
   em vez da data de **publicação** injeta informação que o investidor não tinha — é
   **look-ahead bias / vazamento de futuro**. O resultado é um número **confiante e falso**, que é
   **pior que nenhum**: ele daria uma falsa sensação de validação e mascararia exatamente o tipo de
   overfit que o v2.4 existe para corrigir.

Como o requisito VAL-07 pede explicitamente "**PIT real ou não fazer**", e o PIT real não é viável
com o orçamento (custo zero) e os dados desta fase, a decisão correta e escrita é **não fazer** —
sem gastar nenhum grau de liberdade do orçamento (3 knobs: ERP, n_fade, PIB_real permanecem
intocados).

## Consequência

- O desenho do **PIT correto** fica registrado como **Future Requirement (v2.5+)**: mapear a data de
  disponibilidade de cada DFP + reconstruir preço/rf da época, antes de qualquer backtest temporal.
- Nenhum knob de valuation é tocado nesta fase por conta desta decisão.
- O código do harness de backtest (`src/analista/backtest.py`) carrega um comentário-âncora
  apontando para este ADR — é onde um futuro implementador de backtest tropeça primeiro, e o
  aviso o obriga a fazer PIT direito ou a não fazer.
