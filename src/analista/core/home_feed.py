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

# --- Notícias (plano 03) -------------------------------------------------- #
# Índice de notícias em horário de Brasília (Pitfall 6: pubDate vem em UTC/GMT).
_TZ_B3 = "America/Sao_Paulo"

# User-Agent de browser: InfoMoney (WordPress/Cloudflare) throttla requisições
# "de robô" e devolve feed truncado/bozo (Pitfall 3). Sem isto o feed cai.
_UA = "Mozilla/5.0 (compatible; AnalistaDividendos/1.0)"

# Fontes RSS abertas (D-03), validadas ao vivo (18-RESEARCH Q6). InfoMoney é a
# fonte primária de submanchete; Google News BR complementa a cobertura.
_FEEDS = {
    "InfoMoney": "https://www.infomoney.com.br/mercados/feed/",
    "Google News": ("https://news.google.com/rss/search?"
                    "q=mercado+financeiro+bolsa+dividendos+when:1d"
                    "&hl=pt-BR&gl=BR&ceid=BR:pt-419"),
}

# Remove tags de markup do resumo (submanchete). O Google News entrega HTML pobre
# (âncoras) no summary — vira texto limpo; defesa em profundidade sobre o feedparser.
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _texto_limpo(s):
    """Tira tags HTML e colapsa espaços do resumo RSS (untrusted → texto puro)."""
    try:
        return _WS_RE.sub(" ", _HTML_TAG_RE.sub("", str(s or ""))).strip()
    except Exception:
        return ""


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

    Implementação (plano 02): uma única `yf.download` em lote (nunca um loop por
    ticker — anti-429), `period` FIXO "5d" (nunca derivado do input, senão exceder o
    teto retorna frame vazio). Variação do dia = ``close[-1]/close[-2]-1`` sobre barras
    diárias (robusto a fim de semana/pré-abertura, Pitfall 2). Cada ticker em try/except
    próprio → item degrada para ``ok=False`` sem derrubar a lista. Nunca levanta.
    """
    tickers = tuple(tickers)
    if not tickers:
        return []

    from ..ingest import prices  # import tardio: isola o yfinance pesado (firewall D-06)

    syms = [prices.yahoo_symbol(t) for t in tickers]

    try:
        yf = prices._yf()
        df = yf.download(
            " ".join(syms),
            period="5d",
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )
    except Exception:
        df = None

    out = []
    for t, sym in zip(tickers, syms):
        try:
            close = df[sym]["Close"].dropna()  # KeyError/AttributeError se ausente/df=None
            preco = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            pct = preco / prev - 1.0
            out.append({"ticker": t, "preco": preco, "pct": pct, "ok": True})
        except Exception:
            out.append({"ticker": t, "preco": None, "pct": None, "ok": False})
    return out


def noticias():
    """Feed agregado de notícias de mercado (RSS). Never-raise.

    Contrato (corpo no plano 03): devolve ``list[dict]`` no formato
    ``{"fonte": str, "titulo": str, "resumo": str, "link": str, "quando":
    datetime|None}`` — merge de múltiplos feeds RSS (InfoMoney + Google News)
    via `feedparser` (import tardio), com try/except por feed, dedupe por
    título e ordenação por data desc. Feed fora do ar é pulado.

    Implementação (plano 03): para cada feed em `_FEEDS`, `feedparser.parse(url,
    agent=_UA)` em try/except próprio (fonte que cai é pulada, não derruba as demais).
    Cada entry (até 20/feed) vira dict fonte/titulo/resumo/link/quando: título/resumo
    como TEXTO untrusted (resumo com tags HTML removidas), link só se começar com
    `https://` (senão string vazia — V5/T-18-07), e `published_parsed` (UTC struct_time)
    convertido para America/Sao_Paulo (Pitfall 6; None se o feed não trouxe data).
    Ao final: sort por data desc (itens sem data ao fim) + dedupe por título
    normalizado (strip+lower). NUNCA levanta — se tudo falhar, retorna [].
    """
    from datetime import datetime, timezone  # import tardio: leve, mas mantém o topo limpo

    try:
        import feedparser  # import tardio (firewall D-06: nenhuma engine); fallback → []
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(_TZ_B3)
    except Exception:
        return []

    itens = []
    for fonte, url in _FEEDS.items():
        try:
            fp = feedparser.parse(url, agent=_UA)  # nunca deveria levantar, mas blindamos
            entries = list(fp.entries)[:20]
        except Exception:
            continue  # feed fora do ar / throttle → pula, não derruba os demais
        for e in entries:
            try:
                titulo = str(e.get("title", "") or "").strip()
                resumo = _texto_limpo(e.get("summary", ""))
                link = str(e.get("link", "") or "").strip()
                if not link.startswith("https://"):  # esquema seguro apenas (T-18-07)
                    link = ""
                ts = e.get("published_parsed")  # struct_time UTC (ou None)
                quando = (datetime(*ts[:6], tzinfo=timezone.utc).astimezone(tz)
                          if ts else None)
                itens.append({"fonte": fonte, "titulo": titulo,
                              "resumo": resumo, "link": link, "quando": quando})
            except Exception:
                continue  # entry malformada → pula item, feed segue

    # sort por data desc (sem data vai para o fim) — chave tz-aware homogênea
    _sem_data = datetime.min.replace(tzinfo=timezone.utc)
    itens.sort(key=lambda x: x["quando"] or _sem_data, reverse=True)

    # dedupe por título normalizado, preservando a ordem (mais recente vence)
    vistos, dedup = set(), []
    for it in itens:
        k = it["titulo"].strip().lower()
        if k and k not in vistos:
            vistos.add(k)
            dedup.append(it)
    return dedup
