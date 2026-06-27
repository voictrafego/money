"""Golden unitário da primitiva de normalização de lucro (FIX-04, raiz da cascata).

A camada de normalização entrega a base de lucro robusta a UM exercício atípico
(recuperação de créditos fiscais, distribuição extraordinária) que hoje contamina
ROE/CAGR/payout/DY do valuation. Espelha o espírito BSD (Cap. 8.4): médias trienais
+ winsorização. Funções puras: recebem números, devolvem números (sem rede, sem I/O).

Regras travadas aqui (documentadas em normalizacao.py):
- N == 0 válido            -> None (degradação graciosa, série vazia/só-None)
- N == 1 válido            -> o próprio valor (não há o que suavizar)
- 2 <= N < 5 válidos       -> mediana (winsor não morde poucos pontos; robusta a 1 outlier)
- N >= 5 válidos           -> média winsorizada (extremos clampados aos percentis)
"""

from analista.core import normalizacao as norm


# --------------------------------------------------------------------------- #
# base_normalizada — número-síntese canônico
# --------------------------------------------------------------------------- #
def test_outlier_alto_suavizado_pela_mediana():
    # [100, 105, 300]: 1 ano 3x os demais. A média (168,3) seria contaminada;
    # a mediana (105) é robusta ao outlier — é o número que o valuation deve usar.
    base = norm.base_normalizada([100, 105, 300], anos_media=3, winsor=0.10)
    assert base is not None
    assert abs(base - 105) < 1e-9
    # e claramente abaixo da média aritmética contaminada.
    assert base < (100 + 105 + 300) / 3


def test_winsor_clampa_extremos_em_serie_longa():
    # N>=5: média winsorizada a 10% clampa o outlier alto (1000) ao percentil 90,
    # então a base fica MUITO abaixo da média crua (que o 1000 explode).
    serie = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1000]
    base = norm.base_normalizada(serie, anos_media=10, winsor=0.10)
    media_crua = sum(serie) / len(serie)  # = 104,5 (explodida pelo 1000)
    assert base is not None
    assert base < media_crua
    assert base < 50  # o 1000 foi clampado: não sobra rastro do extremo


def test_none_ignorado_antes_de_normalizar():
    # Os None não contam como 0: a série efetiva é [100, 105, 300] -> mediana 105.
    base = norm.base_normalizada([100, None, 105, None, 300], anos_media=5, winsor=0.10)
    assert base is not None
    assert abs(base - 105) < 1e-9


def test_serie_curta_degrada_para_valor_unico():
    # 1 ponto válido -> o próprio valor (fallback gracioso).
    assert norm.base_normalizada([42.0], anos_media=3, winsor=0.10) == 42.0
    # Série só-None ou vazia -> None (não quebra, não inventa 0).
    assert norm.base_normalizada([None, None], anos_media=3, winsor=0.10) is None
    assert norm.base_normalizada([], anos_media=3, winsor=0.10) is None


def test_apenas_os_ultimos_anos_media_entram_na_base():
    # anos_media=3: só os 3 últimos válidos contam. O ano antigo atípico (10) é ignorado.
    base = norm.base_normalizada([10, 100, 100, 100], anos_media=3, winsor=0.10)
    assert abs(base - 100) < 1e-9


def test_serie_estavel_base_igual_ao_valor():
    # Empresa estável (todos os anos iguais) -> base == valor cru (valuation inalterado).
    assert norm.base_normalizada([200, 200, 200, 200, 200], anos_media=3) == 200


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
