"""Captura (DATA-06) dos 104 tickers da B3 com o dado **LIMPO** — o produto do código
já consertado pelos planos 09-01/02/03 (JCP no filtro amplo, base do controlador, `num_acoes`
da contagem oficial da CVM) — e o congela num fixture YAML versionado.

Ao contrário de `capturar_snapshot_sujo.py`, este fixture **NÃO é evidência intocada**: é o
objeto MEDIDO de "hoje", regenerável a partir do código atual. É ele que faz a monotonicidade
da Fase 8 (`pares_hoje ⊆ pares_baseline`) deixar de ser uma tautologia (sujo-vs-sujo) e passar a
ENCOLHER, provando ticker-a-ticker os consertos. A régua (`baseline_sanidade.yaml`) e a evidência
suja (`snapshot_sanidade_2026-07-14.yaml`) NÃO são tocadas aqui — três artefatos, três papéis.

A FORMA é idêntica ao `capturar_snapshot_sujo.py` (universo de `data/ticker_map.json`, degradação
por ticker never-raise SAN-06, mesmas SERIES_NUM, zero R$ derivado, congela `market_cap`+`splits`+
`origem_num_acoes`). As únicas diferenças são o `DATA_BASE`, o `DESTINO` e o papel do arquivo.
Tickers 404 no Yahoo (MRFG3 etc.) degradam para o bloco `falhas:` com a CVM intacta, como no sujo.

Uso: PYTHONPATH=src .venv/bin/python scripts/capturar_snapshot_limpo.py
"""

from __future__ import annotations

import os
import sys

import yaml

# permite rodar como script standalone (sem depender de pip install -e .)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import json  # noqa: E402

from analista.ingest import build, prices  # noqa: E402

DATA_BASE = "2026-07-15"
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
TICKER_MAP_PATH = os.path.join(ROOT, "data", "ticker_map.json")
DESTINO = os.path.join(
    ROOT, "tests", "fixtures", "snapshot_sanidade_limpo_2026-07-15.yaml"
)

# séries CVM/diagnóstico a congelar por ticker (todas {ano: float}).
SERIES_NUM = (
    "lucro_liquido",
    "lucro_controlador",
    "patrimonio_liquido",
    "pl_nao_controladores",
    "lpa_cvm",
    "dividendos",
    "proventos_filtro_amplo",
    "num_acoes",
    "dpa_por_ano",
)


def _f(v):
    """Coage p/ float nativo (evita tipos numpy no dump do YAML)."""
    return None if v is None else float(v)


def _serie(d):
    """{ano: valor} -> {int: float} nativo, descartando valores None."""
    return {int(a): float(v) for a, v in d.items() if v is not None}


def _serie_str(d):
    """{ano: str} -> {int: str} nativo (origem_num_acoes: cvm | yahoo_fallback)."""
    return {int(a): str(v) for a, v in d.items() if v is not None}


def _splits(d):
    """{data_iso: fator} -> {str: float} nativo. As datas já vêm string ISO do pipeline."""
    return {str(k): float(v) for k, v in (d or {}).items() if v is not None}


def _carregar_universo() -> list[str]:
    """Os tickers reais da B3, do `data/ticker_map.json` (mesma fonte de `tickers_conhecidos`)."""
    with open(TICKER_MAP_PATH, encoding="utf-8") as fh:
        dados = json.load(fh)
    return sorted(k for k in dados if not k.startswith("_"))


def main() -> int:
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    ano_base = cfg["universo"]["ano_base"]     # 2025
    n = cfg["universo"]["anos_historico"]      # 10

    tickers = _carregar_universo()
    print(f"[universo: {len(tickers)} tickers de ticker_map.json]", file=sys.stderr)

    # captura o `DadosMercado` cru que `montar_empresa` consome, sem 2ª chamada de rede:
    # embrulha `prices.coletar_mercado` (mesma referência que build.py usa) e guarda o último.
    _ultimo = {}
    _orig = prices.coletar_mercado

    def _coletar_capturando(ticker, *args, **kwargs):
        dm = _orig(ticker, *args, **kwargs)
        _ultimo["dm"] = dm
        return dm

    prices.coletar_mercado = _coletar_capturando

    snap: dict = {"data_base": DATA_BASE}
    falhas: dict = {}
    ok = 0

    try:
        for i, tk in enumerate(tickers, start=1):
            print(f"  · [{i}/{len(tickers)}] capturando {tk} ao vivo ...", file=sys.stderr)
            _ultimo.pop("dm", None)
            try:
                c = build.montar_empresa(tk, ano_base, n)
            except Exception as e:  # never-raise (SAN-06): degrade por ticker
                falhas[tk] = f"excecao na captura: {type(e).__name__}: {e}"
                print(f"    ! {tk} FALHOU (exceção): {e}", file=sys.stderr)
                continue

            if c is None or not c.anos:
                falhas[tk] = "montar_empresa devolveu vazio/None (CVM ausente)"
                print(f"    ! {tk} FALHOU (CVM ausente) — fora do snapshot", file=sys.stderr)
                continue

            dm = _ultimo.get("dm")
            entrada = {
                "nome": c.nome,
                "setor": c.setor,
                "anos": [int(a) for a in c.anos_ordenados()],
                # mercado (snapshot atual) — congelados p/ o baseline não piscar
                "preco_atual": _f(c.preco_atual),
                "shares_outstanding": _f(getattr(dm, "num_acoes", None)),
                "implied_shares_out": _f(c.implied_shares_outstanding),
                "market_cap": _f(c.market_cap),
                "beta": _f(c.beta),
                "splits": _splits(c.splits),
                "origem_num_acoes": _serie_str(c.origem_num_acoes),
            }
            for s in SERIES_NUM:
                entrada[s] = _serie(getattr(c, s))

            snap[tk] = entrada
            ok += 1

            # o MRFG3 (404 no Yahoo) é o caso vivo do SAN-06: CVM intacta, mercado ausente.
            # fica NO snapshot E registrado em `falhas:` — a ausência é visível, não silenciosa.
            if c.preco_atual is None and c.market_cap is None:
                falhas[tk] = "sem dado de mercado (Yahoo 404/vazio); lado CVM congelado"
                print(f"    ~ {tk}: CVM ok, mercado ausente (congelado sem mercado)", file=sys.stderr)
    finally:
        prices.coletar_mercado = _orig

    if ok == 0:
        print("FALHA: nenhum ticker capturado — snapshot NÃO gerado.", file=sys.stderr)
        return 1

    snap["falhas"] = falhas
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8") as fh:
        yaml.safe_dump(snap, fh, allow_unicode=True, sort_keys=True, default_flow_style=False)
    print(
        f"[snapshot LIMPO gravado em {DESTINO}] — {ok} capturados, {len(falhas)} em falhas:",
        file=sys.stderr,
    )
    for tk, motivo in sorted(falhas.items()):
        print(f"    falha {tk}: {motivo}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
