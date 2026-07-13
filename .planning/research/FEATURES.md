# Feature Landscape — v2.4 Fidelidade do Valuation (Contrato de Saída)

**Domain:** Valuation de ações de dividendos B3 para PF, fiel ao método de *O Investidor em Ações de Dividendos* (Orleans Martins & Felipe Pontes)
**Researched:** 2026-07-13
**Confidence geral:** MEDIUM-HIGH (achado #1 = HIGH; padrões de mercado = HIGH; convenções BR = MEDIUM)
**Orçamento de busca:** 4 de 6 buscas usadas. As fontes de maior peso foram **internas** (as anotações de capítulo da própria engine, escritas por quem leu o livro).

---

## 0. ACHADO DE PRIMEIRA ORDEM — o livro NÃO prescreve preço-teto. Mas o marco continua de pé.

O quality gate pede que, se o livro contradiz a proposta do marco, isso vá no topo. Vai. Com uma ressalva
que salva o marco.

### 0.1 O que o livro prescreve (HIGH confidence)

Reconstruí o índice do livro a partir das anotações de capítulo da própria engine — escritas pelos
desenvolvedores que tinham o livro na mão, com **exemplos numéricos conferidos contra as tabelas do livro**.
É a fonte mais confiável disponível sem o PDF:

| Cap. | Conteúdo | Onde está no código |
|---|---|---|
| 6 | Armadilhas de dividendos | `report.py:494,646` |
| 8 | Garimpo / BSD de Carlson | `screening.py:1` |
| 10 | Múltiplos de lucros e dividendos | `multiples.py:1` |
| 11 | Ranking por múltiplos padronizados (Tabela 27) | `comparables.py:19` |
| 12 | Regressão P/L = f(payout, ROE) → **preço-alvo** | `comparables.py:68` — *confere CTEEP: P/L 14,18 × LPA 2,6256 → R$ 37,22* |
| 13, 15, 17 | **Modelo de Desconto de Dividendos (valor intrínseco)** | `ddm.py:1` — *confere Itaú, Tabela 41: DPA 2,362; g 10,24%; n=10* |
| 14 | Crescimento (g) | `growth.py:1` |
| 16 | CAPM / Ke | `capm.py:1` |

Confirmação externa (busca #1): a editora e a imprensa descrevem o livro como trazendo o **"passo a passo
do valuation de duas empresas (Itaú e Engie)"** — valuation, não regra de bolso. Felipe Pontes implementou
a estratégia do livro num fundo real, o *Dividendos Grandes e Seguros Multifatores FIA* — i.e. o **BSD do
Cap. 8 é o screen**, e o valuation é o DDM.

**Conclusão: o livro entrega VALOR INTRÍNSECO (DDM, Cap. 13–17) + PREÇO-ALVO RELATIVO (regressão, Cap. 12).
Não há preço-teto de Bazin em lugar nenhum do método.**

E o próprio repositório já sabia disso. O docstring de `core/lentes.py`, escrito pela equipe:

> "Fórmulas de referência **CLÁSSICAS, complementares ao método do livro** (o DDM/múltiplos continua sendo
> a análise principal). [...] Bazin (VAL-02): preço-teto = DPA médio ÷ DY-mínimo (6%)."

Bazin está explicitamente **fora** do método. `BAZIN_DY_MIN = 0.06` é uma constante herdada de Décio Bazin,
não dos autores.

### 0.2 Por que isso NÃO mata o marco (a distinção que resolve)

A contradição se dissolve quando se separam duas coisas que o brief funde:

| | O que é | O livro manda? |
|---|---|---|
| **O cálculo** | `V` = valor intrínseco (DDM/RIM) | **SIM.** É o método. Intocável. |
| **O contrato de saída** | Como exibir `V` e que rótulo de decisão pendurar nele | **NÃO.** O livro faz o valuation do Itaú e para. Não prescreve taxonomia de veredito de UI ("SOBREAVALIADA", "Evitar"). |

O livro não autoriza nem proíbe um preço-teto — ele simplesmente não fala do assunto, porque é um livro de
método, não de produto. Os rótulos "SOBREAVALIADA"/"Evitar"/"Qualidade Baixa" que estão no app hoje **também
não vêm do livro**. Foram invenção do produto. Não há uma saída canônica sendo abandonada.

**Portanto o v2.4 é fiel ao livro se — e somente se — o teto for DERIVADO do valor intrínseco do livro:**

```
P_teto = V_RIM × (1 − MS(incerteza))          ✅ Graham (margem de segurança) sobre o V do livro
P_teto = DPA / 0,06                            ❌ Bazin — regra de bolso, NÃO é o método do livro
```

**Esta é a linha vermelha do marco.** Se em algum momento da implementação o teto começar a sair de uma
meta de DY em vez de sair do `V`, o Core Value ("fiel ao método do livro") foi quebrado — mesmo que os
números fiquem mais bonitos. Bazin continua onde já está: **lente de triangulação** em `lentes.py`, rotulada
como não-livro.

> **Bônus de coerência:** o "DY esperado" que a casa de análise publica pode ser reconstruído sem violar nada:
> `DY_no_teto = DPA_recorrente / P_teto`. Isso dá ao investidor exatamente a intuição de Bazin ("que renda eu
> travo se comprar no teto?") **derivada do DDM do livro**, e não da regra de 6%. É a ponte honesta entre os
> dois mundos, de graça.

### 0.3 O corolário desconfortável (Q5)

A regressão do Cap. 11–12 **é do livro**. "Aposentar o Ranking" ao pé da letra significaria deletar dois
capítulos do método — o que viola o Core Value tanto quanto adotar Bazin. Ver §5: a saída correta é
**rebaixar e re-rotular**, não deletar. O defeito não está na regressão; está na **alegação** que penduraram
nela.

---

## 1. Table Stakes

Sem isso, o contrato de saída do v2.4 não fecha.

| # | Feature | Por que é esperado | Complexidade | Depende de |
|---|---|---|---|---|
| **T1** | **Preço-teto derivado do V**: `P_teto = V × (1 − MS)` | É o vernáculo do PF brasileiro (§1.1) e é a única forma de dar um gatilho acionável sem fingir precisão | **BAIXA** (aritmética) | Toda a cadeia v2.4 #1–#4 (V precisa estar sem viés) + T2 |
| **T2** | **Margem de segurança escalonada pela incerteza** (não fixa) | Padrão Morningstar (§2). MS fixa de 25% finge que todo ticker tem a mesma qualidade de dado | **MÉDIA** | T3 |
| **T3** | **Score de incerteza/confiança por ticker** | É o insumo do T2. Sem ele o MS vira knob arbitrário | **MÉDIA** | v2.4 #1 (asserts de reconciliação) |
| **T4** | **Viés binário (Comprar/Aguardar) derivado MECANICAMENTE do teto** | Um número, uma regra: `preço < teto → Comprar`, senão `Aguardar`. Se o viés puder discordar do teto, recria-se a inconsistência entre menus que é o pecado original do projeto | **BAIXA** | T1 |
| **T5** | **DY esperado + DY no teto** | A casa de análise publica; é a métrica nativa do público de dividendos; já temos DPA recorrente | **BAIXA** | — |
| **T6** | **Aposentar "Evitar" / "Qualidade Baixa" → "Aguardar"** | Método **e** jurídico (§6.3) | **BAIXA** (`selo.py`, rótulos) | — |
| **T7** | **Nunca suprimir o número: alargar a faixa + bandeira** | Ferramentas maduras alargam, não escondem (§3) | **MÉDIA** | T3 |

### 1.1 "Preço-teto" é table stakes de vocabulário no Brasil (MEDIUM-HIGH)

Busca #4 confirma: **"preço-teto" é o vernáculo dominante do varejo brasileiro.** O Investidor10 mantém
páginas de ranking inteiras ("Ações mais baratas segundo Bazin", "…segundo Graham"), artigos explicativos e
calculadoras dedicadas; existem calculadoras de terceiros só para isso. O PF brasileiro **já procura por
"preço-teto"** — o termo não precisa ser ensinado.

Isso é uma vantagem de adoção e uma armadilha de método ao mesmo tempo:
- ✅ **Adoção:** falar "preço-teto" alinha o produto ao vocabulário que o usuário já usa e busca (inclusive SEO).
- ⚠️ **Método:** o mercado associa "preço-teto" a **Bazin (DPA/6%)**. Se o app disser "preço-teto" e entregar
  `V × (1−MS)`, ele precisa **dizer de onde vem** — senão o usuário assume Bazin e o número parecerá "errado"
  contra o Investidor10. **Isso torna a ponte auditável (§4) não-opcional.** O rótulo pega carona no vocabulário;
  a ponte impede a confusão de método.

---

## 2. Margem de segurança — como dimensionar (Q2)

**HIGH confidence** (busca #2, metodologia oficial Morningstar).

Confirmado: a Morningstar **escala a margem de segurança pelo Uncertainty Rating**. Números exatos:

| Uncertainty | Desconto p/ 5 estrelas (comprar) | Prêmio p/ 1 estrela (vender) |
|---|---|---|
| Low | **−20%** | +25% |
| Medium | **−30%** | +35% |
| High | **−40%** | +55% |
| Very High | **−50%** | +75% |
| Extreme | **−75%** | +300% |

Três leituras não-óbvias, todas acionáveis:

1. **A MS não é uma opinião — é uma função da incerteza.** "25% fixo" (Graham puro) é o caso degenerado onde
   você finge que todos os tickers têm a mesma qualidade de dado. Num app cuja Doença 2 é *dispersão de dados
   por ticker*, MS fixa é ativamente errada: ela dá o mesmo benefício da dúvida ao ITUB4 (10 anos de CVM limpa)
   e ao CGRA4 (escala quebrada em 1.018×).

2. **A banda é ASSIMÉTRICA** (−20% para comprar vs. +25% para vender; −75% vs. +300% no extremo). Deliberado:
   a perda é limitada a −100% e o ganho é ilimitado, então exigir simetria seria matematicamente incoerente.
   **Se o v2.4 tiver um limiar de "Aguardar por caro", ele deve ficar mais LONGE do V do que o limiar de comprar.**

3. **A Morningstar publica o fair value PONTUAL *E* as bandas.** Isso refuta a generalização do brief
   ("Nunca um valor intrínseco pontual"). Aquilo é a convenção de **uma** casa brasileira, não uma lei do
   ofício. O padrão global maduro é **ambos**: o número (auditável) + a banda (que carrega a humildade).
   Esconder o `V` custaria a transparência que é o diferencial declarado do produto.

### 2.1 De onde tirar a incerteza (o insumo já existe, quase todo)

Nada aqui é pesquisa nova — é plumbing que o v2.2 já construiu:

| Sinal | Estado | Fonte |
|---|---|---|
| **Divergência do ensemble** (motor primário × contraponto DDM) | ✅ **JÁ EXISTE** — flag de >2× e `veredito_range` (ENS-01, `report.py:74`) | v2.2 |
| **Qualidade do dado** (asserts de reconciliação passaram?) | 🔨 v2.4 #1 vai construir os asserts | v2.4 |
| **Comprimento da série** (anos de CVM disponíveis) | ✅ existe (`ultimo_ano`, tabela de 10 anos) | v1.x |
| **Arquétipo** (banco/cíclica/crescimento/holding) | ✅ **JÁ EXISTE** — classificador v2.2 | v2.2 |
| **Volatilidade do lucro / ROE fora de faixa** | ✅ parcialmente (`normalizacao.py`) | v1.3 |

> **Alavancagem escondida:** os asserts de reconciliação do v2.4 #1 foram concebidos como *bug-catchers*
> (levantam exceção). **Se eles gravarem o resultado como DADO em vez de só levantar, viram de graça o score
> de confiança do T3.** Recomendação forte: os asserts devem **retornar um objeto de qualidade**, não só
> `assert`. Custo marginal ~zero, e destrava toda a escada T2→T1.
>
> Igualmente: **a divergência do ensemble já é uma medição de incerteza pronta.** Spread entre motores →
> bucket de incerteza → MS. O v2.2 construiu o termômetro sem saber; o v2.4 só precisa ligá-lo no MS.

### 2.2 ⚠️ A MS é um knob novo — e knobs novos foram o que matou o v2.3

**O risco mais sério deste marco, e ele não está listado nas três armadilhas do PROJECT.md.**

O `MS` é um parâmetro livre multiplicando o `V`. Se ele for **ajustado até os resultados ficarem bonitos**,
ele vira exatamente o que o `ke_teto: 0.13` era: uma muleta que compensa um viés a montante, com dois erros
se cancelando. O post-mortem do v2.3 (overfit sobre 4 observações com ~4 knobs) se repetiria num lugar novo.

**Regra dura proposta:**
> `MS` é função **exclusiva** da incerteza/qualidade do dado (uma tabela fixa, estilo Morningstar, escrita
> ANTES de ver os resultados). **Nunca** é calibrado contra dispersão, preço de mercado, nem contra
> quantos "Comprar" saem. Se o `V` estiver enviesado, o conserto é no `V` (v2.4 #1–#4) — jamais no `MS`.

Corolário de ordenação: **o contrato de saída (v2.4 #5) só pode ser calibrado DEPOIS do #4.** Isso já está
na ordem do marco; a razão é esta, e ela merece estar escrita.

---

## 3. Comunicar incerteza sem paralisar (Q3)

**Confidence: HIGH para Morningstar, MEDIUM para Simply Wall St, MEDIUM para BR.**

O que as maduras fazem, em ordem de qualidade:

| Ferramenta | Comportamento sob baixa confiança | Padrão |
|---|---|---|
| **Morningstar** | **Alarga a exigência.** "Extreme" não suprime o fair value — exige 75% de desconto para virar 5 estrelas. O número aparece; o *gatilho* é que fica quase inalcançável | **ALARGAR** ✅ |
| **Simply Wall St** | *Narratives*: amarra o fair value a premissas explícitas e mostra **"o que teria que ser verdade"** para a ação valer mais/menos. Usa 4 variantes de DCF conforme setor/disponibilidade de dado | **EXPLICITAR PREMISSA** ✅ |
| **AUVP** (do estudo interno) | Selo de 4 cores, e **admite no disclaimer** que ignora preço ("azul pode estar caro") | **BANDEIRA HONESTA** ✅ |
| **App hoje** | `motor_pendente` / `_guarda_faixa_ddm` → `faixa=None` → o selo **não estampa nada**. Usuário vê "indisponível" e um buraco | **SUPRIMIR** ❌ |

### O princípio (a recomendação central desta seção)

> **A incerteza deve mexer no LIMIAR, nunca na VISIBILIDADE.**

Alta incerteza → MS sobe → o teto **desce** → menos sinais de "Comprar". O sistema fica automaticamente mais
conservador onde sabe menos, **sem nunca deixar o usuário olhando para um buraco.** É auto-limitante,
honesto e não paralisa.

Isso é um **conserto direto do comportamento atual**: `_guarda_faixa_ddm` e a suspensão por `motor_pendente`
resolvem "não confio nesse número" com **silêncio**. Silêncio não é honestidade — é abdicação. O usuário fica
sem número *e* sem explicação. A substituição correta:

| Hoje | v2.4 |
|---|---|
| `faixa=None` → selo em branco → "indisponível" | Teto + **"Confiança: BAIXA — série de 4 anos, JCP ausente"** + MS alargada |
| Veredito suprimido quando `motor != "ddm"` | Veredito do motor do arquétipo, com bandeira de divergência |
| "SOBREAVALIADA" reetiquetado por `_guarda_san01` | Desnecessário: se o `V` está certo, a aberração não nasce |

Nota: **os guarda-corpos SAN-01/`_guarda_faixa_ddm` são cicatrizes do viés, não features.** Existem para
mascarar aberrações produzidas pela Doença 1 + Doença 2. Consertadas as doenças, **eles devem ser removidos,
não portados.** Mantê-los seria carregar a muleta para dentro da casa nova. (Mesmo raciocínio das três
armadilhas: dois erros se cancelando.)

---

## 4. A "ponte auditável" (Q4) — table stakes **para este produto**, nicho para os outros

**Veredito: é o MOAT. Não é um nice-to-have.**

Genericamente, decompor o valuation na tela é nicho — Investidor10/Status Invest mostram a fórmula num artigo,
não a derivação por ticker. Mas a pergunta certa não é "o mercado faz?", é "**o posicionamento declarado deste
produto exige?**". E o próprio estudo de mercado do projeto (`docs/estudo-mercado-interno.md`) responde:

> Diferenciais defensáveis reais: […] (c) **transparência — o app mostra as premissas (Ke, g, sensibilidade) e
> se autodiagnostica, em vez de cuspir um número caixa-preta.**

E, sobre o principal concorrente global: *"Simply Wall St: **DCF caixa-preta**"* — listado como **fraqueza dele**.

Se o v2.4 troca "valor intrínseco pontual" por "preço-teto" **sem** a ponte, o produto **vira exatamente o
caixa-preta que ele acusa o concorrente de ser** — e, pior, num vocabulário (preço-teto) que o mercado
associa a *outra* fórmula (Bazin, §1.1). A ponte é o que impede o v2.4 de destruir o diferencial do produto.

### 4.1 A ponte é um TESTE DE CORREÇÃO, não só uma feature de UI

Aqui está o argumento mais forte para priorizá-la, e ele é técnico, não de marketing.

```
P/B justo = 1 + (ROE_T − Ke) / (Ke − g)          →    V = P/B justo × VPA
```

Sob clean surplus, `g = ROE_T × (1 − payout_T)`, logo o modelo tem um **payout terminal implícito**:

```
payout_T = 1 − g / ROE_T
```

Isso não é decoração. É uma **afirmação falsificável que o modelo está fazendo em silêncio** e que hoje
ninguém audita:

| Cenário | ROE_T | g | payout_T implícito | Leitura |
|---|---|---|---|---|
| Banco de qualidade | 18% | 7,3% | **59%** | ✅ Plausível — o Itaú paga por aí |
| Empresa medíocre | 8% | 7,3% | **9%** | 🚩 Absurdo para uma ação de dividendos — e `(ROE_T − Ke) < 0` faz o modelo destruir valor no terminal |
| Qualquer | 10% | 12% | **−20%** | 🔴 **BUG.** Payout negativo = o modelo está inconsistente. Um assert deveria pegar |

**Expor o payout terminal implícito transforma a premissa mais perigosa do RIM (o valor terminal — a raiz do
v2.3 e a "alavanca" registrada na MEMORY) numa afirmação que o usuário pode rejeitar e que um teste pode
travar.** É simultaneamente:
- a **feature de transparência** (o usuário vê "o modelo assume que o Itaú pagará 62% na maturidade" e julga),
- o **guarda-corpo** que o SAN-01 tentou ser por fora, mas agora por dentro do método,
- e uma **fonte de golden tests honestos** (`0 < payout_T < 1` para todo ticker válido) — que é justamente o
  que faltou nos ~150 goldens que o marco vai reescrever.

**Recomendação: `payout_T` implícito vira campo de primeira classe da engine + assert de sanidade + linha na
UI.** Complexidade **MÉDIA**, retorno desproporcional.

### 4.2 Irmã gêmea barata: o "reverse DDM" (o que o preço de hoje está dizendo?)

A matriz de sensibilidade Ke×g **já existe** (`ddm.py:129`). Invertê-la — *"para o preço de hoje se justificar,
o Itaú teria que crescer a X% para sempre"* — é o análogo direto das *Narratives* do Simply Wall St, custa
quase nada, e é a forma mais honesta que existe de comunicar valuation: **em vez de o app dizer que o mercado
está errado, ele mostra no que o mercado está apostando** e deixa o usuário discordar.

Complexidade **BAIXA-MÉDIA** (solve for `g` dado `preço`). Diferenciador de alto valor percebido.

---

## 5. Ranking por regressão (Q5) — DEMOVER e RE-ROTULAR, não deletar

### 5.1 A cegueira ao nível de preço é PROVÁVEL — em uma linha de álgebra

O achado empírico ("multipliquei o preço das elétricas por 1,5 e os upsides saíram bit a bit idênticos") não é
coincidência nem bug. É **teorema**. Prova:

A regressão é `P/L_i ~ β₀ + β₁·payout_i + β₂·ROE_i`.

1. Multiplique todo preço por `k`. `LPA` não muda ⇒ **todo `P/L_i` observado escala por `k`**.
2. `payout` e `ROE` **não dependem de preço** ⇒ a matriz de regressores `X` é **idêntica**.
3. OLS é **linear em y**: `β̂ = (XᵀX)⁻¹Xᵀy`. Escalar `y` por `k` escala `β̂` por `k` ⇒ **`P/L_esperado` escala por `k`**.
4. `preço-alvo = P/L_esperado × LPA` ⇒ **escala por `k`**.
5. `upside = alvo/preço − 1` = `(k·alvo)/(k·preço) − 1` ⇒ **INVARIANTE.** ∎

Bit a bit idêntico, exatamente como observado. **Não há calibração que conserte isso** — é a natureza do
método, não um defeito da implementação.

### 5.2 O que isso significa (crítica padrão de Damodaran — MEDIUM-HIGH)

Valuation relativo embute a premissa: **"o mercado acerta na média e erra no indivíduo."** Ele só sabe dizer
"barato **em relação aos pares**". É **estruturalmente incapaz** de dizer "o setor inteiro está caro" — e é
justamente essa a pergunta que o v2.4 existe para responder (o app hoje diz "caro" para 4 de 5 ações; se o
setor todo estiver caro, a regressão **jamais** avisará).

Isso não é vergonha: é a **definição** de múltiplo relativo. A desonestidade não está na regressão — está em
chamar o output de **"preço-alvo"** e **"upside"**, palavras que prometem uma alegação absoluta que o método
não pode sustentar.

### 5.3 O contrato honesto para a tela de comparar/ranquear

**Não deletar** (seria jogar fora os Cap. 11–12, violando o Core Value tanto quanto adotar Bazin). **Rebaixar
de VALUATION para SCREENER**, que é o que ele sempre foi:

| Hoje (desonesto) | v2.4 (honesto) |
|---|---|
| "Preço-alvo: R$ 37,22" | "Posição relativa aos pares: **+18% acima da linha do setor**" (resíduo da regressão) |
| "Upside: +34%" | "Percentil no setor: **12º de 40** (barato *vs. pares*)" |
| "Veredito: Subavaliada" | "🔎 **Triagem relativa.** Assume que o setor está corretamente precificado. **Não é valuation.** Confirme no motor primário." |
| Ranking como resposta | Ranking como **funil**: regressão triaga → RIM valua → teto decide |

O `comparables.py:74` **já confessa** a fragilidade (`"o veredito Subavaliada/Cara não deve ser lido com
confiança (AUD-CMP-02)"`). O v2.4 só precisa promover essa confissão de comentário a **contrato de UI**.

**Complexidade: MÉDIA** (renomear campos, remover a alegação absoluta, expor o resíduo). **Preserva a
fidelidade ao livro**: o Cap. 12 continua rodando; muda o que se *alega* sobre ele.

> Nota de fidelidade: o próprio exemplo do livro (CTEEP → R$ 37,22) é um alvo **relativo**. Rotulá-lo como tal
> não contradiz o livro — **corrige uma leitura excessivamente literal** que o produto fez dele.

---

## 6. Anti-features — o que NÃO fazer

| # | Anti-feature | Por que evitar | O que fazer em vez |
|---|---|---|---|
| **A1** | **Mirar a dispersão de ~24% das casas** | §6.1 — é o mais perigoso do marco | Dispersão é **output**, nunca **alvo** |
| **A2** | Preço-teto por Bazin (`DPA/0,06`) | Não é o método do livro (§0) | `V × (1 − MS)` |
| **A3** | Manter "Evitar" / "Qualidade Baixa" | Método **e** risco CVM (§6.3) | "Aguardar" / "Acima do preço-teto" |
| **A4** | Suprimir o número sob baixa confiança | Abdicação disfarçada de prudência (§3) | Alargar a MS + bandeira explícita |
| **A5** | Portar SAN-01 / `_guarda_faixa_ddm` para o v2.4 | São cicatrizes do viés; consertadas as doenças, viram um segundo erro cancelando o primeiro | Remover. Se a aberração voltar, é bug de `V` |
| **A6** | Viés binário calculado por regra própria | Se o viés puder discordar do teto, recria a inconsistência entre menus = o **pecado original** do projeto | Viés é `preço < teto`, e nada mais |
| **A7** | Um terceiro estado ("Comprar forte") | Granularidade convida knob-fitting e finge precisão | Binário + o número do teto já é completo |
| **A8** | Calibrar para "sair mais Comprar" | §6.2 | Se o mercado estiver caro depois do conserto, **essa é a resposta** |
| **A9** | Duas casas decimais no `V` (R$ 32,88) | Precisão falsa sobre uma banda de ±40% | Teto arredondado + banda visível |

### 6.1 A armadilha da dispersão (a mais séria — o brief está certo, e eis o porquê)

O brief pede para não copiar a dispersão de ~24% das casas. **Correto, e é a recomendação mais importante
deste documento depois do §0.** O mecanismo:

Preços-alvo de sell-side são **notoriamente ancorados no preço corrente** (anchoring bias bem documentado:
analistas revisam o alvo *em direção ao preço*, não o contrário). A dispersão apertada delas é **sintoma da
ancoragem, não evidência de acurácia**. Elas não estão acertando mais — estão **chutando mais perto de onde a
bola já está**.

Logo, se o v2.4 ajustar knobs até reproduzir ±24%:

> Você terá construído um jeito caríssimo, com 448 testes e quatro motores, de imprimir
> **"o preço de hoje, ± 24%"** — que carrega **informação zero**. E terá destruído a única razão de a
> ferramenta existir: **enxergar uma assimetria de 60% quando ela existe.**

Isso é a **mesma classe de erro** do post-mortem do v2.3 (calibrar contra 4 observações), mas mais insidioso,
porque o alvo (`dispersão parecida com a dos profissionais`) *parece* validação externa. **Não é. É importação
de viés.**

O `PROJECT.md` já blinda isso na feature #6 (*"Métrica: `V/FairValue`, nunca `V/preço`"*). **Isso não é um
detalhe do harness — é a defesa central do marco, e vai ser testada sob pressão**, porque a pressão social de
"nosso número não parece com o dos profissionais" é real e constante.

**Uso legítimo dos números das casas — exatamente um:** *falsificação pontual*, nunca ajuste.
- Modelo diz −81% numa blue chip de dado limpo → **caça ao bug**.
- Modelo diz −40% depois do dado limpo e da identidade do `g` fechada → **isso é uma posição**, não um erro. Publique.

### 6.2 Não otimizar a taxa de "Comprar"

A dor declarada ("diz caro para 4 de cada 5") descreve um **sintoma**. A causa é o erro de unidade
(Ke nominal × g real). O conserto é a **identidade da inflação** (v2.4 #4) — não uma meta de quantos sinais
verdes aparecem. "Quantos Comprar saíram?" é uma métrica **sedutora e corruptora**: ela transforma qualquer
knob num botão de "deixar o cliente feliz". Bani-la explicitamente do harness.

### 6.3 "Aguardar" em vez de "Evitar" é redução de risco jurídico, não gentileza

O produto é vendido (Lazari Capital, R$ 19,90/mês) e posicionado como **"software educacional, sem
recomendação de investimento"**. O estudo interno já sinaliza a exposição à **CVM Res. 19/20** (análise de
valores mobiliários é atividade regulada) e diz: *"vender 'preço-alvo/veredito' pago flerta com análise de
valores mobiliários regulada"*.

"**Evitar**" e "**Qualidade Baixa**" são **juízos de valor sobre a empresa** — o registro linguístico de uma
recomendação. "**Aguardar**"/"**Acima do preço-teto**" é uma **afirmação sobre o preço vs. um modelo
transparente**, que é precisamente o que um software educacional pode dizer. A mudança do T6 **reduz
simultaneamente o risco de método e o risco regulatório** — e ainda vira argumento de venda ("mostramos o
modelo, você decide").

---

## 7. Diferenciadores

| # | Feature | Proposta de valor | Complexidade | Nota |
|---|---|---|---|---|
| **D1** | **Ponte auditável + payout terminal implícito** | **O MOAT.** Nenhum concorrente BR mostra a derivação; o SWS é caixa-preta (fraqueza dele no estudo). E é um **teste de correção** (§4.1) | **MÉDIA** | Prioridade máxima entre os diferenciadores |
| **D2** | **Reverse DDM** ("o que o preço de hoje assume") | Análogo às *Narratives* do SWS. Mostra no que o mercado aposta em vez de decretar que ele erra. **A matriz Ke×g já existe** | **BAIXA-MÉDIA** | Melhor razão valor/esforço do marco |
| **D3** | **Bazin/Graham como lente de triangulação** | Fala o vocabulário do usuário (§1.1) **sem** contaminar o método | **ZERO — já existe** (`lentes.py`) | Só re-rotular: "referência clássica, não é o método do livro" |
| **D4** | **DY no teto** (`DPA_recorrente / P_teto`) | "Que renda você trava comprando no teto" — a intuição de Bazin, derivada do DDM do livro | **BAIXA** | Ponte honesta entre os dois mundos |
| **D5** | **Confiança visível por ticker** | Ninguém no BR mostra qualidade de dado. É o subproduto natural dos asserts do v2.4 #1 | **MÉDIA** | Cai de graça do T3 |

---

## 8. Dependências

```
v2.4 #1 (reconciliação)  ──┬─→ [asserts como DADO] ──→ T3 (score de confiança) ──→ T2 (MS escalonada) ──┐
v2.4 #2 (ingestão)       ──┤                                                                             │
v2.4 #3 (primitivas)     ──┤                                                                             ├─→ T1 (preço-teto) ──→ T4 (viés binário)
v2.4 #4 (g → Ke)         ──┴─→ [V sem viés] ─────────────────────────────────────────────────────────────┘                          │
                                    │                                                                                                │
                                    ├─→ D1 (ponte auditável / payout_T)  ←── também vira ASSERT de sanidade                          │
                                    ├─→ D2 (reverse DDM)                                                                             │
                                    └─→ T5 / D4 (DY esperado / DY no teto) ──────────────────────────────────────────────────────────┘

v2.2 (ensemble/divergência)  ──→ T3   [termômetro de incerteza JÁ PRONTO — só ligar]
v2.2 (classificador)         ──→ T3

INDEPENDENTES (podem ir a qualquer momento):
  T6 (Evitar → Aguardar)        — rótulos + selo.py
  A1/§5 (rebaixar o Ranking)    — renomear campos + remover alegação absoluta
```

**A regra de ordenação que não pode ser violada:**

> **Nenhum parâmetro do contrato de saída (`MS`, limiares do teto) pode ser tocado antes do v2.4 #4 estar
> fechado.** O `MS` multiplica o `V`; calibrá-lo sobre um `V` enviesado o transforma num novo `ke_teto` — uma
> muleta compensando um viés a montante. Seria o post-mortem do v2.3 se repetindo num endereço novo.

---

## 9. Recomendação de MVP do contrato de saída

**Entregar junto (é um contrato, não um menu):**
1. **T1** preço-teto = `V × (1 − MS)` — derivado do RIM, **jamais** de Bazin
2. **T2 + T3** MS escalonada por incerteza (tabela fixa estilo Morningstar, escrita ANTES de ver resultados)
3. **T4** viés binário mecânico (`preço < teto`)
4. **D1** ponte auditável com **payout terminal implícito** — sem ela o produto vira o caixa-preta que critica
5. **T6** "Aguardar" no lugar de "Evitar" (método + jurídico)
6. **T7** alargar em vez de suprimir; **remover** SAN-01/`_guarda_faixa_ddm` (A5)

**Segunda onda (barato, alto valor):** D2 (reverse DDM) · T5/D4 (DY esperado / no teto) · D5 (confiança visível)

**Adiar:** re-rotulagem do Ranking (§5) — independente, não bloqueia, e o valor aparece melhor depois que o
motor absoluto estiver confiável para receber o funil de triagem.

---

## 10. Confiança e lacunas

| Área | Confiança | Base |
|---|---|---|
| **O livro prescreve valor intrínseco, não preço-teto (§0)** | **HIGH** | Anotações de capítulo da engine com exemplos numéricos conferidos (Itaú Tab. 41, CTEEP Cap. 12) + docstring de `lentes.py` ("complementares ao método do livro") + descrição editorial ("passo a passo do valuation de Itaú e Engie") |
| Escala de MS da Morningstar (§2) | **HIGH** | Metodologia oficial; números exatos por bucket |
| Cegueira da regressão ao nível de preço (§5.1) | **HIGH** | Prova algébrica (equivariância do OLS) + replicação empírica do usuário |
| "Preço-teto" é o vernáculo BR (§1.1) | **MEDIUM-HIGH** | Investidor10 (rankings, artigos, calculadoras dedicadas) |
| Simply Wall St sob baixa confiança (§3) | **MEDIUM** | *Narratives* e "4 variantes de DCF conforme disponibilidade de dado" confirmados; comportamento exato de dado faltante **não** confirmado |
| Ancoragem de sell-side (§6.1) | **MEDIUM-HIGH** | Literatura acadêmica consolidada; não re-verificado nesta rodada (orçamento) |
| Status Invest sob baixa confiança | **LOW** | Não investigado (orçamento). Não bloqueia — o padrão "alargar" já está estabelecido por Morningstar/SWS |

### Lacunas honestas

1. **Não li o livro.** A reconstrução do §0 vem das anotações da engine — fonte forte (escrita com o livro na
   mão, com exemplos numéricos que *conferem* contra as tabelas), mas **indireta**. Um `grep` no PDF por
   "preço-teto"/"Bazin"/"margem de segurança" fecharia isso em 5 minutos e **vale a pena antes de commitar o
   contrato de saída** — é a única premissa da qual todo o resto depende.
2. **O livro prescreve alguma margem de segurança?** Não sei. Ele calcula `V` para o Itaú (Tab. 41), mas se ele
   dá uma regra de decisão ("compre X% abaixo"), essa regra **tem precedência** sobre a tabela da Morningstar
   por fidelidade. **Segunda coisa a procurar no PDF.**
3. **`ROE_T` e `g_cap` terminais** — a §4.1 assume `g_cap ≈ 7,3%` (do PROJECT.md). A escolha do `ROE_T`
   (through-cycle? histórico? setorial?) é decisão de método ainda em aberto e **é a premissa que mais move o
   valor terminal** — logo a que mais precisa aparecer na ponte auditável (D1).

---

## Sources

- [Morningstar — An Introduction to the Uncertainty Rating](https://www.morningstar.com/stocks/an-introduction-morningstar-uncertainty-rating) — escala MS↔incerteza (HIGH)
- [Morningstar — Uncertainty Rating Methodology Update (PDF)](https://advisor.morningstar.com/Enterprise/VTC/URFAQ.pdf) — descontos/prêmios por bucket (HIGH)
- [Morningstar — Equity Research Methodology (PDF)](https://www.morningstar.com/content/dam/marketing/shared/research/methodology/705988Morningstar_Equity_Research_Methodology.pdf) (HIGH)
- [Simply Wall St — Understanding the Valuation section](https://support.simplywall.st/hc/en-us/articles/4751563581071-Understanding-the-Valuation-section-in-the-company-report) — 4 variantes de DCF, *Narratives* (MEDIUM)
- [Editora Sextante — O investidor em ações de dividendos](https://sextante.com.br/products/o-investidor-em-acoes-de-dividendos) — "passo a passo do valuation de duas empresas" (MEDIUM-HIGH)
- [Amazon.com.br — ficha do livro](https://www.amazon.com.br/investidor-em-a%C3%A7%C3%B5es-dividendos/dp/8543110726) (MEDIUM)
- [Investidor10 — Preço Justo: Graham x Bazin](https://investidor10.com.br/conteudo/preco-justo-das-acoes-metodo-bazin/) — vernáculo BR de "preço-teto" (MEDIUM-HIGH)
- [Investidor10 — Método Bazin](https://investidor10.com.br/conteudo/metodo-bazin/) — `DPA / 0,06` (MEDIUM-HIGH)
- **Internas (HIGH):** `src/analista/core/lentes.py` (Bazin/Graham = "complementares ao método do livro") · `core/ddm.py:1,8` (Cap. 13-17, Itaú Tab. 41) · `core/comparables.py:1,68,74,190` (Cap. 11-12, CTEEP, confissão AUD-CMP-02) · `core/capm.py`, `growth.py`, `screening.py`, `multiples.py` (mapa de capítulos) · `report/report.py:74,111-177` (SAN-01, guarda-corpos) · `docs/estudo-mercado-interno.md` (transparência = diferencial declarado; CVM Res. 19/20) · `.planning/PROJECT.md` (doenças 1 e 2, três armadilhas)
