"""CLI do analista de dividendos.

Comandos:
  analyze TICKER          análise completa de uma ação (múltiplos + DDM) -> out/TICKER.md
  screen  --tickers ...   garimpo (Cap. 8): filtros + ranking BSD       -> out/screen_*.csv/.md
  rank    --tickers ...   ranking por múltiplos padronizados (Cap. 11)  -> out/rank_*.csv/.md
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import List, Optional

import yaml

from .core import comparables as cmp
from .core import multiples as mult
from .core import screening as sc
from .ingest import build, macro
from .report import report

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(ROOT, "out")
CONFIG_PATH = os.path.join(ROOT, "config.yaml")


def carregar_config(path: Optional[str] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _tickers(args) -> List[str]:
    if args.tickers:
        return [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if args.tickers_file and os.path.exists(args.tickers_file):
        with open(args.tickers_file, encoding="utf-8") as f:
            return [l.strip().upper() for l in f if l.strip() and not l.startswith("#")]
    return []


def _montar(tickers: List[str], cfg: dict):
    ano_base = cfg["universo"]["ano_base"]
    n = cfg["universo"]["anos_historico"]
    empresas = []
    for t in tickers:
        print(f"  · coletando {t} ...", file=sys.stderr)
        c = build.montar_empresa(t, ano_base, n)
        if c is None or not c.anos:
            print(f"    (sem dados suficientes para {t})", file=sys.stderr)
            continue
        empresas.append(c)
    return empresas


def cmd_analyze(args, cfg):
    os.makedirs(OUT_DIR, exist_ok=True)
    empresas = _montar([args.ticker.upper()], cfg)
    if not empresas:
        print("Não foi possível montar a empresa (verifique ticker e conexão).")
        return 1
    c = empresas[0]
    # FIX-03: resolve o rf do CAPM uma vez (Selic ao vivo do BCB, ou o fallback do config)
    # e injeta em cfg ANTES da engine — a rede vive aqui, no entry point; analisar_acao
    # permanece offline lendo cfg["capm"]["rf_local"].
    cfg["capm"]["rf_local"] = macro.selic_para_capm(cfg["capm"]["selic_fallback"])
    a = report.analisar_acao(c, cfg)
    md = report.relatorio_markdown(c, a, cfg)
    destino = os.path.join(OUT_DIR, f"{c.ticker}.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(md)
    print(md)
    print(f"\n[salvo em {destino}]", file=sys.stderr)
    return 0


def cmd_screen(args, cfg):
    os.makedirs(OUT_DIR, exist_ok=True)
    tickers = _tickers(args)
    if not tickers:
        print("Informe --tickers TAEE11,EGIE3,... ou --tickers-file caminho.txt")
        return 1
    empresas = _montar(tickers, cfg)
    if not empresas:
        return 1

    selic = macro.selic_meta() or 0.105
    print(f"Selic (corte do DY): {selic*100:.2f}%", file=sys.stderr)
    csc = cfg["screening"]["custom"]
    n = cfg["universo"]["anos_historico"]

    linhas = []
    for c in empresas:
        rc = sc.filtros_customizados(
            c, selic=selic, n_anos=n, volume_min=csc["volume_min_diario"], roe_min=csc["roe_min"],
        )
        linhas.append({
            "ticker": c.ticker, "nome": c.nome, "setor": c.setor,
            "passou_custom": rc.passou, **{f"c_{k}": v for k, v in rc.criterios.items()},
        })
    bsd = sc.bsd_ranking(empresas, pesos=cfg["screening"]["bsd"]["pesos"],
                         anos_media=cfg["screening"]["bsd"]["anos_media"],
                         winsor=cfg["screening"]["bsd"]["winsor"])
    bsd_map = {b["ticker"]: b for b in bsd}
    for l in linhas:
        b = bsd_map.get(l["ticker"], {})
        l["bsd"] = round(b.get("bsd") or 0, 1)
        l["bsd_acima_80"] = b.get("acima_de_80", False)
    linhas.sort(key=lambda x: x["bsd"], reverse=True)

    csv_path = os.path.join(OUT_DIR, "screen.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)

    print(f"\n{'TICKER':10} {'BSD':>6}  {'>80':>3}  {'CUSTOM':>6}  SETOR")
    for l in linhas:
        print(f"{l['ticker']:10} {l['bsd']:>6}  {'sim' if l['bsd_acima_80'] else 'nao':>3}  "
              f"{'PASS' if l['passou_custom'] else '-':>6}  {l['setor']}")
    print(f"\n[csv em {csv_path}]", file=sys.stderr)
    return 0


def cmd_rank(args, cfg):
    os.makedirs(OUT_DIR, exist_ok=True)
    tickers = _tickers(args)
    if not tickers:
        print("Informe --tickers ... para o ranking por múltiplos.")
        return 1
    empresas = _montar(tickers, cfg)
    if not empresas:
        return 1

    nomes, ML, ROE, PL, EY, DP = [], [], [], [], [], []
    for c in empresas:
        # FIX-04: ROE/LPA/payout de valuation saem dos métodos canônicos normalizados,
        # idênticos ao Analisar e ao Ranking do app. Inclui payout_valuation no lugar do
        # payout(ult) cru — alinha de quebra a divergência cli↔app pré-existente do payout.
        ult = c.ultimo_ano()
        lpa = c.lpa_valuation()
        nomes.append(c.ticker)
        ML.append(mult.margem_liquida(c.lucro_liquido.get(ult), c.vendas_liquidas.get(ult)))
        ROE.append(c.roe_valuation())
        PL.append(mult.preco_lucro(c.preco_atual, lpa))
        EY.append(mult.earnings_yield(lpa, c.preco_atual))
        DP.append(c.payout_valuation())

    ranking = cmp.ranking_por_multiplos(nomes, {"ML": ML, "ROE": ROE, "PL": PL, "EY": EY})

    # regressão P/L ~ f(DP, ROE) e preço-alvo, quando houver pares suficientes (Cap. 12)
    reg = cmp.ajustar_regressao_pl(PL, DP, ROE)
    alvos = {}
    if reg:
        for c in empresas:
            pa = cmp.preco_alvo_por_regressao(
                reg, c.payout_valuation(), c.roe_valuation(), c.lpa_valuation(), c.preco_atual)
            if pa:
                alvos[c.ticker] = pa

    print(f"\n{'#':>2} {'TICKER':10} {'NOTA':>6}  {'P/L alvo':>9}  {'UPSIDE':>7}")
    for i, r in enumerate(ranking, 1):
        pa = alvos.get(r["empresa"])
        alvo = f"{pa.preco_alvo:.2f}" if pa else "-"
        up = f"{pa.upside*100:.0f}%" if pa and pa.upside is not None else "-"
        nota = f"{r['nota']:.1f}" if r["nota"] is not None else "-"
        print(f"{i:>2} {r['empresa']:10} {nota:>6}  {alvo:>9}  {up:>7}")
    if reg:
        print(f"\nRegressão P/L = {reg.coeficientes[0]:.2f} + {reg.coeficientes[1]:.2f}·DP "
              f"+ {reg.coeficientes[2]:.2f}·ROE  (R²={reg.r2:.2f}, n={reg.n})", file=sys.stderr)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="analista", description="Analista de ações de dividendos")
    p.add_argument("--config", help="caminho do config.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("analyze", help="análise completa de uma ação")
    pa.add_argument("ticker")

    ps = sub.add_parser("screen", help="garimpo: filtros + ranking BSD (Cap. 8)")
    ps.add_argument("--tickers", help="lista separada por vírgula")
    ps.add_argument("--tickers-file", help="arquivo com um ticker por linha")
    ps.add_argument("--setor", help="(rótulo informativo)")

    pr = sub.add_parser("rank", help="ranking por múltiplos (Cap. 11)")
    pr.add_argument("--tickers", help="lista separada por vírgula")
    pr.add_argument("--tickers-file", help="arquivo com um ticker por linha")
    pr.add_argument("--setor", help="(rótulo informativo)")

    args = p.parse_args(argv)
    cfg = carregar_config(args.config)

    if args.cmd == "analyze":
        return cmd_analyze(args, cfg)
    if args.cmd == "screen":
        return cmd_screen(args, cfg)
    if args.cmd == "rank":
        return cmd_rank(args, cfg)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
