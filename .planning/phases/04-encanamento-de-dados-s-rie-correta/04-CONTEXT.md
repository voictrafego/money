# Phase 4: Encanamento de dados + série correta - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Preservar o frame OHLCV que o Yahoo **já baixa** em `coletar_mercado` (`tk.history(period="5y", auto_adjust=False)`) e conduzi-lo até a engine — `DadosMercado.ohlc` → `CompanyData.ohlc` — espelhando exatamente o padrão `serie_precos` da v1.1. Além do frame nominal, a fase **prepara uma série ajustada por splits** pronta para os cálculos de indicador da Phase 5.

**Sem novo comportamento visível, sem nova chamada de rede, sem qualquer fórmula de valuation alterada.** É puro encanamento de dados + uma série derivada.

**Fora de escopo (outras fases):** cálculo de indicadores (Phase 5), integração na engine/composite/alerta (Phase 6), UI/overlays (Phase 7).

</domain>

<decisions>
## Implementation Decisions

### Conteúdo e forma do campo `ohlc` (DATA-01)
- **D-01:** O campo `ohlc` guarda o **frame OHLCV nominal completo**, preservando o `hist` como veio do Yahoo — colunas `Open / High / Low / Close / Adj Close / Volume / Stock Splits` (mais `Dividends`). Risco zero: o objeto já está em memória; nada é descartado. (Escolha "Bruto + ajustada, no ingest"; rejeitado "frame enxuto" só com High/Low/Close/Volume.)
- **D-02:** O encanamento espelha 1:1 o padrão `serie_precos`: campo novo em `DadosMercado` (`ingest/prices.py`), copiado para `CompanyData` em `ingest/build.py` (`c.ohlc = dm.ohlc`). `serie_precos` (Close nominal p/ o gráfico) **permanece inalterado** — coexiste com `ohlc`.

### Série split-adjusted — origem e localização (DATA-02, CR-01)
- **D-03:** A série/frame **ajustada por splits** é derivada **já no ingest (Phase 4)**, como função pura, a partir da coluna `Stock Splits` que **já vem dentro do `hist`** — fator de split **cumulativo** aplicado ao OHLC nominal. **Não é dividend-adjusted** (não usar `Adj Close`, que mistura proventos). Fica disponível ao lado do frame nominal (nominal p/ o eixo do gráfico — CR-01; split-adjusted p/ os indicadores — DATA-02).
- **D-04:** **DATA-01 satisfeito sem tensão:** verificado em runtime que `tk.history(period="5y", auto_adjust=False)` já retorna a coluna `Stock Splits` no mesmo frame — **nenhuma chamada extra** (`tk.splits`, refetch) é necessária para reconstruir o ajuste.
- **D-05:** O fator de split aplica-se uniformemente a `Open/High/Low/Close` (multiplicativo) e o `Volume` ajusta-se no sentido inverso; após o último evento de split o fator = 1, então a ponta recente da série ajustada coincide com a nominal.

### Degradação graciosa (DATA-03)
- **D-06:** Quando `hist` vem vazio/`None` ou o histórico é curto, o encanamento degrada para `ohlc=None` (e a série ajustada `None`), **sem quebrar nada** — espelhando o padrão GRAF-03/D-05 já existente em `app.py` (aviso neutro "fonte Yahoo instável", fundamentos seguem). Avisos de "histórico mínimo insuficiente" por indicador (ex.: MM200 < 200 pregões) são responsabilidade das fases posteriores; aqui basta o campo ausente não estourar.

### Invariante (TEST-07)
- **D-07:** Os **64 golden tests** de valuation continuam verdes. Como `ohlc`/série ajustada são campos novos e nenhuma fórmula do livro muda, a fase é aditiva — rodar a suíte ao final é a verificação.

### Validação (critério de aceite #2)
- **D-08:** Ticker de validação do ajuste por split = **ITSA4**. Verificado: tem **5 eventos de split/bonificação nos últimos 5 anos** (recorrente; estressa bem o ajuste) e é a ação de dividendos clássica do público do app. Critério: a série split-adjusted **não** deve gerar saltos/cruzamentos espúrios nas datas de split (esses serão exercitados de fato nos golden tests da Phase 5 — TEST-05; aqui é validação pontual).

### Claude's Discretion
- Nomenclatura exata do(s) campo(s) da série ajustada (ex.: `ohlc_ajustado` vs. coluna adicional vs. par de campos) — fica a critério do planner, desde que mantenha nominal e split-adjusted ambos acessíveis e siga o padrão `serie_precos`.
- Assinatura/local exato da função pura de ajuste por split (helper em `prices.py` vs. utilitário) — desde que seja pura e testável.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e roadmap do marco
- `.planning/ROADMAP.md` § "Phase 4: Encanamento de dados + série correta" — goal, depends-on (Phase 3), success criteria.
- `.planning/REQUIREMENTS.md` — DATA-01, DATA-02, DATA-03, TEST-07 (e a nota de que TEST-07 é invariante contínuo das fases 4-7).
- `.planning/STATE.md` § "Accumulated Context / Decisions" — decisões de pesquisa v1.2 (OHLC já em memória; sem nova dep de TA; Wilder; `a.sinais` em `analisar_acao`) e pontos de validação.
- `.planning/PROJECT.md` — Core Value (fidelidade ao livro + consistência) e decisão CR-01 (eixo nominal vs. indicadores split-adjusted).

### Código-blueprint (padrão `serie_precos` da v1.1 — espelhar)
- `src/analista/ingest/prices.py` (linhas ~45-130) — `DadosMercado` dataclass + `coletar_mercado`; aqui mora `hist = tk.history(period="5y", auto_adjust=False)` e o campo `serie_precos`. **`ohlc` nasce aqui.**
- `src/analista/ingest/build.py` (linhas ~22-42) — `montar_empresa`: onde `c.serie_precos = dm.serie_precos`. **Adicionar `c.ohlc = dm.ohlc` aqui.**
- `src/analista/core/fundamentals.py` (linha ~45) — `CompanyData` dataclass; campo `serie_precos`. **Adicionar campo `ohlc` aqui.**
- `app.py` (linhas ~124-139) — padrão GRAF-03/D-05 de degradação graciosa (`serie = c.serie_precos`; aviso sem quebrar). Modelo para `ohlc=None`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Padrão `serie_precos`**: campo `Optional["pd.Series"]` em `DadosMercado` → copiado em `build.montar_empresa` → `CompanyData` → lido read-only em `app.py`. O campo `ohlc` é uma réplica direta desse fluxo (mesma forma, mesma degradação).
- **`hist` já em memória**: `coletar_mercado` já tem o DataFrame OHLCV completo (com `Stock Splits` e `Adj Close`); hoje só extrai `Close`/`Adj Close`. Basta preservá-lo.

### Established Patterns
- **Camada de borda valida; engine não**: o ingest trata fonte instável (try/except, `dropna`, campos `Optional` → `None`). A degradação de `ohlc` segue esse contrato.
- **CR-01 / dupla base de preço**: `auto_adjust=False` → `Close` nominal (gráfico, mesma base da banda DDM vmin/vmax) vs. `Adj Close` (retorno total, usado em beta/desempenho). Indicadores precisam de uma TERCEIRA base: **split-only-adjusted**, que não existe pronta no Yahoo e é reconstruída da coluna `Stock Splits`.

### Integration Points
- `ingest/prices.py::coletar_mercado` — preencher `dm.ohlc` (nominal) + série/frame split-adjusted.
- `ingest/build.py::montar_empresa` — propagar para `CompanyData`.
- `core/fundamentals.py::CompanyData` — novo(s) campo(s).
- Nenhuma alteração em `report.analisar_acao`/`AnaliseAcao` nesta fase (a integração de `a.sinais` é Phase 6).

</code_context>

<specifics>
## Specific Ideas

- **Verificado em runtime (`.venv`):** `yf.Ticker("ITSA4.SA").history(period="5y", auto_adjust=False)` retorna colunas `[Open, High, Low, Close, Adj Close, Volume, Dividends, Stock Splits]` e a coluna `Stock Splits` traz os 5 eventos de ITSA4 (2021-12, 2022-11, 2023-11, 2024-12, 2025-12). TAEE4 retorna 0 eventos → ITSA4 é o ticker de validação correto.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-Encanamento de dados + série correta*
*Context gathered: 2026-06-24*
