# Pitfalls Research

**Domain:** Análise técnica / swing-trade setups sobre dados B3 gratuitos e atrasados (yfinance), adicionados a um app Streamlit fundamentalista existente
**Researched:** 2026-06-29
**Confidence:** HIGH (no-repaint/timezone/intraday limits verificados contra o código existente e a doc do yfinance; fidelidade de método e fronteira legal ancoradas no método Murphy e na Res. CVM 19/20 já citada no app)

> Numeração de fases: v1.4 começa na **Fase 12** (continua a partir da 11). A estrutura de
> fases assumida abaixo (e usada no mapeamento) é:
> - **Fase 12 — Ingestão intraday / camada de dados** (fetch multi-timeframe, split-adjust,
>   timezone, aviso de atraso, cache separado do diário)
> - **Fase 13 — Contexto de tendência + níveis** (Dow + MMs, S/R, alinhamento multi-timeframe)
> - **Fase 14 — Padrões gráficos + Fibonacci** (OCO, topos/fundos duplos, triângulos, bandeiras)
> - **Fase 15 — Montagem do setup** (zona de entrada, stop técnico, alvo, R:R, score de qualidade)
> - **Fase 16 — Página Streamlit + gráfico do momento** (overlays, botão Atualizar, avisos, "não recomendação")
>
> Se a estrutura final divergir, re-mapear pelo tema, não pelo número.

---

## Critical Pitfalls

### Pitfall 1: Repaint pela barra intraday em formação ("barra viva")

**What goes wrong:**
O gráfico "do momento" e o checklist de sinais usam a ÚLTIMA barra intraday, que ainda está se
formando (a vela das 14:37 num timeframe de 30m representa o intervalo 14:30–15:00 incompleto).
Um sinal (rompimento de Donchian, cruzamento de MACD, toque de Bollinger) aparece "ligado", o
usuário aperta **Atualizar** dois minutos depois e o sinal sumiu — porque o fechamento da barra
mudou. Isso é repaint clássico: o setup do passado se reescreve.

**Why it happens:**
`core/indicators.py` já é no-repaint POR BARRA FECHADA (Donchian com `.shift(1)`,
`min_periods=janela`, regressão trailing causal). Mas no diário a "última barra" só fecha às 18h;
no intraday ela está sempre viva durante o pregão. O código atual lê `close.iloc[-1]` em todos os
rótulos discretos (`posicao_mm200`, `rompimento_donchian`, `toque_bollinger`, `cruzamento_macd`) —
correto para barra fechada, traiçoeiro para barra parcial.

**How to avoid:**
- Na camada intraday, **descartar (ou marcar como provisória) a última barra não-fechada** antes de
  passar o frame para `indicadores.calcular()`. Regra: barra fechada = `now_saopaulo >= fim_do_intervalo`.
- Para sinais discretos (checklist, score), avaliar SEMPRE sobre a penúltima barra (última fechada);
  para o desenho do gráfico, pintar a barra viva com aparência distinta + legenda "barra em formação".
- O `.shift(1)` do Donchian já protege o CANAL; o que falta proteger é o COMPARADO (`close.iloc[-1]`).

**Warning signs:**
Sinais que piscam entre dois cliques de Atualizar no mesmo minuto; score que oscila ±20 pontos sem o
preço andar; "nova_maxima" às 10h05 que vira "nenhum" às 10h06.

**Phase to address:** Fase 12 (descartar barra viva na ingestão) + Fase 15 (score/checklist sobre barra fechada) + Fase 16 (render distinta da barra viva)

---

### Pitfall 2: Lookahead bias na detecção de padrões e no S/R (pivôs que "veem o futuro")

**What goes wrong:**
Detecção de topo/fundo duplo, OCO, triângulos e S/R por pivôs costuma usar `scipy.signal.argrelextrema`
ou "máximo local numa janela centrada" — que olha N barras à DIREITA do pivô. Num backtest visual isso
parece perfeito; ao vivo, o pivô "confirmado" só existe N barras DEPOIS, então o app mostra um padrão/nível
que um trader não poderia ter visto naquele instante. O alvo projetado e o score herdam o viés.

**Why it happens:**
Janela centrada (`order=k` no argrelextrema, ou `rolling(center=True)`) é o jeito intuitivo de achar
extremos "limpos", e em dados históricos não dói. É a mesma armadilha que o `.shift(1)` do Donchian já
evita no canal — mas a detecção de padrões é código NOVO (Fase 14), sem essa proteção embutida.

**How to avoid:**
- Pivô só é válido quando **confirmado por barras já fechadas à esquerda E à direita**; ao reportar "padrão
  detectado", marcar a data de CONFIRMAÇÃO (não a do ápice) e nunca antecipar.
- Para qualquer série derivada (linha de pescoço da OCO, neckline, projeção), garantir que todos os pontos
  usados têm índice ≤ barra atual fechada.
- Escrever um teste no espírito dos goldens: alimentar o detector com a série truncada em t e em t+1; o
  rótulo emitido para as barras ≤ t NÃO pode mudar quando chega t+1 (estabilidade no-repaint do padrão).

**Warning signs:**
Padrão aparece "centrado" no último topo sem barras de confirmação à direita; alvos que mudam quando você
adiciona uma barra ao fim da série; testes de no-repaint inexistentes na Fase 14.

**Phase to address:** Fase 14 (detector causal + teste de estabilidade) — também guardar contra na Fase 13 (pivôs de S/R)

---

### Pitfall 3: Misturar base nominal × split-adjusted × Adj Close no intraday

**What goes wrong:**
O diário já resolve isso com cuidado cirúrgico: `ohlc` nominal (`auto_adjust=False`) para o gráfico/banda
DDM, `ohlc_ajustado` split-only (`_ajustar_por_split`) para os indicadores, e `Adj Close` só para
beta/retorno. No intraday a tentação é chamar `tk.history(interval="30m")` com defaults — e o default do
yfinance é `auto_adjust=True`, que devolve preço dividend-adjusted. Resultado: níveis de S/R, stop e alvo
calculados numa base diferente do preço que o usuário vê, e indicadores rodando sobre uma série que mistura
proventos (o anti-pattern explicitamente proibido no docstring de `_ajustar_por_split`).

**Why it happens:**
Defaults silenciosos do yfinance (`auto_adjust` mudou de False→True como default em versões recentes), e a
janela intraday é curta (≤60d), então raramente cai um split/dividendo DENTRO da janela — o bug fica latente
e só morde quando há provento no período.

**How to avoid:**
- Reusar EXATAMENTE a convenção do diário: buscar intraday com `auto_adjust=False` e passar pela mesma
  `_ajustar_por_split` (split-only) antes dos indicadores; gráfico/níveis em nominal.
- Centralizar a busca intraday numa única função em `ingest/prices.py` que devolve o mesmo contrato
  (`ohlc` nominal + `ohlc_ajustado` split-only), espelhando `coletar_mercado`. Nunca chamar `tk.history`
  solto na página.
- Stop/alvo/entrada/R:R devem ser calculados na MESMA base do eixo do gráfico (nominal), senão o R:R exibido
  não bate com o que o usuário lê na tela.

**Warning signs:**
Preço do gráfico intraday diferente do `preco_atual`; níveis de Fibonacci que não encostam nas velas;
`auto_adjust` ausente da chamada intraday; um salto no preço intraday na data de um JCP/dividendo.

**Phase to address:** Fase 12 (contrato de ingestão intraday espelhando o diário)

---

### Pitfall 4: Setup lido como ORDEM — a fronteira "exibe, nunca recomenda" quebra no detalhe

**What goes wrong:**
"Zona de entrada R$ 28,40–28,70 · stop R$ 27,90 · alvo R$ 31,20 · R:R 1:3,1 · score 82/100" é
**operacionalmente indistinguível de uma recomendação de compra**, por mais disclaimer que tenha no rodapé.
Um score alto + setas verdes + a palavra "entrada" é lido como "compre agora". Isso colide com o
posicionamento de software educacional e com a CVM Res. 19/20 (análise/consultoria de valores mobiliários)
já citada no disclaimer do app — e é o risco mais caro do marco (regulatório + de marca).

**Why it happens:**
O método Murphy É operacional por natureza (ele ensina a montar a operação). Traduzir Murphy fielmente para
a tela produz, sem querer, algo que parece sinal de corretora. O disclaimer global na sidebar não cobre cada
número individual.

**How to avoid:**
- **Linguagem condicional e impessoal, sempre:** "o método de Murphy posicionaria o stop técnico abaixo do
  suporte em R$ 27,90" / "PROJEÇÃO do padrão" — nunca "entre", "compre", "alvo de lucro". Reusar o registro
  já validado nas Key Decisions ("EXIBE sinais, nunca recomenda").
- Rotular tudo como **leitura do método, não opinião do app**: "o que o método de Murphy aponta", não "o que
  recomendamos".
- Disclaimer **contextual** na própria página de swing (não só na sidebar): aviso de que são níveis técnicos
  educacionais, atraso de ~15min, e que score ≠ sinal de compra. Repetir o aviso CVM Res. 19/20 local.
- Score apresentado como **"qualidade técnica do desenho do setup" (0–100)**, com legenda explícita "não é
  probabilidade de alta nem sinal de compra".
- Revisão de copy dedicada antes do deploy (mesma régua do disclaimer adicionado em 2026-06-28).

**Warning signs:**
Qualquer texto no imperativo ("compre/venda/entre/saia"); score sem legenda de ressalva; setas verdes/vermelhas
sem rótulo de "sinal técnico, não ordem"; ausência de disclaimer NA página (só na sidebar).

**Phase to address:** Fase 15 (linguagem do setup/score) + Fase 16 (disclaimer contextual + copy review). É um **gate de aceite do marco**, não um detalhe de UI.

---

### Pitfall 5: Over-promising "tempo real" quando o dado tem ~15min de atraso

**What goes wrong:**
Botão "Atualizar" + gráfico "do momento" cria a expectativa de cotação ao vivo. O dado do Yahoo para B3 é
**atrasado ~15min** (e a última barra pode estar incompleta — Pitfall 1). Se um sinal "rompeu agora" estiver
15min defasado, o usuário age sobre informação velha achando que é live. Isso é tanto UX ruim quanto exposição
legal ("prometeu tempo real e entregou atraso").

**Why it happens:**
"Atualizar" sugere live; o atraso do Yahoo é invisível na resposta da API (vem um timestamp, mas não um
selo de "delayed"). O PROJECT.md já reconhece o atraso, mas é fácil a UI não comunicá-lo em cada refresh.

**How to avoid:**
- Selo permanente e visível: **"Dados atrasados ~15min (Yahoo) · não é cotação em tempo real"**, e mostrar o
  **timestamp da última barra** ("dados até 14:25") ao lado do botão Atualizar.
- Nunca usar a palavra "tempo real" / "ao vivo" na UI; preferir "dados mais recentes disponíveis".
- Streaming real é explicitamente fora de escopo (custo zero) — manter assim.

**Warning signs:**
Texto "ao vivo/tempo real" na página; ausência do timestamp da última barra; usuário não consegue saber se o
gráfico é de agora ou de 20min atrás.

**Phase to address:** Fase 16 (selo de atraso + timestamp por refresh); origem do timestamp vem da Fase 12

---

### Pitfall 6: Quebrar os 191 testes golden / violar o read-only de app.py

**What goes wrong:**
A camada de swing toca `ingest/prices.py` (novo fetch intraday) e reusa `core/indicators.py`. Um refactor
descuidado — mudar a assinatura de `coletar_mercado`, alterar `_ajustar_por_split`, mexer no contrato
`SinaisTecnicos`/`DadosMercado`, ou recalcular método dentro de `app.py` — derruba os goldens ou reintroduz
a divergência que o read-only de app.py foi criado para evitar.

**Why it happens:**
Pressão de "só adicionar um parâmetro" em funções compartilhadas; tentação de calcular stop/alvo/score na
própria página Streamlit (mais rápido de prototipar) em vez de numa função pura testável da engine.

**How to avoid:**
- **Aditividade obrigatória**: novos campos com default (o padrão já usado em `SinaisTecnicos.close` e
  `Canais.donchian_sup_55 = None`), nova FUNÇÃO de fetch intraday em vez de alterar `coletar_mercado`. Não
  mudar assinaturas existentes.
- **Toda lógica de setup (S/R, padrões, stop, alvo, R:R, score) vive na engine** (`core/`), pura e
  golden-testada; `app.py` só LÊ campos e desenha — mantendo a Key Decision "app.py é read-only".
- Rodar a suíte completa (191) ANTES e DEPOIS de cada fase; adicionar goldens NOVOS para a camada técnica
  (incl. testes de no-repaint dos Pitfalls 1 e 2).
- Não tocar nos números/contratos fundamentalistas (v1.0–v1.3) — a página é produto separado.

**Warning signs:**
Diff em assinaturas de funções existentes; cálculo de método dentro de `app.py`; queda em qualquer um dos
191 goldens; novos campos sem default no dataclass.

**Phase to address:** Todas as fases (gate de regressão por fase); explicitamente Fase 15 (lógica na engine, não na página) e Fase 16 (read-only)

---

### Pitfall 7: Ingestão intraday contaminando o pipeline diário e o cache

**What goes wrong:**
Os caches atuais (`montar`, `selic_atual`, `rf_capm`) usam `@st.cache_data(ttl=3600)` — 1h é perfeito para
fundamentos/diário e **errado para intraday** (uma barra de 5m envelhece em minutos; ttl=3600 serviria dados
de 1h atrás como "atualizados"). Pior: se a busca intraday for enfiada dentro de `montar()` ou compartilhar
chave de cache com o diário, o botão Atualizar não invalida nada (cache hit) OU a recoleta intraday dispara
recoleta de CVM/fundamentos desnecessária, estourando rate-limit do Yahoo.

**Why it happens:**
Reuso preguiçoso da função `montar` cacheada; não perceber que intraday e diário têm cadências de frescor
opostas; o `ttl=3600` herdado por copiar-colar o decorator.

**How to avoid:**
- **Função e cache SEPARADOS para intraday**, com `ttl` curto (ex.: 60–300s) coerente com o timeframe; chave
  de cache incluindo `(ticker, interval, period)`.
- Botão **Atualizar** = `st.cache_data.clear()` seletivo da função intraday (ou `ttl` curto + rerun), nunca
  recoletar fundamentos.
- Intraday NÃO entra em `montar()`/`build.montar_empresa`; vive na nova função de `ingest/prices.py`. O
  pipeline diário/fundamentalista fica intocado.
- Respeitar o retry/backoff já existente (`_MAX_TENTATIVAS`/`_BACKOFF_SEG`) para o rate-limit intermitente do
  Yahoo — intraday repetido é mais propenso a 429.

**Warning signs:**
Atualizar não muda nada (cache de 1h); recoleta de CVM ao trocar timeframe; `ttl=3600` numa função intraday;
rate-limit/empty frames do Yahoo após cliques repetidos.

**Phase to address:** Fase 12 (cache/fetch intraday isolado) + Fase 16 (semântica do botão Atualizar)

---

## Moderate Pitfalls

### Pitfall 8: Limites de período/intervalo do yfinance estourando silenciosamente

**What goes wrong:**
Pedir histórico além do que o Yahoo dá para cada intervalo retorna **frame vazio ou erro**, não um aviso
amigável. Limites (HIGH confidence, derivados do source do yfinance):

| Intervalo | Histórico máximo |
|-----------|------------------|
| 1m | ~7 dias por request (~30d total) |
| 2m / 5m / 15m / 30m / 90m | ~60 dias |
| 60m / 1h | ~730 dias |
| 1d e maiores | "max" |

Um SMA200 ou squeeze126 no frame de 5m (≤60d ≈ poucas centenas de barras, mas com buracos) frequentemente
não tem barras suficientes → tudo "indisponivel". Pior, pedir 5m com `period="1y"` simplesmente volta vazio.

**Why it happens:**
Reuso do `period="5y"` do diário em qualquer intervalo; desconhecimento da matriz de limites; a degradação
graciosa do código (NaN → "indisponivel") MASCARA o problema em vez de explicá-lo.

**How to avoid:**
- Tabela de `period` válido por `interval` na camada de ingestão; clamp automático + aviso na UI ("5m: só
  ~60 dias de histórico disponível").
- Avisar quando o histórico é curto demais para os indicadores de janela longa (SMA200/squeeze126): ou ocultar
  esses indicadores no timeframe curto, ou rotular "histórico insuficiente" explicitamente (não só
  "indisponivel" mudo).
- Validar `len(frame)` contra a maior janela ANTES de prometer o indicador.

**Warning signs:**
Frame vazio em 5m com period longo; indicadores todos "indisponivel" no intraday; SMA200 ausente sem explicação.

**Phase to address:** Fase 12 (matriz period×interval + clamp) + Fase 13 (gate de janela longa)

---

### Pitfall 9: Timezone — intraday tz-aware (America/Sao_Paulo) × diário tz-naive

**What goes wrong:**
yfinance devolve timestamps intraday **tz-aware no fuso da bolsa (America/Sao_Paulo, -03)**, mas barras
diárias vêm como datas **tz-naive**. Comparar/concatenar/alinhar as duas (multi-timeframe, marcar evento no
diário a partir de um pivô intraday) levanta `TypeError: tz-aware vs tz-naive` ou desalinha por 3h. Se o
servidor da VPS estiver em UTC, "hoje" e "barra fechada" calculados com `datetime.now()` ingênuo erram por 3h
— podendo tratar uma barra viva como fechada (realimenta Pitfall 1).

**Why it happens:**
Defaults inconsistentes do yfinance entre diário e intraday; cálculo de "agora" sem fuso explícito; a VPS roda
em UTC.

**How to avoid:**
- Normalizar o fuso na borda: **tudo em `America/Sao_Paulo`** ao decidir "barra fechada" e "última atualização";
  usar `pd.Timestamp.now(tz="America/Sao_Paulo")`, nunca `datetime.now()` naive.
- Ao alinhar timeframes, converter explicitamente (localizar o diário ou remover tz do intraday de forma
  consciente) — decisão única e documentada, não ad-hoc por call-site.
- B3 não tem DST desde 2019 (-03 fixo), o que simplifica, mas NÃO assumir o fuso do host.

**Warning signs:**
`TypeError` tz-aware/naive nos logs; "barra fechada" errada quando rodando na VPS (UTC) vs local; horário do
"dados até HH:MM" 3h adiantado.

**Phase to address:** Fase 12 (normalização de fuso na ingestão) + Fase 13 (alinhamento multi-timeframe)

---

### Pitfall 10: Tickers B3 ilíquidos — gaps, barras de volume zero e leilão

**What goes wrong:**
Small caps da B3 negociam pouco: barras intraday faltando, `Volume=0`, e os **leilões de abertura/fechamento
(e o after de fração)** produzem velas com preço estranho ou spread enorme. Indicadores de volume (confirmação
de rompimento, OBV) e padrões (bandeira/triângulo dependem de contração de volume) ficam ruidosos ou falsos.
Donchian/Bollinger sobre uma série esburacada geram "rompimentos" que são só ausência de negócio.

**Why it happens:**
O método assume liquidez contínua; a B3 fora dos blue chips não tem. O Yahoo preenche/omite barras de forma
inconsistente.

**How to avoid:**
- Reusar o `volume_financeiro_diario` já calculado para **avisar/bloquear setups em tickers de baixa
  liquidez** ("liquidez baixa — sinais técnicos pouco confiáveis"); o app já tem `volume_min_diario` no
  screening como referência.
- Tratar `Volume=0` como barra suspeita (não confirmar rompimento por volume nessas barras); não interpolar
  preço em buracos.
- Considerar excluir as barras de leilão de abertura/fechamento dos cálculos intraday, ou ao menos sinalizá-las.

**Warning signs:**
Setups "perfeitos" em tickers que mal negociam; rompimentos com volume 0; velas de leilão distorcendo S/R.

**Phase to address:** Fase 12 (limpeza/flag de barras) + Fase 15 (gate de liquidez no score)

---

### Pitfall 11: Over-fitting de padrões → enxurrada de falsos positivos

**What goes wrong:**
Detectores de OCO/triângulo/bandeira frouxos disparam em quase qualquer série (todo zigue-zague "parece" um
triângulo). O usuário vê 5 padrões num gráfico e perde a confiança — ou pior, age sobre ruído. Calibrar o
detector para bater num gráfico-exemplo (over-fit a 1 caso) explode em falsos positivos no resto.

**Why it happens:**
Padrões gráficos são subjetivos; sem limiares geométricos rígidos (tolerância de simetria, proporção mínima,
nº mínimo de toques), o detector vira gerador de pareidolia. Mesma armadilha do "generalizar, não tunar por
ticker" já aprendida no valuation (memória do projeto).

**How to avoid:**
- Limiares geométricos explícitos e conservadores no `config.yaml` (igual aos params dos indicadores): ex.
  topo/fundo duplo exige 2 toques dentro de X% e um vale/pico intermediário de ≥Y%; triângulo exige ≥N toques
  em cada linha. **Preferir poucos padrões de alta confiança a muitos frouxos.**
- Validar o detector contra um conjunto de tickers variados (não 1) — não recalibrar para acertar um gráfico
  específico.
- Exigir **confirmação** (rompimento + volume) antes de marcar o padrão como "ativo"; antes disso, "em
  formação".

**Warning signs:**
Múltiplos padrões sobrepostos no mesmo gráfico; detector calibrado contra um único exemplo; padrão sem
critério numérico de aceite.

**Phase to address:** Fase 14 (limiares geométricos + validação multi-ticker)

---

### Pitfall 12: S/R e Fibonacci arbitrários (ancoragem subjetiva)

**What goes wrong:**
Suporte/resistência e retração de Fibonacci dependem de QUAIS pivôs (swing high/low) você ancora. Escolha
implícita ou instável → níveis que mudam a cada refresh ou parecem chutados. Dois usuários (ou dois refreshes)
veem Fibos diferentes para o mesmo ticker. Sem regra determinística, o "alvo por Fibonacci" vira número
mágico — e alimenta a leitura de recomendação (Pitfall 4).

**Why it happens:**
Fibonacci/S/R não têm definição canônica única; o trader escolhe o swing "a olho". Em software isso vira uma
heurística implícita não-documentada e não-reproduzível.

**How to avoid:**
- **Regra determinística e documentada** para ancoragem: ex. Fibo ancorado no maior swing significativo das
  últimas N barras com amplitude ≥ X%; S/R por clustering de pivôs confirmados (Pitfall 2) com nº mínimo de
  toques. Mesmos dados → mesmos níveis (reproduzível, como o BSD de referência fixa do projeto).
- Mostrar de ONDE o nível veio ("ancorado no topo de 12/05 e fundo de 03/06") — transparência, não caixa-preta.
- Tornar a janela de look-back um parâmetro de `config.yaml`, não um literal escondido.

**Warning signs:**
Fibos que mudam entre refreshes sem o preço mudar; S/R sem justificativa de origem; ancoragem hard-coded.

**Phase to address:** Fase 13 (S/R determinístico) + Fase 14 (ancoragem de Fibonacci documentada)

---

### Pitfall 13: Erros de alinhamento multi-timeframe (Dow + MMs)

**What goes wrong:**
O contexto de tendência cruza timeframes (tendência maior no diário/semanal, gatilho no menor). Erros comuns:
(a) resample inconsistente (semanal W-FRI vs W-SUN muda as barras), (b) comparar uma MM200 diária com preço de
5m como se fossem o mesmo eixo temporal, (c) "lookahead" no resample (a barra semanal corrente inclui o futuro
da semana). O resultado é um "alinhado/desalinhado" errado, e o score herda.

**Why it happens:**
Resample tem muitas convenções; o projeto já apanhou disso (config `base_temporal` "diario" porque rodar os
params diários no frame semanal dava "RSI em onda quadrada"). Multi-timeframe multiplica essas escolhas.

**How to avoid:**
- Convenção de resample única e documentada (o app já usa W-FRI); a barra do timeframe maior usada para
  "contexto" deve ser **fechada** (não a semana corrente em formação) — mesmo princípio do Pitfall 1.
- Os parâmetros de indicador são calibrados para a barra diária (AUD-IND-01 no config); ao usar timeframe maior
  para contexto, usar leitura grosseira (direção da MM, posição vs MM) e não os mesmos limiares finos.
- Testar o alinhamento com séries truncadas (no-repaint do contexto).

**Warning signs:**
"Tendência de alta" no semanal que muda na sexta quando a barra fecha; mistura de eixos temporais num mesmo
julgamento; RSI/MACD esquisitos no timeframe maior (sinal de params fora de calibração).

**Phase to address:** Fase 13 (contexto de tendência multi-timeframe)

---

### Pitfall 14: R:R e stop produzindo divisão por zero / números absurdos

**What goes wrong:**
R:R = (alvo − entrada)/(entrada − stop). Se stop == entrada (preço colado no suporte) → divisão por zero/inf
vazando para a UI. Stop "técnico" longe demais → R:R lindo mas irreal; alvo de Fibonacci abaixo da entrada num
setup de alta → R:R negativo exibido como se fosse válido.

**Why it happens:**
Aritmética de borda não protegida; o código já teve esse tipo de bug em indicadores (daí os `np.errstate` por
toda parte). A camada de setup é nova e precisa da mesma disciplina.

**How to avoid:**
- Proteger todas as divisões (espelhar o padrão `np.errstate`/guards já onipresente em `indicators.py`):
  stop==entrada → "indisponivel", não inf; R:R negativo → setup inválido, não exibir score.
- Validar coerência geométrica: num setup de alta, exigir stop < entrada < alvo; senão marcar "setup
  incoerente" e não pontuar.
- Nunca propagar inf/NaN para `st.metric` (já há precedente: RSI protegido contra inf).

**Warning signs:**
"inf" ou "R$ nan" na tela; R:R negativo com score alto; stop = entrada.

**Phase to address:** Fase 15 (montagem do setup — guards de borda)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Calcular stop/alvo/score dentro de `app.py` | Protótipo rápido na tela | Quebra o read-only; impossível testar com golden; reintroduz divergência | **Nunca** — lógica vai para `core/` |
| `period="5y"` reaproveitado em qualquer interval | Uma chamada só | Frame vazio em 5m/1m; "indisponivel" mudo | Nunca para intraday — usar matriz period×interval |
| `ttl=3600` copiado para o fetch intraday | Reusa o decorator existente | Atualizar não atualiza; dados de 1h vendidos como frescos | Nunca no intraday — ttl curto |
| Detector de padrão calibrado num gráfico-exemplo | "Funciona" na demo | Falsos positivos em massa; perda de confiança | Nunca — validar multi-ticker |
| Janela centrada (`center=True`/argrelextrema order=k) para pivôs | Extremos "limpos" | Lookahead bias; padrões que repintam | Nunca para sinais ao vivo |
| Última barra intraday tratada como fechada | Gráfico "mais atual" | Repaint; sinais que piscam | Só para DESENHO, marcada como provisória |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| yfinance intraday | `tk.history(interval="30m")` com `auto_adjust` default (True) | `auto_adjust=False` + `_ajustar_por_split` (split-only), igual ao diário |
| yfinance intraday | `period` fixo independente do interval | Matriz period×interval com clamp (1m≤7d, ≤30m≤60d, 1h≤730d) |
| yfinance timezone | `datetime.now()` naive para "barra fechada" | `pd.Timestamp.now(tz="America/Sao_Paulo")`; VPS é UTC |
| yfinance rate-limit | Refresh agressivo sem backoff | Reusar `_MAX_TENTATIVAS`/`_BACKOFF_SEG`; ttl curto mas não zero |
| Streamlit cache | Intraday dentro de `montar()` (ttl=3600) | Função+cache separados, ttl curto, chave (ticker,interval,period) |
| Streamlit "Atualizar" | `st.cache_data.clear()` global (limpa fundamentos) | Clear seletivo só do fetch intraday / rerun com ttl curto |
| `core/indicators.calcular` | Mudar o contrato `SinaisTecnicos` para encaixar swing | Campos aditivos com default (padrão já usado) |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Recoleta de fundamentos a cada Atualizar | App lento, rate-limit Yahoo | Separar cache intraday do `montar` | Já no 1º usuário clicando muito |
| Detecção de padrão O(n²) sobre série longa a cada rerun | Página trava ao mexer em toggle | Cachear a detecção; rodar só na barra fechada nova | Séries 1h/730d ou muitos overlays |
| Loop Python barra-a-barra para S/R/padrões em cada rerun | Lentidão perceptível | Vetorizar; cachear resultado por (ticker,interval) | Reruns frequentes do Streamlit |

## Security / Legal Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Setup lido como ordem de compra/venda | CVM Res. 19/20 (análise/consultoria sem registro); risco de marca | Linguagem condicional; disclaimer contextual; score com ressalva (Pitfall 4) |
| "Tempo real" com dado atrasado | Usuário age sobre dado velho; exposição legal | Selo "~15min atraso" + timestamp da barra (Pitfall 5) |
| Disclaimer só na sidebar | Página de swing parece sinal de corretora | Disclaimer NA página, repetindo Res. 19/20 e "score ≠ compra" |
| Sugerir performance/lucro ("alvo de lucro") | Promessa de resultado | "PROJEÇÃO do padrão", sem linguagem de retorno garantido |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Score sem legenda | Lido como probabilidade de alta / sinal de compra | "Qualidade técnica do desenho (0–100), não é sinal de compra" |
| "indisponivel" mudo no intraday curto | Usuário acha que o app quebrou | "Histórico insuficiente para SMA200 neste timeframe" |
| Gráfico sem marcar a barra viva | Confusão sobre o que é definitivo | Barra em formação com estilo distinto + legenda |
| Múltiplos padrões frouxos sobrepostos | Ruído, perda de confiança | Poucos padrões de alta confiança, confirmados |
| Níveis Fibo/S/R sem origem | Parecem chutados | Mostrar pivôs de ancoragem ("topo 12/05, fundo 03/06") |

## "Looks Done But Isn't" Checklist

- [ ] **Sinais intraday:** a última barra é fechada? Verificar que checklist/score usam barra FECHADA, não a viva.
- [ ] **Detecção de padrão:** existe teste de no-repaint (truncar em t vs t+1, rótulo das barras ≤ t imutável)?
- [ ] **Base de preço intraday:** `auto_adjust=False` + split-only? Conferir num ticker com provento na janela.
- [ ] **Limites yfinance:** 5m com period longo retorna vazio? Há clamp + aviso?
- [ ] **Timezone:** roda igual na VPS (UTC) e local? "Barra fechada" usa America/Sao_Paulo?
- [ ] **Cache intraday:** Atualizar realmente re-busca? Não recoleta fundamentos?
- [ ] **191 goldens:** verdes antes E depois de cada fase? Novos goldens técnicos adicionados?
- [ ] **app.py read-only:** nenhum cálculo de método na página — tudo lido da engine?
- [ ] **Linguagem:** zero imperativo ("compre/venda/entre"); disclaimer na própria página?
- [ ] **Atraso comunicado:** selo ~15min + timestamp da última barra visível a cada refresh?
- [ ] **Liquidez:** ticker ilíquido avisa/bloqueia setup?
- [ ] **R:R:** stop==entrada e R:R negativo tratados (sem inf/nan na tela)?

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Repaint da barra viva | LOW | Descartar última barra na ingestão; reavaliar sinais sobre `iloc[-2]` |
| Lookahead em padrões | MEDIUM | Reescrever detector causal + teste de estabilidade; revalidar alvos |
| Base nominal/ajustada trocada | LOW | Centralizar fetch intraday no contrato do diário; um ponto de correção |
| Setup lido como recomendação | MEDIUM | Copy review + disclaimer contextual; pode exigir redeploy e revisão de marca |
| Cache intraday errado (ttl 3600) | LOW | ttl curto + função separada; clear seletivo no Atualizar |
| Golden quebrado | LOW–MEDIUM | `git` bisect da fase; reverter mudança de assinatura; restaurar aditividade |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. Repaint barra viva | 12 + 15 + 16 | Sinal estável entre dois refreshes no mesmo minuto |
| 2. Lookahead em padrões/S-R | 14 (e 13) | Teste: rótulo das barras ≤ t não muda em t+1 |
| 3. Base nominal × ajustada intraday | 12 | Preço do gráfico == preco_atual; sem salto em data de provento |
| 4. Setup = recomendação | 15 + 16 (gate de marco) | Copy review: zero imperativo; disclaimer na página |
| 5. "Tempo real" vs atraso | 16 | Selo ~15min + timestamp da barra presentes |
| 6. Golden / read-only | Todas (gate por fase) | 191 verdes; nenhum cálculo de método em app.py |
| 7. Cache/pipeline intraday | 12 + 16 | Atualizar re-busca intraday sem recoletar CVM |
| 8. Limites period×interval | 12 + 13 | 5m com period longo não retorna vazio (clamp+aviso) |
| 9. Timezone tz-aware/naive | 12 + 13 | Mesmo resultado na VPS (UTC) e local |
| 10. Tickers ilíquidos | 12 + 15 | Aviso/bloqueio em baixa liquidez; volume 0 não confirma rompimento |
| 11. Over-fit de padrões | 14 | Validação multi-ticker; limiares no config |
| 12. S/R e Fibo arbitrários | 13 + 14 | Mesmos dados → mesmos níveis; origem exibida |
| 13. Alinhamento multi-timeframe | 13 | Contexto usa barra do TF maior FECHADA |
| 14. R:R / stop divisão por zero | 15 | Sem inf/nan; setup incoerente não pontua |

## Sources

- Código existente do projeto (HIGH): `src/analista/core/indicators.py` (no-repaint: Donchian `.shift(1)`,
  `min_periods`, regressão trailing causal, Wilder SMA-seeded; `np.errstate` guards), `src/analista/ingest/prices.py`
  (`auto_adjust=False`, `_ajustar_por_split` split-only, retry/backoff Yahoo), `app.py` (read-only, `@st.cache_data ttl=3600`, disclaimer CVM Res. 19/20), `config.yaml` (`base_temporal: diario`, AUD-IND-01)
- `.planning/PROJECT.md` — Key Decisions ("EXIBE sinais, nunca recomenda"; intraday best-effort ~15min; página separada; v1.4 começa na Fase 12)
- yfinance — limites intraday por intervalo (HIGH, derivado do source `scrapers/history.py`):
  https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/history.py
- AlgoTrading101 — yfinance guide (limites 1m≤7d, intraday≤60d): https://algotrading101.com/learn/yfinance-guide/
- yfinance docs/functions (timezone, prepost): https://ranaroussi.github.io/yfinance/reference/yfinance.functions.html
- yfinance Issue #1010 — resultado depende do timezone do host (MEDIUM): https://github.com/ranaroussi/yfinance/issues/1010
- TradingHours — B3 horários/fuso America/Sao_Paulo (MEDIUM): https://www.tradinghours.com/markets/bovespa
- Memória do projeto — "generalizar, não tunar por ação"; Res. CVM 19/20 já no disclaimer

---
*Pitfalls research for: análise técnica swing-trade sobre dados B3 gratuitos/atrasados, adicionada a app fundamentalista existente*
*Researched: 2026-06-29*
