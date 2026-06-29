# Feature Research

**Domain:** Indicadores de tendência consultivos (timing de entrada + alerta de perda de tendência) sobre app fundamentalista de dividendos (B3), aba "Analisar"
**Researched:** 2026-06-24
**Confidence:** HIGH (parâmetros canônicos verificados em literatura/práticas correntes; interpretação consultiva derivada do método fundamentalista do livro)

> **Nota de enquadramento (não re-litigar):** todos os indicadores são **consultivos**. Eles
> respondem *QUANDO* entrar numa ação que o veredito fundamentalista (DDM/múltiplos) já considerou
> barata, e *SINALIZAM* uma possível perda de tendência que dispara **"reveja os fundamentos"** —
> nunca um veredito barato/caro, nunca uma ordem de compra/venda. Público: investidor buy-and-hold
> de dividendos, não day trader. Tudo vive na aba Analisar, sobreposto ao gráfico de preço de 5a
> existente, ligável/desligável.

---

## 0. Fundamentos por indicador (parâmetros canônicos → sinal legível)

Esta seção é a base técnica que alimenta as tabelas de features. Cada indicador é mapeado para um
**sinal discreto** (bullish / neutro / bearish, ou um rótulo de estado) que o investidor lê sem
saber a matemática.

### 0.1 Médias móveis — SMA/EMA 20/50/200 (HIGH)

**Parâmetros canônicos e por quê:**
- **20** ≈ um mês de pregão (curto prazo / ruído tático).
- **50** ≈ um trimestre (médio prazo; a "linha do swing").
- **200** ≈ ~10 meses de pregão; é a **referência de tendência de longo prazo** por excelência —
  para um investidor de dividendos é a MM mais importante. Preço acima da MM200 = ativo em
  tendência primária de alta; abaixo = tendência primária comprometida.
- SMA = média simples (peso igual); EMA = exponencial (reage mais rápido ao preço recente). Para
  longo prazo a diferença prática é pequena na MM200; oferecer SMA como padrão e EMA opcional.

**Sinais discretos:**
- **Preço × MM200** (o filtro primário): `acima da MM200` = tendência de alta de longo prazo;
  `abaixo da MM200` = tendência perdida (gatilho de reverificação).
- **Golden cross**: MM50 cruza **acima** da MM200 → bullish de longo prazo (início de tendência).
- **Death cross**: MM50 cruza **abaixo** da MM200 → bearish de longo prazo (perda de tendência).
- **Stack alinhado**: preço > MM20 > MM50 > MM200 = tendência de alta saudável e ordenada.

### 0.2 Canais — Donchian (20 / 55) e Bollinger (20, 2σ) (HIGH)

**Donchian — parâmetros canônicos (Turtle System, Dennis/Eckhardt):**
- **20** = máx/mín dos últimos 20 períodos (entrada de curto prazo; rompimento da máxima de 20 = compra).
- **55** = máx/mín dos últimos 55 períodos (entrada de longo prazo; sem filtro no sistema original).
- **10/20** = saída (rompimento da mínima de 10 [S1] ou 20 [S2]). Para nosso público, a **mínima de
  20** é o gatilho de perda de tendência de canal mais apropriado.

**Sinais discretos (Donchian):**
- `rompeu a máxima de 20/55` → bullish (preço fazendo nova máxima do período = força).
- `rompeu a mínima de 20` → bearish / perda do canal (gatilho de reverificação).
- `dentro do canal` → neutro.

**Bollinger — parâmetros canônicos:** média móvel de **20** ± **2σ** (desvio-padrão).

**Sinais discretos (Bollinger):**
- `tocando/rompendo a banda inferior` → preço esticado para baixo (possível sobre-venda; numa ação
  fundamentalmente barata, pode ser ponto de timing de entrada — consultivo).
- `tocando/rompendo a banda superior` → esticado para cima (NÃO é sinal de venda para nós; só contexto).
- `squeeze` (bandas estreitas) → baixa volatilidade, possível movimento à frente (diferenciador, opcional).

> **Aviso de interpretação para dividendos:** Bollinger é mean-reversion no curto prazo. Usar
> APENAS como contexto de "preço esticado", nunca como gatilho de compra/venda isolado. A banda
> inferior numa ação cara continua não sendo compra.

### 0.3 Força e direção — ADX (14) + inclinação de regressão linear (HIGH)

**ADX — parâmetros canônicos:** período **14**. Thresholds da literatura:
- `< 20` → **sem tendência** (mercado lateral/choppy).
- `20–25` → zona neutra/ambígua.
- `> 25` → **tendência forte** confirmada (zona de trend-following).
- `> 50` → tendência muito forte.

ADX mede **intensidade**, não direção. A direção vem do preço × MM200 (ou de +DI vs −DI, opcional).

**Inclinação de regressão linear:** ajusta uma reta aos últimos N fechamentos (janela típica
**50–90** pregões para um horizonte de médio/longo prazo; 63 ≈ um trimestre é uma escolha limpa).
O **sinal da inclinação** (slope) dá a direção; a magnitude normalizada (slope/preço) dá a força.

**Sinais discretos combinados:**
- `tendência de alta forte` = ADX > 25 **e** inclinação positiva.
- `tendência de baixa forte` = ADX > 25 **e** inclinação negativa (gatilho de reverificação).
- `sem tendência / lateral` = ADX < 20 (timing menos confiável; sugerir esperar definição).

### 0.4 Momentum — RSI (14) e MACD (12/26/9) (HIGH)

**RSI — parâmetros canônicos:** período **14**; **30** = sobre-vendido, **70** = sobre-comprado.

**Sinais discretos (RSI):**
- `RSI < 30` → sobre-vendido (numa ação barata, possível janela de timing de entrada).
- `RSI > 70` → sobre-comprado (contexto; não é venda para nós).
- `30–70` → neutro. Cruzar de baixo de 30 para cima = recuperação de momentum (timing fino).

**MACD — parâmetros canônicos:** EMA **12** − EMA **26** = linha MACD; sinal = EMA **9** do MACD; histograma = MACD − sinal.

**Sinais discretos (MACD):**
- `MACD cruzou acima da linha de sinal` → bullish (momentum virou para cima — timing de entrada).
- `MACD cruzou abaixo da linha de sinal` → bearish (momentum enfraquecendo).
- `MACD > 0` (acima da linha zero) = momentum de fundo positivo.

---

## Feature Landscape

### Table Stakes (o investidor espera que existam)

Sem isto, o conjunto de indicadores parece incompleto ou "de brinquedo" para quem conhece o método.

| Feature | Por que esperado | Complexidade | Notas de implementação |
|---------|------------------|--------------|------------------------|
| SMA/EMA 20/50/200 sobrepostas ao preço | MMs são o ABC da leitura de tendência; o livro pensa em longo prazo, a MM200 é a régua natural | LOW | `rolling(window).mean()` / `ewm(span)`; reusar a série Close nominal já no gráfico Plotly do v1.1 |
| **Posição preço × MM200** como filtro primário de tendência | É o sinal de longo prazo nº 1 para buy-and-hold; "acima da MM200 = tendência de alta" | LOW | Comparação do último Close com último valor da MM200; rótulo `acima/abaixo da MM200` |
| Golden cross / Death cross (MM50 × MM200) | Eventos clássicos e reconhecíveis de virada de tendência de longo prazo | LOW | Detectar mudança de sinal de (MM50 − MM200) entre dois pregões; marcar no gráfico |
| RSI(14) com faixas 30/70 | Oscilador de momentum mais conhecido; "sobre-vendido/sobre-comprado" é vocabulário básico | LOW | Cálculo padrão de RSI; rótulo discreto + linha em painel separado ou tooltip |
| MACD(12/26/9) com cruzamento de sinal | Padrão de timing de momentum amplamente usado; cruzamento up = gatilho de entrada | MEDIUM | Três EMAs + histograma; melhor em subpainel para não poluir o eixo de preço |
| Controles ligar/desligar e selecionar indicadores | Decisão JÁ travada; evita virar terminal de trade; cada investidor escolhe o que ver | LOW | `st.multiselect` / `st.checkbox` / `st.toggle`; estado por sessão; redesenha o Plotly |
| **Resumo de timing de entrada** (consultivo, em linguagem natural) | O investidor quer "é boa hora de entrar?" sem ler 6 indicadores; síntese é o valor central | MEDIUM | Composição determinística (ver §Composite); texto + selo bullish/neutro/bearish; SEMPRE com disclaimer de que não altera o veredito |
| **Alerta de reverificação** ao romper tendência | Decisão JÁ travada; perda da MM200 / death cross → "reveja os fundamentos" | MEDIUM | Disparo a partir dos sinais de §0; copy enfática de que é gatilho de revisão, não ordem de venda |
| Tooltips de glossário (ícone ?) em cada indicador | Padrão já existente no app; o público é PF que pode não saber o que é ADX/MACD | LOW | Reusar o mecanismo `help=` / glossário já implementado no v1.1 |
| Degradação graciosa quando faltam dados de preço | Padrão já existente (GRAF-03); indicador precisa de histórico mínimo (ex.: 200 pregões p/ MM200) | LOW | Se série < janela do indicador, esconder o indicador com aviso "histórico insuficiente" |

### Differentiators (vantagem competitiva)

O que diferencia do "qualquer site com gráfico + indicadores", alinhado ao Core Value (fidelidade ao método, longo prazo).

| Feature | Proposta de valor | Complexidade | Notas |
|---------|-------------------|--------------|-------|
| **Composite "timing de entrada" para dividendos** (não soma de osciladores) | Traduz 6 indicadores em UMA leitura voltada a buy-and-hold: "confirme uma tendência de alta antes de comprar uma ação barata" | MEDIUM | Pesa a MM200/ADX/inclinação (tendência de fundo) acima de RSI/MACD (timing fino); regras explícitas e auditáveis (golden test) |
| Donchian 20/55 + rompimentos rotulados | Canal de Turtle é raro em apps PF brasileiros; "nova máxima de 55" é sinal de força limpo | MEDIUM | `rolling(window).max()/.min()`; sombrear o canal no Plotly |
| ADX(14) + inclinação de regressão como "há tendência?" | Resolve o erro nº 1: aplicar sinal de tendência num mercado lateral. Diz SE vale confiar no timing | MEDIUM | ADX é o cálculo mais pesado (TR/+DM/−DM/suavização de Wilder); inclinação via `numpy.polyfit` |
| **Acoplamento explícito com o veredito DDM** no resumo | "Ação BARATA (DDM) + em tendência de alta (técnico) = bom timing"; matriz fundamento × técnico | MEDIUM | Lê o veredito barato/caro que a engine já produz; nunca recalcula; só cruza com o selo técnico |
| Bandas de Bollinger como contexto de "preço esticado" | Ajuda a evitar comprar no topo de um repique de curto prazo numa ação já barata | LOW | MM20 ± 2σ; rotular toque/rompimento; deixar claro que é contexto, não gatilho |
| Marcadores de eventos no gráfico (cross, rompimentos) | Torna os sinais visíveis no tempo, não só um selo no presente | MEDIUM | Annotations/scatter no Plotly nas datas dos eventos |
| Copy "reveja os fundamentos" com link de volta à análise | Fecha o loop fundamentalista: o técnico empurra o investidor de volta aos números do livro | LOW | Texto + âncora para a seção de fundamentos da própria aba Analisar |

### Anti-Features (parecem boas, criam problemas — proibidas para ESTE público)

| Feature | Por que é pedida | Por que é problemática | Alternativa |
|---------|------------------|------------------------|-------------|
| **Sinais intraday / timeframes de minutos/horas** | "Quero precisão no ponto de entrada" | App é fundamentalista de longo prazo; dados gratuitos são diários; vira day trade — contradiz o projeto | Manter timeframe diário; timing é "esta semana/mês", não "este candle" |
| **Recomendação automática de compra/venda** ("COMPRE AGORA") | Parece o ápice da conveniência | Viola a regra travada: técnico é consultivo, jamais ordem; cria responsabilidade/risco e desautoriza o veredito fundamentalista | Selo consultivo bullish/neutro/bearish + disclaimer; decisão é do investidor |
| **Venda automática ao romper a MM200** | "O alerta já existe, por que não vender?" | O livro vende por **perda de fundamento**, não por preço; rompimento técnico é gatilho de revisão, não de venda | "Reveja os fundamentos" → reabrir a análise DDM/múltiplos |
| **Spam de osciladores de day trade** (Stochastic, Williams %R, CCI, Awesome, Ichimoku completo, Fibonacci, Elliott, candlestick patterns…) | "Quanto mais indicadores, melhor" | Poluição cognitiva; sinais contraditórios; público PF se perde; foge do escopo das 4 famílias travadas | Ficar nas 4 famílias escolhidas; tudo ligável/desligável |
| **Backtest / otimização de parâmetros do indicador** | "Quero saber o melhor RSI" | Convida data-mining e a ilusão de que timing técnico bate o veredito fundamentalista; custo de implementação alto; fora de escopo | Parâmetros canônicos fixos (com tooltip explicando o porquê) |
| **Alertas push / e-mail / preço-gatilho** | "Avise quando romper" | Exige backend e estado persistente; o projeto é custo zero, sem backend; Streamlit é stateless por sessão | Alerta exibido na própria aba ao abrir a ação |
| **Score técnico que sobrescreve barato/caro** | "Um número único de 0–100" | Quebra o Core Value: a mesma ação não pode parecer boa pelo técnico e cara pelo fundamento sem hierarquia clara | Fundamento manda; técnico só informa o *quando*; matriz 2 eixos, não nota fundida |
| **Sinais de venda a descoberto / short** | Vem "de brinde" com Donchian/MM (mínima de N, death cross) | Investidor de dividendos não opera vendido; ruído e risco | Suprimir o lado short; usar a mínima/death só como gatilho de reverificação |
| **Volume/OBV e indicadores que exigem dados extras** | "Volume confirma tendência" | Aumenta dependência de dados e complexidade; fora das 4 famílias; benefício marginal p/ buy-and-hold | Adiar; não está nas famílias travadas |

---

## Feature Dependencies

```
[Série de preço Close 5a (v1.1, já existe)]
    └──requires──> [SMA/EMA 20/50/200]
    └──requires──> [Donchian 20/55]
    └──requires──> [Bollinger 20/2σ]
    └──requires──> [RSI 14] ── [MACD 12/26/9] ── [ADX 14] ── [inclinação regressão]
                                   │
[Sinais discretos por indicador (§0)]
    └──requires──> [Resumo de timing de entrada (composite)]
    └──requires──> [Alerta de reverificação (perda de tendência)]

[Veredito DDM/múltiplos (engine, já existe)]
    └──enhances──> [Resumo de timing de entrada]   (cruza barato/caro × bullish/bearish)
    └──enhances──> [Alerta de reverificação]        ("reveja OS fundamentos" = volta ao DDM)

[Controles ligar/desligar/selecionar]
    └──enhances──> [todos os overlays do gráfico]

[Resumo composite] ──conflicts──> [Score técnico único que sobrescreve o veredito]  (anti-feature)
[Sinais diários]   ──conflicts──> [Sinais intraday]                                  (anti-feature)
```

### Dependency Notes

- **Tudo requer a série de preço de 5a do v1.1:** os indicadores são funções da mesma `Close`
  nominal (`auto_adjust=False`) já usada no gráfico — manter a mesma base evita distorção e mantém
  consistência com a banda DDM (decisão CR-01 do projeto). A MM200 exige ~200 pregões; com 5a há folga.
- **Composite requer os sinais discretos de §0:** o resumo é uma função determinística dos rótulos
  individuais — implementar os indicadores primeiro, o composite depois.
- **Composite e alerta são potencializados pelo veredito DDM:** o valor real do marco é cruzar
  *barato/caro* (fundamento, manda) com *em tendência/perdeu tendência* (técnico, informa o timing).
  Ler o campo de veredito da engine; nunca recalcular.
- **Composite conflita com "score técnico único":** fundir tudo num número apaga a hierarquia
  fundamento > técnico — por isso o composite é um selo consultivo + matriz, não uma nota que rivaliza com o DDM.

---

## O composite "timing de entrada" (especificação concreta)

Hierarquia (do mais ao menos importante para buy-and-hold):

1. **Tendência de fundo (peso alto):** preço × MM200 + ADX(14) + sinal da inclinação.
2. **Estrutura de médias (peso médio):** golden/death cross, stack das MMs, Donchian.
3. **Timing fino (peso baixo, desempate):** RSI(14), MACD(12/26/9), Bollinger.

Saída legível (3 estados), sempre prefixada pelo veredito fundamentalista:

- **"Tendência de alta — timing favorável"**: preço acima da MM200 **e** ADX > 25 com inclinação
  positiva (ou golden cross recente). Copy p/ ação barata: *"Ação barata (DDM) e em tendência de
  alta — bom momento para iniciar/aumentar posição. O técnico apoia o timing; o veredito é do fundamento."*
- **"Sem tendência clara — timing neutro"**: ADX < 20 ou sinais mistos. Copy: *"Ação barata, mas
  sem tendência definida no preço — o timing é incerto; você pode entrar pelo fundamento ou esperar
  o preço confirmar uma alta."*
- **"Tendência de baixa — atenção"**: preço abaixo da MM200 / death cross / Donchian rompido p/ baixo.
  Copy (gatilho de reverificação): *"O preço perdeu a tendência de alta (rompeu a MM200). Isso não é
  ordem de venda — reveja os fundamentos: se continuam intactos, queda de preço pode ser oportunidade;
  se deterioraram, é o sinal de saída do método."*

Matriz fundamento × técnico (como apresentar):

| | Em tendência de alta | Sem tendência | Perdeu tendência |
|---|---|---|---|
| **Barata (DDM)** | timing favorável p/ comprar | comprar pelo fundamento ou esperar | comprar com cautela / preço pode cair mais — fundamento manda |
| **Cara (DDM)** | não comprar (cara), técnico não muda | não comprar | não comprar; **reveja os fundamentos** |

> Regra de ouro impressa na UI: **o veredito barato/caro vem do método do livro; o técnico só diz o
> QUANDO e quando RE-OLHAR.**

---

## MVP Definition

### Launch With (v1.2 — marco atual)

- [ ] SMA/EMA 20/50/200 sobrepostas + **posição preço × MM200** — filtro de tendência primário; baixo custo, alto valor
- [ ] Golden cross / death cross (MM50 × MM200) — evento de longo prazo essencial
- [ ] RSI(14) 30/70 e MACD(12/26/9) com cruzamento — momentum/timing fino que o público espera
- [ ] ADX(14) > 25 + inclinação de regressão — responde "SE há tendência"; evita o erro nº 1
- [ ] Donchian 20/55 + Bollinger 20/2σ — canais; rompimentos rotulados
- [ ] Controles ligar/desligar/selecionar — decisão travada; evita poluição
- [ ] **Resumo de timing de entrada (composite consultivo)** — o coração do valor do marco
- [ ] **Alerta de reverificação** na perda de tendência (MM200/death cross/Donchian) → "reveja os fundamentos"
- [ ] Tooltips de glossário e degradação graciosa (histórico insuficiente) — paridade com o app

### Add After Validation (v1.x)

- [ ] Marcadores de eventos (cross/rompimentos) plotados nas datas — quando o resumo estiver validado
- [ ] Bollinger squeeze como contexto extra — se usuários pedirem leitura de volatilidade
- [ ] EMA opcional além da SMA (toggle) — se houver demanda por reação mais rápida

### Future Consideration (v2+)

- [ ] +DI/−DI plotados junto do ADX — só se o público pedir a direção via DMI
- [ ] Exportar o resumo de timing no relatório/CLI — quando o composite estiver estável e testado

---

## Feature Prioritization Matrix

| Feature | Valor p/ usuário | Custo de implementação | Prioridade |
|---------|------------------|------------------------|------------|
| Preço × MM200 + SMA 20/50/200 | HIGH | LOW | P1 |
| Golden/death cross | HIGH | LOW | P1 |
| Resumo de timing (composite) | HIGH | MEDIUM | P1 |
| Alerta de reverificação | HIGH | MEDIUM | P1 |
| Controles ligar/desligar | HIGH | LOW | P1 |
| RSI(14) | MEDIUM | LOW | P1 |
| MACD(12/26/9) | MEDIUM | MEDIUM | P1 |
| ADX(14) + inclinação | HIGH | MEDIUM | P1 |
| Donchian 20/55 | MEDIUM | MEDIUM | P2 |
| Bollinger 20/2σ | MEDIUM | LOW | P2 |
| Cruzamento com veredito DDM na UI | HIGH | MEDIUM | P1 |
| Marcadores de eventos no gráfico | MEDIUM | MEDIUM | P2 |
| Tooltips de glossário dos indicadores | MEDIUM | LOW | P1 |

**Chave de prioridade:**
- P1: necessário para o marco v1.2
- P2: deve entrar quando possível (dentro ou logo após o marco)
- P3: consideração futura

---

## Notas de implementação para o roadmapper

- **Sem dependências novas obrigatórias:** SMA/EMA, RSI, MACD, Donchian, Bollinger, ADX e inclinação
  são todos calculáveis com pandas/numpy (já no stack). `numpy.polyfit` cobre a regressão linear.
  Bibliotecas como `pandas-ta`/`ta` são opcionais e adicionam dependência — preferir cálculo próprio
  para custo zero, controle e testabilidade (golden tests).
- **Indicador mais pesado:** ADX (True Range, +DM/−DM, suavização de Wilder). É o único com risco de
  off-by-one; merece teste golden dedicado contra valores de referência.
- **Consistência de dados:** usar a MESMA série Close nominal do gráfico v1.1 (decisão CR-01). Não
  reintroduzir Adj Close aqui, senão MMs e bandas divergem visualmente do preço plotado.
- **Histórico mínimo:** MM200/Donchian 55 exigem janela cheia; com 5a (~1250 pregões) há folga, mas
  tratar ações recém-listadas com a degradação graciosa já padronizada (GRAF-03).
- **Estado dos controles:** Streamlit é stateless por sessão — guardar seleção em `st.session_state`;
  nada persiste entre sessões (coerente com "sem backend / custo zero").
- **Testabilidade:** o composite e cada sinal discreto devem ser funções puras na engine
  (`src/analista/`), espelhadas na UI sem recálculo — mesmo padrão app.py read-only do v1.1 —
  para entrarem nos testes golden.

---

## Sources

- Donchian / Turtle System (períodos 20/55 entrada, 10/20 saída): [Lizard Indicators — Donchian Channel Strategy (Turtle System)](https://www.lizardindicators.com/donchian-channel-strategy/), [Alchemy Markets — Turtle Trading Guide](https://alchemymarkets.com/education/strategies/turtle-trading-guide/), [Altrady — Turtle Trading Rules](https://www.altrady.com/blog/crypto-trading-strategies/turtle-trading-strategy-rules) — MEDIUM (múltiplas fontes concordam; corresponde ao sistema histórico de Dennis/Eckhardt)
- ADX(14) thresholds (<20 sem tendência, >25 tendência forte, >50 muito forte): [Fidelity — Average Directional Index (ADX)](https://www.fidelity.com/viewpoints/active-investor/average-directional-index-ADX), [Chart Guys — ADX Indicator](https://www.chartguys.com/articles/adx-indicator) — HIGH (fonte institucional + concordância)
- SMA/EMA 20/50/200, golden/death cross, Bollinger 20/2σ, RSI 14 (30/70), MACD 12/26/9: parâmetros canônicos consolidados em literatura padrão de análise técnica (Wilder, Appel, Bollinger) e prática corrente — HIGH (conhecimento estabelecido, estável; não há ambiguidade)
- Enquadramento consultivo / hierarquia fundamento > técnico: método do livro *O Investidor em Ações de Dividendos* (Orleans Martins & Felipe Pontes) + decisões travadas em `.planning/PROJECT.md` — HIGH

---
*Feature research for: indicadores de tendência consultivos sobre app fundamentalista de dividendos (B3)*
*Researched: 2026-06-24*
