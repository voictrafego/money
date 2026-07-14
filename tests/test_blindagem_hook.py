"""BLIND-05 — o backstop do hook: ele nao pode virar protecao fantasma.

O hook (`.githooks/commit-msg`) bloqueia o co-change `config.yaml` + golden/fixture — a
assinatura exata de "calibrei o knob ate o teste passar" (post-mortem do v2.3).

Mas um hook tem DUAS formas de morrer em silencio, e nenhum hook consegue se defender delas:

  1. DESINSTALADO. `core.hooksPath` e' config LOCAL (`.git/config`) e **nao e' versionada**.
     Um `git clone` novo do repo NAO tem a protecao. Ninguem percebe. (RESEARCH § Pitfall 6.)
  2. BURLADO. `git commit --no-verify` pula qualquer hook, por design do git.

Este repo **nao tem CI** (`.github/workflows` nao existe) -> o backstop das duas tem que ser
um TESTE. E' o que este arquivo e': a suite fica VERMELHA se a protecao sumir, e varre o
historico do marco atras de um co-change que tenha entrado pela porta do `--no-verify`.
"""

from __future__ import annotations

import os
import re
import subprocess

import pytest

from helpers_blindagem import RAIZ_REPO, tickers_conhecidos

# O commit que abre o marco v2.4 (`docs: create milestone v2.4 roadmap (8 phases, 52 reqs)`).
# A varredura comeca AQUI, e nao na raiz do repo, de proposito: os 5 co-changes historicos
# (RESEARCH § "Prova historica") sao passado JA' AUDITADO — 1 e' o overfit do v2.3, 2 sao
# legitimos. Falhar sobre eles tornaria este teste impossivel de ficar verde, e um teste que
# nao pode ficar verde e' apagado na primeira sexta-feira. O contrato e' sobre o v2.4 adiante.
BASE_V24 = "955e73d97b06bd4df77bd17efa9cdb7d64af2c07"

HOOK = RAIZ_REPO / ".githooks" / "commit-msg"

_RE_CANDIDATO_TICKER = re.compile(r"[A-Z]{4}[0-9]{1,2}")
_RE_TRAILER = re.compile(r"^Knob-Change-Justification:[ \t]*(.+)$", re.MULTILINE)

# O conjunto "golden" — os arquivos que CONTEM o golden E os que o GOVERNAM (CR-04).
# MESMA regra do hook (`.githooks/commit-msg`). `classificacao.yaml` entra porque mudar a
# CATEGORIA de um teste para `golden_nivel` o DESELECIONA do run default: e' a versao v2.4
# de "silenciar o teste que ficou vermelho", e ela nao passa por editar o golden.
# `pyproject.toml` entra porque `addopts`/`xfail_strict` (a quarentena e o XPASS) moram nele.
_RE_GOVERNA_GOLDEN = re.compile(
    r"^(tests/(fixtures/|test_|classificacao\.yaml|conftest\.py|helpers_blindagem\.py)"
    r"|pyproject\.toml)"
)


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=RAIZ_REPO,
        capture_output=True,
        text=True,
    )


def _menciona_ticker(texto: str) -> str | None:
    """O ticker mencionado, ou None. MESMA regra do hook (`.githooks/commit-msg`).

    A regex e' so' o primeiro filtro — ela casa `MACD12` (falso positivo real, que existe
    no proprio `config.yaml`). O candidato so' conta se for um ticker REAL, do
    `ticker_map.json`.
    """
    conhecidos = tickers_conhecidos()
    for cand in _RE_CANDIDATO_TICKER.findall(texto):
        if cand in conhecidos:
            return cand
    return None


def test_hook_do_blind05_esta_instalado():
    """`core.hooksPath` aponta para `.githooks` — senao o hook do BLIND-05 esta INATIVO.

    Este e' o UNICO estado runtime da Fase 7 que fica desligado por default (RESEARCH
    § Runtime State Inventory): tudo o mais (quarentena, meta-testes, orcamento de knobs)
    vive em arquivo versionado. `core.hooksPath` vive no `.git/config`, que NAO e' versionado.

    Logo: todo clone novo do repo nasce SEM a protecao do BLIND-05. Este teste e' a unica
    coisa que transforma isso num erro ruidoso em vez de uma protecao fantasma (Pitfall 6).
    """
    out = _git("config", "--get", "core.hooksPath").stdout.strip()
    assert out == ".githooks", (
        f"core.hooksPath = {out!r} (esperado '.githooks') -> o hook do BLIND-05 esta INATIVO "
        "e o co-change knob+golden passa sem bloqueio nenhum.\n"
        "    Rode:  git config core.hooksPath .githooks"
    )


def test_hook_do_blind05_e_versionado_e_executavel():
    """O hook vive em `.githooks/` (versionado), nao em `.git/hooks` (que some no clone).

    `git ls-files .git/hooks` -> 0 arquivos, hoje e sempre: o diretorio de hooks do git NAO
    e' rastreado. Um hook solto la' nao protege o REPOSITORIO — protege uma copia de trabalho.
    """
    rastreado = _git("ls-files", ".githooks/commit-msg").stdout.strip()
    assert rastreado == ".githooks/commit-msg", (
        "`.githooks/commit-msg` NAO esta versionado -> o hook morre no proximo `git clone`."
    )
    assert os.access(HOOK, os.X_OK), (
        "`.githooks/commit-msg` nao esta executavel -> o git o ignora em silencio.\n"
        "    Rode:  chmod +x .githooks/commit-msg && git update-index --chmod=+x .githooks/commit-msg"
    )


def test_historico_do_v24_sem_co_change_knob_e_golden():
    """Backstop do `--no-verify`: nenhum commit do v2.4 mexeu num knob e num golden juntos.

    O hook e' bypassavel por design (`git commit --no-verify`). Sem CI, este teste e' a rede.
    A regra e' a MESMA do hook — e a escapatoria tambem: um co-change so' e' aceito com o
    trailer `Knob-Change-Justification:` e sem mencao a ticker. O trailer fica no `git log`
    para sempre: a escapatoria e' auditavel, nao silenciosa.
    """
    commits = _git("log", "--format=%H", f"{BASE_V24}..HEAD")
    if commits.returncode != 0:
        pytest.skip(
            f"historico indisponivel a partir de BASE_V24 ({BASE_V24[:7]}) — "
            f"clone shallow ou repo sem o marco v2.4. git disse: {commits.stderr.strip()!r}. "
            "SKIP explicito: um `assert True` aqui seria uma protecao fantasma."
        )

    shas = [s for s in commits.stdout.split() if s]
    if not shas:
        pytest.skip(
            f"nenhum commit entre BASE_V24 ({BASE_V24[:7]}) e HEAD — nada a varrer."
        )

    ofensores: list[str] = []
    for sha in shas:
        arquivos = _git("show", "--no-renames", "--name-only", "--format=", sha).stdout.split()
        toca_knob = "config.yaml" in arquivos
        toca_golden = any(_RE_GOVERNA_GOLDEN.match(a) for a in arquivos)
        if not (toca_knob and toca_golden):
            continue

        msg = _git("show", "--no-patch", "--format=%B", sha).stdout
        assunto = msg.strip().splitlines()[0] if msg.strip() else "(sem mensagem)"
        achado = _RE_TRAILER.search(msg)
        if not achado:
            ofensores.append(
                f"{sha[:7]} {assunto}\n"
                f"        -> co-change knob+golden SEM `Knob-Change-Justification:` "
                f"(entrou por --no-verify?)"
            )
            continue

        just = achado.group(1).strip()
        ticker = _menciona_ticker(just)
        if ticker:
            ofensores.append(
                f"{sha[:7]} {assunto}\n"
                f"        -> justificativa menciona o TICKER {ticker}: {just!r}"
            )

    assert not ofensores, (
        f"Commit(s) do marco v2.4 com a assinatura do overfit "
        f"(`config.yaml` + golden/fixture no mesmo commit), varrendo "
        f"{BASE_V24[:7]}..HEAD ({len(shas)} commits):\n\n    "
        + "\n    ".join(ofensores)
        + "\n\nO hook do BLIND-05 bloqueia isto no ato do commit. Um commit aqui significa que "
        "ele foi burlado (`--no-verify`) ou estava desinstalado.\n"
        "A correcao NUNCA e' afrouxar este teste: e' `git rebase` separando o knob do golden, "
        "ou declarar o trailer `Knob-Change-Justification:` (razao ECONOMICA, sem citar ticker)."
    )
