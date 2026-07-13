---
phase: 05-backtest-01-valida-o-na-cesta-de-bancos
plan: 01
subsystem: testing
tags: [backtest, snapshot, fixture, yaml, rim, valuation, banks, deterministic]

# Dependency graph
requires:
  - phase: 04-rim-com-valor-terminal-ke-revisado
    provides: "RIM calibrado com valor terminal (ITUB4 ~R$32,87 ao vivo); knobs motores.rim em config.yaml"
provides:
  - "Snapshot congelado (raw fundamentals + preço + beta + rf_local + rota observada) dos 4 bancos ITUB4/BBAS3/BBSE3/BBDC4, data-base 2026-07-12"
  - "scripts/capturar_snapshot_bancos.py — captura one-time ao vivo, reproduzível/auditável (D-05)"
  - "Reprodução offline confirmada: cada CompanyData reconstruído reproduz a.intrinseco_motor com <0,01 de erro"
  - "Rota financeira→rim registrada por ticker (4/4 bancos); BBSE3 casa o token seguradora — sem exceção de roteamento"
affects: [05-02-fair-values, 05-03-script-harness, 05-04-test-backtest-bancos]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fixture YAML versionado de raw fundamentals (não valores derivados) → teste imune a mudança de assinatura de motores.rim (loop D-12 re-roda o snapshot)"
    - "Captura ao vivo isolada num script standalone; rede vive só na captura, teste 100% offline/determinístico"

key-files:
  created:
    - scripts/capturar_snapshot_bancos.py
    - tests/fixtures/snapshot_bancos_2026-07-12.yaml
  modified: []

key-decisions:
  - "rf_local congelado = default shipado 0.105 (NÃO chamar macro.selic_ciclo_para_capm); a rede fica só na captura de fundamentos"
  - "Congelar raw fundamentals + rota observada por ticker, nunca vpa0/roe0/ke derivados (preserva o teste de roteamento e desacopla dos internals do motor)"
  - "Rota lida da captura, nunca assumida: os 4 bancos gravam motor_observado/arquetipo_observado/intrinseco_motor_observado"

patterns-established:
  - "Snapshot fixture: raw fundamentals + escalares de mercado + rf_local global + rota observada por ticker"
  - "Guarda-corpo de captura: campo obrigatório do RIM ausente/None → falha explícita (blocker), nunca fabricar valores"

requirements-completed: [VAL-01]

# Metrics
duration: 12min
completed: 2026-07-13
---

# Phase 5 Plan 01: Captura do Snapshot Congelado da Cesta de Bancos Summary

**Snapshot YAML determinístico dos 4 bancos (ITUB4/BBAS3/BBSE3/BBDC4) capturado uma vez ao vivo via `build.montar_empresa` e validado offline: reconstrói `analisar_acao` reproduzindo o RIM da Fase 4 (ITUB4 R$32,88), com rota financeira→rim registrada por ticker.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-13T01:02Z
- **Completed:** 2026-07-13
- **Tasks:** 2
- **Files modified:** 2 (criados)

## Accomplishments
- `scripts/capturar_snapshot_bancos.py`: captura one-time ao vivo (CVM+Yahoo+BCB), reproduzível/auditável, com guarda-corpo que falha explicitamente se uma fonte vier incompleta (nunca fabrica valores).
- `tests/fixtures/snapshot_bancos_2026-07-12.yaml`: raw fundamentals (lucro/PL/nº ações/dividendos + vendas/fco opcionais) + `preco_atual` + `beta` + `dpa_trailing_12m` por ticker, `rf_local`/`data_base` globais, e a rota observada (`motor_observado`/`arquetipo_observado`/`intrinseco_motor_observado`).
- Reprodução offline confirmada: reconstruir cada `CompanyData` do YAML + injetar o `rf_local` congelado + rodar `report.analisar_acao` reproduz `a.intrinseco_motor` com erro < 0,01 vs o valor gravado na captura.
- Gate ITUB4 verde: `financeira`/`rim`/R$32,88 (dentro da faixa 30–40, bate o live R$32,87 da Fase 4).

## Task Commits

1. **Task 1: Script de captura + captura ao vivo dos 4 bancos** — `5aa5bac` (feat)
2. **Task 2: Validação da reprodução offline** — sem commit (validação pura; nenhum campo faltante, nenhuma re-rota → nada a ajustar no snapshot)

## Files Created/Modified
- `scripts/capturar_snapshot_bancos.py` — captura one-time D-05 via `build.montar_empresa`; extrai os campos mínimos, roda `analisar_acao` para carimbar a rota, grava o YAML.
- `tests/fixtures/snapshot_bancos_2026-07-12.yaml` — snapshot congelado dos 4 bancos, versionado, data-base carimbada.

## Rota observada por ticker (D-08)

| Ticker | Setor CVM | Arquétipo | Motor | Intrínseco RIM | Preço |
|--------|-----------|-----------|-------|----------------|-------|
| ITUB4 | Bancos | financeira | rim | R$32,88 | R$44,30 |
| BBAS3 | Bancos | financeira | rim | R$45,60 | R$20,58 |
| BBSE3 | Emp. Adm. Part. - Seguradoras e Corretoras | financeira | rim | R$25,38 | R$40,35 |
| BBDC4 | Bancos | financeira | rim | R$10,47 | R$18,86 |

**Todos os 4 rotearam financeira→rim** — o setor CVM da BBSE3 ("...Seguradoras e Corretoras") casou o token `seguradora` (word-boundary, plural), então **não houve exceção de roteamento (D-08) neste plano**. A incerteza antecipada pela RESEARCH (A1) resolveu-se a favor do RIM.

## Decisions Made
- **rf_local congelado = 0.105 (default shipado):** captura não chama a Selic ao vivo; a rede vive só na coleta de fundamentos. Garante que o número congelado bate a reprodução offline (Task 2 injeta o mesmo `rf_local` antes de `analisar_acao`).
- **Congelar raw fundamentals, não derivados:** preserva o teste de roteamento e mantém o snapshot imune a mudança de assinatura interna de `motores.rim` (loop D-12 re-roda o script, não reescreve o teste).

## Deviations from Plan

None - plan executed exactly as written. Escopo cirúrgico respeitado: nenhum arquivo de motor/config tocado (`git status` confirmou zero mudança em `core/motores.py`, `core/ddm.py`, `report/selo.py`, `core/lentes.py`, `config.yaml`).

## Issues Encountered

- **BBDC4 intrínseco baixo (R$10,47 vs preço R$18,86):** o RIM entrega o Bradesco abaixo do book — caso "bad-bank" (ROE de valuation < Ke → valua < VPA), comportamento shipado do guarda anti-bad-bank da Fase 4. Reproduz de forma estável; **não é bug deste plano** (só captura raw). É o candidato natural a `excecao_nota` no gate de fair values (Plan 05-04), não a exceção de roteamento.
- **Quirks de dados brutos da CVM** (ex.: ITUB4 `num_acoes` 2019 anômalo; BBSE3 `vendas_liquidas` = 0 — holding sem linha de receita) foram congelados fielmente como capturados. Não afetam o RIM (usa o último ano, 2025) e estão fora do escopo cirúrgico deste plano.

## Next Phase Readiness
- Snapshot congelado pronto para os planos seguintes: 05-02 (tabela de fair values de consenso), 05-03 (script harness `rodar_cesta`), 05-04 (`tests/test_backtest_bancos.py`).
- A rota financeira→rim confirmada para os 4 bancos simplifica o gate: nenhuma exceção de roteamento a documentar; o único desvio de VALOR candidato a nota é o BBDC4 (bad-bank), a ser triangulado contra o fair value no Plan 05-04.

## Self-Check: PASSED

- FOUND: scripts/capturar_snapshot_bancos.py
- FOUND: tests/fixtures/snapshot_bancos_2026-07-12.yaml
- FOUND commit 5aa5bac (Task 1)

---
*Phase: 05-backtest-01-valida-o-na-cesta-de-bancos*
*Completed: 2026-07-13*
