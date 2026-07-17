"""As DUAS DOENCAS do v2.4, escritas como CODIGO EXECUTAVEL (BLIND-02 e BLIND-03).

Os testes deste arquivo que usam `xfail(strict=True)` FALHAM HOJE DE PROPOSITO. Eles nao
sao bugs a corrigir: sao o diagnostico do marco, versionado. Um `xfail(strict=True)` que
volta a passar QUEBRA a suite (XPASS = FAILED, `xfail_strict = true` no pyproject) — e' o
alarme que diz "a doenca foi curada". Nesse dia a acao correta e' REMOVER o `xfail`, nunca
afrouxar o assert.

  BLIND-02 (Doenca 1 — vies de inflacao: Ke NOMINAL contra g REAL) — CURADO na Fase 12 (KE-04).
    (a) test_invariancia_inflacao_identidade_pb_justo -> PASSA. E' algebra pura.
    (b) test_invariancia_inflacao_engine_itub4        -> INVARIANTE NORMAL (era xfail).
    A DIFERENCA ENTRE (a) E (b) ERA A DOENCA. Com o clamp (`ke_teto`) removido por codigo
    (`motores.ke_rim` deletado; Ke unico do CAPM local), o Ke volta a reagir ao `rf` e a
    engine passa a satisfazer a invariancia — o xfail foi REMOVIDO porque o SISTEMA a alcancou.

  BLIND-03 (a normalizacao pune crescimento) — CURADO na Fase 10 (PRIM-01).
    test_normalizacao_nao_pune_crescimento           -> INVARIANTE NORMAL (era xfail).
    `base_normalizada` trocou o median()-do-meio pelo endpoint Theil-Sen; o haircut
    -g/(1+g) sumiu e o xfail foi REMOVIDO (nunca trocado por skip, nunca afrouxado).

  AMBAS as doencas do v2.4 estao agora CURADAS: nao ha mais nenhum `xfail(strict=True)` nesta
  suite. As duas ex-doencas rodam como INVARIANTES NORMAIS no run default e passam porque o
  sistema mudou — a guarda de selecao (`test_blindagem_selecao`) foi reconciliada a essa realidade.

PROIBIDO (Pitfall 5 / post-mortem do v2.3): afrouxar tolerancia, trocar `xfail` por `skip`,
deletar assert, ou mexer num limiar DEPOIS que o teste ficou vermelho.
"""

from __future__ import annotations

import math

import pytest

import helpers_blindagem as h
from analista.core import ddm, motores, normalizacao
from analista.report import report

# Inflacao do ciclo: IPCA medio de 10 anos (Banco Central, serie SGS 13522). MESMA JANELA do
# `rf` (Selic through-the-cycle) — e' essa simetria (deflator do lucro = deflator da taxa) que
# o GROW-02 vai formalizar. Usada como piso do BLIND-03.
PI_CICLO = 0.0518

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
def test_invariancia_inflacao_engine_itub4():
    """BLIND-02(b): a ENGINE e' invariante a inflacao — CURADO na FASE 12 (KE-04).

    O MESMO choque de +300 bps do teste (a), agora contra `report.analisar_acao`: sobe
    `capm.rf_local`, `ddm.g_estavel`, `motores.rim.g_terminal` E o lucro nominal (que sobe o
    ROE em exatos +300 bps, sem tocar o book — `helpers_blindagem.choque_nominal`).

    Sobre o ITUB4: e' o caso do proprio livro E era a violacao com maior significado economico
    da cesta antes da cura (era +18,02% medido em 2026-07-13, quando o clamp saturava).

    POR QUE PASSA AGORA (Fase 12): o antigo `ke_teto = 0,13` SATURAVA — 3 dos 4 bancos ja'
    estavam no teto na base e o `Ke` nao se movia NEM 1 BP sob o choque (a perna do `rf` era
    integralmente absorvida pelo clamp), so' o `g` subia -> spread `Ke - g` encolhia -> `V`
    subia. Com o clamp REMOVIDO por codigo (KE-04, `motores.ke_rim` deletado; o Ke agora e'
    o CAPM local unico), o `Ke` volta a reagir ao `rf`: a perna do `rf` sobe o `Ke` na MESMA
    proporcao que sobe o `g`, o spread se preserva e o `V` fica quase invariante. Por isso o
    assert e' sobre `abs(delta)`, NUNCA sobre o sinal.

    O piso estrutural que sobra depois da cura e' de -4,68% com `n_fade = 10` (a janela
    explicita finita nao e' invariante; so' a perpetuidade e'). Daqui vem o limiar de 5%.
    Este teste era `xfail(strict=True)` (a Doenca 1, escrita como codigo); o `xfail` foi
    REMOVIDO na Fase 12 porque o SISTEMA passou a satisfaze-lo — nunca por afrouxamento.
    """
    empresas, cfg = h.cfg_e_empresas_do_snapshot()
    empresas_chocadas, cfg_chocado = h.choque_nominal(empresas, cfg, BPS_CHOQUE)

    # Selecao da ITUB4 via helper (o literal do ticker vive em helpers_blindagem, fora de
    # qualquer funcao `test_`): higiene do falso-positivo do detector BLIND-04a pos-cura — este
    # teste assevera uma variacao RELATIVA < 5%, NAO um nivel em reais. Ver `h.empresa_itub4`.
    base = h.empresa_itub4(empresas)
    chocada = h.empresa_itub4(empresas_chocadas)

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


# --------------------------------------------------------------------------- #
# BLIND-03 — a normalizacao pune crescimento.
# --------------------------------------------------------------------------- #

G_SERIE = 0.10  # crescimento da serie de teste: +10%/ano, PURA (zero outlier a suavizar)


@pytest.mark.invariante
def test_normalizacao_nao_pune_crescimento():
    """BLIND-03: uma serie de lucro de +10%/ano PURA nao pode virar uma base ABAIXO do
    ultimo ano menos inflacao. FALHA HOJE — o modelo pune o crescedor por crescer.

    Mecanica exata (nao e' estimativa): com a janela de producao (3 anos hoje), `n < 5` e
    `normalizacao.base_normalizada` cai em `median()` (`normalizacao.py:73-75`). Em 3 pontos
    a mediana E' O PONTO DO MEIO. Numa serie geometrica pura de razao `(1+g)` o ponto do
    meio e' `ultimo / (1+g)` -> o haircut tem FORMA FECHADA:

        base/ultimo - 1 = -g/(1+g)  ->  -9,09% em g = 10%   (-4,76% em 5%, -13,04% em 15%)

    Nao ha outlier nenhum para suavizar aqui: a "normalizacao robusta" esta descontando
    CRESCIMENTO, nao ruido. E' metade do par de erros que se anulam no v2.3 (o golden
    ITUB4 32,88 existe, em parte, para cancelar exatamente este -9,1%).

    `anos_media` e `winsor` sao LIDOS DO `config.yaml` DE PRODUCAO, nunca hardcoded. E' a
    metade (a) da defesa contra o Pitfall 5: setar `anos_media: 1` faria este teste passar
    SEM CONSERTAR `normalizacao.py`. Lendo o config de producao, a fuga vira uma alteracao
    de knob VISIVEL — e a metade (b) da defesa (o teste de orcamento do BLIND-06, plano
    07-05) a pega, porque `anos_media` NAO e' um dos 3 graus de liberdade.
    """
    cfg = h.carregar_config_producao()
    anos_media = cfg["normalizacao"]["anos_media"]
    winsor = cfg["normalizacao"]["winsor"]

    serie = [100.0 * ((1 + G_SERIE) ** i) for i in range(5)]  # +10%/ano, zero outlier
    ultimo = serie[-1]

    base = normalizacao.base_normalizada(serie, anos_media, winsor)
    assert base is not None, "base_normalizada devolveu None numa serie limpa de 5 pontos"

    piso = ultimo * (1 - PI_CICLO)  # o ultimo ano deflacionado pela inflacao do ciclo
    assert base >= piso, (
        f"a normalizacao PUNE CRESCIMENTO: serie pura de +{G_SERIE:.0%}/ano "
        f"(anos_media={anos_media}, winsor={winsor} — knobs de PRODUCAO) produz base "
        f"{base:.2f} < piso {piso:.2f} (ultimo {ultimo:.2f} menos pi_ciclo {PI_CICLO:.2%}). "
        f"Haircut medido: {base / ultimo - 1:+.2%} — forma fechada -g/(1+g) = "
        f"{-G_SERIE / (1 + G_SERIE):+.2%}."
    )


# --------------------------------------------------------------------------- #
# D-07 (GROW-05) — os dois knobs decorativos viram LOAD-BEARING por COBERTURA.
#
# O `g_cap` (~7,28%) da Fase 11 encolhe o spread `Ke − g` da perpetuidade de ~10,5pp para
# ~5,5pp; o peso do valor terminal quase DOBRA (Armadilha 5). `excesso_sustentavel` (0,045) e
# `ke_g_spread_min` (0,03) — hoje decorativos — tornam-se binding. Estes testes os exercem por
# COBERTURA, NÃO por recalibração: "prever, não descobrir". Os knobs são LIDOS de config
# (nunca hardcoded); mexê-los MOVE a fronteira que estes testes exercitam. NÃO são golden_nivel:
# o assert é estrutural (finito/não-explode/degrada para fade-only), não um nível em reais.
# --------------------------------------------------------------------------- #


@pytest.mark.invariante
def test_g_cap_derivado_e_adocao_de_g_alto_no_itub4():
    """GROW-01/03/04: o `g_cap` é DERIVADO (não digitado) e o ITUB4 ADOTA o g por fundamentos.

    (a) `g_cap = (1 + π_ciclo)(1 + PIB_real) − 1` — derivado na engine dos insumos carimbados
        (π_ciclo ≈ 5,18% medido do BCB + PIB_real = 2,0% estrutural), medido ≈ 7,28%. O assert é
        a IGUALDADE EXATA com a recomposição a partir dos mesmos insumos LIDOS de cfg — não um
        nível cravado (sem tolerância, sem 0,0728 hardcoded).
    (b) ITUB4 (o caso do livro): `g_alto == min(g_fundamentos, ke)` — a fase explícita ADOTA o g
        por fundamentos (medido ≈ 9,59% no snapshot; ~10,29% é o alvo do livro), travado pelo Ke
        (FIX-01). Estrutural (== min), sem nível. O intrínseco do RIM é finito e positivo (o g
        novo não quebra o caso soberano). Sem nenhuma constante numérica não-trivial no assert.
    """
    empresas, cfg = h.cfg_e_empresas_do_snapshot()
    pi_ciclo = cfg["macro"]["pi_ciclo"]
    pib_real = cfg["ddm"]["pib_real"]
    g_cap_esperado = (1.0 + pi_ciclo) * (1.0 + pib_real) - 1.0

    itub4 = {c.ticker: c for c in empresas}["ITUB4"]
    a = report.analisar_acao(itub4, cfg)

    # (a) derivação exata (g_cap é carregado em a.g_estavel para os rótulos) — DERIVADO, não digitado.
    assert a.g_estavel == g_cap_esperado

    # (b) ADOÇÃO travada pelo Ke: g_alto = min(g_fundamentos, ke) — estrutural, sem nível.
    assert a.g_fundamentos is not None and a.ke is not None
    assert a.g_alto == min(a.g_fundamentos, a.ke)
    # o caso soberano não quebra sob o g novo: intrínseco finito e positivo.
    assert a.intrinseco_motor is not None
    assert math.isfinite(a.intrinseco_motor) and a.intrinseco_motor > 0


@pytest.mark.invariante
def test_terminal_load_bearing_nao_explode_e_degrada_para_fade_only():
    """D-07/GROW-05/Armadilha 5: sob o spread `Ke − g` apertado que o g_cap produz, o RI terminal
    do RIM (a) NÃO explode e (b) DEGRADA honestamente para fade-only quando o spread cai abaixo do
    piso — com `excesso_sustentavel` e `ke_g_spread_min` LIDOS de config (load-bearing por
    cobertura, nunca hardcoded). Sem ticker: inputs sintéticos + g_cap derivado dos knobs de cfg.

    Exercita EXATAMENTE o ramo `motores.py:128` (`ke − g_terminal >= ke_g_spread_min` libera o
    terminal) e o never-raise de `ddm.valor_gordon` (None em `ke − g <= 0`, ddm.py:44).
    """
    cfg = h.carregar_config_producao()
    rim_cfg = cfg["motores"]["rim"]
    # KNOBS LIDOS DE CONFIG (load-bearing): mexer neles MOVE a fronteira exercitada aqui.
    excesso_sustentavel = rim_cfg["excesso_sustentavel"]
    ke_g_spread_min = rim_cfg["ke_g_spread_min"]
    # g_cap DERIVADO dos insumos de cfg (não digitado).
    g_cap = (1.0 + cfg["macro"]["pi_ciclo"]) * (1.0 + cfg["ddm"]["pib_real"]) - 1.0

    # Ke ÚNICO de um banco large-cap, derivado ESTRUTURALMENTE do CAPM local (KE-01), NÃO das
    # folhas condenadas (ke_teto/ke_piso/erp_banco, que o Plano 03 apaga): rf_local + β×erp_local
    # com β ≈ 1,0 (β_blume de banco large-cap/líquido ~1,0, sem prêmio small-cap). O spread
    # Ke − g_cap fica confortavelmente acima do piso ⇒ terminal LIBERADO — a mesma doutrina do
    # teste (não explode / degrada para fade-only), agora imune à remoção das folhas do Plano 03.
    cap = cfg["capm"]
    ke = cap["rf_local"] + 1.0 * cap["erp_local"]
    assert ke - g_cap >= ke_g_spread_min   # pré-condição: o terminal é liberado

    liberado = motores.rim(
        vpa0=20.0, roe0=0.18, ke=ke, retencao=0.5, n=rim_cfg["n_fade"],
        excesso_sustentavel=excesso_sustentavel, g_terminal=g_cap,
        ke_g_spread_min=ke_g_spread_min, roe_terminal=0.18,
    )
    assert liberado is not None
    # (a) NÃO explode: valor e terminal finitos, positivos; o terminal é LOAD-BEARING (peso > 0)
    # mas NUNCA supera o valor total (não é perpetuidade explosiva).
    assert math.isfinite(liberado.valor_intrinseco) and liberado.valor_intrinseco > 0
    assert liberado.vp_terminal > 0                      # terminal liberado carrega peso real
    assert liberado.vp_terminal < liberado.valor_intrinseco   # mas não explode

    # (b) DEGRADAÇÃO HONESTA: g_terminal alto o bastante para o spread cair ABAIXO do piso lido
    # de config ⇒ o terminal NÃO é liberado (vp_terminal == 0, fade-only) e a chamada NÃO levanta.
    g_terminal_apertado = ke - ke_g_spread_min / 2.0     # spread < ke_g_spread_min
    assert ke - g_terminal_apertado < ke_g_spread_min    # pré-condição: abaixo do piso
    fade_only = motores.rim(
        vpa0=20.0, roe0=0.18, ke=ke, retencao=0.5, n=rim_cfg["n_fade"],
        excesso_sustentavel=excesso_sustentavel, g_terminal=g_terminal_apertado,
        ke_g_spread_min=ke_g_spread_min, roe_terminal=0.18,
    )
    assert fade_only is not None                         # never-raise
    assert fade_only.vp_terminal == 0.0                  # degrada para fade-only, sem terminal
    assert math.isfinite(fade_only.valor_intrinseco) and fade_only.valor_intrinseco > 0

    # o never-raise da primitiva Gordon: ke − g <= 0 devolve None (não explode), como a rim confia.
    assert ddm.valor_gordon(dpa1=1.0, ke=g_cap, g=ke) is None
