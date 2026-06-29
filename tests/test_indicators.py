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
