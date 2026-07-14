"""Golden do CAPM 'local' (DDM-FIX-03 — caso VULC3).

Ke pela abordagem `local` (Cap. 17.2): `Ke = rf + beta × ERP`, com `rf` = Selic ao vivo
do BCB e `ERP Brasil` fixo documentado. Fallback gracioso: se `selic_meta()` → None (BCB
indisponível), o rf degrada para o `selic_fallback` do config, SEM exceção.

Invariante crítica (pureza da engine): `analisar_acao` NÃO toca a rede — lê apenas o rf já
resolvido em `cfg['capm']['rf_local']`. A chamada ao BCB vive nos entry points (cli/app).
Por isso todo este arquivo é offline/determinístico: o resolvedor é monkeypatchado e a
engine recebe o rf de fallback direto no cfg.
"""

import os

import yaml

from analista.core import capm
from analista.core.fundamentals import CompanyData
from analista.ingest import macro
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_config_capm_local_documentado():
    """O config shipado usa a abordagem 'local' com os três slots novos documentados."""
    cap = _cfg()["capm"]
    assert cap["abordagem"] == "local"
    assert "erp_local" in cap
    assert "rf_local" in cap
    assert "selic_fallback" in cap
    # rf_local default == selic_fallback: é o slot que os entry points SOBRESCREVEM com a
    # Selic ao vivo; offline (testes) ele vale o fallback e a engine roda determinística.
    assert cap["rf_local"] == cap["selic_fallback"]


def test_ke_local_materialmente_acima_do_ke_de_2019():
    """INVARIANTE (WR-04): a abordagem `local` produz um Ke materialmente ACIMA dos literais
    de 2019 (9,43%) — que é a razão de ela existir. Sobrevive à cura: mesmo com o ERP do KE-02
    (0,06 → 0,045), o `rf_local` sozinho (10,5%) já está acima dos 9,4%.

    Estava PRESO dentro do golden da faixa 0,13–0,22 (função única, `golden_nivel` ⇒ fora do
    run default). A Fase 12 deletaria a função inteira e levaria este invariante junto.
    """
    cap = _cfg()["capm"]
    ke = capm.ke_local(0.88, cap["rf_local"], cap["erp_local"])
    assert ke > 0.094          # materialmente acima do Ke de 2019 (9,43%)


def test_ke_local_na_faixa_small_cap_br():
    """GOLDEN DE NÍVEL: a faixa 0,13–0,22 é função direta dos knobs `rf_local`/`erp_local`.

    Trava um NÚMERO ⇒ trava o método atual. MORRE na Fase 12 (KE) — DELETAR, nunca atualizar.
    O invariante que morava aqui foi extraído para
    `test_ke_local_materialmente_acima_do_ke_de_2019`, que SOBREVIVE a esta deleção (WR-04).

    Caso VULC3, beta 0,88: com rf de fallback (0,105) e erp 0,06 ⇒ 0,105 + 0,88×0,06 = 0,1578.
    """
    cap = _cfg()["capm"]
    ke = capm.ke_local(0.88, cap["rf_local"], cap["erp_local"])
    assert 0.13 < ke < 0.22    # faixa small cap BR


def test_resolvedor_rf_usa_selic_ao_vivo(monkeypatch):
    """selic_meta() devolve valor ⇒ o resolvedor usa a Selic ao vivo (ignora o fallback)."""
    monkeypatch.setattr(macro, "selic_meta", lambda: 0.15)
    assert macro.selic_para_capm(0.105) == 0.15


def test_resolvedor_rf_degrada_para_fallback(monkeypatch):
    """selic_meta() → None (BCB indisponível) ⇒ o resolvedor degrada p/ o fallback, sem exceção."""
    monkeypatch.setattr(macro, "selic_meta", lambda: None)
    assert macro.selic_para_capm(0.105) == 0.105


# --------------------------------------------------------------------------- #
# Problema 3 — rf "through-the-cycle" (média da Selic), não a spot
# --------------------------------------------------------------------------- #
def test_rf_ciclo_usa_media_da_serie(monkeypatch):
    """Com a série histórica disponível, o rf do CAPM é a MÉDIA dela (não a Selic spot)."""
    monkeypatch.setattr(macro, "_selic_historico", lambda anos=10: [0.14, 0.10, 0.06, 0.02])
    assert macro.selic_ciclo_para_capm(0.105) == 0.08  # média de 14/10/6/2%


def test_rf_ciclo_degrada_para_spot_depois_fallback(monkeypatch):
    """Sem a série (rede fora): cai para a Selic spot; sem spot, para o fallback do config."""
    monkeypatch.setattr(macro, "_selic_historico", lambda anos=10: [])
    monkeypatch.setattr(macro, "selic_meta", lambda: 0.1425)
    assert macro.selic_ciclo_para_capm(0.105) == 0.1425  # spot
    monkeypatch.setattr(macro, "selic_meta", lambda: None)
    assert macro.selic_ciclo_para_capm(0.105) == 0.105   # fallback


def test_config_tem_rf_ciclo_anos():
    """O config shipado documenta a janela do rf through-the-cycle."""
    assert _cfg()["capm"]["rf_ciclo_anos"] >= 1


def test_engine_offline_ke_determinístico():
    """`analisar_acao` consome o rf_local do cfg (fallback) SEM tocar a rede ⇒ Ke determinístico.

    Prova a pureza/offline da engine: o Ke calculado é exatamente rf_local + beta×erp_local
    do config, sem nenhuma chamada ao BCB dentro de analisar_acao.
    """
    cfg = _cfg()
    anos = list(range(2015, 2025))
    c = CompanyData(ticker="VULC3T", nome="Small Cap BR", setor="Calçados", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = 1000
        c.patrimonio_liquido[a] = 4000
        c.dividendos[a] = 500
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 5000
        c.fco[a] = 1200
    c.preco_atual = 10.0
    c.beta = 0.88

    a = report.analisar_acao(c, cfg)

    esperado = cfg["capm"]["rf_local"] + 0.88 * cfg["capm"]["erp_local"]
    assert a.ke is not None
    assert abs(a.ke - esperado) < 1e-9
