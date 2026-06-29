# Phase 13: Pivôs, Contexto de Tendência e Níveis - Context

**Gathered:** 2026-06-29
**Status:** Ready for planning

<domain>
## Phase Boundary

A **engine** (server-side, sem UI) deriva, a partir de pivôs determinísticos e **sem lookahead**:
1. **Pivôs** (swing highs/lows) no-repaint — base de tudo (PIVOT-01).
2. **Contexto de tendência** no diário (sequência de Dow + MMs/ADX já existentes) e **alinhamento semanal→diário** (TREND-01, TREND-02).
3. **Níveis geométricos**: S/R em zonas (LEVEL-01), zona de entrada por pullback/Fibonacci (LEVEL-02), stop técnico (LEVEL-03), alvo/projeção Fibonacci (LEVEL-04).
4. **R:R** como razão, degrada para "indisponível" (RR-01).
5. Família **Volume** (MM de volume + flag rompimento c/ volume) aditiva ao contrato `SinaisTecnicos` (VOL-01).

**Tudo é aditivo ao contrato `SinaisTecnicos`.** A renderização (gráfico, overlays, copy) é a **Fase 16** — não pertence a esta fase.

**Out of scope (fases próprias):** padrões gráficos / checklist de sinais (Fase 14); trendlines automáticas desenhadas; OBV / volume relativo avançado; toda renderização.
</domain>

<decisions>
## Implementation Decisions

### Detecção de pivôs (PIVOT-01)
- **D-01:** Método = **fractal de Williams** — um pivô-topo em `t` é a barra cujo High é estritamente maior que o das `N` barras fechadas de cada lado (idem fundo para Low). No-repaint é **trivial e determinístico**: o pivô em `t` só é confirmado quando `t+N` fecha, e nunca muda depois. **NÃO** usar `scipy.signal.find_peaks`/prominence (a prominence depende da janela e pode repaint na borda — conflita com a invariante).
- **D-02:** `N` é parâmetro em `config.yaml` (default **2** para swing no diário). **Defaults derivados do método agora** — NÃO rodar `/gsd-research-phase`. Calibração empírica de `N` em ações B3 fica deferida (params em config → ajuste barato depois), sem bloquear a fase.
- **D-03:** Lag de confirmação aceito: os `N` candidatos mais recentes ficam "não confirmados" até fecharem barras suficientes à direita — coerente com o cálculo sempre sobre a barra fechada (`iloc[-2]`, herdado D-04 da Fase 12). Teste de estabilidade no-repaint (série truncada em `t` == em `t+1` para barras fechadas) é **gate obrigatório**.

### Contexto de tendência e multi-TF (TREND-01, TREND-02)
- **D-04:** O **semanal** é derivado por **resample W-FRI do diário** (`ohlc_ajustado`) — sem nova chamada de rede e sem ampliar o contrato da Fase 12. 5y de diário ≈ 260 barras semanais (suficiente). **NÃO** buscar timeframe `1wk` separado do Yahoo.
- **D-05:** Rótulo de Dow = **sequência HH/HL → alta, LH/LL → baixa**, com **desempate por inclinação de MM/ADX já existentes** quando a sequência for ambígua → **lateral**. Reusa `adx_wilder` e as SMAs/EMAs de `indicators.py` (não reimplementar).
- **D-06:** Alinhamento semanal→diário rotula `alinhado_alta` / `alinhado_baixa` / `conflito`. **Conflito penaliza (modula) o score, nunca bloqueia** o setup (TREND-02).

### Níveis geométricos: âncora, stop e R:R (LEVEL-02/03/04, RR-01)
- **D-07:** Fibonacci (retração de entrada 38,2/50/61,8% e extensão de alvo 161,8%) é ancorado no **último impulso confirmado** — o par de pivôs mais recente (fundo→topo na tendência de alta; topo→fundo na de baixa). Os dois pivôs âncora são **documentados** no contrato (para auditabilidade).
- **D-08:** Stop técnico = o **mais conservador (mais distante)** entre o **swing estrutural** (swing-low/high) e **ATR×m**. Respeita estrutura sem ficar apertado demais. `m` em `config.yaml` (default **1,5**). ATR é exposto a partir do **TR já calculado na cadeia do ADX** (não recalcular).
- **D-09:** R:R = razão formatada (ex.: "1 : 2,5") de entrada/stop/alvo; quando o risco for **zero ou indefinido**, degrada para **"indisponível"** (nunca infinito/divisão por zero).

### Zonas de Suporte/Resistência (LEVEL-01)
- **D-10:** S/R = **faixas/zonas, nunca pontos exatos**. Clustering de pivôs por **proximidade < k×ATR** (largura adapta à volatilidade de cada ticker — mais robusto entre papéis B3 distintos que um % fixo). `k` em `config.yaml`. **Donchian** (já existe em `SinaisTecnicos`: `donchian_sup/inf` 20 e 55) entra como faixa externa de referência.

### Volume (VOL-01)
- **D-11:** Família Volume = MM de volume (janela em config) + flag booleana "rompimento com volume acima da média". **Aditiva** ao `SinaisTecnicos` — nenhum campo existente muda, 191 goldens seguem verdes; novos goldens cobrem a família.

### Claude's Discretion
- Nomes exatos de campos/dataclasses, organização interna dos módulos, e a forma precisa dos novos campos em `SinaisTecnicos` (desde que aditivos).
- Valores default finos dos params em `config.yaml` (k, janela de volume, janela Donchian para S/R) — partir de defaults sensatos do método, todos em config.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e roadmap
- `.planning/ROADMAP.md` § "Phase 13: Pivôs, Contexto de Tendência e Níveis" — goal, success criteria, dependência da Fase 12.
- `.planning/REQUIREMENTS.md` — PIVOT-01, TREND-01/02, LEVEL-01/02/03/04, RR-01, VOL-01 (textos normativos).

### Contratos e código a reusar (NÃO reimplementar)
- `src/analista/core/indicators.py` — contrato `SinaisTecnicos` (linha ~84); `adx_wilder` (~258, expõe TR p/ ATR); SMA/EMA 20/50/200 (~115); Donchian 20/55 causal `.shift(1)` (~183-200); ponto de entrada único `calcular(ohlc, cfg)` (~406). A nova matemática estende este módulo/contrato.
- `src/analista/ingest/intraday.py` — `coletar_intraday(ticker, timeframe) -> FrameOHLC` (engine da Fase 12 que esta fase consome).

### Decisões herdadas (invariantes)
- `.planning/phases/12-ingest-o-intraday-timeframe/12-CONTEXT.md` — D-02 (níveis sobre `ohlc` nominal, indicadores sobre `ohlc_ajustado`), D-03/D-04 (cálculo sempre sobre a barra fechada `iloc[-2]`, no-repaint).
- `.planning/STATE.md` § Blockers — invariante dos 191 goldens, no-repaint causal obrigatório, "exibe, nunca recomenda" (copy é gate das Fases 15/16, não aqui).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SinaisTecnicos` (indicators.py): contrato a estender de forma **aditiva** (Volume + pivôs/tendência/níveis). Donchian 20/55 já presente → base direta para S/R (LEVEL-01).
- `adx_wilder(ohlc, length=14)`: já calcula TR (true range) → **ATR derivado daqui** para stop ATR×m (D-08), sem recalcular.
- SMA/EMA 20/50/200 + ADX: desempate do rótulo de Dow (D-05) e força de tendência.
- `calcular(ohlc, cfg)`: ponto de entrada único, padrão de config-driven (`cfg["indicadores"][...]`) — novos params seguem o mesmo idioma.

### Established Patterns
- **Causalidade explícita**: Donchian usa `.shift(1)`; toda série nova de pivôs/níveis deve ser causal (no-repaint) e testável em golden.
- **Degradação graciosa**: indicadores inviáveis (ex.: frame curto) caem para "indisponível" sem exceção — R:R e níveis seguem o mesmo contrato (D-09).
- **Config-driven**: janelas/limiares vêm de `config.yaml`; pivôs (N), ATR (m), cluster (k), Donchian S/R e janela de volume entram lá.

### Integration Points
- Entrada: `FrameOHLC.ohlc_ajustado` (cálculos) e `.ohlc` nominal (níveis de preço — D-02).
- Saída: campos novos no `SinaisTecnicos`, consumidos pela Fase 16 (renderização) e Fase 14 (padrões).
</code_context>

<specifics>
## Specific Ideas

- Método de referência: *O Investidor em Ações de Dividendos* (Orleans Martins & Felipe Pontes) para a leitura técnica de swing; Fibonacci clássico (38,2/50/61,8 retração; 161,8 extensão).
- Pivôs por **fractal de Williams** (escolha explícita do usuário sobre find_peaks) pela garantia de no-repaint.
- Stop "mais conservador entre swing e ATR×m" — preferência explícita por respeitar estrutura sem aperto excessivo.
</specifics>

<deferred>
## Deferred Ideas

- **Calibração empírica de `N` (pivôs) / `k` (cluster) em ações B3** via `/gsd-research-phase` — adiado; defaults do método agora, params em config para ajuste barato depois.
- **Buscar timeframe `1wk` direto do Yahoo** — preterido em favor de resample W-FRI; reconsiderar só se o resample se mostrar insuficiente.
- **Trendlines automáticas desenhadas, OBV / volume relativo avançado** — fora de escopo (futuras fases / Fase 16+).

None — discussão permaneceu dentro do escopo da fase.
</deferred>

---

*Phase: 13-piv-s-contexto-de-tend-ncia-e-n-veis*
*Context gathered: 2026-06-29*
