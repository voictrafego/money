"""Selo de Sustentabilidade do Dividendo (Fase 20 / SELO-01 e SELO-02).

Camada de DERIVAÇÃO pura sobre números que a engine JÁ calcula e testa:
- o `bsd` (0-100) de `core/screening.py` → cor do selo (config-driven);
- a string de veredito do DDM (`report.py`) → faixa de preço;
- o cruzamento qualidade×preço → rótulo de quadrante (JOIA / VALUE TRAP / ...).

Nenhum método novo, nenhum recálculo fundamentalista.

Princípios (espelham o firewall de `report/setup.py`):
- FIREWALL: este módulo NUNCA importa `report.py`. Recebe só PRIMITIVOS (bsd float,
  veredito str, cfg dict). É `report.py` quem chama `montar_selo` — nunca o contrário.
  Isso preserva os goldens da engine fundamentalista e o veredito de preço intactos.
- CONFIG-DRIVEN: os cortes de cor vêm de `cfg["selo"]["cor"]` (zero hardcode espalhado).
- COPY DESCRITIVA, NUNCA RECOMENDAÇÃO (gate regulatório): "JOIA"/"VALUE TRAP" descrevem
  a combinação qualidade×preço — EXIBEM, jamais dizem "compre/venda".
- DEGRADAÇÃO GRACIOSA: never-raise para a UI; falta de dado colapsa em None/False.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Selo:
    """Selo derivado (aditivo, defaults degradáveis).

    `cor`      : verde | azul | amarelo | vermelho (None quando o BSD é indisponível)
    `qualidade`: Alta (verde/azul) | Baixa (amarelo/vermelho) | None
    `faixa_preco`: Barato | Justo | Caro | None (None em VERIFICAR/veredito ausente)
    `rotulo`   : rótulo do quadrante qualidade×preço (None quando falta qualidade/faixa)
    `verificar`: True quando o veredito é VERIFICAR — alerta 'verificar dados' que se
                 sobrepõe ao rótulo de preço (D2), sem atribuir faixa.
    """

    bsd: Optional[float] = None
    cor: Optional[str] = None
    qualidade: Optional[str] = None
    faixa_preco: Optional[str] = None
    rotulo: Optional[str] = None
    verificar: bool = False


# Matriz de rótulos do quadrante (D2) — copy ESTÁVEL, NÃO tunável (fica no código de propósito;
# os limiares de cor é que são tunáveis em config.yaml). Descreve qualidade×preço; nunca é ordem.
_MATRIZ = {
    ("Alta", "Barato"): "JOIA",
    ("Alta", "Justo"): "Boa, no preço",
    ("Alta", "Caro"): "Boa, mas cara",
    ("Baixa", "Barato"): "VALUE TRAP",
    ("Baixa", "Justo"): "Fraca",
    ("Baixa", "Caro"): "Evitar",
}


def cor_do_bsd(bsd: Optional[float], cfg: dict) -> Optional[str]:
    """Deriva a cor do selo a partir do score BSD (0-100) e dos cortes de `cfg["selo"]["cor"]`.

    verde >= verde_min · azul_min <= azul < verde_min · amarelo_min <= amarelo < azul_min ·
    vermelho < amarelo_min. None quando o BSD é indisponível (never-raise).
    """
    if bsd is None:
        return None
    cortes = (cfg.get("selo") or {}).get("cor") or {}
    verde_min = cortes.get("verde_min", 70)
    azul_min = cortes.get("azul_min", 55)
    amarelo_min = cortes.get("amarelo_min", 40)
    if bsd >= verde_min:
        return "verde"
    if bsd >= azul_min:
        return "azul"
    if bsd >= amarelo_min:
        return "amarelo"
    return "vermelho"


def _qualidade(cor: Optional[str]) -> Optional[str]:
    """Eixo Qualidade do quadrante: verde/azul → 'Alta'; amarelo/vermelho → 'Baixa'."""
    if cor in ("verde", "azul"):
        return "Alta"
    if cor in ("amarelo", "vermelho"):
        return "Baixa"
    return None


def faixa_do_veredito(veredito: Optional[str]) -> Optional[str]:
    """Eixo Preço do quadrante, pelo PREFIXO do veredito do DDM (read-only).

    SUBAVALIADA → 'Barato' · 'NO INTERVALO' → 'Justo' · SOBREAVALIADA → 'Caro'.
    VERIFICAR / vazio / qualquer outro formato → None (T-20-01: casa só prefixos conhecidos).
    """
    if not veredito:
        return None
    if veredito.startswith("SUBAVALIADA"):
        return "Barato"
    if veredito.startswith("NO INTERVALO"):
        return "Justo"
    if veredito.startswith("SOBREAVALIADA"):
        return "Caro"
    return None


def montar_selo(bsd: Optional[float], veredito: Optional[str], cfg: dict) -> Selo:
    """Cruza qualidade (cor do BSD) × preço (veredito do DDM) num Selo (never-raise).

    - deriva cor → qualidade a partir do BSD;
    - VERIFICAR (salvaguarda DDM-FIX-05) é OVERLAY separado (D2): marca `verificar=True`,
      NÃO atribui faixa de preço nem rótulo de quadrante (o alerta se sobrepõe ao rótulo);
    - senão, faixa = faixa_do_veredito e rótulo = _MATRIZ[(qualidade, faixa)] só quando ambos
      existem — degrada para None em qualquer buraco de dado.

    Copy: JOIA/VALUE TRAP EXIBEM a combinação qualidade×preço; NUNCA são ordem de compra/venda.
    """
    cor = cor_do_bsd(bsd, cfg)
    qualidade = _qualidade(cor)

    verificar = bool(veredito) and veredito.startswith("VERIFICAR")
    if verificar:
        return Selo(bsd=bsd, cor=cor, qualidade=qualidade,
                    faixa_preco=None, rotulo=None, verificar=True)

    faixa = faixa_do_veredito(veredito)
    rotulo = _MATRIZ.get((qualidade, faixa)) if (qualidade and faixa) else None
    return Selo(bsd=bsd, cor=cor, qualidade=qualidade,
                faixa_preco=faixa, rotulo=rotulo, verificar=False)
