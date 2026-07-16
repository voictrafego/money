---
phase: 10-primitivas-sem-vi-s-prim
plan: 03
subsystem: valuation
tags: [ipca, deflacao, motor-ciclico, bcb-sgs, offline-stamping, rf-mirror, knob-budget]

# Dependency graph
requires:
  - phase: 10-primitivas-sem-vi-s-prim
    plan: 01
    provides: "norm.media_ciclo = média through-cycle do motor cíclico (o consumidor da série deflacionada); estimator split estabelecido"
provides:
  - "macro.ipca_deflatores_anuais(anos) = {ano: fator para o último ano} da série anual do IPCA (BCB SGS 13522-dez), com degradação graciosa (rede falha → {}), espelhando _selic_historico"
  - "report.py ramo 'normalizado' deflaciona c.serie('lucro_liquido') a reais do último ano (lido offline de cfg['macro']['ipca_deflatores']) ANTES de norm.media_ciclo; fallback nominal never-raise"
  - "stamping nos entry points (cli/app) + leitura no snapshot (backtest.carregar_snapshot) — mesma disciplina offline do rf_local; engine determinística"
  - "config.yaml bloco macro.ipca_deflatores {} default (fora do escopo do orçamento de knobs — dado do BCB, não valuation knob)"
affects: [11-crescimento-grow, 10-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Offline entry-point stamping (espelho do rf_local): rede só no entry point, engine lê cfg carimbado — nova aplicação para o deflator do IPCA (PRIM-04)"
    - "Separação rede/pureza: _ipca_anual_dezembro (rede) x _compor_deflatores (função pura) → composição testável offline, independente de qual série legítima do SGS alimenta"

key-files:
  created:
    - tests/test_macro_ipca.py
    - tests/test_deflacao_ciclica.py
  modified:
    - src/analista/ingest/macro.py
    - src/analista/report/report.py
    - config.yaml
    - src/analista/cli.py
    - app.py
    - src/analista/backtest.py
    - tests/classificacao.yaml
    - tests/test_backtest_bancos.py
    - tests/test_motores.py
    - tests/helpers_blindagem.py
    - scripts/backtest_bancos.py

key-decisions:
  - "SGS 13522 amostrado em DEZEMBRO (constante IPCA_12M reusada): o acumulado 12m no fechamento de dezembro É o IPCA do ano-calendário — sem escolha livre de ano-base (D-03: reais do último ano). Não é knob."
  - "macro.ipca_deflatores vive em bloco macro NOVO, FORA do escopo do lock (motores/capm/ddm/normalizacao): dado objetivo do BCB como o rf, não grau de liberdade de valuation. Orçamento intacto em 3 graus."
  - "Nenhum snapshot de teste modificado: o único snapshot com backtest (bancos) roteia 100% para RIM/seguradora, NÃO exercita o motor cíclico. carregar_snapshot lê ipca_deflatores defensivamente (ausente → {}); adicionar a chave a um snapshot RIM-only seria carimbo vazio sem função."

patterns-established:
  - "Deflate-then-average via cfg carimbado (RESEARCH Pattern 3): a série vira reais do último ano ANTES da média through-cycle, com a rede confinada ao entry point"

requirements-completed: [PRIM-04]

# Metrics
duration: 12min
completed: 2026-07-16
---

# Phase 10 Plan 03: Deflação IPCA do motor cíclico (PRIM-04) Summary

**O motor cíclico deixou de somar reais NOMINAIS de anos diferentes: a série de lucro é trazida a reais do último ano (deflacionada por IPCA do BCB) ANTES da média through-cycle, com os deflatores resolvidos UMA vez nos entry points e carimbados em `cfg` — a engine os lê offline exatamente como o `rf_local`, permanecendo determinística. Zero dependência nova, zero knob novo (orçamento de 3 graus intacto), zero golden de nível tocado.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-16T12:06:13Z
- **Completed:** 2026-07-16T12:18:02Z
- **Tasks:** 3 (Task 1 macro RED→GREEN; Task 2 deflação RED→GREEN; Task 3 stamping)
- **Files:** 2 criados, 11 modificados

## Accomplishments
- **PRIM-04 (Task 1):** `macro.ipca_deflatores_anuais(anos)` copia o esqueleto de `_selic_historico` (date-range + 3 retries + `time.sleep` + degradação graciosa para `{}`). Separação limpa: `_ipca_anual_dezembro` (rede, SGS 13522 filtrado nos pontos de dezembro = IPCA do ano-calendário) × `_compor_deflatores` (função PURA: `{ano: prod(1+ipca[y]) para y in ano+1..T}`, `defl[T]=1.0`). Convenção de fração `/100.0` como `ipca_12m`.
- **PRIM-04 (Task 2):** o ramo `"normalizado"` de `_intrinseco_por_motor` deflaciona `c.serie('lucro_liquido')` por `cfg['macro']['ipca_deflatores']` (lido OFFLINE) antes de `norm.media_ciclo`; fallback nominal never-raise quando deflatores ausentes/vazios. Estimador segue a MÉDIA through-cycle (`media_ciclo`), NÃO o endpoint Theil-Sen — `motores.ciclica.anos_media:10`/`winsor:0.10` congelados intocados.
- **PRIM-04 (Task 3):** stamping em `cli.py` e `app.py` (via `@st.cache_data`) na MESMA janela do `rf` (`rf_ciclo_anos`, a simetria que torna o valuation invariante à inflação); `backtest.carregar_snapshot` lê o carimbo do snapshot (`ipca_deflatores` em `_CHAVES_GLOBAIS`, defensivo → `{}`) e `rodar_cesta` o injeta numa CÓPIA do cfg — espelho exato do `rf_local`.
- **Suíte default:** **483 passed, 1 skipped, 34 deselected, 1 xfailed, 0 failed** (era 477 + 6 testes novos). Orçamento de 3 knobs intacto (`git diff calibracao.lock.yaml` VAZIO; `config.yaml` só adiciona o bloco `macro` aditivo, fora do escopo). Nenhum golden de nível atualizado/deletado.

## Task Commits

1. **Task 1: RED — deflatores anuais do IPCA (composição offline)** — `0f44dae` (test)
2. **Task 1: GREEN — macro.ipca_deflatores_anuais (SGS 13522-dez travado)** — `69766c2` (feat)
3. **Task 2: RED — ramo cíclico deve deflacionar antes da média** — `701d6ea` (test)
4. **Task 2: GREEN — ramo cíclico deflaciona a série a reais do último ano** — `c14aee5` (feat)
5. **Task 3: stamp ipca_deflatores nos entry points + snapshot loader** — `5528819` (feat)

**Plan metadata:** _(este commit)_ `docs(10-03)`

## Files Created/Modified
- `tests/test_macro_ipca.py` (novo) — 4 testes OFFLINE: composição pura (fator do último ano = 1,0; anteriores > 1,0), fronteira vazia → `{}`, fim-a-fim com fetch monkeypatchado (zero rede), degradação graciosa.
- `tests/test_deflacao_ciclica.py` (novo) — 2 testes OFFLINE: base cíclica deflacionada > nominal (série inflacionária) via o ramo real de `_intrinseco_por_motor`; fallback nominal (ausência ≡ vazio) never-raise.
- `src/analista/ingest/macro.py` — `_compor_deflatores` (pura), `_ipca_anual_dezembro` (fetch SGS 13522-dez, esqueleto do `_selic_historico`), `ipca_deflatores_anuais` (resolvedor de entry point); `import Dict`.
- `src/analista/report/report.py` — ramo `"normalizado"`: deflaciona a série por `cfg['macro']['ipca_deflatores']` (offline) antes de `media_ciclo`; fallback nominal.
- `config.yaml` — bloco `macro.ipca_deflatores: {}` default (aditivo; entry points sobrescrevem; NÃO é knob de valuation).
- `src/analista/cli.py` / `app.py` — stamping dos deflatores (janela do `rf`); `app.py` via `@st.cache_data` (uma chamada de rede por execução, read-only).
- `src/analista/backtest.py` — `ipca_deflatores` em `_CHAVES_GLOBAIS`; `carregar_snapshot` lê e devolve o carimbo (3-tupla); `rodar_cesta` injeta em CÓPIA do cfg (param opcional).
- `tests/test_backtest_bancos.py`, `tests/test_motores.py`, `tests/helpers_blindagem.py`, `scripts/backtest_bancos.py` — call sites atualizados para a nova 3-tupla de `carregar_snapshot`.
- `tests/classificacao.yaml` — 6 entradas novas (1 invariante de composição, 1 invariante de direção, 4 contratos de fronteira/offline) no mesmo diff (0 órfão).

## Decisions Made
- **SGS 13522 amostrado em dezembro** (RESEARCH Open Q2 RESOLVED/LOCKED / A1): reusa a constante existente `IPCA_12M`; o acumulado 12m no fechamento de dezembro = IPCA do ano-calendário, sem escolha livre de ano-base. A verificação da composição no teste é independente da série (só a precisão numérica depende do código SGS).
- **`macro.ipca_deflatores` fora do escopo do lock:** dado objetivo do BCB (como o `rf`), não grau de liberdade. O `test_orcamento_de_knobs_e_exatamente_3` só varre os 4 blocos do escopo (`motores/capm/ddm/normalizacao`) — o bloco `macro` novo é aditivo e não entra na partição, como `screening`/`indicadores`. Orçamento segue 3 graus.

## Deviations from Plan

### Auto-fixed (Rule 3 — consistência de assinatura, blocking)

**1. [Rule 3 — Assinatura] `carregar_snapshot` virou 3-tupla → 4 call sites atualizados (fora da lista literal de files_modified)**
- **Found during:** Task 3 (o plano manda `carregar_snapshot` "devolver o deflator ao caller", o que muda a aridade do retorno de `(empresas, rf_local)` para 3 valores).
- **Issue:** 4 chamadores desempacotam a 2-tupla (`tests/test_backtest_bancos.py` ×2, `tests/test_motores.py`, `tests/helpers_blindagem.py`, `scripts/backtest_bancos.py`) — a mudança de assinatura os quebraria com "too many values to unpack".
- **Fix:** call sites atualizados para a 3-tupla; os que passam adiante ao `rodar_cesta` threadam o deflator (bancos → RIM, degrada a `{}`); os de cfg manual desempacotam e (onde faz paridade) injetam `macro`. `backtest.py` está em `files_modified`; os 4 chamadores não estavam — atualização mecânica necessária.
- **Files modified:** tests/test_backtest_bancos.py, tests/test_motores.py, tests/helpers_blindagem.py, scripts/backtest_bancos.py
- **Committed in:** `5528819`

### Desvio de premissa (documentado — snapshot NÃO modificado)

**2. [Premissa] Nenhum snapshot de teste recebeu a chave `ipca_deflatores`**
- **Found during:** Task 3 (o plano prevê adicionar `ipca_deflatores:` "ao(s) snapshot(s) que EXERCITAM o motor cíclico").
- **Issue/realidade:** o único snapshot com backtest (`snapshot_bancos_2026-07-12.yaml`) tem 4 tickers que roteiam 100% para RIM/seguradora — NENHUM exercita o motor cíclico `"normalizado"`. Adicionar a chave ali seria um carimbo VAZIO sem função (os bancos nunca leem o deflator).
- **Resolução:** `carregar_snapshot` lê `snap.get("ipca_deflatores") or {}` (defensivo → `{}`); `ipca_deflatores` entra em `_CHAVES_GLOBAIS` (proteção para qualquer snapshot cíclico futuro). Respeita "NÃO regenerar snapshots" (RESEARCH §Runtime State) — não havia o que carimbar num snapshot RIM-only.
- **Committed in:** `5528819`

**Total deviations:** 2 (1 auto-fix mecânico de assinatura + 1 desvio de premissa honesto sobre o snapshot). Nenhuma tolerância afrouxada, nenhum `xfail`→`skip`, nenhum assert de guarda removido, nenhum knob movido, nenhum golden de nível tocado.

## Issues Encountered / Golden de nível quebrado (reportado, NÃO tocado)

Ao rodar `-m golden_nivel` no HEAD, **4 golden_nivel estão vermelhos** — TODOS pré-existentes ao 10-03 (verificado por execução no commit `abeab5a`, fim do 10-02, ANTES deste plano):
- `test_backtest_bancos.py::test_backtest_alvos_recalibrados` (ITUB4 32,88 — o golden de saída do PRIM-05)
- `test_motores.py::test_rota_seguradora_bbse3_gordon_franquia` (BBSE3 39,87)
- `test_growth_reconciliacao.py::test_teto_absoluto_025_quando_g_fund_e_cagr_explodem`
- `test_growth_reconciliacao.py::test_trava_ke_quando_g_fund_supera_ke`

**Nenhum é consequência do PRIM-04:** os bancos roteiam para RIM e a BBSE3 para o motor seguradora (Gordon) — nenhum passa pelo ramo `"normalizado"` que este plano alterou. Os 4 foram movidos por PRIM-01/PRIM-02 (10-01/10-02) e ficam quarentenados/intactos por contrato (v2.4: golden de nível é DELETADO pela fase que corrige o método, nunca atualizado). O golden ITUB4=32,88 e a cesta de bancos são o critério de saída do plano **10-04 (PRIM-05)**; os 2 de `g` aguardam a Fase 11.

## Threat Flags
Nenhuma superfície nova de fato. T-10-05/06/07 mitigados como planejado: parsing defensivo (`try/except → {}`) + 3 retries + degradação graciosa (a engine cai na série nominal); rede confinada ao entry point; `test_backtest_determinismo` prova a engine offline.

## Known Stubs
Nenhum. O `config.yaml macro.ipca_deflatores: {}` é o DEFAULT offline (como `capm.rf_local`), sobrescrito nos entry points — não é stub de UI.

## User Setup Required
None.

## Next Phase Readiness
- PRIM-04 entregue. O motor cíclico consome uma série deflacionada a reais do último ano, resolvida offline; engine determinística; sem knob novo; sem dependência nova.
- **Para o 10-04 (PRIM-05):** os golden_nivel de nível ITUB4/BBSE3/cesta-de-bancos seguem vivos e quarentenados — sua DELEÇÃO (não atualização) é o critério de saída do plano 10-04.
- **Blocker/nota:** o golden ITUB4=32,88 continua no repo (deleção é do 10-04). A deflação da base do CAGR/`g` NÃO foi tocada (é a Fase 11, D-03 boundary).

## Self-Check: PASSED
- FOUND: 10-03-SUMMARY.md
- FOUND: tests/test_macro_ipca.py, tests/test_deflacao_ciclica.py
- FOUND commit 0f44dae (Task 1 RED), 69766c2 (Task 1 GREEN)
- FOUND commit 701d6ea (Task 2 RED), c14aee5 (Task 2 GREEN)
- FOUND commit 5528819 (Task 3)
- ipca_deflatores_anuais present in macro.py (1); ramo "normalizado" reads cfg['macro']['ipca_deflatores']; _CHAVES_GLOBAIS inclui ipca_deflatores; calibracao.lock.yaml diff VAZIO

---
*Phase: 10-primitivas-sem-vi-s-prim*
*Completed: 2026-07-16*
