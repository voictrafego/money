---
phase: 13-motores-contrato-de-sa-da-eng
plan: 06
subsystem: contrato-de-saida
tags: [ranking-screener, ranking-cego-ao-preco, freio-morto, arquetipo-motor-morto, selo-sem-evitar, ui-minima, ms-slider, ponte-pb]

requires:
  - phase: 13-motores-contrato-de-sa-da-eng
    plan: 03
    provides: "RIM único (_valor_rim); ensemble morto em report.py; a.motor sempre 'rim'"
  - phase: 13-motores-contrato-de-sa-da-eng
    plan: 04
    provides: "Ponte P/B (pb_justo/v_ponte/payout_terminal) exposta em AnaliseAcao; região da MS primária"
provides:
  - "Ranking rebaixado a SCREENER por múltiplos crus (Nota + P/L + P/VP + DY + Selo); preço-alvo/upside/veredito e a lente ensemble×DDM SAÍRAM"
  - "freio.py, arquetipo.ARQUETIPO_MOTOR e comparables.divergencia_entre_lentes DELETADOS (últimos consumidores do mundo antigo)"
  - "UI Analisar mínima (D-08): slider de MS, ponte P/B exibida, matriz Ke×g reusada"
  - "selo sem 'Evitar' e sem o rótulo 'Baixa' (re-rotulado neutro 'Atenção'); VALUE TRAP/Fraca mantidos; faixa_do_veredito intocado"
affects: [14-validacao]

tech-stack:
  added: []
  patterns:
    - "Ranking = screener relativo por múltiplos crus (Cap. 11-12), CEGO ao nível de preço — a regressão de pares NÃO imputa quanto a ação vale"
    - "MS como widget que EXPÕE o parâmetro do usuário (reprojeta a região exibida), nunca calibra o default (Armadilha 4 neutralizada por construção)"
    - "Straggler de behavior-change (não referência de símbolo): teste de propriedade que o sistema removeu → DELETE com classificacao no mesmo diff"

key-files:
  created: []
  modified:
    - src/analista/cli.py
    - app.py
    - src/analista/core/arquetipo.py
    - src/analista/core/comparables.py
    - src/analista/report/report.py
    - src/analista/report/selo.py
    - tests/test_arquetipo.py
    - tests/test_selo.py
    - tests/test_presentation_multiticker.py
    - tests/helpers_blindagem.py
    - tests/classificacao.yaml

key-decisions:
  - "test_cli_rank_consistencia.py DELETADO (straggler): cmd_rank não roda mais analisar_acao, a propriedade cross-menu de intrínseco via CLI deixou de existir (rank virou screener de múltiplos puros, sem macro/valuation)"
  - "Rótulo neutro do eixo qualidade = 'Atenção' (amarelo/vermelho); a célula ('Atenção','Caro') degrada para rotulo None (sem 'Evitar', sem veredito binário)"
  - "test_comparables.py e test_comparador.py NÃO tocados: o CTEEP testa preco_alvo_por_regressao (função MANTIDA) e o comparador deriva o badge da fonte (consistente ao relabel) — não precisaram mudar"

requirements-completed: [ENG-05, ENG-06, ENG-07, ENG-11]

duration: 40min
completed: 2026-07-20
---

# Phase 13 Plan 06: Rebaixamento do Ranking + morte do mundo antigo + UI mínima Summary

**O Ranking foi REBAIXADO a screener por múltiplos crus (Nota + P/L + P/VP + DY + Selo) — as colunas preço-alvo/upside/veredito e a 2ª lente ensemble×DDM saíram porque a regressão de pares é cega ao nível de preço; os últimos artefatos do mundo antigo (`freio.py`, `ARQUETIPO_MOTOR`, `comparables.divergencia_entre_lentes`, `test_ranking_freio.py`) morreram; a UI Analisar recebeu o mínimo do livro (slider de MS + ponte P/B + matriz Ke×g reusada); e o selo perdeu "Evitar" e o rótulo "Baixa" (re-rotulado neutro "Atenção", VALUE TRAP/Fraca mantidos). Suíte default 468 passed / 0 failed; orçamento de 3 graus intacto.**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-07-20
- **Tasks:** 4
- **Files:** 14 (5 produção + 6 testes/config modificados; 3 deletados)

## Task Commits

1. **Task 1: Rebaixar a view do Ranking (cli + app)** — `43d69b8` (refactor)
2. **Task 2: Deletar freio.py, ARQUETIPO_MOTOR, divergencia_entre_lentes + test_ranking_freio + repontar test_arquetipo** — `4cda48e` (refactor)
3. **Task 3: UI Analisar mínima — MS slider + ponte P/B + matriz reusada** — `43e98e4` (feat)
4. **Task 4: selo sem "Evitar" e sem "Baixa" + migrar badges** — `3d72b4f` (feat)

## Accomplishments

- **Ranking = screener por múltiplos crus (ENG-11):** `cli.cmd_rank` e o Ranking do `app.py` deixaram de estampar preço-alvo/upside/veredito e a 2ª lente ensemble×DDM + divergência de lentes (`cli.py:203-243`). O CLI exibe Nota + P/L + DY; o app exibe Nota + P/L + P/VP + DY + Selo, com os múltiplos vindo da fonte canônica `lentes.metricas_par` (o MESMO P/L/P/VP/DY dos "Pares do setor" do Analisar — Core Value cross-modo). O `_carimbar_macro` saiu do rank (sem valuation, sem macro).
- **`preco_alvo_por_regressao` DESCONECTADA, não deletada:** a conferência CTEEP do livro (Cap. 12) permanece na engine (`grep -c 'def preco_alvo_por_regressao' == 1`, `test_preco_alvo_cteep` verde) — só saiu da view do Ranking.
- **Mundo antigo morto (ENG):** `src/analista/core/freio.py` DELETADO (o ranque era o último consumidor); `arquetipo.ARQUETIPO_MOTOR` (registry legado arquétipo→motor) DELETADO; `comparables.divergencia_entre_lentes` + `LIMIAR_DIVERGENCIA` DELETADOS. `grep -rc 'ARQUETIPO_MOTOR' src/ app.py tests/ == 0`; `grep -rc 'import.*freio|freio\\.' src/ app.py == 0`.
- **`test_ranking_freio.py` DELETADO inteiro:** o import de `freio`/`cli._motor_pendente` no topo do módulo impede deleção função-a-função; 16 entradas de `classificacao.yaml` removidas no MESMO diff. `test_arquetipo.py` repontado de `ARQUETIPO_MOTOR` para `ARQUETIPO_ANCORA_ROE` (import + asserts de membership + o `[r.chave]=="ddm"` → `in ARQUETIPO_ANCORA_ROE`).
- **UI Analisar mínima (ENG-06/07, D-08):** slider de MS (`st.slider` 0–20%, default de `cfg["veredito"]["margem_seguranca"]`) que reprojeta a região de valor exibida (`intrínseco×(1∓MS)`) SEM recalibrar o default; bloco da ponte P/B (P/B justo, V=P/B×VPA, payout terminal — campos já derivados no Plano 04, READ-ONLY); matriz Ke×g reusada (já montada sobre `a.ke`, Fase 12). Lentes Graham/Bazin INTOCADAS.
- **Selo sem "Evitar" e sem "Baixa" (D-08):** `_MATRIZ` perdeu a célula `("Baixa","Caro")="Evitar"` (o veredito binário que nunca veio do livro); o eixo de qualidade "Baixa" foi re-rotulado neutro "Atenção" em `_qualidade` e nas chaves do `_MATRIZ`. VALUE TRAP e Fraca permanecem; `faixa_do_veredito` INTOCADO.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `test_cli_rank_consistencia.py` deletado (straggler de behavior-change)**
- **Found during:** Task 1
- **Issue:** o teste espiava `report.analisar_acao` dentro de `cmd_rank` e asseverava `len(vistos)==2` + `motor=="rim"` + intrínseco cross-menu idêntico. Ao remover a lente ensemble×DDM, `cmd_rank` não chama mais `analisar_acao` (o rank virou screener de múltiplos puros, sem macro/valuation) — a propriedade que o teste travava DEIXOU DE EXISTIR (não é um número que quebrou, é um caminho que morreu).
- **Fix:** DELETADO o arquivo inteiro + a entrada em `classificacao.yaml` no mesmo diff (0 órfão). Espelha o padrão de straggler da onda 3 do 13-03.
- **Commit:** `43d69b8`

**2. [Rule 3 - Blocking] Tokens `ARQUETIPO_MOTOR`/`freio` em não-consumidores**
- **Found during:** Task 2
- **Issue:** o acceptance exige `grep -rc 'ARQUETIPO_MOTOR' == 0` e a deleção do módulo `freio`. Sobravam menções em (a) `report.py:310` (comentário citando o registry legado), e (b) `tests/helpers_blindagem.py` `MODULOS_VALUATION` (lista o basename "freio" — módulo agora inexistente).
- **Fix:** comentário de `report.py` reescrito sem o token; "freio" removido de `MODULOS_VALUATION` (referência a módulo deletado).
- **Commit:** `4cda48e`

**Total:** 2 auto-fixed (ambos blocking). Nenhuma mudança arquitetural; `config.yaml`/`calibracao.lock.yaml` INTOCADOS.

## Notas de projeto

- **Ranking é cego ao preço — cumprido por construção** (memória `ranking-e-cego-ao-preco`): o Ranking agora só ordena por Nota (múltiplos padronizados) e mostra os múltiplos crus; nenhuma coluna imputa nível de preço. O valuation absoluto por preço vive só no Analisar (a tríade do livro).
- **Blocos MORTOS do ensemble em `app.py` (Analisar) seguem deferidos.** O manchete do intrínseco ainda rotula "Intrínseco (DDM)" mesmo com o motor sendo RIM (a lógica `_usa_motor`/`_label_intr` depende de `getattr(a,"banda_do_motor",False)` que é sempre False pós-13-03 → cai no rótulo "(DDM)"), e há blocos de `a.divergencia_*`/`a.san01_reetiquetado`/`a.arquetipo_incerto` gateados por `getattr(...,False)` que nunca renderizam. Não crasham (short-circuit), fora do escopo mínimo desta task (D-08 pede só MS/ponte/matriz). Registrado como dívida de UI.

## Known Stubs

None — o Ranking mostra múltiplos reais ou "—" (never-raise via `lentes.metricas_par`); a ponte P/B mostra os campos reais do `_derivar_insumo` (Plano 04) ou é omitida quando `pb_justo is None`. Nenhum placeholder flui para a UI.

## Verification

- `.venv/bin/python -m pytest -q` (default): **468 passed, 1 skipped, 18 deselected, 0 failed** (baseline 485 − 1 straggler [test_cli_rank_consistencia] − 16 test_ranking_freio). `-m golden_nivel`: **18 passed, 0 CLASSIFICACAO ORFA**.
- Ranking sem preço-alvo/upside/veredito no ranque (cli.py/app.py); Nota + múltiplos crus + Selo permanecem; `preco_alvo_por_regressao` intacta (CTEEP verde) e desconectada da view.
- `test ! -f src/analista/core/freio.py`; `test ! -f tests/test_ranking_freio.py`; `grep -rc 'ARQUETIPO_MOTOR' src/ app.py tests/ == 0`; `grep -c 'def divergencia_entre_lentes' comparables.py == 0`; test_arquetipo importa/usa `ARQUETIPO_ANCORA_ROE`.
- `grep -c '"Evitar"|"Baixa"' selo.py == 0`; VALUE TRAP/Fraca presentes; `faixa_do_veredito` diff VAZIO; `ast.parse(app.py)` OK; lentes Graham/Bazin intocadas.
- **Fronteira:** `git diff 43d69b8^..HEAD -- config.yaml calibracao.lock.yaml` **VAZIO** — orçamento de 3 graus intacto (nenhum knob de valuation tocado).


## Self-Check: PASSED

- Files exist: `13-06-SUMMARY.md`, `selo.py` — FOUND; `freio.py`, `test_ranking_freio.py`, `test_cli_rank_consistencia.py` — DELETADOS (confirmado).
- Commits exist: `43d69b8` (T1), `4cda48e` (T2), `43e98e4` (T3), `3d72b4f` (T4) — all FOUND.
- Suíte re-rodada: default 468 passed / 1 skipped / 18 deselected / 0 failed; `-m golden_nivel` 18 passed / 0 ORFA; config/lock diff VAZIO.

---
*Phase: 13-motores-contrato-de-sa-da-eng*
*Completed: 2026-07-20*
