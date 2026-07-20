# Phase 14: Validação honesta (VAL) - Research

**Researched:** 2026-07-20
**Domain:** Validação estatística honesta de um motor de valuation (hold-out estratificado + jackknife + prova de ordem por git), sem recalibrar
**Confidence:** HIGH nos itens medidos por execução (VAL-01, quotas, buckets, lentes); MEDIUM na estatística do LIMIAR(n) e no mecanismo git (design, não medição)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01..D-11 — NÃO re-litigar)
- **D-01:** âncora `fair_value` = lentes Graham+Bazin (não consenso sell-side). `fair_values_bancos.yaml` NÃO é substrato.
- **D-02:** `fair_value = [min(Graham,Bazin), max(Graham,Bazin)]` entre as lentes **definidas**; divergência preservada como sinal de incerteza.
- **D-03:** difícil sem **nenhuma** lente → fica na cesta, **sem** razão V/FairValue, **fora** do jackknife (degradação reportada, jamais exclusão silenciosa).
- **D-04:** VAL-01 (ITUB4=R$37,22) vive **só** no teste soberano closed-form; dentro da cesta ITUB4 usa Graham+Bazin como todo mundo.
- **D-05:** seleção determinística por regra escrita ANTES; zero cherry-pick; arquétipos vivos: FINANCEIRA, PAGADORA_MADURA, CICLICA, CRESCIMENTO, CONCESSAO_FINITA.
- **D-06:** 10 difíceis por 4 baldes (P/B<1, prejuízo recente, payout>100%, book pequeno), disjuntos da cota, regra determinística por extremos.
- **D-07:** reporta por estrato + pooled; CONCESSAO_FINITA isolado (não contamina pooled); arquétipo com <6 no universo usa todos e **MARCA** cota não atingida.
- **D-08:** VAL-07 = **não fazer** backtest temporal, documentar o porquê de forma durável.
- **D-09:** dois commits datados (1: fair_value+LIMIAR; 2: v_modelo) + teste de ordem por git.
- **D-10:** `LIMIAR_JACKKNIFE_PP` vira função de `n`, pré-registrada no Commit 1, independente dos valores reais.
- **D-11:** PASS = (1) VAL-01 verdadeiro **E** (2) nenhum ticker load-bearing **E** (3) nenhuma exceção salvou ticker. Mediana = **detector** reportado, **nunca** alvo/gate.

### Claude's Discretion (o foco desta pesquisa)
1. Regra determinística exata de seleção (D-05) + limiares dos 4 baldes (D-06).
2. Regra de combinação/degradação quando só uma lente vale ou nenhuma (D-02/D-03).
3. Forma fechada/simulação de `LIMIAR_JACKKNIFE_PP(n)` (D-10) e mecanismo exato do teste de ordem (D-09).
4. Onde registrar VAL-07 (D-08) de forma durável.
5. Divisão em waves e ordem dos dois commits load-bearing.

### Deferred Ideas (OUT OF SCOPE)
- Backtest temporal PIT real (v2.5+). Motor nav/SOTP para holdings. Score BSD por arquétipo. Reforma visual da tela / exibição do veredito na UI.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VAL-01 | Caso do livro passa: ITUB4 inputs Cap.17 → V≈R$37,22 (região 35–39) | **VERIFICADO por execução**: injetando Ke=0,1248 em `a.ke` e deixando `g_terminal=g_cap` fluir, `motores.rim` devolve **V=R$38,69 ∈ [35,39]**. Hoje (Ke engine=15,86%) dá R$24,38. Ver §VAL-01. |
| VAL-02 | Cesta estratificada ≥6/arquétipo + 10 difíceis | **VERIFICADO**: distribuição real dos 104 e contagem dos 4 baldes medidas. CRESCIMENTO=4 (<6, marcar). Ver §Cesta. |
| VAL-03 | fair_value commitado ANTES do v_modelo; git prova ordem | Mecanismo `git blame --line-porcelain` (author-time por linha) verificado como viável. Ver §Ordem por git. |
| VAL-04 | Roda uma única vez; falhou → re-arquiteta | Regra de processo; sem knob tocado. Ver §Escopo negativo. |
| VAL-05 | Métrica V/FairValue, distribuição+jackknife, nunca V/preço, nunca ticker==R$ | Guard AST BLIND-04 já existe; fixture é razão, não nível. Ver §Fixture. |
| VAL-06 | Matar `excecao_nota` — nenhuma exceção salva ticker | **LOCALIZADO**: `excecao_nota` NÃO está em `report.py`; vive em `backtest.py:179` (passthrough) + `test_backtest_bancos.py`. Ver §VAL-06. |
| VAL-07 | Decisão PIT tomada e escrita, ou não fazer | Registrar ADR em `.planning/` + comentário em `backtest.py`. Ver §VAL-07. |
</phase_requirements>

## Summary

Esta é uma fase de **validação e subtração**, não de construção. Todo o motor (RIM único, `a.ke`, `g_cap`) já existe e roda; a Fase 14 (a) prova que o motor reproduz o caso do livro, (b) monta um hold-out estratificado honesto contra âncoras independentes (Graham+Bazin), (c) mede robustez por jackknife com um limiar pré-registrado, (d) mata o `excecao_nota`, e (e) grava a decisão de não-fazer-backtest-temporal. **Zero knobs de valuation tocados** — o orçamento fica em 3 graus (`calibracao.lock.yaml`).

Rodei o motor ao vivo sobre o snapshot dos 104 tickers para responder empiricamente aos 5 itens de discrição — a maioria das incertezas do CONTEXT.md agora tem número, não hipótese. **Duas descobertas mudam o plano:** (1) VAL-01 **passa** com Ke do livro injetado (V=R$38,69 ∈ [35,39]) — o gap de hoje é inteiramente o Ke da engine (15,86%) vs o do livro (12,48%); (2) a reconstrução do snapshot **não popula `eh_concessionaria`**, então uma reutilização ingênua classifica os ~19 utilities como CICLICA e deixa o estrato CONCESSAO_FINITA **vazio** — o plano tem de replicar `build.py:168` na montagem da cesta.

**Primary recommendation:** Duas waves com dois commits load-bearing. Wave A: (i) teste soberano VAL-01 closed-form (injeta Ke=0,1248, assere V ∈ [35,39]); (ii) função `LIMIAR_JACKKNIFE_PP(n)` derivada de um null neutro por Monte-Carlo com seed fixo; (iii) **Commit 1** = `holdout_v24.yaml` só com `fair_value` (faixa Graham+Bazin) + `LIMIAR(n)`, montado por regra determinística que replica `eh_concessionaria`; (iv) mata `excecao_nota`; (v) ADR do VAL-07. Wave B: **Commit 2** = preenche `v_modelo` rodando `report.analisar_acao`; acorda `test_nenhum_ticker_e_load_bearing`; adiciona o teste de ordem por `git blame`. Prova final por execução ao vivo, não por suíte verde.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| VAL-01 closed-form (inputs livro → V) | `motores.rim` (engine pura) | `report.analisar_acao` (injeção de `a.ke`) | O V é do RIM; VAL-01 só troca o insumo Ke, não a fórmula. |
| Âncora fair_value (Graham/Bazin) | `core/lentes.py` | `backtest._graham/_bazin` | Lentes puras, independentes do modelo e do preço. |
| Estratificação da cesta | `core/arquetipo.classificar` | montador do fixture (novo, em `scripts/` ou teste) | Classificação é fonte única; a cesta só a consome. |
| Jackknife / robustez | `tests/helpers_blindagem.mediana_jackknife` | `test_blindagem_meta` | Já existe, puro; a fase só alimenta o substrato e o LIMIAR. |
| Prova de ordem | git (metadado) | teste na suíte (`git blame`) | A ordem é um fato de história, não de código. |
| Decisão VAL-07 | doc `.planning/` (ADR) | comentário em `backtest.py` | Requisito satisfeito por decisão escrita durável. |

## VAL-01 — Critério de aceite soberano (o achado mais importante)

**Estado medido HOJE** (snapshot `snapshot_sanidade_limpo_2026-07-15.yaml` + `config.yaml`, via `report.analisar_acao`):

```
ITUB4: arquetipo=financeira, motor=rim
  a.ke = 0.1586   (15,86%)  ← a engine calcula via CAPM local (rf=10,5% + β_blume × ERP)
  g_alto = g_fund = 0.0959  (9,59% ≈ 10,24% do livro)
  g_estavel (g_cap terminal) = 0.0728  (7,28%)
  vpa0 = 19.00,  roe0(val) = 0.1798,  payout = 0.4669,  retencao = 0.5331
  V (intrinseco_motor) = R$ 24,38     ← NÃO é R$16,13 (esse era pré-Fases 11–13); hoje é 24,38
```
`[VERIFIED: execução local 2026-07-20]`

**Injetando os inputs do livro** (`Ke=0,1248`) direto em `motores.rim`, mantendo `g_terminal=g_cap=0,0728`:

```
motores.rim(vpa0=19.0, roe0=0.1798, ke=0.1248, retencao=0.5331,
            n=10, excesso_sustentavel=0.045, g_terminal=0.0728, roe_terminal=roe0)
  → V = R$ 38,69   ∈  [35, 39]   ✅ PASSA
```
`[VERIFIED: execução local 2026-07-20]`

**Conclusões acionáveis para o planner:**
1. **VAL-01 já passa por construção** com o Ke do livro injetado — a fórmula RIM da engine reproduz o caso do livro dentro da região MS. Não há bug de fórmula a consertar; o gap de hoje (R$24,38) é **inteiramente o Ke**: a engine estima 15,86% para o ITUB4, o livro usa 12,48%.
2. **O teste soberano NÃO deve re-derivar Ke.** Ele deve **injetar** `Ke=0,1248` (constante do livro, Cap.17) e assertar `V ∈ [35, 39]`. Caminho recomendado: chamar `report.analisar_acao(c, cfg)` com um `cfg` cujo CAPM force `a.ke=0,1248` **ou** — mais limpo e sem depender do caminho CAPM — chamar `motores.rim(...)` diretamente com os insumos derivados do ITUB4 e `ke=0.1248`. A segunda opção é a mais fiel ao "closed-form dos inputs do livro → output".
3. **`g` do livro (10,24%) entra pela retenção×roe, não por um parâmetro `g`.** `motores.rim` **não tem** argumento de g de fase explícita — o crescimento da janela é `roe0×retencao ≈ 9,58%`, que já bate o `g` do livro. O único `g` explícito do RIM é `g_terminal` (= `g_cap` = 7,28%). Não invente um parâmetro `g_alto` no RIM.
4. **Assertar a REGIÃO [35,39], não o nível 37,22.** Um assert `== 37,22` seria golden de nível e cairia no BLIND-04a (ticker+número→assert). O teste soberano deve assertar `35 <= V <= 39` (um intervalo, não um ponto) — e o literal do ticker deve viver num helper fora de função `test_` (padrão já usado em `empresa_itub4`, helpers_blindagem.py:640) para não disparar o detector.

**Landmine:** o valor exato (38,69 vs 37,22) depende de `excesso_sustentavel=0,045` (knob **travado** no lock) e de `roe0` vindo do dado. Não mexer nesses para "chegar em 37,22" — isso seria recalibrar. A região [35,39] é o gate; 38,69 já passa. `[ASSUMED→needs-confirm: que o planner aceite região, não ponto]`

## Cesta estratificada (D-05/D-06/D-07) — contagens reais

**Distribuição por arquétipo dos 104 tickers, `arquetipo.classificar` ao vivo:**

| Cenário | ciclica | concessao_finita | financeira | pagadora_madura | crescimento |
|---------|---------|------------------|-----------|-----------------|-------------|
| **Sem** `eh_concessionaria` (reuso ingênuo de `helpers_sanidade`) | 65 | **0** ❌ | 17 | 15 | 7 |
| **Com** `eh_concessionaria` (replica `build.py:168`) | 53 | **19** ✅ | 17 | 11 | **4** ❌ |
`[VERIFIED: execução local 2026-07-20]`

### LANDMINE CRÍTICA (D-05/D-07): `eh_concessionaria` não é reconstruído
`tests/helpers_sanidade.carregar_snapshot_sanidade` **não popula** `c.eh_concessionaria` (fica no default `False`). O hard-route de CONCESSAO_FINITA (`arquetipo.py:163`) nunca dispara → os ~19 utilities (Energia/Saneamento/Água/Gás) caem em CICLICA, **divergindo da produção** e deixando o estrato do carve-out **vazio**. O montador da cesta **DEVE** replicar `build.py:168`:
```python
setores_concessionaria = ("Energia", "Saneamento", "Água", "Gás")
c.eh_concessionaria = any(t.lower() in (c.setor or "").lower() for t in setores_concessionaria)
```
Isto não é opcional nem discricionário: sem ele a cesta não valida o roteamento real do app, e o estrato isolado do D-07 não existe. Membros CONCESSAO_FINITA (com o fix): ALUP11, AURE3, CMIG3/4, CPFE3, CPLE3/6, CSMG3, EGIE3, ELET3/6, ENEV3, ENGI11, EQTL3, SAPR11, SAPR4, SBSP3, TAEE11, TRPL4.

### Cota ≥6 (D-07): quem fica abaixo
Com `eh_concessionaria` corrigido, **CRESCIMENTO tem só 4 nomes no universo** (GRND3, MULT3, RADL3, WEGE3). É o único estrato < 6 → usar os 4 e **MARCAR** "cota mínima não atingida" (D-07, honesto). Os outros 4 estratos têm folga. CONCESSAO_FINITA (19) reporta como **seu próprio estrato**, fora do pooled (D-07).

### Regra determinística de seleção (D-05) — proposta concreta
Para cada estrato, ordenar por um campo objetivo **presente no snapshot** e pegar os N maiores. Campos disponíveis por ticker: `market_cap`, `patrimonio_liquido[ult]`, `preco_atual`, séries completas. Recomendação: **ordenar por `market_cap` desc** (proxy de liquidez/robustez de dado, presente em todos), pegar os **6 primeiros** de cada estrato (todos os 4 de CRESCIMENTO), desempate alfabético por ticker (determinístico). Escrever a regra e o snapshot-hash no cabeçalho do YAML e no Commit 1 → o `git log` prova que não foi montada olhando o resultado. Alternativa: ordenar por `patrimonio_liquido` (book) — mas `market_cap` é mais próximo de "liquidez". `[ASSUMED→needs-confirm: campo de ordenação]`

### Os 10 "difíceis" (D-06) — contagens reais dos 4 baldes
| Balde | n candidatos | Observação |
|-------|-------------|------------|
| P/B < 1 | **32** | folga enorme |
| prejuízo recente (≤0 nos últimos 3 anos) | **19** | AURE3, AZUL4, BEEF3, BRFS3, BRKM5, COGN3, CSAN3, CSNA3, DOHL4, HAPV3, JBSS3, MGLU3, MRFG3, MRVE3, RAIL3, RAIZ4, SUZB3, TIMS3, USIM5 |
| payout > 100% | **2** | AGRO3 (1,01), AURE3 (1,47) — **balde raso** |
| book pequeno | vários; **2 com book negativo** | menores: AZUL4 (−29,0), BRKM5 (−16,5), TIMS3 (0,0), DOHL4 (0,70), KEPL3 (0,77), LEVE3 (0,86)… (valores de PL em R$ bi) |
`[VERIFIED: execução local 2026-07-20]`

**Implicações de design do D-06:**
- **payout>100% só tem 2 candidatos.** Uma regra "≥N por balde" não fecha nesse balde. Regra robusta: pegar **todos** os do balde raso (2) e completar até ≥10 pelos extremos dos baldes fartos (ex.: 4 de P/B<1 + 2 de prejuízo + 2 de book pequeno + 2 de payout). Definir "prejuízo recente" = **lucro ≤ 0 em qualquer um dos últimos 3 anos** (medido). "book pequeno" = **menor `patrimonio_liquido[ult]`** (ordinal, não threshold mágico — evita 4º grau de liberdade). Desempate alfabético.
- **Difíceis podem coincidir com a cota do estrato** — D-06 exige **disjuntos** (os difíceis SOMAM). Garantir por construção: montar as cotas primeiro, depois escolher difíceis **fora** do conjunto já selecionado.

## Regra de combinação / degradação das lentes (D-02/D-03) — contagens reais

Rodando Graham (`√(22,5·LPA·VPA)`, exige LPA>0 e VPA>0) e Bazin (`DPA_médio_5a / 0,06`, exige DPA>0) sobre os 104:

| Situação | n | Regra para o fixture |
|----------|---|----------------------|
| **ambas** definidas | 93 | `fair_value = [min(G,B), max(G,B)]` (faixa completa, D-02) |
| **só Bazin** (Graham indefinido: prejuízo/VPA≤0) | 7 | AURE3, BRKM5, CSAN3, CSNA3, HAPV3, MRVE3, TIMS3 → `fair_value = [Bazin, Bazin]` (borda única, D-02) |
| **só Graham** (Bazin indefinido: sem dividendo) | 3 | ELET3, ELET6, ENEV3 → `fair_value = [Graham, Graham]` |
| **nenhuma** (D-03 degradação) | **1** | **AZUL4** (book negativo + sem dividendo confiável) |
`[VERIFIED: execução local 2026-07-20]`

**Acionável:** a razão `v_modelo/fair_value` do jackknife usa a **borda da faixa** (o backtest já faz isso via `fv_mid` em `rodar_cesta:160`; para o hold-out a métrica é `v_modelo/fair_value` com `fair_value` = ponto médio da faixa **ou** a borda mais próxima — decidir e escrever). Só **1 ticker** (AZUL4) é caso D-03 puro (fica na cesta, sem razão, fora do jackknife, reportado). O risco de "difícil sem lente virar exclusão silenciosa" é pequeno em volume mas a regra tem de estar escrita: **AZUL4 aparece no relatório de degradação, nunca some.** Os 10 "só uma lente" entram no jackknife com faixa degenerada [x,x] — decidir se faixa degenerada distorce a razão (ela não distorce: a razão vira `v/x`, legítima).

## LIMIAR_JACKKNIFE_PP(n) — a estatística (D-10)

**Hoje:** `LIMIAR_JACKKNIFE_PP = 0.01` `[ASSUMIDO]` em `test_blindagem_meta.py:30`. O parágrafo `[ASSUMIDO]` deve ser **removido** e substituído por uma função de `n` commitada no Commit 1 (antes de existir qualquer `v_modelo`).

**A teoria (order-statistic spacing):** `mediana_jackknife` (helpers_blindagem.py:327) devolve `max_v |mediana(amostra − {v}) − mediana(amostra)|`. Para `n` ímpar (`=2k+1`, mediana `= x_{k+1}`), remover um ponto acima da mediana desloca-a para `(x_k + x_{k+1})/2`; abaixo, para `(x_{k+1} + x_{k+2})/2`. Logo o desvio máximo do jackknife é **exatamente metade do maior gap entre estatísticas de ordem centrais**:
```
desvio_max ≈ ½ · max( x_{k+1} − x_k ,  x_{k+2} − x_{k+1} )
```
É **data-dependente por natureza** (depende do espaçamento) — não há forma fechada independente dos valores **sem** assumir uma distribuição. `[CITED: teoria de estatísticas de ordem]`

**O caminho honesto (recomendado): Monte-Carlo de um null neutro, seed fixo.**
1. Definir um **null saudável**: `n` pontos iid de uma distribuição suave unimodal representando uma distribuição de `V/FairValue` **sem ponto load-bearing** (ex.: lognormal com σ escolhido a priori, ou uniforme numa faixa plausível). O σ (dispersão saudável) é a **única** premissa de modelagem — deve vir de crença prévia sobre dispersão saudável, **nunca** do hold-out observado.
2. Simular M draws (ex.: 10 000), computar `mediana_jackknife` de cada, tomar um **percentil alto** (95 ou 99).
3. `LIMIAR_JACKKNIFE_PP(n)` = esse percentil. Interpretação: "num sample saudável de `n` pontos, um único ponto move a mediana em ≤ X com 95% de confiança; exceder X = ponto load-bearing além do que suavidade explica."
4. **Seed fixo + função pura + determinística** → o número é reproduzível e o teste que o usa (`test_nenhum_ticker_e_load_bearing`) fica estável.

**Landmine de escala:** o desvio do jackknife **escala com a dispersão** dos dados. Um LIMIAR absoluto (pp) embute uma escala. Duas saídas: (a) normalizar o **estatístico** por uma escala robusta do próprio sample (MAD/IQR) e derivar o LIMIAR de um null de **forma fixa** (escala-invariante); (b) manter absoluto mas fixar σ do null a priori. Recomendação: **(a) normalizar** (`desvio_max / MAD`) — mantém `LIMIAR(n)` dependente só de `n` e da forma do null, ambos fixados no Commit 1, e imune a "que dispersão a cesta acabou tendo". Isto exige tocar `mediana_jackknife` para devolver também a escala — decidir no plano. `[ASSUMED→needs-derivation: forma final da normalização]`

**Recomendação ao planner:** tratar a derivação do `LIMIAR_JACKKNIFE_PP(n)` como **tarefa de investigação/derivação do executor** com dois entregáveis: (1) a função (fechada ou Monte-Carlo com seed) commitada no Commit 1; (2) um teste que prova que ela mede o que promete no null saudável (espelhando `test_mediana_jackknife_e_robusta_por_construcao`, que já valida homogênea vs ponte). **É o item de maior incerteza da fase** — não pode ser "chutado" e não pode olhar os `v_modelo`.

## Ordem por git (D-09) — mecanismo

**Estrutura:** Commit 1 grava `holdout_v24.yaml` com, por ticker, `fair_value` (faixa) + fonte/data, e o `LIMIAR(n)` — **zero `v_modelo`**. Commit 2 (posterior) preenche `v_modelo`.

**Mecanismo verificado:** `git blame --line-porcelain -- tests/fixtures/holdout_v24.yaml` expõe `author-time <epoch>` por **linha** `[VERIFIED: git blame na REQUIREMENTS.md → "author-time 1783972139"]`. O teste:
1. `git blame --line-porcelain` do fixture;
2. mapear cada linha ao campo (parse do YAML por indentação/chave);
3. assertar `max(author-time das linhas fair_value/LIMIAR) < min(author-time das linhas v_modelo)`.

**Requisitos de schema (load-bearing):**
- `fair_value` e `v_modelo` de cada ticker em **linhas separadas** (blame é por linha; dict inline na mesma linha impede a separação).
- Não re-tocar as linhas `fair_value` depois do Commit 2 (re-toque reatribui o blame a um commit novo → o teste corretamente **falha**, flagando adulteração).

**Landmines (do memory `historia-git-tem-fase-13-superseded` e da mecânica do git):**
- **NÃO usar `git log --grep`** de mensagem (falso positivo com os commits de trading `13-0x`). Usar **timestamps das linhas reais**, não a mensagem.
- **Shallow clone (CI `--depth=1`) quebra `git blame`** → o job de CI precisa de história completa (`fetch-depth: 0`). Documentar.
- **Squash/amend colapsa os dois commits** → ambas as linhas ganham o mesmo timestamp e a prova evapora. O `git push` (história remota congelada) é a proteção; o teste deve rodar contra a árvore real, e a disciplina "dois commits, sem squash" é regra de processo escrita no plano.
- **Rebase preserva `author-time`** (é autoria original), então rebase normal não quebra a prova — só squash/reescrita de conteúdo quebra.
- **Alternativa mais robusta a considerar:** dois **arquivos** (`holdout_fair_values.yaml` no Commit 1, `holdout_v_modelo.yaml` no Commit 2) e comparar `git log -1 --format=%ct -- <arquivo>` (timestamp de criação por arquivo, sem blame por linha, imune a shallow-clone só se história presente). Mais simples, porém foge do "fixture único `holdout_v24.yaml`" do contrato existente (helpers_blindagem.py:39). Se o planner preferir robustez a fidelidade do path, é uma troca legítima — mas o path `HOLDOUT_V24` já está cravado no teste que acorda, então **fixture único + blame por linha** é o caminho de menor atrito. `[ASSUMED→needs-confirm: fixture único vs dois arquivos]`

## VAL-06 — matar o `excecao_nota`

**Localização real** (`grep` em src/tests/scripts):
- **NÃO existe em `report.py`.** O caminho report/gate não tem `excecao_nota`.
- `src/analista/backtest.py:179` — `rodar_cesta` emite `"excecao_nota": fv.get("excecao_nota")` como campo passthrough do dict de resultado (lê do `fair_values` yaml).
- `tests/test_backtest_bancos.py` — dois testes assertam sobre ele: `test_nenhuma_rota_diferente_de_rim_e_silenciosa` (:56) e `test_nenhuma_nota_de_excecao_e_orfa` (:72). Ambos são a **bijeção nota⟺rota-de-exceção** do v2.3.
- `scripts/backtest_bancos.py:79` — só imprime a coluna.
`[VERIFIED: grep local 2026-07-20]`

**Acionável para VAL-06:** "matar o `excecao_nota`" = remover o campo do dict de `rodar_cesta` **e** os dois testes de `test_backtest_bancos.py` que o mantêm vivo (ou reescrevê-los), **e** garantir que o novo `holdout_v24.yaml` **não tenha** chave `excecao_nota` (o fixture novo não nasce com a lavanderia). Cuidado: esses testes têm entrada em `tests/classificacao.yaml` — deletar o teste exige **remover a entrada órfã** (senão a coleta quebra, CLAUDE.md). Sob o RIM único (Fase 13) **todo** ticker roteia para `rim`, então a bijeção rota≠rim já é vacuamente satisfeita — os testes protegem uma máquina do v2.3 que a Fase 14 aposenta. Ver o memory `deletar-simbolo-exige-varredura-de-testes`: feche por construção (grep do símbolo na árvore viva), não símbolo a símbolo.

## VAL-07 — registro durável (D-08)

**Não existe padrão ADR no projeto ainda** — `find .planning -iname "*decision*"/"*adr*"` só achou nomes de fase, nenhum ADR real. `[VERIFIED: find local]`

**Recomendação:** criar `.planning/decisions/` (novo) com um arquivo tipo `VAL-07-backtest-temporal.md` (ADR leve: contexto, decisão = não fazer, justificativa PIT/lag 2–3 meses/vazamento de futuro, consequência = Future Requirement v2.5+), **e** um comentário-âncora em `src/analista/backtest.py` (topo do módulo ou perto de `carregar_snapshot`) apontando para o ADR. Dois lugares porque o requisito pede durável+auditável e o código é onde um futuro implementador de backtest tropeça primeiro. Alternativa mais barata: uma seção em `.planning/STATE.md` ou no próprio ROADMAP como "Decisão registrada". O ADR dedicado é mais limpo e auditável. `[ASSUMED→needs-confirm: local do ADR]`

## Contrato do fixture `holdout_v24.yaml` (o que a fase ACORDA)

O teste que dorme (`test_nenhum_ticker_e_load_bearing`, test_blindagem_meta.py:154) lê:
```yaml
# ticker -> {v_modelo, fair_value}; métrica = v_modelo / fair_value
TICKER:
  fair_value: <float>      # ponto (borda/mid da faixa Graham+Bazin) — Commit 1
  v_modelo: <float>        # V do RIM — Commit 2
```
`[VERIFIED: test_blindagem_meta.py:160-165]` — o teste faz `float(d["v_modelo"]) / float(d["fair_value"])` e **pula** entradas sem `v_modelo` ou sem `fair_value` (é assim que a degradação D-03/AZUL4 fica fora do jackknife automaticamente: sem `fair_value`, a entrada é ignorada na lista de razões).

**Compatibilidade com o schema atual:** o teste espera `fair_value` **escalar** (não faixa). A faixa [min,max] do D-02 precisa colapsar num escalar para o campo `fair_value` (ex.: ponto médio) **ou** o teste que acorda tem de ser ajustado para ler a faixa. Decisão de schema para o plano. Recomendo `fair_value` = ponto médio da faixa (escalar) para casar o teste existente sem reescrevê-lo, guardando `fair_value_min`/`fair_value_max` como campos extras auditáveis. `[ASSUMED→needs-confirm]`

**Guarda anti-golden (VAL-05):** o `detectar_ticker_com_valor_cravado` (helpers_blindagem.py:270) varre **`test_*.py`**, não fixtures YAML — então o fixture com números por ticker **não** dispara o BLIND-04a (ele só pega `ticker==R$` em código de teste). Mas o **teste soberano VAL-01** vai ter ITUB4 + um número: manter o literal do ticker num helper fora de `test_` (padrão `empresa_itub4`) e assertar **faixa** [35,39], nunca `==`.

## Don't Hand-Roll

| Problema | Não construir | Usar | Por quê |
|----------|---------------|------|---------|
| V do RIM | reimplementar a fórmula | `report.analisar_acao` / `motores.rim` | Fonte única; reimplementar viola o contrato "harness consome, não recalcula" |
| Graham/Bazin | recalcular lentes | `core/lentes.py` (`preco_justo_graham`, `preco_teto_bazin`, `dpa_medio`, `vpa`) | Já puras, never-raise, com condições de indefinição corretas |
| Jackknife | novo medidor | `helpers_blindagem.mediana_jackknife` | Já existe, validado por `test_mediana_jackknife_e_robusta_por_construcao` |
| Classificação de arquétipo | heurística nova | `arquetipo.classificar` | Fonte única; a cesta tem de classificar como a produção |
| Reconstrução do snapshot | novo loader | `helpers_sanidade.carregar_snapshot_sanidade` (+ **fix `eh_concessionaria`**) | Loader existe; só falta o campo do carve-out |
| Timestamp por linha | parsing manual de `git log` | `git blame --line-porcelain` | Expõe `author-time` por linha diretamente |

**Key insight:** quase tudo já existe — a fase é 80% orquestração de peças prontas + 20% estatística nova (LIMIAR(n)). O maior risco não é construir, é **reconstruir divergente** (o `eh_concessionaria` faltando) ou **recalibrar sem querer** (mexer num knob para "chegar em 37,22").

## Common Pitfalls

### Pitfall 1: cesta divergente da produção (eh_concessionaria)
**O que dá errado:** reusar `carregar_snapshot_sanidade` sem setar `eh_concessionaria` → 19 utilities viram CICLICA, carve-out vazio, hold-out valida um roteamento que a produção não usa.
**Como evitar:** replicar `build.py:168` no montador da cesta. **Warning sign:** CONCESSAO_FINITA com 0 membros; CICLICA com 65.

### Pitfall 2: recalibrar disfarçado de "fazer VAL-01 passar"
**O que dá errado:** ajustar `excesso_sustentavel`/ERP/etc. para o número bater 37,22 → 4º grau de liberdade, suíte vermelha, marco vira v2.3.
**Como evitar:** VAL-01 injeta **só** o Ke do livro; assere **região**; zero toque em `calibracao.lock.yaml`. **Warning sign:** diff em config.yaml/lock sem justificativa de knob.

### Pitfall 3: LIMIAR olhando os dados
**O que dá errado:** derivar `LIMIAR(n)` depois de ver a distribuição de `v_modelo/fair_value` → overfit por construção.
**Como evitar:** LIMIAR no **Commit 1**, antes de qualquer `v_modelo`; derivado de null neutro/seed fixo. **Warning sign:** LIMIAR commitado junto ou depois dos `v_modelo`.

### Pitfall 4: prova de ordem frágil
**O que dá errado:** squash dos dois commits, shallow clone na CI, ou `git log --grep` (falso positivo com commits 13-0x).
**Como evitar:** dois commits sem squash + push; `fetch-depth: 0` na CI; blame por linha, nunca grep de mensagem.

### Pitfall 5: quebrar a coleta ao deletar testes do excecao_nota
**O que dá errado:** deletar `test_nenhuma_nota_de_excecao_e_orfa` sem remover a entrada em `classificacao.yaml` → `CLASSIFICACAO ORFA` quebra a coleta.
**Como evitar:** deletar teste ⇒ deletar entrada no mesmo diff. `pytest -k` (nunca `pytest arquivo.py`).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | VAL-01 aceita **região** [35,39], não o ponto 37,22 | VAL-01 | Se exigirem ==37,22 exato, precisa de um closed-form do livro diferente do RIM (38,69) |
| A2 | Campo de ordenação da cota = `market_cap` desc | Cesta/D-05 | Outra ordenação muda quais 6 representantes entram (não muda a honestidade, só o conteúdo) |
| A3 | `fair_value` no fixture = escalar (ponto médio da faixa) | Fixture | Se for faixa, o teste que acorda precisa ser reescrito |
| A4 | LIMIAR(n) via Monte-Carlo de null neutro + normalização por MAD | D-10 | Forma final da estatística é o item de maior incerteza; exige derivação do executor |
| A5 | Fixture único + `git blame` por linha (vs dois arquivos) | D-09 | Dois arquivos seria mais robusto mas foge do path `HOLDOUT_V24` cravado |
| A6 | ADR em `.planning/decisions/` (novo diretório) | VAL-07 | Local pode ser STATE.md/ROADMAP; só afeta onde documentar |
| A7 | "prejuízo recente" = lucro≤0 em qualquer dos últimos 3 anos | D-06 | Definição diferente muda a lista de 19 candidatos |

## Open Questions (RESOLVED — recomendações adotadas pelo plano 2026-07-20)

1. **VAL-01: região ou ponto?** — **RESOLVED:** assertar REGIÃO [35,39] (Plano 14-01); ponto exato seria golden de nível (BLIND-04a).
   - Sabemos: injetando Ke=0,1248, V=38,69 ∈ [35,39]. REQUIREMENTS diz "região R$35–39, MS ±5%".
   - Incerto: se algum stakeholder quer o número exato 37,22.
   - Recomendação: assertar região; é o que o critério escrito pede e evita golden de nível.

2. **LIMIAR_JACKKNIFE_PP(n): forma exata.** — **RESOLVED:** Monte-Carlo de null neutro + normalização por MAD/IQR, tarefa de derivação dedicada com teste no null, commitada antes do Commit 1 (Plano 14-02).
   - Sabemos: é ½ do maior gap central (data-dependente); Monte-Carlo de null neutro é o caminho honesto.
   - Incerto: normalização (absoluto vs MAD) e o σ/forma do null.
   - Recomendação: tarefa de derivação dedicada no executor, entregue com teste que a valida no null — antes do Commit 1.

3. **Métrica `v_modelo/fair_value`: qual borda da faixa?** — **RESOLVED:** ponto médio no fixture (casa o teste que acorda), com min/max auditáveis ao lado (Plano 14-03).
   - Sabemos: 10 tickers têm faixa degenerada [x,x]; 93 têm faixa real.
   - Incerto: usar ponto médio, borda mais próxima, ou os dois extremos.
   - Recomendação: ponto médio (casa o teste atual), com min/max auditáveis ao lado.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 + PyYAML | tudo | ✓ | rodou local | — |
| `statistics` (stdlib) | jackknife/median | ✓ | stdlib | — |
| git com history completa | teste de ordem D-09 | ✓ (local) | blame porcelain OK | CI precisa `fetch-depth: 0` |
| numpy/scipy | Monte-Carlo do LIMIAR | verificar | — | `random`+`statistics` stdlib bastam |
| Snapshot 104 tickers | cesta/hold-out | ✓ | `snapshot_sanidade_limpo_2026-07-15.yaml` | — |

**Sem dependências externas de rede** — fase 100% offline/determinística (é um requisito: prova por execução reproduzível).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (com `addopts = -m 'not golden_nivel' --strict-markers`, `xfail_strict=true`) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run | `pytest -k "<nome> or blindagem" ` (NUNCA `pytest arquivo.py` → CLASSIFICACAO ORFA) |
| Full suite | `pytest` (0 failed, 2 xfailed, 1 skipped→acorda nesta fase) |
| Classificação | todo teste novo precisa de entrada em `tests/classificacao.yaml` ou quebra a coleta |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VAL-01 | ITUB4 book inputs → V∈[35,39] | contrato/closed-form | `pytest -k soberano_itub4` | ❌ Wave A |
| VAL-02 | cesta ≥6/arq + 10 difíceis, quota<6 marcada | contrato | `pytest -k holdout_estratificado` | ❌ Wave A |
| VAL-03 | fair_value antes de v_modelo (git) | contrato | `pytest -k ordem_por_git` | ❌ Wave B |
| VAL-04/05/D-11 | nenhum ticker load-bearing | contrato | `pytest -k load_bearing` (acorda) | ✅ existe, SKIP hoje |
| VAL-06 | excecao_nota morto, nenhuma exceção salva | contrato | `pytest -k excecao` (reescrever/deletar) | ✅ existe (a matar) |
| VAL-07 | decisão escrita | (doc, não-teste) | revisão do ADR | ❌ Wave A |
| D-10 | LIMIAR(n) mede o que promete no null | invariante | `pytest -k limiar_jackknife` | ❌ Wave A |

### Sampling Rate
- **Per task commit:** `pytest -k` do teste tocado + `pytest -k blindagem` (não quebrar a blindagem).
- **Per wave merge:** `pytest` (suíte default verde).
- **Phase gate:** suíte verde **E** regressão ao vivo dos 104 (o oráculo real, não a suíte) antes de `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/fixtures/holdout_v24.yaml` — nasce em dois commits (D-09); cobre VAL-02/03/05
- [ ] teste soberano VAL-01 (novo `test_*.py` + entrada em `classificacao.yaml`)
- [ ] função `LIMIAR_JACKKNIFE_PP(n)` + teste que a valida (substitui o `[ASSUMIDO]`)
- [ ] teste de ordem por git (novo + entrada em `classificacao.yaml`)
- [ ] `.planning/decisions/VAL-07-*.md` (ADR) + comentário em `backtest.py`
- [ ] remover/reescrever os dois testes de `excecao_nota` em `test_backtest_bancos.py` (+ entradas órfãs)

## Security Domain

Não aplicável em profundidade: fase offline, pura, sem input de usuário, sem rede, sem persistência de segredo. Única superfície = leitura de YAML congelado (já `safe_load`, nunca `load` — padrão do projeto, helpers_blindagem/helpers_sanidade). Sem categorias ASVS materiais.

## Sources

### Primary (HIGH — verificado por execução/leitura local)
- Execução ao vivo de `report.analisar_acao` e `motores.rim` sobre `snapshot_sanidade_limpo_2026-07-15.yaml` (2026-07-20) — VAL-01 (V=24,38 hoje; 38,69 com Ke livro), distribuição de arquétipos, buckets, lentes.
- `src/analista/core/lentes.py`, `core/arquetipo.py`, `core/motores.py`, `report/report.py`, `backtest.py`, `ingest/build.py:168`.
- `tests/helpers_blindagem.py`, `helpers_sanidade.py`, `test_blindagem_meta.py`, `test_backtest_bancos.py`, `classificacao.yaml`.
- `git blame --line-porcelain` — author-time por linha confirmado.
- `.planning/CONTEXT.md` (D-01..D-11), `REQUIREMENTS.md` (VAL-01..07 + critério soberano), `ROADMAP.md`, `CLAUDE.md`.

### Secondary (MEDIUM)
- Teoria de estatísticas de ordem para a sensibilidade da mediana ao leave-one-out (½ do gap central).

## Metadata

**Confidence breakdown:**
- VAL-01 (região passa com Ke livro): **HIGH** — medido por execução.
- Cesta/quotas/buckets/lentes: **HIGH** — contagens medidas nos 104.
- `eh_concessionaria` landmine: **HIGH** — reproduzido nos dois cenários.
- LIMIAR(n): **MEDIUM** — teoria sólida, forma final é design em aberto (maior incerteza).
- Mecanismo git: **MEDIUM-HIGH** — blame verificado; caveats de squash/shallow são conhecidos.
- VAL-06 localização: **HIGH** — grep exaustivo.

**Research date:** 2026-07-20
**Valid until:** ~2026-08-20 (estável; depende do snapshot congelado, que não muda)
