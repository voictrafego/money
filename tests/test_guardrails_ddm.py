"""Guarda-corpo do DDM na borda de emissão/exibição (Achado 2 / SAN-01, Plan 01-07).

Onde o DDM roda mas produz faixa NEGATIVA (payout baixo / alto capex / lucro negativo →
DDM por dividendos estruturalmente inaplicável) ou DEGENERADA (0–0), a faixa NÃO é preço-alvo
— é ruído que o usuário lê como intrínseco. O guarda-corpo suprime a faixa (vmin/vmax → None,
caem no ramo 'não disponível') e sinaliza honestamente `ddm_inaplicavel`, sem tocar as
fórmulas de core/ddm.py nem o firewall selo↛report — só a borda de emissão (report.py) e a de
exibição (app.py / relatorio_markdown).

Casos reais (01-AUDIT-COERENCIA-DATA.json):
  HAPV3 vmin=-2.20/vmax=-1.66 · PCAR3 -7.67/-5.95 · PRIO3 0.0/0.0 (suprimir);
  TAEE11 29.03/47.06 · EGIE3 18.42/29.84 · SBSP3 6.16/9.75 (positivos — NÃO suprimir).

Tudo offline: nenhuma chamada de rede.
"""

import os

import yaml

from analista.core import ddm
from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _analise(vmin, vmax, sensibilidade=None):
    """AnaliseAcao mínima com a faixa já materializada na borda de emissão."""
    a = report.AnaliseAcao(ticker="X", nome="X", setor="S", preco_atual=10.0)
    a.vmin, a.vmax = vmin, vmax
    a.sensibilidade = sensibilidade
    return a


# --------------------------------------------------------------------------- #
# Task 1 — guarda-corpo de emissão: faixa negativa / degenerada suprimida
# --------------------------------------------------------------------------- #

def test_faixa_negativa_hapv3_suprimida():
    """vmax <= 0 (HAPV3-shape, faixa toda negativa) → faixa NÃO emitida como intrínseco."""
    a = _analise(-2.20, -1.66)
    report._guarda_faixa_ddm(a)
    assert a.vmin is None and a.vmax is None
    assert a.ddm_inaplicavel is True
    assert any("inaplic" in al.lower() for al in a.alertas)


def test_faixa_negativa_pcar3_suprimida():
    """PCAR3-shape (-7.67/-5.95): faixa negativa também suprimida."""
    a = _analise(-7.67, -5.95)
    report._guarda_faixa_ddm(a)
    assert a.vmin is None and a.vmax is None
    assert a.ddm_inaplicavel is True


def test_faixa_degenerada_zero_prio3_suprimida():
    """PRIO3-shape (0.00–0.00): faixa degenerada suprimida + sinalizada."""
    a = _analise(0.0, 0.0)
    report._guarda_faixa_ddm(a)
    assert a.vmin is None and a.vmax is None
    assert a.ddm_inaplicavel is True


def test_faixa_valida_positiva_taee11_nao_suprime():
    """Guard-rail inverso: faixa positiva válida (TAEE11-shape 29–47) intacta."""
    a = _analise(29.03, 47.06)
    report._guarda_faixa_ddm(a)
    assert a.vmin == 29.03 and a.vmax == 47.06
    assert a.ddm_inaplicavel is False
    assert not any("inaplic" in al.lower() for al in a.alertas)


def test_faixa_atravessa_zero_com_teto_positivo_nao_suprime():
    """vmin<0 mas vmax>0 (faixa cruza zero, teto positivo): NÃO é o caso degenerado do
    Achado 2 (que exige vmax<=0). Só suprime quando o TETO é <= 0."""
    a = _analise(-1.0, 5.0)
    report._guarda_faixa_ddm(a)
    assert a.vmax == 5.0
    assert a.ddm_inaplicavel is False


# --------------------------------------------------------------------------- #
# Task 2 — exibição honesta no relatório markdown (sem faixa negativa/zero)
# --------------------------------------------------------------------------- #

def _company_min():
    anos = [2023, 2024]
    c = CompanyData(ticker="INA3", nome="Inaplicável SA", setor="Cíclica", anos=anos)
    for i, ano in enumerate(anos):
        c.lucro_liquido[ano] = 100 + i
        c.patrimonio_liquido[ano] = 1000
        c.fco[ano] = 120
        c.vendas_liquidas[ano] = 400
        c.dividendos[ano] = 10
        c.num_acoes[ano] = 100
    c.preco_atual = 10.60
    return c


def _resultado_ddm_negativo():
    return ddm.ResultadoDDM(
        valor_intrinseco=-2.0, vp_dividendos=-1.0, vp_residual=-1.0,
        valor_residual_futuro=-1.0, dividendos_projetados=[-0.1], vp_por_ano=[-0.1],
    )


def test_relatorio_markdown_inaplicavel_sem_faixa_negativa():
    """A seção DDM de um caso ddm_inaplicavel NÃO estampa 'R$ -' nem '0,00' como intrínseco;
    exibe a nota honesta de inaplicabilidade em vez da tabela negativa."""
    c = _company_min()
    a = report.AnaliseAcao(ticker="INA3", nome="Inaplicável SA", setor="Cíclica",
                           preco_atual=10.60)
    a.ddm_inaplicavel = True
    a.vmin = a.vmax = None
    a.ddm_constante = _resultado_ddm_negativo()
    a.ddm_h = _resultado_ddm_negativo()
    a.sensibilidade = [[-2.0, -1.8], [-1.9, -1.66]]
    md = report.relatorio_markdown(c, a, _cfg())

    # Isola a seção "Valuation por Desconto de Dividendos"
    ini = md.index("## Valuation por Desconto de Dividendos")
    fim = md.index("## Veredito", ini)
    secao = md[ini:fim]

    assert "R$ -" not in secao          # nenhum valor intrínseco negativo estampado
    assert "-2" not in secao and "-1,66" not in secao
    assert "inaplic" in secao.lower()   # nota honesta presente


def test_relatorio_markdown_valido_mantem_tabela():
    """Caso NÃO-inaplicável com DDM real: a tabela de cenários continua sendo exibida."""
    c = _company_min()
    a = report.AnaliseAcao(ticker="OK3", nome="OK SA", setor="Energia", preco_atual=40.0)
    pos = ddm.ResultadoDDM(
        valor_intrinseco=45.0, vp_dividendos=30.0, vp_residual=15.0,
        valor_residual_futuro=20.0, dividendos_projetados=[3.0], vp_por_ano=[3.0],
    )
    a.ddm_constante = pos
    a.ddm_h = pos
    a.vmin, a.vmax = 29.03, 47.06
    md = report.relatorio_markdown(c, a, _cfg())
    ini = md.index("## Valuation por Desconto de Dividendos")
    fim = md.index("## Veredito", ini)
    secao = md[ini:fim]
    assert "45" in secao
    assert "inaplic" not in secao.lower()
