---
phase: 14-valida-o-honesta-val
verified: 2026-07-20T17:10:00Z
status: passed
score: 7/7 must-haves verified
overrides_applied: 0
---

# Phase 14: Validação honesta (VAL) — Relatório de Verificação

**Objetivo da fase:** "o caso do livro passa (V ≈ R$ 37,22); hold-out roda uma vez, 3 graus de
liberdade, distribuição + jackknife"
**Verificado em:** 2026-07-20T17:10:00Z
**Status:** passed
**Re-verificação:** Não — verificação inicial

## Metodologia

Esta verificação NÃO confiou nas afirmações dos SUMMARY.md. Todo número reportado abaixo foi
**reproduzido de forma independente** rodando o código real do repositório (pytest ao vivo,
`motores.rim` chamado diretamente, `git blame` recomputado manualmente, `LIMIAR_JACKKNIFE_PP`
recalculado do zero). Onde a reprodução bateu byte-a-byte com o que o SUMMARY alegava, isso está
registrado como evidência; nenhum truth foi marcado VERIFIED só porque o SUMMARY disse que passou.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidência |
|---|-------|--------|-----------|
| 1 | VAL-01: o motor RIM reproduz o caso do livro por EXECUÇÃO (ITUB4, Ke=0,1248 → V ∈ [35,39]) | ✓ VERIFIED | Chamada direta e independente de `motores.rim(**helpers_blindagem.insumos_itub4_livro())` → `valor_intrinseco = 38.688...` ∈ [35,39]. `pytest -k soberano_itub4` → 1 passed. O gap conhecido e documentado (app ao vivo com Ke da engine = R$24,38, não 37,22) é escopo deliberado do VAL-01 (RESEARCH.md D-04: "vive só no teste soberano closed-form"), coerente com o texto literal do REQUIREMENTS.md ("ITUB4 **com os inputs do Cap.17**"). |
| 2 | Hold-out rodou UMA vez contra âncoras pré-cravadas; D-09 prova por `git log`/`git blame` que `fair_value` (Commit 1) foi commitado ANTES de `v_modelo` (Commit 2); o teste de ordem RODA (não skipa) e passa | ✓ VERIFIED | `git log --oneline -- tests/fixtures/holdout_v24.yaml` mostra 2 commits distintos (`a5899b0` antes, `37c0b3b` depois), sem squash. Reproduzi o `git blame --line-porcelain` manualmente (script awk independente do teste): `max(author-time fair_value*) = 1784559251 < min(author-time v_modelo) = 1784565219` — bate exatamente com o SUMMARY. Repo NÃO é shallow (`git rev-parse --is-shallow-repository` = false) → o teste RODA de verdade: `pytest -k ordem_por_git` → 1 passed (não skipped). |
| 3 | O jackknife (`test_nenhum_ticker_e_load_bearing`) está ACORDADO (não skipped) e passa em termos honestos; `LIMIAR_JACKKNIFE_PP(n)` é derivado de um null neutro (Monte-Carlo seed-fixo), nunca dos dados reais | ✓ VERIFIED | `pytest -k nenhum_ticker_e_load_bearing` → 1 passed (era skipped antes da Fase 14). Recalculei do zero (script Python independente): n=34, `desvio_norm=0.05788`, `LIMIAR(34)=0.16405`, `mediana=0.6494` — os TRÊS números batem exatamente com o SUMMARY 14-04. Inspecionei o corpo de `LIMIAR_JACKKNIFE_PP`: usa `random.Random(20260720)` (seed literal) sobre um null lognormal `exp(N(0,0.35))`, `M=10_000`, percentil 95 — nenhuma referência a `v_modelo`/`fair_value`/fixture no corpo da função (grep limpo). |
| 4 | Orçamento de 3 graus de liberdade intacto: nenhum knob de valuation tocado durante a fase | ✓ VERIFIED | `git diff <início-da-fase 6fa8bed> HEAD -- config.yaml calibracao.lock.yaml` = **vazio** (0 linhas). Reproduzido diretamente, não só citado do SUMMARY. |
| 5 | `excecao_nota` está morto na árvore viva (VAL-06): nenhuma regra de exceção pode salvar um ticker | ✓ VERIFIED | `grep -rn excecao_nota src/ tests/ scripts/` retorna só 6 ocorrências, TODAS em `tests/test_holdout_cesta.py`/`classificacao.yaml` como **guarda que PROÍBE o símbolo** (`assert all("excecao_nota" not in e ...)` + docstring/comentário de enforcement) — zero uso vivo. `src/analista/backtest.py` e `scripts/backtest_bancos.py`: 0 ocorrências. |
| 6 | VAL-07 (não fazer backtest temporal) registrado como ADR durável e auditável, com âncora no código | ✓ VERIFIED | `.planning/decisions/VAL-07-backtest-temporal.md` existe com as 4 seções (Contexto/Decisão/Justificativa/Consequência), menciona "point-in-time" e "vazamento de futuro". `grep VAL-07 src/analista/backtest.py` retorna o comentário-âncora nas linhas 48-52. |
| 7 | Suíte verde conforme o contrato do CLAUDE.md: 0 failed, `golden_nivel` deselecionado por padrão | ✓ VERIFIED | `pytest -p no:cacheprovider -q` → **473 passed, 18 deselected, 0 failed** (rodado ao vivo, não copiado do SUMMARY). `pytest -m golden_nivel` → 18 passed, 0 CLASSIFICACAO ORFA. Coleta completa (`pytest -m ""`) → 490 passed, 1 skipped — o único skip restante é `test_blindagem_selecao.py` (skip estrutural sobre execução parcial, não relacionado a esta fase; pré-existente). |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/test_soberano_itub4.py` | Teste closed-form VAL-01 | ✓ VERIFIED | Existe, roda, `grep -c ITUB4` == 0 (literal só no helper), `grep -c "37"` == 0 (assere região, não ponto) |
| `tests/helpers_blindagem.py::insumos_itub4_livro` | Helper com insumos do Cap.17, fora de `test_` | ✓ VERIFIED | Presente; usado com sucesso na reprodução independente (V=38,69) |
| `.planning/decisions/VAL-07-backtest-temporal.md` | ADR não-fazer-backtest-temporal | ✓ VERIFIED | 4 seções presentes, termos técnicos exigidos presentes |
| `tests/helpers_blindagem.py::LIMIAR_JACKKNIFE_PP` | Função de n derivada de null neutro | ✓ VERIFIED | Determinística (seed literal), monótona, grep-clean de `v_modelo`/fixture |
| `tests/test_blindagem_meta.py::test_limiar_jackknife_mede_o_que_promete` | Teste das duas direções (saudável/ponte) | ✓ VERIFIED | `pytest -k limiar_jackknife` → passed |
| `scripts/montar_cesta_holdout.py` | Montador determinístico da cesta | ✓ VERIFIED | Existe; replica `eh_concessionaria` (build.py:168); produz 38 tickers, 5 estratos, 10 difíceis, CRESCIMENTO=4 marcado `cota_incompleta` |
| `tests/fixtures/holdout_v24.yaml` | Fixture Commit1(fair_value)+Commit2(v_modelo) | ✓ VERIFIED | 38 entradas; AZUL4 sem `fair_value` (D-03); 34 com `v_modelo`; TIMS3/CSAN3/BRKM5/AZUL4 sem `v_modelo` (degradação never-raise) |
| `tests/test_holdout_cesta.py` | Composição da cesta (VAL-02) | ✓ VERIFIED | `pytest -k holdout_estratificado` → passed |
| `tests/test_holdout_ordem_git.py` | Prova de ordem por git blame (VAL-03) | ✓ VERIFIED | `pytest -k ordem_por_git` → passed; RODA de verdade (repo não é shallow) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `test_soberano_itub4.py` | `src/analista/core/motores.py::rim` | chamada closed-form ke=0.1248 | ✓ WIRED | Reproduzido diretamente: `motores.rim(**insumos)` retorna `ResultadoRIM` real, não mock |
| `src/analista/backtest.py` | `.planning/decisions/VAL-07-backtest-temporal.md` | comentário-âncora | ✓ WIRED | `grep VAL-07 backtest.py` aponta para o ADR |
| `test_blindagem_meta.py` | `helpers_blindagem.py::LIMIAR_JACKKNIFE_PP` | `LIMIAR_JACKKNIFE_PP(len(razoes))` | ✓ WIRED | Call-site convertido de constante para chamada de função, verificado no código-fonte |
| `montar_cesta_holdout.py` | `src/analista/core/arquetipo.py::classificar` | estratificação | ✓ WIRED | Estratos medidos batem com o esperado (ciclica=13, concessao_finita=8, financeira=7, pagadora_madura=6, crescimento=4) |
| `holdout_v24.yaml (v_modelo)` | `src/analista/report/report.py::analisar_acao` | `intrinseco_motor` | ✓ WIRED | 34/38 tickers com `v_modelo` numérico plausível (mediana pooled V/FairValue = 0,649, recomputada de forma independente) |
| `test_holdout_ordem_git.py` | `tests/fixtures/holdout_v24.yaml` | `git blame --line-porcelain` | ✓ WIRED | Reproduzido com script `awk` independente do teste; mesmo veredito |

### Data-Flow Trace (Nível 4)

| Artifact | Variável de dado | Fonte | Dado real? | Status |
|----------|-------------------|-------|------------|--------|
| `test_nenhum_ticker_e_load_bearing` | `razoes` (v_modelo/fair_value) | leitura ao vivo de `holdout_v24.yaml` (34 entradas reais, geradas por `report.analisar_acao`/lentes Graham+Bazin) | Sim | ✓ FLOWING |
| `LIMIAR_JACKKNIFE_PP(n)` | `estatisticos` (simulação Monte-Carlo) | null lognormal sintético, seed 20260720 — **nunca** lê `v_modelo`/`fair_value` | N/A (por desenho) | ✓ FLOWING (fonte é o null pré-registrado, não dado real — é exatamente a garantia anti-overfit) |
| `test_holdout_ordem_por_git` | `author-time` por linha | `git blame` sobre o arquivo versionado real (não mock) | Sim | ✓ FLOWING |

### Requirements Coverage

| Requirement | Plano de origem | Descrição | Status | Evidência |
|-------------|-----------------|-----------|--------|-----------|
| VAL-01 | 14-01 | Caso do livro passa (ITUB4 Cap.17 → V∈[35,39]) | ✓ SATISFIED | `pytest -k soberano_itub4` + reprodução direta (V=38,69) |
| VAL-02 | 14-03 | Cesta estratificada ≥6/arquétipo + 10 difíceis | ✓ SATISFIED | Composição medida diretamente do fixture: 13/8/7/6/4, 10 difíceis, CRESCIMENTO marcado |
| VAL-03 | 14-03, 14-04 | Fair values commitados ANTES do modelo; git prova ordem | ✓ SATISFIED | Ordem reproduzida por `git blame` independente; 2 commits distintos no `git log` |
| VAL-04 | 14-04 | Hold-out roda uma única vez; falha = re-arquiteta, não recalibra | ✓ SATISFIED | `git diff config.yaml calibracao.lock.yaml` vazio; SUMMARY 14-04 documenta a mediana (0,65) como alerta, não como alvo perseguido |
| VAL-05 | 14-02, 14-03, 14-04 | Métrica é V/FairValue, nunca V/preço; LIMIAR derivado de null | ✓ SATISFIED | `LIMIAR_JACKKNIFE_PP` grep-clean de dado real; call-site usa razão V/FairValue, não preço |
| VAL-06 | 14-01 | Nenhuma exceção pode salvar ticker | ✓ SATISFIED | `excecao_nota` morto na árvore viva (grep == 0 fora de guardas/testes) |
| VAL-07 | 14-01 | Decisão sobre backtest temporal registrada | ✓ SATISFIED | ADR + âncora no código |

Nenhum requisito órfão: os 7 IDs (VAL-01..07) declarados em REQUIREMENTS.md aparecem todos no campo
`requirements:` de algum PLAN da fase (14-01: VAL-01/06/07; 14-02: VAL-05; 14-03: VAL-02/03/05;
14-04: VAL-03/04/05).

### Anti-Patterns Found

Nenhum bloqueador. Busquei `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` nos 12 arquivos tocados pela fase;
os únicos hits são falsos-positivos textuais (substring "TODO" dentro da palavra portuguesa "todo" —
ex. `montar_cesta_holdout.py:21` "usa TODOS e MARCA"). Nenhum marcador de dívida real.

O **code review da fase** (`14-REVIEW.md`, 2026-07-20) já havia sido feito por um agente separado e
levantou 0 críticos / 5 warnings / 2 infos. Reproduzi/avaliei cada warning à luz do objetivo da fase:

| # | Achado do review | Avaliação nesta verificação |
|---|---|---|
| WR-01 | A prova de ordem por `git blame` faz `skip` (não `fail`) em clone shallow/CI sem histórico completo — um fixture adulterado (squash) passaria despercebido num CI padrão (`fetch-depth: 1`) | **Confirmado como risco residual real e não-blocker no estado atual.** Este repositório NÃO é shallow (verificado: `git rev-parse --is-shallow-repository` = false) e não há pipeline de CI configurado (`.github/workflows` inexistente) — logo, no ambiente real de uso deste projeto, o teste RODA e prova a ordem de verdade (verificado independentemente). O risco é sobre uma automação futura ainda não construída. Marcado como WARNING, não como gap da fase — mas é o tipo de dívida que deveria ser fechada antes de qualquer CI ser criado (o próprio review já sugere o fix: falhar, não skipar, quando `CI=true`). |
| WR-02 | `montar_cesta_holdout.py` grava `date.today()` no fixture, contradizendo "determinístico"; um re-run acidental depois do Commit 2 reescreveria o arquivo inteiro e apagaria a prova de ordem | **Warning legítimo, não-blocker.** Não afeta o estado JÁ commitado (a prova de ordem foi reproduzida e bate); é um risco operacional para uma reexecução futura do montador, não uma falha do que foi entregue. |
| WR-03 | Classes de ações duplicadas (PETR3/4, ITUB3/4, BBDC3/4) com `fair_value`/`v_modelo` idênticos reduzem o poder do leave-one-out do jackknife | **Warning legítimo, não-blocker.** O próprio review verificou que deduplicar por emissor não muda o veredito atual (margem cresce). É uma limitação de poder estatístico documentável, não uma falha do PASS medido hoje. |
| WR-04 / WR-05 / IN-01 / IN-02 | Qualidade de código (file handles sem `with`, flag argparse sempre-True, filtro de truthiness, guarda `or 9e9`) | Não tocam a honestidade da validação; qualidade menor, sem impacto no veredito do hold-out. |

Nenhum destes 5 warnings falsifica qualquer um dos 7 truths verificados acima — todos foram
avaliados pelo próprio reviewer como não-bloqueadores, e a reverificação independente concorda.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Motor RIM reproduz o caso do livro | `motores.rim(**insumos_itub4_livro())` chamado ao vivo (script Python isolado) | `valor_intrinseco = 38.688...` | ✓ PASS |
| LIMIAR_JACKKNIFE_PP determinístico e recomputável | Recalculado do zero em processo Python separado | `LIMIAR(34) = 0.16405` (bate com SUMMARY) | ✓ PASS |
| Ordem git fair_value < v_modelo | `git blame --line-porcelain` + parser awk independente do teste | `max_fv=1784559251 < min_vm=1784565219` | ✓ PASS |
| Orçamento de 3 graus intacto na fase inteira | `git diff 6fa8bed HEAD -- config.yaml calibracao.lock.yaml` | saída vazia | ✓ PASS |
| Suíte default 0 failed | `pytest -p no:cacheprovider -q` | 473 passed, 18 deselected, 0 failed | ✓ PASS |
| Coleta sem CLASSIFICACAO ORFA | `pytest --collect-only -m ""` | 491 tests coletados, sem erro | ✓ PASS |

### Probe Execution

Não aplicável — esta fase não declara probes em `scripts/*/tests/probe-*.sh` nem os PLANs/SUMMARYs
mencionam esse mecanismo. Os "probes" reais da fase são os próprios testes pytest e as verificações
por execução direta acima, todos rodados e reproduzidos nesta verificação.

### Human Verification Required

Nenhum item. Esta fase é inteiramente backend/estatística/testes — sem componente visual, fluxo de
usuário ou serviço externo que exija checagem humana. O único ponto que mereceria uma decisão humana
(WR-01, o "fail-open" da prova de ordem em CI shallow) é uma decisão de **arquitetura de CI futura**,
não uma verificação que dependa de julgamento humano sobre o estado atual — o mecanismo, no ambiente
real deste projeto hoje, funciona e foi comprovado por execução independente.

### Gaps Summary

Nenhum gap. As 7 truths do objetivo da fase foram verificadas por execução independente (não por
citação do SUMMARY): o caso do livro passa por injeção do Ke do livro (V=38,69∈[35,39]); o hold-out
rodou uma única vez com a ordem fair_value-antes-de-v_modelo provada por `git blame` reproduzido
manualmente; o jackknife acordou, roda contra dado real do fixture, e usa um LIMIAR derivado
exclusivamente de um null Monte-Carlo pré-registrado (nunca dos dados reais); o orçamento de 3 graus
de liberdade ficou intacto durante toda a fase (diff vazio de `config.yaml`+`calibracao.lock.yaml`
do início ao fim das 4 waves); `excecao_nota` está morto na árvore viva; VAL-07 está registrado como
ADR durável e ancorado no código; e a suíte está verde no contrato exato do CLAUDE.md (0 failed,
`golden_nivel` deselecionado, sem CLASSIFICACAO ORFA). Os 5 warnings do code-review (14-REVIEW.md)
são reais mas não invalidam nenhuma das 7 truths — todos foram reavaliados nesta verificação e
concordo com a classificação de não-bloqueador dada pelo reviewer.

---

_Verificado: 2026-07-20T17:10:00Z_
_Verificador: Claude (gsd-verifier)_
