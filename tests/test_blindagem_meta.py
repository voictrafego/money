"""BLIND-04 — a porta pela qual o overfit voltaria, fechada por um teste.

Este arquivo NAO testa a engine. Ele testa OS TESTES (meta-teste, via AST) e o harness que
vai SUBSTITUIR o golden por ticker (jackknife sobre distribuicao).

  BLIND-04a  test_nenhum_teste_de_calibracao_crava_ticker_em_reais
             Nenhum teste NOVO pode afirmar `ticker == valor em reais`. Os que ja' fazem isso
             so' sao tolerados porque estao na QUARENTENA (`golden_nivel`), que e' divida
             DECLARADA, com data de morte — nao permissao.

  BLIND-04b  test_mediana_jackknife_e_robusta_por_construcao  -> passa hoje (dados sinteticos)
             test_nenhum_ticker_e_load_bearing                -> SKIPa ate a FASE 14

O veredito do jackknife NAO e' inventado hoje: sem a cesta estratificada da FASE 14 (VAL-02)
nao existe substrato sobre o qual ele signifique alguma coisa, e fingir um veredito seria
calibrar um knob contra dado inexistente — exatamente o que este marco combate.

A deteccao e' AST + `data/ticker_map.json` (versionado). NUNCA por padrao textual: um padrao
como `[A-Z]{4}\\d{1,2}` casa indicadores tecnicos que nao sao ticker nenhum (falso positivo
real, medido em `config.yaml` — RESEARCH § Pitfall 7).
"""

from __future__ import annotations

import pytest

import helpers_blindagem as h

# --------------------------------------------------------------------------- #
# BLIND-04a — a proibicao.
# --------------------------------------------------------------------------- #


@pytest.mark.contrato
def test_nenhum_teste_de_calibracao_crava_ticker_em_reais():
    """BLIND-04a: `assert V(TICKER) == R$ x` e' CALIBRACAO DISFARCADA DE TESTE.

    Este e' o mecanismo que impede o overfit de VOLTAR. O plano 07-01 quarentenou os goldens
    que ja' existiam; este teste impede que NOVOS nascam.

    Um ofensor so' e' tolerado por DUAS portas, ambas declaradas e auditaveis:

      1. QUARENTENA (`golden_nivel` em `tests/classificacao.yaml`) — divida declarada, com a
         fase em que o teste MORRE escrita ao lado. Nao e' permissao: e' um obituario agendado.
         Quem entra aqui sai do run default (`addopts` deseleciona) — ou seja, o golden para
         de proteger quem o escreveu.

      2. `xfail(strict=True)` — o teste FALHA DE PROPOSITO. Um golden de calibracao existe
         para ficar VERDE (e' assim que ele trava o numero); um xfail estrito esta VERMELHO
         por contrato e QUEBRA A SUITE no dia em que passar (XPASS, `xfail_strict = true`).
         Nao ha como calibrar um numero por essa porta.

    NAO AFROUXE ESTE TESTE. Se ele ficar vermelho, o teste novo e' que esta errado.
    """
    ofensores = h.detectar_ticker_com_valor_cravado()
    tolerados = h.quarentenados() | h.xfail_estritos()
    novos = ofensores - tolerados

    assert not novos, (
        "Teste(s) cravando `ticker == valor de nivel` FORA da quarentena:\n  "
        + "\n  ".join(sorted(novos))
        + "\n\nUm teste que crava `ticker == R$` e' calibracao disfarcada de teste — e' a porta "
        "pela qual o overfit do v2.3 voltaria. Ou ele e' classificado como `golden_nivel` em "
        "`tests/classificacao.yaml` (quarentena, com a fase da morte declarada ao lado), ou ele "
        "NAO EXISTE. NAO afrouxe este teste, nao afrouxe o detector e nao exclua arquivos da "
        "varredura."
    )
