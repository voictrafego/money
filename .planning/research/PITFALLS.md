# Domain Pitfalls — v2.4 Fidelidade do Valuation

**Domain:** engine de valuation fundamentalista sobre dados públicos brasileiros (CVM + Yahoo + BCB)
**Researched:** 2026-07-13
**Overall confidence:** MEDIUM-HIGH (a maior parte é verificada no próprio código deste repo + execução real; 2 fatos externos verificados em fonte oficial)

> **Como ler este documento.** Cada pitfall tem **Sinal de alerta**, **Prevenção** (um assert, um teste ou uma regra de commit — nunca "tome cuidado") e **Fase**. O Pitfall 1 é o mais importante: é o único que, se falhar, faz todos os outros consertos serem revertidos silenciosamente.

---

## Achados de execução (medidos, não teorizados)

Rodei o código deste repo antes de escrever. Três números que mudam o enquadramento do marco:

**(a) O haircut da `base_normalizada` é real e proporcional ao crescimento.**
`normalizacao.py:69-75` — com `anos_media=3`, `n=3 < 5` → retorna `median(janela)` = **o ano do MEIO**. Numa série de crescimento constante:

| crescimento do lucro | base normalizada vs. último ano |
|---|---|
| 5% a.a. | **−4,8%** |
| 10% a.a. | **−9,1%** |
| 15% a.a. | **−13,0%** |

O haircut é **exatamente o crescimento de um ano**. O modelo penaliza a empresa por crescer. Ele entra em `roe_valuation`, `lpa_valuation`, `margem_valuation` e (via ROE) no âncora terminal do RIM — o mesmo erro aplicado 4 vezes.

**(b) O gate `BACKTEST-01` que declarou "4/4 PASS, a calibração generalizou" é na verdade 2/4.**

| ticker | faixa de consenso | banda efetiva (±15%) | largura | valor do motor | dentro do **consenso**? |
|---|---|---|---|---|---|
| ITUB4 | 30,50–50,00 | 25,93–57,50 | **2,22×** | 32,88 | sim |
| BBAS3 | 20,00–39,00 | 17,00–44,85 | **2,64×** | 43,89 | **NÃO** (acima do teto) |
| BBDC4 | 15,00–24,00 | 12,75–27,60 | **2,16×** | 13,37 | **NÃO** (abaixo do piso) |
| BBSE3 | 33,00–46,00 | 28,05–52,90 | 1,89× | 39,87 | sim (via rota criada *ad hoc*) |

Um gate cuja banda de aprovação tem 2,2× de largura não é um gate — é um carimbo. E BBAS3/BBDC4 **falham o consenso** e passam só pelo acolchoamento. A frase do docstring de `test_backtest_bancos.py:16` ("4/4 na banda ±15% → o quórum 3/4 é atingido com folga") é literalmente verdadeira e substantivamente falsa.

**(c) O teto de P/L do modelo é 9,5×, não 7,8×** (com `ke_teto=0,13` e `g=0,025`), contra P/L mediano de mercado ~9,9×. Com o `g_cap` nominal de 7,3% proposto e um Ke coerente, o teto vai para ~12,1×. O diagnóstico do marco está direcionalmente certo; o número exato no PROJECT.md está um pouco off. Não muda a conclusão.

---

## CRÍTICOS

### Pitfall 1 — Reajustar o knob para o golden voltar a passar (o pitfall META)

**O que dá errado.** Você conserta `build.py:87` (num_acoes), o ITUB4 sai de 32,88 para 27,40, `test_backtest_alvos_recalibrados` fica vermelho, e a saída de menor resistência — a que o próprio repo já ensinou, por escrito — é mexer em `excesso_sustentavel` até voltar a 32,88. Aí você trocou um bug de dados por um knob, e o overfit sobrevive ao conserto que existia para matá-lo.

**Por que acontece aqui, especificamente.** O repo já **codificou a instrução de fazer isso**:
- `config.yaml:237` — *"Move ITUB4 ~R$2."* (um knob descrito pelo seu efeito num ticker, não pela sua economia)
- `config.yaml:258` — *"NÃO mexer nos knobs acima (excesso_sustentavel/g_terminal/ke_teto): mudariam o ITUB4."*
- `tests/test_backtest_bancos.py:121` — `alvos = {"ITUB4": 32.88, ...}`, `± 0,20`

Um agente executor lendo isso conclui, corretamente pelo texto, que **o trabalho dele é preservar 32,88**. O overfit não está no config; está no *contrato implícito* do repositório.

**Consequência.** O v2.4 produz números novos com o mesmo viés antigo e ninguém consegue provar o contrário — porque o único teste de nível que existe é o que trava o viés.

**Prevenção — 6 mecanismos, do mais forte ao mais fraco. Implemente ao menos os 4 primeiros.**

**P1.1 — DELETAR o golden, não atualizá-lo. Fase 0, primeiro commit do marco.**
`test_backtest_alvos_recalibrados` (linhas 113-125) é um *characterization test de um método que sabemos errado*. Atualizar `32.88 → <novo número>` mantém o mecanismo vivo (o próximo bug vai bater no novo número e o reflexo volta). Deletar remove o incentivo. O commit de deleção carrega a justificativa:

```
test(backtest): deleta goldens de nível da cesta de bancos (v2.3)

Os alvos ITUB4 32,88 / BBAS3 43,89 / BBDC4 13,37 foram calibrados contra
4 observações com >=4 graus de liberdade, sobre um pipeline com escala de
num_acoes quebrada. São goldens de um método errado. Substituídos por
testes de distribuição (P1.2) e de invariante (P1.3), que não podem ser
satisfeitos mexendo num knob.
```

**P1.2 — Trocar assert-de-ticker por assert-de-distribuição.** Nenhum teste do v2.4 pode conter o nome de um ticker ao lado de um número de reais. O que substitui:

```python
# tests/test_holdout_distribuicao.py
def test_sem_vies_sistematico():
    r = rodar_cesta(HOLDOUT)                      # 40-60 tickers
    ratios = [x.v / x.fair_value for x in r]
    assert 0.85 <= median(ratios) <= 1.15,  "viés sistemático de nível"

def test_dispersao_sob_controle():
    ratios = [...]
    dentro = sum(0.75 <= x <= 1.33 for x in ratios) / len(ratios)
    assert dentro >= 0.60,  "o motor não concorda com nada em particular"

def test_nenhum_ticker_e_load_bearing():
    """Nenhuma observação isolada pode carregar o resultado (anti-ITUB4)."""
    ratios = [...]
    for i in range(len(ratios)):
        m = median(ratios[:i] + ratios[i+1:])     # jackknife
        assert 0.85 <= m <= 1.15
```

O último é o antídoto direto ao pecado original: se o resultado depende de um ticker, o teste diz.

**P1.3 — Testes de INVARIANTE, que nenhum knob pode satisfazer.** Um knob move um *nível*; ele não conserta uma *identidade*. Estes são os testes que o executor não consegue burlar tunando:

```python
def test_valuation_invariante_a_inflacao():
    """Doença 1. Somar inflação ao rf E ao g não pode mudar o P/L justo."""
    pl_a = teto_pl(rf=0.04, erp=0.06, g_real=0.025, ipca=0.00)
    pl_b = teto_pl(rf=0.04, erp=0.06, g_real=0.025, ipca=0.05)
    assert abs(pl_a - pl_b) / pl_a < 0.02   # HOJE: falha (o modelo cobra 5% pela inflação)

def test_base_normalizada_nao_pune_crescimento():
    """Doença 'primitivas'. Série 10% a.a.: a base não pode dar haircut."""
    s = [100.0 * 1.10**i for i in range(10)]
    assert normalizacao.base_normalizada(s, anos_media=3) >= 0.98 * s[-1]
    # HOJE: retorna s[-2] (mediana de 3 = o do meio) -> 214,36 vs 235,79 = -9,1%

def test_teto_de_pl_cobre_o_mercado():
    """O motor precisa ser capaz de justificar a ação mediana da bolsa."""
    assert 1.0 / (ke_tipico() - g_cap()) >= 10.0   # P/L mediano da B3 ~9,9x

def test_rim_equivale_a_dcf_equity_sob_clean_surplus():
    """Identidade algébrica. Se quebrar, o motor está errado — não é calibração."""
```

**P1.4 — Regra de commit: knob e golden nunca no mesmo commit.** É a assinatura exata da fraude ("afrouxei o parâmetro e movi o alvo"). Hook em `.git/hooks/pre-commit` (e espelhado no CI):

```bash
#!/bin/sh
staged=$(git diff --cached --name-only)
tocou_cfg=$(echo "$staged" | grep -c '^config.yaml$')
tocou_gold=$(echo "$staged" | grep -cE '^tests/(fixtures/|.*golden|test_holdout)')
if [ "$tocou_cfg" -gt 0 ] && [ "$tocou_gold" -gt 0 ]; then
  echo "BLOQUEADO: config.yaml + fixture/golden no mesmo commit."
  echo "Separe: (1) o conserto do código/dado, (2) o número novo com a razão econômica."
  exit 1
fi
```

**P1.5 — `calibracao.lock.yaml` + orçamento de knobs travado por teste.** Exatamente 3 knobs livres. Um teste falha se alguém criar o 4º, ou mudar o valor de um sem registrar o porquê:

```python
KNOBS_LIVRES = {"valuation.g_cap", "valuation.erp", "motores.rim.excesso_sustentavel"}  # 3. Ponto.

def test_orcamento_de_knobs():
    marcados = {k for k in flatten(cfg) if "# CALIBRAVEL" in comentario(k)}
    assert marcados == KNOBS_LIVRES, "grau de liberdade novo sem passar pela porta da frente"

def test_knobs_batem_com_o_lock():
    lock = yaml.safe_load(open("calibracao.lock.yaml"))
    for k in KNOBS_LIVRES:
        assert valor(cfg, k) == lock[k]["valor"], (
            f"{k} mudou de {lock[k]['valor']} para {valor(cfg,k)}.\n"
            f"Para mudar: edite calibracao.lock.yaml com (a) razão ECONÔMICA, "
            f"(b) o resultado do hold-out DEPOIS da mudança, (c) sua assinatura.\n"
            f"Nunca é válido justificar com 'para o teste X voltar a passar'."
        )
```

O lock exige que a mudança seja um ato deliberado, escrito e revisável. Não impede o tuning — torna impossível fazê-lo *em silêncio*, que é como ele acontece.

**P1.6 — Regra de direção de causalidade (escreva no CLAUDE.md do projeto).**
> Quando um número muda depois de um conserto de dado/primitiva, existem **exatamente duas** respostas permitidas: (1) aceitar o número novo e registrar *por que ele se moveu, em termos econômicos*; (2) reverter o conserto porque ele está errado. **Reajustar um knob NUNCA é uma resposta permitida.** Os knobs ficam CONGELADOS (P1.5) durante as Fases 1-5; só a fase de calibração pode tocá-los, e ela roda uma vez.

**Detecção (o sinal de alerta a caçar em code review).** Qualquer justificativa da forma *"ajustei X porque o ticker Y estava em Z"*. Compare `config.yaml:237` ("Move ITUB4 ~R$2") — é o formato canônico do erro. Uma justificativa legítima de knob **nunca menciona um ticker**.

**Fase:** 0 (deleção do golden + lock + hook, ANTES de qualquer código) e 6 (calibração).

---

### Pitfall 2 — A "nota de exceção" é uma lavanderia de overfit

**O que dá errado.** O gate atual (`test_backtest_bancos.py:88-110`) tem uma regra: um ticker fora da banda passa **se tiver `excecao_nota`**. Combinada com o quórum de 3/4, isso torna o gate **infalsificável**: qualquer reprovação vira aprovação escrevendo um parágrafo. Foi exatamente o que aconteceu com a BBSE3 — ela falhou o RIM, então foi **criada uma rota nova de motor** ("seguradora capital-light → Gordon-franquia") e o `excecao_nota` do fixture a documenta como arquétipo, não como falha. O texto da nota é honesto e bem-escrito; o mecanismo é o problema.

Uma rota criada *depois* de ver qual ticker falhou é um grau de liberdade, mesmo que não tenha número nenhum. **Graus de liberdade não se contam só em floats.**

**Consequência.** "4 knobs sobre 4 observações" subestima. O DoF efetivo do v2.3 é: 4 números + 1 mecanismo novo (valor terminal) + 1 escolha de estatística (`roe_terminal_stat: mediana|media`) + 1 rota nova (seguradora) + 1 regra de exceção ≈ **8 graus de liberdade sobre 4 observações**. Isso não é calibração, é interpolação.

**Prevenção.**
- Toda escolha estrutural (rota, carve-out, motor, estatística robusta) conta como **1 grau de liberdade** no orçamento, igual a um float.
- **Carve-outs são declarados ANTES de rodar**, com base no domínio de validade do modelo (transmissora = concessão de prazo finito → perpetuidade é inválida; seguradora capital-light → book não é a base de capital), num arquivo commitado antes do primeiro run. Um carve-out declarado depois é um overfit com boa redação.
- No hold-out, **zero exceções permitidas**. `assert not any(r.excecao_nota for r in holdout)`. Uma exceção no hold-out = hold-out reprovado.
- Aposentar o par quórum+nota. Substituir pelos testes de distribuição do P1.2 (que não têm porta dos fundos).

**Fase:** 6 (revalidação), com o arquivo de carve-outs escrito na Fase 5.

---

### Pitfall 3 — Validação circular: "consenso de casas de análise" é preço com um chapéu

**O que dá errado.** `tests/fixtures/fair_values_bancos.yaml` ancora o modelo em *target prices* de sell-side. Um target price é ≈ preço atual × (1 + upside que o analista defende), com o *upside* mediano da indústria estruturalmente positivo e a dispersão entre casas refletindo, em boa parte, o próprio preço de mercado. Validar V contra ele é validar V contra o preço com passos extras — e o marco inteiro nasceu da constatação de que o modelo **discorda do preço em 80% da bolsa**. Você não pode usar como juiz aquilo que está sendo julgado.

Pior: as faixas foram coletadas em 2026-07-12, **depois** de já se saber que o ITUB4 "estava errado". Fair values colhidos com conhecimento do alvo não são âncora, são espelho.

**Qual é a âncora não-circular.** Não existe uma. Existem quatro parciais, e a validação honesta usa as quatro para coisas *diferentes*:

| Âncora | O que ela pode provar | O que ela NÃO pode provar |
|---|---|---|
| **1. Invariantes algébricos** (RIM ≡ DCF-equity sob clean surplus; NAV = 1º termo; invariância à inflação) | Que o motor não tem erro de unidade nem de fórmula. **É a única prova dura, e é grátis** (sem dado externo). | Que o número é "certo". |
| **2. Centro da seção transversal** (mediana de V/P ≈ 1 no universo) | **Ausência de viés de unidade.** Um modelo que diz que 80% da bolsa está errada *na mesma direção* está diagnosticando a si mesmo. Condição **necessária**. | Acurácia. É um detector de viés, jamais um teste de acerto. **Nunca calibrar para maximizar isso** — é assim que se constrói uma máquina de reproduzir o preço. |
| **3. Ordenação vs. retorno futuro realizado** (backtest temporal: decis de V/P em *t* vs. retorno total em *t+3a*) | **A única evidência não-circular de que o modelo informa alguma coisa.** O output realizado não sabe o que o modelo previu. | Que o *nível* de V está certo (só a ordenação). |
| **4. Expectativas implícitas reversas** (dado o preço, qual `g`/ROE o mercado embute? é plausível vs. o histórico?) | Que o modelo é uma **lente auditável** — "para pagar esse preço você precisa acreditar em ROE de 22% para sempre". | Nada, sozinha. Mas é o output mais honesto que um valuation gratuito pode entregar, e casa com a "ponte auditável" do marco. |

**Recomendação opinativa.** A métrica primária de aceitação do v2.4 deve ser **(1) + (2)**: invariantes duros + ausência de viés no centro da distribuição. (3) é o desempate e a evidência de valor real, com as ressalvas do Pitfall 4. **Descontinue o consenso de sell-side como âncora de aprovação** — mantenha-o, se quiser, como *sanity display*, nunca como gate.

E aceite o corolário desconfortável: **um valuation gratuito não tem como provar que acerta o nível.** O produto honesto não é "o preço justo é R$32,88" — é "a este preço, o mercado embute X; seu histórico diz Y; a diferença é seu edge ou seu erro". Isso é o que o "preço-teto + viés binário + ponte auditável" do marco já quer ser. Vá até o fim: **pare de prometer um número de precisão que o dado não sustenta.**

**Fase:** 6 (contrato de validação) + 5 (contrato de saída).

---

### Pitfall 4 — Look-ahead bias na CVM (invalida o backtest temporal ingênuo)

**O que dá errado.** A DFP do exercício *N* só existe em **até 3 meses após o encerramento do exercício social** (Resolução CVM 80/2022, art. 22, IV — emissor nacional; 4 meses para estrangeiro) — na prática, DFP de 2022 disponível a partir de ~mar/2023, com retardatários depois disso. Um backtest que, em 01/jan/2023, usa o lucro de 2022 está negociando com informação que ninguém tinha. Em séries de dividendos isso infla o resultado brutalmente, porque o que você "sabia" é justamente o que moveu o preço em março.

**Segundo look-ahead, mais sutil e que a maioria ignora:** os ZIPs de Dados Abertos da CVM são **regenerados**. `dfp_cia_aberta_2019.zip` baixado hoje contém a versão **atual** das demonstrações de 2019 — incluindo **reapresentações** (restatements) feitas em 2021, 2022. Você lê números que só passaram a existir depois. `cvm.py:51-70` cacheia o ZIP mas **não registra quando foi baixado nem qual versão é** — então nem dá para medir a contaminação.

**Terceiro:** `universe.py`/`ticker_map` é o universo **de hoje** → **survivorship bias**. Rodar um backtest 2022→2025 sobre os tickers que existem em 2026 exclui, por construção, tudo que quebrou, foi deslistado ou incorporado (AMER3, OIBR, etc.) — as exatas empresas que um modelo de dividendos precisa provar que evita. Um backtest survivorship-contaminado **sempre parece bom**.

**Prevenção.**
```python
# ingest/pit.py
def disponivel_em(ano_exerc: int) -> date:
    """DFP do exercício N vira pública em até 3 meses (Res. CVM 80). +1 mês de folga
    para retardatário/reapresentação inicial."""
    return date(ano_exerc + 1, 4, 30)

def assert_point_in_time(anos_usados: list[int], as_of: date) -> None:
    for a in anos_usados:
        assert disponivel_em(a) <= as_of, (
            f"LOOK-AHEAD: exercício {a} só é público em {disponivel_em(a)}, "
            f"mas o backtest está em {as_of}"
        )
```
- O harness de backtest temporal **chama `assert_point_in_time` obrigatoriamente**; sem `as_of` explícito ele se recusa a rodar (`raise`, não default).
- Carimbe a proveniência: gravar `data_download` + `ETag`/`Last-Modified` do ZIP num sidecar por arquivo em `data/cvm/`. Não elimina a contaminação por reapresentação (impossível sem dado PIT pago), mas **torna-a mensurável e declarável**.
- **Declare a limitação no relatório do backtest**, com esta frase: *"restatement-contaminated — o backtest usa as demonstrações como estão hoje, não como estavam então; isso favorece o modelo."* Um viés declarado é honesto; um viés escondido é fraude.
- Survivorship: monte o universo do ano *t* a partir do **FCA daquele ano** (a CVM publica o FCA por ano, e o repo já usa FCA em `universe.py`) — não do `ticker_map` atual. Se não der: **não rode o backtest de retorno**, ou reporte-o como enviesado-para-cima e não o use como gate.
- Regime único: 2022→2025 é **uma** amostra macro (ciclo de Selic). Não afirme generalidade. Reporte por coorte de ano de entrada.

**Veredito sobre a pergunta "backtest temporal resolve a circularidade?":** resolve **a circularidade** (o retorno futuro não conhece o modelo), mas **importa quatro vieses novos** (look-ahead, restatement, survivorship, regime único). Ele é uma boa **âncora secundária de ordenação** e um **péssimo gate de nível**. Se o custo de fazê-lo direito (universo PIT do FCA + trava de disponibilidade) for alto demais para o orçamento do marco, **prefira não fazê-lo a fazê-lo mal** — um backtest ingênuo produz um número confiante e falso, que é pior que nenhum número.

**Fase:** 6, com a decisão explícita de escopo ("fazer PIT direito" vs. "não fazer") tomada na Fase 5.

---

### Pitfall 5 — O executor "conserta" os ~150 testes em vez de consertar o código

**O que dá errado.** Suíte vermelha em 150 testes é uma pressão enorme. Os caminhos de menor resistência, em ordem de frequência: afrouxar tolerância (`± 0,20` → `± 2,00`), trocar por `pytest.approx(rel=0.5)`, adicionar `xfail`/`skip`, deletar o assert, ou "atualizar o golden" copiando a saída atual sem olhar. Todos deixam a suíte verde. Todos destroem a capacidade da suíte de detectar o próximo erro. Este repo já tem o precedente: o `xfail(strict=True)` do backtest foi *removido* quando o quórum passou (docstring, linha 19) — ou seja, o teste foi projetado para deixar de reprovar.

**Prevenção — 4 mecanismos.**

**P5.1 — Classificar os 448 testes ANTES de escrever uma linha de código (Fase 0), num arquivo commitado.**

| Bucket | Definição | O que pode acontecer com ele |
|---|---|---|
| **INVARIANTE** | Identidade algébrica, degradação graciosa, tratamento de `None`, determinismo, "não puxa rede", escala/unidade | **Deve continuar passando bit-a-bit.** Qualquer quebra aqui é regressão real. **NUNCA reclassificar.** |
| **GOLDEN DE NÍVEL** | Um número produzido pelo método antigo | **DELETADO** (não editado), com uma linha de razão |
| **CONTRATO** | Forma da saída, nomes de campo, tipos | Reescrito deliberadamente para o contrato novo |

O arquivo `tests/CLASSIFICACAO-v2.4.md` é commitado **antes** do primeiro conserto. Sem ele, o executor decide bucket na hora — e um invariante que quebrou vira "ah, era só um golden".

**P5.2 — Golden master + diff aprovado, em vez de golden por teste.** Antes de tocar no código, congele a saída completa do universo (104 tickers × todos os campos) em `tests/fixtures/baseline_v2.3.json`. O teste não é *"a saída == o golden"*; o teste é *"o diff é exatamente o diff aprovado"*:

```python
def test_diff_e_o_aprovado():
    atual = rodar_universo(SNAPSHOT_CONGELADO)
    diff = diffar(carregar("baseline_v2.3.json"), atual)
    aprovado = carregar("tests/fixtures/diff_aprovado_v2.4.json")
    assert diff == aprovado, (
        "A saída mudou de um jeito que ninguém aprovou. Rode `make aprovar-diff`, "
        "que exige uma linha em .planning/DIFF-LOG.md explicando a MUDANÇA ECONÔMICA."
    )
```
Cada número que se move fica **visível, contável e assinado**, em escala, sem congelar o valor errado. É o oposto exato de "atualizar o golden": o *delta* é o artefato revisado, não o nível.

**P5.3 — CI que barra o afrouxamento.** Um script de ~20 linhas sobre `git diff` da PR:
- proibir `xfail`, `skip`, `pytest.approx` **novos** sem `# JUSTIFICATIVA:` na linha anterior;
- proibir aumento de tolerância numérica (regex em `<= 0.20` → `<= 2.00`) sem `# JUSTIFICATIVA:`;
- proibir queda na contagem de testes sem uma entrada correspondente em `DIFF-LOG.md`.

**P5.4 — Meta-teste de sensibilidade (o "canário").** Depois da migração, prove que a suíte nova **consegue** reprovar:
```python
def test_a_suite_reage_a_um_knob():
    """Se eu piorar o g_cap em 1pp e a suíte ficar verde, a suíte não restringe nada."""
    with cfg_perturbado("valuation.g_cap", delta=+0.01):
        falhas = rodar_suite_de_valuation()
    assert len(falhas) >= 3, "a suíte é decorativa"
```
Sem isso, você pode terminar o marco com 448 testes verdes que não constrangem o modelo — que é, essencialmente, o estado de hoje.

**Fase:** 0 (classificação + baseline + CI), contínua até a 6.

---

## MODERADOS — dados financeiros brasileiros

### Pitfall 6 — Minoritários: lucro consolidado ÷ LPA do controlador (a raiz de `build.py:87`)

**O que dá errado.** `build.py:87`: `contagem_cvm[ano] = abs(f["lucro_liquido"] / lpa_cvm)`. As duas pontas vêm de bases **diferentes**:
- `lucro_liquido` ← CD_CONTA `3.11` = *"Lucro/Prejuízo **Consolidado** do Período"* → **inclui** os não-controladores.
- `lpa` ← `3.99.01.01` → é calculado sobre o lucro **atribuído aos controladores** (`3.11.01`).

`num_acoes = lucro_com_minoritários / LPA_sem_minoritários` → **inflado pela proporção de minoritários**. Em holdings e empresas com subsidiárias parcialmente detidas o erro é enorme; em empresa 100% detida é zero — o que explica por que só 41 de 104 tickers estouram.

E como `num_acoes` está inflado, `lpa_valuation = base/num_acoes` fica **deprimido** → **P/L parece alto** → "está caro". É um dos motores independentes do "80% da bolsa está cara".

**A regra correta, sem exceção:** o acionista compra o **controlador**. Todo o valuation roda na base do controlador:
- lucro = `3.11.01` (Atribuído a Sócios da Empresa Controladora)
- PL = `2.03` − `2.03.09` (Participação dos Não Controladores)
- num_acoes = **de uma fonte de contagem real**, nunca de uma razão.

Isso conserta ROE, LPA e o RIM (que precisa de book *do controlador*) num único movimento.

**Prevenção — o assert de reconciliação nº 1 (teria pego CGRA4 1018× e ITUB4 10M-vs-10B):**
```python
def assert_lpa_reconcilia(lucro_controlador, num_acoes, lpa_cvm, ticker, ano):
    if not (lpa_cvm and num_acoes): return
    implicito = lucro_controlador / num_acoes
    erro = abs(implicito - lpa_cvm) / abs(lpa_cvm)
    assert erro < 0.05, (
        f"{ticker}/{ano}: LPA implícito {implicito:.4f} vs CVM {lpa_cvm:.4f} "
        f"(erro {erro:.0%}). Escala ou base (controlador/consolidado) quebrada."
    )
```
Rode-o para **todo ticker × todo ano** na ingestão. Não deixe passar com warning: **falhe o ticker** (o v2.4 inteiro existe porque falhar silencioso é pior que não ter o ticker).

**Fase:** 1 (reconciliação) + 2 (ingestão).

---

### Pitfall 7 — LPA por lote de mil ações (o 1000× do ITUB4)

**O que dá errado.** Prática histórica brasileira (bancos e demonstrações antigas): *"lucro por lote de mil ações"*. Se a linha 3.99 vier nessa unidade, `lucro/LPA` dá uma contagem **1000× menor** → exatamente o "ITUB4 2019 = 10 milhões de ações em vez de 10 bilhões". Combina-se com o Pitfall 6 e vira ruído multiplicativo.

**A armadilha dentro da armadilha:** a "correção" tentadora é `if ticker in BANCOS_ANTIGOS: lpa *= 1000`. **Isso é um knob por ticker** — o overfit de novo, agora na ingestão. Não faça.

**Prevenção.** Trocar a **fonte**, não aplicar fator. `num_acoes` deve vir de uma contagem real (`sharesOutstanding` do Yahoo para o ano corrente; FCA/FRE da CVM para o histórico de ações em circulação), e o LPA da CVM vira **apenas a checagem** do Pitfall 6. Quando a reconciliação falhar e não houver contagem confiável para o ano → o ano é **excluído** com motivo, não chutado.
Corolário: `_fator_unit` (`build.py:24-37`) é uma heurística (`round(mediana(razões))`) construída sobre a contagem quebrada — quando `num_acoes` vier de fonte real, **delete a função**, não a conserte.

**Fase:** 2 (ingestão).

---

### Pitfall 8 — JCP: o código diz que inclui, e não inclui

**O que dá errado.** `cvm.py:169`:
```python
incluir = ds.str.contains("dividendo", na=False)
```
O docstring (linha 150) promete *"dividendos + JCP"*. O filtro casa **só a palavra "dividendo"**. Uma empresa que apresenta a linha da DFC como *"Juros sobre o Capital Próprio Pagos"* — sem a palavra "dividendo" — **tem o JCP inteiramente descartado**. São as 13 empresas do diagnóstico. Para um banco, o JCP é a maior parte da distribuição: o payout sai pela metade → o DDM/RIM subvaloriza → "está caro".

**Prevenção.**
```python
_PROVENTO = r"dividendo|juros sobre (o )?capital|jcp|jscp"
incluir = ds.str.contains(_PROVENTO, na=False, regex=True)
```
E o assert de reconciliação nº 2:
```python
def assert_proventos_reconciliam(div_cvm, dpa_yahoo, num_acoes, ticker, ano):
    """A DFC e o Yahoo têm que contar a mesma história (±30%). Divergência
    grande = uma das fontes está perdendo uma classe de provento."""
    if not (div_cvm and dpa_yahoo and num_acoes): return
    razao = div_cvm / (dpa_yahoo * num_acoes)
    assert 0.7 <= razao <= 1.5, f"{ticker}/{ano}: DFC/Yahoo = {razao:.2f}"
```
(Banda larga de propósito: o Yahoo historicamente perde JCP, então razão ~1,3-1,5 é *esperada* nos bancos; razão ~0,5 significa que **a CVM** perdeu — o bug atual.)

**Fase:** 1 (assert) + 2 (fix do regex).

---

### Pitfall 9 — JCP bruto vs. líquido: o DY exibido superestima a renda no bolso

**O que dá errado.** Três bases se misturam hoje sem rótulo:
1. A saída de caixa da DFC (`6.03`) é tipicamente **líquida de IRRF** para o JCP (a empresa retém na fonte). *(MEDIUM — varia por empresa/apresentação.)*
2. O histórico de proventos do Yahoo é, em geral, o **declarado (bruto)**.
3. O usuário PF recebe **líquido**.

Então: o **payout** (numerador CVM, líquido) fica subestimado, e o **DY** (numerador Yahoo, bruto) fica superestimado. Numerador e denominador de razões diferentes em bases diferentes — e nenhuma delas rotulada.

**E a regra mudou em 2026** *(HIGH — Lei 15.270/2025 + PLP 128/2025)*:
- **IRRF sobre JCP subiu de 15% para 17,5%**, vigente desde 01/jan/2026, **sem isenção de piso** (incide já no primeiro real).
- **Dividendos**: IRRF de **10%** sobre pagamentos de uma mesma empresa à mesma PF **acima de R$ 50 mil/mês** (incide sobre o total do mês, não só sobre o excedente). Abaixo disso, isentos.

O `ddm.tributacao_dividendos: 0.0` do `config.yaml:91` reflete o mundo pré-2026. Para o investidor PF típico do produto (abaixo de R$50k/mês), dividendos seguem isentos — mas **o JCP não**, e para um banco isso é a maior parte da distribuição. **Um DY de banco exibido bruto superestima a renda líquida em ~15-17% da parcela de JCP.** Num pagador majoritariamente-JCP, isso é ~1 a 1,5 p.p. de DY fantasma.

**Prevenção.**
- Carregar **dois campos distintos e explícitos**: `provento_bruto` e `provento_liquido_pf`. Nunca deixar uma função escolher implicitamente.
- **Convenção travada por teste:** *payout e todos os motores rodam em base BRUTA* (é a apropriação contábil do lucro — a única base coerente com o lucro do denominador). *O DY exibido ao usuário roda em base LÍQUIDA*, com o rótulo "líquido de IRRF sobre JCP (17,5%)".
```python
def test_bases_de_provento_nao_se_misturam():
    assert liquido <= bruto
    assert 1.0 <= bruto / liquido <= 1.20      # teto de 17,5% sobre 100% de JCP
def test_payout_usa_bruto_e_dy_usa_liquido():
    ...  # trava a convenção; senão ela volta a derreter
```
- Ver a taxa de JCP como **config**, não constante (`impostos.irrf_jcp: 0.175`) — a lei muda. **Não é um knob de calibração** (é um fato legal); marque-o como tal para não consumir orçamento do P1.5.

**Fase:** 2 (ingestão) + 5 (contrato de saída/rótulos).

---

### Pitfall 10 — Split ajustado duas vezes

**O que dá errado.** O `Close` do Yahoo **já vem ajustado por split, sempre**. O flag `auto_adjust` controla o ajuste por **dividendos** (`Adj Close`), não por split. `prices.py:71-111` (`_ajustar_por_split`) então **divide de novo** os preços antigos pelo fator cumulativo de split → preços históricos comprimidos duas vezes → um salto artificial na série ajustada → beta, `desempenho_relativo_6m` e todos os indicadores técnicos corrompidos em qualquer ticker com split na janela de 5 anos. *(Confiança HIGH na semântica do yfinance; o teste abaixo é definitivo e barato — rode-o antes de mexer.)*

**Prevenção — o teste que decide a questão em 3 linhas:**
```python
def test_yahoo_close_ja_vem_split_ajustado():
    """Escolha um ticker com split conhecido na janela de 5a."""
    hist = yf.Ticker(TICKER_COM_SPLIT).history(period="5y", auto_adjust=False)
    r = hist["Close"].pct_change().abs()
    assert r.max() < 0.35, "salto de split no Close cru -> o Yahoo NÃO ajusta (hipótese falsa)"
    # Se este teste PASSA, o Close já está ajustado e _ajustar_por_split deve ser DELETADA.
```
E o assert genérico anti-descontinuidade, que pega esta e toda a família (bonificação, grupamento, mudança de ticker):
```python
def assert_sem_salto_espurio(serie, ticker):
    r = np.log(serie).diff().abs()
    assert r.max() < 0.4, f"{ticker}: salto de {r.max():.0%} num dia — corporate action não tratada"
```

**Bug irmão, na mesma família (`build.py:113`):** `c.dividendos[ano] = dpa * c.num_acoes[ano]` multiplica um **DPA do Yahoo já retroajustado para a base de hoje** por uma **contagem histórica de ações da época (pré-split, menor)** → dividendos dos anos pré-split subestimados. Mesma classe: duas séries em bases temporais diferentes, multiplicadas. O assert do Pitfall 8 (razão DFC/Yahoo) o detecta.

**Fase:** 1 (assert) + 2 (deleção da função).

---

### Pitfall 11 — Mudança de exercício social, incorporações e o `g` que fita através de uma cratera

**O que dá errado.**
- Empresa que muda o encerramento do exercício publica um **período-tronco** (ex.: 9 meses). O código lê como "o ano" → lucro artificialmente baixo → contamina normalização, CAGR e payout. `cvm.py` **nunca lê `DT_INI_EXERC`/`DT_FIM_EXERC`**, então isso passa invisível.
- Incorporação/fusão: o consolidado **salta** de patamar. O ajuste log-linear do `g_historico` lê o salto como **crescimento estrutural** → `g` fantasma → valuation explosivo. E `num_acoes` salta junto (ações emitidas na operação).

**Prevenção — os asserts de reconciliação nº 3 e nº 4:**
```python
def assert_exercicio_anual(dt_ini, dt_fim, ticker, ano):
    dias = (dt_fim - dt_ini).days
    assert 355 <= dias <= 375, f"{ticker}/{ano}: exercício de {dias} dias — período-tronco"

def assert_clean_surplus(pl_ini, pl_fim, lucro, dividendos, ticker, ano):
    """ΔPL ≈ LL − Div. O resíduo é 'dirty surplus': OCI, recompras, aumento de
    capital, incorporação. É o assert mais poderoso do conjunto — é uma
    identidade contábil E a pré-condição de validade do RIM (Pitfall 12)."""
    residuo = (pl_fim - pl_ini) - (lucro - dividendos)
    razao = abs(residuo) / abs(pl_ini)
    assert razao < 0.10, (
        f"{ticker}/{ano}: dirty surplus de {razao:.0%} do PL — "
        f"OCI / recompra / aumento de capital / evento societário não modelado"
    )
```
- Evento societário detectado → **quebra a série**: o `g` histórico é ajustado só no segmento pós-evento (ou o ticker é marcado como "histórico descontínuo" e sai do valuation). **Nunca fite através da cratera.**

**Fase:** 1 (asserts) + 3 (primitivas/`g`).

---

## RIM na prática brasileira

### Pitfall 12 — Clean surplus não vale em banco brasileiro (e o RIM depende dele)

**O que dá errado.** O RIM é *exato* apenas sob **clean surplus** (ΔB = LL − Div). Em banco sob IFRS 9, uma fatia grande da carteira de títulos é **FVOCI**: a marcação a mercado vai **direto para o patrimônio**, sem passar pelo resultado. Some hedge accounting, ganhos/perdas atuariais e variação cambial de subsidiárias no exterior (CTA). Num choque de juros (2021-22), o OCI **derruba o book** enquanto o lucro parece normal → `B0` deprimido → **o RIM subvaloriza o banco**. Que é, literalmente, o sintoma que o v2.3 tentou consertar com um valor terminal e um cap de excesso de ROE.

**Isso reenquadra o marco: parte do "ITUB4 barato demais" pode ser dirty surplus, não calibração de `g`/Ke.** É uma hipótese *testável e barata* — e se ela for verdade, os knobs do v2.3 estavam mascarando um terceiro bug de dados.

**Prevenção.**
- O `assert_clean_surplus` do Pitfall 11 **é o teste de pré-condição do RIM**. Meça a razão de dirty surplus por ticker e reporte-a.
- Correção de livro-texto, sem knob novo: usar o **resultado abrangente (lucro abrangente / comprehensive income)** no RI, não o lucro líquido. Isso **restaura o clean surplus por construção**. Custo: mais uma conta na ingestão (DRA — Demonstração do Resultado Abrangente, disponível na DFP). **Recomendo fortemente** — é a correção certa e não gasta grau de liberdade.
- Se a DRA não for viável no orçamento: exiba a bandeira "clean surplus violado em X% do PL" ao lado do número do RIM. **Um número com a incerteza declarada é honesto; um número calibrado para esconder a incerteza é o v2.3.**

**Fase:** 2 (ingestão da DRA) + 4/5 (motor).

### Pitfall 13 — Book negativo, quase-zero, e a explosão do ROE

**O que dá errado.** `B0 ≤ 0` → RIM indefinido. `PL < 0` com lucro `< 0` → **ROE positivo** (dois negativos) → uma empresa em colapso pontua como alta qualidade e entra no ranking. `B0` minúsculo (BBSE3, VPA≈5,35) → RIM ancorado em quase nada, dominado inteiramente pelo valor terminal — o que motivou a rota *ad hoc* do Pitfall 2.

**Prevenção.**
```python
def test_roe_e_none_com_pl_nao_positivo():
    assert fundamentals.roe_medio(lucro=-100, pl_ini=-50, pl_fim=-60) is None  # nunca +2.0

# no motor:
if b0 is None or b0 <= 0: return Recusa("book não-positivo — RIM inaplicável")
if b0 / market_cap < 0.10: return Recusa("book imaterial — RIM é 95% valor terminal, sem poder de discriminação")
```
A segunda guarda é a que **teria recusado a BBSE3 honestamente**, em vez de inventar um motor para ela. Recusar é um resultado válido do produto. *"Este motor não fala sobre esta empresa"* é infinitamente mais honesto que um número construído para caber numa banda.

**Fase:** 4/5 (motor).

### Pitfall 14 — Ágio infla o book; a estatística robusta apaga a impairment

**O que dá errado.** Duas coisas que se compõem de forma perversa:
1. Um comprador serial carrega **goodwill** no book. O RIM cobra `Ke × B` sobre esse book → RI deprimido → o serial acquirer parece caro. (Direcionalmente correto! Ágio *é* capital empregado.)
2. Quando o ágio é **baixado (impairment)**, é uma perda grande e pontual. E aí a `base_normalizada` (mediana / média winsorizada) **trata a impairment como outlier e a remove**.

**O ponto profundo:** toda estatística "robusta" é uma decisão de modelagem com direção. Ela **apaga a má notícia grande e pontual** (impairment, provisão, acordo judicial) e **corta o crescimento** (Achado (a): −9,1% num crescedor de 10%). São dois vieses, em direções opostas, em populações diferentes — e nenhum dos dois foi jamais medido neste repo.

**Prevenção.**
```python
def test_normalizacao_nao_tem_vies_direcional():
    """Grupo de controle sintético: lucro estável + ruído simétrico.
    A base normalizada tem que ser NÃO-ENVIESADA."""
    rng = np.random.default_rng(0)
    vieses = []
    for _ in range(200):
        s = [100 * (1 + rng.normal(0, 0.15)) for _ in range(10)]
        vieses.append(norm.base_normalizada(s, anos_media=3) / 100 - 1)
    assert abs(np.median(vieses)) < 0.02, "a primitiva de normalização tem viés próprio"
```
E, para o ágio: **nenhum knob**. Uma **bandeira de qualidade de book** (`intangível / PL > 30%` → "book majoritariamente intangível — o RI é sensível a impairment"). Bandeira, não ajuste.

**Fase:** 3 (primitivas).

### Pitfall 15 — "NAV = 1º termo do RIM" é falso justamente onde o NAV importa

**O que dá errado.** O brief do marco afirma: *"`nav` é o 1º termo do RIM"*. Isso é verdade para o **NAV contábil** (B0). Mas o NAV que faz sentido para uma **holding** (ITSA4) é o valor de **mercado** das participações menos a dívida — e as participações estão no balanço por **equivalência patrimonial** (book do investido), não a mercado. Colapsar NAV em "primeiro termo do RIM" **importa o book contábil para dentro do único arquétipo em que o book contábil é a informação errada**, e joga fora o desconto de holding — que é o fenômeno inteiro que se quer capturar.

**Prevenção.** Ou (a) a holding tem uma rota própria que marca as participações a mercado (declarada **antes** de rodar a cesta, não depois de a ITSA4 falhar — Pitfall 2), ou (b) a holding é **explicitamente recusada** pelo produto ("valuation de holding exige marcar as participações a mercado; fora do escopo desta versão"). **Não** escolha a opção (c): deixar o RIM rodar sobre o book de equivalência e apresentar o número como se fosse um NAV. Também: revise a afirmação no PROJECT.md — ela está sendo carregada como se fosse um fato algébrico, e é uma meia-verdade dependente do arquétipo.

**Fase:** 5 (colapso dos motores) — decisão de carve-out **antes** da Fase 6.

### Pitfall 16 — Instrumentos híbridos de capital (IHCD/AT1) dentro do PL do banco

**O que dá errado.** Bancos brasileiros grandes (ITUB, BB) carregam instrumentos perpétuos elegíveis a capital nível 1. Sem obrigação contratual de pagar, eles são classificados como **patrimônio**, não passivo. Se `PL` inclui esse AT1, então: o **book do acionista ordinário está inflado**, o **ROE do ordinário está deprimido** e a remuneração paga a esses instrumentos **não é o dividendo do ordinário**. No RIM: `B0` grande demais, `RI = (ROE − Ke) × B` pequeno demais → **o banco de qualidade sai barato demais**. Que é, de novo, exatamente o sintoma que o v2.3 combateu com knobs. *(Confiança MEDIUM — precisa de confirmação nas notas explicativas das DFPs; mas é uma hipótese de custo baixo e retorno alto.)*

**Prevenção.** Verificar nas notas se `2.03` contém instrumentos híbridos; se contiver, `PL_comum = PL_controlador − IHCD`. **Verifique antes de calibrar qualquer coisa** — se este bug existe, calibrar por cima dele é reconstruir o v2.3.

**Fase:** 2 (ingestão), com uma investigação (spike) na Fase 1.

---

## MENORES (asserts baratos, alto retorno)

| # | O que dá errado | Prevenção | Fase |
|---|---|---|---|
| 17 | `_valor_conta` casa `DS_CONTA` por **substring** e pega `.iloc[0]` — linha arbitrária quando várias casam (ex.: "Lucro por Ação" casa básico e diluído) | `assert len(matches) == 1` ou ordem de preferência explícita; jamais `.iloc[0]` silencioso | 2 |
| 18 | `ESCALA_MOEDA` lido de `sub[...].iloc[0]` — assume escala única por empresa | `assert sub["ESCALA_MOEDA"].nunique() == 1` | 1 |
| 19 | `_consolidado_ou_individual` escolhe con/ind **por demonstração**; a DFC escolhe por um loop próprio → um ticker pode ler DRE individual + DFC consolidada (ROE/payout de bases mistas) | `assert` que a base escolhida (con/ind) é a MESMA para DRE/BPA/BPP/DFC no ano | 1 |
| 20 | Payout mistura **caixa** (DFC: dividendos *pagos* no ano t, boa parte declarados em t−1) com **competência** (DRE: lucro de t). Num crescedor, subestima o payout sistematicamente | Declarar a convenção e testá-la; ou usar dividendos **declarados** (DMPL) em vez de pagos. No mínimo: documentar o lag e não somar ao viés do Pitfall 6 sem saber | 2/3 |
| 21 | Ano fiscal ≠ ano-calendário → o `ano` da CVM não alinha com preço/dividendo do Yahoo | Assert do Pitfall 11 (`DT_FIM_EXERC`) + alinhar a data-base ao encerramento real | 2 |
| 22 | `data/cvm/*.zip` é cacheado sem carimbo de versão → o backtest não é reprodutível daqui a 6 meses | Sidecar com `data_download` + `ETag`; snapshot congelado é o artefato de teste, o ZIP não | 1 |

---

## Mapa: pitfall → fase

| Fase (proposta do marco) | Pitfalls que ela DEVE endereçar |
|---|---|
| **0 — Blindagem processual** *(NOVA — recomendo fortemente inserir antes de tudo)* | **1** (deletar o golden, lock de knobs, hook de commit), **5** (classificar os 448 testes, baseline golden-master, CI anti-afrouxamento) |
| **1 — Reconciliação de sanidade** | **6** (LPA reconcilia), **8** (proventos DFC↔Yahoo), **10** (sem salto espúrio), **11** (exercício anual + **clean surplus**), 18, 19, 22 — *estes 4 asserts são o coração do marco; o clean surplus é o mais valioso porque é simultaneamente detector de bug e pré-condição do RIM* |
| **2 — Ingestão correta** | **6** (base do controlador), **7** (deletar `_fator_unit`), **8** (regex do JCP), **9** (bruto/líquido + IRRF 17,5%), **10** (deletar `_ajustar_por_split`), **12** (ingerir a DRA), **16** (IHCD), 17, 20, 21 |
| **3 — Primitivas sem viés** | **14** (teste de viés direcional da normalização), **11** (`g` não fita através de evento societário) |
| **4 — `g` e depois Ke** | **1.3** (teste de invariância à inflação — é o teste que *define* esta fase) |
| **5 — Um motor + contrato** | **13** (recusar book não-positivo/imaterial), **15** (holding: rota própria ou recusa explícita), **2** (carve-outs declarados AGORA, por escrito, antes da Fase 6) |
| **6 — Revalidação com hold-out** | **1.2** (distribuição + jackknife), **2** (zero exceções no hold-out), **3** (âncora não-circular; aposentar o consenso como gate), **4** (PIT ou não fazer), **5.4** (canário de sensibilidade) |

---

## Orçamento de graus de liberdade — resposta direta

**Pergunta: para uma cesta de 40-60 tickers, qual o número máximo defensável de knobs livres? A proposta é 3.**

**3 está certo. Mas o orçamento tem que contar o que o v2.3 não contou.**

A heurística clássica de ≥10 observações por parâmetro livre daria 4-6 knobs para 40-60 tickers. Eu recomendo **ficar em 3**, por três razões específicas deste projeto:

1. **As observações não são independentes.** 4 bancos brasileiros grandes são ~1 observação e meia (mesmo país, mesmo ciclo de crédito, mesma Selic, exposição correlacionada). Uma cesta de 50 tickers da B3 tem talvez 15-20 graus de liberdade **efetivos** — a estrutura de fatores comum (Selic, câmbio, commodity) domina. 3 knobs sobre ~15-20 observações efetivas já é o limite do defensável.
2. **O alvo é ruidoso.** O "fair value" é ele próprio uma variável com erro grande (Pitfall 3). Calibrar muitos parâmetros contra um alvo ruidoso é ajustar o ruído por definição.
3. **Os 3 knobs precisam ser econômicos, não numéricos.** Cada um tem que ter um significado defensável fora do modelo — `g_cap` = teto de crescimento nominal da economia; `erp` = prêmio de risco de equity; `excesso_sustentavel` = durabilidade de moat. Se você não consegue defender o valor **sem mencionar um ticker**, não é um knob: é um resíduo (`config.yaml:237` — *"Move ITUB4 ~R$2"* — é o exemplo canônico do que **não** é uma justificativa).

**O que mais consome o orçamento (e não aparece no `config.yaml`):**
- toda **rota/carve-out** criada depois de ver um resultado = 1 DoF (BBSE3);
- toda **escolha de estatística** feita olhando o resultado = 1 DoF (`roe_terminal_stat: mediana|media`);
- todo **mecanismo novo** adicionado porque a cesta não fechou = 1 DoF (valor terminal do RIM);
- toda **exceção documentada** que converte reprovação em aprovação = 1 DoF (`excecao_nota`).

Por essa contagem, o v2.3 gastou **~8 DoF sobre 4 observações** — razão de 0,5 observação por grau de liberdade. Um modelo com essa razão **interpola**; ele não generaliza, e não *pode* generalizar, independentemente de quanto cuidado se tome depois.

**Regra operacional para o v2.4:** os 3 knobs numéricos vão para o `calibracao.lock.yaml` (P1.5); **toda escolha estrutural é congelada e commitada ANTES de o hold-out ser aberto**; o hold-out roda **uma vez**; e o resultado é reportado **como saiu**. Se o hold-out reprovar, a resposta permitida é *"o modelo tem esta limitação"* ou *"a estrutura está errada, volte à Fase 3"* — **nunca** *"mexa no knob"*. Um hold-out que você pode re-rodar depois de tunar não é um hold-out; é uma segunda cesta de treino com nome de gente séria.

---

## Confiança

| Área | Nível | Por quê |
|---|---|---|
| Bugs de código citados (build.py:87, cvm.py:169, normalizacao.py:69-75, prices.py:71-111) | **HIGH** | Lidos no repo; o haircut e as bandas foram **executados**, não estimados |
| Aritmética das bandas do gate (2/4 real, não 4/4) | **HIGH** | Calculado dos fixtures do próprio repo |
| Prazo da DFP (3 meses) | **HIGH** | Resolução CVM 80/2022, art. 22, IV — fonte oficial |
| IRRF: JCP 17,5% e dividendos 10% acima de R$50k/mês em 2026 | **HIGH** | Lei 15.270/2025 + PLP 128/2025; corroborado por Receita Federal e PwC |
| `auto_adjust` do yfinance não controla split (Close já vem split-adjusted) | **HIGH** | Semântica documentada; **e o teste do Pitfall 10 decide em 3 linhas — rode antes de mexer** |
| DFC 6.03 do JCP vir líquida de IRRF | **MEDIUM** | Varia por empresa/apresentação; verificar em 3-4 bancos antes de fixar a convenção |
| IHCD/AT1 dentro do PL de bancos BR | **MEDIUM** | Alta plausibilidade contábil, mas **não verificado nas notas** — trate como spike da Fase 1, não como fato |
| Disciplina de overfitting / DoF / pre-registration | **HIGH** | Conhecimento consolidado (hold-out, researcher DoF, garden of forking paths), aplicado a evidência específica deste repo |
| Circularidade do consenso de sell-side | **MEDIUM-HIGH** | Argumento estrutural sólido; a magnitude do viés de ancoragem no BR não foi medida aqui |

## Sources

- [Resolução CVM 80 (texto consolidado)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/001/resol080consolid.pdf) — prazo de entrega da DFP (3 meses do encerramento do exercício, emissor nacional)
- [Portal Dados Abertos CVM — DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp) — natureza do dataset (regenerado; sem garantia point-in-time)
- [Receita Federal — recolhimento do IRRF sobre lucros e dividendos](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/dezembro/receita-federal-orienta-sobre-os-procedimentos-para-o-recolhimento-do-imposto-de-renda-retido-na-fonte-sobre-lucros-e-dividendos)
- [PwC — Tributação de dividendos: Lei nº 15.270](https://www.pwc.com.br/pt/thinking-about-taxes/tax-intelligence/2025/tax-intelligence-ed-48-tributacao-de-dividendos.pdf) — IRRF 10% acima de R$50k/mês; JCP a 17,5% desde 01/01/2026
- Código do próprio repositório (fonte primária dos achados críticos): `src/analista/ingest/build.py`, `src/analista/ingest/cvm.py`, `src/analista/ingest/prices.py`, `src/analista/core/normalizacao.py`, `src/analista/core/fundamentals.py`, `config.yaml`, `tests/test_backtest_bancos.py`, `tests/fixtures/fair_values_bancos.yaml`
