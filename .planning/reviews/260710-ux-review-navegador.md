---
type: review
review_id: 260710-ux
scope: UX/UI walkthrough no navegador (app ao vivo — app.lazaricapital.com.br)
reviewer: Claude (sessão de usuário simulado)
date: 2026-07-10
milestone_alvo: v2.1 (polish de UX pós-comercialização)
status: captured
---

# Review de UX/UI — walkthrough no navegador (2026-07-10)

Percorri o app ao vivo (`app.lazaricapital.com.br`) como um investidor PF percorreria:
Início → Analisar uma ação → Garimpar carteira (BSD) → Ranking por múltiplos → Comparar ações →
Swing trade, testando botões, tooltips, tratamento de erro (ticker inválido), o link de
Metodologia e casos de borda (watchlist cheia).

## Veredito geral

Produto **muito polido para Streamlit** e com **honestidade intelectual rara** (guardrails que
avisam quando a própria análise é frágil: amostra pequena, R² baixo, coeficiente contraintuitivo;
disclaimers CVM onipresentes; página de Metodologia citando capítulo por capítulo do livro-base).
Os problemas abaixo são de **acabamento**, não de fundação.

## Prioridade (Top 5 → viram quick tasks)

| # | Prioridade | Achado | Quick task |
|---|-----------|--------|-----------|
| 1 | 🔴 Alta | Análise demora ~35s sem feedback no corpo da página | `260710-u1f` |
| 2 | 🔴 Alta | Flash de tabela colapsada ao trocar de aba (Valuation/Fundamentos) | `260710-u2r` |
| 3 | 🟠 Média | Clareza: glossário de siglas (tabelas transpostas) + legenda de selos e triângulos | `260710-u3g` |
| 4 | 🟠 Média | Formatação numérica BR inconsistente (`.` vs `,`, `-0.0%`, `+ -11.17`) | `260710-u4n` |
| 5 | 🟡 Baixa | Cópia inconsistente: "3 ferramentas" / "4 menus" / 5 itens reais | `260710-u5c` |

Os demais achados (6–18) ficam registrados abaixo como backlog do v2.1.

---

## Achados detalhados

### 🔴 Bugs / quebras

**1. Análise sem feedback de carregamento (~35s).** Em "Analisar uma ação", após clicar em
Analisar a tela fica idêntica por ~35s; o único sinal é o ícone minúsculo do Streamlit no canto
superior direito. Risco de abandono / clique duplo. → precisa de `st.spinner`/status no corpo.
Vale para Garimpar e Ranking também (buscam vários tickers).

**2. Flash de tabela colapsada ao trocar de aba.** Nas abas *Valuation (DDM)* e *Fundamentos
(10 anos)* da análise a fundo, ao clicar a tabela renderiza por ~2s **só com a 1ª coluna** (as
colunas de valores colapsam para largura 0) e depois se ajusta. Bug clássico de `st.dataframe`
dentro de `st.tabs` inativo. Transitório, mas passa impressão de "quebrado".

**3. Artefato "0" solto** no rodapé da tabela de Fundamentos (10 anos) — parece label de eixo/
gráfico órfão renderizado abaixo da tabela.

**4. Notícias duplicadas** (Início). Cada card mostra o **mesmo título 2×** (uma como link em
negrito, outra como texto de resumo logo abaixo).

### 🟠 Clareza / termos

**5. Siglas sem definição individual.** A tabela **Múltiplos** (ML, EY, CDC, DY rec., P/L, ROE...)
e **Crescimento e custo de capital** (g histórico, g alto adotado, Ke CAPM...) são **tabelas
transpostas** (sigla no rótulo de LINHA) — o `help=` por coluna do `260704-kps` não cobre esse
caso (Streamlit não faz tooltip em rótulo de linha). `CDC = 1.50` é o mais opaco. Falta glossário
real por termo. Mesmo a página de Metodologia só *lista* as siglas, não as define.

**6. Selos coloridos (🟢🔵🟡) sem legenda** nas tabelas de Garimpar e Ranking. Em Comparar o selo
vem com texto ("Boa, no preço"/"Boa, mas cara"/"JOIA") — bom — mas nas outras duas é só a bolinha.

**7. Triângulos verde/vermelho no gráfico de preço (5A) sem legenda.** Só "Valor intrínseco (DDM)"
é rotulado; dezenas de triângulos de compra/venda poluem sem explicação.

**8. Inconsistência de contagem na cópia.** Tooltip de "O que você quer fazer?" diz **"Três
ferramentas"** (`src/analista/glossario.py:13`); a Início diz **"Os 4 menus ao lado"**
(`app.py:725`); mas a sidebar tem **5 itens** além da Início (Analisar, Garimpar, Ranking,
Comparar, Swing trade). Comparar e Swing trade foram adicionados sem atualizar os textos.

**9. "Garimpar carteira (BSD)" — "carteira" engana.** A tela cola uma lista de tickers para
triagem, não analisa a carteira que o usuário *possui*. "Carteira" sugere posições próprias.
Sugestão: "Garimpar uma lista" / "Triagem de ações".

**10. "watchlist" — MANTER.** Termo consagrado no público investidor BR, mais curto/reconhecível
que "lista de acompanhamento". "Minha watchlist" soa natural. Não é problema (registrado por ser
pergunta explícita do dono).

**11. "SELIC (CORTE DO DY)"** na sidebar é críptico — "corte do DY" só faz sentido a quem já conhece
o método. Tem tooltip, mas o rótulo poderia ser "piso de dividend yield (Selic)".

**12. "Swing trade (análise técnica)" destoa do produto.** App de dividendos/buy-and-hold com aba de
swing trade (alvo/entrada/stop) cria dissonância de posicionamento, apesar dos "(estudo)"/
disclaimers. Nome em inglês. Considerar "Análise técnica (timing)".

### 🟡 Formatação / detalhes

**13. Separador decimal inconsistente.** Banner mostra `R$ 40.31 dentro de R$ 31.32–52.63` (ponto,
US) enquanto os cards mostram `R$ 40,31` (vírgula, BR). **Causa-raiz:**
`src/analista/report/report.py:198–207` monta os vereditos (SUBAVALIADA/SOBREAVALIADA/NO INTERVALO/
VERIFICAR) com `{...:.2f}` cru; o helper BR existe (`_num()` em `app.py:281` e
`presentation.py:38`). Fix = usar `_num()`/formatação BR nesses vereditos. Percentuais também usam
ponto (`8.2%`) em vez de vírgula.

**14. `Upside -0.0%`** (zero negativo) na tabela de Ranking — deveria ser `0.0%`.

**15. Fórmula da regressão com sinal duplo:** `P/L = 24.51 + -11.17·payout + -35.46·ROE`. Trocar
`+ -` por `− `. (cf. `src/analista/cli.py:176`; conferir também o render em `app.py`.)

**16. Rótulos truncados:** cards da análise (`VALOR INTRÍNSEC…`, `DIVIDEND YIELD …`,
`KE (CUSTO CAPIT…)`) e a linha `Valor d` (deveria ser "Valor de mercado") na tabela de Comparar —
coluna de rótulos estreita demais.

**17. Labels alvo/entrada/stop sobrepostas** no canto direito do gráfico Plotly do Swing trade
(o "Modo Trading" resolve isso muito melhor — é o gráfico mais bem resolvido do app).

**18. Menu Streamlit (3 pontinhos) exposto** no topo direito — para produto pago, vale esconder
(`Rerun/Settings/Deploy/Made with Streamlit`) via `.streamlit/config.toml` (`toolbarMode="minimal"`)
para não vazar a stack.

## O que está ótimo (NÃO mexer)

- Guardrails educativos do Ranking (amostra pequena / ROE negativo / R² baixo → "confie no DDM").
- Validação da watchlist (máximo 5, mensagem clara) e do ticker inválido ("Sem candles… Confira o
  ticker").
- Orientação de fluxo entre telas ("Próximo passo: rode o Ranking…"; tooltip "garimpe → rankeie →
  analise").
- Página de Metodologia (fonte, capítulos, fontes de dados públicas).
- "Modo Trading" (gráfico estilo TradingView com Fibonacci) e o painel técnico multi-eixo
  (ADX/RSI/MACD em subpainéis separados).

## Não validado nesta sessão

- **Layout mobile/responsivo:** a ferramenta de resize redimensionou a janela do SO mas o viewport
  do Streamlit não refluiu no teste — responsivo mobile ficou por validar (item de v2.1).
