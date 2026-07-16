"""Golden OFFLINE de PROPRIEDADE multi-ticker do estimador robusto (g log-linear) +
de-poison do screening — trava de aceite do marco (Fase 10, success criteria a/b/c):
o de-poison vale para QUALQUER ticker por regra geral; VULC3 é só o diagnóstico.

Espelha test_payout_sustentavel_multiticker.py: nenhum dado real (que exigiria rede);
cada perfil é um `CompanyData` sintético calibrado ao espírito de um dos 5 tickers da
metodologia e cada assert trava uma PROPRIEDADE do método (desigualdade/igualdade
estrutural), não um número de mercado. A confirmação contra os números REAIS dos 5
tickers (VULC3/ITUB4/EGIE3/TAEE11/BBAS3) é o checkpoint human-verify da Task 3 deste plano.

Propriedades travadas (1 comentário "pelo método" por assert):
- (a) VULC3 — recorrente + 1 ano extraordinário na ponta: g_historico (log-linear sobre a
      série normalizada) NÃO é inflado pelo spike — fica abaixo do CAGR endpoint-a-endpoint
      do mesmo par (D-01); idem para o fator crescimento_lucro_3a do BSD.
- (D-04) consistência por construção: indicadores_bsd(c)["crescimento_lucro_3a"] ==
      report.analisar_acao(c,cfg).g_historico (fonte única Analisar↔Screening).
- (b) NORMAIS (ITUB4/EGIE3/TAEE11/BBAS3 spirit) — trajetória estável e crescente: g_historico
      finito, sinal coerente (crescente ⇒ > 0) e os fatores crescimento_*_3a do BSD finitos,
      sem colapso do ranqueamento.
- (c) TAEE11 — payout ≈ 2.16 recorrente: ajustar_regressao_pl produz os MESMOS coeficientes
      que com essa linha clampada em 1.0 (o fit não "vê" >1.0 — de-poison D-06) e o preço-alvo
      resultante é finito/sensato.

Usa o config.yaml shipado (determinístico, offline) para report.analisar_acao.
"""

import os

import numpy as np
import yaml

from analista.core import comparables, growth, normalizacao
from analista.core import screening
from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _mk(
    ticker: str,
    lucros: list,
    divs: list,
    *,
    preco: float = 10.0,
    num_acoes: float = 1000.0,
    pl: float = 8000.0,
    beta: float = 0.90,
) -> CompanyData:
    """Construtor sintético OFFLINE (mesma forma de test_payout_sustentavel_multiticker._mk):
    séries por ano consistentes (PL/nº de ações/juros/intangível) para report.analisar_acao e
    screening.indicadores_bsd rodarem. `payout(ano) = div/lucro`."""
    anos = list(range(2015, 2015 + len(lucros)))
    c = CompanyData(ticker=ticker, nome=f"{ticker} (sintética)", setor="Teste", anos=anos)
    for i, a in enumerate(anos):
        c.lucro_liquido[a] = lucros[i]
        c.patrimonio_liquido[a] = pl
        c.dividendos[a] = divs[i]
        c.num_acoes[a] = num_acoes
        c.vendas_liquidas[a] = lucros[i] * 4
        c.fco[a] = lucros[i] * 1.2
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = preco
    c.beta = beta
    return c


# --------------------------------------------------------------------------- #
# (a) PERFIL VULC3 — lucro recorrente ~1000/ano (9 anos) + 1 ano extraordinário 4000.
# O spike NÃO pode inflar o g exibido nem o fator de crescimento do BSD.
# --------------------------------------------------------------------------- #
def test_perfil_vulc3_spike_extraordinario_nao_infla_g_nem_bsd():
    raw = [1000] * 9 + [4000]          # recorrente + 1 exercício atípico na ponta
    c = _mk("VULC3", lucros=raw, divs=[430] * 10)

    a = report.analisar_acao(c, _cfg())
    assert a.g_historico is not None

    cagr_raw_endpoint = growth.cagr(raw[0], raw[-1], len(raw) - 1)
    assert cagr_raw_endpoint is not None
    # PRIM-03/D-04: a winsorização temporal do lucro SAIU (série crua até a Fase 11 — o desenho
    # do g robusto é de lá). O que ainda impede o spike na ponta de mandar no g é o ESTIMADOR
    # log-linear: usa TODOS os 10 pontos (9 recorrentes + 1 atípico), então fica MUITO abaixo do
    # CAGR endpoint-a-endpoint da série CRUA — o estimador naïve que só vê base e ponta e que o
    # spike inflaria. A de-poison do estimador é material, não cosmética.
    assert a.g_historico < cagr_raw_endpoint

    ind = screening.indicadores_bsd(c)
    # pelo método (D-04): o fator de crescimento do BSD é a MESMA fonte ⇒ também não inflado.
    assert ind["crescimento_lucro_3a"] is not None
    assert ind["crescimento_lucro_3a"] < cagr_raw_endpoint
    # Core Value (D-04): Screening == Analisar por construção — ambos consomem a MESMA
    # serie_lucro_normalizada crua (PRIM-03), não mais só coincidentemente a winsorizada.
    assert ind["crescimento_lucro_3a"] == a.g_historico


# --------------------------------------------------------------------------- #
# (D-04) Consistência explícita Screening ↔ Analisar num perfil normal crescente.
# --------------------------------------------------------------------------- #
def test_consistencia_crescimento_lucro_3a_igual_g_historico():
    grow = [round(1000 * (1.08 ** i)) for i in range(10)]   # ~+8%/ano estável
    c = _mk("ITUB4", lucros=grow, divs=[round(0.4 * x) for x in grow])

    a = report.analisar_acao(c, _cfg())
    ind = screening.indicadores_bsd(c)
    assert a.g_historico is not None and ind["crescimento_lucro_3a"] is not None
    # pelo método (D-04): mesma série normalizada + mesmo estimador log-linear ⇒ igualdade
    # estrutural exata (não "aproximada"): a empresa não ranqueia diferente do que o Analisar mostra.
    assert ind["crescimento_lucro_3a"] == a.g_historico


# --------------------------------------------------------------------------- #
# (b) PERFIS NORMAIS (ITUB4/EGIE3/TAEE11/BBAS3 spirit) — crescimento plausível e estável.
# g e BSD não regridem/colapsam.
# --------------------------------------------------------------------------- #
def test_perfis_normais_g_finito_coerente_e_bsd_nao_colapsa():
    cfg = _cfg()
    grow = [round(1000 * (1.07 ** i)) for i in range(10)]   # trajetória crescente coerente
    divs = [round(0.45 * x) for x in grow]
    c = _mk("EGIE3", lucros=grow, divs=divs)

    a = report.analisar_acao(c, cfg)
    # pelo método: série crescente ⇒ g_historico finito e POSITIVO (sinal coerente com a
    # trajetória); o estimador robusto não "engole" o crescimento real de um normal.
    assert a.g_historico is not None and a.g_historico > 0

    ind = screening.indicadores_bsd(c)
    # pelo método: os 3 fatores crescimento_*_3a do BSD são finitos (não None/NaN) ⇒ o
    # ranqueamento não colapsa por falta de fator.
    for k in ("crescimento_lucro_3a", "crescimento_dividendos_3a", "crescimento_fc_3a"):
        assert ind[k] is not None
        assert np.isfinite(ind[k])
    # pelo método: lucro e dividendos crescem ⇒ ambos os fatores POSITIVOS (dividendo crescente
    # é núcleo do método; um normal não regride para fator negativo aqui).
    assert ind["crescimento_lucro_3a"] > 0
    assert ind["crescimento_dividendos_3a"] > 0


# --------------------------------------------------------------------------- #
# (c) PERFIL TAEE11 — payout ≈ 2.16 recorrente na regressão de preço-alvo.
# O fit NÃO pode "ver" >1.0 (de-poison D-06).
# --------------------------------------------------------------------------- #
def test_perfil_taee11_fit_payout_2_16_igual_clampado_em_1():
    pl = [10.0, 12.0, 8.0, 11.0, 9.0]
    roe = [0.20, 0.25, 0.15, 0.22, 0.18]
    dp_taee = [0.40, 0.50, 0.30, 0.45, 2.16]   # uma linha com payout ≈ 2.16 (TAEE11)
    dp_clamp = [0.40, 0.50, 0.30, 0.45, 1.00]  # mesma linha já clampada em 1.0

    reg_taee = comparables.ajustar_regressao_pl(pl, dp_taee, roe)
    reg_clamp = comparables.ajustar_regressao_pl(pl, dp_clamp, roe)
    assert reg_taee is not None and reg_clamp is not None
    # pelo método (D-06): o clamp [0,1] vive na ENTRADA do fit ⇒ payout 2.16 produz os MESMOS
    # coeficientes que 1.0; o payout legítimo >100% deixa de envenenar b1.
    assert np.allclose(reg_taee.coeficientes, reg_clamp.coeficientes)


def test_perfil_taee11_preco_alvo_finito_e_sensato_apos_clamp():
    pl = [10.0, 12.0, 8.0, 11.0, 9.0]
    roe = [0.20, 0.25, 0.15, 0.22, 0.18]
    dp = [0.40, 0.50, 0.30, 0.45, 2.16]
    reg = comparables.ajustar_regressao_pl(pl, dp, roe)
    assert reg is not None

    alvo = comparables.preco_alvo_por_regressao(reg, dp=2.16, roe=0.18, lpa=2.0, preco_corrente=20.0)
    assert alvo is not None
    # pelo método (D-06): o preço-alvo de quem paga >100% sai finito e positivo (não NaN/inf
    # nem distorcido por um b1 envenenado) — o clamp da entrada do fit cobre cli e app.
    assert np.isfinite(alvo.preco_alvo) and alvo.preco_alvo > 0
    # pelo método (D-06): a flag sinaliza que o payout de entrada caiu fora de [0,1] (foi clampado).
    assert alvo.payout_fora_faixa is True
