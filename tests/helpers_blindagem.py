"""Substrato compartilhado da blindagem processual (v2.4 / Fase 7).

NAO tem prefixo `test_` de proposito: o pytest nao o coleta. Como `tests/` nao tem
`__init__.py`, o pytest poe `tests/` no `sys.path` -> os testes fazem
`import helpers_blindagem` direto.

Consumido por: `tests/conftest.py` (BLIND-01), `scripts/bootstrap_classificacao.py`,
e pelos meta-testes dos planos 07-03 (BLIND-04a) e 07-05 (BLIND-06).
"""

from __future__ import annotations

import ast
import copy
import json
import os
import pathlib
import re
import shlex
import statistics
import tomllib
from collections.abc import Sequence
from functools import lru_cache

import yaml

# Raiz do repo: tests/helpers_blindagem.py -> tests/ -> repo/
RAIZ_REPO = pathlib.Path(__file__).resolve().parent.parent
PYPROJECT = RAIZ_REPO / "pyproject.toml"
TICKER_MAP = RAIZ_REPO / "data" / "ticker_map.json"
CLASSIFICACAO = RAIZ_REPO / "tests" / "classificacao.yaml"
CONFIG_PROD = RAIZ_REPO / "config.yaml"
LOCK_CALIBRACAO = RAIZ_REPO / "calibracao.lock.yaml"  # BLIND-06: na RAIZ, nao em tests/
SNAPSHOT_BANCOS = RAIZ_REPO / "tests" / "fixtures" / "snapshot_bancos_2026-07-12.yaml"

# NAO EXISTE HOJE — nasce na FASE 14 (VAL-02): cesta estratificada, >= 6 por arquetipo + 10
# "dificeis" deliberados. Ate la' o veredito do jackknife (BLIND-04b) SKIPa. O
# `fair_values_bancos.yaml` (4 tickers, a cesta do overfit v2.3) NAO serve de substrato.
HOLDOUT_V24 = RAIZ_REPO / "tests" / "fixtures" / "holdout_v24.yaml"

CATEGORIAS = {"invariante", "golden_nivel", "contrato"}

# Constantes triviais: aparecem em qualquer teste (indices, fatores, meias) e nao
# caracterizam um NIVEL cravado.
TRIVIAIS = {0.0, 1.0, 0.5, 2.0}

# Modulos que caracterizam o caminho de valuation (o unico universo onde
# "golden de nivel" faz sentido — RESEARCH § Inventario Real da Suite).
MODULOS_VALUATION = (
    "report",
    "motores",
    "ddm",
    "capm",
    "growth",
    "normalizacao",
    "comparables",
    "lentes",
    "selo",
    "multiples",
    "screening",
    "arquetipo",
    "backtest",
)


@lru_cache(maxsize=1)
def tickers_conhecidos() -> frozenset[str]:
    """Os tickers reais da B3, do `data/ticker_map.json` (versionado).

    NUNCA usar regex: `[A-Z]{4}\\d{1,2}` casa `MACD12` (falso positivo real,
    medido em `config.yaml:134` — RESEARCH § Pitfall 7).
    """
    dados = json.loads(TICKER_MAP.read_text(encoding="utf-8"))
    return frozenset(k for k in dados if not k.startswith("_"))


def _arquivos_de_teste(raiz: pathlib.Path) -> list[pathlib.Path]:
    """RECURSIVO (WR-13): o pytest coleta `tests/qualquer_sub/test_x.py` (testpaths=tests).

    Com `glob` (nao-recursivo), bastava criar uma PASTA para um golden por ticker sumir do
    BLIND-04a continuando a rodar. Criar uma pasta e' mais facil que qualquer evasao de AST.
    """
    return sorted(p for p in raiz.rglob("test_*.py"))


def _rel(caminho: pathlib.Path, raiz: pathlib.Path) -> str:
    """Identificador do arquivo, no MESMO formato das chaves de `classificacao.yaml`.

    Relativo a RAIZ_REPO (`tests/sub/test_x.py`), nao `f"tests/{nome}"` (IN-02): com
    subdiretorios (WR-13) o nome puro do arquivo vira um identificador AMBIGUO.
    O fallback cobre a raiz sintetica dos testes do proprio detector (`tmp_path`).
    """
    try:
        return caminho.relative_to(RAIZ_REPO).as_posix()
    except ValueError:
        return caminho.relative_to(raiz.parent).as_posix()


def _escopo_de_modulo(arvore: ast.Module) -> ast.Module:
    """So' as atribuicoes de TOPO (fora de qualquer funcao).

    Varrer a arvore INTEIRA aqui seria um gerador de falso positivo: ele colheria nomes de
    variaveis LOCAIS de outras funcoes (medido: um `esperado = {...}` dentro de um teste
    contaminava qualquer outro teste que usasse um local chamado `esperado`).
    """
    return ast.Module(
        body=[n for n in arvore.body if isinstance(n, (ast.Assign, ast.AnnAssign))],
        type_ignores=[],
    )


def _float_nao_trivial(no: ast.AST) -> bool:
    """True se o no e' um literal numerico de NIVEL (nao um indice/fator trivial)."""
    if not isinstance(no, ast.Constant):
        return False
    if isinstance(no.value, bool) or not isinstance(no.value, (int, float)):
        return False
    return float(no.value) not in TRIVIAIS


def _nomes_usados_em_assert(fn: ast.AST) -> set[str]:
    nomes: set[str] = set()
    for no in ast.walk(fn):
        if isinstance(no, ast.Assert):
            for sub in ast.walk(no):
                if isinstance(sub, ast.Name):
                    nomes.add(sub.id)
    return nomes


def _constantes_de_nivel_por_nome(escopo: ast.AST) -> set[str]:
    """Nomes atribuidos a um valor que contem constante numerica NAO-trivial."""
    nomes: set[str] = set()
    for no in ast.walk(escopo):
        if not isinstance(no, (ast.Assign, ast.AnnAssign)):
            continue
        if no.value is None:
            continue
        if not any(_float_nao_trivial(sub) for sub in ast.walk(no.value)):
            continue
        alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
        for alvo in alvos:
            for sub in ast.walk(alvo):
                if isinstance(sub, ast.Name):
                    nomes.add(sub.id)
    return nomes


def _tickers_por_nome(escopo: ast.AST, tickers: frozenset[str]) -> set[str]:
    """Nomes atribuidos a um valor que contem literal de TICKER (CR-02).

    Simetrico a `_constantes_de_nivel_por_nome`: o detector JA' resolvia constantes de
    MODULO do lado do NIVEL (rota (c)) e nao resolvia do lado do TICKER. A assimetria era o
    furo — e ele fugia pela forma MAIS NATURAL de escrever uma tabela de goldens:

        ALVOS = {"ITUB4": 32.88}          # ticker E valor, ambos no modulo
        TICKERS = ["ITUB4"]
        @pytest.mark.parametrize("t", TICKERS)
        def test_golden(t):
            assert calcular(t) == pytest.approx(ALVOS[t])

    Nao e' contorcao adversarial: e' literalmente como se escreve um golden parametrizado.

    O `escopo` TEM que ser `_escopo_de_modulo(arvore)`, nunca a arvore inteira.
    """
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


def _helpers_conferidores(arvore: ast.Module) -> set[str]:
    """Funcoes de MODULO (nao-teste) que CONFEREM: o corpo delas contem um `assert` (CR-03).

    Exige `ast.Assert`, e NAO `ast.Compare`: uma FACTORY de fixture (`_mk(ticker, lucros=...)`)
    quase sempre contem um `Compare` interno e viraria falso positivo em massa (medido: 37
    testes legitimos, entre eles invariantes e contratos, seriam empurrados para a quarentena).
    Um guarda-corpo que empurra 37 testes bons para a quarentena e' desinstalado por irritacao
    antes de pegar o primeiro overfit — e' a licao explicita do plano 07-04 (o regex ingenuo
    que casava `MACD12`).

    Quem CONFERE tem `assert`. Quem CONSTROI, nao.
    """
    return {
        no.name
        for no in arvore.body
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not no.name.startswith("test_")
        and any(isinstance(s, ast.Assert) for s in ast.walk(no))
    }


def _nivel_via_helper(fn: ast.AST, conferidores: set[str]) -> bool:
    """Constante de NIVEL passada como argumento a um HELPER QUE CONFERE (CR-03).

    A evasao (medida): mover o `assert` para fora da funcao apaga o golden do detector,
    porque as rotas (a)-(c) so' olham `Compare`/`Assert` DENTRO da funcao de teste.

        def _confere(v, alvo):
            assert abs(v - alvo) < 0.01

        def test_golden_via_helper():
            _confere(calcular("ITUB4"), 32.88)   # <- nenhum Assert nesta funcao

    A correcao NAO e' "qualquer numero solto na funcao ja' e' nivel" (o que o review sugeriu):
    isso arrasta as factories de fixture junto e produz os 37 falsos positivos acima. A
    correcao e' SEGUIR A CHAMADA: o numero chega a um assert — so' que o assert esta uma
    moldura acima.
    """
    for no in ast.walk(fn):
        if not isinstance(no, ast.Call):
            continue
        alvo = no.func
        if isinstance(alvo, ast.Name):
            nome = alvo.id
        elif isinstance(alvo, ast.Attribute):
            nome = alvo.attr
        else:
            continue
        if nome not in conferidores:
            continue
        for arg in [*no.args, *(kw.value for kw in no.keywords)]:
            if any(_float_nao_trivial(sub) for sub in ast.walk(arg)):
                return True
    return False


def _tem_nivel_cravado(
    fn: ast.AST,
    nomes_de_nivel_do_modulo: set[str],
    conferidores: set[str] | None = None,
) -> bool:
    """Constante numerica NAO-trivial que chega a um assert.

    Quatro rotas — as tres ultimas sao as evasoes obvias da primeira:
      (a) direto: a constante esta dentro de um `Compare`/`Assert`
          -> `assert 30.0 <= v <= 40.0`
      (b) via variavel LOCAL usada num assert
          -> `alvos = {"ITUB4": 32.88}` ... `assert abs(v - alvo) <= tol`
      (c) via constante de MODULO usada num assert  <- e' assim que o golden da banda
          30-40 do ITUB4 se esconde: `_ITUB4_RIM_MIN = 30.0` mora fora da funcao.
      (d) via HELPER que confere (CR-03): o assert esta uma moldura acima
          -> `_confere(v, 32.88)`. Sem esta rota, mover o assert para um helper apagava
             o golden do detector.
    """
    for no in ast.walk(fn):
        if isinstance(no, (ast.Compare, ast.Assert)):
            if any(_float_nao_trivial(sub) for sub in ast.walk(no)):
                return True

    usados = _nomes_usados_em_assert(fn)
    if usados & nomes_de_nivel_do_modulo:
        return True
    if usados & _constantes_de_nivel_por_nome(fn):
        return True
    return _nivel_via_helper(fn, conferidores or set())


def detectar_ticker_com_valor_cravado(
    raiz: pathlib.Path | None = None,
) -> set[str]:
    """Testes que cravam `ticker == numero de nivel` (BLIND-04a).

    Regra (RESEARCH § BLIND-04a): para cada `FunctionDef` cujo nome comeca com `test_`,
    casa quando o corpo contem
      (i) um TICKER: literal string que e' chave de `ticker_map.json`, OU um nome de
          CONSTANTE DE MODULO cujo valor contem um (CR-02 — `TICKERS = ["ITUB4"]`)  E
      (ii) um `ast.Constant` numerico NAO-trivial (∉ {0, 1, 0.5, 2}) que chega a um assert —
           direto, via variavel local, via constante de modulo, ou via HELPER QUE CONFERE
           (CR-03 — `_confere(v, 32.88)`). Ver `_tem_nivel_cravado`.

    A varredura e' RECURSIVA (WR-13): um golden escondido em `tests/sub/` continua sendo
    coletado pelo pytest, logo precisa continuar visivel aqui.

    Devolve identificadores em NIVEL DE FUNCAO: `tests/arquivo.py::nome` (SEM `[param]`).

    O que o AST NAO ve: goldens ancorados em FIXTURE de ticker real (`snapshot_bancos*`,
    `fair_values_bancos*`, `_cesta_congelada()`) — nenhum literal de ticker aparece no corpo.
    Esses sao promovidos na AUDITORIA (BLIND-01), nao aqui. Por isso este detector e'
    BOOTSTRAP: o `classificacao.yaml` e' sempre um SUPERSET do que ele acha.
    """
    raiz = raiz if raiz is not None else RAIZ_REPO / "tests"
    tickers = tickers_conhecidos()
    achados: set[str] = set()

    for caminho in _arquivos_de_teste(raiz):
        arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
        rel = _rel(caminho, raiz)
        escopo_modulo = _escopo_de_modulo(arvore)
        # Constantes de nivel no escopo do MODULO (fora de qualquer funcao de teste).
        nivel_modulo = _constantes_de_nivel_por_nome(escopo_modulo)
        # ... e os TICKERS no escopo do modulo (CR-02) — o lado simetrico, que faltava.
        ticker_modulo = _tickers_por_nome(escopo_modulo, tickers)
        conferidores = _helpers_conferidores(arvore)

        for fn in ast.walk(arvore):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not fn.name.startswith("test_"):
                continue

            nomes_usados = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
            tem_ticker = any(
                isinstance(n, ast.Constant)
                and isinstance(n.value, str)
                and n.value in tickers
                for n in ast.walk(fn)
            ) or bool(nomes_usados & ticker_modulo)

            if tem_ticker and _tem_nivel_cravado(fn, nivel_modulo, conferidores):
                achados.add(f"{rel}::{fn.name}")

    return achados


def mediana_jackknife(valores: Sequence[float]) -> tuple[float, float]:
    """`(mediana_completa, desvio_max_ao_remover_1)` — o substituto do golden por ticker.

    Funcao PURA: sem I/O, sem config, sem engine. So' aritmetica sobre a amostra.

    O segundo termo e' `max(|mediana(valores - {v}) - mediana(valores)|)` sobre todo `v`:
    o quanto a mediana da amostra depende do PONTO MAIS INFLUENTE dela. Se um unico ticker
    consegue mover a mediana, esse ticker e' LOAD-BEARING — a calibracao esta apoiada nele,
    nao na distribuicao. E' exatamente a doenca do v2.3 (a cesta de 4 bancos), medida.

    O QUE ELE DETECTA (e o que NAO detecta): a mediana e' robusta a OUTLIER por construcao —
    jogar um valor absurdo na cauda NAO move a mediana e NAO move este desvio (medido:
    amostra homogenea de 31 pontos da desvio 0,05 com ou sem um outlier de 1000). O que faz
    o desvio explodir e' um ponto que a mediana USA COMO PONTE: uma observacao sozinha no
    centro, entre dois grupos afastados. Esse ponto e' load-bearing no sentido literal — sem
    ele a mediana pula. E' esse ponto que o jackknife acha, e e' esse que importa.

    `n < 3` levanta: jackknife sobre 2 pontos nao tem significado nenhum.
    """
    vals = list(valores)
    if len(vals) < 3:
        raise ValueError(
            f"jackknife exige n >= 3; recebeu n = {len(vals)}. "
            "Jackknife sobre uma amostra minuscula e' estatisticamente vazio."
        )
    mediana = statistics.median(vals)
    desvio_max = max(
        abs(statistics.median(vals[:i] + vals[i + 1:]) - mediana) for i in range(len(vals))
    )
    return mediana, desvio_max


def importa_caminho_de_valuation(caminho: pathlib.Path) -> bool:
    """True se o arquivo de teste importa qualquer modulo do caminho de valuation."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    for no in ast.walk(arvore):
        nomes: list[str] = []
        if isinstance(no, ast.Import):
            nomes = [a.name for a in no.names]
        elif isinstance(no, ast.ImportFrom):
            base = no.module or ""
            nomes = [base] + [f"{base}.{a.name}" for a in no.names]
        for nome in nomes:
            partes = set(nome.split("."))
            if partes & set(MODULOS_VALUATION):
                return True
    return False


def carregar_classificacao() -> dict[str, str]:
    """Le `tests/classificacao.yaml`. `safe_load`, NUNCA `load` (T-07-01)."""
    if not CLASSIFICACAO.exists():
        return {}
    dados = yaml.safe_load(CLASSIFICACAO.read_text(encoding="utf-8")) or {}
    return dict(dados)


def nodeid_para_funcao(nodeid: str) -> str:
    """Corta o `[param]`. Ponte entre nodeids do pytest e o identificador do AST."""
    return nodeid.split("[", 1)[0]


def quarentenados() -> set[str]:
    """Funcoes classificadas como `golden_nivel` (sem `[param]`)."""
    return {
        nodeid_para_funcao(k)
        for k, v in carregar_classificacao().items()
        if v == "golden_nivel"
    }


def _e_xfail_estrito(decorador: ast.AST) -> bool:
    """True SO' se `@...mark.xfail(strict=True)` SEM CONDICAO e com `run` nao-False.

    A CONDICAO e' a evasao (CR-01, medida): `@pytest.mark.xfail(False, strict=True)` NAO
    marca o teste como xfail — o pytest o roda normalmente e ele fica **PASSED**. Um golden
    por ticker decorado assim entra VERDE na suite E entra na lista de TOLERADOS do
    BLIND-04a. E' a porta que esta fase inteira existe para fechar.

    Por isso qualquer condicao — posicional (`xfail(False, ...)`) ou nomeada
    (`condition=...`) — DESQUALIFICA: nao ha como provar ESTATICAMENTE que ela e' sempre
    verdadeira, e a promessa desta lista ("o teste esta VERMELHO por contrato") so' vale
    quando o xfail e' incondicional.

    `run=False` idem: o teste nem roda, entao ele nao denuncia nada — vira um `skip` com
    outro nome, e o XPASS (que e' o auto-policiamento desta porta) nunca dispara.

    Os dois xfail legitimos de `test_invariantes_v24.py` sao incondicionais -> continuam
    tolerados.
    """
    if not isinstance(decorador, ast.Call):
        return False
    alvo = decorador.func
    if not (isinstance(alvo, ast.Attribute) and alvo.attr == "xfail"):
        return False

    # Qualquer condicao (posicional ou `condition=`) desqualifica.
    if decorador.args:
        return False
    if any(kw.arg == "condition" for kw in decorador.keywords):
        return False
    # `run=False` -> o teste nao roda -> nao ha XPASS possivel -> nao denuncia nada.
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


def xfail_estritos(raiz: pathlib.Path | None = None) -> set[str]:
    """Testes marcados `xfail(strict=True)` — os que FALHAM DE PROPOSITO (BLIND-04a).

    Por que existem, e por que NAO sao uma brecha do BLIND-04a:

    Um golden de calibracao existe para ficar VERDE — e' assim que ele trava o numero.
    Um `xfail(strict=True)` esta VERMELHO por contrato: ele nao trava nada, ele DENUNCIA.
    E o pytest o auto-policia (`xfail_strict = true`): no dia em que ele passar, a suite
    QUEBRA por XPASS. Logo um teste nesta lista nao pode virar um golden em silencio —
    o unico jeito de ele "ficar verde" e' a doenca ser curada, e nesse dia a suite grita.

    Esta lista NAO e' um allowlist por nome (que cresceria em silencio): e' uma propriedade
    ESTRUTURAL, medida no AST. Nao ha como se auto-incluir sem declarar o teste como
    falho-hoje-de-proposito, o que e' o oposto de calibrar.

    ATENCAO (CR-01): "declarar como falho-hoje" exige um xfail INCONDICIONAL. Um
    `xfail(condicao_falsa, strict=True)` deixa o teste VERDE e nao vale — ver
    `_e_xfail_estrito`, que o rejeita.
    """
    raiz = raiz if raiz is not None else RAIZ_REPO / "tests"
    achados: set[str] = set()
    for caminho in _arquivos_de_teste(raiz):
        arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
        rel = _rel(caminho, raiz)
        for fn in ast.walk(arvore):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not fn.name.startswith("test_"):
                continue
            if any(_e_xfail_estrito(d) for d in fn.decorator_list):
                achados.add(f"{rel}::{fn.name}")
    return achados


# --------------------------------------------------------------------------- #
# BLIND-07 — a blindagem se protege do proprio kill-switch (gap 1 da 07-VERIFICATION).
#
# O `addopts` do pyproject.toml e' a RAIZ do BLIND-01/02/03, e ate agora NENHUM teste
# afirmava que ele continua la'. Medido pelo verificador: trocar
#     addopts = "-m 'not golden_nivel' --strict-markers"
# por
#     addopts = "-m 'not golden_nivel and not invariante' --strict-markers"
# apaga as 108 invariantes E os 2 `xfail(strict)` das duas doencas, e a suite reporta
# `316 passed, 0 failed` — VERDE. Uma linha de config desliga a blindagem inteira e a
# suite ainda diz OK. E' exatamente o modo de falha do post-mortem do v2.3 ("o conserto
# e' revertido e ninguem nota"), agora com o carimbo de aprovacao da suite.
#
# O que este bloco pode e o que NAO pode confiar:
#   - NAO pode confiar no `addopts` (e' o que esta sob ataque) -> ele e' o OBJETO da
#     afirmacao, lido do arquivo, nao o veiculo dela.
#   - NAO pode confiar em estar SELECIONADO -> por isso o `conftest.pytest_configure`
#     tambem chama `violacoes_da_blindagem()`: um hook de conftest roda seja qual for o
#     `-m`, entao nao ha expressao de marcador que o desselecione. O teste `contrato`
#     e' a denuncia legivel; o conftest e' o backstop indesligavel.
#
# NUCLEO INEGOCIAVEL (o que `violacoes_da_blindagem` afirma) — as 3 propriedades que
# nenhuma fase futura tem motivo legitimo para mexer:
#   1. `xfail_strict = true`         -> XPASS = FAILED (o alarme "a doenca foi curada").
#   2. `--strict-markers`            -> marcador com typo nao vira quarentena de graca.
#   3. o markexpr do `addopts` SELECIONA `invariante` e `contrato`.
# A quarentena do `golden_nivel` NAO esta no nucleo: a Fase 10 DELETA os goldens, e nesse
# dia mexer no marcador e' legitimo. Ela e' afirmada no teste (diff visivel), nao aqui.
# --------------------------------------------------------------------------- #

CATEGORIAS_PROTEGIDAS = ("invariante", "contrato")

# Escape do BLIND-01 (conftest.py:40). Legitimo SO' dentro de
# `scripts/bootstrap_classificacao.py`, que precisa colher nodeids antes de o YAML existir
# — e que roda `--collect-only` (nenhum teste EXECUTA). Logo, se um teste esta rodando com
# esta variavel no ambiente, ela veio de um `export` no shell/CI: a completude do BLIND-01
# esta desligada em silencio (medido: `423 passed`, teste sem classificacao roda mudo).
ENV_BOOTSTRAP = "BLIND_BOOTSTRAP"


def ini_options_do_pyproject() -> dict:
    """`[tool.pytest.ini_options]` lido do ARQUIVO, nao do runtime do pytest."""
    dados = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return dados.get("tool", {}).get("pytest", {}).get("ini_options", {})


def _tokens_do_addopts(ini: dict | None = None) -> list[str]:
    ini = ini if ini is not None else ini_options_do_pyproject()
    addopts = ini.get("addopts", "")
    if isinstance(addopts, str):
        return shlex.split(addopts)
    return [str(t) for t in addopts]


def markexpr_declarado(ini: dict | None = None) -> str:
    """A expressao de marcador que o `addopts` impoe ao run default (`-m ...`)."""
    tokens = _tokens_do_addopts(ini)
    for i, tok in enumerate(tokens):
        if tok == "-m":
            return tokens[i + 1] if i + 1 < len(tokens) else ""
        if tok.startswith("-m") and len(tok) > 2:
            return tok[2:]
    return ""


def expressao_seleciona(markexpr: str, categoria: str) -> bool:
    """`markexpr` SELECIONA um teste marcado so' com `categoria`?

    Usa o proprio avaliador do pytest (`_pytest.mark.expression`) em vez de casar texto:
    `'not golden_nivel'` e `'not (golden_nivel or invariante)'` sao a MESMA evasao escrita
    de dois jeitos, e um `in` sobre string pegaria so' um deles.
    """
    if not markexpr.strip():
        return True  # `-m ""` seleciona tudo
    from _pytest.mark.expression import Expression

    return bool(Expression.compile(markexpr).evaluate(lambda nome: nome == categoria))


def violacoes_da_blindagem(ini: dict | None = None) -> list[str]:
    """O NUCLEO INEGOCIAVEL. Lista vazia = blindagem ligada. Chamado pelo conftest E pelo teste."""
    ini = ini if ini is not None else ini_options_do_pyproject()
    violacoes: list[str] = []

    if ini.get("xfail_strict") is not True:
        violacoes.append(
            "pyproject.toml: `xfail_strict` NAO e' true — um xfail(strict) que volta a "
            "passar deixa de quebrar a suite, e o alarme 'a doenca foi curada' (BLIND-02/03) "
            "morre calado."
        )

    if "--strict-markers" not in _tokens_do_addopts(ini):
        violacoes.append(
            "pyproject.toml: `--strict-markers` sumiu do addopts — marcador com typo "
            "(`@pytest.mark.golden_nivell`) passa a ser aceito em silencio."
        )

    markexpr = markexpr_declarado(ini)
    for categoria in CATEGORIAS_PROTEGIDAS:
        if not expressao_seleciona(markexpr, categoria):
            violacoes.append(
                f"pyproject.toml: o addopts `-m '{markexpr}'` DESSELECIONA a classe "
                f"'{categoria}' do run default. E' o kill-switch de uma linha: a suite "
                f"fica verde sem rodar a blindagem. Quarentena e' SO' para `golden_nivel`."
            )

    return violacoes


def e_run_default(config) -> bool:
    """O run e' a suite INTEIRA (o que a CI roda), e nao um subconjunto pedido a mao?

    Afirmar a selecao EFETIVA num run parcial seria um falso positivo garantido: um
    `pytest -k blindagem` legitimo nao coleta as 108 invariantes, e uma guarda que fica
    vermelha no trabalho legitimo e' desinstalada por irritacao (a licao do falso positivo
    do `MACD12`, 07-04). Num run parcial so' o contrato ESTATICO (o arquivo) e' afirmado —
    esse vale sempre.

    Parcial = tem `-k`, tem `-m` na linha de comando (diferente do declarado no addopts),
    ou pediu caminho/nodeid explicito (`config.args` != `testpaths`).
    """
    if config.getoption("keyword", default=""):
        return False
    if config.getoption("markexpr", default="") != markexpr_declarado():
        return False
    testpaths = set(config.getini("testpaths") or [])
    return set(config.args) <= testpaths


# --------------------------------------------------------------------------- #
# BLIND-02 — o choque de inflacao (plano 07-02).
#
# O config e' INJETADO POR DEPENDENCIA (`report.analisar_acao(c, cfg)` recebe um
# dict puro) -> perturbar o config num teste e' `deepcopy` + mutar chave. Nenhum
# monkeypatch, nenhum singleton global.
# --------------------------------------------------------------------------- #


def carregar_config_producao() -> dict:
    """Le o `config.yaml` de PRODUCAO. `safe_load`, NUNCA `load` (T-07-04).

    Ler o config de producao (em vez de hardcodar knobs no teste) e' metade (a) da
    defesa contra o Pitfall 5: uma fuga por knob (ex. `normalizacao.anos_media: 1`)
    vira uma alteracao VISIVEL de config — que o teste de orcamento do BLIND-06
    (plano 07-05) pega, porque `anos_media` NAO e' um dos 3 graus de liberdade.
    """
    return yaml.safe_load(CONFIG_PROD.read_text(encoding="utf-8"))


def cfg_e_empresas_do_snapshot():
    """`(empresas, cfg)` do snapshot congelado dos bancos + config de producao.

    Injeta `cfg["capm"]["rf_local"] = rf_local` do snapshot — espelha o que
    `backtest.rodar_cesta` faz (o rf fica carimbado no fixture, nao no config).
    """
    from analista.backtest import carregar_snapshot  # import tardio: precisa de src/ no path

    empresas, rf_local, _ipca_defl = carregar_snapshot(str(SNAPSHOT_BANCOS))
    cfg = carregar_config_producao()
    cfg["capm"]["rf_local"] = rf_local
    return empresas, cfg


def empresa_itub4(empresas):
    """Seleciona a ITUB4 do snapshot congelado — o caso do proprio livro e a MAIOR violacao
    da cesta (BLIND-02b, Doenca 1).

    HIGIENE DECLARADA (Pitfall 6, Fase 12): o literal do ticker vive AQUI, num helper fora de
    qualquer funcao `test_` (o detector BLIND-04a so' varre `test_*.py` e so' inspeciona funcoes
    `test_`). O teste `test_invariancia_inflacao_engine_itub4` assevera uma variacao RELATIVA
    (`abs(V_chocado/V_base - 1) < 5%`), NAO um nivel em reais — logo NAO e' `ticker == valor de
    nivel`. Enquanto foi `xfail(strict=True)` o detector o tolerava por essa porta; curado (o
    `xfail` saiu na Fase 12), ele viraria FALSO-POSITIVO do detector (ticker + numero -> assert).
    Remover o literal da NARRATIVA do teste desfaz o falso-positivo SEM afrouxar o detector nem
    excluir arquivos da varredura (as duas coisas PROIBIDAS pelo CLAUDE.md).
    """
    return {c.ticker: c for c in empresas}["ITUB4"]


def carregar_lock() -> dict:
    """Le o `calibracao.lock.yaml` da RAIZ. `safe_load`, NUNCA `load` (T-07-11).

    Ele mora na raiz, e NAO em `tests/`, de proposito: o hook do BLIND-05 bloqueia
    `config.yaml` + `tests/*` no mesmo commit, e `config.yaml` + lock e' o caminho
    SANCIONADO de mudanca de knob (a mudanca fica visivel e revisavel no diff).
    """
    return yaml.safe_load(LOCK_CALIBRACAO.read_text(encoding="utf-8"))


def folhas_do_escopo(cfg: dict, escopo: Sequence[str]) -> dict[str, object]:
    """`{caminho_pontilhado: valor}` de todas as FOLHAS dos blocos do escopo.

    Uma LISTA e' UMA FOLHA (`ddm.sensibilidade.delta_ke` e' um knob so', nao cinco):
    caminhar dentro dela produziria caminhos indexados que nada significam como knob.
    """
    def _walk(no: dict, prefixo: str) -> dict[str, object]:
        saida: dict[str, object] = {}
        for chave, valor in no.items():
            caminho = f"{prefixo}.{chave}" if prefixo else str(chave)
            if isinstance(valor, dict):
                saida.update(_walk(valor, caminho))
            else:
                saida[caminho] = valor
        return saida

    total: dict[str, object] = {}
    for bloco in escopo:
        total.update(_walk(cfg[bloco], bloco))
    return total


def valor_em(cfg: dict, caminho: str):
    """Resolve um caminho pontilhado (`motores.rim.n_fade`) no config."""
    no = cfg
    for chave in caminho.split("."):
        no = no[chave]
    return no


# Primeiro filtro, NUNCA o veredito: `[A-Z]{4}\d{1,2}` casa `MACD12` (falso positivo REAL,
# medido em `config.yaml:134`). O candidato so' vira ofensor depois de validado contra
# `tickers_conhecidos()` — RESEARCH § Pitfall 7.
_CANDIDATO_TICKER = re.compile(r"\b[A-Z]{4}\d{1,2}\b")


def comentarios_com_ticker(escopo: Sequence[str]) -> list[tuple[int, str, list[str]]]:
    """Comentarios do `config.yaml` que mencionam um TICKER, dentro dos blocos do escopo.

    A regra escrita do ROADMAP, executavel:

        "Uma justificativa legitima de knob NUNCA menciona um ticker."

    Uma justificativa que cita um ticker nao explica POR QUE o numero e' aquele — ela
    confessa CONTRA O QUE ele foi ajustado. E' a assinatura do overfit do v2.3, escrita
    no proprio arquivo que a produziu (`# Move ITUB4 ~R$2`).

    Escopo: so' os blocos que afetam o `V`. As chaves de topo do YAML estao na coluna 0,
    entao um bloco vai da sua chave ate a proxima chave de coluna 0.

    Devolve `[(numero_da_linha_1based, comentario, tickers)]`.
    """
    linhas = CONFIG_PROD.read_text(encoding="utf-8").splitlines()
    tickers = tickers_conhecidos()
    bloco_atual: str | None = None
    ofensores: list[tuple[int, str, list[str]]] = []

    for n, linha in enumerate(linhas, start=1):
        sem_comentario = linha.split("#", 1)[0]
        # Chave de topo (coluna 0, nao comentario, nao linha em branco) -> troca de bloco.
        if sem_comentario.strip() and not linha[:1].isspace():
            bloco_atual = sem_comentario.split(":", 1)[0].strip()

        if bloco_atual not in escopo or "#" not in linha:
            continue

        comentario = linha.split("#", 1)[1].strip()
        achados = sorted(
            {c for c in _CANDIDATO_TICKER.findall(comentario) if c in tickers}
        )
        if achados:
            ofensores.append((n, comentario, achados))

    return ofensores


def choque_nominal(empresas, cfg: dict, bps: int):
    """Choque de inflacao COMPLETO de `+bps`: a perna da TAXA e a perna do LUCRO NOMINAL.

    Devolve `(empresas_chocadas, cfg_chocado)` em `copy.deepcopy` — NUNCA muta os
    originais (T-07-03).

    Perna da TAXA (cfg): `capm.rf_local` e `macro.pi_ciclo` sobem `δ = bps/10_000`. O `g` da
    perpetuidade nao e' mais uma constante digitada (`ddm.g_estavel`/`motores.rim.g_terminal`
    foram REMOVIDOS na GROW-01): ele e' DERIVADO na engine como `g_cap = (1+pi_ciclo)(1+PIB_real)−1`
    (fonte unica, D-04), entao chocar `macro.pi_ciclo` propaga a perna do `g` a TODOS os motores.

    Perna do LUCRO NOMINAL (dado): a inflacao levanta o lucro NOMINAL, nao a taxa de
    desconto sozinha. Chocar so' `rf`/`g` deixaria o `ROE` (real, congelado no snapshot)
    ser comparado com um `Ke` nominal — comprimindo `(ROE−Ke)` em exatamente δ e
    derrubando o `V`. Isso e' a propria Doenca 1 uma camada abaixo, e torna a spec
    literal do BLIND-02 insatisfazivel POR ALGEBRA (`P/B justo = 1 + (ROE−Ke)/(Ke−g)`).

    Como o ROE sobe: NAO existe knob de ROE no config. O ROE vem do DADO —
    `roe_valuation() = base_lucro_normalizada(lucro) / PL_medio`. `base_normalizada` e'
    HOMOGENEA DE GRAU 1 na serie (mediana/media/winsor escalam linearmente) -> multiplicar
    toda a serie `lucro_liquido` por `k` multiplica o `roe_valuation` por `k`. Logo, para
    elevar o ROE em exatamente `+δ`:  `k = (roe0 + δ) / roe0`.

    O que NAO e' tocado: `patrimonio_liquido` e `num_acoes` — o book esta a CUSTO
    HISTORICO, e a inflacao nao o reexpressa. O VPA fica intacto (e' a historia economica
    correta). `dividendos` escala pelo MESMO `k` -> o payout (e a retencao) fica invariante;
    so' o NIVEL do ROE se move, que e' o objetivo.
    """
    delta = bps / 10_000

    cfg2 = copy.deepcopy(cfg)
    cfg2["capm"]["rf_local"] += delta
    cfg2.setdefault("macro", {})
    cfg2["macro"]["pi_ciclo"] = cfg2["macro"].get("pi_ciclo", 0.0518) + delta

    empresas2 = copy.deepcopy(list(empresas))
    for c in empresas2:
        roe0 = c.roe_valuation()
        if roe0 is None or roe0 <= 0:
            # NAO e' `continue` (gap 3 da 07-VERIFICATION). Um `continue` aqui chocaria a
            # empresa PELA METADE — so' a perna da taxa, com o ROE real congelado — que e'
            # a propria Doenca 1, e o teste seguiria afirmando sobre o resultado. Hoje e'
            # inofensivo (os 4 tickers do snapshot tem ROE > 0, medido), mas a PRIM-02
            # (Fase 10) REESCREVE `roe_valuation`: se ela devolver None para o ITUB4, o
            # veredito "doenca curada" da Fase 12 passaria a ser FABRICADO sobre uma cesta
            # meio-chocada, sem um aviso sequer. Ou a empresa e' chocada por inteiro, ou o
            # teste QUEBRA e alguem decide explicitamente tira-la da cesta.
            raise ValueError(
                f"choque_nominal: {getattr(c, 'ticker', c)!r} nao tem base de ROE positiva "
                f"(roe_valuation() = {roe0!r}) — a perna do LUCRO NOMINAL nao e' aplicavel. "
                "Chocar so' a perna da TAXA compara um ROE real com um Ke nominal e fabrica "
                "a Doenca 1 dentro do proprio teste que existe para medi-la. Se este ticker "
                "deve mesmo sair da cesta do choque, tire-o EXPLICITAMENTE do fixture."
            )
        k = (roe0 + delta) / roe0
        for serie in ("lucro_liquido", "dividendos"):
            destino = getattr(c, serie)
            for ano in list(destino):
                if destino[ano] is not None:
                    destino[ano] = destino[ano] * k

    return empresas2, cfg2
