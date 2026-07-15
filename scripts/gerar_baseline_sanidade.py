"""Gera o BASELINE DOS SUJOS (D-05) — o golden de DETECÇÃO da Fase 8, régua do progresso
da Fase 9. Roda 100% OFFLINE sobre o snapshot congelado dos 104 (plano 08-03): não toca a
rede, logo é determinístico e o EQTL3 (a 0,5% do limiar do SAN-01) NÃO pisca.

Para cada ticker: `aplicar_sanidade(c)` e serializa SÓ `confianca` + `flags` (cada flag é
`{check, bucket}`). NENHUM R$, nenhum preço, nenhum market_cap, nenhuma magnitude exata
(D-05/D-07). O `bucket` é uma STRING (`~1e0`, `~1e3`, `~1e-3`) — não é constante numérica,
logo o detector do BLIND-04a nem se aproxima, e um re-download do Yahoo mexendo no terceiro
decimal não muda o bucket.

Tickers limpos entram com `flags: []` e `confianca: alta` — a AUSÊNCIA de flag é informação
tão versionada quanto a presença (é o que torna a RESSURREIÇÃO de uma flag detectável).
Tickers sem insumo entram com `confianca: nao_avaliada`.

Uso: PYTHONPATH=src .venv/bin/python scripts/gerar_baseline_sanidade.py
"""

from __future__ import annotations

import os
import sys

# permite rodar como script standalone (sem depender de pip install -e .)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import yaml  # noqa: E402

import helpers_sanidade as hs  # noqa: E402
from analista.core import sanidade  # noqa: E402

DESTINO = os.path.join(ROOT, "tests", "fixtures", "baseline_sanidade.yaml")

# Cabeçalho versionado JUNTO com o arquivo (para o próximo leitor e a auditoria do BLIND-01).
CABECALHO = """\
# baseline_sanidade.yaml — o BASELINE DOS SUJOS (Fase 8 / plano 08-06).
#
# GERADO por scripts/gerar_baseline_sanidade.py — offline, idempotente. NÃO edite à mão.
#
# Isto é um golden de DETECÇÃO, não de nível. Ele NÃO trava um método nem um número em reais
# — trava QUAIS flags disparam por ticker. É por isso que não viola o BLIND-04a e é por isso
# que vive em YAML (nenhum literal de ticker no AST de um teste; helpers_blindagem.py:286-292).
#
# A lista de sujos só pode ENCOLHER (D-06). Se um par (ticker, check) sumir, foi a Fase 9
# consertando o dado. Se um par RESSUSCITAR, foi uma regressão — e o teste fica vermelho.
# SE VOCÊ ESTÁ TENTADO A "ATUALIZAR" ESTE ARQUIVO PARA DEIXAR A SUÍTE VERDE, PARE — é
# exatamente o reflexo que produziu o overfit do v2.3 (dois erros se anulando).
#
# O `bucket` é ordem de grandeza (string ~1eN), não magnitude. Se o bucket mudar sem a flag
# sumir, a escala não foi consertada — foi só empurrada, e o teste de bucket quebra.
#
# confianca ∈ {alta, media, baixa, nao_avaliada}. flags: [] + confianca: alta = ticker limpo
# (a ausência de flag é versionada tão a sério quanto a presença).
"""


def _flags_do_ticker(c) -> list:
    """Conjunto ordenado e ÚNICO de {check, bucket} de `c.avisos`. Sem R$, sem magnitude
    exata — só a ordem de grandeza (bucket, string). Ordenado para diff estável."""
    pares = sorted({(a.check, a.bucket) for a in c.avisos})
    return [{"check": ck, "bucket": bk} for ck, bk in pares]


def main() -> int:
    empresas = hs.carregar_snapshot_sanidade()
    if not empresas:
        print("FALHA: snapshot vazio — baseline NÃO gerado.", file=sys.stderr)
        return 1

    baseline: dict = {}
    for tk, c in empresas.items():
        sanidade.aplicar_sanidade(c)
        baseline[tk] = {
            "confianca": c.confianca,
            "flags": _flags_do_ticker(c),
        }

    corpo = yaml.safe_dump(
        baseline, allow_unicode=True, sort_keys=True, default_flow_style=False
    )
    with open(DESTINO, "w", encoding="utf-8") as fh:
        fh.write(CABECALHO)
        fh.write(corpo)

    sujos = sum(1 for v in baseline.values() if v["flags"])
    pares = sum(len(v["flags"]) for v in baseline.values())
    print(
        f"[baseline gravado em {DESTINO}] — {len(baseline)} tickers, "
        f"{sujos} sujos, {pares} pares (ticker, check-bucket).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
