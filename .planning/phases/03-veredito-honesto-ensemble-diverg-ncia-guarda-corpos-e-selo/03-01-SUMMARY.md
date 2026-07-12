---
phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo
plan: 01
subsystem: valuation-engine
tags: [python, veredito, ensemble, divergencia, arquetipo, selo, rim, ddm]

# Dependency graph
requires:
  - phase: 01-classificador-de-arqu-tipo-roteamento
    provides: "arquétipo + registry arquétipo→motor; campos arquetipo/motor/candidatos/fronteirico"
  - phase: 02-motores-por-arqu-tipo
    provides: "intrinseco_motor/motor_rotulo calculados pelo motor do arquétipo (RIM/normalizado/DCF/NAV); DDM rebaixado a lente onde motor != ddm"
provides:
  - "Banda do ensemble (motor × contraponto DDM) alimentando o veredito quando motor != ddm (VER-01)"
  - "Selo consome o motor do arquétipo (não o DDM fixo) via os prefixos SUB/NO INTERVALO/SOBRE já casados por selo.faixa_do_veredito"
  - "Bandeira de divergência motor×contraponto (>2×) com razão + hipótese curada exibidas (ENS-01)"
  - "config.yaml: veredito.margem_seguranca (fallback D-01 quando o contraponto degrada)"
affects: [03-02-SAN-01-guarda-corpos, 03-03-VER-02-fronteirico, app.py-render, cli-render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Banda do ensemble na borda do veredito: min/max entre motor primário e mid do contraponto DDM"
    - "Hipótese curada por (arquétipo, sinal) — dicionário-tupla estilo _MATRIZ_LEITURA/_MATRIZ"
    - "Reuso do helper puro comparables.divergencia_entre_lentes no funil single-stock (antes só na CLI)"

key-files:
  created: []
  modified:
    - "src/analista/report/report.py"
    - "config.yaml"
    - "tests/test_report.py"
    - "tests/test_arquetipo_roteamento.py"

key-decisions:
  - "Contraponto universal = mid do DDM (D-02); capturado em contraponto_valor ANTES da banda ser sobrescrita"
  - "Banda do ensemble = min/max(intrinseco_motor, contraponto); fallback ± veredito.margem_seguranca quando o contraponto degrada (D-01)"
  - "Rebaseline deliberado de test_arquetipo_roteamento: motor não-DDM agora produz veredito real (banda_do_motor) em vez do texto de suspensão D-06"
  - "Ramo terminal de degradação reusa o prefixo VERIFICAR (selo suprime faixa) — nunca faixa falsa"

patterns-established:
  - "Veredito único SUB/NO INTERVALO/SOBRE para ddm E não-ddm, alimentado pela banda certa"
  - "Bandeira de divergência: informação exibida (dois números + porquê), nunca cravar o pior número"

requirements-completed: [VER-01, ENS-01]

# Metrics
duration: ~40min
completed: 2026-07-12
---

# Phase 3 Plan 01: Veredito Honesto — Selo consome o motor do arquétipo + bandeira de divergência Summary

**O selo/veredito passa a consumir o motor do arquétipo (RIM p/ ITUB4) via banda do ensemble motor×contraponto DDM, com bandeira de divergência (>2×) exibindo razão + hipótese curada — o DDM vira lente conservadora e o compounder de qualidade nunca mais é carimbado "evitar" pelo DDM de estágio único.**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-07-12
- **Tasks:** 3
- **Files modified:** 4 (report.py, config.yaml, test_report.py, test_arquetipo_roteamento.py)

## Accomplishments
- **VER-01:** o ramo de suspensão D-06 (`if a.motor != "ddm": → VERIFICAR`) foi SUBSTITUÍDO por veredito real. A árvore SUB/NO INTERVALO/SOBRE é agora ÚNICA para ddm e não-ddm, alimentada pela banda do motor. O selo consome o motor certo (ITUB4/RIM → "Boa, mas cara" com BSD alto, nunca "Evitar").
- **ENS-01:** a divergência motor×contraponto DDM (>2×) vira bandeira exibida — razão + hipótese curada por `(arquétipo, sinal)` — reusando o helper puro `comparables.divergencia_entre_lentes` (antes só na CLI multi-ticker).
- **Banda do ensemble:** `vmin/vmax = min/max(intrinseco_motor, mid do DDM)` quando motor != ddm; fallback `± veredito.margem_seguranca` quando o contraponto degrada.
- **Invariantes preservadas:** TAEE11 (motor==ddm) bit-idêntica; VULC3 continua "VERIFICAR" por armadilha real (payout>100%); firewall selo↛report intacto; `comparables.py`/`ddm.py`/`selo.py` não tocados.

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1: Campos de divergência + banda do ensemble** - `fa9213d` (test) → `b02abb3` (feat)
2. **Task 2: VER-01 — substituir o ramo de suspensão D-06 por veredito real** - `fbcc25d` (feat, inclui rebaseline dos goldens)
3. **Task 3: Hipótese curada por (arquétipo, sinal) + render da bandeira** - `56b56ad` (test) → `1669009` (feat)

_Note: Task 2 combinou os testes VER-01 (novos + rebaseline) e a implementação num único feat commit._

## Files Created/Modified
- `src/analista/report/report.py` — 5 campos novos em `AnaliseAcao` (contraponto_valor, banda_do_motor, divergencia_ativa, divergencia_razao, divergencia_hipotese); bloco de ensemble após `_guarda_faixa_ddm`; árvore de veredito unificada (subst. suspensão D-06); `_HIPOTESE_DIVERGENCIA` + `_hipotese_divergencia`; bloco "Bandeira de divergência" em `relatorio_markdown`.
- `config.yaml` — novo bloco top-level `veredito:` com `margem_seguranca: 0.15`.
- `tests/test_report.py` — testes do ensemble/banda/fallback, VER-01 (veredito real + degradação), hipótese curada e render da bandeira.
- `tests/test_arquetipo_roteamento.py` — rebaseline deliberado dos goldens da suspensão D-06 (ver Deviations).

## Decisions Made
- **Contraponto = mid do DDM** (D-02), capturado em `contraponto_valor` antes de a banda do ensemble sobrescrever `vmin/vmax` — análogo a `cli.py:220`.
- **Banda do ensemble** = min/max entre motor e contraponto; **fallback D-01** `± cfg["veredito"]["margem_seguranca"]` (leitura defensiva `.get(...,0.15)`, paridade WR-03) quando o contraponto degrada.
- **Ramo terminal de degradação** (motor não-DDM sem banda) reusa o prefixo VERIFICAR — o selo suprime faixa/rótulo (selo.py:119), nunca estampa faixa falsa.
- **Alerta honesto** declara o DDM como lente conservadora e nomeia o motor primário sempre que `banda_do_motor`.

## Deviations from Plan

### Rebaselines declarados (intencionais)

**1. [Rule 3 - Blocking] Rebaseline dos goldens de suspensão D-06 em `test_arquetipo_roteamento.py`**
- **Found during:** Task 2 (VER-01)
- **Issue:** 5 testes (`test_financeira_suspende_veredito_e_nao_estampa_evitar`, `test_financeira_rim_destrava_vs_ddm_e_segue_verificar`, `test_ciclica_roteia_lucro_normalizado`, `test_crescimento_roteia_dcf_positivo_finito`, `test_holding_roteia_nav_igual_vpa`) cravavam `a.veredito.startswith("VERIFICAR")` e `selo.rotulo is None` — o comportamento de suspensão da Fase 2 que a VER-01 DELIBERADAMENTE substitui. O plano previa esse rebaseline ("rebaseline SÓ com intenção declarada no SUMMARY").
- **Fix:** Reescritas as asserções para o novo contrato VER-01: motor não-DDM agora tem `banda_do_motor is True`, veredito real (sem o texto "só na Fase 3"), e o selo consome o motor (`rotulo != "Evitar"`, faixa casada por `faixa_do_veredito`). Nenhum prefixo NOVO foi introduzido — apenas os prefixos existentes SUB/NO INTERVALO/SOBRE/VERIFICAR passam a ser alimentados pela banda certa, então `selo.faixa_do_veredito`/`_veredito_token` NÃO precisaram mudar.
- **Files modified:** `tests/test_arquetipo_roteamento.py`
- **Verification:** `pytest tests/test_arquetipo_roteamento.py -q` → verde.
- **Committed in:** `fbcc25d` (parte do commit da Task 2)

**Total deviations:** 1 rebaseline declarado (Rule 3). Nenhum prefixo de veredito novo; `selo.py` não tocado.
**Impact on plan:** Rebaseline necessário e previsto pelo plano — é exatamente a mudança de comportamento que a VER-01 entrega. Sem scope creep.

## Issues Encountered
- **VULC3 rota para motor==ddm:** confirmei via probe que a fixture VULC3 (setor "Têxtil e Vestuário") cai no default `pagadora_regulada` → motor `ddm`, então a banda do ensemble NÃO é acionada e `test_vulc3_regressao` (que trava `vmin/vmax == min/max da matriz de sensibilidade DDM`) permanece verde sem ajuste. Isso validou que o guard `if a.motor != "ddm"` protege corretamente o caminho DDM.

## Known Stubs
None — VER-01/ENS-01 estão totalmente ligados ao veredito/render. SAN-01 (guarda-corpo anti-aberração completo) e VER-02 (dúvida honesta no fronteiriço) são escopo explícito de 03-02/03-03; o backstop residual "todo evitar passa pelos guarda-corpos" é 03-02.

## Next Phase Readiness
- **03-02 (SAN-01):** o guarda-corpo anti-aberração (`_guarda_san01` à la `_guarda_faixa_ddm`) entra na mesma borda do veredito. O caso residual a cobrir: motor não-DDM cujo motor degrada (`intrinseco_motor None`) e o DDM reassume a banda — hoje isso pode produzir um veredito DDM; o SAN-01 é o backstop.
- **03-03 (VER-02):** os campos `arquetipo_fronteirico`/`arquetipo_candidatos` seguem prontos; o range dos candidatos + bandeira usa o mesmo dispatch de motor.
- Suíte completa: **415 passed**.

## Self-Check: PASSED

- Files created/modified present: report.py, config.yaml, test_report.py, test_arquetipo_roteamento.py, 03-01-SUMMARY.md ✓
- Commits exist: fa9213d, b02abb3, fbcc25d, 56b56ad, 1669009 ✓
- Full suite: 415 passed ✓
- Firewall selo↛report intacto; comparables/ddm/selo não tocados ✓

---
*Phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo*
*Completed: 2026-07-12*
</content>
</invoke>
