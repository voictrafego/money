---
phase: 08-sanidade-dos-dados-san
plan: 04
subsystem: core
tags: [sanidade, checks, san, valuation-regression, minoritarios, jcp, clean-surplus, splits, never-raise]

# Dependency graph
requires:
  - phase: 08-sanidade-dos-dados-san
    provides: "CompanyData com market_cap/splits/proventos_filtro_amplo/lucro_controlador/origem_num_acoes (08-01) + snapshot congelado offline (08-03)"
provides:
  - "core/sanidade.py — 5 checks aritméticos puros (checar_san01..05) + Aviso + _bucket (D-07) + 6 limiares (D-10)"
  - "tests/test_sanidade_checks.py — os checks provados no snapshot congelado, nos tickers do ROADMAP (contrato)"
  - "tests/test_sanidade_limiares.py — os 6 limiares congelados (D-11) + simetria SAN-02 + never-raise do _bucket (invariante)"
affects: [09-ingestao-correta-data, 10-primitivas-sem-vies-prim]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Check puro sobre CompanyData: never-raise, None quando o insumo falta (não avaliável != limpo)"
    - "_bucket em STRING (ordem de grandeza) — imune ao detector BLIND-04a e a re-download do Yahoo; nunca levanta com fator <= 0 (opera sobre abs, '~0' para zero)"
    - "SAN-03 com dois sinais: detector interno à CVM (imune ao num_acoes quebrado) + reconciliação que reporta DIVERGÊNCIA sem eleger verdade"
    - "Limiar de detecção como constante de módulo, fora do config.yaml/lock (não é knob de valuation)"

key-files:
  created:
    - "src/analista/core/sanidade.py"
    - "tests/test_sanidade_checks.py"
    - "tests/test_sanidade_limiares.py"
  modified:
    - "tests/classificacao.yaml"

key-decisions:
  - "Os limiares (D-10) são constantes de MÓDULO, fora do config.yaml e do calibracao.lock.yaml — limiar de detecção não move Ke/g/preço, logo não é knob de valuation; o lock segue com 3 graus"
  - "sinal_invertido do SAN-04 = (minoritários) e (controlador) com sinais opostos ((LL-LLc)*LLc<0) — captura o CSNA3 (minoritários +0,496bi, controlador -2,00bi, ambos consolidado/controlador negativos)"
  - "BBAS3 removido da lista 'bancos limpos' do teste SAN-04: ele flaga legitimamente (~22% de minoritário no lucro) — o check reporta divergência, não bug para calar"

requirements-completed: [SAN-05]

# Metrics
duration: 18min
completed: 2026-07-15
---

# Phase 8 Plan 04: Os 5 Checks Aritméticos (SAN-01..05) Summary

**`core/sanidade.py` entrega os cinco checks de sanidade como funções puras (espelho de `normalizacao.py`, zero I/O, zero dependência nova): escala de nível (SAN-01), salto temporal simétrico (SAN-02), JCP perdido + reconciliação CVM↔Yahoo (SAN-03), base dos minoritários (SAN-04) e clean surplus (SAN-05) — com os 6 limiares congelados FORA do `calibracao.lock.yaml`. Nada conserta nada: os asserts SÃO o teste de regressão da Fase 9, provados contra o snapshot congelado dos 104, e vistos disparando nos tickers que o ROADMAP nomeia.**

## Performance

- **Duration:** ~18 min
- **Completed:** 2026-07-15
- **Tasks:** 3
- **Files:** 3 criados + 1 modificado

## Accomplishments

- **SAN-01** (`checar_san01`) flaga a escala quebrada de `num_acoes × preço / market_cap`: GOAU4 (2,97×) e CGRA4 (0,0008×) acendem; ITUB4 (1,03×) e BRSR6 (1,00×) ficam limpos; o **MRFG3** (404 no Yahoo → `market_cap = None`) devolve `None` (não avaliável — o caso vivo do never-raise).
- **SAN-02** (`checar_san02`) é **simétrico** (`max(r,1/r) >= 3`): pega o salto nos DOIS anos (BRSR6 `÷~0` em 2020 **e** `×205.099` em 2021; ITUB4 `÷1000` em 2019 **e** `×780` em 2020). Isenta desdobramento real (D-12, extração do ano por `int(chave[:4])`, sem `datetime`) e **pula a fronteira de fonte** (EQTL3 muda CVM→Yahoo em 2018 → salto artificial, não flagado). `num_acoes[t]==0` vira `r=0` → `_bucket("~0")`, não `ZeroDivisionError`.
- **SAN-03** (`checar_san03`) tem **dois sinais**: (a) o **detector direto de JCP perdido** (`Σ proventos_filtro_amplo / Σ dividendos > 1,10`, 100% interno à CVM, imune ao `num_acoes` quebrado) — pega o **BRSR6** (11,5×) e deixa o **ITUB4** limpo (1,0×); (b) a **reconciliação CVM↔Yahoo** que **reporta divergência sem eleger verdade** (o `detalhe` manda cruzar com SAN-01/SAN-02). Cascata esperada e legítima (BBAS3/BRSR6 acendem (b) por escala).
- **SAN-04** (`checar_san04`) pega a base cruzada `LL/LL_controlador`: GOAU4 (2,97×), EQTL3 (1,49×), ALUP11 (1,43×), MRFG3 (2,13×) e o **CSNA3** (0,752×, `sinal_invertido=True` — minoritários +0,496bi contra controlador −2,00bi). `bucket = _bucket(abs(razao))` — nunca passa razão negativa ao `_bucket`.
- **SAN-05** (`checar_san05`) reporta o clean surplus (`mediana |ΔB − (LL − DIV)| / |PL| > 10%`) **como DADO** (o resíduo mediano no `fator`, adimensional), nunca como exceção.
- **Zero conserto de dado:** `git diff src/analista/ingest/` **vazio**. Suíte: **450 passed, 1 skipped, 38 deselected, 2 xfailed, 0 failed**; BLIND-04a e o orçamento de knobs intactos.

## Task Commits

1. **Task 1: limiares, Aviso, _bucket, SAN-01 e SAN-02** — `dab2f27` (feat)
2. **Task 2: SAN-03 (JCP + reconciliação), SAN-04 (minoritários), SAN-05 (clean surplus)** — `2f02698` (feat)
3. **Task 3: prova os 5 checks no snapshot + congela os limiares + classificacao.yaml** — `afe494f` (test)

## Files Created/Modified

- `src/analista/core/sanidade.py` — 5 checks puros + `Aviso` (com `sinal_invertido`) + `_bucket` (string, never-raise) + 6 limiares + `_soma_pareada`; docstring do módulo declara as 3 verdades (SAN-01/02 = mesmo bug; limiares não são knobs; nada conserta nada).
- `tests/test_sanidade_checks.py` — 10 testes `contrato`, asserts de PERTINÊNCIA (zero constante de nível), offline sobre o snapshot congelado.
- `tests/test_sanidade_limiares.py` — 5 testes `invariante`, zero literal de ticker (usa `ZZZZ9`); congela os 6 limiares, prova a simetria do SAN-02, a isenção por split e o never-raise do `_bucket`.
- `tests/classificacao.yaml` — 15 entradas novas (10 `contrato` + 5 `invariante`).

## Decisions Made

- **Os limiares vivem no módulo, não no config/lock.** Limiar de detecção não move `Ke`/`g`/preço — não é knob de valuation. O `calibracao.lock.yaml` segue com exatamente 3 graus de liberdade; `test_limiares_nao_vivem_no_config_nem_no_lock` prova o D-10.
- **`sinal_invertido` = minoritários e controlador com sinais opostos** (`(LL − LL_controlador) × LL_controlador < 0`). É o que captura o CSNA3 (cujo consolidado e controlador são ambos negativos, mas o minoritário é positivo) e qualquer flip consolidado/controlador — sem jamais passar razão negativa ao `_bucket`.
- **A isenção por split é provada com CompanyData sintético** (`ZZZZ9`) no arquivo de limiares, onde número é permitido; no snapshot real a isenção nunca é load-bearing (o único caso, ITUB4 2018 = 1,5187×, já fica abaixo do limiar de 3×).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Premissa do plano medida como incorreta] BBAS3 flaga SAN-04 — sai da lista "bancos limpos"**
- **Found during:** Task 3 (prova do SAN-04 no snapshot)
- **Issue:** O plano listava BBAS3 em `test_san04_nao_flaga_os_bancos`, com base na % de minoritário no **PL** (2,3%). Medido no snapshot congelado, o **LL consolidado do BB supera o do controlador em ~22%** (16,78bi vs 13,70bi → razão 1,225 > limiar 0,10) — minoritário REAL de subsidiárias consolidadas, no LUCRO, não no PL. O SAN-04 flaga o BBAS3 corretamente.
- **Fix:** O teste `test_san04_nao_flaga_os_bancos_limpos` cobre os bancos genuinamente limpos no lucro (ITUB4 2,2%, BBDC4 1,1%, BRSR6 0,04%). BBAS3 documentado no docstring do teste como flag legítima. **Nenhum limiar afrouxado, nenhum xfail casual** — o check reporta divergência, não elege verdade (Fase 9 decide se é bug ou minoritário real).
- **Files modified:** tests/test_sanidade_checks.py
- **Verification:** `pytest -k san04` verde; `checar_san04(BBAS3)` devolve Aviso (medido).
- **Committed in:** `afe494f`

**2. [Rule 1 - Número do plano medido como diferente] ALUP11 flaga SAN-01 no snapshot congelado (0,586×), não ≈0,98×**
- **Found during:** Task 1 (medição do SAN-01)
- **Issue:** O `<interfaces>` do plano dizia "ALUP11 ≈0,98 (mascarado)" — a expectativa de que a ALUP11 **não** acenderia o SAN-01. No snapshot congelado o fator é **0,586×** (`max(0,586; 1,706) ≥ 1,5`), então a ALUP11 **acende** o SAN-01 além do SAN-04.
- **Fix:** Nenhum — nenhum assert do plano exige a ALUP11 limpa no SAN-01 (os testes SAN-01 cobrem GOAU4/CGRA4 flagados e ITUB4/BRSR6 limpos). A ALUP11 continua atribuída ao SAN-04 pelo REQUIREMENTS; que ela também acenda o SAN-01 é o check funcionando (o `_fator_unit` não mascarou tanto quanto o plano previa). Documentado, nenhum conserto de dado.
- **Files modified:** nenhum
- **Committed in:** n/a

---

**Total deviations:** 2 (ambas premissas numéricas do plano corrigidas pela medição contra o snapshot congelado; nenhuma tocou dado, nenhuma afrouxou limiar).
**Impact on plan:** Ambas são "o check funcionando" — a Fase 8 existe exatamente para que o dado sujo dispare os checks. Os desvios ajustaram a EXPECTATIVA do teste à realidade medida, sem mexer no sistema.

## Issues Encountered

Nenhum além dos dois desvios. O snapshot congelado (08-03) tinha todos os insumos; os checks rodam 100% offline.

## Known Stubs

None. Os 5 checks leem insumos reais do `CompanyData` e devolvem `Aviso`/`None`/`[]` conforme o dado. O SAN-06 (never-raise estrutural) e o `aplicar_sanidade` (síntese de `confianca`) são o plano 08-05.

## Threat Flags

Nenhuma superfície nova além da já registrada no `<threat_model>` do plano (T-08-10 DoS por `log10(0)`/divisão-por-zero — mitigado: `_bucket` sobre `abs`/`"~0"`, guardas de denominador zero em todos os checks; T-08-11 afrouxar limiar — mitigado por `test_sanidade_limiares` invariante; T-08-12 limiar virar knob — mitigado por `test_limiares_nao_vivem_no_config_nem_no_lock`).

## Next Phase Readiness

- Os 5 checks existem como funções puras prontas para o `aplicar_sanidade` do plano 08-05 consumir (que os embrulha em try/except never-raise e sintetiza `confianca`).
- **Os asserts SÃO o teste de regressão da Fase 9 (DATA):** eles disparam HOJE nos tickers nomeados; quando a Fase 9 consertar `num_acoes`/`_fator_unit`/JCP, cada flag tem que APAGAR ticker a ticker — é a prova de conserto.
- **Registrado para a Fase 9:** o BBAS3 flaga SAN-04 por minoritário REAL de ~22% no lucro (não bug de escala) — a Fase 9 precisa distinguir minoritário legítimo de base cruzada ao consertar `lucro_controlador`.

## Self-Check: PASSED

- Arquivos criados existem: `src/analista/core/sanidade.py`, `tests/test_sanidade_checks.py`, `tests/test_sanidade_limiares.py` — todos FOUND.
- Commits no histórico: `dab2f27` (Task 1), `2f02698` (Task 2), `afe494f` (Task 3) — todos FOUND.
- Verificação: `pytest` inteiro **450 passed, 0 failed**; `pytest -k "sanidade_checks or sanidade_limiares"` verde offline; BLIND-04a verde; `git diff src/analista/ingest/` vazio; 15 entradas em `classificacao.yaml`; zero literal de ticker no arquivo de limiares.

---
*Phase: 08-sanidade-dos-dados-san*
*Completed: 2026-07-15*
