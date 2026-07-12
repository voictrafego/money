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


# --------------------------------------------------------------------------- #
# SAN-01 (Plan 03-02, Task 1) — guarda-corpo anti-aberração + reetiqueta literal
# --------------------------------------------------------------------------- #
# Regra literal do brief: SE intrínseco < 0,5×valor-dos-pares E ROE > 15% E corte de
# payout > 40% ENTÃO trocar "qualidade baixa/evitar" por "DDM conservador demais para
# este perfil — ver motor primário do arquétipo". No funil single-stock (valor_pares=None)
# a condição de pares degrada e o gate cai para as 2 restantes (custo-zero).

def _company_san01(lucro=1000, pl=5180, div_hist=467, div_ult=1050):
    """Empresa-âncora ITUB4-like: ROE ~19,3% (lucro/PL), payout cru do último ano ~105%
    mas mediana histórica ~46,7% → corte de payout ~55% (> 40%)."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker="ITX4", nome="Banco Aberr", setor="Bancos", anos=anos)
    for ano in anos:
        c.lucro_liquido[ano] = lucro
        c.patrimonio_liquido[ano] = pl
        c.num_acoes[ano] = 1000
        c.vendas_liquidas[ano] = 4000
        c.fco[ano] = 1200
        c.dividendos[ano] = div_ult if ano == anos[-1] else div_hist
    c.preco_atual = 70.0
    c.beta = 0.9
    return c


def _analise_sobreavaliada(intrinseco=8.0):
    a = report.AnaliseAcao(ticker="ITX4", nome="Banco Aberr", setor="Bancos", preco_atual=70.0)
    a.motor = "rim"
    a.motor_rotulo = "RIM"
    a.intrinseco_motor = intrinseco
    a.vmin, a.vmax = 5.0, 10.0
    a.veredito = (
        "SOBREAVALIADA — preço R$ 70,00 acima do intervalo intrínseco R$ 5,00–10,00"
    )
    return a


def test_san01_reetiqueta_aberracao_itub4_like():
    """Aberração-âncora (SOBREAVALIADA, ROE 19,3%, corte payout ~55%, valor_pares=None):
    dispara → veredito reetiquetado 'conservador demais', número visível, flag True."""
    c = _company_san01()
    a = _analise_sobreavaliada(intrinseco=8.0)
    assert abs((c.roe_valuation() or 0) - 0.193) < 0.01
    assert c.payout(c.ultimo_ano()) > 1.0
    report._guarda_san01(a, c, _cfg())
    assert a.san01_reetiquetado is True
    assert "conservador demais" in a.veredito
    assert "8" in a.veredito                       # intrínseco do motor visível
    assert "Evitar" not in a.veredito
    assert any("san" in al.lower() or "conservador" in al.lower() for al in a.alertas)


def test_san01_nao_dispara_sem_aberracao_roe_baixo():
    """ROE baixo (0,08): NÃO é aberração — veredito SOBREAVALIADA inalterado."""
    c = _company_san01(pl=12500)                   # ROE = 1000/12500 = 0,08
    a = _analise_sobreavaliada(intrinseco=8.0)
    veredito_antes = a.veredito
    assert (c.roe_valuation() or 0) < 0.15
    report._guarda_san01(a, c, _cfg())
    assert a.san01_reetiquetado is False
    assert a.veredito == veredito_antes


def test_san01_nao_dispara_veredito_nao_sobreavaliada():
    """Gatilho é o prefixo SOBREAVALIADA (o quadrante Baixa×Caro='Evitar'). Um veredito
    SUBAVALIADA/NO INTERVALO nunca é reetiquetado, por mais aberrante que sejam ROE/payout."""
    c = _company_san01()
    a = _analise_sobreavaliada()
    a.veredito = "NO INTERVALO — preço R$ 7,00 dentro de R$ 5,00–10,00"
    report._guarda_san01(a, c, _cfg())
    assert a.san01_reetiquetado is False
    assert a.veredito.startswith("NO INTERVALO")


def test_san01_never_raise_insumo_none():
    """Insumo ausente (sem PL do ano anterior → roe_valuation None) NÃO inventa aberração."""
    c = _company_san01()
    for ano in list(c.patrimonio_liquido):
        c.patrimonio_liquido[ano] = None           # roe_valuation → None
    a = _analise_sobreavaliada()
    report._guarda_san01(a, c, _cfg())
    assert a.san01_reetiquetado is False


def test_san01_pares_none_nao_puxa_rede():
    """valor_pares=None (funil single-stock, D-04): o gate cai para as 2 condições restantes
    (ROE E corte payout) e dispara sem nenhuma dependência de pares/rede."""
    c = _company_san01()
    a = _analise_sobreavaliada()
    report._guarda_san01(a, c, _cfg(), valor_pares=None)
    assert a.san01_reetiquetado is True


def test_config_tem_bloco_san01():
    cfg = _cfg()
    san01 = cfg["veredito"]["san01"]
    assert san01["fator_pares"] == 0.5
    assert san01["roe_min"] == 0.15
    assert san01["corte_payout_min"] == 0.40


# --------------------------------------------------------------------------- #
# SAN-01 (Plan 03-02, Task 2) — plug no funil + golden e2e ITUB4 sem "Evitar"
# --------------------------------------------------------------------------- #

def test_san01_e2e_itub4_nao_estampa_evitar():
    """Golden e2e: analisar_acao sobre a aberração ITUB4-like (financeira SOBREAVALIADA,
    ROE 19,3%, corte payout ~55%) reetiqueta ANTES do selo — nem o veredito nem o markdown
    contêm 'Evitar', e faixa_do_veredito devolve None (o selo suprime o quadrante)."""
    from analista.report import selo as selo_mod
    c = _company_san01()
    a = report.analisar_acao(c, _cfg())
    assert a.motor == "rim"
    assert a.san01_reetiquetado is True
    assert "conservador demais" in a.veredito
    assert "Evitar" not in a.veredito
    md = report.relatorio_markdown(c, a, _cfg())
    assert "Evitar" not in md
    # A reetiqueta suprime o quadrante: nenhum prefixo SUB/NO INTERVALO/SOBRE casa.
    assert selo_mod.faixa_do_veredito(a.veredito) is None
    # O número segue visível no texto reetiquetado (não é supressão).
    assert "intrínseco" in a.veredito


def test_san01_e2e_regulada_ddm_intocada():
    """Backstop não regride a pagadora regulada (motor==ddm, sem corte de payout): não
    reetiqueta — o veredito e o selo seguem exatamente como o VER-01/DDM os produziu."""
    from tests.test_report import _regulada_ddm
    c = _regulada_ddm()
    a = report.analisar_acao(c, _cfg())
    assert a.motor == "ddm"
    assert a.san01_reetiquetado is False
