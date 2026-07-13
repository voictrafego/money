# Arquitetura — v2.4 Fidelidade do Valuation

**Domínio:** colapso dos 4 motores em um modelo, contrato de saída auditável, ordem de build
**Researched:** 2026-07-13
**Confiança geral:** MEDIUM-HIGH (álgebra e ordem de build HIGH; materialidade de dirty surplus no Brasil e prazo de concessão NÃO medidos — sinalizados abaixo)

---

## Headline

**A tese do RIM universal se confirma — mas NÃO pelo motivo que você listou como (c), e o motivo (c) como enunciado é FALSO.** Confirmar (a) e (b); descartar (c) e substituí-lo por um argumento melhor.

E há um argumento que você não listou e que é o mais forte de todos:

> **Sob clean surplus, os 4 motores não são 4 opiniões — são 4 implementações do MESMO modelo com inputs inconsistentes.** A dispersão medida (rim 0,81 · dcf 0,63 · normalizado 0,63 · ddm 0,48) **não é incerteza econômica; é a assinatura de bugs de implementação.** Logo o `ENS-01` (bandeira de divergência motor×contraponto, `comparables.LIMIAR_DIVERGENCIA = 2×`) está **medindo os próprios bugs do projeto e chamando isso de "divergência de método".** Isso condena o ensemble, não só os motores.

---

## 1. A tese central: RIM ≡ DDM ≡ DCF-equity

### VERDADEIRO — mas as condições importam

Derivação (Ohlson 1995; Penman, *Financial Statement Analysis and Security Valuation*, cap. 5-6):

```
DDM:            V0 = Σ_{t=1..∞} D_t / (1+Ke)^t
Clean surplus:  B_t = B_{t-1} + E_t − D_t     ⟹   D_t = E_t − (B_t − B_{t-1})
Substituindo e telescopando:
RIM:            V0 = B_0 + Σ_{t=1..∞} (E_t − Ke·B_{t-1}) / (1+Ke)^t
                   = B_0 + Σ RI_t / (1+Ke)^t
```

**Condições EXATAS de equivalência (todas necessárias):**

| # | Condição | Consequência prática no projeto |
|---|----------|-------------------------------|
| C1 | **Clean surplus (CSR)** vale em todo `t`: ΔB = E − D | Furado por OCI/IFRS → §2 |
| C2 | **Horizonte infinito**, ou valores terminais mutuamente consistentes | Truncar é onde os modelos *deixam* de concordar — e é onde o RIM ganha (§1a) |
| C3 | **Transversalidade**: `lim_{T→∞} B_T/(1+Ke)^T = 0` (o book não cresce mais rápido que Ke) | O guarda `ke_g_spread_min` do `motores.rim` É esta condição. Vira load-bearing quando o `g` subir (§1a) |
| C4 | DCF≡DDM exige **cash conservation** (FCFE ≡ D): sem emissão/recompra a preço ≠ justo, sobra financeira distribuída | É por isso que "consertar `dcf_crescimento` com FCFE = lpa×payout" **vira DDM** (WEGE3 0,58→0,26). Não é bug — é o teorema funcionando |

Fonte da equivalência com valores terminais: Lundholm & O'Keefe / Penman — *"the intrinsic values coincide as long as the clean surplus relation holds"*; com terminal values não-baseados em preço, o **RIM domina empiricamente**.

### (a) "RIM tem menor sensibilidade ao valor terminal" — **CONFIRMADO, com uma armadilha que vai te morder na Fase do `g`**

O valor não muda; muda **onde o valor mora**. Sob RIM, `B_0` — um número que você **observou**, não projetou — carrega uma fatia grande de `V`, então o erro de truncamento se dilui.

Evidência dura (Penman & Sougiannis, horizonte t+4, sem crescimento no terminal — viés absoluto):

| Modelo | Viés |
|--------|------|
| **RIM** | **8,3%** |
| DDM | 31,4% |
| DCF | **111,2%** |

Isso não é uma propriedade mágica do RIM. É uma propriedade de **erro de truncamento**: a equivalência vale no infinito, e o RIM vence porque forecasts reais são truncados e ele adianta valor para um número já observado.

**⚠️ ARMADILHA — a propriedade se DEGRADA exatamente quando você conserta o `g`.**
O `motores.rim` atual põe uma **perpetuidade de Gordon sobre um RI positivo** (`excesso_sustentavel: 0.045`, `g_terminal: 0.025`). RI perpétuo positivo = ROE em excesso **eterno** = a mesma perpetuidade explosiva que faz o DDM estourar, só que embrulhada.

Aritmética do que vai acontecer:

```
Hoje:            Ke ≈ 13,0%  ·  g_terminal = 2,5%   →  spread = 10,5pp
Pós-conserto:    Ke ≈ 13,0%  ·  g_cap      = 7,3%   →  spread =  5,5pp
Multiplicador do terminal: 1/spread  →  9,5×  vira  18,2×   (≈ 1,9× mais pesado)
```

**O peso do valor terminal no RIM praticamente DOBRA no momento em que o `g` for corrigido.** Os guardas `excesso_sustentavel` e `ke_g_spread_min`, hoje decorativos (o clamp do Ke absorve tudo), viram **load-bearing**. Isso precisa estar no plano da fase do `g`, não ser descoberto nela.

Penman é explícito: **lucro econômico tem que desaparecer** — a competição empurra o RI a zero. Um RI **permanentemente positivo** é a afirmação de um moat permanente. Defensável para o Itaú; indefensável como default global.

> **Recomendação:** `excesso_sustentavel` deve ser uma **constante pequena, dura e não-tunável** (ou zero fora do arquétipo com moat). Como knob calibrável ele é um **4º grau de liberdade** — e o `STACK.md` fixa o orçamento em **3**.

### (b) "Erro de Ke é menos alavancado no RIM" — **CONFIRMADO, e é o argumento mais forte para este projeto especificamente**

Gordon, sensibilidade a 1pp de erro no Ke:

```
dV/V  ≈  −1/(Ke − g)
Ke = 13%, g = 7,3%  →  −17,5% de valor por 1pp de Ke errado.
```

Brutal. E o `Ke` deste projeto é um número **fabricado**: Selic-ciclo (proxy) + ERP arbitrado + beta de 60 meses (ruidoso) + um clamp que o `STACK.md` provou ser *aritmeticamente falso* na justificativa.

Sob RIM, `B_0` é **invariante ao Ke**. Só o fluxo de RI responde — e responde com duplo sinal (Ke maior derruba o numerador `(ROE−Ke)·B` **e** o denominador). A sensibilidade cai aproximadamente na proporção `(1 − B_0/V)`:

| P/B justo | Fatia do valor exposta ao erro de Ke |
|-----------|--------------------------------------|
| 1,0× | ~0% |
| 1,5× | ~33% |
| 2,0× | ~50% |

**Colocar o input menos confiável na posição menos alavancada é a decisão arquitetural certa.** Confirmado sem ressalva.

### (c) "RIM tem teto estrutural de P/B → incapaz de produzir a aberração de 921× (CGRA4)" — **FALSO COMO ENUNCIADO. NÃO CONSTRUA NADA EM CIMA DISSO.**

O bug do CGRA4 é **escala de `num_acoes` (~1000×)**. Todo número *por ação* é `X / num_acoes`:

```
DPA = dividendos / num_acoes   →  1000× inflado   →  DDM (V ∝ DPA)  →  1000× inflado
VPA = PL         / num_acoes   →  1000× inflado   →  RIM (V = VPA × P/B_justo) → 1000× inflado
```

**O RIM herda o erro de escala 1:1, com um P/B justo perfeitamente razoável de 1,4×.** O que é limitado é o **P/B**, não o **V**. O RIM não é imune a um VPA errado — ele é imune a um *ratio* errado, porque `ROE`, `payout` e `retenção` são adimensionais. O CGRA4 não é um bug de ratio; é um bug de escala. **Refutado.**

**O que (c) DE FATO compra — e é valioso, só que é outra coisa:**

> O RIM produz um **intermediário adimensional e auditável**. `P/B justo = 921` é obviamente absurdo para um humano E para um `assert`. `V = R$ 12.400 vs preço R$ 13,50` não *parece* bug de dado — parece uma tese de valuation agressiva.

**O RIM torna a aberração LEGÍVEL; não a torna IMPOSSÍVEL.** A guarda é um assert sobre o P/B justo, não o RIM em si:

```python
# core/veredito.py — a guarda que substitui _guarda_san01
if not (0 < pb_justo < PB_JUSTO_MAX):   # ~6×
    → sem preço-teto; flag "escala do dado suspeita"
```

Isto **substitui** o `_guarda_san01` (report.py:108) por algo dimensional e verificável, em vez de um pattern-match em string de veredito.

### Veredito sobre Q1

**SIM, colapsar em UM motor (RIM).** Justificado por (a) + (b) + o argumento das "4 implementações de 1 modelo". **NÃO por (c).** Com três carve-outs (§3) e uma reformulação do papel do classificador:

> **Os 4 motores não são 4 modelos. São UM modelo (RIM) com uma POLÍTICA DE INPUT dependente do arquétipo.**

| Arquétipo | Modelo | O que o arquétipo realmente muda |
|-----------|--------|----------------------------------|
| `financeira` | RIM | `ROE_0` = ROE through-cycle (mediana 10a); `n_fade` = 10 |
| `ciclica` | RIM | `ROE_0` = `LPA_normalizado / VPA` (ROE de meio-de-ciclo). **`lucro_normalizado` não é um motor — é uma escolha de input** |
| `crescimento` | RIM | `ROE_0` = ROE corrente; `excesso_sustentavel` maior; `n_fade` maior. **`dcf_crescimento` é deletado (double-count provado)** |
| `holding` | RIM | `excesso_sustentavel = 0` → `V` colapsa em `B_0`. **`nav_contabil` É o 1º termo do RIM, não um motor** |
| `pagadora_regulada` | **CARVE-OUT — não é RIM** | §3 |

**Consequência boa e não-óbvia:** o classificador de arquétipo **sobrevive e ganha um papel mais defensável**. Ele deixa de escolher um *modelo* (erro **ilimitado**: motor errado → divergência de 2×) e passa a escolher uma *âncora de ROE* (erro **limitado**: âncora errada → alguns pp de ROE). Um misroute do classificador deixa de ser catastrófico. Isso é uma melhoria arquitetural gratuita.

**Consequência ruim para o `ENS-01`:** duas parametrizações da mesma identidade **não podem discordar legitimamente**. A bandeira de divergência perde o significado e deve ser **aposentada**. Substituto honesto: **banda de incerteza de INPUT** — rodar o RIM em `ROE_p25 / ROE_mediana / ROE_p75` da série de 10 anos. A largura dessa banda significa alguma coisa (incerteza sobre o poder de lucro); a largura da banda atual significa "nossos quatro códigos discordam".

---

## 2. Onde o clean surplus FURA

### Teoria: HIGH — furam **todos** os itens de OCI

> *"Clean surplus accounting is violated if non-owner related transactions are recognized directly in equity rather than in earnings — which is true for ALL items recognized in OCI. This invalidates a residual income valuation. The problem exists irrespective of whether OCI is recycled to P&L."*

Itens materiais em bancos e utilities brasileiros (CPC/IFRS):

| Item | Norma | Onde dói |
|------|-------|----------|
| **MTM de títulos a valor justo (FVOCI/AFS)** | CPC 48 / IFRS 9 | **Bancos — grande.** Carteiras de dezenas de bilhões; num ano de choque de juros a variação de OCI rivaliza com o lucro |
| **Hedge accounting (reserva de hedge de fluxo de caixa)** | CPC 48 | Bancos e utilities com dívida em USD |
| **Conversão cambial (CTA)** | CPC 02 / IAS 21 | ITUB4 (LatAm), exportadoras |
| **Remensuração de planos de pensão** | CPC 33 / IAS 19 | **BBAS3 (Previ), Petrobras (Petros) — notoriamente enorme e lumpy** |
| **Dirty surplus fora do OCI** | — | Recompra/tesouraria, emissão fora do book, ajustes de transição, **reapresentações de exercícios anteriores** — batem no B sem passar pelo E |

### Materialidade no Brasil: **MEDIUM — não medido, e o ponto crítico é OUTRO**

Evidência internacional (Isidro, O'Hanlon & Young, *Accounting and Business Research* 2004, "Dirty surplus accounting flows: international evidence"): **"little evidence to suggest that omission of dirty surplus flows would have caused SYSTEMATIC valuation errors."**

> **A distinção que decide o escopo do marco: dirty surplus é um problema de VARIÂNCIA, não de VIÉS.** A Doença 1 é um viés de −30%. **Consertar clean surplus NÃO conserta a Doença 1. Não gaste o marco nisso.**

### Mas a mitigação que você propôs é quase de graça, e é estritamente melhor — **ADOTAR**

Sim: **use o ΔBook REALIZADO da DFP no histórico; só assuma `B_t = B_{t-1}(1+ROE·b)` no HORIZONTE PROJETADO.**

Arquitetura correta:

**Histórico (`t ≤ 0`) — LER, nunca derivar.** `B_0 = PL da última DFP / num_acoes` (já é o que o app faz).

**Âncora de ROE through-cycle — trocar por um ROE que FORÇA clean surplus por construção:**

```
ROE_CSR_t = (PL_t − PL_{t−1} + Dividendos_t + JCP_t − Aumentos_de_capital_t) / PL_{t−1}
```

Isto é o **resultado abrangente implícito no balanço**. Captura OCI, tesouraria, reapresentação — *tudo* — porque é derivado exatamente da grandeza que o modelo consome (`ΔB`). Custa ~15 linhas em `fundamentals.py`.

**E ele ataca as duas doenças ao mesmo tempo — é também uma RECONCILIAÇÃO:**

```
se |ROE_CSR_t − LL_t/PL_{t−1}| > X pp:
    → ou é um ano genuíno de dirty surplus (informação),
    → ou é um BUG DE DADO (informação melhor ainda).
Nos dois casos você quer saber.  → 5º ASSERT do pipeline de reconciliação.
```

**Custo/risco: VERIFICADO — a DMPL é praticamente DE GRAÇA. Isto sobe a recomendação de "adotar" para "adotar sem hesitar".**

`ROE_CSR` precisa de `aumentos/reduções de capital` e recompras, que vivem na **DMPL** (Demonstração das Mutações do PL). Checagem no código:

- `cvm.py:23` — o ZIP já baixado e cacheado é `dfp_cia_aberta_{ano}.zip`, **que já contém `DMPL_con` e `DMPL_ind`** ao lado de BPA/BPP/DRE/DFC.
- `cvm.py:74` — `_ler_demonstracao(ano, prefixo)` é **totalmente genérica**: monta `dfp_cia_aberta_{prefixo}_{ano}.csv` e lê do ZIP em cache. `cvm.py:206` já itera prefixos (`DFC_MI_con`, `DFC_MD_con`, ...) exatamente com esse padrão.

> **Custo real da DMPL: uma string de prefixo nova.** Zero download novo, zero HTTP novo, zero cache novo, zero dependência nova. **Não é superfície nova de ingestão** — é o mesmo ZIP, o mesmo leitor, o mesmo `lru_cache`.

Logo: **implemente a versão COMPLETA do `ROE_CSR` (com eventos de capital), não a de 80%.** A versão degradada (`ROE_CSR ≈ (ΔPL + proventos)/PL_{t−1}`, ignorando eventos de capital) fica só como *fallback never-raise* quando a DMPL de um ano/empresa não resolver — mantendo o contrato de degradação graciosa do `ingest/`.

**Tarefa de medição barata para a fase (20 linhas, resolve o MEDIUM):** rodar `(ΔPL + proventos)/LL − 1` na série de 10a dos 104 tickers. **Esse número É a materialidade do dirty surplus no seu universo.** Meça antes de decidir quanto investir.

---

## 3. Carve-out das concessões de prazo determinado

**Você está certo — e é PIOR do que você pensa, por um segundo motivo, contábil.**

### Problema A — vida finita (o que você já sabe)

Concessão de transmissão é um contrato de ~30 anos que amortiza a ~zero. **Não há perpetuidade.** Gordon (`1/(Ke−g)`) implica vida infinita. E há um corolário que muda a leitura do produto:

> **Numa transmissora, payout alto NÃO é sinal de negócio maduro e excelente — é AMORTIZAÇÃO.** Parte do dividendo é **retorno DE capital**, não retorno SOBRE capital. Todo o método do livro (payout sustentável, DY recorrente, BSD) lê isso ao contrário.

O DDM atual é *menos errado* que um RIM-perpétuo nelas — **mas só por acidente**: um `Ke−g` grande trunca a cauda por sorte. Consertar o `g` (spread 10,5pp → 5,5pp) **destrói esse acidente**. As transmissoras vão ficar visivelmente mais caras/erradas na Fase do `g`. **Antecipe isso no plano.**

### Problema B — a contabilidade JÁ contém a resposta, e o app está lendo errado (CONFIRMADO)

Sob **ICPC 01 / IFRIC 12**, as transmissoras brasileiras adotam o **modelo de ATIVO FINANCEIRO** — a concessão está no balanço como ativo de contrato ao **custo amortizado com TIR embutida**. (Confirmação forte: a TAESA publica uma *"Nota Técnica: Práticas Contábeis — IFRS × Regulatório"* justamente porque os dois divergem materialmente. Empresas de energia no Brasil mantêm **três** escriturações: societária/IFRS, fiscal e **regulatória**.)

Três consequências que quebram o pipeline atual:

1. **O "lucro líquido" IFRS de uma transmissora não é lucro de caixa.** É `remuneração do ativo de contrato + receita de construção + remensuração por IPCA do ativo`. As empresas reportam **"lucro regulatório"** à parte — **e os dividendos são pagos do resultado regulatório, não do IFRS.**
2. **O ROE = LL_IFRS/PL de uma transmissora é LIXO.** A remensuração inflacionária do ativo de contrato passa pelo P&L → **o ROE dispara em anos de IPCA alto.** Alimentar isso em qualquer motor é garbage-in. (E note o efeito perverso: consertar o `g` para ser inflação-consistente vai interagir com um ROE que *já* é inflação-contaminado nessas empresas → **double-count de inflação**.)
3. **O book de uma transmissora JÁ É, por definição, ≈ o VP da RAP remanescente** — é o que "ativo financeiro ao custo amortizado" significa. Logo **`P/B ≈ 1` é a resposta teoricamente correta** para uma transmissora pura sem crescimento, e o residual income deveria ser ≈ 0 por construção. O RI que o RIM produzir nelas é o gap entre **a WACC da ANEEL e o seu CAPM** — o que é interessante! — mas **não** é "excesso de ROE que faz fade em 10 anos e depois persiste eternamente a 4,5pp".

### Tratamento defensável com dado gratuito — ranqueado

**1. MELHOR-E-BARATO — tirar do pipeline de valor intrínseco e entregar YIELD com aviso de vida finita.**
Saída honesta para `pagadora_regulada`: *"DY corrente vs. NTN-B real + prazo médio remanescente da concessão"*, **sem preço-teto**. É defensável, é barato e **não mente**. Coerente com o ethos do projeto (o classificador já devolve `fronteirico` em vez de fingir certeza).

**2. BOM E VIÁVEL — anuidade de RAP (Gordon truncado).**
```
V = D_1/(Ke−g) × [ 1 − ((1+g)/(1+Ke))^T ]      # perpetuidade crescente TRUNCADA em T
T = prazo médio remanescente ponderado da concessão;  g = IPCA (a RAP é indexada ao IPCA por contrato)
```
**Implementação de blast-radius mínimo:** adicionar `n_anos: Optional[int] = None` a **`ddm.valor_gordon`**. Com `n_anos=None` reproduz a perpetuidade bit-a-bit (backward-safe, igual ao padrão que o `motores.rim` já usa); com `n_anos=T` você ganha a anuidade **de graça**, e o `motores.rim` herda o terminal truncado sem uma linha nova.

**O input duro é `T`.** ⚠️ **NÃO verificado** se está disponível gratuitamente de forma estruturada — não está na DFP da CVM nem no Yahoo. Está na ANEEL e nos releases. **Resposta pragmática: tabela curada de ~12 tickers no `config.yaml`**, rotulada explicitamente `curado, não ingerido`. É um fato, não um knob — trade aceitável.
**Regra dura: `T` ausente DEVE degradar para a opção 1 (sem preço-teto). NUNCA para uma perpetuidade.**

**3. REJEITAR — "manter no DDM atual".**
O DDM atual **é uma perpetuidade**. Manter é preservar o erro conceitual e dizer a si mesmo que fez carve-out. Se vai carve-outar, carve-oute para a anuidade. Se não conseguir o `T`, vá para a opção 1.

### Dois avisos de escopo

- **Saneamento (SBSP3, CSMG3, SAPR11) NÃO é o mesmo caso.** Tipicamente modelo de **ativo intangível**, com contratos municipais renováveis/indefinidos. **Não jogue no mesmo balde.**
- **`eh_concessionaria` (o sinal do hard-route atual, `arquetipo.py:159`) é grosso demais** para este carve-out: manda *tudo* que é concessionário para o mesmo lugar. O carve-out precisa de um sinal mais estreito (setor CVM "energia elétrica" + lista curada de transmissoras) — **e o `PAGADORA_REGULADA` também é o default por eliminação** (`arquetipo.py:176`), o que significa que empresas *sem sinal nenhum* caem no bucket da transmissora. **Isso é um bug latente que o carve-out vai expor: o default por eliminação NÃO pode compartilhar chave com o carve-out de vida finita.** Separar em `PAGADORA_MADURA` (default, → RIM) e `CONCESSAO_FINITA` (curado, → anuidade).

---

## 4. Arquitetura de saída: preço-teto + viés binário + ponte auditável

### A regra de ouro (senão você reintroduz a doença que o marco existe para matar)

`P/B justo = 1 + (ROE_T − Ke)/(Ke − g)` é a forma fechada de **estado estacionário**. O motor do projeto é **multi-estágio** (janela de fade + terminal). **As duas NÃO dão o mesmo número.**

> **NÃO calcule o preço por dois caminhos.** Calcule `V` pelo RIM multi-estágio (**fonte única da verdade**), **derive** `P/B_justo = V / VPA`, e apresente a forma fechada apenas como **decomposição explicativa, rotulada como tal**. Duas rotas de código para um número é exatamente a classe de bug que gerou este marco.

### A ponte auditável — o RIM te dá isso de graça e nenhum outro modelo dá

```
VPA (âncora contábil, do balanço)                R$ 19,40    1,00×
+ VP do excesso de ROE (janela explícita 10a)    R$  8,10    0,42×
+ VP do valor terminal (moat sustentável)        R$  5,40    0,28×
─────────────────────────────────────────────────────────────────
= PREÇO-TETO                                     R$ 32,90    P/B justo 1,70×
  Preço de mercado                               R$ 36,50    P/B       1,88×
  → VIÉS: CARO   (margem −9,9%)
```

Cada linha é um número que o usuário pode **atacar**. **Isso É o produto.** E `ResultadoRIM` já carrega `vpa_base` / `vp_residual_income` / `vp_terminal` — **a ponte já está 90% construída**; falta promovê-la a contrato de saída.

### Estrutura de código — preservando e GENERALIZANDO o firewall

O firewall que existe (`selo.py` nunca importa `report.py`, recebe só primitivos) é a regra certa. **Enuncie-a como invariante global:**

> **Lógica de DECISÃO mora em `core/`, é pura, e recebe primitivos. `report/` COMPÕE. `app.py` RENDERIZA e NUNCA decide.**

**O cheiro arquitetural a matar** (e é a razão de o firewall existir hoje meio de mentira):

```python
# selo.py:88-102 — faixa_do_veredito() PARSEIA UMA STRING HUMANA PARA RECUPERAR UMA DECISÃO
if veredito.startswith("SUBAVALIADA"):  return "Barato"
```
E, em cima disso, `_guarda_faixa_ddm` (report.py:77) e `_guarda_san01` (report.py:108) **reescrevem a string** para derrotar esse parser. **Três camadas lutando por um `if`.**

> **A decisão tem que ser um CAMPO, não um PREFIXO.** No instante em que `Veredito.vies` for um enum, o parser de string morre — e as duas guardas de reescrita de string morrem junto, porque elas só existem para enganar o parser.

### Inventário de componentes — NOVO vs MODIFICADO vs DELETADO

| Componente | Ação | O que faz / por quê |
|-----------|------|---------------------|
| **`core/veredito.py`** | 🟢 **NOVO** (~80 ln) | Puro. `decidir(preco, preco_teto, cfg) → Veredito{vies: "barato"\|"caro"\|None, margem, confianca, motivo_indisponivel}`. **Irmão do `selo.py`, mesmo contrato de firewall — importa NADA de `report/`.** Aqui mora o assert `0 < pb_justo < 6` (substitui `_guarda_san01`). |
| **`core/ponte.py`** (ou dataclass em `motores.py`) | 🟢 **NOVO** (~40 ln) | `PonteValuation` — linhas da decomposição + `preco_teto` + `pb_justo`. **Dados puros, zero formatação.** Invariante testável: `Σ(linhas) == preco_teto`. |
| **`motores.anuidade_concessao`** | 🟢 **NOVO** (~15 ln) | Carve-out §3. Gordon truncado. |
| **`ddm.valor_gordon`** | 🟡 **MODIFICADO** (+1 param) | `n_anos: Optional[int] = None`. `None` ⇒ perpetuidade **bit-idêntica** (backward-safe). Destrava a anuidade E o terminal truncado do RIM de uma vez. **Menor blast radius do marco.** |
| **`core/motores.py`** | 🟡 **MODIFICADO** | `rim()` sobrevive quase intacto. **`excesso_sustentavel` vira constante dura** (§1a). |
| **`core/motores.dcf_crescimento`** | 🔴 **DELETADO** | Double-count provado (`motores.py:186`). "Consertar" com FCFE vira DDM (C4). **Deletar, não consertar.** |
| **`core/motores.lucro_normalizado`** | 🔴 **DELETADO** → vira política de input | `ROE_0 = LPA_normalizado / VPA` alimentando `rim()`. |
| **`core/motores.nav_contabil`** | 🔴 **DELETADO** → vira `rim()` com `excesso=0` | É literalmente `B_0`, o 1º termo do RIM. |
| **`core/fundamentals.py`** | 🟡 **MODIFICADO** | `ROE_CSR` (§2) + conserto do ROE de bases temporais cruzadas (`:137-150`). |
| **`core/normalizacao.py`** | 🟡 **MODIFICADO** | `:73-75` — mediana-de-3 = o ano do MEIO (haircut de 15-20%). Maior alavancagem por linha do repo. |
| **`core/arquetipo.py`** | 🟡 **MODIFICADO** | `ARQUETIPO_MOTOR` (registry motor) → `ARQUETIPO_POLITICA` (registry de **política de input**). Split `PAGADORA_REGULADA` → `PAGADORA_MADURA` + `CONCESSAO_FINITA` (§3). |
| **`core/capm.py`** | 🟡 **MODIFICADO** | Blume (`0,33 + 0,67β`), β setorial, ERP único 4,5%. **`ke_rim` e seus clamps (`ke_piso`/`ke_teto`) DELETADOS** — mas só na Fase 5 (§5). |
| **`ingest/macro.py`** | 🟡 **MODIFICADO** | `ipca_ciclo(anos=10)` — irmã simétrica de `selic_ciclo_para_capm`. Mesma janela (é isso que dá invariância à inflação). |
| **`ingest/cvm.py`** | 🟡 **MODIFICADO** | JCP (`:169`), lucro/PL do controlador, **+ prefixo `DMPL_con`/`DMPL_ind`** para o `ROE_CSR` (§2). ⚠️ **Barato: o ZIP já é baixado e `_ler_demonstracao` já é genérica — custa 1 string, não uma superfície nova.** |
| **`ingest/build.py`** | 🟡 **MODIFICADO** | `num_acoes` (`:87` bases cruzadas; `:102` `sharesOutstanding` → `impliedSharesOutstanding`). |
| **`ingest/` (novo módulo de reconciliação)** | 🟢 **NOVO** (~60 ln) | Os 4 asserts do `STACK.md` + o 5º (`ROE_CSR`, §2). **Avisa e marca confiança baixa — never-raise.** Sem `pandera`. |
| **`report/report.py`** | 🟡 **MODIFICADO — encolhe muito** | `analisar_acao` vira composição: classificar → resolver inputs → `rim()`/`anuidade()` → `veredito.decidir()` → `selo.montar_selo(bsd, vies_enum, cfg)`. **Deletar:** `_intrinseco_por_motor` (dispatch de modelo), `_veredito_fronteirico` (range multi-motor), `_hipotese_divergencia`, campos `divergencia_*`, `_guarda_san01`, `_guarda_faixa_ddm`. |
| **`report/selo.py`** | 🟡 **MODIFICADO — encolhe** | `faixa_do_veredito(str)` **DELETADA**. `montar_selo` passa a receber `vies: enum`. Firewall **preservado e reforçado** (agora recebe um enum em vez de fazer engenharia reversa de uma frase). |
| **`core/comparables.py`** (regressão P/L) | 🔴 **APOSENTADO** | `STACK.md`: R² = 0,037, **cego ao nível de preço**. Com `preco_teto` em todo ticker, o Ranking vira `sort by (preco_teto/preco)` — mais simples E melhor. `LIMIAR_DIVERGENCIA`/ensemble morrem junto (§1). |
| **`core/freio.py`** | ⚪ **INTOCADO** | Já faz o gate do Ranking. Continua. |
| **`app.py`** | 🟡 **MODIFICADO — só leitura** | Ganha leitura dos campos novos. **A Key Decision "app.py é read-only" já existe no PROJECT.md e está rated ✓ Good — só precisa ser ENFORCED para os campos novos.** |
| **`tests/test_firewall.py`** | 🟢 **NOVO** (~20 ln) | `core/` nunca importa `report/` nem `streamlit`; `app.py` nunca chama motor. **A regra é cultural hoje; vire teste.** |

---

## 5. Ordem de build

### O insight de agendamento que vale mais que tudo

O marco vai reescrever ~150 goldens. A suíte **vai ficar vermelha por várias fases** se você tentar mantê-la verde. Então:

> **Não tente manter a suíte verde. Mude o que "verde" SIGNIFICA — na primeira fase.**

Os ~150 goldens são **valores fixados** (`ITUB4: 32.88 ± 0.20`). Eles são, hoje, a **memória de um overfit** (4 knobs contra 4 observações). Mas os testes que serão verdadeiros **no fim** são **propriedades derivadas da teoria** — e podem ser escritos **HOJE**, antes de uma única linha de conserto.

### Fase 0 (NOVA, barata, primeiro de tudo): Quarentena + Invariantes

**Quarentena:** `tests/golden_v23/` marcados `@pytest.mark.legado`, desselecionados por default (`addopts = -m "not legado"`). Eles são **deletados** — não "consertados" — quando a fase deles chega.

**Invariantes (o spec real, escrevível já):**

| Invariante | O que trava | Estado inicial |
|-----------|-------------|----------------|
| `V ≥ VPA` sse `ROE_T > Ke` (e `V < VPA` sse `ROE_T < Ke`) | Anti-bad-bank | verde |
| `0 < P/B_justo < 6` em **todo** o universo | **A guarda CGRA4** — o único uso real do argumento (c) | vermelho → verde na Fase 2 |
| **INVARIÂNCIA À INFLAÇÃO:** config com `π` vs `π+300bps` (deslocando `rf` **e** `g_cap`) ⟹ `V` move < 2% | **ISTO É A DEFINIÇÃO DA DOENÇA 1.** Escrevível hoje, `xfail(strict=True)`, vira verde na Fase 4. **Gate red/green de verdade, em vez de uma pilha de pins quebrados.** | xfail → verde na Fase 4 |
| `Σ(linhas da ponte) == preco_teto` | A ponte reconcilia | verde ao nascer |
| `core/` não importa `report/`; `app.py` não decide | Firewall | verde |

**Resultado: da Fase 1 em diante a suíte ATIVA é verde e SIGNIFICA algo.** Tempo com suíte vermelha ≈ zero. **Maior alavanca de agendamento disponível.**

### A cadeia de dependências

| # | Fase | Depende de | Por que aqui | Suíte |
|---|------|-----------|--------------|-------|
| **0** | **Quarentena + invariantes** | — | Redefine "verde". Compra um gate funcional para todas as fases seguintes. | 🟢 |
| **1** | **Reconciliação de sanidade (4+1 asserts)** | 0 | `STACK.md`: **eles SÃO o teste de regressão da Fase 2.** Instalar o detector **antes** do conserto, senão você não consegue *provar* o conserto. Entrega um relatório dos 41 tickers quebrados. | 🟢 |
| **2** | **Ingestão correta** (`impliedSharesOutstanding`, JCP, lucro do controlador, duplo split) | 1 | Os asserts da Fase 1 viram verde **ticker a ticker**: progresso mensurável, não vibe. | 🟢 |
| **3** | **Primitivas sem viés** (`normalizacao.py:73-75`, `fundamentals.py:137-150`) + **`ROE_CSR`** | 2 | Sem dado correto, primitiva correta não significa nada. `ROE_CSR` cabe aqui: é primitiva **E** reconciliação. | 🟢 · **os pins legados começam a morrer** |
| **4** | **`g` fechado** (`g_cap = (1+π_ciclo)(1+PIB_real)−1`, **mesma janela do `rf`**) | 3 | ⚠️ **TEM que preceder o Ke.** Sozinho ele vai **exagerar** em alguns nomes (o `ke_teto` continua lá, agora compensando nada). **Aceite — é uma janela de 1 fase.** O teste de invariância à inflação vira verde AQUI. | 🟢 |
| **5** | **`Ke` limpo** (remover `ke_teto`/`ke_piso`, Blume, β setorial, ERP 4,5% único) | 4 | Tirar o clamp só é seguro depois do `g`. `STACK.md`: **Blume não muda nada enquanto o clamp absorve tudo** — logo Blume é *de graça* aqui. | 🟢 |
| **6** | **Colapso em um motor + contrato de saída** (RIM único, política de input, ponte, `veredito.py`, carve-out de concessão, aposentar ensemble/regressão) | 5 | Precisa de `Ke` e `g` confiáveis, ou você entrega uma ponte de aparência honesta sobre números desonestos. | 🟢 · **pins legados restantes DELETADOS** |
| **7** | **Hold-out** (40-60 tickers, fair values commitados **ANTES**, roda **UMA** vez, 3 GdL) | 6 | Por último. Qualquer coisa antes disso queima o hold-out. | 🟢 |

### Três regras duras para o roadmapper

**A) NÃO fundir a Fase 4 com a Fase 5 "para economizar tempo".**
A simulação diz que Ke sozinho é líquido-zero (0,68 → 0,67) e g sozinho exagera. **A interação é o ponto inteiro.** Duas fases = duas medições limpas contra o mapa de 104 tickers. Uma fase = um número e zero diagnóstico. **A tentação de fundir vai ser forte e está errada.**

**B) O golden do ITUB4 quebrar É O CONSERTO FUNCIONANDO.**
Ele foi calibrado para *cancelar* o haircut de lucro da primitiva. **Dois erros se anulando.** Preservá-lo é preservar o erro.
> **Escreva como CRITÉRIO DE SAÍDA da Fase 3: "o golden `ITUB4: 32.88 ± 0.20` DEVE quebrar. Se não quebrar, o conserto da primitiva não pegou."**
Isso **inverte o incentivo** — um golden quebrado vira evidência de sucesso, não defeito. Precisa estar escrito porque **vai parecer errado no momento.**

**C) A Fase 6 tem que DELETAR knobs, e isso tem que ser um requisito CONTADO.**
O bloco `motores:` do `config.yaml` (linhas 229-264) tem ~20 chaves. O `STACK.md` fixa o orçamento em **3 graus de liberdade** (ERP 4,5% · n_fade 5 · PIB_real 2,0%). `excesso_sustentavel` (0,045), `g_terminal` (0,025), `ke_teto`, `ke_piso`, `roe_terminal_stat` **foram todos calibrados contra o `g` enviesado** — eles têm que ser **re-derivados, não re-tunados**.
> Requisito verificável: **`config.yaml` bloco `motores:` sai de ~20 chaves para ≤ 5.** Sem um número, essa deleção não acontece.

---

## Riscos e o que NÃO foi verificado

| Item | Confiança | Ação |
|------|-----------|------|
| Equivalência RIM≡DDM≡DCF e condições C1-C4 | **HIGH** | Teoria consolidada (Ohlson 1995, Penman, Lundholm-O'Keefe) |
| Viés truncado RIM 8,3% / DDM 31,4% / DCF 111,2% | **HIGH** | Penman & Sougiannis |
| Dirty surplus = variância, não viés | **MEDIUM-HIGH** | Evidência internacional (Isidro/O'Hanlon/Young 2004). **Materialidade BRASILEIRA não medida** → script de 20 linhas na Fase 3 |
| Transmissoras sob ICPC 01 = modelo de **ativo financeiro**, lucro IFRS ≠ lucro regulatório | **MEDIUM-HIGH** | Confirmado (nota técnica IFRS×Regulatório da própria TAESA; CVM OC-SNC/SEP) |
| **Prazo remanescente `T` da concessão disponível de graça e estruturado** | **⚠️ NÃO VERIFICADO** | **Provável que NÃO.** Plano: tabela curada de ~12 tickers no `config.yaml`. **`T` ausente ⟹ sem preço-teto, NUNCA perpetuidade.** |
| **DMPL disponível para o `ROE_CSR`** | **HIGH — VERIFICADO no código** | ✅ **Já vem no ZIP que o `cvm.py:23` baixa**, e `_ler_demonstracao(ano, prefixo)` (`cvm.py:74`) é genérica. **Custo = 1 string de prefixo.** Implementar a versão COMPLETA; a de 80% vira só fallback |
| O peso do terminal do RIM ~dobra quando o `g` subir | **HIGH** (aritmética) | Guardas `excesso_sustentavel`/`ke_g_spread_min` viram load-bearing na Fase 4 |
| Transmissoras vão piorar visivelmente na Fase 4 (o `g` destrói o truncamento acidental) | **MEDIUM** | Não entre em pânico e re-tune; é esperado. O carve-out da Fase 6 é o conserto |

---

## Sources

- Penman, *Financial Statement Analysis and Security Valuation* — clean surplus, fade do lucro econômico, decomposição RIM. [Valuation Models: An Issue of Accounting Theory (Columbia)](https://business.columbia.edu/sites/default/files-efs/pubfiles/6208/Valuation%20Models%20Routledge.pdf) — HIGH
- Ohlson (1995) / Lundholm & O'Keefe — equivalência com valores terminais ideais. [The Equivalence of Dividend, Cash Flows and Residual Earnings Approaches](https://www.researchgate.net/publication/228306685_The_Equivalance_of_Dividend_Cash_Flows_and_Residual_Earnings_Approaches_to_Equity_Valuation_Employing_Ideal_Terminal_Value_Expressions) — HIGH
- Penman & Sougiannis — viés por truncamento (RIM 8,3% / DDM 31,4% / DCF 111,2%). [Extended Dividend, Cash Flow and Residual Income Valuation (KIT)](https://www.fbv.kit.edu/symposium/11th/Paper/03CorporateGovernance/sievers.pdf) — HIGH
- CFA L2 — RIM vs DDM vs FCF, sensibilidade ao terminal. [AnalystPrep](https://analystprep.com/study-notes/cfa-level-2/residual-income-vs-ddm-and-fcf-models/) — MEDIUM
- OCI/dirty surplus invalida RIM; recycling não salva. [The Footnotes Analyst — Residual income valuation: OCI and clean surplus](https://www.footnotesanalyst.com/residual-income-valuation-oci-and-clean-surplus/) — MEDIUM-HIGH
- Isidro, O'Hanlon & Young (2004) — dirty surplus não causa erro **sistemático**. [Dirty surplus accounting flows: international evidence](https://ideas.repec.org/a/taf/acctbr/v34y2004i4p383-410.html) — MEDIUM-HIGH
- TAESA — *Nota Técnica: Práticas Contábeis IFRS × Regulatório*. [ri.taesa.com.br](https://ri.taesa.com.br/wp-content/uploads/importer-old-site/nota-tecnica-ifrs-x-regulatorio-vfinal_4399_899_22982.pdf) — HIGH (fonte primária da própria companhia)
- CVM — Ofício-Circular SNC/SEP 04/2020 (CPC 47/48 em transmissoras). [conteudo.cvm.gov.br](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/oficios-circulares/snc-sep/anexos/ocsncsep042020.pdf) — HIGH
- CPC — OCPC 05, contratos de concessão (modelos ativo financeiro / intangível / bifurcado). [OCPC 05](https://conteudo.cvm.gov.br/export/sites/cvm/menu/regulados/normascontabeis/cpc/OCPC_05_rev_14.pdf) — HIGH
- Código do próprio projeto: `core/motores.py`, `core/capm.py`, `core/arquetipo.py`, `report/selo.py`, `report/report.py`, `config.yaml:229-264` — HIGH
