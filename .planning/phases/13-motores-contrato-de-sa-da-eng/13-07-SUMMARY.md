---
phase: 13-motores-contrato-de-sa-da-eng
plan: 07
subsystem: validacao
tags: [regressao-104, oraculo-ke04, rim-unico, degrade-not-crash, cross-menu-wr03, blind-04a-safe, ranking-screener]

requires:
  - phase: 13-motores-contrato-de-sa-da-eng
    plan: 04
    provides: "Ponte P/B (pb_justo/payout_terminal) + guard runtime D-10a (razao_patologica sinaliza, degrada veredito)"
  - phase: 13-motores-contrato-de-sa-da-eng
    plan: 06
    provides: "Ranking rebaixado a screener por multiplos crus (cmd_rank sem analisar_acao/macro); test_cli_rank_consistencia DELETADO"
provides:
  - "test_eng_validacao.py (invariante, BLIND-04a-safe): o COLAPSO provado por EXECUCAO sobre os 104 reais — o oraculo herdado de KE-04, agora sob o RIM unico"
  - "test_cli_rank_consistencia.py RECRIADO e reconciliado ao Ranking-screener: cross-menu WR-03 = multiplos crus (ROE/P/L/EY) identicos rank<->analyze"
affects: [14-validacao]

tech-stack:
  added: []
  patterns:
    - "Prova por EXECUCAO (memoria guardrails-devem-ser-provados-por-execucao): rodar a regressao dos 104, nao 'suite verde' generica, e a evidencia de blindagem"
    - "Reconciliacao de teto de contrato: quando o sistema muda sob o teste (rank virou screener), recriar a propriedade CURRENT (multiplos crus), nao ressuscitar a morta (ke/intrinseco cross-menu)"
    - "Invariante degrade-not-crash: a razao patologica FICA visivel (lente auditavel) e e SINALIZADA (razao_patologica=True), nunca apagada nem crashando"

key-files:
  created:
    - tests/test_eng_validacao.py
    - tests/test_cli_rank_consistencia.py
  modified:
    - tests/classificacao.yaml

key-decisions:
  - "Invariante P/B por DEGRADE-NOT-CRASH (nao 'razao sobrevivente sempre in-band'): o guard D-10a do 13-04 NAO apaga pb_justo/payout_terminal (sao lente auditavel) — SINALIZA (razao_patologica=True) e degrada o veredito. O invariante da cesta real e: razao in-band OU sinalizada, nunca patologia muda"
  - "Cross-menu WR-03 RECONCILIADO: a propriedade antiga (a.ke/intrinseco identicos rank<->analyze) morreu no 13-06 (rank virou screener sem valuation). Recriado provando o que SOBREVIVE: ROE/P/L/EY do screener == a.multiplos do Analisar (fonte canonica unica de CompanyData, FIX-04)"

requirements-completed: [ENG-01, ENG-08, ENG-09]

duration: 35min
completed: 2026-07-20
---

# Phase 13 Plan 07: Validacao por execucao do colapso (regressao dos 104 + cross-menu) Summary

**O colapso esta PROVADO POR EXECUCAO: `test_eng_validacao.py` roda `report.analisar_acao` sobre os 104 reais (snapshot limpo, beta setorial carimbado, Ke offline identico ao app) e assere por distribuicao — sem nomear ticker, sem validar o caso do livro — os 4 invariantes do RIM unico: never-raise (`intrinseco_motor` finito>0 ou None), sem explosao (V<50x preco), razao P/B sa por DEGRADE-NOT-CRASH (o guard D-10a sinaliza a patologia, nao a apaga nem crasha) e caminho unico (`a.motor` sempre "rim"). O cross-menu WR-03 foi RECONCILIADO ao Ranking-screener do 13-06: a propriedade antiga (a.ke/intrinseco cross-menu) morreu com o rebaixamento; o teste recriado prova o que sobrevive — ROE/P/L/EY do screener identicos aos do Analisar. Suite default 470 passed / 1 skipped / 18 deselected / 0 failed; fronteira intacta (nenhum knob tocado).**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-07-20
- **Tasks:** 2
- **Files:** 3 (2 criados de teste; 1 config de teste modificado)

## Task Commits

1. **Task 1: Regressao dos 104 pos-colapso (finito, sem explosao, P/B sa, caminho unico)** — `86071c4` (test)
2. **Task 2: Cross-menu WR-03 reconciliado ao Ranking-screener** — `a9ad0da` (test)

## Accomplishments

- **O colapso provado por EXECUCAO (ENG-01, memoria `guardrails-devem-ser-provados-por-execucao`):** `test_eng_validacao.py::test_regressao_104_colapso_rim_unico` (`invariante`, BLIND-04a-safe) espelha o oraculo KE-04 (`test_regressao_104_sem_explosao`), agora sobre o RIM unico. Carrega `hs.CAMINHO_SNAPSHOT_LIMPO`, carimba beta setorial (`macro.carimbar_beta_setorial` — Ke offline identico ao app, D-06), roda `report.analisar_acao` offline sobre os 104 e reprova (com lista de ofensores) se qualquer um dos 4 invariantes falhar. **93 analisados, 0 ofensores.**
- **Invariante (1) never-raise + (2) sem explosao:** todo `intrinseco_motor` e finito e >0 OU None (degradado); zero NaN/inf/excecao; nenhum V >= 50x preco (teto adimensional de sanidade, sem nomear ticker).
- **Invariante (3) razao P/B sa por DEGRADE-NOT-CRASH (ENG-08/ENG-09):** a ponte P/B e uma LENTE auditavel — o guard D-10a do 13-04 NAO apaga `pb_justo`/`payout_terminal` (ficam visiveis) nem crasha: SINALIZA (`razao_patologica=True`) e degrada o veredito de preco. O invariante provado sobre a cesta real: toda razao computavel ou esta na faixa sa (`pb_justo` ∈ (0,6), `payout_terminal` ∈ (0,1] — meio-aberto por identidade do terminal zerado, nota load-bearing 13-01/13-04) OU foi sinalizada. Medido na cesta real: 6 tickers com razao fora da faixa, TODOS sinalizados (`razao_patologica=True`); o guard segurou.
- **Invariante (4) caminho unico (ENG-01):** `a.motor` e sempre "rim" sobre os 104 — nenhum ticker roteia para ddm/seguradora/normalizado/dcf/nav como motor primario. O ensemble morreu no 13-03 e a regressao prova por execucao que ha um so caminho.
- **Cross-menu WR-03 reconciliado ao mundo novo (Core Value cross-modo):** `test_cli_rank_consistencia.py` recriado. Roda `cmd_analyze` e `cmd_rank` offline sobre a mesma acao sintetica e assere que os multiplos crus que o screener ordena (ROE/P/L/EY, capturados via spy em `cmp.ranking_por_multiplos`) sao IDENTICOS aos que o Analisar expoe (`a.multiplos`, spy em `report.analisar_acao`) — a fonte canonica unica de `CompanyData` (FIX-04). Nao assere colunas removidas (preco-alvo/upside/veredito) nem `a.ke`/`intrinseco_motor` (que o rank nao produz mais).

## Deviations from Plan

### Reconciliacao com o 13-06 (obrigatoria, cross-plan)

**1. [Reconciliacao] Cross-menu WR-03 NAO ressuscita a propriedade morta (a.ke/intrinseco cross-menu)**
- **Onde:** Task 2
- **Contexto:** o plano 13-07 (`<interfaces>` e acceptance da Task 2) pedia para adaptar `test_cli_rank_consistencia.py` a casar `a.ke`/`intrinseco_motor` entre `analyze` e `rank`. Mas o 13-06 REBAIXOU o Ranking a screener por multiplos crus: `cmd_rank` **nao chama mais `report.analisar_acao` nem carimba macro** (sem `_carimbar_macro`, sem `a.ke`, sem `intrinseco_motor`). A propriedade cross-menu antiga **deixou de existir** (caminho morto, nao numero quebrado) e o teste que a travava foi DELETADO no 13-06.
- **Resolucao:** seguido o `<cross_plan_note>` e o goal real do plano (provar o colapso por execucao / Core Value cross-modo). O teste recriado prova a propriedade que SOBREVIVE ao rebaixamento: os multiplos crus (ROE/P/L/EY) do screener saem dos MESMOS metodos canonicos de `CompanyData` que o Analisar expoe. Nao assere `a.ke`/`intrinseco_motor` (o rank nao os produz) nem as colunas removidas.

### Interpretacao load-bearing (nao e bug)

**2. [Spec] Invariante (3) e DEGRADE-NOT-CRASH, nao "razao sobrevivente sempre in-band"**
- **Onde:** Task 1 (1a execucao FALHOU com 6 tickers de razao fora da faixa)
- **Motivo:** a leitura literal do must_have ("para todo ticker com razao computavel, payout_T ∈ (0,1) e P/B justo ∈ (0,6)") sugeria assertar que TODA razao nao-None esta na faixa. Mas o guard D-10a do 13-04 (report.py:352-374) NAO apaga a razao quando patologica — ela e uma LENTE auditavel que fica visivel; o guard seta `razao_patologica=True`, emite alerta e degrada o veredito. O proprio must_have qualifica: "ticker fora da faixa deve ter sido DEGRADADO/sinalizado, nao ter quebrado".
- **Resolucao:** o invariante assere `(pb_fora or payout_fora) => razao_patologica == True` (razao in-band OU sinalizada; nunca patologia muda). Isso PROVA o guard por execucao (o intervalo do payout usa (0,1] meio-aberto, IDENTICO ao guard runtime — nao e afrouxamento, e o mesmo contrato do 13-04). NENHUM guard/clamp novo introduzido (anti-goal respeitado).

**Total:** 1 reconciliacao cross-plan (obrigatoria), 1 interpretacao de spec (guard-driven). 0 bugs de producao. Nenhuma mudanca arquitetural; `config.yaml`/`calibracao.lock.yaml`/`src/` INTOCADOS.

## Notas de projeto

- **Fronteira com a Fase 14 respeitada:** a prova e por DISTRIBUICAO dos 104, nenhum ticker nomeado num assert, nenhum numero-alvo do livro (`grep -iE '37[.,]22|ITUB4' tests/test_eng_validacao.py tests/test_cli_rank_consistencia.py` == 0). O caso do livro (ITUB4 = R$ 37,22) NAO foi validado — e a validacao soberana da Fase 14.
- **6 tickers com razao P/B fora da faixa na cesta real, TODOS sinalizados.** Sao patologias de MODELO (spread/razao degenerada), nao explosoes de valor: o `intrinseco_motor` desses tickers segue finito e nao explode (a ponte e lente, nao motor). O guard D-10a degrada o veredito de preco deles para verificacao — o comportamento correto (degrade-not-crash), agora provado sobre a cesta real.

## Known Stubs

None — os testes rodam a engine real sobre dados reais (Task 1) e os dois entry points do CLI sobre uma acao sintetica (Task 2); nenhum valor placeholder. Nenhum codigo de producao tocado.

## Verification

- `.venv/bin/python -m pytest -k 'eng_validacao or cli_rank_consistencia' -q`: **2 passed**.
- `.venv/bin/python -m pytest -q` (default completa): **470 passed, 1 skipped, 18 deselected, 0 failed, 0 xfailed** (baseline 468 + 2 novos invariantes). O 1 skipped e o jackknife (Fase 14).
- `.venv/bin/python -m pytest -m golden_nivel -q`: **18 passed, 0 CLASSIFICACAO ORFA**; nenhum golden_nivel novo criado.
- BLIND-04a-safe: `grep -iE '37[.,]22|ITUB4' tests/test_eng_validacao.py tests/test_cli_rank_consistencia.py` == 0; nenhum ticker nomeado num assert.
- **Fronteira:** `git diff 86071c4^..HEAD -- config.yaml calibracao.lock.yaml src/` **VAZIO** — orcamento de 3 graus intacto, zero producao tocada (validacao pura).

## Self-Check: PASSED

- Files exist: `tests/test_eng_validacao.py`, `tests/test_cli_rank_consistencia.py`, `13-07-SUMMARY.md` — all FOUND.
- Commits exist: `86071c4` (T1), `a9ad0da` (T2) — all FOUND.
- Suite re-rodada: default 470 passed / 1 skipped / 18 deselected / 0 failed; `-m golden_nivel` 18 passed / 0 ORFA; config/lock/src diff VAZIO.

---
*Phase: 13-motores-contrato-de-sa-da-eng*
*Completed: 2026-07-20*
