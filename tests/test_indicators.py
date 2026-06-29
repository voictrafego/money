"""Trava a matemática dos indicadores (Wilder vs TradingView, no-repaint, tendência sobre SMA)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from analista.core import indicators
from analista.ingest import prices
from tests.test_ingest_ohlc import _hist_itsa4_multisplit, _ITSA4_EVENTOS


def _cfg_ind() -> dict:
    """Carrega o config.yaml shipado para pinar os parâmetros canônicos nos testes."""
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _serie_golden_cross() -> pd.Series:
    """Tendência de baixa longa seguida de alta sustentada → MM50 cruza acima da MM200."""
    down = np.linspace(100.0, 50.0, 200)
    up = np.linspace(50.0, 160.0, 140)
    closes = np.concatenate([down, up])
    idx = pd.date_range("2019-01-01", periods=len(closes), freq="B")
    return pd.Series(closes, index=idx)


# --- Tendencia (TREND-01..04) ---
def test_sinais_tendencia_sma():
    # Golden cross MM50×MM200 derivado SEMPRE de SMA (D-03). Recorta a série no 1º bar
    # de cruzamento para fixar o sinal "golden_cross" na última barra.
    cfg = _cfg_ind()
    close = _serie_golden_cross()
    sma50 = close.rolling(50, min_periods=50).mean()
    sma200 = close.rolling(200, min_periods=200).mean()
    diff = sma50 - sma200
    sign = np.sign(diff)
    cross_pos = None
    for i in range(1, len(diff)):
        if sign.iloc[i] > 0 and sign.iloc[i - 1] <= 0 and not np.isnan(diff.iloc[i - 1]):
            cross_pos = i
            break
    assert cross_pos is not None

    t = indicators._tendencia(close.iloc[: cross_pos + 1], cfg)
    assert t.cruzamento == "golden_cross"
    assert t.posicao_mm200 == "acima"

    # D-03: se o sinal fosse derivado da EMA, já teria cruzado antes → daria "nenhum".
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    ediff = ema50 - ema200
    assert ediff.iloc[cross_pos] > 0 and ediff.iloc[cross_pos - 1] > 0


def test_historico_curto_tendencia():
    # <200 bars: sma200 toda-NaN; sinais discretos degradam para "indisponivel" sem exceção.
    cfg = _cfg_ind()
    idx = pd.date_range("2021-01-01", periods=120, freq="B")
    close = pd.Series(np.linspace(10.0, 20.0, 120), index=idx)
    t = indicators._tendencia(close, cfg)
    assert t.sma200.isna().all()
    assert t.posicao_mm200 == "indisponivel"
    assert t.cruzamento == "indisponivel"


# --- Momentum (MOM-01..02) ---
# Dataset canônico de Wilder ("New Concepts in Technical Trading Systems"), replicado por
# StockCharts/Wikipedia/TradingView: primeiro RSI(14) = 70,5328 (SMA-seeded).
_WILDER_CLOSES = [
    44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245, 45.8433,
    46.0826, 45.8931, 46.0328, 45.6140, 46.2820, 46.2820, 46.0028, 46.0328, 46.4116,
    46.2222, 45.6439, 46.2122, 46.2521, 45.7137, 46.4515, 45.7835, 45.3548, 44.0288,
    44.1783, 44.2181, 44.5672, 43.4205, 42.6628, 43.1314,
]


def _serie_ruidosa(n: int = 320, seed: int = 42) -> pd.Series:
    """Série determinística (tendência + ciclo + ruído seedado) para no-repaint/MACD."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    base = 50.0 + 10.0 * np.sin(t / 15.0) + 0.05 * t + rng.normal(0, 1.0, n)
    idx = pd.date_range("2019-01-01", periods=n, freq="B")
    return pd.Series(base, index=idx)


def test_rsi_wilder_canonico():
    # Âncora pública: 1º RSI(14) = 70,5328; cinco seguintes batem o TradingView.
    close = pd.Series(_WILDER_CLOSES)
    rsi = indicators.rsi_wilder(close, length=14)
    validos = rsi.dropna()
    assert validos.iloc[0] == pytest.approx(70.5328, abs=1e-3)
    np.testing.assert_allclose(
        validos.iloc[:6].to_numpy(float),
        [70.5328, 66.3186, 66.5498, 69.4063, 66.3552, 57.9749],
        atol=1e-3,
    )


def test_macd_cross():
    # MACD usa EMA padrão (não Wilder). Recorta no 1º bar de cruzamento da linha×sinal.
    cfg = _cfg_ind()
    close = _serie_ruidosa()
    fast, slow, signal = cfg["indicadores"]["macd"]
    macd = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    macd_sinal = macd.ewm(span=signal, adjust=False).mean()
    d = macd - macd_sinal
    sign = np.sign(d)
    cross_pos = None
    for i in range(1, len(d)):
        if sign.iloc[i] > 0 and sign.iloc[i - 1] <= 0:
            cross_pos = i
            break
    assert cross_pos is not None
    m = indicators._momentum(close.iloc[: cross_pos + 1], cfg)
    assert m.cruzamento_macd == "cruz_alta"


def test_no_repaint_momentum():
    # ind(s[:k])[-1] == ind(s)[k-1] para RSI e linha MACD (TEST-04).
    cfg = _cfg_ind()
    s = _serie_ruidosa()
    rsi_full = indicators.rsi_wilder(s, length=cfg["indicadores"]["rsi_janela"])
    macd_full = indicators._momentum(s, cfg).macd
    for k in (60, 120, 200, 300):
        rsi_k = indicators.rsi_wilder(s.iloc[:k], length=cfg["indicadores"]["rsi_janela"])
        assert rsi_k.iloc[-1] == pytest.approx(rsi_full.iloc[k - 1], abs=1e-9)
        macd_k = indicators._momentum(s.iloc[:k], cfg).macd
        assert macd_k.iloc[-1] == pytest.approx(macd_full.iloc[k - 1], abs=1e-9)


# --- Canais (CHAN-01..03) ---
def _frame_ohlc(close, high=None, low=None, start: str = "2021-01-01") -> pd.DataFrame:
    """Frame OHLC determinístico (colunas capitalizadas, DatetimeIndex) para os Canais."""
    close = np.asarray(close, dtype=float)
    high = close + 0.5 if high is None else np.asarray(high, dtype=float)
    low = close - 0.5 if low is None else np.asarray(low, dtype=float)
    idx = pd.date_range(start, periods=len(close), freq="B")
    return pd.DataFrame({"High": high, "Low": low, "Close": close}, index=idx)


def test_donchian_breakout_causal():
    # Canal Donchian-20 dos 20 bars ANTERIORES (.shift(1)); último close rompe acima → nova_maxima.
    cfg = _cfg_ind()
    close = np.full(60, 100.0)
    close[-1] = 120.0
    df = _frame_ohlc(close)
    c = indicators._canais(df, cfg)
    assert c.rompimento_donchian == "nova_maxima"

    # No-repaint: o canal nunca inclui a barra atual → _canais(s[:k]).iloc[-1] == _canais(s)[k-1].
    for k in (40, 50):
        ck = indicators._canais(df.iloc[:k], cfg)
        assert ck.donchian_sup.iloc[-1] == pytest.approx(c.donchian_sup.iloc[k - 1], abs=1e-9)
        assert ck.donchian_inf.iloc[-1] == pytest.approx(c.donchian_inf.iloc[k - 1], abs=1e-9)

    # Sem o .shift(1) o max dos últimos 20 incluiria a própria barra (high=120.5) → nunca romperia.
    hi20_sem_shift = df["High"].rolling(20, min_periods=20).max()
    assert df["Close"].iloc[-1] <= hi20_sem_shift.iloc[-1]


def test_bollinger_touch():
    # Último close encosta na banda superior; bb usa desvio POPULACIONAL (ddof=0, TradingView).
    cfg = _cfg_ind()
    close = np.full(40, 50.0)
    close[-1] = 60.0
    df = _frame_ohlc(close, high=np.full(40, 60.5), low=np.full(40, 49.5))
    c = indicators._canais(df, cfg)
    assert c.toque_bollinger == "banda_superior"

    # Cross-check ddof=0 num slice fixo: bb_sup == SMA20 + 2*std_populacional dos últimos 20.
    sl = pd.Series(close[-20:])
    sigma = cfg["indicadores"]["bollinger"]["sigma"]
    esperado = sl.mean() + sigma * sl.std(ddof=0)
    np.testing.assert_allclose(c.bb_sup.iloc[-1], esperado, rtol=1e-12)
    # Discriminação anti-ddof=1: a amostral deslocaria a banda e NÃO bateria.
    esperado_ddof1 = sl.mean() + sigma * sl.std(ddof=1)
    assert not np.isclose(c.bb_sup.iloc[-1], esperado_ddof1, rtol=1e-9)


def test_squeeze_percentil_causal():
    # Cauda de baixa volatilidade vs janela de 126 → largura atual no percentil baixo → squeeze_on.
    cfg = _cfg_ind()
    rng = np.random.default_rng(7)
    close = np.concatenate([100 + rng.normal(0, 5.0, 140), 100 + rng.normal(0, 0.1, 60)])
    df = _frame_ohlc(close)
    c = indicators._canais(df, cfg)
    assert c.squeeze == "squeeze_on"
    assert c.squeeze_pct.iloc[-1] <= cfg["indicadores"]["squeeze_percentil"]

    # Primeiro válido: o warmup do Bollinger (20) empurra a largura para o índice 19, e o
    # percentil rolling de 126 só fica válido em 19 + 125 = 144 (causal; o "125" do método é
    # sobre uma série de largura sem NaN inicial, aqui o canal acrescenta o warmup das bandas).
    jbb = cfg["indicadores"]["bollinger"]["janela"]
    jsq = cfg["indicadores"]["squeeze_janela"]
    primeiro_valido = (jbb - 1) + (jsq - 1)
    assert c.squeeze_pct.iloc[:primeiro_valido].isna().all()
    assert not np.isnan(c.squeeze_pct.iloc[primeiro_valido])

    # Causal/no-repaint: squeeze_pct(serie[:k]).iloc[-1] == squeeze_pct(serie)[k-1].
    for k in (160, 180, 200):
        ck = indicators._canais(df.iloc[:k], cfg)
        assert ck.squeeze_pct.iloc[-1] == pytest.approx(c.squeeze_pct.iloc[k - 1], abs=1e-9)


def test_canais_historico_curto():
    # <20 bars: Donchian/Bollinger/squeeze degradam para "indisponivel" sem exceção (T-05-04).
    cfg = _cfg_ind()
    close = np.linspace(10.0, 12.0, 15)
    df = _frame_ohlc(close)
    c = indicators._canais(df, cfg)
    assert c.squeeze_pct.isna().all()
    assert c.squeeze == "indisponivel"
    assert c.rompimento_donchian == "indisponivel"
    assert c.toque_bollinger == "indisponivel"


# --- Forca (FORCE-01..02) ---
def _ohlc_adx_ref(n: int = 80, seed: int = 11) -> pd.DataFrame:
    """Série OHLC determinística (np.linspace + ruído seedado) — fixture canônica do ADX.

    É a MESMA série usada no checkpoint humano TradingView (Task 3). High/Low envolvem
    o close por um spread positivo para gerar um True Range não-trivial.
    """
    rng = np.random.default_rng(seed)
    base = np.linspace(20.0, 60.0, n) + rng.normal(0, 1.5, n)
    high = base + np.abs(rng.normal(0, 0.8, n)) + 0.5
    low = base - np.abs(rng.normal(0, 0.8, n)) - 0.5
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    return pd.DataFrame({"High": high, "Low": low, "Close": base}, index=idx)


def test_adx_wilder_estrutural():
    # Dupla suavização de Wilder: 1º ADX válido no índice 2*length-1 = 27 (length 14).
    # Seed errado (start=0) deixaria adx.dropna() vazio — este teste pega a armadilha.
    cfg = _cfg_ind()
    length = cfg["indicadores"]["adx_janela"]
    df = _ohlc_adx_ref()
    adx, pdi, ndi = indicators.adx_wilder(df, length)
    validos = adx.dropna()
    assert len(validos) > 0                              # apanha o bug start=0 (tudo NaN)
    primeiro = adx.reset_index(drop=True).first_valid_index()
    assert primeiro == 2 * length - 1 == 27
    # +DI/-DI também válidos a partir do índice length
    assert pdi.reset_index(drop=True).first_valid_index() == length
    assert ndi.reset_index(drop=True).first_valid_index() == length

    # No-repaint: adx(s[:k]).iloc[-1] == adx(s)[k-1] (TEST-04).
    for k in (40, 55, 70, 80):
        adx_k = indicators.adx_wilder(df.iloc[:k], length)[0]
        assert adx_k.iloc[-1] == pytest.approx(adx.iloc[k - 1], abs=1e-9)


def test_adx_wilder_referencia():
    # TEST-03 (checkpoint humano APROVADO): âncora numérica do ADX(14)/+DI/-DI cruzada com
    # o TradingView na série canônica _ohlc_adx_ref(80, seed=11). Literais congelados (atol 1e-2).
    cfg = _cfg_ind()
    df = _ohlc_adx_ref()
    adx, pdi, ndi = indicators.adx_wilder(df, cfg["indicadores"]["adx_janela"])
    referencia = {
        27: (33.2531, 34.4017, 18.8407),
        40: (42.0324, 35.9687, 10.7024),
        60: (40.2369, 35.9882, 17.4333),
        79: (39.6431, 38.3801, 15.3219),
    }
    for i, (adx_ref, pdi_ref, ndi_ref) in referencia.items():
        np.testing.assert_allclose(adx.iloc[i], adx_ref, atol=1e-2)
        np.testing.assert_allclose(pdi.iloc[i], pdi_ref, atol=1e-2)
        np.testing.assert_allclose(ndi.iloc[i], ndi_ref, atol=1e-2)


def test_regressao_slope_r2():
    # Série perfeitamente linear → R² ~ 1.0 e slope_ano > 0; série flat → slope_ano ~ 0.
    idx = pd.date_range("2020-01-01", periods=120, freq="B")
    subida = pd.Series(np.linspace(10.0, 30.0, 120), index=idx)
    slope, r2 = indicators.regressao_trailing(subida, win=90)
    assert r2.iloc[-1] == pytest.approx(1.0, abs=1e-9)
    assert slope.iloc[-1] > 0
    assert pd.isna(slope.iloc[88])                       # 1º válido no índice win-1 = 89
    assert not pd.isna(slope.iloc[89])

    flat = pd.Series(np.full(120, 50.0), index=idx)
    slope_flat, _ = indicators.regressao_trailing(flat, win=90)
    assert slope_flat.iloc[-1] == pytest.approx(0.0, abs=1e-9)


# --- calcular() entry-point + split TEST-05 ---
_SINAIS_DISCRETOS = [
    ("tendencia", "posicao_mm200"), ("tendencia", "cruzamento"),
    ("canais", "rompimento_donchian"), ("canais", "toque_bollinger"), ("canais", "squeeze"),
    ("forca", "forca_adx"),
    ("momentum", "nivel_rsi"), ("momentum", "cruzamento_macd"),
]


def _frame_ohlc_longo(n: int = 320, seed: int = 3) -> pd.DataFrame:
    """Frame OHLC longo o suficiente para todas as janelas (200/126/90) ficarem válidas."""
    s = _serie_ruidosa(n=n, seed=seed)
    close = s.to_numpy(float)
    rng = np.random.default_rng(seed + 1)
    spread = np.abs(rng.normal(0, 0.8, n)) + 0.5
    return pd.DataFrame(
        {"Open": close, "High": close + spread, "Low": close - spread, "Close": close},
        index=s.index,
    )


def test_calcular_completo():
    # Histórico cheio: calcular devolve SinaisTecnicos com as 4 famílias, todos os
    # sinais discretos VÁLIDOS (não "indisponivel").
    cfg = _cfg_ind()
    sinais = indicators.calcular(_frame_ohlc_longo(), cfg)
    assert isinstance(sinais, indicators.SinaisTecnicos)
    for fam in ("tendencia", "canais", "forca", "momentum"):
        assert getattr(sinais, fam) is not None
    for fam, attr in _SINAIS_DISCRETOS:
        assert getattr(getattr(sinais, fam), attr) != "indisponivel", (fam, attr)


def test_calcular_degrada():
    # ohlc=None → TODOS os sinais "indisponivel", sem exceção.
    cfg = _cfg_ind()
    nulo = indicators.calcular(None, cfg)
    for fam, attr in _SINAIS_DISCRETOS:
        assert getattr(getattr(nulo, fam), attr) == "indisponivel", (fam, attr)

    # Histórico curto (12 bars): sinais de janela longa degradam para "indisponivel".
    close = np.linspace(10.0, 12.0, 12)
    curto = _frame_ohlc(close)  # já tem Open? não — adiciona
    curto = curto.assign(Open=close)
    s = indicators.calcular(curto, cfg)
    assert s.tendencia.posicao_mm200 == "indisponivel"
    assert s.forca.forca_adx == "indisponivel"
    assert s.canais.rompimento_donchian == "indisponivel"
    assert s.momentum.nivel_rsi == "indisponivel"
    assert s.canais.squeeze == "indisponivel"


def test_split_sem_cross_espurio():
    # TEST-05: a série split-adjusted (contínua) NÃO gera cross/breakout espúrio nas 5
    # datas de split do ITSA4; a NOMINAL (com degraus) geraria — contraste prova a teeth.
    cfg = _cfg_ind()
    hist, _A = _hist_itsa4_multisplit()
    aj = prices._ajustar_por_split(hist)

    # calcular roda sobre o frame ajustado sem exceção e devolve as 4 famílias
    sinais = indicators.calcular(aj, cfg)
    assert isinstance(sinais, indicators.SinaisTecnicos)

    j20 = cfg["indicadores"]["donchian"][0]
    j50, j200 = cfg["indicadores"]["sma_emas"][1], cfg["indicadores"]["sma_emas"][2]

    def _sinais_por_barra(df: pd.DataFrame):
        close, high, low = df["Close"], df["High"], df["Low"]
        don_inf = low.rolling(j20, min_periods=j20).min().shift(1)
        don_sup = high.rolling(j20, min_periods=j20).max().shift(1)
        perda = close < don_inf            # rompimento de baixa (gatilho espúrio do degrau)
        sma50 = close.rolling(j50, min_periods=j50).mean()
        sma200 = close.rolling(j200, min_periods=j200).mean()
        d = np.sign(sma50 - sma200)
        cross = d.ne(d.shift(1)) & d.notna() & d.shift(1).notna()  # qualquer cruzamento
        return perda, cross

    perda_aj, cross_aj = _sinais_por_barra(aj)
    perda_nom, _ = _sinais_por_barra(hist)

    for data, _f in _ITSA4_EVENTOS:
        loc = aj.index.get_loc(data)
        # ajustado contínuo: nenhum rompimento de baixa nem cruzamento na data do split
        assert not bool(perda_aj.iloc[loc]), (data, "perda_minima espúria no ajustado")
        assert not bool(cross_aj.iloc[loc]), (data, "cruzamento espúrio no ajustado")

    # teeth: o NOMINAL dispara pelo menos uma perda_minima espúria em torno dos splits
    janela_eventos = pd.Index([d for d, _ in _ITSA4_EVENTOS])
    proximos = perda_nom.reindex(janela_eventos, method="nearest")
    assert proximos.any(), "fixture sem teeth: nominal deveria romper de baixa nos splits"


# --------------------------------------------------------------------------- #
# Exposição read-only da close (split-adjusted) usada pelos indicadores (07-01)
# --------------------------------------------------------------------------- #
def test_sinais_close_paridade():
    # 07-01 / UI-04: SinaisTecnicos.close é a MESMA série de ohlc["Close"] (índice e
    # valores idênticos) — read-only, sem recálculo, para os marcadores de evento da UI.
    cfg = _cfg_ind()
    idx = pd.date_range("2019-01-01", periods=30, freq="B")
    close = pd.Series(np.linspace(10.0, 25.0, 30), index=idx)
    ohlc = pd.DataFrame(
        {"Open": close, "High": close + 0.5, "Low": close - 0.5, "Close": close}
    )

    sinais = indicators.calcular(ohlc, cfg)

    assert sinais.close.equals(ohlc["Close"])


def test_sinais_close_frame_vazio():
    # 07-01 / DATA-03: frame vazio/None degrada para uma close Series VAZIA (sem exceção),
    # espelhando o guard de borda existente — a UI não quebra ao acessar sinais.close.
    cfg = _cfg_ind()
    for entrada in (None, pd.DataFrame()):
        sinais = indicators.calcular(entrada, cfg)
        assert isinstance(sinais.close, pd.Series)
        assert len(sinais.close) == 0


# --------------------------------------------------------------------------- #
# Pivôs fractal de Williams (PIVOT-01) — no-repaint causal (D-01/D-03)
# --------------------------------------------------------------------------- #
def _frame_pivos(n: int = 80) -> pd.DataFrame:
    """OHLC com swings claros (seno suave determinístico) para os goldens de pivô.

    Período ~2π·6 ≈ 38 barras → ~2 ciclos em 80 barras: vários topos/fundos confirmados,
    longe da borda. Sem ruído de propósito (posições de pivô determinísticas).
    """
    t = np.arange(n)
    close = 50.0 + 8.0 * np.sin(t / 6.0)
    high = close + 0.5
    low = close - 0.5
    idx = pd.date_range("2021-01-01", periods=n, freq="B")
    return pd.DataFrame({"Open": close, "High": high, "Low": low, "Close": close}, index=idx)


def test_config_pivo_n():
    # O config.yaml shipado expõe o N do fractal de Williams (D-02, default 2 — swing diário).
    cfg = _cfg_ind()
    assert cfg["indicadores"]["pivo_n"] == 2


def test_pivos_no_repaint_truncacao():
    # GATE D-03 (obrigatório da fase): _pivos(df[:k]) == _pivos(df) nas barras já fechadas.
    # Um pivô confirmado em t é IMUTÁVEL quando chegam barras à direita (no-repaint trivial
    # do fractal de Williams — ao contrário de find_peaks, cuja prominence repaint na borda).
    cfg = _cfg_ind()
    df = _frame_pivos()
    N = cfg["indicadores"]["pivo_n"]
    full = indicators._pivos(df, cfg)
    for k in (40, 60):
        pk = indicators._pivos(df.iloc[:k], cfg)
        # barras fechadas no truncado: índices 0..k-1-N (têm N barras à direita no slice).
        lim = k - N
        np.testing.assert_allclose(
            pk.pivot_high.iloc[:lim].to_numpy(float),
            full.pivot_high.iloc[:lim].to_numpy(float),
            equal_nan=True,
        )
        np.testing.assert_allclose(
            pk.pivot_low.iloc[:lim].to_numpy(float),
            full.pivot_low.iloc[:lim].to_numpy(float),
            equal_nan=True,
        )


def test_pivos_lag_confirmacao():
    # As N barras mais recentes NUNCA são pivô confirmado (faltam N barras à direita) — D-03.
    cfg = _cfg_ind()
    df = _frame_pivos()
    N = cfg["indicadores"]["pivo_n"]
    p = indicators._pivos(df, cfg)
    assert p.pivot_high.iloc[-N:].isna().all()
    assert p.pivot_low.iloc[-N:].isna().all()
    assert p.n == N


def test_pivos_teeth():
    # Anti-falso-positivo: série monotônica crescente NÃO tem topo interno confirmado;
    # um V tem EXATAMENTE um fundo confirmado na ponta (com N barras de cada lado).
    cfg = _cfg_ind()
    subida = np.linspace(10.0, 30.0, 40)
    p_up = indicators._pivos(_frame_ohlc(subida), cfg)
    assert p_up.pivot_high.isna().all()
    assert p_up.pivot_low.isna().all()
    assert p_up.ultimo_topo is None

    desce = np.linspace(30.0, 10.0, 21)
    sobe = np.linspace(10.0, 30.0, 21)[1:]
    v = np.concatenate([desce, sobe])              # ponta do V no índice 20
    p_v = indicators._pivos(_frame_ohlc(v), cfg)
    fundos = p_v.pivot_low.dropna()
    assert len(fundos) == 1
    assert p_v.pivot_low.notna().to_numpy().nonzero()[0][0] == 20
    assert p_v.pivot_high.isna().all()
    assert p_v.ultimo_fundo == pytest.approx(v[20] - 0.5, abs=1e-9)


def test_pivos_historico_curto():
    # Frame < 2N+1 barras → séries todo-NaN e ultimo_topo/ultimo_fundo None, sem exceção.
    cfg = _cfg_ind()
    N = cfg["indicadores"]["pivo_n"]
    close = np.linspace(10.0, 12.0, 2 * N)         # 2N barras (< 2N+1)
    p = indicators._pivos(_frame_ohlc(close), cfg)
    assert p.pivot_high.isna().all()
    assert p.pivot_low.isna().all()
    assert p.ultimo_topo is None and p.ultimo_fundo is None
    assert p.n == N

    # None via calcular não levanta exceção e popula um Pivos degradado.
    s = indicators.calcular(None, cfg)
    assert s.pivos is not None
    assert s.pivos.ultimo_topo is None and s.pivos.ultimo_fundo is None


def test_calcular_pivos():
    # calcular popula SinaisTecnicos.pivos de forma aditiva (topos e fundos confirmados).
    cfg = _cfg_ind()
    sinais = indicators.calcular(_frame_pivos(), cfg)
    assert sinais.pivos is not None
    assert sinais.pivos.pivot_high.notna().any()
    assert sinais.pivos.pivot_low.notna().any()


# --------------------------------------------------------------------------- #
# ATR exposto a partir do TR da cadeia do ADX (D-08) — insumo de LEVEL-01/03
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Contexto de tendência: Dow no diário (TREND-01, D-05) — sequência de pivôs + desempate
# --------------------------------------------------------------------------- #
def _frame_trend(close) -> pd.DataFrame:
    """Frame OHLC determinístico (4 colunas) para os goldens de Dow/alinhamento."""
    close = np.asarray(close, dtype=float)
    idx = pd.date_range("2021-01-01", periods=len(close), freq="B")
    return pd.DataFrame(
        {"Open": close, "High": close + 0.5, "Low": close - 0.5, "Close": close}, index=idx
    )


def test_dow_alta_hh_hl():
    # Seno com drift de alta → topos e fundos confirmados CRESCENTES (HH+HL) → "alta".
    cfg = _cfg_ind()
    t = np.arange(120)
    df = _frame_trend(50.0 + 5.0 * np.sin(t / 6.0) + 0.15 * t)
    pivos = indicators._pivos(df, cfg)
    assert indicators._dow(pivos, df, cfg) == "alta"


def test_dow_baixa_lh_ll():
    # Seno com drift de baixa → topos e fundos DECRESCENTES (LH+LL) → "baixa".
    cfg = _cfg_ind()
    t = np.arange(120)
    df = _frame_trend(50.0 + 5.0 * np.sin(t / 6.0) - 0.15 * t)
    pivos = indicators._pivos(df, cfg)
    assert indicators._dow(pivos, df, cfg) == "baixa"


def test_dow_lateral_ambiguo_adx_fraco():
    # Série ruidosa de lado: sequência de pivôs ambígua + ADX fraco (<20) → "lateral".
    cfg = _cfg_ind()
    rng = np.random.default_rng(7)
    df = _frame_trend(100.0 + rng.normal(0, 1.0, 240))
    pivos = indicators._pivos(df, cfg)
    assert indicators._dow(pivos, df, cfg) == "lateral"


def test_dow_desempate_por_slope_adx():
    # Rampa linear: 0 pivôs confirmados, mas ADX forte + slope claramente +/- → desempate
    # reusa MM/ADX existentes (D-05) e resolve direção.
    cfg = _cfg_ind()
    up = _frame_trend(np.linspace(10.0, 40.0, 120))
    dn = _frame_trend(np.linspace(40.0, 10.0, 120))
    assert indicators._dow(indicators._pivos(up, cfg), up, cfg) == "alta"
    assert indicators._dow(indicators._pivos(dn, cfg), dn, cfg) == "baixa"


def test_dow_frame_curto_indisponivel():
    # Frame curto: sem pivôs e ADX NaN → "indisponivel" (degradação graciosa).
    cfg = _cfg_ind()
    df = _frame_trend(np.linspace(10.0, 12.0, 8))
    pivos = indicators._pivos(df, cfg)
    assert indicators._dow(pivos, df, cfg) == "indisponivel"


def test_dow_deterministico():
    # Mesma entrada → mesmo rótulo (determinístico).
    cfg = _cfg_ind()
    t = np.arange(120)
    df = _frame_trend(50.0 + 5.0 * np.sin(t / 6.0) + 0.15 * t)
    pivos = indicators._pivos(df, cfg)
    r1 = indicators._dow(pivos, df, cfg)
    r2 = indicators._dow(pivos, df, cfg)
    assert r1 == r2 == "alta"


# --------------------------------------------------------------------------- #
# Alinhamento semanal→diário via resample W-FRI (TREND-02, D-04/D-06)
# --------------------------------------------------------------------------- #
def test_alinhamento_alinhado_alta():
    # Diário "alta" + semanal "alta" (resample W-FRI) → "alinhado_alta".
    cfg = _cfg_ind()
    t = np.arange(400)
    df = _frame_trend(50.0 + 8.0 * np.sin(t / 6.0) + 0.10 * t)
    ctx = indicators._contexto(df, cfg)
    assert ctx.dow_diario == "alta"
    assert ctx.alinhamento_mtf == "alinhado_alta"


def test_alinhamento_alinhado_baixa():
    # Diário "baixa" + semanal "baixa" → "alinhado_baixa".
    cfg = _cfg_ind()
    t = np.arange(400)
    df = _frame_trend(50.0 + 8.0 * np.sin(t / 6.0) - 0.10 * t)
    ctx = indicators._contexto(df, cfg)
    assert ctx.dow_diario == "baixa"
    assert ctx.alinhamento_mtf == "alinhado_baixa"


def test_alinhamento_conflito_nao_bloqueia():
    # Macro de baixa (semanal=baixa) + perna recente de alta (diário=alta) → "conflito".
    # D-06: conflito é só rótulo — os demais campos de SinaisTecnicos seguem preenchidos.
    cfg = _cfg_ind()
    close = np.concatenate([np.linspace(100.0, 40.0, 800), np.linspace(40.0, 55.0, 40)])
    df = _frame_trend(close)
    sinais = indicators.calcular(df, cfg)
    assert sinais.contexto is not None
    assert sinais.contexto.dow_diario == "alta"
    assert sinais.contexto.alinhamento_mtf == "conflito"
    # D-06: NÃO zera/altera as demais famílias — o setup não é bloqueado.
    assert sinais.tendencia.posicao_mm200 != "indisponivel"
    assert sinais.forca.forca_adx != "indisponivel"
    assert sinais.canais.rompimento_donchian != "indisponivel"


def test_alinhamento_frame_nao_datetime_indisponivel():
    # Índice não-DatetimeIndex → resample inviável → alinhamento "indisponivel" (sem exceção).
    cfg = _cfg_ind()
    t = np.arange(400)
    close = 50.0 + 8.0 * np.sin(t / 6.0) + 0.10 * t
    df = pd.DataFrame(
        {"Open": close, "High": close + 0.5, "Low": close - 0.5, "Close": close}
    )  # RangeIndex (não-datetime)
    ctx = indicators._contexto(df, cfg)
    assert ctx.alinhamento_mtf == "indisponivel"


def test_calcular_popula_contexto():
    # calcular popula SinaisTecnicos.contexto de forma aditiva, com rótulos do vocabulário.
    cfg = _cfg_ind()
    sinais = indicators.calcular(_frame_ohlc_longo(), cfg)
    assert sinais.contexto is not None
    assert sinais.contexto.dow_diario in {"alta", "baixa", "lateral", "indisponivel"}
    assert sinais.contexto.alinhamento_mtf in {
        "alinhado_alta", "alinhado_baixa", "conflito", "indisponivel"
    }


def test_calcular_contexto_degrada():
    # None → calcular não levanta e o contexto degrada para "indisponivel".
    cfg = _cfg_ind()
    nulo = indicators.calcular(None, cfg)
    assert nulo.contexto is not None
    assert nulo.contexto.dow_diario == "indisponivel"
    assert nulo.contexto.alinhamento_mtf == "indisponivel"


def test_sem_fetch_semanal_1wk():
    # D-04: o semanal vem de resample W-FRI, NUNCA de um fetch "1wk" separado do Yahoo.
    raiz = Path(__file__).resolve().parents[1]
    fonte = (raiz / "src" / "analista" / "core" / "indicators.py").read_text(encoding="utf-8")
    assert "1wk" not in fonte
    assert "W-FRI" in fonte


# --------------------------------------------------------------------------- #
# ATR exposto a partir do TR da cadeia do ADX (D-08) — insumo de LEVEL-01/03
# --------------------------------------------------------------------------- #
def test_config_stop_atr_m():
    # O config.yaml shipado expõe o multiplicador do ATR no stop técnico (D-08, default 1.5).
    cfg = _cfg_ind()
    assert cfg["indicadores"]["stop_atr_m"] == 1.5


def test_atr_wilder_consistente_com_adx():
    # ATR exposto == 1ª suavização de Wilder do TR (start=1) — o MESMO `atr` interno do ADX.
    cfg = _cfg_ind()
    length = cfg["indicadores"]["adx_janela"]
    df = _ohlc_adx_ref()
    atr = indicators.atr_wilder(df, length)

    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    esperado = indicators._wilder_rma_from(tr.to_numpy(float), length, start=1)

    np.testing.assert_allclose(atr.to_numpy(float), esperado, equal_nan=True, atol=1e-9)
    assert atr.index.equals(df.index)
    assert atr.reset_index(drop=True).first_valid_index() == length   # 1º válido no índice 14


def test_atr_wilder_historico_curto():
    # Frame com < length+1 barras → ATR todo-NaN, sem exceção (degradação graciosa).
    cfg = _cfg_ind()
    length = cfg["indicadores"]["adx_janela"]
    df = _frame_ohlc(np.linspace(10.0, 12.0, length))   # length barras (< length+1)
    atr = indicators.atr_wilder(df, length)
    assert atr.isna().all()


def test_atr_exposto_em_forca_adx_intacto():
    # adx_wilder PRESERVA a assinatura (adx, pdi, ndi); Forca.atr é exposto aditivamente
    # e bate atr_wilder(df, adx_janela). None via calcular não levanta exceção.
    cfg = _cfg_ind()
    df = _frame_ohlc_longo()
    adx, pdi, ndi = indicators.adx_wilder(df, cfg["indicadores"]["adx_janela"])
    assert adx is not None and pdi is not None and ndi is not None

    sinais = indicators.calcular(df, cfg)
    assert sinais.forca.atr is not None
    assert sinais.forca.atr.notna().any()
    esperado = indicators.atr_wilder(df, cfg["indicadores"]["adx_janela"])
    np.testing.assert_allclose(
        sinais.forca.atr.to_numpy(float), esperado.to_numpy(float),
        equal_nan=True, atol=1e-9,
    )

    nulo = indicators.calcular(None, cfg)
    assert isinstance(nulo.forca.atr, pd.Series)


# --------------------------------------------------------------------------- #
# Zonas de Suporte/Resistência por cluster de pivôs (LEVEL-01, D-10) + ohlc_nominal (D-02)
# --------------------------------------------------------------------------- #
def test_config_cluster_k():
    # O config.yaml shipado expõe o k da largura da zona S/R (= k×ATR — D-10).
    cfg = _cfg_ind()
    assert cfg["indicadores"]["cluster_k"] == 1.0


def _pivos_manual(precos_topo, precos_fundo, n_barras: int = 6) -> "indicators.Pivos":
    """Constrói um Pivos determinístico com preços de pivô conhecidos para o clustering."""
    idx = pd.date_range("2021-01-01", periods=n_barras, freq="B")
    ph = pd.Series(np.nan, index=idx)
    pl = pd.Series(np.nan, index=idx)
    for i, p in enumerate(precos_topo):
        ph.iloc[i] = p
    for j, p in enumerate(precos_fundo):
        pl.iloc[len(precos_topo) + j] = p
    topos = ph.dropna()
    fundos = pl.dropna()
    return indicators.Pivos(
        pivot_high=ph, pivot_low=pl,
        ultimo_topo=float(topos.iloc[-1]) if len(topos) else None,
        ultimo_fundo=float(fundos.iloc[-1]) if len(fundos) else None,
        n=2,
    )


def test_niveis_sr_cluster_zonas():
    # Pivôs próximos (gap < k×ATR) fundem numa ÚNICA zona (low,high) com low<high (faixa,
    # não ponto); pivôs distantes geram zonas separadas. Suportes abaixo, resistências acima
    # do close da barra FECHADA (iloc[-2], D-04 herdado).
    cfg = _cfg_ind()
    idx = pd.date_range("2021-01-01", periods=6, freq="B")
    close = pd.Series([104.0, 104.0, 104.0, 104.0, 105.0, 106.0], index=idx)  # iloc[-2]=105
    ohlc = pd.DataFrame(
        {"Open": close, "High": close + 0.5, "Low": close - 0.5, "Close": close}
    )
    # k×ATR = 1.0×1.0 = 1.0: 100.0 e 100.8 (gap 0.8 < 1.0) fundem; 110.0 (gap 9.2) separa.
    pivos = _pivos_manual(precos_topo=[110.0], precos_fundo=[100.0, 100.8])
    atr = pd.Series([np.nan] * 5 + [1.0], index=idx)

    niveis = indicators._niveis_sr(pivos, ohlc, atr, None, None, cfg)
    assert len(niveis.suportes) == 1            # 100.0 e 100.8 fundidos numa zona
    assert len(niveis.resistencias) == 1        # 110.0 separado
    low, high = niveis.suportes[0]
    assert low < high                           # faixa, NUNCA ponto
    assert high <= 105.0                        # suporte abaixo do close fechado
    rlow, rhigh = niveis.resistencias[0]
    assert rlow < rhigh
    assert rlow >= 105.0                         # resistência acima do close fechado


def test_niveis_donchian_externo():
    # As referências Donchian externas batem a ponta de donchian_*_55 (D-10).
    cfg = _cfg_ind()
    sinais = indicators.calcular(_frame_ohlc_longo(), cfg)
    assert sinais.niveis is not None
    c = sinais.canais
    assert sinais.niveis.donchian_externo_sup == pytest.approx(
        c.donchian_sup_55.dropna().iloc[-1], abs=1e-9
    )
    assert sinais.niveis.donchian_externo_inf == pytest.approx(
        c.donchian_inf_55.dropna().iloc[-1], abs=1e-9
    )


def test_niveis_ohlc_nominal_aditivo():
    # Sem ohlc_nominal: pivôs idênticos ao comportamento anterior. Com ohlc_nominal diferente
    # (preços dobrados): zonas/pivôs de PREÇO mudam (D-02), sem tocar indicadores.
    cfg = _cfg_ind()
    df = _frame_pivos()
    base = indicators.calcular(df, cfg)
    assert base.niveis is not None
    assert base.niveis.suportes or base.niveis.resistencias    # há zonas

    nominal = df * 2.0                                          # frame nominal dobrado
    com_nominal = indicators.calcular(df, cfg, ohlc_nominal=nominal)
    assert com_nominal.pivos.ultimo_topo == pytest.approx(base.pivos.ultimo_topo * 2.0)
    # indicadores (close split-adjusted) inalterados — o ATR continua o do df
    np.testing.assert_allclose(
        com_nominal.forca.atr.to_numpy(float), base.forca.atr.to_numpy(float),
        equal_nan=True, atol=1e-9,
    )


def test_niveis_degrada_sem_pivos():
    # Frame curto / sem pivôs / ATR NaN → zonas vazias e referências None, sem exceção.
    cfg = _cfg_ind()
    close = np.linspace(10.0, 12.0, 6)
    df = _frame_ohlc(close).assign(Open=close)
    sinais = indicators.calcular(df, cfg)
    assert sinais.niveis is not None
    assert sinais.niveis.suportes == []
    assert sinais.niveis.resistencias == []

    nulo = indicators.calcular(None, cfg)
    assert nulo.niveis is not None
    assert nulo.niveis.suportes == [] and nulo.niveis.resistencias == []


# --------------------------------------------------------------------------- #
# Família Volume — MM de volume + flag rompimento com volume (VOL-01, D-11)
# --------------------------------------------------------------------------- #
def test_config_volume_janela():
    # O config.yaml shipado expõe a janela da MM de volume (VOL-01).
    cfg = _cfg_ind()
    assert cfg["indicadores"]["volume_janela"] == 20


def _frame_ohlcv(close, high=None, low=None, volume=None, start="2021-01-01") -> pd.DataFrame:
    """Frame OHLCV determinístico (coluna Volume) para os goldens da família Volume."""
    close = np.asarray(close, dtype=float)
    high = close + 0.5 if high is None else np.asarray(high, dtype=float)
    low = close - 0.5 if low is None else np.asarray(low, dtype=float)
    volume = np.full(len(close), 1000.0) if volume is None else np.asarray(volume, dtype=float)
    idx = pd.date_range(start, periods=len(close), freq="B")
    return pd.DataFrame(
        {"Open": close, "High": high, "Low": low, "Close": close, "Volume": volume}, index=idx
    )


def test_volume_rompimento_com_volume():
    # Barra FECHADA (iloc[-2]) rompe a Donchian superior COM volume acima da MM → flag True.
    cfg = _cfg_ind()
    n = 40
    close = np.full(n, 100.0)
    close[-2] = 130.0            # barra fechada rompe a banda superior
    close[-1] = 131.0            # barra viva — ignorada (D-04)
    vol = np.full(n, 1000.0)
    vol[-2] = 5000.0             # volume acima da média na barra fechada
    df = _frame_ohlcv(close, high=close + 0.5, volume=vol)
    v = indicators._volume(df, cfg)
    assert v.rompimento_com_volume is True
    assert v.volume_mm is not None


def test_volume_rompimento_sem_volume():
    # Mesmo rompimento, mas volume NÃO acima da média na barra fechada → flag False.
    cfg = _cfg_ind()
    n = 40
    close = np.full(n, 100.0)
    close[-2] = 130.0
    close[-1] = 131.0
    df = _frame_ohlcv(close, high=close + 0.5)        # volume constante (= MM) → não confirma
    v = indicators._volume(df, cfg)
    assert v.rompimento_com_volume is False


def test_volume_degrada_sem_coluna():
    # Frame SEM coluna Volume (como os 191 goldens) → volume_mm None, flag False, sem exceção.
    cfg = _cfg_ind()
    close = np.full(40, 100.0)
    df = _frame_ohlc(close).assign(Open=close)        # só OHLC, sem Volume
    v = indicators._volume(df, cfg)
    assert v.volume_mm is None
    assert v.rompimento_com_volume is False


def test_volume_frame_curto():
    # Frame curto → volume_mm todo-NaN e flag False (degradação), sem exceção.
    cfg = _cfg_ind()
    df = _frame_ohlcv(np.full(10, 100.0))
    v = indicators._volume(df, cfg)
    assert v.volume_mm.isna().all()
    assert v.rompimento_com_volume is False


def test_volume_mm_min_periods():
    # volume_mm usa min_periods == volume_janela (NaN com histórico curto, não valor parcial).
    cfg = _cfg_ind()
    janela = cfg["indicadores"]["volume_janela"]
    df = _frame_ohlcv(np.full(janela + 5, 100.0))
    v = indicators._volume(df, cfg)
    assert v.volume_mm.iloc[: janela - 1].isna().all()
    assert not pd.isna(v.volume_mm.iloc[janela - 1])


def test_calcular_popula_volume():
    # calcular popula SinaisTecnicos.volume de forma aditiva quando há coluna Volume.
    cfg = _cfg_ind()
    sinais = indicators.calcular(_frame_ohlcv(np.full(60, 100.0)), cfg)
    assert sinais.volume is not None
    assert sinais.volume.volume_mm is not None


def test_calcular_volume_degrada_sem_coluna():
    # Frame OHLC sem Volume (os 191 goldens) → volume.volume_mm None, sem exceção.
    cfg = _cfg_ind()
    sinais = indicators.calcular(_frame_ohlc_longo(), cfg)
    assert sinais.volume is not None
    assert sinais.volume.volume_mm is None
    assert sinais.volume.rompimento_com_volume is False


# --------------------------------------------------------------------------- #
# Fibonacci ancorado no último impulso confirmado (LEVEL-02/04, D-07)
# --------------------------------------------------------------------------- #
def _pivos_ts(topos: dict, fundos: dict, n_barras: int = 10) -> "indicators.Pivos":
    """Pivos determinístico com topos/fundos em posições/preços conhecidos (com timestamps)."""
    idx = pd.date_range("2021-01-01", periods=n_barras, freq="B")
    ph = pd.Series(np.nan, index=idx)
    pl = pd.Series(np.nan, index=idx)
    for i, p in topos.items():
        ph.iloc[i] = p
    for i, p in fundos.items():
        pl.iloc[i] = p
    t = ph.dropna()
    f = pl.dropna()
    return indicators.Pivos(
        pivot_high=ph, pivot_low=pl,
        ultimo_topo=float(t.iloc[-1]) if len(t) else None,
        ultimo_fundo=float(f.iloc[-1]) if len(f) else None, n=2,
    )


def test_niveis_fib_alta():
    # Impulso de alta F→T confirmado (fundo antes do topo): retração de entrada 38,2/50/61,8%
    # ancorada no topo e extensão de alvo 161,8% projetada do fundo (LEVEL-02/04, D-07).
    cfg = _cfg_ind()
    pivos = _pivos_ts(topos={5: 120.0}, fundos={2: 100.0})
    ctx = indicators.ContextoTendencia(dow_diario="alta", alinhamento_mtf="alinhado_alta")
    niveis = indicators.Niveis()
    indicators._niveis_fib(niveis, pivos, ctx, None, cfg)
    F, T = 100.0, 120.0
    R = T - F
    assert niveis.entrada_zona[0] == pytest.approx(T - R * 0.618)   # 61,8% (mais fundo)
    assert niveis.entrada_zona[1] == pytest.approx(T - R * 0.382)   # 38,2% (mais raso)
    assert niveis.fib_retracoes["500"] == pytest.approx(T - R * 0.5)
    assert niveis.alvo == pytest.approx(F + R * 1.618)
    assert niveis.pivos_ancora["fundo_preco"] == 100.0
    assert niveis.pivos_ancora["topo_preco"] == 120.0
    assert niveis.pivos_ancora["fundo_ts"] < niveis.pivos_ancora["topo_ts"]


def test_niveis_fib_baixa():
    # Impulso de baixa T→F (topo antes do fundo): espelha — retração medida do fundo p/ cima,
    # alvo projetado abaixo do topo.
    cfg = _cfg_ind()
    pivos = _pivos_ts(topos={2: 120.0}, fundos={5: 100.0})
    ctx = indicators.ContextoTendencia(dow_diario="baixa", alinhamento_mtf="alinhado_baixa")
    niveis = indicators.Niveis()
    indicators._niveis_fib(niveis, pivos, ctx, None, cfg)
    F, T = 100.0, 120.0
    R = T - F
    assert niveis.entrada_zona[0] == pytest.approx(F + R * 0.382)
    assert niveis.entrada_zona[1] == pytest.approx(F + R * 0.618)
    assert niveis.fib_retracoes["500"] == pytest.approx(F + R * 0.5)
    assert niveis.alvo == pytest.approx(T - R * 1.618)
    assert niveis.pivos_ancora["topo_ts"] < niveis.pivos_ancora["fundo_ts"]


def test_niveis_fib_lateral_degrada():
    # dow "lateral" → níveis direcionais não fazem sentido: entrada/alvo/âncora None, sem exceção.
    cfg = _cfg_ind()
    pivos = _pivos_ts(topos={5: 120.0}, fundos={2: 100.0})
    ctx = indicators.ContextoTendencia(dow_diario="lateral", alinhamento_mtf="indisponivel")
    niveis = indicators.Niveis()
    indicators._niveis_fib(niveis, pivos, ctx, None, cfg)
    assert niveis.entrada_zona is None
    assert niveis.alvo is None
    assert niveis.pivos_ancora is None


def test_niveis_fib_sem_par_degrada():
    # dow "alta" mas SEM fundo confirmado antes do último topo → sem par âncora → None.
    cfg = _cfg_ind()
    pivos = _pivos_ts(topos={2: 120.0}, fundos={5: 100.0})   # fundo DEPOIS do topo
    ctx = indicators.ContextoTendencia(dow_diario="alta", alinhamento_mtf="alinhado_alta")
    niveis = indicators.Niveis()
    indicators._niveis_fib(niveis, pivos, ctx, None, cfg)
    assert niveis.entrada_zona is None and niveis.alvo is None and niveis.pivos_ancora is None


def test_calcular_popula_fib():
    # calcular popula os níveis de Fibonacci de forma aditiva; âncora auditável (2 pivôs ts+preço).
    cfg = _cfg_ind()
    t = np.arange(120)
    df = _frame_trend(50.0 + 5.0 * np.sin(t / 6.0) + 0.15 * t)   # tendência de alta
    sinais = indicators.calcular(df, cfg)
    assert sinais.contexto.dow_diario == "alta"
    assert sinais.niveis.entrada_zona is not None
    assert sinais.niveis.alvo is not None
    anc = sinais.niveis.pivos_ancora
    assert anc is not None
    assert anc["fundo_ts"] < anc["topo_ts"]            # fundo→topo (impulso de alta)
    assert anc["topo_preco"] > anc["fundo_preco"]
    # no-repaint: âncora em pivôs CONFIRMADOS → entrada_zona é uma faixa (low<high)
    assert sinais.niveis.entrada_zona[0] < sinais.niveis.entrada_zona[1]


# --------------------------------------------------------------------------- #
# Stop técnico (mais conservador entre swing e ATR×m, D-08) + R:R (RR-01, D-09)
# --------------------------------------------------------------------------- #
def _atr_const(valor: float, n: int = 20) -> pd.Series:
    """ATR com último valor válido conhecido (resto NaN) p/ os goldens de stop/RR."""
    idx = pd.date_range("2021-01-01", periods=n, freq="B")
    return pd.Series([np.nan] * (n - 1) + [valor], index=idx)


def _niveis_com_fib(entrada_zona, alvo, fundo_preco=None, topo_preco=None) -> "indicators.Niveis":
    """Niveis com os campos de Fibonacci já preenchidos (isola o cálculo de stop/RR)."""
    n = indicators.Niveis()
    n.entrada_zona = entrada_zona
    n.alvo = alvo
    n.fib_retracoes = {"382": None, "500": None, "618": None}
    n.pivos_ancora = {
        "fundo_ts": None, "fundo_preco": fundo_preco,
        "topo_ts": None, "topo_preco": topo_preco,
    }
    return n


def test_niveis_stop_swing_mais_distante():
    # Alta: swing-low (90) é MAIS DISTANTE da entrada (97) que ATR×m (97-3=94) → stop == swing (D-08).
    cfg = _cfg_ind()
    n = _niveis_com_fib((95.0, 99.0), alvo=120.0, fundo_preco=90.0)   # entrada_ref=97
    ctx = indicators.ContextoTendencia("alta", "alinhado_alta")
    indicators._niveis_stop_rr(n, ctx, _atr_const(2.0), None, cfg)    # m=1.5 → atr_stop=94
    assert n.stop == pytest.approx(90.0)


def test_niveis_stop_atr_mais_distante():
    # Alta: ATR×m é MAIS DISTANTE (97-15=82) que o swing (90) → stop == atr_stop (D-08).
    cfg = _cfg_ind()
    m = cfg["indicadores"]["stop_atr_m"]
    n = _niveis_com_fib((95.0, 99.0), alvo=120.0, fundo_preco=90.0)   # entrada_ref=97
    ctx = indicators.ContextoTendencia("alta", "alinhado_alta")
    indicators._niveis_stop_rr(n, ctx, _atr_const(10.0), None, cfg)
    assert n.stop == pytest.approx(97.0 - m * 10.0)                   # 82


def test_niveis_stop_baixa_mais_alto():
    # Baixa: stop é o MAIS DISTANTE para CIMA → max(swing=topo, atr_stop) (D-08).
    cfg = _cfg_ind()
    n = _niveis_com_fib((101.0, 105.0), alvo=80.0, topo_preco=110.0)  # entrada_ref=103
    ctx = indicators.ContextoTendencia("baixa", "alinhado_baixa")
    indicators._niveis_stop_rr(n, ctx, _atr_const(2.0), None, cfg)    # atr_stop=103+3=106
    assert n.stop == pytest.approx(110.0)                            # swing (mais alto)


def test_niveis_rr_formatado():
    # R:R razão 2,5 → string "1 : 2,5" (vírgula decimal BR). entrada_ref=97, stop=90 (risco 7),
    # alvo=114.5 (retorno 17.5) → 17.5/7 = 2.5.
    cfg = _cfg_ind()
    n = _niveis_com_fib((95.0, 99.0), alvo=114.5, fundo_preco=90.0)
    ctx = indicators.ContextoTendencia("alta", "alinhado_alta")
    indicators._niveis_stop_rr(n, ctx, _atr_const(2.0), None, cfg)
    assert n.stop == pytest.approx(90.0)
    assert n.risco_retorno == "1 : 2,5"


def test_niveis_rr_risco_zero_indisponivel():
    # Risco == 0 (stop == entrada_ref, ATR=0 e swing==entrada_ref) → "indisponivel", NUNCA inf (D-09).
    cfg = _cfg_ind()
    n = _niveis_com_fib((97.0, 97.0), alvo=120.0, fundo_preco=97.0)
    ctx = indicators.ContextoTendencia("alta", "alinhado_alta")
    indicators._niveis_stop_rr(n, ctx, _atr_const(0.0), None, cfg)
    assert n.risco_retorno == "indisponivel"
    assert "inf" not in n.risco_retorno.lower()


def test_niveis_stop_rr_lateral_degrada():
    # dow lateral / sem entrada_zona → stop None e risco_retorno "indisponivel", sem exceção (D-09).
    cfg = _cfg_ind()
    n = indicators.Niveis()                              # entrada_zona/alvo None
    ctx = indicators.ContextoTendencia("lateral", "indisponivel")
    indicators._niveis_stop_rr(n, ctx, _atr_const(2.0), None, cfg)
    assert n.stop is None
    assert n.risco_retorno == "indisponivel"


def test_calcular_popula_stop_rr():
    # calcular popula stop (mais conservador) e risco_retorno (string), nunca infinito.
    cfg = _cfg_ind()
    t = np.arange(120)
    df = _frame_trend(50.0 + 5.0 * np.sin(t / 6.0) + 0.15 * t)   # alta
    sinais = indicators.calcular(df, cfg)
    assert sinais.contexto.dow_diario == "alta"
    assert sinais.niveis.stop is not None
    assert isinstance(sinais.niveis.risco_retorno, str)
    assert "inf" not in sinais.niveis.risco_retorno.lower()
    # stop em alta fica ABAIXO da entrada (proteção estrutural)
    entrada_ref = sum(sinais.niveis.entrada_zona) / 2.0
    assert sinais.niveis.stop < entrada_ref


def test_rr_usa_errstate():
    # D-09: o cálculo da razão R:R é protegido com np.errstate (nunca divisão por zero/inf).
    raiz = Path(__file__).resolve().parents[1]
    fonte = (raiz / "src" / "analista" / "core" / "indicators.py").read_text(encoding="utf-8")
    bloco = fonte[fonte.index("def _niveis_stop_rr"):]
    assert "errstate" in bloco
