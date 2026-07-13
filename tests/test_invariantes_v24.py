"""As DUAS DOENCAS do v2.4, escritas como CODIGO EXECUTAVEL (BLIND-02 e BLIND-03).

Os testes deste arquivo que usam `xfail(strict=True)` FALHAM HOJE DE PROPOSITO. Eles nao
sao bugs a corrigir: sao o diagnostico do marco, versionado. Um `xfail(strict=True)` que
volta a passar QUEBRA a suite (XPASS = FAILED, `xfail_strict = true` no pyproject) — e' o
alarme que diz "a doenca foi curada". Nesse dia a acao correta e' REMOVER o `xfail`, nunca
afrouxar o assert.

  BLIND-02 (Doenca 1 — vies de inflacao: Ke NOMINAL contra g REAL)
    (a) test_invariancia_inflacao_identidade_pb_justo -> PASSA hoje. E' algebra pura.
    (b) test_invariancia_inflacao_engine_itub4        -> xfail. Vira verde na FASE 12.
    A DIFERENCA ENTRE (a) E (b) E' A DOENCA. (a) prova que a invariancia a inflacao e'
    POSSIVEL; (b) prova que a engine de hoje nao a tem.

  BLIND-03 (a normalizacao pune crescimento)
    test_normalizacao_nao_pune_crescimento           -> xfail. Vira verde na FASE 10.

PROIBIDO (Pitfall 5 / post-mortem do v2.3): afrouxar tolerancia, trocar `xfail` por `skip`,
deletar assert, ou mexer num limiar DEPOIS que o teste ficou vermelho.
"""

from __future__ import annotations

import pytest

import helpers_blindagem as h
from analista.report import report

# --------------------------------------------------------------------------- #
# BLIND-02 — invariancia a inflacao.
# --------------------------------------------------------------------------- #

# Base do livro (Cap. 17, Tabelas 41/43) — o caso Itau publicado.
ROE_LIVRO = 0.18
KE_LIVRO = 0.1248
G_LIVRO = 0.0728

# O choque: +300 bps de inflacao, SIMULTANEO em rf/Ke, em g e no ROE (lucro nominal).
BPS_CHOQUE = 300

LIMIAR_INFLACAO = 0.05  # <- NAO MEXER NESTE NUMERO. Justificativa completa logo abaixo.
    # 1. E' 5%, e nao os 2% do texto original do ROADMAP, porque com `n_fade = 10` a janela
    #    explicita do RIM tem um PISO ESTRUTURAL MEDIDO de -4,68%: a perpetuidade e'
    #    exatamente invariante a inflacao, mas a janela finita NAO e' (ela desconta RI
    #    nominal a Ke nominal sobre um book a custo historico, nao reexpresso). Os 2% eram
    #    INALCANCAVEIS sem amarrar o `n_fade` — que e' 1 dos 3 graus de liberdade do
    #    orcamento do BLIND-06. Um teste que so' pode ficar verde matando um grau de
    #    liberdade nao e' um teste, e' um knob disfarcado.
    # 2. Os 5% foram fixados na PRIMEIRA ESCRITA, com a medicao na mao. Isto NAO e'
    #    "afrouxar tolerancia": o proibido (Pitfall 5) e' mexer no limiar DEPOIS que o teste
    #    fica vermelho. Fixar um limiar alcancavel antes de escrever o assert e' o oposto.
    # 3. Delta MEDIDO hoje no ITUB4 sob o choque completo de +300 bps: +18,02%
    #    (V 32,88 -> 38,80). Folga de 3,6x sobre o limiar — o teste nao esta na borda.
    #    Cesta inteira, mesma medicao: BBAS3 +45,44% · BBSE3 +6,49% · ITUB4 +18,02%.
    # 4. Se este teste ficar VERMELHO por XPASS, e' porque a doenca FOI CURADA. A acao
    #    correta e' REMOVER o `xfail` — nunca alterar este limiar.


@pytest.mark.invariante
def test_invariancia_inflacao_identidade_pb_justo():
    """BLIND-02(a): a ponte auditavel do ENG-08 e' EXATAMENTE invariante a inflacao.

    Identidade fechada:  P/B justo = 1 + (ROE_T - Ke) / (Ke - g)

    Um choque de inflacao de +300 bps que sobe as TRES pernas (ROE, Ke e g) preserva
    `(ROE - Ke)` E `(Ke - g)` -> o P/B justo nao se move NEM UM DECIMO DE CENTAVO. Por isso
    o assert e' exato (< 1e-9), nao uma banda: e' algebra, nao medicao.

    E' KNOB-PROOF: nao le o `config.yaml`, nao passa pela engine. Knob nenhum pode faze-lo
    passar ou falhar. E' a guarda permanente da ponte auditavel do ENG-08.

    ESTE TESTE E' A PROVA DE QUE A INVARIANCIA A INFLACAO E' POSSIVEL. O teste (b) aplica o
    MESMO choque contra a engine real — e falha. A diferenca entre (a) e (b) E' A DOENCA 1.

    (Corolario que mata a spec literal original do BLIND-02: chocar so' `Ke` e `g`, deixando
    o ROE parado, preserva `(Ke - g)` mas COMPRIME `(ROE - Ke)` em exatamente delta -> o P/B
    justo despenca. Um ROE congelado e' um ROE REAL comparado com um Ke NOMINAL: e' a propria
    Doenca 1, uma camada abaixo. Invariancia a inflacao EXIGE chocar o lucro nominal.)
    """

    def pb_justo(roe: float, ke: float, g: float) -> float:
        return 1.0 + (roe - ke) / (ke - g)

    delta = BPS_CHOQUE / 10_000

    pb_base = pb_justo(ROE_LIVRO, KE_LIVRO, G_LIVRO)
    pb_chocado = pb_justo(ROE_LIVRO + delta, KE_LIVRO + delta, G_LIVRO + delta)

    assert abs(pb_chocado - pb_base) < 1e-9, (
        f"a identidade fechada do ENG-08 nao e' invariante a inflacao: "
        f"P/B {pb_base:.6f} -> {pb_chocado:.6f} sob +{BPS_CHOQUE} bps em (ROE, Ke, g)"
    )


@pytest.mark.invariante
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Doenca 1 (vies de inflacao): Ke nominal contra g real. Vira VERDE sozinho na "
        "FASE 12, quando o ke_teto sair. NAO 'consertar' este teste."
    ),
)
def test_invariancia_inflacao_engine_itub4():
    """BLIND-02(b): a ENGINE nao e' invariante a inflacao. FALHA HOJE — e' a Doenca 1.

    O MESMO choque de +300 bps do teste (a), agora contra `report.analisar_acao`: sobe
    `capm.rf_local`, `ddm.g_estavel`, `motores.rim.g_terminal` E o lucro nominal (que sobe o
    ROE em exatos +300 bps, sem tocar o book — `helpers_blindagem.choque_nominal`).

    Sobre o ITUB4: e' o caso do proprio livro E a violacao com maior significado economico da
    cesta (V 32,88 -> 38,80, +18,02% medido em 2026-07-13).

    POR QUE O `V` SOBE (e nao cai, como a intuicao "inflacao destroi valor" sugere): o
    `ke_teto = 0,13` SATURA. Na base, 3 dos 4 bancos ja' estao no teto; sob o choque, os 4
    estao. O `Ke` nao se move NEM 1 BP — a perna do `rf` e' integralmente absorvida pelo
    clamp. So' o `g` sobe -> o spread `Ke - g` encolhe -> o `V` sobe. Por isso o assert e'
    sobre `abs(delta)`, NUNCA sobre o sinal.

    POR QUE FASE 12 E NAO 11: enquanto o `ke_teto` existir, ele continua saturando e a perna
    do `rf` continua absorvida — o teste continua falhando mesmo depois que o `g` for
    consertado na Fase 11. So' quando o clamp SAI (KE-04, Fase 12) a invariancia passa a ser
    alcancavel. Nao "consertar" o teste na Fase 11 por ele nao ter ficado verde.

    O piso estrutural que sobra depois da cura e' de -4,68% com `n_fade = 10` (a janela
    explicita finita nao e' invariante; so' a perpetuidade e'). Daqui vem o limiar de 5%.
    """
    empresas, cfg = h.cfg_e_empresas_do_snapshot()
    empresas_chocadas, cfg_chocado = h.choque_nominal(empresas, cfg, BPS_CHOQUE)

    base = {c.ticker: c for c in empresas}["ITUB4"]
    chocada = {c.ticker: c for c in empresas_chocadas}["ITUB4"]

    v_base = report.analisar_acao(base, cfg).intrinseco_motor
    v_chocado = report.analisar_acao(chocada, cfg_chocado).intrinseco_motor

    assert v_base and v_chocado, "sem intrinseco: o choque quebrou a engine (nao e' a doenca)"

    variacao = abs(v_chocado / v_base - 1)
    assert variacao < LIMIAR_INFLACAO, (
        f"a engine NAO e' invariante a inflacao: +{BPS_CHOQUE} bps simultaneos em "
        f"(rf, g, ROE) movem o V de R$ {v_base:.2f} para R$ {v_chocado:.2f} "
        f"({v_chocado / v_base - 1:+.2%}), acima do limiar de {LIMIAR_INFLACAO:.0%}. "
        f"E' a Doenca 1: Ke nominal descontando g real."
    )
