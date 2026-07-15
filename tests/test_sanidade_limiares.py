"""Fase 8 / plano 08-04 — congela os limiares de sanidade (D-11) e prova as invariantes
estruturais dos checks (simetria do SAN-02, isenção por split, never-raise do _bucket).

Categoria `invariante`: aqui o NÚMERO é permitido — o TICKER é que é PROIBIDO. A condição (i)
do detector BLIND-04a é o literal de ticker; sem ele a condição nunca fecha, por mais número
que o arquivo tenha. NÃO PODE CONTER NENHUM LITERAL DE TICKER (nem em comentário, nem em nome
de variável, nem em docstring). CompanyData sintético usa um ticker fictício ('ZZZZ9').

Afrouxar um limiar até a flag calar é o atalho de uma linha da Fase 9 que ninguém nota. Aqui
ele fica VERMELHO e tem que ser encarado. Limiar de detecção NÃO é knob de valuation (D-10):
não vive no config.yaml nem no calibracao.lock.yaml.
"""

from __future__ import annotations

import yaml

from analista.core import sanidade as s
from analista.core.fundamentals import CompanyData
from helpers_blindagem import CONFIG_PROD, LOCK_CALIBRACAO


def test_limiares_de_sanidade_estao_congelados():
    """Os 5 limiares + a TOLERANCIA_SPLIT batem com os valores esperados (D-11)."""
    assert s.LIMIAR_SAN01 == 1.5
    assert s.LIMIAR_SAN02 == 3.0
    assert s.LIMIAR_SAN03 == 1.5
    assert s.LIMIAR_SAN03_JCP == 1.10
    assert s.LIMIAR_SAN04 == 0.10
    assert s.LIMIAR_SAN05 == 0.10
    assert s.TOLERANCIA_SPLIT == 0.20


def test_limiar_do_san02_e_simetrico():
    """Um salto de fator F (para cima) e um de 1/F (para baixo) disparam AMBOS, com o mesmo
    limiar — e o bucket preserva a direção (~1e3 vs ~1e-3)."""
    c = CompanyData(ticker="ZZZZ9", anos=[2020, 2021, 2022])
    c.num_acoes = {2020: 1000.0, 2021: 1.0, 2022: 1000.0}  # 2021: ÷1000; 2022: ×1000
    avisos = s.checar_san02(c)
    assert len(avisos) == 2
    assert {a.check for a in avisos} == {"SAN-02"}
    assert {a.bucket for a in avisos} == {"~1e-3", "~1e3"}


def test_isencao_por_split_exime_salto_compativel_e_flaga_o_sem_split():
    """Um salto que casa um desdobramento registrado (|r/Πfatores − 1| < 20%) é ISENTO; o
    mesmo salto sem split registrado DISPARA. `c.splits` vazio nunca isenta (direção segura)."""
    com_split = CompanyData(ticker="ZZZZ9", anos=[2020, 2021])
    com_split.num_acoes = {2020: 100.0, 2021: 400.0}  # r = 4.0 (> limiar 3)
    com_split.splits = {"2021-06-01": 4.0}
    assert s.checar_san02(com_split) == []

    sem_split = CompanyData(ticker="ZZZZ9", anos=[2020, 2021])
    sem_split.num_acoes = {2020: 100.0, 2021: 400.0}
    assert "SAN-02" in {a.check for a in s.checar_san02(sem_split)}


def test_bucket_nunca_levanta_com_fator_nao_positivo():
    """_bucket sobre um fator NEGATIVO (sinal invertido) e sobre ZERO não levanta ValueError —
    é a guarda que impede o try/except do aplicar_sanidade de engolir uma detecção real."""
    assert s._bucket(-0.752) == "~1e0"
    assert s._bucket(0.0) == "~0"
    assert s._bucket(-205099.0) == "~1e5"


def test_limiares_nao_vivem_no_config_nem_no_lock():
    """D-10: nenhum LIMIAR_SAN* aparece no config.yaml nem no calibracao.lock.yaml, e o lock
    continua com exatamente os 3 graus de liberdade. Limiar de detecção não é knob de valuation."""
    texto_config = CONFIG_PROD.read_text(encoding="utf-8")
    texto_lock = LOCK_CALIBRACAO.read_text(encoding="utf-8")
    assert "LIMIAR_SAN" not in texto_config
    assert "LIMIAR_SAN" not in texto_lock

    lock = yaml.safe_load(texto_lock)
    graus = lock.get("graus_de_liberdade", {})
    assert len(graus) == 3
    assert set(graus) == {"ERP", "n_fade", "PIB_real"}
