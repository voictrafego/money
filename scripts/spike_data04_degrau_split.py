"""Spike DATA-04 — localizar (por medição) o degrau artificial de ~13% no ITUB4.

A referência do requisito (prices.py:71-111) está OBSOLETA (módulo reescrito nas Fases 3-4).
Este spike reconstrói a série POR-AÇÃO histórica do ITUB4 (2015-2025) sobre o estado JÁ
consertado pelos planos 09-01/09-02 e mede se/onde existe um degrau artificial na fronteira
da bonificação 2024→2025 (fator real ≈ 1,1286×).

Offline: os fundamentos e a contagem oficial vêm do cache CVM (ZIPs). A série de split do
Yahoo (.splits) e o ajuste por split (prices._ajustar_por_split) são inspecionados sem rede
(reconstruímos um hist sintético a partir dos fatores de split conhecidos do ITUB4 quando a
rede não estiver disponível). NÃO edita código de produção.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from analista.ingest import cvm  # noqa: E402

ITUB4_CD_CVM = 19348
ANOS = list(range(2015, 2026))


def _fmt(x):
    return "None" if x is None else f"{x:,.4f}"


def main() -> None:
    print("=" * 78)
    print("SPIKE DATA-04 — ITUB4 (CD_CVM=19348) — série por-ação, estado pós-09-01/09-02")
    print("=" * 78)

    # (a) contagem oficial CRUA da CVM por ano (composicao_capital, ON+PN em circulação)
    oficial_cru = {}
    for ano in ANOS:
        oficial_cru[ano] = cvm.contagem_oficial_do_ano(ITUB4_CD_CVM, ano)

    # (b) lucro (controlador quando presente, senão consolidado) por ano
    lucro = {}
    for ano in ANOS:
        f = cvm.fundamentos_do_ano(ITUB4_CD_CVM, ano)
        lc = f.get("lucro_controlador")
        lucro[ano] = lc if lc is not None else f.get("lucro_liquido")

    print("\n[a] Contagem oficial CRUA (composicao_capital, sem escala) e razão ano/ano:")
    print(f"{'ano':>5} {'num_acoes_cru':>18} {'razao_yoy':>12}")
    prev = None
    for ano in ANOS:
        v = oficial_cru[ano]
        razao = (v / prev) if (v and prev) else None
        print(f"{ano:>5} {_fmt(v):>18} {_fmt(razao):>12}")
        if v:
            prev = v

    print("\n[b] Lucro por ano (controlador→consolidado) e LPA CRU = lucro/num_acoes_cru:")
    print(f"{'ano':>5} {'lucro':>20} {'LPA_cru':>14} {'LPA_razao_yoy':>14}")
    prev_lpa = None
    for ano in ANOS:
        na = oficial_cru[ano]
        ll = lucro[ano]
        lpa = (ll / na) if (na and ll) else None
        razao = (lpa / prev_lpa) if (lpa and prev_lpa) else None
        print(f"{ano:>5} {_fmt(ll):>20} {_fmt(lpa):>14} {_fmt(razao):>14}")
        if lpa:
            prev_lpa = lpa

    # (c) fronteira da bonificação 2024→2025
    print("\n[c] Fronteira da bonificação 2024→2025:")
    n24, n25 = oficial_cru.get(2024), oficial_cru.get(2025)
    if n24 and n25:
        print(f"    num_acoes 2024 = {n24:,.0f}")
        print(f"    num_acoes 2025 = {n25:,.0f}")
        print(f"    razão num_acoes 2025/2024 = {n25 / n24:.4f} (bonif. real ≈ 1,1286)")
    else:
        print("    contagem 2024 e/ou 2025 ausente no composicao_capital.")

    # (d) O ajuste por split (prices._ajustar_por_split) toca a série por-ação de valuation?
    print("\n[d] Onde o split entra no pipeline (leitura estática do código):")
    print("    prices._ajustar_por_split → dm.ohlc_ajustado → c.ohlc_ajustado")
    print("    consumidor de c.ohlc_ajustado: SÓ core/indicators.py (indicadores técnicos).")
    print("    serie_precos (valuation/gráfico) = Close NOMINAL (auto_adjust=False, fix Fase 3).")
    print("    num_acoes (valuation) = composicao_capital oficial por ano (fix 09-02).")
    print("    → nenhuma série de VALUATION multiplica num_acoes por preço split-ajustado.")


if __name__ == "__main__":
    main()
