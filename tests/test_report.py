"""Golden tests do read técnico consultivo da engine (Phase 6):

- TEST-06 / D-02: o desempate canônico do composite — preço ACIMA da MM200 mas com
  ADX < 20 → "sem_tendencia" (o ADX fraco vence o viés de alta da MM200).
- D-10: o resample semanal W-FRI (agregação first/max/min/last) que roda dentro de
  `analisar_acao` antes de calcular os indicadores quando a base é "semanal".

Ambos travam contra os MESMOS limiares do config.yaml shipado (via `_cfg_ind()`), de
modo que o teste e a engine compartilham os limiares de `indicators._forca` (< 20 / > 25).
"""

import copy
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from analista.core.fundamentals import CompanyData
from analista.report import report


def _cfg_ind() -> dict:
    """Carrega o config.yaml shipado para pinar os parâmetros canônicos nos testes."""
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _ohlc_acima_mm200_adx_fraco() -> pd.DataFrame:
    """Série DIÁRIA acima da própria MM200 mas com ADX < 20.

    ~210 pregões de subida lenta (100→120) seguidos de ~80 de deriva lateral estreita
    (oscilação senoidal de amplitude 0,6 em torno de 122). Ao final: o preço fica acima
    da MM200 (que ainda carrega a subida antiga, mais baixa), porém a ausência de direção
    na fase lateral leva o ADX da ponta a ~12 (< 20) → força "sem_tendencia".
    """
    subida = np.linspace(100.0, 120.0, 210)
    n_lat = 80
    t = np.arange(n_lat)
    lateral = 122.0 + 0.6 * np.sin(t * 0.7)
    closes = np.concatenate([subida, lateral])
    idx = pd.date_range("2019-01-01", periods=len(closes), freq="B")
    close = pd.Series(closes, index=idx)
    return pd.DataFrame(
        {
            "Open": close.shift(1).bfill(),
            "High": close + 0.3,
            "Low": close - 0.3,
            "Close": close,
        }
    )


def test_composite_acima_mm200_adx_fraco_eh_sem_tendencia():
    # TEST-06 / D-02: preço ACIMA da MM200 mas ADX < 20 → "sem_tendencia".
    # Crava o caso no timeframe DIÁRIO (base_temporal="diario") para não precisar de
    # ~200 barras SEMANAIS — a árvore composite é a mesma nos dois timeframes; o que se
    # trava aqui é o desempate, não o resample (esse é o test_resample_semanal_w_fri).
    cfg = copy.deepcopy(_cfg_ind())
    cfg["indicadores"]["base_temporal"] = "diario"
    c = CompanyData(ticker="TST", anos=[2023], ohlc_ajustado=_ohlc_acima_mm200_adx_fraco())

    a = report.analisar_acao(c, cfg)

    # Pré-condição do desempate: realmente acima da MM200 e com ADX fraco.
    assert a.sinais.tendencia.posicao_mm200 == "acima"
    assert a.sinais.forca.forca_adx == "sem_tendencia"
    # Veredito do composite: ADX fraco vence o viés de alta da MM200 (D-02).
    assert a.timing_estado == "sem_tendencia"


def test_resample_semanal_w_fri():
    # D-10: o resample W-FRI agrega Open=first, High=max, Low=min, Close=last e carimba
    # o índice na sexta-feira de cada semana. 3 semanas completas (15 pregões, seg→sex)
    # → exatamente 3 barras semanais, todas em sexta (weekday == 4).
    idx = pd.date_range("2019-01-07", periods=15, freq="B")  # 2019-01-07 é segunda-feira
    closes = np.arange(1, 16, dtype=float) * 10.0            # 10, 20, ..., 150 (todos distintos)
    close = pd.Series(closes, index=idx)
    df = pd.DataFrame(
        {
            "Open": close - 1.0,
            "High": close + 2.0,
            "Low": close - 2.0,
            "Close": close,
        }
    )

    sem = df.resample("W-FRI").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    ).dropna()

    # 3 barras semanais, todas carimbadas em sexta-feira.
    assert len(sem) == 3
    assert all(ts.weekday() == 4 for ts in sem.index)

    # Semana 1 (07–11/jan): Close diário 10..50. Open=primeiro dia, High=máx, Low=mín, Close=último.
    s1 = sem.iloc[0]
    assert s1["Open"] == df["Open"].iloc[0]    # primeiro pregão da semana
    assert s1["High"] == df["High"].iloc[0:5].max()
    assert s1["Low"] == df["Low"].iloc[0:5].min()
    assert s1["Close"] == df["Close"].iloc[4]  # último pregão (sexta)


# --------------------------------------------------------------------------- #
# Matriz fundamento×técnico (TIMING-02 / D-04/D-05/D-06)
# --------------------------------------------------------------------------- #
# A matriz é read-only: SÓ lê o token líder do veredito e o estado técnico. Por isso
# os goldens das células-âncora pinam os inputs direto no helper puro `_matriz_leitura`
# (mesma frase que `analisar_acao` grava em `a.matriz_leitura`), sem precisar montar um
# CompanyData inteiro com fundamentos que produzam SUBAVALIADA/SOBREAVALIADA.

def test_matriz_subavaliada_atencao_eh_frase_ancora_d05():
    # D-05 (verbatim): BARATO + ATENÇÃO → "atrativa, mas reverifique antes".
    frase = report._matriz_leitura(
        "SUBAVALIADA — preço R$ 10.00 abaixo do intervalo intrínseco R$ 15.00–20.00",
        "atencao",
    )
    assert frase == (
        "Fundamentalmente descontada, porém o preço perdeu a tendência — "
        "confirme que os fundamentos seguem intactos antes de entrar."
    )


def test_matriz_sobreavaliada_alta_eh_frase_ancora_d06():
    # D-06 (verbatim): CARO + ALTA → "o método não paga caro".
    frase = report._matriz_leitura(
        "SOBREAVALIADA — preço R$ 30.00 acima do intervalo intrínseco R$ 15.00–20.00",
        "tendencia_de_alta",
    )
    assert frase == (
        "Tecnicamente em alta, porém acima do valor intrínseco — "
        "o método não compra caro; aguarde um preço melhor."
    )


def test_matriz_fundamento_lidera_sempre():
    # D-04 / UI-06: o fundamento SEMPRE abre a frase. As células-âncora começam pelo
    # adjetivo fundamentalista ("Fundamentalmente descontada" / "Tecnicamente em alta,
    # porém acima do valor intrínseco" — o veto fundamentalista lidera a oração).
    assert report._matriz_leitura("SUBAVALIADA — ...", "atencao").startswith(
        "Fundamentalmente descontada"
    )
    # Demais células curadas também abrem pelo fundamento (não pela parte técnica).
    assert report._matriz_leitura("NO INTERVALO — ...", "tendencia_de_alta").startswith(
        "Dentro do intervalo justo"
    )
    assert report._matriz_leitura("SOBREAVALIADA — ...", "sem_tendencia").startswith(
        "Acima do valor intrínseco"
    )


def test_matriz_veredito_vazio_degrada_para_vazio():
    # DDM não calculou → veredito "" → matriz "" (sem frase inventada).
    assert report._matriz_leitura("", "atencao") == ""
    assert report._matriz_leitura("", "tendencia_de_alta") == ""


# --------------------------------------------------------------------------- #
# Alerta de reverificação (TIMING-03 / D-07/D-08/D-09)
# --------------------------------------------------------------------------- #
def _ohlc_baixa_rompimento() -> pd.DataFrame:
    """Série DIÁRIA em queda contínua: preço termina ABAIXO da própria MM200 e fazendo
    novas mínimas (perda da mínima do Donchian). Aciona ≥2 gatilhos de baixa.

    O passo da queda (~0,47/barra) é maior que o offset Low (0,3), de modo que o Close
    da ponta rompe abaixo da mínima causal das 20 barras anteriores (perda_minima)."""
    closes = np.linspace(200.0, 60.0, 300)
    idx = pd.date_range("2019-01-01", periods=len(closes), freq="B")
    close = pd.Series(closes, index=idx)
    return pd.DataFrame(
        {
            "Open": close.shift(1).bfill(),
            "High": close + 0.3,
            "Low": close - 0.3,
            "Close": close,
        }
    )


def test_alerta_dispara_consolidado_em_rompimento():
    # D-07/D-09: OR dos gatilhos → UMA mensagem consolidada, voz reverificação, sem "venda".
    cfg = copy.deepcopy(_cfg_ind())
    cfg["indicadores"]["base_temporal"] = "diario"   # 300 barras diárias bastam p/ MM200
    c = CompanyData(ticker="TST", anos=[2023], ohlc_ajustado=_ohlc_baixa_rompimento())

    a = report.analisar_acao(c, cfg)

    # Pré-condição: realmente abaixo da MM200 e perdendo a mínima do canal.
    assert a.sinais.tendencia.posicao_mm200 == "abaixo"
    assert a.sinais.canais.rompimento_donchian == "perda_minima"
    # Alerta consolidado, voz reverificação.
    assert a.alerta_reverificacao is not None
    assert "Reverifique os fundamentos" in a.alerta_reverificacao
    assert "Não é sinal de venda" in a.alerta_reverificacao
    assert "preço abaixo da MM200" in a.alerta_reverificacao
    assert "rompimento da mínima do canal" in a.alerta_reverificacao
    # T-06-05: nunca soa como ordem de venda — "venda" só aparece dentro da negação.
    assert a.alerta_reverificacao.count("venda") == 1
    assert "Não é sinal de venda" in a.alerta_reverificacao


def test_alerta_none_sem_rompimento():
    # D-07: nenhum gatilho de baixa (preço acima da MM200, sem death cross / perda mínima)
    # → alerta None. Reusa a série lateral-acima-da-MM200 (mesma de TEST-06).
    cfg = copy.deepcopy(_cfg_ind())
    cfg["indicadores"]["base_temporal"] = "diario"
    c = CompanyData(ticker="TST", anos=[2023], ohlc_ajustado=_ohlc_acima_mm200_adx_fraco())

    a = report.analisar_acao(c, cfg)

    assert a.sinais.tendencia.posicao_mm200 == "acima"
    assert a.alerta_reverificacao is None


def test_alerta_independe_do_veredito_d08():
    # D-08: o alerta dispara lendo SÓ os sinais, independente do veredito DDM.
    # O helper puro recebe apenas `sinais` — não há canal para o veredito influenciar.
    cfg = copy.deepcopy(_cfg_ind())
    cfg["indicadores"]["base_temporal"] = "diario"
    c = CompanyData(ticker="TST", anos=[2023], ohlc_ajustado=_ohlc_baixa_rompimento())
    a = report.analisar_acao(c, cfg)
    # veredito vazio (sem fundamentos) e ainda assim o alerta disparou.
    assert a.veredito == ""
    assert a.alerta_reverificacao is not None


# --------------------------------------------------------------------------- #
# Seção CLI "Sinais técnicos (consultivos)" (CLI-01 / D-13)
# --------------------------------------------------------------------------- #
def test_cli_secao_sinais_tecnicos_normal():
    # CLI-01: a seção espelha o read da engine, com alerta ⚠️ quando há rompimento.
    cfg = copy.deepcopy(_cfg_ind())
    cfg["indicadores"]["base_temporal"] = "diario"
    c = CompanyData(ticker="TST", anos=[2023], ohlc_ajustado=_ohlc_baixa_rompimento())
    a = report.analisar_acao(c, cfg)

    md = report.relatorio_markdown(c, a, cfg)

    assert "## Sinais técnicos (consultivos)" in md
    assert "**Timing de entrada:**" in md
    # Glifo ⚠️ da seção Alertas reaparece no read técnico quando há alerta (paridade visual).
    assert "- ⚠️ Reverifique os fundamentos" in md


def test_cli_secao_sinais_tecnicos_degradado():
    # D-13 / DATA-03: histórico ausente (ohlc_ajustado=None) → fallback em itálico, sem quebrar.
    cfg = copy.deepcopy(_cfg_ind())
    c = CompanyData(ticker="TST", anos=[2023], ohlc_ajustado=None)
    a = report.analisar_acao(c, cfg)

    md = report.relatorio_markdown(c, a, cfg)

    assert "## Sinais técnicos (consultivos)" in md
    assert "_Histórico de preços insuficiente para o read técnico._" in md


# --------------------------------------------------------------------------- #
# Degradação holística "só-de-força" (CR-01 / WR-02 / IN-02)
# --------------------------------------------------------------------------- #
def _ohlc_achatado(n: int = 220) -> pd.DataFrame:
    """Série DIÁRIA achatada (close ~constante) por ≥200 barras.

    A MM200 fica DISPONÍVEL (≥200 barras), mas a ausência total de movimento direcional
    leva o ADX a ser todo-NaN ⇒ forca_adx="indisponivel". É o caso "só-de-força" (CR-01):
    a direção (MM200) existe, mas a força (ADX) não — o read técnico degrada por aí.
    """
    close = pd.Series(100.0, index=pd.date_range("2019-01-01", periods=n, freq="B"))
    return pd.DataFrame(
        {"Open": close, "High": close + 0.3, "Low": close - 0.3, "Close": close}
    )


def test_degradacao_so_de_forca():
    # CR-01/WR-02: ADX indisponível com MM200 disponível (série achatada) tem de degradar
    # IGUAL ao histórico curto — nenhum campo derivado pode afirmar um estado fabricado.
    cfg = copy.deepcopy(_cfg_ind())
    cfg["indicadores"]["base_temporal"] = "diario"
    c = CompanyData(ticker="TST", anos=[2023], ohlc_ajustado=_ohlc_achatado())

    a = report.analisar_acao(c, cfg)

    # Pré-condição do caso só-de-força: MM200 disponível, ADX indisponível.
    assert a.sinais.tendencia.posicao_mm200 != "indisponivel"
    assert a.sinais.forca.forca_adx == "indisponivel"
    # Degradação holística: timing e matriz colapsam coerentemente (nada fabricado).
    assert a.timing_resumo == ""
    assert a.matriz_leitura == ""

    # Markdown: a linha de degradação aparece e a de timing NÃO (guarda por not timing_resumo).
    md = report.relatorio_markdown(c, a, cfg)
    assert "_Histórico de preços insuficiente para o read técnico._" in md
    assert "**Timing de entrada:**" not in md
