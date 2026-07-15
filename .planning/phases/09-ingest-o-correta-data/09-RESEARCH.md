# Phase 09: Ingestão correta (DATA) — Research

**Researched:** 2026-07-15
**Domain:** Conserto dos dados de ENTRADA do pipeline CVM+Yahoo (JCP, base do controlador, `num_acoes`, split, DY), sem tocar em método
**Confidence:** HIGH para o mapa de código e o mecanismo de regressão (lido linha a linha + herdado do `08-RESEARCH.md`, que foi MEDIDO); MEDIUM para o site exato do DATA-04 (a referência de linha do requisito está desatualizada); MEDIUM para o texto legal do DATA-05.

---

## User Constraints

> **Não existe `09-CONTEXT.md`** (a fase ainda não passou por `/gsd-discuss-phase`). As restrições
> abaixo vêm do `ROADMAP.md` (Phase 9 "NÃO fazer") e do `CLAUDE.md`, e têm a mesma autoridade que
> decisões travadas até que um CONTEXT as substitua.

### Locked (do ROADMAP — "NÃO fazer nesta fase")
- **NÃO tocar em primitiva, `g`, `Ke` ou motor.** Esta fase move dados de entrada, e só. Misturar
  conserto de dado com conserto de método torna impossível atribuir a variação de `V` a uma causa.
- **NÃO "reajustar" um knob** porque um número ficou feio depois do conserto de dado — a variação
  por ticker (−48% a +193%) é o conserto funcionando.
- **NÃO comprar dado pago** para resolver a base de ações — viola o custo zero (constraint do produto).
  Só CVM + Yahoo Finance + Banco Central.

### Locked (do CLAUDE.md — regra "suíte verde" v2.4)
- `pytest` verde = **0 failed**, `golden_nivel` em quarentena (deselecionados por `addopts`), 2 xfailed,
  1 skipped. Golden de nível que quebra é **DELETADO na Fase 10, não atualizado** — não é problema desta fase.
- **Orçamento de knobs = exatamente 3 graus de liberdade** (`ERP`, `n_fade`, `PIB_real`), em
  `calibracao.lock.yaml`. **Esta fase não toca nenhum knob** — logo o lock fica intocado.
- **NUNCA** afrouxar tolerância, marcar `xfail`/`skip` casual ou deletar assert para a suíte ficar verde.
- Uma justificativa de knob **nunca menciona um ticker** (hook `.githooks/commit-msg` + teste `-k justificativa`).
- `pytest tests/arquivo.py` **não funciona** (dispara `CLASSIFICACAO ORFA`); use `-k <expr>`.
- Todo teste novo precisa de entrada em `tests/classificacao.yaml` **no mesmo commit** — senão a coleta quebra.

### Claude's Discretion
- Estratégia de escala do `composicao_capital` (detecção milhares×unidades), forma exata do conserto do
  `_fator_unit`, e como DATA-05 declara a base do DY (aplicar IRRF vs. rotular "bruto").
- Mecânica exata do DATA-06 (ver a decisão de arquitetura na seção própria — precisa de confirmação).

### Deferred (OUT OF SCOPE)
- Exibir selo de confiança na tela (Fase 13). O veredito `c.confianca` continua interno.
- Cindir as funções mistas (gap WR-04) — antes da Fase 10.
- Deflator no `dpa_recorrente` / séries longas de dividendo (Future Requirements).

---

## Phase Requirements

| ID | Descrição (REQUIREMENTS.md:114-144) | Suporte da pesquisa |
|----|-------------------------------------|---------------------|
| DATA-01 | JCP capturado nas 13 empresas que hoje o perdem (`cvm.py` filtro estreito). BRSR6: payout 10,3% → 55,9% | Insumo pronto: `_distribuicoes_proventos_amplo` (cvm.py:183) já existe e casa "dividendo OU juros sobre capital". Prova: SAN-03 sinal (a). §DATA-01 |
| DATA-02 | `lucro` e `PL` na base do **controlador**, não consolidado com minoritários | Insumos prontos: `lucro_controlador` (3.11.01) e `pl_nao_controladores` já são lidos (cvm.py:289/297). Prova: SAN-04. §DATA-02 |
| DATA-03 | `num_acoes` deixa de ser `LL/LPA`; fallback usa `impliedSharesOutstanding` (ON+PN) | Insumo herdado: `composicao_capital` (per-ano, no ZIP) + `impliedSharesOutstanding` batem <0,3% em 5/5. **4 armadilhas medidas.** Prova: SAN-01 + SAN-02. §DATA-03 |
| DATA-04 | Remover duplo ajuste de split (degrau artificial de 13% no ITUB4) | ⚠️ **Referência de linha DESATUALIZADA.** O site exato precisa ser RE-MEDIDO. §DATA-04 |
| DATA-05 | DY reflete IRRF de 17,5% sobre JCP (Lei 15.270/2025) OU declara que é bruto | `multiples.dividend_yield` = DPA/Preço, sem imposto. Requisito de rótulo/contrato. §DATA-05 |
| DATA-06 | Snapshot de teste regenerado (ITUB4 2019 com bilhões, não milhões) | ⚠️ **Decisão de arquitetura pendente** — o snapshot sujo é evidência congelada. §DATA-06 |

---

## Summary

Esta fase é o oposto da Fase 8: a Fase 8 construiu os **detectores** e provou (medindo) exatamente
onde cada bug mora, no nível da conta CVM. Esta fase **conserta os dados de entrada** e prova o
conserto fazendo os detectores da Fase 8 pararem de disparar, ticker a ticker. Quase todo o insumo
já existe no `CompanyData` — a Fase 8 leu de propósito as contas que a Fase 9 vai promover a fonte de
verdade (`lucro_controlador`, `pl_nao_controladores`, `proventos_filtro_amplo`, `implied_shares_outstanding`,
`splits`), sem consertar nada. O trabalho da Fase 9 é **trocar a fonte** que os motores consomem, dos
campos sujos para os campos limpos que já estão ali ao lado.

Quatro dos seis requisitos têm o site de código **confirmado** e o insumo de conserto **já presente**
(DATA-01, DATA-02, DATA-03, DATA-05). Dois têm ressalvas que o planner precisa encarar antes da
primeira task: **DATA-04** aponta para uma linha (`prices.py:71-111`) que **não contém mais** a lógica
de split (o módulo foi reescrito nas Fases 3-4) — o "degrau de 13% no ITUB4" precisa ser **re-medido**
para localizar o site atual; e **DATA-06** ("regenerar o snapshot") colide com o fato de que o snapshot
sujo é a **evidência congelada** contra a qual o progresso é medido, e os testes de detecção da Fase 8
**precisam** dele sujo — a régua e o objeto medido não podem ser o mesmo arquivo.

**Primary recommendation:** Ataque na ordem DATA-01 → DATA-02 → DATA-03 (JCP, controlador, `num_acoes`),
porque cada conserto apaga um subconjunto de flags do baseline e o progresso é imediatamente visível na
monotonicidade. Trate DATA-04 como um **spike de localização** antes de virar task de conserto. Resolva
a arquitetura do DATA-06 (snapshot limpo novo + evidência suja preservada) **antes** de rodar o primeiro
conserto — senão a monotonicidade não consegue enxergar o progresso.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| JCP no filtro de proventos (DATA-01) | `ingest/cvm.py` (`_distribuicoes_proventos` → `dividendos_distribuidos`) | — | O campo `c.dividendos` que os motores consomem nasce aqui. A gêmea ampla já existe. |
| Base do controlador (DATA-02) | `ingest/build.py` (`montar_empresa`) | `ingest/cvm.py` (leitura já feita) | `c.lucro_liquido`/`c.patrimonio_liquido` são populados no build; a decisão de qual base usar é do build. |
| `num_acoes` correto (DATA-03) | `ingest/build.py` (`contagem_cvm`, `_fator_unit`) | `ingest/cvm.py` (nova leitura de `composicao_capital`) | O `num_acoes` que os motores consomem é derivado no build; a contagem oficial vem de uma leitura nova na CVM. |
| Duplo split (DATA-04) | ⚠️ **a localizar** — provavelmente `ingest/prices.py` OU o consumidor histórico | `core/` (motor cíclico/histórico?) | A referência do requisito está obsoleta; ver §DATA-04. |
| Base do DY (DATA-05) | `core/multiples.py` (`dividend_yield`) OU `report/presentation.py` (rótulo) | — | Cálculo vs. rótulo — a discricionariedade decide onde. |
| Snapshot regenerado (DATA-06) | `scripts/` + `tests/fixtures/` + `tests/helpers_sanidade.py` | `tests/test_sanidade_*` | Decisão de arquitetura de fixtures; ver §DATA-06. |

---

## 🔴 O mecanismo de regressão — como uma flag "vira verde" (leia ANTES de planejar)

Este é o coração da fase. Sem entendê-lo, o executor conserta o dado e **não vê progresso nenhum**,
ou pior, quebra os testes de detecção.

**Três artefatos, três papéis distintos:**

1. **`tests/fixtures/snapshot_sanidade_2026-07-14.yaml`** (104 tickers, dado **SUJO**, congelado).
   O cabeçalho do gerador (`scripts/capturar_snapshot_sujo.py`) diz literalmente: *"a evidência
   intocada do dado sujo, contra a qual a Fase 9 mede o conserto... **NÃO regenerar nesta fase.**"*
   Congela séries CRUAS por ano: `lucro_liquido`, `lucro_controlador`, `pl_nao_controladores`,
   `lpa_cvm`, `dividendos`, `proventos_filtro_amplo`, `num_acoes`, `dpa_por_ano`, `market_cap`,
   `implied_shares_out`, `splits`, `origem_num_acoes`.

2. **`tests/fixtures/baseline_sanidade.yaml`** (o BASELINE DOS SUJOS, 104 tickers). Gerado por
   `scripts/gerar_baseline_sanidade.py` rodando `aplicar_sanidade` sobre o snapshot sujo. Registra,
   por ticker, `confianca` + a lista de `{check, bucket}`. **É a régua do progresso da Fase 9.**

3. **Os testes** que ligam os dois:
   - `test_sanidade_checks.py` (10 testes, `contrato`) — lê o snapshot sujo e afirma que os checks
     **DISPARAM** nos alvos (GOAU4/CGRA4 SAN-01; ITUB4/BRSR6 SAN-02; BRSR6 SAN-03; MRFG3/CSNA3/ALUP11/EQTL3 SAN-04).
     **Estes testes PROVAM que os detectores funcionam — precisam do dado SUJO para ficarem verdes.**
   - `test_sanidade_baseline.py::test_baseline_de_sujos_so_encolhe` (`invariante`) — a
     **monotonicidade**: `pares_hoje ⊆ pares_baseline`. Se um par `(ticker, check)` sumir, foi o
     conserto; se **ressuscitar**, é regressão → vermelho.

**A pegadinha central (VERIFICADA no código):** hoje, TANTO a geração do baseline QUANTO a medição de
"hoje" (`_pares_e_buckets_de_hoje`, test_sanidade_baseline.py:65) leem o **mesmo** snapshot sujo via
`hs.carregar_snapshot_sanidade()`. Logo, no fim da Fase 8, `pares_hoje == pares_baseline` — a
monotonicidade é uma **tautologia** e mostra **zero progresso**. Para a Fase 9 provar o conserto,
a medição de "hoje" precisa ler **dado produzido pelo código consertado** — e isso é a decisão de
arquitetura do DATA-06 (ver seção própria). **Consertar o código sem resolver isso não move a régua.**

**Como cada conserto aparece na régua** (par que DEVE sumir de `pares_hoje`):

| Conserto | Par que some | Medido hoje (08-RESEARCH) |
|----------|--------------|----------------------------|
| DATA-01 (JCP) | `("BRSR6", "SAN-03")` e as ~13 empresas | `Σ amplo / Σ estreito` = 5×–25×; vira ≈1 |
| DATA-02 (controlador) | `("MRFG3"/"CSNA3"/"ALUP11"/"EQTL3", "SAN-04")` | razão `3.11/3.11.01` = 0,75–2,97×; vira ≈1 |
| DATA-03 (num_acoes) | `("GOAU4"/"CGRA4", "SAN-01")` + `("ITUB4"/"BRSR6", "SAN-02")` | SAN-01 2,97×/0,001×; SAN-02 ÷1000/×205.000 |

⚠️ **`test_bucket_nao_muda_sem_a_flag_sumir`**: para um par que **persiste**, o bucket tem de ser
igual. Um conserto PARCIAL (a flag ainda dispara mas o bucket mudou) fica **vermelho**. Corolário: os
consertos têm de fazer a flag **DESAPARECER limpa**, não "empurrar a escala". Se você reduziu a doença
mas não a curou, isso é vermelho — e é o comportamento desejado.

---

## Deep-dive por requisito

### DATA-01 — JCP perdido no filtro estreito da CVM

**Onde está o código hoje (VERIFICADO):**
- `cvm.py:155-180` — `_distribuicoes_proventos`: `incluir = ds.str.contains("dividendo")` (linha 175).
  Alimenta `fundamentos_do_ano["dividendos_distribuidos"]` (cvm.py:286) → `dist_cvm` (build.py:95) →
  `c.dividendos` (build.py:131-132). **É a fonte suja que os motores consomem.**
- `cvm.py:183-214` — `_distribuicoes_proventos_amplo` (a GÊMEA, criada na Fase 8): idêntica, exceto
  `incluir = ds.str.contains("dividendo|juros sobre.*capital", regex=True)` (linha 209). Alimenta
  `proventos_filtro_amplo` — hoje só o detector do SAN-03 a consome.

**A correção de dado (não de método):** ampliar o filtro que alimenta `c.dividendos` para casar
`"dividendo" OU "juros sobre capital"` — a fonte continua a CVM (`_distribuicoes_proventos`), **não
se troca para o Yahoo**. A gêmea ampla já é a implementação correta; a decisão é apontar
`dividendos_distribuidos` para a lógica ampla (fundir as duas, ou trocar a chamada da cvm.py:286).

**Armadilha (MEDIDA, 08-RESEARCH §Achado 1/§R-02):**
- A direção do bug é o **contrário** do que o comentário antigo afirmava: quem PERDE o JCP é a CVM
  (filtro estreito), não o Yahoo. O comentário já foi corrigido na Fase 8 (build.py:120-130).
- Os 4 grandes bancos **escapam por acidente** — filam numa linha `"Dividendos E Juros sobre o Capital
  Próprio Pagos"` que já casa `"dividendo"`. Ao ampliar o filtro, **verifique que essa linha não é
  contada em dobro**: se existir simultaneamente uma linha `"Dividendos..."` E uma `"Juros sobre..."`,
  o `.sum()` (cvm.py:214) soma as duas — o que é correto (são proventos distintos), mas confirme que
  não há uma única linha casando ambos os termos e sendo somada uma vez só (é o caso, mas prove).
- `c.dividendos` também alimenta o **SAN-05 (clean surplus)** e o **payout**. Ao capturar o JCP, o
  BRSR6 sobe de payout 10,3% → 55,9% — isso é o conserto, não um problema.

**Como provar que virou verde:** SAN-03 tem **dois sinais** (sanidade.py:179). O sinal (a) —
`Σ proventos_filtro_amplo / Σ dividendos` (interno à CVM, imune a `num_acoes`) — é o teste de
regressão direto: hoje `> LIMIAR_SAN03_JCP (1,10)` para BRSR6; após o conserto, `dividendos` inclui o
JCP → razão ≈ 1 → a flag `("BRSR6", "SAN-03")` **some de `pares_hoje`**. O sinal (b) (reconciliação
CVM↔Yahoo) some junto quando o `num_acoes` também estiver correto (DATA-03).

---

### DATA-02 — Base do controlador vs. consolidado com minoritários

**Onde está o código hoje (VERIFICADO):**
- `build.py:83-84` — `c.lucro_liquido[ano] = f["lucro_liquido"]`, onde `lucro_liquido` é o
  **consolidado** (`3.11`/`3.13`/`3.09`, cvm.py:253-258).
- `build.py:85-89` — `c.patrimonio_liquido[ano]` = `2.03`/`2.08` (PL consolidado, **inclui**
  minoritários).
- Insumos limpos **já lidos** (Fase 8): `f["lucro_controlador"]` (3.11.01, cvm.py:289) e
  `f["pl_nao_controladores"]` (2.03.09/2.07.02/2.08.09, cvm.py:297) → `c.lucro_controlador`,
  `c.pl_nao_controladores` (build.py:99-101).

**A correção de dado:** fazer a base de valuation usar o controlador —
`c.lucro_liquido = lucro_controlador` (quando presente) e `c.patrimonio_liquido -= pl_nao_controladores`.
Os campos de diagnóstico já existem; a Fase 9 os promove a fonte.

**Armadilha (MEDIDA, 08-RESEARCH §Achado 4):**
- `lucro_controlador`/`pl_nao_controladores` são **None** para a maioria dos tickers (só existem quando
  a empresa consolida subsidiárias com minoritários). O conserto **precisa de fallback ao consolidado**
  quando a linha do controlador estiver ausente — senão quebra as ~empresas single-entity limpas.
- **CSNA3 é sinal invertido:** minoritários com lucro (+0,496 bi) e controlador com prejuízo (−2,002 bi).
  Trocar para o controlador muda o **sinal** do lucro do CSNA3 — o que é o conserto correto, mas vai
  mexer no `V` dele bastante. Não é bug; é a doença sendo removida.
- **Consistência lucro↔PL:** ao mover o lucro para o controlador, **mova o PL junto** (subtraia
  minoritários). Deixar um no consolidado e outro no controlador cria uma NOVA base cruzada — a doença
  que o SAN-04 detecta, por outro caminho.

**Como provar que virou verde:** SAN-04 (sanidade.py:237) compara `razao = LL / LL_controlador` no
último ano com ambos. Hoje flaga GOAU4 (2,967×), EQTL3 (1,492×), ALUP11 (1,426×), CSNA3 (0,752×,
`sinal_invertido`). Após o conserto, `lucro_liquido == lucro_controlador` → `razao = 1` → as flags
`("...", "SAN-04")` **somem**. Confirme que os bancos limpos (ITUB4 minoritários 4,9%; BBAS3 2,3%)
continuam sem flag (já estão abaixo do `LIMIAR_SAN04 = 0,10`).

---

### DATA-03 — `num_acoes` sem base cruzada (o coração da dispersão, 41/104 tickers)

**Onde está o código hoje (VERIFICADO):**
- `build.py:91-93` — `contagem_cvm[ano] = abs(f["lucro_liquido"] / lpa_cvm)`. A causa-raiz: `lpa_cvm`
  vem de `3.99.01.01` (cvm.py:282) sem validar escala nem semântica (ITUB4 2019 = 2780 = ×1000; BRSR6
  2020 = 310.665 = lucro alocado à classe, não LPA).
- `build.py:25-38` — `_fator_unit`: **CORROMPIDO** (08-RESEARCH §Achado 8). Devolve **5** para ALUP11
  (verdadeiro = 3), porque calcula a mediana de `contagem_cvm/acoes_yahoo` sobre a contagem já inflada
  pelos minoritários. A divisão excessiva **mascara** o erro — por isso o SAN-01 **não** pega a ALUP11
  (ela é do SAN-04).
- `build.py:113-118` — fallback: `acoes_atual = dm.num_acoes = info["sharesOutstanding"]` (prices.py:158),
  que é **só a classe negociada**, não ON+PN. Insumo limpo já lido: `dm.implied_shares_outstanding`
  (prices.py:164, ON+PN).

**A correção de dado:** parar de derivar `num_acoes` de `LL/LPA`. Fonte por ano = a contagem oficial da
CVM (`dfp_cia_aberta_composicao_capital_{ano}.csv`, **dentro do ZIP que o projeto já baixa** —
`QT_ACAO_TOTAL_CAP_INTEGR − QT_ACAO_TOTAL_TESOURO`), com `impliedSharesOutstanding` como âncora/validador
do último ano. Requer uma **leitura nova** em `cvm.py` (o `composicao_capital` não é lido hoje).

**4 armadilhas MEDIDAS (08-RESEARCH §Achado 4/§R-09) — todas obrigatórias:**
1. **`impliedSharesOutstanding`, NUNCA `sharesOutstanding`.** O `sharesOutstanding` é só a classe (ITUB4
   5,4 bn = só PN); o `impliedSharesOutstanding` é ON+PN (11,02 bn). A contagem da CVM é ON+PN. Comparar
   com o errado dá falso ~2× em toda empresa com PN.
2. **`composicao_capital` é chaveado por `CNPJ_CIA`, não por `CD_CVM`** — exige join via
   `cad_cia_aberta.csv` (que o projeto já baixa).
3. **A escala do `composicao_capital` é INCONSISTENTE entre empresas:** ITUB4 e BRSR6 vêm em **MILHARES**
   de ações; GOAU4/CGRA4/CSNA3/EQTL3/ALUP11/MRFG3 vêm em **unidades**. Usá-lo cru **reintroduz a doença
   do ×1000 por outro caminho.** Detecte a escala cruzando com `impliedSharesOutstanding` do último ano
   (bate <0,3% em 5/5) e aplique o fator inferido à série inteira.
4. **`_fator_unit` precisa ser refeito ou aposentado junto.** Ele está corrompido (devolve 5 p/ ALUP11).
   Com a contagem oficial (988.880.601 / 329.626.866 = exatamente 3,000), o fator de unit vira derivável
   corretamente — ou dispensável, se a contagem já vier na base certa. Não deixe o `_fator_unit` velho
   consumindo a contagem nova.

⚠️ **Nota de série temporal:** `impliedSharesOutstanding` é um valor **único** (snapshot atual), não uma
série por ano. A série por ano tem de vir do `composicao_capital` (que É por ano no ZIP). Use o
`impliedSharesOutstanding` só como âncora do último ano e validador de escala.

**Como provar que virou verde:** **SAN-01** (nível) — hoje GOAU4 2,969×, CGRA4 0,001×; após o conserto
`num_acoes[ult] × preço / market_cap ≈ 1` → flags `("GOAU4"/"CGRA4", "SAN-01")` somem. **SAN-02** (salto)
— hoje ITUB4 2019 ÷1000, BRSR6 2020/21 ×205.000; após o conserto a série não tem saltos artificiais →
flags `("ITUB4"/"BRSR6", "SAN-02")` somem. Este é o conserto de maior alavancagem (41 dos 104 tickers).

---

### DATA-04 — Duplo ajuste de split (⚠️ referência de linha OBSOLETA)

**Estado do código (VERIFICADO — a referência do requisito NÃO bate mais):**
- O requisito aponta `prices.py:71-111`. **Hoje essas linhas são o dataclass `DadosMercado` e
  `_retornos_mensais`** — não a lógica de split. O módulo `prices.py` foi **reescrito nas Fases 3-4**
  (git: `c4c4b7a feat(04-01): _ajustar_por_split`, `8964d55 fix(03): serie_precos nominal`).
- A lógica de split atual vive em `prices._ajustar_por_split` (prices.py:93-133): usa
  `auto_adjust=False` (Close **nominal**, não ajustado), deriva o ajuste da coluna `"Stock Splits"` e
  produz `dm.ohlc_ajustado`. Esse frame é consumido **só pelos indicadores técnicos** (`core/indicators.py`,
  Fase 5), **não pelo motor de valuation**. `serie_precos` já é nominal (fix da Fase 3).

**Consequência para o plano:** o "degrau artificial de 13% no ITUB4" **precisa ser re-medido** para
localizar o site atual — a referência do requisito é de antes dos refactors. Hipótese com MEDIUM
confiança: o degrau nasce da interação entre a série `num_acoes` da CVM (que carrega os degraus REAIS
de bonificação, porque `_ler_demonstracao` filtra `ORDEM_EXERC == "ÚLTIMO"` e nunca captura a
reapresentação retroativa do LPA — 08-RESEARCH §Achado 5) e alguma série de preço/por-ação ajustada por
split, causando double-count da bonificação de ~13% do ITUB4 (a de 2024→2025, 1,1286×). O 13% ≈ o
produto dos splits de 2025 (1,1 × 1,03 = 1,133).

**Recomendação:** trate DATA-04 como um **spike de localização** (medir onde o degrau de 13% aparece
hoje, comparando a série por-ação histórica do ITUB4) **antes** de virar task de conserto. É o único
DATA sem site confirmado e sem assert SAN dedicado — **não escreva a task de conserto às cegas sobre a
linha 71-111.** Pode estar parcialmente mitigado pelos refactors das Fases 3-4; confirme por medição.

**Como provar:** não há assert SAN direto para o duplo split (o SAN-02 cobre `num_acoes`, não preço).
A prova terá de ser um teste novo específico (ex.: a série por-ação do ITUB4 não tem degrau na
fronteira da bonificação) — o que exige primeiro localizar o site. Registre isso como risco de escopo.

---

### DATA-05 — Base do DY (IRRF sobre JCP)

**Onde está o código hoje (VERIFICADO):**
- `multiples.dividend_yield` (multiples.py:97-99): `DY = DPA / Preço`, sem imposto. `DPA` vem de
  `c.dividendos` (proventos brutos). O DY aparece no header (`presentation.header_dy`), no comparador e
  nos alertas (`report.py:590/648`, "DY > 15%").

**A correção (rótulo OU cálculo):** o requisito aceita **duas** saídas — aplicar o IRRF de 17,5% sobre a
**parcela de JCP** dos proventos, OU **declarar explicitamente que o DY é bruto**. A parcela de JCP é
obtível (a diferença entre o filtro amplo e o estreito, ou as linhas `6.03.04` da DFC).

**Armadilha:**
- Separar JCP de dividendo por ano exige a decomposição da DFC — não é trivial, e a Fase 9 não deve
  inflar escopo. A saída de **menor risco** é **declarar o DY como bruto** (um rótulo em
  `presentation.py`/glossário), que satisfaz o requisito sem introduzir uma conta de imposto frágil.
- ⚠️ **Verificar a lei antes de cravar a alíquota.** O requisito cita Lei 15.270/2025 (IRRF 17,5% sobre
  JCP, vigente 01/01/2026). **Não confirmei o texto legal nesta sessão** (ver Assumptions A2) — e há a
  reforma da tributação de dividendos a partir de 2026 que pode mexer na base do próprio dividendo. Se
  optar por aplicar imposto, valide a alíquota e a vigência com fonte oficial primeiro.

**Como provar:** não há assert SAN. A prova é um teste de contrato novo (o header/glossário declara a
base; se aplicar imposto, um teste do valor líquido vs. bruto). Sem literal de ticker + número não-trivial
no mesmo teste (BLIND-04a).

---

### DATA-06 — Regenerar o snapshot (⚠️ DECISÃO DE ARQUITETURA)

**O conflito (VERIFICADO no código):** DATA-06 pede "regenerar o snapshot de teste". Mas:
- `snapshot_sanidade_2026-07-14.yaml` é a **evidência congelada do dado sujo** — o gerador diz "NÃO
  regenerar". Os testes de detecção (`test_sanidade_checks.py`) **precisam dele sujo** para provar que
  os checks disparam. Regenerá-lo limpo faz `test_san01_flaga_os_tickers_de_escala_quebrada` **falhar**
  (GOAU4 deixaria de disparar).
- Mas a monotonicidade (`_pares_e_buckets_de_hoje`) lê **esse mesmo arquivo** — então, para a régua
  enxergar progresso, "hoje" tem de vir do **dado consertado**.
- A régua (baseline) e o objeto medido (snapshot sujo) e o objeto consertado (dado novo) **não podem ser
  o mesmo arquivo.**

**Recomendação (precisa de confirmação do usuário / discuss-phase):**
1. **Preservar** `snapshot_sanidade_2026-07-14.yaml` (sujo) e `baseline_sanidade.yaml` (sujo)
   **intocados** — são a régua e a evidência. `test_sanidade_checks.py` continua ligado a eles (verde).
2. **Gerar** um snapshot NOVO com o código consertado (ex.: `snapshot_sanidade_2026-07-XX.yaml`,
   "limpo") e apontar **apenas a medição de "hoje"** (`_pares_e_buckets_de_hoje`) para ele.
3. A monotonicidade `pares_hoje (limpo) ⊆ pares_baseline (sujo)` então **encolhe** → verde + progresso
   mensurável. Nenhum golden é "atualizado".

Isso exige **desacoplar** o loader: hoje `test_sanidade_checks` e `_pares_e_buckets_de_hoje` usam o
mesmo `hs.carregar_snapshot_sanidade()`. O planner precisa de dois caminhos (sujo p/ detecção, limpo p/
"hoje"). **Alternativa** (mais invasiva): reescrever `_pares_e_buckets_de_hoje` para rodar o pipeline
LIVE — rejeitada, porque perde o offline/determinismo que é o valor do snapshot.

**Sobre o "outro" snapshot (`snapshot_bancos_2026-07-12.yaml`):** é o que o texto do DATA-06 descreve
("ITUB4 com 10 milhões de ações... dá verde nos 448 testes"). Consumido por `test_backtest_bancos.py`,
`test_motores.py` e `helpers_blindagem.py`. **Todos os asserts de nível do ITUB4 nele (32,88 / bandas
30-40) são `golden_nivel` → quarentenados** (VERIFICADO em `classificacao.yaml:61-63,333-349`) e serão
**DELETADOS na Fase 10**, não aqui. Se a Fase 9 regenerar esse snapshot (ITUB4 → bilhões), só os
quarentenados quebram (a suíte fica verde, pois estão deselecionados); os testes `invariante`/`contrato`
que o consomem são **relacionais** (determinismo, rótulo de motor, `rim_1 == rim_2`) e devem sobreviver.
**Confirme com o usuário se o `snapshot_bancos` deve ser regenerado nesta fase ou deixado para a Fase 10**
(onde o golden 32,88 é formalmente deletado) — regenerar aqui é permitido mas antecipa uma quebra
quarentenada.

---

## Runtime State Inventory

Fase de conserto de dados (não é rename), mas há **estado congelado e artefatos derivados** relevantes:

| Categoria | Encontrado | Ação |
|-----------|-----------|------|
| Fixtures congelados (sujos) | `snapshot_sanidade_2026-07-14.yaml` + `baseline_sanidade.yaml` — evidência + régua | **Preservar.** DATA-06: gerar arquivo NOVO limpo, não sobrescrever (ver §DATA-06). |
| Fixture dos bancos | `snapshot_bancos_2026-07-12.yaml` — ITUB4 dirty; consumido por backtest/motores/blindagem | Decisão pendente (regenerar aqui vs. Fase 10). Só quebra golden quarentenado. |
| Cache CVM | `data/cvm/dfp_cia_aberta_{2015..2025}.zip` + `cad_cia_aberta.csv` — completo, 11 anos | Nenhuma. O `composicao_capital` do DATA-03 **já está dentro** desses ZIPs. |
| `data/ticker_map.json` | 104 tickers (CD_CVM). Também alimenta `tickers_conhecidos()` do BLIND-04a | MRFG3 (404 no Yahoo, virou MBRF) segue como caso vivo do SAN-06. **Não** remover (efeito colateral no BLIND-04a). |
| Hook do BLIND-05 | `.githooks/commit-msg` — bloqueia `config.yaml` + fixture/teste no MESMO commit | Fase 9 **não toca `config.yaml`** → hook não dispara. Mas ao commitar fixtures novos, garanta que `config.yaml` não vá junto. `core.hooksPath` é estado local por clone. |
| `classificacao.yaml` | 466 entradas; teste sem entrada quebra a COLETA | Cada teste novo (DATA-04/05/06) precisa de linha **no mesmo commit** (R-10 da Fase 8). |
| Cálculo/knobs | `calibracao.lock.yaml` (3 graus) | **Intocado** — DATA não é valuation. Se algum knob se mover, saiu do escopo. |

---

## Project Constraints (from CLAUDE.md)

- **Suíte verde v2.4:** 0 failed, `golden_nivel` quarentenados, 2 xfailed, 1 skipped. Golden de nível que
  quebra é **deletado na Fase 10**, não atualizado nesta fase.
- **Orçamento de 3 knobs** (`ERP`, `n_fade`, `PIB_real`) em `calibracao.lock.yaml` — **esta fase não
  mexe em nenhum**; o lock fica intocado. Não há justificativa de knob a escrever.
- **NUNCA** afrouxar tolerância / `xfail` casual / trocar `xfail` por `skip` / deletar assert para ficar verde.
- **Justificativa de knob nunca cita ticker** — irrelevante aqui (sem mudança de knob), mas o hook
  `commit-msg` está ativo: não commite `config.yaml` junto de fixture/teste.
- `pytest tests/arquivo.py` **quebra** (`CLASSIFICACAO ORFA`) — rode com `-k <expr>`.
- Todo teste novo precisa de entrada em `tests/classificacao.yaml` **no mesmo commit** (senão a coleta quebra).
- Idioma: PT-BR; comentário só quando o "porquê" não é óbvio; validação só nas bordas.

---

## Don't Hand-Roll

| Problema | Não construa | Use | Por quê |
|----------|--------------|-----|---------|
| Contagem oficial de ações | Parser de eventos societários / scraping de RI | `composicao_capital` (dentro do ZIP CVM já baixado) + `impliedSharesOutstanding` | Já grátis, já no disco; batem <0,3% em 5/5. Custo zero. |
| Filtro de JCP | Nova varredura da DFC | `_distribuicoes_proventos_amplo` (cvm.py:183, já existe) | A Fase 8 já escreveu e testou o filtro amplo correto. |
| Base do controlador | Recalcular minoritários | `lucro_controlador`/`pl_nao_controladores` (já lidos, cvm.py:289/297) | Insumos prontos; só promover a fonte. |
| Detecção de split | Calendário de bonificações próprio | `c.splits` (yfinance `.splits`, já congelado no snapshot) | Já existe e é grátis. |
| Validação de dados | `pandera` / `great-expectations` | Os 5 checks de `core/sanidade.py` (já existem) | **Proibido** (custo zero); os checks SÃO o teste de regressão. |
| Snapshot/fixture | Mock manual de yfinance | Reaproveitar `capturar_snapshot_sujo.py` (forma provada) | Padrão já no repo, offline, determinístico. |

**Key insight:** a tentação nesta fase **não** é hand-rollar uma lib — é **consertar demais** ou
**consertar no lugar errado**. Todo insumo de conserto (JCP amplo, controlador, implied shares, splits)
**já está no `CompanyData`**, colocado ali de propósito pela Fase 8. O trabalho é **trocar a fonte que
os motores leem**, não inventar cálculo novo. E resistir a mexer em `g`/`Ke`/motor quando um `V` ficar
feio depois do conserto (é o conserto funcionando).

---

## Common Pitfalls

### Pitfall 1: consertar o código e não ver progresso (a régua olha o arquivo errado)
**O que dá errado:** o executor conserta cvm.py/build.py, roda a suíte, e a monotonicidade continua
tautológica (dirty-vs-dirty) — nenhuma flag some. Conclui que o conserto não funcionou.
**Como evitar:** resolver o DATA-06 (medição de "hoje" sobre dado limpo) **antes** de rodar o primeiro
conserto. Ver §mecanismo de regressão.

### Pitfall 2: quebrar os testes de detecção ao limpar o snapshot congelado
**O que dá errado:** regenerar `snapshot_sanidade_2026-07-14.yaml` limpo → `test_sanidade_checks` falha
(os checks deixam de disparar no que agora é dado limpo).
**Como evitar:** o snapshot sujo é evidência **congelada**; gere um arquivo NOVO para "hoje", preserve o sujo.

### Pitfall 3: base cruzada NOVA no DATA-02
**O que dá errado:** mover o lucro para o controlador mas deixar o PL no consolidado (ou vice-versa) —
cria exatamente a base cruzada que o SAN-04 detecta, por outro caminho.
**Como evitar:** mover lucro E PL juntos para a base do controlador; fallback ao consolidado quando a
linha do controlador estiver ausente.

### Pitfall 4: reintroduzir o ×1000 pelo `composicao_capital` cru (DATA-03)
**O que dá errado:** ITUB4/BRSR6 vêm em MILHARES no `composicao_capital`; usar cru dá ×1000.
**Como evitar:** detectar a escala cruzando com `impliedSharesOutstanding` do último ano e aplicar à série.

### Pitfall 5: `_fator_unit` corrompido consumindo a contagem nova
**O que dá errado:** manter o `_fator_unit` velho (devolve 5 p/ ALUP11) sobre a contagem oficial nova →
divide por 5 em vez de 3.
**Como evitar:** refazer ou aposentar `_fator_unit` no mesmo conserto do DATA-03.

### Pitfall 6: escrever a task do DATA-04 sobre a linha errada
**O que dá errado:** `prices.py:71-111` não contém mais a lógica de split; um "conserto" ali não
endereça o degrau de 13%.
**Como evitar:** spike de localização primeiro (medir onde o degrau aparece hoje).

---

## Environment Availability

Herdado e confirmado do `08-RESEARCH.md` (medido 2026-07-14, mesma máquina):

| Dependência | Requerida por | Disponível | Versão | Observação |
|-------------|--------------|-----------|--------|------------|
| Python | tudo | ✓ | 3.14.5 | |
| yfinance | DATA-03/04/05 | ✓ | 1.4.1 | `impliedSharesOutstanding`, `.splits` confirmados |
| pandas | tudo | ✓ | 3.0.3 | |
| PyYAML | snapshot/baseline | ✓ | — | já usado |
| pytest | testes | ✓ | — | config em `pyproject.toml` |
| Cache CVM | DATA-01/02/03 | ✓ | 2015–2025 | **`composicao_capital` + `cad_cia_aberta.csv` já estão nos ZIPs** — o insumo do DATA-03 é 100% offline |
| Rede Yahoo | regenerar snapshot | ✓ (parcial) | — | MRFG3 = 404 (never-raise/SAN-06) |

**Nenhuma dependência nova.** DATA-03 não precisa de fonte paga — a contagem oficial já está no disco.

---

## Test Map (nyquist_validation = false, mas os testes são o entregável)

`workflow.nyquist_validation = false`. Mas, como na Fase 8, os asserts SÃO a prova do conserto. Não há
Wave 0 de framework (pytest já configurado). Novos testes precisam de entrada em `classificacao.yaml`.

| Req | Prova de "virou verde" | Onde | Comando | Novo? |
|-----|------------------------|------|---------|-------|
| DATA-01 | `("BRSR6","SAN-03")` some de `pares_hoje`; payout 55,9% | monotonicidade + snapshot limpo | `pytest -k baseline` | reusa Fase 8 |
| DATA-02 | `("CSNA3"/"ALUP11"/"EQTL3"/"MRFG3","SAN-04")` somem | monotonicidade | `pytest -k baseline` | reusa Fase 8 |
| DATA-03 | `("GOAU4"/"CGRA4","SAN-01")` + `("ITUB4"/"BRSR6","SAN-02")` somem | monotonicidade | `pytest -k baseline` | reusa Fase 8 |
| DATA-04 | teste novo: série por-ação do ITUB4 sem degrau na bonificação | a definir (após spike) | `pytest -k split` | ❌ novo + classificação |
| DATA-05 | teste novo: DY declara a base (bruto) ou aplica IRRF | contrato | `pytest -k dy_base` | ❌ novo + classificação |
| DATA-06 | monotonicidade encolhe (hoje limpo ⊆ baseline sujo); detecção segue verde | baseline + checks | `pytest -k sanidade` | rewire do loader |

**Sampling:** por commit `pytest -k sanidade`; por wave `pytest -m ""` (tudo, incl. quarentenados sob
demanda `-m golden_nivel`); gate da fase: suíte verde v2.4 (0 failed).

---

## Assumptions Log

| # | Claim | Seção | Risco se errado |
|---|-------|-------|-----------------|
| A1 | O "degrau de 13% no ITUB4" ainda existe pós-refactor das Fases 3-4 | DATA-04 | **Médio** — pode já estar mitigado; por isso a recomendação é spike de localização, não conserto direto. |
| A2 | Lei 15.270/2025 = IRRF 17,5% sobre JCP, vigente 01/01/2026 | DATA-05 | **Médio** — copiado do requisito, **não verifiquei o texto legal**. Se aplicar imposto, valide antes; a saída "declarar bruto" contorna o risco. |
| A3 | Regenerar `snapshot_bancos` só quebra golden quarentenado | DATA-06 | **Baixo** — a classificação foi VERIFICADA (`classificacao.yaml`); os `invariante`/`contrato` são relacionais. |
| A4 | Ampliar o filtro de JCP não conta linha em dobro nos 4 bancos | DATA-01 | **Baixo** — as linhas "Dividendos" e "Juros" são distintas; confirme por medição no diff. |
| A5 | `impliedSharesOutstanding` é snapshot único (não série); a série por ano vem do `composicao_capital` | DATA-03 | **Baixo** — medido na Fase 8; o `composicao_capital` é per-ano no ZIP. |

---

## Open Questions (RESOLVED)

1. **DATA-06 — arquitetura dos fixtures (a mais importante).**
   - Sabemos: o snapshot sujo é evidência congelada; a monotonicidade precisa de "hoje" limpo; os
     testes de detecção precisam do sujo.
   - Falta decidir: gerar snapshot limpo novo + desacoplar o loader (recomendado) vs. rodar live.
   - Recomendação: snapshot limpo novo, preservar sujo, apontar só `_pares_e_buckets_de_hoje` para o limpo.
   - **RESOLVED:** preservar snapshot sujo + baseline; gerar snapshot limpo novo; desacoplar loader via `carregar_snapshot_sanidade(path=CAMINHO_SNAPSHOT_LIMPO)` (ver plano 09-05).

2. **DATA-06 — o `snapshot_bancos` é regenerado nesta fase ou na 10?**
   - Regenerar aqui (ITUB4 → bilhões) é permitido e só quebra golden quarentenado; deixar p/ Fase 10
     mantém a antecipação de quebra fora de escopo. **Confirmar preferência.**
   - **RESOLVED:** NÃO regenerar nesta fase; deferido à Fase 10 (ver plano 09-05).

3. **DATA-04 — onde está o degrau de 13% hoje?**
   - Requer spike de localização (a linha do requisito está obsoleta). Recomendação: medir antes de planejar a task.
   - **RESOLVED:** spike de localização primeiro (a ref prices.py:71-111 está obsoleta), depois o conserto (ver plano 09-03).

4. **DATA-05 — aplicar IRRF ou declarar bruto?**
   - Menor risco: declarar bruto (rótulo). Aplicar imposto exige decompor JCP por ano + validar a lei.
     **Discricionário; recomendo declarar bruto salvo decisão do usuário.**
   - **RESOLVED:** declarar DY BRUTO no rótulo/glossário, sem calcular IRRF especulativo (ver plano 09-04).

---

## Sources

### Primária (HIGH — lido linha a linha nesta sessão)
- `src/analista/ingest/cvm.py`, `build.py`, `prices.py` — sites de DATA-01/02/03/04
- `src/analista/core/sanidade.py`, `fundamentals.py`, `multiples.py` — checks, CompanyData, DY
- `tests/test_sanidade_baseline.py`, `test_sanidade_checks.py`, `test_sanidade_snapshot.py`,
  `test_sanidade_pipeline.py`, `helpers_sanidade.py`, `classificacao.yaml` — mecanismo de regressão
- `scripts/capturar_snapshot_sujo.py`, `gerar_baseline_sanidade.py` — geração de fixtures
- `.githooks/commit-msg`, `calibracao.lock.yaml` — restrições de blindagem
- `git log` de `prices.py` — confirmação de que DATA-04 foi refatorado (Fases 3-4)

### Secundária (HIGH — medido na Fase 8, herdado)
- `.planning/phases/08-sanidade-dos-dados-san/08-RESEARCH.md` — todos os números (§Achado 1-8, §R-01..R-10)
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `CLAUDE.md`

### Não verificado (MEDIUM/LOW)
- Texto da Lei 15.270/2025 (DATA-05) — copiado do requisito, não confirmado em fonte oficial (A2)
- Site atual do duplo split / degrau de 13% (DATA-04) — hipótese, precisa de medição (A1)

---

## Metadata

**Confidence breakdown:**
- **Sites de código DATA-01/02/03:** HIGH — lidos linha a linha; insumos de conserto já presentes.
- **Mecanismo de regressão (como a flag vira verde):** HIGH — o fluxo snapshot→baseline→monotonicidade
  foi lido em `test_sanidade_baseline.py`, `helpers_sanidade.py` e os geradores.
- **DATA-04:** MEDIUM — referência de linha obsoleta; recomendação é spike, não conserto direto.
- **DATA-05:** MEDIUM — cálculo localizado, mas o texto legal não foi verificado.
- **DATA-06:** HIGH no diagnóstico do conflito; MEDIUM na recomendação (precisa de confirmação do usuário).
- **Restrições de blindagem (lock/hook/classificacao):** HIGH — lidas diretamente.

**Research date:** 2026-07-15
**Valid until:** ~2026-08-15 (30 dias). O cache CVM é imutável; o `.splits`/`marketCap` do Yahoo são
móveis (daí o snapshot congelado). Os sites de código são estáveis até a Fase 9 começar a editá-los.

---

## RESEARCH COMPLETE
