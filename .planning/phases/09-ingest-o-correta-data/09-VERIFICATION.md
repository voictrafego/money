---
phase: 09-ingest-o-correta-data
verified: 2026-07-15T19:30:00Z
status: passed
score: 10/10 must-haves verified
overrides_applied: 0
---

# Phase 09: Ingestão correta (DATA) Verification Report

**Phase Goal:** Curar a Doença 2 (dispersão). Os asserts da Fase 8 viram verde ticker a ticker —
progresso mensurável, não declarado. Regenerar o snapshot de teste.
**Verified:** 2026-07-15T19:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Os asserts da Fase 8 param de disparar nos tickers-alvo (JCP capturado; lucro/PL na base do controlador; duplo ajuste de split some) | ✓ VERIFIED | `tests/test_sanidade_baseline.py::test_os_alvos_consertados_sumiram_de_hoje` passa — os 9 pares nomeados (BRSR6/SAN-03, GOAU4·CGRA4/SAN-01, ITUB4·BRSR6/SAN-02, CSNA3·ALUP11·EQTL3·MRFG3/SAN-04) estão no baseline sujo e ausentes de `pares_hoje` (medido sobre o snapshot limpo, não declarado). `tests/test_ingest_split.py` (3 asserts) prova por execução (regressão simulada → RED) que o double-count de split não existe na série de valuation. |
| 2 | num_acoes deixa de ser derivado de lucro/LPA com bases cruzadas; fallback usa impliedSharesOutstanding (ON+PN), não sharesOutstanding | ✓ VERIFIED | `src/analista/ingest/build.py:172-239` — fonte é `cvm.contagem_oficial_do_ano` (composicao_capital), escala detectada por ano (`_escala_por_ano`) e internamente à série quando sem âncora (`_alinhar_escala_interna`, com no-shrink guard). Fallback = `dm.implied_shares_outstanding` (build.py:237-239), nunca `dm.num_acoes`. `tests/test_ingest_unit.py` (4 goldens do método antigo LL/LPA) foi DELETADO — não há mais golden que codifique o método removido. |
| 3 | O DY declara sua base (bruto explícito, sem imposto especulativo) | ✓ VERIFIED | `presentation.header_dy` declara "**bruto**" nos dois caminhos (recorrente e fallback) — grep confirma nas linhas 66 e 79. `glossario.py` declara "bruta" no verbete `"dy"` (linha 33) e na linha do DY em `"tab_multiplos"` (linha 59). `multiples.dividend_yield` intocado (nenhum imposto calculado). `tests/test_dy_base.py` (3 asserts) trava a declaração; suíte passa. |
| 4 | O snapshot de teste é regenerado e passa nos asserts da Fase 8 — o ITUB4 de 2019 tem bilhões de ações, não milhões | ✓ VERIFIED | `tests/fixtures/snapshot_sanidade_limpo_2026-07-15.yaml` existe (gerado por `scripts/capturar_snapshot_limpo.py`, live, a partir do código consertado). Medido diretamente: `ITUB4.num_acoes[2019] = 11.021.872.542` (≈11 bi, via fallback `implied` porque `composicao_capital` só existe a partir de ~2020 — origem carimbada `yahoo_fallback`). O snapshot SUJO (`snapshot_sanidade_2026-07-14.yaml`) e o BASELINE (`baseline_sanidade.yaml`) permanecem intocados desde a Fase 8 (`git log` mostra último commit em `f72a1c7`/`5f969ef`, nenhum na Fase 9). |

**Score:** 4/4 truths verified

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| DATA-01 | 09-01 | JCP capturado em `c.dividendos` (filtro amplo dentro da CVM) | ✓ SATISFIED | `cvm.py:376` — `dividendos_distribuidos` sai de `_distribuicoes_proventos_amplo`. Medido no snapshot limpo: `BRSR6.dividendos == BRSR6.proventos_filtro_amplo` em todos os 10 anos (JCP presente). WR-01 (regex sobre-amplo) foi corrigido no mesmo escopo (commit `aad298c`, ancorado em "capital proprio") — medição offline: 0 mudança nos 4 bancos. |
| DATA-02 | 09-01 | lucro/PL na base do controlador com fallback | ✓ SATISFIED | `build.py:187-195` — gate único em `lucro_controlador`; com controlador, LL=controlador e PL=consolidado−minoritários; sem controlador, ambos ficam no consolidado, minoritários não subtraídos. Nunca base cruzada. |
| DATA-03 | 09-02 | num_acoes = contagem oficial CVM, não LL/LPA; fallback = implied ON+PN | ✓ SATISFIED | `cvm.py:152-184` (`contagem_oficial_do_ano`, join CNPJ→CD_CVM) + `build.py:172-239` (escala por ano/interna, fallback implied). `tests/test_ingest_unit.py` (4 goldens do método antigo) deletado no mesmo commit que a troca de fonte. |
| DATA-04 | 09-03 | Degrau artificial de split (~13% ITUB4) removido/provado ausente | ✓ SATISFIED | Spike `.planning/spikes/data-04-degrau-split.md` mede e conclui que o degrau já não existe (firewall Fases 3-4 + DATA-03); `tests/test_ingest_split.py` (3 testes) trava a ausência, provado RED-able por regressão simulada (documentado no SUMMARY). |
| DATA-05 | 09-04 | DY declara base bruta | ✓ SATISFIED | `presentation.py` + `glossario.py` declaram "bruto"/"bruta"; `tests/test_dy_base.py` passa; `multiples.py` intocado. |
| DATA-06 | 09-05 | Snapshot regenerado; monotonicidade encolhe (não tautologia) | ✓ SATISFIED | Snapshot limpo novo + loader desacoplado (`CAMINHO_SNAPSHOT_LIMPO`) + ratchet reformulado (`pares_hoje ⊆ baseline ∪ aceitos`) provado RED-able; accept-list versionada (9 pares + 2 buckets) com justificativa categórica, sem ticker+número (BLIND-04a-safe, confirmado por leitura do YAML e pelo teste `test_accept_list_e_disjunta_e_sem_reais`). |

**Nenhum requisito órfão** — REQUIREMENTS.md mapeia exatamente DATA-01..06 à Fase 9, e todos os 6 aparecem no `requirements:` de algum PLAN (09-01: DATA-01/02; 09-02: DATA-03; 09-03: DATA-04; 09-04: DATA-05; 09-05: DATA-06).

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/analista/ingest/cvm.py` | filtro amplo + composicao_capital | ✓ VERIFIED | `_distribuicoes_proventos_amplo` (ancorada, WR-01 resolvido), `contagem_oficial_do_ano`, `_mapa_cnpj_por_cd_cvm`, `_composicao_capital` presentes e testados |
| `src/analista/ingest/build.py` | gate controlador + num_acoes oficial + escala | ✓ VERIFIED | Gate único (linhas 187-195), `_escala_por_ano`/`_alinhar_escala_interna` com no-shrink guard (WR-03 resolvido) |
| `src/analista/report/presentation.py` | header_dy declara bruto | ✓ VERIFIED | 2 ocorrências de "bruto" nos dois caminhos |
| `src/analista/glossario.py` | verbete DY declara bruta | ✓ VERIFIED | 2 ocorrências ("dy" e "tab_multiplos") |
| `tests/test_dy_base.py` | contrato DY bruto | ✓ VERIFIED | 3 asserts, classificado em classificacao.yaml |
| `.planning/spikes/data-04-degrau-split.md` | medição do degrau | ✓ VERIFIED | Existe, documenta site real + veredito medido |
| `tests/test_ingest_split.py` | guarda de regressão do split | ✓ VERIFIED | 3 testes, provados RED-able por execução (SUMMARY) |
| `scripts/capturar_snapshot_limpo.py` | captura do snapshot limpo | ✓ VERIFIED | Existe, reusa a forma do script sujo, live |
| `tests/fixtures/snapshot_sanidade_limpo_2026-07-15.yaml` | dado limpo congelado | ✓ VERIFIED | Existe, 104 tickers, ITUB4 2019 em bilhões |
| `tests/helpers_sanidade.py` | loader desacoplado | ✓ VERIFIED | `CAMINHO_SNAPSHOT_LIMPO` definido e separado do sujo |
| `tests/fixtures/pares_aceitos_sanidade.yaml` | accept-list versionada | ✓ VERIFIED | 9 pares + 2 buckets, motivos categóricos sem ticker/número |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `cvm.fundamentos_do_ano["dividendos_distribuidos"]` | `c.dividendos` | `dist_cvm` (build.py) | ✓ WIRED | Medido: `BRSR6.dividendos == BRSR6.proventos_filtro_amplo` no snapshot limpo (JCP fluindo) |
| `build.montar_empresa` | `c.lucro_liquido`/`c.patrimonio_liquido` | gate único `lucro_controlador` | ✓ WIRED | Código lido linha a linha (build.py:187-195); nunca cruza bases |
| `cvm.contagem_oficial_do_ano` | `build.num_acoes` | escala por ano + fallback implied | ✓ WIRED | Medido: ITUB4 2019 = 11 bi (fallback); 2020+ = origem "cvm" |
| `_pares_e_buckets_de_hoje` (test_sanidade_baseline.py) | snapshot LIMPO | `hs.carregar_snapshot_sanidade(path=hs.CAMINHO_SNAPSHOT_LIMPO)` | ✓ WIRED | Confirmado por leitura do código (linha 91) e pelos 9 pares desaparecendo em `test_os_alvos_consertados_sumiram_de_hoje` |
| `test_sanidade_checks.py` | snapshot SUJO | `carregar_snapshot_sanidade()` default | ✓ WIRED | Não modificado nesta fase; suíte segue verde no sujo (detectores continuam disparando) |
| `presentation.header_dy` | usuário | `help` com "bruto" | ✓ WIRED | Grep + teste de contrato passando |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Suíte verde default (regra do CLAUDE.md v2.4) | `.venv/bin/python -m pytest -q` | `467 passed, 1 skipped, 34 deselected, 2 xfailed, 0 failed` | ✓ PASS |
| Suíte verde `-m ""` (tudo, incl. golden quarentenado) | `.venv/bin/python -m pytest -m "" -q` | `500 passed, 2 skipped, 2 xfailed, 0 failed` | ✓ PASS |
| `golden_nivel` sob demanda, sem órfãos | `.venv/bin/python -m pytest -m golden_nivel -q` | `34 passed, 0 failed` (sem "CLASSIFICACAO ORFA" na saída) | ✓ PASS |
| Orçamento de 3 knobs intocado | `git diff 810e2e6 HEAD -- config.yaml calibracao.lock.yaml` | vazio | ✓ PASS |
| Snapshot sujo/baseline preservados | `git log --oneline -- tests/fixtures/snapshot_sanidade_2026-07-14.yaml tests/fixtures/baseline_sanidade.yaml` | último commit é da Fase 8 (`f72a1c7`/`5f969ef`), nada na Fase 9 | ✓ PASS |
| `snapshot_bancos` não regenerado (decisão travada p/ Fase 10) | `git log --oneline -- tests/fixtures/snapshot_bancos_2026-07-12.yaml` | último commit é da Fase 5 (`5aa5bac`) | ✓ PASS |
| ITUB4 2019 em bilhões, não milhões | leitura direta do YAML limpo | `11.021.872.542` | ✓ PASS |
| BRSR6 dividendos == proventos_filtro_amplo (JCP fluindo) | leitura direta do YAML limpo | idênticos em todos os 10 anos | ✓ PASS |
| Commits das 5 tasks + 2 fixes de review existem | `git log --oneline \| grep <hash>` | todos os 16 hashes declarados nos SUMMARYs encontrados | ✓ PASS |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `src/analista/ingest/build.py` | 241-251 | Comentário `BUG-JCP` afirma "c.dividendos continua sujo, de propósito" — desatualizado após o DATA-01 mudar a fonte de `dividendos_distribuidos` para o filtro amplo em `cvm.py`. O comportamento medido é correto (BRSR6.dividendos == proventos_filtro_amplo), mas o comentário contradiz o código atual. | ℹ️ INFO | Não afeta o goal (comportamento correto, medido); risco de confundir manutenção futura — recomendável atualizar o comentário em um commit de limpeza |
| `src/analista/ingest/cvm.py` | 116-118 (WR-04) | `_mapa_cnpj_por_cd_cvm` se auto-desabilita silenciosamente se `cad_cia_aberta.csv` faltar (clone novo) — todo o universo cai no fallback `impliedSharesOutstanding` sem log/aviso. | ⚠️ WARNING (aberto, documentado no REVIEW) | Não bloqueia o goal desta fase (medido: arquivo presente no ambiente atual, universo usa `cvm` como origem); é dívida técnica rastreada, não um defeito da Fase 9 |
| `src/analista/ingest/cvm.py` | 130-149 (WR-05) | `_composicao_capital` não filtra `ORDEM_EXERC == "ÚLTIMO"` como `_ler_demonstracao` faz; desambiguação depende só de sort+`iloc[-1]` | ⚠️ WARNING (aberto, documentado no REVIEW) | Risco teórico de linha errada se o CSV trouxer múltiplos exercícios; não observado no universo atual (suíte verde, snapshot medido correto) |
| `src/analista/ingest/build.py` | 79 (WR-02) | Heurística de escala confunde variação societária real 31,6×-316× com troca de unidade — investigado e a correção sugerida REGREDE 4 valores reais (ASAI3/ENEV3/KEPL3); deixado OPEN por decisão de design, não aplicado | ℹ️ INFO (investigado, decisão documentada) | Buraco teórico não alcançado no universo atual dos 104 tickers (medido); tratado como follow-up de design, não como blocker desta fase, per decisão registrada no REVIEW e autorizada |

Nenhum marcador de dívida não referenciado (`TBD`/`FIXME`/`XXX`) foi encontrado nos arquivos modificados pela fase — grep limpo em todos os 11 arquivos de produção/teste/script revisados.

### Desvios do Plano (autorizados pelo usuário, não são defeitos)

Dois desvios documentados nos SUMMARYs foram verificados como intencionais e coerentes com a
doutrina do projeto ("golden que codifica o método removido: DELETE, não atualize"):

1. **09-01**: dois testes-diagnóstico da Fase 8 (`test_o_filtro_estreito_da_cvm_perde_o_jcp`,
   `test_montar_empresa_carimba_o_lucro_do_controlador`) re-apontados aos insumos crus, pois
   asseriam a relação SUJA através de `c.dividendos`/`c.lucro_liquido` — que o próprio conserto
   move. Verificado: `tests/test_sanidade_insumos.py` contém os asserts re-apontados; suíte verde.
2. **09-02**: `tests/test_ingest_unit.py` (4 goldens do método `LL/LPA`) DELETADO, com as 4
   entradas correspondentes removidas de `classificacao.yaml` no mesmo commit. Verificado:
   arquivo ausente no repositório; `-m golden_nivel` roda sem "CLASSIFICACAO ORFA".
3. **09-05**: o invariante de subconjunto puro do DATA-06 foi reformulado para um ratchet com
   accept-list versionada (documentado acima). Verificado como load-bearing: `test_accept_list_e_disjunta_e_sem_reais`
   garante que a accept-list não pode silenciar um alvo do ROADMAP nem citar ticker/número no
   motivo, e o SUMMARY documenta a prova RED-able por injeção (par/bucket fake → suíte vermelha).

### Human Verification Required

Nenhum item requer verificação humana. A Fase 9 é inteiramente backend/dados (ingestão CVM/Yahoo
+ rótulos de texto), sem UI interativa nova além de dois textos estáticos (`help`/glossário) já
confirmados por grep e por teste de contrato automatizado.

### Gaps Summary

Nenhum gap bloqueante. Os 4 critérios de sucesso do ROADMAP e os 6 requisitos DATA-01..06 estão
verificados no código, não apenas declarados nos SUMMARYs. A suíte está verde exatamente na forma
que o CLAUDE.md exige (0 failed no default; `-m ""` limpo; `-m golden_nivel` sem órfãos). O
orçamento de 3 knobs (`config.yaml`/`calibracao.lock.yaml`) está intocado desde antes da Fase 9. O
snapshot sujo, o baseline e o `snapshot_bancos` permanecem intactos, como a decisão travada exigia.

Os únicos itens abertos (WR-02 investigado-e-rejeitado, WR-04, WR-05, e o comentário stale em
`build.py:241`) são dívida técnica documentada e não impedem o goal desta fase — nenhum é
observável no universo atual dos 104 tickers (medido, não suposto), e ficam registrados como
follow-up para a Fase 10+ (WR-02/04/05 já constam no `09-REVIEW.md` como itens abertos).

---

_Verified: 2026-07-15T19:30:00Z_
_Verifier: Claude (gsd-verifier)_
