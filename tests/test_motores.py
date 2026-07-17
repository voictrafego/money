"""Golden puro por motor de valuation por arquétipo (v2.2 Fase 2; v2.3 Fase 4 — ENG-02..05).

Offline/síncrono (padrão do repo): inputs fixos de livro + tolerância absoluta. Um golden por
motor. O crítico é o RIM (ENG-02 / CAL-01): RIM híbrido com valor terminal (perpetuidade de
Gordon sobre o RI terminal). Com inputs tipo-ITUB4 devolve ~R$32,9 (live VPA~19, ke~13%) /
~R$39,2 (golden VPA~22, ke~12,5%), terminal ≈17% do valor — materialmente acima do DDM ao vivo
(~R$16), destravando o ITUB4 do "evitar". O Ke que alimenta o RIM é o Ke ÚNICO do sistema
(`a.ke`, β setorial+Blume — KE-01/Fase 12); a alavanca principal é o valor terminal.
"""

import math
import os

import yaml

from analista.backtest import carregar_snapshot
from analista.core import arquetipo, motores
from analista.core import normalizacao as norm
from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------------------------------------------------------- #
# RIM (ENG-02 / CAL-01) — o crítico: destrava o ITUB4 com valor terminal
# --------------------------------------------------------------------------- #
def test_rim_terminal_normalizado():
    # Alavanca 2 (CAL-01/D-01): normalização through-cycle do ROE ENTRA SÓ no RI terminal.
    # Prova as duas metades da tese: (a) roe_terminal abaixo do cap MOVE o valor; (b) roe_terminal
    # acima do cap SATURA no excesso_sustentavel → bit-idêntico ao legado (protege o ITUB4).
    base = dict(
        vpa0=19.0, roe0=0.193, ke=0.13, retencao=0.533, n=10,
        excesso_sustentavel=0.045, g_terminal=0.025,
    )
    legado = motores.rim(**base)  # roe_terminal ausente → comportamento D-02/it.1
    assert legado is not None
    assert legado.vp_terminal > 0

    # (a) excesso terminal (roe_ciclo − ke = 0,02) MENOR que o cap (0,045) → o terminal encolhe,
    #     logo o valor_intrinseco DIFERE (e é menor) do legado — a alavanca move o número.
    abaixo = motores.rim(**base, roe_terminal=0.15)
    assert abaixo is not None
    assert abaixo.valor_intrinseco != legado.valor_intrinseco
    assert abaixo.valor_intrinseco < legado.valor_intrinseco
    assert abaixo.vp_terminal < legado.vp_terminal
    # A janela explícita fica INTOCADA (Pitfall 1): só o terminal muda.
    assert abs(abaixo.vp_residual_income - legado.vp_residual_income) < 1e-12

    # (b) excesso terminal (0,07) MAIOR que o cap (0,045) → min(...) satura no cap → o RI terminal
    #     é idêntico ao legado (que também satura) → valor_intrinseco bit-idêntico (não regride).
    acima = motores.rim(**base, roe_terminal=0.20)
    assert acima is not None
    assert abs(acima.valor_intrinseco - legado.valor_intrinseco) < 1e-9
    assert abs(acima.vp_terminal - legado.vp_terminal) < 1e-9


def test_rim_bad_bank_abaixo_do_book():
    # Guarda anti-bad-bank: banco que destrói valor (ROE < Ke) valua ABAIXO do book (P/B < 1).
    # fade_para = ke + min(roe0−ke, cap) SEM clampar a ≥ ke → RI terminal negativo → V < VPA.
    res = motores.rim(
        vpa0=22.0, roe0=0.10, ke=0.125, retencao=0.53, n=10,
        excesso_sustentavel=0.045, g_terminal=0.025,
    )
    assert res is not None
    assert res.valor_intrinseco < 22.0
    assert res.vp_terminal <= 0


def test_rim_roe_igual_ke_ancora_no_vpa():
    # Sem excesso de ROE em nenhum ano → valor ancorado no VPA.
    res = motores.rim(vpa0=22.0, roe0=0.125, ke=0.125, retencao=0.53, n=10)
    assert res is not None
    assert abs(res.valor_intrinseco - 22.0) < 1e-9


def test_rim_never_raise():
    assert motores.rim(vpa0=None, roe0=0.19, ke=0.125, retencao=0.53, n=10) is None
    assert motores.rim(vpa0=22.0, roe0=0.19, ke=0.0, retencao=0.53, n=10) is None
    assert motores.rim(vpa0=-5.0, roe0=0.19, ke=0.125, retencao=0.53, n=10) is None
    assert motores.rim(vpa0=22.0, roe0=0.19, ke=0.125, retencao=0.53, n=0) is None


# --------------------------------------------------------------------------- #
# Ke ÚNICO (KE-01) — o RIM consome `a.ke`, não recomputa
# --------------------------------------------------------------------------- #
def test_o_ke_que_alimenta_o_rim_e_o_a_ke_unico(monkeypatch):
    """INVARIANTE DA UNIFICAÇÃO (WR-04, KE-01): o Ke que alimenta o RIM É `a.ke` — o Ke ÚNICO
    do CAPM (β setorial+Blume). O antigo Ke estrutural do RIM (função separada, clampada a
    [ke_piso, ke_teto] e teto ke_live) foi DELETADO; o RIM não recomputa mais um Ke próprio.

    O espírito do criério #1 ("o Ke do RIM não excede o Ke ao vivo") fica trivialmente
    verdadeiro porque agora são o MESMO número — relação entre motores, sem depender de NÍVEL.
    Prova por espionagem: roda `analisar_acao` num banco (rota RIM) e assevera que o `ke` passado
    a `motores.rim` é idêntico ao `a.ke` computado/exibido.
    """
    cfg = _cfg()
    capturado = {}
    original_rim = motores.rim

    def _spy(*args, **kwargs):
        capturado["ke"] = kwargs.get("ke")
        return original_rim(*args, **kwargs)

    monkeypatch.setattr(motores, "rim", _spy)

    anos = list(range(2015, 2025))
    c = CompanyData(ticker="BANK4", nome="Banco Sintético", setor="Bancos", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = 1000
        c.patrimonio_liquido[a] = 4000
        c.dividendos[a] = 500
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 5000
        c.fco[a] = 1200
    c.preco_atual = 10.0
    c.beta = 1.0

    a = report.analisar_acao(c, cfg)

    assert a.motor == "rim"           # a rota RIM foi exercitada
    assert capturado.get("ke") is not None
    assert a.ke is not None
    assert capturado["ke"] == a.ke    # o RIM recebe o Ke ÚNICO, não recomputa


# --------------------------------------------------------------------------- #
# Lucro normalizado (ENG-03) — usa média 7–10a, não 1 ano
# --------------------------------------------------------------------------- #
def test_lucro_normalizado_usa_media_e_ignora_pico_vale():
    # Série de LPA oscilante: picos e vales não podem mandar no intrínseco.
    serie = [2.0, 6.0, 1.0, 7.0, 1.5, 8.0, 1.2, 6.5, 1.8, 7.5]
    lpa_mid = norm.base_normalizada(serie, anos_media=10, winsor=0.10)
    # A base normalizada difere materialmente do último ano (7,5).
    assert abs(lpa_mid - serie[-1]) > 0.5
    intr = motores.lucro_normalizado(lpa_mid, ke=0.12, g_estavel=0.025)
    assert intr is not None and intr > 0 and math.isfinite(intr)
    # Gordon puro: intrínseco = lpa_mid / (ke - g).
    assert abs(intr - lpa_mid / (0.12 - 0.025)) < 1e-9


def test_lucro_normalizado_never_raise():
    assert motores.lucro_normalizado(5.0, ke=0.02, g_estavel=0.025) is None  # ke-g<=0
    assert motores.lucro_normalizado(None, ke=0.12, g_estavel=0.025) is None


# --------------------------------------------------------------------------- #
# DCF crescimento (ENG-04) — positivo e finito, modelo-H conservador
# --------------------------------------------------------------------------- #
def test_dcf_crescimento_positivo_finito_e_modelo_h_conservador():
    h = motores.dcf_crescimento(
        lpa_valuation=2.0, g_alto=0.15, g_estavel=0.025, ke=0.14, n=10
    )
    assert h is not None and h > 0 and math.isfinite(h)  # critério #3: não zero/lixo
    const = motores.dcf_crescimento(
        lpa_valuation=2.0, g_alto=0.15, g_estavel=0.025, ke=0.14, n=10, decrescente=False
    )
    # Modelo-H (decrescente) é conservador: <= cenário de crescimento constante.
    assert h < const


def test_dcf_crescimento_never_raise():
    # ke - g_estavel <= 0 → None.
    assert motores.dcf_crescimento(2.0, 0.15, 0.15, 0.10, 10) is None
    assert motores.dcf_crescimento(None, 0.15, 0.025, 0.14, 10) is None


# --------------------------------------------------------------------------- #
# NAV contábil (ENG-05) — piso patrimonial = VPA
# --------------------------------------------------------------------------- #
def test_nav_contabil_igual_vpa():
    assert motores.nav_contabil(5000.0, 1000.0) == 5.0


def test_nav_contabil_never_raise():
    assert motores.nav_contabil(None, 1000.0) is None
    assert motores.nav_contabil(5000.0, 0.0) is None


# --------------------------------------------------------------------------- #
# Rota de seguradora (Alavanca 3 / D-03/D-04) — Gordon-franquia, reuso PURO
# --------------------------------------------------------------------------- #
_SNAPSHOT = os.path.join(ROOT, "tests", "fixtures", "snapshot_bancos_2026-07-12.yaml")


def _cesta_congelada():
    """CompanyData da cesta congelada + cfg com o rf_local carimbado (offline, determinístico)."""
    empresas, rf_local, _ipca_defl = carregar_snapshot(_SNAPSHOT)
    cfg = _cfg()
    cfg = {**cfg, "capm": {**cfg["capm"], "rf_local": rf_local}}
    return {c.ticker: c for c in empresas}, cfg


def test_rota_seguradora_roteia_e_da_intrinseco_finito_positivo():
    """CONTRATO (WR-04): a seguradora capital-light roteia para a rota Gordon-franquia
    (`motor == "seguradora"`) e devolve um intrínseco FINITO e > 0 — nunca o bank-RIM ancorado
    no book minúsculo (VPA≈5,35, que a subvaloriza), nunca None/explosão.

    Extraído do golden de NÍVEL `test_rota_seguradora_bbse3_gordon_franquia` (banda ≈R$39,87),
    DELETADO na Fase 11 (GROW-01): o nível morreu porque a rota passou a usar o `g_cap` derivado
    (~7,28%) no lugar do `cfg["ddm"]["g_estavel"]` (chave removida na Fase 11), encolhendo o
    denominador Gordon `Ke − g` — comportamento INTENCIONAL (D-04). A guarda ESTRUTURAL de
    roteamento + finitude/positividade SOBREVIVE (split-before-delete), sem cravar reais e sem
    ler a chave removida. Auto-consistência: o número bate EXATAMENTE o Gordon-franquia dos
    insumos (dpa_recorrente×(1+g_cap), ke=a.ke, g=g_cap) — reuso PURO de `ddm.valor_gordon`.
    """
    por_ticker, cfg = _cesta_congelada()
    c = por_ticker["BBSE3"]
    a = report.analisar_acao(c, cfg)

    # rótulo honesto: a rota assume a seguradora, não mais 'rim' — o roteamento sobrevive.
    assert a.motor == "seguradora"
    # finitude/positividade estrutural: sob o g_cap derivado (~7,28%) o Gordon de estágio único
    # da seguradora NÃO explode nem devolve None/absurdo — sem cravar nenhum nível em reais.
    assert a.intrinseco_motor is not None
    assert math.isfinite(a.intrinseco_motor) and a.intrinseco_motor > 0


def test_setor_de_banco_nao_casa_o_token_seguradora():
    """INVARIANTE (WR-04): o roteamento de seguradora é ancorado em FRONTEIRA DE PALAVRA — um setor
    de banco NÃO casa o token 'seguradora', logo um banco jamais é desviado para a rota
    Gordon-franquia da seguradora.

    Extraído do golden de nível `test_rota_seguradora_nao_pega_banco` (banda R$30–40), DELETADO na
    Fase 10 (PRIM-05): a banda de nível morreu, a guarda estrutural de roteamento-negativo SOBREVIVE
    (WR-04). Puro: sem engine, sem ticker, sem constante em reais — só a álgebra do casador de token.
    """
    # Negativo: um setor de banco não pode casar o token da seguradora (sem over-match de substring).
    assert not arquetipo._setor_casa_token("bancos", ["seguradora"])
    # Controle positivo: o token casa o próprio setor de seguros (fronteira de palavra + plural).
    assert arquetipo._setor_casa_token("seguradoras", ["seguradora"])
