"""Teste soberano VAL-01 — o criterio de aceite mais duro do marco v2.4.

O motor RIM tem de reproduzir o caso-exemplo do PROPRIO livro (Cap. 17): injetando o Ke do livro
(constante do Cap. 17) nos insumos do book, o valor intrinseco cai na regiao de valor do livro.

Closed-form: chama `motores.rim` diretamente com os insumos do helper `insumos_itub4_livro`
(literal do ticker + numeros do Cap. 17 vivem no helper, FORA de funcao `test_` — higiene
BLIND-04a). Assere a REGIAO, nunca o ponto de nivel (`==` seria golden de nivel -> BLIND-04a).

Nao re-deriva Ke via CAPM (a engine estima ~15,86% para o book); injeta o Ke do livro. Zero knob
tocado: a regiao e' o gate, nao um numero para "chegar" mexendo em `excesso_sustentavel`.
"""

from __future__ import annotations

import pytest

import helpers_blindagem as hb
from analista.core import motores


@pytest.mark.contrato
def test_soberano_itub4_reproduz_caso_do_livro():
    res = motores.rim(**hb.insumos_itub4_livro())
    assert res is not None
    v = res.valor_intrinseco
    # REGIAO de valor do livro (Cap. 17), nunca o ponto de nivel: `==` seria golden de nivel.
    assert 35.0 <= v <= 39.0
