"""Gera o artefato versionado `data/beta_setorial.yaml` (KE-03, D-05).

Irmao offline de `scripts/capturar_snapshot_limpo.py`: carrega os 104 tickers do snapshot
LIMPO congelado (MESMA fonte determinística do Plano 04, sem tocar a rede), computa o mapa
`setor_normalizado -> mediana(beta cru)` via `macro.mapa_beta_setorial` (limiar estrutural 3)
e o dumpa ordenado. O artefato e' DERIVADO, nao digitado ("derivado, nao digitado", GROW-01):
regeneravel a qualquer momento a partir do dado real, auto-atualiza ao regenerar. A engine LE
este mapa carimbado em `cfg` e aplica Blume (`capm.beta_blume`) — nunca recomputa a mediana.

Uso: PYTHONPATH=src .venv/bin/python scripts/gerar_beta_setorial.py
"""

from __future__ import annotations

import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# `helpers_sanidade` (loader offline dos 104) vive em tests/; `macro`, em src/.
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import helpers_sanidade as hs  # noqa: E402
from analista.ingest import macro  # noqa: E402

DESTINO = os.path.join(ROOT, "data", "beta_setorial.yaml")
LIMIAR = 3  # estrutural: menor n em que a mediana rejeita 1 outlier (D-02). Nao e' knob.


def main() -> int:
    empresas = list(hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO).values())
    print(f"[universo: {len(empresas)} tickers do snapshot limpo]", file=sys.stderr)

    mapa = macro.mapa_beta_setorial(empresas, limiar=LIMIAR)
    if not mapa:
        print("FALHA: mapa vazio — artefato NAO gerado.", file=sys.stderr)
        return 1

    # floats nativos (evita tags numpy/!!python no dump), ordenado por setor.
    saida = {str(setor): float(mediana) for setor, mediana in mapa.items()}
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8") as fh:
        yaml.safe_dump(saida, fh, allow_unicode=True, sort_keys=True, default_flow_style=False)

    print(f"[beta_setorial gravado em {DESTINO}] — {len(saida)} setores (n>={LIMIAR}):",
          file=sys.stderr)
    for setor, mediana in sorted(saida.items()):
        print(f"    {setor}: {mediana:.4f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
