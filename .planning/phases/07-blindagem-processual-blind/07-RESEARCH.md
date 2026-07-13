# Phase 7: Blindagem processual (BLIND) — Research

**Pesquisado:** 2026-07-13
**Domínio:** engenharia de testes (pytest), governança de configuração, hooks de git
**Confiança:** ALTA (quase tudo verificado por execução direta no repo, não por memória)

> **Nota de método:** este documento não cita "boas práticas". Cada número abaixo foi **medido
> rodando código neste repositório hoje**. Onde não consegui medir, está marcado `[ASSUMIDO]`.

---

<phase_requirements>
## Phase Requirements

| ID | Descrição | Suporte da pesquisa |
|----|-----------|---------------------|
| BLIND-01 | 448 testes classificados (INVARIANTE / GOLDEN-DE-NÍVEL / CONTRATO) em arquivo commitado; goldens em quarentena | § Mecanismo de Quarentena (validado E2E); contagens reais em § Inventário Real da Suíte |
| BLIND-02 | Teste de invariância à inflação, `xfail(strict=True)`, `V` varia < 2% sob +300 bps em `rf` e `g_cap` | § **ACHADO CRÍTICO**: a spec literal é **insatisfazível**. Ver § Open Questions Q1 — decisão obrigatória antes do plano |
| BLIND-03 | Teste de que a normalização não pune crescimento (haircut de −9,1%) | § BLIND-03: haircut medido, **fórmula fechada `−g/(1+g)`** — assert exato, não fuzzy |
| BLIND-04 | Nenhum teste de calibração afirma `ticker == valor em reais`; validação por distribuição + jackknife | § BLIND-04: metade **executável hoje** (meta-teste AST); metade **sem substrato de dados** até a Fase 14 |
| BLIND-05 | Pre-commit hook bloqueia commit que toque `config.yaml` + golden/fixture | § BLIND-05: `core.hooksPath` validado; 5 co-changes achados em 676 commits |
| BLIND-06 | Orçamento de exatamente 3 graus de liberdade (`ERP`, `n_fade`, `PIB_real`) travado por teste | § BLIND-06: `motores:` tem **11 chaves, não ~20**; regra do ticker é executável e **falha hoje** |
</phase_requirements>

---

## User Constraints

**Não existe `07-CONTEXT.md`** (`/gsd-discuss-phase` não foi rodado para esta fase). As restrições
abaixo vêm do `CLAUDE.md` do projeto e do ROADMAP, e têm a mesma autoridade de decisão travada.

### Project Constraints (from CLAUDE.md)

| Restrição | Consequência para esta fase |
|-----------|------------------------------|
| Python 3 + Streamlit; **sem backend próprio; custo zero** | Nenhuma dep paga, nenhum serviço de CI pago |
| **Testes golden existentes em `tests/` devem continuar passando** | ⚠️ **Conflito aparente com o v2.4** — resolvido em § Nota sobre o conflito CLAUDE.md × ROADMAP |
| Respostas em **pt-BR** | Este doc e os comentários dos testes em pt-BR |
| **Não criar arquivos de documentação extras sem ser solicitado** | O artefato de classificação é *requisito* (BLIND-01), não doc extra |
| Comentários só quando o "porquê" não é óbvio | Os testes BLIND são exceção legítima: o *porquê* é a doença |

### Anti-goals travados pelo ROADMAP (regras duras)

- **NÃO consertar nenhum número.** Se o `V` de qualquer ticker mudar nesta fase, saiu do escopo.
- **NÃO "atualizar" golden de nível.** Quarentenar agora, **deletar** quando a fase chegar.
- **NÃO afrouxar tolerância / `xfail` casual / deletar assert** para a suíte ficar verde (Pitfall 5).

### Nota sobre o conflito CLAUDE.md × ROADMAP

O `CLAUDE.md` diz *"testes golden existentes devem continuar passando"*. O ROADMAP v2.4 diz que
~150 goldens *serão quarentenados e deletados*. **Não é contradição — é sequenciamento.** O
`CLAUDE.md` foi escrito no v1.x, quando os goldens codificavam o método *pretendido*. O v2.4 provou
que eles codificam um método *errado* (o golden ITUB4 32,88 existe para cancelar um haircut de
−9,1% — dois erros se anulando). **Esta fase não deleta nada**: ela põe em quarentena e mantém tudo
rodável sob demanda. A suíte continua verde. Recomendo que o planner **atualize o `CLAUDE.md`** ao
final da fase para refletir a nova definição de "suíte verde" — senão a próxima sessão lê a regra
velha e "conserta" o teste.

---

## Summary

O diagnóstico do ROADMAP está **substancialmente certo, e a suíte é de fato decorativa** — provei
rodando: o `ITUB4` tem **10.004.676 ações em 2019** no snapshot contra ~10 **bilhões** nos anos
vizinhos (quebra de escala de ~1000×), e os **448 testes passam em 4,23s** sobre esse dado. Mas
três dos seis requisitos têm números ou premissas que **não se sustentam na medição**, e um deles
(**BLIND-02**) está **especificado de forma insatisfazível**. Descobrir isso na Fase 11, quando o
teste se recusar a ficar verde, custaria o diagnóstico inteiro do marco.

**As três correções factuais que o plano precisa absorver:**

1. **BLIND-02 é insatisfazível como escrito.** Chocar `rf` e `g_cap` em +300 bps *deixando o ROE
   parado* derruba o `V` em **−27,67%** mesmo com o `Ke` e o `g` **perfeitos do livro** e **zero
   clamps**. A razão é algébrica, não empírica: `P/B justo = 1 + (ROE−Ke)/(Ke−g)`. O choque preserva
   `(Ke−g)` mas **comprime `(ROE−Ke)`**. Invariância à inflação exige chocar **`ROE` também** —
   inflação levanta o lucro nominal, não só a taxa de desconto. E mesmo o choque correto só fica
   < 2% se `n_fade ≤ ~4`; com o `n_fade = 10` de hoje o piso é **−4,68%**. Ver § Open Questions Q1.
2. **`motores:` tem 11 chaves, não ~20.** A meta "~20 → ≤5" (regra dura C) está mal-calibrada. O
   orçamento de 3 graus de liberdade precisa de um **escopo declarado** — hoje a superfície de
   knobs de valuation é `motores`(11) + `capm`(12) + `ddm`(5) + `normalizacao`(2) = **30 folhas**.
3. **"~150 goldens de nível" não é reproduzível por nenhuma regra mecânica que eu consiga
   construir.** Os números defensáveis são **47** (testes que cravam ticker + número de nível) e
   **271** (testes no caminho de valuation). Ver § Inventário Real da Suíte.

O lado bom: **a arquitetura do repo coopera**. O config é **injetado por dependência** —
`report.analisar_acao(company, cfg)` recebe um `dict` puro. Perturbar o config num teste é
`copy.deepcopy` + mutar chave. Nenhum monkeypatch, nenhum singleton global. BLIND-02/03 são
escrevíveis sem tocar em código de produção.

**Recomendação primária:** classificação **YAML + `conftest.py`** (marcadores aplicados
dinamicamente, completude imposta na coleta) — **zero edições nos 448 testes existentes**, o que
honra literalmente o anti-goal "esta fase não move o `V` de ticker nenhum". Validado ponta a ponta.
E **resolver a Q1 (BLIND-02) antes de escrever o plano**, porque ela muda o que o teste afirma.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Classificação dos 448 testes (BLIND-01) | Test harness (`tests/conftest.py` + `tests/classificacao.yaml`) | — | É metadado de teste; não pertence a `src/` |
| Quarentena / deseleção | pytest config (`pyproject.toml` `addopts`) | conftest | Deseleção é config de runner, não lógica |
| Invariância à inflação (BLIND-02) | Test (`tests/test_invariantes_v24.py`) | Engine (`report.analisar_acao`, config injetado) | Testa a **engine**, chamando-a com cfg perturbado |
| Haircut da normalização (BLIND-03) | Test | Primitiva pura (`normalizacao.base_normalizada`) | Função pura → teste unitário exato |
| Proibição de `ticker == R$` (BLIND-04a) | Meta-teste (AST sobre `tests/`) | — | Analisa o **código-fonte dos testes**, não a engine |
| Jackknife (BLIND-04b) | Test harness + fixture | — | **Sem substrato de dados até a Fase 14** |
| Bloqueio de co-change (BLIND-05) | Git (`.githooks/pre-commit` + `core.hooksPath`) | Meta-teste (backstop p/ `--no-verify`) | Hook é a borda; teste é a rede de segurança |
| Orçamento de knobs (BLIND-06) | Test (lê `config.yaml`) + `calibracao.lock.yaml` | — | Config é o artefato sob teste |

**Observação de tier:** nenhum requisito desta fase pertence a `src/analista/`. **Se o plano
propuser editar qualquer arquivo em `src/`, é sinal de escopo vazando.** As únicas exceções
legítimas: nenhuma. (O `config.yaml` é tocado só para *limpar comentários* que mencionam ticker —
e isso **não muda valor nenhum**, ver § BLIND-06.)

---

## Inventário Real da Suíte (medido, não estimado)

```bash
python -m pytest --collect-only -q   # 448 tests collected in 1.69s
python -m pytest -q                  # 448 passed in 4.23s
```

**"448 testes" — CONFIRMADO exatamente** `[VERIFIED: pytest --collect-only]`.
(São 443 funções `test_*` no AST; 448 após expansão de 2 `parametrize`.)

### Partição por subsistema (soma = 448, verificada)

| Subsistema | Testes | Relevância p/ GOLDEN-DE-NÍVEL |
|---|---:|---|
| **Caminho de VALUATION** (importam `report`/`motores`/`ddm`/`capm`/`growth`/`normalizacao`/`comparables`/`lentes`/`selo`/`multiples`/`screening`/`freio`/`arquetipo`) | **271** | **É o único universo onde "golden de nível" faz sentido** |
| Caminho de INGEST (`cvm`, `prices`, `build`, `intraday`, `universe`) | 52 | Goldens de **dado** — mudam na Fase 9 (DATA-06) |
| Outros subsistemas (`indicators` 86, `grafico_ui` 12, `setup_report` 12, `home_feed` 13, `glossario` 2) | 125 | **Não tocam `V`** — análise técnica/UI. Trivialmente CONTRATO/INVARIANTE |

### O número "~150 goldens de nível" NÃO se reproduz

Construí um detector AST (`ast.walk` sobre cada `FunctionDef` `test_*`, procurando menção a ticker
validada contra `data/ticker_map.json` **E** constante float não-trivial):

| Bucket | Testes | Leitura |
|---|---:|---|
| A) ticker + número de nível | **47** | **Candidatos fortes a GOLDEN-DE-NÍVEL** |
| B) ticker, sem número | 53 | Provável CONTRATO (roteamento, rótulo) |
| C) número, sem ticker | 201 | Maioria é `test_indicators.py` (matemática pura → INVARIANTE) |
| D) nem ticker nem número | 142 | CONTRATO (never-raise, formato) |

**Distribuição dos 47 candidatos:** `test_arquetipo`(7), `test_motores`(5), `test_ingest_unit`(4),
`test_ranking_freio`(4), `test_vulc3_regressao`(4), `test_growth_robusto_multiticker`(3),
`test_guardrails_ddm`(3), `test_home_feed`(3), `test_lentes`(3),
`test_payout_sustentavel_multiticker`(3), `test_comparador`(2), + 6 arquivos com 1 cada.

**Conclusão honesta:** a verdade está entre **47** (regra mecânica estrita) e **271** (todo o
caminho de valuation). **Não existe regra automática que produza 150.** O plano deve tratar o "~150"
do ROADMAP como **estimativa não-verificada**, e a classificação como uma **auditoria dos 271**,
*bootstrapada* pelo detector dos 47. Os 125 "outros" podem ser classificados **em bloco** (por
arquivo) sem risco — não tocam `V`.

> ⚠️ **Descoberta importante para o mecanismo:** goldens e invariantes **coabitam o mesmo arquivo**.
> `test_motores.py` tem tanto o golden `30.0 <= intrinseco <= 40.0` (linha 238) quanto asserts
> algébricos puros. **Isso desqualifica qualquer mecanismo de quarentena com granularidade de
> arquivo** (`--ignore`, diretório separado). Ver § Mecanismo de Quarentena.

---

## Localização exata dos artefatos nomeados pelo ROADMAP

Todos verificados por leitura direta `[VERIFIED: grep/read no repo]`. **Duas correções de
line-number** — o ROADMAP e o `PITFALLS.md` estão off-by-one:

| Artefato | Local real | Status |
|---|---|---|
| **Golden `ITUB4: 32.88 ± 0.20`** | **`tests/test_backtest_bancos.py:121`** — `alvos = {"ITUB4": 32.88, "BBAS3": 43.89, "BBDC4": 13.37}`, assert `abs(rim - alvo) <= 0.20` na linha 125, teste `test_backtest_alvos_recalibrados` | ✅ **É o alvo da deleção na Fase 10 (PRIM-05)** |
| Golden ITUB4 (banda, 2º) | `tests/test_backtest_bancos.py:49-50` — `_ITUB4_RIM_MIN = 30.0` / `_MAX = 40.0`, usado no `test_backtest_cesta_rota_por_ticker:78` | ⚠️ **Segundo golden de nível do ITUB4** — o ROADMAP só nomeia o `32.88`. **Ambos precisam morrer na Fase 10**, senão a deleção é parcial |
| Golden ITUB4 (banda, 3º) | `tests/test_motores.py:238` — `assert 30.0 <= a.intrinseco_motor <= 40.0` | ⚠️ **Terceiro.** Idem |
| Golden ITUB4 (snapshot) | `tests/fixtures/snapshot_bancos_2026-07-12.yaml:296` — `intrinseco_motor_observado: 32.8803908610021` | Carimbo do valor observado no fixture |
| `config.yaml` `motores:` | linha **229**; **3 sub-blocos** (`rim`, `ciclica`, `crescimento`), **11 chaves-folha** | ❌ **ROADMAP diz "~20 chaves" — são 11** |
| `config.yaml:235` ("Blume" falso) | ✅ **correto** — `ke_teto: 0.13` + comentário "Blume puxa betas para 1,0" | Confirmado |
| `config.yaml:237` ("Move ITUB4 ~R$2") | ❌ **é a linha 238**, não 237 | Off-by-one no ROADMAP **e** no `PITFALLS.md:48` |
| `config.yaml:258` (PITFALLS) | ❌ **é a linha 259** ("NÃO mexer nos knobs acima... mudariam o ITUB4") | Off-by-one |
| `normalizacao.py:73-75` | ✅ **correto** — `if n < 5: return float(median(janela))` | Confirmado; ver § BLIND-03 |
| `fundamentals.py:137-150` | ✅ **correto** — `roe_valuation`: base normalizada (3a) ÷ `pl_ini=ult-1`,`pl_fim=ult` | Bases temporais cruzadas confirmadas |
| `build.py:87` | ✅ **correto** — `contagem_cvm[ano] = abs(f["lucro_liquido"] / lpa_cvm)` | Confirmado |
| `arquetipo.py:176` | ✅ **correto** — `candidatos.append(PAGADORA_REGULADA)  # pagadora madura por eliminação` | Confirmado |

### O snapshot (a prova de que a suíte é decorativa)

`tests/fixtures/snapshot_bancos_2026-07-12.yaml` — **7,6 KB, versionado**, 4 tickers
(BBAS3/BBDC4/BBSE3/ITUB4) + `data_base` + `rf_local: 0.105`.
**Gerado por:** `scripts/capturar_snapshot_bancos.py` (captura *one-time* ao vivo: CVM + Yahoo +
BCB via `build.montar_empresa`; congela fundamentos **crus**, não derivados).
**Consumido por:** `analista.backtest.carregar_snapshot()` → reconstrói `CompanyData` → offline.

`num_acoes` do ITUB4 no snapshot `[VERIFIED: yaml.safe_load]`:

```
2016:  6.605.602.241
2017:  6.594.565.217
2018: 10.015.234.375
2019:     10.004.676   <-- 10 MILHÕES. ~1000× menor que os vizinhos.
2020:  7.805.181.347
2021: 10.359.124.088
...
```

**Os 448 testes passam em 4,23s sobre isto.** É a definição operacional de "suíte decorativa".
(Bônus não documentado: **BBAS3 2024 = 6,31 bi vs 2023 = 3,16 bi — salto de 2×**, provável mesma
classe de bug. A Fase 8/SAN-02 deve pegá-lo.)

---

## Standard Stack

**Nada novo é instalado.** Tudo abaixo já está no ambiente `[VERIFIED: pip list]`.

| Ferramenta | Versão instalada | Uso nesta fase | Por que é o padrão |
|---|---|---|---|
| **pytest** | **9.0.3** | Marcadores, `xfail(strict)`, `addopts`, `conftest` | Já é o runner do projeto |
| **PyYAML** | 6.0.3 | `tests/classificacao.yaml`, `calibracao.lock.yaml` | Já é a dep de config do projeto |
| **`ast`** (stdlib) | — | Meta-teste BLIND-04a (detectar `ticker == R$`) | Zero dep; parser oficial do Python |
| **`git` hooks** (nativo) | git 2.39.5 | BLIND-05 via `core.hooksPath` | Zero dep; ver § BLIND-05 |
| **`subprocess`/`re`** (stdlib) | — | Backstop de `--no-verify`, scan de comentários | Zero dep |

### Alternativas consideradas e REJEITADAS

| Em vez de | Poderia usar | Por que rejeitei |
|---|---|---|
| `.githooks/` + `core.hooksPath` | **framework `pre-commit`** (pypi) | Adiciona dep pip, baixa **ambientes isolados por hook via rede**, exige `.pre-commit-config.yaml` + passo `pre-commit install`. **Peso e rede para 15 linhas de shell.** Viola o custo-zero/minimalismo que o ROADMAP impõe explicitamente na Fase 8 (`NÃO instalar pandera/great-expectations`) |
| Meta-teste AST caseiro | `pytest-golden`, `syrupy`, `pytest-regressions` | Todos resolvem *snapshot testing*, que é **exatamente o que estamos desmontando**. Instalar um framework de golden para gerenciar a morte dos goldens é irônico e errado |
| `hypothesis` p/ invariantes | — | Tentador para BLIND-02/03, mas os invariantes aqui são **algébricos e determinísticos** (fórmula fechada). Property-based testing não agrega e é +1 dep |
| Marcadores dinâmicos via YAML | Marcadores inline em 448 testes | Ver § Mecanismo de Quarentena — **rejeitado por superfície de edição** |

**Instalação:** *nenhuma*. `pip install` não é executado nesta fase.

---

## Mecanismo de Quarentena (BLIND-01) — decisão recomendada

### Recomendação: marcador pytest + deseleção via `addopts`, **com marcadores aplicados dinamicamente a partir de um YAML commitado**

Testado ponta a ponta neste ambiente `[VERIFIED: execução no scratchpad, pytest 9.0.3]`.

**`pyproject.toml`** (o bloco `[tool.pytest.ini_options]` já existe — **acrescentar**, não substituir):

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
xfail_strict = true                                    # BLIND-02: XPASS = FAIL, globalmente
addopts = "-m 'not golden_nivel' --strict-markers"     # BLIND-01: quarentena + marcador desconhecido = erro
markers = [
  "invariante: verdade algebrica que knob nenhum satisfaz (v2.4/BLIND-01).",
  "golden_nivel: trava um NUMERO do metodo atual. QUARENTENADO no v2.4. DELETAR na fase que o corrige — NUNCA atualizar.",
  "contrato: formato/borda/never-raise. Independe do nivel dos numeros.",
]
```

**`tests/classificacao.yaml`** (o artefato commitado que BLIND-01 pede — 448 entradas):

```yaml
# BLIND-01 — classificacao dos 448 testes do v2.4.
# invariante   : verdade algebrica; knob nenhum a satisfaz.
# golden_nivel : trava um numero -> trava o metodo atual. QUARENTENADO (deselecionado do default).
#                DELETAR na fase que o corrige. NUNCA atualizar para o valor novo.
# contrato     : formato/borda/never-raise.
tests/test_backtest_bancos.py::test_backtest_alvos_recalibrados: golden_nivel  # ITUB4 32.88 -> DELETAR na Fase 10
tests/test_backtest_bancos.py::test_backtest_cesta_rota_por_ticker: golden_nivel  # banda 30-40 -> DELETAR na Fase 10
tests/test_motores.py::test_rota_seguradora_nao_pega_banco: golden_nivel        # banda 30-40 -> Fase 10
tests/test_normalizacao.py::test_outlier_alto_suavizado_pela_mediana: invariante
tests/test_indicators.py::test_rsi_wilder_bate_referencia: invariante
# ... 443 restantes
```

**`tests/conftest.py`** (não existe hoje — **arquivo novo**):

```python
"""BLIND-01: aplica a classificacao commitada como marcador e IMPÕE completude.

Um teste novo sem entrada em classificacao.yaml QUEBRA a coleta. Uma entrada orfa (teste
deletado, classificacao esquecida) tambem. A classificacao nao pode silenciosamente driftar.
"""
import pathlib
import pytest
import yaml

CATEGORIAS = {"invariante", "golden_nivel", "contrato"}
_MAPA = pathlib.Path(__file__).parent / "classificacao.yaml"


def pytest_collection_modifyitems(config, items):
    mapa = yaml.safe_load(_MAPA.read_text(encoding="utf-8")) or {}
    vistos, sem_classe = set(), []

    for item in items:
        cat = mapa.get(item.nodeid)
        if cat is None:
            sem_classe.append(item.nodeid)
            continue
        if cat not in CATEGORIAS:
            raise pytest.UsageError(f"categoria invalida '{cat}' em {item.nodeid}")
        item.add_marker(getattr(pytest.mark, cat))
        vistos.add(item.nodeid)

    orfaos = set(mapa) - vistos
    erros = []
    if sem_classe:
        erros.append(
            "TESTE NAO CLASSIFICADO (BLIND-01) — adicione a tests/classificacao.yaml:\n  "
            + "\n  ".join(sorted(sem_classe))
        )
    if orfaos:
        erros.append(
            "CLASSIFICACAO ORFA — o teste sumiu mas a entrada ficou:\n  "
            + "\n  ".join(sorted(orfaos))
        )
    if erros:
        raise pytest.UsageError("\n\n".join(erros))
```

### Comportamento verificado

| Comando | Resultado medido |
|---|---|
| `pytest` | goldens **deselecionados**; suíte verde; **não bloqueiam o marco** ✅ |
| `pytest -m golden_nivel` | roda **só** os quarentenados, sob demanda ✅ |
| `pytest -m ""` | roda **tudo** (sobrepõe o `addopts`) ✅ |
| teste novo sem classificação | `ERROR: TESTE NAO CLASSIFICADO (BLIND-01)` ✅ |
| entrada órfã no YAML | `ERROR: CLASSIFICACAO ORFA` ✅ |
| marcador não registrado | `--strict-markers` → erro ✅ |

### Por que esta variante, e não as outras

| Alternativa | Por que **não** |
|---|---|
| **Diretório separado** (`tests/quarentena/`) | Exige **mover código**. Goldens e invariantes **coabitam o mesmo arquivo** (`test_motores.py`!) → mover exigiria *partir arquivos ao meio*, quebrando imports e helpers compartilhados (`_cesta_congelada()`). Churn de git enorme numa fase cujo anti-goal é "não mexer em nada". **Desqualificado.** |
| **`--ignore=arquivo`** | Granularidade de **arquivo**. Mesmo problema: `test_motores.py` tem 16 testes, só ~5 são goldens. Ignorar o arquivo mataria 11 testes legítimos. **Desqualificado pela mesma razão.** |
| **Marcadores inline** (`@pytest.mark.golden_nivel` nos 448) | Tecnicamente o mais limpo (marcador **junto** do teste, deleção auto-consistente). **Rejeitado**: exige editar ~448 corpos de teste numa fase cujo contrato é *"se o `V` de algum ticker mudar, saiu do escopo"*. Um `sed` em 36 arquivos é exatamente o tipo de edição que introduz um erro silencioso. Com o YAML, **zero arquivo de teste existente é tocado**. |
| **Deletar os goldens agora** | Perde a capacidade de rodá-los sob demanda e perde o registro. E o ROADMAP é explícito: *quarentenar agora, deletar quando a fase chegar*. |

**Deleção na Fase 10 (PRIM-05) fica trivial e auditável:** apagar a função de teste **e** sua linha
no `classificacao.yaml`. O check de órfão **força** a segunda edição → a deleção não pode ser
esquecida pela metade, e aparece como um diff de 2 linhas no review.

---

## BLIND-02 — ⚠️ ACHADO CRÍTICO: a spec é insatisfazível como escrita

Esta é a descoberta mais importante da pesquisa. **Resolva antes de planejar.**

### 1. A semântica de `xfail(strict=True)` está confirmada

Rodei uma sonda real em **pytest 9.0.3** `[VERIFIED: execução direta]`:

| Situação | Resultado | Suíte |
|---|---|---|
| `xfail(strict=True)` + teste **falha** | `x` (xfailed) | **verde** ✅ |
| `xfail(strict=True)` + teste **passa** | `FAILED [XPASS(strict)]` | **VERMELHA** ✅ |
| `xfail` não-strict + teste passa | `X` (xpassed) | verde |

A semântica que o BLIND-02 precisa **existe e funciona**. `xfail_strict = true` no ini torna o
`strict=True` o default global (recomendo **ambos**: o ini como rede, o `strict=True` explícito no
decorator como documentação legível). **O repo hoje tem ZERO `xfail`** e apenas 2 `parametrize` —
não há precedente nem conflito.

> **Precedente de alerta:** `test_backtest_bancos.py:19` documenta que *"o `xfail(strict=True)` que
> travava a reprovação de propósito foi REMOVIDO ao cruzar o quórum"*. Ou seja: **este repo já
> projetou um teste para deixar de reprovar.** É literalmente o Pitfall 5. O `xfail_strict` global
> é a defesa contra a repetição.

### 2. O teste **falha hoje** — mas pela razão errada

Rodei o choque de +300 bps (simultâneo em `capm.rf_local`, `ddm.g_estavel`, `motores.rim.g_terminal`)
através da **engine real** sobre o snapshot `[VERIFIED: report.analisar_acao]`:

| Ticker | V base | V +300bps | Δ | Invariante (<2%)? |
|---|---:|---:|---:|---|
| ITUB4 | 32,88 | 35,41 | **+7,69%** | NÃO |
| BBAS3 | 43,89 | 45,49 | +3,65% | NÃO |
| BBSE3 | 39,87 | 41,04 | +2,93% | NÃO |
| **BBDC4** | 13,37 | 13,63 | **+1,96%** | **SIM — passa por acidente!** |

🚨 **Duas armadilhas para o executor:**

- **O `V` SOBE**, não desce. Contra-intuitivo para "inflação destrói valor". A causa: **o
  `ke_teto = 0.13` satura**. Medi o `ke` cru vs. clampado: com `rf` base, **3 dos 4 bancos já estão
  saturados no teto**; sob o choque, **os 4 estão**. O `Ke` **não se move nem 1 bp**. Só o `g` se
  move → o spread `Ke−g` encolhe → `V` sobe. *O `ke_teto` absorve integralmente a perna do `rf`.*
- **BBDC4 passa hoje (+1,96% < 2%).** Se o plano escrever o BLIND-02 sobre o BBDC4, o
  `xfail(strict=True)` dá **XPASS → suíte vermelha imediatamente**, pelo motivo errado. **O teste
  precisa ser sobre o ITUB4** (o caso do próprio livro, e a maior violação) ou sobre a **mediana/máx
  da cesta**.

### 3. O problema de fundo: o teste, como escrito, **nunca pode ficar verde**

Rodei o RIM puro **sem clamps** (simulando a Fase 12) com o `Ke` e o `g` **exatos do livro**
(`Ke = 12,48%`, `g = 7,28%`, `ROE = 18%`) `[VERIFIED: motores.rim direto]`:

| Cenário de choque (+300 bps) | V | Δ | Invariante? |
|---|---:|---:|---|
| **A) só `Ke` e `g`** ← **literal do BLIND-02** | 31,81 | **−27,67%** | **NÃO** |
| **B) `Ke`, `g` E `ROE`** ← invariância real | 41,92 | −4,68% | NÃO (mas perto) |
| C) só `Ke` | 29,49 | −32,95% | NÃO |
| D) só `g` | 30,55 | −30,54% | NÃO |

**A álgebra explica.** A ponte auditável do próprio ENG-08:

```
P/B justo = 1 + (ROE_T − Ke) / (Ke − g)
```

| | ROE−Ke | Ke−g | P/B justo |
|---|---:|---:|---:|
| base | +0,0552 | 0,0520 | **2,062** |
| choque só em Ke,g | **+0,0252** ⬅ comprimido | 0,0520 | **1,485** ❌ |
| choque em Ke,g **e ROE** | +0,0552 | 0,0520 | **2,062** ✅ **exato** |

Chocar `Ke` e `g` preserva `(Ke−g)` mas **comprime `(ROE−Ke)` em exatamente δ**. **Invariância à
inflação exige chocar o `ROE` também** — inflação levanta o *lucro nominal*, não só a taxa de
desconto. Um `ROE` congelado num snapshot é, por construção, um `ROE` *real* sendo comparado com um
`Ke` *nominal*. (Ironia: **é a própria Doença 1, uma camada abaixo.**)

### 4. E mesmo o choque correto não alcança < 2% com o `n_fade` de hoje

O resíduo do cenário B **escala com o `n_fade`** `[VERIFIED]`:

| `n_fade` | Δ sob choque completo |
|---:|---:|
| 1 | **0,00%** (exatamente invariante) |
| 5 | −2,32% |
| **10** ← config atual | **−4,68%** |
| 20 | −8,15% |

A janela explícita desconta RI **nominal** a `Ke` **nominal** sobre um book `B0` a **custo
histórico** (não reexpresso). A identidade fechada (perpetuidade) é *exatamente* invariante; **a
janela explícita não é**. Com `n_fade = 10` — que é **1 dos 3 graus de liberdade do orçamento
BLIND-06** — **o piso é −4,68%, e o limiar de 2% é inalcançável.**

### 5. Consequência para a ordem das fases (regra dura A)

O ROADMAP afirma (Fase 11, critério 1): *"O teste BLIND-02 vira VERDE sozinho"*. **Isso não se
sustenta na mecânica**: na Fase 11 o `ke_teto` **ainda existe** (só sai na Fase 12) e continua
saturando → a perna do `rf` continua absorvida → o teste continua falhando. Pela medição,
**BLIND-02 só pode ficar verde depois da Fase 12.**

Isso **não invalida a regra dura A** (não fundir 11 e 12 — essa regra é sobre *ordem de conserto*,
provada por simulação). Mas invalida o *critério de saída* da Fase 11. Ver Q1.

---

## BLIND-03 — o mais fácil, e o único com fórmula fechada

`normalizacao.py:73-75`: com `anos_media=3`, `n=3 < 5` → `median(janela)` → **em 3 pontos, a mediana
É o ponto do meio**. Numa série geométrica pura de razão `(1+g)`, o meio é `último/(1+g)`.

**Logo o haircut tem forma fechada: `base/último − 1 = −g/(1+g)`.** Medido `[VERIFIED]`:

| g | haircut medido | `−g/(1+g)` |
|---|---:|---:|
| 5% | −4,76% | −4,76% ✅ |
| **10%** | **−9,09%** | **−9,09%** ✅ |
| 15% | −13,04% | −13,04% ✅ |

O **−9,1%** do ROADMAP está **confirmado** (é −9,09%, com `g = 10%`). E é **algébrico, não
empírico** → o assert pode ser **exato**, não uma banda frouxa.

```python
def test_normalizacao_nao_pune_crescimento():
    """BLIND-03: serie de +10%/ano PURA (zero outlier) nao pode virar base < ultimo ano menos inflacao.

    Hoje `base_normalizada(anos_media=3)` cai em `median()` de 3 pontos = O PONTO DO MEIO.
    Numa serie geometrica isso e' `ultimo/(1+g)` -> haircut = -g/(1+g) = -9,09% em g=10%.
    O modelo pune o crescedor por crescer. Vira verde na Fase 10 (PRIM-01).
    """
    serie = [100.0 * (1.10 ** i) for i in range(5)]     # +10%/ano, zero outlier
    ultimo = serie[-1]
    base = norm.base_normalizada(serie, anos_media=3, winsor=0.10)

    piso = ultimo * (1 - PI_CICLO)     # PI_CICLO = 0.0518 (IPCA medio 10a, BCB SGS 13522)
    assert base >= piso, (
        f"normalizacao pune crescimento: base {base:.2f} < ultimo-inflacao {piso:.2f} "
        f"(haircut {base/ultimo-1:+.2%}, forma fechada -g/(1+g))"
    )
```

**Status hoje:** `base = 133,10` vs `piso = 138,83` → **FALHA** (haircut −9,09%). Correto: é a
doença. `xfail(strict=True)` até a Fase 10.

> ⚠️ **Fuga por knob que o plano precisa fechar:** `anos_media` é um parâmetro. Setar
> `anos_media=1` faz o teste passar **sem consertar nada**. Duas defesas, ambas necessárias:
> (a) o teste **lê o `anos_media` do `config.yaml` de produção**, não hardcoda 3;
> (b) **`anos_media` NÃO está nos 3 graus de liberdade** (`ERP`, `n_fade`, `PIB_real`) → o teste de
> orçamento do BLIND-06 **pega** a alteração. **É o intertravamento BLIND-03 × BLIND-06 — e ele só
> funciona se os dois forem escritos na mesma fase.**

---

## BLIND-04 — metade executável hoje, metade sem substrato

### 4a. A proibição (`nenhum teste afirma ticker == R$`) — **executável agora**

É um **meta-teste AST** sobre `tests/`. Já construí e rodei o detector: **47 testes** cravam ticker +
número de nível. O teste falha listando-os; a "correção" é classificá-los como `golden_nivel` no
`classificacao.yaml` (quarentena) — **é o mesmo mecanismo do BLIND-01**, e é aí que os dois
requisitos se intertravam de forma elegante:

```python
def test_nenhum_teste_de_calibracao_crava_ticker_em_reais():
    """BLIND-04a: `assert V(TICKER) == R$ x` e' calibracao disfarcada de teste.

    Permitido SO em testes ja classificados como `golden_nivel` (quarentenados, com data de
    morte). Um teste NOVO com esse formato falha aqui — e' a porta pela qual o overfit voltaria.
    """
    ofensores = _detectar_ticker_com_valor_cravado(pathlib.Path("tests"))   # AST
    quarentenados = {k for k, v in _classificacao().items() if v == "golden_nivel"}
    novos = {o for o in ofensores if o not in quarentenados}
    assert not novos, f"teste crava ticker==R$ fora da quarentena: {sorted(novos)}"
```

**Detecção (regra exata):** `ast.walk` sobre cada `FunctionDef` `test_*`; casa se o corpo contém
**(i)** um literal string que é chave de `data/ticker_map.json` (105 tickers, **versionado**) **e**
**(ii)** um `ast.Constant` float não-trivial (∉ {0, 1, 0.5, 2}) num `Compare`/`Assert`.
⚠️ **Não use regex nua `[A-Z]{4}\d{1,2}`**: ela casa `MACD12` (falso positivo real, medido).
**Valide sempre contra `ticker_map.json`.**

### 4b. O jackknife — **não tem sobre o que operar hoje**

`tests/fixtures/fair_values_bancos.yaml` tem **4 tickers** (a cesta do overfit v2.3). **Jackknife
sobre 4 observações é estatisticamente vazio** — remover 1 de 4 move a mediana por construção.
E **o universo de 104 tickers NÃO é um artefato commitado**: `out/` está no `.gitignore`
`[VERIFIED: git check-ignore]`; o mapa dos 104 vive num artefato externo (link no REQUIREMENTS.md).

**Portanto:** o jackknife (BLIND-04b) **só ganha sentido na Fase 14** (VAL-02: cesta estratificada,
≥ 6 por arquétipo + 10 "difíceis"). Na Fase 7 escreva **o harness**, não o veredito:

- função `mediana_jackknife(valores) -> (mediana, desvio_max_ao_remover_1)` — pura, testável com
  dados sintéticos **hoje** (INVARIANTE);
- `test_nenhum_ticker_e_load_bearing` — lê `tests/fixtures/holdout_v24.yaml`; **`pytest.skip` se o
  fixture não existir** (ele só nasce na Fase 14). Não use `xfail`: a ausência do fixture não é uma
  doença a curar, é uma dependência de fase.

**Limiar:** o ROADMAP não fixa um. **Recomendação `[ASSUMIDO — precisa de confirmação do usuário]`:
a mediana de `V/FairValue` não pode mover mais que 1 pp ao remover qualquer ticker.** Com N ≥ 30
(o alvo da Fase 14) isso é folgado para dados saudáveis e aperta em qualquer ticker que domine.
**Não invente esse número na Fase 7 sem dado** — deixe o limiar como constante nomeada no topo do
arquivo, e **fixe-o na Fase 14** com a distribuição real na mão. (Fixá-lo agora seria... calibrar um
knob contra dado inexistente. Exatamente o que o marco combate.)

---

## BLIND-05 — o hook: `core.hooksPath`, não o framework `pre-commit`

### O problema que o objetivo levanta é real

`.git/hooks` **não é versionado** — confirmei: `git ls-files .git/hooks` → **0 arquivos**. Um hook
solto em `.git/hooks/pre-commit` **não protege o repositório**: some no próximo clone.

### Solução verificada: diretório versionado + `core.hooksPath`

Testei num repo descartável `[VERIFIED: git 2.39.5]` — o hook **rodou e bloqueou o commit**:

```bash
# 1. o hook vive num diretorio VERSIONADO
.githooks/pre-commit          # tracked, chmod +x

# 2. ativacao (uma vez por clone)
git config core.hooksPath .githooks
```

`core.hooksPath` existe desde o git 2.9 `[CITED: git-config docs]` e funciona no git 2.39.5 do
ambiente. **Rejeitado:** o framework `pre-commit` (pypi) — dep + ambientes isolados baixados por
rede + `.pre-commit-config.yaml`, para 15 linhas de shell. Viola o custo-zero.

### O hook (`.githooks/pre-commit`)

```sh
#!/bin/sh
# BLIND-05: config.yaml + golden/fixture no MESMO commit e' a assinatura exata de
# "calibrei o knob ate o teste passar" (o post-mortem do v2.3).
staged=$(git diff --cached --name-only)

echo "$staged" | grep -qx 'config.yaml' || exit 0
echo "$staged" | grep -qE '^tests/(fixtures/|test_)' || exit 0

# Chegou aqui: tocou os dois. Exige justificativa explicita no commit message.
msg=$(cat "$1" 2>/dev/null || git log -1 --format=%B 2>/dev/null)
just=$(printf '%s' "$msg" | sed -n 's/^Knob-Change-Justification:[[:space:]]*//p')

if [ -z "$just" ]; then
  echo "BLOQUEADO (BLIND-05): config.yaml + teste/fixture no mesmo commit."
  echo "  E' a assinatura de 'calibrei o knob ate o golden passar' (post-mortem v2.3)."
  echo "  Separe em dois commits. Se for legitimo (primitiva nova + knob + teste nascendo"
  echo "  juntos), adicione ao commit message:"
  echo "      Knob-Change-Justification: <razao ECONOMICA, sem citar ticker>"
  exit 1
fi

# A regra escrita do ROADMAP, executavel: "uma justificativa legitima nunca menciona um ticker".
if printf '%s' "$just" | grep -qE '\b[A-Z]{4}[0-9]{1,2}\b'; then
  echo "BLOQUEADO (BLIND-06): a justificativa menciona um TICKER."
  echo "  '$just'"
  echo "  Uma justificativa legitima de knob nunca menciona um ticker."
  echo "  (compare config.yaml:238 — 'Move ITUB4 ~R\$2')"
  exit 1
fi
exit 0
```

> ⚠️ **`pre-commit` recebe o path do commit-msg?** **Não** — esse é o `commit-msg` hook. Duas
> opções para o planner: **(a)** dividir em `pre-commit` (detecta o co-change, exporta um flag) +
> `commit-msg` (valida o trailer); ou **(b) mais simples: fazer tudo no `commit-msg` hook**, que
> recebe o arquivo da mensagem **e** consegue ler o índice via `git diff --cached`. **Recomendo
> (b)** — um hook só, `.githooks/commit-msg`. O nome "pre-commit" do BLIND-05 é descritivo, não
> normativo. `[VERIFIED: git hooks docs — commit-msg recebe $1 = path do arquivo de mensagem]`

### O hook é bypassável — precisa de backstop

`git commit --no-verify` pula qualquer hook. E **não existe CI neste repo** (`.github/workflows`
não existe `[VERIFIED]`). Sem CI, o backstop tem que ser **um teste**:

```python
def test_hook_do_blind05_esta_instalado():
    """O hook nao pode ser silenciosamente desinstalado (core.hooksPath e' estado LOCAL, nao versionado)."""
    out = subprocess.run(["git", "config", "--get", "core.hooksPath"],
                         capture_output=True, text=True).stdout.strip()
    assert out == ".githooks", (
        "core.hooksPath nao aponta para .githooks -> o hook do BLIND-05 esta INATIVO. "
        "Rode: git config core.hooksPath .githooks"
    )

def test_historico_sem_co_change_knob_e_golden():
    """Backstop de --no-verify: varre os commits do marco v2.4 atras da assinatura do overfit."""
    # git log --format=%h <base_v24>..HEAD ; para cada, git show --name-only
    ...
```

### Prova histórica de que a regra tem alvo real

Varri os **676 commits** do repo `[VERIFIED: git log + git show --name-only]`. **5 commits** tocam
`config.yaml` **e** `tests/` juntos:

| Commit | Data | Assunto | Leitura |
|---|---|---|---|
| **`5cd3b61`** | 2026-07-13 | *"ROE through-cycle no report injetado via `roe_terminal` + knob"* | 🚨 **É o overfit do v2.3.** Exatamente o que BLIND-05 existe para barrar |
| `d2f2212` | 2026-06-29 | pivôs fractal de Williams | Feature nova + knob + teste nascendo juntos — **legítimo** |
| `be568cb` | 2026-06-28 | `rf` do Ke = Selic through-the-cycle | Fronteiriço |
| `a26fc0c` | 2026-06-26 | *"primitiva de normalização + knob de config + golden unitário"* | **Legítimo** (primitiva + knob + teste nascem juntos) |
| `0784d77` | 2026-06-04 | repo inicial | Trivial |

**~2 de 5 são falsos positivos legítimos** → o hook **precisa** da escapatória, e ela precisa ser
**barulhenta e auditável** (o trailer `Knob-Change-Justification:`), não um `--no-verify` silencioso.
O trailer fica no `git log` para sempre — é revisável.

---

## BLIND-06 — o orçamento de knobs

### Correção factual: `motores:` tem **11 chaves, não ~20**

`[VERIFIED: yaml.safe_load + walk recursivo]`

```
motores.rim.erp_banco = 0.045          motores.rim.g_terminal = 0.025
motores.rim.ke_piso = 0.11             motores.rim.ke_g_spread_min = 0.03
motores.rim.ke_teto = 0.13             motores.rim.roe_terminal_stat = 'mediana'
motores.rim.n_fade = 10                motores.ciclica.anos_media = 10
motores.rim.excesso_sustentavel = 0.045  motores.ciclica.winsor = 0.1
                                       motores.crescimento.n_anos_explicito = 10
```
**11 folhas.** A regra dura C ("~20 → ≤5") está mal-calibrada na origem. A meta **≤5 continua
válida e continua sendo um corte real** (11 → 5), mas o plano **não deve reproduzir o "~20"**, senão
a Fase 13 vai "contar" uma deleção que nunca existiu.

### O escopo do orçamento precisa ser DECLARADO

"Exatamente 3 graus de liberdade" só é testável contra um **conjunto declarado**. A superfície de
knobs que **afeta o `V`** hoje:

| Bloco | Folhas | No orçamento? |
|---|---:|---|
| `motores` | 11 | `n_fade` ✅ · os outros 10 morrem/derivam |
| `capm` | 12 | `ERP` ✅ (hoje `erp_local` **e** `motores.rim.erp_banco` — **dois ERPs!**) |
| `ddm` | 5 | `PIB_real` ✅ (hoje `g_estavel` = 2,5% real, digitado) |
| `normalizacao` | 2 | ❌ `anos_media` **não** é grau de liberdade (trava do BLIND-03) |
| **Total valuation** | **30** | **→ 3** |
| (`screening` 33, `indicadores` 16, `score` 11, `padroes` 6, `selo` 3, `arquetipo` 5, `veredito` 4, `universo` 2) | 80 | **Fora do escopo** — não afetam `V` |

`config.yaml` tem **110 folhas no total**. O orçamento se aplica às **30 de valuation**. **O plano
precisa declarar essa fronteira explicitamente**, senão o teste ou é vazio ou é impossível.

### `calibracao.lock.yaml` + o teste

```yaml
# calibracao.lock.yaml — BLIND-06. Orcamento: EXATAMENTE 3 graus de liberdade.
# Regra: "uma justificativa legitima de knob nunca menciona um ticker."
escopo:                     # os blocos do config.yaml que afetam V
  - motores
  - capm
  - ddm
  - normalizacao
graus_de_liberdade:         # os UNICOS 3 valores calibraveis do sistema
  ERP:      {caminho: capm.erp_local,   valor: 0.045, fonte: "Damodaran mature market"}
  n_fade:   {caminho: motores.rim.n_fade, valor: 10,  fonte: "horizonte de fade do excesso de ROE"}
  PIB_real: {caminho: ddm.pib_real,     valor: 0.020, fonte: "constante estrutural, nao serie ajustavel"}
```

```python
def test_orcamento_de_knobs_e_exatamente_3():
    lock = _lock(); cfg = _config()
    livres = _folhas_calibraveis(cfg, escopo=lock["escopo"]) - _derivados(cfg)
    assert len(livres) == 3, f"orcamento estourado: {sorted(livres)} (esperado 3)"

def test_knobs_batem_com_o_lock():
    """Mudar o VALOR de um grau de liberdade exige mexer no lock — no MESMO diff, revisavel."""
    for nome, spec in _lock()["graus_de_liberdade"].items():
        assert _get(_config(), spec["caminho"]) == spec["valor"], f"{nome} divergiu do lock"

def test_nenhuma_justificativa_de_knob_menciona_ticker():
    """A regra escrita do ROADMAP, executavel. FALHA HOJE (10 linhas ofensoras)."""
    ofensores = _comentarios_com_ticker("config.yaml", escopo=_lock()["escopo"])
    assert not ofensores, f"justificativa de knob menciona ticker: {ofensores}"
```

### O teste do ticker **falha hoje** — e é bom que falhe

Varri os comentários do `config.yaml` contra `data/ticker_map.json`
`[VERIFIED: 10 linhas, MACD12 eliminado]`:

| Linha | Tickers | Trecho |
|---|---|---|
| 218 | WEGE3, RADL3, ABEV3, LREN3 | `(WEGE3 0.174, RADL3 0.156, ...)` — bloco `arquetipo` (ilustrativo) |
| 219 | VALE3, GGBR4, SUZB3, PETR4 | idem |
| **233** | ITUB4 | *"É a alavanca que **destrava o ITUB4** do 'evitar'"* 🚨 |
| **238** | ITUB4 | *"**Move ITUB4 ~R$2**"* 🚨 **o exemplo canônico do ROADMAP** |
| **240** | ITUB4 | *"golden ITUB4 (VPA~22...)"* 🚨 |
| **242** | ITUB4, BBAS3, BBSE3, BBDC4 | *"a calibração dos knobs contra a cesta (ITUB4/BBAS3/...)"* 🚨 |
| **255–257** | BBAS3, BBDC4, ITUB4 | *"cobre BBAS3 ... deixa o **ITUB4 bit-idêntico**"* 🚨 |
| **259** | ITUB4 | *"NÃO mexer nos knobs acima: **mudariam o ITUB4**"* 🚨 |

**8 das 10 estão no bloco `motores.rim`** — a superfície exata do overfit v2.3. Limpar esses
comentários **não muda nenhum valor** (são comentários) → **é seguro nesta fase** e não viola o
anti-goal "não move o `V` de ticker nenhum`. Lines 218–219 (bloco `arquetipo`, ranges ilustrativos
de beta) são discutíveis: **sugiro manter o escopo do teste nos 4 blocos de valuation**, o que as
deixa fora e evita uma limpeza cosmética sem valor.

---

## Don't Hand-Roll

| Problema | Não construa | Use | Por quê |
|---|---|---|---|
| Deseleção de testes | Flag custom / `sys.argv` / env var | `pytest` markers + `addopts` | Nativo, compõe com `-m`, documentado |
| "XPASS deve quebrar a suíte" | `if resultado: raise` manual | `xfail(strict=True)` + `xfail_strict = true` | **Verificado** funcionando; é a semântica exata |
| Detectar teste não classificado | Script externo pós-hoc | `pytest_collection_modifyitems` | Roda **na coleta**, in-process, custo ~0 |
| Parsear os testes p/ achar goldens | Regex sobre o fonte | **`ast`** (stdlib) | Regex casa `MACD12` como ticker (**falso positivo real, medido**) |
| Distribuir git hooks | Copiar p/ `.git/hooks` no README | `.githooks/` + `core.hooksPath` | `.git/hooks` **não é versionado** (0 arquivos, verificado) |
| Snapshot/golden testing | `pytest-golden`, `syrupy` | — | Estamos **desmontando** goldens, não gerenciando-os |
| Validação de invariante algébrico | `hypothesis` | assert exato | Os invariantes têm **forma fechada** (`−g/(1+g)`) |

**Insight central:** *toda* a Fase 7 é implementável com **pytest + PyYAML + `ast` + `git`** — tudo
já instalado. **Zero `pip install`.** Se o plano propuser uma dep nova, é sinal de que se procurou
uma abstração onde bastavam 20 linhas.

---

## Runtime State Inventory

Fase de tooling/processo — mas **tem** estado fora do git, e é justamente aí que ela pode falhar
silenciosamente.

| Categoria | Encontrado | Ação |
|---|---|---|
| **Estado registrado no SO/repo** | 🚨 **`core.hooksPath` é config LOCAL do git** (`.git/config`), **não versionada**. Hoje: **não configurado** (verificado). Um `git clone` novo **não tem o hook do BLIND-05**. | Hook versionado em `.githooks/` + **teste que falha se `core.hooksPath != .githooks`** (§ BLIND-05). Sem esse teste, a proteção é fantasma |
| **Dados armazenados** | `tests/fixtures/snapshot_bancos_2026-07-12.yaml` (versionado, 4 tickers, **ITUB4 2019 = 10M ações**) — regenerado na Fase 9 (DATA-06), **não nesta** | Nenhuma nesta fase (**só classificar** os testes que o consomem) |
| **Config de serviço vivo** | Nenhum. App Streamlit lê `config.yaml` do repo; sem estado externo | Nenhuma |
| **Secrets / env vars** | Nenhum relevante (projeto usa só dados públicos gratuitos) | Nenhuma |
| **Artefatos de build** | `out/` (**gitignored** — não é fonte de verdade); `.pytest_cache/`; `__pycache__/` | Nenhuma. ⚠️ **`out/` ser gitignored é o motivo de o jackknife (BLIND-04b) não ter dado** |

**A pergunta canônica:** *depois que os 6 requisitos estiverem no repo, que estado runtime ainda tem
a proteção desligada?* → **Exatamente um: `core.hooksPath`.** É o único item desta fase que exige um
comando manual por clone. Por isso o teste-backstop não é opcional.

---

## Common Pitfalls

### Pitfall 1 — Escrever o BLIND-02 sobre o ticker errado (BBDC4) 🚨
**O que dá errado:** BBDC4 varia **+1,96%** hoje, **abaixo do limiar de 2%**. Com
`xfail(strict=True)` → **XPASS → suíte vermelha na hora**, e o executor "conserta" afrouxando.
**Como evitar:** escrever sobre o **ITUB4** (+7,69%, e é o caso do livro) ou sobre a **mediana/máx da
cesta**. **Nunca sobre um ticker só, sem checar a margem.**
**Sinal de alerta:** o teste fica vermelho por `XPASS` em vez de `xfail` logo no primeiro commit.

### Pitfall 2 — Assumir que o `V` CAI sob choque de inflação
**O que dá errado:** o executor escreve `assert V_chocado < V_base` e o teste falha "ao contrário".
**Por quê:** o `ke_teto = 0.13` **satura** (3 de 4 bancos já no teto na base; 4 de 4 sob choque). O
`Ke` **não se move**; só o `g` → spread encolhe → **`V` SOBE**.
**Como evitar:** o assert é sobre `abs(ΔV) < limiar`, **nunca sobre o sinal**.

### Pitfall 3 — "Atualizar" o golden em vez de quarentenar (Armadilha 3, a mais provável)
**O que dá errado:** o executor vê `ITUB4: 32.88` falhar e escreve `ITUB4: 27.40`.
**Como evitar:** o marcador `golden_nivel` **não tem valor a atualizar** — o teste é *deselecionado*,
não reescrito. E o `classificacao.yaml` carrega o comentário `-> DELETAR na Fase 10`.
**Sinal de alerta:** qualquer diff que **mude um número** dentro de um teste `golden_nivel`.

### Pitfall 4 — Deletar só **um** dos três goldens do ITUB4
**O que dá errado:** o ROADMAP só nomeia `32.88`. Mas existem **três** travas de nível do ITUB4:
`test_backtest_bancos.py:121` (32.88 ± 0.20), `:49-50` (banda 30–40) e `test_motores.py:238`
(banda 30–40). Deletar só o primeiro deixa a fase "concluída" com o método ainda travado.
**Como evitar:** o `classificacao.yaml` marca **os três** com `# -> DELETAR na Fase 10`; a Fase 10
faz `pytest -m golden_nivel` e confirma **zero** restantes com ITUB4.

### Pitfall 5 — Fugir do BLIND-03 pelo knob `anos_media`
**O que dá errado:** `anos_media: 1` faz o teste passar sem consertar `normalizacao.py`.
**Como evitar:** o teste lê o `anos_media` **do config de produção**; e `anos_media` **não está** nos
3 graus de liberdade → BLIND-06 pega. **Os dois testes precisam nascer na mesma fase** ou o
intertravamento não existe.

### Pitfall 6 — O hook que não protege ninguém
**O que dá errado:** hook em `.git/hooks/pre-commit` → some no próximo clone; ou hook instalado mas
`core.hooksPath` nunca configurado → **proteção fantasma**.
**Como evitar:** `.githooks/` versionado + teste que falha se `core.hooksPath != .githooks`.
**Sinal de alerta:** ninguém nunca viu o hook bloquear nada.

### Pitfall 7 — Regex nua para detectar ticker
**O que dá errado:** `[A-Z]{4}\d{1,2}` casa **`MACD12`** (falso positivo **real**, medido em
`config.yaml:134`).
**Como evitar:** validar contra `data/ticker_map.json` (105 tickers, versionado).

---

## Code Examples

### BLIND-02 — perturbação de config (o config é injetado, não global)

```python
# Fonte: verificado contra report.analisar_acao(c, cfg) — assinatura em report.py:350
import copy, yaml
from analista.backtest import carregar_snapshot
from analista.report import report

def _cfg_base():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    empresas, rf_local = carregar_snapshot("tests/fixtures/snapshot_bancos_2026-07-12.yaml")
    cfg["capm"]["rf_local"] = rf_local          # espelha rodar_cesta
    return empresas, cfg

def _choque_inflacao(cfg, bps):
    """+bps SIMULTANEO em rf e em todo g estrutural. (E no ROE? -> ver Open Question Q1.)"""
    c = copy.deepcopy(cfg)                       # deepcopy: NAO mutar o cfg base
    d = bps / 10_000
    c["capm"]["rf_local"] += d
    c["ddm"]["g_estavel"] += d
    c["motores"]["rim"]["g_terminal"] += d
    return c
```
**Nenhum monkeypatch é necessário** — o config é um `dict` passado por argumento. Verificado.

### O canário (PITFALLS.md P5.4) — provar que a suíte nova CONSEGUE reprovar

```python
def test_a_suite_reage_a_um_knob():
    """Meta-teste: depois da quarentena, a suite ainda detecta um erro de metodo?

    Sem isto, "448 verdes" pode significar "448 deselecionados". O canario garante que
    a suite nova nao e' MAIS decorativa que a velha.
    """
    empresas, cfg = _cfg_base()
    sabotado = copy.deepcopy(cfg)
    sabotado["capm"]["erp_local"] *= 2          # dobra o ERP: um erro grosseiro de metodo
    v0 = report.analisar_acao(empresas[0], cfg).intrinseco_motor
    v1 = report.analisar_acao(empresas[0], sabotado).intrinseco_motor
    assert abs(v1 / v0 - 1) > 0.05, "a suite nao reage a um knob dobrado -> e' decorativa"
```

---

## State of the Art

| Abordagem antiga | Abordagem atual | Impacto |
|---|---|---|
| `@pytest.mark.skip` p/ testes indesejados | **`xfail(strict=True)`** + `xfail_strict` no ini | `skip` esconde; `xfail(strict)` **avisa quando o teste voltar a passar** — é o que faz o BLIND-02 virar verde *sozinho* |
| Hooks copiados em `.git/hooks` | **`core.hooksPath`** (git ≥ 2.9) | Hook **versionado** e revisável |
| Golden por teste | **Golden master + diff aprovado** (PITFALLS P5.2) | O *delta* vira o artefato revisado, não o nível. ⚠️ **Requer um baseline de 104 tickers que NÃO existe commitado hoje** — ver Q3 |

---

## Assumptions Log

| # | Afirmação | Seção | Risco se errado |
|---|---|---|---|
| A1 | Limiar do jackknife = **mediana não move > 1 pp** ao remover 1 ticker | BLIND-04b | Limiar frouxo → jackknife não reprova nada; apertado → falha por ruído. **Fixar na Fase 14 com a distribuição real** |
| A2 | `π_ciclo = 5,18%` (IPCA 10a, BCB SGS 13522) é o deflator certo do piso do BLIND-03 | BLIND-03 | Muda o piso; **não muda o sinal** (haircut é −9,09%, folgado vs. qualquer π razoável) |
| A3 | Os 125 testes "outros" (indicators/UI/home/glossário) podem ser classificados **em bloco por arquivo** | Inventário | Se algum tocar `V` indiretamente, um golden escapa. **Mitigação: rodar o detector AST neles também** (achou 3 em `test_home_feed`) |
| A4 | Limpar os comentários com ticker do `config.yaml` é seguro (não muda valor) | BLIND-06 | Baixo — são comentários. Mas **confirme que nenhum é lido por código** (YAML: não são) |
| A5 | O escopo do orçamento de knobs = `motores` + `capm` + `ddm` + `normalizacao` (30 folhas) | BLIND-06 | Se `screening`/`veredito` afetarem `V`, o orçamento tem furo. **`veredito.margem_seguranca` merece um olhar** — vira controle do usuário no ENG-06 |

---

## Open Questions — **TODAS RESOLVIDAS** (2026-07-13, decisão do usuário)

| # | Resolução | Onde vive agora |
|---|---|---|
| **Q1** | **Opção (a) + (b)** — invariante algébrico exato **mais** o `xfail(strict)` sobre a engine com limiar **5%**, choque em `rf`+`g_cap`+**`ROE`**. | `REQUIREMENTS.md` BLIND-02 · `ROADMAP.md` Fase 7 crit. 2 · plano `07-02` |
| **Q2** | **Sim, o ROADMAP estava errado.** BLIND-02 vira verde na **Fase 12**, não na 11 (o `ke_teto` satura até lá). Regra dura (A) intacta. | `ROADMAP.md` Fase 11 crit. 1 · `REQUIREMENTS.md` GROW-02 |
| **Q3** | **Fora do escopo da Fase 7.** O golden master dos 104 tickers não é requisito BLIND — é **pré-requisito das Fases 8/9**. Handoff registrado. | SUMMARY dos planos `07-01` e `07-05` |
| **Q4** | **Sim, é um 4º grau de liberdade escondido.** `veredito.margem_seguranca` é congelada no lock como **`user_control`**, não como `grau_de_liberdade`. Morre por construção no ENG-06. | plano `07-05` (`calibracao.lock.yaml`) |

<details>
<summary>Texto original das perguntas (mantido para rastreabilidade)</summary>

### Q1 🚨 — BLIND-02: a spec literal é insatisfazível. Qual formulação vale?
**O que sabemos (medido):** chocar só `rf` e `g_cap` → **−27,67%** mesmo com `Ke`/`g` perfeitos e
zero clamps, porque `(ROE−Ke)` é comprimido. Chocar `ROE` junto → invariância **exata** na identidade
`P/B justo`, mas **−4,68%** no RIM com `n_fade = 10` (e **0,00%** com `n_fade = 1`).
**O que está em aberto:** três caminhos, e a escolha **muda o que o teste afirma e quando ele vira
verde**:

| Opção | Teste | Fica verde quando | Custo |
|---|---|---|---|
| **(a)** Invariante sobre a **identidade fechada** `P/B justo = 1 + (ROE−Ke)/(Ke−g)` sob choque em `ROE`,`Ke`,`g` | Exato (< 1e-9) | **Já passa hoje** (é álgebra pura) → **não serve de `xfail`** | Não testa a engine |
| **(b)** Choque completo (`rf`, `g_cap`, **`ROE`**) na **engine**, limiar **5%** | `xfail(strict)` | Fase 12 (quando o `ke_teto` sai) | Limiar 5% ≠ os 2% do ROADMAP |
| **(c)** Choque completo + limiar 2%, **exigindo `n_fade ≤ 4`** | `xfail(strict)` | Fase 12 **e** só se o `n_fade` cair | Amarra um grau de liberdade a um teste |

**Recomendação:** **(a) + (b) juntos** — (a) como `invariante` (barato, knob-proof, guarda a ponte
auditável do ENG-08) e (b) como o `golden`/`xfail` do BLIND-02, **com limiar 5%** e um comentário
explicando que o piso de −4,68% é estrutural em `n_fade = 10`. **Isto NÃO é "afrouxar tolerância"**
(Pitfall 5) — é **especificar um limiar alcançável na primeira escrita**, com a medição na mão. O
proibido é *mexer no limiar depois que o teste ficar vermelho*.
**Precisa de decisão do usuário** — muda um critério de aceite do ROADMAP.

### Q2 — O critério de saída da Fase 11 está errado?
O ROADMAP diz *"BLIND-02 vira VERDE sozinho na Fase 11"*. **Pela mecânica medida, não vira**: o
`ke_teto` só sai na **Fase 12**, e enquanto ele saturar, a perna do `rf` é absorvida.
**Recomendação:** o BLIND-02 vira verde na **Fase 12**. **A regra dura A (não fundir 11 e 12)
continua válida** — ela é sobre a *ordem do conserto*, provada por simulação, não sobre qual teste
fica verde onde. Sugiro que o plano registre isso e o ROADMAP/REQUIREMENTS sejam corrigidos
(GROW-02 e o critério 1 da Fase 11).

### Q3 — O golden master de 104 tickers (PITFALLS P5.2) é escopo da Fase 7?
`PITFALLS.md:255` recomenda congelar a saída dos 104 tickers em
`tests/fixtures/baseline_v2.3.json` **antes de tocar no código**. Mas: (i) **não é um requisito
BLIND**; (ii) exige **captura ao vivo** (CVM+Yahoo+BCB), como `capturar_snapshot_bancos.py`;
(iii) `out/` é gitignored → **não existe baseline hoje**; (iv) seria o substrato do jackknife
(BLIND-04b).
**Recomendação:** **fora do escopo da Fase 7** (não é BLIND-01..06). Mas é **pré-requisito da Fase
8/9** — sem baseline, "os asserts viram verde ticker a ticker" não é mensurável. **Sinalize ao
planner do marco**, não a esta fase.

### Q4 — `veredito.margem_seguranca` (0.15) consome grau de liberdade?
Está fora dos 3 (`ERP`, `n_fade`, `PIB_real`) mas **multiplica o `V`** — é exatamente a Armadilha 4.
O ENG-06 a transforma em **controle do usuário** (morre por construção). **Até lá, ela é um knob
livre de fato.** O teste do BLIND-06 deve **congelá-la explicitamente** (no lock, marcada como
`user_control`, não `grau_de_liberdade`), senão há um 4º grau de liberdade escondido.

</details>

---

## Environment Availability

| Dependência | Requerida por | Disponível | Versão | Fallback |
|---|---|---|---|---|
| pytest | tudo | ✅ | **9.0.3** | — |
| PyYAML | classificacao.yaml, lock | ✅ | 6.0.3 | — |
| `git` c/ `core.hooksPath` | BLIND-05 | ✅ | **2.39.5** (feature desde 2.9) | — |
| `ast`, `re`, `subprocess`, `pathlib` | BLIND-04a, BLIND-06 | ✅ | stdlib | — |
| pandas / numpy | engine (indireto) | ✅ | pandas 3.0.3 | — |
| `pre-commit` (framework) | — | ❌ | — | **Não é necessário** — `core.hooksPath` cobre |
| CI (GitHub Actions) | backstop de `--no-verify` | ❌ **não existe** | — | **Teste-backstop** (§ BLIND-05) |

**Faltando, sem fallback:** nenhum.
**Faltando, com fallback:** CI → substituído por teste-backstop in-suite. **`pip install` não roda
nesta fase.**

---

## Validation Architecture

### Test Framework

| Propriedade | Valor |
|---|---|
| Framework | **pytest 9.0.3** |
| Config | `pyproject.toml` → `[tool.pytest.ini_options]` (**`pythonpath=["src"]`, `testpaths=["tests"]`** — sem markers, sem addopts, sem `xfail_strict` hoje) |
| `conftest.py` | **NÃO EXISTE** — será criado nesta fase (Wave 0) |
| Comando rápido | `python -m pytest -q` |
| Suíte completa | `python -m pytest -q -m ""` (inclui quarentenados) |
| **Baseline medido** | **448 passed in 4,23s** — suíte rápida, sem preocupação de sampling |

### Phase Requirements → Test Map

| Req | Comportamento | Tipo | Comando | Existe? |
|---|---|---|---|---|
| BLIND-01 | 448 testes classificados; goldens deselecionados | infra + meta | `pytest -q` (verde, N deselecionados) · `pytest -m golden_nivel` | ❌ Wave 0 |
| BLIND-01 | teste não classificado quebra a coleta | meta | `pytest -q` → `UsageError` | ❌ Wave 0 |
| BLIND-02 | invariância à inflação (**ver Q1**) | unit (engine) | `pytest -m "" -k invariancia_inflacao` → **xfailed** | ❌ Wave 1 |
| BLIND-03 | normalização não pune crescimento | unit (puro) | `pytest -m "" -k pune_crescimento` → **xfailed** | ❌ Wave 1 |
| BLIND-04a | nenhum teste crava `ticker == R$` fora da quarentena | meta (AST) | `pytest -k crava_ticker` | ❌ Wave 1 |
| BLIND-04b | jackknife: nenhum ticker é load-bearing | unit + harness | `pytest -k load_bearing` → **skipped** (fixture só na Fase 14) | ❌ Wave 1 |
| BLIND-05 | hook bloqueia co-change config+golden | integration (git) | `pytest -k hook_do_blind05` + teste manual de commit | ❌ Wave 2 |
| BLIND-06 | exatamente 3 graus de liberdade | unit (config) | `pytest -k orcamento_de_knobs` | ❌ Wave 2 |
| BLIND-06 | justificativa de knob não menciona ticker | unit (config) | `pytest -k justificativa` → **falha hoje (10 linhas)** | ❌ Wave 2 |
| (meta) | **canário**: a suíte consegue reprovar | meta | `pytest -k suite_reage` | ❌ Wave 2 |

### Estado esperado da suíte ao fim da Fase 7

| Estado | Contagem | Significado |
|---|---|---|
| passed | 448 − Q + novos | Q = quarentenados |
| **deselected** | **Q** (a classificar; **≥ 47**, provavelmente 50–150) | Goldens de nível — **não bloqueiam o marco** |
| **xfailed** | **2** (BLIND-02, BLIND-03) | **As duas doenças, escritas como código** |
| skipped | 1 (BLIND-04b jackknife) | Aguarda a cesta da Fase 14 |
| **failed** | **0** | ⚠️ **Inclusive o teste do ticker no `config.yaml`** — logo **a limpeza dos comentários (linhas 233–259) faz parte desta fase** |

### Sampling Rate
- **Por commit:** `python -m pytest -q` (4,23s — roda inteira, sem sampling)
- **Por wave:** `python -m pytest -q -m ""` (inclui quarentenados — confirma que ainda rodam)
- **Portão da fase:** suíte verde + **exatamente 2 xfailed** + `pytest -m golden_nivel` roda e falha
  como esperado + `git config --get core.hooksPath` = `.githooks`

### Wave 0 Gaps (não existem hoje)
- [ ] `tests/conftest.py` — **não existe** (aplica marcadores + impõe completude)
- [ ] `tests/classificacao.yaml` — **não existe** (448 entradas; BLIND-01)
- [ ] `pyproject.toml` — acrescentar `markers`, `addopts`, `xfail_strict`
- [ ] `calibracao.lock.yaml` — **não existe** (BLIND-06)
- [ ] `.githooks/commit-msg` — **não existe** (BLIND-05)
- [ ] Script bootstrap da classificação (detector AST → primeira versão do YAML, **auditada à mão**)

---

## Security Domain

Fase sem superfície de ataque: sem entrada de usuário, sem rede, sem authn/authz, sem cripto,
sem persistência. Todo o código novo é **test harness + hook de git local**.

| ASVS | Aplica | Controle |
|---|---|---|
| V2 Authentication | não | — |
| V3 Session | não | — |
| V4 Access Control | não | — |
| V5 Input Validation | **marginal** | `classificacao.yaml` / `calibracao.lock.yaml` são **arquivos do repo** (trusted). Ainda assim: `yaml.safe_load`, **nunca `yaml.load`** — o repo já usa `safe_load` em todos os call-sites ✅ |
| V6 Cryptography | não | — |

**Única nota real:** o hook roda `sh` sobre o commit message. **Não interpole a mensagem em `eval`**
— o exemplo em § BLIND-05 usa `printf '%s' "$msg" | grep`, sem `eval`, sem expansão de comando.

---

## Sources

### Primárias (ALTA confiança — execução direta neste repo, 2026-07-13)
- `pytest --collect-only -q` → **448 testes**; `pytest -q` → **448 passed in 4.23s**
- Sonda `xfail(strict=True)` em pytest 9.0.3 → **XPASS(strict) = FAILED** (verificado)
- Sonda quarentena (marker + `addopts` + `conftest`) → 3 modos verificados E2E
- `report.analisar_acao(c, cfg)` sob choque de +300 bps → ITUB4 **+7,69%**, BBDC4 **+1,96%**
- `motores.rim(...)` sem clamps, alvos do livro → choque literal **−27,67%**; c/ ROE **−4,68%**
- `normalizacao.base_normalizada([+10%/ano], anos_media=3)` → haircut **−9,09%** = `−g/(1+g)`
- `yaml.safe_load(config.yaml)` → `motores` = **11 folhas**; total = **110 folhas**
- `yaml.safe_load(snapshot_bancos)` → **ITUB4 2019 = 10.004.676 ações**
- `git log` (676 commits) + `git show --name-only` → **5 co-changes** `config.yaml` + `tests/`
- `git config core.hooksPath` em repo de teste → hook **versionado bloqueia o commit** (git 2.39.5)
- Detector AST sobre `tests/` → **47** testes com ticker + número de nível
- Scan de comentários do `config.yaml` vs `data/ticker_map.json` → **10 linhas** com ticker

### Secundárias (MÉDIA)
- `.planning/research/PITFALLS.md` (P1.4 hook, P1.5 lock, P5.1 classificação, P5.2 golden master,
  P5.4 canário) — **incorporado**; corrigi 2 line-numbers off-by-one (237→238, 258→259)
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`
- Docs do git (`core.hooksPath` desde 2.9; `commit-msg` recebe `$1`) `[CITED: git-scm docs]`

### Não verificado
- **"~150 goldens de nível"** — não reproduzível por nenhuma regra mecânica. Ver § Inventário
- **"`motores:` ~20 chaves"** — **refutado** (são 11)
- **"BLIND-02 vira verde na Fase 11"** — **refutado pela mecânica** (Q2)

---

## Metadata

**Confiança por área:**

| Área | Nível | Razão |
|---|---|---|
| Inventário da suíte | **ALTA** | Contado por `--collect-only` + AST |
| Mecanismo de quarentena | **ALTA** | Validado E2E, 5 modos |
| `xfail(strict)` | **ALTA** | Sonda executada em pytest 9.0.3 |
| BLIND-03 (haircut) | **ALTA** | Fórmula fechada, bate com a medição em 3 valores de `g` |
| BLIND-02 (diagnóstico) | **ALTA** | Medido na engine **e** explicado pela álgebra |
| BLIND-02 (**qual teste escrever**) | **BAIXA** | **Bloqueado na Q1 — precisa de decisão** |
| BLIND-05 (hook) | **ALTA** | `core.hooksPath` testado; 676 commits varridos |
| BLIND-06 (contagem) | **ALTA** | `yaml.safe_load` + walk |
| BLIND-04b (limiar do jackknife) | **BAIXA** | **Sem dado** até a Fase 14 |
| "~150 goldens" | **REFUTADO** | 47 (mecânico) / 271 (caminho de valuation) |

**Data:** 2026-07-13 · **Válido até:** ~2026-08-13 (estável: pytest/git não se movem rápido; o
inventário de testes muda a cada commit — **recontar se a fase começar depois de novos commits em
`tests/`**)
</content>
</invoke>
