"""WR-02 — `carregar_snapshot` normaliza as chaves de `ipca_deflatores` para `int(ano)`.

Todo carimbo anual de série no snapshot é re-chaveado com `int(ano)` na carga (backtest.py)
porque um YAML round-trip pode devolver os anos como STRING (`"2020"`). O carimbo global
`ipca_deflatores` (PRIM-04) entrava SEM essa normalização — e o consumidor
(`report._intrinseco_por_motor`) filtra por `an in defl` com `an` INTEIRO. Chave-string ⇒
`2020 in {"2020": ...}` é sempre False ⇒ série deflacionada VAZIA ⇒ o motor cíclico devolve
None em silêncio, embora o ramo `if defl:` (dict não-vazio) tenha sido tomado.

Este teste faz o round-trip REAL por YAML com chaves-string e prova que a carga devolve
chaves INT — a série deflacionada volta a poder casar os anos da empresa (deflaciona, não
no-opera em silêncio). Zero rede; ticker sintético; fatores adimensionais (não reais).
"""

import yaml

from analista.backtest import carregar_snapshot


def _escrever_snapshot(tmp_path, ipca_deflatores):
    snap = {
        "data_base": "2024-01-01",
        "rf_local": 0.10,
        "ipca_deflatores": ipca_deflatores,
        "XPTO3": {
            "nome": "Sintetica SA",
            "setor": "Siderurgia",
            "anos": [2020, 2021, 2022],
            "preco_atual": 10.0,
            "lucro_liquido": {2020: 100.0, 2021: 110.0, 2022: 120.0},
            "patrimonio_liquido": {2020: 1000.0, 2021: 1000.0, 2022: 1000.0},
            "num_acoes": {2020: 100.0, 2021: 100.0, 2022: 100.0},
        },
    }
    caminho = tmp_path / "snap.yaml"
    caminho.write_text(yaml.safe_dump(snap), encoding="utf-8")
    return str(caminho)


def test_carregar_snapshot_normaliza_chaves_string_do_ipca_para_int(tmp_path):
    # Chaves de ano como STRING (o que um YAML round-trip pode produzir).
    caminho = _escrever_snapshot(tmp_path, {"2020": 1.2, "2021": 1.1, "2022": 1.0})

    _empresas, _rf, defl = carregar_snapshot(caminho)

    # A carga deve re-chavear para INT, como toda série anual irmã (backtest.py:74-75).
    assert set(defl.keys()) == {2020, 2021, 2022}
    assert all(isinstance(k, int) for k in defl)
    # Valores preservados como float.
    assert defl[2020] == 1.2 and defl[2022] == 1.0


def test_carregar_snapshot_sem_ipca_degrada_para_dict_vazio(tmp_path):
    # Ausência do carimbo global permanece never-raise → {} (série nominal a jusante).
    snap = {
        "data_base": "2024-01-01",
        "rf_local": 0.10,
        "XPTO3": {"nome": "S", "setor": "Siderurgia", "anos": [2020]},
    }
    caminho = tmp_path / "snap.yaml"
    caminho.write_text(yaml.safe_dump(snap), encoding="utf-8")

    _empresas, _rf, defl = carregar_snapshot(caminho)
    assert defl == {}
