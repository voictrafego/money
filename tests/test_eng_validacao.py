"""Validação por EXECUÇÃO do colapso: o RIM único sobre os 104 reais (ENG / Fase 13).

Memória `guardrails-devem-ser-provados-por-execucao`: "suíte verde" genérica NÃO prova
blindagem — RODAR a regressão prova. Este é o oráculo herdado de KE-04
(`test_regressao_104_sem_explosao`), agora sobre o RIM ÚNICO pós-colapso (o ensemble morreu
no 13-03; o contrato P/B religou no 13-04). NÃO introduz nenhum guard/clamp novo: OBSERVA o
que a engine produz sobre o mapa real e reprova se algo explodir/rotear errado.

BLIND-04a-safe: nenhuma assertiva cruza `ticker == valor de nível`. Os limiares são
ESTRUTURAIS/adimensionais (um múltiplo de preço; as faixas (0,6)/(0,1] da razão P/B — o
guard runtime do 13-04), nunca um alvo de ticker. NÃO valida o caso do livro (Fase 14): a
prova é por DISTRIBUIÇÃO dos 104, sem nomear ticker num assert.

Quatro invariantes por distribuição (§Validation Architecture do 13-RESEARCH):
  (1) never-raise — todo `intrinseco_motor` finito > 0 OU None; zero NaN/inf/exceção;
  (2) sem explosão — `V < 50× preço` (teto de sanidade, sem nomear ticker);
  (3) razão P/B sã por DEGRADE-NOT-CRASH — a ponte P/B é lente auditável: toda razão
      computável ou está na faixa sã (`pb_justo` ∈ (0,6), `payout_terminal` ∈ (0,1], meio-
      aberto — terminal zerado crava 1,0 por IDENTIDADE, nota load-bearing do 13-01/13-04),
      OU foi SINALIZADA (`a.razao_patologica=True`) e o veredito degradou; nunca passa muda;
  (4) caminho único — `a.motor` é sempre "rim", nunca ddm/seguradora/normalizado/dcf/nav.
"""

from __future__ import annotations

import math

import helpers_blindagem as hb
import helpers_sanidade as hs
from analista.ingest import macro
from analista.report import report

# Teto GENEROSO de sanidade (não um nível calibrado): pega explosão de perpetuidade sem
# constranger o nível. Usado SÓ na varredura do universo (que NÃO nomeia ticker) — BLIND-04a-safe.
FATOR_SANIDADE = 50.0

# Faixas do guard runtime D-10a (report.py): razão SÃ = pb_justo ∈ (0,6) e payout_T ∈ (0,1].
# O upper do payout é INCLUSIVO (meio-aberto) por IDENTIDADE — terminal zerado (carve-out /
# g_T=0) crava payout_T=1,0, não é patologia (nota load-bearing do spike 13-01, guard 13-04).
PB_MIN, PB_MAX = 0.0, 6.0
PAYOUT_MIN, PAYOUT_MAX = 0.0, 1.0

# Motores primários do mundo antigo (ensemble morto no 13-03): nenhum ticker pode rotear a eles.
MOTORES_MORTOS = {"ddm", "seguradora", "normalizado", "dcf", "nav"}


def _cfg_offline_com_beta_setorial() -> dict:
    """Config de produção OFFLINE com o β SETORIAL carimbado (determinístico, sem rede).

    Espelha os entry points do app (`cli._carimbar_macro`/`app.py`) e o oráculo KE-04: o `rf`
    cai no fallback da Selic e o mapa `setor → mediana(β)` é carimbado via
    `macro.carimbar_beta_setorial`. É esse carimbo que faz o Ke offline usar o β SETORIAL+Blume
    IDÊNTICO ao do app — sem ele, o Ke cairia no β individual e divergiria do produto (D-06).
    """
    cfg = hb.carregar_config_producao()
    cfg["capm"]["rf_local"] = cfg["capm"]["selic_fallback"]  # rf offline determinístico
    cfg.setdefault("macro", {})
    macro.carimbar_beta_setorial(cfg)
    return cfg


def test_regressao_104_colapso_rim_unico():
    """Os 104 REAIS (mapa limpo, β setorial carimbado), sob o RIM ÚNICO: nada explode/roteia-errado.

    Prova por EXECUÇÃO (memória `guardrails-devem-ser-provados-por-execucao`): RODAMOS o
    dispatch da engine sobre o mapa real e observamos, por ticker, os 4 invariantes por
    distribuição. `None` é aceitável (never-raise / falha de mercado). NENHUM guard novo é
    introduzido — o teste OBSERVA, não corrige: se algo explodir/rotear-errado, o bug está no
    ROE_T/spread do motor (não num clamp a reintroduzir). Reporta a lista de ofensores no assert.
    """
    empresas = hs.carregar_snapshot_sanidade(hs.CAMINHO_SNAPSHOT_LIMPO)
    falhas = hs.falhas_do_snapshot(hs.CAMINHO_SNAPSHOT_LIMPO)
    cfg = _cfg_offline_com_beta_setorial()

    ofensores: list[str] = []
    analisados = 0
    com_ponte = 0
    for tk, c in empresas.items():
        if tk in falhas:
            continue
        try:
            a = report.analisar_acao(c, cfg)
        except Exception as e:  # noqa: BLE001 — a engine é never-raise; qualquer exceção é ofensor
            ofensores.append(f"{tk}: EXCECAO {e!r}")
            continue
        analisados += 1

        # (4) Caminho único: sempre o RIM, nunca um motor primário do mundo antigo.
        if a.motor != "rim" or a.motor in MOTORES_MORTOS:
            ofensores.append(f"{tk}: motor primário {a.motor!r} != 'rim' (roteou fora do RIM único)")

        # (1) Never-raise: intrínseco finito e > 0, OU None (degradado). (2) Sem explosão.
        v = a.intrinseco_motor
        if v is not None:
            if not math.isfinite(v) or v <= 0:
                ofensores.append(f"{tk}: intrinseco_motor não-finito/não-positivo {v}")
            elif c.preco_atual and v >= FATOR_SANIDADE * c.preco_atual:
                ofensores.append(f"{tk}: V absurdo {v} (>= {FATOR_SANIDADE}x preco)")

        # (3) Razão P/B sã por DEGRADE-NOT-CRASH: a ponte P/B é uma LENTE auditável — o guard
        # D-10a NÃO apaga a razão (ela fica visível para inspeção), ele SINALIZA a patologia
        # (`a.razao_patologica=True` + alerta) e degrada o veredito de preço. O invariante da
        # cesta real é: toda razão computável ou está na faixa SÃ (pb_justo ∈ (0,6), payout_T ∈
        # (0,1]), OU foi DEGRADADA/sinalizada — nunca uma razão patológica passa muda. Provamos o
        # guard por EXECUÇÃO: se um pb_justo/payout_T sai da faixa SEM `razao_patologica`, o guard
        # FUROU (o bug é o guard/ROE_T, não a faixa a afrouxar).
        pb_fora = a.pb_justo is not None and not (PB_MIN < a.pb_justo < PB_MAX)
        payout_fora = (
            a.payout_terminal is not None and not (PAYOUT_MIN < a.payout_terminal <= PAYOUT_MAX)
        )
        if a.pb_justo is not None:
            com_ponte += 1
        if (pb_fora or payout_fora) and not a.razao_patologica:
            ofensores.append(
                f"{tk}: razão fora da faixa (pb={a.pb_justo}, payout_T={a.payout_terminal}) "
                "NÃO sinalizada (razao_patologica=False) — o guard D-10a furou (não degradou)"
            )

    assert analisados > 0, "nenhum ticker analisado — o mapa real dos 104 não carregou"
    assert com_ponte > 0, (
        "nenhuma razão P/B computável — o guard D-10a não foi exercitado sobre a cesta real"
    )
    assert not ofensores, (
        "o RIM único explodiu/divergiu/roteou-errado no mapa real dos 104 "
        f"({analisados} analisados):\n  " + "\n  ".join(sorted(ofensores))
    )
