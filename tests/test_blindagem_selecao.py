"""BLIND-07 — a blindagem nao pode ser desligada em silencio (gap 1 da 07-VERIFICATION).

A Fase 7 inteira apoia-se em DUAS linhas de config e UMA variavel de ambiente:

    pyproject.toml   xfail_strict = true                      -> XPASS = FAILED
    pyproject.toml   addopts = "-m 'not golden_nivel' ..."    -> quem roda no default
    conftest.py      BLIND_BOOTSTRAP                          -> desliga a completude

Ate agora NENHUM teste afirmava que elas continuavam la'. O verificador EXECUTOU as duas
evasoes:

  (1) `addopts` -> `-m 'not golden_nivel and not invariante'`
      => `316 passed, 1 skipped, 146 deselected` — ZERO failed, VERDE.
      As 108 invariantes e os 2 `xfail(strict)` (as duas doencas escritas como codigo)
      evaporam sem um unico teste reclamar.

  (2) `BLIND_BOOTSTRAP=1` no ambiente (um `export` num `.zshrc` basta)
      => `423 passed` — um teste sem classificacao roda em silencio.

E' literalmente o modo de falha do post-mortem do v2.3 ("o conserto e' revertido e ninguem
nota"), agora com o carimbo de aprovacao da suite. Este arquivo fecha os dois caminhos.

O que estes testes podem confiar: NADA que dependa do proprio `addopts` — ele e' o objeto
sob ataque. Por isso o pyproject.toml e' LIDO DO DISCO (`tomllib`) e a selecao EFETIVA e'
lida do `pytest_collection_finish` (o que de fato foi coletado), nunca presumida.

Backstop: `conftest.pytest_configure` chama o MESMO `violacoes_da_blindagem()`. Um hook de
conftest roda seja qual for o `-m` — nao ha expressao de marcador que o desselecione. Se
alguem desselecionar tambem a classe `contrato` (matando estes testes), a coleta QUEBRA
antes de comecar.

Falso positivo, explicitamente evitado: num run PARCIAL (`-k`, `-m` na linha de comando,
caminho explicito) so' o contrato ESTATICO e' afirmado. Uma guarda que fica vermelha no
trabalho legitimo e' desinstalada por irritacao — a licao do falso positivo do `MACD12`
(07-04) ja' esta escrita na historia desta fase.
"""

from __future__ import annotations

import os

import pytest

import helpers_blindagem as h


def test_addopts_nao_desliga_a_blindagem():
    """O NUCLEO, lido do pyproject.toml no disco: xfail_strict, --strict-markers, e o
    markexpr do run default NAO pode desselecionar `invariante` nem `contrato`."""
    violacoes = h.violacoes_da_blindagem()
    assert violacoes == [], (
        "A BLINDAGEM FOI DESLIGADA NO pyproject.toml:\n  - " + "\n  - ".join(violacoes)
    )

    # A quarentena e' SO' do `golden_nivel` — deliberadamente fora do nucleo inegociavel:
    # a Fase 10 DELETA os goldens e nesse dia mexer neste marcador e' legitimo. Aqui a
    # afirmacao e' que HOJE a quarentena continua sendo o que o BLIND-01 declarou, e nao
    # virou um balde onde cabe qualquer classe.
    markexpr = h.markexpr_declarado()
    assert not h.expressao_seleciona(markexpr, "golden_nivel"), (
        f"O addopts `-m '{markexpr}'` parou de quarentenar os goldens de nivel — eles "
        "voltaram ao run default. Se a Fase 10 chegou e os goldens foram DELETADOS, apague "
        "tambem este assert (diff visivel). Nunca deixe o golden voltar em silencio."
    )


def test_selecao_efetiva_roda_as_invariantes_e_as_duas_doencas(pytestconfig):
    """A afirmacao sobre a REALIDADE: o que foi coletado, nao o que o config promete.

    Fecha a evasao pela LINHA DE COMANDO e por qualquer caminho que o parse estatico do
    `addopts` nao anteveja: se as invariantes ou os `xfail(strict)` nao estao na selecao
    efetiva de um run default, este teste fica vermelho.
    """
    if not h.e_run_default(pytestconfig):
        pytest.skip(
            "run parcial (-k / -m / caminho explicito) — a selecao efetiva nao e' a da "
            "suite inteira; o contrato estatico e' afirmado no outro teste"
        )

    selecionados = getattr(pytestconfig, "_blind_selecionados", None)
    assert selecionados is not None, (
        "conftest.pytest_collection_finish nao registrou a selecao efetiva — o proprio "
        "instrumento desta guarda foi removido."
    )

    classificacao = h.carregar_classificacao()
    invariantes = {k for k, v in classificacao.items() if v == "invariante"}
    assert invariantes, "classificacao.yaml nao tem NENHUMA invariante — a classe sumiu."

    fora = sorted(invariantes - selecionados)
    assert not fora, (
        f"{len(fora)} teste(s) da classe `invariante` NAO estao no run default — a "
        f"blindagem foi desselecionada:\n  " + "\n  ".join(fora[:10])
    )

    # As duas doencas (BLIND-02b e BLIND-03) sao os `xfail(strict=True)`. Descobertos por
    # AST, nunca por nodeid hardcoded: um nome hardcoded envelhece calado quando o teste e'
    # renomeado, e a lista voltaria vazia — a guarda passaria afirmando sobre o conjunto
    # vazio (exatamente o veredito fabricado que o gap 3 fecha do outro lado).
    doencas = set(h.xfail_estritos())
    assert doencas, (
        "Nenhum `xfail(strict=True)` na suite: as duas doencas do v2.4 (BLIND-02b, "
        "BLIND-03) deixaram de estar escritas como codigo."
    )
    doencas_fora = sorted(doencas - selecionados)
    assert not doencas_fora, (
        "As doencas escritas como codigo NAO rodam no run default — o alarme 'a doenca "
        f"foi curada' (XPASS) nunca vai disparar:\n  " + "\n  ".join(doencas_fora)
    )


def test_bootstrap_do_blind01_nao_esta_ligado():
    """`BLIND_BOOTSTRAP` desliga a completude do BLIND-01 globalmente e sem denuncia.

    Ele e' legitimo em UM lugar: `scripts/bootstrap_classificacao.py`, que roda
    `--collect-only` (nenhum teste EXECUTA). Se este teste esta EXECUTANDO com a variavel
    no ambiente, ela veio de um `export` no shell ou na CI — e um teste sem classificacao
    passa a rodar em silencio (medido: `423 passed`, nada reclama).
    """
    assert h.ENV_BOOTSTRAP not in os.environ, (
        f"{h.ENV_BOOTSTRAP}={os.environ.get(h.ENV_BOOTSTRAP)!r} esta no ambiente: a "
        "completude do BLIND-01 esta DESLIGADA. Um teste novo sem entrada em "
        "tests/classificacao.yaml roda sem que ninguem note. Esta variavel e' exclusiva do "
        "scripts/bootstrap_classificacao.py (que usa --collect-only) — tire-a do shell/CI."
    )
