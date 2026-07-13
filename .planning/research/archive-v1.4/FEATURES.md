# Feature Research

**Domain:** Página de *setups* de swing trade (análise técnica, método John Murphy) dentro de app educacional — exibe sinais, NUNCA recomenda
**Researched:** 2026-06-29
**Confidence:** HIGH (convenções de AT são bem estabelecidas e o livro de Murphy é a autoridade do método; limites de dados intraday verificados na fonte)

> **Princípio inegociável que atravessa TODO o arquivo:** a página **EXIBE** níveis, sinais e
> contexto. Ela **NUNCA** emite ordem ("compre/venda"), nem texto imperativo. "Zona de entrada",
> "stop técnico" e "alvo" são **níveis geométricos derivados do gráfico**, apresentados como
> *referências de estudo*, não como instruções. Essa fronteira é o que separa o produto de um
> terminal de trade — e está cravada nas decisões do PROJECT.md (linhas 161-162).

---

## Como funcionam, na prática, as features pedidas (definições concretas e testáveis)

Esta seção responde às perguntas centrais do milestone com definições suficientemente precisas
para virar requisito testável. Tudo abaixo reusa ou estende `core/indicators.py`.

### 1. Contexto de tendência (Dow + MMs) + alinhamento multi-timeframe

**O que um "bom" produto faz — top-down de Murphy (semanal → diário):**
A análise técnica de Murphy é **top-down**: o timeframe maior define a *direção permitida*; o
timeframe de operação define o *gatilho*. Convenção clássica swing:

- **Tendência primária (semanal)** = direção do contexto. Derivada de: posição vs. MM200/MM30
  semanal + sequência de Dow (topos e fundos ascendentes/descendentes) + inclinação da
  regressão. Já existe quase tudo: `Tendencia.posicao_mm200`, `cruzamento`, `Forca.regressao_slope_ann`.
- **Tendência intermediária/gatilho (diário)** = onde o setup é montado. Mesmo conjunto de sinais
  no frame diário.
- **Regra de alinhamento (o "alinhamento de timeframes" do requisito):**
  - `alinhado_alta` = semanal em alta **E** diário em alta → setups de continuação a favor.
  - `alinhado_baixa` = ambos em baixa.
  - `conflito` = direções divergentes → o setup é marcado como **contra-tendência / menor
    qualidade** (penaliza o score, não bloqueia — exibe e avisa).

**Dow operacionalizado (sem subjetividade):** "topo/fundo ascendente" = detectar **pivots**
(swing highs/lows) e comparar os dois últimos de cada tipo. Sequência de topos e fundos mais
altos = uptrend; mais baixos = downtrend; misto = lateral/indefinida. Isso **exige detecção de
pivots, que NÃO existe hoje** (ver dependências).

**Dependência indicators.py:** ALTA reutilização (MMs, cruzamento, ADX, regressão prontos);
NOVO: orquestração multi-timeframe (rodar `calcular()` em frame diário E semanal e cruzar
rótulos — o `report.py` já mostra o padrão de resample W-FRI nas linhas 246-255) + detecção de
pivots para a regra de Dow. Complexidade: **MÉDIA**.

### 2. Suporte/Resistência (S/R) — derivação e exibição convencional

Três métodos convencionais, do mais simples ao mais robusto. Recomendo combinar (1)+(2):

1. **Extremos de canal (grátis, já existe):** `donchian_sup`/`donchian_inf` (20 e 55) são
   literalmente a máxima/mínima das N barras passadas = resistência/suporte de rompimento de
   Donchian. Reuso direto, custo ~zero.
2. **Pivots por fractais (swing highs/lows):** um topo é uma barra cujo High é maior que os `k`
   Highs de cada lado (idem fundo com Low). Convenção: `k=2` ou `k=3`. Cada pivot vira um nível.
3. **Clustering de pivots em zonas:** agrupar pivots próximos (ex.: dentro de ~1 ATR ou ~1-2% do
   preço) numa **zona** (faixa, não linha) — é assim que S/R aparece "de verdade", como banda.
   Quanto mais toques, mais "forte" a zona (input para o score).

**Exibição (Plotly overlay):** linhas/faixas horizontais (`add_hrect`/`add_hline`) rotuladas
"Suporte ~R$ X" / "Resistência ~R$ Y". Sempre **faixa**, nunca ponto exato (S/R é zona, ensina
Murphy). Murphy: papel de suporte/resistência **se inverte** após rompimento (resistência rompida
vira suporte) — diferencial bom de exibir.

**Dependência indicators.py:** Donchian reusável; NOVO: detector de pivots + clustering.
Complexidade: **MÉDIA**.

### 3. Stop "técnico" — o que o qualifica

Um stop é "técnico" quando está ancorado em **estrutura de mercado**, não num % arbitrário. Três
definições convencionais, todas válidas e testáveis (oferecer as três, deixar o usuário ver):

- **Swing-low/high stop (Dow puro):** logo **abaixo do último fundo de pivot** (compra) ou acima
  do último topo (venda). É o mais fiel a Murphy: o stop quebra quando a estrutura de tendência
  quebra. Requer pivots.
- **ATR-based (volatilidade):** `stop = entrada − m·ATR(14)`, `m` tipicamente 1.5–3 (2 é o
  default mais citado). Robusto a ruído; **ATR NÃO existe hoje como série exposta** — o TR já é
  calculado *dentro* de `adx_wilder` (linhas 277-285) mas não é retornado. Extrair ATR é barato.
- **Abaixo do suporte / da banda:** logo abaixo da zona de S/R relevante ou da MM/Donchian inferior.

**Regra prática boa:** stop final = o **mais conservador coerente** entre swing-low e
ATR-stop (ou exibir ambos). Testável: dado entrada+série, o stop está abaixo do último pivot-low
E a no máximo `m·ATR` da entrada.

**Dependência indicators.py:** NOVO ATR (trivial, TR já existe internamente) + pivots.
Complexidade: **BAIXA-MÉDIA**.

### 4. Risco:Retorno (R:R) — cálculo

Aritmética simples e universal, totalmente testável:

```
risco   = |entrada − stop|
retorno = |alvo − entrada|
R:R     = retorno / risco        (ex.: 2.5  → exibir "1 : 2,5")
```

Convenção de mercado: R:R ≥ **2** é o piso de um setup "de qualidade"; < 1 é desfavorável.
A página **exibe** o número e uma leitura qualitativa ("retorno potencial 2,5× o risco"), **sem**
dizer "opere". Edge cases testáveis: stop == entrada → risco 0 → R:R indefinido (mostrar
"indisponível", nunca infinito — mesmo padrão de degradação `np.errstate` já usado em indicators.py).

**Dependência indicators.py:** nenhuma direta (consome entrada/stop/alvo). Complexidade: **BAIXA**.

### 5. Alvo / projeção — padrão gráfico ou Fibonacci

Duas fontes de alvo convencionais:

- **Projeção por padrão (measured move):** cada padrão tem alvo geométrico próprio —
  - OCO: altura cabeça→linha de pescoço, projetada do rompimento.
  - Topo/fundo duplo: altura do padrão projetada do rompimento.
  - Triângulo/bandeira: altura da base do padrão / "mastro" projetado.
  Exige **detecção de padrões** (a parte mais difícil; ver §6).
- **Fibonacci (sem precisar de padrão):**
  - **Retração** (correção dentro de tendência): níveis 23,6 / 38,2 / **50** / **61,8** / 78,6%
    entre um swing-low e swing-high recentes → candidatos a **zona de entrada** (pullback) e a S/R.
  - **Extensão/projeção** (alvo além do último topo): 127,2 / **161,8** / 261,8% → candidatos a **alvo**.
  Convenção: 61,8% e 161,8% são os mais usados. Tudo depende de **ancorar em dois pivots**
  (swing low + swing high) — de novo, pivots.

**Exibição:** linhas horizontais Fibonacci rotuladas com % e preço; alvo destacado. Plotly nativo.

**Dependência indicators.py:** nenhuma direta; depende do detector de pivots novo.
Complexidade: Fibonacci **BAIXA-MÉDIA** (dado pivots); projeção por padrão **ALTA** (atrelada à detecção).

### 6. Detecção de padrões gráficos (OCO, topos/fundos duplos, triângulos, bandeiras)

É a feature **mais cara e mais frágil** do milestone. Não existe nada disso hoje. Abordagens:

- **Baseada em pivots + regras geométricas** (recomendada, custo-zero, determinística):
  topo duplo = dois pivots-topo de altura similar (~tolerância %) com um fundo entre eles, rompido
  para baixo na linha do fundo. OCO = pivot central (cabeça) mais alto que dois ombros similares
  + linha de pescoço. Triângulo = trendlines convergentes sobre pivots. Bandeira = forte impulso
  ("mastro") + consolidação curta em canal contrário.
- **ML / template matching:** fora de escopo (custo, opacidade, e contradiz "educacional/explicável").

**Risco de falsos positivos é ALTO** — padrões são notoriamente subjetivos. Mitigação de produto:
exigir **confirmação por rompimento + volume** antes de marcar o padrão como "disparado"
(ver checklist), e rotular padrões "em formação" vs "confirmados". Honestidade > cobertura:
melhor detectar bem 2-3 padrões (duplo topo/fundo, OCO) do que mal os cinco.

**Dependência indicators.py:** pivots (novo) + Donchian/volume para confirmar rompimento.
Complexidade: **ALTA** (candidata a fatiar em fase própria, possivelmente MVP só com duplo topo/fundo).

### 7. Score de qualidade do setup — como se constrói (ponderação)

Não existe um "score canônico" único na literatura — é uma **soma ponderada de confirmações**,
e o padrão de mercado é um **checklist com pesos**. Proposta concreta, testável e explicável
(cada ponto rastreável a um sinal já existente), alinhada à hierarquia de Murphy (tendência manda):

| Componente | Peso sugerido | Fonte (indicators.py) | Liga quando |
|---|---|---|---|
| Alinhamento de tendência (multi-TF + Dow) | **30%** | `posicao_mm200`, regressão, pivots | semanal+diário alinhados |
| Força da tendência (ADX) | 15% | `forca.forca_adx` (>25 forte) | ADX forte e DI a favor |
| Momentum (RSI + MACD) | 15% | `nivel_rsi`, `cruzamento_macd` | MACD a favor, RSI não esticado |
| Gatilho de rompimento | 15% | `rompimento_donchian` / nível S/R | rompeu resistência/suporte |
| Confirmação por volume | 15% | **NOVO** (volume não usado hoje) | volume no rompimento > média |
| Padrão gráfico presente | 10% | **NOVO** (detector de padrões) | padrão confirmado a favor |

Score 0–100 = soma dos pesos ligados; mapear para **grade qualitativa** (ex.: A/B/C ou
"Forte/Moderado/Fraco"). **R:R entra como gate/modulador, não como soma:** R:R < 1 rebaixa a
grade independentemente do score (um setup "bonito" com retorno menor que o risco não é "bom").

**Princípios de design do score (testáveis):**
- **Tendência domina** (peso maior) — fiel a Murphy e ao princípio do projeto (técnica é timing,
  não tese). Setup contra a tendência semanal nunca atinge a grade máxima.
- **Determinístico e explicável:** mostrar a decomposição ("trend 30/30, volume 0/15…"), nunca
  um número-caixa-preta. Isso reforça o caráter educacional.
- **Pesos vêm do config.yaml** (como todos os params de indicadores hoje, linhas 97-114) → ajustáveis sem deploy.

**Dependência indicators.py:** ALTA reutilização para 75% do peso; volume e padrão são novos.
Complexidade: **MÉDIA** (a soma é trivial; o custo está nos componentes novos que ela consome).

### 8. Volume — confirmação (Murphy: "volume precede preço")

Hoje o `Volume` existe no OHLC (`prices.py`) mas **nenhum indicador o usa**. Mínimo viável:
média móvel de volume + flag "volume do rompimento acima da média" (confirma) / "rompimento sem
volume" (suspeito). Diferenciais: OBV, volume relativo. Murphy trata volume como confirmação
secundária — peso menor no score, coerente com a tabela acima.

**Dependência indicators.py:** NOVO (família "Volume" no contrato `SinaisTecnicos`, aditiva como
foram `donchian_55`/`close`). Complexidade: **BAIXA**.

### 9. Timeframe diário + intraday (1h/30m/5m) — best-effort

**Verificado na fonte (yfinance/Yahoo):** intervalos <1d só retornam histórico recente —
**1m ≈ 7 dias**, demais intraday (2m/5m/15m/30m/60m/1h) ≈ **60 dias**; diário/semanal sem limite.
Bate com o PROJECT.md (linha 59). Implicações concretas:
- Intraday tem **poucas barras** → MM200/squeeze126/regressão90 ficam "indisponivel" (a
  degradação graciosa de indicators.py já cobre isso — vira `indisponivel` sem exceção). Convém
  **parâmetros mais curtos** por timeframe (ex.: MM curtas) OU exibir só os indicadores viáveis.
- Atraso ~15min e sem streaming (custo-zero) → **aviso explícito** de "dados atrasados" + botão
  **Atualizar** (cache TTL curto). `prices.py` hoje só busca `period="5y"` diário → NOVO: fetch
  parametrizado por `interval`/`period`.

**Dependência indicators.py:** o `calcular()` já é agnóstico de timeframe (docstring linha 413);
recebe o frame que der. NOVO só no ingest (intraday) + ajuste de params por TF. Complexidade: **MÉDIA**.

### 10. Gráfico interativo "do momento" + botão Atualizar

Candlestick Plotly (o app já usa Plotly no gráfico da aba Analisar, v1.1) com overlays
liga/desliga: MMs, Donchian/Bollinger, S/R, Fibonacci, padrões anotados, subpainéis RSI/MACD/ADX
(o `grafico.py` já monta subpainéis exatamente assim, linhas 151-174). Botão **Atualizar** =
limpar cache + refetch. Reuso ALTO de `grafico.py`. Complexidade: **MÉDIA**.

---

## Feature Landscape

### Table Stakes (o usuário espera — faltar = produto incompleto)

| Feature | Por que esperado | Complexidade | Notas / dependência indicators.py |
|---|---|---|---|
| Contexto de tendência (Dow + MMs, diário) | É o "para onde aponta" — base de qualquer setup | BAIXA | Reuso direto: `posicao_mm200`, `cruzamento`, `forca_adx` |
| Níveis de S/R exibidos no gráfico | Sem S/R não há "níveis de preço" | MÉDIA | Donchian reusável; NOVO pivots+clustering |
| Zona de entrada, stop técnico e alvo (como níveis) | É o coração do "setup"; pedido explícito | MÉDIA | NOVO ATR+pivots; R:R consome esses 3 |
| Relação Risco:Retorno | Métrica universal de qualidade de setup | BAIXA | Aritmética pura, sem dep. |
| Checklist de sinais disparados (liga/desliga) | Transparência: mostra POR QUE o setup existe | BAIXA-MÉDIA | Lê rótulos discretos já prontos + volume novo |
| Score/grade de qualidade do setup | Pedido explícito; sintetiza o checklist | MÉDIA | Soma ponderada sobre componentes (75% já existem) |
| Gráfico interativo com overlays + botão Atualizar | Pedido explícito; é a "tela do momento" | MÉDIA | Reuso ALTO de `grafico.py` (Plotly + subpainéis) |
| Timeframe diário (default) selecionável | Swing clássico opera no diário | BAIXA | `calcular()` já agnóstico de TF |
| Aviso de "dados atrasados ~15min" + limite de histórico | Honestidade (custo-zero, sem streaming) | BAIXA | Texto + TTL de cache |
| RSI/MACD/ADX no painel | Osciladores básicos de Murphy; já existem | NENHUMA (reuso) | 100% `indicators.py` |
| Disclaimer "exibe, não recomenda" visível | Posicionamento legal/educacional do projeto | BAIXA | Mesmo padrão do disclaimer v1.3 |

### Differentiators (vantagem competitiva — alinhados ao Core Value: fidelidade ao método + explicabilidade)

| Feature | Proposta de valor | Complexidade | Notas / dependência |
|---|---|---|---|
| Alinhamento multi-timeframe (semanal→diário) explícito | Top-down de Murphy de verdade; raro em apps grátis BR | MÉDIA | Roda `calcular()` em 2 frames + cruza (padrão resample já em report.py) |
| Score **explicável** (decomposição visível, não caixa-preta) | Reforça o caráter educacional; diferencia de "robôs de sinal" | BAIXA-MÉDIA | Mostrar peso a peso |
| Stop técnico em 3 sabores (swing-low / ATR / S/R) lado a lado | Ensina o conceito em vez de cuspir um número | BAIXA-MÉDIA | NOVO ATR+pivots |
| Fibonacci (retração p/ entrada, extensão p/ alvo) ancorado em pivots | Ferramenta clássica de Murphy, bem exibida | BAIXA-MÉDIA | Depende de pivots |
| Detecção de padrões com rótulo "em formação" vs "confirmado" + alvo medido | Mão na roda visual; honesto sobre incerteza | ALTA | NOVO; candidato a MVP reduzido |
| Inversão de papel S/R (resistência rompida vira suporte) anotada | Detalhe "de quem entende Murphy" | BAIXA | Sobre o detector de S/R |
| Ponte com o fundamentalista: "este ticker no Garimpo está caro/barato?" | Une os dois produtos do app sem misturar veredito | BAIXA | Link/leitura read-only do módulo existente |

### Anti-Features (parecem boas, viram terminal de day-trade ou implicam recomendação — EVITAR)

| Feature | Por que é pedida | Por que é problemática | Alternativa |
|---|---|---|---|
| Botão/sinal "COMPRAR" ou "VENDER" | Parece o "resultado" óbvio | **Vira recomendação** — quebra o posicionamento educacional e cria risco legal | Exibir níveis e checklist; o usuário decide |
| Streaming em tempo real / cotação ao vivo | "Quero o preço agora" | Feed B3 real-time é **pago** → quebra custo-zero; vira day-trade terminal | Intraday best-effort + aviso de atraso + Atualizar manual |
| Alertas/push de gatilho ("avise quando romper") | Conveniência | Exige backend/scheduler (não há backend) + empurra p/ operar = recomendação implícita | Usuário aperta Atualizar; checklist mostra o estado atual |
| Scanner de universo ("quais ações têm setup hoje") | Poderoso | **Fora de escopo explícito** (v1.4 = 1 ticker); custo de fetch e vira ferramenta de sinal | Um ticker por vez; scanner fica p/ outro marco |
| Backtest / "win rate do setup" | "Será que funciona?" | Sugere **promessa de retorno** (recomendação) + custo alto + induz overfitting | Nada de estatística de performance; só o estado técnico atual |
| Position sizing / "quanto investir" / alavancagem | Continuação natural do R:R | É **aconselhamento financeiro** explícito | Mostrar só R:R como razão; nunca R$ a alocar |
| Scalping 1m / book de ofertas / DOM | "Intraday completo" | Empurra para day-trade puro; dados 1m só 7 dias e atrasados | 5m/30m/1h best-effort; diário é o foco |
| Auto-refresh em segundos | "Tempo real grátis" | Martela o Yahoo (rate-limit, já tratado em prices.py) e simula streaming | Refresh **manual** + cache TTL |
| Otimização automática de parâmetros do setup | "Achar o melhor setup" | Caixa-preta, overfitting, contradiz explicabilidade | Params fixos e visíveis no config.yaml |

---

## Feature Dependencies

```
Detector de PIVOTS (swing highs/lows)  ← peça central NOVA
    ├──requires──> (nada além do OHLC)
    ├──enables──> S/R por pivots + clustering em zonas
    ├──enables──> Stop swing-low/high (Dow)
    ├──enables──> Fibonacci (ancora em 2 pivots)
    ├──enables──> Sequência de Dow (topos/fundos asc./desc.) → contexto de tendência
    └──enables──> Detecção de padrões gráficos → alvo measured-move

ATR (NOVO; TR já existe dentro de adx_wilder)
    └──enables──> Stop ATR-based  ──feeds──> Risco:Retorno

Família VOLUME (NOVO no contrato SinaisTecnicos)
    └──enables──> Confirmação de rompimento ──feeds──> Score + Checklist

Ingest INTRADAY (NOVO em prices.py)
    └──enables──> Seletor de timeframe 1h/30m/5m

Entrada + Stop + Alvo  ──compute──> Risco:Retorno  ──gate──> Grade do Score

calcular() [indicators.py, JÁ EXISTE, agnóstico de TF]
    └──reused-by──> Contexto tendência, momentum, ADX, Donchian, Bollinger
                        └──feeds──> Score (≈75% do peso) + Checklist + Gráfico

Score ──synthesizes──> Checklist + Tendência + Volume + Padrão + (R:R como gate)
Gráfico "do momento" ──overlays──> S/R, Fibonacci, Padrões, indicadores (reuso grafico.py)
```

### Dependency Notes

- **PIVOTS é o gargalo de habilitação:** S/R robusto, stop swing-low, Fibonacci, Dow e padrões
  TODOS dependem dele. Construir pivots **primeiro**; sem ele, metade do milestone não existe.
- **ATR é barato e desbloqueia stop+R:R:** o TR já é computado dentro de `adx_wilder`
  (indicators.py:277-285) mas não exposto — extrair uma série ATR é trivial e de alto valor.
- **Volume é a única família totalmente ausente** e entra como confirmação (peso menor). Adicioná-la
  ao dataclass `SinaisTecnicos` segue o padrão aditivo já usado (`donchian_55`, `close` com default None).
- **Multi-timeframe reusa o resample W-FRI** já presente em `report.py:246-255`.
- **Padrões gráficos CONFLITAM com prazo/qualidade** se feitos por completo: alto custo + falsos
  positivos. Recomendo fatiar e talvez entregar MVP só com duplo topo/fundo + OCO.
- **Score depende de QUASE tudo** — é a última peça a montar (consome checklist+volume+padrão+R:R).

---

## MVP Definition

### Launch With (v1.4 núcleo — a "página de setup" mínima que já entrega valor)

- [ ] Página/menu nova e isolada (não toca aba Analisar nem veredito fundamentalista) — fronteira do projeto
- [ ] Fetch diário + reuso de `indicators.calcular()` → contexto de tendência (Dow simples + MMs) — base
- [ ] **Detector de pivots** (swing highs/lows) — desbloqueia metade do milestone
- [ ] S/R por pivots+Donchian, exibido como faixas no gráfico — "níveis de preço"
- [ ] **ATR** + stop técnico (swing-low e ATR) + zona de entrada + alvo (Fibonacci) como níveis
- [ ] Risco:Retorno calculado de entrada/stop/alvo (com degradação p/ "indisponível")
- [ ] Checklist de sinais liga/desliga (rompimento, cruzamento MM, RSI/MACD, volume)
- [ ] Família **Volume** + confirmação de rompimento
- [ ] Score ponderado **explicável** (decomposição visível) + grade, com R:R como gate
- [ ] Gráfico candlestick interativo com overlays + botão **Atualizar** (reuso grafico.py)
- [ ] Disclaimer "exibe sinais, não recomenda" + aviso de dados atrasados
- [ ] Alinhamento multi-timeframe semanal→diário (rótulo alinhado/conflito → modula o score)

### Add After Validation (dentro ou logo após v1.4)

- [ ] Timeframe intraday 1h/30m/5m best-effort (params curtos por TF) — gatilho: diário estável
- [ ] Detecção de **padrões gráficos** completa (triângulos, bandeiras) com alvo measured-move —
      gatilho: duplo topo/fundo+OCO validados sem excesso de falso positivo
- [ ] Inversão de papel S/R anotada; Fibonacci de extensão como alvo alternativo
- [ ] Ponte read-only com o veredito fundamentalista do ticker

### Future Consideration (provavelmente outro marco)

- [ ] Scanner de universo (explicitamente fora do v1.4)
- [ ] OBV / volume relativo avançado
- [ ] Trendlines automáticas (Dow) desenhadas sobre pivots

---

## Feature Prioritization Matrix

| Feature | Valor p/ usuário | Custo de implementação | Prioridade |
|---|---|---|---|
| Detector de pivots | ALTO (habilita tudo) | MÉDIO | **P1** |
| Contexto de tendência (reuso) | ALTO | BAIXO | **P1** |
| ATR + stop técnico + R:R | ALTO | BAIXO-MÉDIO | **P1** |
| S/R no gráfico | ALTO | MÉDIO | **P1** |
| Checklist de sinais | ALTO | BAIXO | **P1** |
| Família volume + confirmação | MÉDIO-ALTO | BAIXO | **P1** |
| Score explicável + grade | ALTO | MÉDIO | **P1** |
| Gráfico + Atualizar (reuso) | ALTO | MÉDIO | **P1** |
| Fibonacci (retração/extensão) | MÉDIO-ALTO | BAIXO-MÉDIO | **P1/P2** |
| Multi-timeframe semanal→diário | ALTO (diferencial) | MÉDIO | **P2** |
| Intraday 1h/30m/5m | MÉDIO | MÉDIO | **P2** |
| Padrões gráficos (duplo topo/fundo, OCO) | MÉDIO-ALTO | ALTO | **P2** |
| Padrões avançados (triângulo/bandeira) | MÉDIO | ALTO | **P3** |
| Ponte com fundamentalista | MÉDIO | BAIXO | **P3** |

**Chave:** P1 = núcleo do v1.4 · P2 = enriquecimento do mesmo marco · P3 = diferir.

---

## Competitor Feature Analysis (apps/terminais BR e globais que o usuário conhece)

| Feature | TradingView (free) | Status Invest / brokers BR | Nossa abordagem |
|---|---|---|---|
| Indicadores (RSI/MACD/MM/ADX) | Completo, ao vivo | Básico | Reuso `indicators.py` (Wilder, bate TradingView) |
| S/R automático | Manual/indicador pago | Raro | Pivots+Donchian automáticos, como faixas |
| Padrões gráficos | Detector pago | Não | Determinístico, explicável, escopo reduzido honesto |
| Score de setup | Não (ou "rating" caixa-preta) | "Rating" caixa-preta | **Explicável**, decomposto, fiel a Murphy |
| Sinal compra/venda | Evita (ou rating) | Alguns dão "recomendação" | **NUNCA** — exibe níveis e checklist |
| Tempo real | Sim (pago p/ B3) | Atrasado | Best-effort + aviso de atraso (custo-zero) |
| R:R / risco | Ferramenta manual | Não | Calculado e exibido como razão (sem position sizing) |

**Posicionamento:** não competimos em "tempo real" nem em cobertura de padrões — competimos em
**explicabilidade e fidelidade ao método de Murphy**, coerente com o Core Value do projeto
("fiel ao método do livro e consistente"), e na fronteira ética "exibe, não recomenda".

---

## Notas de dependência consolidadas sobre `core/indicators.py`

**Reuso direto (sem tocar):** SMA/EMA 20/50/200, `posicao_mm200`, golden/death cross, Donchian
20/55, Bollinger+squeeze, ADX/+DI/−DI, regressão slope/r2, RSI(14) Wilder, MACD 12/26/9, e a
`close` split-adjusted exposta. `calcular()` é **agnóstico de timeframe** → serve diário, semanal
e intraday sem mudança. A degradação graciosa para `"indisponivel"` (histórico curto) já protege
o caso intraday. Params todos no `config.yaml` (bloco `indicadores:`, linhas 97-114).

**Extensões NOVAS necessárias (em ordem de habilitação):**
1. **Pivots** (swing highs/lows) — gargalo; habilita S/R, stop swing, Fibonacci, Dow, padrões.
2. **ATR** — TR já existe interno ao `adx_wilder`; só expor a série. Habilita stop ATR + R:R.
3. **Família Volume** — aditiva no dataclass (padrão `default None` já usado). Confirmação.
4. **S/R por clustering**, **Fibonacci**, **detector de padrões**, **score** — módulos novos que
   *consomem* indicators.py, não o alteram (preserva os 191 testes golden — restrição do projeto).
5. **Ingest intraday** — novo fetch parametrizado em `prices.py` (hoje só `period="5y"` diário).

**Não recalcular na UI:** seguir a decisão `app.py` read-only (PROJECT.md:152) — a página de
setup lê valores/níveis de uma camada de engine nova (`core/setup.py` ou similar), não recalcula
método na view. Espelhar o padrão CLI/UI compartilhando engine.

---

## Sources

- **John Murphy — *Análise Técnica dos Mercados Financeiros*** (livro de referência do método;
  convenções de Dow, S/R como zona e inversão de papel, padrões de reversão/continuação e seus
  alvos medidos, volume como confirmação, top-down multi-timeframe). Autoridade do método. HIGH.
- **Código existente:** `src/analista/core/indicators.py` (contrato `SinaisTecnicos`, Wilder
  RSI/ADX, Donchian causal, regressão), `src/analista/report/report.py:237-288` (resample W-FRI +
  árvore de decisão de timing), `src/analista/grafico.py` (Plotly + subpainéis), `src/analista/
  ingest/prices.py` (fetch 5y diário, split-adjust), `config.yaml:97-114` (params de indicadores).
  Verificado por leitura direta. HIGH.
- **Convenções de R:R, stop ATR (1.5–3×), Fibonacci (38,2/50/61,8 retração; 161,8 extensão),
  checklist ponderado de confirmação** — práticas padrão e consensuais de análise técnica. HIGH.
- **Limites de dados intraday yfinance/Yahoo** (1m≈7d; demais intraday≈60d; diário sem limite) —
  verificado em fontes da comunidade yfinance (AlgoTrading101, docs/issues do projeto). Bate com
  PROJECT.md:59. HIGH.

---
*Feature research for: página de setups de swing trade (método Murphy) — milestone v1.4*
*Researched: 2026-06-29*
