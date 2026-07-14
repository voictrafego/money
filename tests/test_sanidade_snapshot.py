"""Fase 8 / plano 08-03 — prova de que o snapshot congelado dos 104 (D-08) e' a evidencia
intocada do dado SUJO: cobertura do universo, market_cap+splits congelados, MRFG3 sem mercado
com a CVM intacta, zero R$ derivado por ticker, e reconstrucao de CompanyData 100% OFFLINE.

Categoria `contrato`: presenca/ausencia/conjunto — nenhum assert numerico. (BLIND-04a: um assert
sobre um numero de NIVEL num teste que cite um ticker OFENDE e quebra a suite inteira.)
"""

from __future__ import annotations

import helpers_sanidade as hs
from helpers_blindagem import tickers_conhecidos

# chaves proibidas: se qualquer uma aparecer numa entrada do snapshot, alguem colou um R$
# derivado por ticker (D-05/D-07) e o baseline virou golden de nivel.
_CHAVES_PROIBIDAS = ("intrinseco", "motor", "arquetipo", "valor_justo")


def test_snapshot_cobre_o_universo_conhecido():
    """Todo ticker conhecido — menos os que degradaram por completo (bloco `falhas:`) — esta
    congelado. Comparacao de CONJUNTOS: sem literal de ticker, sem contagem."""
    presentes = hs.tickers_do_snapshot()
    falhas = set(hs.falhas_do_snapshot())
    esperados = set(tickers_conhecidos()) - falhas
    faltando = esperados - presentes
    assert not faltando, f"tickers conhecidos ausentes do snapshot (e nao em falhas): {faltando}"


def test_snapshot_congela_market_cap_e_splits():
    """Para toda entrada de ticker as chaves `market_cap` e `splits` EXISTEM (podem ser
    None/{}, mas a chave existe) — o baseline nao busca mercado ao vivo, logo nao pisca."""
    bruto = hs.carregar_snapshot_bruto()
    for tk in hs.tickers_do_snapshot():
        entrada = bruto[tk]
        assert "market_cap" in entrada, f"{tk} sem a chave market_cap congelada"
        assert "splits" in entrada, f"{tk} sem a chave splits congelada"


def test_snapshot_nao_estampa_reais_por_ticker():
    """Nenhuma entrada carrega chave de R$ DERIVADO (intrinseco/motor/arquetipo/valor_justo).
    O teste que protege o D-05/D-07: fica vermelho no dia em que alguem colar um veredito."""
    bruto = hs.carregar_snapshot_bruto()
    for tk in hs.tickers_do_snapshot():
        entrada = bruto[tk]
        for chave in entrada:
            baixa = str(chave).lower()
            for proibida in _CHAVES_PROIBIDAS:
                assert proibida not in baixa, f"{tk} estampa chave proibida {chave!r}"


def test_ticker_sem_dado_de_mercado_e_congelado_com_a_cvm_intacta():
    """O caso vivo do SAN-06: o MRFG3 (404 no Yahoo, virou MBRF) esta NO snapshot, com a CVM
    completa e SEM dado de mercado. Asserts de presenca/ausencia — zero constante numerica."""
    bruto = hs.carregar_snapshot_bruto()
    assert "MRFG3" in bruto, "MRFG3 deveria estar congelado (a CVM dele funciona)"
    entrada = bruto["MRFG3"]
    assert entrada.get("lucro_liquido"), "MRFG3 sem serie de lucro da CVM (deveria estar intacta)"
    assert entrada.get("market_cap") is None, "MRFG3 nao deveria ter market_cap (Yahoo 404)"
    assert "MRFG3" in hs.falhas_do_snapshot(), "MRFG3 deveria estar registrado em falhas:"


def test_snapshot_reconstroi_companydata_offline():
    """`carregar_snapshot_sanidade()` devolve CompanyData sem tocar a rede, e cada um nasce
    `confianca == 'nao_avaliada'` (D-03) — um objeto reconstruido nao parece limpo."""
    empresas = hs.carregar_snapshot_sanidade()
    assert empresas, "snapshot reconstruiu zero empresas"
    for tk, c in empresas.items():
        assert c.ticker == tk
        assert c.confianca == "nao_avaliada", f"{tk} nasceu com confianca != nao_avaliada"
        assert c.avisos == []
