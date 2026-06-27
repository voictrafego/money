# Phase 9: Payout sustentável + DY recorrente (núcleo de metodologia) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-27
**Phase:** 9-Payout sustentável + DY recorrente (núcleo de metodologia)
**Areas discussed:** Critério de "ano não-recorrente", Janela + fallback do payout, Como derivar o DY recorrente, Papel do clamp 1.0

---

## Estimador do payout sustentável (núcleo — cascateia p/ as 4 áreas)

| Option | Description | Selected |
|--------|-------------|----------|
| Mediana da série completa | mediana de payout(ano) sobre toda a história, sem threshold/exclusão; VULC3→43%, TAEE11→216% preservado | ✓ |
| Expurgo explícito >100% + média | marcar anos >100% como extraordinários, média dos restantes — QUEBRA no TAEE11 (zero anos sobram) | |
| Outro critério robusto (winsor/MAD) | média winsorizada ou desvio robusto da mediana | |

**User's choice:** Mediana da série completa.
**Notes:** Decisão embasada em diagnóstico multi-ticker ao vivo. TAEE11 (payout >100% em TODOS os 10 anos, política recorrente de transmissora) é o contraexemplo que invalida o critério de limiar absoluto >100%. A mediana da série completa captura "desvio do próprio histórico" sem threshold nem constante por empresa.

## Metodologia completa (DY rec. + clamp)

| Option | Description | Selected |
|--------|-------------|----------|
| Confirmo, escrever CONTEXT | DY rec = payout_sust × lucro_norm; payout sust = mediana série completa, sem clamp; piso do g_alto trata >100%; efeito na regressão do Ranking → Fase 10 | ✓ |
| Clampar só na regressão | igual, mas já decidir clamp 1.0 na entrada da regressão do Ranking | |
| Ajustar algo | rever derivação do DY rec ou clamp | |

**User's choice:** Confirmo, escrever CONTEXT.
**Notes:** DY recorrente earnings-based validado (TAEE11 8,3% ≈ dividend-based real 8,1%; VULC3 20,4%→6,2%). Sem clamp; o piso `g_alto = max(0,…)` existente trata payout >100%. Efeito cruzado da regressão do Ranking (payout uncapped) registrado como consideração da Fase 10.

---

## Claude's Discretion

- Assinatura/local exatos dos métodos (estender `payout_valuation` vs novo `payout_sustentavel`; primitiva em `normalizacao.py` vs `fundamentals.py`) — a critério do planner, mantendo a primitiva pura sem ciclo de import.
- Knob de config (se houver) segue o padrão do bloco `normalizacao` do config.yaml.

## Deferred Ideas

- Clampar payout só na entrada da regressão de P/L do Ranking → Fase 10 (de-poison).
- Payout-alvo por setor configurável → Future (v2+).
- Sinalização de "ano extraordinário" na tabela de Fundamentos por ano → Future (v2+).
