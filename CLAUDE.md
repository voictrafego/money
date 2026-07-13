<!-- GSD:project-start source:PROJECT.md -->
## Project

**Analista de Dividendos**

Engine Python + app Streamlit que replica o método do livro *O Investidor em Ações de Dividendos*
(Orleans Martins & Felipe Pontes) para analisar ações de dividendos da B3, usando apenas dados
gratuitos (CVM + Yahoo Finance + Banco Central). Voltado ao investidor pessoa física que quer
aplicar o método do livro sem pagar por terminais de dados.

**Core Value:** Os números que o app mostra precisam ser **fiéis ao método do livro e consistentes entre si** —
a mesma ação não pode parecer barata num menu e cara/ausente em outro sem explicação.

### Constraints

- **Tech stack**: Python 3 + Streamlit; sem backend próprio; custo zero (só dados gratuitos)
- **Infra/git**: este projeto agora é um **repositório git dedicado** (`git init` próprio),
  desacoplado do repositório do `$HOME`. `.planning/` vive dentro do projeto.

### O que significa "suíte verde" (regra do v2.4 — Fase 7 / BLIND)

A regra antiga — a que exigia manter **todos** os goldens de `tests/` verdes — foi **REVOGADA**.
Ela foi escrita no v1.x, quando os goldens codificavam o método **pretendido**. O v2.4 provou que
eles codificam um método **errado**: o golden `ITUB4 = 32,88` existe para cancelar um haircut de
−9,1% da normalização — **dois erros se anulando**. Mantê-los verdes é manter a doença.

- **`pytest` verde** = **0 failed**, com os `golden_nivel` em **quarentena** (deselecionados por
  `addopts`) e **2 xfailed** (BLIND-02b e BLIND-03 — as duas doenças, escritas como código, que
  ficam verdes sozinhas nas Fases 12 e 10) e **1 skipped** (o veredito do jackknife, aguarda a
  Fase 14). `pytest -m ""` roda tudo; `pytest -m golden_nivel` roda os quarentenados sob demanda.
- **Golden de nível quebrou? DELETE, não atualize.** Atualizar o número mantém vivo exatamente o
  reflexo que produziu o overfit do v2.3. A classificação dos testes vive em
  `tests/classificacao.yaml` (completude imposta na coleta: teste sem entrada **quebra a coleta**).
- **O orçamento de knobs vive em `calibracao.lock.yaml`** (raiz): **exatamente 3 graus de
  liberdade** — `ERP`, `n_fade`, `PIB_real`. Mexer em **qualquer** knob de valuation exige mexer no
  lock **no mesmo diff**. Um 4º grau de liberdade deixa a suíte vermelha.
- **Uma justificativa legítima de knob nunca menciona um ticker.** É teste (`-k justificativa`) e é
  hook (`.githooks/commit-msg`).
- **NUNCA** afrouxar tolerância, marcar `xfail` casual, trocar `xfail` por `skip` ou deletar assert
  para a suíte ficar verde. Se um teste da blindagem fica vermelho, o que mudou foi o **sistema**.
- **Todo clone novo nasce sem o hook** (`core.hooksPath` é estado local, não versionado):
  `git config core.hooksPath .githooks`. O teste `-k hook_do_blind05_esta_instalado` avisa.
- `pytest tests/arquivo.py` **não funciona** neste repo (dispara `CLASSIFICACAO ORFA`). Use `-k`.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
