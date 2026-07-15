# Phase 10: Primitivas sem viés (PRIM) - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Tirar o **viés das primitivas de valuation** — a base de lucro normalizada, `roe_valuation`/`lpa_valuation`, a base do CAGR (`g_historico`) e a base do motor cíclico — para que parem de:
- **punir crescimento** (o `median()` de 3 anos em `base_normalizada` é o ano-do-meio; haircut medido de −9,1% num crescedor de 10%);
- **cruzar bases temporais** (`roe_valuation` = lucro normalizado de 3a ÷ PL médio do último ano);
- **winsorizar a tendência** (a winsorização na série temporal ressuscita ano de prejuízo e fabrica `g`);
- **somar reais nominais** entre anos (o motor cíclico soma reais de 2015 com 2024; IPCA acumulado de 58%).

**Critério de saída (PRIM-05, NÃO é regressão):** o golden `ITUB4 = 32,88 ± 0,20` **QUEBRA e é DELETADO, não atualizado** — ele foi calibrado para cancelar o haircut da normalização (dois erros se anulando). A fase não está concluída enquanto ele existir no repositório.

Esta fase move **apenas primitivas** (dados já corretos após a Fase 9). NÃO toca em `g_cap`, `Ke`, `ke_teto`, `ke_piso`, ERP, beta ou motor — isso é Fases 11 e 12, nessa ordem.
</domain>

<decisions>
## Implementation Decisions

### Estimador de normalização do lucro (PRIM-01 / BLIND-03)
- **D-01:** Substituir o `median()` de 3 anos em `base_normalizada` (`normalizacao.py:58-75`) por um **endpoint de regressão robusta (Theil-Sen)**: ajustar uma tendência robusta na série de lucro e usar o valor ajustado **no ano atual**. Reflete crescimento, mantém o ano recente e é robusto a 1 exercício atípico — que é exatamente o que o BLIND-03 exige.
- **D-01a (a validar na pesquisa):** a memória `duas-doencas-do-valuation` avisa que "3 correções óbvias PIORAM o modelo". O `gsd-phase-researcher` DEVE validar o estimador Theil-Sen contra o mapa de 104 tickers antes do planejamento — confirmar que não overshoota e que o alvo do critério de saída (BLIND-03 verde, golden 32,88 quebrando) se materializa.
- **D-01b:** o estimador precisa de um **fallback para séries curtas** (N=1 → o próprio valor; N=2 → média/mediana simples), porque Theil-Sen degenera com poucos pontos. Manter a fronteira de `None` para série vazia.

### roe_valuation (PRIM-02)
- **D-02:** `roe_valuation` deixa de cruzar bases e passa a ser a **mediana da série de ROEs anuais**. Cada ROE anual usa a definição já existente de `roe(ano)` (lucro_t ÷ **PL médio(t-1, t)**, `fundamentals.py:125`), e a mediana é tomada sobre a **série completa** — espelhando `mediana_payout` (D-04, série completa sem janela de 3a). Alvo de ancoragem: ITUB4 16,1% → **18,0%**.

### Deflação do motor cíclico (PRIM-04)
- **D-03:** Deflacionar a base do motor cíclico por **IPCA do Banco Central (BCB SGS, via o `macro.py` que já puxa o BCB)**, trazendo a série a **reais do último ano** (real-terms "de hoje"). **Escopo limitado ao motor cíclico** — a deflação da base do CAGR/`g` fica para a Fase 11, para não misturar a medição das primitivas com a do `g`. Alvo: CSNA3 deixa de sair 31,8% subvalorizada só por nominalidade.

### Winsorização (PRIM-03)
- **D-04:** **Remover** a winsorização da série temporal (`serie_winsorizada`/`serie_lucro_normalizada`, `normalizacao.py:94+`, `fundamentals.py:145`) e deixar a série do CAGR/`g_historico` **crua até a Fase 11**. A Fase 10 tira o viés que ressuscita ano de prejuízo (os `g` fabricados de 36% no VULC3 e 47% no CYRE3 **somem** — critério do ROADMAP); a Fase 11 é quem desenha o `g` robusto. Fronteira limpa entre as fases.

### Claude's Discretion
- O usuário respondeu "recomendado" nos 4 pontos; a última área (winsor) tinha "Você decide" como opção, mas ele escolheu explicitamente "remover e deixar cru até a Fase 11". Detalhes de implementação (biblioteca do Theil-Sen — provavelmente `scipy.stats.theilslopes`, respeitando o constraint de custo zero / dependências já presentes; forma exata do fallback de série curta) ficam a critério do planner/researcher, dentro das decisões acima.

### Restrições travadas pelo ROADMAP (herdadas, NÃO re-perguntadas)
- **NÃO atualizar o golden do ITUB4 32,88** — DELETAR. É a Armadilha 3 ("atualizar mantém o reflexo vivo"). Uma justificativa legítima de knob nunca menciona um ticker (compare `config.yaml:237` "Move ITUB4 ~R$2" — anti-exemplo).
- **NÃO mexer** em `g_cap`, `Ke`, `ke_teto`, `ke_piso`, ERP, beta nem motor. As primitivas mudam sozinhas; se o `V` ficar exagerado, é esperado (Fases 11/12).
- **NÃO compensar** o novo nível de lucro com nenhum knob ("subiu demais, vou abaixar X") — é o post-mortem do v2.3 se repetindo.
- **Orçamento de 3 knobs** (`ERP`, `n_fade`, `PIB_real` em `calibracao.lock.yaml`) intocado: mexer em qualquer knob de valuation exige o lock no mesmo diff. O researcher deve confirmar se a mudança de método remove `anos_media`/`winsor` como knobs (viram método fixo, não grau de liberdade) sem adicionar um 4º grau.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e critérios da fase
- `.planning/ROADMAP.md` §"Phase 10: Primitivas sem viés (PRIM)" — goal, 5 success criteria (inclui o critério de saída do golden 32,88) e as regras "NÃO fazer".
- `.planning/REQUIREMENTS.md` PRIM-01..05 — rastreabilidade e números-alvo.
- `CLAUDE.md` §"O que significa suíte verde" — regra do v2.4: golden que quebra é DELETADO não atualizado; orçamento de 3 knobs no `calibracao.lock.yaml`; classificação obrigatória em `tests/classificacao.yaml`; justificativa de knob nunca menciona ticker.

### Código-alvo (o que muda)
- `src/analista/core/normalizacao.py` §`base_normalizada` (58-75, o `median()`-de-3) e §`serie_winsorizada` (94+, a winsorização temporal).
- `src/analista/core/fundamentals.py` §`base_lucro_normalizada`/`serie_lucro_normalizada`/`roe_valuation` (140-159, os consumidores canônicos) e §`roe(ano)` (125, a definição por-ano a reusar).
- `src/analista/core/` motor cíclico + `src/analista/ingest/macro.py` (fonte BCB/IPCA para a deflação — o researcher confirma o ponto exato de integração).

### Critério de saída (onde vive o golden a deletar)
- `tests/helpers_blindagem.py:157,215` — `ALVOS = {"ITUB4": 32.88}` (BLIND).
- `tests/test_backtest_bancos.py:121` — `alvos = {"ITUB4": 32.88, ...}`. **Nuance a resolver no planejamento:** este arquivo rotula o 32,88 como "INALTERADO — o cap satura, não regride" (ligado ao `ke_teto`, Fase 12). O planner precisa distinguir qual golden é o alvo do critério de saída do PRIM-05 vs. o que só vira verde na Fase 12.

### Contexto de raciocínio (memórias do projeto, não versionadas no repo)
- `duas-doencas-do-valuation` — "3 correções óbvias PIORAM o modelo; ordem obrigatória de conserto" (por que Theil-Sen precisa de validação contra os 104).
- `rim-terminal-value-root-cause` — o golden ITUB4 32,88 pós-v2.3 e por que ele existe.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `mediana_payout` (`normalizacao.py:78-91`): já é o padrão "mediana sobre a série completa, sem janela de 3a, sem clamp" — o `roe_valuation` (D-02) deve espelhá-lo.
- `roe(ano)` (`fundamentals.py:125`): a definição por-ano (lucro_t ÷ PL médio t-1/t) a ser reusada dentro da mediana de ROEs — evita inventar uma segunda semântica de ROE.
- `macro.py`: já puxa séries do BCB — a deflação por IPCA (D-03) reaproveita essa infraestrutura, sem nova fonte de dados (respeita custo zero).

### Established Patterns
- **Número-síntese canônico chamado sem args** em todas as superfícies (Analisar + Ranking app + Ranking cli) → consistência entre menus por construção. As mudanças de D-01/D-02 devem preservar essa fronteira (assinaturas `roe_valuation()`/`lpa_valuation()` estáveis).
- **Fronteira crú×valuation:** `roe(ano)`/`lpa(ano)`/`lucro_liquido` CRUS continuam alimentando a tabela por-ano e o screening (semântica de elegibilidade). Só a base de VALUATION muda.

### Integration Points
- `base_normalizada` é o ponto único que alimenta `roe_valuation`/`lpa_valuation` → mudar o estimador ali propaga para todos os motores e telas (a "maior alavancagem por linha" do goal).
- A suíte de blindagem (`helpers_blindagem.py`, BLIND-03 `xfail` que vira verde nesta fase) é o oráculo do critério de saída.
</code_context>

<specifics>
## Specific Ideas

- Estimador de tendência: **Theil-Sen** especificamente (regressão robusta), não OLS — a robustez a 1 outlier é o requisito.
- ROE e payout devem compartilhar a mesma filosofia de agregação (mediana da série completa), por consistência entre primitivas.
- Deflação expressa em **reais do último ano** ("de hoje"), não em ano-base fixo, para números absolutos intuitivos.
</specifics>

<deferred>
## Deferred Ideas

- **Deflação da base do CAGR/`g`** — mencionado como opção mais abrangente, mas reservado à **Fase 11** (GROW) para não misturar a medição das primitivas com a do `g`.
- **Desenho do `g` robusto** (ex.: slope de regressão em log no lugar da winsorização) — explicitamente **Fase 11**; a Fase 10 apenas remove o viés da winsorização e deixa a série crua.
- **Conserto do `Ke`/`ke_teto`** — **Fase 12**, depois do `g` (regra dura A: consertar o Ke antes do g piora o modelo).

### Reviewed Todos (not folded)
None — não havia todos casando com a Fase 10.
</deferred>

---

*Phase: 10-primitivas-sem-vi-s-prim*
*Context gathered: 2026-07-15*
