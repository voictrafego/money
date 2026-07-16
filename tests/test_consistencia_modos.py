"""Trava de consistência cross-modo (TEST-01).

A MESMA `CompanyData` (montada à mão, sem rede) deve produzir ROE/payout/veredito
coerentes entre os três modos do app:

- **Analisar:** `report.analisar_acao(c, cfg)` → `a.multiplos["ROE"]`,
  `a.multiplos["DP (payout)"]`, `a.veredito` (DDM).
- **Ranking:** funções diretas da engine — `c.roe(ult)`, `c.payout_valuation()`,
  `c.payout(ult)` e a regressão `cmp.preco_alvo_por_regressao(...).subavaliada`.

É a rede de segurança que impede uma futura divergência de reintroduzir os bugs
CR-02 / CR-03 / WR-03 fechados na Fase 1. Tudo offline: nenhuma chamada de rede.
"""

import os

import yaml

from analista.core import comparables as cmp
from analista.core import multiples as mult
from analista.core.fundamentals import CompanyData
from analista.report import report

# Raiz do projeto (espelha cli.py:25-32 — yaml.safe_load, SEM @st.cache_data).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cfg() -> dict:
    """Carrega config.yaml da raiz, como o cli.py (sem cache do streamlit)."""
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _empresa_solida(ticker="TAEE11"):
    """Fixture-modelo (espelha tests/test_screening.py:7-26): 10 anos, todos os campos."""
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Empresa Sólida", setor="Energia Elétrica", anos=anos)
    # Fidelidade à ingestão (build.py:68 deriva Energia/Saneamento/Água/Gás): utility regulada
    # → roteia pagadora_regulada → motor ddm (motor_pendente=False), mantendo o veredito DDM.
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


def test_roe_coerente_analisar_vs_ranking():
    """Guard cross-menu (FIX-04 / Core Value): o ROE que o Analisar EXIBE é o MESMO
    método canônico (`roe_valuation`) que o Ranking vivo (app.py/cli.py) consome.

    Compara superfície-viva (`a.multiplos["ROE"]`) contra o método-canônico-vivo do outro
    menu (`c.roe_valuation()`), NÃO contra um número recomputado à mão — assim o teste prova
    consistência entre menus em vez de mascarar uma futura divergência.
    """
    c = _empresa_solida()
    cfg = _cfg()

    a = report.analisar_acao(c, cfg)

    # GUARDA CORE VALUE (intacta): o ROE que o Analisar EXIBE é o MESMO método canônico
    # (roe_valuation) que o Ranking vivo (app.py/cli.py) consome — igualdade EXATA entre menus.
    # É esta igualdade que impede uma divergência de menu (o Core Value); ela NÃO foi tocada.
    assert a.multiplos["ROE"] == c.roe_valuation()
    assert a.multiplos["ROE"] is not None
    # PRIM-01: a base passou do median()-do-meio para o ENDPOINT de tendência robusta. Nesta
    # fixture de crescimento ~linear (+50/ano) o endpoint dos últimos anos COINCIDE com o lucro
    # do último ano, então roe_valuation == roe(ult) — legítimo, não é bug. O antigo assert
    # `!= roe(ult)` era um proxy preso à mediana antiga (que SEMPRE diferia do cru); foi
    # REMOVIDO por invalidez de premissa (autorizado), não afrouxado — a guarda cross-modo é a
    # igualdade acima.


def test_payout_coerente_ultimo_ano_vs_valuation():
    """Payout do Analisar é o canônico ÚNICO (FIX-04), igual ao do Ranking.

    Rebaseline FIX-04: o múltiplo EXIBIDO de payout passa a ser `payout_valuation()`
    (média 3a + clamp 1.0) — o MESMO número que o Ranking (app.py/cli.py) consome na
    regressão (Core Value). O payout CRU por ano (`c.payout(ano)`) não some: continua na
    tabela "Fundamentos (por ano)" do relatório, que é a sua superfície de exibição.
    """
    c = _empresa_solida()
    cfg = _cfg()
    ult = c.ultimo_ano()

    a = report.analisar_acao(c, cfg)

    # Display de payout == canônico de valuation (mesma função no Analisar e no Ranking).
    assert a.multiplos["DP (payout)"] == c.payout_valuation()

    # E o cru por ano segue existindo na engine, intacto, para a tabela por ano.
    assert c.payout(ult) is not None
    # Nesta fixture payout é estável (0,6 em todos os anos), então cru e canônico coincidem;
    # o ponto do guard é que AMBOS os menus leem `payout_valuation`, não que difiram.
    assert a.multiplos["DP (payout)"] == c.payout_valuation()


def _empresa_param(ticker, *, preco, lucro, pl, div, num_acoes=1000):
    """CompanyData de 10 anos parametrizada para montar a amostra da regressão.

    Mantém séries constantes (sem crescimento) para um ROE/payout estáveis e simples
    de calibrar. `preco` define o P/L corrente; `lucro`/`pl`/`div` definem ROE e payout.
    """
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome=ticker, setor="Energia Elétrica", anos=anos)
    # Fidelidade à ingestão: utility regulada → pagadora_regulada → motor ddm (não pendente).
    c.eh_concessionaria = True
    for a in anos:
        c.lucro_liquido[a] = lucro
        c.patrimonio_liquido[a] = pl
        c.dividendos[a] = div
        c.num_acoes[a] = num_acoes
        c.vendas_liquidas[a] = lucro * 5
        c.fco[a] = lucro * 1.2
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = preco
    c.volume_financeiro_diario = 40_000_000
    c.desempenho_relativo_6m = 0.10
    c.beta = 0.8
    return c


def _empresa_param_crescente(ticker, *, preco, lucro_inicial, g, pl, payout, num_acoes=1000):
    """Como _empresa_param, mas com lucro/dividendos CRESCENTES à taxa `g` (payout fixo).

    Rebaseline FIX-03: com o Ke local (~15% com Selic ao vivo + beta), uma série CONSTANTE
    (g_alto=0) cola o intrínseco do DDM no limiar de DY>15% — não há janela robusta de
    "barata sem disparar o flag DDM-FIX-05". Uma empresa que CRESCE (CAGR>0 ⇒ g_alto>0) faz
    o intrínseco subir bem acima do piso de DY, recuperando uma alvo claramente SUBAVALIADA.
    """
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome=ticker, setor="Energia Elétrica", anos=anos)
    # Fidelidade à ingestão: utility regulada → pagadora_regulada → motor ddm (não pendente).
    # AAA3 tem retenção alta (payout 0.35) e roteava "crescimento" (motor pendente) sem este
    # flag — a suspensão D-04 quebraria o veredito SUBAVALIADA que este golden trava.
    c.eh_concessionaria = True
    for i, a in enumerate(anos):
        lucro = round(lucro_inicial * (1 + g) ** i)
        c.lucro_liquido[a] = lucro
        c.patrimonio_liquido[a] = pl
        c.dividendos[a] = round(payout * lucro)
        c.num_acoes[a] = num_acoes
        c.vendas_liquidas[a] = lucro * 5
        c.fco[a] = lucro * 1.2
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = preco
    c.volume_financeiro_diario = 40_000_000
    c.desempenho_relativo_6m = 0.10
    c.beta = 0.8
    return c


def test_veredito_direcao_coerente():
    """Direção (subavaliada/cara) coerente entre DDM (Analisar) e regressão (Ranking).

    Monta ≥4 CompanyData determinísticas (tickers distintos) calibradas para que:
      - a regressão P/L = f(DP, ROE) ajuste (n≥4, comparables.py:94) — NÃO pode ser None;
      - a empresa-alvo seja claramente BARATA: preço bem abaixo do valor justo, ROE alto
        e payout saudável, com os comparáveis em P/L mais alto (puxando o P/L "justo" da
        alvo para cima).
    Afirma a DIREÇÃO (sinal), não igualdade numérica (DDM ≠ regressão por construção).
    A asserção é obrigatória e nunca opcional: se o sinal não estabilizar, recalibram-se
    os números das fixtures (preços/lucros/dividendos/PL) — nunca se relaxa o assert.
    """
    cfg = _cfg()

    # Empresa-alvo claramente barata e que CRESCE (~14%/ano): preço (5,50) abaixo TANTO do
    # valor intrínseco do DDM (vmin≈8,10 pós-PRIM-01 — o endpoint elevou a base/LPA) quanto do
    # preço-alvo da regressão (~7,20). Rebaseline FIX-03 (ver _empresa_param_crescente): com o
    # Ke local ~15% a alvo precisa crescer p/ o DDM render um intrínseco bem acima do preço SEM
    # disparar o flag DY>15% (DY≈12,4% < 15%).
    alvo = _empresa_param_crescente("AAA3", preco=5.5, lucro_inicial=600, g=0.14, pl=5000, payout=0.35)
    # Comparáveis EXPENSIVOS (P/L ~42-48) e comparáveis DE VERDADE: ROE ~0,23 (bracketando o da
    # alvo) e payout ~0,35 (próximo do da alvo). Puxam o P/L justo para cima, deixando a alvo
    # (P/L corrente ~2,84, bem mais barata) acima do preço na regressão.
    # RECALIBRAÇÃO PRIM-02 (doutrina deste teste: "recalibram-se os NÚMEROS das fixtures, nunca
    # se relaxa o assert"): o `roe_valuation` da alvo passou do ENDPOINT (~0,39) para a MEDIANA
    # through-cycle dos roe(a) (~0,231, o meio da subida de 14%/ano). Os comparáveis, portanto,
    # voltaram de ROE ~0,34 para ROE ~0,23 — bracketando a mediana da alvo, um conjunto comparável
    # honesto ao novo nível. A DIREÇÃO volta a bater nos dois menus (barata na regressão E
    # SUBAVALIADA no DDM), SEM afrouxar nenhum assert.
    comp_b = _empresa_param("BBB3", preco=42.0, lucro=920, pl=4000, div=322)
    comp_c = _empresa_param("CCC3", preco=43.0, lucro=900, pl=4000, div=324)
    comp_d = _empresa_param("DDD3", preco=40.0, lucro=960, pl=4000, div=326)
    empresas = [alvo, comp_b, comp_c, comp_d]

    # Vetores PL/DP/ROE como no modo Ranking VIVO (app.py/cli.py pós-FIX-04): tudo via
    # métodos canônicos normalizados — o que se garante aqui é que o guard usa exatamente os
    # métodos que o Ranking consome. Os comparáveis seguem CONSTANTES (P/L corrente alto, p/
    # puxar o P/L justo p/ cima); a alvo agora CRESCE (FIX-03).
    # Rebaseline FIX-03 (Ke local ~15%): a alvo passou de série constante (g_alto=0, vmin≈6,79
    # com o Ke antigo de 9,4%) para uma empresa que cresce ~14%/ano. Com o Ke local mais alto,
    # uma série constante derruba o intrínseco p/ ~3,4 e qualquer preço abaixo disso dispara o
    # flag DY>15% (vira "VERIFICAR", não "SUBAVALIADA"). A alvo crescente recupera vmin≈6,75 >
    # preço 5,50 com DY≈12,4% < 15% — a DIREÇÃO SUBAVALIADA volta a valer com folga, sem
    # afrouxar nenhum assert.
    PL, DP, ROE = [], [], []
    for c in empresas:
        PL.append(mult.preco_lucro(c.preco_atual, c.lpa_valuation()))
        DP.append(c.payout_valuation())
        ROE.append(c.roe_valuation())

    reg = cmp.ajustar_regressao_pl(PL, DP, ROE)
    # Com 4 fixtures completas a regressão NÃO pode falhar (n≥4). Se vier None é bug do teste.
    assert reg is not None, "regressão None com 4 fixtures — calibrar PL/DP/ROE"
    assert reg.n >= 4

    # Preço-alvo da empresa-alvo pelo Ranking (regressão) — métodos canônicos vivos.
    pa = cmp.preco_alvo_por_regressao(
        reg, alvo.payout_valuation(), alvo.roe_valuation(), alvo.lpa_valuation(), alvo.preco_atual
    )
    assert pa is not None, "PrecoAlvo None — todos os campos da alvo estão presentes"

    # Veredito da MESMA empresa pelo Analisar (DDM).
    a = report.analisar_acao(alvo, cfg)
    assert a.veredito, "veredito vazio — DDM não rodou (checar beta/ke/payout)"

    # Coerência de DIREÇÃO (sinal), não de valor: barato no DDM <=> barato na regressão.
    assert a.veredito.startswith("SUBAVALIADA") == pa.subavaliada
    # Ancorar o teste num sinal determinístico conhecido: a alvo foi calibrada como barata.
    assert pa.subavaliada is True
    assert a.veredito.startswith("SUBAVALIADA")
