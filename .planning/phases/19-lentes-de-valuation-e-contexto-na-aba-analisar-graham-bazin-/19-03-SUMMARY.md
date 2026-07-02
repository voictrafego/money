---
phase: 19-lentes-de-valuation-e-contexto-na-aba-analisar-graham-bazin-
plan: 03
subsystem: ui/app
tags: [valuation, graham, bazin, retorno, comparador-pares, read-only, streamlit]
requires:
  - src/analista/core/lentes.py (Plano 01: 4 lentes puras)
  - src/analista/core/fundamentals.py (CompanyData.serie_precos_ajustada — Plano 02)
provides:
  - app.py (branch Analisar: render read-only das 4 lentes)
affects:
  - Fase 19 (fecha o wiring das lentes na UI; encerra VAL-01/VAL-02/RET-01/PEER-01)
tech-stack:
  added: []
  patterns:
    - app-py-read-only (view só LÊ lentes.*/campos de c/a; zero fórmula na UI)
    - degradacao-graciosa (indisponível/ocultar/st.info neutro; nunca quebra a aba)
    - copy-exibe-nunca-recomenda (fronteira regulatória: sem compre/venda/ranking)
key-files:
  created: []
  modified:
    - app.py
decisions:
  - "As 4 lentes agrupadas numa seção única 'Lentes de referência (além do DDM)' logo após as métricas m1..m5, antes do gráfico — mantém contexto junto ao DDM"
  - "Comparador num expander (default fechado) p/ conter o custo de rede (montar() por par) — usuário opta por expandir"
  - "Valor de mercado escalado p/ R$ bi (valor/1e9 + ' B') na view; único cálculo aritmético é a escala de exibição, não fórmula de método"
metrics:
  duration: ~8min
  completed: 2026-07-02
---

# Phase 19 Plan 03: Render das 4 lentes na aba Analisar (read-only) Summary

Camada fina read-only em `app.py` que renderiza as 4 lentes da Fase 19 na aba **Analisar** —
cards de Graham e Bazin ao lado do valor intrínseco (DDM), bloco "quanto R$ 1.000 teriam
rendido" (1a/5a via Adj Close) e comparador de pares com o ticker analisado destacado — sempre
LENDO a engine (`lentes.*` + campos de `CompanyData`/`AnaliseAcao`), com zero fórmula na view,
degradação graciosa por lente e copy que exibe mas nunca recomenda.

## What Was Built

- **`app.py` (import):** `from analista.core import lentes` junto dos demais imports do pacote.
- **`app.py` (branch `if modo.startswith("Analisar")`)** — nova seção "Lentes de referência
  (além do DDM)", inserida logo após as métricas `m1..m5` e o bloco de alertas, antes do gráfico:
  - **Graham (VAL-01):** `lentes.vpa(PL, nº ações)` → `lentes.preco_justo_graham(lpa_valuation, vpa)`
    → `st.metric` com `delta = upside vs preço`; degrada para "indisponível" + disclaimer
    ("não vale para empresa sem lucro/PL positivo") quando `None`.
  - **Bazin (VAL-02):** `lentes.dpa_medio([c.dpa(ano) for ano in c.anos_ordenados()], n=5)` →
    `lentes.preco_teto_bazin` → `st.metric` com `delta = upside`; degrada para "indisponível" +
    disclaimer ("só vale para boas pagadoras") quando `None`.
  - **"Quanto teria rendido" (RET-01):** `lentes.retorno_periodo(c.serie_precos_ajustada, anos=1/5)`;
    cada janela `None` (histórico insuficiente) é OCULTADA; ambas `None` → caption neutra; nota
    honesta "rentabilidade passada não garante retorno futuro".
  - **Comparador de pares (PEER-01):** expander com `st.text_input` editável (default
    `TAEE11, EGIE3, CMIG4, ALUP11, CPFE3`), sempre incluindo o ticker analisado; `montar()` por
    par (cache), `lentes.metricas_par` → `lentes.tabela_pares(metricas, ticker_ativo)` →
    `lentes.pares_suficientes(tabela)`. Tabela `pd.DataFrame` com colunas Ticker / P/L / P/VP /
    ROE / DY / Valor de Mercado (R$ bi), linha alvo destacada com prefixo `➤`; pares
    insuficientes → `st.info` neutro. Sem ordenar/recomendar.

## Key Decisions

- **4 lentes agrupadas numa única seção** logo após `m1..m5` (antes do gráfico) — mantém as
  referências de valuation coladas ao DDM, como pedem os must_haves ("ao lado do DDM").
- **Comparador num expander fechado por padrão** — contém o custo de rede (PEER-01 é a única
  exceção à regra "zero rede nova"; buscar pares não-cacheados dispara fetch, igual à aba
  Ranking). O usuário decide expandir.
- **`esc_md`** em todo valor/ticker derivado de dado externo (mitigação T-19-01); montar() é
  `@st.cache_data` (mitigação T-19-02); degradação graciosa em toda lente.

## Deviations from Plan

**Ajuste de copy (não é bug/feature):** o caption do card Graham foi redigido sem o literal
numérico da constante ("raiz do produto de LPA, VPA e um fator fixo") em vez de "√(22,5×LPA×VPA)"
sugerido no texto da task. Motivo: o critério de aceite audita `grep -c "22.5\|sqrt\|0.06" == 0`
e, em regex, o `.` casaria "22,5" do caption — um falso positivo de "aritmética na view". A copy
segue educativa e neutra; nenhuma aritmética de método existe na view (Rule 1 — evitar falso
sinal de violação da regra locked read-only).

## Verification

- `.venv/bin/python -c "import ast; ast.parse(open('app.py').read())"` → app.py sintaticamente válido.
- `grep -c "preco_justo_graham\|preco_teto_bazin" app.py` == 2.
- `grep -c "22.5\|sqrt\|0.06" app.py` == 0 (nenhuma fórmula/aritmética de método na view).
- `grep -c "retorno_periodo\|tabela_pares\|pares_suficientes\|serie_precos_ajustada" app.py` == 6.
- `.venv/bin/python -m pytest -q` → **307 passed** (engine intacta; nenhum golden alterado).
- Só o branch Analisar (+ imports) foi tocado; Garimpar/Ranking/Swing/Início intactos.

## Self-Check: PASSED

- FOUND: app.py (import lentes + seção "Lentes de referência" no branch Analisar)
- FOUND commit: ac94209 (feat Graham+Bazin), eea824e (feat retorno+comparador)
</content>
</invoke>
