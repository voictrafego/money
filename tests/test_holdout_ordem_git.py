"""VAL-03 / D-09 — a prova de ORDEM do hold-out por `git blame` (por LINHA).

O hold-out do v2.4 nasce em DOIS commits datados (D-09), e a ordem é load-bearing:

  Commit 1 (Plano 03): grava `holdout_v24.yaml` com SÓ `fair_value` (faixa Graham+Bazin,
                       lucro/dividendo real, independente do modelo e do preço).
  Commit 2 (Plano 04): preenche `v_modelo` (V do RIM) rodando o modelo sobre a MESMA cesta.

Se os `fair_value` fossem cravados DEPOIS de ver o `v_modelo`, a validação seria circular
(calibrar a âncora contra o resultado — a doença do v2.3). Este teste prova, pela META-DATA
do git, que isso NÃO aconteceu: toda linha `fair_value*` tem `author-time` ANTERIOR a toda
linha `v_modelo`. A prova vem da HISTÓRIA, não de uma promessa no código.

MECANISMO: `git blame --line-porcelain` expõe `author-time <epoch>` por LINHA. Mapeamos cada
linha ao seu campo (parse por chave do YAML) e asseramos
`max(author-time das linhas fair_value) < min(author-time das linhas v_modelo)`.

POR QUE NÃO GREP DE MENSAGEM DE COMMIT: a mensagem é falsificável e, neste repo, commits de
trading `13-0x` (superseded) dão FALSO POSITIVO em qualquer gate que case a mensagem do commit.
A prova tem de vir do timestamp das LINHAS reais (git blame), nunca da mensagem.

O QUE PROTEGE A PROVA:
  - Dois commits SEM squash + `git push` (história remota congelada) — burlar exige reescrever
    história publicada. Squash/amend colapsaria os dois num só timestamp e a prova evaporaria
    (o teste corretamente falharia).
  - Rebase preserva `author-time` (é autoria original) — rebase normal NÃO quebra a prova.
  - Re-tocar uma linha `fair_value` depois do Commit 2 reatribui seu blame ao commit novo →
    o teste falha, flagando a adulteração.

SHALLOW CLONE (CI `--depth=1`): sem história completa, `git blame` não consegue atribuir os
commits e o teste faria falso-reprovar. Nesse caso ele faz `skip` com instrução clara
(`fetch-depth: 0`). Localmente e na CI com história completa o teste RODA de verdade.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

_RAIZ = pathlib.Path(__file__).resolve().parent.parent
_FIXTURE = _RAIZ / "tests" / "fixtures" / "holdout_v24.yaml"
_FIXTURE_REL = "tests/fixtures/holdout_v24.yaml"


def _is_shallow() -> bool:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--is-shallow-repository"],
            cwd=_RAIZ, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001 — sem git/história → tratado como shallow (skip)
        return True
    return out == "true"


def _author_times_por_campo(blame: str) -> dict:
    """Extrai `{campo: [author-time, ...]}` do `git blame --line-porcelain`.

    Cada linha blameada expõe um bloco com `author-time <epoch>` seguido (após os headers) da
    linha de conteúdo prefixada por TAB. Mapeamos a linha ao campo pela chave YAML crua.
    """
    campos: dict = {}
    cur_at = None
    for ln in blame.split("\n"):
        if ln.startswith("author-time "):
            cur_at = int(ln.split()[1])
        elif ln.startswith("\t"):
            conteudo = ln[1:].strip()
            chave = conteudo.split(":", 1)[0].strip() if ":" in conteudo else ""
            if chave and cur_at is not None:
                campos.setdefault(chave, []).append(cur_at)
    return campos


@pytest.mark.contrato
def test_holdout_ordem_por_git():
    """max(author-time de fair_value*) < min(author-time de v_modelo) — VAL-03/D-09."""
    if not _FIXTURE.exists():
        pytest.skip("holdout_v24.yaml ainda não existe (nasce na Fase 14)")
    if _is_shallow():
        pytest.skip(
            "repositório shallow (ex.: CI checkout --depth=1): `git blame` não tem história "
            "para atribuir os commits. Use `fetch-depth: 0` no checkout para RODAR este teste."
        )

    try:
        blame = subprocess.run(
            ["git", "blame", "--line-porcelain", "--", _FIXTURE_REL],
            cwd=_RAIZ, capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError as exc:  # história ausente/erro de blame → não falso-reprova
        pytest.skip(f"`git blame` indisponível ({exc}); requer história completa (fetch-depth: 0)")

    campos = _author_times_por_campo(blame)

    fair = []
    for chave in ("fair_value", "fair_value_min", "fair_value_max"):
        fair.extend(campos.get(chave, []))
    v_modelo = campos.get("v_modelo", [])

    assert fair, "nenhuma linha fair_value blameada — fixture vazio ou schema inline (quebra a prova)"
    assert v_modelo, (
        "nenhuma linha v_modelo blameada — o Commit 2 (Plano 04) não preencheu o modelo, ou o "
        "schema não põe v_modelo em linha própria"
    )

    max_fv = max(fair)
    min_vm = min(v_modelo)
    assert max_fv < min_vm, (
        f"ORDEM VIOLADA (D-09): a última linha fair_value foi cravada em author-time {max_fv}, "
        f"NÃO antes da primeira v_modelo ({min_vm}). Os fair values têm de ser commitados ANTES "
        f"de o modelo rodar — senão a âncora foi montada olhando o resultado (o overfit do v2.3). "
        f"Squash dos dois commits ou re-toque de uma linha fair_value produz exatamente isto."
    )
