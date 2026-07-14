"""Modelo de dados de fundamentos por empresa e cálculos derivados.

`CompanyData` é preenchido pela camada de ingestão (CVM + yfinance + BCB) e consumido
pelo screening (Cap. 8), múltiplos (Cap. 10) e valuation (Cap. 13-17).

As séries anuais são dicionários {ano: valor} para tolerar buracos (anos faltantes),
que o livro trata como motivo de exclusão nos filtros de persistência.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import multiples as mult
from . import normalizacao as norm


@dataclass
class CompanyData:
    ticker: str
    nome: str = ""
    setor: str = ""
    anos: List[int] = field(default_factory=list)

    # séries anuais {ano: valor}
    lucro_liquido: Dict[int, float] = field(default_factory=dict)
    patrimonio_liquido: Dict[int, float] = field(default_factory=dict)
    fco: Dict[int, float] = field(default_factory=dict)          # fluxo de caixa operacional
    vendas_liquidas: Dict[int, float] = field(default_factory=dict)
    dividendos: Dict[int, float] = field(default_factory=dict)   # proventos totais (R$)
    num_acoes: Dict[int, float] = field(default_factory=dict)
    ativo_circulante: Dict[int, float] = field(default_factory=dict)
    passivo_circulante: Dict[int, float] = field(default_factory=dict)
    divida_lp: Dict[int, float] = field(default_factory=dict)    # exigível de longo prazo
    despesa_juros: Dict[int, float] = field(default_factory=dict)
    ativo_intangivel: Dict[int, float] = field(default_factory=dict)

    # snapshot atual / mercado
    preco_atual: Optional[float] = None
    volume_financeiro_diario: Optional[float] = None  # média R$/dia
    desempenho_relativo_6m: Optional[float] = None     # excesso de retorno vs Ibov
    g_lucro_esperado: Optional[float] = None           # crescimento esperado LP (analistas)
    beta: Optional[float] = None
    eh_concessionaria: bool = False
    serie_precos: Optional["pd.Series"] = None  # close diário 5a (índice = datas) p/ o gráfico
    ohlc: Optional["pd.DataFrame"] = None           # frame OHLCV nominal 5a (Yahoo cru, auto_adjust=False)
    ohlc_ajustado: Optional["pd.DataFrame"] = None  # OHLCV split-only-adjusted p/ indicadores (Phase 5)
    serie_precos_ajustada: Optional["pd.Series"] = None  # Adj Close 5a p/ RET-01 — retorno total, dividendos reinvestidos

    # proventos dos últimos 12 meses reais (datas do Yahoo) para o DY corrente (WR-04)
    dpa_trailing_12m: Optional[float] = None
    ano_dpa: Optional[int] = None  # ano-base do DPA usado (exposto p/ a Fase 2 exibir)

    # ---------------- DIAGNÓSTICO (Fase 8 / SAN) — leitura, não conserto ---------------- #
    # D-01/D-03: um CompanyData construído à mão NÃO pode nascer parecendo limpo.
    avisos: List["Aviso"] = field(default_factory=list)  # flags de sanidade disparadas (List genérica p/ não importar core.sanidade → ciclo)
    confianca: str = "nao_avaliada"                       # síntese; default inegociável (D-03), nunca "alta"

    # insumos dos checks (séries {ano: valor}) — os motores NÃO consomem nenhum destes
    lucro_controlador: Dict[int, float] = field(default_factory=dict)      # SAN-04: lucro do controlador (CVM 3.11.01)
    pl_nao_controladores: Dict[int, float] = field(default_factory=dict)   # SAN-04: minoritários no PL
    lpa_cvm: Dict[int, float] = field(default_factory=dict)                # LPA CRU da CVM (pré-divisão) — a causa-raiz
    dpa_por_ano: Dict[int, float] = field(default_factory=dict)            # SAN-03: DPA do Yahoo por ano
    proventos_filtro_amplo: Dict[int, float] = field(default_factory=dict) # SAN-03: DFC 6.03.* por "dividendo" OU "juros sobre capital"
    origem_num_acoes: Dict[int, str] = field(default_factory=dict)         # "cvm" | "yahoo_fallback" por ano (SAN-02)

    # insumos de mercado (SAN-01/SAN-02)
    market_cap: Optional[float] = None
    implied_shares_outstanding: Optional[float] = None
    splits: Dict[str, float] = field(default_factory=dict)  # {"YYYY-MM-DD": fator} histórico completo (D-12)

    # ------------------------------------------------------------------ #
    def anos_ordenados(self) -> List[int]:
        return sorted(a for a in self.anos)

    def ultimo_ano(self) -> Optional[int]:
        anos = self.anos_ordenados()
        return anos[-1] if anos else None

    def serie(self, attr: str, anos: Optional[List[int]] = None) -> List[float]:
        """Retorna a série de um atributo na ordem dos anos (pula faltantes)."""
        d: Dict[int, float] = getattr(self, attr)
        anos = anos or self.anos_ordenados()
        return [d[a] for a in anos if a in d]

    def lpa(self, ano: int) -> Optional[float]:
        return mult.lpa(self.lucro_liquido.get(ano), self.num_acoes.get(ano))

    def dpa(self, ano: int) -> Optional[float]:
        return mult.dpa(self.dividendos.get(ano), self.num_acoes.get(ano))

    def payout(self, ano: int) -> Optional[float]:
        return mult.dividend_payout(self.dpa(ano), self.lpa(ano))

    def payout_valuation(self) -> Optional[float]:
        """Payout-para-valuation: definição ÚNICA usada por DDM (Analisar) e regressão (Ranking).

        Mediana do payout sobre a série histórica COMPLETA (PAY-01); o expurgo de anos
        não-recorrentes é intrínseco à mediana (um desvio do próprio histórico é descartado
        sem marcar/excluir anos — D-01). SEM clamp em 1.0: a mediana pode ser legitimamente
        >100% para quem distribui de caixa regulatório acima do lucro contábil (TAEE11 ≈ 216%,
        D-03) — o piso já existente `g_alto = max(0, …)` no report trata payout>100% sem piso
        novo. `payout(ano)` CRU segue alimentando a tabela por ano, o detector de armadilha e
        o screening per-ano (D-06). Canônico, chamado sem args nas 3 superfícies (FIX-04).
        """
        serie = [self.payout(a) for a in self.anos_ordenados()]
        return norm.mediana_payout(serie)

    def roe(self, ano: int) -> Optional[float]:
        """ROE com PL médio ((PL_ini + PL_fim)/2); None quando falta o PL inicial.

        Base ÚNICA em toda a série: usa `roe_medio` (PL médio) quando há PL do ano anterior
        e do próprio ano. No 1º ano da janela (sem PL ano-1) retorna None em vez de cair
        silenciosamente para o PL final — assim a série nunca mistura bases (WR-01).

        CRU por ano: continua sendo a base da exibição "Fundamentos (por ano)" e do
        screening (Cap. 8, elegibilidade histórica per-ano). NÃO é o número de valuation —
        para isso use `roe_valuation()` (base de lucro normalizada). Fronteira FIX-04.
        """
        pl_ini = self.patrimonio_liquido.get(ano - 1)
        pl_fim = self.patrimonio_liquido.get(ano)
        if pl_ini is None:
            return None
        return mult.roe_medio(self.lucro_liquido.get(ano), pl_ini, pl_fim)

    # ------------------------------------------------------------------ #
    # FIX-04: métodos canônicos de VALUATION (base de lucro normalizada).
    #
    # `roe_valuation` / `lpa_valuation` são o número-síntese ÚNICO de qualidade
    # consumido por TODAS as superfícies de valuation (Analisar + Ranking app + Ranking
    # cli), substituindo o `roe(ult)`/`lpa(ult)` CRU de um único exercício. Espelham o
    # padrão de `payout_valuation` (canônico, chamado sem args em todas as superfícies →
    # consistência entre menus por construção). Os defaults `anos_media=3`/`winsor=0.10`
    # espelham o bloco `normalizacao` do config.yaml (knob canônico documentado).
    #
    # FRONTEIRA: `roe(ano)`/`lpa(ano)`/`payout(ano)`/`lucro_liquido` CRUS continuam
    # alimentando a tabela por ano e o screening (semântica de elegibilidade per-ano).
    # ------------------------------------------------------------------ #
    def base_lucro_normalizada(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
        """Base de lucro robusta a UM exercício atípico (mediana/média winsorizada dos
        últimos `anos_media` anos). É o lucro que o valuation consome no lugar do cru."""
        return norm.base_normalizada(self.serie("lucro_liquido"), anos_media, winsor)

    def serie_lucro_normalizada(self, winsor: float = 0.10) -> List[float]:
        """Série de lucro winsorizada (mesmo comprimento) p/ o CAGR de valuation — um ano
        atípico no início/fim deixa de distorcer o `g_historico`."""
        return norm.serie_winsorizada(self.serie("lucro_liquido"), winsor)

    def lpa_valuation(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
        """LPA canônico de valuation: base de lucro normalizada / nº de ações do último ano."""
        base = self.base_lucro_normalizada(anos_media, winsor)
        return mult.lpa(base, self.num_acoes.get(self.ultimo_ano()))

    def roe_valuation(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
        """ROE canônico de valuation: base de lucro normalizada / PL médio do último ano.

        Mesma fronteira de None que `roe(ano)` (sem PL do ano anterior → None), só trocando
        o lucro cru do último ano pela base normalizada."""
        base = self.base_lucro_normalizada(anos_media, winsor)
        if base is None:
            return None
        ult = self.ultimo_ano()
        if ult is None:
            return None
        pl_ini = self.patrimonio_liquido.get(ult - 1)
        pl_fim = self.patrimonio_liquido.get(ult)
        return mult.roe_medio(base, pl_ini, pl_fim)

    def margem_valuation(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
        """ML canônica de valuation: base de lucro normalizada / base de vendas normalizada.

        AUD-RANK-01: o Ranking por múltiplos consome ROE/LPA/EY já normalizados, mas o ML
        saía cru do último ano — um exercício atípico inflava (ou um prejuízo zerava/negativava)
        a margem e movia a empresa no ranque por um número que o resto do app já descarta.
        Espelha `roe_valuation`/`lpa_valuation` (mesma fronteira de None) p/ consistência entre
        superfícies. O ML CRU do último ano segue na tela Analisar (métrica de exibição)."""
        lucro = self.base_lucro_normalizada(anos_media, winsor)
        vendas = norm.base_normalizada(self.serie("vendas_liquidas"), anos_media, winsor)
        return mult.margem_liquida(lucro, vendas)

    def dy_atual(self) -> Optional[float]:
        """DY corrente. Usa o DPA dos últimos 12 meses reais quando disponível (WR-04);
        senão cai para o DPA do último ano-calendário coletado (fallback)."""
        if self.dpa_trailing_12m is not None:
            return mult.dividend_yield(self.dpa_trailing_12m, self.preco_atual)
        ano = self.ultimo_ano()
        if ano is None:
            return None
        return mult.dividend_yield(self.dpa(ano), self.preco_atual)

    # ------------------------------------------------------------------ #
    # FIX-06 (item J): DY RECORRENTE — leitura sustentável vs trailing.
    #
    # `dy_atual()` é o DY TRAILING: carrega os proventos dos últimos 12 meses, inclusive
    # um ano de distribuição extraordinária (JCP especial, dividendo de evento). Sobre um
    # ano atípico ele superestima a renda sustentável. O DY RECORRENTE aplica a MESMA
    # normalização de lucro (mediana/winsor dos últimos anos, primitiva do Plan 01) sobre
    # a série de PROVENTOS, devolvendo a renda que a empresa distribui de forma recorrente.
    # Ambos são exibidos lado a lado: o recorrente é a leitura sustentável; o trailing fica
    # como contexto (e segue alimentando o detector de armadilha de dividendos, Cap. 6).
    # ------------------------------------------------------------------ #
    def dpa_recorrente(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
        """DPA recorrente (sustentável) = payout sustentável aplicado ao lucro normalizado
        por ação (earnings-based, D-05): `payout_valuation() × lpa_valuation()`. Consistente
        com o `g_fund` (mesmo `payout_valuation`), e não mais a mediana crua da série de
        dividendos (que, no VULC3, cai inteira na era de payout >100%). Fronteira None: se
        payout ou LPA forem None, devolve None."""
        p = self.payout_valuation()
        l = self.lpa_valuation(anos_media, winsor)
        if p is None or l is None:
            return None
        return p * l

    def dy_recorrente(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
        """DY recorrente (sustentável): DPA recorrente earnings-based / preço. Distinto do
        `dy_atual()` trailing, que reflete os proventos extraordinários do período."""
        return mult.dividend_yield(self.dpa_recorrente(anos_media, winsor), self.preco_atual)
