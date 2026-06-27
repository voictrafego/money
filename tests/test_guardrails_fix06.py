"""Guardrails de apresentação do FIX-06 (caso VULC3), travados por golden:

- **Banda intrínseca = sensibilidade REAL** (item H): `vmin/vmax` derivam do min/max da
  matriz Ke×g (`ddm.matriz_sensibilidade`, já calculada), não do toggle binário de 2
  cenários (ddm_constante × ddm_h). A matriz cobre o grid `delta_ke × delta_g` do config —
  É a sensibilidade real, mais larga que os 2 pontos centrais.
- **DY recorrente vs trailing** (item J): existe um DY recorrente sobre o dividendo
  NORMALIZADO (suaviza um ano de provento extraordinário), distinto do `dy_atual()`
  trailing — o recorrente é a leitura sustentável.
- **Setor correto** (item K): `resolver('VULC3', ...)` devolve Calçados/Consumo Cíclico,
  não o 'Têxtil e Vestuário' que o SETOR_ATIV da CVM classifica errado.

Tudo offline: nenhuma chamada de rede (o setor sai do override em data/ticker_map.json).
"""

import os

import yaml

from analista.core.fundamentals import CompanyData
from analista.ingest import universe
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _empresa_crescente_solida(ticker="SOLID3"):
    """10 anos de lucro/dividendos crescentes — DDM roda e a matriz Ke×g tem spread claro."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Sólida Crescente", setor="Energia Elétrica", anos=anos)
    for i, a in enumerate(anos):
        lucro = round(1000 * (1 + 0.08) ** i)
        c.lucro_liquido[a] = lucro
        c.patrimonio_liquido[a] = 4000 + i * 100
        c.dividendos[a] = round(0.5 * lucro)
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = lucro * 4
        c.fco[a] = lucro * 1.2
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = 25.0
    c.volume_financeiro_diario = 40_000_000
    c.desempenho_relativo_6m = 0.10
    c.beta = 0.8
    return c


def _empresa_com_provento_extraordinario(ticker="EXTR3"):
    """Dividendos estáveis com UM ano de provento extraordinário (10×) no fim da janela."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Com Extraordinário", setor="Calçados", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = 1000
        c.patrimonio_liquido[a] = 5000
        c.dividendos[a] = 100_000           # ~R$ recorrente; DPA = 100
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 4000
        c.fco[a] = 1200
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.dividendos[2024] = 1_000_000          # provento extraordinário (10×) no último ano
    c.preco_atual = 10.0
    c.dpa_trailing_12m = 1000.0             # trailing reflete o extraordinário (1_000_000/1000)
    c.num_acoes  # noqa
    c.beta = 0.8
    return c


# --------------------------------------------------------------------------- #
# (a) Banda intrínseca = sensibilidade real (item H)
# --------------------------------------------------------------------------- #
def test_banda_vem_da_matriz_de_sensibilidade():
    c = _empresa_crescente_solida()
    cfg = _cfg()
    a = report.analisar_acao(c, cfg)

    assert a.sensibilidade is not None, "DDM/ matriz não rodaram — checar fixture"
    celulas = [v for linha in a.sensibilidade for v in linha if v is not None]
    assert celulas

    # A banda exibida É o min/max da matriz Ke×g (sensibilidade real).
    assert a.vmin == min(celulas)
    assert a.vmax == max(celulas)

    # E é ESTRITAMENTE mais larga que o toggle binário (ddm_h, ddm_constante): a matriz
    # alcança um Ke menor (vmax maior) e um Ke maior (vmin menor) que os 2 pontos centrais.
    binario = [r.valor_intrinseco for r in (a.ddm_h, a.ddm_constante) if r]
    assert a.vmax > max(binario)
    assert a.vmin < min(binario)


def test_banda_degrada_quando_ddm_nao_roda():
    # Sem fundamentos suficientes (sem PL/ações) o DDM não roda → matriz None → sem banda,
    # sem exceção (T-08-07: matriz só-None não pode virar vmin/vmax espúrio).
    c = CompanyData(ticker="VAZIA3", anos=[2024])
    c.preco_atual = 10.0
    a = report.analisar_acao(c, _cfg())
    assert a.sensibilidade is None
    assert a.vmin is None and a.vmax is None
    assert a.veredito == ""


# --------------------------------------------------------------------------- #
# (b) DY recorrente vs trailing (item J)
# --------------------------------------------------------------------------- #
def test_dy_recorrente_menor_que_trailing_com_extraordinario():
    c = _empresa_com_provento_extraordinario()
    rec = c.dy_recorrente()
    trail = c.dy_atual()
    assert rec is not None and trail is not None
    # O recorrente (sobre dividendo normalizado, mediana ~100/ação) é MUITO menor que o
    # trailing (que carrega o provento extraordinário de 1000/ação).
    assert rec < trail


def test_relatorio_exibe_dy_recorrente_e_trailing():
    c = _empresa_com_provento_extraordinario()
    cfg = _cfg()
    a = report.analisar_acao(c, cfg)
    # Ambos expostos e DISTINTOS nos múltiplos.
    assert a.multiplos.get("DY") == c.dy_atual()
    assert a.multiplos.get("DY rec.") == c.dy_recorrente()
    assert a.multiplos["DY rec."] != a.multiplos["DY"]
    md = report.relatorio_markdown(c, a, cfg)
    assert "DY rec." in md
    assert "DY" in md


# --------------------------------------------------------------------------- #
# (c) Setor correto (item K) — override display-only, offline
# --------------------------------------------------------------------------- #
def test_setor_override_vulc3_calcados():
    cd, setor = universe.resolver("VULC3", "Vulcabras")
    assert cd == 11762
    assert "Calçados" in setor or "Consumo Cíclico" in setor
    assert "Têxtil" not in setor
