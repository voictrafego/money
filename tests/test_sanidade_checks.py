"""Fase 8 / plano 08-04 — os 5 checks aritméticos (SAN-01..SAN-05) provados contra o
snapshot congelado dos 104 (offline, determinístico), nos tickers que o ROADMAP nomeia.

Categoria `contrato`: os asserts são de PERTINÊNCIA, não de valor. `"SAN-01" in {...}` ✅;
`assert fator > 1.5` ❌ (é OFENSOR do BLIND-04a: ticker + número de nível). NENHUM número
não-trivial neste arquivo. Se precisar assertar sobre um fator, asserte sobre o `bucket` (str).

Estes asserts SÃO o teste de regressão da Fase 9: eles precisam DISPARAR e ser vistos
disparando antes de qualquer conserto de dado. Se um check não flagar o ticker que o ROADMAP
nomeia, o errado é o CHECK, não o teste — nunca afrouxar limiar nem marcar xfail para calar.
"""

from __future__ import annotations

import helpers_sanidade as hs
from analista.core import sanidade as s

SNAP = hs.carregar_snapshot_sanidade()


def _checks_san02(ticker):
    return {a.check for a in s.checar_san02(SNAP[ticker])}


def _checks_san03(ticker):
    return {a.check for a in s.checar_san03(SNAP[ticker])}


# --------------------------- SAN-01 (escala de nível) --------------------------- #
def test_san01_flaga_os_tickers_de_escala_quebrada():
    """GOAU4 e CGRA4 têm aviso SAN-01 (o bug de num_acoes visível no nível)."""
    assert s.checar_san01(SNAP["GOAU4"]) is not None
    assert s.checar_san01(SNAP["CGRA4"]) is not None


def test_san01_nao_flaga_os_tickers_sadios():
    """ITUB4 e BRSR6 (escala sadia) NÃO têm aviso — zero falso positivo é metade da guarda."""
    assert s.checar_san01(SNAP["ITUB4"]) is None
    assert s.checar_san01(SNAP["BRSR6"]) is None


def test_san01_e_nao_avaliavel_sem_dado_de_mercado():
    """MRFG3 (404 no Yahoo) devolve None: nem flag, nem exceção — o caso vivo do never_raise."""
    assert s.checar_san01(SNAP["MRFG3"]) is None


# --------------------------- SAN-02 (salto temporal) --------------------------- #
def test_san02_flaga_o_salto_de_escala():
    """ITUB4 e BRSR6 têm aviso SAN-02 (o mesmo bug do SAN-01, visto na série temporal)."""
    assert "SAN-02" in _checks_san02("ITUB4")
    assert "SAN-02" in _checks_san02("BRSR6")


def test_san02_isenta_o_desdobramento_real():
    """Nenhum ano com desdobramento REAL registrado no ITUB4 aparece como salto anômalo —
    a isenção D-12 (e o limiar simétrico de 3×) não confundem split com bug de dado."""
    c = SNAP["ITUB4"]
    anos_flagados = {a.ano for a in s.checar_san02(c)}
    anos_de_split = {int(k.split("-")[0]) for k in c.splits}
    assert not (anos_flagados & anos_de_split)


# --------------------------- SAN-03 (proventos / JCP) --------------------------- #
def test_san03_flaga_o_jcp_perdido():
    """BRSR6 (JCP filado em '6.03.04 Juros sobre o Capital Próprio Pagos', fora do filtro
    estreito 'dividendo') acende SAN-03 — o ticker real do bug."""
    assert "SAN-03" in _checks_san03("BRSR6")


def test_san03_nao_flaga_o_grande_banco_que_escapa_por_acidente():
    """ITUB4 fila numa linha que casa o filtro estreito por acidente → não acende o sinal
    de JCP perdido, e a reconciliação CVM↔Yahoo dele também fica dentro da tolerância."""
    assert "SAN-03" not in _checks_san03("ITUB4")


# --------------------------- SAN-04 (base dos minoritários) --------------------------- #
def test_san04_flaga_a_base_divergente():
    """MRFG3, CSNA3, ALUP11 e EQTL3 têm aviso SAN-04 — inclusive o sinal invertido do CSNA3."""
    for ticker in ("MRFG3", "CSNA3", "ALUP11", "EQTL3"):
        assert s.checar_san04(SNAP[ticker]) is not None, ticker
    assert s.checar_san04(SNAP["CSNA3"]).sinal_invertido is True


def test_san04_nao_flaga_os_bancos_limpos():
    """ITUB4, BBDC4 e BRSR6 (minoritários imateriais no lucro) NÃO têm aviso SAN-04.

    O BBAS3 é deixado FORA desta lista de propósito: medido no snapshot, o LL consolidado do
    Banco do Brasil supera o do controlador em ~22% (minoritário REAL de subsidiárias
    consolidadas). O SAN-04 flaga o BBAS3 — e isso é o check funcionando (ele reporta
    divergência, não elege verdade), não um bug para calar afrouxando o limiar.
    """
    for ticker in ("ITUB4", "BBDC4", "BRSR6"):
        assert s.checar_san04(SNAP[ticker]) is None, ticker


# --------------------------- SAN-05 (clean surplus) --------------------------- #
def test_san05_reporta_o_clean_surplus_como_dado():
    """O check devolve um Aviso OU None (dado, não exceção), mesmo num ticker com PL/lucro
    sujos — nunca levanta."""
    for ticker in ("ITUB4", "BRSR6", "GOAU4", "CSNA3"):
        resultado = s.checar_san05(SNAP[ticker])
        assert resultado is None or isinstance(resultado, s.Aviso), ticker
