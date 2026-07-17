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

import pytest

import helpers_blindagem as hb
from analista.core import capm

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
