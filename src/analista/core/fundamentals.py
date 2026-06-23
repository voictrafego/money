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

    # proventos dos últimos 12 meses reais (datas do Yahoo) para o DY corrente (WR-04)
    dpa_trailing_12m: Optional[float] = None
    ano_dpa: Optional[int] = None  # ano-base do DPA usado (exposto p/ a Fase 2 exibir)

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

    def payout_valuation(self, janela: int = 3) -> Optional[float]:
        """Payout-para-valuation: definição ÚNICA usada por DDM (Analisar) e regressão (Ranking).

        Média do payout cru dos `janela` últimos anos (ignorando os None), com clamp em
        1.0 (uma empresa não pode projetar distribuir mais que 100% do lucro). Substitui o
        antigo `_media_payout_3a`+clamp local do report, eliminando a divergência CR-02/WR-03
        (Analisar usava média 3a+clamp; Ranking usava 1 ano sem clamp). `payout(ano)` cru
        continua existindo para a exibição por ano.
        """
        anos = self.anos_ordenados()[-janela:]
        vals = [v for v in (self.payout(a) for a in anos) if v is not None]
        if not vals:
            return None
        return min(sum(vals) / len(vals), 1.0)

    def roe(self, ano: int) -> Optional[float]:
        """ROE com PL médio ((PL_ini + PL_fim)/2); None quando falta o PL inicial.

        Base ÚNICA em toda a série: usa `roe_medio` (PL médio) quando há PL do ano anterior
        e do próprio ano. No 1º ano da janela (sem PL ano-1) retorna None em vez de cair
        silenciosamente para o PL final — assim a série nunca mistura bases (WR-01).
        """
        pl_ini = self.patrimonio_liquido.get(ano - 1)
        pl_fim = self.patrimonio_liquido.get(ano)
        if pl_ini is None:
            return None
        return mult.roe_medio(self.lucro_liquido.get(ano), pl_ini, pl_fim)

    def dy_atual(self) -> Optional[float]:
        """DY corrente. Usa o DPA dos últimos 12 meses reais quando disponível (WR-04);
        senão cai para o DPA do último ano-calendário coletado (fallback)."""
        if self.dpa_trailing_12m is not None:
            return mult.dividend_yield(self.dpa_trailing_12m, self.preco_atual)
        ano = self.ultimo_ano()
        if ano is None:
            return None
        return mult.dividend_yield(self.dpa(ano), self.preco_atual)
