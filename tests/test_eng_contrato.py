"""ENG-05/06/07/09 — contrato de saída do livro (Cap. 17) sobre o RIM único (contrato).

Testa FORMATO / BORDA / never-raise, NUNCA nível: a tríade SUBAVALIADA / NO INTERVALO /
SOBREAVALIADA é função da POSIÇÃO de `preco` vs a região `[V×(1−MS), V×(1+MS)]`; a região é
SIMÉTRICA e escala com a MS (controle do usuário, nunca calibrada); e uma razão implícita
patológica DEGRADA o veredito para VERIFICAR sem levantar (guard runtime never-raise).

Fixtures 100% sintéticas, offline. SEM nomear ticker real, SEM asserir número-alvo do livro
(a validação do caso soberano do livro = Fase 14 é sagrada).
"""

import os

import pytest
import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _financeira_sadia(ticker="SYN3", roe_alvo=0.20) -> CompanyData:
    """Financeira sintética (hard-route → RIM) com ROE constante = `roe_alvo`, razão implícita SÃ
    quando roe_alvo é moderado. Sem flags de risco (payout ~30%, DY baixo). Produz intrínseco
    finito e positivo, logo uma região `[V×(1−MS), V×(1+MS)]` bem-definida."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Financeira Sintética", setor="Bancos", anos=anos)
    pl = 5000.0
    for a in anos:
        c.lucro_liquido[a] = roe_alvo * pl
        c.patrimonio_liquido[a] = pl
        c.dividendos[a] = 0.30 * roe_alvo * pl   # payout 30% → sem armadilha
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 4000
        c.fco[a] = 1200
    c.preco_atual = 1.0   # placeholder; os testes o reposicionam vs a banda
    c.beta = 0.9
    return c


def _analise_com_preco(c: CompanyData, cfg: dict, preco: float):
    c.preco_atual = preco
    return report.analisar_acao(c, cfg)


# --- (a) A tríade é função da POSIÇÃO de `preco` vs a região da MS ------------------------------ #


@pytest.mark.contrato
def test_triade_vem_da_posicao_do_preco_vs_regiao_da_ms():
    """ENG-05: SUBAVALIADA / NO INTERVALO / SOBREAVALIADA saem SÓ da posição de `preco` vs
    `[V×(1−MS), V×(1+MS)]` — FORMATO, não nível. A região (vmin/vmax) independe do preço; variar
    só o preço percorre os três ramos. (O V vem do RIM único; não asserimos o V em reais.)"""
    cfg = _cfg()
    c = _financeira_sadia()
    base = report.analisar_acao(c, cfg)
    assert base.intrinseco_motor is not None and base.intrinseco_motor > 0
    assert base.vmin is not None and base.vmax is not None
    assert not base.razao_patologica   # pré-condição: razão sã, o ramo limpo da tríade

    vmin, vmax = base.vmin, base.vmax
    abaixo = _analise_com_preco(c, cfg, vmin * 0.5)
    dentro = _analise_com_preco(c, cfg, (vmin + vmax) / 2.0)
    acima = _analise_com_preco(c, cfg, vmax * 1.5)

    assert abaixo.veredito.startswith("SUBAVALIADA"), abaixo.veredito
    assert dentro.veredito.startswith("NO INTERVALO"), dentro.veredito
    assert acima.veredito.startswith("SOBREAVALIADA"), acima.veredito


@pytest.mark.contrato
def test_regiao_e_simetrica_e_escala_com_a_margem_de_seguranca():
    """ENG-06: a região é SIMÉTRICA sobre V (vmax−V == V−vmin) e escala com a MS (dobrar a MS dobra
    a meia-largura simetricamente). A MS é PARÂMETRO consumido de cfg — nunca calibrada aqui."""
    cfg = _cfg()
    c = _financeira_sadia()

    cfg["veredito"]["margem_seguranca"] = 0.05
    a5 = report.analisar_acao(c, cfg)
    v = a5.intrinseco_motor
    assert v is not None and v > 0
    # simetria exata sobre V.
    assert abs((a5.vmax - v) - (v - a5.vmin)) < 1e-9
    assert abs((a5.vmax - v) - v * 0.05) < 1e-9

    cfg["veredito"]["margem_seguranca"] = 0.10
    a10 = report.analisar_acao(c, cfg)
    # V é invariante à MS (a MS não move o valor, só a banda).
    assert abs(a10.intrinseco_motor - v) < 1e-9
    # dobrar a MS dobra a meia-largura, simetricamente dos dois lados.
    assert abs((a10.vmax - v) - 2.0 * (a5.vmax - v)) < 1e-9
    assert abs((v - a10.vmin) - 2.0 * (v - a5.vmin)) < 1e-9


@pytest.mark.contrato
def test_razao_patologica_degrada_veredito_never_raise():
    """ENG-09/D-10b: um insumo que produz razão implícita patológica (ROE ≫ Ke ⇒ P/B justo > 6)
    DEGRADA o veredito para VERIFICAR e `analisar_acao` NÃO levanta (never-raise). O guard pega
    patologia de MODELO (spread/razão), não bug de dado."""
    cfg = _cfg()
    # ROE constante altíssimo: o excesso ROE−Ke explode o P/B justo implícito acima de 6.
    c = _financeira_sadia(roe_alvo=0.80)
    a = report.analisar_acao(c, cfg)   # NÃO deve levantar
    assert a.razao_patologica is True
    assert a.pb_justo is not None and a.pb_justo > 6.0
    assert a.veredito.startswith("VERIFICAR"), a.veredito
    # a patologia é surfaçada honestamente nos alertas (nunca some em silêncio).
    assert any("patológica" in al.lower() for al in a.alertas)

