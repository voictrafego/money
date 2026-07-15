"""Fase 8 / plano 08-05 — o diagnóstico LIGADO ao pipeline, e PROVADO por execução (D-04).

`aplicar_sanidade` NÃO roda sozinho (D-02): ele é uma função explícita que alguém precisa
CHAMAR. Isso abre a porta para o esquecimento silencioso — ninguém chama, o app roda liso e
CEGO, e nada fica vermelho. Estes testes fecham essa porta:

  - `test_sanidade_e_chamada_pelo_pipeline_real` (D-04) roda `montar_empresa` DE VERDADE, com
    `coletar_mercado` monkeypatchado (mercado reconstruído do snapshot congelado) e a CVM do
    cache local real — offline e determinístico. Apagar a linha `aplicar_sanidade(c)` de
    `montar_empresa` deixa a saída em `nao_avaliada` e este teste fica VERMELHO na hora. A
    evasão foi RODADA, não declarada (guarda que não é exercitada é guarda fantasma).
  - o never-raise (SAN-06) sobre os 104 tickers do snapshot: nenhuma exceção, e nenhuma queda
    no `try/except` (uma exceção engolida é uma detecção perdida em silêncio).

Categoria `contrato`: asserts de PERTINÊNCIA/presença/ausência/não-exceção — NENHUMA constante
numérica de nível chega a um assert (BLIND-04a). Um assert sobre o R$ resultante seria um
golden de nível disfarçado e violaria o CLAUDE.md. Onde há literais numéricos (ano-base,
janela), eles vivem DENTRO de helpers sem assert — invisíveis ao detector, longe dos asserts.
"""

from __future__ import annotations

import helpers_blindagem as hb
import helpers_sanidade as hs
from analista.core import sanidade as s
from analista.ingest import build, prices
from analista.report import report

SNAP = hs.carregar_snapshot_sanidade()
SNAP_RAW = hs.carregar_snapshot_bruto()
ROTULOS = ("alta", "media", "baixa", "nao_avaliada")


def _dm_do_snapshot(tk):
    """Reconstrói o `DadosMercado` que `montar_empresa` consome, a partir do snapshot
    congelado — offline, sem tocar a rede. É o que o monkeypatch de `coletar_mercado`
    devolve. `shares_outstanding` é o `sharesOutstanding` CRU do Yahoo (o que o pipeline
    consome como `dm.num_acoes`); `implied_shares_out` alimenta o insumo do SAN-01."""
    d = SNAP_RAW[tk]
    dm = prices.DadosMercado(ticker=tk)
    dm.preco_atual = d.get("preco_atual")
    dm.num_acoes = d.get("shares_outstanding")
    dm.market_cap = d.get("market_cap")
    dm.implied_shares_outstanding = d.get("implied_shares_out")
    dm.beta = d.get("beta")
    dm.nome = d.get("nome") or tk
    dm.setor = d.get("setor") or ""
    dm.splits = {str(k): float(v) for k, v in (d.get("splits") or {}).items()}
    dm.dividendos_por_ano = {int(a): float(v) for a, v in (d.get("dpa_por_ano") or {}).items()}
    return dm


def _montar_via_pipeline(monkeypatch, tk):
    """Roda o pipeline REAL (`build.montar_empresa`) com o mercado do snapshot e a CVM do
    cache local. Sem assert (não é conferidor): os literais de ano-base/janela ficam aqui,
    longe de qualquer assert de teste."""
    monkeypatch.setattr(build.prices, "coletar_mercado", lambda t: _dm_do_snapshot(tk))
    return build.montar_empresa(tk, ano_base=2025, n_anos=10)


def _checks(c):
    return {a.check for a in c.avisos}


# ------------------------- D-04: a chamada provada por execução ------------------------- #
def test_sanidade_e_chamada_pelo_pipeline_real(monkeypatch):
    """O pipeline REAL produz uma confiança avaliada. Se `aplicar_sanidade(c)` sumir de
    `montar_empresa`, a saída volta a `nao_avaliada` e este assert fica vermelho — foi
    exatamente assim que a evasão foi rodada e vista antes de fechar a task."""
    c = _montar_via_pipeline(monkeypatch, "ITUB4")
    assert c is not None
    assert c.confianca != "nao_avaliada"
    assert c.confianca in ROTULOS


# ------------------------- SAN-06: never-raise sobre os 104 ------------------------- #
def test_nenhum_check_levanta_em_nenhum_ticker_do_snapshot():
    """`aplicar_sanidade` roda sobre TODOS os tickers do snapshot congelado sem levantar,
    todos saem num dos rótulos válidos, e NENHUM check caiu no `try/except` (uma exceção
    engolida é uma detecção perdida em silêncio). É a prova do critério de sucesso do ROADMAP."""
    for tk, c in SNAP.items():
        diag = {}
        s.aplicar_sanidade(c, diag)
        assert c.confianca in ROTULOS, tk
        assert diag["quedas"] == 0, (tk, diag["checks_com_queda"])


def test_ticker_sem_dado_de_mercado_nao_estoura_e_san01_e_incomputavel():
    """MRFG3 (404 no Yahoo → sem market_cap): o SAN-01 é INCOMPUTÁVEL → não aparece em
    `c.avisos` (nem flag, nem exceção). Mas o SAN-04 (100% CVM) APARECE — o bug de base
    existe e não depende do Yahoo. Never-raise entregando resposta sobre dado ausente."""
    c = SNAP["MRFG3"]
    s.aplicar_sanidade(c)
    checks = _checks(c)
    assert "SAN-01" not in checks
    assert "SAN-04" in checks
    assert c.confianca in ROTULOS


def test_o_sinal_invertido_nao_vira_nao_avaliavel(monkeypatch):
    """CSNA3 (LL consolidado e controlador negativos, minoritário positivo) ACENDE SAN-04.
    Prova que o `_bucket` não estourou sobre a razão de sinal invertido e que o `try/except`
    não engoliu a detecção — se tivesse, o SAN-04 do CSNA3 sumiria em silêncio."""
    c = SNAP["CSNA3"]
    s.aplicar_sanidade(c)
    checks = _checks(c)
    assert "SAN-04" in checks


def test_engine_roda_num_ticker_sujo_e_produz_resposta():
    """A engine que o app já roda (`report.analisar_acao`) produz RESPOSTA sobre um ticker de
    escala quebrada (GOAU4), sem levantar. Assert de presença/não-exceção — NUNCA sobre o
    valor (um assert sobre o R$ resultante seria um golden de nível, proibido pelo CLAUDE.md)."""
    c = SNAP["GOAU4"]
    s.aplicar_sanidade(c)
    analise = report.analisar_acao(c, hb.carregar_config_producao())
    assert analise is not None
    assert c.confianca in ROTULOS
