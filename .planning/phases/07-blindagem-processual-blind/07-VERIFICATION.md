---
phase: 07-blindagem-processual-blind
verified: 2026-07-13T00:00:00Z
status: gaps_found
score: 5/8 must-haves verificados
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
  note: "Verificação inicial. Roda DEPOIS do 07-REVIEW.md (5 BLOCKERs) e do 07-REVIEW-FIX.md. Os 5 fixes foram re-executados aqui de forma independente — todos confirmados."
gaps:
  - truth: "Nenhuma guarda da fase pode ser desligada em silêncio (suíte continua verde)"
    status: failed
    reason: >-
      EXECUTADO: trocar `addopts` no pyproject.toml de `-m 'not golden_nivel'` para
      `-m 'not golden_nivel and not invariante'` deseleciona as 108 invariantes E os 2
      xfail(strict) — a suíte reporta `316 passed, 1 skipped, 146 deselected`, ZERO failed,
      VERDE. BLIND-02 e BLIND-03 (as duas doenças escritas como código) somem sem um único
      teste reclamar. Segundo caminho, também executado: `BLIND_BOOTSTRAP=1` no ambiente
      desliga a completude do BLIND-01 — um teste sem classificação passa a rodar em silêncio
      (423 passed, nada reclama). É exatamente o modo de falha que a fase existe para fechar:
      "ninguém nota". Previsto pelo review como WR-12/WR-05 e deliberadamente pulado no fix pass.
    artifacts:
      - path: "pyproject.toml"
        issue: "`addopts` e `xfail_strict` são a raiz de BLIND-01/02/03 e nenhum teste afirma que continuam lá"
      - path: "tests/conftest.py"
        issue: "`BLIND_BOOTSTRAP=1` (linha 40) desliga a completude globalmente, sem denúncia"
    missing:
      - "Teste `contrato` que lê `pytestconfig`: `xfail_strict is True`, `not golden_nivel` e `--strict-markers` presentes em addopts, e `invariante` AUSENTE de addopts"
      - "Teste `contrato` que falha se `BLIND_BOOTSTRAP` estiver no ambiente (o env é só do scripts/bootstrap_classificacao.py)"
  - truth: "A quarentena remove NÍVEL, não proteção estrutural"
    status: failed
    reason: >-
      Auditoria por AST (independente): 21 das 38 funções em quarentena carregam, na MESMA
      função, um golden de nível E um invariante estrutural que não depende de nível nenhum
      (`a.motor == 'rim'`, `a.san01_reetiquetado is True`, `c.dy_recorrente() <= c.dy_atual()`,
      `itub['arquetipo'] == 'financeira'`, contratos de chave do home feed, degradação por item).
      Esses asserts HOJE JÁ NÃO RODAM (deselecionados). O CLAUDE.md manda "golden de nível
      quebrou? DELETE" — logo a Fase 10/12 vai deletar as funções e levar os invariantes junto,
      em silêncio. A fase, que existe para AUMENTAR a superfície de constrangimento, REDUZIU-a
      em 21 asserts estruturais. O fix pass cindiu 2 e documentou o resto como aberto.
    artifacts:
      - path: "tests/classificacao.yaml"
        issue: "21 funções `golden_nivel` são mistas (nível + invariante estrutural preso)"
      - path: "tests/test_motores.py, tests/test_growth_reconciliacao.py, tests/test_arquetipo_roteamento.py, tests/test_guardrails_ddm.py, tests/test_home_feed.py, tests/test_payout_sustentavel_multiticker.py, tests/test_vulc3_regressao.py, tests/test_backtest_bancos.py"
        issue: "funções mistas — o assert relacional morre com o golden"
    missing:
      - "Cindir as 21 funções mistas: assert relacional vira função `invariante` (volta ao run default), banda de nível fica na função `golden_nivel`"
      - "Depois da cisão: teste `contrato` que PROÍBE quarentenar função mista (fecha a classe inteira)"
      - "Prazo: antes da Fase 10 — é a fase que deleta os goldens"
  - truth: "O choque do BLIND-02 não pode fabricar um veredito de doença"
    status: partial
    reason: >-
      `choque_nominal` (helpers_blindagem.py:630) tem `if roe0 is None or roe0 <= 0: continue`
      — a empresa recebe choque só de taxa e o teste segue afirmando sobre o resultado. Medido
      hoje: os 4 tickers do snapshot têm ROE positivo e a perna do lucro aplica +300 bps exatos
      (ITUB4 0,1931 -> 0,2231), então o veredito de HOJE é honesto. Mas a PRIM-02 (Fase 10)
      reescreve `roe_valuation`. Se ela devolver None para o ITUB4, o teste continua rodando,
      chocando pela metade, e o veredito "doença curada / não curada" da Fase 12 passa a ser
      fabricado — sem aviso.
    artifacts:
      - path: "tests/helpers_blindagem.py"
        issue: "linha 630: `continue` silencioso na perna do lucro nominal"
    missing:
      - "Trocar o `continue` por `raise ValueError` — o ticker sai da cesta do choque explicitamente, nunca é chocado pela metade"
deferred:
  - truth: "test_nenhum_ticker_e_load_bearing emite veredito (jackknife)"
    addressed_in: "Phase 14"
    evidence: "ROADMAP Phase 14 (VAL): 'hold-out roda uma vez, 3 graus de liberdade, distribuição + jackknife'. O teste SKIPa hoje por falta do fixture tests/fixtures/holdout_v24.yaml, que nasce em VAL-02. O harness (mediana_jackknife) existe e é provado em dados sintéticos."
  - truth: "BLIND-02(b) test_invariancia_inflacao_engine_itub4 fica verde"
    addressed_in: "Phase 12"
    evidence: "ROADMAP Phase 12 (KE): 'ke_teto/ke_piso deletados'. ROADMAP SC2 da Fase 7 diz explicitamente que o xfail 'vira verde sozinho na Fase 12'. Vermelho hoje é o comportamento CORRETO."
  - truth: "BLIND-03 test_normalizacao_nao_pune_crescimento fica verde"
    addressed_in: "Phase 10"
    evidence: "ROADMAP Phase 10 (PRIM): 'critério de saída: o golden ITUB4 32.88 quebra e é DELETADO'; PRIM-01 conserta normalizacao.py:73-75. Vermelho hoje é o comportamento CORRETO."
---

# Fase 7: Blindagem processual (BLIND) — Relatório de Verificação

**Objetivo da fase:** Redefinir o que "suíte verde" significa **antes de tocar uma linha de código
de método**. Hoje 448 testes ficam verdes sobre um snapshot em que o ITUB4 tem 10 milhões de ações —
a suíte é decorativa e não constrange mais o modelo.
**Verificado:** 2026-07-13
**Status:** gaps_found
**Re-verificação:** Não — verificação inicial (posterior ao 07-REVIEW + 07-REVIEW-FIX)

## Método

Não confiei em nenhuma afirmação de SUMMARY nem do 07-REVIEW-FIX.md. Montei um **worktree git
isolado** no HEAD da fase e **executei cada evasão** — as 5 que o review provou e as que o fixer
disse ter fechado, mais as que ele disse ter deixado abertas. Toda linha de "Resultado medido"
abaixo é saída de comando, não leitura de código. O worktree foi removido e o repo está intacto
(`git status` idêntico ao início; suíte em `422 passed, 1 skipped, 38 deselected, 2 xfailed`).

## Goal Achievement

### Observable Truths

Os itens 1–5 são os **Success Criteria literais do ROADMAP** (o contrato). Os itens 6–8 são
derivados do **objetivo** da fase — a fase entrega uma *guarda*, e o modo de falha que importa é
uma guarda que existe mas **não morde**. O prompt da fase é explícito: "pode ser trivialmente
evadida ou silenciosamente desligada?"

| # | Truth | Status | Evidência |
|---|-------|--------|-----------|
| 1 | Arquivo commitado classifica os testes em INVARIANTE / GOLDEN-DE-NÍVEL / CONTRATO; goldens em quarentena não bloqueiam o marco | ✓ VERIFICADO | `tests/classificacao.yaml`: 463 entradas, 3 categorias (108 invariante / 38 golden_nivel / 317 contrato), 0 `REVISAR` pendente. `addopts = -m 'not golden_nivel'` deseleciona os 38. **Executado:** teste novo sem entrada no YAML → `UsageError`, coleta QUEBRA (`no tests ran`). A completude morde. |
| 2 | Dois testes de invariância à inflação, choque +300 bps simultâneo em `rf`, `g_cap` E `ROE`: (a) invariante algébrico exato, passa hoje; (b) `xfail(strict=True)` sobre a engine, limiar 5%, falha se passar | ✓ VERIFICADO | `test_invariantes_v24.py`. (a) `test_invariancia_inflacao_identidade_pb_justo`: `P/B = 1+(ROE−Ke)/(Ke−g)`, choque nas 3 pernas, assert `< 1e-9`, não lê config (knob-proof), PASSA. (b) `test_invariancia_inflacao_engine_itub4`: `xfail(strict=True)`, `LIMIAR_INFLACAO = 0.05`. **Executado:** o choque aplica +300 bps exatos ao ROE dos 4 tickers (ITUB4 0,1931→0,2231) e o V vai 32,88 → 38,80 (**+18,02%**) — bate com a medição documentada. `xfail_strict = true` no pyproject → XPASS = FAILED. |
| 3 | Teste prova que a normalização pune crescimento hoje (série pura de +10%/ano → base abaixo do último ano menos inflação) | ✓ VERIFICADO | `test_normalizacao_nao_pune_crescimento`, `xfail(strict=True)`. Série geométrica pura (zero outlier), lê `anos_media`/`winsor` do **config de produção** (não hardcoded) — a fuga por knob vira alteração visível que o BLIND-06 pega. Forma fechada `-g/(1+g)` = −9,09%. |
| 4 | Nenhum teste de calibração afirma `ticker == valor em reais`; validação por distribuição + jackknife | ✓ VERIFICADO | `test_nenhum_teste_de_calibracao_crava_ticker_em_reais` (AST + `ticker_map.json`, nunca regex). **Executado:** 0 ofensores não tolerados na suíte real. Ataque realista (golden novo classificado como `contrato`, não quarentenado) → **VERMELHO**. Harness do jackknife existe e é provado em dados sintéticos. O *veredito* SKIPa até a Fase 14 (ver Deferred). |
| 5 | Hook de pre-commit bloqueia co-change `config.yaml` + golden/fixture; orçamento de exatamente 3 graus de liberdade travado por teste | ✓ VERIFICADO | **Executado (commits reais):** 5/5 co-changes de governança BLOQUEADOS (rc=1), 2/2 controles passam (rc=0). Trailer legítimo passa; ticker minúsculo, ticker no 2º trailer e ticker maiúsculo → BLOQUEADOS. `--no-verify` → o backstop histórico fica **VERMELHO**. `core.hooksPath` removido (clone novo) → teste VERMELHO. Hook sem bit de exec → VERMELHO. Lock: 3 graus (`ERP`, `n_fade`, `PIB_real`) + 27 congelados + 1 `user_control`; knob novo não declarado → VERMELHO. |
| 6 | **Nenhuma guarda pode ser desligada em silêncio (suíte continua verde)** | ✗ **FALHOU** | **Executado:** `addopts` → `-m 'not golden_nivel and not invariante'` ⇒ `316 passed, 1 skipped, 146 deselected`, **0 failed, VERDE**. As 108 invariantes e os 2 xfail somem; nenhum teste reclama. Segundo caminho: `BLIND_BOOTSTRAP=1` ⇒ teste sem classificação roda em silêncio (`423 passed`), completude do BLIND-01 desligada. (WR-12 / WR-05) |
| 7 | **A quarentena remove NÍVEL, não proteção estrutural** | ✗ **FALHOU** | Auditoria AST: **21 das 38** funções em quarentena são mistas — carregam invariante estrutural preso junto do golden (`a.motor == 'rim'`, `a.san01_reetiquetado is True`, `c.dy_recorrente() <= c.dy_atual()`, contratos de roteamento e degradação). Já não rodam hoje; a Fase 10/12 vai deletá-los junto com o golden. O fix pass cindiu 2. (WR-04, parcial) |
| 8 | O choque do BLIND-02 não pode fabricar um veredito de doença | ⚠️ PARCIAL | `choque_nominal` tem `continue` silencioso quando `roe0 is None`. Hoje inofensivo (os 4 tickers têm ROE > 0, medido). Mas a PRIM-02 (Fase 10) reescreve `roe_valuation` — se ela devolver None para o ITUB4, o teste chocará pela metade e o veredito da Fase 12 vira fabricação. (WR-10) |

**Score:** 5/8 — os **5 Success Criteria do ROADMAP passam**; 2 verdades de objetivo falham, 1 parcial.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | `test_nenhum_ticker_e_load_bearing` emite veredito | Phase 14 | ROADMAP Ph.14: "hold-out roda uma vez, 3 graus de liberdade, **distribuição + jackknife**". SKIPa hoje por falta do fixture `holdout_v24.yaml` (nasce em VAL-02). O `skip` explícito é a escolha certa — um `xfail` viraria XPASS por dependência de fase, sinal trocado. |
| 2 | BLIND-02(b) fica verde | Phase 12 | ROADMAP Ph.12: `ke_teto`/`ke_piso` deletados. O SC2 da própria Fase 7 diz "vira verde sozinho na Fase 12". **Vermelho hoje é o correto.** |
| 3 | BLIND-03 fica verde | Phase 10 | ROADMAP Ph.10 (PRIM-01). **Vermelho hoje é o correto.** |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/classificacao.yaml` | Classificação dos testes | ✓ VERIFICADO | 463 entradas, 3 categorias, 0 REVISAR. Aplicado por `conftest.py`; completude imposta. |
| `tests/conftest.py` | Marcadores + completude | ⚠️ FUNCIONAL, DESLIGÁVEL | Morde (executado). Mas `BLIND_BOOTSTRAP=1` desliga em silêncio (T6). |
| `pyproject.toml` | Quarentena + `xfail_strict` | ⚠️ FUNCIONAL, DESPROTEGIDO | É a raiz de BLIND-01/02/03 e nenhum teste afirma que continua lá (T6). |
| `tests/helpers_blindagem.py` | Detector AST + choque | ✓ VERIFICADO (1 ressalva) | Detector pega as 4 evasões. `choque_nominal` tem o `continue` da T8. |
| `tests/test_invariantes_v24.py` | As 2 doenças como código | ✓ VERIFICADO | 2 xfail(strict) incondicionais, ambos genuinamente vermelhos. |
| `tests/test_blindagem_meta.py` | BLIND-04a + jackknife | ✓ VERIFICADO | Morde o ataque realista. |
| `.githooks/commit-msg` | Bloqueio de co-change | ✓ VERIFICADO | 9/9 evasões bloqueadas, 0 falso positivo (commits reais). |
| `tests/test_blindagem_hook.py` | Backstop `--no-verify` | ✓ VERIFICADO | Fica vermelho com commit burlado, hook desinstalado, hook sem exec. |
| `calibracao.lock.yaml` | 3 graus de liberdade | ✓ VERIFICADO | Partição completa: 3 graus + 27 congelados + 1 user_control. |
| `tests/test_blindagem_orcamento.py` | Orçamento + canário | ✓ VERIFICADO | 4 testes; todos mordem (executado). Canário é substantivo, não `assert True`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `classificacao.yaml` | run default | `conftest` marca → `addopts` deseleciona | ✓ WIRED | 38 deselected, confirmado |
| `test_invariantes_v24` | engine real | `report.analisar_acao` + `choque_nominal` | ✓ WIRED | V 32,88 → 38,80 medido |
| `test_blindagem_meta` | suíte inteira | `detectar_ticker_com_valor_cravado` (AST, rglob) | ✓ WIRED | pega subdiretório, constante de módulo, helper |
| `.githooks/commit-msg` | git | `core.hooksPath` + teste que verifica a instalação | ✓ WIRED | clone sem hooksPath → teste vermelho |
| `calibracao.lock.yaml` | `config.yaml` | `test_knobs_batem_com_o_lock` | ✓ WIRED | `margem_seguranca` 0,15→0,30 → vermelho |
| `pyproject.toml` (addopts) | *qualquer teste* | — | ✗ **NOT_WIRED** | **Nada verifica a raiz da blindagem** (T6) |
| funções mistas em quarentena | run default | — | ✗ **NOT_WIRED** | 21 invariantes estruturais fora do run (T7) |

### Behavioral Spot-Checks (evasões executadas)

| Comportamento | Resultado medido | Status |
|---|---|---|
| Suíte default | `422 passed, 1 skipped, 38 deselected, 2 xfailed`, 0 XPASS | ✓ PASS |
| `git diff 2056839 -- src/` | **vazio** — zero código de produção tocado | ✓ PASS |
| `config.yaml` semanticamente inalterado | `yaml.safe_load(antes) == yaml.safe_load(depois)` → **True** (diff é só comentário) | ✓ PASS |
| CR-01 `xfail(False, strict=True)` + golden ITUB4 | detectado=SIM, tolerado=**NÃO** | ✓ PASS (fix confirmado) |
| CR-02 ticker em constante de módulo | detectado=SIM, tolerado=NÃO | ✓ PASS (fix confirmado) |
| CR-03 assert movido para helper | detectado=SIM, tolerado=NÃO | ✓ PASS (fix confirmado) |
| WR-13 golden em `tests/sub/` | detectado=SIM, tolerado=NÃO | ✓ PASS (fix confirmado) |
| Golden novo classificado como `contrato` | `BLIND-04a` **FAILED** | ✓ PASS |
| CR-04 `config.yaml` + `classificacao.yaml` | rc=1 **BLOQUEADO** (era rc=0) | ✓ PASS (fix confirmado) |
| CR-04 `config.yaml` + `conftest.py` / `helpers_blindagem.py` / `pyproject.toml` | rc=1 **BLOQUEADO** (3/3) | ✓ PASS |
| WR-02 ticker minúsculo no trailer | rc=1 BLOQUEADO | ✓ PASS |
| WR-03 ticker no 2º trailer | rc=1 BLOQUEADO | ✓ PASS |
| Trailer econômico legítimo (sem ticker) | rc=0 passa | ✓ PASS (sem falso positivo) |
| `--no-verify` num co-change | `test_historico...` **FAILED** | ✓ PASS |
| `core.hooksPath` removido (clone novo) | `test_hook_do_blind05_esta_instalado` **FAILED** | ✓ PASS |
| CR-05 `margem_seguranca` 0,15 → 0,30 | `test_knobs_batem_com_o_lock` **FAILED** | ✓ PASS (fix confirmado) |
| Knob novo não declarado no lock | `test_orcamento_de_knobs_e_exatamente_3` **FAILED** | ✓ PASS |
| Canário: ERP dobrado | passa (a engine reage) | ✓ PASS |
| **WR-12 `addopts` + `and not invariante`** | **`316 passed, 0 failed` — VERDE** | ✗ **FAIL** |
| **WR-05 `BLIND_BOOTSTRAP=1`** | **`423 passed` — teste sem classificação roda** | ✗ **FAIL** |

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|---|---|---|---|
| BLIND-01 | 07-01 | ✓ SATISFEITO | 463 testes classificados; quarentena de 38 deseleciona; completude quebra a coleta. Ressalva: desligável por `BLIND_BOOTSTRAP` (T6). |
| BLIND-02 | 07-02 | ✓ SATISFEITO | Invariante algébrico exato passa; xfail(strict) sobre a engine vermelho, choque nas 3 pernas confirmado por medição. |
| BLIND-03 | 07-02 | ✓ SATISFEITO | xfail(strict), série pura, knobs lidos do config de produção. |
| BLIND-04 | 07-03 | ✓ SATISFEITO | Detector AST resiste às 4 evasões; veredito do jackknife **deferido à Fase 14** (declarado). |
| BLIND-05 | 07-04 | ✓ SATISFEITO | Hook + backstop `--no-verify` + guarda de instalação, todos executados. |
| BLIND-06 | 07-05 | ✓ SATISFEITO | 3 graus travados; partição completa; canário substantivo. |

Nenhum requisito órfão: os 6 IDs do ROADMAP aparecem no frontmatter dos 5 planos.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `pyproject.toml` | 23 | Raiz da blindagem sem auto-proteção | 🛑 Blocker | Kill-switch de uma linha; suíte fica verde |
| `tests/conftest.py` | 40 | `BLIND_BOOTSTRAP` global e mudo | 🛑 Blocker | Desliga a completude do BLIND-01 em silêncio |
| `tests/classificacao.yaml` | — | 21 funções mistas em quarentena | 🛑 Blocker | Invariantes estruturais morrem com o golden na Fase 10 |
| `tests/helpers_blindagem.py` | 630 | `continue` silencioso no choque | ⚠️ Warning | Pode fabricar o veredito "doença curada" na Fase 12 |

**Marcadores de dívida (TBD/FIXME/XXX/HACK):** nenhum nos 11 arquivos da fase. ✓

### Gaps Summary

**O que a fase acertou — e é muito.** Os 5 Success Criteria do ROADMAP passam, e passam *de
verdade*: eu executei as evasões em vez de ler o código. O hook bloqueia 9/9 ataques com 0 falso
positivo e ainda fica vermelho se alguém o desinstalar ou usar `--no-verify`. O detector do
BLIND-04a resiste às 4 evasões que o review provou (constante de módulo, assert em helper,
`xfail(False, strict=True)`, subdiretório). O `margem_seguranca` agora tem dente. As duas doenças
estão escritas como código, vermelhas pelo motivo certo, com o choque nas 3 pernas confirmado por
medição (ITUB4: 32,88 → 38,80, +18,02%). E a promessa central foi cumprida: **`git diff -- src/`
está vazio e o `config.yaml` é semanticamente idêntico** — a fase não moveu o `V` de ticker nenhum.
Os 5 BLOCKERs do code review foram genuinamente fechados; não aceitei a palavra do fixer em nenhum
deles.

**O que ainda não morde.** A fase entrega uma guarda, então o padrão de aprovação é mais alto que
"os testes passam": a guarda não pode ser desligada em silêncio. Duas podem, e eu provei rodando:

1. **`addopts` é um kill-switch de uma linha.** Acrescentar `and not invariante` ao `pyproject.toml`
   deseleciona as 108 invariantes *e* os 2 xfail — a suíte reporta `316 passed, 0 failed`, **verde**.
   Todo o BLIND-02 e BLIND-03 evaporam sem um único teste reclamar. Isso é literalmente o modo de
   falha do post-mortem do v2.3 ("o conserto é revertido e ninguém nota"), só que agora com a suíte
   dando um OK falso. O `BLIND_BOOTSTRAP=1` é o segundo caminho, mais discreto ainda: basta um
   `export` num `.zshrc`.

2. **A quarentena levou proteção junto.** 21 das 38 funções quarentenadas carregam invariantes
   estruturais presos (`a.motor == 'rim'`, `a.san01_reetiquetado is True`, contratos de roteamento e
   degradação). Eles **já não rodam hoje**, e o CLAUDE.md instrui a Fase 10 a *deletar* os goldens —
   levando os invariantes junto, em silêncio. A fase que existia para aumentar a superfície de
   constrangimento reduziu-a em 21 asserts. O fixer cindiu 2 e documentou honestamente que faltam as
   outras; a auditoria por AST confirma 21.

**Por que isto é gaps_found e não passed:** o próprio objetivo da fase é que "suíte verde" volte a
significar alguma coisa. Uma suíte que fica verde depois de eu desligar as invariantes por uma linha
de config não satisfaz esse objetivo — e uma proteção fantasma é pior que nenhuma, porque as Fases
9–13 vão confiar nela. Os três gaps são baratos de fechar (dois testes `contrato` de ~6 linhas cada,
mais um refactor de cisão que precisa de decisão humana de classificação).

**Ordem recomendada:** os dois testes `contrato` (T6) e o `raise` do `choque_nominal` (T8) podem
entrar já — são mecânicos. A cisão das 21 funções (T7) precisa de decisão de classificação caso a
caso (o fixer aponta que algumas metades "invariante" carregariam ticker + constante de módulo e
seriam pegas pelo BLIND-04a agora endurecido) — **task própria, obrigatoriamente antes da Fase 10**.
Nada aqui bloqueia a **Fase 8** (SAN), que não deleta golden nenhum.

---

_Verificado: 2026-07-13_
_Verificador: Claude (gsd-verifier)_
