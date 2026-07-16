"""Golden unitário da primitiva de normalização de lucro (FIX-04, raiz da cascata).

A camada de normalização entrega a base de lucro robusta a UM exercício atípico
(recuperação de créditos fiscais, distribuição extraordinária) que hoje contamina
ROE/CAGR/payout/DY do valuation. Espelha o espírito BSD (Cap. 8.4): médias trienais
+ winsorização. Funções puras: recebem números, devolvem números (sem rede, sem I/O).

Regras travadas aqui (documentadas em normalizacao.py) — PRIM-01 dividiu o estimador:
- base_normalizada (base de VALUATION) = ENDPOINT de tendência robusta (Theil-Sen) no ano
  atual — reflete o crescimento recente e é robusto a UM exercício atípico. Ladder curta
  (D-01b): vazio -> None; N==1 -> o próprio valor; N==2 -> média dos dois. GUARD de
  degeneração: endpoint <= 0 -> median(janela) (nunca devolve base negativa).
- media_ciclo (motor CÍCLICO) = média/mediana through-cycle (o estimador ANTIGO), robusto a
  UM prejuízo recente: vazio -> None; N==1 -> valor; 2<=N<5 -> mediana; N>=5 -> winsorizada.
"""

from statistics import median

from analista.core import normalizacao as norm


# --------------------------------------------------------------------------- #
# base_normalizada — ENDPOINT de tendência robusta (Theil-Sen), PRIM-01/D-01
# --------------------------------------------------------------------------- #
def test_endpoint_reflete_crescimento_e_nao_pune_o_ano_recente():
    # ANTES (doença BLIND-03): o median()-de-3 devolvia o ANO-DO-MEIO e punia o crescedor
    # (haircut fechado -g/(1+g) = -9,1% em g=10%). AGORA: o endpoint da tendência robusta
    # reflete o ANO ATUAL — fica ACIMA da mediana-do-meio, não abaixo.
    serie = [100.0, 110.0, 121.0, 133.1, 146.41]  # +10%/ano puro, zero outlier a suavizar
    base = norm.base_normalizada(serie, anos_media=5, winsor=0.10)
    assert base is not None
    assert base > median(serie)   # não pune crescimento (mediana-do-meio = 121, seria o haircut)
    assert 143.0 < base < 146.0   # ~144,15 (endpoint Theil-Sen, janela 5)


def test_endpoint_robusto_a_pico_terminal_na_janela_5():
    # Um PICO atípico (2x) no penúltimo ano. Na janela de 5, a regressão robusta NÃO persegue
    # o pico (median-of-slopes o ignora): o endpoint fica na TENDÊNCIA (~145), não em ~266.
    serie = [100.0, 110.0, 121.0, 266.2, 146.41]
    base = norm.base_normalizada(serie, anos_media=5, winsor=0.10)
    assert base is not None
    assert base < 170.0          # o pico não estoura a base
    assert 143.0 < base < 148.0  # ~144,74: robusto ao pico E ainda reflete a tendência


def test_guard_endpoint_negativo_degrada_para_mediana():
    # Série em queda com prejuízo recente: o endpoint da tendência seria NEGATIVO (-40).
    # O GUARD degrada para median(janela) e NUNCA devolve base negativa (protege RIM/DCF).
    serie = [100.0, 50.0, -80.0]
    base = norm.base_normalizada(serie, anos_media=3, winsor=0.10)
    assert base is not None
    assert base > 0                  # guard: nunca negativo
    assert abs(base - 50.0) < 1e-9   # median([100, 50, -80]) = 50 (degradação graciosa)


def test_media_ciclo_e_a_media_through_cycle_nao_o_endpoint():
    # O ESTIMADOR DIVIDIDO (RESEARCH §Estimator split): o motor cíclico quer a força de lucro
    # do MEIO do ciclo, não o ano atual. media_ciclo devolve a média/mediana (comportamento
    # ANTIGO), que numa série crescente fica ABAIXO do endpoint que base_normalizada usa.
    serie = [100.0, 110.0, 121.0, 133.1, 146.41]
    mc = norm.media_ciclo(serie, anos_media=5, winsor=0.10)
    bn = norm.base_normalizada(serie, anos_media=5, winsor=0.10)
    assert mc is not None and bn is not None
    assert mc < bn                # média through-cycle (~121,8) < endpoint recente (~144,2)
    assert abs(mc - 121.84) < 0.5  # winsorized-mean preservada no ramo cíclico


def test_none_ignorado_e_endpoint_da_serie_limpa():
    # Os None não contam como 0: a série efetiva é [100, 110, 121].
    com_none = norm.base_normalizada([100, None, 110, None, 121], anos_media=5, winsor=0.10)
    sem_none = norm.base_normalizada([100, 110, 121], anos_media=5, winsor=0.10)
    assert com_none is not None
    assert abs(com_none - sem_none) < 1e-9  # None puramente ignorado (não é 0 na regressão)
    assert abs(com_none - 120.5) < 0.5      # endpoint da tendência (não a mediana-do-meio 110)


def test_fallback_dois_pontos_e_media():
    # D-01b: 2 pontos válidos -> média dos dois (Theil-Sen degenera com N=2).
    assert norm.base_normalizada([40.0, 60.0], anos_media=3, winsor=0.10) == 50.0


def test_serie_curta_degrada_para_valor_unico():
    # 1 ponto válido -> o próprio valor (fallback gracioso).
    assert norm.base_normalizada([42.0], anos_media=3, winsor=0.10) == 42.0
    # Série só-None ou vazia -> None (não quebra, não inventa 0).
    assert norm.base_normalizada([None, None], anos_media=3, winsor=0.10) is None
    assert norm.base_normalizada([], anos_media=3, winsor=0.10) is None


def test_apenas_os_ultimos_anos_media_entram_na_base():
    # anos_media=3: só os 3 últimos válidos contam. O ano antigo atípico (10) é ignorado.
    # Série [100,100,100] (tendência plana) -> endpoint = 100.
    base = norm.base_normalizada([10, 100, 100, 100], anos_media=3, winsor=0.10)
    assert abs(base - 100) < 1e-9


def test_serie_estavel_base_igual_ao_valor():
    # Empresa estável (todos os anos iguais) -> endpoint da tendência plana == valor cru.
    assert norm.base_normalizada([200, 200, 200, 200, 200], anos_media=3) == 200


# --------------------------------------------------------------------------- #
# media_ciclo — winsor/mediana through-cycle para o motor cíclico (PRIM-01, split)
# --------------------------------------------------------------------------- #
def test_winsor_clampa_extremos_em_serie_longa():
    # N>=5: a média winsorizada a 10% (agora em media_ciclo) clampa o outlier alto (1000)
    # ao percentil 90, então a base fica MUITO abaixo da média crua (que o 1000 explode).
    serie = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1000]
    base = norm.media_ciclo(serie, anos_media=10, winsor=0.10)
    media_crua = sum(serie) / len(serie)  # = 104,5 (explodida pelo 1000)
    assert base is not None
    assert base < media_crua
    assert base < 50  # o 1000 foi clampado: não sobra rastro do extremo


# --------------------------------------------------------------------------- #
# serie_winsorizada — série (mesmo comprimento) para o CAGR de valuation
# --------------------------------------------------------------------------- #
def test_serie_winsorizada_clampa_extremo_terminal():
    # Um último ano atípico (3x) é clampado: o CAGR de valuation deixa de explodir.
    serie = [100, 102, 104, 106, 108, 110, 112, 114, 116, 360]
    w = norm.serie_winsorizada(serie, winsor=0.10)
    assert w[-1] < 360  # extremo terminal suavizado
    assert len(w) == len(serie)  # preserva comprimento (CAGR usa início e fim)


def test_serie_winsorizada_ignora_none_e_serie_curta():
    # < 5 pontos válidos: winsor não morde, devolve os pontos limpos como estão.
    assert norm.serie_winsorizada([100, None, 200], winsor=0.10) == [100, 200]


# --------------------------------------------------------------------------- #
# mediana_payout — payout sustentável (PAY-01): mediana sobre a série COMPLETA,
# SEM janela de 3a e SEM clamp em 1.0 (D-01/D-03/D-04).
# --------------------------------------------------------------------------- #
def test_mediana_payout_nao_crava_em_1_para_serie_acima_de_100pct():
    # Espírito TAEE11 (D-03): transmissora que distribui de caixa regulatório paga
    # >100% em TODO ano. A mediana é legítima >1.0 — NÃO pode ser cravada em 1.0.
    res = norm.mediana_payout([2.0, 2.1, 2.2, 2.3])
    assert res is not None
    assert res > 1.0  # sem clamp
    assert abs(res - 2.15) < 1e-9  # mediana de 4 = (2.1+2.2)/2


def test_mediana_payout_descarta_spike_extraordinario():
    # D-01: um ano extraordinário do PRÓPRIO histórico (1.30) é naturalmente
    # descartado pela mediana, sem precisar marcar/excluir o ano explicitamente.
    serie = [0.40, 0.45, 0.50, 1.30]
    res = norm.mediana_payout(serie)
    media_crua = sum(serie) / len(serie)  # 0.6625, contaminada pelo spike
    assert res is not None
    assert abs(res - 0.475) < 1e-9  # mediana de 4 = (0.45+0.50)/2
    assert res < media_crua  # mediana abaixo da média contaminada


def test_mediana_payout_usa_serie_completa_nao_so_3_ultimos():
    # D-04: usa TODOS os pontos válidos (não fatia os 3 últimos). Com o ano antigo
    # baixo (0.10), a mediana-de-4 (0.55) difere da mediana-dos-3-últimos (0.60).
    res = norm.mediana_payout([0.10, 0.50, 0.60, 0.70])
    assert res is not None
    assert abs(res - 0.55) < 1e-9  # mediana sobre a série completa
    assert abs(res - 0.60) > 1e-9  # NÃO é a mediana só dos 3 últimos


def test_mediana_payout_ignora_none():
    # Reuso de _limpar: None não conta como 0; série efetiva [0.5, 0.7] -> 0.6.
    res = norm.mediana_payout([0.5, None, 0.7])
    assert res is not None
    assert abs(res - 0.6) < 1e-9


def test_mediana_payout_fronteira_none_e_valor_unico():
    # D-04: fronteira de None preservada. Vazio/só-None -> None; 1 ano -> o próprio valor.
    assert norm.mediana_payout([]) is None
    assert norm.mediana_payout([None, None]) is None
    assert norm.mediana_payout([0.42]) == 0.42


# --------------------------------------------------------------------------- #
# Pureza (T-08-01 / acceptance): primitiva sem ciclo de import com a engine
# --------------------------------------------------------------------------- #
def test_primitiva_e_pura_sem_import_de_fundamentals():
    import inspect

    src = inspect.getsource(norm)
    assert "fundamentals" not in src
    assert "report" not in src
