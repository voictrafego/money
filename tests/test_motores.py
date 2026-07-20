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


def test_seguradora_como_financeira_da_intrinseco_finito_positivo():
    """REWRITE (WR-04, Fase 13/ENG-01): sob o RIM ÚNICO a rota própria de seguradora MORREU — a
    seguradora capital-light é classificada FINANCEIRA e roda o MESMO `motores.rim` que os bancos
    (`motor == "rim"`, sem chave `seguradora`). O invariante ESTRUTURAL que o aviso Fase-7 exige
    SOBREVIVE (não é morto em silêncio): o intrínseco é FINITO e > 0 — o ROE alto da franquia
    compensa o book pequeno (VPA≈5,35) que preocupava; o RIM não a subvaloriza a None/absurdo.
    Sem cravar nível em reais (BLIND-04a); só finitude/positividade estrutural.
    """
    por_ticker, cfg = _cesta_congelada()
    c = por_ticker["BBSE3"]
    a = report.analisar_acao(c, cfg)

    # RIM único: nenhuma rota própria — a seguradora é uma FINANCEIRA como qualquer banco.
    assert a.motor == "rim"
    # finitude/positividade estrutural: o RIM não explode nem devolve None/absurdo para a franquia
    # capital-light — sem cravar nenhum nível em reais.
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
