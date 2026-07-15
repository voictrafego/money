"""Fase 8 / plano 08-06 — a REGRA DA MONOTONICIDADE (D-06). O baseline dos sujos é o teste
de regressão da Fase 9: a lista de sujos só pode ENCOLHER.

Quatro guardas, e todas passam por dentro do BLIND-04a de propósito:

  - `test_baseline_de_sujos_so_encolhe` (invariante): o conjunto de pares (ticker, check) de
    HOJE é subconjunto do baseline. Comparação de CONJUNTOS — nenhuma constante numérica. Se um
    par RESSUSCITAR, fica vermelho e lista os culpados. É a monotonicidade POR PAR (ticker,
    check), nunca por ticker (R-06): um num_acoes quebrado acende SAN-01/03/05 ao mesmo tempo,
    e o conserto de UM bug na Fase 9 remove UMA entrada — não o ticker inteiro.

  - `test_bucket_nao_muda_sem_a_flag_sumir` (invariante): para todo par que PERSISTE, o bucket
    (string, ordem de grandeza) é igual ao do baseline. É o assert que impede a escala de ser
    EMPURRADA em vez de CONSERTADA (D-07): flag acesa + bucket diferente = algo se mexeu sem se
    curar.

  - `test_o_baseline_contem_os_alvos_do_roadmap` (contrato): os alvos nomeados estão lá, com as
    flags certas — e o negativo vale tanto quanto (ITUB4 NÃO tem SAN-03, escapa por acidente do
    filtro estreito: zero falso positivo). Este teste CITA tickers reais → NENHUMA constante
    numérica pode chegar a um assert (os pares são tuplas de STRINGS).

  - `test_o_baseline_nao_estampa_reais_por_ticker` (contrato): o guarda que impede este arquivo
    de virar, um dia, um golden de nível — nenhum preco/market_cap/intrinseco, todo bucket é str.

🔴 BLIND-04a: um teste é OFENSOR com (i) literal de ticker E (ii) constante numérica não-trivial
chegando a um assert. O baseline vem de FIXTURE YAML (nenhum literal de ticker no AST) e os
asserts são de contenção/igualdade de strings. Nenhuma contagem de cardinalidade, nenhuma
contagem de sujos, nenhum dict de ticker no topo do .py — é assim que este desenho fecha
D-05 + D-06 + D-07 + BLIND-04a de uma vez.
"""

from __future__ import annotations

import pathlib

import yaml

import helpers_sanidade as hs
from analista.core import sanidade

CAMINHO_BASELINE = (
    pathlib.Path(__file__).resolve().parent / "fixtures" / "baseline_sanidade.yaml"
)


def _carregar_baseline() -> dict:
    """Lê o baseline YAML como dict cru. Carregado em runtime → nenhum literal de ticker
    aparece no AST deste módulo (o que mantém o detector do BLIND-04a longe)."""
    return yaml.safe_load(CAMINHO_BASELINE.read_text(encoding="utf-8")) or {}


def _pares_e_buckets_do_baseline():
    """(conjunto de pares (ticker, check), dict (ticker, check) -> frozenset(buckets))."""
    b = _carregar_baseline()
    pares = set()
    buckets: dict = {}
    for tk, dados in b.items():
        for fl in dados.get("flags") or []:
            par = (tk, fl["check"])
            pares.add(par)
            buckets.setdefault(par, set()).add(fl["bucket"])
    return pares, {k: frozenset(v) for k, v in buckets.items()}


def _pares_e_buckets_de_hoje():
    """O mesmo, medido AGORA: roda `aplicar_sanidade` sobre o snapshot congelado (offline)."""
    empresas = hs.carregar_snapshot_sanidade()
    pares = set()
    buckets: dict = {}
    for tk, c in empresas.items():
        sanidade.aplicar_sanidade(c)
        for a in c.avisos:
            par = (tk, a.check)
            pares.add(par)
            buckets.setdefault(par, set()).add(a.bucket)
    return pares, {k: frozenset(v) for k, v in buckets.items()}


# ----------------------------- D-06: a monotonicidade ----------------------------- #
def test_baseline_de_sujos_so_encolhe():
    """A lista de sujos só ENCOLHE: pares de hoje ⊆ pares do baseline. Se algum par
    ressuscitar (`hoje - baseline`), é regressão — e a mensagem os lista para o leitor."""
    pares_hoje, _ = _pares_e_buckets_de_hoje()
    pares_baseline, _ = _pares_e_buckets_do_baseline()
    ressuscitados = pares_hoje - pares_baseline
    assert pares_hoje <= pares_baseline, (
        "Pares (ticker, check) RESSUSCITARAM — a lista de sujos só pode ENCOLHER (D-06). "
        "Se você 'atualizou' o baseline para calar isto, é o reflexo do overfit do v2.3. "
        f"Ressuscitados: {sorted(ressuscitados)}"
    )


def test_bucket_nao_muda_sem_a_flag_sumir():
    """Para todo par que PERSISTE, o bucket (ordem de grandeza, string) é o mesmo. Bucket
    diferente com a flag ainda acesa = escala EMPURRADA, não consertada (D-07)."""
    pares_hoje, buckets_hoje = _pares_e_buckets_de_hoje()
    _, buckets_baseline = _pares_e_buckets_do_baseline()
    persistentes = pares_hoje & set(buckets_baseline)
    empurrados = {
        p: {"baseline": sorted(buckets_baseline[p]), "hoje": sorted(buckets_hoje[p])}
        for p in persistentes
        if buckets_hoje[p] != buckets_baseline[p]
    }
    assert not empurrados, (
        "O bucket mudou sem a flag sumir — a escala foi empurrada, não consertada (D-07): "
        f"{empurrados}"
    )


# ----------------------------- contrato: os alvos e o "sem R$" ----------------------------- #
def test_o_baseline_contem_os_alvos_do_roadmap():
    """Os alvos que o ROADMAP nomeia estão no baseline com as flags certas — e o negativo
    (ITUB4/BBDC4 sem SAN-03) prova zero falso positivo do detector de JCP. Só tuplas de
    strings: NENHUMA constante numérica chega a um assert (BLIND-04a)."""
    pares, _ = _pares_e_buckets_do_baseline()
    # positivos — as flags que TÊM que estar acesas hoje
    assert ("GOAU4", "SAN-01") in pares
    assert ("CGRA4", "SAN-01") in pares
    assert ("ITUB4", "SAN-02") in pares
    assert ("BRSR6", "SAN-02") in pares
    assert ("BRSR6", "SAN-03") in pares  # o JCP perdido, medido em 5×–25×
    assert ("MRFG3", "SAN-04") in pares
    assert ("CSNA3", "SAN-04") in pares
    assert ("ALUP11", "SAN-04") in pares
    assert ("EQTL3", "SAN-04") in pares
    # negativos — valem tanto quanto: os grandes bancos escapam do detector direto de JCP
    assert ("ITUB4", "SAN-03") not in pares
    assert ("BBDC4", "SAN-03") not in pares
    # MRFG3 (404 no Yahoo) é INCOMPUTÁVEL no SAN-01 — ausência é informação versionada
    assert ("MRFG3", "SAN-01") not in pares


def test_o_baseline_nao_estampa_reais_por_ticker():
    """Nenhuma chave/termo de R$ (preco/market_cap/intrinseco/valor_justo); todo bucket é str;
    cada ticker só tem `confianca` + `flags`. É o guarda que impede o baseline de virar golden
    de nível. Sem literal de ticker e sem número: imune ao BLIND-04a por construção."""
    proibidos = ("preco", "market_cap", "intrinseco", "valor_justo")
    b = _carregar_baseline()
    for tk, dados in b.items():
        assert set(dados.keys()) <= {"confianca", "flags"}, tk
        for fl in dados.get("flags") or []:
            assert set(fl.keys()) == {"check", "bucket"}, tk
            assert isinstance(fl["bucket"], str), tk
            assert isinstance(fl["check"], str), tk
    # varredura textual das linhas de DADO (comentários do cabeçalho são isentos)
    for linha in CAMINHO_BASELINE.read_text(encoding="utf-8").splitlines():
        if linha.lstrip().startswith("#"):
            continue
        baixa = linha.lower()
        for termo in proibidos:
            assert termo not in baixa, linha
