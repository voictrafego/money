"""Substrato compartilhado da blindagem processual (v2.4 / Fase 7).

NAO tem prefixo `test_` de proposito: o pytest nao o coleta. Como `tests/` nao tem
`__init__.py`, o pytest poe `tests/` no `sys.path` -> os testes fazem
`import helpers_blindagem` direto.

Consumido por: `tests/conftest.py` (BLIND-01), `scripts/bootstrap_classificacao.py`,
e pelos meta-testes dos planos 07-03 (BLIND-04a) e 07-05 (BLIND-06).
"""

from __future__ import annotations

import ast
import json
import pathlib
from functools import lru_cache

import yaml

# Raiz do repo: tests/helpers_blindagem.py -> tests/ -> repo/
RAIZ_REPO = pathlib.Path(__file__).resolve().parent.parent
TICKER_MAP = RAIZ_REPO / "data" / "ticker_map.json"
CLASSIFICACAO = RAIZ_REPO / "tests" / "classificacao.yaml"

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
    "freio",
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
    return sorted(p for p in raiz.glob("test_*.py"))


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


def _tem_nivel_cravado(fn: ast.AST, nomes_de_nivel_do_modulo: set[str]) -> bool:
    """Constante numerica NAO-trivial que chega a um assert.

    Tres rotas — as duas ultimas sao as evasoes obvias da primeira:
      (a) direto: a constante esta dentro de um `Compare`/`Assert`
          -> `assert 30.0 <= v <= 40.0`
      (b) via variavel LOCAL usada num assert
          -> `alvos = {"ITUB4": 32.88}` ... `assert abs(v - alvo) <= tol`
      (c) via constante de MODULO usada num assert  <- e' assim que o golden da banda
          30-40 do ITUB4 se esconde: `_ITUB4_RIM_MIN = 30.0` mora fora da funcao.
    """
    for no in ast.walk(fn):
        if isinstance(no, (ast.Compare, ast.Assert)):
            if any(_float_nao_trivial(sub) for sub in ast.walk(no)):
                return True

    usados = _nomes_usados_em_assert(fn)
    if usados & nomes_de_nivel_do_modulo:
        return True
    return bool(usados & _constantes_de_nivel_por_nome(fn))


def detectar_ticker_com_valor_cravado(
    raiz: pathlib.Path | None = None,
) -> set[str]:
    """Testes que cravam `ticker == numero de nivel` (BLIND-04a).

    Regra (RESEARCH § BLIND-04a): para cada `FunctionDef` cujo nome comeca com `test_`,
    casa quando o corpo contem
      (i) um literal string que e' chave de `ticker_map.json`  E
      (ii) um `ast.Constant` numerico NAO-trivial (∉ {0, 1, 0.5, 2}) que chega a um assert
           (direto ou via variavel — ver `_tem_nivel_cravado`).

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
        rel = f"tests/{caminho.name}"
        # Constantes de nivel no escopo do MODULO (fora de qualquer funcao de teste).
        nivel_modulo = _constantes_de_nivel_por_nome(
            ast.Module(
                body=[n for n in arvore.body if isinstance(n, (ast.Assign, ast.AnnAssign))],
                type_ignores=[],
            )
        )

        for fn in ast.walk(arvore):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not fn.name.startswith("test_"):
                continue

            tem_ticker = any(
                isinstance(n, ast.Constant)
                and isinstance(n.value, str)
                and n.value in tickers
                for n in ast.walk(fn)
            )
            if tem_ticker and _tem_nivel_cravado(fn, nivel_modulo):
                achados.add(f"{rel}::{fn.name}")

    return achados


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
