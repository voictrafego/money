---
phase: 07-blindagem-processual-blind
plan: 05
subsystem: test-harness
tags: [orcamento-de-knobs, graus-de-liberdade, config, canario, blind-06, claude-md]
requires:
  - "07-01: helpers_blindagem (tickers_conhecidos), classificacao.yaml, completude na coleta"
  - "07-02: carregar_config_producao() / cfg_e_empresas_do_snapshot(); o intertravamento BLIND-03 x BLIND-06"
  - "07-03: o meta-teste AST (o canario NAO pode ser detectado como golden — ver Desvio 1)"
  - "07-04: o hook do co-change; o lock na RAIZ e' o caminho SANCIONADO"
provides:
  - "calibracao.lock.yaml (raiz) — o orcamento: escopo declarado (30 folhas), 3 graus de liberdade, 27 congelados, 1 user_control"
  - "tests/test_blindagem_orcamento.py — 4 testes (particao, o dente, a regra do ticker, o CANARIO)"
  - "helpers_blindagem: carregar_lock(), folhas_do_escopo(), valor_em(), comentarios_com_ticker()"
  - "config.yaml sem NENHUM ticker nas justificativas de knob de valuation"
  - "CLAUDE.md: 'suite verde' definida pela regra do v2.4 (a regra velha esta REVOGADA)"
affects: [tests/, config.yaml, CLAUDE.md]
tech-stack:
  added: []
  patterns:
    - "orcamento de knobs como PARTICAO verificavel (folhas do escopo == graus | congelados), nao como contagem"
    - "canario sobre a CESTA, nunca sobre um ticker: monotonico na direcao da cura"
key-files:
  created:
    - calibracao.lock.yaml
    - tests/test_blindagem_orcamento.py
  modified:
    - config.yaml
    - tests/helpers_blindagem.py
    - tests/classificacao.yaml
    - CLAUDE.md
decisions:
  - "O canario e' sobre a CESTA (max |dV/V|), nao sobre o ITUB4 como o plano pedia: MEDIDO antes de escrever o assert, dobrar o erp_local move o ITUB4 em 0,00% (o ke_teto satura). O canario literal do plano nasceria VERMELHO, e a 'correcao' obvia seria afrouxar o limiar."
  - "O criterio de aceite `grep -c '0.045' lock -> 0` e' insatisfazivel: erp_banco e excesso_sustentavel VALEM 0.045 hoje e o lock registra as 30 folhas. O espirito (o grau ERP nao pode valer 0.045, que e' o ALVO do KE-02) foi honrado: graus_de_liberdade.ERP.valor == 0.06."
  - "A Task 2 virou DOIS commits (config / testes), nao um com o trailer Knob-Change-Justification: nenhum knob mudou de valor, entao declarar uma justificativa de knob seria mentir no git log para sempre."
metrics:
  duration: ~45min
  completed: 2026-07-13
  tasks: 3
  commits: 4
---

# Fase 7 Plano 05: BLIND-06 — o orcamento de knobs — Summary

O sistema passa a ter **exatamente 3 graus de liberdade DECLARADOS** (`ERP`, `n_fade`, `PIB_real`)
sobre uma superficie de valuation **declarada** (30 folhas), mexer em qualquer knob deixou de ser
invisivel, o `config.yaml` nao instrui mais ninguem a calibrar contra um ticker — e o **canario**
prova que a suite nova **consegue reprovar**.

**ESTE PLANO NAO MOVEU NENHUM NUMERO.** O `config.yaml` esta **semanticamente identico ao inicio da
fase** (so' comentarios mudaram) — prova abaixo.

## O orcamento, medido

| Metrica | Medido | Plano dizia |
|---|---:|---|
| Folhas do `config.yaml` (total) | **110** | 110 ✅ |
| Folhas da superficie de valuation (`motores`+`capm`+`ddm`+`normalizacao`) | **30** | 30 ✅ |
| ...`motores` | **11** | 11 ✅ (o ROADMAP diz "~20" — mal-calibrado na origem) |
| **Graus de liberdade** | **3** | 3 ✅ |
| **Congelados** | **27** | 27 ✅ |
| `user_control` (D-04) | **1** (`veredito.margem_seguranca` = 0.15) | 1 ✅ |
| Particao (3 + 27 = 30, zero folha orfa, zero fantasma) | **EXATA** | — |
| Comentarios com ticker nos blocos de valuation | **10 → 0** | 10 ✅ |

Os 3 graus registram o valor de **HOJE**, nao o alvo: `ERP` = `capm.erp_local` **0.06** (nao 0.045,
que e' o alvo do KE-02); `PIB_real` = **`ddm.g_estavel`** (nao `ddm.pib_real`, que **nao existe**).

## O PORTAO DA FASE — as 4 verificacoes

| # | Comando | Saida |
|---|---|---|
| **1** | `pytest -q -rxXs` | **`420 passed, 1 skipped, 38 deselected, 2 xfailed`** — 0 failed, 0 errors, **0 XPASS** |
| **2** | `pytest -q -m golden_nivel` | **`38 passed, 423 deselected`** — os quarentenados **rodam sob demanda** |
| **3** | `pytest -q -m "" --collect-only` | **`461 tests collected`** — nada foi perdido, so' deselecionado |
| **4** | `git config --get core.hooksPath` | **`.githooks`** |

**Contabilidade:** `420 + 38 + 1 + 2 = 461 = 448 (base) + 13 (os testes novos da fase: 3+3+3+4)`.
Os **2 xfailed** sao exatamente as duas doencas (BLIND-02b → Fase 12; BLIND-03 → Fase 10). O
**1 skipped** e' o veredito do jackknife (Fase 14 / VAL-02).

## O CANARIO DO LOCK — mexer num knob deixa a suite VERMELHA

```
# n_fade: 10 -> 9 no config.yaml
$ pytest -q -k knobs_batem
E  AssertionError: knob(s) alterado(s) sem atualizar o `calibracao.lock.yaml`:
E      `motores.rim.n_fade`: lock=10 -> config=9
E    Toda mudanca de knob tem que aparecer no MESMO diff — e' o que a torna revisavel.
1 failed, 459 deselected in 0.69s

# revertido:
1 passed, 459 deselected in 0.66s
```

Vermelho → verde. **A mudanca de knob deixou de ser invisivel.**

## O HOOK DO BLIND-05 ME BARROU DE VERDADE (nao num teste sintetico)

Ao tentar commitar `config.yaml` + `tests/*` juntos na Task 2:

```
BLOQUEADO (BLIND-05): config.yaml + teste/fixture no MESMO commit.
  E' a assinatura de 'calibrei o knob ate o golden passar' (post-mortem do v2.3).
  O caminho normal e' SEPARAR EM DOIS COMMITS: o knob de um lado, o teste do outro.
```

**Nao usei o trailer `Knob-Change-Justification`.** Nenhum knob mudou de valor — so' comentarios.
Declarar uma "justificativa de mudanca de knob" que nao existe deixaria uma mentira no `git log`
**para sempre**, e ensinaria o repo que o trailer e' o jeito de calar o hook. Segui o caminho que o
proprio hook prescreve: **dois commits**. A protecao do 07-04 funciona no fluxo real, nao so' no E2E.

## PROVA: nenhum numero movido na FASE INTEIRA

```
$ python -c "config.yaml de hoje == config.yaml de 2056839 (antes do 07-01), via yaml.safe_load"
config semanticamente identico ao inicio da fase: True

$ git diff --stat 2056839..HEAD -- src/ tests/test_motores.py tests/test_backtest_bancos.py tests/fixtures/
(vazio)
```

**Zero edicao em producao, nos testes existentes e nas fixtures. O `V` de nenhum ticker se moveu.**
O `config.yaml` mudou **so' em comentarios** (os dicts carregados sao iguais → o YAML ignora
comentarios → se os dicts batem, so' comentario mudou).

## As 10 linhas que instruiam o overfit — e o que ficou no lugar

| Antes (config.yaml) | Depois |
|---|---|
| `# Move ITUB4 ~R$2` (`ke_teto`) | `# ⚠ CLAMP QUE SATURA: o Ke PARA de reagir ao rf — e' a Doenca 3 (BLIND-02b). KE-04 (Fase 12): REMOVIDO, nao recalibrado.` |
| `# E a alavanca que destrava o ITUB4 do "evitar"` (`erp_banco`) | `# SEGUNDO ERP do sistema: o KE-02 unifica — dois premios de risco no mesmo modelo e' sintoma.` |
| `# golden ITUB4 (VPA~22...) ... a cesta (ITUB4/BBAS3/BBSE3/BBDC4)` (`n_fade`) | `# E' UM DOS 3 GRAUS DE LIBERDADE (calibracao.lock.yaml) — e e' ele que impoe o piso de -4,68% do BLIND-02(b).` |
| **`# NAO mexer nos knobs acima: mudariam o ITUB4`** | **LINHA DELETADA.** Era a instrucao escrita, no proprio repo, de cometer a Armadilha 3. |

As linhas **218-219** (bloco `arquetipo`, ranges ilustrativos de dispersao) ficaram **fora do
escopo** de proposito — sao uma escala empirica, nao uma justificativa de nivel.

## Desvios do plano

### 1. [Rule 1 - premissa do plano falsa] O canario sobre o ITUB4 nasceria VERMELHO — o `ke_teto` satura

- **Achado:** na Task 3, **medindo antes de escrever o assert** (a lição dos 4 planos anteriores).
- **O plano manda:** `sabotado["capm"]["erp_local"] *= 2` → `assert abs(V_sab/V_base - 1) > 0.05`
  **sobre o ITUB4**.
- **O que medi:**

  | Ticker | V base | V com ERP dobrado | Δ |
  |---|---:|---:|---:|
  | ITUB4 | 32,88 | 32,88 | **+0,00%** |
  | BBAS3 | 43,89 | 43,89 | **+0,00%** |
  | BBDC4 | 13,37 | 13,37 | **+0,00%** |
  | BBSE3 | 39,87 | 33,55 | **−15,85%** |

- **Causa (nao e' a engine morta — e' a Doenca 3):** o `ke_teto = 0,13` **clampa** o Ke do RIM. O
  `capm.erp_local` so' entra por `ke_live`, que **ja' esta acima do teto** → o clamp **engole o
  choque inteiro**. E' a **mesma saturacao** que o `test_invariancia_inflacao_engine_itub4`
  (BLIND-02b) denuncia, uma camada acima. A seguradora, que nao satura, reage.
- **Por que a "correcao obvia" seria o Pitfall 5:** um canario vermelho no primeiro commit convida a
  afrouxar o limiar ou a trocar o ticker ate passar — **exatamente** o que a fase inteira existe para
  impedir.
- **O que fiz:** o assert e' sobre a **CESTA** (`max |ΔV/V| > 5%`). Ele afirma a coisa certa (*"a
  engine reage ao custo de capital"*) e e' **MONOTONICO NA DIRECAO DA CURA**: quando o KE-04 (Fase
  12) remover o `ke_teto`, os 4 tickers passarao a reagir e o `max` so' **cresce** → o teste
  **continua verde no dia da cura**. Um alarme que nao precisa ser "consertado".
- **Bonus estrutural:** o corpo do canario **nao tem literal de ticker** (eles vem do snapshot) e
  **nao crava nivel em reais** (a afirmacao e' relativa) → o meta-teste do **BLIND-04a** nao o
  confunde com um golden. Escrever sobre o ITUB4 exigiria o literal `"ITUB4"` + a constante `0.05`
  chegando a um assert = **ofensor detectado**, e as unicas saidas seriam quarentena-lo (canario
  fantasma, fora do default) ou `xfail` (mas o canario **precisa** ficar verde). **O canario literal
  do plano era incompativel com o 07-03.**
- **Commit:** `a5f8357`

### 2. [Rule 1 - criterio de aceite insatisfazivel] `grep -c "0.045" calibracao.lock.yaml` → 0

O criterio da Task 1 exige **zero** ocorrencias de `0.045` no lock. Impossivel: `motores.rim.erp_banco`
**e** `motores.rim.excesso_sustentavel` **valem 0.045 hoje** e o lock registra **todas as 30 folhas**
com o valor de hoje (o proprio criterio seguinte exige `3 + 27 = 30`). Os dois criterios se
contradizem.

**O espirito e claro e foi honrado:** o `0.045` do esboco da pesquisa era o **ALVO** do KE-02 para o
`ERP` — copia-lo deixaria `test_knobs_batem_com_o_lock` vermelho na primeira escrita, e a "correcao"
obvia seria **editar o config.yaml**, ou seja, **MOVER UM NUMERO** (a armadilha que o proprio plano
nomeia como a mais perigosa). Verificado: `graus_de_liberdade.ERP.valor == 0.06` (o valor de hoje).
O `0.045` so' aparece em **`congelados`**, onde e' o valor **real**.

### 3. [Rule 3 - bloqueio] A Task 2 virou dois commits

O hook do BLIND-05 bloqueia `config.yaml` + `tests/test_*` no mesmo commit — e a Task 2 toca os dois.
Ver a secao do hook acima: escolhi **dois commits** em vez do trailer, porque **nenhum knob mudou de
valor**. E' o mecanismo do 07-04 funcionando exatamente como projetado.

## O intertravamento BLIND-03 x BLIND-06 — FECHADO

O handoff do 07-02 exigia: *"o teste de orcamento **precisa** deixar `normalizacao.anos_media` fora
dos graus de liberdade, senao a defesa (b) do Pitfall 5 nao existe."*

**Honrado.** `normalizacao.anos_media: 3` esta em **`congelados`**, com a razao escrita no lock:

> *PRIM-01, Fase 10. **NAO E' GRAU DE LIBERDADE — E' A TRAVA DO BLIND-03.** Mudar para 1 faria
> `test_normalizacao_nao_pune_crescimento` passar SEM CONSERTAR `normalizacao.py`. O teste de
> orcamento pega a alteracao porque `anos_media` NAO esta em `graus_de_liberdade`.*

A fuga do Pitfall 5 esta fechada **pelos dois lados**, e os dois nasceram na mesma fase.

## Handoffs duraveis para o marco

1. **Golden master dos 104 tickers** (PITFALLS P5.2 / RESEARCH Q3) — **fora do escopo da Fase 7**
   (nao e' requisito BLIND, e `out/` e' gitignored → **nao existe baseline hoje**). E'
   **pre-requisito das Fases 8/9**: sem baseline, *"os asserts viram verde ticker a ticker"* nao e'
   mensuravel. **Sinalizar ao planner do marco.**
2. **BLIND-02(b) vira verde na Fase 12, NAO na 11** (o `ke_teto` satura ate la'). A regra dura A
   (nao fundir 11 e 12) **continua valida** — ela e' sobre a **ordem do conserto**, nao sobre onde um
   teste fica verde. O canario deste plano **mede** essa saturacao: 3 de 4 bancos com Δ = 0,00%.
3. **`LIMIAR_JACKKNIFE_PP` esta `[ASSUMIDO]`** — fixar na **Fase 14 (VAL-02)** com a distribuicao
   real da cesta estratificada.
4. **`motores:` tem 11 chaves, nao ~20** — a regra dura C do ROADMAP esta mal-calibrada **na origem**.
   A meta ≤5 (ENG-10, Fase 13) continua sendo um corte real (**11 → 5**), mas a contagem de partida
   e' **11**. Nao "contar" uma delecao que nunca existiu.
5. **`core.hooksPath` e' estado LOCAL por clone** — todo clone novo nasce **sem** a protecao:
   `git config core.hooksPath .githooks`. O teste do 07-04 e' o unico que avisa.
6. **Fase 11 (GROW-01):** quando o `g_cap` derivado (7,28%) substituir o `ddm.g_estavel`,
   **ATUALIZE O `caminho` do grau `PIB_real` no lock, no mesmo commit.** Isso **nao e' afrouxar o
   orcamento — e' o orcamento sendo MANTIDO.** Esta escrito dentro do proprio lock.
7. **Fase 13 (ENG-06):** ao transformar a `veredito.margem_seguranca` em controle do usuario, ela sai
   de `user_control` do lock. Ela **nunca** vira grau de liberdade.

## Commits

| Hash | Task | Descricao |
|---|---|---|
| `1d62f0f` | 1 | `calibracao.lock.yaml` — escopo (30 folhas), 3 graus, 27 congelados, 1 user_control |
| `20fc41b` | 2a | `config.yaml`: os tickers saem das justificativas de knob (**so' comentarios**) |
| `5f08378` | 2b | os 3 testes do orcamento + helpers (`carregar_lock`, `folhas_do_escopo`, ...) |
| `a5f8357` | 3 | o **canario** (a suite CONSEGUE reprovar) + `CLAUDE.md` define "suite verde" |

## Self-Check: PASSED

- `calibracao.lock.yaml` — FOUND (raiz, nao `tests/`)
- `tests/test_blindagem_orcamento.py` — FOUND (4 testes, 240 linhas)
- `tests/helpers_blindagem.py` (`carregar_lock`, `folhas_do_escopo`, `comentarios_com_ticker`) — FOUND
- `CLAUDE.md` — FOUND (regra velha REVOGADA; `grep -c "devem continuar passando"` → **0**)
- commits `1d62f0f`, `20fc41b`, `5f08378`, `a5f8357` — FOUND
- `pytest -q -rxXs` → `420 passed, 1 skipped, 38 deselected, 2 xfailed` (0 failed, 0 errors, 0 XPASS)
- `pytest -q -k "orcamento_de_knobs or knobs_batem or justificativa or suite_reage"` → **4 passed**
- lock: `graus: 3` · `batem: True` · `congelados: 27` · particao **exata** (30 == 30)
- `config.yaml` semanticamente identico a `2056839` (inicio da fase) → **True**
- `git diff --stat 2056839..HEAD -- src/ tests/test_motores.py tests/test_backtest_bancos.py tests/fixtures/` → **vazio**
