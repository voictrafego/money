---
phase: 01-classificador-de-arqu-tipo-roteamento
plan: 04
subsystem: ui/streamlit-render
tags: [arquetipo, ui, streamlit, gap-closure, read-only, paridade-cli-ui]
gap_closure: true
requires:
  - "AnaliseAcao.arquetipo / .motor já populados por analisar_acao (Plan 01-02, report.py:52-56,147-153)"
  - "esc_md(...) helper já existente em app.py:289"
provides:
  - "UI Streamlit (app.py) exibe 'Arquétipo: X → motor Y' no caption principal, junto a Setor/Estágio, incondicional em motor_pendente"
  - "paridade CLI/UI para a SC#1 (arquétipo exibido antes do bloco de valuation)"
affects:
  - "Fase 3 (veredito honesto): a UI já expõe o arquétipo/candidatos; consumo futuro pode reusar o caption"
tech-stack:
  added: []
  patterns:
    - "render aditivo read-only na UI: só LÊ campos derivados na engine (a.arquetipo/a.motor), zero recálculo"
    - "esc_md(...) em conteúdo dinâmico, consistente com o resto do arquivo (defesa em profundidade T-01-04-01)"
key-files:
  created:
    - .planning/phases/01-classificador-de-arqu-tipo-roteamento/01-04-SUMMARY.md
  modified:
    - app.py
decisions:
  - "st.caption ADICIONAL após a linha 881 (não concatenar no caption Setor/Estágio) — lê melhor e mantém o diff mínimo e legível"
  - "Render INCONDICIONAL (sem guard por a.motor_pendente): fecha o buraco da pagadora_regulada/TAEE11 (motor=ddm, não suspenso), que era exatamente o caso sem exposição na UI"
metrics:
  duration: "~0h08m"
  completed: "2026-07-11"
  tasks: 1
  files: 1
  suite: "355 passed (baseline 354; mudança read-only na view, nenhum golden tocado)"
---

# Phase 1 Plan 04: Exposição de Arquétipo/Motor na UI Streamlit Summary

Fechou o Gap 2 (partial, SC#1 exposição na UI) da 01-VERIFICATION.md: `app.py` — a interface
Streamlit primária e documentada do projeto — agora exibe explicitamente
`Arquétipo: {a.arquetipo} → motor {a.motor}` no caption principal de render, ao lado de
Setor/Estágio e antes do bloco de veredito/valuation, em paridade com o CLI (report.py:452).
A exibição é **incondicional** — aparece inclusive para a pagadora regulada (TAEE11, motor='ddm',
não suspenso), que era exatamente o caso em que a UI nunca nomeava a classificação em lugar nenhum.

## What Was Built

- **`app.py:882` — st.caption adicional** logo após o caption `Setor/Estágio` (:881), dentro do
  ramo `else:` de dados OK e ANTES do bloco de veredito (:884): `st.caption(f"Arquétipo:
  {esc_md(a.arquetipo or '—')} → motor {esc_md(a.motor or '—')}")`.
- **Read-only e aditivo:** só LÊ `a.arquetipo`/`a.motor` (campos já derivados na engine pelo
  Plan 01-02); zero fórmula, zero recálculo, nenhuma alteração em `report.py`/`arquetipo.py`.
- **`esc_md(...)`** em ambos os campos dinâmicos, consistente com o resto do arquivo (defesa em
  profundidade, T-01-04-01) — mesmo os valores vindo de um enum interno fixo.
- **Sem guard por `a.motor_pendente`:** decisão deliberada para cobrir o caso não-suspenso
  (pagadora_regulada/TAEE11), o ponto cego identificado pela verificação.

## Task Commits

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Expor Arquétipo → motor no caption da UI Streamlit | 33571eb | app.py |

## Verification

- `grep -n "a.arquetipo" app.py` → 1 ocorrência (linha 882, no render principal); `a.motor` idem.
- `python -c "import ast; ast.parse(open('app.py').read())"` → `ast-ok` (arquivo válido).
- `python -m pytest -q` → **355 passed, 0 failed** (baseline 354; mudança read-only na view não
  quebra nenhum golden).
- `git diff --name-only` (do commit da task) == `app.py` — nenhum outro arquivo tocado.
- Sem deleções no commit (`git diff --diff-filter=D HEAD~1 HEAD` vazio).

## Deviations from Plan

None - plano executado exatamente como escrito. Task única, `type="auto"`, sem checkpoints; sem
bugs, funcionalidade crítica ausente ou bloqueios encontrados.

## Threat Model Compliance

- **T-01-04-01 (Injection XSS/markdown):** mitigado — `a.arquetipo`/`a.motor` vêm de um enum
  interno fixo (não de input do usuário) e ainda assim passam por `esc_md(...)`, defesa em
  profundidade idêntica ao resto do arquivo.
- **T-01-04-02 (Information Disclosure):** accept (conforme registro) — expõe apenas a chave de
  arquétipo/motor, informação já pública no CLI e no propósito do produto; sem dado sensível.

## Known Stubs

Nenhum. A mudança é uma exposição completa e final do campo na UI; não há placeholder, dado mock
ou fonte de dados por conectar. O `motor == "pendente_fase_2"` que pode aparecer para arquétipos
sem motor primário é pendência planejada da Fase 2 (exposta honestamente), não um stub desta view.

## Self-Check: PASSED

- Arquivo: app.py — FOUND (contém `a.arquetipo` na linha 882).
- Arquivo: .planning/phases/01-classificador-de-arqu-tipo-roteamento/01-04-SUMMARY.md — FOUND.
- Commit: 33571eb — FOUND no git log.
