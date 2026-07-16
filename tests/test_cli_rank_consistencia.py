"""WR-03 — o CLI `rank` carimba os MESMOS macro-inputs que `analyze` (Core Value cross-modo).

`cmd_analyze` resolve o rf (Selic-ciclo) e os deflatores do IPCA e os carimba em `cfg` ANTES
de `report.analisar_acao`; `cmd_rank` chamava `analisar_acao` com o `cfg` cru — sem rf, sem
deflatores. Para uma ação cíclica isso faz a MESMA ação mostrar um intrínseco (a 2ª lente do
ranque, ensemble motor×DDM) DIFERENTE do que `Analisar` mostra: uma cara num menu, outra no
outro — exatamente a inconsistência que o Core Value proíbe.

Este teste roda os DOIS entry points do CLI com a rede monkeypatchada (offline, determinístico)
e prova que `analisar_acao` recebe o MESMO carimbo (rf + deflatores) e produz o MESMO
`intrinseco_motor` nos dois. RED-able: antes do fix, `rank` não carimba → os inputs (e o
intrínseco) divergem. Ticker sintético; nenhum nível de reais asserido (só a IGUALDADE
cross-modo) — BLIND-04a-safe.
"""

import os
from argparse import Namespace

import yaml

from analista import cli
from analista.core.fundamentals import CompanyData
from analista.ingest import macro
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DEFL = {ano: (1.06) ** (2023 - ano) for ano in range(2014, 2024)}
_RF = 0.10


def _cfg():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _empresa_ciclica():
    """Lucro OSCILANTE com vale recente (perfil cíclico) — roteia ao motor 'normalizado'."""
    anos = list(range(2014, 2024))
    lucros = [1200.0, 2100.0, 500.0, 1900.0, 700.0, 2300.0, 400.0, 2000.0, 600.0, 1800.0]
    c = CompanyData(ticker="CICL3", nome="Ciclica SA",
                    setor="Siderurgia e Metalurgia", anos=anos)
    for ano, lucro in zip(anos, lucros):
        c.lucro_liquido[ano] = lucro
        c.num_acoes[ano] = 100.0
        c.patrimonio_liquido[ano] = 12000.0
        c.dividendos[ano] = 200.0
    c.beta = 1.3
    c.preco_atual = 25.0
    return c


def test_rank_e_analyze_carimbam_o_mesmo_macro_e_produzem_o_mesmo_intrinseco(monkeypatch, tmp_path):
    c = _empresa_ciclica()

    # Rede confinada e determinística.
    monkeypatch.setattr(macro, "selic_ciclo_para_capm", lambda fallback, anos=10: _RF)
    monkeypatch.setattr(macro, "ipca_deflatores_anuais", lambda anos=10: dict(_DEFL))
    monkeypatch.setattr(cli, "_montar", lambda tickers, cfg: [c])
    monkeypatch.setattr(cli, "OUT_DIR", str(tmp_path))
    # cmd_analyze renderiza markdown — irrelevante para este teste; stub para focar no carimbo.
    monkeypatch.setattr(report, "relatorio_markdown", lambda c, a, cfg: "")

    vistos = []
    _real = report.analisar_acao

    def _spy(cc, ccfg):
        a = _real(cc, ccfg)
        vistos.append({
            "rf": ccfg.get("capm", {}).get("rf_local"),
            "defl": (ccfg.get("macro") or {}).get("ipca_deflatores"),
            "motor": a.motor,
            "intr": a.intrinseco_motor,
        })
        return a

    monkeypatch.setattr(report, "analisar_acao", _spy)

    cli.cmd_analyze(Namespace(ticker="CICL3"), _cfg())
    cli.cmd_rank(Namespace(tickers="CICL3", tickers_file=None, setor=None), _cfg())

    assert len(vistos) == 2
    v_analyze, v_rank = vistos[0], vistos[1]

    # O carimbo macro (rf + deflatores) precisa ser IDÊNTICO entre os dois menus.
    assert v_analyze["rf"] == v_rank["rf"] == _RF
    assert v_analyze["defl"] == v_rank["defl"] == _DEFL

    # A ação é cíclica: o intrínseco vem do motor 'normalizado' (deflator-sensível).
    assert v_analyze["motor"] == "normalizado"
    # Core Value: o intrínseco do motor cíclico é o MESMO em rank e analyze.
    assert v_analyze["intr"] is not None
    assert v_analyze["intr"] == v_rank["intr"]
