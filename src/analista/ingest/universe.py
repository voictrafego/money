"""Universo de empresas e mapeamento ticker -> CD_CVM.

Usa o cadastro oficial da CVM (cad_cia_aberta) como fonte do CD_CVM e do setor.
O ticker da B3 não existe no dado da CVM, então resolvemos o CD_CVM por:
  1) override manual em data/ticker_map.json  (ex.: {"ITUB4": 19348});
  2) casamento por nome (DENOM_SOCIAL x nome vindo do Yahoo).
"""

from __future__ import annotations

import json
import os
import unicodedata
from functools import lru_cache
from typing import Optional, Tuple

import pandas as pd
import requests

CAD_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
CAD_CACHE = os.path.join(DATA_DIR, "cvm", "cad_cia_aberta.csv")
TICKER_MAP = os.path.join(DATA_DIR, "ticker_map.json")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    for lixo in [" s.a.", " s/a", " sa", " s a", " holding", " participacoes", " do brasil",
                 " brasil", " companhia", " cia", " energia", " banco"]:
        s = s.replace(lixo, " ")
    return " ".join(s.split())


@lru_cache(maxsize=1)
def carregar_cadastro() -> Optional[pd.DataFrame]:
    os.makedirs(os.path.dirname(CAD_CACHE), exist_ok=True)
    if not os.path.exists(CAD_CACHE):
        try:
            resp = requests.get(CAD_URL, timeout=60)
            resp.raise_for_status()
            with open(CAD_CACHE, "wb") as f:
                f.write(resp.content)
        except requests.RequestException:
            return None
    try:
        df = pd.read_csv(CAD_CACHE, sep=";", encoding="latin-1", dtype={"CD_CVM": "Int64"})
    except (ValueError, FileNotFoundError):
        return None
    if "SIT" in df.columns:
        df = df[df["SIT"] == "ATIVO"]
    return df


def _carregar_override() -> dict:
    if os.path.exists(TICKER_MAP):
        try:
            with open(TICKER_MAP, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def resolver(ticker: str, nome_yahoo: str = "") -> Tuple[Optional[int], str]:
    """Resolve (CD_CVM, setor) para um ticker. CD_CVM None se não encontrado."""
    override = _carregar_override()
    cad = carregar_cadastro()
    chave = ticker.upper().replace(".SA", "")

    cd = override.get(chave)
    if cd is not None and cad is not None:
        linha = cad[cad["CD_CVM"] == int(cd)]
        setor = linha["SETOR_ATIV"].iloc[0] if not linha.empty and "SETOR_ATIV" in cad.columns else ""
        return int(cd), str(setor or "")

    if cad is None or not nome_yahoo:
        return (int(cd) if cd is not None else None, "")

    alvo = _norm(nome_yahoo)
    cad = cad.copy()
    cad["_n"] = cad["DENOM_SOCIAL"].map(_norm)
    # 1) match exato normalizado
    exato = cad[cad["_n"] == alvo]
    if not exato.empty:
        linha = exato.iloc[0]
    else:
        # 2) contém (escolhe o nome mais curto que contém o alvo ou vice-versa)
        cand = cad[cad["_n"].apply(lambda x: x in alvo or alvo in x) & (cad["_n"].str.len() > 2)]
        if cand.empty:
            return None, ""
        linha = cand.iloc[cand["_n"].str.len().argmin()]
    setor = str(linha.get("SETOR_ATIV", "") or "")
    return int(linha["CD_CVM"]), setor
