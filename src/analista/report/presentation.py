"""Camada de APRESENTAÇÃO do analista (Cap. 6/10): helpers PUROS que formatam e montam
o que o app Streamlit exibe, sem nunca subir o Streamlit.

Este módulo é a fundação da hierarquia visual (D-09): a lógica de formatação que antes
vivia inline no `app.py` (não-testável) sai para cá, importável sem efeito colateral de
import. Os helpers só FORMATAM/ORGANIZAM campos já calculados pela engine de valuation
(`report.analisar_acao` → `a.multiplos`); nenhum número é recalculado aqui.

Convenção de None (GRAF-03): toda ausência vira o sentinela em-dash "—" — distinto do hífen
"-" da superfície CLI (`report._pct`/`_num`), que NÃO é unificado de propósito (UI-SPEC trava
o em-dash para a superfície do app).
"""

from __future__ import annotations

from typing import Optional


# --------------------------------------------------------------------------- #
# Sentinelas de formatação (movidos de app.py L51-56 — em-dash "—", não o hífen
# do report._pct). NÃO unificar com report._pct/_num: superfícies distintas.
# --------------------------------------------------------------------------- #
def fmt_pct(x: Optional[float], casas: int = 1) -> str:
    return "—" if x is None else f"{x*100:.{casas}f}%"


def fmt_num(x: Optional[float], casas: int = 2) -> str:
    return "—" if x is None else f"{x:.{casas}f}"


# --------------------------------------------------------------------------- #
# Header do Dividend Yield (HIER-01 / D-01,D-02,D-03)
#
# O recorrente (earnings-based, sustentável) é o VALOR PRINCIPAL; o trailing entra
# como delta neutro (cinza, delta_color="off") — contexto, não direção. Quando o
# recorrente é indisponível (ano de prejuízo na janela → dy_recorrente() None), cai
# para o trailing como principal, com label e help explícitos (fallback=True).
# --------------------------------------------------------------------------- #
def header_dy(dy_recorrente: Optional[float], dy_atual: Optional[float]) -> dict:
    """Monta o dict do header de DY (st.metric) escolhendo o recorrente como principal.

    Retorna sempre as chaves: label, value, delta, delta_color, help, fallback.
    """
    if dy_recorrente is not None:
        # Caminho normal: recorrente é a leitura sustentável (principal).
        delta = ("trailing " + fmt_pct(dy_atual)) if dy_atual is not None else None
        return {
            "label": "Dividend Yield (recorrente)",
            "value": fmt_pct(dy_recorrente),
            "delta": delta,
            "delta_color": "off",  # cinza neutro — trailing é contexto, não direção
            "help": (
                "DY recorrente: provento sustentável (lucro normalizado × payout "
                "sustentável) sobre o preço. O trailing (cinza, ao lado) pode estar "
                "inflado por proventos extraordinários da janela (Cap. 6)."
            ),
            "fallback": False,
        }
    # Fallback: recorrente indisponível (ano de prejuízo) → trailing vira o principal.
    return {
        "label": "Dividend Yield (trailing)",
        "value": fmt_pct(dy_atual),
        "delta": None,
        "delta_color": "off",
        "help": (
            "DY recorrente indisponível (ano de prejuízo na janela) — exibindo o DY trailing."
        ),
        "fallback": True,
    }


# --------------------------------------------------------------------------- #
# Linhas da tabela de Múltiplos (DYR-02 / PAY-02)
#
# Espelha a paridade do CLI (report.py L396-401), com DOIS fixes vs. o app.py atual:
#  - DYR-02: "DY rec." entra no ramo % (fmt_pct), não no default fmt_num (bug 0.06).
#  - PAY-02: "DP (payout)" vira DUAS linhas distintas — o payout CRU do último ano
#            (payout_ult) e o sustentável p/ valuation (payout_proj), que hoje colapsam
#            no mesmo valor clampado (app.py L317-323).
# --------------------------------------------------------------------------- #
def linhas_multiplos(
    multiplos: dict,
    payout_ult: Optional[float],
    payout_proj: Optional[float],
) -> list[tuple[str, str]]:
    """Monta as linhas (rótulo, valor formatado) da tabela de Múltiplos a partir do
    `a.multiplos` da engine (read-only) mais os dois payouts já calculados pelo caller."""
    linhas: list[tuple[str, str]] = []
    for k, val in multiplos.items():
        if k == "DP (payout)":
            # DUAS linhas distintas (D-05/D-06): cru do último ano x sustentável p/ valuation.
            linhas.append(("Payout (último ano)", fmt_pct(payout_ult)))
            linhas.append(("Payout p/ valuation (sustentável)", fmt_pct(payout_proj)))
        elif k in ("ML", "ROE", "DY", "DY rec.", "EY"):
            # Ramo % (paridade com report.py L397) — "DY rec." incluído é o fix DYR-02.
            linhas.append((k, fmt_pct(val)))
        else:
            linhas.append((k, fmt_num(val)))
    return linhas
