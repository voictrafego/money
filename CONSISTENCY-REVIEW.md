---
review: consistency-audit
target: app.py (3 modos) + engine + glossário + cli
reviewed: 2026-06-04
depth: deep
status: issues_found
findings:
  critical: 3
  warning: 7
  info: 6
  total: 16
files_reviewed_list:
  - app.py
  - src/analista/cli.py
  - src/analista/glossario.py
  - src/analista/core/multiples.py
  - src/analista/core/fundamentals.py
  - src/analista/core/screening.py
  - src/analista/core/comparables.py
  - src/analista/core/ddm.py
  - src/analista/core/capm.py
  - src/analista/core/growth.py
  - src/analista/core/lifecycle.py
  - src/analista/report/report.py
  - src/analista/ingest/build.py
  - src/analista/ingest/cvm.py
  - src/analista/ingest/prices.py
  - src/analista/ingest/macro.py
  - src/analista/ingest/universe.py
  - config.yaml
---

# Auditoria de Consistência — Analista de Dividendos

**Escopo:** consistência das análises financeiras entre os 3 modos da app Streamlit
(`Analisar`, `Garimpar BSD`, `Ranking por múltiplos`), e entre app.py / cli.py / report.py / engine / glossário.

## Sumário executivo

A boa notícia: as **fórmulas das métricas** (ROE, P/L, DY, payout, ML, EY) têm
**uma única implementação** em `multiples.py`/`fundamentals.py` e são chamadas pelos três
modos e pela CLI. Não há ROE/P-L/DY duplicado divergindo entre modos. As **unidades**
(decimal interno, ×100 só na borda de exibição) são consistentes em app.py, report.py e
cli.py. CLI e UI consomem a mesma engine sem cálculo copiado divergente.

A má notícia: há **três inconsistências de ANO-BASE** entre o que a engine usa para os
números e o que a UI/glossário promete ("até ANO_BASE", "DY > Selic"), uma promessa de
corte que **não existe** em dois dos três modos, e uma **discrepância de definição de
crescimento esperado** (BSD vs glossário). Esses geram casos reais em que a mesma empresa
parece boa num modo e ruim noutro sem explicação visível ao usuário.

---

## Critical

### CR-01: "Garimpar" promete "DY > Selic" mas o ranking BSD exibido **ignora** esse corte

**Arquivos:** `app.py:185-223`, `app.py:71`, `glossario.py:79-84`, `core/screening.py:285-328`

No modo Garimpar a UI promete fortemente o corte por Selic:
- Sidebar: `st.sidebar.metric("Selic (corte do DY)", ...)` (`app.py:71`)
- Subtítulo do modo BSD e tooltip `h("bsd")` falam de "dividendo grande e seguro".

Mas o **ranking exibido** (coluna `BSD` e `BSD > 80`, `app.py:216-217`) vem de
`sc.bsd_ranking(...)`, que **não recebe `selic`** e **não aplica corte algum por Selic**
(`screening.py:285`). O corte por Selic só existe em `filtros_customizados()`
(`screening.py:63-65`), cujo resultado é jogado numa coluna secundária "Passa filtros"
(`app.py:217`) e **a tabela é ordenada por BSD**, não por esse filtro (`app.py:221`).

Consequência concreta: uma empresa com DY abaixo da Selic pode aparecer no topo do
garimpo com BSD alto e selo "✅ BSD > 80", contradizendo diretamente o rótulo
"Selic (corte do DY)" e o método do livro ("não começar pelo DY, mas o DY tem de superar
a renda fixa"). Dentro do próprio BSD, o `dividend_yield` é só 1 de 10 fatores com peso 5%
(`screening.py:181`), e ainda é padronizado 0–100 relativo ao grupo — nunca comparado à Selic.

**Por que é inconsistente:** o usuário lê "corte do DY = Selic" e vê um ranking que não
corta nada por Selic. O mesmo papel reprovado no espírito do filtro aparece como campeão.

**Correção sugerida:** ou (a) ordenar/filtrar a tabela do Garimpo por `passou` (filtros
customizados, que contêm o corte Selic) antes do BSD, ou (b) trocar o rótulo da sidebar e
o caption para deixar claro que o BSD é uma nota relativa de estabilidade **sem** corte por
Selic, e que o corte vive apenas na coluna "Passa filtros". Recomendado (a)+destacar que
BSD>80 sem "Passa filtros" não é recomendação.

---

### CR-02: Ano usado nos múltiplos depende de dados faltantes — Ranking e Analisar podem divergir para a MESMA empresa

**Arquivos:** `app.py:251` e `app.py:263` (Ranking), `report/report.py:50` (Analisar),
`fundamentals.py:50-52` (`ultimo_ano`), `ingest/build.py:43-66`

Os três modos usam `c.ultimo_ano()` como ano-base das métricas (Analisar em
`report.py:50`; Ranking em `app.py:251`; DY do Garimpo via `dy_atual()` em
`fundamentals.py:74-78`). Isso é **bom** — todos olham o mesmo conceito de "último ano".
Porém `ultimo_ano()` é o **maior ano com lucro líquido coletado** (`build.py:66`:
`c.anos = sorted(a for a in anos if a in c.lucro_liquido)`), e isso depende de **quais
contas a CVM tinha** no momento da coleta.

Dois problemas concretos de consistência:

1. **Ano dos múltiplos ≠ ano do payout do veredito.** Em Analisar, os múltiplos
   (incl. ROE, DY, P/L) usam `ult` (`report.py:54-64`), mas o payout projetado do DDM
   usa **média dos 3 últimos anos** (`_media_payout_3a`, `report.py:41-45`, `:102`). Já no
   Ranking, o payout que alimenta a regressão usa **só `ultimo_ano`** (`app.py:257, 264`).
   Assim, para a mesma empresa, o payout que decide o preço-alvo no Ranking (ano único)
   diverge do payout que decide o valor intrínseco em Analisar (média 3a) — sem nenhuma
   indicação ao usuário. Veredito "subavaliada" pode discordar entre os modos por isso.

2. **`ultimo_ano` instável entre execuções/empresas.** Como o cache `montar()` tem
   `ttl=3600` (`app.py:33`) e a coleta CVM pode trazer o ano N para uma empresa e só N-1
   para outra (fallback de DFP não publicada, `cvm.py:51-70`), duas empresas no **mesmo
   Ranking** podem estar sendo comparadas em **anos-base diferentes** (uma em 2025, outra
   em 2024) dentro da mesma regressão `ajustar_regressao_pl` (`app.py:259`), o que mistura
   P/L correntes (preço de hoje) com payout/ROE de anos distintos. O livro pressupõe o
   mesmo corte temporal para a regressão de comparáveis (Cap. 12).

**Por que é inconsistente:** a coluna "até ANO_BASE" da sidebar (`app.py:72`) sugere ano
uniforme; na prática cada empresa pode cair num ano diferente, e o veredito/preço-alvo do
Ranking usa um payout (1 ano) diferente do payout (3 anos) do veredito do Analisar.

**Correção sugerida:**
- Padronizar a janela do payout: usar `_media_payout_3a` (ou o último ano) **nos dois**
  modos. Hoje Analisar usa 3a e Ranking usa 1a — escolher um e reusar a mesma função.
- Exibir, no Ranking e no Garimpo, o ano-base efetivo de cada empresa
  (`c.ultimo_ano()`), para o usuário enxergar quando há mistura de anos.
- Opcional: na regressão, restringir ao mesmo ano-base ou sinalizar quando os anos diferem.

---

### CR-03: ROE/EY do Ranking entram com valores `None`/negativos tratados de forma silenciosamente diferente do Analisar

**Arquivos:** `app.py:249-258`, `core/comparables.py:26-34`, `core/comparables.py:89-93`,
`report/report.py:56-64`

No Ranking, `padronizar_multiplo` descarta valores `<= 0` e `None`
(`comparables.py:27, 34`), e `ajustar_regressao_pl` descarta linhas com `p <= 0` ou
qualquer `None` em (PL, DP, ROE) (`comparables.py:90-93`). Isso significa que uma empresa
com **ROE não calculável** (PL inicial ≤ 0 → `mult.roe` devolve `None`, `multiples.py:37`)
ou **payout `None`** é silenciosamente **removida da regressão** e recebe nota parcial,
**enquanto no Analisar a mesma empresa recebe um veredito completo** baseada apenas nos
múltiplos que existem. Pior: `preco_alvo_por_regressao` exige `dp`, `roe`, `lpa` não-None
(`comparables.py:128`); se faltar qualquer um, **a empresa não recebe preço-alvo** e
aparece como "—"/"Cara 🔺"=ausente, sem aviso de que faltou dado — o usuário pode ler
"sem upside" como "cara".

Além disso, **DP (payout) > 1.0 não é tratado igual.** Em Analisar, payout é limitado a
1.0 só para a projeção do DDM (`report.py:104`) e gera **alerta** ">100%"
(`report.py:136-137`). No Ranking, o payout cru (podendo ser >1 ou negativo se LPA<0)
entra direto na regressão `b1*DP` (`comparables.py:130`) sem limite nem alerta, podendo
puxar o P/L esperado e o preço-alvo para valores sem sentido — divergindo do tratamento
do Analisar para a mesma empresa.

**Por que é inconsistente:** mesma empresa, mesmo ano, dado idêntico → Analisar dá
veredito e alerta de payout; Ranking dá "—" silencioso ou um preço-alvo distorcido por
payout fora de faixa. O usuário não tem como saber que a divergência vem de dado faltante
vs. dado anômalo.

**Correção sugerida:**
- No Ranking, exibir explicitamente "ROE/payout indisponível" quando a empresa for
  descartada da regressão (em vez de "—" ambíguo).
- Aplicar o mesmo clamp/alerta de payout>100% do Analisar antes de alimentar a regressão,
  ou ao menos sinalizar payout fora de [0,1] na tabela do Ranking.

---

## Warning

### WR-01: ROE usa "PL inicial com fallback para PL do próprio ano" — diverge do glossário e do significado entre empresas

**Arquivos:** `fundamentals.py:69-72`, `glossario.py:34-38`, `glossario.py:48`

`c.roe(ano)` faz: `pl_ini = self.patrimonio_liquido.get(ano-1, self.patrimonio_liquido.get(ano))`
(`fundamentals.py:71`). O glossário promete "PL inicial **ou médio** (não o final)"
(`glossario.py:36-37`). Na prática:
- Para o **primeiro ano da janela** (sem ano-1 coletado), o ROE usa **PL final do próprio
  ano** — exatamente o que o tooltip diz que NÃO se usa.
- Para os demais anos usa PL inicial. Nunca usa PL médio, embora `roe_medio` exista em
  `multiples.py:42-49` e não seja chamado em lugar nenhum.

Consequência de consistência: o ROE do 1º ano da tabela de 10 anos (`app.py:175`,
`report.py:182`) é calculado com base diferente dos outros anos → a série de ROE mistura
duas definições. Em empresas que cresceram muito o PL, isso muda visivelmente o ROE do ano
inicial.

**Correção sugerida:** ou alinhar o glossário ("PL inicial; no 1º ano sem histórico, usa o
PL do próprio ano"), ou usar `roe_medio` quando houver PL inicial e final e remover o
fallback silencioso para PL final.

---

### WR-02: "g por fundamentos" no BSD usa payout de 1 ano; em Analisar usa payout de 1 ano também, mas o glossário do BSD não menciona que é um proxy

**Arquivos:** `core/screening.py:234-237`, `report/report.py:70`, `glossario.py:54-62`,
`glossario.py:79-84`

`crescimento_por_fundamentos(roe, payout)` = `roe*(1-payout)` (`growth.py:49-56`) — bate
com o glossário (`glossario.py:57`). OK na fórmula. Porém:
- Em Analisar, `g_fundamentos` usa `c.roe(ult)` e `c.payout(ult)` (`report.py:70`) — ano
  único.
- No BSD, o fator `crescimento_lucro_lp` cai para esse mesmo `g_fundamentos` **como proxy**
  quando `g_lucro_esperado` é None (`screening.py:235-237`), mas usando `c.roe(ult)`/`c.payout(ult)`
  — também ano único, embora os demais fatores do BSD usem **média de 3 anos**
  (`screening.py:193`, `anos_media`). Mistura de janelas dentro do próprio BSD.

O tooltip do BSD (`glossario.py:79-84`) não diz que `crescimento_lucro_lp` é, na ausência
de estimativa de analistas, apenas `ROE×(1−payout)` do último ano — o usuário pode crer que
é "crescimento esperado pelos analistas".

**Correção sugerida:** documentar o proxy no tooltip do BSD e padronizar a janela
(usar média de `anos_media` para roe/payout do proxy, igual aos outros fatores).

### WR-03: Payout do DDM (média 3a, clamp 1.0) vs payout dos múltiplos (1 ano, sem clamp) na MESMA tela

**Arquivos:** `report/report.py:41-45`, `report/report.py:61`, `report/report.py:102-104`

Na tela Analisar, a tabela de múltiplos mostra `DP (payout)` do **último ano**
(`report.py:61`, exibido em `app.py:128-129`), mas o DDM logo abaixo usa
`_media_payout_3a` com clamp em 1.0 (`report.py:102-104`). São dois números de "payout" na
mesma análise com bases diferentes. Se o payout do último ano for 130% e a média 3a 85%, o
usuário vê "Payout 130% (alerta)" e um DDM calculado com 85% sem explicação do porquê.

**Correção sugerida:** exibir também o "payout projetado (média 3a)" usado pelo DDM, ou
anotar na aba Valuation qual payout alimentou a projeção.

### WR-04: `dy_atual()` (Garimpo/BSD) usa `dpa` do `ultimo_ano`, não DY "trailing 12m" — diverge da intuição do tooltip de DY

**Arquivos:** `fundamentals.py:74-78`, `glossario.py:30-33`, `report/report.py:63`

`dy_atual` = `dpa(ultimo_ano)/preco_atual` (`fundamentals.py:78`). O DPA do último ano vem
de `dividendos_por_ano` do Yahoo agregado por ano-calendário (`build.py:60-63`,
`prices.py:96-101`). Se o `ultimo_ano` da empresa for um ano antigo (DFP recente faltando,
CR-02), o DY do Garimpo usa **dividendos de um ano antigo sobre o preço de hoje** — número
sem sentido econômico, e diferente do DY mostrado em Analisar quando os anos divergirem.
O tooltip (`glossario.py:30-33`) implica DY corrente.

**Correção sugerida:** usar o DPA dos últimos 12 meses (soma das datas reais do Yahoo) para
o DY corrente, ou alinhar `ultimo_ano` ao ano dos dividendos. Pelo menos sinalizar o ano do
DPA usado.

### WR-05: `desempenho_relativo_6m` e fatores de mercado entram no BSD mas dependem do Yahoo, que pode estar parcialmente vazio — fatores viram 0 silenciosamente

**Arquivos:** `core/screening.py:271-282`, `core/screening.py:222-223`, `ingest/prices.py:82-92`

`_padronizar_0_100` atribui **0** a indicadores ausentes (`screening.py:275, 280`). Vários
fatores do BSD (`desempenho_relativo_preco`, `variacao_tangivel_vp`, `cobertura_juros`)
dependem de dados que podem faltar (sem intangível, sem despesa de juros, sem índice no
yfinance). Quando faltam, a empresa recebe **0** naquele fator (não "neutro"), penalizando
empresas com lacuna de dado em vez de excluí-las — e o usuário não vê quais fatores
entraram. Duas empresas idênticas, uma com `despesa_juros` ausente, terão BSD diferentes
por motivo puramente de cobertura de dados.

**Correção sugerida:** distinguir "ausente" de "pior valor"; usar média/neutro (50) para
ausentes, ou expor quantos fatores foram efetivamente calculados por empresa.

### WR-06: `bsd_ranking` re-padroniza a média ponderada para 0–100 → "BSD > 80" é **relativo ao lote**, não absoluto como o glossário promete

**Arquivos:** `core/screening.py:315-324`, `glossario.py:79-84`, `app.py:188`

O passo final faz `bsd_final = _padronizar_0_100(medias_ponderadas)` (`screening.py:315`):
a maior média do lote vira ~100 e a menor ~0. Logo o "BSD" depende de **quais outras
empresas** você colou na caixa. O tooltip e o caption dizem "BSD acima de 80" como um corte
absoluto de Carlson ("só 19 de 297 passaram", `glossario.py:82-83`; `app.py:188`). Na
implementação, colar 2 empresas faz a melhor ter BSD≈100 quase sempre; colar as mesmas 2
junto de 10 ótimas muda o BSD delas. O mesmo papel pode ter BSD 95 num lote e 40 noutro.

**Por que é inconsistente:** o número exibido como se fosse uma nota absoluta (comparável
ao corte 80 do livro) é, na verdade, um rank relativo ao conjunto submetido. O Garimpo e o
Ranking ficam não-reproduzíveis entre execuções com tickers diferentes.

**Correção sugerida:** ou (a) padronizar contra uma referência fixa/universo amplo em vez
do lote, ou (b) renomear a coluna para "BSD relativo (0–100 no lote)" e remover a sugestão
de comparar com o corte absoluto 80; ajustar o tooltip `h("bsd")`.

### WR-07: `min(valores)`/`max(valores)` do intervalo intrínseco assume DDM-H ≤ DDM-constante, mas o veredito recomputa min/max independentemente

**Arquivos:** `app.py:107-108`, `report/report.py:122-130`

O intervalo exibido na métrica (`app.py:107-108`) calcula `min/max` dos dois DDMs, e o
veredito (`report.py:122-130`) recalcula `min/max` dos mesmos dois. Funcionalmente
coincidem hoje, mas são **dois cálculos independentes do mesmo intervalo** — se um dia a
ordem mudar (ex.: `ddm_h` faltando), a métrica e o texto do veredito podem mostrar
intervalos diferentes. Duplicação de lógica de fronteira.

**Correção sugerida:** o veredito já calcula `vmin/vmax`; expor esses valores no
`AnaliseAcao` e a UI reusar, em vez de recomputar de `(a.ddm_h, a.ddm_constante)`.

---

## Info

### IN-01: ROE — implementação única, consistente entre todos os modos (OK, com a ressalva WR-01)

`mult.roe` (`multiples.py:32-39`) é a única fórmula de ROE; chamada via `c.roe()` em
Analisar (`report.py:58`), Ranking (`app.py:254`, `cli.py:139`), BSD/filtros
(`screening.py:57, 237`) e tabela de fundamentos (`app.py:175`). **Não há ROE duplicado
divergente.** A única ressalva é o fallback de PL do 1º ano (WR-01).

### IN-02: P/L, EY, ML, DY, payout — fórmula única em multiples.py, usada por todos os modos (OK)

`preco_lucro`, `earnings_yield`, `margem_liquida`, `dividend_yield`, `dividend_payout`
(`multiples.py:52-92`) são chamadas de forma idêntica em `report.py:57-63`, `app.py:253-257`
e `cli.py:138-142`. Sem duplicação divergente. Unidades em decimal, consistentes.

### IN-03: Unidades (decimal vs %) — consistentes; ×100 só na borda de exibição (OK)

Engine mantém tudo em decimal. `fmt_pct` (`app.py:48`) e `_pct` (`report.py:153`) aplicam
×100 uma única vez na exibição. No Ranking, `fmt_pct(pa.upside)` (`app.py:275`) e na CLI
`pa.upside*100` (`cli.py:161`) — coerentes. Não há double-scaling nem falta de scaling
detectados. O PEG (`multiples.py:57-66`) é o único que espera g em pontos percentuais, mas
não é exibido em nenhum dos 3 modos (sem risco de mistura).

### IN-04: Ke / Beta / g / DDM — UI não recalcula; lê direto de `AnaliseAcao` (OK)

`a.ke`, `a.beta`, `a.g_historico/g_fundamentos/g_alto/g_estavel`,
`a.ddm_constante/ddm_h.valor_intrinseco` exibidos em `app.py:114, 137-143, 149-152` vêm
direto de `report.analisar_acao` (`report.py:69-119`). A matriz de sensibilidade da UI
(`app.py:159-163`) só **rotula** as linhas/colunas recomputando `a.g_alto+dg` e
`(a.ke or 0)+dk`, mas os **valores** vêm de `a.sensibilidade` (engine). Mesmos rótulos em
`report.py:224-227`. Sem recálculo divergente de valor.

### IN-05: CLI vs UI — mesma engine, sem cálculo de valor duplicado (OK)

`cmd_rank` (`cli.py:133-167`) e o modo Ranking da UI (`app.py:249-281`) montam os mesmos
vetores (ML/ROE/PL/EY/DP) chamando as mesmas funções, e ambos delegam a
`cmp.ranking_por_multiplos` / `ajustar_regressao_pl` / `preco_alvo_por_regressao`. Idem
`cmd_screen` vs modo Garimpo. A única diferença é formatação. Não há fórmula copiada na CLI
que divirja do `comparables.py`. (As inconsistências CR-02/CR-03/WR-* afetam CLI e UI por
igual, justamente por compartilharem a engine — são problemas da engine, não de divergência
CLI×UI.)

### IN-06: Semântica de `dpa_inicial` no DDM é ambígua entre report.py e o teste de referência

**Arquivos:** `report/report.py:108`, `core/ddm.py:62-75`, `core/ddm.py:101`, `tests/test_ddm.py:38-43`

Em `report.py:108`, `dpa_inicial = lpa*(1+g_alto)*payout` = DPA já projetado para o ano 1,
e o engine coloca `divs[0]=dpa_inicial` descontado a `(1+ke)^1` (`ddm.py:101`) — coerente.
Já o teste de referência (`test_ddm.py:38-43`) passa `dpa_inicial=2.362` que é o DPA_2020
**já pago** (ano 0) e espera `dividendos_projetados[-1]≈5,68` (= 2,362·1,1024^9), ou seja,
trata divs[0] como ano 1 mesmo sendo o ano 0. A matemática reproduz o livro nos dois casos
porque o desconto começa em `^1` em ambos, mas a **documentação** ("PRIMEIRO ano (t=1)",
`ddm.py:89`) e o uso em report.py (que cresce 1 ano antes de passar) descrevem um
deslocamento de 1 ano em relação ao caso de referência. Não é divergência entre modos
(report.py é a única fonte do DDM nos 3 modos), mas é fonte provável de confusão/erro
futuro. Sugestão: alinhar a docstring e o caso de teste para a mesma convenção de t.

---

_Auditoria de consistência — Claude (gsd-code-reviewer), depth=deep._
_Nenhum arquivo de código foi alterado._
