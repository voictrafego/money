"""Testes da consistência de agregação na engine (Fase 01).

Cobrem as funções canônicas que os 3 modos (Analisar/Garimpo/Ranking) compartilham:
- payout_valuation (CR-02/WR-03): janela 3a + clamp 1.0, definição única
- roe (WR-01): base de PL consistente em toda a série (PL médio; None sem PL inicial)
- dy_atual (WR-04): trailing-12m quando disponível, com ano-base exposto
"""

from analista.core.fundamentals import CompanyData


# --------------------------------------------------------------------------- #
# Task 1: payout_valuation — média 3a com clamp 1.0
# --------------------------------------------------------------------------- #
def test_payout_valuation_clamp_em_1():
    # payout médio 3a > 1.0 deve ser cravado em 1.0
    c = CompanyData(ticker="X", anos=[2022, 2023, 2024])
    c.lucro_liquido = {2022: 100, 2023: 100, 2024: 100}
    c.dividendos = {2022: 150, 2023: 150, 2024: 150}  # payout 1.5 cada
    c.num_acoes = {2022: 1, 2023: 1, 2024: 1}
    assert c.payout_valuation() == 1.0


def test_payout_valuation_media_dos_3_ultimos_anos():
    c = CompanyData(ticker="X", anos=[2021, 2022, 2023, 2024])
    c.lucro_liquido = {2021: 100, 2022: 100, 2023: 100, 2024: 100}
    # payouts: 2021=0.2 (ignorado, fora da janela 3a), 2022=.6, 2023=.7, 2024=.8
    c.dividendos = {2021: 20, 2022: 60, 2023: 70, 2024: 80}
    c.num_acoes = {2021: 1, 2022: 1, 2023: 1, 2024: 1}
    v = c.payout_valuation()
    assert abs(v - (0.6 + 0.7 + 0.8) / 3) < 1e-9


def test_payout_valuation_ignora_none():
    c = CompanyData(ticker="X", anos=[2022, 2023, 2024])
    c.lucro_liquido = {2022: 100, 2024: 100}  # 2023 sem lucro -> payout(2023)=None
    c.dividendos = {2022: 50, 2024: 70}
    c.num_acoes = {2022: 1, 2024: 1}
    v = c.payout_valuation()
    assert abs(v - (0.5 + 0.7) / 2) < 1e-9


def test_payout_valuation_none_sem_dados():
    c = CompanyData(ticker="X", anos=[2024])
    assert c.payout_valuation() is None


# --------------------------------------------------------------------------- #
# Task 2: roe — base de PL consistente (PL médio; None sem PL inicial)
# --------------------------------------------------------------------------- #
def test_roe_none_no_primeiro_ano_sem_pl_inicial():
    c = CompanyData(ticker="X", anos=[2023, 2024])
    c.lucro_liquido = {2023: 100, 2024: 120}
    c.patrimonio_liquido = {2023: 1000, 2024: 1200}
    assert c.roe(2023) is None  # 1º ano sem PL de 2022 -> None, nunca PL final


def test_roe_usa_pl_medio_quando_ha_inicial_e_final():
    c = CompanyData(ticker="X", anos=[2023, 2024])
    c.lucro_liquido = {2023: 100, 2024: 120}
    c.patrimonio_liquido = {2023: 1000, 2024: 1200}
    r = c.roe(2024)
    assert r is not None and abs(r - 120 / 1100) < 1e-9  # PL médio (1000+1200)/2


# --------------------------------------------------------------------------- #
# Task 3: dy_atual — trailing-12m quando disponível, com fallback
# --------------------------------------------------------------------------- #
def test_dy_atual_usa_trailing_12m_quando_disponivel():
    c = CompanyData(ticker="X", anos=[2024])
    c.preco_atual = 10.0
    c.dpa_trailing_12m = 0.8
    assert abs(c.dy_atual() - 0.08) < 1e-9


def test_dy_atual_fallback_para_ano_base():
    c = CompanyData(ticker="Y", anos=[2024])
    c.preco_atual = 10.0
    c.dividendos = {2024: 100}
    c.num_acoes = {2024: 100}
    assert c.dy_atual() is not None  # dpa(2024)/preco via fallback


def test_company_data_expoe_ano_dpa():
    c = CompanyData(ticker="X", anos=[2024])
    assert hasattr(c, "ano_dpa")
