"""BLIND-06 — O ORCAMENTO DE KNOBS. Exatamente 3 graus de liberdade, travados por teste.

O post-mortem, em uma linha: o v2.3 gastou ~8 graus de liberdade sobre 4 observacoes (uma
cesta de 4 bancos) e NINGUEM CONTOU. Um modelo com mais knobs do que observacoes nao e' um
modelo — e' uma interpolacao. Este arquivo faz a contagem virar um teste.

Os quatro testes, e o que cada um impede:

  1. test_orcamento_de_knobs_e_exatamente_3
     Impede que um 4o grau de liberdade APARECA. E impede o furo mais silencioso: um knob
     NOVO no `config.yaml` que ninguem declarou (ou um knob deletado e esquecido no lock).
     A verificacao e' de PARTICAO, nao de contagem.

  2. test_knobs_batem_com_o_lock
     O DENTE do requisito. Mexer num knob deixa de ser INVISIVEL: a mudanca tem que
     aparecer no `calibracao.lock.yaml`, no MESMO diff. E' o que a torna revisavel.

  3. test_nenhuma_justificativa_de_knob_menciona_ticker
     A regra escrita do ROADMAP, EXECUTAVEL. Uma justificativa que cita um ticker nao
     explica por que o numero e' aquele — ela confessa CONTRA O QUE ele foi ajustado.

  4. test_a_suite_reage_a_um_knob_grosseiramente_errado
     O CANARIO (PITFALLS P5.4): a prova de que a suite nova CONSEGUE REPROVAR.

PROIBIDO: "consertar" qualquer um destes afrouxando o assert, ou mexendo num VALOR do
`config.yaml`. Se um destes ficar vermelho, o que mudou foi o SISTEMA, nao o teste.
"""

from __future__ import annotations

import copy

import pytest

import helpers_blindagem as h
from analista.report import report

# --------------------------------------------------------------------------- #
# 1. O orcamento: exatamente 3 — e a particao do escopo e' completa.
# --------------------------------------------------------------------------- #


@pytest.mark.contrato
def test_orcamento_de_knobs_e_exatamente_3():
    """A superficie de valuation esta INTEIRAMENTE declarada, e so' 3 folhas sao livres.

    "3 graus de liberdade" so' e' testavel contra um ESCOPO DECLARADO. Sem ele, o teste ou
    e' vazio (nao ha o que contar) ou e' impossivel (o config tem 110 folhas).

    A verificacao e' de PARTICAO — `folhas(escopo) == graus | congelados` — e nao de mera
    contagem, porque a contagem sozinha tem dois furos:
      - knob NOVO no config, nao declarado no lock  -> nasceria calibravel em silencio;
      - knob DELETADO do config, esquecido no lock  -> o lock viraria ficcao.
    Os dois lados sao reportados na mensagem de erro.
    """
    cfg = h.carregar_config_producao()
    lock = h.carregar_lock()

    folhas = set(h.folhas_do_escopo(cfg, lock["escopo"]))
    graus = {spec["caminho"] for spec in lock["graus_de_liberdade"].values()}
    congelados = set(lock["congelados"])
    declaradas = graus | congelados

    nao_declaradas = folhas - declaradas
    fantasmas = declaradas - folhas
    assert folhas == declaradas, (
        "a superficie de valuation e o `calibracao.lock.yaml` divergiram.\n"
        f"  knobs no config.yaml SEM declaracao no lock: {sorted(nao_declaradas)}\n"
        "    -> um knob nao declarado nasce CALIBRAVEL EM SILENCIO. Declare-o em "
        "`congelados` (ou, se ele PRECISA ser calibravel, mate outro grau de liberdade).\n"
        f"  declaracoes no lock SEM knob no config.yaml: {sorted(fantasmas)}\n"
        "    -> o knob morreu e o lock virou ficcao. Remova a linha."
    )

    assert graus & congelados == set(), (
        f"knob declarado nos DOIS lados: {sorted(graus & congelados)}. "
        "Um knob e' livre ou congelado — nao os dois."
    )

    assert len(lock["graus_de_liberdade"]) == 3, (
        f"ORCAMENTO ESTOURADO: {len(lock['graus_de_liberdade'])} graus de liberdade "
        f"({sorted(lock['graus_de_liberdade'])}), esperado 3 (ERP, n_fade, PIB_real).\n"
        "Um 4o grau de liberdade e' EXATAMENTE como o v2.3 gastou ~8 sobre 4 observacoes. "
        "Se um knob PRECISA ser calibravel, OUTRO PRECISA MORRER. E' um orcamento, nao uma "
        "lista de desejos."
    )

    # D-04 — o 4o grau de liberdade ESCONDIDO. `veredito.margem_seguranca` MULTIPLICA o `V`,
    # mas nao mora em nenhum bloco de valuation: sem esta linha ela escaparia do escopo e o
    # orcamento teria um furo do tamanho de um multiplicador. E' a Armadilha 4, fechada por
    # declaracao (o livro: "se 5%, 10% ou qualquer outro valor, e' VOCE quem decide" -> ela
    # e' um controle do USUARIO, ENG-06/Fase 13, nunca um knob calibrado contra dispersao,
    # preco ou taxa de compra).
    assert "veredito.margem_seguranca" in lock["user_control"], (
        "a `veredito.margem_seguranca` sumiu do `user_control` do lock. Ela MULTIPLICA o V: "
        "solta, e' um 4o grau de liberdade escondido. Ela fica CONGELADA e ETIQUETADA ate o "
        "ENG-06 — nunca como grau de liberdade."
    )


# --------------------------------------------------------------------------- #
# 2. O dente: mexer num knob deixa de ser invisivel.
# --------------------------------------------------------------------------- #


@pytest.mark.contrato
def test_knobs_batem_com_o_lock():
    """Todo knob da superficie de valuation vale, no config, EXATAMENTE o que o lock diz.

    E' ESTE teste que transforma "mexer num knob" de um evento INVISIVEL num evento
    REVISAVEL. Sem ele, um numero muda de 0,13 para 0,11 no meio de um commit de 400 linhas
    e ninguem ve. Com ele, a mudanca OBRIGA um diff no `calibracao.lock.yaml` — um arquivo
    de 200 linhas cujo unico proposito e' ser lido.

    A verificacao e' sobre AS 30 FOLHAS (os 3 graus E os 27 congelados), nao so' sobre os
    graus de liberdade: sao justamente os knobs "congelados" (`ke_teto`, `excesso_sustentavel`)
    que o overfit do v2.3 moveu.
    """
    cfg = h.carregar_config_producao()
    lock = h.carregar_lock()

    esperado: dict[str, object] = {
        spec["caminho"]: spec["valor"] for spec in lock["graus_de_liberdade"].values()
    }
    esperado.update(lock["congelados"])

    divergentes = []
    for caminho, valor_lock in sorted(esperado.items()):
        valor_cfg = h.valor_em(cfg, caminho)
        if valor_cfg != valor_lock:
            divergentes.append(f"  `{caminho}`: lock={valor_lock!r} -> config={valor_cfg!r}")

    assert not divergentes, (
        "knob(s) alterado(s) sem atualizar o `calibracao.lock.yaml`:\n"
        + "\n".join(divergentes)
        + "\n\nToda mudanca de knob tem que aparecer no MESMO diff — e' o que a torna "
        "revisavel. Se a mudanca e' LEGITIMA, atualize o lock no mesmo commit (e o hook do "
        "BLIND-05 permite esse par de proposito). Se voce esta aqui porque um golden ficou "
        "vermelho: PARE. Calibrar o knob ate o golden passar e' o post-mortem do v2.3."
    )


# --------------------------------------------------------------------------- #
# 3. A regra do ticker, executavel.
# --------------------------------------------------------------------------- #


@pytest.mark.contrato
def test_nenhuma_justificativa_de_knob_menciona_ticker():
    """"Uma justificativa legitima de knob NUNCA menciona um ticker." — ROADMAP v2.4.

    Uma justificativa que cita um ticker nao explica POR QUE o numero e' aquele: ela
    confessa CONTRA O QUE ele foi ajustado. O `config.yaml` do v2.3 dizia, literalmente,
    `# Move ITUB4 ~R$2` e `# NAO mexer nos knobs acima: mudariam o ITUB4` — o repo instruia
    o proximo executor a calibrar contra um ticker. Este teste tornou isso impossivel.

    Escopo: os 4 blocos de valuation (o lock e' a fonte). O bloco `arquetipo` cita tickers
    em ranges ILUSTRATIVOS de dispersao (uma escala empirica, nao uma justificativa de
    nivel) e fica de fora de proposito — varrer tudo seria limpeza cosmetica sem valor.

    O candidato a ticker vem de regex, mas o VEREDITO vem de `data/ticker_map.json`: a
    regex nua casa `MACD12` (falso positivo REAL, `config.yaml:134`). Um teste que bloqueia
    `MACD12` e' desligado por irritacao antes de barrar o primeiro overfit de verdade.
    """
    ofensores = h.comentarios_com_ticker(h.carregar_lock()["escopo"])

    assert not ofensores, (
        "justificativa de knob mencionando TICKER no config.yaml:\n"
        + "\n".join(
            f"  linha {n} ({', '.join(t)}): {c}" for n, c, t in ofensores
        )
        + "\n\nReescreva a justificativa em termos ECONOMICOS (o que o knob significa), nao "
        "em termos do efeito que ele tem sobre uma acao especifica. Se a unica justificativa "
        "honesta para o numero e' 'e' o que faz o ticker X sair do evitar', entao o numero "
        "nao tem justificativa — tem um alvo."
    )


# --------------------------------------------------------------------------- #
# 4. O CANARIO — a suite CONSEGUE reprovar.
# --------------------------------------------------------------------------- #

# Um erro GROSSEIRO de metodo: o ERP dobrado (6% -> 12%). Nenhum modelo defensavel sobrevive
# a isso sem se mover. Se a engine nao reagir, ela parou de ler o custo de capital.
LIMIAR_CANARIO = 0.05


@pytest.mark.contrato
def test_a_suite_reage_a_um_knob_grosseiramente_errado():
    """CANARIO (PITFALLS P5.4): a blindagem CONSTRANGE alguma coisa.

    Sem este teste, "448 verdes" pode significar "448 DESELECIONADOS". Ele prova que a suite
    nova nao e' MAIS DECORATIVA que a velha: dobrar o ERP (6% -> 12%, um erro grosseiro de
    metodo) MOVE o valor intrinseco. Se ele um dia falhar, e' porque a engine parou de reagir
    ao custo de capital — e NENHUM OUTRO TESTE VAI TE CONTAR ISSO.

    POR QUE O ASSERT E' SOBRE A CESTA, E NAO SOBRE UM TICKER (medido em 2026-07-13, antes de
    escrever o assert — este teste NAO foi calibrado depois de ficar vermelho):

        dobrar `capm.erp_local` move o V da seguradora da cesta em -15,85%
        e move os TRES BANCOS em EXATAMENTE 0,00%.

    Os bancos NAO estao mortos: eles estao SATURADOS. O `ke_teto = 0,13` clampa o Ke do RIM,
    e o `erp_local` so' entra por `ke_live` — que ja' esta acima do teto. O clamp ENGOLE o
    choque inteiro. E' a MESMA saturacao que o `test_invariancia_inflacao_engine_itub4`
    (BLIND-02b) denuncia como a Doenca 3, uma camada acima: um knob que absorve as pernas do
    modelo e as impede de chegar ao numero.

    Um canario escrito sobre UM ticker saturado ficaria VERMELHO HOJE — e a "correcao" obvia
    seria afrouxar o limiar ou trocar o ticker ate passar, que e' o Pitfall 5 pela porta dos
    fundos. Um canario escrito sobre a CESTA afirma a coisa certa ("a engine reage ao custo
    de capital") e e' MONOTONICO NA DIRECAO DA CURA: quando o KE-04 (Fase 12) remover o
    `ke_teto`, os 4 tickers passarao a reagir e o `max` so' CRESCE. Este teste continuara
    verde no dia da cura — e' assim que se escreve um alarme que nao precisa ser "consertado".

    Nao ha ticker literal neste corpo de proposito: os tickers vem do DADO (o snapshot). Nao
    ha nivel em reais cravado — a afirmacao e' RELATIVA (|dV/V|). Nao ha, portanto, nada que
    o BLIND-04a possa confundir com um golden de calibracao.
    """
    empresas, cfg = h.cfg_e_empresas_do_snapshot()

    sabotado = copy.deepcopy(cfg)
    sabotado["capm"]["erp_local"] *= 2

    assert sabotado["capm"]["erp_local"] != cfg["capm"]["erp_local"], (
        "o deepcopy vazou: a sabotagem mutou o config original."
    )

    variacoes: dict[str, float] = {}
    for empresa in empresas:
        v_base = report.analisar_acao(empresa, cfg).intrinseco_motor
        v_sabotado = report.analisar_acao(empresa, sabotado).intrinseco_motor
        if v_base and v_sabotado:
            variacoes[empresa.ticker] = abs(v_sabotado / v_base - 1)

    assert variacoes, (
        "nenhum intrinseco saiu da engine — o canario nao pode nem medir. Isto NAO e' "
        "'a engine nao reagiu': e' a engine quebrada, ou o snapshot vazio."
    )

    maior = max(variacoes.values())
    assert maior > LIMIAR_CANARIO, (
        f"A ENGINE NAO REAGIU AO CUSTO DE CAPITAL DOBRADO.\n"
        f"  ERP {cfg['capm']['erp_local']:.1%} -> {sabotado['capm']['erp_local']:.1%} "
        f"moveu o V de TODA a cesta em menos de {LIMIAR_CANARIO:.0%}:\n"
        + "\n".join(f"    {t}: {v:+.2%}" for t, v in sorted(variacoes.items()))
        + "\n\nUm erro GROSSEIRO de metodo passou despercebido. Se nem isto a suite pega, "
        "'suite verde' nao significa nada — e nenhum outro teste vai te contar. NAO afrouxe "
        "este limiar: procure o knob que esta engolindo o choque (hoje, o `ke_teto`)."
    )
