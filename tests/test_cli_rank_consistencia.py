"""WR-03 — a MESMA ação mostra os MESMOS múltiplos crus no `rank` e no `analyze` (Core Value).

RECONCILIAÇÃO com o 13-06: o Ranking foi REBAIXADO a screener por múltiplos crus (ENG-11) —
`cmd_rank` NÃO chama mais `report.analisar_acao` nem carimba macro; a 2ª lente ensemble×DDM
(preço-alvo/upside/veredito) e o `intrinseco_motor`/`a.ke` SAÍRAM do ranque (a regressão de
pares é cega ao nível de preço, memória `ranking-e-cego-ao-preco`). Logo a propriedade
cross-menu ANTIGA (`analyze` e `rank` batem em `a.ke`/`intrinseco_motor`) DEIXOU DE EXISTIR —
o teste que a travava foi deletado no 13-06.

O que SOBREVIVE (e é o Core Value cross-modo, FIX-04 em `cli.py`/`report.py`): os múltiplos
CRUS que o screener ordena (ROE, P/L, EY) saem dos MESMOS métodos canônicos normalizados de
`CompanyData` que o `Analisar` expõe em `a.multiplos`. A mesma ação NÃO pode mostrar um P/L
num menu e outro no outro. Este teste prova essa igualdade por EXECUÇÃO dos dois entry points
(offline, determinístico), sem asserir colunas removidas (preço-alvo/upside/veredito) nem
`a.ke`/`intrinseco_motor` (que o `rank` não produz mais). Ticker sintético, nenhum nível de
reais asserido — só a IGUALDADE cross-modo. BLIND-04a-safe.
"""

import os
from argparse import Namespace

import yaml

from analista import cli
from analista.core import comparables as cmp
from analista.core.fundamentals import CompanyData
from analista.ingest import macro
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DEFL = {ano: (1.06) ** (2023 - ano) for ano in range(2014, 2024)}
_RF = 0.10


def _cfg():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _empresa():
    """Empresa lucrativa estável — P/L, ROE, EY e DY todos computáveis (múltiplos não-None)."""
    anos = list(range(2014, 2024))
    c = CompanyData(ticker="MULT3", nome="Multipla SA",
                    setor="Bancos", anos=anos)
    for ano in anos:
        c.lucro_liquido[ano] = 1800.0
        c.lucro_controlador[ano] = 1800.0
        c.num_acoes[ano] = 100.0
        c.patrimonio_liquido[ano] = 12000.0
        c.dividendos[ano] = 900.0
    c.beta = 1.1
    c.preco_atual = 30.0
    return c


def test_rank_e_analyze_mostram_os_mesmos_multiplos_crus(monkeypatch, tmp_path):
    c = _empresa()

    # Rede confinada e determinística (os dois entry points ficam offline).
    monkeypatch.setattr(macro, "selic_ciclo_para_capm", lambda fallback, anos=10: _RF)
    monkeypatch.setattr(macro, "ipca_deflatores_anuais", lambda anos=10: dict(_DEFL))
    monkeypatch.setattr(macro, "ipca_ciclo_para_g", lambda fallback, anos=10: 0.0518)
    monkeypatch.setattr(cli, "_montar", lambda tickers, cfg: [c])
    monkeypatch.setattr(cli, "OUT_DIR", str(tmp_path))
    # cmd_analyze renderiza markdown — irrelevante aqui; stub para focar nos múltiplos de a.multiplos.
    monkeypatch.setattr(report, "relatorio_markdown", lambda c, a, cfg: "")

    # ANALYZE: espia a AnaliseAcao para capturar os múltiplos de valuation expostos (a.multiplos).
    mult_analyze = {}
    _real_analisar = report.analisar_acao

    def _spy_analisar(cc, ccfg):
        a = _real_analisar(cc, ccfg)
        mult_analyze.update(a.multiplos)
        return a

    monkeypatch.setattr(report, "analisar_acao", _spy_analisar)

    # RANK: espia o ranqueador para capturar o dict de múltiplos CRUS que o screener ordena.
    mult_rank = {}
    _real_ranking = cmp.ranking_por_multiplos

    def _spy_ranking(nomes, multiplos, pesos=None):
        mult_rank.update({k: list(v) for k, v in multiplos.items()})
        return _real_ranking(nomes, multiplos, pesos)

    monkeypatch.setattr(cmp, "ranking_por_multiplos", _spy_ranking)

    cli.cmd_analyze(Namespace(ticker="MULT3"), _cfg())
    cli.cmd_rank(Namespace(tickers="MULT3", tickers_file=None, setor=None), _cfg())

    assert mult_analyze, "o Analisar não expôs a.multiplos (fluxo não rodou)"
    assert mult_rank, "o Ranking não chamou ranking_por_multiplos (fluxo não rodou)"

    # Core Value cross-modo (FIX-04): ROE/P/L/EY do screener == os do Analisar, POR CONSTRUÇÃO
    # (ambos leem os métodos canônicos normalizados de CompanyData — não recomputam por menu).
    # É a fonte única cross-modo que SOBREVIVE ao rebaixamento do Ranking (13-06).
    assert mult_rank["ROE"][0] == mult_analyze["ROE"]
    assert mult_rank["PL"][0] == mult_analyze["P/L"]
    assert mult_rank["EY"][0] == mult_analyze["EY"]

    # Sanidade: os múltiplos existem (o teste não é vacuamente verde com None==None).
    assert mult_analyze["P/L"] is not None
    assert mult_analyze["ROE"] is not None
