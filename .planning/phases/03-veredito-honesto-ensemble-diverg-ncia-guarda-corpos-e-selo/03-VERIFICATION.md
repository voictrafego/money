---
phase: 03-veredito-honesto-ensemble-diverg-ncia-guarda-corpos-e-selo
verified: 2026-07-12T13:01:22Z
status: gaps_found
score: 4/6 must-haves verified (2 partial/failed on independently-confirmed defects)
overrides_applied: 0
gaps:
  - truth: "O selo/veredito nunca apresenta silenciosamente a banda do DDM sob o rótulo do motor do arquétipo, sem aviso (Core Value: números fiéis ao método e consistentes entre si)"
    status: failed
    reason: >
      CR-01 do code review (03-REVIEW.md) confirmado por leitura direta do código: em
      `report.py:495` o bloco do ensemble só roda `if a.motor != "ddm" and a.intrinseco_motor
      is not None:`. Quando o motor do arquétipo degrada para None (RIM/DCF/NAV/normalizado
      podem legitimamente devolver None sob dado degenerado) mas a banda DDM (vmin/vmax)
      sobrevive, não existe ramo `else`/`elif` — o código cai direto no bloco de veredito de
      preço em `report.py:520` (`if a.vmin is not None and a.vmax is not None and
      a.preco_atual:`), que NÃO verifica `a.banda_do_motor`. O veredito SUB/NO INTERVALO/SOBRE
      resultante vem 100% do DDM, mas `a.banda_do_motor` fica False, então: (1) o alerta "DDM é
      lente conservadora" (linha 548) NÃO dispara; (2) o alerta de degradação do motor (linha
      567) também NÃO dispara (está no `elif` que exige vmin/vmax None). Nenhum sinal informa
      ao usuário que o motor falhou. `app.py:982-988` rotula a métrica
      `f"Intrínseco ({a.motor_rotulo or _motor})"` usando só `a.motor` (não `a.banda_do_motor`),
      então exibe, por exemplo, "Intrínseco (RIM)" com uma faixa que é inteiramente o DDM.
      `report.py:880-889` também rotula o bloco DDM como "lente conservadora — não é o motor
      deste arquétipo" mesmo quando é a ÚNICA fonte da faixa exibida. Confirmado via leitura de
      código (não apenas a alegação do reviewer); path é alcançável e SEM disclaimer.
    artifacts:
      - path: "src/analista/report/report.py"
        issue: "Linhas 495-511 (bloco ensemble) sem ramo else para motor None + banda DDM válida; linha 520 não checa a.banda_do_motor antes de montar o veredito de preço"
      - path: "app.py"
        issue: "Linhas 982-988: rótulo do intrínseco usa só a.motor (!= 'ddm'), não a.banda_do_motor — pode chamar uma faixa 100% DDM de 'Intrínseco (RIM)' sem aviso"
    missing:
      - "Ramo elif explícito em report.py: quando a.motor != 'ddm' e a.intrinseco_motor is None mas vmin/vmax (DDM) sobrevivem, marcar a.banda_do_motor=False e emitir alerta honesto de que a faixa exibida é do DDM, não do motor"
      - "app.py e relatorio_markdown devem derivar o rótulo/nota de a.banda_do_motor (não só de a.motor) para nunca rotular uma faixa 100% DDM com o nome de outro motor"
      - "Teste golden cobrindo motor None + DDM válido (caso hoje só coberto para motor None E DDM None simultaneamente, em test_ver01_motor_sem_banda_degrada_para_verificar)"
  - truth: "Em caso-fronteira, TODA a superfície (CLI e UI) assume a dúvida em voz alta — nenhum número específico é exibido como se fosse certo"
    status: partial
    reason: >
      WR-01 do code review confirmado por execução ao vivo: no caso fronteiriço (fixture
      `_fronteirico`), `a.veredito`/banner mostra corretamente "classificação incerta entre
      ciclica e crescimento... range R$ 9,08–22,68" (candidatos_intrinsecos = [9.08, 22.68]),
      mas `a.vmin/a.vmax` (usados pelo m2.metric "Intrínseco (<motor>)" em app.py:976-988)
      permanecem a banda do ENSEMBLE do arquétipo primário do VER-01 (4,41–9,08) — um range
      DIFERENTE do que a bandeira de incerteza anuncia. A mesma tela mostra dois números
      contraditórios: o metric card cravado (4,41–9,08) sob um rótulo de motor específico, e o
      banner de dúvida (9,08–22,68). Isso é exatamente "fingir certeza" no metric card enquanto
      o texto ao lado assume a dúvida — viola o espírito do objetivo da fase para a superfície
      Streamlit (VER-02/03-04 delimita escopo só de leitura, mas não trata esta inconsistência).
    artifacts:
      - path: "app.py"
        issue: "Linhas 976-988: m2.metric usa incondicionalmente a.vmin/a.vmax mesmo quando a.arquetipo_incerto é True, sem suprimir/substituir pelo a.veredito_range"
    missing:
      - "Gate no app.py: quando a.arquetipo_incerto, suprimir ou substituir o metric card do intrínseco pelo a.veredito_range (ou por '—'), evitando dois números conflitantes na mesma tela"
deferred: []
human_verification: []
---

# Phase 3: Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo — Verification Report

**Phase Goal:** Fechar o loop na agregação do veredito (hoje single-model BSD×DDM). O selo deve
consumir o motor DO ARQUÉTIPO classificado (não o DDM fixo), preservando o firewall
selo↛report. Rodar motor primário + ≥1 contraponto e, quando divergência > limiar (maior > 2×
menor), levantar bandeira de divergência com hipótese. Interpor guarda-corpos anti-aberração
antes de estampar "evitar" (SAN-01). Em caso-fronteira, assumir a dúvida em voz alta (range +
bandeira) em vez de fingir certeza.

**Verified:** 2026-07-12T13:01:22Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC#1 — ITUB4 não é mais estampado "evitar": selo consome motor RIM, DDM rebaixado a lente conservadora | ✓ VERIFIED | Executado ao vivo (não só via teste): `a.arquetipo='financeira'`, `a.motor='rim'`, `a.banda_do_motor=True`, `a.veredito='SOBREAVALIADA — ...'` (sem "Evitar"), `selo.rotulo='Boa, mas cara'`. Testes `test_capstone_itub4_sem_evitar_motor_rim_ddm_como_lente` e `test_san01_e2e_itub4_nao_estampa_evitar` verdes. |
| 2 | SC#2 — Motor×contraponto divergem >2× → range + bandeira de divergência com hipótese, não número único | ✓ VERIFIED | Executado ao vivo: ITUB4 produz `divergencia_ativa=True`, `divergencia_razao≈3.02`, `divergencia_hipotese='compounder subvalorizado pelo DDM...'`. `_HIPOTESE_DIVERGENCIA` dict presente (report.py:742) com chaves (arquétipo,sinal); renderizado em `relatorio_markdown` e em `app.py` (st.warning). |
| 3 | SC#3 — Todo veredito "evitar" passa por guarda-corpos; aberração (ROE>15% E corte payout>40%, pares degradável) é reetiquetada "DDM conservador demais..." mantendo o número | ✓ VERIFIED (com ressalva WR-02, ver Anti-Patterns) | `_guarda_san01` existe (report.py:107), chamado após a cadeia de veredito e antes de `montar_selo` (report.py:587). `config.yaml` tem `veredito.san01.{fator_pares,roe_min,corte_payout_min}`. Golden e2e `test_san01_e2e_itub4_nao_estampa_evitar` verde. Literal da SC#3 satisfeito — mas ver WR-02: o gate não verifica que o motor primário CONCORDA com a tese "DDM conservador demais", podendo reetiquetar uma sobreavaliação genuína (confirmado por leitura do código; ver seção Anti-Patterns). |
| 4 | SC#4 — Em caso-fronteira, veredito assume a dúvida (range+bandeira) em vez de selo cravado | ⚠️ PARTIAL | `report.py`/CLI: VERIFIED — `_veredito_fronteirico` roda, `a.veredito` começa com VERIFICAR + "classificação incerta entre X e Y" + range; `selo.faixa_do_veredito(a.veredito) is None`. Confirmado ao vivo com fixture fronteiriça: candidatos=[9.08, 22.68], veredito_range=(9.08,22.68). **UI (app.py): FALHA PARCIAL** — o metric card "Intrínseco (<motor>)" (app.py:976-988) continua mostrando a banda do ensemble do arquétipo primário (4,41–9,08 na mesma fixture), um número DIFERENTE do range de incerteza anunciado no banner (9,08–22,68) — dois números contraditórios na mesma tela (WR-01, confirmado ao vivo). Ver gap estruturado no frontmatter. |
| 5 | SC#5 — Firewall selo↛report preservado; test_selo/test_vulc3_regressao/test_guardrails_fix06/test_consistencia_modos verdes | ✓ VERIFIED | `grep -n "import report" src/analista/report/selo.py` vazio; `selo.py` só importa `dataclasses`/`typing`. Suíte da fase (13 módulos, 164 testes) verde; suíte completa do repo (434 testes) verde. |
| 6 (derivada do Core Value / objetivo da fase) | O selo NUNCA apresenta a banda do DDM sob o rótulo de outro motor sem aviso (nunca "finge certeza" atribuindo autoria errada ao número) | ✗ FAILED | CR-01 do code review, CONFIRMADO por leitura direta de `report.py:495-520` e `app.py:982-988` (não é só a alegação do reviewer — reproduzi a lógica linha a linha). Path alcançável: motor do arquétipo degrada (None) mas a banda DDM sobrevive → veredito e métrica saem 100% do DDM, rotulados com o nome do motor, sem qualquer alerta. Nenhum teste cobre esse caminho especificamente (o teste existente força motor E DDM a degradarem juntos). Ver gap estruturado no frontmatter. |

**Score:** 4/6 truths fully verified; 1 partial (SC#4 na UI); 1 failed (Core Value/CR-01 no caminho de degradação silenciosa)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/report/report.py` | Banda do ensemble + campos de divergência + `_HIPOTESE_DIVERGENCIA` | ✓ VERIFIED | 5 campos em `AnaliseAcao` (contraponto_valor, banda_do_motor, divergencia_ativa, divergencia_razao, divergencia_hipotese) presentes e usados; `_HIPOTESE_DIVERGENCIA` dict presente (linha 742) |
| `src/analista/report/report.py` | `_guarda_san01` (SAN-01) | ✓ VERIFIED | Função presente (linha 107), assinatura `(a, c, cfg, valor_pares=None)`, chamada no funil antes de `montar_selo` |
| `src/analista/report/report.py` | `_intrinseco_por_motor` + ramo fronteiriço (VER-02) | ✓ VERIFIED | Helper presente (linha 183), reutilizado pelo dispatch principal e pelo ramo `arquetipo_fronteirico`; campos `arquetipo_incerto`/`candidatos_intrinsecos`/`veredito_range` presentes e populados |
| `config.yaml` | Bloco `veredito.margem_seguranca` + `veredito.san01.*` | ✓ VERIFIED | Confirmado via leitura direta (linhas 101-107) |
| `app.py` | Render da bandeira/range/reetiqueta + rótulo do intrínseco por motor | ⚠️ WIRED mas com defeito de consistência | Blocos `st.info`/`st.warning` presentes e conectados aos campos corretos (`divergencia_ativa`, `arquetipo_incerto`, `san01_reetiquetado`); rótulo do intrínseco usa `a.motor_rotulo` quando `motor != "ddm"` — mas NÃO considera `a.banda_do_motor`, produzindo o defeito CR-01/WR-01 acima |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `report.analisar_acao` (banda vmin/vmax do motor) | `selo.montar_selo` via `a.veredito` | prefixo SUB/NO INTERVALO/SOBRE reconhecido por `faixa_do_veredito` | ✓ WIRED | Confirmado ao vivo (ITUB4: SOBREAVALIADA → selo "Boa, mas cara", não "Evitar") |
| `report.analisar_acao` | `comparables.divergencia_entre_lentes` | chamada direta no funil (linha 504) | ✓ WIRED | Confirmado ao vivo (ITUB4: divergencia_ativa=True, razao≈3.02) |
| `report._guarda_san01` | `a.veredito` reetiquetado | troca de texto antes de `montar_selo` | ✓ WIRED | Confirmado: `_guarda_san01` chamado na linha 587, antes do bloco do selo |
| `report.analisar_acao` (ramo fronteiriço) | dispatch de motor por candidato | `_intrinseco_por_motor` reutilizado | ✓ WIRED | Confirmado ao vivo: 2 candidatos resolvidos, range correto |
| Veredito fronteiriço (prefixo VERIFICAR) | `selo.montar_selo` (faixa suprimida) | overlay VERIFICAR existente em `selo.py:119` | ✓ WIRED | Confirmado: `selo.faixa_do_veredito(a.veredito) is None` no caso fronteiriço |
| `app.py` bloco veredito | campos `a.divergencia_*`/`a.veredito_range`/`a.san01_reetiquetado` | leitura read-only | ⚠️ WIRED mas INCOMPLETO | Os 3 blocos textuais estão conectados; mas o metric card do intrínseco (linha 976) NÃO está condicionado a `a.arquetipo_incerto` nem a `a.banda_do_motor`, produzindo os defeitos WR-01/CR-01 acima |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VER-01 | 03-01, 03-04 | Selo consome motor do arquétipo, não DDM fixo | ✓ SATISFIED (com ressalva CR-01) | Confirmado ao vivo para os arquétipos com motor válido; falha silenciosa confirmada no caminho motor-None+DDM-válido (CR-01) |
| ENS-01 | 03-01, 03-04 | Motor primário + contraponto DDM; divergência >2× levanta bandeira com hipótese | ✓ SATISFIED | Confirmado ao vivo |
| SAN-01 | 03-02, 03-04 | Guarda-corpo anti-aberração antes de "evitar" | ✓ SATISFIED (com ressalva WR-02) | Guardrail existe e dispara no caso âncora; falta checagem direcional (WR-02) |
| VER-02 | 03-03, 03-04 | Caso-fronteira assume a dúvida (range+bandeira) | ✓ SATISFIED no engine/CLI; ⚠️ PARCIAL na UI (WR-01) | Confirmado ao vivo report.py/relatorio_markdown; app.py metric card contradiz o banner |

Nenhum requisito órfão: `.planning/REQUIREMENTS.md` mapeia só ENS-01/SAN-01/VER-01/VER-02 para a Fase 3, e todos os 4 aparecem no frontmatter `requirements:` de algum plano (03-01/02/03/04).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/analista/report/report.py` | 495-520 | Bloco condicional sem `else`/`elif` para motor-None + DDM-válido (CR-01) | 🛑 Blocker | Veredito/métrica podem ser 100% DDM sob rótulo de outro motor, sem aviso — viola diretamente o Core Value do projeto ("números fiéis ao método e consistentes entre si") e o próprio objetivo da fase |
| `app.py` | 976-988 | Metric card do intrínseco não suprime/substitui a faixa quando `a.arquetipo_incerto` (WR-01) | ⚠️ Warning | Mesma tela mostra dois números de "intrínseco" conflitantes no caso-fronteira |
| `src/analista/report/report.py` | 107-180 (`_guarda_san01`) | Gate SAN-01 sem checagem direcional entre motor e DDM (WR-02) | ⚠️ Warning | Pode reetiquetar uma sobreavaliação genuína (onde o próprio motor primário concorda que está cara) como "DDM conservador demais" |
| `app.py` vs `report.py:880-889` | 976-988 / 880-889 | Representação do intrínseco do motor difere entre CLI (ponto único) e UI (banda motor×DDM) sob o mesmo rótulo (WR-03) | ℹ️ Info | Inconsistência de apresentação entre superfícies, mesmo número de base |
| `report.py` | 274-278 | "entre X e Y" nomeia primeiro/último candidato por ordem de inserção, não necessariamente os extremos do range (IN-01) | ℹ️ Info | Prosa pode nomear um par mais estreito que o range implica com ≥3 candidatos |

Nenhum marcador de dívida (TBD/FIXME/XXX) sem referência de follow-up encontrado nos arquivos da fase.

### Human Verification Required

Nenhum item requer verificação humana — todos os achados acima foram confirmados programaticamente (leitura de código + execução ao vivo), não apenas inferidos do SUMMARY.

## Gaps Summary

A fase entrega e verifica corretamente 4 das 5 Success Criteria do ROADMAP de forma direta e
demonstrável em execução ao vivo (não só via testes goldens, que também passam: 434/434 na suíte
completa). O firewall selo↛report está intacto, e os quatro requisitos (VER-01/ENS-01/SAN-01/
VER-02) têm artefatos e wiring reais, não stubs.

Porém, a verificação independente confirmou (não apenas aceitou a alegação do SUMMARY) os
achados centrais do code review (03-REVIEW.md):

1. **CR-01 (BLOCKER):** existe um caminho real e alcançável — motor do arquétipo degrada para
   `None` mas a banda DDM sobrevive — em que o veredito e a métrica de intrínseco são
   inteiramente derivados do DDM, mas exibidos sob o rótulo do motor do arquétipo, sem qualquer
   alerta. Isso é exatamente o tipo de "veredito desonesto" que a Fase 3 foi desenhada para
   eliminar, e nenhum teste cobre esse caminho especificamente. Como o objetivo da fase e o Core
   Value do projeto giram em torno de "números fiéis ao método e consistentes entre si", este é
   um gap que bloqueia a alegação de que "o selo consome o motor do arquétipo" de forma
   incondicional.

2. **WR-01 (gap parcial em SC#4, superfície Streamlit):** no caso-fronteira, o metric card
   "Intrínseco (<motor>)" do Streamlit mostra um número diferente do range anunciado no banner de
   incerteza — a UI não "assume a dúvida" de forma consistente na mesma tela, mesmo que o texto
   do veredito/CLI o faça corretamente.

3. **WR-02 (risco de qualidade, não bloqueante para as SCs literais):** o guarda-corpo SAN-01 não
   verifica que o motor primário concorda com a tese de "DDM conservador demais" antes de
   reetiquetar — pode mascarar uma sobreavaliação genuína.

Recomendação: fechar CR-01 (obrigatório) e WR-01 (recomendado, mesma fase) antes de considerar a
Fase 3 goal-complete; WR-02/WR-03/IN-01/IN-02 podem ser tratados via `/gsd-plan-phase --gaps` na
mesma leva ou registrados como débito técnico explícito com override, a critério do
desenvolvedor.

---

_Verified: 2026-07-12T13:01:22Z_
_Verifier: Claude (gsd-verifier)_
