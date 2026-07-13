#!/usr/bin/env python
"""Gerador da PRIMEIRA versao de `tests/classificacao.yaml` (BLIND-01).

NAO e' a fonte de verdade — o YAML commitado e' (ele passa por auditoria humana).
Este script so' propoe: a lista de nodeids vem do pytest, a categoria proposta vem do AST.

Idempotente: reexecutar NAO sobrescreve decisao ja' tomada. Ele so' acrescenta as
entradas novas e reporta as orfas.

Uso:
    .venv/bin/python scripts/bootstrap_classificacao.py --dry-run
    .venv/bin/python scripts/bootstrap_classificacao.py
"""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
from collections import Counter

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tests"))

import helpers_blindagem as h  # noqa: E402

DESTINO = RAIZ / "tests" / "classificacao.yaml"
PY = RAIZ / ".venv" / "bin" / "python"

# Marcador de pendencia. A palavra nao pode aparecer no cabecalho/prosa do YAML:
# a Task 3 fecha com `grep -c REVISAR -> 0`.
PENDENCIA = "REVISAR"

# Arquivos fora do caminho de valuation, classificaveis em bloco (RESEARCH § A3).
BLOCO = {
    "tests/test_indicators.py": "invariante",  # matematica pura (RSI de Wilder etc.)
    "tests/test_glossario.py": "contrato",
    "tests/test_grafico_ui.py": "contrato",
    "tests/test_setup_report.py": "contrato",
}

CABECALHO = """\
# BLIND-01 — classificacao dos testes do v2.4. ARQUIVO COMMITADO, fonte de verdade.
#
# invariante   : verdade algebrica/estrutural; knob nenhum a satisfaz.
#                (monotonicidade, identidade fechada, idempotencia, referencia matematica)
# golden_nivel : trava um NUMERO -> trava o metodo ATUAL. QUARENTENADO (deselecionado do
#                default via `addopts = -m 'not golden_nivel'`). Roda sob demanda:
#                `.venv/bin/python -m pytest -m golden_nivel`.
# contrato     : formato / borda / never-raise / roteamento. Independe do NIVEL dos numeros.
#
# REGRA DURA: quarentenar agora, DELETAR quando a fase que corrige o metodo chegar.
#             NUNCA atualizar o golden para o valor novo — atualizar mantem o reflexo vivo
#             (post-mortem do v2.3: o golden ITUB4 32,88 existe para cancelar um haircut
#             de -9,1% da normalizacao; dois erros se anulando).
#
# Completude imposta na coleta por `tests/conftest.py`: teste sem entrada aqui QUEBRA a
# coleta; entrada orfa (teste deletado, linha esquecida) tambem. A classificacao nao pode
# driftar em silencio.
"""


def _nodeids_do_pytest() -> list[str]:
    """A lista autoritativa vem do pytest (com os `[param]` exatos), nao do AST.

    T-07-02: `subprocess.run` com lista de argumentos, sem `shell=True`.
    `-m ""` sobrepoe o `addopts` da quarentena -> a coleta ve TUDO.
    `BLIND_BOOTSTRAP=1` desliga so' a imposicao de completude do conftest (senao o
    gerador nao consegue rodar antes de o YAML existir). Escape auditavel e explicito.
    """
    env = dict(os.environ, BLIND_BOOTSTRAP="1")
    proc = subprocess.run(
        [str(PY), "-m", "pytest", "--collect-only", "-q", "-m", ""],
        capture_output=True,
        text=True,
        cwd=str(RAIZ),
        env=env,
    )
    ids = [ln.strip() for ln in proc.stdout.splitlines() if "::" in ln]
    if not ids:
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit("pytest nao colheu nenhum nodeid")
    return ids


def _propor(nodeids: list[str]) -> dict[str, str]:
    goldens = h.detectar_ticker_com_valor_cravado()
    valuation = {
        f"tests/{p.name}"
        for p in sorted((RAIZ / "tests").glob("test_*.py"))
        if h.importa_caminho_de_valuation(p)
    }

    proposta: dict[str, str] = {}
    for nodeid in nodeids:
        fn = h.nodeid_para_funcao(nodeid)
        arquivo = fn.split("::", 1)[0]

        if fn in goldens:
            proposta[nodeid] = "golden_nivel"
        elif arquivo in valuation:
            # Caminho de valuation sem ticker cravado: precisa de decisao individual.
            proposta[nodeid] = f"contrato  # {PENDENCIA}"
        elif arquivo in BLOCO:
            proposta[nodeid] = BLOCO[arquivo]
        else:
            proposta[nodeid] = "contrato"
    return proposta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    nodeids = _nodeids_do_pytest()
    proposta = _propor(nodeids)
    existente = h.carregar_classificacao()

    novas = [n for n in nodeids if n not in existente]
    orfas = sorted(set(existente) - set(nodeids))

    contagem = Counter(v.split("#")[0].strip() for v in proposta.values())
    pendentes = sum(1 for v in proposta.values() if PENDENCIA in v)

    print(f"nodeids colhidos pelo pytest: {len(nodeids)}")
    for cat, n in sorted(contagem.items()):
        print(f"  {cat:14s} {n}")
    print(f"  (pendentes de decisao individual: {pendentes})")
    print(f"ja' classificados: {len(existente)} | novos: {len(novas)} | orfaos: {len(orfas)}")
    for o in orfas:
        print(f"  ORFAO: {o}")

    if args.dry_run:
        print("\n--dry-run: nada escrito.")
        return 0

    linhas = [CABECALHO]
    for nodeid in nodeids:
        # Decisao ja' tomada e' preservada; so' as novas usam a proposta do AST.
        valor = existente.get(nodeid) or proposta[nodeid]
        # ASPAS SIMPLES, obrigatorio: o pytest ASCII-escapa acentos nos ids de parametrize
        # (`Petr\xf3leo`). Em aspas DUPLAS o YAML reinterpretaria `\xf3` como escape e a
        # chave deixaria de casar com o nodeid real -> teste "nao classificado" + entrada
        # "orfa" ao mesmo tempo. Aspas simples nao processam escapes.
        linhas.append(f"'{nodeid}': {valor}")
    DESTINO.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"\nescrito: {DESTINO.relative_to(RAIZ)} ({len(nodeids)} entradas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
