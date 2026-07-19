"""Spike ENG (Fase 13) — medição OFFLINE do RIM ÚNICO sobre os 104 tickers.

THROWAWAY. NÃO é importado por produção; NÃO toca `src/`, `config.yaml` nem
`calibracao.lock.yaml`. É o oráculo herdado de KE-04 (`test_regressao_104_sem_explosao`)
aplicado como spike de MEDIÇÃO — de-risca as Ondas 2-4 da fase.

Pergunta que responde (por DISTRIBUIÇÃO de coorte, nunca por caso/ticker):
  (1) regulada (madura + concessão) e cíclica ficam SÃS sob o RIM único proposto no §"Mapa de
      âncoras" do 13-RESEARCH (hoje madura→DDM, cíclica→lucro_normalizado/Gordon-P/L)?
  (2) o carve-out CONCESSAO_FINITA deve usar `g_terminal = None` (fade-only) ou `= PIB_real`?

Método: carrega os 104 do snapshot LIMPO (mesmo loader de `test_ke_validacao.py`,
`hs.CAMINHO_SNAPSHOT_LIMPO`, β setorial carimbado), classifica o arquétipo, deriva o insumo do
RIM pela política do arquétipo, e chama `motores.rim(...)` com `ke=a.ke` (pronto, Fase 12). Para
o coorte CONCESSAO_FINITA roda DUAS variantes de `g_terminal` (None e PIB_real). Coleta por
COORTE: distribuição de V/preço, P/B justo e payout_T + contagem de ofensores.

Never-raise (T-13-01 / SAN-06): ticker que degrada conta como `None`, nunca aborta a varredura.
Anti-goals (BLIND-04a / Fase 14): nenhum print/assert nomeia ticker com número-alvo; a saída é
agregada por coorte; NÃO valida o caso do livro.

Uso: .venv/bin/python scripts/spike_eng_rim_104.py
"""

from __future__ import annotations

import math
import os
import statistics
import sys

# Roda standalone: adiciona src/ (engine) e tests/ (helpers offline) ao path.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "tests"))

import helpers_blindagem as hb  # noqa: E402
import helpers_sanidade as hs  # noqa: E402
from analista.core import arquetipo, lentes, motores  # noqa: E402
from analista.core import multiples as mult  # noqa: E402
from analista.core import normalizacao as norm  # noqa: E402
from analista.ingest import macro  # noqa: E402
from analista.report import report  # noqa: E402

# Teto GENEROSO de sanidade (não um nível calibrado): pega explosão de perpetuidade sem
# constranger o nível. Adimensional (V vs preço), espelha KE-04 — BLIND-04a-safe.
FATOR_SANIDADE = 50.0

# Tokens de setor que marcam concessão/regulada — MIRROR EXATO de `build.py:139` (a fonte de
# `c.eh_concessionaria`). O snapshot congelado NÃO grava `eh_concessionaria` (é derivado do
# setor no build, não persistido), então o loader offline o reconstrói aqui para que o coorte
# CONCESSAO_FINITA exista na medição (senão as concessões se dispersam nos outros coortes).
SETORES_CONCESSIONARIA = ("energia", "saneamento", "água", "gás")


def _eh_concessionaria(setor) -> bool:
    s = (setor or "").lower()
    return any(t in s for t in SETORES_CONCESSIONARIA)


def _cfg_offline() -> dict:
    """Config de produção OFFLINE com o β SETORIAL carimbado (determinístico, sem rede).

    Espelha `test_ke_validacao._cfg_offline_com_beta_setorial`: o `rf` cai no fallback da Selic e
    o mapa `setor → mediana(β)` é carimbado em `cfg["capm"]["beta_setorial"]`. É esse carimbo que
    faz o Ke offline usar o β setorial+Blume IDÊNTICO ao do app (D-06).
    """
    cfg = hb.carregar_config_producao()
    cfg["capm"]["rf_local"] = cfg["capm"]["selic_fallback"]  # rf offline determinístico
    cfg.setdefault("macro", {})
    macro.carimbar_beta_setorial(cfg)
    return cfg


def _g_cap(cfg: dict) -> float:
    """g_cap derivado EXATAMENTE como a engine: `(1+π_ciclo)(1+PIB_real) − 1` (D-04)."""
    pi_ciclo = cfg.get("macro", {}).get("pi_ciclo", 0.0518)
    pib_real = cfg["ddm"].get("pib_real", 0.02)
    return (1.0 + pi_ciclo) * (1.0 + pib_real) - 1.0


def _coorte(c, chave: str) -> str:
    """Coorte de medição a partir da chave do classificador ATUAL + o split D-05 proposto.

    O classificador de produção (intocado — spike) ainda devolve `PAGADORA_REGULADA` tanto no
    hard-route de concessão quanto no default-por-eliminação. O split D-05 (Plano 02/03) separa
    esses dois: `eh_concessionaria` → CONCESSAO_FINITA; senão → PAGADORA_MADURA. Aqui derivamos a
    coorte pelo MESMO sinal, sem alterar o classificador.
    """
    if chave == arquetipo.PAGADORA_REGULADA:
        return "concessao" if c.eh_concessionaria else "madura"
    return {
        arquetipo.FINANCEIRA: "financeira",
        arquetipo.CICLICA: "ciclica",
        arquetipo.CRESCIMENTO: "crescimento",
        arquetipo.HOLDING: "holding",
    }.get(chave, chave)


def _roe0_da_politica(coorte: str, c, vpa0: float, cfg: dict):
    """ROE-âncora da janela (`roe0`) pela política do arquétipo (§Mapa de âncoras, D-03).

    - financeira/madura/concessao/holding → `c.roe_valuation()` (mediana through-cycle);
    - ciclica → `lpa_norm_deflacionado / vpa0` (série deflacionada por IPCA como o ramo
      `normalizado` do report; offline sem deflatores cai na série nominal, never-raise);
    - crescimento → `c.roe_qualidade_atual()` (endpoint, o sinal de qualidade corrente).
    """
    if coorte == "ciclica":
        cic = (cfg.get("motores", {}) or {}).get("ciclica", {})
        _defl_raw = (cfg.get("macro", {}) or {}).get("ipca_deflatores") or {}
        defl = {}
        for _ano, _fator in _defl_raw.items():
            try:
                defl[int(_ano)] = float(_fator)
            except (TypeError, ValueError):
                continue
        ult = c.ultimo_ano()
        serie_lucro = [
            c.lucro_liquido[an] * defl[an]
            for an in c.anos_ordenados()
            if an in c.lucro_liquido and an in defl
        ]
        if not serie_lucro:
            serie_lucro = c.serie("lucro_liquido")
        lpa_norm = mult.lpa(
            norm.media_ciclo(
                serie_lucro,
                anos_media=cic.get("anos_media", 10),
                winsor=cic.get("winsor", 0.10),
            ),
            c.num_acoes.get(ult),
        )
        if lpa_norm is None or not vpa0:
            return None
        return lpa_norm / vpa0
    if coorte == "crescimento":
        return c.roe_qualidade_atual()
    return c.roe_valuation()


def _medir_ticker(c, cfg: dict, ke, coorte: str, g_cap: float, g_terminal):
    """Roda o RIM único de UM ticker com um dado `g_terminal` e devolve as razões medidas.

    Devolve `(vpreco, pb_justo, payout_T)` ou `None` (never-raise / dado degenerado). `pb_justo`
    e `payout_T` são a lente steady-state (Gordon-RIM) do RI terminal — a ponte auditável do
    ENG-08 — computadas com o `g` EFETIVO usado no terminal (0 quando `g_terminal is None`).
    """
    rim_cfg = (cfg.get("motores", {}) or {}).get("rim", {})
    ult = c.ultimo_ano()
    vpa0 = lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))
    if vpa0 is None or vpa0 <= 0 or ke is None:
        return None
    retencao = 1.0 - (c.payout_valuation() or 0.0)
    roe0 = _roe0_da_politica(coorte, c, vpa0, cfg)
    roe_term = report._roe_through_cycle(c, rim_cfg)
    if roe0 is None:
        return None

    res = motores.rim(
        vpa0=vpa0,
        roe0=roe0,
        ke=ke,
        retencao=retencao,
        n=rim_cfg.get("n_fade", 10),
        excesso_sustentavel=rim_cfg.get("excesso_sustentavel", 0.0),
        g_terminal=g_terminal,
        ke_g_spread_min=rim_cfg.get("ke_g_spread_min", 0.03),
        roe_terminal=roe_term,
    )
    if res is None:
        return None
    v = res.valor_intrinseco
    if v is None or not math.isfinite(v) or v <= 0:
        return None

    vpreco = v / c.preco_atual if c.preco_atual else None
    # Ponte steady-state: g efetivo do terminal (None ⇒ 0, sem crescimento).
    g_eff = 0.0 if g_terminal is None else g_terminal
    pb_justo = payout_T = None
    if roe_term is not None and abs(ke - g_eff) > 1e-9:
        pb_justo = 1.0 + (roe_term - ke) / (ke - g_eff)
        if roe_term != 0:
            payout_T = 1.0 - g_eff / roe_term
    return (vpreco, pb_justo, payout_T)


def _pct(vals, q):
    """Percentil simples (interpolação linear); None se vazio."""
    xs = sorted(v for v in vals if v is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    pos = q * (len(xs) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def _resumo(vals):
    """(mediana, p10, p90, max) de uma lista, ignorando None."""
    xs = [v for v in vals if v is not None]
    if not xs:
        return (None, None, None, None)
    return (statistics.median(xs), _pct(xs, 0.10), _pct(xs, 0.90), max(xs))


def _fmt(x):
    return "   n/a" if x is None else f"{x:6.2f}"


def _imprimir_tabela(titulo: str, coortes: dict, ordem) -> None:
    """Imprime a tabela por coorte: V/preço, P/B justo, payout_T, contagem de ofensores."""
    print(f"\n{'='*100}\n{titulo}\n{'='*100}")
    print(
        f"{'coorte':<14}{'n':>4}{'None':>6} | "
        f"{'V/preço (med/p10/p90/max)':>30} | {'P/B justo (med/p10/p90)':>26} | "
        f"{'payout_T (med/p10/p90)':>24}"
    )
    print("-" * 100)
    for coorte in ordem:
        d = coortes.get(coorte)
        if not d:
            continue
        vp = _resumo(d["vpreco"])
        pb = _resumo(d["pb"])
        po = _resumo(d["payout"])
        print(
            f"{coorte:<14}{d['n']:>4}{d['none']:>6} | "
            f"{_fmt(vp[0])}{_fmt(vp[1])}{_fmt(vp[2])}{_fmt(vp[3])} | "
            f"{_fmt(pb[0])}{_fmt(pb[1])}{_fmt(pb[2])} | "
            f"{_fmt(po[0])}{_fmt(po[1])}{_fmt(po[2])}"
        )
    print("-" * 100)
    print("Ofensores por coorte (V/preço>50x | P/B fora (0,6) | payout_T fora (0,1)):")
    for coorte in ordem:
        d = coortes.get(coorte)
        if not d:
            continue
        o = d["ofensores"]
        print(
            f"  {coorte:<14} V>50x={o['vpreco']:<3} "
            f"P/B_fora={o['pb']:<3} payout_fora={o['payout']:<3} degradou(None)={d['none']}"
        )


def _accumular(coortes: dict, coorte: str, medida) -> None:
    d = coortes.setdefault(
        coorte,
        {"n": 0, "none": 0, "vpreco": [], "pb": [], "payout": [],
         "ofensores": {"vpreco": 0, "pb": 0, "payout": 0}},
    )
    d["n"] += 1
    if medida is None:
        d["none"] += 1
        return
    vpreco, pb, payout_T = medida
    d["vpreco"].append(vpreco)
    d["pb"].append(pb)
    d["payout"].append(payout_T)
    if vpreco is not None and vpreco > FATOR_SANIDADE:
        d["ofensores"]["vpreco"] += 1
    if pb is not None and not (0.0 < pb < 6.0):
        d["ofensores"]["pb"] += 1
    if payout_T is not None and not (0.0 < payout_T < 1.0):
        d["ofensores"]["payout"] += 1


def main() -> int:
    cfg = _cfg_offline()
    empresas = hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO)
    falhas = hs.falhas_do_snapshot(hs.CAMINHO_SNAPSHOT_LIMPO)
    g_cap = _g_cap(cfg)
    pib_real = cfg["ddm"].get("pib_real", 0.02)
    rim_cfg = (cfg.get("motores", {}) or {}).get("rim", {})

    ordem = ["financeira", "madura", "concessao", "ciclica", "crescimento", "holding"]
    var_none: dict = {}
    var_pib: dict = {}
    total = sem_ke = erros = 0

    for tk, c in empresas.items():
        if tk in falhas:
            continue
        total += 1
        # Reconstrói o sinal derivado que o snapshot não persiste (mirror de build.py:168),
        # para o hard-route de concessão do classificador e o coorte funcionarem offline.
        c.eh_concessionaria = _eh_concessionaria(c.setor)
        try:
            a = report.analisar_acao(c, cfg)
        except Exception:  # noqa: BLE001 — engine é never-raise; qualquer exceção é ofensor
            erros += 1
            continue
        if a.ke is None:
            sem_ke += 1  # sem β de mercado ⇒ sem Ke (never-raise); não é explosão
            continue
        coorte = _coorte(c, arquetipo.classificar(c, cfg).chave)
        roe_term = report._roe_through_cycle(c, rim_cfg)
        retencao = 1.0 - (c.payout_valuation() or 0.0)
        g_T = (max(0.0, min(roe_term * retencao, g_cap))
               if roe_term is not None else g_cap)

        if coorte == "concessao":
            _accumular(var_none, coorte, _medir_ticker(c, cfg, a.ke, coorte, g_cap, None))
            _accumular(var_pib, coorte, _medir_ticker(c, cfg, a.ke, coorte, g_cap, pib_real))
        else:
            m = _medir_ticker(c, cfg, a.ke, coorte, g_cap, g_T)
            _accumular(var_none, coorte, m)
            _accumular(var_pib, coorte, m)

    print("Spike ENG (Fase 13) — RIM único sobre os 104 (snapshot LIMPO, β setorial carimbado)")
    print(f"  tickers no snapshot (fora de `falhas`): {total}")
    print(f"  degradados sem Ke (never-raise): {sem_ke}   |   exceções na engine: {erros}")
    print(f"  g_cap = {g_cap*100:.2f}%   PIB_real = {pib_real*100:.2f}%   "
          f"teto de sanidade V/preço = {FATOR_SANIDADE:.0f}x")

    _imprimir_tabela(
        "Variante A — CONCESSAO_FINITA com g_terminal = None (fade-only, recomendação do research)",
        var_none, ordem)
    _imprimir_tabela(
        f"Variante B — CONCESSAO_FINITA com g_terminal = PIB_real ({pib_real*100:.1f}% real puro)",
        var_pib, ordem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
