---
phase: 08-saneamento-do-motor-ddm
plan: 03
subsystem: valuation
tags: [FIX-03, capm, ke, selic-bcb, custo-de-capital, golden-rebaseline, pureza-da-engine]

requires:
  - phase: 08-02 (FIX-02)
    provides: "trava g_alto ≤ Ke que agora consome o Ke local recalibrado (small cap BR)"
provides:
  - "CAPM 'local' como abordagem padrão: Ke = rf (Selic ao vivo BCB) + beta × ERP Brasil (0,06)"
  - "macro.selic_para_capm(fallback): resolvedor de rf com degradação graciosa (selic_meta None → fallback de config)"
  - "Pureza da engine: analisar_acao lê cfg['capm']['rf_local'] (offline); a rede vive nos entry points (cli/app)"
  - "tests/test_capm_local.py: golden offline do caminho ao vivo (Ke na faixa) + caminho fallback"
affects: [08-04 (FIX-06 regressão VULC3 — o intrínseco usa o novo Ke ~15-20%)]

tech-stack:
  added: []
  patterns:
    - "Rede só nos entry points (cli/app), nunca na engine: resolvedor injeta rf em cfg antes de analisar_acao (espelha o padrão selic_meta() or 0.105 do corte de DY)"
    - "app.py reusa selic_atual() cacheado (@st.cache_data) ⇒ 1 chamada de rede por execução, compartilhada com a métrica da sidebar"

key-files:
  created:
    - tests/test_capm_local.py
  modified:
    - config.yaml
    - src/analista/ingest/macro.py
    - src/analista/report/report.py
    - src/analista/cli.py
    - app.py
    - tests/test_consistencia_modos.py
    - tests/test_growth_reconciliacao.py

key-decisions:
  - "ERP Brasil = 0,06 (6%): ~4,5% de mercado maduro (Damodaran) + ~1,5% small-cap/iliquidez, aplicado SOBRE a Selic (que já precifica país+inflação)"
  - "rf_local default == selic_fallback (0,105): slot que os entry points sobrescrevem com a Selic ao vivo; mantém a engine determinística offline"
  - "Resolvedor com `selic_meta() or fallback` (espelha exatamente o padrão já usado no corte de DY) — degradação graciosa sem exceção"
  - "Caso-limite que flipou com o Ke maior é recalibrado na FIXTURE, nunca afrouxando assert (alvo crescente; PL do TRKE 1987→1700)"

patterns-established:
  - "Ke local ao vivo com fallback: a única chamada de rede mora no entry point; a engine é uma função pura de cfg"

requirements-completed: [DDM-FIX-03]

duration: ~25min
completed: 2026-06-26
---

# Phase 8 Plan 03: CAPM 'local' com Selic ao vivo (FIX-03) Summary

**O Ke deixa de ser o literal de fim de 2019 (9,43% — combustível do valuation explosivo do VULC3) e passa a ser calculado pela abordagem `local`: `Ke = rf (Selic ao vivo do BCB) + beta × ERP Brasil`, com fallback gracioso ao config quando o BCB cai — VULC3 sobe para 15,78% (fallback) / 19,53% (Selic ao vivo 14,25% em 2026), faixa de small cap BR.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2
- **Files modified:** 7 (1 criado, 6 modificados)
- **Tests:** 126 passed (121 baseline + 5 de test_capm_local)

## Ke do VULC3 com a nova calibração (registro pedido pelo plano)

| Cenário | rf | ERP | beta | Ke |
|---------|----|----|------|----|
| Antigo (eua_ajustada, literais 2019) | rf_us 1,92% + EMBI/inflação | erp_us 6,2% | 0,88 | **9,43%** |
| Novo — fallback (BCB indisponível) | selic_fallback 10,5% | erp_local 6% | 0,88 | **15,78%** |
| Novo — Selic ao vivo (BCB respondeu: 14,25% em 2026) | 14,25% | 6% | 0,88 | **19,53%** |

O Ke do VULC3 sobe de 9,43% para ~16–20% — materialmente acima dos literais de 2019 e dentro da
faixa de small cap BR (CONTEXT FIX-03: ~16–19%). O BCB respondeu ao vivo durante a execução (Selic
14,25%), confirmando o caminho-vivo; o caminho fallback (15,78%) é o que os testes exercitam offline.

## Accomplishments

- **CAPM 'local' como default:** `config.yaml` troca `abordagem` para `"local"` e adiciona `erp_local: 0.06`,
  `selic_fallback: 0.105` e `rf_local: 0.105` (slot sobrescrito ao vivo), com comentários de justificativa.
  Os literais legados (`rf_us`/`embi_brasil`/`erp_us`/`inflacao_*`) ficam intactos para a abordagem
  `eua_ajustada` continuar valendo como fallback de método (caso Itaú do livro).
- **Resolvedor de rf com fallback gracioso:** `macro.selic_para_capm(fallback)` devolve `selic_meta() or fallback`
  — Selic ao vivo do BCB quando disponível, senão o fallback do config, sem exceção (espelha o padrão do corte de DY).
- **Pureza da engine preservada:** `report.analisar_acao` lê `cfg['capm']['rf_local']`/`erp_local` e chama
  `capm.ke_local(c.beta, rf_local, erp_local)` — NÃO toca a rede (`grep -c selic_meta report.py` == 0). A engine
  é uma função pura de cfg; os testes a exercitam offline com o rf de fallback.
- **Rede isolada nos entry points:** `cli.cmd_analyze` injeta `cfg['capm']['rf_local'] = macro.selic_para_capm(...)`
  antes da engine; `app.py` reusa `selic_atual()` (já `@st.cache_data`) para injetar `CFG['capm']['rf_local']` —
  uma única chamada de rede por execução, compartilhada com a métrica da sidebar. `app.py` segue read-only.
- **Golden offline (test_capm_local.py):** cobre config documentado, Ke na faixa small cap BR, resolvedor ao vivo
  (monkeypatch selic_meta→0,15) e resolvedor fallback (monkeypatch→None), e a engine determinística offline.

## Task Commits

1. **Task 1 (RED): golden do CAPM 'local'** — `84ec9c3` (test)
2. **Task 1 (GREEN): branch 'local' + resolvedor + config** — `601e521` (feat)
3. **Task 2: injeção da Selic nos entry points + rebaseline de Ke** — `3f77add` (feat)

_TDD na Task 1: RED (test_capm_local falha 5/5) → GREEN (config+macro+report). Sem REFACTOR (mudança pontual)._

## Files Created/Modified

- `config.yaml` — bloco `capm`: `abordagem: "local"`, `erp_local: 0.06`, `selic_fallback: 0.105`, `rf_local: 0.105`,
  literais legados preservados.
- `src/analista/ingest/macro.py` — `selic_para_capm(fallback)`: resolvedor puro do rf (Selic ao vivo ou fallback).
- `src/analista/report/report.py` — branch `local` reescrito: `ke_local(c.beta, cap["rf_local"], cap["erp_local"])`;
  branch `else` (eua_ajustada) intacto; trava FIX-01 (g_alto ≤ Ke) preservada.
- `src/analista/cli.py` — `cmd_analyze` injeta `rf_local` resolvido em cfg antes de `analisar_acao`.
- `app.py` — Analisar injeta `CFG['capm']['rf_local'] = selic_atual()` (cacheado) antes de `analisar_acao`.
- `tests/test_capm_local.py` (novo) — 5 goldens offline/determinísticos.
- `tests/test_consistencia_modos.py` — rebaseline + novo helper `_empresa_param_crescente` (ver abaixo).
- `tests/test_growth_reconciliacao.py` — rebaseline do PL do caso-limite TRKE (ver abaixo).

## Rebaseline dos golden (com justificativa)

| Asserção / fixture | Antes | Depois | Por que o novo número é o correto pelo método |
|--------------------|-------|--------|-----------------------------------------------|
| `test_veredito_direcao_coerente` — fixture alvo | série constante, preço 6,00 (Ke 9,43% ⇒ vmin≈6,79) | série CRESCENTE ~14%/ano, preço 5,50 (Ke local 15,3% ⇒ vmin≈6,75, DY≈12,4%) | Com o Ke local ~15% e g_alto=0 (série constante), o múltiplo do DDM (~6,9×) cola no limiar de DY (1/0,15≈6,67×): qualquer preço abaixo do intrínseco dispara o flag DY>15% (FIX-05) e o veredito vira "VERIFICAR", não "SUBAVALIADA". Uma empresa que CRESCE (g_alto>0) eleva o intrínseco bem acima do piso de DY, recuperando uma alvo claramente SUBAVALIADA (vmin 6,75 > preço 5,50; DY 12,4% < 15%) **sem afrouxar nenhum assert**. |
| `test_trava_ke_quando_g_fund_supera_ke` — PL do TRKE | PL 1987 (ROE_val≈0,30 ⇒ g_fund≈0,15 > Ke antigo 0,0875) | PL 1700 (ROE_val≈0,35 ⇒ g_fund≈0,175 > Ke novo 0,153) | O caso-limite testa "g_fund > Ke ⇒ a trava ≤Ke é o teto efetivo". O Ke local (0,153 com beta 0,8) ultrapassou o g_fund antigo (0,15), desligando a condição. Baixar o PL recompõe ROE_val/g_fund acima do novo Ke, mantendo o mesmo assert `g_alto == Ke`. |

`test_ddm.py::test_ke_itau_capm` (Ke 12,48% do livro pela `ke_eua_ajustada`) permanece **inalterado e verde** — é a
regressão da fórmula do livro pela abordagem legada, não tocada por esta mudança. Os demais goldens
(`test_growth_reconciliacao` casos 1–3, `test_fundamentals_consistencia`, `test_multiples`, `test_normalizacao`,
`test_report`) não dependem do Ke e seguem intactos.

## Decisions Made

- **ERP Brasil = 0,06.** Aplicado SOBRE a Selic (que já precifica risco-país + inflação), o ERP é só o prêmio de
  equity: ~4,5% de mercado maduro (Damodaran) + ~1,5% de prêmio small-cap/iliquidez. Com a Selic 2-dígitos de 2026
  e beta < 1, o Ke aterrissa na faixa small cap BR (VULC3: 15,78%–19,53%).
- **`rf_local` default == `selic_fallback`.** O slot `rf_local` é o que os entry points sobrescrevem com a Selic
  ao vivo; deixá-lo igual ao fallback no config faz a engine rodar offline/determinística nos testes sem rede.
- **Resolvedor `selic_meta() or fallback`.** Espelha exatamente o padrão já existente no corte de DY (cli.py:85 /
  app.py:41), em vez de inventar uma assinatura nova — consistência de encanamento e degradação graciosa.
- **Caso-limite flipado recalibra a FIXTURE, nunca o assert.** O Ke maior derrubou dois casos discriminantes;
  ambos foram recompostos nos dados (alvo crescente; PL do TRKE) com justificativa, preservando os asserts.

## Deviations from Plan

None - plan executado como escrito. O plano antecipou o rebaseline; a única nuance emergente foi que o caso-limite
de SUBAVALIADA não bastava baixar o preço (o flag DY>15% do FIX-05 o transformaria em "VERIFICAR") — a recalibração
correta foi tornar a alvo uma empresa que cresce (g_alto>0), documentada na fixture e na tabela de rebaseline acima.
Decisão dentro do mandato do plano ("recalibrar fixtures se um caso-limite flipar, nunca afrouxar assert").

## Issues Encountered

None.

## Known Stubs

Nenhum. O resolvedor consome dado real (BCB SGS) com fallback de config; a engine consome o rf resolvido.

## Threat Flags

Nenhuma nova superfície além da já registrada no threat_model do plano. T-08-05 (BCB indisponível/lento durante
analisar_acao) **mitigado**: a rede vive só nos entry points; a engine é offline e o resolvedor degrada para o
`selic_fallback` do config sem exceção (test_resolvedor_rf_degrada_para_fallback). T-08-06 (Selic absurda)
**aceito**: `macro.selic_meta` já valida parse/exceções → None, e o dado do BCB é público.

## Next Phase Readiness

- 08-04 (FIX-06, regressão VULC3): o intrínseco do VULC3 agora desconta a um Ke ~16–20% (não 9,4%) — o caso de
  regressão deve cravar um intrínseco materialmente mais baixo, fechando o terceiro vetor da cascata (Ke baixo).
- A trava `g_alto ≤ Ke` (FIX-01) e a reconciliação g×payout (FIX-02) já consomem o novo Ke de forma robusta.

## Self-Check: PASSED

- Arquivos verificados: config.yaml, macro.py, report.py, cli.py, app.py, test_capm_local.py,
  test_consistencia_modos.py, test_growth_reconciliacao.py, 08-03-SUMMARY.md — todos presentes.
- Commits verificados: 84ec9c3 (test RED), 601e521 (feat GREEN), 3f77add (feat Task 2) — todos no histórico.
- Suíte: 126 passed; test_ke_itau_capm intacto; engine offline (grep selic_meta em report.py == 0).

---
*Phase: 08-saneamento-do-motor-ddm*
*Completed: 2026-06-26*
