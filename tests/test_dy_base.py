"""Contrato DATA-05 — o DY DECLARA sua base ao usuário: é BRUTO (antes de IRRF).

O `multiples.dividend_yield` é `DPA/Preço`, sem imposto — proventos BRUTOS. A decisão
travada da Fase 9 (menor risco, sem calcular imposto especulativo da Lei 15.270/2025 não
verificada) é DECLARAR a base explicitamente onde o usuário lê o número: no `help` do
header (`presentation.header_dy`, ambos os caminhos, recorrente e fallback) e no glossário.

Assertos de CONTRATO sobre STRING (substring "bruto", case-insensitive) — sem literal de
ticker + constante numérica de nível no mesmo assert (BLIND-04a). Trava a AUSÊNCIA de
ambiguidade sobre a base do DY; não trava nenhum valor de mercado nem de valuation.
"""

from analista import glossario
from analista.report import presentation


def test_header_dy_recorrente_declara_base_bruta():
    # caminho normal (recorrente é o principal): o help declara que o DY é bruto.
    h = presentation.header_dy(0.06, 0.07)
    assert h["fallback"] is False
    assert "bruto" in h["help"].lower()


def test_header_dy_fallback_declara_base_bruta():
    # caminho fallback (recorrente indisponível → trailing vira principal): também declara.
    h = presentation.header_dy(None, 0.05)
    assert h["fallback"] is True
    assert "bruto" in h["help"].lower()


def test_glossario_do_dy_declara_base_bruta():
    # o verbete do DY no glossário (tooltip) declara a base bruta.
    verbete = glossario.h("dy")
    assert verbete is not None
    assert "bruto" in verbete.lower()
