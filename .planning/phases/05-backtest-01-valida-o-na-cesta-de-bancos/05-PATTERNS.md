# Phase 5: BACKTEST-01 — Validação na cesta de bancos - Pattern Map

**Mapped:** 2026-07-12
**Files analyzed:** 4 new artifacts (1 test, 2 YAML fixtures, 1 script) + 1 shared harness function
**Analogs found:** 4 / 4 (2 exact, 2 role/shape-match)

**Escopo cirúrgico:** esta fase só CRIA artefatos novos (teste + fixtures + script). Nenhum
arquivo de motor é tocado (`core/motores.py`, `core/lentes.py`, `core/ddm.py`, `report/selo.py`,
`config.yaml` ficam READ-ONLY, exceto se o loop D-12 disparar). Todos os analogs abaixo são lidos
verbatim; o planner deve LIFTAR os excerpts, não parafrasear.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tests/test_backtest_bancos.py` | test | batch / transform (golden offline) | `tests/test_vulc3_regressao.py` | exact |
| `tests/fixtures/snapshot_bancos_2026-07-12.yaml` | fixture (frozen data) | file-I/O | `_itub4_live_like()` em `tests/test_vulc3_regressao.py:160-175` (forma serializada) | shape-match |
| `tests/fixtures/fair_values_bancos.yaml` | fixture (config data) | file-I/O | `config.yaml` (forma YAML por-chave) + campo novo | partial (artefato novo) |
| `scripts/backtest_bancos.py` | script / CLI | batch → file-I/O (markdown) | `cli.py::cmd_analyze` + `_montar` (`cli.py:52-87`) | role-match |
| `rodar_cesta()` (fn compartilhada teste↔script) | utility | transform | `cli.py::cmd_rank` loop (`cli.py:150-183`) | role-match |

**Diretórios novos a criar:** `tests/fixtures/` e `scripts/` — nenhum existe hoje (verificado via `ls`).

---

## Pattern Assignments

### `tests/test_backtest_bancos.py` (test, golden offline)

**Analog:** `tests/test_vulc3_regressao.py` — molde 1:1. Copiar estilo verbatim.

**Imports + ROOT + `_cfg()` pattern** (`test_vulc3_regressao.py:20-36`):
```python
import math
import os

import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)
```
> Nota: `ROOT` sobe 2 níveis de `tests/`, chegando na raiz do projeto onde vive `config.yaml`.
> Para ler os fixtures, usar `os.path.join(ROOT, "tests", "fixtures", "<arquivo>.yaml")`.

**Construção offline de CompanyData + dispatch + gate numérico** (`test_vulc3_regressao.py:160-188`):
```python
def _itub4_live_like() -> CompanyData:
    c = CompanyData(ticker="ITUB4", nome="Itaú (live-like)", setor="Bancos", anos=_anos())
    for a in _anos():
        c.lucro_liquido[a] = 3667.0        # ROE = 3667/19000 ≈ 0,193
        c.patrimonio_liquido[a] = 19000.0  # VPA = 19000/1000 = 19,0
        c.dividendos[a] = 1712.0           # payout ≈ 0,467 → retenção ≈ 0,533
        c.num_acoes[a] = 1000.0
        c.vendas_liquidas[a] = 14000.0
        c.fco[a] = 4400.0
    c.preco_atual = 44.30
    c.beta = 1.0
    return c


def test_rim_itub4_dispatch_banda():
    cfg = _cfg()
    a = report.analisar_acao(_itub4_live_like(), cfg)
    assert a.arquetipo == "financeira"
    assert a.motor == "rim"
    assert a.intrinseco_motor is not None
    assert a.intrinseco_motor > 30.0
```
> **Chave de tudo:** o número validado é `a.intrinseco_motor` (populado quando `a.motor == "rim"`).
> O teste deve LER `a.arquetipo`/`a.motor` por ticker antes de comparar — nunca assumir RIM
> (crítico para a exceção BBSE3, D-08). Convenção de tolerância do repo = **bounds absolutos**
> (`> 30.0`, `32.0 <= v <= 40.0`), NÃO `pytest.approx`.

**Determinismo de reexecução** (`test_vulc3_regressao.py:274-276`) — padrão a espelhar para provar
que o snapshot não deriva:
```python
a2 = report.analisar_acao(_taee11_regulada(), cfg)
assert a2.veredito == a1.veredito
assert (a2.vmin, a2.vmax) == (a1.vmin, a1.vmax)
```

**Estrutura recomendada do arquivo novo** (RESEARCH Q3):
1. `_cfg()` — copiado de `test_vulc3_regressao.py:34-36`.
2. `_carregar_snapshot()` → lê `tests/fixtures/snapshot_bancos_2026-07-12.yaml`, reconstrói os 4
   `CompanyData` (mesmo padrão de kwargs + preenchimento de dicts por ano de `_itub4_live_like`)
   + `rf_local`.
3. `_carregar_fair_values()` → lê `tests/fixtures/fair_values_bancos.yaml`.
4. Teste que itera os 4, injeta `cfg["capm"]["rf_local"]` congelado, roda `analisar_acao`, calcula
   PASS/FAIL e crava o gate quórum-3/4 + regra de anotação.

**Constantes nomeadas (Established Pattern — zero número solto):**
```python
BANDA_PASS = 0.15   # D-07
QUORUM_MIN = 3      # D-08
```

**Gate PASS/FAIL + quórum + anotação** (RESEARCH Q7 — lógica NOVA, sem analog direto, mas segue o
estilo assert-duro do molde):
```python
# PASS por ticker (D-07): banda ±15% em torno de qualquer borda da faixa FV.
def _passa(rim, fv_min, fv_max):
    return rim is not None and fv_min * (1 - BANDA_PASS) <= rim <= fv_max * (1 + BANDA_PASS)

passes = [t for t in cesta if _passa(...)]
falhas = [t for t in cesta if not _passa(...)]
assert len(passes) >= QUORUM_MIN
for t in falhas:                      # cada falha DEVE estar anotada (senão FAIL silencioso)
    assert fv[t].get("excecao_nota"), f"{t} fora da banda sem nota de exceção → FAIL silencioso"
```

**LANDMINE — `rf_local` (determinismo):** o teste NUNCA chama a rede. `analisar_acao` lê
`cfg["capm"]["rf_local"]` (default shipado 0.105). Congelar o `rf_local` da captura ao vivo no
snapshot e injetá-lo em `cfg["capm"]["rf_local"]` ANTES de `analisar_acao`. `analisar_acao` NÃO
muta `cfg` (a mutação de rf_local é do caller, ver `cli.py:77-79`), então é seguro rodar os 4
bancos com o mesmo dict `cfg`.

---

### `tests/fixtures/snapshot_bancos_2026-07-12.yaml` (fixture, frozen data)

**Analog:** a forma serializada dos campos que `_itub4_live_like()` (`test_vulc3_regressao.py:160-175`)
preenche em memória. Não existe fixture YAML no repo hoje (`tests/fixtures/` é novo) — este YAML é a
persistência dos MESMOS campos que o molde constrói inline.

**Campos mínimos a congelar por ticker** (RESEARCH Q2 — freeze SÓ estes; resto degrada gracioso a None):

| Campo | Tipo | Papel no RIM/roteamento |
|-------|------|-------------------------|
| `ticker`, `nome`, `setor` | str | `setor` DECIDE a rota (financeira→rim); crítico p/ BBSE3 |
| `anos` | List[int] | `ultimo_ano`, séries |
| `lucro_liquido` | Dict[int,float] | `roe_valuation`, `lpa_valuation`, payout |
| `patrimonio_liquido` | Dict[int,float] | `vpa` (RIM), PL médio |
| `num_acoes` | Dict[int,float] | `vpa`, `lpa`, `dpa` |
| `dividendos` | Dict[int,float] | `payout_valuation` → retenção do RIM |
| `preco_atual` | float | âncora (b) + veredito |
| `beta` | float | `ke_rim` |
| `vendas_liquidas`, `fco`, `dpa_trailing_12m` | opcionais | display (None → "-") |

**Global carimbado:** `rf_local: <escalar>` + `data_base: "2026-07-12"`. Também congelar, por ticker,
o `setor` real da CVM e o `a.motor` observado na captura (registra a rota; antecipa a exceção BBSE3).

**Anti-pattern (RESEARCH):** NÃO congelar `vpa0`/`roe0`/`ke` já-derivados — perde o teste de roteamento
e acopla ao internals do motor. Congelar raw fundamentals mantém o teste imune a mudança de assinatura
de `motores.rim` (loop D-12 re-roda o snapshot, não reescreve o teste).

**Como gerar (D-05, UMA vez ao vivo)** — mesmo padrão de `cli._montar` (`cli.py:52-63`):
```python
ano_base = cfg["universo"]["ano_base"]   # 2025
n = cfg["universo"]["anos_historico"]    # 10
c = build.montar_empresa(t, ano_base, n) # CVM+Yahoo+BCB combinados
```

---

### `tests/fixtures/fair_values_bancos.yaml` (fixture, config data — D-03)

**Analog:** estrutura YAML por-chave do `config.yaml` (lido via `yaml.safe_load`). Artefato novo,
semanticamente distinto — é a âncora-verdade do gate (D-06), NÃO knobs do motor (por isso fora do
`config.yaml`).

**Shape por ticker** (RESEARCH Q7 + D-02/D-03/D-08):
```yaml
ITUB4:
  min: <float>          # borda inferior da faixa de consenso
  max: <float>          # borda superior
  data: "2026-07-XX"    # janela do consenso, alinhada ao snapshot (D-05)
  fonte: "<casa/relatório — média de target prices>"
  excecao_nota:         # OPCIONAL — presente só se o ticker fica fora da banda (D-08)
```
> O teste lê `min`, `max` (gate), e `.get("excecao_nota")` (distingue "exceção documentada" de
> "FAIL silencioso"). **Bloqueio D-01:** os números vêm de pesquisa de consenso aprovada pelo
> usuário ANTES de versionar — task de pesquisa + aprovação PRECEDE a task deste fixture.

---

### `scripts/backtest_bancos.py` (script standalone → `out/backtest_bancos.md`)

**Analog:** `cli.py::cmd_analyze` (`cli.py:66-87`) para o padrão de escrita em `out/`.

**Padrão de saída em `out/` (`cli.py:66-87`):**
```python
def cmd_analyze(args, cfg):
    os.makedirs(OUT_DIR, exist_ok=True)
    ...
    a = report.analisar_acao(c, cfg)
    md = report.relatorio_markdown(c, a, cfg)
    destino = os.path.join(OUT_DIR, f"{c.ticker}.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(md)
```
> `OUT_DIR = os.path.join(ROOT, "out")` (`cli.py:28`). **`out/` está no `.gitignore` (linha 8)** —
> `out/backtest_bancos.md` será ignorado pelo git (esperado: é saída gerada, confirma A2). NÃO reusar
> `relatorio_markdown` (é por-ação); o backtest é uma tabela-resumo da cesta.

**Markdown via tabulate** (RESEARCH Q6 — `report.py:14` já importa `tabulate`; zero dep nova):
```python
from tabulate import tabulate
md = tabulate(linhas, headers=[
    "Ticker","Motor","RIM","Graham","Bazin","Preço","FV faixa",
    "P/VP med","P/L med","Desvio RIM×FV","PASS/FAIL","Nota exceção",
], tablefmt="github")
```

**Reuso da função compartilhada:** o script chama a MESMA `rodar_cesta(snapshot, fair_values, cfg)`
que o teste usa — garante que script e teste produzem o mesmo número (RESEARCH Open Q3). Invocável
por `python scripts/backtest_bancos.py`.

---

### `rodar_cesta()` (utility compartilhada teste ↔ script)

**Analog:** o loop de `cli.py::cmd_rank` (`cli.py:150-183`) que itera empresas, chama
`analisar_acao(c, cfg)` e coleta métricas por ticker:
```python
for c in empresas:
    ult = c.ultimo_ano()
    lpa = c.lpa_valuation()
    PL.append(mult.preco_lucro(c.preco_atual, lpa))
    ...
    a = report.analisar_acao(c, cfg)
    if a.vmin is not None and a.vmax is not None:
        ensemble_mid[c.ticker] = (a.vmin + a.vmax) / 2.0
```
> A função nova recebe os 4 `CompanyData` reconstruídos + fair values + cfg, roda `analisar_acao`
> por ticker, calcula âncoras + mediana da cesta, e devolve os resultados. Sem I/O e sem rede (pura),
> para que teste e script consumam o MESMO retorno.

---

## Shared Patterns

### Extração do intrínseco validado (RIM)
**Source:** `report.analisar_acao(c, cfg)` → `a.intrinseco_motor` (`report.py:312`, campo em `report.py:59`)
**Apply to:** teste, `rodar_cesta`, script
```python
a = report.analisar_acao(c, cfg)
# ler junto para registrar a rota (D-08):
a.arquetipo   # esperado "financeira"
a.motor       # esperado "rim"; se ≠ "rim" → exceção documentada BBSE3
a.intrinseco_motor  # o número sob validação; PODE ser None (never-raise) → tratar como fora-da-banda
a.preco_atual # espelho de c.preco_atual (âncora b)
```

### Âncora (a) — Graham + Bazin
**Source:** `core/lentes.py:37` (`preco_justo_graham`) e `:75` (`preco_teto_bazin`); receita canônica `app.py:1053-1069`
**Apply to:** `rodar_cesta` (colunas Graham/Bazin do relatório)
```python
_ult = c.ultimo_ano()
_vpa = lentes.vpa(c.patrimonio_liquido.get(_ult), c.num_acoes.get(_ult))
graham = lentes.preco_justo_graham(c.lpa_valuation(), _vpa)   # √(22,5×LPA×VPA); None se LPA/VPA≤0

_dpas = [c.dpa(ano) for ano in c.anos_ordenados()]
_dpa_med = lentes.dpa_medio(_dpas, n=5)                        # média últimos 5 anos-calendário
bazin = lentes.preco_teto_bazin(_dpa_med)                     # DPA_med / 0,06; None se DPA≤0
```

### Âncora (d) — múltiplos de pares P/VP e P/L (D-11, mediana da cesta)
**Source:** `core/lentes.py:151` (`metricas_par`) + `statistics.median` (agregação NOVA do harness)
**Apply to:** `rodar_cesta` — zero fonte externa, medianas dos 4 bancos do snapshot
```python
import statistics
pares = [lentes.metricas_par(c) for c in cesta]   # .pvp, .pl (LPA/VPA canônicos), never-raise
pvp_med = statistics.median([p.pvp for p in pares if p.pvp is not None])
pl_med  = statistics.median([p.pl  for p in pares if p.pl  is not None])
```

### Config load
**Source:** `_cfg()` em `test_vulc3_regressao.py:34-36` (idêntico em `cli.carregar_config`, `cli.py:32-34`)
**Apply to:** teste e script
```python
with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
```

### Knobs RIM da Fase 4 (READ-ONLY, consumidos via config)
**Source:** `config.yaml` §`motores.rim` (linhas 229-252) + `capm.rf_local` (linha 76)
**Apply to:** confirmar que o snapshot reproduz os números da Fase 4 (ITUB4 golden R$39,23, live R$32,87)
```
erp_banco=0.045 · ke_piso=0.11 · ke_teto=0.13 · n_fade=10 ·
excesso_sustentavel=0.045 · g_terminal=0.025 · ke_g_spread_min=0.03 · rf_local=0.105
```
> O snapshot reproduz o intrínseco porque roda o MESMO config + os MESMOS raw inputs. NÃO editar
> config.yaml (escopo cirúrgico), a menos que o loop D-12 dispare.

---

## No Analog Found

Lógica genuinamente nova (sem analog direto — o planner deve seguir RESEARCH Q7 + o estilo assert-duro
do molde):

| Elemento | Role | Data Flow | Razão |
|----------|------|-----------|-------|
| Gate quórum-3/4-±15% + regra de anotação | test logic | transform | Nenhuma validação "N de M com exceção documentada" existe no repo; é o coração do D-08 |
| Mediana da cesta como âncora setorial (D-11) | aggregation | transform | `metricas_par` dá métricas por-par; a mediana da cesta é agregação nova do harness |
| Tabela-resumo da cesta em markdown (D-10) | output | file-I/O | `relatorio_markdown` é por-ação; a tabela uma-linha-por-ticker é nova (usar `tabulate` direto) |
| `tests/fixtures/*.yaml` (snapshot + fair values) | data fixture | file-I/O | Não há fixture YAML versionado no repo hoje; `tests/fixtures/` é diretório novo |

---

## Metadata

**Analog search scope:** `tests/` (36 arquivos), `src/analista/` (cli, report, core/lentes, core/motores,
ingest/build), `config.yaml`, `.gitignore`
**Files scanned (read verbatim nesta sessão):** `tests/test_vulc3_regressao.py`, `src/analista/cli.py`,
`src/analista/core/lentes.py:30-196`; estrutura confirmada via `ls`/`grep` (scripts/ e tests/fixtures/
inexistentes; `out/` gitignored linha 8)
**Analogs herdados da RESEARCH (file:line verificados):** report.py:312 (`analisar_acao`/`intrinseco_motor`),
build.py:40 (`montar_empresa`), lentes.py:37/75/151, arquetipo.py:150-154 (roteamento financeira→rim)
**Pattern extraction date:** 2026-07-12
