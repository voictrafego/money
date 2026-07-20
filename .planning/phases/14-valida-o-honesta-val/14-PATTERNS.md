# Phase 14: Validação honesta (VAL) - Pattern Map

**Mapped:** 2026-07-20
**Files analyzed:** 9 (4 novos + 5 modificados)
**Analogs found:** 9 / 9

> Fase de **validação e subtração**, não de construção. ~80% orquestração de peças
> prontas (`rodar_cesta`, `mediana_jackknife`, `lentes`, `arquetipo.classificar`,
> `motores.rim`) + ~20% estatística nova (`LIMIAR_JACKKNIFE_PP(n)`). O maior risco é
> **reconstruir divergente** (`eh_concessionaria` faltando) ou **recalibrar sem querer**
> (mexer knob para "chegar em 37,22"). Zero knobs de valuation tocados.

## File Classification

| Arquivo (novo/modificado) | Role | Data Flow | Analog mais próximo | Match |
|---------------------------|------|-----------|---------------------|-------|
| `tests/fixtures/holdout_v24.yaml` **(novo)** | fixture (data) | file-I/O / transform | `tests/fixtures/fair_values_bancos.yaml` | exato (estrutura) — é o que **NÃO** repetir |
| Montador da cesta estratificada **(novo, `scripts/`)** | script/builder | batch / transform | `scripts/spike_eng_rim_104.py` | exato (role+flow) |
| Teste soberano VAL-01 (ITUB4) **(novo `test_*.py`)** | test | request-response (closed-form) | `tests/helpers_blindagem.py::empresa_itub4` + `motores.rim` call em `spike_eng_rim_104._medir_ticker` | exato |
| Função `LIMIAR_JACKKNIFE_PP(n)` + teste **(novo, em `helpers_blindagem.py`)** | utility + test | transform (pura, determinística) | `helpers_blindagem.mediana_jackknife` + `test_mediana_jackknife_e_robusta_por_construcao` | role-match |
| Teste de ordem por git (D-09) **(novo `test_*.py`)** | test | event-driven (git metadata) | `helpers_blindagem` (subprocess ausente — ver §No Analog) | parcial |
| ADR VAL-07 **(novo `.planning/decisions/`)** | doc | — | nenhum ADR existe (ver §No Analog) | nenhum |
| `tests/test_blindagem_meta.py` **(mod)** | test | transform | ele mesmo (`:30`, `:132-173`) | self |
| `src/analista/backtest.py:179` **(mod)** | harness (service) | CRUD/transform | ele mesmo | self |
| `tests/test_backtest_bancos.py` **(mod: remover 2 testes)** | test | invariante | ele mesmo (`:56`, `:72`) | self |
| `tests/classificacao.yaml` **(mod)** | config | — | ele mesmo | self |

## Pattern Assignments

### `tests/fixtures/holdout_v24.yaml` (fixture, file-I/O)

**Analog:** `tests/fixtures/fair_values_bancos.yaml` (estrutura por-ticker) — **anti-padrão de conteúdo**.

O que **replicar** do analog (forma YAML plana `TICKER: {campos}`, com `fonte`/`data`):
```yaml
# fair_values_bancos.yaml (analog de FORMA)
ITUB4:
  min: 30.50
  max: 50.00
  data: "2026-07-12"
  fonte: "Consenso de casas de análise ..."
```

O que **NÃO** repetir: `min/max` = **consenso sell-side** (circular, VAL-05 proíbe como gate) e
`excecao_nota` (a lavanderia VAL-06 mata). O substrato é Graham+Bazin, não consenso.

**Contrato do fixture que o teste que acorda EXIGE** (`test_blindagem_meta.py:160-165`):
```python
cesta = yaml.safe_load(h.HOLDOUT_V24.read_text(encoding="utf-8")) or {}
razoes = [
    float(d["v_modelo"]) / float(d["fair_value"])
    for d in cesta.values()
    if d.get("v_modelo") and d.get("fair_value")   # AZUL4/D-03 (sem fair_value) cai fora automático
]
```
→ o teste espera `fair_value` **ESCALAR** (não faixa). Schema recomendado (RESEARCH A3): colapsar a
faixa D-02 num escalar (ponto médio) para casar o teste sem reescrevê-lo, com min/max ao lado:
```yaml
ITUB4:
  fair_value: <float>          # ponto médio da faixa Graham+Bazin — COMMIT 1
  fair_value_min: <float>      # borda (auditável)              — COMMIT 1
  fair_value_max: <float>      # borda (auditável)              — COMMIT 1
  lentes: [graham, bazin]      # quais lentes valeram (D-02/D-03)
  arquetipo: financeira        # estrato (D-05/D-07)
  dificil: false               # marca dos 10 difíceis (D-06)
  fonte: "lentes Graham+Bazin (core/lentes)"
  data: "2026-07-20"
  v_modelo: <float>            # V do RIM (report.analisar_acao) — COMMIT 2 (linha SEPARADA)
```

**Schema load-bearing para D-09 (prova por git blame):** `fair_value*` e `v_modelo` de cada ticker
em **linhas separadas** (blame é por linha; dict inline na mesma linha impede a separação). Não
re-tocar linhas `fair_value` depois do Commit 2. Cabeçalho do YAML deve gravar a **regra de seleção
+ snapshot-hash** (prova que a cesta não foi montada olhando o resultado — D-05).

**Guarda anti-golden (VAL-05):** `detectar_ticker_com_valor_cravado` varre só `test_*.py`, **não**
YAML → o fixture com números por ticker **não** dispara o BLIND-04a. Seguro.

---

### Montador da cesta estratificada (script/builder, batch)

**Analog:** `scripts/spike_eng_rim_104.py` — **template quase pronto**. Carrega os 104, replica
`eh_concessionaria`, classifica, roda `report.analisar_acao`, agrega por coorte, never-raise.

**Imports pattern** (`spike_eng_rim_104.py:32-43`):
```python
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "tests"))
import helpers_blindagem as hb   # carregar_config_producao
import helpers_sanidade as hs    # carregar_snapshot_sanidade, CAMINHO_SNAPSHOT_LIMPO, falhas_do_snapshot
from analista.core import arquetipo, lentes, motores
from analista.report import report
```

**LANDMINE CRÍTICA — replicar `build.py:168` (senão CONCESSAO_FINITA fica vazio):**
`hs.carregar_snapshot_sanidade` **não popula** `c.eh_concessionaria` (fica `False`) → 19 utilities
viram CICLICA e o estrato do carve-out (D-07) não existe. O analog já mostra o mirror
(`spike_eng_rim_104.py:53-58,290`):
```python
SETORES_CONCESSIONARIA = ("energia", "saneamento", "água", "gás")  # mirror de build.py:139
def _eh_concessionaria(setor) -> bool:
    return any(t in (setor or "").lower() for t in SETORES_CONCESSIONARIA)
# no loop, ANTES de classificar/analisar:
c.eh_concessionaria = _eh_concessionaria(c.setor)
```
Warning sign: CONCESSAO_FINITA com 0 membros; CICLICA com 65.

**Loop core pattern** (`spike_eng_rim_104.py:284-299`):
```python
empresas = hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO)
falhas = hs.falhas_do_snapshot(hs.CAMINHO_SNAPSHOT_LIMPO)
for tk, c in empresas.items():
    if tk in falhas:
        continue
    c.eh_concessionaria = _eh_concessionaria(c.setor)   # mirror obrigatório
    a = report.analisar_acao(c, cfg)                     # V do RIM (Commit 2)
    coorte = arquetipo.classificar(c, cfg).chave         # estrato (D-05/D-07)
```

**Cfg offline determinístico** (β setorial carimbado — `spike_eng_rim_104.py:61-72`):
```python
cfg = hb.carregar_config_producao()
cfg["capm"]["rf_local"] = cfg["capm"]["selic_fallback"]
cfg.setdefault("macro", {})
macro.carimbar_beta_setorial(cfg)   # de analista.ingest import macro
```

**Fair value via lentes** (Commit 1 — mesmo padrão de `backtest._graham`/`_bazin`, `backtest.py:94-104`):
```python
ult = c.ultimo_ano()
graham = lentes.preco_justo_graham(c.lpa_valuation(), lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult)))
bazin  = lentes.preco_teto_bazin(lentes.dpa_medio([c.dpa(a) for a in c.anos_ordenados()], n=5))
# D-02: faixa = [min,max] das lentes DEFINIDAS; D-03: nenhuma definida (AZUL4) → sem fair_value
```
Degradação medida (RESEARCH §lentes): 93 têm ambas, 10 só uma (faixa degenerada `[x,x]`), **1**
(AZUL4) tem nenhuma → fica na cesta **sem** `fair_value`, fora do jackknife, reportado (D-03).

**Ordenação determinística (D-05):** por `market_cap` desc (campo presente no snapshot —
`fundamentals.py:70`), 6 primeiros por estrato, desempate alfabético. CRESCIMENTO tem só 4 no
universo (GRND3, MULT3, RADL3, WEGE3) → usar os 4 e **MARCAR** cota <6 (D-07).

---

### Teste soberano VAL-01 (test, closed-form request-response)

**Analog A (literal do ticker fora de `test_`):** `helpers_blindagem.empresa_itub4` (`:640-653`) — o
literal `"ITUB4"` vive num helper fora de qualquer função `test_`, e o teste assere **variação
relativa**, nunca nível em reais, para não disparar BLIND-04a.

**Analog B (chamada de `motores.rim`):** `spike_eng_rim_104._medir_ticker` + a assinatura em
`motores.py:60-71`:
```python
def rim(vpa0, roe0, ke, retencao, n, excesso_sustentavel=0.0,
        g_terminal=None, ke_g_spread_min=0.03, fade_para=None, roe_terminal=None) -> Optional[ResultadoRIM]:
```

**Padrão a escrever** (RESEARCH VAL-01, VERIFIED por execução → V=R$38,69 ∈ [35,39]):
```python
# literal ITUB4 + insumos do Cap.17 num helper FORA de test_ (higiene BLIND-04a, padrão empresa_itub4)
res = motores.rim(vpa0=19.0, roe0=0.1798, ke=0.1248, retencao=0.5331,
                  n=10, excesso_sustentavel=0.045, g_terminal=0.0728, roe_terminal=0.1798)
V = res.valor_intrinseco
assert 35.0 <= V <= 39.0     # REGIÃO, nunca == 37,22 (== seria golden de nível → BLIND-04a)
```
Regras (RESEARCH):
- **Injetar** `ke=0.1248` (constante do livro), **não** re-derivar via CAPM (engine estima 15,86%).
- `g` do livro (10,24%) entra por `roe0×retencao ≈ 9,58%`, **não** há parâmetro `g_alto` no RIM.
  Único `g` explícito é `g_terminal = g_cap = 0.0728`. Não inventar parâmetro.
- **Não** mexer `excesso_sustentavel=0.045` (knob travado no lock) para "chegar em 37,22" = recalibrar.
- Marcador: `@pytest.mark.contrato`; nome `-k soberano_itub4`; **entrada em classificacao.yaml**.

---

### Função `LIMIAR_JACKKNIFE_PP(n)` + teste (utility pura + invariante)

**Analog:** `helpers_blindagem.mediana_jackknife` (`:327-356`, função pura, sem I/O) + o teste que a
valida por construção `test_mediana_jackknife_e_robusta_por_construcao` (`test_blindagem_meta.py:88-129`).

**Padrão da função pura** (mesma casa/módulo, `helpers_blindagem.py`):
```python
def mediana_jackknife(valores: Sequence[float]) -> tuple[float, float]:
    vals = list(valores)
    if len(vals) < 3:
        raise ValueError("jackknife exige n >= 3; ...")
    mediana = statistics.median(vals)
    desvio_max = max(abs(statistics.median(vals[:i] + vals[i+1:]) - mediana) for i in range(len(vals)))
    return mediana, desvio_max
```
→ escrever `LIMIAR_JACKKNIFE_PP(n)` **ao lado**, também pura, **determinística com seed fixo**
(RESEARCH D-10): Monte-Carlo de um null neutro (M draws, percentil 95/99), σ do null vem de crença
prévia, **nunca** do hold-out observado. É o **item de maior incerteza da fase** — tratar como tarefa
de derivação do executor com **dois entregáveis**: (1) a função commitada no **Commit 1** (antes de
qualquer `v_modelo`); (2) um teste que prova que ela mede o que promete no null (espelhando o
padrão de 3-verdades-algébricas de `test_mediana_jackknife_e_robusta_por_construcao`: homogênea →
desvio baixo; ponte → desvio explode).

**Landmine de escala:** o desvio escala com a dispersão. Considerar normalizar o estatístico por
escala robusta (MAD/IQR) para `LIMIAR(n)` depender só de `n` e da forma do null. Stdlib basta
(`random`+`statistics`); numpy opcional.

**Substituir** o `LIMIAR_JACKKNIFE_PP = 0.01 [ASSUMIDO]` de `test_blindagem_meta.py:30-35` e remover
o parágrafo `[ASSUMIDO]`.

---

### Teste de ordem por git (D-09) (test, event-driven / git metadata)

**Analog parcial:** não há teste usando `subprocess`/`git blame` no repo hoje (ver §No Analog). O
mecanismo verificado (RESEARCH §Ordem por git):
```python
# git blame --line-porcelain -- tests/fixtures/holdout_v24.yaml  → "author-time <epoch>" por linha
# 1. blame do fixture; 2. mapear cada linha ao campo (parse YAML por indentação/chave);
# 3. assertar max(author-time das linhas fair_value/LIMIAR) < min(author-time das linhas v_modelo)
```
Landmines (RESEARCH §Pitfall 4 + memory `historia-git-tem-fase-13-superseded`):
- **NÃO** usar `git log --grep` (falso positivo com commits de trading `13-0x`). Usar timestamps das
  **linhas reais**.
- Shallow clone (CI `--depth=1`) quebra `git blame` → CI precisa `fetch-depth: 0`.
- Squash/amend colapsa os dois commits (timestamps iguais) → disciplina "dois commits sem squash" +
  `git push` (história remota congelada) é a proteção. Rebase preserva `author-time` (não quebra).
- Marcador `@pytest.mark.contrato`; nome `-k ordem_por_git`; **entrada em classificacao.yaml**.

---

### ADR VAL-07 (doc)

**Analog:** nenhum ADR existe (`find .planning -iname "*decision*"/"*adr*"` só achou nomes de fase).
Criar padrão novo: `.planning/decisions/VAL-07-backtest-temporal.md` (ADR leve: contexto, decisão =
**não fazer**, justificativa = PIT honesto exige data de disponibilidade de cada DFP (lag ~2-3 meses)
+ reconstruir preço/rf da época; backtest ingênuo = vazamento de futuro, pior que nenhum;
consequência = Future Requirement v2.5+). **Mais** um comentário-âncora em `src/analista/backtest.py`
(topo do módulo ou perto de `carregar_snapshot`) apontando para o ADR — o código é onde um futuro
implementador de backtest tropeça primeiro.

## Shared Patterns

### Reconstrução do snapshot dos 104 (aplica ao montador da cesta + qualquer runner)
**Source:** `helpers_sanidade.carregar_snapshot_sanidade` + mirror `build.py:168`
**Apply to:** montador da cesta, teste soberano se rodar sobre ITUB4 do snapshot
```python
empresas = hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO)
for tk, c in empresas.items():
    c.eh_concessionaria = _eh_concessionaria(c.setor)   # SEMPRE — o loader não popula
```

### Never-raise / degradação silenciosa proibida
**Source:** `backtest._passa` (None → FAIL, `:107-111`), `lentes` (todas never-raise), D-03/AZUL4
**Apply to:** montador (ticker que degrada → `None`/sem `fair_value`, nunca aborta; AZUL4 no relatório
de degradação, nunca some).

### Config injetado por dependência (nunca singleton global)
**Source:** `report.analisar_acao(c, cfg)` recebe dict puro; `backtest.rodar_cesta` copia+carimba o cfg
sem mutar o do chamador (`:129-140`).
**Apply to:** montador da cesta e teste soberano — `deepcopy`/cópia local antes de injetar `rf`/β.

### Higiene BLIND-04a (literal de ticker + número → assert)
**Source:** `helpers_blindagem.empresa_itub4` (`:640-653`)
**Apply to:** teste soberano VAL-01 — literal `"ITUB4"` num helper fora de `test_`; assertar **região**
`35 <= V <= 39`, nunca `==`. Um `TICKERS = ["ITUB4"]` + número no escopo do módulo também dispara o
detector (CR-02, `_tickers_por_nome`).

### Completude da classificação imposta na coleta
**Source:** `tests/classificacao.yaml` (completude via `conftest`); `helpers_blindagem.carregar_classificacao`
**Apply to:** TODO teste novo (VAL-01, LIMIAR, ordem-git) precisa de entrada ou **quebra a coleta**.
Teste DELETADO (os 2 do excecao_nota) precisa da entrada **removida** no mesmo diff (senão órfã quebra
a coleta). `pytest -k` sempre; `pytest arquivo.py` dispara CLASSIFICACAO ORFA.

## Modified Files — pontos exatos

### `tests/test_blindagem_meta.py`
- **`:30-35`** — `LIMIAR_JACKKNIFE_PP = 0.01 [ASSUMIDO]` → função de `n` (D-10); remover parágrafo `[ASSUMIDO]`.
- **`:132-173`** — `test_nenhum_ticker_e_load_bearing`: hoje `pytest.skip` se `not h.HOLDOUT_V24.exists()`
  (`:154-158`). Acorda automaticamente quando o fixture nascer. Remover o parágrafo "NA FASE 14: fixar
  LIMIAR..." (`:151-152`). O corpo `:160-172` já consome o contrato — **não** reescrever a métrica.

### `src/analista/backtest.py`
- **`:179`** — remover `"excecao_nota": fv.get("excecao_nota")` do dict de `rodar_cesta` (VAL-06). É
  passthrough do fair_values yaml; não existe em `report.py`.
- **topo do módulo / perto de `carregar_snapshot`** — comentário-âncora da decisão VAL-07 (D-08)
  apontando para o ADR.

### `tests/test_backtest_bancos.py`
- **`:56` `test_nenhuma_rota_diferente_de_rim_e_silenciosa`** e **`:72` `test_nenhuma_nota_de_excecao_e_orfa`**
  — os dois testes da bijeção nota⟺rota-de-exceção do v2.3. Sob RIM único (Fase 13) todo ticker roteia
  para `rim`, então a bijeção é vacuamente satisfeita. **Remover** ambos (VAL-06) e as entradas órfãs
  em `classificacao.yaml:48-49`. Preservar `test_backtest_determinismo` (`:96`) e
  `test_backtest_rotulo_do_motor_consistente` (`:119`) — não dependem do excecao_nota.

### `tests/classificacao.yaml`
- **Adicionar** entradas para: teste soberano VAL-01, teste do LIMIAR(n), teste de ordem-git.
- **Remover** as 2 entradas dos testes deletados de excecao_nota (`:48-49`).
- Fechar por construção: `grep` do símbolo `excecao_nota` na árvore viva após o diff (memory
  `deletar-simbolo-exige-varredura-de-testes`).

## No Analog Found

| Arquivo | Role | Data Flow | Motivo |
|---------|------|-----------|--------|
| Teste de ordem por git (D-09) | test | git metadata | Nenhum teste no repo usa `subprocess`/`git blame` hoje. Padrão vem do RESEARCH (`git blame --line-porcelain`), não de código existente. Item MEDIUM de confiança. |
| ADR VAL-07 | doc | — | Nenhum ADR/DECISION existe em `.planning/` (só nomes de fase). Cria diretório+padrão novos. |
| `LIMIAR_JACKKNIFE_PP(n)` (a estatística em si) | utility | Monte-Carlo | A *forma* (função pura em `helpers_blindagem`) tem analog; a *derivação estatística* (null neutro + normalização) é nova — tarefa de investigação do executor. |

## Metadata

**Analog search scope:** `src/analista/` (backtest, core/lentes, core/arquetipo, core/motores,
report/report, ingest/build, ingest/macro, core/fundamentals), `tests/` (test_blindagem_meta,
test_backtest_bancos, helpers_blindagem, helpers_sanidade, classificacao.yaml, fixtures/),
`scripts/` (spike_eng_rim_104, backtest_bancos), `.planning/decisions|adr` (inexistente).
**Files scanned:** ~15
**Pattern extraction date:** 2026-07-20
