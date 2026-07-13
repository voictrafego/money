---
phase: 07-blindagem-processual-blind
reviewed: 2026-07-13T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - .githooks/commit-msg
  - CLAUDE.md
  - calibracao.lock.yaml
  - config.yaml
  - pyproject.toml
  - scripts/bootstrap_classificacao.py
  - tests/classificacao.yaml
  - tests/conftest.py
  - tests/helpers_blindagem.py
  - tests/test_blindagem_hook.py
  - tests/test_blindagem_meta.py
  - tests/test_blindagem_orcamento.py
  - tests/test_invariantes_v24.py
findings:
  critical: 5
  warning: 13
  info: 7
  total: 25
status: issues_found
---

# Fase 7: Relatório de Code Review

**Revisado:** 2026-07-13
**Profundidade:** standard
**Arquivos revisados:** 13
**Status:** issues_found

## Summary

A fase entrega o que prometeu no nível estrutural: a quarentena funciona (`10 passed, 1 skipped,
448 deselected, 2 xfailed` — confere com o contrato escrito no CLAUDE.md), os dois `xfail(strict=True)`
são a doença escrita como código (corretos, **não** reportados como bug), o canário do ERP dobrado
realmente constrange, e o `calibracao.lock.yaml` é uma partição completa e verificada das 30 folhas
do escopo.

O problema é o outro lado: **as guardas mordem menos do que a prosa afirma**. Escrevi um repo de
teste e um arquivo de teste sintético e **executei** as evasões — não são hipóteses:

| Evasão | Resultado medido |
|---|---|
| `@pytest.mark.xfail(False, strict=True)` + golden `ITUB4 == 32.88` | **PASSA verde** e o BLIND-04a o **tolera** |
| Ticker + valor em constantes de MÓDULO (`TICKERS`/`ALVOS`) | detector **não vê** |
| `assert` movido para um helper (`_confere(v, 32.88)`) | detector **não vê** |
| `config.yaml` + `tests/classificacao.yaml` no mesmo commit (quarentenar o golden que ficou vermelho) | hook **não bloqueia** (rc=0) |
| Trailer `Knob-Change-Justification:` com `itub4` minúsculo | hook **não bloqueia** (rc=0) |
| Dois trailers, ticker no segundo | hook **não bloqueia** (rc=0) |
| Comentário `# Move ITUB4 ~R$2` uma linha **acima** de `motores:` | teste de justificativa **não vê** |
| `veredito.margem_seguranca` (o 4º grau declarado) mudar de 0.15 → 0.30 | **nenhum teste reprova** |

Ou seja: os três mecanismos centrais da fase (BLIND-04a, BLIND-05, BLIND-06/D-04) têm cada um pelo
menos um caminho pelo qual o overfit do v2.3 voltaria **sem acender nenhuma luz**. Isso é exatamente
a classe de bug que a fase existe para não ter: uma proteção fantasma é pior que nenhuma, porque
produz confiança.

Nada em `src/` foi tocado (confere com a intenção). As mudanças no `config.yaml` são só de comentário.

---

## Critical Issues

### CR-01: `xfail(condition_falsa, strict=True)` fura o BLIND-04a por completo — golden verde e tolerado

**Arquivo:** `tests/helpers_blindagem.py:259-271` (consumido em `tests/test_blindagem_meta.py:68`)

**Issue:** `_e_xfail_estrito()` só verifica se existe o kwarg `strict=True`. Ele **ignora a condição**
do `xfail`. Com uma condição falsa, o pytest **não** marca o teste como xfail — ele roda normalmente
e fica **PASSED**. E o `xfail_estritos()` o coloca na lista de tolerados do BLIND-04a.

Medido (com `xfail_strict=true` ligado, como no `pyproject.toml`):

```python
@pytest.mark.xfail(False, strict=True, reason="nao me olhe")
def test_golden_com_xfail_falso():
    assert calc("ITUB4") == 32.88
# -> pytest: 4 passed   (PASSED, nao xfailed)
# -> h.detectar_ticker_com_valor_cravado() acha
# -> h.xfail_estritos() TOLERA
# -> novos = ofensores - tolerados = {}   <- BLIND-04a fica VERDE
```

O docstring de `xfail_estritos()` diz "não há como se auto-incluir sem declarar o teste como
falho-hoje-de-propósito". Há: basta uma condição falsa. Um golden por ticker entra verde, tolerado,
e sem quarentena. É a porta que a fase inteira existe para fechar.

**Fix:**

```python
def _e_xfail_estrito(decorador: ast.AST) -> bool:
    """True so' se `@...mark.xfail(strict=True)` SEM condicao e com `run` nao-False.

    Uma CONDICAO (posicional ou `condition=`) pode ser falsa -> o teste roda normal e fica
    VERDE, mas continuaria na lista de tolerados. E' a evasao do BLIND-04a.
    """
    if not isinstance(decorador, ast.Call):
        return False
    alvo = decorador.func
    if not (isinstance(alvo, ast.Attribute) and alvo.attr == "xfail"):
        return False
    # Qualquer condicao (posicional ou nomeada) DESQUALIFICA: nao ha como provar
    # estaticamente que ela e' sempre verdadeira.
    if decorador.args:
        return False
    if any(kw.arg == "condition" for kw in decorador.keywords):
        return False
    if any(
        kw.arg == "run" and isinstance(kw.value, ast.Constant) and kw.value.value is False
        for kw in decorador.keywords
    ):
        return False
    return any(
        kw.arg == "strict"
        and isinstance(kw.value, ast.Constant)
        and kw.value.value is True
        for kw in decorador.keywords
    )
```

Os dois xfail legítimos de `test_invariantes_v24.py` não têm condição — continuam tolerados.

---

### CR-02: o detector não vê ticker em constante de MÓDULO — a forma mais natural de escrever um golden

**Arquivo:** `tests/helpers_blindagem.py:176-182`

**Issue:** o detector exige um `ast.Constant` string igual a um ticker **dentro do corpo da função**.
Mas ele **já resolve** constantes de módulo do outro lado (rota `(c)` de `_tem_nivel_cravado`, via
`nivel_modulo`). A assimetria é o furo: valores de nível em constante de módulo são pegos; tickers em
constante de módulo, não.

Medido — nenhum destes é detectado:

```python
ALVOS = {"ITUB4": 32.88}      # ticker E valor, ambos no MODULO
TICKERS = ["ITUB4"]

@pytest.mark.parametrize("t", TICKERS)
def test_golden_via_modulo(t):
    v = calcular(t)
    assert v == pytest.approx(ALVOS[t])
# -> detectar_ticker_com_valor_cravado() = {}  (nao acha)
```

Isso não é contorção adversarial: é literalmente como se escreve uma tabela de goldens. O docstring
admite só a evasão por *fixture*; a evasão por *constante de módulo* não está admitida nem coberta.

**Fix:** coletar os tickers do escopo de módulo do mesmo jeito que `nivel_modulo`, e considerar
"tem ticker" também quando a função referencia um nome de módulo que contém ticker:

```python
def _tickers_por_nome(escopo: ast.AST, tickers: frozenset[str]) -> set[str]:
    """Nomes atribuidos a um valor que contem literal de TICKER (simetrico a
    `_constantes_de_nivel_por_nome` — sem isto o ticker foge pelo escopo de modulo)."""
    nomes: set[str] = set()
    for no in ast.walk(escopo):
        if not isinstance(no, (ast.Assign, ast.AnnAssign)) or no.value is None:
            continue
        if not any(
            isinstance(s, ast.Constant) and isinstance(s.value, str) and s.value in tickers
            for s in ast.walk(no.value)
        ):
            continue
        alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
        for alvo in alvos:
            for sub in ast.walk(alvo):
                if isinstance(sub, ast.Name):
                    nomes.add(sub.id)
    return nomes

# em detectar_ticker_com_valor_cravado(), por arquivo:
nomes_ticker_modulo = _tickers_por_nome(arvore, tickers)
# ... por funcao:
usados = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
tem_ticker = (
    any(isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in tickers
        for n in ast.walk(fn))
    or bool(usados & nomes_ticker_modulo)
)
```

---

### CR-03: mover o `assert` para um helper apaga o golden do detector

**Arquivo:** `tests/helpers_blindagem.py:115-134` (`_tem_nivel_cravado`)

**Issue:** as três rotas de `_tem_nivel_cravado` só olham `ast.Compare` / `ast.Assert` **dentro da
própria função de teste** e nomes usados em `ast.Assert` **dela**. Se a comparação vive num helper,
não há `Assert` nem `Compare` na função — e o nível some, mesmo com o ticker literal presente.

Medido — não detectado:

```python
def _confere(v, alvo):
    assert abs(v - alvo) < 0.01

def test_golden_via_helper():
    v = calcular("ITUB4")
    _confere(v, 32.88)      # <- 32.88 nao esta em nenhum Assert/Compare desta funcao
# -> detectar_ticker_com_valor_cravado() = {}  (nao acha)
```

**Fix:** quando a função **tem ticker literal**, qualquer constante numérica não-trivial em qualquer
lugar do corpo já é sinal suficiente — a exigência de "chegar a um assert" é o que abre a fuga.
Custa alguns falsos positivos (que viram entrada declarada no YAML, o comportamento desejado):

```python
def _tem_nivel_cravado(fn, nomes_de_nivel_do_modulo: set[str]) -> bool:
    # Rota (0): QUALQUER constante de nivel no corpo. Se a funcao ja' cita um ticker,
    # um numero solto nela e' nivel ate' prova em contrario — exigir que ele "chegue a um
    # assert" e' a fuga: basta mover o assert para um helper.
    if any(_float_nao_trivial(no) for no in ast.walk(fn)):
        return True
    usados = _nomes_usados_em_assert(fn) | {
        n.id for n in ast.walk(fn) if isinstance(n, ast.Name)
    }
    return bool(usados & nomes_de_nivel_do_modulo) or bool(
        usados & _constantes_de_nivel_por_nome(fn)
    )
```

(Se a taxa de falso positivo incomodar, o caminho correto é ampliar `TRIVIAIS`, **nunca** reintroduzir
a exigência de `Assert`.)

---

### CR-04: o hook não cobre `tests/classificacao.yaml` — dá para mudar o knob e quarentenar o golden vermelho no mesmo commit

**Arquivo:** `.githooks/commit-msg:33` e `tests/test_blindagem_hook.py:123-125`

**Issue:** o padrão é `^tests/(fixtures/|test_)`. Depois desta fase, o jeito moderno de fazer
"calibrei o knob até o teste parar de reclamar" **não é** editar o golden — é **mudar sua categoria
para `golden_nivel` no `tests/classificacao.yaml`**, o que o deseleciona do run default. Esse arquivo
não casa o padrão. Nem `tests/conftest.py`, nem `tests/helpers_blindagem.py`, nem `pyproject.toml`
(que contém o `addopts` da quarentena e o `xfail_strict`).

Medido em repo limpo com o hook instalado:

```
### co-change config.yaml + tests/classificacao.yaml (quarentenar o golden vermelho)
  rc=0      <- PASSOU. Commit criado.
```

O backstop histórico (`test_historico_do_v24_sem_co_change_knob_e_golden:123-125`) tem exatamente a
mesma cegueira, então nem o teste pega depois.

**Fix:** nos dois lugares, ampliar o conjunto "golden" para incluir os arquivos que **governam** o
golden, não só os que o contêm.

`.githooks/commit-msg`:
```sh
# `classificacao.yaml` entra: mudar a CATEGORIA de um teste para `golden_nivel` o
# deseleciona do run default — e' a versao v2.4 de "silenciar o teste que ficou vermelho".
printf '%s\n' "$staged" \
  | grep -qE '^(tests/(fixtures/|test_|classificacao\.yaml|conftest\.py|helpers_blindagem\.py)|pyproject\.toml)' \
  || exit 0
```

`tests/test_blindagem_hook.py`:
```python
_GOVERNA_GOLDEN = re.compile(
    r"^(tests/(fixtures/|test_|classificacao\.yaml|conftest\.py|helpers_blindagem\.py)"
    r"|pyproject\.toml)"
)
toca_golden = any(_GOVERNA_GOLDEN.match(a) for a in arquivos)
```

---

### CR-05: `veredito.margem_seguranca` — o "4º grau de liberdade fechado por declaração" não tem dente

**Arquivos:** `calibracao.lock.yaml:106-121`, `tests/test_blindagem_orcamento.py:94-98` e `:122-126`

**Issue:** o lock declara `veredito.margem_seguranca: 0.15` em `user_control` e escreve que ela
"MULTIPLICA o V" e "seria o 4º grau de liberdade, o mais perigoso de todos". Mas:

1. `test_orcamento_de_knobs_e_exatamente_3` só verifica **a presença da chave** no lock
   (`assert "veredito.margem_seguranca" in lock["user_control"]`). Nunca lê o config.
2. `test_knobs_batem_com_o_lock` monta `esperado` a partir de `graus_de_liberdade` **+ `congelados`**
   apenas — `user_control` **nunca entra**.
3. `veredito` não está no `escopo`, então `folhas_do_escopo` não a alcança e
   `comentarios_com_ticker` não varre os comentários dela.

Verificado:

```
margem_seguranca no escopo?               False
margem_seguranca em graus|congelados?     False
valor no lock (user_control): 0.15  |  valor no config: 0.15
-> nenhum teste compara os dois.
```

Consequência: alguém troca `margem_seguranca: 0.15` por `0.30` no `config.yaml`, **todo o `V` da
carteira muda de escala**, o lock continua dizendo `0.15`, e a suíte fica verde. A "Armadilha 4
morta por construção" está morta só no comentário.

**Fix:** dar dente à declaração — `user_control` entra na comparação de valores, e o bloco `veredito`
entra na varredura de ticker (mesmo sem entrar no orçamento de graus de liberdade).

```python
# test_knobs_batem_com_o_lock
esperado: dict[str, object] = {
    spec["caminho"]: spec["valor"] for spec in lock["graus_de_liberdade"].values()
}
esperado.update(lock["congelados"])
# `user_control` NAO e' grau de liberdade — mas MULTIPLICA o V. Se o valor dela pode mudar
# sem aparecer no lock, a declaracao do D-04 e' decorativa.
esperado.update(
    {caminho: spec["valor"] for caminho, spec in lock["user_control"].items()}
)
```

```python
# test_nenhuma_justificativa_de_knob_menciona_ticker
lock = h.carregar_lock()
escopo_comentarios = list(lock["escopo"]) + [
    c.split(".", 1)[0] for c in lock["user_control"]
]  # -> inclui `veredito`
ofensores = h.comentarios_com_ticker(escopo_comentarios)
```

---

## Warnings

### WR-01: comentário colado ACIMA da chave de bloco escapa da varredura de ticker

**Arquivo:** `tests/helpers_blindagem.py:405-419`

**Issue:** `bloco_atual` só muda quando a linha da **chave de topo** aparece. Um comentário na linha
*imediatamente anterior* a `motores:` ainda pertence ao bloco anterior (`arquetipo`, que está fora do
escopo de propósito). Medido: inserir `# Move ITUB4 ~R$2 — calibrado ate o ITUB4 sair do evitar` uma
linha acima de `motores:` → `comentarios_com_ticker(...)` devolve `[]`.

É justamente onde um humano escreveria a justificativa de um bloco.

**Fix:** acumular os comentários pendentes e atribuí-los ao bloco que os **segue**:

```python
pendentes: list[tuple[int, str]] = []
for n, linha in enumerate(linhas, start=1):
    sem_comentario = linha.split("#", 1)[0]
    e_chave_de_topo = bool(sem_comentario.strip()) and not linha[:1].isspace()
    if e_chave_de_topo:
        bloco_atual = sem_comentario.split(":", 1)[0].strip()
        if bloco_atual in escopo:
            # os comentarios ORFAOS logo acima da chave pertencem a ELA.
            for pn, pc in pendentes:
                _registrar(pn, pc)
        pendentes = []
    elif not sem_comentario.strip() and "#" in linha and bloco_atual not in escopo:
        pendentes.append((n, linha.split("#", 1)[1].strip()))
    elif not sem_comentario.strip() and not linha.strip():
        pendentes = []   # linha em branco corta o "cabecalho do bloco"
    ...
```

### WR-02: a regra "nunca menciona um ticker" é um corretor ortográfico, não uma regra semântica — e existe em 3 cópias divergentes

**Arquivos:** `.githooks/commit-msg:63`, `tests/test_blindagem_hook.py:36`, `tests/helpers_blindagem.py:381`

**Issue:** três implementações da mesma regra, com definições diferentes:

| Local | Padrão |
|---|---|
| `.githooks/commit-msg:63` | `grep -oE '[A-Z]{4}[0-9]{1,2}'` (sem `\b`) |
| `tests/test_blindagem_hook.py:36` | `re.compile(r"[A-Z]{4}[0-9]{1,2}")` (sem `\b`) |
| `tests/helpers_blindagem.py:381` | `re.compile(r"\b[A-Z]{4}\d{1,2}\b")` (**com** `\b`) |

As três são case-sensitive. Medido no hook: um trailer com `itub4` minúsculo **passa** (rc=0). Um
trailer com "para o banco grande sair do evitar" também passa. O comentário canônico do post-mortem
(`# NAO mexer nos knobs acima: mudariam o ITUB4`) só precisa ser reescrito sem o código do papel.

Não dá para consertar isso 100% (é semântica), mas dá para não deixar o furo trivial:

**Fix:** (a) `re.IGNORECASE` + `.upper()` antes do lookup nos três lugares; (b) uma única fonte —
o hook chama um helper Python em vez de duplicar a regex em `sh`:

```sh
# .githooks/commit-msg — uma implementacao so'.
if ! printf '%s' "$just" | "$RAIZ/.venv/bin/python" "$RAIZ/scripts/checa_justificativa.py"; then
  exit 1
fi
```

### WR-03: hook e backstop só inspecionam o PRIMEIRO trailer

**Arquivos:** `.githooks/commit-msg:40` (`| head -1`), `tests/test_blindagem_hook.py:138` (`_RE_TRAILER.search`)

**Issue:** medido — dois trailers, ticker no segundo, **passa** (rc=0):

```
Knob-Change-Justification: premio de risco revisado
Knob-Change-Justification: na real e' para o ITUB4 sair do evitar
```

**Fix:** validar **todos** os trailers, não o primeiro.

```sh
# hook: sem `head -1`; o loop ja' itera sobre tudo.
just=$(printf '%s\n' "$msg" | sed -n 's/^Knob-Change-Justification:[[:space:]]*//p')
```
```python
# teste: findall, nao search.
justificativas = _RE_TRAILER.findall(msg)
if not justificativas: ...
for just in justificativas:
    if (ticker := _menciona_ticker(just.strip())): ...
```

### WR-04: a quarentena é por FUNÇÃO — invariantes estruturais foram deselecionados junto com o nível

**Arquivos:** `tests/test_motores.py:126-133`, `tests/test_capm_local.py:42-51`, `tests/classificacao.yaml`

**Issue:** 38 testes saíram do run default. Alguns deles carregam, **na mesma função**, uma banda de
nível *e* um invariante relacional que não depende de nível nenhum:

```python
def test_ke_rim_menor_que_ke_live_de_banco():      # -> golden_nivel (deselecionado)
    kr = motores.ke_rim(1.0, cfg)
    assert 0.11 <= kr <= 0.14                       # NIVEL  (ok quarentenar)
    ke_live = capm.ke_local(1.0, ...)
    assert kr < ke_live   # "o coração do critério #1"  <- INVARIANTE, hoje nao guarda NADA
```
```python
def test_ke_local_na_faixa_small_cap_br():          # -> golden_nivel (deselecionado)
    assert ke > 0.094        # invariante fraco, mas invariante
    assert 0.13 < ke < 0.22  # NIVEL
```

O CLAUDE.md diz "golden de nível quebrou? DELETE". Quando a Fase 10/12 deletar essas funções, o
invariante `kr < ke_live` vai embora com elas — e ninguém vai notar, porque hoje ele já não roda.

**Fix:** antes de fechar a fase, **cindir** as funções mistas: o assert relacional vira uma função
`invariante` própria (fica no run default), a banda de nível fica na função `golden_nivel`. Não é
opcional — é a diferença entre quarentenar dívida e quarentenar a proteção junto.

### WR-05: `BLIND_BOOTSTRAP=1` desliga a imposição de completude e nada detecta isso

**Arquivo:** `tests/conftest.py:40-41`

**Issue:** um `export BLIND_BOOTSTRAP=1` num `.zshrc`, num `Makefile` ou numa futura CI desativa a
completude do BLIND-01 **para sempre e em silêncio**: testes novos passam a rodar sem classificação,
entradas órfãs acumulam, e a suíte continua verde. Não há nenhum teste que afirme que o run não foi
bootstrapado. O escape existe por uma razão real (o gerador), mas hoje ele é global e mudo.

**Fix:** estreitar o escape para o processo do gerador e denunciá-lo quando ativo:

```python
if os.environ.get("BLIND_BOOTSTRAP"):
    config.stash[_BOOTSTRAP] = True   # e imprime no header do relatorio
    ...
    return
```
```python
# tests/test_blindagem_meta.py — novo teste `contrato`
@pytest.mark.contrato
def test_completude_do_blind01_esta_ligada():
    assert not os.environ.get("BLIND_BOOTSTRAP"), (
        "BLIND_BOOTSTRAP=1 no ambiente -> a completude do BLIND-01 esta DESLIGADA e testes "
        "novos entram sem classificacao. Este env e' SO' do scripts/bootstrap_classificacao.py."
    )
```

### WR-06: a completude quebra `pytest arquivo.py`, `pytest nodeid`, `--lf` e `--sw` — e empurra o dev para o `BLIND_BOOTSTRAP=1`

**Arquivo:** `tests/conftest.py:43-56`

**Issue:** `orfaos = set(mapa) - vistos` compara o YAML inteiro contra os itens **coletados**. Qualquer
coleta parcial (arquivo, nodeid, `--lf`, `--sw`, `--deselect`) marca ~480 testes como órfãos e derruba
a coleta com `UsageError`. O CLAUDE.md documenta isso como "use `-k`" — mas é um atrito diário, e o
atalho óbvio para escapar dele é exatamente o env da WR-05.

**Fix:** só impor a checagem de órfãos quando a coleta foi **completa**:

```python
# args extras (arquivo/nodeid) ou seletores de subconjunto -> coleta PARCIAL.
coleta_parcial = (
    any("::" in a or a.endswith(".py") for a in config.args)
    or config.option.last_failed
    or config.option.stepwise
)
if coleta_parcial:
    if sem_classe:
        raise pytest.UsageError(...)   # nao-classificado AINDA vale
    return                              # orfaos, nao: a coleta nao viu tudo
```

### WR-07: o gerador escreve YAML por interpolação de string — um nodeid com aspa simples corrompe o arquivo

**Arquivo:** `scripts/bootstrap_classificacao.py:148`

**Issue:** `linhas.append(f"'{nodeid}': {valor}")`. Um id de `parametrize` com `'` (ex.: um param
string `"d'agua"`) produz YAML inválido ou uma chave truncada — que aparece como "teste não
classificado" **e** "entrada órfã" ao mesmo tempo, exatamente a falha que o comentário logo acima
diz estar evitando. Hoje não acontece por sorte dos dados.

**Fix:** deixar o YAML serializar:

```python
import yaml
corpo = yaml.safe_dump(
    {nid: (existente.get(nid) or proposta[nid]) for nid in nodeids},
    default_flow_style=False, sort_keys=False, allow_unicode=False, width=10**6,
)
DESTINO.write_text(CABECALHO + "\n" + corpo, encoding="utf-8")
```

### WR-08: o gerador ignora o `returncode` do pytest — erro de coleta vira classificação parcial silenciosa

**Arquivo:** `scripts/bootstrap_classificacao.py:74-85`

**Issue:** se um arquivo de teste tem `ImportError`, o `--collect-only` ainda imprime os nodeids dos
**outros** arquivos e sai com código != 0. `_nodeids_do_pytest` só checa `if not ids`. O YAML é
reescrito sem os testes do arquivo quebrado → na próxima coleta completa eles aparecem como "não
classificados".

**Fix:**

```python
if proc.returncode not in (0, 5):   # 5 = "no tests collected"
    sys.stderr.write(proc.stdout + proc.stderr)
    raise SystemExit(
        f"pytest --collect-only falhou (rc={proc.returncode}) — a lista de nodeids estaria "
        "INCOMPLETA e o YAML nasceria com buracos. Conserte a coleta antes de gerar."
    )
```

### WR-09: o marcador `REVISAR` é apagado pelo próprio ciclo de reescrita — pendência vira decisão sem revisão humana

**Arquivo:** `scripts/bootstrap_classificacao.py:105` e `:143`

**Issue:** o gerador escreve `contrato  # REVISAR`, mas `carregar_classificacao()` usa `yaml.safe_load`,
que **descarta o comentário** → o valor relido é `"contrato"`. Numa segunda execução,
`existente.get(nodeid) or proposta[nodeid]` preserva `"contrato"` como "decisão já tomada" e o
`# REVISAR` desaparece. A pendência se auto-resolve como `contrato` sem ninguém decidir nada — e o
`grep -c REVISAR -> 0` da Task 3 fica verde por apagamento, não por revisão.

**Fix:** representar a pendência **no valor**, não no comentário (ex.: `contrato_REVISAR`, categoria
inválida que quebra a coleta até um humano decidir), ou passar a preservar comentários com
`ruamel.yaml`.

### WR-10: `choque_nominal` pula a perna do lucro em silêncio — e o teste segue afirmando sobre o resultado

**Arquivo:** `tests/helpers_blindagem.py:461-462`

**Issue:**

```python
roe0 = c.roe_valuation()
if roe0 is None or roe0 <= 0:
    continue  # perna do lucro nao aplicavel
```

O próprio docstring do módulo explica que chocar só `rf`/`g` sem chocar o lucro **é a Doença 1 uma
camada abaixo** e torna a spec insatisfazível por álgebra. Mas o `continue` faz exatamente isso, sem
avisar: aquela empresa recebe um choque só de taxa. Se um dia o `ITUB4` do snapshot tiver
`roe_valuation()` None (dado faltando, mudança na primitiva), o `test_invariancia_inflacao_engine_itub4`
continua rodando e **afirmando sobre um choque errado** — e o veredito de "doença curada / não curada"
passa a ser fabricado.

**Fix:** não deixar a empresa passar meio-chocada em silêncio.

```python
if roe0 is None or roe0 <= 0:
    raise ValueError(
        f"{c.ticker}: sem base de ROE positiva -> a perna do LUCRO NOMINAL nao pode ser "
        "aplicada. Chocar so' rf/g e' a propria Doenca 1 uma camada abaixo (a spec vira "
        "insatisfazivel por algebra). O ticker precisa sair da cesta do choque, nao ser "
        "chocado pela metade."
    )
```
(Se algum ticker do snapshot legitimamente não tem ROE, ele deve ser **filtrado antes**, explicitamente.)

### WR-11: a mensagem do hook cita `config.yaml:238: 'Move ITUB4 ~R$2'` — texto deletado nesta própria fase

**Arquivo:** `.githooks/commit-msg:73-74`

**Issue:** o hook imprime, como contra-exemplo canônico, `config.yaml:238` com o texto
`'Move ITUB4 ~R$2'`. O diff desta fase **removeu** esse comentário do `config.yaml` (era o que fazia
`test_nenhuma_justificativa_de_knob_menciona_ticker` ficar vermelho). Hoje a linha 238 é outra coisa.
Quem for conferir a citação não acha nada — e o hook perde credibilidade justamente no momento em que
está bloqueando alguém.

**Fix:** citar o **histórico**, que é imutável, em vez de uma linha viva:

```sh
echo "  Contra-exemplo canonico, no historico deste repo (v2.3, commit 5cd3b61):" >&2
echo "      config.yaml:  '# ... Move ITUB4 ~R\$2'   <- e' isto que o v2.4 existe para nao repetir." >&2
echo "      (o comentario foi REMOVIDO na Fase 7; veja \`git log -S 'Move ITUB4' -- config.yaml\`)" >&2
```

### WR-12: o `pyproject.toml` é a raiz da blindagem e não se auto-protege

**Arquivo:** `pyproject.toml:17-28`

**Issue:** `xfail_strict = true` e `addopts = "-m 'not golden_nivel' --strict-markers"` são o alicerce
de BLIND-01 e BLIND-02. Nenhum teste afirma que eles continuam lá. Remover `-m 'not golden_nivel'`
faria os 38 goldens voltarem ao run default (falha ruidosa — ok); mas **acrescentar** um
`-m 'not golden_nivel and not invariante'` deselecionaria as invariantes em silêncio, e o único teste
que reclamaria é o canário — que continuaria verde porque é `contrato`.

**Fix:** um teste `contrato` que lê a própria configuração:

```python
@pytest.mark.contrato
def test_configuracao_da_blindagem_esta_intacta(pytestconfig):
    assert pytestconfig.getini("xfail_strict") is True, "XPASS deixou de quebrar a suite (BLIND-02)"
    addopts = " ".join(pytestconfig.getini("addopts"))
    assert "not golden_nivel" in addopts and "--strict-markers" in addopts
    assert "invariante" not in addopts, (
        "alguem deselecionou as INVARIANTES pelo addopts — a suite ficaria verde por omissao."
    )
```

### WR-13: o detector não é recursivo — um teste em `tests/sub/` some do BLIND-04a mas continua sendo coletado

**Arquivo:** `tests/helpers_blindagem.py:74-75`

**Issue:** `_arquivos_de_teste` usa `raiz.glob("test_*.py")` (não recursivo). O pytest, com
`testpaths = ["tests"]`, **coleta** `tests/qualquer_sub/test_x.py`. Logo um golden por ticker num
subdiretório: (a) é coletado e roda; (b) precisa de uma entrada em `classificacao.yaml` — que pode ser
`contrato`; (c) é **invisível** para `detectar_ticker_com_valor_cravado()` e para `xfail_estritos()`.
Criar uma pasta é mais fácil que escrever a evasão de CR-02.

**Fix:** `raiz.rglob("test_*.py")`, e ajustar o identificador para o caminho relativo à raiz do repo
(ver IN-02, que precisa ser corrigido junto — hoje `rel` é sempre `f"tests/{caminho.name}"`).

---

## Info

### IN-01: subtração morta em `conftest.py`

**Arquivo:** `tests/conftest.py:43`
`orfaos = sorted(set(mapa) - vistos - set(sem_classe))` — por construção `sem_classe` contém apenas
nodeids **ausentes** de `mapa`, então `- set(sem_classe)` é sempre no-op. Remover, ou o leitor vai
supor uma interação que não existe.

### IN-02: `rel` ignora o parâmetro `raiz`

**Arquivos:** `tests/helpers_blindagem.py:161` e `:293`
`rel = f"tests/{caminho.name}"` prefixa `tests/` mesmo quando `raiz` aponta para outro lugar (é o que
os testes com `tmp_path` fariam). Combinado com WR-13, o identificador vira ambíguo se houver
subdiretórios. Fix: `rel = caminho.relative_to(RAIZ_REPO).as_posix()`.

### IN-03: `LIMIAR_JACKKNIFE_PP` mede razão, não pontos percentuais

**Arquivo:** `tests/test_blindagem_meta.py:30`
A métrica é `V / FairValue` (adimensional) e `desvio_max` é um desvio dessa razão. `0.01` não é "1 pp":
é 1% **da razão**. O sufixo `_PP` vai induzir erro na Fase 14, quando o número for fixado de verdade.
Renomear para `LIMIAR_JACKKNIFE_RAZAO`.

### IN-04: o hook valida o ticker contra o JSON inteiro, o Python valida contra as chaves

**Arquivo:** `.githooks/commit-msg:65`
`grep -qF "\"$cand\"" "$MAPA"` casa a string em qualquer lugar do JSON (chave **ou** valor) e não
exclui as chaves `_`-prefixadas, enquanto `tickers_conhecidos()` (`helpers_blindagem.py:71`) filtra
`k.startswith("_")` e olha só chaves. Divergência silenciosa entre a regra do hook e a do teste.
Resolvido de graça pelo fix da WR-02 (uma implementação só).

### IN-05: `.venv/bin/python` hardcoded no gerador

**Arquivo:** `scripts/bootstrap_classificacao.py:30`
`PY = RAIZ / ".venv" / "bin" / "python"` quebra em qualquer venv com outro nome e no Windows. Use
`sys.executable` — o gerador já roda *dentro* do interpretador certo.

### IN-06: filtro por truthiness descarta `fair_value: 0` em silêncio

**Arquivo:** `tests/test_blindagem_meta.py:163`
`if d.get("v_modelo") and d.get("fair_value")` — uma entrada com `fair_value: 0` (dado corrompido) é
**silenciosamente removida** da amostra em vez de estourar. Numa cesta de 20 tickers, três entradas
zeradas encolhem a amostra sem aviso e o jackknife emite veredito sobre 17. Fix: validar
explicitamente e falhar com mensagem.

### IN-07: a varredura do histórico quebra em caminhos com espaço e ignora merges

**Arquivo:** `tests/test_blindagem_hook.py:121`
`.stdout.split()` fragmenta caminhos com espaço (e `git show --name-only --format=` não lista arquivos
em commits de merge — um co-change entrado por merge é invisível). Fix: `-z` + `split("\0")`, e
`git show -m --first-parent` para merges.

---

_Reviewed: 2026-07-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
