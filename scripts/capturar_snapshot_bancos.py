"""Captura one-time (D-05) dos fundamentos dos 4 bancos da cesta e os congela num
fixture YAML versionado (D-04), para o backtest (BACKTEST-01) rodar 100% offline e
determinístico.

Roda UMA vez ao vivo (CVM + Yahoo + BCB, via `build.montar_empresa`). A rede vive
SÓ aqui: o teste (Plan 05-04) reconstrói o `CompanyData` a partir do YAML e roda
`report.analisar_acao` sem tocar a rede. Congela raw fundamentals (não `vpa0/roe0/ke`
derivados) — assim o teste fica imune a mudança de assinatura interna de `motores.rim`:
se a Fase 4 recalibrar (loop D-12), re-roda-se este script, não se reescreve o teste.

Por ticker também carimba a ROTA observada na captura (`motor_observado`,
`arquetipo_observado`, `intrinseco_motor_observado`) — crítico para antecipar a
exceção BBSE3 (D-08): a rota é LIDA, nunca assumida como "rim".

Uso: python scripts/capturar_snapshot_bancos.py
"""

from __future__ import annotations

import os
import sys

import yaml

# permite rodar como script standalone (sem depender de pip install -e .)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from analista.ingest import build  # noqa: E402
from analista.report import report  # noqa: E402

BANCOS = ["ITUB4", "BBAS3", "BBSE3", "BBDC4"]
DATA_BASE = "2026-07-12"
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
DESTINO = os.path.join(ROOT, "tests", "fixtures", "snapshot_bancos_2026-07-12.yaml")

# séries anuais mínimas que analisar_acao consome p/ um banco→RIM (RESEARCH Q2)
SERIES_OBRIGATORIAS = ["lucro_liquido", "patrimonio_liquido", "num_acoes", "dividendos"]
SERIES_OPCIONAIS = ["vendas_liquidas", "fco"]  # display; degradam gracioso a "-"


def _f(v):
    """Coage p/ float nativo (evita tipos numpy no dump do YAML)."""
    return None if v is None else float(v)


def _serie(d):
    """{ano: valor} -> {int: float} nativo, descartando valores None."""
    return {int(a): float(v) for a, v in d.items() if v is not None}


def main() -> int:
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    ano_base = cfg["universo"]["ano_base"]        # 2025
    n = cfg["universo"]["anos_historico"]         # 10
    # rf_local congelado = default shipado (0.105). NÃO chamar macro.selic_ciclo_para_capm:
    # a rede fica só na captura de fundamentos; o ke do RIM lê este rf_local determinístico.
    rf_local = float(cfg["capm"]["rf_local"])

    snap = {"data_base": DATA_BASE, "rf_local": rf_local}

    for tk in BANCOS:
        print(f"  · capturando {tk} ao vivo ...", file=sys.stderr)
        c = build.montar_empresa(tk, ano_base, n)
        if c is None or not c.anos:
            print(
                f"FALHA: captura ao vivo de {tk} retornou vazia/None "
                f"(CVM/Yahoo/BCB) — snapshot NÃO gerado.",
                file=sys.stderr,
            )
            return 1

        # rota observada na captura — cfg já carrega rf_local=0.105 (mesmo valor congelado)
        a = report.analisar_acao(c, cfg)

        entrada = {
            "nome": c.nome,
            "setor": c.setor,
            "anos": [int(x) for x in c.anos_ordenados()],
            "preco_atual": _f(c.preco_atual),
            "beta": _f(c.beta),
            "dpa_trailing_12m": _f(c.dpa_trailing_12m),
            "motor_observado": a.motor,
            "arquetipo_observado": a.arquetipo,
            "intrinseco_motor_observado": _f(a.intrinseco_motor),
        }
        for s in SERIES_OBRIGATORIAS:
            entrada[s] = _serie(getattr(c, s))
        for s in SERIES_OPCIONAIS:
            serie = _serie(getattr(c, s))
            if serie:
                entrada[s] = serie

        # guarda-corpo: campos obrigatórios do RIM não podem faltar (fonte incompleta = blocker)
        for campo in ("preco_atual", "beta"):
            if entrada[campo] is None:
                print(
                    f"FALHA: {tk} sem {campo} na captura ao vivo (fonte incompleta) "
                    f"— snapshot NÃO gerado.",
                    file=sys.stderr,
                )
                return 1
        for campo in SERIES_OBRIGATORIAS:
            if not entrada[campo]:
                print(
                    f"FALHA: {tk} sem série {campo} na captura ao vivo (fonte incompleta) "
                    f"— snapshot NÃO gerado.",
                    file=sys.stderr,
                )
                return 1

        snap[tk] = entrada
        print(
            f"    {tk}: setor={c.setor!r} arquetipo={a.arquetipo} motor={a.motor} "
            f"intrinseco={entrada['intrinseco_motor_observado']}",
            file=sys.stderr,
        )

    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8") as fh:
        yaml.safe_dump(snap, fh, allow_unicode=True, sort_keys=True, default_flow_style=False)
    print(f"[snapshot gravado em {DESTINO}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
