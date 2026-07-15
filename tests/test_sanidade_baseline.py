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
CAMINHO_ACEITOS = (
    pathlib.Path(__file__).resolve().parent / "fixtures" / "pares_aceitos_sanidade.yaml"
)


def _carregar_baseline() -> dict:
    """Lê o baseline YAML como dict cru. Carregado em runtime → nenhum literal de ticker
    aparece no AST deste módulo (o que mantém o detector do BLIND-04a longe)."""
    return yaml.safe_load(CAMINHO_BASELINE.read_text(encoding="utf-8")) or {}


def _carregar_aceitos() -> dict:
    """A accept-list DATA-06 (pares + buckets), lida em runtime — identidade de par como DADO,
    nenhum literal de ticker no AST (BLIND-04a). {} se ausente."""
    return yaml.safe_load(CAMINHO_ACEITOS.read_text(encoding="utf-8")) or {}


def _pares_aceitos() -> set:
    """Conjunto de pares (ticker, check) aceitos como NOVOS em pares_hoje (cura legítima)."""
    a = _carregar_aceitos()
    return {(e["ticker"], e["check"]) for e in (a.get("pares") or [])}


def _buckets_aceitos() -> set:
    """Conjunto de pares (ticker, check) cujo bucket NOVO (deslocado pela cura) é aceito."""
    a = _carregar_aceitos()
    return {(e["ticker"], e["check"]) for e in (a.get("buckets") or [])}


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
    """O mesmo, medido AGORA sobre o snapshot LIMPO (DATA-06) — o dado produzido pelo código
    JÁ consertado (DATA-01/02/03). É isto que faz a monotonicidade ENXERGAR o progresso: antes,
    "hoje" lia o mesmo sujo do baseline (tautologia); agora lê o limpo e a lista ENCOLHE. Os
    detectores (`test_sanidade_checks`) e a régua (`_pares_e_buckets_do_baseline`) SEGUEM no sujo."""
    empresas = hs.carregar_snapshot_sanidade(path=hs.CAMINHO_SNAPSHOT_LIMPO)
    pares = set()
    buckets: dict = {}
    for tk, c in empresas.items():
        sanidade.aplicar_sanidade(c)
        for a in c.avisos:
            par = (tk, a.check)
            pares.add(par)
            buckets.setdefault(par, set()).add(a.bucket)
    return pares, {k: frozenset(v) for k, v in buckets.items()}


# ----------------------------- D-06: a monotonicidade (ratchet honesto) ----------------------------- #
def test_baseline_de_sujos_so_encolhe():
    """O RATCHET honesto do DATA-06 (reformulado no 09-05). Antes: `pares_hoje ⊆ pares_baseline`
    (subconjunto puro). Mas a cura MUDA os dados de entrada — logo ela legitimamente SURFACED
    pares que o pipeline antigo (LL/LPA + filtro estreito) não conseguia medir. O subconjunto puro
    passa a exigir "a cura introduz ZERO flag nova em qualquer lugar" — impossível ao trocar a
    fonte. Reformulação: `pares_hoje ⊆ (pares_baseline ∪ pares_aceitos)`.

    `pares_aceitos` é uma lista VERSIONADA e justificada por categoria — o ÚNICO lugar onde um par
    novo pode entrar. Isto NÃO é regenerar o baseline: um par novo NÃO documentado ainda quebra
    este teste (provado RED-able por execução — ver 09-05-SUMMARY). Assim o ratchet segue pegando
    regressão silenciosa, sem fingir que uma cura que troca a fonte não mexe em nada."""
    pares_hoje, _ = _pares_e_buckets_de_hoje()
    pares_baseline, _ = _pares_e_buckets_do_baseline()
    aceitos = _pares_aceitos()
    nao_documentados = pares_hoje - pares_baseline - aceitos
    assert not nao_documentados, (
        "Pares (ticker, check) NOVOS e NÃO DOCUMENTADOS apareceram em pares_hoje — o ratchet do "
        "DATA-06 só aceita par novo via a accept-list VERSIONADA (com justificativa por categoria). "
        "Se você 'atualizou' o baseline para calar isto, é o reflexo do overfit do v2.3. "
        f"Não documentados: {sorted(nao_documentados)}"
    )


def test_bucket_nao_muda_sem_a_flag_sumir():
    """D-07 reformulado (09-05). Antes: bucket IGUAL para todo par persistente. Mas a cura desloca
    a ordem-de-grandeza de flags que sobrevivem (a reconciliação SAN-03 muda com o JCP; o resíduo
    SAN-05 muda com o PL do controlador). Regra correta: `buckets_hoje ⊆ buckets_baseline`. Um
    bucket que SOME é ocorrência CURADA (melhora — encolher o conjunto passa livre); um bucket
    NOVO é o perigo que D-07 existe para pegar (escala EMPURRADA). Bucket novo legítimo entra na
    `buckets_aceitos` (versionada, justificada). Também RED-able por execução (ver SUMMARY)."""
    pares_hoje, buckets_hoje = _pares_e_buckets_de_hoje()
    _, buckets_baseline = _pares_e_buckets_do_baseline()
    aceitos = _buckets_aceitos()
    persistentes = pares_hoje & set(buckets_baseline)
    empurrados = {
        p: {"baseline": sorted(buckets_baseline[p]), "hoje": sorted(buckets_hoje[p])}
        for p in persistentes
        if not (buckets_hoje[p] <= buckets_baseline[p]) and p not in aceitos
    }
    assert not empurrados, (
        "Um bucket NOVO apareceu num par persistente sem estar documentado — a escala foi "
        "EMPURRADA, não consertada (D-07). Bucket novo legítimo vai para buckets_aceitos: "
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


def test_os_alvos_consertados_sumiram_de_hoje():
    """O POSITIVO da cura (DATA-06): os pares que o ROADMAP nomeia como alvo dos consertos
    DATA-01/02/03 estão no baseline (sujo) mas NÃO em pares_hoje (limpo). É o espelho de
    `test_o_baseline_contem_os_alvos_do_roadmap` — a monotonicidade ENCOLHEU, ticker a ticker,
    e a prova é ausência de par (tuplas de STRINGS, nenhuma constante numérica — BLIND-04a)."""
    pares_hoje, _ = _pares_e_buckets_de_hoje()
    pares_baseline, _ = _pares_e_buckets_do_baseline()
    consertados = {
        ("BRSR6", "SAN-03"),  # DATA-01: JCP capturado
        ("GOAU4", "SAN-01"), ("CGRA4", "SAN-01"),  # DATA-03: escala de nível
        ("ITUB4", "SAN-02"), ("BRSR6", "SAN-02"),  # DATA-03: salto temporal
        ("CSNA3", "SAN-04"), ("ALUP11", "SAN-04"),  # DATA-02: base do controlador
        ("EQTL3", "SAN-04"), ("MRFG3", "SAN-04"),
    }
    # cada alvo estava sujo (no baseline) e foi CURADO (fora de hoje) — as duas metades importam.
    for par in consertados:
        assert par in pares_baseline, par
        assert par not in pares_hoje, par


def test_accept_list_e_disjunta_e_sem_reais():
    """A accept-list é o único portão de par/bucket novo — e não pode virar um baseline paralelo:
    (i) todo par aceito é NOVO (fora do baseline dos sujos); (ii) nenhum alvo do ROADMAP pode ser
    'aceito' (um conserto não pode ser silenciado por accept-list); (iii) nenhum `motivo` menciona
    um ticker conhecido (a regra da justificativa de knob) nem estampa termo de R$. Tuplas de
    strings + varredura textual: imune ao BLIND-04a por construção."""
    from helpers_blindagem import tickers_conhecidos

    aceitos_pares = _pares_aceitos()
    aceitos_buckets = _buckets_aceitos()
    pares_baseline, _ = _pares_e_buckets_do_baseline()
    alvos = {
        ("BRSR6", "SAN-03"), ("GOAU4", "SAN-01"), ("CGRA4", "SAN-01"),
        ("ITUB4", "SAN-02"), ("BRSR6", "SAN-02"), ("CSNA3", "SAN-04"),
        ("ALUP11", "SAN-04"), ("EQTL3", "SAN-04"), ("MRFG3", "SAN-04"),
    }
    # (i) par aceito é NOVO (não é reetiquetar um par que já estava sujo no baseline)
    assert not (aceitos_pares & pares_baseline), aceitos_pares & pares_baseline
    # (ii) nenhum alvo do ROADMAP entra por accept-list (não silenciar um conserto)
    assert not (aceitos_pares & alvos), aceitos_pares & alvos
    assert not (aceitos_buckets & alvos), aceitos_buckets & alvos
    # (iii) motivo categórico: sem ticker conhecido, sem termo de R$
    conhecidos = {t.upper() for t in tickers_conhecidos()}
    proibidos = ("preco", "market_cap", "intrinseco", "valor_justo")
    a = _carregar_aceitos()
    for secao in ("pares", "buckets"):
        for e in a.get(secao) or []:
            assert set(e.keys()) == {"ticker", "check", "motivo"}, e
            motivo = e["motivo"].lower()
            for termo in proibidos:
                assert termo not in motivo, e
            for palavra in motivo.replace("↔", " ").replace("/", " ").split():
                assert palavra.strip(".,;:()").upper() not in conhecidos, e


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
