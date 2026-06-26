"""Montagem de CompanyData a partir das fontes gratuitas (CVM + yfinance + BCB).

Combina:
  - fundamentos anuais (CVM): LL, PL, FCO, receita, ativos/passivos, dívida, intangível;
  - mercado (yfinance): preço, dividendos/ação por ano, nº de ações, beta, liquidez;
  - nº de ações por ano: deduzido de LL/LPA (CVM) quando o LPA está disponível.
"""

from __future__ import annotations

from typing import List, Optional

from ..core.fundamentals import CompanyData
from . import cvm, prices, universe


def montar_empresa(
    ticker: str,
    ano_base: int,
    n_anos: int = 10,
    setores_concessionaria=("Energia", "Saneamento", "Água", "Gás"),
) -> Optional[CompanyData]:
    dm = prices.coletar_mercado(ticker)
    cd_cvm, setor = universe.resolver(ticker, dm.nome)
    if cd_cvm is None:
        return None

    anos = list(range(ano_base - n_anos + 1, ano_base + 1))
    c = CompanyData(
        ticker=ticker.upper().replace(".SA", ""),
        nome=dm.nome or ticker,
        setor=setor or dm.setor,
        anos=anos,
    )
    c.preco_atual = dm.preco_atual
    c.volume_financeiro_diario = dm.volume_financeiro_diario
    c.beta = dm.beta
    c.desempenho_relativo_6m = dm.desempenho_relativo_6m
    c.dpa_trailing_12m = dm.dpa_trailing_12m  # DY corrente trailing-12m (WR-04)
    c.ano_dpa = dm.ano_dpa
    c.serie_precos = dm.serie_precos
    c.ohlc = dm.ohlc                      # frame OHLCV nominal cru (D-02; None quando Yahoo falha)
    c.ohlc_ajustado = dm.ohlc_ajustado    # OHLCV split-only-adjusted p/ indicadores (Phase 5)
    c.eh_concessionaria = any(t.lower() in (c.setor or "").lower() for t in setores_concessionaria)

    acoes_atual = dm.num_acoes

    for ano in anos:
        f = cvm.fundamentos_do_ano(cd_cvm, ano)
        if f["lucro_liquido"] is not None:
            c.lucro_liquido[ano] = f["lucro_liquido"]
        for campo in ("patrimonio_liquido", "fco", "vendas_liquidas",
                      "ativo_circulante", "passivo_circulante", "divida_lp",
                      "ativo_intangivel"):
            if f[campo] is not None:
                getattr(c, campo)[ano] = f[campo]

        # nº de ações do ano: LL / LPA (CVM) quando possível; senão usa o atual (Yahoo)
        lpa_cvm = f.get("lpa")
        if lpa_cvm and f["lucro_liquido"]:
            c.num_acoes[ano] = abs(f["lucro_liquido"] / lpa_cvm)
        elif acoes_atual:
            c.num_acoes[ano] = acoes_atual

        # dividendos totais do ano = DPA (Yahoo) * nº de ações do ano
        dpa = dm.dividendos_por_ano.get(ano)
        if dpa is not None and ano in c.num_acoes:
            c.dividendos[ano] = dpa * c.num_acoes[ano]

    # mantém apenas anos com lucro líquido coletado (núcleo da análise)
    c.anos = sorted(a for a in anos if a in c.lucro_liquido)
    return c
