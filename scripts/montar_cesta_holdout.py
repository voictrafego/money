"""Montador determinístico da cesta estratificada do hold-out (Fase 14 / VAL-02/03).

Não é importado por produção; roda OFFLINE sobre o snapshot congelado dos 104 e emite
`tests/fixtures/holdout_v24.yaml`. É o gerador do substrato de validação HONESTO do v2.4:
âncoras Graham+Bazin (lucro/dividendo real, independentes do modelo e do preço de mercado),
estratificado por arquétipo + 10 "difíceis" deliberados, montado por REGRA ESCRITA ANTES de
rodar o modelo.

DOIS MODOS (a ordem load-bearing do D-09 é o coração da fase):
- `--fair-value-only` (default) → COMMIT 1: emite SÓ `fair_value` (faixa Graham+Bazin). ZERO
  `v_modelo`. O `git log` prova que os fair values foram cravados ANTES de o modelo rodar.
- `--fill-v-modelo` → COMMIT 2 (Plano 04): preenche `v_modelo` rodando `report.analisar_acao`.
  NÃO é usado neste plano.

REGRA DE SELEÇÃO (D-05/D-06/D-07), escrita AQUI, reproduzível, cega ao resultado do modelo:
- Estrato = `arquetipo.classificar(c, cfg).chave` (fonte única de roteamento).
- LANDMINE OBRIGATÓRIA: o loader offline NÃO persiste `eh_concessionaria` (derivado do setor
  em `build.py:168`) — sem o mirror abaixo o estrato CONCESSAO_FINITA fica VAZIO e a cesta
  valida um roteamento que a produção não usa. Replicado em `_eh_concessionaria`.
- Cota: por estrato, ordena por `market_cap` desc (desempate alfabético por ticker), pega os 6
  primeiros. Estrato com universo < 6 (CRESCIMENTO tem 4) usa TODOS e MARCA `cota_incompleta`
  (D-07, honesto — não inventa nomes).
- 10 difíceis (D-06): 4 baldes (P/B<1, prejuízo ≤ 0 em qualquer dos últimos 3 anos,
  payout > 100%, menor patrimônio líquido). Pega TODOS do balde raso (payout>100%) e completa
  até ≥ 10 pelos EXTREMOS (ordinais, não thresholds mágicos) dos baldes fartos, em round-robin.
  Os difíceis são DISJUNTOS da cota (montam-se as cotas primeiro; difíceis escolhidos FORA).
- `fair_value` = faixa [min(Graham,Bazin), max(Graham,Bazin)] entre as lentes DEFINIDAS (D-02);
  Graham indefinido se lpa≤0/vpa≤0, Bazin indefinido se dpa≤0. Nenhuma definida → SEM
  fair_value (D-03, degradação REPORTADA, nunca exclusão silenciosa). O campo escalar
  `fair_value` é o ponto médio da faixa (casa o teste que acorda em test_blindagem_meta.py).

Never-raise: ticker que degrada → sem fair_value, nunca aborta a montagem.

Uso:
  python3 scripts/montar_cesta_holdout.py --fair-value-only --dry-run   # imprime YAML
  python3 scripts/montar_cesta_holdout.py --fair-value-only             # grava o fixture
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import sys

# Roda standalone: adiciona src/ (engine) e tests/ (helpers offline) ao path.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "tests"))

import helpers_blindagem as hb  # noqa: E402
import helpers_sanidade as hs  # noqa: E402
from analista.core import arquetipo, lentes  # noqa: E402
from analista.ingest import macro  # noqa: E402

CAMINHO_FIXTURE = os.path.join(_ROOT, "tests", "fixtures", "holdout_v24.yaml")

# Tokens de setor que marcam concessão/regulada — MIRROR EXATO de `build.py:168` (a fonte de
# `c.eh_concessionaria`, que o snapshot congelado NÃO grava). Sem isto os ~19 utilities caem
# em CICLICA e o estrato do carve-out (D-07) fica vazio, divergindo da produção.
SETORES_CONCESSIONARIA = ("energia", "saneamento", "água", "gás")

# Cota mínima por estrato (D-07). Estrato com universo menor usa todos e marca a cota.
COTA_MINIMA = 6
# Quantidade mínima de "difíceis" deliberados (D-06).
MIN_DIFICEIS = 10


def _eh_concessionaria(setor) -> bool:
    s = (setor or "").lower()
    return any(t in s for t in SETORES_CONCESSIONARIA)


def _cfg_offline() -> dict:
    """Config de produção OFFLINE com o β setorial carimbado (determinístico, sem rede).

    `classificar` só consome `cfg["arquetipo"]`; o carimbo do β é necessário para o Ke offline
    idêntico ao app no modo `--fill-v-modelo` (Plano 04). Espelha `spike_eng_rim_104._cfg_offline`.
    """
    cfg = hb.carregar_config_producao()
    cfg["capm"]["rf_local"] = cfg["capm"]["selic_fallback"]
    cfg.setdefault("macro", {})
    macro.carimbar_beta_setorial(cfg)
    return cfg


def _fair_value(c) -> tuple:
    """Faixa Graham+Bazin (D-02/D-03). Devolve `(fv_min, fv_max, lentes_validas)`.

    Never-raise: lente indefinida → ausente; nenhuma definida → (None, None, []).
    """
    ult = c.ultimo_ano()
    graham = lentes.preco_justo_graham(
        c.lpa_valuation(), lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))
    )
    bazin = lentes.preco_teto_bazin(
        lentes.dpa_medio([c.dpa(a) for a in c.anos_ordenados()], n=5)
    )
    valores = {}
    if graham is not None and graham > 0:
        valores["graham"] = graham
    if bazin is not None and bazin > 0:
        valores["bazin"] = bazin
    if not valores:
        return (None, None, [])
    return (min(valores.values()), max(valores.values()), sorted(valores.keys()))


def _pb_ratio(c) -> "float | None":
    """P/B = preço / VPA (mercado vs. book). None se indefinido."""
    ult = c.ultimo_ano()
    _vpa = lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))
    if _vpa is None or _vpa <= 0 or c.preco_atual is None:
        return None
    return c.preco_atual / _vpa


def _prejuizo_recente(c) -> "float | None":
    """Menor lucro dos últimos 3 anos SE houver algum ≤ 0; senão None (não é do balde).

    O ordinal do balde é o prejuízo mais profundo (menor lucro), determinístico.
    """
    anos = c.anos_ordenados()[-3:]
    lucros = [c.lucro_liquido[a] for a in anos if a in c.lucro_liquido]
    if not lucros or not any(v <= 0 for v in lucros):
        return None
    return min(lucros)


def _payout(c) -> "float | None":
    return c.payout_valuation()


def _book(c) -> "float | None":
    return c.patrimonio_liquido.get(c.ultimo_ano())


def montar(cfg: dict) -> dict:
    """Monta a cesta determinística. Devolve `{ticker: entrada_dict}` na ordem de emissão."""
    empresas = hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO)

    # 1. Reconstrói o roteamento de produção e classifica TODO o universo (104). ------ #
    # NÃO filtra `falhas` (tickers sem dado de MERCADO): o hold-out mede o modelo contra
    # âncoras Graham+Bazin, que partem de lucro/dividendo (não de preço/β) — um ticker sem
    # preço ainda tem fair_value E é um "difícil" legítimo (book negativo). Filtrar `falhas`
    # (artefato do spike, que RODAVA o modelo e precisava de Ke) esconderia justamente o caso
    # D-03 (AZUL4: book negativo + sem dividendo → sem lente) que a cesta tem de expor.
    universo = {}  # ticker -> (c, estrato)
    for tk, c in empresas.items():
        c.eh_concessionaria = _eh_concessionaria(c.setor)  # MIRROR obrigatório (build.py:168)
        estrato = arquetipo.classificar(c, cfg).chave
        universo[tk] = (c, estrato)

    # Universo por estrato (tamanho do estrato decide a marca de cota). ------------- #
    por_estrato: dict = {}
    for tk, (c, estrato) in universo.items():
        por_estrato.setdefault(estrato, []).append(tk)
    tamanho_estrato = {e: len(ts) for e, ts in por_estrato.items()}

    def _ordena_market_cap(tickers):
        # market_cap desc; None por último; desempate alfabético por ticker.
        return sorted(
            tickers,
            key=lambda t: (
                0 if universo[t][0].market_cap is not None else 1,
                -(universo[t][0].market_cap or 0.0),
                t,
            ),
        )

    # 2. Cotas (D-05/D-07): 6 primeiros por market_cap desc; estrato < 6 usa todos. -- #
    cota_selecionada = set()
    for estrato, tickers in por_estrato.items():
        for tk in _ordena_market_cap(tickers)[:COTA_MINIMA]:
            cota_selecionada.add(tk)

    # 3. Os 10 difíceis (D-06), DISJUNTOS da cota, por extremos ordinais. ----------- #
    fora_da_cota = [tk for tk in universo if tk not in cota_selecionada]

    # Balde raso: payout > 100% (pega TODOS), ordenado por payout desc.
    balde_payout = sorted(
        [tk for tk in fora_da_cota if (_payout(universo[tk][0]) or 0.0) > 1.0],
        key=lambda t: (-(_payout(universo[t][0]) or 0.0), t),
    )
    # Baldes fartos, cada um por seu EXTREMO (ordinal), não por threshold mágico.
    balde_pb = sorted(
        [tk for tk in fora_da_cota if (_pb_ratio(universo[tk][0]) or 9e9) < 1.0],
        key=lambda t: (_pb_ratio(universo[t][0]), t),  # menor P/B primeiro
    )
    balde_prej = sorted(
        [tk for tk in fora_da_cota if _prejuizo_recente(universo[tk][0]) is not None],
        key=lambda t: (_prejuizo_recente(universo[t][0]), t),  # prejuízo mais profundo primeiro
    )
    balde_book = sorted(
        [tk for tk in fora_da_cota if _book(universo[tk][0]) is not None],
        key=lambda t: (_book(universo[t][0]), t),  # menor book primeiro
    )

    dificeis = []
    visto = set(cota_selecionada)
    # Todos do balde raso primeiro (D-06).
    for tk in balde_payout:
        if tk not in visto:
            dificeis.append(tk)
            visto.add(tk)
    # Round-robin pelos extremos dos baldes fartos até >= 10.
    baldes_fartos = [balde_pb, balde_prej, balde_book]
    idx = [0, 0, 0]
    while len(dificeis) < MIN_DIFICEIS:
        progrediu = False
        for bi, balde in enumerate(baldes_fartos):
            while idx[bi] < len(balde) and balde[idx[bi]] in visto:
                idx[bi] += 1
            if idx[bi] < len(balde):
                tk = balde[idx[bi]]
                idx[bi] += 1
                dificeis.append(tk)
                visto.add(tk)
                progrediu = True
                if len(dificeis) >= MIN_DIFICEIS:
                    break
        if not progrediu:
            break  # baldes esgotados (never-raise: marca honesta pela contagem final)

    dificeis_set = set(dificeis)

    # 4. Cesta = cota ∪ difíceis. Ordena por (estrato, market_cap desc) p/ leitura. -- #
    na_cesta = sorted(cota_selecionada | dificeis_set)
    na_cesta = sorted(
        na_cesta,
        key=lambda t: (
            universo[t][1],
            0 if universo[t][0].market_cap is not None else 1,
            -(universo[t][0].market_cap or 0.0),
            t,
        ),
    )

    hoje = datetime.date.today().isoformat()
    cesta: dict = {}
    for tk in na_cesta:
        c, estrato = universo[tk]
        fv_min, fv_max, lentes_validas = _fair_value(c)
        entrada = {}
        if fv_min is not None:
            fv_mid = (fv_min + fv_max) / 2.0
            entrada["fair_value"] = round(fv_mid, 2)
            entrada["fair_value_min"] = round(fv_min, 2)
            entrada["fair_value_max"] = round(fv_max, 2)
        entrada["lentes"] = lentes_validas
        entrada["arquetipo"] = estrato
        entrada["dificil"] = tk in dificeis_set
        entrada["cota_incompleta"] = tamanho_estrato[estrato] < COTA_MINIMA
        entrada["fonte"] = "lentes Graham+Bazin (core/lentes)"
        entrada["data"] = hoje
        cesta[tk] = entrada
    return cesta


def _fmt_num(x) -> str:
    return f"{x:.2f}"


def _emitir_yaml(cesta: dict, snapshot_hash: str) -> str:
    """Serializa a cesta com CADA campo em sua PRÓPRIA LINHA (git blame é por linha, D-09).

    Escrito à mão (não yaml.dump) para controlar a ordem dos campos, garantir que `fair_value`
    e `v_modelo` (Plano 04) fiquem em linhas separadas, e gravar o cabeçalho auditável.
    """
    hoje = datetime.date.today().isoformat()
    linhas = [
        "# holdout_v24.yaml — substrato de validação HONESTO do v2.4 (Fase 14 / VAL-02/03/05).",
        "#",
        "# COMMIT 1 (D-09): SÓ `fair_value` (faixa Graham+Bazin, lucro/dividendo real, independente",
        "# do modelo e do preço). ZERO `v_modelo` — o modelo roda no COMMIT 2 (Plano 04); o `git",
        "# blame` por linha prova que os fair values foram cravados ANTES do modelo.",
        "#",
        "# REGRA DE SELEÇÃO (escrita ANTES de rodar o modelo — cega ao resultado):",
        "#   - Estrato = arquetipo.classificar (com eh_concessionaria replicado de build.py:168).",
        "#   - Cota: por estrato, market_cap desc, desempate alfabético, 6 primeiros. Estrato com",
        "#     universo < 6 usa todos e marca `cota_incompleta: true` (D-07).",
        "#   - 10 difíceis (D-06): baldes P/B<1, prejuízo≤0 (últimos 3a), payout>100%, menor book;",
        "#     todos do balde raso (payout>100%) + extremos dos fartos em round-robin, DISJUNTOS",
        "#     da cota.",
        "#   - fair_value = ponto médio da faixa [min,max] das lentes definidas; nenhuma lente",
        "#     definida → SEM fair_value (D-03, degradação reportada, nunca exclusão silenciosa).",
        "#",
        f"#   snapshot: {os.path.basename(hs.CAMINHO_SNAPSHOT_LIMPO)}",
        f"#   snapshot_sha256_12: {snapshot_hash}",
        f"#   gerado_por: scripts/montar_cesta_holdout.py --fair-value-only",
        f"#   data: {hoje}",
        "",
    ]
    for tk, e in cesta.items():
        linhas.append(f"{tk}:")
        if "fair_value" in e:
            linhas.append(f"  fair_value: {_fmt_num(e['fair_value'])}")
            linhas.append(f"  fair_value_min: {_fmt_num(e['fair_value_min'])}")
            linhas.append(f"  fair_value_max: {_fmt_num(e['fair_value_max'])}")
        lentes_str = "[" + ", ".join(e["lentes"]) + "]"
        linhas.append(f"  lentes: {lentes_str}")
        linhas.append(f"  arquetipo: {e['arquetipo']}")
        linhas.append(f"  dificil: {str(e['dificil']).lower()}")
        linhas.append(f"  cota_incompleta: {str(e['cota_incompleta']).lower()}")
        linhas.append(f"  fonte: \"{e['fonte']}\"")
        linhas.append(f"  data: \"{e['data']}\"")
    return "\n".join(linhas) + "\n"


def _snapshot_hash() -> str:
    dados = open(hs.CAMINHO_SNAPSHOT_LIMPO, "rb").read()
    return hashlib.sha256(dados).hexdigest()[:12]


def main() -> int:
    parser = argparse.ArgumentParser(description="Montador da cesta estratificada do hold-out.")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--fair-value-only", action="store_true", default=True,
                      help="COMMIT 1: emite só fair_value (default).")
    modo.add_argument("--fill-v-modelo", action="store_true",
                      help="COMMIT 2 (Plano 04): preenche v_modelo. NÃO usado neste plano.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Imprime o YAML no stdout em vez de gravar o fixture.")
    args = parser.parse_args()

    if args.fill_v_modelo:
        print("ERRO: --fill-v-modelo é o COMMIT 2 (Plano 04); não implementado neste plano.",
              file=sys.stderr)
        return 2

    cfg = _cfg_offline()
    cesta = montar(cfg)
    texto = _emitir_yaml(cesta, _snapshot_hash())

    if args.dry_run:
        sys.stdout.write(texto)
    else:
        with open(CAMINHO_FIXTURE, "w", encoding="utf-8") as fh:
            fh.write(texto)
        print(f"gravado: {CAMINHO_FIXTURE} ({len(cesta)} tickers)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
