"""relatorio_sanidade.py — a ferramenta de trabalho da Fase 9 (SAN Wave 5, plano 08-06).

Mostra, por ticker, `confianca` + as flags de sanidade (com o bucket, ordem de grandeza), um
resumo por check e a CONTAGEM TOTAL DE SUJOS — o número que a Fase 9 persegue até ZERO. É por
aqui que o conserto do dado é medido ticker a ticker.

Dois modos:
  --snapshot  (DEFAULT)  roda sobre o snapshot congelado (plano 08-03). OFFLINE e determinístico.
  --ao-vivo              roda `build.montar_empresa` de verdade nos 104 tickers. É o modo que a
                         Fase 9 usa DEPOIS de consertar o dado, para ver as flags APAGAREM.

  --diff-baseline        imprime os pares (ticker, check) que SUMIRAM (progresso) e os que
                         RESSUSCITARAM (regressão) em relação a tests/fixtures/baseline_sanidade.yaml.

⚠️ EQTL3 no modo --ao-vivo: ele fica a ~0,5% do limiar do SAN-01 (fator medido 1,496 contra 1,5)
e vai OSCILAR entre flagado e não-flagado a cada mudança de preço do Yahoo. Isso NÃO é bug do
check — é o motivo de o baseline rodar sobre o snapshot congelado. Quem usar --ao-vivo precisa
saber, senão vai perseguir um fantasma. O EQTL3 é pego de forma ESTÁVEL pelo SAN-04 (100% CVM,
não oscila).

REGRAS DURAS (D-05/D-07/D-14):
  - Nenhum R$ na saída. Fatores são adimensionais e aparecem; valores em reais, NÃO.
  - Nada muda na tela do app (D-14): app.py NÃO é tocado. Acender "baixa confiança" a cliente
    pagante agora exporia 41/104 tickers como "dado suspeito" por semanas — decisão da Fase 13.

Uso: PYTHONPATH=src .venv/bin/python scripts/relatorio_sanidade.py [--ao-vivo] [--diff-baseline]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# permite rodar como script standalone (sem depender de pip install -e .)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import yaml  # noqa: E402

import helpers_sanidade as hs  # noqa: E402
from analista.core import sanidade  # noqa: E402

CAMINHO_BASELINE = os.path.join(ROOT, "tests", "fixtures", "baseline_sanidade.yaml")
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
TICKER_MAP_PATH = os.path.join(ROOT, "data", "ticker_map.json")
CHECKS = ("SAN-01", "SAN-02", "SAN-03", "SAN-04", "SAN-05")


def _empresas_snapshot() -> dict:
    """Modo default: reconstrói os 104 do snapshot congelado, OFFLINE."""
    return hs.carregar_snapshot_sanidade()


def _empresas_ao_vivo() -> dict:
    """Modo --ao-vivo: roda o pipeline REAL nos tickers de ticker_map.json, degradando por
    ticker (never-raise, SAN-06). É o modo com que a Fase 9 vê as flags apagarem — mas o EQTL3
    OSCILA no SAN-01 aqui (ver o cabeçalho do módulo)."""
    from analista.ingest import build  # import tardio: só o modo ao-vivo toca a rede

    with open(CONFIG_PATH, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    ano_base = cfg["universo"]["ano_base"]
    n = cfg["universo"]["anos_historico"]
    with open(TICKER_MAP_PATH, encoding="utf-8") as fh:
        tickers = sorted(k for k in json.load(fh) if not k.startswith("_"))

    empresas: dict = {}
    for i, tk in enumerate(tickers, start=1):
        print(f"  · [{i}/{len(tickers)}] {tk} ao vivo ...", file=sys.stderr)
        try:
            c = build.montar_empresa(tk, ano_base, n)
        except Exception as e:  # never-raise: degrade por ticker
            print(f"    ! {tk} falhou: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        if c is not None and c.anos:
            empresas[tk] = c
    return empresas


def _pares_de(empresas: dict) -> set:
    """Conjunto de pares (ticker, check) de hoje — após aplicar_sanidade."""
    pares = set()
    for tk, c in empresas.items():
        for a in c.avisos:
            pares.add((tk, a.check))
    return pares


def _pares_do_baseline() -> set:
    with open(CAMINHO_BASELINE, encoding="utf-8") as fh:
        b = yaml.safe_load(fh) or {}
    pares = set()
    for tk, dados in b.items():
        for fl in dados.get("flags") or []:
            pares.add((tk, fl["check"]))
    return pares


def _imprimir_tabela(empresas: dict) -> None:
    print(f"{'TICKER':<8} {'CONFIANCA':<13} FLAGS (check@bucket, fator adimensional)")
    print("-" * 78)
    for tk in sorted(empresas):
        c = empresas[tk]
        if c.avisos:
            flags = ", ".join(
                f"{a.check}@{a.bucket}(x{a.fator:.3g})" for a in c.avisos
            )
        else:
            flags = "—"
        print(f"{tk:<8} {c.confianca:<13} {flags}")


def _imprimir_resumo(empresas: dict) -> None:
    por_check = {ck: 0 for ck in CHECKS}
    for c in empresas.values():
        for ck in {a.check for a in c.avisos}:
            if ck in por_check:
                por_check[ck] += 1
    sujos = sum(1 for c in empresas.values() if c.avisos)
    print("\n== RESUMO POR CHECK (tickers que acendem) ==")
    for ck in CHECKS:
        print(f"  {ck}: {por_check[ck]}")
    print(f"\n== TOTAL DE TICKERS SUJOS: {sujos} de {len(empresas)} ==")
    print("   (o número que a Fase 9 persegue até ZERO)")


def _imprimir_diff(empresas: dict) -> None:
    hoje = _pares_de(empresas)
    base = _pares_do_baseline()
    sumidos = sorted(base - hoje)      # progresso: a Fase 9 consertou
    ressuscitados = sorted(hoje - base)  # regressão: uma flag voltou
    print("\n== DIFF vs baseline_sanidade.yaml ==")
    print(f"  SUMIDOS (progresso, {len(sumidos)}): {sumidos or '—'}")
    print(f"  RESSUSCITADOS (regressao, {len(ressuscitados)}): {ressuscitados or '—'}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Relatorio de sanidade dos dados (SAN). Veredito INTERNO (D-14): "
        "nada muda na tela do app. Nenhum valor em reais na saida (D-05/D-07).",
        epilog="EQTL3 no modo --ao-vivo OSCILA no SAN-01 (a 0,5%% do limiar) — e' o motivo do "
        "baseline rodar sobre o snapshot congelado; o SAN-04 o pega de forma estavel.",
    )
    modo = ap.add_mutually_exclusive_group()
    modo.add_argument("--snapshot", action="store_true", help="offline, snapshot congelado (default)")
    modo.add_argument("--ao-vivo", action="store_true", help="pipeline real nos 104 (toca a rede)")
    ap.add_argument("--diff-baseline", action="store_true", help="diff de pares vs o baseline")
    args = ap.parse_args()

    empresas = _empresas_ao_vivo() if args.ao_vivo else _empresas_snapshot()
    if not empresas:
        print("FALHA: nenhuma empresa carregada.", file=sys.stderr)
        return 1

    for c in empresas.values():
        sanidade.aplicar_sanidade(c)

    _imprimir_tabela(empresas)
    _imprimir_resumo(empresas)
    if args.diff_baseline:
        _imprimir_diff(empresas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
