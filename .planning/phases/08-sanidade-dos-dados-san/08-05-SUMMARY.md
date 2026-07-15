---
phase: 08-sanidade-dos-dados-san
plan: 05
subsystem: core
tags: [sanidade, aplicar-sanidade, confianca, never-raise, pipeline, prova-por-execucao, d-04, san-06]

# Dependency graph
requires:
  - phase: 08-sanidade-dos-dados-san
    provides: "5 checks puros checar_san01..05 + Aviso + _bucket (08-04); snapshot congelado dos 104 + loader offline (08-03)"
provides:
  - "core/sanidade.py::aplicar_sanidade — roda os 5 checks, acumula c.avisos e deriva c.confianca (escala discreta de 4 rotulos), never-raise estrutural com contador de quedas"
  - "ingest/build.py — a CHAMADA UNICA de aplicar_sanidade no pipeline real (montar_empresa), provada por execucao"
  - "tests/test_sanidade_pipeline.py — a prova D-04 (apagar a chamada fica vermelho, evasao rodada) + never-raise sobre os 104 (SAN-06)"
affects: [09-ingestao-correta-data, 13-apresentacao, 06-relatorio-cli-san]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "aplicar_sanidade: mutacao in-place + retorno, idempotente (reinicia c.avisos); cada check em try/except com quedas CONTADAS (excecao engolida = deteccao perdida em silencio)"
    - "confianca discreta de 4 rotulos (D-13): baixa (escala SAN-01/02) > media (base SAN-03/04/05) > alta (avaliado e limpo) > nao_avaliada (sem insumo) — NUNCA um score por ticker"
    - "predicados _avaliavel_sanNN separam 'avaliado e limpo' de 'nao avaliavel' — a distincao que o retorno None dos checks nao carrega sozinho"
    - "prova por execucao (D-04): teste roda o pipeline REAL com coletar_mercado monkeypatchado do snapshot; a evasao (apagar a chamada) e RODADA, nao declarada"

key-files:
  created:
    - "tests/test_sanidade_pipeline.py"
  modified:
    - "src/analista/core/sanidade.py"
    - "src/analista/ingest/build.py"
    - "tests/classificacao.yaml"

key-decisions:
  - "A distincao alta vs nao_avaliada exige saber se o check TINHA insumo (o retorno None conflaciona 'limpo' com 'sem insumo'); resolvida com predicados _avaliavel_sanNN leves que espelham os guards dos checks, sem alterar as assinaturas dos 5 checks (que os testes 08-04 chamam direto)"
  - "O contador de quedas no try/except e exposto via param opcional _diagnostico (dict), nao via atributo ad-hoc no CompanyData; producao chama aplicar_sanidade(c) e ignora"
  - "A chamada entra em montar_empresa (import + 1 linha), zero linha de calculo tocada — este plano NAO conserta dado"

requirements-completed: [SAN-01, SAN-02, SAN-03, SAN-04, SAN-05, SAN-06]

# Metrics
duration: 20min
completed: 2026-07-15
---

# Phase 8 Plan 05: aplicar_sanidade Ligado ao Pipeline e Provado por Execução Summary

**`aplicar_sanidade(c)` costura os 5 checks numa síntese never-raise: acumula `c.avisos` e deriva `c.confianca` numa escala discreta de 4 rótulos (baixa/media/alta/nao_avaliada — nunca um score por ticker), com cada check numa rede `try/except` cujas quedas são CONTADAS (0 sobre os 104), não silenciadas. `montar_empresa` passa a chamá-lo como PONTO ÚNICO — e a chamada é provada por execução (D-04): um teste roda o pipeline real offline e apagar a linha `aplicar_sanidade(c)` fica vermelho na hora — evasão RODADA e vista, não declarada. Zero conserto de dado; nada muda na tela.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-15
- **Tasks:** 2
- **Files:** 1 criado + 3 modificados

## Accomplishments

- **`aplicar_sanidade(c)`** roda os 5 checks, acumula `c.avisos` (lista, sem dedupe — um `num_acoes` quebrado acende SAN-01/03/05 ao mesmo tempo, e isso é correto, R-06) e deriva `c.confianca`. Idempotente (reinicia `c.avisos`), devolve `c` para encadear.
- **Never-raise estrutural (SAN-06):** cada check dentro de `try/except Exception` → "não avaliável" para aquele check, nunca propaga. Medido sobre os **104** tickers do snapshot: **0 exceções, 0 quedas no `except`** — uma exceção engolida seria uma detecção perdida em silêncio, então o contador de quedas exige ZERO, não só ausência de propagação.
- **Confiança discreta de 4 rótulos (D-13):** `baixa` (flag de escala SAN-01/02), `media` (só base SAN-03/04/05), `alta` (nenhuma flag E pelo menos um check avaliado), `nao_avaliada` (nenhum insumo — não avaliável ≠ limpo, D-03). Distribuição medida nos 104: 31 baixa / 31 media / 42 alta. Sem score numérico (verificado por `grep`).
- **Chamada única no pipeline (D-02/D-04):** `montar_empresa` chama `aplicar_sanidade(c)` logo antes do `return` — import + 1 linha, **nenhuma linha de cálculo tocada** (`contagem_cvm`/`_fator_unit`/`c.num_acoes`/`c.dividendos` byte a byte iguais).
- **A prova por execução, RODADA:** comentei `aplicar_sanidade(c)` em `build.py`, rodei `pytest -k sanidade_e_chamada` e **vi vermelho** (`assert 'nao_avaliada' != 'nao_avaliada'`); descomentei e ficou verde. Guarda que não é exercitada é guarda fantasma — a evasão foi vista, não declarada.
- **Casos vivos:** MRFG3 (404 no Yahoo) → SAN-01 **incomputável** (ausente de `c.avisos`), mas SAN-04 (100% CVM) **presente**; CSNA3 (sinal invertido) **acende SAN-04** (o `_bucket` não estourou, o `try/except` não engoliu); GOAU4 (escala quebrada) roda em `report.analisar_acao` e **produz resposta** sem levantar.
- **Suíte:** `455 passed, 1 skipped, 38 deselected, 2 xfailed, 0 failed`; BLIND-04a verde (zero constante de nível nos testes que citam ticker).

## Task Commits

1. **Task 1: aplicar_sanidade + agregação discreta de c.confianca** — `b5de9c8` (feat)
2. **Task 2: liga no pipeline + prova por execução (D-04) + never-raise 104 (SAN-06)** — `1ced50b` (feat)

## Files Created/Modified

- `src/analista/core/sanidade.py` — `aplicar_sanidade` + `_CHECKS_ESCALA`/`_ROTULOS_CONFIANCA` + 5 predicados `_avaliavel_sanNN` + a tabela `_CHECKS` (check pareado com predicado). Docstring declara: veredito interno (D-14), escala discreta (D-13), never-raise com quedas contadas.
- `src/analista/ingest/build.py` — import `from ..core import sanidade` + a chamada única `sanidade.aplicar_sanidade(c)` antes do `return c`. Nada mais.
- `tests/test_sanidade_pipeline.py` — 6 testes `contrato`: a prova D-04 (pipeline real offline), never-raise sobre os 104 (com contador de quedas == 0), MRFG3 (SAN-01 ausente / SAN-04 presente), CSNA3 (sinal invertido acende SAN-04), engine roda em ticker sujo. Asserts de pertinência; literais numéricos (ano-base/janela) vivem em helper sem assert, longe do detector BLIND-04a.
- `tests/classificacao.yaml` — 5 entradas `contrato` (08-05).

## Decisions Made

- **Predicados `_avaliavel_sanNN` para a distinção `alta` vs `nao_avaliada`.** O retorno `None` dos checks conflaciona "avaliado e limpo" com "sem insumo" — as duas viram None. Para o D-13 distinguir confiança `alta` (avaliado, sem flag) de `nao_avaliada` (nada avaliável), `aplicar_sanidade` consulta predicados leves que espelham os guards de entrada de cada check. Alternativa descartada: mudar a assinatura dos 5 checks para sinalizar avaliabilidade — quebraria os testes 08-04 que os chamam direto e retornam Aviso/None/[].
- **O contador de quedas via `_diagnostico: Optional[dict]`, não via atributo no `CompanyData`.** O teste passa um dict e inspeciona `quedas`/`checks_com_queda`; a chamada de produção `aplicar_sanidade(c)` ignora o parâmetro. Evita poluir o dataclass com um campo de diagnóstico interno.
- **Confiança rebaixa pela flag mais grave (escala > base).** SAN-01/02 quebram a ordem de grandeza (tudo que depende de `num_acoes` fica sem sentido) → `baixa`, mesmo que também haja flags de base. É a leitura conservadora correta.

## Deviations from Plan

**None — plano executado exatamente como escrito.** Os dois testes de casos vivos foram ajustados ao nome fiel à realidade medida: o MRFG3 acende SAN-02 além do SAN-04 (o `num_acoes` da CVM salta), então o teste afirma o que o plano descreve literalmente — SAN-01 **ausente** (incomputável sem market_cap) e SAN-04 **presente** — sem uma alegação genérica de "não flagado por escala" que a medição contradiria. Nenhum assert do plano foi afrouxado; nenhuma constante de nível entrou.

## Issues Encountered

Nenhum. O snapshot congelado (08-03) e o cache CVM local (2015-2025) tornaram o teste do D-04 100% offline; `report.analisar_acao` roda sobre os `CompanyData` sujos reconstruídos sem levantar.

## Known Stubs

None. `aplicar_sanidade` consome os 5 checks reais e o `CompanyData` real; os predicados de avaliabilidade leem os mesmos insumos dos checks. Nada de placeholder — a confiança sai de flags reais medidas sobre dado real.

## Threat Flags

Nenhuma superfície nova além do `<threat_model>` do plano (T-08-13 esquecimento silencioso — mitigado pela prova D-04 rodada; T-08-14 check estourando derruba o pipeline — mitigado pelo never-raise sobre os 104; T-08-15 expor "dado suspeito" ao cliente — mitigado por D-14: veredito interno, nada na tela).

## Next Phase Readiness

- **`c.confianca` está disponível para o relatório CLI (plano 08-06):** cada `CompanyData` do pipeline real agora carrega `avisos` + `confianca`. O 08-06 lê isso e imprime o diagnóstico por ticker.
- **O teste de regressão da Fase 9 está armado de ponta a ponta:** quando a Fase 9 consertar `num_acoes`/`_fator_unit`/JCP, as flags têm que APAGAR ticker a ticker, e a confiança de 31 tickers `baixa` tem que subir. `test_nenhum_check_levanta...` continua a rede de segurança never-raise.
- **A apresentação ao usuário (selo de confiança) é decisão da Fase 13 (D-14)** — com o dado já consertado, sem expor 41/104 como "suspeito" a cliente pagante no interim.

## Self-Check: PASSED

- Arquivos: `tests/test_sanidade_pipeline.py` (FOUND); `src/analista/core/sanidade.py` e `src/analista/ingest/build.py` modificados (FOUND).
- Commits: `b5de9c8` (Task 1), `1ced50b` (Task 2) — ambos FOUND no histórico.
- Critérios: `def aplicar_sanidade` = 1; `raise ` não-comentário = 0; rótulos ≥ 4; score/0-100/pontuacao = 0; `aplicar_sanidade(c)` em build.py = 1; diff de build.py sem linhas de cálculo; `grep test_sanidade_pipeline classificacao.yaml` = 5; evasão RODADA (vermelho visto, verde restaurado); `pytest` inteiro **455 passed, 0 failed**.

---
*Phase: 08-sanidade-dos-dados-san*
*Completed: 2026-07-15*
