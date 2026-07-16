# Phase 11: Crescimento / `g` (GROW) - Context

**Gathered:** 2026-07-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Curar a **metade `g` da Doença 1** — a metade que precede o `Ke`. Fechar a identidade do
crescimento na perpetuidade e reconciliar o `g` da fase explícita com o método do livro.

Entregas mensuráveis:
- `g_cap = (1 + π_ciclo) × (1 + PIB_real) − 1 = **7,28%**`, com π_ciclo (5,18%, IPCA médio 10a,
  BCB SGS 13522) medido na **mesma janela do `rf`** (`capm.rf_ciclo_anos = 10`) — é essa simetria
  de janela que torna o valuation invariante à inflação (GROW-01/02).
- `g_T = min(ROE_T × retenção, g_cap)` — identidade fechada por empresa, não constante (GROW-03).
- O `g` da fase explícita passa a **adotar o `g` por fundamentos** (o do livro), em vez de descartá-lo
  em favor do histórico (GROW-04).
- `excesso_sustentavel` e `ke_g_spread_min`, hoje decorativos, tratados como **load-bearing** sob o
  spread apertado que o `g` novo produz (GROW-05).

**Escopo negativo (regra dura A — provada por simulação):** esta fase **NÃO toca** `Ke`, `ke_teto`,
`ke_piso`, `ERP` nem `beta`. Consertar o Ke antes do g **piora** o modelo (ITUB4 0,75→0,64;
BBDC4 0,71→0,52) — o `ke_teto` é a muleta que compensa exatamente o viés do `g` que esta fase remove.
O Ke é a Fase 12, separada de propósito.

**Fronteira de teste crítica:** o **BLIND-02 NÃO vira verde nesta fase.** Enquanto o `ke_teto = 0,13`
existir (Fase 12), ele **satura** sob o choque de +300 bps, o `Ke` não se move 1 bp e a perna do `rf`
é absorvida. **Se o BLIND-02 ficar verde aqui, algo está errado — investigar, não comemorar.** O
`xfail(strict=True)` permanece; será removido na Fase 12 porque o código passou a satisfazê-lo, não
porque alguém o afrouxou. O progresso desta fase se mede pelo `g_cap` derivado (7,28%) e pela
reconciliação com o livro, **não** pelo BLIND-02.

</domain>

<decisions>
## Implementation Decisions

### Seleção do `g` da fase explícita (GROW-04)
- **D-01:** Substituir o `min(g_historico, g_fundamentos)` de `report.py:426-431` pela **adoção do
  `g_fundamentos`** como o `g` da fase explícita — reproduz o método do livro (Cap. 14.3; ITUB4 →
  ~10,29%, contra os 10,24% do livro). `g_historico` deixa de ser teto: fica **exibido como número
  de sanidade** e só é usado como **fallback** quando `g_fundamentos` é None. O comentário
  `DDM-FIX-02` (report.py:418, que subordinava o g ao histórico) é revertido.
  ```
  g_alto = g_fundamentos if g_fundamentos is not None else g_historico
  g_alto = max(0.0, min(g_alto, 0.25))   # teto absoluto (inalterado)
  g_alto = min(g_alto, ke)               # FIX-01, teto econômico (report.py:462, inalterado)
  ```
- **D-02 (CRÍTICA — impacta VAL-01):** o `g_cap` (7,28%) trava **SÓ o terminal**, nunca a fase
  explícita. A estrutura de dois estágios do livro é: `g` explícito alto (10,24%) → *fade* → `g`
  terminal ≤ `g_cap`. Travar `g_alto` em `g_cap` derrubaria o ITUB4 explícito para 7,28% e o caso
  soberano do marco (VAL-01, ITUB4 = R$ 37,22 com g = 10,24%) **não reproduziria**. O `g` explícito
  mantém teto `Ke` (FIX-01) + absoluto 0,25 — como hoje.
  ```
  g_T = min(roe_T * retencao, g_cap)     # g_cap = 7,28%  (GROW-03), só o terminal
  ```
- Nota: `g_fundamentos = crescimento_por_fundamentos(roe_valuation, payout_valuation)` já consome as
  primitivas curadas na Fase 10 (`roe_valuation` = mediana dos ROEs anuais, ITUB4 18,0%) — o ~10,29%
  cai naturalmente, sem knob novo.

### Topologia do `g_cap` no config (GROW-01/02)
- **D-03:** A **engine deriva** `g_cap = (1 + π_ciclo)(1 + PIB_real) − 1` em tempo de cálculo, a
  partir de: `π_ciclo` **carimbado** nos entry points (não-knob, medido do BCB, mesma janela 10a do
  rf) + `PIB_real` **knob estático** (2,0%, constante estrutural). Derivar na engine torna o
  "derivado, não digitado" do GROW-01 **literal e testável** — nos testes carimba-se o `π_ciclo`, não
  o `g_cap`. A engine permanece offline/determinística (lê de `cfg`, nunca chama a rede).
- **D-04:** **Fonte única** — um `g_cap` derivado, consumido tanto pela **perpetuidade do DDM**
  (substitui `ddm.g_estavel`) quanto pelo **RI terminal do RIM** (substitui `motores.rim.g_terminal`).
  Elimina as duas constantes gêmeas de 2,5% ("mesma Doença 1, mesma cura" — lock:150); ajuda o corte
  de knobs do bloco `motores:` da Fase 13 (ENG-10).
- **D-05 (restrição de lock, MESMO diff):** ao migrar `PIB_real` de `ddm.g_estavel` para o novo
  home derivado, **atualizar o `caminho` do grau `PIB_real` em `calibracao.lock.yaml`** (linhas
  84-101) no **mesmo commit** — o grau de liberdade continua sendo UM; o que muda é onde ele mora e
  como é consumido. As folhas congeladas `motores.rim.g_terminal: 0.025` e `ddm.g_estavel: 0.025`
  saem da lista congelados (a partição das 30 folhas muda) — o `test_knobs_batem_com_o_lock` e a
  partição precisam refletir isso no mesmo diff.

### Fonte/janela do π_ciclo (GROW-02)
- **D-06:** Novo helper em `macro.py`, **irmão de `selic_ciclo_para_capm`**: `π_ciclo` = **média
  aritmética** de `_ipca_anual_dezembro(10).values()` (`sum/len`) — espelha exatamente o `rf`
  (`sum(hist)/len(hist)`). Reusa a **mesma série SGS 13522 e a mesma janela 10a** já usada pelos
  deflatores da Fase 10 (PRIM-04) — zero fonte nova, zero grau de liberdade novo. Carimbado nos
  entry points (cli/app) em `cfg["macro"]["pi_ciclo"]`; a engine lê o valor carimbado.
  ```python
  def ipca_ciclo_para_g(fallback, anos=10):        # irmão de selic_ciclo_para_capm
      por_ano = _ipca_anual_dezembro(anos)         # SGS 13522, reuso PRIM-04
      if por_ano:
          return sum(por_ano.values()) / len(por_ano)   # aritmética, = rf
      return fallback
  ```
- **D-06a:** o `config.yaml` precisa de um **default `macro.pi_ciclo`** (≈ 5,18%, o valor medido)
  para determinismo offline/testes — espelha o `rf_local` default (`selic_fallback`). Degradação
  graciosa: rede falha → default (a engine ainda deriva um `g_cap` determinístico).

### Postura dos knobs sob spread apertado (GROW-05)
- **D-07:** **Congelar** os valores de `excesso_sustentavel` (0,045) e `ke_g_spread_min` (0,03) —
  mexer é knob move (exige lock no mesmo diff) e abre porta para calibrar contra resultado
  (Armadilha 4 / post-mortem v2.3). Torná-los load-bearing por **COBERTURA de teste**, não por
  recalibração: adicionar teste que exercita o RI terminal sob o spread `Ke − g` ~5,5pp (os dois
  knobs **binding**) e assegura que o terminal (a) não explode e (b) degrada de forma honesta quando
  `Ke − g_terminal < ke_g_spread_min` (cai para fade-only, never-raise). "Prever, não descobrir."

### Claude's Discretion
- O usuário respondeu com a opção recomendada em todas as perguntas (nenhum "Você decide" foi
  escolhido). Detalhes deixados ao planner/researcher dentro das decisões acima: o **nome exato da
  chave** do novo home do `PIB_real`/`g_cap` no config e do `caminho` no lock; a assinatura exata do
  helper `ipca_ciclo_para_g`; a forma exata do teste de cobertura do D-07; os rótulos do report
  markdown (`report.py:960-962`) que precisam refletir a nova semântica (`g estável` 2,5% → `g_cap`
  7,28% derivado; `g_T` por empresa) — mudança de apresentação, não de método, dentro do escopo.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e critérios da fase
- `.planning/ROADMAP.md` §"Phase 11: Crescimento / `g` (GROW)" — goal, 4 success criteria (inclui a
  fronteira "BLIND-02 NÃO vira verde aqui") e as regras "NÃO fazer".
- `.planning/ROADMAP.md` §"Overview" (regra dura A) e §"Phase 14: VAL" (critério soberano: ITUB4 =
  R$ 37,22 com g = 10,24%, Ke = 12,48%) — o que esta fase precisa **não quebrar** rio abaixo.
- `.planning/REQUIREMENTS.md` GROW-01..05 — rastreabilidade e números-alvo.
- `CLAUDE.md` §"O que significa suíte verde" — golden que quebra é DELETADO não atualizado; orçamento
  de 3 knobs (`ERP`, `n_fade`, `PIB_real`); justificativa de knob nunca menciona ticker; qualquer
  knob de valuation exige mexer no lock no mesmo diff.

### Orçamento de knobs (mudança obrigatória nesta fase)
- `calibracao.lock.yaml:84-101` (grau `PIB_real`) — instrução literal de migrar o `caminho` de
  `ddm.g_estavel` para o `g_cap` derivado **no mesmo commit** (D-05).
- `calibracao.lock.yaml:144-152` (`motores.rim.excesso_sustentavel`, `motores.rim.g_terminal`,
  `motores.rim.ke_g_spread_min`) — as folhas afetadas; a partição das 30 folhas precisa refletir a
  remoção de `g_terminal`/`g_estavel` como folhas congeladas.

### Código-alvo (o que muda)
- `src/analista/core/growth.py` — `crescimento_por_fundamentos`, `crescimento_estavel`,
  `crescimento_log_linear` (as fórmulas de `g`).
- `src/analista/report/report.py:405-431` — a seleção `g_alto` (o `min` a reverter, D-01) e
  `report.py:459-463` (o teto FIX-01 = Ke, inalterado, D-02).
- `src/analista/report/report.py:217` (`g_estavel = cfg["ddm"]["g_estavel"]`) + os consumidores da
  perpetuidade (`motores.py:175-215` `lucro_normalizado`/`dcf_crescimento`; `ddm.valor_gordon`) e
  `report.py:239-252` (`motores.rim(..., g_terminal=...)`) — os pontos onde o `g_cap` único entra.
- `src/analista/ingest/macro.py` — `_ipca_anual_dezembro(10)` e `selic_ciclo_para_capm` (o helper a
  espelhar para o `π_ciclo`, D-06); os entry points `cli.py`/`app.py` que carimbam `rf_local`/
  `ipca_deflatores` (onde carimbar o `pi_ciclo`).
- `config.yaml:95-97` (`ddm.g_estavel`), `config.yaml:261` (`motores.rim.g_terminal`),
  `config.yaml:256/264` (`excesso_sustentavel`, `ke_g_spread_min`).

### Contexto de raciocínio (memórias do projeto, não versionadas no repo)
- `duas-doencas-do-valuation` — "3 correções óbvias PIORAM o modelo; ordem obrigatória de conserto"
  (por que g antes de Ke, e por que não fundir as fases).
- `ddm-nao-consertar-e-lente-nao-motor` — o DDM é lente, não motor; mexer em `g_estavel`/`payout`
  historicamente quebrou TAEE11/BBSE3/VULC3 → a mudança de `g_alto`/`g_cap` precisa ser validada
  contra o mapa de 104 tickers antes do plano.
- `rim-terminal-value-root-cause` — o valor terminal do RIM e por que o `excesso_sustentavel`/
  `roe_terminal` governam o terminal (contexto do GROW-05).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `macro.selic_ciclo_para_capm(fallback, anos=10)` (`macro.py:161`): o **template exato** do helper
  do `π_ciclo` — média aritmética de série BCB, carimbo nos entry points, degradação graciosa.
- `macro._ipca_anual_dezembro(anos=10)` (`macro.py:109`): a série de IPCA anual (SGS 13522) já
  existente — o `π_ciclo` a consome direto, sem nova chamada de rede.
- `macro.ipca_deflatores_anuais` + o padrão de carimbo `cfg["macro"]["ipca_deflatores"]` (PRIM-04):
  o `pi_ciclo` segue o mesmo padrão de carimbo/leitura.
- `growth.crescimento_por_fundamentos(roe, payout)` (`growth.py:78`): já implementa `ROE × (1−payout)`
  — GROW-04 apenas passa a **adotá-lo** em vez de descartá-lo.

### Established Patterns
- **Pureza da engine:** rf/IPCA são resolvidos UMA vez nos entry points e carimbados em `cfg`;
  `analisar_acao` nunca toca a rede. O `pi_ciclo`/`g_cap` DEVEM respeitar essa fronteira.
- **Simetria de janela rf↔π_ciclo:** `capm.rf_ciclo_anos = 10` é a janela do rf; o `π_ciclo` usa a
  MESMA — é o que o GROW-02 formaliza (lock:166-168).
- **Fonte única de número-síntese:** as assinaturas dos consumidores da perpetuidade devem
  permanecer estáveis; o `g_cap` entra como um valor único derivado, não como constante duplicada.

### Integration Points
- O `g_cap` derivado alimenta **dois** consumidores (perpetuidade DDM + RI terminal RIM) — ponto
  único de verdade (D-04).
- `report.py` é onde `g_historico`, `g_fundamentos`, `g_alto` e `g_estavel` são montados e exibidos
  (`report.py:960-962`) — a mudança de semântica precisa refletir nos rótulos.
- A suíte de blindagem (`test_invariancia_inflacao_engine_itub4`, o `xfail(strict)` do BLIND-02b) é o
  oráculo — e **deve permanecer xfail** ao fim desta fase (vira verde na Fase 12).

</code_context>

<specifics>
## Specific Ideas

- `g_cap = (1 + π_ciclo)(1 + PIB_real) − 1 = 7,28%`; π_ciclo = 5,18% (IPCA médio 10a, SGS 13522);
  PIB_real = 2,0%.
- Reconciliação com o livro: o app deve **adotar** o `g` por fundamentos (10,29% ITUB4 ≈ 10,24% do
  livro), não o histórico (6,94%).
- Média **aritmética** para o π_ciclo (não geométrica) — para bater a simetria exata com o rf.
- `g_cap` trava só o terminal; o `g` explícito é o do livro (10,24%) e mantém teto Ke — a estrutura
  de dois estágios não pode ser colapsada num teto só.

</specifics>

<deferred>
## Deferred Ideas

- **Conserto do `Ke`/`ke_teto`/`ke_piso`/ERP/beta** — **Fase 12** (regra dura A: consertar o Ke antes
  do g piora o modelo). O BLIND-02 vira verde lá, quando o `ke_teto` sai.
- **Colapso dos 4 motores num RIM único + contrato de saída do livro + corte de knobs `motores:`
  ~11→5** — **Fase 13** (ENG). A remoção final de folhas de knob é contada lá.
- **Rótulos do report / UI** — a atualização de apresentação (`g estável` → `g_cap` derivado; matriz
  de sensibilidade sobre Ke×g corretos) é mínima nesta fase; a reforma de UI do contrato de saída é a
  Fase 13 (UI hint: yes).
- **Validação honesta / hold-out / caso do livro (ITUB4 = R$ 37,22)** — **Fase 14** (VAL). Esta fase
  entrega uma das duas metades; o número final só se prova depois do Ke (Fase 12) e do motor (Fase 13).

### Reviewed Todos (not folded)
None — não havia todos casando com a Fase 11.

</deferred>

---

*Phase: 11-crescimento-g-grow*
*Context gathered: 2026-07-16*
