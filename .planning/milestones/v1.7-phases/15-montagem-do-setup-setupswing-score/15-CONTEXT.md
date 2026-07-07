# Phase 15: Montagem do Setup (SetupSwing) + Score - Context

**Gathered:** 2026-06-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega um dataclass read-only **`SetupSwing`** (em `report/setup.py`) que **integra** os componentes puros já golden-testados das Fases 13–14 — contexto de tendência, níveis geométricos, sinais/checklist e padrões gráficos — num **score ponderado e explicável**, com **R:R como gate**, numa grade qualitativa e em **linguagem de estudo que exibe e nunca recomenda** (SCORE-01).

**No escopo:** montagem do `SetupSwing` como firewall (nunca importa `report/report.py`), score ponderado com decomposição peso-a-peso visível, grade qualitativa, R:R como gate, pesos/limiares parametrizados no `config.yaml`, guards de borda, copy condicional/de estudo, e `test_setup_report.py`.

**Fora do escopo:** renderização/gráfico/página Streamlit (Fase 16), novos indicadores ou padrões (Fases 13–14 já entregaram), qualquer recomendação de compra/venda (proibido por design — D-01/SWING-02).
</domain>

<decisions>
## Implementation Decisions

### Pesos do score
- **D-01:** Esquema inicial "tendência domina forte" — **Tendência 35% / R:R 20% / Padrões 20% / Momentum (RSI-MACD) 15% / Volume 10%**. Alinhado ao Murphy (operar a favor da tendência). Todos os pesos vivem no `config.yaml` (sem hardcode na montagem) e são calibráveis.
- **D-02:** A decomposição do score é **visível peso a peso** (cada família mostra sua contribuição) — explicabilidade é requisito, não opcional. O score final é normalizado (faixa a definir no research, ex.: 0–100).

### R:R como gate
- **D-03:** R:R atua como **gate duro**: abaixo do R:R mínimo aceitável, o setup é **zerado** → cai para a grade "Sem setup", independentemente de quão bons sejam os outros sinais. Mais conservador, coerente com "exibe sinais, nunca recomenda".
- **D-04:** R:R mínimo sugerido **≈1.5** — valor exato parametrizado no `config.yaml`, calibrável. O guard de R:R usa `np.errstate` (sem divisão por zero) e exige stop/alvo coerentes (idioma já estabelecido na Fase 13 / LEVEL-03).

### Grade qualitativa
- **D-05:** **4 faixas em PT-BR: Forte / Moderado / Fraco / Sem setup.** Legível pro investidor PF, tom de estudo. "Sem setup" é também o resultado do gate de R:R (D-03). Os cortes de score entre faixas vivem no `config.yaml` e são calibráveis.

### Copy / enquadramento (gate de aceite)
- **D-06:** O score é nomeado **"Pontuação de confluência técnica"** — descreve factualmente quantos sinais técnicos se alinham, neutro, sem soar convite. Linguagem condicional/de estudo em todo o veredito; entrada/stop/alvo sempre como referências de estudo, jamais ordens. **Copy review é gate de aceite** (firewall de copy, herda D-01 da Fase 14).
- **D-07:** **Conflito multi-timeframe** (semanal × diário) **penaliza o score sem bloquear** o setup (Critério 2). Magnitude da penalização parametrizada no `config.yaml`.

### Claude's Discretion
- Normalização exata do score (escala 0–100 vs 0–1) e os cortes numéricos das 4 faixas → ancorar no research, sempre no `config.yaml`.
- Valor exato do R:R mínimo (em torno de 1.5) e do piso crítico, e a magnitude da penalização multi-TF → research ancora valores iniciais sensatos, calibráveis.
- Estrutura interna do dataclass `SetupSwing` (campos, sub-objetos da decomposição) → planner/research, respeitando read-only e degradação graciosa.
- Eventual gate de liquidez (volume mínimo) como pré-condição do setup → research avalia se cabe no MVP.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Escopo e requisito da fase
- `.planning/ROADMAP.md` §"Phase 15: Montagem do Setup (SetupSwing) + Score" — Goal + 5 Success Criteria (firewall, score explicável, config-driven, guards de borda, goldens).
- `.planning/REQUIREMENTS.md` §SCORE-01 — score ponderado explicável + grade qualitativa + R:R como gate/modulador + pesos no `config.yaml`.

### Contratos consumidos (Fases 13–14, já golden-testados)
- `src/analista/core/indicators.py` — `indicators.calcular()` retorna `SinaisTecnicos` (tendência/Dow/multi-TF, níveis S/R/Fibonacci/stop/R:R, momentum RSI/MACD/ADX, volume, **pivôs**, **padrões** `Padroes.lista`, **checklist** 6 sinais liga/desliga). É a fonte de TODOS os insumos do score.
- `config.yaml` §`padroes:` e §`indicadores:` — molde para o novo bloco de pesos/limiares do score (mesmo padrão config-driven).

### Firewall (NUNCA importar)
- `src/analista/report/report.py` — engine fundamentalista (25KB). `report/setup.py` **não pode importá-lo** sob nenhuma circunstância (Critério 1). Mantém a engine de swing isolada da fundamentalista.
- `src/analista/report/presentation.py` — verificar padrão de apresentação read-only existente (analog de como expor campos sem recalcular).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `indicators.calcular()` → `SinaisTecnicos`: já agrega tendência, níveis, R:R, momentum, volume, padrões e checklist. O `SetupSwing` é um consumidor read-only desse contrato — zero recálculo de método.
- `config.yaml` blocos `padroes:`/`indicadores:`: molde direto para um novo bloco `setup:`/`score:` com pesos, R:R mínimo, cortes de grade e penalização multi-TF.
- Idioma `np.errstate` + guards de borda (Fase 13, `_niveis_stop_rr`): reusar para o R:R do score sem divisão por zero.

### Established Patterns
- Aditividade e degradação graciosa: o `SetupSwing` deve degradar sem levantar exceção para a UI (Critério 1) — retorno neutro/"Sem setup" em vez de erro.
- Firewall de copy (D-01, Fase 14, `test_checklist_sem_copy_natural`): replicar o teste anti-copy imperativo para o veredito do setup.

### Integration Points
- `report/setup.py` (novo): consome `indicators.calcular()` (+ eventuais helpers de `setups.*`/`core`), monta `SetupSwing`. É consumido pela Fase 16 (página) como thin renderer.
</code_context>

<specifics>
## Specific Ideas

- O usuário enfatizou (Fase 16, mas vale como princípio) que o gráfico precisa ter médias, Bollinger e as análises — o `SetupSwing` deve expor a decomposição de forma que a página consiga mostrar *por que* o score é o que é (rastreabilidade peso-a-peso), não só o número.
- Tom "software educacional / exibe, nunca recomenda" é inegociável — herança direta do posicionamento do produto e pré-condição da v2.0 comercial.
</specifics>

<deferred>
## Deferred Ideas

- Renderização do score/decomposição na tela, gráfico candlestick com overlays (médias, Bollinger, padrões anotados), subpainéis RSI/MACD/ADX → **Fase 16** (CHART-01/SWING-01/02).
- Padrões de continuação (triângulos, bandeiras, retângulos) como insumo extra do score → backlog (diferidos por risco de falso positivo).
- Ranqueamento/seleção entre múltiplos padrões simultâneos além do peso no score → se necessário, refinar quando a Fase 16 expuser na UI.
</deferred>

---

*Phase: 15-montagem-do-setup-setupswing-score*
*Context gathered: 2026-06-29 via /gsd-discuss-phase*
