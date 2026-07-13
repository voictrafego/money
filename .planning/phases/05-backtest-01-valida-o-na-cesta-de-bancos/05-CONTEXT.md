# Phase 5: BACKTEST-01 — Validação na cesta de bancos - Context

**Gathered:** 2026-07-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Entregar um **harness de validação reproduzível** (script + teste) que roda o motor RIM
**calibrado na Fase 4** sobre a cesta de bancos **ITUB4, BBAS3, BBSE3, BBDC4** e reporta,
por ticker, o intrínseco do RIM lado a lado com **4 âncoras de realidade**:
(a) Graham + Bazin, (b) preço de mercado, (c) tabela manual de fair values, (d) múltiplos de pares.
O objetivo é **provar que a calibração generaliza** (não é overfit no ITUB4) e explicar — não
esconder — qualquer desvio remanescente.

**Escopo cirúrgico (herdado do v2.3 / Fase 4):** só RIM/bancos. NÃO tocar DCF, normalizado, DDM,
selo, lentes. Esta fase **valida** a calibração; ela não re-calibra o motor (isso é o loop com a
Fase 4 se a validação reprovar — ver SC#4).

**Fora de escopo (novas capacidades → outras fases):** deploy em produção (Fase 6), expandir para
não-bancos, backtest histórico multi-período, dashboard de backtest no Streamlit.

</domain>

<decisions>
## Implementation Decisions

### Tabela manual de fair values (4ª âncora — VAL-02 "a definir na fase")
- **D-01:** A origem dos valores-alvo é **pesquisa de consenso** — o executor pesquisa
  fair values / preços-alvo de consenso de casas de análise (relatórios públicos, média de
  target prices) para cada ticker e traz uma **proposta para o usuário aprovar ANTES de versionar**.
  (Não é o usuário quem digita os números; não deriva de Graham/Bazin — VAL-02 pede âncora manual
  independente.)
- **D-02:** Cada fair value é uma **faixa (mín–máx)**, não um ponto — reconhece a incerteza do
  consenso e casa com "a maioria cai na banda razoável".
- **D-03:** A tabela é versionada em **arquivo YAML dedicado** — `tests/fixtures/fair_values_bancos.yaml`
  (ou local equivalente em fixtures/data; NÃO no `config.yaml`, que é knobs do motor). Por ticker:
  `min`, `max`, `data`, `fonte/comentário`. Serve como âncora citável e input do teste.

### Reprodutibilidade dos dados
- **D-04:** O harness roda sobre **snapshots congelados**, não ao vivo. Congelar os inputs do RIM
  (VPA, ROE, preço) de cada banco num fixture versionado, com data carimbada. Teste vira
  **determinístico (golden reproduzível)** — não quebra quando o preço oscila nem quando Yahoo/CVM
  cai. "Reproduzível" do VAL-01 exige isso.
- **D-05:** **Data-base = hoje (~2026-07-12), captura única ao vivo.** Rodar `build.montar_empresa`
  ao vivo uma vez agora para os 4 bancos, congelar VPA/ROE/preço com essa data, e **alinhar o
  consenso de fair value (D-01) à mesma janela temporal** para coerência.

### Critério de aceite (o gate do teste)
- **D-06:** A âncora-verdade que o teste automatizado cobra é a **tabela manual de fair values (D-01)**.
  As outras 3 âncoras (Graham+Bazin, preço, múltiplos) entram como **contexto no relatório**, não no
  gate. (Casa com o sintoma diagnosticado "RIM ~40-50% abaixo das âncoras".)
- **D-07:** Banda de PASS = **±15% da faixa FV** — PASS se o RIM cai dentro da faixa ou até 15%
  fora de qualquer borda. Tolera incerteza do consenso + ruído do modelo, mas ainda pega o viés
  crônico. É um **ponto de partida honesto e calibrável**, não uma constante sagrada.
- **D-08:** Quórum = **3 de 4** bancos dentro da banda. O 4º pode ficar fora **se e somente se o
  desvio estiver documentado** (motivo: bad-bank, dado atípico, etc.). **Desvio não-explicado = FAIL.**
  Espelha SC#2 (maioria na banda) + SC#4 (exceção explicada, não escondida).
  - *Nota de implementação para o planner:* o teste pytest trava o **quórum numérico 3/4 ±15%**;
    a "explicação" da exceção é uma **nota humana** no fixture YAML / relatório (o teste não julga
    a validade do texto, só exige que a 4ª esteja anotada). Definir como o teste distingue
    "3 passam + 1 anotada" de "3 passam + 1 silenciosa".

### Formato / entrega do harness
- **D-09:** Entrega = **teste pytest + script standalone** (cobre "script + teste" do VAL-01):
  - `tests/test_backtest_bancos.py` — teste **determinístico** que trava o gate D-06/D-07/D-08
    sobre o snapshot congelado (guarda a regressão).
  - script standalone que roda a cesta e imprime a tabela legível (RIM × 4 âncoras por ticker).
- **D-10:** O script gera **`out/backtest_bancos.md`** (markdown) — consistente com o padrão
  `out/TICKER.md` que o CLI já usa. Colunas por ticker: RIM, Graham+Bazin, preço, faixa FV,
  múltiplos de pares, desvio (RIM vs FV), PASS/FAIL, nota de exceção.
- **D-11:** A âncora de **múltiplos de pares** (P/VP, P/L do setor bancário) é calculada
  **da própria cesta** — medianas de P/VP e P/L dos 4 bancos do snapshot (referência setorial
  interna). Reusa `comparables.py`/`multiples.py`; zero fonte externa; coerente com a data-base.

### Loop de falha (SC#4)
- **D-12:** Se a validação revelar que a calibração da Fase 4 falha para algum banco além da
  exceção permitida, o achado é **registrado** (no relatório + como finding) e **volta para
  ajustar a Fase 4** (loop) — nunca ignorado. Esta fase não silencia desvios.

### Claude's Discretion
- Local exato do fixture de fair values e do snapshot (fixtures/ vs data/) — desde que versionado
  e citável.
- Estrutura interna do snapshot congelado (raw fundamentals no boundary do RIM vs CompanyData
  serializado) — escolher o mínimo que reproduz o intrínseco de forma estável.
- Como o script standalone é invocado (módulo `python -m`, script em scripts/, ou função) — desde
  que reproduza o mesmo resultado do teste.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo, requisitos e diagnóstico da fase
- `.planning/ROADMAP.md` §"Phase 5: BACKTEST-01" — goal, depends-on (Phase 4), 4 success criteria.
- `.planning/REQUIREMENTS.md` — **VAL-01** (harness reproduzível na cesta) e **VAL-02** (4 âncoras +
  tabela manual + critério de aceite "não cronicamente ~40-50% abaixo").
- `.planning/v2.2-MILESTONE-AUDIT.md` — origem do BACKTEST-01 adiado e o diagnóstico da subestimação.

### Calibração da Fase 4 (o que este backtest valida)
- `.planning/phases/04-rim-com-valor-terminal-ke-revisado/04-01-SUMMARY.md` — números verificados do
  RIM calibrado (ITUB4 live R$32,87, golden R$39,23, bad-bank R$15,54), knobs e invariantes.
- `.planning/phases/04-rim-com-valor-terminal-ke-revisado/04-01-PLAN.md` — plano da calibração.
- `.planning/phases/04-rim-com-valor-terminal-ke-revisado/04-RESEARCH.md` — fundamentação teórica do
  valor terminal (perpetuidade de RI / P/B justo) e a análise de sensibilidade do Ke.
- `config.yaml` §`motores.rim` — knobs `excesso_sustentavel`, `g_terminal`, `ke_g_spread_min`,
  `ke_teto=0.13` que o RIM calibrado consome.

### Código a reusar (ver code_context)
- `src/analista/core/motores.py::rim` · `src/analista/report/report.py::analisar_acao`
- `src/analista/ingest/build.py::montar_empresa` · `src/analista/cli.py`
- `src/analista/core/comparables.py` · `src/analista/core/multiples.py`
- `src/analista/core/screening.py` / `src/analista/core/lentes.py` (Graham + Bazin)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`build.montar_empresa(ticker, ano_base, n)`** (`src/analista/ingest/build.py`): monta o
  `CompanyData` a partir de CVM+Yahoo — usar UMA vez ao vivo para capturar o snapshot congelado
  (D-05).
- **`report.analisar_acao(c, cfg)`** (`src/analista/report/report.py:312`): pipeline completo que
  roteia arquétipo→motor e produz o intrínseco do RIM já com os knobs calibrados. É a superfície que
  o harness deve chamar para obter o número que está sendo validado.
- **`comparables.py` / `multiples.py`**: já calculam P/VP e P/L padronizados — base da âncora de
  múltiplos de pares (D-11), computada sobre a própria cesta.
- **`screening.py` / `lentes.py`**: já calculam Graham e Bazin — âncora (a) do relatório.
- **Padrão `out/TICKER.md`** (via `cli.py`): o `out/backtest_bancos.md` (D-10) deve seguir o mesmo
  estilo de saída markdown.

### Established Patterns
- **Golden test determinístico** (ex: `tests/test_motores.py`, `tests/test_vulc3_regressao.py`,
  `test_ddm.py`): inputs fixos → intrínseco esperado com gate numérico duro. O `test_backtest_bancos.py`
  segue esse padrão sobre o snapshot congelado.
- **Knobs config-driven, zero magic constant no corpo do motor** (Fase 4). A banda ±15% e o quórum
  3/4 devem ser parâmetros/constantes nomeadas no harness, não números soltos.
- **Suíte verde é gate de fase** (440 testes na Fase 4). O novo teste soma à suíte sem quebrar
  nada (firewall selo↛report, DDM/TAEE11 intactos).

### Integration Points
- O harness **consome** o RIM calibrado via `analisar_acao` — não reimplementa fórmula. Se a
  calibração mudar (loop D-12), o snapshot é re-rodado, não o teste reescrito.
- Fixture de fair values (D-03) e snapshot (D-04) são novos artefatos versionados; nada no motor
  muda por causa desta fase (a menos que o loop D-12 dispare).

</code_context>

<specifics>
## Specific Ideas

- Cesta fixa e nomeada: **ITUB4, BBAS3, BBSE3, BBDC4** (do ROADMAP/VAL-01).
- Âncora de realidade do ITUB4 já conhecida da Fase 4: Graham R$39,88, preço R$44,30, RIM live
  R$32,87 — o backtest deve reproduzir esse alinhamento e estendê-lo aos outros 3 bancos.
- BBSE3 (BB Seguridade) é seguradora, não banco de balanço clássico — atenção se o arquétipo/roteamento
  a manda para RIM ou outro motor; se divergir, é candidata natural à "exceção documentada" (D-08).

</specifics>

<deferred>
## Deferred Ideas

- **Redeploy do v2.3 na VPS** — é a Fase 6 (OPS-01), depende desta.
- **Expandir o backtest para não-bancos / outros arquétipos** — nova capacidade, fora do escopo
  cirúrgico RIM/bancos; candidato a marco futuro.
- **Backtest histórico multi-período** (validar o RIM contra fair values de vários anos) — fora do
  escopo desta fase (que é snapshot único).

None além dessas — a discussão ficou dentro do escopo da fase.

</deferred>

---

*Phase: 5-BACKTEST-01 — Validação na cesta de bancos*
*Context gathered: 2026-07-12*
