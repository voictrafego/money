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
- **Compatibility**: testes golden existentes em `tests/` devem continuar passando após as correções
- **Infra/git**: este projeto agora é um **repositório git dedicado** (`git init` próprio),
  desacoplado do repositório do `$HOME`. `.planning/` vive dentro do projeto.
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
