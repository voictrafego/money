---
phase: 04-rim-com-valor-terminal-ke-revisado
verified: 2026-07-13T18:00:00Z
status: passed
score: 7/7 must-haves verified (loop D-12) + 4/4 Success Criteria originais (ROADMAP)
overrides_applied: 0
re_verification:
  previous_status: passed (iteração 1 — verificação superada pelo loop D-12)
  previous_score: 5/5 (04-01 apenas)
  gaps_closed:
    - "Cesta de bancos generaliza (Fase 5 provou 1/4; agora 4/4 via Alavanca 2 + Alavanca 3)"
    - "xfail(strict) do gate de quórum removido (test_backtest_bancos.py)"
  gaps_remaining: []
  regressions: []
---

# Phase 4: RIM com Valor Terminal + Ke Revisado Verification Report

**Phase Goal:** Consertar a alavanca principal — dar ao motor RIM um valor terminal (perpetuidade de residual income) que substitui o fade-sem-terminal, para que o intrínseco de um banco que sustenta ROE > Ke deixe de ancorar no VPA. Revisar o Ke do RIM de banco como ajuste fino. Motor puro/never-raise, sem tocar ddm.py/selo.py/lentes.py. **+ Loop D-12 (iteração 2): a calibração deve generalizar na cesta de bancos (ITUB4/BBAS3/BBDC4/BBSE3), cruzando o quórum 4/4 na banda ±15%.**

**Verified:** 2026-07-13
**Status:** passed
**Re-verification:** Yes — a verificação anterior (2026-07-12, `status: passed`, score 5/5) cobria só a iteração 1 (04-01). O loop D-12 reabriu a fase porque a Fase 5 (BACKTEST-01) provou que a calibração não generalizava (1/4 na cesta). Esta verificação **substitui integralmente** o relatório anterior, cobrindo 04-01 + 04-02 + 04-03.

## Goal Achievement

### Observable Truths — Loop D-12 (critério de fechamento exigido nesta verificação)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ITUB4 (RIM) intrínseco na faixa ~R$32–40 e NÃO regride (≈R$32,88 bit-idêntico ao legado — o cap satura) | ✓ VERIFIED | Reproduzido ao vivo via `rodar_cesta` sobre o snapshot congelado: **ITUB4 = R$32,8804**, motor="rim", `passa=True`. Prova de saturação do cap: chamei `motores.rim(...)` com `roe_terminal=None` (legado) vs `roe_terminal=0.20` (acima do cap) — **valor idêntico bit-a-bit** (`32.87214820406446 == 32.87214820406446`). O ROE through-cycle real do ITUB4 no snapshot é `0.17984` vs `ke=0.13` → excesso 4,98pp ≥ cap `excesso_sustentavel=0.045` → satura, confirmando a tese "não regride por construção". |
| 2 | O valor terminal do RIM é parametrizado em config.yaml, sem constantes mágicas; through-cycle knob `roe_terminal_stat` documentado | ✓ VERIFIED | `config.yaml:229-256`: bloco `motores.rim` com `erp_banco`, `ke_piso`, `ke_teto=0.13`, `n_fade`, `excesso_sustentavel=0.045`, `g_terminal=0.025`, `ke_g_spread_min=0.03`, `roe_terminal_stat="mediana"` — cada um com comentário WHY. `motores.py::rim()` lê tudo via parâmetros (nenhum literal mágico no corpo); `report.py::_intrinseco_por_motor` lê os knobs de `cfg["motores"]["rim"]` e computa `_roe_through_cycle(c, rim_cfg)` (mediana\|média dos `c.roe(ano)`, lida do knob `roe_terminal_stat`) antes de injetar via `roe_terminal=`. |
| 3 | Ke do RIM revisado/clamps sãos; sem intrínseco explosivo | ✓ VERIFIED | `config.yaml:235` `ke_teto: 0.13` com rationale (Selic-ciclo já embute risco-país; Blume-beta). `ke_rim()` clampa a `[ke_piso, ke_teto]` e depois trava contra `ke_live` (nunca excede o CAPM ao vivo). RI terminal só é liberado se `ke - g_terminal >= ke_g_spread_min` (protege perpetuidade explosiva); reusa `ddm.valor_gordon` já testado (retorna `None` se `ke-g<=0`). Nenhum dos 4 tickers da cesta produziu valor fora de faixas plausíveis. |
| 4 | Não quebrou nada: goldens test_ddm/test_vulc3/test_selo verdes, TAEE11 idêntica, firewall selo↛report intacto, suíte COMPLETA verde | ✓ VERIFIED | `pytest tests/test_ddm.py tests/test_vulc3_regressao.py tests/test_selo.py tests/test_motores.py -q` → **45 passed, 0 failed**. `pytest -k "firewall or taee11" -q` → **7 passed** (inclui `test_firewall_selo_nao_importa_report` e o capstone TAEE11 idêntico). Suíte completa: `pytest -q` → **447 passed, 0 failed** (era 440 no início da it.2 → +7 testes novos, todos verdes). |
| 5 | A cesta de bancos cruza o quórum: 4/4 na banda ±15% (ITUB4 ≈32,88, BBAS3 ≈43,89, BBDC4 ≈13,37 rim; BBSE3 ≈39,87 rota seguradora) | ✓ VERIFIED | Rodei `rodar_cesta` diretamente (não só o pytest) sobre `snapshot_bancos_2026-07-12.yaml` + `fair_values_bancos.yaml`: **ITUB4=32.8804 (rim, passa=True) · BBAS3=43.8940 (rim, passa=True) · BBDC4=13.3659 (rim, passa=True) · BBSE3=39.8684 (seguradora, passa=True)**. 4/4. Números batem exatamente com os alvos documentados nos SUMMARYs 04-02/04-03. `test_backtest_alvos_recalibrados` crava ITUB4/BBAS3/BBDC4 com bounds absolutos ±R$0,20 — passa. |
| 6 | O gate xfail(strict) foi REMOVIDO de test_backtest_bancos.py e o gate de quórum fica verde (grep de pytest.mark.xfail retorna 0) | ✓ VERIFIED | `grep -c "pytest.mark.xfail" tests/test_backtest_bancos.py` → **0**. `pytest tests/test_backtest_bancos.py -q` → **4 passed** (`test_backtest_cesta_rota_por_ticker`, `test_backtest_gate_quorum_e_anotacao`, `test_backtest_alvos_recalibrados`, `test_backtest_determinismo`), sem xfail/xpass. |
| 7 | ddm.py / fundamentals.py / arquetipo.py / selo.py / lentes.py INTOCADOS na iteração 2 (git diff beafcc4..HEAD não os inclui) | ✓ VERIFIED | `git diff beafcc4..HEAD --stat -- src/analista/core/ddm.py src/analista/core/fundamentals.py src/analista/core/arquetipo.py src/analista/report/selo.py src/analista/core/lentes.py` → **saída vazia** (zero diff). O diff completo da it.2 toca apenas: `motores.py`, `report.py`, `config.yaml`, `tests/test_motores.py`, `tests/test_backtest_bancos.py`, `tests/fixtures/fair_values_bancos.yaml` (+ artefatos de planejamento). |

**Score (loop D-12):** 7/7 truths verified

### Observable Truths — Success Criteria originais (ROADMAP.md, Phase 4)

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|-------|--------|----------|
| SC1 | ITUB4 (roteado para RIM) produz intrínseco na faixa ~R$32–40 | ✓ VERIFIED | Ver Truth #1 acima — R$32,88, dentro da faixa e do gate duro `_ITUB4_RIM_MIN/MAX = 30.0/40.0` em `test_backtest_bancos.py` e `[32,40]` em `test_rim_itub4_live_alvo_32_40`. |
| SC2 | Valor terminal parametrizado em config.yaml, sem constantes mágicas, com justificativa teórica | ✓ VERIFIED | Ver Truth #2 acima. |
| SC3 | Ke do RIM de banco revisado (teto/erp_banco) e documentado; sem intrínseco explosivo | ✓ VERIFIED | Ver Truth #3 acima. |
| SC4 | Não quebrou nada: test_ddm verde, TAEE11 idêntica, firewall selo↛report intacto, suíte completa verde | ✓ VERIFIED | Ver Truth #4 acima. |

**Score (ROADMAP SC originais):** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/motores.py::rim` | Parâmetro opcional `roe_terminal` (backward-safe), como último argumento | ✓ VERIFIED | `def rim(..., fade_para=None, roe_terminal=None)` — confirmado por leitura direta (linha ~64-73). Bloco terminal computa `excesso_t = min(roe_terminal - ke, excesso_sustentavel)` sobre `b_base_ri_final` (a mesma base do RI legado) quando `roe_terminal is not None`; senão usa `ris[-1]` (legado). Janela explícita (`roe0`/`fade_para`) intocada. |
| `config.yaml::motores.rim.roe_terminal_stat` | Knob novo, documentado, sem alterar knobs existentes | ✓ VERIFIED | `config.yaml:250` `roe_terminal_stat: "mediana"` com WHY completo; `excesso_sustentavel`/`g_terminal`/`ke_teto` inalterados desde 04-01. |
| `src/analista/report/report.py::_roe_through_cycle` | Computa ROE through-cycle (mediana\|média), never-raise <3 pontos → None | ✓ VERIFIED | Linhas 184-198: `statistics.median`/`statistics.mean` sobre `[c.roe(a) for a in c.anos_ordenados()]` filtrado; `len(validos) < 3 → None`. Injetado via `roe_terminal=_roe_through_cycle(c, rim_cfg)` na chamada de `motores.rim` (linha 250), só no ramo `motor=="rim"`. |
| `src/analista/report/report.py` (ramo seguradora) | Rota Gordon-franquia ANTES do bank-RIM, roteada por `_setor_casa_token` | ✓ VERIFIED | Linhas 220-238: detecta `arquetipo._setor_casa_token((c.setor or "").lower(), ["seguradora"])`, chama `ddm.valor_gordon(c.dpa_recorrente()*(1+g_estavel), a.ke, g_estavel)`, seta `a.motor = "seguradora"`. Never-raise: dado degenerado cai para o RIM legado (fall-through). |
| `tests/test_motores.py` | Testes: `test_rim_terminal_normalizado`, rota seguradora (`test_rota_seguradora_*`) | ✓ VERIFIED | 16 testes coletados, todos verdes; `-k seguradora` → 2 passed; `-k rim` cobre golden ITUB4, bad-bank, terminal normalizado. |
| `tests/test_backtest_bancos.py` | Gate de quórum sem `xfail`, `test_backtest_alvos_recalibrados` cravando ITUB4/BBAS3/BBDC4 | ✓ VERIFIED | 4 testes, todos verdes; `grep -c pytest.mark.xfail` = 0. |
| `tests/fixtures/fair_values_bancos.yaml::BBSE3.excecao_nota` | Nota descrevendo a rota (não mais a falha) | ✓ VERIFIED | Linha 16: texto atualizado para "rota DDM-franquia... arquétipo documentado... aterrissa em ≈R$39,87... dentro da banda". |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `report.py::_intrinseco_por_motor` | `motores.py::rim` | `roe_terminal=_roe_through_cycle(c, rim_cfg)` | WIRED | Confirmado por leitura direta (linha 250) e pelo resultado ao vivo: BBAS3/BBDC4 mudaram de valor (43,89/13,37) vs. os antigos 45,60/10,47, provando que o through-cycle está de fato influenciando o cálculo via este link. |
| `report.py::_intrinseco_por_motor` | `arquetipo.py::_setor_casa_token` | detecção do token "seguradora" no setor CVM | WIRED | Confirmado por leitura (linha 229-231) e pelo resultado ao vivo: BBSE3 rotula `motor="seguradora"` e ITUB4 (setor "Bancos") permanece `motor="rim"` — `test_rota_seguradora_nao_pega_banco` cobre a regressão negativa. |
| `report.py::_intrinseco_por_motor` (ramo seguradora) | `ddm.py::valor_gordon` | `valor_gordon(dpa_recorrente*(1+g), a.ke, g_estavel)` | WIRED | Linha 234; valor recomputado independentemente bate exatamente com o output ao vivo (39,868 via `dpa_recorrente=3,83404`, `ke_live=0,123572`, `g=0,025`). |
| `tests/test_backtest_bancos.py` | `src/analista/backtest.py::rodar_cesta` | gate de quórum reusa o mesmo harness do script | WIRED | Confirmado — `_rodar()` no teste chama `carregar_snapshot`/`carregar_fair_values`/`rodar_cesta`, os mesmos símbolos importados de `analista.backtest`. |

### Data-Flow Trace (Level 4)

Motor numérico puro (sem UI). Rastreei diretamente: `snapshot congelado (YAML)` → `carregar_snapshot` → `CompanyData` → `report.analisar_acao/_intrinseco_por_motor` → `motores.rim`/`ddm.valor_gordon` → float real (não estático). Confirmado com reprodução independente fora da suíte (valores idênticos aos dos testes, ver Truths #1 e #5). Nenhum valor hardcoded/vazio encontrado no caminho de dados.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| ITUB4 bit-idêntico ao legado (cap satura) | Reprodução inline: `motores.rim(...)` com `roe_terminal=None` vs `roe_terminal=0.20` | `32.87214820406446 == 32.87214820406446` | PASS |
| Cesta 4/4 via `rodar_cesta` (fora do pytest) | Script Python inline usando `analista.backtest` | ITUB4=32.88(rim) · BBAS3=43.89(rim) · BBDC4=13.37(rim) · BBSE3=39.87(seguradora); todos `passa=True` | PASS |
| xfail removido | `grep -c "pytest.mark.xfail" tests/test_backtest_bancos.py` | `0` | PASS |
| Arquivos proibidos intocados na it.2 | `git diff beafcc4..HEAD --stat -- ddm.py fundamentals.py arquetipo.py selo.py lentes.py` | vazio | PASS |
| Suíte completa | `pytest -q` | 447 passed, 0 failed | PASS |
| Goldens-chave (ddm/vulc3/selo/motores) | `pytest tests/test_ddm.py tests/test_vulc3_regressao.py tests/test_selo.py tests/test_motores.py -q` | 45 passed | PASS |
| Gate de bancos isolado | `pytest tests/test_backtest_bancos.py -q` | 4 passed | PASS |
| Rota seguradora isolada | `pytest tests/test_motores.py -k seguradora -q` | 2 passed | PASS |

### Probe Execution

Não aplicável — nenhum `scripts/*/tests/probe-*.sh` declarado nos planos ou presente no repositório. Skipped.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CAL-01 | 04-01/04-02/04-03-PLAN.md | RIM ganha valor terminal, parametrizado; ITUB4 R$32-40; calibração generaliza na cesta | SATISFIED | Truths #1, #2, #5 — R$32,88 + cesta 4/4, todos os knobs em config.yaml. |
| CAL-02 | 04-01-PLAN.md | Ke do RIM revisado ke_teto 0.14→0.13, sem explosão | SATISFIED | Truth #3. |

`REQUIREMENTS.md` marca ambos CAL-01/CAL-02 como `[x]` e traça para Phase 4 — consistente. Sem requisitos órfãos para a Phase 4 (VAL-01/VAL-02 → Phase 5, OPS-01 → Phase 6, corretamente fora do escopo desta fase).

### Anti-Patterns Found

Nenhum bloqueador. Nenhum marcador de débito (`TBD`/`FIXME`/`XXX`) nos arquivos modificados pela iteração 2 (`motores.py`, `report.py`, `config.yaml`, `tests/test_motores.py`, `tests/test_backtest_bancos.py`, `tests/fixtures/fair_values_bancos.yaml`). O único match de `TODO` foi um falso-positivo (substring de "TODOS" em comentário, não um marcador real).

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_backtest_bancos.py` | 8-20 (docstring do módulo) | Documentação desatualizada — descreve o estado pós-04-02 ("3/4 na banda + BBSE3 FAIL documentado") e não foi atualizada após o 04-03 entregar 4/4 (BBSE3 agora passa via rota seguradora, `passa=True`) | ℹ️ Info | Não afeta comportamento nem os asserts do teste (que passam corretamente com 4/4 real). É só uma inconsistência textual entre o docstring e o resultado real — pode confundir um leitor futuro sobre o estado da cesta. Recomendação: atualizar o docstring para refletir 4/4 num follow-up de housekeeping. |
| `.planning/ROADMAP.md` | linha 85 | Checkbox `[ ] 04-03-PLAN.md` não marcado como concluído, apesar de `STATE.md` confirmar "Fase 04 completa" e o código/testes provarem a entrega | ℹ️ Info | Puramente de rastreamento de planejamento; não é um gap de código. `STATE.md` já está correto ("Completed 04-03-PLAN.md"). |

### Human Verification Required

Nenhum. Fase é um motor numérico puro (sem UI, sem serviço externo, sem comportamento visual/assíncrono) — todas as alegações foram verificadas programaticamente e reproduzidas de forma independente (não só confiando no pytest ou nos SUMMARYs).

### Gaps Summary

Nenhum gap encontrado. O loop D-12 está fechado: a cesta de bancos cruza 4/4 na banda ±15% (ITUB4≈32,88/BBAS3≈43,89/BBDC4≈13,37 via RIM recalibrado com normalização through-cycle do ROE terminal; BBSE3≈39,87 via rota de seguradora Gordon-franquia), o `xfail(strict)` foi removido do gate, o ITUB4 não regrediu (bit-idêntico, prova de saturação do cap reproduzida), o Ke do RIM permanece são (sem explosão), a suíte completa está verde (447 passed) e os arquivos proibidos (`ddm.py`/`fundamentals.py`/`arquetipo.py`/`selo.py`/`lentes.py`) seguem intocados desde o início da iteração 2. Dois achados de nível informativo (docstring desatualizado em `test_backtest_bancos.py` e checkbox não marcado em `ROADMAP.md`) são puramente de documentação e não bloqueiam o fechamento da fase — recomenda-se corrigi-los num housekeeping leve, mas não impedem prosseguir para a Fase 6.

---

_Verified: 2026-07-13_
_Verifier: Claude (gsd-verifier)_
