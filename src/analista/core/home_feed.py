"""Agregador read-only da Home (watchlist + notícias) — custo-zero, never-raise.

Módulo leve da landing page (Fase 18). Espelha o contrato de degradação graciosa
de `intraday.FrameOHLC`/`prices.coletar_mercado`: NENHUMA função levanta exceção
nem devolve None — qualquer falha vira estado (item com ``ok=False`` / feed pulado /
lista vazia). O que quebra degrada **por item**, nunca derruba a página.

Firewall D-06: este módulo é read-only e NÃO importa nenhuma engine
(report/build/indicators/multiples/screening/comparables/grafico) — nem no topo nem
por import tardio. Só reusa `ingest.prices` (resolução `.SA` + yfinance) e `feedparser`,
sempre por import TARDIO dentro das funções, para isolar as dependências pesadas e
manter os 283 goldens e a aba Analisar totalmente isolados.

Contratos (corpos preenchidos nos planos 02 watchlist / 03 notícias):
- cotacoes(tickers) -> list[dict]   (preço + variação do dia; never-raise)
- noticias()        -> list[dict]   (manchete + fonte + hora + link; never-raise)
"""

from __future__ import annotations

import re

# Watchlist default de dividendos (D-02) — todos líquidos e resolvem no Yahoo `.SA`.
DEFAULT_WATCHLIST = ("BBSE3", "TAEE11", "EGIE3", "ITUB4", "BBAS3")
MAX_WATCHLIST = 5  # teto fixo: limita as chamadas ao Yahoo (D-02)

# Defesa V5 (input do usuário → símbolo Yahoo): 4 a 6 chars A-Z0-9.
_TICKER_RE = re.compile(r"^[A-Z0-9]{4,6}$")


def validar_ticker(t):
    """Normaliza e valida um ticker (defesa V5). Nunca levanta.

    Devolve o ticker em maiúsculas/sem espaços se casar ``^[A-Z0-9]{4,6}$``,
    senão None. Rejeita antes de qualquer uso em `yahoo_symbol()`/HTML.
    """
    try:
        t = str(t).strip().upper()
    except Exception:
        return None
    return t if _TICKER_RE.match(t) else None


def cotacoes(tickers):
    """Preço atual + variação do dia de cada ticker da watchlist. Never-raise.

    Contrato (corpo no plano 02): recebe uma tupla de tickers e devolve
    ``list[dict]`` no formato ``{"ticker": str, "preco": float|None,
    "pct": float|None, "ok": bool}`` — uma entrada por ticker, degradando
    por item (``ok=False``) quando o Yahoo falha, sem derrubar a lista.
    Fetch em UMA chamada em lote via `prices.yahoo_symbol`/`_yf` (import tardio).

    Esqueleto: retorna lista vazia até o plano 02 preencher o fetch.
    """
    return []


def noticias():
    """Feed agregado de notícias de mercado (RSS). Never-raise.

    Contrato (corpo no plano 03): devolve ``list[dict]`` no formato
    ``{"fonte": str, "titulo": str, "resumo": str, "link": str, "quando":
    datetime|None}`` — merge de múltiplos feeds RSS (InfoMoney + Google News)
    via `feedparser` (import tardio), com try/except por feed, dedupe por
    título e ordenação por data desc. Feed fora do ar é pulado.

    Esqueleto: retorna lista vazia até o plano 03 preencher o parse RSS.
    """
    return []
