---
phase: 07-blindagem-processual-blind
plan: 01
subsystem: test-harness
tags: [pytest, quarentena, golden, blindagem, blind-01]
requires: []
provides:
  - "tests/helpers_blindagem.py (substrato: detector AST, loaders) — consumido por 07-03 e 07-05"
  - "tests/classificacao.yaml (448 testes classificados, artefato de BLIND-01)"
  - "tests/conftest.py (marcadores dinamicos + completude imposta na coleta)"
  - "marcadores pytest: invariante / golden_nivel / contrato"
  - "xfail_strict = true (pre-requisito de BLIND-02, plano 07-02)"
affects: [pyproject.toml, tests/]
tech-stack:
  added: []
  patterns: ["quarentena por marcador dinamico via YAML commitado (zero edicao nos testes existentes)"]
key-files:
  created:
    - tests/helpers_blindagem.py
    - tests/conftest.py
    - tests/classificacao.yaml
    - scripts/bootstrap_classificacao.py
  modified:
    - pyproject.toml
decisions:
  - "golden_nivel = trava um NIVEL de saida de valuation ancorado em (a) empresa real OU (b) knob de producao. A regra (b) foi acrescentada na auditoria: um nivel travado por knob quebra na mesma fase que um travado por ticker."
  - "O caso do livro (DDM Itau R$ 37,22, Ke 12,48%) fica INVARIANTE, nao golden_nivel — e' referencia publicada com inputs hardcoded, e' a estrela-guia do marco. Quarentena-lo perderia o norte."
  - "Os goldens de DADO (ingest) entram como golden_nivel: sao `ticker == numero`, e o meta-teste BLIND-04a (07-03) exige detectados ⊆ quarentenados."
metrics:
  duration: ~50min
  completed: 2026-07-13
  tasks: 3
  commits: 3
---

# Fase 7 Plano 01: Classificacao e quarentena dos 448 testes — Summary

Quarentena dos goldens de nivel por YAML commitado + `conftest.py`, com completude imposta na
coleta: **410 testes rodam por default, 38 ficam deselecionados**, zero edicao nos testes existentes
e zero mudanca de numero.

## Numeros MEDIDOS (nao os da pesquisa)

| Metrica | Medido | Plano/pesquisa dizia |
|---|---:|---|
| Nodeids colhidos | **448** | 448 ✅ |
| `N` — rodam por default | **410** | — |
| `Q` — quarentenados (`golden_nivel`) | **38** | ≥ 47 ❌ (ver Desvio 2) |
| `invariante` | **102** | — |
| `contrato` | **308** | — |
| Goldens vindos do **detector AST** | **26** | 47 ❌ |
| Goldens **promovidos na auditoria manual** | **12** | — |
| Tickers em `ticker_map.json` | **104** | 105 ❌ (ver Desvio 1) |
| Travas de nivel do **ITUB4** achadas | **6** | 1 (ROADMAP) / 3 (pesquisa) |

`N + Q = 410 + 38 = 448` ✅

## Comportamento verificado (os 3 modos + os 2 canarios)

| Comando | Resultado |
|---|---|
| `.venv/bin/python -m pytest -q` | `410 passed, 38 deselected in 3.4s` |
| `pytest -q -m golden_nivel` | `38 passed, 410 deselected` — quarentenados rodam sob demanda |
| `pytest -q -m "" --collect-only` | `448 tests collected` — nada foi perdido |
| **canario** — teste novo sem classificacao | `ERROR: TESTE NAO CLASSIFICADO (BLIND-01) — adicione a tests/classificacao.yaml: tests/test_tmp_canario.py::test_tmp` → arquivo removido → suite volta a `410 passed` |
| **orfao** — entrada no YAML sem teste | `ERROR: CLASSIFICACAO ORFA — o teste sumiu mas a entrada ficou` |

O check de orfao e' o que torna a delecao da Fase 10 **auditavel**: apagar a funcao de teste sem
apagar a linha do YAML quebra a coleta.

## As SEIS travas de nivel do ITUB4 (o ROADMAP nomeia uma)

Todas marcadas no YAML com `-> DELETAR na Fase 10 (PRIM-05), NUNCA atualizar`:

| # | Teste | O que trava |
|---|---|---|
| 1 | `test_backtest_bancos.py::test_backtest_alvos_recalibrados` | `32.88 ± 0.20` |
| 2 | `test_backtest_bancos.py::test_backtest_cesta_rota_por_ticker` | banda 30–40 (`_ITUB4_RIM_MIN/MAX`) |
| 3 | `test_motores.py::test_rota_seguradora_nao_pega_banco` | banda 30–40 |
| 4 | `test_motores.py::test_rim_itub4_honesto_maior_que_ddm` | banda 36–42 |
| 5 | `test_motores.py::test_rim_itub4_live_alvo_32_40` | banda 32–40 |
| 6 | `test_vulc3_regressao.py::test_rim_itub4_dispatch_banda` | `intrinseco > 30` |

(+ `test_backtest_gate_quorum_e_anotacao`, que trava o quorum sobre `fair_values_bancos`.)

**Deletar so' as 3 da pesquisa deixaria 3 travas vivas.** A Fase 10 fecha com
`pytest -m golden_nivel` e **zero** restante citando ITUB4.

## Desvios do plano

### 1. [Rule 1 - Fato do plano errado] `ticker_map.json` tem 104 tickers, nao 105

- **Achado na:** Task 1 (criterio de aceite dizia "imprime 105")
- **Causa:** o JSON tem **106** chaves, das quais **duas** sao comentarios
  (`_comentario` e `_comentario_liquidez`) — a pesquisa filtrou so' uma.
- **Decisao:** `tickers_conhecidos()` filtra `startswith("_")` → **104**. Contar um comentario
  como ticker seria um falso positivo do mesmo tipo que o `MACD12` que o Pitfall 7 proibe.
- **Commit:** `b77a241`

### 2. [Rule 1 - Spec insatisfazivel] O "47" do detector AST nao se reproduz — medi 26 (e Q=38)

- **Achado na:** Task 1; confirmado na Task 3.
- **O que medi:** a regra exata do RESEARCH § BLIND-04a (ticker literal validado contra
  `ticker_map.json` **E** constante nao-trivial num `Compare`/`Assert`) acha **25**. Fechei
  duas rotas de evasao (constante via variavel local; **constante de MODULO** — e' onde o golden
  da banda 30–40 do ITUB4 se esconde, `_ITUB4_RIM_MIN = 30.0` mora fora da funcao) → **26**.
  A regra "larga" (constante em qualquer lugar do corpo) da **39**. **Nenhuma regra mecanica
  defensavel produz 47.** E' a mesma classe de problema que a pesquisa ja' havia diagnosticado
  para o "~150" do ROADMAP e para a spec do BLIND-02: um numero herdado que nao sobrevive a medicao.
- **Por que o detector nao ve mais:** ele so' enxerga **ticker literal dentro da funcao**. Goldens
  ancorados em **fixture de ticker real** (`snapshot_bancos`, `fair_values_bancos`,
  `_cesta_congelada()`) ou em **helper de modulo** nao tem literal nenhum no corpo. **Por
  construcao, o detector e' bootstrap — o YAML e' sempre um SUPERSET dele.** Isto esta escrito na
  docstring, porque o meta-teste BLIND-04a (plano 07-03) depende dessa direcao:
  `detectados ⊆ quarentenados`.
- **Decisao:** **nao inflei a quarentena para bater 47.** `Q = 38` e' o numero auditado.
- **Consequencia para o 07-03:** o meta-teste do BLIND-04a **passa** (26 detectados ⊆ 38
  quarentenados), com folga de 12.

### 3. [Rule 2 - Funcionalidade critica ausente] Aspas SIMPLES nas chaves do YAML

- **Achado na:** Task 3 — a suite reportou o **mesmo** teste como "nao classificado" **e** "orfao".
- **Causa (bug real, nao cosmetico):** o pytest **ASCII-escapa acentos** nos ids de `parametrize`
  (`...[PETR4-Petr\xf3leo-...]`). Em chave de **aspas duplas**, o YAML **reinterpreta** `\xf3` como
  escape → a chave vira `Petróleo` e **deixa de casar** com o nodeid real.
- **Fix:** chaves em **aspas simples** (YAML nao processa escapes em aspas simples). Comentado no
  gerador para nao regredir.
- **Commit:** `1f24e01`

### 4. [Auditoria] Regra de `golden_nivel` estendida a niveis ancorados em KNOB

O plano define `golden_nivel` como nivel ancorado em **ticker real ou fixture de ticker real**.
Na auditoria apareceu uma terceira forma da **mesma doenca**: testes que travam um nivel lido dos
**knobs de producao** do `config.yaml`, sem citar ticker — ex.
`test_ke_local_na_faixa_small_cap_br` (`0.13 < ke < 0.22`, vem de `erp_local`/`rf_local`),
`test_ke_rim_menor_que_ke_live_de_banco` (`0.11 <= kr <= 0.14` = `ke_piso`/`ke_teto`),
`test_teto_absoluto_025_...` (o teto de `g` = 0,25). **A Fase 11/12 move exatamente esses knobs** →
o executor "atualizaria a banda". Foram quarentenados (precedencia do plano: `golden_nivel` >
`invariante` > `contrato`). Os 12 promovidos estao listados em `scripts/`-nenhum: a lista vive no
proprio `classificacao.yaml`, com o comentario da fase que os mata.

### 5. [Auditoria] O caso do livro NAO foi quarentenado — de proposito

`test_ddm.py::test_ddm_itau_crescimento_constante` (`valor_intrinseco ≈ 37.22`) e
`test_ke_itau_capm` (`Ke ≈ 12,48%`) sao **o criterio de aceite soberano do marco v2.4**. Pela regra
literal do plano eles nao sao golden (nao ha literal de ticker no arquivo — nem `ITUB4` nem `ITSA4`
aparecem em `test_ddm.py`; os inputs sao hardcoded do livro), e pela **semantica** eles sao
`invariante`: **referencia publicada** (Cap. 17, Tabelas 41/43), imune a knob. Quarentena-los
tiraria a estrela-guia do default. **Ficam rodando.** Mesma decisao para
`test_comparables.py::test_preco_alvo_cteep` (Cap. 12).

## O que NAO foi feito (e nao devia)

- **Zero edicao** em `src/`, `config.yaml`, `tests/test_*.py`, `tests/fixtures/`
  (`git diff --stat HEAD~3 -- src/ config.yaml tests/test_*.py tests/fixtures/` → **vazio**).
- **Nenhum numero mudou.** O `V` de nenhum ticker se moveu.
- Nenhuma dependencia instalada (pytest 9.0.3 + PyYAML + `ast`, tudo ja' no ambiente).

## Handoff — fora do escopo desta fase

- **Golden master dos 104 tickers** (PITFALLS P5.2 / RESEARCH Q3): **nao e' requisito BLIND e nao
  foi feito aqui.** E' **pre-requisito das Fases 8/9** — sem baseline commitado, "os asserts viram
  verde ticker a ticker" nao e' mensuravel (`out/` e' gitignored → nao existe baseline hoje).
  **Sinalizar ao planner do marco.**
- **`CLAUDE.md` diz "testes golden existentes devem continuar passando"** — a regra velha. Continua
  literalmente verdadeira (os 38 passam em `-m golden_nivel`), mas a proxima sessao pode ler isso e
  "consertar" um golden. A pesquisa recomenda atualizar o `CLAUDE.md` **ao final da Fase 7**
  (depois do 07-05), nao agora.
- **`invariante` vs `contrato`** foi resolvido **por regra** (nome + forma do assert), nao teste a
  teste — como o plano autoriza. So' o bucket `golden_nivel` foi auditado linha a linha. A distincao
  nao e' operacional nesta fase: **as duas categorias rodam por default**; so' `golden_nivel`
  deseleciona.

## Commits

| Hash | Task | Descricao |
|---|---|---|
| `b77a241` | 1 | substrato: detector AST (3 rotas de evasao fechadas) + bootstrap |
| `9e40bf5` | 2 | `pyproject` (marcadores + `addopts` + `xfail_strict`) + `conftest` (completude) |
| `1f24e01` | 3 | `classificacao.yaml` auditado: 448 entradas, 38 em quarentena |

## Self-Check: PASSED

- `tests/helpers_blindagem.py` — FOUND
- `tests/conftest.py` — FOUND
- `tests/classificacao.yaml` — FOUND
- `scripts/bootstrap_classificacao.py` — FOUND
- commits `b77a241`, `9e40bf5`, `1f24e01` — FOUND
- `pytest -q` → `410 passed, 38 deselected` (0 failed, 0 errors); `410 + 38 = 448`
