"""BLIND-01: aplica a classificacao commitada como marcador e IMPOE completude.

Um teste novo sem entrada em `classificacao.yaml` QUEBRA a coleta. Uma entrada orfa
(teste deletado, classificacao esquecida) tambem. A classificacao nao pode driftar em
silencio — e' o que torna a DELECAO dos goldens (Fase 10) auditavel: apagar a funcao sem
apagar a linha do YAML quebra a coleta.

Escape unico e explicito: `BLIND_BOOTSTRAP=1` desliga a imposicao de completude (nao os
marcadores). E' usado SO por `scripts/bootstrap_classificacao.py`, que precisa colher os
nodeids antes de o YAML existir.
"""

from __future__ import annotations

import os

import pytest

from helpers_blindagem import CATEGORIAS, carregar_classificacao


def pytest_collection_modifyitems(config, items):
    mapa = carregar_classificacao()
    vistos: set[str] = set()
    sem_classe: list[str] = []

    for item in items:
        cat = mapa.get(item.nodeid)
        if cat is None:
            sem_classe.append(item.nodeid)
            continue
        if cat not in CATEGORIAS:
            raise pytest.UsageError(
                f"CATEGORIA INVALIDA '{cat}' em {item.nodeid} "
                f"(validas: {sorted(CATEGORIAS)})"
            )
        item.add_marker(getattr(pytest.mark, cat))
        vistos.add(item.nodeid)

    if os.environ.get("BLIND_BOOTSTRAP"):
        return

    orfaos = sorted(set(mapa) - vistos - set(sem_classe))
    erros = []
    if sem_classe:
        erros.append(
            "TESTE NAO CLASSIFICADO (BLIND-01) — adicione a tests/classificacao.yaml:\n  "
            + "\n  ".join(sorted(sem_classe))
        )
    if orfaos:
        erros.append(
            "CLASSIFICACAO ORFA — o teste sumiu mas a entrada ficou:\n  "
            + "\n  ".join(orfaos)
        )
    if erros:
        raise pytest.UsageError("\n\n".join(erros))
