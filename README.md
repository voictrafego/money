# Analista de Ações de Dividendos

MVP de um analista fundamentalista que replica **exatamente** a metodologia do livro
**_O Investidor em Ações de Dividendos_** (Orleans Martins & Felipe Pontes, 2022): do
garimpo de empresas ao valuation por desconto de dividendos.

100% gratuito — usa apenas fontes públicas:

| Dado | Fonte (grátis) |
|------|----------------|
| Fundamentos (LL, PL, FCO, receita, dívida) — 10 anos | **CVM** Dados Abertos (DFP em CSV) |
| Preços, dividendos, nº de ações, beta | **yfinance** (Yahoo Finance) |
| Selic, IPCA | **Banco Central** (API SGS) |

> O livro usa a Refinitiv Eikon (paga). Substituímos por CVM + yfinance + BCB sem perder a
> metodologia. Cada fórmula referencia o capítulo do livro no docstring.

## Instalação

```bash
cd analista_dividendos
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip install -e .
```

## Uso — Interface web (recomendado)

A forma mais simples: uma página no navegador onde você digita o ticker e vê tudo.

```bash
./.venv/bin/streamlit run app.py
```

Ou, no Finder, dê **duplo-clique em `abrir.command`**. Abre em `http://localhost:8501`.
Três telas no menu lateral: **Analisar uma ação**, **Garimpar carteira (BSD)** e **Ranking por múltiplos**.

## Uso — Linha de comando

```bash
# Análise completa de uma ação (múltiplos + DDM + veredito) -> out/ITUB4.md
./.venv/bin/python -m analista analyze ITUB4

# Garimpo (Cap. 8): filtros customizados + ranking Big, Safe Dividend -> out/screen.csv
./.venv/bin/python -m analista screen --tickers TAEE11,EGIE3,CMIG4,ALUP11,TRPL4

# Ranking por múltiplos padronizados + preço-alvo por regressão (Cap. 11-12)
./.venv/bin/python -m analista rank --tickers TAEE11,EGIE3,CMIG4,ALUP11,CPFE3,EQTL3
```

Parâmetros (thresholds dos filtros, pesos do BSD, n de anos do DDM, Rf/ERP do CAPM) ficam
em `config.yaml`.

## Metodologia → onde está no código

| Capítulo do livro | Módulo |
|---|---|
| Cap. 8 — Garimpo: filtros customizados, Graham, Big Safe Dividend | `core/screening.py` |
| Cap. 8 — Estágio do ciclo de vida (Damodaran) | `core/lifecycle.py` |
| Cap. 10 — Múltiplos (ML, ROE, P/L, PEG, EY, DP, CDC, DY, YOC, RTA) | `core/multiples.py` |
| Cap. 11-12 — Comparáveis, regressão P/L~f(DP,ROE), preço-alvo | `core/comparables.py` |
| Cap. 14 — Taxa de crescimento (histórico, fundamentos, estável) | `core/growth.py` |
| Cap. 16 — Custo de capital (CAPM: Ke = Rf + β·ERP) | `core/capm.py` |
| Cap. 15/17 — DDM de dois estágios + valor residual + modelo H | `core/ddm.py` |

## Validação contra o livro

Os exemplos numéricos do livro são testes "golden" (`pytest`):

- **Itaú (Cap. 17):** Ke = 12,48%; DDM com g=10,24%, payout 75,1% → valor intrínseco
  **R$ 37,22** (VP dividendos R$ 19,23 + VP residual R$ 17,99).
- **CTEEP (Cap. 12):** P/L esperado ≈ 14,18 → preço-alvo ≈ **R$ 37,22**, upside ~68%.
- Múltiplos de Hypera, MRV, Engie, Odontoprev (Cap. 10).

```bash
./.venv/bin/python -m pip install pytest
./.venv/bin/python -m pytest
```

## Mapeamento de tickers (CVM)

O ticker da B3 não existe no dado da CVM. A resolução ticker → CD_CVM usa:
1. `data/ticker_map.json` (override curado — tem precedência);
2. casamento por nome (Yahoo × cadastro CVM).

Para adicionar uma empresa, inclua `"TICKER": CD_CVM` no `ticker_map.json` (o CD_CVM está
no cadastro `cad_cia_aberta`, baixado em `data/cvm/`).

## Limitações (fontes gratuitas)

- **Dividendos via Yahoo** são agregados por ano-calendário do ex-date e não separam JCP de
  dividendo; isso gera ruído no payout de alguns anos. O DDM usa média de 3 anos para mitigar.
- **FCO de bancos** é volátil (atividade operacional financeira), afetando o CDC.
- **yfinance** ocasionalmente retorna 404 transitório para alguns `.SA` (rate limit) — basta
  repetir. Os fundamentos da CVM continuam disponíveis em cache.
- O filtro "DY > Selic" fica restritivo quando a Selic está alta (ex.: 14,5%); ajuste
  `screening.custom.dy_corte` para um valor fixo se quiser o comportamento do livro (Selic 2019 = 4,5%).
