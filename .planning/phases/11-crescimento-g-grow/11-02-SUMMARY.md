---
phase: 11-crescimento-g-grow
plan: 02
subsystem: valuation-engine
tags: [g_cap, perpetuidade, rim, ddm, knob-migration, doenca-1-g, blindagem]

# Dependency graph
requires:
  - phase: 11-crescimento-g-grow
    provides: "insumo carimbado cfg['macro']['pi_ciclo'] (Plano 01)"
provides:
  - "g_cap = (1+pi_ciclo)(1+PIB_real)-1 ~= 0.0728 DERIVADO na engine (report.py, 2 sitios) — FONTE UNICA do crescimento terminal (D-04)"
  - "RIM g terminal fechado por empresa: g_T = min(roe_terminal*retencao, g_cap) (GROW-03)"
  - "fase explicita adota g_fundamentos (g_historico vira sanidade/fallback) (GROW-04/D-01)"
  - "PIB_real migrado ddm.g_estavel -> ddm.pib_real (config+lock, particao de 29 folhas, D-05)"
affects: [12-ke (ke_teto sai; BLIND-02 vira verde), 13-eng (motores colapsam), 14-val (soberano ITUB4 R$37,22)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "g da perpetuidade DERIVADO (nunca digitado) — leitura defensiva cfg['ddm'].get('pib_real', 0.02) com fallback == default do config"
    - "co-change knob (config.yaml + lock + teste) atravessa o hook BLIND-05 com trailer Knob-Change-Justification sem ticker"
    - "split-before-delete (WR-04) aplicado a um INVARIANTE: decouplar do nivel v2.3 em vez de deletar"

key-files:
  created: []
  modified:
    - src/analista/report/report.py
    - config.yaml
    - calibracao.lock.yaml
    - tests/helpers_blindagem.py
    - tests/test_report.py
    - tests/test_backtest_bancos.py
    - tests/classificacao.yaml

key-decisions:
  - "g_cap e' FONTE UNICA: substituiu ddm.g_estavel E motores.rim.g_terminal em TODOS os 6 call sites (Gordon seguradora/ciclica, dcf, DDM lens x3, guarda de convergencia) + os 2 sitios de leitura (D-04)"
  - "PIB_real = 0.02 (era 0.025 embutido no g_estavel): o home migrou para ddm.pib_real, o grau de liberdade continua UM (D-05); orcamento em 3 graus intacto"
  - "FIX-01 (g_alto <= Ke) byte-identico: g_cap trava SO o terminal, nunca a fase explicita (D-02)"
  - "EXTENSAO DE ESCOPO APROVADA pelo usuario: 3 arquivos de teste alem dos 4 do plano — o g_cap moveu insumos calibrados ao g=2,5% (fixture de divergencia + invariante de nota do backtest)"

patterns-established:
  - "fixture de teste calibrada a um knob antigo re-tunada COM o metodo (nao afrouxada): _financeira_rim ROE 26%/payout 17% mantem RIM ~3x DDM sob g_cap"
  - "invariante coupled a um nivel v2.3 (passa/banda +-15%) e' decouplado para o dual estrutural (nota<=>rota-nao-RIM), preservando D-08 sem referenciar a banda"

requirements-completed: [GROW-01, GROW-03, GROW-04]

# Metrics
duration: WIP-recovery + scope-extension (session 2026-07-17)
completed: 2026-07-17
---

# Phase 11 Plan 02: g_cap derivado como fonte unica do crescimento terminal Summary

**A mudanca atomica de valuation do marco: `g_cap = (1+pi_ciclo)(1+PIB_real)-1 ~= 7,28%` derivado na engine substitui as duas constantes gemeas de 2,5% e vira a FONTE UNICA do crescimento terminal; a fase explicita adota `g_fundamentos`; o RIM fecha `g_T` por empresa — tudo num diff atomico que mantem o orcamento em 3 graus.**

## Procedencia (recuperacao de WIP)

Este plano foi encontrado **ja implementado na working tree** por uma sessao anterior — codigo completo e fiel ao plano, mas **sem commit e sem SUMMARY**. A execucao desta sessao foi de **recuperacao (close-out)**: verificar a WIP contra os asserts do plano, resolver as quebras nao antecipadas, e fechar. Nada foi re-implementado do zero.

## Accomplishments
- **`g_cap` derivado (report.py:217 e :416):** `(1.0 + cfg.get("macro",{}).get("pi_ciclo",0.0518)) * (1.0 + cfg["ddm"].get("pib_real",0.02)) - 1.0`; nenhum `0.0728` literal. Fonte unica nos 6 call sites (D-04).
- **RIM `g_T` por empresa (GROW-03):** `min(_roe_through_cycle(c,rim_cfg) * (1 - payout_valuation), g_cap)`, degrada para `g_cap` quando o ROE through-cycle e' None. Assinatura de `motores.rim` inalterada.
- **Adocao de `g_fundamentos` (GROW-04/D-01):** `g_alto = g_fundamentos if not None else g_historico`, capado [0, 0.25]; `g_historico` vira sanidade/fallback. Comentario DDM-FIX-02 reescrito para a nova doutrina.
- **Migracao de knob (D-05, MESMO diff):** `config.yaml` sem `ddm.g_estavel`/`motores.rim.g_terminal`, com `ddm.pib_real: 0.02`; `calibracao.lock.yaml` grau `PIB_real` -> `caminho: ddm.pib_real`, `motores.rim.g_terminal` fora de `congelados`, particao recontada (29 folhas). `choque_nominal` migra para `macro.pi_ciclo`.

## Task Commits
1. **Task 1 (atomica): g_cap derivado + adocao g_fundamentos + g_T por empresa + migracao de knob + extensao de teste aprovada** — `a461147` (feat, com trailer `Knob-Change-Justification:` sem ticker)

## Deviations from Plan

**Extensao de escopo (aprovada pelo usuario nesta sessao).** O plano assumia `pytest -q -> 0 failed`, esperando que so' `golden_nivel` (ja em quarentena) quebrasse. O `g_cap` (perpetuidade 2,5% -> 7,28%) quebrou **4 testes NAO-quarentenados** (3 `contrato` + 1 `invariante`), fora dos 4 arquivos do plano. Diagnostico e resolucao, ambos aprovados:

1. **3 `contrato` de divergencia (`test_report.py`)** — a fixture sintetica `_financeira_rim` estava calibrada ao g=2,5% (razao RIM/DDM caiu para 1,86x < limiar 2x). **Re-tunada COM o metodo** (ROE 26%/payout 17%) para manter RIM ~3,26x DDM sob o g_cap — contrato preservado, nao afrouxado.
2. **1 `invariante` (`test_backtest_bancos::test_nenhuma_reprovacao_de_banda_e_silenciosa`)** — BBAS3 RIM subiu para 44,87, **R$0,02 (0,04%) acima** do teto da banda de consenso **v2.3** (`fair_values +-15%`), sem `excecao_nota`. A invariante disparava a nota sobre `not passa` — um NIVEL v2.3 que o motor v2.4 move de proposito. **Decouplada (split-before-delete WR-04 aplicado a um invariante):** renomeada para `test_nenhuma_nota_de_excecao_e_orfa`, agora o **dual estrutural** de `test_nenhuma_rota_diferente_de_rim_e_silenciosa` (nota<=>rota-nao-RIM, D-08), SEM referenciar a banda +-15%. `classificacao.yaml` atualizado (segue `invariante`).

## Issues Encountered / Observacoes para as proximas fases
- **BBSE3 seguradora explodiu sob g_cap:** a rota Gordon de estagio unico da seguradora agora consome `g_cap` (7,28%), encolhendo o denominador `ke-g` -> `intrinseco_motor` de BBSE3 saltou ~39,87 -> ~86. Comportamento **exigido pelo plano** (a rota seguradora usa g_cap, D-04), e a invariante nao dispara (BBSE3 tem `excecao_nota`). **Sinalizado para a Fase 12 (Ke)/13 (colapso dos motores):** um Gordon de estagio unico com spread `ke-g` apertado e' fragil; a Fase 13 revisita a rota seguradora.
- **ITUB4 moveu na direcao certa:** RIM 32,88 -> 36,65 (o antigo golden de nivel, DELETADO na Fase 10, ficaria vermelho — como previsto). Aproxima do soberano R$37,22 da Fase 14, mas o veredito soberano so' fecha depois do `Ke` (Fase 12).

## Verification
- `pytest -q` -> **490 passed, 1 skipped, 27 deselected, 1 xfailed, 0 failed** (suite verde per CLAUDE.md).
- `pytest -k invariancia_inflacao_engine_itub4` -> **1 xfailed** (BLIND-02, NAO xpassed) — a Doenca 1 so' cai na Fase 12; `xfail_strict` deixaria o default vermelho num XPASS.
- `pytest -k "orcamento_de_knobs or knobs_batem_com_o_lock"` -> 2 passed (3 graus de liberdade; particao de 29 folhas).
- `pytest -k "justificativa or hook"` -> passed (nenhuma justificativa de knob menciona ticker; hook BLIND-05 instalado).
- Assercoes do plano: `g_cap=0.0728`; ITUB4 `g_alto == min(g_fundamentos, ke)` (g_fundamentos=0.0959); config sem g_estavel/g_terminal, com pib_real; lock com `PIB_real.caminho=ddm.pib_real` e sem `motores.rim.g_terminal`.
- Commit `a461147` traz o trailer `Knob-Change-Justification:` sem ticker (hook passou).

## Next Phase Readiness
- Metade `g` da Doenca 1 curada: o `g` da perpetuidade deixou de ser 2,5% real descontado por um Ke nominal.
- **BLIND-02 permanece xfail de proposito** — a outra metade (`Ke` nominal + `ke_teto` muleta) e' a Fase 12, que e' quando o invariante de inflacao vira verde. **NAO fundir 11 com 12** (regra dura A).
- Fronteira respeitada: **nenhum toque em Ke/ke_teto/ERP/beta/excesso_sustentavel/ke_g_spread_min** (Plano 03 os cobre por teste).

## Self-Check: PASSED
- Files: `11-02-SUMMARY.md`, `report.py`, `config.yaml`, `calibracao.lock.yaml`, `helpers_blindagem.py`, `test_report.py`, `test_backtest_bancos.py`, `classificacao.yaml` — all FOUND.
- Commit: `a461147` — FOUND in git log; trailer present; hook passed.
- Suite: 0 failed, BLIND-02 xfailed (not xpassed).

---
*Phase: 11-crescimento-g-grow*
*Completed: 2026-07-17*
