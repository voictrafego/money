---
phase: 14-valida-o-honesta-val
plan: 04
subsystem: validação (Commit 2 do hold-out — v_modelo + prova de ordem + phase gate v2.4)
tags: [VAL-03, VAL-04, VAL-05, D-09, D-11, hold-out, jackknife, git-blame, phase-gate]
requires:
  - "tests/fixtures/holdout_v24.yaml (Commit 1, fair_value) — CONSUMIDO e ESTENDIDO (v_modelo)"
  - "LIMIAR_JACKKNIFE_PP(n) + desvio_jackknife_normalizado (Plano 02) — CONSUMIDOS"
  - "report.analisar_acao.intrinseco_motor (RIM único, Fase 13) — FONTE ÚNICA do v_modelo"
  - "test_soberano_itub4 (VAL-01, Plano 01) — CONSUMIDO como condição 1 do D-11"
provides:
  - "scripts/montar_cesta_holdout.py: modo --fill-v-modelo (inserção cirúrgica, sem re-tocar fair_value)"
  - "tests/fixtures/holdout_v24.yaml: Commit 2 do D-09 — v_modelo por ticker (34), fair_value intocado"
  - "tests/test_holdout_ordem_git.py: prova de ordem por git blame (author-time por linha)"
  - "test_nenhum_ticker_e_load_bearing ACORDADO: jackknife robusto sobre a cesta real (D-11)"
affects:
  - "test_holdout_estratificado_composicao: clausula de ausencia de v_modelo removida (ordem provada por git blame)"
tech-stack:
  added: []
  patterns:
    - "inserção cirúrgica por linha (linha NOVA ao fim do bloco, fair_value byte-a-byte intocado): 34 additions / 0 deletions no diff — pré-condição do git blame por linha (D-09)"
    - "prova de ordem por META-DATA do git (author-time por linha), nunca por grep de mensagem (falso positivo com commits 13-0x)"
    - "shallow-clone-safe: skip com instrução fetch-depth: 0, nunca falso-reprova sem história"
    - "mediana V/FairValue = DETECTOR de viés reportado, jamais alvo — PASS provado por execução (3 condições D-11), não por suíte verde"
key-files:
  created:
    - tests/test_holdout_ordem_git.py
  modified:
    - tests/fixtures/holdout_v24.yaml
    - scripts/montar_cesta_holdout.py
    - tests/test_holdout_cesta.py
    - tests/classificacao.yaml
decisions:
  - "v_modelo = report.analisar_acao(c,cfg).intrinseco_motor (V do RIM, fonte única); inserção cirúrgica (34 add / 0 del) prova por git blame que fair_value foi cravado antes"
  - "mediana V/FairValue pooled = 0,65 (RIM ~35% abaixo de Graham+Bazin): DETECTOR reportado como ALERTA, NUNCA alvo — nenhum knob tocado para aproximá-la de 1"
  - "composição (Plano 03): clausula 'sem v_modelo' removida (ordem agora provada por HISTORIA/git blame, nao por ausencia de conteúdo); clausula excecao_nota (VAL-06) intacta"
  - "PASS do hold-out provado por EXECUÇÃO (VAL-01 + jackknife robusto + zero excecao_nota viva), não só por pytest verde"
metrics:
  duration: ~30min
  tasks: 3
  files: 5
  completed: "2026-07-20"
---

# Phase 14 Plan 04: Commit 2 do hold-out — v_modelo, prova de ordem e o phase gate do v2.4 Summary

O marco v2.4 fecha **provado por execução, sem se enganar**. O **Commit 2** do D-09 gravou o
`v_modelo` (V do RIM) rodando o modelo **uma única vez** sobre a MESMA cesta cravada no Commit 1,
por **inserção cirúrgica** (34 linhas novas, `fair_value` byte-a-byte intocado). O `git blame` por
linha **prova** que os `fair_value` têm `author-time` anterior a todo `v_modelo` — a âncora foi
cravada ANTES do modelo, não olhando o resultado. O jackknife **acordou** e passou: **nenhum ticker
é load-bearing** (desvio 0,058 MADs ≤ LIMIAR 0,164). A mediana V/FairValue **pooled = 0,65** é um
**DETECTOR de viés reportado** (o RIM é ~35% mais conservador que Graham+Bazin), **jamais um alvo** —
**nenhum knob foi tocado** (orçamento intacto em 3 graus). O PASS do D-11 é provado por **execução ao
vivo dos 104**, não por suíte verde.

## What Was Built

### Task 1 — Commit 2: v_modelo rodado sobre a cesta cravada (commit `37c0b3b`)
- **`scripts/montar_cesta_holdout.py` modo `--fill-v-modelo`** (antes um stub que recusava): roda
  `report.analisar_acao(c, cfg)` sobre os 104 (mesmo cfg offline, β setorial carimbado, D-06) e
  usa `a.intrinseco_motor` (V do RIM, **fonte única — a fórmula NÃO é reimplementada**). Never-raise:
  exceção ou `intrinseco_motor` None/≤0 → ticker sem `v_modelo`.
- **Inserção CIRÚRGICA (D-09):** `_inserir_v_modelo` insere `v_modelo` como **linha NOVA ao fim de
  cada bloco de ticker**, sem re-tocar nenhuma linha do Commit 1. Verificado: `git diff` do fixture =
  **34 additions, 0 deletions**; removendo as linhas `v_modelo` do resultado, o conteúdo é
  **byte-idêntico** ao Commit 1. Se o arquivo fosse reescrito inteiro, todas as linhas ganhariam o
  timestamp do Commit 2 e a prova de ordem evaporaria.
- **34 `v_modelo` preenchidos** (dos 38 tickers). Degradaram (sem V, never-raise): **TIMS3, CSAN3,
  BRKM5** (sem dado de mercado → sem Ke → intrínseco None) e **AZUL4** (D-03, já sem `fair_value`) —
  caem fora do jackknife automaticamente.
- **`test_nenhum_ticker_e_load_bearing` ACORDOU** (não mais `skipped`) e passa.

### Task 2 — Prova de ordem por git blame (commit `ba05828`)
- **`tests/test_holdout_ordem_git.py::test_holdout_ordem_por_git`** (`@pytest.mark.contrato`): roda
  `git blame --line-porcelain` via `subprocess`, extrai `author-time <epoch>` por linha, mapeia cada
  linha ao campo pela chave YAML, e assere **`max(author-time de fair_value*) < min(author-time de
  v_modelo)`**. Medido: `max_fv = 1784559251 < min_vm = 1784565219`. **NÃO usa grep de mensagem de
  commit** (`grep -c -- "--grep" == 0`) — falso positivo com os commits de trading `13-0x`. **Shallow
  clone** (`git rev-parse --is-shallow-repository`) ou blame indisponível → `skip` com instrução
  `fetch-depth: 0`, nunca falso-reprova. Docstring documenta: dois commits sem squash + `git push`
  (história congelada) é a proteção; rebase preserva `author-time`; squash/amend ou re-toque de
  `fair_value` quebra a prova (o teste falha, flagando adulteração).
- **`test_holdout_estratificado_composicao` (Plano 03):** a clausula de verdade 1 que asseria
  ausência de `v_modelo` foi **removida** — a ordem agora é provada por **HISTÓRIA** (git blame), não
  por ausência de conteúdo; depois do Commit 2 o `v_modelo` legitimamente existe. A clausula
  **`excecao_nota` (VAL-06) permaneceu intacta**. Entrada em `classificacao.yaml` no mesmo diff.

### Task 3 — Phase gate: PASS provado por EXECUÇÃO (D-11)
As **três condições do D-11**, verdes por execução ao vivo:
1. **VAL-01 (soberano):** `pytest -k soberano_itub4` → **1 passed** (ITUB4 com Ke do livro ∈ [35,39]).
2. **Jackknife robusto:** `pytest -k nenhum_ticker_e_load_bearing` → **1 passed** (desvio normalizado
   **0,0579 MADs ≤ LIMIAR 0,164** para n=34 — nenhum ticker load-bearing).
3. **Zero exceção viva:** `excecao_nota` em produção (`src/`) = **0** e no fixture = **0** (a
   lavanderia morreu no Plano 01). As 5 menções restantes vivem só em `tests/` como o **GUARD que
   PROÍBE o token** (o `assert all("excecao_nota" not in e ...)`) + prose — enforcement, não violação.

**Suíte default: 473 passed, 0 skipped, 18 deselected, 0 failed** (vs 14-03: 471 passed + 1 skipped →
o jackknife acordou como pass +1, e +1 do novo teste de ordem; 0 skipped agora). `-m golden_nivel`:
**18 passed, 0 CLASSIFICACAO ORFA**. **`git diff config.yaml calibracao.lock.yaml` VAZIO** —
orçamento intacto em 3 graus (ERP, n_fade, PIB_real). Nenhum knob tocado.

## Distribuição V/FairValue (D-07) — DETECTOR, nunca gate

Reportada por estrato + pooled, com `CONCESSAO_FINITA` isolado (não contamina o pooled):

| Estrato | n | Mediana V/FairValue |
|---------|---|---------------------|
| ciclica | 9 | 0,436 |
| concessao_finita (isolado) | 8 | 0,606 (IQR [0,523, 0,923]) |
| crescimento | 4 | 0,855 |
| financeira | 7 | 0,719 |
| pagadora_madura | 6 | 0,679 |
| **pooled (todos, 34)** | 34 | **0,649** (IQR [0,502, 0,988]) |
| pooled EX-concessao (26) | 26 | 0,664 (IQR [0,450, 1,002]) |

**Leitura (ALERTA escrito, nunca alvo):** a mediana ~0,65 diz que o RIM único é **sistematicamente
~35% mais conservador** que as lentes clássicas Graham+Bazin. Isso é **coerente e esperado** (o RIM
desconta excesso de retorno com fade + Ke local alto; Graham/Bazin são otimistas por construção) e é
um **detector de viés reportado** — **NÃO** um gate. **Nenhum knob foi tocado para aproximar a
mediana de 1** (isso seria calibrar contra a âncora = o espelho do mercado que VAL-05 condena, e o
overfit do v2.3 que esta fase existe para impedir). O jackknife robusto (nenhum ticker load-bearing)
é o gate; a mediana é só o termômetro.

**Degradação reportada (never-raise, nunca exclusão silenciosa):**
- **Sem `v_modelo`** (degradou no modelo, sem dado de mercado/Ke): TIMS3, CSAN3, BRKM5.
- **Sem `fair_value`** (D-03, nenhuma lente): AZUL4.
- Todos ficam **fora do jackknife automaticamente** (o teste só monta razão quando há AMBOS).

## Verification

- `pytest -k "soberano_itub4 or nenhum_ticker_e_load_bearing or ordem_por_git or holdout or blindagem"`: verde.
- **Suíte default: 473 passed, 0 skipped, 18 deselected, 0 failed**; sem CLASSIFICACAO ORFA.
- `git log --oneline -3 -- tests/fixtures/holdout_v24.yaml`: `37c0b3b` (Commit 2) e `a5899b0`
  (Commit 1) — **dois commits distintos, sem squash**.
- **Ordem por git blame:** `max(author-time fair_value*) = 1784559251 < min(author-time v_modelo) =
  1784565219` — VERDADEIRO.
- `git diff config.yaml calibracao.lock.yaml` **VAZIO**; `grep excecao_nota src/` = **0**.
- Fixture: `git diff` = **34 additions / 0 deletions** (fair_value byte-a-byte intocado).

## Deviations from Plan

**1. [Rule 3 - Transição de fase] `test_holdout_estratificado_composicao` reprovou ao nascer o v_modelo**
- **Found during:** Task 2 (o `pytest -k holdout` ficou vermelho após o Commit 2).
- **Issue:** a verdade 1 da composição (Plano 03) asseria `all("v_modelo" not in e ...)` — a **pureza
  do Commit 1**, uma DEPENDÊNCIA DE FASE (guarda válida enquanto só existia o Commit 1). O Commit 2
  deste plano preenche `v_modelo` LEGITIMAMENTE, disparando o assert.
- **Fix:** **removida apenas a clausula de ausência de `v_modelo`** — a ordem passa a ser provada por
  **HISTÓRIA** (`test_holdout_ordem_git`, git blame por linha), o mecanismo CORRETO e permanente, não
  por ausência de conteúdo (temporária). A clausula **`excecao_nota` (VAL-06) permaneceu intacta** —
  nada afrouxado. Mesma natureza da correção do skip do jackknife no Plano 03 (transição de fase, não
  afrouxamento de blindagem).
- **Files modified:** tests/test_holdout_cesta.py
- **Commit:** ba05828.

**2. [Rule 1 - Higiene] O token `--grep` vazou para o docstring do teste de ordem**
- **Found during:** verificação do critério de aceite (`grep -c -- "--grep" == 0`).
- **Issue:** o docstring explicava "NÃO usar `git log --grep`" citando o literal `--grep`, disparando
  o grep de aceite por falso-positivo textual.
- **Fix:** reescrito para "grep de mensagem de commit" mantendo o sentido; `grep -c -- "--grep" == 0`
  confirmado antes do commit.
- **Files modified:** tests/test_holdout_ordem_git.py
- **Commit:** ba05828.

Fora isso, o plano foi executado exatamente como escrito. **O hold-out PASSOU honestamente** — nenhum
knob foi tocado para forçar o verde (VAL-04); a mediana longe de 1 foi reportada como alerta, não
perseguida.

## Known Stubs

Nenhum. O `--fill-v-modelo` (antes um stub que recusava) foi implementado neste plano. O fixture está
completo (v_modelo rodado sobre a cesta real); AZUL4 sem `fair_value`/`v_modelo` é **degradação D-03
reportada**, não stub.

## Threat Flags

Nenhum. Superfície = leitura de YAML congelado (`safe_load`) + `subprocess` de `git blame`
(read-only, sobre arquivo versionado, sem input de usuário/rede). As mitigações do threat register
(T-14-03 ordem por linha sem squash; T-14-02b fronteira vazia + mediana como detector; T-14-05c
LIMIAR pré-commitado na Wave 2; T-14-11 PASS por execução) estão TODAS implementadas e provadas.

## Self-Check: PASSED
- `tests/test_holdout_ordem_git.py` — FOUND
- `tests/fixtures/holdout_v24.yaml` (34 v_modelo, fair_value intocado) — FOUND
- `scripts/montar_cesta_holdout.py` (--fill-v-modelo) — FOUND
- Commit `37c0b3b` (Commit 2 — v_modelo) — FOUND
- Commit `ba05828` (prova de ordem por git blame) — FOUND
