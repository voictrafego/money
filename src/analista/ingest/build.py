"""Montagem de CompanyData a partir das fontes gratuitas (CVM + yfinance + BCB).

Combina:
  - fundamentos anuais (CVM): LL, PL, FCO, receita, ativos/passivos, dívida, intangível;
  - mercado (yfinance): preço, dividendos/ação por ano, nº de ações, beta, liquidez;
  - nº de ações por ano: a contagem OFICIAL da CVM (`composicao_capital`, ON+PN), com a escala
    (MILHARES × unidades) detectada contra o `impliedSharesOutstanding` (DATA-03). O fallback,
    quando o ano não tem contagem oficial, é o `impliedSharesOutstanding` (ON+PN) — NUNCA o
    `sharesOutstanding` (só a classe negociada). A derivação `LL/LPA`, causa-raiz da dispersão
    em 41/104 tickers, foi APOSENTADA; `c.lpa_cvm` segue como diagnóstico.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from ..core import sanidade
from ..core.fundamentals import CompanyData
from . import cvm, prices, universe


def _eh_unit(ticker: str) -> bool:
    """Tickers de UNIT na B3 terminam em '11' (ex.: TAEE11, KLBN11, SAPR11). Ações ON/PN
    terminam em 3/4/5/6. O preço e os proventos do Yahoo são POR UNIT, mas o "Lucro por
    Ação" da CVM é POR AÇÃO (total ON+PN) — daí a necessidade do fator de conversão."""
    return ticker.upper().replace(".SA", "").endswith("11")


def _fator_unit(contagem_oficial: Dict[int, float], acoes_yahoo: Optional[float]) -> int:
    """Nº de ações que compõem 1 unit (3 = TAEE/ALUP, ~5 = KLBN). A contagem OFICIAL da CVM
    (`composicao_capital`, já escalada) é a base POR AÇÃO (ON+PN total); o `sharesOutstanding`
    do Yahoo, para units, é a contagem de UNITS negociadas. A razão (ações/unit) é um inteiro
    pequeno — usamos a mediana das razões anuais, arredondada. Com a contagem ON+PN correta, o
    fator vira exato (ALUP11: 988.880.601 / 329.626.867 = 3,000), sem o valor 5 espúrio que a
    contagem inflada pelos minoritários produzia (Pitfall 5).

    Só aceita ≥ 2 (senão não há unit de fato); 1 = sem conversão (deixa os números intactos).
    A trava ≥ 2 protege não-units que caiam aqui por engano (razão ≈ 1 → fator 1)."""
    if not acoes_yahoo:
        return 1
    razoes = sorted(c / acoes_yahoo for c in contagem_oficial.values() if c)
    if not razoes:
        return 1
    mediana = razoes[len(razoes) // 2]
    cand = round(mediana)
    return cand if cand >= 2 else 1


def _escala_por_ano(
    oficial_cru: Dict[int, float], implied: Optional[float]
) -> Dict[int, float]:
    """Escala da contagem oficial (armadilha 3), detectada POR ANO. A CVM publica o
    `composicao_capital` em MILHARES para umas empresas (ITUB4/BRSR6) e em UNIDADES para outras
    (GOAU4/…). Usar a contagem CRUA reintroduziria o ×1000 por outro caminho (Pitfall 4).

    🔴 A unidade de reporte NÃO é constante DENTRO de um mesmo ticker: o `composicao_capital`
    troca de MILHARES para UNIDADES entre anos (PETR4 2020 vem em milhares, 2021+ em unidades;
    BBDC4 2020-2023 em milhares, 2024+ em unidades). Um fator ÚNICO — o do último ano — deixa os
    anos de escala diferente com o ×1000 PRESO, e o salto artificial ÷1000 reaparece na série
    (o mesmo Pitfall 4 num eixo novo, o temporal). Por isso ancoramos CADA ano no
    `impliedSharesOutstanding` (ON+PN, âncora limpa e ÚNICA) pela potência de 1000 mais próxima:
    a unidade é decidida ano a ano.

    Variação societária REAL (bonificação, fusão, recompra) é sempre < 1000× — logo nunca é
    confundida com troca de unidade e NÃO é mascarada (AGRO3 2020 = 59M contra 99M de 2021 fica
    intacto; o `implied/cru` = 1,68 arredonda a expoente 0). Uma anomalia CRUA que não seja
    potência de 1000 (ex.: CMIN3 2025 = 54,3 bi = 10× o real 5,4 bi, erro do próprio arquivo da
    CVM) NÃO é potência de 1000, então NÃO é tocada aqui — fica visível ao SAN, de propósito.

    Sem âncora (`implied` None — ex.: MRFG3 404): devolve a contagem crua (não confirmável, mas
    nunca aborta — SAN-06). Nunca ENCOLHE (`max(0, expoente)`) — multiplicar por unidade perdida
    é o conserto; dividir perderia ações reais."""
    if not implied:
        return _alinhar_escala_interna(oficial_cru)
    escalado: Dict[int, float] = {}
    for ano, cru in oficial_cru.items():
        if cru and cru > 0:
            expoente = round(math.log10(implied / cru) / 3.0)  # potência de 1000, por ano
            escalado[ano] = cru * (1000 ** max(0, expoente))
        else:
            escalado[ano] = cru
    return escalado


def _alinhar_escala_interna(oficial_cru: Dict[int, float]) -> Dict[int, float]:
    """Alinhamento de escala INTERNO À SÉRIE, para quando NÃO há âncora externa (`implied`
    None — ELET3/ELET6/IGTI11 dão 404 no Yahoo). O `composicao_capital` troca de MILHARES para
    UNIDADES entre anos do MESMO ticker (ELET3: 2020 em unidades = 1,57 bi, 2021+ em milhares =
    1,57 M) → salto artificial ÷1000 que o SAN-02 acende. Sem `impliedSharesOutstanding`, a
    unidade de cada ano é inferida da PRÓPRIA série: a "banda" de cada ano é `round(log10(n)/3)`
    (a potência de 1000), a banda de REFERÊNCIA é a mais frequente (empate → a do ano mais
    recente) e cada ano é trazido à referência por `1000 ** (banda − ref)`.

    Corrige SÓ desvios que são potência de 1000 (troca de unidade). Variação corporativa REAL
    (não-potência-de-1000) sobrevive: no IGTI11 o salto 2020→2021 = 12.811 = 1000 (unidade) ×
    ~12,8 (reorganização real de 2021) — a unidade é corrigida, os ~12,8× reais permanecem e o
    SAN-02 os reporta, de propósito. Menos de 2 anos com contagem: devolve a série crua."""
    validos = {a: v for a, v in oficial_cru.items() if v and v > 0}
    if len(validos) < 2:
        return dict(oficial_cru)
    bandas = {a: round(math.log10(v) / 3.0) for a, v in validos.items()}
    freq: Dict[int, int] = {}
    for b in bandas.values():
        freq[b] = freq.get(b, 0) + 1
    mais_freq = max(freq.values())
    candidatas = [b for b, f in freq.items() if f == mais_freq]
    banda_ano_recente = bandas[max(validos)]
    ref = banda_ano_recente if banda_ano_recente in candidatas else max(candidatas)
    return {
        a: (v / (1000 ** (bandas[a] - ref)) if (v and v > 0) else v)
        for a, v in oficial_cru.items()
    }


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
    # DIAGNÓSTICO (Fase 8 / SAN) — insumos de mercado paralelos (SAN-01/SAN-02/SAN-03).
    c.market_cap = dm.market_cap
    c.implied_shares_outstanding = dm.implied_shares_outstanding
    c.splits = dm.splits
    c.dpa_por_ano = dict(dm.dividendos_por_ano)
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

    # Passo 1: fundamentos por ano + contagem OFICIAL de ações da CVM por ano (CRUA, ON+PN).
    # DATA-03 (Fase 9): a fonte de num_acoes deixa de ser a derivação LL/LPA (base cruzada, a
    # causa-raiz da dispersão em 41/104 tickers) e passa a ser a contagem oficial do
    # composicao_capital (cvm.contagem_oficial_do_ano). A escala é aplicada depois do laço.
    oficial_cru: Dict[int, float] = {}
    dist_cvm: Dict[int, float] = {}  # proventos pagos (div + JCP) por ano, da CVM
    for ano in anos:
        f = cvm.fundamentos_do_ano(cd_cvm, ano)
        # DATA-02 (Fase 9): lucro E PL na base do CONTROLADOR, acoplados por um ÚNICO gate em
        # lucro_controlador — para nunca cruzar bases (lucro do controlador com PL consolidado é
        # exatamente a doença que o SAN-04 detecta). COM controlador: LL = controlador e PL =
        # consolidado − minoritários (os dois juntos). SEM controlador (single-entity): ambos
        # ficam no consolidado (fallback) e minoritários NÃO são subtraídos mesmo que
        # pl_nao_controladores exista — lucro (DRE) e PL (BPP) podem divergir em disponibilidade,
        # e subtrair só o PL recriaria a base cruzada. `.get()` tolera stubs sem a chave.
        if f.get("lucro_controlador") is not None:
            c.lucro_liquido[ano] = f["lucro_controlador"]
            if f.get("patrimonio_liquido") is not None:
                c.patrimonio_liquido[ano] = f["patrimonio_liquido"] - (f.get("pl_nao_controladores") or 0)
        else:
            if f.get("lucro_liquido") is not None:
                c.lucro_liquido[ano] = f["lucro_liquido"]
            if f.get("patrimonio_liquido") is not None:
                c.patrimonio_liquido[ano] = f["patrimonio_liquido"]
        for campo in ("fco", "vendas_liquidas",
                      "ativo_circulante", "passivo_circulante", "divida_lp",
                      "ativo_intangivel"):
            if f[campo] is not None:
                getattr(c, campo)[ano] = f[campo]

        cont_oficial = cvm.contagem_oficial_do_ano(cd_cvm, ano)
        if cont_oficial is not None:
            oficial_cru[ano] = cont_oficial
        if f.get("dividendos_distribuidos") is not None:
            dist_cvm[ano] = f["dividendos_distribuidos"]

        # DIAGNÓSTICO (Fase 8 / SAN) — insumos PARALELOS; nenhum motor os consome. c.dividendos
        # continua saindo de dist_cvm (filtro estreito, sujo); proventos_filtro_amplo é à parte.
        for campo in ("lucro_controlador", "pl_nao_controladores", "proventos_filtro_amplo"):
            if f.get(campo) is not None:
                getattr(c, campo)[ano] = f[campo]
        if f.get("lpa") is not None:
            c.lpa_cvm[ano] = f["lpa"]  # LPA cru da CVM (pré-divisão) — a causa-raiz

    # Escala (armadilha 3 / Pitfall 4): a contagem oficial vem em MILHARES (ITUB4/BRSR6) ou em
    # UNIDADES (GOAU4/…) — e a unidade TROCA entre anos de um mesmo ticker. Detecta o fator
    # POR ANO contra o impliedSharesOutstanding (âncora ON+PN) — nunca usa a contagem crua nem um
    # fator único de série (que deixaria o ×1000 preso nos anos de escala divergente).
    oficial: Dict[int, float] = _escala_por_ano(oficial_cru, dm.implied_shares_outstanding)

    # BUG-UNIT: a contagem oficial é POR AÇÃO (ON+PN), mas preço e proventos (Yahoo) são POR UNIT.
    # Sem converter, LPA/P/L/EY ficam inflados pelo fator da unit (3× TAEE/ALUP, ~5× KLBN), o
    # payout estoura (>100% falso) e o DDM subavalia a unit → veredito "sobreavaliada" espúrio.
    # Dividir pela contagem pelo fator coloca num_acoes na base de UNITS, alinhando ao preço.
    fator = _fator_unit(oficial, acoes_atual) if _eh_unit(ticker) else 1

    # Passo 2: num_acoes na base de UNITS e dividendos totais (consistentes com o preço).
    # DATA-03 (armadilha 1): o fallback é o impliedSharesOutstanding (ON+PN), NUNCA o
    # sharesOutstanding (dm.num_acoes = só a classe negociada), que daria falso ~2× em toda
    # empresa com PN.
    implied = dm.implied_shares_outstanding
    for ano in anos:
        if ano in oficial:
            c.num_acoes[ano] = oficial[ano] / fator
            c.origem_num_acoes[ano] = "cvm"          # SAN-02: carimba a origem de cada ano
        elif implied:
            c.num_acoes[ano] = implied / fator
            c.origem_num_acoes[ano] = "yahoo_fallback"

        # dividendos totais do ano (R$). 🔴 BUG-JCP — a DIREÇÃO ESTÁ AO CONTRÁRIO DO QUE O
        # COMENTÁRIO ANTIGO AFIRMAVA (medido, não suposto): é a CVM que PERDE o JCP, não o
        # Yahoo. O filtro de cvm.py:169 casa só "dividendo", e o BRSR6 fila o JCP em
        # 6.03.04 "Juros sobre o Capital Próprio Pagos" → a CVM devolve R$ 36,0 M em 2025
        # contra R$ 620,0 M reais (18× a menos; 19×/24×/25×/5× em 2021-2024). E o DPA do
        # Yahoo INCLUI o JCP: bate com o provento real do BRSR6 com erro < 5% em 4 anos. Os 4
        # grandes bancos escapam por acidente (linha "Dividendos E Juros sobre o Capital
        # Próprio Pagos", que casa o filtro). Ou seja: o código PREFERE a CVM (dist_cvm)
        # exatamente ONDE a CVM está quebrada. Consertar isso é o DATA-01 da Fase 9, NÃO aqui —
        # a lógica abaixo fica idêntica (c.dividendos continua sujo, de propósito, como
        # teste de regressão). O detector do JCP perdido usa c.proventos_filtro_amplo (paralelo).
        if ano in dist_cvm:
            c.dividendos[ano] = dist_cvm[ano]
        else:
            dpa = dm.dividendos_por_ano.get(ano)
            if dpa is not None and ano in c.num_acoes:
                c.dividendos[ano] = dpa * c.num_acoes[ano]

    # mantém apenas anos com lucro líquido coletado (núcleo da análise)
    c.anos = sorted(a for a in anos if a in c.lucro_liquido)
    # DIAGNÓSTICO (Fase 8 / SAN) — a CHAMADA ÚNICA, provada por execução (D-02/D-04).
    # never-raise (SAN-06): não pode derrubar montar_empresa. NÃO conserta dado nenhum.
    sanidade.aplicar_sanidade(c)
    return c
