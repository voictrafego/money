---
phase: 06-integra-o-na-engine-composite-alerta-cli
verified: 2026-06-26T00:00:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Phase 6: Integração na Engine — Composite + Alerta + CLI — Verification Report

**Phase Goal:** Os sinais técnicos passam a viver em `AnaliseAcao` via `analisar_acao`, com um resumo de timing composite que lê (sem recalcular) o veredito DDM numa matriz fundamento×técnico, um alerta de reverificação ao rompimento de tendência e a base temporal diária/semanal dos alertas — tudo espelhado na CLI.
**Verified:** 2026-06-26
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `analisar_acao` popula `a.sinais` via `indicators.calcular` — ponto único CLI/UI (TIMING-01) | VERIFIED | `report.py:159` — `a.sinais = indicators.calcular(ohlc, cfg)`; import em linha 15 |
| 2 | Composite classifica timing por árvore MM200-direção/ADX-força em 3 estados macro, com RSI/MACD como matiz fino que nunca muda o estado (TIMING-01 / D-01/D-02/D-03) | VERIFIED | `report.py:163-189` — 4 ramos exatos; matiz fino só refina `timing_resumo`, não altera `timing_estado` |
| 3 | Base temporal default "semanal" faz resample W-FRI antes dos indicadores; "diario" passa o frame direto (TIMING-04 / D-10) | VERIFIED | `report.py:152-157` — `cfg.get("indicadores", {}).get("base_temporal", "semanal")`; `resample("W-FRI").agg(...)` |
| 4 | `config.yaml` contém `base_temporal: "semanal"` no bloco `indicadores` (TIMING-04) | VERIFIED | `config.yaml:84` — `base_temporal: "semanal"` presente com comentário canônico |
| 5 | Golden test trava o caso-limite acima-da-MM200-com-ADX<20 → "sem_tendencia" (TEST-06 / D-02) | VERIFIED | `tests/test_report.py:55-70` — `test_composite_acima_mm200_adx_fraco_eh_sem_tendencia` passa; pré-condições assertadas |
| 6 | `matriz_leitura` cruza o veredito DDM com o estado técnico, fundamento-primeiro, células-âncora D-05/D-06 verbatim (TIMING-02) | VERIFIED | `report.py:206-236` — dict explícito 9 células; D-05 e D-06 verificadas verbatim em runtime |
| 7 | `alerta_reverificacao` dispara no OR dos três gatilhos de baixa, mensagem consolidada, nunca "venda" (TIMING-03 / D-07/D-08/D-09) | VERIFIED | `report.py:255-273` — OR-of-three em `_alerta_reverificacao`; "venda" só dentro da negação |
| 8 | `relatorio_markdown` imprime seção "Sinais técnicos (consultivos)" com fallback gracioso de histórico curto (CLI-01) | VERIFIED | `report.py:375-390` — seção presente; fallback itálico quando sinais degradados |
| 9 | Os 64 golden tests de valuation existentes continuam verdes (TEST-07 invariante) | VERIFIED | Suíte completa: 103/103 verde — 11 novos testes de report + 92 preexistentes |

**Score:** 9/9 observações verificadas (6/6 must-haves dos planos cobertos)

---

## Required Artifacts

| Artifact | Esperado | Status | Detalhes |
|----------|----------|--------|----------|
| `src/analista/report/report.py` | 5 campos em `AnaliseAcao`; import `indicators`; resample W-FRI + árvore composite em `analisar_acao`; helpers puros `_matriz_leitura` / `_alerta_reverificacao`; seção CLI em `relatorio_markdown` | VERIFIED | Todos os elementos presentes nas linhas exatas; defaults corretos confirmados em runtime |
| `config.yaml` | Chave `base_temporal: "semanal"` no bloco `indicadores` | VERIFIED | Linha 84 — presente com comentário explicativo |
| `tests/test_report.py` | 11 golden tests cobrindo: TEST-06 (composite tiebreak), resample W-FRI, células-âncora D-05/D-06 verbatim, alerta OR-of-three, independência do veredito, CLI normal e degradada | VERIFIED | 11 testes, todos passando em 0.65 s |

---

## Key Link Verification

| De | Para | Via | Status | Detalhes |
|----|------|-----|--------|----------|
| `report.py:analisar_acao` | `indicators.calcular` | `c.ohlc_ajustado` (resampleado quando semanal) | WIRED | Linha 159; import linha 15 |
| `report.py:analisar_acao` | `a.sinais.tendencia.posicao_mm200` + `a.sinais.forca.forca_adx` | Rótulos discretos já classificados (não relê o float do ADX) | WIRED | Linhas 163-164; sem releitura de `.adx.iloc[-1]` |
| `report.py:analisar_acao` | `a.veredito` (token líder) × `a.timing_estado` | `_matriz_leitura(a.veredito, a.timing_estado)` via `_veredito_token` + dict `_MATRIZ_LEITURA` | WIRED | Linha 194; helper puro linha 247 |
| `report.py:analisar_acao` | `a.sinais.tendencia.posicao_mm200`, `.cruzamento`, `.canais.rompimento_donchian` | OR dos três gatilhos em `_alerta_reverificacao` | WIRED | Linha 195; helper puro linhas 255-273 |
| `report.py:relatorio_markdown` | `a.timing_resumo` / `a.matriz_leitura` / `a.alerta_reverificacao` | Seção "Sinais técnicos (consultivos)" via `L.append` | WIRED | Linhas 375-390; fallback quando `sinais is None` |

---

## Requirements Coverage

| Requirement | Plano | Descrição | Status | Evidência |
|-------------|-------|-----------|--------|-----------|
| TIMING-01 | 06-01 | Resumo de timing composite em linguagem natural (3 estados macro) | SATISFIED | `timing_estado` + `timing_resumo` preenchidos em `analisar_acao`; 3 ramos + matiz |
| TIMING-02 | 06-02 | Matriz fundamento×técnico sem recalcular o fundamento | SATISFIED | `_matriz_leitura` read-only; 9 células mapeadas; âncoras D-05/D-06 verbatim |
| TIMING-03 | 06-02 | Alerta de reverificação ao rompimento, voz nunca-venda | SATISFIED | `_alerta_reverificacao` OR-of-three; "venda" só na negação; `None` quando sem gatilho |
| TIMING-04 | 06-01 | Base temporal diário/semanal em cfg; default semanal com resample W-FRI | SATISFIED | `config.yaml:84`; `report.py:152-157` |
| CLI-01 | 06-02 | CLI imprime seção "Sinais técnicos (consultivos)" com fallback gracioso | SATISFIED | `report.py:375-390`; confirmado por golden `test_cli_secao_sinais_tecnicos_*` |
| TEST-06 | 06-01 | Golden trava o desempate composite acima-da-MM200-com-ADX<20 | SATISFIED | `tests/test_report.py:55-70`; pré-condições e estado afirmados e passando |

---

## Anti-Patterns Found

| Arquivo | Linha | Padrão | Severidade | Impacto |
|---------|-------|--------|------------|---------|
| `src/analista/report/report.py` | 378 | `a.timing_estado == ""` é condição morta (timing_estado nunca é `""` após `analisar_acao`) | Info (IN-01 da revisão) | Nenhum comportamento incorreto; condição inerte |
| `src/analista/report/report.py` | 386 | `L.append(a.matriz_leitura)` insere linha em branco quando veredito DDM é `""` | Info (IN-02 da revisão) | Linha vazia espúria no markdown, sem falsa leitura |

Nenhum marcador TBD / FIXME / XXX encontrado nos arquivos modificados pela fase.

---

## Nota sobre CR-01 (06-REVIEW.md)

O code review identificou uma **assimetria de degradação** (CR-01) que o usuário solicitou avaliar:

**O que é:** Quando `forca_adx == "indisponivel"` com `posicao_mm200 != "indisponivel"` (série muito achatada com 200+ barras), o bloco degradado define `timing_estado = "sem_tendencia"` e `timing_resumo = ""` corretamente, mas `_matriz_leitura` é chamada logo após com o veredito DDM disponível e `"sem_tendencia"` — produzindo um `matriz_leitura` não-vazio. O guard da CLI (`a.timing_estado == ""`) é condição morta e `posicao_mm200 == "indisponivel"` não pega esse sub-caso, então a seção CLI exibe `**Timing de entrada:** ` (frase vazia) seguida de `matriz_leitura` preenchida.

**É um bloqueador da meta da fase?** Não. A meta é implementar os sinais técnicos em `AnaliseAcao` com composite + matriz + alerta + CLI espelhada — todos implementados e funcionando nos caminhos principais. CR-01 é uma inconsistência no sub-caminho de degradação de um caso de borda raro (série com 200+ barras acima da MM200 mas ADX computacionalmente indisponível, que exigiria variação TR nula por pelo menos ~14 barras).

**Severidade para esta fase:** Advisory — nenhum requisito de aceite da Phase 6 exige que `matriz_leitura == ""` quando `forca_adx == "indisponivel"`. O comportamento é internamente inconsistente mas não silencioso: `timing_resumo = ""` já indica ausência de leitura técnica a quem consome o campo.

**Ação recomendada antes da Phase 7:** Corrigir o ramo degradado para também zerar `a.matriz_leitura = ""` (1 linha), e substituir o guard da CLI por `not a.timing_resumo` (cobre todos os casos degradados). WR-01 (guard de DatetimeIndex antes do resample) e WR-02 (golden adicional do sub-caso `forca_adx == "indisponivel"`) são recomendações paralelas da revisão de menor prioridade.

---

## Human Verification Required

Nenhum item requer verificação humana — todos os comportamentos verificáveis programaticamente foram confirmados pela suíte de testes e pelas inspeções de código acima.

---

## Gaps Summary

Nenhum gap identificado. Todos os must-haves dos planos 01 e 02 e todos os requirements da fase (TIMING-01/02/03/04, CLI-01, TEST-06) estão implementados, conectados e travados por golden tests verdes.

CR-01 e WR-01/WR-02 (06-REVIEW.md) são achados advisory do code review — não bloqueiam a meta da fase. Recomendado endereçar antes que a Phase 7 (UI) consuma os campos `matriz_leitura` / `alerta_reverificacao` em modo read-only.

---

_Verified: 2026-06-26_
_Verifier: Claude (gsd-verifier)_
