"""PRIM-04 — deflatores anuais do IPCA (BCB SGS), testados OFFLINE.

`macro.ipca_deflatores_anuais` traz cada ano da série de lucro a **reais do último ano**
(D-03: reais do último ano, NÃO ano-base fixo). A rede vive só no fetch (`_ipca_anual_dezembro`,
espelho do `_selic_historico`: date-range + 3 retries + degradação graciosa para vazio); a
COMPOSIÇÃO dos fatores é uma função pura (`_compor_deflatores`) testável sem tocar a rede.

A asserção de composição é INDEPENDENTE de qual série legítima do SGS alimenta (13522-dez
travado, ou 433 mensal composto) — a escolha só afeta a precisão numérica, não a corretude do
método. Por isso estes testes montam o IPCA anual à mão / monkeypatcham o fetch: zero rede.
"""

import pytest

from analista.ingest import macro


# --------------------------------------------------------------------------- #
# _compor_deflatores — a matemática pura (independe da rede e da série do SGS)
# --------------------------------------------------------------------------- #
def test_deflator_do_ultimo_ano_e_1_e_anos_anteriores_compoem_a_inflacao():
    # IPCA anual sintético em FRAÇÃO (convenção /100.0, como ipca_12m). Último ano T = 2023.
    ipca = {2021: 0.10, 2022: 0.05, 2023: 0.04}
    defl = macro._compor_deflatores(ipca)
    # D-03: o fator do ÚLTIMO ano é 1.0 (a base já está em reais dele).
    assert defl[2023] == 1.0
    # anos anteriores acumulam a inflação DEPOIS deles até T (prod(1+ipca[y]), y in ano+1..T).
    assert defl[2022] == pytest.approx(1.04)          # só 2023
    assert defl[2021] == pytest.approx(1.05 * 1.04)   # 2022 e 2023
    # IPCA positivo → quanto mais antigo o ano, MAIOR o fator para o último ano.
    assert defl[2021] > defl[2022] > defl[2023]
    assert defl[2021] > 1.0 and defl[2022] > 1.0


def test_serie_de_ipca_vazia_degrada_para_dict_vazio_never_raise():
    # Fronteira: sem série (falha de rede resolvida a {}) → {} sem levantar (espelha _selic → []).
    assert macro._compor_deflatores({}) == {}


# --------------------------------------------------------------------------- #
# ipca_deflatores_anuais — fim-a-fim OFFLINE (fetch monkeypatchado: zero rede)
# --------------------------------------------------------------------------- #
def test_deflatores_anuais_compoe_a_serie_carimbada_sem_tocar_a_rede(monkeypatch):
    # O fetch é substituído por um IPCA anual à mão: prova que a composição é a da fronteira
    # e que a função NÃO chama requests (se chamasse, o monkeypatch não seria exercido).
    monkeypatch.setattr(macro, "_ipca_anual_dezembro", lambda anos=10: {2022: 0.06, 2023: 0.045})
    defl = macro.ipca_deflatores_anuais(10)
    assert defl[2023] == 1.0
    assert defl[2022] == pytest.approx(1.045)


def test_deflatores_anuais_falha_de_rede_degrada_gracioso(monkeypatch):
    # Fetch devolve vazio (rede falhou 3x) → {} (a engine cai na série nominal, never-raise).
    monkeypatch.setattr(macro, "_ipca_anual_dezembro", lambda anos=10: {})
    assert macro.ipca_deflatores_anuais(10) == {}
