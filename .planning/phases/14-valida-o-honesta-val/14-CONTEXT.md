# Phase 14: Validação honesta (VAL) - Context

**Gathered:** 2026-07-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Provar o marco v2.4 **sem se enganar**. Esta fase **valida** — não constrói motor e **não
recalibra** (o RIM único, o `a.ke` e o `g` já vêm prontos das Fases 11–13). Entregas mensuráveis
(VAL-01..07):

- **Critério de aceite soberano (VAL-01):** ITUB4 com os inputs do Cap. 17 (`g` = 10,24%,
  `Ke` = 12,48%) reproduz `V` ≈ **R$ 37,22** (região R$ 35–39). Enquanto isso não for verdade, o
  marco **não está entregue**, independente de qualquer outra métrica. É um teste **closed-form** dos
  inputs do livro → output, **separado** do hold-out.
- **Hold-out estratificado (VAL-02):** cesta com ≥ 6 por arquétipo + **10 "difíceis" deliberados**
  (P/B < 1, prejuízo recente, payout > 100%, book pequeno). Roda **uma única vez** (VAL-04).
- **Ordem provada (VAL-03):** os `fair_value` são commitados **ANTES** de rodar o modelo; o `git log`
  prova a ordem.
- **Métrica honesta (VAL-05):** `V/FairValue`, medida por **distribuição + jackknife** — **nunca**
  `V/preço` (espelho do mercado), **nunca** assert `ticker == R$`.
- **Sem lavanderia (VAL-06):** **matar o `excecao_nota`** — nenhuma regra de exceção pode salvar um
  ticker.
- **Backtest temporal (VAL-07):** decisão **tomada e escrita** — PIT real **ou não fazer**.

**Escopo negativo (regras "NÃO fazer" do roadmap — duras, sem exceção):**
- **Se o hold-out falhar, RE-ARQUITETA-SE — NÃO se recalibra.** Um knob mexido aqui invalida o
  hold-out inteiro e o marco vira o v2.3 num endereço novo. **Orçamento intacto em 3 graus**
  (`ERP`, `n_fade`, `PIB_real`); zero knobs de valuation tocados nesta fase.
- **NÃO validar contra consenso de sell-side como GATE de aprovação** — é circular (target price é
  preço com chapéu, e o preço é o que está sendo julgado).
- **NÃO criar carve-out/rota nova depois de ver um ticker falhar** (foi assim que a BBSE3 ganhou rota
  de seguradora no v2.3). Carve-outs foram declarados na Fase 13, antes do hold-out. **Zero exceções.**
- **NÃO alargar a banda de tolerância** para o quórum passar (o "±15% sobre faixas largas" do v2.3).

**Recontagem do v2.3 (o que esta fase corrige):** o v2.3 gastou **~8 graus de liberdade sobre 4
observações** e chamou de "4/4 PASS" um resultado que era **2/4** (BBAS3 e BBDC4 fora do consenso,
salvos só pelo acolchoamento de ±15% + `excecao_nota`).

</domain>

<decisions>
## Implementation Decisions

### Âncora de fair value (VAL-05)
- **D-01 (âncora = Graham+Bazin, não consenso):** o `fair_value` de cada ticker no
  `holdout_v24.yaml` vem das **lentes clássicas Graham + Bazin** (já em `core/lentes`, já consumidas
  por `backtest.rodar_cesta`). É genuinamente **independente do modelo E do sell-side** — partem de
  lucro/dividendo real, não de preço. Isso resolve a tensão do VAL-05: consenso de sell-side fica
  **fora** como gate de aprovação (circular). O `fair_values_bancos.yaml` (consenso, 4 bancos, ±15%)
  **não** é o substrato do hold-out.
- **D-02 (fair_value é uma FAIXA [min,max]):** `fair_value = [min(Graham,Bazin), max(Graham,Bazin)]`
  entre as lentes que estão **definidas** para aquele ticker (como o backtest já trata a faixa FV,
  usando a borda). A divergência Graham≠Bazin é, ela própria, sinal de incerteza — preserva-se.
- **D-03 (difícil sem lente → degradação observada, não exclusão silenciosa):** ticker onde **nenhuma**
  lente vale (prejuízo → Graham indefinido; sem dividendo / payout > 100% → Bazin indefinido) **fica na
  cesta** mas **sem razão V/FairValue** — **não entra no jackknife**, entra como **caso de degradação
  observada e reportada**. Regra dura: um difícil sem lente **não pode** ser silenciosamente excluído
  para melhorar a distribuição (isso re-introduziria o viés de "validar só o meio").
- **D-04 (VAL-01 separado do hold-out; ITUB4 na cesta usa a regra dos outros):** o caso-do-livro
  (ITUB4 = R$ 37,22) vive **só** no teste soberano VAL-01 (closed-form, inputs do Cap. 17). Dentro da
  cesta do hold-out o ITUB4 usa **Graham+Bazin como todo mundo** — cesta homogênea, jackknife honesto,
  ITUB4 **não** vira âncora privilegiada da mediana.

### Composição da cesta estratificada (VAL-02)
- **D-05 (seleção determinística por regra, anti cherry-pick):** os representantes de cada arquétipo
  (fora os difíceis) são escolhidos por **regra fixa e escrita ANTES** (ex.: os N maiores por
  liquidez/patrimônio de cada arquétipo entre os que têm série completa; ou ordem determinística).
  **Zero escolha discricionária de ticker** — o `git log` prova que a cesta não foi montada olhando o
  resultado. Arquétipos vivos (pós-Fase 13): `FINANCEIRA`, `PAGADORA_MADURA`, `CICLICA`, `CRESCIMENTO`,
  `CONCESSAO_FINITA`.
- **D-06 (10 difíceis por filtro de atributo, disjuntos da cota):** 4 baldes (`P/B < 1`,
  `prejuízo recente`, `payout > 100%`, `book pequeno`); regra determinística pega os extremos de cada
  balde até somar ≥ 10, **separados** dos ≥ 6 normais de cada arquétipo (os difíceis **somam**, não
  enfraquecem a cota).
- **D-07 (reporta por estrato + pooled; carve-out isolado; cota faltante marcada):** a distribuição
  `V/FairValue` é mostrada **tanto pooled (todos) quanto por arquétipo**. `CONCESSAO_FINITA` (carve-out,
  não aplica `g`, book já = VP da RAP) aparece como **seu próprio estrato** — validado, mas **sem
  contaminar o pooled** (evita virar outlier estrutural que dispara o jackknife por um motivo que não é
  doença). Arquétipo com < 6 nomes no universo: usa todos os que existem e **MARCA** que a cota mínima
  não foi atingida (honesto, não inventa).

### Backtest temporal (VAL-07)
- **D-08 (não fazer, documentar o porquê):** decisão **tomada e escrita** — **não** fazer backtest
  temporal nesta fase. Justificativa a registrar de forma durável e auditável: PIT honesto exige mapear
  a **data de disponibilidade** de cada DFP (lag de ~2–3 meses após o fechamento — a DFP de 2022 só
  existiu em mar/2023) e reconstruir preço/rf da época, inviável de forma confiável só com dados
  gratuitos. Um backtest **ingênuo** (usando a DFP no fechamento, não na publicação) é **vazamento de
  futuro** → um número confiante e **falso**, **pior que nenhum**. VAL-07 é satisfeito pela **decisão
  escrita** (que é o que o requisito pede). O desenho do PIT correto pode ser registrado como Future
  Requirement (v2.5+) sem gastar orçamento desta fase.

### Rigor: ordem do commit + limiar do jackknife (VAL-03 / VAL-04)
- **D-09 (dois commits datados + teste de ordem):** **Commit 1** grava o `holdout_v24.yaml` **só** com
  `fair_value` (+ fonte/data), **zero `v_modelo`**. **Commit 2** (posterior) preenche `v_modelo` rodando
  o motor. Um **teste na suíte** verifica que, na árvore atual, todo `fair_value` tem timestamp de
  commit **anterior** ao do `v_modelo` (via git blame/log) — burlar exige reescrever história, que o
  push protege. A ordem é provável por `git log` **sozinho**, sem confiar em promessa.
- **D-10 (LIMIAR derivado de n + pré-registrado):** `LIMIAR_JACKKNIFE_PP` (hoje `0.01` `[ASSUMIDO]` em
  `tests/test_blindagem_meta.py:30`) passa a ser **função de n** — quanto um único ponto **pode** mover
  a mediana numa distribuição saudável de n observações (fechado/simulado, **independente dos valores
  reais**) — e é **commitado no Commit 1**, antes de existir qualquer `v_modelo`. À prova de overfit
  por **construção** (não olha o resultado) e por **timestamp** (fixado antes). O parágrafo `[ASSUMIDO]`
  do teste é removido.
- **D-11 (PASS = robustez é gate, viés é detector):** o hold-out "passa" quando **(1)** VAL-01 é
  verdadeiro (ITUB4 = R$ 37,22 — **soberano e inegociável**), **(2)** o jackknife mostra **nenhum ticker
  load-bearing** (desvio da mediana ≤ `LIMIAR_JACKKNIFE_PP`), e **(3)** **nenhuma exceção salvou** um
  ticker (VAL-06). A **mediana `V/FairValue`** é **reportada como detector de viés**, mas **NÃO é alvo
  numérico** — mediana longe de 1 vira **alerta escrito**, nunca um gate que empurra rumo à mediana = 1
  (calibrar para a âncora é o **espelho do mercado** que VAL-05 condena). Falha de robustez ou VAL-01 →
  **re-arquiteta, não recalibra** (VAL-04).

### Claude's Discretion
O usuário escolheu a **opção recomendada em todas** as questões (nenhum "Você decide" acionado). Fica
ao researcher/planner, dentro das decisões acima:
- A **regra determinística exata** de seleção por arquétipo (D-05) e os **limiares dos 4 baldes** de
  dificuldade (D-06: o que é "book pequeno", "prejuízo recente" = quantos trimestres, desempate).
- A **regra de combinação/degradação** precisa quando só uma lente vale ou nenhuma (D-02/D-03), e como a
  borda da faixa entra na razão.
- A **forma fechada/simulação** do `LIMIAR_JACKKNIFE_PP(n)` (D-10) e o **mecanismo exato** do teste de
  ordem (D-09: git blame vs log vs tag).
- **Onde** registrar de forma durável a decisão VAL-07 (D-08) — provável `.planning` DECISION/ADR +
  comentário no código do backtest.
- A **divisão em waves** e a ordem dos commits atômicos (os dois commits do D-09 têm ordem load-bearing:
  fair_value+limiar → depois v_modelo).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e critérios da fase
- `.planning/ROADMAP.md` §"Phase 14: Validação honesta (VAL)" (linhas ~290-308) — goal, os 5 success
  criteria e as 4 regras "NÃO fazer" (re-arquiteta não recalibra; não validar contra consenso; zero
  carve-out novo; não alargar banda).
- `.planning/ROADMAP.md` §"Overview" / regras duras — **(A)** ordem provada por simulação (VAL é a
  última fase); **(B)** golden que quebra é DELETADO; **(C)** orçamento travado em 3 graus
  (`ERP`/`n_fade`/`PIB_real`) — nenhum knob de valuation muda nesta fase.
- `.planning/REQUIREMENTS.md` VAL-01..07 (linhas 233-249) — o "por quê" de cada requisito e a recontagem
  do v2.3 (~8 graus sobre 4 obs; "4/4 PASS" real = 2/4).

### Contrato do fixture e harness do jackknife (o que esta fase ACORDA)
- `tests/test_blindagem_meta.py` — `test_nenhum_ticker_e_load_bearing` (`:132-173`, hoje **skip**;
  acorda quando `holdout_v24.yaml` nascer) e `test_mediana_jackknife_e_robusta_por_construcao`
  (`:88`, BLIND-04b harness). O **contrato do fixture** (`ticker → {v_modelo, fair_value}`, métrica
  `v_modelo/fair_value`) está escrito em `:147-149`. `LIMIAR_JACKKNIFE_PP = 0.01 [ASSUMIDO]` em
  `:30-31` — **D-10 o substitui**.
- `tests/helpers_blindagem.py` — `HOLDOUT_V24` path (`:39`, `tests/fixtures/holdout_v24.yaml` — **não
  existe ainda, nasce nesta fase**); `mediana_jackknife(valores)` (`:327`, `n < 3` levanta);
  `detectar_ticker_com_valor_cravado` (`:270`, a guarda BLIND-04 anti `ticker == R$`).
- `src/analista/backtest.py` — `rodar_cesta` (harness PURO que **consome** o motor, triangula as 4
  âncoras: Graham+Bazin, preço, faixa FV, múltiplos de par; `BANDA_PASS = 0.15` **não** se aplica ao
  gate do hold-out — D-01/D-11); `carregar_snapshot`, `carregar_fair_values`, `_CHAVES_GLOBAIS`.
- `tests/fixtures/fair_values_bancos.yaml` — a cesta do overfit v2.3 (4 bancos, consenso ±15%). **NÃO**
  é o substrato do hold-out (D-01); referência do que **não** repetir.

### Método do livro (precedência sobre qualquer requisito conflitante)
- `.planning/REQUIREMENTS.md` §"Critério de aceite soberano" (linhas 8-18) — o livro tem precedência;
  Cap. 17 = valor intrínseco + tríade + MS do usuário + matriz Ke×g.
- `Referencias/` (PDF *O Investidor em Ações de Dividendos*, se presente) — Cap. 17 (o caso ITUB4 =
  R$ 37,22, os inputs `g`/`Ke` do VAL-01) e as lentes clássicas Graham/Bazin.

### Código-alvo das lentes (âncora de fair value, D-01/D-02)
- `src/analista/core/lentes.py` — Graham e Bazin, a origem do `fair_value` da cesta (independente do
  modelo e do sell-side). Verificar as condições de indefinição (prejuízo → Graham; sem dividendo /
  payout > 100% → Bazin) para a regra de degradação D-03.
- `src/analista/core/arquetipo.py` — `classificar` + arquétipos vivos pós-Fase 13 (`FINANCEIRA`,
  `PAGADORA_MADURA`, `CICLICA`, `CRESCIMENTO`, `CONCESSAO_FINITA`) — a estratificação da cesta (D-05) e
  o estrato isolado do carve-out (D-07).
- `src/analista/report/report.py` — `analisar_acao` (FONTE ÚNICA do V do RIM que o `rodar_cesta`
  consome). O `excecao_nota` do v2.3 a **matar** (VAL-06/D-11) — localizar e remover.

### Contexto herdado (inputs prontos — NÃO recomputar)
- `.planning/phases/13-motores-contrato-de-sa-da-eng/13-CONTEXT.md` — RIM único, contrato de saída,
  guard P/B, corte de knobs; o motor que esta fase valida.
- `.planning/phases/12-custo-de-capital-ke-ke/12-CONTEXT.md` e `11-.../11-CONTEXT.md` — `a.ke` único e
  `g_cap`/`g_T` prontos; **esta fase não os toca** (re-arquiteta ≠ recalibra).

### Contexto de raciocínio (memórias do projeto, não versionadas no repo)
- `guardrails-devem-ser-provados-por-execucao` — "suíte verde" não prova blindagem; o hold-out e o teste
  de ordem precisam ser **provados por execução**, não só por teste verde.
- `ranking-e-cego-ao-preco` — por que múltiplos de par / centro da seção transversal é **detector de
  viés, nunca alvo** (base do D-11: mediana é detector, não gate).
- `duas-doencas-do-valuation` — as duas doenças e por que "correções óbvias" pioram; base do "re-arquiteta
  não recalibra".
- `historia-git-tem-fase-13-superseded` — commits de trading em `13-0x` dão falso positivo em gates
  `git log --grep`; relevante para o teste de ordem do D-09 (usar timestamps/arquivos reais, não grep de
  mensagem).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backtest.rodar_cesta` (`src/analista/backtest.py`) — harness PURO já pronto que consome
  `report.analisar_acao` e triangula 4 âncoras; o hold-out (D-01/D-07) reusa, não reinventa. A fórmula
  RIM **não** é reimplementada aqui.
- `helpers_blindagem.mediana_jackknife` (`tests/helpers_blindagem.py:327`) — o jackknife já existe e
  levanta em `n < 3`; o veredito (D-11) é `test_nenhum_ticker_e_load_bearing`, hoje `skip`.
- `core/lentes.py` (Graham+Bazin) — a âncora de fair value (D-01), já consumida pelo backtest.
- `helpers_blindagem.detectar_ticker_com_valor_cravado` (`:270`) — a guarda AST BLIND-04 que proíbe
  `ticker == R$`; garante que o fixture novo não vire golden de nível disfarçado (VAL-05).

### Established Patterns
- **Golden de nível que quebra é DELETADO, não atualizado** (CLAUDE.md / regra dura B). O fixture do
  hold-out é `ticker → {v_modelo, fair_value}` — **razão**, não nível cravado.
- **Nenhum knob de valuation tocado** — o orçamento fica em 3 graus; se o hold-out falhar,
  **re-arquiteta** (não mexe knob). Um 4º grau deixa a suíte vermelha.
- **Classificação de testes imposta na coleta** (`tests/classificacao.yaml`) — o teste de ordem (D-09) e
  qualquer teste novo precisa de entrada ou **quebra a coleta**. O clone novo nasce sem o hook:
  `git config core.hooksPath .githooks`.
- **`pytest tests/arquivo.py` NÃO funciona** neste repo (dispara `CLASSIFICACAO ORFA`); usar `-k`.
- **Provado por execução** (regressão dos 104 tickers ao vivo é o oráculo, não a suíte verde).

### Integration Points
- `holdout_v24.yaml` (**novo**, `tests/fixtures/`) → `test_nenhum_ticker_e_load_bearing` acorda (D-01..D-11).
- **Dois commits ordenados** (D-09): Commit 1 (`fair_value` + `LIMIAR(n)`) → Commit 2 (`v_modelo`) → teste
  de ordem por `git log`.
- O `excecao_nota` do v2.3 (VAL-06) precisa ser **localizado e removido** no caminho do report/gate.
- Decisão VAL-07 (D-08) → registro durável em `.planning` (DECISION/ADR) + comentário no `backtest.py`.

</code_context>

<specifics>
## Specific Ideas

- `fair_value` = **faixa [min,max] de Graham+Bazin** (independente do modelo e do sell-side); difícil sem
  lente → degradação reportada, fora do jackknife.
- VAL-01 (ITUB4 = R$ 37,22) = teste **closed-form soberano**, separado do hold-out; ITUB4 na cesta usa a
  regra geral.
- Cesta: seleção **determinística** por arquétipo + 10 difíceis por **filtro de atributo disjunto**;
  distribuição **por estrato + pooled**; `CONCESSAO_FINITA` isolado; cota < 6 marcada.
- VAL-07: **não fazer, documentar** — backtest ingênuo = vazamento de futuro, pior que nenhum.
- Rigor: **dois commits datados** + teste de ordem por `git log`; `LIMIAR_JACKKNIFE_PP` **derivado de n +
  pré-registrado** no Commit 1; **PASS = VAL-01 soberano + jackknife robusto + zero exceção**; mediana =
  detector reportado, **nunca** gate.

</specifics>

<deferred>
## Deferred Ideas

- **Backtest temporal PIT real** — Future Requirement (v2.5+). O desenho correto (mapear data de
  disponibilidade de cada DFP + reconstruir preço/rf da época) fica escrito; não se gasta orçamento
  desta fase (D-08).
- **Motor `nav`/SOTP real para holdings** (ITSA4, B3SA3) e **score BSD por arquétipo** — Future
  Requirements herdados da Fase 13 (`REQUIREMENTS.md`), fora desta fase.
- **Reforma visual pesada da tela Streamlit** e **como o app exibe/consome o veredito do hold-out** —
  esta fase é validação de engine; exibição aprofundada fica para um plano de UI dedicado se necessário.

### Reviewed Todos (not folded)
None — `todo.match-phase 14` retornou 0 matches.

</deferred>

---

*Phase: 14-valida-o-honesta-val*
*Context gathered: 2026-07-20*
