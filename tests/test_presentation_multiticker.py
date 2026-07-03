"""Golden OFFLINE de PROPRIEDADE multi-ticker da camada de APRESENTAÇÃO (layer a da
trava TEST-08 / D-08) — o fix de apresentação vale para QUALQUER ticker, não tuna a um.

Diferente do golden de valuation (`test_payout_sustentavel_multiticker.py`, que trava a
ENGINE), aqui a propriedade travada é da APRESENTAÇÃO: dado o `a.multiplos` REAL que a
engine já expõe (read-only), os helpers puros de `analista.report.presentation` formatam e
montam as linhas/headers do jeito certo —

- "DY rec." sai como % (fix DYR-02), nunca a forma decimal de `fmt_num`;
- o payout CRU do último ano e o payout sustentável p/ valuation viram DUAS linhas
  DISTINTAS (fix PAY-02), não o mesmo número clampado;
- o header de DY elege o recorrente como principal e o trailing como delta neutro,
  caindo para o trailing (fallback) quando o recorrente é indisponível (ano sem lucro).

Importa `from analista.report import presentation` e `from analista.report import report` —
NUNCA importa do módulo `app` do Streamlit (D-09: os helpers existem JUSTAMENTE para serem
testáveis sem subir o Streamlit). Cada perfil é um `CompanyData` sintético calibrado ao espírito de um dos
5 tickers da metodologia; cada assert trava uma PROPRIEDADE do método (não um número de
mercado). Usa o config.yaml shipado (determinístico, offline) para `report.analisar_acao`.
"""

import os

import yaml

from analista.core.fundamentals import CompanyData
from analista.report import presentation
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
    dpa_trailing: float | None = None,
    beta: float = 0.90,
) -> CompanyData:
    """Construtor sintético OFFLINE (mesma forma de `test_payout_sustentavel_multiticker`):
    séries por ano consistentes (PL/nº de ações) para o report rodar. `payout(ano) = div/lucro`.
    Use `dpa_trailing` para simular o trailing inflado (proventos extraordinários, EGIE3 spirit)."""
    anos = list(range(2015, 2015 + len(lucros)))
    c = CompanyData(ticker=ticker, nome=f"{ticker} (sintética)", setor="Teste", anos=anos)
    for i, a in enumerate(anos):
        c.lucro_liquido[a] = lucros[i]
        c.patrimonio_liquido[a] = pl
        c.dividendos[a] = divs[i]
        c.num_acoes[a] = num_acoes
        c.vendas_liquidas[a] = (lucros[i] or 0) * 4 or 100
        c.fco[a] = (lucros[i] or 0) * 1.2
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = preco
    if dpa_trailing is not None:
        c.dpa_trailing_12m = dpa_trailing
    c.beta = beta
    return c


def _linha(rows: list, rotulo: str) -> str:
    """Valor formatado da linha de rótulo exato (KeyError implícito se ausente)."""
    return next(v for k, v in rows if k == rotulo)


# --------------------------------------------------------------------------- #
# PERFIL VULC3 — recorrente ~0.43 em 9 anos + 1 ano extraordinário (payout cru >1.0).
# Trava PAY-02 (dois payouts distintos) + DYR-02 ("DY rec." como %).
# --------------------------------------------------------------------------- #
def test_vulc3_payout_cru_distinto_do_sustentavel_e_dy_rec_como_pct():
    c = _mk("VULC3", lucros=[1000] * 10, divs=[430] * 9 + [1200])
    a = report.analisar_acao(c, _cfg())

    payout_ult = c.payout(c.ultimo_ano())   # CRU do último ano (fronteira report.py L156)
    payout_proj = c.payout_valuation()       # sustentável (mediana série completa)
    rows = presentation.linhas_multiplos(a.multiplos, payout_ult, payout_proj)

    linha_cru = _linha(rows, "Payout (último ano)")
    linha_sust = _linha(rows, "Payout p/ valuation (sustentável)")
    # pelo método (PAY-02/D-05/D-06): o payout CRU do último ano (>100%, ano extraordinário)
    # NÃO colapsa no sustentável (mediana ≈0.43) — as duas linhas são strings DISTINTAS.
    assert linha_cru != linha_sust
    assert payout_ult > 1.0 and payout_proj < 1.0  # cru inflado vs. regime recorrente

    linha_dy_rec = _linha(rows, "DY rec.")
    # pelo método (DYR-02/D-07): "DY rec." é uma TAXA → formatada como % (termina em "%"),
    # nunca a forma decimal "0.04" que o default fmt_num produziria (bug atual do app).
    assert linha_dy_rec.endswith("%")
    assert linha_dy_rec == presentation.fmt_pct(a.multiplos["DY rec."])


# --------------------------------------------------------------------------- #
# PERFIL NORMAL ESTÁVEL — EGIE3/ITUB4/BBAS3 spirit (payout estável, trailing inflado).
# Trava HIER-01: recorrente é o principal; trailing entra como delta neutro.
# --------------------------------------------------------------------------- #
def test_normal_estavel_header_elege_recorrente_como_principal():
    # payout estável 0.49; trailing inflado por proventos extraordinários (dpa_trailing alto).
    c = _mk("EGIE3", lucros=[1000] * 10, divs=[490] * 10, dpa_trailing=1.0)
    a = report.analisar_acao(c, _cfg())

    h = presentation.header_dy(a.multiplos["DY rec."], a.multiplos["DY"])
    # pelo método (HIER-01/D-01,D-02): o recorrente (sustentável) é o VALOR PRINCIPAL —
    # não há fallback, e o trailing fica como delta NEUTRO (cinza), não direção.
    assert h["fallback"] is False
    assert h["label"] == "Dividend Yield (recorrente)"
    assert h["value"] == presentation.fmt_pct(a.multiplos["DY rec."])
    assert h["delta_color"] == "off"
    assert h["delta"] == "trailing " + presentation.fmt_pct(a.multiplos["DY"])
    # pelo método (FIX-06 item J): sob trailing inflado, a leitura recorrente é a sustentável
    # ⇒ DY recorrente <= DY trailing (ticker normal não regride no header).
    assert a.multiplos["DY rec."] <= a.multiplos["DY"]


# --------------------------------------------------------------------------- #
# PERFIL TAEE11 — payout >100% recorrente (transmissora). O sustentável é preservado
# >1.0 na linha "p/ valuation" e continua formatado como %.
# --------------------------------------------------------------------------- #
def test_taee11_payout_sustentavel_acima_100_preservado_e_formatado_como_pct():
    c = _mk("TAEE11", lucros=[1000] * 10, divs=[2100] * 10)
    a = report.analisar_acao(c, _cfg())

    payout_proj = c.payout_valuation()
    rows = presentation.linhas_multiplos(a.multiplos, c.payout(c.ultimo_ano()), payout_proj)

    linha_sust = _linha(rows, "Payout p/ valuation (sustentável)")
    # pelo método (D-03): a mediana legítima >100% NÃO é rebaixada na apresentação — a
    # linha p/ valuation reflete o sustentável >1.0 e continua formatada como % (termina em "%").
    assert payout_proj > 1.0
    assert linha_sust == presentation.fmt_pct(payout_proj)
    assert linha_sust.endswith("%")


# --------------------------------------------------------------------------- #
# FALLBACK — ano sem lucro na janela ⇒ lucro normalizado / payout sustentável indefinido
# ⇒ dy_recorrente() None. O header cai para o DY trailing como principal.
# --------------------------------------------------------------------------- #
def test_fallback_sem_lucro_header_cai_para_trailing():
    # série sem lucro distribuível (lucro nulo/indefinido) ⇒ payout sustentável indefinido.
    c = _mk("LOSS3", lucros=[0] * 10, divs=[0] * 10, dpa_trailing=1.0)
    dy_rec = c.dy_recorrente()
    dy_trailing = c.dy_atual()
    # pelo método: payout sustentável indefinido ⇒ dy_recorrente() None (fronteira da engine).
    assert dy_rec is None
    assert dy_trailing is not None

    h = presentation.header_dy(dy_rec, dy_trailing)
    # pelo método (HIER-01/D-03): sem recorrente, o trailing vira o PRINCIPAL com label
    # explícito e sem delta — o usuário sabe que está vendo o trailing, não o sustentável.
    assert h["fallback"] is True
    assert h["label"] == "Dividend Yield (trailing)"
    assert h["value"] == presentation.fmt_pct(dy_trailing)
    assert h["delta"] is None
    assert h["delta_color"] == "off"


# --------------------------------------------------------------------------- #
# SELO (Fase 20 / SELO-03) — formatação PURA do selo, render único p/ os 3 sítios
# (Analisar + Garimpo + Ranking). Trava a copy descritiva (gate "exibe, nunca
# recomenda") e a convenção do em-dash "—" (GRAF-03) para ausências.
# --------------------------------------------------------------------------- #
def test_selo_emoji_mapa_fixo_das_quatro_cores_e_ausencia():
    # pelo contrato (SELO-03): mapa fixo cor→emoji, idêntico nos três sítios da UI.
    assert presentation.selo_emoji("verde") == "🟢"
    assert presentation.selo_emoji("azul") == "🔵"
    assert presentation.selo_emoji("amarelo") == "🟡"
    assert presentation.selo_emoji("vermelho") == "🔴"
    # ausência / cor desconhecida degrada para o sentinela em-dash (GRAF-03).
    assert presentation.selo_emoji(None) == "—"
    assert presentation.selo_emoji("roxo") == "—"


def test_selo_badge_verde_joia_traz_emoji_e_rotulo():
    b = presentation.selo_badge("verde", "JOIA", "Alta", False)
    # começa com o emoji da cor e exibe o rótulo do quadrante (qualidade×preço).
    assert b.startswith("🟢")
    assert "JOIA" in b


def test_selo_badge_verificar_alerta_e_sem_rotulo_de_preco():
    v = presentation.selo_badge("verde", None, "Alta", True)
    # VERIFICAR é overlay (D2): mostra "Verificar dados", nunca um rótulo de preço.
    assert "Verificar" in v
    assert "Barato" not in v and "Justo" not in v and "Caro" not in v


def test_selo_badge_cor_none_degrada_para_em_dash():
    assert presentation.selo_badge(None, None, None, False) == "—"


def test_selo_badge_nunca_e_imperativo():
    # gate regulatório: o selo EXIBE, nunca ordena. Nenhuma saída contém verbo de ordem.
    import re
    saidas = [
        presentation.selo_badge("verde", "JOIA", "Alta", False),
        presentation.selo_badge("azul", "Boa, no preço", "Alta", False),
        presentation.selo_badge("amarelo", "VALUE TRAP", "Baixa", False),
        presentation.selo_badge("vermelho", "Evitar", "Baixa", False),
        presentation.selo_badge("verde", None, "Alta", True),
        presentation.selo_badge(None, None, None, False),
    ]
    for s in saidas:
        assert not re.search(r"compr[ae]|vend[ae]|recomend", s, re.IGNORECASE)
