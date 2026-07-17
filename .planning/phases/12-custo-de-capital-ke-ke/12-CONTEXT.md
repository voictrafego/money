# Phase 12: Custo de capital / `Ke` (KE) - Context

**Gathered:** 2026-07-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Curar a **outra metade da Doença 1** (o `Ke`), e **só agora** — porque tirar o clamp
(`ke_teto`/`ke_piso`) só é seguro **depois** do `g` (Fase 11). Alvo do livro: `Ke` = 12,48%.

Entregas mensuráveis (KE-01..05):
- **Um único `Ke` no sistema.** Hoje há dois simultâneos — `capm.ke_local` → `a.ke` (DDM/manchete)
  e `motores.ke_rim` (RIM, com `erp_banco` + clamp). O `Ke` **exibido** passa a ser **o mesmo** que
  produziu o número, e a matriz de sensibilidade é construída em torno dele (KE-01/KE-05).
- **ERP único = 4,5%** (Damodaran mature market), **sem** o prêmio small-cap de 1,5% — injustificável
  num universo já filtrado por liquidez de R$ 15M/dia. `capm.erp_local` 0,06 → 0,045 (KE-02).
- **Beta setorial + Blume** (`0,33 + 0,67 × β`), não individual bruto — BB e Bradesco, mesmo risco de
  negócio, param de receber `Ke` com 1,7pp de diferença; some o ruído que produzia 2,7× de
  espalhamento no valor final (KE-03).
- **`ke_piso` e `ke_teto` removidos** do código e do config. Com `Ke_min ≈ 11,07%` (piso estrutural do
  Blume) > `g_cap = 7,28%`, nenhuma perpetuidade pode divergir — **por aritmética, não por clamp** (KE-04).

**Escopo negativo (regras "NÃO fazer" do roadmap):**
- **NÃO reintroduzir um clamp com outro nome** quando algum ticker ficar feio sem o `ke_teto`. Se um
  valor explodir sem clamp, o bug está em `ROE_T` ou no spread — não no Ke. O guarda-corpo sobre a
  **razão** (`0 < P/B justo < 6`) é a **Fase 13**, não esta.
- **NÃO recalibrar o `g` da Fase 11** para "acomodar" o Ke novo — as duas fases são medições
  independentes; misturá-las apaga o diagnóstico.
- **NÃO criar prêmio de risco por ticker/setor** para explicar um caso — grau de liberdade fora do
  orçamento de 3 (BLIND-06).

**Fronteira de teste crítica:** o **BLIND-02b vira verde AQUI** (`test_invariancia_inflacao_engine_itub4`,
`xfail(strict=True)`). Enquanto o `ke_teto = 0,13` existia (até a Fase 11), ele **saturava** sob o
choque de +300 bps e o `Ke` não se movia 1 bp — a Doença 3. Removido o clamp, o `Ke` reage ao `rf` e o
teste passa a ser satisfeito **pelo código**, não por afrouxamento. O `xfail` é **removido** nesta fase
(vira teste normal que passa; `xfail_estritos()` cai de 2→1). O golden **`ITUB4 = 32,88` DEVE quebrar e
ser DELETADO** — é **critério de saída explícito** (dois erros que se anulavam), **não** regressão.

</domain>

<decisions>
## Implementation Decisions

### Beta setorial — método de agregação (KE-03)
- **D-01 (chave de agrupamento):** agrupar pelo **setor CVM** (`c.setor`, string econômica —
  "Bancos", "Energia Elétrica"…). É a "industry beta" de Damodaran, disponível já no **ingest** (antes
  do Ke), e faz BB×Bradesco caírem no mesmo grupo. **Não** usar o `arquetipo` como chave: ele é
  computado **depois** do Ke hoje (`report.py:489` vs `:470`) e exigiria reordenar.
- **D-02 (estatística):** **mediana** dos betas crus dos pares do setor — robusta a outliers (um beta
  distorcido não contamina o grupo), padrão para betas setoriais ruidosos da B3.
- **D-03 (ordem Blume × agregação — discricionária):** Blume (`0,33 + 0,67×β`) é linear e monotônico,
  então **agregar-β-cru→Blume ≡ Blume→agregar** para mediana/média. Aplicar Blume **uma vez**, sobre o
  β setorial agregado (implementação mais limpa, um único ponto de ajuste).
- **D-04 (fallback):** grupo com pares **< limiar estrutural** (ex.: 3), ou ticker **sem setor** →
  usar o **próprio `c.beta` com Blume aplicado** (β individual Blume-ajustado). Degradação graciosa,
  never-raise; o limiar é **estrutural, não calibrado contra ticker** (justificativa de knob nunca
  menciona ticker — `.githooks/commit-msg`).

### Onde o β setorial é computado — pureza da engine (KE-03/integração)
- **D-05 (fonte = artefato pré-computado e versionado):** um passo **offline** gera o mapa
  `setor → mediana(β cru)` a partir dos betas do universo (dado real — respeita o "derivado, não
  digitado" do GROW-01), grava num **arquivo versionado**; os **entry points carimbam** o mapa em
  `cfg` e a engine lê `cfg[...][setor]` e aplica Blume. Determinístico, offline, engine-pura. **Não**
  tabela digitada à mão (viola "derivado, não digitado"). **Não** computar dinâmico por run — ver D-06.
- **D-06 (invariante analyze==rank, DURO + teste):** o β setorial (logo o Ke) da **mesma ação** deve
  ser **idêntico** entre `analyze` e `rank`. Computar a mediana dinamicamente por run é o **anti-padrão
  WR-03**: `cmd_analyze` monta **1 ticker** e não tem os pares; só `rank`/`screen` têm → drift. Solução:
  **fonte única carimbada** (espelha `_carimbar_macro`/`rf_local`), com **teste** garantindo que
  analyze e rank leem o mesmo mapa. É o KE-05 na prática.
- **D-07 (β setorial é DADO, FORA do lock):** o β vem do mercado (medido, auto-atualiza), **não** é
  knob de calibração — igual a `rf_local` (Selic-ciclo) e `pi_ciclo`. **Não** entra no orçamento de 3
  graus (`ERP`, `n_fade`, `PIB_real`) e **não** mexe em `calibracao.lock.yaml`. (A mediana e o limiar
  de pares são estruturais, não graus de liberdade calibráveis.)

### Unificação dos dois Ke — fonte única (KE-01/KE-05)
- **D-08 (deletar `ke_rim`):** `motores.ke_rim` é **removido**; `report.py:261` passa a alimentar o RIM
  com o **`a.ke` único**. Com ERP=0,045 e clamp fora, `ke_rim` já colapsa **exatamente** em `ke_local`
  — deletar é limpo e apaga a Doença 3 (BLIND-02b). **Não** manter passthrough neutralizado (deixaria
  uma 2ª porta de entrada de Ke viva, contra o corte de knobs da Fase 13).
- **D-09 (RIM recebe `a.ke` pronto — não recomputa):** o Ke único é computado **uma vez**
  (`capm.ke_local` com β setorial+Blume e ERP 0,045), carimbado em `a.ke`, e **todos** os consumidores
  (DDM, RIM, rota de segurança `report.py:240-241`, matriz Ke×g) leem o **mesmo** `a.ke`. É o KE-05
  literal; evita drift futuro de dois pontos de cálculo.
- **D-10 (limpeza config + lock no MESMO diff):** `erp_banco`, `ke_piso`, `ke_teto` saem do
  `config.yaml` (bloco `motores.rim`); as **folhas congeladas** correspondentes saem da partição do
  `calibracao.lock.yaml` no **mesmo commit** (como D-05 fez na Fase 11); `test_knobs_batem_com_o_lock` e
  a contagem de folhas (29 → menos) refletem. **NÃO** recriar clamp com outro nome.

### Validação sem clamp + Ke exibido (KE-04/KE-05)
- **D-11 (postura de validação):** provar "nada explode" com **(a)** regressão contra o **mapa REAL de
  104 tickers** (como GROW-04/05) checando que nenhum `V` explode, **+ (b)** teste do **invariante
  estrutural** `Ke_min(Blume) ≈ 11,07% > g_cap = 7,28%` (perpetuidade converge por aritmética). **SEM**
  novo guard nesta fase — o guarda-corpo sobre a razão P/B é a Fase 13.
- **D-12 (ERP + golden no mesmo diff):** `capm.erp_local` **0,06 → 0,045** (valor do grau `ERP` no
  lock, `caminho: capm.erp_local`, atualizado no mesmo commit); o golden `ITUB4 = 32,88` **quebra e é
  DELETADO** (não atualizado — critério de saída, não regressão). Junto com D-10, tudo no mesmo diff de
  knob sancionado.
- **D-13 (destravar BLIND-02b):** remover o marker `xfail(strict=True)` de
  `test_invariancia_inflacao_engine_itub4`; o teste passa a **asseverar a invariância de verdade** e
  **passa** porque o sistema mudou (clamp fora → Ke reage ao rf). **NÃO afrouxar o limiar** — só remover
  o xfail. `test_blindagem_meta` (`xfail_estritos()`) reflete a queda 2→1.
- **D-14 (Ke exibido único + matriz):** o report exibe **`a.ke`** como **O** Ke (nunca `ke_rim`); a
  matriz de sensibilidade é sempre `delta_ke × delta_g` em torno do `a.ke` único, **idêntica** entre
  `analyze`/`rank`. Remover qualquer exibição de Ke que não seja o `a.ke`.

### Claude's Discretion
- O usuário escolheu a opção recomendada em **todas** as perguntas (nenhum "Você decide" acionado).
  Detalhes deixados ao researcher/planner dentro das decisões acima: o **nome/formato exato do arquivo
  do artefato** de betas setoriais e sua chave em `cfg`; o **valor exato do limiar** de pares do
  fallback (D-04) a partir da distribuição real dos setores nos 104 tickers; a **assinatura** do
  gerador offline e do helper de carimbo (irmão de `_carimbar_macro`); a **ordem dos commits atômicos**
  (o diff de knob sancionado do lock precisa ser coeso); os **rótulos exatos** do report/matriz (D-14);
  como a **partição das folhas** do lock é reescrita (D-10).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e critérios da fase
- `.planning/ROADMAP.md` §"Phase 12: Custo de capital / `Ke` (KE)" — goal, 4 success criteria, regras
  "NÃO fazer" (não reintroduzir clamp, não recalibrar o g, não criar prêmio por ticker).
- `.planning/ROADMAP.md` §"Overview" — regra dura **(A)** (não fundir g com Ke; ordem provada por
  simulação), **(B)** (o golden `ITUB4 = 32,88` DEVE quebrar e ser DELETADO), **(C)** (deleção de knobs
  é contada; orçamento travado em 3 graus).
- `.planning/ROADMAP.md` §"Phase 14: VAL" — critério soberano: ITUB4 = R$ 37,22 com g=10,24%,
  Ke=12,48% — o que esta fase não pode quebrar rio abaixo.
- `.planning/REQUIREMENTS.md` KE-01..05 (linhas 182-193) — rastreabilidade e números-alvo.
- `.planning/phases/11-crescimento-g-grow/11-CONTEXT.md` — a metade `g` já curada (g_cap=7,28%,
  π_ciclo=5,18%, PIB_real=2,0%), o padrão de carimbo do `pi_ciclo` (template do D-05/D-06) e a fronteira
  "BLIND-02 NÃO vira verde na Fase 11 — vira na 12".

### Orçamento de knobs / lock (mudança obrigatória nesta fase)
- `calibracao.lock.yaml:58-72` (grau **ERP**, `caminho: capm.erp_local`) — mudar o valor 0,06→0,045 no
  mesmo diff (D-12). O comentário já anota "KE-02 (Fase 12) UNIFICA — sobra UM ERP".
- `calibracao.lock.yaml:122-131` (`congelados`) — `motores.rim.erp_banco: 0.045`, `ke_piso`, `ke_teto`
  saem da partição; a contagem de folhas (29 → menos) e `test_knobs_batem_com_o_lock` refletem (D-10).
- `CLAUDE.md` §"O que significa suíte verde" — golden que quebra é **DELETADO não atualizado**;
  orçamento de 3 knobs; **justificativa de knob nunca menciona ticker** (teste + `.githooks/commit-msg`);
  qualquer knob de valuation exige mexer no lock no mesmo diff; nunca afrouxar tolerância / trocar
  `xfail` por `skip` para ficar verde.

### Código-alvo (o que muda)
- `src/analista/core/capm.py` — `ke_local`, `beta`, `CapmParams` (a fórmula única do Ke; o β setorial+
  Blume entra aqui ou num helper irmão).
- `src/analista/core/motores.py:148-172` — `ke_rim` (a **deletar**, D-08) e seus knobs `erp_banco`/
  `ke_piso`/`ke_teto`.
- `src/analista/report/report.py:463-482` (cálculo de `a.ke` via `capm.ke_local`), `:261`
  (`motores.ke_rim(c.beta, cfg)` → passar `a.ke`), `:539-566` (matriz de sensibilidade em torno do
  `a.ke`), `:240-241` (rota de segurança já usa `a.ke`).
- `src/analista/cli.py:66-91` (`_carimbar_macro`) e `src/analista/report/setup.py` — o ponto de carimbo
  único a espelhar para o mapa de betas setoriais (D-05/D-06). `cmd_analyze` (`:96`) monta 1 ticker;
  `cmd_screen`/`cmd_rank` (`:114`/`:164`) montam muitos — a fonte única precisa servir os dois igual.
- `src/analista/ingest/build.py:139-168` — onde `c.setor` é resolvido (chave de agrupamento, D-01) e
  `c.beta` é preenchido (`dm.beta`, insumo cru do artefato).
- `config.yaml:72-96` (bloco `capm`, `erp_local`) e `config.yaml:244-268` (bloco `motores.rim`,
  `erp_banco`/`ke_piso`/`ke_teto`).
- `tests/test_blindagem_orcamento.py:238-239` e o teste `test_invariancia_inflacao_engine_itub4`
  (BLIND-02b, `xfail strict` a remover, D-13); `tests/test_blindagem_meta.py:60-68`
  (`xfail_estritos()`); o golden `ITUB4 = 32,88` a deletar (localizar em `tests/`).

### Contexto de raciocínio (memórias do projeto, não versionadas no repo)
- `duas-doencas-do-valuation` — viés (g nominal×real) e dispersão; por que **g antes de Ke**; 3
  "correções óbvias" PIORAM o modelo.
- `rim-terminal-value-root-cause` — pós-v2.3 ITUB4 RIM=R$32,88; por que o `ke_teto` era cirúrgico e o
  clamp saturava (a Doença 3 que esta fase remove).
- `ddm-nao-consertar-e-lente-nao-motor` — o DDM é lente, não motor; a mudança de Ke precisa ser
  validada contra o mapa de 104 tickers antes do plano (D-11).
- `guardrails-devem-ser-provados-por-execucao` — "suíte verde" não prova blindagem; rodar a regressão
  dos 104 tickers é o que vale (D-11).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `capm.ke_local(beta, rf_local, erp_local)` (`capm.py:69`) — a fórmula única `rf + β×ERP`; passa a
  receber o **β setorial+Blume** e **ERP 0,045**. É a fonte única do Ke (D-09).
- `cli._carimbar_macro(cfg)` (`cli.py:66`) — o **template exato** do carimbo de fonte única para
  TODOS os entry points (rf_local, pi_ciclo, deflatores). O mapa de betas setoriais segue o mesmo
  padrão (D-05/D-06): rede/artefato resolvidos no entry point, engine lê `cfg`.
- `macro.selic_ciclo_para_capm` / `macro.ipca_ciclo_para_g` (Fase 10/11) — o padrão "derivado de fonte,
  carimbado, degradação graciosa" que o gerador do artefato de betas espelha.
- `c.setor` (resolvido em `build.py:142`, `fundamentals.setor`) — a chave de agrupamento (D-01), já
  disponível no ingest antes do Ke.
- `arquetipo._setor_casa_token` (`arquetipo.py:107`) — casamento de token de setor por limite de
  palavra; útil se o agrupamento precisar normalizar strings CVM (não como chave, mas como utilitário).

### Established Patterns
- **Pureza da engine:** rf/IPCA são resolvidos UMA vez nos entry points e carimbados em `cfg`;
  `analisar_acao` **nunca** toca a rede. O mapa de betas setoriais DEVE respeitar essa fronteira (D-05).
- **Fonte única para todos os menus (WR-03):** `analyze` E `rank` chamam o MESMO carimbo — sem isso a
  mesma ação mostra número diferente entre menus. O β setorial tem exatamente esse risco (D-06).
- **Never-raise nas bordas:** `ke_rim` degrada com `beta None → None` e lê config defensivamente; a
  fórmula única e o fallback do β setorial (D-04) preservam esse contrato.
- **Diff de knob sancionado é coeso:** qualquer knob de valuation muda **com** o lock no mesmo commit
  (CLAUDE.md); ERP muda de valor, três folhas saem da partição (D-10/D-12).

### Integration Points
- O `a.ke` único alimenta **quatro** consumidores: DDM (banda vmin/vmax = matriz de sensibilidade),
  RIM (`report.py:261`), rota de segurança (`report.py:240-241`) e a matriz Ke×g — ponto único de
  verdade (D-09/D-14).
- O mapa `setor → β` é carimbado no entry point e consumido por `analyze`/`rank`/`screen`
  identicamente (D-06).
- A suíte de blindagem (`test_invariancia_inflacao_engine_itub4` / BLIND-02b, `test_blindagem_meta`) é
  o oráculo — o `xfail` sai porque o código passou a satisfazer, não porque alguém afrouxou (D-13).

</code_context>

<specifics>
## Specific Ideas

- ERP único = **4,5%** (`capm.erp_local` 0,06→0,045); some o prêmio small-cap de 1,5%.
- Beta setorial+Blume = `0,33 + 0,67 × mediana(β cru do setor CVM)`; fallback β individual Blume.
- `Ke_min ≈ 11,07%` (piso estrutural do Blume) > `g_cap = 7,28%` → perpetuidade converge por
  aritmética, sem clamp.
- Dois Ke hoje: 17,3% (DDM ao vivo) e 13,0% (RIM) — colapsam num só ≈ 12,48% (alvo do livro).
- O golden `ITUB4 = 32,88` é dois erros que se anulavam — deletar, não atualizar.

</specifics>

<deferred>
## Deferred Ideas

- **Guarda-corpo sobre a razão P/B justo (`0 < P/B < 6`)** — **Fase 13** (ENG). Não é o clamp de Ke; é
  o guard que impede o CGRA4 a 921× e vive na ponte auditável do RIM único.
- **Colapso dos 4 motores num RIM único + contrato de saída do livro + corte final de knobs `motores:`
  ~11→≤5** — **Fase 13** (ENG). A remoção final de folhas (incl. as que esta fase começa a cortar) é
  contada lá.
- **Validação honesta / hold-out / caso do livro (ITUB4 = R$ 37,22)** — **Fase 14** (VAL). Esta fase
  entrega a segunda metade da Doença 1; o número final só se prova depois do motor (Fase 13).
- **Reforma de UI do contrato de saída** (tríade, matriz Ke×g sobre Ke/g corretos, MS do usuário) —
  Fase 13. Nesta fase a mudança de apresentação é mínima (exibir o `a.ke` único, D-14).

### Reviewed Todos (not folded)
None — não havia todos casando com a Fase 12.

</deferred>

---

*Phase: 12-custo-de-capital-ke-ke*
*Context gathered: 2026-07-17*
