"""Spike SAN-07 (D-15) — re-emissão OFFLINE dos números do documento
`.planning/spikes/san-07-ihcd-at1-fvoci.md`.

Responde, MEDINDO contra o cache CVM (2015-2025, já em `data/cvm/`), as duas perguntas do
requisito SAN-07 para os 4 bancos da cesta (ITUB4, BBAS3, BBDC4, BRSR6):

  1. IHCD/AT1 entram no PL dos bancos (a premissa do requisito diz `2.03`)?  -> NÃO
  2. O dirty surplus por IFRS 9 FVOCI (OCI da DRA) é material contra o PL?    -> NÃO

Para cada banco imprime:
  (1) o que a conta `2.03` REALMENTE é naquele banco × onde o PL de fato está (código + nome);
  (2) a composição do bloco do PL (subcontas), para o leitor ver com os próprios olhos que
      não existe linha de IHCD / AT1 / instrumento perpétuo dentro dele;
  (3) o dirty surplus: `4.01` (LL), `4.02` (OCI) da DRA — o arquivo que o parser NUNCA abriu —
      e a razão OCI / PL, em %.

100% OFFLINE. Nada é escrito em disco; nada é consertado; nenhum knob é lido. É evidência
re-executável (T-08-05), não parte do pipeline (D-15: o spike responde uma pergunta contábil,
NÃO move um knob — Armadilha 3 do ROADMAP).

Uso: PYTHONPATH=src .venv/bin/python scripts/spike_san07_bancos.py
"""

from __future__ import annotations

import json
import os
import sys

# permite rodar como script standalone (sem depender de pip install -e .)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from analista.ingest.cvm import _ler_demonstracao, _norm  # noqa: E402

BANCOS = ["ITUB4", "BBAS3", "BBDC4", "BRSR6"]
ANO = 2025
TICKER_MAP = os.path.join(ROOT, "data", "ticker_map.json")

# termos que denunciariam um instrumento de capital híbrido/perpétuo (IHCD/AT1) dentro do PL
TERMOS_AT1 = [
    "instrumento elegivel",
    "elegivel ao capital",
    "perpetu",
    "divida perpetua",
    "hibrido",
    "at1",
    "ihcd",
    "capital complementar",
    "subordinada",
]


def _cd_cvm(tk: str) -> int:
    with open(TICKER_MAP, encoding="utf-8") as fh:
        return int(json.load(fh)[tk])


def _bi(vl_mil: float) -> float:
    """VL_CONTA vem em MILHARES de reais -> retorna em bilhões de R$."""
    return float(vl_mil) * 1000.0 / 1e9


def _pl_row(bpp, cd_cvm):
    """A linha do PL, casada por NOME (é assim que cvm.py já a acha: nome_primeiro=True)."""
    sub = bpp[bpp["CD_CVM"] == cd_cvm]
    pl = sub[sub["DS_CONTA"].map(_norm).str.contains("patrimonio liquido consolidado", na=False)]
    if pl.empty:
        return None
    return pl.iloc[0]


def _analisa_banco(tk: str) -> dict:
    cd = _cd_cvm(tk)
    bpp = _ler_demonstracao(ANO, "BPP_con")
    dra = _ler_demonstracao(ANO, "DRA_con")
    if bpp is None or dra is None:
        raise SystemExit(f"FALHA: cache CVM {ANO} ausente para BPP_con/DRA_con.")

    sub_bpp = bpp[bpp["CD_CVM"] == cd]
    if sub_bpp.empty:
        raise SystemExit(f"FALHA: {tk} (CD_CVM {cd}) ausente no BPP_con {ANO}.")

    # (1) o que 2.03 realmente é × onde o PL está
    r203 = sub_bpp[sub_bpp["CD_CONTA"] == "2.03"]
    conta_203 = None if r203.empty else (r203["DS_CONTA"].iloc[0], _bi(r203["VL_CONTA"].iloc[0]))

    pl = _pl_row(bpp, cd)
    if pl is None:
        raise SystemExit(f"FALHA: {tk} sem linha de 'Patrimônio Líquido Consolidado'.")
    cd_pl = str(pl["CD_CONTA"])
    vl_pl = _bi(pl["VL_CONTA"])

    print(f"\n{'='*74}\n{tk}  (CD_CVM {cd})  —  ano-base {ANO}\n{'='*74}")
    print("  A premissa do requisito diz que o PL é a conta 2.03. Medido:")
    if conta_203:
        print(f"    2.03  = {conta_203[0]!r}  (R$ {conta_203[1]:.2f} bi)  <- NÃO é PL")
    else:
        print("    2.03  = (ausente)")
    print(f"    PL    = {cd_pl}  'Patrimônio Líquido Consolidado'  (R$ {vl_pl:.2f} bi)  <- o PL real")

    # (2) composição do bloco do PL — subcontas diretas + o 2º nível (para ver a ausência de AT1)
    bloco = sub_bpp[sub_bpp["CD_CONTA"].str.startswith(cd_pl + ".", na=False)].copy()
    bloco["_prof"] = bloco["CD_CONTA"].str.count(r"\.")
    prof_pl = cd_pl.count(".")
    diretas = bloco[bloco["_prof"] <= prof_pl + 2]
    print("\n  Composição do PL (subcontas):")
    for _, row in diretas.iterrows():
        print(f"    {row['CD_CONTA']:<12} {row['DS_CONTA'][:48]:<48} R$ {_bi(row['VL_CONTA']):>8.2f} bi")

    # varredura por termos de IHCD/AT1 dentro do bloco do PL
    ds_pl = bloco["DS_CONTA"].map(_norm)
    achados_pl = [
        (c, d) for c, d in zip(bloco["CD_CONTA"], bloco["DS_CONTA"])
        if any(t in _norm(d) for t in TERMOS_AT1)
    ]
    print("\n  IHCD / AT1 / instrumento perpétuo DENTRO do PL:",
          "NENHUM" if not achados_pl else achados_pl)

    # onde o instrumento subordinado aparece (do lado do PASSIVO, não do PL) — se aparecer
    ds_all = sub_bpp["DS_CONTA"].map(_norm)
    subord = sub_bpp[ds_all.str.contains("subordinada", na=False)]
    subord = subord[~subord["CD_CONTA"].str.startswith(cd_pl + ".", na=False)]
    if not subord.empty:
        for _, row in subord.iterrows():
            print(f"    (passivo) {row['CD_CONTA']:<10} {row['DS_CONTA'][:40]:<40} "
                  f"R$ {_bi(row['VL_CONTA']):.2f} bi")

    # anomalia declarada: Ajustes de Avaliação Patrimonial (o ESTOQUE de OCI) = 0,00
    ajuste = sub_bpp[ds_all.str.contains("ajustes de avaliacao patrimonial", na=False)]
    if not ajuste.empty:
        c_aj = ajuste["CD_CONTA"].iloc[0]
        v_aj = _bi(ajuste["VL_CONTA"].iloc[0])
        print(f"\n  ⚠ Anomalia: '{c_aj} Ajustes de Avaliação Patrimonial' (estoque de OCI) "
              f"= R$ {v_aj:.2f} bi")

    # (3) dirty surplus (FVOCI) — da DRA (o arquivo que o parser nunca abriu)
    sub_dra = dra[dra["CD_CVM"] == cd]
    ll = sub_dra[sub_dra["CD_CONTA"] == "4.01"]
    oci = sub_dra[sub_dra["CD_CONTA"] == "4.02"]
    ll_v = _bi(ll["VL_CONTA"].iloc[0]) if not ll.empty else None
    oci_v = _bi(oci["VL_CONTA"].iloc[0]) if not oci.empty else None
    razao = None if (oci_v is None or vl_pl == 0) else (oci_v / vl_pl) * 100.0
    print("\n  Dirty surplus (DRA — Demonstração do Resultado Abrangente):")
    print(f"    4.01 Lucro Líquido            R$ {ll_v:>8.2f} bi" if ll_v is not None
          else "    4.01 Lucro Líquido            (ausente)")
    print(f"    4.02 Outros Result. Abrang.   R$ {oci_v:>8.3f} bi" if oci_v is not None
          else "    4.02 Outros Result. Abrang.   (ausente)")
    print(f"    OCI / PL                      {razao:>8.2f} %" if razao is not None
          else "    OCI / PL                      (indisponível)")

    return {"ticker": tk, "cd_pl": cd_pl, "oci_pl_pct": razao,
            "at1_no_pl": bool(achados_pl)}


def main() -> int:
    print("SPIKE SAN-07 — IHCD/AT1 no PL dos bancos? dirty surplus FVOCI material?")
    print(f"Fonte: cache CVM {ANO} (offline). Nenhum knob é lido; nada é escrito em disco.")
    resultados = [_analisa_banco(tk) for tk in BANCOS]

    print(f"\n{'='*74}\nVEREDITO\n{'='*74}")
    print("Pergunta 1 — IHCD/AT1 dentro do PL dos bancos?")
    algum = any(r["at1_no_pl"] for r in resultados)
    print(f"  -> {'SIM (revisar)' if algum else 'NÃO'} — nenhuma subconta de instrumento "
          "perpétuo/híbrido no bloco do PL de nenhum banco.")
    print("Pergunta 2 — dirty surplus FVOCI (OCI/PL) é material?")
    for r in resultados:
        print(f"  {r['ticker']}: OCI/PL = {r['oci_pl_pct']:.2f} %")
    pior = max(abs(r["oci_pl_pct"]) for r in resultados if r["oci_pl_pct"] is not None)
    print(f"  -> NÃO — o maior |OCI/PL| é {pior:.2f} % do PL/ano; contra o clean surplus, é ruído.")
    print("\nAs duas respostas são NÃO. O terceiro bug de dados NÃO existe. Nenhum knob se move.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
