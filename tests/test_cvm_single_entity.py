"""Empresas single-entity (só demonstração INDIVIDUAL, sem consolidado — ex.: SANEPAR)
somem do frame consolidado (cheio de OUTRAS empresas). A seleção consolidado/individual
deve ser POR EMPRESA, não pelo frame estar globalmente vazio. Sem rede."""

import pandas as pd
import pytest

from analista.ingest import cvm


def _frame(linhas):
    """(cd, cod, ds, val) -> frame DRE sintético (escala MIL)."""
    return pd.DataFrame(
        [{"CD_CVM": cd, "CD_CONTA": cod, "DS_CONTA": ds, "VL_CONTA": val,
          "ESCALA_MOEDA": "MIL"} for cd, cod, ds, val in linhas]
    ).astype({"CD_CONTA": "string"})


def test_cai_para_individual_quando_empresa_so_no_ind(monkeypatch):
    # consolidado existe e é NÃO-vazio (outra empresa), mas a alvo (18627) só está no individual.
    con = _frame([(14443, "3.11", "Lucro/Prejuízo do Período", 5000.0)])   # SABESP, não a alvo
    ind = _frame([(18627, "3.11", "Lucro/Prejuízo do Período", 1503000.0)])  # SANEPAR

    def fake_ler(ano, prefixo):
        return {"DRE_con": con, "DRE_ind": ind}.get(prefixo)

    monkeypatch.setattr(cvm, "_ler_demonstracao", fake_ler)
    f = cvm.fundamentos_do_ano(18627, 2023)
    assert f["lucro_liquido"] == pytest.approx(1503000.0 * 1000)  # achou no individual


def test_prefere_consolidado_quando_empresa_esta_nele(monkeypatch):
    # a alvo está no consolidado E no individual com valores diferentes → usa o consolidado.
    con = _frame([(1023, "3.11", "Lucro/Prejuízo Consolidado do Período", 29000.0)])
    ind = _frame([(1023, "3.11", "Lucro/Prejuízo do Período", 25000.0)])

    def fake_ler(ano, prefixo):
        return {"DRE_con": con, "DRE_ind": ind}.get(prefixo)

    monkeypatch.setattr(cvm, "_ler_demonstracao", fake_ler)
    f = cvm.fundamentos_do_ano(1023, 2023)
    assert f["lucro_liquido"] == pytest.approx(29000.0 * 1000)  # consolidado tem precedência


def test_seletor_por_empresa_isolado(monkeypatch):
    con = _frame([(111, "3.11", "Lucro", 1.0)])
    ind = _frame([(222, "3.11", "Lucro", 2.0)])
    monkeypatch.setattr(cvm, "_ler_demonstracao",
                        lambda ano, p: {"X_con": con, "X_ind": ind}.get(p))
    assert cvm._consolidado_ou_individual(2023, "X", 222) is ind   # 222 só no ind
    assert cvm._consolidado_ou_individual(2023, "X", 111) is con   # 111 no con
