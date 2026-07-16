"""Testes de MÉTODO das primitivas de valuation de fundamentals (PRIM-02, PRIM-03).

Asserções de MÉTODO (igualdade estrutural), NUNCA golden de nível `ticker == R$/%`:

- `roe_valuation()` = mediana da série de `roe(a)` anuais (lucro_t ÷ PL médio(t-1,t)),
  NÃO mais o cruzamento `base_lucro_normalizada ÷ PL do último ano` (PRIM-02/D-02).
  Espelha `payout_valuation` e usa a MESMA estatística que `report._roe_through_cycle`
  — assim `roe0` e `roe_terminal` do RIM não divergem mais.
- `serie_lucro_normalizada()` devolve a série CRUA de lucro (sem winsorização temporal);
  a winsorização (`norm.serie_winsorizada`) continua VIVA para o screening (PRIM-03/D-04).

Fixtures sintéticas (ticker "X"): número nenhum é cravado contra um ticker real (BLIND-04a).
"""

from statistics import median

from analista.core import normalizacao as norm
from analista.core.fundamentals import CompanyData


def _roe_validos(c: CompanyData):
    return [r for r in (c.roe(a) for a in c.anos_ordenados()) if r is not None]


# --------------------------------------------------------------------------- #
# roe_valuation — mediana da série de roe(a) anuais (PRIM-02, D-02)
# --------------------------------------------------------------------------- #
def test_roe_valuation_e_a_mediana_da_serie_de_roe_anuais():
    # MÉTODO: roe_valuation == median(roe(a) válidos). Série com um ano de pico terminal:
    # o cruzamento ANTIGO (endpoint da base de lucro ÷ PL) devolvia 0,20; a mediana-dos-ROEs
    # (roe(2022)=0,10; roe(2023)=0,10; roe(2024)=0,30) devolve 0,10.
    c = CompanyData(ticker="X", anos=[2021, 2022, 2023, 2024])
    c.lucro_liquido = {2021: 100, 2022: 100, 2023: 100, 2024: 300}
    for a in c.anos:
        c.patrimonio_liquido[a] = 1000
    validos = _roe_validos(c)
    assert validos  # [0.1, 0.1, 0.3]
    assert c.roe_valuation() == median(validos)


def test_roe_valuation_usa_a_mesma_estatistica_que_roe_through_cycle():
    # Consistência (must_have): roe0 (=roe_valuation) e roe_terminal (=_roe_through_cycle)
    # passam a usar a MESMA mediana da série de roe(a). Uma série irregular (não monótona)
    # em que o cruzamento-de-bases ANTIGO discordava da mediana torna a igualdade discriminante.
    from analista.report.report import _roe_through_cycle

    c = CompanyData(ticker="X", anos=list(range(2018, 2025)))
    lucros = {2018: 90, 2019: 100, 2020: 110, 2021: 105, 2022: 120, 2023: 130, 2024: 140}
    for a in c.anos:
        c.lucro_liquido[a] = lucros[a]
        c.patrimonio_liquido[a] = 1000
    assert c.roe_valuation() == _roe_through_cycle(c, {})


def test_roe_valuation_ignora_ano_de_prejuizo_pela_mediana():
    # CSNA3-like: um ano de prejuízo NÃO puxa a mediana para negativa (a mediana o descarta).
    # roe(2022)=0,20; roe(2023)=-0,40; roe(2024)=0,30 -> mediana = 0,20 (positiva).
    # O cruzamento ANTIGO (endpoint da base ÷ PL) daria 0,30 — a igualdade é discriminante.
    c = CompanyData(ticker="X", anos=[2021, 2022, 2023, 2024])
    c.lucro_liquido = {2021: 100, 2022: 200, 2023: -400, 2024: 300}
    for a in c.anos:
        c.patrimonio_liquido[a] = 1000
    rv = c.roe_valuation()
    assert rv is not None
    assert rv > 0                       # a mediana não vira negativa por 1 ano ruim
    assert rv == median(_roe_validos(c))


def test_roe_valuation_none_sem_roe_valido_e_chamavel_sem_args():
    # Fronteira None: nenhuma roe(a) válida (sem PL do ano anterior em lugar nenhum) -> None.
    # E roe_valuation continua chamável SEM args (número-síntese canônico das 3 superfícies).
    c = CompanyData(ticker="X", anos=[2023, 2024])
    c.lucro_liquido = {2023: 100, 2024: 100}
    c.patrimonio_liquido = {2024: 1000}  # falta o PL de 2023 -> roe(2024) e roe(2023) None
    assert c.roe_valuation() is None


# --------------------------------------------------------------------------- #
# serie_lucro_normalizada — série CRUA, sem winsorização temporal (PRIM-03, D-04)
# --------------------------------------------------------------------------- #
def test_serie_lucro_normalizada_e_a_serie_crua_sem_winsor():
    # MÉTODO: serie_lucro_normalizada == serie("lucro_liquido") crua. Um outlier terminal
    # (série longa, ≥5 pontos) NÃO é mais clampado — contraste explícito com serie_winsorizada,
    # que continua clampando o mesmo outlier (viva para o screening, Cap. 8).
    c = CompanyData(ticker="X", anos=list(range(2015, 2025)))
    lucros = [100, 102, 104, 106, 108, 110, 112, 114, 116, 360]
    for a, v in zip(c.anos, lucros):
        c.lucro_liquido[a] = v
    crua = c.serie("lucro_liquido")
    assert c.serie_lucro_normalizada() == crua        # devolve a série crua
    assert c.serie_lucro_normalizada()[-1] == 360      # outlier terminal NÃO clampado
    assert norm.serie_winsorizada(crua)[-1] < 360      # a winsor (screening) AINDA clampa
