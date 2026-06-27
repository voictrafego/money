"""Universo de empresas e mapeamento ticker -> CD_CVM.

Usa o cadastro oficial da CVM (cad_cia_aberta) como fonte do CD_CVM e do setor.
O ticker da B3 não existe no dado da CVM, então resolvemos o CD_CVM por:
  1) override manual em data/ticker_map.json  (ex.: {"ITUB4": 19348});
  2) casamento por nome (DENOM_SOCIAL x nome vindo do Yahoo).
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from functools import lru_cache
from typing import Optional, Tuple

import pandas as pd
import requests

CAD_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
CAD_CACHE = os.path.join(DATA_DIR, "cvm", "cad_cia_aberta.csv")
TICKER_MAP = os.path.join(DATA_DIR, "ticker_map.json")


# Tokens jurídicos/genéricos removidos só em FRONTEIRA DE PALAVRA — usar str.replace
# apagava substrings reais (" sa" dentro de "Saneamento" -> "neamento", "Sao" -> "o").
_LIXO_TOKENS = [
    "s.a.", "s/a", "sa", "s a", "ltda",
    "holding", "participacoes", "do brasil", "brasil",
    "companhia", "cia", "energia", "banco",
]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    # remove pontuação leve que separa tokens jurídicos (s.a. / s/a)
    s = s.replace(".", " ").replace("/", " ")
    for lixo in _LIXO_TOKENS:
        # \b...\b garante fronteira de palavra; "sa" não casa dentro de "saneamento"
        s = re.sub(r"\b" + re.escape(lixo) + r"\b", " ", s)
    return " ".join(s.split())


def _tokens_significativos(nome_norm: str) -> set:
    """Tokens de _norm com len>2 (descarta conectivos curtos sobreviventes)."""
    return {t for t in nome_norm.split() if len(t) > 2}


def _segmentos(nome: str) -> list:
    """Nome completo + segmentos separados por ' - ' (marca à parte, ex.: '... - SABESP')."""
    partes = [nome] + [p for p in nome.split(" - ") if p.strip()]
    # dedup preservando ordem
    vistos, out = set(), []
    for p in partes:
        if p not in vistos:
            vistos.add(p)
            out.append(p)
    return out


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


def _cd_de(raw) -> Optional[int]:
    """Extrai o CD_CVM de um valor do override (int direto ou dict {cd_cvm, setor})."""
    if isinstance(raw, dict):
        return raw.get("cd_cvm")
    return raw


def resolver(ticker: str, nome_yahoo: str = "") -> Tuple[Optional[int], str]:
    """Resolve (CD_CVM, setor). FIX-06 (item K): aplica override de setor display-only por
    ticker — quando o ticker traz `setor` no override (data/ticker_map.json), ele PREVALECE
    sobre o SETOR_ATIV da CVM, que às vezes classifica errado (ex.: VULC3 cai em 'Têxtil',
    mas Vulcabras é Calçados/Consumo Cíclico). O override é só de EXIBIÇÃO — nenhum cálculo
    de valuation consome setor; o CD_CVM segue resolvido normalmente."""
    chave = ticker.upper().replace(".SA", "")
    raw = _carregar_override().get(chave)
    setor_override = str(raw["setor"]) if isinstance(raw, dict) and raw.get("setor") else ""
    cd_override = _cd_de(raw)
    # Atalho 100% offline: cd + setor no override dispensam o cadastro CVM (sem rede).
    if cd_override is not None and setor_override:
        return int(cd_override), setor_override
    cd, setor = _resolver_base(ticker, nome_yahoo)
    return cd, (setor_override or setor)


def _resolver_base(ticker: str, nome_yahoo: str = "") -> Tuple[Optional[int], str]:
    """Resolução-base de (CD_CVM, setor): override de CD_CVM → match por nome → token-set."""
    override = _carregar_override()
    cad = carregar_cadastro()
    chave = ticker.upper().replace(".SA", "")

    cd = _cd_de(override.get(chave))
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
        return int(linha["CD_CVM"]), str(linha.get("SETOR_ATIV", "") or "")

    # 2) contém (escolhe o nome mais curto que contém o alvo ou vice-versa)
    cand = cad[cad["_n"].apply(lambda x: x in alvo or alvo in x) & (cad["_n"].str.len() > 2)]
    if not cand.empty:
        linha = cand.iloc[cand["_n"].str.len().argmin()]
        return int(linha["CD_CVM"]), str(linha.get("SETOR_ATIV", "") or "")

    # 3) fallback token-set (ADITIVO): nomes legais da CVM divergem do longName do
    #    Yahoo (ordem/abreviações), então casamos por sobreposição de tokens. Só roda
    #    quando exato E contém falharam; exige limiar p/ evitar falso-positivo.
    return _resolver_token_set(nome_yahoo, cad)


def _token_casa(token: str, alvo_tokens: set) -> bool:
    if token in alvo_tokens:
        return True
    # abreviação: prefixo de >=3 chars de um token do alvo (ou vice-versa)
    for a in alvo_tokens:
        n = min(len(token), len(a))
        if n >= 3 and (a.startswith(token) or token.startswith(a)):
            return True
    return False


def _resolver_token_set(nome_yahoo: str, cad: pd.DataFrame) -> Tuple[Optional[int], str]:
    # une tokens do nome completo e dos segmentos (' - SABESP', 'BrasilAgro - ...')
    alvo_tokens: set = set()
    for seg in _segmentos(nome_yahoo):
        alvo_tokens |= _tokens_significativos(_norm(seg))
    if len(alvo_tokens) < 2:
        return None, ""

    melhor = None
    melhor_score: tuple = ()
    for _, row in cad.iterrows():
        cvm_tokens = _tokens_significativos(row["_n"])
        if not cvm_tokens:
            continue
        # token casa se igual OU se um é prefixo do outro (abreviações CVM: "bras"~"brasileira",
        # "prop"~"propriedades") com pelo menos 3 chars no prefixo — evita casar ruído.
        comum = {t for t in cvm_tokens if _token_casa(t, alvo_tokens)}
        if len(comum) < 2:
            continue
        cobertos_cvm = comum  # tokens da CVM que encontraram correspondência no alvo
        jaccard = len(comum) / len(cvm_tokens | alvo_tokens) if (cvm_tokens | alvo_tokens) else 0.0
        subset = cobertos_cvm == cvm_tokens  # todo token da CVM casou no alvo
        # limiar de segurança: Jaccard >= 0.5 OU todos os tokens da CVM cobertos pelo alvo
        if not (jaccard >= 0.5 or subset):
            continue
        # score: mais tokens em comum melhor; empate -> nome CVM mais curto (menos tokens)
        score = (len(comum), -len(cvm_tokens), jaccard)
        if score > melhor_score:
            melhor_score = score
            melhor = row
    if melhor is None:
        return None, ""
    return int(melhor["CD_CVM"]), str(melhor.get("SETOR_ATIV", "") or "")
