"""core/sanidade.py — os cinco checks aritméticos de sanidade dos dados (SAN-01..SAN-05).

Funções PURAS sobre `CompanyData`: sem I/O, sem rede, sem estado — o espelho de
`core/normalizacao.py`. Nenhuma dependência nova (`pandera`/`great-expectations` são
**proibidos**: isto são cinco asserts aritméticos, não um framework de validação).

TRÊS VERDADES QUE MORAM AQUI DE PROPÓSITO (apagá-las convida a Fase 9 a errar):

1. **SAN-01 e SAN-02 são o MESMO bug visto de dois ângulos** — nível (escala absoluta) vs.
   série temporal (salto ano-a-ano). Ambos nascem de `cvm.py:242` lendo a conta `3.99.01.01`
   sem validar escala nem semântica, e de `build.py:87` dividindo `LL / LPA` para inventar
   `num_acoes`. Consertar UM na Fase 9 e achar que consertou os dois é o erro que esta nota
   existe para impedir.

2. **Os limiares NÃO são knobs de valuation** (D-10). Um limiar de detecção não move `Ke`,
   não move `g`, não move preço — logo NÃO entra no `config.yaml` nem no `calibracao.lock.yaml`.
   O lock tem exatamente 3 graus de liberdade (`ERP`, `n_fade`, `PIB_real`); um 4º deixa a
   suíte vermelha por construção. Estes limiares são constantes de MÓDULO, congeladas por um
   teste `invariante` (D-11).

3. **NADA aqui conserta nada.** Os checks LEEM o dado sujo e RELATAM. Se um check flaga um
   ticker, isso é o sistema funcionando — não um bug para corrigir. Estes asserts SÃO o teste
   de regressão da Fase 9: apagar uma flag consertando o dado aqui destrói a prova. O conserto
   (num_acoes, _fator_unit, lpa, JCP) é a Fase 9 (DATA), não este módulo.

O SAN-01 roda sobre `c.num_acoes` (pós-`_fator_unit`), o campo que os motores consomem — é
exatamente onde o mascaramento acontece. A ALUP11, p.ex., é atribuída pelo REQUIREMENTS ao
SAN-04; NÃO "consertar" o `_fator_unit` para o SAN-01 acender nela é o mesmo princípio (3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from .fundamentals import CompanyData

# --------------------------------------------------------------------------- #
# LIMIARES (D-10) — constantes de MÓDULO. NÃO vão para config.yaml nem para o
# calibracao.lock.yaml. Limiar de detecção NÃO é knob de valuation. Congelados
# por tests/test_sanidade_limiares.py (categoria `invariante`, D-11).
# --------------------------------------------------------------------------- #
LIMIAR_SAN01 = 1.5      # simétrico: flaga max(f, 1/f) >= 1.5 (desvio > 50%, D-09)
LIMIAR_SAN02 = 3.0      # simétrico: flaga max(r, 1/r) >= 3.0 (medido: ignora bonificação real da B3)
LIMIAR_SAN03 = 1.5      # simétrico: razão das SOMAS da janela (consistência CVM<->Yahoo)
LIMIAR_SAN03_JCP = 1.10  # detector direto de JCP perdido, 100% interno à CVM
LIMIAR_SAN04 = 0.10     # flaga |LL/LL_controlador - 1| > 10% (ou sinais divergentes)
LIMIAR_SAN05 = 0.10     # resíduo mediano do clean surplus > 10% do PL
TOLERANCIA_SPLIT = 0.20  # isenção D-12: |salto / Πfatores_do_ano - 1| < 20%


@dataclass
class Aviso:
    """Flag de sanidade disparada. `fator` é SEMPRE adimensional — nunca um R$.

    `sinal_invertido` vive FORA do `bucket`: o bucket usa abs(fator) e nunca levanta,
    mas o SAN-04 (CSNA3) precisa registrar que os minoritários e o controlador têm
    sinais opostos — informação que se perderia se ela fosse embutida no bucket.
    """

    check: str
    ano: Optional[int]
    fator: float
    bucket: str
    detalhe: str
    sinal_invertido: bool = False


def _bucket(fator: float) -> str:
    """Ordem de grandeza (D-07), como STRING — nunca a magnitude exata.

    String (não constante numérica) de propósito: o baseline serializa isto, e o detector
    do BLIND-04a não se aproxima de uma string. Um re-download do Yahoo mexendo no terceiro
    decimal NÃO vira teste vermelho; silenciar a flag sem corrigir a escala TEM que quebrar.

    NUNCA levanta com fator <= 0: opera sobre abs(fator) e devolve "~0" para zero, sem jamais
    chamar `log10` de negativo ou de zero (que levantariam `ValueError`). Se estourasse aqui,
    o try/except do `aplicar_sanidade` (plano 08-05) engoliria a exceção e converteria uma
    detecção REAL em "não avaliável", em silêncio — o oposto exato do requisito.
    """
    f = abs(fator)
    if f == 0:
        return "~0"
    return f"~1e{round(math.log10(f))}"


def checar_san01(c: CompanyData) -> Optional[Aviso]:
    """Escala de nível: `num_acoes × preço ≈ market cap`.

    Referência = `c.market_cap` (o Yahoo satisfaz marketCap = preço × implied_shares_outstanding,
    e o implied_shares_outstanding bate com a contagem oficial da CVM com erro < 0,3% em 5/5).
    NUNCA usar a contagem só-da-classe-negociada (ON ou PN isolada) como referência: produziria
    falso positivo ~2× em toda empresa com PN. A base é ON+PN (implícita no market_cap).

    Sem market_cap / preço / num_acoes[ult] → None (não avaliável — nem flag, nem exceção).
    É o caso do MRFG3 (404 no Yahoo) e o caso vivo do never-raise (SAN-06).
    """
    ult = c.ultimo_ano()
    if ult is None:
        return None
    na = c.num_acoes.get(ult)
    if not na or not c.preco_atual or not c.market_cap:
        return None
    fator = na * c.preco_atual / c.market_cap
    if fator <= 0 or max(fator, 1.0 / fator) < LIMIAR_SAN01:
        return None
    return Aviso(
        check="SAN-01",
        ano=ult,
        fator=fator,
        bucket=_bucket(fator),
        detalhe="num_acoes[ult] × preço / market_cap fora de 1,0 — escala de num_acoes suspeita.",
    )


def checar_san02(c: CompanyData) -> List[Aviso]:
    """Salto de `num_acoes` ano-a-ano sem evento societário — SIMÉTRICO.

    O salto aparece DUAS vezes (entrada e saída do ano quebrado), por isso o check é simétrico
    (`max(r, 1/r) >= LIMIAR_SAN02`): olhar só aumento pegaria o ano são e deixaria o doente passar.

    Fronteira de fonte (Achado 2c): par de anos com origem diferente NÃO é avaliável (troca de
    fonte produz salto artificial, não bug de dado). Isenção por split (D-12): salto isento
    quando o `c.splits` registra desdobramento(s) no ano `t` cujo produto satisfaz
    `|r / Πfatores - 1| < TOLERANCIA_SPLIT`. `c.splits` vazio → nenhuma isenção (falha na direção
    segura: o falso positivo fica VISÍVEL). O `bucket` usa o `r` CRU (direcional).
    """
    avisos: List[Aviso] = []
    anos = c.anos_ordenados()
    for i in range(1, len(anos)):
        t, p = anos[i], anos[i - 1]
        n_curr = c.num_acoes.get(t)
        n_prev = c.num_acoes.get(p)
        if n_prev in (None, 0) or n_curr is None:
            continue
        # fronteira de fonte: só pula quando ambas as origens existem E divergem.
        origem_t = c.origem_num_acoes.get(t)
        origem_p = c.origem_num_acoes.get(p)
        if origem_t is not None and origem_p is not None and origem_t != origem_p:
            continue
        r = n_curr / n_prev
        severidade = max(r, 1.0 / r) if r > 0 else float("inf")
        if severidade < LIMIAR_SAN02:
            continue
        # isenção por split (D-12): só o ANO importa; não construir datetime.
        produto = 1.0
        tem_split = False
        for chave, fator_split in c.splits.items():
            try:
                ano_split = int(str(chave)[:4])
            except (ValueError, TypeError):
                continue
            if ano_split == t:
                produto *= fator_split
                tem_split = True
        if tem_split and produto > 0 and abs(r / produto - 1.0) < TOLERANCIA_SPLIT:
            continue
        avisos.append(
            Aviso(
                check="SAN-02",
                ano=t,
                fator=r,
                bucket=_bucket(r),
                detalhe="num_acoes saltou entre anos consecutivos sem split compatível.",
            )
        )
    return avisos
