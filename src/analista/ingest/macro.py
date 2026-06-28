"""Indicadores macro do Banco Central (API SGS) — grátis.

Usado para: Selic (corte do DY nos filtros, Cap. 8) e IPCA (inflação BR para o CAPM).
API pública: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados
"""

from __future__ import annotations

import datetime
import time
from typing import List, Optional

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


def _selic_historico(anos: int = 10) -> List[float]:
    """Meta Selic diária dos últimos `anos` anos, em fração (lista). [] em qualquer falha.

    Consulta por intervalo de datas: a série diária 432 do SGS limita `/ultimos` a 20 pontos
    e a janela diária a 10 anos — por isso usamos dataInicial/dataFinal logo abaixo de 10 anos.
    """
    hoje = datetime.date.today()
    ini = hoje - datetime.timedelta(days=anos * 365)  # < 10 anos exatos (respeita a trava do BCB)
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{SELIC_META}/dados"
        f"?formato=json&dataInicial={ini.strftime('%d/%m/%Y')}&dataFinal={hoje.strftime('%d/%m/%Y')}"
    )
    # O SGS é intermitente (timeouts esporádicos por IP); re-tenta antes de degradar p/ a Selic
    # spot — assim uma falha pontual não congela o rf no pico de ciclo (a sidebar cacheia 1h).
    for tentativa in range(3):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            dados = resp.json()
            if isinstance(dados, list) and dados:
                return [float(d["valor"].replace(",", ".")) / 100.0 for d in dados]
        except (requests.RequestException, ValueError, KeyError, TypeError):
            pass
        if tentativa < 2:
            time.sleep(0.5 * (tentativa + 1))
    return []


def selic_ciclo_para_capm(fallback: float, anos: int = 10) -> float:
    """rf do CAPM/DDM = Selic MÉDIA dos últimos `anos` anos (through-the-cycle).

    Numa perpetuidade (DDM), a taxa de desconto deve refletir o juro de LONGO PRAZO, não o
    pico de ciclo: a Selic spot (ex.: 14,25%) infla o Ke e subavalia todo o mercado de
    dividendos. A média de ~10 anos da meta Selic (BCB) é um rf "through-the-cycle" objetivo
    e auto-atualizável. Degradação graciosa: sem a série histórica → Selic spot
    (`selic_para_capm`) → fallback de config. Chamado SÓ nos entry points (a engine lê cfg e
    permanece determinística).
    """
    hist = _selic_historico(anos)
    if hist:
        return sum(hist) / len(hist)
    return selic_para_capm(fallback)
