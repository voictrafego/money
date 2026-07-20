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
import yaml

import helpers_blindagem as h

# O limiar do jackknife e' agora `h.LIMIAR_JACKKNIFE_PP(n)` — uma FUNCAO de `n`, derivada de um
# null neutro por Monte-Carlo com seed fixo (helpers_blindagem, Plano 14-02, Wave 2), pre-registrada
# ANTES de existir qualquer valor do modelo (Plano 04). A constante magica `0.01` (que nunca foi
# medida) morreu: fixa-la olhando a cesta seria calibrar um knob contra o resultado.

# A metrica e' `V / FairValue` (VAL-05) — o modelo contra uma referencia INDEPENDENTE.
# NUNCA o modelo contra o preco de mercado: um modelo cuja mediana bate o mercado e' um
# ESPELHO do mercado, e um espelho nao serve para achar acao barata.

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


# --------------------------------------------------------------------------- #
# BLIND-04b — o substituto: distribuicao + jackknife.
# --------------------------------------------------------------------------- #


@pytest.mark.invariante
def test_mediana_jackknife_e_robusta_por_construcao():
    """BLIND-04b (harness): prova, em dados SINTETICOS, que o jackknife mede o que promete.

    Nenhum ticker aqui — sao numeros puros. Tres verdades algebricas:

      1. AMOSTRA HOMOGENEA -> remover 1 ponto quase nao move a mediana. Nenhum ponto e'
         load-bearing: a mediana esta apoiada na DISTRIBUICAO. E' o estado saudavel.

      2. OUTLIER NAO MOVE NADA. Contra a intuicao (e contra o que o plano supunha): jogar um
         valor absurdo na cauda deixa o desvio do jackknife IDENTICO. A mediana e' robusta a
         outlier POR CONSTRUCAO — e' por isso que ela, e nao a media, e' a estatistica certa
         para este teste.

      3. PONTO-PONTE -> o desvio EXPLODE. Uma observacao sozinha no centro, entre dois grupos
         afastados, e' LOAD-BEARING no sentido literal: a mediana se apoia nela e pula quando
         ela sai. E' ESTE o padrao que o jackknife acha — e e' a forma exata da doenca do
         v2.3 (uma cesta minuscula em que um ticker carrega a calibracao).
    """
    homogenea = [10.0 + 0.1 * i for i in range(31)]
    _, desvio_homogeneo = h.mediana_jackknife(homogenea)
    assert desvio_homogeneo < 0.1, (
        f"amostra homogenea nao deveria ter ponto influente: desvio {desvio_homogeneo}"
    )

    _, desvio_com_outlier = h.mediana_jackknife([*homogenea, 1000.0])
    assert desvio_com_outlier == pytest.approx(desvio_homogeneo, abs=1e-9), (
        "a mediana NAO e' robusta a outlier — o harness esta medindo extremidade, nao "
        "dependencia de um ponto. Nesse caso ele reprovaria cauda gorda em vez de "
        "calibracao apoiada num ticker so'."
    )

    ponte = [0.0, 0.0, 10.0, 100.0, 100.0]  # o 10.0 sozinho decide a mediana
    mediana_ponte, desvio_ponte = h.mediana_jackknife(ponte)
    assert mediana_ponte == 10.0
    assert desvio_ponte > 20 * desvio_homogeneo, (
        f"o harness NAO detectou o ponto load-bearing: desvio {desvio_ponte} numa amostra "
        f"em que uma unica observacao decide a mediana. Sem isso, o BLIND-04b nao reprova "
        f"nada e o golden por ticker nao tem substituto."
    )

    with pytest.raises(ValueError):
        h.mediana_jackknife([1.0, 3.0])  # jackknife sobre 2 pontos e' vazio


@pytest.mark.invariante
def test_limiar_jackknife_mede_o_que_promete():
    """D-10: prova que `LIMIAR_JACKKNIFE_PP(n)` separa sample saudavel de sample load-bearing.

    Espelha `test_mediana_jackknife_e_robusta_por_construcao`, mas sobre o par
    (estatistico normalizado, limiar). Nenhum ticker aqui — numeros puros. Duas verdades:

      1. SAMPLE SAUDAVEL (homogeneo, sem ponto load-bearing) -> o desvio do jackknife
         NORMALIZADO (em MADs) fica ABAIXO de `LIMIAR_JACKKNIFE_PP(n)`. Nenhum ponto e'
         load-bearing: o gate nao acusa nada. E' o estado saudavel.

      2. SAMPLE COM PONTO LOAD-BEARING (ponte: uma unica observacao no centro, entre dois
         grupos afastados) -> o desvio normalizado EXCEDE `LIMIAR_JACKKNIFE_PP(n)`. O gate
         reprova corretamente — e' a forma exata da doenca do v2.3 (a calibracao apoiada num
         ponto so').

    O limiar e' derivado de um null NEUTRO (seed fixo), NAO destes samples: por isso um
    saudavel qualquer fica abaixo e uma ponte deliberada fica acima. Determinismo herdado da
    funcao (seed literal) mantem o teste estavel.
    """
    n = 31
    limiar = h.LIMIAR_JACKKNIFE_PP(n)
    assert 0.0 < limiar < 1.0, (
        f"para uma cesta de n={n} o limiar deveria ser uma fracao de MAD em (0,1); "
        f"veio {limiar}"
    )

    saudavel = [10.0 + 0.1 * i for i in range(n)]  # distribuicao suave, sem ponto influente
    desvio_saudavel = h.desvio_jackknife_normalizado(saudavel)
    assert desvio_saudavel < limiar, (
        f"um sample saudavel nao deveria disparar o gate: desvio normalizado "
        f"{desvio_saudavel:.4f} >= limiar {limiar:.4f}"
    )

    ponte = [0.0] * 15 + [10.0] + [100.0] * 15  # o 10.0 sozinho decide a mediana
    desvio_ponte = h.desvio_jackknife_normalizado(ponte)
    assert desvio_ponte > limiar, (
        f"o gate NAO detectou o ponto load-bearing: desvio normalizado {desvio_ponte:.4f} "
        f"<= limiar {limiar:.4f} numa amostra em que uma unica observacao decide a mediana. "
        f"Sem isso, o LIMIAR nao reprova a doenca do v2.3."
    )


@pytest.mark.contrato
def test_nenhum_ticker_e_load_bearing():
    """BLIND-04b (o veredito): nenhum ticker sozinho pode mover a mediana da cesta.

    ESTE TESTE SKIPa HOJE, DE PROPOSITO. O `tests/fixtures/holdout_v24.yaml` nasce na
    FASE 14 (VAL-02): cesta estratificada, >= 6 por arquetipo + 10 "dificeis" deliberados.
    A cesta de hoje tem 4 tickers (a do overfit v2.3) — jackknife sobre 4 observacoes e'
    estatisticamente vazio: remover 1 de 4 move a mediana POR CONSTRUCAO. Emitir um veredito
    sobre isso seria fabricar um resultado.

    POR QUE `skip` E NAO `xfail`: a ausencia do fixture NAO e' uma doenca a curar — e' uma
    DEPENDENCIA DE FASE. Um `xfail` aqui viraria XPASS no dia em que a Fase 14 criasse o
    fixture, quebrando a suite por um motivo que nao tem nada a ver com a doenca. Sinal
    trocado e' pior que sinal ausente.

    CONTRATO DO FIXTURE (o que a Fase 14 precisa entregar) — mapa `ticker -> {v_modelo,
    fair_value}`. A metrica e' a razao `v_modelo / fair_value` (VAL-05): o modelo contra uma
    referencia INDEPENDENTE, jamais contra o preco de mercado.

    O limiar e' `h.LIMIAR_JACKKNIFE_PP(len(razoes))` (funcao de `n`, Plano 14-02) e o desvio
    observado e' NORMALIZADO pela mesma escala (`desvio_jackknife_normalizado`) — os dois lados na
    MESMA unidade (desvio em MADs), nunca a constante magica de antes.
    """
    if not h.HOLDOUT_V24.exists():
        pytest.skip(
            "a cesta estratificada nasce na FASE 14 (VAL-02); jackknife sobre os 4 tickers "
            "do v2.3 e' estatisticamente vazio"
        )

    cesta = yaml.safe_load(h.HOLDOUT_V24.read_text(encoding="utf-8")) or {}
    razoes = [
        float(d["v_modelo"]) / float(d["fair_value"])
        for d in cesta.values()
        if d.get("v_modelo") and d.get("fair_value")
    ]

    mediana, _ = h.mediana_jackknife(razoes)
    desvio_norm = h.desvio_jackknife_normalizado(razoes)
    limiar = h.LIMIAR_JACKKNIFE_PP(len(razoes))
    assert desvio_norm <= limiar, (
        f"um unico ticker e' LOAD-BEARING: remove-lo move a mediana de V/FairValue em "
        f"{desvio_norm:.4f} MADs (mediana {mediana:.4f}), acima do limiar de {limiar:.4f} "
        f"para n = {len(razoes)}. A calibracao esta apoiada NUM TICKER, nao na "
        f"distribuicao — e' a doenca do v2.3 se repetindo."
    )
