# Phase 11: Apresentação, hierarquia e trava multi-ticker - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-27
**Phase:** 11-Apresentação, hierarquia e trava multi-ticker
**Areas discussed:** Header — hierarquia DY, Sinalização do DY inflado, Payout duplo — rótulos/fonte, Trava multi-ticker + golden

---

## Header — hierarquia DY (HIER-01)

### Q1: Como o DY recorrente substitui/convive com o trailing na coluna m3?

| Option | Description | Selected |
|--------|-------------|----------|
| DY rec. vira a métrica, trailing no delta | m3 = recorrente; trailing como st.metric(delta=…) abaixo | ✓ |
| DY rec. na métrica, trailing no tooltip/legenda | recorrente como valor; trailing no help/caption | |
| Duas métricas lado a lado | header de 6 colunas, recorrente + trailing com paridade | |

**User's choice:** DY rec. vira a métrica, trailing no delta.

### Q2: Cor e rótulo do delta (trailing)?

| Option | Description | Selected |
|--------|-------------|----------|
| Delta neutro (cinza) + rótulo 'trailing' | delta_color='off', sem verde/vermelho enganoso | ✓ |
| Delta inverso (vermelho quando trailing > rec.) | delta_color='inverse', trata todo excesso como alerta | |
| Você decide | a critério do planner | |

**User's choice:** Delta neutro (cinza) + rótulo 'trailing'.
**Notes:** Levantado que o trailing costuma ser maior → delta positivo pintaria verde por padrão, conotação enganosa de "bom".

### Q3: Fallback quando dy_recorrente é None?

| Option | Description | Selected |
|--------|-------------|----------|
| Trailing como principal, rotulado | cai para trailing com rótulo "recorrente indisponível" | ✓ |
| Métrica vazia ('—') + nota | mostra '—' e legenda explicando ausência | |
| Você decide | planner segue fronteira de None da engine | |

**User's choice:** Trailing como principal, rotulado.

---

## Sinalização do DY inflado (HIER-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Sem badge novo — hierarquia + alertas bastam | estrutura + alertas existentes da engine comunicam o risco | ✓ |
| Badge só quando divergem muito | chip 'DY inflado' acima de limiar trailing/recorrente | |
| Legenda fixa explicando os dois DYs | caption permanente sob o header | |

**User's choice:** Sem badge novo — hierarquia + alertas bastam.
**Notes:** A engine já emite alertas de armadilha (flag_dy/flag_payout, report.py:155-200) renderizados como avisos amarelos. Evitar redundância/ruído.

---

## Payout duplo — rótulos/fonte (PAY-02)

### Q1: Como rotular a linha do payout sustentável (hoje "média 3a")?

| Option | Description | Selected |
|--------|-------------|----------|
| 'Payout p/ valuation (sustentável)' | mantém vínculo com DDM, troca método obsoleto por conceito | ✓ |
| 'Payout sustentável (mediana histórica)' | explicita a mecânica (mediana série) | |
| Você decide | planner escolhe, desde que não diga "média 3a" | |

**User's choice:** 'Payout p/ valuation (sustentável)'.
**Notes:** Confirmado o fix de fonte: "Payout (último ano)" passa a ler c.payout(ult) cru (hoje lê payout_valuation() via a.multiplos["DP (payout)"], colapsando as duas linhas).

### Q2: Varrer rótulos/comentários obsoletos das Fases 9-10 nesta fase?

| Option | Description | Selected |
|--------|-------------|----------|
| Sim — incluir a varredura de rótulos obsoletos | corrige "g histórico (CAGR lucro)" → log-linear e comentários defasados | ✓ |
| Só o escopo estrito (DYR-02/PAY-02/HIER-01) | mantém enxuto; rótulo do g vira ideia diferida | |

**User's choice:** Sim — incluir a varredura de rótulos obsoletos.

---

## Trava multi-ticker + golden (TEST-08)

### Q1: Forma da trava, dado que a fase é apresentação read-only?

| Option | Description | Selected |
|--------|-------------|----------|
| Teste automatizado de apresentação + checkpoint live | helpers puros travados por golden nos 5 tickers + checkpoint manual | ✓ |
| Só checkpoint manual ao vivo dos 5 tickers | padrão das Fases 9-10, sem teste automatizado | |
| Teste automatizado de propriedade (sem live) | golden offline só, sem checkpoint manual | |

**User's choice:** Teste automatizado de apresentação + checkpoint live.
**Notes:** Engine intocada → golden de valuation seguem verdes sem rebaseline.

### Q2: Onde colocar os helpers puros extraídos do app.py?

| Option | Description | Selected |
|--------|-------------|----------|
| Novo módulo em src/ (ex.: report/presentation.py) | helpers puros importáveis sem Streamlit; app.py vira chamador fino | ✓ |
| Helpers no topo do próprio app.py | from app import …; arrasta efeitos colaterais do app | |
| Você decide | planner escolhe seguindo o padrão de report | |

**User's choice:** Novo módulo em src/ (ex.: report/presentation.py).

---

## Claude's Discretion

- Texto exato dos rótulos/labels e dos tooltips `help` (desde que DY rec. seja %, suma "média 3a", e o g histórico não diga "CAGR").
- Nome/assinatura exatos dos helpers puros e do módulo (`report/presentation.py` é sugestão), desde que puros e importáveis sem Streamlit.

## Deferred Ideas

- DY recorrente earnings-based híbrido (não subestimar quem distribui de reservas, ex.: TAEE11) — metodologia/engine, não apresentação.
- Payout-alvo por setor configurável; sinalização de "ano extraordinário" na tabela por ano — Future (v2+).
