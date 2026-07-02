"""Montagem de CompanyData a partir das fontes gratuitas (CVM + yfinance + BCB).

Combina:
  - fundamentos anuais (CVM): LL, PL, FCO, receita, ativos/passivos, dívida, intangível;
  - mercado (yfinance): preço, dividendos/ação por ano, nº de ações, beta, liquidez;
  - nº de ações por ano: deduzido de LL/LPA (CVM) quando o LPA está disponível.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..core.fundamentals import CompanyData
from . import cvm, prices, universe


def _eh_unit(ticker: str) -> bool:
    """Tickers de UNIT na B3 terminam em '11' (ex.: TAEE11, KLBN11, SAPR11). Ações ON/PN
    terminam em 3/4/5/6. O preço e os proventos do Yahoo são POR UNIT, mas o "Lucro por
    Ação" da CVM é POR AÇÃO (total ON+PN) — daí a necessidade do fator de conversão."""
    return ticker.upper().replace(".SA", "").endswith("11")


def _fator_unit(contagem_cvm: Dict[int, float], acoes_yahoo: Optional[float]) -> int:
    """Nº de ações que compõem 1 unit (3 = TAEE, ~5 = KLBN). A contagem da CVM (LL/LPA) é a
    base POR AÇÃO; o `sharesOutstanding` do Yahoo, para units, é a contagem de UNITS negociadas.
    A razão (ações/unit) é um inteiro pequeno — usamos a mediana das razões anuais, arredondada.
    Só aceita ≥ 2 (senão não há unit de fato); 1 = sem conversão (deixa os números intactos).
    A trava ≥ 2 protege não-units que caiam aqui por engano (razão ≈ 1 → fator 1)."""
    if not acoes_yahoo:
        return 1
    razoes = sorted(c / acoes_yahoo for c in contagem_cvm.values() if c)
    if not razoes:
        return 1
    mediana = razoes[len(razoes) // 2]
    cand = round(mediana)
    return cand if cand >= 2 else 1


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
    c.serie_precos_ajustada = dm.serie_precos_ajustada  # Adj Close 5a p/ RET-01 (None quando Yahoo falha)
    c.ohlc = dm.ohlc                      # frame OHLCV nominal cru (D-02; None quando Yahoo falha)
    c.ohlc_ajustado = dm.ohlc_ajustado    # OHLCV split-only-adjusted p/ indicadores (Phase 5)
    c.eh_concessionaria = any(t.lower() in (c.setor or "").lower() for t in setores_concessionaria)

    acoes_atual = dm.num_acoes  # Yahoo sharesOutstanding: já é a contagem de UNITS p/ tickers unit

    # Passo 1: fundamentos por ano + contagem de ações CRUA da CVM (base POR AÇÃO = LL/LPA).
    contagem_cvm: Dict[int, float] = {}
    dist_cvm: Dict[int, float] = {}  # proventos pagos (div + JCP) por ano, da CVM
    for ano in anos:
        f = cvm.fundamentos_do_ano(cd_cvm, ano)
        if f["lucro_liquido"] is not None:
            c.lucro_liquido[ano] = f["lucro_liquido"]
        for campo in ("patrimonio_liquido", "fco", "vendas_liquidas",
                      "ativo_circulante", "passivo_circulante", "divida_lp",
                      "ativo_intangivel"):
            if f[campo] is not None:
                getattr(c, campo)[ano] = f[campo]

        lpa_cvm = f.get("lpa")
        if lpa_cvm and f["lucro_liquido"]:
            contagem_cvm[ano] = abs(f["lucro_liquido"] / lpa_cvm)
        if f.get("dividendos_distribuidos") is not None:
            dist_cvm[ano] = f["dividendos_distribuidos"]

    # BUG-UNIT: a contagem da CVM é POR AÇÃO (ON+PN), mas preço e proventos (Yahoo) são POR UNIT.
    # Sem converter, LPA/P/L/EY ficam inflados pelo fator da unit (3× TAEE, ~5× KLBN), o payout
    # estoura (>100% falso) e o DDM subavalia a unit → veredito "sobreavaliada" espúrio. Dividir a
    # contagem pelo fator coloca num_acoes na base de UNITS, alinhando TODOS os derivados ao preço.
    fator = _fator_unit(contagem_cvm, acoes_atual) if _eh_unit(ticker) else 1

    # Passo 2: num_acoes na base de UNITS e dividendos totais (consistentes com o preço).
    for ano in anos:
        if ano in contagem_cvm:
            c.num_acoes[ano] = contagem_cvm[ano] / fator
        elif acoes_atual:
            c.num_acoes[ano] = acoes_atual  # Yahoo já está na base de unit — não dividir

        # dividendos totais do ano (R$). BUG-JCP: o histórico do Yahoo perde o JCP (metade da
        # distribuição dos bancos nos anos antigos), subestimando o payout-mediana e o DDM. A
        # DFC da CVM traz div + JCP completos e auditáveis → fonte preferida; Yahoo é fallback
        # (DPA por unit × nº de units) só quando a CVM não tem a linha de provento no ano.
        if ano in dist_cvm:
            c.dividendos[ano] = dist_cvm[ano]
        else:
            dpa = dm.dividendos_por_ano.get(ano)
            if dpa is not None and ano in c.num_acoes:
                c.dividendos[ano] = dpa * c.num_acoes[ano]

    # mantém apenas anos com lucro líquido coletado (núcleo da análise)
    c.anos = sorted(a for a in anos if a in c.lucro_liquido)
    return c
