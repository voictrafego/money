"""Robustez da resolução de tickers (offline): retry do Yahoo, _norm cirúrgico,
fallback token-set e não-regressão. Nenhum teste bate na rede."""

import pandas as pd
import pytest

from analista.ingest import prices, universe


# ---------------------------------------------------------------------------
# FIX 1 — retry de fetch no coletar_mercado
# ---------------------------------------------------------------------------

class _TkStub:
    """Ticker dummy: history/dividends vazios para não tocar a rede."""

    def history(self, *a, **k):
        return pd.DataFrame()

    @property
    def dividends(self):
        return pd.Series(dtype=float)


def _stub_yf(monkeypatch):
    class _YF:
        @staticmethod
        def Ticker(sym):
            return _TkStub()

    monkeypatch.setattr(prices, "_yf", lambda: _YF())


def test_retry_excecao_depois_sucesso(monkeypatch):
    _stub_yf(monkeypatch)
    monkeypatch.setattr(prices.time, "sleep", lambda *_: None)
    chamadas = {"n": 0}
    info_ok = {"longName": "Foo S.A.", "currentPrice": 12.34}

    def fake_fetch(tk):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            raise RuntimeError("rate limit")
        return info_ok

    monkeypatch.setattr(prices, "_fetch_info", fake_fetch)
    dm = prices.coletar_mercado("FOO3")
    assert dm.nome == "Foo S.A."
    assert dm.preco_atual == 12.34
    assert chamadas["n"] == 2


def test_retry_info_vazio_depois_sucesso(monkeypatch):
    _stub_yf(monkeypatch)
    monkeypatch.setattr(prices.time, "sleep", lambda *_: None)
    chamadas = {"n": 0}

    def fake_fetch(tk):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            return {}  # sem nome e sem preço -> tentativa falha
        return {"shortName": "Bar", "regularMarketPrice": 9.0}

    monkeypatch.setattr(prices, "_fetch_info", fake_fetch)
    dm = prices.coletar_mercado("BAR3")
    assert dm.nome == "Bar"
    assert dm.preco_atual == 9.0
    assert chamadas["n"] == 2


def test_retry_todas_falham_desiste_sem_excecao(monkeypatch):
    _stub_yf(monkeypatch)
    monkeypatch.setattr(prices.time, "sleep", lambda *_: None)
    chamadas = {"n": 0}

    def fake_fetch(tk):
        chamadas["n"] += 1
        raise RuntimeError("sempre falha")

    monkeypatch.setattr(prices, "_fetch_info", fake_fetch)
    dm = prices.coletar_mercado("ZZZ3")  # não deve propagar exceção
    assert dm.nome == ""
    assert dm.preco_atual is None
    assert chamadas["n"] == prices._MAX_TENTATIVAS


# ---------------------------------------------------------------------------
# FIX 2 — _norm cirúrgico
# ---------------------------------------------------------------------------

def test_norm_preserva_saneamento_sao():
    toks = universe._norm("CIA SANEAMENTO BASICO ESTADO SAO PAULO").split()
    assert "saneamento" in toks
    assert "sao" in toks
    assert "neamento" not in toks  # o bug do str.replace(' sa', ' ') geraria isto


def test_norm_preserva_sabesp():
    n = universe._norm("Companhia de Saneamento Basico do Estado de Sao Paulo - SABESP")
    assert "sabesp" in n
    assert "besp" not in n.split()


def test_norm_remove_sufixo_juridico():
    n = universe._norm("Itau Unibanco S.A.")
    assert "itau" in n
    assert "unibanco" in n
    assert "s a" not in n
    assert "sa" not in n.split()


def test_norm_remove_sa_barra_e_ltda():
    assert "sa" not in universe._norm("Energisa S/A").split()
    assert "ltda" not in universe._norm("X LTDA").split()
    # não corrompe "energisa"
    assert "energisa" in universe._norm("Energisa S/A")


# ---------------------------------------------------------------------------
# FIX 2 — fallback token-set em resolver + não-regressão
# ---------------------------------------------------------------------------

CADASTRO_SINTETICO = pd.DataFrame(
    [
        {"DENOM_SOCIAL": "CIA SANEAMENTO BASICO ESTADO SAO PAULO", "CD_CVM": 14443,
         "SETOR_ATIV": "Saneamento", "SIT": "ATIVO"},
        {"DENOM_SOCIAL": "BRASILAGRO CIA BRAS DE PROP AGRICOLAS", "CD_CVM": 20036,
         "SETOR_ATIV": "Agro", "SIT": "ATIVO"},
        {"DENOM_SOCIAL": "COMPANHIA DE SANEAMENTO DE MINAS GERAIS", "CD_CVM": 19445,
         "SETOR_ATIV": "Saneamento", "SIT": "ATIVO"},
        {"DENOM_SOCIAL": "TELEFONICA BRASIL S.A.", "CD_CVM": 17671,
         "SETOR_ATIV": "Telecom", "SIT": "ATIVO"},
        {"DENOM_SOCIAL": "TOTVS S.A.", "CD_CVM": 19992,
         "SETOR_ATIV": "Tech", "SIT": "ATIVO"},
        {"DENOM_SOCIAL": "COSAN S.A.", "CD_CVM": 19836,
         "SETOR_ATIV": "Energia", "SIT": "ATIVO"},
        {"DENOM_SOCIAL": "ENERGISA SA", "CD_CVM": 15253,
         "SETOR_ATIV": "Utilities", "SIT": "ATIVO"},
        {"DENOM_SOCIAL": "TIM S.A.", "CD_CVM": 24929,
         "SETOR_ATIV": "Telecom", "SIT": "ATIVO"},
    ]
).astype({"CD_CVM": "Int64"})


@pytest.fixture
def cadastro_sintetico(monkeypatch):
    universe.carregar_cadastro.cache_clear()  # descarta qualquer cache real prévio
    monkeypatch.setattr(universe, "carregar_cadastro", lambda: CADASTRO_SINTETICO.copy())
    monkeypatch.setattr(universe, "_carregar_override", lambda: {})
    yield
    # monkeypatch restaura carregar_cadastro (com lru_cache) ao final do teste


def test_tokenset_casa_agro3(cadastro_sintetico):
    cd, _ = universe.resolver(
        "AGRO3", "BrasilAgro - Companhia Brasileira de Propriedades Agricolas")
    assert cd == 20036


def test_tokenset_casa_sbsp3_sem_falso_positivo(cadastro_sintetico):
    cd, _ = universe.resolver(
        "SBSP3", "Companhia de Saneamento Basico do Estado de Sao Paulo - SABESP")
    assert cd == 14443  # não pode casar CSMG (19445)


def test_regressao_totvs(cadastro_sintetico):
    assert universe.resolver("TOTS3", "TOTVS S.A.")[0] == 19992


def test_regressao_cosan(cadastro_sintetico):
    assert universe.resolver("CSAN3", "Cosan S.A.")[0] == 19836


def test_regressao_energisa(cadastro_sintetico):
    assert universe.resolver("ENGI11", "Energisa S.A.")[0] == 15253


def test_regressao_tim(cadastro_sintetico):
    assert universe.resolver("TIMS3", "TIM S.A.")[0] == 24929
