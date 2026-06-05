"""Glossário dos termos do método, para os tooltips (help=) da interface.

Definições curtas e fiéis ao livro *O Investidor em Ações de Dividendos*
(Orleans Martins & Felipe Pontes). O número do capítulo segue o próprio livro.
Texto em markdown (o tooltip do Streamlit renderiza markdown).
"""

from __future__ import annotations

# Definições individuais (chave curta -> texto do tooltip).
G: dict[str, str] = {
    "menu": (
        "**Três ferramentas, na ordem do método:**\n\n"
        "1. **Analisar uma ação** — estudo a fundo de um papel (múltiplos, valuation por DDM e fundamentos).\n"
        "2. **Garimpar carteira (BSD)** — passa vários tickers por um filtro de *dividendo grande e seguro*.\n"
        "3. **Ranking por múltiplos** — ordena candidatas e estima preço-alvo por regressão.\n\n"
        "Fluxo sugerido: garimpe → rankeie as melhores → analise as finalistas a fundo."
    ),
    "selic": (
        "Taxa básica de juros (meta Selic). Serve de **piso de comparação**: um Dividend Yield "
        "só é atraente se compensar o risco de trocar a renda fixa (Selic) pela renda variável."
    ),
    "ticker": "Código da ação na B3 (ex.: ITUB4, EGIE3, TAEE11). Units terminam em 11.",
    "preco": "Último preço de fechamento da ação no mercado (Yahoo Finance).",
    "valor_intrinseco": (
        "**Valor intrínseco (DDM)** — valor 'justo' estimado pelos fundamentos: os proventos "
        "futuros esperados trazidos a valor presente. Mostrado como intervalo entre o cenário "
        "otimista (g constante) e o conservador (modelo H). Acima do preço = ação barata. (Cap. 13–17)"
    ),
    "dy": (
        "**Dividend Yield (DY)** — proventos por ação ÷ preço da ação, em %. Quanto a ação 'rende' "
        "em dividendos. Compare com a Selic/renda fixa, lembrando que ação tem risco maior. (Cap. 10)"
    ),
    "roe": (
        "**ROE — Retorno sobre o Patrimônio Líquido** — lucro líquido recorrente ÷ patrimônio líquido. "
        "Quanto de lucro a empresa gera para cada R$ 1 de capital próprio. Usa-se o PL médio "
        "(inicial+final)/2; indisponível no 1º ano sem histórico. (Cap. 10)"
    ),
    "ke": (
        "**Ke — custo do capital próprio** — retorno mínimo que o investidor exige para correr o risco "
        "da ação; é a taxa de desconto do DDM. Pelo CAPM: Ke = juro livre de risco + Beta × prêmio de "
        "mercado. (Cap. 16)"
    ),
    # ---- Aba Múltiplos & Crescimento ----
    "tab_multiplos": (
        "**Múltiplos (Cap. 10)**\n\n"
        "- **ML — Margem Líquida**: lucro líquido ÷ vendas. Quanto da receita vira lucro.\n"
        "- **ROE**: lucro ÷ patrimônio líquido (rentabilidade do capital próprio).\n"
        "- **P/L — Preço/Lucro**: quantas vezes o preço cabe no lucro por ação (≈ anos para recuperar o investido).\n"
        "- **EY — Earnings Yield**: lucro por ação ÷ preço (o inverso do P/L), comparável a juros.\n"
        "- **DP — Payout**: % do lucro distribuído como proventos. Acima de 100% é alerta.\n"
        "- **DY — Dividend Yield**: proventos ÷ preço, em %."
    ),
    "tab_crescimento": (
        "**Crescimento e custo de capital (Cap. 14/16)**\n\n"
        "- **g histórico (CAGR)**: crescimento médio do lucro nos últimos anos.\n"
        "- **g por fundamentos**: ROE × (1 − payout), o crescimento que a empresa se autofinancia.\n"
        "- **g alto**: taxa adotada para a fase de crescimento.\n"
        "- **g estável (perpetuidade)**: taxa perpétua; não deve superar o crescimento do PIB.\n"
        "- **Beta**: risco da ação vs. mercado (1 = igual ao mercado; >1 mais volátil).\n"
        "- **Ke (CAPM)**: retorno exigido pelo investidor (taxa de desconto)."
    ),
    # ---- Aba Valuation ----
    "tab_ddm": (
        "**Valuation por Desconto de Dividendos (DDM) — Cap. 13–17**\n\n"
        "Valor justo = proventos futuros trazidos a valor presente.\n\n"
        "- **Otimista (g constante)**: modelo de Gordon, dividendos crescendo a uma taxa fixa.\n"
        "- **Conservador (modelo H)**: o crescimento alto **cai aos poucos** até a taxa estável "
        "(mais realista para empresas saindo do crescimento).\n"
        "- **VP dividendos**: parte do valor vinda dos proventos do período projetado.\n"
        "- **VP residual**: parte vinda da perpetuidade (após a fase de alto crescimento)."
    ),
    "tab_sensibilidade": (
        "**Sensibilidade** — mostra quanto o valor muda ao mexer no custo de capital (Ke, nas linhas) "
        "e no crescimento (g, nas colunas). O DDM é muito sensível a essas duas taxas: o maior valor "
        "fica com g alto + Ke baixo; o menor, com g baixo + Ke alto. (Cap. 12/17)"
    ),
    # ---- Modo Garimpar ----
    "bsd": (
        "**BSD — Big, Safe Dividend** (Charles Carlson, Cap. 8) — nota de 0 a 100 que combina dez "
        "fatores de estabilidade e crescimento dos dividendos, sendo o **payout** o de maior peso (30%). "
        "Carlson recomenda focar em empresas com **BSD acima de 80** (no estudo do livro, só 19 de 297 "
        "empresas brasileiras passaram).\n\n"
        "- **Nota absoluta**: cada fator é comparado a uma **referência fixa** (não às outras ações "
        "coladas no lote), então a mesma ação tem o mesmo BSD em qualquer execução e o corte 80 vale "
        "de verdade.\n"
        "- **Crescimento de longo prazo**: na ausência de estimativa de analistas, é um **proxy por "
        "fundamentos** = ROE × (1 − payout) (média da janela), não uma previsão de analistas.\n"
        "- **Dados faltantes**: um fator sem dado entra como **neutro**, não como pior nota; o app "
        "indica **quantos fatores faltaram** em cada empresa."
    ),
    # ---- Modo Ranking ----
    "ranking": (
        "**Ranking por múltiplos + preço-alvo (Cap. 11–12)** — padroniza os múltiplos em nota 0–100 e "
        "estima o **preço justo** por regressão (P/L explicado por payout e ROE do setor). "
        "**Upside** = quanto o preço-alvo está acima do preço atual; positivo = candidata a estar barata "
        "(subavaliada). Use de preferência empresas do mesmo setor."
    ),
    # ---- Fase 2: ano-base, dual-payout, indisponível ----
    "ano_base": (
        "**Ano-base** — último exercício (ano) com lucro coletado para esta empresa, vindo das "
        "demonstrações da CVM. Empresas diferentes podem ter ano-base diferente conforme o que já "
        "foi divulgado; quando os anos divergem, a comparação mistura períodos — fique atento a isso."
    ),
    "payout_dual": (
        "**Por que dois payouts?** O *Payout (último ano)* é a fatia do lucro distribuída no exercício "
        "mais recente. O *Payout p/ valuation (média 3a)* é a média projetada dos últimos 3 anos "
        "(com teto de 100%), e é esse que o modelo de valuation (DDM) usa para estimar o valor justo. "
        "Quando os dois divergem, o app mostra ambos para você entender de onde vem o preço-alvo."
    ),
    "indisponivel": (
        "**indisponível** — esta empresa foi deixada de fora da regressão de preço-alvo porque faltou "
        "ROE ou payout para estimá-la. Não é 'cara' nem 'barata': simplesmente não há dado suficiente "
        "para o cálculo."
    ),
}


def h(chave: str) -> str | None:
    """Retorna o texto de ajuda para a chave, ou None se não existir."""
    return G.get(chave)
