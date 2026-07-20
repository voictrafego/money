"""Golden tests do Selo de Sustentabilidade (Fase 20 / SELO-01 e SELO-02).

Trava a camada de DERIVAÇÃO da engine:
- cor do selo a partir do score BSD (cortes config-driven, com as BORDAS exatas);
- qualidade (Alta/Atenção) por cor;
- faixa de preço a partir do PREFIXO do veredito do DDM;
- matriz de quadrante qualidade×preço (os 6 rótulos de D2);
- overlay VERIFICAR (alerta separado, sem rótulo de preço);
- degradação graciosa (bsd None / veredito vazio) — never-raise;
- firewall: selo.py não importa report.py.

Os cortes de cor são pinados contra o config.yaml shipado (mesmo padrão do test_report.py),
de modo que teste e engine compartilham `selo.cor.{verde_min,azul_min,amarelo_min}`.
"""

from pathlib import Path

import yaml

from analista.core import screening
from analista.core.fundamentals import CompanyData
from analista.report import report, selo


def _cfg() -> dict:
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


CFG = _cfg()


# --------------------------------------------------------------------------- #
# Cortes de cor (SELO-01) — incluindo as bordas exatas
# --------------------------------------------------------------------------- #
def test_cor_do_bsd_faixas_e_bordas():
    assert selo.cor_do_bsd(90, CFG) == "verde"
    assert selo.cor_do_bsd(70, CFG) == "verde"      # borda: >= verde_min
    assert selo.cor_do_bsd(69.9, CFG) == "azul"
    assert selo.cor_do_bsd(60, CFG) == "azul"
    assert selo.cor_do_bsd(55, CFG) == "azul"       # borda: >= azul_min
    assert selo.cor_do_bsd(54.9, CFG) == "amarelo"
    assert selo.cor_do_bsd(45, CFG) == "amarelo"
    assert selo.cor_do_bsd(40, CFG) == "amarelo"    # borda: >= amarelo_min
    assert selo.cor_do_bsd(39.9, CFG) == "vermelho"
    assert selo.cor_do_bsd(30, CFG) == "vermelho"
    assert selo.cor_do_bsd(0, CFG) == "vermelho"


def test_cor_do_bsd_none():
    assert selo.cor_do_bsd(None, CFG) is None


# --------------------------------------------------------------------------- #
# Qualidade por cor
# --------------------------------------------------------------------------- #
def test_qualidade_por_cor():
    assert selo._qualidade("verde") == "Alta"
    assert selo._qualidade("azul") == "Alta"
    assert selo._qualidade("amarelo") == "Atenção"
    assert selo._qualidade("vermelho") == "Atenção"
    assert selo._qualidade(None) is None


# --------------------------------------------------------------------------- #
# Faixa de preço a partir do prefixo do veredito
# --------------------------------------------------------------------------- #
def test_faixa_do_veredito_prefixos():
    assert selo.faixa_do_veredito("SUBAVALIADA — preço abaixo do intervalo") == "Barato"
    assert selo.faixa_do_veredito("NO INTERVALO — preço dentro de R$ ...") == "Justo"
    assert selo.faixa_do_veredito("SOBREAVALIADA — preço acima do intervalo") == "Caro"
    assert selo.faixa_do_veredito("VERIFICAR — sinais de risco contradizem") is None
    assert selo.faixa_do_veredito("") is None
    assert selo.faixa_do_veredito("Indeterminado") is None


# --------------------------------------------------------------------------- #
# Matriz de quadrante (SELO-02) — os rótulos de D2 ("Evitar" removido no Plano 13-06)
# --------------------------------------------------------------------------- #
def test_matriz_quadrante_alta():
    assert selo.montar_selo(85, "SUBAVALIADA — x", CFG).rotulo == "JOIA"
    assert selo.montar_selo(85, "NO INTERVALO — x", CFG).rotulo == "Boa, no preço"
    assert selo.montar_selo(85, "SOBREAVALIADA — x", CFG).rotulo == "Boa, mas cara"


def test_matriz_quadrante_atencao():
    # ENG-11/D-08: o eixo "Baixa" foi re-rotulado neutro ("Atenção"); VALUE TRAP/Fraca ficam.
    assert selo.montar_selo(30, "SUBAVALIADA — x", CFG).rotulo == "VALUE TRAP"
    assert selo.montar_selo(30, "NO INTERVALO — x", CFG).rotulo == "Fraca"
    # A célula ("Atenção","Caro") perdeu o rótulo "Evitar" → degrada para None (sem veredito binário).
    assert selo.montar_selo(30, "SOBREAVALIADA — x", CFG).rotulo is None


def test_montar_selo_joia_completo():
    s = selo.montar_selo(85, "SUBAVALIADA — x", CFG)
    assert s.cor == "verde"
    assert s.qualidade == "Alta"
    assert s.faixa_preco == "Barato"
    assert s.rotulo == "JOIA"
    assert s.verificar is False


# --------------------------------------------------------------------------- #
# Overlay VERIFICAR — alerta separado, sem rótulo de preço
# --------------------------------------------------------------------------- #
def test_overlay_verificar():
    s = selo.montar_selo(85, "VERIFICAR — sinais de risco", CFG)
    assert s.verificar is True
    assert s.faixa_preco is None
    assert s.rotulo is None
    # a cor/qualidade seguem derivadas do BSD (só o rótulo de preço é suprimido)
    assert s.cor == "verde"
    assert s.qualidade == "Alta"


# --------------------------------------------------------------------------- #
# Degradação graciosa
# --------------------------------------------------------------------------- #
def test_degradacao_bsd_none():
    s = selo.montar_selo(None, "NO INTERVALO — x", CFG)
    assert s.cor is None
    assert s.qualidade is None
    assert s.rotulo is None


def test_degradacao_veredito_vazio():
    s = selo.montar_selo(85, "", CFG)
    assert s.cor == "verde"       # cor segue definida pelo BSD
    assert s.qualidade == "Alta"
    assert s.faixa_preco is None
    assert s.rotulo is None        # sem faixa de preço → sem rótulo de quadrante


# --------------------------------------------------------------------------- #
# Firewall: selo.py não importa report.py
# --------------------------------------------------------------------------- #
def test_firewall_selo_nao_importa_report():
    # Inspeciona só as LINHAS DE IMPORT do módulo (docstring/comentários podem citar "report").
    src = Path(selo.__file__).read_text(encoding="utf-8")
    linhas_import = [
        ln.strip() for ln in src.splitlines()
        if ln.lstrip().startswith(("import ", "from "))
    ]
    assert not any("report" in ln for ln in linhas_import), linhas_import


# --------------------------------------------------------------------------- #
# Integração barata: analisar_acao popula a.selo coerente com o BSD e o veredito
# --------------------------------------------------------------------------- #
def _empresa_solida() -> CompanyData:
    """Fixture determinística de empresa sólida (espelha tests/test_screening.py)."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker="TAEE11", nome="Empresa Sólida", setor="Energia Elétrica", anos=anos)
    # Fidelidade à ingestão: utility regulada → pagadora_regulada → motor ddm (não pendente).
    c.eh_concessionaria = True
    for a in anos:
        c.lucro_liquido[a] = 1000 + (a - 2015) * 50
        c.patrimonio_liquido[a] = 4000 + (a - 2015) * 100
        c.dividendos[a] = 600 + (a - 2015) * 30
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 1800
        c.fco[a] = 1200
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = 30.0
    c.volume_financeiro_diario = 40_000_000
    c.desempenho_relativo_6m = 0.10
    c.beta = 0.8
    return c


def test_bsd_empresa_reproduzivel_vs_ranking():
    # bsd_empresa (1 empresa) == bsd_ranking([c]) — padronização ABSOLUTA, reproduzível.
    c = _empresa_solida()
    esperado = screening.bsd_ranking([c])[0]["bsd"]
    obtido = screening.bsd_empresa(c, CFG)
    assert obtido is not None
    assert 0.0 <= obtido <= 100.0
    assert abs(obtido - esperado) < 1e-9


def test_analisar_acao_popula_selo_coerente():
    c = _empresa_solida()
    a = report.analisar_acao(c, CFG)
    # a.selo é um Selo coerente com o BSD e o veredito JÁ calculados (read-only, sem rede).
    assert isinstance(a.selo, selo.Selo)
    bsd = screening.bsd_empresa(c, CFG)
    assert a.selo.cor == selo.cor_do_bsd(bsd, CFG)
    assert a.selo.qualidade == selo._qualidade(a.selo.cor)
    if a.veredito.startswith("VERIFICAR"):
        assert a.selo.verificar is True
        assert a.selo.faixa_preco is None and a.selo.rotulo is None
    else:
        assert a.selo.faixa_preco == selo.faixa_do_veredito(a.veredito)
