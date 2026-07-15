"""DATA-04 — guarda de regressão do degrau artificial de split (o "~13% do ITUB4").

O spike `.planning/spikes/data-04-degrau-split.md` MEDIU que o degrau já não existe na série
por-ação de valuation: a ref do requisito (`prices.py:71-111`) é obsoleta, e o double-count foi
eliminado pelo firewall das Fases 3-4 (`serie_precos` = Close NOMINAL; o ajuste por split vive
só em `ohlc_ajustado`, que nunca cruza `num_acoes`) somado ao 09-02 (`num_acoes` = contagem
oficial da CVM por ano, que carrega a bonificação real UMA vez).

Estes testes TRAVAM essa ausência. O degrau reapareceria se alguém regredisse `serie_precos`
para o preço ajustado por split — e é exatamente essa regressão que os asserts reprovam.

Offline, zero rede (monkeypatch do yfinance, padrão de test_ingest_ohlc.py). Sem literal de
ticker real e sem R$ de nível: ticker SINTÉTICO + razões ADIMENSIONAIS ≈ 1 (BLIND-04a).
"""

import pandas as pd
import pytest

from analista.ingest import prices

# Bonificação sintética (não é R$ de ticker; é o fator do evento societário do cenário).
_FATOR_BONIF = 1.1286  # ≈ a bonificação ITUB4 2024→2025; o "~13%" do requisito
_PRECO_PRE = 30.0      # base nominal "cara" pré-bonificação (cenário sintético)
_ACOES_PRE = 1_000_000.0  # contagem de ações pré-bonificação (cenário sintético)
_I_SPLIT = 5           # índice do pregão do evento no hist sintético


def _hist_bonificacao():
    """Hist OHLCV com UMA bonificação de fator `_FATOR_BONIF` no pregão `_I_SPLIT`.

    Convenção Yahoo (auto_adjust=False): o Close NOMINAL já cai no dia do evento. Os pregões
    pré-evento ficam na base "cara" (~`_PRECO_PRE`) e os pós na base "barata" (~`_PRECO_PRE`/F),
    reproduzindo a queda nominal que a bonificação provoca no preço.
    """
    idx = pd.date_range("2024-06-01", periods=10, freq="D")
    pos = _PRECO_PRE / _FATOR_BONIF
    close = pd.Series(
        [_PRECO_PRE] * _I_SPLIT + [pos] * (10 - _I_SPLIT),
        index=idx, dtype=float,
    )
    splits = pd.Series([0.0] * 10, index=idx)
    splits.iloc[_I_SPLIT] = _FATOR_BONIF
    return pd.DataFrame({
        "Open": close, "High": close, "Low": close, "Close": close,
        "Adj Close": close / _FATOR_BONIF,  # retroajustado — NUNCA a base de valuation
        "Volume": pd.Series([1000.0] * 10, index=idx),
        "Stock Splits": splits,
        "Dividends": pd.Series([0.0] * 10, index=idx),
    })


def _coletar(monkeypatch):
    class _Tk:
        def history(self, *a, **k):
            return _hist_bonificacao()

        @property
        def dividends(self):
            return pd.Series(dtype=float)

    class _YF:
        @staticmethod
        def Ticker(sym):
            return _Tk()

    monkeypatch.setattr(prices, "_yf", lambda: _YF())
    monkeypatch.setattr(prices.time, "sleep", lambda *_: None)
    monkeypatch.setattr(prices, "_fetch_info", lambda tk: {})
    return prices.coletar_mercado("BON3")


def test_serie_precos_de_valuation_preserva_a_queda_nominal_da_bonificacao(monkeypatch):
    """`serie_precos` (base do valuation) NÃO é ajustada por split: a queda nominal na data da
    bonificação continua lá. Se regredisse para o preço ajustado, a queda sumiria e a razão iria
    a ≈ 1 (contínua) — e o degrau voltaria ao cruzar com `num_acoes`."""
    dm = _coletar(monkeypatch)
    serie = dm.serie_precos
    razao_na_fronteira = serie.iloc[_I_SPLIT] / serie.iloc[_I_SPLIT - 1]
    # a queda nominal (~1/F) está preservada: claramente MENOR que 1 (não foi ajustada)
    assert razao_na_fronteira < 0.95, razao_na_fronteira
    assert razao_na_fronteira == pytest.approx(1.0 / _FATOR_BONIF, rel=1e-6)


def test_sem_degrau_no_produto_preco_nominal_x_num_acoes_na_bonificacao(monkeypatch):
    """O double-count (degrau artificial) NÃO existe: com a bonificação, `num_acoes` sobe ×F e o
    preço NOMINAL cai ×(1/F), então o produto (proxy de market cap) atravessa a fronteira SEM
    salto — razão ADIMENSIONAL ≈ 1. Se `serie_precos` fosse o preço ajustado por split, o produto
    saltaria ×F (o degrau), e este assert ficaria vermelho."""
    dm = _coletar(monkeypatch)
    serie = dm.serie_precos
    preco_pre = serie.iloc[_I_SPLIT - 1]
    preco_pos = serie.iloc[_I_SPLIT]
    # num_acoes carrega a bonificação real UMA vez (contagem CVM por ano, 09-02)
    acoes_pre = _ACOES_PRE
    acoes_pos = _ACOES_PRE * _FATOR_BONIF
    proxy_pre = preco_pre * acoes_pre
    proxy_pos = preco_pos * acoes_pos
    razao = proxy_pos / proxy_pre
    # continuidade: bonificação não cria nem destrói valor de mercado → razão ≈ 1 (sem degrau)
    assert razao == pytest.approx(1.0, rel=1e-6), razao


def test_ajuste_por_split_fica_confinado_ao_ohlc_ajustado(monkeypatch):
    """O ajuste por split existe (ohlc_ajustado remove a queda), mas é TRILHO SEPARADO: nunca é o
    `serie_precos` do valuation. Trava o firewall — se `serie_precos` passar a ser o ajustado,
    a ponta pré-evento deixaria de coincidir com o nominal e este teste ficaria vermelho."""
    dm = _coletar(monkeypatch)
    hist = _hist_bonificacao()
    # ohlc_ajustado É contínuo na fronteira (queda removida) — trilho dos indicadores
    aj = dm.ohlc_ajustado
    razao_aj = aj["Close"].iloc[_I_SPLIT] / aj["Close"].iloc[_I_SPLIT - 1]
    assert razao_aj == pytest.approx(1.0, rel=1e-3)
    # serie_precos é o NOMINAL cru (trilho do valuation), distinto do ajustado antes do evento
    assert dm.serie_precos.iloc[0] == hist["Close"].iloc[0]
    assert dm.serie_precos.iloc[0] != aj["Close"].iloc[0]
