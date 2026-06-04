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

    def roe(self, ano: int) -> Optional[float]:
        """ROE com PL inicial (= PL do ano anterior, se houver; senão do próprio ano)."""
        pl_ini = self.patrimonio_liquido.get(ano - 1, self.patrimonio_liquido.get(ano))
        return mult.roe(self.lucro_liquido.get(ano), pl_ini)

    def dy_atual(self) -> Optional[float]:
        ano = self.ultimo_ano()
        if ano is None:
            return None
        return mult.dividend_yield(self.dpa(ano), self.preco_atual)
