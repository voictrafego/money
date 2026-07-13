---
phase: quick-260713-hoo
plan: 01
subsystem: ui-streamlit
tags: [ux, render, app.py, presentation-only]
requires: [a.intrinseco_motor, a.banda_do_motor, a.motor, a.san01_reetiquetado, a.divergencia_ativa]
provides: [card-intrinseco-lidera-motor, banners-consolidados-em-expander]
affects: [app.py]
tech-stack:
  added: []
  patterns: [st.expander-opcional-para-detalhe-secundario, manchete-metric-lidera-motor-primario]
key-files:
  created: []
  modified: [app.py]
decisions:
  - "Manchete do intrínseco lidera com a.intrinseco_motor (fmt_rs) quando _usa_motor (motor!=ddm E banda_do_motor E não arquetipo_incerto E intrinseco_motor!=None); faixa/DDM rebaixados a caption discreto"
  - "SAN-01 + divergência (ENS-01) consolidados em 1 st.expander opcional fechado; veredito colorido é a única caixa principal"
  - "Nenhuma lógica de cálculo tocada — mudança 100% de render; R$ 32,88 (ITUB4) intacto"
metrics:
  duration: 0h10m
  completed: 2026-07-13
---

# Quick 260713-hoo: Limpar a tela de análise (card intrínseco + banners) Summary

Mudança 100% de apresentação em `app.py`: o card INTRÍNSECO agora lidera com o valor do
motor primário (ITUB4 → "Intrínseco (RIM) R$ 32,88") em vez da faixa "16,13 – 32,88", e os
3 banners repetitivos ("é RIM, o DDM é conservador") colapsam em 1 veredito + 1 expander opcional.

## What Was Built

### Task 1 — Card INTRÍNSECO lidera com o motor primário (commit af24abf)
- Nova condição `_usa_motor` = `motor != "ddm"` E `banda_do_motor` E não `arquetipo_incerto`
  E `intrinseco_motor is not None`.
- Quando `_usa_motor`, `m2.metric` mostra `fmt_rs(a.intrinseco_motor)` (ex.: "R$ 32,88") com o
  rótulo já-honesto `"Intrínseco (RIM)"`. Fora desse caso (DDM primário, banda degradada,
  caso-fronteira) a manchete continua sendo a faixa `vmin – vmax` ou "—", comportamento inalterado.
- A antiga legenda "A faixa combina o motor do arquétipo..." foi substituída por um `st.caption`
  discreto exibido só quando `_usa_motor` e `contraponto_valor is not None`:
  "Faixa com o DDM como contraponto conservador: {vmin} – {vmax} · DDM {contraponto}."

### Task 2 — Consolidação dos banners em veredito + 1 expander (commit 9897bd9)
- SAN-01 (`st.info`) e a bandeira de divergência ENS-01 (`st.warning`) migraram para um único
  `st.expander("Por que {motor_rotulo or 'o motor do arquétipo'} e não DDM?")`, exibido só quando
  `san01_reetiquetado` OU `divergencia_ativa`. Conteúdo/valores idênticos; só mudou o container
  (`st.info`/`st.warning` → `st.markdown` dentro do expander).
- Veredito colorido (`st.success/error/warning`) permanece como a única caixa principal.
- FORA do expander e intactos: banner "Classificação incerta" (VER-02), selo de sustentabilidade,
  alerta "Verificar dados" e alertas de dado (Payout>100% etc.).
- Ordem final: veredito → expander opcional → Classificação incerta → selo → alertas → métricas.

### Task 3 — Gate de testes (verde)
- `python -m pytest -q` → **448 passed** em 5,32s. Nenhuma edição em `tests/`, `report.py` ou engine.

## Deviations from Plan

None - plano executado exatamente como escrito. Nota de implementação: o rótulo `_label_intr`
já produzia `"Intrínseco ({motor_rotulo})"` no caso `_usa_motor` (motor!=ddm E banda_do_motor),
então não precisou ser alterado — só o VALOR da manchete mudou.

## Known Stubs

Nenhum.

## Verification

- `python -c "import ast; ast.parse(open('app.py').read())"` → syntax ok (após cada task).
- `grep -n "intrinseco_motor" app.py` e `grep -n "st.expander" app.py` confirmam as âncoras.
- `python -m pytest -q` → 448 passed, 0 failed (firewall selo↛report intacto).
- Diff restrito ao intervalo ~884-1015 de `app.py`; `report.py` e engine intocados.
- Restrição dura respeitada: R$ 32,88 (a.intrinseco_motor do ITUB4) não muda — só o render.

## Self-Check: PASSED
- FOUND: app.py (modificado, commits af24abf + 9897bd9)
- FOUND: af24abf (Task 1), 9897bd9 (Task 2)
- 448 passed
