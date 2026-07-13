---
phase: 07-blindagem-processual-blind
plan: 04
subsystem: git-hooks
tags: [git, hook, commit-msg, hooksPath, overfit, blind-05]
requires:
  - "07-01: helpers_blindagem.tickers_conhecidos() (os 104 tickers reais) + completude na coleta"
  - "07-03: precedente de que o backstop precisa MORDER (canario vermelho->verde)"
provides:
  - ".githooks/commit-msg — bloqueio do co-change config.yaml + golden/fixture (BLIND-05)"
  - "core.hooksPath = .githooks (estado LOCAL — cada clone precisa reinstalar)"
  - "tests/test_blindagem_hook.py — 3 testes de backstop (instalado / versionado / historico limpo)"
  - "trailer `Knob-Change-Justification:` — a escapatoria auditavel, no git log para sempre"
  - "BASE_V24 = 955e73d — o SHA de onde a varredura do historico comeca"
affects: [tests/, .githooks/]
tech-stack:
  added: []
  patterns:
    - "hook VERSIONADO via core.hooksPath (zero dep; .git/hooks nao e' versionado)"
    - "regra semantica executavel: regex como PRIMEIRO FILTRO, validacao contra ticker_map.json"
key-files:
  created:
    - .githooks/commit-msg
    - tests/test_blindagem_hook.py
  modified:
    - tests/classificacao.yaml
decisions:
  - "Um hook so', `commit-msg` (nao `pre-commit`): so' ele recebe o arquivo da mensagem em $1, e ele TAMBEM le o indice via `git diff --cached`. O nome 'pre-commit' do BLIND-05 e' descritivo, nao normativo."
  - "A escapatoria e' OBRIGATORIA e BARULHENTA: 2 dos 5 co-changes historicos sao legitimos (primitiva + knob + teste nascendo juntos). Sem escapatoria o hook seria contornado por --no-verify em silencio; com o trailer, a excecao fica no git log para sempre."
  - "A varredura do backstop comeca em BASE_V24 (955e73d), nao na raiz: os 5 co-changes historicos sao passado JA' AUDITADO pela pesquisa. Um teste que nao pode ficar verde e' apagado na primeira sexta-feira — seria o Pitfall 5 pela porta dos fundos."
  - "`calibracao.lock.yaml` (07-05) fica na RAIZ, fora de tests/: `config.yaml` + lock no mesmo commit e' o caminho SANCIONADO e NAO pode cair no bloqueio. Escrito como nota dentro do proprio hook."
metrics:
  duration: ~25min
  completed: 2026-07-13
  tasks: 2
  commits: 2
---

# Fase 7 Plano 04: BLIND-05 — o co-change knob+golden, bloqueado no ato do commit — Summary

A assinatura exata do overfit do v2.3 (`config.yaml` + um golden no MESMO commit) agora **e'
rejeitada pelo git**, com escapatoria **auditavel** (trailer no `git log`) e **backstop em teste**
contra o `--no-verify` — porque este repo **nao tem CI**.

**ESTE PLANO NAO MOVEU NENHUM NUMERO.** `config.yaml` bit-identico: sha `441ae99` antes **e**
depois das 3 provas E2E (`git hash-object config.yaml`).

## As 3 provas E2E do hook (rodadas de verdade, em branch descartavel)

| # | Stage | Mensagem | Resultado |
|---|---|---|---|
| **(a)** | `config.yaml` + `tests/test_ddm.py` | `teste: mexe no knob e no golden juntos` | 🔴 **BLOQUEADO** (`exit=1`) — *"E' a assinatura de 'calibrei o knob ate o golden passar' (post-mortem do v2.3)"* |
| **(b)** | idem | `Knob-Change-Justification: ITUB4 estava baixo` | 🔴 **BLOQUEADO** (`exit=1`) — *"a justificativa do knob menciona um TICKER (ITUB4)"*, citando `config.yaml:238` (*"Move ITUB4 ~R$2"*) |
| **(b2)** | idem | `Knob-Change-Justification: o MACD12 do bloco de sinais tecnicos ganha primitiva propria` | 🟢 **PASSA** (`exit=0`) — o falso positivo do Pitfall 7 **nao** bloqueia |
| **(c)** | idem | `Knob-Change-Justification: primitiva nova de normalizacao nasce com knob e teste` | 🟢 **PASSA** (`exit=0`) — o caso legitimo (2 dos 5 co-changes historicos) |

**(b2) nao estava no plano e e' a prova que faltava:** a regex nua `[A-Z]{4}[0-9]{1,2}` casa
`MACD12` — que existe **dentro do proprio `config.yaml`**. O hook usa a regex **so' como primeiro
filtro** e valida o candidato contra `data/ticker_map.json` (`grep -qF "\"$cand\""`). Sem isso, o
bloqueio do BLIND-05 mentiria e seria desligado na primeira semana.

Limpeza: branch `tmp-blind05-e2e` deletada (`was c974b47`), `git status --porcelain config.yaml tests/`
→ **vazio**.

## A prova de que o backstop MORDE

```
$ git config --unset core.hooksPath
$ pytest -q -k hook_do_blind05_esta_instalado
E  AssertionError: core.hooksPath = '' (esperado '.githooks') -> o hook do BLIND-05 esta INATIVO
E        e o co-change knob+golden passa sem bloqueio nenhum.
E        Rode:  git config core.hooksPath .githooks
1 failed, 456 deselected in 0.77s

$ git config core.hooksPath .githooks
$ pytest -q -k hook_do_blind05_esta_instalado
1 passed, 456 deselected in 0.66s
```

Vermelho → verde. **A protecao nao consegue sumir em silencio.**

## Estado da suite

```
.venv/bin/python -m pytest -q -rs
  416 passed, 1 skipped, 38 deselected, 2 xfailed in 3,87s   # 0 failed, 0 errors, 0 XPASS
```

413 → **416** (+3, os do backstop). O `1 skipped` continua sendo o veredito do jackknife (Fase 14);
os `2 xfailed` continuam sendo as duas doencas do 07-02.

`git diff --stat -- src/ config.yaml` → **vazio**.

## NOTA DURAVEL — `core.hooksPath` e' estado LOCAL, por clone

Este e' o **unico** item da Fase 7 que **nao vive num arquivo versionado**. Tudo o mais (quarentena,
meta-testes, orcamento de knobs) esta em `git`. `core.hooksPath` mora no `.git/config`, que **nunca**
e' clonado.

> **Todo clone novo do repo nasce SEM a protecao do BLIND-05.**
> `git config core.hooksPath .githooks`

O `test_hook_do_blind05_esta_instalado` e' a **unica** coisa que transforma isso num erro ruidoso em
vez de uma protecao fantasma (RESEARCH § Pitfall 6). E' de proposito que ele nao "conserta sozinho":
um teste que se auto-repara ensina o repo a ignorar o alarme.

## `BASE_V24` — de onde a varredura comeca, e por que nao da raiz

```python
BASE_V24 = "955e73d97b06bd4df77bd17efa9cdb7d64af2c07"
# docs: create milestone v2.4 roadmap (8 phases, 52 reqs)
```

A pesquisa varreu os **676 commits** e achou **5 co-changes** de `config.yaml` + `tests/`:
`5cd3b61` (**o overfit do v2.3**), `d2f2212` e `a26fc0c` (**legitimos**), `be568cb` (fronteirico),
`0784d77` (repo inicial). **Passado auditado.** Fazer o teste falhar sobre eles o tornaria
impossivel de ficar verde — e um teste que nao pode ficar verde e' apagado, nao consertado. O
contrato e' **do v2.4 adiante**. Se o repo aparecer sem esse historico (clone shallow), o teste
**SKIPa com razao explicita** — nunca um `assert True` silencioso.

## Desvios do plano

### 1. [Rule 2 - funcionalidade critica ausente] A prova (b2): o falso positivo `MACD12`

O plano exige a validacao contra `ticker_map.json` (e ela esta la'), mas as provas E2E pedidas eram
so' (a)/(b)/(c) — **nenhuma delas exercita o falso positivo**. Um hook que bloqueia `MACD12` seria
desinstalado por irritacao antes de barrar o primeiro overfit de verdade. Acrescentei **(b2)** como
prova executada: passa. A defesa do Pitfall 7 esta **medida**, nao so' escrita.

Nenhum outro desvio. O script do RESEARCH § BLIND-05 foi usado como base (nao reinventado), com tres
endurecimentos: `set -u`, `RAIZ` via `git rev-parse --show-toplevel` (o hook nao depende do cwd) e
todas as mensagens em `stderr`.

## Seguranca (o threat register do plano)

| Threat | Estado |
|---|---|
| **T-07-07** — `sh` sobre texto livre (a mensagem de commit) | `grep -c eval .githooks/commit-msg` → **0**. A mensagem so' passa por `printf '%s' "$msg" \| sed/grep`. **Zero** expansao de comando sobre ela. |
| **T-07-08** — bypass silencioso via `--no-verify` | `test_historico_do_v24_sem_co_change_knob_e_golden` varre `BASE_V24..HEAD`. A escapatoria fica no `git log` **para sempre**. |
| **T-07-09** — `core.hooksPath` desinstalado | `test_hook_do_blind05_esta_instalado` → suite **vermelha**. Provado acima. |

## Handoff

- **07-05 (BLIND-06):** `calibracao.lock.yaml` **precisa** ficar na **raiz**, fora de `tests/`.
  `config.yaml` + lock no mesmo commit e' o caminho **sancionado** — se o lock morasse em `tests/`,
  o proprio hook do BLIND-05 bloquearia o fluxo normal de mudanca de knob. Isso esta escrito **dentro
  do hook**, como comentario, para nao se perder.
- **Fases 10–13 (as que mexem em knob):** o caminho e' **dois commits** — o knob de um lado, o teste
  do outro. Se for genuinamente atomico (primitiva nova nascendo com knob e teste), o trailer existe
  e e' revisavel. **Nao existe versao silenciosa disto.**

## Commits

| Hash | Task | Descricao |
|---|---|---|
| `94f76c0` | 1 | `.githooks/commit-msg` + `core.hooksPath` — bloqueio provado E2E (a/b/b2/c) |
| `fee75f9` | 2 | backstop: 3 testes (instalado / versionado / historico do v2.4 limpo) |

## Self-Check: PASSED

- `.githooks/commit-msg` — FOUND (executavel, `git ls-files` → 1 linha)
- `tests/test_blindagem_hook.py` — FOUND
- commits `94f76c0`, `fee75f9` — FOUND
- `git config --get core.hooksPath` → `.githooks`
- `grep -c "Knob-Change-Justification" .githooks/commit-msg` → **4** (≥2) · `grep -c eval` → **0** ·
  `grep -c ticker_map.json` → **2** (≥1) · `grep -c BASE_V24 tests/test_blindagem_hook.py` → **5** (≥2)
- `pytest -q -rs` → `416 passed, 1 skipped, 38 deselected, 2 xfailed` (0 failed, 0 errors, 0 XPASS)
- `git diff --stat -- src/ config.yaml` → **vazio** · `git hash-object config.yaml` → `441ae99` (inalterado)
