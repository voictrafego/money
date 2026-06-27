"""Trava o contrato do glossário técnico (UI-05/UI-06).

Garante que toda chave `tec_*` da seção técnica existe com texto não-vazio e que
nenhuma usa linguagem de ordem ("compre"/"venda") — o enquadramento é consultivo.
"""

from analista.glossario import h

# Lista canônica das chaves técnicas — fonte da verdade do contrato com a UI (Plan 04).
CHAVES_TEC = [
    "tec_indicadores",
    "tec_mm",
    "tec_cross",
    "tec_donchian",
    "tec_bollinger",
    "tec_squeeze",
    "tec_rsi",
    "tec_macd",
    "tec_adx",
    "tec_regressao",
    "tec_timing",
]

# Substrings de linguagem de ordem proibidas no tom consultivo (UI-06).
PROIBIDAS = ["compre", "venda", "compre agora"]


def test_chaves_tec_presentes():
    for k in CHAVES_TEC:
        texto = h(k)
        assert texto, f"chave de glossário ausente ou vazia: {k}"


def test_tom_consultivo():
    for k in CHAVES_TEC:
        texto = h(k).lower()
        for proibida in PROIBIDAS:
            assert proibida not in texto, (
                f"linguagem de ordem '{proibida}' encontrada em {k}; "
                "o glossário técnico deve ser consultivo (timing, nunca ordem)"
            )
