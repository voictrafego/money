"""Validação por EXECUÇÃO de que "nada explode sem clamp" (KE-04 / D-11, Fase 12).

Memória `guardrails-devem-ser-provados-por-execucao`: uma guarda só vale se for provada por
RODAR a regressão — "suíte verde" genérica não é evidência de blindagem. Estes testes NÃO
introduzem nenhum guard novo na engine (o `ke_teto`/`ke_piso` foram DELETADOS no 12-02/12-03):
eles OBSERVAM que a perpetuidade converge pela ARITMÉTICA do piso do Blume, não por trava.

Duas formas, ambas exigidas pelo requisito:
  (a) o invariante estrutural `Ke_min > g_cap` como DESIGUALDADE (nunca cravando 11,07%);
  (b) a regressão anti-explosão sobre o mapa REAL dos 104 tickers (test_regressao_104_...).

BLIND-04a-safe: nenhuma assertiva cruza `ticker == valor de nível`. Os limiares aqui são
ESTRUTURAIS/adimensionais (o intercepto 0,33 do Blume; a desigualdade Ke_min > g_cap; um
múltiplo de preço na varredura), nunca um alvo de ticker.
"""

from __future__ import annotations

import math

import pytest

import helpers_blindagem as hb
import helpers_sanidade as hs
from analista.core import capm
from analista.ingest import macro
from analista.report import report

# Limite superior GENEROSO de sanidade (não um nível calibrado): pega explosão de perpetuidade
# (Gordon perto da singularidade Ke≈g) sem constranger o nível. Usado SÓ na varredura do
# universo (que NÃO nomeia ticker), espelhando GROW-04/05 — fica BLIND-04a-safe.
FATOR_SANIDADE = 50.0

# Piso estrutural do Blume: o INTERCEPTO da regressão `β_blume = 0,33 + 0,67 × base`. Em base=0
# vale exatamente 0,33 e a função é monotônica crescente — logo 0,33 é o piso de β_blume para
# todo β ≥ 0 (o caso do equity), INDEPENDENTE de outlier setorial. É o intercepto de Blume, NÃO
# um alvo de ticker (compare a regra dura do CLAUDE.md: justificativa de threshold sem ticker).
PISO_BLUME = 0.33


def _g_cap(cfg: dict) -> float:
    """g_cap derivado EXATAMENTE como a engine (report.analisar_acao): a FONTE ÚNICA (D-04).

    `g_cap = (1 + π_ciclo)(1 + PIB_real) − 1`. Offline, π_ciclo cai no default `macro.pi_ciclo`
    e PIB_real no `ddm.pib_real` — a mesma leitura defensiva de `report`.
    """
    pi_ciclo = cfg.get("macro", {}).get("pi_ciclo", 0.0518)
    pib_real = cfg["ddm"].get("pib_real", 0.02)
    return (1.0 + pi_ciclo) * (1.0 + pib_real) - 1.0


def test_ke_min_estrutural_acima_do_g_cap():
    """DESIGUALDADE `rf + 0,33 × erp_local > g_cap` — sem cravar o número (robusta ao drift do rf).

    O `erp_local`, o `rf` e o `g_cap` são LIDOS do config dinamicamente (passaria com ERP 0,06 e
    com 0,045). No Selic-ciclo AO VIVO (rf ~9,58%) o Ke_min dá ~11,07% > 7,28% — documentado só
    aqui em comentário, NUNCA cravado num assert (Pitfall 3 do RESEARCH). No rf offline default
    (selic_fallback) dá ~11,99% > 7,28%. Para o Ke_min tocar o g_cap seria preciso rf abaixo de
    ~5,79% (g_cap − 0,33×erp_local) — implausível. O piso do Blume garante que essa é a MENOR
    Ke possível: como β_blume ≥ 0,33 para todo β ≥ 0, todo Ke real ≥ Ke_min > g_cap.
    """
    cfg = hb.carregar_config_producao()
    cfg["capm"]["rf_local"] = cfg["capm"]["selic_fallback"]  # rf offline determinístico

    erp_local = cfg["capm"]["erp_local"]        # lido do config (0,045 hoje; passaria com 0,06)
    rf = cfg["capm"]["rf_local"]
    g_cap = _g_cap(cfg)
    ke_min = rf + PISO_BLUME * erp_local

    assert ke_min > g_cap, (
        f"Ke_min estrutural ({ke_min:.5f} = rf {rf:.5f} + {PISO_BLUME}×erp {erp_local:.5f}) NÃO "
        f"supera g_cap ({g_cap:.5f}) — a perpetuidade poderia divergir SEM o clamp. O bug estaria "
        f"no rf ou no erp_local, não num clamp a reintroduzir."
    )

    # Piso do Blume é 0,33 (o intercepto): prova que Ke_min INDEPENDE de outlier de β. Em base=0
    # vale exatamente 0,33; um β alto só AUMENTA o Ke (afasta de g_cap), nunca abaixa o piso.
    assert capm.beta_blume(0.0, "setor_inexistente", {}) == pytest.approx(PISO_BLUME)
    assert capm.beta_blume(2.0, "setor_inexistente", {}) >= PISO_BLUME


def _cfg_offline_com_beta_setorial() -> dict:
    """Config de produção OFFLINE com o β SETORIAL carimbado (determinístico, sem rede).

    Espelha os entry points do app (`cli._carimbar_macro`/`app.py`): o `rf` cai no fallback da
    Selic e o mapa `setor → mediana(β)` é carimbado em `cfg["capm"]["beta_setorial"]` via
    `macro.carimbar_beta_setorial`. É esse carimbo que faz o Ke offline usar o β SETORIAL+Blume
    IDÊNTICO ao do app — sem ele, o Ke cairia no β individual e divergiria do produto.
    """
    cfg = hb.carregar_config_producao()
    cfg["capm"]["rf_local"] = cfg["capm"]["selic_fallback"]  # rf offline determinístico
    cfg.setdefault("macro", {})
    macro.carimbar_beta_setorial(cfg)  # o Ke offline usa o β setorial, idêntico ao app (D-06)
    return cfg


def _valor_efetivo(a) -> float | None:
    """A valuation EFETIVA de um arquétipo, sem assert (helper que CONSTRÓI, não confere).

    O motor primário grava `intrinseco_motor`; a REGULADA usa o DDM como lente (motor None) e a
    valuation vive na banda `vmin/vmax`. `None` é aceitável (motor pendente / dado degenerado).
    """
    if a.intrinseco_motor is not None:
        return a.intrinseco_motor
    if a.vmin is not None and a.vmax is not None:
        return (a.vmin + a.vmax) / 2.0
    return None


def _g_terminal(c, cfg: dict, g_cap: float) -> float:
    """g_T da perpetuidade DERIVADO como a engine: `max(0, min(ROE_T × retenção, g_cap))`.

    Piso 0 e teto g_cap (GROW-03). Quando o ROE through-cycle degrada (None), a engine usa g_cap.
    Como g_T ≤ g_cap por construção e Ke > g_cap (piso do Blume), o spread `Ke − g_T` é sempre
    positivo — é essa convergência aritmética que substitui o clamp.
    """
    roe_term = report._roe_through_cycle(c, (cfg.get("motores", {}) or {}).get("rim", {}))
    retencao = 1.0 - (c.payout_valuation() or 0.0)
    if roe_term is None:
        return g_cap
    return max(0.0, min(roe_term * retencao, g_cap))


def test_regressao_104_sem_explosao():
    """Os 104 tickers REAIS (mapa limpo), com o Ke setorial+Blume: nada explode, SEM clamp (D-11a).

    Prova por EXECUÇÃO (memória `guardrails-devem-ser-provados-por-execucao`): não basta a suíte
    verde — RODAMOS o dispatch da engine sobre o mapa real e observamos que, por ticker COM Ke:

      • `Ke ≥ Ke_min` estrutural (rf + 0,33 × erp_local) — o piso do Blume mantém o Ke acima do
        chão, INDEPENDENTE de outlier de β;
      • quando há `intrinseco_motor` finito: ele é > 0 e o spread `Ke − g_T > 0` (perpetuidade
        convergente pela aritmética, não por trava);
      • nenhum `V` explode: limite adimensional `V < 50× preço` (BLIND-04a-safe, sem nomear ticker).

    `None` é aceitável (never-raise / falha de mercado). NENHUM guard novo é introduzido — o teste
    OBSERVA, não corrige: se algum V explodisse, o bug estaria no ROE_T/spread (Fase 13), não num
    clamp a reintroduzir. Reporta a lista de ofensores na mensagem do assert.
    """
    empresas = hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO)
    falhas = hs.falhas_do_snapshot(hs.CAMINHO_SNAPSHOT_LIMPO)
    cfg = _cfg_offline_com_beta_setorial()

    erp_local = cfg["capm"]["erp_local"]
    rf = cfg["capm"]["rf_local"]
    g_cap = _g_cap(cfg)
    ke_min = rf + PISO_BLUME * erp_local

    ofensores: list[str] = []
    analisados = 0
    for tk, c in empresas.items():
        if tk in falhas:
            continue
        try:
            a = report.analisar_acao(c, cfg)
        except Exception as e:  # noqa: BLE001 — a engine é never-raise; qualquer exceção é ofensor
            ofensores.append(f"{tk}: EXCECAO {e!r}")
            continue

        if a.ke is None:
            continue  # sem β de mercado ⇒ sem Ke (never-raise); não é explosão
        analisados += 1

        # Piso do Blume por EXECUÇÃO: todo Ke real ≥ Ke_min > g_cap (anti-explosão sem clamp).
        if a.ke < ke_min - 1e-12:
            ofensores.append(f"{tk}: Ke {a.ke:.5f} ABAIXO do piso estrutural {ke_min:.5f}")

        valor = _valor_efetivo(a)
        if valor is None:
            continue  # motor pendente / dado degenerado — aceitável
        if not math.isfinite(valor) or valor <= 0:
            ofensores.append(f"{tk}: valuation não-finita/não-positiva {valor}")
            continue
        # Spread da perpetuidade convergente: Ke − g_T > 0 (g_T ≤ g_cap < Ke pela aritmética).
        g_T = _g_terminal(c, cfg, g_cap)
        if a.ke - g_T <= 0:
            ofensores.append(f"{tk}: spread Ke−g_T ({a.ke:.5f}−{g_T:.5f}) NÃO positivo")
        if c.preco_atual and valor >= FATOR_SANIDADE * c.preco_atual:
            ofensores.append(f"{tk}: V absurdo {valor} (>= {FATOR_SANIDADE}x preco)")

    assert analisados > 0, "nenhum ticker com Ke analisado — o mapa real dos 104 não carregou"
    assert not ofensores, (
        "o Ke setorial+Blume SEM clamp explodiu/divergiu no mapa real dos 104 "
        f"({analisados} com Ke):\n  " + "\n  ".join(sorted(ofensores))
    )
