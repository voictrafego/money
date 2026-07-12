---
phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo
plan: 03
subsystem: valuation-engine
tags: [python, veredito, ver02, caso-fronteira, arquetipo, divergencia, range, selo, ddm]

# Dependency graph
requires:
  - phase: 01-classificador-de-arqu-tipo-roteamento
    provides: "arquetipo_fronteirico + arquetipo_candidatos (conflito real de sinais, fallback honesto) + ARQUETIPO_MOTOR"
  - phase: 03-veredito-honesto (plan 01)
    provides: "banda do ensemble motor×contraponto + dispatch motor->intrínseco no funil (a EXTRAIR)"
provides:
  - "_intrinseco_por_motor: helper de dispatch motor->intrínseco puro/never-raise/reutilizável (rim/normalizado/dcf/nav/ddm-mid)"
  - "_veredito_fronteirico (VER-02): em caso-fronteira roda o motor de cada candidato e monta o range [menor..maior] + bandeira 'classificação incerta entre X e Y'"
  - "campos arquetipo_incerto/candidatos_intrinsecos/veredito_range em AnaliseAcao"
  - "render do bloco 'Classificação incerta (caso-fronteira)' no relatorio_markdown"
affects: [app.py-render, cli-render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dispatch motor->intrínseco extraído em helper puro reutilizado pelo funil E pelo ramo fronteiriço (um motor por candidato)"
    - "Dúvida honesta em voz alta: prefixo VERIFICAR (reusa a supressão de faixa do selo, selo.py:119) + range/candidatos como conteúdo exibido"
    - "Degradação em cascata: >=2 candidatos -> range; 1 -> valor único (sem range de 1 ponto); 0 -> VERIFICAR informativo"

key-files:
  created: []
  modified:
    - "src/analista/report/report.py"
    - "tests/test_arquetipo_roteamento.py"

key-decisions:
  - "Guarda de não-positivo do dispatch fica no chamador (funil emite alerta; fronteiriço filtra > 0 ao coletar) — refator puro do funil sem perder o alerta observável"
  - "Ramo fronteiriço SOBRESCREVE o veredito do VER-01 (precedência no fronteiriço), rodando depois da árvore SUB/NO INTERVALO/SOBRE e antes do SAN-01"
  - "Caso 'ddm' no helper devolve o mid da banda (vmin/vmax) — para candidato pagadora_regulada num fronteiriço; no funil retorna None (banda ainda não calculada), preservando o baseline"
  - "Bandeira usa primeiro e último candidato resolvido como X e Y ('classificação incerta entre X e Y')"

patterns-established:
  - "Span da dúvida honesto: o range é o conteúdo, não um preço-alvo cravado; o selo não estampa faixa no fronteiriço"

requirements-completed: [VER-02]

# Metrics
duration: ~20min
completed: 2026-07-12
---

# Phase 3 Plan 03: VER-02 — Veredito honesto no caso-fronteira (range + bandeira) Summary

**Em caso-fronteira (`arquetipo_fronteirico`, conflito real de sinais da Fase 1), o veredito assume a dúvida em voz alta: roda o motor de cada arquétipo candidato via o helper extraído `_intrinseco_por_motor`, exibe o range [menor..maior] dos intrínsecos + a bandeira "classificação incerta entre X e Y" — e o selo NÃO estampa faixa cravada (reusa a supressão do prefixo VERIFICAR), sem tocar `selo.py`.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-12
- **Tasks:** 2
- **Files modified:** 2 (report.py, tests/test_arquetipo_roteamento.py)

## Accomplishments

- **Helper extraído (Task 1):** o dispatch motor→intrínseco do funil (`rim`/`normalizado`/`dcf`/`nav`) virou `_intrinseco_por_motor(motor, c, a, cfg) -> Optional[float]` — puro, never-raise, consumindo sempre números-síntese (`*_valuation`, `norm.base_normalizada`, `lentes.vpa`), nunca o cru. Caso `"ddm"` devolve o mid da banda quando disponível (para candidato pagadora_regulada num fronteiriço), senão None. O funil passou a consumir o helper — comportamento **idêntico ao baseline** (goldens de roteamento/motores/report verdes sem rebaseline).
- **Ramo fronteiriço VER-02 (Task 1):** quando `a.arquetipo_fronteirico`, `_veredito_fronteirico` itera `a.arquetipo_candidatos`, resolve `ARQUETIPO_MOTOR.get(cand)`, roda o helper por candidato e coleta os que resolveram (não-None, > 0). Com **≥2** resolvidos: `a.veredito_range = (menor, maior)` e o veredito começa com `VERIFICAR` exibindo o range + "classificação incerta entre X e Y". Com **1**: exibe o valor único sem forçar range de 1 ponto (`veredito_range is None`). Com **0**: VERIFICAR informativo. Precedência sobre o VER-01 (sobrescreve).
- **Selo suprime faixa no fronteiriço:** o prefixo `VERIFICAR` já faz `montar_selo` suprimir faixa/rótulo (selo.py:119) — `selo.faixa_do_veredito(a.veredito) is None`. `selo.py` **intocado** (firewall preservado).
- **Render (Task 2):** `relatorio_markdown` emite o bloco "Classificação incerta (caso-fronteira)" quando `a.arquetipo_incerto` — lista cada candidato com o intrínseco, a bandeira e o range (formatação ptBR via `_num`). Fora do fronteiriço: nenhum bloco novo (render limpo).

## Task Commits

1. **Task 1: Extrair _intrinseco_por_motor + ramo fronteiriço** — `e57c5f4` (feat; refator puro + ramo + testes do fronteiriço/degradação/não-fronteiriço)
2. **Task 2: Render do range/candidatos no markdown + golden fronteiriço** — `059634b` (feat; bloco no markdown + goldens de render fronteiriço/limpo)

_Nota TDD: a Task 1 é predominantemente um refator puro travado por golden existente (`test_arquetipo_roteamento`/`test_motores`/`test_report`) — a lógica extraída já tinha cobertura. Os testes NOVOS do ramo fronteiriço (RED→GREEN) foram commitados junto com a implementação no mesmo feat, seguindo o padrão do 03-01 Task 2._

## Files Created/Modified

- `src/analista/report/report.py` — 3 campos novos em `AnaliseAcao` (`arquetipo_incerto`, `candidatos_intrinsecos`, `veredito_range`); helper `_intrinseco_por_motor`; função `_veredito_fronteirico`; funil consome o helper no dispatch e chama o ramo fronteiriço após a árvore VER-01 e antes do SAN-01; bloco "Classificação incerta (caso-fronteira)" na seção Veredito de `relatorio_markdown`.
- `tests/test_arquetipo_roteamento.py` — 6 testes novos: range+bandeira (≥2 candidatos + selo suprime faixa), degradação 1 candidato (sem range de 1 ponto), 0 candidatos, não-fronteiriço não aciona VER-02, render fronteiriço (candidatos+bandeira+range) e render limpo fora do fronteiriço.

## Decisions Made

- **Guarda de não-positivo fica no chamador, não no helper.** O funil mantém o alerta observável "Motor devolveu valor não-positivo" exatamente como antes (refator puro); o ramo fronteiriço filtra `> 0` ao coletar candidatos (herda a guarda, T-0303-01/02). Assim os casos não-fronteiriços ficam byte-idênticos.
- **Precedência do fronteiriço:** roda **depois** da árvore SUB/NO INTERVALO/SOBRE do VER-01 e a **sobrescreve** com o prefixo VERIFICAR — o SAN-01 (que só dispara sobre `SOBREAVALIADA`) não é acionado no fronteiriço.
- **Caso "ddm" no helper = mid da banda:** cobre um candidato `pagadora_regulada` num fronteiriço; no dispatch do funil retorna None (a banda DDM ainda não foi calculada nesse ponto), preservando o baseline (funil nunca setava `intrinseco_motor` para ddm).
- **Bandeira X↔Y = primeiro e último candidato resolvido** ("classificação incerta entre X e Y").

## Deviations from Plan

None — plano executado exatamente como escrito. **Nenhum rebaseline de golden foi necessário**: o refator do dispatch é puro (não muda o intrínseco de nenhum ticker não-fronteiriço) e o ramo VER-02 é ADITIVO (só roda quando `arquetipo_fronteirico`). Nenhum prefixo de veredito novo foi introduzido — o ramo reusa o `VERIFICAR` existente, então `selo.faixa_do_veredito`/`_veredito_token` não precisaram mudar.

## Threat Register Outcome

Todas as disposições `mitigate` do threat model do plano foram implementadas:

- **T-0303-01 (crash em loop de candidatos):** `_intrinseco_por_motor` é never-raise (try/except → None); candidato None/≤0 é filtrado ao coletar, nunca quebra o range.
- **T-0303-02 (range de 1 ponto enganoso):** range só com ≥2 candidatos resolvidos; 1 candidato → valor único (`veredito_range is None`); 0 → VERIFICAR informativo (D-06 degradação).
- **T-0303-03 (selo estampa faixa no fronteiriço):** prefixo VERIFICAR suprime faixa/rótulo (selo.py:119); `selo.py` intocado; teste trava `faixa_do_veredito is None` e `montar_selo(...).faixa_preco is None`.

## Issues Encountered

Nenhum. O helper extraído e o ramo fronteiriço rodaram verdes na primeira execução; `_fronteirico` (fixture existente) resolve os 2 motores candidatos (ciclica R$ 9,08 × crescimento R$ 22,68), exercitando o caminho ≥2 sem fixture nova.

## Known Stubs

None — VER-02 está totalmente ligado ao veredito/render/selo. Fecha o último requisito da Active list do marco v2.2 (VER).

## Next Phase Readiness

- **SC#4 fechado:** caso-fronteira exibe range + bandeira de divergência (dúvida honesta), não selo cravado.
- **SC#5 (firewall) preservado:** goldens de roteamento/selo/consistência verdes; `selo.py` intocado.
- Suíte completa: **429 passed** (era 423 no fim do 03-02; +6 testes VER-02).

## Self-Check: PASSED

- Files modified present: report.py, tests/test_arquetipo_roteamento.py, 03-03-SUMMARY.md ✓
- Commits exist: e57c5f4, 059634b ✓
- Full suite: 429 passed ✓
- Firewall selo↛report intacto; `selo.py` não tocado ✓

---
*Phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo*
*Completed: 2026-07-12*
