"""Garimpo / triagem de empresas — Cap. 8 do livro.

Três conjuntos de filtros:
  A) Customizados (8.2): liquidez, PL positivo, lucro, ROE, dividendos, DY > Selic.
  B) Graham (8.3): 7 critérios (original) + versão flexibilizada para o Brasil.
  C) Big, Safe Dividend de Carlson (8.4): 10 fatores ponderados, padronizados em [0,100].

A regra de ouro do livro: NÃO iniciar a triagem pelo dividend yield — primeiro confirmar
solidez e persistência dos fundamentos; só então olhar o DY.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from . import growth
from .fundamentals import CompanyData


@dataclass
class ResultadoFiltro:
    ticker: str
    passou: bool
    criterios: Dict[str, bool] = field(default_factory=dict)
    detalhes: Dict[str, object] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# A) Filtros customizados (8.2)
# --------------------------------------------------------------------------- #
def filtros_customizados(
    c: CompanyData,
    selic: float,
    n_anos: int = 10,
    volume_min: float = 15_000_000,
    roe_min: float = 0.10,
    dy_corte: Optional[float] = None,
) -> ResultadoFiltro:
    """Filtros customizados do livro (8.2). Se um ano falhar, a empresa é excluída.

    `dy_corte`: se None, usa a Selic como piso (DY > Selic), como no livro.
    """
    anos = c.anos_ordenados()[-n_anos:]
    crit: Dict[str, bool] = {}

    crit["liquidez"] = (c.volume_financeiro_diario or 0) > volume_min

    crit["pl_positivo"] = all(
        c.patrimonio_liquido.get(a, -1) > 0 for a in anos
    ) and len(anos) > 0

    lucros = [c.lucro_liquido.get(a) for a in anos]
    crit["lucro_todos_anos"] = all(l is not None and l > 0 for l in lucros) and len(lucros) > 0

    roes = [c.roe(a) for a in anos]
    crit["roe_min"] = all(r is not None and r > roe_min for r in roes) and len(roes) > 0

    divs = [c.dividendos.get(a) for a in anos]
    crit["dividendos_todos_anos"] = all(d is not None and d > 0 for d in divs) and len(divs) > 0

    corte = selic if dy_corte is None else dy_corte
    dy = c.dy_atual()
    crit["dy_acima_corte"] = dy is not None and dy > corte

    return ResultadoFiltro(
        ticker=c.ticker,
        passou=all(crit.values()),
        criterios=crit,
        detalhes={"dy": dy, "dy_corte": corte, "n_anos": len(anos)},
    )


# --------------------------------------------------------------------------- #
# B) Filtros de Graham (8.3)
# --------------------------------------------------------------------------- #
def _crescimento_trienal(lucros_por_ano: Dict[int, float], anos: Sequence[int]) -> Optional[float]:
    """Crescimento de lucros usando médias trienais no início e no fim (critério 4 de Graham)."""
    if len(anos) < 6:
        return None
    inicio = [lucros_por_ano.get(a) for a in anos[:3]]
    fim = [lucros_por_ano.get(a) for a in anos[-3:]]
    if any(v is None for v in inicio + fim):
        return None
    media_ini = sum(inicio) / 3
    media_fim = sum(fim) / 3
    if media_ini <= 0:
        return None
    return media_fim / media_ini - 1.0


def filtros_graham(
    c: CompanyData,
    faturamento_usd: Optional[float],
    pl_atual: Optional[float],
    pvpa_atual: Optional[float],
    variante: str = "original",
    cfg: Optional[dict] = None,
) -> ResultadoFiltro:
    """Aplica os 7 critérios de Graham. `variante`: 'original' ou 'flexivel_br'.

    Exige dados de faturamento (US$), P/L e P/VPA atuais calculados pela camada superior.
    """
    cfg = cfg or {}
    orig = variante == "original"
    anos = c.anos_ordenados()
    n_lucro = 10 if orig else 5
    n_div = 20 if orig else 5
    pl_max = (15.0 if orig else 20.0)
    pvpa_max = (1.5 if orig else 3.0)
    lc_min = (2.0 if orig else None)

    crit: Dict[str, bool] = {}

    # 1. Tamanho
    fmin = 50_000_000 if c.eh_concessionaria else 100_000_000
    crit["tamanho"] = faturamento_usd is not None and faturamento_usd > fmin

    # 2. Condição financeira: liquidez corrente e ELP <= capital de giro
    ultimo = c.ultimo_ano()
    ac = c.ativo_circulante.get(ultimo) if ultimo else None
    pc = c.passivo_circulante.get(ultimo) if ultimo else None
    if lc_min is not None and ac is not None and pc not in (None, 0):
        crit["liquidez_corrente"] = (ac / pc) >= lc_min
    else:
        crit["liquidez_corrente"] = True  # relaxado na versão flexível
    elp = c.divida_lp.get(ultimo) if ultimo else None
    if ac is not None and pc is not None and elp is not None:
        crit["endividamento"] = elp <= (ac - pc)
    else:
        crit["endividamento"] = True

    # 3. Lucro positivo por n anos
    ult_lucro = anos[-n_lucro:]
    crit["lucros"] = len(ult_lucro) >= min(n_lucro, len(anos)) and all(
        c.lucro_liquido.get(a, -1) > 0 for a in ult_lucro
    )

    # 4. Crescimento de lucros >= 1/3 (só na versão original; trienal)
    if orig:
        g = _crescimento_trienal(c.lucro_liquido, anos[-10:])
        crit["crescimento_lucro"] = g is not None and g >= 1 / 3
    else:
        crit["crescimento_lucro"] = True

    # 5. Dividendos ininterruptos por n anos
    ult_div = anos[-n_div:]
    crit["dividendos"] = len(ult_div) >= min(n_div, len(anos)) and all(
        c.dividendos.get(a, 0) > 0 for a in ult_div
    )

    # 6/7. P/L, P/VPA e produto <= 22,5 (regra do produto só na original)
    crit["pl"] = pl_atual is not None and pl_atual <= pl_max
    crit["pvpa"] = pvpa_atual is not None and pvpa_atual <= pvpa_max
    if orig and pl_atual is not None and pvpa_atual is not None:
        crit["produto_pl_pvpa"] = (pl_atual * pvpa_atual) <= 22.5
    else:
        crit["produto_pl_pvpa"] = True

    return ResultadoFiltro(
        ticker=c.ticker,
        passou=all(crit.values()),
        criterios=crit,
        detalhes={"variante": variante, "pl": pl_atual, "pvpa": pvpa_atual,
                  "faturamento_usd": faturamento_usd},
    )


# --------------------------------------------------------------------------- #
# C) Big, Safe Dividend (BSD) de Carlson (8.4)
# --------------------------------------------------------------------------- #
PESOS_BSD_PADRAO = {
    "payout": 30,
    "cobertura_juros": 10,
    "fc_sobre_lucro": 5,
    "dividend_yield": 5,
    "desempenho_relativo_preco": 10,
    "variacao_tangivel_vp": 10,
    "crescimento_lucro_lp": 10,
    "crescimento_fc_3a": 5,
    "crescimento_dividendos_3a": 10,
    "crescimento_lucro_3a": 5,
}


def indicadores_bsd(c: CompanyData, anos_media: int = 3) -> Dict[str, Optional[float]]:
    """Calcula os 10 indicadores brutos do BSD para uma empresa (médias de `anos_media`).

    Nota: cobertura de juros e variação tangível no valor contábil seguem a definição-padrão
    de Carlson (a fórmula exata estava em figura do livro). Validar contra a Tab. 15.
    """
    anos = c.anos_ordenados()[-anos_media:]
    ult = c.ultimo_ano()

    def media(vals):
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    # 1. payout médio
    payout = media([c.payout(a) for a in anos])

    # 2. cobertura de juros: (Lucro + Despesa de juros) / Despesa de juros (proxy de LAJIR/juros)
    cob = []
    for a in anos:
        ll, dj = c.lucro_liquido.get(a), c.despesa_juros.get(a)
        if ll is not None and dj not in (None, 0):
            cob.append((ll + dj) / dj)
    cobertura = media(cob) if cob else None

    # 3. FCO / lucro líquido
    fc_ll = []
    for a in anos:
        f, ll = c.fco.get(a), c.lucro_liquido.get(a)
        if f is not None and ll not in (None, 0):
            fc_ll.append(f / ll)
    fc_sobre_lucro = media(fc_ll) if fc_ll else None

    # 4. dividend yield atual
    dy = c.dy_atual()

    # 5. desempenho relativo do preço (6m vs Ibov)
    desempenho = c.desempenho_relativo_6m

    # 6. variação tangível no valor contábil: CAGR de (PL - intangível)
    def tangivel(a):
        pl, intang = c.patrimonio_liquido.get(a), c.ativo_intangivel.get(a, 0)
        return None if pl is None else pl - (intang or 0)
    if len(anos) >= 2:
        var_tangivel = growth.cagr(tangivel(anos[0]), tangivel(anos[-1]), len(anos) - 1)
    else:
        var_tangivel = None

    # 7. crescimento esperado do lucro no longo prazo (analistas; proxy = g por fundamentos)
    cresc_lucro_lp = c.g_lucro_esperado
    if cresc_lucro_lp is None and ult is not None:
        cresc_lucro_lp = growth.crescimento_por_fundamentos(c.roe(ult), c.payout(ult))

    # 8/9/10. crescimento de FCO, dividendos e lucro em 3 anos (CAGR)
    def cagr_serie(d: Dict[int, float]):
        if len(anos) < 2:
            return None
        return growth.cagr(d.get(anos[0]), d.get(anos[-1]), len(anos) - 1)

    return {
        "payout": payout,
        "cobertura_juros": cobertura,
        "fc_sobre_lucro": fc_sobre_lucro,
        "dividend_yield": dy,
        "desempenho_relativo_preco": desempenho,
        "variacao_tangivel_vp": var_tangivel,
        "crescimento_lucro_lp": cresc_lucro_lp,
        "crescimento_fc_3a": cagr_serie(c.fco),
        "crescimento_dividendos_3a": cagr_serie(c.dividendos),
        "crescimento_lucro_3a": cagr_serie(c.lucro_liquido),
    }


def _winsorize(valores: List[float], p: float) -> List[float]:
    """Winsoriza ao nível p (ex.: 0,10 limita aos percentis 10 e 90)."""
    finitos = sorted(v for v in valores if v is not None)
    if not finitos:
        return valores
    n = len(finitos)
    lo_idx = max(0, math.floor(p * (n - 1)))
    hi_idx = min(n - 1, math.ceil((1 - p) * (n - 1)))
    lo, hi = finitos[lo_idx], finitos[hi_idx]
    return [None if v is None else min(max(v, lo), hi) for v in valores]


def _padronizar_0_100(valores: List[Optional[float]]) -> List[Optional[float]]:
    """Min-max para [0,100] (maior = melhor). Ausentes recebem 0."""
    finitos = [v for v in valores if v is not None]
    if not finitos:
        return [0.0 for _ in valores]
    vmin, vmax = min(finitos), max(finitos)
    if vmax == vmin:
        return [50.0 if v is not None else 0.0 for v in valores]
    return [
        0.0 if v is None else (v - vmin) / (vmax - vmin) * 100.0
        for v in valores
    ]


def bsd_ranking(
    empresas: List[CompanyData],
    pesos: Optional[Dict[str, int]] = None,
    anos_media: int = 3,
    winsor: float = 0.10,
) -> List[Dict[str, object]]:
    """Calcula o BSD de Carlson para um conjunto de empresas (8.4).

    Passos: (1) indicadores brutos; (2) winsorização a `winsor`; (3) padronização [0,100]
    de cada indicador (maior=melhor); (4) média ponderada pelos pesos; (5) re-padronização
    da média ponderada em [0,100], formando o ranking. Foco em BSD > 80.
    """
    pesos = pesos or PESOS_BSD_PADRAO
    nomes = list(pesos.keys())

    brutos = [indicadores_bsd(c, anos_media) for c in empresas]

    # winsoriza e padroniza coluna a coluna
    notas: Dict[str, List[Optional[float]]] = {}
    for nome in nomes:
        coluna = [b.get(nome) for b in brutos]
        coluna_w = _winsorize(coluna, winsor)
        notas[nome] = _padronizar_0_100(coluna_w)

    soma_pesos = sum(pesos.values())
    medias_ponderadas = []
    for i in range(len(empresas)):
        mp = sum(notas[nome][i] * pesos[nome] for nome in nomes) / soma_pesos
        medias_ponderadas.append(mp)

    bsd_final = _padronizar_0_100(medias_ponderadas)

    resultado = []
    for i, c in enumerate(empresas):
        resultado.append({
            "ticker": c.ticker,
            "nome": c.nome,
            "setor": c.setor,
            "bsd": bsd_final[i],
            "acima_de_80": (bsd_final[i] or 0) > 80,
            "indicadores": brutos[i],
        })
    resultado.sort(key=lambda r: r["bsd"] or 0, reverse=True)
    return resultado
