"""Freio do modo Ranking — fonte única compartilhada por cli.py (CLI) e app.py (Streamlit).

Móduло puro/testável extraído de cli.py (quick-260712-p6r) para garantir PARIDADE POR CONSTRUÇÃO
entre o `cmd_rank` do CLI e a aba "Ranking por múltiplos" do Streamlit: ambos consomem o MESMO
objeto de função, então uma superfície não pode divergir da outra sem quebrar o teste de paridade.

Firewall: este módulo NÃO importa `report` nem `selo` — só `arquetipo` e `comparables` (ambos
core, sem ciclo). Isso mantém `motor_pendente` offline (só classifica, não roda analisar_acao) e
preserva o firewall selo↛report.
"""

from __future__ import annotations

from . import arquetipo
from . import comparables as cmp


def motor_pendente(c, cfg: dict) -> bool:
    """Resolve a suspensão do Ranking pelo arquétipo da empresa (paridade com report.py, D-06).

    O Ranking classifica o negócio e consulta o registry ARQUETIPO_MOTOR. Na Fase 2 os motores
    JÁ EXISTEM (financeira→rim, ciclica→normalizado, crescimento→dcf, holding→nav), mas o SELO
    ainda consome só o DDM até a Fase 3 — então onde o motor do arquétipo NÃO é o DDM
    (`motor != "ddm"`) o Ranking segue SEM estampar preço-alvo por regressão, para não afirmar
    um alvo por um modelo que não é o do perfil (é o mesmo erro de arquitetura do ITUB4). O
    predicado migrou de "registry devolveu None" para `motor != "ddm"` no MESMO wave do plug.
    """
    arq = arquetipo.classificar(c, cfg)
    return arquetipo.ARQUETIPO_MOTOR.get(arq.chave) != "ddm"


def alvo_regressao_confiavel(reg, pa, motor_pendente: bool):
    """Freio do modo Ranking (Achado 3): o alvo de regressão pode ser ESTAMPADO como preço-alvo?

    Puro/testável — NÃO toca a NOTA do ranque (múltiplos padronizados), governa apenas a COLUNA
    de alvo/upside. Suprime (retorna confiavel=False) em quatro condições, paridade com a
    suspensão D-04 do modo Analisar:
      1. sem PrecoAlvo (regressão não gerou alvo p/ a empresa) → (False, None);
      2. regressão frágil — `reg.r2_baixo` (R²≈0: ITUB4/BBAS3) ou `reg.amostra_pequena` (n<10):
         o alvo derivado é ruído/instável;
      3. alvo degenerado — upside <= `LIMIAR_UPSIDE_ABSURDO` (ROMI3 R$0,10, −98%): extrapolação
         fora do suporte, não uma tese de −98%;
      4. suspensão por arquétipo — `motor_pendente`: não afirmar preço-alvo por um modelo (P/L
         relativo) que não serve ao perfil cujo motor primário só chega na Fase 2.

    Devolve `(confiavel: bool, motivo: Optional[str])`; `motivo` explica a supressão (p/ nota).
    """
    if pa is None:
        return (False, None)
    if reg is None:
        return (False, "sem regressão")
    if reg.r2_baixo:
        return (False, "R² baixo")
    if reg.amostra_pequena:
        return (False, "amostra pequena")
    if pa.upside is not None and pa.upside <= cmp.LIMIAR_UPSIDE_ABSURDO:
        return (False, "alvo degenerado")
    if motor_pendente:
        return (False, "motor pendente")
    return (True, None)
