---
phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo
verified: 2026-07-12T13:53:43Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: "4/6 must-haves verified (2 partial/failed on independently-confirmed defects)"
  gaps_closed:
    - "O selo/veredito nunca apresenta silenciosamente a banda do DDM sob o rótulo do motor do arquétipo, sem aviso (CR-01)"
    - "Em caso-fronteira, TODA a superfície (CLI e UI) assume a dúvida em voz alta — nenhum número específico é exibido como se fosse certo (WR-01)"
  gaps_remaining: []
  regressions: []
deferred: []
human_verification: []
---

# Phase 3: Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo — Verification Report

**Phase Goal:** Fechar o loop na agregação do veredito (hoje single-model BSD×DDM). O selo deve
consumir o motor DO ARQUÉTIPO classificado (não o DDM fixo), preservando o firewall
selo↛report. Rodar motor primário + ≥1 contraponto e, quando divergência > limiar (maior > 2×
menor), levantar bandeira de divergência com hipótese. Interpor guarda-corpos anti-aberração
antes de estampar "evitar" (SAN-01). Em caso-fronteira, assumir a dúvida em voz alta (range +
bandeira) em vez de fingir certeza.

**Verified:** 2026-07-12T13:53:43Z
**Status:** passed
**Re-verification:** Yes — after code-review fix commits 5ea45ce (CR-01), eb2906a (WR-01), 69dd243 (WR-03)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC#1 — ITUB4 não é mais estampado "evitar": selo consome motor RIM, DDM rebaixado a lente conservadora | ✓ VERIFIED | Executado ao vivo (não só via teste): fixture `_itub4_financeira()` → `a.arquetipo='financeira'`, `a.motor='rim'`, `a.banda_do_motor=True`, alerta "lente conservadora" presente, `"Evitar" not in a.veredito`, `selo_mod.montar_selo(...).rotulo != "Evitar"`. Golden `test_capstone_itub4_sem_evitar_motor_rim_ddm_como_lente` verde. |
| 2 | SC#2 — Motor×contraponto divergem >2× → range + bandeira de divergência com hipótese, não número único | ✓ VERIFIED | `_HIPOTESE_DIVERGENCIA` dict presente (report.py:742), `divergencia_entre_lentes` (comparables) chamado no funil (report.py:504), populando `divergencia_ativa`/`divergencia_razao`/`divergencia_hipotese`; renderizado via `st.warning` em app.py (linhas 940-953) e no markdown CLI. Comportamento inalterado desde a verificação anterior (não tocado pelas correções). |
| 3 | SC#3 — Todo veredito "evitar" passa por guarda-corpos; aberração (ROE>15% E corte payout>40%, pares degradável) é reetiquetada "DDM conservador demais..." mantendo o número | ✓ VERIFIED | Reexecutado ao vivo: `_company_san01()` + `analisar_acao` → `a.san01_reetiquetado=True`, `a.veredito="DDM conservador demais para este perfil — ver motor primário do arquétipo (intrínseco ≈ R$ 6,27)"`, `"Evitar" not in a.veredito`, `selo.rotulo=None` (faixa suprimida). `_guarda_san01` (report.py:107) chamado antes de `montar_selo` (report.py:587). WR-02 (checagem direcional) permanece deliberadamente não implementado — ver Anti-Patterns; não afeta o literal da SC#3. |
| 4 | SC#4 — Em caso-fronteira, veredito assume a dúvida (range+bandeira) em vez de selo cravado | ✓ VERIFIED (gap fechado) | Reexecutado ao vivo com fixture `_fronteirico()`: `a.arquetipo_incerto=True`, `a.candidatos_intrinsecos=[('ciclica', 9.075), ('crescimento', 22.677)]`, `a.veredito_range=(9.075, 22.677)`, `a.veredito` começa com "VERIFICAR — caso-fronteira: classificação incerta...". `a.vmin/a.vmax` continuam sendo a banda antiga do ensemble primário (4,41–9,08) — mas isso não é mais exibido: `app.py` linha 976-978 agora suprime o metric card (`intervalo = "—"`) quando `getattr(a, "arquetipo_incerto", False)`, confirmado por leitura direta do código pós-fix (commit eb2906a). O único número exibido na UI é o range de candidatos do banner. |
| 5 | SC#5 — Firewall selo↛report preservado; test_selo/test_vulc3_regressao/test_guardrails_fix06/test_consistencia_modos verdes | ✓ VERIFIED | `grep -n "^import\|^from" src/analista/report/selo.py` → só `dataclasses`/`typing`. Suíte completa: **435 passed** (`python3 -m pytest tests/ -q`). Alvo dos 4 módulos nomeados executado isoladamente: **35 passed** (`-k "test_selo or test_vulc3_regressao or test_guardrails_fix06 or test_consistencia_modos or ..."`). |
| 6 (derivada do Core Value / objetivo da fase) | O selo NUNCA apresenta a banda do DDM sob o rótulo de outro motor sem aviso | ✓ VERIFIED (gap fechado — CR-01) | Reexecutado ao vivo (`monkeypatch.setattr(rep.motores, "rim", lambda **k: None)`): `a.motor='rim'`, `a.intrinseco_motor=None`, `a.vmin/a.vmax` sobrevivem do DDM, `a.banda_do_motor=False` (confirmado pela leitura de `report.py:511-521`, novo ramo `elif a.motor != "ddm" and a.vmin is not None and a.vmax is not None:`), alerta honesto "Motor 'rim' (RIM) degradou; a faixa exibida vem do DDM (contraponto), não do motor do arquétipo." presente em `a.alertas`. `app.py:982-988` agora rotula `"Intrínseco (DDM)"` (não mais `"Intrínseco (RIM)"`) porque a condição do rótulo passou a checar `not getattr(a, "banda_do_motor", False)`, não só `a.motor`. Markdown `relatorio_markdown` não chama o DDM de "lente conservadora" nesse caminho (`ddm_e_lente = a.motor != "ddm" and a.banda_do_motor` → False) e omite a seção "Valuation pelo motor do arquétipo". Golden `test_cr01_motor_degrada_mas_ddm_sobrevive_rotula_ddm` verde. |

**Score:** 6/6 truths fully verified (both previously-blocking gaps — CR-01 critical, WR-01 warning — independently confirmed closed by live execution + code reading, not just by the SUMMARY/REVIEW-FIX narrative).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/report/report.py` | Banda do ensemble + divergência + `_HIPOTESE_DIVERGENCIA` | ✓ VERIFIED | Unchanged from prior verification, still present and wired. |
| `src/analista/report/report.py` | `_guarda_san01` (SAN-01) | ✓ VERIFIED | Present (line 107), called before `montar_selo` (line 587). |
| `src/analista/report/report.py` | `_intrinseco_por_motor` + ramo fronteiriço (VER-02) | ✓ VERIFIED | Present (line 183), reused by primary dispatch and `arquetipo_fronteirico` branch. |
| `src/analista/report/report.py` | CR-01 fix: `elif` branch for motor-None + DDM-valid | ✓ VERIFIED | Lines 511-521: sets honest alert, leaves `banda_do_motor=False`. Covered by `test_cr01_motor_degrada_mas_ddm_sobrevive_rotula_ddm`. |
| `src/analista/report/report.py` | WR-03 fix: markdown shows motor×DDM band, not just a point | ✓ VERIFIED | Lines 897-903: prints `Faixa do veredito (motor × DDM contraponto)` when `banda_do_motor` is set. |
| `app.py` | CR-01 fix: metric label falls back to "Intrínseco (DDM)" when `banda_do_motor` is False | ✓ VERIFIED | Lines 984-988: `_label_intr` now checks `_motor == "ddm" or not getattr(a, "banda_do_motor", False)`. |
| `app.py` | WR-01 fix: metric card suppressed on `arquetipo_incerto` | ✓ VERIFIED | Lines 975-978: `if getattr(a, "arquetipo_incerto", False): intervalo = "—"`. Confirmed live: fronteiriço fixture produces `arquetipo_incerto=True`, metric card no longer shows the stale primary-archetype band. |
| `config.yaml` | Bloco `veredito.margem_seguranca` + `veredito.san01.*` | ✓ VERIFIED | Unchanged, present. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `report.analisar_acao` motor-degraded branch | `a.banda_do_motor` / `a.alertas` | new `elif` at report.py:511 | ✓ WIRED | Confirmed live: alert text present, `banda_do_motor` stays False. |
| `a.banda_do_motor` | `app.py` metric label (`_label_intr`) | `not getattr(a, "banda_do_motor", False)` check | ✓ WIRED | Confirmed by code read: label falls back to "Intrínseco (DDM)" whenever the band isn't motor-sourced, regardless of `a.motor` value. |
| `a.banda_do_motor` | `relatorio_markdown` "lente conservadora" caption | `ddm_e_lente = a.motor != "ddm" and a.banda_do_motor` | ✓ WIRED | Confirmed: golden test asserts `"lente conservadora" not in md` and `"Valuation pelo motor do arquétipo" not in md` on the degraded-motor path. |
| `a.arquetipo_incerto` | `app.py` metric card suppression | `if getattr(a, "arquetipo_incerto", False): intervalo = "—"` | ✓ WIRED | Confirmed live: fronteiriço fixture sets `arquetipo_incerto=True`; code path unconditionally overwrites `intervalo` before rendering, eliminating the two-conflicting-numbers defect. |
| `report._guarda_san01` | `a.veredito` reetiquetado | pre-selo funil call | ✓ WIRED | Unchanged, confirmed live again this run. |
| `selo.py` | `report.py` | (must NOT import) | ✓ FIREWALL INTACT | `selo.py` imports only `dataclasses`/`typing`. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VER-01 | 03-01, 03-04 | Selo consome motor do arquétipo, não DDM fixo | ✓ SATISFIED | Confirmed live for both the healthy-motor path and the motor-degraded path (CR-01 fix closes the previously-silent fallback). |
| ENS-01 | 03-01, 03-04 | Motor primário + contraponto DDM; divergência >2× levanta bandeira com hipótese | ✓ SATISFIED | Unchanged, confirmed present and wired. |
| SAN-01 | 03-02, 03-04 | Guarda-corpo anti-aberração antes de "evitar" | ✓ SATISFIED (literal criteria met; WR-02 directional refinement deliberately deferred as a documented design tradeoff, not part of the ROADMAP SC wording) | Reetiqueta confirmed live; `_guarda_san01` gate matches the literal SC#3 wording exactly (intrínseco < 0,5× pares E ROE>15% E corte payout>40%). Note: `.planning/REQUIREMENTS.md:33` still shows SAN-01 as `[~]` (partial) with stale text referring to "fica na Fase 3" — this is a documentation-bookkeeping lag, not a code gap (the Phase 3 portion described there is implemented and tested). |
| VER-02 | 03-03, 03-04 | Caso-fronteira assume a dúvida (range+bandeira) | ✓ SATISFIED | Confirmed live in both CLI/engine (unchanged) and UI (WR-01 fix closes the previously-contradicting metric card). |

Nenhum requisito órfão: `.planning/REQUIREMENTS.md` mapeia só ENS-01/SAN-01/VER-01/VER-02 para a Fase 3.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/analista/report/report.py` | 107-180 (`_guarda_san01`) | Gate SAN-01 sem checagem direcional entre motor e DDM (WR-02) | ℹ️ Info (downgraded from Warning) | Documented, deliberate design tradeoff (03-REVIEW-FIX.md): a directional guard would break the intentional golden `test_san01_e2e_itub4_nao_estampa_evitar`. Left as an explicit product-design decision, not a mechanical defect. Does not violate the literal SC#3 wording. Recommend tracking as technical debt if product later wants the directional check. |
| `src/analista/report/report.py` | 274-278 | "entre X e Y" nomeia primeiro/último candidato por ordem de inserção, não necessariamente os extremos do range (IN-01) | ℹ️ Info | Unchanged, out of fix scope. Prosa pode nomear um par mais estreito que o range implica com ≥3 candidatos. |
| `app.py` | 696, 713 | Redundant local `import json` shadows module-level import (IN-02) | ℹ️ Info | Unchanged, out of fix scope. Harmless/cosmetic. |
| `.planning/REQUIREMENTS.md` | 33 | SAN-01 checkbox still `[~]` (partial) with stale "fica na Fase 3" text after Phase 3 SAN-01 work is committed and tested | ℹ️ Info | Documentation bookkeeping lag, not a code defect — does not affect goal achievement, but should be updated to `[x]` in a housekeeping pass. |

Nenhum marcador de dívida (TBD/FIXME/XXX) sem referência de follow-up encontrado nos arquivos tocados pelos fixes (`git diff 4ce52d8..HEAD -- report.py app.py tests/test_report.py` não retorna nenhum TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER).

### Human Verification Required

Nenhum item bloqueante. Nota não-bloqueante: `03-REVIEW-FIX.md` marca o fix CR-01 como
"requires human verification (touches verdict/label logic on a previously untested degradation
path)" — mas isso se refere apenas à confirmação de que a *redação* do alerta ("Motor '<motor>'
degradou; a faixa exibida vem do DDM...") corresponde à intenção de produto, não a uma dúvida
funcional. A lógica foi confirmada programaticamente (execução ao vivo + leitura de código +
golden test cobrindo exatamente esse caminho), então isso não bloqueia o status `passed`; é uma
sugestão de revisão de copy, não um gap.

## Gaps Summary

Ambos os gaps que bloquearam a verificação anterior (`03-VERIFICATION.md` datado de
2026-07-12T13:01:22Z, status `gaps_found`, score 4/6) foram fechados e reconfirmados de forma
independente nesta rodada:

1. **CR-01 (era BLOCKER):** o novo ramo `elif a.motor != "ddm" and a.vmin is not None and
   a.vmax is not None:` em `report.py:511` cobre exatamente o caminho antes silencioso (motor
   degrada para `None`, banda DDM sobrevive). `banda_do_motor` permanece `False`, um alerta
   honesto é emitido, o rótulo do app cai para "Intrínseco (DDM)", e o markdown não chama o DDM
   de "lente conservadora" nesse caminho. Reproduzido ao vivo com `monkeypatch` no motor RIM;
   comportamento bate 100% com o que o fix declarou. Golden test cobre o caminho especificamente.

2. **WR-01 (era gap parcial em SC#4):** `app.py` agora suprime o metric card do intrínseco
   (`intervalo = "—"`) sempre que `a.arquetipo_incerto` é `True`, eliminando o conflito entre o
   metric card cravado e o banner de "classificação incerta". Reproduzido ao vivo com a fixture
   `_fronteirico()`: `arquetipo_incerto=True` confirmado, e a lógica de supressão está no lugar
   certo do código de render.

WR-02 (checagem direcional do SAN-01) permanece deliberadamente não implementado — é uma decisão
de design documentada (não um defeito mecânico), e não contradiz a redação literal da SC#3 do
ROADMAP. WR-03/IN-01/IN-02 foram tratados ou permanecem como débito técnico info-level, sem
impacto no objetivo da fase.

Suíte completa: 435/435 testes passam. Os 4 módulos golden nomeados no objetivo da fase
(test_selo, test_vulc3_regressao, test_guardrails_fix06, test_consistencia_modos) passam
isoladamente. O firewall selo↛report permanece intacto (`selo.py` só importa
`dataclasses`/`typing`). As 5 Success Criteria do ROADMAP estão VERIFICADAS por execução ao vivo,
não apenas por teste golden ou pela alegação do SUMMARY/REVIEW-FIX.

---

_Verified: 2026-07-12T13:53:43Z_
_Verifier: Claude (gsd-verifier)_
