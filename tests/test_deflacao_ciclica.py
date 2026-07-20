"""PRIM-04 — o motor CÍCLICO consome a série de lucro deflacionada a reais do último ano.

A política CÍCLICA do RIM único (`_roe0_ciclico`, consumida por `_valor_rim`) somava reais
NOMINAIS de anos diferentes (reais de 2015 com 2024) antes da média through-cycle —
subvalorizando cíclicas só por nominalidade. Agora deflaciona `c.serie("lucro_liquido")` pelos
deflatores JÁ CARIMBADOS em `cfg["macro"]["ipca_deflatores"]` (OFFLINE — a engine nunca puxa rede).

Estes testes carimbam os deflatores À MÃO (zero rede) e provam a DIREÇÃO (base deflacionada
> nominal para série inflacionária) e a FRONTEIRA de fallback (deflatores ausentes/vazios →
série nominal, never-raise). O estimador continua `norm.media_ciclo` (média through-cycle),
NÃO o endpoint Theil-Sen — anos_media/winsor do bloco `motores.ciclica` intocados.
"""

import os

import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _empresa_ciclica_inflacionaria():
    """10 anos de lucro POSITIVO crescente (série inflacionária), num_acoes constante."""
    anos = list(range(2014, 2024))
    c = CompanyData(ticker="CICL3", nome="Ciclica SA", setor="Siderurgia", anos=anos)
    for i, ano in enumerate(anos):
        c.lucro_liquido[ano] = 1000.0 + 100.0 * i   # 1000 .. 1900
        c.num_acoes[ano] = 100.0
        c.patrimonio_liquido[ano] = 10000.0
    c.beta = 1.0
    return c, anos


def _analise_com_ke():
    # ENG-01 (Fase 13): o motor cíclico é o RIM ÚNICO com a política do arquétipo CICLICA
    # ("normalizado"): roe0 = LPA normalizado DEFLACIONADO / VPA0. `_valor_rim` lê a.arquetipo.
    a = report.AnaliseAcao(ticker="CICL3", nome="Ciclica SA", setor="Siderurgia",
                           preco_atual=None)
    a.ke = 0.12
    a.arquetipo = "ciclica"
    return a


def _deflatores_inflacao(anos, taxa=0.05):
    """{ano: (1+taxa)**(T-ano)} — reais do último ano T; fator > 1 para anos anteriores."""
    T = anos[-1]
    return {ano: (1.0 + taxa) ** (T - ano) for ano in anos}


def test_base_ciclica_deflacionada_supera_a_nominal():
    c, anos = _empresa_ciclica_inflacionaria()
    cfg = _cfg()

    cfg_defl = {**cfg, "macro": {"ipca_deflatores": _deflatores_inflacao(anos)}}
    cfg_nom = {**cfg, "macro": {"ipca_deflatores": {}}}

    v_defl = report._valor_rim(c, _analise_com_ke(), cfg_defl)
    v_nom = report._valor_rim(c, _analise_com_ke(), cfg_nom)

    assert v_defl is not None and v_nom is not None
    assert v_defl > 0 and v_nom > 0
    # Série inflacionária → a base em reais do último ano é MAIOR que a soma de reais nominais.
    assert v_defl > v_nom


def test_deflatores_com_chaves_string_ainda_deflacionam_nao_no_opam():
    # WR-02 (consumidor report.py): um carimbo cujas chaves chegam como STRING (round-trip
    # YAML) casava ZERO anos (`an in defl` com `an` inteiro) → série vazia → motor cíclico
    # devolve None em SILÊNCIO, embora o ramo `if defl:` fosse tomado. O ramo deve coagir as
    # chaves para int e ainda DEFLACIONAR (não no-opar para nominal/None).
    c, anos = _empresa_ciclica_inflacionaria()
    cfg = _cfg()

    defl_int = _deflatores_inflacao(anos)
    defl_str = {str(ano): fator for ano, fator in defl_int.items()}
    cfg_str = {**cfg, "macro": {"ipca_deflatores": defl_str}}
    cfg_int = {**cfg, "macro": {"ipca_deflatores": defl_int}}
    cfg_nom = {**cfg, "macro": {"ipca_deflatores": {}}}

    v_str = report._valor_rim(c, _analise_com_ke(), cfg_str)
    v_int = report._valor_rim(c, _analise_com_ke(), cfg_int)
    v_nom = report._valor_rim(c, _analise_com_ke(), cfg_nom)

    assert v_str is not None
    # chave-string deflaciona IGUAL à chave-int (não some para série vazia/None)
    assert abs(v_str - v_int) < 1e-9
    # e realmente deflaciona (série inflacionária) — não caiu na série nominal
    assert v_str > v_nom


def test_fallback_nominal_quando_deflatores_ausentes_never_raise():
    c, _ = _empresa_ciclica_inflacionaria()
    cfg = _cfg()

    # Sem bloco macro nenhum: o ramo degrada para a série nominal sem levantar.
    cfg_sem_macro = {k: v for k, v in cfg.items() if k != "macro"}
    v_sem = report._valor_rim(c, _analise_com_ke(), cfg_sem_macro)

    # Deflatores vazios: mesmo caminho nominal.
    cfg_vazio = {**cfg, "macro": {"ipca_deflatores": {}}}
    v_vazio = report._valor_rim(c, _analise_com_ke(), cfg_vazio)

    assert v_sem is not None and v_vazio is not None
    assert v_sem == v_vazio   # ausência ≡ vazio: ambos caem na série nominal
