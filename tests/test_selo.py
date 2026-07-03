"""Golden tests do Selo de Sustentabilidade (Fase 20 / SELO-01 e SELO-02).

Trava a camada de DERIVAÇÃO da engine:
- cor do selo a partir do score BSD (cortes config-driven, com as BORDAS exatas);
- qualidade (Alta/Baixa) por cor;
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

from analista.report import selo


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
    assert selo._qualidade("amarelo") == "Baixa"
    assert selo._qualidade("vermelho") == "Baixa"
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
# Matriz de quadrante (SELO-02) — os 6 rótulos de D2
# --------------------------------------------------------------------------- #
def test_matriz_quadrante_alta():
    assert selo.montar_selo(85, "SUBAVALIADA — x", CFG).rotulo == "JOIA"
    assert selo.montar_selo(85, "NO INTERVALO — x", CFG).rotulo == "Boa, no preço"
    assert selo.montar_selo(85, "SOBREAVALIADA — x", CFG).rotulo == "Boa, mas cara"


def test_matriz_quadrante_baixa():
    assert selo.montar_selo(30, "SUBAVALIADA — x", CFG).rotulo == "VALUE TRAP"
    assert selo.montar_selo(30, "NO INTERVALO — x", CFG).rotulo == "Fraca"
    assert selo.montar_selo(30, "SOBREAVALIADA — x", CFG).rotulo == "Evitar"


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
    src = Path(selo.__file__).read_text(encoding="utf-8")
    assert "report" not in src.replace("report/selo", "")  # nenhum import de report
