---
phase: 06-redeploy-do-app-v2-3-na-vps
plan: 01
subsystem: ops/deploy
tags: [deploy, gate, git-tag, release, v2.3]
requires:
  - "Suíte de testes verde (Fases 1-5) — engine v2.3"
  - "Loop D-12 fechado (Fase 04 it.2) — cesta de bancos 4/4"
provides:
  - "git tag v2.3 no remote voictrafego/money (versão nomeada reproduzível)"
  - "main sincronizado no remote voictrafego/money (fonte de verdade do deploy)"
  - "Gate pré-deploy OPS-01 comprovado (448 verde + firewall selo↛report intacto)"
affects:
  - "06-02 (redeploy na VPS dará checkout da tag v2.3)"
tech-stack:
  added: []
  patterns:
    - "Gate pré-deploy como HARD BLOCK (D-10): push só após suíte verde"
    - "Deploy reproduzível amarrado a tag git anotada (D-04)"
key-files:
  created:
    - ".planning/phases/06-redeploy-do-app-v2-3-na-vps/06-01-SUMMARY.md"
  modified: []
decisions:
  - "Tag v2.3 anotada no HEAD de main (a0fb0be), mensagem documenta a cesta 4/4"
  - "gh auth switch -u voictrafego explícito antes do push (única conta com permissão; D-03)"
metrics:
  duration: "~8min"
  completed: "2026-07-13"
  tasks: 2
  files: 1
---

# Phase 6 Plan 01: Gate pré-deploy + entrega v2.3 ao GitHub — Summary

Gate pré-deploy (D-10) comprovado verde e código v2.3 publicado no remote `voictrafego/money`
via tag anotada `v2.3` + `main` sincronizado — a VPS já pode dar checkout da versão nomeada (06-02).

## What Was Built

- **Gate pré-deploy (Task 1):** suíte completa `python -m pytest -q` = **448 passed, 0 failed**
  (ordem ~447 esperada, +1). O teste do firewall `test_selo.py::test_firewall_selo_nao_importa_report`
  passa explicitamente — `selo.py` não importa `report.py`. HARD BLOCK D-10 satisfeito: só com a
  suíte verde a Task 2 foi liberada.
- **Entrega v2.3 (Task 2):** conta ativa do `gh` confirmada/trocada para `voictrafego`
  (`gh auth switch -u voictrafego`), tag anotada `v2.3` criada no HEAD de `main` (a0fb0be),
  `git push origin main` + `git push origin v2.3` bem-sucedidos (nenhum 403).

## Verification

| Critério | Resultado |
|----------|-----------|
| `python -m pytest -q` | 448 passed, 0 failed (status 0) |
| `test_firewall_selo_nao_importa_report` | passed |
| `gh auth status --active` | voictrafego (active) |
| `git ls-remote --tags origin refs/tags/v2.3` | `38f8491 refs/tags/v2.3` (presente) |
| `git ls-remote origin refs/heads/main` | `a0fb0be` == HEAD local (sincronizado) |
| Push 403 | Nenhum |

Nota: a tag anotada `v2.3` é o objeto `38f84919...`, que aponta para o commit `a0fb0be` (HEAD de main).

## Deviations from Plan

None — plano executado exatamente como escrito. A conta `gh` ativa já era `voictrafego` no início
(pré-verificada pelo orquestrador); o `gh auth switch` foi rodado assim mesmo para tornar a
pré-condição D-03 explícita. As duas tasks são gate/operações git e não produziram mudanças na
árvore de trabalho, portanto não há commits por-task (só o commit de metadados do plano).

## Authentication Gates

Nenhum gate de auth interativa foi disparado (D-02 não acionado): o `gh` estava autenticado via
keyring (token com escopo `repo`), o push HTTPS usou o credential helper do `gh` sem prompt.

## Notes for Next Plan (06-02)

- A VPS deve dar `git fetch` + `checkout` da tag **`v2.3`** em `/root/money` (D-04), depois
  `docker build -t money:latest .` → `docker service update --force --image money:latest lazari_money`
  no stack `lazari` (**nunca `--remove-orphans`**, D-05).
- Rollback safety (D-06): taguear a imagem atual como `money:pre-v2.3` antes do rebuild.
- Nenhum deploy foi feito neste plano — só a publicação do código à fonte de verdade.

## Self-Check: PASSED

- FOUND: `.planning/phases/06-redeploy-do-app-v2-3-na-vps/06-01-SUMMARY.md`
- FOUND: remote tag `v2.3` em `voictrafego/money` (`38f8491` → `a0fb0be`)
- FOUND: remote `main` == HEAD local (`a0fb0be`)
