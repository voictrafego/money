"""Harness de validação BACKTEST-01 (VAL-01/VAL-02) — CONSOME o motor, nunca reimplementa.

`rodar_cesta` é PURA (sem I/O, sem rede): recebe os `CompanyData` reconstruídos do snapshot
congelado (`carregar_snapshot`) + as faixas de fair value (`carregar_fair_values`) + o `cfg`
+ o `rf_local` congelado, roda `report.analisar_acao` por ticker (FONTE ÚNICA do intrínseco
RIM calibrado da Fase 4) e triangula as 4 âncoras de realidade:

  (a) Graham + Bazin   — lentes clássicas (core/lentes)
  (b) preço de mercado — c.preco_atual (âncora do próprio snapshot)
  (c) faixa FV         — consenso aprovado (tests/fixtures/fair_values_bancos.yaml)
  (d) múltiplos de par — medianas de P/VP e P/L da PRÓPRIA cesta (D-11), zero fonte externa

O teste (Plan 05-04) e o script (`scripts/backtest_bancos.py`) chamam a MESMA `rodar_cesta`
→ provam o mesmo resultado. A fórmula RIM NÃO é reimplementada aqui (se a Fase 4 recalibrar
via loop D-12, re-roda-se o snapshot; este harness não muda).
"""

from __future__ import annotations

import statistics
from typing import List, Optional, Tuple

import yaml

from .core import lentes
from .core.fundamentals import CompanyData
from .report import report

# D-07: banda de tolerância ±15% em torno das bordas da faixa de fair value.
BANDA_PASS = 0.15

# chaves globais do snapshot que NÃO são tickers (carimbos de captura).
_CHAVES_GLOBAIS = {"data_base", "rf_local", "ipca_deflatores"}

# séries anuais reconstruídas no CompanyData (obrigatórias + display).
_SERIES = (
    "lucro_liquido",
    "patrimonio_liquido",
    "num_acoes",
    "dividendos",
    "vendas_liquidas",
    "fco",
)


def carregar_snapshot(caminho: str) -> Tuple[List[CompanyData], float, dict]:
    """Lê o snapshot YAML congelado e reconstrói os `CompanyData` + os carimbos globais.

    Congela raw fundamentals (não `vpa0/roe0/ke` derivados) → imune a mudança de assinatura
    interna de `motores.rim`. Devolve `(empresas, rf_local, ipca_deflatores)` para o caller
    injetar no cfg — o `ipca_deflatores` (PRIM-04) é carimbo global aditivo lido offline como o
    `rf_local`; ausente/vazio → {} (o motor cíclico degrada para a série nominal, never-raise).
    """
    with open(caminho, encoding="utf-8") as fh:
        snap = yaml.safe_load(fh)

    rf_local = float(snap["rf_local"])
    ipca_deflatores = snap.get("ipca_deflatores") or {}
    empresas: List[CompanyData] = []
    for tk, dados in snap.items():
        if tk in _CHAVES_GLOBAIS:
            continue
        c = CompanyData(
            ticker=tk,
            nome=dados.get("nome", ""),
            setor=dados.get("setor", ""),
            anos=[int(a) for a in dados.get("anos", [])],
        )
        c.preco_atual = dados.get("preco_atual")
        c.beta = dados.get("beta")
        c.dpa_trailing_12m = dados.get("dpa_trailing_12m")
        for serie in _SERIES:
            valores = dados.get(serie) or {}
            destino = getattr(c, serie)
            for ano, valor in valores.items():
                destino[int(ano)] = float(valor)
        empresas.append(c)
    return empresas, rf_local, ipca_deflatores


def carregar_fair_values(caminho: str) -> dict:
    """Lê o YAML das faixas de fair value (âncora-verdade do gate, D-03)."""
    with open(caminho, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _graham(c: CompanyData) -> Optional[float]:
    """Âncora (a) Graham: √(22,5×LPA×VPA) com LPA/VPA canônicos (app.py:1053-1069)."""
    ult = c.ultimo_ano()
    _vpa = lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))
    return lentes.preco_justo_graham(c.lpa_valuation(), _vpa)


def _bazin(c: CompanyData) -> Optional[float]:
    """Âncora (a) Bazin: DPA médio (5 anos-calendário) ÷ DY-mínimo (6%)."""
    dpas = [c.dpa(ano) for ano in c.anos_ordenados()]
    return lentes.preco_teto_bazin(lentes.dpa_medio(dpas, n=5))


def _passa(rim: Optional[float], fv_min: Optional[float], fv_max: Optional[float]) -> bool:
    """PASS por ticker (D-07): RIM dentro da faixa FV ±15%. RIM None → fora-da-banda (FAIL)."""
    if rim is None or fv_min is None or fv_max is None:
        return False
    return fv_min * (1 - BANDA_PASS) <= rim <= fv_max * (1 + BANDA_PASS)


def rodar_cesta(
    empresas: List[CompanyData],
    fair_values: dict,
    cfg: dict,
    rf_local: float,
    ipca_deflatores: Optional[dict] = None,
) -> List[dict]:
    """Roda o RIM calibrado nos bancos (offline) e triangula as 4 âncoras — 1 dict por ticker.

    Injeta `rf_local` e `ipca_deflatores` carimbados numa CÓPIA local do cfg (não muta o dict do
    chamador — função pura); `analisar_acao` NÃO muta o cfg, então é seguro rodar os 4 bancos com
    o MESMO dict. O `ipca_deflatores` (PRIM-04) só é consumido pelo motor cíclico — os bancos
    roteiam para o RIM, então aqui degrada para {} (série nominal, never-raise). O intrínseco RIM
    vem de `analisar_acao(...).intrinseco_motor` (never-raise: None → fora-da-banda).
    """
    cfg = {
        **cfg,
        "capm": {**cfg.get("capm", {}), "rf_local": rf_local},
        "macro": {**cfg.get("macro", {}), "ipca_deflatores": ipca_deflatores or {}},
    }

    # âncora (d): medianas de P/VP e P/L da PRÓPRIA cesta (D-11), agregação do harness.
    pares = [lentes.metricas_par(c) for c in empresas]
    pvps = [p.pvp for p in pares if p.pvp is not None]
    pls = [p.pl for p in pares if p.pl is not None]
    pvp_med = statistics.median(pvps) if pvps else None
    pl_med = statistics.median(pls) if pls else None

    resultados: List[dict] = []
    for c in empresas:
        a = report.analisar_acao(c, cfg)
        rim = a.intrinseco_motor  # never-raise: pode ser None → fora-da-banda
        fv = fair_values.get(c.ticker) or {}
        fv_min = fv.get("min")
        fv_max = fv.get("max")

        # desvio RIM×FV = distância relativa do RIM ao ponto médio da faixa de consenso.
        desvio: Optional[float] = None
        if rim is not None and fv_min is not None and fv_max is not None:
            fv_mid = (fv_min + fv_max) / 2.0
            if fv_mid:
                desvio = rim / fv_mid - 1.0

        resultados.append(
            {
                "ticker": c.ticker,
                "motor": a.motor,
                "arquetipo": a.arquetipo,
                "rim": rim,
                "graham": _graham(c),
                "bazin": _bazin(c),
                "preco": c.preco_atual,
                "fv_min": fv_min,
                "fv_max": fv_max,
                "pvp_med": pvp_med,
                "pl_med": pl_med,
                "desvio": desvio,
                "passa": _passa(rim, fv_min, fv_max),
                "excecao_nota": fv.get("excecao_nota"),
            }
        )
    return resultados
