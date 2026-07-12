---
phase: quick-260712-p6r
plan: 01
subsystem: valuation/ranking
tags: [freio, paridade-cli-streamlit, ens-01, refactor, veredito-honesto]
requires:
  - analista.core.arquetipo
  - analista.core.comparables
provides:
  - analista.core.freio (motor_pendente + alvo_regressao_confiavel — freio puro compartilhado)
  - app.py aba Ranking com freio aplicado (paridade com cli.cmd_rank)
affects:
  - src/analista/cli.py (re-export + label ENS-01)
  - app.py (aba Ranking)
  - tests/test_ranking_freio.py
tech-stack:
  added: []
  patterns:
    - "Fonte única de função compartilhada por CLI e Streamlit (paridade por construção via `is`)"
key-files:
  created:
    - src/analista/core/freio.py
  modified:
    - src/analista/cli.py
    - app.py
    - tests/test_ranking_freio.py
decisions:
  - "Freio do Ranking extraído para core/freio.py como fonte única — cli.py re-exporta (alias _motor_pendente preserva import dos testes); app.py importa direto. Paridade CLI↔Streamlit por construção, travada por teste `is`."
  - "Aba Ranking do Streamlit reetiqueta motor_pendente/reg-frágil como 'Ver Analisar a fundo (motivo)' em vez de cravar Cara/Subavaliada — dado ausente (pa is None) mantém 'indisponível' (≠ freio). NOTA/Selo/régua intactos."
  - "ENS-01: mid do ensemble motor×DDM renomeado ddm_mid→ensemble_mid; aviso e comentário deixam de chamá-lo 'DDM absoluto'; removida cláusula estagnada 'reconciliação na Fase 3'. Saída numérica inalterada."
metrics:
  duration: ~20min
  completed: 2026-07-12
---

# Quick Task 260712-p6r: Freio do Ranking no Streamlit (paridade CLI↔UI) + label ENS-01 Summary

Fecha o BLOCKER da auditoria v2.2: a aba "Ranking por múltiplos" do Streamlit passou a aplicar o
MESMO freio de arquétipo/fragilidade do CLI `cmd_rank`, reusando um módulo compartilhado
(`core/freio.py`) — a mesma ação (ITUB4) não aparece mais "Cara" no Ranking e protegida no
Analisar. Também corrige o label drift ENS-01 em `cmd_rank` (o mid é o ensemble motor×DDM, não
"DDM absoluto").

## What Was Built

- **`src/analista/core/freio.py`** (novo): `motor_pendente(c, cfg)` e
  `alvo_regressao_confiavel(reg, pa, motor_pendente)` movidos de cli.py sem alterar lógica.
  Importa só `arquetipo` e `comparables` (core), preservando o firewall selo↛report e mantendo
  `motor_pendente` offline.
- **`src/analista/cli.py`**: re-exporta o freio (`from .core.freio import alvo_regressao_confiavel,
  motor_pendente as _motor_pendente`) — o alias preserva `tests/test_ranking_freio.py:21` e o uso
  em cmd_rank. Correção ENS-01: `ddm_mid`→`ensemble_mid`, comentário/aviso rotulam o mid como
  ensemble motor×DDM, cláusula "reconciliação na Fase 3" removida.
- **`app.py`** (aba Ranking, `elif modo.startswith("Ranking")`): importa `from analista.core import
  freio` e, no loop que monta `rows`, aplica `freio.motor_pendente` + `freio.alvo_regressao_confiavel`
  antes de decidir veredito/preço-alvo/upside — espelhando cmd_rank. `pa is None` → mantém
  "indisponível (ROE/payout ausente)"; `not confiavel` → "—"/"—"/"Ver Analisar a fundo (motivo)";
  `confiavel` → comportamento anterior (Subavaliada/Cara + payout ajustado). NOTA/Selo intactos.
- **`tests/test_ranking_freio.py`**: teste de paridade de superfície
  (`freio.alvo_regressao_confiavel is cli.alvo_regressao_confiavel` e `freio.motor_pendente is
  cli._motor_pendente`) + caso documentando a supressão de motor_pendente na aba Ranking.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extrair freio para core/freio.py + re-export em cli.py | f800e65 | src/analista/core/freio.py, src/analista/cli.py |
| 2 | Aplicar freio na aba Ranking do app.py + teste de paridade | 1329f95 | app.py, tests/test_ranking_freio.py |
| 3 | Corrigir label drift ENS-01 em cmd_rank | f9ace2d | src/analista/cli.py |

## Deviations from Plan

None — plano executado como escrito. (Ajuste menor de redação: no comentário do aviso de
divergência a expressão "DDM absoluto" foi substituída por "ensemble motor×DDM, valuation absoluto"
para satisfazer a verificação `! grep "DDM absoluto"` da Task 3, sem mudar o cálculo.)

## Verification

- `./.venv/bin/python -m pytest -q` → **437 passed** (435 baseline + 2 novos testes de paridade).
- Firewall intacto: `selo.py` NÃO importa `report`; `core/freio.py` NÃO importa report/selo
  (só menções em docstring).
- Fonte única confirmada: `analista.cli.alvo_regressao_confiavel is
  analista.core.freio.alvo_regressao_confiavel` (e o mesmo para `_motor_pendente`).
- `app.py`: `ast.parse` OK; `grep "freio\."` mostra as chamadas na aba Ranking.
- Strings de drift ausentes em cli.py: `ddm_mid`, "DDM absoluto", "reconciliação na Fase 3".
- Tickers-default do app (utilities reguladas, motor_pendente=False) inalterados.

## Self-Check: PASSED

- FOUND: src/analista/core/freio.py
- FOUND commit f800e65, 1329f95, f9ace2d
