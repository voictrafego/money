---
phase: 08-saneamento-do-motor-ddm
plan: 04
subsystem: valuation
tags: [FIX-06, guardrails, banda-sensibilidade, dy-recorrente, setor-override, golden-regressao, capstone]

requires:
  - phase: 08-01 (FIX-04)
    provides: "primitiva normalizacao.base_normalizada (reusada p/ DPA recorrente) + roe_valuation/payout_valuation canônicos (cross-menu)"
  - phase: 08-02 (FIX-02)
    provides: "g_alto subordinado ao g sustentável (payout 100% ⇒ g_alto=0) — cravado no golden VULC3"
  - phase: 08-03 (FIX-03)
    provides: "Ke local (rf_local 0,105 fallback + beta×ERP) — Ke 15,78% determinístico offline no golden"
provides:
  - "report.py: banda vmin/vmax derivada da matriz Ke×g (sensibilidade REAL), não do toggle binário ddm_constante×ddm_h; fallback gracioso p/ matriz só-None (T-08-07)"
  - "fundamentals.py: dpa_recorrente()/dy_recorrente() sobre provento NORMALIZADO, distinto do dy_atual() trailing; ambos exibidos"
  - "universe.py: override de setor display-only por ticker (dict {cd_cvm,setor}) com atalho offline; _resolver_base preserva match por nome/token-set"
  - "data/ticker_map.json: VULC3 = 11762 + setor 'Calçados (Consumo Cíclico)' (corrige Têxtil errado da CVM)"
  - "tests/test_vulc3_regressao.py: golden de regressão end-to-end (cascata FIX-04→02→03→06 domada), capstone da fase"
affects: []

tech-stack:
  added: []
  patterns:
    - "Banda intrínseca = sensibilidade real (min/max da matriz Ke×g já calculada), filtrando células None antes do min/max"
    - "DY recorrente reusa a primitiva de normalização (Plan 01) sobre a série de proventos — mesmo espírito do roe_valuation/lpa_valuation"
    - "Override de setor display-only: wrapper resolver() aplica o override e delega a _resolver_base (sem refatorar todos os return points)"

key-files:
  created:
    - tests/test_guardrails_fix06.py
    - tests/test_vulc3_regressao.py
  modified:
    - src/analista/core/fundamentals.py
    - src/analista/report/report.py
    - src/analista/ingest/universe.py
    - data/ticker_map.json

key-decisions:
  - "Banda = min/max da matriz de sensibilidade (Ke×g), não dos 2 cenários centrais; fallback p/ os 2 cenários quando a matriz é só-None (DDM não rodou)"
  - "DY recorrente sobre dividendo normalizado (mediana/winsor) — distinto e nunca maior que o trailing; trailing PRESERVADO (contexto + detector de armadilha)"
  - "Setor override display-only (item K): dict {cd_cvm,setor} no ticker_map com atalho 100% offline; nenhum cálculo de valuation consome setor"
  - "Golden VULC3: limiar do intrínseco = 3× o preço (folga sobre o ~2,3× observado; pré-fix era 11–23×) — justificado, não número mágico"

requirements-completed: [DDM-FIX-06]

duration: ~35min
completed: 2026-06-27
---

# Phase 8 Plan 04: Guardrails + regressão VULC3 (FIX-06, capstone) Summary

**Fecha a cascata VULC3 com os ajustes de apresentação (banda = sensibilidade Ke×g real, DY recorrente vs trailing, setor Calçados) e o caso de regressão golden end-to-end que falha se qualquer FIX-04/02/03/06 regredir: o intrínseco do VULC3 sintético cai de 11–23× para 2,3× o preço, o veredito é "VERIFICAR" (não verde) e ROE/payout batem entre Analisar e Ranking.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 2 (Task 1 em TDD: RED → GREEN)
- **Files modified:** 6 (2 criados, 4 modificados)
- **Tests:** 133 passed (126 baseline + 5 guardrails + 2 regressão)

## Accomplishments

- **Banda intrínseca = sensibilidade REAL (item H):** `vmin/vmax` passam a derivar do min/max dos valores não-None da matriz Ke×g (`ddm.matriz_sensibilidade`, que já era calculada e só virava tabela), em vez do toggle binário `ddm_constante × ddm_h`. A matriz cobre o grid `delta_ke × delta_g` do config — é a sensibilidade econômica de fato (um Ke menor / g maior abre o teto da banda). Fallback gracioso preservado (matriz só-None ⇒ degrada para os 2 cenários, sem célula inválida virar banda espúria — T-08-07).
- **DY recorrente vs trailing (item J):** `dy_recorrente()`/`dpa_recorrente()` aplicam a MESMA normalização do Plan 01 (mediana/winsor) sobre a série de proventos, devolvendo a renda sustentável — distinta do `dy_atual()` trailing, que carrega o ano extraordinário. Ambos exibidos nos múltiplos ("DY" e "DY rec.") e no relatório; o trailing foi PRESERVADO (segue como contexto e como detector de armadilha de dividendos do FIX-05).
- **Setor correto (item K):** override display-only por ticker em `data/ticker_map.json` (forma dict `{cd_cvm, setor}`); `resolver()` virou um wrapper fino que aplica o override de setor e delega a resolução de CD_CVM a `_resolver_base` (preservando match por nome/token-set). VULC3 = 11762 + "Calçados (Consumo Cíclico)", corrigindo o "Têxtil e Vestuário" que o SETOR_ATIV da CVM classifica errado. Atalho 100% offline quando cd+setor estão no override.
- **Golden de regressão VULC3 (capstone):** `tests/test_vulc3_regressao.py` monta offline a patologia (1 ano de lucro extraordinário 3× dentro da janela, dividendos ≥ lucro ⇒ payout > 100%, beta 0,88, preço 14,40) e trava os 6 invariantes da cascata domada + a consistência cross-menu.

## VULC3 sintético — cascata domada (números observados)

| Vetor | Pré-fix (FINDINGS) | Pós-cascata (golden) | FIX |
|-------|--------------------|----------------------|-----|
| Base de lucro de valuation | lucro cru 12000 (ano extraordinário) | mediana 4000 | FIX-04 |
| g_alto adotado | 25% | **0,0** (payout_valuation=100% ⇒ g_fund=0) | FIX-02 |
| Ke | 9,43% (literais 2019) | **15,78%** (rf_local 0,105 + 0,88×0,06) | FIX-03 |
| Intrínseco (teto da banda) | 167–334 (11–23× o preço) | **32,72 (2,3× o preço)** | FIX-01/06 |
| Veredito | SUBAVALIADA (verde) | **VERIFICAR** (payout>100% + DY>15%) | FIX-05 |
| ROE/payout Analisar vs Ranking | — | **iguais** (cross-menu) | Core Value |

## Task Commits

1. **Task 1 (RED): golden dos guardrails** — `813e69c` (test)
2. **Task 1 (GREEN): banda real + DY recorrente + setor VULC3** — `1635bf8` (feat)
3. **Task 2: golden de regressão VULC3 (cascata domada)** — `69721f5` (test)

_TDD na Task 1: RED (4/5 falham — banda, DY recorrente ×2, setor; o 5º é o teste de degradação, que já passa por ser o fallback atual) → GREEN. Sem REFACTOR._

## Rebaseline dos golden (com justificativa)

**Nenhum golden existente precisou de rebaseline.** A banda mais larga (sensibilidade real) NÃO virou nenhum caso existente: `test_consistencia_modos::test_veredito_direcao_coerente` (alvo crescente, preço 5,50) seguiu "abaixo do intervalo" mesmo com `vmin` menor (a matriz alcança um Ke maior), mantendo a direção SUBAVALIADA; `test_report.py` não assere sobre `vmin/vmax`; `test_ddm.py`/`test_multiples.py` são matemática pura com literais. Os 126 testes do baseline + 7 novos ficaram verdes sem afrouxar nenhum assert.

## Decisions Made

- **Banda = min/max da matriz, não dos 2 cenários.** A matriz Ke×g já existia (só virava tabela de sensibilidade); reusá-la para a banda é a leitura honesta de "amplitude por sensibilidade real" (CONTEXT item H), e o center cell coincide com o `ddm_constante` antigo — a banda só ALARGA simetricamente. Fallback p/ os 2 cenários quando a matriz é só-None mantém a degradação graciosa (T-08-07).
- **DY recorrente reusa a primitiva de normalização.** Em vez de inventar uma síntese de dividendo nova, apliquei `norm.base_normalizada` sobre a série `dividendos` — mesmo espírito de `roe_valuation`/`lpa_valuation`. O recorrente nunca supera o trailing; ambos exibidos.
- **Override de setor por wrapper.** Em vez de refatorar todos os return points de `resolver`, criei `_resolver_base` (resolução de CD_CVM intacta) e um `resolver` fino que aplica o setor override. Atalho offline (cd+setor no override) evita tocar o cadastro CVM (rede) no teste.
- **Limiar do intrínseco = 3× o preço.** Documentado: pós-cascata o teto da banda é ~2,3× o preço; 3× dá folga sem ser frouxo — qualquer regressão de FIX-01/02/03 (que reinflaria o intrínseco) estouraria os 3×. Não é número mágico.

## Deviations from Plan

None - plan executado como escrito. `config.yaml` estava em `files_modified` por precaução, mas nenhuma mudança de config foi necessária: a banda reusa `ddm.sensibilidade` (já existente) e o DY recorrente reusa o bloco `normalizacao` (Plan 01). A fixture de regressão saiu calibrada de primeira (cascata domada confirmada num script antes de escrever os asserts).

## Issues Encountered

None.

## Known Stubs

Nenhum. Toda a lógica consome dados reais via os métodos canônicos; o setor override é dado curado (display-only).

## Threat Flags

Nenhuma nova superfície. T-08-07 (matriz só-None vira banda inválida) **mitigado**: as células None são filtradas antes do min/max e o fallback degrada para os 2 cenários (coberto por `test_banda_degrada_quando_ddm_nao_roda`). T-08-08 (setor override desatualiza vs CVM) **aceito**: é display-only, curado à mão, baixo impacto (item K) — nenhum cálculo de valuation consome setor.

## Next Phase Readiness

- **Fase 8 fechada (4/4 plans):** a cascata VULC3 está domada e travada por regressão. O veredito do VULC3 deixa de ser um falso "SUBAVALIADA" verde — a Phase 6 (matriz fundamento×técnico, que lê `a.veredito` como token líder) passa a propagar um veredito correto.
- Próximo no marco v1.2: Phase 7 (UI — overlays/subpainéis), agora sobre um motor fundamentalista saneado.

## Self-Check: PASSED
