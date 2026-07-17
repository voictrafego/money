# Phase 13: Motores + contrato de saída (ENG) - Context

**Gathered:** 2026-07-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Colapsar os **4 motores** (`rim`, `lucro_normalizado`, `dcf_crescimento`, `nav_contabil` em
`core/motores.py`) num **RIM único**. Sob clean surplus (Ohlson 1995), RIM ≡ DDM ≡ DCF-equity — os 4
não são 4 opiniões, são 4 implementações do mesmo modelo com inputs inconsistentes; a dispersão
medida (0,81/0,63/0,63/0,48) **é a assinatura dos bugs**, não divergência de método. Entregas
mensuráveis (ENG-01..11):

- **RIM único** (ENG-01); os 3 ex-motores viram **políticas de input** (derivação do ROE-âncora), não
  motores.
- **Ensemble morre** junto com `_guarda_san01` e `_guarda_faixa_ddm` (`report.py:77-182`) — **removidos,
  não portados** (ENG-02). São cicatrizes do viés que mediam os próprios bugs do projeto.
- **Classificador de arquétipo sobrevive e melhora** — deixa de escolher um *modelo* (erro ilimitado) e
  passa a escolher uma *âncora de ROE* (erro limitado) (ENG-03).
- **`PAGADORA_REGULADA` → `PAGADORA_MADURA` + `CONCESSAO_FINITA`** (ENG-04); a concessão finita é
  carve-out (book já = VP da RAP, **não consertar o `g`** sob ICPC 01).
- **Contrato de saída do livro** (ENG-05..08): valor intrínseco → região de valor → tríade
  **SUBAVALIADA / NO INTERVALO / SOBREAVALIADA**; **MS = controle do usuário** simétrica default 5-10%,
  **nunca calibrada** (ENG-06); **matriz Ke×g vive** (ENG-07); **ponte auditável** exibida e é **teste
  de correção** (ENG-08).
- **Guarda-corpo sobre a razão** `0 < P/B justo < 6` (ENG-09) — o RIM sozinho **não** impede CGRA4 a
  921× (`VPA = PL/num_acoes` infla junto).
- **`motores:` de ~20 → ≤5 chaves, contadas** (ENG-10).
- **Ranking rebaixado e re-rotulado, não deletado** → screener comparativo por múltiplos (ENG-11).

**Ordem obrigatória:** esta fase entrega o **motor**; o **número final** (ITUB4 = R$ 37,22) só se prova
na **Fase 14** (VAL) — nada de validar o caso do livro aqui (queima o hold-out).

**Escopo negativo (regras "NÃO fazer" do roadmap):**
- **NÃO calibrar a MS** contra dispersão, preço ou taxa de "compra" (Armadilha 4 — post-mortem do v2.3
  num endereço novo). A MS é escolha do usuário e morre por construção.
- **NÃO inventar contrato de saída novo** — "preço-teto"/"Bazin" têm ZERO ocorrências no PDF; nada de
  viés binário Comprar/Aguardar; nada de MS escalonada da Morningstar.
- **NÃO "consertar" o `dcf_crescimento` com FCFE** (`lpa × payout`) — vira DDM por teorema (Armadilha 2).
- **NÃO consertar o `g` das transmissoras sob ICPC 01** — double-count de inflação; é o carve-out
  `CONCESSAO_FINITA`, declarado ANTES do hold-out.
- **NÃO deletar o Ranking** — rebaixar e re-rotular (deletar joga fora os Cap. 11-12 do livro).

</domain>

<decisions>
## Implementation Decisions

### Âncora de ROE por arquétipo (ENG-01/ENG-03)
- **D-01 (arquétipo → política de ROE-âncora):** `arquetipo.ARQUETIPO_MOTOR` (`arquetipo.py:48-54`)
  deixa de mapear arquétipo→*motor* e passa a mapear arquétipo→**política de derivação do ROE-âncora/base**
  do RIM único. A **fórmula RIM é idêntica** para todos os arquétipos; o que varia por arquétipo é o
  **insumo** (o ROE-âncora e a base de book) que alimenta o `motores.rim(...)`. É o "erro limitado" do
  ENG-03: escolher uma âncora, não um modelo.
- **D-02 (os 3 ex-motores viram funções de derivação de insumo):** `lucro_normalizado`,
  `dcf_crescimento` e `nav_contabil` **não são mais motores primários** — sobrevivem (se sobreviverem)
  apenas como **derivadores de insumo** do RIM (ex.: o lucro normalizado 7-10a → ROE implícito da
  cíclica; o NAV → piso patrimonial). O dispatch `_intrinseco_por_motor` (`report.py:201-327`) colapsa
  num caminho único que sempre chama o RIM com o insumo derivado pela política do arquétipo.
- **D-03 (mapa de âncoras por arquétipo — direção):** financeira/madura → ROE **through-cycle mediana**
  (o `roe_terminal`/`roe_valuation` já usado hoje); cíclica → ROE **implícito do lucro normalizado
  7-10a**; crescimento → ROE **atual + retenção** com fade (o `n_fade` já existente). A granularidade
  exata de cada política fica com o researcher (ver Discricionário), mas o **formato** é
  arquétipo→âncora, não arquétipo→motor.

### Ensemble e guardas (ENG-02)
- **D-04 (remover, não portar):** `_guarda_san01` (`report.py:108-182`), `_guarda_faixa_ddm`
  (`report.py:77-105`), a banda do ensemble (`banda_do_motor`, `divergencia_ativa`, VER-01/ENS-01 em
  `AnaliseAcao`) e a 2ª lente ensemble×DDM + divergência do ranque (`cli.py:203-243`) são **deletados**.
  São cicatrizes do viés: mediam os próprios bugs do projeto e chamam isso de "divergência de método".
  Consertadas as doenças (Fases 9-12), são um 2º erro cancelando o 1º.

### CONCESSAO_FINITA + novo default de arquétipo (ENG-04)
- **D-05 (split com sinal explícito):** o hard-route `c.eh_concessionaria` (`arquetipo.py:159-160`) passa
  a rotular **`CONCESSAO_FINITA`** (sinal explícito, mantém a guarda anti-Petróleo). O default-por-
  eliminação da linha `:180` (hoje `PAGADORA_REGULADA`) passa a ser **`PAGADORA_MADURA`** (RIM normal,
  ROE through-cycle). Empresa **sem sinal deixa de cair no balde da transmissora** — a raiz do bug do
  ENG-04.
- **D-06 (carve-out da concessão finita):** `CONCESSAO_FINITA` usa **modelo de ativo financeiro** — o
  book **já é** o VP da RAP e o ROE dispara em ano de IPCA alto → **não conserta o `g`** (evita
  double-count de inflação sob ICPC 01). A mecânica exata do carve-out no RIM único (g fixado / terminal
  tratado à parte) fica com o researcher, mas a **regra é não aplicar o `g` de inflação** à concessão.

### Contrato de saída — escopo engine + UI mínima (ENG-05/06/07/08)
- **D-07 (engine entrega o contrato completo NESTA fase):** a tríade **SUBAVALIADA / NO INTERVALO /
  SOBREAVALIADA** passa a ser computada de **V vs região de valor** `[V×(1−MS), V×(1+MS)]` (não mais só
  o prefixo do veredito do DDM). A **MS é parâmetro** com default de config, **simétrica 5-10%**, **nunca
  calibrada**. A **ponte auditável** `P/B justo = 1 + (ROE_T − Ke)/(Ke − g)` × VPA = `V` com
  `payout_T = 1 − g/ROE_T` é **exibida**. A **matriz Ke×g** vive (sobre o `a.ke`/`g` corretos das Fases
  11-12).
- **D-08 (UI Streamlit = mudança mínima de exibição):** a tela recebe o **mínimo** para exibir o contrato
  — widget/parâmetro de MS, a tríade, a matriz Ke×g, e a **remoção de "Evitar" e "Qualidade Baixa"**
  (`selo.py:_MATRIZ[("Baixa","Caro")]="Evitar"` e o eixo qualidade "Baixa"), que nunca vieram do livro.
  Reforma visual pesada fica para depois se necessário.
- **D-09 (a tríade migra do DDM para o V do RIM):** hoje `selo.faixa_do_veredito` lê o **prefixo do
  veredito do DDM**; sob RIM único o veredito/tríade passa a vir do **V do RIM vs a região de valor da
  MS**. O selo (BSD/quadrante) permanece como camada derivada, menos os dois rótulos que saem.

### Guarda-corpo P/B justo (ENG-08/ENG-09)
- **D-10 (dois níveis — teste + runtime):**
  - **TESTE de correção:** a identidade fechada `P/B justo = 1 + (ROE_T − Ke)/(Ke − g)` e
    `payout_T = 1 − g/ROE_T` viram **assert**. `payout_T` negativo ou > 100%, ou `P/B justo` fora de
    `(0, 6)`, **FALHA o teste** (é bug, não resultado). O guard é sobre a **razão**, não sobre o valor.
  - **RUNTIME never-raise:** fora da faixa **degrada** (suprime veredito / VERIFICAR), **não levanta** —
    CGRA4 a 921× é **sinalizado**, não quebra a UI. Preserva o contrato `never-raise` das bordas
    (SAN-06). O guard **não** conserta o `VPA = PL/num_acoes` inflado (o motor herda o erro 1:1); ele
    **sinaliza** que a razão implícita é absurda.

### Rebaixamento do Ranking (ENG-11)
- **D-11 (sai o nível de preço; ficam múltiplos crus):** as colunas **preço-alvo / upside / veredito**
  saem do Ranking — imputam **nível de preço**, e a regressão de pares é *matematicamente cega ao nível*
  (multiplicar o preço de todas as elétricas por 1,5 dá upsides bit-a-bit idênticos). O screener passa a
  mostrar **múltiplos crus comparáveis e ordenáveis** (P/L, P/VP, DY, BSD) — o comparativo relativo do
  Cap. 11-12. A parte de `comparables.preco_alvo_por_regressao` que gera **preço-alvo/upside** sai do
  caminho do Ranking; o **comparativo por múltiplos** permanece. O ensemble×DDM + divergência
  (`cli.py:203-243`) é removido com o ENG-02.

### Corte de knobs `motores:` (ENG-10)
- **D-12 (deleção contada, lock no mesmo diff):** o bloco `motores:` do `config.yaml` (`:245-...`) vai de
  **~20 chaves para ≤ 5** e a **contagem é critério de verificação** (regra dura C — sem número
  contável, a deleção não acontece). Como `dcf_crescimento`/`lucro_normalizado`/`nav_contabil` deixam de
  ser motores, os sub-blocos `motores.ciclica` e `motores.crescimento` colapsam (o que sobreviver vira
  política de input, ver D-02). Qualquer folha de valuation que saia do `config.yaml` sai da partição do
  `calibracao.lock.yaml` **no mesmo commit** (CLAUDE.md); a contagem de folhas e `test_knobs_batem_com_o_lock`
  refletem. **Orçamento intacto em 3 graus** (`ERP`, `n_fade`, `PIB_real`) — nenhum grau novo.

### Claude's Discretion
- O usuário escolheu a **opção recomendada em todas** as 5 perguntas (nenhum "Você decide" acionado).
  Fica ao researcher/planner, dentro das decisões acima:
  - o **mapa exato** de arquétipo → política de ROE-âncora (D-03), calibrado ao código e à distribuição
    dos 104 tickers;
  - a **mecânica precisa do carve-out** `CONCESSAO_FINITA` no RIM único (D-06: como o `g` é fixado / o
    terminal tratado à parte);
  - **quais são exatamente as ≤5 chaves finais** do bloco `motores:` e o destino de
    `ciclica.anos_media` / `crescimento.n_anos_explicito` como políticas de input (D-12);
  - o **formato exato** da ponte P/B exibida e dos rótulos do contrato de saída (D-07/D-08);
  - a **divisão em waves** e a ordem dos commits atômicos (o diff de knob sancionado do lock precisa ser
    coeso);
  - o **conjunto exato de colunas** do screener rebaixado (D-11).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e critérios da fase
- `.planning/ROADMAP.md` §"Phase 13: Motores + contrato de saída (ENG)" (linhas ~247-269) — goal, 5
  success criteria, regras "NÃO fazer" (não calibrar MS, não inventar contrato, não consertar dcf com
  FCFE, não consertar g das transmissoras, não deletar o Ranking).
- `.planning/ROADMAP.md` §"Overview" — regra dura **(A)** (ordem provada por simulação), **(B)** (golden
  que quebra é DELETADO), **(C)** (deleção de knobs é **contada**; `motores:` ~20 → ≤5; orçamento travado
  em 3 graus `ERP`/`n_fade`/`PIB_real`).
- `.planning/ROADMAP.md` §"Phase 14: VAL" — critério soberano: ITUB4 = R$ 37,22 (g=10,24%, Ke=12,48%) —
  o número que **esta fase entrega o motor para**, mas que **não valida aqui** (queima o hold-out).
- `.planning/REQUIREMENTS.md` ENG-01..11 (linhas 195-229) — rastreabilidade e o "por quê" de cada
  requisito; e a seção "Future Requirements" (linhas 253-261: motor `nav`/SOTP real para holdings,
  score BSD por arquétipo) que **fica deferida**.

### Método do livro (precedência sobre qualquer requisito conflitante)
- `.planning/REQUIREMENTS.md` §"Critério de aceite soberano" (linhas 8-18) — o livro tem precedência;
  "preço-teto": 0 ocorrências, "Bazin": 0, "valor intrínseco": 39. Cap. 17 = tríade + MS do usuário +
  matriz Ke×g ("a que mais gostamos").
- `Referencias/` (PDF do livro *O Investidor em Ações de Dividendos*, se presente) — Cap. 11-12
  (comparativo por múltiplos → Ranking rebaixado) e Cap. 17 (contrato de saída, MS simétrica escolhida
  pelo usuário, matriz Ke×g).

### Contexto herdado das fases anteriores (inputs prontos do RIM único)
- `.planning/phases/12-custo-de-capital-ke-ke/12-CONTEXT.md` — `a.ke` único (β setorial+Blume, ERP 4,5%,
  sem clamp) alimenta os 4 consumidores; matriz Ke×g em torno do `a.ke`; BLIND-02b curado. Lista o
  **deferido para a Fase 13**: guard P/B, colapso dos 4 motores, contrato do livro, corte final de knobs.
- `.planning/phases/11-crescimento-g-grow/11-CONTEXT.md` — `g_cap = 7,28%`, `g_T = min(ROE_T×retenção,
  g_cap)`, `excesso_sustentavel`/`ke_g_spread_min` load-bearing; rota seguradora e cascata VULC3 já
  tratadas; dívida WR-04 (funções mistas de Ke) em aberto.

### Orçamento de knobs / lock (mudança obrigatória nesta fase)
- `CLAUDE.md` §"O que significa suíte verde" — golden que quebra é **DELETADO não atualizado**; orçamento
  de 3 knobs; **justificativa de knob nunca menciona ticker** (teste + `.githooks/commit-msg`); knob de
  valuation muda **com** o lock no mesmo diff; nunca afrouxar tolerância / trocar `xfail` por `skip` /
  deletar assert para ficar verde. `tests/classificacao.yaml` (completude imposta na coleta).
- `calibracao.lock.yaml` — partição `congelados`/graus; as folhas de `motores.ciclica`/`motores.crescimento`
  que saírem do config saem da partição no **mesmo commit** (D-12).
- `config.yaml:245-...` (bloco `motores:` — `rim`/`ciclica`/`crescimento`) — o alvo do corte ~20 → ≤5.

### Código-alvo (o que muda)
- `src/analista/core/motores.py` — `rim` (`:66-146`, o motor único que sobrevive), `lucro_normalizado`
  (`:149`), `dcf_crescimento` (`:161`), `nav_contabil` (`:195`) → viram derivadores de insumo (D-02) ou
  são removidos.
- `src/analista/core/arquetipo.py` — `ARQUETIPO_MOTOR` (`:48-54` → vira `ARQUETIPO_ANCORA_ROE`, D-01);
  `classificar` (`:124-190`, split do hard-route `:159` e do default `:180`, D-05); `_setor_casa_token`
  (`:107`, reutilizável para o token de concessão).
- `src/analista/report/report.py` — `_guarda_faixa_ddm` (`:77`), `_guarda_san01` (`:108`) → **deletar**
  (D-04); `_intrinseco_por_motor` (`:201-327`) → colapsar num caminho RIM único (D-02); `_roe_through_cycle`
  (`:184`) → a âncora through-cycle (D-03); `AnaliseAcao` (`:54-77`, remover `banda_do_motor`/
  `divergencia_ativa`/`motor_pendente`, D-04/D-09); a matriz de sensibilidade Ke×g (herdada da Fase 12).
- `src/analista/report/selo.py` — `_MATRIZ` (`:48-55`, remover "Evitar"; `_qualidade` eixo "Baixa",
  D-08); `faixa_do_veredito` (`:88`, a tríade passa a vir do V do RIM, D-09).
- `src/analista/core/comparables.py` — `preco_alvo_por_regressao` (`:181`), `ResultadoComparaveis`
  (`preco_alvo`/`upside`/`subavaliada`, `:175-214`) → a parte de preço-alvo/upside sai do Ranking; o
  comparativo por múltiplos permanece (D-11).
- `src/analista/cli.py` — o caminho do Ranking (`:164-...`): a 2ª lente ensemble×DDM + divergência
  (`:203-243`) é removida (D-04/D-11); colunas preço-alvo/upside/veredito saem (D-11).
- `src/analista/core/freio.py` (`:36-56`) — supressão de alvo/upside degenerado; alinhar com a saída do
  preço-alvo do Ranking.

### Contexto de raciocínio (memórias do projeto, não versionadas no repo)
- `duas-doencas-do-valuation` — as duas doenças e a ordem de conserto; por que 3 "correções óbvias"
  pioram o modelo (relevante para não "consertar" dcf/g nesta fase).
- `ranking-e-cego-ao-preco` — a regressão de pares **não pode** dizer que o setor está caro; base do
  ENG-11 (D-11).
- `ddm-nao-consertar-e-lente-nao-motor` — o DDM é lente, não motor; a tríade migra para o V do RIM sem
  mexer nas primitivas do DDM (D-09).
- `rim-terminal-value-root-cause` — o RIM terminal e o excesso sustentável; insumo para o carve-out da
  concessão (D-06) e o guard P/B (D-10).
- `guardrails-devem-ser-provados-por-execucao` — "suíte verde" não prova blindagem; o guard P/B e o corte
  de knobs precisam ser provados por execução (regressão dos 104 tickers), não só por teste verde.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `motores.rim(vpa0, roe0, ke, retencao, n, excesso_sustentavel, g_terminal, ke_g_spread_min, fade_para,
  roe_terminal)` (`motores.py:66`) — **o motor único** que sobrevive. Já é RIM híbrido multiestágio
  (janela explícita + terminal Gordon), never-raise, com terminal normalizado through-cycle (`roe_terminal`)
  e anti-bad-bank. A ponte P/B do ENG-08 é derivável dele.
- `report._intrinseco_por_motor` (`report.py:201`) — o dispatch motor→intrínseco que **colapsa** num
  caminho RIM único; hoje já roteia rim/normalizado/dcf/nav/ddm.
- `report._roe_through_cycle` (`report.py:184`) — a âncora de ROE through-cycle (mediana da série),
  insumo direto da política de âncora do arquétipo (D-03).
- `arquetipo.classificar` + `ARQUETIPO_MOTOR` (`arquetipo.py:48,124`) — o classificador que **sobrevive e
  melhora** (D-01); `eh_concessionaria` já é sinal disponível no ingest para o split (D-05).
- `comparables.py` — o comparativo por múltiplos (Cap. 11-12) que **permanece** no screener; só a imputação
  de preço-alvo/upside sai (D-11).
- `selo.montar_selo` / `_MATRIZ` / `faixa_do_veredito` (`selo.py`) — a camada derivada do contrato de saída;
  firewall (nunca importa `report.py`), config-driven, copy descritiva. Ajuste cirúrgico (D-08/D-09).
- Matriz de sensibilidade Ke×g (herdada da Fase 12, em torno do `a.ke` único) — o ENG-07 reusa, não
  reinventa.

### Established Patterns
- **Never-raise nas bordas (SAN-06):** todo assert degrada para aviso + confiança rebaixada, nunca
  levanta. O guard P/B em runtime (D-10) segue esse contrato; o assert de correção vive no **teste**.
- **Fonte única cross-modo (WR-03):** `analyze` e `rank` leem os mesmos números carimbados; o contrato de
  saída e a matriz Ke×g devem ser **idênticos** entre menus (herdado da Fase 12, D-06/D-14 de lá).
- **Engine pura:** `analisar_acao` nunca toca a rede; políticas de input do RIM leem só sinais que
  `CompanyData` já expõe.
- **Diff de knob sancionado é coeso (CLAUDE.md):** o corte de `motores:` muda **com** o lock no mesmo
  commit; a contagem de folhas reflete (D-12).
- **Classificação de testes imposta na coleta (`tests/classificacao.yaml`):** teste novo (contrato,
  ponte P/B, guard) precisa de entrada na classificação ou **quebra a coleta**. Golden de nível que
  quebrar é **deletado**, não atualizado.

### Integration Points
- O `a.ke` único (Fase 12) e o `g_cap`/`g_T` (Fase 11) são os **insumos prontos** do RIM único — esta
  fase **não** os recomputa.
- A tríade do contrato (D-09) conecta `report.py` (V do RIM + região da MS) → `selo.py`
  (`faixa_do_veredito`) → tela Streamlit.
- O corte de `motores:` (config.yaml) ↔ `calibracao.lock.yaml` ↔ `test_knobs_batem_com_o_lock` —
  precisam mudar juntos (D-12).
- A regressão dos **104 tickers ao vivo** é o oráculo do guard P/B e do "nada explode sem clamp" (herdado
  do padrão GROW-04/05, KE-04/D-11 da Fase 12).

</code_context>

<specifics>
## Specific Ideas

- `ARQUETIPO_MOTOR` → `ARQUETIPO_ANCORA_ROE`: arquétipo escolhe **âncora de ROE**, não motor (erro
  limitado, ENG-03).
- Split: `eh_concessionaria` → `CONCESSAO_FINITA` (carve-out, não conserta g); default-por-eliminação →
  `PAGADORA_MADURA` (RIM normal).
- Tríade de V vs região `[V×(1−MS), V×(1+MS)]`; MS default de config, simétrica 5-10%, **nunca calibrada**.
- Ponte exibida: `P/B justo = 1 + (ROE_T − Ke)/(Ke − g)`; `payout_T = 1 − g/ROE_T`; payout_T negativo/>100%
  ou P/B fora de (0,6) = **bug** (assert em teste); runtime degrada never-raise.
- Ranking: fora preço-alvo/upside/veredito; dentro múltiplos crus (P/L, P/VP, DY, BSD); ensemble/divergência
  removidos.
- `motores:` ~20 → ≤5 chaves, **contadas**; lock no mesmo diff; orçamento intacto em 3 graus.

</specifics>

<deferred>
## Deferred Ideas

- **Validação honesta / hold-out / caso do livro (ITUB4 = R$ 37,22)** — **Fase 14** (VAL). Esta fase
  entrega o motor; o número final só se prova depois, uma única vez (VAL-04). Validar aqui queima o
  hold-out.
- **Motor `nav`/SOTP real para holdings** (ITSA4, B3SA3) — **Future Requirement** (REQUIREMENTS.md:255).
  Nesta fase o NAV é, no máximo, piso patrimonial/insumo do RIM, não SOTP por segmento.
- **Score BSD por arquétipo** (`cobertura_juros` constante 50; FCO de banco) — **Future Requirement**
  (REQUIREMENTS.md:258). O selo permanece como está (menos "Evitar"/"Qualidade Baixa").
- **Reforma visual pesada da tela Streamlit** — nesta fase a UI recebe só o mínimo de exibição do contrato
  (D-08); layout/estética aprofundados ficam para depois se necessário.
- **Deflator no `dpa_recorrente`** e séries longas de dividendo — Future Requirement (REQUIREMENTS.md:261).

### Reviewed Todos (not folded)
None — não havia todos casando com a Fase 13 (`todo.match-phase 13` retornou 0).

</deferred>

---

*Phase: 13-motores-contrato-de-sa-da-eng*
*Context gathered: 2026-07-17*
