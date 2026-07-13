---
phase: 05-backtest-01-valida-o-na-cesta-de-bancos
plan: 04
subsystem: backtest-gate
tags: [backtest, gate, quorum, xfail, d-12, regressao, offline, val-01, val-02]
requires:
  - src/analista/backtest.py::rodar_cesta          # 05-03 (harness puro reusado)
  - tests/fixtures/snapshot_bancos_2026-07-12.yaml # 05-01 (RIM congelado)
  - tests/fixtures/fair_values_bancos.yaml         # 05-02 (faixas de consenso aprovadas)
provides:
  - tests/test_backtest_bancos.py                  # gate deterministico quorum-3/4-±15% (VAL-01/VAL-02)
affects:
  - Phase 04 (rim-com-valor-terminal) — REABERTURA sinalizada (loop D-12): calibracao nao generaliza
  - Phase 06 (OPS-01 deploy) — bloqueada ate o loop D-12 fechar
tech-stack:
  added: []          # zero dep nova: pytest.mark.xfail ja disponivel
  patterns:
    - "gate encoda a regra VERBATIM e marca xfail(strict) quando a realidade congelada reprova — nunca afrouxa a banda/quorum"
    - "strict=True = tripwire: XPASS forca remover o marcador e fechar o loop D-12 quando a Fase 4 recalibrar"
    - "teste reusa rodar_cesta (mesmo harness do script) — prova o mesmo numero, nao reimplementa RIM"
key-files:
  created:
    - tests/test_backtest_bancos.py
  modified: []
decisions:
  - "D-12 disparado: cesta 1/4 na banda ±15% < quorum 3/4 — calibracao da Fase 4 NAO generaliza; achado registrado + Fase 4 reaberta, gate NAO afrouxado"
  - "Falha em DOIS sentidos (BBAS3 super-avaliado +54.6%, BBSE3/BBDC4 sub-avaliados) — nao e vies uniforme corrigivel por 1 knob"
  - "gate marcado xfail(strict=True) — suite verde SEM silenciar: reprovacao rastreavel, vira XPASS→FAIL quando recalibrar"
  - "nenhuma excecao_nota espuria adicionada: 3 falhas != 1 excecao documentavel (D-08); afrouxar seria fraude ao gate (T-05-10)"
metrics:
  duration: 0h14m
  completed: 2026-07-13
  tasks: 2
  files: 1
---

# Phase 05 Plan 04: Gate determinístico do backtest da cesta de bancos Summary

Gate pytest determinístico e offline (`tests/test_backtest_bancos.py`) que crava o critério
quórum-3/4-±15% (D-06/D-07/D-08) do RIM calibrado da Fase 4 contra as faixas de consenso, reusando
a mesma `rodar_cesta` do script. **O gate reprova a cesta (1/4 < 3/4) — achado D-12 registrado, Fase
4 reaberta, gate NÃO afrouxado.** Suíte completa verde (442 passed, 1 xfailed; baseline 440).

## O que foi construído

**Task 1 — `tests/test_backtest_bancos.py` (commit 5cff323):**

Três testes espelhando o molde de `test_vulc3_regressao.py`, importando `rodar_cesta`,
`carregar_snapshot`, `carregar_fair_values` e `BANDA_PASS` de `analista.backtest` (mesmo harness do
script → mesmo número). Constante nomeada `QUORUM_MIN = 3` (D-08); `BANDA_PASS` importada (D-07),
zero número solto no corpo do gate.

1. `test_backtest_cesta_rota_por_ticker` — ITUB4: `arquetipo == "financeira"`, `motor == "rim"`,
   RIM ∈ [30, 40] (bounds absolutos). Loop de segurança: qualquer roteamento ≠ rim exige
   `excecao_nota` (D-08). Hoje os 4 roteiam para RIM. **PASS.**
2. `test_backtest_gate_quorum_e_anotacao` — `assert len(passes) >= QUORUM_MIN` + loop
   `for r in falhas: assert r["excecao_nota"]` (barra FAIL silencioso). Encoda a regra VERBATIM.
   Marcado `@pytest.mark.xfail(strict=True, reason=...)` porque a cesta congelada reprova (ver
   finding). **XFAIL (esperado).**
3. `test_backtest_determinismo` — `rodar_cesta` duas vezes, RIM idêntico por ticker (igualdade
   exata, não `approx`). Prova reprodutibilidade offline. **PASS.**

**Task 2 — confirmação da suíte + tratamento do loop D-12 (sem novo commit de código):**

Suíte completa `pytest` = **442 passed, 1 xfailed** (baseline 440 passed → +2 passing +1 xfail, zero
regressão). Invariantes HARD verdes (32 passed): `test_ddm` (DDM Itaú R$37,22), `test_vulc3_regressao`
(capstone e2e), `test_selo` (firewall selo↛report + matriz de cores), `test_consistencia_modos`
(mesmo número entre Analisar/Garimpo/Ranking). `git diff --name-only` = apenas
`tests/test_backtest_bancos.py`; core/motores.py, core/lentes.py, core/ddm.py, report/selo.py,
config.yaml **intocados** (escopo cirúrgico). Nenhuma `excecao_nota` espúria adicionada ao fixture.

## Finding D-12 (registrado — loop para a Fase 4)

**A calibração RIM da Fase 4, afinada no ITUB4, NÃO generaliza na cesta: 1/4 na banda ±15%, abaixo
do quórum 3/4.** E falha em DOIS sentidos opostos — não é o viés uniforme "~40-50% abaixo" corrigível
por um único knob.

| Ticker | Motor | RIM observado | Faixa FV (consenso) | Banda ±15% | Desvio vs. mid | Veredito |
|--------|-------|---------------|---------------------|------------|----------------|----------|
| ITUB4  | rim   | 32.88         | 30.50–50.00         | 25.93–57.50 | −18.3%        | **PASS** |
| BBAS3  | rim   | 45.60         | 20.00–39.00         | 17.00–44.85 | **+54.6%**    | FAIL (acima) |
| BBSE3  | rim   | 25.38         | 33.00–46.00         | 28.05–52.90 | **−35.7%**    | FAIL (abaixo) |
| BBDC4  | rim   | 10.47         | 15.00–24.00         | 12.75–27.60 | **−46.3%**    | FAIL (abaixo) |

**Hipóteses de causa (para a Fase 4 investigar):**

- **BBAS3 (+54.6%, super-avaliado):** anomalia mais grave — o RIM valua ACIMA do teto de consenso.
  Suspeitos: (a) o `num_acoes` dobra em 2024 (3,16 bi → 6,31 bi; desdobramento/bonificação) e cai para
  5,71 bi em 2025, distorcendo VPA/ROE por ação na janela; (b) o valor terminal (Fase 4) super-dispara
  no ROE alto do BB. Precisa de guarda contra split não-normalizado e/ou teto no prêmio terminal.
- **BBSE3 (−35.7%, sub-avaliado):** BB Seguridade é **seguradora capital-light**, não banco de balanço
   (`vendas_liquidas` = 0 em todos os anos, ROE altíssimo sobre PL pequeno). O RIM ancorado em book
  sub-avalia um negócio cujo valor está no fluxo de lucro, não no patrimônio. Flag já antecipado em
  CONTEXT §specifics — mas roteia para `rim`, então é falha de AJUSTE de modelo, não exceção de
  roteamento (não cabe `excecao_nota`).
- **BBDC4 (−46.3%, sub-avaliado):** padrão crônico de subestimação — Bradesco em vale de ROE
  (turnaround), a guarda anti-bad-bank fade o valor terminal com força e valua abaixo do book; o
  consenso precifica recuperação forward que o RIM não credita.

**Ação de loop:** a Fase 4 (`04-rim-com-valor-terminal-ke-revisado`) precisa **reabrir** para
recalibrar antes que o v2.3 possa declarar o RIM "validado na cesta". A Fase 6 (deploy OPS-01) fica
bloqueada até o loop fechar. Quando a recalibração cruzar o quórum, `test_backtest_gate_quorum_e_anotacao`
vira **XPASS → FAIL** (strict), forçando remover o marcador `xfail` e fechar o loop explicitamente —
nunca silencioso.

## Deviations from Plan

**1. [Rule 2 / D-12 - interpretação de loop] Gate marcado `xfail(strict=True)` em vez de PASS trivial**

- **Encontrado durante:** Task 1 (ao rodar o gate sobre o snapshot congelado).
- **Situação:** o plano assume no acceptance-criteria da Task 1 que o gate sai verde (exit 0), mas os
  dados congelados (1/4 na banda) fazem o `assert len(passes) >= QUORUM_MIN` reprovar legitimamente —
  o caminho `≤2 PASS → loop D-12` que o próprio plano prevê no corpo da Task 1/Task 2. Há tensão real
  entre o must-have "suíte verde" e o must-have "reprovação registrada + loop D-12, não silenciada".
- **Resolução:** encodar o gate **VERBATIM** (banda ±15% e quórum 3/4 intactos, executados, reprovando)
  e marcá-lo `xfail(strict=True)` com `reason` apontando para o finding + reabertura da Fase 4. Isto
  satisfaz os dois must-haves: (a) suíte verde (xfail é falha esperada, exit 0); (b) gate NÃO afrouxado
  (T-05-10) e reprovação **não silenciada** (T-05-11) — `strict=True` é tripwire que vira XPASS→FAIL
  ao recalibrar. É exatamente o "documented-failure test" autorizado pelo orquestrador para o caminho D-12.
- **NÃO feito (deliberadamente):** não afrouxei banda/quórum; não adicionei `excecao_nota` espúria (3
  falhas ≠ 1 exceção documentável — seria fraude ao gate); não toquei core/config para forçar verde.
- **Arquivos:** `tests/test_backtest_bancos.py`. **Commit:** 5cff323.

## Verification

- `pytest tests/test_backtest_bancos.py -q` → exit 0 (2 passed, 1 xfailed). ✓
- `pytest` (suíte cheia) → **442 passed, 1 xfailed** (baseline 440 passed; +2/+1 xfail, zero regressão). ✓
- `grep -v '^#' tests/test_backtest_bancos.py | grep -c QUORUM_MIN` = 2 (≥1, constante nomeada). ✓
- `assert len(passes) >= QUORUM_MIN` + loop `for ...: assert ...excecao_nota` presentes (gate íntegro, não afrouxado). ✓
- Asserção de determinismo (RIM idêntico em duas execuções) presente e verde. ✓
- ITUB4: `motor == "rim"`, RIM 32.88 ∈ [30, 40]. ✓
- Invariantes HARD verdes: test_ddm (R$37,22), test_vulc3_regressao capstone, firewall selo↛report, test_consistencia_modos (32 passed). ✓
- `git diff --name-only` = apenas `tests/test_backtest_bancos.py`; motores/lentes/ddm/selo/config intocados. ✓
- Loop D-12 tratado: finding registrado (ticker/RIM/FV/desvio/causa) + reabertura da Fase 4 sinalizada; gate NÃO afrouxado. ✓

## Self-Check: PASSED

- FOUND: tests/test_backtest_bancos.py
- FOUND commit: 5cff323 (Task 1)
