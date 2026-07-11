---
phase: 01-classificador-de-arqu-tipo-roteamento
verified: 2026-07-11T14:30:00Z
status: gaps_found
score: 3/4 must-haves verified
overrides_applied: 0
gaps:
  - truth: "Rodar a engine (CLI/UI) em ITUB4, TAEE11, VALE3 e WEGE3 classifica e exibe o arquétipo do negócio (banco, pagadora regulada, cíclica, crescimento) antes do bloco de valuation"
    status: failed
    reason: >
      Reproduzido com dados REAIS da CVM (cache local, cd_cvm 5410, WEGE3, anos 2016-2023,
      offline via src.analista.ingest.cvm.fundamentos_do_ano): classificar() retorna
      chave='ciclica', fronteirico=False, confianca='alta' para WEGE3 — não 'crescimento'
      como a própria Success Criteria nomeia entre parênteses. O motivo é estrutural
      (CR-01 do code review já confirmado): _cv_lucro() mede o coeficiente de variação do
      NÍVEL BRUTO da série de lucro, que é dominado pela tendência de crescimento, não pela
      oscilação. Qualquer compounder real (WEGE3: ROE de valuation ≈25.8%, CV do lucro cru
      ≈0.61) ultrapassa ciclica_cv_min=0.40 e é roteado para cíclica com confiança ALTA —
      nem sequer cai no fallback honesto fronteiriço (ARQ-02), porque o candidato
      'crescimento' não chega a competir (payout/retenção não estava calculável no teste
      offline, mas mesmo quando calculável o tie-break de `distintos[0]` favorece cíclica
      por ordem de append, não por confiança). O golden test_roe_alto_retencao_alta_vira_crescimento
      (tests/test_arquetipo.py:103) usa apenas 3%/ano de crescimento (CV≈0.08), que fica
      abaixo do threshold e mascara completamente o defeito — por isso a suíte está 100%
      verde (354 passed) mas o comportamento real com WEGE3 (ticker citado explicitamente
      na Success Criteria) está incorreto.
    artifacts:
      - path: "src/analista/core/arquetipo.py"
        issue: "_cv_lucro (linhas 58-69) e seu uso em classificar() (linha 113) medem dispersão do nível bruto da série, não a oscilação relativa/detrended — não separa 'tendência de alta forte' de 'oscilação em torno de uma média estável'."
    missing:
      - "Detrend antes de medir oscilação: CV dos retornos ano-a-ano ((lucro[t]-lucro[t-1])/|lucro[t-1]|) ou dispersão dos resíduos de um ajuste log-linear, conforme já sugerido no code review (01-REVIEW.md CR-01)."
      - "Golden test com compounder realista (>=15%/ano de crescimento, ex.: réplica dos números reais de WEGE3) travando chave==CRESCIMENTO e fronteirico is False, para impedir regressão silenciosa como a atual."
  - truth: "UI Streamlit (app.py) exibe o arquétipo/motor antes do bloco de valuation, no mesmo nível que a linha 'Setor/Estágio' já exibida"
    status: partial
    reason: >
      app.py nunca referencia a.arquetipo nem a.motor em nenhum ponto do fluxo principal
      de renderização (grep vazio). Para arquétipos com motor_pendente (financeira/
      crescimento/cíclica/holding), o texto do veredito embute a frase "arquétipo X usa o
      motor Y" e por isso aparece indiretamente via st.warning(esc_md(v)) — mas para a
      pagadora regulada (TAEE11, motor='ddm', não suspenso) o veredito segue o formato DDM
      padrão (SUBAVALIADA/SOBREAVALIADA/NO INTERVALO) SEM qualquer menção ao arquétipo, e a
      UI não expõe a classificação em lugar nenhum nesse caso. Só o CLI
      (report.relatorio_markdown, usado por `python -m analista analyze TICKER`) tem uma
      linha dedicada e sempre visível "Arquétipo: X → motor Y" (report.py:452). Como o
      roadmap nomeia "CLI/UI" e o Streamlit (`streamlit run app.py`) é o primeiro modo de
      uso documentado no README e a interface principal do projeto (CLAUDE.md: "app
      Streamlit"), a ausência total de exibição explícita na UI é uma lacuna real, mesmo
      que a letra da Success Criteria possa ser lida como "CLI OU UI" (o CLI sozinho já
      satisfaz essa leitura).
    artifacts:
      - path: "app.py"
        issue: "Nenhuma referência a a.arquetipo/a.motor no fluxo principal de renderização (linhas ~880-935); caption da linha 881 mostra só 'Setor: ... · Estágio: ...'."
    missing:
      - "Exibir explicitamente algo como 'Arquétipo: {a.arquetipo} → motor {a.motor}' na UI Streamlit, junto ao caption Setor/Estágio (app.py:881), igual ao CLI — inclusive para o caso não-suspenso (pagadora regulada)."
---

# Phase 1: Classificador de Arquétipo + Roteamento Verification Report

**Phase Goal:** Erguer a etapa de classificação/roteamento que hoje não existe. A ferramenta
decide o arquétipo do negócio (financeira, pagadora regulada, compounder, cíclica, holding)
ANTES de valuar, a partir dos dados já puxados (setor CVM como filtro grosso + refino
quantitativo por ROE/retenção/oscilação de margem). Quando a confiança é baixa, marca como
fronteiriço e guarda 2-3 lentes candidatas. A escolha do motor passa por um registry
arquétipo→motor, com DDM plugado como primário da pagadora regulada — roteamento no funil de
report.py entre CAPM e a montagem do DDM, sem tocar nos motores.

**Verified:** 2026-07-11T14:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Rodar a engine (CLI/UI) em ITUB4, TAEE11, VALE3 e WEGE3 classifica e exibe o arquétipo antes do bloco de valuation | ✗ FAILED | ITUB4→financeira ✓, TAEE11→pagadora_regulada ✓, VALE3→ciclica ✓ (todos confirmados com dados CVM reais offline), mas **WEGE3→'ciclica' em vez de 'crescimento'** (chave nomeada explicitamente na própria Success Criteria), com confianca='alta' — não nem sequer fronteiriço. Reproduzido com dados reais de cache CVM (cd_cvm 5410). Ver gap CR-01 acima. Adicionalmente, a UI Streamlit (app.py) nunca exibe "Arquétipo → motor" de forma explícita (só o CLI faz isso de forma consistente). |
| 2 | Escolha do motor vem do registry arquétipo→motor; arquétipo sem motor primário cai em fallback explícito, não crash | ✓ VERIFIED | `ARQUETIPO_MOTOR` (arquetipo.py:36-42) é dict módulo-nível com as 5 chaves; report.py:151-153 resolve `motor = ARQUETIPO_MOTOR.get(arq.chave)`, `a.motor_pendente = motor is None`; veredito passa a "VERIFICAR — arquétipo X usa o motor Y, que chega na Fase 2" (report.py:203-219) — sem exceção, testado em `test_financeira_suspende_veredito_e_nao_estampa_evitar` e `test_petroleo_nao_vira_pagadora_regulada`. |
| 3 | TAEE11 (pagadora regulada) roteada para DDM primário; números/veredito idênticos; test_ddm/test_selo/test_consistencia_modos verdes | ✓ VERIFIED | Confirmado com dados CVM reais de TAEE11 (cd_cvm 20257, eh_concessionaria=True): `classificar()` retorna `pagadora_regulada`, motor='ddm'. `pytest tests/test_ddm.py tests/test_selo.py tests/test_consistencia_modos.py tests/test_guardrails_fix06.py tests/test_vulc3_regressao.py -q` → todos verdes (roda como parte da suíte completa de 354 passed). Fidelity fix nas fixtures (eh_concessionaria=True) confirmado via `grep -c "eh_concessionaria = True" tests/test_consistencia_modos.py` = 3. |
| 4 | Ticker de confiança baixa (híbrido/fronteiriço) marcado fronteiriço com 2-3 arquétipos candidatos | ✓ VERIFIED | `test_conflito_de_sinais_marca_fronteirico` (tests/test_arquetipo.py:114-123) e `test_fronteirico_via_funil_expoe_conflito` (tests/test_arquetipo_roteamento.py:148) passam; mecanismo em classificar() (linhas 121-127) crava `fronteirico=True` com `len(distintos)>=2` e `confianca="baixa"`. Nota: o mesmo defeito CR-01 (item 1) faz com que casos que DEVERIAM disparar fronteiriço (compounder real com CV alto por tendência) às vezes vençam com confiança ALTA em vez de cair no fallback honesto — o mecanismo de fronteiriço em si funciona para os casos testados, mas o sinal de entrada (CV) que alimenta a decisão de conflito é o mesmo que está quebrado. |

**Score:** 3/4 truths verified (roadmap Success Criteria). 1 truth FAILED (blocker), plus a secondary partial gap on UI exposure folded into the same item.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/arquetipo.py` | `classificar()` + `ResultadoArquetipo` + `ARQUETIPO_MOTOR` + `_cv_lucro` | ✓ VERIFIED (exists, substantive, wired) | 130 lines; all four symbols present and match the contract. Imported and called from `report.py:147` (wired). Functionally INCORRECT for the cyclicality signal (see gap above) — exists/substantive/wired but produces wrong output for realistic inputs. |
| `config.yaml` bloco `arquetipo:` | tokens + thresholds | ✓ VERIFIED | Lines 177-195; `financeiro_tokens`, `regulada_excluir_tokens`, `roe_alto_min: 0.15`, `retencao_alta_min: 0.50`, `ciclica_cv_min: 0.40` all present; no pre-existing block altered (appended at end of file). |
| `tests/test_arquetipo.py` | golden classifier tests | ✓ VERIFIED | 10 tests, all pass. Compounder golden uses only 3%/yr growth (CV≈0.08) — does not exercise the realistic-growth path where CR-01 manifests. |
| `src/analista/report/report.py` | roteamento inserido entre CAPM e DDM + campos em `AnaliseAcao` + suspensão D-04 + render | ✓ VERIFIED (wired) | `arquetipo.classificar(c, cfg)` called once at line 147, between the CAPM block (`min(a.g_alto, a.ke)` at line 140) and the DDM comment (`--- DDM de dois estágios ---` at line 155). 5 new fields on `AnaliseAcao` (lines 52-56). Suspension guard `if a.motor_pendente:` at line 203, before the DDM verdict branch. Render line at 452. |
| `tests/test_arquetipo_roteamento.py` | golden e2e (regulada idêntica, financeira suspensa, anti-Petróleo, fronteiriço via funil) | ✓ VERIFIED | 6 tests present (SUMMARY claims 7 — minor metrics discrepancy, not a functional gap), all pass. |
| `app.py` (Streamlit UI) | exibe arquétipo/motor no fluxo principal | ✗ NOT WIRED | No reference to `a.arquetipo` or `a.motor` anywhere in app.py. Only the CLI (`relatorio_markdown`) exposes it as a dedicated, always-visible line. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `arquetipo.py::classificar` | `CompanyData.roe_valuation/payout_valuation/serie/eh_concessionaria/setor` | consumo de sinais canônicos | ✓ WIRED | Confirmed at arquetipo.py:95,102,106-109 — reads `c.setor`, `c.eh_concessionaria`, `c.roe_valuation()`, `c.payout_valuation()`, `c.serie("lucro_liquido")`; never recomputes. |
| `arquetipo.py::classificar` | `config.yaml arquetipo:` | `cfg.get("arquetipo", {})` | ✓ WIRED | arquetipo.py:88-93 reads all 5 thresholds/token lists from `cfg["arquetipo"]` with defaults. |
| `report.py::analisar_acao` | `arquetipo.classificar + ARQUETIPO_MOTOR` | import + lookup after CAPM | ✓ WIRED | report.py:16 (import), :147-153 (call + lookup). |
| `report.py::analisar_acao` (veredito) | `selo.montar_selo` overlay VERIFICAR | prefixo "VERIFICAR" reusado | ✓ WIRED | report.py:211-215 reuses the exact "VERIFICAR" prefix; `selo.py` untouched (confirmed via `git log` — last touch to selo.py predates this phase). `test_selo` green confirms the firewall contract holds. |
| `app.py` (Streamlit render) | `a.arquetipo` / `a.motor` | direct field display | ✗ NOT WIRED | No occurrence of `a.arquetipo` or `a.motor` in app.py. Indirect exposure only for motor_pendente cases via embedded text in `a.veredito`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `arquetipo.py::classificar` | `cv = _cv_lucro(c.serie("lucro_liquido"))` | Real CVM earnings series (verified offline against cached DFP data for WEGE3, cd_cvm 5410, 2016-2023) | Yes, data flows — but the **signal itself is structurally wrong** for compounders (measures raw-level dispersion, dominated by growth trend, not oscillation) | ⚠️ FLOWING BUT INCORRECT — this is the CR-01 defect; not a wiring/hollow-data problem, a logic defect confirmed with production-shape data. |
| `report.py::analisar_acao` → `a.arquetipo`/`a.motor` | Populated at line 148-153 | `arquetipo.classificar(c, cfg)` | Yes | ✓ FLOWING |
| `app.py` render → arquétipo display | N/A | N/A | No — field never read | ✗ DISCONNECTED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| ITUB4 (real CVM data) classifica financeira | offline script using `cvm.fundamentos_do_ano(19348, ...)` + `arquetipo.classificar` | `chave='financeira'` | ✓ PASS |
| TAEE11 (real CVM data, eh_concessionaria=True) classifica pagadora_regulada, motor ddm | offline script, cd_cvm 20257 | `chave='pagadora_regulada'`, `motor='ddm'` | ✓ PASS |
| VALE3 (real CVM data) classifica cíclica | offline script, cd_cvm 4170 | `chave='ciclica'` (ROE 49%, CV 1.0 — genuinely volatile commodity earnings) | ✓ PASS |
| WEGE3 (real CVM data) classifica crescimento | offline script, cd_cvm 5410 | `chave='ciclica'`, `confianca='alta'` — **expected `crescimento`** | ✗ FAIL |
| Full test suite green | `python -m pytest -q` | `354 passed` | ✓ PASS |
| `test_arquetipo.py` + `test_arquetipo_roteamento.py` | `pytest tests/test_arquetipo.py tests/test_arquetipo_roteamento.py -q` | `16 passed` | ✓ PASS |
| No TODO/FIXME/TBD/XXX markers in phase files | `grep -n -E "TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER"` on arquetipo.py, report.py, config.yaml | No matches | ✓ PASS |
| `selo.py`/`core/ddm.py` untouched by this phase | `git log --oneline -- src/analista/report/selo.py src/analista/core/ddm.py` | Last touches predate phase 1 commits | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|--------------|--------|----------|
| ARQ-01 | 01-01, 01-02 | Classifica o arquétipo antes de valuar (setor CVM + refino quantitativo por ROE/retenção/oscilação) | ⚠️ PARTIAL | Hard-route por setor (financeira/regulada) funciona corretamente e é soberano — verificado com ITUB4/TAEE11 reais. O refino quantitativo (cíclica vs. crescimento), que é metade explícita do requirement ("ROE alto e estável... → compounder; margem/lucro oscilando violento... → cíclica"), está QUEBRADO para compounders reais (WEGE3) — CR-01. O requisito não está integralmente satisfeito. |
| ARQ-02 | 01-01, 01-02 | Fallback honesto: fronteiriço + 2-3 lentes candidatas em conflito real | ✓ SATISFIED | Mecanismo implementado e testado (`fronteirico`, `candidatos`, `confianca`) tanto no classificador puro quanto ponta-a-ponta pelo funil (`test_fronteirico_via_funil_expoe_conflito`). O mesmo bug de CR-01 tangencia este requisito (casos que deveriam ser fronteiriços às vezes vencem com confiança alta), mas o MECANISMO em si — o que ARQ-02 pede — existe e funciona para os cenários testados. |
| ENG-01 | 01-01, 01-02 | Registry arquétipo→motor consumido na agregação do veredito | ✓ SATISFIED | `ARQUETIPO_MOTOR` (arquetipo.py:36-42), consumido em report.py:151. Motor não é mais fixo em DDM — código não referencia DDM diretamente para decidir o motor (só a chave `pagadora_regulada` mapeia para `"ddm"` no registry). |
| ENG-06 | 01-02 | DDM permanece motor primário para pagadora madura/regulada, sem quebrar o que já funciona | ✓ SATISFIED | Confirmado: TAEE11 real classifica pagadora_regulada→ddm; `test_ddm`/`test_selo`/`test_consistencia_modos`/`test_guardrails_fix06`/`test_vulc3_regressao` todos verdes; `selo.py`/`ddm.py` não tocados. |

**Orphaned requirements check:** REQUIREMENTS.md maps exactly ARQ-01, ARQ-02, ENG-01, ENG-06 to "Phase 1" (line 84: `Phase 1 (Classificador + Roteamento): ARQ-01, ARQ-02, ENG-01, ENG-06 (4)`), matching the `requirements:` fields declared across both plans. No orphaned requirements found.

**Note:** REQUIREMENTS.md currently marks ARQ-01/ARQ-02/ENG-01/ENG-06 as `[x]` complete (lines 15-16, 20, 25). Given the ARQ-01 finding above, this checkbox is premature — ARQ-01 is not fully satisfied by the current implementation.

### Anti-Patterns Found

Carried forward from `01-REVIEW.md` (code review, standard depth, 2026-07-11), independently spot-checked against the current codebase:

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/analista/core/arquetipo.py` | 58-69, 113 | CR-01: `_cv_lucro` uses CV of raw earnings level, dominated by growth trend | 🛑 Blocker | Misroutes real compounders (WEGE3 confirmed) to `ciclica` with high confidence — directly fails ROADMAP Success Criterion #1 |
| `src/analista/core/arquetipo.py` | 89-90, 98, 102 | WR-01: `financeiro_tokens`/`regulada_excluir_tokens` default to `[]` when config block absent — "mandatory" guards silently disable | ⚠️ Warning | Not triggered in normal operation (config.yaml always ships the block), but the safety-critical guard has no code-level floor |
| `src/analista/core/arquetipo.py` | 99, 103 vs. dataclass docstring/comment `:47-49,122-123` | WR-02: `candidatos` empty on hard-route returns despite "sempre populado" claim in code comment and SUMMARY.md | ⚠️ Warning | Contract inconsistency; downstream Phase 3 consumers trusting "always populated" will see empty lists for financeira/regulada |
| `src/analista/report/report.py` | 211-215 | WR-03: suspended-verdict message interpolates placeholder `'pendente_fase_2'` instead of the real engine name (RIM/DCF/etc.) | ⚠️ Warning | Cosmetic/UX — message reads "usa o motor 'pendente_fase_2'" instead of naming the actual pending engine |
| `src/analista/report/report.py` | 203-215 | WR-04: suspended-verdict text always references "o DDM abaixo" even when DDM produced no band | ⚠️ Warning | Minor UX inconsistency when a pendente archetype also lacks valuation inputs |
| `app.py` | — | No reference to `a.arquetipo`/`a.motor` anywhere in the main render flow | ⚠️ Warning (folded into gap above) | Primary Streamlit UI never explicitly surfaces the classification |

No TBD/FIXME/XXX debt markers found in phase-modified files (Debt marker gate: clean).

### Human Verification Required

None. All must-haves were verifiable programmatically against real cached CVM data and the existing test suite; no visual/UX/real-time behavior needed manual confirmation for this phase's scope.

### Gaps Summary

The phase successfully erects the classifier scaffolding, the arquétipo→motor registry, the D-04
verdict-suspension mechanism, and preserves the regulated-payer (TAEE11/DDM) path byte-for-byte —
these parts are solid and test-locked. However, the core "refino quantitativo" half of ARQ-01 —
the part that is supposed to distinguish a cyclical business from a compounder — is measurably
broken for real companies. Using the project's own cached CVM data (no network required), WEGE3 —
named explicitly in the ROADMAP's Success Criterion #1 as the expected "crescimento" example —
classifies as "ciclica" with high confidence. This is not a hypothetical edge case: it is the
textbook shape of any strong, consistently profitable grower, which is exactly the archetype the
classifier's own docstring claims to detect. The existing golden test suite is green only because
its one compounder fixture uses an unrealistically slow 3%/year growth rate that happens to stay
under the CV threshold.

A secondary, lower-severity gap: the Streamlit UI (`app.py`), which is the project's primary
documented interface, never displays the arquétipo/motor classification explicitly — only the CLI
(`relatorio_markdown`) does so consistently. For archetypes whose verdict is suspended
(motor_pendente), the arquétipo name leaks into the UI incidentally via the verdict text, but for
the regulated payer (TAEE11-like, non-suspended) nothing in the UI names the archetype at all.

Both gaps are structured above for `/gsd-plan-phase --gaps`. The CR-01 fix should include a golden
test with a realistic (>=15%/yr) compounder to prevent silent regression, since the current test
suite's blind spot is what let this ship green.

---

_Verified: 2026-07-11T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
