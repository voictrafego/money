"""Indicadores macro do Banco Central (API SGS) — grátis.

Usado para: Selic (corte do DY nos filtros, Cap. 8) e IPCA (inflação BR para o CAPM).
API pública: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados
"""

from __future__ import annotations

from typing import Optional

import requests

SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/{n}?formato=json"

# Códigos das séries no SGS
SELIC_META = 432       # Meta Selic definida pelo Copom (% a.a.)
IPCA_12M = 13522       # IPCA acumulado em 12 meses (%)


def _ultimo_valor(codigo: int, n: int = 1, timeout: int = 20) -> Optional[float]:
    url = SGS_URL.format(codigo=codigo, n=n)
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        dados = resp.json()
        if not dados:
            return None
        return float(dados[-1]["valor"].replace(",", "."))
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def selic_meta() -> Optional[float]:
    """Meta Selic atual em fração (ex.: 0.105 para 10,5%). None se indisponível."""
    v = _ultimo_valor(SELIC_META)
    return v / 100.0 if v is not None else None


def ipca_12m() -> Optional[float]:
    """IPCA acumulado 12 meses em fração. None se indisponível."""
    v = _ultimo_valor(IPCA_12M)
    return v / 100.0 if v is not None else None


def selic_para_capm(fallback: float) -> float:
    """rf do CAPM local (Cap. 16/17): Selic ao vivo do BCB quando disponível, senão o
    fallback de config. Puro e sem exceção — espelha o padrão `selic_meta() or 0.105` já
    usado p/ o corte de DY nos entry points.

    Pureza da engine (FIX-03): isto é chamado SÓ nos pontos de entrada (cli/app), que
    resolvem o rf uma única vez e o injetam em `cfg['capm']['rf_local']`. `analisar_acao`
    NÃO chama esta função — permanece offline/determinística lendo o rf já resolvido.
    """
    return selic_meta() or fallback
