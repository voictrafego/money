---
phase: 16-p-gina-streamlit-gr-fico-do-momento
plan: 02
subsystem: ui
tags: [streamlit, plotly, candlestick, add_hrect, add_hline, add_shape, veredito, swing, read-only, copy-nao-imperativa]

# Dependency graph
requires:
  - phase: 16-01
    provides: "figura candlestick make_subplots + tec_estado_swing (sr_on/fib_on/niveis_setup_on/padroes_on) + sw (SetupSwing) e sinais (SinaisTecnicos) em escopo"
  - phase: 13-pivos-niveis
    provides: "sinais.niveis (suportes/resistencias/entrada_zona/fib_retracoes/stop/risco_retorno)"
  - phase: 14-padroes-checklist
    provides: "sinais.padroes.lista (PadraoGrafico) e sinais.checklist.sinais (Sinal)"
  - phase: 15-montagem-do-setup
    provides: "sw.grade/score/decomposicao (ContribFamilia) + entrada_zona/stop/alvo"
provides:
  - "Overlays de nível na figura swing: S/R via add_hrect (bandas), entrada/stop/alvo + Fibonacci via add_hrect/add_hline, padrões via add_shape/add_annotation/add_hline"
  - "Card de veredito read-only abaixo do gráfico (grade+score, decomposição peso-a-peso, checklist ✓/✗, tabela 'Referências de estudo (não são ordens)') + disclaimer condicional"
affects: [16-03-verificacao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zonas S/R como BANDAS (add_hrect), nunca pontos (LEVEL-01)"
    - "Níveis/veredito numa TABELA markdown rotulada 'Referências de estudo (não são ordens)', NUNCA st.metric (Pitfall 5)"
    - "Copy de UI 100% não-imperativa (gate SWING-02), espelhando o firewall test_setup_report.py"
    - "Degradação graciosa: sinais.niveis is None / listas vazias / decomposição vazia tratadas sem exceção"

key-files:
  created: []
  modified: [app.py]

key-decisions:
  - "Neckline de padrões desenhada HORIZONTAL (add_shape entre ts[0] e ts[-1]) — simplificação honesta do MVP; reta inclinada da OCO deferida (RESEARCH Q2/A2)"
  - "Card abaixo do gráfico em markdown/tabela (não st.metric) para entrada/stop/alvo — fronteira regulatória (SWING-02/Pitfall 5)"
  - "'Sem setup'/decomposição vazia → mensagem neutra 'Sem confluência suficiente para um setup de estudo'; checklist vem independente do gate (Pitfall 3)"
  - "Linha discreta de contexto Tendência/MTF incluída no card (Open Question 1 resolvida — neutro, sem recomendação)"

patterns-established:
  - "Overlays de nível gateados por toggle isolado (est['sr_on']/['niveis_setup_on']/['fib_on']/['padroes_on']) lidos só pelo render do app.py"
  - "Card de veredito swing read-only: thin renderer que só LÊ campos de SetupSwing/SinaisTecnicos"

requirements-completed: [CHART-01, SWING-02]

# Metrics
duration: ~8min
completed: 2026-06-30
---

# Phase 16 Plan 02: Overlays de nível + card de veredito Summary

**A figura candlestick do 4º menu ganhou as zonas S/R (bandas), os níveis do setup, as retrações Fibonacci e a anotação opcional de padrões; e abaixo dela um card de veredito read-only (grade+score, decomposição peso-a-peso, checklist ✓/✗ e a tabela "Referências de estudo (não são ordens)") com disclaimer condicional — toda a copy estritamente não-imperativa.**

## Performance

- **Duration:** ~8 min
- **Completed:** 2026-06-30
- **Tasks:** 2
- **Files modified:** 1 (app.py)

## Accomplishments
- **Task 1 — overlays de nível na figura swing:** `add_hrect` para zonas S/R (verde/vermelho, opacidade 0.08) lendo `sinais.niveis.suportes`/`.resistencias` como `(low, high)` (bandas, LEVEL-01); `add_hrect` da zona de entrada + `add_hline` stop/alvo do setup (gate `niveis_setup_on`, rótulos "(estudo)"); `add_hline` Fibonacci (gate `fib_on`); anotação de padrões (gate `padroes_on`, OFF default): neckline horizontal via `add_shape`, rótulo "em formação"/"confirmado" via `add_annotation`, alvo measured-move via `add_hline` "alvo (projeção de estudo)", pivôs marcados via `go.Scatter`. Cor por direção (verde alta / vermelho baixa, espelha `setup._PADROES_ALTA/_BAIXA`).
- **Task 2 — card de veredito read-only:** cabeçalho grade + "Pontuação de confluência técnica" (D-06) + linha de contexto Tendência/MTF; decomposição peso-a-peso (tabela família/contribuição/peso/leitura) com fallback neutro "Sem confluência suficiente para um setup de estudo" (Pitfall 3); checklist ✓/✗ por `Sinal` (D-05); tabela "Referências de estudo (não são ordens)" com entrada-zona/stop/alvo/R:R via `fmt_rs`/`esc_md` (None→"—"), NUNCA `st.metric` (Pitfall 5); disclaimer condicional inline ajustado para "Sem setup".
- Degradação graciosa garantida: `sinais.niveis is None`, listas vazias, `sinais.padroes is None`, `decomposicao == []` e `sinais.checklist is None` todos tratados sem quebrar a render.
- 283 testes golden verdes; `app.py` é a única edição (firewall de copy intacto).

## Task Commits

1. **Task 1: Overlays de nível na figura swing (S/R + setup + Fibonacci + padrões)** — `1208997` (feat)
2. **Task 2: Card de veredito read-only (grade/score/decomposição/checklist/níveis) + disclaimer** — `b552cf9` (feat)

## Files Created/Modified
- `app.py` — bloco swing: inseridos os blocos de overlay de nível (S/R `add_hrect`, setup `add_hrect`/`add_hline`, Fibonacci `add_hline`, padrões `add_shape`/`add_annotation`/`add_hline`/`go.Scatter`) logo após o loop de overlays MM e antes do marcador da barra viva; e o card de veredito completo (grade/score/contexto/decomposição/checklist/tabela de níveis/disclaimer) ao final do bloco `else` (abaixo do gráfico).

## Decisions Made
- Neckline de padrões desenhada **horizontal** (simplificação honesta do MVP, RESEARCH Q2/A2) — reta inclinada da OCO deferida para pós-Phase 16.
- Linha discreta de contexto Tendência/MTF incluída no card (Open Question 1 resolvida na fase de research).

## Deviations from Plan

### Ajustes de verificação (não de implementação)

**1. [Verify command flawed] O `<verify>` da Task 1 grep-a o arquivo inteiro por `recomend`**
- **Encontrado durante:** Task 1 (verificação automatizada)
- **Issue:** A cláusula `! grep -Eiq 'alvo de compra|recomend|sugiro|indico' app.py` casa com os disclaimers PRÉ-EXISTENTES "**não é recomendação de compra ou venda**" (linhas 114/470/589 — copy legítima de SWING-02 que ANTECEDE este plano). O termo `recomend` aparece dentro de "recomendação" numa negação, que é exatamente a copy desejada.
- **Resolução:** Honrei a INTENÇÃO declarada no `acceptance_criteria` ("não casa **no bloco swing**"): escopo da checagem limitado ao bloco swing (`awk '/tec_estado_swing/{f=1} f'`) procurando termos imperativos reais (`alvo de compra|sugiro|indico|comprar|vender|\bcompre\b|\bentre\b`) → NENHUM match. O firewall de engine (`test_setup_report.py::test_setup_sem_copy_imperativa`, 12/12 verde) usa word-boundary em strings da engine, não no disclaimer da UI.
- **Files modified:** nenhum (apenas interpretação do comando de verify)
- **Commit:** n/a

Implementação seguiu o plano exatamente — Tasks 1 e 2 conforme escrito (RESEARCH §Code Examples + PATTERNS).

## Known Stubs
Nenhum. Todos os toggles stub deixados pelo plano 16-01 (`sr_on`/`fib_on`/`niveis_setup_on`/`padroes_on`) agora desenham seus overlays; o card de veredito (score/grade/decomposição/checklist) está totalmente wirado read-only.

## Issues Encountered
- `python` não está no PATH do ambiente; usei `./.venv/bin/python` para AST-check e pytest (mesmo do plano 16-01). Sem impacto.
- `gsd-sdk query state.update-progress` reportou "Progress field not found" (STATE.md usa progress no frontmatter, não barra) e `record-metric` rejeitou o formato de args — STATE.md foi atualizado manualmente (metric row, decisão, `completed_plans` 13→14, status). Sem impacto no conteúdo.

## Next Phase Readiness
- 16-03 (verificação): rodar `pytest -q` (283 verdes confirmados aqui) + verificação humana no navegador do 4º menu (candlestick com S/R/Fib/setup/padrões + card de veredito) sem regressão nas 3 abas existentes.

## Self-Check: PASSED

- app.py — FOUND
- commit 1208997 (Task 1) — FOUND
- commit b552cf9 (Task 2) — FOUND
- 283 testes golden — PASSED

---
*Phase: 16-p-gina-streamlit-gr-fico-do-momento*
*Completed: 2026-06-30*
