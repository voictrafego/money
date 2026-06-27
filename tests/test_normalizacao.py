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
# Pureza (T-08-01 / acceptance): primitiva sem ciclo de import com a engine
# --------------------------------------------------------------------------- #
def test_primitiva_e_pura_sem_import_de_fundamentals():
    import inspect

    src = inspect.getsource(norm)
    assert "fundamentals" not in src
    assert "report" not in src
