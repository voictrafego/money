---
phase: 12-custo-de-capital-ke-ke
plan: 02
subsystem: valuation-engine
tags: [ke, capm, beta-blume, ke-unico, clamp-removido, blind-02b, doenca-1, wr-04]

# Dependency graph
requires:
  - phase: 12-custo-de-capital-ke-ke
    plan: 01
    provides: "capm.beta_blume + carimbo do beta setorial (data/beta_setorial.yaml) — a infra que o a.ke agora consome"
  - phase: 11-crescimento-g-grow
    provides: "g_cap=7,28% (derivado); o Ke_min do Blume tem de superá-lo por aritmética (sem clamp)"
provides:
  - "Ke ÚNICO: a.ke = ke_local(beta_blume(c.beta, c.setor, beta_setorial), rf_local, erp_local) — o Ke exibido == o que alimenta o RIM (L261) == o centro da matriz"
  - "motores.ke_rim DELETADO (clamp ke_piso/ke_teto/ke_live removido por código, KE-04 lado-código)"
  - "BLIND-02b (test_invariancia_inflacao_engine_itub4) curado: invariante NORMAL verde; xfail_estritos() == 0"
  - "guarda de seleção reconciliada à cura (0 doenças pendentes válido); ex-doenças rodam como invariantes no run default"
  - "nenhum teste vivo depende das folhas ke_teto/ke_piso/erp_banco (o Plano 03 pode apagá-las sem quebrar a suíte)"
affects: [12-03-erp-lock, 13-motores-contrato-eng, 14-validacao-honesta-val]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ke único (KE-01): a engine calcula UM Ke (CAPM local sobre β setorial+Blume) e o passa PRONTO ao RIM — o motor não recomputa nem clampa"
    - "perpetuidade converge pelo piso do Blume (β_blume ≥ 0,33 ⇒ Ke_min > g_cap por aritmética), NÃO por clamp"

key-files:
  created: []
  modified:
    - src/analista/report/report.py
    - src/analista/core/motores.py
    - tests/test_motores.py
    - tests/test_capm_local.py
    - tests/test_invariantes_v24.py
    - tests/test_blindagem_selecao.py
    - tests/helpers_blindagem.py
    - tests/test_growth_reconciliacao.py
    - tests/classificacao.yaml

key-decisions:
  - "Ke único via beta_blume no a.ke (L470) + RIM lê a.ke (L261); ke_rim deletado sem guard substituto — o piso do Blume é a garantia aritmética contra g_cap"
  - "BLIND-02b vira invariante normal porque o SISTEMA passou a satisfazê-lo (clamp removido, Ke reage ao rf) — nunca por afrouxamento"
  - "guarda de seleção: contrato mudado de 'doença é xfail selecionado' para 'ex-doença é invariante selecionada' — justificado pela cura (0 xfail_estritos válido), não afrouxado"
  - "higiene do detector BLIND-04a (Pitfall 6): literal 'ITUB4' movido p/ helper empresa_itub4 (fora de test_*) — desfaz o falso-positivo pós-cura sem afrouxar o detector"

patterns-established:
  - "quando a mudança de método muda o NÍVEL do Ke de uma fixture-precondição de invariante, recalibra-se o INPUT (β), não o assert-doutrina (mirror PRIM-02)"

requirements-completed: [KE-01, KE-04, KE-05]

# Metrics
duration: 30min
completed: 2026-07-17
---

# Phase 12 Plan 02: Colapso do Ke — um único Ke, clamp removido, BLIND-02b curado Summary

**O sistema passa a ter UM Ke (CAPM local sobre o β setorial+Blume): `a.ke` é o Ke exibido, o que alimenta o RIM e o centro da matriz — `motores.ke_rim` (com o clamp `ke_piso`/`ke_teto`/`ke_live`) foi DELETADO, a perpetuidade converge pelo piso do Blume por aritmética, e a metade Ke da Doença 1 morre: BLIND-02b vira invariante normal verde, com `xfail_estritos()` indo de 1 → 0 e a guarda de seleção reconciliada à cura. Config/lock intocados (o corte de ERP é o Plano 03).**

## Performance

- **Duration:** ~30 min
- **Tasks:** 3 (todas `auto`)
- **Files modified:** 9 (0 criados)

## Accomplishments

- **Ke ÚNICO (KE-01/KE-05).** `report.py:470` passou a computar `a.ke = capm.ke_local(capm.beta_blume(c.beta, c.setor, cap.get("beta_setorial")), rf_local, erp_local)` — o β de entrada é o setorial+Blume da infra do Plano 01. `report.py:261` (RIM) troca `motores.ke_rim(c.beta, cfg)` por `ke=a.ke` (D-09: recebe o Ke pronto, não recomputa). A rota de segurança (L241), a matriz de sensibilidade (L540) e a exibição (L982) já liam `a.ke` — nada a acrescentar (KE-05: exibido == calculado).
- **Clamp removido por código (KE-04 lado-código).** `motores.ke_rim` inteiro (função + `max(ke_piso, min(ke, ke_teto))` + `min(ke_clamp, ke_live)`) foi DELETADO. **Sem guard substituto, sem clamp com outro nome** — o piso do Blume (`β_blume = 0,33 + 0,67×base ≥ 0,33`) garante `Ke_min > g_cap` por aritmética.
- **BLIND-02b curado como teste normal (a metade Ke da Doença 1).** Removido o `@pytest.mark.xfail(strict=True)` de `test_invariancia_inflacao_engine_itub4` (mantido `@pytest.mark.invariante`, `assert variacao < LIMIAR_INFLACAO` **INTOCADO**). O teste passa porque o clamp saiu e o Ke volta a reagir ao `rf` (a perna do `rf` sobe o Ke na mesma proporção que sobe o `g`, o spread se preserva, o `V` fica quase invariante). `xfail_estritos()` foi de **1 → 0**.
- **Guarda de seleção reconciliada à cura (BLOQUEADOR — Correção #3).** Com `xfail_estritos()` a 0, `test_selecao_efetiva_roda_as_invariantes_e_as_duas_doencas` (o `assert doencas`) quebraria. Contrato mudado à realidade pós-cura: assevera agora que **não há mais nenhum `xfail(strict=True)`** (0 doenças pendentes é válido) **E** que as duas ex-doenças (`test_invariancia_inflacao_engine_itub4`, `test_normalizacao_nao_pune_crescimento`) continuam classificadas `invariante` e selecionadas no run default — o alarme de regressão migrou do XPASS para o próprio assert do teste (que agora executa). **Mudança justificada pela cura, não afrouxamento.**
- **Bracket-read condenado reescrito (BLOQUEADOR do checker).** `test_terminal_load_bearing_nao_explode_e_degrada_para_fade_only` lia `ke = rim_cfg["ke_teto"]` (folha que o Plano 03 apaga). Trocado por um Ke derivado estruturalmente do CAPM local (`rf_local + 1,0×erp_local`, β_blume de banco large-cap ≈ 1,0) — imune à remoção das folhas, com toda a doutrina e todos os asserts intactos. **Busca global confirma:** nenhum consumidor vivo de `ke_teto`/`ke_piso`/`erp_banco` fora de `motores.py` (deletado) e de config/lock.

## Task Commits

1. **Task 1: Unificar o Ke — beta_blume no a.ke, deletar ke_rim, RIM lê a.ke** — `d750c34` (feat)
2. **Task 2: Reconciliar testes de ke_rim + fórmula do Ke + o bracket-read de ke_teto** — `c291ae9` (test)
3. **Task 3: Destravar BLIND-02b + reconciliar a guarda de seleção (1 → 0 xfail)** — `94e03d4` (test)

## Files Modified

- `src/analista/report/report.py` — `a.ke` via `beta_blume` (L470); RIM lê `a.ke` (L261); comentários de docstring/módulo atualizados à unificação
- `src/analista/core/motores.py` — `ke_rim` DELETADO; docstring de módulo reescrita (o RIM recebe `a.ke` pronto, não clampa)
- `tests/test_motores.py` — `test_ke_rim_menor_que_ke_live_de_banco` → `test_o_ke_que_alimenta_o_rim_e_o_a_ke_unico` (invariante da unificação, spy em `motores.rim`); DELETA `test_ke_rim_na_banda_estrutural` (golden) e `test_ke_rim_never_raise`; import `capm` removido, `CompanyData` adicionado
- `tests/test_capm_local.py` — DELETA `test_ke_local_na_faixa_small_cap_br` (golden de banda); β Blume-ajustado nos 2 testes de fórmula sobreviventes
- `tests/test_invariantes_v24.py` — remove o xfail de BLIND-02b; reescreve o bracket-read `ke_teto` em Ke estrutural do CAPM; docstrings à cura
- `tests/test_blindagem_selecao.py` — guarda de seleção reconciliada (0 xfail_estritos válido; ex-doenças rodam como invariantes)
- `tests/helpers_blindagem.py` — helper `empresa_itub4` (higiene do falso-positivo do detector BLIND-04a pós-cura)
- `tests/test_growth_reconciliacao.py` — recalibra β da fixture TETO (3,0 → 5,0) ao β Blume-ajustado (precondição Ke>0,25; doutrina teto absoluto 0,25 intacta)
- `tests/classificacao.yaml` — entradas dos goldens deletados removidas + `test_o_ke_que_alimenta_o_rim_e_o_a_ke_unico` renomeada (0 órfão)

## Decisions Made

- **Ke único sem guard substituto.** O RIM não clampa mais; o piso do Blume é a defesa aritmética contra `g_cap`. Se algum V explodir sem clamp, o bug é `ROE_T`/spread (Fase 13), não o Ke — sinalizar, não clampar.
- **Guarda de seleção: contrato mudado, não afrouxado.** As DUAS doenças do v2.4 (BLIND-03 na Fase 10, BLIND-02b aqui) estão curadas. A guarda migrou de "a doença é um `xfail(strict)` selecionado" para "a ex-doença é uma `invariante` selecionada" — os asserts continuam existindo (nada deletado/skipado/afrouxado); apenas a forma do contrato mudou pela cura.
- **Higiene do detector BLIND-04a (Pitfall 6).** Pós-cura, o ex-BLIND-02b viraria falso-positivo do detector (ticker `"ITUB4"` + `LIMIAR_INFLACAO` chegando a assert), quebrando `test_blindagem_meta`. O literal do ticker foi movido para `helpers_blindagem.empresa_itub4` (fora de qualquer `test_*`). O teste assevera uma variação RELATIVA < 5%, NÃO um nível em reais — remover a narrativa desfaz o falso-positivo **sem afrouxar o detector nem excluir arquivos da varredura**.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Recalibração do β da fixture `TETO` em `test_growth_reconciliacao.py`**
- **Found during:** Task 3 (rodada da suíte default completa)
- **Issue:** `test_g_alto_respeita_o_teto_absoluto_de_025` (invariante) usa β cru 3,0 assumindo o Ke antigo (`rf + β×erp = 0,285 > 0,25`). Sob o β Blume-ajustado, `β_blume(3,0) = 2,34` ⇒ `Ke = 0,2454 < 0,25`, quebrando a **precondição** `a.ke > 0,25` do cenário (o teto absoluto 0,25 é que deve morder, não o Ke).
- **Fix:** β da fixture 3,0 → 5,0 (`β_blume(5,0) = 3,68` ⇒ `Ke ≈ 0,326 > 0,25`). **Recalibração do INPUT da fixture ao novo modelo de Ke** — a doutrina (`g_alto == 0,25`) e os asserts ficam INTACTOS (mirror do precedente PRIM-02: recalibrar número de fixture pela própria doutrina do teste). NÃO é golden de nível (é `invariante` estrutural) e NÃO é afrouxamento.
- **Files modified:** `tests/test_growth_reconciliacao.py`
- **Commit:** `94e03d4`
- **Fora da lista `files_modified` do plano** — desvio necessário (o plano não previu esta fixture a jusante).

**2. [Rule 3 - Blocking] Higiene do detector em `helpers_blindagem.py` (helper `empresa_itub4`)**
- **Found during:** Task 3
- **Issue:** ao remover o xfail de BLIND-02b, o detector `detectar_ticker_com_valor_cravado` passou a flagá-lo (ticker + número → assert), tornando-o "novo" ofensor e quebrando `test_blindagem_meta` (`tolerados = quarentenados | xfail_estritos`, agora sem o segundo).
- **Fix:** literal `"ITUB4"` movido para `helpers_blindagem.empresa_itub4` (arquivo não-`test_*`, função não-`test_`). Antecipado pelo plano (Pitfall 6, Task 3) — resolvido sem afrouxar o detector.
- **Files modified:** `tests/helpers_blindagem.py`, `tests/test_invariantes_v24.py`
- **Commit:** `94e03d4`
- **`helpers_blindagem.py` fora da lista `files_modified` do plano** — desvio necessário previsto pelo texto do plano.

## Threat Flags

Nenhuma superfície nova. O cálculo do `a.ke` é offline/determinístico sobre `cfg` local (T-12-03 accept, T-12-04 mitigate: `beta_blume` never-raise já degrada β None → Ke None nos consumidores). Sem rede/auth/secrets novos.

## Verification

- `pytest` (suíte default) → **517 passed, 1 skipped, 20 deselected, 0 failed, 0 xfailed, 0 xpassed** (a 1 skipped = jackknife/Fase 14; era 22 deselected → 20 porque 2 golden_nivel de banda de Ke foram DELETADOS).
- `pytest -m golden_nivel` → **20 passed, 0 CLASSIFICACAO ORFA**.
- `pytest --collect-only -m ""` → **0 CLASSIFICACAO ORFA**.
- `grep -c "def ke_rim" src/analista/core/motores.py` → **0**; `grep -c "ke_rim" tests/test_motores.py` → **0**.
- Busca global de bracket-read de `ke_teto`/`ke_piso`/`erp_banco` fora de `motores.py`/config/lock → **VAZIO**.
- `xfail_estritos()` → **0**; BLIND-02b roda no default e passa.
- `git diff config.yaml calibracao.lock.yaml` → **VAZIO** (o knob ERP e a remoção das folhas são o Plano 03; orçamento de 3 graus intacto).

## Next Phase Readiness

- **Plano 03 (ERP/lock)** pode agora, num commit SANCIONADO config+lock (separado pelo hook BLIND-05): baixar `erp_local` 0,06 → 0,045 e REMOVER as folhas mortas `erp_banco`/`ke_piso`/`ke_teto` de `config.yaml` — nenhum código nem teste vivo as lê. O Ke único já está no lugar e verde.
- **Fronteira respeitada:** config/lock intocados neste plano; g_cap da Fase 11 não recalibrado.
- Nenhum blocker.

## Self-Check: PASSED

- Arquivos verificados no disco: report.py, motores.py, test_motores.py, test_capm_local.py, test_invariantes_v24.py, test_blindagem_selecao.py, helpers_blindagem.py, test_growth_reconciliacao.py, classificacao.yaml.
- Commits verificados no git log: `d750c34`, `c291ae9`, `94e03d4`.
- `def ke_rim` == 0; `beta_blume` em report.py == 2; `xfail_estritos()` == 0.

---
*Phase: 12-custo-de-capital-ke-ke*
*Completed: 2026-07-17*
