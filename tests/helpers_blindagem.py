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
import pathlib
import statistics
from collections.abc import Sequence
from functools import lru_cache

import yaml

# Raiz do repo: tests/helpers_blindagem.py -> tests/ -> repo/
RAIZ_REPO = pathlib.Path(__file__).resolve().parent.parent
TICKER_MAP = RAIZ_REPO / "data" / "ticker_map.json"
CLASSIFICACAO = RAIZ_REPO / "tests" / "classificacao.yaml"
CONFIG_PROD = RAIZ_REPO / "config.yaml"
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
    """True se o decorador e' `@...mark.xfail(..., strict=True)` com literal True."""
    if not isinstance(decorador, ast.Call):
        return False
    alvo = decorador.func
    if not (isinstance(alvo, ast.Attribute) and alvo.attr == "xfail"):
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
    """
    raiz = raiz if raiz is not None else RAIZ_REPO / "tests"
    achados: set[str] = set()
    for caminho in _arquivos_de_teste(raiz):
        arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
        rel = f"tests/{caminho.name}"
        for fn in ast.walk(arvore):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not fn.name.startswith("test_"):
                continue
            if any(_e_xfail_estrito(d) for d in fn.decorator_list):
                achados.add(f"{rel}::{fn.name}")
    return achados


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

    empresas, rf_local = carregar_snapshot(str(SNAPSHOT_BANCOS))
    cfg = carregar_config_producao()
    cfg["capm"]["rf_local"] = rf_local
    return empresas, cfg


def choque_nominal(empresas, cfg: dict, bps: int):
    """Choque de inflacao COMPLETO de `+bps`: a perna da TAXA e a perna do LUCRO NOMINAL.

    Devolve `(empresas_chocadas, cfg_chocado)` em `copy.deepcopy` — NUNCA muta os
    originais (T-07-03).

    Perna da TAXA (cfg): `capm.rf_local`, `ddm.g_estavel` e `motores.rim.g_terminal`
    sobem `δ = bps/10_000`.

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
    cfg2["ddm"]["g_estavel"] += delta
    cfg2["motores"]["rim"]["g_terminal"] += delta

    empresas2 = copy.deepcopy(list(empresas))
    for c in empresas2:
        roe0 = c.roe_valuation()
        if roe0 is None or roe0 <= 0:
            continue  # perna do lucro nao aplicavel (sem base de ROE positiva)
        k = (roe0 + delta) / roe0
        for serie in ("lucro_liquido", "dividendos"):
            destino = getattr(c, serie)
            for ano in list(destino):
                if destino[ano] is not None:
                    destino[ano] = destino[ano] * k

    return empresas2, cfg2
