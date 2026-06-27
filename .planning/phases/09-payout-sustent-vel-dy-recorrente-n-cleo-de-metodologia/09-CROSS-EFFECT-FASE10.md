# Cross-effect (handoff Fase 10): payout sem clamp → regressão P/L do screening

**Registrado:** 2026-06-27 (Fase 9, Plan 03) — **NÃO resolvido aqui** (D-06 / out of scope).

## O efeito

A Fase 9 (Plan 02) trocou `payout_valuation()` para a **mediana sobre a série completa SEM
clamp em 1.0** (D-03). A mediana agora pode ser legitimamente >100% para quem distribui de
caixa regulatório acima do lucro contábil (TAEE11 ≈ 2.16). Esse valor sem clamp passa a fluir
para a **regressão de preço-alvo (P/L ~ f(payout, ROE))** do Ranking:

- `cli.py` L158-159: `cmp.preco_alvo_por_regressao(reg, c.payout_valuation(), c.roe_valuation(), c.lpa_valuation(), c.preco_atual)`
- `app.py` L472: mesma chamada (`preco_alvo_por_regressao(reg, c.payout_valuation(), …)`)
- Implementação: `src/analista/core/comparables.py` §`preco_alvo_por_regressao` (L133)

A regressão foi calibrada com **payout ∈ [0,1]**. Alimentá-la com payout ≈ 2.16 (TAEE11)
pode envenenar (`poison`) o ajuste P/L ~ f(payout, ROE) e distorcer o preço-alvo/Ranking.

## O que NÃO é afetado (fronteira D-06 preservada)

- O **BSD per-ano** usa `payout(ano)` **CRU** (`screening.py` L218 `media([c.payout(a) for a in anos])`
  e L257 no proxy `crescimento_por_fundamentos`), além do clamp absoluto da banda `REFERENCIA_BSD`
  (`payout: (0.0, 0.80)`, L192). É CRU por ano e **não** consome `payout_valuation()` → intacto.
- `screening.py` **NÃO foi editado** neste plano. Só o agregado de valuation mudou de base.

## Item de verificação para a Fase 10 (de-poison do screening)

Decidir se o payout deve ser **clampado SÓ na entrada da regressão** de P/L
(`preco_alvo_por_regressao`) — sem reintroduzir clamp no `payout_valuation()` canônico (que
deve seguir sem clamp, D-03). Verificar que TAEE11 (≈2.16) não distorce o Ranking/preço-alvo
após a decisão. A escolha do ponto de clamp é da **Fase 10**, não desta.
