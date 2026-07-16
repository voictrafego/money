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

from . import growth, normalizacao
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

    # ROE usa PL médio e é None no 1º ano sem PL inicial (WR-01). Avalia só os anos com
    # ROE definido (precisam de PL do ano anterior) e exige pelo menos um ano avaliável.
    roes = [r for r in (c.roe(a) for a in anos) if r is not None]
    crit["roe_min"] = len(roes) > 0 and all(r > roe_min for r in roes)

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

# CALIBRÁVEL — ajustar as bandas aqui muda o corte 80; não tocar na lógica de padronização.
# Cada par (lo, hi) é a referência FIXA de um fator: lo → nota 0, hi → nota 100 (maior=melhor
# nos 10). É o ÚNICO ponto de ajuste do corte absoluto; torna o BSD reproduzível entre lotes.
REFERENCIA_BSD: Dict[str, tuple] = {
    "payout": (0.0, 0.80),            # fração do lucro distribuída; payout sustentável até ~80% pontua máximo, acima disso não pontua mais (clamp). Carlson penaliza payout esticado/insustentável.
    "cobertura_juros": (1.0, 8.0),    # (LL+juros)/juros, "vezes"; 1x mal cobre a dívida (0), >=8x folga confortável (100).
    "fc_sobre_lucro": (0.5, 1.2),     # FCO/LL; caixa < metade do lucro = baixa qualidade (0), caixa >= 1.2x lucro = lucro "de verdade" (100).
    "dividend_yield": (0.0, 0.10),    # DY corrente em fração; 0% = 0, 10% a.a. = 100. Não estende acima de 10% para não premiar armadilha de dividendos (Cap. 6).
    "desempenho_relativo_preco": (-0.20, 0.20),  # excesso 6m vs Ibov; -20% = 0, +20% = 100; em torno de 0 dá nota ~50 (neutro).
    "variacao_tangivel_vp": (0.0, 0.15),         # CAGR do PL tangível; 0% não cria valor contábil (0), 15% a.a. forte criação de valor (100).
    "crescimento_lucro_lp": (0.0, 0.15),         # g esperado / proxy ROE×(1−payout); reinvestir a 0% = 0, 15% a.a. = 100.
    "crescimento_fc_3a": (-0.05, 0.15),          # CAGR do FCO 3a; queda de caixa (-5%) = 0, +15% a.a. = 100; lo levemente negativo tolera ruído.
    "crescimento_dividendos_3a": (0.0, 0.12),    # CAGR dos proventos 3a; dividendo estagnado (0%) = 0, +12% a.a. = 100 (dividendo CRESCENTE é núcleo do método).
    "crescimento_lucro_3a": (-0.05, 0.15),       # CAGR do lucro 3a; -5% = 0, +15% a.a. = 100; lo levemente negativo tolera anos atípicos.
}


def indicadores_bsd(c: CompanyData, anos_media: int = 3) -> Dict[str, Optional[float]]:
    """Calcula os 10 indicadores brutos do BSD para uma empresa (médias de `anos_media`).

    Nota: cobertura de juros e variação tangível no valor contábil seguem a definição-padrão
    de Carlson (a fórmula exata estava em figura do livro). Validar contra a Tab. 15.
    """
    anos = c.anos_ordenados()[-anos_media:]

    def media(vals):
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    # 1. payout sustentável (AUD-SCR-01): mediana do histórico completo (payout_valuation),
    #    o MESMO número do Analisar/Ranking — não a média aritmética do payout CRU 3a, que um
    #    ano de lucro deprimido inflava no fator de maior peso do BSD (30/100).
    payout = c.payout_valuation()

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

    # 4. dividend yield recorrente (AUD-SCR-03): leitura sustentável (mesmo do Analisar), não
    #    o trailing-12m que inclui extraordinários e cravava nota máxima por provento de evento.
    dy = c.dy_recorrente()

    # 5. desempenho relativo do preço (6m vs Ibov)
    desempenho = c.desempenho_relativo_6m

    # 6. variação tangível no valor contábil (AUD-SCR-02): tendência LOG-LINEAR sobre a série
    #    COMPLETA winsorizada de (PL − intangível) — mesmo estimador robusto dos demais
    #    crescimentos do BSD. Antes era CAGR endpoint-a-endpoint (só base e ponta da janela 3a),
    #    distorcido por um PL atípico numa das pontas.
    def tangivel(a):
        pl, intang = c.patrimonio_liquido.get(a), c.ativo_intangivel.get(a, 0)
        return None if pl is None else pl - (intang or 0)
    serie_tang = [t for t in (tangivel(a) for a in c.anos_ordenados()) if t is not None]
    var_tangivel = growth.crescimento_log_linear(normalizacao.serie_winsorizada(serie_tang))

    # 7. crescimento esperado do lucro no longo prazo (analistas; proxy = g por fundamentos).
    #    Sem estimativa de analistas, usa a MÉDIA de roe/payout na MESMA janela `anos_media`
    #    (não ano único — WR-02), ignorando None (incl. roe do 1º ano sem PL inicial — WR-01).
    cresc_lucro_lp = c.g_lucro_esperado
    if cresc_lucro_lp is None:
        roe_medio = media([c.roe(a) for a in anos])
        payout_medio = media([c.payout(a) for a in anos])
        cresc_lucro_lp = growth.crescimento_por_fundamentos(roe_medio, payout_medio)

    # 8/9. crescimento de FCO e dividendos: tendência log-linear (OLS de ln) sobre a série
    #    COMPLETA winsorizada de cada atributo (D-05, elegibilidade BSD do Cap. 8). Um ano
    #    extraordinário de provento/caixa deixa de envenenar o BSD; a winsorização morde só com
    #    ≥5 pontos (a janela 3a tornaria D-05 inócuo), por isso usa-se a série inteira. Estes são
    #    conceitos de screening (fora do escopo PRIM) — seguem winsorizados.
    def crescimento_serie(attr: str):
        return growth.crescimento_log_linear(normalizacao.serie_winsorizada(c.serie(attr)))

    # 10. crescimento do LUCRO: consome a MESMA série de valuation que report.g_historico
    #    (`serie_lucro_normalizada`, PRIM-03/D-04 = série CRUA na Fase 10) — assim
    #    crescimento_lucro_3a coincide POR CONSTRUÇÃO com o g_historico do Analisar (Core Value:
    #    a ação não ranqueia num g diferente do que o Analisar exibe). A winsorização temporal do
    #    lucro saiu na Fase 10 (o g robusto é desenhado na Fase 11); FCO/dividendos acima seguem
    #    winsorizados por serem elegibilidade de screening. Chave mantém o sufixo _3a (REFERENCIA_BSD).
    def crescimento_lucro():
        return growth.crescimento_log_linear(c.serie_lucro_normalizada())

    return {
        "payout": payout,
        "cobertura_juros": cobertura,
        "fc_sobre_lucro": fc_sobre_lucro,
        "dividend_yield": dy,
        "desempenho_relativo_preco": desempenho,
        "variacao_tangivel_vp": var_tangivel,
        "crescimento_lucro_lp": cresc_lucro_lp,
        "crescimento_fc_3a": crescimento_serie("fco"),
        "crescimento_dividendos_3a": crescimento_serie("dividendos"),
        "crescimento_lucro_3a": crescimento_lucro(),
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


def _padronizar_absoluto(
    valores: List[Optional[float]], lo: float, hi: float, maior_melhor: bool = True
) -> List[Optional[float]]:
    """Padroniza cada valor para [0,100] por clamp linear contra a banda fixa (lo,hi).

    Independente do lote (reproduzível): nota = clamp((v-lo)/(hi-lo), 0, 1) * 100.
    Valor ausente (None) recebe nota NEUTRA (50), distinguindo "ausente" de "pior valor" (0).
    """
    span = hi - lo
    notas: List[Optional[float]] = []
    for v in valores:
        if v is None:
            notas.append(50.0)  # neutro: ausente não é penalizado como pior valor (WR-05)
            continue
        frac = (v - lo) / span if span else 0.0
        if not maior_melhor:
            frac = 1.0 - frac
        notas.append(min(max(frac, 0.0), 1.0) * 100.0)
    return notas


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

    Passos: (1) indicadores brutos; (2) padronização ABSOLUTA [0,100] de cada indicador
    contra a banda fixa de `REFERENCIA_BSD` (maior=melhor), reproduzível entre lotes;
    (3) média ponderada pelos pesos — esse é o BSD final (NÃO há re-padronização min-max do
    lote). Corte de Carlson: BSD > 80 (absoluto). Foco em BSD > 80.

    A winsorização foi substituída pelo clamp das bandas fixas (que já limita extremos);
    o parâmetro `winsor` deixou de ter efeito e é mantido só por compatibilidade de assinatura.
    """
    pesos = pesos or PESOS_BSD_PADRAO
    nomes = list(pesos.keys())

    brutos = [indicadores_bsd(c, anos_media) for c in empresas]

    # padroniza cada coluna contra a banda fixa de REFERENCIA_BSD (absoluto, não min-max do lote)
    notas: Dict[str, List[Optional[float]]] = {}
    for nome in nomes:
        coluna = [b.get(nome) for b in brutos]
        lo, hi = REFERENCIA_BSD[nome]
        notas[nome] = _padronizar_absoluto(coluna, lo, hi)

    soma_pesos = sum(pesos.values())

    resultado = []
    for i, c in enumerate(empresas):
        bsd = sum(notas[nome][i] * pesos[nome] for nome in nomes) / soma_pesos
        # fatores com indicador BRUTO ausente (entraram como neutro 50, não como pior valor)
        faltantes = [nome for nome in nomes if brutos[i].get(nome) is None]
        resultado.append({
            "ticker": c.ticker,
            "nome": c.nome,
            "setor": c.setor,
            "bsd": bsd,
            "acima_de_80": bsd > 80,
            "indicadores": brutos[i],
            "fatores_faltantes": faltantes,
            "n_fatores_faltantes": len(faltantes),
        })
    resultado.sort(key=lambda r: r["bsd"] or 0, reverse=True)
    return resultado


def bsd_empresa(c: CompanyData, cfg: Optional[dict] = None) -> Optional[float]:
    """BSD (0-100) de UMA empresa, reusando `bsd_ranking` (Fase 20 / SELO-01).

    Como a padronização do BSD é ABSOLUTA (clamp contra `REFERENCIA_BSD`, bandas fixas) e
    NÃO min-max do lote, o BSD de uma empresa isolada é IDÊNTICO ao que ela teria dentro de
    um lote maior — logo `bsd_ranking([c])[0]["bsd"]` é reproduzível e estável. Isso permite
    computar o selo de 1 ticker na aba Analisar sem depender de um universo carregado.

    Lê `pesos`/`anos_media`/`winsor` de `cfg["screening"]["bsd"]` quando `cfg` vier (os MESMOS
    parâmetros que o Garimpo usa → consistência entre menus). Com `cfg=None`, usa os defaults
    canônicos (`PESOS_BSD_PADRAO`/3/0.10). Never-raise para a UI: degrada para None quando a
    lista sai vazia ou o BSD é None.
    """
    pesos = PESOS_BSD_PADRAO
    anos_media = 3
    winsor = 0.10
    if cfg:
        bsd_cfg = (cfg.get("screening") or {}).get("bsd") or {}
        pesos = bsd_cfg.get("pesos") or pesos
        anos_media = bsd_cfg.get("anos_media", anos_media)
        winsor = bsd_cfg.get("winsor", winsor)

    ranking = bsd_ranking([c], pesos=pesos, anos_media=anos_media, winsor=winsor)
    if not ranking:
        return None
    return ranking[0].get("bsd")
