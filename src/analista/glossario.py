"""Glossário dos termos do método, para os tooltips (help=) da interface.

Definições curtas e descritivas dos termos da metodologia. As referências e
a fundamentação completa ficam na página "Metodologia e referências" (link no rodapé).
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
        "otimista (g constante) e o conservador (modelo H). Acima do preço = ação barata."
    ),
    "dy": (
        "**Dividend Yield (DY)** — proventos por ação ÷ preço da ação, em %. Quanto a ação 'rende' "
        "em dividendos. Compare com a Selic/renda fixa, lembrando que ação tem risco maior."
    ),
    "roe": (
        "**ROE — Retorno sobre o Patrimônio Líquido** — lucro líquido recorrente ÷ patrimônio líquido. "
        "Quanto de lucro a empresa gera para cada R$ 1 de capital próprio. Usa-se o PL médio "
        "(inicial+final)/2; indisponível no 1º ano sem histórico."
    ),
    "ke": (
        "**Ke — custo do capital próprio** — retorno mínimo que o investidor exige para correr o risco "
        "da ação; é a taxa de desconto do DDM. Pelo CAPM: Ke = juro livre de risco + Beta × prêmio de "
        "mercado."
    ),
    # ---- Aba Múltiplos & Crescimento ----
    "tab_multiplos": (
        "**Múltiplos**\n\n"
        "- **ML — Margem Líquida**: lucro líquido ÷ vendas. Quanto da receita vira lucro.\n"
        "- **ROE**: lucro ÷ patrimônio líquido (rentabilidade do capital próprio).\n"
        "- **P/L — Preço/Lucro**: quantas vezes o preço cabe no lucro por ação (≈ anos para recuperar o investido).\n"
        "- **EY — Earnings Yield**: lucro por ação ÷ preço (o inverso do P/L), comparável a juros.\n"
        "- **DP — Payout**: % do lucro distribuído como proventos. Acima de 100% é alerta.\n"
        "- **DY — Dividend Yield**: proventos ÷ preço, em %."
    ),
    "tab_crescimento": (
        "**Crescimento e custo de capital**\n\n"
        "- **g histórico (tendência log-linear)**: ritmo de crescimento do lucro estimado por "
        "regressão log-linear sobre a série de lucro normalizada (mede a tendência, robusta a anos atípicos).\n"
        "- **g por fundamentos**: ROE × (1 − payout), o crescimento que a empresa se autofinancia.\n"
        "- **g alto**: taxa adotada para a fase de crescimento.\n"
        "- **g estável (perpetuidade)**: taxa perpétua; não deve superar o crescimento do PIB.\n"
        "- **Beta**: risco da ação vs. mercado (1 = igual ao mercado; >1 mais volátil).\n"
        "- **Ke (CAPM)**: retorno exigido pelo investidor (taxa de desconto)."
    ),
    # ---- Aba Valuation ----
    "tab_ddm": (
        "**Valuation por Desconto de Dividendos (DDM)**\n\n"
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
        "fica com g alto + Ke baixo; o menor, com g baixo + Ke alto."
    ),
    # ---- Modo Garimpar ----
    "bsd": (
        "**BSD — Big, Safe Dividend** — nota de 0 a 100 que combina dez "
        "fatores de estabilidade e crescimento dos dividendos, sendo o **payout** o de maior peso (30%). "
        "O corte de referência é **BSD acima de 80** — nota alta e rara (num estudo de referência com "
        "297 empresas brasileiras, só 19 passaram).\n\n"
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
        "**Ranking por múltiplos + preço-alvo** — padroniza os múltiplos em nota 0–100 e "
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
        "mais recente (valor cru, pode estar distorcido por um ano atípico). O *Payout p/ valuation "
        "(sustentável)* é a **mediana da série histórica completa** (sem teto/clamp), e é esse que o "
        "modelo de valuation (DDM) usa para estimar o valor justo — mais robusto a anos extremos. "
        "Quando os dois divergem, o app mostra ambos para você entender de onde vem o preço-alvo."
    ),
    "indisponivel": (
        "**indisponível** — esta empresa foi deixada de fora da regressão de preço-alvo porque faltou "
        "ROE ou payout para estimá-la. Não é 'cara' nem 'barata': simplesmente não há dado suficiente "
        "para o cálculo."
    ),
    # ---- Fase 7: indicadores técnicos (consultivos — timing, nunca ordem) ----
    "tec_indicadores": (
        "**Indicadores técnicos (consultivo)** — leitura do *timing* a partir do histórico de preço, "
        "para ajudar a escolher **quando** olhar uma ação que os fundamentos já indicam. São "
        "**secundários e auxiliares**: o veredito vem do método (DDM/múltiplos); o técnico só sugere "
        "timing e dispara reverificação dos fundamentos quando o preço perde a tendência. Nunca dizem "
        "'comprar' ou 'vender'."
    ),
    "tec_mm": (
        "**Médias móveis (MM 20/50/200)** — a média do preço de fechamento nas últimas N barras, "
        "suavizando o ruído para revelar a tendência. **SMA** dá peso igual a todas as barras; **EMA** "
        "dá mais peso às recentes. A posição do preço **acima ou abaixo da MM200** resume a tendência "
        "de fundo: acima = força compradora predominante; abaixo = fraqueza. Referência de timing, "
        "não recomendação."
    ),
    "tec_cross": (
        "**Cruzamentos (golden/death cross)** — o cruzamento da MM50 com a MM200. **Golden cross** "
        "(MM50 cruza para cima) sinaliza fortalecimento da tendência; **death cross** (MM50 cruza para "
        "baixo) sinaliza enfraquecimento. Servem de gatilho para **reverificar os fundamentos** no "
        "momento da virada, não como ordem por si só."
    ),
    "tec_donchian": (
        "**Canal de Donchian (20/55)** — a faixa entre a **máxima** e a **mínima** dos últimos N "
        "períodos. Romper a máxima do canal indica força/continuação da alta; perder a mínima indica "
        "fraqueza e é um gatilho para **reverificar os fundamentos**. Mostra onde o preço está dentro "
        "do seu próprio histórico recente."
    ),
    "tec_bollinger": (
        "**Bandas de Bollinger (20, 2σ)** — uma média de 20 períodos com duas bandas a 2 desvios-padrão "
        "acima e abaixo, medindo a volatilidade. O preço passa a maior parte do tempo **dentro** das "
        "bandas; um **toque** na banda superior/inferior indica esticamento de curto prazo, útil para o "
        "timing fino — referência consultiva, nunca uma ordem de operação."
    ),
    "tec_squeeze": (
        "**Squeeze (estreitamento)** — quando as bandas de Bollinger se **estreitam**, a volatilidade "
        "está baixa e a tendência, indefinida; costuma anteceder um movimento mais forte, **sem dizer a "
        "direção**. É um aviso de 'atenção ao timing', não um sinal de entrada."
    ),
    "tec_rsi": (
        "**RSI (14, Wilder)** — Índice de Força Relativa, oscila de 0 a 100 e mede o fôlego do movimento. "
        "Abaixo de **30** o ativo está sobrevendido (esticado para baixo); acima de **70**, sobrecomprado "
        "(esticado para cima). Ajuda no timing fino — em tendência forte pode ficar esticado por bastante "
        "tempo, então é referência, não ordem."
    ),
    "tec_macd": (
        "**MACD (12/26/9)** — diferença entre duas médias exponenciais (12 e 26) com uma linha de sinal "
        "(9). O **cruzamento** da linha MACD com a de sinal indica mudança de momentum: para cima = "
        "momentum se fortalecendo; para baixo = enfraquecendo. Lê o *timing* da tendência, sem ser "
        "recomendação de operação."
    ),
    "tec_adx": (
        "**ADX (14, Wilder)** — mede a **força** da tendência (não a direção), de 0 a 100. Abaixo de "
        "**20** indica ausência de tendência (lateralização); acima de **25**, tendência definida (de "
        "alta ou de baixa). Diz **se** vale ler os demais sinais direcionais, não o que fazer."
    ),
    "tec_regressao": (
        "**Regressão da tendência** — ajusta uma reta ao preço recente e reporta a **inclinação "
        "anualizada** (ritmo e direção da tendência) e o **R²** (quão bem a reta descreve o movimento: "
        "perto de 1 = tendência limpa; perto de 0 = ruído). Quantifica a tendência para o timing, sem "
        "emitir ordem."
    ),
    "tec_timing": (
        "**Resumo de timing (consultivo)** — combina os indicadores acima num retrato do momento "
        "(tendência de fundo + força + momentum) para sugerir **quando** acompanhar a ação. É sempre "
        "**subordinado ao fundamento**: nunca sobrepõe o veredito barato/caro do método e, ao romper a "
        "tendência, apenas pede que você **reverifique os fundamentos**."
    ),
    # ---- Colunas das tabelas (Garimpar / Ranking / Pares / Comparar / Histórico) ----
    "selo": (
        "**Selo de Sustentabilidade do Dividendo** — cor que cruza a *qualidade* do dividendo "
        "(nota BSD) com o *preço* (veredito do DDM): bom e barato = **joia**; bom, mas caro = "
        "**espere**; ruim e barato = **cilada de valor**; ruim e caro = **evite**. Triagem visual, "
        "não recomendação."
    ),
    "passa_filtros": (
        "**Passa filtros** — 'Sim' quando a ação cumpre os cortes objetivos do método: Dividend "
        "Yield acima da Selic (**DY > Selic**), liquidez (volume diário mínimo) e **ROE mínimo**. "
        "Comece por aqui: o BSD sozinho não é recomendação."
    ),
    "bsd_maior_80": (
        "**BSD > 80** — se a nota BSD ultrapassa o corte de referência **80** ('dividendo grande e "
        "seguro'). Nota alta e rara; ainda assim, só faz sentido junto de 'Passa filtros'."
    ),
    "fatores_faltando": (
        "**Fatores faltando** — quantos fatores do BSD ficaram sem dado para esta empresa. Fatores "
        "ausentes entram como **neutros** (não como pior nota); quanto mais faltando, menos "
        "confiável é o BSD."
    ),
    "setor": (
        "**Setor** — classificação setorial da empresa (CVM/B3). Compare de preferência ações do "
        "**mesmo setor**, pois os múltiplos 'normais' variam muito entre setores."
    ),
    "pl": (
        "**P/L — Preço/Lucro** — quantas vezes o preço cabe no lucro por ação (≈ anos para "
        "recuperar o investido, mantido o lucro). Menor costuma ser mais barato, mas compare "
        "dentro do setor."
    ),
    "pvp": (
        "**P/VP — Preço/Valor Patrimonial** — preço da ação ÷ valor patrimonial por ação. Abaixo "
        "de 1 = negociada abaixo do patrimônio contábil. Faz mais sentido em bancos e empresas de "
        "capital intensivo."
    ),
    "valor_mercado": (
        "**Valor de mercado** — preço da ação × número de ações; o 'tamanho' da empresa na bolsa."
    ),
    "nota_padronizada": (
        "**Nota (0–100)** — múltiplos (ML, ROE, P/L, EY) padronizados e combinados numa nota "
        "comparável entre as ações do lote. Só **ordena** candidatas — não é preço-alvo nem "
        "recomendação."
    ),
    "preco_alvo": (
        "**Preço-alvo** — preço 'justo' estimado por **regressão** (P/L explicado por payout e ROE "
        "do grupo). Depende da qualidade da amostra (de preferência mesmo setor); confira o R² e o "
        "nº de empresas."
    ),
    "upside": (
        "**Upside** — quanto o preço-alvo está acima (%) do preço atual. Positivo = candidata a "
        "estar barata (subavaliada) pela regressão; negativo = cara. É estimativa, não garantia."
    ),
    "veredito": (
        "**Veredito** — leitura da regressão de preço-alvo: *Subavaliada* (alvo acima do preço) ou "
        "*Cara*; 'indisponível' quando faltou ROE/payout. É estudo, nunca ordem de compra/venda."
    ),
    "lucro_liq": (
        "**Lucro líquido** — resultado final da empresa no ano (R$ milhões), das demonstrações da "
        "CVM. Base dos dividendos e do ROE."
    ),
    "patrim_liq": (
        "**Patrimônio líquido** — capital próprio da empresa (ativos − passivos), em R$ milhões. "
        "É o denominador do ROE."
    ),
    "fco": (
        "**FCO — Fluxo de Caixa Operacional** — caixa gerado pela operação no ano (R$ milhões). "
        "Ajuda a checar se o lucro 'virou dinheiro' e se os dividendos são sustentáveis."
    ),
    "payout_col": (
        "**Payout** — fatia do lucro do ano distribuída como proventos (%). Acima de 100% = "
        "distribuir mais do que lucrou (alerta de sustentabilidade)."
    ),
    "valor_intrinseco_col": (
        "**Valor intrínseco** — valor 'justo' por ação estimado pelo DDM em cada cenário (otimista "
        "g constante / conservador modelo H). Acima do preço = ação barata."
    ),
    "vp_dividendos": (
        "**VP dividendos** — parte do valor intrínseco vinda dos proventos do período projetado, "
        "trazidos a valor presente."
    ),
    "vp_residual": (
        "**VP residual** — parte do valor intrínseco vinda da perpetuidade (após a fase de alto "
        "crescimento), trazida a valor presente."
    ),
    "comparar_metricas": (
        "**O que a tabela mostra** (uma coluna por ticker): **Selo** (qualidade × preço), "
        "**P/L** (preço/lucro), **P/VP** (preço/valor patrimonial), **ROE** (retorno sobre o "
        "patrimônio), **DY** (dividend yield) e **Valor de mercado**. Triagem lado a lado, de "
        "preferência do mesmo setor — não é ranking nem recomendação."
    ),
}


def h(chave: str) -> str | None:
    """Retorna o texto de ajuda para a chave, ou None se não existir."""
    return G.get(chave)
