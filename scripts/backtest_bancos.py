"""Wrapper standalone do BACKTEST-01 (D-09/D-10): roda a cesta de bancos e grava a
tabela-resumo RIM × 4 âncoras + PASS/FAIL em `out/backtest_bancos.md`.

Chama a MESMA `backtest.rodar_cesta` que o teste (Plan 05-04) usa → script e teste provam
o MESMO número (RESEARCH Open Q3). Offline e determinístico: lê os fixtures congelados
(snapshot + fair values), nunca toca a rede. `out/` é gitignored (linha 8) — a saída é
gerada, não versionada. Os desvios são REPORTADOS, não escondidos (D-12): um ticker fora
da banda ainda aparece com o veredito. A coluna de nota de exceção do v2.3 foi REMOVIDA na
Fase 14 (VAL-06) — nenhuma nota pode salvar um ticker.

Uso: python scripts/backtest_bancos.py
"""

from __future__ import annotations

import os
import sys

import yaml

# permite rodar como script standalone (sem depender de pip install -e .)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from tabulate import tabulate  # noqa: E402

from analista import backtest  # noqa: E402

CONFIG_PATH = os.path.join(ROOT, "config.yaml")
SNAPSHOT_PATH = os.path.join(ROOT, "tests", "fixtures", "snapshot_bancos_2026-07-12.yaml")
FAIR_VALUES_PATH = os.path.join(ROOT, "tests", "fixtures", "fair_values_bancos.yaml")
OUT_DIR = os.path.join(ROOT, "out")
DESTINO = os.path.join(OUT_DIR, "backtest_bancos.md")

HEADERS = [
    "Ticker", "Motor", "RIM", "Graham", "Bazin", "Preço", "FV faixa",
    "P/VP med", "P/L med", "Desvio RIM×FV", "PASS/FAIL",
]


def _num(v, casas: int = 2) -> str:
    """Formata float com `casas` decimais; None → '-'."""
    return "-" if v is None else f"{v:.{casas}f}"


def _pct(v) -> str:
    """Formata fração como percentual assinado; None → '-'."""
    return "-" if v is None else f"{v * 100:+.1f}%"


def _faixa(fv_min, fv_max) -> str:
    """Faixa de fair value como 'min–max'; '-' se ausente."""
    if fv_min is None or fv_max is None:
        return "-"
    return f"{fv_min:.2f}–{fv_max:.2f}"


def main() -> int:
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    empresas, rf_local, ipca_defl = backtest.carregar_snapshot(SNAPSHOT_PATH)
    fair_values = backtest.carregar_fair_values(FAIR_VALUES_PATH)
    cesta = backtest.rodar_cesta(empresas, fair_values, cfg, rf_local, ipca_defl)

    linhas = []
    for r in sorted(cesta, key=lambda x: x["ticker"]):
        linhas.append([
            r["ticker"],
            r["motor"] or "-",
            _num(r["rim"]),
            _num(r["graham"]),
            _num(r["bazin"]),
            _num(r["preco"]),
            _faixa(r["fv_min"], r["fv_max"]),
            _num(r["pvp_med"]),
            _num(r["pl_med"]),
            _pct(r["desvio"]),
            "PASS" if r["passa"] else "FAIL",
        ])

    md = tabulate(linhas, headers=HEADERS, tablefmt="github")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8") as fh:
        fh.write("# Backtest da cesta de bancos (BACKTEST-01)\n\n")
        fh.write(md)
        fh.write("\n")
    print(md)
    print(f"\n[salvo em {DESTINO}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
